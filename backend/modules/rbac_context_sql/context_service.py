from typing import Dict, Optional
from core.sql_first.db import get_sql_connection
from core.auth.sql_user_identity import resolve_sql_usuario_id

class RBACContextService:
    def get_user_context(self, current_user: Dict, unidad_negocio_id: Optional[str] = None):
        usuario_id = resolve_sql_usuario_id(current_user)
        if not usuario_id:
            return None

        with get_sql_connection() as conn:
            cur = conn.cursor()

            # usuario base
            cur.execute("""
                SELECT TOP 1
                    u.UsuarioID,
                    u.PublicUUID,
                    u.Email,
                    u.NombreCompleto,
                    u.Activo,
                    u.FechaAlta,
                    u.FechaModificacion
                FROM Usuario_Catalogo u
                WHERE u.UsuarioID = %s
            """, (usuario_id,))
            urow = cur.fetchone()
            if not urow:
                return None

            user_cols = [c[0] for c in cur.description]
            user_data = dict(zip(user_cols, urow))

            # unidades permitidas
            cur.execute("""
                SELECT DISTINCT
                    urc.UnidadNegocioID,
                    un.nombre AS UnidadNegocioNombre,
                    urc.EmpresaID,
                    e.NombreEmpresa,
                    urc.SucursalID,
                    s.NombreSucursal
                FROM Usuario_RolesContexto urc
                LEFT JOIN Unidades_Negocio un
                    ON urc.UnidadNegocioID = un.id
                LEFT JOIN Sistema_Empresas e
                    ON urc.EmpresaID = e.EmpresaID
                LEFT JOIN Sistema_Sucursales s
                    ON urc.SucursalID = s.SucursalID
                WHERE urc.UsuarioID = %s
                  AND urc.Activo = 1
                ORDER BY un.nombre
            """, (usuario_id,))
            unit_cols = [c[0] for c in cur.description]
            unidades = [dict(zip(unit_cols, r)) for r in cur.fetchall()]

            # unidad activa
            unidad_activa = unidad_negocio_id
            if not unidad_activa and unidades:
                unidad_activa = str(unidades[0]["UnidadNegocioID"]) if unidades[0]["UnidadNegocioID"] else None

            # roles contextuales activos para unidad elegida
            cur.execute("""
                SELECT
                    urc.UsuarioRolContextoID,
                    urc.UsuarioID,
                    urc.RolID,
                    r.NombreRol,
                    urc.EmpresaID,
                    urc.UnidadNegocioID,
                    urc.SucursalID,
                    urc.EsRolPrimario,
                    urc.Activo
                FROM Usuario_RolesContexto urc
                INNER JOIN Usuario_Roles r
                    ON urc.RolID = r.RolID
                WHERE urc.UsuarioID = %s
                  AND urc.Activo = 1
                  AND (%s IS NULL OR CONVERT(NVARCHAR(100), urc.UnidadNegocioID) = %s)
                ORDER BY urc.EsRolPrimario DESC, r.NombreRol
            """, (usuario_id, unidad_activa, unidad_activa))
            role_cols = [c[0] for c in cur.description]
            roles_contexto = [dict(zip(role_cols, r)) for r in cur.fetchall()]

            # permisos efectivos de la unidad activa
            cur.execute("""
                SELECT
                    urc.RolID,
                    r.NombreRol,
                    urc.UnidadNegocioID,
                    prm.ModuloID,
                    sm.Codigo AS CodigoModulo,
                    sm.Nombre AS NombreModulo,
                    prm.AccionID,
                    prm.Permitido,
                    prm.RestriccionPropietario,
                    prm.RestriccionSucursal,
                    prm.RequiereAutorizacion
                FROM Usuario_RolesContexto urc
                INNER JOIN Usuario_Roles r
                    ON urc.RolID = r.RolID
                INNER JOIN Usuario_PermisosRolModulo prm
                    ON urc.RolID = prm.RolID AND prm.Activo = 1
                LEFT JOIN Sistema_Modulos sm
                    ON prm.ModuloID = sm.ModuloID
                WHERE urc.UsuarioID = %s
                  AND urc.Activo = 1
                  AND (%s IS NULL OR CONVERT(NVARCHAR(100), urc.UnidadNegocioID) = %s)
                ORDER BY sm.Nombre, r.NombreRol
            """, (usuario_id, unidad_activa, unidad_activa))
            perm_cols = [c[0] for c in cur.description]
            permisos = [dict(zip(perm_cols, r)) for r in cur.fetchall()]

        return {
            "usuario": user_data,
            "usuario_id": usuario_id,
            "unidad_activa": unidad_activa,
            "unidades_permitidas": unidades,
            "roles_contexto": roles_contexto,
            "permisos_efectivos": permisos,
        }
