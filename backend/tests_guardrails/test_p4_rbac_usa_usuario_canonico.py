from pathlib import Path
import sys

svc = Path("core/rbac_sql/service.py").read_text(errors="ignore")

required = [
    "Usuario_RolesAsignacion",
    "Usuario_EmpresasAsignacion",
    "Usuario_SucursalesAsignacion",
]

for token in required:
    if token not in svc:
        print("FAIL falta uso canónico:", token)
        sys.exit(1)

for forbidden in [
    "FROM dbo.RBAC_UsuariosRoles",
    "FROM dbo.RBAC_UsuariosEmpresas",
    "FROM dbo.RBAC_UsuariosUnidadesNegocio",
    "FROM dbo.RBAC_UsuariosSucursales",
]:
    if forbidden in svc:
        print("FAIL usa tabla RBAC duplicada:", forbidden)
        sys.exit(1)

print("PASS RBAC runtime usa Usuario_* canónico")
