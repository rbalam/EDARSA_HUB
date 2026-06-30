# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-30T10:10:32.793505
- Modo: `validate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/validation/phase2c_rbac_menu_multiuser_candidates.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 4
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: Comando
- Filas afectadas: -1

### Batch 2
- Tipo: SELECT
- Columnas: CodigoRol, NombreRol, NivelJerarquia, Activo, usuarios_activos_asignados, permisos_permitidos, modulos_visibles_con_permiso, estado_validacion
- Filas: 23
- Preview (primeras 20 filas):
```
  {'CodigoRol': 'SUPERADMIN', 'NombreRol': 'SuperAdministrador', 'NivelJerarquia': 100, 'Activo': True, 'usuarios_activos_asignados': 4, 'permisos_permitidos': 61, 'modulos_visibles_con_permiso': 56, 'estado_validacion': 'OK'}
  {'CodigoRol': 'ADMIN', 'NombreRol': 'Administrador', 'NivelJerarquia': 90, 'Activo': True, 'usuarios_activos_asignados': 3, 'permisos_permitidos': 61, 'modulos_visibles_con_permiso': 56, 'estado_validacion': 'OK'}
  {'CodigoRol': 'ADMIN_COMERCIAL', 'NombreRol': 'Administrador Comercial', 'NivelJerarquia': 85, 'Activo': True, 'usuarios_activos_asignados': 0, 'permisos_permitidos': 15, 'modulos_visibles_con_permiso': 1, 'estado_validacion': 'INFO_ROL_ACTIVO_SIN_USUARIOS'}
  {'CodigoRol': 'DIRECCION', 'NombreRol': 'Dirección', 'NivelJerarquia': 80, 'Activo': True, 'usuarios_activos_asignados': 0, 'permisos_permitidos': 34, 'modulos_visibles_con_permiso': 9, 'estado_validacion': 'INFO_ROL_ACTIVO_SIN_USUARIOS'}
  {'CodigoRol': 'GERENTE_OPS', 'NombreRol': 'Gerente Operaciones', 'NivelJerarquia': 60, 'Activo': True, 'usuarios_activos_asignados': 0, 'permisos_permitidos': 46, 'modulos_visibles_con_permiso': 19, 'estado_validacion': 'INFO_ROL_ACTIVO_SIN_USUARIOS'}
  {'CodigoRol': 'GERENTE_UNIDAD', 'NombreRol': 'Gerente de Unidad', 'NivelJerarquia': 55, 'Activo': True, 'usuarios_activos_asignados': 0, 'permisos_permitidos': 10, 'modulos_visibles_con_permiso': 1, 'estado_validacion': 'INFO_ROL_ACTIVO_SIN_USUARIOS'}
  {'CodigoRol': 'SUPERVISOR', 'NombreRol': 'Supervisor', 'NivelJerarquia': 50, 'Activo': True, 'usuarios_activos_asignados': 1, 'permisos_permitidos': 45, 'modulos_visibles_con_permiso': 25, 'estado_validacion': 'OK'}
  {'CodigoRol': 'CONFIGURADOR_COMERCIAL', 'NombreRol': 'Configurador Comercial', 'NivelJerarquia': 45, 'Activo': True, 'usuarios_activos_asignados': 0, 'permisos_permitidos': 12, 'modulos_visibles_con_permiso': 1, 'estado_validacion': 'INFO_ROL_ACTIVO_SIN_USUARIOS'}
  {'CodigoRol': 'ANALISTA_COMERCIAL', 'NombreRol': 'Analista Comercial', 'NivelJerarquia': 40, 'Activo': True, 'usuarios_activos_asignados': 0, 'permisos_permitidos': 9, 'modulos_visibles_con_permiso': 1, 'estado_validacion': 'INFO_ROL_ACTIVO_SIN_USUARIOS'}
  {'CodigoRol': 'AUDITOR', 'NombreRol': 'Auditor', 'NivelJerarquia': 30, 'Activo': True, 'usuarios_activos_asignados': 0, 'permisos_permitidos': 49, 'modulos_visibles_con_permiso': 28, 'estado_validacion': 'INFO_ROL_ACTIVO_SIN_USUARIOS'}
```

### Batch 3
- Tipo: SELECT
- Columnas: UsuarioID, Email, Username, NombreCompleto, Activo, tiene_password_hash, roles_activos, roles_activos_count, nivel_jerarquia_max, permisos_efectivos, modulos_visibles_con_permiso, empresas_count, servidores_count, sucursales_count, candidato_api
- Filas: 12
- Preview (primeras 20 filas):
```
  {'UsuarioID': 1, 'Email': 'admin@edarsa.com', 'Username': 'admin@edarsa.com', 'NombreCompleto': 'Admin Test Editado', 'Activo': True, 'tiene_password_hash': 1, 'roles_activos': 'SUPERADMIN', 'roles_activos_count': 1, 'nivel_jerarquia_max': 100, 'permisos_efectivos': 61, 'modulos_visibles_con_permiso': 56, 'empresas_count': 0, 'servidores_count': 0, 'sucursales_count': 0, 'candidato_api': 'CANDIDATO_GLOBAL'}
  {'UsuarioID': 24, 'Email': 'ewsbaquedano@gmail.com', 'Username': 'ewsbaquedano@gmail.com', 'NombreCompleto': 'Salim Baquedano Mir', 'Activo': True, 'tiene_password_hash': 0, 'roles_activos': 'SUPERADMIN', 'roles_activos_count': 1, 'nivel_jerarquia_max': 100, 'permisos_efectivos': 61, 'modulos_visibles_con_permiso': 56, 'empresas_count': 0, 'servidores_count': 0, 'sucursales_count': 0, 'candidato_api': 'WARN_SIN_HASH_LOGIN'}
  {'UsuarioID': 22, 'Email': 'qa.superadmin@edarsa.com', 'Username': 'qa.superadmin', 'NombreCompleto': 'QA SuperAdmin', 'Activo': True, 'tiene_password_hash': 1, 'roles_activos': 'SUPERADMIN', 'roles_activos_count': 1, 'nivel_jerarquia_max': 100, 'permisos_efectivos': 61, 'modulos_visibles_con_permiso': 56, 'empresas_count': 0, 'servidores_count': 0, 'sucursales_count': 0, 'candidato_api': 'CANDIDATO_GLOBAL'}
  {'UsuarioID': 8, 'Email': 'ricardo@edarsa.com.mx', 'Username': 'ricardo@edarsa.com.mx', 'NombreCompleto': 'Ricardo Balam Garcia', 'Activo': True, 'tiene_password_hash': 1, 'roles_activos': 'SUPERADMIN', 'roles_activos_count': 1, 'nivel_jerarquia_max': 100, 'permisos_efectivos': 61, 'modulos_visibles_con_permiso': 56, 'empresas_count': 0, 'servidores_count': 0, 'sucursales_count': 0, 'candidato_api': 'CANDIDATO_GLOBAL'}
  {'UsuarioID': 11, 'Email': 'carlos@alpuntoycoma.mx', 'Username': 'carlos@alpuntoycoma.mx', 'NombreCompleto': 'Carlos Alberto Aguirre de Leon', 'Activo': True, 'tiene_password_hash': 1, 'roles_activos': 'ADMIN', 'roles_activos_count': 1, 'nivel_jerarquia_max': 90, 'permisos_efectivos': 61, 'modulos_visibles_con_permiso': 56, 'empresas_count': 0, 'servidores_count': 5, 'sucursales_count': 2, 'candidato_api': 'CANDIDATO_LIMITADO'}
  {'UsuarioID': 3, 'Email': 'carlosruz@edarsa.com.mx', 'Username': 'carlosruz@edarsa.com.mx', 'NombreCompleto': 'Carlos Ruz', 'Activo': True, 'tiene_password_hash': 1, 'roles_activos': 'ADMIN', 'roles_activos_count': 1, 'nivel_jerarquia_max': 90, 'permisos_efectivos': 61, 'modulos_visibles_con_permiso': 56, 'empresas_count': 0, 'servidores_count': 14, 'sucursales_count': 10, 'candidato_api': 'CANDIDATO_LIMITADO'}
  {'UsuarioID': 12, 'Email': 'eduardo@alpuntoycoma.mx', 'Username': 'eduardo@alpuntoycoma.mx', 'NombreCompleto': 'Eduardo Jose Medina García', 'Activo': True, 'tiene_password_hash': 1, 'roles_activos': 'ADMIN', 'roles_activos_count': 1, 'nivel_jerarquia_max': 90, 'permisos_efectivos': 61, 'modulos_visibles_con_permiso': 56, 'empresas_count': 0, 'servidores_count': 0, 'sucursales_count': 0, 'candidato_api': 'CANDIDATO_LIMITADO'}
  {'UsuarioID': 4, 'Email': 'noxte@alpyc.com', 'Username': 'noxte@alpyc.com', 'NombreCompleto': 'Nestor Oxte', 'Activo': True, 'tiene_password_hash': 1, 'roles_activos': 'SUPERVISOR', 'roles_activos_count': 1, 'nivel_jerarquia_max': 50, 'permisos_efectivos': 45, 'modulos_visibles_con_permiso': 25, 'empresas_count': 0, 'servidores_count': 0, 'sucursales_count': 0, 'candidato_api': 'CANDIDATO_LIMITADO'}
  {'UsuarioID': 6, 'Email': 'almacen@cienfuegos.mx', 'Username': 'almacen@cienfuegos.mx', 'NombreCompleto': 'Cristina Chi', 'Activo': True, 'tiene_password_hash': 1, 'roles_activos': 'OPERADOR', 'roles_activos_count': 1, 'nivel_jerarquia_max': 20, 'permisos_efectivos': 28, 'modulos_visibles_con_permiso': 20, 'empresas_count': 0, 'servidores_count': 1, 'sucursales_count': 1, 'candidato_api': 'CANDIDATO_LIMITADO'}
  {'UsuarioID': 5, 'Email': 'auditoria@edarsa.com.mx', 'Username': 'auditoria@edarsa.com.mx', 'NombreCompleto': 'William Chuc', 'Activo': True, 'tiene_password_hash': 1, 'roles_activos': 'OPERADOR', 'roles_activos_count': 1, 'nivel_jerarquia_max': 20, 'permisos_efectivos': 28, 'modulos_visibles_con_permiso': 20, 'empresas_count': 0, 'servidores_count': 4, 'sucursales_count': 4, 'candidato_api': 'CANDIDATO_LIMITADO'}
```

### Batch 4
- Tipo: SELECT
- Columnas: metrica, total
- Filas: 4
- Preview (primeras 20 filas):
```
  {'metrica': 'usuarios_activos', 'total': 12}
  {'metrica': 'usuarios_activos_con_hash', 'total': 11}
  {'metrica': 'usuarios_activos_sin_rol_activo', 'total': 0}
  {'metrica': 'usuarios_activos_sin_permisos_no_globales', 'total': 0}
```


## SQL ejecutado / revisado
```sql
/*
Fase 2C RBAC/Menu multiuser candidates.

Solo lectura. No selecciona PasswordHashTexto ni ningun secreto.
Objetivo:
- Identificar usuarios activos candidatos para validacion API real multiusuario.
- Ver roles efectivos, conteo de permisos y alcance operativo por usuario.
- Detectar usuarios activos sin rol, sin permisos efectivos o sin hash de login.

Ejecutar con:
/app/.venv/bin/python backend/tools/edarsahub_sql_runner.py --mode validate --script backend/database/validation/phase2c_rbac_menu_multiuser_candidates.sql
*/

SET NOCOUNT ON;
GO

WITH role_permissions AS (
    SELECT
        r.RolID,
        COUNT(DISTINCT CASE
            WHEN prm.Activo = 1
             AND prm.Permitido = 1
             AND m.Activo = 1
             AND a.Activo = 1
            THEN prm.PermisoRolModuloID
        END) AS permisos_permitidos,
        COUNT(DISTINCT CASE
            WHEN prm.Activo = 1
             AND prm.Permitido = 1
             AND m.Activo = 1
             AND m.EsVisibleMenu = 1
             AND a.Activo = 1
            THEN m.ModuloID
        END) AS modulos_visibles_con_permiso
    FROM dbo.Usuario_Roles r
    LEFT JOIN dbo.Usuario_PermisosRolModulo prm
        ON prm.RolID = r.RolID
    LEFT JOIN dbo.Usuario_Modulos m
        ON m.ModuloID = prm.ModuloID
    LEFT JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
    GROUP BY r.RolID
),
role_users AS (
    SELECT
        r.RolID,
        COUNT(DISTINCT CASE
            WHEN u.Activo = 1
             AND ura.Activo = 1
            THEN u.UsuarioID
        END) AS usuarios_activos_asignados
    FROM dbo.Usuario_Roles r
    LEFT JOIN dbo.Usuario_RolesAsignacion ura
        ON ura.RolID = r.RolID
    LEFT JOIN dbo.Usuario_Catalogo u
        ON u.UsuarioID = ura.UsuarioID
    GROUP BY r.RolID
)
SELECT
    r.CodigoRol,
    r.NombreRol,
    r.NivelJerarquia,
    r.Activo,
    ISNULL(ru.usuarios_activos_asignados, 0) AS usuarios_activos_asignados,
    ISNULL(rp.permisos_permitidos, 0) AS permisos_permitidos,
    ISNULL(rp.modulos_visibles_con_permiso, 0) AS modulos_visibles_con_permiso,
    CASE
        WHEN r.Activo = 1
         AND ISNULL(ru.usuarios_activos_asignados, 0) > 0
         AND ISNULL(rp.permisos_permitidos, 0) = 0
        THEN 'WARN_ROL_ACTIVO_CON_USUARIOS_SIN_PERMISOS'
        WHEN r.Activo = 1
         AND ISNULL(ru.usuarios_activos_asignados, 0) = 0
        THEN 'INFO_ROL_ACTIVO_SIN_USUARIOS'
        ELSE 'OK'
    END AS estado_validacion
FROM dbo.Usuario_Roles r
LEFT JOIN role_permissions rp
    ON rp.RolID = r.RolID
LEFT JOIN role_users ru
    ON ru.RolID = r.RolID
ORDER BY
    r.Activo DESC,
    r.NivelJerarquia DESC,
    r.CodigoRol;
GO

WITH user_roles AS (
    SELECT
        u.UsuarioID,
        STRING_AGG(CONVERT(varchar(100), r.CodigoRol), ', ') AS roles_activos,
        MAX(ISNULL(r.NivelJerarquia, 0)) AS nivel_jerarquia_max,
        COUNT(DISTINCT r.RolID) AS roles_activos_count
    FROM dbo.Usuario_Catalogo u
    LEFT JOIN dbo.Usuario_RolesAsignacion ura
        ON ura.UsuarioID = u.UsuarioID
        AND ura.Activo = 1
    LEFT JOIN dbo.Usuario_Roles r
        ON r.RolID = ura.RolID
        AND r.Activo = 1
    GROUP BY u.UsuarioID
),
user_permissions AS (
    SELECT
        u.UsuarioID,
        COUNT(DISTINCT CASE
            WHEN prm.Activo = 1
             AND prm.Permitido = 1
             AND m.Activo = 1
             AND a.Activo = 1
            THEN CONCAT(UPPER(m.CodigoModulo), '_', UPPER(a.CodigoAccion))
        END) AS permisos_efectivos,
        COUNT(DISTINCT CASE
            WHEN prm.Activo = 1
             AND prm.Permitido = 1
             AND m.Activo = 1
             AND m.EsVisibleMenu = 1
             AND a.Activo = 1
            THEN m.ModuloID
        END) AS modulos_visibles_con_permiso
    FROM dbo.Usuario_Catalogo u
    LEFT JOIN dbo.Usuario_RolesAsignacion ura
        ON ura.UsuarioID = u.UsuarioID
        AND ura.Activo = 1
    LEFT JOIN dbo.Usuario_Roles r
        ON r.RolID = ura.RolID
        AND r.Activo = 1
    LEFT JOIN dbo.Usuario_PermisosRolModulo prm
        ON prm.RolID = r.RolID
    LEFT JOIN dbo.Usuario_Modulos m
        ON m.ModuloID = prm.ModuloID
    LEFT JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
    GROUP BY u.UsuarioID
),
user_scope AS (
    SELECT
        u.UsuarioID,
        (
            SELECT COUNT(DISTINCT EmpresaID)
            FROM dbo.Usuario_EmpresasAsignacion uea
            WHERE uea.UsuarioID = u.UsuarioID
              AND ISNULL(uea.Activo, 1) = 1
        ) AS empresas_count,
        (
            SELECT COUNT(DISTINCT ServidorID)
            FROM dbo.Usuario_ServidoresAsignacion usv
            WHERE usv.UsuarioID = u.UsuarioID
              AND ISNULL(usv.Activo, 1) = 1
        ) AS servidores_count,
        (
            SELECT COUNT(*)
            FROM dbo.Usuario_SucursalesAsignacion usa
            WHERE usa.UsuarioID = u.UsuarioID
              AND ISNULL(usa.Activo, 1) = 1
        ) AS sucursales_count
    FROM dbo.Usuario_Catalogo u
)
SELECT TOP (100)
    u.UsuarioID,
    u.Email,
    u.Username,
    u.NombreCompleto,
    u.Activo,
    CASE
        WHEN u.PasswordHashTexto IS NOT NULL
         AND LTRIM(RTRIM(CONVERT(NVARCHAR(MAX), u.PasswordHashTexto))) <> ''
        THEN 1
        ELSE 0
    END AS tiene_password_hash,
    ISNULL(ur.roles_activos, '') AS roles_activos,
    ISNULL(ur.roles_activos_count, 0) AS roles_activos_count,
    ISNULL(ur.nivel_jerarquia_max, 0) AS nivel_jerarquia_max,
    ISNULL(upm.permisos_efectivos, 0) AS permisos_efectivos,
    ISNULL(upm.modulos_visibles_con_permiso, 0) AS modulos_visibles_con_permiso,
    ISNULL(us.empresas_count, 0) AS empresas_count,
    ISNULL(us.servidores_count, 0) AS servidores_count,
    ISNULL(us.sucursales_count, 0) AS sucursales_count,
    CASE
        WHEN u.Activo <> 1
        THEN 'SKIP_USUARIO_INACTIVO'
        WHEN u.PasswordHashTexto IS NULL
          OR LTRIM(RTRIM(CONVERT(NVARCHAR(MAX), u.PasswordHashTexto))) = ''
        THEN 'WARN_SIN_HASH_LOGIN'
        WHEN ISNULL(ur.roles_activos_count, 0) = 0
        THEN 'WARN_SIN_ROL_ACTIVO'
        WHEN ISNULL(upm.permisos_efectivos, 0) = 0
         AND ISNULL(ur.nivel_jerarquia_max, 0) < 100
        THEN 'WARN_SIN_PERMISOS_EFECTIVOS'
        WHEN ISNULL(ur.nivel_jerarquia_max, 0) >= 100
        THEN 'CANDIDATO_GLOBAL'
        ELSE 'CANDIDATO_LIMITADO'
    END AS candidato_api
FROM dbo.Usuario_Catalogo u
LEFT JOIN user_roles ur
    ON ur.UsuarioID = u.UsuarioID
LEFT JOIN user_permissions upm
    ON upm.UsuarioID = u.UsuarioID
LEFT JOIN user_scope us
    ON us.UsuarioID = u.UsuarioID
WHERE u.Activo = 1
ORDER BY
    CASE
        WHEN ISNULL(ur.nivel_jerarquia_max, 0) >= 100 THEN 0
        WHEN ISNULL(upm.permisos_efectivos, 0) > 0 THEN 1
        ELSE 2
    END,
    ISNULL(ur.nivel_jerarquia_max, 0) DESC,
    ISNULL(upm.permisos_efectivos, 0) DESC,
    u.Email;
GO

SELECT
    'usuarios_activos' AS metrica,
    COUNT(*) AS total
FROM dbo.Usuario_Catalogo
WHERE Activo = 1
UNION ALL
SELECT
    'usuarios_activos_con_hash',
    COUNT(*)
FROM dbo.Usuario_Catalogo
WHERE Activo = 1
  AND PasswordHashTexto IS NOT NULL
  AND LTRIM(RTRIM(CONVERT(NVARCHAR(MAX), PasswordHashTexto))) <> ''
UNION ALL
SELECT
    'usuarios_activos_sin_rol_activo',
    COUNT(*)
FROM dbo.Usuario_Catalogo u
WHERE u.Activo = 1
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.Usuario_RolesAsignacion ura
      INNER JOIN dbo.Usuario_Roles r
          ON r.RolID = ura.RolID
          AND r.Activo = 1
      WHERE ura.UsuarioID = u.UsuarioID
        AND ura.Activo = 1
  )
UNION ALL
SELECT
    'usuarios_activos_sin_permisos_no_globales',
    COUNT(*)
FROM dbo.Usuario_Catalogo u
WHERE u.Activo = 1
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.Usuario_RolesAsignacion ura
      INNER JOIN dbo.Usuario_Roles r
          ON r.RolID = ura.RolID
          AND r.Activo = 1
      INNER JOIN dbo.Usuario_PermisosRolModulo prm
          ON prm.RolID = r.RolID
          AND prm.Activo = 1
          AND prm.Permitido = 1
      INNER JOIN dbo.Usuario_Modulos m
          ON m.ModuloID = prm.ModuloID
          AND m.Activo = 1
      INNER JOIN dbo.Usuario_Acciones a
          ON a.AccionID = prm.AccionID
          AND a.Activo = 1
      WHERE ura.UsuarioID = u.UsuarioID
        AND ura.Activo = 1
  )
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.Usuario_RolesAsignacion ura
      INNER JOIN dbo.Usuario_Roles r
          ON r.RolID = ura.RolID
          AND r.Activo = 1
      WHERE ura.UsuarioID = u.UsuarioID
        AND ura.Activo = 1
        AND ISNULL(r.NivelJerarquia, 0) >= 100
  );
GO

```