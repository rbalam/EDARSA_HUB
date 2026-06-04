"""
EDARSA HUB - System Type Utilities (Global/Core)
================================================
Utilidades centralizadas para normalización y manejo de system_type.

FASE 3A.1 - Cierre técnico del blindaje system_type

Este módulo es la FUENTE DE VERDAD para normalización de system_type
en todo el sistema EDARSA HUB.

OBJETIVO:
- Normalizar system_type a valores estándar (MANAGEMENTPRO, SOFTRESTAURANT, API, UNKNOWN)
- Proporcionar helpers para comparaciones seguras
- Evitar comparaciones directas frágiles como `== "MPRO"` o `== "SR"`

USO:
    from core.system_type_utils import (
        normalize_system_type,
        is_mpro_system,
        is_softrestaurant_system,
        is_api_system,
        is_supported_system_type,
        get_system_type_label
    )

    # Normalización
    normalized = normalize_system_type("MPRO")  # → "MANAGEMENTPRO"
    
    # Comparaciones seguras
    if is_mpro_system(server.get('system_type')):
        # Lógica MPRO
    elif is_softrestaurant_system(server.get('system_type')):
        # Lógica SoftRestaurant
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging


# ============================================================================
# CONSTANTES DE SYSTEM_TYPE
# ============================================================================

class SystemType(str, Enum):
    """Tipos de sistema origen soportados."""
    SOFTRESTAURANT = "SOFTRESTAURANT"
    MANAGEMENTPRO = "MANAGEMENTPRO"
    API = "API"
    UNKNOWN = "UNKNOWN"


# Mapeo de variantes a sistema normalizado
SYSTEM_TYPE_MAP = {
    # ManagementPro variantes
    "MPRO": SystemType.MANAGEMENTPRO,
    "MANAGEMENTPRO": SystemType.MANAGEMENTPRO,
    "MANAGEMENT_PRO": SystemType.MANAGEMENTPRO,
    "MANAGEMENT PRO": SystemType.MANAGEMENTPRO,
    "MANAGMENTPRO": SystemType.MANAGEMENTPRO,   # Typo común
    "MANAGMENT_PRO": SystemType.MANAGEMENTPRO,  # Typo común
    "MANAGMENT PRO": SystemType.MANAGEMENTPRO,  # Typo común
    "MANAG": SystemType.MANAGEMENTPRO,
    
    # SoftRestaurant variantes
    "SOFTRESTAURANT": SystemType.SOFTRESTAURANT,
    "SOFTRESTAURANT_PRO": SystemType.SOFTRESTAURANT,  # SR Pro variant
    "SOFTRESTAURANTPRO": SystemType.SOFTRESTAURANT,   # SR Pro variant
    "SR": SystemType.SOFTRESTAURANT,
    "SR_PRO": SystemType.SOFTRESTAURANT,
    "SOFT_RESTAURANT": SystemType.SOFTRESTAURANT,
    "SOFT RESTAURANT": SystemType.SOFTRESTAURANT,
    "SOFT": SystemType.SOFTRESTAURANT,
    "SOFTREST": SystemType.SOFTRESTAURANT,
    
    # API variantes
    "API": SystemType.API,
    "LOCAL_API": SystemType.API,
    "API_LOCAL": SystemType.API,
    "LOCALAPI": SystemType.API,
}

# Labels para UI
SYSTEM_TYPE_LABELS = {
    SystemType.SOFTRESTAURANT: "SoftRestaurant",
    SystemType.MANAGEMENTPRO: "ManagementPro",
    SystemType.API: "API Local",
    SystemType.UNKNOWN: "Desconocido",
}


# ============================================================================
# FUNCIONES DE NORMALIZACIÓN
# ============================================================================

def normalize_system_type(system_type: Optional[str]) -> str:
    """
    Normaliza system_type a valores estándar.
    
    REGLAS DE NORMALIZACIÓN:
    - MPRO, MANAGEMENTPRO, MANAGEMENT_PRO, etc. → "MANAGEMENTPRO"
    - SOFT, SR, SOFTRESTAURANT, etc. → "SOFTRESTAURANT"
    - API, LOCAL_API → "API"
    - None, vacío, desconocido → "UNKNOWN"
    
    Args:
        system_type: Valor de system_type del servidor (puede ser None)
        
    Returns:
        str: Uno de SOFTRESTAURANT, MANAGEMENTPRO, API, UNKNOWN
        
    IMPORTANTE: NUNCA asume SoftRestaurant por default.
    Si el valor es desconocido, retorna UNKNOWN.
    """
    if not system_type:
        return SystemType.UNKNOWN.value
    
    st_upper = system_type.upper().strip()
    
    mapped = SYSTEM_TYPE_MAP.get(st_upper)
    if mapped:
        return mapped.value
    
    return SystemType.UNKNOWN.value


def is_mpro_system(system_type: Optional[str]) -> bool:
    """
    Verifica si el sistema es ManagementPro/MPRO.
    
    Acepta cualquier variante: MPRO, ManagementPro, MANAGEMENT_PRO, etc.
    
    Args:
        system_type: Valor de system_type (puede ser None)
        
    Returns:
        bool: True si es ManagementPro/MPRO
    """
    return normalize_system_type(system_type) == SystemType.MANAGEMENTPRO.value


def is_softrestaurant_system(system_type: Optional[str]) -> bool:
    """
    Verifica si el sistema es SoftRestaurant.
    
    Acepta cualquier variante: SR, SOFT, SoftRestaurant, etc.
    
    Args:
        system_type: Valor de system_type (puede ser None)
        
    Returns:
        bool: True si es SoftRestaurant
    """
    return normalize_system_type(system_type) == SystemType.SOFTRESTAURANT.value


def is_api_system(system_type: Optional[str]) -> bool:
    """
    Verifica si el sistema es API local.
    
    Args:
        system_type: Valor de system_type (puede ser None)
        
    Returns:
        bool: True si es API
    """
    return normalize_system_type(system_type) == SystemType.API.value


def is_supported_system_type(system_type: Optional[str]) -> bool:
    """
    Verifica si el system_type es soportado (no es UNKNOWN).
    
    Args:
        system_type: Valor de system_type (puede ser None)
        
    Returns:
        bool: True si es un sistema soportado
    """
    return normalize_system_type(system_type) != SystemType.UNKNOWN.value


def is_unknown_system(system_type: Optional[str]) -> bool:
    """
    Verifica si el system_type es desconocido.
    
    Args:
        system_type: Valor de system_type (puede ser None)
        
    Returns:
        bool: True si es desconocido o no soportado
    """
    return normalize_system_type(system_type) == SystemType.UNKNOWN.value


def get_system_type_label(system_type: Optional[str]) -> str:
    """
    Obtiene el label legible para UI del system_type.
    
    Args:
        system_type: Valor de system_type (puede ser None)
        
    Returns:
        str: Label legible (ej: "ManagementPro", "SoftRestaurant")
    """
    normalized = normalize_system_type(system_type)
    return SYSTEM_TYPE_LABELS.get(SystemType(normalized), "Desconocido")


# ============================================================================
# RESPUESTAS ESTÁNDAR
# ============================================================================

def get_unsupported_system_response(
    system_type: Optional[str],
    endpoint: str = "",
    feature: str = ""
) -> Dict[str, Any]:
    """
    Genera respuesta estándar para system_type no soportado.
    
    Args:
        system_type: Valor original de system_type
        endpoint: Nombre del endpoint (opcional)
        feature: Nombre de la funcionalidad (opcional)
        
    Returns:
        Dict con estructura estándar de error
    """
    normalized = normalize_system_type(system_type)
    context = feature or endpoint or "esta funcionalidad"
    
    return {
        "status": "UNSUPPORTED_SYSTEM_TYPE",
        "data": [],
        "meta": {
            "system_type": system_type,
            "system_type_normalized": normalized
        },
        "warnings": [],
        "error": {
            "code": "UNSUPPORTED_SYSTEM_TYPE",
            "message": f"El tipo de sistema '{system_type}' no está soportado para {context}",
            "technical_detail": f"system_type_normalized={normalized}"
        }
    }


def get_not_available_response(
    system_type: Optional[str],
    feature: str,
    available_for: List[str] = None
) -> Dict[str, Any]:
    """
    Genera respuesta estándar para funcionalidad no disponible en este sistema.
    
    Args:
        system_type: Valor original de system_type
        feature: Nombre de la funcionalidad
        available_for: Lista de sistemas donde está disponible (ej: ["MPRO"])
        
    Returns:
        Dict con estructura estándar de error
    """
    normalized = normalize_system_type(system_type)
    available = ", ".join(available_for) if available_for else "otros sistemas"
    
    return {
        "status": "NOT_AVAILABLE_FOR_SYSTEM",
        "data": [],
        "meta": {
            "system_type": system_type,
            "system_type_normalized": normalized
        },
        "warnings": [f"'{feature}' solo está disponible para: {available}"],
        "error": {
            "code": "NOT_AVAILABLE_FOR_SYSTEM",
            "message": f"'{feature}' no está implementado para sistemas {get_system_type_label(system_type)}",
            "technical_detail": None
        }
    }


# ============================================================================
# LOGGING HELPERS
# ============================================================================

def log_system_type_normalized(
    original: Optional[str],
    normalized: str,
    context: str = "",
    server_id: str = None
) -> None:
    """
    Log estándar para normalización de system_type.
    
    Formato: [SYSTEM_TYPE][NORMALIZED] original=X normalized=Y context=Z
    """
    logging.info(
        f"[SYSTEM_TYPE][NORMALIZED] "
        f"original={original or 'None'} "
        f"normalized={normalized} "
        f"server_id={server_id or 'N/A'} "
        f"context={context}"
    )


def log_system_type_check(
    system_type: Optional[str],
    check_type: str,
    result: bool,
    endpoint: str = ""
) -> None:
    """
    Log estándar para verificación de system_type.
    
    Formato: [SYSTEM_TYPE][CHECK] check=is_mpro result=True endpoint=X
    """
    logging.debug(
        f"[SYSTEM_TYPE][CHECK] "
        f"check={check_type} "
        f"system_type={system_type or 'None'} "
        f"result={result} "
        f"endpoint={endpoint}"
    )


# ============================================================================
# CACHE KEY HELPERS
# ============================================================================

def build_cache_key_with_system_type(
    prefix: str,
    endpoint: str,
    server_id: str,
    system_type: Optional[str],
    **kwargs
) -> str:
    """
    Construye una cache_key que incluye system_type_normalized.
    
    Garantiza que MPRO y SoftRestaurant NUNCA compartan caché.
    
    Args:
        prefix: Prefijo del módulo (ej: "compras", "comercial")
        endpoint: Nombre del endpoint
        server_id: ID del servidor
        system_type: Valor de system_type (será normalizado)
        **kwargs: Parámetros adicionales (sucursal_id, fecha_inicio, etc.)
        
    Returns:
        str: Cache key formateada
        
    Ejemplo:
        build_cache_key_with_system_type(
            "compras", "inventarios", "server-123", "MPRO",
            sucursal_id="0021", fecha_inicio="2025-01-01"
        )
        → "compras:inventarios:server-123:MANAGEMENTPRO:sucursal_id=0021:fecha_inicio=2025-01-01"
    """
    normalized = normalize_system_type(system_type)
    
    # Construir partes de la key
    parts = [prefix, endpoint, server_id, normalized]
    
    # Agregar parámetros adicionales ordenados
    for key in sorted(kwargs.keys()):
        value = kwargs[key]
        if value is not None:
            parts.append(f"{key}={value}")
    
    cache_key = ":".join(parts)
    
    logging.debug(f"[CACHE_KEY][BUILT] {cache_key}")
    return cache_key


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Constantes
    'SystemType',
    'SYSTEM_TYPE_MAP',
    'SYSTEM_TYPE_LABELS',
    # Funciones de normalización
    'normalize_system_type',
    'is_mpro_system',
    'is_softrestaurant_system',
    'is_api_system',
    'is_supported_system_type',
    'is_unknown_system',
    'get_system_type_label',
    # Respuestas estándar
    'get_unsupported_system_response',
    'get_not_available_response',
    # Logging
    'log_system_type_normalized',
    'log_system_type_check',
    # Cache
    'build_cache_key_with_system_type',
    # SQL Filters
    'get_system_type_sql_values',
    'build_system_type_sql_filter',
]


# ============================================================================
# FUNCIONES SQL PARA FILTROS
# ============================================================================

def get_system_type_sql_values(target_type: str) -> list:
    """
    Obtiene lista de valores SQL para filtrar por un tipo de sistema.
    
    Args:
        target_type: Tipo objetivo ('SOFTRESTAURANT' o 'MANAGEMENTPRO')
        
    Returns:
        Lista de strings con todas las variantes conocidas
        
    Ejemplo:
        get_system_type_sql_values('SOFTRESTAURANT')
        → ['SOFTRESTAURANT', 'SOFTRESTAURANT_PRO', 'SR', 'SOFT', ...]
    """
    target_enum = None
    if target_type.upper() in ['SOFTRESTAURANT', 'SR', 'SOFT']:
        target_enum = SystemType.SOFTRESTAURANT
    elif target_type.upper() in ['MANAGEMENTPRO', 'MPRO']:
        target_enum = SystemType.MANAGEMENTPRO
    elif target_type.upper() == 'API':
        target_enum = SystemType.API
    else:
        return [target_type]
    
    # Obtener todas las variantes que mapean a este tipo
    values = [k for k, v in SYSTEM_TYPE_MAP.items() if v == target_enum]
    return sorted(set(values))


def build_system_type_sql_filter(column_name: str, target_type: str) -> str:
    """
    Construye filtro SQL IN() para system_type usando variantes centralizadas.
    
    Args:
        column_name: Nombre de la columna SQL (ej: 's.system_type')
        target_type: Tipo objetivo ('SOFTRESTAURANT' o 'MANAGEMENTPRO')
        
    Returns:
        String SQL con filtro IN()
        
    Ejemplo:
        build_system_type_sql_filter('s.system_type', 'SOFTRESTAURANT')
        → "s.system_type IN ('SOFTRESTAURANT', 'SOFTRESTAURANT_PRO', 'SR', ...)"
    """
    values = get_system_type_sql_values(target_type)
    quoted = ", ".join(f"'{v}'" for v in values)
    return f"{column_name} IN ({quoted})"
