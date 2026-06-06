from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - User Context Service
=================================
Servicio para resolver y gestionar el contexto de usuario.

FASE 2 (Abril 2026):
- Resuelve contexto inicial de sesión
- Obtiene empresas/sucursales permitidas
- Obtiene rol y permisos en contexto
- Mantiene compatibilidad con modelo legacy

MIGRACIÓN FASE 3-E:
====================
Este módulo ha sido migrado de MongoDB a EDARSAHUB SQL.
Tablas SQL utilizadas:
- Usuario_Catalogo
- Usuario_Roles
- Usuario_RolesAsignacion
- Usuario_EmpresasAsignacion
- Sistema_Empresas
- Sistema_EmpresasMongoMap
- Sistema_Sucursales

MongoDB ya no es fuente de datos para contexto de usuario.
Fecha migración: 2026-05-14
Autor: Agente E1
Régimen: Autorización Controlada

PRINCIPIO: EDARSA HUB es el cerebro del sistema.
El contexto se resuelve aquí, no en sistemas externos.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging
import pymssql

logger = logging.getLogger(__name__)


# =========================================================================
# CONEXIÓN SQL
# =========================================================================

def _get_sql_connection():
    """Obtiene conexión a EDARSAHUB SQL."""
    return pymssql.connect(
        server=os.getenv('EDARSAHUB_SQL_HOST'),
        port=1433,
        user=os.getenv('EDARSAHUB_SQL_USER'),
        password=os.getenv('EDARSAHUB_SQL_PASSWORD'),
        database='EDARSAHUB'
    )


# =========================================================================
# HELPERS SQL
# =========================================================================

def _get_user_by_public_uuid(cursor, user_id: str) -> Optional[Dict]:
    """
    Obtiene usuario por PublicUUID desde Usuario_Catalogo.
    """
    cursor.execute('''
        SELECT 
            UsuarioID,
            Email,
            Nombre,
            CAST(PublicUUID AS VARCHAR(36)) as PublicUUID,
            Activo
        FROM Usuario_Catalogo
        WHERE LOWER(CAST(PublicUUID AS VARCHAR(36))) = LOWER(%s)
          AND Activo = 1
    ''', (user_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        'usuario_id_sql': row[0],
        'email': row[1],
        'nombre': row[2],
        'id': row[3],  # PublicUUID
        'activo': bool(row[4])
    }


def _get_user_role_sql(cursor, usuario_id: int) -> Optional[Dict]:
    """
    Obtiene rol del usuario desde Usuario_RolesAsignacion.
    """
    cursor.execute('''
        SELECT 
            r.RolID,
            r.CodigoRol,
            r.NombreRol,
            r.NivelJerarquia
        FROM Usuario_RolesAsignacion ra
        JOIN Usuario_Roles r ON ra.RolID = r.RolID
        WHERE ra.UsuarioID = %s AND ra.Activo = 1
        ORDER BY ra.EsPrincipal DESC
    ''', (usuario_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        'rol_id': row[0],
        'codigo': row[1],
        'nombre': row[2],
        'nivel_jerarquia': row[3]
    }


def _get_user_empresas_sql(cursor, usuario_id: int) -> tuple:
    """
    Obtiene empresas asignadas al usuario con detalles.
    
    Returns:
        tuple: (lista_empresas, empresa_default)
    """
    cursor.execute('''
        SELECT 
            e.EmpresaID,
            e.CodigoEmpresa,
            e.NombreEmpresa,
            m.EmpresaMongoUUID,
            ea.EsPrincipal
        FROM Usuario_EmpresasAsignacion ea
        JOIN Sistema_Empresas e ON ea.EmpresaID = e.EmpresaID
        JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
        WHERE ea.UsuarioID = %s 
          AND ea.Activo = 1
          AND e.Activo = 1
        ORDER BY ea.EsPrincipal DESC, e.EmpresaID
    ''', (usuario_id,))
    
    empresas = []
    empresa_default = None
    
    for row in cursor.fetchall():
        emp = {
            'id': row[3],  # EmpresaMongoUUID (compatibilidad)
            'empresa_id_sql': row[0],
            'codigo': row[1],
            'nombre': row[2],
            'es_principal': bool(row[4])
        }
        empresas.append(emp)
        
        if row[4] and not empresa_default:  # EsPrincipal
            empresa_default = emp
    
    # Si no hay default explícito, usar la primera
    if not empresa_default and empresas:
        empresa_default = empresas[0]
    
    return empresas, empresa_default


def _get_all_empresas_sql(cursor) -> List[Dict]:
    """
    Obtiene todas las empresas activas (para SUPERADMIN/ADMIN).
    """
    cursor.execute('''
        SELECT 
            e.EmpresaID,
            e.CodigoEmpresa,
            e.NombreEmpresa,
            m.EmpresaMongoUUID
        FROM Sistema_Empresas e
        JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
        WHERE e.Activo = 1
        ORDER BY e.EmpresaID
    ''')
    
    empresas = []
    for row in cursor.fetchall():
        empresas.append({
            'id': row[3],  # EmpresaMongoUUID
            'empresa_id_sql': row[0],
            'codigo': row[1],
            'nombre': row[2]
        })
    
    return empresas


def _get_sucursales_by_empresa_sql(cursor, empresa_id_sql: int) -> List[Dict]:
    """
    Obtiene sucursales de una empresa.
    """
    cursor.execute('''
        SELECT 
            s.SucursalID,
            s.CodigoSucursal,
            s.NombreSucursal,
            s.MongoUUID
        FROM Sistema_Sucursales s
        WHERE s.EmpresaID = %s
          AND s.Activo = 1
        ORDER BY s.SucursalID
    ''', (empresa_id_sql,))
    
    sucursales = []
    for row in cursor.fetchall():
        sucursales.append({
            'id': row[3] or row[1],  # MongoUUID o Codigo como fallback
            'codigo': row[1],
            'nombre': row[2]
        })
    
    return sucursales


def _get_empresa_by_uuid_sql(cursor, empresa_uuid: str) -> Optional[Dict]:
    """
    Obtiene una empresa por UUID MongoDB.
    """
    cursor.execute('''
        SELECT 
            e.EmpresaID,
            e.CodigoEmpresa,
            e.NombreEmpresa,
            m.EmpresaMongoUUID
        FROM Sistema_Empresas e
        JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
        WHERE LOWER(m.EmpresaMongoUUID) = LOWER(%s)
          AND e.Activo = 1
    ''', (empresa_uuid,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        'id': row[3],
        'empresa_id_sql': row[0],
        'codigo': row[1],
        'nombre': row[2]
    }


def _get_user_allowed_servers_sql(cursor, usuario_id: int) -> List[str]:
    """
    Obtiene servidores permitidos del usuario (legacy compatibility).
    """
    cursor.execute('''
        SELECT LOWER(CAST(ServidorID AS VARCHAR(36))) as ServidorID
        FROM Usuario_ServidoresAsignacion
        WHERE UsuarioID = %s AND Activo = 1
    ''', (usuario_id,))
    
    return [row[0] for row in cursor.fetchall()]


def _get_user_allowed_sucursales_sql(cursor, usuario_id: int) -> Dict[str, List[str]]:
    """
    Obtiene sucursales permitidas del usuario agrupadas por servidor (legacy compatibility).
    """
    cursor.execute('''
        SELECT 
            LOWER(CAST(ServidorID AS VARCHAR(36))) as ServidorID,
            SucursalCodigo
        FROM Usuario_SucursalesAsignacion
        WHERE UsuarioID = %s AND Activo = 1
    ''', (usuario_id,))
    
    result = {}
    for row in cursor.fetchall():
        server_id = row[0]
        suc_codigo = row[1]
        if server_id not in result:
            result[server_id] = []
        result[server_id].append(suc_codigo)
    
    return result


# =========================================================================
# FUNCIONES PÚBLICAS
# =========================================================================

async def get_user_context(user_id: str) -> Dict[str, Any]:
    """
    Resuelve el contexto completo de un usuario.
    
    MIGRACIÓN FASE 3-E: Ahora lee desde EDARSAHUB SQL.
    
    Returns:
        Dict con:
        - user_id
        - email
        - nombre
        - empresa_default (id, nombre)
        - empresas_permitidas (lista de {id, nombre, codigo})
        - rol_actual (nombre del rol RBAC)
        - permisos (lista de códigos de permisos)
        - sucursales_por_empresa (lista por empresa)
        - legacy (campos viejos para compatibilidad)
    """
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        
        # Obtener usuario
        user = _get_user_by_public_uuid(cursor, user_id)
        if not user:
            return None
        
        usuario_id_sql = user['usuario_id_sql']
        
        # Obtener rol
        rol_info = _get_user_role_sql(cursor, usuario_id_sql)
        rol_nombre = rol_info['nombre'] if rol_info else 'Usuario'
        rol_codigo = rol_info['codigo'] if rol_info else 'USUARIO'
        
        # Determinar si tiene acceso global
        tiene_acceso_global = rol_codigo in ('SUPERADMIN', 'ADMIN')
        
        # Obtener empresas
        if tiene_acceso_global:
            # SUPERADMIN/ADMIN: todas las empresas
            all_empresas = _get_all_empresas_sql(cursor)
            empresas_permitidas = [{
                'id': e['id'],
                'nombre': e['nombre'],
                'codigo': e['codigo']
            } for e in all_empresas]
            # Default: primera empresa
            empresa_default = empresas_permitidas[0] if empresas_permitidas else None
        else:
            # Usuario normal: empresas asignadas
            empresas_raw, emp_default = _get_user_empresas_sql(cursor, usuario_id_sql)
            empresas_permitidas = [{
                'id': e['id'],
                'nombre': e['nombre'],
                'codigo': e['codigo']
            } for e in empresas_raw]
            empresa_default = {
                'id': emp_default['id'],
                'nombre': emp_default['nombre'],
                'codigo': emp_default['codigo']
            } if emp_default else None
        
        # Obtener sucursales por empresa
        sucursales_por_empresa = {}
        for emp in empresas_permitidas:
            # Buscar empresa_id_sql
            emp_sql = _get_empresa_by_uuid_sql(cursor, emp['id'])
            if emp_sql:
                sucursales = _get_sucursales_by_empresa_sql(cursor, emp_sql['empresa_id_sql'])
                sucursales_por_empresa[emp['id']] = sucursales
        
        # Legacy: servidores y sucursales permitidos
        allowed_servers = _get_user_allowed_servers_sql(cursor, usuario_id_sql)
        allowed_sucursales = _get_user_allowed_sucursales_sql(cursor, usuario_id_sql)
        
        return {
            'user_id': user_id,
            'email': user['email'],
            'nombre': user['nombre'],
            'empresa_default': empresa_default,
            'empresas_permitidas': empresas_permitidas,
            'rol_actual': rol_nombre,
            'permisos': [],  # Permisos se resuelven desde el user dict en otras capas
            'sucursales_por_empresa': sucursales_por_empresa,
            # Legacy para compatibilidad
            'legacy': {
                'role': rol_nombre,
                'allowed_servers': allowed_servers,
                'allowed_sucursales': allowed_sucursales
            }
        }
        
    finally:
        conn.close()


async def get_user_context_for_empresa(user_id: str, empresa_id: str) -> Dict[str, Any]:
    """
    Resuelve el contexto de un usuario para una empresa específica.
    Útil cuando el usuario cambia de empresa activa.
    
    MIGRACIÓN FASE 3-E: Ahora lee desde EDARSAHUB SQL.
    """
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        
        # Obtener usuario
        user = _get_user_by_public_uuid(cursor, user_id)
        if not user:
            return None
        
        usuario_id_sql = user['usuario_id_sql']
        
        # Obtener rol
        rol_info = _get_user_role_sql(cursor, usuario_id_sql)
        rol_nombre = rol_info['nombre'] if rol_info else 'Usuario'
        rol_codigo = rol_info['codigo'] if rol_info else 'USUARIO'
        
        # Determinar si tiene acceso global
        tiene_acceso_global = rol_codigo in ('SUPERADMIN', 'ADMIN')
        
        # Verificar acceso a la empresa
        if not tiene_acceso_global:
            empresas_raw, _ = _get_user_empresas_sql(cursor, usuario_id_sql)
            empresas_uuids = [e['id'].lower() for e in empresas_raw]
            if empresa_id.lower() not in empresas_uuids:
                return {'error': 'Usuario no tiene acceso a esta empresa'}
        
        # Obtener empresa
        empresa = _get_empresa_by_uuid_sql(cursor, empresa_id)
        if not empresa:
            return {'error': 'Empresa no encontrada'}
        
        # Obtener sucursales de esta empresa
        sucursales = _get_sucursales_by_empresa_sql(cursor, empresa['empresa_id_sql'])
        
        return {
            'empresa': {
                'id': empresa['id'],
                'nombre': empresa['nombre'],
                'codigo': empresa['codigo']
            },
            'rol': rol_nombre,
            'permisos': [],  # Permisos se resuelven desde el user dict en otras capas
            'sucursales': sucursales
        }
        
    finally:
        conn.close()


async def get_empresas_disponibles(user_id: str) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de empresas disponibles para un usuario.
    
    MIGRACIÓN FASE 3-E: Ahora lee desde EDARSAHUB SQL.
    """
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        
        # Obtener usuario
        user = _get_user_by_public_uuid(cursor, user_id)
        if not user:
            return []
        
        usuario_id_sql = user['usuario_id_sql']
        
        # Obtener rol
        rol_info = _get_user_role_sql(cursor, usuario_id_sql)
        rol_codigo = rol_info['codigo'] if rol_info else 'USUARIO'
        
        # Determinar si tiene acceso global
        tiene_acceso_global = rol_codigo in ('SUPERADMIN', 'ADMIN')
        
        if tiene_acceso_global:
            # SUPERADMIN/ADMIN: todas las empresas
            empresas = _get_all_empresas_sql(cursor)
        else:
            # Usuario normal: empresas asignadas
            empresas, _ = _get_user_empresas_sql(cursor, usuario_id_sql)
        
        return [{
            'id': e['id'],
            'nombre': e['nombre'],
            'codigo': e['codigo']
        } for e in empresas]
        
    finally:
        conn.close()


__all__ = [
    'get_user_context',
    'get_user_context_for_empresa',
    'get_empresas_disponibles'
]
