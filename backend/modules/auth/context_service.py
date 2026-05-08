"""
EDARSA HUB - User Context Service
=================================
Servicio para resolver y gestionar el contexto de usuario.

FASE 2 (Abril 2026):
- Resuelve contexto inicial de sesión
- Obtiene empresas/sucursales permitidas
- Obtiene rol y permisos en contexto
- Mantiene compatibilidad con modelo legacy

PRINCIPIO: EDARSA HUB es el cerebro del sistema.
El contexto se resuelve aquí, no en sistemas externos.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging

from modules.auth.repository import get_db

logger = logging.getLogger(__name__)


async def get_user_context(user_id: str) -> Dict[str, Any]:
    """
    Resuelve el contexto completo de un usuario.
    
    Returns:
        Dict con:
        - user_id
        - email
        - nombre
        - empresa_default (id, nombre)
        - empresas_permitidas (lista de {id, nombre, codigo})
        - rol_actual (nombre del rol RBAC)
        - permisos (lista de códigos de permisos)
        - sucursales_permitidas (lista por empresa)
        - legacy (campos viejos para compatibilidad)
    """
    db = get_db()
    
    # Obtener usuario
    user = await db.users.find_one({'id': user_id}, {'_id': 0, 'password': 0})
    if not user:
        return None
    
    # Obtener empresas permitidas
    empresas_ids = user.get('empresas_permitidas', [])
    empresa_default_id = user.get('empresa_default_id')
    
    # Resolver empresas con nombres
    empresas_permitidas = []
    for emp_id in empresas_ids:
        empresa = await db.empresas.find_one({'id': emp_id}, {'_id': 0})
        if empresa:
            empresas_permitidas.append({
                'id': empresa['id'],
                'nombre': empresa['nombre'],
                'codigo': empresa['codigo']
            })
    
    # Resolver empresa default
    empresa_default = None
    if empresa_default_id:
        emp = await db.empresas.find_one({'id': empresa_default_id}, {'_id': 0})
        if emp:
            empresa_default = {
                'id': emp['id'],
                'nombre': emp['nombre'],
                'codigo': emp['codigo']
            }
    elif empresas_permitidas:
        empresa_default = empresas_permitidas[0]
    
    # Obtener rol RBAC para la empresa default
    rol_actual = None
    permisos = []
    
    if empresa_default:
        asignacion = await db.rbac_usuarios_roles.find_one({
            'user_id': user_id,
            'empresa_id': empresa_default['id'],
            'activo': True
        }, {'_id': 0})
        
        if asignacion:
            rol = await db.rbac_roles.find_one({'id': asignacion['rol_id']}, {'_id': 0})
            if rol:
                rol_actual = rol['nombre']
                # Obtener permisos del rol
                permisos_cursor = db.rbac_permisos.find(
                    {'id': {'$in': rol.get('permisos', [])}},
                    {'_id': 0, 'codigo': 1}
                )
                permisos_docs = await permisos_cursor.to_list(100)
                permisos = [p['codigo'] for p in permisos_docs]
    
    # Obtener sucursales por empresa
    sucursales_por_empresa = {}
    for emp in empresas_permitidas:
        cursor = db.sucursales_catalogo.find(
            {'empresa_id': emp['id'], 'activa': True},
            {'_id': 0, 'id': 1, 'nombre': 1, 'codigo': 1}
        )
        sucursales = await cursor.to_list(100)
        sucursales_por_empresa[emp['id']] = sucursales
    
    return {
        'user_id': user_id,
        'email': user.get('email'),
        'nombre': user.get('name', user.get('nombre', '')),
        'empresa_default': empresa_default,
        'empresas_permitidas': empresas_permitidas,
        'rol_actual': rol_actual or user.get('role', 'Usuario'),  # Fallback a legacy
        'permisos': permisos,
        'sucursales_por_empresa': sucursales_por_empresa,
        # Legacy para compatibilidad
        'legacy': {
            'role': user.get('role'),
            'allowed_servers': user.get('allowed_servers', []),
            'allowed_sucursales': user.get('allowed_sucursales', {})
        }
    }


async def get_user_context_for_empresa(user_id: str, empresa_id: str) -> Dict[str, Any]:
    """
    Resuelve el contexto de un usuario para una empresa específica.
    Útil cuando el usuario cambia de empresa activa.
    """
    db = get_db()
    
    # Verificar que el usuario tiene acceso a esa empresa
    user = await db.users.find_one({'id': user_id}, {'_id': 0, 'password': 0})
    if not user:
        return None
    
    empresas_permitidas = user.get('empresas_permitidas', [])
    if empresa_id not in empresas_permitidas:
        return {'error': 'Usuario no tiene acceso a esta empresa'}
    
    # Obtener empresa
    empresa = await db.empresas.find_one({'id': empresa_id}, {'_id': 0})
    if not empresa:
        return {'error': 'Empresa no encontrada'}
    
    # Obtener rol y permisos para esta empresa
    asignacion = await db.rbac_usuarios_roles.find_one({
        'user_id': user_id,
        'empresa_id': empresa_id,
        'activo': True
    }, {'_id': 0})
    
    rol_actual = None
    permisos = []
    
    if asignacion:
        rol = await db.rbac_roles.find_one({'id': asignacion['rol_id']}, {'_id': 0})
        if rol:
            rol_actual = rol['nombre']
            cursor = db.rbac_permisos.find(
                {'id': {'$in': rol.get('permisos', [])}},
                {'_id': 0, 'codigo': 1}
            )
            permisos_docs = await cursor.to_list(100)
            permisos = [p['codigo'] for p in permisos_docs]
    
    # Obtener sucursales de esta empresa
    cursor = db.sucursales_catalogo.find(
        {'empresa_id': empresa_id, 'activa': True},
        {'_id': 0, 'id': 1, 'nombre': 1, 'codigo': 1}
    )
    sucursales = await cursor.to_list(100)
    
    return {
        'empresa': {
            'id': empresa['id'],
            'nombre': empresa['nombre'],
            'codigo': empresa['codigo']
        },
        'rol': rol_actual or user.get('role', 'Usuario'),
        'permisos': permisos,
        'sucursales': sucursales
    }


async def get_empresas_disponibles(user_id: str) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de empresas disponibles para un usuario.
    """
    db = get_db()
    
    user = await db.users.find_one({'id': user_id}, {'_id': 0, 'empresas_permitidas': 1})
    if not user:
        return []
    
    empresas_ids = user.get('empresas_permitidas', [])
    
    cursor = db.empresas.find(
        {'id': {'$in': empresas_ids}, 'activa': True},
        {'_id': 0, 'id': 1, 'nombre': 1, 'codigo': 1}
    )
    empresas = await cursor.to_list(100)
    
    return empresas


__all__ = [
    'get_user_context',
    'get_user_context_for_empresa',
    'get_empresas_disponibles'
]
