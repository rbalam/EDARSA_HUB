"""Backfill historico completo MPRO para Finanzas_CortesCaja.

Resuelve una unica unidad MPRO desde el catalogo canonico, descubre MIN/MAX
directamente en Comanda_Corte y procesa ventanas mensuales usando el sincronizador
canonico idempotente. No imprime secretos. Requiere --execute para escribir.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta

from modules.finanzas.canonical_sync_units import get_canonical_finance_sync_units
from modules.finanzas.sync_cortes_mpro import get_unidad_info_mpro, get_mpro_connection, sincronizar_unidad_mpro


def _month_windows(start: datetime, end: datetime):
    cur = datetime(start.year, start.month, 1)
    while cur < end:
        if cur.month == 12:
            nxt = datetime(cur.year + 1, 1, 1)
        else:
            nxt = datetime(cur.year, cur.month + 1, 1)
        yield max(cur, start), min(nxt, end)
        cur = nxt


def _resolve_unit(code: str):
    wanted = code.strip().upper()
    rows = get_canonical_finance_sync_units('MANAGEMENTPRO')
    matches = [r for r in rows if str(r.get('unidad_negocio_codigo') or '').strip().upper() == wanted]
    if len(matches) != 1:
        raise RuntimeError(f'FAIL_CLOSED:MPRO_UNIT_NOT_UNIQUE:{wanted}')
    return matches[0]


def _origin_bounds(unit):
    info = get_unidad_info_mpro(unit['unidad_negocio_nombre'])
    if not info:
        raise RuntimeError('FAIL_CLOSED:MPRO_CONNECTION_NOT_FOUND')
    conn = get_mpro_connection(info)
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("""
            SELECT MIN(Cc_Fecha) AS min_fecha, MAX(Cc_Fecha) AS max_fecha, COUNT_BIG(*) AS total_rows
            FROM Comanda_Corte
            WHERE Sc_Cve_Sucursal = %s
              AND (Es_Cve_Estado IS NULL OR Es_Cve_Estado <> 'BAJA')
        """, (unit['sucursal_origen_id'],))
        row = cur.fetchone() or {}
        return row.get('min_fecha'), row.get('max_fecha'), int(row.get('total_rows') or 0)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--unit', required=True)
    args = parser.parse_args()
    unit = _resolve_unit(args.unit)
    min_fecha, max_fecha, total_rows = _origin_bounds(unit)
    print(json.dumps({'event':'origin_bounds','unidad':unit['unidad_negocio_codigo'],'sucursal':unit['sucursal_origen_id'],'min_fecha':min_fecha.isoformat() if min_fecha else None,'max_fecha':max_fecha.isoformat() if max_fecha else None,'total_rows':total_rows}, ensure_ascii=False))
    if not min_fecha or not max_fecha:
        raise SystemExit('FAIL_CLOSED:MPRO_ORIGIN_EMPTY')
    if not args.execute:
        print(json.dumps({'event':'summary','unidad':unit['unidad_negocio_codigo'],'status':'DRY_RUN','windows':0,'origin_rows':total_rows}, ensure_ascii=False))
        return
    end = max_fecha + timedelta(days=1)
    windows = 0
    totals = {'leidos':0,'insertados':0,'actualizados':0,'omitidos':0,'errores':0}
    errors = []
    for fi, ff in _month_windows(min_fecha, end):
        result = sincronizar_unidad_mpro(unit['unidad_negocio_nombre'], fecha_desde=fi, fecha_hasta=ff)
        windows += 1
        stats = result.get('stats') or {}
        for key in totals:
            totals[key] += int(stats.get(key) or 0)
        safe = {'event':'window','unidad':unit['unidad_negocio_codigo'],'fi':fi.isoformat(),'ff':ff.isoformat(),'estatus':result.get('estatus'),'stats':stats}
        print(json.dumps(safe, ensure_ascii=False, default=str))
        if result.get('estatus') != 'COMPLETADO' or int(stats.get('errores') or 0) != 0:
            errors.append({'fi':fi.isoformat(),'ff':ff.isoformat(),'estatus':result.get('estatus'),'error_type':type(result.get('error')).__name__ if result.get('error') is not None else None})
            break
    status = 'PASS' if not errors else 'FAIL'
    print(json.dumps({'event':'summary','unidad':unit['unidad_negocio_codigo'],'status':status,'windows':windows,'origin_rows':total_rows,'stats':totals,'error_count':len(errors)}, ensure_ascii=False, default=str))
    if errors:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
