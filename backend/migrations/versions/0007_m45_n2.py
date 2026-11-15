"""M4.5 remediation and N2 condition-policy matcher.

Installs:
1. Condition approval review variable-definition lineage guard on aggregate_seal.
2. N2 condition policy matching rules (all 12 truth-table cases) in schema flare_n2.
3. Deferred N2 certification triggers on aggregate_seal and review_event.
"""
from pathlib import Path

from alembic import context, op
from alembic.util import CommandError
from sqlalchemy import text

revision = "0007_m45_n2"
down_revision = "0006_evidence_immutability"
branch_labels = depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA flare_n2")
    asset = Path(__file__).with_name("m45_n2.sql").read_text(encoding="utf-8")
    for statement in asset.split("-- next function"):
        cleaned = statement.strip()
        if cleaned:
            op.execute(text(cleaned.replace(":", r"\:")))

    # Guard 1: Verify condition approval dependencies when review seal is inserted
    op.execute("CREATE TRIGGER condition_approval_seal_guard BEFORE INSERT ON public.aggregate_seal "
               "FOR EACH ROW EXECUTE FUNCTION flare_sealing.check_condition_review()")


def downgrade():
    confirmed = context.config.attributes.get("allow_destructive_downgrade") is True
    if not confirmed and context.get_x_argument(as_dictionary=True).get("confirm_destructive_downgrade") != "yes":
        raise CommandError("Removing M4.5 remediation and N2 enforcement requires explicit confirmation")

    op.execute("DROP TRIGGER IF EXISTS condition_approval_seal_guard ON public.aggregate_seal")

    op.execute("DROP FUNCTION IF EXISTS flare_n2.certify()")
    op.execute("DROP FUNCTION IF EXISTS flare_n2.matches(uuid, uuid)")
    op.execute("DROP FUNCTION IF EXISTS flare_n2.validate_result(uuid, uuid)")
    op.execute("DROP FUNCTION IF EXISTS flare_sealing.check_condition_review()")

    op.execute("DROP SCHEMA IF EXISTS flare_n2")
