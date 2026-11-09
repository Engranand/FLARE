"""N1 applicability snapshots on the existing result-review dependency aggregate."""
from pathlib import Path

from alembic import context, op
from alembic.util import CommandError
from sqlalchemy import text

revision = "0004_m44_n1"
down_revision = "0003_m43_sealing"
branch_labels = depends_on = None

FUNCTIONS = [
    "facts(uuid,uuid)", "expected(uuid,uuid)", "stored(uuid,uuid)",
    "matches(uuid,uuid)", "historical(uuid,uuid,uuid)", "applicability_current(uuid,uuid)",
    "build(uuid,uuid,uuid,text)", "lock_write()", "check_owner()", "certify()",
    "recheck_new()", "append_head(uuid,text,uuid,uuid,text,uuid,text,text)",
]


def triggers():
    for table in ("test_source_record", "data_quality_issue", "analytical_eligibility", "condition_segment", "experimental_test"):
        yield table, "n1_immutable", "BEFORE UPDATE OR DELETE", "ROW", "flare_sealing.immutable"
        yield table, "n1_truncate", "BEFORE TRUNCATE", "STATEMENT", "flare_sealing.immutable"
    for table in ("test_source_record", "data_quality_issue", "review_event", "analytical_eligibility"):
        yield table, "n1_lock", "BEFORE INSERT", "ROW", "flare_n1.lock_write"
    yield "approval_dependency", "n1_owner", "BEFORE INSERT", "ROW", "flare_n1.check_owner"
    yield "aggregate_seal", "n1_certify", "AFTER INSERT", "DEFERRED", "flare_n1.certify"
    yield "review_event", "n1_result_final", "AFTER INSERT", "DEFERRED", "flare_n1.certify"
    for table in ("test_source_record", "data_quality_issue", "review_event", "aggregate_seal"):
        yield table, "n1_mutation_final", "AFTER INSERT", "DEFERRED", "flare_n1.recheck_new"


def upgrade():
    op.execute("LOCK TABLE public.review_event, public.approval_dependency, public.aggregate_seal, "
               "public.test_source_record, public.data_quality_issue IN SHARE ROW EXCLUSIVE MODE")
    op.execute("CREATE SCHEMA flare_n1")
    # Earlier migrations allowed arbitrary scope facts. Prior transaction visibility
    # cannot be proved by comparing them with today's heads.
    op.execute("""DO $$ BEGIN
        IF EXISTS (SELECT FROM public.review_event WHERE result_id IS NOT NULL AND decision='approved')
           OR EXISTS (SELECT FROM public.approval_dependency WHERE entry_kind<>'decision'
                      OR role IN ('applicability_identity','applicability_clearance')) THEN
            RAISE EXCEPTION 'Pre-N1 snapshot evidence requires provenance review';
        END IF; END $$""")
    op.execute("""DO $$ BEGIN IF EXISTS (
        SELECT FROM (
            SELECT r.*, row_number() OVER stream AS n, lag(id) OVER stream AS prior
            FROM public.review_event r WHERE num_nonnulls(test_link_id,issue_id,result_id)=1
            WINDOW stream AS (PARTITION BY investigation_id,test_link_id,issue_id,result_id ORDER BY revision)
        ) h WHERE revision<>n OR supersedes_id IS DISTINCT FROM prior
        OR ((issue_id IS NOT NULL) <> (decision IN ('open','resolved')))
    ) THEN RAISE EXCEPTION 'Invalid pre-existing N1 review stream'; END IF; END $$""")
    asset = Path(__file__).with_name("m44_n1.sql").read_text(encoding="utf-8")
    for statement in asset.split("-- next function"):
        op.execute(text(statement.strip().replace(":", r"\:")))
    for table, name, timing, level, func in triggers():
        deferred = level == "DEFERRED"
        op.execute(f"CREATE {'CONSTRAINT ' if deferred else ''}TRIGGER {name} {timing} ON public.{table} "
                   f"{'DEFERRABLE INITIALLY DEFERRED ' if deferred else ''}FOR EACH "
                   f"{'ROW' if deferred else level} EXECUTE FUNCTION {func}()")


def downgrade():
    if context.config.attributes.get("allow_destructive_downgrade") is not True and context.get_x_argument(as_dictionary=True).get("confirm_destructive_downgrade") != "yes":
        raise CommandError("Removing N1 enforcement requires explicit confirmation")
    for table, name, *_ in reversed(list(triggers())):
        op.execute(f"DROP TRIGGER {name} ON public.{table}")
    for signature in reversed(FUNCTIONS):
        op.execute(f"DROP FUNCTION flare_n1.{signature}")
    op.execute("DROP SCHEMA flare_n1")
