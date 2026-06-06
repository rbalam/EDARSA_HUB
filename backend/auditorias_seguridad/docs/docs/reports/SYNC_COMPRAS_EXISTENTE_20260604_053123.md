# BÚSQUEDA DE SINCRONIZACIÓN EXISTENTE - COMPRAS / INVENTARIOS
Fecha: Thu Jun  4 05:31:23 UTC 2026

## 1. Archivos relacionados con sync compras/inventarios
```text
/app/backend/api/admin_scheduler_resync.py
/app/backend/api/sync_receiver.py
/app/backend/api/sync_schemas.py
/app/backend/core/inventory_analysis_core.py
/app/backend/core/scheduler/jobs/crm_sync_job.py
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py
/app/backend/core/scheduler/jobs/inventarios_detector_job.py
/app/backend/core/scheduler/jobs/pedidos_detector_job.py
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py
/app/backend/core/scheduler/jobs/sync_compras_job.py
/app/backend/core/scheduler/jobs/sync_ingresos_job.py
/app/backend/core/scheduler/jobs/sync_nightly_comercial_job.py
/app/backend/core/scheduler/jobs/sync_propinas_tpv_job.py
/app/backend/core/scheduler/jobs/sync_short_comercial_job.py
/app/backend/core/scheduler/jobs/vtiger_sync_job.py
/app/backend/database/migrations/031_diagnostico_sync_sales_pax_detalle.sql
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py
/app/backend/modules/compras/__init__.py
/app/backend/modules/compras/eventos_compras.py
/app/backend/modules/compras/historical_kpis_repository.py
/app/backend/modules/compras/repository.py
/app/backend/modules/compras/repository_compras_sql.py
/app/backend/modules/compras/repository_pedidos_sql.py
/app/backend/modules/compras/routes.py
/app/backend/modules/compras/schemas.py
/app/backend/modules/compras/service.py
/app/backend/modules/compras/sync_service.py
/app/backend/modules/compras/system_type_utils.py
/app/backend/modules/configuracion/services/almacenes_sync_service.py
/app/backend/modules/crm/integration/sync_engine.py
/app/backend/modules/edge/gestor_sincronizacion_rafagas.py
/app/backend/modules/edge/motor_inventario_parametrico.py
/app/backend/modules/edge/sincronizador_catalogos_edge.py
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py
/app/backend/modules/finanzas/sync_cortes_mpro.py
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py
/app/backend/modules/finanzas/sync_propinas_mpro.py
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py
/app/backend/modules/inventarios/__init__.py
/app/backend/modules/inventarios/repository.py
/app/backend/modules/inventarios/routes.py
/app/backend/modules/inventarios/schemas.py
/app/backend/modules/inventarios/service.py
/app/backend/modules/sync_historicos/__init__.py
/app/backend/modules/sync_historicos/models.py
/app/backend/modules/sync_historicos/repository.py
/app/backend/modules/sync_historicos/service.py
/app/backend/modules/sync_historicos/sync_ventas.py
/app/backend/modules/sync_recetas/__init__.py
/app/backend/modules/sync_recetas/models.py
/app/backend/modules/sync_recetas/sync_recetas.py
/app/backend/modules/tablajeria/ordenes_service.py
/app/backend/modules/tablajeria/sync_service.py
/app/backend/scripts/ddl_sync_comercial_tablas.sql
/app/backend/scripts/ddl_sync_vtiger_tablas.sql
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py
/app/backend/scripts/paquete_piloto_sync_agent/sync_agent_piloto.py
/app/backend/scripts/run_historical_load_compras.py
/app/backend/scripts/sync_agent_piloto.py
/app/backend/scripts/sync_response_cache_finops.py
/app/backend/sql/automatizacion_inventarios_ddl.sql
/app/backend/tests/test_automatizacion_compras_fase4.py
/app/backend/tests/test_automatizacion_compras_fase43.py
/app/backend/tests/test_comparativo_inventarios.py
/app/backend/tests/test_compras_analisis.py
/app/backend/tests/test_compras_module.py
/app/backend/tests/test_inventory_analysis_filters.py
/app/backend/tests/test_mpro_inventory_analysis.py
/app/backend/tests/test_softrestaurant_inventory.py
/app/backend/tools/sync_sales_dry_run.py
```
## 2. Referencias a tablas destino EDARSAHUB
```text
/app/backend/modules/comercial/routes.py:217:        'tabla_requerida': 'Sync_Movimientos_Detalle',
/app/backend/modules/comercial/routes.py:3255:    Este endpoint requiere conexión LIVE. Bloqueado hasta migrar a Sync_Movimientos_Detalle.
/app/backend/modules/corporate_filters/router.py:329:            ["Inventario_Almacenes", "Sistema_Almacenes", "Almacenes", "Sync_Almacenes"],
/app/backend/modules/catalogos/schemas.py:64:            {"tabla": "Compras_OrdenesEstatus", "nombre": "Estatus de Órdenes", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:65:            {"tabla": "Compras_PedidosEstatus", "nombre": "Estatus de Pedidos", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:66:            {"tabla": "Compras_RecepcionesEstatus", "nombre": "Estatus de Recepciones", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:313:    "Compras_OrdenesEstatus": {
/app/backend/modules/catalogos/schemas.py:320:    "Compras_PedidosEstatus": {
/app/backend/modules/catalogos/schemas.py:327:    "Compras_RecepcionesEstatus": {
/app/backend/modules/compras/sync_service.py:9:- Compras_Requisiciones_Sync: Requisiciones/pedidos sincronizados
/app/backend/modules/compras/sync_service.py:129:            FROM Compras_Requisiciones_Sync
/app/backend/modules/compras/sync_service.py:391:            UPDATE Compras_Requisiciones_Sync 
/app/backend/modules/compras/sync_service.py:401:                    INSERT INTO Compras_Requisiciones_Sync
/app/backend/scripts/ddl_sync_comercial_tablas.sql:12:-- 4. Sync_Movimientos_Detalle
/app/backend/scripts/ddl_sync_comercial_tablas.sql:150:-- 4. Sync_Movimientos_Detalle
/app/backend/scripts/ddl_sync_comercial_tablas.sql:153:IF OBJECT_ID('dbo.Sync_Movimientos_Detalle', 'U') IS NULL
/app/backend/scripts/ddl_sync_comercial_tablas.sql:155:    CREATE TABLE dbo.Sync_Movimientos_Detalle (
/app/backend/scripts/ddl_sync_comercial_tablas.sql:185:    CREATE INDEX IX_Sync_Movimientos_ServerSucursal ON dbo.Sync_Movimientos_Detalle (ServerID, SucursalID);
/app/backend/scripts/ddl_sync_comercial_tablas.sql:186:    CREATE INDEX IX_Sync_Movimientos_Fecha ON dbo.Sync_Movimientos_Detalle (FechaOperacion);
/app/backend/scripts/ddl_sync_comercial_tablas.sql:187:    CREATE INDEX IX_Sync_Movimientos_Producto ON dbo.Sync_Movimientos_Detalle (ProductoID);
/app/backend/scripts/ddl_sync_comercial_tablas.sql:188:    CREATE INDEX IX_Sync_Movimientos_Cuenta ON dbo.Sync_Movimientos_Detalle (CuentaID);
/app/backend/scripts/ddl_sync_comercial_tablas.sql:190:    PRINT 'Tabla Sync_Movimientos_Detalle creada exitosamente';
/app/backend/scripts/ddl_sync_comercial_tablas.sql:284:    'Sync_Movimientos_Detalle',
/app/backend/scripts/consolidado_general_sistema_comercial.py:10:             Sync_Inventory, Sync_Purchases), funciones matemáticas de proyección,
/app/backend/scripts/consolidado_general_sistema_comercial.py:130:    IF OBJECT_ID('dbo.Sync_Inventory', 'U') IS NULL
/app/backend/scripts/consolidado_general_sistema_comercial.py:132:        CREATE TABLE dbo.Sync_Inventory (
/app/backend/scripts/consolidado_general_sistema_comercial.py:141:        CREATE NONCLUSTERED INDEX IX_SyncIndex_Inventory_Warehouse ON dbo.Sync_Inventory (warehouse);
/app/backend/scripts/consolidado_general_sistema_comercial.py:146:    IF OBJECT_ID('dbo.Sync_Purchases', 'U') IS NULL
/app/backend/scripts/consolidado_general_sistema_comercial.py:148:        CREATE TABLE dbo.Sync_Purchases (
/app/backend/scripts/consolidado_general_sistema_comercial.py:319:        SELECT 'Sync_Inventory' AS TableName, COUNT(1) AS RecordCount, MAX(last_audit) AS LastSyncTime, 'EDARSAHUB' AS Target FROM dbo.Sync_Inventory WITH (NOLOCK)
/app/backend/scripts/consolidado_general_sistema_comercial.py:321:        SELECT 'Sync_Purchases' AS TableName, COUNT(1) AS RecordCount, MAX(created_at) AS LastSyncTime, 'EDARSAHUB' AS Target FROM dbo.Sync_Purchases WITH (NOLOCK);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2466:-- TABLA: [dbo].[Compras_Ordenes]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2468:CREATE TABLE [dbo].[Compras_Ordenes] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2503:    CONSTRAINT [PK_Compras_Ordenes] PRIMARY KEY ([OrdenCompraID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2508:-- TABLA: [dbo].[Compras_OrdenesDetalle]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2510:CREATE TABLE [dbo].[Compras_OrdenesDetalle] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2534:    CONSTRAINT [PK_Compras_OrdenesDetalle] PRIMARY KEY ([DetalleOrdenCompraID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2539:-- TABLA: [dbo].[Compras_OrdenesEstatus]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2541:CREATE TABLE [dbo].[Compras_OrdenesEstatus] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2545:    CONSTRAINT [PK_Compras_OrdenesEstatus] PRIMARY KEY ([EstatusOrdenCompraID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2570:-- TABLA: [dbo].[Compras_Pedidos]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2572:CREATE TABLE [dbo].[Compras_Pedidos] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2605:    CONSTRAINT [PK_Compras_Pedidos] PRIMARY KEY ([PedidoCompraID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2610:-- TABLA: [dbo].[Compras_PedidosDetalle]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2612:CREATE TABLE [dbo].[Compras_PedidosDetalle] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2635:    CONSTRAINT [PK_Compras_PedidosDetalle] PRIMARY KEY ([DetallePedidoCompraID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2640:-- TABLA: [dbo].[Compras_PedidosEstatus]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2642:CREATE TABLE [dbo].[Compras_PedidosEstatus] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2646:    CONSTRAINT [PK_Compras_PedidosEstatus] PRIMARY KEY ([EstatusPedidoCompraID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2651:-- TABLA: [dbo].[Compras_Recepciones]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2653:CREATE TABLE [dbo].[Compras_Recepciones] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2677:    CONSTRAINT [PK_Compras_Recepciones] PRIMARY KEY ([RecepcionCompraID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2682:-- TABLA: [dbo].[Compras_RecepcionesDetalle]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2684:CREATE TABLE [dbo].[Compras_RecepcionesDetalle] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2704:    CONSTRAINT [PK_Compras_RecepcionesDetalle] PRIMARY KEY ([RecepcionDetalleID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2709:-- TABLA: [dbo].[Compras_RecepcionesEstatus]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2711:CREATE TABLE [dbo].[Compras_RecepcionesEstatus] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2715:    CONSTRAINT [PK_Compras_RecepcionesEstatus] PRIMARY KEY ([EstatusRecepcionID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2720:-- TABLA: [dbo].[Compras_Requisiciones_Sync]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2722:CREATE TABLE [dbo].[Compras_Requisiciones_Sync] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:2742:    CONSTRAINT [PK_Compras_Requisiciones_Sync] PRIMARY KEY ([id])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4560:-- TABLA: [dbo].[Inventario_Almacenes]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4562:CREATE TABLE [dbo].[Inventario_Almacenes] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4574:    CONSTRAINT [PK_Inventario_Almacenes] PRIMARY KEY ([AlmacenID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4579:-- TABLA: [dbo].[Inventario_Existencias]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4581:CREATE TABLE [dbo].[Inventario_Existencias] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4594:    CONSTRAINT [PK_Inventario_Existencias] PRIMARY KEY ([ExistenciaID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4599:-- TABLA: [dbo].[Inventario_Movimientos]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4601:CREATE TABLE [dbo].[Inventario_Movimientos] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4615:    CONSTRAINT [PK_Inventario_Movimientos] PRIMARY KEY ([MovimientoID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4620:-- TABLA: [dbo].[Inventario_MovimientosDetalle]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4622:CREATE TABLE [dbo].[Inventario_MovimientosDetalle] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4635:    CONSTRAINT [PK_Inventario_MovimientosDetalle] PRIMARY KEY ([MovimientoDetalleID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7576:-- TABLA: [dbo].[Sync_Inventory]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7578:CREATE TABLE [dbo].[Sync_Inventory] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7586:    CONSTRAINT [PK_Sync_Inventory] PRIMARY KEY ([sku])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7706:-- TABLA: [dbo].[Sync_Movimientos_Detalle]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7708:CREATE TABLE [dbo].[Sync_Movimientos_Detalle] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7736:    CONSTRAINT [PK_Sync_Movimientos_Detalle] PRIMARY KEY ([ID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7989:-- TABLA: [dbo].[Sync_Purchases]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7991:CREATE TABLE [dbo].[Sync_Purchases] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8000:    CONSTRAINT [PK_Sync_Purchases] PRIMARY KEY ([id])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10079:    FOREIGN KEY ([OrdenCompraID]) REFERENCES [dbo].[Compras_Ordenes]([OrdenCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10082:    FOREIGN KEY ([PedidoCompraID]) REFERENCES [dbo].[Compras_Pedidos]([PedidoCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10121:    FOREIGN KEY ([RecepcionDetalleID]) REFERENCES [dbo].[Compras_RecepcionesDetalle]([RecepcionDetalleID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10127:    FOREIGN KEY ([OrdenDetalleCompraID]) REFERENCES [dbo].[Compras_OrdenesDetalle]([DetalleOrdenCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10130:    FOREIGN KEY ([PedidoDetalleCompraID]) REFERENCES [dbo].[Compras_PedidosDetalle]([DetallePedidoCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10162:ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Autorizacion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10165:ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Comprador]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10168:ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_CondicionPago]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10171:ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Estatus]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10172:    FOREIGN KEY ([EstatusOrdenCompraID]) REFERENCES [dbo].[Compras_OrdenesEstatus]([EstatusOrdenCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10174:ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Moneda]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10177:ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Pedido]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10178:    FOREIGN KEY ([PedidoCompraID]) REFERENCES [dbo].[Compras_Pedidos]([PedidoCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10180:ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Proveedor]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10183:ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Solicitante]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10186:ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Sucursal]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10189:ALTER TABLE [dbo].[Compras_OrdenesDetalle] ADD CONSTRAINT [FK_Compras_OrdenesDetalle_Orden]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10190:    FOREIGN KEY ([OrdenCompraID]) REFERENCES [dbo].[Compras_Ordenes]([OrdenCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10192:ALTER TABLE [dbo].[Compras_OrdenesDetalle] ADD CONSTRAINT [FK_Compras_OrdenesDetalle_PedidoDetalle]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10193:    FOREIGN KEY ([PedidoDetalleCompraID]) REFERENCES [dbo].[Compras_PedidosDetalle]([DetallePedidoCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10195:ALTER TABLE [dbo].[Compras_OrdenesDetalle] ADD CONSTRAINT [FK_Compras_OrdenesDetalle_Presentacion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10198:ALTER TABLE [dbo].[Compras_OrdenesDetalle] ADD CONSTRAINT [FK_Compras_OrdenesDetalle_Producto]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10201:ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_Autorizacion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10204:ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_Comprador]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10207:ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_Estatus]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10208:    FOREIGN KEY ([EstatusPedidoCompraID]) REFERENCES [dbo].[Compras_PedidosEstatus]([EstatusPedidoCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10210:ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_Moneda]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10213:ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_ProveedorSugerido]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10216:ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_Solicitante]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10219:ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_Sucursal]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10222:ALTER TABLE [dbo].[Compras_PedidosDetalle] ADD CONSTRAINT [FK_Compras_PedidosDetalle_Pedido]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10223:    FOREIGN KEY ([PedidoCompraID]) REFERENCES [dbo].[Compras_Pedidos]([PedidoCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10225:ALTER TABLE [dbo].[Compras_PedidosDetalle] ADD CONSTRAINT [FK_Compras_PedidosDetalle_Presentacion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10228:ALTER TABLE [dbo].[Compras_PedidosDetalle] ADD CONSTRAINT [FK_Compras_PedidosDetalle_Producto]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10231:ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Almacen]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10232:    FOREIGN KEY ([AlmacenID]) REFERENCES [dbo].[Inventario_Almacenes]([AlmacenID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10234:ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Compra]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10237:ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Estatus]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10238:    FOREIGN KEY ([EstatusRecepcionID]) REFERENCES [dbo].[Compras_RecepcionesEstatus]([EstatusRecepcionID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10240:ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Movimiento]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10241:    FOREIGN KEY ([MovimientoInventarioID]) REFERENCES [dbo].[Inventario_Movimientos]([MovimientoID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10243:ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Orden]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10244:    FOREIGN KEY ([OrdenCompraID]) REFERENCES [dbo].[Compras_Ordenes]([OrdenCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10246:ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Proveedor]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10249:ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Recibio]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10252:ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Reviso]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10255:ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Sucursal]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10258:ALTER TABLE [dbo].[Compras_RecepcionesDetalle] ADD CONSTRAINT [FK_Compras_RecepcionesDetalle_CompraDetalle]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10261:ALTER TABLE [dbo].[Compras_RecepcionesDetalle] ADD CONSTRAINT [FK_Compras_RecepcionesDetalle_MovimientoDetalle]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10262:    FOREIGN KEY ([MovimientoDetalleID]) REFERENCES [dbo].[Inventario_MovimientosDetalle]([MovimientoDetalleID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10264:ALTER TABLE [dbo].[Compras_RecepcionesDetalle] ADD CONSTRAINT [FK_Compras_RecepcionesDetalle_OrdenDetalle]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10265:    FOREIGN KEY ([OrdenDetalleID]) REFERENCES [dbo].[Compras_OrdenesDetalle]([DetalleOrdenCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10267:ALTER TABLE [dbo].[Compras_RecepcionesDetalle] ADD CONSTRAINT [FK_Compras_RecepcionesDetalle_Presentacion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10270:ALTER TABLE [dbo].[Compras_RecepcionesDetalle] ADD CONSTRAINT [FK_Compras_RecepcionesDetalle_Producto]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10273:ALTER TABLE [dbo].[Compras_RecepcionesDetalle] ADD CONSTRAINT [FK_Compras_RecepcionesDetalle_Recepcion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10274:    FOREIGN KEY ([RecepcionCompraID]) REFERENCES [dbo].[Compras_Recepciones]([RecepcionCompraID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10345:ALTER TABLE [dbo].[Inventario_Almacenes] ADD CONSTRAINT [FK_Inventario_Almacenes_Sucursal]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10348:ALTER TABLE [dbo].[Inventario_Existencias] ADD CONSTRAINT [FK_Inventario_Existencias_Almacen]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10349:    FOREIGN KEY ([AlmacenID]) REFERENCES [dbo].[Inventario_Almacenes]([AlmacenID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10351:ALTER TABLE [dbo].[Inventario_Existencias] ADD CONSTRAINT [FK_Inventario_Existencias_Presentacion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10354:ALTER TABLE [dbo].[Inventario_Existencias] ADD CONSTRAINT [FK_Inventario_Existencias_Producto]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10357:ALTER TABLE [dbo].[Inventario_Existencias] ADD CONSTRAINT [FK_Inventario_Existencias_Sucursal]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10360:ALTER TABLE [dbo].[Inventario_Movimientos] ADD CONSTRAINT [FK_Inventario_Movimientos_Almacen]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10361:    FOREIGN KEY ([AlmacenID]) REFERENCES [dbo].[Inventario_Almacenes]([AlmacenID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10363:ALTER TABLE [dbo].[Inventario_Movimientos] ADD CONSTRAINT [FK_Inventario_Movimientos_Sucursal]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10366:ALTER TABLE [dbo].[Inventario_Movimientos] ADD CONSTRAINT [FK_Inventario_Movimientos_Tipo]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10369:ALTER TABLE [dbo].[Inventario_Movimientos] ADD CONSTRAINT [FK_Inventario_Movimientos_Usuario]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10372:ALTER TABLE [dbo].[Inventario_MovimientosDetalle] ADD CONSTRAINT [FK_Inventario_MovimientosDetalle_Movimiento]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10373:    FOREIGN KEY ([MovimientoID]) REFERENCES [dbo].[Inventario_Movimientos]([MovimientoID]);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10375:ALTER TABLE [dbo].[Inventario_MovimientosDetalle] ADD CONSTRAINT [FK_Inventario_MovimientosDetalle_Presentacion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10378:ALTER TABLE [dbo].[Inventario_MovimientosDetalle] ADD CONSTRAINT [FK_Inventario_MovimientosDetalle_Producto]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11624:CREATE NONCLUSTERED INDEX [IX_Compras_Ordenes_Autorizacion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11625:    ON [dbo].[Compras_Ordenes] (AutorizacionID);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11627:CREATE NONCLUSTERED INDEX [IX_Compras_Ordenes_Estatus]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11628:    ON [dbo].[Compras_Ordenes] (EstatusOrdenCompraID, FechaOrden);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11630:CREATE NONCLUSTERED INDEX [IX_Compras_Ordenes_Pedido]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11631:    ON [dbo].[Compras_Ordenes] (PedidoCompraID);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11633:CREATE NONCLUSTERED INDEX [IX_Compras_Ordenes_Proveedor_Fecha]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11634:    ON [dbo].[Compras_Ordenes] (ProveedorID, FechaOrden);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11636:CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_Ordenes_FolioOrden]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11637:    ON [dbo].[Compras_Ordenes] (FolioOrden);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11639:CREATE NONCLUSTERED INDEX [IX_Compras_OrdenesDetalle_PedidoDetalle]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11640:    ON [dbo].[Compras_OrdenesDetalle] (PedidoDetalleCompraID);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11642:CREATE NONCLUSTERED INDEX [IX_Compras_OrdenesDetalle_Producto]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11643:    ON [dbo].[Compras_OrdenesDetalle] (ProductoID, PresentacionProductoID);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11645:CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_OrdenesDetalle_Renglon]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11646:    ON [dbo].[Compras_OrdenesDetalle] (OrdenCompraID, Renglon);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11648:CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_OrdenesEstatus_Descripcion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11649:    ON [dbo].[Compras_OrdenesEstatus] (Descripcion);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11654:CREATE NONCLUSTERED INDEX [IX_Compras_Pedidos_Autorizacion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11655:    ON [dbo].[Compras_Pedidos] (AutorizacionID);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11657:CREATE NONCLUSTERED INDEX [IX_Compras_Pedidos_Estatus]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11658:    ON [dbo].[Compras_Pedidos] (EstatusPedidoCompraID, FechaPedido);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11660:CREATE NONCLUSTERED INDEX [IX_Compras_Pedidos_Sucursal_Fecha]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11661:    ON [dbo].[Compras_Pedidos] (SucursalID, FechaPedido);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11663:CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_Pedidos_FolioPedido]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11664:    ON [dbo].[Compras_Pedidos] (FolioPedido);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11666:CREATE NONCLUSTERED INDEX [IX_Compras_PedidosDetalle_Producto]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11667:    ON [dbo].[Compras_PedidosDetalle] (ProductoID, PresentacionProductoID);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11669:CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_PedidosDetalle_Renglon]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11670:    ON [dbo].[Compras_PedidosDetalle] (PedidoCompraID, Renglon);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11672:CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_PedidosEstatus_Descripcion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11673:    ON [dbo].[Compras_PedidosEstatus] (Descripcion);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11675:CREATE NONCLUSTERED INDEX [IX_Compras_Recepciones_Estatus]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11676:    ON [dbo].[Compras_Recepciones] (EstatusRecepcionID, FechaRecepcion);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11678:CREATE NONCLUSTERED INDEX [IX_Compras_Recepciones_ProveedorFecha]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11679:    ON [dbo].[Compras_Recepciones] (ProveedorID, FechaRecepcion);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11681:CREATE NONCLUSTERED INDEX [IX_Compras_Recepciones_SucursalAlmacenFecha]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11682:    ON [dbo].[Compras_Recepciones] (SucursalID, AlmacenID, FechaRecepcion);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11684:CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_Recepciones_Folio]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11685:    ON [dbo].[Compras_Recepciones] (FolioRecepcion);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11687:CREATE NONCLUSTERED INDEX [IX_Compras_RecepcionesDetalle_Producto]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11688:    ON [dbo].[Compras_RecepcionesDetalle] (ProductoID, PresentacionProductoID, RecepcionCompraID);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11690:CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_RecepcionesDetalle_Renglon]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11691:    ON [dbo].[Compras_RecepcionesDetalle] (RecepcionCompraID, Renglon);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11693:CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_RecepcionesEstatus_Descripcion]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11694:    ON [dbo].[Compras_RecepcionesEstatus] (Descripcion);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11697:    ON [dbo].[Compras_Requisiciones_Sync] (fecha);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11700:    ON [dbo].[Compras_Requisiciones_Sync] (server_id);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11703:    ON [dbo].[Compras_Requisiciones_Sync] (unidad_negocio_id);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11706:    ON [dbo].[Compras_Requisiciones_Sync] (folio, server_id, tipo);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11978:CREATE UNIQUE NONCLUSTERED INDEX [UQ_Inventario_Almacenes_Sucursal_Codigo]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11979:    ON [dbo].[Inventario_Almacenes] (SucursalID, CodigoAlmacen);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11981:CREATE NONCLUSTERED INDEX [IX_Inventario_Existencias_Consulta]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11982:    ON [dbo].[Inventario_Existencias] (ExistenciaActual, CostoPromedio, UltimaFechaMovimiento, SucursalID, AlmacenID, ProductoID, PresentacionProductoID);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11984:CREATE UNIQUE NONCLUSTERED INDEX [UQ_Inventario_Existencias_Clave]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11985:    ON [dbo].[Inventario_Existencias] (SucursalID, AlmacenID, ProductoID, PresentacionProductoID);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11987:CREATE NONCLUSTERED INDEX [IX_Inventario_Movimientos_Ref]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11988:    ON [dbo].[Inventario_Movimientos] (ReferenciaTipo, ReferenciaID, FechaMovimiento);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11990:CREATE NONCLUSTERED INDEX [IX_Inventario_Movimientos_SucursalAlmacenFecha]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11991:    ON [dbo].[Inventario_Movimientos] (SucursalID, AlmacenID, FechaMovimiento);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11993:CREATE NONCLUSTERED INDEX [IX_Inventario_MovimientosDetalle_Producto]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:11994:    ON [dbo].[Inventario_MovimientosDetalle] (ProductoID, PresentacionProductoID, MovimientoID);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:12633:    ON [dbo].[Sync_Inventory] (warehouse);
/app/backend/server.py:7331:    1. Primero intenta leer de EDARSAHUB (tabla Compras_Requisiciones_Sync)
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:10:- Sync_Movimientos_Detalle
/app/backend/core/scheduler/jobs/sync_compras_job.py:16:- Compras_Requisiciones_Sync
```
## 3. Referencias a MERGE/INSERT en tablas de compras/inventarios
```text
/app/backend/modules/compras/repository_compras_sql.py:238:                UPDATE SET 
/app/backend/modules/compras/eventos_compras.py:159:                INSERT INTO Compras_Eventos_Pendientes (
/app/backend/modules/compras/historical_kpis_repository.py:174:            UPDATE Compras_KPIs_Historico SET
/app/backend/modules/compras/historical_kpis_repository.py:219:            INSERT INTO Compras_KPIs_Historico (
/app/backend/modules/compras/sync_service.py:268:                    INSERT INTO Compras_Inventarios_Fisicos_Sync
/app/backend/modules/compras/sync_service.py:401:                    INSERT INTO Compras_Requisiciones_Sync
/app/backend/modules/compras/sync_service.py:451:            INSERT INTO Compras_Sync_Log
/app/backend/modules/compras/repository_pedidos_sql.py:318:            INSERT INTO Compras_Eventos_Pendientes (
/app/backend/server.py:9108:                INSERT INTO Auditoria_Inventario_Provisional 
/app/backend/core/scheduler/jobs/sync_compras_job.py:101:                    UPDATE Sync_Control_Ejecuciones SET Status='TIMEOUT', FinishedAtMexico=%s
/app/backend/core/scheduler/jobs/sync_compras_job.py:114:            INSERT INTO Sync_Control_Ejecuciones (
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:91:                    UPDATE Sync_Control_Ejecuciones SET Status='TIMEOUT', FinishedAtMexico=%s
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:101:            INSERT INTO Sync_Control_Ejecuciones (
```
