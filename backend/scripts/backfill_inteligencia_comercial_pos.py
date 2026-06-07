#!/usr/bin/env python3
"""
Backfill de Inteligencia Comercial desde POS (SoftRestaurant/MPRO) hacia EDARSAHUB.

SEGURIDAD:
- Por defecto corre en DRY-RUN (no extrae ni carga datos).
- Para ejecución real se requiere --execute Y credenciales POS válidas.
- NO crea un sync nuevo: reutiliza el job existente corregido (opción D).

Uso:
  # Dry-run (no toca nada, solo valida rango/unidades):
  python3 backfill_inteligencia_comercial_pos.py --fecha-inicio 2026-06-01 --fecha-fin 2026-06-02

  # Ejecución real (solo cuando haya credenciales/conectividad POS):
  python3 backfill_inteligencia_comercial_pos.py --fecha-inicio 2026-06-01 --fecha-fin 2026-06-02 --execute
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

from core.scheduler.jobs.inteligencia_comercial_sync_job import job_inteligencia_comercial_sync


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fecha-inicio", required=True, help="YYYY-MM-DD")
    ap.add_argument("--fecha-fin", required=True, help="YYYY-MM-DD (exclusiva)")
    ap.add_argument("--unidades", default="", help="CSV opcional; vacío = todas las configuradas")
    ap.add_argument("--execute", action="store_true", help="Ejecuta de verdad; sin esto es dry-run")
    args = ap.parse_args()

    unidades = [x.strip() for x in args.unidades.split(",") if x.strip()] or None

    result = job_inteligencia_comercial_sync(
        fecha_inicio=args.fecha_inicio,
        fecha_fin=args.fecha_fin,
        unidades=unidades,
        dry_run=not args.execute,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
