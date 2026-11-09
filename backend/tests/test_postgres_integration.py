import pytest
from alembic import command
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from app.db.check import database_available
from app.db.migrations import migration_config
from app.db.session import create_session_factory, session_scope

pytestmark = pytest.mark.postgres


def test_real_postgres_connectivity_and_unprivileged_app(postgres_engines):
    _, engine = postgres_engines
    assert database_available(engine)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
        assert int(connection.execute(text("SHOW server_version_num")).scalar_one()) >= 140000
        assert connection.execute(text("SHOW transaction_isolation")).scalar_one() == "serializable"
        assert connection.execute(text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")).scalar_one() is False
        assert connection.execute(text("SELECT pg_get_userbyid(nspowner) = current_user FROM pg_namespace WHERE nspname = 'public'")).scalar_one() is False


def test_real_session_failure_rollback_and_pool_return(postgres_engines):
    _, engine = postgres_engines
    factory = create_session_factory(engine)
    with pytest.raises(DBAPIError):
        with session_scope(factory) as session:
            session.execute(text("SELECT 1 / 0"))
    assert engine.pool.checkedout() == 0
    with session_scope(factory) as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1
    assert engine.pool.checkedout() == 0


def test_baseline_upgrade_downgrade_private_database(postgres_engines):
    engine, _ = postgres_engines
    # Fixture owns this freshly created random database; no external URLs are accepted.
    assert engine.url.database.startswith("flare_test_")
    with engine.connect() as connection:
        assert inspect(connection).get_table_names(schema="public") == []
    config = migration_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "0001_m41_baseline")
        command.upgrade(config, "0001_m41_baseline")
        assert MigrationContext.configure(connection).get_current_revision() == "0001_m41_baseline"
        assert inspect(connection).get_table_names(schema="public") == ["alembic_version"]
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "base")
        assert MigrationContext.configure(connection).get_current_revision() is None
        assert set(inspect(connection).get_table_names(schema="public")) <= {"alembic_version"}
