/* EDARSAHUB - Cavas Gate 12E - BOS Persona link. DESARROLLO. NO EJECUTAR EN PRODUCCION. */
SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.CavaSocios_Socios', N'U') IS NULL
        THROW 51000, 'Falta dbo.CavaSocios_Socios.', 1;
    IF OBJECT_ID(N'dbo.Gobierno_Persona', N'U') IS NULL
        THROW 51000, 'Falta dbo.Gobierno_Persona BOS canonica.', 1;

    IF COL_LENGTH(N'dbo.CavaSocios_Socios', N'PersonaID') IS NULL
    BEGIN
        ALTER TABLE dbo.CavaSocios_Socios ADD PersonaID BIGINT NULL;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.foreign_keys
        WHERE parent_object_id = OBJECT_ID(N'dbo.CavaSocios_Socios')
          AND name = N'FK_CavaSocios_Socios_GobiernoPersona'
    )
    BEGIN
        ALTER TABLE dbo.CavaSocios_Socios WITH CHECK
        ADD CONSTRAINT FK_CavaSocios_Socios_GobiernoPersona
            FOREIGN KEY (PersonaID) REFERENCES dbo.Gobierno_Persona(PersonaID);
        ALTER TABLE dbo.CavaSocios_Socios CHECK CONSTRAINT FK_CavaSocios_Socios_GobiernoPersona;
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.CavaSocios_Socios')
          AND name = N'IX_CavaSocios_Socios_PersonaID'
    )
    BEGIN
        CREATE INDEX IX_CavaSocios_Socios_PersonaID
        ON dbo.CavaSocios_Socios(PersonaID)
        WHERE PersonaID IS NOT NULL;
    END;

    /* Gate 12E intentionally performs NO backfill.
       Certified audit: 2 socios, 0 deterministic identity matches.
       Unresolved socios remain PersonaID NULL. */

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
