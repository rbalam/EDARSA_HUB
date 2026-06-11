#!/usr/bin/env python3
"""
PILOTO · Enriquecimiento por ticket (tipo de servicio + formas de pago).
ALCANCE PILOTO (autorizado): 1 unidad, 1 mes. SOLO LECTURA del POS.
Escribe: Sync_Sales.TipoServicio* (UPDATE) + Finanzas_CortesCaja_DetallePagos (re-escribe rango).
PROHIBIDO tocar KPIs / vw_*. Registra bitácora en Sistema_SyncPOS_Bitacora.

Uso:
  python3 scripts/pilot_enrich_tiposervicio_pagos.py --unidad ESTELAR --fecha-inicio 2026-05-01 --fecha-fin 2026-06-01
  (agrega --dry-run para extraer y medir SIN escribir)
"""
import os
import sys
import json
import argparse
from pathlib import Path

BACKEND_DIR = Path("/app/backend")
ENV_PATH = BACKEND_DIR / ".env"


def load_env():
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
sys.path.insert(0, str(BACKEND_DIR))

from core.scheduler.jobs.inteligencia_comercial_enrich import enrich_unidad
from core.scheduler.jobs.inteligencia_comercial_sync_job import registrar_syncpos_bitacora


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unidad", default="ESTELAR")
    ap.add_argument("--fecha-inicio", default="2026-05-01")
    ap.add_argument("--fecha-fin", default="2026-06-01", help="exclusivo")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    registrar_syncpos_bitacora(
        "ENRICH", "INICIO",
        f"Enriquecido {args.unidad} {args.fecha_inicio}..{args.fecha_fin} dry_run={args.dry_run}",
        unidad=args.unidad, fecha_inicio=args.fecha_inicio, fecha_fin=args.fecha_fin,
    )
    res = enrich_unidad(args.unidad, args.fecha_inicio, args.fecha_fin, dry_run=args.dry_run)
    estado = "ERROR" if res.get("error") else ("DRY_RUN" if args.dry_run else "OK")
    registrar_syncpos_bitacora(
        "ENRICH", estado,
        json.dumps({k: res.get(k) for k in ("pagos_extraidos", "pagos_insertados",
                                            "tickets_actualizados", "error")}, ensure_ascii=False),
        unidad=args.unidad, fecha_inicio=args.fecha_inicio, fecha_fin=args.fecha_fin,
        tickets=res.get("tickets_actualizados"), lineas=res.get("pagos_insertados"),
    )
    print(json.dumps(res, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
