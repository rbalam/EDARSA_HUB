#!/usr/bin/env python3
"""
Catch-up puntual: ejecuta el pipeline OFICIAL sync_comercial_v2 (ventas cerradas)
para los ultimos N dias y rellena Comercial_KPIs_Diarios_v2 (via vw_..._Runtime).

- SOLO LECTURA del POS (SELECT).
- Upsert idempotente (hash_origen). No borra ni trunca.
- Mismo pipeline que ya lleno del 1 al 4 de junio (fuente SQL_LIVE).
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path("/app/backend")))

from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

from core.scheduler.jobs.sync_comercial_v2_job import run_sync_comercial_v2_manual

if __name__ == "__main__":
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    print(f"[CATCHUP] Iniciando catch-up KPIs v2 ventas cerradas, dias_atras={dias}")
    res = run_sync_comercial_v2_manual(dias_atras=dias)
    print("[CATCHUP] RESULTADO:")
    print(json.dumps({
        "estatus_general": res.get("estatus_general"),
        "fecha_inicio": res.get("fecha_inicio"),
        "fecha_fin": res.get("fecha_fin"),
        "unidades_exitosas": res.get("unidades_exitosas"),
        "unidades_fallidas": res.get("unidades_fallidas"),
        "total_insertados": res.get("total_insertados"),
        "total_actualizados": res.get("total_actualizados"),
        "total_omitidos": res.get("total_omitidos"),
        "errores": res.get("errores"),
    }, indent=2, ensure_ascii=False))
