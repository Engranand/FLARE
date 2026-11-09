import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client():
    settings = Settings(_env_file=None, app_name="FLARE Scientific Intelligence API",
                        app_version="0.1.0", environment="test", api_v1_prefix="/api/v1",
                        frontend_origin="http://localhost:5173")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"application_name": "FLARE Scientific Intelligence API",
                               "version": "0.1.0", "docs_url": "/docs"}


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "application_name": "FLARE Scientific Intelligence API",
                               "version": "0.1.0"}


def test_system_info_does_not_leak_secrets(client, monkeypatch):
    monkeypatch.setenv("SECRET_TOKEN", "must-not-be-returned")
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    assert response.json() == {"application_name": "FLARE Scientific Intelligence API",
                               "api_version": "0.1.0", "environment": "test"}


def test_startup_and_openapi(client):
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "FLARE Scientific Intelligence API"
    assert schema["info"]["version"] == "0.1.0"
    assert set(schema["paths"]) == {"/", "/api/v1/health", "/api/v1/system/info"}


def test_cors_allowed_and_disallowed_origins(client):
    allowed = client.options("/api/v1/health", headers={"Origin": "http://localhost:5173",
                            "Access-Control-Request-Method": "GET"})
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    denied = client.options("/api/v1/health", headers={"Origin": "https://untrusted.example",
                           "Access-Control-Request-Method": "GET"})
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers


def test_custom_prefix():
    with TestClient(create_app(Settings(_env_file=None, api_v1_prefix="/custom"))) as client:
        assert client.get("/custom/health").status_code == 200
        assert client.get("/api/v1/health").status_code == 404


@pytest.mark.parametrize("origin", ["*", "http://localhost:5173/path", "https://user:password@example.com"])
def test_invalid_origin(origin):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, frontend_origin=origin)
