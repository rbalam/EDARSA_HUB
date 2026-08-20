SET NOCOUNT ON;

DECLARE @Crear NVARCHAR(MAX);
DECLARE @Resolver NVARCHAR(MAX);

SELECT
    @Crear =
        OBJECT_DEFINITION(
            OBJECT_ID(
                N'dbo.sp_Usuario_CrearAutorizacion'
            )
        );

SELECT
    @Resolver =
        OBJECT_DEFINITION(
            OBJECT_ID(
                N'dbo.sp_Usuario_ResolverAutorizacion'
            )
        );

IF @Crear IS NULL
    THROW 51120,
    'sp_Usuario_CrearAutorizacion inexistente.',
    1;

IF @Resolver IS NULL
    THROW 51121,
    'sp_Usuario_ResolverAutorizacion inexistente.',
    1;

IF @Crear NOT LIKE '%ModoAutorizacion%'
    THROW 51122,
    'CrearAutorizacion no usa ModoAutorizacion.',
    1;

IF @Crear NOT LIKE '%Usuario_Autorizaciones%'
    THROW 51123,
    'CrearAutorizacion no persiste solicitud.',
    1;

IF @Resolver NOT LIKE '%MANCOMUNADA%'
    THROW 51124,
    'ResolverAutorizacion no contempla MANCOMUNADA.',
    1;

IF @Resolver NOT LIKE '%ESCALABLE%'
    THROW 51125,
    'ResolverAutorizacion no contempla ESCALABLE.',
    1;

IF @Resolver NOT LIKE '%MIN(NivelAutorizacion)%'
    THROW 51126,
    'Se perdió resolución secuencial ESCALABLE.',
    1;

SELECT
    'PASS' AS AuthorizationModeAwareEngine;
