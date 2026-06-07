#!/usr/bin/env bash
set -euo pipefail
OUT_DIR="/app/auditorias_p5"; TS="$(date +%Y%m%d_%H%M%S)"
RAW="$OUT_DIR/FASE_OPERATIVO_GATE_9_MODULOS_${TS}.txt"
JSON_DIR="$OUT_DIR/FASE_OPERATIVO_GATE_9_MODULOS_${TS}"
mkdir -p "$OUT_DIR" "$JSON_DIR"; cd /app || exit 1
API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
echo "FASE OPERATIVO - GATE 9 MODULOS CRITICOS $(date)" | tee "$RAW"
curl -sS --max-time 15 -X POST "$API/api/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"admin@edarsa.com","password":"pruebas123"}' -o "$JSON_DIR/login.json" \
  -w "LOGIN HTTP=%{http_code}\n" | tee -a "$RAW"
TOKEN=$(python3 -c "import json;d=json.load(open('$JSON_DIR/login.json'));print(d.get('token') or d.get('access_token') or '')")
[ -z "$TOKEN" ] && { echo "ERROR: no token" | tee -a "$RAW"; exit 2; }
ENDPOINTS=(
  "/api/health/v1" "/api/admin/core-connections" "/api/api-connections"
  "/api/centro-control/destinatarios" "/api/centro-control/destinatarios/resumen"
  "/api/finanzas/health" "/api/admin/unidades-negocio/todas/configuracion-operativa"
  "/api/comercial/tablero-ejecutivo" "/api/dashboard-ejecutivo/resumen"
)
for path in "${ENDPOINTS[@]}"; do
  safe_name=$(echo "$path" | sed 's#[/:?&=]#_#g')
  code=$(curl -sS --max-time 25 -H "Authorization: Bearer $TOKEN" -o "$JSON_DIR/${safe_name}.json" -w "%{http_code}" "$API${path}" || true)
  echo "${path} HTTP=${code}" | tee -a "$RAW"
done
echo "===== VALIDACION =====" | tee -a "$RAW"
JSON_DIR="$JSON_DIR" python3 - <<'PY' | tee -a "$RAW"
import json, os, sys
from pathlib import Path
base=Path(os.environ["JSON_DIR"])
targets={
 "_api_health_v1.json":("Health V1","overall_status","healthy"),
 "_api_admin_core-connections.json":("Admin CORE","status","SUCCESS"),
 "_api_api-connections.json":("API Connections",None,None),
 "_api_centro-control_destinatarios.json":("Destinatarios",None,None),
 "_api_centro-control_destinatarios_resumen.json":("Resumen Destinatarios",None,None),
 "_api_finanzas_health.json":("Finanzas","overall_status","healthy"),
 "_api_admin_unidades-negocio_todas_configuracion-operativa.json":("Config Operativa",None,None),
 "_api_comercial_tablero-ejecutivo.json":("Tablero Comercial",None,None),
 "_api_dashboard-ejecutivo_resumen.json":("Dashboard Ejecutivo",None,None),
}
errors=[]
for suffix,(label,key,expected) in targets.items():
    m=list(base.glob(f"*{suffix}"))
    if not m: errors.append(f"{label}: SIN_ARCHIVO"); continue
    try: d=json.loads(m[0].read_text())
    except Exception as e: errors.append(f"{label}: JSON_INVALIDO"); continue
    if key is not None and isinstance(d,dict):
        if d.get(key)!=expected: errors.append(f"{label}: {key}={d.get(key)!r} esperado={expected!r}")
    if label in ("Tablero Comercial","Dashboard Ejecutivo") and isinstance(d,dict) and "error" in d:
        errors.append(f"{label}: trae error")
    print(f"  {label:24} -> {'OK' if not any(label in e for e in errors) else 'REVISAR'}")
if errors:
    print("\nRESULTADO=FAIL");[print('ERROR=',e) for e in errors]; sys.exit(3)
print("\nRESULTADO=PASS")
PY
echo "RAW_REPORT=$RAW"; echo "OK - GATE listo" | tee -a "$RAW"
