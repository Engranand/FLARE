"""Explicit PostgreSQL migrations; no URL interpolation or startup migrations."""
from alembic import context
from alembic.util import CommandError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.base import Base
import app.models  # Register all 33 domain mappings for Alembic metadata.
from app.db.engine import create_db_engine
from app.db.errors import DatabaseConfigurationError

config = context.config
target_metadata = Base.metadata


def configure_connection(connection):
    if connection.dialect.name != "postgresql":
        raise DatabaseConfigurationError("PostgreSQL is required for migrations")
    context.configure(connection=connection, target_metadata=target_metadata,
                      compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run():
    settings = config.attributes.get("settings") or Settings()
    if context.is_offline_mode():
        context.configure(url=settings.require_database_url(),
                          target_metadata=target_metadata, literal_binds=True,
                          dialect_opts={"paramstyle": "named"}, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    elif config.attributes.get("connection") is not None:
        configure_connection(config.attributes["connection"])
    else:
        engine = create_db_engine(settings)
        try:
            with engine.connect() as connection:
                configure_connection(connection)
        finally:
            engine.dispose()


try:
    run()
except (DatabaseConfigurationError, SQLAlchemyError, ValueError):
    raise CommandError("Database migration failed; check configuration and availability") from None
