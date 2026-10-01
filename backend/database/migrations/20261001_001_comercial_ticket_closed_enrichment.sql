/*
  EDARSAHUB V1.0
  Comercial - enriquecimiento de Ticket de Venta cerrado.

  Objetivo:
  - Persistir vendedor/mesero ya disponible en el POS al sincronizar detalle cerrado.
  - Persistir porcentaje de descuento por linea/grupo de producto.
  - Permitir mas de una banda de descuento del mismo producto en un ticket.
  - No recalcular KPIs ni tocar Produccion.
*/

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'vendedor_id') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD vendedor_id nvarchar(100) NULL;
END
GO

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'vendedor_nombre') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD vendedor_nombre nvarchar(200) NULL;
END
GO

IF COL_LENGTH('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'descuento_pct') IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto
    ADD descuento_pct decimal(9,4) NULL;
END
GO

IF EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID('dbo.Comercial_Inteligencia_VentasDetalleProducto')
      AND name = 'UX_Comercial_Intel_VentasDetalle_NoDup'
)
BEGIN
    DROP INDEX UX_Comercial_Intel_VentasDetalle_NoDup
    ON dbo.Comercial_Inteligencia_VentasDetalleProducto;
END
GO

CREATE UNIQUE INDEX UX_Comercial_Intel_VentasDetalle_NoDup
ON dbo.Comercial_Inteligencia_VentasDetalleProducto(
    id_transaccion,
    numero_ticket,
    producto_codigo_fuente,
    descuento_pct,
    fecha_operacion
);
GO
