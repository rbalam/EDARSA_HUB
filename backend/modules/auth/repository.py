"""
Auth Repository - SQL Only (P5-07)
==================================
Repositorio de autenticación usando únicamente Usuario_Catalogo SQL.
Sin fallback a MongoDB.
"""
import logging
from typing import Optional, Dict, Any
from core.sql_first.db import get_sql_connection

# Variable global para compatibilidad con init_auth_repository
_db = None

def init_auth_repository(database):
    """Inicializa el repositorio (compatibilidad legacy, no usa MongoDB)."""
    global _db
    _db = database
    logging.info("[AuthRepository] Inicializado en modo SQL-only (P5-07)")

class AuthRepository:
    """Repositorio de autenticación SQL-only."""
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Obtiene usuario por email desde Usuario_Catalogo."""
        if not email:
            return None
            
        conn = get_sql_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT TOP 1
                    uc.UsuarioID,
                    uc.Email,
                    uc.Username,
                    uc.PasswordHashTexto,
                    uc.Nombre,
                    uc.Apellidos,
                    uc.NombreCompleto,
                    uc.Activo,
                    uc.PublicUUID,
                    uc.MongoLegacyID,
                    ur.CodigoRol,
                    ur.NombreRol
                FROM dbo.Usuario_Catalogo uc
                LEFT JOIN dbo.Usuario_RolesAsignacion ura 
                    ON ura.UsuarioID = uc.UsuarioID AND ISNULL(ura.Activo,1)=1 AND ISNULL(ura.EsPrincipal,0)=1
                LEFT JOIN dbo.Usuario_Roles ur 
                    ON ur.RolID = ura.RolID
                WHERE LOWER(uc.Email) = LOWER(%s)
                   OR LOWER(uc.Username) = LOWER(%s)
            """, (email, email))
            
            row = cur.fetchone()
            if not row:
                return None
            
            cols = [d[0] for d in cur.description]
            user = dict(zip(cols, row))
            
            return AuthRepository._normalize_user(user)
            
        except Exception as e:
            logging.error(f"[AuthRepository] Error get_user_by_email: {e}")
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_user_by_id(usuario_id) -> Optional[Dict[str, Any]]:
        """Obtiene usuario por ID desde Usuario_Catalogo."""
        if not usuario_id:
            return None
            
        conn = get_sql_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT TOP 1
                    uc.UsuarioID,
                    uc.Email,
                    uc.Username,
                    uc.PasswordHashTexto,
                    uc.Nombre,
                    uc.Apellidos,
                    uc.NombreCompleto,
                    uc.Activo,
                    uc.PublicUUID,
                    uc.MongoLegacyID,
                    ur.CodigoRol,
                    ur.NombreRol
                FROM dbo.Usuario_Catalogo uc
                LEFT JOIN dbo.Usuario_RolesAsignacion ura 
                    ON ura.UsuarioID = uc.UsuarioID AND ISNULL(ura.Activo,1)=1 AND ISNULL(ura.EsPrincipal,0)=1
                LEFT JOIN dbo.Usuario_Roles ur 
                    ON ur.RolID = ura.RolID
                WHERE uc.UsuarioID = %s
                   OR uc.PublicUUID = %s
                   OR uc.MongoLegacyID = %s
            """, (str(usuario_id), str(usuario_id), str(usuario_id)))
            
            row = cur.fetchone()
            if not row:
                return None
            
            cols = [d[0] for d in cur.description]
            user = dict(zip(cols, row))
            
            return AuthRepository._normalize_user(user)
            
        except Exception as e:
            logging.error(f"[AuthRepository] Error get_user_by_id: {e}")
            return None
        finally:
            conn.close()
    
    @staticmethod
    def _normalize_user(user: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza usuario SQL al formato esperado por el sistema."""
        if not user:
            return None
        
        role = user.get("CodigoRol") or user.get("NombreRol") or "USUARIO"
        
        return {
            "id": str(user.get("PublicUUID") or user.get("MongoLegacyID") or user.get("UsuarioID")),
            "UsuarioID": user.get("UsuarioID"),
            "email": user.get("Email"),
            "username": user.get("Username"),
            "nombre": user.get("NombreCompleto") or user.get("Nombre") or user.get("Username"),
            "name": user.get("NombreCompleto") or user.get("Nombre") or user.get("Username"),
            "role": role,
            "active": bool(user.get("Activo", True)),
            "password_hash": user.get("PasswordHashTexto"),
            "password": user.get("PasswordHashTexto"),  # Compatibilidad con service.py
            "auth_source": "SQL_USUARIO_CATALOGO",
            "_sql_usuario_id": user.get("UsuarioID"),
        }
    
    @staticmethod
    def build_user_response(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Construye respuesta de usuario para API."""
        if not user:
            return None
        
        return {
            "id": user.get("id"),
            "email": user.get("email"),
            "nombre": user.get("nombre"),
            "name": user.get("name"),
            "role": user.get("role"),
            "active": user.get("active"),
            "auth_source": user.get("auth_source"),
        }


# ============================================================
# Funciones de compatibilidad legacy para service.py
# ============================================================

async def find_user_by_email(email: str, include_password: bool = False) -> Optional[Dict[str, Any]]:
    """Busca usuario por email (compatibilidad legacy)."""
    user = AuthRepository.get_user_by_email(email)
    if user and not include_password:
        user.pop("password_hash", None)
    return user

async def find_user_by_id(user_id: str, include_password: bool = False) -> Optional[Dict[str, Any]]:
    """Busca usuario por ID (compatibilidad legacy)."""
    user = AuthRepository.get_user_by_id(user_id)
    if user and not include_password:
        user.pop("password_hash", None)
    return user

async def create_user(user_data: Dict[str, Any]) -> str:
    """Crea usuario en SQL (compatibilidad legacy)."""
    conn = get_sql_connection()
    cur = conn.cursor()
    
    try:
        email = user_data.get("email")
        username = user_data.get("username") or email
        password_hash = user_data.get("password_hash")
        nombre = user_data.get("nombre") or user_data.get("name", "")
        role = user_data.get("role", "USUARIO")
        
        # Separar nombre/apellidos
        apellidos = ""
        if nombre and " " in nombre:
            parts = nombre.split(" ", 1)
            nombre = parts[0]
            apellidos = parts[1]
        
        cur.execute("""
        INSERT INTO dbo.Usuario_Catalogo
        (CodigoUsuario, Username, Email, PasswordHashTexto, Nombre, Apellidos, Activo, FechaAlta)
        VALUES (%s, %s, %s, %s, %s, %s, 1, GETDATE())
        """, (username[:50], username, email, password_hash, nombre, apellidos))
        
        cur.execute("SELECT SCOPE_IDENTITY()")
        usuario_id = cur.fetchone()[0]
        
        # Asignar rol
        cur.execute("SELECT TOP 1 RolID FROM dbo.Usuario_Roles WHERE CodigoRol = %s OR LOWER(NombreRol) = LOWER(%s)", 
                   (role.upper(), role))
        row = cur.fetchone()
        if row:
            rol_id = row[0]
            cur.execute("""
            INSERT INTO dbo.Usuario_RolesAsignacion
            (UsuarioID, RolID, EsPrincipal, Activo, FechaInicio, CreatedAt)
            VALUES (%s, %s, 1, 1, GETDATE(), GETDATE())
            """, (usuario_id, rol_id))
        
        conn.commit()
        return str(usuario_id)
        
    except Exception as e:
        logging.error(f"[AuthRepository] Error create_user: {e}")
        raise
    finally:
        conn.close()

async def update_user(user_id: str, update_data: Dict[str, Any]) -> bool:
    """Actualiza usuario en SQL (compatibilidad legacy)."""
    conn = get_sql_connection()
    cur = conn.cursor()
    
    try:
        sets = []
        params = []
        
        if "nombre" in update_data or "name" in update_data:
            nombre = update_data.get("nombre") or update_data.get("name", "")
            apellidos = ""
            if nombre and " " in nombre:
                parts = nombre.split(" ", 1)
                nombre = parts[0]
                apellidos = parts[1]
            sets.append("Nombre = %s")
            sets.append("Apellidos = %s")
            params.extend([nombre, apellidos])
        
        if "email" in update_data:
            sets.append("Email = %s")
            params.append(update_data["email"])
        
        if "password_hash" in update_data:
            sets.append("PasswordHashTexto = %s")
            params.append(update_data["password_hash"])
        
        if "active" in update_data:
            sets.append("Activo = %s")
            params.append(1 if update_data["active"] else 0)
        
        if not sets:
            return True
        
        sets.append("FechaModificacion = GETDATE()")
        params.append(user_id)
        
        sql = f"UPDATE dbo.Usuario_Catalogo SET {', '.join(sets)} WHERE UsuarioID = %s OR MongoLegacyID = %s OR PublicUUID = %s"
        params.extend([user_id, user_id])
        
        cur.execute(sql, tuple(params))
        conn.commit()
        return cur.rowcount > 0
        
    except Exception as e:
        logging.error(f"[AuthRepository] Error update_user: {e}")
        return False
    finally:
        conn.close()

async def delete_user(user_id: str) -> bool:
    """Desactiva usuario en SQL (compatibilidad legacy, no elimina)."""
    conn = get_sql_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
        UPDATE dbo.Usuario_Catalogo 
        SET Activo = 0, FechaModificacion = GETDATE()
        WHERE UsuarioID = %s OR MongoLegacyID = %s OR PublicUUID = %s
        """, (user_id, user_id, user_id))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        logging.error(f"[AuthRepository] Error delete_user: {e}")
        return False
    finally:
        conn.close()

async def get_all_users(skip: int = 0, limit: int = 100) -> list:
    """Obtiene todos los usuarios (compatibilidad legacy)."""
    conn = get_sql_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
        SELECT 
            uc.UsuarioID, uc.Email, uc.Username, uc.Nombre, uc.Apellidos,
            uc.NombreCompleto, uc.Activo, uc.PublicUUID, uc.MongoLegacyID,
            ur.CodigoRol, ur.NombreRol
        FROM dbo.Usuario_Catalogo uc
        LEFT JOIN dbo.Usuario_RolesAsignacion ura 
            ON ura.UsuarioID = uc.UsuarioID AND ISNULL(ura.Activo,1)=1 AND ISNULL(ura.EsPrincipal,0)=1
        LEFT JOIN dbo.Usuario_Roles ur 
            ON ur.RolID = ura.RolID
        ORDER BY uc.UsuarioID
        OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
        """, (skip, limit))
        
        cols = [d[0] for d in cur.description]
        users = []
        for row in cur.fetchall():
            user = dict(zip(cols, row))
            users.append(AuthRepository._normalize_user(user))
        
        return users
        
    except Exception as e:
        logging.error(f"[AuthRepository] Error get_all_users: {e}")
        return []
    finally:
        conn.close()
