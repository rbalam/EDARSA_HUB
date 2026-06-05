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
    from server import db
    
    # Verificar rol admin
    role = current_user.get('role', '')
    if role.lower() in ['admin', 'superadmin', 'administrador', 'superadministrador']:
        return None  # Sin restricción
    
    # Obtener empresas_permitidas del usuario
    empresas_permitidas = current_user.get('empresas_permitidas', [])
    if not empresas_permitidas:
        return None  # Sin restricción (legacy)
    
    # Mapear empresas a UnidadNegocioID
    # Buscar en MongoDB las empresas y sus unidades
    try:
        empresas = await db.empresas.find(
            {'id': {'$in': empresas_permitidas}},
            {'_id': 0, 'id': 1, 'codigo': 1, 'nombre': 1}
        ).to_list(100)
        
        if not empresas:
            return None
        
        # Buscar unidades de negocio asociadas en EDARSAHUB
        from .repository_edarsahub import PropinasTPVRepositoryEdarsahub
        repo = PropinasTPVRepositoryEdarsahub()
        unidades = repo.obtener_unidades_disponibles()
        
        # Filtrar por empresas permitidas (matching por nombre/código)
        codigos_permitidos = set()
        for e in empresas:
            if e.get('codigo'):
                codigos_permitidos.add(e['codigo'].upper())
            if e.get('nombre'):
                codigos_permitidos.add(e['nombre'].upper())
        
        unidades_ids = []
        for u in unidades:
            nombre_upper = (u.get('unidad_negocio_nombre') or '').upper()
            if any(cod in nombre_upper for cod in codigos_permitidos):
                unidades_ids.append(u['unidad_negocio_id'])
        
        return unidades_ids if unidades_ids else None
        
    except Exception as e:
        logger.warning(f"Error obteniendo unidades RBAC: {e}")
        return None


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
    unidad_negocio_id: Optional[str] = Query(None, description="Filtrar por UnidadNegocioID (o 'TODAS')"),
    sistema_origen: Optional[str] = Query(None, description="Filtrar por SistemaOrigen (SoftRestaurant, MPRO)"),
    current_user: dict = Depends(get_user_v2)
):
    """Resumen de propinas TPV desde EDARSAHUB"""
    try:
        # RBAC
        unidades_permitidas = await get_unidades_permitidas_rbac(current_user)
        
        repo = PropinasTPVRepositoryEdarsahub()
        result = repo.obtener_resumen(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            unidad_negocio_id=unidad_negocio_id,
            sistema_origen=sistema_origen,
            unidades_permitidas=unidades_permitidas
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen EDARSAHUB: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    unidad_negocio_id: Optional[str] = Query(None, description="Filtrar por UnidadNegocioID"),
    sistema_origen: Optional[str] = Query(None, description="Filtrar por SistemaOrigen"),
    forma_pago: Optional[str] = Query(None, description="Filtrar por FormaPagoNombre"),
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(50, ge=1, le=200, description="Registros por página"),
    current_user: dict = Depends(get_user_v2)
):
    """Detalle de propinas TPV desde EDARSAHUB"""
    try:
        # RBAC
        unidades_permitidas = await get_unidades_permitidas_rbac(current_user)
        
        repo = PropinasTPVRepositoryEdarsahub()
        result = repo.obtener_detalle(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            unidad_negocio_id=unidad_negocio_id,
            sistema_origen=sistema_origen,
            forma_pago=forma_pago,
            page=page,
            limit=limit,
            unidades_permitidas=unidades_permitidas
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo detalle EDARSAHUB: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    unidad_negocio_id: Optional[str] = Query(None, description="Filtrar por UnidadNegocioID"),
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
        
        # RBAC
        unidades_permitidas = await get_unidades_permitidas_rbac(current_user)
        
        repo = PropinasTPVRepositoryEdarsahub()
        result = repo.obtener_propinas(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            unidad_negocio_id=unidad_negocio_id,
            sistema_origen=sistema_origen,
            forma_pago=forma_pago,
            page=page,
            limit=limit,
            unidades_permitidas=unidades_permitidas
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listando propinas EDARSAHUB: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        unidades = repo.obtener_unidades_disponibles()
        
        return {
            'unidades': unidades,
            'total': len(unidades),
            'fuente': 'EDARSAHUB_REAL'
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo unidades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))
