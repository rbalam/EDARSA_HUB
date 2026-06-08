#!/usr/bin/env python3
"""
Auditoría SEGURA del Sync POS canónico (P1B).

- Lee config de control (dbo.Sistema_SyncPOS_Config).
- Resuelve unidades desde SQL canónico (Unidades_Negocio + Servidores_Conexiones).
- NO conecta al POS. NO imprime password ni password_encrypted (solo has_password bool).
- Indica si el job correría ahora (should_run_syncpos_now).

Uso:
    python3 /app/backend/scripts/auditar_sync_pos_canonico.py
"""
import os
import sys
import json
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

from core.scheduler.jobs.inteligencia_comercial_sync_job import (
    get_syncpos_config,
    audit_syncpos_canonical_configs,
    detectar_faltantes_syncpos,
    should_run_syncpos_now,
)


def main():
    cfg = get_syncpos_config()
    can_run, reason = should_run_syncpos_now(cfg)

    payload = {
        "config": {
            "Habilitado": bool(cfg.get("Habilitado")),
            "PermitirPOSAutomatico": bool(cfg.get("PermitirPOSAutomatico")),
            "BackfillAutomaticoHabilitado": bool(cfg.get("BackfillAutomaticoHabilitado")),
            "FrecuenciaMinutos": cfg.get("FrecuenciaMinutos"),
            "DiasAtrasAutomatico": cfg.get("DiasAtrasAutomatico"),
            "DiasRevisionFaltantes": cfg.get("DiasRevisionFaltantes"),
            "MaxDiasBackfillPorCorrida": cfg.get("MaxDiasBackfillPorCorrida"),
            "FechaUltimaEjecucion": cfg.get("FechaUltimaEjecucion"),
            "FechaSiguienteEjecucion": cfg.get("FechaSiguienteEjecucion"),
        },
        "can_run_now": can_run,
        "reason": reason,
        "configs": audit_syncpos_canonical_configs(),
        "faltantes": detectar_faltantes_syncpos(),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
