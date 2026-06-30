/*
Fase 2 RBAC/Menu empty-role impact audit.

Solo lectura. Ejecutar con:
python backend/tools/edarsahub_sql_runner.py --mode validate --script backend/database/validation/phase2_rbac_empty_roles_impact_audit.sql

Objetivo:
- Medir impacto real de roles activos sin permisos permitidos.
- Separar roles vacios sin usuarios, roles vacios asignados como secundarios
  y usuarios cuyo acceso depende solo de roles vacios.
- Revisar que los roles destino del mapeo legacy tengan permisos.
*/

SET NOCOUNT ON;
GO

WITH RolePermissionCounts AS (
    SELECT
        r.RolID,
        r.CodigoRol,
        r.NombreRol,
        r.NivelJerarquia,
        r.Activo,
        COUNT(prm.PermisoRolModuloID) AS permisos_permitidos
    FROM dbo.Usuario_Roles r
    LEFT JOIN dbo.Usuario_PermisosRolModulo prm
        ON prm.RolID = r.RolID
        AND prm.Activo = 1
        AND prm.Permitido = 1
    LEFT JOIN dbo.Usuario_Modulos m
        ON m.ModuloID = prm.ModuloID
        AND m.Activo = 1
    LEFT JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
        AND a.Activo = 1
    WHERE r.Activo = 1
    GROUP BY
        r.RolID,
        r.CodigoRol,
        r.NombreRol,
        r.NivelJerarquia,
        r.Activo
)
SELECT
    RolID,
    CodigoRol,
    NombreRol,
    NivelJerarquia,
    permisos_permitidos
FROM RolePermissionCounts
WHERE permisos_permitidos = 0
ORDER BY
    NivelJerarquia DESC,
    CodigoRol;
GO

WITH RolePermissionCounts AS (
    SELECT
        r.RolID,
        r.CodigoRol,
        r.NombreRol,
        r.NivelJerarquia,
        COUNT(prm.PermisoRolModuloID) AS permisos_permitidos
    FROM dbo.Usuario_Roles r
    LEFT JOIN dbo.Usuario_PermisosRolModulo prm
        ON prm.RolID = r.RolID
        AND prm.Activo = 1
        AND prm.Permitido = 1
    WHERE r.Activo = 1
    GROUP BY
        r.RolID,
        r.CodigoRol,
        r.NombreRol,
        r.NivelJerarquia
),
EmptyRoles AS (
    SELECT *
    FROM RolePermissionCounts
    WHERE permisos_permitidos = 0
)
SELECT
    er.RolID,
    er.CodigoRol,
    er.NombreRol,
    er.NivelJerarquia,
    COUNT(DISTINCT u.UsuarioID) AS usuarios_activos_asignados,
    SUM(CASE WHEN ura.EsPrincipal = 1 THEN 1 ELSE 0 END) AS asignaciones_principales,
    COUNT(ura.UsuarioRolAsignacionID) AS asignaciones_activas
FROM EmptyRoles er
LEFT JOIN dbo.Usuario_RolesAsignacion ura
    ON ura.RolID = er.RolID
    AND ura.Activo = 1
LEFT JOIN dbo.Usuario_Catalogo u
    ON u.UsuarioID = ura.UsuarioID
    AND u.Activo = 1
GROUP BY
    er.RolID,
    er.CodigoRol,
    er.NombreRol,
    er.NivelJerarquia
ORDER BY
    usuarios_activos_asignados DESC,
    er.NivelJerarquia DESC,
    er.CodigoRol;
GO

WITH RolePermissionCounts AS (
    SELECT
        r.RolID,
        r.CodigoRol,
        r.NombreRol,
        r.NivelJerarquia,
        COUNT(prm.PermisoRolModuloID) AS permisos_permitidos
    FROM dbo.Usuario_Roles r
    LEFT JOIN dbo.Usuario_PermisosRolModulo prm
        ON prm.RolID = r.RolID
        AND prm.Activo = 1
        AND prm.Permitido = 1
    WHERE r.Activo = 1
    GROUP BY
        r.RolID,
        r.CodigoRol,
        r.NombreRol,
        r.NivelJerarquia
),
UserRoleImpact AS (
    SELECT
        u.UsuarioID,
        u.Email,
        u.Username,
        u.NombreCompleto,
        COUNT(rpc.RolID) AS roles_activos,
        SUM(CASE WHEN rpc.permisos_permitidos = 0 THEN 1 ELSE 0 END) AS roles_vacios,
        SUM(CASE WHEN rpc.permisos_permitidos > 0 THEN 1 ELSE 0 END) AS roles_con_permisos,
        SUM(rpc.permisos_permitidos) AS permisos_permitidos_acumulados
    FROM dbo.Usuario_Catalogo u
    INNER JOIN dbo.Usuario_RolesAsignacion ura
        ON ura.UsuarioID = u.UsuarioID
        AND ura.Activo = 1
    INNER JOIN RolePermissionCounts rpc
        ON rpc.RolID = ura.RolID
    WHERE u.Activo = 1
    GROUP BY
        u.UsuarioID,
        u.Email,
        u.Username,
        u.NombreCompleto
)
SELECT
    UsuarioID,
    Email,
    Username,
    NombreCompleto,
    roles_activos,
    roles_vacios,
    roles_con_permisos,
    permisos_permitidos_acumulados,
    CASE
        WHEN roles_activos = roles_vacios THEN 'CRITICO_SOLO_ROLES_VACIOS'
        WHEN roles_vacios > 0 THEN 'REVISAR_ROL_VACIO_SECUNDARIO'
        ELSE 'OK'
    END AS severidad_operativa
FROM UserRoleImpact
WHERE roles_vacios > 0
ORDER BY
    CASE WHEN roles_activos = roles_vacios THEN 0 ELSE 1 END,
    Email;
GO

WITH RolePermissionCounts AS (
    SELECT
        r.RolID,
        r.CodigoRol,
        r.NombreRol,
        r.NivelJerarquia,
        COUNT(prm.PermisoRolModuloID) AS permisos_permitidos
    FROM dbo.Usuario_Roles r
    LEFT JOIN dbo.Usuario_PermisosRolModulo prm
        ON prm.RolID = r.RolID
        AND prm.Activo = 1
        AND prm.Permitido = 1
    WHERE r.Activo = 1
    GROUP BY
        r.RolID,
        r.CodigoRol,
        r.NombreRol,
        r.NivelJerarquia
),
LegacyMap AS (
    SELECT *
    FROM (VALUES
        ('SuperAdministrador', 'SUPERADMIN'),
        ('Administrador', 'SUPERADMIN'),
        ('Supervisor', 'SUPERVISOR'),
        ('Usuario', 'OPERADOR'),
        ('Gerente', 'GERENTE_OPS'),
        ('Director', 'DIRECCION'),
        ('Auditor', 'AUDITOR'),
        ('Visor', 'OPERADOR')
    ) AS v(RolLegacy, CodigoRolDestino)
)
SELECT
    lm.RolLegacy,
    lm.CodigoRolDestino,
    rpc.RolID,
    rpc.NombreRol,
    rpc.NivelJerarquia,
    COALESCE(rpc.permisos_permitidos, 0) AS permisos_permitidos,
    CASE
        WHEN rpc.RolID IS NULL THEN 'CRITICO_ROL_DESTINO_NO_EXISTE'
        WHEN rpc.permisos_permitidos = 0 THEN 'CRITICO_ROL_DESTINO_SIN_PERMISOS'
        ELSE 'OK'
    END AS estado_mapeo_legacy
FROM LegacyMap lm
LEFT JOIN RolePermissionCounts rpc
    ON rpc.CodigoRol = lm.CodigoRolDestino
ORDER BY
    lm.RolLegacy;
GO

WITH RolePermissionCounts AS (
    SELECT
        r.RolID,
        r.CodigoRol,
        r.NombreRol,
        r.NivelJerarquia,
        COUNT(prm.PermisoRolModuloID) AS permisos_permitidos
    FROM dbo.Usuario_Roles r
    LEFT JOIN dbo.Usuario_PermisosRolModulo prm
        ON prm.RolID = r.RolID
        AND prm.Activo = 1
        AND prm.Permitido = 1
    WHERE r.Activo = 1
    GROUP BY
        r.RolID,
        r.CodigoRol,
        r.NombreRol,
        r.NivelJerarquia
),
EmptyRoleAssignments AS (
    SELECT
        rpc.RolID,
        rpc.CodigoRol,
        rpc.NombreRol,
        rpc.NivelJerarquia,
        u.UsuarioID,
        u.Email
    FROM RolePermissionCounts rpc
    LEFT JOIN dbo.Usuario_RolesAsignacion ura
        ON ura.RolID = rpc.RolID
        AND ura.Activo = 1
    LEFT JOIN dbo.Usuario_Catalogo u
        ON u.UsuarioID = ura.UsuarioID
        AND u.Activo = 1
    WHERE rpc.permisos_permitidos = 0
),
UserRoleImpact AS (
    SELECT
        u.UsuarioID,
        COUNT(rpc.RolID) AS roles_activos,
        SUM(CASE WHEN rpc.permisos_permitidos = 0 THEN 1 ELSE 0 END) AS roles_vacios
    FROM dbo.Usuario_Catalogo u
    INNER JOIN dbo.Usuario_RolesAsignacion ura
        ON ura.UsuarioID = u.UsuarioID
        AND ura.Activo = 1
    INNER JOIN RolePermissionCounts rpc
        ON rpc.RolID = ura.RolID
    WHERE u.Activo = 1
    GROUP BY u.UsuarioID
)
SELECT
    era.RolID,
    era.CodigoRol,
    era.NombreRol,
    era.NivelJerarquia,
    COUNT(DISTINCT era.UsuarioID) AS usuarios_activos_asignados,
    SUM(CASE WHEN uri.roles_activos = uri.roles_vacios THEN 1 ELSE 0 END) AS usuarios_solo_con_roles_vacios,
    CASE
        WHEN SUM(CASE WHEN uri.roles_activos = uri.roles_vacios THEN 1 ELSE 0 END) > 0 THEN 'CRITICO_AFECTA_USUARIO'
        WHEN COUNT(DISTINCT era.UsuarioID) > 0 THEN 'REVISAR_ASIGNADO_SECUNDARIO'
        ELSE 'BAJO_SIN_USUARIOS_ACTIVOS'
    END AS recomendacion
FROM EmptyRoleAssignments era
LEFT JOIN UserRoleImpact uri
    ON uri.UsuarioID = era.UsuarioID
GROUP BY
    era.RolID,
    era.CodigoRol,
    era.NombreRol,
    era.NivelJerarquia
ORDER BY
    CASE
        WHEN SUM(CASE WHEN uri.roles_activos = uri.roles_vacios THEN 1 ELSE 0 END) > 0 THEN 0
        WHEN COUNT(DISTINCT era.UsuarioID) > 0 THEN 1
        ELSE 2
    END,
    era.NivelJerarquia DESC,
    era.CodigoRol;
GO
