#!/usr/bin/env bash
# =============================================================================
# 91C — VALIDACION DE LA CONTENCION LIVE NATIVA
# Confirma: flags activas, fail-fast en pool, estabilidad de login y que ya no
# se saturan los pools externos caídos.
# =============================================================================
set -uo pipefail
ENV_FILE="/app/backend/.env"
POOL_FILE="/app/backend/core/pool.py"
API_LOCAL="http://127.0.0.1:8001"
EMAIL="ricardo@edarsa.com.mx"; PASS="Ricardo2835!"

echo "===== FLAGS LIVE (deben estar en false) ====="
grep -nE "SCHEDULER_(SYNC_COMERCIAL_V2|SYNC_COMERCIAL_ABIERTAS_V2|SYNC_INGRESOS|SYNC_PROPINAS|INTELIGENCIA_SYNC|CRM_SYNC|VTIGER_SYNC)_ENABLED" "$ENV_FILE" || echo "SIN FLAGS"

echo ""
echo "===== FAIL-FAST POOL ====="
grep -nE "connection_timeout: int|blocking_timeout: int" "$POOL_FILE"

echo ""
echo "===== ESPERAR BACKEND ====="
for i in $(seq 1 8); do
  CODE=$(curl -s --max-time 8 -o /dev/null -w "%{http_code}" "${API_LOCAL}/api/health" 2>/dev/null || echo 000)
  echo "health $i: $CODE"; [ "$CODE" = "200" ] && break; sleep 6
done

echo ""
echo "===== ERRORES EXTERNOS NUEVOS EN 20s (debe ser ~0) ====="
B=$(grep -cE "Adaptive Server is unavailable|Connection refused" /var/log/supervisor/backend.err.log 2>/dev/null || echo 0)
sleep 20
A=$(grep -cE "Adaptive Server is unavailable|Connection refused" /var/log/supervisor/backend.err.log 2>/dev/null || echo 0)
echo "delta errores externos: $((A-B))"

echo ""
echo "===== 6 LOGINS (estabilidad) ====="
OK=0
for i in $(seq 1 6); do
  curl -s --max-time 20 -X POST "${API_LOCAL}/api/auth/login" -H "Content-Type: application/json" \
       -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASS}\"}" -o /tmp/_v.json -w "login $i: HTTP=%{http_code} t=%{time_total}s\n"
  python3 -c "import json;exit(0 if 'token' in json.load(open('/tmp/_v.json')) else 1)" 2>/dev/null && OK=$((OK+1))
  sleep 2
done
echo "RESULTADO: ${OK}/6 logins OK"
[ "$OK" -ge 5 ] && echo "CONTENCION OK ✅" || echo "REVISAR ❌"
