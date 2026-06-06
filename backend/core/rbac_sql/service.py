from core.sql_first.db import fetch_all_dict, fetch_one_dict

class RBACSQLService:
    """
    RBAC SQL usando modelo canónico existente:
    - Sys_Usuarios
    - Sys_Roles / Usuario_Roles
    - Usuario_RolesAsignacion
    - Usuario_EmpresasAsignacion
    - Usuario_SucursalesAsignacion
    """

    @staticmethod
    def get_roles(usuario_id):
        return fetch_all_dict("""
            SELECT
                COALESCE(r.CodigoRol, r.Codigo, r.NombreRol, r.Nombre) AS CodigoRol,
                COALESCE(r.NombreRol, r.Nombre, r.CodigoRol, r.Codigo) AS NombreRol,
                COALESCE(TRY_CONVERT(INT, r.NivelJerarquia), 10) AS NivelJerarquia
            FROM dbo.Usuario_RolesAsignacion ura
            INNER JOIN dbo.Usuario_Roles r
                ON TRY_CONVERT(NVARCHAR(100), r.RolID) = TRY_CONVERT(NVARCHAR(100), ura.RolID)
                OR TRY_CONVERT(NVARCHAR(100), r.Id) = TRY_CONVERT(NVARCHAR(100), ura.RolID)
            WHERE TRY_CONVERT(NVARCHAR(100), ura.UsuarioID) = %s
              AND COALESCE(TRY_CONVERT(BIT, ura.Activo), 1) = 1
              AND COALESCE(TRY_CONVERT(BIT, r.Activo), 1) = 1
        """, [str(usuario_id)])

    @staticmethod
    def get_empresas(usuario_id):
        return fetch_all_dict("""
            SELECT TRY_CONVERT(NVARCHAR(100), EmpresaID) AS EmpresaID
            FROM dbo.Usuario_EmpresasAsignacion
            WHERE TRY_CONVERT(NVARCHAR(100), UsuarioID) = %s
              AND COALESCE(TRY_CONVERT(BIT, Activo), 1) = 1
        """, [str(usuario_id)])

    @staticmethod
    def get_sucursales(usuario_id):
        return fetch_all_dict("""
            SELECT TRY_CONVERT(NVARCHAR(100), SucursalID) AS SucursalID
            FROM dbo.Usuario_SucursalesAsignacion
            WHERE TRY_CONVERT(NVARCHAR(100), UsuarioID) = %s
              AND COALESCE(TRY_CONVERT(BIT, Activo), 1) = 1
        """, [str(usuario_id)])

    @staticmethod
    def get_unidades(usuario_id):
        return fetch_all_dict("""
            SELECT DISTINCT
                COALESCE(
                    TRY_CONVERT(NVARCHAR(100), sc.UnidadNegocioID),
                    TRY_CONVERT(NVARCHAR(100), sc.unidad_negocio_id),
                    TRY_CONVERT(NVARCHAR(100), sc.unidad_negocio_pk)
                ) AS UnidadNegocioID
            FROM dbo.Usuario_SucursalesAsignacion usa
            LEFT JOIN dbo.Sucursales_Catalogo sc
                ON TRY_CONVERT(NVARCHAR(100), sc.SucursalID) = TRY_CONVERT(NVARCHAR(100), usa.SucursalID)
                OR TRY_CONVERT(NVARCHAR(100), sc.Id) = TRY_CONVERT(NVARCHAR(100), usa.SucursalID)
            WHERE TRY_CONVERT(NVARCHAR(100), usa.UsuarioID) = %s
              AND COALESCE(TRY_CONVERT(BIT, usa.Activo), 1) = 1
              AND COALESCE(
                    TRY_CONVERT(NVARCHAR(100), sc.UnidadNegocioID),
                    TRY_CONVERT(NVARCHAR(100), sc.unidad_negocio_id),
                    TRY_CONVERT(NVARCHAR(100), sc.unidad_negocio_pk)
              ) IS NOT NULL
        """, [str(usuario_id)])

    @staticmethod
    def build_context(usuario_id):
        return {
            "roles": RBACSQLService.get_roles(usuario_id),
            "empresas": RBACSQLService.get_empresas(usuario_id),
            "unidades_negocio": RBACSQLService.get_unidades(usuario_id),
            "sucursales": RBACSQLService.get_sucursales(usuario_id),
            "source": "SQL_CANONICO_SYS_USUARIO"
        }

    @staticmethod
    def can_access_empresa(usuario_id, empresa_id):
        return bool(fetch_one_dict("""
            SELECT TOP 1 1 AS permitido
            FROM dbo.Usuario_EmpresasAsignacion
            WHERE TRY_CONVERT(NVARCHAR(100), UsuarioID) = %s
              AND TRY_CONVERT(NVARCHAR(100), EmpresaID) = %s
              AND COALESCE(TRY_CONVERT(BIT, Activo), 1) = 1
        """, [str(usuario_id), str(empresa_id)]))

    @staticmethod
    def can_access_sucursal(usuario_id, sucursal_id):
        return bool(fetch_one_dict("""
            SELECT TOP 1 1 AS permitido
            FROM dbo.Usuario_SucursalesAsignacion
            WHERE TRY_CONVERT(NVARCHAR(100), UsuarioID) = %s
              AND TRY_CONVERT(NVARCHAR(100), SucursalID) = %s
              AND COALESCE(TRY_CONVERT(BIT, Activo), 1) = 1
        """, [str(usuario_id), str(sucursal_id)]))

    @staticmethod
    def can_access_unidad(usuario_id, unidad_id):
        row = fetch_one_dict("""
            SELECT TOP 1 1 AS permitido
            FROM (
                SELECT DISTINCT
                    TRY_CONVERT(NVARCHAR(100), usa.UsuarioID) AS UsuarioID,
                    COALESCE(
                        TRY_CONVERT(NVARCHAR(100), sc.UnidadNegocioID),
                        TRY_CONVERT(NVARCHAR(100), sc.unidad_negocio_id),
                        TRY_CONVERT(NVARCHAR(100), sc.unidad_negocio_pk)
                    ) AS UnidadID
                FROM dbo.Usuario_SucursalesAsignacion usa
                LEFT JOIN dbo.Sucursales_Catalogo sc
                    ON TRY_CONVERT(NVARCHAR(100), sc.SucursalID) = TRY_CONVERT(NVARCHAR(100), usa.SucursalID)
                    OR TRY_CONVERT(NVARCHAR(100), sc.Id) = TRY_CONVERT(NVARCHAR(100), usa.SucursalID)
                WHERE COALESCE(TRY_CONVERT(BIT, usa.Activo), 1) = 1
            ) x
            WHERE x.UsuarioID = %s AND x.UnidadID = %s
        """, [str(usuario_id), str(unidad_id)])
        return bool(row)
