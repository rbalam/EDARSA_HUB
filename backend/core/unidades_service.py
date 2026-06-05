"""
EDARSA HUB - Servicio Centralizado de Unidades de Negocio
=========================================================

FUENTE ÚNICA: Tabla Unidades_Negocio en EDARSAHUB SQL

Este servicio reemplaza todos los hardcodes de códigos/nombres de unidades.
Cualquier módulo que necesite información de unidades debe usar este servicio.

Uso:
    from core.unidades_service import UnidadesService
    
    # Obtener todas las unidades activas
    unidades = UnidadesService.get_all()
    
    # Obtener códigos canónicos
    codigos = UnidadesService.get_codigos()  # ['130MID', '130QRO', ...]
    
    # Resolver variante a código canónico
    codigo = UnidadesService.resolver_codigo('130 MERIDA')  # '130MID'
    
    # Obtener nombre display
    nombre = UnidadesService.get_nombre('130MID')  # '130° MERIDA'
"""

import logging
from typing import Dict, List, Optional, Set
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

# Cache TTL en segundos (5 minutos)
_CACHE_TTL = 300
_cache_timestamp: float = 0
_unidades_cache: List[Dict] = []


def _load_unidades_from_sql() -> List[Dict]:
    """Carga unidades desde EDARSAHUB SQL."""
    try:
        from core.config.edarsahub_sql import get_edarsahub_connection
        
        conn = get_edarsahub_connection()
        cur = conn.cursor(as_dict=True)
        
        cur.execute("""
        SELECT 
            CAST(id AS NVARCHAR(100)) AS id,
            codigo,
            nombre,
            CAST(server_id AS NVARCHAR(100)) AS server_id,
            sucursal_origen_id,
            system_type,
            activo,
            orden
        FROM Unidades_Negocio
        WHERE activo = 1
        ORDER BY orden, nombre
        """)
        
        unidades = cur.fetchall()
        conn.close()
        
        logger.info(f"[UNIDADES_SERVICE] Cargadas {len(unidades)} unidades desde SQL")
        return unidades
        
    except Exception as e:
        logger.error(f"[UNIDADES_SERVICE] Error cargando unidades: {e}")
        return []


def _get_cached_unidades() -> List[Dict]:
    """Obtiene unidades con cache."""
    global _cache_timestamp, _unidades_cache
    
    now = time.time()
    if now - _cache_timestamp > _CACHE_TTL or not _unidades_cache:
        _unidades_cache = _load_unidades_from_sql()
        _cache_timestamp = now
    
    return _unidades_cache


class UnidadesService:
    """Servicio centralizado para gestión de unidades de negocio."""
    
    # Mapeo de variantes a código canónico (para compatibilidad legacy)
    # Esto es temporal hasta que todos los sistemas usen códigos canónicos
    _VARIANTES_MAP = {
        # Mérida
        '130-MER': '130MID',
        '130-MID': '130MID',
        '130MER': '130MID',
        '130 MERIDA': '130MID',
        '130 MÉRIDA': '130MID',
        '130° MERIDA': '130MID',
        '130° MÉRIDA': '130MID',
        'MERIDA': '130MID',
        'MÉRIDA': '130MID',
        '130MID': '130MID',
        # Querétaro
        '130-QRO': '130QRO',
        '130 QRO': '130QRO',
        '130 QUERETARO': '130QRO',
        '130 QUERÉTARO': '130QRO',
        '130° QUERETARO': '130QRO',
        '130° QUERÉTARO': '130QRO',
        'QUERETARO': '130QRO',
        'QUERÉTARO': '130QRO',
        '130QRO': '130QRO',
        # La Estelar
        'LA-ESTELAR': 'ESTELAR',
        'LA ESTELAR': 'ESTELAR',
        'ESTELAR': 'ESTELAR',
        # Cienfuegos y Origen (sin variantes)
        'CIENFUEGOS': 'CIENFUEGOS',
        'ORIGEN': 'ORIGEN',
    }
    
    @classmethod
    def get_all(cls) -> List[Dict]:
        """
        Obtiene todas las unidades activas.
        
        Returns:
            Lista de dicts con: id, codigo, nombre, server_id, system_type, etc.
        """
        return _get_cached_unidades()
    
    @classmethod
    def get_codigos(cls) -> List[str]:
        """
        Obtiene lista de códigos canónicos.
        
        Returns:
            Lista de códigos: ['130MID', '130QRO', 'CIENFUEGOS', 'ESTELAR', 'ORIGEN']
        """
        return [u['codigo'] for u in cls.get_all() if u.get('codigo')]
    
    @classmethod
    def get_codigos_set(cls) -> Set[str]:
        """
        Obtiene set de códigos canónicos (para búsquedas O(1)).
        
        Returns:
            Set de códigos
        """
        return set(cls.get_codigos())
    
    @classmethod
    def get_nombres(cls) -> List[str]:
        """
        Obtiene lista de nombres display.
        
        Returns:
            Lista de nombres: ['130° MERIDA', '130° QUERETARO', ...]
        """
        return [u['nombre'] for u in cls.get_all() if u.get('nombre')]
    
    @classmethod
    def get_by_codigo(cls, codigo: str) -> Optional[Dict]:
        """
        Obtiene unidad por código canónico.
        
        Args:
            codigo: Código canónico (130MID, CIENFUEGOS, etc.)
            
        Returns:
            Dict con datos de la unidad o None
        """
        codigo_upper = codigo.upper().strip()
        for u in cls.get_all():
            if u.get('codigo', '').upper() == codigo_upper:
                return u
        return None
    
    @classmethod
    def get_by_server_id(cls, server_id: str) -> Optional[Dict]:
        """
        Obtiene unidad por server_id (UUID).
        
        Args:
            server_id: UUID del servidor
            
        Returns:
            Dict con datos de la unidad o None
        """
        for u in cls.get_all():
            if u.get('server_id') == server_id:
                return u
        return None
    
    @classmethod
    def get_nombre(cls, codigo: str) -> Optional[str]:
        """
        Obtiene nombre display para un código.
        
        Args:
            codigo: Código canónico
            
        Returns:
            Nombre display o None
        """
        unidad = cls.get_by_codigo(codigo)
        return unidad.get('nombre') if unidad else None
    
    @classmethod
    def resolver_codigo(cls, variante: str) -> Optional[str]:
        """
        Resuelve cualquier variante de nombre a código canónico.
        
        Args:
            variante: Cualquier variante ('130 MERIDA', 'LA ESTELAR', etc.)
            
        Returns:
            Código canónico o None si no se reconoce
        """
        if not variante:
            return None
        
        variante_upper = variante.upper().strip()
        
        # Buscar en mapeo de variantes
        if variante_upper in cls._VARIANTES_MAP:
            return cls._VARIANTES_MAP[variante_upper]
        
        # Buscar directo en códigos
        if variante_upper in cls.get_codigos_set():
            return variante_upper
        
        # Buscar por nombre
        for u in cls.get_all():
            if u.get('nombre', '').upper() == variante_upper:
                return u.get('codigo')
        
        return None
    
    @classmethod
    def es_codigo_valido(cls, codigo: str) -> bool:
        """
        Verifica si un código es válido.
        
        Args:
            codigo: Código a verificar
            
        Returns:
            True si es un código canónico válido
        """
        return codigo.upper().strip() in cls.get_codigos_set()
    
    @classmethod
    def get_mapeo_codigo_nombre(cls) -> Dict[str, str]:
        """
        Obtiene diccionario código -> nombre.
        
        Returns:
            {'130MID': '130° MERIDA', ...}
        """
        return {u['codigo']: u['nombre'] for u in cls.get_all() if u.get('codigo')}
    
    @classmethod
    def get_mapeo_nombre_codigo(cls) -> Dict[str, str]:
        """
        Obtiene diccionario nombre -> código.
        
        Returns:
            {'130° MERIDA': '130MID', ...}
        """
        return {u['nombre']: u['codigo'] for u in cls.get_all() if u.get('nombre')}
    
    @classmethod
    def get_mapeo_server_id_codigo(cls) -> Dict[str, str]:
        """
        Obtiene diccionario server_id -> código.
        
        Returns:
            {'uuid-xxx': '130MID', ...}
        """
        return {u['server_id']: u['codigo'] for u in cls.get_all() if u.get('server_id')}
    
    @classmethod
    def invalidate_cache(cls) -> None:
        """Invalida el cache forzando recarga en siguiente llamada."""
        global _cache_timestamp
        _cache_timestamp = 0
        logger.info("[UNIDADES_SERVICE] Cache invalidado")


# Funciones de conveniencia (para compatibilidad)
def get_unidades_canonicas() -> List[str]:
    """Alias para UnidadesService.get_codigos()"""
    return UnidadesService.get_codigos()


def resolver_unidad(variante: str) -> Optional[str]:
    """Alias para UnidadesService.resolver_codigo()"""
    return UnidadesService.resolver_codigo(variante)


def get_nombre_unidad(codigo: str) -> Optional[str]:
    """Alias para UnidadesService.get_nombre()"""
    return UnidadesService.get_nombre(codigo)
