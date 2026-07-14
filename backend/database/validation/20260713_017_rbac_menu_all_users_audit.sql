SET NOCOUNT ON;

IF DB_NAME() <> N'EDARSAHUB'
   OR SUSER_SNAME() <> N'HRLectura'
   OR USER_NAME() <> N'HRLectura'
BEGIN
    THROW 51000, 'Contexto SQL invalido. Se requiere EDARSAHUB / HRLectura / HRLectura.', 1;
END;

SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    USER_NAME() AS database_user,
    SYSUTCDATETIME() AS audited_at_utc;
GO

WITH global_roles AS (
    SELECT
        u.UsuarioID,
        COUNT(DISTINCT CASE
            WHEN ISNULL(ura.Activo, 1) = 1 AND ISNULL(r.Activo, 1) = 1
            THEN ura.RolID
        END) AS roles_globales_activos,
        COUNT(DISTINCT CASE
            WHEN ISNULL(ura.Activo, 1) = 1
             AND ISNULL(r.Activo, 1) = 1
             AND ISNULL(ura.EsPrincipal, 0) = 1
            THEN ura.RolID
        END) AS roles_principales_activos,
        MAX(CASE
            WHEN ISNULL(ura.Activo, 1) = 1 AND ISNULL(r.Activo, 1) = 1
            THEN ISNULL(r.NivelJerarquia, 0)
            ELSE 0
        END) AS nivel_global_max,
        MAX(CASE
            WHEN ISNULL(ura.Activo, 1) = 1
             AND ISNULL(r.Activo, 1) = 1
             AND (
                    UPPER(LTRIM(RTRIM(ISNULL(r.CodigoRol, '')))) IN ('SUPERADMIN', 'ADMIN')
                 OR UPPER(LTRIM(RTRIM(ISNULL(r.NombreRol, '')))) IN ('SUPERADMINISTRADOR', 'ADMINISTRADOR')
                 OR ISNULL(r.NivelJerarquia, 0) >= 90
             )
            THEN 1 ELSE 0
        END) AS bypass_global
    FROM dbo.Usuario_Catalogo u
    LEFT JOIN dbo.Usuario_RolesAsignacion ura
        ON ura.UsuarioID = u.UsuarioID
    LEFT JOIN dbo.Usuario_Roles r
        ON r.RolID = ura.RolID
    GROUP BY u.UsuarioID
),
context_roles AS (
    SELECT
        u.UsuarioID,
        COUNT(DISTINCT CASE
            WHEN ISNULL(urc.Activo, 1) = 1 AND ISNULL(r.Activo, 1) = 1
            THEN urc.RolID
        END) AS roles_contexto_activos,
        COUNT(DISTINCT CASE
            WHEN ISNULL(urc.Activo, 1) = 1
             AND ISNULL(r.Activo, 1) = 1
             AND urc.UnidadNegocioID IS NOT NULL
            THEN CONVERT(NVARCHAR(100), urc.UnidadNegocioID)
        END) AS unidades_contexto_activas,
        SUM(CASE
            WHEN ISNULL(urc.Activo, 1) = 1
             AND ISNULL(r.Activo, 1) = 1
             AND urc.UnidadNegocioID IS NULL
            THEN 1 ELSE 0
        END) AS contextos_sin_unidad,
        MAX(CASE
            WHEN ISNULL(urc.Activo, 1) = 1 AND ISNULL(r.Activo, 1) = 1
            THEN ISNULL(r.NivelJerarquia, 0)
            ELSE 0
        END) AS nivel_contexto_max,
        MAX(CASE
            WHEN ISNULL(urc.Activo, 1) = 1
             AND ISNULL(r.Activo, 1) = 1
             AND (
                    UPPER(LTRIM(RTRIM(ISNULL(r.CodigoRol, '')))) IN ('SUPERADMIN', 'ADMIN')
                 OR UPPER(LTRIM(RTRIM(ISNULL(r.NombreRol, '')))) IN ('SUPERADMINISTRADOR', 'ADMINISTRADOR')
                 OR ISNULL(r.NivelJerarquia, 0) >= 90
             )
            THEN 1 ELSE 0
        END) AS bypass_contexto
    FROM dbo.Usuario_Catalogo u
    LEFT JOIN dbo.Usuario_RolesContexto urc
        ON urc.UsuarioID = u.UsuarioID
    LEFT JOIN dbo.Usuario_Roles r
        ON r.RolID = urc.RolID
    GROUP BY u.UsuarioID
),
global_permissions AS (
    SELECT DISTINCT
        ura.UsuarioID,
        prm.PermisoRolModuloID,
        UPPER(REPLACE(REPLACE(
            LTRIM(RTRIM(CONVERT(NVARCHAR(255), m.CodigoModulo))),
            '-', '_'), ' ', '_')) AS permiso_clave
    FROM dbo.Usuario_RolesAsignacion ura
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = ura.RolID
       AND ISNULL(r.Activo, 1) = 1
    INNER JOIN dbo.Usuario_PermisosRolModulo prm
        ON prm.RolID = ura.RolID
       AND ISNULL(prm.Activo, 1) = 1
       AND ISNULL(prm.Permitido, 1) = 1
    INNER JOIN dbo.Usuario_Modulos m
        ON m.ModuloID = prm.ModuloID
       AND ISNULL(m.Activo, 1) = 1
    INNER JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
       AND ISNULL(a.Activo, 1) = 1
    WHERE ISNULL(ura.Activo, 1) = 1
),
context_permissions AS (
    SELECT DISTINCT
        urc.UsuarioID,
        CONVERT(NVARCHAR(100), urc.UnidadNegocioID) AS UnidadNegocioID,
        prm.PermisoRolModuloID,
        UPPER(REPLACE(REPLACE(
            LTRIM(RTRIM(CONVERT(NVARCHAR(255), m.CodigoModulo))),
            '-', '_'), ' ', '_')) AS permiso_clave
    FROM dbo.Usuario_RolesContexto urc
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = urc.RolID
       AND ISNULL(r.Activo, 1) = 1
    INNER JOIN dbo.Usuario_PermisosRolModulo prm
        ON prm.RolID = urc.RolID
       AND ISNULL(prm.Activo, 1) = 1
       AND ISNULL(prm.Permitido, 1) = 1
    INNER JOIN dbo.Usuario_Modulos m
        ON m.ModuloID = prm.ModuloID
       AND ISNULL(m.Activo, 1) = 1
    INNER JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
       AND ISNULL(a.Activo, 1) = 1
    WHERE ISNULL(urc.Activo, 1) = 1
),
menu_candidates AS (
    SELECT DISTINCT
        smm.MenuID,
        v.permiso_clave
    FROM dbo.Sistema_ModulosMenus smm
    CROSS APPLY (VALUES
        (UPPER(REPLACE(REPLACE(
            LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.RequierePermiso))),
            '-', '_'), ' ', '_'))),
        (UPPER(REPLACE(REPLACE(
            LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.Codigo))),
            '-', '_'), ' ', '_'))),
        (UPPER(REPLACE(REPLACE(REPLACE(
            CASE
                WHEN LEFT(LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.Ruta))), 1) = '/'
                THEN SUBSTRING(LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.Ruta))), 2, 300)
                ELSE LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.Ruta)))
            END,
            '/', '.'), '-', '_'), ' ', '_')))
    ) v(permiso_clave)
    WHERE ISNULL(smm.Activo, 1) = 1
      AND NULLIF(v.permiso_clave, '') IS NOT NULL
),
global_permission_counts AS (
    SELECT UsuarioID, COUNT(DISTINCT PermisoRolModuloID) AS permisos_globales
    FROM global_permissions
    GROUP BY UsuarioID
),
context_permission_counts AS (
    SELECT UsuarioID, COUNT(DISTINCT PermisoRolModuloID) AS permisos_contexto
    FROM context_permissions
    GROUP BY UsuarioID
),
global_menu_counts AS (
    SELECT x.UsuarioID, COUNT(*) AS menus_globales_directos
    FROM (
        SELECT DISTINCT gp.UsuarioID, mc.MenuID
        FROM global_permissions gp
        INNER JOIN menu_candidates mc
            ON mc.permiso_clave = gp.permiso_clave
    ) x
    GROUP BY x.UsuarioID
),
context_menu_counts AS (
    SELECT x.UsuarioID, COUNT(*) AS menus_contexto_directos
    FROM (
        SELECT DISTINCT cp.UsuarioID, cp.UnidadNegocioID, mc.MenuID
        FROM context_permissions cp
        INNER JOIN menu_candidates mc
            ON mc.permiso_clave = cp.permiso_clave
    ) x
    GROUP BY x.UsuarioID
),
scope_counts AS (
    SELECT
        u.UsuarioID,
        (SELECT COUNT(DISTINCT CONVERT(NVARCHAR(100), usa.ServidorID))
         FROM dbo.Usuario_ServidoresAsignacion usa
         WHERE usa.UsuarioID = u.UsuarioID AND ISNULL(usa.Activo, 1) = 1) AS servidores_activos,
        (SELECT COUNT(*)
         FROM dbo.Usuario_SucursalesAsignacion usa
         WHERE usa.UsuarioID = u.UsuarioID AND ISNULL(usa.Activo, 1) = 1) AS sucursales_activas,
        (SELECT COUNT(*)
         FROM dbo.Usuario_AlmacenesAsignacion uaa
         WHERE uaa.UsuarioID = u.UsuarioID AND ISNULL(uaa.Activo, 1) = 1) AS almacenes_activos
    FROM dbo.Usuario_Catalogo u
)
SELECT
    u.UsuarioID,
    u.Email,
    u.Username,
    u.NombreCompleto,
    ISNULL(u.Activo, 1) AS usuario_activo,
    ISNULL(gr.roles_globales_activos, 0) AS roles_globales_activos,
    ISNULL(gr.roles_principales_activos, 0) AS roles_principales_activos,
    ISNULL(gr.nivel_global_max, 0) AS nivel_global_max,
    ISNULL(cr.roles_contexto_activos, 0) AS roles_contexto_activos,
    ISNULL(cr.unidades_contexto_activas, 0) AS unidades_contexto_activas,
    ISNULL(cr.contextos_sin_unidad, 0) AS contextos_sin_unidad,
    ISNULL(cr.nivel_contexto_max, 0) AS nivel_contexto_max,
    ISNULL(gpc.permisos_globales, 0) AS permisos_globales,
    ISNULL(cpc.permisos_contexto, 0) AS permisos_contexto,
    ISNULL(gmc.menus_globales_directos, 0) AS menus_globales_directos,
    ISNULL(cmc.menus_contexto_directos, 0) AS menus_contexto_directos,
    ISNULL(sc.servidores_activos, 0) AS servidores_activos,
    ISNULL(sc.sucursales_activas, 0) AS sucursales_activas,
    ISNULL(sc.almacenes_activos, 0) AS almacenes_activos,
    CASE
        WHEN ISNULL(u.Activo, 1) <> 1 THEN 'SKIP_INACTIVO'
        WHEN ISNULL(gr.roles_globales_activos, 0) = 0
         AND ISNULL(cr.roles_contexto_activos, 0) = 0 THEN 'ERROR_SIN_ROL'
        WHEN ISNULL(gr.roles_principales_activos, 0) <> 1 THEN 'ERROR_ROL_PRINCIPAL_INVALIDO'
        WHEN ISNULL(gr.roles_globales_activos, 0) > 0
         AND ISNULL(cr.roles_contexto_activos, 0) = 0 THEN 'ERROR_GLOBAL_SIN_CONTEXTO'
        WHEN ISNULL(gr.roles_globales_activos, 0) = 0
         AND ISNULL(cr.roles_contexto_activos, 0) > 0 THEN 'ERROR_CONTEXTO_SIN_GLOBAL'
        WHEN ISNULL(gr.bypass_global, 0) <> ISNULL(cr.bypass_contexto, 0)
            THEN 'ERROR_BYPASS_DIVERGENTE'
        WHEN ISNULL(gr.bypass_global, 0) = 0
         AND ISNULL(gpc.permisos_globales, 0) = 0 THEN 'ERROR_SIN_PERMISOS_GLOBALES'
        WHEN ISNULL(cr.bypass_contexto, 0) = 0
         AND ISNULL(cr.roles_contexto_activos, 0) > 0
         AND ISNULL(cpc.permisos_contexto, 0) = 0 THEN 'ERROR_SIN_PERMISOS_CONTEXTO'
        WHEN ISNULL(gr.bypass_global, 0) = 0
         AND ISNULL(sc.servidores_activos, 0) > 0
         AND ISNULL(cr.unidades_contexto_activas, 0) = 0 THEN 'ERROR_ALCANCE_SIN_ROL_POR_UNIDAD'
        WHEN ISNULL(gr.bypass_global, 0) = 0
         AND ISNULL(gmc.menus_globales_directos, 0) = 0 THEN 'ERROR_SIN_MENU_GLOBAL'
        WHEN ISNULL(cr.bypass_contexto, 0) = 0
         AND ISNULL(cr.roles_contexto_activos, 0) > 0
         AND ISNULL(cmc.menus_contexto_directos, 0) = 0 THEN 'ERROR_SIN_MENU_CONTEXTO'
        WHEN ISNULL(gr.bypass_global, 0) = 0
         AND ISNULL(sc.servidores_activos, 0) = 0 THEN 'WARN_SIN_ALCANCE_OPERATIVO'
        ELSE 'OK'
    END AS estado_auditoria
FROM dbo.Usuario_Catalogo u
LEFT JOIN global_roles gr ON gr.UsuarioID = u.UsuarioID
LEFT JOIN context_roles cr ON cr.UsuarioID = u.UsuarioID
LEFT JOIN global_permission_counts gpc ON gpc.UsuarioID = u.UsuarioID
LEFT JOIN context_permission_counts cpc ON cpc.UsuarioID = u.UsuarioID
LEFT JOIN global_menu_counts gmc ON gmc.UsuarioID = u.UsuarioID
LEFT JOIN context_menu_counts cmc ON cmc.UsuarioID = u.UsuarioID
LEFT JOIN scope_counts sc ON sc.UsuarioID = u.UsuarioID
ORDER BY
    CASE
        WHEN ISNULL(u.Activo, 1) = 1 THEN 0 ELSE 1
    END,
    estado_auditoria,
    u.NombreCompleto,
    u.Email;
GO

WITH targets AS (
    SELECT
        u.UsuarioID,
        u.Email,
        u.Username,
        u.NombreCompleto,
        u.Activo
    FROM dbo.Usuario_Catalogo u
    WHERE CONCAT(
        ISNULL(u.NombreCompleto, ''), ' ',
        ISNULL(u.Email, ''), ' ',
        ISNULL(u.Username, '')
    ) COLLATE Latin1_General_100_CI_AI LIKE '%DAVID%RICALD%'
       OR CONCAT(
        ISNULL(u.NombreCompleto, ''), ' ',
        ISNULL(u.Email, ''), ' ',
        ISNULL(u.Username, '')
    ) COLLATE Latin1_General_100_CI_AI LIKE '%CARLOS%RUZ%'
)
SELECT
    t.UsuarioID,
    t.Email,
    t.Username,
    t.NombreCompleto,
    t.Activo AS usuario_activo,
    'GLOBAL' AS fuente_rol,
    r.RolID,
    r.CodigoRol,
    r.NombreRol,
    r.NivelJerarquia,
    ura.EsPrincipal,
    ura.Activo AS asignacion_activa,
    CAST(NULL AS NVARCHAR(100)) AS unidad_negocio_id,
    CAST(NULL AS NVARCHAR(255)) AS unidad_negocio_nombre
FROM targets t
LEFT JOIN dbo.Usuario_RolesAsignacion ura
    ON ura.UsuarioID = t.UsuarioID
LEFT JOIN dbo.Usuario_Roles r
    ON r.RolID = ura.RolID

UNION ALL

SELECT
    t.UsuarioID,
    t.Email,
    t.Username,
    t.NombreCompleto,
    t.Activo AS usuario_activo,
    'CONTEXTO' AS fuente_rol,
    r.RolID,
    r.CodigoRol,
    r.NombreRol,
    r.NivelJerarquia,
    urc.EsRolPrimario AS EsPrincipal,
    urc.Activo AS asignacion_activa,
    CONVERT(NVARCHAR(100), urc.UnidadNegocioID) AS unidad_negocio_id,
    un.nombre AS unidad_negocio_nombre
FROM targets t
LEFT JOIN dbo.Usuario_RolesContexto urc
    ON urc.UsuarioID = t.UsuarioID
LEFT JOIN dbo.Usuario_Roles r
    ON r.RolID = urc.RolID
LEFT JOIN dbo.Unidades_Negocio un
    ON un.id = urc.UnidadNegocioID
ORDER BY UsuarioID, fuente_rol, unidad_negocio_nombre, NivelJerarquia DESC;
GO

WITH targets AS (
    SELECT
        u.UsuarioID,
        u.Email,
        u.NombreCompleto
    FROM dbo.Usuario_Catalogo u
    WHERE CONCAT(
        ISNULL(u.NombreCompleto, ''), ' ',
        ISNULL(u.Email, ''), ' ',
        ISNULL(u.Username, '')
    ) COLLATE Latin1_General_100_CI_AI LIKE '%DAVID%RICALD%'
       OR CONCAT(
        ISNULL(u.NombreCompleto, ''), ' ',
        ISNULL(u.Email, ''), ' ',
        ISNULL(u.Username, '')
    ) COLLATE Latin1_General_100_CI_AI LIKE '%CARLOS%RUZ%'
),
menu_candidates AS (
    SELECT DISTINCT
        smm.MenuID,
        smm.Codigo AS menu_codigo,
        smm.Nombre AS menu_nombre,
        smm.Ruta AS menu_ruta,
        v.permiso_clave
    FROM dbo.Sistema_ModulosMenus smm
    CROSS APPLY (VALUES
        (UPPER(REPLACE(REPLACE(LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.RequierePermiso))), '-', '_'), ' ', '_'))),
        (UPPER(REPLACE(REPLACE(LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.Codigo))), '-', '_'), ' ', '_'))),
        (UPPER(REPLACE(REPLACE(REPLACE(
            CASE
                WHEN LEFT(LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.Ruta))), 1) = '/'
                THEN SUBSTRING(LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.Ruta))), 2, 300)
                ELSE LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.Ruta)))
            END,
            '/', '.'), '-', '_'), ' ', '_')))
    ) v(permiso_clave)
    WHERE ISNULL(smm.Activo, 1) = 1
      AND NULLIF(v.permiso_clave, '') IS NOT NULL
),
permisos AS (
    SELECT
        t.UsuarioID,
        t.Email,
        t.NombreCompleto,
        'GLOBAL' AS fuente_permiso,
        CAST(NULL AS NVARCHAR(100)) AS unidad_negocio_id,
        CAST(NULL AS NVARCHAR(255)) AS unidad_negocio_nombre,
        r.CodigoRol,
        r.NombreRol,
        m.ModuloID,
        m.CodigoModulo,
        m.NombreModulo,
        a.CodigoAccion,
        a.NombreAccion,
        UPPER(REPLACE(REPLACE(LTRIM(RTRIM(CONVERT(NVARCHAR(255), m.CodigoModulo))), '-', '_'), ' ', '_')) AS permiso_clave
    FROM targets t
    INNER JOIN dbo.Usuario_RolesAsignacion ura
        ON ura.UsuarioID = t.UsuarioID
       AND ISNULL(ura.Activo, 1) = 1
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = ura.RolID
       AND ISNULL(r.Activo, 1) = 1
    INNER JOIN dbo.Usuario_PermisosRolModulo prm
        ON prm.RolID = ura.RolID
       AND ISNULL(prm.Activo, 1) = 1
       AND ISNULL(prm.Permitido, 1) = 1
    INNER JOIN dbo.Usuario_Modulos m
        ON m.ModuloID = prm.ModuloID
       AND ISNULL(m.Activo, 1) = 1
    INNER JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
       AND ISNULL(a.Activo, 1) = 1

    UNION ALL

    SELECT
        t.UsuarioID,
        t.Email,
        t.NombreCompleto,
        'CONTEXTO' AS fuente_permiso,
        CONVERT(NVARCHAR(100), urc.UnidadNegocioID) AS unidad_negocio_id,
        un.nombre AS unidad_negocio_nombre,
        r.CodigoRol,
        r.NombreRol,
        m.ModuloID,
        m.CodigoModulo,
        m.NombreModulo,
        a.CodigoAccion,
        a.NombreAccion,
        UPPER(REPLACE(REPLACE(LTRIM(RTRIM(CONVERT(NVARCHAR(255), m.CodigoModulo))), '-', '_'), ' ', '_')) AS permiso_clave
    FROM targets t
    INNER JOIN dbo.Usuario_RolesContexto urc
        ON urc.UsuarioID = t.UsuarioID
       AND ISNULL(urc.Activo, 1) = 1
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = urc.RolID
       AND ISNULL(r.Activo, 1) = 1
    INNER JOIN dbo.Usuario_PermisosRolModulo prm
        ON prm.RolID = urc.RolID
       AND ISNULL(prm.Activo, 1) = 1
       AND ISNULL(prm.Permitido, 1) = 1
    INNER JOIN dbo.Usuario_Modulos m
        ON m.ModuloID = prm.ModuloID
       AND ISNULL(m.Activo, 1) = 1
    INNER JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
       AND ISNULL(a.Activo, 1) = 1
    LEFT JOIN dbo.Unidades_Negocio un
        ON un.id = urc.UnidadNegocioID
)
SELECT
    p.UsuarioID,
    p.Email,
    p.NombreCompleto,
    p.fuente_permiso,
    p.unidad_negocio_id,
    p.unidad_negocio_nombre,
    p.CodigoRol,
    p.NombreRol,
    p.ModuloID,
    p.CodigoModulo,
    p.NombreModulo,
    p.CodigoAccion,
    p.NombreAccion,
    COUNT(DISTINCT mc.MenuID) AS menus_coincidentes,
    MIN(mc.menu_codigo) AS ejemplo_menu_codigo,
    MIN(mc.menu_nombre) AS ejemplo_menu_nombre,
    MIN(mc.menu_ruta) AS ejemplo_menu_ruta
FROM permisos p
LEFT JOIN menu_candidates mc
    ON mc.permiso_clave = p.permiso_clave
GROUP BY
    p.UsuarioID,
    p.Email,
    p.NombreCompleto,
    p.fuente_permiso,
    p.unidad_negocio_id,
    p.unidad_negocio_nombre,
    p.CodigoRol,
    p.NombreRol,
    p.ModuloID,
    p.CodigoModulo,
    p.NombreModulo,
    p.CodigoAccion,
    p.NombreAccion
HAVING COUNT(DISTINCT mc.MenuID) = 0
ORDER BY
    p.UsuarioID,
    p.fuente_permiso,
    p.unidad_negocio_nombre,
    p.CodigoModulo,
    p.CodigoAccion;
GO

SELECT
    u.UsuarioID,
    u.Email,
    u.NombreCompleto,
    r.RolID,
    r.CodigoRol,
    r.NombreRol,
    'GLOBAL_SIN_CONTEXTO' AS hallazgo
FROM dbo.Usuario_Catalogo u
INNER JOIN dbo.Usuario_RolesAsignacion ura
    ON ura.UsuarioID = u.UsuarioID
   AND ISNULL(ura.Activo, 1) = 1
INNER JOIN dbo.Usuario_Roles r
    ON r.RolID = ura.RolID
   AND ISNULL(r.Activo, 1) = 1
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.Usuario_RolesContexto urc
    WHERE urc.UsuarioID = ura.UsuarioID
      AND urc.RolID = ura.RolID
      AND ISNULL(urc.Activo, 1) = 1
)

UNION ALL

SELECT
    u.UsuarioID,
    u.Email,
    u.NombreCompleto,
    r.RolID,
    r.CodigoRol,
    r.NombreRol,
    'CONTEXTO_SIN_GLOBAL' AS hallazgo
FROM dbo.Usuario_Catalogo u
INNER JOIN dbo.Usuario_RolesContexto urc
    ON urc.UsuarioID = u.UsuarioID
   AND ISNULL(urc.Activo, 1) = 1
INNER JOIN dbo.Usuario_Roles r
    ON r.RolID = urc.RolID
   AND ISNULL(r.Activo, 1) = 1
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.Usuario_RolesAsignacion ura
    WHERE ura.UsuarioID = urc.UsuarioID
      AND ura.RolID = urc.RolID
      AND ISNULL(ura.Activo, 1) = 1
)
ORDER BY UsuarioID, hallazgo, CodigoRol;
GO

WITH scope_units AS (
    SELECT DISTINCT
        usa.UsuarioID,
        un.id AS UnidadNegocioID,
        un.nombre AS UnidadNegocioNombre
    FROM dbo.Usuario_ServidoresAsignacion usa
    INNER JOIN dbo.Unidades_Negocio un
        ON un.server_id = usa.ServidorID
    WHERE ISNULL(usa.Activo, 1) = 1
),
context_units AS (
    SELECT DISTINCT
        urc.UsuarioID,
        urc.UnidadNegocioID,
        un.nombre AS UnidadNegocioNombre
    FROM dbo.Usuario_RolesContexto urc
    LEFT JOIN dbo.Unidades_Negocio un
        ON un.id = urc.UnidadNegocioID
    WHERE ISNULL(urc.Activo, 1) = 1
      AND urc.UnidadNegocioID IS NOT NULL
)
SELECT
    u.UsuarioID,
    u.Email,
    u.NombreCompleto,
    CONVERT(NVARCHAR(100), su.UnidadNegocioID) AS unidad_negocio_id,
    su.UnidadNegocioNombre AS unidad_negocio_nombre,
    'ALCANCE_SIN_ROL_CONTEXTO' AS hallazgo
FROM scope_units su
INNER JOIN dbo.Usuario_Catalogo u
    ON u.UsuarioID = su.UsuarioID
WHERE NOT EXISTS (
    SELECT 1
    FROM context_units cu
    WHERE cu.UsuarioID = su.UsuarioID
      AND cu.UnidadNegocioID = su.UnidadNegocioID
)

UNION ALL

SELECT
    u.UsuarioID,
    u.Email,
    u.NombreCompleto,
    CONVERT(NVARCHAR(100), cu.UnidadNegocioID) AS unidad_negocio_id,
    cu.UnidadNegocioNombre AS unidad_negocio_nombre,
    'ROL_CONTEXTO_SIN_ALCANCE' AS hallazgo
FROM context_units cu
INNER JOIN dbo.Usuario_Catalogo u
    ON u.UsuarioID = cu.UsuarioID
WHERE NOT EXISTS (
    SELECT 1
    FROM scope_units su
    WHERE su.UsuarioID = cu.UsuarioID
      AND su.UnidadNegocioID = cu.UnidadNegocioID
)
ORDER BY UsuarioID, hallazgo, unidad_negocio_nombre;
GO

SELECT
    COALESCE(um.ModuloID, sm.ModuloID) AS ModuloID,
    um.CodigoModulo AS usuario_modulo_codigo,
    um.NombreModulo AS usuario_modulo_nombre,
    um.Activo AS usuario_modulo_activo,
    sm.Codigo AS sistema_modulo_codigo,
    sm.Nombre AS sistema_modulo_nombre,
    sm.Activo AS sistema_modulo_activo,
    CASE
        WHEN um.ModuloID IS NULL THEN 'ERROR_FALTA_USUARIO_MODULO'
        WHEN sm.ModuloID IS NULL THEN 'ERROR_FALTA_SISTEMA_MODULO'
        WHEN UPPER(REPLACE(REPLACE(LTRIM(RTRIM(ISNULL(um.CodigoModulo, ''))), '-', '_'), ' ', '_'))
          <> UPPER(REPLACE(REPLACE(LTRIM(RTRIM(ISNULL(sm.Codigo, ''))), '-', '_'), ' ', '_'))
            THEN 'ERROR_CODIGO_DIVERGENTE'
        ELSE 'OK'
    END AS hallazgo
FROM dbo.Usuario_Modulos um
FULL OUTER JOIN dbo.Sistema_Modulos sm
    ON sm.ModuloID = um.ModuloID
WHERE um.ModuloID IS NULL
   OR sm.ModuloID IS NULL
   OR UPPER(REPLACE(REPLACE(LTRIM(RTRIM(ISNULL(um.CodigoModulo, ''))), '-', '_'), ' ', '_'))
     <> UPPER(REPLACE(REPLACE(LTRIM(RTRIM(ISNULL(sm.Codigo, ''))), '-', '_'), ' ', '_'))
ORDER BY ModuloID;
GO

WITH menu_candidates AS (
    SELECT DISTINCT
        sm.ModuloID AS sistema_modulo_id,
        sm.Codigo AS sistema_modulo_codigo,
        sm.Nombre AS sistema_modulo_nombre,
        smm.MenuID,
        smm.Codigo AS menu_codigo,
        smm.Nombre AS menu_nombre,
        smm.Ruta,
        smm.RequierePermiso,
        v.origen_clave,
        v.permiso_clave
    FROM dbo.Sistema_Modulos sm
    INNER JOIN dbo.Sistema_ModulosMenus smm
        ON smm.ModuloID = sm.ModuloID
    CROSS APPLY (VALUES
        ('REQUIERE_PERMISO', UPPER(REPLACE(REPLACE(LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.RequierePermiso))), '-', '_'), ' ', '_'))),
        ('CODIGO_MENU', UPPER(REPLACE(REPLACE(LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.Codigo))), '-', '_'), ' ', '_'))),
        ('RUTA_MENU', UPPER(REPLACE(REPLACE(REPLACE(
            CASE
                WHEN LEFT(LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.Ruta))), 1) = '/'
                THEN SUBSTRING(LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.Ruta))), 2, 300)
                ELSE LTRIM(RTRIM(CONVERT(NVARCHAR(300), smm.Ruta)))
            END,
            '/', '.'), '-', '_'), ' ', '_')))
    ) v(origen_clave, permiso_clave)
    WHERE ISNULL(sm.Activo, 1) = 1
      AND ISNULL(smm.Activo, 1) = 1
      AND NULLIF(v.permiso_clave, '') IS NOT NULL
)
SELECT
    mc.sistema_modulo_id,
    mc.sistema_modulo_codigo,
    mc.sistema_modulo_nombre,
    mc.MenuID,
    mc.menu_codigo,
    mc.menu_nombre,
    mc.Ruta,
    mc.RequierePermiso,
    mc.origen_clave,
    mc.permiso_clave,
    'ERROR_MENU_SIN_USUARIO_MODULO' AS hallazgo
FROM menu_candidates mc
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.Usuario_Modulos um
    WHERE ISNULL(um.Activo, 1) = 1
      AND UPPER(REPLACE(REPLACE(LTRIM(RTRIM(CONVERT(NVARCHAR(300), um.CodigoModulo))), '-', '_'), ' ', '_'))
          = mc.permiso_clave
)
ORDER BY mc.sistema_modulo_nombre, mc.menu_nombre, mc.origen_clave;
GO

IF OBJECT_ID('dbo.Usuario_LogRBACVerificacion', 'U') IS NULL
BEGIN
    SELECT
        'INFO_SIN_TABLA_LOG_RBAC' AS estado,
        CAST(NULL AS INT) AS UsuarioID,
        CAST(NULL AS NVARCHAR(255)) AS Email,
        CAST(NULL AS NVARCHAR(255)) AS NombreCompleto,
        CAST(NULL AS NVARCHAR(255)) AS PermisoRequerido,
        CAST(NULL AS NVARCHAR(20)) AS Resultado,
        CAST(NULL AS NVARCHAR(255)) AS Endpoint,
        CAST(NULL AS DATETIME2) AS FechaVerificacion;
END
ELSE
BEGIN
    ;WITH targets AS (
        SELECT
            u.UsuarioID,
            u.Email,
            u.NombreCompleto,
            CONVERT(NVARCHAR(36), u.PublicUUID) AS PublicUUID
        FROM dbo.Usuario_Catalogo u
        WHERE CONCAT(
            ISNULL(u.NombreCompleto, ''), ' ',
            ISNULL(u.Email, ''), ' ',
            ISNULL(u.Username, '')
        ) COLLATE Latin1_General_100_CI_AI LIKE '%DAVID%RICALD%'
           OR CONCAT(
            ISNULL(u.NombreCompleto, ''), ' ',
            ISNULL(u.Email, ''), ' ',
            ISNULL(u.Username, '')
        ) COLLATE Latin1_General_100_CI_AI LIKE '%CARLOS%RUZ%'
    )
    SELECT TOP (200)
        'LOG_RBAC' AS estado,
        t.UsuarioID,
        t.Email,
        t.NombreCompleto,
        l.PermisoRequerido,
        l.Resultado,
        l.Endpoint,
        l.FechaVerificacion
    FROM dbo.Usuario_LogRBACVerificacion l
    INNER JOIN targets t
        ON t.UsuarioID = l.UsuarioID
        OR t.PublicUUID = CONVERT(NVARCHAR(36), l.PublicUUID)
    WHERE UPPER(LTRIM(RTRIM(ISNULL(l.Resultado, '')))) = 'DENEGADO'
    ORDER BY l.FechaVerificacion DESC;
END;
GO
