/*
EDARSAHUB — CERTIFICACION HISTORICA COMERCIAL
Fecha: 2026-07-30
Modo: SOLO LECTURA
Objetivo:
  - Determinar cobertura, huecos y duplicados por unidad en la capa canonica.
  - Comparar cobertura de KPI Runtime, KPI Historico, Sync_Sales y Detalle.
  - Preparar certificacion de 130MID, 130QRO, ORIGEN, CIENFUEGOS y ESTELAR.

RESTRICCIONES:
  - No DDL.
  - No DML.
  - No EXEC dinamico.
  - No modifica datos.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'EDARSAHUB'
BEGIN
    THROW 51000, 'Base de datos inesperada. Debe ejecutarse en EDARSAHUB.', 1;
END;

DECLARE @FechaFin DATE = DATEADD(DAY, -1, CAST(GETDATE() AS DATE));

DECLARE @Unidades TABLE (
    unidad_negocio_id VARCHAR(50) NOT NULL PRIMARY KEY,
    sistema_origen VARCHAR(30) NOT NULL
);

INSERT INTO @Unidades (unidad_negocio_id, sistema_origen)
VALUES
    ('130MID', 'SOFTRESTAURANT'),
    ('130QRO', 'MPRO'),
    ('ORIGEN', 'MPRO'),
    ('CIENFUEGOS', 'SOFTRESTAURANT'),
    ('ESTELAR', 'SOFTRESTAURANT');

/* 1. Identidad de ejecucion */
SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    USER_NAME() AS database_user,
    SYSDATETIME() AS fecha_ejecucion,
    @FechaFin AS ultima_fecha_cerrada_objetivo,
    'READ_ONLY' AS modo;

/* 2. Objetos requeridos */
SELECT
    objeto,
    tipo_esperado,
    CASE
        WHEN OBJECT_ID(objeto) IS NULL THEN 'FALTANTE'
        ELSE 'OK'
    END AS estado
FROM (VALUES
    ('dbo.Comercial_KPIs_Diarios_v2', 'USER_TABLE'),
    ('dbo.Comercial_Ventas_Dia_Abiertas_v2', 'USER_TABLE'),
    ('dbo.vw_Comercial_KPIs_Diarios_v2_Runtime', 'VIEW'),
    ('dbo.Sync_Sales', 'USER_TABLE'),
    ('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'USER_TABLE'),
    ('dbo.Sync_PAX_Detalle', 'USER_TABLE')
) x(objeto, tipo_esperado)
ORDER BY objeto;

/* 3. Cobertura de la vista runtime por unidad */
SELECT
    u.unidad_negocio_id,
    u.sistema_origen,
    MIN(k.fecha_operacion) AS fecha_minima,
    MAX(k.fecha_operacion) AS fecha_maxima,
    COUNT(DISTINCT k.fecha_operacion) AS dias_con_datos,
    DATEDIFF(DAY, MIN(k.fecha_operacion), MAX(k.fecha_operacion)) + 1 AS dias_calendario_rango,
    DATEDIFF(DAY, MIN(k.fecha_operacion), MAX(k.fecha_operacion)) + 1
        - COUNT(DISTINCT k.fecha_operacion) AS dias_sin_fila_en_rango,
    SUM(ISNULL(k.ventas_total, 0)) AS ventas_total,
    SUM(ISNULL(k.ventas_sin_propina, 0)) AS ventas_sin_propina,
    SUM(ISNULL(k.propinas_total, 0)) AS propinas_total,
    SUM(ISNULL(k.tickets_total, 0)) AS tickets_total,
    SUM(ISNULL(k.pax_total, 0)) AS pax_total,
    CASE
        WHEN MIN(k.fecha_operacion) IS NULL THEN 'SIN_DATOS'
        WHEN MAX(k.fecha_operacion) < @FechaFin THEN 'REZAGADA'
        WHEN DATEDIFF(DAY, MIN(k.fecha_operacion), MAX(k.fecha_operacion)) + 1
             <> COUNT(DISTINCT k.fecha_operacion) THEN 'CON_HUECOS'
        ELSE 'CONTINUA_EN_RANGO'
    END AS estado_cobertura
FROM @Unidades u
LEFT JOIN dbo.vw_Comercial_KPIs_Diarios_v2_Runtime k
    ON k.unidad_negocio_id = u.unidad_negocio_id
GROUP BY
    u.unidad_negocio_id,
    u.sistema_origen
ORDER BY u.unidad_negocio_id;

/* 4. Duplicados en tabla historica canonica */
SELECT
    k.unidad_negocio_id,
    k.fecha_operacion,
    COUNT(*) AS filas,
    SUM(ISNULL(k.ventas_total, 0)) AS ventas_total_sumadas,
    SUM(ISNULL(k.ventas_sin_propina, 0)) AS ventas_sin_propina_sumadas,
    SUM(ISNULL(k.propinas_total, 0)) AS propinas_sumadas
FROM dbo.Comercial_KPIs_Diarios_v2 k
JOIN @Unidades u
    ON u.unidad_negocio_id = k.unidad_negocio_id
GROUP BY
    k.unidad_negocio_id,
    k.fecha_operacion
HAVING COUNT(*) > 1
ORDER BY
    k.unidad_negocio_id,
    k.fecha_operacion;

/* 5. Huecos de calendario dentro del rango existente por unidad */
;WITH Limites AS (
    SELECT
        k.unidad_negocio_id,
        MIN(k.fecha_operacion) AS fecha_minima,
        MAX(k.fecha_operacion) AS fecha_maxima
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime k
    JOIN @Unidades u
        ON u.unidad_negocio_id = k.unidad_negocio_id
    GROUP BY k.unidad_negocio_id
),
Calendario AS (
    SELECT
        unidad_negocio_id,
        fecha_minima AS fecha
    FROM Limites
    WHERE fecha_minima IS NOT NULL

    UNION ALL

    SELECT
        c.unidad_negocio_id,
        DATEADD(DAY, 1, c.fecha)
    FROM Calendario c
    JOIN Limites l
        ON l.unidad_negocio_id = c.unidad_negocio_id
    WHERE c.fecha < l.fecha_maxima
)
SELECT
    c.unidad_negocio_id,
    c.fecha AS fecha_faltante
FROM Calendario c
LEFT JOIN dbo.vw_Comercial_KPIs_Diarios_v2_Runtime k
    ON k.unidad_negocio_id = c.unidad_negocio_id
   AND k.fecha_operacion = c.fecha
WHERE k.fecha_operacion IS NULL
ORDER BY
    c.unidad_negocio_id,
    c.fecha
OPTION (MAXRECURSION 32767);

/* 6. Coherencia aritmetica de ventas y propinas */
SELECT
    k.unidad_negocio_id,
    k.fecha_operacion,
    k.ventas_total,
    k.ventas_sin_propina,
    k.propinas_total,
    CAST(
        ISNULL(k.ventas_total, 0)
        - ISNULL(k.ventas_sin_propina, 0)
        - ISNULL(k.propinas_total, 0)
        AS DECIMAL(18, 2)
    ) AS diferencia,
    CASE
        WHEN ABS(
            ISNULL(k.ventas_total, 0)
            - ISNULL(k.ventas_sin_propina, 0)
            - ISNULL(k.propinas_total, 0)
        ) <= 0.02 THEN 'OK'
        ELSE 'REVISAR'
    END AS estado
FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime k
JOIN @Unidades u
    ON u.unidad_negocio_id = k.unidad_negocio_id
WHERE ABS(
    ISNULL(k.ventas_total, 0)
    - ISNULL(k.ventas_sin_propina, 0)
    - ISNULL(k.propinas_total, 0)
) > 0.02
ORDER BY
    k.unidad_negocio_id,
    k.fecha_operacion;

/* 7. Cobertura comparativa de fuentes EDARSAHUB */
;WITH Fuentes AS (
    SELECT
        'KPI_RUNTIME' AS fuente,
        unidad_negocio_id,
        fecha_operacion AS fecha
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE unidad_negocio_id IN (
        '130MID', '130QRO', 'ORIGEN', 'CIENFUEGOS', 'ESTELAR'
    )

    UNION ALL

    SELECT
        'KPI_HISTORICO',
        unidad_negocio_id,
        fecha_operacion
    FROM dbo.Comercial_KPIs_Diarios_v2
    WHERE unidad_negocio_id IN (
        '130MID', '130QRO', 'ORIGEN', 'CIENFUEGOS', 'ESTELAR'
    )
)
SELECT
    fuente,
    unidad_negocio_id,
    MIN(fecha) AS fecha_minima,
    MAX(fecha) AS fecha_maxima,
    COUNT(DISTINCT fecha) AS dias_con_datos
FROM Fuentes
GROUP BY
    fuente,
    unidad_negocio_id
ORDER BY
    unidad_negocio_id,
    fuente;

/* 8. Resultado de certificacion interna EDARSAHUB */
;WITH Cobertura AS (
    SELECT
        u.unidad_negocio_id,
        MIN(k.fecha_operacion) AS fecha_minima,
        MAX(k.fecha_operacion) AS fecha_maxima,
        COUNT(DISTINCT k.fecha_operacion) AS dias_con_datos,
        DATEDIFF(DAY, MIN(k.fecha_operacion), MAX(k.fecha_operacion)) + 1 AS dias_rango
    FROM @Unidades u
    LEFT JOIN dbo.vw_Comercial_KPIs_Diarios_v2_Runtime k
        ON k.unidad_negocio_id = u.unidad_negocio_id
    GROUP BY u.unidad_negocio_id
),
Duplicados AS (
    SELECT
        unidad_negocio_id,
        COUNT(*) AS grupos_duplicados
    FROM (
        SELECT
            unidad_negocio_id,
            fecha_operacion
        FROM dbo.Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id IN (
            '130MID', '130QRO', 'ORIGEN', 'CIENFUEGOS', 'ESTELAR'
        )
        GROUP BY
            unidad_negocio_id,
            fecha_operacion
        HAVING COUNT(*) > 1
    ) d
    GROUP BY unidad_negocio_id
)
SELECT
    c.unidad_negocio_id,
    c.fecha_minima,
    c.fecha_maxima,
    c.dias_con_datos,
    c.dias_rango,
    ISNULL(d.grupos_duplicados, 0) AS grupos_duplicados,
    CASE
        WHEN c.fecha_minima IS NULL THEN 'NO_CERTIFICADO_SIN_DATOS'
        WHEN c.fecha_maxima < @FechaFin THEN 'NO_CERTIFICADO_REZAGO'
        WHEN c.dias_con_datos <> c.dias_rango THEN 'NO_CERTIFICADO_HUECOS'
        WHEN ISNULL(d.grupos_duplicados, 0) > 0 THEN 'NO_CERTIFICADO_DUPLICADOS'
        ELSE 'EDARSAHUB_CONTINUO_PENDIENTE_VALIDAR_FECHA_MINIMA_POS'
    END AS estado_certificacion
FROM Cobertura c
LEFT JOIN Duplicados d
    ON d.unidad_negocio_id = c.unidad_negocio_id
ORDER BY c.unidad_negocio_id;
