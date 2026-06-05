"""
Resolver canónico unidad -> servidor centralizado.
NO imprime credenciales.
NO devuelve passwords en logs.
"""
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

def get_server_for_unidad(unidad_codigo: str) -> Optional[Dict]:
    """
    Resolver canónico: código de unidad -> configuración de servidor.
    Usa el server_registry existente.
    """
    if not unidad_codigo:
        return None
    
    try:
        from core.server_registry import get_server_by_unidad_codigo
        return get_server_by_unidad_codigo(unidad_codigo)
    except Exception as e:
        logger.error(f"Error resolviendo servidor para {unidad_codigo}: {e}")
        return None

def assert_server_available(unidad_codigo: str) -> Dict:
    """
    Valida si una unidad tiene servidor disponible para sync.
    """
    result = get_server_for_unidad(unidad_codigo)
    
    if not result:
        return {
            "ok": False,
            "unidad": unidad_codigo,
            "reason": "UNIDAD_O_SERVIDOR_NO_ENCONTRADO"
        }
    
    if not result.get("server_id"):
        return {
            "ok": False,
            "unidad": unidad_codigo,
            "reason": "SERVIDOR_NO_ASOCIADO_EN_UNIDADES_NEGOCIO"
        }
    
    if not result.get("servidor_activo"):
        return {
            "ok": False,
            "unidad": unidad_codigo,
            "reason": "SERVIDOR_INACTIVO"
        }
    
    return {
        "ok": True,
        "unidad": unidad_codigo,
        "server_id": result.get("server_id"),
        "servidor_nombre": result.get("servidor_nombre"),
        "host": result.get("host"),
        "system_type": result.get("servidor_system_type")
    }
