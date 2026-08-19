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
            # P5-10B: Usar TRY_CONVERT para manejar tanto INT como UUID
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
                WHERE uc.UsuarioID = TRY_CONVERT(INT, %s)
                   OR LOWER(uc.PublicUUID) = LOWER(%s)
                   OR LOWER(uc.MongoLegacyID) = LOWER(%s)
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
        
        # CANONICIDAD DE ROL: el sistema (backend ~185 sitios + frontend ~47)
        # compara mayoritariamente contra el NombreRol legacy ('SuperAdministrador',
        # 'Administrador', ...). La migración SQL-First había expuesto el CodigoRol
        # canónico ('SUPERADMIN', ...) en `role`, rompiendo esas comparaciones por
        # igualdad. Punto único de normalización: `role` lleva el NombreRol legacy
        # (lo que esperan los guards y el frontend) y se conserva el CodigoRol
        # canónico en `role_code`/`_sql_rol_codigo` para el código RBAC canónico-aware.
        role_code = user.get("CodigoRol") or ""
        role = user.get("NombreRol") or user.get("CodigoRol") or "Usuario"
        
        return {
            "id": str(user.get("PublicUUID") or user.get("MongoLegacyID") or user.get("UsuarioID")),
            "UsuarioID": user.get("UsuarioID"),
            "email": user.get("Email"),
            "username": user.get("Username"),
            "nombre": user.get("NombreCompleto") or user.get("Nombre") or user.get("Username"),
            "name": user.get("NombreCompleto") or user.get("Nombre") or user.get("Username"),
            "role": role,
            "role_code": role_code,
            "active": bool(user.get("Activo", True)),
            "password_hash": user.get("PasswordHashTexto"),
            "password": user.get("PasswordHashTexto"),  # Compatibilidad con service.py
            "auth_source": "SQL_USUARIO_CATALOGO",
            "_sql_usuario_id": user.get("UsuarioID"),
            "_sql_rol_codigo": role_code,
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
    """
    Actualiza un usuario y su rol principal en SQL canónico.

    Garantías:
    - Usuario_Catalogo + Usuario_RolesAsignacion en una sola transacción.
    - El rol se resuelve desde dbo.Usuario_Roles.
    - Sin mapas hardcodeados ni fallback implícito.
    - Exactly one active primary role cuando se solicita role.
    - Fail-closed y rollback ante cualquier inconsistencia.
    """
    conn = get_sql_connection()
    cur = conn.cursor()

    try:
        # Resolver UsuarioID canónico.
        cur.execute(
            """
            SELECT TOP 2 UsuarioID
            FROM dbo.Usuario_Catalogo
            WHERE UsuarioID = TRY_CONVERT(INT, %s)
               OR LOWER(CAST(MongoLegacyID AS NVARCHAR(128))) = LOWER(%s)
               OR LOWER(CAST(PublicUUID AS NVARCHAR(128))) = LOWER(%s)
            ORDER BY UsuarioID
            """,
            (user_id, user_id, user_id),
        )
        user_rows = cur.fetchall()

        if len(user_rows) != 1:
            raise ValueError(
                f"Usuario no encontrado o ambiguo para identificador {user_id}"
            )

        usuario_id = user_rows[0][0]

        requested_role_id = None

        if "role" in update_data:
            requested_role = str(update_data.get("role") or "").strip()
            if not requested_role:
                raise ValueError("Rol vacío no permitido")

            cur.execute(
                """
                SELECT TOP 2 RolID
                FROM dbo.Usuario_Roles
                WHERE Activo = 1
                  AND (
                        LOWER(CodigoRol) = LOWER(%s)
                     OR LOWER(NombreRol) = LOWER(%s)
                  )
                ORDER BY RolID
                """,
                (requested_role, requested_role),
            )
            role_rows = cur.fetchall()

            if len(role_rows) != 1:
                raise ValueError(
                    f"Rol inexistente, inactivo o ambiguo: {requested_role}"
                )

            requested_role_id = role_rows[0][0]

        sets = []
        params = []

        if "nombre" in update_data or "name" in update_data:
            nombre_completo = (
                update_data.get("nombre")
                or update_data.get("name")
                or ""
            ).strip()

            nombre = nombre_completo
            apellidos = ""

            if nombre_completo and " " in nombre_completo:
                nombre, apellidos = nombre_completo.split(" ", 1)

            sets.extend([
                "Nombre = %s",
                "Apellidos = %s",
            ])
            params.extend([nombre, apellidos])

        if "email" in update_data:
            sets.append("Email = %s")
            params.append(update_data["email"])

        if "password_hash" in update_data:
            sets.extend([
                "PasswordHashTexto = %s",
                "PasswordHash = NULL",
                "PasswordTemporal = 0",
                "DebeCambiarPassword = 0",
                "UltimoCambioPassword = SYSUTCDATETIME()",
            ])
            params.append(update_data["password_hash"])

        if "active" in update_data:
            sets.append("Activo = %s")
            params.append(1 if update_data["active"] else 0)

        if sets:
            sets.append("FechaModificacion = GETDATE()")
            params.append(usuario_id)

            cur.execute(
                f"""
                UPDATE dbo.Usuario_Catalogo
                SET {', '.join(sets)}
                WHERE UsuarioID = %s
                """,
                tuple(params),
            )

            if cur.rowcount != 1:
                raise RuntimeError(
                    f"Usuario_Catalogo update inesperado: rowcount={cur.rowcount}"
                )

        if requested_role_id is not None:
            # Buscar asignación reutilizable exacta.
            cur.execute(
                """
                SELECT TOP 2 UsuarioRolAsignacionID
                FROM dbo.Usuario_RolesAsignacion
                WHERE UsuarioID = %s
                  AND RolID = %s
                ORDER BY
                    CASE WHEN Activo = 1 AND EsPrincipal = 1 THEN 0 ELSE 1 END,
                    UsuarioRolAsignacionID DESC
                """,
                (usuario_id, requested_role_id),
            )
            reusable_rows = cur.fetchall()

            if len(reusable_rows) > 1:
                # Más de una fila histórica compatible no impide operar,
                # pero elegimos una única fila determinista y desactivamos el resto.
                reusable_id = reusable_rows[0][0]
            elif len(reusable_rows) == 1:
                reusable_id = reusable_rows[0][0]
            else:
                reusable_id = None

            # Desactivar cualquier principal activo distinto.
            cur.execute(
                """
                UPDATE dbo.Usuario_RolesAsignacion
                SET Activo = 0,
                    EsPrincipal = 0
                WHERE UsuarioID = %s
                  AND Activo = 1
                  AND EsPrincipal = 1
                  AND RolID <> %s
                """,
                (usuario_id, requested_role_id),
            )

            if reusable_id is not None:
                # Desactivar duplicados históricos del mismo rol.
                cur.execute(
                    """
                    UPDATE dbo.Usuario_RolesAsignacion
                    SET Activo = 0,
                        EsPrincipal = 0
                    WHERE UsuarioID = %s
                      AND RolID = %s
                      AND UsuarioRolAsignacionID <> %s
                    """,
                    (usuario_id, requested_role_id, reusable_id),
                )

                cur.execute(
                    """
                    UPDATE dbo.Usuario_RolesAsignacion
                    SET Activo = 1,
                        EsPrincipal = 1
                    WHERE UsuarioRolAsignacionID = %s
                    """,
                    (reusable_id,),
                )

                if cur.rowcount != 1:
                    raise RuntimeError(
                        "No se pudo reactivar la asignación de rol solicitada"
                    )
            else:
                cur.execute(
                    """
                    INSERT INTO dbo.Usuario_RolesAsignacion
                    (
                        UsuarioID,
                        RolID,
                        EsPrincipal,
                        Activo,
                        FechaInicio,
                        CreatedAt
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        1,
                        1,
                        GETDATE(),
                        GETDATE()
                    )
                    """,
                    (usuario_id, requested_role_id),
                )

                if cur.rowcount != 1:
                    raise RuntimeError(
                        "No se pudo insertar la asignación de rol solicitada"
                    )

            # Invariante: exactamente un rol principal activo.
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    MAX(CASE WHEN RolID = %s THEN 1 ELSE 0 END) AS requested_present
                FROM dbo.Usuario_RolesAsignacion
                WHERE UsuarioID = %s
                  AND Activo = 1
                  AND EsPrincipal = 1
                """,
                (requested_role_id, usuario_id),
            )
            invariant_row = cur.fetchone()

            total_primary = int(invariant_row[0] or 0)
            requested_present = int(invariant_row[1] or 0)

            if total_primary != 1 or requested_present != 1:
                raise RuntimeError(
                    "Invariante de rol principal violada"
                )

        if not sets and requested_role_id is None:
            raise ValueError("No hay cambios válidos para persistir")

        conn.commit()
        return True

    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise

    finally:
        conn.close()

async def delete_user(user_id: str) -> bool:
    """Desactiva usuario en SQL (compatibilidad legacy, no elimina)."""
    conn = get_sql_connection()
    cur = conn.cursor()
    
    try:
        # P5-10B: Usar TRY_CONVERT para manejar tanto INT como UUID
        cur.execute("""
        UPDATE dbo.Usuario_Catalogo 
        SET Activo = 0, FechaModificacion = GETDATE()
        WHERE UsuarioID = TRY_CONVERT(INT, %s) OR LOWER(MongoLegacyID) = LOWER(%s) OR LOWER(PublicUUID) = LOWER(%s)
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



# ============================================================
# FASE2B P0-2: Funciones module-level SQL-First para CRUD
# Usuarios/Roles (service.py llama repo.<func>() a nivel módulo)
# ============================================================

def _rows_as_dicts(cursor):
    cols = [d[0] for d in cursor.description] if cursor.description else []
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _row_as_dict(cursor):
    cols = [d[0] for d in cursor.description] if cursor.description else []
    row = cursor.fetchone()
    return dict(zip(cols, row)) if row else None


def _normalize_role(r: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normaliza fila Usuario_Roles al shape que espera service.py."""
    if not r:
        return None
    return {
        "id": str(r.get("RolID")),
        "RolID": r.get("RolID"),
        "codigo": r.get("CodigoRol"),
        "nombre": r.get("NombreRol"),
        "descripcion": r.get("Descripcion"),
        "es_sistema": bool(r.get("EsRolSistema")),
        "nivel": r.get("NivelJerarquia"),
        "activo": bool(r.get("Activo", True)),
        "permisos": [],
    }


def get_db():
    """Compatibilidad legacy: ya no hay MongoDB (SQL-First)."""
    return None


async def get_users_by_empresas(empresas_ids: list) -> list:
    """Usuarios filtrados por empresas (alcance organizacional)."""
    if not empresas_ids:
        return []
    placeholders = ",".join(["%s"] * len(empresas_ids))
    sql = f"""
        SELECT DISTINCT
            uc.UsuarioID, uc.Email, uc.Username, uc.Nombre, uc.Apellidos,
            uc.NombreCompleto, uc.Activo, uc.PublicUUID, uc.MongoLegacyID,
            ur.CodigoRol, ur.NombreRol
        FROM dbo.Usuario_Catalogo uc
        INNER JOIN dbo.Usuario_RolesContexto urc
            ON urc.UsuarioID = uc.UsuarioID AND ISNULL(urc.Activo,1)=1
        LEFT JOIN dbo.Usuario_Roles ur ON ur.RolID = urc.RolID
        WHERE urc.EmpresaID IN ({placeholders})
        ORDER BY uc.UsuarioID
    """
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, tuple(empresas_ids))
        return [AuthRepository._normalize_user(u) for u in _rows_as_dicts(cur)]
    except Exception as e:
        logging.error(f"[AuthRepository] Error get_users_by_empresas: {e}")
        return []
    finally:
        conn.close()


async def deactivate_user(user_id: str) -> bool:
    """Desactiva usuario (alias de delete_user para service.py)."""
    return await delete_user(user_id)


# ----- Roles -----

async def get_all_roles() -> list:
    sql = """
        SELECT RolID, CodigoRol, NombreRol, Descripcion,
               EsRolSistema, Activo, NivelJerarquia
        FROM dbo.Usuario_Roles
        ORDER BY NivelJerarquia DESC, NombreRol
    """
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        return [_normalize_role(r) for r in _rows_as_dicts(cur)]
    except Exception as e:
        logging.error(f"[AuthRepository] Error get_all_roles: {e}")
        return []
    finally:
        conn.close()


async def find_role_by_id(role_id) -> Optional[Dict[str, Any]]:
    sql = """
        SELECT RolID, CodigoRol, NombreRol, Descripcion,
               EsRolSistema, Activo, NivelJerarquia
        FROM dbo.Usuario_Roles
        WHERE RolID = TRY_CONVERT(INT, %s)
    """
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, (str(role_id),))
        return _normalize_role(_row_as_dict(cur))
    except Exception as e:
        logging.error(f"[AuthRepository] Error find_role_by_id: {e}")
        return None
    finally:
        conn.close()


async def find_role_by_name(role_name: str) -> Optional[Dict[str, Any]]:
    if not role_name:
        return None
    sql = """
        SELECT TOP 1 RolID, CodigoRol, NombreRol, Descripcion,
               EsRolSistema, Activo, NivelJerarquia
        FROM dbo.Usuario_Roles
        WHERE UPPER(LTRIM(RTRIM(NombreRol))) = UPPER(LTRIM(RTRIM(%s)))
           OR UPPER(LTRIM(RTRIM(CodigoRol))) = UPPER(LTRIM(RTRIM(%s)))
    """
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, (role_name, role_name))
        return _normalize_role(_row_as_dict(cur))
    except Exception as e:
        logging.error(f"[AuthRepository] Error find_role_by_name: {e}")
        return None
    finally:
        conn.close()


async def create_role(role_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    nombre = role_data.get("nombre") or role_data.get("NombreRol") or ""
    descripcion = role_data.get("descripcion") or role_data.get("Descripcion") or ""
    codigo = (role_data.get("codigo") or role_data.get("CodigoRol")
              or nombre.strip().upper().replace(" ", "_"))[:50]
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO dbo.Usuario_Roles
            (CodigoRol, NombreRol, Descripcion, EsRolSistema, Activo, FechaAlta, NivelJerarquia)
            VALUES (%s, %s, %s, 0, 1, GETDATE(), %s)
        """, (codigo, nombre, descripcion, int(role_data.get("nivel", 10))))
        cur.execute("SELECT SCOPE_IDENTITY()")
        new_id = cur.fetchone()[0]
        conn.commit()
    except Exception as e:
        logging.error(f"[AuthRepository] Error create_role: {e}")
        conn.close()
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return await find_role_by_id(int(new_id))


async def update_role(role_id, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    sets, params = [], []
    if "nombre" in update_data:
        sets.append("NombreRol = %s")
        params.append(update_data["nombre"])
    if "descripcion" in update_data:
        sets.append("Descripcion = %s")
        params.append(update_data["descripcion"])
    if not sets:
        return await find_role_by_id(role_id)
    sets.append("FechaModificacion = GETDATE()")
    params.append(str(role_id))
    sql = f"UPDATE dbo.Usuario_Roles SET {', '.join(sets)} WHERE RolID = TRY_CONVERT(INT, %s)"
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, tuple(params))
        conn.commit()
    except Exception as e:
        logging.error(f"[AuthRepository] Error update_role: {e}")
    finally:
        conn.close()
    return await find_role_by_id(role_id)


async def count_users_with_role(role_ref) -> int:
    """Cuenta usuarios activos con un rol. role_ref puede ser nombre o RolID."""
    sql = """
        SELECT COUNT(DISTINCT urc.UsuarioID) AS total
        FROM dbo.Usuario_RolesContexto urc
        INNER JOIN dbo.Usuario_Roles r ON r.RolID = urc.RolID
        WHERE ISNULL(urc.Activo,1)=1
          AND (
                r.RolID = TRY_CONVERT(INT, %s)
                OR UPPER(LTRIM(RTRIM(r.NombreRol))) = UPPER(LTRIM(RTRIM(%s)))
                OR UPPER(LTRIM(RTRIM(r.CodigoRol))) = UPPER(LTRIM(RTRIM(%s)))
          )
    """
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, (str(role_ref), str(role_ref), str(role_ref)))
        row = _row_as_dict(cur)
        return int((row or {}).get("total", 0))
    except Exception as e:
        logging.error(f"[AuthRepository] Error count_users_with_role: {e}")
        return 0
    finally:
        conn.close()


async def delete_role(role_id) -> bool:
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM dbo.Usuario_Roles WHERE RolID = TRY_CONVERT(INT, %s)", (str(role_id),))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        logging.error(f"[AuthRepository] Error delete_role: {e}")
        return False
    finally:
        conn.close()


async def create_default_roles(default_roles: list = None) -> list:
    """Crea roles predeterminados que falten. Idempotente."""
    created = []
    for role in (default_roles or []):
        nombre = role.get("nombre") if isinstance(role, dict) else str(role)
        if not nombre:
            continue
        if not await find_role_by_name(nombre):
            try:
                created.append(await create_role(role if isinstance(role, dict) else {"nombre": nombre}))
            except Exception as e:
                logging.error(f"[AuthRepository] Error create_default_roles ({nombre}): {e}")
    return created
