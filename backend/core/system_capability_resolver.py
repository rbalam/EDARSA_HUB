from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - System Capability Resolver
=======================================
Servicio central para consultar sistemas, capacidades, variantes y visibilidad
desde EDARSAHUB SQL Server.

FASE 4 del Catálogo Maestro de Sistemas y Capacidades SQL-First.

Este módulo es el RESOLVER CENTRAL para:
- Normalizar system_type usando Sistema_TiposVariantes
- Consultar capacidades de un sistema
- Validar si un sistema soporta una capacidad
- Obtener sistemas por capacidad
- Consultar visibilidad por módulo/menu/tab

TABLAS SQL CONSULTADAS:
- Sistema_Tipos (catálogo de tipos de sistema)
- Sistema_Capacidades (capacidades por sistema)
- Sistema_ModulosVisibilidad (visibilidad por módulo)
- Sistema_TiposVariantes (variantes de nombres)

USO:
    from core.system_capability_resolver import SystemCapabilityResolver
    
    resolver = SystemCapabilityResolver()
    
    # Normalizar variante
    result = resolver.normalize_system_type("ManagmentPro")
    # {'codigo_sistema': 'MPRO', 'nombre_sistema': 'ManagementPro', ...}
    
    # Verificar capacidad
    if resolver.system_supports("SOFTRESTAURANT", Capability.SYNC_VENTAS_HISTORICAS):
        # Sistema soporta sync de ventas
    
    # Obtener sistemas explorables
    sistemas = resolver.get_explorable_systems()

REGLAS:
- EDARSAHUB SQL es la fuente primaria
- NO usar MongoDB
- NO exponer secrets
- Compatibilidad temporal con system_type_utils.py

Autor: Arquitecto Senior Backend
Fecha: 2025-12-XX
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES DE CAPACIDADES
# ============================================================================

class Capability(str, Enum):
    """Capacidades de sistema registradas en Sistema_Capacidades."""
    
    # Explorador BD
    EXPLORADOR_BD = "EXPLORADOR_BD"
    EXPLORADOR_TABLAS = "EXPLORADOR_TABLAS"
    EXPLORADOR_COLUMNAS = "EXPLORADOR_COLUMNAS"
    EXPLORADOR_PREVIEW = "EXPLORADOR_PREVIEW"
    
    # Sync Históricos
    SYNC_VENTAS_HISTORICAS = "SYNC_VENTAS_HISTORICAS"
    SYNC_VENTAS_POR_HORA = "SYNC_VENTAS_POR_HORA"
    SYNC_VENTAS_DIA_SEMANA = "SYNC_VENTAS_DIA_SEMANA"
    
    # Ventas
    VENTAS_DIA = "VENTAS_DIA"
    VENTAS_PERIODO = "VENTAS_PERIODO"
    
    # Módulos
    COMPRAS = "COMPRAS"
    INVENTARIOS = "INVENTARIOS"
    CORTES_Z = "CORTES_Z"
    REPORTES = "REPORTES"
    CATALOGO_SQL = "CATALOGO_SQL"
    PROPINAS_TPV = "PROPINAS_TPV"
    
    # Exclusivas MPRO
    SUCURSALES_VISIBLES = "SUCURSALES_VISIBLES"
    CUENTAS_POR_PAGAR = "CUENTAS_POR_PAGAR"


class Module(str, Enum):
    """Módulos de visibilidad registrados en Sistema_ModulosVisibilidad."""
    EXPLORADOR_BD = "EXPLORADOR_BD"
    COMERCIAL = "COMERCIAL"
    COMPRAS = "COMPRAS"
    REPORTES = "REPORTES"
    FINANZAS = "FINANZAS"
    SYNC_HISTORICOS = "SYNC_HISTORICOS"
    CATALOGO_SQL = "CATALOGO_SQL"
    OPERACIONES = "OPERACIONES"
    TABLERO = "TABLERO"


# ============================================================================
# CONFIGURACIÓN EDARSAHUB
# ============================================================================

EDARSAHUB_CONFIG = {
    'host': os.getenv('EDARSAHUB_SQL_HOST'),
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': os.getenv('EDARSAHUB_SQL_USER'),
    'password': os.getenv('EDARSAHUB_SQL_PASSWORD')
}


# ============================================================================
# CACHE LIGERO EN MEMORIA
# ============================================================================

@dataclass
class CacheEntry:
    """Entrada de cache con TTL."""
    data: Any
    expires_at: datetime
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


class LightCache:
    """Cache ligero en memoria con TTL."""
    
    def __init__(self, default_ttl_seconds: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired():
                return entry.data
            elif entry:
                del self._cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds or self._default_ttl
        expires = datetime.now() + timedelta(seconds=ttl)
        with self._lock:
            self._cache[key] = CacheEntry(data=value, expires_at=expires)
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
    
    def clear_expired(self) -> int:
        """Limpia entradas expiradas y retorna cantidad eliminada."""
        removed = 0
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                del self._cache[key]
                removed += 1
        return removed


# ============================================================================
# SYSTEM CAPABILITY RESOLVER
# ============================================================================

class SystemCapabilityResolver:
    """
    Resolver central para capacidades de sistemas.
    
    FUENTE: EDARSAHUB SQL Server
    - Sistema_Tipos
    - Sistema_Capacidades
    - Sistema_ModulosVisibilidad
    - Sistema_TiposVariantes
    """
    
    def __init__(self, cache_ttl_seconds: int = 300):
        """
        Inicializa el resolver.
        
        Args:
            cache_ttl_seconds: TTL del cache en segundos (default: 5 minutos)
        """
        self._cache = LightCache(default_ttl_seconds=cache_ttl_seconds)
        self._config = EDARSAHUB_CONFIG.copy()
    
    def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Ejecuta query en EDARSAHUB SQL.
        
        NO expone secrets ni passwords.
        """
        try:
            # Importar aquí para evitar dependencias circulares
            from core.db import execute_sql_query
            
            result = execute_sql_query(
                host=self._config['host'],
                port=self._config['port'],
                database=self._config['database'],
                username=self._config['username'],
                password=self._config['password'],
                query=query
            )
            return result if result else []
        except Exception as e:
            logger.error(f"[SystemCapabilityResolver] Error ejecutando query: {e}")
            return []
    
    def clear_cache(self) -> None:
        """Limpia todo el cache."""
        self._cache.clear()
        logger.info("[SystemCapabilityResolver] Cache limpiado")
    
    # ========================================================================
    # NORMALIZACIÓN DE SYSTEM_TYPE
    # ========================================================================
    
    def normalize_system_type(self, system_type: str) -> Dict[str, Any]:
        """
        Normaliza un system_type usando Sistema_TiposVariantes.
        
        Args:
            system_type: Variante de nombre de sistema (ej: "ManagmentPro", "SOFRESATAURANT_ENTER")
        
        Returns:
            dict con:
            - codigo_sistema: Código canónico del sistema
            - nombre_sistema: Nombre legible
            - sistema_tipo_id: ID en Sistema_Tipos
            - variante_original: El valor recibido
            - found: True si se encontró en SQL
            - source: 'sql' o 'fallback'
        """
        if not system_type:
            return {
                'codigo_sistema': None,
                'nombre_sistema': None,
                'sistema_tipo_id': None,
                'variante_original': system_type,
                'found': False,
                'source': 'empty_input'
            }
        
        # Normalizar entrada
        normalized_input = system_type.strip().upper()
        
        # Buscar en cache
        cache_key = f"normalize:{normalized_input}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        
        # Buscar en Sistema_TiposVariantes
        query = f"""
        SELECT 
            st.SistemaTipoID,
            st.CodigoSistema,
            st.NombreSistema,
            st.Descripcion,
            sv.VarianteNombre,
            sv.EsCanonico
        FROM Sistema_TiposVariantes sv
        JOIN Sistema_Tipos st ON sv.SistemaTipoID = st.SistemaTipoID
        WHERE UPPER(sv.VarianteNombre) = '{normalized_input}'
          AND sv.Activo = 1
          AND st.Activo = 1
        """
        
        results = self._execute_query(query)
        
        if results:
            row = results[0]
            result = {
                'codigo_sistema': row['CodigoSistema'],
                'nombre_sistema': row['NombreSistema'],
                'sistema_tipo_id': row['SistemaTipoID'],
                'descripcion': row.get('Descripcion'),
                'variante_original': system_type,
                'variante_encontrada': row['VarianteNombre'],
                'es_canonico': row.get('EsCanonico', False),
                'found': True,
                'source': 'sql'
            }
            self._cache.set(cache_key, result)
            return result
        
        # Buscar directamente en Sistema_Tipos por CodigoSistema
        query_direct = f"""
        SELECT 
            SistemaTipoID,
            CodigoSistema,
            NombreSistema,
            Descripcion
        FROM Sistema_Tipos
        WHERE UPPER(CodigoSistema) = '{normalized_input}'
          AND Activo = 1
        """
        
        direct_results = self._execute_query(query_direct)
        
        if direct_results:
            row = direct_results[0]
            result = {
                'codigo_sistema': row['CodigoSistema'],
                'nombre_sistema': row['NombreSistema'],
                'sistema_tipo_id': row['SistemaTipoID'],
                'descripcion': row.get('Descripcion'),
                'variante_original': system_type,
                'variante_encontrada': row['CodigoSistema'],
                'es_canonico': True,
                'found': True,
                'source': 'sql_direct'
            }
            self._cache.set(cache_key, result)
            return result
        
        # Fallback a system_type_utils.py para compatibilidad temporal
        try:
            from core.system_type_utils import normalize_system_type as legacy_normalize
            legacy_result = legacy_normalize(system_type)
            
            if legacy_result and legacy_result != 'UNKNOWN':
                result = {
                    'codigo_sistema': legacy_result,
                    'nombre_sistema': legacy_result,
                    'sistema_tipo_id': None,
                    'variante_original': system_type,
                    'found': True,
                    'source': 'fallback_legacy',
                    '_warning': 'Normalizado via system_type_utils.py (compatibilidad temporal)'
                }
                self._cache.set(cache_key, result)
                return result
        except Exception as e:
            logger.debug(f"[SystemCapabilityResolver] Fallback legacy falló: {e}")
        
        # No encontrado
        result = {
            'codigo_sistema': None,
            'nombre_sistema': None,
            'sistema_tipo_id': None,
            'variante_original': system_type,
            'found': False,
            'source': 'not_found'
        }
        self._cache.set(cache_key, result, ttl_seconds=60)  # Cache corto para no encontrados
        return result
    
    # ========================================================================
    # CONSULTA DE CAPACIDADES
    # ========================================================================
    
    def system_supports(self, codigo_sistema: str, capacidad: str) -> bool:
        """
        Verifica si un sistema soporta una capacidad.
        
        Args:
            codigo_sistema: Código del sistema (ej: "SOFTRESTAURANT", "MPRO")
            capacidad: Código de la capacidad (ej: "SYNC_VENTAS_HISTORICAS")
        
        Returns:
            True si el sistema soporta la capacidad y está activa
        """
        if not codigo_sistema or not capacidad:
            return False
        
        # Normalizar
        codigo_upper = codigo_sistema.strip().upper()
        capacidad_upper = capacidad.strip().upper()
        
        # Cache
        cache_key = f"supports:{codigo_upper}:{capacidad_upper}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        query = f"""
        SELECT COUNT(*) as soporta
        FROM Sistema_Capacidades sc
        JOIN Sistema_Tipos st ON sc.SistemaTipoID = st.SistemaTipoID
        WHERE UPPER(st.CodigoSistema) = '{codigo_upper}'
          AND UPPER(sc.CodigoCapacidad) = '{capacidad_upper}'
          AND sc.Activo = 1
          AND st.Activo = 1
        """
        
        results = self._execute_query(query)
        supports = results[0]['soporta'] > 0 if results else False
        
        self._cache.set(cache_key, supports)
        return supports
    
    def get_capabilities(self, codigo_sistema: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las capacidades activas de un sistema.
        
        Args:
            codigo_sistema: Código del sistema
        
        Returns:
            Lista de capacidades con código, descripción y requisitos
        """
        if not codigo_sistema:
            return []
        
        codigo_upper = codigo_sistema.strip().upper()
        
        # Cache
        cache_key = f"capabilities:{codigo_upper}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        query = f"""
        SELECT 
            sc.CodigoCapacidad,
            sc.Descripcion,
            sc.RequiereApiLocal,
            sc.RequiereSqlDirecto,
            sc.ConfiguracionJSON
        FROM Sistema_Capacidades sc
        JOIN Sistema_Tipos st ON sc.SistemaTipoID = st.SistemaTipoID
        WHERE UPPER(st.CodigoSistema) = '{codigo_upper}'
          AND sc.Activo = 1
          AND st.Activo = 1
        ORDER BY sc.CodigoCapacidad
        """
        
        results = self._execute_query(query)
        
        capabilities = []
        for row in results:
            capabilities.append({
                'codigo': row['CodigoCapacidad'],
                'descripcion': row.get('Descripcion'),
                'requiere_api_local': bool(row.get('RequiereApiLocal')),
                'requiere_sql_directo': bool(row.get('RequiereSqlDirecto')),
                'configuracion': row.get('ConfiguracionJSON')
            })
        
        self._cache.set(cache_key, capabilities)
        return capabilities
    
    def get_systems_for_capability(self, capacidad: str) -> List[Dict[str, Any]]:
        """
        Obtiene sistemas que soportan una capacidad específica.
        
        Args:
            capacidad: Código de la capacidad
        
        Returns:
            Lista de sistemas con código, nombre y detalles
        """
        if not capacidad:
            return []
        
        capacidad_upper = capacidad.strip().upper()
        
        # Cache
        cache_key = f"systems_for:{capacidad_upper}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        query = f"""
        SELECT 
            st.SistemaTipoID,
            st.CodigoSistema,
            st.NombreSistema,
            st.Descripcion,
            sc.RequiereApiLocal,
            sc.RequiereSqlDirecto
        FROM Sistema_Capacidades sc
        JOIN Sistema_Tipos st ON sc.SistemaTipoID = st.SistemaTipoID
        WHERE UPPER(sc.CodigoCapacidad) = '{capacidad_upper}'
          AND sc.Activo = 1
          AND st.Activo = 1
        ORDER BY st.CodigoSistema
        """
        
        results = self._execute_query(query)
        
        systems = []
        for row in results:
            systems.append({
                'sistema_tipo_id': row['SistemaTipoID'],
                'codigo_sistema': row['CodigoSistema'],
                'nombre_sistema': row['NombreSistema'],
                'descripcion': row.get('Descripcion'),
                'capacidad': capacidad_upper,
                'requiere_api_local': bool(row.get('RequiereApiLocal')),
                'requiere_sql_directo': bool(row.get('RequiereSqlDirecto'))
            })
        
        self._cache.set(cache_key, systems)
        return systems
    
    # ========================================================================
    # VISIBILIDAD POR MÓDULO
    # ========================================================================
    
    def get_visible_systems_for_module(
        self, 
        modulo: str, 
        menu: Optional[str] = None, 
        tab: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene sistemas visibles para un módulo específico.
        
        Args:
            modulo: Código del módulo (ej: "EXPLORADOR_BD", "COMERCIAL")
            menu: Submenú opcional
            tab: Tab opcional
        
        Returns:
            Lista de sistemas visibles ordenados por OrdenMenu
        """
        if not modulo:
            return []
        
        modulo_upper = modulo.strip().upper()
        
        # Cache
        cache_key = f"visible:{modulo_upper}:{menu or ''}:{tab or ''}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        query = f"""
        SELECT 
            st.SistemaTipoID,
            st.CodigoSistema,
            st.NombreSistema,
            sm.DescripcionModulo,
            sm.OrdenMenu,
            sm.ConfiguracionJSON
        FROM Sistema_ModulosVisibilidad sm
        JOIN Sistema_Tipos st ON sm.SistemaTipoID = st.SistemaTipoID
        WHERE UPPER(sm.CodigoModulo) = '{modulo_upper}'
          AND sm.Visible = 1
          AND sm.Activo = 1
          AND st.Activo = 1
        ORDER BY sm.OrdenMenu, st.CodigoSistema
        """
        
        results = self._execute_query(query)
        
        systems = []
        for row in results:
            systems.append({
                'sistema_tipo_id': row['SistemaTipoID'],
                'codigo_sistema': row['CodigoSistema'],
                'nombre_sistema': row['NombreSistema'],
                'descripcion_modulo': row.get('DescripcionModulo'),
                'orden': row.get('OrdenMenu', 0),
                'configuracion': row.get('ConfiguracionJSON')
            })
        
        self._cache.set(cache_key, systems)
        return systems
    
    def get_visibility(
        self, 
        codigo_sistema: str, 
        modulo: str, 
        menu: Optional[str] = None, 
        tab: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene configuración de visibilidad para un sistema en un módulo.
        
        Args:
            codigo_sistema: Código del sistema
            modulo: Código del módulo
            menu: Submenú opcional
            tab: Tab opcional
        
        Returns:
            dict con visible, orden y configuración
        """
        if not codigo_sistema or not modulo:
            return {'visible': False, 'orden': 0, 'configuracion': None}
        
        codigo_upper = codigo_sistema.strip().upper()
        modulo_upper = modulo.strip().upper()
        
        query = f"""
        SELECT 
            sm.Visible,
            sm.OrdenMenu,
            sm.DescripcionModulo,
            sm.ConfiguracionJSON
        FROM Sistema_ModulosVisibilidad sm
        JOIN Sistema_Tipos st ON sm.SistemaTipoID = st.SistemaTipoID
        WHERE UPPER(st.CodigoSistema) = '{codigo_upper}'
          AND UPPER(sm.CodigoModulo) = '{modulo_upper}'
          AND sm.Activo = 1
          AND st.Activo = 1
        """
        
        results = self._execute_query(query)
        
        if results:
            row = results[0]
            return {
                'visible': bool(row.get('Visible')),
                'orden': row.get('OrdenMenu', 0),
                'descripcion': row.get('DescripcionModulo'),
                'configuracion': row.get('ConfiguracionJSON')
            }
        
        return {'visible': False, 'orden': 0, 'configuracion': None}
    
    # ========================================================================
    # HELPERS ESPECÍFICOS
    # ========================================================================
    
    def get_explorable_systems(self) -> List[Dict[str, Any]]:
        """
        Obtiene sistemas que soportan EXPLORADOR_BD.
        
        Returns:
            Lista de sistemas explorables
        """
        return self.get_systems_for_capability(Capability.EXPLORADOR_BD)
    
    def get_sync_sales_systems(self) -> List[Dict[str, Any]]:
        """
        Obtiene sistemas que soportan sincronización de ventas.
        
        IMPORTANTE: Solo incluye sistemas con capacidades de sync activadas.
        API_LOCAL/Enterprise NO aparece si no tiene SYNC_VENTAS_* activo.
        
        Returns:
            Lista de sistemas con capacidades de sync
        """
        # Cache
        cache_key = "sync_sales_systems"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Buscar sistemas con cualquiera de las capacidades de sync
        query = """
        SELECT DISTINCT
            st.SistemaTipoID,
            st.CodigoSistema,
            st.NombreSistema,
            st.Descripcion
        FROM Sistema_Capacidades sc
        JOIN Sistema_Tipos st ON sc.SistemaTipoID = st.SistemaTipoID
        WHERE sc.CodigoCapacidad IN (
            'SYNC_VENTAS_HISTORICAS',
            'SYNC_VENTAS_POR_HORA',
            'SYNC_VENTAS_DIA_SEMANA'
        )
          AND sc.Activo = 1
          AND st.Activo = 1
        ORDER BY st.CodigoSistema
        """
        
        results = self._execute_query(query)
        
        systems = []
        for row in results:
            # Obtener capacidades específicas de sync para cada sistema
            caps = self.get_capabilities(row['CodigoSistema'])
            sync_caps = [c['codigo'] for c in caps if c['codigo'].startswith('SYNC_VENTAS')]
            
            systems.append({
                'sistema_tipo_id': row['SistemaTipoID'],
                'codigo_sistema': row['CodigoSistema'],
                'nombre_sistema': row['NombreSistema'],
                'descripcion': row.get('Descripcion'),
                'sync_capabilities': sync_caps
            })
        
        self._cache.set(cache_key, systems)
        return systems
    
    def get_all_systems(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los sistemas activos.
        
        Returns:
            Lista de todos los sistemas
        """
        cache_key = "all_systems"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        query = """
        SELECT 
            SistemaTipoID,
            CodigoSistema,
            NombreSistema,
            Descripcion,
            Activo
        FROM Sistema_Tipos
        WHERE Activo = 1
        ORDER BY SistemaTipoID
        """
        
        results = self._execute_query(query)
        
        systems = []
        for row in results:
            systems.append({
                'sistema_tipo_id': row['SistemaTipoID'],
                'codigo_sistema': row['CodigoSistema'],
                'nombre_sistema': row['NombreSistema'],
                'descripcion': row.get('Descripcion')
            })
        
        self._cache.set(cache_key, systems)
        return systems
    
    # ========================================================================
    # DIAGNÓSTICO
    # ========================================================================
    
    def explain_system(self, system_type: str) -> Dict[str, Any]:
        """
        Proporciona información completa de diagnóstico sobre un sistema.
        
        Args:
            system_type: Cualquier variante de nombre de sistema
        
        Returns:
            dict con normalización, capacidades, visibilidad y diagnóstico
        """
        # Normalizar primero
        normalized = self.normalize_system_type(system_type)
        
        if not normalized.get('found'):
            return {
                'input': system_type,
                'normalized': normalized,
                'found': False,
                'capacidades': [],
                'visibilidad': [],
                'soporta_explorador': False,
                'soporta_sync_ventas': False,
                'diagnostico': f"Sistema '{system_type}' no encontrado en catálogo"
            }
        
        codigo = normalized['codigo_sistema']
        
        # Obtener capacidades
        capacidades = self.get_capabilities(codigo)
        capacidad_codigos = [c['codigo'] for c in capacidades]
        
        # Verificar soportes clave
        soporta_explorador = Capability.EXPLORADOR_BD in capacidad_codigos
        
        sync_caps = [
            Capability.SYNC_VENTAS_HISTORICAS,
            Capability.SYNC_VENTAS_POR_HORA,
            Capability.SYNC_VENTAS_DIA_SEMANA
        ]
        soporta_sync_ventas = any(cap in capacidad_codigos for cap in sync_caps)
        
        # Obtener visibilidad
        visibilidad = []
        for modulo in Module:
            vis = self.get_visibility(codigo, modulo.value)
            if vis['visible']:
                visibilidad.append({
                    'modulo': modulo.value,
                    'visible': vis['visible'],
                    'orden': vis['orden']
                })
        
        # Diagnóstico
        diagnostico_items = []
        if soporta_explorador:
            diagnostico_items.append("✅ Puede aparecer en Explorador BD")
        else:
            diagnostico_items.append("❌ NO aparece en Explorador BD")
        
        if soporta_sync_ventas:
            sync_activos = [c for c in capacidad_codigos if c.startswith('SYNC_VENTAS')]
            diagnostico_items.append(f"✅ Sync ventas activo: {', '.join(sync_activos)}")
        else:
            diagnostico_items.append("❌ Sync ventas NO activo")
        
        return {
            'input': system_type,
            'normalized': normalized,
            'found': True,
            'capacidades': capacidades,
            'capacidad_codigos': capacidad_codigos,
            'visibilidad': visibilidad,
            'soporta_explorador': soporta_explorador,
            'soporta_sync_ventas': soporta_sync_ventas,
            'diagnostico': diagnostico_items
        }


# ============================================================================
# INSTANCIA SINGLETON (opcional)
# ============================================================================

_resolver_instance: Optional[SystemCapabilityResolver] = None


def get_resolver() -> SystemCapabilityResolver:
    """
    Obtiene instancia singleton del resolver.
    
    Returns:
        SystemCapabilityResolver instance
    """
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = SystemCapabilityResolver()
    return _resolver_instance


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'SystemCapabilityResolver',
    'Capability',
    'Module',
    'get_resolver',
]
