"""Committed PostgreSQL history and interleaving tests using only technical fixtures."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from threading import Event
from time import monotonic, sleep
from uuid import uuid4

from alembic import command
from alembic.util import CommandError
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.migrations import migration_config
from test_aggregate_sealing import canonical_row, db as old_db, expected_bytes, migrate, scalar, seal
from test_n1_snapshot import build, clone, current, g, history, insert
from test_variable_immutability import approve, evidence, read_row

pytestmark = pytest.mark.postgres
BASE = "0005_variable_immutability"
HEAD = "0007_m45_n2"


@pytest.fixture(scope="module")
def db(old_db):
    with old_db.begin() as conn:
        migrate(conn, "upgrade", HEAD)
        assert scalar(conn, "show server_version_num") == "170011"
    return old_db


def new_condition(conn, g, prior, revision, variable_review):
    shared = evidence(conn, g)
    condition_ev = evidence(conn, g)
    review_ev = evidence(conn, g)
    role = clone(conn, g, "condition_role", g["condition_role"],
                 role_code=f"technical role {revision}", evidence_id=shared)
    instrument = insert(conn, g, "instrument", instrument_code=f"technical instrument {revision}",
                        description="technical fixture", evidence_id=shared)
    condition = clone(conn, g, "experimental_condition", prior, revision=revision,
                      supersedes_id=prior, evidence_id=condition_ev)
    # An explicit unknown value has no annotation. Its role, instrument and
    # variable definition still belong to the review of the exact condition.
    component = clone(conn, g, "condition_component", g["condition_component"],
                      condition_id=condition, role_id=role, instrument_id=instrument,
                      instrument_status="identified", evidence_id=shared)
    condition_seal = seal(conn, g, "experimental_condition", pid=condition)
    reviewer = clone(conn, g, "review_event", g["review_event"], condition_id=condition,
                     evidence_id=review_ev, decision="approved")
    for role_name, edge in [
        ("condition_content", {"dependency_seal_id": condition_seal}),
        ("variable_definition", {"dependency_review_id": variable_review}),
    ]:
        insert(conn, g, "approval_dependency", owner_review_id=reviewer, entry_kind="decision",
               role=role_name, **edge)
    review_seal = seal(conn, g, "review_event", pid=reviewer)
    return dict(role=role, instrument=instrument, component=component, condition=condition,
                reviewer=reviewer, shared=shared, condition_ev=condition_ev, review_ev=review_ev,
                condition_seal=condition_seal, review_seal=review_seal)


@pytest.fixture
def reviewed(db, g):
    with db.begin() as conn:
        variable_review = g["var_review"]
        rows = new_condition(conn, g, g["experimental_condition"], 2, variable_review)
    return rows, variable_review


@pytest.mark.parametrize("table,target,assignment", [
    ("condition_role", "role", "variable_category='incompatible'"),
    ("condition_role", "role", "definition='changed meaning'"),
    ("instrument", "instrument", "instrument_code='changed instrument'"),
    ("evidence_reference", "condition_ev", "excerpt='changed scope'"),
    ("evidence_reference", "review_ev", "locator_key='changed location'"),
    ("evidence_reference", "shared", "verification_scope='changed verification'"),
    ("source_document", "source_document", "sha256=repeat('9',64)"),
])
@pytest.mark.parametrize("operation", ["update", "delete"])
def test_direct_mutation(db, g, reviewed, table, target, assignment, operation):
    identities, _ = reviewed
    key = (g | identities)[target]
    query = f"UPDATE {table} SET {assignment}" if operation == "update" else f"DELETE FROM {table}"
    with db.begin() as conn:
        original = read_row(conn, table, key)
        with pytest.raises(DBAPIError) as exc, conn.begin_nested():
            conn.execute(text(query + " WHERE id=:id"), {"id": key})
        assert exc.value.orig.sqlstate == "55000"
        assert read_row(conn, table, key) == original


def independent_seal(conn, inv, parent, pk, child, foreign_key, seal_id):
    member_ids = conn.execute(text(f"SELECT id FROM {child} WHERE investigation_id=:inv "
                                   f"AND {foreign_key}=:pk ORDER BY id"), dict(inv=inv, pk=pk)).scalars()
    members = [[child, str(inv), str(mid), canonical_row(conn, child, mid, inv)] for mid in member_ids]
    payload = expected_bytes(dict(parent=canonical_row(conn, parent, pk, inv), members=members))
    row = read_row(conn, "aggregate_seal", seal_id)
    assert row[foreign_key] == pk if foreign_key == "condition_id" else row["review_id"] == pk
    assert row["member_digest"] == sha256(payload).hexdigest()
    return row["id"], payload, row["member_digest"]


def test_populated_upgrade_successor_and_history(db, g):
    with pytest.raises(CommandError, match="explicit"), db.begin() as conn:
        migrate(conn, "downgrade", BASE)
    with db.begin() as conn:
        migrate(conn, "downgrade", BASE, True)
    with db.begin() as conn:
        variable_review = g["var_review"]
        original = new_condition(conn, g, g["experimental_condition"], 2, variable_review)
        result = clone(conn, g, "analytical_result", g["analytical_result"])
        clone(conn, g, "result_input", g["result_input"], result_id=result)
        eligibility = clone(conn, g, "analytical_eligibility", g["analytical_eligibility"],
                            condition_id=original["condition"], condition_review_id=original["reviewer"],
                            supersedes_id=g["analytical_eligibility"], revision=2)
        clone(conn, g, "result_condition", g["result_condition"], result_id=result,
              condition_id=original["condition"], eligibility_id=eligibility)
        seal(conn, g, "analytical_result", pid=result)
        owner, sid = build(conn, g | {"analytical_result": result})
        protocol_seal = seal(conn, g, "analysis_protocol")

    def audit(conn):
        r = original
        component = read_row(conn, "condition_component", r["component"])
        role = read_row(conn, "condition_role", component["role_id"])
        instrument = read_row(conn, "instrument", component["instrument_id"])
        assert role["evidence_id"] == instrument["evidence_id"] == component["evidence_id"] == r["shared"]
        return (
            component, role, instrument,
            [read_row(conn, "evidence_reference", r[k]) for k in ("shared","condition_ev","review_ev")],
            read_row(conn, "source_document", g["source_document"]),
            independent_seal(conn, g["investigation"], "experimental_condition", r["condition"],
                             "condition_component", "condition_id", r["condition_seal"]),
            independent_seal(conn, g["investigation"], "review_event", r["reviewer"],
                             "approval_dependency", "owner_review_id", r["review_seal"]),
            read_row(conn, "aggregate_seal", protocol_seal), history(conn, g, owner, sid),
        )

    with db.begin() as conn:
        before = audit(conn)
        assert before[-1] and current(conn, g, owner)
        migrate(conn, "upgrade", HEAD)
        config = migration_config()
        config.attributes["connection"] = conn
        command.check(config)
    with db.begin() as conn:
        assert audit(conn) == before
        successor = new_condition(conn, g, original["condition"], 3, variable_review)
        for field in original:
            assert original[field] != successor[field]
        comp = read_row(conn, "condition_component", successor["component"])
        assert (comp["role_id"],comp["instrument_id"]) == (successor["role"],successor["instrument"])
        review = read_row(conn, "review_event", successor["reviewer"])
        assert (review["condition_id"],review["decision"]) == (successor["condition"],"approved")
        assert read_row(conn,"aggregate_seal",successor["review_seal"])["review_id"] == review["id"]
    with db.begin() as conn:
        assert audit(conn) == before and current(conn, g, owner)


def test_truncate_cascade_rejected(db, reviewed):
    with db.begin() as conn:
        with pytest.raises(DBAPIError) as exc, conn.begin_nested():
            conn.exec_driver_sql("TRUNCATE public.evidence_reference CASCADE")
        assert exc.value.orig.sqlstate == "55000"


@pytest.mark.parametrize("action", ["edit", "delete", "share", "approval"])
def test_overlap(db, g, reviewed, action):
    original, variable_review = reviewed
    with db.begin() as conn:
        fresh = evidence(conn, g)
    started = Event()
    worker_pid = []

    def concurrent_operation():
        try:
            with db.begin() as conn:
                worker_pid.append(scalar(conn, "SELECT pg_backend_pid()"))
                started.set()
                if action == "share":
                    return insert(conn, g, "instrument", instrument_code=str(uuid4()),
                                  description="concurrent fixture", evidence_id=fresh)
                if action == "approval":
                    query = "UPDATE condition_role SET definition='changed' WHERE id=:id"
                    key = original["role"]
                else:
                    query = ("DELETE FROM evidence_reference" if action == "delete" else
                             "UPDATE evidence_reference SET excerpt='changed'") + " WHERE id=:id"
                    key = fresh
                conn.execute(text(query), {"id":key})
        except DBAPIError as exc:
            return exc.orig.sqlstate

    with ThreadPoolExecutor(max_workers=1) as pool, db.connect() as leader:
        with leader.begin():
            leader_pid = scalar(leader, "SELECT pg_backend_pid()")
            if action == "approval":
                successor = new_condition(leader, g, original["condition"], 3, variable_review)
            else:
                attached = clone(leader, g, "condition_role", original["role"], role_code=str(uuid4()), evidence_id=fresh)
            future = pool.submit(concurrent_operation)
            assert started.wait(10)
            # Non-key updates may reach the rejection trigger immediately. A
            # delete may wait on the FK KEY SHARE lock until attachment commits.
            with db.connect().execution_options(isolation_level="AUTOCOMMIT") as observer:
                deadline = monotonic() + 10
                while not future.done():
                    if scalar(observer, "SELECT :leader=ANY(pg_blocking_pids(:worker))",
                              leader=leader_pid, worker=worker_pid[0]):
                        break
                    assert monotonic() < deadline
                    sleep(0.02)
        outcome = future.result(timeout=10)
    with db.begin() as conn:
        if action == "approval":
            assert outcome == "55000"
            assert read_row(conn, "aggregate_seal", successor["review_seal"])["review_id"] == successor["reviewer"]
        else:
            assert read_row(conn, "condition_role", attached)["evidence_id"] == fresh
            assert read_row(conn, "evidence_reference", fresh)["excerpt"] != "changed"
            if action == "share":
                assert read_row(conn, "instrument", outcome)["evidence_id"] == fresh
            else:
                assert outcome == "55000"
