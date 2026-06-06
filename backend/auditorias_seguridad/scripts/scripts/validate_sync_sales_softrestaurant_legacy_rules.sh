#!/usr/bin/env bash
# =============================================================================
# VALIDADOR DE REGLA: SYNC_SALES SOFTRESTAURANT LEGACY
# =============================================================================
# Este script valida que el código cumpla con las reglas permanentes:
# 1. NO usar FOR JSON PATH contra SoftRestaurant
# 2. NO usar totalsrx/subtotalsrx como fuente de importe
# 3. Calcular item_total como cantidad * precio en Python
# 4. Usar json.dumps() para construir items JSON
# =============================================================================
set -euo pipefail

ROOT="${1:-/app}"
TARGET="$ROOT/backend/tools/sync_sales_dry_run.py"
REPORT="$ROOT/docs/reports/VALIDACION_REGLA_SYNC_SALES_SOFTRESTAURANT_LEGACY.md"

mkdir -p "$ROOT/docs/reports"

FAIL=0
WARNINGS=0

echo "=========================================="
echo "VALIDADOR: SYNC_SALES SOFTRESTAURANT LEGACY"
echo "=========================================="
echo ""

# 1. Buscar FOR JSON PATH en archivos relevantes (solo sync_sales_dry_run.py)
echo "Paso 1: Buscando FOR JSON PATH..."
FOR_JSON_MATCHES=$(grep -ni "FOR JSON PATH" "$TARGET" 2>/dev/null || echo "")

# Filtrar solo coincidencias activas (excluir comentarios y documentación)
# Las líneas válidas son las que NO contienen: "NO USA", "NO depende", "COMPATIBLE", "Prohibido", comentarios
FOR_JSON_ACTIVE=""
if [[ -n "$FOR_JSON_MATCHES" ]]; then
    FOR_JSON_ACTIVE=$(echo "$FOR_JSON_MATCHES" | grep -vi "NO USA" | grep -vi "NO depende" | grep -vi "COMPATIBLE" | grep -vi "Prohibido" | grep -vi "^[0-9]*:#" || echo "")
fi

# 2. Buscar uso de totalsrx/subtotalsrx como fuente de importe
echo "Paso 2: Buscando uso de totalsrx/subtotalsrx..."
BAD_TOTALSRX_USAGE=$(grep -rni "totalsrx\|subtotalsrx" \
    "$TARGET" \
    --include="*.py" \
    2>/dev/null || echo "")

# 3. Verificar cálculo Python de cantidad * precio
echo "Paso 3: Verificando cálculo Python cantidad * precio..."
PY_CALC_PRESENT=$(grep -n "quantity.*price\|cantidad.*precio\|item_quantity.*item_price\|calculate_softrestaurant_item_total" \
    "$TARGET" \
    2>/dev/null || echo "")

# 4. Verificar json.dumps
echo "Paso 4: Verificando json.dumps..."
JSON_DUMPS_PRESENT=$(grep -n "json.dumps" "$TARGET" 2>/dev/null || echo "")

# 5. Verificar función específica
echo "Paso 5: Verificando función calculate_softrestaurant_item_total..."
CALC_FUNC_PRESENT=$(grep -n "def calculate_softrestaurant_item_total" "$TARGET" 2>/dev/null || echo "")

# Generar reporte
{
    echo "# VALIDACIÓN REGLA SYNC_SALES SOFTRESTAURANT LEGACY"
    echo ""
    echo "**Generado:** $(date -Iseconds)"
    echo "**Archivo validado:** $TARGET"
    echo ""
    echo "---"
    echo ""
    echo "## Regla"
    echo ""
    echo "SoftRestaurant legacy no debe usar FOR JSON PATH ni totalsrx/subtotalsrx como importe."
    echo "El item_total debe calcularse en Python como \`cantidad * precio\`."
    echo ""
    echo "---"
    echo ""
    echo "## 1. Coincidencias FOR JSON PATH"
    echo ""
    echo "\`\`\`"
    if [[ -z "$FOR_JSON_MATCHES" ]]; then
        echo "✅ No se encontró FOR JSON PATH"
    else
        echo "$FOR_JSON_MATCHES"
    fi
    echo "\`\`\`"
    echo ""
    echo "## 2. Referencias a totalsrx/subtotalsrx"
    echo ""
    echo "\`\`\`"
    if [[ -z "$BAD_TOTALSRX_USAGE" ]]; then
        echo "✅ No se encontraron referencias"
    else
        echo "$BAD_TOTALSRX_USAGE"
    fi
    echo "\`\`\`"
    echo ""
    echo "## 3. Evidencia cálculo Python cantidad * precio"
    echo ""
    echo "\`\`\`"
    if [[ -z "$PY_CALC_PRESENT" ]]; then
        echo "❌ No se encontró evidencia"
    else
        echo "$PY_CALC_PRESENT"
    fi
    echo "\`\`\`"
    echo ""
    echo "## 4. Evidencia json.dumps"
    echo ""
    echo "\`\`\`"
    if [[ -z "$JSON_DUMPS_PRESENT" ]]; then
        echo "❌ No se encontró json.dumps"
    else
        echo "$JSON_DUMPS_PRESENT"
    fi
    echo "\`\`\`"
    echo ""
    echo "## 5. Función calculate_softrestaurant_item_total"
    echo ""
    echo "\`\`\`"
    if [[ -z "$CALC_FUNC_PRESENT" ]]; then
        echo "❌ Función no encontrada"
    else
        echo "$CALC_FUNC_PRESENT"
    fi
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
    echo "## Resultado"
    echo ""
} > "$REPORT"

# Evaluar resultados
if [[ -n "$FOR_JSON_ACTIVE" ]]; then
    echo "❌ FAIL: Se encontró FOR JSON PATH activo en flujo revisado." | tee -a "$REPORT"
    FAIL=1
else
    echo "✅ PASS: No hay FOR JSON PATH activo." | tee -a "$REPORT"
fi

if echo "$BAD_TOTALSRX_USAGE" | grep -qi "= .*totalsrx\|= .*subtotalsrx\|return.*totalsrx\|return.*subtotalsrx" 2>/dev/null; then
    echo "❌ FAIL: Se usa totalsrx/subtotalsrx como fuente de importe." | tee -a "$REPORT"
    FAIL=1
elif [[ -n "$BAD_TOTALSRX_USAGE" ]]; then
    echo "⚠️ WARNING: Referencias a totalsrx/subtotalsrx encontradas (validar que sean solo diagnóstico)." | tee -a "$REPORT"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ PASS: No hay uso de totalsrx/subtotalsrx como importe." | tee -a "$REPORT"
fi

if [[ -z "$PY_CALC_PRESENT" ]]; then
    echo "❌ FAIL: No se encontró cálculo item_total = cantidad * precio en Python." | tee -a "$REPORT"
    FAIL=1
else
    echo "✅ PASS: Cálculo Python cantidad * precio presente." | tee -a "$REPORT"
fi

if [[ -z "$JSON_DUMPS_PRESENT" ]]; then
    echo "❌ FAIL: No se encontró json.dumps para construir items JSON." | tee -a "$REPORT"
    FAIL=1
else
    echo "✅ PASS: json.dumps presente." | tee -a "$REPORT"
fi

if [[ -z "$CALC_FUNC_PRESENT" ]]; then
    echo "⚠️ WARNING: Función calculate_softrestaurant_item_total no encontrada (recomendada)." | tee -a "$REPORT"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ PASS: Función calculate_softrestaurant_item_total presente." | tee -a "$REPORT"
fi

echo "" | tee -a "$REPORT"

if [[ "$FAIL" -eq 0 ]]; then
    echo "---" >> "$REPORT"
    echo "" >> "$REPORT"
    echo "## **RESULTADO = OK** ✅" >> "$REPORT"
    if [[ "$WARNINGS" -gt 0 ]]; then
        echo "(con $WARNINGS warnings)" >> "$REPORT"
    fi
    echo ""
    echo "=========================================="
    echo "RESULTADO: OK ✅"
    if [[ "$WARNINGS" -gt 0 ]]; then
        echo "($WARNINGS warnings)"
    fi
    echo "=========================================="
    echo "Reporte: $REPORT"
    exit 0
else
    echo "---" >> "$REPORT"
    echo "" >> "$REPORT"
    echo "## **RESULTADO = FAIL** ❌" >> "$REPORT"
    echo ""
    echo "=========================================="
    echo "RESULTADO: FAIL ❌"
    echo "=========================================="
    echo "Reporte: $REPORT"
    exit 1
fi
