from typing import Any, Literal

from pydantic import BaseModel


class ApiInfo(BaseModel):
    application_name: str
    version: str
    docs_url: str


class DatabaseHealth(BaseModel):
    status: str
    connected: bool
    server_version: str | None = None
    server_version_num: int | None = None
    transaction_isolation: str | None = None
    current_revision: str | None = None
    head_revision: str | None = None
    is_head: bool = False
    schemas: list[str] = []
    required_schemas_present: bool = False
    latency_ms: float | None = None
    pool: dict[str, Any] | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    application_name: str
    version: str
    database: DatabaseHealth | None = None


class SystemInfo(BaseModel):
    application_name: str
    api_version: str
    environment: str
