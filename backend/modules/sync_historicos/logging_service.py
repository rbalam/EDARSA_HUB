"""Bitacora persistente para Sincronizacion Historica.

Reutiliza dbo.Sync_Logs. La bitacora es evidencia operativa y nunca debe
interrumpir la sincronizacion si el esquema aun no fue migrado.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Mapping, Optional

from core.sql_first.db import get_sql_connection

logger = logging.getLogger(__name__)

SERVICE = "SYNC_HISTORICAL"


def log_event(
    *,
    sync_control_id: Optional[int],
    correlation_id: Optional[str],
    event_code: str,
    level: str,
    message: str,
    operator: str = "WORKER_UNIVERSAL_V1.2",
    payload: Optional[Mapping[str, Any]] = None,
) -> bool:
    try:
        conn = get_sql_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO dbo.Sync_Logs (
                    service, type, message, timestamp, operador,
                    SyncControlID, CorrelationID, EventCode, PayloadJSON
                )
                VALUES (
                    %s, %s, %s, SYSDATETIME(), %s,
                    %s, %s, %s, %s
                )
                """,
                (
                    SERVICE,
                    str(level or "INFO")[:20],
                    str(message or "")[:4000],
                    str(operator or "WORKER_UNIVERSAL_V1.2")[:100],
                    int(sync_control_id) if sync_control_id else None,
                    correlation_id or None,
                    str(event_code or "")[:80] or None,
                    (
                        json.dumps(
                            dict(payload),
                            ensure_ascii=False,
                            default=str,
                            separators=(",", ":"),
                        )
                        if payload
                        else None
                    ),
                ),
            )
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()
    except Exception as exc:
        logger.warning(
            "[SYNC_HISTORICAL][LOG_NON_BLOCKING] %s: %s",
            type(exc).__name__,
            str(exc)[:200],
        )
        return False
