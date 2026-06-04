#!/bin/bash
# ============================================================
# EDARSAHUB - Auditoría de Conexiones LIVE a Sistemas Externos
# ============================================================
# REGLA: EDARSAHUB SQL es la ÚNICA fuente de verdad.
# SoftRestaurant, MPRO y sistemas externos SOLO pueden ser origen de sync.
# PROHIBIDO: Consultas live desde pantallas, reportes, dashboards.
# ============================================================

set -e

REPORT_DIR="/app/docs/reports"
REPORT_FILE="$REPORT_DIR/AUDITORIA_CONEXIONES_LIVE_$(date +%Y%m%d_%H%M%S).md"

mkdir -p "$REPORT_DIR"

echo "# Auditoría de Conexiones LIVE a Sistemas Externos" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "**Fecha:** $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "**Regla:** EDARSAHUB SQL debe ser la ÚNICA fuente de verdad." >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# ============================================================
echo "Analizando código..."
# ============================================================

echo "## 1. Conexiones Directas en Backend (execute_sql_query a servidores externos)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
grep -Rn "execute_sql_query" /app/backend \
  --include="*.py" \
  | grep -v "EDARSAHUB\|edarsahub\|__pycache__\|\.pyc" \
  | grep -v "sync_\|Sync_\|scheduler\|job" \
  | head -100 >> "$REPORT_FILE" 2>/dev/null || echo "No se encontraron conexiones directas" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "## 2. Endpoints que reciben server_id (posibles consultas live)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
grep -Rn "server_id\|server\['host'\]\|server\['database'\]" /app/backend \
  --include="*.py" \
  | grep -v "__pycache__\|\.pyc\|sync_\|Sync_\|scheduler\|job\|registry\|migration" \
  | head -150 >> "$REPORT_FILE" 2>/dev/null || echo "No se encontraron" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "## 3. Rutas API que consultan sistemas externos" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
grep -Rn "@api_router\.\(get\|post\|put\|delete\)" /app/backend/server.py \
  | grep -i "inventario\|movimiento\|pedido\|requisicion\|orden\|compra\|auditoria\|reporte\|dashboard" \
  | head -100 >> "$REPORT_FILE" 2>/dev/null || echo "No se encontraron" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "## 4. Frontend con fetch a servidores dinámicos" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
grep -Rn "server_id\|selectedServer\|serverId" /app/frontend/src \
  --include="*.js" --include="*.jsx" \
  | grep -v "node_modules" \
  | head -100 >> "$REPORT_FILE" 2>/dev/null || echo "No se encontraron" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "## 5. Funciones que usan get_server_connection_info (conexiones dinámicas)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
grep -Rn "get_server_connection_info\|get_connection_info" /app/backend \
  --include="*.py" \
  | grep -v "__pycache__\|sync_\|Sync_\|scheduler\|job" \
  | head -100 >> "$REPORT_FILE" 2>/dev/null || echo "No se encontraron" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "## 6. Conexiones pymssql/pyodbc directas (no a EDARSAHUB)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
grep -Rn "pymssql.connect\|pyodbc.connect\|pytds.connect" /app/backend \
  --include="*.py" \
  | grep -v "__pycache__\|EDARSAHUB\|edarsahub" \
  | head -50 >> "$REPORT_FILE" 2>/dev/null || echo "No se encontraron" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "## 7. Resumen de Violaciones Potenciales" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Contar violaciones
VIOLACIONES_BACKEND=$(grep -Rn "execute_sql_query" /app/backend --include="*.py" | grep -v "EDARSAHUB\|edarsahub\|__pycache__\|sync_\|Sync_\|scheduler\|job" | wc -l)
VIOLACIONES_FRONTEND=$(grep -Rn "server_id\|selectedServer" /app/frontend/src --include="*.js" --include="*.jsx" | grep -v "node_modules" | wc -l)
VIOLACIONES_CONEXION=$(grep -Rn "get_server_connection_info" /app/backend --include="*.py" | grep -v "__pycache__\|sync_\|Sync_\|scheduler\|job" | wc -l)

echo "| Categoría | Cantidad |" >> "$REPORT_FILE"
echo "|-----------|----------|" >> "$REPORT_FILE"
echo "| Conexiones directas backend | $VIOLACIONES_BACKEND |" >> "$REPORT_FILE"
echo "| Referencias server_id frontend | $VIOLACIONES_FRONTEND |" >> "$REPORT_FILE"
echo "| Uso de get_server_connection_info | $VIOLACIONES_CONEXION |" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "## Acciones Recomendadas" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "1. **Migrar endpoints** para que consulten tablas Sync_* en EDARSAHUB SQL" >> "$REPORT_FILE"
echo "2. **Eliminar parámetro server_id** de pantallas operativas" >> "$REPORT_FILE"
echo "3. **Crear vistas/tablas canónicas** en EDARSAHUB para cada entidad" >> "$REPORT_FILE"
echo "4. **Mantener jobs de sync** como único punto de conexión a externos" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "*Generado automáticamente por auditoría EDARSAHUB*" >> "$REPORT_FILE"

echo ""
echo "============================================================"
echo "AUDITORÍA COMPLETADA"
echo "============================================================"
echo ""
echo "Reporte generado: $REPORT_FILE"
echo ""
echo "Resumen:"
echo "  - Conexiones directas backend: $VIOLACIONES_BACKEND"
echo "  - Referencias server_id frontend: $VIOLACIONES_FRONTEND"
echo "  - Uso get_server_connection_info: $VIOLACIONES_CONEXION"
echo ""
