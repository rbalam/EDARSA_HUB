#!/usr/bin/env bash
set -euo pipefail

: "${EDARSAHUB_TEST_AUTH_EMAIL:?Variable requerida}"
: "${EDARSAHUB_TEST_AUTH_PASSWORD:?Variable requerida}"
export EDARSAHUB_TEST_AUTH_EMAIL EDARSAHUB_TEST_AUTH_PASSWORD

LOGIN_PAYLOAD="$(python3 -c 'import json,os; print(json.dumps({
    "email": os.environ["EDARSAHUB_TEST_AUTH_EMAIL"],
    "password": os.environ["EDARSAHUB_TEST_AUTH_PASSWORD"],
}))')"
OUT_DIR="/app/auditorias_p5"; TS="$(date +%Y%m%d_%H%M%S)"
RAW="$OUT_DIR/FASE20_OPERATIVO_SNAPSHOT_MODULOS_CRITICOS_${TS}.txt"
JSON_DIR="$OUT_DIR/FASE20_OPERATIVO_${TS}"
mkdir -p "$OUT_DIR" "$JSON_DIR"; cd /app || exit 1
API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
echo "FASE 20 - SNAPSHOT OPERATIVO MODULOS CRITICOS $(date)" | tee "$RAW"
echo "===== 1) LOGIN =====" | tee -a "$RAW"
curl -sS --max-time 15 -X POST "$API/api/auth/login" -H "Content-Type: application/json" \
  -d "$LOGIN_PAYLOAD" -o "$JSON_DIR/login.json" \
  -w "LOGIN HTTP=%{http_code} t=%{time_total}s\n" | tee -a "$RAW"
TOKEN=$(python3 -c "import json;d=json.load(open('$JSON_DIR/login.json'));print(d.get('token') or d.get('access_token') or '')")
[ -z "$TOKEN" ] && { echo "ERROR: no token" | tee -a "$RAW"; exit 2; }
echo "===== 2) SNAPSHOT HTTP MODULOS CRITICOS =====" | tee -a "$RAW"
ENDPOINTS=(
  "/api/health/v1"
  "/api/admin/core-connections"
  "/api/api-connections"
  "/api/centro-control/destinatarios"
  "/api/centro-control/destinatarios/resumen"
  "/api/finanzas/health"
  "/api/admin/unidades-negocio/todas/configuracion-operativa"
  "/api/comercial/tablero-ejecutivo"
  "/api/dashboard-ejecutivo/resumen"
)
for path in "${ENDPOINTS[@]}"; do
  safe_name=$(echo "$path" | sed 's#[/:?&=]#_#g')
  curl -sS --max-time 25 "$API${path}" -H "Authorization: Bearer $TOKEN" \
    -o "$JSON_DIR/${safe_name}.json" -w "${path} HTTP=%{http_code} t=%{time_total}s\n" | tee -a "$RAW" || true
done
echo "===== 3) SEMAFORO OPERATIVO =====" | tee -a "$RAW"
JSON_DIR="$JSON_DIR" python3 - <<'PY' | tee -a "$RAW"
import json, os
from pathlib import Path
base = Path(os.environ["JSON_DIR"])
for f in sorted(base.glob("*.json")):
    if f.name == "login.json": continue
    try:
        d = json.loads(f.read_text())
        estado = "OK"
        if isinstance(d, dict):
            if d.get("overall_status") in ("error","critical","unhealthy"): estado=f"REVISAR:{d.get('overall_status')}"
            elif d.get("status") in ("ERROR","FAILED","error"): estado=f"REVISAR:{d.get('status')}"
            extra = d.get("overall_status") or d.get("status") or ("total="+str(d.get("total")) if "total" in d else "")
        elif isinstance(d, list): extra=f"list_len={len(d)}"
        else: extra=""
        print(f"  {f.name:70} {estado:14} {extra}")
    except Exception as e:
        print(f"  {f.name:70} NO_PARSEABLE {str(e)[:60]}")
PY
echo "RAW_REPORT=$RAW"; echo "OK - FASE 20 lista" | tee -a "$RAW"
