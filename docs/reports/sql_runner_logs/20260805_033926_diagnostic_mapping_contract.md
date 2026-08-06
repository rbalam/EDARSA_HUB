# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:39:26.521389
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_pos_context_mapping_retry_20260805T033924Z/mapping_contract.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: unidad_codigo, server_id, sucursal_origen_id, sucursal_legacy_id, system_type
- Filas: 5
- Preview (primeras 20 filas):
```
  {'unidad_codigo': '130MID', 'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6', 'sucursal_origen_id': None, 'sucursal_legacy_id': None, 'system_type': 'SOFTRESTAURANT_PRO'}
  {'unidad_codigo': 'CIENFUEGOS', 'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b', 'sucursal_origen_id': None, 'sucursal_legacy_id': None, 'system_type': 'SOFTRESTAURANT_PRO'}
  {'unidad_codigo': 'ESTELAR', 'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f', 'sucursal_origen_id': None, 'sucursal_legacy_id': None, 'system_type': 'SOFTRESTAURANT_PRO'}
  {'unidad_codigo': '130QRO', 'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6', 'sucursal_origen_id': '0021', 'sucursal_legacy_id': '21', 'system_type': 'MPRO'}
  {'unidad_codigo': 'ORIGEN', 'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6', 'sucursal_origen_id': '0023', 'sucursal_legacy_id': '23', 'system_type': 'MPRO'}
```


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT
    u.codigo AS unidad_codigo,
    CONVERT(nvarchar(100), u.server_id) AS server_id,
    CONVERT(nvarchar(100), u.sucursal_origen_id) AS sucursal_origen_id,
    CONVERT(nvarchar(100), TRY_CONVERT(int, u.sucursal_origen_id))
        AS sucursal_legacy_id,
    s.system_type
FROM dbo.Unidades_Negocio AS u
INNER JOIN dbo.Servidores_Conexiones AS s
    ON s.id = u.server_id
WHERE
    u.activo = 1
    AND s.activo = 1
ORDER BY
    u.orden,
    u.codigo;

SELECT
    CONVERT(nvarchar(100), server_id) AS server_id,
    CONVERT(nvarchar(100), sucursal_id) AS sucursal_id,
    COUNT_BIG(*) AS filas,
    MIN(CAST(fecha_operacion AS date)) AS fecha_min,
    MAX(CAST(fecha_operacion AS date)) AS fecha_max
FROM dbo.Comercial_Ventas_Dia_Abiertas_v2
GROUP BY
    CONVERT(nvarchar(100), server_id),
    CONVERT(nvarchar(100), sucursal_id)
ORDER BY
    server_id,
    sucursal_id;

SELECT
    CONVERT(nvarchar(100), server_id) AS server_id,
    CONVERT(nvarchar(100), sucursal_id) AS sucursal_id,
    COUNT_BIG(*) AS filas,
    MIN(fecha_operacion) AS fecha_min,
    MAX(fecha_operacion) AS fecha_max
FROM dbo.Comercial_KPIs_Diarios_v2
GROUP BY
    CONVERT(nvarchar(100), server_id),
    CONVERT(nvarchar(100), sucursal_id)
ORDER BY
    server_id,
    sucursal_id;

```