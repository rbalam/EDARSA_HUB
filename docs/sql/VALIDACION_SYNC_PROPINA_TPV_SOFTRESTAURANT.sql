/* ============================================================
   VALIDACION SYNC PROPINA TPV SOFTRESTAURANT
   No modifica datos.
   ============================================================ */

SET NOCOUNT ON;

PRINT '============================================================';
PRINT '1. Ultima fecha por sistema/unidad en propinas_tpv_control';
PRINT '============================================================';

IF OBJECT_ID('dbo.propinas_tpv_control', 'U') IS NOT NULL
BEGIN
    SELECT
        sistema,
        unidad,
        COUNT(*) AS registros,
        MIN(CAST(fecha AS DATE)) AS fecha_min,
        MAX(CAST(fecha AS DATE)) AS fecha_max,
        SUM(CAST(ISNULL(propinas_tpv, 0) AS DECIMAL(18,2))) AS total_propinas_tpv,
        SUM(CAST(ISNULL(comision, 0) AS DECIMAL(18,2))) AS total_comision,
        SUM(CAST(ISNULL(a_pagar, 0) AS DECIMAL(18,2))) AS total_a_pagar
    FROM dbo.propinas_tpv_control
    GROUP BY sistema, unidad
    ORDER BY sistema, unidad;
END
ELSE
BEGIN
    PRINT 'No existe dbo.propinas_tpv_control';
END;

PRINT '============================================================';
PRINT '2. Ultima fecha SoftRestaurant';
PRINT '============================================================';

IF OBJECT_ID('dbo.propinas_tpv_control', 'U') IS NOT NULL
BEGIN
    SELECT
        sistema,
        unidad,
        COUNT(*) AS registros,
        MAX(CAST(fecha AS DATE)) AS fecha_max
    FROM dbo.propinas_tpv_control
    WHERE UPPER(ISNULL(sistema, '')) LIKE '%SOFT%'
    GROUP BY sistema, unidad
    ORDER BY fecha_max DESC;
END;
