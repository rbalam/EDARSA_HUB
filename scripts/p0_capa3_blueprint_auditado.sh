#!/usr/bin/env bash
set -euo pipefail

# Capa 3: diagnóstico auditado + blueprint exacto
# SOLO diagnóstico. NO cambia código. NO mete stub. NO migra nada.

BACKEND_DIR="/app/backend"
REPORT_DIR="/app/auditorias_p5"
TS="$(date +%Y%m%d_%H%M%S)"
RAW_REPORT="$REPORT_DIR/P0_CAPA3_BLUEPRINT_RAW_${TS}.txt"

mkdir -p "$REPORT_DIR"
cd "$BACKEND_DIR" || exit 1

ENDPOINT_PATTERNS=(
  "/api/v2/dashboard/resumen"
  "/api/v2/dashboard/alertas"
  "/api/v2/tareas"
  "/api/v2/workflows"
  "/api/v2/sla/metricas"
  "/api/v2/responsabilidad/metricas"
  "/api/v2/responsabilidad/pendientes-aprobacion"
  "/api/v2/responsabilidad/en-disputa"
)

echo "==================================================" | tee "$RAW_REPORT"
echo "CAPA 3 - DIAGNOSTICO AUDITADO Y BLUEPRINT EXACTO" | tee -a "$RAW_REPORT"
echo "Fecha: $(date)" | tee -a "$RAW_REPORT"
echo "==================================================" | tee -a "$RAW_REPORT"

echo "===== 1) UBICACION DE ROUTERS /v2 =====" | tee -a "$RAW_REPORT"
grep -RniE 'prefix=.*v2|/v2/' "$BACKEND_DIR" --include="*.py" | grep -iE "router|prefix|include_router" | tee -a "$RAW_REPORT" || true

echo "===== 2) USO DE get_database()/stub EN fase2_operativo =====" | tee -a "$RAW_REPORT"
grep -RniE "get_database\(|db_utils|mongo_stub|self\.db\b|self\.collection" "$BACKEND_DIR/modules/fase2_operativo" --include="*.py" | tee -a "$RAW_REPORT" || true

echo "===== 3) COLECCIONES MONGO POR REPOSITORIO =====" | tee -a "$RAW_REPORT"
python3 - <<'PY' | tee -a "$RAW_REPORT"
from pathlib import Path
import re
root = Path("/app/backend/modules/fase2_operativo/repositories")
for p in sorted(root.rglob("*.py")):
    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        continue
    cols = set(re.findall(r'db\[[\'"]([^\'"]+)[\'"]\]', txt))
    cols |= set(re.findall(r'self\.db\.([A-Za-z_][A-Za-z0-9_]*)', txt))
    cols |= set(re.findall(r'collection_name\s*=\s*[\'"]([^\'"]+)[\'"]', txt))
    cols |= set(re.findall(r'COLLECTION\s*=\s*[\'"]([^\'"]+)[\'"]', txt))
    if cols:
        print(f"[{p.name}] -> {sorted(cols)}")
PY

echo "===== 4) ENDPOINTS OBJETIVO (ubicacion) =====" | tee -a "$RAW_REPORT"
for ep in "${ENDPOINT_PATTERNS[@]}"; do
  echo "--- $ep" | tee -a "$RAW_REPORT"
  grep -RniF "$ep" "$BACKEND_DIR/modules" --include="*.py" | tee -a "$RAW_REPORT" || true
done

echo "===== 5) REPOSITORIOS SQL YA EXISTENTES (referencia) =====" | tee -a "$RAW_REPORT"
grep -RilE "edarsahub|get_sql_connection|pymssql|SELECT |FROM " "$BACKEND_DIR/modules/fase2_operativo/repositories" --include="*.py" | tee -a "$RAW_REPORT" || true

echo | tee -a "$RAW_REPORT"
echo "RAW_REPORT=$RAW_REPORT"
echo "OK - diagnostico auditado Capa 3 generado"
