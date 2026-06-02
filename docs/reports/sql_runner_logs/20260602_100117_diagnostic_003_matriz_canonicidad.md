# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T10:01:17.566344
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/diagnostics/003_matriz_canonicidad.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 3
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: SELECT
- Columnas: tabla, esquema, registros_aproximados, clasificacion_sugerida
- Filas: 423
- Preview (primeras 20 filas):
```
  {'tabla': 'Comercial_AlertasMargenDestinatarios', 'esquema': 'dbo', 'registros_aproximados': 0, 'clasificacion_sugerida': 'CANONICA_COMERCIAL_DERIVADA'}
  {'tabla': 'Comercial_AlertasMargenEnvios', 'esquema': 'dbo', 'registros_aproximados': 0, 'clasificacion_sugerida': 'CANONICA_COMERCIAL_DERIVADA'}
  {'tabla': 'Comercial_AlertasMargenEventos', 'esquema': 'dbo', 'registros_aproximados': 0, 'clasificacion_sugerida': 'CANONICA_COMERCIAL_DERIVADA'}
  {'tabla': 'Comercial_AlertasMargenReglas', 'esquema': 'dbo', 'registros_aproximados': 3, 'clasificacion_sugerida': 'CANONICA_COMERCIAL_DERIVADA'}
  {'tabla': 'Comercial_AlertasUmbralesSeveridad', 'esquema': 'dbo', 'registros_aproximados': 4, 'clasificacion_sugerida': 'CANONICA_COMERCIAL_DERIVADA'}
  {'tabla': 'Comercial_Competidores', 'esquema': 'dbo', 'registros_aproximados': 3, 'clasificacion_sugerida': 'CANONICA_COMERCIAL_DERIVADA'}
  {'tabla': 'Comercial_CompetidoresCatalogo', 'esquema': 'dbo', 'registros_aproximados': 4, 'clasificacion_sugerida': 'CANONICA_COMERCIAL_DERIVADA'}
  {'tabla': 'Comercial_CompetidoresListas', 'esquema': 'dbo', 'registros_aproximados': 1, 'clasificacion_sugerida': 'CANONICA_COMERCIAL_DERIVADA'}
  {'tabla': 'Comercial_CompetidoresListasDetalle', 'esquema': 'dbo', 'registros_aproximados': 1, 'clasificacion_sugerida': 'CANONICA_COMERCIAL_DERIVADA'}
  {'tabla': 'Comercial_CompetidoresMenuItems', 'esquema': 'dbo', 'registros_aproximados': 6, 'clasificacion_sugerida': 'CANONICA_COMERCIAL_DERIVADA'}
```

### Batch 2
- Tipo: SELECT
- Columnas: TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION
- Filas: 381
- Preview (primeras 20 filas):
```
  {'TABLE_NAME': 'Finanzas_Cat_CuentasBancarias', 'COLUMN_NAME': 'CuentaBancariaID', 'DATA_TYPE': 'int', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 1}
  {'TABLE_NAME': 'Finanzas_Cat_CuentasBancarias', 'COLUMN_NAME': 'EmpresaID', 'DATA_TYPE': 'int', 'IS_NULLABLE': 'YES', 'ORDINAL_POSITION': 2}
  {'TABLE_NAME': 'Finanzas_Cat_CuentasBancarias', 'COLUMN_NAME': 'BancoID', 'DATA_TYPE': 'int', 'IS_NULLABLE': 'YES', 'ORDINAL_POSITION': 3}
  {'TABLE_NAME': 'Finanzas_Cat_CuentasBancarias', 'COLUMN_NAME': 'NumeroCuenta', 'DATA_TYPE': 'varchar', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 4}
  {'TABLE_NAME': 'Finanzas_Cat_CuentasBancarias', 'COLUMN_NAME': 'CLABE', 'DATA_TYPE': 'varchar', 'IS_NULLABLE': 'YES', 'ORDINAL_POSITION': 5}
  {'TABLE_NAME': 'Finanzas_Cat_CuentasBancarias', 'COLUMN_NAME': 'Alias', 'DATA_TYPE': 'varchar', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 6}
  {'TABLE_NAME': 'Finanzas_Cat_CuentasBancarias', 'COLUMN_NAME': 'Moneda', 'DATA_TYPE': 'varchar', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 7}
  {'TABLE_NAME': 'Finanzas_Cat_CuentasBancarias', 'COLUMN_NAME': 'EsCuentaPrincipal', 'DATA_TYPE': 'bit', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 8}
  {'TABLE_NAME': 'Finanzas_Cat_CuentasBancarias', 'COLUMN_NAME': 'Activo', 'DATA_TYPE': 'bit', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 9}
  {'TABLE_NAME': 'Finanzas_Cat_CuentasBancarias', 'COLUMN_NAME': 'FechaAlta', 'DATA_TYPE': 'datetime2', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 10}
```

### Batch 3
- Tipo: SELECT
- Columnas: TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION
- Filas: 192
- Preview (primeras 20 filas):
```
  {'TABLE_NAME': 'Comercial_KPIs_Diarios_v2', 'COLUMN_NAME': 'id', 'DATA_TYPE': 'uniqueidentifier', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 1}
  {'TABLE_NAME': 'Comercial_KPIs_Diarios_v2', 'COLUMN_NAME': 'unidad_negocio_id', 'DATA_TYPE': 'nvarchar', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 2}
  {'TABLE_NAME': 'Comercial_KPIs_Diarios_v2', 'COLUMN_NAME': 'unidad_negocio_nombre', 'DATA_TYPE': 'nvarchar', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 3}
  {'TABLE_NAME': 'Comercial_KPIs_Diarios_v2', 'COLUMN_NAME': 'server_id', 'DATA_TYPE': 'nvarchar', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 4}
  {'TABLE_NAME': 'Comercial_KPIs_Diarios_v2', 'COLUMN_NAME': 'sucursal_id', 'DATA_TYPE': 'nvarchar', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 5}
  {'TABLE_NAME': 'Comercial_KPIs_Diarios_v2', 'COLUMN_NAME': 'sucursal_nombre', 'DATA_TYPE': 'nvarchar', 'IS_NULLABLE': 'YES', 'ORDINAL_POSITION': 6}
  {'TABLE_NAME': 'Comercial_KPIs_Diarios_v2', 'COLUMN_NAME': 'sistema_origen', 'DATA_TYPE': 'nvarchar', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 7}
  {'TABLE_NAME': 'Comercial_KPIs_Diarios_v2', 'COLUMN_NAME': 'fecha_operacion', 'DATA_TYPE': 'date', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 8}
  {'TABLE_NAME': 'Comercial_KPIs_Diarios_v2', 'COLUMN_NAME': 'anio', 'DATA_TYPE': 'int', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 9}
  {'TABLE_NAME': 'Comercial_KPIs_Diarios_v2', 'COLUMN_NAME': 'mes', 'DATA_TYPE': 'int', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 10}
```


## SQL ejecutado / revisado
```sql
/* ============================================================
   MATRIZ DE CANONICIDAD EDARSAHUB
   Script: 003_matriz_canonicidad.sql
   Modo: diagnostic
   
   Identifica tablas activas, heredadas, sincronizadas y en revisión.
   No modifica datos.
   ============================================================ */

-- 1. MATRIZ DE CANONICIDAD
SELECT
    t.name AS tabla,
    s.name AS esquema,
    SUM(p.rows) AS registros_aproximados,
    CASE
        WHEN t.name LIKE 'Global_Cat_%' THEN 'CANONICA_GLOBAL'
        WHEN t.name LIKE 'RH_%' THEN 'CANONICA_RH'
        WHEN t.name LIKE 'Finanzas_%' THEN 'CANONICA_FINANZAS_PROPUESTA'
        WHEN t.name LIKE 'FIN_%' THEN 'LEGADO_FINANZAS_REVISION'
        WHEN t.name LIKE 'propinas_tpv_%' THEN 'CANONICA_PROPINAS_TPV'
        WHEN t.name LIKE 'Sync_%' THEN 'SINCRONIZADA'
        WHEN t.name LIKE 'Comercial_%' THEN 'CANONICA_COMERCIAL_DERIVADA'
        WHEN t.name LIKE 'Sistema_%' THEN 'CANONICA_SISTEMA'
        WHEN t.name LIKE 'Sys_%' THEN 'SISTEMA_REVISION'
        WHEN t.name IN ('Products', 'Fact_Ventas_Consolidadas', 'Config_Horarios') THEN 'LEGADO_REVISION_NO_USAR_NUEVO'
        ELSE 'SIN_CLASIFICAR'
    END AS clasificacion_sugerida
FROM sys.tables t
INNER JOIN sys.schemas s
    ON t.schema_id = s.schema_id
LEFT JOIN sys.partitions p
    ON t.object_id = p.object_id
    AND p.index_id IN (0, 1)
GROUP BY
    t.name,
    s.name
ORDER BY
    clasificacion_sugerida,
    t.name;
GO

-- 2. VALIDACIÓN FIN_* vs Finanzas_*
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE 
    TABLE_NAME LIKE 'FIN_%'
    OR TABLE_NAME LIKE 'Finanzas_%'
ORDER BY TABLE_NAME, ORDINAL_POSITION;
GO

-- 3. VALIDACIÓN COMERCIAL / SYNC / PRODUCTS
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN (
    'Comercial_KPIs_Diarios_v2',
    'Comercial_Ventas_Dia_Abiertas_v2',
    'Sync_Sales',
    'Sync_PAX_Detalle',
    'Sync_Productos',
    'Sync_Productos_Familias',
    'Sync_Productos_SubFamilias',
    'Products',
    'Fact_Ventas_Consolidadas',
    'Config_Horarios'
)
ORDER BY TABLE_NAME, ORDINAL_POSITION;
GO

```