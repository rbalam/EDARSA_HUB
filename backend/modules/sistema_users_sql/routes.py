from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Optional
from core.security import get_current_user
from core.sql_first.db import get_sql_connection
from core.auth.sql_user_identity import enrich_current_user_with_sql_id

router = APIRouter(prefix="/api", tags=["Sistema Users SQL"])


def _fetch_all(sql: str, params=()):
    with get_sql_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def _fetch_one(sql: str, params=()):
    with get_sql_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))


@router.get("/sistema/usuarios")
async def listar_usuarios(
    current_user: Dict = Depends(get_current_user),
    activo: Optional[bool] = True
):
    current_user = enrich_current_user_with_sql_id(current_user)

    sql = """
        SELECT
            u.UsuarioID,
            u.PublicUUID,
            u.Email,
            u.NombreCompleto,
            u.Activo,
            u.FechaAlta,
            u.FechaModificacion
        FROM Usuario_Catalogo u
        WHERE (%s IS NULL OR u.Activo = %s)
        ORDER BY u.NombreCompleto
    """
    return _fetch_all(sql, (activo, activo))


@router.get("/sistema/usuarios/{usuario_id}")
async def obtener_usuario(
    usuario_id: int,
    current_user: Dict = Depends(get_current_user)
):
    current_user = enrich_current_user_with_sql_id(current_user)

    sql = """
        SELECT
            u.UsuarioID,
            u.PublicUUID,
            u.Email,
            u.NombreCompleto,
            u.Activo,
            u.FechaAlta,
            u.FechaModificacion
        FROM Usuario_Catalogo u
        WHERE u.UsuarioID = %s
    """
    row = _fetch_one(sql, (usuario_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return row


@router.get("/sistema/usuarios/email/{email}")
async def obtener_usuario_por_email(
    email: str,
    current_user: Dict = Depends(get_current_user)
):
    current_user = enrich_current_user_with_sql_id(current_user)

    sql = """
        SELECT
            u.UsuarioID,
            u.PublicUUID,
            u.Email,
            u.NombreCompleto,
            u.Activo,
            u.FechaAlta,
            u.FechaModificacion
        FROM Usuario_Catalogo u
        WHERE u.Email = %s
    """
    row = _fetch_one(sql, (email,))
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return row


@router.get("/sistema/mi-usuario")
async def obtener_mi_usuario(current_user: Dict = Depends(get_current_user)):
    current_user = enrich_current_user_with_sql_id(current_user)
    usuario_id = current_user.get("UsuarioID")

    if not usuario_id:
        raise HTTPException(status_code=404, detail="No se pudo resolver UsuarioID SQL")

    sql = """
        SELECT
            u.UsuarioID,
            u.PublicUUID,
            u.Email,
            u.NombreCompleto,
            u.Activo,
            ura.RolID,
            r.NombreRol,
            ura.EsPrincipal,
            u.FechaAlta,
            u.FechaModificacion
        FROM Usuario_Catalogo u
        LEFT JOIN Usuario_RolesAsignacion ura
            ON u.UsuarioID = ura.UsuarioID
           AND ura.Activo = 1
        LEFT JOIN Usuario_Roles r
            ON ura.RolID = r.RolID
        WHERE u.UsuarioID = %s
        ORDER BY r.NombreRol
    """
    rows = _fetch_all(sql, (usuario_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return rows
