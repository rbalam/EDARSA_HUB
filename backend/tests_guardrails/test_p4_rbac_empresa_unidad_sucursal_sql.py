import sys
sys.path.insert(0, "/app/backend")

from core.sql_first.db import get_sql_connection

required_tables = [
    "RBAC_Roles",
    "RBAC_Permisos",
    "RBAC_RolesPermisos",
    "RBAC_UsuariosRoles",
    "RBAC_UsuariosEmpresas",
    "RBAC_UsuariosUnidadesNegocio",
    "RBAC_UsuariosSucursales",
    "RBAC_AuditLog",
]

conn = get_sql_connection()
cur = conn.cursor()

missing = []

for table in required_tables:
    cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME=%s", (table,))
    if cur.fetchone()[0] == 0:
        missing.append(table)

if missing:
    print("FAIL tablas RBAC faltantes:", missing)
    sys.exit(1)

cur.execute("SELECT COUNT(*) FROM dbo.RBAC_Roles WHERE Activo=1")
roles = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM dbo.RBAC_Permisos WHERE Activo=1")
permisos = cur.fetchone()[0]

conn.close()

if roles < 5 or permisos < 5:
    print("FAIL RBAC seed insuficiente", roles, permisos)
    sys.exit(1)

print("PASS RBAC SQL empresa/unidad/sucursal base listo")
print(f"  Roles: {roles}, Permisos: {permisos}")
