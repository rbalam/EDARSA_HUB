/*
IA_ASSISTANT_VALIDATION

Validación read-only posterior a la migración.
Cada resultset está separado con GO para que el runner
capture los ocho resultados de manera independiente.
*/

SET NOCOUNT ON;

IF DB_NAME() <> N'EDARSAHUB'
BEGIN
    THROW 51000,
        'La validación IA solo puede ejecutarse en EDARSAHUB.',
        1;
END;

SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    USER_NAME() AS database_user,
    SYSUTCDATETIME() AS validated_at_utc;
GO

SELECT
    t.name AS tabla,
    c.column_id,
    c.name AS columna,
    TYPE_NAME(c.user_type_id) AS tipo,
    c.max_length,
    c.is_nullable,
    c.is_identity,
    dc.name AS default_name,
    dc.definition AS default_definition
FROM sys.tables t
INNER JOIN sys.columns c
    ON c.object_id = t.object_id
LEFT JOIN sys.default_constraints dc
    ON dc.object_id = c.default_object_id
WHERE t.schema_id = SCHEMA_ID(N'dbo')
  AND t.name IN (
      N'IA_Assistant_Sesiones',
      N'IA_Assistant_Mensajes'
  )
ORDER BY
    t.name,
    c.column_id;
GO

SELECT
    fk.name AS foreign_key_name,
    fk.is_disabled,
    fk.is_not_trusted,
    OBJECT_NAME(
        fk.parent_object_id
    ) AS parent_table,
    COL_NAME(
        fkc.parent_object_id,
        fkc.parent_column_id
    ) AS parent_column,
    OBJECT_NAME(
        fk.referenced_object_id
    ) AS referenced_table,
    COL_NAME(
        fkc.referenced_object_id,
        fkc.referenced_column_id
    ) AS referenced_column
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc
    ON fkc.constraint_object_id = fk.object_id
WHERE fk.parent_object_id =
    OBJECT_ID(N'dbo.IA_Assistant_Mensajes')
  AND fk.referenced_object_id =
    OBJECT_ID(N'dbo.IA_Assistant_Sesiones');
GO

SELECT
    OBJECT_NAME(i.object_id) AS tabla,
    i.name AS indice,
    i.is_disabled,
    i.is_unique,
    i.is_primary_key,
    ic.key_ordinal,
    c.name AS columna,
    ic.is_descending_key
FROM sys.indexes i
INNER JOIN sys.index_columns ic
    ON ic.object_id = i.object_id
   AND ic.index_id = i.index_id
INNER JOIN sys.columns c
    ON c.object_id = ic.object_id
   AND c.column_id = ic.column_id
WHERE i.object_id IN (
    OBJECT_ID(N'dbo.IA_Assistant_Sesiones'),
    OBJECT_ID(N'dbo.IA_Assistant_Mensajes')
)
ORDER BY
    tabla,
    indice,
    ic.key_ordinal;
GO

SELECT
    (
        SELECT COUNT_BIG(*)
        FROM dbo.IA_Assistant_Sesiones
    ) AS sesiones_total,

    (
        SELECT COUNT_BIG(*)
        FROM dbo.IA_Assistant_Mensajes
    ) AS mensajes_total,

    (
        SELECT COUNT_BIG(*)
        FROM dbo.IA_Assistant_Mensajes m
        LEFT JOIN dbo.IA_Assistant_Sesiones s
            ON s.SesionID = m.SesionID
        WHERE s.SesionID IS NULL
    ) AS mensajes_huerfanos;
GO

SELECT
    r.CodigoRol,
    r.NombreRol,
    r.NivelJerarquia,
    CONCAT(
        m.CodigoModulo,
        N'_',
        a.CodigoAccion
    ) AS permiso,
    prm.Permitido,
    prm.Activo
FROM dbo.Usuario_Roles r
INNER JOIN dbo.Usuario_PermisosRolModulo prm
    ON prm.RolID = r.RolID
INNER JOIN dbo.Usuario_Modulos m
    ON m.ModuloID = prm.ModuloID
INNER JOIN dbo.Usuario_Acciones a
    ON a.AccionID = prm.AccionID
WHERE m.CodigoModulo = N'IA_ASSISTANT'
  AND a.CodigoAccion = N'VER'
ORDER BY
    r.NivelJerarquia DESC,
    r.CodigoRol;
GO

SELECT
    sm.ModuloID,
    sm.Codigo AS modulo_codigo,
    sm.Nombre AS modulo_nombre,
    sm.Descripcion AS modulo_descripcion,
    sm.Icono AS modulo_icono,
    sm.Orden AS modulo_orden,
    sm.EsPrincipal,
    sm.EsSatelite,
    sm.EsPortal,
    sm.URLExterna,
    sm.Activo AS modulo_activo,
    smm.MenuID,
    smm.Codigo AS menu_codigo,
    smm.Nombre AS menu_nombre,
    smm.Ruta,
    smm.RequierePermiso,
    smm.Activo AS menu_activo
FROM dbo.Sistema_Modulos sm
INNER JOIN dbo.Sistema_ModulosMenus smm
    ON smm.ModuloID = sm.ModuloID
WHERE sm.Codigo = N'IA'
  AND smm.Codigo = N'ia.assistant'
  AND smm.Ruta = N'/ia';
GO

WITH Facts AS (
    SELECT
        DB_NAME() AS database_name,
        SUSER_SNAME() AS login_name,
        USER_NAME() AS database_user,

        CASE
            WHEN EXISTS (
                SELECT 1
                FROM sys.columns c
                WHERE c.object_id =
                    OBJECT_ID(
                        N'dbo.IA_Assistant_Sesiones'
                    )
                  AND c.name = N'UsuarioEmail'
                  AND TYPE_NAME(
                        c.user_type_id
                      ) = N'nvarchar'
                  AND c.max_length >= 640
                  AND c.is_nullable = 0
            )
            THEN 1 ELSE 0
        END AS usuario_email_contract_ok,

        CASE
            WHEN EXISTS (
                SELECT 1
                FROM sys.foreign_keys fk
                WHERE fk.name =
                    N'FK_IA_Assistant_Mensajes_Sesion'
                  AND fk.parent_object_id =
                    OBJECT_ID(
                        N'dbo.IA_Assistant_Mensajes'
                    )
                  AND fk.referenced_object_id =
                    OBJECT_ID(
                        N'dbo.IA_Assistant_Sesiones'
                    )
                  AND fk.is_disabled = 0
                  AND fk.is_not_trusted = 0
            )
            THEN 1 ELSE 0
        END AS foreign_key_ok,

        CASE
            WHEN EXISTS (
                SELECT 1
                FROM sys.indexes i
                WHERE i.object_id =
                    OBJECT_ID(
                        N'dbo.IA_Assistant_Sesiones'
                    )
                  AND i.name =
                    N'IX_IA_Assistant_Sesiones_Usuario_Activo'
                  AND i.is_disabled = 0
            )
            THEN 1 ELSE 0
        END AS session_index_ok,

        CASE
            WHEN EXISTS (
                SELECT 1
                FROM sys.indexes i
                WHERE i.object_id =
                    OBJECT_ID(
                        N'dbo.IA_Assistant_Mensajes'
                    )
                  AND i.name IN (
                      N'IX_IA_Mensajes_Sesion',
                      N'IX_IA_Assistant_Mensajes_Sesion_Fecha'
                  )
                  AND i.is_disabled = 0
            )
            THEN 1 ELSE 0
        END AS message_index_ok,

        CASE
            WHEN EXISTS (
                SELECT 1
                FROM dbo.Sistema_Modulos
                WHERE ModuloID = 20
                  AND Codigo = N'IA'
                  AND Nombre =
                      N'Inteligencia Artificial'
                  AND Descripcion =
                      N'Asistentes, análisis, automatización'
                  AND Icono = N'Brain'
                  AND Orden = 20
                  AND EsPrincipal = 1
                  AND EsSatelite = 0
                  AND EsPortal = 0
                  AND URLExterna IS NULL
                  AND Activo = 1
            )
            THEN 1 ELSE 0
        END AS existing_module_preserved,

        CASE
            WHEN (
                SELECT COUNT_BIG(*)
                FROM dbo.Sistema_ModulosMenus smm
                INNER JOIN dbo.Sistema_Modulos sm
                    ON sm.ModuloID = smm.ModuloID
                WHERE sm.Codigo = N'IA'
                  AND smm.Codigo =
                      N'ia.assistant'
                  AND smm.Ruta = N'/ia'
                  AND smm.RequierePermiso =
                      N'IA_ASSISTANT'
                  AND ISNULL(sm.Activo, 1) = 1
                  AND ISNULL(smm.Activo, 1) = 1
            ) = 1
            THEN 1 ELSE 0
        END AS menu_ok,

        CASE
            WHEN (
                SELECT COUNT_BIG(*)
                FROM dbo.Usuario_Modulos
                WHERE CodigoModulo =
                    N'IA_ASSISTANT'
                  AND Ruta = N'/ia'
                  AND Activo = 1
            ) = 1
            THEN 1 ELSE 0
        END AS rbac_module_ok,

        CASE
            WHEN EXISTS (
                SELECT 1
                FROM dbo.Usuario_PermisosRolModulo prm
                INNER JOIN dbo.Usuario_Roles r
                    ON r.RolID = prm.RolID
                INNER JOIN dbo.Usuario_Modulos m
                    ON m.ModuloID = prm.ModuloID
                INNER JOIN dbo.Usuario_Acciones a
                    ON a.AccionID = prm.AccionID
                WHERE m.CodigoModulo =
                    N'IA_ASSISTANT'
                  AND a.CodigoAccion = N'VER'
                  AND prm.Permitido = 1
                  AND prm.Activo = 1
                  AND r.Activo = 1
                  AND r.CodigoRol IN (
                      N'SUPERADMIN',
                      N'SUPERADMINISTRADOR'
                  )
            )
            THEN 1 ELSE 0
        END AS superadmin_permission_ok,

        CASE
            WHEN EXISTS (
                SELECT 1
                FROM dbo.Usuario_PermisosRolModulo prm
                INNER JOIN dbo.Usuario_Roles r
                    ON r.RolID = prm.RolID
                INNER JOIN dbo.Usuario_Modulos m
                    ON m.ModuloID = prm.ModuloID
                INNER JOIN dbo.Usuario_Acciones a
                    ON a.AccionID = prm.AccionID
                WHERE m.CodigoModulo =
                    N'IA_ASSISTANT'
                  AND a.CodigoAccion = N'VER'
                  AND prm.Permitido = 1
                  AND prm.Activo = 1
                  AND r.Activo = 1
                  AND r.CodigoRol IN (
                      N'ADMIN',
                      N'ADMINISTRADOR'
                  )
            )
            THEN 1 ELSE 0
        END AS admin_permission_ok,

        CASE
            WHEN NOT EXISTS (
                SELECT 1
                FROM dbo.Usuario_PermisosRolModulo prm
                INNER JOIN dbo.Usuario_Roles r
                    ON r.RolID = prm.RolID
                INNER JOIN dbo.Usuario_Modulos m
                    ON m.ModuloID = prm.ModuloID
                INNER JOIN dbo.Usuario_Acciones a
                    ON a.AccionID = prm.AccionID
                WHERE m.CodigoModulo =
                    N'IA_ASSISTANT'
                  AND a.CodigoAccion = N'VER'
                  AND prm.Permitido = 1
                  AND prm.Activo = 1
                  AND r.Activo = 1
                  AND r.CodigoRol NOT IN (
                      N'SUPERADMIN',
                      N'SUPERADMINISTRADOR',
                      N'ADMIN',
                      N'ADMINISTRADOR'
                  )
            )
            THEN 1 ELSE 0
        END AS no_extra_roles_ok,

        CASE
            WHEN NOT EXISTS (
                SELECT 1
                FROM dbo.IA_Assistant_Mensajes m
                LEFT JOIN dbo.IA_Assistant_Sesiones s
                    ON s.SesionID = m.SesionID
                WHERE s.SesionID IS NULL
            )
            THEN 1 ELSE 0
        END AS no_orphans_ok
),
Evaluated AS (
    SELECT
        *,
        CASE
            WHEN database_name <> N'EDARSAHUB'
            THEN N'FAIL_DATABASE'

            WHEN login_name <> N'HRLectura'
            THEN N'FAIL_LOGIN'

            WHEN database_user <> N'HRLectura'
            THEN N'FAIL_DATABASE_USER'

            WHEN usuario_email_contract_ok <> 1
            THEN N'FAIL_EMAIL_CONTRACT'

            WHEN foreign_key_ok <> 1
            THEN N'FAIL_FOREIGN_KEY'

            WHEN session_index_ok <> 1
            THEN N'FAIL_SESSION_INDEX'

            WHEN message_index_ok <> 1
            THEN N'FAIL_MESSAGE_INDEX'

            WHEN existing_module_preserved <> 1
            THEN N'FAIL_EXISTING_MODULE'

            WHEN menu_ok <> 1
            THEN N'FAIL_MENU'

            WHEN rbac_module_ok <> 1
            THEN N'FAIL_RBAC_MODULE'

            WHEN superadmin_permission_ok <> 1
            THEN N'FAIL_SUPERADMIN_PERMISSION'

            WHEN admin_permission_ok <> 1
            THEN N'FAIL_ADMIN_PERMISSION'

            WHEN no_extra_roles_ok <> 1
            THEN N'FAIL_EXTRA_ROLES'

            WHEN no_orphans_ok <> 1
            THEN N'FAIL_ORPHANS'

            ELSE N'PASS'
        END AS ia_assistant_validation
    FROM Facts
)
SELECT
    database_name,
    login_name,
    database_user,
    usuario_email_contract_ok,
    foreign_key_ok,
    session_index_ok,
    message_index_ok,
    existing_module_preserved,
    menu_ok,
    rbac_module_ok,
    superadmin_permission_ok,
    admin_permission_ok,
    no_extra_roles_ok,
    no_orphans_ok,
    ia_assistant_validation
FROM Evaluated;
