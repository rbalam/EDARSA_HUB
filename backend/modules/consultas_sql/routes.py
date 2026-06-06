"""
Rutas SQL-first para Consultas SQL
Reemplaza endpoints MongoDB legacy (/queries, /consultas-custom)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Optional
from core.security import get_current_user
from .repository import get_consultas_sql_repo

router = APIRouter(prefix="/api/sql", tags=["Consultas SQL"])


@router.get("/consultas")
async def listar_consultas_sql(
    tipo: Optional[str] = Query(None, description="QUERY o CUSTOM"),
    modulo: Optional[str] = Query(None),
    activa: Optional[bool] = Query(True),
    current_user: Dict = Depends(get_current_user)
):
    """Lista consultas SQL desde SQL Server."""
    repo = get_consultas_sql_repo()
    consultas = repo.list_consultas(tipo=tipo, modulo=modulo, activa=activa)
    return {
        "consultas": consultas,
        "total": len(consultas),
        "source": "SQL_CONSULTAS"
    }


@router.get("/consultas/{consulta_id}")
async def obtener_consulta_sql(
    consulta_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene una consulta por ID desde SQL Server."""
    repo = get_consultas_sql_repo()
    consulta = repo.get_consulta(consulta_id)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return consulta


@router.post("/consultas")
async def crear_consulta_sql(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Crea una consulta en SQL Server."""
    repo = get_consultas_sql_repo()
    result = repo.create_consulta(body, current_user)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error al crear"))
    return {
        "ok": True,
        "id": result.get("id"),
        "message": "Consulta creada en SQL Server",
        "source": "SQL_CONSULTAS"
    }


@router.put("/consultas/{consulta_id}")
async def actualizar_consulta_sql(
    consulta_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza una consulta en SQL Server."""
    repo = get_consultas_sql_repo()
    result = repo.update_consulta(consulta_id, body, current_user)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error al actualizar"))
    if not result.get("updated"):
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return {
        "ok": True,
        "message": "Consulta actualizada en SQL Server",
        "source": "SQL_CONSULTAS"
    }


@router.delete("/consultas/{consulta_id}")
async def eliminar_consulta_sql(
    consulta_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Desactiva (soft delete) una consulta en SQL Server."""
    repo = get_consultas_sql_repo()
    result = repo.delete_consulta(consulta_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error al eliminar"))
    if not result.get("deleted"):
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return {
        "ok": True,
        "message": "Consulta desactivada en SQL Server",
        "source": "SQL_CONSULTAS"
    }
