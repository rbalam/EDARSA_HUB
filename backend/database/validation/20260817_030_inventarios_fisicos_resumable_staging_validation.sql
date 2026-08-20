SET NOCOUNT ON;

DECLARE @errors int = 0;

IF OBJECT_ID(
    'dbo.Compras_Inventarios_Fisicos_SyncRuns',
    'U'
) IS NULL
BEGIN
    PRINT 'ERROR=SYNC_RUNS_TABLE_MISSING';
    SET @errors += 1;
END;

IF OBJECT_ID(
    'dbo.Compras_Inventarios_Fisicos_Stage',
    'U'
) IS NULL
BEGIN
    PRINT 'ERROR=HEADER_STAGE_TABLE_MISSING';
    SET @errors += 1;
END;

IF OBJECT_ID(
    'dbo.Compras_Inventarios_Fisicos_Detalle_Stage',
    'U'
) IS NULL
BEGIN
    PRINT 'ERROR=DETAIL_STAGE_TABLE_MISSING';
    SET @errors += 1;
END;

IF OBJECT_ID(
    'dbo.Compras_Inventarios_Fisicos_SyncRuns',
    'U'
) IS NOT NULL
AND NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id =
        OBJECT_ID(
            'dbo.Compras_Inventarios_Fisicos_SyncRuns'
        )
      AND name = 'IX_CIFSR_UnidadStatus'
)
BEGIN
    PRINT 'ERROR=SYNC_RUNS_INDEX_MISSING';
    SET @errors += 1;
END;

IF OBJECT_ID(
    'dbo.Compras_Inventarios_Fisicos_Stage',
    'U'
) IS NOT NULL
AND NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id =
        OBJECT_ID(
            'dbo.Compras_Inventarios_Fisicos_Stage'
        )
      AND name = 'IX_CIFS_Run'
)
BEGIN
    PRINT 'ERROR=HEADER_STAGE_INDEX_MISSING';
    SET @errors += 1;
END;

IF OBJECT_ID(
    'dbo.Compras_Inventarios_Fisicos_Detalle_Stage',
    'U'
) IS NOT NULL
AND NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id =
        OBJECT_ID(
            'dbo.Compras_Inventarios_Fisicos_Detalle_Stage'
        )
      AND name = 'IX_CIFDS_RunFolio'
)
BEGIN
    PRINT 'ERROR=DETAIL_STAGE_INDEX_MISSING';
    SET @errors += 1;
END;

IF @errors <> 0
BEGIN
    THROW 51010,
        'Validacion staging inventarios fisicos fallo',
        1;
END;

PRINT 'INVENTARIOS_RESUMABLE_STAGING_SCHEMA_OK=1';
