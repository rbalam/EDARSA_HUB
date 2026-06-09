"""Test del path REAL de sync: execute_sql_query (pool, context=jobs) + queries de origen."""
import os, sys
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

from core.sql_first.db import get_sql_connection
from core.db import execute_sql_query
from core.secret_manager import decrypt_secret

conn = get_sql_connection()
cur = conn.cursor()
cur.execute("""
    SELECT nombre, host, port, database_name, username, password_encrypted, system_type
    FROM Servidores_Conexiones
    WHERE activo=1 AND tipo_conexion='DATA_SOURCE' AND host IS NOT NULL AND host!=''
      AND nombre IN ('LA ESTELAR','130° MERIDA','MPRO TABLAJERIA','ManagmentPro')
""")
cols=[d[0] for d in cur.description]
rows=[dict(zip(cols,r)) for r in cur.fetchall()]
conn.close()

for r in rows:
    nombre=r["nombre"]; host=r["host"]; port=int(r["port"] or 1433)
    db=r["database_name"]; user=r["username"]; st=(r["system_type"] or "").upper()
    pwd=decrypt_secret(r["password_encrypted"] or "")
    print("="*60); print(f"{nombre} ({st}) {host}:{port}/{db}")
    if "MPRO" in st or "MANAGEMENT" in st:
        q_alm="SELECT TOP 3 Al_Cve_Almacen, Al_Descripcion FROM Almacen"
        q_mov="SELECT COUNT(*) AS n FROM Movimiento WHERE Mo_Fecha >= DATEADD(DAY,-30,GETDATE())"
    else:
        q_alm="SELECT TOP 3 idalmacen, nombre FROM almacen"
        q_mov="SELECT COUNT(*) AS n FROM movtosalmacen WHERE fecha >= DATEADD(DAY,-30,GETDATE()) AND cancelado=0"
    for label,q in [("ALMACENES",q_alm),("MOVIMIENTOS_30d",q_mov)]:
        res=execute_sql_query(host,port,db,user,pwd,q,timeout_seconds=20,context="jobs")
        print(f"  {label}: {len(res) if res is not None else 'None'} -> {res[:3] if res else res}")
