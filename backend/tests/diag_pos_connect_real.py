"""Test de conexión SQL REAL a cada POS DATA_SOURCE (captura error exacto)."""
import os, sys, time
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

from core.sql_first.db import get_sql_connection
from core.db import parse_sql_server_host
from core.secret_manager import decrypt_secret

conn = get_sql_connection()
cur = conn.cursor()
cur.execute("""
    SELECT id, nombre, host, port, database_name, username, password_encrypted, system_type
    FROM Servidores_Conexiones
    WHERE activo = 1 AND tipo_conexion = 'DATA_SOURCE'
      AND host IS NOT NULL AND host != ''
""")
cols = [d[0] for d in cur.description]
rows = [dict(zip(cols, r)) for r in cur.fetchall()]
conn.close()

import pymssql
for r in rows:
    nombre = r["nombre"]
    host = r["host"]; port = int(r["port"] or 1433)
    db = r["database_name"]; user = r["username"]
    try:
        pwd = decrypt_secret(r["password_encrypted"] or "")
    except Exception as e:
        print(f"[{nombre}] DECRYPT_FAIL: {e}"); continue
    hostname, parsed_port, instance = parse_sql_server_host(host, port)
    server = f"{hostname}\\{instance}" if instance else hostname
    t0 = time.time()
    try:
        c = pymssql.connect(server=server, port=parsed_port, user=user, password=pwd,
                            database=db, login_timeout=8, timeout=15, tds_version="7.0")
        cc = c.cursor()
        cc.execute("SELECT 1 AS ok")
        res = cc.fetchone()
        c.close()
        print(f"[{nombre}] ✅ CONNECT OK ({time.time()-t0:.1f}s) server={server!r} port={parsed_port} db={db} -> {res}")
    except Exception as e:
        print(f"[{nombre}] ❌ FAIL ({time.time()-t0:.1f}s) server={server!r} port={parsed_port} db={db} user={user} :: {type(e).__name__}: {str(e)[:200]}")
