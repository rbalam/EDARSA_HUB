#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/app}"
OUT="$ROOT/docs/reports/VALIDACION_PORTAL_INTELIGENCIA_COMERCIAL_FASE1.md"

mkdir -p "$ROOT/docs/reports"

{
  echo "# VALIDACIÓN PORTAL INTELIGENCIA COMERCIAL FASE 1"
  echo ""
  echo "Generado: $(date -Iseconds)"
  echo ""
  echo "## Objetivo"
  echo ""
  echo "Validar que Inteligencia Comercial Fase 1 opera con EDARSAHUB SQL y sin conexión live en dashboard."
  echo ""
  echo "## Archivos backend detectados"
  echo ""
  echo '```text'
  find "$ROOT/backend" -iname "*inteligencia*" -o -iname "*comercial*repository*" 2>/dev/null | sort || true
  echo '```'
  echo ""
  echo "## Endpoints registrados"
  echo ""
  echo '```text'
  grep -Rni "/api/comercial/inteligencia\|inteligencia_comercial" "$ROOT/backend" "$ROOT/frontend" 2>/dev/null || true
  echo '```'
  echo ""
  echo "## Fuentes SQL canónicas usadas"
  echo ""
  echo '```text'
  grep -Rni "Comercial_Inteligencia_VW_KPIsEjecutivos\|Comercial_KPIs_Diarios_v2\|Comercial_Ventas_Dia_Abiertas_v2\|Sync_PAX_Detalle\|Sync_Sales\|Unidades_Negocio\|Sp_Validar_Inteligencia_Comercial_Status" "$ROOT/backend/modules/comercial" 2>/dev/null || true
  echo '```'
  echo ""
  echo "## Búsqueda de patrones prohibidos en endpoints IC"
  echo ""
  echo '```text'
  grep -Rni "SoftRestaurant\|MPRO\|MongoDB\|motor.motor_asyncio\|pymongo\|AsyncIOMotor\|requests.get\|requests.post\|httpx\|aiohttp\|pyodbc.connect\|pymssql.connect" "$ROOT/backend/modules/comercial" 2>/dev/null || true
  echo '```'
  echo ""
  echo "## Compilación Python"
  echo ""
  echo '```text'
  cd "$ROOT/backend" 2>/dev/null && python -m py_compile server.py 2>&1 || true
  find "$ROOT/backend/modules/comercial" -name "*.py" -print -exec python -m py_compile {} \; 2>&1 || true
  echo '```'
  echo ""
  echo "## Estado esperado"
  echo ""
  echo "| Elemento | Estado esperado |"
  echo "|---|---|"
  echo "| Dashboard ejecutivo | Operativo con Comercial_KPIs_Diarios_v2 |"
  echo "| Sync_Sales | Puede estar SIN_DATOS sin bloquear Fase 1 |"
  echo "| Sync_PAX_Detalle | Puede estar SIN_DATOS sin bloquear Fase 1 |"
  echo "| Dashboard live | Prohibido |"
  echo "| MongoDB comercial | Prohibido |"
  echo "| RBAC | Usuario_* canónico |"
  echo ""
  echo "## Conclusión"
  echo ""
  echo "Fase 1 debe mantenerse operativa con Comercial_KPIs_Diarios_v2 mientras se diagnostica el llenado de Sync_Sales y Sync_PAX_Detalle."
} > "$OUT"

echo "Reporte generado: $OUT"
