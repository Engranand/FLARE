import pytest

from app.core.config import Settings
from app.db.errors import DatabaseConfigurationError


def test_valid_url_and_secret_redaction():
    settings = Settings(_env_file=None,
                        database_url="postgresql+psycopg://someone:secret%25value@localhost:5432/flare_dev")
    url = settings.require_database_url()
    assert url.drivername == "postgresql+psycopg"
    assert url.password == "secret%value"
    assert "secret" not in str(settings)
    assert "someone" not in settings.model_dump_json()


@pytest.mark.parametrize("value", [None, "", "  "])
def test_missing_url(value):
    with pytest.raises(DatabaseConfigurationError, match="required"):
        Settings(_env_file=None, database_url=value).require_database_url()


@pytest.mark.parametrize("value", [
    "secret-invalid-url", "sqlite:///secret.db", "postgresql://user:secret@localhost/db",
    "postgresql+psycopg://user:secret@localhost", "postgresql+psycopg://user:secret@:5432/db",
    "postgresql+psycopg://user:secret@localhost:bad/db",
    "postgresql+psycopg://user:secret@localhost:70000/db",
    "postgresql+psycopg://user:secret@localhost/db?password=another-secret",
])
def test_invalid_url_never_leaks(value):
    with pytest.raises(DatabaseConfigurationError) as caught:
        Settings(_env_file=None, database_url=value).require_database_url()
    assert "secret" not in str(caught.value)
    assert "localhost" not in str(caught.value)


def test_env_loading_and_distinct_test_url(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("DATABASE_URL=postgresql+psycopg://user:example@localhost/from_file\n")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:example@localhost/dev")
    monkeypatch.setenv("TEST_DATABASE_URL", "postgresql+psycopg://user:example@localhost/test")
    settings = Settings(_env_file=env)
    assert settings.require_database_url().database == "dev"
    assert settings.require_database_url(test=True).database == "test"
    monkeypatch.delenv("DATABASE_URL")
    assert Settings(_env_file=env).require_database_url().database == "from_file"


def test_test_url_never_falls_back_to_development():
    with pytest.raises(DatabaseConfigurationError):
        Settings(_env_file=None, database_url="postgresql+psycopg://user:pw@localhost/dev",
                 test_database_url=None).require_database_url(test=True)


@pytest.mark.parametrize("field,value", [("db_pool_size", 0), ("db_max_overflow", -1),
                                        ("db_pool_timeout", 0), ("db_connect_timeout", 0)])
def test_invalid_pool_configuration(field, value):
    with pytest.raises(ValueError):
        Settings(_env_file=None, **{field: value})
