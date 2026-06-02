#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/app}"
OUT="$ROOT/docs/reports/AUDITORIA_CONEXIONES_LIVE.md"

mkdir -p "$ROOT/docs/reports"

{
  echo "# Auditoría de Conexiones Live"
  echo ""
  echo "Generado: $(date -Iseconds)"
  echo ""
  echo "## Posibles conexiones live"
  echo ""
  echo '```text'
  grep -Rni \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude-dir=venv \
    --exclude-dir=__pycache__ \
    "pyodbc.connect\|pymssql\|requests.get\|requests.post\|httpx\|aiohttp\|SoftRestaurant\|MPRO\|NetPay\|api_url\|host\|database_name\|Servidores_Conexiones" \
    "$ROOT/backend" "$ROOT/frontend" "$ROOT/docs" 2>/dev/null || true
  echo '```'
  echo ""
  echo "## Riesgo"
  echo ""
  echo "- Si aparece dentro de endpoints de dashboard/reportes: P0."
  echo "- Si aparece dentro de scheduler/jobs/sync: permitido con control."
  echo "- Si aparece dentro de configuración/repositorio legado: documentar migración."
} > "$OUT"

echo "Reporte generado: $OUT"
