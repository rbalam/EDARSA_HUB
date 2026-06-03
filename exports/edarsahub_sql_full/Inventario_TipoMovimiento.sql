-- Inventario_TipoMovimiento - 6 registros
INSERT INTO [Inventario_TipoMovimiento] ([TipoMovimientoID], [Codigo], [Descripcion], [Naturaleza], [AfectaCostoPromedio], [Activo]) VALUES (1, N'ENTRADA_COMPRA', N'Entrada por recepción de compra', N'E', 1, 1);
INSERT INTO [Inventario_TipoMovimiento] ([TipoMovimientoID], [Codigo], [Descripcion], [Naturaleza], [AfectaCostoPromedio], [Activo]) VALUES (2, N'SALIDA_DEV_PROV', N'Salida por devolución a proveedor', N'S', 1, 1);
INSERT INTO [Inventario_TipoMovimiento] ([TipoMovimientoID], [Codigo], [Descripcion], [Naturaleza], [AfectaCostoPromedio], [Activo]) VALUES (3, N'AJUSTE_ENTRADA', N'Ajuste de inventario de entrada', N'E', 1, 1);
INSERT INTO [Inventario_TipoMovimiento] ([TipoMovimientoID], [Codigo], [Descripcion], [Naturaleza], [AfectaCostoPromedio], [Activo]) VALUES (4, N'AJUSTE_SALIDA', N'Ajuste de inventario de salida', N'S', 1, 1);
INSERT INTO [Inventario_TipoMovimiento] ([TipoMovimientoID], [Codigo], [Descripcion], [Naturaleza], [AfectaCostoPromedio], [Activo]) VALUES (5, N'TRASPASO_ENTRADA', N'Entrada por traspaso', N'E', 0, 1);
INSERT INTO [Inventario_TipoMovimiento] ([TipoMovimientoID], [Codigo], [Descripcion], [Naturaleza], [AfectaCostoPromedio], [Activo]) VALUES (6, N'TRASPASO_SALIDA', N'Salida por traspaso', N'S', 0, 1);
