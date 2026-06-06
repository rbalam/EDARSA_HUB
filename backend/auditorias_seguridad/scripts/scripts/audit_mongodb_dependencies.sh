#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/app}"
OUT="$ROOT/docs/reports/AUDITORIA_DEPENDENCIAS_MONGODB.md"

mkdir -p "$ROOT/docs/reports"

{
  echo "# Auditoría de Dependencias MongoDB"
  echo ""
  echo "Generado: $(date -Iseconds)"
  echo ""
  echo "## Coincidencias en backend/frontend/docs"
  echo ""
  echo '```text'
  grep -Rni \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude-dir=venv \
    --exclude-dir=__pycache__ \
    --exclude="*.pyc" \
    "mongo\|mongodb\|motor\|pymongo\|AsyncIOMotor\|db\.\|collection" \
    "$ROOT/backend" "$ROOT/frontend" "$ROOT/docs" 2>/dev/null || true
  echo '```'
  echo ""
  echo "## Archivos package/requirements"
  echo ""
  echo '```text'
  grep -Rni \
    "mongo\|mongodb\|motor\|pymongo" \
    "$ROOT/backend/requirements.txt" "$ROOT/frontend/package.json" 2>/dev/null || true
  echo '```'
} > "$OUT"

echo "Reporte generado: $OUT"
