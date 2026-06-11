#!/usr/bin/env python3
"""
ESCALADO (autorizado) · Enriquecimiento por TICKET para las 5 unidades × 24 meses.
Itera unidad × mes llamando enrich_unidad (idempotente por rango mensual).
Escribe LOG por unidad/mes en stdout + bitácora Sistema_SyncPOS_Bitacora.
SOLO LECTURA del POS. NO toca KPIs canónicos.

Uso:
  python3 scripts/escalar_enrich_5u_24m.py [--desde 2024-06] [--hasta 2026-06] [--unidades ESTELAR,ORIGEN] [--dry-run]
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

BACKEND_DIR = Path("/app/backend")
for raw in (BACKEND_DIR / ".env").read_text(encoding="utf-8", errors="ignore").splitlines():
    line = raw.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
sys.path.insert(0, str(BACKEND_DIR))

from core.scheduler.jobs.inteligencia_comercial_enrich import enrich_unidad
from core.scheduler.jobs.inteligencia_comercial_sync_job import (
    get_unidades_negocio_pos, registrar_syncpos_bitacora,
)

UNIDADES_DEFAULT = ["130MID", "CIENFUEGOS", "ESTELAR", "130QRO", "ORIGEN"]


def month_iter(d0, d1):
    y, m = d0
    while (y, m) <= d1:
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        yield f"{y:04d}-{m:02d}-01", f"{ny:04d}-{nm:02d}-01"
        y, m = ny, nm


def _ym(s):
    y, m = s.split("-")
    return (int(y), int(m))


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2024-06")
    ap.add_argument("--hasta", default="2026-06")
    ap.add_argument("--unidades", default=",".join(UNIDADES_DEFAULT))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    unidades = [u.strip() for u in args.unidades.split(",") if u.strip()]
    d0, d1 = _ym(args.desde), _ym(args.hasta)
    meses = list(month_iter(d0, d1))

    log(f"=== ESCALADO ENRICH · {len(unidades)} unidades × {len(meses)} meses · dry_run={args.dry_run} ===")
    registrar_syncpos_bitacora("ENRICH_ESCALADO", "INICIO",
                               f"{len(unidades)} unidades × {len(meses)} meses ({args.desde}..{args.hasta}) dry_run={args.dry_run}")

    totales = {"pagos": 0, "tickets_ts": 0, "errores": 0, "ok": 0}
    t_global = time.time()
    for u in unidades:
        t_u = time.time(); pu = 0; tu = 0; eu = 0
        for fi, ff in meses:
            try:
                r = enrich_unidad(u, fi, ff, dry_run=args.dry_run)
                if r.get("error"):
                    eu += 1; totales["errores"] += 1
                    log(f"  [{u}] {fi[:7]} ERROR: {r.get('error')}")
                else:
                    pag = r.get("pagos_extraidos" if args.dry_run else "pagos_insertados", 0) or 0
                    ts = r.get("tickets_con_tiposervicio" if args.dry_run else "tickets_actualizados", 0) or 0
                    pu += pag; tu += ts; totales["pagos"] += pag; totales["tickets_ts"] += ts; totales["ok"] += 1
                    log(f"  [{u}] {fi[:7]} OK pagos={pag} ts={ts} ({r.get('tiempo_total_s', r.get('tiempo_extraccion_s'))}s)")
            except Exception as e:
                eu += 1; totales["errores"] += 1
                log(f"  [{u}] {fi[:7]} EXC: {type(e).__name__}: {e}")
        log(f"== {u} LISTO: pagos={pu} tickets_ts={tu} errores={eu} ({round(time.time()-t_u,1)}s) ==")
        registrar_syncpos_bitacora("ENRICH_ESCALADO", "UNIDAD_OK" if eu == 0 else "UNIDAD_PARCIAL",
                                   f"{u}: pagos={pu} ts={tu} err={eu}", unidad=u,
                                   tickets=tu, lineas=pu)

    log(f"=== FIN · ok={totales['ok']} pagos={totales['pagos']} tickets_ts={totales['tickets_ts']} "
        f"errores={totales['errores']} · {round(time.time()-t_global,1)}s ===")
    registrar_syncpos_bitacora("ENRICH_ESCALADO", "FIN" if totales["errores"] == 0 else "FIN_CON_ERRORES",
                               json.dumps(totales, ensure_ascii=False))
    print(json.dumps(totales, ensure_ascii=False))


if __name__ == "__main__":
    main()
