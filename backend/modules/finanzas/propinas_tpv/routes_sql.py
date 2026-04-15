"""
API Routes SQL para el módulo de Control de Propinas TPV
========================================================
Fecha: 15 de Abril de 2026
CAB: ARQUITECTURA_PROPINAS_TPV_v3.md

ARQUITECTURA:
- SQL Server EDARSA HUB = Persistencia oficial
- MongoDB = Solo cache

ENDPOINTS (SIN CAMBIO DE INTERFAZ):
- POST /api/finanzas/propinas/sincronizar
- GET  /api/finanzas/propinas
- GET  /api/finanzas/propinas/resumen
- GET  /api/finanzas/propinas/health
- GET  /api/finanzas/propinas/config
- POST /api/finanzas/propinas/inicializar-sql
- GET  /api/finanzas/propinas/cache/stats
- POST /api/finanzas/propinas/cache/invalidar
- GET  /api/finanzas/propinas/{id}
- PUT  /api/finanzas/propinas/{id}/pago

IMPORTANTE - AISLAMIENTO:
- NO interfiere con /api/finanzas/tesoreria/*
- NO modifica el tab de Cuadre Z
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.security import get_current_user
from .service_sql import PropinasTPVSQLService
from .service import PropinasTPVService  # Para diagnóstico (schema detector)
from .models import (
    SincronizarRequest,
    SincronizarResponse,
    RegistrarPagoRequest,
    PropinasConfigCreate
)

logger = logging.getLogger(__name__)

# Router con prefijo específico para aislamiento
router_sql = APIRouter(
    prefix="/finanzas/propinas",
    tags=["Propinas TPV - SQL Server"]
)


async def get_db():
    """Obtiene la conexión a MongoDB."""
    from server import db
    return db


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router_sql.get(
    "/health",
    summary="Health check del módulo SQL"
)
async def health_check_sql(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Verifica el estado del módulo con arquitectura SQL + Cache."""
    try:
        # Verificar MongoDB (cache)
        await db.command('ping')
        
        # Verificar SQL Server
        service = PropinasTPVSQLService(db)
        server = await service.sql_repo.get_edarsa_hub_server()
        
        # Verificar cache stats
        cache_stats = await service.obtener_cache_stats()
        
        return {
            "status": "healthy",
            "module": "propinas_tpv",
            "arquitectura": "SQL Server (persistencia) + MongoDB (cache)",
            "fase": "MVP FASE 1 - Solo SoftRestaurant",
            "alcance": ["La Estelar", "Cienfuegos", "130 Mérida"],
            "mongodb_connected": True,
            "sql_server": {
                "connected": server is not None,
                "server_name": server.get('name') if server else None,
                "database": server.get('database') if server else None
            },
            "cache": cache_stats
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# ============================================================================
# INICIALIZACIÓN SQL
# ============================================================================

@router_sql.post(
    "/inicializar-sql",
    summary="Inicializar módulo con tablas SQL",
    description="""
    Inicializa el módulo de propinas TPV:
    - Crea tablas en SQL Server EDARSA HUB
    - Crea índices de cache en MongoDB
    - Inserta configuración GLOBAL por defecto
    
    Solo debe ejecutarse UNA VEZ.
    """
)
async def inicializar_modulo_sql(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        if current_user.get('role') not in ['admin', 'superadmin', 'Admin']:
            raise HTTPException(status_code=403, detail="Solo administradores pueden inicializar")
        
        service = PropinasTPVSQLService(db)
        result = await service.inicializar_modulo()
        
        return {
            "success": result['success'],
            "message": "Módulo de Propinas TPV inicializado con arquitectura SQL + Cache",
            "resultado": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inicializando módulo SQL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SINCRONIZACIÓN
# ============================================================================

@router_sql.post(
    "/sincronizar",
    response_model=SincronizarResponse,
    summary="Sincronizar propinas a SQL Server"
)
async def sincronizar_propinas_sql(
    request: SincronizarRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Sincroniza propinas desde SoftRestaurant a SQL Server EDARSA HUB.
    
    FLUJO:
    1. Lee de SoftRestaurant (query defensiva)
    2. Calcula comisión 2%
    3. Persiste en SQL Server
    4. Invalida cache MongoDB
    """
    try:
        service = PropinasTPVSQLService(db)
        result = await service.sincronizar_propinas(
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
            server_id=request.server_id,
            usuario=current_user.get('email', 'sistema')
        )
        return result
    except Exception as e:
        logger.error(f"Error en sincronización SQL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONSULTAS
# ============================================================================

@router_sql.get(
    "/resumen",
    summary="Resumen de propinas desde SQL"
)
async def resumen_propinas_sql(
    fecha_inicio: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    fecha_fin: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    server_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Obtiene resumen agregado desde SQL Server (con cache)."""
    try:
        service = PropinasTPVSQLService(db)
        result = await service.obtener_resumen(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            server_id=server_id
        )
        return result
    except Exception as e:
        logger.error(f"Error obteniendo resumen SQL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router_sql.get(
    "",
    summary="Listar propinas desde SQL"
)
async def listar_propinas_sql(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    server_id: Optional[str] = Query(None),
    sucursal_id: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Obtiene listado de propinas desde SQL Server (con cache)."""
    try:
        service = PropinasTPVSQLService(db)
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
        logger.error(f"Error listando propinas SQL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

@router_sql.get(
    "/config",
    summary="Obtener configuración desde SQL"
)
async def obtener_config_sql(
    server_id: Optional[str] = Query(None),
    sucursal_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Obtiene configuración vigente desde SQL Server (con cache)."""
    try:
        service = PropinasTPVSQLService(db)
        config = await service.obtener_config(
            server_id=server_id,
            sucursal_id=sucursal_id
        )
        return config
    except Exception as e:
        logger.error(f"Error obteniendo config SQL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CACHE (Nuevos endpoints para administración)
# ============================================================================

@router_sql.get(
    "/cache/stats",
    summary="Estadísticas de cache"
)
async def cache_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Obtiene estadísticas del cache MongoDB."""
    try:
        service = PropinasTPVSQLService(db)
        return await service.obtener_cache_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_sql.post(
    "/cache/invalidar",
    summary="Invalidar cache"
)
async def invalidar_cache(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Invalida todo el cache de propinas."""
    try:
        if current_user.get('role') not in ['admin', 'superadmin', 'Admin']:
            raise HTTPException(status_code=403, detail="Solo administradores")
        
        service = PropinasTPVSQLService(db)
        return await service.invalidar_cache_completo()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DIAGNÓSTICO (Usa el servicio original para leer de SoftRestaurant)
# ============================================================================

@router_sql.get(
    "/detectar-esquema/{server_id}",
    summary="Detectar esquema de servidor"
)
async def detectar_esquema(
    server_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Detecta el esquema de tablas de un servidor SoftRestaurant."""
    try:
        server = await db.servers.find_one({'id': server_id}, {'_id': 0})
        if not server:
            raise HTTPException(status_code=404, detail="Servidor no encontrado")
        
        if server.get('system_type') != 'SoftRestaurant':
            raise HTTPException(status_code=400, detail="Solo servidores SoftRestaurant soportados")
        
        service = PropinasTPVService(db)
        schema = await service.repository.detectar_esquema_servidor(server)
        
        return {
            "success": True,
            "server_name": server.get('name'),
            "schema": schema
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detectando esquema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router_sql.get(
    "/detectar-esquema-todos",
    summary="Detectar esquema de todos los servidores"
)
async def detectar_esquema_todos(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Detecta esquema en todos los servidores SoftRestaurant."""
    try:
        servers = await db.servers.find(
            {'system_type': 'SoftRestaurant'},
            {'_id': 0}
        ).to_list(length=100)
        
        if not servers:
            return {
                "success": True,
                "message": "No hay servidores SoftRestaurant configurados",
                "servidores": []
            }
        
        service = PropinasTPVService(db)
        resultados = []
        
        for server in servers:
            try:
                schema = await service.repository.detectar_esquema_servidor(server)
                
                if schema.get('compatible'):
                    dictamen = "GO" if not schema.get('problemas') else "GO_CON_RESTRICCIONES"
                else:
                    dictamen = "NO_GO"
                
                resultados.append({
                    'servidor': server.get('name'),
                    'server_id': server.get('id'),
                    'compatible': schema.get('compatible', False),
                    'dictamen': dictamen,
                    'problemas': schema.get('problemas', []),
                    'schema_detalle': schema
                })
            except Exception as e:
                resultados.append({
                    'servidor': server.get('name'),
                    'server_id': server.get('id'),
                    'compatible': False,
                    'dictamen': "NO_GO",
                    'error': str(e)
                })
        
        total = len(resultados)
        compatibles = sum(1 for r in resultados if r.get('compatible'))
        
        return {
            "success": True,
            "resumen": {
                "total_servidores": total,
                "compatibles": compatibles,
                "go": sum(1 for r in resultados if r.get('dictamen') == 'GO'),
                "no_go": sum(1 for r in resultados if r.get('dictamen') == 'NO_GO')
            },
            "servidores": resultados
        }
    except Exception as e:
        logger.error(f"Error detectando esquemas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router_sql.get(
    "/preview",
    summary="Preview de propinas (sin persistir)"
)
async def preview_propinas(
    fecha_inicio: str = Query(...),
    fecha_fin: str = Query(...),
    server_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Consulta propinas de SoftRestaurant sin guardar."""
    try:
        filtro = {'system_type': 'SoftRestaurant'}
        if server_id:
            filtro['id'] = server_id
        
        servers = await db.servers.find(filtro, {'_id': 0}).to_list(length=100)
        
        if not servers:
            return {
                "success": True,
                "message": "No hay servidores SoftRestaurant",
                "resultados": []
            }
        
        service = PropinasTPVService(db)
        resultados = []
        
        for server in servers:
            resultado = await service.repository.get_propinas_cortes_defensivo(
                server, fecha_inicio, fecha_fin
            )
            
            cortes = resultado.get('cortes', [])
            total_propinas = sum(c['propinas_totales'] for c in cortes)
            
            resultados.append({
                'servidor': server.get('name'),
                'server_id': server.get('id'),
                'compatible': resultado.get('compatible'),
                'cortes_encontrados': len(cortes),
                'cortes_con_propinas': len([c for c in cortes if c['propinas_totales'] > 0]),
                'total_propinas': total_propinas,
                'comision_2pct': round(total_propinas * 0.02, 2),
                'error': resultado.get('error'),
                'muestra_cortes': cortes[:5] if cortes else []
            })
        
        return {
            "success": True,
            "periodo": {"inicio": fecha_inicio, "fin": fecha_fin},
            "resultados": resultados
        }
    except Exception as e:
        logger.error(f"Error en preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS CON PARÁMETROS DINÁMICOS (AL FINAL)
# ============================================================================

@router_sql.get(
    "/{propina_id}",
    summary="Obtener propina por ID"
)
async def obtener_propina_sql(
    propina_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Obtiene detalle de una propina desde SQL Server."""
    try:
        service = PropinasTPVSQLService(db)
        propina = await service.obtener_propina_por_id(propina_id)
        if not propina:
            raise HTTPException(status_code=404, detail="Propina no encontrada")
        return propina
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo propina: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router_sql.put(
    "/{propina_id}/pago",
    summary="Registrar pago de propinas"
)
async def registrar_pago_sql(
    propina_id: str,
    request: RegistrarPagoRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Registra pago de propinas en SQL Server."""
    try:
        service = PropinasTPVSQLService(db)
        result = await service.registrar_pago(
            propina_id=propina_id,
            monto_pagado=request.monto_pagado,
            metodo=request.metodo.value,
            observaciones=request.observaciones,
            usuario_id=current_user.get('id', 'unknown'),
            usuario_email=current_user.get('email', 'sistema')
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registrando pago: {e}")
        raise HTTPException(status_code=500, detail=str(e))
