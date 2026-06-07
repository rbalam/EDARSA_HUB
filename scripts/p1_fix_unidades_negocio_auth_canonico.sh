#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8001}"

echo "===== LOGIN ====="
curl -sS --max-time 15 -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"ricardo@edarsa.com.mx","password":"Ricardo2835!"}' \
  -o /tmp/unidades_login.json \
  -w "HTTP=%{http_code} t=%{time_total}s\n"

TOKEN=$(python3 - <<'PY'
import json
try:
    with open('/tmp/unidades_login.json','r',encoding='utf-8') as f:
        d=json.load(f)
        print(d.get('token') or d.get('access_token') or "")
except Exception:
    print("")
PY
)

echo
echo "===== ACCESS-CONTEXT ====="
curl -sS --max-time 15 -i "$BASE_URL/api/auth/access-context" \
  -H "Authorization: Bearer $TOKEN" || true
