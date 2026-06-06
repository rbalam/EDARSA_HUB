"""
EDARSA HUB - Rutas de Menús Gobernados (P5-10B)
===============================================
API para obtener menús dinámicos 100% SQL canónico.
NO HAY HARDCODES de emails ni roles.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Optional
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

    usuario_id = (
        current_user.get("UsuarioID")
        or current_user.get("user_id")
        or current_user.get("id")
        or current_user.get("sub")
    )

    if not usuario_id:
        raise HTTPException(status_code=401, detail="Usuario sin identificador válido")

    menus = service.obtener_menus_usuario(str(usuario_id), unidad_negocio_id)
    es_superadmin = service.es_superadmin(str(usuario_id))

    return {
        "modulos": menus,
        "total": len(menus),
        "es_super_admin": es_superadmin,
        "unidad_negocio_id": unidad_negocio_id,
        "source": "SQL_MENU_CANONICO",
        "hardcoded": False
    }
