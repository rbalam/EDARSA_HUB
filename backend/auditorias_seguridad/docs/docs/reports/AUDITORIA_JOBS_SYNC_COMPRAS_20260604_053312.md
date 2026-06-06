# AUDITORÍA JOBS SYNC COMPRAS / INVENTARIOS
Fecha: Thu Jun  4 05:33:12 UTC 2026

## 1. Ubicación de archivos sync
```text
/app/backend/core/scheduler/jobs/inventarios_detector_job.py
/app/backend/core/scheduler/jobs/pedidos_detector_job.py
/app/backend/core/scheduler/jobs/sync_compras_job.py
/app/backend/modules/compras/sync_service.py
/app/backend/modules/tablajeria/sync_service.py
```

## 2. Contenido relevante sync_compras_job.py
```python
# FILE: /app/backend/core/scheduler/jobs/sync_compras_job.py
2:EDARSA HUB - Job de Sincronización de Compras (Inventarios y Requisiciones)
6:Sincroniza datos de inventarios físicos y requisiciones desde los servidores
15:- Compras_Inventarios_Fisicos_Sync
16:- Compras_Requisiciones_Sync
17:- Compras_Sync_Log
35:from core.db import execute_sql_query as _base_execute_sql_query
43:logger = logging.getLogger(__name__)
64:def _acquire_sync_lock(run_id: str) -> bool:
88:            FROM Sync_Control_Ejecuciones
99:                logger.warning(f"[SYNC-COMPRAS-LOCK] Timeout detectado: {active['SyncRunID']}")
101:                    UPDATE Sync_Control_Ejecuciones SET Status='TIMEOUT', FinishedAtMexico=%s
107:                logger.info(f"[SYNC-COMPRAS-LOCK] Lock activo: {active['SyncRunID']} - Abortando")
109:                return False
114:            INSERT INTO Sync_Control_Ejecuciones (
122:        logger.info(f"[SYNC-COMPRAS-LOCK] 🔒 Lock adquirido: {run_id}")
123:        return True
124:    except Exception as e:
125:        logger.error(f"[SYNC-COMPRAS-LOCK] Error adquiriendo lock: {e}")
126:        return True  # Permitir ejecución si falla el lock (fail-open)
129:def _release_sync_lock(run_id: str, status: str, processed: int, errors: int, error_msg: str = None):
130:    """Libera el lock de sincronización."""
144:        cursor.execute("SELECT StartedAtMexico FROM Sync_Control_Ejecuciones WHERE SyncRunID=%s", (run_id,))
154:            UPDATE Sync_Control_Ejecuciones
160:        logger.info(f"[SYNC-COMPRAS-LOCK] 🔓 Lock liberado: {run_id} (status={status}, duration={duration}s)")
161:    except Exception as e:
162:        logger.error(f"[SYNC-COMPRAS-LOCK] Error liberando lock: {e}")
169:def _execute_sql_with_timeout(host, port, database, username, password, query, timeout_seconds=30):
173:    def timeout_handler(signum, frame):
184:        result = _base_execute_sql_query(host, port, database, username, password, query, timeout_seconds=timeout_seconds, context="jobs")
185:        return result
186:    except TimeoutError as e:
187:        logger.warning(f"[SYNC-COMPRAS] Timeout conectando a {host}: {e}")
188:        return None
189:    except Exception as e:
191:            logger.warning(f"[SYNC-COMPRAS] Error de conexión a {host}: {str(e)[:100]}")
192:            return None
200:def _get_servers_to_sync() -> List[Dict]:
202:    Obtiene la lista de servidores activos configurados para sincronización.
234:                except Exception as e:
235:                    logger.warning(f"[SYNC-COMPRAS] No se pudo desencriptar password de {row['server_name']}: {e}")
252:        logger.info(f"[SYNC-COMPRAS] Servidores encontrados: {len(servers)}")
253:        return servers
255:    except Exception as e:
256:        logger.error(f"[SYNC-COMPRAS] Error obteniendo servidores: {e}")
257:        return []
264:def execute_sync_compras(dry_run: bool = False) -> Dict[str, Any]:
266:    Ejecuta la sincronización completa de Compras.
272:        Dict con resultados de la sincronización
275:    logger.info(f"[SYNC-COMPRAS] ========== INICIO SINCRONIZACIÓN {run_id} ==========")
279:        return {
281:            "reason": "Lock activo - otra sincronización en curso",
299:            logger.warning("[SYNC-COMPRAS] No hay servidores configurados para sincronizar")
301:            return {
307:        # Sincronizar cada servidor
312:            logger.info(f"[SYNC-COMPRAS] Procesando: {server_name} ({unidad_codigo})")
315:                logger.warning(f"[SYNC-COMPRAS] Servidor {server_name} sin host/password - Saltando")
322:                'host': server['host'],
335:            # Sincronizar Inventarios Físicos
358:                    logger.info(f"[SYNC-COMPRAS] ✅ Inventarios {server_name}: {inv_result.get('records_synced', 0)} registros")
362:                    logger.warning(f"[SYNC-COMPRAS] ❌ Inventarios {server_name}: {inv_result.get('error')}")
377:            except Exception as e:
378:                logger.error(f"[SYNC-COMPRAS] Error sincronizando inventarios {server_name}: {e}")
382:            # Sincronizar Requisiciones
405:                    logger.info(f"[SYNC-COMPRAS] ✅ Requisiciones {server_name}: {req_result.get('records_synced', 0)} registros")
409:                    logger.warning(f"[SYNC-COMPRAS] ❌ Requisiciones {server_name}: {req_result.get('error')}")
424:            except Exception as e:
425:                logger.error(f"[SYNC-COMPRAS] Error sincronizando requisiciones {server_name}: {e}")
440:        logger.info("[SYNC-COMPRAS] ========== FIN SINCRONIZACIÓN ==========")
441:        logger.info(f"[SYNC-COMPRAS] Status: {final_status}, Procesados: {total_processed}, Errores: {total_errors}, Duración: {duration}s")
447:        return {
458:    except Exception as e:
459:        logger.error(f"[SYNC-COMPRAS] Error crítico: {e}")
461:        return {
474:async def run_sync_compras_job():
475:    """Función async para el scheduler APScheduler."""
478:    logger.info("[SYNC-COMPRAS-JOB] Iniciando job programado")
484:    logger.info(f"[SYNC-COMPRAS-JOB] Completado: {result.get('status')}")
485:    return result
488:def get_job_config() -> Dict:
489:    """Retorna la configuración del job para el scheduler."""
490:    return {
492:        "job_name": "Sincronización Compras (Inventarios/Requisiciones)",
496:        "description": "Sincroniza inventarios físicos y requisiciones desde servidores origen hacia EDARSAHUB SQL",
```

## 3. Contenido relevante compras/sync_service.py
```python
# FILE: /app/backend/modules/compras/sync_service.py
8:- Compras_Inventarios_Fisicos_Sync: Inventarios físicos sincronizados
9:- Compras_Requisiciones_Sync: Requisiciones/pedidos sincronizados
10:- Compras_Sync_Log: Log de sincronizaciones
18:logger = logging.getLogger(__name__)
30:def get_edarsahub_connection():
32:    return pymssql.connect(
46:def obtener_inventarios_fisicos_sync(
67:            FROM Compras_Inventarios_Fisicos_Sync
101:        logger.info(f"[SYNC-READ] Inventarios físicos: {len(rows)} registros desde EDARSAHUB")
102:        return rows
104:    except Exception as e:
105:        logger.error(f"[SYNC-READ] Error obteniendo inventarios: {e}")
106:        return []
109:def obtener_requisiciones_sync(
129:            FROM Compras_Requisiciones_Sync
158:        logger.info(f"[SYNC-READ] Requisiciones: {len(rows)} registros desde EDARSAHUB")
159:        return rows
161:    except Exception as e:
162:        logger.error(f"[SYNC-READ] Error obteniendo requisiciones: {e}")
163:        return []
170:def sync_inventarios_fisicos_from_server(
173:    execute_sql_query_func
182:        execute_sql_query_func: Función para ejecutar queries en el servidor origen
194:    logger.info(f"[SYNC] Iniciando sync inventarios: {unidad_codigo} ({system_type})")
237:            return {"status": "ERROR", "records_synced": 0, "error": f"Sistema no soportado: {system_type}"}
240:        rows = execute_sql_query_func(
250:            return {"status": "OK", "records_synced": 0, "error": None}
258:            UPDATE Compras_Inventarios_Fisicos_Sync 
268:                    INSERT INTO Compras_Inventarios_Fisicos_Sync
286:            except Exception as e:
287:                logger.warning(f"[SYNC] Error insertando inventario {row.get('folio')}: {e}")
292:        logger.info(f"[SYNC] Inventarios sincronizados: {records_synced} de {len(rows)}")
293:        return {"status": "OK", "records_synced": records_synced, "error": None}
295:    except Exception as e:
296:        logger.error(f"[SYNC] Error sync inventarios {unidad_codigo}: {e}")
297:        return {"status": "ERROR", "records_synced": 0, "error": str(e)}
300:def sync_requisiciones_from_server(
303:    execute_sql_query_func
315:    logger.info(f"[SYNC] Iniciando sync requisiciones: {unidad_codigo} ({system_type})")
370:            return {"status": "ERROR", "records_synced": 0, "error": f"Sistema no soportado: {system_type}"}
373:        rows = execute_sql_query_func(
383:            return {"status": "OK", "records_synced": 0, "error": None}
391:            UPDATE Compras_Requisiciones_Sync 
401:                    INSERT INTO Compras_Requisiciones_Sync
422:            except Exception as e:
423:                logger.warning(f"[SYNC] Error insertando requisición {row.get('folio')}: {e}")
428:        logger.info(f"[SYNC] Requisiciones sincronizadas: {records_synced} de {len(rows)}")
429:        return {"status": "OK", "records_synced": records_synced, "error": None}
431:    except Exception as e:
432:        logger.error(f"[SYNC] Error sync requisiciones {unidad_codigo}: {e}")
433:        return {"status": "ERROR", "records_synced": 0, "error": str(e)}
436:def log_sync_operation(
451:            INSERT INTO Compras_Sync_Log
461:    except Exception as e:
462:        logger.error(f"[SYNC-LOG] Error registrando log: {e}")
465:def get_last_sync_info(server_id: str, sync_type: str) -> Optional[Dict]:
471:            SELECT TOP 1 * FROM Compras_Sync_Log
477:        return row
478:    except Exception as e:
479:        logger.error(f"[SYNC-LOG] Error obteniendo último sync: {e}")
480:        return None
```

## 4. Contenido relevante detectores
```python
# FILE: /app/backend/core/scheduler/jobs/inventarios_detector_job.py
37:- try/except con rollback e invalidación de conexión
50:from ..job_logger import get_job_logger
53:    get_server_by_id,
62:logger = logging.getLogger(__name__)
101:def _es_error_estructura_sql(error_msg: str) -> bool:
108:    return any(indicador in error_lower for indicador in ERRORES_ESTRUCTURA_SQL)
111:def _validar_tabla_existe(servidor: Dict, tabla: str) -> bool:
124:    from core.db import execute_sql_query
132:        result = execute_sql_query(
142:        logger.debug(f"[INVENTARIOS_DETECTOR] Tabla '{tabla}' en {servidor['name']}: {'EXISTE' if existe else 'NO EXISTE'}")
143:        return existe
145:    except Exception as e:
146:        logger.warning(f"[INVENTARIOS_DETECTOR] Error verificando tabla '{tabla}' en {servidor['name']}: {e}")
147:        return False
150:def _invalidar_conexion_si_error_estructura(servidor: Dict, error: Exception) -> None:
165:            logger.warning(f"[INVENTARIOS_DETECTOR] Pool [jobs] invalidado para {servidor['name']} por error de estructura SQL")
166:        except Exception as cleanup_error:
167:            logger.error(f"[INVENTARIOS_DETECTOR] Error invalidando pool [jobs]: {cleanup_error}")
175:class ClaveIdempotencia:
183:    def to_dict(self) -> Dict:
184:        return asdict(self)
186:    def to_query(self) -> Dict:
188:        return {
197:@dataclass  
198:class InventarioDetectado:
213:class InventariosDetectorJob:
222:    def __init__(self, db, config: Optional[dict] = None):
227:            logger.info("[INVENTARIOS_DETECTOR] Usando StubDatabase")
231:        self.job_logger = get_job_logger(db)
251:    def _is_stub_db(self) -> bool:
254:            return True
255:        return hasattr(self.db, '_collections') and self.db.__class__.__name__ == 'StubDatabase'
257:    async def run(self, manual: bool = False, server_id_filter: str = None):
272:        logger.info(f"[INVENTARIOS_DETECTOR] Iniciando ejecución SQL Server - {started_at.isoformat()}")
283:        log_entry = await self.job_logger.start_execution(
297:            logger.info(f"[INVENTARIOS_DETECTOR] Servidores a escanear: {len(servidores)}")
302:            except Exception as e:
303:                logger.warning(f"[INVENTARIOS_DETECTOR] Error procesando reintentos: {e}")
309:                except Exception as e:
310:                    logger.error(f"[INVENTARIOS_DETECTOR] Error en servidor {servidor.get('name')}: {e}")
325:            await self.job_logger.finish_execution(
336:            logger.info(f"[INVENTARIOS_DETECTOR] Finalizado ({final_status}) - {self._generar_resumen()}")
338:            return {
343:        except Exception as e:
344:            logger.error(f"[INVENTARIOS_DETECTOR] ERROR CRÍTICO: {e}")
346:            logger.error(traceback.format_exc())
348:            await self.job_logger.finish_execution(
357:            return {
363:    async def _ensure_index(self):
368:    async def _obtener_servidores(self, server_id_filter: str = None) -> List[Dict]:
370:        logger.info("[INVENTARIOS_DETECTOR] _obtener_servidores: Usando SQL Server")
373:        logger.info(f"[INVENTARIOS_DETECTOR] Obtenidos {len(servidores)} servidores de SQL")
382:        return compatible
384:    async def _procesar_reintentos(self):
399:                logger.info("[INVENTARIOS_DETECTOR] Límite alcanzado, saltando reintentos")
403:            logger.info(f"[INVENTARIOS_DETECTOR] Reintentando folio={registro.get('FolioInventario')}")
419:    async def _escanear_servidor(self, servidor: Dict):
425:        logger.info(f"[INVENTARIOS_DETECTOR] Escaneando {server_name} ({system_type})")
434:                logger.warning(f"[INVENTARIOS_DETECTOR] Tipo de sistema desconocido: {system_type}")
435:                return
438:            logger.info(f"[INVENTARIOS_DETECTOR] {server_name}: {len(inventarios)} inventarios detectados")
444:        except Exception as e:
445:            logger.warning(f"[INVENTARIOS_DETECTOR] {server_name}: Conexión fallida - {e}")
447:    async def _detectar_soft(self, servidor: Dict) -> List[InventarioDetectado]:
454:        - try/except con invalidación de conexión si error de estructura
457:        from core.db import execute_sql_query
465:            logger.warning(f"[INVENTARIOS_DETECTOR] {server_name}: _detectar_soft llamado con system_type={system_type} (esperado: SoftRestaurant)")
466:            return inventarios
470:            logger.info(f"[INVENTARIOS_DETECTOR] {server_name}: Tabla 'invfisico' no existe - saltando detección")
471:            return inventarios
497:            result = execute_sql_query(
508:                logger.debug(f"[INVENTARIOS_DETECTOR] {server_name}: Sin inventarios recientes")
509:                return inventarios
552:        except Exception as e:
555:            logger.error(f"[INVENTARIOS_DETECTOR] Error detectando SOFT en {server_name}: {e}")
557:        return inventarios
559:    async def _detectar_mpro(self, servidor: Dict) -> List[InventarioDetectado]:
567:        logger.info(f"[INVENTARIOS_DETECTOR] MPRO {servidor.get('name')}: Saltando detección (tabla invfisico no existe en MPRO)")
568:        return []
570:    async def _calcular_folio_inicial_soft(
582:        from core.db import execute_sql_query
599:            result = execute_sql_query(
616:                return folio, fecha_str
618:        except Exception as e:
621:            logger.warning(f"[INVENTARIOS_DETECTOR] Error calculando folio inicial en {server_name}: {e}")
623:        return None, None
625:    async def _calcular_folio_inicial_mpro(
640:        logger.debug("[INVENTARIOS_DETECTOR] _calcular_folio_inicial_mpro no implementado para MPRO (tabla invfisico no existe)")
641:        return None, None
643:    async def _procesar_inventario(self, inv: InventarioDetectado, servidor: Dict):
650:            logger.info(f"[INVENTARIOS_DETECTOR] Límite de {self.max_inventarios_por_ejecucion} alcanzado, saltando folio={clave.folio_inventario}")
651:            return
664:            logger.debug(f"[INVENTARIOS_DETECTOR] Duplicado: folio={clave.folio_inventario}")
665:            return
668:        logger.info(f"[INVENTARIOS_DETECTOR] Nuevo inventario: folio={clave.folio_inventario}, almacen={inv.almacen_nombre}")
711:                logger.info(f"[INVENTARIOS_DETECTOR] Ya en proceso: folio={clave.folio_inventario}")
712:                return
713:        except Exception as e:
717:                logger.info(f"[INVENTARIOS_DETECTOR] Ya en proceso: folio={clave.folio_inventario}")
718:                return
724:    async def _procesar_inventario_desde_registro(self, registro: Dict):
727:        servidor = await get_server_by_id(registro["clave"]["server_id"])
731:            return
747:    async def _ejecutar_analisis(self, registro: Dict, servidor: Dict, inv: InventarioDetectado):
752:            logger.info(f"[INVENTARIOS_DETECTOR] Ejecutando análisis folio={clave.folio_inventario}")
786:            logger.info(f"[INVENTARIOS_DETECTOR] Análisis completado: {len(productos_con_diferencia)} diferencias")
812:            logger.info(f"[INVENTARIOS_DETECTOR] Procesado exitosamente: folio={clave.folio_inventario}, workflow={workflow_id}")
814:        except Exception as e:
815:            logger.error(f"[INVENTARIOS_DETECTOR] ERROR en análisis folio={clave.folio_inventario}: {e}")
818:    async def _ejecutar_orquestacion(
851:                logger.info(f"[INVENTARIOS_DETECTOR] Workflow creado: {resumen.get('workflow_id')}")
852:                return resumen.get("workflow_id")
854:                logger.info(f"[INVENTARIOS_DETECTOR] Workflow no creado: {resumen.get('mensaje', 'Sin detalles')}")
855:                return None
857:        except Exception as e:
858:            logger.error(f"[INVENTARIOS_DETECTOR] Error en orquestación: {e}")
861:    async def _marcar_error(self, registro: Dict, error_msg: str):
878:            logger.error(f"[INVENTARIOS_DETECTOR] ERROR CRÍTICO: Máximo de intentos alcanzado - {error_msg}")
880:            logger.warning(f"[INVENTARIOS_DETECTOR] Error (intento {intentos}/{MAX_INTENTOS}): {error_msg}")
882:    def _generar_resumen(self) -> str:
884:        return (
897:def create_inventarios_detector_job(db, config: Optional[dict] = None) -> InventariosDetectorJob:
899:    return InventariosDetectorJob(db, config)

# FILE: /app/backend/core/scheduler/jobs/pedidos_detector_job.py
38:from ..job_logger import get_job_logger
47:logger = logging.getLogger(__name__)
50:class PedidosDetectorJob:
73:    # COLLECTION_TAREAS = "tareas_operativas_compras"              # -> Compras_Eventos_Pendientes  
76:    def __init__(self, db, config: Optional[dict] = None):
77:        # db se mantiene para compatibilidad con job_logger (migrar después)
82:            logger.info("[PEDIDOS_DETECTOR] Usando StubDatabase para job_logger (tracking en SQL)")
86:        self.job_logger = get_job_logger(db)
89:    def _is_stub_db(self) -> bool:
92:            return True
93:        return hasattr(self.db, '_collections') and self.db.__class__.__name__ == 'StubDatabase'
95:    async def run(self, manual: bool = False, empresa_id_filter: str = None):
115:        logger.info(f"[PEDIDOS_DETECTOR] Iniciando ejecución SQL Server - {started_at.isoformat()}")
126:        log_entry = await self.job_logger.start_execution(
165:            logger.info(f"[PEDIDOS_DETECTOR] Empresas activas: {len(empresas)}")
173:                await self.job_logger.finish_execution(
178:                return stats
190:                        logger.debug(f"[PEDIDOS_DETECTOR] {empresa_nombre}: Sin servidores asociados")
193:                    logger.info(f"[PEDIDOS_DETECTOR] {empresa_nombre}: {len(servidores)} servidores")
227:                                logger.warning(
233:                                logger.warning(
239:                                logger.error(
265:                            logger.info(
272:                        logger.info(
305:                                        logger.info(
311:                                        logger.info(
318:                            except Exception as e:
320:                                logger.error(
329:                except Exception as e:
330:                    logger.error(
367:            await self.job_logger.finish_execution(
384:            logger.info(f"[PEDIDOS_DETECTOR] {message}")
386:            return stats
388:        except Exception as e:
391:            await self.job_logger.finish_execution(
406:            logger.error(f"[PEDIDOS_DETECTOR] Error general: {e}")
409:    def _format_stats_message(self, stats: Dict) -> str:
411:        return self._format_stats_message_with_state(stats)
413:    def _format_stats_message_with_state(self, stats: Dict) -> str:
438:        return base_msg
444:    async def _obtener_empresas_activas(self, empresa_id_filter: str = None) -> List[Dict]:
451:        return await get_empresas_activas(empresa_id_filter)
453:    async def _obtener_servidores_empresa(self, empresa_id: str) -> List[Dict]:
471:        return compatible
477:    async def _consultar_pedidos_con_estado(self, server: Dict) -> SourceQueryResult:
499:                return SourceQueryResult.success_with_data(
508:                return SourceQueryResult.success_empty(
515:        except Exception as e:
526:                return SourceQueryResult.connection_cooldown(
535:                return SourceQueryResult.source_unreachable(
542:                return SourceQueryResult.auth_error(
549:                return SourceQueryResult.query_timeout(
556:                return SourceQueryResult.unknown_error(
563:    async def _consultar_pedidos_vigentes(self, server: Dict) -> List[Dict]:
571:            return result.data
572:        return []
578:    async def _ya_procesado(self, empresa_id: str, folio: str, origen: str) -> bool:
586:        return await pedido_ya_procesado_sql(empresa_id, folio, origen)
588:    async def _marcar_procesado(
620:    async def _procesar_pedido_nuevo(
664:            return {"estado": "SIN_PRODUCTOS", "automatizacion_id": automatizacion_id}
706:            return {
739:        return {
750:    async def _obtener_detalle_pedido(self, server: Dict, folio: str) -> List[Dict]:
756:                return [
766:            return []
767:        except Exception as e:
768:            logger.warning(f"[PEDIDOS_DETECTOR] Error detalle pedido {folio}: {e}")
769:            return []
775:    async def _validar_inventario_disponible(
795:        logger.debug("[PEDIDOS_DETECTOR] _inventario_valido: Retornando True (MongoDB eliminado)")
796:        return True
802:    async def _crear_tarea_operativa(
846:        return tarea_id
848:    async def _notificar_tarea_creada(self, tarea: Dict):
852:            logger.info(
856:        except Exception as e:
857:            logger.warning(f"Error notificando tarea: {e}")
863:    async def _iniciar_auditoria(
908:        return resultado
914:    async def _registrar_bitacora_job(self, evento: str, datos: Dict):
925:def create_pedidos_detector_job(db, config: Optional[dict] = None) -> PedidosDetectorJob:
927:    return PedidosDetectorJob(db, config)
934:async def ejecutar_detector_manual(
951:    return await job.run(manual=True, empresa_id_filter=empresa_id)

```

## 5. Configuración scheduler/supervisor relacionada
```text
/app/scripts/run_sync_sales_dry_run_backfill_7_dias.sh:40:echo "- No debe activar scheduler automático." >> "$REPORT"
/app/scripts/run_sync_sales_dry_run_backfill_7_dias.sh:96:    MAX(fecha_sincronizacion) AS ultima_sincronizacion
/app/scripts/run_sync_sales_dry_run_backfill_7_dias.sh:193:    MAX(fecha_sincronizacion) AS ultima_sincronizacion
/app/scripts/audit_live_connections.sh:29:  echo "- Si aparece dentro de scheduler/jobs/sync: permitido con control."
/app/scripts/classify_no_live_violations.sh:30:  echo "| P1 | Repositorios/servicios de modulos con live fuera de scheduler | Migrar a SQL sincronizado |"
/app/scripts/classify_no_live_violations.sh:32:  echo "| PERMITIDO | scheduler/jobs/sync/scripts/tests/tools/adapters controlados | Mantener con logs |"
/app/scripts/classify_no_live_violations.sh:56:    elif [[ "$lower" == *"/scheduler/"* || "$lower" == *"/jobs/"* || "$lower" == *"/sync"* || "$lower" == *"/adapters.py"* ]]; then
/app/scripts/classify_no_live_violations.sh:58:      action="Permitido solo como sincronizacion/control; validar logs y no uso directo en dashboard"
/app/scripts/classify_no_live_violations.sh:64:      action="Remediar si alimenta dashboard/reporte; mover a SQL sincronizado"
/app/scripts/classify_no_live_violations.sh:67:      action="Revisar dependencia; migrar a SQL sincronizado si no es job"
/app/scripts/auditorias/01_auditar_conexiones_live_edarsahub.sh:36:  | grep -v "sync_\|Sync_\|scheduler\|job" \
/app/scripts/auditorias/01_auditar_conexiones_live_edarsahub.sh:46:  | grep -v "__pycache__\|\.pyc\|sync_\|Sync_\|scheduler\|job\|registry\|migration" \
/app/scripts/auditorias/01_auditar_conexiones_live_edarsahub.sh:75:  | grep -v "__pycache__\|sync_\|Sync_\|scheduler\|job" \
/app/scripts/auditorias/01_auditar_conexiones_live_edarsahub.sh:94:VIOLACIONES_BACKEND=$(grep -Rn "execute_sql_query" /app/backend --include="*.py" | grep -v "EDARSAHUB\|edarsahub\|__pycache__\|sync_\|Sync_\|scheduler\|job" | wc -l)
/app/scripts/auditorias/01_auditar_conexiones_live_edarsahub.sh:96:VIOLACIONES_CONEXION=$(grep -Rn "get_server_connection_info" /app/backend --include="*.py" | grep -v "__pycache__\|sync_\|Sync_\|scheduler\|job" | wc -l)
/app/scripts/run_sync_sales_dry_run_todas_unidades.sh:136:    MAX(fecha_sincronizacion) AS ultima_sincronizacion
/app/scripts/02_validate_workspace.sh:16:echo "=== Scheduler jobs ==="
/app/scripts/02_validate_workspace.sh:17:ls -la ./backend/core/scheduler/jobs || true
/app/scripts/02_validate_workspace.sh:19:echo "=== Scheduler config ==="
/app/scripts/02_validate_workspace.sh:20:grep -Rni "sla_processor\|notifications_dispatcher\|auditorias_scheduler\|pedidos_detector\|inteligencia" ./backend/core/scheduler 2>/dev/null || true
/app/scripts/validar_server_secret_key_edarsahub.sh:16:  echo "SERVER_SECRET_KEY debe estar configurada en todo entorno que ejecute jobs, scheduler, sincronizaciones, dry-runs o conexiones a Servidores_Conexiones."
/app/scripts/06_apply_inteligencia_fase1_patch.py:53:config = ROOT / "backend" / "core" / "scheduler" / "config.py"
/app/scripts/06_apply_inteligencia_fase1_patch.py:55:new_jobs = '''            "pedidos_detector": JobConfig(\n                job_id="pedidos_detector",\n                job_name="Pedidos Detector",\n                description="Detecta pedidos nuevos en MPro/Soft y dispara automatización operativa de compras",\n                enabled=pedidos_enabled,\n                interval_seconds=pedidos_interval,\n                batch_size=50,\n                timeout_seconds=300\n            ),\n            "inteligencia_comercial_sync": JobConfig(\n                job_id="inteligencia_comercial_sync",\n                job_name="Inteligencia Comercial Sync Status",\n                description="Valida frescura de fuentes SQL para Portal de Inteligencia Comercial",\n                enabled=os.environ.get("SCHEDULER_INTELIGENCIA_COMERCIAL_ENABLED", "true").lower() == "true",\n                interval_seconds=int(os.environ.get("SCHEDULER_INTELIGENCIA_COMERCIAL_INTERVAL_SECONDS", "3600")),\n                batch_size=10,\n                timeout_seconds=180\n            )\n        }'''
/app/scripts/06_apply_inteligencia_fase1_patch.py:58:# 3) scheduler_manager.py: imports, wrapper, registro y run now
/app/scripts/06_apply_inteligencia_fase1_patch.py:59:manager = ROOT / "backend" / "core" / "scheduler" / "scheduler_manager.py"
/app/scripts/06_apply_inteligencia_fase1_patch.py:62:    "from .jobs.pedidos_detector_job import create_pedidos_detector_job\n",
/app/scripts/06_apply_inteligencia_fase1_patch.py:68:    '''    async def _run_pedidos_detector_job(self):\n        """Wrapper async para ejecutar job de detección de pedidos."""\n        job_config = self.config.jobs.get("pedidos_detector")\n        if not job_config or not job_config.enabled:\n            return\n        \n        job = create_pedidos_detector_job(self.db, job_config)\n        await job.run()\n''',
/app/scripts/06_apply_inteligencia_fase1_patch.py:75:    '''\n        # Job Inteligencia Comercial Sync Status\n        inteligencia_config = self.config.jobs.get("inteligencia_comercial_sync")\n        if inteligencia_config and inteligencia_config.enabled:\n            if inteligencia_config.cron_expression:\n                trigger = CronTrigger.from_crontab(inteligencia_config.cron_expression)\n            else:\n                trigger = IntervalTrigger(seconds=inteligencia_config.interval_seconds)\n\n            self._scheduler.add_job(\n                self._run_inteligencia_comercial_sync_job,\n                trigger=trigger,\n                id="inteligencia_comercial_sync",\n                name="Inteligencia Comercial Sync Status",\n                replace_existing=True,\n                max_instances=1,\n                coalesce=True\n            )\n            self._jobs["inteligencia_comercial_sync"] = inteligencia_config\n            logger.info(f"Job Inteligencia Comercial registrado: intervalo={inteligencia_config.interval_seconds}s")\n'''
/app/scripts/06_apply_inteligencia_fase1_patch.py:80:    '''        elif job_id == "pedidos_detector":\n            await self._run_pedidos_detector_job()\n            return {"status": "executed", "job_id": job_id}\n        else:\n            return {"status": "error", "message": f"Job desconocido: {job_id}"}\n''',
/app/scripts/06_apply_inteligencia_fase1_patch.py:81:    '''        elif job_id == "pedidos_detector":\n            await self._run_pedidos_detector_job()\n            return {"status": "executed", "job_id": job_id}\n        elif job_id == "inteligencia_comercial_sync":\n            await self._run_inteligencia_comercial_sync_job()\n            return {"status": "executed", "job_id": job_id}\n        else:\n            return {"status": "error", "message": f"Job desconocido: {job_id}"}\n'''
/app/scripts/06_apply_inteligencia_fase1_patch.py:86:print("- backend/core/scheduler/jobs/inteligencia_comercial_status_job.py")
/app/scripts/run_ic_next_steps.sh:34:echo "- Este script bash no sincroniza ventas."
/app/backend/modules/comercial/service.py:1684:    - Las APIs locales SOLO pueden ser consultadas por jobs de sincronización
/app/backend/modules/comercial/service.py:1796:                    "source_status": "NO_SYNC_DATA",  # Estado claro: sin sincronización
/app/backend/modules/comercial/service.py:1797:                    "message": "Sin datos sincronizados para esta fecha operativa",
/app/backend/modules/comercial/service.py:2648:                fecha_sincronizacion,
/app/backend/modules/comercial/service.py:2668:        fecha_snapshot = row['fecha_sincronizacion'] or row['fecha_operacion']
/app/backend/modules/comercial/cache_service.py:234:    - last_successful_sync: Timestamp de última sincronización exitosa
/app/backend/modules/comercial/queries/__init__.py:30:- Schedulers SYNC-S/SYNC-N (kpis_repository.py)
/app/backend/modules/comercial/queries/mpro.py:40:- SYNC-S scheduler
/app/backend/modules/comercial/queries/mpro.py:147:    - SYNC-S scheduler
/app/backend/modules/comercial/queries/softrestaurant.py:36:- SYNC-S scheduler
/app/backend/modules/comercial/queries/softrestaurant.py:123:    - SYNC-S scheduler (migración Fase 2)
/app/backend/modules/comercial/crm_router.py:262:    Clona la cabecera y el detalle de líneas de forma local y síncrona en SQL Server.
/app/backend/modules/comercial/crm_router.py:371:    """Fase 10: Actualiza el estado de un entregable (Aprobación/Rechazo) con auditoría síncrona."""
/app/backend/modules/comercial/crm_router.py:411:    # 2. Tasa de Conversión de Leads (Nativos/Sincronizados)
/app/backend/modules/comercial/crm_router.py:600:    Consulta de forma local las transacciones pendientes de transmitir por el Scheduler.
/app/backend/modules/comercial/inteligencia_comercial_routes.py:198:        MAX(fecha_sincronizacion) AS ultima_sincronizacion
/app/backend/modules/comercial/inteligencia_comercial_routes.py:250:        MAX(fecha_sincronizacion) AS ultima_sincronizacion
/app/backend/modules/comercial/inteligencia_comercial_routes.py:269:    Fuente: dbo.Sync_PAX_Detalle (tabla sincronizada)
/app/backend/modules/comercial/inteligencia_comercial_routes.py:332:    Estado de sincronización de fuentes de datos.
/app/backend/modules/comercial/inteligencia_comercial_routes.py:410:        MAX(fecha_sincronizacion) AS ultima_sincronizacion
/app/backend/modules/comercial/inteligencia_repository.py:78:                MAX(fecha_sincronizacion) AS ultima_sincronizacion
/app/backend/modules/comercial/inteligencia_repository.py:120:                MAX(fecha_sincronizacion) AS ultima_sincronizacion
/app/backend/modules/comercial/rentabilidad.py:35:        # Consultar el costo unitario consolidado en el historial de inventarios físicos síncronos
/app/backend/modules/comercial/historical_kpis_repository.py:85:    """Versión síncrona para obtener credenciales."""
/app/backend/modules/comercial/kpis_repository.py:172:    updated_by: str = "scheduler",
/app/backend/modules/comercial/kpis_repository.py:284:        if updated_by not in ["scheduler_sync_n", "reconciliacion", "admin_manual"]:
/app/backend/modules/comercial/kpis_repository.py:471:    Usado por schedulers de sincronización.
/app/backend/modules/comercial/kpis_repository.py:507:    updated_by: str = "scheduler_sync_n"
/app/backend/modules/comercial/services/impuestos_service.py:8:2. Tasa específica por producto sincronizada desde origen
/app/backend/modules/comercial/services/impuestos_service.py:94:    2. Tasa específica por producto sincronizada desde origen
/app/backend/modules/comercial/services/impuestos_service.py:245:            mensaje="Tasa desde sincronización origen (sin mapeo canónico)"
/app/backend/modules/comercial/services/impuestos_service.py:276:        m.FechaSincronizacion,
/app/backend/modules/comercial/services/impuestos_service.py:299:            'fecha_sincronizacion': row['FechaSincronizacion'],
/app/backend/modules/comercial/services/impuestos_service.py:332:        m.FechaSincronizacion
/app/backend/modules/comercial/services/impuestos_service.py:348:            'fecha_sincronizacion': r['FechaSincronizacion']
/app/backend/modules/comercial/routes.py:986:                                    '_warning': 'Sin datos sincronizados',
/app/backend/modules/comercial/routes.py:1108:                                cache_warning = f"Último dato sincronizado hace {minutos} min"
/app/backend/modules/comercial/routes.py:1111:                                cache_warning = f"Última sincronización: hace {minutos} min (desactualizado)"
/app/backend/modules/comercial/routes.py:1114:                                cache_warning = f"Última sincronización fallida, mostrando último dato válido ({minutos} min)"
/app/backend/modules/comercial/routes.py:1302:                                cache_warning = f"Último dato sincronizado hace {minutos} min"
/app/backend/modules/comercial/routes.py:1304:                                cache_warning = f"Última sincronización: hace {minutos} min (desactualizado)"
/app/backend/modules/comercial/routes.py:2041:    # SQL-FIRST: Consultar tabla sincronizada
/app/backend/modules/comercial/routes.py:2378:    # SQL-FIRST: Consultar tabla sincronizada
/app/backend/modules/comercial/routes.py:2724:            # Obtener última sincronización
/app/backend/modules/comercial/routes.py:2741:                    "source_message": f"No hay datos de ventas por hora en EDARSAHUB para {server.get('name')} en el período {fecha_ini} a {fecha_fin}. Verifique sincronización.",
/app/backend/modules/comercial/routes.py:2764:                    stale_message = f"Datos de hace {dias_antiguedad} días. Última sincronización: {ultima_sync['SyncedAtMexico']}"
/app/backend/modules/comercial/routes.py:2897:    # SQL-FIRST: Consultar tabla sincronizada
/app/backend/modules/comercial/routes.py:4126:    # SQL-FIRST: Consultar tabla sincronizada
/app/backend/modules/comercial/routes.py:4541:                    "source_message": f"Datos históricos de EDARSAHUB. Última sincronización: {stale_snapshot['fecha_snapshot']}. Datos pueden estar desactualizados.",
/app/backend/modules/comercial/routes.py:4551:                        "mensaje": f"Datos históricos. Última sincronización: {stale_snapshot['fecha_snapshot']}"
/app/backend/modules/comercial/routes.py:4561:                "source_message": f"No hay datos consolidados para {server['name']} en el período {fecha_ini} a {fecha_fin}. Verifique que la sincronización automática esté funcionando.",
/app/backend/modules/comercial/routes.py:4571:                    "mensaje": "No hay datos consolidados en EDARSAHUB para este período. Verifique el estado de sincronización."
/app/backend/modules/comercial/routes.py:4652:                    "source_message": f"Datos históricos de EDARSAHUB. Última sincronización: {stale_snapshot_mpro['fecha_snapshot']}. Datos pueden estar desactualizados.",
/app/backend/modules/comercial/routes.py:4662:                        "mensaje": f"Datos históricos. Última sincronización: {stale_snapshot_mpro['fecha_snapshot']}"
/app/backend/modules/comercial/routes.py:4672:                "source_message": f"No hay datos consolidados para {server['name']} en el período {fecha_ini} a {fecha_fin}. Verifique que la sincronización automática esté funcionando.",
/app/backend/modules/comercial/routes.py:4682:                    "mensaje": "No hay datos consolidados en EDARSAHUB para este período. Verifique el estado de sincronización."
/app/backend/modules/fase2_operativo/sql_repository.py:53:    """Ejecuta una query SQL de forma síncrona."""
/app/backend/modules/fase2_operativo/sql_repository.py:82:    """Ejecuta una query SQL de forma asíncrona."""
/app/backend/modules/fase2_operativo/db_utils.py:10:# Conexión síncrona a MongoDB para los repositories
/app/backend/modules/fase2_operativo/db_utils.py:18:    Usa conexión síncrona para compatibilidad con los repositories.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:49:    "scheduler_job_logs": "Scheduler_BitacoraJobs",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:519:        pero internamente usa operaciones síncronas de pymssql.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:735:            "Scheduler_BitacoraJobs": "ID",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:740:    # MÉTODOS DE COMPATIBILIDAD MONGODB (Síncronos)
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:745:        Versión síncrona de get para compatibilidad con código MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:783:        Versión síncrona para compatibilidad con código MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:847:        Versión síncrona de create para compatibilidad con código MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:858:        Versión síncrona de update para compatibilidad con código MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:897:        Versión síncrona de count para compatibilidad con código MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:909:        Versión síncrona para compatibilidad con MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:935:        Versión síncrona para compatibilidad con MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:980:        Versión síncrona para compatibilidad con MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1227:        # Para compatibilidad: exponer métodos síncronos como 'collection'
/app/backend/modules/fase2_operativo/schemas/auditoria_programada_schemas.py:168:    disparado_por: str  # "SCHEDULER" | "MANUAL" | user_id
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:177:        """Ejecuta una auditoría programada (scheduler)."""
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:183:        return self._ejecutar_auditoria(auditoria, fecha_programada, "SCHEDULER")
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:252:            "created_by": auditoria.get("created_by", "SCHEDULER"),
/app/backend/modules/fase2_operativo/routes/sla_routes.py:13:- POST /actualizar-estados - SLA_VER (invocado por scheduler)
/app/backend/modules/fase2_operativo/routes/sla_routes.py:200:    por un cron externo o mecanismo equivalente.
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:7:- Ejecución automática vía job scheduler
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:106:    # Obtener db async desde el scheduler manager
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:107:    from core.scheduler.scheduler_manager import get_scheduler_manager
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:108:    from core.scheduler.jobs.pedidos_detector_job import ejecutar_detector_manual as _ejecutar
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:110:    manager = get_scheduler_manager()
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:137:    from core.scheduler.scheduler_manager import get_scheduler_manager
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:143:    ultima = db.scheduler_job_logs.find_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:151:        manager = get_scheduler_manager()
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:64:    # Usar método síncrono para MongoDB síncrono
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:85:    Este endpoint puede ser invocado manualmente o por un cron externo cada hora.
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:98:    # Primero actualizar el campo vencida en tareas (síncrono)
/app/backend/modules/api_connections/__init__.py:10:- Sincronización bidireccional entre ambas fuentes
/app/backend/modules/api_connections/__init__.py:15:- Sincronización automática con MongoDB
/app/backend/modules/api_connections/repository.py:7:- Sincronización: EDARSAHUB SQL → MongoDB (nunca al revés)
/app/backend/modules/api_connections/repository.py:478:# SINCRONIZACIÓN EDARSAHUB SQL → MONGODB (CACHÉ)
/app/backend/modules/api_connections/repository.py:483:    Sincroniza una conexión específica de EDARSAHUB SQL a MongoDB caché.
/app/backend/modules/api_connections/repository.py:521:        logging.warning(f"[API_CONNECTIONS] Error sincronizando caché MongoDB: {e}")
/app/backend/modules/api_connections/repository.py:527:    Sincroniza todas las conexiones API de EDARSAHUB SQL a MongoDB caché.
/app/backend/modules/api_connections/repository.py:541:        logging.info(f"[API_CONNECTIONS] Sincronización completa: {synced} OK, {errors} errores")
/app/backend/modules/api_connections/repository.py:544:        logging.error(f"[API_CONNECTIONS] Error en sincronización masiva: {e}")
/app/backend/modules/api_connections/repository.py:545:        raise RuntimeError(f"Error sincronizando: {e}")
/app/backend/modules/api_connections/routes.py:281:    Sincroniza conexiones API de EDARSAHUB SQL a MongoDB caché.
/app/backend/modules/api_connections/routes.py:289:            "message": "Sincronización EDARSAHUB SQL → MongoDB completada", 
/app/backend/modules/api_connections/routes.py:295:        logging.error(f"[API_CONNECTIONS] Error sincronizando: {e}")
/app/backend/modules/costos_margenes/repository.py:88:        'ultima_sincronizacion': p.get('ultima_sync'),
/app/backend/modules/costos_margenes/repository.py:224:        p.SyncedAtMexico as ultima_sincronizacion,
/app/backend/modules/costos_margenes/repository.py:290:            'ultima_sincronizacion': row.get('ultima_sincronizacion'),
/app/backend/modules/costos_margenes/repository.py:588:    Obtiene estado de sincronización.
/app/backend/modules/costos_margenes/repository.py:669:        'fecha_ultima_sincronizacion': sync_info.get('SyncedAtMexico'),
/app/backend/modules/costos_margenes/routes_precios.py:565:    se realizará en una fase posterior con diseño de sincronización.
/app/backend/modules/costos_margenes/routes_precios.py:583:        comentario = data.comentario if data else "Aplicación registrada (pendiente sincronización con origen)"
/app/backend/modules/costos_margenes/routes_precios.py:603:                f"Nota: La sincronización con sistema origen se realizará en fase posterior."
/app/backend/modules/costos_margenes/routes.py:187:    - Total productos sincronizados
/app/backend/modules/costos_margenes/routes.py:191:    - Metadata de sincronización
/app/backend/modules/costos_margenes/routes.py:211:            ultima_sincronizacion=data.get('ultima_sincronizacion'),
/app/backend/modules/costos_margenes/routes.py:326:                ultima_sincronizacion=p.get('ultima_sincronizacion'),
/app/backend/modules/costos_margenes/routes.py:430:            ultima_sincronizacion=producto.get('SyncedAtMexico'),
/app/backend/modules/costos_margenes/routes.py:510:    Obtiene estado de sincronización del módulo.
/app/backend/modules/costos_margenes/routes.py:518:    - Fecha última sincronización
/app/backend/modules/costos_margenes/routes.py:530:            fecha_ultima_sincronizacion=data.get('fecha_ultima_sincronizacion'),
/app/backend/modules/costos_margenes/schemas.py:50:    ultima_sincronizacion: Optional[datetime] = None
/app/backend/modules/costos_margenes/schemas.py:108:    ultima_sincronizacion: Optional[datetime] = None
/app/backend/modules/costos_margenes/schemas.py:176:    ultima_sincronizacion: Optional[datetime] = None
/app/backend/modules/costos_margenes/schemas.py:244:    """Estado de sincronización."""
/app/backend/modules/costos_margenes/schemas.py:247:    fecha_ultima_sincronizacion: Optional[datetime] = None
/app/backend/modules/rh/repository.py:160:    Versión síncrona de get_edarsa_hub_server para uso en funciones no-async.
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:49:    """Ejecuta query SQL de forma síncrona."""
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:75:    """Ejecuta query SQL de forma asíncrona."""
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:395:    async def sincronizar_almacenes_unidad(
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:402:        Sincroniza almacenes - operación placeholder.
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:405:        logger.info(f"[CONFIG_ASIG] Sincronización de almacenes omitida (SQL-only mode)")
/app/backend/modules/configuracion/services/almacenes_sync_service.py:2:Servicio de Sincronización de Almacenes
/app/backend/modules/configuracion/services/almacenes_sync_service.py:6:Sincroniza almacenes desde sistemas origen (SoftRestaurant/MPRO) al catálogo local MongoDB.
/app/backend/modules/configuracion/services/almacenes_sync_service.py:14:5. NO consulta SQL desde UI - este service es el único punto de sincronización
/app/backend/modules/configuracion/services/almacenes_sync_service.py:38:    Resultado de sincronización de almacenes con metadatos útiles.
/app/backend/modules/configuracion/services/almacenes_sync_service.py:45:    # Metadatos de sincronización
/app/backend/modules/configuracion/services/almacenes_sync_service.py:57:    def total_sincronizados(self) -> int:
/app/backend/modules/configuracion/services/almacenes_sync_service.py:75:            "sincronizados": self.total_sincronizados,
/app/backend/modules/configuracion/services/almacenes_sync_service.py:82:async def sincronizar_almacenes_desde_origen(
/app/backend/modules/configuracion/services/almacenes_sync_service.py:89:    Sincroniza almacenes desde el sistema origen al catálogo local.
/app/backend/modules/configuracion/services/almacenes_sync_service.py:100:        unidad_negocio_id: ID de la unidad de negocio a sincronizar
/app/backend/modules/configuracion/services/almacenes_sync_service.py:101:        usuario_sync: Email del usuario que ejecuta la sincronización
/app/backend/modules/configuracion/services/almacenes_sync_service.py:198:        # PASO 5: Sincronizar al catálogo local MongoDB
/app/backend/modules/configuracion/services/almacenes_sync_service.py:275:        result.status = QueryStatus.SUCCESS_WITH_DATA if result.total_sincronizados > 0 else QueryStatus.SUCCESS_EMPTY
/app/backend/modules/configuracion/services/almacenes_sync_service.py:277:            f"Sincronizados {result.total_sincronizados} almacenes para {result.unidad_negocio_nombre}"
/app/backend/modules/configuracion/services/almacenes_sync_service.py:289:        logger.exception(f"[Sync Almacenes] Error inesperado sincronizando {unidad_negocio_id}")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:269:async def info_sincronizacion_almacenes(
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:274:    Obtiene información de la última sincronización de almacenes.
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:277:        - ultima_sincronizacion: timestamp ISO
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:299:            "ultima_sincronizacion": almacen_mas_reciente.get("fecha_sync") if almacen_mas_reciente else None,
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:633:# ENDPOINT DE SINCRONIZACIÓN DE ALMACENES (Admin only)
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:636:@router.post("/almacenes/sincronizar/{unidad_negocio_id}")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:637:async def sincronizar_almacenes(
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:642:    Sincroniza almacenes desde el servidor SQL al catálogo local.
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:654:    # Solo SuperAdministrador puede sincronizar
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:656:        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede sincronizar almacenes")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:664:    from ..services.almacenes_sync_service import sincronizar_almacenes_desde_origen
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:666:    result = await sincronizar_almacenes_desde_origen(
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:677:            detail=result.error_message or "Error desconocido en sincronización"
/app/backend/modules/inventarios/repository.py:9:- Datos sincronizados en tabla Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:20:    Obtiene inventarios físicos desde la tabla sincronizada de EDARSAHUB.
/app/backend/modules/consultas_sql/repository.py:128:        if filters.es_sincronizable is not None:
/app/backend/modules/consultas_sql/repository.py:129:            where_clauses.append(f"c.EsSincronizable = {1 if filters.es_sincronizable else 0}")
/app/backend/modules/consultas_sql/repository.py:159:                c.EsSincronizable,
/app/backend/modules/consultas_sql/repository.py:205:                c.EsSincronizable,
/app/backend/modules/consultas_sql/repository.py:255:                c.EsSincronizable,
/app/backend/modules/consultas_sql/repository.py:304:                c.EsSincronizable,
/app/backend/modules/consultas_sql/models.py:236:    es_sincronizable: bool = False
/app/backend/modules/consultas_sql/models.py:274:            es_sincronizable=bool(row.get('EsSincronizable', False)),
/app/backend/modules/consultas_sql/models.py:306:            'es_sincronizable': self.es_sincronizable,
/app/backend/modules/consultas_sql/models.py:348:    es_sincronizable: Optional[bool] = None
/app/backend/modules/sync_historicos/service.py:4:FASE SYNC-1: Lógica de negocio para sincronización histórica.
/app/backend/modules/sync_historicos/service.py:61:    Service para sincronización de históricos de ventas.
/app/backend/modules/sync_historicos/service.py:75:        logger.info("[SYNC-SERVICE] Inicializando infraestructura de sincronización...")
/app/backend/modules/sync_historicos/service.py:79:        """Genera un ID único para el run de sincronización."""
/app/backend/modules/sync_historicos/service.py:235:        Sincroniza ventas históricas.
/app/backend/modules/sync_historicos/service.py:603:        Sincroniza ventas por hora.
/app/backend/modules/sync_historicos/service.py:830:        Sincroniza ventas agregadas por día de semana.
/app/backend/modules/sync_historicos/__init__.py:2:EDARSA HUB - Sync Históricos: Módulo de Sincronización
/app/backend/modules/sync_historicos/__init__.py:4:FASE SYNC-1: Infraestructura base para sincronización de históricos a EDARSAHUB.
/app/backend/modules/sync_historicos/repository.py:4:FASE SYNC-1: Acceso a datos para sincronización histórica.
/app/backend/modules/sync_historicos/repository.py:122:                -- Control de sincronización
/app/backend/modules/sync_historicos/repository.py:443:        """Registra el inicio de una ejecución de sincronización."""
/app/backend/modules/sync_historicos/repository.py:492:        """Obtiene la última ejecución de sincronización para un servidor."""
/app/backend/modules/sync_historicos/models.py:78:    # Control de sincronización
/app/backend/modules/sync_historicos/models.py:134:    # Control de sincronización
/app/backend/modules/sync_historicos/models.py:189:    # Control de sincronización
/app/backend/modules/sync_historicos/models.py:207:    Bitácora de ejecuciones de sincronización.
/app/backend/modules/sync_historicos/models.py:249:    """Configuración para una ejecución de sincronización."""
/app/backend/modules/sync_historicos/models.py:272:    """Resultado de una ejecución de sincronización."""
/app/backend/modules/sync_historicos/sync_ventas.py:4:FASE SYNC-1: Funciones específicas para sincronización de ventas.
/app/backend/modules/sync_historicos/sync_ventas.py:7:de sincronización de ventas históricas.
/app/backend/modules/sync_historicos/sync_ventas.py:35:    Ejecuta sincronización de ventas en modo DRY-RUN.
/app/backend/modules/sync_historicos/sync_ventas.py:74:    Ejecuta sincronización de ventas con escritura real.
/app/backend/modules/sync_historicos/sync_ventas.py:122:    Verifica el estado de la infraestructura de sincronización.
/app/backend/modules/sync_historicos/sync_ventas.py:213:    Ejecuta sincronización de ventas por hora en modo DRY-RUN.
/app/backend/modules/sync_historicos/sync_ventas.py:240:    Ejecuta sincronización de ventas por hora con escritura real.
/app/backend/modules/sync_historicos/sync_ventas.py:274:    Ejecuta sincronización de ventas por día de semana en modo DRY-RUN.
/app/backend/modules/sync_historicos/sync_ventas.py:301:    Ejecuta sincronización de ventas por día de semana con escritura real.
/app/backend/modules/automatizacion/feature_flags.py:18:    # Scheduler - Detección automática de nuevos folios
/app/backend/modules/automatizacion/feature_flags.py:19:    "SCHEDULER_ACTIVO": False,
/app/backend/modules/automatizacion/schemas.py:147:    """Schema base para ejecuciones del scheduler."""
/app/backend/modules/edge/sincronizador_catalogos_edge.py:1:# backend/modules/edge/sincronizador_catalogos_edge.py
/app/backend/modules/edge/sincronizador_catalogos_edge.py:8:class SincronizadorCatalogosEdge:
/app/backend/modules/edge/sincronizador_catalogos_edge.py:14:    # 1. SINCRONIZACIÓN DE PERSONAL Y MATRIZ DE ROLES (ERP ENTERPRISE)
/app/backend/modules/edge/sincronizador_catalogos_edge.py:61:    # 2. SINCRONIZACIÓN ELÁSTICA DE LA CARTA Y RECETAS (SOFT RESTAURANT / MOPRO)
/app/backend/modules/edge/motor_reglas_comerciales.py:77:        Analiza el contexto de la comanda de forma asíncrona local para guiar al vendedor.
/app/backend/modules/edge/gestor_sincronizacion_rafagas.py:1:# backend/modules/edge/gestor_sincronizacion_rafagas.py
/app/backend/modules/edge/gestor_sincronizacion_rafagas.py:9:class GestorSincronizacionRafagas:
/app/backend/modules/edge/gestor_sincronizacion_rafagas.py:27:    def procesar_rafaga_sincronizacion(self) -> None:
/app/backend/modules/edge/gestor_sincronizacion_rafagas.py:30:        cola FIFO en orden cronológico estricto (First In, First Out).
/app/backend/modules/edge/gestor_sincronizacion_rafagas.py:37:        query_fifo = "SELECT uuid_transaccion, payload_json FROM cola_sincronizacion_offline WHERE estado = 'PENDING_SYNC' ORDER BY creado_at ASC"
/app/backend/modules/edge/gestor_sincronizacion_rafagas.py:58:                # Actualizar el registro local a sincronizado
/app/backend/modules/edge/gestor_sincronizacion_rafagas.py:61:                    cursor.execute("UPDATE cola_sincronizacion_offline SET estado = 'SYNCED' WHERE uuid_transaccion = ?", (token_uuid,))
/app/backend/modules/edge/servidor_local_contingencia.py:44:        if self.path == "/v1/edge/sincronizar_ticket":
/app/backend/modules/edge/servidor_local_contingencia.py:62:                self.send_response(202) # Accepted para procesamiento asíncrono
/app/backend/modules/edge/comandero_local_core.py:20:            # 1. Réplica Local del Catálogo (Sincronizada en background desde EdarasHub)
/app/backend/modules/edge/comandero_local_core.py:53:                CREATE TABLE IF NOT EXISTS cola_sincronizacion_offline (
/app/backend/modules/edge/comandero_local_core.py:66:    def edge_sincronizar_producto(self, prod: Dict[str, Any]) -> None:
/app/backend/modules/edge/comandero_local_core.py:152:                INSERT INTO cola_sincronizacion_offline (uuid_transaccion, payload_json, creado_at)
/app/backend/modules/edge/comandero_local_core.py:162:        Extrae las transacciones pendientes en orden cronológico estricto (FIFO).
/app/backend/modules/edge/comandero_local_core.py:167:            cursor.execute("SELECT payload_json FROM cola_sincronizacion_offline WHERE estado = 'PENDING_SYNC' ORDER BY creado_at ASC")
/app/backend/modules/edge/comandero_local_core.py:170:    def marcar_transaccion_sincronizada(self, uuid_transaccion: str) -> None:
/app/backend/modules/edge/comandero_local_core.py:176:            cursor.execute("UPDATE cola_sincronizacion_offline SET estado = 'SYNCED' WHERE uuid_transaccion = ?", (uuid_transaccion,))
/app/backend/modules/edge/orquestador_kds_core.py:31:                    timestamp_liberacion INTEGER NOT NULL, -- Conteo regresivo para sincronía
/app/backend/modules/edge/orquestador_kds_core.py:80:        # Segundo: Calcular retenciones para lograr la entrega al mismo tiempo (Sincronía)
/app/backend/modules/edge/super_caja_arquero.py:39:        query_tickets = "SELECT payload_json FROM cola_sincronizacion_offline"
/app/backend/modules/edge/super_caja_arquero.py:136:                "status_sincronizacion": "PENDING_SYNC",
/app/backend/modules/edge/auditoria_inteligencia_operativa.py:77:        query = "SELECT payload_json FROM cola_sincronizacion_offline WHERE estado = 'PENDING_SYNC' ORDER BY creado_at DESC LIMIT 1"
/app/backend/modules/auth/routes.py:546:            'SCHEDULER_VER' in context.permisos
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:5:Sincronizador de datos comerciales hacia EDARSAHUB.
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:12:- NO tiene scheduler activo (ejecución manual)
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:275:    Sincroniza ventas cerradas de SoftRestaurant hacia EDARSAHUB v2.
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:381:    Sincroniza ventas cerradas de MPRO hacia EDARSAHUB v2.
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:504:    Sincroniza ventas cerradas de una unidad específica.
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:535:    Sincroniza ventas cerradas de TODAS las unidades activas.
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:542:        logger.info(f"Sincronizando {config.unidad_negocio_nombre}...")
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:574:    PRUEBA CONTROLADA: Sincroniza 1 día de 1 unidad SoftRestaurant.
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:602:    PRUEBA CONTROLADA: Sincroniza 1 día de 1 unidad MPRO.
/app/backend/modules/comercial_v2/__init__.py:6:1. Sincronización de datos comerciales hacia EDARSAHUB (Subfases 1-2)
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:16:- Activar scheduler
/app/backend/modules/comercial_v2/repository_readonly.py:117:        fecha_sincronizacion
/app/backend/modules/comercial_v2/repository_readonly.py:413:    Obtiene el estado de sincronización desde Comercial_SyncLog_v2.
/app/backend/modules/comercial_v2/repository_readonly.py:452:    Obtiene la última sincronización por unidad.
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:6:Incluye operaciones CRUD y funciones de sincronización.
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:215:            fecha_sincronizacion, fecha_alta, fecha_ultima_actualizacion, version
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:467:    """Inserta un registro en el log de sincronización"""
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:507:    """Obtiene el último log de sincronización para una unidad"""
/app/backend/modules/comercial_v2/routes.py:1180:    - NO mostrar $0 falso si no hay dato sincronizado válido
/app/backend/modules/comercial_v2/routes.py:1394:    Estado de sincronización v2.
/app/backend/modules/comercial_v2/schemas.py:5:Modelos Pydantic para el módulo de sincronización comercial v2.
/app/backend/modules/comercial_v2/schemas.py:32:    """Tipos de ejecución de sincronización"""
/app/backend/modules/comercial_v2/schemas.py:40:    """Estados posibles de una sincronización"""
/app/backend/modules/comercial_v2/schemas.py:229:    """Resultado de una operación de sincronización"""
/app/backend/modules/tablajeria/ordenes_service.py:125:            if plantilla['Estatus'] not in ('PUBLICADA', 'SINCRONIZADA', 'VALIDADA'):
/app/backend/modules/tablajeria/sync_service.py:4:Servicio de sincronización de plantillas desde servidores legacy.
/app/backend/modules/tablajeria/sync_service.py:34:    Servicio de sincronización de plantillas de tablajería.
/app/backend/modules/tablajeria/sync_service.py:66:    # SINCRONIZACIÓN PRINCIPAL
/app/backend/modules/tablajeria/sync_service.py:76:        Sincroniza plantillas desde un servidor legacy.
/app/backend/modules/tablajeria/sync_service.py:80:            entidades: Lista de entidades a sincronizar ['plantillas']
/app/backend/modules/tablajeria/sync_service.py:149:        """Sincroniza desde MPRO TABLAJERIA"""
/app/backend/modules/tablajeria/sync_service.py:196:        """Sincroniza plantillas desde MPRO"""
/app/backend/modules/tablajeria/sync_service.py:295:                    SET FechaSincronizacionUTC = %s
/app/backend/modules/tablajeria/sync_service.py:377:                Estatus, Activo, FechaAltaUTC, FechaSincronizacionUTC,
/app/backend/modules/tablajeria/sync_service.py:403:            EstatusPlantilla.SINCRONIZADA.value,
/app/backend/modules/tablajeria/sync_service.py:481:                FechaSincronizacionUTC = %s,
/app/backend/modules/tablajeria/sync_service.py:489:            EstatusPlantilla.SINCRONIZADA.value,
/app/backend/modules/tablajeria/sync_service.py:572:        """Sincroniza desde CIENFUEGOS TABLAJERIA (SoftRestaurant)"""
/app/backend/modules/tablajeria/sync_service.py:622:        """Registra el resultado de la sincronización en EDARSAHUB"""
```
