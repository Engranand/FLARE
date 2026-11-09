"""Freeze reviewed identities, evidence locators and their source registrations."""
from alembic import context, op
from alembic.util import CommandError

revision = "0006_evidence_immutability"
down_revision = "0005_variable_immutability"
branch_labels = None
depends_on = None

# A locator pins a source_document UUID. Its registered hash and storage identity
# must also remain stable. Descriptive corrections use the existing metadata_revision.
TABLES = ("condition_role", "evidence_reference", "instrument", "source_document")


def upgrade():
    for table in TABLES:
        op.execute(f"CREATE TRIGGER evidence_freeze BEFORE UPDATE OR DELETE ON public.{table} "
                   "FOR EACH ROW EXECUTE FUNCTION flare_sealing.immutable()")
        op.execute(f"CREATE TRIGGER evidence_truncate BEFORE TRUNCATE ON public.{table} "
                   "FOR EACH STATEMENT EXECUTE FUNCTION flare_sealing.immutable()")


def downgrade():
    confirmed = context.config.attributes.get("allow_destructive_downgrade") is True
    if not confirmed and context.get_x_argument(as_dictionary=True).get("confirm_destructive_downgrade") != "yes":
        raise CommandError("Removing scientific evidence protection requires explicit confirmation")
    for table in reversed(TABLES):
        op.execute(f"DROP TRIGGER evidence_truncate ON public.{table}")
        op.execute(f"DROP TRIGGER evidence_freeze ON public.{table}")
