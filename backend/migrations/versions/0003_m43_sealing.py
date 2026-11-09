"""Freeze M4.2 aggregate membership and install canonical-json-v2."""
from pathlib import Path

from alembic import context, op
from alembic.util import CommandError
from sqlalchemy import text

revision = "0003_m43_sealing"
down_revision = "0002_m42_core_schema"
branch_labels = None
depends_on = None

# Names and columns belong to this revision, independent of future ORM changes.
AGGREGATES = {
    "parse_run": ("parse_run_id", {"source_field": "parse_run_id", "source_record": "parse_run_id", "observation": "parse_run_id"}),
    "semantic_annotation": ("annotation_id", {"annotation_evidence": "annotation_id"}),
    "experimental_condition": ("condition_id", {"condition_component": "condition_id"}),
    "analysis_protocol": ("protocol_id", {"protocol_requirement": "protocol_id", "protocol_unit_rule": "requirement_id"}),
    "analytical_result": ("result_id", {"result_input": "result_id", "result_condition": "result_id", "result_evidence": "result_id"}),
    "review_event": ("review_id", {"approval_dependency": "owner_review_id"}),
}
FUNCTIONS = [
    "quote_string(text)", "json_value(jsonb,boolean)", "full_row(regclass,jsonb)",
    "ownership()", "snapshot(text,uuid,uuid)", "lock_parent(text,uuid,uuid)",
    "lock_parents(jsonb)", "immutable()", "guard_child()", "parse_shape(uuid,uuid)", "check_parse()",
    "archive_matches(uuid,uuid,bytea)", "check_seal()", "seal(text,uuid,uuid,uuid,text,bytea)",
]


def triggers():
    for parent, (_, children) in AGGREGATES.items():
        for table in (parent, *children):
            yield table, "freeze_row", "BEFORE UPDATE OR DELETE", "ROW", "immutable()"
            yield table, "freeze_truncate", "BEFORE TRUNCATE", "STATEMENT", "immutable()"
        for child in children:
            yield child, "guard_member", "BEFORE INSERT", "ROW", "guard_child()"
            yield child, "member_final", "AFTER INSERT", "DEFERRED", "guard_child()"
        if parent == "parse_run":
            for table in (parent, *children):
                yield table, "parse_final", "AFTER INSERT", "DEFERRED", "check_parse()"
    yield "aggregate_seal", "freeze_row", "BEFORE UPDATE OR DELETE", "ROW", "immutable()"
    yield "aggregate_seal", "freeze_truncate", "BEFORE TRUNCATE", "STATEMENT", "immutable()"
    yield "aggregate_seal", "seal_guard", "BEFORE INSERT", "ROW", "check_seal()"
    yield "aggregate_seal", "seal_final", "AFTER INSERT", "DEFERRED", "check_seal()"


def upgrade():
    op.execute("CREATE SCHEMA flare_sealing")
    rows = [f"('{p}','{fk}','{c}','{ck}')" for p, (fk, children) in AGGREGATES.items()
            for c, ck in children.items()]
    op.execute("CREATE FUNCTION flare_sealing.ownership() RETURNS TABLE(parent text, seal_key text, child text, child_key text) LANGUAGE sql IMMUTABLE AS $$ VALUES " + ", ".join(rows) + " $$")
    sql = Path(__file__).with_name("m43_sealing.sql").read_text(encoding="utf-8")
    for statement in sql.split("-- next function"):
        op.execute(text(statement.strip().replace(":", r"\:")))
    for table, name, timing, level, routine in triggers():
        deferred = level == "DEFERRED"
        op.execute(f"CREATE {'CONSTRAINT ' if deferred else ''}TRIGGER {name} {timing} ON public.{table} "
                   f"{'DEFERRABLE INITIALLY DEFERRED ' if deferred else ''}"
                   f"FOR EACH {'ROW' if deferred else level} EXECUTE FUNCTION flare_sealing.{routine}")
    op.execute("""DO $$ DECLARE r record; BEGIN
        FOR r IN SELECT investigation_id,id FROM public.parse_run LOOP
            PERFORM flare_sealing.parse_shape(r.investigation_id,r.id);
        END LOOP; END $$""")

    # Validate retained rows under the DDL locks before enabling this revision.
    # Parse archives are content-addressed bytes supplied only for a populated upgrade.
    op.execute("""DO $$ DECLARE s record; m record; pid uuid; x record; h text;
        archives jsonb := nullif(current_setting('flare.m43_archives',true),'')::jsonb;
        BEGIN FOR s IN SELECT * FROM public.aggregate_seal LOOP
            SELECT DISTINCT parent,seal_key INTO STRICT m FROM flare_sealing.ownership()
                WHERE to_jsonb(s)->>seal_key IS NOT NULL;
            pid := (to_jsonb(s)->>m.seal_key)::uuid;
            SELECT * INTO STRICT x FROM flare_sealing.snapshot(m.parent,s.investigation_id,pid);
            IF s.member_counts::text IS DISTINCT FROM x.member_counts::text OR s.member_digest IS DISTINCT FROM x.member_digest
                OR s.seal_version <> 'canonical-json-v2' THEN
                RAISE EXCEPTION 'Retained seal differs from its members' USING ERRCODE='23514';
            END IF;
            IF m.parent='parse_run' THEN
                SELECT output_sha256 INTO STRICT h FROM public.parse_run WHERE investigation_id=s.investigation_id AND id=pid;
                PERFORM flare_sealing.archive_matches(s.investigation_id,pid,decode(archives->>h,'hex'));
            END IF;
        END LOOP; END $$""")


def downgrade():
    confirmed = context.config.attributes.get("allow_destructive_downgrade") is True
    if not confirmed and context.get_x_argument(as_dictionary=True).get("confirm_destructive_downgrade") != "yes":
        raise CommandError("Removing aggregate enforcement requires explicit confirmation")
    for table, name, *_ in reversed(list(triggers())):
        op.execute(f"DROP TRIGGER {name} ON public.{table}")
    for signature in reversed(FUNCTIONS):
        op.execute(f"DROP FUNCTION flare_sealing.{signature}")
    op.execute("DROP SCHEMA flare_sealing")
