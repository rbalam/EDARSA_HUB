/*
EDARSAHUB - RBAC Fase 2E
Validación permiso Bitácora RBAC.

Modo recomendado:
python backend/tools/edarsahub_sql_runner.py \
  --mode validate \
  --script backend/database/validation/phase2e_rbac_bitacora_permiso_validation.sql
*/

SET NOCOUNT ON;

IF OBJECT_ID('dbo.Usuario_Roles', 'U') IS NULL
    THROW 51000, 'No existe dbo.Usuario_Roles.', 1;

IF OBJECT_ID('dbo.Usuario_Modulos', 'U') IS NULL
    THROW 51000, 'No existe dbo.Usuario_Modulos.', 1;

IF OBJECT_ID('dbo.Usuario_Acciones', 'U') IS NULL
    THROW 51000, 'No existe dbo.Usuario_Acciones.', 1;

IF OBJECT_ID('dbo.Usuario_PermisosRolModulo', 'U') IS NULL
    THROW 51000, 'No existe dbo.Usuario_PermisosRolModulo.', 1;

SELECT
    'MODULE_EXISTS' AS paso,
    ModuloID,
    CodigoModulo,
    NombreModulo,
    Activo
FROM dbo.Usuario_Modulos
WHERE CodigoModulo = 'SISTEMA_RBAC_BITACORA';

SELECT
    'ACTION_EXISTS' AS paso,
    AccionID,
    CodigoAccion,
    NombreAccion,
    Activo
FROM dbo.Usuario_Acciones
WHERE CodigoAccion = 'VER';

SELECT
    'ROLE_PERMISSION_MATRIX' AS paso,
    r.RolID,
    r.CodigoRol,
    r.NombreRol,
    r.NivelJerarquia,
    m.CodigoModulo,
    a.CodigoAccion,
    CONCAT(UPPER(m.CodigoModulo), '_', UPPER(a.CodigoAccion)) AS permiso_normalizado,
    prm.Permitido,
    prm.Activo
FROM dbo.Usuario_PermisosRolModulo prm
INNER JOIN dbo.Usuario_Roles r
    ON r.RolID = prm.RolID
INNER JOIN dbo.Usuario_Modulos m
    ON m.ModuloID = prm.ModuloID
INNER JOIN dbo.Usuario_Acciones a
    ON a.AccionID = prm.AccionID
WHERE m.CodigoModulo = 'SISTEMA_RBAC_BITACORA'
  AND a.CodigoAccion = 'VER'
ORDER BY r.NivelJerarquia DESC, r.CodigoRol;

SELECT
    'RICARDO_EFFECTIVE_PERMISSION_CHECK' AS paso,
    u.UsuarioID,
    u.Email,
    r.CodigoRol,
    CONCAT(UPPER(m.CodigoModulo), '_', UPPER(a.CodigoAccion)) AS permiso_normalizado,
    prm.Permitido,
    prm.Activo
FROM dbo.Usuario_Catalogo u
INNER JOIN dbo.Usuario_RolesAsignacion ura
    ON ura.UsuarioID = u.UsuarioID
    AND ura.Activo = 1
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
WHERE LOWER(u.Email) = 'ricardo@edarsa.com.mx'
  AND m.CodigoModulo = 'SISTEMA_RBAC_BITACORA'
  AND a.CodigoAccion = 'VER';

SELECT
    'EXPECTED_PERMISSION' AS paso,
    'SISTEMA_RBAC_BITACORA_VER' AS permiso_esperado;
