/*
EDARSAHUB V1.0
Separación de propinas en el overlay de ventas del día.

No crea una segunda tabla.
Amplía dbo.Comercial_Ventas_Dia_Abiertas_v2 y modifica
únicamente las expresiones de propinas de la vista runtime.

Ejecución:
- Solo mediante runner SQL autorizado.
- Debe validarse en EDARSAHUB como HRLectura.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'EDARSAHUB'
BEGIN
    THROW 51000,
        'Base no autorizada. Se esperaba EDARSAHUB.',
        1;
END;

IF UPPER(SUSER_SNAME()) <> N'HRLECTURA'
BEGIN
    THROW 51001,
        'Login no autorizado. Se esperaba HRLectura.',
        1;
END;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(
        N'dbo.Comercial_Ventas_Dia_Abiertas_v2',
        N'U'
    ) IS NULL
    BEGIN
        THROW 51002,
            'No existe Comercial_Ventas_Dia_Abiertas_v2.',
            1;
    END;

    IF COL_LENGTH(
        N'dbo.Comercial_Ventas_Dia_Abiertas_v2',
        N'propinas_abiertas'
    ) IS NULL
    BEGIN
        ALTER TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2
        ADD propinas_abiertas decimal(18,2)
            NOT NULL
            CONSTRAINT DF_ComercialVentasDia_PropinasAbiertas
            DEFAULT (0)
            WITH VALUES;
    END;

    IF COL_LENGTH(
        N'dbo.Comercial_Ventas_Dia_Abiertas_v2',
        N'propinas_cerradas_dia'
    ) IS NULL
    BEGIN
        ALTER TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2
        ADD propinas_cerradas_dia decimal(18,2)
            NOT NULL
            CONSTRAINT DF_ComercialVentasDia_PropinasCerradas
            DEFAULT (0)
            WITH VALUES;
    END;

    IF COL_LENGTH(
        N'dbo.Comercial_Ventas_Dia_Abiertas_v2',
        N'propinas_total'
    ) IS NULL
    BEGIN
        ALTER TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2
        ADD propinas_total decimal(18,2)
            NOT NULL
            CONSTRAINT DF_ComercialVentasDia_PropinasTotal
            DEFAULT (0)
            WITH VALUES;
    END;

    -- 20260729_023 BATCH-SAFE DYNAMIC CHECK
    /*
    La restricción debe compilarse después de agregar las columnas.
    pymssql envía el archivo como un solo lote; una referencia estática
    a las columnas nuevas falla durante la compilación inicial.
    */
    IF NOT EXISTS (
        SELECT 1
        FROM sys.check_constraints
        WHERE parent_object_id = OBJECT_ID(
            N'dbo.Comercial_Ventas_Dia_Abiertas_v2'
        )
          AND name =
              N'CK_ComercialVentasDia_PropinasTotal'
    )
    BEGIN
        EXEC sys.sp_executesql N'
            ALTER TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2
            WITH CHECK
            ADD CONSTRAINT CK_ComercialVentasDia_PropinasTotal
            CHECK (
                propinas_total =
                    propinas_abiertas
                    + propinas_cerradas_dia
            );
        ';
    END;

    IF OBJECT_ID(
        N'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime',
        N'V'
    ) IS NULL
    BEGIN
        THROW 51003,
            'No existe la vista runtime comercial.',
            1;
    END;

    DECLARE @view_definition nvarchar(max) =
        OBJECT_DEFINITION(
            OBJECT_ID(
                N'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime'
            )
        );

    IF NULLIF(@view_definition, N'') IS NULL
    BEGIN
        THROW 51004,
            'No fue posible leer la vista runtime.',
            1;
    END;

    DECLARE @old_overlay_existing nvarchar(max) =
        N'CAST(0 AS decimal(18,2)) ELSE k.propinas_total';

    DECLARE @new_overlay_existing nvarchar(max) =
        N'ISNULL(s.propinas_total, 0) ELSE k.propinas_total';

    DECLARE @old_snapshot_only nvarchar(max) =
        N'CAST(0 AS decimal(18,2)) AS propinas_total';

    DECLARE @new_snapshot_only nvarchar(max) =
        N'ISNULL(s.propinas_total, 0) AS propinas_total';

    IF CHARINDEX(
        @old_overlay_existing,
        @view_definition
    ) > 0
    BEGIN
        SET @view_definition = REPLACE(
            @view_definition,
            @old_overlay_existing,
            @new_overlay_existing
        );
    END
    ELSE IF CHARINDEX(
        @new_overlay_existing,
        @view_definition
    ) = 0
    BEGIN
        THROW 51005,
            'No se encontró la expresión overlay de propinas.',
            1;
    END;

    IF CHARINDEX(
        @old_snapshot_only,
        @view_definition
    ) > 0
    BEGIN
        SET @view_definition = REPLACE(
            @view_definition,
            @old_snapshot_only,
            @new_snapshot_only
        );
    END
    ELSE IF CHARINDEX(
        @new_snapshot_only,
        @view_definition
    ) = 0
    BEGIN
        THROW 51006,
            'No se encontró la expresión snapshot de propinas.',
            1;
    END;

    DECLARE @upper_definition nvarchar(max) =
        UPPER(@view_definition);

    DECLARE @view_name_position int =
        CHARINDEX(
            N'VW_COMERCIAL_KPIS_DIARIOS_V2_RUNTIME',
            @upper_definition
        );

    DECLARE @as_position int =
        CHARINDEX(
            N'AS',
            @upper_definition,
            @view_name_position
            + LEN(
                N'VW_COMERCIAL_KPIS_DIARIOS_V2_RUNTIME'
            )
        );

    IF @view_name_position = 0
       OR @as_position = 0
    BEGIN
        THROW 51007,
            'No se pudo reconstruir el encabezado de la vista.',
            1;
    END;

    SET @view_definition =
        N'CREATE OR ALTER VIEW '
        + N'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime '
        + SUBSTRING(
            @view_definition,
            @as_position,
            LEN(@view_definition)
        );

    EXEC sys.sp_executesql @view_definition;

    EXEC sys.sp_refreshview
        N'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime';

    IF OBJECT_DEFINITION(
        OBJECT_ID(
            N'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime'
        )
    ) NOT LIKE N'%s.propinas_total%'
    BEGIN
        THROW 51008,
            'La vista no publicó propinas del overlay.',
            1;
    END;

    COMMIT TRANSACTION;

    SELECT
        DB_NAME() AS database_name,
        SUSER_SNAME() AS login_name,
        COL_LENGTH(
            N'dbo.Comercial_Ventas_Dia_Abiertas_v2',
            N'propinas_abiertas'
        ) AS propinas_abiertas_column_id,
        COL_LENGTH(
            N'dbo.Comercial_Ventas_Dia_Abiertas_v2',
            N'propinas_cerradas_dia'
        ) AS propinas_cerradas_column_id,
        COL_LENGTH(
            N'dbo.Comercial_Ventas_Dia_Abiertas_v2',
            N'propinas_total'
        ) AS propinas_total_column_id;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
