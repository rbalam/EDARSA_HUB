"""
EDARSA HUB - System Capability Integration (FASE 6)
====================================================
Funciones auxiliares para integrar SystemCapabilityResolver en módulos existentes
de forma NO DESTRUCTIVA.

Este módulo proporciona funciones que pueden ser llamadas opcionalmente por:
- Explorador BD (validar sistemas explorables)
- Sync Históricos (validar candidatos para sync de ventas)

REGLAS:
- NO modificar comportamiento existente
- Funciones auxiliares que se llaman DESPUÉS de la lógica legacy
- Si el resolver falla, retornar True (permisivo) para no romper funcionalidad
- Logs de diagnóstico para monitorear adopción gradual

Autor: Arquitecto Senior Backend
Fecha: 2025-12-XX
"""

import logging
from typing import List, Dict, Any, Optional, Set

from core.system_capability_resolver import (
    SystemCapabilityResolver,
    Capability,
    get_resolver
)

logger = logging.getLogger(__name__)


# ============================================================================
# EXPLORADOR BD - VALIDACIÓN DE SISTEMAS EXPLORABLES
# ============================================================================

def is_system_explorable(system_type: str) -> bool:
    """
    Verifica si un sistema es explorable según el Catálogo Maestro.
    
    FASE 6 - Integración No Destructiva:
    - Si el resolver confirma, retorna True
    - Si no encuentra el sistema, retorna True (permisivo para compatibilidad)
    - Si hay error, retorna True (no bloquear por falla del resolver)
    
    Args:
        system_type: Código o variante del sistema (ej: "MPRO", "ManagmentPro", "SOFRESATAURANT_ENTER")
    
    Returns:
        True si el sistema es explorable o si hay duda (permisivo)
    """
    try:
        resolver = get_resolver()
        
        # Normalizar primero
        normalized = resolver.normalize_system_type(system_type)
        
        if not normalized.get('found'):
            logger.debug(
                f"[CAPABILITY-INTEGRATION] Sistema '{system_type}' no encontrado en catálogo. "
                f"Permitiendo por compatibilidad."
            )
            return True
        
        codigo = normalized['codigo_sistema']
        
        # Verificar capacidad EXPLORADOR_BD
        supports = resolver.system_supports(codigo, Capability.EXPLORADOR_BD.value)
        
        logger.debug(
            f"[CAPABILITY-INTEGRATION] {system_type} -> {codigo}: "
            f"EXPLORADOR_BD={supports}"
        )
        
        return supports
        
    except Exception as e:
        logger.warning(
            f"[CAPABILITY-INTEGRATION] Error verificando explorable para '{system_type}': {e}. "
            f"Permitiendo por seguridad."
        )
        return True


def get_explorable_system_codes() -> Set[str]:
    """
    Obtiene el set de códigos de sistema que soportan EXPLORADOR_BD.
    
    Returns:
        Set de códigos de sistema explorables (ej: {'SOFTRESTAURANT', 'MPRO', 'API_LOCAL'})
    """
    try:
        resolver = get_resolver()
        systems = resolver.get_explorable_systems()
        
        codes = {s['codigo_sistema'] for s in systems}
        
        logger.debug(f"[CAPABILITY-INTEGRATION] Sistemas explorables: {codes}")
        
        return codes
        
    except Exception as e:
        logger.warning(f"[CAPABILITY-INTEGRATION] Error obteniendo sistemas explorables: {e}")
        # Retornar set vacío para no filtrar nada (permisivo)
        return set()


def filter_explorable_connections(connections: List[Dict]) -> List[Dict]:
    """
    Filtra conexiones que pertenecen a sistemas explorables.
    
    FASE 6 - Integración No Destructiva:
    - Si el sistema está en el catálogo con EXPLORADOR_BD, lo incluye
    - Si el sistema NO está en el catálogo, lo incluye (permisivo)
    - Solo excluye si el sistema está en catálogo pero SIN capacidad EXPLORADOR_BD
    
    Args:
        connections: Lista de conexiones con campo 'system_type' o 'sistema_codigo'
    
    Returns:
        Lista filtrada de conexiones explorables
    """
    try:
        resolver = get_resolver()
        explorable_systems = get_explorable_system_codes()
        
        filtered = []
        for conn in connections:
            system_type = conn.get('system_type') or conn.get('sistema_codigo') or ''
            
            # Normalizar
            normalized = resolver.normalize_system_type(system_type)
            
            if not normalized.get('found'):
                # Sistema no en catálogo - incluir por compatibilidad
                filtered.append(conn)
                continue
            
            codigo = normalized['codigo_sistema']
            
            if codigo in explorable_systems:
                filtered.append(conn)
            else:
                logger.info(
                    f"[CAPABILITY-INTEGRATION] Conexión '{conn.get('nombre', '')}' "
                    f"excluida: sistema {codigo} no tiene EXPLORADOR_BD"
                )
        
        return filtered
        
    except Exception as e:
        logger.warning(f"[CAPABILITY-INTEGRATION] Error filtrando conexiones: {e}")
        # Retornar todas las conexiones sin filtrar (permisivo)
        return connections


# ============================================================================
# SYNC HISTÓRICOS - VALIDACIÓN DE CANDIDATOS PARA SYNC VENTAS
# ============================================================================

def is_system_sync_sales_enabled(system_type: str) -> bool:
    """
    Verifica si un sistema soporta sincronización de ventas según el Catálogo Maestro.
    
    FASE 6 - Integración No Destructiva:
    - Si el sistema tiene capacidades SYNC_VENTAS_*, retorna True
    - Si el sistema no tiene esas capacidades, retorna False
    - Si el sistema no está en catálogo, usa lógica legacy (SOFT/MPRO = True)
    
    IMPORTANTE:
    - API_LOCAL/Enterprise retornará FALSE porque no tiene SYNC_VENTAS_* activo
    - Esto es correcto según el seed de FASE 3 (no tiene query_ventas validada)
    
    Args:
        system_type: Código o variante del sistema
    
    Returns:
        True si el sistema soporta sync de ventas
    """
    try:
        resolver = get_resolver()
        
        # Normalizar primero
        normalized = resolver.normalize_system_type(system_type)
        
        if not normalized.get('found'):
            # Sistema no en catálogo - usar lógica legacy
            upper = system_type.upper() if system_type else ''
            legacy_result = 'SOFT' in upper or 'MPRO' in upper or 'MANAGEMENT' in upper
            logger.debug(
                f"[CAPABILITY-INTEGRATION] Sistema '{system_type}' no en catálogo. "
                f"Usando legacy: {legacy_result}"
            )
            return legacy_result
        
        codigo = normalized['codigo_sistema']
        
        # Verificar cualquiera de las capacidades de sync ventas
        sync_capabilities = [
            Capability.SYNC_VENTAS_HISTORICAS.value,
            Capability.SYNC_VENTAS_POR_HORA.value,
            Capability.SYNC_VENTAS_DIA_SEMANA.value
        ]
        
        for cap in sync_capabilities:
            if resolver.system_supports(codigo, cap):
                logger.debug(
                    f"[CAPABILITY-INTEGRATION] {system_type} -> {codigo}: "
                    f"Soporta sync ventas (tiene {cap})"
                )
                return True
        
        logger.info(
            f"[CAPABILITY-INTEGRATION] {system_type} -> {codigo}: "
            f"NO soporta sync ventas (sin capacidades SYNC_VENTAS_*)"
        )
        return False
        
    except Exception as e:
        logger.warning(
            f"[CAPABILITY-INTEGRATION] Error verificando sync ventas para '{system_type}': {e}. "
            f"Usando lógica legacy."
        )
        # Fallback a lógica legacy
        upper = system_type.upper() if system_type else ''
        return 'SOFT' in upper or 'MPRO' in upper or 'MANAGEMENT' in upper


def get_sync_sales_system_codes() -> Set[str]:
    """
    Obtiene el set de códigos de sistema que soportan sync de ventas.
    
    Returns:
        Set de códigos (ej: {'SOFTRESTAURANT', 'MPRO'})
        
    NOTA: API_LOCAL NO debe aparecer aquí
    """
    try:
        resolver = get_resolver()
        systems = resolver.get_sync_sales_systems()
        
        codes = {s['codigo_sistema'] for s in systems}
        
        logger.debug(f"[CAPABILITY-INTEGRATION] Sistemas sync ventas: {codes}")
        
        return codes
        
    except Exception as e:
        logger.warning(f"[CAPABILITY-INTEGRATION] Error obteniendo sistemas sync: {e}")
        # Retornar los conocidos por legacy
        return {'SOFTRESTAURANT', 'MPRO'}


def filter_sync_sales_servers(servers: List[Dict]) -> List[Dict]:
    """
    Filtra servidores que soportan sincronización de ventas.
    
    FASE 6 - Integración No Destructiva:
    - Incluye servidores cuyo sistema tiene SYNC_VENTAS_* activo
    - EXCLUYE API_LOCAL/Enterprise (no tienen capacidad activa)
    - Si el servidor tiene query_ventas configurada Y el sistema lo soporta
    
    Args:
        servers: Lista de servidores con campos 'system_type' y opcionalmente 'query_ventas'
    
    Returns:
        Lista filtrada de servidores candidatos para sync
    """
    try:
        sync_systems = get_sync_sales_system_codes()
        resolver = get_resolver()
        
        filtered = []
        for server in servers:
            system_type = server.get('system_type', '')
            server_name = server.get('nombre', server.get('id', ''))
            
            # Normalizar
            normalized = resolver.normalize_system_type(system_type)
            
            if not normalized.get('found'):
                # Sistema no en catálogo - usar lógica legacy
                upper = system_type.upper() if system_type else ''
                if 'SOFT' in upper or 'MPRO' in upper or 'MANAGEMENT' in upper:
                    filtered.append(server)
                    logger.debug(
                        f"[CAPABILITY-INTEGRATION] Servidor '{server_name}' incluido por legacy "
                        f"(system_type no en catálogo)"
                    )
                continue
            
            codigo = normalized['codigo_sistema']
            
            if codigo in sync_systems:
                filtered.append(server)
                logger.debug(
                    f"[CAPABILITY-INTEGRATION] Servidor '{server_name}' ({codigo}) "
                    f"incluido para sync ventas"
                )
            else:
                logger.info(
                    f"[CAPABILITY-INTEGRATION] Servidor '{server_name}' ({codigo}) "
                    f"EXCLUIDO de sync ventas (sin capacidad activa)"
                )
        
        return filtered
        
    except Exception as e:
        logger.warning(f"[CAPABILITY-INTEGRATION] Error filtrando servidores sync: {e}")
        # Fallback - usar filtro legacy
        return [
            s for s in servers 
            if 'SOFT' in (s.get('system_type', '') or '').upper() 
            or 'MPRO' in (s.get('system_type', '') or '').upper()
        ]


def validate_server_for_sync(server: Dict) -> Dict[str, Any]:
    """
    Valida si un servidor específico puede ser usado para sync de ventas.
    
    Retorna diagnóstico detallado útil para debugging.
    
    Args:
        server: Dict con al menos 'system_type'
    
    Returns:
        Dict con:
        - can_sync: bool
        - reason: str explicativo
        - normalized_system: código normalizado
        - has_capability: bool
    """
    result = {
        'can_sync': False,
        'reason': '',
        'normalized_system': None,
        'has_capability': False,
        'has_query_ventas': bool(server.get('query_ventas'))
    }
    
    try:
        system_type = server.get('system_type', '')
        
        if not system_type:
            result['reason'] = 'system_type vacío'
            return result
        
        resolver = get_resolver()
        normalized = resolver.normalize_system_type(system_type)
        
        if not normalized.get('found'):
            # Fallback legacy
            upper = system_type.upper()
            if 'SOFT' in upper or 'MPRO' in upper:
                result['can_sync'] = True
                result['reason'] = 'Permitido por compatibilidad legacy (sistema no en catálogo)'
            else:
                result['reason'] = f'Sistema "{system_type}" no reconocido'
            return result
        
        codigo = normalized['codigo_sistema']
        result['normalized_system'] = codigo
        
        # Verificar capacidades
        has_sync = is_system_sync_sales_enabled(system_type)
        result['has_capability'] = has_sync
        
        if has_sync:
            result['can_sync'] = True
            result['reason'] = f'Sistema {codigo} tiene capacidades SYNC_VENTAS_* activas'
        else:
            result['reason'] = f'Sistema {codigo} NO tiene capacidades SYNC_VENTAS_* activas'
        
        return result
        
    except Exception as e:
        result['reason'] = f'Error de validación: {e}'
        # Permisivo en caso de error para no bloquear
        system_type = server.get('system_type', '').upper()
        if 'SOFT' in system_type or 'MPRO' in system_type:
            result['can_sync'] = True
            result['reason'] += ' (permitido por fallback legacy)'
        return result


# ============================================================================
# DIAGNÓSTICO Y REPORTING
# ============================================================================

def get_integration_status() -> Dict[str, Any]:
    """
    Obtiene estado de la integración del Catálogo Maestro.
    
    Útil para dashboards y diagnóstico.
    
    Returns:
        Dict con estadísticas y estado de integración
    """
    try:
        resolver = get_resolver()
        
        all_systems = resolver.get_all_systems()
        explorable = resolver.get_explorable_systems()
        sync_sales = resolver.get_sync_sales_systems()
        
        return {
            'integration_active': True,
            'total_systems': len(all_systems),
            'systems': [s['codigo_sistema'] for s in all_systems],
            'explorable_systems': [s['codigo_sistema'] for s in explorable],
            'sync_sales_systems': [s['codigo_sistema'] for s in sync_sales],
            'api_local_in_explorable': 'API_LOCAL' in [s['codigo_sistema'] for s in explorable],
            'api_local_in_sync_sales': 'API_LOCAL' in [s['codigo_sistema'] for s in sync_sales],
            'source': 'EDARSAHUB_SQL',
            'cache_status': 'active'
        }
        
    except Exception as e:
        return {
            'integration_active': False,
            'error': str(e),
            'fallback': 'legacy_system_type_utils'
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Explorador BD
    'is_system_explorable',
    'get_explorable_system_codes',
    'filter_explorable_connections',
    
    # Sync Históricos
    'is_system_sync_sales_enabled',
    'get_sync_sales_system_codes',
    'filter_sync_sales_servers',
    'validate_server_for_sync',
    
    # Diagnóstico
    'get_integration_status',
]
