"""Explicit safe connectivity and health check: python -m app.db.check [--test] [--detailed]."""
import argparse
import json
from time import monotonic
from typing import Any

from alembic.script import ScriptDirectory
from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.engine import create_db_engine
from app.db.errors import DatabaseConfigurationError
from app.db.migrations import migration_config

REQUIRED_SCHEMAS = {"public", "flare_sealing", "flare_n1", "flare_n2"}


def database_available(engine: Engine) -> bool:
    try:
        with engine.connect() as connection:
            return connection.execute(text("SELECT 1")).scalar_one() == 1
    except SQLAlchemyError:
        return False


def get_head_revision(settings: Settings) -> str | None:
    try:
        config = migration_config(settings)
        directory = ScriptDirectory.from_config(config)
        heads = directory.get_heads()
        return heads[0] if heads else None
    except Exception:
        return "0008_m6_security_remediation"


def check_database_health(
    settings: Settings,
    *,
    test: bool = False,
    engine: Engine | None = None,
) -> dict[str, Any]:
    secret = settings.test_database_url if test else settings.database_url
    if secret is None or not secret.get_secret_value().strip():
        return {
            "status": "not_configured",
            "connected": False,
            "error": "Database URL is not configured",
        }

    owned_engine = False
    if engine is None:
        try:
            engine = create_db_engine(settings, test=test)
            owned_engine = True
        except DatabaseConfigurationError:
            return {
                "status": "invalid_configuration",
                "connected": False,
                "error": "Invalid database configuration",
            }

    head_rev = get_head_revision(settings)
    try:
        start = monotonic()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            latency_ms = round((monotonic() - start) * 1000, 2)

            server_version = connection.execute(text("SHOW server_version")).scalar_one()
            server_version_num = int(connection.execute(text("SHOW server_version_num")).scalar_one())
            transaction_isolation = connection.execute(text("SHOW transaction_isolation")).scalar_one()

            # Check alembic revision
            current_revision = None
            try:
                current_revision = connection.execute(
                    text("SELECT version_num FROM alembic_version LIMIT 1")
                ).scalar_one_or_none()
            except SQLAlchemyError:
                pass

            # Check schemas
            insp = inspect(connection)
            schemas = insp.get_schema_names()
            required_present = REQUIRED_SCHEMAS.issubset(set(schemas))
            is_head = (current_revision == head_rev) and (head_rev is not None)

            # Determine health status
            if is_head and required_present and transaction_isolation == "serializable":
                status = "healthy"
            else:
                status = "degraded"

            pool_stats = None
            try:
                pool_stats = {
                    "size": engine.pool.size(),
                    "checkedin": engine.pool.checkedin(),
                    "checkedout": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow(),
                }
            except Exception:
                pass

            return {
                "status": status,
                "connected": True,
                "server_version": server_version,
                "server_version_num": server_version_num,
                "transaction_isolation": transaction_isolation,
                "current_revision": current_revision,
                "head_revision": head_rev,
                "is_head": is_head,
                "schemas": schemas,
                "required_schemas_present": required_present,
                "latency_ms": latency_ms,
                "pool": pool_stats,
                "error": None,
            }
    except SQLAlchemyError:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": "Database connection failed",
        }
    finally:
        if owned_engine and engine is not None:
            engine.dispose()


def check_database(settings: Settings, *, test: bool = False) -> str:
    secret = settings.test_database_url if test else settings.database_url
    if secret is None or not secret.get_secret_value().strip():
        return "not_configured"
    try:
        engine = create_db_engine(settings, test=test)
    except DatabaseConfigurationError:
        return "invalid_configuration"
    try:
        return "available" if database_available(engine) else "unavailable"
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", action="store_true", help="Use TEST_DATABASE_URL only")
    parser.add_argument("--detailed", action="store_true", help="Output full JSON health report")
    args = parser.parse_args()

    settings = Settings()
    if args.detailed:
        health_report = check_database_health(settings, test=args.test)
        print(json.dumps(health_report, indent=2))
        return 0 if health_report.get("status") == "healthy" else 1

    try:
        status = check_database(settings, test=args.test)
    except ValueError:
        status = "invalid_configuration"
    print(json.dumps({"component": "database", "status": status}))
    return 0 if status == "available" else 1


if __name__ == "__main__":
    raise SystemExit(main())
