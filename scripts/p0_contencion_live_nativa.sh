#!/usr/bin/env bash
# =============================================================================
# 91C — CONTENCION P0 NATIVA Y SEGURA (versión corregida)
# -----------------------------------------------------------------------------
# Corrige los 2 nombres de env var que NO existían en core/scheduler/config.py:
#   SCHEDULER_SYNC_INGRESOS_INCREMENTAL_ENABLED   -> SCHEDULER_SYNC_INGRESOS_ENABLED
#   SCHEDULER_INTELIGENCIA_COMERCIAL_SYNC_ENABLED -> SCHEDULER_INTELIGENCIA_SYNC_ENABLED
#
# Idempotente. Reversible (poner los flags en true / restaurar backups).
# NO toca la conexión canónica EDARSAHUB (solo core/pool.py = pool externo).
# =============================================================================
set -uo pipefail

BACKEND_DIR="/app/backend"
ENV_FILE="$BACKEND_DIR/.env"
POOL_FILE="$BACKEND_DIR/core/pool.py"
TS="$(date +%Y%m%d_%H%M%S)"
cd "$BACKEND_DIR" || exit 1

echo "=================================================="
echo "91C CONTENCION LIVE NATIVA (corregida) | $(date)"
echo "=================================================="

[ -f "$ENV_FILE" ] || { echo "ERROR: no existe $ENV_FILE"; exit 1; }
[ -f "$POOL_FILE" ] || { echo "ERROR: no existe $POOL_FILE"; exit 1; }
cp "$ENV_FILE" "${ENV_FILE}.bak_${TS}"
cp "$POOL_FILE" "${POOL_FILE}.bak_${TS}"
echo "BACKUP ENV:  ${ENV_FILE}.bak_${TS}"
echo "BACKUP POOL: ${POOL_FILE}.bak_${TS}"

# 1) DESACTIVAR JOBS LIVE (nombres REALES de config.py) -------------------------
python3 - <<'PY'
from pathlib import Path
env_path = Path("/app/backend/.env")
txt = env_path.read_text(encoding="utf-8")

flags = {
    "SCHEDULER_SYNC_COMERCIAL_V2_ENABLED": "false",
    "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED": "false",
    "SCHEDULER_SYNC_INGRESOS_ENABLED": "false",          # REAL
    "SCHEDULER_SYNC_PROPINAS_ENABLED": "false",
    "SCHEDULER_INTELIGENCIA_SYNC_ENABLED": "false",      # REAL
    "SCHEDULER_CRM_SYNC_ENABLED": "false",
    "SCHEDULER_VTIGER_SYNC_ENABLED": "false",
}

lines = txt.splitlines()
idx = {}
for i, line in enumerate(lines):
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        continue
    k = s.split("=", 1)[0].strip()
    idx[k] = i

for key, value in flags.items():
    new_line = f"{key}={value}"
    if key in idx:
        lines[idx[key]] = new_line
    else:
        lines.append(new_line)

env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("OK - env flags live desactivadas (nombres reales)")
for k, v in flags.items():
    print(f"  {k}={v}")
PY

# 2) FAIL-FAST SOLO EN POOL EXTERNO -------------------------------------------
python3 - <<'PY'
from pathlib import Path
import re
p = Path("/app/backend/core/pool.py")
txt = p.read_text(encoding="utf-8")
original = txt
txt = re.sub(r'connection_timeout:\s*int\s*=\s*\d+', 'connection_timeout: int = 5', txt)
txt = re.sub(r'blocking_timeout:\s*int\s*=\s*\d+', 'blocking_timeout: int = 10', txt)
# query_timeout se conserva en 120 para no cortar queries legítimas a POS sanos.
if txt != original:
    p.write_text(txt, encoding="utf-8")
    print("OK - pool externo en fail-fast (connection=5, blocking=10)")
else:
    print("NO CHANGE - pool.py (ya en fail-fast)")
PY

# 3) VALIDACION ---------------------------------------------------------------
echo ""
echo "===== VALIDACION PYTHON ====="
python3 -m py_compile "$POOL_FILE"
python3 -m py_compile "$BACKEND_DIR/core/scheduler/config.py"

# 4) REINICIO -----------------------------------------------------------------
echo ""
echo "===== REINICIO BACKEND ====="
sudo supervisorctl restart backend || supervisorctl restart backend || true
sleep 8

# 5) EVIDENCIA ----------------------------------------------------------------
echo ""
echo "===== FLAGS EN .env ====="
grep -nE "SCHEDULER_(SYNC_COMERCIAL_V2|SYNC_COMERCIAL_ABIERTAS_V2|SYNC_INGRESOS|SYNC_PROPINAS|INTELIGENCIA_SYNC|CRM_SYNC|VTIGER_SYNC)_ENABLED" "$ENV_FILE"
echo ""
echo "===== FAIL-FAST pool.py ====="
grep -nE "connection_timeout: int|query_timeout: int|blocking_timeout: int" "$POOL_FILE"
echo ""
echo "OK - contención nativa aplicada"
