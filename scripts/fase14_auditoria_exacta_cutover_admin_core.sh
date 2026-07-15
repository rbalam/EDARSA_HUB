#!/usr/bin/env bash
set -euo pipefail

: "${EDARSAHUB_TEST_AUTH_EMAIL:?Variable requerida}"
: "${EDARSAHUB_TEST_AUTH_PASSWORD:?Variable requerida}"
export EDARSAHUB_TEST_AUTH_EMAIL EDARSAHUB_TEST_AUTH_PASSWORD

LOGIN_PAYLOAD="$(python3 -c 'import json,os; print(json.dumps({
    "email": os.environ["EDARSAHUB_TEST_AUTH_EMAIL"],
    "password": os.environ["EDARSAHUB_TEST_AUTH_PASSWORD"],
}))')"
OUT_DIR="/app/auditorias_p5"; TS="$(date +%Y%m%d_%H%M%S)"
RAW="$OUT_DIR/FASE14_AUDITORIA_EXACTA_CUTOVER_ADMIN_CORE_${TS}.txt"
JSON_DIR="$OUT_DIR/FASE14_ADMIN_CORE_${TS}"
mkdir -p "$OUT_DIR" "$JSON_DIR" /app/scripts; cd /app || exit 1
echo "FASE 14 - AUDITORIA EXACTA CUTOVER ADMIN CORE $(date)" | tee "$RAW"
echo "===== 1) LOGIN =====" | tee -a "$RAW"
curl -sS --max-time 15 -X POST "http://127.0.0.1:8001/api/auth/login" -H "Content-Type: application/json" \
  -d "$LOGIN_PAYLOAD" -o "$JSON_DIR/login.json" \
  -w "HTTP=%{http_code} t=%{time_total}s\n" | tee -a "$RAW"
TOKEN=$(python3 -c "import json;d=json.load(open('$JSON_DIR/login.json'));print(d.get('token') or d.get('access_token') or '')" 2>/dev/null)
[ -z "$TOKEN" ] && { echo "ERROR: no token" | tee -a "$RAW"; exit 2; }
echo "===== 2) SNAPSHOT LIST =====" | tee -a "$RAW"
curl -sS --max-time 20 "http://127.0.0.1:8001/api/admin/core-connections" -H "Authorization: Bearer $TOKEN" \
  -o "$JSON_DIR/core_connections_list.json" -w "LIST HTTP=%{http_code} t=%{time_total}s\n" | tee -a "$RAW"
JSON_DIR="$JSON_DIR" python3 - <<'PY' | tee -a "$RAW"
import json, os
d=json.load(open(os.environ["JSON_DIR"]+"/core_connections_list.json"))
print("TOP_LEVEL_KEYS=", sorted(d.keys()) if isinstance(d,dict) else type(d).__name__)
items=d.get("data") if isinstance(d,dict) and isinstance(d.get("data"),list) else []
print("ITEM_COUNT=", len(items))
if items:
    print("FIRST_ITEM_KEYS=", sorted(items[0].keys()))
    for k in ("id","server_id","ServerID","ServidorID","name","nombre"):
        if k in items[0]: print(f"FIRST_{k}=", items[0].get(k))
PY
FIRST_ID=$(JSON_DIR="$JSON_DIR" python3 -c "
import json,os
d=json.load(open(os.environ['JSON_DIR']+'/core_connections_list.json'))
items=d.get('data') if isinstance(d,dict) and isinstance(d.get('data'),list) else []
fid=''
if items and isinstance(items[0],dict):
    for k in ('id','server_id','ServerID','ServidorID'):
        v=items[0].get(k)
        if v not in (None,''): fid=str(v); break
print(fid)")
echo "FIRST_ID=$FIRST_ID" | tee -a "$RAW"
if [ -n "$FIRST_ID" ]; then
  echo "===== 3) SNAPSHOT ITEM + TEST =====" | tee -a "$RAW"
  curl -sS --max-time 20 "http://127.0.0.1:8001/api/admin/core-connections/$FIRST_ID" -H "Authorization: Bearer $TOKEN" \
    -o "$JSON_DIR/core_connection_item.json" -w "ITEM HTTP=%{http_code} t=%{time_total}s\n" | tee -a "$RAW"
  curl -sS --max-time 20 -X POST "http://127.0.0.1:8001/api/admin/core-connections/$FIRST_ID/test" -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" -o "$JSON_DIR/core_connection_test.json" -w "TEST HTTP=%{http_code} t=%{time_total}s\n" | tee -a "$RAW"
  JSON_DIR="$JSON_DIR" python3 - <<'PY' | tee -a "$RAW"
import json, os
jd=os.environ["JSON_DIR"]
for label,f in [("ITEM",jd+"/core_connection_item.json"),("TEST",jd+"/core_connection_test.json")]:
    try:
        d=json.load(open(f))
        if isinstance(d,dict):
            print(label,"TOP_LEVEL_KEYS=",sorted(d.keys()))
            if isinstance(d.get("data"),dict): print(label,"DATA_KEYS=",sorted(d["data"].keys()))
        else: print(label,"TYPE=",type(d).__name__)
    except Exception as e: print(label,"PARSE_ERROR=",str(e)[:180])
PY
fi
echo "===== 4) AUDITORIA SQL (READ-ONLY, solo nombres de columnas) =====" | tee -a "$RAW"
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
    print(f"PYMSSQL_NO_DISPONIBLE={e}"); raise SystemExit(0)
host=os.environ.get("EDARSAHUB_SQL_HOST"); db=os.environ.get("EDARSAHUB_SQL_DATABASE")
user=os.environ.get("EDARSAHUB_SQL_USER"); pwd=os.environ.get("EDARSAHUB_SQL_PASSWORD")
port=int(os.environ.get("EDARSAHUB_SQL_PORT","1433"))
try:
    conn=pymssql.connect(server=host,user=user,password=pwd,database=db,port=port,login_timeout=5,timeout=15)
except Exception as e:
    print("SQL_CONNECT_ERROR="+str(e)[:180]); raise SystemExit(0)
cur=conn.cursor(as_dict=True)
for t in ["Servidores_Conexiones","Servidores_Conexiones_Log","ConsultasSQL_Servidores","CRM_Integracion_Conectores"]:
    print(f"\nTABLA=dbo.{t}")
    cur.execute("SELECT COLUMN_NAME,DATA_TYPE,IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",(t,))
    cols=cur.fetchall() or []
    if not cols: print("NO_EXISTE=1"); continue
    for c in cols: print(f"COL={c['COLUMN_NAME']}|TYPE={c['DATA_TYPE']}|NULL={c['IS_NULLABLE']}")
    try:
        cur.execute(f"SELECT TOP 1 * FROM dbo.{t}"); row=cur.fetchone()
        print("SAMPLE_KEYS="+(",".join(row.keys()) if row else "NO_ROWS"))
    except Exception as e: print("SAMPLE_ERROR="+str(e)[:180])
conn.close()
PY
echo "RAW_REPORT=$RAW"; echo "JSON_DIR=$JSON_DIR"; echo "OK - AUDITORIA EXACTA LISTA"
