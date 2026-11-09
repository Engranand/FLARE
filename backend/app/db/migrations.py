from pathlib import Path

from alembic.config import Config

from app.core.config import Settings


def migration_config(settings: Settings | None = None) -> Config:
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    if settings is not None:
        config.attributes["settings"] = settings
    return config
