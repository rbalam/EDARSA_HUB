# Auditoría de Conexiones LIVE a Sistemas Externos

**Fecha:** Thu Jun  4 04:26:05 UTC 2026

**Regla:** EDARSAHUB SQL debe ser la ÚNICA fuente de verdad.

---

## 1. Conexiones Directas en Backend (execute_sql_query a servidores externos)

```
/app/backend/modules/comercial/service.py:36:from core.db import execute_sql_query, check_column_exists, get_propina_safe_column, get_propina_safe_column_tempcheques
/app/backend/modules/comercial/service.py:128:        result = execute_sql_query(
/app/backend/modules/comercial/service.py:242:            from core.db import execute_sql_query
/app/backend/modules/comercial/service.py:480:        result = execute_sql_query(
/app/backend/modules/comercial/service.py:1937:        result_ultimo = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/service.py:2063:            result_ultimo_suc = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/service.py:2126:            r_ant = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/service.py:2149:            r_año = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/queries/mpro.py:53:from core.db import execute_sql_query
/app/backend/modules/comercial/queries/mpro.py:199:        result = execute_sql_query(
/app/backend/modules/comercial/queries/mpro.py:380:        result = execute_sql_query(
/app/backend/modules/comercial/queries/mpro.py:690:        result = execute_sql_query(
/app/backend/modules/comercial/queries/softrestaurant.py:47:from core.db import execute_sql_query, check_column_exists, get_propina_safe_column
/app/backend/modules/comercial/queries/softrestaurant.py:181:        result = execute_sql_query(
/app/backend/modules/comercial/alertas_margen_repository.py:20:from core.db import execute_sql_query
/app/backend/modules/comercial/alertas_margen_repository.py:108:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/alertas_margen_repository.py:148:    rows = execute_sql_query(*conn, data_query) or []
/app/backend/modules/comercial/alertas_margen_repository.py:225:    rows = execute_sql_query(*conn, query)
/app/backend/modules/comercial/alertas_margen_repository.py:317:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/alertas_margen_repository.py:421:    execute_sql_query(*conn, query)
/app/backend/modules/comercial/alertas_margen_repository.py:486:    execute_sql_query(*conn, query)
/app/backend/modules/comercial/alertas_margen_repository.py:518:    execute_sql_query(*conn, query)
/app/backend/modules/comercial/alertas_margen_repository.py:618:        rows = execute_sql_query(*conn, query)
/app/backend/modules/comercial/alertas_margen_repository.py:675:    rows = execute_sql_query(*conn, query) or []
/app/backend/modules/comercial/alertas_margen_repository.py:752:    rows = execute_sql_query(*conn, query)
/app/backend/modules/comercial/repository.py:24:from core.db import execute_sql_query
/app/backend/modules/comercial/repository.py:156:        results = execute_sql_query(
/app/backend/modules/comercial/repository.py:186:        results = execute_sql_query(
/app/backend/modules/comercial/repository.py:306:        results = execute_sql_query(
/app/backend/modules/comercial/repository.py:384:    return execute_sql_query(
/app/backend/modules/comercial/repository.py:413:    return execute_sql_query(
/app/backend/modules/comercial/repository.py:448:    return execute_sql_query(
/app/backend/modules/comercial/historical_kpis_repository.py:31:from core.db import execute_sql_query
/app/backend/modules/comercial/historical_kpis_repository.py:95:    return execute_sql_query(
/app/backend/modules/comercial/services/impuestos_service.py:22:from core.db import execute_sql_query
/app/backend/modules/comercial/services/impuestos_service.py:152:    override_result = execute_sql_query(*conn, override_query)
/app/backend/modules/comercial/services/impuestos_service.py:182:    producto_result = execute_sql_query(*conn, producto_query)
/app/backend/modules/comercial/services/impuestos_service.py:286:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/impuestos_service.py:339:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/listas_competidores_service.py:20:from core.db import execute_sql_query
/app/backend/modules/comercial/services/listas_competidores_service.py:103:        execute_sql_query(*conn, ddl_listas)
/app/backend/modules/comercial/services/listas_competidores_service.py:104:        execute_sql_query(*conn, ddl_detalle)
/app/backend/modules/comercial/services/listas_competidores_service.py:175:        result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/listas_competidores_service.py:176:        count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/services/listas_competidores_service.py:256:        execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/listas_competidores_service.py:314:        execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/listas_competidores_service.py:336:        execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/listas_competidores_service.py:372:        result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/listas_competidores_service.py:445:        result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/listas_competidores_service.py:498:        existing = execute_sql_query(*conn, check_query)
/app/backend/modules/comercial/services/listas_competidores_service.py:513:            execute_sql_query(*conn, reactivate_query)
/app/backend/modules/comercial/services/listas_competidores_service.py:533:            execute_sql_query(*conn, insert_query)
/app/backend/modules/comercial/services/listas_competidores_service.py:563:        execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/listas_competidores_service.py:584:        result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/listas_competidores_service.py:612:        result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_service.py:25:from core.db import execute_sql_query
/app/backend/modules/comercial/services/competidores_service.py:155:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/services/competidores_service.py:202:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_service.py:255:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_service.py:345:    execute_sql_query(*conn, insert_query)
/app/backend/modules/comercial/services/competidores_service.py:423:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/competidores_service.py:442:    execute_sql_query(*conn, update_items_query)
/app/backend/modules/comercial/services/competidores_service.py:453:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/competidores_service.py:489:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/services/competidores_service.py:521:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_service.py:559:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_service.py:622:    execute_sql_query(*conn, insert_query)
/app/backend/modules/comercial/services/competidores_service.py:681:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/competidores_service.py:699:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/competidores_service.py:725:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_service.py:760:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:22:from core.db import execute_sql_query
/app/backend/modules/comercial/services/competidores_enterprise_service.py:116:    execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:151:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:181:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:232:    check_result = execute_sql_query(*conn, check_query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:245:    existe_result = execute_sql_query(*conn, existe_query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:292:    execute_sql_query(*conn, insert_query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:326:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:372:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:411:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:493:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:542:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:580:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/competidores_enterprise_service.py:635:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/benchmark_service.py:24:from core.db import execute_sql_query
/app/backend/modules/comercial/services/benchmark_service.py:121:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/services/benchmark_service.py:158:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/benchmark_service.py:201:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/benchmark_service.py:251:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/benchmark_service.py:304:    execute_sql_query(*conn, insert_query)
/app/backend/modules/comercial/services/benchmark_service.py:352:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/benchmark_service.py:374:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/benchmark_service.py:394:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/benchmark_service.py:430:    result_benchmark = execute_sql_query(*conn, query_benchmark)
/app/backend/modules/comercial/services/benchmark_service.py:449:    result_productos = execute_sql_query(*conn, query_productos)
/app/backend/modules/comercial/services/benchmark_service.py:523:    result = execute_sql_query(*conn, query_validados)
/app/backend/modules/comercial/services/benchmark_service.py:571:    result_menu = execute_sql_query(*conn, query_con_menu)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:21:from core.db import execute_sql_query
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:75:    result = execute_sql_query(*conn, query)
```

## 2. Endpoints que reciben server_id (posibles consultas live)

```
/app/backend/modules/comercial/service.py:105:    - por_server_id: {server_id: {codigo, nombre, sucursal_origen_id}}
/app/backend/modules/comercial/service.py:106:    - por_server_sucursal: {server_id:sucursal: {codigo, nombre}}
/app/backend/modules/comercial/service.py:118:        server_id,
/app/backend/modules/comercial/service.py:137:        por_server_id = {}
/app/backend/modules/comercial/service.py:141:            server_id = row.get('server_id', '')
/app/backend/modules/comercial/service.py:153:            # Mapeo por server_id (para SoftRestaurant sin sucursal)
/app/backend/modules/comercial/service.py:155:                por_server_id[server_id] = unidad_data
/app/backend/modules/comercial/service.py:157:            # Mapeo por server_id:sucursal (para MPRO con sucursal)
/app/backend/modules/comercial/service.py:158:            key = f"{server_id}:{sucursal}" if sucursal else server_id
/app/backend/modules/comercial/service.py:162:            'por_server_id': por_server_id,
/app/backend/modules/comercial/service.py:172:        return {'por_server_id': {}, 'por_server_sucursal': {}, 'lista': []}
/app/backend/modules/comercial/service.py:175:def obtener_unidad_negocio_edarsahub(server_id: str, sucursal: str = None) -> Dict:
/app/backend/modules/comercial/service.py:183:        server_id: UUID del servidor
/app/backend/modules/comercial/service.py:191:    # Priorizar búsqueda por server_id:sucursal
/app/backend/modules/comercial/service.py:193:        key = f"{server_id}:{sucursal}"
/app/backend/modules/comercial/service.py:197:    # Fallback: búsqueda solo por server_id
/app/backend/modules/comercial/service.py:198:    if server_id in catalogo['por_server_id']:
/app/backend/modules/comercial/service.py:199:        return catalogo['por_server_id'][server_id]
/app/backend/modules/comercial/service.py:202:    logging.warning(f"[UNIDADES_NEGOCIO] No se encontró unidad para server_id={server_id}, sucursal={sucursal}")
/app/backend/modules/comercial/service.py:204:        'codigo': server_id,  # Fallback al server_id
/app/backend/modules/comercial/service.py:211:def _obtener_codigo_canonico_mpro(server_id: str, sucursal_id: str, sucursal_nombre: str) -> tuple:
/app/backend/modules/comercial/service.py:221:        server_id: ID del servidor MPRO
/app/backend/modules/comercial/service.py:265:    unidad_edarsahub = obtener_unidad_negocio_edarsahub(server_id, sucursal=sucursal_id)
/app/backend/modules/comercial/service.py:378:        Lista de dicts con: codigo, sucursal_id, server_id, empresa_id
/app/backend/modules/comercial/service.py:430:                server_id = row['ServidorID'].lower() if row['ServidorID'] else ''
/app/backend/modules/comercial/service.py:432:                if codigo and sucursal_id and server_id:
/app/backend/modules/comercial/service.py:436:                        "server_id": server_id,
/app/backend/modules/comercial/service.py:458:            "server_id": "817a0aa8-6170-4738-a8f6-a72ac36ba0df",
/app/backend/modules/comercial/service.py:465:            "server_id": "72f6e9a7-8ea2-4eb2-802e-4ee31753435e",
/app/backend/modules/comercial/service.py:494:def _get_ultimo_dia_con_datos_edarsahub(server_id: str, mes: int, anio: int) -> Optional[int]:
/app/backend/modules/comercial/service.py:502:    WHERE server_id = '{server_id}'
/app/backend/modules/comercial/service.py:514:    server_id: str,
/app/backend/modules/comercial/service.py:525:    - Si no, usar server_id + sucursal_id (comportamiento legacy)
/app/backend/modules/comercial/service.py:527:    RAZÓN: Para MPRO, los datos en Comercial_KPIs_Diarios_v2 tienen un server_id
/app/backend/modules/comercial/service.py:546:        # Legacy: Usar server_id
/app/backend/modules/comercial/service.py:547:        filtro_principal = f"server_id = '{server_id}'"
/app/backend/modules/comercial/service.py:589:def _get_ventas_abiertas_edarsahub(server_id: str, sucursal_id: str = 'DEFAULT', unidad_negocio_id: str = None) -> Dict:
/app/backend/modules/comercial/service.py:638:            f"[TABLERO-EDARSAHUB] _get_ventas_abiertas: server_id={server_id} FechaOperacion default={fecha_operacion} "
/app/backend/modules/comercial/service.py:647:    # FIX P0 (15-May-2026): Buscar por unidad_negocio_id en lugar de server_id
/app/backend/modules/comercial/service.py:676:        # Fallback: buscar por server_id + sucursal_id
/app/backend/modules/comercial/service.py:689:        WHERE server_id = '{server_id}'
/app/backend/modules/comercial/service.py:732:            f"[TABLERO-EDARSAHUB] _get_ventas_abiertas: server_id={server_id} "
/app/backend/modules/comercial/service.py:748:        f"[TABLERO-EDARSAHUB] _get_ventas_abiertas: Sin datos para server_id={server_id}, "
/app/backend/modules/comercial/service.py:788:    server_id: str,
/app/backend/modules/comercial/service.py:817:        server_id: ID del servidor EDARSAHUB (para mapear unidad)
/app/backend/modules/comercial/service.py:913:    kpis_actual = _get_kpis_periodo_edarsahub(server_id, fecha_ini, fecha_fin_real, sucursal_id, unidad_negocio_id=unidad_negocio_id)
/app/backend/modules/comercial/service.py:952:    kpis_mes_ant = _get_kpis_periodo_edarsahub(server_id, fecha_ini_ant, fecha_fin_ant, sucursal_id, unidad_negocio_id=unidad_negocio_id)
/app/backend/modules/comercial/service.py:965:    kpis_anio_ant = _get_kpis_periodo_edarsahub(server_id, fecha_ini_anio_ant, fecha_fin_anio_ant, sucursal_id, unidad_negocio_id=unidad_negocio_id)
/app/backend/modules/comercial/service.py:1191:    server_id = server.get('id', '')
/app/backend/modules/comercial/service.py:1206:    unidad_key = f"{server_id}:{unidad_negocio_codigo or sucursal or 'default'}"
/app/backend/modules/comercial/service.py:1231:        "unidad_negocio_id": unidad_negocio_codigo or server_id,  # Código canónico, no server_id
/app/backend/modules/comercial/service.py:1234:        "server_id": server_id,  # Mantener server_id solo como identificador técnico
/app/backend/modules/comercial/service.py:1332:async def obtener_sucursales_servidor(server_id: str) -> List[Dict]:
/app/backend/modules/comercial/service.py:1336:    server = await repo.get_server_by_id(server_id)
/app/backend/modules/comercial/service.py:1343:async def obtener_metas(server_id: str, sucursal: str, mes: int, anio: int) -> Dict:
/app/backend/modules/comercial/service.py:1347:    metas = await repo.get_metas_sucursal(server_id, sucursal, mes, anio)
/app/backend/modules/comercial/service.py:1351:async def guardar_metas(server_id: str, sucursal: str, mes: int, anio: int, metas: Dict) -> Dict:
/app/backend/modules/comercial/service.py:1355:    await repo.save_metas_sucursal(server_id, sucursal, mes, anio, metas)
/app/backend/modules/comercial/service.py:1389:    server_id = server.get('id', '')
/app/backend/modules/comercial/service.py:1396:    unidad_edarsahub = obtener_unidad_negocio_edarsahub(server_id, sucursal=None)
/app/backend/modules/comercial/service.py:1405:        logging.warning(f"[TABLERO-EDARSAHUB] server_id {server_id} no encontrado en Unidades_Negocio EDARSAHUB")
/app/backend/modules/comercial/service.py:1424:        ventas_abiertas = _get_ventas_abiertas_edarsahub(server_id, sucursal_id, unidad_negocio_id=unidad_negocio_codigo)
/app/backend/modules/comercial/service.py:1478:        server_id=server_id,
/app/backend/modules/comercial/service.py:1515:    server_id = server.get('id', '')
/app/backend/modules/comercial/service.py:1519:    mpro_config = UNIDADES_EDARSAHUB_MAP.get(server_id, {})
/app/backend/modules/comercial/service.py:1522:        logging.warning(f"[TABLERO-EDARSAHUB] {nombre}: server_id {server_id} no tiene mapeo de unidad MPRO")
/app/backend/modules/comercial/service.py:1553:            server_id=server_id,
/app/backend/modules/comercial/service.py:1713:                suc['server_id'], suc['sucursal_id']
/app/backend/modules/comercial/service.py:1721:                server_id=suc['server_id'],
/app/backend/modules/comercial/service.py:1736:                    "server_id": suc['server_id'],
/app/backend/modules/comercial/service.py:1774:                    "server_id": suc['server_id'],
/app/backend/modules/comercial/service.py:1833:            suc['server_id'], suc['sucursal_id']
/app/backend/modules/comercial/service.py:1845:            server_id=suc['server_id'],
/app/backend/modules/comercial/service.py:1858:            kpis['server_id'] = suc['server_id']
/app/backend/modules/comercial/service.py:1876:                "server_id": suc['server_id'],
/app/backend/modules/comercial/service.py:1937:        result_ultimo = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/service.py:2063:            result_ultimo_suc = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/service.py:2126:            r_ant = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/service.py:2149:            r_año = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/service.py:2164:            server_host=server['host'],
/app/backend/modules/comercial/service.py:2224:            "server_id": server['id'],
/app/backend/modules/comercial/service.py:2362:    server_id: str,
/app/backend/modules/comercial/service.py:2382:        server_id: UUID del servidor
/app/backend/modules/comercial/service.py:2392:        f"[DASHBOARD-EDARSAHUB] server_id={server_id[:8]}... "
/app/backend/modules/comercial/service.py:2398:    kpis_actual = _get_kpis_periodo_edarsahub_flexible(server_id, fecha_ini, fecha_fin, sucursal_id)
/app/backend/modules/comercial/service.py:2402:            f"[DASHBOARD-EDARSAHUB] Sin datos para server_id={server_id[:8]}... "
/app/backend/modules/comercial/service.py:2427:        kpis_ant = _get_kpis_periodo_edarsahub_flexible(server_id, fecha_ini_ant, fecha_fin_ant, sucursal_id)
/app/backend/modules/comercial/service.py:2439:        kpis_ano = _get_kpis_periodo_edarsahub_flexible(server_id, fecha_ini_ano_ant, fecha_fin_ano_ant, sucursal_id)
/app/backend/modules/comercial/service.py:2478:    server_id: str,
/app/backend/modules/comercial/service.py:2489:    FIX MPRO: Si no encuentra por server_id, intenta buscar por unidad_negocio_id
/app/backend/modules/comercial/service.py:2491:    tienen un server_id diferente al de Servidores_Conexiones.
/app/backend/modules/comercial/service.py:2494:    kpis = _get_kpis_periodo_edarsahub(server_id, fecha_ini, fecha_fin, sucursal_id)
/app/backend/modules/comercial/service.py:2508:        WHERE server_id = '{server_id}'
/app/backend/modules/comercial/service.py:2536:    # FIX MPRO: Buscar por unidad_negocio_id si no encontramos por server_id
/app/backend/modules/comercial/service.py:2539:    # tienen un server_id diferente (ej: ManagmentPro) pero el unidad_negocio_id
/app/backend/modules/comercial/service.py:2543:    unidad_ids = _obtener_unidad_ids_desde_servidor(server_id)
/app/backend/modules/comercial/service.py:2595:def _obtener_unidad_ids_desde_servidor(server_id: str) -> List[str]:
/app/backend/modules/comercial/service.py:2597:    Obtiene posibles unidad_negocio_id a partir del server_id.
/app/backend/modules/comercial/service.py:2604:    # Mapeo de server_id a posibles unidad_negocio_id
/app/backend/modules/comercial/service.py:2614:    return mapeo_servidor_unidad.get(server_id, [])
/app/backend/modules/comercial/service.py:2618:def get_last_valid_snapshot_edarsahub(server_id: str) -> Dict:
/app/backend/modules/comercial/service.py:2645:                server_id,
/app/backend/modules/comercial/service.py:2656:            WHERE server_id = %s
/app/backend/modules/comercial/service.py:2658:        """, (server_id,))
/app/backend/modules/comercial/service.py:2664:            logging.warning(f"[STALE-SNAPSHOT] Sin datos históricos para server_id={server_id[:8]}...")
/app/backend/modules/comercial/service.py:2672:        logging.info(f"[STALE-SNAPSHOT] Encontrado snapshot de {fecha_snapshot} para server_id={server_id[:8]}...")
/app/backend/modules/comercial/routes_pricing_ai.py:55:    server_id: str = Field(..., description="UUID del servidor")
/app/backend/modules/comercial/routes_pricing_ai.py:65:    server_id: str = Field(..., description="UUID del servidor")
/app/backend/modules/comercial/routes_pricing_ai.py:74:    server_id: str = Field(..., description="UUID del servidor")
/app/backend/modules/comercial/routes_pricing_ai.py:133:        server_id=request.server_id,
/app/backend/modules/comercial/routes_pricing_ai.py:194:        server_id=request.server_id,
/app/backend/modules/comercial/routes_pricing_ai.py:246:        server_id=request.server_id,
/app/backend/modules/comercial/cache_service.py:79:    server_id: str,
/app/backend/modules/comercial/cache_service.py:99:    base_key = f"comercial:{endpoint}:{server_id}"
/app/backend/modules/comercial/queries/hub.py:10:- kpis_comercial: KPIs consolidados por (server_id, empresa_id, sucursal_id, fecha)
/app/backend/modules/comercial/queries/hub.py:27:    "server_id": str,
/app/backend/modules/comercial/queries/hub.py:96:#     server_id: str,
/app/backend/modules/comercial/queries/hub.py:104:#         server_id: ID del servidor
/app/backend/modules/comercial/queries/hub.py:120:#     server_id: str,
/app/backend/modules/comercial/queries/hub.py:129:#         server_id: ID del servidor
/app/backend/modules/comercial/queries/hub.py:142:#     server_id: str,
/app/backend/modules/comercial/queries/hub.py:161:    server_id: str,
/app/backend/modules/comercial/queries/hub.py:171:        server_id: ID del servidor (requerido)
/app/backend/modules/comercial/queries/hub.py:180:    filtro = {"server_id": server_id}
/app/backend/modules/comercial/queries/mpro.py:39:- /comercial/dashboard/{server_id}
/app/backend/modules/comercial/queries/mpro.py:200:            server['host'], 
/app/backend/modules/comercial/queries/mpro.py:202:            server['database'],
/app/backend/modules/comercial/queries/mpro.py:258:    ORIGEN: Extraída de routes.py endpoint /comercial/dashboard/{server_id}
/app/backend/modules/comercial/queries/mpro.py:278:    - /comercial/dashboard/{server_id} (sección MPRO)
/app/backend/modules/comercial/queries/mpro.py:381:            server['host'], 
/app/backend/modules/comercial/queries/mpro.py:383:            server['database'],
/app/backend/modules/comercial/queries/mpro.py:691:            server['host'], 
/app/backend/modules/comercial/queries/mpro.py:693:            server['database'],
/app/backend/modules/comercial/queries/softrestaurant.py:35:- /comercial/dashboard/{server_id}
/app/backend/modules/comercial/queries/softrestaurant.py:122:    - /comercial/dashboard/{server_id} (migración Fase 2)
/app/backend/modules/comercial/queries/softrestaurant.py:160:        server['host'], server['port'], server['database'],
/app/backend/modules/comercial/queries/softrestaurant.py:182:            server['host'], 
/app/backend/modules/comercial/queries/softrestaurant.py:184:            server['database'],
/app/backend/modules/comercial/routes_precios_sugeridos.py:58:    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
/app/backend/modules/comercial/routes_precios_sugeridos.py:85:        server_id=server_id,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:319:        server_id,
/app/backend/modules/comercial/alertas_margen_service.py:163:    server_id: Optional[str] = None,
/app/backend/modules/comercial/alertas_margen_service.py:181:        server_id: Servidor (opcional)
/app/backend/modules/comercial/alertas_margen_service.py:229:        server_id=server_id,
/app/backend/modules/comercial/alertas_margen_service.py:337:    server_id: Optional[str] = None
/app/backend/modules/comercial/alertas_margen_service.py:350:        server_id: Servidor (opcional)
/app/backend/modules/comercial/alertas_margen_service.py:366:        server_id=server_id
/app/backend/modules/comercial/alertas_margen_service.py:397:    server_id: Optional[str] = None
/app/backend/modules/comercial/alertas_margen_service.py:415:        server_id: Servidor
/app/backend/modules/comercial/alertas_margen_service.py:428:        server_id=server_id
```

## 3. Rutas API que consultan sistemas externos

```
741:@api_router.post("/admin/sync/compras")
775:@api_router.post("/admin/detect/compras")
807:@api_router.get("/admin/compras/checkpoints")
830:@api_router.get("/admin/compras/eventos-pendientes")
854:@api_router.post("/admin/compras/procesar-eventos")
2278:@api_router.get("/servers/{server_id}/tipos-movimiento")
3248:@api_router.get("/servers/{server_id}/inventarios")
3364:@api_router.get("/inventarios/pendientes/{server_id}")
5976:@api_router.post("/reports/export/comparativo-inventarios")
6417:@api_router.get("/debug/tipos-movimiento-live/{server_id}")
6787:@api_router.get("/dashboard/inventory-summary")
6996:@api_router.get("/dashboard/servers-configured")
7023:@api_router.get("/dashboard/metrics")
7164:@api_router.get("/compras/inventarios-fisicos/{server_id}")
7325:@api_router.get("/compras/pedidos-vigentes/{server_id}")
7457:@api_router.get("/compras/detalle-pedido-manual/{server_id}")
7512:@api_router.get("/compras/detalle-movimientos/{server_id}")
7549:@api_router.get("/compras/detalle-consumos/{server_id}")
7584:@api_router.get("/compras/detalle-pedido/{server_id}/{folio}")
7631:@api_router.post("/compras/calculo-pedido")
8065:@api_router.get("/compras/parametros/{server_id}")
8090:@api_router.post("/compras/parametros")
8140:@api_router.post("/compras/productos-para-captura")
8336:@api_router.post("/compras/auditoria-operativa")
9079:@api_router.post("/compras/inventarios-provisionales")
9148:@api_router.get("/compras/inventarios-provisionales/{unidad_negocio_id}")
9208:@api_router.delete("/compras/inventarios-provisionales/{item_id}")
9252:@api_router.delete("/compras/inventarios-provisionales/limpiar/{unidad_negocio_id}")
9302:@api_router.post("/compras/detalle-movimientos")
9512:@api_router.post("/compras/detalle-consumos")
9621:@api_router.get("/compras/dashboard/{server_id}")
9942:@api_router.post("/compras/analisis")
10094:@api_router.get("/compras/facturas-proveedor/{server_id}")
10161:@api_router.get("/compras/detalle-factura/{server_id}/{folio}")
11422:@api_router.post("/auditoria/informes")
11496:@api_router.get("/auditoria/informes")
11566:@api_router.get("/auditoria/informes/{informe_id}")
11590:@api_router.put("/auditoria/informes/{informe_id}")
11629:@api_router.delete("/auditoria/informes/{informe_id}")
11663:@api_router.post("/auditoria/informes/{informe_id}/evidencias")
11740:@api_router.delete("/auditoria/informes/{informe_id}/evidencias/{evidencia_id}")
11786:@api_router.put("/auditoria/informes/{informe_id}/finalizar")
11816:@api_router.get("/auditoria/informes/{informe_id}/pdf")
12864:# @api_router.get("/rrhh/auditoria-fiscal")
12917:# @api_router.get("/rrhh/dashboard")
13339:@api_router.get("/finanzas/dashboard")
13439:@api_router.post("/finanzas/registrar-movimiento")
13643:# @api_router.get("/rrhh/reclutamiento/dashboard")
14398:@api_router.post("/informes-auditoria")
14445:@api_router.get("/informes-auditoria")
14497:@api_router.get("/informes-auditoria/{informe_id}")
14510:@api_router.put("/informes-auditoria/{informe_id}")
14543:@api_router.delete("/informes-auditoria/{informe_id}")
14559:@api_router.post("/informes-auditoria/{informe_id}/evidencias")
14621:@api_router.delete("/informes-auditoria/{informe_id}/evidencias/{evidencia_id}")
14645:@api_router.get("/informes-auditoria/{informe_id}/evidencias/{evidencia_id}")
14669:@api_router.put("/informes-auditoria/{informe_id}/estado")
14690:@api_router.get("/informes-auditoria/{informe_id}/export-pdf")
16360:@api_router.get("/nomina/ciclos/{ciclo_id}/movimientos")
16377:@api_router.post("/nomina/ciclos/{ciclo_id}/movimientos")
16437:@api_router.delete("/nomina/movimientos/{movimiento_id}")
```

## 4. Frontend con fetch a servidores dinámicos

```
/app/frontend/src/pages/Compras.js:80:function DashboardCompras({ servers, unidadesNegocio, selectedUnidad, setSelectedUnidad, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales, loadingUnidades }) {
/app/frontend/src/pages/Compras.js:111:      server_id: selectedServer,
/app/frontend/src/pages/Compras.js:125:      const response = await api.get(`/compras/dashboard/${selectedServer}?sucursal=${encodeURIComponent(selectedSucursal)}&meses=${selectedMeses.join(',')}&anios=${selectedAnios.join(',')}`);
/app/frontend/src/pages/Compras.js:210:  }, [selectedServer, selectedSucursal, selectedMeses, selectedAnios, selectedUnidad]);
/app/frontend/src/pages/Compras.js:213:    if (selectedServer && selectedSucursal) {
/app/frontend/src/pages/Compras.js:216:  }, [selectedServer, selectedSucursal, selectedMeses, selectedAnios, cargarDashboard]);
/app/frontend/src/pages/Compras.js:386:            <Button onClick={cargarDashboard} disabled={!selectedServer || !selectedSucursal || loading} className="mt-5">
/app/frontend/src/pages/Compras.js:526:function AutorizacionComprasTab({ servers, unidadesNegocio, selectedUnidad, setSelectedUnidad, selectedServer, setSelectedServer, selectedSucursal: parentSucursal, setSelectedSucursal: setParentSucursal, sucursales: parentSucursales }) {
/app/frontend/src/pages/Compras.js:549:    if (selectedServer) {
/app/frontend/src/pages/Compras.js:550:      const server = servers.find(s => s.id === selectedServer);
/app/frontend/src/pages/Compras.js:553:  }, [selectedServer, servers]);
/app/frontend/src/pages/Compras.js:556:  const fetchAlmacenes = useCallback(async (serverId, sucursal) => {
/app/frontend/src/pages/Compras.js:558:      const response = await api.get(`/servers/${serverId}/almacenes?sucursal=${encodeURIComponent(sucursal)}`);
/app/frontend/src/pages/Compras.js:566:  const fetchInventariosFisicos = useCallback(async (serverId, sucursal) => {
/app/frontend/src/pages/Compras.js:568:      const response = await api.get(`/compras/inventarios-fisicos/${serverId}?sucursal=${encodeURIComponent(sucursal)}`);
/app/frontend/src/pages/Compras.js:579:  const fetchPedidosVigentes = useCallback(async (serverId, sucursal) => {
/app/frontend/src/pages/Compras.js:581:      const response = await api.get(`/compras/pedidos-vigentes/${serverId}?sucursal=${encodeURIComponent(sucursal)}`);
/app/frontend/src/pages/Compras.js:590:    if (selectedServer && parentSucursal) {
/app/frontend/src/pages/Compras.js:591:      fetchAlmacenes(selectedServer, parentSucursal);
/app/frontend/src/pages/Compras.js:592:      fetchInventariosFisicos(selectedServer, parentSucursal);
/app/frontend/src/pages/Compras.js:593:      fetchPedidosVigentes(selectedServer, parentSucursal);
/app/frontend/src/pages/Compras.js:595:  }, [selectedServer, parentSucursal, fetchAlmacenes, fetchInventariosFisicos, fetchPedidosVigentes]);
/app/frontend/src/pages/Compras.js:645:    if (!selectedServer || !parentSucursal || (selectedAlmacenes.length === 0 && !todosAlmacenes)) {
/app/frontend/src/pages/Compras.js:667:        server_id: selectedServer,
/app/frontend/src/pages/Compras.js:826:            <Button onClick={calcularPedido} disabled={loading || !selectedServer || !parentSucursal}>
/app/frontend/src/pages/Compras.js:891:function AnalisisCompras({ servers, unidadesNegocio, selectedUnidad, setSelectedUnidad, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales }) {
/app/frontend/src/pages/Compras.js:918:    if (!selectedServer || !selectedSucursal) {
/app/frontend/src/pages/Compras.js:926:        server_id: selectedServer,
/app/frontend/src/pages/Compras.js:951:  }, [selectedServer, selectedSucursal, aniosSeleccionados, mesesSeleccionados]);
/app/frontend/src/pages/Compras.js:955:    if (selectedServer && selectedSucursal && mesesSeleccionados.length > 0 && aniosSeleccionados.length > 0) {
/app/frontend/src/pages/Compras.js:958:  }, [selectedServer, selectedSucursal, mesesSeleccionados, aniosSeleccionados, cargarAnalisis]);
/app/frontend/src/pages/Compras.js:994:      const response = await api.get(`/compras/facturas-proveedor/${selectedServer}`, {
/app/frontend/src/pages/Compras.js:1023:      const response = await api.get(`/compras/detalle-factura/${selectedServer}/${encodeURIComponent(factura.folio)}`);
/app/frontend/src/pages/Compras.js:1380:      {!loading && comprasPorProveedor.length === 0 && selectedServer && selectedSucursal && (
/app/frontend/src/pages/Compras.js:1485:function AuditoriaOperativaTab({ servers, unidadesNegocio, selectedUnidad, setSelectedUnidad, selectedServer, setSelectedServer, selectedSucursal: parentSucursal, setSelectedSucursal: setParentSucursal, sucursales: parentSucursales }) {
/app/frontend/src/pages/Compras.js:1637:    const savedFilters = localStorage.getItem(`auditoria_filters_${selectedServer}_${parentSucursal}`);
/app/frontend/src/pages/Compras.js:1652:  }, [selectedServer, parentSucursal]);
/app/frontend/src/pages/Compras.js:1656:    if (selectedServer && parentSucursal) {
/app/frontend/src/pages/Compras.js:1666:      localStorage.setItem(`auditoria_filters_${selectedServer}_${parentSucursal}`, JSON.stringify(filters));
/app/frontend/src/pages/Compras.js:1668:  }, [selectedServer, parentSucursal, selectedAlmacenes, folioPedido, fechaInicial, fechaAuditoria, selectedInvIniciales, selectedInvFinales, usarCapturaManual]);
/app/frontend/src/pages/Compras.js:1671:  // selectedServer y parentSucursal del closure. Incluirlas en deps causaría loops infinitos.
/app/frontend/src/pages/Compras.js:1673:    if (selectedServer && parentSucursal) {
/app/frontend/src/pages/Compras.js:1679:  }, [selectedServer, parentSucursal]);
/app/frontend/src/pages/Compras.js:1683:      const response = await api.get(`/servers/${selectedServer}/almacenes?sucursal=${encodeURIComponent(parentSucursal)}`);
/app/frontend/src/pages/Compras.js:1694:      const response = await api.get(`/compras/inventarios-fisicos/${selectedServer}?sucursal=${encodeURIComponent(parentSucursal)}`, {
/app/frontend/src/pages/Compras.js:1718:      const response = await api.get(`/compras/pedidos-vigentes/${selectedServer}?sucursal=${encodeURIComponent(parentSucursal)}`, {
/app/frontend/src/pages/Compras.js:1789:          server_id: selectedServer,
/app/frontend/src/pages/Compras.js:1823:          server_id: selectedServer,
/app/frontend/src/pages/Compras.js:1913:          server_id: selectedServer,
/app/frontend/src/pages/Compras.js:1961:        server_id: selectedServer,
/app/frontend/src/pages/Compras.js:2012:        server_id: selectedServer,
/app/frontend/src/pages/Compras.js:2065:    if (!selectedServer || !parentSucursal) {
/app/frontend/src/pages/Compras.js:2100:        server_id: selectedServer,
/app/frontend/src/pages/Compras.js:2631:              <Button onClick={realizarAuditoria} disabled={loading || !selectedServer || !parentSucursal} size="sm" className="h-8">
/app/frontend/src/pages/Compras.js:3394:  // Derivar server_id desde la unidad seleccionada (dato interno, no visible)
/app/frontend/src/pages/Compras.js:3395:  const selectedServer = useMemo(() => {
/app/frontend/src/pages/Compras.js:3403:      id: u.server_id,
/app/frontend/src/pages/Compras.js:3466:              const unidadPorServer = unidades.find(u => u.server_id === params.server);
/app/frontend/src/pages/Compras.js:3490:    if (selectedUnidad && selectedServer) {
/app/frontend/src/pages/Compras.js:3493:          const response = await api.get(`/servers/${selectedServer}/sucursales`);
/app/frontend/src/pages/Compras.js:3521:          localStorage.setItem(STORAGE_KEY, JSON.stringify({ unidad: selectedUnidad, server: selectedServer }));
/app/frontend/src/pages/Compras.js:3532:  }, [selectedUnidad, selectedServer, unidadesNegocio]);
/app/frontend/src/pages/Compras.js:3540:  // Traduce server_id a unidad_id
/app/frontend/src/pages/Compras.js:3541:  const handleServerChange = (serverId) => {
/app/frontend/src/pages/Compras.js:3542:    const unidad = unidadesNegocio.find(u => u.server_id === serverId);
/app/frontend/src/pages/Compras.js:3585:            selectedServer={selectedServer} 
/app/frontend/src/pages/Compras.js:3600:            selectedServer={selectedServer} 
/app/frontend/src/pages/Compras.js:3614:            selectedServer={selectedServer} 
/app/frontend/src/pages/Compras.js:3628:            selectedServer={selectedServer} 
/app/frontend/src/pages/comercial/PricingIA.jsx:672:    server_id: '',
/app/frontend/src/pages/comercial/PricingIA.jsx:738:              value={form.server_id}
/app/frontend/src/pages/comercial/PricingIA.jsx:739:              onChange={(e) => setForm({ ...form, server_id: e.target.value })}
/app/frontend/src/pages/comercial/PricingIA.jsx:828:            disabled={loading || !form.codigo_producto || !form.server_id}
/app/frontend/src/pages/comercial/CostosMargenes.jsx:124:const RecetaModal = ({ isOpen, onClose, productoId, serverId, onVerSubReceta }) => {
/app/frontend/src/pages/comercial/CostosMargenes.jsx:129:  const [productoActual, setProductoActual] = useState({ id: productoId, serverId });
/app/frontend/src/pages/comercial/CostosMargenes.jsx:148:      if (srvId) params.append('server_id', srvId);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:164:      setProductoActual({ id: productoId, serverId });
/app/frontend/src/pages/comercial/CostosMargenes.jsx:167:      cargarReceta(productoId, serverId);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:169:  }, [isOpen, productoId, serverId, cargarReceta]);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:177:        serverId: productoActual.serverId,
/app/frontend/src/pages/comercial/CostosMargenes.jsx:181:      const nuevoServerId = receta?.server_id || productoActual.serverId;
/app/frontend/src/pages/comercial/CostosMargenes.jsx:182:      setProductoActual({ id: nuevoId, serverId: nuevoServerId });
/app/frontend/src/pages/comercial/CostosMargenes.jsx:192:      setProductoActual({ id: anterior.id, serverId: anterior.serverId });
/app/frontend/src/pages/comercial/CostosMargenes.jsx:193:      cargarReceta(anterior.id, anterior.serverId);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:317:                    setProductoActual({ id: p.id, serverId: p.serverId });
/app/frontend/src/pages/comercial/CostosMargenes.jsx:318:                    cargarReceta(p.id, p.serverId);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:748:        server_id: producto.server_id,
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1351:  const [recetaModal, setRecetaModal] = useState({ open: false, productoId: null, serverId: null });
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1352:  const [insumosModal, setInsumosModal] = useState({ open: false, productoId: null, serverId: null });
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1640:              <option key={u.server_id} value={u.server_id}>{u.nombre}</option>
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1883:                                  onClick={() => setRecetaModal({ open: true, productoId: prod.producto_id, serverId: prod.server_id })}
/app/frontend/src/pages/comercial/CostosMargenes.jsx:2053:                              onClick={() => setRecetaModal({ open: true, productoId: prod.producto_id, serverId: prod.server_id })}
/app/frontend/src/pages/comercial/CostosMargenes.jsx:2065:                              onClick={() => setInsumosModal({ open: true, productoId: prod.producto_id, serverId: prod.server_id })}
/app/frontend/src/pages/comercial/CostosMargenes.jsx:2131:        onClose={() => setRecetaModal({ open: false, productoId: null, serverId: null })}
/app/frontend/src/pages/comercial/CostosMargenes.jsx:2133:        serverId={recetaModal.serverId}
/app/frontend/src/pages/comercial/CostosMargenes.jsx:2138:        onClose={() => setInsumosModal({ open: false, productoId: null, serverId: null })}
/app/frontend/src/pages/Finanzas.js:321:        ...(selectedUnidad && { server_id: selectedUnidad })
/app/frontend/src/pages/Finanzas.js:339:        ...(selectedUnidad && { server_id: selectedUnidad })
/app/frontend/src/pages/Finanzas.js:748:      // SUBFASE 2.5: Usar unidad_negocio_id en lugar de server_id
/app/frontend/src/pages/ConfigAsignaciones.jsx:10: * - Solo conceptos de negocio (NO server_id, NO sucursal_id)
```

## 5. Funciones que usan get_server_connection_info (conexiones dinámicas)

```
/app/backend/modules/consultas_sql/routes.py:36:from core.server_registry import get_server_connection_info_with_secrets
/app/backend/modules/consultas_sql/routes.py:749:        server_info = get_server_connection_info_with_secrets(request.servidor_id)
/app/backend/modules/universal_query/routes.py:171:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/modules/universal_query/routes.py:174:    server = get_server_connection_info_with_secrets(server_id)
/app/backend/modules/universal_query/routes.py:251:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/modules/universal_query/routes.py:256:    server = get_server_connection_info_with_secrets(server_id)
/app/backend/modules/finanzas/health.py:19:from core.server_registry import list_servers, get_server_connection_info, EDARSAHUB_CONFIG
/app/backend/modules/finanzas/health.py:124:        config = await get_server_connection_info(server_id, db=db)
/app/backend/modules/finanzas/health.py:436:    config = await get_server_connection_info(server_id, db=db)
/app/backend/modules/finanzas/repository_cortes_z.py:50:            from core.server_registry import get_server_connection_info
/app/backend/modules/finanzas/repository_cortes_z.py:54:            config = await get_server_connection_info(server_id, db=db)
/app/backend/modules/compras/repository.py:144:    from core.server_registry import get_server_connection_info
/app/backend/modules/compras/repository.py:148:    server = await get_server_connection_info(server_id, db=db)
/app/backend/modules/compras/repository.py:149:    # get_server_connection_info ya descifra credenciales, no necesita _decrypt_server_password
/app/backend/server.py:1783:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:1786:    from core.server_registry import get_server_connection_info
/app/backend/server.py:1792:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:2008:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:2028:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:2113:    from core.server_registry import get_server_connection_info_with_secrets, update_server as registry_update_server, get_server_by_id
/app/backend/server.py:2126:    server = get_server_connection_info_with_secrets(server_id)
/app/backend/server.py:2249:    from core.server_registry import get_server_connection_info_with_secrets, update_server as registry_update_server
/app/backend/server.py:2256:    server = get_server_connection_info_with_secrets(server_id)
/app/backend/server.py:2299:    from core.server_registry import get_server_connection_info
/app/backend/server.py:2302:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:2560:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:2566:    from core.server_registry import get_server_connection_info
/app/backend/server.py:2570:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:2665:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:2668:    from core.server_registry import get_server_connection_info
/app/backend/server.py:2679:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:2775:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:2778:    from core.server_registry import get_server_connection_info
/app/backend/server.py:2782:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:2812:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:2815:    from core.server_registry import get_server_connection_info
/app/backend/server.py:2822:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:3186:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:3189:    from core.server_registry import get_server_connection_info
/app/backend/server.py:3200:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:3260:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:3263:    from core.server_registry import get_server_connection_info
/app/backend/server.py:3274:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:3377:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:3380:    from core.server_registry import get_server_connection_info
/app/backend/server.py:3391:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:3612:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:3620:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:3659:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:3662:    from core.server_registry import get_server_connection_info
/app/backend/server.py:3666:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:3797:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:3866:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:5161:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:5172:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:5417:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:5427:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:5988:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:5999:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(request.server_id))
/app/backend/server.py:6258:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:6261:    from core.server_registry import get_server_connection_info
/app/backend/server.py:6269:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:6324:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:6345:    from core.server_registry import get_server_connection_info
/app/backend/server.py:6346:    conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:6423:    from core.server_registry import get_server_connection_info
/app/backend/server.py:6425:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:6481:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:6492:    from core.server_registry import get_server_connection_info
/app/backend/server.py:6493:    conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:6801:    from core.server_registry import get_server_connection_info_with_secrets, list_servers as registry_list_servers
/app/backend/server.py:6812:            server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:7121:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:7133:    from core.server_registry import get_server_connection_info
/app/backend/server.py:7140:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:8149:    from core.server_registry import get_server_connection_info
/app/backend/server.py:8150:    server = await get_server_connection_info(request.server_id, db=db)
/app/backend/server.py:8350:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:8358:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(request.server_id))
/app/backend/server.py:9317:    from core.server_registry import get_server_connection_info
/app/backend/server.py:9318:    server = await get_server_connection_info(request.server_id, db=db)
/app/backend/server.py:9519:    from core.server_registry import get_server_connection_info
/app/backend/server.py:9520:    server = await get_server_connection_info(request.server_id, db=db)
/app/backend/server.py:9948:    from core.server_registry import get_server_connection_info
/app/backend/server.py:9949:    server = await get_server_connection_info(request.server_id, db=db)
/app/backend/server.py:10100:    from core.server_registry import get_server_connection_info
/app/backend/server.py:10101:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:10167:    from core.server_registry import get_server_connection_info
/app/backend/server.py:10168:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:10581:    from core.server_registry import get_server_connection_info
/app/backend/server.py:10599:        conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:10830:    from core.server_registry import get_server_connection_info
/app/backend/server.py:10849:        conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:10946:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:10951:    from core.server_registry import get_server_connection_info
/app/backend/server.py:10954:    conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:11016:    from core.server_registry import get_server_connection_info
/app/backend/server.py:11034:        conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:11117:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:11128:    from core.server_registry import get_server_connection_info
```

## 6. Conexiones pymssql/pyodbc directas (no a EDARSAHUB)

```
/app/backend/modules/comercial/service.py:2632:        conn = pymssql.connect(
/app/backend/modules/comercial/inteligencia_comercial_routes.py:62:    return pytds.connect(
/app/backend/modules/comercial/routes.py:2044:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:2381:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:2683:            conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:2791:                conn_hoy = pymssql.connect(
/app/backend/modules/comercial/routes.py:2900:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:4129:        conn = pymssql.connect(
/app/backend/modules/fase2_operativo/sql_repository.py:41:    return pymssql.connect(
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:318:        return pymssql.connect(
/app/backend/modules/api_connections/universal_test_routes.py:142:        conn = pymssql.connect(
/app/backend/modules/api_connections/universal_test_routes.py:181:        conn = pymssql.connect(
/app/backend/modules/sistema/menu_service.py:29:        return pymssql.connect(
/app/backend/modules/rh/importador/homologacion_service.py:30:    return pymssql.connect(
/app/backend/modules/rh/importador/aprobacion_service.py:47:    return pymssql.connect(
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:37:    return pymssql.connect(
/app/backend/modules/inteligencia_comercial/routes.py:79:    return pymssql.connect(
/app/backend/modules/automatizacion/repository.py:344:        conn = pymssql.connect(
/app/backend/modules/auth/service.py:374:        conn = pymssql.connect(
/app/backend/modules/auth/password_reset.py:55:    return pymssql.connect(
/app/backend/modules/auth/repository.py:101:        conn = pymssql.connect(
/app/backend/modules/auth/repository.py:313:    return pymssql.connect(
/app/backend/modules/auth/context_service.py:47:    return pymssql.connect(
/app/backend/modules/tablajeria/ordenes_service.py:39:        return pymssql.connect(
/app/backend/modules/tablajeria/dashboard_service.py:27:        return pymssql.connect(
/app/backend/modules/tablajeria/fase6_service.py:81:        return pymssql.connect(
/app/backend/modules/tablajeria/sync_service.py:43:        return pymssql.connect(
/app/backend/modules/tablajeria/sync_service.py:161:            conn_mpro = pymssql.connect(
/app/backend/modules/tablajeria/sync_service.py:592:            conn_cf = pymssql.connect(
/app/backend/modules/tablajeria/routes.py:50:    return pymssql.connect(
/app/backend/modules/universal_query/routes.py:184:        conn = pymssql.connect(
/app/backend/modules/crm/automation_service.py:31:        return pymssql.connect(
/app/backend/modules/crm/comercial_routes.py:184:        conn = pymssql.connect(
/app/backend/modules/crm/trigger_service.py:73:        return pymssql.connect(
/app/backend/modules/crm/comercial_service.py:33:        return pymssql.connect(
/app/backend/modules/crm/repository.py:32:    return pymssql.connect(
/app/backend/modules/crm/native_routes.py:81:        conn = pymssql.connect(
/app/backend/modules/crm/native_routes.py:311:        conn = pymssql.connect(
/app/backend/modules/crm/native_routes.py:422:        conn = pymssql.connect(
/app/backend/modules/crm/sql/execute_crm_migration.py:68:        conn = pymssql.connect(
/app/backend/modules/crm/sql/execute_crm_migration.py:166:        conn = pymssql.connect(
/app/backend/modules/crm/integration/staging_processor.py:76:        return pymssql.connect(
/app/backend/modules/crm/integration/staging_service.py:33:        return pymssql.connect(
/app/backend/modules/crm/integration_routes.py:85:    return pymssql.connect(
/app/backend/modules/finanzas/sync_propinas_mpro.py:85:    return pymssql.connect(
/app/backend/modules/finanzas/sync_propinas_mpro.py:168:    return pymssql.connect(
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:58:    return pymssql.connect(
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:187:        conn = pytds.connect(
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:205:        conn = pymssql.connect(
/app/backend/modules/finanzas/sql_query_worker.py:133:        conn = pytds.connect(**conn_params)
```

## 7. Resumen de Violaciones Potenciales

| Categoría | Cantidad |
|-----------|----------|
| Conexiones directas backend | 583 |
| Referencias server_id frontend | 290 |
| Uso de get_server_connection_info | 129 |

---

## Acciones Recomendadas

1. **Migrar endpoints** para que consulten tablas Sync_* en EDARSAHUB SQL
2. **Eliminar parámetro server_id** de pantallas operativas
3. **Crear vistas/tablas canónicas** en EDARSAHUB para cada entidad
4. **Mantener jobs de sync** como único punto de conexión a externos

---
*Generado automáticamente por auditoría EDARSAHUB*
