SET XACT_ABORT ON;
SET NOCOUNT ON;

IF COL_LENGTH('dbo.Comercial_Ventas_Dia_Abiertas_v2', 'detalle_abiertas_json') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2
    ADD detalle_abiertas_json NVARCHAR(MAX) NULL;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE name = 'CK_Comercial_Ventas_Dia_Abiertas_v2_DetalleJson'
      AND parent_object_id = OBJECT_ID('dbo.Comercial_Ventas_Dia_Abiertas_v2')
)
BEGIN
    EXEC(N'
        ALTER TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2 WITH NOCHECK
        ADD CONSTRAINT CK_Comercial_Ventas_Dia_Abiertas_v2_DetalleJson
        CHECK (
            detalle_abiertas_json IS NULL
            OR ISJSON(detalle_abiertas_json) = 1
        );
    ');
END;
