"""Introspección de esquemas reales POS para corregir queries de sync."""
import os, sys
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
from core.sql_first.db import get_sql_connection
from core.db import execute_sql_query
from core.secret_manager import decrypt_secret

conn = get_sql_connection(); cur = conn.cursor()
cur.execute("""SELECT nombre, host, port, database_name, username, password_encrypted, system_type
    FROM Servidores_Conexiones WHERE activo=1 AND tipo_conexion='DATA_SOURCE'
      AND nombre IN ('LA ESTELAR','ManagmentPro','MPRO TABLAJERIA')""")
cols=[d[0] for d in cur.description]; rows=[dict(zip(cols,r)) for r in cur.fetchall()]; conn.close()

def cols_of(host,port,db,user,pwd,table):
    q=f"""SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
          WHERE TABLE_NAME='{table}' ORDER BY ORDINAL_POSITION"""
    return execute_sql_query(host,port,db,user,pwd,q,timeout_seconds=20,context="jobs")

def tables_like(host,port,db,user,pwd,pat):
    q=f"""SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
          WHERE TABLE_TYPE='BASE TABLE' AND TABLE_NAME LIKE '{pat}' ORDER BY TABLE_NAME"""
    return execute_sql_query(host,port,db,user,pwd,q,timeout_seconds=20,context="jobs")

for r in rows:
    nombre=r["nombre"]; host=r["host"]; port=int(r["port"] or 1433)
    db=r["database_name"]; user=r["username"]; pwd=decrypt_secret(r["password_encrypted"] or "")
    st=(r["system_type"] or "").upper()
    print("="*70); print(f"{nombre} ({st}) db={db}")
    if "MPRO" in st or "MANAGEMENT" in st:
        for t in ["Movimiento","Almacen"]:
            c=cols_of(host,port,db,user,pwd,t)
            print(f"  Tabla {t}: {[x['COLUMN_NAME'] for x in c] if c else 'NO EXISTE'}")
        print("  Tablas *movim*/*almac*:", [x['TABLE_NAME'] for x in (tables_like(host,port,db,user,pwd,'%ovim%') or [])] + [x['TABLE_NAME'] for x in (tables_like(host,port,db,user,pwd,'%lmac%') or [])])
    else:
        for t in ["movtosalmacen","almacen"]:
            c=cols_of(host,port,db,user,pwd,t)
            print(f"  Tabla {t}: {[x['COLUMN_NAME'] for x in c] if c else 'NO EXISTE'}")
