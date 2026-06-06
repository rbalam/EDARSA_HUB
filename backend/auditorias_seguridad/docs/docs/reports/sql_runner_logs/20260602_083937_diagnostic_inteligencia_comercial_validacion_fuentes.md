# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T08:39:37.867936
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/sql/inteligencia_comercial_validacion_fuentes.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: SELECT
- Columnas: Fuente, Registros, FechaMinima, FechaMaxima, UltimaSincronizacion
- Filas: 1
- Preview (primeras 20 filas):
```
  {'Fuente': 'Comercial_KPIs_Diarios_v2', 'Registros': 3372, 'FechaMinima': datetime.date(2024, 5, 1), 'FechaMaxima': datetime.date(2026, 6, 1), 'UltimaSincronizacion': datetime.datetime(2026, 6, 2, 6, 24, 44, 201045)}
```


## SQL ejecutado / revisado
```sql
/* ============================================================
   VALIDACIÓN DE FUENTES PARA PORTAL INTELIGENCIA COMERCIAL
   No modifica datos.
   ============================================================ */

SELECT
    'Comercial_KPIs_Diarios_v2' AS Fuente,
    COUNT(*) AS Registros,
    MIN(fecha_operacion) AS FechaMinima,
    MAX(fecha_operacion) AS FechaMaxima,
    MAX(fecha_sincronizacion) AS UltimaSincronizacion
FROM dbo.Comercial_KPIs_Diarios_v2;

SELECT
    unidad_negocio_nombre,
    sistema_origen,
    COUNT(*) AS Registros,
    MIN(fecha_operacion) AS FechaMinima,
    MAX(fecha_operacion) AS FechaMaxima,
    MAX(fecha_sincronizacion) AS UltimaSincronizacion
FROM dbo.Comercial_KPIs_Diarios_v2
GROUP BY unidad_negocio_nombre, sistema_origen
ORDER BY unidad_negocio_nombre;

SELECT
    'Comercial_Ventas_Dia_Abiertas_v2' AS Fuente,
    COUNT(*) AS Registros,
    MIN(fecha_operacion) AS FechaMinima,
    MAX(fecha_operacion) AS FechaMaxima,
    MAX(fecha_ultima_actualizacion) AS UltimaActualizacion
FROM dbo.Comercial_Ventas_Dia_Abiertas_v2;

SELECT
    'Sync_PAX_Detalle' AS Fuente,
    COUNT(*) AS Registros,
    MIN(FechaOperacion) AS FechaMinima,
    MAX(FechaOperacion) AS FechaMaxima,
    MAX(FechaSync) AS UltimaSync
FROM dbo.Sync_PAX_Detalle;

SELECT
    SucursalNombre,
    COUNT(*) AS Registros,
    MIN(FechaOperacion) AS FechaMinima,
    MAX(FechaOperacion) AS FechaMaxima,
    MAX(FechaSync) AS UltimaSync
FROM dbo.Sync_PAX_Detalle
GROUP BY SucursalNombre
ORDER BY SucursalNombre;

SELECT
    'Sync_Sales' AS Fuente,
    COUNT(*) AS Registros,
    MIN(CAST(FechaHora AS DATE)) AS FechaMinima,
    MAX(CAST(FechaHora AS DATE)) AS FechaMaxima,
    MAX(last_modified) AS UltimaModificacion
FROM dbo.Sync_Sales;

SELECT
    UnidadNegocio,
    COUNT(*) AS Registros,
    MIN(CAST(FechaHora AS DATE)) AS FechaMinima,
    MAX(CAST(FechaHora AS DATE)) AS FechaMaxima,
    MAX(last_modified) AS UltimaModificacion
FROM dbo.Sync_Sales
GROUP BY UnidadNegocio
ORDER BY UnidadNegocio;

SELECT
    codigo,
    nombre,
    system_type,
    activo,
    server_id
FROM dbo.Unidades_Negocio
ORDER BY orden, nombre;

```