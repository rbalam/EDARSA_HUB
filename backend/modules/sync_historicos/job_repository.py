"""Persistencia del planner historico sobre el ledger canonico.

No crea colas alternativas. La entrega al WORKER UNIVERSAL V1.2 corresponde
a la fase de integración del Worker; este repositorio solo persiste el plan.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence

from core.sql_first.db import get_sql_connection

from .planner import HistoricalPlan, plan_json


ACTIVE_ATOMIC_STATES = (
    "QUEUED",
    "RUNNING",
    "WAITING_RETRY",
    "PAUSED",
    "CANCEL_REQUESTED",
)


class HistoricalJobConflict(RuntimeError):
    pass


def _run_id(prefix: str, correlation_id: str, suffix: str = "") -> str:
    compact = correlation_id.replace("-", "")
    value = f"{prefix}-{compact}{suffix}"
    return value[:50]


def find_active_atomic_duplicates(
    atomic_keys: Sequence[str],
) -> List[Dict[str, Any]]:
    keys = [str(value)[:200] for value in atomic_keys if value]
    if not keys:
        return []

    placeholders = ",".join(["%s"] * len(keys))
    states = ",".join(["%s"] * len(ACTIVE_ATOMIC_STATES))
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute(
            f"""
            SELECT
                SyncControlID,
                SyncRunID,
                ParentSyncControlID,
                IdempotencyKey,
                Status
            FROM dbo.Sync_Control_Ejecuciones
            WHERE RunKind='ATOMIC'
              AND IdempotencyKey IN ({placeholders})
              AND Status IN ({states})
            ORDER BY SyncControlID
            """,
            tuple(keys) + ACTIVE_ATOMIC_STATES,
        )
        return list(cur.fetchall() or [])
    finally:
        cur.close()
        conn.close()


def persist_plan(
    plan: HistoricalPlan,
    *,
    requested_by: str,
    reason: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Persiste padre + hijos en una sola transaccion.

    Si existe una unidad atomica activa con la misma IdempotencyKey, falla
    cerrado antes de insertar el nuevo job.
    """
    requested_by = str(requested_by or "").strip()
    reason = str(reason or "").strip()
    if not requested_by:
        raise ValueError("REQUESTED_BY_REQUIRED")
    if len(reason) < 10:
        raise ValueError("REASON_MIN_LENGTH_10")

    atomic_keys = [item.atomic_key for item in plan.atomic_units]
    duplicates = find_active_atomic_duplicates(atomic_keys)
    if duplicates:
        raise HistoricalJobConflict("ACTIVE_ATOMIC_DUPLICATE")

    now_utc = datetime.now(timezone.utc)
    parent_run_id = _run_id("HIST-P", plan.correlation_id)
    parent_idempotency = f"historical-parent:{plan.correlation_id}"[:200]
    parent_payload = plan_json(plan)

    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute("BEGIN TRANSACTION")

        cur.execute(
            """
            INSERT INTO dbo.Sync_Control_Ejecuciones (
                SyncRunID, SyncType, FechaInicio, FechaFin,
                IsDryRun, Status, StartedAtMexico,
                StartedAtUTC, IdempotencyKey,
                RunKind, CorrelationID, PlanJSON,
                AttemptCount, MaxAttempts,
                PauseRequested, CancelRequested,
                RequestedBy, Reason, UpdatedAtUTC
            )
            OUTPUT INSERTED.SyncControlID
            VALUES (
                %s, 'HISTORICAL_PARENT', %s, %s,
                %s, 'QUEUED', SYSDATETIME(),
                %s, %s,
                'PARENT', %s, %s,
                0, 1,
                0, 0,
                %s, %s, %s
            )
            """,
            (
                parent_run_id,
                plan.start,
                plan.end,
                1 if dry_run else 0,
                now_utc,
                parent_idempotency,
                plan.correlation_id,
                parent_payload,
                requested_by,
                reason,
                now_utc,
            ),
        )
        parent_row = cur.fetchone()
        parent_id = int(parent_row["SyncControlID"])

        children: List[Dict[str, Any]] = []
        for index, item in enumerate(plan.atomic_units, start=1):
            child_run_id = _run_id(
                "HIST-A",
                plan.correlation_id,
                f"-{index:06d}",
            )
            child_plan = json.dumps(
                item.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            cur.execute(
                """
                INSERT INTO dbo.Sync_Control_Ejecuciones (
                    SyncRunID, SyncType, ServerID, EmpresaID,
                    FechaInicio, FechaFin,
                    IsDryRun, Status, StartedAtMexico,
                    ConexionID, UnidadNegocioID, CodigoSync,
                    StartedAtUTC, IdempotencyKey,
                    ParentSyncControlID, RunKind, CorrelationID,
                    SistemaTipoID, SistemaCapacidadID, SistemaVersionID, SucursalID,
                    SucursalOrigenID, CategoriaCodigo, EntidadCodigo, BlockOrdinal,
                    ExecutionOrder, PlanJSON, AttemptCount, MaxAttempts,
                    PauseRequested, CancelRequested,
                    RequestedBy, Reason, UpdatedAtUTC
                )
                OUTPUT INSERTED.SyncControlID
                VALUES (
                    %s, 'HISTORICAL_ATOMIC', %s, %s,
                    %s, %s,
                    %s, 'QUEUED', SYSDATETIME(),
                    %s, %s, %s,
                    %s, %s,
                    %s, 'ATOMIC', %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, 0, %s,
                    0, 0,
                    %s, %s, %s
                )
                """,
                (
                    child_run_id,
                    item.connection_id,
                    item.company_id,
                    item.block_start,
                    item.block_end,
                    1 if dry_run else 0,
                    item.connection_id,
                    item.unit_id,
                    item.capability_key,
                    now_utc,
                    item.atomic_key,
                    parent_id,
                    plan.correlation_id,
                    item.system_id,
                    item.system_capability_id,
                    item.system_version_id,
                    item.branch_id,
                    item.branch_origin_id,
                    item.category_key,
                    item.entity_key,
                    item.block_ordinal,
                    item.execution_order,
                    child_plan,
                    item.max_attempts,
                    requested_by,
                    reason,
                    now_utc,
                ),
            )
            row = cur.fetchone()
            children.append(
                {
                    "sync_control_id": int(row["SyncControlID"]),
                    "sync_run_id": child_run_id,
                    "atomic_key": item.atomic_key,
                }
            )

        conn.commit()
        return {
            "parent_sync_control_id": parent_id,
            "parent_sync_run_id": parent_run_id,
            "correlation_id": plan.correlation_id,
            "status": "QUEUED",
            "requested_by": requested_by,
            "total_atomic_units": len(children),
            "children": children,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
