from typing import Dict, Optional
from core.sql_first.db import get_sql_connection  # CORREGIDO: era core.database

def resolve_sql_usuario_id(current_user: Dict) -> Optional[int]:
    """
    Regla:
    1. Si ya viene UsuarioID entero, usarlo.
    2. Si viene _sql_usuario_id, usarlo como compat temporal.
    3. Si viene UUIDPublico / uuid / public_id, resolver en SQL.
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
        current_user.get("UUIDPublico")
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
                WHERE UUIDPublico = %s
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
