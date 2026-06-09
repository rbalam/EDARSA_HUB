"""Prueba E2E: sync_movimientos_canonico POS -> Inventario_Movimientos(+Detalle)."""
import os, sys
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
from core.sql_first.db import get_sql_connection
from core.secret_manager import decrypt_secret
from core.inventarios.sync_movimientos_canonico import sync_movimientos_canonico
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

def counts():
    c=conn.cursor()
    c.execute("SELECT COUNT(*) FROM Inventario_Movimientos"); h=c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM Inventario_MovimientosDetalle"); d=c.fetchone()[0]
    return h,d

print("Movimientos/Detalle antes:", counts())
for r in rows:
    si={'id':str(r['id']),'host':r['host'],'port':int(r['port'] or 1433),'database':r['database_name'],
        'username':r['username'],'password':decrypt_secret(r['password_encrypted'] or ''),
        'system_type':r['system_type']}
    ui={'id':str(r['unidad_id']),'codigo':r['unidad_codigo'],'nombre':r['unidad_nombre']}
    print(f"\n>>> {r['nombre']} ({r['unidad_codigo']})")
    res=sync_movimientos_canonico(si, ui, _execute_sql_with_timeout, dias_atras=30)
    print("   resultado:", res)
print("\nMovimientos/Detalle despues:", counts())
conn.close()
