"""
FASE 2-D: Auth Repository SQL Paralelo
======================================
Repositorio SQL para Auth/RBAC que consulta EDARSAHUB como fuente alternativa.

IMPORTANTE:
- Este repositorio es PARALELO y de COMPARACIÓN
- NO reemplaza el flujo actual de MongoDB
- NO modifica get_current_user, login ni JWT
- MongoDB sigue siendo la fuente productiva de autenticación

Regla SUPERADMIN:
- Si el usuario tiene rol SUPERADMIN, tiene acceso global implícito
- No depende de Usuario_EmpresasAsignacion
- Resuelve todas las empresas activas automáticamente

Autor: Agente E1
Fecha: 14-Dic-2025
Régimen: Autorización Controlada
"""

import os
import pymssql
from typing import Optional, Dict, List, Any
from datetime import datetime


class AuthRepositorySQL:
    """
    Repositorio SQL para autenticación y RBAC.
    Consulta EDARSAHUB como fuente de datos.
    """
    
    def __init__(self):
        self.sql_host = '54.39.104.176'
        self.sql_port = 1433
        self.sql_db = 'EDARSAHUB'
        self.sql_user = 'HRLectura'
        self.sql_pass = 'National09$'
    
    def _get_connection(self):
        """Obtiene conexión a EDARSAHUB"""
        return pymssql.connect(
            server=self.sql_host,
            port=self.sql_port,
            user=self.sql_user,
            password=self.sql_pass,
            database=self.sql_db
        )
    
    def _get_all_active_empresas(self, cursor) -> List[Dict]:
        """Obtiene todas las empresas activas (para SUPERADMIN)"""
        cursor.execute('''
            SELECT 
                e.EmpresaID,
                e.CodigoEmpresa,
                e.NombreEmpresa,
                m.EmpresaMongoUUID
            FROM Sistema_Empresas e
            LEFT JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
            WHERE e.Activo = 1
            ORDER BY e.EmpresaID
        ''')
        empresas = []
        for row in cursor.fetchall():
            empresas.append({
                'empresa_id_sql': row[0],
                'codigo': row[1],
                'nombre': row[2],
                'uuid_mongo': row[3]
            })
        return empresas
    
    def _get_user_empresas(self, cursor, usuario_id: int, rol_codigo: str) -> tuple:
        """
        Obtiene empresas permitidas para un usuario.
        Aplica regla SUPERADMIN: acceso global implícito.
        
        Returns:
            tuple: (empresas_permitidas_uuids, empresa_default_uuid)
        """
        # REGLA SUPERADMIN: Acceso global implícito
        if rol_codigo == 'SUPERADMIN':
            all_empresas = self._get_all_active_empresas(cursor)
            empresas_uuids = [e['uuid_mongo'] for e in all_empresas if e['uuid_mongo']]
            # Para SUPERADMIN, empresa_default es la primera (ORIGEN) o None
            empresa_default = empresas_uuids[0] if empresas_uuids else None
            return empresas_uuids, empresa_default
        
        # Usuarios normales: consultar Usuario_EmpresasAsignacion
        cursor.execute('''
            SELECT 
                m.EmpresaMongoUUID,
                ea.EsPrincipal
            FROM Usuario_EmpresasAsignacion ea
            JOIN Sistema_EmpresasMongoMap m ON ea.EmpresaID = m.EmpresaID_SQL
            WHERE ea.UsuarioID = %s AND ea.Activo = 1
            ORDER BY ea.EsPrincipal DESC, ea.EmpresaID
        ''', (usuario_id,))
        
        empresas_uuids = []
        empresa_default = None
        
        for row in cursor.fetchall():
            uuid = row[0]
            es_principal = row[1]
            if uuid:
                empresas_uuids.append(uuid)
                if es_principal and not empresa_default:
                    empresa_default = uuid
        
        return empresas_uuids, empresa_default
    
    def _get_user_rol(self, cursor, usuario_id: int) -> Dict:
        """Obtiene rol del usuario desde Usuario_RolesAsignacion"""
        cursor.execute('''
            SELECT r.RolID, r.CodigoRol, r.NombreRol, r.NivelJerarquia
            FROM Usuario_RolesAsignacion ra
            JOIN Usuario_Roles r ON ra.RolID = r.RolID
            WHERE ra.UsuarioID = %s AND ra.Activo = 1
        ''', (usuario_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'rol_id': row[0],
                'codigo': row[1],
                'nombre': row[2],
                'nivel_jerarquia': row[3]
            }
        return None
    
    def _build_user_dict(self, sql_row: tuple, rol: Dict, empresas: List[str], 
                         empresa_default: str) -> Dict:
        """
        Construye diccionario de usuario compatible con estructura MongoDB.
        
        IMPORTANTE:
        - 'id' = PublicUUID (string) para compatibilidad con JWT actual
        - No exponer UsuarioID SQL como id principal
        """
        usuario_id, email, nombre, password_hash, activo, public_uuid, mongo_legacy_id = sql_row
        
        # Mapeo de rol SQL a rol MongoDB
        ROL_SQL_TO_MONGO = {
            'SUPERADMIN': 'SuperAdministrador',
            'ADMIN': 'Administrador',
            'SUPERVISOR': 'Supervisor',
            'USUARIO': 'Usuario',
            'VISOR': 'Visor',
            'GERENCIA': 'Gerencia',
            'COMPRAS': 'Compras',
            'VENTAS': 'Ventas',
            'TESORERIA': 'Tesoreria',
        }
        
        rol_codigo = rol['codigo'] if rol else None
        rol_mongo = ROL_SQL_TO_MONGO.get(rol_codigo, rol_codigo) if rol_codigo else None
        
        return {
            # Campos compatibles con MongoDB
            'id': str(public_uuid) if public_uuid else None,  # PublicUUID como string
            'email': email,
            'name': nombre,
            'nombre': nombre,
            'role': rol_mongo,
            'rol': rol_mongo,
            'active': bool(activo),
            'activo': bool(activo),
            'password': password_hash,  # Hash bcrypt para validación
            'empresas_permitidas': empresas,
            'empresa_default_id': empresa_default,
            
            # Campos adicionales SQL
            '_sql_usuario_id': usuario_id,  # ID interno SQL (no usar como id principal)
            '_sql_rol_id': rol['rol_id'] if rol else None,
            '_sql_rol_codigo': rol_codigo,
            '_sql_mongo_legacy_id': mongo_legacy_id,
            
            # Metadatos de fuente
            '_source': 'EDARSAHUB_SQL',
            '_fetched_at': datetime.utcnow().isoformat(),
        }
    
    # =========================================================================
    # FUNCIONES PÚBLICAS
    # =========================================================================
    
    def get_user_by_email_sql(self, email: str) -> Optional[Dict]:
        """
        Busca usuario por email en EDARSAHUB SQL.
        
        Args:
            email: Email del usuario
            
        Returns:
            Dict con estructura compatible MongoDB o None si no existe
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            cur.execute('''
                SELECT 
                    UsuarioID,
                    Email,
                    Nombre,
                    PasswordHashTexto,
                    Activo,
                    CAST(PublicUUID AS VARCHAR(36)) as PublicUUID,
                    MongoLegacyID
                FROM Usuario_Catalogo
                WHERE LOWER(Email) = LOWER(%s)
            ''', (email,))
            
            row = cur.fetchone()
            if not row:
                return None
            
            usuario_id = row[0]
            
            # Obtener rol
            rol = self._get_user_rol(cur, usuario_id)
            rol_codigo = rol['codigo'] if rol else None
            
            # Obtener empresas (aplica regla SUPERADMIN)
            empresas, empresa_default = self._get_user_empresas(cur, usuario_id, rol_codigo)
            
            return self._build_user_dict(row, rol, empresas, empresa_default)
            
        finally:
            conn.close()
    
    def get_user_by_public_uuid_sql(self, public_uuid: str) -> Optional[Dict]:
        """
        Busca usuario por PublicUUID en EDARSAHUB SQL.
        
        Args:
            public_uuid: UUID público del usuario (formato string)
            
        Returns:
            Dict con estructura compatible MongoDB o None si no existe
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            cur.execute('''
                SELECT 
                    UsuarioID,
                    Email,
                    Nombre,
                    PasswordHashTexto,
                    Activo,
                    CAST(PublicUUID AS VARCHAR(36)) as PublicUUID,
                    MongoLegacyID
                FROM Usuario_Catalogo
                WHERE CAST(PublicUUID AS VARCHAR(36)) = %s
            ''', (public_uuid,))
            
            row = cur.fetchone()
            if not row:
                return None
            
            usuario_id = row[0]
            
            # Obtener rol
            rol = self._get_user_rol(cur, usuario_id)
            rol_codigo = rol['codigo'] if rol else None
            
            # Obtener empresas (aplica regla SUPERADMIN)
            empresas, empresa_default = self._get_user_empresas(cur, usuario_id, rol_codigo)
            
            return self._build_user_dict(row, rol, empresas, empresa_default)
            
        finally:
            conn.close()
    
    def get_user_auth_context_sql(self, email_or_uuid: str) -> Optional[Dict]:
        """
        Obtiene contexto de autenticación completo desde SQL.
        Intenta primero por email, luego por UUID.
        
        Args:
            email_or_uuid: Email o UUID del usuario
            
        Returns:
            Dict con contexto de auth o None
        """
        # Intentar por email
        if '@' in email_or_uuid:
            user = self.get_user_by_email_sql(email_or_uuid)
            if user:
                return user
        
        # Intentar por UUID
        user = self.get_user_by_public_uuid_sql(email_or_uuid)
        return user
    
    def list_all_users_sql(self) -> List[Dict]:
        """Lista todos los usuarios SQL con su contexto completo"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            cur.execute('''
                SELECT 
                    UsuarioID,
                    Email,
                    Nombre,
                    PasswordHashTexto,
                    Activo,
                    CAST(PublicUUID AS VARCHAR(36)) as PublicUUID,
                    MongoLegacyID
                FROM Usuario_Catalogo
                ORDER BY UsuarioID
            ''')
            
            users = []
            for row in cur.fetchall():
                usuario_id = row[0]
                
                # Obtener rol
                rol = self._get_user_rol(cur, usuario_id)
                rol_codigo = rol['codigo'] if rol else None
                
                # Obtener empresas
                empresas, empresa_default = self._get_user_empresas(cur, usuario_id, rol_codigo)
                
                user_dict = self._build_user_dict(row, rol, empresas, empresa_default)
                users.append(user_dict)
            
            return users
            
        finally:
            conn.close()


# =========================================================================
# FUNCIONES DE COMPARACIÓN MONGODB VS SQL
# =========================================================================

async def compare_user_mongo_vs_sql(email: str) -> Dict:
    """
    Compara usuario entre MongoDB y SQL.
    
    Args:
        email: Email del usuario a comparar
        
    Returns:
        Dict con comparación detallada
    """
    import os
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # Obtener de SQL
    repo_sql = AuthRepositorySQL()
    user_sql = repo_sql.get_user_by_email_sql(email)
    
    # Obtener de MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'edarsa_hub')
    mongo_client = AsyncIOMotorClient(mongo_url)
    mongo_db = mongo_client[db_name]
    
    user_mongo = await mongo_db.users.find_one({'email': email}, {'_id': 0})
    
    mongo_client.close()
    
    # Comparar
    differences = []
    
    if not user_sql and not user_mongo:
        return {
            'email': email,
            'exists_sql': False,
            'exists_mongo': False,
            'differences': ['Usuario no existe en ninguna fuente'],
            'status': 'NOT_FOUND'
        }
    
    if not user_sql:
        return {
            'email': email,
            'exists_sql': False,
            'exists_mongo': True,
            'user_mongo': user_mongo,
            'differences': ['Usuario no migrado a SQL'],
            'status': 'MONGO_ONLY'
        }
    
    if not user_mongo:
        return {
            'email': email,
            'exists_sql': True,
            'exists_mongo': False,
            'user_sql': user_sql,
            'differences': ['Usuario solo en SQL'],
            'status': 'SQL_ONLY'
        }
    
    # Comparar campos
    # ID/UUID
    sql_id = user_sql.get('id')
    mongo_id = user_mongo.get('id')
    if sql_id != mongo_id:
        differences.append(f"id: SQL='{sql_id}' vs Mongo='{mongo_id}'")
    
    # Role
    sql_role = user_sql.get('role')
    mongo_role = user_mongo.get('role')
    if sql_role != mongo_role:
        differences.append(f"role: SQL='{sql_role}' vs Mongo='{mongo_role}'")
    
    # Active
    sql_active = user_sql.get('active')
    mongo_active = user_mongo.get('active', user_mongo.get('activo', False))
    if sql_active != mongo_active:
        differences.append(f"active: SQL={sql_active} vs Mongo={mongo_active}")
    
    # Hash presente
    sql_has_hash = bool(user_sql.get('password'))
    mongo_has_hash = bool(user_mongo.get('password'))
    if sql_has_hash != mongo_has_hash:
        differences.append(f"has_password: SQL={sql_has_hash} vs Mongo={mongo_has_hash}")
    
    # Empresas
    sql_empresas = set(user_sql.get('empresas_permitidas', []))
    mongo_empresas = set(user_mongo.get('empresas_permitidas', []))
    if sql_empresas != mongo_empresas:
        only_sql = sql_empresas - mongo_empresas
        only_mongo = mongo_empresas - sql_empresas
        if only_sql:
            differences.append(f"empresas solo en SQL: {only_sql}")
        if only_mongo:
            differences.append(f"empresas solo en Mongo: {only_mongo}")
    
    # Empresa default
    sql_default = user_sql.get('empresa_default_id')
    mongo_default = user_mongo.get('empresa_default_id')
    if sql_default != mongo_default:
        differences.append(f"empresa_default: SQL='{sql_default}' vs Mongo='{mongo_default}'")
    
    status = 'MATCH' if not differences else 'DIFFERENCES'
    
    return {
        'email': email,
        'exists_sql': True,
        'exists_mongo': True,
        'user_sql': {
            'id': user_sql.get('id'),
            'role': user_sql.get('role'),
            'active': user_sql.get('active'),
            'has_password': bool(user_sql.get('password')),
            'empresas_count': len(user_sql.get('empresas_permitidas', [])),
            'empresa_default': user_sql.get('empresa_default_id'),
        },
        'user_mongo': {
            'id': user_mongo.get('id'),
            'role': user_mongo.get('role'),
            'active': user_mongo.get('active', user_mongo.get('activo')),
            'has_password': bool(user_mongo.get('password')),
            'empresas_count': len(user_mongo.get('empresas_permitidas', [])),
            'empresa_default': user_mongo.get('empresa_default_id'),
        },
        'differences': differences,
        'status': status
    }


async def list_auth_migration_differences() -> List[Dict]:
    """
    Lista diferencias de migración Auth entre MongoDB y SQL para todos los usuarios SQL.
    
    Returns:
        Lista de comparaciones por usuario
    """
    repo_sql = AuthRepositorySQL()
    users_sql = repo_sql.list_all_users_sql()
    
    comparisons = []
    for user in users_sql:
        email = user.get('email')
        comparison = await compare_user_mongo_vs_sql(email)
        comparisons.append(comparison)
    
    return comparisons


# =========================================================================
# FUNCIONES DE UTILIDAD
# =========================================================================

def validate_superadmin_rule() -> Dict:
    """
    Valida que la regla SUPERADMIN funciona correctamente.
    
    Returns:
        Dict con resultados de validación
    """
    repo = AuthRepositorySQL()
    
    conn = repo._get_connection()
    try:
        cur = conn.cursor()
        
        # Obtener empresas activas totales
        all_empresas = repo._get_all_active_empresas(cur)
        total_empresas = len(all_empresas)
        
        # Obtener SUPERADMIN
        cur.execute('''
            SELECT u.Email, CAST(u.PublicUUID AS VARCHAR(36))
            FROM Usuario_Catalogo u
            JOIN Usuario_RolesAsignacion ra ON u.UsuarioID = ra.UsuarioID AND ra.Activo = 1
            JOIN Usuario_Roles r ON ra.RolID = r.RolID
            WHERE r.CodigoRol = 'SUPERADMIN'
        ''')
        superadmins = cur.fetchall()
        
        results = []
        for email, uuid in superadmins:
            user = repo.get_user_by_email_sql(email)
            empresas_resolved = len(user.get('empresas_permitidas', [])) if user else 0
            
            results.append({
                'email': email,
                'uuid': uuid,
                'empresas_resolved': empresas_resolved,
                'expected': total_empresas,
                'rule_applied': empresas_resolved == total_empresas
            })
        
        return {
            'total_empresas_activas': total_empresas,
            'superadmins': results,
            'rule_working': all(r['rule_applied'] for r in results)
        }
        
    finally:
        conn.close()


# =========================================================================
# EXPORTACIONES
# =========================================================================

__all__ = [
    'AuthRepositorySQL',
    'compare_user_mongo_vs_sql',
    'list_auth_migration_differences',
    'validate_superadmin_rule',
]
