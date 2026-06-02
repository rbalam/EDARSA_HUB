#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/app}"

echo "=== EDARSAHUB GOVERNANCE AUDIT ==="
echo "ROOT=$ROOT"
echo "Fecha: $(date -Iseconds)"
echo ""

# 1. Clasificar violaciones NO-LIVE
if [[ -f "$ROOT/scripts/classify_no_live_violations.sh" ]]; then
  echo ">>> Ejecutando classify_no_live_violations.sh..."
  timeout 120 bash "$ROOT/scripts/classify_no_live_violations.sh" "$ROOT" || echo "Timeout o error en classify_no_live_violations.sh"
else
  echo "No existe classify_no_live_violations.sh"
fi

echo ""

# 2. Generar plantilla de tablas sin clasificar
if [[ -f "$ROOT/scripts/report_tablas_sin_clasificar.sh" ]]; then
  echo ">>> Ejecutando report_tablas_sin_clasificar.sh..."
  bash "$ROOT/scripts/report_tablas_sin_clasificar.sh" "$ROOT"
else
  echo "No existe report_tablas_sin_clasificar.sh"
fi

echo ""

# 3. Ejecutar política NO-LIVE
if [[ -f "$ROOT/backend/core/policies/no_live_dashboard_policy.py" ]]; then
  echo ">>> Ejecutando no_live_dashboard_policy.py..."
  python "$ROOT/backend/core/policies/no_live_dashboard_policy.py" || true
else
  echo "No existe no_live_dashboard_policy.py"
fi

echo ""
echo "=== REPORTES DISPONIBLES ==="
ls -la "$ROOT/docs/reports" 2>/dev/null | tail -50 || echo "No hay reportes"

echo ""
echo "=== AUDIT COMPLETADO ==="
