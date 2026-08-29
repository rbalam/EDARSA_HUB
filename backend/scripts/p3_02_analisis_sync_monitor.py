import os
from pathlib import Path
import pymssql

def load_env():
    env = Path("/app/backend/.env")
    if env.exists():
        for line in env.read_text(errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

cn = pymssql.connect(
    server=os.getenv("EDARSAHUB_SQL_HOST"),
    port=int(os.getenv("EDARSAHUB_SQL_PORT", "1433")),
    user=os.getenv("EDARSAHUB_SQL_USER"),
    password=os.getenv("EDARSAHUB_SQL_PASSWORD"),
    database=os.getenv("EDARSAHUB_SQL_DATABASE"),
    login_timeout=10,
    timeout=30
)
cur = cn.cursor(as_dict=True)

tables = [
    "Compras_Sync_Log",
    "Compras_Sync_Checkpoint",
    "Sync_Logs",
    "Sync_Log",
    "Scheduler_Jobs",
    "Scheduler_Ejecuciones",
    "Servidores_Conexiones",
    "Comercial_SyncLog_v2",
]

for t in tables:
    print(f"\n{'='*80}\n{t}\n{'='*80}")
    cur.execute("""
        SELECT COUNT(*) AS existe FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME=%s
    """, (t,))
    if not cur.fetchone()["existe"]:
        print("NO EXISTE")
        continue
    
    cur.execute(f"SELECT COUNT(*) AS total FROM {t}")
    print("Registros:", cur.fetchone()["total"])
    
    cur.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME=%s
        ORDER BY ORDINAL_POSITION
    """, (t,))
    print("Columnas:", [r["COLUMN_NAME"] for r in cur.fetchall()])
    
    try:
        cur.execute(f"SELECT TOP 3 * FROM {t} ORDER BY 1 DESC")
        for r in cur.fetchall():
            print(r)
    except Exception:
        pass

cn.close()
