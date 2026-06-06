#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/app}"
OUT="$ROOT/docs/reports/VALIDACION_SERVER_SECRET_KEY_EDARSAHUB.md"

mkdir -p "$ROOT/docs/reports"

{
  echo "# VALIDACIÓN SERVER_SECRET_KEY EDARSAHUB"
  echo ""
  echo "Generado: $(date -Iseconds)"
  echo ""
  echo "## Regla"
  echo ""
  echo "SERVER_SECRET_KEY debe estar configurada en todo entorno que ejecute jobs, scheduler, sincronizaciones, dry-runs o conexiones a Servidores_Conexiones."
  echo ""
  echo "## Validación de variable de entorno"
  echo ""
  echo '```text'
  cd "$ROOT/backend"

  python - <<'PY'
import os
key = os.getenv("SERVER_SECRET_KEY")
print("SERVER_SECRET_KEY_STATUS=", "CONFIGURADA" if key else "NO_CONFIGURADA")
print("SERVER_SECRET_KEY_LENGTH=", len(key) if key else 0)
PY
  echo '```'

  echo ""
  echo "## Validación de descifrado"
  echo ""
  echo '```text'
  cd "$ROOT/backend"
  python tools/validate_server_secret_key.py || true
  echo '```'

  echo ""
  echo "## Archivos relacionados"
  echo ""
  echo '```text'
  ls -la "$ROOT/backend/core/guards" || true
  ls -la "$ROOT/backend/tools" | grep -E "validate_server_secret_key|test_sql_connection|sync_sales" || true
  echo '```'

  echo ""
  echo "## Conclusión esperada"
  echo ""
  echo "- Si RESULT=OK: se pueden ejecutar pruebas de conexión y dry-runs."
  echo "- Si RESULT=FAIL: no ejecutar dry-runs ni jobs contra servidores externos."
  echo ""
  echo "## Seguridad"
  echo ""
  echo "- No se imprimen passwords."
  echo "- No se imprime SERVER_SECRET_KEY."
  echo "- No se modifican credenciales."
  echo "- No se re-cifran secretos."
} > "$OUT"

echo "Reporte generado: $OUT"
