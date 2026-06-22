from pathlib import Path
from datetime import datetime
import re

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 1) FRONTEND: Usuarios.js debe guardar roles en /admin-sql/roles, no en /roles legacy
f = Path("/app/frontend/src/pages/Usuarios.js")
txt = f.read_text()
f.write_text(txt)
f.rename(f.with_suffix(f".js.bak_roles_permisos_{stamp}"))
f = Path("/app/frontend/src/pages/Usuarios.js.bak_roles_permisos_" + stamp)
txt = f.read_text()

txt = txt.replace("api.put(`/roles/${editingRole.id}`, roleFormData)", "api.put(`/admin-sql/roles/${editingRole.id}`, roleFormData)")
txt = txt.replace("api.post('/roles', roleFormData)", "api.post('/admin-sql/roles', roleFormData)")
txt = txt.replace("api.delete(`/roles/${roleId}`)", "api.delete(`/admin-sql/roles/${roleId}`)")

Path("/app/frontend/src/pages/Usuarios.js").write_text(txt)

# 2) BACKEND: agregar CRUD SQL real en admin_sql/routes.py
p = Path("/app/backend/modules/admin_sql/routes.py")
src = p.read_text()
p.rename(p.with_suffix(f".py.bak_roles_permisos_{stamp}"))
src = Path("/app/backend/modules/admin_sql/routes.py.bak_roles_permisos_" + stamp).read_text()

insert = r'''

def _normalizar_modulos_permisos(permisos):
    """Recibe lista de ModuloID desde frontend y devuelve enteros válidos."""
    out = []
    for x in permisos or []:
        try:
            out.append(int(str(x)))
        except Exception:
            continue
    return sorted(set(out))


def _get_accion_ver_id():
    rows = execute_query("""
        SELECT TOP 1 AccionID
        FROM dbo.Usuario_Acciones
        WHERE CodigoAccion = 'VER' AND Activo = 1
    """)
    if not rows:
        raise HTTPException(status_code=500, detail="No existe acción VER en Usuario_Acciones")
    return rows[0]["AccionID"]


def _guardar_permisos_modulos_rol(rol_id: int, permisos):
    """
    Guarda permisos de módulo desde pantalla actual.
    La pantalla actual manda módulos, no matriz acción x módulo.
    Por compatibilidad: módulo seleccionado = permiso VER activo.
    """
    modulos = _normalizar_modulos_permisos(permisos)
    accion_ver_id = _get_accion_ver_id()

    execute_non_query("""
        UPDATE dbo.Usuario_PermisosRolModulo
        SET Activo = 0,
            Permitido = 0,
            FechaModificacion = GETDATE(),
            ModifiedBy = 'admin-sql.roles'
        WHERE RolID = %s
    """, (rol_id,))

    for modulo_id in modulos:
        existe_mod = execute_query("""
            SELECT TOP 1 ModuloID
            FROM dbo.Usuario_Modulos
            WHERE ModuloID = %s AND Activo = 1
        """, (modulo_id,))
        if not existe_mod:
            continue

        existe = execute_query("""
            SELECT TOP 1 PermisoRolModuloID
            FROM dbo.Usuario_PermisosRolModulo
            WHERE RolID = %s AND ModuloID = %s AND AccionID = %s
        """, (rol_id, modulo_id, accion_ver_id))

        if existe:
            execute_non_query("""
                UPDATE dbo.Usuario_PermisosRolModulo
                SET Permitido = 1,
                    Activo = 1,
                    FechaModificacion = GETDATE(),
                    ModifiedBy = 'admin-sql.roles'
                WHERE PermisoRolModuloID = %s
            """, (existe[0]["PermisoRolModuloID"],))
        else:
            execute_non_query("""
                INSERT INTO dbo.Usuario_PermisosRolModulo
                (RolID, ModuloID, AccionID, Permitido, RestriccionPropietario,
                 RestriccionSucursal, RequiereAutorizacion, Activo, FechaAlta, CreatedBy)
                VALUES (%s, %s, %s, 1, 0, 0, 0, 1, GETDATE(), 'admin-sql.roles')
            """, (rol_id, modulo_id, accion_ver_id))


@router.post("/roles")
async def create_role(role_data: dict, current_user: dict = Depends(get_current_user)):
    require_admin(current_user)

    nombre = (role_data.get("nombre") or "").strip()
    descripcion = (role_data.get("descripcion") or "").strip()
    permisos = role_data.get("permisos") or []

    if not nombre:
        raise HTTPException(status_code=400, detail="Nombre del rol requerido")

    dup = execute_query("""
        SELECT TOP 1 RolID
        FROM dbo.Usuario_Roles
        WHERE UPPER(CodigoRol) = UPPER(%s) OR UPPER(NombreRol) = UPPER(%s)
    """, (nombre, nombre))
    if dup:
        raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")

    codigo = re.sub(r'[^A-Z0-9_]+', '_', nombre.upper()).strip('_') or nombre.upper()

    execute_non_query("""
        INSERT INTO dbo.Usuario_Roles
        (CodigoRol, NombreRol, Descripcion, EsRolSistema, Activo, FechaAlta, NivelJerarquia)
        VALUES (%s, %s, %s, 0, 1, GETDATE(), 0)
    """, (codigo, nombre, descripcion))

    row = execute_query("SELECT TOP 1 RolID FROM dbo.Usuario_Roles WHERE CodigoRol = %s ORDER BY RolID DESC", (codigo,))
    rol_id = int(row[0]["RolID"])

    _guardar_permisos_modulos_rol(rol_id, permisos)

    return {"message": "Rol creado", "id": str(rol_id)}


@router.put("/roles/{role_id}")
async def update_role(role_id: str, role_data: dict, current_user: dict = Depends(get_current_user)):
    require_admin(current_user)

    row = execute_query("""
        SELECT TOP 1 RolID, EsRolSistema
        FROM dbo.Usuario_Roles
        WHERE RolID = TRY_CONVERT(INT, %s) OR CodigoRol = %s
    """, (role_id, role_id))
    if not row:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    rol_id = int(row[0]["RolID"])
    es_sistema = bool(row[0]["EsRolSistema"])

    descripcion = role_data.get("descripcion")
    nombre = role_data.get("nombre")

    if descripcion is not None:
        execute_non_query("""
            UPDATE dbo.Usuario_Roles
            SET Descripcion = %s,
                FechaModificacion = GETDATE()
            WHERE RolID = %s
        """, (descripcion, rol_id))

    if nombre is not None and not es_sistema:
        nombre = nombre.strip()
        if nombre:
            execute_non_query("""
                UPDATE dbo.Usuario_Roles
                SET NombreRol = %s,
                    FechaModificacion = GETDATE()
                WHERE RolID = %s
            """, (nombre, rol_id))

    if "permisos" in role_data:
        _guardar_permisos_modulos_rol(rol_id, role_data.get("permisos") or [])

    return {"message": "Rol actualizado", "id": str(rol_id)}


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str, current_user: dict = Depends(get_current_user)):
    require_admin(current_user)

    row = execute_query("""
        SELECT TOP 1 RolID, EsRolSistema
        FROM dbo.Usuario_Roles
        WHERE RolID = TRY_CONVERT(INT, %s) OR CodigoRol = %s
    """, (role_id, role_id))
    if not row:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    if bool(row[0]["EsRolSistema"]):
        raise HTTPException(status_code=400, detail="No se pueden eliminar roles de sistema")

    rol_id = int(row[0]["RolID"])

    execute_non_query("""
        UPDATE dbo.Usuario_Roles
        SET Activo = 0,
            FechaModificacion = GETDATE()
        WHERE RolID = %s
    """, (rol_id,))

    return {"message": "Rol eliminado", "id": str(rol_id)}
'''

# insertar antes de @router.get("/servers") para que quede junto a roles
marker = "\n@router.get(\"/servers\")"
if "@router.put(\"/roles/{role_id}\")" not in src:
    src = src.replace(marker, insert + marker)

# asegurar import re y HTTPException
if "import re" not in src:
    src = src.replace("from typing import", "import re\nfrom typing import", 1)
if "HTTPException" not in src.splitlines()[0:80].__str__():
    src = src.replace("from fastapi import", "from fastapi import HTTPException,", 1)

Path("/app/backend/modules/admin_sql/routes.py").write_text(src)

print("PATCH_OK")
