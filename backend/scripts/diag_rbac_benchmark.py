"""Diagnóstico RBAC para permisos comercial.benchmark.* / pricing.
Solo lectura. Inspecciona módulos, acciones, permisos por rol y formato.
"""
import os, pymssql

DB = {
    'server': os.getenv('EDARSAHUB_SQL_HOST'),
    'port': int(os.getenv('EDARSAHUB_SQL_PORT', '1433')),
    'database': os.getenv('EDARSAHUB_SQL_DATABASE', 'EDARSAHUB'),
    'user': os.getenv('EDARSAHUB_SQL_USER'),
    'password': os.getenv('EDARSAHUB_SQL_PASSWORD'),
}

conn = pymssql.connect(**DB)
cur = conn.cursor(as_dict=True)

print("=== Usuario_Modulos LIKE 'comercial%' ===")
cur.execute("SELECT ModuloID, CodigoModulo, NombreModulo, Activo FROM Usuario_Modulos WHERE CodigoModulo LIKE 'comercial%' ORDER BY CodigoModulo")
for r in cur.fetchall():
    print(r)

print("\n=== Usuario_Acciones (todas) ===")
cur.execute("SELECT AccionID, CodigoAccion FROM Usuario_Acciones ORDER BY AccionID")
for r in cur.fetchall():
    print(r)

print("\n=== Roles (Usuario_Roles) ===")
cur.execute("SELECT RolID, CodigoRol, NombreRol, NivelJerarquia, Activo FROM Usuario_Roles ORDER BY RolID")
for r in cur.fetchall():
    print(r)

print("\n=== Permisos existentes para modulos comercial.* (PorRolModulo) ===")
cur.execute("""
  SELECT prm.RolID, r.CodigoRol, m.CodigoModulo, a.CodigoAccion, prm.Permitido, prm.Activo
  FROM Usuario_PermisosRolModulo prm
  JOIN Usuario_Modulos m ON prm.ModuloID = m.ModuloID
  JOIN Usuario_Acciones a ON prm.AccionID = a.AccionID
  LEFT JOIN Usuario_Roles r ON prm.RolID = r.RolID
  WHERE m.CodigoModulo LIKE 'comercial%'
  ORDER BY m.CodigoModulo, r.CodigoRol, a.CodigoAccion
""")
rows = cur.fetchall()
print(f"total: {len(rows)}")
for r in rows[:80]:
    print(r)

conn.close()
