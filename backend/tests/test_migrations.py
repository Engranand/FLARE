import io

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from alembic.util import CommandError

from app.core.config import Settings
from app.db.base import Base
from app.db.migrations import migration_config


def test_migration_discovery_and_empty_baseline():
    config = migration_config()
    directory = ScriptDirectory.from_config(config)
    assert directory.get_heads() == ["0009_m10_4_document_chunks"]
    revisions = list(directory.walk_revisions())
    assert len(revisions) == 9 and revisions[-1].down_revision is None
    assert revisions[-1].module.upgrade() is None
    assert revisions[-1].module.downgrade() is None
    assert config.get_main_option("sqlalchemy.url") is None


def test_offline_migration_has_only_version_table():
    config = migration_config(Settings(_env_file=None,
        database_url="postgresql+psycopg://user:secret%25@localhost/unused"))
    config.output_buffer = io.StringIO()
    command.upgrade(config, "0001_m41_baseline", sql=True)
    sql = config.output_buffer.getvalue()
    assert sql.count("CREATE TABLE") == 1
    assert "CREATE TABLE alembic_version" in sql
    assert "0001_m41_baseline" in sql
    assert "secret" not in sql and "unused" not in sql


def test_migration_missing_url_is_safe():
    config = migration_config(Settings(_env_file=None, database_url=None))
    with pytest.raises(CommandError, match="check configuration"):
        command.upgrade(config, "0001_m41_baseline", sql=True)
