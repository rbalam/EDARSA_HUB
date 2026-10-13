#!/usr/bin/env python3
"""Read-only diagnostic for zero closed sales and Cienfuegos open sales."""

import json
import os
from datetime import date, datetime
from decimal import Decimal

from core.db import execute_sql_query
from core.unidades_service import UnidadesService
from modules.comercial_v2.sync_comercial_edarsahub import (
    get_server_connection_config,
    execute_query_on_server,
)
from core.scheduler.jobs.sync_comercial_abiertas_v2_job import (
    QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS,
    QUERY_SOFTRESTAURANT_CERRADAS_HOY,
)

UNITS = ("130MID", "CIENFUEGOS", "ESTELAR", "ORIGEN", "130QRO")
START = "2026-10-10"
END = "2026-10-13"
TARGET = "2026-10-12"

CFG = {
    "host": os.getenv("EDARSAHUB_SQL_HOST"),
    "port": int(os.getenv("EDARSAHUB_SQL_PORT") or 1433),
    "database": os.getenv("EDARSAHUB_SQL_DATABASE") or "EDARSAHUB",
    "username": os.getenv("EDARSAHUB_SQL_USER"),
    "password": os.getenv("EDARSAHUB_SQL_PASSWORD"),
}

def clean(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v

def emit(label, rows):
    if isinstance(rows, dict):
        rows = [rows]
    safe = [{k: clean(v) for k, v in row.items()} for row in (rows or [])]
    print(label + "=" + json.dumps(safe, ensure_ascii=False, default=str), flush=True)

def hub(sql):
    return execute_sql_query(
        CFG["host"], CFG["port"], CFG["database"],
        CFG["username"], CFG["password"], sql
    ) or []

def qlist(values):
    return ",".join("'" + str(v).replace("'", "''") + "'" for v in values)

def main():
    rows = UnidadesService.get_all() or []
    selected = [
        r for r in rows
        if str(r.get("codigo") or "").strip().upper() in UNITS
    ]
    codes = [str(r.get("codigo")).strip().upper() for r in selected]
    pks = [str(r.get("unidad_negocio_pk") or r.get("id") or "").strip() for r in selected]
    pks = [x for x in pks if x]

    emit("UNITS", [{
        "codigo": r.get("codigo"),
        "pk": r.get("unidad_negocio_pk") or r.get("id"),
        "server_id": r.get("server_id"),
        "sucursal": r.get("sucursal_origen_id"),
        "system_type": r.get("system_type"),
    } for r in selected])

    emit("BASE_KPI", hub(f"""
SELECT
    unidad_negocio_id,
    CONVERT(varchar(36), unidad_negocio_pk) AS unidad_negocio_pk,
    sucursal_id,
    sistema_origen,
    fecha_operacion,
    ventas_total,
    ventas_cerradas,
    ventas_abiertas,
    total_estimado_dia,
    tickets_total,
    pax_total,
    activo,
    es_demo,
    fuente_original,
    sync_run_id,
    fecha_ultima_actualizacion
FROM dbo.Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id IN ({qlist(codes)})
  AND fecha_operacion BETWEEN '{START}' AND '{END}'
ORDER BY fecha_operacion DESC, unidad_negocio_id
"""))

    emit("BASE_SUMMARY", hub(f"""
SELECT
    unidad_negocio_id,
    COUNT(*) AS rows_total,
    MAX(fecha_operacion) AS fecha_max,
    SUM(CASE WHEN fecha_operacion='{TARGET}' THEN ISNULL(ventas_total,0) ELSE 0 END) AS ventas_target,
    SUM(CASE WHEN fecha_operacion='{TARGET}' THEN ISNULL(tickets_total,0) ELSE 0 END) AS tickets_target,
    SUM(CASE WHEN fecha_operacion='{TARGET}' THEN ISNULL(pax_total,0) ELSE 0 END) AS pax_target
FROM dbo.Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id IN ({qlist(codes)})
  AND fecha_operacion BETWEEN '{START}' AND '{END}'
GROUP BY unidad_negocio_id
ORDER BY unidad_negocio_id
"""))

    emit("RUNTIME_TARGET", hub(f"""
SELECT
    unidad_negocio_id,
    CONVERT(varchar(36), unidad_negocio_pk) AS unidad_negocio_pk,
    sucursal_id,
    sistema_origen,
    fecha_operacion,
    ventas_total,
    ventas_cerradas,
    ventas_abiertas,
    total_estimado_dia,
    tickets_total,
    pax_total,
    fuente_original,
    fecha_sincronizacion
FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
WHERE unidad_negocio_id IN ({qlist(codes)})
  AND fecha_operacion = '{TARGET}'
ORDER BY unidad_negocio_id
"""))

    emit("OPEN_SNAPSHOT", hub(f"""
WITH ranked AS (
    SELECT
        unidad_negocio_id,
        sucursal_id,
        sistema_origen,
        fecha_operacion,
        ventas_abiertas,
        ventas_cerradas_dia,
        total_estimado_dia,
        tickets_abiertos,
        tickets_cerrados_dia,
        pax_abiertos,
        pax_cerrados_dia,
        source_status,
        fuente_original,
        sync_run_id,
        snapshot_timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY unidad_negocio_id
            ORDER BY snapshot_timestamp DESC
        ) AS rn
    FROM dbo.Comercial_Ventas_Dia_Abiertas_v2
    WHERE unidad_negocio_id IN ({qlist(codes)})
)
SELECT *
FROM ranked
WHERE rn = 1
ORDER BY unidad_negocio_id
"""))

    if pks:
        emit("SYNC_LOG", hub(f"""
SELECT TOP (80)
    run_id,
    run_timestamp,
    run_type,
    CONVERT(varchar(36), unidad_negocio_id) AS unidad_ref,
    sucursal_id,
    fecha_inicio,
    fecha_fin,
    status,
    records_processed,
    records_inserted,
    records_updated,
    records_skipped,
    records_errored,
    error_code,
    error_message,
    source_connection_status
FROM dbo.Comercial_SyncLog_v2
WHERE CONVERT(varchar(36), unidad_negocio_id) IN ({qlist(pks)})
ORDER BY run_timestamp DESC
"""))

    cf = next((r for r in selected if str(r.get("codigo") or "").strip().upper() == "CIENFUEGOS"), None)
    if not cf:
        raise RuntimeError("CIENFUEGOS not found in canonical units")

    server_config = get_server_connection_config(str(cf.get("server_id")))
    if not server_config:
        raise RuntimeError("CIENFUEGOS server config not found")

    q_open = QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS.format(fecha_operacion=TARGET)
    open_rows, open_status = execute_query_on_server(server_config, q_open, context="jobs")
    emit("CIENFUEGOS_POS_OPEN", [{
        "status": str(getattr(open_status, "value", open_status)),
        **(open_rows[0] if open_rows else {})
    }])

    q_closed = QUERY_SOFTRESTAURANT_CERRADAS_HOY.format(fecha_operacion=TARGET)
    closed_rows, closed_status = execute_query_on_server(server_config, q_closed, context="jobs")
    emit("CIENFUEGOS_POS_CLOSED", [{
        "status": str(getattr(closed_status, "value", closed_status)),
        **(closed_rows[0] if closed_rows else {})
    }])

    print("DIAG_RESULT=PASS_READ_ONLY", flush=True)

if __name__ == "__main__":
    main()
