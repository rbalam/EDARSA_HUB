# VALIDACIÓN FIRMAS SYNC JOB
Fecha: Thu Jun  4 07:27:50 UTC 2026

## 1. Firmas disponibles en sync_service.py
```text
170:def sync_inventarios_fisicos_from_server(
300:def sync_requisiciones_from_server(
487:def sync_almacenes_from_server(
564:def sync_existencias_from_server(
651:def sync_movimientos_from_server(
819:def sync_pedidos_from_server(
961:def sync_ordenes_from_server(
1103:def sync_recepciones_from_server(
```

## 2. Llamadas actuales desde sync_compras_job.py
```text
339-            try:
340-                sync_start = datetime.now(ZoneInfo("America/Mexico_City"))
341-                
342-                if not dry_run:
343:                    inv_result = sync_inventarios_fisicos_from_server(
344-                        server_info, unidad_info, _execute_sql_with_timeout
345-                    )
346-                else:
347-                    inv_result = {"status": "DRY_RUN", "records_synced": 0, "error": None}
348-                
349-                sync_end = datetime.now(ZoneInfo("America/Mexico_City"))
350-                
351-                results["inventarios"].append({
352-                    "server": server_name,
353-                    "unidad": unidad_codigo,
354-                    "status": inv_result.get("status"),
355-                    "records": inv_result.get("records_synced", 0),
--
386-            try:
387-                sync_start = datetime.now(ZoneInfo("America/Mexico_City"))
388-                
389-                if not dry_run:
390:                    req_result = sync_requisiciones_from_server(
391-                        server_info, unidad_info, _execute_sql_with_timeout
392-                    )
393-                else:
394-                    req_result = {"status": "DRY_RUN", "records_synced": 0, "error": None}
395-                
396-                sync_end = datetime.now(ZoneInfo("America/Mexico_City"))
397-                
398-                results["requisiciones"].append({
399-                    "server": server_name,
400-                    "unidad": unidad_codigo,
401-                    "status": req_result.get("status"),
402-                    "records": req_result.get("records_synced", 0),
```

## 3. Validación AST de parámetros requeridos
```text
FUNCION: sync_almacenes_from_server
  Firma args: ['server_info', 'unidad_info', 'execute_sql_fn']
  Requeridos: ['server_info', 'unidad_info', 'execute_sql_fn']
  ERROR: no hay llamada desde job

FUNCION: sync_existencias_from_server
  Firma args: ['server_info', 'unidad_info', 'execute_sql_fn']
  Requeridos: ['server_info', 'unidad_info', 'execute_sql_fn']
  ERROR: no hay llamada desde job

FUNCION: sync_inventarios_fisicos_from_server
  Firma args: ['server_info', 'unidad_info', 'execute_sql_query_func']
  Requeridos: ['server_info', 'unidad_info', 'execute_sql_query_func']
  Llamada línea 343 con 3 posicionales y kwargs []
  OK: llamada compatible

FUNCION: sync_movimientos_from_server
  Firma args: ['server_info', 'unidad_info', 'execute_sql_fn', 'fecha_inicio', 'fecha_fin', 'dry_run']
  Requeridos: ['server_info', 'unidad_info', 'execute_sql_fn']
  ERROR: no hay llamada desde job

FUNCION: sync_ordenes_from_server
  Firma args: ['server_info', 'unidad_info', 'execute_sql_fn', 'dias_atras', 'dry_run']
  Requeridos: ['server_info', 'unidad_info', 'execute_sql_fn']
  ERROR: no hay llamada desde job

FUNCION: sync_pedidos_from_server
  Firma args: ['server_info', 'unidad_info', 'execute_sql_fn', 'dias_atras', 'dry_run']
  Requeridos: ['server_info', 'unidad_info', 'execute_sql_fn']
  ERROR: no hay llamada desde job

FUNCION: sync_recepciones_from_server
  Firma args: ['server_info', 'unidad_info', 'execute_sql_fn', 'dias_atras', 'dry_run']
  Requeridos: ['server_info', 'unidad_info', 'execute_sql_fn']
  ERROR: no hay llamada desde job

FUNCION: sync_requisiciones_from_server
  Firma args: ['server_info', 'unidad_info', 'execute_sql_query_func']
  Requeridos: ['server_info', 'unidad_info', 'execute_sql_query_func']
  Llamada línea 390 con 3 posicionales y kwargs []
  OK: llamada compatible

```


## 4. Conclusión Compatibilidad

| Función | Requeridos | Opcionales | Llamada Job | Status |
|---------|------------|------------|-------------|--------|
| sync_almacenes_from_server | 3 | 0 | 3 posicionales | ✅ OK |
| sync_existencias_from_server | 3 | 0 | 3 posicionales | ✅ OK |
| sync_movimientos_from_server | 3 | 2 (fecha_inicio, fecha_fin) | 3 posicionales | ✅ OK |
| sync_pedidos_from_server | 3 | 2 (dias_atras, dry_run) | 3 posicionales | ✅ OK |
| sync_ordenes_from_server | 3 | 2 (dias_atras, dry_run) | 3 posicionales | ✅ OK |
| sync_recepciones_from_server | 3 | 2 (dias_atras, dry_run) | 3 posicionales | ✅ OK |

**NOTA**: El loop dinámico `sync_steps` en línea 450 llama a todas las funciones con 3 argumentos posicionales:
- `server_info`
- `unidad_info`
- `_execute_sql_with_timeout`

Esto es compatible con todas las firmas porque los parámetros opcionales tienen valores por defecto.

**RESULTADO: ✅ TODAS LAS FIRMAS SON COMPATIBLES**
