from core.sql_first.db import fetch_all_dict, fetch_one_dict

class RBACSQLService:
    """
    Modelo canónico:
    - Sys_Usuarios = usuarios/login
    - Usuario_Roles = catálogo canónico de roles
    - Usuario_RolesAsignacion = asignación usuario-rol
    - Usuario_EmpresasAsignacion = alcance empresa
    - Usuario_SucursalesAsignacion = alcance sucursal
    - Usuario_ServidoresAsignacion = alcance servidor

    NO usar Sys_Roles ni RBAC_* como fuente final.
    """

    @staticmethod
    def get_roles(usuario_id):
        return fetch_all_dict("""
            SELECT
                r.CodigoRol,
                r.NombreRol,
                r.NivelJerarquia
            FROM dbo.Usuario_RolesAsignacion ura
            INNER JOIN dbo.Usuario_Roles r
                ON r.RolID = ura.RolID
            WHERE ura.UsuarioID = %s
              AND ISNULL(ura.Activo, 1) = 1
              AND ISNULL(r.Activo, 1) = 1
        """, [usuario_id])

    @staticmethod
    def get_empresas(usuario_id):
        return fetch_all_dict("""
            SELECT EmpresaID
            FROM dbo.Usuario_EmpresasAsignacion
            WHERE UsuarioID = %s
              AND ISNULL(Activo, 1) = 1
        """, [usuario_id])

    @staticmethod
    def get_sucursales(usuario_id):
        return fetch_all_dict("""
            SELECT
                UsuarioID,
                EmpresaID,
                ServidorID,
                SucursalCodigo
            FROM dbo.Usuario_SucursalesAsignacion
            WHERE UsuarioID = %s
              AND ISNULL(Activo, 1) = 1
        """, [usuario_id])

    @staticmethod
    def get_servidores(usuario_id):
        return fetch_all_dict("""
            SELECT ServidorID
            FROM dbo.Usuario_ServidoresAsignacion
            WHERE UsuarioID = %s
              AND ISNULL(Activo, 1) = 1
        """, [usuario_id])

    @staticmethod
    def get_unidades(usuario_id):
        """
        Unidad de negocio derivada desde sucursales/servidores.
        No crear Usuario_UnidadesAsignacion si el modelo actual usa sucursales/servidores.
        """
        return fetch_all_dict("""
            SELECT DISTINCT
                COALESCE(
                    TRY_CONVERT(NVARCHAR(100), sc.UnidadNegocioID),
                    TRY_CONVERT(NVARCHAR(100), sc.unidad_negocio_id),
                    TRY_CONVERT(NVARCHAR(100), sc.unidad_negocio_pk)
                ) AS UnidadNegocioID
            FROM dbo.Usuario_SucursalesAsignacion usa
            LEFT JOIN dbo.Sistema_Sucursales sc
                ON TRY_CONVERT(NVARCHAR(100), sc.ServidorID) = TRY_CONVERT(NVARCHAR(100), usa.ServidorID)
               AND TRY_CONVERT(NVARCHAR(100), sc.SucursalCodigo) = TRY_CONVERT(NVARCHAR(100), usa.SucursalCodigo)
            WHERE usa.UsuarioID = %s
              AND ISNULL(usa.Activo, 1) = 1
              AND COALESCE(
                    TRY_CONVERT(NVARCHAR(100), sc.UnidadNegocioID),
                    TRY_CONVERT(NVARCHAR(100), sc.unidad_negocio_id),
                    TRY_CONVERT(NVARCHAR(100), sc.unidad_negocio_pk)
              ) IS NOT NULL
        """, [usuario_id])

    @staticmethod
    def build_context(usuario_id):
        return {
            "roles": RBACSQLService.get_roles(usuario_id),
            "empresas": RBACSQLService.get_empresas(usuario_id),
            "sucursales": RBACSQLService.get_sucursales(usuario_id),
            "servidores": RBACSQLService.get_servidores(usuario_id),
            "unidades_negocio": RBACSQLService.get_unidades(usuario_id),
            "source": "SQL_CANONICO_SYS_USUARIOS_USUARIO_ROLES"
        }

    @staticmethod
    def can_access_empresa(usuario_id, empresa_id):
        return bool(fetch_one_dict("""
            SELECT TOP 1 1 AS permitido
            FROM dbo.Usuario_EmpresasAsignacion
            WHERE UsuarioID = %s
              AND EmpresaID = %s
              AND ISNULL(Activo, 1) = 1
        """, [usuario_id, empresa_id]))

    @staticmethod
    def can_access_sucursal(usuario_id, servidor_id, sucursal_codigo):
        return bool(fetch_one_dict("""
            SELECT TOP 1 1 AS permitido
            FROM dbo.Usuario_SucursalesAsignacion
            WHERE UsuarioID = %s
              AND ServidorID = %s
              AND SucursalCodigo = %s
              AND ISNULL(Activo, 1) = 1
        """, [usuario_id, servidor_id, sucursal_codigo]))

    @staticmethod
    def can_access_servidor(usuario_id, servidor_id):
        return bool(fetch_one_dict("""
            SELECT TOP 1 1 AS permitido
            FROM dbo.Usuario_ServidoresAsignacion
            WHERE UsuarioID = %s
              AND ServidorID = %s
              AND ISNULL(Activo, 1) = 1
        """, [usuario_id, servidor_id]))

    @staticmethod
    def can_access_unidad(usuario_id, unidad_id):
        row = fetch_one_dict("""
            SELECT TOP 1 1 AS permitido
            FROM (
                SELECT DISTINCT
                    usa.UsuarioID,
                    COALESCE(
                        TRY_CONVERT(NVARCHAR(100), sc.UnidadNegocioID),
                        TRY_CONVERT(NVARCHAR(100), sc.unidad_negocio_id),
                        TRY_CONVERT(NVARCHAR(100), sc.unidad_negocio_pk)
                    ) AS UnidadNegocioID
                FROM dbo.Usuario_SucursalesAsignacion usa
                LEFT JOIN dbo.Sistema_Sucursales sc
                    ON TRY_CONVERT(NVARCHAR(100), sc.ServidorID) = TRY_CONVERT(NVARCHAR(100), usa.ServidorID)
                   AND TRY_CONVERT(NVARCHAR(100), sc.SucursalCodigo) = TRY_CONVERT(NVARCHAR(100), usa.SucursalCodigo)
                WHERE ISNULL(usa.Activo, 1) = 1
            ) x
            WHERE x.UsuarioID = %s
              AND x.UnidadNegocioID = %s
        """, [usuario_id, str(unidad_id)])
        return bool(row)
