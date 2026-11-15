"""N1 acceptance fixtures use invented technical identifiers only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import threading
import time
from uuid import uuid4

from alembic import command
from alembic.util import CommandError
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.db.aggregate import run_aggregate_transaction
from app.db.migrations import migration_config
from test_aggregate_sealing import TABLES, db as old_db, graph, migrate, scalar, seal

pytestmark = pytest.mark.postgres


@pytest.fixture(scope='module')
def db(old_db):
    with old_db.begin() as conn:
        migrate(conn,'upgrade','head')
        with pytest.raises(CommandError,match='explicit'):
            migrate(conn,'downgrade','0003_m43_sealing')
        migrate(conn,'downgrade','0003_m43_sealing',True)
        assert scalar(conn,"select to_regnamespace('flare_n1')") is None
        migrate(conn,'upgrade','head')
        config=migration_config()
        config.attributes['connection']=conn
        command.check(config)
    return old_db


def insert(c,g,table,**values):
    pk=uuid4()
    c.execute(TABLES[table].insert(),dict(investigation_id=g['investigation'],id=pk,
              created_at=datetime.now(timezone.utc))|values)
    return pk


def clone(c,g,table,pk,**values):
    t=TABLES[table]
    row=dict(c.execute(select(t).where(t.c.investigation_id==g['investigation'],t.c.id==pk)).mappings().one())
    for key in ('id','created_at','investigation_id'):
        del row[key]
    return insert(c,g,table,**(row|values))


def review(c,g,column,subject,decision,sealed=True):
    kind={'result_id':'result','test_link_id':'link','issue_id':'issue'}[column]
    pk=scalar(c,"select flare_n1.append_head(:i,:k,:subject,:id,:d,:e,'technical fixture','technical fixture')",
              i=g['investigation'],k=kind,subject=subject,id=uuid4(),d=decision,e=g['evidence_reference'])
    if sealed: seal(c,g,'review_event',pid=pk)
    return pk


def link(c,g,record=None,test=None):
    if test is None:
        test=clone(c,g,'experimental_test',g['experimental_test'],test_identifier=str(uuid4()))
    identity=clone(c,g,'test_source_record',g['test_source_record'],source_record_id=record or g['source_record'],experimental_test_id=test)
    return identity,test


def issue(c,g,severity,**target):
    return insert(c,g,'data_quality_issue',issue_type='fixture',description='fixture',severity=severity,
                  detector_method='fixture',detector_version='1',evidence_id=g['evidence_reference'],**target)


def build(c,g):
    owner=review(c,g,'result_id',g['analytical_result'],'approved',False)
    sid=scalar(c,"select flare_n1.build(:i,:o,:s,'technical fixture')",i=g['investigation'],o=owner,s=uuid4())
    return owner,sid


def current(c,g,owner):
    return scalar(c,'select flare_n1.applicability_current(:i,:o)',i=g['investigation'],o=owner)


def history(c,g,owner,sid):
    return list(c.execute(text('select * from flare_n1.historical(:i,:o,:s)'),dict(i=g['investigation'],o=owner,s=sid)).mappings())


@pytest.fixture
def g(db):
    with db.begin() as c:
        g,_=graph(c,n1=True)
        def duplicate(table,**values): return clone(c,g,table,g[table],**values)
        selected=scalar(c,'select test_link_review_id from result_input where id=:id',id=g['result_input'])
        seal(c,g,'review_event',pid=selected)
        run=duplicate('parse_run',parser_version='condition fixture')
        row=duplicate('source_record',parse_run_id=run)
        field=duplicate('source_field',parse_run_id=run)
        obs=duplicate('observation',parse_run_id=run,source_record_id=row,source_field_id=field)
        annotation=duplicate('semantic_annotation',observation_id=obs)
        duplicate('condition_component',slot=2,value_status='known',annotation_id=annotation)
        selected2,_=link(c,g,record=row,test=g['experimental_test'])
        head=review(c,g,'test_link_id',selected2,'approved')
        insert(c,g,'approval_dependency',owner_review_id=g['review_event'],entry_kind='decision',role='identity',dependency_review_id=head)
        has_guard = scalar(c, "SELECT to_regprocedure('flare_sealing.check_condition_review()') IS NOT NULL")
        if has_guard:
            from test_variable_immutability import approve
            cond_seal=seal(c,g,'experimental_condition')
            var_rev=approve(c,g,g['scientific_variable'],g['evidence_reference'])
            insert(c,g,'approval_dependency',owner_review_id=g['review_event'],entry_kind='decision',role='condition_content',dependency_seal_id=cond_seal)
            insert(c,g,'approval_dependency',owner_review_id=g['review_event'],entry_kind='decision',role='variable_definition',dependency_review_id=var_rev)
            seal(c,g,'review_event')
            seal(c,g,'analytical_result')
            g['var_review']=var_rev
        else:
            for parent in ('experimental_condition','review_event','analytical_result'):
                seal(c,g,parent)



        g['extra_obs']=obs
        g['extra_link']=selected2
        for state in ('approved','rejected','unreviewed','revoked','unsealed'):
            key,test=link(c,g)
            g[state]=key
            if state!='unreviewed':
                g[state+'_head']=review(c,g,'test_link_id',key,'approved' if state=='unsealed' else state,state!='unsealed')
            if state=='approved':
                g['whole']=issue(c,g,'blocking',experimental_test_id=test)
                g['clearance']=review(c,g,'issue_id',g['whole'],'resolved')
        g['info']=issue(c,g,'info',observation_id=g['observation'])
        g['local']=issue(c,g,'review',observation_id=g['observation'])
        review(c,g,'issue_id',g['local'],'resolved')
        return g


def test_complete_historical_and_current(db,g):
    with db.begin() as c: owner,sid=build(c,g)
    with db.begin() as c:
        assert current(c,g,owner)
        rows=history(c,g,owner,sid)
        assert history(c,g,owner,uuid4())==[]
        assert {r['observation_id'] for r in rows if r['kind']=='scope_observation'}=={g['observation'],g['extra_obs']}
        links={r['link_id']:r for r in rows if r['kind']=='scope_link'}
        assert set(links)=={g['test_source_record'],g['extra_link'],*(g[k] for k in ('approved','rejected','unreviewed','revoked','unsealed'))}
        for state in ('rejected','unreviewed','revoked','unsealed'): assert links[g[state]]['effective_test'] is None
        assert links[g['unreviewed']]['head'] is None
        assert links[g['unsealed']]['head']==g['unsealed_head'] and links[g['unsealed']]['head_seal'] is None
        assert links[g['approved']]['effective_test']==links[g['approved']]['associated_test']
        issues={r['issue_id']:r for r in rows if r['kind']=='scope_issue'}
        assert set(issues)=={g['whole'],g['local'],g['info']}
        assert issues[g['whole']]['issue_test']==links[g['approved']]['effective_test']
        assert issues[g['info']]['head'] is None
        assert all(r['observation_id']==g['observation'] for r in issues.values())
        assert {r['dependency'] for r in rows if r['role']=='applicability_identity'}=={r['head'] for r in links.values() if r['effective_test']}
        assert {r['dependency'] for r in rows if r['role']=='applicability_clearance'}=={r['head'] for r in issues.values() if r['issue_severity']!='info'}


def change(c,g,action):
    if action=='new_link': link(c,g)
    elif action=='approve': review(c,g,'test_link_id',g['unreviewed'],'approved')
    elif action=='revoke': review(c,g,'test_link_id',g['approved'],'revoked')
    elif action=='head': review(c,g,'test_link_id',g['rejected'],'rejected',False)
    elif action=='seal': seal(c,g,'review_event',pid=g['unsealed_head'])
    elif action=='issue': issue(c,g,'info',observation_id=g['extra_obs'])
    elif action=='reopen': review(c,g,'issue_id',g['whole'],'open')
    elif action=='resolve': review(c,g,'issue_id',g['whole'],'resolved')
    else: raise ValueError(action)


@pytest.mark.parametrize('action',['new_link','approve','revoke','head','seal','issue','reopen','resolve'])
def test_invalidation_preserves_pinned_evidence(db,g,action):
    with db.begin() as c: owner,sid=build(c,g)
    with db.begin() as c: before=history(c,g,owner,sid)
    with db.begin() as c: change(c,g,action)
    if action=='reopen':
        with db.begin() as c: change(c,g,'resolve')
    with db.begin() as c:
        assert not current(c,g,owner)
        assert history(c,g,owner,sid)==before
        new_owner,new_seal=build(c,g)
        assert new_owner!=owner and new_seal!=sid
        assert current(c,g,new_owner) and not current(c,g,owner)


def test_unrelated_changes(db,g):
    with db.begin() as c: owner,sid=build(c,g)
    with db.begin() as c:
        t=clone(c,g,'experimental_test',g['experimental_test'],test_identifier='unrelated')
        issue(c,g,'blocking',experimental_test_id=t)
    with db.begin() as c: assert current(c,g,owner)


@pytest.mark.parametrize('decision,sealed',[(None,False),('open',True),('resolved',False)])
def test_unresolved_blocks(db,g,decision,sealed):
    with db.begin() as c:
        q=issue(c,g,'review',observation_id=g['extra_obs'])
        if decision: review(c,g,'issue_id',q,decision,sealed)
    with pytest.raises(DBAPIError) as exc, db.begin() as c: build(c,g)
    assert exc.value.orig.sqlstate=='23514'


@pytest.mark.parametrize('early',[False,True])
def test_mutation_later_in_same_transaction(db,g,early):
    with pytest.raises(DBAPIError) as exc, db.begin() as c:
        owner,sid=build(c,g)
        if early: c.exec_driver_sql('SET CONSTRAINTS ALL IMMEDIATE')
        change(c,g,'issue')
    assert exc.value.orig.sqlstate=='23514'
    with db.begin() as c: assert not history(c,g,owner,sid)

@pytest.mark.parametrize('fault',[
    'missing_O','extra_O','missing_L','extra_L','missing_Q','extra_Q','wrong_head','cross_target_seal',
    'absent_seal','unapproved_T','missing_identity_edge','missing_clearance_edge','extra_clearance',
    'duplicate','wrong_owner','wrong_kind','wrong_source','selected_revoked'])
def test_forged_snapshot(db,g,fault):
    with pytest.raises(DBAPIError) as exc, db.begin() as c:
        owner=review(c,g,'result_id',g['analytical_result'],'approved',False)
        if fault=='selected_revoked': review(c,g,'test_link_id',g['test_source_record'],'revoked')
        facts=list(c.execute(text('select * from flare_n1.expected(:i,:r)'),dict(i=g['investigation'],r=g['analytical_result'])).mappings())
        rows=[dict(owner_review_id=owner,entry_kind=f['kind'],role=f['role'],snapshot_observation_id=f['obs'],
                   snapshot_link_id=f['link_id'],snapshot_issue_id=f['issue_id'],snapshot_review_id=f['head'],
                   snapshot_review_seal_id=f['head_seal'],dependency_review_id=f['dependency']) for f in facts]
        def one(**filters): return next(r for r in rows if all(r[k]==v for k,v in filters.items()))
        marker=one(entry_kind='scope_observation',snapshot_observation_id=g['observation'])
        edge=one(snapshot_link_id=g['approved']); q=one(snapshot_issue_id=g['whole'])
        if fault=='missing_O': rows.remove(marker)
        elif fault=='extra_O':
            run=clone(c,g,'parse_run',g['parse_run'],parser_version='outside')
            r=clone(c,g,'source_record',g['source_record'],parse_run_id=run)
            f=clone(c,g,'source_field',g['source_field'],parse_run_id=run)
            obs=clone(c,g,'observation',g['observation'],parse_run_id=run,source_record_id=r,source_field_id=f)
            rows.append(marker|{'snapshot_observation_id':obs})
        elif fault=='missing_L': rows.remove(edge)
        elif fault=='extra_L': rows.append(edge|{'snapshot_observation_id':g['extra_obs']})
        elif fault=='wrong_source': edge['snapshot_observation_id']=g['extra_obs']
        elif fault=='missing_Q': rows.remove(q)
        elif fault=='extra_Q': rows.append(q|{'snapshot_observation_id':g['extra_obs']})
        elif fault=='wrong_head': edge['snapshot_review_id']=g['rejected_head']
        elif fault=='cross_target_seal': edge['snapshot_review_seal_id']=q['snapshot_review_seal_id']
        elif fault=='absent_seal': edge['snapshot_review_seal_id']=None
        elif fault=='unapproved_T':
            t=scalar(c,'select experimental_test_id from test_source_record where id=:x',x=g['rejected'])
            unrelated=issue(c,g,'info',experimental_test_id=t)
            rows.append(q|{'snapshot_issue_id':unrelated,'snapshot_review_id':None,'snapshot_review_seal_id':None})
        elif fault=='missing_identity_edge': rows.remove(one(role='applicability_identity'))
        elif fault=='missing_clearance_edge': rows.remove(one(role='applicability_clearance'))
        elif fault=='extra_clearance': rows.append(one(role='applicability_clearance')|{'dependency_review_id':g['rejected_head']})
        elif fault=='duplicate': rows.append(marker.copy())
        elif fault=='wrong_owner':
            marker['owner_review_id']=review(c,g,'issue_id',g['info'],'open',False)
        elif fault=='wrong_kind': marker['entry_kind']='unsupported'
        for row in rows: insert(c,g,'approval_dependency',**row)
        # Even a direct call to the existing aggregate sealer must pass N1 on commit.
        seal(c,g,'review_event',pid=owner)
    assert exc.value.orig.sqlstate==('23505' if fault=='duplicate' else '23514')


def race(db,leader_op,worker_op):
    """Release leader only after the observer sees the worker waiting for its lock."""
    arrived=threading.Event()
    pids=[]
    def attempt(c):
        pids.append(scalar(c,'select pg_backend_pid()'))
        arrived.set()
        return worker_op(c)
    with ThreadPoolExecutor(max_workers=1) as pool, db.connect() as c:
        tx=c.begin()
        try:
            left=leader_op(c)
            future=pool.submit(run_aggregate_transaction,db,attempt)
            assert arrived.wait(10)
            with db.connect().execution_options(isolation_level='AUTOCOMMIT') as observer:
                until=time.monotonic()+10
                while not scalar(observer,'select cardinality(pg_blocking_pids(:p))>0',p=pids[0]):
                    if future.done(): future.result()
                    assert time.monotonic()<until
                    time.sleep(0.02)
            tx.commit()
            try: right=future.result(timeout=20)
            except DBAPIError as err: right=err.orig.sqlstate
            return left,right,len(pids)
        finally:
            if tx.is_active: tx.rollback()


@pytest.mark.parametrize('first',['snapshot','mutation'])
@pytest.mark.parametrize('action',['new_link','approve','seal','issue','reopen','resolve'])
def test_snapshot_mutation_race(db,g,first,action):
    from app.db.applicability import applicability_current
    snapshot=lambda c: build(c,g)
    mutation=lambda c: change(c,g,action)
    if first=='snapshot':
        (owner,sid),worker,attempts=race(db,snapshot,mutation)
        assert worker is None
        assert not applicability_current(db,g['investigation'],owner)
        with db.begin() as c: assert history(c,g,owner,sid)
    else:
        _,worker,attempts=race(db,mutation,snapshot)
        if action=='reopen': assert worker=='23514'
        else:
            assert isinstance(worker,tuple),worker
            assert applicability_current(db,g['investigation'],worker[0])
        assert attempts>=2


def test_two_concurrent_review_heads(db,g):
    mutate=lambda c: review(c,g,'issue_id',g['whole'],'resolved')
    first,second,attempts=race(db,mutate,mutate)
    assert attempts>=2 and isinstance(second,type(first))
    with db.begin() as c:
        assert scalar(c,'select supersedes_id from review_event where id=:i',i=second)==first


def test_frozen_historical_identities(db,g):
    with db.begin() as c:
        for table,pk in [('test_source_record',g['approved']),('data_quality_issue',g['whole'])]:
            with pytest.raises(DBAPIError) as exc,c.begin_nested():
                tab=TABLES[table]
                c.execute(tab.update().where(tab.c.id==pk).values(id=pk))
            assert exc.value.orig.sqlstate=='55000'


def test_shared_issue_counts_once_per_observation(db,g):
    with db.begin() as c:
        shared=issue(c,g,'blocking',experimental_test_id=g['experimental_test'])
        cleared=review(c,g,'issue_id',shared,'resolved')
        owner,sid=build(c,g)
    with db.begin() as c:
        rows=history(c,g,owner,sid)
        assert {r['observation_id'] for r in rows if r['issue_id']==shared}=={g['observation'],g['extra_obs']}
        assert sum(r['dependency']==cleared and r['role']=='applicability_clearance' for r in rows)==1


@pytest.mark.parametrize('target',['input','component'])
def test_selected_identity_must_match_source_test_and_pinned_review(db,g,target):
    with db.begin() as c:
        result=clone(c,g,'analytical_result',g['analytical_result'])
        if target=='input':
            clone(c,g,'result_input',g['result_input'],result_id=result,
                  test_link_id=g['approved'],test_link_review_id=g['approved_head'])
        else:
            # Seal a condition with a new identity whose eligibility still selects the old condition.
            cond=clone(c,g,'experimental_condition',g['experimental_condition'],revision=2,supersedes_id=g['experimental_condition'])
            comp=scalar(c,'select id from condition_component where condition_id=:p and annotation_id is not null',p=g['experimental_condition'])
            clone(c,g,'condition_component',comp,condition_id=cond)
            seal(c,g,'experimental_condition',pid=cond)
            clone(c,g,'result_condition',g['result_condition'],result_id=result,condition_id=cond)
        g['analytical_result']=result
        seal(c,g,'analytical_result')
    with pytest.raises(DBAPIError) as exc, db.begin() as c: build(c,g)
    assert exc.value.orig.sqlstate=='23514'


def test_missing_seal_and_invalid_revision(db,g):
    with pytest.raises(DBAPIError) as exc, db.begin() as c:
        review(c,g,'result_id',g['analytical_result'],'approved',False)
    assert exc.value.orig.sqlstate=='23514'
    with pytest.raises(DBAPIError) as exc, db.begin() as c:
        clone(c,g,'review_event',g['approved_head'],revision=3,supersedes_id=g['rejected_head'])
    assert exc.value.orig.sqlstate=='23514'


def test_valid_component_identity_cannot_mask_another_wrong_selected_link(db,g):
    with db.begin() as c:
        cond=clone(c,g,'experimental_condition',g['experimental_condition'],revision=2,supersedes_id=g['experimental_condition'])
        member=scalar(c,'select id from condition_component where condition_id=:id and annotation_id is not null',id=g['experimental_condition'])
        clone(c,g,'condition_component',member,condition_id=cond)
        condition_review=clone(c,g,'review_event',g['review_event'],condition_id=cond)
        valid=scalar(c,'select id from review_event where test_link_id=:id',id=g['extra_link'])
        for pinned in (valid,g['approved_head']):
            insert(c,g,'approval_dependency',owner_review_id=condition_review,entry_kind='decision',role='identity',dependency_review_id=pinned)
        cond_seal=seal(c,g,'experimental_condition',pid=cond)
        insert(c,g,'approval_dependency',owner_review_id=condition_review,entry_kind='decision',role='condition_content',dependency_seal_id=cond_seal)
        insert(c,g,'approval_dependency',owner_review_id=condition_review,entry_kind='decision',role='variable_definition',dependency_review_id=g['var_review'])
        seal(c,g,'review_event',pid=condition_review)
        eligibility=clone(c,g,'analytical_eligibility',g['analytical_eligibility'],condition_id=cond,
                          condition_review_id=condition_review,revision=2,supersedes_id=g['analytical_eligibility'])
        result=clone(c,g,'analytical_result',g['analytical_result'])
        clone(c,g,'result_input',g['result_input'],result_id=result)
        clone(c,g,'result_condition',g['result_condition'],result_id=result,condition_id=cond,eligibility_id=eligibility)
        seal(c,g,'analytical_result',pid=result)
        g['analytical_result']=result
    with pytest.raises(DBAPIError) as exc, db.begin() as c: build(c,g)
    assert exc.value.orig.sqlstate=='23514'
