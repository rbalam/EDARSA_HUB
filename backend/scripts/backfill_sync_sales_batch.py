#!/usr/bin/env python3
"""
Backfill por TANDAS (mes × unidad) de detalle a Sync_Sales — SOLO LECTURA del POS.

Reusa la lógica validada del piloto (pilot_backfill_sync_sales):
- Credenciales canónicas (sin hardcode, sin imprimir secretos).
- Solo escribe Sync_Sales. PROHIBIDO tocar Comercial_KPIs_Diarios_v2 / vw_* / KPIs.
- Idempotente por (NumeroTicket, UnidadNegocio, fecha). Por lotes, transaccional, con bitácora.

Itera mes a mes dentro del rango [fecha-inicio, fecha-fin) por cada unidad.

Uso:
  python3 scripts/backfill_sync_sales_batch.py --unidades CIENFUEGOS,ESTELAR,130MID \
      --fecha-inicio 2024-06-01 --fecha-fin 2024-12-01
  (agrega --dry-run para medir sin insertar)
"""
import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path("/app/backend")
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

import pilot_backfill_sync_sales as pilot  # reusa lógica validada
from core.scheduler.jobs.inteligencia_comercial_sync_job import (
    get_unidades_negocio_pos,
    get_pos_config_for_unidad,
    registrar_syncpos_bitacora,
)


def month_ranges(fi: str, ff: str):
    """Genera tuplas (inicio_mes, inicio_mes_siguiente) dentro de [fi, ff)."""
    start = datetime.strptime(fi, "%Y-%m-%d")
    end = datetime.strptime(ff, "%Y-%m-%d")
    cur = datetime(start.year, start.month, 1)
    out = []
    while cur < end:
        if cur.month == 12:
            nxt = datetime(cur.year + 1, 1, 1)
        else:
            nxt = datetime(cur.year, cur.month + 1, 1)
        out.append((cur.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")))
        cur = nxt
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unidades", default="CIENFUEGOS,ESTELAR,130MID")
    ap.add_argument("--fecha-inicio", required=True)
    ap.add_argument("--fecha-fin", required=True, help="exclusivo")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    unidades = [u.strip() for u in args.unidades.split(",") if u.strip()]
    meses = month_ranges(args.fecha_inicio, args.fecha_fin)
    t0 = time.time()

    print(f"[BATCH] Inicio {datetime.now().isoformat()} | unidades={unidades} | "
          f"rango={args.fecha_inicio}..{args.fecha_fin} | meses={len(meses)} | dry_run={args.dry_run}",
          flush=True)
    registrar_syncpos_bitacora("BACKFILL", "TANDA_INICIO",
                               f"{unidades} {args.fecha_inicio}..{args.fecha_fin} dry_run={args.dry_run}",
                               fecha_inicio=args.fecha_inicio, fecha_fin=args.fecha_fin)

    resumen = []
    tot_extra = tot_ins = tot_dup = tot_lineas = 0
    tot_venta = 0.0

    # Resolver config canónica una vez por unidad
    cfg_cache = {}
    for u in unidades:
        rows = get_unidades_negocio_pos([u])
        if not rows:
            print(f"[BATCH][WARN] Unidad {u} no encontrada en canónico; se omite.", flush=True)
            continue
        cfg = get_pos_config_for_unidad(rows[0])
        if not cfg or not cfg.get("host"):
            print(f"[BATCH][WARN] Sin config canónica para {u}; se omite.", flush=True)
            continue
        cfg_cache[u] = (rows[0], cfg)

    for (mi, mf) in meses:
        for u, (urow, cfg) in cfg_cache.items():
            t1 = time.time()
            try:
                rows, ext_s = pilot.extract_from_pos(urow, cfg, mi, mf)
                m = pilot.load_to_sync_sales(rows, urow.get("unidad_codigo"), mi, mf, args.dry_run)
            except Exception as e:
                print(f"[BATCH][ERROR] {u} {mi}: {type(e).__name__}: {e}", flush=True)
                registrar_syncpos_bitacora("BACKFILL", "ERROR", f"{u} {mi}: {e}",
                                           unidad=u, fecha_inicio=mi, fecha_fin=mf)
                resumen.append({"unidad": u, "mes": mi, "error": str(e)})
                continue

            tot_extra += m["tickets_extraidos"]
            tot_ins += m["inserted"]
            tot_dup += m["tickets_duplicados"]
            tot_lineas += m["lineas_extraidas"]
            tot_venta += m.get("venta_detalle_total", 0.0)
            line = {
                "unidad": u, "mes": mi,
                "extraidos": m["tickets_extraidos"], "insertados": m["inserted"],
                "duplicados": m["tickets_duplicados"], "lineas": m["lineas_extraidas"],
                "venta": round(m.get("venta_detalle_total", 0.0), 2),
                "error": m.get("error"), "seg": round(time.time() - t1, 1),
            }
            resumen.append(line)
            print(f"[BATCH] {u} {mi}: extraidos={line['extraidos']} insertados={line['insertados']} "
                  f"dup={line['duplicados']} lineas={line['lineas']} ${line['venta']} ({line['seg']}s)"
                  + (f" ERROR={line['error']}" if line['error'] else ""), flush=True)
            registrar_syncpos_bitacora("BACKFILL", "ERROR" if m.get("error") else ("DRY_RUN" if args.dry_run else "OK"),
                                       f"{u} {mi} ins={m['inserted']} dup={m['tickets_duplicados']}",
                                       unidad=u, fecha_inicio=mi, fecha_fin=mf,
                                       tickets=m["inserted"], lineas=m["lineas_extraidas"],
                                       venta=round(m.get("venta_detalle_total", 0.0), 2))

    total = {
        "tandas_meses": len(meses), "unidades": list(cfg_cache.keys()),
        "tickets_extraidos": tot_extra, "tickets_insertados": tot_ins,
        "tickets_duplicados": tot_dup, "lineas_extraidas": tot_lineas,
        "venta_detalle_total": round(tot_venta, 2),
        "tiempo_total_s": round(time.time() - t0, 1),
        "dry_run": args.dry_run,
    }
    registrar_syncpos_bitacora("BACKFILL", "TANDA_FIN",
                               json.dumps(total, ensure_ascii=False),
                               fecha_inicio=args.fecha_inicio, fecha_fin=args.fecha_fin,
                               tickets=tot_ins, lineas=tot_lineas, venta=round(tot_venta, 2))
    print("[BATCH] === TOTAL ===", flush=True)
    print(json.dumps(total, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
