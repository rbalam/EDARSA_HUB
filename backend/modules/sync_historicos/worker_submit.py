"""Publicacion canonica de un parent job al WORKER UNIVERSAL V1.2."""
from __future__ import annotations

from typing import Any, Dict

from core.sql_first.db import get_sql_connection
from tools.mirror_sync import gate_chain_publisher
from tools.mirror_sync.worker_job_factory import canonicalize_job


AUDIT_PROFILE = "sync_historical_parent_status_v1"


class HistoricalWorkerSubmitError(RuntimeError):
    pass


def _reserve_dispatch(parent_id: int) -> Dict[str, Any]:
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute(
            """
            SELECT
                SyncControlID, SyncRunID, CorrelationID,
                DispatchCount, Status
            FROM dbo.Sync_Control_Ejecuciones WITH (UPDLOCK,HOLDLOCK)
            WHERE SyncControlID=%s AND RunKind='PARENT'
            """,
            (int(parent_id),),
        )
        row = cur.fetchone()
        if not row:
            raise HistoricalWorkerSubmitError("PARENT_NOT_FOUND")
        dispatch_count = int(row.get("DispatchCount") or 0) + 1
        job_id = (
            f"SYNC-HIST-P-{int(parent_id)}-D{dispatch_count}"
        )[:121]
        cur.execute(
            """
            UPDATE dbo.Sync_Control_Ejecuciones
            SET DispatchCount=%s,
                WorkerJobID=%s,
                UpdatedAtUTC=SYSUTCDATETIME()
            WHERE SyncControlID=%s
            """,
            (dispatch_count, job_id, int(parent_id)),
        )
        conn.commit()
        return {
            "parent_id": int(parent_id),
            "job_id": job_id,
            "dispatch_count": dispatch_count,
            "correlation_id": str(row.get("CorrelationID") or ""),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def _mark_enqueue_failure(parent_id: int, reason: str) -> None:
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE dbo.Sync_Control_Ejecuciones
            SET Status='ENQUEUE_FAILED',
                ErrorMessage=%s,
                UpdatedAtUTC=SYSUTCDATETIME()
            WHERE SyncControlID=%s AND RunKind='PARENT'
            """,
            (str(reason or "")[:4000], int(parent_id)),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def submit_parent_to_worker(
    parent_id: int,
    *,
    requester_email: str,
) -> Dict[str, Any]:
    reservation = _reserve_dispatch(parent_id)
    job = canonicalize_job(
        {
            "job_id": reservation["job_id"],
            "objective": (
                "Ejecutar el job padre persistido de Sincronizacion "
                "Historica de Tablas mediante unidades atomicas canonicas."
            ),
            "mode": "SYNC_HISTORICAL_PARENT",
            "actions": [],
            "checks": [],
            "parent_sync_control_id": int(parent_id),
            "confirm_sync_historical_parent": True,
            "audit_profile": AUDIT_PROFILE,
            "requester": {
                "email": str(requester_email or "").strip().lower(),
                "source": "sync-historical-api",
                "project": "EDARSAHUB",
                "chat": "historical-sync-module",
            },
            "scheduling": {
                "project_id": "EDARSAHUB",
                "bounded_context": "SYNC_HISTORICAL",
                "priority_class": "NORMAL",
                "fairness_weight": 1,
                "max_parallelism": 1,
                "resource_claims": [
                    f"sync-historical-parent:{int(parent_id)}",
                ],
                "conflict_domains": [
                    f"SYNC_HISTORICAL_PARENT_{int(parent_id)}",
                ],
            },
        }
    )
    result = gate_chain_publisher.submit(job)
    status = str(result.get("status") or "")
    accepted = {
        "PUBLISHED",
        "ALREADY_SUBMITTED",
        "ALREADY_PENDING",
        "ALREADY_PROCESSING",
        "PENDING",
        "PROCESSING",
    }
    if status not in accepted:
        _mark_enqueue_failure(
            parent_id,
            str(result.get("reason") or result.get("errors") or status),
        )
        raise HistoricalWorkerSubmitError(
            "WORKER_ENQUEUE_FAILED:" + status
        )

    return {
        **reservation,
        "worker_status": status,
        "production_touched": bool(
            result.get("production_touched", False)
        ),
    }
