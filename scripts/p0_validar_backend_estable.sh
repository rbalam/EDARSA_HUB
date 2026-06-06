#!/usr/bin/env bash
# =============================================================================
# P0 VALIDAR BACKEND ESTABLE
# Verifica que /api/health y /api/auth/login respondan de forma estable y
# rápida (sin bloqueos por jobs live), repitiendo varias veces.
# =============================================================================
set -uo pipefail

API_LOCAL="http://127.0.0.1:8001"
EMAIL="ricardo@edarsa.com.mx"
PASS="Ricardo2835!"

echo "===== ESPERANDO ARRANQUE BACKEND ====="
for i in $(seq 1 8); do
  CODE=$(curl -s --max-time 10 -o /dev/null -w "%{http_code}" "${API_LOCAL}/api/health" 2>/dev/null || echo 000)
  echo "health intento $i: $CODE"
  [ "$CODE" = "200" ] && break
  sleep 6
done

echo ""
echo "===== 6 LOGINS CONSECUTIVOS (estabilidad) ====="
OK=0
for i in $(seq 1 6); do
  RES=$(curl -s --max-time 20 -X POST "${API_LOCAL}/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASS}\"}" \
        -o /tmp/_lg.json -w "HTTP=%{http_code} t=%{time_total}s")
  HAS_TOKEN=$(python3 -c "import json;print('token' in json.load(open('/tmp/_lg.json')))" 2>/dev/null || echo False)
  echo "login $i: $RES token=$HAS_TOKEN"
  [ "$HAS_TOKEN" = "True" ] && OK=$((OK+1))
  sleep 2
done

echo ""
echo "RESULTADO: ${OK}/6 logins exitosos"
[ "$OK" -ge 5 ] && echo "BACKEND ESTABLE ✅" || echo "BACKEND INESTABLE ❌"
