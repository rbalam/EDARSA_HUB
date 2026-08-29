from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
FASE 1C-3I-G: Endpoints de Listas Manuales de Competidores

Rutas CRUD para gestionar listas de competidores.

REGLAS:
- EDARSAHUB SQL es el cerebro
- CERO MongoDB
- No modificar precios oficiales
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import logging

from core.security import get_current_user
from core.rbac.middleware import require_permission
from modules.comercial.services.listas_competidores_service import (
    listar_listas_competidores,
    crear_lista_competidores,
    actualizar_lista_competidores,
    desactivar_lista_competidores,
    obtener_lista_competidores,
    listar_competidores_de_lista,
    agregar_competidor_a_lista,
    quitar_competidor_de_lista,
    obtener_listas_de_competidor,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/comercial/pricing/listas-competidores",
    tags=["Comercial - Listas de Competidores"]
)


# =============================================================================
# SCHEMAS
# =============================================================================

class ListaCompetidoresCreate(BaseModel):
    nombre_lista: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    empresa_id: Optional[int] = None
    unidad_negocio_pk: Optional[int] = None
    segmento: Optional[str] = Field(None, max_length=100)
    categoria: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=20)


class ListaCompetidoresUpdate(BaseModel):
    nombre_lista: Optional[str] = Field(None, min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    segmento: Optional[str] = Field(None, max_length=100)
    categoria: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=20)


class AgregarCompetidorRequest(BaseModel):
    competidor_id: str
    orden: int = 0
    notas: Optional[str] = Field(None, max_length=500)


# =============================================================================
# ENDPOINTS LISTAS
# =============================================================================

@router.get(
    "",
    summary="Listar listas de competidores"
)
async def endpoint_listar_listas(
    empresa_id: Optional[int] = Query(None),
    unidad_negocio_pk: Optional[int] = Query(None),
    solo_activas: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.ver"))
):
    """
    Lista todas las listas de competidores con conteo de miembros.
    """
    try:
        result = listar_listas_competidores(
            empresa_id=empresa_id,
            unidad_negocio_pk=unidad_negocio_pk,
            solo_activas=solo_activas,
            page=page,
            page_size=page_size
        )
        return {
            "success": True,
            **result,
            "fuente": "EDARSAHUB_SQL"
        }
    except Exception as e:
        logger.error(f"[LISTAS] Error listando: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post(
    "",
    summary="Crear lista de competidores"
)
async def endpoint_crear_lista(
    data: ListaCompetidoresCreate,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.crear"))
):
    """
    Crea una nueva lista de competidores.
    """
    try:
        result = crear_lista_competidores(
            nombre_lista=data.nombre_lista,
            descripcion=data.descripcion,
            empresa_id=data.empresa_id,
            unidad_negocio_pk=data.unidad_negocio_pk,
            segmento=data.segmento,
            categoria=data.categoria,
            color=data.color,
            usuario=current_user.get('email', 'sistema')
        )
        return {
            "success": True,
            "lista": result,
            "mensaje": f"Lista '{data.nombre_lista}' creada correctamente"
        }
    except Exception as e:
        logger.error(f"[LISTAS] Error creando: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get(
    "/{lista_id}",
    summary="Obtener lista de competidores"
)
async def endpoint_obtener_lista(
    lista_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.ver"))
):
    """
    Obtiene una lista de competidores por ID.
    """
    try:
        result = obtener_lista_competidores(lista_id)
        if not result:
            raise HTTPException(status_code=404, detail="Lista no encontrada")
        return {
            "success": True,
            "lista": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LISTAS] Error obteniendo: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put(
    "/{lista_id}",
    summary="Actualizar lista de competidores"
)
async def endpoint_actualizar_lista(
    lista_id: str,
    data: ListaCompetidoresUpdate,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.editar"))
):
    """
    Actualiza una lista de competidores existente.
    """
    try:
        result = actualizar_lista_competidores(
            lista_id=lista_id,
            nombre_lista=data.nombre_lista,
            descripcion=data.descripcion,
            segmento=data.segmento,
            categoria=data.categoria,
            color=data.color,
            usuario=current_user.get('email', 'sistema')
        )
        return {
            "success": True,
            "lista": result,
            "mensaje": "Lista actualizada correctamente"
        }
    except Exception as e:
        logger.error(f"[LISTAS] Error actualizando: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete(
    "/{lista_id}",
    summary="Desactivar lista de competidores"
)
async def endpoint_desactivar_lista(
    lista_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.eliminar"))
):
    """
    Desactiva (soft delete) una lista de competidores.
    """
    try:
        result = desactivar_lista_competidores(
            lista_id=lista_id,
            usuario=current_user.get('email', 'sistema')
        )
        return {
            "success": result,
            "mensaje": "Lista desactivada correctamente" if result else "Error desactivando lista"
        }
    except Exception as e:
        logger.error(f"[LISTAS] Error desactivando: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# =============================================================================
# ENDPOINTS DETALLE (COMPETIDORES EN LISTA)
# =============================================================================

@router.get(
    "/{lista_id}/competidores",
    summary="Listar competidores de una lista"
)
async def endpoint_listar_competidores_lista(
    lista_id: str,
    solo_activos: bool = Query(True),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.ver"))
):
    """
    Lista todos los competidores de una lista específica.
    """
    try:
        result = listar_competidores_de_lista(
            lista_id=lista_id,
            solo_activos=solo_activos
        )
        return {
            "success": True,
            "competidores": result,
            "total": len(result),
            "lista_id": lista_id
        }
    except Exception as e:
        logger.error(f"[LISTAS] Error listando competidores: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post(
    "/{lista_id}/competidores",
    summary="Agregar competidor a lista"
)
async def endpoint_agregar_competidor(
    lista_id: str,
    data: AgregarCompetidorRequest,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.editar"))
):
    """
    Agrega un competidor a una lista.
    """
    try:
        result = agregar_competidor_a_lista(
            lista_id=lista_id,
            competidor_id=data.competidor_id,
            orden=data.orden,
            notas=data.notas,
            usuario=current_user.get('email', 'sistema')
        )
        return {
            "success": True,
            "detalle": result,
            "mensaje": "Competidor agregado a la lista"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[LISTAS] Error agregando competidor: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete(
    "/{lista_id}/competidores/{competidor_id}",
    summary="Quitar competidor de lista"
)
async def endpoint_quitar_competidor(
    lista_id: str,
    competidor_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.editar"))
):
    """
    Quita un competidor de una lista.
    """
    try:
        result = quitar_competidor_de_lista(
            lista_id=lista_id,
            competidor_id=competidor_id,
            usuario=current_user.get('email', 'sistema')
        )
        return {
            "success": result,
            "mensaje": "Competidor quitado de la lista" if result else "Error quitando competidor"
        }
    except Exception as e:
        logger.error(f"[LISTAS] Error quitando competidor: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# =============================================================================
# ENDPOINT AUXILIAR
# =============================================================================

@router.get(
    "/competidor/{competidor_id}/listas",
    summary="Obtener listas de un competidor"
)
async def endpoint_listas_de_competidor(
    competidor_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.ver"))
):
    """
    Obtiene todas las listas a las que pertenece un competidor.
    """
    try:
        result = obtener_listas_de_competidor(competidor_id)
        return {
            "success": True,
            "listas": result,
            "total": len(result),
            "competidor_id": competidor_id
        }
    except Exception as e:
        logger.error(f"[LISTAS] Error obteniendo listas de competidor: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
