"""M6 security remediation: GUC removal and hardened parse trigger deduplication.

Installs:
1. Unlogged tracking table flare_sealing.checked_parse for safe transaction-scoped deduplication.
2. Hardened SECURITY DEFINER replacement for flare_sealing.check_parse() with fixed search_path.
3. Strict privilege revocation on flare_sealing.checked_parse preventing direct client manipulation.
"""
from alembic import context, op
from alembic.util import CommandError
from sqlalchemy import text

revision = "0008_m6_security_remediation"
down_revision = "0007_m45_n2"
branch_labels = depends_on = None


def upgrade():
    # 1. Unlogged deduplication tracking table scoped to transaction ID
    op.execute("""
    CREATE UNLOGGED TABLE IF NOT EXISTS flare_sealing.checked_parse (
        xact_id xid8 NOT NULL,
        parse_run_id uuid NOT NULL,
        PRIMARY KEY (xact_id, parse_run_id)
    );
    """)

    # 2. Strict permission lockdown: revoke all direct table access from public
    op.execute("""
    REVOKE ALL ON TABLE flare_sealing.checked_parse FROM PUBLIC;
    """)

    # 3. Replace flare_sealing.check_parse() with hardened SECURITY DEFINER implementation
    op.execute("""
    CREATE OR REPLACE FUNCTION flare_sealing.check_parse() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, flare_sealing, public AS $$
    DECLARE
        pid uuid;
        first_check boolean;
    BEGIN
        IF TG_TABLE_NAME = 'parse_run' THEN
            PERFORM flare_sealing.parse_shape(NEW.investigation_id, NEW.id);
            RETURN NULL;
        END IF;

        pid := (to_jsonb(NEW)->>'parse_run_id')::uuid;

        INSERT INTO flare_sealing.checked_parse (xact_id, parse_run_id)
        VALUES (pg_current_xact_id(), pid)
        ON CONFLICT DO NOTHING;

        GET DIAGNOSTICS first_check = ROW_COUNT;
        IF NOT first_check THEN
            RETURN NULL;
        END IF;

        PERFORM flare_sealing.parse_shape(NEW.investigation_id, pid);
        RETURN NULL;
    END $$;
    """)


def downgrade():
    confirmed = context.config.attributes.get("allow_destructive_downgrade") is True
    if not confirmed and context.get_x_argument(as_dictionary=True).get("confirm_destructive_downgrade") != "yes":
        raise CommandError("Reverting M6 security remediation requires explicit confirmation")

    # Revert check_parse() to original un-memoized M4.3 implementation
    op.execute("""
    CREATE OR REPLACE FUNCTION flare_sealing.check_parse() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        PERFORM flare_sealing.parse_shape(NEW.investigation_id, CASE WHEN TG_TABLE_NAME='parse_run' THEN NEW.id ELSE (to_jsonb(NEW)->>'parse_run_id')::uuid END);
        RETURN NULL;
    END $$;
    """)

    op.execute("DROP TABLE IF EXISTS flare_sealing.checked_parse;")
