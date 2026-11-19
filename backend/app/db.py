from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row

from app.core.config import settings


def connect() -> psycopg.Connection:
    """Create a fresh PostgreSQL connection with dict rows."""
    return psycopg.connect(**settings.db_conninfo, row_factory=dict_row)


def get_db() -> Iterator[psycopg.Connection]:
    """Yield a connection and commit its work when the request succeeds.

    psycopg opens an implicit transaction on the first statement. Endpoints use
    ``with conn.transaction()`` for writes, but any earlier read would turn that
    into a savepoint and the implicit transaction was never committed when the
    connection closed. Committing here makes every successful request durable
    and rolls back cleanly when the endpoint raises.
    """
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
