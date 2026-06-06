from core.sql_first.db import fetch_all_dict, fetch_one_dict

class RBACSQLService:
    @staticmethod
    def get_user_roles(usuario_id):
        return fetch_all_dict("""
            SELECT r.CodigoRol, r.NombreRol, r.NivelJerarquia
            FROM dbo.RBAC_UsuariosRoles ur
            INNER JOIN dbo.RBAC_Roles r ON r.RolID = ur.RolID
            WHERE ur.UsuarioID = %s AND ur.Activo = 1 AND r.Activo = 1
        """, [usuario_id])

    @staticmethod
    def get_user_empresas(usuario_id):
        return fetch_all_dict("""
            SELECT EmpresaID
            FROM dbo.RBAC_UsuariosEmpresas
            WHERE UsuarioID = %s AND Activo = 1
        """, [usuario_id])

    @staticmethod
    def get_user_unidades(usuario_id):
        return fetch_all_dict("""
            SELECT UnidadNegocioID
            FROM dbo.RBAC_UsuariosUnidadesNegocio
            WHERE UsuarioID = %s AND Activo = 1
        """, [usuario_id])

    @staticmethod
    def get_user_sucursales(usuario_id):
        return fetch_all_dict("""
            SELECT SucursalID
            FROM dbo.RBAC_UsuariosSucursales
            WHERE UsuarioID = %s AND Activo = 1
        """, [usuario_id])

    @staticmethod
    def can_access_empresa(usuario_id, empresa_id):
        row = fetch_one_dict("""
            SELECT TOP 1 1 AS permitido
            FROM dbo.RBAC_UsuariosEmpresas
            WHERE UsuarioID = %s AND EmpresaID = %s AND Activo = 1
        """, [usuario_id, empresa_id])
        return bool(row)

    @staticmethod
    def can_access_unidad(usuario_id, unidad_id):
        row = fetch_one_dict("""
            SELECT TOP 1 1 AS permitido
            FROM dbo.RBAC_UsuariosUnidadesNegocio
            WHERE UsuarioID = %s AND UnidadNegocioID = %s AND Activo = 1
        """, [usuario_id, unidad_id])
        return bool(row)

    @staticmethod
    def can_access_sucursal(usuario_id, sucursal_id):
        row = fetch_one_dict("""
            SELECT TOP 1 1 AS permitido
            FROM dbo.RBAC_UsuariosSucursales
            WHERE UsuarioID = %s AND SucursalID = %s AND Activo = 1
        """, [usuario_id, sucursal_id])
        return bool(row)
