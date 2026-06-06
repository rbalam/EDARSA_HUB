# DIAGNÓSTICO ESQUEMA EDARSAHUB
## Fecha: 2026-06-02
## Base de Datos: EDARSAHUB @ 54.39.104.176:1433

---

## 📊 RESUMEN EJECUTIVO

| Métrica | Valor |
|---------|-------|
| Total Tablas/Vistas | 427 |
| Sync_Sales | **0 registros** (VACÍA) |
| Sync_PAX_Detalle | **0 registros** (VACÍA) |
| Comercial_KPIs_Diarios_v2 | ✅ Con datos |
| Jobs Scheduler | 6 registrados |

---

## 🔴 TABLAS VACÍAS (Críticas para Inteligencia Comercial)

### Sync_Sales (16 columnas)
```
id                    varchar(64)       NOT NULL
branch                nvarchar(100)     NOT NULL
customer_id           varchar(64)       NULL
items                 nvarchar(MAX)     NULL      -- JSON de productos
total                 numeric           NOT NULL
currency              varchar(3)        NULL
status                varchar(32)       NULL
created_at            datetime          NULL
last_modified         datetime          NULL
sync_hash             varchar(64)       NULL
IdTransaccion         varchar(64)       NULL
UnidadNegocio         nvarchar(100)     NULL
MontoTotal            numeric           NULL
Pax                   int               NULL
NumeroTicket          varchar(64)       NULL
FechaHora             datetime          NULL
```

### Sync_PAX_Detalle (22 columnas)
```
ID                    int               NOT NULL (IDENTITY)
PAXRegistroID         nvarchar(50)      NOT NULL
ServerID              nvarchar(50)      NOT NULL
SucursalID            nvarchar(20)      NOT NULL
SucursalNombre        nvarchar(100)     NULL
FechaOperacion        date              NOT NULL
FechaHora             datetime2         NOT NULL
CuentaID              nvarchar(50)      NULL
CuentaFolio           nvarchar(50)      NULL
MesaNumero            nvarchar(20)      NULL
MeseroID              nvarchar(50)      NULL
MeseroNombre          nvarchar(100)     NULL
NumeroComensales      int               NOT NULL
TipoPAX               nvarchar(20)      NULL
VentaCuenta           decimal           NULL
ConsumoPromedioPAX    decimal           NULL
TiempoMesa            int               NULL
HoraEntrada           datetime2         NULL
HoraSalida            datetime2         NULL
Turno                 nvarchar(20)      NULL
DiaSemana             nvarchar(20)      NULL
FechaSync             datetime2         NULL
```

---

## ✅ TABLAS CON DATOS

### Comercial_KPIs_Diarios_v2 (33 columnas)
**Últimos registros:**
| Unidad | Fecha | Ventas | PAX | Tickets |
|--------|-------|--------|-----|---------|
| 130° MERIDA | 2026-06-01 | $79,474.00 | 52 | 17 |
| LA ESTELAR | 2026-06-01 | $560.00 | 2 | 2 |
| 130° MERIDA | 2026-05-31 | $149,947.00 | 93 | 33 |
| 130° QUERETARO | 2026-05-31 | $53,119.00 | 36 | 11 |
| CIENFUEGOS | 2026-05-31 | $108,325.00 | 86 | 28 |

---

## ⏰ SCHEDULER JOBS REGISTRADOS

| JobID | JobName | Cron | Status | Last Run |
|-------|---------|------|--------|----------|
| SYNC-INTELIGENCIA-01 | inteligencia_comercial_sync | 0 * * * * | ACTIVE | 2026-06-02 01:00:02 |
| sync-sales | Sincronización de Ventas SQL | 0 * * * * | activo | 2026-06-01 16:21:19 |
| sync-vtiger | Importación Vtiger CRM | 0 0 * * * | activo | - |
| sync-inteligencia | Actualizar Vista Inteligencia | 0 */6 * * * | activo | - |
| recalc-kpis | Recálculo de KPIs Globales | */30 * * * * | activo | - |
| backup-db | Respaldo Completo EDARSAHUB | 0 2 * * 0 | activo | - |

---

## 📋 VISTAS RELEVANTES

### View_Sync_Sales_Detalle
Deserializa el campo `items` (JSON) de Sync_Sales usando OPENJSON.
```sql
-- Columnas:
IdTransaccion, UnidadNegocio, NumeroTicket, FechaHora, Pax, MontoTotal,
CodigoProducto_JSON, NombreProducto_JSON, Cantidad, PrecioUnitario, TotalLinea
```

### View_Inteligencia_Comercial
Vista consolidada para el dashboard.
```sql
-- Columnas:
UnidadNegocio, IdProducto, Producto, Familia, CasaProductora,
PorcentajeAlcohol, CantidadTotal, IngresoTotal, Propina, Pax, FranjaHoraria
```

---

## 🗂️ CATÁLOGO COMPLETO DE TABLAS (427)

### Esquema [Comercial]
- TableroEjecutivoCache
- v_TableroComercialConsolidado (VIEW)

### Esquema [dbo] - Activo Fijo (19 tablas)
ActivoFijo_ActivoMedidores, ActivoFijo_Activos, ActivoFijo_ActivosLibros, 
ActivoFijo_Alertas, ActivoFijo_Archivos, ActivoFijo_Autorizaciones, 
ActivoFijo_BajasActivos, ActivoFijo_ClaseActivo, ActivoFijo_Cotizaciones,
ActivoFijo_DepreciacionMovimientos, ActivoFijo_EstadoUsoActivo, 
ActivoFijo_EstatusActivo, ActivoFijo_EstatusOT, ActivoFijo_HistorialAsignaciones,
ActivoFijo_LecturasMedidor, ActivoFijo_LibrosDepreciacion, ActivoFijo_Medidores,
ActivoFijo_MetodosDepreciacion, ActivoFijo_MovimientosActivo, 
ActivoFijo_OrdenesTrabajo, ActivoFijo_OrdenTrabajoCostos, ActivoFijo_PlanesMantenimiento,
ActivoFijo_PrioridadOT, ActivoFijo_ReemplazosActivos, ActivoFijo_ReglasClaseLibro,
ActivoFijo_TipoActivo, ActivoFijo_TipoBaja, ActivoFijo_TipoMedidor,
ActivoFijo_TipoOT, ActivoFijo_TipoUbicacion, ActivoFijo_Ubicaciones

### Esquema [dbo] - Comercial (28 tablas)
Comercial_AlertasMargenDestinatarios, Comercial_AlertasMargenEnvios,
Comercial_AlertasMargenEventos, Comercial_AlertasMargenReglas,
Comercial_AlertasUmbralesSeveridad, Comercial_Competidores,
Comercial_CompetidoresCatalogo, Comercial_CompetidoresListas,
Comercial_CompetidoresListasDetalle, Comercial_CompetidoresMenuItems,
Comercial_CompetidoresUnidad, Comercial_Dashboard_Cache,
Comercial_ImpuestosCatalogo, Comercial_ImpuestosMapeo,
Comercial_ImpuestosOverrides, Comercial_ImpuestosTasas,
Comercial_KPIs_Cache, Comercial_KPIs_Diarios_v2, Comercial_KPIs_Historico,
Comercial_KPIs_Mensuales_v2, Comercial_Metas, Comercial_PreciosSugeridos,
Comercial_PricingAnalisisIA, Comercial_PricingBenchmarkProducto,
Comercial_RecetasSnapshot, Comercial_RecetasSnapshotDetalle,
Comercial_ReglasPrecio, Comercial_ReglasPrecioRangos,
Comercial_SimulacionesPrecios, Comercial_SolicitudesCambioPrecio,
Comercial_SolicitudesCambioPrecioHistorial, Comercial_SyncLog_v2,
Comercial_Ventas_Dia_Abiertas_v2

### Esquema [dbo] - CRM (33 tablas)
CRM_Actividades, CRM_ActividadesHistorial, CRM_Automation_Log,
CRM_Automation_Reglas, CRM_Cat_EstatusActividad, CRM_Cat_EstatusContrato,
CRM_Cat_EstatusLead, CRM_Cat_EstatusOportunidad, CRM_Cat_EstatusPropuesta,
CRM_Cat_MotivosGanada, CRM_Cat_MotivosPerdida, CRM_Cat_OrigenLead,
CRM_Cat_Prioridades, CRM_Cat_Sectores, CRM_Cat_TamanosCliente,
CRM_Cat_TiposActividad, CRM_Cat_TiposPipeline, CRM_ClientesSolicitudesAlta,
CRM_ClientesSolicitudesAltaHistorial, CRM_Config_PipelineEtapas,
CRM_Config_Pipelines, CRM_Contratos, CRM_Cuentas, CRM_ERPSyncLog,
CRM_Implementaciones, CRM_ImplementacionesEntregables, CRM_Integracion_Conectores,
CRM_Integracion_MapeoEtapas, CRM_Integracion_SyncLog, CRM_IntegracionesConflictos,
CRM_IntegracionesSyncLog, CRM_Leads, CRM_Oportunidad_Contactos,
CRM_Oportunidad_Documentos, CRM_Oportunidades, CRM_Oportunidades_HistorialEtapas,
CRM_OportunidadesHistorial, CRM_PostventaEncuestas, CRM_PostventaTickets,
CRM_Propuestas, CRM_Staging_Cuentas, CRM_Staging_Leads, CRM_Staging_Oportunidades,
CRM_Tareas, CRM_Trigger_Log, CRM_Triggers

### Esquema [dbo] - Sync (20+ tablas)
Sync_Control_Ejecuciones, Sync_Customers, Sync_Impuestos_Origen,
Sync_Inventory, Sync_KPI_Ventas_Unidades, Sync_Logs, Sync_Menus,
Sync_Mesas, Sync_Metas_Comerciales, Sync_Movimientos_Detalle,
**Sync_PAX_Detalle**, Sync_Payments (VIEW), Sync_Precios_Historicos,
Sync_Productos, Sync_Productos_Elaborados, Sync_Productos_Familias,
Sync_Productos_Insumos, Sync_Productos_Recetas, Sync_Productos_SubFamilias,
Sync_Purchases, Sync_Response_Cache, **Sync_Sales**, Sync_Ticket_Perfecto,
Sync_Token_Ledger, Sync_Ventas_Historicas, Sync_Ventas_PorDiaSemana,
Sync_Ventas_PorHora, Sync_Vtiger_Contactos, Sync_Vtiger_Cuentas,
Sync_Vtiger_Leads, Sync_Vtiger_Log, Sync_Vtiger_Oportunidades

---

## 🔧 ACCIONES RECOMENDADAS

1. **Poblar Sync_Sales**: El job `inteligencia_comercial_sync` está registrado y activo, pero las credenciales de los POS deben estar configuradas en producción para que extraiga datos.

2. **Poblar Sync_PAX_Detalle**: Requiere lógica específica para extraer detalle de comensales por mesa/cuenta.

3. **Fallback Activo**: El dashboard de Inteligencia Comercial usa `Comercial_KPIs_Diarios_v2` como fuente primaria y genera distribuciones proporcionales matemáticas mientras `Sync_Sales` esté vacía.

---

*Documento generado automáticamente - E1 Agent*
