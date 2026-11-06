/*
EDARSAHUB BOS - HCM Identity Convergence Gate 4
Colaborador -> Gobierno_Persona
DESARROLLO. NO EJECUTAR EN PRODUCCION DESDE ESTE GATE.

Principios:
- Gobierno_Persona es la identidad transversal.
- RH_Colaboradores_Expediente conserva ColaboradorID y compatibilidad legacy.
- PersonaID es nullable durante convergencia.
- Este Gate NO ejecuta backfill.
- Este Gate NO mueve ni elimina PII.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(
        N'dbo.RH_Colaboradores_Expediente',
        N'U'
    ) IS NULL
        THROW 51000,
            'Falta dbo.RH_Colaboradores_Expediente.',
            1;

    IF OBJECT_ID(
        N'dbo.Gobierno_Persona',
        N'U'
    ) IS NULL
        THROW 51000,
            'Falta dbo.Gobierno_Persona BOS canonica.',
            1;

    IF COL_LENGTH(
        N'dbo.RH_Colaboradores_Expediente',
        N'PersonaID'
    ) IS NULL
    BEGIN
        ALTER TABLE dbo.RH_Colaboradores_Expediente
        ADD PersonaID BIGINT NULL;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.foreign_keys
        WHERE parent_object_id =
              OBJECT_ID(N'dbo.RH_Colaboradores_Expediente')
          AND name =
              N'FK_RH_Colaboradores_Expediente_GobiernoPersona'
    )
    BEGIN
        ALTER TABLE dbo.RH_Colaboradores_Expediente
        WITH CHECK
        ADD CONSTRAINT
            FK_RH_Colaboradores_Expediente_GobiernoPersona
        FOREIGN KEY (PersonaID)
        REFERENCES dbo.Gobierno_Persona(PersonaID);

        ALTER TABLE dbo.RH_Colaboradores_Expediente
        CHECK CONSTRAINT
            FK_RH_Colaboradores_Expediente_GobiernoPersona;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE object_id =
              OBJECT_ID(N'dbo.RH_Colaboradores_Expediente')
          AND name =
              N'IX_RH_Colaboradores_Expediente_PersonaID'
    )
    BEGIN
        CREATE INDEX
            IX_RH_Colaboradores_Expediente_PersonaID
        ON dbo.RH_Colaboradores_Expediente(PersonaID)
        WHERE PersonaID IS NOT NULL;
    END;

    /*
    Gate 4 intentionally performs NO backfill.

    Certified Gate 3 evidence:
    - RH_Colaboradores_Expediente: 510 rows
    - Gobierno_Persona: 0 rows
    - PersonaID in RH: absent
    - Duplicate CURP in RH: 0
    - Duplicate RFC in RH: 0
    - 56 colaboradores without CURP
    - 74 colaboradores without RFC
    - 56 without CURP and RFC

    Backfill belongs to a separate Gate.
    */

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
