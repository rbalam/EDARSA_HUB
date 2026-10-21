from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List, Optional, Set, Tuple
from core.security import get_current_user
from core.sql_first.db import get_sql_connection
from core.auth.sql_user_identity import enrich_current_user_with_sql_id
from core.rbac_helper_sql import es_admin, es_superadmin

router = APIRouter(prefix="/api", tags=["RBAC Context SQL"])


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


def _resolve_actor_sql_id(current_user: Dict[str, Any]) -> Optional[int]:
    raw_id = current_user.get("usuario_id")
    if raw_id is None:
        raw_id = current_user.get("UsuarioID")
    try:
        return int(raw_id) if raw_id is not None else None
    except (TypeError, ValueError):
        return None


def _is_actor_superadmin(actor_id: Optional[int], current_user: Dict[str, Any]) -> bool:
    if es_superadmin(current_user):
        return True
    if actor_id is None:
        return False
    try:
        row = _fetch_one(
            """
            SELECT TOP 1 1 AS EsSuperAdmin
            FROM dbo.Usuario_Catalogo u
            INNER JOIN dbo.Usuario_RolesAsignacion ura
                ON ura.UsuarioID = u.UsuarioID AND ura.Activo = 1
            INNER JOIN dbo.Usuario_Roles r
                ON r.RolID = ura.RolID AND r.Activo = 1
            WHERE u.UsuarioID = %s
              AND u.Activo = 1
              AND UPPER(r.CodigoRol) IN ('SUPERADMIN', 'SUPERADMINISTRADOR')
            """,
            (actor_id,),
        )
        return bool(row and row.get("EsSuperAdmin"))
    except Exception:
        return False


def _actor_has_sql_permission(
    actor_id: Optional[int],
    current_user: Dict[str, Any],
    permission_codes: Tuple[str, ...],
) -> bool:
    if _is_actor_superadmin(actor_id, current_user) or es_admin(current_user):
        return True
    if actor_id is None or not permission_codes:
        return False
    normalized_codes = tuple(str(c).strip().upper() for c in permission_codes if c)
    if not normalized_codes:
        return False
    placeholders = ", ".join(["%s"] * len(normalized_codes))
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
            ) roles_activos
                ON roles_activos.UsuarioID = u.UsuarioID
            INNER JOIN dbo.Usuario_Roles r
                ON r.RolID = roles_activos.RolID AND r.Activo = 1
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
            (actor_id, *normalized_codes, *normalized_codes),
        )
        return bool(row)
    except Exception:
        return False


def _get_actor_scope(actor_id: Optional[int], current_user: Dict[str, Any]) -> Dict[str, Any]:
    if _is_actor_superadmin(actor_id, current_user):
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


def _assert_scope_isolation(
    actor_id: Optional[int],
    current_user: Dict[str, Any],
    empresa_id: Optional[int] = None,
    unidad_negocio_id: Optional[str] = None,
    sucursal_id: Optional[int] = None,
    require_explicit_scope_for_non_global: bool = False,
) -> Dict[str, Any]:
    scope = _get_actor_scope(actor_id, current_user)
    if scope["is_global"]:
        return scope

    has_any_scope = bool(scope["empresas"] or scope["unidades"] or scope["sucursales"])
    if require_explicit_scope_for_non_global and not has_any_scope:
        raise HTTPException(
            status_code=403,
            detail="Actor sin alcance corporativo verificable en SQL",
        )

    if empresa_id is not None and (scope["empresas"] or require_explicit_scope_for_non_global):
        if int(empresa_id) not in scope["empresas"]:
            raise HTTPException(
                status_code=403,
                detail=f"Aislamiento corporativo: sin acceso a EmpresaID={empresa_id}",
            )

    if unidad_negocio_id is not None and str(unidad_negocio_id).strip():
        norm_un = str(unidad_negocio_id).strip().upper()
        if scope["unidades"] and norm_un not in scope["unidades"]:
            raise HTTPException(
                status_code=403,
                detail=f"Aislamiento por unidad de negocio: sin acceso a UnidadNegocioID={unidad_negocio_id}",
            )

    if sucursal_id is not None and (scope["sucursales"] or (require_explicit_scope_for_non_global and not scope["empresas"] and not scope["unidades"])):
        if scope["sucursales"] and int(sucursal_id) not in scope["sucursales"]:
            raise HTTPException(
                status_code=403,
                detail=f"Aislamiento por sucursal: sin acceso a SucursalID={sucursal_id}",
            )

    return scope


def _ensure_target_user_active(usuario_id: int) -> bool:
    row = _fetch_one(
        """
        SELECT TOP 1 UsuarioID, ISNULL(Activo, 0) AS Activo
        FROM dbo.Usuario_Catalogo
        WHERE UsuarioID = %s
        """,
        (usuario_id,),
    )
    if not row:
        return False
    return bool(row.get("Activo"))


@router.get("/rbac-context/usuarios/{usuario_id}/roles-contexto")
async def listar_roles_contexto_usuario(
    usuario_id: int,
    empresa_id: Optional[int] = None,
    unidad_negocio_id: Optional[str] = None,
    sucursal_id: Optional[int] = None,
    current_user: Dict = Depends(get_current_user)
):
    current_user = enrich_current_user_with_sql_id(current_user)
    actor_id = _resolve_actor_sql_id(current_user)
    is_self = actor_id is not None and int(actor_id) == int(usuario_id)

    if not is_self and not _actor_has_sql_permission(
        actor_id,
        current_user,
        ("USUARIOS_VER", "SISTEMA_USUARIOS_VER", "USUARIOS_EDITAR", "RBAC_ADMIN"),
    ):
        raise HTTPException(
            status_code=403,
            detail="No autorizado para consultar roles contextuales de este usuario",
        )

    scope = _assert_scope_isolation(
        actor_id,
        current_user,
        empresa_id=empresa_id,
        unidad_negocio_id=unidad_negocio_id,
        sucursal_id=sucursal_id,
    )

    if not _ensure_target_user_active(usuario_id):
        return []

    sql = """
        SELECT *
        FROM vw_Usuario_RolesContexto
        WHERE UsuarioID = %s
          AND (%s IS NULL OR EmpresaID = %s)
          AND (%s IS NULL OR UnidadNegocioID = %s)
          AND (%s IS NULL OR SucursalID = %s)
        ORDER BY Activo DESC, EsRolPrimario DESC, NombreRol
    """
    rows = _fetch_all(
        sql,
        (
            usuario_id,
            empresa_id, empresa_id,
            unidad_negocio_id, unidad_negocio_id,
            sucursal_id, sucursal_id,
        ),
    )

    if not is_self and not scope["is_global"]:
        has_scope = bool(scope["empresas"] or scope["unidades"] or scope["sucursales"])
        if has_scope:
            filtered: List[Dict[str, Any]] = []
            for r in rows:
                emp = r.get("EmpresaID")
                uni = str(r.get("UnidadNegocioID") or "").strip().upper()
                suc = r.get("SucursalID")
                if scope["empresas"] and emp is not None and int(emp) not in scope["empresas"]:
                    continue
                if scope["unidades"] and uni and uni not in scope["unidades"]:
                    continue
                if scope["sucursales"] and suc is not None and int(suc) not in scope["sucursales"]:
                    continue
                filtered.append(r)
            if rows and not filtered:
                raise HTTPException(
                    status_code=403,
                    detail="Usuario fuera del alcance corporativo/contextual del solicitante",
                )
            return filtered

    return rows


@router.post("/rbac-context/usuarios/{usuario_id}/roles-contexto")
async def crear_rol_contexto_usuario(
    usuario_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    current_user = enrich_current_user_with_sql_id(current_user)
    actor_id = _resolve_actor_sql_id(current_user)

    if not _actor_has_sql_permission(
        actor_id,
        current_user,
        ("USUARIOS_EDITAR", "USUARIOS_CREAR", "SISTEMA_USUARIOS_EDITAR", "RBAC_ADMIN"),
    ):
        raise HTTPException(
            status_code=403,
            detail="No autorizado: se requiere permiso explícito para asignar roles contextuales",
        )

    rol_id = body.get("rol_id")
    if rol_id is None:
        raise HTTPException(status_code=400, detail="rol_id es obligatorio")

    empresa_id = body.get("empresa_id")
    unidad_negocio_id = body.get("unidad_negocio_id")
    sucursal_id = body.get("sucursal_id")

    _assert_scope_isolation(
        actor_id,
        current_user,
        empresa_id=empresa_id,
        unidad_negocio_id=unidad_negocio_id,
        sucursal_id=sucursal_id,
        require_explicit_scope_for_non_global=True,
    )

    if not _ensure_target_user_active(usuario_id):
        raise HTTPException(
            status_code=403,
            detail="No se puede asignar rol contextual a un usuario inactivo o inexistente en Usuario_Catalogo",
        )

    with get_sql_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO Usuario_RolesContexto (
                UsuarioID,
                RolID,
                EmpresaID,
                UnidadNegocioID,
                SucursalID,
                EsRolPrimario,
                Activo,
                FechaAlta,
                Observaciones,
                CreatedAt,
                CreatedBy
            )
            VALUES (%s, %s, %s, %s, %s, %s, 1, GETDATE(), %s, GETDATE(), %s)
        """, (
            usuario_id,
            rol_id,
            empresa_id,
            unidad_negocio_id,
            sucursal_id,
            1 if body.get("es_rol_primario") else 0,
            body.get("observaciones"),
            current_user.get("email") or str(current_user.get("id"))
        ))

        conn.commit()

    return {"ok": True, "message": "Rol contextual creado en SQL"}


@router.put("/rbac-context/roles-contexto/{usuario_rol_contexto_id}")
async def actualizar_rol_contexto(
    usuario_rol_contexto_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    current_user = enrich_current_user_with_sql_id(current_user)
    actor_id = _resolve_actor_sql_id(current_user)

    if not _actor_has_sql_permission(
        actor_id,
        current_user,
        ("USUARIOS_EDITAR", "SISTEMA_USUARIOS_EDITAR", "RBAC_ADMIN"),
    ):
        raise HTTPException(
            status_code=403,
            detail="No autorizado: se requiere permiso explícito para modificar roles contextuales",
        )

    empresa_id = body.get("empresa_id")
    unidad_negocio_id = body.get("unidad_negocio_id")
    sucursal_id = body.get("sucursal_id")

    _assert_scope_isolation(
        actor_id,
        current_user,
        empresa_id=empresa_id,
        unidad_negocio_id=unidad_negocio_id,
        sucursal_id=sucursal_id,
        require_explicit_scope_for_non_global=True,
    )

    with get_sql_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
            UPDATE Usuario_RolesContexto
            SET
                RolID = %s,
                EmpresaID = %s,
                UnidadNegocioID = %s,
                SucursalID = %s,
                EsRolPrimario = %s,
                Activo = %s,
                FechaBaja = %s,
                Observaciones = %s,
                UpdatedAt = GETDATE(),
                UpdatedBy = %s
            WHERE UsuarioRolContextoID = %s
        """, (
            body.get("rol_id"),
            empresa_id,
            unidad_negocio_id,
            sucursal_id,
            1 if body.get("es_rol_primario") else 0,
            1 if body.get("activo", True) else 0,
            body.get("fecha_baja"),
            body.get("observaciones"),
            current_user.get("email") or str(current_user.get("id")),
            usuario_rol_contexto_id
        ))

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Asignación contextual no encontrada")

        conn.commit()

    return {"ok": True, "message": "Rol contextual actualizado en SQL"}


@router.get("/rbac-context/usuarios/{usuario_id}/permisos-efectivos")
async def obtener_permisos_efectivos_usuario(
    usuario_id: int,
    unidad_negocio_id: Optional[str] = None,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    current_user: Dict = Depends(get_current_user)
):
    current_user = enrich_current_user_with_sql_id(current_user)
    actor_id = _resolve_actor_sql_id(current_user)
    is_self = actor_id is not None and int(actor_id) == int(usuario_id)

    if not is_self and not _actor_has_sql_permission(
        actor_id,
        current_user,
        ("USUARIOS_VER", "SISTEMA_USUARIOS_VER", "USUARIOS_EDITAR", "RBAC_ADMIN"),
    ):
        raise HTTPException(
            status_code=403,
            detail="No autorizado para consultar permisos efectivos de este usuario",
        )

    _assert_scope_isolation(
        actor_id,
        current_user,
        empresa_id=empresa_id,
        unidad_negocio_id=unidad_negocio_id,
        sucursal_id=sucursal_id,
    )

    if not _ensure_target_user_active(usuario_id):
        return []

    sql = """
        SELECT
            urc.UsuarioID,
            urc.RolID,
            urc.NombreRol,
            urc.EmpresaID,
            urc.UnidadNegocioID,
            urc.SucursalID,
            prm.ModuloID,
            COALESCE(m.CodigoModulo, sm.Codigo) AS CodigoModulo,
            COALESCE(m.NombreModulo, sm.Nombre) AS NombreModulo,
            prm.AccionID,
            a.CodigoAccion,
            a.NombreAccion,
            CASE
                WHEN COALESCE(m.CodigoModulo, sm.Codigo) IS NOT NULL AND a.CodigoAccion IS NOT NULL
                THEN UPPER(CONCAT(COALESCE(m.CodigoModulo, sm.Codigo), '_', a.CodigoAccion))
                ELSE UPPER(COALESCE(m.CodigoModulo, sm.Codigo, ''))
            END AS CodigoPermiso,
            prm.Permitido,
            prm.RestriccionPropietario,
            prm.RestriccionSucursal,
            prm.RequiereAutorizacion
        FROM vw_Usuario_RolesContexto urc
        INNER JOIN dbo.Usuario_Catalogo u
            ON u.UsuarioID = urc.UsuarioID
           AND u.Activo = 1
        INNER JOIN dbo.Usuario_PermisosRolModulo prm
            ON urc.RolID = prm.RolID
           AND prm.Activo = 1
           AND prm.Permitido = 1
        LEFT JOIN dbo.Usuario_Modulos m
            ON prm.ModuloID = m.ModuloID
           AND ISNULL(m.Activo, 1) = 1
        LEFT JOIN dbo.Usuario_Acciones a
            ON prm.AccionID = a.AccionID
           AND ISNULL(a.Activo, 1) = 1
        LEFT JOIN Sistema_Modulos sm
            ON prm.ModuloID = sm.ModuloID
        WHERE urc.UsuarioID = %s
          AND urc.Activo = 1
          AND (%s IS NULL OR urc.UnidadNegocioID = %s)
          AND (%s IS NULL OR urc.EmpresaID = %s)
          AND (%s IS NULL OR urc.SucursalID = %s)
        ORDER BY COALESCE(m.NombreModulo, sm.Nombre), urc.NombreRol
    """
    rows = _fetch_all(sql, (
        usuario_id,
        unidad_negocio_id, unidad_negocio_id,
        empresa_id, empresa_id,
        sucursal_id, sucursal_id
    ))
    return [r for r in rows if bool(r.get("Permitido", 0))]
