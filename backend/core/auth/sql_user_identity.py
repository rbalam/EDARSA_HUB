from typing import Dict, Optional
from core.sql_first.db import get_sql_connection  # CORREGIDO: era core.database

def resolve_sql_usuario_id(current_user: Dict) -> Optional[int]:
    """
    Regla:
    1. Si ya viene UsuarioID entero, usarlo.
    2. Si viene _sql_usuario_id, usarlo como compat temporal.
    3. Si viene PublicUUID / uuid / public_id, resolver en SQL.
    4. Si viene email, resolver en SQL.
    """
    if not current_user:
        return None

    for key in ("UsuarioID", "usuario_id", "_sql_usuario_id"):
        value = current_user.get(key)
        if value is not None:
            try:
                return int(value)
            except Exception:
                pass

    uuid_value = (
        current_user.get("PublicUUID")
        or current_user.get("uuid")
        or current_user.get("public_id")
        or current_user.get("user_uuid")
    )

    email = current_user.get("email") or current_user.get("Email")

    with get_sql_connection() as conn:
        cur = conn.cursor()

        if uuid_value:
            cur.execute("""
                SELECT TOP 1 UsuarioID
                FROM Usuario_Catalogo
                WHERE PublicUUID = %s
            """, (str(uuid_value),))
            row = cur.fetchone()
            if row:
                return int(row[0])

        if email:
            cur.execute("""
                SELECT TOP 1 UsuarioID
                FROM Usuario_Catalogo
                WHERE Email = %s
            """, (str(email),))
            row = cur.fetchone()
            if row:
                return int(row[0])

    return None


def enrich_current_user_with_sql_id(current_user: Dict) -> Dict:
    """
    Enriquecer sin romper compatibilidad:
    - deja UsuarioID como canónico
    - conserva _sql_usuario_id solo como compat temporal
    """
    sql_id = resolve_sql_usuario_id(current_user)
    if sql_id is not None:
        current_user["UsuarioID"] = sql_id
        current_user["_sql_usuario_id"] = sql_id
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
