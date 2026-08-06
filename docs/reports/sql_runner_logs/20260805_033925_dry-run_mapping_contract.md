# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:39:25.769083
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_pos_context_mapping_retry_20260805T033924Z/mapping_contract.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Dry-run ejecutado. No se aplicaron cambios.


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