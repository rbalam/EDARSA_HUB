from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Optional
from core.security import get_current_user
from core.sql_first.db import get_sql_connection
from core.auth.sql_user_identity import enrich_current_user_with_sql_id

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


@router.get("/rbac-context/usuarios/{usuario_id}/roles-contexto")
async def listar_roles_contexto_usuario(
    usuario_id: int,
    current_user: Dict = Depends(get_current_user)
):
    current_user = enrich_current_user_with_sql_id(current_user)

    sql = """
        SELECT *
        FROM vw_Usuario_RolesContexto
        WHERE UsuarioID = %s
        ORDER BY Activo DESC, EsRolPrimario DESC, NombreRol
    """
    return _fetch_all(sql, (usuario_id,))


@router.post("/rbac-context/usuarios/{usuario_id}/roles-contexto")
async def crear_rol_contexto_usuario(
    usuario_id: int,
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    current_user = enrich_current_user_with_sql_id(current_user)

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
            body.get("rol_id"),
            body.get("empresa_id"),
            body.get("unidad_negocio_id"),
            body.get("sucursal_id"),
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
            body.get("empresa_id"),
            body.get("unidad_negocio_id"),
            body.get("sucursal_id"),
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

    sql = """
        SELECT
            urc.UsuarioID,
            urc.RolID,
            urc.NombreRol,
            urc.EmpresaID,
            urc.UnidadNegocioID,
            urc.SucursalID,
            prm.ModuloID,
            sm.Codigo AS CodigoModulo,
            sm.Nombre AS NombreModulo,
            prm.AccionID,
            prm.Permitido,
            prm.RestriccionPropietario,
            prm.RestriccionSucursal,
            prm.RequiereAutorizacion
        FROM vw_Usuario_RolesContexto urc
        INNER JOIN Usuario_PermisosRolModulo prm
            ON urc.RolID = prm.RolID AND prm.Activo = 1
        LEFT JOIN Sistema_Modulos sm
            ON prm.ModuloID = sm.ModuloID
        WHERE urc.UsuarioID = %s
          AND urc.Activo = 1
          AND (%s IS NULL OR urc.UnidadNegocioID = %s)
          AND (%s IS NULL OR urc.EmpresaID = %s)
          AND (%s IS NULL OR urc.SucursalID = %s)
        ORDER BY sm.Nombre, urc.NombreRol
    """
    return _fetch_all(sql, (
        usuario_id,
        unidad_negocio_id, unidad_negocio_id,
        empresa_id, empresa_id,
        sucursal_id, sucursal_id
    ))
