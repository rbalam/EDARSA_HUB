"""
API Routes para el módulo de Control de Propinas TPV
FASE 1 MVP - Solo SoftRestaurant
PROTEGIDO CON RBAC (Fase 3.1)

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
FASE T2.3 (Mayo 2026): Migrado a server_registry.py (elimina MongoDB db.servers)

IMPORTANTE - AISLAMIENTO:
- Todos los endpoints están bajo /api/finanzas/propinas/
- NO interfieren con endpoints existentes
- NO modifican módulos existentes

NOTA: Los endpoints con paths dinámicos (/{id}) DEBEN ir al final para evitar
conflictos con paths específicos como /config, /health, etc.
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.security import get_current_user, get_user_empresas_permitidas, get_servers_for_empresas
from .service import PropinasTPVService
from .models import (
    SincronizarRequest,
    SincronizarResponse,
    RegistrarPagoRequest,
    PropinasListResponse,
    ResumenPropinasResponse,
    PropinasConfigCreate
)

# FASE T2.3: Importar server_registry para resolver servidores desde EDARSAHUB
from core.server_registry import get_server_by_id, list_operational_servers

logger = logging.getLogger(__name__)


# ============================================================================
# FASE T2.3: Helpers para resolver servidores desde EDARSAHUB
# ============================================================================

def _get_server_from_registry(server_id: str) -> Optional[Dict]:
    """
    Obtiene un servidor por ID desde server_registry (EDARSAHUB).
    
    FASE T2.3: Reemplaza db.servers.find_one()
    """
    server = get_server_by_id(server_id)
    if not server:
        return None
    
    # Adaptar campos para compatibilidad con código existente
    return {
        'id': server.get('id'),
        'name': server.get('name'),
        'host': server.get('host'),
        'port': server.get('port', 1433),
        'database': server.get('database'),
        'username': server.get('username'),
        'password': server.get('password'),
        'system_type': server.get('system_type'),
        'active': server.get('active', True),
        'visible_en_operaciones': server.get('visible_en_operaciones', False),
        '_source': 'EDARSAHUB'
    }


def _list_softrestaurant_servers() -> List[Dict]:
    """
    Lista servidores SoftRestaurant desde server_registry (EDARSAHUB).
    
    FASE T2.3: Reemplaza db.servers.find({system_type: 'SoftRestaurant'})
    """
    all_servers = list_operational_servers()
    sr_servers = []
    
    for s in all_servers:
        system_type = (s.get('system_type') or s.get('system_type_normalized') or '').upper()
        if system_type in ['SOFTRESTAURANT', 'SR']:
            sr_servers.append({
                'id': s.get('id'),
                'name': s.get('name'),
                'host': s.get('host'),
                'port': s.get('port', 1433),
                'database': s.get('database'),
                'username': s.get('username'),
                'password': s.get('password'),
                'system_type': 'SoftRestaurant',
                'active': s.get('active', True),
                '_source': 'EDARSAHUB'
            })
    
    logger.info(f"[PROPINAS][T2.3] Obtenidos {len(sr_servers)} servidores SoftRestaurant desde EDARSAHUB")
    return sr_servers


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


async def get_user_server_ids_permitidos(current_user: Dict[str, Any]) -> List[str]:
    """
    RBAC Fase 3.1: Obtiene los CÓDIGOS de sucursales permitidas para el usuario.
    Retorna lista vacía si el usuario tiene acceso total (admin).
    """
    from server import db
    
    empresas_permitidas = await get_user_empresas_permitidas(current_user)
    if not empresas_permitidas:
        return []  # Sin restricción (admin)
    
    # Obtener códigos de las empresas permitidas
    empresas = await db.empresas.find(
        {'id': {'$in': empresas_permitidas}},
        {'_id': 0, 'codigo': 1, 'nombre': 1}
    ).to_list(100)
    
    # Retornar códigos y nombres para matching flexible
    codigos = []
    for e in empresas:
        if e.get('codigo'):
            codigos.append(e['codigo'].upper())
        if e.get('nombre'):
            codigos.append(e['nombre'].upper())
    
    return codigos


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
# ENDPOINTS DE DIAGNÓSTICO (FASE 1B)
# ============================================================================

@router.get(
    "/detectar-esquema/{server_id}",
    summary="Detectar esquema de un servidor",
    description="""
    FASE 1B: Detecta el esquema de tablas de un servidor SoftRestaurant.
    
    Útil para:
    - Diagnosticar problemas de compatibilidad
    - Validar estructura antes de sincronizar
    - Documentar diferencias entre servidores
    """
)
async def detectar_esquema(
    server_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        # FASE T2.3: Usar server_registry en lugar de db.servers
        server = _get_server_from_registry(server_id)
        if not server:
            raise HTTPException(status_code=404, detail="Servidor no encontrado")
        
        if server.get('system_type') != 'SoftRestaurant':
            raise HTTPException(status_code=400, detail="Solo servidores SoftRestaurant soportados en FASE 1")
        
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


@router.get(
    "/detectar-esquema-todos",
    summary="Detectar esquema de todos los servidores SoftRestaurant",
    description="""
    FASE 1B: Ejecuta detección de esquema en todos los servidores SoftRestaurant.
    
    Retorna:
    - Matriz de compatibilidad
    - Diferencias de esquema entre servidores
    - Recomendación GO/NO GO por servidor
    """
)
async def detectar_esquema_todos(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        # FASE T2.3: Usar server_registry en lugar de db.servers
        servers = _list_softrestaurant_servers()
        
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
                
                # Determinar dictamen
                if schema.get('compatible'):
                    if not schema.get('problemas'):
                        dictamen = "GO"
                    else:
                        dictamen = "GO_CON_RESTRICCIONES"
                else:
                    dictamen = "NO_GO"
                
                resultados.append({
                    'servidor': server.get('name'),
                    'server_id': server.get('id'),
                    'host': f"{server.get('host')}:{server.get('port')}",
                    'database': server.get('database'),
                    'compatible': schema.get('compatible', False),
                    'dictamen': dictamen,
                    'problemas': schema.get('problemas', []),
                    'tablas_detectadas': schema.get('tablas_detectadas', []),
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
        
        # Resumen
        total = len(resultados)
        compatibles = sum(1 for r in resultados if r.get('compatible'))
        go = sum(1 for r in resultados if r.get('dictamen') == 'GO')
        go_restricciones = sum(1 for r in resultados if r.get('dictamen') == 'GO_CON_RESTRICCIONES')
        no_go = sum(1 for r in resultados if r.get('dictamen') == 'NO_GO')
        
        return {
            "success": True,
            "resumen": {
                "total_servidores": total,
                "compatibles": compatibles,
                "go": go,
                "go_con_restricciones": go_restricciones,
                "no_go": no_go
            },
            "servidores": resultados
        }
    except Exception as e:
        logger.error(f"Error detectando esquemas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/preview",
    summary="Preview de propinas sin sincronizar",
    description="""
    FASE 1B: Consulta propinas de un período SIN guardar en MongoDB.
    
    Útil para:
    - Validar que la lectura funciona correctamente
    - Ver datos antes de sincronizar
    - Probar la query defensiva
    """
)
async def preview_propinas(
    fecha_inicio: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    fecha_fin: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        # FASE T2.3: Usar server_registry en lugar de db.servers
        if server_id:
            server = _get_server_from_registry(server_id)
            servers = [server] if server and server.get('system_type') == 'SoftRestaurant' else []
        else:
            servers = _list_softrestaurant_servers()
        
        if not servers:
            return {
                "success": True,
                "message": "No hay servidores SoftRestaurant" + (f" con id {server_id}" if server_id else ""),
                "resultados": []
            }
        
        service = PropinasTPVService(db)
        resultados = []
        
        for server in servers:
            resultado = await service.repository.get_propinas_cortes_defensivo(
                server, fecha_inicio, fecha_fin
            )
            
            # Calcular totales
            cortes = resultado.get('cortes', [])
            total_propinas = sum(c['propinas_totales'] for c in cortes)
            cortes_con_propinas = len([c for c in cortes if c['propinas_totales'] > 0])
            
            resultados.append({
                'servidor': server.get('name'),
                'server_id': server.get('id'),
                'compatible': resultado.get('compatible'),
                'cortes_encontrados': len(cortes),
                'cortes_con_propinas': cortes_con_propinas,
                'total_propinas': total_propinas,
                'comision_2pct': round(total_propinas * 0.02, 2),
                'error': resultado.get('error'),
                'schema': resultado.get('schema'),
                'muestra_cortes': cortes[:5] if cortes else []  # Solo 5 de muestra
            })
        
        return {
            "success": True,
            "periodo": {
                "inicio": fecha_inicio,
                "fin": fecha_fin
            },
            "resultados": resultados
        }
    except Exception as e:
        logger.error(f"Error en preview: {e}")
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
