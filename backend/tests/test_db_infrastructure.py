from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.db.base import Base
from app.db.check import check_database, database_available
from app.db.engine import create_db_engine
from app.db.session import create_session_factory, get_session, session_scope
from app.main import create_app


def configured():
    return Settings(_env_file=None, database_url="postgresql+psycopg://user:secret@localhost/unused")


def test_engine_options_and_empty_metadata():
    with patch("app.db.engine.create_engine") as create:
        create_db_engine(configured())
    _, options = create.call_args
    assert options == {"pool_size": 5, "max_overflow": 5, "pool_timeout": 5.0,
                       "pool_recycle": 1800, "pool_pre_ping": True,
                       "connect_args": {"connect_timeout": 5}, "isolation_level": "SERIALIZABLE",
                       "echo": False, "hide_parameters": True}


def test_real_engine_and_distinct_unconnected_sessions():
    engine = create_db_engine(configured())
    try:
        factory = create_session_factory(engine)
        with session_scope(factory) as first, session_scope(factory) as second:
            assert first is not second
            assert first.get_bind() is engine
            assert not first.autoflush
            assert engine.pool.checkedout() == 0
    finally:
        engine.dispose()


@pytest.mark.parametrize("fail", [False, True])
def test_session_cleanup_and_explicit_commit_policy(fail):
    session = MagicMock()
    session.__enter__.return_value = session
    session.in_transaction.return_value = True
    factory = MagicMock(return_value=session)
    if fail:
        with pytest.raises(RuntimeError):
            with session_scope(factory):
                raise RuntimeError("work failed")
    else:
        with session_scope(factory) as actual:
            assert actual is session
    session.rollback.assert_called()
    session.commit.assert_not_called()
    session.__exit__.assert_called_once()


def test_failed_connectivity_is_safe(capsys):
    engine = MagicMock()
    engine.connect.side_effect = OperationalError("secret statement", {}, Exception("secret password"))
    assert database_available(engine) is False
    with patch("app.db.check.create_db_engine", return_value=engine):
        assert check_database(configured()) == "unavailable"
    engine.dispose.assert_called_once()
    assert "secret" not in capsys.readouterr().out


def test_select_one_and_connection_cleanup():
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value.scalar_one.return_value = 1
    assert database_available(engine)
    assert str(connection.execute.call_args.args[0]) == "SELECT 1"
    engine.connect.return_value.__exit__.assert_called_once()


def test_missing_and_invalid_connectivity_configuration():
    assert check_database(Settings(_env_file=None, database_url=None)) == "not_configured"
    assert check_database(Settings(_env_file=None, database_url="bad secret")) == "invalid_configuration"


def test_application_lifespan_disposes_engine_without_connecting():
    with patch("app.main.create_db_engine") as create:
        engine = create.return_value
        with TestClient(create_app(configured())) as client:
            assert client.get("/api/v1/health").json()["status"] == "ok"
            assert client.app.state.session_factory is not None
            engine.connect.assert_not_called()
        engine.dispose.assert_called_once()
        assert client.app.state.session_factory is None


def test_request_dependency_without_database_is_safe():
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(session_factory=None)))
    with pytest.raises(HTTPException) as caught:
        next(get_session(request))
    assert caught.value.status_code == 503
    assert caught.value.detail == "Database unavailable"


def test_request_dependency_rolls_back_and_hides_driver_exception():
    session = MagicMock()
    session.__enter__.return_value = session
    factory = MagicMock(return_value=session)
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(session_factory=factory)))
    dependency = get_session(request)
    assert next(dependency) is session
    with pytest.raises(HTTPException) as caught:
        dependency.throw(OperationalError("secret SQL", {}, Exception("secret password")))
    assert caught.value.status_code == 503
    assert "secret" not in caught.value.detail
    session.rollback.assert_called()
    session.__exit__.assert_called_once()
