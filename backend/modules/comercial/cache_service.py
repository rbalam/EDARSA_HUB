"""
Servicio Central de Cache para Módulo Comercial
===============================================

Implementa cache controlado con las siguientes reglas:
- Cache NO es fuente de verdad
- Siempre intentar primero la fuente real SQL/API
- Solo usar cache como fallback si la fuente falla o hay timeout
- Si la fuente real responde, actualizar cache
- Si la fuente falla y existe cache válido, devolver con status degradado
- Si no existe cache, devolver estructura vacía controlada

FASE 3A.3: Cache keys incluyen system_type_normalized para evitar colisiones
entre SoftRestaurant y MPRO.

Autor: Arquitectura Senior
Fecha: 2026-04-20
Actualizado: FASE 3A.3 - Cache keys con system_type_normalized
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, Tuple

# Importar db desde server.py (motor async client)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# FASE 3A.3: Import de helpers centralizados de system_type
from core.system_type_utils import normalize_system_type

# Referencia global a MongoDB (evita circular import con server.py)
_db = None

def init_cache_service(database):
    """Inicializa el servicio de cache con la conexión a MongoDB."""
    global _db
    _db = database

def get_db():
    """Obtiene la conexión a MongoDB."""
    global _db
    if _db is None:
        # Fallback: import tardío solo si no se inicializó
        from server import db
        _db = db
    return _db

# TTLs configurables por endpoint (en segundos)
CACHE_TTL = {
    "dashboard": 180,       # 3 minutos
    "reporte_pax": 180,     # 3 minutos
    "ticket_perfecto": 300, # 5 minutos
    "metas": 900,           # 15 minutos
    "ventas_tiempo": 180,   # 3 minutos
    "mesas": 300,           # 5 minutos
}

# Estados de respuesta estándar
class SourceStatus:
    SUCCESS = "SUCCESS"
    NO_DATA = "NO_DATA"
    DEGRADED_CACHE = "DEGRADED_CACHE"
    SOURCE_UNREACHABLE = "SOURCE_UNREACHABLE"
    ERROR = "ERROR"


def build_cache_key(
    modulo: str,
    endpoint: str,
    server_id: str,
    sucursal: str = "",
    fecha: str = "",
    system_type: str = "",  # FASE 3A.3: Agregado parámetro system_type
    **extra_params
) -> str:
    """
    Construye clave de cache con granularidad por módulo + endpoint + empresa + sucursal + fecha + system_type + filtros.
    
    FASE 3A.3: Incluye system_type_normalized para evitar colisiones entre
    SoftRestaurant y MPRO. Esto garantiza que:
    - SoftRestaurant NO comparta caché con MPRO
    - MPRO NO comparta caché con SoftRestaurant
    - Variantes de system_type (MPRO, ManagmentPro, etc.) se normalicen
    
    Ejemplo: comercial:dashboard:server123:suc001:MANAGEMENTPRO:2026-04-20:periodo=mes
    """
    # FASE 3A.3: Normalizar system_type para evitar variantes
    system_type_normalized = normalize_system_type(system_type) if system_type else "UNKNOWN"
    
    base_key = f"comercial:{endpoint}:{server_id}"
    
    if sucursal:
        base_key += f":{sucursal}"
    else:
        base_key += ":all"
    
    # FASE 3A.3: Incluir system_type_normalized ANTES de la fecha
    base_key += f":{system_type_normalized}"
    
    if fecha:
        base_key += f":{fecha}"
    else:
        base_key += f":{datetime.now().strftime('%Y-%m-%d')}"
    
    # Agregar parámetros extra ordenados
    if extra_params:
        sorted_params = sorted(extra_params.items())
        params_str = ":".join(f"{k}={v}" for k, v in sorted_params if v)
        if params_str:
            base_key += f":{params_str}"
    
    logging.debug(f"[COMERCIAL][CACHE_KEY_BUILT] {base_key}")
    return base_key


async def get_cached_response(cache_key: str) -> Optional[Dict]:
    """
    Obtiene respuesta cacheada si existe y no ha expirado.
    
    Returns:
        Dict con 'data', 'cached_at', 'ttl' si existe cache válido
        None si no existe o expiró
    """
    try:
        db = get_db()
        cached = await db.comercial_cache.find_one({"cache_key": cache_key})
        
        if not cached:
            return None
        
        cached_at = cached.get("cached_at")
        ttl = cached.get("ttl", 300)
        
        if cached_at:
            # Verificar si expiró
            if isinstance(cached_at, str):
                cached_dt = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
            else:
                cached_dt = cached_at
            
            now = datetime.now(timezone.utc)
            if cached_dt.tzinfo is None:
                cached_dt = cached_dt.replace(tzinfo=timezone.utc)
            
            age_seconds = (now - cached_dt).total_seconds()
            
            if age_seconds > ttl:
                logging.info(f"Cache expirado para {cache_key} (edad: {age_seconds}s, TTL: {ttl}s)")
                return None
        
        return {
            "data": cached.get("data"),
            "cached_at": cached.get("cached_at"),
            "ttl": ttl,
            "server_name": cached.get("server_name"),
            "server_type": cached.get("server_type")
        }
    
    except Exception as e:
        logging.warning(f"Error obteniendo cache para {cache_key}: {e}")
        return None


async def save_to_cache(
    cache_key: str,
    data: Dict,
    endpoint: str,
    server_name: str = "",
    server_type: str = ""
) -> bool:
    """
    Guarda respuesta en cache.
    
    Returns:
        True si se guardó correctamente
    """
    try:
        db = get_db()
        ttl = CACHE_TTL.get(endpoint, 300)
        
        cache_doc = {
            "cache_key": cache_key,
            "data": data,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl": ttl,
            "endpoint": endpoint,
            "server_name": server_name,
            "server_type": server_type,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.comercial_cache.update_one(
            {"cache_key": cache_key},
            {"$set": cache_doc},
            upsert=True
        )
        
        logging.debug(f"Cache guardado para {cache_key} (TTL: {ttl}s)")
        return True
    
    except Exception as e:
        logging.warning(f"Error guardando cache para {cache_key}: {e}")
        return False


def build_envelope_response(
    source_status: str,
    data: Any,
    server_name: str = "",
    server_type: str = "",
    cache_used: bool = False,
    last_successful_sync: str = None,
    fuentes_consultadas: list = None,
    source_message: str = "",
    **extra_fields
) -> Dict:
    """
    Construye envelope de respuesta homologado.
    
    Campos estándar:
    - source_status: SUCCESS | NO_DATA | DEGRADED_CACHE | SOURCE_UNREACHABLE | ERROR
    - source_message: Mensaje descriptivo del estado
    - fuentes_consultadas: Lista de fuentes que se intentaron consultar
    - cache_used: Si se usó cache como fallback
    - last_successful_sync: Timestamp de última sincronización exitosa
    - data: Los datos de la respuesta
    """
    envelope = {
        "source_status": source_status,
        "source_message": source_message or _get_default_message(source_status, server_name),
        "fuentes_consultadas": fuentes_consultadas or [server_name] if server_name else [],
        "cache_used": cache_used,
        "last_successful_sync": last_successful_sync,
        "server_name": server_name,
        "server_type": server_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Agregar campos extra
    envelope.update(extra_fields)
    
    return envelope


def _get_default_message(status: str, server_name: str = "") -> str:
    """Genera mensaje descriptivo por defecto según el status."""
    messages = {
        SourceStatus.SUCCESS: f"Datos obtenidos correctamente de {server_name}" if server_name else "Datos obtenidos correctamente",
        SourceStatus.NO_DATA: f"Conexión exitosa a {server_name} pero no hay datos en el período seleccionado" if server_name else "No hay datos en el período seleccionado",
        SourceStatus.DEGRADED_CACHE: f"Fuente {server_name} no disponible. Mostrando datos de cache" if server_name else "Fuente no disponible. Mostrando datos de cache",
        SourceStatus.SOURCE_UNREACHABLE: f"No se pudo conectar a {server_name}" if server_name else "Fuente de datos no disponible",
        SourceStatus.ERROR: "Error interno al procesar la solicitud"
    }
    return messages.get(status, "Estado desconocido")


async def execute_with_cache_fallback(
    cache_key: str,
    endpoint: str,
    query_func,
    server_name: str = "",
    server_type: str = "",
    empty_response_factory = None
) -> Tuple[Dict, str, bool]:
    """
    Ejecuta una función de query con fallback a cache.
    
    Args:
        cache_key: Clave de cache
        endpoint: Nombre del endpoint para TTL
        query_func: Función async que ejecuta la query real
        server_name: Nombre del servidor
        server_type: Tipo de servidor
        empty_response_factory: Función que genera respuesta vacía por defecto
    
    Returns:
        Tuple de (data, source_status, cache_used)
    """
    try:
        # Intentar query real primero
        data = await query_func()
        
        if data is not None:
            # Query exitosa - guardar en cache
            await save_to_cache(cache_key, data, endpoint, server_name, server_type)
            
            # Determinar si hay datos o está vacío
            has_data = _check_has_data(data)
            status = SourceStatus.SUCCESS if has_data else SourceStatus.NO_DATA
            
            return data, status, False
    
    except Exception as e:
        logging.warning(f"Error en query para {endpoint}: {e}")
    
    # Query falló - intentar cache
    cached = await get_cached_response(cache_key)
    
    if cached and cached.get("data"):
        logging.info(f"Usando cache para {cache_key}")
        return cached["data"], SourceStatus.DEGRADED_CACHE, True
    
    # Sin cache - devolver estructura vacía
    empty_data = empty_response_factory() if empty_response_factory else {}
    return empty_data, SourceStatus.SOURCE_UNREACHABLE, False


def _check_has_data(data: Any) -> bool:
    """Verifica si la respuesta tiene datos reales."""
    if data is None:
        return False
    if isinstance(data, dict):
        # Verificar si tiene listas no vacías o valores numéricos > 0
        for k, v in data.items():
            if isinstance(v, list) and len(v) > 0:
                return True
            if isinstance(v, (int, float)) and v > 0:
                return True
            if isinstance(v, dict) and _check_has_data(v):
                return True
    if isinstance(data, list) and len(data) > 0:
        return True
    return False


# Colección de cache necesaria - crear índice al importar
async def ensure_cache_indexes():
    """Asegura que existen los índices necesarios para el cache."""
    try:
        db = get_db()
        await db.comercial_cache.create_index("cache_key", unique=True)
        await db.comercial_cache.create_index("cached_at")
        logging.info("Índices de cache comercial verificados")
    except Exception as e:
        logging.warning(f"Error creando índices de cache: {e}")


async def cleanup_expired_cache(max_age_hours: int = 24) -> Dict:
    """
    Limpia entradas de cache expiradas.
    
    Args:
        max_age_hours: Máximo de horas para considerar un cache como expirado (default 24h)
    
    Returns:
        Dict con estadísticas de limpieza
    """
    try:
        db = get_db()
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        # Contar antes de eliminar
        total_before = await db.comercial_cache.count_documents({})
        
        # Eliminar caches antiguos basados en cached_at
        result = await db.comercial_cache.delete_many({
            "cached_at": {"$lt": cutoff_time.isoformat()}
        })
        
        # También eliminar por updated_at si cached_at no existe
        result2 = await db.comercial_cache.delete_many({
            "updated_at": {"$lt": cutoff_time.isoformat()},
            "cached_at": {"$exists": False}
        })
        
        total_after = await db.comercial_cache.count_documents({})
        deleted_count = result.deleted_count + result2.deleted_count
        
        logging.info(f"Cache cleanup: {deleted_count} entradas eliminadas (antes: {total_before}, después: {total_after})")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "total_before": total_before,
            "total_after": total_after,
            "cutoff_time": cutoff_time.isoformat(),
            "max_age_hours": max_age_hours
        }
    
    except Exception as e:
        logging.error(f"Error en limpieza de cache: {e}")
        return {
            "success": False,
            "error": str(e),
            "deleted_count": 0
        }


async def get_cache_stats() -> Dict:
    """
    Obtiene estadísticas del cache.
    
    Returns:
        Dict con estadísticas
    """
    try:
        db = get_db()
        
        total_entries = await db.comercial_cache.count_documents({})
        
        # Obtener distribución por endpoint
        pipeline = [
            {"$group": {"_id": "$endpoint", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_endpoint = []
        async for doc in db.comercial_cache.aggregate(pipeline):
            by_endpoint.append({"endpoint": doc["_id"], "count": doc["count"]})
        
        # Obtener el más antiguo y más reciente
        oldest = await db.comercial_cache.find_one(sort=[("cached_at", 1)])
        newest = await db.comercial_cache.find_one(sort=[("cached_at", -1)])
        
        return {
            "total_entries": total_entries,
            "by_endpoint": by_endpoint,
            "oldest_entry": oldest.get("cached_at") if oldest else None,
            "newest_entry": newest.get("cached_at") if newest else None
        }
    
    except Exception as e:
        logging.error(f"Error obteniendo stats de cache: {e}")
        return {
            "total_entries": 0,
            "error": str(e)
        }


__all__ = [
    'SourceStatus',
    'build_cache_key',
    'get_cached_response',
    'save_to_cache',
    'build_envelope_response',
    'execute_with_cache_fallback',
    'ensure_cache_indexes',
    'cleanup_expired_cache',
    'get_cache_stats',
    'CACHE_TTL'
]
