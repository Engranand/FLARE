"""Comprehensive tests for M4.5 remediation and N2 condition-policy matcher.

Covers:
1. Forward migration 0007 upgrade, confirmation-required downgrade, and re-upgrade.
2. Audit 1: Version-qualified role and instrument identities via identity service.
3. Audit 2: Condition approval lineage guard (check_condition_review) on aggregate_seal.
4. N2 Condition-Policy Matcher: Complete 12-case truth table and edge cases.
5. Historical Reference & Digest Preservation.
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from alembic import command
from alembic.util import CommandError
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.migrations import migration_config
from app.db.n2 import n2_matches, validate_n2_result
from app.services.identity import (
    IdentityValidationError,
    validate_identity_code,
)
from test_aggregate_sealing import (
    TABLES,
    db as old_db,
    graph,
    migrate,
    scalar,
    seal,
)
from test_n1_snapshot import clone, insert
from test_variable_immutability import approve, evidence, read_row

pytestmark = pytest.mark.postgres
BASE = "0006_evidence_immutability"
HEAD = "0007_m45_n2"


@pytest.fixture(scope="module")
def db(old_db):
    with old_db.begin() as conn:
        migrate(conn, "upgrade", HEAD)
        assert scalar(conn, "show server_version_num") == "170011"
    return old_db


# ============================================================================
# PART 1: Migration 0007 Lifecycle Tests
# ============================================================================


def test_migration_0007_lifecycle(db):
    """Test 0007 downgrade requires confirmation and re-upgrade succeeds."""
    with db.begin() as conn:
        with pytest.raises(CommandError, match="explicit"):
            migrate(conn, "downgrade", BASE)

    with db.begin() as conn:
        migrate(conn, "downgrade", BASE, confirmed=True)
        assert scalar(conn, "SELECT to_regnamespace('flare_n2')") is None

    with db.begin() as conn:
        migrate(conn, "upgrade", HEAD)
        assert scalar(conn, "SELECT to_regnamespace('flare_n2')") is not None
        config = migration_config()
        config.attributes["connection"] = conn
        command.check(config)


# ============================================================================
# PART 2: Audit 1 Service Layer Tests
# ============================================================================


def test_version_qualified_code_validation():
    """Verify version-qualified role and instrument identities."""
    from app.services.identity import parse_code_version

    # Base codes (version 1)
    validate_identity_code("airflow_sensor", [])
    validate_identity_code("radiometer_gain", [])
    assert parse_code_version("airflow_sensor") == ("airflow_sensor", None)

    # Successor codes with explicit _v<N>
    validate_identity_code("airflow_sensor_v2", ["airflow_sensor"])
    validate_identity_code("airflow_sensor_v3", ["airflow_sensor", "airflow_sensor_v2"])
    assert parse_code_version("airflow_sensor_v2") == ("airflow_sensor", 2)
    assert parse_code_version("airflow_sensor_v3") == ("airflow_sensor", 3)

    # Prohibited non-versioned duplicate
    with pytest.raises(IdentityValidationError, match="already registered"):
        validate_identity_code("airflow_sensor", ["airflow_sensor"])

    # Prohibited backward or equal versions
    with pytest.raises(IdentityValidationError, match="must be greater than"):
        validate_identity_code("airflow_sensor_v2", ["airflow_sensor", "airflow_sensor_v3"])

    # Prohibited version suffix v1
    with pytest.raises(IdentityValidationError, match="_v2 or higher"):
        validate_identity_code("airflow_sensor_v1", ["airflow_sensor"])

    # Prohibited unversioned correction of versioned base
    with pytest.raises(IdentityValidationError, match="cannot correct existing"):
        validate_identity_code("airflow_sensor", ["airflow_sensor_v2"])


# ============================================================================
# PART 3: Audit 2 Condition Approval Lineage Guard Tests
# ============================================================================


def new_audited_condition(conn, g, prior, revision, variable_review, *,
                         status="identified", stability="stable"):
    """Helper to create an experimental condition with full approval dependencies."""
    shared = evidence(conn, g)
    condition_ev = evidence(conn, g)
    review_ev = evidence(conn, g)
    role = clone(conn, g, "condition_role", g["condition_role"],
                 role_code=f"audited_role_{revision}_{uuid4().hex[:6]}", evidence_id=shared)
    inst = insert(conn, g, "instrument",
                  instrument_code=f"audited_inst_{revision}_{uuid4().hex[:6]}",
                  description="fixture instrument", evidence_id=shared)
    inst_id = inst if status == "identified" else None
    cond = clone(conn, g, "experimental_condition", prior, revision=revision,
                 supersedes_id=prior, airflow_stability=stability, evidence_id=condition_ev)
    comp = clone(conn, g, "condition_component", g["condition_component"],
                 condition_id=cond, role_id=role, instrument_id=inst_id,
                 instrument_status=status, evidence_id=shared)
    cond_seal = seal(conn, g, "experimental_condition", pid=cond)
    reviewer = clone(conn, g, "review_event", g["review_event"], condition_id=cond,
                     evidence_id=review_ev, decision="approved")
    for role_name, edge in [
        ("condition_content", {"dependency_seal_id": cond_seal}),
        ("variable_definition", {"dependency_review_id": variable_review}),
    ]:
        insert(conn, g, "approval_dependency", owner_review_id=reviewer, entry_kind="decision",
               role=role_name, **edge)
    review_seal = seal(conn, g, "review_event", pid=reviewer)
    return dict(role=role, instrument=inst, component=comp, condition=cond,
                reviewer=reviewer, shared=shared, condition_ev=condition_ev,
                review_ev=review_ev, condition_seal=cond_seal, review_seal=review_seal)


def test_condition_approval_lineage_positive(db):
    """Positive: Condition review with condition_content seal and approved/sealed variable review passes."""
    with db.begin() as conn:
        g, _ = graph(conn, n1=True)
        var_rev = approve(conn, g, g["scientific_variable"], g["evidence_reference"])
        created = new_audited_condition(conn, g, g["experimental_condition"], 2, var_rev)
        assert created["review_seal"] is not None


def test_condition_approval_lineage_missing_content_seal(db):
    """Negative: Condition review lacks condition_content dependency -> SQLSTATE 23514."""
    with db.begin() as conn:
        g, _ = graph(conn, n1=True)
        var_rev = approve(conn, g, g["scientific_variable"], g["evidence_reference"])
        shared = evidence(conn, g)
        condition_ev = evidence(conn, g)
        review_ev = evidence(conn, g)

        role = clone(conn, g, "condition_role", g["condition_role"],
                     role_code=f"test_role_{uuid4().hex[:6]}", evidence_id=shared)
        inst = insert(conn, g, "instrument", instrument_code=f"test_inst_{uuid4().hex[:6]}",
                      description="test inst", evidence_id=shared)
        cond = clone(conn, g, "experimental_condition", g["experimental_condition"], revision=2,
                     supersedes_id=g["experimental_condition"], evidence_id=condition_ev)
        clone(conn, g, "condition_component", g["condition_component"],
              condition_id=cond, role_id=role, instrument_id=inst,
              instrument_status="identified", evidence_id=shared)
        seal(conn, g, "experimental_condition", pid=cond)

        cond_rev = clone(conn, g, "review_event", g["review_event"], condition_id=cond,
                         evidence_id=review_ev, decision="approved")
        # Attach only variable_definition, omit condition_content
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="variable_definition", dependency_review_id=var_rev)

        with pytest.raises(DBAPIError) as exc:
            seal(conn, g, "review_event", pid=cond_rev)
        assert exc.value.orig.sqlstate == "23514"
        assert "condition_content" in str(exc.value)


def test_condition_approval_lineage_missing_variable_review(db):
    """Negative: Condition component variable has no variable_definition dependency -> SQLSTATE 23514."""
    with db.begin() as conn:
        g, _ = graph(conn, n1=True)
        shared = evidence(conn, g)
        condition_ev = evidence(conn, g)
        review_ev = evidence(conn, g)

        role = clone(conn, g, "condition_role", g["condition_role"],
                     role_code=f"test_role_{uuid4().hex[:6]}", evidence_id=shared)
        inst = insert(conn, g, "instrument", instrument_code=f"test_inst_{uuid4().hex[:6]}",
                      description="test inst", evidence_id=shared)
        cond = clone(conn, g, "experimental_condition", g["experimental_condition"], revision=2,
                     supersedes_id=g["experimental_condition"], evidence_id=condition_ev)
        clone(conn, g, "condition_component", g["condition_component"],
              condition_id=cond, role_id=role, instrument_id=inst,
              instrument_status="identified", evidence_id=shared)
        cond_seal = seal(conn, g, "experimental_condition", pid=cond)

        cond_rev = clone(conn, g, "review_event", g["review_event"], condition_id=cond,
                         evidence_id=review_ev, decision="approved")
        # Attach condition_content, but omit variable_definition
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="condition_content", dependency_seal_id=cond_seal)

        with pytest.raises(DBAPIError) as exc:
            seal(conn, g, "review_event", pid=cond_rev)
        assert exc.value.orig.sqlstate == "23514"
        assert "variable_definition" in str(exc.value)


def test_condition_approval_lineage_unapproved_variable_review(db):
    """Negative: Variable definition review decision is rejected -> SQLSTATE 23514."""
    with db.begin() as conn:
        g, _ = graph(conn, n1=True)
        shared = evidence(conn, g)
        condition_ev = evidence(conn, g)
        review_ev = evidence(conn, g)

        # Rejected variable review
        var_rev = insert(conn, g, "review_event",
                         variable_id=g["scientific_variable"], revision=1, decision="rejected",
                         rationale="rejected definition", reviewer_ref="auditor",
                         reviewed_at=datetime.now(timezone.utc), evidence_id=shared)
        seal(conn, g, "review_event", pid=var_rev)

        role = clone(conn, g, "condition_role", g["condition_role"],
                     role_code=f"test_role_{uuid4().hex[:6]}", evidence_id=shared)
        inst = insert(conn, g, "instrument", instrument_code=f"test_inst_{uuid4().hex[:6]}",
                      description="test inst", evidence_id=shared)
        cond = clone(conn, g, "experimental_condition", g["experimental_condition"], revision=2,
                     supersedes_id=g["experimental_condition"], evidence_id=condition_ev)
        clone(conn, g, "condition_component", g["condition_component"],
              condition_id=cond, role_id=role, instrument_id=inst,
              instrument_status="identified", evidence_id=shared)
        cond_seal = seal(conn, g, "experimental_condition", pid=cond)

        cond_rev = clone(conn, g, "review_event", g["review_event"], condition_id=cond,
                         evidence_id=review_ev, decision="approved")
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="condition_content", dependency_seal_id=cond_seal)
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="variable_definition", dependency_review_id=var_rev)

        with pytest.raises(DBAPIError) as exc:
            seal(conn, g, "review_event", pid=cond_rev)
        assert exc.value.orig.sqlstate == "23514"
        assert "not approved" in str(exc.value)


def test_condition_approval_lineage_unsealed_variable_review(db):
    """Negative: Variable definition review is not sealed -> SQLSTATE 23514."""
    with db.begin() as conn:
        g, _ = graph(conn, n1=True)
        shared = evidence(conn, g)
        condition_ev = evidence(conn, g)
        review_ev = evidence(conn, g)

        # Unsealed variable review (approved, but no seal)
        var_rev = insert(conn, g, "review_event",
                         variable_id=g["scientific_variable"], revision=1, decision="approved",
                         rationale="unsealed definition", reviewer_ref="auditor",
                         reviewed_at=datetime.now(timezone.utc), evidence_id=shared)

        role = clone(conn, g, "condition_role", g["condition_role"],
                     role_code=f"test_role_{uuid4().hex[:6]}", evidence_id=shared)
        inst = insert(conn, g, "instrument", instrument_code=f"test_inst_{uuid4().hex[:6]}",
                      description="test inst", evidence_id=shared)
        cond = clone(conn, g, "experimental_condition", g["experimental_condition"], revision=2,
                     supersedes_id=g["experimental_condition"], evidence_id=condition_ev)
        clone(conn, g, "condition_component", g["condition_component"],
              condition_id=cond, role_id=role, instrument_id=inst,
              instrument_status="identified", evidence_id=shared)
        cond_seal = seal(conn, g, "experimental_condition", pid=cond)

        cond_rev = clone(conn, g, "review_event", g["review_event"], condition_id=cond,
                         evidence_id=review_ev, decision="approved")
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="condition_content", dependency_seal_id=cond_seal)
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="variable_definition", dependency_review_id=var_rev)

        with pytest.raises(DBAPIError) as exc:
            seal(conn, g, "review_event", pid=cond_rev)
        assert exc.value.orig.sqlstate == "23514"
        assert "not sealed" in str(exc.value)


def test_condition_approval_lineage_superseded_variable_review(db):
    """Negative: Pinned variable definition review revision is superseded -> SQLSTATE 23514."""
    with db.begin() as conn:
        g, _ = graph(conn, n1=True)
        shared = evidence(conn, g)
        condition_ev = evidence(conn, g)
        review_ev = evidence(conn, g)

        var_rev_1 = approve(conn, g, g["scientific_variable"], shared)
        var_rev_2 = insert(conn, g, "review_event",
                           variable_id=g["scientific_variable"], revision=2, supersedes_id=var_rev_1,
                           decision="approved", rationale="updated revision",
                           reviewer_ref="auditor", reviewed_at=datetime.now(timezone.utc),
                           evidence_id=shared)
        seal(conn, g, "review_event", pid=var_rev_2)

        role = clone(conn, g, "condition_role", g["condition_role"],
                     role_code=f"test_role_{uuid4().hex[:6]}", evidence_id=shared)
        inst = insert(conn, g, "instrument", instrument_code=f"test_inst_{uuid4().hex[:6]}",
                      description="test inst", evidence_id=shared)
        cond = clone(conn, g, "experimental_condition", g["experimental_condition"], revision=2,
                     supersedes_id=g["experimental_condition"], evidence_id=condition_ev)
        clone(conn, g, "condition_component", g["condition_component"],
              condition_id=cond, role_id=role, instrument_id=inst,
              instrument_status="identified", evidence_id=shared)
        cond_seal = seal(conn, g, "experimental_condition", pid=cond)

        cond_rev = clone(conn, g, "review_event", g["review_event"], condition_id=cond,
                         evidence_id=review_ev, decision="approved")
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="condition_content", dependency_seal_id=cond_seal)
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="variable_definition", dependency_review_id=var_rev_1)

        with pytest.raises(DBAPIError) as exc:
            seal(conn, g, "review_event", pid=cond_rev)
        assert exc.value.orig.sqlstate == "23514"
        assert "superseded" in str(exc.value)


def test_condition_approval_zero_dependencies_rejected(db):
    """Negative: Approved condition review with zero dependencies fails -> SQLSTATE 23514."""
    with db.begin() as conn:
        g, _ = graph(conn, n1=True)
        shared = evidence(conn, g)
        condition_ev = evidence(conn, g)
        review_ev = evidence(conn, g)

        role = clone(conn, g, "condition_role", g["condition_role"],
                     role_code=f"test_role_{uuid4().hex[:6]}", evidence_id=shared)
        inst = insert(conn, g, "instrument", instrument_code=f"test_inst_{uuid4().hex[:6]}",
                      description="test inst", evidence_id=shared)
        cond = clone(conn, g, "experimental_condition", g["experimental_condition"], revision=2,
                     supersedes_id=g["experimental_condition"], evidence_id=condition_ev)
        clone(conn, g, "condition_component", g["condition_component"],
              condition_id=cond, role_id=role, instrument_id=inst,
              instrument_status="identified", evidence_id=shared)
        seal(conn, g, "experimental_condition", pid=cond)

        cond_rev = clone(conn, g, "review_event", g["review_event"], condition_id=cond,
                         evidence_id=review_ev, decision="approved")
        # Zero dependencies attached

        with pytest.raises(DBAPIError) as exc:
            seal(conn, g, "review_event", pid=cond_rev)
        assert exc.value.orig.sqlstate == "23514"
        assert "condition_content" in str(exc.value)


def test_condition_zero_components_requires_content_seal(db):
    """Condition with 0 components still requires condition_content dependency; succeeds with it."""
    with db.begin() as conn:
        g, _ = graph(conn, n1=True)
        condition_ev = evidence(conn, g)
        review_ev = evidence(conn, g)

        # Condition with no components
        cond = clone(conn, g, "experimental_condition", g["experimental_condition"], revision=2,
                     supersedes_id=g["experimental_condition"], evidence_id=condition_ev)
        cond_seal = seal(conn, g, "experimental_condition", pid=cond)

        # 1. Try sealing with zero dependencies -> fails
        cond_rev = clone(conn, g, "review_event", g["review_event"], condition_id=cond,
                         evidence_id=review_ev, decision="approved")
        with pytest.raises(DBAPIError) as exc, conn.begin_nested():
            seal(conn, g, "review_event", pid=cond_rev)
        assert exc.value.orig.sqlstate == "23514"
        assert "condition_content" in str(exc.value)

        # 2. Add condition_content seal dependency -> succeeds without variable_definition (0 components)
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="condition_content", dependency_seal_id=cond_seal)
        rev_seal = seal(conn, g, "review_event", pid=cond_rev)
        assert rev_seal is not None


def test_condition_approval_wrong_condition_seal_rejected(db):
    """Negative: condition_content dependency points to seal of a different condition -> SQLSTATE 23514."""
    with db.begin() as conn:
        g, _ = graph(conn, n1=True)
        shared = evidence(conn, g)
        condition_ev = evidence(conn, g)
        review_ev = evidence(conn, g)
        var_rev = approve(conn, g, g["scientific_variable"], shared)

        # Condition 1
        cond1 = clone(conn, g, "experimental_condition", g["experimental_condition"], revision=2,
                      supersedes_id=g["experimental_condition"], evidence_id=condition_ev)
        clone(conn, g, "condition_component", g["condition_component"],
              condition_id=cond1, evidence_id=shared)
        seal(conn, g, "experimental_condition", pid=cond1)

        # Condition 2
        cond2 = clone(conn, g, "experimental_condition", g["experimental_condition"], revision=3,
                      supersedes_id=cond1, evidence_id=condition_ev)
        cond2_seal = seal(conn, g, "experimental_condition", pid=cond2)

        # Review is for cond1, but points to cond2's seal
        cond_rev = clone(conn, g, "review_event", g["review_event"], condition_id=cond1,
                         evidence_id=review_ev, decision="approved")
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="condition_content", dependency_seal_id=cond2_seal)
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="variable_definition", dependency_review_id=var_rev)

        with pytest.raises(DBAPIError) as exc:
            seal(conn, g, "review_event", pid=cond_rev)
        assert exc.value.orig.sqlstate == "23514"
        assert "condition_content" in str(exc.value)


def test_condition_approval_wrong_variable_review_rejected(db):
    """Negative: variable_definition dependency references wrong variable -> SQLSTATE 23514."""
    with db.begin() as conn:
        g, _ = graph(conn, n1=True)
        shared = evidence(conn, g)
        condition_ev = evidence(conn, g)
        review_ev = evidence(conn, g)

        # Other variable
        other_var = clone(conn, g, "scientific_variable", g["scientific_variable"],
                          variable_code=f"other_var_{uuid4().hex[:6]}")
        other_var_rev = approve(conn, g, other_var, shared)

        cond = clone(conn, g, "experimental_condition", g["experimental_condition"], revision=2,
                     supersedes_id=g["experimental_condition"], evidence_id=condition_ev)
        clone(conn, g, "condition_component", g["condition_component"],
              condition_id=cond, variable_id=g["scientific_variable"], evidence_id=shared)
        cond_seal = seal(conn, g, "experimental_condition", pid=cond)

        cond_rev = clone(conn, g, "review_event", g["review_event"], condition_id=cond,
                         evidence_id=review_ev, decision="approved")
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="condition_content", dependency_seal_id=cond_seal)
        # Point to wrong variable's review
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="variable_definition", dependency_review_id=other_var_rev)

        with pytest.raises(DBAPIError) as exc:
            seal(conn, g, "review_event", pid=cond_rev)
        assert exc.value.orig.sqlstate == "23514"
        assert "variable_definition" in str(exc.value)


def test_condition_approval_multiple_components_all_reviews_required(db):
    """Condition with multiple components requires valid review dependencies for all variables."""
    with db.begin() as conn:
        g, _ = graph(conn, n1=True)
        shared = evidence(conn, g)
        condition_ev = evidence(conn, g)
        review_ev = evidence(conn, g)

        var1 = g["scientific_variable"]
        var1_rev = approve(conn, g, var1, shared)

        var2 = clone(conn, g, "scientific_variable", g["scientific_variable"],
                     variable_code=f"multivar_{uuid4().hex[:6]}")
        var2_rev = approve(conn, g, var2, shared)

        role1 = clone(conn, g, "condition_role", g["condition_role"],
                      role_code=f"role1_{uuid4().hex[:6]}", evidence_id=shared)
        role2 = clone(conn, g, "condition_role", g["condition_role"],
                      role_code=f"role2_{uuid4().hex[:6]}", evidence_id=shared)

        cond = clone(conn, g, "experimental_condition", g["experimental_condition"], revision=2,
                     supersedes_id=g["experimental_condition"], evidence_id=condition_ev)
        clone(conn, g, "condition_component", g["condition_component"],
              condition_id=cond, slot=1, role_id=role1, variable_id=var1, evidence_id=shared)
        clone(conn, g, "condition_component", g["condition_component"],
              condition_id=cond, slot=2, role_id=role2, variable_id=var2, evidence_id=shared)
        cond_seal = seal(conn, g, "experimental_condition", pid=cond)

        # 1. Attach only var1 review -> fails because var2 is missing
        cond_rev = clone(conn, g, "review_event", g["review_event"], condition_id=cond,
                         evidence_id=review_ev, decision="approved")
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="condition_content", dependency_seal_id=cond_seal)
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="variable_definition", dependency_review_id=var1_rev)

        with pytest.raises(DBAPIError) as exc, conn.begin_nested():
            seal(conn, g, "review_event", pid=cond_rev)
        assert exc.value.orig.sqlstate == "23514"
        assert "variable_definition" in str(exc.value)

        # 2. Attach var2 review -> succeeds
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="variable_definition", dependency_review_id=var2_rev)
        rev_seal = seal(conn, g, "review_event", pid=cond_rev)
        assert rev_seal is not None


# ============================================================================
# PART 4: N2 Condition-Policy Matcher Truth Table Tests (12 Cases)
# ============================================================================


def build_n2_suite(conn, *,
                   instrument_policy="not_required",
                   stability_policy="not_applicable",
                   has_condition_role=False,
                   provide_condition=True,
                   instrument_status="identified",
                   airflow_stability="stable",
                   condition_role_count=1):
    """Build an N2 environment on top of graph() with parameterizable policies."""
    g, _ = graph(conn, n1=True)
    inv = g["investigation"]
    ev = g["evidence_reference"]
    now = datetime.now(timezone.utc)

    # 1. Variable and variable approval
    var_rev = approve(conn, g, g["scientific_variable"], ev)

    # 2. Documented condition segment
    seg = clone(conn, g, "condition_segment", g["condition_segment"],
                scope_status="documented", segment_key="doc_seg")

    # 3. Annotation with exact matching unit and phase
    ann = clone(conn, g, "semantic_annotation", g["semantic_annotation"],
                interpretation_key=f"interp_{uuid4().hex[:6]}",
                interpreted_unit="m/s", unit_status="known",
                observed_phase="not_applicable")

    # 4. Protocol & Input Requirement
    protocol = clone(conn, g, "analysis_protocol", g["analysis_protocol"],
                     protocol_code=f"prot_{uuid4().hex[:6]}")
    req_in = insert(conn, g, "protocol_requirement",
                    protocol_id=protocol,
                    requirement_key="req_speed",
                    target_kind="input",
                    variable_id=g["scientific_variable"],
                    phase="not_applicable",
                    min_count=1, max_count=1,
                    value_policy="numeric_only",
                    stability_policy=stability_policy,
                    instrument_policy=instrument_policy,
                    evidence_id=ev)
    insert(conn, g, "protocol_unit_rule",
           requirement_id=req_in, unit_text="m/s", unit_basis="fixture",
           method="fixture", method_version="1", evidence_id=ev)

    cond_role_id = None
    cond_var_id = None
    cond_var_rev = None
    if has_condition_role:
        cond_role_id = clone(conn, g, "condition_role", g["condition_role"],
                             role_code=f"cond_role_{uuid4().hex[:6]}")
        cond_var_id = clone(conn, g, "scientific_variable", g["scientific_variable"],
                            variable_code=f"cond_var_{uuid4().hex[:6]}")
        cond_var_rev = approve(conn, g, cond_var_id, ev)
        creq = insert(conn, g, "protocol_requirement",
                      protocol_id=protocol,
                      requirement_key="req_chamber",
                      target_kind="condition",
                      variable_id=cond_var_id,
                      role_id=cond_role_id,
                      phase="not_applicable",
                      min_count=1, max_count=1,
                      value_policy="numeric_only",
                      stability_policy=stability_policy,
                      instrument_policy=instrument_policy,
                      evidence_id=ev)
        insert(conn, g, "protocol_unit_rule",
               requirement_id=creq, unit_text="m/s", unit_basis="fixture",
               method="fixture", method_version="1", evidence_id=ev)

    seal(conn, g, "analysis_protocol", pid=protocol)

    # 5. Result
    result = clone(conn, g, "analytical_result", g["analytical_result"],
                   protocol_id=protocol)

    # 6. Input eligibility
    input_elig = insert(
        conn, g, "analytical_eligibility",
        protocol_id=protocol,
        revision=1,
        observation_id=g["observation"],
        experimental_test_id=None,
        segment_id=None,
        condition_id=None,
        condition_review_id=None,
        eligibility_status="needs_review",
        reason="fixture",
        reviewer_ref="fixture",
        reviewed_at=now,
        evidence_id=ev,
    )
    clone(conn, g, "result_input", g["result_input"],
          result_id=result, segment_id=seg, annotation_id=ann,
          input_role="req_speed", eligibility_id=input_elig)

    # 7. Condition (if provided)
    cond = None
    if provide_condition:
        cond = clone(conn, g, "experimental_condition", g["experimental_condition"],
                     segment_id=seg, segment_key="doc_seg", airflow_stability=airflow_stability)

        inst = insert(conn, g, "instrument", instrument_code=f"inst_{uuid4().hex[:6]}",
                      description="test sensor", evidence_id=ev)
        inst_id = inst if instrument_status == "identified" else None

        # Input matching component
        clone(conn, g, "condition_component", g["condition_component"],
              condition_id=cond, annotation_id=ann, variable_id=g["scientific_variable"],
              instrument_id=inst_id, instrument_status=instrument_status,
              value_status="known")

        # Condition role component if requested
        if has_condition_role and condition_role_count > 0:
            for s in range(1, condition_role_count + 1):
                insert(conn, g, "condition_component",
                       condition_id=cond, role_id=cond_role_id, slot=s + 1,
                       instrument_id=inst_id, instrument_status=instrument_status,
                       variable_id=cond_var_id, value_status="unknown", evidence_id=ev)

        cond_seal = seal(conn, g, "experimental_condition", pid=cond)

        cond_rev = clone(conn, g, "review_event", g["review_event"], condition_id=cond,
                         decision="approved")
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="condition_content", dependency_seal_id=cond_seal)
        insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
               role="variable_definition", dependency_review_id=var_rev)
        if has_condition_role:
            insert(conn, g, "approval_dependency", owner_review_id=cond_rev, entry_kind="decision",
                   role="variable_definition", dependency_review_id=cond_var_rev)
        seal(conn, g, "review_event", pid=cond_rev)

        cond_elig = insert(conn, g, "analytical_eligibility",
                           protocol_id=protocol, revision=1,
                           experimental_test_id=g["experimental_test"],
                           segment_id=seg, condition_id=cond, condition_review_id=cond_rev,
                           eligibility_status="eligible", reason="verified",
                           reviewer_ref="auditor", reviewed_at=now, evidence_id=ev)
        clone(conn, g, "result_condition", g["result_condition"],
              result_id=result, condition_id=cond, eligibility_id=cond_elig)

    seal(conn, g, "analytical_result", pid=result)
    return dict(investigation=inv, result=result, condition=cond, g=g)


# Case 1 (C=0): not_required, not_applicable -> Empty ResultCondition permitted (True)
def test_truth_table_case_1_empty_permitted(db):
    with db.begin() as conn:
        b = build_n2_suite(conn,
                           instrument_policy="not_required",
                           stability_policy="not_applicable",
                           has_condition_role=False,
                           provide_condition=False)

    assert n2_matches(db, b["investigation"], b["result"]) is True


# Case 1 (C=1): not_required, not_applicable -> Empty ResultCondition rejected (False)
def test_truth_table_case_1_c1_empty_rejected(db):
    with db.begin() as conn:
        b = build_n2_suite(conn,
                           instrument_policy="not_required",
                           stability_policy="not_applicable",
                           has_condition_role=True,
                           provide_condition=False)

    assert n2_matches(db, b["investigation"], b["result"]) is False


# Case 2: identified_required, not_applicable, C=0
def test_truth_table_case_2_identified_instrument(db):
    with db.begin() as conn:
        b_pass = build_n2_suite(conn,
                                instrument_policy="identified_required",
                                stability_policy="not_applicable",
                                instrument_status="identified")

    assert n2_matches(db, b_pass["investigation"], b_pass["result"]) is True

    with db.begin() as conn:
        b_fail = build_n2_suite(conn,
                                instrument_policy="identified_required",
                                stability_policy="not_applicable",
                                instrument_status="unknown")

    assert n2_matches(db, b_fail["investigation"], b_fail["result"]) is False


# Case 3: not_required, transient_allowed, C=0
def test_truth_table_case_3_transient_allowed(db):
    with db.begin() as conn:
        b_trans = build_n2_suite(conn,
                                 instrument_policy="not_required",
                                 stability_policy="transient_allowed",
                                 airflow_stability="transient",
                                 instrument_status="unknown")

    assert n2_matches(db, b_trans["investigation"], b_trans["result"]) is True

    with db.begin() as conn:
        b_unknown = build_n2_suite(conn,
                                   instrument_policy="not_required",
                                   stability_policy="transient_allowed",
                                   airflow_stability="unknown",
                                   instrument_status="unknown")

    assert n2_matches(db, b_unknown["investigation"], b_unknown["result"]) is False


# Case 4: identified_required, transient_allowed, C=0
def test_truth_table_case_4_identified_transient(db):
    with db.begin() as conn:
        b_pass = build_n2_suite(conn,
                                instrument_policy="identified_required",
                                stability_policy="transient_allowed",
                                instrument_status="identified",
                                airflow_stability="transient")

    assert n2_matches(db, b_pass["investigation"], b_pass["result"]) is True


# Case 5: not_required, stable_required, C=0
def test_truth_table_case_5_stable_required(db):
    with db.begin() as conn:
        b_pass = build_n2_suite(conn,
                                instrument_policy="not_required",
                                stability_policy="stable_required",
                                airflow_stability="stable",
                                instrument_status="unknown")

    assert n2_matches(db, b_pass["investigation"], b_pass["result"]) is True

    with db.begin() as conn:
        b_fail = build_n2_suite(conn,
                                instrument_policy="not_required",
                                stability_policy="stable_required",
                                airflow_stability="transient",
                                instrument_status="unknown")

    assert n2_matches(db, b_fail["investigation"], b_fail["result"]) is False


# Case 6: identified_required, stable_required, C=0
def test_truth_table_case_6_identified_stable(db):
    with db.begin() as conn:
        b_pass = build_n2_suite(conn,
                                instrument_policy="identified_required",
                                stability_policy="stable_required",
                                instrument_status="identified",
                                airflow_stability="stable")

    assert n2_matches(db, b_pass["investigation"], b_pass["result"]) is True


# Cases 7-12 (C=1): Condition-Role Requirements Declared
@pytest.mark.parametrize("inst_pol,stab_pol,inst_stat,stab,expect_match", [
    ("not_required", "not_applicable", "unknown", "unknown", True),     # Case 7
    ("identified_required", "not_applicable", "identified", "unknown", True),  # Case 8
    ("identified_required", "not_applicable", "unknown", "unknown", False),    # Case 8 fail
    ("not_required", "transient_allowed", "unknown", "transient", True), # Case 9
    ("identified_required", "transient_allowed", "identified", "transient", True), # Case 10
    ("not_required", "stable_required", "unknown", "stable", True),     # Case 11
    ("not_required", "stable_required", "unknown", "transient", False), # Case 11 fail
    ("identified_required", "stable_required", "identified", "stable", True), # Case 12
    ("identified_required", "stable_required", "identified", "transient", False), # Case 12 fail
])
def test_truth_table_cases_7_to_12(db, inst_pol, stab_pol, inst_stat, stab, expect_match):
    with db.begin() as conn:
        b = build_n2_suite(conn,
                           instrument_policy=inst_pol,
                           stability_policy=stab_pol,
                           has_condition_role=True,
                           provide_condition=True,
                           instrument_status=inst_stat,
                           airflow_stability=stab,
                           condition_role_count=1)

    assert n2_matches(db, b["investigation"], b["result"]) is expect_match


def test_condition_role_cardinality_violation(db):
    """Condition-role requirement cardinality: min_count not met -> fails."""
    with db.begin() as conn:
        b = build_n2_suite(conn,
                           instrument_policy="not_required",
                           stability_policy="not_applicable",
                           has_condition_role=True,
                           provide_condition=True,
                           condition_role_count=0)

    assert n2_matches(db, b["investigation"], b["result"]) is False
    diag = validate_n2_result(db, b["investigation"], b["result"])
    failed = [d for d in diag if not d["passed"]]
    assert any(d["rule"] == "condition_role_requirements" for d in failed)


# ============================================================================
# PART 4B: N2 Review-Head Freshness Tests
# ============================================================================


def test_n2_superseded_condition_review_rejected(db):
    """N2 rejects analytical_result when condition_review in eligibility is superseded."""
    with db.begin() as conn:
        b = build_n2_suite(conn,
                           instrument_policy="identified_required",
                           stability_policy="stable_required",
                           instrument_status="identified",
                           airflow_stability="stable")

    # Positive baseline
    assert n2_matches(db, b["investigation"], b["result"]) is True

    # Now create revision 2 of the condition review
    with db.begin() as conn:
        g = b["g"]
        # Find the existing condition review
        old_rev_id = scalar(conn,
            "SELECT ae.condition_review_id FROM public.result_condition rc "
            "JOIN public.analytical_eligibility ae ON (ae.investigation_id, ae.id) = (rc.investigation_id, rc.eligibility_id) "
            "WHERE rc.result_id = :r", r=b["result"])

        # Create revision 2
        rev2 = clone(conn, g, "review_event", old_rev_id,
                     revision=2, supersedes_id=old_rev_id, decision="approved",
                     reviewer_ref="auditor_v2", reviewed_at=datetime.now(timezone.utc))
        # Re-attach dependencies & seal rev2
        for dep in conn.execute(text("SELECT * FROM public.approval_dependency WHERE owner_review_id=:o"), dict(o=old_rev_id)).mappings():
            insert(conn, g, "approval_dependency", owner_review_id=rev2, entry_kind=dep["entry_kind"],
                   role=dep["role"], dependency_review_id=dep["dependency_review_id"],
                   dependency_seal_id=dep["dependency_seal_id"])
        seal(conn, g, "review_event", pid=rev2)

    # N2 must reject because analytical_eligibility still points to old_rev_id (not current head)
    assert n2_matches(db, b["investigation"], b["result"]) is False
    diag = validate_n2_result(db, b["investigation"], b["result"])
    failed = [d for d in diag if not d["passed"]]
    assert any(d["rule"] == "condition_approval_and_eligibility" for d in failed)


def test_n2_superseded_variable_review_rejected(db):
    """N2 rejects analytical_result when a component variable_definition review is superseded."""
    with db.begin() as conn:
        b = build_n2_suite(conn,
                           instrument_policy="identified_required",
                           stability_policy="stable_required",
                           instrument_status="identified",
                           airflow_stability="stable")

    # Positive baseline
    assert n2_matches(db, b["investigation"], b["result"]) is True

    # Supersede the variable review
    with db.begin() as conn:
        g = b["g"]
        shared = evidence(conn, g)
        var_id = scalar(conn,
            "SELECT k.variable_id FROM public.result_condition rc "
            "JOIN public.condition_component k ON (k.investigation_id, k.condition_id) = (rc.investigation_id, rc.condition_id) "
            "WHERE rc.result_id = :r LIMIT 1", r=b["result"])
        old_var_rev = read_row(conn, "review_event",
            scalar(conn, "SELECT id FROM public.review_event WHERE variable_id=:v ORDER BY revision DESC LIMIT 1", v=var_id))

        new_var_rev = insert(conn, g, "review_event",
                             variable_id=var_id, revision=old_var_rev["revision"] + 1,
                             supersedes_id=old_var_rev["id"], decision="approved",
                             rationale="updated variable review", reviewer_ref="auditor",
                             reviewed_at=datetime.now(timezone.utc), evidence_id=shared)
        seal(conn, g, "review_event", pid=new_var_rev)

    # N2 must reject because the condition review's dependency is now superseded
    assert n2_matches(db, b["investigation"], b["result"]) is False
    diag = validate_n2_result(db, b["investigation"], b["result"])
    failed = [d for d in diag if not d["passed"]]
    assert any(d["rule"] == "condition_approval_and_eligibility" for d in failed)


def test_n2_draft_new_revision_fails_closed(db):
    """N2 fails closed when an unsealed needs_review draft head exists for a variable."""
    with db.begin() as conn:
        b = build_n2_suite(conn,
                           instrument_policy="identified_required",
                           stability_policy="stable_required",
                           instrument_status="identified",
                           airflow_stability="stable")

    # Positive baseline
    assert n2_matches(db, b["investigation"], b["result"]) is True

    # Insert unsealed 'needs_review' draft head for the variable
    with db.begin() as conn:
        g = b["g"]
        shared = evidence(conn, g)
        var_id = scalar(conn,
            "SELECT k.variable_id FROM public.result_condition rc "
            "JOIN public.condition_component k ON (k.investigation_id, k.condition_id) = (rc.investigation_id, rc.condition_id) "
            "WHERE rc.result_id = :r LIMIT 1", r=b["result"])
        old_var_rev = read_row(conn, "review_event",
            scalar(conn, "SELECT id FROM public.review_event WHERE variable_id=:v ORDER BY revision DESC LIMIT 1", v=var_id))

        insert(conn, g, "review_event",
               variable_id=var_id, revision=old_var_rev["revision"] + 1,
               supersedes_id=old_var_rev["id"], decision="needs_review",
               rationale="open review draft", reviewer_ref="auditor",
               reviewed_at=datetime.now(timezone.utc), evidence_id=shared)
        # Note: Unsealed!

    # Per N1 semantics, unsealed draft head supersedes the older approved head -> fails closed
    assert n2_matches(db, b["investigation"], b["result"]) is False
    diag = validate_n2_result(db, b["investigation"], b["result"])
    failed = [d for d in diag if not d["passed"]]
    assert any(d["rule"] == "condition_approval_and_eligibility" for d in failed)


# ============================================================================
# PART 5: Historical Reference and Digest Preservation Tests
# ============================================================================


def test_historical_digest_preservation(db):
    """Verify evaluating N2 does not mutate condition content digests or protocol seals."""
    with db.begin() as conn:
        b = build_n2_suite(conn,
                           instrument_policy="identified_required",
                           stability_policy="stable_required",
                           instrument_status="identified",
                           airflow_stability="stable")

        cond_seal_before = read_row(conn, "aggregate_seal", scalar(
            conn, "SELECT id FROM public.aggregate_seal WHERE condition_id=:c", c=b["condition"]
        ))

    # Evaluate N2 multiple times
    res_1 = n2_matches(db, b["investigation"], b["result"])
    res_2 = validate_n2_result(db, b["investigation"], b["result"])
    assert res_1 is True
    assert all(r["passed"] for r in res_2)

    with db.begin() as conn:
        cond_seal_after = read_row(conn, "aggregate_seal", cond_seal_before["id"])
        assert cond_seal_before["member_digest"] == cond_seal_after["member_digest"]
        assert cond_seal_before["member_counts"] == cond_seal_after["member_counts"]
