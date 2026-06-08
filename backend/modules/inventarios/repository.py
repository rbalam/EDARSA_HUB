from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Inventarios Repository
===================================
Acceso a datos de inventarios desde SQL Server.

MIGRACIÓN SQL-ONLY (Mayo 2026):
- ELIMINADA dependencia de MongoDB
- Todas las consultas usan EDARSAHUB como única fuente
- Datos sincronizados en tabla Compras_Inventarios_Fisicos_Sync
"""

from typing import Dict, List, Optional, Any
import logging
from core.pool import execute_hub_query, execute_hub_query_single


def get_inventarios_fisicos(server_id: str = None, almacen: str = None, 
                            sucursal_id: str = None, limit: int = 100) -> List[Dict]:
    """
    Obtiene inventarios físicos desde la tabla sincronizada de EDARSAHUB.
    Reemplaza: mongo_db.inventarios.find(filtro)

    NO-LIVE / EDARSAHUB única fuente. Se leen ACTIVE y REPLACED deduplicando por
    inventario real (server_id+sucursal_id+almacen_id+folio) y prefiriendo ACTIVE,
    para NO ocultar inventarios MPRO/REPLACED (deuda histórica corregida).
    """
    inner_where = "WHERE sync_status IN ('ACTIVE', 'REPLACED')"
    params = []
    
    if server_id:
        inner_where += " AND LOWER(server_id) = LOWER(%s)"
        params.append(server_id)
    
    if almacen:
        inner_where += " AND almacen = %s"
        params.append(almacen)
    
    if sucursal_id:
        inner_where += " AND sucursal_id = %s"
        params.append(sucursal_id)
    
    query = f"""
        SELECT folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
               tipo, estatus, total_productos, sync_source, sync_timestamp, sync_status
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY server_id, sucursal_id, almacen_id, folio
                    ORDER BY CASE WHEN sync_status = 'ACTIVE' THEN 0 ELSE 1 END, sync_timestamp DESC
                ) AS _rn
            FROM Compras_Inventarios_Fisicos_Sync
            {inner_where}
        ) t
        WHERE t._rn = 1
        ORDER BY fecha DESC
    """
    
    results = execute_hub_query(query, tuple(params) if params else None)
    return results[:limit] if limit else results


def get_inventario_by_folio(folio: str, server_id: str = None) -> Optional[Dict]:
    """
    Obtiene un inventario físico específico por folio (ACTIVE o REPLACED, prefiere ACTIVE).
    """
    params = [folio]
    server_filter = ""
    if server_id:
        server_filter = " AND LOWER(server_id) = LOWER(%s)"
        params.append(server_id)
    
    query = f"""
        SELECT TOP 1 folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
               tipo, estatus, total_productos, sync_source, sync_timestamp
        FROM Compras_Inventarios_Fisicos_Sync
        WHERE folio = %s AND sync_status IN ('ACTIVE', 'REPLACED'){server_filter}
        ORDER BY CASE WHEN sync_status = 'ACTIVE' THEN 0 ELSE 1 END, sync_timestamp DESC
    """
    
    return execute_hub_query_single(query, tuple(params))


def get_inventarios_count_by_server(server_id: str) -> int:
    """
    Cuenta inventarios físicos por servidor (deduplicados, ACTIVE o REPLACED).
    """
    query = """
        SELECT COUNT(*) as total
        FROM (
            SELECT DISTINCT server_id, sucursal_id, almacen_id, folio
            FROM Compras_Inventarios_Fisicos_Sync
            WHERE LOWER(server_id) = LOWER(%s) AND sync_status IN ('ACTIVE', 'REPLACED')
        ) t
    """
    result = execute_hub_query_single(query, (server_id,))
    return result.get('total', 0) if result else 0


class InventariosRepository:
    """Clase de compatibilidad - métodos estáticos."""
    
    @staticmethod
    def get_all(server_id: str = None, **filters) -> List[Dict]:
        return get_inventarios_fisicos(server_id=server_id, **filters)
    
    @staticmethod
    def get_by_folio(folio: str, server_id: str = None) -> Optional[Dict]:
        return get_inventario_by_folio(folio, server_id)


__all__ = [
    'InventariosRepository',
    'get_inventarios_fisicos',
    'get_inventario_by_folio',
    'get_inventarios_count_by_server',
]
