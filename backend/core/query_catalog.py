"""
EDARSA HUB - Catálogo Central de Queries
========================================
P2-21: Centralización de queries SQL por sistema.

OBJETIVO:
- Eliminar SQL hardcodeado de módulos
- Resolver automáticamente query según sistema origen
- Facilitar mantenimiento y auditoría

USO:
    from core.query_catalog import get_query
    
    query = get_query('SOFTRESTAURANT_PRO', 'comercial_ventas_cerradas')
    # Returns: "SELECT ... FROM cheques ..."

CREADO: Junio 2026 - P2-21
"""

import logging
from typing import Optional, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

# Cache de queries para evitar consultas repetidas
_query_cache: Dict[str, str] = {}


def get_query(sistema_codigo: str, query_codigo: str, use_cache: bool = True) -> Optional[str]:
    """
    Obtiene un query SQL desde el catálogo central Sistema_Queries.
    
    Args:
        sistema_codigo: Código del sistema (SOFTRESTAURANT_PRO, MPRO, MANAGEMENTPRO, etc.)
        query_codigo: Código del query (comercial_ventas_cerradas, ventas_hora, etc.)
        use_cache: Si usar cache en memoria (default True)
    
    Returns:
        String SQL del query o None si no existe
    """
    cache_key = f"{sistema_codigo}:{query_codigo}"
    
    # Verificar cache
    if use_cache and cache_key in _query_cache:
        logger.debug(f"[QUERY_CATALOG] Cache hit: {cache_key}")
        return _query_cache[cache_key]
    
    try:
        from core.sql_first.db import get_sql_connection
        
        conn = get_sql_connection()
        cur = conn.cursor()
        
        # Buscar query exacto o normalizado
        cur.execute("""
            SELECT QuerySQL
            FROM Sistema_Queries
            WHERE UPPER(SistemaCodigo) = UPPER(%s)
              AND UPPER(QueryCodigo) = UPPER(%s)
              AND Activo = 1
        """, [sistema_codigo, query_codigo])
        
        row = cur.fetchone()
        conn.close()
        
        if row:
            query_sql = row[0]
            _query_cache[cache_key] = query_sql
            logger.info(f"[QUERY_CATALOG] Query obtenido: {sistema_codigo}/{query_codigo}")
            return query_sql
        
        logger.warning(f"[QUERY_CATALOG] Query no encontrado: {sistema_codigo}/{query_codigo}")
        return None
        
    except Exception as e:
        logger.error(f"[QUERY_CATALOG] Error obteniendo query: {e}")
        return None


def get_query_for_server(server_config: Dict[str, Any], query_codigo: str) -> Optional[str]:
    """
    Obtiene query apropiado para un servidor según su system_type.
    
    Args:
        server_config: Config del servidor (debe tener 'system_type')
        query_codigo: Código del query
    
    Returns:
        String SQL del query o None
    """
    system_type = server_config.get('system_type') or server_config.get('servidor_system_type') or ''
    
    # Normalizar system_type
    st_upper = system_type.upper().strip()
    
    # Mapeo de variantes a códigos canónicos
    system_map = {
        'SOFTRESTAURANT': 'SOFTRESTAURANT_PRO',
        'SOFTRESTAURANT_PRO': 'SOFTRESTAURANT_PRO',
        'SR': 'SOFTRESTAURANT_PRO',
        'SOFT': 'SOFTRESTAURANT_PRO',
        'MPRO': 'MPRO',
        'MANAGEMENTPRO': 'MPRO',
        'MANAGEMENT_PRO': 'MPRO',
        'MANAGMENTPRO': 'MPRO',  # Typo común
    }
    
    sistema_codigo = system_map.get(st_upper, st_upper)
    
    return get_query(sistema_codigo, query_codigo)


def clear_cache():
    """Limpia el cache de queries."""
    global _query_cache
    _query_cache = {}
    logger.info("[QUERY_CATALOG] Cache limpiado")


def list_queries(sistema_codigo: Optional[str] = None) -> list:
    """
    Lista queries disponibles en el catálogo.
    
    Args:
        sistema_codigo: Filtrar por sistema (opcional)
    
    Returns:
        Lista de dicts con info de queries
    """
    try:
        from core.sql_first.db import get_sql_connection
        
        conn = get_sql_connection()
        cur = conn.cursor()
        
        if sistema_codigo:
            cur.execute("""
                SELECT SistemaCodigo, QueryCodigo, Descripcion, TablaDestino, Activo
                FROM Sistema_Queries
                WHERE UPPER(SistemaCodigo) = UPPER(%s)
                ORDER BY QueryCodigo
            """, [sistema_codigo])
        else:
            cur.execute("""
                SELECT SistemaCodigo, QueryCodigo, Descripcion, TablaDestino, Activo
                FROM Sistema_Queries
                ORDER BY SistemaCodigo, QueryCodigo
            """)
        
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        conn.close()
        
        return [dict(zip(cols, row)) for row in rows]
        
    except Exception as e:
        logger.error(f"[QUERY_CATALOG] Error listando queries: {e}")
        return []


__all__ = ['get_query', 'get_query_for_server', 'clear_cache', 'list_queries']
