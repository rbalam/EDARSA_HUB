#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/app}"
OUT="$ROOT/docs/reports/MATRIZ_NO_LIVE_DASHBOARD_EDARSAHUB.md"

mkdir -p "$ROOT/docs/reports"

TMP="$(mktemp)"

grep -Rni \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  --exclude-dir=venv \
  --exclude-dir=__pycache__ \
  --exclude="*.pyc" \
  "pyodbc.connect\|pymssql.connect\|requests.get\|requests.post\|httpx\|aiohttp\|SoftRestaurant\|MPRO\|NetPay\|api_url\|database_name\|Servidores_Conexiones\|motor.motor_asyncio\|pymongo\|AsyncIOMotor" \
  "$ROOT/backend" "$ROOT/frontend" "$ROOT/docs" 2>/dev/null > "$TMP" || true

{
  echo "# MATRIZ NO-LIVE DASHBOARD EDARSAHUB"
  echo ""
  echo "Generado: $(date -Iseconds)"
  echo ""
  echo "## Criterios"
  echo ""
  echo "| Prioridad | Criterio | Accion |"
  echo "|---|---|---|"
  echo "| P0 | Endpoints/dashboard/reportes con live/Mongo/API externa | Remediar primero |"
  echo "| P1 | Repositorios/servicios de modulos con live fuera de scheduler | Migrar a SQL sincronizado |"
  echo "| P2 | Helpers/documentacion/configuracion no productiva | Documentar |"
  echo "| PERMITIDO | scheduler/jobs/sync/scripts/tests/tools/adapters controlados | Mantener con logs |"
  echo "| FALSO_POSITIVO | policy scanner o strings de busqueda | Ignorar |"
  echo ""
  echo "## Hallazgos clasificados"
  echo ""
  echo "| Prioridad | Archivo | Linea | Patron | Accion recomendada |"
  echo "|---|---|---:|---|---|"

  while IFS= read -r line; do
    file="$(echo "$line" | cut -d: -f1)"
    lineno="$(echo "$line" | cut -d: -f2)"
    content="$(echo "$line" | cut -d: -f3-)"

    priority="P2"
    action="Documentar"

    lower="$(echo "$file" | tr '[:upper:]' '[:lower:]')"

    if [[ "$lower" == *"no_live_dashboard_policy.py"* ]]; then
      priority="FALSO_POSITIVO"
      action="Ignorar: contiene patrones de busqueda"
    elif [[ "$lower" == *"/scripts/"* || "$lower" == *"/tests/"* || "$lower" == *"/tools/"* ]]; then
      priority="PERMITIDO"
      action="Herramienta/test; no endpoint productivo"
    elif [[ "$lower" == *"/scheduler/"* || "$lower" == *"/jobs/"* || "$lower" == *"/sync"* || "$lower" == *"/adapters.py"* ]]; then
      priority="PERMITIDO"
      action="Permitido solo como sincronizacion/control; validar logs y no uso directo en dashboard"
    elif [[ "$lower" == *"/modules/comercial/routes.py"* || "$lower" == *"/modules/comercial/service.py"* || "$lower" == *"/modules/comercial/repository.py"* ]]; then
      priority="P0"
      action="Marcar Comercial Legacy; nuevos dashboards deben usar /api/comercial/inteligencia/*"
    elif [[ "$lower" == *"/api/"* || "$lower" == *"/routes"* || "$lower" == *"dashboard"* || "$lower" == *"report"* || "$lower" == *"reporte"* ]]; then
      priority="P0"
      action="Remediar si alimenta dashboard/reporte; mover a SQL sincronizado"
    elif [[ "$lower" == *"/modules/"* || "$lower" == *"/core/"* ]]; then
      priority="P1"
      action="Revisar dependencia; migrar a SQL sincronizado si no es job"
    fi

    safe_content="$(echo "$content" | sed 's/|/\\|/g' | cut -c1-140)"
    echo "| $priority | \`$file\` | $lineno | \`$safe_content\` | $action |"
  done < "$TMP"

  echo ""
  echo "## Resumen"
  echo ""
  echo '```text'
  awk -F'|' '/^\| P0 /{p0++} /^\| P1 /{p1++} /^\| P2 /{p2++} /^\| PERMITIDO /{ok++} /^\| FALSO_POSITIVO /{fp++} END {print "P0="p0+0"\nP1="p1+0"\nP2="p2+0"\nPERMITIDO="ok+0"\nFALSO_POSITIVO="fp+0}' "$OUT" 2>/dev/null || true
  echo '```'
} > "$OUT"

rm -f "$TMP"

echo "Reporte generado: $OUT"
