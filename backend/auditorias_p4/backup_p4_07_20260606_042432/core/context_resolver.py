from core.sql_first.connection_factory import get_edarsahub_pymssql_connection, get_external_sql_connection, get_edarsahub_connection
from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
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

MIGRACIÓN FASE 3-C:
====================
Este módulo ha sido migrado de MongoDB a EDARSAHUB SQL.
Tablas SQL utilizadas:
- Sistema_Empresas
- Sistema_Sucursales
- Sistema_SucursalServidorMapeo
- Servidores_Conexiones
- Sistema_EmpresasMongoMap

MongoDB ya no es fuente de datos para resolución de contexto.
Fecha migración: 2026-05-14
Autor: Agente E1
Régimen: Autorización Controlada

Fecha original: 2026-04-20
Autor original: Arquitecto de Software Senior
"""

from typing import Dict, List, Optional, Any
from fastapi import HTTPException
import logging
import pymssql

# Import lazy para evitar circular imports
_security_module = None

# =========================================================================
# CONEXIÓN SQL
# =========================================================================

def _get_sql_connection():
    """Obtiene conexión a EDARSAHUB SQL"""
    return get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)


def _get_security():
    global _security_module
    if _security_module is None:
        from core import security as sec
        _security_module = sec
    return _security_module


# =========================================================================
# HELPERS SQL DE LECTURA
# =========================================================================

def _get_empresas_by_uuids_sql(cursor, empresa_uuids: List[str]) -> List[Dict]:
    """
    Obtiene empresas desde Sistema_Empresas + Sistema_EmpresasMongoMap
    por UUIDs de MongoDB (empresas_permitidas del usuario).
    
    Args:
        cursor: Cursor SQL activo
        empresa_uuids: Lista de UUIDs MongoDB de empresas
        
    Returns:
        Lista de dicts con id (uuid), codigo, nombre, empresa_id_sql
    """
    if not empresa_uuids:
        return []
    
    # Construir IN clause
    placeholders = ', '.join(['%s'] * len(empresa_uuids))
    
    cursor.execute(f'''
        SELECT 
            e.EmpresaID,
            e.CodigoEmpresa,
            e.NombreEmpresa,
            m.EmpresaMongoUUID,
            e.Activo
        FROM Sistema_Empresas e
        JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
        WHERE m.EmpresaMongoUUID IN ({placeholders})
          AND e.Activo = 1
        ORDER BY e.EmpresaID
    ''', tuple(empresa_uuids))
    
    empresas = []
    for row in cursor.fetchall():
        empresas.append({
            'id': row[3],  # EmpresaMongoUUID (compatibilidad)
            'empresa_id_sql': row[0],
            'codigo': row[1],
            'nombre': row[2],
            'activa': bool(row[4])
        })
    
    return empresas


def _get_sucursales_by_empresas_sql(cursor, empresa_ids_sql: List[int]) -> List[Dict]:
    """
    Obtiene sucursales desde Sistema_Sucursales por IDs SQL de empresas.
    
    Args:
        cursor: Cursor SQL activo
        empresa_ids_sql: Lista de EmpresaID SQL
        
    Returns:
        Lista de dicts con id (uuid), codigo, nombre, empresa_id, sucursal_id_sql
    """
    if not empresa_ids_sql:
        return []
    
    placeholders = ', '.join(['%s'] * len(empresa_ids_sql))
    
    cursor.execute(f'''
        SELECT 
            s.SucursalID,
            s.CodigoSucursal,
            s.NombreSucursal,
            s.EmpresaID,
            s.MongoUUID,
            s.Activo,
            m.EmpresaMongoUUID
        FROM Sistema_Sucursales s
        JOIN Sistema_EmpresasMongoMap m ON s.EmpresaID = m.EmpresaID_SQL
        WHERE s.EmpresaID IN ({placeholders})
          AND s.Activo = 1
        ORDER BY s.SucursalID
    ''', tuple(empresa_ids_sql))
    
    sucursales = []
    for row in cursor.fetchall():
        sucursales.append({
            'id': row[4],  # MongoUUID sucursal (compatibilidad)
            'sucursal_id_sql': row[0],
            'codigo': row[1],
            'nombre': row[2],
            'empresa_id': row[6],  # EmpresaMongoUUID (compatibilidad)
            'empresa_id_sql': row[3],
            'activa': bool(row[5])
        })
    
    return sucursales


def _get_mapeos_by_sucursales_sql(cursor, sucursal_ids_sql: List[int]) -> Dict[int, Dict]:
    """
    Obtiene mapeos sucursal-servidor desde Sistema_SucursalServidorMapeo.
    
    Args:
        cursor: Cursor SQL activo
        sucursal_ids_sql: Lista de SucursalID SQL
        
    Returns:
        Dict {sucursal_id_sql: {server_id, sucursal_origen_id, ...}}
    """
    if not sucursal_ids_sql:
        return {}
    
    placeholders = ', '.join(['%s'] * len(sucursal_ids_sql))
    
    cursor.execute(f'''
        SELECT 
            m.MapeoID,
            m.SucursalID,
            LOWER(CAST(m.ServidorID AS VARCHAR(36))) as ServidorID,
            m.SucursalOrigenID,
            m.MongoSucursalUUID,
            m.Activo
        FROM Sistema_SucursalServidorMapeo m
        WHERE m.SucursalID IN ({placeholders})
          AND m.Activo = 1
        ORDER BY m.SucursalID
    ''', tuple(sucursal_ids_sql))
    
    mapeos = {}
    for row in cursor.fetchall():
        sucursal_id_sql = row[1]
        mapeos[sucursal_id_sql] = {
            'mapeo_id': row[0],
            'sucursal_id': row[4],  # MongoSucursalUUID (compatibilidad)
            'sucursal_id_sql': sucursal_id_sql,
            'server_id': row[2],  # UUID como string lowercase
            'sucursal_origen_id': row[3],
            'activo': bool(row[5])
        }
    
    return mapeos


def _get_servers_by_ids_sql(cursor, server_ids: List[str]) -> Dict[str, Dict]:
    """
    Obtiene información de servidores desde Servidores_Conexiones.
    
    Args:
        cursor: Cursor SQL activo
        server_ids: Lista de UUIDs de servidor (strings lowercase)
        
    Returns:
        Dict {server_id: {id, name, system_type, visible_en_operaciones}}
    """
    if not server_ids:
        return {}
    
    placeholders = ', '.join(['%s'] * len(server_ids))
    
    cursor.execute(f'''
        SELECT 
            LOWER(CAST(id AS VARCHAR(36))) as id,
            nombre,
            system_type,
            visible_en_operaciones
        FROM Servidores_Conexiones
        WHERE LOWER(CAST(id AS VARCHAR(36))) IN ({placeholders})
        ORDER BY nombre
    ''', tuple(server_ids))
    
    servers = {}
    for row in cursor.fetchall():
        server_id = row[0]
        servers[server_id] = {
            'id': server_id,
            'name': row[1],
            'system_type': row[2],
            'visible_en_operaciones': bool(row[3])
        }
    
    return servers


def _get_server_by_id_sql(cursor, server_id: str) -> Optional[Dict]:
    """
    Obtiene un servidor por ID desde Servidores_Conexiones.
    
    Args:
        cursor: Cursor SQL activo
        server_id: UUID del servidor (string)
        
    Returns:
        Dict con info del servidor o None
    """
    cursor.execute('''
        SELECT 
            LOWER(CAST(id AS VARCHAR(36))) as id,
            nombre,
            system_type,
            visible_en_operaciones
        FROM Servidores_Conexiones
        WHERE LOWER(CAST(id AS VARCHAR(36))) = LOWER(%s)
    ''', (server_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        'id': row[0],
        'name': row[1],
        'system_type': row[2],
        'visible_en_operaciones': bool(row[3])
    }


def _get_sucursal_by_mapeo_server_sql(cursor, server_id: str) -> Optional[Dict]:
    """
    Obtiene la sucursal asociada a un servidor desde Sistema_SucursalServidorMapeo.
    
    Args:
        cursor: Cursor SQL activo
        server_id: UUID del servidor
        
    Returns:
        Dict con info de sucursal y mapeo o None
    """
    cursor.execute('''
        SELECT 
            s.SucursalID,
            s.CodigoSucursal,
            s.NombreSucursal,
            s.EmpresaID,
            s.MongoUUID,
            m.SucursalOrigenID,
            em.EmpresaMongoUUID
        FROM Sistema_SucursalServidorMapeo m
        JOIN Sistema_Sucursales s ON m.SucursalID = s.SucursalID
        JOIN Sistema_EmpresasMongoMap em ON s.EmpresaID = em.EmpresaID_SQL
        WHERE LOWER(CAST(m.ServidorID AS VARCHAR(36))) = LOWER(%s)
          AND m.Activo = 1
          AND s.Activo = 1
    ''', (server_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        'sucursal_id_sql': row[0],
        'codigo': row[1],
        'nombre': row[2],
        'empresa_id_sql': row[3],
        'sucursal_id': row[4],  # MongoUUID
        'sucursal_origen_id': row[5],
        'empresa_id': row[6]  # EmpresaMongoUUID
    }


def _get_empresa_by_id_sql(cursor, empresa_uuid: str) -> Optional[Dict]:
    """
    Obtiene una empresa por UUID MongoDB desde Sistema_Empresas.
    
    Args:
        cursor: Cursor SQL activo
        empresa_uuid: UUID MongoDB de la empresa
        
    Returns:
        Dict con info de empresa o None
    """
    cursor.execute('''
        SELECT 
            e.EmpresaID,
            e.CodigoEmpresa,
            e.NombreEmpresa,
            m.EmpresaMongoUUID,
            e.Activo
        FROM Sistema_Empresas e
        JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
        WHERE LOWER(m.EmpresaMongoUUID) = LOWER(%s)
          AND e.Activo = 1
    ''', (empresa_uuid,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        'empresa_id_sql': row[0],
        'codigo': row[1],
        'nombre': row[2],
        'id': row[3],
        'activa': bool(row[4])
    }


# =========================================================================
# FUNCIONES PÚBLICAS
# =========================================================================

async def get_user_unidades_negocio(user: Dict[str, Any]) -> List[Dict]:
    """
    Obtiene las unidades de negocio disponibles para un usuario según RBAC.
    
    MIGRACIÓN FASE 3-C: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
    
    Args:
        user: Diccionario del usuario autenticado
        
    Returns:
        Lista de unidades de negocio con:
        - id: ID de la empresa (UUID MongoDB)
        - codigo: Código corto
        - nombre: Nombre visible
        - server_id: ID del servidor asociado
        - system_type: Tipo de sistema (MPRO/SoftRestaurant)
        - sucursal_origen_id: ID de sucursal en sistema externo (MPRO)
        - sucursales: Lista de sucursales
    """
    security = _get_security()
    
    # 1. Obtener empresas permitidas (UUIDs MongoDB)
    empresas_permitidas = await security.get_user_empresas_permitidas(user)
    
    if not empresas_permitidas:
        return []
    
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        
        # 2. Obtener empresas del catálogo SQL
        empresas = _get_empresas_by_uuids_sql(cursor, empresas_permitidas)
        
        if not empresas:
            return []
        
        # 3. Obtener IDs SQL para consultas subsecuentes
        empresa_ids_sql = [e['empresa_id_sql'] for e in empresas]
        
        # 4. Obtener sucursales asociadas
        sucursales = _get_sucursales_by_empresas_sql(cursor, empresa_ids_sql)
        
        # 5. Obtener mapeos sucursal → servidor
        sucursal_ids_sql = [s['sucursal_id_sql'] for s in sucursales]
        mapeos_dict = _get_mapeos_by_sucursales_sql(cursor, sucursal_ids_sql)
        
        # 6. Obtener info de servidores
        server_ids = list(set(m['server_id'] for m in mapeos_dict.values() if m.get('server_id')))
        servers_dict = _get_servers_by_ids_sql(cursor, server_ids)
        
        # 7. Construir resultado (mantener contrato de salida original)
        resultado = []
        for empresa in empresas:
            empresa_id = empresa['id']  # UUID MongoDB
            empresa_id_sql = empresa['empresa_id_sql']
            
            # Buscar sucursal de esta empresa
            sucursal_empresa = next(
                (s for s in sucursales if s['empresa_id_sql'] == empresa_id_sql), 
                None
            )
            
            if sucursal_empresa:
                sucursal_id_sql = sucursal_empresa['sucursal_id_sql']
                mapeo = mapeos_dict.get(sucursal_id_sql, {})
                server_id = mapeo.get('server_id')
                server_info = servers_dict.get(server_id, {})
                sucursal_origen_id = mapeo.get('sucursal_origen_id')
                
                resultado.append({
                    'id': empresa_id,  # UUID MongoDB (compatibilidad)
                    'codigo': empresa.get('codigo', ''),
                    'nombre': empresa.get('nombre', ''),
                    'server_id': server_id,
                    'server_nombre': server_info.get('name', ''),
                    'system_type': server_info.get('system_type', ''),
                    'sucursal_origen_id': sucursal_origen_id,
                    'sucursales': [{
                        'id': sucursal_origen_id or sucursal_empresa.get('codigo'),
                        'nombre': sucursal_empresa.get('nombre')
                    }]
                })
        
        resultado.sort(key=lambda x: x['nombre'])
        return resultado
        
    finally:
        conn.close()


async def resolve_unidad_context(user: Dict[str, Any], unidad_id: str) -> Dict:
    """
    Resuelve el contexto completo de una unidad de negocio.
    Valida que el usuario tenga acceso según RBAC.
    
    MIGRACIÓN FASE 3-C: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
    
    Args:
        user: Usuario autenticado
        unidad_id: ID de la unidad de negocio (empresa_id UUID MongoDB)
        
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
    unidad = next((u for u in unidades if u['id'] == unidad_id), None)
    
    if not unidad:
        raise HTTPException(status_code=404, detail="Unidad de negocio no encontrada")
    
    return {
        'unidad_id': unidad['id'],
        'unidad_nombre': unidad['nombre'],
        'server_id': unidad['server_id'],
        'server_nombre': unidad.get('server_nombre', ''),
        'system_type': unidad['system_type'],
        'sucursal_origen_id': unidad.get('sucursal_origen_id'),
        'sucursales': unidad.get('sucursales', [])
    }


async def resolve_server_context(user: Dict[str, Any], server_id: str) -> Dict:
    """
    Resuelve el contexto de un servidor validando acceso RBAC.
    COMPATIBILIDAD: Para endpoints que aún reciben server_id.
    
    MIGRACIÓN FASE 3-C: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
    
    El server_id se traduce internamente a unidad de negocio y se valida acceso.
    
    Args:
        user: Usuario autenticado
        server_id: ID del servidor (UUID)
        
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
    security = _get_security()
    
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Verificar que el servidor existe
        server = _get_server_by_id_sql(cursor, server_id)
        if not server:
            raise HTTPException(status_code=404, detail="Servidor no encontrado")
        
        # 2. Obtener empresas permitidas del usuario
        empresas_permitidas = await security.get_user_empresas_permitidas(user)
        
        if not empresas_permitidas:
            raise HTTPException(status_code=403, detail="Usuario sin empresas asignadas")
        
        # 3. Buscar qué unidad de negocio corresponde a este servidor
        sucursal_info = _get_sucursal_by_mapeo_server_sql(cursor, server_id)
        
        unidad_id = None
        unidad_nombre = ""
        sucursal_origen_id = None
        sucursales = []
        
        if sucursal_info:
            empresa_id = sucursal_info.get('empresa_id')  # UUID MongoDB
            sucursal_origen_id = sucursal_info.get('sucursal_origen_id')
            
            # Validar que el usuario tenga acceso a esta empresa
            if empresa_id not in empresas_permitidas:
                logging.warning(f"[Context Resolver] Usuario {user.get('email')} sin acceso a servidor {server_id}")
                raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")
            
            unidad_id = empresa_id
            
            # Obtener nombre de la empresa
            empresa = _get_empresa_by_id_sql(cursor, empresa_id)
            if empresa:
                unidad_nombre = empresa.get('nombre', '')
            
            sucursales = [{
                'id': sucursal_origen_id or sucursal_info.get('codigo'),
                'nombre': sucursal_info.get('nombre')
            }]
        else:
            # Sin mapeo: intentar validar por servers_for_empresas
            servers_permitidos = await security.get_servers_for_empresas(empresas_permitidas)
            if server_id not in servers_permitidos:
                raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")
        
        return {
            'server_id': server_id,
            'server_nombre': server.get('name', ''),
            'system_type': server.get('system_type', ''),
            'unidad_id': unidad_id,
            'unidad_nombre': unidad_nombre,
            'sucursal_origen_id': sucursal_origen_id,
            'sucursales': sucursales
        }
        
    finally:
        conn.close()


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
    system_type = context.get('system_type', '')
    
    if system_type == 'MPRO':
        # MPRO usa sucursal_origen_id (código numérico)
        return context.get('sucursal_origen_id') or 'default'
    else:
        # SoftRestaurant usa default o nombre
        sucursales = context.get('sucursales', [])
        if sucursales:
            return sucursales[0].get('id') or sucursales[0].get('nombre') or 'default'
        return 'default'


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
