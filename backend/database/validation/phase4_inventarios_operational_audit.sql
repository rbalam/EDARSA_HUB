/*
Fase 4 Inventarios - auditoria operacional.

Solo lectura. Objetivo:
- Confirmar servidores productivos mapeados a unidad.
- Medir desface de Compras_Inventarios_Fisicos_Sync por unidad.
- Ver ultimo log de sync de INVENTARIOS.
- Ver si el detector automatico ya escribio Scheduler_InventariosProcesados.
*/

SET NOCOUNT ON;
GO

WITH servidores AS (
    SELECT
        CAST(s.id AS VARCHAR(50)) AS server_id,
        s.nombre AS server_name,
        s.system_type,
        u.id AS unidad_negocio_id,
        u.codigo AS unidad_codigo,
        u.nombre AS unidad_nombre
    FROM dbo.Servidores_Conexiones s
    INNER JOIN dbo.Unidades_Negocio u
        ON u.server_id = CAST(s.id AS NVARCHAR(36))
    WHERE s.activo = 1
      AND s.tipo_conexion IN ('SQL_SERVER', 'DATA_SOURCE')
      AND UPPER(LTRIM(RTRIM(s.system_type))) IN (
          'SOFTRESTAURANT', 'SOFTRESTAURANT_PRO', 'SOFTRESTAURANTPRO', 'SR',
          'MPRO', 'MANAGEMENTPRO', 'MANAGMENTPRO'
      )
)
SELECT
    unidad_codigo,
    unidad_nombre,
    server_name,
    server_id,
    system_type
FROM servidores
ORDER BY unidad_codigo, server_name;
GO

WITH inv AS (
    SELECT
        unidad_negocio_codigo,
        server_id,
        COUNT(*) AS filas_sync,
        COUNT(DISTINCT folio) AS folios_distintos,
        COUNT(DISTINCT almacen_id) AS almacenes_distintos,
        MAX(fecha) AS fecha_inventario_max,
        MAX(sync_timestamp) AS sync_timestamp_max,
        SUM(CASE WHEN CAST(fecha AS date) = CAST(GETDATE() AS date) THEN 1 ELSE 0 END) AS filas_inventario_hoy,
        SUM(CASE WHEN sync_status = 'ACTIVE' THEN 1 ELSE 0 END) AS filas_active,
        SUM(CASE WHEN sync_status = 'REPLACED' THEN 1 ELSE 0 END) AS filas_replaced
    FROM dbo.Compras_Inventarios_Fisicos_Sync
    GROUP BY unidad_negocio_codigo, server_id
)
SELECT
    s.unidad_codigo,
    s.server_name,
    s.system_type,
    ISNULL(inv.filas_sync, 0) AS filas_sync,
    ISNULL(inv.folios_distintos, 0) AS folios_distintos,
    ISNULL(inv.almacenes_distintos, 0) AS almacenes_distintos,
    inv.fecha_inventario_max,
    DATEDIFF(DAY, CAST(inv.fecha_inventario_max AS date), CAST(GETDATE() AS date)) AS dias_desfase_inventario,
    inv.sync_timestamp_max,
    DATEDIFF(HOUR, inv.sync_timestamp_max, GETDATE()) AS horas_desfase_sync,
    ISNULL(inv.filas_inventario_hoy, 0) AS filas_inventario_hoy,
    ISNULL(inv.filas_active, 0) AS filas_active,
    ISNULL(inv.filas_replaced, 0) AS filas_replaced,
    CASE
        WHEN inv.fecha_inventario_max IS NULL THEN 'SIN_SYNC'
        WHEN CAST(inv.fecha_inventario_max AS date) < CAST(GETDATE() AS date) THEN 'DESFASADO_FECHA_INVENTARIO'
        WHEN inv.sync_timestamp_max < DATEADD(HOUR, -2, GETDATE()) THEN 'DESFASADO_SYNC'
        ELSE 'OK'
    END AS estado_operacional
FROM (
    SELECT
        CAST(s.id AS VARCHAR(50)) AS server_id,
        s.nombre AS server_name,
        s.system_type,
        u.codigo AS unidad_codigo
    FROM dbo.Servidores_Conexiones s
    INNER JOIN dbo.Unidades_Negocio u
        ON u.server_id = CAST(s.id AS NVARCHAR(36))
    WHERE s.activo = 1
      AND s.tipo_conexion IN ('SQL_SERVER', 'DATA_SOURCE')
      AND UPPER(LTRIM(RTRIM(s.system_type))) IN (
          'SOFTRESTAURANT', 'SOFTRESTAURANT_PRO', 'SOFTRESTAURANTPRO', 'SR',
          'MPRO', 'MANAGEMENTPRO', 'MANAGMENTPRO'
      )
) s
LEFT JOIN inv
    ON LOWER(inv.server_id) = LOWER(s.server_id)
   AND inv.unidad_negocio_codigo = s.unidad_codigo
ORDER BY estado_operacional DESC, s.unidad_codigo;
GO

WITH logs AS (
    SELECT
        l.*,
        u.codigo AS unidad_codigo,
        s.nombre AS server_name,
        ROW_NUMBER() OVER (
            PARTITION BY l.server_id, l.unidad_negocio_id
            ORDER BY l.created_at DESC, l.id DESC
        ) AS rn
    FROM dbo.Compras_Sync_Log l
    LEFT JOIN dbo.Unidades_Negocio u
        ON CONVERT(NVARCHAR(36), u.id) = CONVERT(NVARCHAR(36), l.unidad_negocio_id)
    LEFT JOIN dbo.Servidores_Conexiones s
        ON CONVERT(NVARCHAR(36), s.id) = CONVERT(NVARCHAR(36), l.server_id)
    WHERE l.sync_type = 'INVENTARIOS'
)
SELECT
    unidad_codigo,
    server_name,
    server_id,
    sync_start,
    sync_end,
    records_synced,
    status,
    LEFT(CONVERT(NVARCHAR(MAX), error_message), 300) AS error_message,
    created_at
FROM logs
WHERE rn = 1
ORDER BY created_at DESC;
GO

SELECT
    SistemaOrigen,
    ServerID,
    SucursalID,
    AlmacenID,
    Estado,
    COUNT(*) AS registros,
    MIN(FechaDeteccion) AS primera_deteccion,
    MAX(FechaDeteccion) AS ultima_deteccion,
    MAX(FechaProcesamiento) AS ultimo_procesamiento
FROM dbo.Scheduler_InventariosProcesados
GROUP BY SistemaOrigen, ServerID, SucursalID, AlmacenID, Estado
ORDER BY ultima_deteccion DESC, SistemaOrigen, ServerID, AlmacenID;
GO

SELECT
    s.nombre AS server_name,
    CAST(s.id AS VARCHAR(50)) AS server_id,
    s.system_type,
    s.tipo_conexion,
    'SERVIDOR_ACTIVO_SIN_UNIDAD_NEGOCIO' AS hallazgo
FROM dbo.Servidores_Conexiones s
LEFT JOIN dbo.Unidades_Negocio u
    ON u.server_id = CAST(s.id AS NVARCHAR(36))
WHERE s.activo = 1
  AND s.tipo_conexion IN ('SQL_SERVER', 'DATA_SOURCE')
  AND UPPER(LTRIM(RTRIM(s.system_type))) IN (
      'SOFTRESTAURANT', 'SOFTRESTAURANT_PRO', 'SOFTRESTAURANTPRO', 'SR',
      'MPRO', 'MANAGEMENTPRO', 'MANAGMENTPRO'
  )
  AND u.id IS NULL
ORDER BY s.system_type, s.nombre;
GO
