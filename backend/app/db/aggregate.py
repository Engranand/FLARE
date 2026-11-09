"""Run replayable aggregate operations in fresh SERIALIZABLE transactions."""
from collections.abc import Callable

from sqlalchemy import Connection, Engine
from sqlalchemy.exc import DBAPIError


def run_aggregate_transaction[T](engine: Engine, operation: Callable[[Connection], T], *, attempts: int = 3) -> T:
    """Retry the entire callback, including commit. Keep external side effects outside it."""
    if attempts < 1:
        raise ValueError("attempts must be positive")
    for attempt in range(attempts):
        try:
            with engine.connect().execution_options(isolation_level="SERIALIZABLE") as conn:
                with conn.begin():
                    result = operation(conn)
                return result
        except DBAPIError as exc:
            if getattr(exc.orig, "sqlstate", None) != "40001" or attempt + 1 == attempts:
                raise
    raise AssertionError("unreachable")
