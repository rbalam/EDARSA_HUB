#!/usr/bin/env python3
"""
CLI · Sincroniza Cuentas por Pagar a la tabla canónica dbo.Finanzas_CxP_Sync.
Uso:
  python3 scripts/sync_cxp_canonico.py            # carga real
  python3 scripts/sync_cxp_canonico.py --dry-run  # solo extrae y mide
"""
import os
import sys
import json
import argparse
from pathlib import Path

BACKEND_DIR = Path("/app/backend")
for raw in (BACKEND_DIR / ".env").read_text(encoding="utf-8", errors="ignore").splitlines():
    line = raw.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
sys.path.insert(0, str(BACKEND_DIR))

from core.scheduler.jobs.cxp_sync_job import run_cxp_sync


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    res = run_cxp_sync(dry_run=args.dry_run)
    print(json.dumps(res, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
