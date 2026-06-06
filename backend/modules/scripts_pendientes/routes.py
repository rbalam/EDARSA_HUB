"""
Rutas SQL-first para Scripts Pendientes
Reemplaza endpoints MongoDB legacy
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Optional
from core.security import get_current_user
from .repository import get_scripts_pendientes_repo

router = APIRouter(prefix="/api/sql", tags=["Scripts Pendientes SQL"])


@router.get("/scripts-pendientes")
async def listar_scripts_pendientes_sql(
    estado: Optional[str] = Query(None),
    modulo: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """Lista scripts pendientes desde SQL Server."""
    repo = get_scripts_pendientes_repo()
    scripts = repo.list_scripts(estado=estado, modulo=modulo)
    return {
        "scripts": scripts,
        "total": len(scripts),
        "source": "SQL_SCRIPTS_PENDIENTES"
    }


@router.get("/scripts-pendientes/{script_id}")
async def obtener_script_pendiente_sql(
    script_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene un script por ID desde SQL Server."""
    repo = get_scripts_pendientes_repo()
    script = repo.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script no encontrado")
    return script


@router.post("/scripts-pendientes")
async def crear_script_pendiente_sql(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea un script pendiente en SQL Server."""
    repo = get_scripts_pendientes_repo()
    result = repo.create_script(body, current_user)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error al crear"))
    return {
        "ok": True,
        "id": result.get("id"),
        "message": "Script creado en SQL Server",
        "source": "SQL_SCRIPTS_PENDIENTES"
    }


@router.put("/scripts-pendientes/{script_id}")
async def actualizar_script_pendiente_sql(
    script_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza un script en SQL Server."""
    repo = get_scripts_pendientes_repo()
    result = repo.update_script(script_id, body, current_user)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error al actualizar"))
    if not result.get("updated"):
        raise HTTPException(status_code=404, detail="Script no encontrado")
    return {
        "ok": True,
        "message": "Script actualizado en SQL Server",
        "source": "SQL_SCRIPTS_PENDIENTES"
    }


@router.delete("/scripts-pendientes/{script_id}")
async def eliminar_script_pendiente_sql(
    script_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Cancela un script en SQL Server."""
    repo = get_scripts_pendientes_repo()
    result = repo.delete_script(script_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error al eliminar"))
    if not result.get("deleted"):
        raise HTTPException(status_code=404, detail="Script no encontrado")
    return {
        "ok": True,
        "message": "Script cancelado en SQL Server",
        "source": "SQL_SCRIPTS_PENDIENTES"
    }
