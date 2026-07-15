#!/usr/bin/env bash
set -euo pipefail

: "${EDARSAHUB_TEST_AUTH_EMAIL:?Variable requerida}"
: "${EDARSAHUB_TEST_AUTH_PASSWORD:?Variable requerida}"
export EDARSAHUB_TEST_AUTH_EMAIL EDARSAHUB_TEST_AUTH_PASSWORD

LOGIN_PAYLOAD="$(python3 -c 'import json,os; print(json.dumps({
    "email": os.environ["EDARSAHUB_TEST_AUTH_EMAIL"],
    "password": os.environ["EDARSAHUB_TEST_AUTH_PASSWORD"],
}))')"

# FASE 4 - P0-4  Explorador BD: reponer _execute_sql_direct_with_error en core/db.py
BACK_DIR="/app/backend"
OUT_DIR="/app/auditorias_p5"
TS="$(date +%Y%m%d_%H%M%S)"
RAW="$OUT_DIR/FASE4_P0_4_EXPLORADOR_BD_${TS}.txt"
CORE_DB="$BACK_DIR/core/db.py"
SERVER_PY="$BACK_DIR/server.py"

mkdir -p "$OUT_DIR" /app/scripts
cd /app || exit 1
[ -f "$CORE_DB" ] || { echo "ERROR: no existe $CORE_DB"; exit 1; }

echo "FASE 4 - P0-4 EXPLORADOR BD  $(date)" | tee "$RAW"

echo "===== 1) AUDITORIA PREVIA =====" | tee -a "$RAW"
grep -n "from core.db import _execute_sql_direct_with_error" "$SERVER_PY" | tee -a "$RAW" || true
grep -n "_execute_sql_direct_with_error" "$CORE_DB" | tee -a "$RAW" || echo "helper NO existe (esperado)" | tee -a "$RAW"

echo "===== 2) BACKUP =====" | tee -a "$RAW"
cp "$CORE_DB" "${CORE_DB}.bak_${TS}"
echo "BACKUP: ${CORE_DB}.bak_${TS}" | tee -a "$RAW"

echo "===== 3) PARCHE core/db.py =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
from pathlib import Path
p = Path("/app/backend/core/db.py")
txt = p.read_text(encoding="utf-8")
marker = "async def _execute_sql_direct_with_error("
if marker in txt:
    print("NO CHANGE: helper ya existe")
else:
    block = '''

async def _execute_sql_direct_with_error(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    query: str,
    timeout_seconds: int = 30
) -> tuple:
    """
    Ejecuta SQL directo y retorna (resultado, error_mensaje).
    Explorador BD necesita distinguir 0 resultados vs error.
    Returns: (list, None) si exito; ([], str) si error.
    """
    import asyncio
    try:
        result = await asyncio.to_thread(
            execute_sql_query, host, port, database, username, password, query, timeout_seconds
        )
        if result is None:
            return ([], None)
        return (result, None)
    except Exception as e:
        error_msg = str(e)
        low = error_msg.lower()
        if "login" in low or "inicio de sesion" in low or "authentication" in low:
            return ([], f"Error de autenticacion: acceso denegado a la base '{database}'")
        if "connection refused" in low or "unavailable" in low or "refused" in low:
            return ([], f"Error de conexion: no se puede conectar al servidor {host}:{port}")
        if "timeout" in low:
            return ([], f"Timeout: el servidor no respondio en {timeout_seconds} segundos")
        if "does not exist" in low or ("database" in low and "exist" in low):
            return ([], f"Error: la base de datos '{database}' no existe")
        return ([], f"Error SQL: {error_msg[:180]}")
'''
    txt = txt.rstrip() + "\n\n" + block.lstrip()
    p.write_text(txt, encoding="utf-8")
    print("PATCHED core/db.py")
PY

echo "===== 4) VALIDACION SINTACTICA =====" | tee -a "$RAW"
python3 -m py_compile "$CORE_DB" && echo "COMPILE core/db.py OK" | tee -a "$RAW"

echo "===== 5) REINICIO BACKEND =====" | tee -a "$RAW"
sudo supervisorctl restart backend || true
sleep 9
sudo supervisorctl status backend | head -1 | tee -a "$RAW"

echo "===== 6) LOGIN ADMIN =====" | tee -a "$RAW"
TOKEN=$(curl -sS --max-time 20 -X POST "http://127.0.0.1:8001/api/auth/login" -H "Content-Type: application/json" -d "$LOGIN_PAYLOAD" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))")
echo "TOKEN_LEN=${#TOKEN}" | tee -a "$RAW"
[ -n "$TOKEN" ] || { echo "SIN TOKEN" | tee -a "$RAW"; echo "RAW=$RAW"; exit 1; }

echo "===== 7) SMOKE EXPLORADOR =====" | tee -a "$RAW"
echo "--- conexiones-explorables" | tee -a "$RAW"
curl -sS --max-time 25 -o /tmp/f4_conx.json -w "HTTP=%{http_code} t=%{time_total}s\n" "http://127.0.0.1:8001/api/explorador/conexiones-explorables" -H "Authorization: Bearer $TOKEN" | tee -a "$RAW"
python3 -c "import json;d=json.load(open('/tmp/f4_conx.json'));a=d.get('data') or d.get('conexiones') or (d if isinstance(d,list) else []);print('CONEXIONES=',len(a) if isinstance(a,list) else a)" | tee -a "$RAW" || head -c 200 /tmp/f4_conx.json | tee -a "$RAW"

SID=$(python3 -c "import json
d=json.load(open('/tmp/f4_conx.json'))
a=d.get('data') or d.get('conexiones') or (d if isinstance(d,list) else [])
print(str(a[0].get('id') or a[0].get('_id') or a[0].get('server_id') or '') if isinstance(a,list) and a else '')" 2>/dev/null)
echo "SERVER_ID=$SID" | tee -a "$RAW"
if [ -n "$SID" ]; then
  echo "--- tablas/$SID" | tee -a "$RAW"
  curl -sS --max-time 30 -o /tmp/f4_tab.json -w "HTTP=%{http_code} t=%{time_total}s\n" "http://127.0.0.1:8001/api/explorador/tablas/$SID" -H "Authorization: Bearer $TOKEN" | tee -a "$RAW"
  head -c 240 /tmp/f4_tab.json | tee -a "$RAW"; echo "" | tee -a "$RAW"
fi
echo "RAW_REPORT=$RAW" | tee -a "$RAW"
echo "OK - FASE 4 ejecutado" | tee -a "$RAW"
