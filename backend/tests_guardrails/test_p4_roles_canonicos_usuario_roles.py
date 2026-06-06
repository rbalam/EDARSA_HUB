from pathlib import Path
import sys

svc = Path("core/rbac_sql/service.py").read_text(errors="ignore")

required = [
    "Usuario_Roles",
    "Usuario_RolesAsignacion",
    "Usuario_EmpresasAsignacion",
    "Usuario_SucursalesAsignacion",
    "Usuario_ServidoresAsignacion",
]

for token in required:
    if token not in svc:
        print("FAIL falta tabla canónica:", token)
        sys.exit(1)

for forbidden in [
    "FROM dbo.Sys_Roles",
    "JOIN dbo.Sys_Roles",
    "FROM dbo.RBAC_",
    "JOIN dbo.RBAC_",
]:
    if forbidden in svc:
        print("FAIL usa tabla duplicada/no canónica:", forbidden)
        sys.exit(1)

print("PASS roles canónicos usan Usuario_Roles y asignaciones Usuario_*")
