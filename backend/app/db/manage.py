"""FLARE Database Operations Management CLI: python -m app.db.manage <command> [options].

Safe administration tool supporting:
- status: inspect connectivity, current revision, and schema status
- health: comprehensive automated database health audit
- migrate: safely upgrade or downgrade migrations with explicit confirmation guards
- backup: create consistent pg_dump archive
- restore: safely restore into target database
- verify: audit aggregate seal digests, triggers, and N1/N2 integrity
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from alembic import command
from alembic.script import ScriptDirectory

from app.core.config import Settings
from app.db.backup import (
    create_backup,
    find_postgres_bin,
    restore_backup,
    verify_database_integrity,
)
from app.db.check import check_database_health
from app.db.engine import create_db_engine
from app.db.migrations import migration_config


def cmd_status(args: argparse.Namespace, settings: Settings) -> int:
    report = check_database_health(settings, test=args.test)
    print(json.dumps(report, indent=2))
    return 0 if report.get("connected") else 1


def cmd_health(args: argparse.Namespace, settings: Settings) -> int:
    report = check_database_health(settings, test=args.test)
    print(json.dumps(report, indent=2))
    return 0 if report.get("status") == "healthy" else 1


def cmd_migrate(args: argparse.Namespace, settings: Settings) -> int:
    config = migration_config(settings)
    target_rev = args.revision or "head"
    confirm = bool(args.confirm_downgrade)

    engine = create_db_engine(settings, test=args.test)
    try:
        with engine.begin() as conn:
            config.attributes["connection"] = conn
            config.attributes["allow_destructive_downgrade"] = confirm

            # Check if moving forward or backward
            dir_script = ScriptDirectory.from_config(config)
            head_rev = dir_script.get_heads()[0] if dir_script.get_heads() else "head"

            if target_rev in ("head", head_rev):
                print(f"Upgrading database to head revision '{head_rev}'...")
                command.upgrade(config, target_rev)
            elif target_rev in ("base", "-1") or "downgrade" in target_rev:
                if not confirm:
                    print("ERROR: Destructive downgrade requested without --confirm-downgrade.", file=sys.stderr)
                    return 2
                print(f"Downgrading database to '{target_rev}' (confirmed)...")
                command.downgrade(config, target_rev)
            else:
                print(f"Applying migration to revision '{target_rev}'...")
                command.upgrade(config, target_rev)

        print("Migration completed successfully.")
        return 0
    finally:
        engine.dispose()


def cmd_backup(args: argparse.Namespace, settings: Settings) -> int:
    output_path = Path(args.output).resolve()
    print(f"Backing up database to {output_path} (format: {args.format})...")
    out_file = create_backup(
        settings,
        output_path,
        pg_bin=args.pg_bin,
        format=args.format,
        test=args.test,
    )
    print(f"Backup created successfully: {out_file} ({out_file.stat().st_size} bytes)")
    return 0


def cmd_restore(args: argparse.Namespace, settings: Settings) -> int:
    input_path = Path(args.input).resolve()
    print(f"Restoring database from {input_path}...")
    res = restore_backup(
        input_path,
        settings,
        pg_bin=args.pg_bin,
        test=args.test,
        confirm=args.confirm,
    )
    print(f"Restore completed: {res}")

    print("Verifying database integrity post-restore...")
    engine = create_db_engine(settings, test=args.test)
    try:
        audit = verify_database_integrity(engine)
        print(json.dumps(audit, indent=2))
        return 0 if audit.get("valid") else 1
    finally:
        engine.dispose()


def cmd_verify(args: argparse.Namespace, settings: Settings) -> int:
    engine = create_db_engine(settings, test=args.test)
    try:
        audit = verify_database_integrity(engine)
        print(json.dumps(audit, indent=2))
        return 0 if audit.get("valid") else 1
    finally:
        engine.dispose()


def cmd_ingest_bass_ii(args: argparse.Namespace, settings: Settings) -> int:
    from app.ingestion.pipeline import ingest_bass_ii
    from app.ingestion.reconciliation import ROOT_DIR

    engine = create_db_engine(settings, test=args.test)
    try:
        # Pre-ingestion check: verify database integrity before touching it
        print("Auditing pre-ingestion database integrity...")
        pre_audit = verify_database_integrity(engine)
        if not pre_audit.get("valid"):
            print("ERROR: Pre-ingestion database integrity check failed. Ingestion aborted.", file=sys.stderr)
            print(json.dumps(pre_audit, indent=2), file=sys.stderr)
            return 1

        # Safe pre-ingestion backup if requested
        if args.backup:
            bk_path = Path(args.backup).resolve()
            print(f"Creating pre-ingestion database backup at {bk_path}...")
            create_backup(settings, bk_path, pg_bin=args.pg_bin, test=args.test)
            if not bk_path.is_file() or bk_path.stat().st_size == 0:
                print("ERROR: Pre-ingestion database backup failed or produced empty file.", file=sys.stderr)
                return 1

        # Run ingestion
        print("Executing NASA BASS-II ingestion pipeline...")
        root_path = Path(args.root).resolve() if args.root else ROOT_DIR
        result = ingest_bass_ii(engine, root=root_path)
        print(json.dumps(result, indent=2, default=str))

        # Post-ingestion audit
        print("Auditing post-ingestion database integrity...")
        post_audit = verify_database_integrity(engine)
        print(json.dumps(post_audit, indent=2))
        return 0 if post_audit.get("valid") else 1
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Show database connectivity and revision")
    p_status.add_argument("--test", action="store_true", help="Target TEST_DATABASE_URL")

    # health
    p_health = subparsers.add_parser("health", help="Run automated health check")
    p_health.add_argument("--test", action="store_true", help="Target TEST_DATABASE_URL")

    # migrate
    p_migrate = subparsers.add_parser("migrate", help="Run database migration")
    p_migrate.add_argument("--revision", default="head", help="Target revision (default: head)")
    p_migrate.add_argument("--confirm-downgrade", action="store_true", help="Confirm destructive downgrade")
    p_migrate.add_argument("--test", action="store_true", help="Target TEST_DATABASE_URL")

    # backup
    p_backup = subparsers.add_parser("backup", help="Create database backup")
    p_backup.add_argument("--output", "-o", required=True, help="Destination backup file path")
    p_backup.add_argument("--format", choices=["custom", "plain"], default="custom", help="Archive format")
    p_backup.add_argument("--pg-bin", help="PostgreSQL binaries directory")
    p_backup.add_argument("--test", action="store_true", help="Target TEST_DATABASE_URL")

    # restore
    p_restore = subparsers.add_parser("restore", help="Restore database backup")
    p_restore.add_argument("--input", "-i", required=True, help="Input backup file path")
    p_restore.add_argument("--confirm", action="store_true", help="Confirm restore into target database")
    p_restore.add_argument("--pg-bin", help="PostgreSQL binaries directory")
    p_restore.add_argument("--test", action="store_true", help="Target TEST_DATABASE_URL")

    # verify
    p_verify = subparsers.add_parser("verify", help="Verify cryptographic aggregate seals and integrity")
    p_verify.add_argument("--test", action="store_true", help="Target TEST_DATABASE_URL")

    # ingest-bass-ii
    p_ingest = subparsers.add_parser("ingest-bass-ii", help="Ingest NASA BASS-II data into database")
    p_ingest.add_argument("--root", help="Repository root containing canonical source data")
    p_ingest.add_argument("--backup", help="Path to create pre-ingestion backup")
    p_ingest.add_argument("--pg-bin", help="PostgreSQL binaries directory")
    p_ingest.add_argument("--test", action="store_true", help="Target TEST_DATABASE_URL")

    args = parser.parse_args()
    settings = Settings()

    commands = {
        "status": cmd_status,
        "health": cmd_health,
        "migrate": cmd_migrate,
        "backup": cmd_backup,
        "restore": cmd_restore,
        "verify": cmd_verify,
        "ingest-bass-ii": cmd_ingest_bass_ii,
    }

    return commands[args.command](args, settings)


if __name__ == "__main__":
    raise SystemExit(main())
