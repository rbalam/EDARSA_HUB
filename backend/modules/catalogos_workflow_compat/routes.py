from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from core.security import get_current_user
from modules.catalogos_workflow_sql.repository import CatalogosWorkflowSQLRepository

router = APIRouter(prefix="/api", tags=["Catalogos Workflow Compat"])
repo = CatalogosWorkflowSQLRepository()

# =========================================================
# COMPATIBILIDAD LEGACY - CATALOGOS
# Mantiene frontend actual, pero usa SQL
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

@router.post("/sistema/catalogos/permisos")
async def compat_post_permisos_catalogo(body: Dict, current_user: Dict = Depends(get_current_user)):
    repo.upsert_permisos_catalogo(body, current_user)
    return {"ok": True, "message": "Permisos guardados en SQL (compat)"}

# =========================================================
# COMPATIBILIDAD LEGACY - SOLICITUDES
# =========================================================

@router.get("/sistema/catalogos/solicitudes")
async def compat_get_solicitudes_catalogo(current_user: Dict = Depends(get_current_user)):
    return repo.listar_solicitudes_catalogo()

@router.post("/sistema/catalogos/solicitudes")
async def compat_post_solicitud_catalogo(body: Dict, current_user: Dict = Depends(get_current_user)):
    repo.crear_solicitud_catalogo(body, current_user)
    return {"ok": True, "message": "Solicitud creada en SQL (compat)"}

@router.put("/sistema/catalogos/solicitudes/{solicitud_id}/estado")
async def compat_put_estado_solicitud_catalogo(solicitud_id: int, body: Dict, current_user: Dict = Depends(get_current_user)):
    updated = repo.actualizar_estado_solicitud(solicitud_id, body, current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return {"ok": True, "message": "Estado actualizado en SQL (compat)"}

# =========================================================
# COMPATIBILIDAD LEGACY - TAREAS
# =========================================================

@router.get("/sistema/tareas")
async def compat_get_tareas(current_user: Dict = Depends(get_current_user)):
    return repo.listar_tareas()

@router.post("/sistema/tareas")
async def compat_post_tarea(body: Dict, current_user: Dict = Depends(get_current_user)):
    repo.crear_tarea(body, current_user)
    return {"ok": True, "message": "Tarea creada en SQL (compat)"}
