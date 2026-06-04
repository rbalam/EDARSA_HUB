/* ============================================================
   CIERRE P0 - VALIDACION PROPINA TPV SOFTRESTAURANT
   No modifica datos.
   ============================================================ */

SET NOCOUNT ON;

PRINT '============================================================';
PRINT '1. RESUMEN SOFTRESTAURANT POR UNIDAD';
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
    WHERE
        UPPER(ISNULL(sistema, '')) LIKE '%SOFT%'
        OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT%'
        OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT_PRO%'
    GROUP BY sistema, unidad
    ORDER BY unidad;
END
ELSE
BEGIN
    PRINT 'No existe dbo.propinas_tpv_control';
END;


PRINT '============================================================';
PRINT '2. RESUMEN BACKFILL DESDE 2026-05-18';
PRINT '============================================================';

IF OBJECT_ID('dbo.propinas_tpv_control', 'U') IS NOT NULL
BEGIN
    SELECT
        unidad,
        COUNT(*) AS registros,
        MIN(CAST(fecha AS DATE)) AS fecha_min,
        MAX(CAST(fecha AS DATE)) AS fecha_max,
        SUM(CAST(ISNULL(propinas_tpv, 0) AS DECIMAL(18,2))) AS total_propinas_tpv,
        SUM(CAST(ISNULL(comision, 0) AS DECIMAL(18,2))) AS total_comision,
        SUM(CAST(ISNULL(a_pagar, 0) AS DECIMAL(18,2))) AS total_a_pagar
    FROM dbo.propinas_tpv_control
    WHERE CAST(fecha AS DATE) >= '2026-05-18'
      AND (
            UPPER(ISNULL(sistema, '')) LIKE '%SOFT%'
         OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT%'
         OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT_PRO%'
      )
      AND (
            UPPER(ISNULL(unidad, '')) LIKE '%130%'
         OR UPPER(ISNULL(unidad, '')) LIKE '%MERIDA%'
         OR UPPER(ISNULL(unidad, '')) LIKE '%MID%'
         OR UPPER(ISNULL(unidad, '')) LIKE '%CIENFUEGOS%'
         OR UPPER(ISNULL(unidad, '')) LIKE '%ESTELAR%'
      )
    GROUP BY unidad
    ORDER BY unidad;

    SELECT
        COUNT(*) AS registros_total,
        MIN(CAST(fecha AS DATE)) AS fecha_min,
        MAX(CAST(fecha AS DATE)) AS fecha_max,
        SUM(CAST(ISNULL(propinas_tpv, 0) AS DECIMAL(18,2))) AS total_propinas_tpv,
        SUM(CAST(ISNULL(comision, 0) AS DECIMAL(18,2))) AS total_comision,
        SUM(CAST(ISNULL(a_pagar, 0) AS DECIMAL(18,2))) AS total_a_pagar
    FROM dbo.propinas_tpv_control
    WHERE CAST(fecha AS DATE) >= '2026-05-18'
      AND (
            UPPER(ISNULL(sistema, '')) LIKE '%SOFT%'
         OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT%'
         OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT_PRO%'
      )
      AND (
            UPPER(ISNULL(unidad, '')) LIKE '%130%'
         OR UPPER(ISNULL(unidad, '')) LIKE '%MERIDA%'
         OR UPPER(ISNULL(unidad, '')) LIKE '%MID%'
         OR UPPER(ISNULL(unidad, '')) LIKE '%CIENFUEGOS%'
         OR UPPER(ISNULL(unidad, '')) LIKE '%ESTELAR%'
      );
END;


PRINT '============================================================';
PRINT '3. VALIDACION POR FECHA DESDE 2026-05-18';
PRINT '============================================================';

IF OBJECT_ID('dbo.propinas_tpv_control', 'U') IS NOT NULL
BEGIN
    SELECT
        CAST(fecha AS DATE) AS fecha,
        sistema,
        unidad,
        COUNT(*) AS registros,
        SUM(CAST(ISNULL(propinas_tpv, 0) AS DECIMAL(18,2))) AS total_propinas_tpv,
        SUM(CAST(ISNULL(comision, 0) AS DECIMAL(18,2))) AS total_comision,
        SUM(CAST(ISNULL(a_pagar, 0) AS DECIMAL(18,2))) AS total_a_pagar
    FROM dbo.propinas_tpv_control
    WHERE CAST(fecha AS DATE) >= '2026-05-18'
      AND (
            UPPER(ISNULL(sistema, '')) LIKE '%SOFT%'
         OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT%'
         OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT_PRO%'
      )
    GROUP BY CAST(fecha AS DATE), sistema, unidad
    ORDER BY fecha DESC, unidad;
END;


PRINT '============================================================';
PRINT '4. COMPARATIVO MPRO VS SOFTRESTAURANT';
PRINT '============================================================';

IF OBJECT_ID('dbo.propinas_tpv_control', 'U') IS NOT NULL
BEGIN
    SELECT
        CASE
            WHEN UPPER(ISNULL(sistema, '')) LIKE '%MPRO%'
              OR UPPER(ISNULL(sistema, '')) LIKE '%MANAGEMENT%'
                THEN 'MPRO'
            WHEN UPPER(ISNULL(sistema, '')) LIKE '%SOFT%'
              OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT%'
              OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT_PRO%'
                THEN 'SOFTRESTAURANT_PRO'
            ELSE ISNULL(sistema, 'SIN_SISTEMA')
        END AS sistema_canonico,
        COUNT(*) AS registros,
        MIN(CAST(fecha AS DATE)) AS fecha_min,
        MAX(CAST(fecha AS DATE)) AS fecha_max,
        SUM(CAST(ISNULL(propinas_tpv, 0) AS DECIMAL(18,2))) AS total_propinas_tpv
    FROM dbo.propinas_tpv_control
    GROUP BY
        CASE
            WHEN UPPER(ISNULL(sistema, '')) LIKE '%MPRO%'
              OR UPPER(ISNULL(sistema, '')) LIKE '%MANAGEMENT%'
                THEN 'MPRO'
            WHEN UPPER(ISNULL(sistema, '')) LIKE '%SOFT%'
              OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT%'
              OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT_PRO%'
                THEN 'SOFTRESTAURANT_PRO'
            ELSE ISNULL(sistema, 'SIN_SISTEMA')
        END
    ORDER BY sistema_canonico;
END;


PRINT '============================================================';
PRINT '5. SERVIDORES SOFTRESTAURANT REGISTRADOS';
PRINT '============================================================';

IF OBJECT_ID('dbo.vw_Servidores_Conexiones_Versiones', 'V') IS NOT NULL
BEGIN
    SELECT
        servidor_conexion_id,
        nombre,
        tipo_sistema,
        host,
        database_name,
        activo,
        visible_en_operaciones,
        sistema_version_id,
        version_sistema
    FROM dbo.vw_Servidores_Conexiones_Versiones
    WHERE
        UPPER(ISNULL(tipo_sistema, '')) LIKE '%SOFT%'
        OR UPPER(ISNULL(nombre, '')) LIKE '%SOFT%'
        OR UPPER(ISNULL(nombre_sistema, '')) LIKE '%SOFT%'
    ORDER BY nombre;
END;


PRINT '============================================================';
PRINT '6. DICTAMEN AUTOMATICO';
PRINT '============================================================';

IF OBJECT_ID('dbo.propinas_tpv_control', 'U') IS NOT NULL
BEGIN
    DECLARE @Registros INT;
    DECLARE @Total DECIMAL(18,2);
    DECLARE @FechaMax DATE;

    SELECT
        @Registros = COUNT(*),
        @Total = SUM(CAST(ISNULL(propinas_tpv, 0) AS DECIMAL(18,2))),
        @FechaMax = MAX(CAST(fecha AS DATE))
    FROM dbo.propinas_tpv_control
    WHERE CAST(fecha AS DATE) >= '2026-05-18'
      AND (
            UPPER(ISNULL(sistema, '')) LIKE '%SOFT%'
         OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT%'
         OR UPPER(ISNULL(sistema, '')) LIKE '%SOFTRESTAURANT_PRO%'
      );

    SELECT
        @Registros AS registros_backfill_softrestaurant,
        @Total AS total_propinas_tpv_backfill,
        @FechaMax AS fecha_maxima_backfill,
        CASE
            WHEN @Registros > 0 AND @Total > 0 THEN 'P0_OPERATIVO_VALIDADO'
            ELSE 'P0_NO_VALIDADO'
        END AS dictamen;
END;
