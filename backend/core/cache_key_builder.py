"""
EDARSA HUB - Central Cache Key Builder
======================================

FASE 3C.1: Política Global de Cache Contextual.

Define funciones centralizadas para construir cache_keys que incluyen
todo el contexto necesario para evitar:
- Datos pegados entre servidores
- Datos pegados entre sucursales
- Datos pegados entre usuarios con permisos diferentes
- Datos pegados entre sistemas origen (SoftRestaurant vs MPRO)
- Datos pegados entre rangos de fechas

REGLA CENTRAL:
Un cache solo es válido mientras no cambie el contexto completo que lo generó.

USO:
    from core.cache_key_builder import build_context_cache_key, CacheContext

CREADO: FASE 3C.1 - Diciembre 2025
REFACTOR: FASE 17 - Abril 2026 (Dataclass para parámetros)
"""

import hashlib
import json
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CacheContext:
    """Contexto para construcción de cache keys."""
    namespace: str
    endpoint: Optional[str] = None
    server_id: Optional[str] = None
    sucursal_id: Optional[str] = None
    unidad_negocio_id: Optional[str] = None
    empresa_id: Optional[str] = None
    system_type: Optional[str] = None
    system_type_normalized: Optional[str] = None
    user: Optional[Dict] = None
    user_id: Optional[str] = None
    permissions_hash: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    fecha: Optional[str] = None
    filters: Optional[Dict] = None
    version: Optional[str] = None
    config_version: Optional[str] = None
    extra: Dict = field(default_factory=dict)


def stable_hash(value: Any, length: int = 8) -> str:
    """
    Genera un hash estable y corto de cualquier valor.
    
    Args:
        value: Valor a hashear (str, dict, list, etc.)
        length: Longitud del hash resultante
        
    Returns:
        Hash hexadecimal de la longitud especificada
        
    Note:
        - Ordena diccionarios y listas para garantizar estabilidad
        - No incluye secretos - verificar antes de llamar
    """
    if value is None:
        return "null"
    
    # Convertir a string de forma estable
    if isinstance(value, dict):
        # Ordenar claves para estabilidad
        stable_str = json.dumps(value, sort_keys=True, default=str)
    elif isinstance(value, (list, tuple)):
        # Ordenar si es lista de strings/números simples
        try:
            sorted_list = sorted(value)
            stable_str = json.dumps(sorted_list, default=str)
        except TypeError:
            # No se puede ordenar, usar como está
            stable_str = json.dumps(list(value), default=str)
    else:
        stable_str = str(value)
    
    # Hash SHA256 truncado
    full_hash = hashlib.sha256(stable_str.encode('utf-8')).hexdigest()
    return full_hash[:length]


def build_permissions_hash(user: Optional[Dict], length: int = 8) -> str:
    """
    Construye hash de permisos de usuario para incluir en cache_key.
    
    Args:
        user: Diccionario de usuario con role, allowed_servers, etc.
        length: Longitud del hash
        
    Returns:
        Hash de permisos o "anon" si no hay usuario
        
    Note:
        - Incluye: role, allowed_servers, allowed_sucursales
        - NO incluye: password, token, email, datos personales
    """
    if not user:
        return "anon"
    
    # Extraer solo datos relevantes para permisos (sin datos sensibles)
    permissions_data = {
        'role': user.get('role', 'unknown'),
        'allowed_servers': sorted(user.get('allowed_servers', [])),
        'allowed_sucursales': sorted(user.get('allowed_sucursales', [])),
        'user_id': user.get('id', user.get('user_id', 'unknown'))
    }
    
    return stable_hash(permissions_data, length)


def build_filters_hash(filters: Optional[Dict], length: int = 8) -> str:
    """
    Construye hash de filtros para incluir en cache_key.
    
    Args:
        filters: Diccionario de filtros
        length: Longitud del hash
        
    Returns:
        Hash de filtros o "nofilter" si vacío
    """
    if not filters:
        return "nofilter"
    
    # Filtrar valores None y vacíos
    clean_filters = {k: v for k, v in filters.items() if v is not None and v != ''}
    
    if not clean_filters:
        return "nofilter"
    
    return stable_hash(clean_filters, length)


def build_context_cache_key(
    namespace: str,
    endpoint: str = None,
    server_id: str = None,
    sucursal_id: str = None,
    unidad_negocio_id: str = None,
    empresa_id: str = None,
    system_type: str = None,
    system_type_normalized: str = None,
    user: Optional[Dict] = None,
    user_id: str = None,
    permissions_hash: str = None,
    fecha_inicio: str = None,
    fecha_fin: str = None,
    fecha: str = None,
    filters: Optional[Dict] = None,
    version: str = None,
    config_version: str = None,
    **extra
) -> str:
    """
    Construye cache_key completa con todo el contexto necesario.
    
    Args:
        namespace: Módulo o área (comercial, compras, finanzas, etc.)
        endpoint: Nombre del endpoint o operación
        server_id: ID del servidor (SQL id o mongodb_id)
        sucursal_id: ID de la sucursal
        unidad_negocio_id: ID de la unidad de negocio
        empresa_id: ID de la empresa
        system_type: Tipo de sistema (MPRO, SoftRestaurant, etc.)
        system_type_normalized: Tipo normalizado (preferido sobre system_type)
        user: Diccionario de usuario (para extraer permissions_hash)
        user_id: ID de usuario (alternativa a extraer de user)
        permissions_hash: Hash de permisos pre-calculado
        fecha_inicio: Fecha inicio del rango
        fecha_fin: Fecha fin del rango
        fecha: Fecha única (alternativa a fecha_inicio/fecha_fin)
        filters: Diccionario de filtros adicionales
        version: Versión de API o formato
        config_version: Versión de configuración
        **extra: Parámetros adicionales
        
    Returns:
        Cache key completa con todos los contextos
        
    Example:
        key = build_context_cache_key(
            namespace="comercial",
            endpoint="dashboard",
            server_id="abc123",
            sucursal_id="suc001",
            system_type_normalized="MANAGEMENTPRO",
            fecha="2026-04-25"
        )
        # Resultado: "comercial:dashboard:abc123:suc001:MANAGEMENTPRO:2026-04-25"
    """
    parts = [namespace]
    
    if endpoint:
        parts.append(endpoint)
    
    # Contexto de servidor
    if server_id:
        parts.append(f"srv:{server_id[:12]}" if len(server_id) > 12 else f"srv:{server_id}")
    
    # Contexto de ubicación
    if unidad_negocio_id:
        parts.append(f"un:{unidad_negocio_id}")
    if empresa_id:
        parts.append(f"emp:{empresa_id}")
    if sucursal_id:
        parts.append(f"suc:{sucursal_id}")
    
    # Sistema origen (crítico para no mezclar SR y MPRO)
    if system_type_normalized:
        parts.append(f"sys:{system_type_normalized}")
    elif system_type:
        # Normalizar si se proporciona sin normalizar
        try:
            from core.system_type_utils import normalize_system_type
            normalized = normalize_system_type(system_type)
            parts.append(f"sys:{normalized}")
        except ImportError:
            parts.append(f"sys:{system_type.upper()}")
    
    # Contexto temporal
    if fecha_inicio and fecha_fin:
        parts.append(f"range:{fecha_inicio}_{fecha_fin}")
    elif fecha:
        parts.append(f"date:{fecha}")
    
    # Contexto de permisos (si el resultado depende de permisos)
    if permissions_hash:
        parts.append(f"perm:{permissions_hash}")
    elif user:
        perm_hash = build_permissions_hash(user)
        parts.append(f"perm:{perm_hash}")
    elif user_id:
        parts.append(f"uid:{user_id[:8]}" if len(user_id) > 8 else f"uid:{user_id}")
    
    # Filtros
    if filters:
        filter_hash = build_filters_hash(filters)
        if filter_hash != "nofilter":
            parts.append(f"flt:{filter_hash}")
    
    # Versión de configuración
    if version:
        parts.append(f"v:{version}")
    if config_version:
        parts.append(f"cfg:{config_version}")
    
    # Parámetros extra ordenados
    for key, value in sorted(extra.items()):
        if value is not None and value != '':
            parts.append(f"{key}:{value}")
    
    cache_key = ":".join(parts)
    
    # Log para auditoría (sin datos sensibles)
    logger.debug(f"[CACHE][KEY_BUILT] {cache_key[:80]}...")
    
    return cache_key


def build_cache_key_from_context(ctx: CacheContext) -> str:
    """
    Construye cache_key desde un CacheContext dataclass.
    Versión más limpia de build_context_cache_key.
    
    Args:
        ctx: Instancia de CacheContext con todos los parámetros
        
    Returns:
        Cache key completa con todos los contextos
        
    Example:
        ctx = CacheContext(
            namespace="comercial",
            endpoint="dashboard",
            server_id="abc123",
            fecha="2026-04-25"
        )
        key = build_cache_key_from_context(ctx)
    """
    return build_context_cache_key(
        namespace=ctx.namespace,
        endpoint=ctx.endpoint,
        server_id=ctx.server_id,
        sucursal_id=ctx.sucursal_id,
        unidad_negocio_id=ctx.unidad_negocio_id,
        empresa_id=ctx.empresa_id,
        system_type=ctx.system_type,
        system_type_normalized=ctx.system_type_normalized,
        user=ctx.user,
        user_id=ctx.user_id,
        permissions_hash=ctx.permissions_hash,
        fecha_inicio=ctx.fecha_inicio,
        fecha_fin=ctx.fecha_fin,
        fecha=ctx.fecha,
        filters=ctx.filters,
        version=ctx.version,
        config_version=ctx.config_version,
        **ctx.extra
    )


def validate_cache_context(
    cache_key: str,
    current_context: Dict
) -> bool:
    """
    Valida que un cache_key sigue siendo válida para el contexto actual.
    
    Args:
        cache_key: Cache key a validar
        current_context: Contexto actual con server_id, system_type, etc.
        
    Returns:
        True si el cache sigue siendo válido
        
    Note:
        Esta es una validación básica por componentes del key.
        Para validación completa, regenerar el key y comparar.
    """
    # Validaciones básicas de contexto
    if 'system_type_normalized' in current_context:
        expected = f"sys:{current_context['system_type_normalized']}"
        if expected not in cache_key:
            logger.warning("[CACHE][CONTEXT_MISMATCH] system_type no coincide")
            return False
    
    if 'server_id' in current_context:
        server_prefix = f"srv:{current_context['server_id'][:12]}"
        if server_prefix not in cache_key:
            logger.warning("[CACHE][CONTEXT_MISMATCH] server_id no coincide")
            return False
    
    return True


# Función de utilidad para crear fingerprint de configuración
def build_config_fingerprint(config: Dict, include_keys: List[str] = None) -> str:
    """
    Crea fingerprint de configuración para detectar cambios.
    
    Args:
        config: Diccionario de configuración
        include_keys: Lista de claves a incluir (None = todas excepto sensibles)
        
    Returns:
        Fingerprint de la configuración
    """
    SENSITIVE_KEYS = {'password', 'api_key', 'secret', 'token', 'key'}
    
    if include_keys:
        filtered = {k: config.get(k) for k in include_keys if k not in SENSITIVE_KEYS}
    else:
        filtered = {k: v for k, v in config.items() if k.lower() not in SENSITIVE_KEYS}
    
    return stable_hash(filtered, length=12)
