"""Verifica tablas puente y resolución empresa/sucursal para unidades que conectan."""
import os, sys
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
from core.sql_first.db import get_sql_connection
from core.inventarios.resolver_canonico import resolver_empresa_id, resolver_sucursal_id, _tabla_existe
from core.server_registry import get_server_by_unidad_codigo

conn=get_sql_connection(); cur=conn.cursor()
print("Tabla Producto_MapeoOrigen existe?:", _tabla_existe("Producto_MapeoOrigen"))
print("Tabla Inventario_ConceptoMapeoOrigen existe?:", _tabla_existe("Inventario_ConceptoMapeoOrigen"))
print("Tabla Inventario_TipoMovimiento existe?:", _tabla_existe("Inventario_TipoMovimiento"))

# Servidores activos DATA_SOURCE -> ¿tienen unidad mapeada?
cur.execute("""
  SELECT s.id, s.nombre, s.system_type, u.codigo AS unidad_codigo
  FROM Servidores_Conexiones s
  LEFT JOIN Unidades_Negocio u ON u.server_id = CAST(s.id AS NVARCHAR(36))
  WHERE s.activo=1 AND s.tipo_conexion='DATA_SOURCE'
""")
cols=[d[0] for d in cur.description]; rows=[dict(zip(cols,r)) for r in cur.fetchall()]
print("\n-- Mapeo servidor -> unidad / resolución empresa+sucursal --")
for r in rows:
    uc=r["unidad_codigo"]
    emp = resolver_empresa_id(uc) if uc else None
    suc = resolver_sucursal_id(str(r["id"]), None)
    print(f"  {r['nombre']!r} sys={r['system_type']} unidad={uc!r} "
          f"empresa={'OK:'+str(emp.canonical_id) if emp and emp.resuelto else (emp.motivo if emp else 'SIN_UNIDAD')} "
          f"sucursal={'OK:'+str(suc.canonical_id) if suc.resuelto else suc.motivo}")
conn.close()
