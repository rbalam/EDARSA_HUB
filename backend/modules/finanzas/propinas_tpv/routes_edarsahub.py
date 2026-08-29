from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
SUBFASE 3.4 — Rutas EDARSAHUB para Propinas TPV

Endpoints que leen propinas TPV desde EDARSAHUB como fuente de verdad.
Reemplazan la lectura de MongoDB para consultas financieras.

Endpoints:
- GET /api/finanzas/propinas/v2/resumen
- GET /api/finanzas/propinas/v2/detalle
- GET /api/finanzas/propinas/v2/listado
- GET /api/finanzas/propinas/v2/unidades
- GET /api/finanzas/propinas/v2/formas-pago
- GET /api/finanzas/propinas/v2/status
- GET /api/finanzas/propinas/v2/{id}

Autor: E1 Agent
Fecha: 1 Mayo 2026
Fase: Finanzas Fase 3 - Propinas TPV - Subfase 3.4
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Request

from core.security import get_current_user_dual
from .repository_edarsahub import PropinasTPVRepositoryEdarsahub
from .models import PropinasConfigCreate
from .sql_repository import PropinasTPVSQLRepository
from modules.finanzas.access import (
    FINANZAS_ADMINISTRAR,
    FINANZAS_EDITAR,
    FINANZAS_VER,
    filter_unidades_for_finanzas,
    get_finanzas_allowed_unidad_pks,
    require_any_finanzas_permission,
    require_finanzas_permission,
    resolve_finanzas_unit_filter,
)

logger = logging.getLogger(__name__)

# Router con prefijo específico para endpoints EDARSAHUB v2
router = APIRouter(
    prefix="/finanzas/propinas/v2",
    tags=["Propinas TPV - EDARSAHUB v2"]
)


# ============================================================================
# DEPENDENCIA DE AUTENTICACIÓN DUAL
# ============================================================================

async def get_user_v2(request: Request) -> dict:
    """
    Dependencia para autenticación dual (Header Bearer O Cookie httpOnly).
    SUBFASE 3.5: Soporte para frontend con cookies.
    """
    return await get_current_user_dual(request)


# ============================================================================
# HELPERS RBAC
# ============================================================================

async def get_unidades_permitidas_rbac(current_user: dict) -> Optional[List[str]]:
    """
    Obtiene las unidades de negocio permitidas para el usuario (RBAC).
    
    Returns:
        None si es admin (sin restricción)
        Lista de UnidadNegocioID si tiene restricciones
    """
    return get_finanzas_allowed_unidad_pks(current_user, FINANZAS_VER)


# ============================================================================
# ENDPOINT: RESUMEN
# ============================================================================

@router.get(
    "/resumen",
    summary="Resumen de propinas TPV (EDARSAHUB)",
    description="""
    Obtiene resumen agregado de propinas TPV desde EDARSAHUB.
    
    Fuente: EDARSAHUB.propinas_tpv_control
    Filtros: EsDemo=0, Activo=1
    
    Retorna:
    - Resumen general (totales)
    - Desglose por unidad de negocio
    - Status de sincronización
    """
)
async def resumen_propinas_edarsahub(
    fecha_inicio: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    fecha_fin: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    unidad_negocio_pk: Optional[str] = Query(None, description="Filtrar por UnidadNegocioID (o 'TODAS')"),
    unidad_negocio_id: Optional[str] = Query(None, description="DEPRECATED: usar unidad_negocio_pk"),
    sistema_origen: Optional[str] = Query(None, description="Filtrar por SistemaOrigen (SoftRestaurant, MPRO)"),
    current_user: dict = Depends(get_user_v2)
):
    """Resumen de propinas TPV desde EDARSAHUB"""
    try:
        unidad_pk, unidades_permitidas = resolve_finanzas_unit_filter(
            current_user,
            unidad_negocio_pk or unidad_negocio_id,
        )
        
        repo = PropinasTPVRepositoryEdarsahub()
        result = repo.obtener_resumen(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            unidad_negocio_pk=unidad_pk,
            sistema_origen=sistema_origen,
            unidades_permitidas=unidades_permitidas
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen EDARSAHUB: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ============================================================================
# ENDPOINT: DETALLE
# ============================================================================

@router.get(
    "/detalle",
    summary="Detalle de propinas TPV (EDARSAHUB)",
    description="""
    Obtiene detalle de propinas TPV desde EDARSAHUB para listado.
    
    Fuente: EDARSAHUB.propinas_tpv_control
    Filtros: EsDemo=0, Activo=1
    
    Retorna:
    - Lista de propinas con detalle
    - Totales agregados
    - Paginación
    """
)
async def detalle_propinas_edarsahub(
    fecha_inicio: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    fecha_fin: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    unidad_negocio_pk: Optional[str] = Query(None, description="Filtrar por UnidadNegocioID"),
    unidad_negocio_id: Optional[str] = Query(None, description="DEPRECATED: usar unidad_negocio_pk"),
    sistema_origen: Optional[str] = Query(None, description="Filtrar por SistemaOrigen"),
    forma_pago: Optional[str] = Query(None, description="Filtrar por FormaPagoNombre"),
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(50, ge=1, le=200, description="Registros por página"),
    current_user: dict = Depends(get_user_v2)
):
    """Detalle de propinas TPV desde EDARSAHUB"""
    try:
        unidad_pk, unidades_permitidas = resolve_finanzas_unit_filter(
            current_user,
            unidad_negocio_pk or unidad_negocio_id,
        )
        
        repo = PropinasTPVRepositoryEdarsahub()
        result = repo.obtener_detalle(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            unidad_negocio_pk=unidad_pk,
            sistema_origen=sistema_origen,
            forma_pago=forma_pago,
            page=page,
            limit=limit,
            unidades_permitidas=unidades_permitidas
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo detalle EDARSAHUB: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ============================================================================
# ENDPOINT: LISTADO (compatibilidad)
# ============================================================================

@router.get(
    "/listado",
    summary="Listado de propinas TPV (EDARSAHUB)",
    description="""
    Obtiene listado de propinas TPV desde EDARSAHUB.
    Compatible con formato anterior de MongoDB.
    
    Fuente: EDARSAHUB.propinas_tpv_control
    """
)
async def listado_propinas_edarsahub(
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio YYYY-MM-DD"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin YYYY-MM-DD"),
    unidad_negocio_pk: Optional[str] = Query(None, description="Filtrar por UnidadNegocioID"),
    unidad_negocio_id: Optional[str] = Query(None, description="DEPRECATED: usar unidad_negocio_pk"),
    sistema_origen: Optional[str] = Query(None, description="Filtrar por SistemaOrigen"),
    forma_pago: Optional[str] = Query(None, description="Filtrar por FormaPagoNombre"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_user_v2)
):
    """Listado de propinas TPV desde EDARSAHUB"""
    try:
        # Si no se especifican fechas, usar últimos 7 días
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not fecha_fin:
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
        
        unidad_pk, unidades_permitidas = resolve_finanzas_unit_filter(
            current_user,
            unidad_negocio_pk or unidad_negocio_id,
        )
        
        repo = PropinasTPVRepositoryEdarsahub()
        result = repo.obtener_propinas(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            unidad_negocio_pk=unidad_pk,
            sistema_origen=sistema_origen,
            forma_pago=forma_pago,
            page=page,
            limit=limit,
            unidades_permitidas=unidades_permitidas
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listando propinas EDARSAHUB: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ============================================================================
# ENDPOINT: UNIDADES DISPONIBLES
# ============================================================================

@router.get(
    "/unidades",
    summary="Unidades de negocio con propinas TPV",
    description="""
    Obtiene lista de unidades de negocio que tienen propinas TPV sincronizadas.
    Útil para poblar selectores en frontend.
    
    Fuente: EDARSAHUB.propinas_tpv_control
    """
)
async def unidades_disponibles(
    current_user: dict = Depends(get_user_v2)
):
    """Lista de unidades con propinas TPV"""
    try:
        repo = PropinasTPVRepositoryEdarsahub()
        unidades = filter_unidades_for_finanzas(
            repo.obtener_unidades_disponibles(),
            current_user,
        )
        
        return {
            'unidades': unidades,
            'total': len(unidades),
            'fuente': 'EDARSAHUB_REAL'
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo unidades: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ============================================================================
# ENDPOINTS: CONFIGURACION SQL CANONICA
# ============================================================================

def _config_repo() -> PropinasTPVSQLRepository:
    return PropinasTPVSQLRepository(None)


def _enum_value(value):
    return getattr(value, "value", value)


def _config_request_to_sql(
    request: PropinasConfigCreate,
    current_user: dict,
    *,
    updating: bool = False,
) -> dict:
    payload = request.dict()
    alcance = payload.get("alcance") or {}
    vigencia = payload.get("vigencia") or {}
    parametros = payload.get("parametros") or {}
    usuario = (
        current_user.get("email")
        or current_user.get("username")
        or str(current_user.get("UsuarioID") or "")
        or "sistema"
    )

    data = {
        "alcance_tipo": _enum_value(alcance.get("tipo")),
        "alcance_server_id": alcance.get("server_id"),
        "alcance_empresa_id": alcance.get("empresa_id"),
        "alcance_sucursal_id": alcance.get("sucursal_id"),
        "vigencia_inicio": vigencia.get("fecha_inicio"),
        "vigencia_fin": vigencia.get("fecha_fin"),
        "activa": bool(vigencia.get("activa", True)),
        "porcentaje_comision": parametros.get("porcentaje_comision"),
        "tolerancia_descuadre": parametros.get("tolerancia_descuadre"),
        "dias_para_cuadrar": parametros.get("dias_para_cuadrar"),
        "motivo_cambio": payload.get("motivo_cambio"),
    }

    data["updated_by" if updating else "created_by"] = usuario
    return data


@router.get(
    "/config",
    summary="Configuracion vigente de propinas TPV (SQL canonico)",
)
async def obtener_config_v2(
    current_user: dict = Depends(get_user_v2),
):
    require_finanzas_permission(current_user, FINANZAS_VER)
    configs = await _config_repo().listar_configs()
    if len(configs) == 1 and configs[0].get("id") == "default":
        return {
            "config": None,
            "fuente": "EDARSAHUB_REAL",
            "mensaje": "Sin configuracion canonica de propinas registrada."
        }
    return {
        "config": next((c for c in configs if c.get("vigencia", {}).get("activa")), None),
        "fuente": "EDARSAHUB_REAL",
    }


@router.get(
    "/config/all",
    summary="Listar configuraciones de propinas TPV (SQL canonico)",
)
async def listar_configs_v2(
    current_user: dict = Depends(get_user_v2),
):
    require_finanzas_permission(current_user, FINANZAS_VER)
    configs = await _config_repo().listar_configs()
    if len(configs) == 1 and configs[0].get("id") == "default":
        configs = []
    return {
        "success": True,
        "configs": configs,
        "total": len(configs),
        "fuente": "EDARSAHUB_REAL",
    }


@router.post(
    "/config",
    summary="Crear configuracion de propinas TPV (SQL canonico)",
)
async def crear_config_v2(
    request: PropinasConfigCreate,
    current_user: dict = Depends(get_user_v2),
):
    require_any_finanzas_permission(
        current_user,
        (FINANZAS_ADMINISTRAR, FINANZAS_EDITAR),
    )
    return await _config_repo().crear_config(
        _config_request_to_sql(request, current_user)
    )


@router.put(
    "/config/{config_id}",
    summary="Actualizar configuracion de propinas TPV (SQL canonico)",
)
async def actualizar_config_v2(
    config_id: str,
    request: PropinasConfigCreate,
    current_user: dict = Depends(get_user_v2),
):
    require_any_finanzas_permission(
        current_user,
        (FINANZAS_ADMINISTRAR, FINANZAS_EDITAR),
    )
    return await _config_repo().actualizar_config(
        config_id,
        _config_request_to_sql(
            request,
            current_user,
            updating=True,
        ),
    )


# ============================================================================
# ENDPOINT: FORMAS DE PAGO
# ============================================================================

@router.get(
    "/formas-pago",
    summary="Formas de pago disponibles",
    description="""
    Obtiene lista de formas de pago (tarjeta) disponibles.
    Útil para filtros en frontend.
    
    Fuente: EDARSAHUB.propinas_tpv_control
    """
)
async def formas_pago_disponibles(
    current_user: dict = Depends(get_user_v2)
):
    """Lista de formas de pago"""
    try:
        repo = PropinasTPVRepositoryEdarsahub()
        formas_pago = repo.obtener_formas_pago()
        
        return {
            'formas_pago': formas_pago,
            'total': len(formas_pago),
            'fuente': 'EDARSAHUB_REAL'
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo formas de pago: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ============================================================================
# ENDPOINT: STATUS SINCRONIZACIÓN
# ============================================================================

@router.get(
    "/status",
    summary="Status de sincronización",
    description="""
    Obtiene status de sincronización de propinas TPV.
    
    Fuente: EDARSAHUB.Finanzas_PropinasTPV_SyncLog
    
    Retorna:
    - Última sincronización global
    - Última sincronización por unidad
    - Totales actuales
    """
)
async def status_sincronizacion(
    current_user: dict = Depends(get_user_v2)
):
    """Status de sincronización"""
    try:
        repo = PropinasTPVRepositoryEdarsahub()
        status = repo.obtener_status_sincronizacion()
        
        return status
        
    except Exception as e:
        logger.error(f"Error obteniendo status: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ============================================================================
# ENDPOINT: HEALTH CHECK (debe estar antes de /{propina_id})
# ============================================================================

@router.get(
    "/health",
    summary="Health check EDARSAHUB",
    description="Verifica conectividad con EDARSAHUB"
)
async def health_check():
    """Health check de conexión EDARSAHUB"""
    try:
        repo = PropinasTPVRepositoryEdarsahub()
        status = repo.obtener_status_sincronizacion()
        
        return {
            'status': 'healthy',
            'fuente': 'EDARSAHUB_REAL',
            'total_registros': status['totales']['total_registros'],
            'total_unidades': status['totales']['total_unidades'],
            'ultima_sincronizacion': status['ultima_sincronizacion']
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'fuente': 'EDARSAHUB',
            'error': str(e)
        }


# ============================================================================
# ENDPOINT: PROPINA POR ID (debe estar después de /health)
# ============================================================================

@router.get(
    "/{propina_id}",
    summary="Obtener propina por ID",
    description="""
    Obtiene el detalle de una propina específica por su ID.
    
    Fuente: EDARSAHUB.propinas_tpv_control
    """
)
async def obtener_propina_por_id(
    propina_id: int,
    current_user: dict = Depends(get_user_v2)
):
    """Obtener propina por ID"""
    try:
        repo = PropinasTPVRepositoryEdarsahub()
        propina = repo.obtener_propina_por_id(propina_id)
        
        if not propina:
            raise HTTPException(status_code=404, detail="Propina no encontrada")
        
        return propina
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo propina {propina_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
