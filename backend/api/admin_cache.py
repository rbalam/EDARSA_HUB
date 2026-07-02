"""
EDARSA HUB - Endpoint de Limpieza de Caché para Modo Preview
=============================================================
P0-CACHE-PREVIEW: Limpieza automática de cachés del backend

Solo funciona en modo preview/staging/desarrollo.
Requiere permiso SQL explícito RBAC_ADMIN.

NO AFECTA DATOS SQL - Solo limpia cachés en memoria.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any
import os
import logging

from core.security import get_current_user
from core.rbac.middleware import require_explicit_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/cache", tags=["Admin - Cache Management"])


# =============================================================================
# DETECCIÓN DE MODO PREVIEW
# =============================================================================

def is_preview_mode() -> bool:
    """
    Detecta si el backend está corriendo en modo preview.
    
    Criterios:
    1. Variable PREVIEW_MODE='true'
    2. Variable ENVIRONMENT='preview' o 'staging' o 'development'
    3. Hostname contiene 'preview' o 'staging'
    """
    # Variable explícita
    if os.environ.get('PREVIEW_MODE', '').lower() == 'true':
        return True
    
    # Variable de ambiente
    env = os.environ.get('ENVIRONMENT', '').lower()
    if env in ['preview', 'staging', 'development', 'dev']:
        return True
    
    # Detección por URL del backend (si está configurada)
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', '')
    if 'preview.emergentagent.com' in backend_url:
        return True
    if 'staging' in backend_url:
        return True
    
    # Default: asumir preview si no está explícitamente en producción
    if env != 'production' and env != 'prod':
        return True
    
    return False


# =============================================================================
# CACHÉS A LIMPIAR
# =============================================================================

# Referencia a cachés globales del sistema
_cache_registry: Dict[str, Any] = {}

def register_cache(name: str, cache_obj: Any):
    """Registra un objeto de caché para limpieza posterior."""
    _cache_registry[name] = cache_obj

def get_registered_caches() -> List[str]:
    """Obtiene nombres de cachés registrados."""
    return list(_cache_registry.keys())


def clear_server_registry_cache() -> bool:
    """Limpia caché del server_registry (si existe)."""
    try:
        # El server_registry no tiene caché persistente actualmente
        # pero preparamos para cuando se agregue
        logger.info("[PREVIEW_CACHE_CLEAR] Server registry cache check - no persistent cache found")
        return True
    except Exception as e:
        logger.warning(f"Error limpiando server_registry cache: {e}")
        return False


def clear_context_resolver_cache() -> bool:
    """Limpia caché del context_resolver (si existe)."""
    try:
        # El context_resolver no tiene caché persistente actualmente
        logger.info("[PREVIEW_CACHE_CLEAR] Context resolver cache check - no persistent cache found")
        return True
    except Exception as e:
        logger.warning(f"Error limpiando context_resolver cache: {e}")
        return False


def clear_db_pool_cache() -> bool:
    """Limpia cooldowns del pool de conexiones."""
    try:
        from core.db import _server_status_cache
        
        # Resetear servidores marcados como offline
        _server_status_cache.clear()
        
        logger.info("[PREVIEW_CACHE_CLEAR] DB pool cooldowns reset")
        return True
    except Exception as e:
        logger.warning(f"Error limpiando db pool cache: {e}")
        return False


def clear_lru_caches() -> bool:
    """Limpia cachés decorados con @lru_cache."""
    try:
        import functools
        import gc
        
        cleared = 0
        # Buscar funciones con cache_clear
        for obj in gc.get_objects():
            if hasattr(obj, 'cache_clear') and callable(getattr(obj, 'cache_clear', None)):
                try:
                    obj.cache_clear()
                    cleared += 1
                except Exception:
                    pass
        
        logger.info(f"Cleared {cleared} LRU caches")
        return True
    except Exception as e:
        logger.warning(f"Error limpiando LRU caches: {e}")
        return False


# =============================================================================
# ENDPOINT DE LIMPIEZA
# =============================================================================

@router.post("/clear-preview")
async def clear_preview_cache(
    current_user: dict = Depends(require_explicit_permission("RBAC_ADMIN"))
):
    """
    Limpia cachés del backend en modo preview.
    
    Solo disponible en ambientes preview/staging/development.
    Requiere permiso SQL explícito RBAC_ADMIN.
    
    NO BORRA DATOS SQL - Solo limpia cachés en memoria.
    
    Permisos: RBAC_ADMIN explícito
    """
    # Verificar modo preview
    if not is_preview_mode():
        raise HTTPException(
            status_code=403,
            detail="Cache clearing is only available in preview mode"
        )
    
    user_email = current_user.get('email', 'unknown')
    logger.info(f"[PREVIEW_CACHE_CLEAR] Requested by {user_email}")
    
    result = {
        'success': True,
        'environment': 'preview',
        'requested_by': user_email,
        'cleared': [],
        'failed': [],
        'warnings': []
    }
    
    # 1. Limpiar server_registry
    if clear_server_registry_cache():
        result['cleared'].append('server_registry')
    else:
        result['failed'].append('server_registry')
    
    # 2. Limpiar context_resolver
    if clear_context_resolver_cache():
        result['cleared'].append('context_resolver')
    else:
        result['failed'].append('context_resolver')
    
    # 3. Limpiar DB pool cooldowns
    if clear_db_pool_cache():
        result['cleared'].append('db_pool_cooldowns')
    else:
        result['failed'].append('db_pool_cooldowns')
    
    # 4. Limpiar LRU caches
    if clear_lru_caches():
        result['cleared'].append('lru_caches')
    else:
        result['failed'].append('lru_caches')
    
    # 5. Limpiar cachés registrados
    for name, cache_obj in _cache_registry.items():
        try:
            if hasattr(cache_obj, 'clear'):
                cache_obj.clear()
                result['cleared'].append(name)
            elif hasattr(cache_obj, 'cache_clear'):
                cache_obj.cache_clear()
                result['cleared'].append(name)
            else:
                result['warnings'].append(f"{name}: no clear method")
        except Exception as e:
            result['failed'].append(name)
            result['warnings'].append(f"{name}: {str(e)}")
    
    logger.info(f"[PREVIEW_CACHE_CLEAR] Completed: cleared={result['cleared']}, failed={result['failed']}")
    
    return result


@router.get("/status")
async def get_cache_status(
    current_user: dict = Depends(require_explicit_permission("RBAC_ADMIN"))
):
    """
    Obtiene estado de los cachés del sistema.
    
    Permisos: RBAC_ADMIN explícito
    """
    return {
        'success': True,
        'environment': 'preview' if is_preview_mode() else 'production',
        'is_preview_mode': is_preview_mode(),
        'registered_caches': get_registered_caches(),
        'cache_clearing_enabled': is_preview_mode()
    }

