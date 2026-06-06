# AUDITORÍA INTEGRACIÓN SYNC COMPRAS JOB
Fecha: Thu Jun  4 07:20:08 UTC 2026

## 1. Funciones disponibles en sync_service.py
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

## 2. Imports actuales en sync_compras_job.py
```text
36:from modules.compras.sync_service import (
```

## 3. execute_sync_compras actual
```python
235-                'username': row.get('username', ''),
236-                'password': password,
237-                'system_type': row.get('system_type', ''),
238-                'unidad_id': str(row.get('unidad_id', '')),
239-                'unidad_codigo': row.get('unidad_codigo', ''),
240-                'unidad_nombre': row.get('unidad_nombre', ''),
241-            })
242-        
243-        logger.info(f"[SYNC-COMPRAS] Servidores encontrados: {len(servers)}")
244-        return servers
245-        
246-    except Exception as e:
247-        logger.error(f"[SYNC-COMPRAS] Error obteniendo servidores: {e}")
248-        return []
249-
250-
251-# =============================================================================
252-# FUNCIÓN PRINCIPAL DE EJECUCIÓN
253-# =============================================================================
254-
255:def execute_sync_compras(dry_run: bool = False) -> Dict[str, Any]:
256-    """
257-    Ejecuta la sincronización completa de Compras.
258-    
259-    Args:
260-        dry_run: Si True, no guarda cambios en la base de datos
261-    
262-    Returns:
263-        Dict con resultados de la sincronización
264-    """
265-    run_id = f"COMPRAS-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
266-    logger.info(f"[SYNC-COMPRAS] ========== INICIO SINCRONIZACIÓN {run_id} ==========")
267-    
268-    # Adquirir lock
269-    if not _acquire_sync_lock(run_id):
270-        return {
271-            "status": "SKIPPED",
272-            "reason": "Lock activo - otra sincronización en curso",
273-            "run_id": run_id
274-        }
275-    
276-    start_time = datetime.now(ZoneInfo("America/Mexico_City"))
277-    total_processed = 0
278-    total_errors = 0
279-    results = {
280-        "inventarios": [],
281-        "requisiciones": []
282-    }
283-    error_messages = []
284-    
285-    try:
286-        # Obtener servidores
287-        servers = _get_servers_to_sync()
288-        
289-        if not servers:
290-            logger.warning("[SYNC-COMPRAS] No hay servidores configurados para sincronizar")
291-            _release_sync_lock(run_id, "WARNING", 0, 0, "Sin servidores configurados")
292-            return {
293-                "status": "WARNING",
294-                "message": "No hay servidores configurados",
295-                "run_id": run_id
296-            }
297-        
298-        # Sincronizar cada servidor
299-        for server in servers:
300-            server_name = server.get('name', 'UNKNOWN')
301-            unidad_codigo = server.get('unidad_codigo', '')
302-            
303-            logger.info(f"[SYNC-COMPRAS] Procesando: {server_name} ({unidad_codigo})")
304-            
305-            if not server.get('host') or not server.get('password'):
306-                logger.warning(f"[SYNC-COMPRAS] Servidor {server_name} sin host/password - Saltando")
307-                error_messages.append(f"{server_name}: Sin credenciales")
308-                total_errors += 1
309-                continue
310-            
311-            server_info = {
312-                'id': server['id'],
313-                'host': server['host'],
314-                'port': server['port'],
315-                'database': server['database'],
316-                'username': server['username'],
317-                'password': server['password'],
318-                'system_type': server['system_type'],
319-            }
320-            unidad_info = {
321-                'id': server['unidad_id'],
322-                'codigo': unidad_codigo,
323-                'nombre': server['unidad_nombre'],
324-            }
325-            
326-            # Sincronizar Inventarios Físicos
327-            try:
328-                sync_start = datetime.now(ZoneInfo("America/Mexico_City"))
329-                
330-                if not dry_run:
331-                    inv_result = sync_inventarios_fisicos_from_server(
332-                        server_info, unidad_info, _execute_sql_with_timeout
333-                    )
334-                else:
335-                    inv_result = {"status": "DRY_RUN", "records_synced": 0, "error": None}
336-                
337-                sync_end = datetime.now(ZoneInfo("America/Mexico_City"))
338-                
339-                results["inventarios"].append({
340-                    "server": server_name,
341-                    "unidad": unidad_codigo,
342-                    "status": inv_result.get("status"),
343-                    "records": inv_result.get("records_synced", 0),
344-                    "error": inv_result.get("error")
345-                })
346-                
347-                if inv_result.get("status") == "OK" or inv_result.get("status") == "DRY_RUN":
348-                    total_processed += inv_result.get("records_synced", 0)
349-                    logger.info(f"[SYNC-COMPRAS] ✅ Inventarios {server_name}: {inv_result.get('records_synced', 0)} registros")
350-                else:
351-                    total_errors += 1
352-                    error_messages.append(f"{server_name} INV: {inv_result.get('error', 'Error desconocido')}")
353-                    logger.warning(f"[SYNC-COMPRAS] ❌ Inventarios {server_name}: {inv_result.get('error')}")
354-                
355-                # Log en tabla de sync
356-                if not dry_run:
357-                    log_sync_operation(
358-                        unidad_negocio_id=unidad_info['id'],
359-                        server_id=server_info['id'],
360-                        sync_type="INVENTARIOS",
361-                        sync_start=sync_start,
362-                        sync_end=sync_end,
363-                        records_synced=inv_result.get("records_synced", 0),
364-                        status=inv_result.get("status", "ERROR"),
365-                        error_message=inv_result.get("error")
366-                    )
367-                    
368-            except Exception as e:
369-                logger.error(f"[SYNC-COMPRAS] Error sincronizando inventarios {server_name}: {e}")
370-                total_errors += 1
371-                error_messages.append(f"{server_name} INV: {str(e)[:100]}")
372-            
373-            # Sincronizar Requisiciones
374-            try:
375-                sync_start = datetime.now(ZoneInfo("America/Mexico_City"))
376-                
377-                if not dry_run:
378-                    req_result = sync_requisiciones_from_server(
379-                        server_info, unidad_info, _execute_sql_with_timeout
380-                    )
381-                else:
382-                    req_result = {"status": "DRY_RUN", "records_synced": 0, "error": None}
383-                
384-                sync_end = datetime.now(ZoneInfo("America/Mexico_City"))
385-                
386-                results["requisiciones"].append({
387-                    "server": server_name,
388-                    "unidad": unidad_codigo,
389-                    "status": req_result.get("status"),
390-                    "records": req_result.get("records_synced", 0),
391-                    "error": req_result.get("error")
392-                })
393-                
394-                if req_result.get("status") == "OK" or req_result.get("status") == "DRY_RUN":
395-                    total_processed += req_result.get("records_synced", 0)
396-                    logger.info(f"[SYNC-COMPRAS] ✅ Requisiciones {server_name}: {req_result.get('records_synced', 0)} registros")
397-                else:
398-                    total_errors += 1
399-                    error_messages.append(f"{server_name} REQ: {req_result.get('error', 'Error desconocido')}")
400-                    logger.warning(f"[SYNC-COMPRAS] ❌ Requisiciones {server_name}: {req_result.get('error')}")
401-                
402-                # Log en tabla de sync
403-                if not dry_run:
404-                    log_sync_operation(
405-                        unidad_negocio_id=unidad_info['id'],
406-                        server_id=server_info['id'],
407-                        sync_type="REQUISICIONES",
408-                        sync_start=sync_start,
409-                        sync_end=sync_end,
410-                        records_synced=req_result.get("records_synced", 0),
411-                        status=req_result.get("status", "ERROR"),
412-                        error_message=req_result.get("error")
413-                    )
414-                    
415-            except Exception as e:
416-                logger.error(f"[SYNC-COMPRAS] Error sincronizando requisiciones {server_name}: {e}")
417-                total_errors += 1
418-                error_messages.append(f"{server_name} REQ: {str(e)[:100]}")
419-        
420-        # Determinar status final
421-        if total_errors == 0:
422-            final_status = "SUCCESS"
423-        elif total_processed > 0:
424-            final_status = "PARTIAL"
425-        else:
426-            final_status = "FAILED"
427-        
428-        end_time = datetime.now(ZoneInfo("America/Mexico_City"))
429-        duration = int((end_time - start_time).total_seconds())
430-        
431-        logger.info("[SYNC-COMPRAS] ========== FIN SINCRONIZACIÓN ==========")
432-        logger.info(f"[SYNC-COMPRAS] Status: {final_status}, Procesados: {total_processed}, Errores: {total_errors}, Duración: {duration}s")
433-        
434-        # Liberar lock
435-        error_summary = "; ".join(error_messages[:5]) if error_messages else None
436-        _release_sync_lock(run_id, final_status, total_processed, total_errors, error_summary)
437-        
438-        return {
439-            "status": final_status,
440-            "run_id": run_id,
441-            "duration_seconds": duration,
442-            "total_processed": total_processed,
443-            "total_errors": total_errors,
444-            "servers_processed": len(servers),
445-            "results": results,
446-            "errors": error_messages[:10]
447-        }
448-        
449-    except Exception as e:
450-        logger.error(f"[SYNC-COMPRAS] Error crítico: {e}")
451-        _release_sync_lock(run_id, "FAILED", total_processed, total_errors + 1, str(e)[:500])
452-        return {
453-            "status": "FAILED",
454-            "run_id": run_id,
455-            "error": str(e),
456-            "total_processed": total_processed,
457-            "total_errors": total_errors + 1
458-        }
459-
460-
461-# =============================================================================
462-# FUNCIONES PARA SCHEDULER
463-# =============================================================================
464-
465-async def run_sync_compras_job():
466-    """Función async para el scheduler APScheduler."""
467-    import asyncio
468-    
469-    logger.info("[SYNC-COMPRAS-JOB] Iniciando job programado")
470-    
471-    # Ejecutar en thread separado para no bloquear el event loop
472-    loop = asyncio.get_event_loop()
473-    result = await loop.run_in_executor(None, execute_sync_compras, False)
474-    
475-    logger.info(f"[SYNC-COMPRAS-JOB] Completado: {result.get('status')}")
```
