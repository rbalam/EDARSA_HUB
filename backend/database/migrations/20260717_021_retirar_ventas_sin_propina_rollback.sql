/*
Rollback de esquema para 20260717_021.

No reconstruye valores legacy: las columnas se restauran NULL y sin uso público.
No modifica backups ni datos históricos existentes.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'EDARSAHUB'
BEGIN
    THROW 51300, 'Base no autorizada. Se esperaba EDARSAHUB.', 1;
END;

THROW 51310,
    'Rollback 021 no disponible: la migración física permanece diferida.',
    1;

/* BLOQUE DIFERIDO: no ejecutar.
BEGIN TRANSACTION;

IF COL_LENGTH(
    N'dbo.Comercial_KPIs_Diarios_v2',
    N'ventas_sin_propina'
) IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_KPIs_Diarios_v2
    ADD ventas_sin_propina decimal(18,2) NULL;
END;

IF COL_LENGTH(
    N'dbo.Comercial_KPIs_Mensuales_v2',
    N'ventas_sin_propina'
) IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_KPIs_Mensuales_v2
    ADD ventas_sin_propina decimal(18,2) NULL;
END;

COMMIT TRANSACTION;

SELECT
    OBJECT_SCHEMA_NAME(column_object.object_id) AS schema_name,
    OBJECT_NAME(column_object.object_id) AS table_name,
    column_object.name AS column_name,
    TYPE_NAME(column_object.user_type_id) AS data_type,
    column_object.precision,
    column_object.scale,
    column_object.is_nullable
FROM sys.columns column_object
WHERE column_object.object_id IN (
        OBJECT_ID(N'dbo.Comercial_KPIs_Diarios_v2'),
        OBJECT_ID(N'dbo.Comercial_KPIs_Mensuales_v2')
    )
  AND column_object.name = N'ventas_sin_propina'
ORDER BY table_name;
*/
