#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8001}"

echo "===== LOGIN ====="
curl -sS --max-time 15 -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"ricardo@edarsa.com.mx","password":"Ricardo2835!"}' \
  -o /tmp/opv2_login.json \
  -w "HTTP=%{http_code} t=%{time_total}s\n"

TOKEN=$(python3 - <<'PY'
import json
try:
    with open('/tmp/opv2_login.json','r',encoding='utf-8') as f:
        d=json.load(f)
        print(d.get('token') or d.get('access_token') or "")
except Exception:
    print("")
PY
)

echo
echo "TOKEN_LEN=${#TOKEN}"
echo
echo "===== OPERACIONES V2 (con Bearer) ====="
for ep in \
  "/api/v2/sla/metricas" \
  "/api/v2/responsabilidad/metricas" \
  "/api/v2/responsabilidad/pendientes-aprobacion" \
  "/api/v2/responsabilidad/en-disputa" \
  "/api/v2/dashboard/resumen" \
  "/api/v2/dashboard/alertas" \
  "/api/v2/tareas?limit=50" \
  "/api/v2/workflows?limit=50"
do
  echo "--- $ep"
  curl -sS --max-time 15 -o /dev/null -w "HTTP=%{http_code} t=%{time_total}s\n" "$BASE_URL$ep" \
    -H "Authorization: Bearer $TOKEN" || true
done

echo
echo "===== FORGOT PASSWORD ====="
curl -sS --max-time 20 -o /dev/null -w "HTTP=%{http_code} t=%{time_total}s\n" -X POST "$BASE_URL/api/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email":"ricardo@edarsa.com.mx"}' || true
