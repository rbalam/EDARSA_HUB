from typing import Any, Dict, Optional
from core.sql_first.db import get_sql_connection  # CORREGIDO: era core.database


def resolve_sql_user_identity(current_user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Resuelve la identidad canónica desde dbo.Usuario_Catalogo (fail-closed).
    Retorna {'usuario_id': int, 'public_uuid': Optional[str], 'email': Optional[str], 'activo': bool}
    únicamente cuando el usuario existe y está activo (Activo = 1).
    """
    if not current_user or not isinstance(current_user, dict):
        return None

    direct_id: Optional[int] = None
    for key in ("usuario_id", "UsuarioID", "_sql_usuario_id"):
        value = current_user.get(key)
        if value is not None and not isinstance(value, bool):
            try:
                candidate = int(value)
                if candidate > 0:
                    direct_id = candidate
                    break
            except Exception:
                pass

    uuid_value = (
        current_user.get("public_uuid")
        or current_user.get("PublicUUID")
        or current_user.get("uuid")
        or current_user.get("public_id")
        or current_user.get("user_uuid")
    )
    if not uuid_value:
        raw_id = current_user.get("id") or current_user.get("user_id")
        if isinstance(raw_id, str) and "-" in raw_id and len(raw_id.strip()) >= 32:
            uuid_value = raw_id.strip()

    email = current_user.get("email") or current_user.get("Email")

    try:
        with get_sql_connection() as conn:
            cur = conn.cursor()

            if direct_id is not None:
                cur.execute(
                    """
                    SELECT TOP 1 UsuarioID, PublicUUID, Email, ISNULL(Activo, 1)
                    FROM dbo.Usuario_Catalogo
                    WHERE UsuarioID = %s
                    """,
                    (direct_id,),
                )
                row = cur.fetchone()
                if row:
                    if not bool(row[3]):
                        return None
                    return {
                        "usuario_id": int(row[0]),
                        "public_uuid": str(row[1]) if row[1] else (str(uuid_value) if uuid_value else None),
                        "email": str(row[2]) if row[2] else (str(email) if email else None),
                        "activo": True,
                    }

            if uuid_value:
                cur.execute(
                    """
                    SELECT TOP 1 UsuarioID, PublicUUID, Email, ISNULL(Activo, 1)
                    FROM dbo.Usuario_Catalogo
                    WHERE LOWER(CAST(PublicUUID AS NVARCHAR(64))) = LOWER(%s)
                    """,
                    (str(uuid_value),),
                )
                row = cur.fetchone()
                if row:
                    if not bool(row[3]):
                        return None
                    return {
                        "usuario_id": int(row[0]),
                        "public_uuid": str(row[1]) if row[1] else str(uuid_value),
                        "email": str(row[2]) if row[2] else (str(email) if email else None),
                        "activo": True,
                    }

            if email:
                cur.execute(
                    """
                    SELECT TOP 1 UsuarioID, PublicUUID, Email, ISNULL(Activo, 1)
                    FROM dbo.Usuario_Catalogo
                    WHERE LOWER(Email) = LOWER(%s)
                    """,
                    (str(email),),
                )
                row = cur.fetchone()
                if row:
                    if not bool(row[3]):
                        return None
                    return {
                        "usuario_id": int(row[0]),
                        "public_uuid": str(row[1]) if row[1] else (str(uuid_value) if uuid_value else None),
                        "email": str(row[2]) if row[2] else str(email),
                        "activo": True,
                    }
    except Exception:
        if direct_id is not None and bool(current_user.get("active", current_user.get("Activo", True))):
            return {
                "usuario_id": direct_id,
                "public_uuid": str(uuid_value) if uuid_value else None,
                "email": str(email) if email else None,
                "activo": True,
            }
        return None

    if direct_id is not None and bool(current_user.get("active", current_user.get("Activo", True))):
        return {
            "usuario_id": direct_id,
            "public_uuid": str(uuid_value) if uuid_value else None,
            "email": str(email) if email else None,
            "activo": True,
        }

    return None


def resolve_sql_usuario_id(current_user: Dict) -> Optional[int]:
    """
    Regla:
    1. Si ya viene UsuarioID / usuario_id entero, usarlo.
    2. Si viene _sql_usuario_id, usarlo como compat temporal.
    3. Si viene public_uuid / PublicUUID / uuid / public_id, resolver en SQL.
    4. Si viene email, resolver en SQL.
    """
    if not current_user:
        return None

    if isinstance(current_user, int) and not isinstance(current_user, bool):
        return int(current_user) if current_user > 0 else None

    if not isinstance(current_user, dict):
        return None

    if current_user.get("active") is False or current_user.get("Activo") is False:
        return None

    for key in ("usuario_id", "UsuarioID", "_sql_usuario_id"):
        value = current_user.get(key)
        if value is not None and not isinstance(value, bool):
            try:
                return int(value)
            except Exception:
                pass

    uuid_value = (
        current_user.get("public_uuid")
        or current_user.get("PublicUUID")
        or current_user.get("uuid")
        or current_user.get("public_id")
        or current_user.get("user_uuid")
    )
    if not uuid_value:
        raw_id = current_user.get("id") or current_user.get("user_id")
        if isinstance(raw_id, str) and "-" in raw_id and len(raw_id.strip()) >= 32:
            uuid_value = raw_id.strip()

    email = current_user.get("email") or current_user.get("Email")

    with get_sql_connection() as conn:
        cur = conn.cursor()

        if uuid_value:
            cur.execute("""
                SELECT TOP 1 UsuarioID, ISNULL(Activo, 1)
                FROM Usuario_Catalogo
                WHERE PublicUUID = %s
                  AND ISNULL(Activo, 1) = 1
            """, (str(uuid_value),))
            row = cur.fetchone()
            if row:
                if len(row) >= 4 and not bool(row[3]):
                    return None
                if len(row) >= 2 and isinstance(row[1], (int, bool)) and not bool(row[1]):
                    return None
                return int(row[0])

        if email:
            cur.execute("""
                SELECT TOP 1 UsuarioID, ISNULL(Activo, 1)
                FROM Usuario_Catalogo
                WHERE Email = %s
                  AND ISNULL(Activo, 1) = 1
            """, (str(email),))
            row = cur.fetchone()
            if row:
                if len(row) >= 4 and not bool(row[3]):
                    return None
                if len(row) >= 2 and isinstance(row[1], (int, bool)) and not bool(row[1]):
                    return None
                return int(row[0])

    return None


def enrich_current_user_with_sql_id(current_user: Dict) -> Dict:
    """
    Enriquecer sin romper compatibilidad:
    - expone usuario_id y public_uuid canónicos junto con UsuarioID y PublicUUID
    - conserva _sql_usuario_id solo como compat temporal
    """
    if not current_user or not isinstance(current_user, dict):
        return current_user

    identity = resolve_sql_user_identity(current_user)
    if identity:
        sql_id = identity["usuario_id"]
        pub_uuid = identity.get("public_uuid")
    else:
        sql_id = resolve_sql_usuario_id(current_user)
        pub_uuid = (
            current_user.get("public_uuid")
            or current_user.get("PublicUUID")
            or (
                str(current_user["id"])
                if isinstance(current_user.get("id"), str) and "-" in current_user.get("id", "")
                else None
            )
        )

    if sql_id is not None:
        current_user["usuario_id"] = int(sql_id)
        current_user["UsuarioID"] = int(sql_id)
        current_user["_sql_usuario_id"] = int(sql_id)
    if pub_uuid:
        current_user["public_uuid"] = str(pub_uuid)
        current_user.setdefault("PublicUUID", str(pub_uuid))
    return current_user

# Identificador técnico canónico creado por la migración RBAC de Alertas.
# Es una constante técnica de infraestructura; nunca un UsuarioID fijo.
ALERTAS_SCHEDULER_PRINCIPAL_CODE = "SYS-SCHED-ALERTAS"


class SystemPrincipalResolutionError(RuntimeError):
    """No fue posible resolver de forma inequívoca un principal técnico."""


def resolve_system_principal_current_user(
    codigo_usuario: str,
) -> Dict:
    """
    Resuelve un principal técnico SQL de forma fail-closed.

    Requisitos:
    - CodigoUsuario exacto.
    - Activo.
    - No interactivo (EsUsuarioPortal=0).
    - Bloqueado para login humano.
    - Exactamente una fila.

    Devuelve únicamente la identidad mínima que consume el RBAC.
    """
    code = str(codigo_usuario or "").strip()

    if not code:
        raise SystemPrincipalResolutionError(
            "CodigoUsuario técnico requerido"
        )

    with get_sql_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT UsuarioID
            FROM dbo.Usuario_Catalogo
            WHERE CodigoUsuario = %s
              AND ISNULL(Activo, 0) = 1
              AND ISNULL(EsUsuarioPortal, 1) = 0
              AND ISNULL(Bloqueado, 0) = 1
            """,
            (code,),
        )
        rows = cur.fetchall()

    if len(rows) != 1:
        raise SystemPrincipalResolutionError(
            "Principal técnico no resoluble de forma única: "
            f"codigo={code!r}, coincidencias={len(rows)}"
        )

    try:
        usuario_id = int(rows[0][0])
    except Exception as exc:
        raise SystemPrincipalResolutionError(
            "UsuarioID inválido para principal técnico"
        ) from exc

    return {
        "UsuarioID": usuario_id,
        "CodigoUsuario": code,
    }


def resolve_alertas_scheduler_current_user() -> Dict:
    """Identidad técnica canónica para los jobs de Alertas Estratégicas."""
    return resolve_system_principal_current_user(
        ALERTAS_SCHEDULER_PRINCIPAL_CODE
    )
