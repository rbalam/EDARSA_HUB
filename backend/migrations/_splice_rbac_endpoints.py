"""Splicer puntual: reescribe 5 endpoints RBAC piloto de server.py a SQL-First.
Reemplaza el texto entre anclas únicas (sin tocar los modelos Pydantic intermedios)."""
import io

PATH = "/app/backend/server.py"

BLOCKS = [
    # (start_anchor, end_anchor, new_text)
    (
        '@api_router.post("/admin/permisos/asignar")\n',
        'class RolAsignacionRequest(BaseModel):\n',
        '''@api_router.post("/admin/permisos/asignar")
async def admin_asignar_permiso(
    request: PermisoAsignacionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """RBAC piloto SQL-First: asigna/retira un permiso directo (sec_permisos)."""
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede administrar permisos")
    return rbac_pilot_service.toggle_asignacion(
        request.usuario_email, "PERMISO", request.permiso, request.accion
    )


''',
    ),
    (
        '@api_router.post("/admin/roles/asignar")\n',
        '@api_router.get("/admin/bitacora")\n',
        '''@api_router.post("/admin/roles/asignar")
async def admin_asignar_rol(
    request: RolAsignacionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """RBAC piloto SQL-First: asigna/retira un rol (sec_roles)."""
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede administrar roles")
    return rbac_pilot_service.toggle_asignacion(
        request.usuario_email, "ROL", request.rol, request.accion
    )


''',
    ),
    (
        '@api_router.get("/admin/perfiles")\n',
        'class AsignarPerfilRequest(BaseModel):\n',
        '''@api_router.get("/admin/perfiles")
async def get_perfiles_disponibles(current_user: Dict = Depends(get_current_user)):
    """RBAC piloto SQL-First: lista los perfiles predefinidos disponibles."""
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede ver perfiles")
    return {"perfiles": rbac_pilot_service.get_perfiles_catalogo()}


''',
    ),
    (
        '@api_router.post("/admin/perfiles/asignar")\n',
        'class RetirarPerfilRequest(BaseModel):\n',
        '''@api_router.post("/admin/perfiles/asignar")
async def asignar_perfil_usuario(
    request: AsignarPerfilRequest,
    current_user: Dict = Depends(get_current_user)
):
    """RBAC piloto SQL-First: asigna un perfil (sobrescribe sec_roles con los del perfil)."""
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede asignar perfiles")
    if request.perfil not in PERFILES_FASE_13_WHITELIST:
        raise HTTPException(status_code=400, detail=f"Perfil '{request.perfil}' no esta en whitelist FASE 13")
    return rbac_pilot_service.asignar_perfil(
        request.usuario_email, request.perfil, current_user.get('email', 'sistema')
    )


''',
    ),
    (
        '@api_router.post("/admin/perfiles/retirar")\n',
        '@api_router.get("/admin/alcance/empresas")\n',
        '''@api_router.post("/admin/perfiles/retirar")
async def retirar_perfil_usuario(
    request: RetirarPerfilRequest,
    current_user: Dict = Depends(get_current_user)
):
    """RBAC piloto SQL-First: retira el perfil de un usuario (limpia sec_perfil y sec_roles)."""
    if current_user.get('role') != 'SuperAdministrador':
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede retirar perfiles")
    return rbac_pilot_service.retirar_perfil(
        request.usuario_email, current_user.get('email', 'sistema')
    )


''',
    ),
]

with io.open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

for start_anchor, end_anchor, new_text in BLOCKS:
    s = content.find(start_anchor)
    if s == -1:
        raise SystemExit(f"START anchor no encontrado: {start_anchor!r}")
    e = content.find(end_anchor, s + len(start_anchor))
    if e == -1:
        raise SystemExit(f"END anchor no encontrado tras start: {end_anchor!r}")
    content = content[:s] + new_text + content[e:]
    print(f"OK reemplazado bloque: {start_anchor.strip()}")

with io.open(PATH, "w", encoding="utf-8") as f:
    f.write(content)
print("server.py reescrito.")
