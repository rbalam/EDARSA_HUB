#!/usr/bin/env bash
set -euo pipefail

: "${EDARSAHUB_TEST_AUTH_EMAIL:?Variable requerida}"
: "${EDARSAHUB_TEST_AUTH_PASSWORD:?Variable requerida}"
export EDARSAHUB_TEST_AUTH_EMAIL EDARSAHUB_TEST_AUTH_PASSWORD

LOGIN_PAYLOAD="$(python3 -c 'import json,os; print(json.dumps({
    "email": os.environ["EDARSAHUB_TEST_AUTH_EMAIL"],
    "password": os.environ["EDARSAHUB_TEST_AUTH_PASSWORD"],
}))')"

BASE_URL="${1:-http://127.0.0.1:8001}"

echo "===== LOGIN ====="
curl -sS --max-time 15 -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "$LOGIN_PAYLOAD" \
  -o /tmp/fase6_val_login.json \
  -w "HTTP=%{http_code} t=%{time_total}s\n"

TOKEN=$(python3 - <<'PY'
import json
try:
    with open('/tmp/fase6_val_login.json','r',encoding='utf-8') as f:
        d=json.load(f)
        print(d.get('token') or d.get('access_token') or "")
except Exception:
    print("")
PY
)

echo
echo "===== HEALTH V1 ====="
curl -sS --max-time 25 -i "$BASE_URL/api/health/v1" \
  -H "Authorization: Bearer $TOKEN" || true
echo

echo "===== FINANZAS QUICK ====="
curl -sS --max-time 25 -i "$BASE_URL/api/finanzas/health/quick" \
  -H "Authorization: Bearer $TOKEN" || true
echo

echo "===== ACCESS CONTEXT ====="
curl -sS --max-time 20 -i "$BASE_URL/api/auth/access-context" \
  -H "Authorization: Bearer $TOKEN" || true
