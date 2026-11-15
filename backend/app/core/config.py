from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

from app.db.errors import DatabaseConfigurationError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_name: str = "FLARE Scientific Intelligence API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"
    # Optional for the existing API-only mode; required by every DB operation.
    database_url: SecretStr | None = None
    test_database_url: SecretStr | None = None
    db_pool_size: int = Field(default=5, ge=1, le=100)
    db_max_overflow: int = Field(default=5, ge=0, le=100)
    db_pool_timeout: float = Field(default=5, gt=0, le=60)
    db_pool_recycle: int = Field(default=1800, ge=1)
    db_connect_timeout: int = Field(default=5, ge=1, le=60)

    # LLM Scientific Intelligence Layer (Milestone 10.5)
    llm_provider: str = Field(default="ollama", description="LLM provider: 'ollama', 'mock', etc.")
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", description="Ollama API base URL")
    llm_model: str = Field(default="qwen2.5:3b", description="Model name for synthesis")
    llm_timeout_seconds: float = Field(default=30.0, gt=0, le=180, description="HTTP timeout for LLM calls")
    llm_api_key: SecretStr | None = Field(default=None, description="Optional API key for external providers")

    def require_database_url(self, *, test: bool = False) -> URL:
        """Validate on DB use; never put an input URL in validation errors."""
        secret = self.test_database_url if test else self.database_url
        if secret is None or not secret.get_secret_value().strip():
            raise DatabaseConfigurationError("Database URL is required")
        try:
            value = secret.get_secret_value()
            if any(character.isspace() for character in value):
                raise ValueError
            url = make_url(value)
            if (url.drivername != "postgresql+psycopg" or not url.host
                    or not url.username or not url.database
                    or (url.port is not None and not 1 <= url.port <= 65535)):
                raise ValueError
            # Connection endpoints/credentials cannot be overridden in query args.
            if set(url.query) - {"sslmode", "sslrootcert", "application_name"}:
                raise ValueError
        except (ValueError, TypeError, ArgumentError):
            # SQLAlchemy URL parsing exceptions can embed the original input.
            raise DatabaseConfigurationError("Invalid PostgreSQL configuration") from None

        # Test database isolation enforcement
        if test:
            protected_names = {
                "flare", "flare_dev", "flare_development", "flare_prod", "flare_production",
                "production", "prod", "development", "dev", "master", "main", "postgres"
            }
            if url.database and url.database.lower() in protected_names:
                raise DatabaseConfigurationError(
                    f"Test database cannot use protected database name: {url.database}"
                )
            if self.database_url is not None:
                dev_str = self.database_url.get_secret_value().strip()
                if dev_str and not any(character.isspace() for character in dev_str):
                    dev_url = None
                    try:
                        dev_url = make_url(dev_str)
                    except (ValueError, TypeError, ArgumentError):
                        dev_url = None
                    if dev_url is not None:
                        if (url.host == dev_url.host and (url.port or 5432) == (dev_url.port or 5432)
                                and url.database == dev_url.database):
                            raise DatabaseConfigurationError(
                                "Test database cannot be the same as the development or production database"
                            )

        return url

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_prefix(cls, value: str) -> str:
        if not value.startswith("/") or value.endswith("/"):
            raise ValueError("API prefix must begin with / and have no trailing slash")
        return value

    @field_validator("frontend_origin")
    @classmethod
    def validate_origin(cls, value: str) -> str:
        from urllib.parse import urlsplit

        parsed = urlsplit(value)
        if (parsed.scheme not in {"http", "https"} or not parsed.netloc
                or parsed.path or parsed.query or parsed.fragment
                or parsed.username or parsed.password):
            raise ValueError("FRONTEND_ORIGIN must be one HTTP(S) origin without a path")
        return value
