/*
Migracion: trazabilidad minima para detalle comercial canonico
Tabla: dbo.Comercial_Inteligencia_VentasDetalleProducto

Objetivo:
- Preservar consecutivo / folio.
- Conservar cancelados de SoftRestaurant.
- Conservar estados AC / FA / CA de MPRO.
- Separar filas KPI-validas de filas de trazabilidad.
- Evitar tabla paralela si la tabla canonica existente puede sostener el dato.
*/

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'estado_origen') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD estado_origen nvarchar(20) NULL;
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
    ADD es_kpi_valido bit NOT NULL
        CONSTRAINT DF_Comercial_Intel_VentasDetalle_es_kpi_valido DEFAULT (1);
END
GO

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'folio_origen') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD folio_origen nvarchar(64) NULL;
END
GO

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'documento_origen') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD documento_origen nvarchar(64) NULL;
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
    WHERE name = 'IX_Comercial_Intel_VentasDetalle_KPI'
      AND object_id = OBJECT_ID('dbo.Comercial_Inteligencia_VentasDetalleProducto')
)
BEGIN
    CREATE INDEX IX_Comercial_Intel_VentasDetalle_KPI
    ON dbo.Comercial_Inteligencia_VentasDetalleProducto (
        fecha_operacion,
        unidad_negocio_id,
        sistema_origen,
        es_kpi_valido
    );
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_Comercial_Intel_VentasDetalle_Trazabilidad'
      AND object_id = OBJECT_ID('dbo.Comercial_Inteligencia_VentasDetalleProducto')
)
BEGIN
    CREATE INDEX IX_Comercial_Intel_VentasDetalle_Trazabilidad
    ON dbo.Comercial_Inteligencia_VentasDetalleProducto (
        sistema_origen,
        fecha_operacion,
        numero_ticket,
        estado_origen,
        cancelado_origen
    );
END
GO
