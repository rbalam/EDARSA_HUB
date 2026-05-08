"""
Context Resolver - Resolución Centralizada de Contexto por Usuario
==================================================================

PROPÓSITO:
Este módulo centraliza la resolución del contexto de acceso según RBAC.
El frontend envía la unidad de negocio seleccionada, y el backend resuelve:
- server_id
- system_type (MPRO/SoftRestaurant)
- sucursal_origen_id (para MPRO)
- sucursales permitidas

REGLAS:
1. El usuario NO define el contexto de seguridad
2. El sistema lo resuelve según: usuario → roles → empresas_permitidas → contexto
3. Todo endpoint funcional debe usar estas funciones para validar acceso

MÓDULOS QUE DEBEN USAR ESTE RESOLVER:
- Compras
- Comercial
- Operaciones (Dashboard, Inventarios)
- Finanzas
- Reportes

Fecha: 2026-04-20
Autor: Arquitecto de Software Senior
"""

from typing import Dict, List, Optional, Any
from fastapi import HTTPException
import logging

# Import lazy para evitar circular imports
_db = None
_security_module = None

def _get_db():
    global _db
    if _db is None:
        import os
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'edarsa_hub')
        client = AsyncIOMotorClient(mongo_url)
        _db = client[db_name]
    return _db

def _get_security():
    global _security_module
    if _security_module is None:
        from core import security as sec
        _security_module = sec
    return _security_module


async def get_user_unidades_negocio(user: Dict[str, Any]) -> List[Dict]:
    """
    Obtiene las unidades de negocio disponibles para un usuario según RBAC.
    
    Args:
        user: Diccionario del usuario autenticado
        
    Returns:
        Lista de unidades de negocio con:
        - id: ID de la empresa
        - codigo: Código corto
        - nombre: Nombre visible
        - server_id: ID del servidor asociado
        - system_type: Tipo de sistema (MPRO/SoftRestaurant)
        - sucursal_origen_id: ID de sucursal en sistema externo (MPRO)
        - sucursales: Lista de sucursales
    """
    db = _get_db()
    security = _get_security()
    
    # 1. Obtener empresas permitidas
    empresas_permitidas = await security.get_user_empresas_permitidas(user)
    
    if not empresas_permitidas:
        return []
    
    # 2. Obtener empresas del catálogo
    empresas_cursor = db.empresas.find(
        {"id": {"$in": empresas_permitidas}, "activa": True},
        {"_id": 0}
    )
    empresas = await empresas_cursor.to_list(100)
    
    # 3. Obtener sucursales asociadas
    sucursales_cursor = db.sucursales_catalogo.find(
        {"empresa_id": {"$in": empresas_permitidas}, "activa": True},
        {"_id": 0}
    )
    sucursales = await sucursales_cursor.to_list(100)
    
    # 4. Obtener mapeos sucursal → servidor
    sucursal_ids = [s["id"] for s in sucursales]
    mapeos_cursor = db.sucursal_servidor_map.find(
        {"sucursal_id": {"$in": sucursal_ids}, "activo": True},
        {"_id": 0}
    )
    mapeos = await mapeos_cursor.to_list(100)
    mapeos_dict = {m["sucursal_id"]: m for m in mapeos}
    
    # 5. Obtener info de servidores
    server_ids = list(set(m["server_id"] for m in mapeos if m.get("server_id")))
    servers_cursor = db.servers.find(
        {"id": {"$in": server_ids}},
        {"_id": 0, "id": 1, "name": 1, "system_type": 1}
    )
    servers_dict = {s["id"]: s async for s in servers_cursor}
    
    # 6. Construir resultado
    resultado = []
    for empresa in empresas:
        empresa_id = empresa["id"]
        sucursal_empresa = next((s for s in sucursales if s["empresa_id"] == empresa_id), None)
        
        if sucursal_empresa:
            mapeo = mapeos_dict.get(sucursal_empresa["id"], {})
            server_id = mapeo.get("server_id")
            server_info = servers_dict.get(server_id, {})
            sucursal_origen_id = mapeo.get("sucursal_origen_id")
            
            resultado.append({
                "id": empresa_id,
                "codigo": empresa.get("codigo", ""),
                "nombre": empresa.get("nombre", ""),
                "server_id": server_id,
                "server_nombre": server_info.get("name", ""),
                "system_type": server_info.get("system_type", ""),
                "sucursal_origen_id": sucursal_origen_id,
                "sucursales": [{
                    "id": sucursal_origen_id or sucursal_empresa.get("codigo"),
                    "nombre": sucursal_empresa.get("nombre")
                }]
            })
    
    resultado.sort(key=lambda x: x["nombre"])
    return resultado


async def resolve_unidad_context(user: Dict[str, Any], unidad_id: str) -> Dict:
    """
    Resuelve el contexto completo de una unidad de negocio.
    Valida que el usuario tenga acceso según RBAC.
    
    Args:
        user: Usuario autenticado
        unidad_id: ID de la unidad de negocio (empresa_id)
        
    Returns:
        {
            "unidad_id": str,
            "unidad_nombre": str,
            "server_id": str,
            "server_nombre": str,
            "system_type": str,
            "sucursal_origen_id": str | None,
            "sucursales": List[Dict]
        }
        
    Raises:
        HTTPException 403 si usuario no tiene acceso
        HTTPException 404 si unidad no encontrada
    """
    security = _get_security()
    
    # Validar acceso RBAC
    empresas_permitidas = await security.get_user_empresas_permitidas(user)
    
    if not empresas_permitidas or unidad_id not in empresas_permitidas:
        logging.warning(f"[Context Resolver] Usuario {user.get('email')} sin acceso a unidad {unidad_id}")
        raise HTTPException(status_code=403, detail="No tiene acceso a esta unidad de negocio")
    
    # Obtener unidades del usuario
    unidades = await get_user_unidades_negocio(user)
    
    # Buscar la unidad solicitada
    unidad = next((u for u in unidades if u["id"] == unidad_id), None)
    
    if not unidad:
        raise HTTPException(status_code=404, detail="Unidad de negocio no encontrada")
    
    return {
        "unidad_id": unidad["id"],
        "unidad_nombre": unidad["nombre"],
        "server_id": unidad["server_id"],
        "server_nombre": unidad.get("server_nombre", ""),
        "system_type": unidad["system_type"],
        "sucursal_origen_id": unidad.get("sucursal_origen_id"),
        "sucursales": unidad.get("sucursales", [])
    }


async def resolve_server_context(user: Dict[str, Any], server_id: str) -> Dict:
    """
    Resuelve el contexto de un servidor validando acceso RBAC.
    COMPATIBILIDAD: Para endpoints que aún reciben server_id.
    
    El server_id se traduce internamente a unidad de negocio y se valida acceso.
    
    Args:
        user: Usuario autenticado
        server_id: ID del servidor
        
    Returns:
        {
            "server_id": str,
            "server_nombre": str,
            "system_type": str,
            "unidad_id": str | None,
            "unidad_nombre": str,
            "sucursal_origen_id": str | None,
            "sucursales": List[Dict]
        }
        
    Raises:
        HTTPException 403 si usuario no tiene acceso
        HTTPException 404 si servidor no encontrado
    """
    db = _get_db()
    security = _get_security()
    
    # 1. Verificar que el servidor existe
    server = await db.servers.find_one({"id": server_id}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # 2. Obtener empresas permitidas del usuario
    empresas_permitidas = await security.get_user_empresas_permitidas(user)
    
    if not empresas_permitidas:
        raise HTTPException(status_code=403, detail="Usuario sin empresas asignadas")
    
    # 3. Buscar qué unidad de negocio corresponde a este servidor
    # Primero buscar en mapeos
    mapeo = await db.sucursal_servidor_map.find_one(
        {"server_id": server_id, "activo": True},
        {"_id": 0}
    )
    
    unidad_id = None
    unidad_nombre = ""
    sucursal_origen_id = None
    sucursales = []
    
    if mapeo:
        sucursal_id = mapeo.get("sucursal_id")
        sucursal_origen_id = mapeo.get("sucursal_origen_id")
        
        # Buscar la sucursal para obtener empresa_id
        sucursal = await db.sucursales_catalogo.find_one(
            {"id": sucursal_id},
            {"_id": 0}
        )
        
        if sucursal:
            empresa_id = sucursal.get("empresa_id")
            
            # Validar que el usuario tenga acceso a esta empresa
            if empresa_id not in empresas_permitidas:
                logging.warning(f"[Context Resolver] Usuario {user.get('email')} sin acceso a servidor {server_id}")
                raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")
            
            unidad_id = empresa_id
            
            # Obtener nombre de la empresa
            empresa = await db.empresas.find_one({"id": empresa_id}, {"_id": 0})
            if empresa:
                unidad_nombre = empresa.get("nombre", "")
            
            sucursales = [{
                "id": sucursal_origen_id or sucursal.get("codigo"),
                "nombre": sucursal.get("nombre")
            }]
    else:
        # Sin mapeo: intentar validar por servers_for_empresas
        servers_permitidos = await security.get_servers_for_empresas(empresas_permitidas)
        if server_id not in servers_permitidos:
            raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")
    
    return {
        "server_id": server_id,
        "server_nombre": server.get("name", ""),
        "system_type": server.get("system_type", ""),
        "unidad_id": unidad_id,
        "unidad_nombre": unidad_nombre,
        "sucursal_origen_id": sucursal_origen_id,
        "sucursales": sucursales
    }


async def get_sucursal_for_query(context: Dict) -> str:
    """
    Obtiene el valor de sucursal a usar en queries SQL según el contexto.
    
    Para MPRO: usa sucursal_origen_id (código como "0025")
    Para SoftRestaurant: usa "default" o nombre de sucursal
    
    Args:
        context: Contexto resuelto por resolve_unidad_context o resolve_server_context
        
    Returns:
        String con el identificador de sucursal para queries
    """
    system_type = context.get("system_type", "")
    
    if system_type == "MPRO":
        # MPRO usa sucursal_origen_id (código numérico)
        return context.get("sucursal_origen_id") or "default"
    else:
        # SoftRestaurant usa default o nombre
        sucursales = context.get("sucursales", [])
        if sucursales:
            return sucursales[0].get("id") or sucursales[0].get("nombre") or "default"
        return "default"


async def validate_user_access_to_server(user: Dict[str, Any], server_id: str) -> bool:
    """
    Valida si un usuario tiene acceso a un servidor según RBAC.
    No lanza excepción, solo retorna True/False.
    
    Args:
        user: Usuario autenticado
        server_id: ID del servidor
        
    Returns:
        True si tiene acceso, False si no
    """
    try:
        await resolve_server_context(user, server_id)
        return True
    except HTTPException:
        return False


# Exportar funciones principales
__all__ = [
    'get_user_unidades_negocio',
    'resolve_unidad_context',
    'resolve_server_context',
    'get_sucursal_for_query',
    'validate_user_access_to_server',
]
