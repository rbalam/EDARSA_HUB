#!/usr/bin/env bash
# =============================================================================
# P0 — Desactivar SYNC-S / SYNC-N por obsolescencia (idempotente, reversible)
# Escriben a Mongo `kpis_comercial` (deprecado) que los tableros ya no consumen.
# Mecanismo nativo: flags SCHEDULER_SYNC_S_ENABLED / SCHEDULER_SYNC_N_ENABLED.
# =============================================================================
set -uo pipefail
ENV_FILE="/app/backend/.env"
TS="$(date +%Y%m%d_%H%M%S)"
[ -f "$ENV_FILE" ] || { echo "ERROR: no existe $ENV_FILE"; exit 1; }
cp "$ENV_FILE" "${ENV_FILE}.bak_${TS}"; echo "BACKUP: ${ENV_FILE}.bak_${TS}"

python3 - <<'PY'
from pathlib import Path
p = Path("/app/backend/.env")
lines = p.read_text(encoding="utf-8").splitlines()
flags = {"SCHEDULER_SYNC_S_ENABLED": "false", "SCHEDULER_SYNC_N_ENABLED": "false"}
idx = {}
for i, raw in enumerate(lines):
    s = raw.strip()
    if s and not s.startswith("#") and "=" in s:
        idx[s.split("=",1)[0].strip()] = i
for k, v in flags.items():
    nl = f"{k}={v}"
    if k in idx: lines[idx[k]] = nl
    else: lines.append(nl)
p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("OK - SYNC-S / SYNC-N = false")
PY

echo "=== flags ==="
grep -nE "SCHEDULER_SYNC_(S|N)_ENABLED" "$ENV_FILE"
echo "=== reinicio backend ==="
sudo supervisorctl restart backend || supervisorctl restart backend || true
echo "OK - desactivación SYNC-S/N aplicada"
