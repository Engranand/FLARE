"""PostgreSQL 17 aggregate acceptance tests. All values are technical fixtures."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
import threading
import time
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.util import CommandError
from sqlalchemy import create_engine, text, select
from sqlalchemy.exc import DBAPIError

import app.models
from app.db.aggregate import run_aggregate_transaction
from app.db.base import Base
from app.db.migrations import migration_config

pytestmark = pytest.mark.postgres
M = {
    'parse_run': ('parse_run_id', ['source_field','source_record','observation']),
    'semantic_annotation': ('annotation_id', ['annotation_evidence']),
    'experimental_condition': ('condition_id', ['condition_component']),
    'analysis_protocol': ('protocol_id',['protocol_requirement','protocol_unit_rule']),
    'analytical_result': ('result_id',['result_input','result_condition','result_evidence']),
    'review_event': ('review_id',['approval_dependency']),
}
TABLES = Base.metadata.tables


def migrate(conn, direction, rev, confirmed=False):
    cfg = migration_config()
    cfg.attributes.update(connection=conn, allow_destructive_downgrade=confirmed)
    getattr(command, direction)(cfg, rev)


@pytest.fixture(scope='module')
def db(postgres_engines):
    owner, _ = postgres_engines
    assert owner.url.database.startswith('flare_test_')
    name = 'flare_seal_' + uuid4().hex
    with owner.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{name}"')
    engine = create_engine(owner.url.set(database=name), isolation_level='SERIALIZABLE')
    try:
        with engine.begin() as conn:
            migrate(conn,'upgrade','0003_m43_sealing')
        yield engine
    finally:
        engine.dispose()
        with owner.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{name}"')


def scalar(conn, query, **args):
    return conn.execute(text(query),args).scalar_one()


def seal(conn, g, target, archive=None, pid=None):
    return scalar(conn, 'select (flare_sealing.seal(:target,:inv,:pid,:sid,\'technical fixture\',:archive)).id',
                  target=target,inv=g['investigation'],pid=pid or g[target],sid=uuid4(),archive=archive)


def graph(conn, archive_edit=None, *, n1=False):
    ids = {}
    now = datetime(2026,1,1,tzinfo=timezone.utc)
    def add(table, **values):
        identity = uuid4()
        row = {'id':identity,'created_at':now, **values}
        if table!='investigation':
            row['investigation_id']=ids['investigation']
        conn.execute(TABLES[table].insert(),row)
        ids[table]=identity
        return identity
    add('investigation',repository_code='fixture',investigation_code=str(uuid4()),name='test',agency='fixture',source_repository_url='urn:test',metadata={})
    doc=add('source_document',original_filename='test.csv',source_type='csv',artifact_origin='software_artifact',sha256='a'*64,file_size_bytes=1,storage_key='fixture',metadata={})
    evidence=add('evidence_reference',source_document_id=doc,locator_kind='document',locator_key='fixture',locator_version='1',locator={},location_basis='fixture',extraction_method='fixture',extractor_version='1',verification_status='unverified',verification_scope='fixture')
    cell={'column_index':1,'original_header':'field','raw_value':'','classification':'empty','quality_flags':[]}
    archived={'source':{'filename':'test.csv','sha256':'a'*64},'parser_version':'1','record_provenance':{'source_row_id':'fixture','data_row_index':1,'csv_record_number':2,'original_headers':['field']},'cells':{'field':cell}}
    if archive_edit is not None:
        # Separate the producer bytes from the rows submitted to PostgreSQL.
        archived=json.loads(json.dumps(archived))
        archive_edit(archived)
    archive=(json.dumps(archived)+'\n').encode()
    run=add('parse_run',source_document_id=doc,parser_name='fixture',parser_version='1',code_sha256='b'*64,code_storage_key='fixture',configuration_sha256='c'*64,configuration={},output_sha256=hashlib.sha256(archive).hexdigest(),output_storage_key='fixture',record_count=1,status='complete')
    field=add('source_field',parse_run_id=run,table_key='fixture',ordinal=1,original_header='field',raw_unit_status='not_stated',header_evidence_id=evidence)
    record=add('source_record',parse_run_id=run,table_key='fixture',source_record_number=2,source_row_id='fixture',row_evidence_id=evidence)
    obs=add('observation',parse_run_id=run,source_record_id=record,source_field_id=field,evidence_id=evidence,raw_value='',source_value_kind='text',unit_origin='not_stated',parser_classification='empty',parser_flags={'quality_flags':[]},original_representation=cell)
    var=add('scientific_variable',variable_code='fixture',definition_version=1,canonical_name='fixture',description='fixture',unit_basis='fixture',variable_category='context',measurement_type='fixture',definition_status='unresolved',evidence_id=evidence)
    ann=add('semantic_annotation',observation_id=obs,variable_id=var,interpretation_key='fixture',revision=1,value_kind='numeric',numeric_value=Decimal('0.0123456789012345678900'),unit_status='unknown',transformation_method='fixture',transformation_version='1',parameters={'b':['','9',9,None,True],'a':'é\n'},uncertainty={},primary_evidence_id=evidence,author_ref='technical fixture')
    add('annotation_evidence',annotation_id=ann,evidence_id=evidence,role='technical')
    test=add('experimental_test',identity_namespace='fixture',test_identifier='fixture',identity_evidence_id=evidence,metadata={})
    segment=add('condition_segment',experimental_test_id=test,segment_key='fixture',scope_status='unknown',description='fixture',evidence_id=evidence)
    role=add('condition_role',role_code='fixture',definition='fixture',variable_category='context',evidence_id=evidence)
    cond=add('experimental_condition',segment_id=segment,experimental_test_id=test,segment_key='fixture',revision=1,scope_description='fixture',airflow_stability='unknown',evidence_id=evidence,extension_metadata={})
    add('condition_component',condition_id=cond,role_id=role,slot=1,instrument_status='unknown',variable_id=var,value_status='unknown',evidence_id=evidence)
    protocol=add('analysis_protocol',issue_policy='all_unresolved_review_or_blocking',coverage_policy='every_input_test_segment',protocol_code='fixture',protocol_version='1',description='fixture',requirements_schema_version='relational-v1',display_metadata={},evidence_id=evidence)
    req=add('protocol_requirement',protocol_id=protocol,requirement_key='fixture',target_kind='input',variable_id=var,phase='fixture',min_count=1,max_count=1,value_policy='numeric_only',stability_policy='not_applicable',instrument_policy='not_required',evidence_id=evidence)
    add('protocol_unit_rule',requirement_id=req,unit_text='technical',unit_basis='fixture',method='fixture',method_version='1',evidence_id=evidence)
    result=add('analytical_result',protocol_id=protocol,method='technical',method_version='1',parameters={},result_kind='text',unit_status='not_applicable',text_value='fixture',producer_ref='fixture',uncertainty={})
    link=add('test_source_record',experimental_test_id=test,source_record_id=record,evidence_id=evidence,match_method='fixture',method_version='1')
    review=add('review_event',test_link_id=link,revision=1,decision='approved' if n1 else 'needs_review',rationale='fixture',evidence_id=evidence,reviewer_ref='fixture',reviewed_at=now)
    if not n1:
        add('approval_dependency',owner_review_id=review,entry_kind='scope_link',role='scope_link',snapshot_observation_id=obs,snapshot_link_id=link)
    elig=add('analytical_eligibility',protocol_id=protocol,revision=1,observation_id=obs,eligibility_status='needs_review',reason='fixture',evidence_id=evidence,reviewer_ref='fixture',reviewed_at=now)
    add('result_input',segment_id=segment,result_id=result,annotation_id=ann,eligibility_id=elig,test_link_id=link,test_link_review_id=review,input_role='fixture')
    if n1:
        condition_head=add('review_event',condition_id=cond,revision=1,decision='approved',rationale='fixture',evidence_id=evidence,reviewer_ref='fixture',reviewed_at=now)
        elig=add('analytical_eligibility',protocol_id=protocol,revision=1,experimental_test_id=test,segment_id=segment,condition_id=cond,condition_review_id=condition_head,eligibility_status='eligible',reason='fixture',evidence_id=evidence,reviewer_ref='fixture',reviewed_at=now)
    add('result_condition',result_id=result,condition_id=cond,eligibility_id=elig)
    add('result_evidence',result_id=result,evidence_id=evidence,role='fixture')
    return ids,archive


@pytest.fixture
def dataset(db):
    with db.begin() as conn:
        return graph(conn)


def tagged(value):
    if value is None: return ['null']
    if isinstance(value,bool): return ['boolean',value]
    if isinstance(value,(int,Decimal)): return ['number',decimal_string(value)]
    if isinstance(value,str): return ['string',value]
    if isinstance(value,list): return ['array',[tagged(v) for v in value]]
    return ['object',[[k,tagged(value[k])] for k in sorted(value)]]


def decimal_string(value):
    s=format(value,'f')
    return s.rstrip('0').rstrip('.') if '.' in s else s


def canonical_row(conn, table, identity, inv):
    t=TABLES[table]
    row=dict(conn.execute(select(t).where(t.c.id==identity,t.c.investigation_id==inv)).mappings().one())
    for key,v in row.items():
        if str(t.c[key].type)=='JSONB': row[key]=tagged(v)
        elif isinstance(v,datetime): row[key]=v.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        elif isinstance(v,(int,Decimal)): row[key]=decimal_string(v)
        elif isinstance(v,(UUID,date)): row[key]=str(v)
    return row


def expected_bytes(value):
    s=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    # Python may abbreviate controls, so emit strings through an independent encoder.
    if isinstance(value,str):
        return ('"'+''.join('\\u%04x'%ord(c) if ord(c)<32 else '\\'+c if c in '"\\' else c for c in value)+'"').encode()
    if isinstance(value,list): return b'['+b','.join(map(expected_bytes,value))+b']'
    if isinstance(value,dict): return b'{'+b','.join(expected_bytes(k)+b':'+expected_bytes(value[k]) for k in sorted(value))+b'}'
    return s.encode()


@pytest.mark.parametrize('target', M)
def test_seal_bytes_members_and_freeze(db,dataset,target):
    g,archive=dataset
    inv=g['investigation']
    children=M[target][1]
    with db.begin() as conn:
        sid=seal(conn,g,target,archive)
        conn.exec_driver_sql('SET CONSTRAINTS ALL IMMEDIATE')
    with db.begin() as conn:
        payload=scalar(conn,'select canonical_bytes from flare_sealing.snapshot(:t,:i,:p)',t=target,i=inv,p=g[target])
        members=[[name,str(inv),str(g[name]),canonical_row(conn,name,g[name],inv)] for name in sorted(children)]
        expected=expected_bytes({'parent':canonical_row(conn,target,g[target],inv),'members':members})
        assert bytes(payload)==expected
        row=conn.execute(select(TABLES['aggregate_seal']).where(TABLES['aggregate_seal'].c.id==sid)).mappings().one()
        assert row['member_digest']==hashlib.sha256(expected).hexdigest()
        assert row['member_counts']=={'parent':1,**dict.fromkeys(children,1)}
        assert seal(conn,g,target,archive)==sid
        for table in children:
            t=TABLES[table]
            data=dict(conn.execute(select(t).where(t.c.id==g[table])).mappings().one())
            rejects(conn,t.insert(),data|{'id':uuid4()},'55000')
        for table,identity in [(target,g[target]),*((c,g[c]) for c in children),('aggregate_seal',sid)]:
            t=TABLES[table]
            rejects(conn,t.update().where(t.c.id==identity).values(id=identity),{},'55000')
            rejects(conn,t.delete().where(t.c.id==identity),{},'55000')


def rejects(conn,statement,args,state):
    with pytest.raises(DBAPIError) as exc, conn.begin_nested():
        conn.execute(statement,args)
    assert exc.value.orig.sqlstate==state


def test_golden_literals(db):
    with db.begin() as conn:
        actual=scalar(conn,'select flare_sealing.json_value(cast(:j as jsonb),true)',j='{"é":[null,"",1.2000,"1.2","\\t\\n\\u0001/","\\\"\\\\"]}')
        assert actual.encode()==r'["object",[["é",["array",[["null"],["string",""],["number","1.2"],["string","1.2"],["string","\u0009\u000a\u0001/"],["string","\"\\"]]]]]]'.encode()
        assert scalar(conn,'select flare_sealing.json_value(cast(:j as jsonb),true)',j='-0.000')=='["number","0"]'


def test_migration_cycle(db):
    with db.begin() as conn:
        g,archive=graph(conn)
        sid=seal(conn,g,'parse_run',archive)
        conn.exec_driver_sql('SET CONSTRAINTS ALL IMMEDIATE')
        with pytest.raises(CommandError,match='explicit'):
            migrate(conn,'downgrade','0002_m42_core_schema')
        migrate(conn,'downgrade','0002_m42_core_schema',True)
        assert scalar(conn,"select to_regnamespace('flare_sealing')") is None
        args=dict(value=json.dumps({hashlib.sha256(archive).hexdigest():archive.hex()}))
        scalar(conn,"select set_config('flare.m43_archives',:value,true)",**args)
        # Retained rows survive removal of enforcement. Tampering must block re-upgrade.
        with pytest.raises(CommandError),conn.begin_nested():
            conn.execute(text("update aggregate_seal set member_digest=repeat('0',64) where id=:s"),{'s':sid})
            migrate(conn,'upgrade','0003_m43_sealing')
        migrate(conn,'upgrade','0003_m43_sealing')
        assert scalar(conn,'select count(*) from aggregate_seal where id=:s',s=sid)==1
        assert scalar(conn,"select count(*) from pg_trigger where not tgisinternal and tgname='guard_member'")==11
        assert scalar(conn,"select count(*) from pg_trigger t join pg_proc p on p.oid=t.tgfoid where p.pronamespace='flare_sealing'::regnamespace")==64
        assert scalar(conn,"select count(*) from pg_proc where pronamespace='flare_sealing'::regnamespace")==14
        cfg=migration_config()
        cfg.attributes['connection']=conn
        from alembic.autogenerate import compare_metadata
        from alembic.migration import MigrationContext
        assert compare_metadata(MigrationContext.configure(conn), Base.metadata) == []



@pytest.mark.parametrize('alter',['counts','missing','extra','version','digest'])
def test_forged_seals_and_rollback(db,dataset,alter):
    g,_=dataset
    t='analysis_protocol'; inv=g['investigation']; pid=g[t]
    with db.begin() as conn:
        snap=conn.execute(text('select * from flare_sealing.snapshot(:t,:i,:p)'),dict(t=t,i=inv,p=pid)).mappings().one()
        counts=snap['member_counts']; digest=snap['member_digest']; version='canonical-json-v2'
        if alter=='counts': counts=counts|{'protocol_unit_rule':0}
        if alter=='version': version='canonical-json-v1'
        if alter=='digest': digest='0'*64
        if alter in ('missing','extra'):
            payload=json.loads(bytes(snap['canonical_bytes']))
            if alter=='missing': payload['members'].pop()
            else: payload['members'].append(payload['members'][0])
            digest=hashlib.sha256(expected_bytes(payload)).hexdigest()
        rejects(conn,TABLES['aggregate_seal'].insert(),dict(investigation_id=inv,id=uuid4(),protocol_id=pid,seal_version=version,member_counts=counts,member_digest=digest,sealed_by='technical',created_at=datetime.now(timezone.utc)),'23514')
        assert not scalar(conn,'select exists(select from aggregate_seal where protocol_id=:p)',p=pid)
        with pytest.raises(RuntimeError),conn.begin_nested():
            seal(conn,g,t)
            raise RuntimeError('injected after seal insert')
        assert not scalar(conn,'select exists(select from aggregate_seal where protocol_id=:p)',p=pid)


def test_new_parent_preserves_old_members_and_same_transaction_rejection(db,dataset):
    g,_=dataset
    with db.begin() as conn:
        first=seal(conn,g,'analysis_protocol')
        parent=TABLES['analysis_protocol']; child=TABLES['protocol_requirement']
        original=dict(conn.execute(select(parent).where(parent.c.id==g['analysis_protocol'])).mappings().one())
        req=dict(conn.execute(select(child).where(child.c.id==g['protocol_requirement'])).mappings().one())
        rejects(conn,child.insert(),req|{'id':uuid4(),'requirement_key':'late'},'55000')
        new=uuid4()
        conn.execute(parent.insert(),original|{'id':new,'protocol_version':'2'})
        for key in ('fixture','additional'):
            conn.execute(child.insert(),req|{'id':uuid4(),'requirement_key':key,'protocol_id':new})
        second=seal(conn,g,'analysis_protocol',pid=new)
        assert scalar(conn,'select member_counts from aggregate_seal where id=:s',s=first)=={'parent':1,'protocol_requirement':1,'protocol_unit_rule':1}
        assert scalar(conn,'select member_counts from aggregate_seal where id=:s',s=second)=={'parent':1,'protocol_requirement':2,'protocol_unit_rule':0}


@pytest.mark.parametrize('first',['child','seal'])
def test_two_connection_serialization(db,dataset,first):
    g,_=dataset
    pid=g['analysis_protocol']
    ready=threading.Event()
    worker_pid=[]
    attempts=[]
    def child(conn):
        row=conn.execute(select(TABLES['protocol_requirement']).where(TABLES['protocol_requirement'].c.id==g['protocol_requirement'])).mappings().one()
        conn.execute(TABLES['protocol_requirement'].insert(),dict(row)|{'id':uuid4(),'requirement_key':'racing member'})
    def operation(conn):
        attempts.append(1)
        worker_pid.append(scalar(conn,'select pg_backend_pid()'))
        ready.set()
        if first=='child': return seal(conn,g,'analysis_protocol')
        child(conn)
    with ThreadPoolExecutor(max_workers=1) as pool, db.connect() as leader:
        tx=leader.begin()
        try:
            if first=='child': child(leader)
            else: seal(leader,g,'analysis_protocol')
            future=pool.submit(run_aggregate_transaction,db,operation)
            assert ready.wait(10)
            with db.connect().execution_options(isolation_level='AUTOCOMMIT') as monitor:
                deadline=time.monotonic()+10
                while not scalar(monitor,'select cardinality(pg_blocking_pids(:pid))>0',pid=worker_pid[0]):
                    assert time.monotonic()<deadline,'worker failed to reach parent lock'
                    time.sleep(0.025)
            tx.commit()
            if first=='child': future.result(timeout=15)
            else:
                with pytest.raises(DBAPIError) as exc: future.result(timeout=15)
                assert exc.value.orig.sqlstate=='55000'
        finally:
            if tx.is_active: tx.rollback()
    with db.begin() as conn:
        assert len(attempts)>=2
        assert scalar(conn,'select member_counts from aggregate_seal where protocol_id=:p',p=pid)['protocol_requirement']==(2 if first=='child' else 1)
        assert scalar(conn,"select s.member_digest=x.member_digest from aggregate_seal s cross join lateral flare_sealing.snapshot('analysis_protocol',s.investigation_id,s.protocol_id) x where protocol_id=:p",p=pid)


def test_archive_wrong_bytes_and_truncate(db,dataset):
    g,archive=dataset
    with db.begin() as conn:
        rejects(conn,text("select flare_sealing.seal('parse_run',:i,:p,:s,'fixture',:archive)"),
                dict(i=g['investigation'],p=g['parse_run'],s=uuid4(),archive=archive+b' '),'23514')
        # All FK participants are named so RESTRICT cannot mask the truncate trigger.
        rejects(conn,text('TRUNCATE '+','.join('public.'+name for name in TABLES)),{},'55000')
        assert seal(conn,g,'parse_run',archive)


def test_parse_final_state_rejects_partial_run(db,dataset):
    g,_=dataset
    with pytest.raises(DBAPIError) as exc:
        with db.begin() as conn:
            parent=TABLES['parse_run']
            row=conn.execute(select(parent).where(parent.c.id==g['parse_run'])).mappings().one()
            conn.execute(parent.insert(),dict(row)|{'id':uuid4(),'parser_version':'partial'})
    assert exc.value.orig.sqlstate=='23514'


@pytest.mark.parametrize('alter',['missing','extra','raw','flags','header','ordinal'])
def test_correct_archive_hash_still_requires_exact_output(db,alter):
    def edit(row):
        if alter=='missing': del row['cells']['field']
        elif alter=='extra': row['cells']['extra']=row['cells']['field']
        elif alter=='header': row['record_provenance']['original_headers']=['other']
        elif alter=='ordinal': row['cells']['field']['column_index']=2
        elif alter=='flags': row['cells']['field']['quality_flags']=['other']
        else: row['cells']['field']['raw_value']='0'
    with db.begin() as conn:
        g,archive=graph(conn,edit)
        rejects(conn,text("select flare_sealing.seal('parse_run',:i,:p,:s,'fixture',:archive)"),
                dict(i=g['investigation'],p=g['parse_run'],s=uuid4(),archive=archive),'23514')


def test_ordered_members_and_batch_lock(db,dataset):
    g,_=dataset
    with db.begin() as conn:
        scalar(conn,'select flare_sealing.lock_parents(cast(:keys as jsonb))',keys=json.dumps([
            dict(target=t,inv=str(g['investigation']),pid=str(g[t])) for t in reversed(M)]))
        t=TABLES['protocol_unit_rule']
        row=dict(conn.execute(select(t).where(t.c.id==g[t.name])).mappings().one())
        ids=[UUID(int=n) for n in (3,2,1)]
        for identity in ids:
            conn.execute(t.insert(), row|{'id':identity,'unit_text':str(identity)})
        seal(conn,g,'analysis_protocol')
        data=scalar(conn,"select canonical_bytes from flare_sealing.snapshot('analysis_protocol',:i,:p)",i=g['investigation'],p=g['analysis_protocol'])
        members=json.loads(bytes(data))['members']
        assert [m[2] for m in members if m[0]==t.name]==sorted(map(str,[g[t.name],*ids]))


def test_failed_run_children_and_isolation(db,dataset):
    g,_=dataset
    with db.connect().execution_options(isolation_level='READ COMMITTED') as conn:
        rejects(conn,text("select flare_sealing.seal('analysis_protocol',:i,:p,:s,'fixture')"),dict(i=g['investigation'],p=g['analysis_protocol'],s=uuid4()),'25001')
    with pytest.raises(DBAPIError) as exc:
        with db.begin() as conn:
            t=TABLES['parse_run']; f=TABLES['source_field']
            failed=uuid4()
            row=dict(conn.execute(select(t).where(t.c.id==g['parse_run'])).mappings().one())
            conn.execute(t.insert(),row|{'id':failed,'status':'failed','parser_version':'failed'})
            field=dict(conn.execute(select(f).where(f.c.id==g['source_field'])).mappings().one())
            conn.execute(f.insert(),field|{'id':uuid4(),'parse_run_id':failed})
    assert exc.value.orig.sqlstate=='23514'


def test_invalid_unicode_and_exact_decimal(db):
    with db.begin() as conn:
        assert scalar(conn,'select flare_sealing.json_value(cast(:j as jsonb),true)',j='12345678901234567890.123456789012345678900000')=='["number","12345678901234567890.1234567890123456789"]'
        for raw in (r'"\ud800"',r'"\udc00"',r'"\u0000"'):
            with pytest.raises(DBAPIError) as exc,conn.begin_nested():
                scalar(conn,'select flare_sealing.json_value(cast(:j as jsonb),true)',j=raw)
            assert exc.value.orig.sqlstate in ('22P02','22P05')
