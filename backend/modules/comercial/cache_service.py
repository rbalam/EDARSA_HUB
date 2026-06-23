from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
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

def init_cache_service(database=None):
    """
    DEPRECADO: MongoDB ya no se usa.
    El módulo comercial está en proceso de migración a SQL.
    """
    global _db
    _db = database
    import logging
    logging.warning("[COMERCIAL] Cache service - MongoDB deprecado, funcionalidad limitada")

def get_db():
    """
    DEPRECADO: MongoDB ya no se usa.
    Retorna None - las funciones deben manejar este caso.
    """
    global _db
    if _db is None:
        import logging
        logging.debug("[COMERCIAL] get_db() - MongoDB deprecado")
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


# ============================================================================
# SQL-FIRST cache backend: dbo.Sync_Response_Cache
# ============================================================================

def _sql_cache_hash(cache_key: str) -> str:
    import hashlib
    return hashlib.sha256(str(cache_key).encode("utf-8")).hexdigest()


def _sql_conn():
    from modules.compras.sync_service import get_edarsahub_connection
    return get_edarsahub_connection()


def _sql_next_cache_id(cur) -> int:
    cur.execute("SELECT ISNULL(MAX(id),0)+1 AS NextID FROM dbo.Sync_Response_Cache WITH (UPDLOCK, HOLDLOCK)")
    row = cur.fetchone()
    return int(row["NextID"] if isinstance(row, dict) else row[0])


def _json_dumps(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, default=str)


def _json_loads(txt):
    import json
    if not txt:
        return None
    return json.loads(txt)


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
    h = _sql_cache_hash(cache_key)
    conn = _sql_conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("""
            SELECT ResponsePayload
            FROM dbo.Sync_Response_Cache
            WHERE RequestHash=%s
              AND ServiceSource='comercial_cache'
              AND (ExpiresAt IS NULL OR ExpiresAt > GETDATE())
        """, (h,))
        row = cur.fetchone()
        if not row:
            return None

        cur.execute("""
            UPDATE dbo.Sync_Response_Cache
            SET HitCount = ISNULL(HitCount,0) + 1
            WHERE RequestHash=%s AND ServiceSource='comercial_cache'
        """, (h,))
        conn.commit()

        payload = _json_loads(row.get("ResponsePayload"))
        if isinstance(payload, dict) and "data" in payload:
            return payload.get("data")
        return payload
    finally:
        conn.close()

async def save_to_cache(
    cache_key: str,
    data: Any,
    endpoint: str,
    server_name: str = "",
    server_type: str = "",
    ttl_hours: int = 24
) -> None:
    h = _sql_cache_hash(cache_key)
    payload = {
        "cache_key": cache_key,
        "data": data,
        "endpoint": endpoint,
        "server_name": server_name,
        "server_type": server_type,
    }
    conn = _sql_conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("""
            SELECT id FROM dbo.Sync_Response_Cache
            WHERE RequestHash=%s AND ServiceSource='comercial_cache'
        """, (h,))
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE dbo.Sync_Response_Cache
                SET RequestPayload=%s,
                    ResponsePayload=%s,
                    CacheDurationMinutes=%s,
                    CreatedAt=GETDATE(),
                    ExpiresAt=DATEADD(hour, %s, GETDATE())
                WHERE RequestHash=%s AND ServiceSource='comercial_cache'
            """, (cache_key, _json_dumps(payload), int(ttl_hours) * 60, int(ttl_hours), h))
        else:
            cur.execute("""
                INSERT INTO dbo.Sync_Response_Cache
                (id, RequestHash, ServiceSource, RequestPayload, ResponsePayload,
                 TokenCostFraction, CacheDurationMinutes, CreatedAt, ExpiresAt, HitCount)
                VALUES (%s,%s,'comercial_cache',%s,%s,0,%s,GETDATE(),DATEADD(hour,%s,GETDATE()),0)
            """, (_sql_next_cache_id(cur), h, cache_key, _json_dumps(payload), int(ttl_hours) * 60, int(ttl_hours)))
        conn.commit()
    finally:
        conn.close()

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
    return {"success": True, "message": "Sync_Response_Cache SQL-first"}

async def cleanup_expired_cache(max_age_hours: int = 24) -> Dict:
    conn = _sql_conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("SELECT COUNT(*) AS total FROM dbo.Sync_Response_Cache WHERE ServiceSource='comercial_cache'")
        before = int((cur.fetchone() or {}).get("total") or 0)

        cur.execute("""
            DELETE FROM dbo.Sync_Response_Cache
            WHERE ServiceSource='comercial_cache'
              AND (
                    (ExpiresAt IS NOT NULL AND ExpiresAt < GETDATE())
                 OR CreatedAt < DATEADD(hour, -%s, GETDATE())
              )
        """, (max_age_hours,))
        deleted = cur.rowcount if cur.rowcount is not None else 0

        cur.execute("SELECT COUNT(*) AS total FROM dbo.Sync_Response_Cache WHERE ServiceSource='comercial_cache'")
        after = int((cur.fetchone() or {}).get("total") or 0)

        conn.commit()
        return {"success": True, "total_before": before, "deleted": deleted, "total_after": after}
    finally:
        conn.close()

async def get_cache_stats() -> Dict:
    conn = _sql_conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("""
            SELECT COUNT(*) AS total_entries,
                   ISNULL(SUM(ISNULL(HitCount,0)),0) AS total_hits,
                   MIN(CreatedAt) AS oldest,
                   MAX(CreatedAt) AS newest
            FROM dbo.Sync_Response_Cache
            WHERE ServiceSource='comercial_cache'
        """)
        row = cur.fetchone() or {}
        return {
            "total_entries": int(row.get("total_entries") or 0),
            "total_hits": int(row.get("total_hits") or 0),
            "oldest": row.get("oldest"),
            "newest": row.get("newest"),
            "backend": "sql",
            "table": "Sync_Response_Cache",
        }
    finally:
        conn.close()

