"""
Servicio de Sincronización de Almacenes
========================================

PROPÓSITO:
Sincroniza almacenes desde sistemas origen (SoftRestaurant/MPRO) al catálogo local MongoDB.
Reutiliza queries y patrones ya probados del sistema.

PRINCIPIOS:
1. El endpoint solo pasa unidad_negocio_id y usuario_sync
2. Este service resuelve internamente el contexto técnico
3. Reutiliza queries existentes de automatizacion/queries_*.py
4. Usa SourceQueryResult para manejo estandarizado de errores
5. NO consulta SQL desde UI - este service es el único punto de sincronización

Fecha: Abril 2026
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.source_resolver import QueryStatus, SourceQueryResult, classify_sql_error
from core.db import execute_sql_query
from core.context_resolver import resolve_unidad_context

# Reutilizar queries existentes
from modules.automatizacion.queries_soft import QUERY_ALMACENES as QUERY_ALMACENES_SOFT
from modules.automatizacion.queries_mpro import QUERY_ALMACENES_SUCURSAL as QUERY_ALMACENES_MPRO

logger = logging.getLogger(__name__)


@dataclass
class SyncAlmacenesResult:
    """
    Resultado de sincronización de almacenes con metadatos útiles.
    Extiende el concepto de SourceQueryResult con datos específicos de sync.
    """
    status: QueryStatus
    unidad_negocio_id: str
    unidad_negocio_nombre: str = ""
    
    # Metadatos de sincronización
    leidos_origen: int = 0
    insertados: int = 0
    actualizados: int = 0
    desactivados: int = 0
    
    # Para compatibilidad con respuesta API
    message: str = ""
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    @property
    def total_sincronizados(self) -> int:
        return self.insertados + self.actualizados
    
    @property
    def success(self) -> bool:
        return self.status.is_success if hasattr(self.status, 'is_success') else self.status in (QueryStatus.SUCCESS_WITH_DATA, QueryStatus.SUCCESS_EMPTY)
    
    def to_dict(self) -> Dict[str, Any]:
        is_success = self.status in (QueryStatus.SUCCESS_WITH_DATA, QueryStatus.SUCCESS_EMPTY)
        return {
            "success": is_success,
            "status": self.status.value,
            "unidad_negocio_id": self.unidad_negocio_id,
            "unidad_negocio_nombre": self.unidad_negocio_nombre,
            "leidos_origen": self.leidos_origen,
            "insertados": self.insertados,
            "actualizados": self.actualizados,
            "desactivados": self.desactivados,
            "sincronizados": self.total_sincronizados,
            "message": self.message,
            "error_message": self.error_message,
            "timestamp": self.timestamp
        }


async def sincronizar_almacenes_desde_origen(
    db,
    user: Dict[str, Any],
    unidad_negocio_id: str,
    usuario_sync: str
) -> SyncAlmacenesResult:
    """
    Sincroniza almacenes desde el sistema origen al catálogo local.
    
    Este service resuelve internamente:
    - server_id, system_type, sucursal_origen_id via context_resolver
    - Selecciona la query correcta según el sistema
    - Ejecuta la consulta SQL
    - Persiste en MongoDB (almacenes_catalogo)
    
    Args:
        db: Conexión a MongoDB
        user: Usuario autenticado (para validación RBAC en context_resolver)
        unidad_negocio_id: ID de la unidad de negocio a sincronizar
        usuario_sync: Email del usuario que ejecuta la sincronización
        
    Returns:
        SyncAlmacenesResult con metadatos completos de la operación
    """
    result = SyncAlmacenesResult(
        status=QueryStatus.UNKNOWN_ERROR,
        unidad_negocio_id=unidad_negocio_id
    )
    
    try:
        # =====================================================================
        # PASO 1: Resolver contexto técnico internamente
        # =====================================================================
        try:
            context = await resolve_unidad_context(user, unidad_negocio_id)
        except Exception as e:
            result.status = QueryStatus.UNKNOWN_ERROR
            result.error_message = f"No se pudo resolver contexto de la unidad: {str(e)}"
            result.message = result.error_message
            logger.warning(f"[Sync Almacenes] Error resolviendo contexto {unidad_negocio_id}: {e}")
            return result
        
        server_id = context.get("server_id")
        system_type = context.get("system_type")
        sucursal_origen_id = context.get("sucursal_origen_id")
        result.unidad_negocio_nombre = context.get("unidad_nombre", "")
        
        if not server_id:
            result.status = QueryStatus.UNKNOWN_ERROR
            result.error_message = "Unidad sin servidor configurado"
            result.message = result.error_message
            return result
        
        # =====================================================================
        # PASO 2: Obtener credenciales del servidor
        # FASE P1.4-F (Dic 2025): Migrado de MongoDB db.servers a server_registry
        # FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
        # =====================================================================
        from core.server_registry import get_server_connection_info_with_secrets
        # ANTES: server = await db.servers.find_one({"id": server_id}, {"_id": 0})
        server = get_server_connection_info_with_secrets(server_id)
        if not server:
            result.status = QueryStatus.UNKNOWN_ERROR
            result.error_message = "Servidor no encontrado en configuración"
            result.message = result.error_message
            return result
        
        # =====================================================================
        # PASO 3: Seleccionar query según sistema origen
        # =====================================================================
        if system_type == "SoftRestaurant":
            query = QUERY_ALMACENES_SOFT
        elif system_type == "MPRO":
            if not sucursal_origen_id:
                result.status = QueryStatus.UNKNOWN_ERROR
                result.error_message = "MPRO requiere sucursal_origen_id configurado"
                result.message = result.error_message
                return result
            # Reemplazar parámetro en query MPRO
            query = QUERY_ALMACENES_MPRO.replace(":sucursal_id", f"'{sucursal_origen_id}'")
        else:
            result.status = QueryStatus.UNKNOWN_ERROR
            result.error_message = f"Tipo de sistema no soportado: {system_type}"
            result.message = result.error_message
            return result
        
        logger.info(f"[Sync Almacenes] Ejecutando query {system_type} para {unidad_negocio_id}")
        
        # =====================================================================
        # PASO 4: Ejecutar consulta SQL
        # =====================================================================
        try:
            almacenes_origen = execute_sql_query(
                server['host'],
                server['port'],
                server['database'],
                server['username'],
                server['password'],
                query
            )
            
            if almacenes_origen is None:
                almacenes_origen = []
            
            result.leidos_origen = len(almacenes_origen)
            logger.info(f"[Sync Almacenes] Leídos {result.leidos_origen} almacenes de {system_type}")
            
        except Exception as e:
            error_status = classify_sql_error(e)
            result.status = error_status
            result.error_message = f"Error consultando servidor externo: {str(e)}"
            result.message = result.error_message
            logger.error(f"[Sync Almacenes] Error SQL {unidad_negocio_id}: {e}")
            return result
        
        # =====================================================================
        # PASO 5: Sincronizar al catálogo local MongoDB
        # =====================================================================
        now = datetime.now(timezone.utc).isoformat()
        almacenes_collection = db.almacenes_catalogo
        
        # IDs de almacenes que vienen del origen (para detectar desactivados)
        ids_origen = set()
        
        for alm in almacenes_origen:
            # Normalizar campos según sistema
            if system_type == "SoftRestaurant":
                alm_id = str(alm.get("almacen_id", ""))
                alm_nombre = alm.get("almacen_nombre", "")
            else:  # MPRO
                alm_id = str(alm.get("almacen_id", ""))
                alm_nombre = alm.get("almacen_nombre", "")
            
            if not alm_id:
                continue
            
            ids_origen.add(alm_id)
            
            # Verificar si existe
            existente = await almacenes_collection.find_one({
                "unidad_negocio_id": unidad_negocio_id,
                "id": alm_id
            })
            
            if existente:
                # Actualizar si cambió el nombre o estaba inactivo
                if existente.get("nombre") != alm_nombre or not existente.get("activo", True):
                    await almacenes_collection.update_one(
                        {"unidad_negocio_id": unidad_negocio_id, "id": alm_id},
                        {"$set": {
                            "nombre": alm_nombre,
                            "activo": True,
                            "fecha_sync": now,
                            "usuario_sync": usuario_sync
                        }}
                    )
                    result.actualizados += 1
            else:
                # Insertar nuevo
                await almacenes_collection.insert_one({
                    "id": alm_id,
                    "unidad_negocio_id": unidad_negocio_id,
                    "nombre": alm_nombre,
                    "codigo": alm_id,
                    "activo": True,
                    "fecha_creacion": now,
                    "fecha_sync": now,
                    "usuario_sync": usuario_sync
                })
                result.insertados += 1
        
        # =====================================================================
        # PASO 6: Desactivar almacenes que ya no existen en origen
        # =====================================================================
        if ids_origen:
            # Buscar almacenes activos que no están en el origen
            desactivar_result = await almacenes_collection.update_many(
                {
                    "unidad_negocio_id": unidad_negocio_id,
                    "id": {"$nin": list(ids_origen)},
                    "activo": True
                },
                {"$set": {
                    "activo": False,
                    "fecha_sync": now,
                    "usuario_sync": usuario_sync
                }}
            )
            result.desactivados = desactivar_result.modified_count
        
        # =====================================================================
        # PASO 7: Resultado exitoso
        # =====================================================================
        result.status = QueryStatus.SUCCESS_WITH_DATA if result.total_sincronizados > 0 else QueryStatus.SUCCESS_EMPTY
        result.message = (
            f"Sincronizados {result.total_sincronizados} almacenes para {result.unidad_negocio_nombre}"
            f" ({result.insertados} nuevos, {result.actualizados} actualizados"
            f"{f', {result.desactivados} desactivados' if result.desactivados else ''})"
        )
        
        logger.info(f"[Sync Almacenes] {result.message}")
        return result
        
    except Exception as e:
        result.status = QueryStatus.UNKNOWN_ERROR
        result.error_message = f"Error inesperado: {str(e)}"
        result.message = result.error_message
        logger.exception(f"[Sync Almacenes] Error inesperado sincronizando {unidad_negocio_id}")
        return result
