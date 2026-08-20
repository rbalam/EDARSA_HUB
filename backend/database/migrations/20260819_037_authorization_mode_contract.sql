SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

/*
    EDARSAHUB
    Contrato canónico de modos de autorización.

    ESCALABLE:
      el rango aplicable determina el autorizador/nivel correspondiente.

    MANCOMUNADA:
      todos los autorizadores aplicables deben resolver favorablemente
      la misma solicitud.

    No elimina RequiereTodosLosNiveles todavía por compatibilidad.
*/

IF COL_LENGTH(
    'dbo.Usuario_TiposAutorizacion',
    'ModoAutorizacion'
) IS NULL
BEGIN
    ALTER TABLE dbo.Usuario_TiposAutorizacion
    ADD ModoAutorizacion VARCHAR(20) NULL;
END;
GO

BEGIN TRY
    BEGIN TRANSACTION;

    UPDATE dbo.Usuario_TiposAutorizacion
    SET ModoAutorizacion = 'ESCALABLE'
    WHERE ModoAutorizacion IS NULL;

    ALTER TABLE dbo.Usuario_TiposAutorizacion
    ALTER COLUMN ModoAutorizacion VARCHAR(20) NOT NULL;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.check_constraints
        WHERE parent_object_id =
              OBJECT_ID('dbo.Usuario_TiposAutorizacion')
          AND name = 'CK_Usuario_TiposAutorizacion_Modo'
    )
    BEGIN
        ALTER TABLE dbo.Usuario_TiposAutorizacion
        ADD CONSTRAINT CK_Usuario_TiposAutorizacion_Modo
        CHECK (
            ModoAutorizacion IN (
                'ESCALABLE',
                'MANCOMUNADA'
            )
        );
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

IF COL_LENGTH(
    'dbo.Usuario_Autorizaciones',
    'ModoAutorizacion'
) IS NULL
BEGIN
    ALTER TABLE dbo.Usuario_Autorizaciones
    ADD ModoAutorizacion VARCHAR(20) NULL;
END;
GO

BEGIN TRY
    BEGIN TRANSACTION;

    UPDATE A
    SET A.ModoAutorizacion =
        ISNULL(
            TA.ModoAutorizacion,
            'ESCALABLE'
        )
    FROM dbo.Usuario_Autorizaciones AS A
    INNER JOIN dbo.Usuario_TiposAutorizacion AS TA
        ON TA.TipoAutorizacionID =
           A.TipoAutorizacionID
    WHERE A.ModoAutorizacion IS NULL;

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_Autorizaciones
        WHERE ModoAutorizacion IS NULL
    )
        THROW 51100,
        'Existen autorizaciones sin modo resoluble.',
        1;

    ALTER TABLE dbo.Usuario_Autorizaciones
    ALTER COLUMN ModoAutorizacion VARCHAR(20) NOT NULL;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.check_constraints
        WHERE parent_object_id =
              OBJECT_ID('dbo.Usuario_Autorizaciones')
          AND name = 'CK_Usuario_Autorizaciones_Modo'
    )
    BEGIN
        ALTER TABLE dbo.Usuario_Autorizaciones
        ADD CONSTRAINT CK_Usuario_Autorizaciones_Modo
        CHECK (
            ModoAutorizacion IN (
                'ESCALABLE',
                'MANCOMUNADA'
            )
        );
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO
