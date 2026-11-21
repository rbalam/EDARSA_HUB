/*
  EDARSAHUB V1.0
  Comercial - mesa/referencia del Ticket de Venta.

  Objetivo:
  - Persistir la mesa/referencia del POS en EDARSAHUB.
  - Mantener el Ticket de Venta NO-LIVE.
  - SoftRestaurant: MESA.
  - ManagementPro: Comanda.Co_Referencia.
  - No recalcular KPIs ni tocar Produccion.
*/

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'mesa') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD mesa nvarchar(100) NULL;
END
GO
