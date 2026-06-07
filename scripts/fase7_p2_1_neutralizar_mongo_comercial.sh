#!/usr/bin/env bash
set -euo pipefail

# FASE 7 - P2-1 (CORREGIDO por el agente)
# Neutralizar residual Mongo deprecado en Comercial — SIN tocar producción de forma riesgosa.
#
# HALLAZGO de validación (vs script original):
#   - Los nombres save_kpis_batch / upsert_kpis / save_historical_kpis /
#     upsert_historical_kpis NO EXISTEN en el código.
#   - La ÚNICA función Mongo VIVA es upsert_kpi_comercial (la importa
#     api/sync_receiver.py:147). Esa hacía db=get_db()->None y luego
#     db[COLLECTION].find_one(...) => crash en cada sync.
#   - El script original NO tocaba esa función (apuntaba a nombres inexistentes)
#     y usaba regex de cuerpo de función frágil sobre firmas multilínea.
#
# FIX APLICADO (vía edición controlada, no regex):
#   modules/comercial/kpis_repository.py :: upsert_kpi_comercial
#   -> guard temprano: if db is None: return {"action":"SKIP","disabled":True,
#      "reason":"MONGO_COMMERCIAL_DEPRECATED"}
#   sync_receiver solo lee result["action"], por lo que SKIP es seguro.
#   Las get_*/cerrar_* NO se importan en ningún router (código muerto, inerte).

BACK_DIR="/app/backend"
KPI_REPO="$BACK_DIR/modules/comercial/kpis_repository.py"

echo "=== Validación de presencia del guard ==="
grep -q "MONGO_COMMERCIAL_DEPRECATED" "$KPI_REPO" && echo "OK guard presente" || { echo "FALTA guard"; exit 1; }

echo "=== Compile ==="
python3 -m py_compile "$KPI_REPO" && echo "COMPILE OK"

echo "=== Smoke: upsert_kpi_comercial no debe crashear con Mongo deprecado ==="
cd "$BACK_DIR"
python3 - <<'PY'
import asyncio
from dotenv import load_dotenv; load_dotenv('/app/backend/.env')
from modules.comercial.kpis_repository import upsert_kpi_comercial
r = asyncio.run(upsert_kpi_comercial(
    server_id="t", empresa_id="t", sucursal_id="t", fecha="2026-06-07",
    kpis={"ventas": 1}, source_info={"type": "TEST"}, updated_by="fase7_test"))
print("RESULT=", r)
assert r.get("action") == "SKIP" and r.get("disabled") is True, "guard no aplicó"
print("OK - no-op seguro")
PY
echo "OK - FASE 7 (neutralización correcta) verificada"
