"""
Rutas SQL-first para Informes de Auditoría
Reemplaza endpoints MongoDB legacy en server.py
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Optional
from core.security import get_current_user
from .repository import get_informes_auditoria_repo

router = APIRouter(prefix="/api/sql", tags=["Informes Auditoría SQL"])


@router.get("/informes-auditoria")
async def listar_informes_auditoria_sql(
    empresa_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """Lista informes de auditoría desde SQL Server."""
    repo = get_informes_auditoria_repo()
    filtros = {}
    if empresa_id:
        filtros['empresa_id'] = empresa_id
    if estado:
        filtros['estado'] = estado
    if tipo:
        filtros['tipo'] = tipo
    
    informes = repo.list_informes(filtros)
    return {
        "informes": informes,
        "total": len(informes),
        "source": "SQL_AUDITORIA_INFORMES"
    }


@router.get("/informes-auditoria/{informe_id}")
async def obtener_informe_auditoria_sql(
    informe_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene un informe de auditoría por ID desde SQL Server."""
    repo = get_informes_auditoria_repo()
    informe = repo.get_informe(informe_id)
    if not informe:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    return informe


@router.post("/informes-auditoria")
async def crear_informe_auditoria_sql(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea un informe de auditoría en SQL Server."""
    repo = get_informes_auditoria_repo()
    result = repo.create_informe(body, current_user)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error al crear informe"))
    return {
        "ok": True,
        "id": result.get("id"),
        "message": "Informe creado en SQL Server",
        "source": "SQL_AUDITORIA_INFORMES"
    }


@router.put("/informes-auditoria/{informe_id}")
async def actualizar_informe_auditoria_sql(
    informe_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza un informe de auditoría en SQL Server."""
    repo = get_informes_auditoria_repo()
    result = repo.update_informe(informe_id, body, current_user)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error al actualizar"))
    if not result.get("updated"):
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    return {
        "ok": True,
        "message": "Informe actualizado en SQL Server",
        "source": "SQL_AUDITORIA_INFORMES"
    }


@router.delete("/informes-auditoria/{informe_id}")
async def eliminar_informe_auditoria_sql(
    informe_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Cancela (soft delete) un informe de auditoría en SQL Server."""
    repo = get_informes_auditoria_repo()
    result = repo.delete_informe(informe_id, current_user)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error al eliminar"))
    if not result.get("deleted"):
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    return {
        "ok": True,
        "message": "Informe cancelado en SQL Server",
        "source": "SQL_AUDITORIA_INFORMES"
    }
