from core.corporate_filters.service import CorporateFilterService
"""
Rutas de Precios Sugeridos para Costos y Márgenes.

FASE 1C-3G-F: Endpoints para:
- Obtener precios sugeridos consolidados
- CRUD de rangos de vinos (VINOS_RANGOS_MX)

REGLAS:
- NO modifica precios oficiales
- EDARSAHUB SQL es la fuente de verdad
- CERO MongoDB
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from pydantic import BaseModel, Field
from core.security import get_current_user
from core.rbac.middleware import require_permission
from core.corporate_filters.request_resolver import (
    resolve_authorized_unidad_scope,
)
from modules.costos_margenes.configuracion_repository import (
    resolver_configuracion_efectiva,
)

from modules.comercial.services.precios_sugeridos_consolidado_service import (
    obtener_precios_sugeridos,
    obtener_rangos_vinos,
    crear_rango_vino,
    actualizar_rango_vino,
    desactivar_rango_vino
)

router = APIRouter(prefix="/comercial/pricing", tags=["Precios Sugeridos"])

_PERMISO_PRECIOS_SUGERIDOS = "comercial.precios_sugeridos.generar"


def _actor_from_user(current_user: dict, usuario: Optional[str] = None) -> str:
    return (
        (current_user or {}).get("email")
        or (current_user or {}).get("username")
        or usuario
        or "sistema"
    )


# =============================================================================
# SCHEMAS
# =============================================================================

class RangoVinoCreate(BaseModel):
    """Request para crear rango de vino"""
    limite_inferior: float = Field(..., ge=0, description="Limite inferior del rango (costo)")
    limite_superior: float = Field(..., gt=0, description="Limite superior del rango (costo)")
    multiplicador: float = Field(..., gt=0, description="Multiplicador para calcular precio")
    descripcion: str = Field(..., max_length=100, description="Descripcion del rango")
    orden: int = Field(..., ge=1, description="Orden de aplicacion")


class RangoVinoUpdate(BaseModel):
    """Request para actualizar rango de vino"""
    limite_inferior: Optional[float] = Field(None, ge=0)
    limite_superior: Optional[float] = Field(None, gt=0)
    multiplicador: Optional[float] = Field(None, gt=0)
    descripcion: Optional[str] = Field(None, max_length=100)
    orden: Optional[int] = Field(None, ge=1)
    activo: Optional[bool] = None


# =============================================================================
# ENDPOINTS PRECIOS SUGERIDOS
# =============================================================================

@router.get("/precios-sugeridos")
async def get_precios_sugeridos(
    server_id: Optional[str] = Query(None, description="DEPRECATED: usar 'unidad'"),
    unidad: Optional[str] = Query(None, description="CANÓNICO: unidad de negocio (codigo o id)"),
    familia: Optional[str] = Query(None, description="Filtrar por familia"),
    subfamilia: Optional[str] = Query(None, description="Filtrar por subfamilia"),
    solo_vinos: bool = Query(False, description="Solo productos vino"),
    solo_fuera_rango: bool = Query(False, description="Solo productos fuera de rango"),
    solo_requiere_revision: bool = Query(False, description="Solo productos que requieren revision"),
    fuente: Optional[str] = Query(None, description="Filtrar por fuente sugerencia"),
    margen_bajo: bool = Query(
        False,
        description=(
            "Solo productos cuyo margen actual está por debajo "
            "del margen efectivo canónico"
        ),
    ),
    solo_con_receta: bool = Query(False, description="Solo productos con receta"),
    incluir_inactivos: bool = Query(False, description="Incluir productos inactivos/dados de baja"),
    search: Optional[str] = Query(None, description="Buscar por nombre o codigo"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission(_PERMISO_PRECIOS_SUGERIDOS))
):
    """
    Obtiene lista de productos con precios sugeridos calculados.
    
    BUG-COSTOS-001: Por defecto solo muestra productos activos.
    Usar incluir_inactivos=true para ver también productos inactivos/dados de baja.
    
    Para vinos: Usa VINOS_RANGOS
    Para otros: Usa COSTO_MARGEN
    
    NO modifica precios oficiales. Solo muestra recomendaciones.
    """
    if not unidad:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "UNIDAD_CANONICA_REQUERIDA",
                "mensaje": (
                    "Precios Sugeridos requiere una unidad "
                    "canónica para resolver configuración efectiva"
                ),
            },
        )

    scope = await resolve_authorized_unidad_scope(
        current_user,
        _PERMISO_PRECIOS_SUGERIDOS,
        unidad,
    )

    if scope.access_denied or not scope.unidad_pk:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "ALCANCE_DENEGADO",
                "mensaje": "No tiene acceso a la unidad solicitada",
                "permiso_requerido": _PERMISO_PRECIOS_SUGERIDOS,
            },
        )

    usuario_value = (
        (current_user or {}).get("_sql_usuario_id")
        or (current_user or {}).get("UsuarioID")
        or (current_user or {}).get("usuario_id")
    )

    if isinstance(usuario_value, bool):
        usuario_value = None

    try:
        usuario_id = int(usuario_value)
    except (TypeError, ValueError):
        usuario_id = None

    if not usuario_id or usuario_id <= 0:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "SQL_USUARIO_NO_RESUELTO",
                "mensaje": (
                    "No existe identidad SQL canónica para "
                    "resolver configuración de Precios Sugeridos"
                ),
            },
        )

    try:
        configuracion_efectiva = (
            resolver_configuracion_efectiva(
                str(scope.unidad_pk),
                usuario_id=usuario_id,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "CONFIGURACION_EFECTIVA_NO_RESUELTA",
                "mensaje": str(exc),
            },
        ) from exc

    multiplo_redondeo = configuracion_efectiva.get(
        "multiplo_redondeo"
    )
    metodo_redondeo = configuracion_efectiva.get(
        "metodo_redondeo"
    )

    if (
        multiplo_redondeo is None
        or metodo_redondeo is None
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "error": "REDONDEO_NO_CONFIGURADO",
                "mensaje": (
                    "La configuración efectiva no define "
                    "múltiplo y método de redondeo"
                ),
            },
        )
    result = obtener_precios_sugeridos(
        server_id=scope.server_id,
        familia=familia,
        subfamilia=subfamilia,
        solo_vinos=solo_vinos,
        solo_fuera_rango=solo_fuera_rango,
        solo_requiere_revision=solo_requiere_revision,
        fuente=fuente,
        margen_bajo=margen_bajo,
        solo_con_receta=solo_con_receta,
        incluir_inactivos=incluir_inactivos,
        search=search,
        page=page,
        page_size=page_size,
        empresa_id=configuracion_efectiva.get(
            "empresa_id"
        ),
        unidad_negocio_pk=str(scope.unidad_pk),
        usuario_id=usuario_id,
        multiplo_redondeo=multiplo_redondeo,
        metodo_redondeo=metodo_redondeo,
    )
    return result


# =============================================================================
# ENDPOINTS CRUD RANGOS VINOS
# =============================================================================

@router.get("/reglas/vinos/rangos")
async def get_rangos_vinos(
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission(_PERMISO_PRECIOS_SUGERIDOS))
):
    """
    Lista todos los rangos de VINOS_RANGOS_MX.
    
    Incluye verificacion de traslapes entre rangos activos.
    """
    return obtener_rangos_vinos()


@router.post("/reglas/vinos/rangos")
async def post_crear_rango_vino(
    rango: RangoVinoCreate,
    usuario: Optional[str] = Query(None, description="DEPRECATED: se usa el usuario autenticado"),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission(_PERMISO_PRECIOS_SUGERIDOS))
):
    """
    Crea un nuevo rango para VINOS_RANGOS_MX.
    
    Valida que no haya traslapes con rangos activos existentes.
    """
    result = crear_rango_vino(
        limite_inferior=rango.limite_inferior,
        limite_superior=rango.limite_superior,
        multiplicador=rango.multiplicador,
        descripcion=rango.descripcion,
        orden=rango.orden,
        usuario=_actor_from_user(current_user, usuario)
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('mensaje'))
    
    return result


@router.put("/reglas/vinos/rangos/{rango_id}")
async def put_actualizar_rango_vino(
    rango_id: str,
    rango: RangoVinoUpdate,
    usuario: Optional[str] = Query(None, description="DEPRECATED: se usa el usuario autenticado"),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission(_PERMISO_PRECIOS_SUGERIDOS))
):
    """
    Actualiza un rango existente de VINOS_RANGOS_MX.
    
    Valida que no haya traslapes si se modifican limites.
    """
    result = actualizar_rango_vino(
        rango_id=rango_id,
        limite_inferior=rango.limite_inferior,
        limite_superior=rango.limite_superior,
        multiplicador=rango.multiplicador,
        descripcion=rango.descripcion,
        orden=rango.orden,
        activo=rango.activo,
        usuario=_actor_from_user(current_user, usuario)
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('mensaje'))
    
    return result


@router.patch("/reglas/vinos/rangos/{rango_id}/desactivar")
async def patch_desactivar_rango_vino(
    rango_id: str,
    usuario: Optional[str] = Query(None, description="DEPRECATED: se usa el usuario autenticado"),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission(_PERMISO_PRECIOS_SUGERIDOS))
):
    """
    Desactiva un rango de VINOS_RANGOS_MX (soft delete).
    
    No elimina fisicamente, solo marca Activo = 0.
    """
    result = desactivar_rango_vino(
        rango_id=rango_id,
        usuario=_actor_from_user(current_user, usuario),
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('mensaje'))
    
    return result


@router.patch("/reglas/vinos/rangos/{rango_id}/activar")
async def patch_activar_rango_vino(
    rango_id: str,
    usuario: Optional[str] = Query(None, description="DEPRECATED: se usa el usuario autenticado"),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission(_PERMISO_PRECIOS_SUGERIDOS))
):
    """
    Activa un rango previamente desactivado.
    
    Valida que no haya traslapes con otros rangos activos.
    """
    result = actualizar_rango_vino(
        rango_id=rango_id,
        activo=True,
        usuario=_actor_from_user(current_user, usuario),
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('mensaje'))
    
    return result
