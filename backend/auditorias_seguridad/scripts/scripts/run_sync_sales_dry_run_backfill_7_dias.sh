#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/app}"
FECHA_INICIO="${2:-2026-06-01}"
FECHA_FIN="${3:-2026-06-07}"

BACKEND="$ROOT/backend"
REPORT_DIR="$ROOT/docs/reports"
LOG_DIR="$ROOT/docs/reports/sync_sales_dry_run_backfill_7_dias"

mkdir -p "$REPORT_DIR"
mkdir -p "$LOG_DIR"

REPORT="$REPORT_DIR/RESULTADO_SYNC_SALES_DRY_RUN_BACKFILL_${FECHA_INICIO}_${FECHA_FIN}.md"

UNIDADES=(
  "CIENFUEGOS"
  "130MID"
  "ESTELAR"
  "130QRO"
  "ORIGEN"
)

echo "# RESULTADO SYNC_SALES DRY-RUN BACKFILL 7 DÍAS" > "$REPORT"
echo "" >> "$REPORT"
echo "Generado: $(date -Iseconds)" >> "$REPORT"
echo "" >> "$REPORT"
echo "Fecha inicio: $FECHA_INICIO" >> "$REPORT"
echo "Fecha fin: $FECHA_FIN" >> "$REPORT"
echo "" >> "$REPORT"

echo "## Reglas de ejecución" >> "$REPORT"
echo "" >> "$REPORT"
echo "- Solo se ejecuta modo --dry-run." >> "$REPORT"
echo "- No se ejecuta --execute." >> "$REPORT"
echo "- No debe insertar datos en Sync_Sales." >> "$REPORT"
echo "- No debe modificar Comercial_KPIs_Diarios_v2." >> "$REPORT"
echo "- No debe tocar Sync_PAX_Detalle." >> "$REPORT"
echo "- No debe activar scheduler automático." >> "$REPORT"
echo "- SoftRestaurant legacy debe construir items JSON en Python." >> "$REPORT"
echo "- Prohibido usar FOR JSON PATH contra SoftRestaurant legacy." >> "$REPORT"
echo "- Para SoftRestaurant legacy, item_total debe calcularse como cantidad * precio." >> "$REPORT"
echo "" >> "$REPORT"

cd "$BACKEND"

echo "## 1. Validación SERVER_SECRET_KEY" >> "$REPORT"
echo "" >> "$REPORT"
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

echo "## 2. Validación de regla SoftRestaurant legacy" >> "$REPORT"
echo "" >> "$REPORT"
echo '```text' >> "$REPORT"

if [[ -f "$ROOT/scripts/validate_sync_sales_softrestaurant_legacy_rules.sh" ]]; then
  bash "$ROOT/scripts/validate_sync_sales_softrestaurant_legacy_rules.sh" "$ROOT" >> "$REPORT" 2>&1 || {
    echo "WARNING: La validación de regla legacy falló. Revisar reporte específico." >> "$REPORT"
  }
else
  echo "WARNING: No existe validate_sync_sales_softrestaurant_legacy_rules.sh" >> "$REPORT"
fi

echo '```' >> "$REPORT"
echo "" >> "$REPORT"

echo "## 3. Estado inicial de tablas" >> "$REPORT"
echo "" >> "$REPORT"
echo "Validar en SQL Server antes y después:" >> "$REPORT"
echo "" >> "$REPORT"
echo '```sql' >> "$REPORT"
cat >> "$REPORT" <<'SQL'
SELECT
    COUNT(*) AS registros,
    MIN(FechaHora) AS fecha_minima,
    MAX(FechaHora) AS fecha_maxima,
    MAX(last_modified) AS ultima_modificacion
FROM dbo.Sync_Sales;

SELECT
    COUNT(*) AS registros,
    MIN(fecha_operacion) AS fecha_minima,
    MAX(fecha_operacion) AS fecha_maxima,
    MAX(fecha_sincronizacion) AS ultima_sincronizacion
FROM dbo.Comercial_KPIs_Diarios_v2;

SELECT
    COUNT(*) AS registros
FROM dbo.Sync_PAX_Detalle;
SQL
echo '```' >> "$REPORT"
echo "" >> "$REPORT"

echo "## 4. Ejecución dry-run por unidad" >> "$REPORT"
echo "" >> "$REPORT"
echo "| Unidad | Estado | Log |" >> "$REPORT"
echo "|---|---|---|" >> "$REPORT"

for UNIDAD in "${UNIDADES[@]}"; do
  SAFE_UNIDAD="$(echo "$UNIDAD" | tr '[:lower:]' '[:upper:]' | tr -c 'A-Z0-9_' '_')"
  LOG_FILE="$LOG_DIR/dry_run_backfill_${SAFE_UNIDAD}_${FECHA_INICIO}_${FECHA_FIN}.log"

  echo "Ejecutando dry-run backfill $UNIDAD del $FECHA_INICIO al $FECHA_FIN..."

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

echo "## 5. Logs completos por unidad" >> "$REPORT"
echo "" >> "$REPORT"

for UNIDAD in "${UNIDADES[@]}"; do
  SAFE_UNIDAD="$(echo "$UNIDAD" | tr '[:lower:]' '[:upper:]' | tr -c 'A-Z0-9_' '_')"
  LOG_FILE="$LOG_DIR/dry_run_backfill_${SAFE_UNIDAD}_${FECHA_INICIO}_${FECHA_FIN}.log"

  echo "### $UNIDAD" >> "$REPORT"
  echo "" >> "$REPORT"
  echo '```text' >> "$REPORT"
  cat "$LOG_FILE" >> "$REPORT" || true
  echo '```' >> "$REPORT"
  echo "" >> "$REPORT"
done

echo "## 6. Validaciones SQL posteriores obligatorias" >> "$REPORT"
echo "" >> "$REPORT"
echo "Después del dry-run, ejecutar en SQL Server. Sync_Sales no debe cambiar por tratarse de --dry-run." >> "$REPORT"
echo "" >> "$REPORT"
echo '```sql' >> "$REPORT"
cat >> "$REPORT" <<SQL
/* ============================================================
   Validación posterior al dry-run backfill
   ============================================================ */

SELECT
    COUNT(*) AS registros,
    MIN(FechaHora) AS fecha_minima,
    MAX(FechaHora) AS fecha_maxima,
    MAX(last_modified) AS ultima_modificacion
FROM dbo.Sync_Sales;

SELECT
    UnidadNegocio,
    CAST(FechaHora AS DATE) AS Fecha,
    COUNT(*) AS tickets,
    SUM(MontoTotal) AS monto_total
FROM dbo.Sync_Sales
WHERE CAST(FechaHora AS DATE) BETWEEN '$FECHA_INICIO' AND '$FECHA_FIN'
GROUP BY UnidadNegocio, CAST(FechaHora AS DATE)
ORDER BY UnidadNegocio, Fecha;

SELECT
    UnidadNegocio,
    NumeroTicket,
    CAST(FechaHora AS DATE) AS Fecha,
    COUNT(*) AS duplicados
FROM dbo.Sync_Sales
WHERE CAST(FechaHora AS DATE) BETWEEN '$FECHA_INICIO' AND '$FECHA_FIN'
GROUP BY UnidadNegocio, NumeroTicket, CAST(FechaHora AS DATE)
HAVING COUNT(*) > 1
ORDER BY UnidadNegocio, Fecha, NumeroTicket;

SELECT
    COUNT(*) AS registros,
    MIN(fecha_operacion) AS fecha_minima,
    MAX(fecha_operacion) AS fecha_maxima,
    MAX(fecha_sincronizacion) AS ultima_sincronizacion
FROM dbo.Comercial_KPIs_Diarios_v2;

SELECT
    COUNT(*) AS registros
FROM dbo.Sync_PAX_Detalle;
SQL
echo '```' >> "$REPORT"
echo "" >> "$REPORT"

echo "## 7. Comparativo recomendado contra KPIs" >> "$REPORT"
echo "" >> "$REPORT"
echo "Ejecutar en SQL Server para comparar el rango contra Comercial_KPIs_Diarios_v2:" >> "$REPORT"
echo "" >> "$REPORT"
echo '```sql' >> "$REPORT"
cat >> "$REPORT" <<SQL
SELECT
    unidad_negocio_nombre,
    sistema_origen,
    fecha_operacion,
    ventas_total,
    ventas_sin_propina,
    propinas_total,
    tickets_total,
    pax_total
FROM dbo.Comercial_KPIs_Diarios_v2
WHERE fecha_operacion BETWEEN '$FECHA_INICIO' AND '$FECHA_FIN'
ORDER BY unidad_negocio_nombre, fecha_operacion;
SQL
echo '```' >> "$REPORT"
echo "" >> "$REPORT"

echo "## 8. Criterios de aprobación para execute del backfill" >> "$REPORT"
echo "" >> "$REPORT"
echo "No autorizar --execute hasta que el reporte demuestre:" >> "$REPORT"
echo "" >> "$REPORT"
echo "- Todas las unidades ejecutaron dry-run OK." >> "$REPORT"
echo "- Tickets por unidad y día > 0 cuando exista operación." >> "$REPORT"
echo "- Monto total por unidad y día > 0 cuando existan tickets." >> "$REPORT"
echo "- 100% items JSON válidos." >> "$REPORT"
echo "- 0 tickets con monto cero sin justificación." >> "$REPORT"
echo "- 0 duplicados no controlados." >> "$REPORT"
echo "- Sync_Sales no cambió durante dry-run." >> "$REPORT"
echo "- Comercial_KPIs_Diarios_v2 no cambió." >> "$REPORT"
echo "- Sync_PAX_Detalle no cambió." >> "$REPORT"
echo "- Diferencias contra KPIs explicadas por propinas, ventanas de sync, redondeos o reglas de corte." >> "$REPORT"
echo "" >> "$REPORT"

echo "## 9. Estado final" >> "$REPORT"
echo "" >> "$REPORT"
echo "Backfill 7 días ejecutado solo en modo dry-run. No se autoriza --execute con este script." >> "$REPORT"

echo "Reporte generado: $REPORT"
echo "Logs: $LOG_DIR"
