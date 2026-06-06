from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Optional
from core.security import get_current_user
from modules.catalogos_workflow_sql.repository import CatalogosWorkflowSQLRepository

router = APIRouter(prefix="/api/sql/catalogos-workflow", tags=["Catalogos Workflow SQL"])
repo = CatalogosWorkflowSQLRepository()


@router.get("/config")
async def get_catalogos_disponibles(current_user: Dict = Depends(get_current_user)):
    """Lista todas las configuraciones de catálogos activas"""
    try:
        return repo.get_catalogos_disponibles()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/{catalogo_id}/niveles")
async def put_catalogo_niveles(
    catalogo_id: str,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Upsert niveles de aprobación para un catálogo"""
    try:
        repo.upsert_niveles_catalogo(catalogo_id, body, current_user)
        return {"ok": True, "message": "Niveles de aprobación guardados en SQL"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/permisos/usuario/{user_id}")
async def get_permisos_catalogo(
    user_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene permisos de catálogos para un usuario específico"""
    try:
        return repo.get_permisos_catalogo_usuario(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/permisos")
async def post_permisos_catalogo(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea o actualiza permisos de catálogo"""
    try:
        repo.upsert_permisos_catalogo(body, current_user)
        return {"ok": True, "message": "Permisos guardados en SQL"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/solicitudes")
async def get_solicitudes_catalogo(
    limit: int = Query(default=100, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """Lista solicitudes de catálogos"""
    try:
        return repo.listar_solicitudes_catalogo(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/solicitudes")
async def post_solicitud_catalogo(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea una nueva solicitud de catálogo"""
    try:
        repo.crear_solicitud_catalogo(body, current_user)
        return {"ok": True, "message": "Solicitud creada en SQL"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/solicitudes/{solicitud_id}/estado")
async def put_estado_solicitud_catalogo(
    solicitud_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza el estado de una solicitud"""
    try:
        updated = repo.actualizar_estado_solicitud(solicitud_id, body, current_user)
        if not updated:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        return {"ok": True, "message": "Estado actualizado en SQL"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tareas")
async def get_tareas(
    limit: int = Query(default=100, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """Lista tareas del sistema"""
    try:
        return repo.listar_tareas(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tareas")
async def post_tarea(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea una nueva tarea del sistema"""
    try:
        repo.crear_tarea(body, current_user)
        return {"ok": True, "message": "Tarea creada en SQL"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
