# FASE 2 - ORIGEN SYNC COMPRAS / INVENTARIOS
Fecha: Thu Jun  4 06:50:23 UTC 2026

## 1. Código actual de sync_compras_job.py
```python
# FILE: /app/backend/core/scheduler/jobs/sync_compras_job.py
6:Sincroniza datos de inventarios físicos y requisiciones desde los servidores
7:físicos (SoftRestaurant, MPRO) hacia las tablas intermedias en EDARSAHUB SQL.
15:- Compras_Inventarios_Fisicos_Sync
16:- Compras_Requisiciones_Sync
17:- Compras_Sync_Log
37:    sync_inventarios_fisicos_from_server,
38:    sync_requisiciones_from_server,
64:def _acquire_sync_lock(run_id: str) -> bool:
73:            server=EDARSAHUB_CONFIG['host'],
87:            SELECT SyncControlID, SyncRunID, StartedAtMexico
88:            FROM Sync_Control_Ejecuciones
101:                    UPDATE Sync_Control_Ejecuciones SET Status='TIMEOUT', FinishedAtMexico=%s
114:            INSERT INTO Sync_Control_Ejecuciones (
129:def _release_sync_lock(run_id: str, status: str, processed: int, errors: int, error_msg: str = None):
133:            server=EDARSAHUB_CONFIG['host'],
144:        cursor.execute("SELECT StartedAtMexico FROM Sync_Control_Ejecuciones WHERE SyncRunID=%s", (run_id,))
154:            UPDATE Sync_Control_Ejecuciones
169:def _execute_sql_with_timeout(host, port, database, username, password, query, timeout_seconds=30):
191:def _get_servers_to_sync() -> List[Dict]:
204:            SELECT 
205:                s.id, s.nombre as server_name, s.host, s.port, s.database_name,
208:            FROM Servidores_Conexiones s
209:            LEFT JOIN Unidades_Negocio u ON u.server_id = CAST(s.id AS NVARCHAR(36))
212:              AND s.system_type IN ('SOFTRESTAURANT', 'MPRO', 'MANAGEMENTPRO', 'SOFTRESTAURANT_PRO')
218:        servers = []
226:                    logger.warning(f"[SYNC-COMPRAS] No se pudo desencriptar password de {row['server_name']}: {e}")
229:            servers.append({
231:                'name': row.get('server_name', ''),
243:        logger.info(f"[SYNC-COMPRAS] Servidores encontrados: {len(servers)}")
244:        return servers
255:def execute_sync_compras(dry_run: bool = False) -> Dict[str, Any]:
260:        dry_run: Si True, no guarda cambios en la base de datos
281:        "requisiciones": []
287:        servers = _get_servers_to_sync()
289:        if not servers:
299:        for server in servers:
300:            server_name = server.get('name', 'UNKNOWN')
301:            unidad_codigo = server.get('unidad_codigo', '')
303:            logger.info(f"[SYNC-COMPRAS] Procesando: {server_name} ({unidad_codigo})")
305:            if not server.get('host') or not server.get('password'):
306:                logger.warning(f"[SYNC-COMPRAS] Servidor {server_name} sin host/password - Saltando")
307:                error_messages.append(f"{server_name}: Sin credenciales")
311:            server_info = {
312:                'id': server['id'],
313:                'host': server['host'],
314:                'port': server['port'],
315:                'database': server['database'],
316:                'username': server['username'],
317:                'password': server['password'],
318:                'system_type': server['system_type'],
321:                'id': server['unidad_id'],
323:                'nombre': server['unidad_nombre'],
330:                if not dry_run:
331:                    inv_result = sync_inventarios_fisicos_from_server(
332:                        server_info, unidad_info, _execute_sql_with_timeout
340:                    "server": server_name,
349:                    logger.info(f"[SYNC-COMPRAS] ✅ Inventarios {server_name}: {inv_result.get('records_synced', 0)} registros")
352:                    error_messages.append(f"{server_name} INV: {inv_result.get('error', 'Error desconocido')}")
353:                    logger.warning(f"[SYNC-COMPRAS] ❌ Inventarios {server_name}: {inv_result.get('error')}")
356:                if not dry_run:
359:                        server_id=server_info['id'],
369:                logger.error(f"[SYNC-COMPRAS] Error sincronizando inventarios {server_name}: {e}")
371:                error_messages.append(f"{server_name} INV: {str(e)[:100]}")
377:                if not dry_run:
378:                    req_result = sync_requisiciones_from_server(
379:                        server_info, unidad_info, _execute_sql_with_timeout
386:                results["requisiciones"].append({
387:                    "server": server_name,
396:                    logger.info(f"[SYNC-COMPRAS] ✅ Requisiciones {server_name}: {req_result.get('records_synced', 0)} registros")
399:                    error_messages.append(f"{server_name} REQ: {req_result.get('error', 'Error desconocido')}")
400:                    logger.warning(f"[SYNC-COMPRAS] ❌ Requisiciones {server_name}: {req_result.get('error')}")
403:                if not dry_run:
406:                        server_id=server_info['id'],
416:                logger.error(f"[SYNC-COMPRAS] Error sincronizando requisiciones {server_name}: {e}")
418:                error_messages.append(f"{server_name} REQ: {str(e)[:100]}")
444:            "servers_processed": len(servers),
465:async def run_sync_compras_job():
479:def get_job_config() -> Dict:
487:        "description": "Sincroniza inventarios físicos y requisiciones desde servidores origen hacia EDARSAHUB SQL",
```

## 2. Código actual de compras/sync_service.py
```python
# FILE: /app/backend/modules/compras/sync_service.py
8:- Compras_Inventarios_Fisicos_Sync: Inventarios físicos sincronizados
9:- Compras_Requisiciones_Sync: Requisiciones/pedidos sincronizados
10:- Compras_Sync_Log: Log de sincronizaciones
30:def get_edarsahub_connection():
33:        server=EDARSAHUB_CONFIG['host'],
46:def obtener_inventarios_fisicos_sync(
48:    server_id: str = None,
50:    almacen: str = None,
62:            SELECT 
63:                folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
65:                unidad_negocio_codigo, server_id, system_type,
67:            FROM Compras_Inventarios_Fisicos_Sync
76:        if server_id:
77:            query += " AND LOWER(server_id) = LOWER(%s)"
78:            params.append(server_id)
84:        if almacen and almacen != 'TODOS':
85:            query += " AND almacen LIKE %s"
86:            params.append(f'%{almacen}%')
109:def obtener_requisiciones_sync(
111:    server_id: str = None,
116:    Obtiene requisiciones/pedidos DESDE EDARSAHUB (sincronizados).
124:            SELECT 
127:                unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
129:            FROM Compras_Requisiciones_Sync
138:        if server_id:
139:            query += " AND server_id = %s"
140:            params.append(server_id)
162:        logger.error(f"[SYNC-READ] Error obteniendo requisiciones: {e}")
170:def sync_inventarios_fisicos_from_server(
171:    server_info: Dict,
180:        server_info: Diccionario con host, port, database, username, password, system_type
189:    server_id = server_info.get('id')
190:    system_type = server_info.get('system_type', '')
199:            # MPRO usa tabla "Fisico" (no Fisico_Inventario)
201:                SELECT 
204:                    A.Al_Descripcion as almacen,
205:                    A.Al_Cve_Almacen as almacen_id,
211:                FROM Fisico F
212:                INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
213:                LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
219:            # SoftRestaurant usa tabla "invfisico"
221:                SELECT 
224:                    A.nombre as almacen,
225:                    CAST(A.idalmacen AS VARCHAR) as almacen_id,
231:                FROM invfisico INV
232:                LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
241:            server_info['host'],
242:            server_info['port'],
243:            server_info['database'],
244:            server_info['username'],
245:            server_info['password'],
258:            UPDATE Compras_Inventarios_Fisicos_Sync 
260:            WHERE server_id = %s AND sync_status = 'ACTIVE'
261:        """, (server_id,))
268:                    INSERT INTO Compras_Inventarios_Fisicos_Sync
269:                    (unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
270:                     folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
274:                    unidad_id, unidad_codigo, server_id, system_type,
277:                    row.get('almacen', ''),
278:                    str(row.get('almacen_id', '')),
300:def sync_requisiciones_from_server(
301:    server_info: Dict,
306:    Sincroniza requisiciones/pedidos desde un servidor físico a EDARSAHUB.
310:    server_id = server_info.get('id')
311:    system_type = server_info.get('system_type', '')
315:    logger.info(f"[SYNC] Iniciando sync requisiciones: {unidad_codigo} ({system_type})")
321:                SELECT 
337:                FROM Orden_Compra OC
338:                LEFT JOIN Proveedor P ON P.Pv_Cve_Proveedor = OC.Pv_Cve_Proveedor
339:                LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = OC.Sc_Cve_Sucursal
346:                SELECT 
355:                    (SELECT COUNT(*) FROM ordenescompramov WHERE idOrdenCompra = OC.idOrdenCompra) as total_productos,
363:                FROM ordenescompra OC
364:                LEFT JOIN proveedores P ON P.idProveedor = OC.idProveedor
374:            server_info['host'],
375:            server_info['port'],
376:            server_info['database'],
377:            server_info['username'],
378:            server_info['password'],
391:            UPDATE Compras_Requisiciones_Sync 
393:            WHERE server_id = %s AND sync_status = 'ACTIVE'
394:        """, (server_id,))
401:                    INSERT INTO Compras_Requisiciones_Sync
402:                    (unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
408:                    unidad_id, unidad_codigo, server_id, system_type,
423:                logger.warning(f"[SYNC] Error insertando requisición {row.get('folio')}: {e}")
432:        logger.error(f"[SYNC] Error sync requisiciones {unidad_codigo}: {e}")
436:def log_sync_operation(
438:    server_id: str,
451:            INSERT INTO Compras_Sync_Log
452:            (unidad_negocio_id, server_id, sync_type, sync_start, sync_end, 
456:            unidad_negocio_id, server_id, sync_type,
465:def get_last_sync_info(server_id: str, sync_type: str) -> Optional[Dict]:
471:            SELECT TOP 1 * FROM Compras_Sync_Log
472:            WHERE server_id = %s AND sync_type = %s
474:        """, (server_id, sync_type))
```

## 3. Tablas EDARSAHUB destino disponibles
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
/app/backend/modules/compras/sql_first_repository.py:42:        FROM dbo.Compras_PedidosDetalle d
/app/backend/modules/compras/sql_first_repository.py:43:        INNER JOIN dbo.Compras_Pedidos p
/app/backend/modules/compras/sql_first_repository.py:68:        FROM dbo.Inventario_MovimientosDetalle d
/app/backend/modules/compras/sql_first_repository.py:69:        INNER JOIN dbo.Inventario_Movimientos m
/app/backend/modules/compras/sql_first_repository.py:71:        LEFT JOIN dbo.Inventario_Almacenes a
/app/backend/modules/compras/sql_first_repository.py:84:        SELECT 'Compras_Pedidos' AS Tabla, COUNT(*) AS Registros FROM dbo.Compras_Pedidos
/app/backend/modules/compras/sql_first_repository.py:85:        UNION ALL SELECT 'Compras_PedidosDetalle', COUNT(*) FROM dbo.Compras_PedidosDetalle
/app/backend/modules/compras/sql_first_repository.py:86:        UNION ALL SELECT 'Compras_Ordenes', COUNT(*) FROM dbo.Compras_Ordenes
/app/backend/modules/compras/sql_first_repository.py:87:        UNION ALL SELECT 'Compras_OrdenesDetalle', COUNT(*) FROM dbo.Compras_OrdenesDetalle
/app/backend/modules/compras/sql_first_repository.py:88:        UNION ALL SELECT 'Compras_Recepciones', COUNT(*) FROM dbo.Compras_Recepciones
/app/backend/modules/compras/sql_first_repository.py:89:        UNION ALL SELECT 'Compras_RecepcionesDetalle', COUNT(*) FROM dbo.Compras_RecepcionesDetalle
/app/backend/modules/compras/sql_first_repository.py:91:        UNION ALL SELECT 'Inventario_Almacenes', COUNT(*) FROM dbo.Inventario_Almacenes
/app/backend/modules/compras/sql_first_repository.py:92:        UNION ALL SELECT 'Inventario_Existencias', COUNT(*) FROM dbo.Inventario_Existencias
/app/backend/modules/compras/sql_first_repository.py:93:        UNION ALL SELECT 'Inventario_Movimientos', COUNT(*) FROM dbo.Inventario_Movimientos
/app/backend/modules/compras/sql_first_repository.py:94:        UNION ALL SELECT 'Inventario_MovimientosDetalle', COUNT(*) FROM dbo.Inventario_MovimientosDetalle;
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
/app/backend/server.py:874:    UNION ALL SELECT 'Compras_Pedidos', COUNT(*) FROM dbo.Compras_Pedidos
/app/backend/server.py:875:    UNION ALL SELECT 'Compras_PedidosDetalle', COUNT(*) FROM dbo.Compras_PedidosDetalle
/app/backend/server.py:876:    UNION ALL SELECT 'Compras_Ordenes', COUNT(*) FROM dbo.Compras_Ordenes
/app/backend/server.py:877:    UNION ALL SELECT 'Compras_OrdenesDetalle', COUNT(*) FROM dbo.Compras_OrdenesDetalle
/app/backend/server.py:878:    UNION ALL SELECT 'Compras_Recepciones', COUNT(*) FROM dbo.Compras_Recepciones
/app/backend/server.py:879:    UNION ALL SELECT 'Compras_RecepcionesDetalle', COUNT(*) FROM dbo.Compras_RecepcionesDetalle
/app/backend/server.py:880:    UNION ALL SELECT 'Inventario_Almacenes', COUNT(*) FROM dbo.Inventario_Almacenes
/app/backend/server.py:881:    UNION ALL SELECT 'Inventario_Existencias', COUNT(*) FROM dbo.Inventario_Existencias
/app/backend/server.py:882:    UNION ALL SELECT 'Inventario_Movimientos', COUNT(*) FROM dbo.Inventario_Movimientos
/app/backend/server.py:883:    UNION ALL SELECT 'Inventario_MovimientosDetalle', COUNT(*) FROM dbo.Inventario_MovimientosDetalle
/app/backend/server.py:7844:    Este endpoint lee EXCLUSIVAMENTE de dbo.Compras_Pedidos y dbo.Compras_PedidosDetalle.
/app/backend/server.py:7904:            (SELECT COUNT(*) FROM dbo.Compras_PedidosDetalle d WHERE d.PedidoID = p.PedidoID) AS total_productos
/app/backend/server.py:7905:        FROM dbo.Compras_Pedidos p
/app/backend/server.py:8783:    - Compras_Pedidos
/app/backend/server.py:8784:    - Compras_PedidosDetalle
/app/backend/server.py:8833:            FROM dbo.Compras_PedidosDetalle d
/app/backend/server.py:8834:            INNER JOIN dbo.Compras_Pedidos p
/app/backend/server.py:10074:    - Inventario_Movimientos
/app/backend/server.py:10075:    - Inventario_MovimientosDetalle
/app/backend/server.py:10076:    - Inventario_Almacenes
/app/backend/server.py:10133:        FROM dbo.Inventario_MovimientosDetalle d
/app/backend/server.py:10134:        INNER JOIN dbo.Inventario_Movimientos m
/app/backend/server.py:10136:        LEFT JOIN dbo.Inventario_Almacenes a
/app/backend/server.py:10915:    Lee de dbo.Compras_Recepciones (facturas recibidas).
/app/backend/server.py:10968:        FROM dbo.Compras_Recepciones
/app/backend/server.py:11002:    Lee de dbo.Compras_RecepcionesDetalle.
/app/backend/server.py:11041:        FROM dbo.Compras_RecepcionesDetalle d
/app/backend/server.py:11042:        INNER JOIN dbo.Compras_Recepciones r ON r.RecepcionID = d.RecepcionID
/app/backend/server.py:11116:        FROM dbo.Inventario_MovimientosDetalle d
/app/backend/server.py:11117:        INNER JOIN dbo.Inventario_Movimientos m ON m.MovimientoID = d.MovimientoID
/app/backend/server.py:11118:        LEFT JOIN dbo.Inventario_Almacenes a ON a.AlmacenID = m.AlmacenID
/app/backend/server.py:11165:    Agrega datos de Compras_Pedidos, Compras_Recepciones, Inventario_Movimientos.
/app/backend/server.py:11209:            FROM dbo.Compras_Pedidos
/app/backend/server.py:11218:            FROM dbo.Compras_Recepciones
/app/backend/server.py:11229:            FROM dbo.Inventario_Movimientos
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:10:- Sync_Movimientos_Detalle
```
