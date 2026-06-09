"""Prueba E2E: sync_almacenes desde POS (preview) -> Inventario_Almacenes (EDARSAHUB)."""
import os, sys
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
from core.sql_first.db import get_sql_connection
from core.secret_manager import decrypt_secret
from modules.compras.sync_service import sync_almacenes_from_server
from core.scheduler.jobs.sync_compras_job import _execute_sql_with_timeout

conn=get_sql_connection(); cur=conn.cursor()
cur.execute("""
  SELECT s.id, s.nombre, s.host, s.port, s.database_name, s.username, s.password_encrypted, s.system_type,
         u.id AS unidad_id, u.codigo AS unidad_codigo, u.nombre AS unidad_nombre
  FROM Servidores_Conexiones s
  JOIN Unidades_Negocio u ON u.server_id = CAST(s.id AS NVARCHAR(36))
  WHERE s.activo=1 AND s.tipo_conexion='DATA_SOURCE' AND u.codigo IN ('130MID','ESTELAR')
""")
cols=[d[0] for d in cur.description]; rows=[dict(zip(cols,r)) for r in cur.fetchall()]

def count_alm(empresa=None):
    c=conn.cursor()
    if empresa:
        c.execute("SELECT COUNT(*) FROM Inventario_Almacenes WHERE EmpresaID=%s",(empresa,))
    else:
        c.execute("SELECT COUNT(*) FROM Inventario_Almacenes")
    return c.fetchone()[0]

print("Inventario_Almacenes TOTAL antes:", count_alm())
for r in rows:
    si={'id':str(r['id']),'host':r['host'],'port':int(r['port'] or 1433),'database':r['database_name'],
        'username':r['username'],'password':decrypt_secret(r['password_encrypted'] or ''),
        'system_type':r['system_type']}
    ui={'id':str(r['unidad_id']),'codigo':r['unidad_codigo'],'nombre':r['unidad_nombre']}
    print(f"\n>>> {r['nombre']} ({r['unidad_codigo']})")
    res=sync_almacenes_from_server(si, ui, _execute_sql_with_timeout)
    print("   resultado:", res)
print("\nInventario_Almacenes TOTAL despues:", count_alm())
conn.close()
