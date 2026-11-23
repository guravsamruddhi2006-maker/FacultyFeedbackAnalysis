from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row

from app.core.config import settings


def connect() -> psycopg.Connection:
    """Create a fresh PostgreSQL connection with dict rows.

    Managed PostgreSQL providers such as Neon suspend idle compute and can
    briefly refuse or stall a new connection while it wakes up. Retrying a
    couple of times with a short backoff prevents a cold start from surfacing
    as a false "database unavailable" error. If every attempt fails, the real
    ``OperationalError`` is raised so the API still reports the outage.
    """
    attempts = max(1, settings.db_connect_retries + 1)
    last_error: psycopg.OperationalError | None = None
    for attempt in range(attempts):
        try:
            return psycopg.connect(
                **settings.db_conninfo,
                row_factory=dict_row,
                connect_timeout=settings.db_connect_timeout,
            )
        except psycopg.OperationalError as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(0.4 * (2**attempt))
    assert last_error is not None
    raise last_error


def get_db() -> Iterator[psycopg.Connection]:
    """Yield a connection and commit its work when the request succeeds.

    psycopg opens an implicit transaction on the first statement. Endpoints use
    ``with conn.transaction()`` for writes, but any earlier read would turn that
    into a savepoint and the implicit transaction was never committed when the
    connection closed. Committing here makes every successful request durable
    and rolls back cleanly when the endpoint raises.
    """
    # Apply the additive self-selection schema once per process before serving
    # the first database-backed request. Imported lazily to avoid a cycle.
    from app.schema import ensure_runtime_schema

    ensure_runtime_schema()

    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def db_transaction() -> Iterator[psycopg.Connection]:
    conn = connect()
    try:
        with conn.transaction():
            yield conn
    finally:
        conn.close()


def fetch_one(conn: psycopg.Connection, sql: str, params: tuple | dict = ()) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def fetch_all(conn: psycopg.Connection, sql: str, params: tuple | dict = ()) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def fetch_scalar(conn: psycopg.Connection, sql: str, params: tuple | dict = ()) -> Any:
    row = fetch_one(conn, sql, params)
    if row is None:
        return None
    return next(iter(row.values()))


def execute(conn: psycopg.Connection, sql: str, params: tuple | dict = ()) -> int:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount
