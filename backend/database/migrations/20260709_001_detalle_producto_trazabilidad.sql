/*
  EDARSAHUB V1.0
  Comercial Inteligencia - trazabilidad de cancelados sin tabla paralela.

  Objetivo:
  - Preservar cancelados/consecutivos.
  - Separar filas KPI validas de filas de trazabilidad.
  - Evitar ADD NOT NULL pesado sobre tabla con datos.
*/

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'estado_origen') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD estado_origen nvarchar(50) NULL;
END
GO

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'cancelado_origen') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD cancelado_origen bit NULL;
END
GO

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'es_kpi_valido') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD es_kpi_valido bit NULL;
END
GO

WHILE 1 = 1
BEGIN
    UPDATE TOP (50000) dbo.Comercial_Inteligencia_VentasDetalleProducto
    SET es_kpi_valido = 1
    WHERE es_kpi_valido IS NULL;

    IF @@ROWCOUNT = 0
        BREAK;
END
GO

IF EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.Comercial_Inteligencia_VentasDetalleProducto')
      AND name = 'es_kpi_valido'
      AND is_nullable = 1
)
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ALTER COLUMN es_kpi_valido bit NOT NULL;
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    JOIN sys.columns c
      ON c.object_id = dc.parent_object_id
     AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID('dbo.Comercial_Inteligencia_VentasDetalleProducto')
      AND c.name = 'es_kpi_valido'
)
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD CONSTRAINT DF_Comercial_Intel_VentasDetalle_es_kpi_valido
    DEFAULT (1) FOR es_kpi_valido;
END
GO

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'folio_origen') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD folio_origen nvarchar(100) NULL;
END
GO

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'documento_origen') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD documento_origen nvarchar(100) NULL;
END
GO

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'fuente_original') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD fuente_original nvarchar(50) NULL;
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID('dbo.Comercial_Inteligencia_VentasDetalleProducto')
      AND name = 'IX_Comercial_Intel_VentasDetalle_KPI'
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_Comercial_Intel_VentasDetalle_KPI
    ON dbo.Comercial_Inteligencia_VentasDetalleProducto (
        es_kpi_valido,
        fecha_operacion,
        unidad_negocio_id
    );
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID('dbo.Comercial_Inteligencia_VentasDetalleProducto')
      AND name = 'IX_Comercial_Intel_VentasDetalle_Trazabilidad'
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_Comercial_Intel_VentasDetalle_Trazabilidad
    ON dbo.Comercial_Inteligencia_VentasDetalleProducto (
        fuente_original,
        estado_origen,
        folio_origen,
        documento_origen
    );
END
GO
