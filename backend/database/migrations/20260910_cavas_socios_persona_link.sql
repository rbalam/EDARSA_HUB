/*
EDARSAHUB - CAVAS CORPORATIVAS - GATE 12G
Relacion canonica Membresia Cava -> Gobierno_Persona

ESTE ARTEFACTO NO SE EJECUTA EN GATE 12G.

Decisiones:
- Gobierno_Persona.PersonaID es la identidad fisica BOS.
- CavaSocios_Socios.SocioID permanece como PK de membresia.
- NO se agrega ClienteID a CavaSocios_Socios.
- PersonaID inicia NULL.
- NO hay backfill automatico.
- NO se modifican Botellas, Cargos ni Movimientos.
- NO se eliminan campos legacy.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.CavaSocios_Socios', N'U') IS NULL
        THROW 51000, 'CavaSocios_Socios no existe', 1;

    IF OBJECT_ID(N'dbo.Gobierno_Persona', N'U') IS NULL
        THROW 51001, 'Gobierno_Persona no existe', 1;

    IF COL_LENGTH(N'dbo.CavaSocios_Socios', N'PersonaID') IS NULL
    BEGIN
        ALTER TABLE dbo.CavaSocios_Socios
        ADD PersonaID bigint NULL;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.foreign_keys
        WHERE parent_object_id = OBJECT_ID(N'dbo.CavaSocios_Socios')
          AND referenced_object_id = OBJECT_ID(N'dbo.Gobierno_Persona')
          AND name = N'FK_CavaSocios_Socios_GobiernoPersona'
    )
    BEGIN
        EXEC sys.sp_executesql N'
            ALTER TABLE dbo.CavaSocios_Socios
            ADD CONSTRAINT FK_CavaSocios_Socios_GobiernoPersona
            FOREIGN KEY (PersonaID)
            REFERENCES dbo.Gobierno_Persona(PersonaID);
        ';
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.CavaSocios_Socios')
          AND name = N'IX_CavaSocios_Socios_PersonaID'
    )
    BEGIN
        EXEC sys.sp_executesql N'
            CREATE INDEX IX_CavaSocios_Socios_PersonaID
            ON dbo.CavaSocios_Socios(PersonaID)
            WHERE PersonaID IS NOT NULL;
        ';
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
