from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Registro Central de Unidades de Negocio
=====================================================

FASE P0: Corrección de Jobs de Sincronización

Este módulo proporciona acceso centralizado al catálogo de Unidades de Negocio
desde EDARSAHUB. REEMPLAZA los mapeos hardcodeados en los jobs de sincronización.

FUENTE MAESTRA: EDARSAHUB.Unidades_Negocio
CÓDIGOS OFICIALES: 130MID, 130QRO, CIENFUEGOS, ESTELAR, ORIGEN

MÁXIMAS:
- EDARSAHUB es el cerebro del sistema
- Unidades_Negocio.codigo es el código canónico único
- NO usar MongoDB como fuente funcional
- NO usar nombres visibles como llave
- NO usar server_id como unidad_negocio_pk

Autor: E1 Agent
Fecha: 2026-05-13
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Cache global del catálogo
_CACHE_UNIDADES: Optional[Dict[str, Any]] = None
_CACHE_TIMESTAMP: Optional[datetime] = None
_CACHE_TTL_SECONDS = 300  # 5 minutos


@dataclass
class UnidadNegocioConfig:
    """Configuración de una unidad de negocio para sincronización."""
    codigo: str                     # Código canónico (130MID, CIENFUEGOS, etc.)
    nombre: str                     # Nombre oficial
    server_id: str                  # UUID del servidor
    sucursal_id: str                # ID de sucursal (DEFAULT, 0021, 0023, etc.)
    sistema: str                    # SoftRestaurant, MPRO
    activo: bool = True


def _get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB."""
    import pymssql
    return pymssql.connect(
        server=os.getenv('EDARSAHUB_SQL_HOST'),
        port=1433,
        database='EDARSAHUB',
        user=os.getenv('EDARSAHUB_SQL_USER'),
        password=os.getenv('EDARSAHUB_SQL_PASSWORD')
    )


def _cargar_catalogo_unidades() -> Dict[str, Any]:
    """
    Carga el catálogo completo de Unidades_Negocio desde EDARSAHUB.
    
    Returns:
        Dict con estructura:
        {
            'by_codigo': {codigo: UnidadNegocioConfig},
            'by_server_sucursal': {(server_id, sucursal_id): UnidadNegocioConfig},
            'all': [UnidadNegocioConfig, ...]
        }
    """
    global _CACHE_UNIDADES, _CACHE_TIMESTAMP
    
    # Verificar cache
    now = datetime.now(timezone.utc)
    if _CACHE_UNIDADES and _CACHE_TIMESTAMP:
        age = (now - _CACHE_TIMESTAMP).total_seconds()
        if age < _CACHE_TTL_SECONDS:
            return _CACHE_UNIDADES
    
    try:
        conn = _get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        cursor.execute("""
            SELECT 
                id,
                codigo,
                nombre,
                server_id,
                sucursal_origen_id,
                system_type,
                activo,
                orden
            FROM Unidades_Negocio
            WHERE activo = 1
            ORDER BY orden
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        catalogo = {
            'by_codigo': {},
            'by_server_sucursal': {},
            'all': []
        }
        
        for row in rows:
            config = UnidadNegocioConfig(
                codigo=row['codigo'],
                nombre=row['nombre'],
                server_id=str(row['server_id']),
                sucursal_id=row['sucursal_origen_id'] or 'DEFAULT',
                sistema=row['system_type'] or 'UNKNOWN',
                activo=bool(row['activo'])
            )
            
            catalogo['by_codigo'][config.codigo] = config
            key = (config.server_id, config.sucursal_id)
            catalogo['by_server_sucursal'][key] = config
            catalogo['all'].append(config)
        
        _CACHE_UNIDADES = catalogo
        _CACHE_TIMESTAMP = now
        
        logger.info(f"[UNIDADES_REGISTRY] Catálogo cargado: {len(catalogo['all'])} unidades desde EDARSAHUB")
        return catalogo
        
    except Exception as e:
        logger.error(f"[UNIDADES_REGISTRY] Error cargando catálogo: {e}")
        # Fallback a catálogo vacío
        return {'by_codigo': {}, 'by_server_sucursal': {}, 'all': []}


def get_unidad_by_server_sucursal(server_id: str, sucursal_id: Optional[str] = None) -> Optional[UnidadNegocioConfig]:
    """
    Obtiene la configuración de unidad dado server_id y sucursal_id.
    
    Args:
        server_id: UUID del servidor
        sucursal_id: ID de sucursal (opcional, usa 'DEFAULT' si no se proporciona)
    
    Returns:
        UnidadNegocioConfig o None si no se encuentra
    """
    catalogo = _cargar_catalogo_unidades()
    
    # Normalizar sucursal_id
    suc = sucursal_id if sucursal_id and sucursal_id != 'NULL' else 'DEFAULT'
    
    # Buscar por (server_id, sucursal_id)
    key = (server_id, suc)
    config = catalogo['by_server_sucursal'].get(key)
    
    if config:
        return config
    
    # Fallback: buscar con DEFAULT si no se encontró
    if suc != 'DEFAULT':
        key_default = (server_id, 'DEFAULT')
        config = catalogo['by_server_sucursal'].get(key_default)
        if config:
            logger.warning(f"[UNIDADES_REGISTRY] Fallback a DEFAULT para server={server_id}, sucursal={suc}")
            return config
    
    logger.warning(f"[UNIDADES_REGISTRY] No encontrado: server={server_id}, sucursal={suc}")
    return None


def get_all_unidades_for_sync() -> List[UnidadNegocioConfig]:
    """
    Obtiene todas las unidades activas para sincronización.
    
    Returns:
        Lista de UnidadNegocioConfig ordenada por prioridad
    """
    catalogo = _cargar_catalogo_unidades()
    return catalogo['all']


def get_unidades_by_sistema(sistema: str) -> List[UnidadNegocioConfig]:
    """
    Obtiene unidades filtradas por sistema (SoftRestaurant, MPRO).
    
    Args:
        sistema: "SoftRestaurant" o "MPRO"
    
    Returns:
        Lista de UnidadNegocioConfig del sistema especificado
    """
    catalogo = _cargar_catalogo_unidades()
    return [u for u in catalogo['all'] if u.sistema.upper() == sistema.upper()]


def invalidate_cache():
    """Invalida el cache del catálogo (útil para testing)."""
    global _CACHE_UNIDADES, _CACHE_TIMESTAMP
    _CACHE_UNIDADES = None
    _CACHE_TIMESTAMP = None
    logger.info("[UNIDADES_REGISTRY] Cache invalidado")
