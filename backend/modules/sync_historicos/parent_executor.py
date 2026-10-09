"""Orquestador de un job padre de Sincronizacion Historica.

El Worker Universal V1.2 ejecuta este entrypoint cerrado. El orquestador:
- procesa hijos atomicos persistidos;
- respeta orden de dependencias;
- continua con unidades independientes ante fallos;
- reintenta con backoff exponencial declarado en metadata;
- honra pause/cancel en limites atomicos seguros;
- no crea otra cola ni otro Worker.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from core.sql_first.db import get_sql_connection

from .atomic_executor import execute_atomic_unit_sync


class HistoricalParentExecutionError(RuntimeError):
    pass


def _utcnow():
    return datetime.now(timezone.utc)


def _json_object(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _load_parent(parent_id: int) -> Dict[str, Any]:
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute(
            """
            SELECT
                SyncControlID, SyncRunID, Status,
                PauseRequested, CancelRequested,
                CorrelationID, RequestedBy, Reason,
                FechaInicio, FechaFin, IsDryRun
            FROM dbo.Sync_Control_Ejecuciones
            WHERE SyncControlID=%s AND RunKind='PARENT'
            """,
            (int(parent_id),),
        )
        row = cur.fetchone()
        return dict(row) if row else {}
    finally:
        cur.close()
        conn.close()


def _children(parent_id: int) -> List[Dict[str, Any]]:
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute(
            """
            SELECT
                SyncControlID, SyncRunID, Status, CodigoSync,
                UnidadNegocioID, ConexionID,
                ExecutionOrder, BlockOrdinal,
                AttemptCount, MaxAttempts,
                PauseRequested, CancelRequested,
                PlanJSON, ErrorMessage
            FROM dbo.Sync_Control_Ejecuciones
            WHERE ParentSyncControlID=%s
              AND RunKind='ATOMIC'
            ORDER BY
                ISNULL(ExecutionOrder,100),
                ISNULL(BlockOrdinal,0),
                SyncControlID
            """,
            (int(parent_id),),
        )
        return [dict(row) for row in (cur.fetchall() or [])]
    finally:
        cur.close()
        conn.close()


def _set_parent_status(
    parent_id: int,
    status: str,
    *,
    error_message: str | None = None,
    finished: bool = False,
) -> None:
    now = _utcnow()
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE dbo.Sync_Control_Ejecuciones
            SET Status=%s,
                ErrorMessage=%s,
                LastHeartbeatUTC=%s,
                UpdatedAtUTC=%s,
                FinishedAtUTC=CASE WHEN %s=1 THEN %s ELSE FinishedAtUTC END,
                FinishedAtMexico=CASE WHEN %s=1 THEN SYSDATETIME() ELSE FinishedAtMexico END
            WHERE SyncControlID=%s AND RunKind='PARENT'
            """,
            (
                status,
                error_message,
                now,
                now,
                1 if finished else 0,
                now,
                1 if finished else 0,
                int(parent_id),
            ),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def _set_retry_at(child_id: int, seconds: int) -> None:
    retry_at = _utcnow() + timedelta(seconds=max(1, int(seconds)))
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE dbo.Sync_Control_Ejecuciones
            SET Status='WAITING_RETRY',
                NextRetryAtUTC=%s,
                UpdatedAtUTC=%s
            WHERE SyncControlID=%s
              AND RunKind='ATOMIC'
              AND Status='FAILED_RETRYABLE'
            """,
            (retry_at, _utcnow(), int(child_id)),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def _clear_retry_at(child_id: int) -> None:
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE dbo.Sync_Control_Ejecuciones
            SET NextRetryAtUTC=NULL, UpdatedAtUTC=%s
            WHERE SyncControlID=%s AND RunKind='ATOMIC'
            """,
            (_utcnow(), int(child_id)),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def _cancel_pending_children(parent_id: int) -> None:
    now = _utcnow()
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE dbo.Sync_Control_Ejecuciones
            SET CancelRequested=1,
                Status='CANCELLED_SAFE',
                CheckpointJSON=%s,
                FinishedAtUTC=%s,
                FinishedAtMexico=SYSDATETIME(),
                UpdatedAtUTC=%s
            WHERE ParentSyncControlID=%s
              AND RunKind='ATOMIC'
              AND Status IN (
                  'QUEUED','WAITING_RETRY','FAILED_RETRYABLE','PAUSED'
              )
            """,
            (
                json.dumps(
                    {"state": "NOT_STARTED_PARENT_CANCELLED"},
                    separators=(",", ":"),
                ),
                now,
                now,
                int(parent_id),
            ),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def _control_requested(parent_id: int) -> str | None:
    parent = _load_parent(parent_id)
    if not parent:
        raise HistoricalParentExecutionError("PARENT_NOT_FOUND")
    if bool(parent.get("CancelRequested")):
        return "CANCEL"
    if bool(parent.get("PauseRequested")):
        return "PAUSE"
    return None


def _retry_delay(child: Dict[str, Any]) -> int:
    plan = _json_object(child.get("PlanJSON"))
    metadata = _json_object(plan.get("metadata"))
    try:
        base = int(metadata.get("retry_backoff_seconds"))
    except (TypeError, ValueError) as exc:
        raise HistoricalParentExecutionError(
            "RETRY_BACKOFF_METADATA_INVALID"
        ) from exc
    if base < 1:
        raise HistoricalParentExecutionError(
            "RETRY_BACKOFF_METADATA_INVALID"
        )
    attempt = max(1, int(child.get("AttemptCount") or 1))
    return min(base * (2 ** max(0, attempt - 1)), 300)


def _progress(parent_id: int) -> Dict[str, int]:
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute(
            """
            SELECT
                COUNT_BIG(*) AS total,
                SUM(CASE WHEN Status='SUCCESS' THEN 1 ELSE 0 END) AS success,
                SUM(CASE WHEN Status='PERMANENT_FAILURE' THEN 1 ELSE 0 END) AS permanent_failure,
                SUM(CASE WHEN Status='CANCELLED_SAFE' THEN 1 ELSE 0 END) AS cancelled,
                SUM(CASE WHEN Status='PAUSED' THEN 1 ELSE 0 END) AS paused
            FROM dbo.Sync_Control_Ejecuciones
            WHERE ParentSyncControlID=%s AND RunKind='ATOMIC'
            """,
            (int(parent_id),),
        )
        row = dict(cur.fetchone() or {})
        return {
            "total": int(row.get("total") or 0),
            "success": int(row.get("success") or 0),
            "permanent_failure": int(row.get("permanent_failure") or 0),
            "cancelled": int(row.get("cancelled") or 0),
            "paused": int(row.get("paused") or 0),
        }
    finally:
        cur.close()
        conn.close()


def execute_parent_job(parent_id: int) -> Dict[str, Any]:
    parent = _load_parent(parent_id)
    if not parent:
        raise HistoricalParentExecutionError("PARENT_NOT_FOUND")
    if str(parent.get("Status") or "") not in {
        "QUEUED",
        "RUNNING",
        "PAUSED",
        "PARTIAL_FAILED",
    }:
        raise HistoricalParentExecutionError(
            "PARENT_STATUS_NOT_RUNNABLE:" + str(parent.get("Status") or "")
        )

    _set_parent_status(parent_id, "RUNNING")
    executed: List[Dict[str, Any]] = []

    while True:
        control = _control_requested(parent_id)
        if control == "CANCEL":
            _cancel_pending_children(parent_id)
            _set_parent_status(parent_id, "CANCELLED_SAFE", finished=True)
            return {
                "success": True,
                "parent_sync_control_id": int(parent_id),
                "status": "CANCELLED_SAFE",
                "progress": _progress(parent_id),
                "executed": executed,
            }
        if control == "PAUSE":
            _set_parent_status(parent_id, "PAUSED")
            return {
                "success": True,
                "parent_sync_control_id": int(parent_id),
                "status": "PAUSED",
                "progress": _progress(parent_id),
                "executed": executed,
            }

        children = _children(parent_id)
        runnable = [
            child
            for child in children
            if child.get("Status")
            in {"QUEUED", "FAILED_RETRYABLE", "WAITING_RETRY"}
        ]

        if not runnable:
            progress = _progress(parent_id)
            if progress["permanent_failure"]:
                status = "PARTIAL_FAILED"
                _set_parent_status(
                    parent_id,
                    status,
                    error_message=(
                        f"{progress['permanent_failure']} unidad(es) "
                        "atomica(s) con fallo permanente."
                    ),
                    finished=True,
                )
                success = False
            elif progress["cancelled"]:
                status = "CANCELLED_SAFE"
                _set_parent_status(parent_id, status, finished=True)
                success = True
            else:
                status = "SUCCESS"
                _set_parent_status(parent_id, status, finished=True)
                success = True
            return {
                "success": success,
                "parent_sync_control_id": int(parent_id),
                "status": status,
                "progress": progress,
                "executed": executed,
            }

        child = runnable[0]
        if child.get("Status") in {"FAILED_RETRYABLE", "WAITING_RETRY"}:
            attempts = int(child.get("AttemptCount") or 0)
            maximum = int(child.get("MaxAttempts") or 1)
            if attempts >= maximum:
                conn = get_sql_connection()
                cur = conn.cursor()
                try:
                    cur.execute(
                        """
                        UPDATE dbo.Sync_Control_Ejecuciones
                        SET Status='PERMANENT_FAILURE',
                            UpdatedAtUTC=%s
                        WHERE SyncControlID=%s
                        """,
                        (_utcnow(), int(child["SyncControlID"])),
                    )
                    conn.commit()
                finally:
                    cur.close()
                    conn.close()
                continue

            delay = _retry_delay(child)
            _set_retry_at(int(child["SyncControlID"]), delay)
            for _ in range(delay):
                control = _control_requested(parent_id)
                if control:
                    break
                time.sleep(1)
            if control:
                continue
            _clear_retry_at(int(child["SyncControlID"]))

        result = execute_atomic_unit_sync(int(child["SyncControlID"]))
        executed.append(
            {
                "sync_control_id": int(child["SyncControlID"]),
                "status": result.get("status"),
                "success": bool(result.get("success")),
            }
        )
        _set_parent_status(parent_id, "RUNNING")
