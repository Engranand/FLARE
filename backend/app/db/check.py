"""Explicit safe connectivity check: python -m app.db.check [--test]."""
import argparse
import json

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.engine import create_db_engine
from app.db.errors import DatabaseConfigurationError


def database_available(engine: Engine) -> bool:
    try:
        with engine.connect() as connection:
            return connection.execute(text("SELECT 1")).scalar_one() == 1
    except SQLAlchemyError:
        return False


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
    args = parser.parse_args()
    try:
        status = check_database(Settings(), test=args.test)
    except ValueError:
        status = "invalid_configuration"
    print(json.dumps({"component": "database", "status": status}))
    return 0 if status == "available" else 1


if __name__ == "__main__":
    raise SystemExit(main())
