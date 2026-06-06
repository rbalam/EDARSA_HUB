from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Rutas de Menús Gobernados
=======================================
API para obtener menús dinámicos según permisos del usuario.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
import logging

from core.security import get_current_user
from .menu_service import get_menu_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sistema/menus", tags=["Sistema - Menús"])


@router.get("/modulos", summary="Listar Módulos")
async def listar_modulos(
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista todos los módulos del sistema.
    
    Retorna módulos principales, satélites y portales.
    """
    service = get_menu_service()
    modulos = service.obtener_modulos()
    
    return {
        "modulos": modulos,
        "total": len(modulos),
        "principales": len([m for m in modulos if m.get('EsPrincipal')]),
        "satelites": len([m for m in modulos if m.get('EsSatelite')]),
        "portales": len([m for m in modulos if m.get('EsPortal')])
    }


@router.get("/arbol", summary="Árbol Completo de Menús")
async def obtener_arbol_menus(
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene el árbol completo de módulos y menús.
    
    Útil para administración del sistema.
    """
    service = get_menu_service()
    arbol = service.obtener_arbol_menus()
    
    return {
        "arbol": arbol,
        "total_modulos": len(arbol)
    }


@router.get("/usuario", summary="Menús del Usuario Actual")
async def obtener_menus_usuario(
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene los menús visibles para el usuario actual según sus permisos.
    
    Este endpoint debe usarse para construir el menú lateral del frontend.
    Solo retorna módulos y menús a los que el usuario tiene acceso.
    """
    service = get_menu_service()
    
    # Obtener permisos del usuario
    permisos = current_user.get('permissions', [])
    usuario_id = current_user.get('user_id')
    email = current_user.get('email', '')
    
    # Verificar si es SuperAdmin por email o rol
    roles = current_user.get('roles', [])
    role = current_user.get('role', '')  # Rol directo del usuario
    es_super_admin = False
    
    # Verificar por email de admin conocido
    admin_emails = ['admin@edarsa.com', 'superadmin@edarsa.com', 'ricardo@edarsa.com.mx']
    if email.lower() in [e.lower() for e in admin_emails]:
        es_super_admin = True
    
    # Verificar por rol directo (SUPERADMIN, Administrador, etc.)
    admin_roles = ['SUPERADMIN', 'SuperAdministrador', 'Administrador', 'ADMIN', 'Admin']
    if role in admin_roles or (isinstance(role, str) and role.upper() in [r.upper() for r in admin_roles]):
        es_super_admin = True
    
    # Verificar por lista de roles
    if isinstance(roles, list):
        for r in roles:
            rol_nombre = None
            if isinstance(r, dict):
                rol_nombre = r.get('nombre') or r.get('CodigoRol') or r.get('NombreRol')
            elif isinstance(r, str):
                rol_nombre = r
            
            if rol_nombre and (rol_nombre in admin_roles or rol_nombre.upper() in [ar.upper() for ar in admin_roles]):
                es_super_admin = True
                break
    
    if es_super_admin:
        # SuperAdmin ve todo
        arbol = service.obtener_arbol_menus()
        return {
            "modulos": arbol,
            "total": len(arbol),
            "es_super_admin": True
        }
    
    # Usuario normal: filtrar por permisos
    menus = service.obtener_menus_usuario(usuario_id, permisos)
    
    return {
        "modulos": menus,
        "total": len(menus),
        "es_super_admin": False
    }


@router.get("/modulo/{modulo_id}", summary="Menús de un Módulo")
async def obtener_menus_modulo(
    modulo_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene los menús de un módulo específico.
    """
    service = get_menu_service()
    menus = service.obtener_menus_modulo(modulo_id)
    
    return {
        "modulo_id": modulo_id,
        "menus": menus,
        "total": len(menus)
    }
