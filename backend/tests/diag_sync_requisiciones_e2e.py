"""E2E: sync_requisiciones POS -> Compras_Requisiciones_Sync (SR + MPRO)."""
import os, sys
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
from core.sql_first.db import get_sql_connection
from core.secret_manager import decrypt_secret
from modules.compras.sync_service import sync_requisiciones_from_server, obtener_requisiciones_sync
from core.scheduler.jobs.sync_compras_job import _execute_sql_with_timeout

conn=get_sql_connection(); cur=conn.cursor()
cur.execute("""
  SELECT TOP 1 s.id,s.nombre,s.host,s.port,s.database_name,s.username,s.password_encrypted,s.system_type,
         u.id uid,u.codigo uc,u.nombre un
  FROM Servidores_Conexiones s JOIN Unidades_Negocio u ON u.server_id=CAST(s.id AS NVARCHAR(36))
  WHERE u.codigo='ESTELAR'
""")
c=[d[0] for d in cur.description]; estelar=dict(zip(c,cur.fetchone()))
cur.execute("""
  SELECT TOP 1 s.id,s.nombre,s.host,s.port,s.database_name,s.username,s.password_encrypted,s.system_type,
         u.id uid,u.codigo uc,u.nombre un
  FROM Servidores_Conexiones s JOIN Unidades_Negocio u ON u.server_id=CAST(s.id AS NVARCHAR(36))
  WHERE u.codigo='ORIGEN'
""")
c=[d[0] for d in cur.description]; r2=cur.fetchone()
mpro=dict(zip(c,r2)) if r2 else None

def run(r):
    si={'id':str(r['id']),'host':r['host'],'port':int(r['port'] or 1433),'database':r['database_name'],
        'username':r['username'],'password':decrypt_secret(r['password_encrypted'] or ''),'system_type':r['system_type']}
    ui={'id':str(r['uid']),'codigo':r['uc'],'nombre':r['un']}
    print(f"\n>>> {r['nombre']} ({r['uc']}) [{r['system_type']}]")
    res=sync_requisiciones_from_server(si, ui, _execute_sql_with_timeout)
    print("   resultado:", res)
    return str(r['id'])

cc=conn.cursor(); cc.execute("SELECT COUNT(*) FROM Compras_Requisiciones_Sync WHERE sync_status='ACTIVE'")
print("Requisiciones_Sync ACTIVE antes:", cc.fetchone()[0])
sid1=run(estelar)
sid2=run(mpro) if mpro else None
cc=conn.cursor(); cc.execute("SELECT COUNT(*) FROM Compras_Requisiciones_Sync WHERE sync_status='ACTIVE'")
print("\nRequisiciones_Sync ACTIVE despues:", cc.fetchone()[0])

print("\n-- Lectura NO-LIVE (obtener_requisiciones_sync) --")
for sid,nm in [(sid1,'ESTELAR'),(sid2,'ORIGEN')]:
    if not sid: continue
    rows=obtener_requisiciones_sync(server_id=sid, limit=5)
    print(f"  {nm}: {len(rows)} req. ej:", rows[0] if rows else None)
conn.close()
