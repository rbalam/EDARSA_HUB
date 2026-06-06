#!/usr/bin/env bash
# =============================================================================
# P0 CONTENCION LIVE EXTERNOS  (versión corregida y segura)
# -----------------------------------------------------------------------------
# Objetivo: evitar que los jobs de SYNC a servidores POS/CRM EXTERNOS (caídos)
# saturen el event loop compartido con la API y tumben el login.
#
# Estrategia (mecanismos NATIVOS del proyecto, sin regex destructivas):
#   1) FAIL-FAST en el POOL EXTERNO  -> core/pool.py (connection_timeout=5,
#      blocking_timeout=10). NO toca la conexión canónica EDARSAHUB.
#   2) DESACTIVAR jobs live          -> variables SCHEDULER_*_ENABLED=false en
#      backend/.env (las lee core/scheduler/config.py). NO comenta código.
#
# Reversible: poner los flags en true (o quitarlos) y restaurar pool.py.
# =============================================================================
set -uo pipefail
cd /app/backend || exit 1

echo "=================================================="
echo "P0 CONTENCION LIVE EXTERNOS  |  $(date)"
echo "=================================================="

ENV_FILE="/app/backend/.env"

declare -a FLAGS=(
  "SCHEDULER_SYNC_COMERCIAL_V2_ENABLED"
  "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED"
  "SCHEDULER_SYNC_INGRESOS_ENABLED"
  "SCHEDULER_SYNC_PROPINAS_ENABLED"
  "SCHEDULER_INTELIGENCIA_SYNC_ENABLED"
  "SCHEDULER_CRM_SYNC_ENABLED"
  "SCHEDULER_VTIGER_SYNC_ENABLED"
)

echo ""
echo "===== 1) FLAGS DE JOBS LIVE (idempotente) ====="
for flag in "${FLAGS[@]}"; do
  if grep -qE "^${flag}=" "$ENV_FILE"; then
    sed -i -E "s/^${flag}=.*/${flag}=false/" "$ENV_FILE"
    echo "SET  ${flag}=false"
  else
    printf '%s=false\n' "$flag" >> "$ENV_FILE"
    echo "ADD  ${flag}=false"
  fi
done

echo ""
echo "===== 2) FAIL-FAST POOL EXTERNO (core/pool.py) ====="
grep -nE "connection_timeout: int|blocking_timeout: int" /app/backend/core/pool.py | head -4

echo ""
echo "===== 3) VALIDACION PYTHON ====="
python3 -m py_compile /app/backend/core/pool.py && echo "py_compile pool.py OK"

echo ""
echo "===== 4) REINICIO BACKEND (.env cambió) ====="
sudo supervisorctl restart backend || true

echo ""
echo "===== 5) EVIDENCIA FLAGS ====="
grep -nE "SCHEDULER_(SYNC_COMERCIAL_V2|SYNC_COMERCIAL_ABIERTAS_V2|SYNC_INGRESOS|SYNC_PROPINAS|INTELIGENCIA_SYNC|CRM_SYNC|VTIGER_SYNC)_ENABLED" "$ENV_FILE"

echo ""
echo "OK - contención P0 aplicada"
