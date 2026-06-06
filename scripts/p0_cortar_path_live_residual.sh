#!/usr/bin/env bash
set -uo pipefail

# P0: cortar path live residual de PEDIDOS/INVENTARIOS (POS externo en vivo)
# - usa mecanismos nativos via .env (solo flags que EXISTEN en config.py)
# - NO toca frontend ni EDARSAHUB SQL canónico
# - reversible por backup del .env

BACKEND_DIR="/app/backend"
ENV_FILE="$BACKEND_DIR/.env"
CONFIG_FILE="$BACKEND_DIR/core/scheduler/config.py"
TS="$(date +%Y%m%d_%H%M%S)"

cd "$BACKEND_DIR" || exit 1
[ -f "$ENV_FILE" ] || { echo "ERROR: no existe $ENV_FILE"; exit 1; }
[ -f "$CONFIG_FILE" ] || { echo "ERROR: no existe $CONFIG_FILE"; exit 1; }

cp "$ENV_FILE" "${ENV_FILE}.bak_${TS}"
echo "BACKUP: ${ENV_FILE}.bak_${TS}"

python3 - <<'PY'
from pathlib import Path
import re

env_path = Path("/app/backend/.env")
config_path = Path("/app/backend/core/scheduler/config.py")
config = config_path.read_text(encoding="utf-8")
env_lines = env_path.read_text(encoding="utf-8").splitlines()

# flags reales declaradas en config.py
flags_found = set(re.findall(r'os\.environ\.get\("([^"]+_ENABLED)"', config))

targets_preferred = [
    "SCHEDULER_PEDIDOS_ENABLED",
    "SCHEDULER_INVENTARIOS_ENABLED",
    "SCHEDULER_COMPRAS_ENABLED",
    "SCHEDULER_SYNC_COMPRAS_ENABLED",
    "SCHEDULER_DETECT_NUEVOS_COMPRAS_ENABLED",
]
targets = [x for x in targets_preferred if x in flags_found]

if not targets:
    print("ERROR: no se encontraron flags nativas para pedidos/inventarios/compras")
    print("FLAGS_FOUND=", sorted(flags_found))
    raise SystemExit(2)

existing = {}
for i, raw in enumerate(env_lines):
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k = line.split("=", 1)[0].strip()
    existing[k] = i

for key in targets:
    new_line = f"{key}=false"
    if key in existing:
        env_lines[existing[key]] = new_line
    else:
        env_lines.append(new_line)

env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
print("OK - flags desactivadas:")
for k in targets:
    print(f"  {k}=false")
PY

echo ""
echo "===== FLAGS APLICADAS EN .env ====="
grep -nE 'SCHEDULER_(PEDIDOS|INVENTARIOS|COMPRAS|SYNC_COMPRAS|DETECT_NUEVOS_COMPRAS)_ENABLED' "$ENV_FILE" || true

echo ""
echo "===== REINICIO BACKEND ====="
sudo supervisorctl restart backend || supervisorctl restart backend || true
sleep 8
sudo supervisorctl status backend || true

echo ""
echo "===== VALIDACION RAPIDA ====="
for i in $(seq 1 6); do
  CODE=$(curl -s -m 10 -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/api/health || echo 000)
  echo "health intento $i: $CODE"; [ "$CODE" = "200" ] && break; sleep 6
done

echo ""
echo "===== INTENTOS POS EXTERNOS NUEVOS EN 25s (debe ~0) ====="
B=$(grep -cE "pool \[web\]|QUERETARO|ORIGEN|ManagmentPro|Invalid object name 'Requisicion'" /var/log/supervisor/backend.err.log 2>/dev/null || echo 0)
sleep 25
A=$(grep -cE "pool \[web\]|QUERETARO|ORIGEN|ManagmentPro|Invalid object name 'Requisicion'" /var/log/supervisor/backend.err.log 2>/dev/null || echo 0)
echo "delta intentos POS externos: $((A-B))"

echo ""
echo "OK - path live residual cortado"
