from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from core.security import get_current_user
from modules.catalogos_workflow_sql.repository import CatalogosWorkflowSQLRepository

router = APIRouter(prefix="/api", tags=["Catalogos Workflow Compat"])
repo = CatalogosWorkflowSQLRepository()

# =========================================================
# CATALOGOS / PERMISOS
# =========================================================

@router.get("/sistema/catalogos-disponibles")
async def compat_get_catalogos_disponibles(current_user: Dict = Depends(get_current_user)):
    return repo.get_catalogos_disponibles()

@router.put("/sistema/catalogos/{catalogo_id}/niveles")
async def compat_put_catalogo_niveles(catalogo_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    repo.upsert_niveles_catalogo(catalogo_id, body, current_user)
    return {"ok": True, "message": "Niveles guardados en SQL (compat)"}

@router.get("/sistema/catalogos/permisos/{user_id}")
async def compat_get_permisos_catalogo(user_id: int, current_user: Dict = Depends(get_current_user)):
    return repo.get_permisos_catalogo_usuario(user_id)

@router.get("/sistema/mis-permisos-catalogos")
async def compat_get_mis_permisos_catalogos(current_user: Dict = Depends(get_current_user)):
    # Usar UsuarioID (INT) en lugar de id (UUID)
    user_id = current_user.get("UsuarioID") or current_user.get("_sql_usuario_id") or current_user.get("id")
    return repo.get_mis_permisos_catalogos(user_id)

@router.post("/sistema/permisos-catalogos")
async def compat_post_permisos_catalogo(body: Dict, current_user: Dict = Depends(get_current_user)):
    repo.upsert_permisos_catalogo(body, current_user)
    return {"ok": True, "message": "Permisos guardados en SQL (compat)"}

@router.get("/sistema/usuarios-asignables")
async def compat_get_usuarios_asignables(current_user: Dict = Depends(get_current_user)):
    return repo.listar_usuarios_asignables()

# =========================================================
# SOLICITUDES
# =========================================================

@router.get("/sistema/catalogos/solicitudes")
async def compat_get_solicitudes_catalogo(current_user: Dict = Depends(get_current_user)):
    return repo.listar_solicitudes_catalogo()

@router.get("/sistema/solicitudes/{solicitud_id}")
async def compat_get_solicitud(solicitud_id: int, current_user: Dict = Depends(get_current_user)):
    row = repo.get_solicitud_catalogo(solicitud_id)
    if not row:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return row

@router.get("/sistema/solicitudes/{solicitud_id}/historial")
async def compat_get_historial_solicitud(solicitud_id: int, current_user: Dict = Depends(get_current_user)):
    return repo.get_historial_solicitud_catalogo(solicitud_id)

@router.post("/sistema/solicitudes")
async def compat_post_solicitud_catalogo(body: Dict, current_user: Dict = Depends(get_current_user)):
    solicitud_id = repo.crear_solicitud_catalogo(body, current_user)
    return {"ok": True, "message": "Solicitud creada en SQL (compat)", "solicitud_id": solicitud_id}

@router.post("/sistema/solicitudes/{solicitud_id}/aprobar")
async def compat_aprobar_solicitud(solicitud_id: int, body: Dict, current_user: Dict = Depends(get_current_user)):
    updated = repo.aprobar_solicitud(solicitud_id, body, current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return {"ok": True, "message": "Solicitud aprobada en SQL (compat)"}

@router.post("/sistema/solicitudes/{solicitud_id}/rechazar")
async def compat_rechazar_solicitud(solicitud_id: int, body: Dict, current_user: Dict = Depends(get_current_user)):
    updated = repo.rechazar_solicitud(solicitud_id, body, current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return {"ok": True, "message": "Solicitud rechazada en SQL (compat)"}

@router.put("/sistema/solicitudes/{solicitud_id}/corregir")
async def compat_corregir_solicitud(solicitud_id: int, body: Dict, current_user: Dict = Depends(get_current_user)):
    updated = repo.corregir_solicitud(solicitud_id, body, current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return {"ok": True, "message": "Solicitud corregida en SQL (compat)"}

# =========================================================
# TAREAS
# =========================================================

@router.get("/sistema/mis-tareas")
async def compat_get_mis_tareas(current_user: Dict = Depends(get_current_user)):
    # Usar UsuarioID (INT) en lugar de id (UUID)
    user_id = current_user.get("UsuarioID") or current_user.get("_sql_usuario_id") or current_user.get("id")
    return repo.listar_mis_tareas(user_id)

@router.get("/sistema/tareas")
async def compat_get_tareas(current_user: Dict = Depends(get_current_user)):
    return repo.listar_tareas()

@router.post("/sistema/tareas")
async def compat_post_tarea(body: Dict, current_user: Dict = Depends(get_current_user)):
    repo.crear_tarea(body, current_user)
    return {"ok": True, "message": "Tarea creada en SQL (compat)"}
