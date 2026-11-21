from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List, Optional, Set, Tuple
from core.security import get_current_user
from core.sql_first.db import get_sql_connection
from core.auth.sql_user_identity import enrich_current_user_with_sql_id
from core.rbac_helper_sql import es_admin, es_superadmin

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


def _normalize_sql_user_row(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    raw_id = out.get("UsuarioID") if out.get("UsuarioID") is not None else out.get("usuario_id")
    if raw_id is not None:
        try:
            out["usuario_id"] = int(raw_id)
            out["UsuarioID"] = int(raw_id)
        except (TypeError, ValueError):
            out["usuario_id"] = None
    else:
        out["usuario_id"] = None

    raw_uuid = out.get("PublicUUID") if out.get("PublicUUID") is not None else out.get("public_uuid")
    out["public_uuid"] = str(raw_uuid).strip() if raw_uuid is not None and str(raw_uuid).strip() else None
    if out["public_uuid"] is not None and "PublicUUID" not in out:
        out["PublicUUID"] = out["public_uuid"]
    return out


def _resolve_actor_sql_id(current_user: Dict[str, Any]) -> Optional[int]:
    raw_id = current_user.get("usuario_id")
    if raw_id is None:
        raw_id = current_user.get("UsuarioID")
    try:
        return int(raw_id) if raw_id is not None else None
    except (TypeError, ValueError):
        return None


def _actor_has_users_permission(
    actor_id: Optional[int],
    current_user: Dict[str, Any],
    permission_codes: Tuple[str, ...] = (
        "USUARIOS_VER",
        "SISTEMA_USUARIOS_VER",
        "USUARIOS_EDITAR",
        "RBAC_ADMIN",
    ),
) -> bool:
    if es_superadmin(current_user) or es_admin(current_user):
        return True
    if actor_id is None:
        return False
    placeholders = ", ".join(["%s"] * len(permission_codes))
    try:
        row = _fetch_one(
            f"""
            SELECT TOP 1 1 AS Permitido
            FROM dbo.Usuario_Catalogo u
            INNER JOIN (
                SELECT UsuarioID, RolID
                FROM dbo.Usuario_RolesContexto
                WHERE Activo = 1
                UNION
                SELECT UsuarioID, RolID
                FROM dbo.Usuario_RolesAsignacion
                WHERE Activo = 1
            ) ra
                ON ra.UsuarioID = u.UsuarioID
            INNER JOIN dbo.Usuario_Roles r
                ON r.RolID = ra.RolID AND r.Activo = 1
            INNER JOIN dbo.Usuario_PermisosRolModulo prm
                ON prm.RolID = r.RolID
               AND prm.Activo = 1
               AND prm.Permitido = 1
            INNER JOIN dbo.Usuario_Modulos m
                ON m.ModuloID = prm.ModuloID AND m.Activo = 1
            INNER JOIN dbo.Usuario_Acciones a
                ON a.AccionID = prm.AccionID AND a.Activo = 1
            WHERE u.UsuarioID = %s
              AND u.Activo = 1
              AND (
                    UPPER(CONCAT(m.CodigoModulo, '_', a.CodigoAccion)) IN ({placeholders})
                 OR UPPER(m.CodigoModulo) IN ({placeholders})
              )
            """,
            (actor_id, *permission_codes, *permission_codes),
        )
        return bool(row)
    except Exception:
        return False


def _get_actor_scope(actor_id: Optional[int], current_user: Dict[str, Any]) -> Dict[str, Any]:
    if es_superadmin(current_user):
        return {
            "is_global": True,
            "empresas": set(),
            "unidades": set(),
            "sucursales": set(),
        }
    empresas: Set[int] = set()
    unidades: Set[str] = set()
    sucursales: Set[int] = set()
    if actor_id is not None:
        try:
            ctx_rows = _fetch_all(
                """
                SELECT EmpresaID, UnidadNegocioID, SucursalID
                FROM dbo.Usuario_RolesContexto
                WHERE UsuarioID = %s AND Activo = 1
                """,
                (actor_id,),
            )
            for r in ctx_rows or []:
                if r.get("EmpresaID") is not None:
                    empresas.add(int(r["EmpresaID"]))
                if r.get("UnidadNegocioID"):
                    unidades.add(str(r["UnidadNegocioID"]).strip().upper())
                if r.get("SucursalID") is not None:
                    sucursales.add(int(r["SucursalID"]))
        except Exception:
            pass
        try:
            emp_rows = _fetch_all(
                """
                SELECT EmpresaID
                FROM dbo.Usuario_EmpresasAsignacion
                WHERE UsuarioID = %s AND Activo = 1
                """,
                (actor_id,),
            )
            for r in emp_rows or []:
                if r.get("EmpresaID") is not None:
                    empresas.add(int(r["EmpresaID"]))
        except Exception:
            pass
    return {
        "is_global": False,
        "empresas": empresas,
        "unidades": unidades,
        "sucursales": sucursales,
    }


def _get_user_scope_summary(target_user_id: int) -> Dict[str, Any]:
    empresas: Set[int] = set()
    unidades: Set[str] = set()
    sucursales: Set[int] = set()
    roles_contexto: List[Dict[str, Any]] = []
    try:
        ctx_rows = _fetch_all(
            """
            SELECT
                urc.UsuarioRolContextoID,
                urc.UsuarioID,
                urc.RolID,
                r.CodigoRol,
                r.NombreRol,
                urc.EmpresaID,
                urc.UnidadNegocioID,
                urc.SucursalID,
                urc.EsRolPrimario,
                urc.Activo
            FROM dbo.Usuario_RolesContexto urc
            LEFT JOIN dbo.Usuario_Roles r
                ON r.RolID = urc.RolID
            WHERE urc.UsuarioID = %s AND urc.Activo = 1
            """,
            (target_user_id,),
        )
        for r in ctx_rows or []:
            roles_contexto.append(dict(r))
            if r.get("EmpresaID") is not None:
                empresas.add(int(r["EmpresaID"]))
            if r.get("UnidadNegocioID"):
                unidades.add(str(r["UnidadNegocioID"]).strip().upper())
            if r.get("SucursalID") is not None:
                sucursales.add(int(r["SucursalID"]))
    except Exception:
        pass
    try:
        emp_rows = _fetch_all(
            """
            SELECT EmpresaID
            FROM dbo.Usuario_EmpresasAsignacion
            WHERE UsuarioID = %s AND Activo = 1
            """,
            (target_user_id,),
        )
        for r in emp_rows or []:
            if r.get("EmpresaID") is not None:
                empresas.add(int(r["EmpresaID"]))
    except Exception:
        pass
    return {
        "empresas": empresas,
        "unidades": unidades,
        "sucursales": sucursales,
        "roles_contexto": roles_contexto,
    }


def _actor_can_access_target_user(
    actor_scope: Dict[str, Any],
    target_scope: Dict[str, Any],
) -> bool:
    if actor_scope["is_global"]:
        return True
    has_actor_scope = bool(
        actor_scope["empresas"] or actor_scope["unidades"] or actor_scope["sucursales"]
    )
    if not has_actor_scope:
        return True
    has_target_scope = bool(
        target_scope["empresas"] or target_scope["unidades"] or target_scope["sucursales"]
    )
    if not has_target_scope:
        return False
    if actor_scope["empresas"] and target_scope["empresas"]:
        if not (actor_scope["empresas"] & target_scope["empresas"]):
            return False
    if actor_scope["unidades"] and target_scope["unidades"]:
        if not (actor_scope["unidades"] & target_scope["unidades"]):
            return False
    if actor_scope["sucursales"] and target_scope["sucursales"]:
        if not (actor_scope["sucursales"] & target_scope["sucursales"]):
            return False
    return True


@router.get("/sistema/usuarios")
async def listar_usuarios(
    current_user: Dict = Depends(get_current_user),
    activo: Optional[bool] = True,
    empresa_id: Optional[int] = None,
    unidad_negocio_id: Optional[str] = None,
    sucursal_id: Optional[int] = None,
):
    current_user = enrich_current_user_with_sql_id(current_user)
    actor_id = _resolve_actor_sql_id(current_user)

    if not _actor_has_users_permission(actor_id, current_user):
        raise HTTPException(
            status_code=403,
            detail="No autorizado para listar el catálogo de usuarios",
        )

    actor_scope = _get_actor_scope(actor_id, current_user)
    if not actor_scope["is_global"]:
        if empresa_id is not None and actor_scope["empresas"] and int(empresa_id) not in actor_scope["empresas"]:
            raise HTTPException(
                status_code=403,
                detail=f"Aislamiento corporativo: sin acceso a EmpresaID={empresa_id}",
            )
        if unidad_negocio_id is not None and actor_scope["unidades"]:
            if str(unidad_negocio_id).strip().upper() not in actor_scope["unidades"]:
                raise HTTPException(
                    status_code=403,
                    detail=f"Aislamiento por unidad de negocio: sin acceso a UnidadNegocioID={unidad_negocio_id}",
                )
        if sucursal_id is not None and actor_scope["sucursales"] and int(sucursal_id) not in actor_scope["sucursales"]:
            raise HTTPException(
                status_code=403,
                detail=f"Aislamiento por sucursal: sin acceso a SucursalID={sucursal_id}",
            )

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
    rows = [_normalize_sql_user_row(r) for r in _fetch_all(sql, (activo, activo))]

    has_actor_scope = not actor_scope["is_global"] and bool(
        actor_scope["empresas"] or actor_scope["unidades"] or actor_scope["sucursales"]
    )
    has_explicit_filter = (
        empresa_id is not None or unidad_negocio_id is not None or sucursal_id is not None
    )

    if not has_actor_scope and not has_explicit_filter:
        return rows

    filtered: List[Dict[str, Any]] = []
    for row in rows:
        uid = row.get("usuario_id")
        if uid is None:
            continue
        target_scope = _get_user_scope_summary(uid)
        row["roles_contexto"] = target_scope["roles_contexto"]
        if has_actor_scope and not _actor_can_access_target_user(actor_scope, target_scope):
            continue
        if empresa_id is not None and int(empresa_id) not in target_scope["empresas"]:
            continue
        if unidad_negocio_id is not None and str(unidad_negocio_id).strip().upper() not in target_scope["unidades"]:
            continue
        if sucursal_id is not None and int(sucursal_id) not in target_scope["sucursales"]:
            continue
        filtered.append(row)

    return filtered


@router.get("/sistema/usuarios/{usuario_id}")
async def obtener_usuario(
    usuario_id: int,
    current_user: Dict = Depends(get_current_user)
):
    current_user = enrich_current_user_with_sql_id(current_user)
    actor_id = _resolve_actor_sql_id(current_user)
    is_self = actor_id is not None and int(actor_id) == int(usuario_id)

    if not is_self and not _actor_has_users_permission(actor_id, current_user):
        raise HTTPException(
            status_code=403,
            detail="No autorizado para consultar este usuario",
        )

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

    normalized = _normalize_sql_user_row(row)
    target_scope = _get_user_scope_summary(usuario_id)
    normalized["roles_contexto"] = target_scope["roles_contexto"]

    if not is_self:
        actor_scope = _get_actor_scope(actor_id, current_user)
        if not _actor_can_access_target_user(actor_scope, target_scope):
            raise HTTPException(
                status_code=403,
                detail="Usuario fuera del alcance corporativo/contextual autorizado",
            )

    return normalized


@router.get("/sistema/usuarios/email/{email}")
async def obtener_usuario_por_email(
    email: str,
    current_user: Dict = Depends(get_current_user)
):
    current_user = enrich_current_user_with_sql_id(current_user)
    actor_id = _resolve_actor_sql_id(current_user)
    actor_email = str(current_user.get("email") or "").strip().lower()
    is_self = bool(actor_email and actor_email == str(email or "").strip().lower())

    if not is_self and not _actor_has_users_permission(actor_id, current_user):
        raise HTTPException(
            status_code=403,
            detail="No autorizado para consultar este usuario por email",
        )

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

    normalized = _normalize_sql_user_row(row)
    uid = normalized.get("usuario_id")
    if uid is not None:
        target_scope = _get_user_scope_summary(uid)
        normalized["roles_contexto"] = target_scope["roles_contexto"]
        if not is_self:
            actor_scope = _get_actor_scope(actor_id, current_user)
            if not _actor_can_access_target_user(actor_scope, target_scope):
                raise HTTPException(
                    status_code=403,
                    detail="Usuario fuera del alcance corporativo/contextual autorizado",
                )

    return normalized


@router.get("/sistema/mi-usuario")
async def obtener_mi_usuario(current_user: Dict = Depends(get_current_user)):
    current_user = enrich_current_user_with_sql_id(current_user)
    usuario_id = _resolve_actor_sql_id(current_user)

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
            r.CodigoRol,
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
          AND u.Activo = 1
        ORDER BY r.NombreRol
    """
    rows = _fetch_all(sql, (usuario_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")

    target_scope = _get_user_scope_summary(usuario_id)
    normalized_rows: List[Dict[str, Any]] = []
    for r in rows:
        item = _normalize_sql_user_row(r)
        item["roles_contexto"] = target_scope["roles_contexto"]
        normalized_rows.append(item)
    return normalized_rows
