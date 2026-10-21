from typing import Any, Dict, List, Optional
from core.sql_first.db import get_sql_connection
from core.auth.sql_user_identity import resolve_sql_usuario_id


class RBACContextService:
    def get_user_context(
        self,
        current_user: Any,
        unidad_negocio_id: Optional[str] = None,
        empresa_id: Optional[int] = None,
        sucursal_id: Optional[int] = None,
        raise_on_forbidden: bool = False,
    ) -> Optional[Dict[str, Any]]:
        usuario_id = resolve_sql_usuario_id(current_user)
        if not usuario_id:
            return None

        try:
            with get_sql_connection() as conn:
                cur = conn.cursor()

                # 1. Identidad SQL canónica en dbo.Usuario_Catalogo (fail-closed si inactivo o inexistente)
                cur.execute("""
                    SELECT TOP 1
                        u.UsuarioID,
                        u.PublicUUID,
                        u.Email,
                        u.NombreCompleto,
                        u.Activo,
                        u.FechaAlta,
                        u.FechaModificacion
                    FROM dbo.Usuario_Catalogo u
                    WHERE u.UsuarioID = %s
                      AND ISNULL(u.Activo, 1) = 1
                """, (usuario_id,))
                urow = cur.fetchone()
                if not urow:
                    return None

                user_cols = [c[0] for c in cur.description]
                user_data = dict(zip(user_cols, urow))
                if not bool(user_data.get("Activo", True)):
                    return None

                canonical_uid = int(user_data.get("UsuarioID") or usuario_id)
                canonical_puuid = (
                    str(user_data["PublicUUID"])
                    if user_data.get("PublicUUID")
                    else (
                        current_user.get("public_uuid") or current_user.get("PublicUUID")
                        if isinstance(current_user, dict)
                        else None
                    )
                )
                user_data["usuario_id"] = canonical_uid
                user_data["public_uuid"] = canonical_puuid

                # 2. Alcance contextual autorizado desde dbo.Usuario_RolesContexto
                cur.execute("""
                    SELECT DISTINCT
                        urc.UnidadNegocioID,
                        un.nombre AS UnidadNegocioNombre,
                        urc.EmpresaID,
                        e.NombreEmpresa,
                        urc.SucursalID,
                        s.NombreSucursal
                    FROM dbo.Usuario_RolesContexto urc
                    INNER JOIN dbo.Usuario_Roles r
                        ON urc.RolID = r.RolID AND ISNULL(r.Activo, 1) = 1
                    LEFT JOIN dbo.Unidades_Negocio un
                        ON urc.UnidadNegocioID = un.id
                    LEFT JOIN dbo.Sistema_Empresas e
                        ON urc.EmpresaID = e.EmpresaID
                    LEFT JOIN dbo.Sistema_Sucursales s
                        ON urc.SucursalID = s.SucursalID
                    WHERE urc.UsuarioID = %s
                      AND urc.Activo = 1
                    ORDER BY un.nombre
                """, (canonical_uid,))
                unit_cols = [c[0] for c in cur.description]
                unidades = [dict(zip(unit_cols, r)) for r in cur.fetchall()]

                # 3. Aislamiento estricto por empresa, unidad de negocio y sucursal (fail-closed)
                def _matches_scope(item: Dict[str, Any]) -> bool:
                    if empresa_id is not None and str(item.get("EmpresaID")) != str(empresa_id):
                        return False
                    if unidad_negocio_id is not None and str(item.get("UnidadNegocioID")) != str(unidad_negocio_id):
                        return False
                    if sucursal_id is not None and str(item.get("SucursalID")) != str(sucursal_id):
                        return False
                    return True

                if empresa_id is not None or unidad_negocio_id is not None or sucursal_id is not None:
                    scoped_unidades = [u for u in unidades if _matches_scope(u)]
                    if not scoped_unidades:
                        if raise_on_forbidden:
                            raise PermissionError("Contexto solicitado fuera del alcance autorizado del usuario")
                        return None
                else:
                    scoped_unidades = unidades

                unidad_activa = (
                    str(unidad_negocio_id)
                    if unidad_negocio_id is not None
                    else (
                        str(scoped_unidades[0]["UnidadNegocioID"])
                        if scoped_unidades and scoped_unidades[0].get("UnidadNegocioID") is not None
                        else None
                    )
                )
                empresa_activa = (
                    int(empresa_id)
                    if empresa_id is not None
                    else (
                        scoped_unidades[0].get("EmpresaID")
                        if scoped_unidades
                        else None
                    )
                )
                sucursal_activa = (
                    int(sucursal_id)
                    if sucursal_id is not None
                    else (
                        scoped_unidades[0].get("SucursalID")
                        if scoped_unidades
                        else None
                    )
                )

                if not scoped_unidades:
                    return {
                        "usuario": user_data,
                        "usuario_id": canonical_uid,
                        "public_uuid": canonical_puuid,
                        "empresa_activa": None,
                        "unidad_activa": None,
                        "sucursal_activa": None,
                        "unidades_permitidas": [],
                        "roles_contexto": [],
                        "permisos_efectivos": [],
                    }

                # 4. Roles contextuales activos para el alcance aislado
                cur.execute("""
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
                    INNER JOIN dbo.Usuario_Roles r
                        ON urc.RolID = r.RolID AND ISNULL(r.Activo, 1) = 1
                    WHERE urc.UsuarioID = %s
                      AND urc.Activo = 1
                      AND (%s IS NULL OR CONVERT(NVARCHAR(100), urc.UnidadNegocioID) = %s)
                      AND (%s IS NULL OR urc.EmpresaID = %s)
                      AND (%s IS NULL OR urc.SucursalID = %s)
                    ORDER BY urc.EsRolPrimario DESC, r.NombreRol
                """, (
                    canonical_uid,
                    unidad_activa, unidad_activa,
                    empresa_activa, empresa_activa,
                    sucursal_activa, sucursal_activa,
                ))
                role_cols = [c[0] for c in cur.description]
                roles_contexto = [dict(zip(role_cols, r)) for r in cur.fetchall()]

                if not roles_contexto:
                    return {
                        "usuario": user_data,
                        "usuario_id": canonical_uid,
                        "public_uuid": canonical_puuid,
                        "empresa_activa": empresa_activa,
                        "unidad_activa": unidad_activa,
                        "sucursal_activa": sucursal_activa,
                        "unidades_permitidas": unidades,
                        "roles_contexto": [],
                        "permisos_efectivos": [],
                    }

                # 5. Permisos efectivos en dbo.Usuario_PermisosRolModulo (fail-closed: prm.Activo=1 AND prm.Permitido=1)
                cur.execute("""
                    SELECT
                        urc.RolID,
                        r.CodigoRol,
                        r.NombreRol,
                        urc.EmpresaID,
                        urc.UnidadNegocioID,
                        urc.SucursalID,
                        prm.ModuloID,
                        COALESCE(um.CodigoModulo, sm.Codigo) AS CodigoModulo,
                        COALESCE(um.NombreModulo, sm.Nombre) AS NombreModulo,
                        prm.AccionID,
                        ua.CodigoAccion,
                        ua.NombreAccion,
                        prm.Permitido,
                        prm.RestriccionPropietario,
                        prm.RestriccionSucursal,
                        prm.RequiereAutorizacion
                    FROM dbo.Usuario_RolesContexto urc
                    INNER JOIN dbo.Usuario_Roles r
                        ON urc.RolID = r.RolID AND ISNULL(r.Activo, 1) = 1
                    INNER JOIN dbo.Usuario_PermisosRolModulo prm
                        ON urc.RolID = prm.RolID
                       AND prm.Activo = 1
                       AND prm.Permitido = 1
                    LEFT JOIN dbo.Usuario_Modulos um
                        ON prm.ModuloID = um.ModuloID AND ISNULL(um.Activo, 1) = 1
                    LEFT JOIN dbo.Usuario_Acciones ua
                        ON prm.AccionID = ua.AccionID AND ISNULL(ua.Activo, 1) = 1
                    LEFT JOIN dbo.Sistema_Modulos sm
                        ON prm.ModuloID = sm.ModuloID
                    WHERE urc.UsuarioID = %s
                      AND urc.Activo = 1
                      AND (%s IS NULL OR CONVERT(NVARCHAR(100), urc.UnidadNegocioID) = %s)
                      AND (%s IS NULL OR urc.EmpresaID = %s)
                      AND (%s IS NULL OR urc.SucursalID = %s)
                    ORDER BY COALESCE(um.NombreModulo, sm.Nombre), r.NombreRol
                """, (
                    canonical_uid,
                    unidad_activa, unidad_activa,
                    empresa_activa, empresa_activa,
                    sucursal_activa, sucursal_activa,
                ))
                perm_cols = [c[0] for c in cur.description]
                raw_permisos = [dict(zip(perm_cols, r)) for r in cur.fetchall()]
                permisos: List[Dict[str, Any]] = []
                for p in raw_permisos:
                    if not bool(p.get("Permitido", 0)):
                        continue
                    cod_mod = str(p.get("CodigoModulo") or "").strip().upper()
                    cod_acc = str(p.get("CodigoAccion") or "").strip().upper()
                    if cod_mod and cod_acc:
                        p["CodigoPermiso"] = f"{cod_mod}_{cod_acc}"
                    elif cod_mod:
                        p["CodigoPermiso"] = cod_mod
                    permisos.append(p)
        except PermissionError:
            raise
        except Exception:
            return None

        return {
            "usuario": user_data,
            "usuario_id": canonical_uid,
            "public_uuid": canonical_puuid,
            "empresa_activa": empresa_activa,
            "unidad_activa": unidad_activa,
            "sucursal_activa": sucursal_activa,
            "unidades_permitidas": unidades,
            "roles_contexto": roles_contexto,
            "permisos_efectivos": permisos,
        }
