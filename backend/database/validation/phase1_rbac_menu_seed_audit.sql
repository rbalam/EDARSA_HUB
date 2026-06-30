/*
Fase 1 RBAC/Menu seed audit.

Solo lectura. Ejecutar con:
python backend/tools/edarsahub_sql_runner.py --mode validate --script backend/database/validation/phase1_rbac_menu_seed_audit.sql

Objetivo:
- Confirmar que la semilla RBAC canonica existe en SQL.
- Ver usuarios activos, roles asignados, modulos, acciones y permisos efectivos.
- Detectar usuarios activos sin rol y roles activos sin permisos permitidos.
*/

SET NOCOUNT ON;
GO

SELECT
    'Usuario_Catalogo' AS tabla,
    COUNT(*) AS total,
    SUM(CASE WHEN Activo = 1 THEN 1 ELSE 0 END) AS activos
FROM dbo.Usuario_Catalogo;
GO

SELECT
    'Usuario_Roles' AS tabla,
    COUNT(*) AS total,
    SUM(CASE WHEN Activo = 1 THEN 1 ELSE 0 END) AS activos
FROM dbo.Usuario_Roles;
GO

SELECT
    'Usuario_Modulos' AS tabla,
    COUNT(*) AS total,
    SUM(CASE WHEN Activo = 1 THEN 1 ELSE 0 END) AS activos,
    SUM(CASE WHEN Activo = 1 AND EsVisibleMenu = 1 THEN 1 ELSE 0 END) AS visibles_menu
FROM dbo.Usuario_Modulos;
GO

SELECT
    'Usuario_Acciones' AS tabla,
    COUNT(*) AS total,
    SUM(CASE WHEN Activo = 1 THEN 1 ELSE 0 END) AS activos
FROM dbo.Usuario_Acciones;
GO

SELECT
    'Usuario_RolesAsignacion' AS tabla,
    COUNT(*) AS total,
    SUM(CASE WHEN Activo = 1 THEN 1 ELSE 0 END) AS activos
FROM dbo.Usuario_RolesAsignacion;
GO

SELECT
    'Usuario_PermisosRolModulo' AS tabla,
    COUNT(*) AS total,
    SUM(CASE WHEN Activo = 1 THEN 1 ELSE 0 END) AS activos,
    SUM(CASE WHEN Activo = 1 AND Permitido = 1 THEN 1 ELSE 0 END) AS permitidos_activos
FROM dbo.Usuario_PermisosRolModulo;
GO

SELECT
    r.RolID,
    r.CodigoRol,
    r.NombreRol,
    r.NivelJerarquia,
    r.Activo,
    COUNT(prm.PermisoRolModuloID) AS permisos_activos,
    COUNT(DISTINCT prm.ModuloID) AS modulos_con_permiso
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
    r.NivelJerarquia,
    r.Activo
ORDER BY
    r.NivelJerarquia DESC,
    r.CodigoRol;
GO

SELECT TOP (200)
    u.UsuarioID,
    u.Email,
    u.Username,
    u.NombreCompleto,
    u.Activo AS usuario_activo,
    r.CodigoRol,
    r.NombreRol,
    r.NivelJerarquia,
    ura.EsPrincipal,
    ura.Activo AS asignacion_activa,
    ura.FechaInicio,
    ura.FechaFin
FROM dbo.Usuario_Catalogo u
LEFT JOIN dbo.Usuario_RolesAsignacion ura
    ON ura.UsuarioID = u.UsuarioID
    AND ura.Activo = 1
LEFT JOIN dbo.Usuario_Roles r
    ON r.RolID = ura.RolID
WHERE u.Activo = 1
ORDER BY
    u.Email,
    ura.EsPrincipal DESC,
    r.NivelJerarquia DESC;
GO

SELECT TOP (300)
    r.CodigoRol,
    r.NombreRol,
    m.CodigoModulo,
    m.NombreModulo,
    m.Ruta,
    m.EsVisibleMenu,
    a.CodigoAccion,
    a.NombreAccion,
    prm.Permitido,
    prm.Activo,
    CONCAT(UPPER(m.CodigoModulo), '_', UPPER(a.CodigoAccion)) AS permiso_normalizado
FROM dbo.Usuario_PermisosRolModulo prm
INNER JOIN dbo.Usuario_Roles r
    ON r.RolID = prm.RolID
INNER JOIN dbo.Usuario_Modulos m
    ON m.ModuloID = prm.ModuloID
INNER JOIN dbo.Usuario_Acciones a
    ON a.AccionID = prm.AccionID
WHERE
    prm.Activo = 1
    AND prm.Permitido = 1
    AND r.Activo = 1
    AND m.Activo = 1
    AND a.Activo = 1
ORDER BY
    r.NivelJerarquia DESC,
    r.CodigoRol,
    m.OrdenMenu,
    m.CodigoModulo,
    a.CodigoAccion;
GO

SELECT
    u.UsuarioID,
    u.Email,
    u.Username,
    u.NombreCompleto,
    'USUARIO_ACTIVO_SIN_ROL_ACTIVO' AS hallazgo
FROM dbo.Usuario_Catalogo u
WHERE
    u.Activo = 1
    AND NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_RolesAsignacion ura
        INNER JOIN dbo.Usuario_Roles r
            ON r.RolID = ura.RolID
        WHERE
            ura.UsuarioID = u.UsuarioID
            AND ura.Activo = 1
            AND r.Activo = 1
    )
ORDER BY u.Email;
GO

SELECT
    r.RolID,
    r.CodigoRol,
    r.NombreRol,
    'ROL_ACTIVO_SIN_PERMISOS_PERMITIDOS' AS hallazgo
FROM dbo.Usuario_Roles r
WHERE
    r.Activo = 1
    AND NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo prm
        WHERE
            prm.RolID = r.RolID
            AND prm.Activo = 1
            AND prm.Permitido = 1
    )
ORDER BY r.CodigoRol;
GO
