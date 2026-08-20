SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF EXISTS (
        SELECT 1
        FROM sys.check_constraints
        WHERE name = 'CK_Usuario_Autorizaciones_Modo'
          AND parent_object_id =
              OBJECT_ID('dbo.Usuario_Autorizaciones')
    )
        ALTER TABLE dbo.Usuario_Autorizaciones
        DROP CONSTRAINT CK_Usuario_Autorizaciones_Modo;

    IF COL_LENGTH(
        'dbo.Usuario_Autorizaciones',
        'ModoAutorizacion'
    ) IS NOT NULL
        ALTER TABLE dbo.Usuario_Autorizaciones
        DROP COLUMN ModoAutorizacion;

    IF EXISTS (
        SELECT 1
        FROM sys.check_constraints
        WHERE name = 'CK_Usuario_TiposAutorizacion_Modo'
          AND parent_object_id =
              OBJECT_ID('dbo.Usuario_TiposAutorizacion')
    )
        ALTER TABLE dbo.Usuario_TiposAutorizacion
        DROP CONSTRAINT CK_Usuario_TiposAutorizacion_Modo;

    IF COL_LENGTH(
        'dbo.Usuario_TiposAutorizacion',
        'ModoAutorizacion'
    ) IS NOT NULL
        ALTER TABLE dbo.Usuario_TiposAutorizacion
        DROP COLUMN ModoAutorizacion;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
