"""Ejecutor de una unidad atomica de sincronizacion historica.

Contrato:
- recibe exclusivamente SyncControlID persistido;
- reconstruye contexto desde EDARSAHUB SQL;
- revalida binding sistema/capability/conexion/unidad;
- resuelve un adapter backend registrado;
- ejecuta exactamente un bloque atomico;
- conserva checkpoint y auditoria.

No acepta SQL, comandos, scripts ni rutas desde el job del Worker.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Mapping

from core.sql_first.db import get_sql_connection


AtomicAdapter = Callable[[Mapping[str, Any]], Awaitable[Dict[str, Any]]]


class HistoricalAtomicExecutionError(RuntimeError):
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


def _load_atomic_context(sync_control_id: int) -> Dict[str, Any]:
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute(
            """
            SELECT
                e.SyncControlID,
                e.SyncRunID,
                e.ParentSyncControlID,
                e.Status,
                e.IsDryRun,
                e.FechaInicio,
                e.FechaFin,
                e.ConexionID,
                e.UnidadNegocioID,
                e.CodigoSync,
                e.SistemaTipoID,
                e.SistemaCapacidadID,
                e.SistemaVersionID,
                e.SucursalID,
                e.SucursalOrigenID,
                e.CategoriaCodigo,
                e.EntidadCodigo,
                e.BlockOrdinal,
                e.PlanJSON,
                e.CheckpointJSON,
                e.AttemptCount,
                e.MaxAttempts,
                e.PauseRequested,
                e.CancelRequested,
                u.codigo AS UnidadCodigo,
                u.nombre AS UnidadNombre,
                CONVERT(varchar(36), u.server_id) AS UnidadConexionID,
                u.sucursal_origen_id AS UnidadSucursalOrigenID,
                s.system_type AS ConexionSystemType,
                CONVERT(varchar(36), s.sistema_version_id) AS ConexionSistemaVersionID,
                s.activo AS ConexionActiva,
                sc.Handler,
                sc.HandlerImplementado,
                sc.Activo AS SyncActivo,
                sc.PermiteResync,
                sc.CategoriaCodigo AS RegistryCategoriaCodigo,
                sc.EntidadCodigo AS RegistryEntidadCodigo,
                sc.CampoFecha,
                sc.ClaveNegocio,
                sc.SoportaResume,
                sc.SoportaSafeStop,
                sc.MetadataJSON,
                link.SyncCapacidadID,
                link.Activo AS BindingActivo,
                cap.SistemaCapacidadID,
                cap.CodigoCapacidad,
                cap.Activo AS CapacidadActiva,
                st.CodigoSistema,
                st.Activo AS SistemaActivo
            FROM dbo.Sync_Control_Ejecuciones e
            JOIN dbo.Unidades_Negocio u
              ON u.id=e.UnidadNegocioID
            JOIN dbo.Servidores_Conexiones s
              ON s.id=e.ConexionID
            JOIN dbo.Sistema_Sync_Catalogo sc
              ON sc.Codigo=e.CodigoSync
            JOIN dbo.Sistema_Sync_Capacidades link
              ON link.CodigoSync=sc.Codigo
             AND link.SistemaCapacidadID=e.SistemaCapacidadID
            JOIN dbo.Sistema_Capacidades cap
              ON cap.SistemaCapacidadID=e.SistemaCapacidadID
             AND cap.SistemaTipoID=e.SistemaTipoID
            JOIN dbo.Sistema_Tipos st
              ON st.SistemaTipoID=e.SistemaTipoID
            WHERE e.SyncControlID=%s
              AND e.RunKind='ATOMIC'
            """,
            (int(sync_control_id),),
        )
        rows = list(cur.fetchall() or [])
    finally:
        cur.close()
        conn.close()

    if not rows:
        raise HistoricalAtomicExecutionError("ATOMIC_UNIT_NOT_FOUND")
    if len(rows) != 1:
        raise HistoricalAtomicExecutionError("ATOMIC_SYSTEM_BINDING_AMBIGUOUS")

    row = dict(rows[0])
    if str(row.get("UnidadConexionID") or "").lower() != str(row.get("ConexionID") or "").lower():
        raise HistoricalAtomicExecutionError("UNIT_CONNECTION_MISMATCH")
    if row.get("SucursalOrigenID") and str(row.get("SucursalOrigenID")) != str(row.get("UnidadSucursalOrigenID") or ""):
        raise HistoricalAtomicExecutionError("BRANCH_ORIGIN_MISMATCH")
    if not bool(row.get("ConexionActiva")):
        raise HistoricalAtomicExecutionError("CONNECTION_INACTIVE")
    if not bool(row.get("SyncActivo")) or not bool(row.get("PermiteResync")):
        raise HistoricalAtomicExecutionError("HISTORICAL_CAPABILITY_DISABLED")
    if not bool(row.get("HandlerImplementado")):
        raise HistoricalAtomicExecutionError("HANDLER_NOT_IMPLEMENTED")
    if not bool(row.get("BindingActivo")) or not bool(row.get("CapacidadActiva")) or not bool(row.get("SistemaActivo")):
        raise HistoricalAtomicExecutionError("SYSTEM_CAPABILITY_BINDING_INACTIVE")
    if str(row.get("CategoriaCodigo") or "") != str(row.get("RegistryCategoriaCodigo") or ""):
        raise HistoricalAtomicExecutionError("CATEGORY_METADATA_MISMATCH")
    if str(row.get("EntidadCodigo") or "") != str(row.get("RegistryEntidadCodigo") or ""):
        raise HistoricalAtomicExecutionError("ENTITY_METADATA_MISMATCH")

    row["Plan"] = _json_object(row.get("PlanJSON"))
    row["Metadata"] = _json_object(row.get("MetadataJSON"))
    return row


def _transition_to_running(sync_control_id: int) -> Dict[str, Any]:
    now = _utcnow()
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute(
            """
            SELECT
                SyncControlID, Status, AttemptCount, MaxAttempts,
                PauseRequested, CancelRequested
            FROM dbo.Sync_Control_Ejecuciones WITH (UPDLOCK, HOLDLOCK)
            WHERE SyncControlID=%s AND RunKind='ATOMIC'
            """,
            (int(sync_control_id),),
        )
        row = cur.fetchone()
        if not row:
            raise HistoricalAtomicExecutionError("ATOMIC_UNIT_NOT_FOUND")
        if bool(row.get("CancelRequested")):
            cur.execute(
                """
                UPDATE dbo.Sync_Control_Ejecuciones
                SET Status='CANCELLED_SAFE',
                    FinishedAtUTC=%s,
                    FinishedAtMexico=SYSDATETIME(),
                    UpdatedAtUTC=%s,
                    CheckpointJSON=%s
                WHERE SyncControlID=%s
                """,
                (
                    now,
                    now,
                    json.dumps({"state": "NOT_STARTED_CANCELLED"}, separators=(",", ":")),
                    int(sync_control_id),
                ),
            )
            conn.commit()
            return {"terminal": True, "status": "CANCELLED_SAFE"}
        if bool(row.get("PauseRequested")):
            cur.execute(
                """
                UPDATE dbo.Sync_Control_Ejecuciones
                SET Status='PAUSED', UpdatedAtUTC=%s
                WHERE SyncControlID=%s
                """,
                (now, int(sync_control_id)),
            )
            conn.commit()
            return {"terminal": True, "status": "PAUSED"}
        if str(row.get("Status") or "") not in {"QUEUED", "WAITING_RETRY", "FAILED_RETRYABLE"}:
            raise HistoricalAtomicExecutionError(
                "ATOMIC_STATUS_NOT_RUNNABLE:" + str(row.get("Status") or "")
            )

        attempt = int(row.get("AttemptCount") or 0) + 1
        maximum = int(row.get("MaxAttempts") or 1)
        if attempt > maximum:
            raise HistoricalAtomicExecutionError("MAX_ATTEMPTS_EXCEEDED")

        cur.execute(
            """
            UPDATE dbo.Sync_Control_Ejecuciones
            SET Status='RUNNING',
                AttemptCount=%s,
                LastHeartbeatUTC=%s,
                UpdatedAtUTC=%s,
                ErrorMessage=NULL
            WHERE SyncControlID=%s
            """,
            (attempt, now, now, int(sync_control_id)),
        )
        conn.commit()
        return {"terminal": False, "status": "RUNNING", "attempt": attempt}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def _finish(
    sync_control_id: int,
    *,
    success: bool,
    result: Mapping[str, Any],
) -> Dict[str, Any]:
    now = _utcnow()
    checkpoint = {
        "state": "ATOMIC_BLOCK_COMPLETE" if success else "ATOMIC_BLOCK_FAILED",
        "completed_at_utc": now.isoformat(),
        "result": {
            "success": bool(result.get("success")),
            "records_processed": int(result.get("records_processed") or 0),
            "records_inserted": int(result.get("records_inserted") or 0),
            "records_updated": int(result.get("records_updated") or 0),
            "records_errored": int(result.get("records_errored") or 0),
            "warning_message": str(result.get("warning_message") or "")[:1000],
        },
    }

    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute(
            """
            SELECT CancelRequested, PauseRequested, AttemptCount, MaxAttempts
            FROM dbo.Sync_Control_Ejecuciones WITH (UPDLOCK, HOLDLOCK)
            WHERE SyncControlID=%s
            """,
            (int(sync_control_id),),
        )
        control = cur.fetchone() or {}
        cancel_requested = bool(control.get("CancelRequested"))
        pause_requested = bool(control.get("PauseRequested"))

        attempt_count = int(control.get("AttemptCount") or 0)
        max_attempts = int(control.get("MaxAttempts") or 1)

        if success and cancel_requested:
            status = "CANCELLED_SAFE"
        elif success and pause_requested:
            status = "PAUSED"
        elif success:
            status = "SUCCESS"
        elif attempt_count >= max_attempts:
            status = "PERMANENT_FAILURE"
        else:
            status = "FAILED_RETRYABLE"

        cur.execute(
            """
            UPDATE dbo.Sync_Control_Ejecuciones
            SET Status=%s,
                RegistrosProcesados=%s,
                RegistrosInsertados=%s,
                RegistrosActualizados=%s,
                RegistrosError=%s,
                ErrorMessage=%s,
                FinishedAtUTC=CASE WHEN %s IN ('SUCCESS','CANCELLED_SAFE') THEN %s ELSE FinishedAtUTC END,
                FinishedAtMexico=CASE WHEN %s IN ('SUCCESS','CANCELLED_SAFE') THEN SYSDATETIME() ELSE FinishedAtMexico END,
                DurationSeconds=%s,
                CheckpointJSON=%s,
                LastHeartbeatUTC=%s,
                UpdatedAtUTC=%s
            WHERE SyncControlID=%s
            """,
            (
                status,
                int(result.get("records_processed") or 0),
                int(result.get("records_inserted") or 0),
                int(result.get("records_updated") or 0),
                int(result.get("records_errored") or 0),
                (str(result.get("error_message") or "")[:4000] or None),
                status,
                now,
                status,
                int(result.get("duration_seconds") or 0),
                json.dumps(checkpoint, ensure_ascii=False, separators=(",", ":")),
                now,
                now,
                int(sync_control_id),
            ),
        )
        conn.commit()
        return {"status": status, "checkpoint": checkpoint}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


async def _execute_comercial_ventas_cerradas(context: Mapping[str, Any]) -> Dict[str, Any]:
    """Adapter certificado que reutiliza el handler oficial existente."""
    from api.admin_scheduler_resync import (
        _ejecutar_dry_run,
        _ejecutar_sync_real,
        _get_unidad_config,
    )

    unit_code = str(context.get("UnidadCodigo") or "").strip().upper()
    config = _get_unidad_config(unit_code)
    if not config:
        return {"success": False, "error_message": "UNIT_CONFIG_NOT_FOUND"}

    if str(config.get("server_id") or "").lower() != str(context.get("ConexionID") or "").lower():
        return {"success": False, "error_message": "UNIT_CONFIG_CONNECTION_MISMATCH"}

    if bool(context.get("IsDryRun")):
        return await _ejecutar_dry_run(
            unit_code,
            config,
            context["FechaInicio"],
            context["FechaFin"],
        )

    return await _ejecutar_sync_real(
        unit_code,
        config,
        context["FechaInicio"],
        context["FechaFin"],
        str(context["SyncRunID"]),
    )


_ATOMIC_ADAPTERS: Dict[str, AtomicAdapter] = {
    "comercial_ventas_cerradas": _execute_comercial_ventas_cerradas,
}


def registered_atomic_handlers():
    return tuple(sorted(_ATOMIC_ADAPTERS))


async def execute_atomic_unit(sync_control_id: int) -> Dict[str, Any]:
    control = _transition_to_running(sync_control_id)
    if control.get("terminal"):
        return {
            "success": control.get("status") in {"PAUSED", "CANCELLED_SAFE"},
            "sync_control_id": int(sync_control_id),
            "status": control.get("status"),
            "executed": False,
        }

    try:
        context = _load_atomic_context(sync_control_id)
        capability_key = str(context.get("CodigoSync") or "").strip()
        adapter = _ATOMIC_ADAPTERS.get(capability_key)
        if not adapter:
            raise HistoricalAtomicExecutionError(
                "ATOMIC_HANDLER_NOT_REGISTERED:" + capability_key
            )
        result = await adapter(context)
        success = bool(result.get("success"))
        final = _finish(sync_control_id, success=success, result=result)
        return {
            "success": success,
            "sync_control_id": int(sync_control_id),
            "sync_run_id": context.get("SyncRunID"),
            "capability_key": capability_key,
            "system_code": context.get("CodigoSistema"),
            "unit_code": context.get("UnidadCodigo"),
            "status": final["status"],
            "result": dict(result),
        }
    except Exception as exc:
        error_result = {
            "success": False,
            "error_message": f"{type(exc).__name__}: {str(exc)[:1000]}",
        }
        final = _finish(sync_control_id, success=False, result=error_result)
        return {
            "success": False,
            "sync_control_id": int(sync_control_id),
            "status": final["status"],
            "error_message": error_result["error_message"],
        }


def execute_atomic_unit_sync(sync_control_id: int) -> Dict[str, Any]:
    return asyncio.run(execute_atomic_unit(int(sync_control_id)))
