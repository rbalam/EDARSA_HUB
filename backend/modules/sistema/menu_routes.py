"""
EDARSA HUB - Rutas de Menús Gobernados (P5-10B)
===============================================
API para obtener menús dinámicos 100% SQL canónico.
NO HAY HARDCODES de emails ni roles.
"""

from fastapi import APIRouter, Depends, Body
from typing import Dict, Optional, Any
import logging

from core.security import get_current_user
from .menu_service import get_menu_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sistema/menus", tags=["Sistema - Menús"])


@router.get("/usuario", summary="Menús del Usuario Actual")
async def obtener_menus_usuario(
    unidad_negocio_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    P5-10B: Menús 100% SQL canónico sin hardcodes.
    El backend determina permisos desde SQL.
    Si se envía `unidad_negocio_id`, los módulos se filtran por el contexto
    activo del usuario (Usuario_RolesContexto) en esa unidad de negocio.
    """
    service = get_menu_service()
    resolved = service.obtener_menus_current_user(current_user, unidad_negocio_id)
    menus = resolved["menus"]

    return {
        "modulos": menus,
        "total": len(menus),
        "es_super_admin": resolved["es_superadmin"],
        "unidad_negocio_id": unidad_negocio_id,
        "source": "SQL_MENU_CANONICO",
        "hardcoded": False
    }

@router.get("/favoritos", summary="Favoritos de Menú del Usuario Actual")
async def obtener_menu_favoritos(
    current_user: Dict = Depends(get_current_user)
):
    """
    Favoritos de menú por usuario desde SQL canónico.
    No usa MongoDB. No duplica el menú: guarda solo rutas permitidas.
    """
    service = get_menu_service()
    return service.obtener_favoritos_current_user(current_user)


@router.put("/favoritos", summary="Actualizar Favoritos de Menú del Usuario Actual")
async def actualizar_menu_favoritos(
    payload: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Persiste favoritos por usuario en SQL canónico.
    Payload: { "rutas": ["/comercial", "/tablero-ejecutivo"] }
    """
    rutas = payload.get("rutas") if isinstance(payload, dict) else []
    service = get_menu_service()
    return service.actualizar_favoritos_current_user(current_user, rutas)

