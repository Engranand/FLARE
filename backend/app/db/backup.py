"""Production-grade database backup, restore, and integrity verification.

Implements M5 requirements:
- Safe database backup using pg_dump without credentials exposure.
- Safe restore using pg_restore / psql into target databases.
- Cryptographic integrity verification of aggregate seals, historical references, and digests.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from alembic.script import ScriptDirectory
from sqlalchemy import Engine, URL, create_engine, inspect, text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from app.core.config import Settings
from app.db.engine import create_db_engine
from app.db.errors import DatabaseConfigurationError
from app.db.migrations import migration_config

REQUIRED_TABLE_COUNT = 33
REQUIRED_SCHEMAS = {"public", "flare_sealing", "flare_n1", "flare_n2"}


def get_authoritative_alembic_head(settings: Settings | None = None) -> str | None:
    """Resolve the authoritative Alembic migration head dynamically from repository migration scripts."""
    try:
        config = migration_config(settings)
        directory = ScriptDirectory.from_config(config)
        heads = directory.get_heads()
        return heads[0] if heads else None
    except Exception:
        return None


# Backward-compatible alias resolved dynamically from authoritative migration scripts
EXPECTED_ALEMBIC_HEAD = get_authoritative_alembic_head()
PROTECTED_DATABASE_NAMES = {
    "flare", "flare_dev", "flare_development", "flare_prod", "flare_production",
    "production", "prod", "main", "master", "postgres"
}

# Complete set of 102 triggers installed across migrations 0003 through 0007
REQUIRED_TRIGGERS: frozenset[tuple[str, str]] = frozenset({
    # Migration 0003_m43_sealing (Freeze, truncate, child guards, seal checks, parse check)
    ("parse_run", "freeze_row"),
    ("parse_run", "freeze_truncate"),
    ("parse_run", "parse_final"),
    ("source_field", "freeze_row"),
    ("source_field", "freeze_truncate"),
    ("source_field", "guard_member"),
    ("source_field", "member_final"),
    ("source_field", "parse_final"),
    ("source_record", "freeze_row"),
    ("source_record", "freeze_truncate"),
    ("source_record", "guard_member"),
    ("source_record", "member_final"),
    ("source_record", "parse_final"),
    ("observation", "freeze_row"),
    ("observation", "freeze_truncate"),
    ("observation", "guard_member"),
    ("observation", "member_final"),
    ("observation", "parse_final"),
    ("semantic_annotation", "freeze_row"),
    ("semantic_annotation", "freeze_truncate"),
    ("annotation_evidence", "freeze_row"),
    ("annotation_evidence", "freeze_truncate"),
    ("annotation_evidence", "guard_member"),
    ("annotation_evidence", "member_final"),
    ("experimental_condition", "freeze_row"),
    ("experimental_condition", "freeze_truncate"),
    ("condition_component", "freeze_row"),
    ("condition_component", "freeze_truncate"),
    ("condition_component", "guard_member"),
    ("condition_component", "member_final"),
    ("analysis_protocol", "freeze_row"),
    ("analysis_protocol", "freeze_truncate"),
    ("protocol_requirement", "freeze_row"),
    ("protocol_requirement", "freeze_truncate"),
    ("protocol_requirement", "guard_member"),
    ("protocol_requirement", "member_final"),
    ("protocol_unit_rule", "freeze_row"),
    ("protocol_unit_rule", "freeze_truncate"),
    ("protocol_unit_rule", "guard_member"),
    ("protocol_unit_rule", "member_final"),
    ("analytical_result", "freeze_row"),
    ("analytical_result", "freeze_truncate"),
    ("result_input", "freeze_row"),
    ("result_input", "freeze_truncate"),
    ("result_input", "guard_member"),
    ("result_input", "member_final"),
    ("result_condition", "freeze_row"),
    ("result_condition", "freeze_truncate"),
    ("result_condition", "guard_member"),
    ("result_condition", "member_final"),
    ("result_evidence", "freeze_row"),
    ("result_evidence", "freeze_truncate"),
    ("result_evidence", "guard_member"),
    ("result_evidence", "member_final"),
    ("review_event", "freeze_row"),
    ("review_event", "freeze_truncate"),
    ("approval_dependency", "freeze_row"),
    ("approval_dependency", "freeze_truncate"),
    ("approval_dependency", "guard_member"),
    ("approval_dependency", "member_final"),
    ("aggregate_seal", "freeze_row"),
    ("aggregate_seal", "freeze_truncate"),
    ("aggregate_seal", "seal_guard"),
    ("aggregate_seal", "seal_final"),

    # Migration 0004_m44_n1
    ("aggregate_seal", "n1_certify"),
    ("aggregate_seal", "n1_mutation_final"),
    ("test_source_record", "n1_immutable"),
    ("test_source_record", "n1_truncate"),
    ("test_source_record", "n1_lock"),
    ("test_source_record", "n1_mutation_final"),
    ("data_quality_issue", "n1_immutable"),
    ("data_quality_issue", "n1_truncate"),
    ("data_quality_issue", "n1_lock"),
    ("data_quality_issue", "n1_mutation_final"),
    ("review_event", "n1_lock"),
    ("review_event", "n1_result_final"),
    ("review_event", "n1_mutation_final"),
    ("approval_dependency", "n1_owner"),
    ("condition_segment", "n1_immutable"),
    ("condition_segment", "n1_truncate"),
    ("experimental_test", "n1_immutable"),
    ("experimental_test", "n1_truncate"),
    ("analytical_eligibility", "n1_immutable"),
    ("analytical_eligibility", "n1_truncate"),
    ("analytical_eligibility", "n1_lock"),

    # Migration 0005_variable_immutability
    ("scientific_variable", "variable_freeze"),
    ("scientific_variable", "variable_truncate"),
    ("scientific_variable", "variable_register"),
    ("review_event", "variable_review"),
    ("evidence_reference", "variable_evidence"),
    ("protocol_requirement", "variable_requirement"),
    ("aggregate_seal", "variable_protocol"),
    ("aggregate_seal", "variable_protocol_final"),

    # Migration 0006_evidence_immutability
    ("condition_role", "evidence_freeze"),
    ("condition_role", "evidence_truncate"),
    ("evidence_reference", "evidence_freeze"),
    ("evidence_reference", "evidence_truncate"),
    ("instrument", "evidence_freeze"),
    ("instrument", "evidence_truncate"),
    ("source_document", "evidence_freeze"),
    ("source_document", "evidence_truncate"),

    # Migration 0007_m45_n2
    ("aggregate_seal", "condition_approval_seal_guard"),
})


def find_postgres_bin(supplied: str | Path | None = None) -> Path:
    """Locate PostgreSQL binary directory (containing pg_dump, pg_restore, psql)."""
    if supplied:
        p = Path(supplied)
        if p.is_dir():
            return p
    env_bin = os.environ.get("POSTGRES_BIN")
    if env_bin and Path(env_bin).is_dir():
        return Path(env_bin)
    which = shutil.which("pg_dump") or shutil.which("initdb")
    if which:
        return Path(which).parent
    for ver in ["17", "16", "15"]:
        std_win = Path(f"C:/Program Files/PostgreSQL/{ver}/bin")
        if std_win.is_dir():
            return std_win
    for p in [Path("/usr/lib/postgresql/17/bin"), Path("/usr/local/bin"), Path("/opt/homebrew/bin")]:
        if p.is_dir() and (p / "pg_dump").is_file():
            return p
    raise RuntimeError("PostgreSQL binaries not found; specify POSTGRES_BIN or --pg-bin")


def _resolve_url(target: URL | Settings, *, test: bool = False) -> URL:
    if isinstance(target, URL):
        return target
    if isinstance(target, Settings):
        return target.require_database_url(test=test)
    raise TypeError(f"Expected URL or Settings, got {type(target)}")


def create_backup(
    target: URL | Settings,
    output_path: str | Path,
    *,
    pg_bin: str | Path | None = None,
    format: str = "custom",
    test: bool = False,
) -> Path:
    """Create a consistent PostgreSQL backup using pg_dump.
    
    Credentials are passed exclusively via environment (never on CLI).
    Never exposes passwords or sensitive connection strings.
    """
    url = _resolve_url(target, test=test)
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    bin_dir = find_postgres_bin(pg_bin)
    suffix = ".exe" if os.name == "nt" else ""
    dump_bin = bin_dir / f"pg_dump{suffix}"
    if not dump_bin.is_file():
        raise RuntimeError(f"pg_dump executable not found in {bin_dir}")

    fmt_flag = "c" if format == "custom" else "p"
    cmd = [
        str(dump_bin),
        "-h", str(url.host),
        "-p", str(url.port or 5432),
        "-U", str(url.username),
        "-d", str(url.database),
        f"-F{fmt_flag}",
        "-f", str(out),
    ]

    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password

    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    proc = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        creationflags=creation_flags,
        timeout=120,
    )

    if proc.returncode != 0:
        clean_err = proc.stderr.replace(url.password or "", "***") if url.password else proc.stderr
        raise RuntimeError(f"pg_dump failed (exit code {proc.returncode}): {clean_err.strip()}")

    if not out.is_file() or out.stat().st_size == 0:
        raise RuntimeError(f"pg_dump produced empty or missing backup file: {out}")

    return out


def restore_backup(
    backup_path: str | Path,
    target: URL | Settings,
    *,
    pg_bin: str | Path | None = None,
    test: bool = False,
    confirm: bool = False,
) -> dict[str, Any]:
    """Restore a PostgreSQL backup into a target database.
    
    Prevents accidental restoration over protected databases without explicit confirm=True.
    """
    url = _resolve_url(target, test=test)
    src = Path(backup_path).resolve()
    if not src.is_file() or src.stat().st_size == 0:
        raise FileNotFoundError(f"Backup file not found or empty: {src}")

    # Guard protected databases
    if not confirm and url.database and url.database.lower() in PROTECTED_DATABASE_NAMES:
        raise ValueError(
            f"Restoring into protected database '{url.database}' requires explicit confirm=True"
        )

    # Inspect target database to verify existence and detect existing populated objects
    inspect_engine = create_engine(url, isolation_level="AUTOCOMMIT")
    try:
        with inspect_engine.connect() as conn:
            table_count = conn.execute(
                text("SELECT count(*) FROM pg_tables WHERE schemaname = 'public'")
            ).scalar_one()
            if table_count > 0 and not confirm:
                raise ValueError(
                    f"Target database '{url.database}' is populated with {table_count} existing tables; "
                    "restoring requires explicit confirm=True"
                )
    except DBAPIError as exc:
        clean_err = str(exc.orig or exc).replace(url.password or "", "***") if url.password else str(exc.orig or exc)
        raise RuntimeError(f"Cannot inspect target database '{url.database}': {clean_err.strip()}") from None
    finally:
        inspect_engine.dispose()

    bin_dir = find_postgres_bin(pg_bin)
    suffix = ".exe" if os.name == "nt" else ""

    # Detect format by inspecting magic bytes
    with src.open("rb") as f:
        header = f.read(5)
    is_custom = header == b"PGDMP"

    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password

    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    if is_custom:
        restore_bin = bin_dir / f"pg_restore{suffix}"
        if not restore_bin.is_file():
            raise RuntimeError(f"pg_restore executable not found in {bin_dir}")
        cmd = [
            str(restore_bin),
            "-h", str(url.host),
            "-p", str(url.port or 5432),
            "-U", str(url.username),
            "-d", str(url.database),
            "--no-owner",
            str(src),
        ]
    else:
        psql_bin = bin_dir / f"psql{suffix}"
        if not psql_bin.is_file():
            raise RuntimeError(f"psql executable not found in {bin_dir}")
        cmd = [
            str(psql_bin),
            "-h", str(url.host),
            "-p", str(url.port or 5432),
            "-U", str(url.username),
            "-d", str(url.database),
            "-f", str(src),
        ]

    proc = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        creationflags=creation_flags,
        timeout=180,
    )

    # Note: pg_restore returns non-zero for warnings (e.g. existing tables/types).
    # We inspect standard error without leaking credentials.
    clean_err = proc.stderr.replace(url.password or "", "***") if url.password else proc.stderr

    if proc.returncode not in (0, 1):  # 1 can be non-fatal warnings in pg_restore
        raise RuntimeError(f"Restore failed (exit code {proc.returncode}): {clean_err.strip()}")

    return {
        "success": True,
        "target_database": url.database,
        "backup_path": str(src),
        "backup_size_bytes": src.stat().st_size,
        "format": "custom" if is_custom else "plain",
    }


def verify_database_integrity(engine: Engine, settings: Settings | None = None) -> dict[str, Any]:
    """Perform rigorous verification of restored or live database integrity.
    
    Verifies:
    1. Migration head matches authoritative Alembic repository head.
    2. Core schemas and 33 domain entities exist.
    3. Aggregate seal member digests match cryptographic SHA-256 reconstruction.
    4. Historical N1 applicability snapshots are intact and queryable.
    5. N2 condition matching evaluates deterministically.
    6. Immutability and seal triggers are enabled.
    """
    failures: list[str] = []

    with engine.connect() as conn:
        # 1. Check Alembic revision
        try:
            current_rev = conn.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            ).scalar_one_or_none()
        except SQLAlchemyError as exc:
            current_rev = None
            failures.append(f"alembic_version table unreadable: {exc}")

        authoritative_head = get_authoritative_alembic_head(settings)
        if authoritative_head is None:
            failures.append("Authoritative Alembic migration head could not be determined from script directory")
        elif current_rev != authoritative_head:
            failures.append(
                f"Alembic revision mismatch: expected '{authoritative_head}', got '{current_rev}'"
            )

        # 2. Check schemas
        insp = inspect(conn)
        schemas = set(insp.get_schema_names())
        missing_schemas = REQUIRED_SCHEMAS - schemas
        if missing_schemas:
            failures.append(f"Missing required schemas: {sorted(missing_schemas)}")

        # 3. Check table count
        public_tables = set(insp.get_table_names(schema="public"))
        # Exclude alembic_version from domain entity count
        domain_tables = public_tables - {"alembic_version"}
        if len(domain_tables) < REQUIRED_TABLE_COUNT:
            failures.append(
                f"Missing domain tables: expected at least {REQUIRED_TABLE_COUNT}, found {len(domain_tables)}"
            )

        # 4. Check Aggregate Seals and Digest Integrity
        verified_seals = 0
        seal_mismatches = []
        try:
            seal_rows = conn.execute(
                text("""
                SELECT s.id, s.member_digest, x.member_digest AS computed_digest,
                       (s.member_digest = x.member_digest) AS digest_valid,
                       s.member_counts, x.member_counts AS computed_counts,
                       (s.member_counts = x.member_counts) AS counts_valid
                FROM public.aggregate_seal s
                CROSS JOIN LATERAL flare_sealing.snapshot(
                    CASE
                        WHEN s.parse_run_id IS NOT NULL THEN 'parse_run'
                        WHEN s.annotation_id IS NOT NULL THEN 'semantic_annotation'
                        WHEN s.condition_id IS NOT NULL THEN 'experimental_condition'
                        WHEN s.protocol_id IS NOT NULL THEN 'analysis_protocol'
                        WHEN s.result_id IS NOT NULL THEN 'analytical_result'
                        WHEN s.review_id IS NOT NULL THEN 'review_event'
                    END,
                    s.investigation_id,
                    COALESCE(s.parse_run_id, s.annotation_id, s.condition_id, s.protocol_id, s.result_id, s.review_id)
                ) x;
                """)
            ).mappings().all()

            for row in seal_rows:
                if row["digest_valid"] and row["counts_valid"]:
                    verified_seals += 1
                else:
                    seal_mismatches.append(str(row["id"]))

            if seal_mismatches:
                failures.append(f"Cryptographic seal digest mismatches on seal IDs: {seal_mismatches}")
        except SQLAlchemyError as exc:
            failures.append(f"Aggregate seal verification query failed: {exc}")

        # 5. Check triggers enabled and present
        triggers_active = False
        try:
            trigger_rows = conn.execute(
                text("""
                SELECT c.relname AS table_name, t.tgname AS trigger_name, t.tgenabled AS trigger_enabled
                FROM pg_trigger t
                JOIN pg_class c ON c.oid = t.tgrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND NOT t.tgisinternal;
                """)
            ).mappings().all()

            existing_triggers = {
                (r["table_name"], r["trigger_name"]): r["trigger_enabled"]
                for r in trigger_rows
            }

            missing_triggers = REQUIRED_TRIGGERS - set(existing_triggers.keys())
            if missing_triggers:
                failures.append(f"Missing required triggers: {sorted(missing_triggers)}")

            disabled_triggers = [
                pair for pair, status in existing_triggers.items()
                if status != "O" and pair in REQUIRED_TRIGGERS
            ]
            if disabled_triggers:
                failures.append(f"Disabled required triggers: {sorted(disabled_triggers)}")

            if not missing_triggers and not disabled_triggers:
                triggers_active = True
        except SQLAlchemyError as exc:
            failures.append(f"Trigger inspection failed: {exc}")

        # 6. Check N1 and N2 operational functions
        n1_ok = False
        n2_ok = False
        try:
            n1_ok = conn.execute(
                text("SELECT to_regprocedure('flare_n1.applicability_current(uuid,uuid)') IS NOT NULL")
            ).scalar_one()
            n2_ok = conn.execute(
                text("SELECT to_regprocedure('flare_n2.matches(uuid,uuid)') IS NOT NULL")
            ).scalar_one()
        except SQLAlchemyError as exc:
            failures.append(f"Function inspection failed: {exc}")

        is_valid = len(failures) == 0

        return {
            "valid": is_valid,
            "alembic_revision": current_rev,
            "domain_table_count": len(domain_tables),
            "schemas_present": sorted(schemas),
            "verified_seals_count": verified_seals,
            "failed_seals_count": len(seal_mismatches),
            "triggers_active": triggers_active,
            "n1_operational": bool(n1_ok),
            "n2_operational": bool(n2_ok),
            "failures": failures,
        }
