#!/bin/bash
set -e

REPORT="/app/docs/reports/TABLEROS_CON_FILTROS_DUPLICADOS.md"

echo "# Tableros con filtros duplicados pendientes de migrar" > "$REPORT"
echo "" >> "$REPORT"
echo "Fecha: $(date)" >> "$REPORT"
echo "" >> "$REPORT"

echo "## Fetch directos a catálogos/filtros desde frontend" >> "$REPORT"
echo '```text' >> "$REPORT"

grep -RIn --exclude-dir=node_modules --exclude-dir=.git \
  -E "fetch\\(|axios|get\\(|/api/empresas|/api/unidades|/api/sucursales|/api/almacenes|/api/servers|/api/servidores|/api/productos|/api/vendedores|setEmpresas|setSucursales|setAlmacenes|setProductos|setVendedores" \
  /app/frontend/src \
  | grep -Ei "dashboard|tablero|page|component|comercial|inventario|compras|finanzas|propinas|tesoreria|servidores" \
  >> "$REPORT" || true

echo '```' >> "$REPORT"

echo "Reporte generado: $REPORT"
