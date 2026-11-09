from sqlalchemy import Engine, create_engine

from app.core.config import Settings


def create_db_engine(settings: Settings, *, test: bool = False) -> Engine:
    """Construct lazily: no connection, schema creation or migration on import."""
    return create_engine(
        settings.require_database_url(test=test),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,
        connect_args={"connect_timeout": settings.db_connect_timeout},
        isolation_level="SERIALIZABLE",
        echo=False,
        hide_parameters=True,
    )
