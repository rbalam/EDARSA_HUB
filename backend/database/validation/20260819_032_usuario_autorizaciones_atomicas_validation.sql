SET NOCOUNT ON;

IF DB_NAME() <> N'EDARSAHUB'
    THROW 51050, 'Base de datos inesperada.', 1;

IF OBJECT_ID(N'dbo.sp_Usuario_CrearAutorizacion', N'P') IS NULL
    THROW 51051, 'sp_Usuario_CrearAutorizacion inexistente.', 1;

IF OBJECT_ID(N'dbo.sp_Usuario_ResolverAutorizacion', N'P') IS NULL
    THROW 51052, 'sp_Usuario_ResolverAutorizacion inexistente.', 1;

DECLARE @CrearDefinicion NVARCHAR(MAX) =
    OBJECT_DEFINITION(OBJECT_ID(N'dbo.sp_Usuario_CrearAutorizacion'));
DECLARE @ResolverDefinicion NVARCHAR(MAX) =
    OBJECT_DEFINITION(OBJECT_ID(N'dbo.sp_Usuario_ResolverAutorizacion'));

IF @CrearDefinicion IS NULL OR @ResolverDefinicion IS NULL
    THROW 51053, 'No se pudo obtener definicion de procedimientos.', 1;

IF @CrearDefinicion NOT LIKE N'%SET XACT_ABORT ON%'
   OR @CrearDefinicion NOT LIKE N'%BEGIN TRY%'
   OR @CrearDefinicion NOT LIKE N'%BEGIN TRANSACTION%'
   OR @CrearDefinicion LIKE N'%SET @UsuarioSolicitanteID = 1%'
   OR @CrearDefinicion NOT LIKE N'%Usuario solicitante requerido.%'
   OR @CrearDefinicion NOT LIKE N'%Usuario solicitante inexistente o inactivo.%'
   OR @CrearDefinicion NOT LIKE N'%No existe matriz de autorizacion aplicable.%'
   OR @CrearDefinicion NOT LIKE N'%La matriz aplicable no tiene autorizadores activos.%'
   OR @CrearDefinicion NOT LIKE N'%La solicitud no contiene todos los detalles requeridos.%'
   OR @CrearDefinicion NOT LIKE N'%@AutorizacionID BIGINT OUTPUT%'
   OR @CrearDefinicion NOT LIKE N'%@@TRANCOUNT > 0%'
    THROW 51054, 'Contrato atomico fail-closed de creacion invalido.', 1;

IF @ResolverDefinicion NOT LIKE N'%SET XACT_ABORT ON%'
   OR @ResolverDefinicion NOT LIKE N'%BEGIN TRY%'
   OR @ResolverDefinicion NOT LIKE N'%BEGIN TRANSACTION%'
   OR @ResolverDefinicion NOT LIKE N'%UPDLOCK, HOLDLOCK%'
   OR @ResolverDefinicion NOT LIKE N'%@Resultado NOT IN (''AUTORIZADA'', ''RECHAZADA'')%'
   OR @ResolverDefinicion NOT LIKE N'%Usuario autorizador requerido.%'
   OR @ResolverDefinicion NOT LIKE N'%Usuario autorizador inexistente o inactivo.%'
   OR @ResolverDefinicion NOT LIKE N'%Autorizacion inexistente o no pendiente.%'
   OR @ResolverDefinicion NOT LIKE N'%No existe nivel pendiente.%'
   OR @ResolverDefinicion NOT LIKE N'%@@ROWCOUNT <> 1%'
   OR @ResolverDefinicion LIKE N'%SET @UsuarioAutorizadorID = 1%'
    THROW 51055, 'Contrato atomico de resolucion invalido.', 1;

IF @CrearDefinicion LIKE N'%CREATE ' + N'TABLE%'
   OR @CrearDefinicion LIKE N'%ALTER ' + N'TABLE%'
   OR @ResolverDefinicion LIKE N'%CREATE ' + N'TABLE%'
   OR @ResolverDefinicion LIKE N'%ALTER ' + N'TABLE%'
    THROW 51056, 'Los procedimientos no deben modificar esquema.', 1;

SELECT
    CONVERT(
        VARCHAR(64),
        HASHBYTES(
            'SHA2_256',
            CONVERT(VARBINARY(MAX), @CrearDefinicion)
        ),
        2
    ) AS sp_crear_runtime_sha256,
    CONVERT(
        VARCHAR(64),
        HASHBYTES(
            'SHA2_256',
            CONVERT(VARBINARY(MAX), @ResolverDefinicion)
        ),
        2
    ) AS sp_resolver_runtime_sha256;
