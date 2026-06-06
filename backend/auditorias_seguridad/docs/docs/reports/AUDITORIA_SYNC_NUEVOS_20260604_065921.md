# AUDITORIA FUNCIONES SYNC NUEVAS

## Funciones sync definidas
170:def sync_inventarios_fisicos_from_server(
300:def sync_requisiciones_from_server(
487:def sync_almacenes_from_server(
564:def sync_existencias_from_server(
651:def sync_movimientos_from_server(
755:def sync_pedidos_from_server(
851:def sync_ordenes_from_server(
945:def sync_recepciones_from_server(

## MERGE/INSERT/UPDATE en tablas destino
258:            UPDATE Compras_Inventarios_Fisicos_Sync 
268:                    INSERT INTO Compras_Inventarios_Fisicos_Sync
391:            UPDATE Compras_Requisiciones_Sync 
401:                    INSERT INTO Compras_Requisiciones_Sync
451:            INSERT INTO Compras_Sync_Log
539:                    MERGE INTO Inventario_Almacenes AS target
620:            UPDATE Inventario_Existencias SET EsActual = 0
628:                    INSERT INTO Inventario_Existencias
729:                    INSERT INTO Inventario_MovimientosDetalle
819:                    MERGE INTO Compras_Pedidos AS target
913:                    MERGE INTO Compras_Ordenes AS target
1009:                    MERGE INTO Compras_Recepciones AS target

## Validar NO hay conexiones LIVE en funciones sync
173:    execute_sql_query_func
182:        execute_sql_query_func: Función para ejecutar queries en el servidor origen
240:        rows = execute_sql_query_func(
303:    execute_sql_query_func
373:        rows = execute_sql_query_func(
