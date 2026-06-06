#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/app}"

echo "============================================================"
echo "EDARSAHUB - INTELIGENCIA COMERCIAL NEXT STEPS"
echo "============================================================"

echo ""
echo "1) Diagnóstico RBAC MongoDB → Usuario_* SQL"
if [[ -f "$ROOT/scripts/030_audit_mongodb_rbac_mapping.sh" ]]; then
  bash "$ROOT/scripts/030_audit_mongodb_rbac_mapping.sh" "$ROOT"
else
  echo "Falta $ROOT/scripts/030_audit_mongodb_rbac_mapping.sh"
fi

echo ""
echo "2) Validación IC Fase 1 backend/frontend"
if [[ -f "$ROOT/scripts/032_validar_inteligencia_comercial_fase1.sh" ]]; then
  bash "$ROOT/scripts/032_validar_inteligencia_comercial_fase1.sh" "$ROOT"
else
  echo "Falta $ROOT/scripts/032_validar_inteligencia_comercial_fase1.sh"
fi

echo ""
echo "3) Reportes generados"
ls -la "$ROOT/docs/reports" | tail -50

echo ""
echo "IMPORTANTE:"
echo "- Los SQL 030, 031 y 032 deben ejecutarse en SQL Server."
echo "- Este script bash no migra usuarios."
echo "- Este script bash no sincroniza ventas."
echo "- Este script bash no toca MongoDB."
