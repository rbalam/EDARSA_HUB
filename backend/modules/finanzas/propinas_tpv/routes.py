"""
API Routes para el módulo de Control de Propinas TPV
FASE 1 MVP - Solo SoftRestaurant

Endpoints:
- POST /api/finanzas/propinas/sincronizar
- GET  /api/finanzas/propinas
- GET  /api/finanzas/propinas/resumen
- GET  /api/finanzas/propinas/health
- GET  /api/finanzas/propinas/config
- GET  /api/finanzas/propinas/config/all
- POST /api/finanzas/propinas/config
- PUT  /api/finanzas/propinas/config/{id}
- POST /api/finanzas/propinas/inicializar
- GET  /api/finanzas/propinas/{id}          <- DEBE IR AL FINAL
- PUT  /api/finanzas/propinas/{id}/pago     <- DEBE IR AL FINAL

CAB Aprobado: 2026-04-14

IMPORTANTE - AISLAMIENTO:
- Todos los endpoints están bajo /api/finanzas/propinas/
- NO interfieren con endpoints existentes
- NO modifican módulos existentes

NOTA: Los endpoints con paths dinámicos (/{id}) DEBEN ir al final para evitar
conflictos con paths específicos como /config, /health, etc.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.security import get_current_user
from .service import PropinasTPVService
from .models import (
    SincronizarRequest,
    SincronizarResponse,
    RegistrarPagoRequest,
    PropinasListResponse,
    ResumenPropinasResponse,
    PropinasConfigCreate
)

logger = logging.getLogger(__name__)

# Router con prefijo específico para aislamiento
router = APIRouter(
    prefix="/finanzas/propinas",
    tags=["Propinas TPV - FASE 1 MVP"]
)


# Dependency para obtener la base de datos
async def get_db():
    """
    Obtiene la conexión a MongoDB.
    Se inyecta desde server.py al registrar el router.
    """
    from server import db
    return db


# ============================================================================
# ENDPOINT DE HEALTH CHECK (PÚBLICO)
# ============================================================================

@router.get(
    "/health",
    summary="Health check del módulo",
    description="Verifica que el módulo esté funcionando correctamente"
)
async def health_check(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        await db.command('ping')
        collections = await db.list_collection_names()
        propinas_control_exists = 'propinas_control' in collections
        propinas_config_exists = 'propinas_config' in collections
        
        return {
            "status": "healthy",
            "module": "propinas_tpv",
            "fase": "MVP FASE 1 - Solo SoftRestaurant",
            "alcance": ["La Estelar", "Cienfuegos", "130 Mérida"],
            "mongodb_connected": True,
            "colecciones": {
                "propinas_control": propinas_control_exists,
                "propinas_config": propinas_config_exists
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# ============================================================================
# ENDPOINTS DE SINCRONIZACIÓN
# ============================================================================

@router.post(
    "/sincronizar",
    response_model=SincronizarResponse,
    summary="Sincronizar propinas desde SoftRestaurant",
    description="""
    Sincroniza propinas de cortes Z desde servidores SoftRestaurant.
    
    FASE 1 MVP - Solo SoftRestaurant:
    - La Estelar
    - Cienfuegos
    - 130 Mérida
    
    Lee concepto 9 (Propinas Pagadas) de movtoscajadetalles.
    Tipo de dato: EXACTO
    """
)
async def sincronizar_propinas(
    request: SincronizarRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        service = PropinasTPVService(db)
        result = await service.sincronizar_propinas(
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
            server_id=request.server_id,
            usuario=current_user.get('email', 'sistema')
        )
        return result
    except Exception as e:
        logger.error(f"Error en sincronización de propinas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/inicializar",
    summary="Inicializar módulo",
    description="""
    Inicializa el módulo de propinas TPV:
    - Crea índices en MongoDB
    - Crea configuración GLOBAL por defecto
    
    Solo debe ejecutarse UNA VEZ.
    """
)
async def inicializar_modulo(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        if current_user.get('role') not in ['admin', 'superadmin', 'Admin']:
            raise HTTPException(status_code=403, detail="Solo administradores pueden inicializar")
        
        service = PropinasTPVService(db)
        await service.inicializar_modulo()
        return {
            "success": True,
            "message": "Módulo de Propinas TPV inicializado correctamente",
            "colecciones_creadas": ["propinas_control", "propinas_config"],
            "indices_creados": ["uk_propinas_corte", "idx_fecha_estado", "idx_server_fecha", "idx_config_alcance"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inicializando módulo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE CONSULTA (paths específicos primero)
# ============================================================================

@router.get(
    "/resumen",
    summary="Resumen de propinas",
    description="Obtiene resumen agregado de propinas por período"
)
async def resumen_propinas(
    fecha_inicio: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    fecha_fin: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        service = PropinasTPVService(db)
        result = await service.obtener_resumen(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            server_id=server_id
        )
        return result
    except Exception as e:
        logger.error(f"Error obteniendo resumen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "",
    summary="Listar propinas",
    description="Obtiene listado de propinas con filtros opcionales"
)
async def listar_propinas(
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio YYYY-MM-DD"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin YYYY-MM-DD"),
    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
    sucursal_id: Optional[str] = Query(None, description="Filtrar por sucursal"),
    estado: Optional[str] = Query(None, description="Filtrar por estado de cuadre"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        service = PropinasTPVService(db)
        result = await service.obtener_propinas(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            server_id=server_id,
            sucursal_id=sucursal_id,
            estado=estado,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Error listando propinas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE CONFIGURACIÓN (paths específicos)
# ============================================================================

@router.get(
    "/config/all",
    summary="Listar todas las configuraciones",
    description="Lista todas las configuraciones de propinas"
)
async def listar_configs(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        service = PropinasTPVService(db)
        configs = await service.listar_configs()
        return {"configs": configs, "total": len(configs)}
    except Exception as e:
        logger.error(f"Error listando configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/config",
    summary="Obtener configuración vigente",
    description="Obtiene la configuración de propinas vigente"
)
async def obtener_config(
    server_id: Optional[str] = Query(None),
    sucursal_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        service = PropinasTPVService(db)
        config = await service.obtener_config(
            server_id=server_id,
            sucursal_id=sucursal_id
        )
        return config
    except Exception as e:
        logger.error(f"Error obteniendo config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/config",
    summary="Crear configuración",
    description="Crea una nueva configuración de propinas"
)
async def crear_config(
    config: PropinasConfigCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        service = PropinasTPVService(db)
        config_id = await service.crear_config(
            config_data=config.dict(),
            usuario=current_user.get('email', 'sistema')
        )
        return {"id": config_id, "message": "Configuración creada"}
    except Exception as e:
        logger.error(f"Error creando config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/config/{config_id}",
    summary="Actualizar configuración",
    description="Actualiza una configuración existente"
)
async def actualizar_config(
    config_id: str,
    config: PropinasConfigCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        service = PropinasTPVService(db)
        success = await service.actualizar_config(
            config_id=config_id,
            config_data=config.dict(),
            usuario=current_user.get('email', 'sistema')
        )
        if not success:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        return {"message": "Configuración actualizada"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS CON PARÁMETROS DINÁMICOS (AL FINAL)
# ============================================================================

@router.get(
    "/{propina_id}",
    summary="Obtener propina por ID",
    description="Obtiene el detalle de una propina específica"
)
async def obtener_propina(
    propina_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        service = PropinasTPVService(db)
        propina = await service.repository.obtener_propina_por_id(propina_id)
        if not propina:
            raise HTTPException(status_code=404, detail="Propina no encontrada")
        return propina
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo propina: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{propina_id}/pago",
    summary="Registrar pago de propinas",
    description="Registra el pago de propinas a meseros y calcula el cuadre"
)
async def registrar_pago(
    propina_id: str,
    request: RegistrarPagoRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        service = PropinasTPVService(db)
        result = await service.registrar_pago(
            propina_id=propina_id,
            monto_pagado=request.monto_pagado,
            metodo=request.metodo.value,
            observaciones=request.observaciones,
            usuario=current_user.get('email', 'sistema')
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registrando pago: {e}")
        raise HTTPException(status_code=500, detail=str(e))
