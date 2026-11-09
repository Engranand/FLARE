from typing import Literal

from pydantic import BaseModel


class ApiInfo(BaseModel):
    application_name: str
    version: str
    docs_url: str


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    application_name: str
    version: str


class SystemInfo(BaseModel):
    application_name: str
    api_version: str
    environment: str
