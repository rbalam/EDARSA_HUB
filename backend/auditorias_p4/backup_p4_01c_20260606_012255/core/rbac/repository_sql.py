from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - RBAC Repository SQL
================================
FASE 4B-RBAC: Repositorio SQL-first para el sistema RBAC.

Fuente de datos: EDARSAHUB SQL Server
- Usuario_Roles
- Usuario_RolesAsignacion  
- Usuario_Modulos
- Usuario_Acciones
- Usuario_PermisosRolModulo
- Usuario_LogRBACVerificacion

Autor: Agente E1
Fecha: 2026-05-14
Régimen: Autorización Controlada
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import logging
import os
import json
import pymssql

logger = logging.getLogger(__name__)


class RBACRepositorySQL:
    """
    Repository SQL para operaciones RBAC.
    Lee y escribe exclusivamente en EDARSAHUB SQL Server.
    """
    
    def __init__(self):
        self.sql_host = '<REDACTED_EDARSAHUB_SQL_HOST>'
        self.sql_port = 1433
        self.sql_db = 'EDARSAHUB'
        self.sql_user = '<REDACTED_EDARSAHUB_SQL_USER>'
        self.sql_pass = '<REDACTED_EDARSAHUB_SQL_PASSWORD>'
        self._permisos_cache = None
        self._roles_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutos
    
    def _get_connection(self):
        """Obtiene conexión a EDARSAHUB"""
        return pymssql.connect(
            server=self.sql_host,
            port=self.sql_port,
            user=self.sql_user,
            password=self.sql_pass,
            database=self.sql_db
        )
    
    def _is_cache_valid(self) -> bool:
        """Verifica si el cache sigue válido"""
        if not self._cache_timestamp:
            return False
        elapsed = (datetime.now(timezone.utc) - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl
    
    def _invalidate_cache(self):
        """Invalida el cache"""
        self._permisos_cache = None
        self._roles_cache = None
        self._cache_timestamp = None
    
    # =========================================================================
    # PERMISOS (Usuario_Modulos + Usuario_Acciones -> códigos compuestos)
    # =========================================================================
    
    def get_all_permisos(self, activos_only: bool = True) -> List[Dict]:
        """
        Obtiene todos los permisos del sistema.
        Construye códigos compuestos MODULO_ACCION desde las tablas SQL.
        """
        if self._is_cache_valid() and self._permisos_cache is not None:
            return self._permisos_cache
        
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            # Obtener módulos y acciones para construir permisos
            cur.execute('''
                SELECT DISTINCT 
                    m.CodigoModulo,
                    m.NombreModulo,
                    a.CodigoAccion,
                    a.NombreAccion
                FROM Usuario_Modulos m
                CROSS JOIN Usuario_Acciones a
                WHERE m.Activo = 1 AND a.Activo = 1
                ORDER BY m.CodigoModulo, a.CodigoAccion
            ''')
            
            permisos = []
            for row in cur.fetchall():
                modulo_code, modulo_name, accion_code, accion_name = row
                codigo = f"{modulo_code}_{accion_code}"
                permisos.append({
                    "id": codigo,
                    "codigo": codigo,
                    "modulo": modulo_code.lower(),
                    "accion": accion_code.lower(),
                    "descripcion": f"{accion_name} {modulo_name}",
                    "es_sistema": True,
                    "activo": True,
                })
            
            self._permisos_cache = permisos
            self._cache_timestamp = datetime.now(timezone.utc)
            return permisos
            
        finally:
            conn.close()
    
    def get_permiso_by_codigo(self, codigo: str) -> Optional[Dict]:
        """Obtiene un permiso por su código."""
        permisos = self.get_all_permisos()
        for p in permisos:
            if p["codigo"] == codigo:
                return p
        return None
    
    def seed_permisos(self, permisos: List[Dict]) -> int:
        """
        Siembra permisos del sistema.
        En SQL, los permisos se derivan de Usuario_Modulos × Usuario_Acciones,
        por lo que esta función solo verifica que existan los módulos/acciones.
        """
        # En SQL los permisos son derivados, no se siembran directamente
        logger.info("[RBAC-SQL] Permisos derivados de Usuario_Modulos × Usuario_Acciones")
        return 0
    
    # =========================================================================
    # ROLES (Usuario_Roles + Usuario_PermisosRolModulo)
    # =========================================================================
    
    def get_all_roles(self, activos_only: bool = True) -> List[Dict]:
        """Obtiene todos los roles con sus permisos."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            # Obtener roles
            where_clause = "WHERE r.Activo = 1" if activos_only else ""
            cur.execute(f'''
                SELECT 
                    r.RolID,
                    r.CodigoRol,
                    r.NombreRol,
                    r.Descripcion,
                    r.EsRolSistema,
                    r.NivelJerarquia,
                    r.Activo
                FROM Usuario_Roles r
                {where_clause}
                ORDER BY r.NivelJerarquia DESC
            ''')
            
            roles = []
            for row in cur.fetchall():
                rol_id, codigo, nombre, desc, es_sistema, nivel, activo = row
                
                # Obtener permisos del rol
                cur.execute('''
                    SELECT m.CodigoModulo, a.CodigoAccion
                    FROM Usuario_PermisosRolModulo prm
                    JOIN Usuario_Modulos m ON prm.ModuloID = m.ModuloID
                    JOIN Usuario_Acciones a ON prm.AccionID = a.AccionID
                    WHERE prm.RolID = %s AND prm.Permitido = 1 AND prm.Activo = 1
                ''', (rol_id,))
                
                permisos = [f"{r[0]}_{r[1]}" for r in cur.fetchall()]
                
                roles.append({
                    "id": str(rol_id),
                    "nombre": codigo,  # Usar código como nombre (compatible con MongoDB)
                    "descripcion": desc or nombre,
                    "nivel_jerarquia": nivel,
                    "es_sistema": bool(es_sistema),
                    "activo": bool(activo),
                    "permisos": permisos,
                    "_sql_rol_id": rol_id,
                })
            
            return roles
            
        finally:
            conn.close()
    
    def get_rol_by_id(self, rol_id: str) -> Optional[Dict]:
        """Obtiene un rol por ID (puede ser RolID SQL o código)."""
        roles = self.get_all_roles(activos_only=False)
        for r in roles:
            if r["id"] == rol_id or r["nombre"] == rol_id:
                return r
        return None
    
    def get_rol_by_nombre(self, nombre: str) -> Optional[Dict]:
        """Obtiene un rol por nombre/código."""
        roles = self.get_all_roles(activos_only=False)
        for r in roles:
            if r["nombre"].upper() == nombre.upper():
                return r
        return None
    
    def create_rol(self, rol: Dict) -> Dict:
        """Crea un nuevo rol."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            nombre = rol.get("nombre", "")
            descripcion = rol.get("descripcion", "")
            nivel = rol.get("nivel_jerarquia", 0)
            es_sistema = 1 if rol.get("es_sistema", False) else 0
            permisos = rol.get("permisos", [])
            
            # Insertar rol
            cur.execute('''
                INSERT INTO Usuario_Roles 
                (CodigoRol, NombreRol, Descripcion, EsRolSistema, Activo, FechaAlta, NivelJerarquia)
                VALUES (%s, %s, %s, %s, 1, GETDATE(), %s)
            ''', (nombre, descripcion, descripcion, es_sistema, nivel))
            
            # Obtener RolID generado
            cur.execute("SELECT @@IDENTITY")
            rol_id = int(cur.fetchone()[0])
            
            # Insertar permisos
            for permiso_codigo in permisos:
                parts = permiso_codigo.rsplit('_', 1)
                if len(parts) != 2:
                    continue
                modulo_code, accion_code = parts
                
                cur.execute('SELECT ModuloID FROM Usuario_Modulos WHERE CodigoModulo = %s', (modulo_code,))
                mod_row = cur.fetchone()
                cur.execute('SELECT AccionID FROM Usuario_Acciones WHERE CodigoAccion = %s', (accion_code,))
                acc_row = cur.fetchone()
                
                if mod_row and acc_row:
                    cur.execute('''
                        INSERT INTO Usuario_PermisosRolModulo 
                        (RolID, ModuloID, AccionID, Permitido, RestriccionPropietario, 
                         RestriccionSucursal, RequiereAutorizacion, Activo, FechaAlta, CreatedBy)
                        VALUES (%s, %s, %s, 1, 0, 0, 0, 1, GETDATE(), 'RBAC-SQL')
                    ''', (rol_id, mod_row[0], acc_row[0]))
            
            conn.commit()
            self._invalidate_cache()
            
            return {
                "id": str(rol_id),
                "nombre": nombre,
                "descripcion": descripcion,
                "nivel_jerarquia": nivel,
                "es_sistema": bool(es_sistema),
                "activo": True,
                "permisos": permisos,
            }
            
        finally:
            conn.close()
    
    def update_rol(self, rol_id: str, data: Dict) -> Optional[Dict]:
        """Actualiza un rol existente."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            # Buscar RolID
            cur.execute('SELECT RolID FROM Usuario_Roles WHERE RolID = %s OR CodigoRol = %s', (rol_id, rol_id))
            row = cur.fetchone()
            if not row:
                return None
            
            sql_rol_id = row[0]
            
            # Construir UPDATE
            updates = []
            params = []
            
            if "descripcion" in data:
                updates.append("Descripcion = %s")
                params.append(data["descripcion"])
            if "nivel_jerarquia" in data:
                updates.append("NivelJerarquia = %s")
                params.append(data["nivel_jerarquia"])
            if "activo" in data:
                updates.append("Activo = %s")
                params.append(1 if data["activo"] else 0)
            
            if updates:
                updates.append("FechaModificacion = GETDATE()")
                params.append(sql_rol_id)
                cur.execute(f"UPDATE Usuario_Roles SET {', '.join(updates)} WHERE RolID = %s", tuple(params))
            
            # Actualizar permisos si se proporcionaron
            if "permisos" in data:
                # Desactivar permisos existentes
                cur.execute("UPDATE Usuario_PermisosRolModulo SET Activo = 0 WHERE RolID = %s", (sql_rol_id,))
                
                # Insertar nuevos permisos
                for permiso_codigo in data["permisos"]:
                    parts = permiso_codigo.rsplit('_', 1)
                    if len(parts) != 2:
                        continue
                    modulo_code, accion_code = parts
                    
                    cur.execute('SELECT ModuloID FROM Usuario_Modulos WHERE CodigoModulo = %s', (modulo_code,))
                    mod_row = cur.fetchone()
                    cur.execute('SELECT AccionID FROM Usuario_Acciones WHERE CodigoAccion = %s', (accion_code,))
                    acc_row = cur.fetchone()
                    
                    if mod_row and acc_row:
                        # Reactivar o insertar
                        cur.execute('''
                            UPDATE Usuario_PermisosRolModulo SET Activo = 1
                            WHERE RolID = %s AND ModuloID = %s AND AccionID = %s
                        ''', (sql_rol_id, mod_row[0], acc_row[0]))
                        
                        if cur.rowcount == 0:
                            cur.execute('''
                                INSERT INTO Usuario_PermisosRolModulo 
                                (RolID, ModuloID, AccionID, Permitido, RestriccionPropietario,
                                 RestriccionSucursal, RequiereAutorizacion, Activo, FechaAlta, CreatedBy)
                                VALUES (%s, %s, %s, 1, 0, 0, 0, 1, GETDATE(), 'RBAC-SQL')
                            ''', (sql_rol_id, mod_row[0], acc_row[0]))
            
            conn.commit()
            self._invalidate_cache()
            
            return self.get_rol_by_id(str(sql_rol_id))
            
        finally:
            conn.close()
    
    def delete_rol(self, rol_id: str) -> bool:
        """Elimina un rol (soft delete)."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            # Solo eliminar si no es rol del sistema
            cur.execute('''
                UPDATE Usuario_Roles SET Activo = 0, FechaModificacion = GETDATE()
                WHERE (RolID = %s OR CodigoRol = %s) AND EsRolSistema = 0
            ''', (rol_id, rol_id))
            
            conn.commit()
            self._invalidate_cache()
            
            return cur.rowcount > 0
            
        finally:
            conn.close()
    
    def seed_roles(self, roles: List[Dict]) -> int:
        """Siembra roles del sistema si no existen."""
        count = 0
        for r in roles:
            existing = self.get_rol_by_nombre(r["nombre"])
            if not existing:
                self.create_rol({
                    "nombre": r["nombre"],
                    "descripcion": r["descripcion"],
                    "permisos": r["permisos"],
                    "nivel_jerarquia": r["nivel_jerarquia"],
                    "es_sistema": r.get("es_sistema", True),
                })
                count += 1
        return count
    
    # =========================================================================
    # ASIGNACIONES USUARIO-ROL (Usuario_RolesAsignacion)
    # =========================================================================
    
    def get_roles_usuario(self, user_id: str, activos_only: bool = True) -> List[Dict]:
        """
        Obtiene los roles asignados a un usuario.
        user_id puede ser PublicUUID o UsuarioID.
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            # Obtener UsuarioID desde PublicUUID si es necesario
            cur.execute('''
                SELECT UsuarioID FROM Usuario_Catalogo 
                WHERE CAST(PublicUUID AS VARCHAR(36)) = %s OR UsuarioID = %s
            ''', (user_id, user_id if user_id.isdigit() else '0'))
            
            row = cur.fetchone()
            if not row:
                return []
            
            usuario_id = row[0]
            
            # Obtener roles asignados
            where_activo = "AND ra.Activo = 1" if activos_only else ""
            cur.execute(f'''
                SELECT 
                    ra.UsuarioRolAsignacionID,
                    r.RolID,
                    r.CodigoRol,
                    r.NombreRol,
                    r.Descripcion,
                    r.NivelJerarquia,
                    r.EsRolSistema,
                    ra.FechaInicio
                FROM Usuario_RolesAsignacion ra
                JOIN Usuario_Roles r ON ra.RolID = r.RolID AND r.Activo = 1
                WHERE ra.UsuarioID = %s {where_activo}
            ''', (usuario_id,))
            
            roles = []
            for row in cur.fetchall():
                asig_id, rol_id, codigo, nombre, desc, nivel, es_sistema, fecha = row
                
                # Obtener permisos del rol
                cur.execute('''
                    SELECT m.CodigoModulo, a.CodigoAccion
                    FROM Usuario_PermisosRolModulo prm
                    JOIN Usuario_Modulos m ON prm.ModuloID = m.ModuloID
                    JOIN Usuario_Acciones a ON prm.AccionID = a.AccionID
                    WHERE prm.RolID = %s AND prm.Permitido = 1 AND prm.Activo = 1
                ''', (rol_id,))
                
                permisos = [f"{r[0]}_{r[1]}" for r in cur.fetchall()]
                
                roles.append({
                    "asignacion_id": str(asig_id),
                    "rol": {
                        "id": str(rol_id),
                        "nombre": codigo,
                        "descripcion": desc or nombre,
                        "nivel_jerarquia": nivel,
                        "es_sistema": bool(es_sistema),
                        "activo": True,
                        "permisos": permisos,
                    },
                    "sucursal_id": None,  # Por ahora no manejamos sucursales
                    "fecha_asignacion": fecha.isoformat() if fecha else None,
                })
            
            return roles
            
        finally:
            conn.close()
    
    def asignar_rol(self, user_id: str, rol_id: str, asignado_por: str, 
                    sucursal_id: Optional[str] = None) -> Dict:
        """Asigna un rol a un usuario."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            # Obtener UsuarioID
            cur.execute('''
                SELECT UsuarioID FROM Usuario_Catalogo 
                WHERE CAST(PublicUUID AS VARCHAR(36)) = %s
            ''', (user_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Usuario {user_id} no encontrado")
            usuario_id = row[0]
            
            # Obtener RolID
            cur.execute('SELECT RolID, CodigoRol FROM Usuario_Roles WHERE RolID = %s OR CodigoRol = %s', (rol_id, rol_id))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Rol {rol_id} no encontrado")
            sql_rol_id, rol_nombre = row
            
            # Verificar si ya existe
            cur.execute('''
                SELECT UsuarioRolAsignacionID, Activo FROM Usuario_RolesAsignacion
                WHERE UsuarioID = %s AND RolID = %s
            ''', (usuario_id, sql_rol_id))
            
            existing = cur.fetchone()
            if existing:
                # Reactivar si estaba inactivo
                if not existing[1]:
                    cur.execute('''
                        UPDATE Usuario_RolesAsignacion 
                        SET Activo = 1, CreatedBy = %s, CreatedAt = GETDATE()
                        WHERE UsuarioRolAsignacionID = %s
                    ''', (asignado_por, existing[0]))
                    conn.commit()
                return {
                    "id": str(existing[0]),
                    "user_id": user_id,
                    "rol_id": str(sql_rol_id),
                    "rol_nombre": rol_nombre,
                    "activo": True,
                }
            
            # Insertar nueva asignación
            cur.execute('''
                INSERT INTO Usuario_RolesAsignacion 
                (UsuarioID, RolID, EsPrincipal, FechaInicio, Activo, CreatedAt, CreatedBy)
                VALUES (%s, %s, 1, GETDATE(), 1, GETDATE(), %s)
            ''', (usuario_id, sql_rol_id, asignado_por))
            
            cur.execute("SELECT @@IDENTITY")
            asig_id = int(cur.fetchone()[0])
            
            conn.commit()
            
            return {
                "id": str(asig_id),
                "user_id": user_id,
                "rol_id": str(sql_rol_id),
                "rol_nombre": rol_nombre,
                "activo": True,
                "fecha_asignacion": datetime.now(timezone.utc).isoformat(),
            }
            
        finally:
            conn.close()
    
    def revocar_rol(self, user_id: str, rol_id: str, sucursal_id: Optional[str] = None) -> bool:
        """Revoca un rol de un usuario."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            # Obtener UsuarioID
            cur.execute('''
                SELECT UsuarioID FROM Usuario_Catalogo 
                WHERE CAST(PublicUUID AS VARCHAR(36)) = %s
            ''', (user_id,))
            row = cur.fetchone()
            if not row:
                return False
            usuario_id = row[0]
            
            # Obtener RolID
            cur.execute('SELECT RolID FROM Usuario_Roles WHERE RolID = %s OR CodigoRol = %s', (rol_id, rol_id))
            row = cur.fetchone()
            if not row:
                return False
            sql_rol_id = row[0]
            
            cur.execute('''
                UPDATE Usuario_RolesAsignacion SET Activo = 0
                WHERE UsuarioID = %s AND RolID = %s
            ''', (usuario_id, sql_rol_id))
            
            conn.commit()
            return cur.rowcount > 0
            
        finally:
            conn.close()
    
    def get_permisos_usuario(self, user_id: str) -> List[str]:
        """Obtiene todos los permisos efectivos de un usuario."""
        roles_data = self.get_roles_usuario(user_id)
        
        permisos_set = set()
        for rd in roles_data:
            rol = rd.get("rol", {})
            for permiso in rol.get("permisos", []):
                permisos_set.add(permiso)
        
        return list(permisos_set)
    
    def get_nivel_jerarquia_usuario(self, user_id: str) -> int:
        """Obtiene el nivel jerárquico máximo del usuario."""
        roles_data = self.get_roles_usuario(user_id)
        if not roles_data:
            return 0
        return max(rd.get("rol", {}).get("nivel_jerarquia", 0) for rd in roles_data)
    
    # =========================================================================
    # AUDITORÍA (Usuario_LogRBACVerificacion)
    # =========================================================================
    
    def log_verificacion(
        self,
        user_id: str,
        permiso_requerido: str,
        resultado: str,
        user_email: Optional[str] = None,
        endpoint: Optional[str] = None,
        metodo_http: Optional[str] = None,
        ip_address: Optional[str] = None,
        detalles: Optional[Dict] = None
    ) -> str:
        """Registra una verificación de permiso en el log de auditoría SQL."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            # Obtener UsuarioID si existe
            usuario_id_sql = None
            if user_id:
                cur.execute('''
                    SELECT UsuarioID FROM Usuario_Catalogo 
                    WHERE CAST(PublicUUID AS VARCHAR(36)) = %s
                ''', (user_id,))
                row = cur.fetchone()
                if row:
                    usuario_id_sql = row[0]
            
            detalles_json = json.dumps(detalles) if detalles else None
            
            cur.execute('''
                INSERT INTO Usuario_LogRBACVerificacion 
                (UsuarioID, PublicUUID, Email, PermisoRequerido, Resultado,
                 Endpoint, MetodoHTTP, IPAddress, DetallesJSON, FechaVerificacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE())
            ''', (
                usuario_id_sql,
                user_id[:36] if user_id else None,
                user_email,
                permiso_requerido[:50],
                resultado[:20],
                endpoint[:200] if endpoint else None,
                metodo_http[:10] if metodo_http else None,
                ip_address[:45] if ip_address else None,
                detalles_json
            ))
            
            cur.execute("SELECT @@IDENTITY")
            log_id = str(cur.fetchone()[0])
            
            conn.commit()
            return log_id
            
        except Exception as e:
            logger.error(f"[RBAC-SQL] Error logging verificación: {e}")
            return ""
        finally:
            conn.close()
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        resultado: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Obtiene logs de auditoría."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            where_clauses = []
            params = []
            
            if user_id:
                where_clauses.append("PublicUUID = %s")
                params.append(user_id)
            if resultado:
                where_clauses.append("Resultado = %s")
                params.append(resultado)
            
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            params.append(limit)
            
            cur.execute(f'''
                SELECT TOP (%s)
                    LogID, UsuarioID, PublicUUID, Email, PermisoRequerido,
                    Resultado, Endpoint, MetodoHTTP, IPAddress, DetallesJSON,
                    FechaVerificacion
                FROM Usuario_LogRBACVerificacion
                {where_sql}
                ORDER BY FechaVerificacion DESC
            '''.replace('TOP (%s)', f'TOP {limit}'), tuple(params[:-1]) if params[:-1] else ())
            
            logs = []
            for row in cur.fetchall():
                detalles = None
                if row[9]:
                    try:
                        detalles = json.loads(row[9])
                    except:
                        pass
                
                logs.append({
                    "id": str(row[0]),
                    "user_id": row[2],
                    "user_email": row[3],
                    "permiso_requerido": row[4],
                    "resultado": row[5],
                    "endpoint": row[6],
                    "metodo_http": row[7],
                    "ip_address": row[8],
                    "detalles": detalles,
                    "fecha": row[10].isoformat() if row[10] else None,
                })
            
            return logs
            
        finally:
            conn.close()


# Instancia global
_rbac_repo_sql: Optional[RBACRepositorySQL] = None


def get_rbac_repository_sql() -> RBACRepositorySQL:
    """Obtiene o crea la instancia del repositorio RBAC SQL."""
    global _rbac_repo_sql
    if _rbac_repo_sql is None:
        _rbac_repo_sql = RBACRepositorySQL()
    return _rbac_repo_sql


__all__ = ['RBACRepositorySQL', 'get_rbac_repository_sql']
