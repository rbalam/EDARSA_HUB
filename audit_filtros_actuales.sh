#!/bin/bash
set -e

mkdir -p /app/docs/reports

REPORT="/app/docs/reports/DIAGNOSTICO_FILTROS_ACTUALES_EDARSAHUB.md"

echo "# Diagnóstico de filtros actuales EDARSAHUB" > "$REPORT"
echo "" >> "$REPORT"
echo "Fecha: $(date)" >> "$REPORT"
echo "" >> "$REPORT"

echo "## 1. Endpoints backend relacionados con filtros" >> "$REPORT"
echo '```text' >> "$REPORT"
grep -RIn --exclude-dir=venv --exclude-dir=__pycache__ --exclude-dir=node_modules --exclude-dir=.git \
  -E "@api_router\\.(get|post|put|delete).*empresas|@api_router\\.(get|post|put|delete).*sucursales|@api_router\\.(get|post|put|delete).*almacenes|@api_router\\.(get|post|put|delete).*servers|@api_router\\.(get|post|put|delete).*servidores|@api_router\\.(get|post|put|delete).*productos|@api_router\\.(get|post|put|delete).*vendedores|@api_router\\.(get|post|put|delete).*proveedores" \
  /app/backend 2>/dev/null >> "$REPORT" || true
echo '```' >> "$REPORT"
echo "" >> "$REPORT"

echo "## 2. Frontend con fetch directo a filtros" >> "$REPORT"
echo '```text' >> "$REPORT"
grep -RIn --exclude-dir=node_modules --exclude-dir=.git \
  -E "/api/empresas|/api/unidades|/api/sucursales|/api/almacenes|/api/servers|/api/servidores|/api/productos|/api/vendedores|/api/proveedores" \
  /app/frontend/src 2>/dev/null >> "$REPORT" || true
echo '```' >> "$REPORT"
echo "" >> "$REPORT"

echo "## 3. Posibles conexiones live en backend" >> "$REPORT"
echo '```text' >> "$REPORT"
grep -RIn --exclude-dir=venv --exclude-dir=__pycache__ --exclude-dir=node_modules --exclude-dir=.git \
  -E "execute_sql_query\\(|pyodbc.connect|pymssql.connect|pytds.connect|MongoClient|AsyncIOMotorClient|mongoose|mongodb|motor" \
  /app/backend 2>/dev/null | head -500 >> "$REPORT" || true
echo '```' >> "$REPORT"
echo "" >> "$REPORT"

echo "## 4. Hardcodes críticos" >> "$REPORT"
echo '```text' >> "$REPORT"
grep -RIn --exclude-dir=venv --exclude-dir=__pycache__ --exclude-dir=node_modules --exclude-dir=.git \
  -E "CIENFUEGOS|ESTELAR|130MID|130QRO|ORIGEN|SoftRestaurant|MPRO|Enterprise|exclude_core|visible_en_operaciones|es_core" \
  /app/backend /app/frontend/src 2>/dev/null | head -500 >> "$REPORT" || true
echo '```' >> "$REPORT"

echo ""
echo "Reporte generado:"
echo "$REPORT"
