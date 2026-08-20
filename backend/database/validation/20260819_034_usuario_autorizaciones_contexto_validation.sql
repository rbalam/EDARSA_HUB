SET NOCOUNT ON;
GO

IF DB_NAME() <> N'EDARSAHUB'
    THROW 51050, 'Base de datos incorrecta. Se requiere EDARSAHUB.', 1;

-- 1. Columna RequiereUnidadNegocio en dbo.Usuario_TiposAutorizacion
IF COL_LENGTH('dbo.Usuario_TiposAutorizacion', 'RequiereUnidadNegocio') IS NULL
    THROW 51080, 'Falta columna RequiereUnidadNegocio en dbo.Usuario_TiposAutorizacion.', 1;

-- 2. AUT_TES_PAGOS configurado con RequiereUnidadNegocio = 1
IF NOT EXISTS (
    SELECT 1
    FROM dbo.Usuario_TiposAutorizacion
    WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS'
      AND RequiereUnidadNegocio = 1
      AND Activo = 1
)
    THROW 51081, 'AUT_TES_PAGOS no tiene configurado RequiereUnidadNegocio = 1.', 1;

-- 3. Tipos legacy preservan RequiereUnidadNegocio = 0
IF EXISTS (
    SELECT 1
    FROM dbo.Usuario_TiposAutorizacion
    WHERE CodigoTipoAutorizacion <> 'AUT_TES_PAGOS'
      AND RequiereUnidadNegocio = 1
)
    THROW 51082, 'Tipos de autorizacion legacy no deben tener RequiereUnidadNegocio = 1 sin configuracion explicita.', 1;

-- 4. Definicion de sp_Usuario_CrearAutorizacion contiene parametro @UnidadNegocioID
DECLARE @SpDef NVARCHAR(MAX);
SELECT @SpDef = OBJECT_DEFINITION(OBJECT_ID(N'dbo.sp_Usuario_CrearAutorizacion'));

IF @SpDef IS NULL
    THROW 51083, 'sp_Usuario_CrearAutorizacion inexistente.', 1;

IF @SpDef NOT LIKE '%@UnidadNegocioID UNIQUEIDENTIFIER = NULL%'
    THROW 51084, 'sp_Usuario_CrearAutorizacion no incluye parametro @UnidadNegocioID.', 1;

-- 5. sp_Usuario_CrearAutorizacion consulta dbo.Usuario_RolesContexto
IF @SpDef NOT LIKE '%dbo.Usuario_RolesContexto%'
    THROW 51085, 'sp_Usuario_CrearAutorizacion no consulta dbo.Usuario_RolesContexto.', 1;

-- 6. sp_Usuario_CrearAutorizacion valida fail-closed para RequiereUnidadNegocio
IF @SpDef NOT LIKE '%@RequiereUnidadNegocio = 1 AND @UnidadNegocioID IS NULL%'
    THROW 51086, 'sp_Usuario_CrearAutorizacion no valida fail-closed cuando RequiereUnidadNegocio = 1 y @UnidadNegocioID IS NULL.', 1;

-- 7. sp_Usuario_CrearAutorizacion valida existencia activa de unidad
IF @SpDef NOT LIKE '%dbo.Unidades_Negocio%'
    THROW 51087, 'sp_Usuario_CrearAutorizacion no valida la existencia de la unidad en dbo.Unidades_Negocio.', 1;

-- 8. Validar que no se crearon asignaciones sinteticas de roles en Usuario_RolesContexto
IF EXISTS (
    SELECT 1
    FROM dbo.Usuario_RolesContexto urc
    INNER JOIN dbo.Usuario_Roles r ON urc.RolID = r.RolID
    WHERE r.CodigoRol IN ('GERENCIA', 'DIRECCION')
      AND urc.Activo = 1
)
    THROW 51088, 'Violacion: No deben crearse asignaciones sinteticas de usuarios en Usuario_RolesContexto durante la migracion.', 1;

PRINT 'VALIDATION_SUCCESS: Slice 2.5 context schema and SP contract validated successfully.';
GO
