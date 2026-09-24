"""Backfill historico completo MPRO para Finanzas_CortesCaja y pagos ISCAM.

Resuelve una unica unidad MPRO desde el catalogo canonico, descubre MIN/MAX
directamente en origen y procesa cortes por mes y pagos por dia. No imprime
secretos. Requiere --execute para escribir.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta

from core.connections.pos_runtime_resolver import resolve_pos_runtime_context
from core.scheduler.jobs.inteligencia_comercial_enrich import resync_pagos_unidad
from core.sql_first.connection_factory import get_external_sql_connection
from modules.finanzas.cortes_z_runtime_sync import sync_cortes_z_context


def _month_windows(start: datetime, end: datetime):
    cur = datetime(start.year, start.month, 1)
    while cur < end:
        if cur.month == 12:
            nxt = datetime(cur.year + 1, 1, 1)
        else:
            nxt = datetime(cur.year, cur.month + 1, 1)
        yield max(cur, start), min(nxt, end)
        cur = nxt


def _day_windows(start: datetime, end: datetime):
    cur = datetime(start.year, start.month, start.day)
    while cur < end:
        nxt = min(cur + timedelta(days=1), end)
        yield cur, nxt
        cur = nxt


def _resolve_unit(code: str):
    return resolve_pos_runtime_context(
        code.strip().upper(),
        expected_system_types=["MANAGEMENTPRO"],
    )


def _cursor_dict(conn):
    try:
        return conn.cursor(as_dict=True)
    except TypeError:
        return conn.cursor()


def _one_dict(cur):
    row = cur.fetchone()
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    columns = [item[0] for item in (cur.description or [])]
    return {columns[index]: row[index] for index in range(len(columns))}


def _origin_bounds(context):
    if not context.sucursal_origen_id:
        raise RuntimeError(f"FAIL_CLOSED:MPRO_BRANCH_MISSING:{context.unidad_codigo}")
    conn = get_external_sql_connection(context.external_connection_config(as_dict=True))
    try:
        cur = _cursor_dict(conn)
        cur.execute(
            """
            SELECT MIN(Cc_Fecha) AS min_fecha, MAX(Cc_Fecha) AS max_fecha, COUNT_BIG(*) AS total_rows
            FROM Comanda_Corte
            WHERE Sc_Cve_Sucursal = %s
              AND (Es_Cve_Estado IS NULL OR Es_Cve_Estado <> 'BAJA')
            """,
            (context.sucursal_origen_id,),
        )
        row = _one_dict(cur)
        return row.get("min_fecha"), row.get("max_fecha"), int(row.get("total_rows") or 0)
    finally:
        conn.close()


def _payment_bounds(context):
    conn = get_external_sql_connection(context.external_connection_config(as_dict=True))
    try:
        cur = _cursor_dict(conn)
        cur.execute(
            """
            SELECT MIN(Vn_Fecha) AS min_fecha, MAX(Vn_Fecha) AS max_fecha, COUNT_BIG(*) AS total_rows
            FROM Venta_Encabezado
            WHERE Sc_Cve_Sucursal = %s
              AND ISNULL(Es_Cve_Estado, '') <> 'CA'
              AND Vn_Precio_Neto_Importe > 0
            """,
            (context.sucursal_origen_id,),
        )
        row = _one_dict(cur)
        return row.get("min_fecha"), row.get("max_fecha"), int(row.get("total_rows") or 0)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--unit', required=True)
    args = parser.parse_args()

    context = _resolve_unit(args.unit)
    cut_min, cut_max, cut_rows = _origin_bounds(context)
    pay_min, pay_max, pay_rows = _payment_bounds(context)

    print(json.dumps({
        "event": "origin_bounds",
        "unidad": context.unidad_codigo,
        "sucursal": context.sucursal_origen_id,
        "cortes_min_fecha": cut_min.isoformat() if cut_min else None,
        "cortes_max_fecha": cut_max.isoformat() if cut_max else None,
        "cortes_rows": cut_rows,
        "pagos_min_fecha": pay_min.isoformat() if pay_min else None,
        "pagos_max_fecha": pay_max.isoformat() if pay_max else None,
        "pagos_source_rows": pay_rows,
    }, ensure_ascii=False))

    if not pay_min or not pay_max:
        raise SystemExit("FAIL_CLOSED:MPRO_PAYMENTS_ORIGIN_EMPTY")

    if not args.execute:
        print(json.dumps({
            "event": "summary",
            "unidad": context.unidad_codigo,
            "status": "DRY_RUN",
            "corte_windows": 0,
            "payment_windows": 0,
            "cortes_origin_rows": cut_rows,
            "payments_origin_rows": pay_rows,
        }, ensure_ascii=False))
        return

    totals = {"leidos": 0, "insertados": 0, "actualizados": 0, "omitidos": 0, "errores": 0}
    errors = []
    corte_windows = 0
    payment_windows = 0
    pagos_extraidos = 0
    pagos_insertados = 0

    if cut_min and cut_max:
        cut_end = cut_max + timedelta(days=1)
        for fi, ff in _month_windows(cut_min, cut_end):
            result = sync_cortes_z_context(
                context,
                fecha_desde=fi,
                fecha_hasta=ff,
                tipo_ejecucion="FULL_HISTORY_BACKFILL",
            )
            corte_windows += 1
            stats = result.get("stats") or {}
            for key in totals:
                totals[key] += int(stats.get(key) or 0)
            print(json.dumps({
                "event": "corte_window",
                "unidad": context.unidad_codigo,
                "fi": fi.isoformat(),
                "ff": ff.isoformat(),
                "estatus": result.get("estatus"),
                "stats": stats,
            }, ensure_ascii=False, default=str))
            if result.get('estatus') != 'COMPLETADO' or int(stats.get("errores") or 0) != 0:
                errors.append({"domain": "cortes", "fi": fi.isoformat(), "ff": ff.isoformat(), "estatus": result.get("estatus")})
                break

    if not errors:
        pay_end = datetime(pay_max.year, pay_max.month, pay_max.day) + timedelta(days=1)
        for fi, ff in _day_windows(pay_min, pay_end):
            result = resync_pagos_unidad(
                context.unidad_codigo,
                fi.strftime("%Y-%m-%d"),
                ff.strftime("%Y-%m-%d"),
                dry_run=False,
            )
            payment_windows += 1
            pagos_extraidos += int(result.get("pagos_extraidos") or 0)
            pagos_insertados += int(result.get("pagos_insertados") or 0)
            print(json.dumps({
                "event": "payment_window",
                "unidad": context.unidad_codigo,
                "fi": fi.isoformat(),
                "ff": ff.isoformat(),
                "pagos_extraidos": int(result.get("pagos_extraidos") or 0),
                "pagos_insertados": int(result.get("pagos_insertados") or 0),
                "status": "FAIL" if result.get("error") else "PASS",
            }, ensure_ascii=False, default=str))
            if result.get("error"):
                errors.append({
                    "domain": "payments",
                    "fi": fi.isoformat(),
                    "ff": ff.isoformat(),
                    "error_type": str(result.get("error")).split(":", 1)[0][:80],
                })
                break

    status = "PASS" if not errors else "FAIL"
    print(json.dumps({
        "event": "summary",
        "unidad": context.unidad_codigo,
        "status": status,
        "corte_windows": corte_windows,
        "payment_windows": payment_windows,
        "cortes_origin_rows": cut_rows,
        "payments_origin_rows": pay_rows,
        "pagos_extraidos": pagos_extraidos,
        "pagos_insertados": pagos_insertados,
        "stats": totals,
        "error_count": len(errors),
    }, ensure_ascii=False, default=str))

    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
