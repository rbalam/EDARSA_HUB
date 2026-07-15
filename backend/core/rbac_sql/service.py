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

    @staticmethod
    def get_permission_scope_by_code(
        usuario_id,
        permission_code,
    ):
        """
        Resuelve un permiso funcional activo para el UsuarioID SQL.

        No usa nombre de rol, jerarquía hardcodeada ni datos del JWT.
        """
        normalized_permission = str(
            permission_code or ""
        ).strip()

        if not usuario_id or not normalized_permission:
            return None

        row = fetch_one_dict("""
            SELECT
                CASE
                    WHEN COUNT_BIG(*) > 0 THEN 1
                    ELSE 0
                END AS permitido,
                CASE
                    WHEN MIN(
                        CASE
                            WHEN ISNULL(
                                prm.RestriccionSucursal,
                                0
                            ) = 0
                            THEN 0
                            ELSE 1
                        END
                    ) = 1
                    THEN 1
                    ELSE 0
                END AS restriccion_sucursal
            FROM dbo.Usuario_RolesAsignacion AS ura
            INNER JOIN dbo.Usuario_Roles AS r
                ON r.RolID = ura.RolID
            INNER JOIN dbo.Usuario_PermisosRolModulo AS prm
                ON prm.RolID = r.RolID
            INNER JOIN dbo.Usuario_Modulos AS m
                ON m.ModuloID = prm.ModuloID
            INNER JOIN dbo.Usuario_Acciones AS a
                ON a.AccionID = prm.AccionID
            WHERE ura.UsuarioID = %s
              AND CONCAT(
                    m.CodigoModulo,
                    '_',
                    a.CodigoAccion
                  ) = %s
              AND ISNULL(ura.Activo, 1) = 1
              AND ISNULL(r.Activo, 1) = 1
              AND ISNULL(prm.Activo, 1) = 1
              AND ISNULL(prm.Permitido, 0) = 1
              AND ISNULL(m.Activo, 1) = 1
              AND ISNULL(a.Activo, 1) = 1
        """, [usuario_id, normalized_permission])

        if not row or not bool(row.get("permitido")):
            return None

        return {
            "permission_code": normalized_permission,
            "permitido": True,
            "restriccion_sucursal": bool(
                row.get("restriccion_sucursal")
            ),
        }

    @staticmethod
    def can_access_permission(
        usuario_id,
        permission_code,
    ):
        try:
            return bool(
                RBACSQLService.get_permission_scope_by_code(
                    usuario_id,
                    permission_code,
                )
            )
        except Exception:
            return False

    @staticmethod
    def get_scope_assignment_state(usuario_id):
        """
        Devuelve únicamente el estado agregado de asignaciones explícitas.

        Cualquier error será tratado como denegación por el consumidor.
        """
        if not usuario_id:
            return None

        row = fetch_one_dict("""
            SELECT
                (
                    SELECT COUNT_BIG(*)
                    FROM dbo.Usuario_ServidoresAsignacion
                    WHERE UsuarioID = %s
                      AND ISNULL(Activo, 1) = 1
                ) AS server_assignment_count,
                (
                    SELECT COUNT_BIG(*)
                    FROM dbo.Usuario_SucursalesAsignacion
                    WHERE UsuarioID = %s
                      AND ISNULL(Activo, 1) = 1
                ) AS branch_assignment_count
        """, [usuario_id, usuario_id])

        if not row:
            return None

        return {
            "server_assignment_count": int(
                row.get("server_assignment_count") or 0
            ),
            "branch_assignment_count": int(
                row.get("branch_assignment_count") or 0
            ),
        }

    @staticmethod
    def can_access_unit_metadata(
        usuario_id,
        permission_code,
        metadata,
    ):
        """
        Combina permiso funcional y alcance explícito de unidad.

        Política:
        - sin permiso: denegar;
        - metadata incompleta o inactiva: denegar;
        - sin asignaciones:
          * permiso no restringido: permitir unidad canónica activa;
          * permiso restringido: denegar;
        - con cualquier asignación: limitar al alcance exacto;
        - servidor compartido: exigir servidor + sucursal exactos.
        """
        try:
            permission = (
                RBACSQLService.get_permission_scope_by_code(
                    usuario_id,
                    permission_code,
                )
            )

            if not permission:
                return False

            unit = dict(metadata or {})

            server_id = str(
                unit.get("server_id") or ""
            ).strip()

            branch_id = str(
                unit.get("sucursal_origen_id") or ""
            ).strip()

            unit_pk = str(
                unit.get("unidad_negocio_pk") or ""
            ).strip()

            unit_code = str(
                unit.get("unidad_negocio_codigo") or ""
            ).strip()

            if not server_id:
                return False

            if not unit_pk and not unit_code:
                return False

            if not bool(unit.get("unidad_activo")):
                return False

            if not bool(unit.get("servidor_activo")):
                return False

            try:
                active_units_on_server = int(
                    unit.get("active_units_on_server")
                )
            except (TypeError, ValueError):
                return False

            if active_units_on_server < 1:
                return False

            shared_server = active_units_on_server > 1

            if shared_server and not branch_id:
                return False

            assignment_state = (
                RBACSQLService.get_scope_assignment_state(
                    usuario_id
                )
            )

            if assignment_state is None:
                return False

            server_assignment_count = int(
                assignment_state.get(
                    "server_assignment_count",
                    0,
                )
            )

            branch_assignment_count = int(
                assignment_state.get(
                    "branch_assignment_count",
                    0,
                )
            )

            has_explicit_scope = (
                server_assignment_count > 0
                or branch_assignment_count > 0
            )

            if not has_explicit_scope:
                return not bool(
                    permission.get(
                        "restriccion_sucursal"
                    )
                )

            if shared_server:
                return RBACSQLService.can_access_sucursal(
                    usuario_id,
                    server_id,
                    branch_id,
                )

            if RBACSQLService.can_access_servidor(
                usuario_id,
                server_id,
            ):
                return True

            if branch_id and RBACSQLService.can_access_sucursal(
                usuario_id,
                server_id,
                branch_id,
            ):
                return True

            return False
        except Exception:
            return False
