"""Estado y controles cooperativos de jobs historicos persistentes."""
from __future__ import annotations

import json
from typing import Any, Dict

from core.sql_first.db import get_sql_connection
from .logging_service import log_event


def get_parent_status(parent_id: int) -> Dict[str, Any] | None:
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute(
            """
            SELECT
                SyncControlID, SyncRunID, Status, CorrelationID,
                FechaInicio, FechaFin, IsDryRun,
                StartedAtUTC, FinishedAtUTC, UpdatedAtUTC,
                LastHeartbeatUTC, RequestedBy, Reason,
                PauseRequested, CancelRequested,
                WorkerJobID, DispatchCount, ErrorMessage
            FROM dbo.Sync_Control_Ejecuciones
            WHERE SyncControlID=%s AND RunKind='PARENT'
            """,
            (int(parent_id),),
        )
        parent = cur.fetchone()
        if not parent:
            return None

        cur.execute(
            """
            SELECT
                SyncControlID, SyncRunID, Status,
                CodigoSync, UnidadNegocioID, ConexionID,
                CategoriaCodigo, EntidadCodigo,
                FechaInicio, FechaFin,
                ExecutionOrder, BlockOrdinal,
                AttemptCount, MaxAttempts, NextRetryAtUTC,
                RegistrosProcesados, RegistrosInsertados,
                RegistrosActualizados, RegistrosError,
                ErrorMessage, CheckpointJSON,
                UpdatedAtUTC, FinishedAtUTC
            FROM dbo.Sync_Control_Ejecuciones
            WHERE ParentSyncControlID=%s AND RunKind='ATOMIC'
            ORDER BY ISNULL(ExecutionOrder,100),
                     ISNULL(BlockOrdinal,0),
                     SyncControlID
            """,
            (int(parent_id),),
        )
        children = [dict(row) for row in (cur.fetchall() or [])]

        cur.execute(
            """
            SELECT TOP 200
                id, SyncControlID, CorrelationID, EventCode,
                type, message, timestamp, operador, PayloadJSON
            FROM dbo.Sync_Logs
            WHERE SyncControlID=%s
               OR CorrelationID=%s
            ORDER BY timestamp DESC, id DESC
            """,
            (int(parent_id), parent.get("CorrelationID")),
        )
        logs = [dict(row) for row in (cur.fetchall() or [])]
    finally:
        cur.close()
        conn.close()

    counts: Dict[str, int] = {}
    for child in children:
        state = str(child.get("Status") or "UNKNOWN")
        counts[state] = counts.get(state, 0) + 1
        raw_checkpoint = child.get("CheckpointJSON")
        if raw_checkpoint:
            try:
                child["checkpoint"] = json.loads(raw_checkpoint)
            except Exception:
                child["checkpoint"] = None
        child.pop("CheckpointJSON", None)

    total = len(children)
    terminal = sum(
        counts.get(state, 0)
        for state in (
            "SUCCESS",
            "PERMANENT_FAILURE",
            "CANCELLED_SAFE",
        )
    )

    return {
        "parent": dict(parent),
        "children": children,
        "logs": logs,
        "progress": {
            "total": total,
            "terminal": terminal,
            "percent": (
                round(terminal * 100.0 / total, 2)
                if total
                else 0.0
            ),
            "by_status": counts,
        },
    }


def list_parent_jobs(limit: int = 50) -> list[Dict[str, Any]]:
    safe_limit = max(1, min(int(limit), 200))
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute(
            f'''
            SELECT TOP {safe_limit}
                e.SyncControlID, e.SyncRunID, e.Status, e.CorrelationID,
                e.FechaInicio, e.FechaFin, e.IsDryRun,
                e.StartedAtUTC, e.FinishedAtUTC, e.UpdatedAtUTC,
                e.RequestedBy, e.Reason, e.WorkerJobID,
                e.DispatchCount, e.ErrorMessage,
                COUNT(c.SyncControlID) AS TotalAtomicUnits,
                SUM(CASE WHEN c.Status='SUCCESS' THEN 1 ELSE 0 END) AS SuccessCount,
                SUM(CASE WHEN c.Status='PERMANENT_FAILURE' THEN 1 ELSE 0 END) AS FailureCount,
                SUM(CASE WHEN c.Status='CANCELLED_SAFE' THEN 1 ELSE 0 END) AS CancelledCount
            FROM dbo.Sync_Control_Ejecuciones e
            LEFT JOIN dbo.Sync_Control_Ejecuciones c
              ON c.ParentSyncControlID=e.SyncControlID
             AND c.RunKind='ATOMIC'
            WHERE e.RunKind='PARENT'
            GROUP BY
                e.SyncControlID, e.SyncRunID, e.Status, e.CorrelationID,
                e.FechaInicio, e.FechaFin, e.IsDryRun,
                e.StartedAtUTC, e.FinishedAtUTC, e.UpdatedAtUTC,
                e.RequestedBy, e.Reason, e.WorkerJobID,
                e.DispatchCount, e.ErrorMessage
            ORDER BY e.SyncControlID DESC
            '''
        )
        return [dict(row) for row in (cur.fetchall() or [])]
    finally:
        cur.close()
        conn.close()

def request_pause(parent_id: int) -> Dict[str, Any]:
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute(
            """
            SELECT Status
            FROM dbo.Sync_Control_Ejecuciones WITH (UPDLOCK,HOLDLOCK)
            WHERE SyncControlID=%s AND RunKind='PARENT'
            """,
            (int(parent_id),),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("PARENT_NOT_FOUND")
        status = str(row.get("Status") or "")
        if status in {"SUCCESS","CANCELLED_SAFE","PARTIAL_FAILED"}:
            raise ValueError("PARENT_TERMINAL")
        target = "PAUSED" if status in {"QUEUED","ENQUEUE_FAILED"} else "PAUSE_REQUESTED"
        cur.execute(
            """
            UPDATE dbo.Sync_Control_Ejecuciones
            SET PauseRequested=1, Status=%s,
                UpdatedAtUTC=SYSUTCDATETIME()
            WHERE SyncControlID=%s
            """,
            (target, int(parent_id)),
        )
        conn.commit()
        log_event(sync_control_id=int(parent_id), correlation_id=None, event_code="PAUSE_REQUESTED", level="INFO", message=f"Pausa solicitada. Estado: {target}")
        return {"status": target}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def request_cancel(parent_id: int) -> Dict[str, Any]:
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute(
            """
            SELECT Status
            FROM dbo.Sync_Control_Ejecuciones WITH (UPDLOCK,HOLDLOCK)
            WHERE SyncControlID=%s AND RunKind='PARENT'
            """,
            (int(parent_id),),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("PARENT_NOT_FOUND")
        status = str(row.get("Status") or "")
        if status in {"SUCCESS","CANCELLED_SAFE"}:
            conn.commit()
            return {"status": status}
        cur.execute(
            """
            UPDATE dbo.Sync_Control_Ejecuciones
            SET CancelRequested=1,
                PauseRequested=0,
                Status='CANCEL_REQUESTED',
                UpdatedAtUTC=SYSUTCDATETIME()
            WHERE SyncControlID=%s
            """,
            (int(parent_id),),
        )
        conn.commit()
        log_event(sync_control_id=int(parent_id), correlation_id=None, event_code="CANCEL_REQUESTED", level="WARN", message="Detencion segura solicitada.")
        return {"status": "CANCEL_REQUESTED"}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def prepare_resume(
    parent_id: int,
    *,
    retry_failed: bool = False,
) -> Dict[str, Any]:
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute(
            """
            SELECT Status
            FROM dbo.Sync_Control_Ejecuciones WITH (UPDLOCK,HOLDLOCK)
            WHERE SyncControlID=%s AND RunKind='PARENT'
            """,
            (int(parent_id),),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("PARENT_NOT_FOUND")
        status = str(row.get("Status") or "")
        allowed = {
            "PAUSED",
            "PAUSE_REQUESTED",
            "CANCELLED_SAFE",
            "ENQUEUE_FAILED",
        }
        if retry_failed:
            allowed.add("PARTIAL_FAILED")
        if status not in allowed:
            raise ValueError("PARENT_NOT_RESUMABLE:" + status)

        cur.execute(
            """
            UPDATE dbo.Sync_Control_Ejecuciones
            SET PauseRequested=0,
                CancelRequested=0,
                Status='QUEUED',
                ErrorMessage=NULL,
                FinishedAtUTC=NULL,
                FinishedAtMexico=NULL,
                UpdatedAtUTC=SYSUTCDATETIME()
            WHERE SyncControlID=%s
            """,
            (int(parent_id),),
        )
        cur.execute(
            """
            UPDATE dbo.Sync_Control_Ejecuciones
            SET PauseRequested=0,
                CancelRequested=0,
                Status='QUEUED',
                FinishedAtUTC=NULL,
                FinishedAtMexico=NULL,
                NextRetryAtUTC=NULL,
                UpdatedAtUTC=SYSUTCDATETIME()
            WHERE ParentSyncControlID=%s
              AND RunKind='ATOMIC'
              AND Status IN ('PAUSED','CANCELLED_SAFE')
            """,
            (int(parent_id),),
        )
        if retry_failed:
            cur.execute(
                """
                UPDATE dbo.Sync_Control_Ejecuciones
                SET Status='QUEUED',
                    AttemptCount=0,
                    NextRetryAtUTC=NULL,
                    ErrorMessage=NULL,
                    FinishedAtUTC=NULL,
                    FinishedAtMexico=NULL,
                    UpdatedAtUTC=SYSUTCDATETIME()
                WHERE ParentSyncControlID=%s
                  AND RunKind='ATOMIC'
                  AND Status='PERMANENT_FAILURE'
                """,
                (int(parent_id),),
            )
        conn.commit()
        log_event(sync_control_id=int(parent_id), correlation_id=None, event_code="RESUME_REQUESTED", level="INFO", message=("Reanudacion solicitada con reintento de fallidos." if retry_failed else "Reanudacion solicitada."), payload={"retry_failed": bool(retry_failed)})
        return {"status": "QUEUED", "retry_failed": bool(retry_failed)}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
