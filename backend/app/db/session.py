from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException, Request
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """One unit of work; commits are explicit, never deferred until response cleanup."""
    with factory() as session:
        try:
            yield session
        except BaseException:
            session.rollback()
            raise
        finally:
            # Also discard uncommitted successful work rather than implicit commit.
            if session.in_transaction():
                session.rollback()


def get_session(request: Request) -> Iterator[Session]:
    factory = request.app.state.session_factory
    if factory is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        with session_scope(factory) as session:
            yield session
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
