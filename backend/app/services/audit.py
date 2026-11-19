from __future__ import annotations

import json
from typing import Any

import psycopg

from app.core.deps import Principal, client_ip
from fastapi import Request


def write_audit(
    conn: psycopg.Connection,
    actor: Principal,
    action: str,
    *,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    details: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit_logs
                (actor_role, actor_id, action, entity_type, entity_id, details, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
            """,
            (
                actor.role,
                actor.id,
                action,
                entity_type,
                str(entity_id) if entity_id is not None else None,
                json.dumps(details or {}),
                client_ip(request) if request else None,
            ),
        )
