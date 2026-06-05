#!/usr/bin/env bash
set -e

echo "=== AUDITORIA HARDCODE UNIDADES ==="

grep -RIn \
  "130MID\|130QRO\|ESTELAR\|CIENFUEGOS\|ORIGEN\|130° MERIDA\|130° QUERETARO\|LA ESTELAR" \
  /app/backend /app/frontend/src \
  --exclude-dir=venv \
  --exclude-dir=__pycache__ \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  --include="*.py" --include="*.js" --include="*.jsx" \
  > /app/backend/auditoria_unidades_hardcodeadas.txt 2>/dev/null || true

wc -l /app/backend/auditoria_unidades_hardcodeadas.txt
head -50 /app/backend/auditoria_unidades_hardcodeadas.txt
