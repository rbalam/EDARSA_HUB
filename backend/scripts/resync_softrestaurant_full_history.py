"""Backfill historico completo SoftRestaurant para ISCAM/Finanzas.

Descubre unidades activas mediante PosRuntimeResolver y fechas minimas directamente
desde cada POS. Procesa ventanas mensuales e invoca los contratos canonicos existentes:
- inteligencia_comercial_enrich.enrich_unidad -> Finanzas_CortesCaja_DetallePagos
- cortes_z_runtime_sync.sync_cortes_z_context -> Finanzas_CortesCaja

No imprime secretos. Requiere --execute para escribir.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta

from core.connections.pos_runtime_resolver import list_pos_runtime_contexts
from core.sql_first.connection_factory import get_external_sql_connection
from core.system_type_utils import is_softrestaurant_system
from core.scheduler.jobs.inteligencia_comercial_enrich import enrich_unidad
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


def _origin_bounds(context):
    conn = get_external_sql_connection(context.external_connection_config(as_dict=True))
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(
            """
            SELECT
              MIN(CASE WHEN cierre IS NOT NULL THEN cierre END) AS min_corte,
              MAX(CASE WHEN cierre IS NOT NULL THEN cierre END) AS max_corte,
              MIN(apertura) AS min_turno,
              MAX(COALESCE(cierre, apertura)) AS max_turno
            FROM turnos
            """
        )
        turno = (cur.fetchone() or {})
        cur.execute(
            """
            SELECT MIN(t.apertura) AS min_pago, MAX(t.apertura) AS max_pago
            FROM chequespagos cp
            INNER JOIN cheques ch ON ch.folio = cp.folio
            INNER JOIN turnos t ON t.idturno = ch.idturno
            WHERE ch.cancelado = 0 AND ch.total > 0
            """
        )
        pago = (cur.fetchone() or {})
        return {
            "min_corte": turno.get("min_corte"),
            "max_corte": turno.get("max_corte"),
            "min_pago": pago.get("min_pago") or turno.get("min_turno"),
            "max_pago": pago.get("max_pago") or turno.get("max_turno"),
        }
    finally:
        conn.close()


def _iso(dt):
    return dt.isoformat() if dt else None


def _run_unit(context, execute: bool):
    bounds = _origin_bounds(context)
    print(json.dumps({
        "event": "origin_bounds",
        "unidad": context.unidad_codigo,
        "min_pago": _iso(bounds["min_pago"]),
        "max_pago": _iso(bounds["max_pago"]),
        "min_corte": _iso(bounds["min_corte"]),
        "max_corte": _iso(bounds["max_corte"]),
    }, ensure_ascii=False, default=str))

    if not execute:
        return {"unidad": context.unidad_codigo, "status": "DRY_RUN", "bounds": bounds}

    errors = []
    payment_windows = 0
    corte_windows = 0
    pagos_insertados = 0

    pstart = bounds.get("min_pago")
    pend = bounds.get("max_pago")
    if pstart and pend:
        pend_exclusive = pend + timedelta(days=1)
        for fi, ff in _month_windows(pstart, pend_exclusive):
            result = enrich_unidad(
                context.unidad_codigo,
                fi.strftime("%Y-%m-%d"),
                ff.strftime("%Y-%m-%d"),
                dry_run=False,
            )
            payment_windows += 1
            pagos_insertados += int(result.get("pagos_insertados") or 0)
            print(json.dumps({"event": "payments_window", "unidad": context.unidad_codigo, "fi": fi.isoformat(), "ff": ff.isoformat(), "result": result}, ensure_ascii=False, default=str))
            if result.get("error"):
                errors.append({"domain": "payments", "fi": fi.isoformat(), "ff": ff.isoformat(), "error": result.get("error")})
                break

    cstart = bounds.get("min_corte")
    cend = bounds.get("max_corte")
    if cstart and cend and not errors:
        cend_exclusive = cend + timedelta(days=1)
        for fi, ff in _month_windows(cstart, cend_exclusive):
            result = sync_cortes_z_context(
                context,
                fecha_desde=fi,
                fecha_hasta=ff,
                tipo_ejecucion="FULL_HISTORY_BACKFILL",
            )
            corte_windows += 1
            print(json.dumps({"event": "cortes_window", "unidad": context.unidad_codigo, "fi": fi.isoformat(), "ff": ff.isoformat(), "result": result}, ensure_ascii=False, default=str))
            if result.get("estatus") != "COMPLETADO":
                errors.append({"domain": "cortes", "fi": fi.isoformat(), "ff": ff.isoformat(), "error": result.get("error") or result.get("stats")})
                break

    return {
        "unidad": context.unidad_codigo,
        "status": "PASS" if not errors else "FAIL",
        "payment_windows": payment_windows,
        "corte_windows": corte_windows,
        "pagos_insertados": pagos_insertados,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Ejecuta escritura idempotente en SQL canonico")
    parser.add_argument("--unit", action="append", default=[], help="Limita a codigo de unidad; repetible")
    args = parser.parse_args()

    contexts = [c for c in list_pos_runtime_contexts() if is_softrestaurant_system(c.system_type)]
    if args.unit:
        wanted = {u.strip().upper() for u in args.unit}
        contexts = [c for c in contexts if c.unidad_codigo.upper() in wanted]
    if not contexts:
        raise SystemExit("FAIL_CLOSED:NO_SOFTRESTAURANT_CONTEXTS")

    print(json.dumps({"event": "start", "execute": args.execute, "units": [c.unidad_codigo for c in contexts]}, ensure_ascii=False))
    results = []
    for context in contexts:
        try:
            results.append(_run_unit(context, args.execute))
        except Exception as exc:
            results.append({"unidad": context.unidad_codigo, "status": "FAIL", "errors": [f"{type(exc).__name__}:{exc}"]})
            if args.execute:
                break
    print(json.dumps({"event": "summary", "results": results}, ensure_ascii=False, default=str))
    if any(r.get("status") == "FAIL" for r in results):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
