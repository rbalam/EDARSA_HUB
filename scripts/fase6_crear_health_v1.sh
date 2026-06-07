#!/usr/bin/env bash
set -euo pipefail

# FASE 6 (CORREGIDO por el agente)
# Crear /api/health/v1 canónico, SQL-First, NO-LIVE
#
# NOTA DE SEGURIDAD: el registro del router NO se hace por prepend en la línea 1
# de server.py (eso ejecutaría imports ANTES de load_dotenv y rompería el arranque,
# según la advertencia explícita en server.py líneas 1-18). En su lugar:
#   - import junto a los demás routers (tras finanzas.health)
#   - include justo después de app.include_router(api_router)
#
# Los archivos del módulo ya fueron creados por el agente:
#   backend/modules/health_v1/__init__.py
#   backend/modules/health_v1/routes.py
# y el registro en server.py se aplicó vía edición controlada.
#
# Este script queda como referencia/validación idempotente.

BACK_DIR="/app/backend"
SERVER_PY="$BACK_DIR/server.py"
ROUTES_PY="$BACK_DIR/modules/health_v1/routes.py"

echo "=== Validación de presencia ==="
test -f "$ROUTES_PY" && echo "OK routes.py" || { echo "FALTA routes.py"; exit 1; }
grep -q "from modules.health_v1.routes import router as health_v1_router" "$SERVER_PY" && echo "OK import en server.py" || { echo "FALTA import"; exit 1; }
grep -q "app.include_router(health_v1_router, prefix=\"/api\")" "$SERVER_PY" && echo "OK include en server.py" || { echo "FALTA include"; exit 1; }

echo "=== Compile ==="
python3 -m py_compile "$ROUTES_PY" && echo "COMPILE routes.py OK"

echo "OK - FASE 6 (registro seguro) verificada"
