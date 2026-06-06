#!/usr/bin/env bash
# =============================================================================
# P0 — Validar desactivación SYNC-S/N obsoletos (con login propio para token)
# =============================================================================
set -uo pipefail
BASE_URL="${1:-http://127.0.0.1:8001}"
EMAIL="ricardo@edarsa.com.mx"; PASS="Ricardo2835!"

echo "===== ESPERAR BACKEND ====="
for i in $(seq 1 8); do
  CODE=$(curl -s -m 10 -o /dev/null -w "%{http_code}" "$BASE_URL/api/health" 2>/dev/null || echo 000)
  echo "health $i: $CODE"; [ "$CODE" = "200" ] && break; sleep 6
done

echo ""
echo "===== LOGIN (genera token) ====="
curl -s --max-time 20 -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASS}\"}" \
  -o /tmp/login_syncsn_1.json -w "login: HTTP=%{http_code} t=%{time_total}s\n"

TOKEN=$(python3 -c "import json;print(json.load(open('/tmp/login_syncsn_1.json')).get('token',''))" 2>/dev/null || echo "")
echo "token_len: ${#TOKEN}"

echo ""
echo "===== ACCESS CONTEXT ====="
if [ -n "$TOKEN" ]; then
  curl -s --max-time 15 -o /tmp/ctx_syncsn.json -w "access-context: HTTP=%{http_code}\n" \
    "$BASE_URL/api/auth/access-context" -H "Authorization: Bearer $TOKEN"
  python3 -c "import json;d=json.load(open('/tmp/ctx_syncsn.json'));print('  unidad_activa:',d.get('unidad_activa'),'| unidades:',len(d.get('unidades_permitidas',[])))" 2>/dev/null || true
else echo "SIN TOKEN"; fi

echo ""
echo "===== MENUS USUARIO ====="
if [ -n "$TOKEN" ]; then
  curl -s --max-time 15 -o /tmp/menu_syncsn.json -w "menus: HTTP=%{http_code}\n" \
    "$BASE_URL/api/sistema/menus/usuario" -H "Authorization: Bearer $TOKEN"
  python3 -c "import json;d=json.load(open('/tmp/menu_syncsn.json'));print('  total:',d.get('total'),'| superadmin:',d.get('es_super_admin'),'| source:',d.get('source'))" 2>/dev/null || true
else echo "SIN TOKEN"; fi

echo ""
echo "===== SYNC-S/N: ¿registrados? (debe 0) ====="
grep -cE "SYNC-S registrado|SYNC-N registrado" /var/log/supervisor/backend.*.log 2>/dev/null | tail -2

echo ""
echo "===== ERRORES LIVE NUEVOS EN 20s (debe 0) ====="
B=$(grep -cE "pool \[web\]|Requisicion|Adaptive Server is unavailable" /var/log/supervisor/backend.err.log 2>/dev/null || echo 0)
sleep 20
A=$(grep -cE "pool \[web\]|Requisicion|Adaptive Server is unavailable" /var/log/supervisor/backend.err.log 2>/dev/null || echo 0)
echo "delta: $((A-B))"
echo ""
echo "===== flags SYNC-S/N en .env ====="
grep -nE "SCHEDULER_SYNC_(S|N)_ENABLED" /app/backend/.env
