# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-30T14:55:06.895291
- Modo: `validate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/Users/ricardobalamgarcia/Documents/v1.0/EDARSA_HUB_work/backend/database/validation/phase4_inventarios_operational_audit.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 6
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: Comando
- Filas afectadas: -1

### Batch 2
- Tipo: SELECT
- Columnas: unidad_codigo, unidad_nombre, server_name, server_id, system_type
- Filas: 5
- Preview (primeras 20 filas):
```
  {'unidad_codigo': '130MID', 'unidad_nombre': '130° MERIDA', 'server_name': '130° MERIDA', 'server_id': 'A5547321-1139-4D2B-9D53-182CA737B6B6', 'system_type': 'SOFTRESTAURANT_PRO'}
  {'unidad_codigo': '130QRO', 'unidad_nombre': '130° QUERETARO', 'server_name': 'ManagmentPro', 'server_id': '1B230A06-FFAF-4C70-BD27-B1BE3579DEA6', 'system_type': 'MPRO'}
  {'unidad_codigo': 'CIENFUEGOS', 'unidad_nombre': 'CIENFUEGOS', 'server_name': 'CIENFUEGOS', 'server_id': '6D053C22-523E-48C0-B72B-96081E2D781B', 'system_type': 'SOFTRESTAURANT_PRO'}
  {'unidad_codigo': 'ESTELAR', 'unidad_nombre': 'LA ESTELAR', 'server_name': 'LA ESTELAR', 'server_id': 'A5FF0E25-F029-43DB-B634-D4AC814C904F', 'system_type': 'SOFTRESTAURANT_PRO'}
  {'unidad_codigo': 'ORIGEN', 'unidad_nombre': 'ORIGEN', 'server_name': 'ManagmentPro', 'server_id': '1B230A06-FFAF-4C70-BD27-B1BE3579DEA6', 'system_type': 'MPRO'}
```

### Batch 3
- Tipo: SELECT
- Columnas: unidad_codigo, server_name, system_type, filas_sync, folios_distintos, almacenes_distintos, fecha_inventario_max, dias_desfase_inventario, sync_timestamp_max, horas_desfase_sync, filas_inventario_hoy, filas_active, filas_replaced, estado_operacional
- Filas: 5
- Preview (primeras 20 filas):
```
  {'unidad_codigo': '130MID', 'server_name': '130° MERIDA', 'system_type': 'SOFTRESTAURANT_PRO', 'filas_sync': 172, 'folios_distintos': 172, 'almacenes_distintos': 10, 'fecha_inventario_max': datetime.datetime(2026, 6, 1, 16, 25, 44), 'dias_desfase_inventario': 29, 'sync_timestamp_max': datetime.datetime(2026, 6, 3, 23, 45, 44, 10000), 'horas_desfase_sync': 639, 'filas_inventario_hoy': 0, 'filas_active': 0, 'filas_replaced': 172, 'estado_operacional': 'DESFASADO_FECHA_INVENTARIO'}
  {'unidad_codigo': '130QRO', 'server_name': 'ManagmentPro', 'system_type': 'MPRO', 'filas_sync': 1, 'folios_distintos': 1, 'almacenes_distintos': 1, 'fecha_inventario_max': datetime.datetime(2026, 6, 29, 0, 0), 'dias_desfase_inventario': 1, 'sync_timestamp_max': datetime.datetime(2026, 6, 29, 23, 2, 6, 943000), 'horas_desfase_sync': 15, 'filas_inventario_hoy': 0, 'filas_active': 0, 'filas_replaced': 1, 'estado_operacional': 'DESFASADO_FECHA_INVENTARIO'}
  {'unidad_codigo': 'CIENFUEGOS', 'server_name': 'CIENFUEGOS', 'system_type': 'SOFTRESTAURANT_PRO', 'filas_sync': 185, 'folios_distintos': 185, 'almacenes_distintos': 10, 'fecha_inventario_max': datetime.datetime(2026, 5, 25, 13, 22, 58), 'dias_desfase_inventario': 36, 'sync_timestamp_max': datetime.datetime(2026, 6, 25, 22, 52, 31, 277000), 'horas_desfase_sync': 112, 'filas_inventario_hoy': 0, 'filas_active': 185, 'filas_replaced': 0, 'estado_operacional': 'DESFASADO_FECHA_INVENTARIO'}
  {'unidad_codigo': 'ESTELAR', 'server_name': 'LA ESTELAR', 'system_type': 'SOFTRESTAURANT_PRO', 'filas_sync': 131, 'folios_distintos': 131, 'almacenes_distintos': 6, 'fecha_inventario_max': datetime.datetime(2026, 6, 1, 15, 28, 27), 'dias_desfase_inventario': 29, 'sync_timestamp_max': datetime.datetime(2026, 6, 3, 23, 48, 32, 107000), 'horas_desfase_sync': 639, 'filas_inventario_hoy': 0, 'filas_active': 0, 'filas_replaced': 131, 'estado_operacional': 'DESFASADO_FECHA_INVENTARIO'}
  {'unidad_codigo': 'ORIGEN', 'server_name': 'ManagmentPro', 'system_type': 'MPRO', 'filas_sync': 292, 'folios_distintos': 292, 'almacenes_distintos': 3, 'fecha_inventario_max': datetime.datetime(2026, 6, 21, 0, 0), 'dias_desfase_inventario': 9, 'sync_timestamp_max': datetime.datetime(2026, 6, 25, 22, 53, 33, 347000), 'horas_desfase_sync': 112, 'filas_inventario_hoy': 0, 'filas_active': 0, 'filas_replaced': 292, 'estado_operacional': 'DESFASADO_FECHA_INVENTARIO'}
```

### Batch 4
- Tipo: SELECT
- Columnas: unidad_codigo, server_name, server_id, sync_start, sync_end, records_synced, status, error_message, created_at
- Filas: 9
- Preview (primeras 20 filas):
```
  {'unidad_codigo': None, 'server_name': 'MPRO TABLAJERIA', 'server_id': 'd1d8c70f-c3d0-4407-ae50-f09e8e5992ee', 'sync_start': datetime.datetime(2026, 6, 30, 14, 47, 0, 293000), 'sync_end': datetime.datetime(2026, 6, 30, 14, 47, 0, 543000), 'records_synced': 0, 'status': 'OK', 'error_message': None, 'created_at': datetime.datetime(2026, 6, 30, 14, 47, 0, 753000)}
  {'unidad_codigo': 'ESTELAR', 'server_name': 'LA ESTELAR', 'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f', 'sync_start': datetime.datetime(2026, 6, 30, 14, 43, 27, 587000), 'sync_end': datetime.datetime(2026, 6, 30, 14, 43, 28, 157000), 'records_synced': 0, 'status': 'OK', 'error_message': None, 'created_at': datetime.datetime(2026, 6, 30, 14, 43, 28, 367000)}
  {'unidad_codigo': None, 'server_name': 'HR2020 ESCRITURA', 'server_id': 'b5175237-5e57-41f3-ab6d-b5ae2f5e780b', 'sync_start': datetime.datetime(2026, 6, 30, 14, 43, 24, 37000), 'sync_end': datetime.datetime(2026, 6, 30, 14, 43, 24, 77000), 'records_synced': 0, 'status': 'OK', 'error_message': None, 'created_at': datetime.datetime(2026, 6, 30, 14, 43, 24, 300000)}
  {'unidad_codigo': '130QRO', 'server_name': 'ManagmentPro', 'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6', 'sync_start': datetime.datetime(2026, 6, 30, 14, 30, 59, 287000), 'sync_end': datetime.datetime(2026, 6, 30, 14, 31, 18, 700000), 'records_synced': 0, 'status': 'OK', 'error_message': None, 'created_at': datetime.datetime(2026, 6, 30, 14, 31, 18, 913000)}
  {'unidad_codigo': 'ORIGEN', 'server_name': 'ManagmentPro', 'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6', 'sync_start': datetime.datetime(2026, 6, 30, 14, 17, 29, 127000), 'sync_end': datetime.datetime(2026, 6, 30, 14, 17, 49, 257000), 'records_synced': 0, 'status': 'OK', 'error_message': None, 'created_at': datetime.datetime(2026, 6, 30, 14, 17, 49, 467000)}
  {'unidad_codigo': 'CIENFUEGOS', 'server_name': 'CIENFUEGOS', 'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b', 'sync_start': datetime.datetime(2026, 6, 30, 14, 15, 18, 97000), 'sync_end': datetime.datetime(2026, 6, 30, 14, 15, 34, 167000), 'records_synced': 0, 'status': 'OK', 'error_message': None, 'created_at': datetime.datetime(2026, 6, 30, 14, 15, 34, 377000)}
  {'unidad_codigo': None, 'server_name': 'CIENFUEGOS TABLAJERIA', 'server_id': '6d859026-710a-4920-9a44-6da98fabc690', 'sync_start': datetime.datetime(2026, 6, 30, 14, 13, 39, 500000), 'sync_end': datetime.datetime(2026, 6, 30, 14, 13, 55, 557000), 'records_synced': 0, 'status': 'OK', 'error_message': None, 'created_at': datetime.datetime(2026, 6, 30, 14, 13, 55, 770000)}
  {'unidad_codigo': None, 'server_name': 'PRUEBAS SOFTRESTAURANT', 'server_id': 'd8425038-5e57-42d9-8f3a-62e287888874', 'sync_start': datetime.datetime(2026, 6, 30, 14, 13, 35, 163000), 'sync_end': datetime.datetime(2026, 6, 30, 14, 13, 35, 600000), 'records_synced': 0, 'status': 'OK', 'error_message': None, 'created_at': datetime.datetime(2026, 6, 30, 14, 13, 35, 810000)}
  {'unidad_codigo': '130MID', 'server_name': '130° MERIDA', 'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6', 'sync_start': datetime.datetime(2026, 6, 30, 14, 9, 53, 377000), 'sync_end': datetime.datetime(2026, 6, 30, 14, 9, 53, 967000), 'records_synced': 0, 'status': 'OK', 'error_message': None, 'created_at': datetime.datetime(2026, 6, 30, 14, 9, 54, 183000)}
```

### Batch 5
- Tipo: SELECT
- Columnas: SistemaOrigen, ServerID, SucursalID, AlmacenID, Estado, registros, primera_deteccion, ultima_deteccion, ultimo_procesamiento
- Filas: 0

### Batch 6
- Tipo: SELECT
- Columnas: server_name, server_id, system_type, tipo_conexion, hallazgo
- Filas: 4
- Preview (primeras 20 filas):
```
  {'server_name': 'HR2020 ESCRITURA', 'server_id': 'B5175237-5E57-41F3-AB6D-B5AE2F5E780B', 'system_type': 'MPRO', 'tipo_conexion': 'DATA_SOURCE', 'hallazgo': 'SERVIDOR_ACTIVO_SIN_UNIDAD_NEGOCIO'}
  {'server_name': 'MPRO TABLAJERIA', 'server_id': 'D1D8C70F-C3D0-4407-AE50-F09E8E5992EE', 'system_type': 'MPRO', 'tipo_conexion': 'DATA_SOURCE', 'hallazgo': 'SERVIDOR_ACTIVO_SIN_UNIDAD_NEGOCIO'}
  {'server_name': 'CIENFUEGOS TABLAJERIA', 'server_id': '6D859026-710A-4920-9A44-6DA98FABC690', 'system_type': 'SOFTRESTAURANT_PRO', 'tipo_conexion': 'DATA_SOURCE', 'hallazgo': 'SERVIDOR_ACTIVO_SIN_UNIDAD_NEGOCIO'}
  {'server_name': 'PRUEBAS SOFTRESTAURANT', 'server_id': 'D8425038-5E57-42D9-8F3A-62E287888874', 'system_type': 'SOFTRESTAURANT_PRO', 'tipo_conexion': 'DATA_SOURCE', 'hallazgo': 'SERVIDOR_ACTIVO_SIN_UNIDAD_NEGOCIO'}
```


## SQL ejecutado / revisado
```sql
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

```