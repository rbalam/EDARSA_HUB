/* ============================================================
   SP de validación de frescura para Inteligencia Comercial.
   No sincroniza, no inserta ventas, no borra datos.
   ============================================================ */
CREATE OR ALTER PROCEDURE dbo.Sp_Validar_Inteligencia_Comercial_Status
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        'Comercial_KPIs_Diarios_v2' AS Fuente,
        MAX(fecha_operacion) AS UltimaFechaOperacion,
        MAX(fecha_sincronizacion) AS UltimaFechaSincronizacion,
        COUNT(*) AS Registros
    FROM dbo.Comercial_KPIs_Diarios_v2
    WHERE ISNULL(activo, 1) = 1

    UNION ALL

    SELECT
        'Comercial_Ventas_Dia_Abiertas_v2' AS Fuente,
        MAX(fecha_operacion) AS UltimaFechaOperacion,
        MAX(fecha_ultima_actualizacion) AS UltimaFechaSincronizacion,
        COUNT(*) AS Registros
    FROM dbo.Comercial_Ventas_Dia_Abiertas_v2

    UNION ALL

    SELECT
        'Sync_PAX_Detalle' AS Fuente,
        MAX(FechaOperacion) AS UltimaFechaOperacion,
        MAX(FechaSync) AS UltimaFechaSincronizacion,
        COUNT(*) AS Registros
    FROM dbo.Sync_PAX_Detalle

    UNION ALL

    SELECT
        'Sync_Sales' AS Fuente,
        CAST(MAX(FechaHora) AS DATE) AS UltimaFechaOperacion,
        MAX(last_modified) AS UltimaFechaSincronizacion,
        COUNT(*) AS Registros
    FROM dbo.Sync_Sales;
END;
GO
