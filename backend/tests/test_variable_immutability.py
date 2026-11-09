"""R6 integrity tests, exclusively on the owned PostgreSQL fixture."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from alembic.util import CommandError
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.models import ScientificVariable
from test_aggregate_sealing import TABLES, db as old_db, migrate, scalar, seal
from test_n1_snapshot import build, clone, g, history, insert, race

pytestmark = pytest.mark.postgres
HEAD = '0005_variable_immutability'
BASE = '0004_m44_n1'


@pytest.fixture(scope='module')
def db(old_db):
    with old_db.begin() as c:
        migrate(c,'upgrade',HEAD)
    return old_db


def approve(c,g,variable,evidence,sealed=True):
    rid=insert(c,g,'review_event',variable_id=variable,revision=1,decision='approved',
               rationale='technical fixture',reviewer_ref='fixture',reviewed_at=datetime.now(timezone.utc),evidence_id=evidence)
    if sealed:
        seal(c,g,'review_event',pid=rid)
    return rid


def evidence(c,g):
    return clone(c,g,'evidence_reference',g['evidence_reference'],locator_key=str(uuid4()))


def successor(c,g,ev,version=2):
    return clone(c,g,'scientific_variable',g['scientific_variable'],definition_version=version,
                 unit_basis='corrected fixture',evidence_id=ev)


def read_row(c,table,pk):
    t=TABLES[table]
    return dict(c.execute(select(t).where(t.c.id==pk)).mappings().one())


@pytest.mark.parametrize('approved',[False,True])
@pytest.mark.parametrize('mutation',["UPDATE scientific_variable SET definition_version=2",
    "UPDATE scientific_variable SET unit_basis='changed'","UPDATE scientific_variable SET description='changed'",
    "DELETE FROM scientific_variable"])
def test_direct_mutation(db,g,approved,mutation):
    with db.begin() as c:
        variable=g['scientific_variable']
        if approved: approve(c,g,variable,g['evidence_reference'])
        before=read_row(c,'scientific_variable',variable)
        with pytest.raises(DBAPIError) as error,c.begin_nested():
            c.execute(text(mutation+' WHERE id=:id'),{'id':variable})
        assert error.value.orig.sqlstate=='55000'
        assert read_row(c,'scientific_variable',variable)==before


def test_orm_rollback(db,g):
    key=(g['investigation'],g['scientific_variable'])
    with Session(db) as session:
        row=session.get(ScientificVariable,key)
        before=row.description
        row.description='forbidden ORM change'
        with pytest.raises(DBAPIError) as error: session.commit()
        assert error.value.orig.sqlstate=='55000'
        session.rollback()
        assert session.get(ScientificVariable,key).description==before


def test_preexisting_pins_roundtrip_and_successor(db,g):
    inv=g['investigation']; original=g['scientific_variable']; ev=g['evidence_reference']
    with pytest.raises(CommandError,match='explicit'),db.begin() as c:
        migrate(c,'downgrade',BASE)
    with db.begin() as c:
        migrate(c,'downgrade',BASE,True)
        rid=approve(c,g,original,ev)
        ps=seal(c,g,'analysis_protocol')
        owner,sid=build(c,g)

    def state(c):
        rows=[read_row(c,t,k) for t,k in [('scientific_variable',original),('evidence_reference',ev),('review_event',rid),
              ('aggregate_seal',ps),('protocol_requirement',g['protocol_requirement'])]]
        digest=scalar(c,"select member_digest from flare_sealing.snapshot('analysis_protocol',:i,:p)",i=inv,p=g['analysis_protocol'])
        assert digest==rows[3]['member_digest'] and rows[4]['variable_id']==original
        return rows,digest,history(c,g,owner,sid)

    with db.begin() as c:
        before=state(c)
        # Audit the existing M4.4 fixture by all four scoped FK paths.
        for table in ('semantic_annotation','review_event','condition_component','protocol_requirement'):
            assert scalar(c,f'select count(*) from {table} where investigation_id=:i and variable_id=:v',i=inv,v=original)>0
        migrate(c,'upgrade',HEAD)
    with db.begin() as c:
        assert state(c)==before
        new_ev=evidence(c,g)
        v=successor(c,g,new_ev)
        assert v!=original
        new=read_row(c,'scientific_variable',v)
        assert (new['variable_code'],new['definition_version'])==(before[0][0]['variable_code'],2)
        p=clone(c,g,'analysis_protocol',g['analysis_protocol'],protocol_version='successor fixture')
        def requirement():
            clone(c,g,'protocol_requirement',g['protocol_requirement'],protocol_id=p,variable_id=v)
        def rejected(operation):
            with pytest.raises(DBAPIError) as error,c.begin_nested(): operation()
            assert error.value.orig.sqlstate=='23514'
        rejected(requirement)
        rejected(lambda: approve(c,g,v,ev))
        new_review=approve(c,g,v,new_ev,False)
        rejected(requirement)
        seal(c,g,'review_event',pid=new_review)
        requirement()
        seal(c,g,'analysis_protocol',pid=p)
    with db.begin() as c: assert state(c)==before


def test_fresh_evidence_version_and_rollback(db,g):
    with db.begin() as c:
        new_ev=evidence(c,g)
        for ev,version in [(g['evidence_reference'],2),(new_ev,3)]:
            with pytest.raises(DBAPIError) as error,c.begin_nested(): successor(c,g,ev,version)
            assert error.value.orig.sqlstate=='23514'
        with pytest.raises(RuntimeError),c.begin_nested():
            successor(c,g,new_ev)
            raise RuntimeError('rollback technical correction')
        successor(c,g,new_ev)
        with pytest.raises(DBAPIError) as error,c.begin_nested():
            c.execute(text("update evidence_reference set excerpt='changed' where id=:id"),{'id':new_ev})
        assert error.value.orig.sqlstate=='55000'


def test_concurrent_successors(db,g):
    with db.begin() as c: e1,e2=evidence(c,g),evidence(c,g)
    first,second,_=race(db,lambda c:successor(c,g,e1),lambda c:successor(c,g,e2))
    assert second in ('23505','23514')
    with db.begin() as c:
        assert scalar(c,'select id from scientific_variable where investigation_id=:i and definition_version=2',i=g['investigation'])==first


def test_unreferenced_delete_and_truncate(db,g):
    with db.begin() as c:
        v=clone(c,g,'scientific_variable',g['scientific_variable'],variable_code='unreferenced')
        for statement in ('delete from scientific_variable where id=:id','truncate '+','.join('public.'+t for t in TABLES)):
            with pytest.raises(DBAPIError) as error,c.begin_nested():
                c.execute(text(statement),{'id':v})
            assert error.value.orig.sqlstate=='55000'
