#!/usr/bin/env bash
set -euo pipefail

# FASE 1 - P0-1
# Normalizar vistas corruptas de Tablero Ejecutivo / Comercial
#
# VISTAS CANONICAS CONFIRMADAS:
#   vw_Comercial_KPIs_Diarios_v2_Runtime
#   vw_Comercial_KPIs_Mensuales_v2_Runtime

APP_DIR="/app"
BACK_DIR="/app/backend"
FRONT_DIR="/app/frontend"
OUT_DIR="/app/auditorias_p5"
TS="$(date +%Y%m%d_%H%M%S)"
RAW="$OUT_DIR/FASE1_P0_1_VISTAS_CORRUPTAS_${TS}.txt"

mkdir -p "$OUT_DIR" /app/scripts
cd /app || exit 1

TARGET_DIARIA="vw_Comercial_KPIs_Diarios_v2_Runtime"
TARGET_MENSUAL="vw_Comercial_KPIs_Mensuales_v2_Runtime"

echo "==================================================" | tee "$RAW"
echo "FASE 1 - P0-1 FIX VISTAS CORRUPTAS" | tee -a "$RAW"
echo "Fecha: $(date)" | tee -a "$RAW"
echo "==================================================" | tee -a "$RAW"
echo | tee -a "$RAW"

echo "===== 1) AUDITORIA PREVIA =====" | tee -a "$RAW"
grep -RniE "vw_Comercial_KPIs_Diarios|vw_Comercial_KPIs_Mensuales|Runtime_Runtime|vw_vw|KPI.*Runtime" \
  "$BACK_DIR" "$FRONT_DIR" \
  --include="*.py" --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" --include="*.sql" \
  | tee -a "$RAW" || true
echo | tee -a "$RAW"

echo "===== 2) BACKUPS SOLO DE ARCHIVOS AFECTADOS =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
from pathlib import Path
import re, shutil, time

roots = [Path("/app/backend"), Path("/app/frontend")]
pat = re.compile(r"vw_Comercial_KPIs_Diarios|vw_Comercial_KPIs_Mensuales|Runtime_Runtime|vw_vw|KPI.*Runtime", re.I)
ts = time.strftime("%Y%m%d_%H%M%S")

for root in roots:
    for p in root.rglob("*"):
        if p.suffix.lower() not in {".py",".js",".jsx",".ts",".tsx",".sql",".md"}:
            continue
        # No reprocesar backups/dependencias para evitar churn masivo
        sp = str(p)
        if "/node_modules/" in sp or "/auditorias_p4/" in sp or ".bak_" in sp:
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if pat.search(txt):
            b = Path(str(p) + f".bak_{ts}")
            shutil.copy2(p, b)
            print(f"BACKUP: {b}")
PY
echo | tee -a "$RAW"

echo "===== 3) PARCHE QUIRURGICO =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
from pathlib import Path
import re

TARGET_DIARIA = "vw_Comercial_KPIs_Diarios_v2_Runtime"
TARGET_MENSUAL = "vw_Comercial_KPIs_Mensuales_v2_Runtime"

patterns_diaria = [
    r"\bvw_(?:vw_)+Comercial_KPIs_Diarios_v2(?:_Runtime)+(?:_Runtime)*\b",
    r"\bvw_Comercial_KPIs_Diarios_v2(?:_Runtime){2,}\b",
    r"\bvw_(?:vw_)+Comercial_KPIs_Diarios_Runtime(?:_Runtime)*\b",
    r"\bvw_Comercial_KPIs_Diarios_Runtime(?:_Runtime)*\b",
    r"\bvw_Comercial_KPIs_Diarios_v2\b(?!_Runtime)",
]

patterns_mensual = [
    r"\bvw_(?:vw_)+Comercial_KPIs_Mensuales_v2(?:_Runtime)+(?:_Runtime)*\b",
    r"\bvw_Comercial_KPIs_Mensuales_v2(?:_Runtime){2,}\b",
    r"\bvw_(?:vw_)+Comercial_KPIs_Mensuales_Runtime(?:_Runtime)*\b",
    r"\bvw_Comercial_KPIs_Mensuales_Runtime(?:_Runtime)*\b",
    r"\bvw_Comercial_KPIs_Mensuales_v2\b(?!_Runtime)",
]

changed = []
for root in [Path("/app/backend"), Path("/app/frontend")]:
    for p in root.rglob("*"):
        if p.suffix.lower() not in {".py",".js",".jsx",".ts",".tsx",".sql",".md"}:
            continue
        sp = str(p)
        if "/node_modules/" in sp or "/auditorias_p4/" in sp or ".bak_" in sp:
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        original = txt

        for pat in patterns_diaria:
            txt = re.sub(pat, TARGET_DIARIA, txt)
        for pat in patterns_mensual:
            txt = re.sub(pat, TARGET_MENSUAL, txt)

        if txt != original:
            p.write_text(txt, encoding="utf-8")
            changed.append(str(p))

print("PATCHED FILES:")
for f in changed:
    print(f" - {f}")
print(f"TOTAL_PATCHED={len(changed)}")
PY
echo | tee -a "$RAW"

echo "===== 4) EVIDENCIA POST-PARCHE =====" | tee -a "$RAW"
grep -RniE "Runtime_Runtime|vw_vw" \
  "$BACK_DIR" "$FRONT_DIR" \
  --include="*.py" --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" --include="*.sql" \
  | grep -vE "/auditorias_p4/|\.bak_" | tee -a "$RAW" || echo ">> SIN residuos corruptos (vw_vw / Runtime_Runtime)" | tee -a "$RAW"
echo | tee -a "$RAW"

echo "===== 5) VALIDACION SINTACTICA BACKEND =====" | tee -a "$RAW"
find "$BACK_DIR" -type f -name "*.py" -not -path "*/auditorias_p4/*" -not -name "*.bak_*" -print0 | while IFS= read -r -d '' f; do
  python3 -m py_compile "$f" 2>/dev/null || echo "WARN compile: $f"
done | tee -a "$RAW"
echo | tee -a "$RAW"

echo "===== 6) BUILD FRONTEND (gate de validacion) =====" | tee -a "$RAW"
cd "$FRONT_DIR" && yarn build >> "$RAW" 2>&1 && echo "BUILD_OK=1" | tee -a "$RAW" || echo "BUILD_OK=0" | tee -a "$RAW"
cd /app
echo | tee -a "$RAW"

echo "===== 7) REINICIO =====" | tee -a "$RAW"
sudo supervisorctl restart backend || supervisorctl restart backend || true
sleep 6
sudo supervisorctl status backend || supervisorctl status backend || true
echo | tee -a "$RAW"

echo "===== 8) HEALTH =====" | tee -a "$RAW"
curl -sS --max-time 10 -i http://127.0.0.1:8001/api/health | tee -a "$RAW" || true
echo | tee -a "$RAW"

echo "===== 9) LOGIN QA =====" | tee -a "$RAW"
curl -sS --max-time 15 -X POST "http://127.0.0.1:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"qa.superadmin@edarsa.com","password":"QaSuper2026!"}' \
  -o /tmp/fase1_p0_1_login.json \
  -w "HTTP=%{http_code} t=%{time_total}s\n" | tee -a "$RAW"
echo | tee -a "$RAW"

echo "===== 10) TOKEN =====" | tee -a "$RAW"
TOKEN=$(python3 - <<'PY'
import json
try:
    with open('/tmp/fase1_p0_1_login.json','r',encoding='utf-8') as f:
        d=json.load(f)
        print(d.get('token') or d.get('access_token') or "")
except Exception:
    print("")
PY
)
if [ -n "$TOKEN" ]; then
  echo "TOKEN_OK=1" | tee -a "$RAW"
else
  echo "TOKEN_OK=0" | tee -a "$RAW"
fi
echo | tee -a "$RAW"

echo "===== 11) SMOKE KPIs COMERCIALES / DASHBOARD =====" | tee -a "$RAW"
if [ -n "$TOKEN" ]; then
  for ep in \
    "/api/auth/me" \
    "/api/auth/access-context"
  do
    echo "--- $ep" | tee -a "$RAW"
    curl -sS --max-time 20 -o /tmp/smoke_resp.json -w "HTTP=%{http_code} t=%{time_total}s" "http://127.0.0.1:8001$ep" \
      -H "Authorization: Bearer $TOKEN" | tee -a "$RAW" || true
    echo | tee -a "$RAW"
  done
else
  echo "SIN TOKEN - smoke reducido" | tee -a "$RAW"
fi

echo "RAW_REPORT=$RAW" | tee -a "$RAW"
echo "OK - FASE 1 P0-1 ejecutado" | tee -a "$RAW"
