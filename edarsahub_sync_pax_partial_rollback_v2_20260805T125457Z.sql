/*
EDARSAHUB - REFERENCIA DE RESTAURACION
NO EJECUTAR AUTOMATICAMENTE.

Contiene exactamente las tres filas auditadas antes
de la limpieza controlada.
*/

INSERT INTO dbo.Sync_PAX_Detalle (
    [PAXRegistroID], [ServerID], [SucursalID], [SucursalNombre], [FechaOperacion], [FechaHora], [CuentaID], [CuentaFolio], [MesaNumero], [MeseroID], [MeseroNombre], [NumeroComensales], [TipoPAX], [VentaCuenta], [ConsumoPromedioPAX], [TiempoMesa], [HoraEntrada], [HoraSalida], [Turno], [DiaSemana], [FechaSync]
)
VALUES
    (N'379ef2b96dda3f4234b9290ac44c1ad9a65c1d0486251ce12c', N'a5ff0e25-f029-43db-b634-d4ac814c904f', N'DEFAULT', N'LA ESTELAR', N'2026-08-04', N'2026-08-05 05:47:16.5020000', NULL, NULL, NULL, NULL, NULL, 2, N'NORMAL', 603.00, 301.50, 0, NULL, NULL, NULL, NULL, N'2026-08-05 05:47:16.5200000'),
    (N'55708f66125c132d622b946c2fbff726301594ca2f6a4a6d24', N'a5547321-1139-4d2b-9d53-182ca737b6b6', N'DEFAULT', N'130° MERIDA', N'2026-08-04', N'2026-08-05 05:47:16.2320000', NULL, NULL, NULL, NULL, NULL, 0, N'NORMAL', 0.00, 0.00, 0, NULL, NULL, NULL, NULL, N'2026-08-05 05:47:16.2500000'),
    (N'c0460e55b20fd4430c5b3268fb07c587d44151b32e3c2e917b', N'6d053c22-523e-48c0-b72b-96081e2d781b', N'DEFAULT', N'CIENFUEGOS', N'2026-08-04', N'2026-08-05 05:47:16.3710000', NULL, NULL, NULL, NULL, NULL, 1, N'NORMAL', 10000.00, 10000.00, 0, NULL, NULL, NULL, NULL, N'2026-08-05 05:47:16.3900000');
