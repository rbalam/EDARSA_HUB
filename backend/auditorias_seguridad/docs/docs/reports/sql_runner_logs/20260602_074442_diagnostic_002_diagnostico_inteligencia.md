# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T07:44:42.487197
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/diagnostics/002_diagnostico_inteligencia.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 4
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: SELECT
- Columnas: Tabla, Registros
- Filas: 4
- Preview (primeras 20 filas):
```
  {'Tabla': 'Sync_Sales', 'Registros': 0}
  {'Tabla': 'Sync_PAX_Detalle', 'Registros': 0}
  {'Tabla': 'Comercial_KPIs_Diarios_v2', 'Registros': 3372}
  {'Tabla': 'Sys_Scheduler_Jobs', 'Registros': 6}
```

### Batch 2
- Tipo: SELECT
- Columnas: JobID, JobName, CronExpression, JobType, Status, LastRunDate
- Filas: 6
- Preview (primeras 20 filas):
```
  {'JobID': 'sync-inteligencia', 'JobName': 'Actualizar Vista Inteligencia', 'CronExpression': '0 */6 * * *', 'JobType': 'DB', 'Status': 'activo', 'LastRunDate': None}
  {'JobID': 'sync-vtiger', 'JobName': 'Importación Vtiger CRM', 'CronExpression': '0 0 * * *', 'JobType': 'API', 'Status': 'activo', 'LastRunDate': None}
  {'JobID': 'SYNC-INTELIGENCIA-01', 'JobName': 'inteligencia_comercial_sync', 'CronExpression': '0 * * * *', 'JobType': 'DATA_SYNC', 'Status': 'ACTIVE', 'LastRunDate': datetime.datetime(2026, 6, 2, 1, 0, 2, 343000)}
  {'JobID': 'recalc-kpis', 'JobName': 'Recálculo de KPIs Globales', 'CronExpression': '*/30 * * * *', 'JobType': 'App', 'Status': 'activo', 'LastRunDate': None}
  {'JobID': 'backup-db', 'JobName': 'Respaldo Completo EDARSAHUB', 'CronExpression': '0 2 * * 0', 'JobType': 'Sys', 'Status': 'activo', 'LastRunDate': None}
  {'JobID': 'sync-sales', 'JobName': 'Sincronización de Ventas SQL', 'CronExpression': '0 * * * *', 'JobType': 'DB', 'Status': 'activo', 'LastRunDate': datetime.datetime(2026, 6, 1, 16, 21, 19, 863000)}
```

### Batch 3
- Tipo: SELECT
- Columnas: unidad_negocio_nombre, fecha_operacion, ventas_total, pax_total, tickets_total, ticket_promedio, fuente_original, fecha_ultima_actualizacion
- Filas: 10
- Preview (primeras 20 filas):
```
  {'unidad_negocio_nombre': '130° MERIDA', 'fecha_operacion': datetime.date(2026, 6, 1), 'ventas_total': Decimal('79474.00'), 'pax_total': 52, 'tickets_total': 17, 'ticket_promedio': Decimal('4674.94'), 'fuente_original': 'SQL_LIVE', 'fecha_ultima_actualizacion': datetime.datetime(2026, 6, 2, 6, 24, 44, 201045)}
  {'unidad_negocio_nombre': 'LA ESTELAR', 'fecha_operacion': datetime.date(2026, 6, 1), 'ventas_total': Decimal('560.00'), 'pax_total': 2, 'tickets_total': 2, 'ticket_promedio': Decimal('280.00'), 'fuente_original': 'SQL_LIVE', 'fecha_ultima_actualizacion': datetime.datetime(2026, 6, 2, 1, 37, 30, 392469)}
  {'unidad_negocio_nombre': '130° MERIDA', 'fecha_operacion': datetime.date(2026, 5, 31), 'ventas_total': Decimal('149947.00'), 'pax_total': 93, 'tickets_total': 33, 'ticket_promedio': Decimal('4543.85'), 'fuente_original': 'SQL_LIVE', 'fecha_ultima_actualizacion': datetime.datetime(2026, 6, 2, 6, 24, 44, 122916)}
  {'unidad_negocio_nombre': '130° QUERETARO', 'fecha_operacion': datetime.date(2026, 5, 31), 'ventas_total': Decimal('53119.00'), 'pax_total': 36, 'tickets_total': 11, 'ticket_promedio': Decimal('4829.00'), 'fuente_original': 'SQL_LIVE', 'fecha_ultima_actualizacion': datetime.datetime(2026, 6, 1, 12, 7, 33, 459754)}
  {'unidad_negocio_nombre': 'CIENFUEGOS', 'fecha_operacion': datetime.date(2026, 5, 31), 'ventas_total': Decimal('108325.00'), 'pax_total': 86, 'tickets_total': 28, 'ticket_promedio': Decimal('3868.75'), 'fuente_original': 'SQL_LIVE', 'fecha_ultima_actualizacion': datetime.datetime(2026, 6, 1, 1, 55, 0, 915010)}
  {'unidad_negocio_nombre': 'LA ESTELAR', 'fecha_operacion': datetime.date(2026, 5, 31), 'ventas_total': Decimal('105495.00'), 'pax_total': 196, 'tickets_total': 95, 'ticket_promedio': Decimal('1110.47'), 'fuente_original': 'SQL_LIVE', 'fecha_ultima_actualizacion': datetime.datetime(2026, 6, 1, 4, 7, 29, 946266)}
  {'unidad_negocio_nombre': 'ORIGEN', 'fecha_operacion': datetime.date(2026, 5, 31), 'ventas_total': Decimal('48291.07'), 'pax_total': 88, 'tickets_total': 29, 'ticket_promedio': Decimal('1665.21'), 'fuente_original': 'SQL_LIVE', 'fecha_ultima_actualizacion': datetime.datetime(2026, 6, 1, 10, 37, 33, 136821)}
  {'unidad_negocio_nombre': '130° MERIDA', 'fecha_operacion': datetime.date(2026, 5, 30), 'ventas_total': Decimal('184960.00'), 'pax_total': 135, 'tickets_total': 46, 'ticket_promedio': Decimal('4020.87'), 'fuente_original': 'SQL_LIVE', 'fecha_ultima_actualizacion': datetime.datetime(2026, 6, 2, 6, 24, 44, 57886)}
  {'unidad_negocio_nombre': '130° QUERETARO', 'fecha_operacion': datetime.date(2026, 5, 30), 'ventas_total': Decimal('161546.00'), 'pax_total': 94, 'tickets_total': 37, 'ticket_promedio': Decimal('4366.11'), 'fuente_original': 'SQL_LIVE', 'fecha_ultima_actualizacion': datetime.datetime(2026, 5, 31, 11, 7, 36, 104795)}
  {'unidad_negocio_nombre': 'CIENFUEGOS', 'fecha_operacion': datetime.date(2026, 5, 30), 'ventas_total': Decimal('210365.00'), 'pax_total': 170, 'tickets_total': 60, 'ticket_promedio': Decimal('3506.08'), 'fuente_original': 'SQL_LIVE', 'fecha_ultima_actualizacion': datetime.datetime(2026, 5, 31, 19, 7, 34, 830074)}
```

### Batch 4
- Tipo: SELECT
- Columnas: unidad_negocio_nombre, sistema_origen, dias_con_datos
- Filas: 5
- Preview (primeras 20 filas):
```
  {'unidad_negocio_nombre': '130° MERIDA', 'sistema_origen': 'SOFTRESTAURANT', 'dias_con_datos': 757}
  {'unidad_negocio_nombre': '130° QUERETARO', 'sistema_origen': 'MPRO', 'dias_con_datos': 757}
  {'unidad_negocio_nombre': 'CIENFUEGOS', 'sistema_origen': 'SOFTRESTAURANT', 'dias_con_datos': 755}
  {'unidad_negocio_nombre': 'LA ESTELAR', 'sistema_origen': 'SOFTRESTAURANT', 'dias_con_datos': 348}
  {'unidad_negocio_nombre': 'ORIGEN', 'sistema_origen': 'MPRO', 'dias_con_datos': 755}
```


## SQL ejecutado / revisado
```sql
/* 
   EDARSAHUB - Diagnóstico Tablas Inteligencia Comercial
   Script: 002_diagnostico_inteligencia.sql
   Modo: diagnostic (solo lectura)
*/

-- 1. Conteo de registros en tablas clave
SELECT 'Sync_Sales' AS Tabla, COUNT(*) AS Registros FROM Sync_Sales
UNION ALL
SELECT 'Sync_PAX_Detalle', COUNT(*) FROM Sync_PAX_Detalle
UNION ALL
SELECT 'Comercial_KPIs_Diarios_v2', COUNT(*) FROM Comercial_KPIs_Diarios_v2
UNION ALL
SELECT 'Sys_Scheduler_Jobs', COUNT(*) FROM Sys_Scheduler_Jobs;

GO

-- 2. Jobs programados
SELECT 
    JobID,
    JobName,
    CronExpression,
    JobType,
    Status,
    LastRunDate
FROM Sys_Scheduler_Jobs
ORDER BY JobName;

GO

-- 3. Últimos KPIs diarios
SELECT TOP 10
    unidad_negocio_nombre,
    fecha_operacion,
    ventas_total,
    pax_total,
    tickets_total,
    ticket_promedio,
    fuente_original,
    fecha_ultima_actualizacion
FROM Comercial_KPIs_Diarios_v2
ORDER BY fecha_operacion DESC, unidad_negocio_nombre;

GO

-- 4. Unidades de negocio activas en KPIs
SELECT DISTINCT
    unidad_negocio_nombre,
    sistema_origen,
    COUNT(*) AS dias_con_datos
FROM Comercial_KPIs_Diarios_v2
WHERE activo = 1
GROUP BY unidad_negocio_nombre, sistema_origen
ORDER BY unidad_negocio_nombre;

GO

```