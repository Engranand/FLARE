"""Append-only scientific definitions and exact successor approvals (M3 R6)."""
from alembic import context, op
from alembic.util import CommandError

revision = "0005_variable_immutability"
down_revision = "0004_m44_n1"
branch_labels = None
depends_on = None

# Kept in this revision so historical installation never imports live model code.
FUNCTIONS = {
    "register_version()": """
    DECLARE last_version integer;
    BEGIN
        IF current_setting('transaction_isolation') <> 'serializable' THEN
            RAISE EXCEPTION 'Variable registration requires SERIALIZABLE' USING ERRCODE='25001';
        END IF;
        PERFORM id FROM public.investigation WHERE id=NEW.investigation_id FOR UPDATE;
        SELECT max(definition_version) INTO last_version FROM public.scientific_variable
            WHERE investigation_id=NEW.investigation_id AND variable_code=NEW.variable_code;
        IF NEW.definition_version::bigint <> coalesce(last_version::bigint,0)+1 THEN
            RAISE EXCEPTION 'Expected the next definition version for this variable code' USING ERRCODE='23514';
        END IF;
        PERFORM id FROM public.evidence_reference
            WHERE investigation_id=NEW.investigation_id AND id=NEW.evidence_id FOR SHARE;
        IF EXISTS (SELECT FROM public.scientific_variable v WHERE v.investigation_id=NEW.investigation_id
                   AND v.variable_code=NEW.variable_code AND (v.evidence_id=NEW.evidence_id OR EXISTS (
                       SELECT FROM public.review_event r WHERE r.investigation_id=v.investigation_id
                       AND r.variable_id=v.id AND r.evidence_id=NEW.evidence_id))) THEN
            RAISE EXCEPTION 'Successor definition requires fresh evidence' USING ERRCODE='23514';
        END IF;
        RETURN NEW;
    END""",
    "review_version()": """
    DECLARE v public.scientific_variable; previous public.review_event;
    BEGIN
        -- The existing n1_lock trigger takes the investigation lock first.
        SELECT * INTO STRICT v FROM public.scientific_variable
            WHERE investigation_id=NEW.investigation_id AND id=NEW.variable_id FOR UPDATE;
        PERFORM id FROM public.evidence_reference
            WHERE investigation_id=NEW.investigation_id AND id=NEW.evidence_id FOR SHARE;
        SELECT * INTO previous FROM public.review_event
            WHERE investigation_id=v.investigation_id AND variable_id=v.id ORDER BY revision DESC LIMIT 1;
        IF NEW.revision<>coalesce(previous.revision,0)+1 OR NEW.supersedes_id IS DISTINCT FROM previous.id
            OR NEW.decision IN ('open','resolved') THEN
            RAISE EXCEPTION 'Invalid review stream for exact variable identity' USING ERRCODE='23514';
        END IF;
        IF NEW.decision='approved' AND EXISTS (
            SELECT FROM public.scientific_variable older WHERE older.investigation_id=v.investigation_id
            AND older.variable_code=v.variable_code AND older.definition_version<v.definition_version
            AND (older.evidence_id=NEW.evidence_id OR EXISTS (
                SELECT FROM public.review_event r WHERE r.investigation_id=older.investigation_id
                AND r.variable_id=older.id AND r.evidence_id=NEW.evidence_id))) THEN
            RAISE EXCEPTION 'Successor approval cites earlier version evidence' USING ERRCODE='23514';
        END IF;
        RETURN NEW;
    END""",
    "protect_evidence()": """
    BEGIN
        IF EXISTS (SELECT FROM public.scientific_variable WHERE investigation_id=OLD.investigation_id AND evidence_id=OLD.id)
            OR EXISTS (SELECT FROM public.review_event WHERE investigation_id=OLD.investigation_id
                       AND variable_id IS NOT NULL AND evidence_id=OLD.id) THEN
            RAISE EXCEPTION 'Evidence pinned to a variable definition or review is immutable' USING ERRCODE='55000';
        END IF;
        -- A stable old snapshot must not authorize edits across a concurrent registration.
        IF current_setting('transaction_isolation')='repeatable read' THEN
            RAISE EXCEPTION 'Evidence mutation requires a refreshed or SERIALIZABLE view' USING ERRCODE='25001';
        END IF;
        IF TG_OP='DELETE' THEN RETURN OLD; END IF;
        RETURN NEW;
    END""",
    "check_successor_use()": """
    DECLARE target_protocol uuid; variable_key uuid;
    BEGIN
        IF TG_TABLE_NAME='protocol_requirement' THEN variable_key:=NEW.variable_id;
        ELSE target_protocol:=NEW.protocol_id;
        END IF;
        IF EXISTS (
            SELECT FROM public.scientific_variable v
            LEFT JOIN LATERAL (SELECT r.id,r.decision FROM public.review_event r
                WHERE r.investigation_id=v.investigation_id AND r.variable_id=v.id
                ORDER BY r.revision DESC LIMIT 1) head ON true
            WHERE v.investigation_id=NEW.investigation_id AND v.definition_version>1
              AND (v.id=variable_key OR EXISTS (SELECT FROM public.protocol_requirement q
                  WHERE q.investigation_id=v.investigation_id AND q.protocol_id=target_protocol AND q.variable_id=v.id))
              AND (head.decision IS DISTINCT FROM 'approved' OR NOT EXISTS (
                  SELECT FROM public.aggregate_seal s WHERE s.investigation_id=v.investigation_id AND s.review_id=head.id))
        ) THEN RAISE EXCEPTION 'Successor use requires current sealed approval of its exact UUID' USING ERRCODE='23514';
        END IF;
        RETURN NEW;
    END""",
}

TRIGGERS = (
    ("scientific_variable","variable_freeze","BEFORE UPDATE OR DELETE","ROW","flare_sealing.immutable()", ""),
    ("scientific_variable","variable_truncate","BEFORE TRUNCATE","STATEMENT","flare_sealing.immutable()", ""),
    ("scientific_variable","variable_register","BEFORE INSERT","ROW","flare_variable.register_version()", ""),
    ("review_event","variable_review","BEFORE INSERT","ROW","flare_variable.review_version()", "NEW.variable_id IS NOT NULL"),
    ("evidence_reference","variable_evidence","BEFORE UPDATE OR DELETE","ROW","flare_variable.protect_evidence()", ""),
    ("protocol_requirement","variable_requirement","BEFORE INSERT","ROW","flare_variable.check_successor_use()", ""),
    ("aggregate_seal","variable_protocol","BEFORE INSERT","ROW","flare_variable.check_successor_use()", "NEW.protocol_id IS NOT NULL"),
    ("aggregate_seal","variable_protocol_final","AFTER INSERT","DEFERRED","flare_variable.check_successor_use()", "NEW.protocol_id IS NOT NULL"),
)


def upgrade():
    op.execute("CREATE SCHEMA flare_variable")
    for signature, body in FUNCTIONS.items():
        op.execute(f"CREATE FUNCTION flare_variable.{signature} RETURNS trigger LANGUAGE plpgsql "
                   f"SET search_path=pg_catalog,pg_temp AS $$ {body} $$")
    for table, name, timing, level, routine, predicate in TRIGGERS:
        deferred = level == "DEFERRED"
        op.execute(f"CREATE {'CONSTRAINT ' if deferred else ''}TRIGGER {name} {timing} ON public.{table} "
                   f"{'DEFERRABLE INITIALLY DEFERRED ' if deferred else ''}FOR EACH {'ROW' if deferred else level} "
                   f"{'WHEN (' + predicate + ')' if predicate else ''}EXECUTE FUNCTION {routine}")


def downgrade():
    confirmed = context.config.attributes.get("allow_destructive_downgrade") is True
    if not confirmed and context.get_x_argument(as_dictionary=True).get("confirm_destructive_downgrade") != "yes":
        raise CommandError("Removing variable immutability requires explicit confirmation")
    for table, name, *_ in reversed(TRIGGERS):
        op.execute(f"DROP TRIGGER {name} ON public.{table}")
    for signature in reversed(FUNCTIONS):
        op.execute(f"DROP FUNCTION flare_variable.{signature}")
    op.execute("DROP SCHEMA flare_variable")
