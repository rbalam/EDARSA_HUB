-- =====================================================
-- VALIDACIÓN RBAC CONTEXT
-- Ejecutar después de SQL_SCRIPT_64
-- =====================================================
SET NOCOUNT ON;

PRINT '===== VALIDACION RBAC CONTEXT =====';

SELECT
    CASE WHEN OBJECT_ID('dbo.Usuario_RolesContexto', 'U') IS NOT NULL THEN 'OK' ELSE 'FALTA' END AS Tabla_Usuario_RolesContexto,
    CASE WHEN OBJECT_ID('dbo.vw_Usuario_RolesContexto', 'V') IS NOT NULL THEN 'OK' ELSE 'FALTA' END AS Vista_vw_Usuario_RolesContexto;

PRINT '===== CONTEO TABLA =====';
SELECT COUNT(*) AS TotalRolesContexto
FROM dbo.Usuario_RolesContexto;

PRINT '===== MUESTRA ROLES CONTEXTO =====';
SELECT TOP 20 *
FROM dbo.vw_Usuario_RolesContexto
ORDER BY UsuarioID, EsRolPrimario DESC, NombreRol;

PRINT '===== USUARIOS SIN CONTEXTO =====';
SELECT TOP 20
    u.UsuarioID,
    u.Email,
    u.NombreCompleto
FROM dbo.Usuario_Catalogo u
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.Usuario_RolesContexto urc
    WHERE urc.UsuarioID = u.UsuarioID
      AND urc.Activo = 1
)
ORDER BY u.NombreCompleto;
