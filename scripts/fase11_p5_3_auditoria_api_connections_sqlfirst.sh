#!/usr/bin/env bash
set -euo pipefail
APP_DIR="/app"; BACK_DIR="/app/backend"; OUT_DIR="/app/auditorias_p5"
TS="$(date +%Y%m%d_%H%M%S)"
RAW="$OUT_DIR/FASE11_P5_3_AUDITORIA_API_CONNECTIONS_SQLFIRST_${TS}.txt"
REPO_FILE="$BACK_DIR/modules/api_connections/repository.py"
API_FILE="$BACK_DIR/api/admin_core_connections.py"
MONGO_COMPAT="$BACK_DIR/core/mongo_compat.py"
SERVER_PY="$BACK_DIR/server.py"
mkdir -p "$OUT_DIR" /app/scripts; cd /app || exit 1
for f in "$REPO_FILE" "$API_FILE" "$MONGO_COMPAT" "$SERVER_PY"; do
  [ -f "$f" ] || { echo "ERROR: no existe $f"; exit 1; }; done
echo "FASE 11 - P5-3 AUDITORIA API_CONNECTIONS SQL-FIRST $(date)" | tee "$RAW"
echo "===== 2) DEFS REALES =====" | tee -a "$RAW"
echo "--- repository.py" | tee -a "$RAW"; grep -nE "^(async )?def " "$REPO_FILE" | tee -a "$RAW" || true
echo "--- admin_core_connections.py" | tee -a "$RAW"; grep -nE "^(async )?def " "$API_FILE" | tee -a "$RAW" || true
echo "--- mongo_compat.py" | tee -a "$RAW"; grep -nE "^(async )?def |^class " "$MONGO_COMPAT" | tee -a "$RAW" || true
echo "===== 3) RUTAS / ENDPOINTS =====" | tee -a "$RAW"
grep -nE "@.*\.(get|post|put|delete|patch)\(" "$API_FILE" | tee -a "$RAW" || true
echo "===== 4) USOS VIVOS MONGO/COMPAT =====" | tee -a "$RAW"
grep -nE "get_mongo_db|get_db\(|mongo_compat|MongoClient|client\[|insert_one|update_one|find_one|find\(|delete_one|delete_many|aggregate\(" "$REPO_FILE" "$API_FILE" "$MONGO_COMPAT" | tee -a "$RAW" || true
echo "===== 5) IMPORTADORES/CALLERS VIVOS =====" | tee -a "$RAW"
grep -RnoE "from modules\.api_connections\.repository import .*|import modules\.api_connections\.repository|from api\.admin_core_connections import .*|import api\.admin_core_connections|from core\.mongo_compat import .*|import core\.mongo_compat" "$BACK_DIR" --include="*.py" | grep -v "__pycache__" | grep -v ".bak_" | grep -v "auditorias_p" | tee -a "$RAW" || true
echo "===== 6) REGISTRO server.py =====" | tee -a "$RAW"
grep -nE "admin_core_connections|api_connections" "$SERVER_PY" | tee -a "$RAW" || true
echo "===== 7) COLECCIONES MONGO =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
from pathlib import Path
import re
targets=[Path("/app/backend/modules/api_connections/repository.py"),Path("/app/backend/api/admin_core_connections.py")]
pats=[re.compile(r"get_collection\(['\"]([A-Za-z0-9_\-]+)['\"]\)"),re.compile(r"\bdb\[['\"]([A-Za-z0-9_\-]+)['\"]\]")]
for p in targets:
    txt=p.read_text(errors="ignore"); vals=set()
    for pat in pats: vals.update(pat.findall(txt))
    print(f"{p}:"); [print(f"  - {x}") for x in sorted(vals)] or print("  - (patron simple sin matches)")
PY
echo "===== 9) TABLAS SQL RELACIONADAS (READ-ONLY) =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
import os
from pathlib import Path
ep=Path("/app/backend/.env")
if ep.exists():
    for line in ep.read_text(errors="ignore").splitlines():
        line=line.strip()
        if line and not line.startswith("#") and "=" in line:
            k,v=line.split("=",1); os.environ.setdefault(k.strip(),v.strip())
try:
    import pymssql
except Exception as e:
    print(f"PYMSSQL_NO_DISPONIBLE: {e}"); raise SystemExit(0)
host=os.environ.get("EDARSAHUB_SQL_HOST"); db=os.environ.get("EDARSAHUB_SQL_DATABASE")
user=os.environ.get("EDARSAHUB_SQL_USER"); pwd=os.environ.get("EDARSAHUB_SQL_PASSWORD")
port=int(os.environ.get("EDARSAHUB_SQL_PORT","1433"))
if not all([host,db,user,pwd]): print("ENV_SQL_INCOMPLETO"); raise SystemExit(0)
try:
    conn=pymssql.connect(server=host,user=user,password=pwd,database=db,port=port,login_timeout=5,timeout=10)
    cur=conn.cursor(as_dict=True)
    cur.execute("SELECT TABLE_SCHEMA,TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Servidor%' OR TABLE_NAME LIKE '%Conexion%' OR TABLE_NAME LIKE '%Conector%' ORDER BY TABLE_SCHEMA,TABLE_NAME")
    rows=cur.fetchall() or []
    print("TABLAS_SQL_RELACIONADAS:"); [print(f"  - {r['TABLE_SCHEMA']}.{r['TABLE_NAME']}") for r in rows] or print("  - SIN MATCHES")
    conn.close()
except Exception as e:
    print(f"ERROR_SQL_READONLY: {str(e)[:200]}")
PY
echo "===== 10) RESUMEN =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
from pathlib import Path
import re
repo=Path("/app/backend/modules/api_connections/repository.py").read_text(errors="ignore")
api=Path("/app/backend/api/admin_core_connections.py").read_text(errors="ignore")
c=lambda p,t: len(re.findall(p,t,flags=re.M))
print("  repo_defs:",c(r"^(?:async\s+)?def ",repo))
print("  api_defs:",c(r"^(?:async\s+)?def ",api))
print("  repo_mongo_ops:",c(r"insert_one|update_one|find_one|find\(|delete_one|aggregate\(",repo))
print("  api_mongo_refs:",c(r"get_mongo_db|mongo_compat",api))
print("  api_routes:",c(r"@.*\.(?:get|post|put|delete|patch)\(",api))
PY
echo "RAW_REPORT=$RAW"; echo "OK - FASE 11 auditoria lista"
