-- Ticket fiscal header fields: additive extension only.
-- Does not recalculate KPIs and does not alter sync semantics.
SET XACT_ABORT ON;
BEGIN TRANSACTION;

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'ticket_subtotal') IS NULL
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD ticket_subtotal decimal(18,4) NULL;

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'ticket_impuesto') IS NULL
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD ticket_impuesto decimal(18,4) NULL;

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'ticket_total') IS NULL
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD ticket_total decimal(18,4) NULL;

COMMIT TRANSACTION;
GO
