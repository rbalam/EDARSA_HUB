#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/app}"
FECHA_INICIO="${2:-2026-06-01}"
FECHA_FIN="${3:-2026-06-01}"

BACKEND="$ROOT/backend"
REPORT_DIR="$ROOT/docs/reports"
LOG_DIR="$ROOT/docs/reports/sync_sales_dry_runs"

mkdir -p "$REPORT_DIR"
mkdir -p "$LOG_DIR"

REPORT="$REPORT_DIR/RESULTADO_SYNC_SALES_DRY_RUN_TODAS_UNIDADES_${FECHA_INICIO}.md"

UNIDADES=(
  "CIENFUEGOS"
  "130MID"
  "ESTELAR"
  "130QRO"
  "ORIGEN"
)

echo "# RESULTADO SYNC_SALES DRY-RUN TODAS LAS UNIDADES" > "$REPORT"
echo "" >> "$REPORT"
echo "Generado: $(date -Iseconds)" >> "$REPORT"
echo "" >> "$REPORT"
echo "Fecha inicio: $FECHA_INICIO" >> "$REPORT"
echo "Fecha fin: $FECHA_FIN" >> "$REPORT"
echo "" >> "$REPORT"
echo "## Reglas" >> "$REPORT"
echo "" >> "$REPORT"
echo "- Solo se ejecuta --dry-run." >> "$REPORT"
echo "- No se ejecuta --execute." >> "$REPORT"
echo "- No debe insertar en Sync_Sales." >> "$REPORT"
echo "- No debe modificar Comercial_KPIs_Diarios_v2." >> "$REPORT"
echo "- SoftRestaurant legacy debe construir items JSON en Python." >> "$REPORT"
echo "- Prohibido FOR JSON PATH contra SoftRestaurant legacy." >> "$REPORT"
echo "" >> "$REPORT"

cd "$BACKEND"

echo "## 1. Validación SERVER_SECRET_KEY" >> "$REPORT"
echo '```text' >> "$REPORT"
python tools/validate_server_secret_key.py >> "$REPORT" 2>&1 || {
  echo '```' >> "$REPORT"
  echo "" >> "$REPORT"
  echo "❌ **FAIL:** SERVER_SECRET_KEY no está configurada o no descifra correctamente." >> "$REPORT"
  echo "" >> "$REPORT"
  echo "No se ejecutaron dry-runs." >> "$REPORT"
  exit 1
}
echo '```' >> "$REPORT"
echo "" >> "$REPORT"

echo "## 2. Estado inicial Sync_Sales" >> "$REPORT"
echo "" >> "$REPORT"
echo "Ejecutar en SQL Server para validar antes/después:" >> "$REPORT"
echo '```sql' >> "$REPORT"
cat >> "$REPORT" <<'SQL'
SELECT
    COUNT(*) AS registros,
    MIN(FechaHora) AS fecha_minima,
    MAX(FechaHora) AS fecha_maxima,
    MAX(last_modified) AS ultima_modificacion
FROM dbo.Sync_Sales;
SQL
echo '```' >> "$REPORT"
echo "" >> "$REPORT"

echo "## 3. Dry-runs por unidad" >> "$REPORT"
echo "" >> "$REPORT"
echo "| Unidad | Estado | Log |" >> "$REPORT"
echo "|---|---|---|" >> "$REPORT"

for UNIDAD in "${UNIDADES[@]}"; do
  SAFE_UNIDAD="$(echo "$UNIDAD" | tr '[:lower:]' '[:upper:]' | tr -c 'A-Z0-9_' '_')"
  LOG_FILE="$LOG_DIR/dry_run_${SAFE_UNIDAD}_${FECHA_INICIO}_${FECHA_FIN}.log"

  echo "Ejecutando dry-run $UNIDAD..."

  set +e
  python tools/sync_sales_dry_run.py \
    --unidad "$UNIDAD" \
    --fecha-inicio "$FECHA_INICIO" \
    --fecha-fin "$FECHA_FIN" \
    --dry-run \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  set -e

  if [[ "$EXIT_CODE" -eq 0 ]]; then
    echo "| $UNIDAD | ✅ OK | $LOG_FILE |" >> "$REPORT"
  else
    echo "| $UNIDAD | ❌ FAIL | $LOG_FILE |" >> "$REPORT"
  fi
done

echo "" >> "$REPORT"

echo "## 4. Logs completos" >> "$REPORT"
echo "" >> "$REPORT"

for UNIDAD in "${UNIDADES[@]}"; do
  SAFE_UNIDAD="$(echo "$UNIDAD" | tr '[:lower:]' '[:upper:]' | tr -c 'A-Z0-9_' '_')"
  LOG_FILE="$LOG_DIR/dry_run_${SAFE_UNIDAD}_${FECHA_INICIO}_${FECHA_FIN}.log"

  echo "### $UNIDAD" >> "$REPORT"
  echo "" >> "$REPORT"
  echo '```text' >> "$REPORT"
  cat "$LOG_FILE" >> "$REPORT" || true
  echo '```' >> "$REPORT"
  echo "" >> "$REPORT"
done

echo "## 5. Validaciones obligatorias posteriores" >> "$REPORT"
echo "" >> "$REPORT"
echo "Después de este dry-run, validar en SQL Server:" >> "$REPORT"
echo "" >> "$REPORT"
echo '```sql' >> "$REPORT"
cat >> "$REPORT" <<'SQL'
/* Sync_Sales debe seguir sin cambios si solo fue dry-run */
SELECT
    COUNT(*) AS registros,
    MIN(FechaHora) AS fecha_minima,
    MAX(FechaHora) AS fecha_maxima,
    MAX(last_modified) AS ultima_modificacion
FROM dbo.Sync_Sales;

/* Comercial_KPIs_Diarios_v2 no debe cambiar por el dry-run */
SELECT
    COUNT(*) AS registros,
    MIN(fecha_operacion) AS fecha_minima,
    MAX(fecha_operacion) AS fecha_maxima,
    MAX(fecha_sincronizacion) AS ultima_sincronizacion
FROM dbo.Comercial_KPIs_Diarios_v2;
SQL
echo '```' >> "$REPORT"

echo "" >> "$REPORT"
echo "## 6. Criterio de aprobación para --execute" >> "$REPORT"
echo "" >> "$REPORT"
echo "No autorizar --execute hasta que todas las unidades tengan:" >> "$REPORT"
echo "" >> "$REPORT"
echo "- tickets > 0" >> "$REPORT"
echo "- items JSON válido" >> "$REPORT"
echo "- monto_total > 0" >> "$REPORT"
echo "- tickets_con_monto_cero = 0" >> "$REPORT"
echo "- items_con_total_cero = 0 o justificados" >> "$REPORT"
echo "- Sync_Sales sin cambios en dry-run" >> "$REPORT"
echo "- Comercial_KPIs_Diarios_v2 sin cambios" >> "$REPORT"

echo "Reporte generado: $REPORT"
