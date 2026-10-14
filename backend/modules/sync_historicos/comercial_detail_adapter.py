"""Adapter historico atomico para dbo.Sync_Sales.

Aislado de los sincronizadores protegidos de Ventas del Dia y Ventas Cerradas.
Resuelve el POS con PosRuntimeResolver y reutiliza unicamente el backfill historico
existente de Sync_Sales para extraccion/carga idempotente.
"""
from __future__ import annotations

import time
from datetime import timedelta
from typing import Any, Dict, Mapping

from core.connections.pos_runtime_resolver import resolve_pos_runtime_context
from core.system_type_utils import is_mpro_system, is_softrestaurant_system


def _runtime_config(runtime) -> Dict[str, Any]:
    host = (
        f"{runtime.host}\\{runtime.instance}"
        if runtime.instance
        else runtime.host
    )
    return {
        "host": host,
        "port": runtime.port,
        "database": runtime.database,
        "username": runtime.username,
        "password": runtime.password,
        "system_type": runtime.system_type,
        "sucursal_origen_id": runtime.sucursal_origen_id,
    }


async def execute_comercial_ventas_detalle(
    context: Mapping[str, Any],
) -> Dict[str, Any]:
    from scripts import pilot_backfill_sync_sales as backfill

    started = time.monotonic()
    unit_code = str(context.get("UnidadCodigo") or "").strip().upper()
    if not unit_code:
        return {"success": False, "error_message": "UNIT_CODE_MISSING"}

    runtime = resolve_pos_runtime_context(unit_code)
    expected_connection = str(context.get("ConexionID") or "").strip().lower()
    if str(runtime.server_id).strip().lower() != expected_connection:
        return {
            "success": False,
            "error_message": "UNIT_CONFIG_CONNECTION_MISMATCH",
        }

    start = context.get("FechaInicio")
    end = context.get("FechaFin")
    if start is None or end is None:
        return {"success": False, "error_message": "DATE_RANGE_MISSING"}

    # El backfill historico usa fin exclusivo; la unidad atomica persiste fin
    # inclusivo, por eso se avanza un dia sin ampliar el scope del bloque.
    fi = start.isoformat()
    ff = (end + timedelta(days=1)).isoformat()
    cfg = _runtime_config(runtime)

    if is_mpro_system(runtime.system_type):
        rows = backfill.extract_mpro_twopass(cfg, fi, ff)
    elif is_softrestaurant_system(runtime.system_type):
        rows = backfill.extract_softrestaurant_twopass(cfg, fi, ff)
    else:
        return {
            "success": False,
            "error_message": "SYSTEM_NOT_SUPPORTED_FOR_SALES_DETAIL",
        }

    for row in rows:
        row["UnidadNegocio"] = unit_code

    metrics = backfill.load_to_sync_sales(
        rows,
        unit_code,
        fi,
        ff,
        bool(context.get("IsDryRun")),
    )
    error = str(metrics.get("error") or "").strip()
    processed = int(metrics.get("tickets_extraidos") or len(rows) or 0)
    inserted = int(metrics.get("inserted") or 0)

    return {
        "success": not bool(error),
        "records_processed": processed,
        "records_inserted": inserted,
        "records_updated": 0,
        "records_errored": 1 if error else 0,
        "duration_seconds": int(max(0, time.monotonic() - started)),
        "warning_message": (
            f"duplicados={int(metrics.get('tickets_duplicados') or 0)}"
        ),
        "error_message": error or None,
    }
