# AUDITORIA DE CONEXIONES LIVE

Fecha: Thu Jun  4 04:28:19 UTC 2026

## RESUMEN

- Total referencias encontradas: 3935

## DETALLE DE HALLAZGOS

```text
/app/backend/modules/comercial/service.py:36:from core.db import execute_sql_query, check_column_exists, get_propina_safe_column, get_propina_safe_column_tempcheques
/app/backend/modules/comercial/service.py:105:    - por_server_id: {server_id: {codigo, nombre, sucursal_origen_id}}
/app/backend/modules/comercial/service.py:106:    - por_server_sucursal: {server_id:sucursal: {codigo, nombre}}
/app/backend/modules/comercial/service.py:118:        server_id,
/app/backend/modules/comercial/service.py:128:        result = execute_sql_query(
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
/app/backend/modules/comercial/service.py:242:            from core.db import execute_sql_query
/app/backend/modules/comercial/service.py:265:    unidad_edarsahub = obtener_unidad_negocio_edarsahub(server_id, sucursal=sucursal_id)
/app/backend/modules/comercial/service.py:378:        Lista de dicts con: codigo, sucursal_id, server_id, empresa_id
/app/backend/modules/comercial/service.py:430:                server_id = row['ServidorID'].lower() if row['ServidorID'] else ''
/app/backend/modules/comercial/service.py:432:                if codigo and sucursal_id and server_id:
/app/backend/modules/comercial/service.py:436:                        "server_id": server_id,
/app/backend/modules/comercial/service.py:458:            "server_id": "817a0aa8-6170-4738-a8f6-a72ac36ba0df",
/app/backend/modules/comercial/service.py:465:            "server_id": "72f6e9a7-8ea2-4eb2-802e-4ee31753435e",
/app/backend/modules/comercial/service.py:480:        result = execute_sql_query(
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
/app/backend/modules/comercial/service.py:2633:            server='<REDACTED_EDARSAHUB_SQL_HOST>',
/app/backend/modules/comercial/service.py:2636:            database='EDARSAHUB',
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
/app/backend/modules/comercial/cache_service.py:36:def init_cache_service(database=None):
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
/app/backend/modules/comercial/queries/mpro.py:53:from core.db import execute_sql_query
/app/backend/modules/comercial/queries/mpro.py:199:        result = execute_sql_query(
/app/backend/modules/comercial/queries/mpro.py:258:    ORIGEN: Extraída de routes.py endpoint /comercial/dashboard/{server_id}
/app/backend/modules/comercial/queries/mpro.py:278:    - /comercial/dashboard/{server_id} (sección MPRO)
/app/backend/modules/comercial/queries/mpro.py:380:        result = execute_sql_query(
/app/backend/modules/comercial/queries/mpro.py:690:        result = execute_sql_query(
/app/backend/modules/comercial/queries/softrestaurant.py:35:- /comercial/dashboard/{server_id}
/app/backend/modules/comercial/queries/softrestaurant.py:47:from core.db import execute_sql_query, check_column_exists, get_propina_safe_column
/app/backend/modules/comercial/queries/softrestaurant.py:122:    - /comercial/dashboard/{server_id} (migración Fase 2)
/app/backend/modules/comercial/queries/softrestaurant.py:181:        result = execute_sql_query(
/app/backend/modules/comercial/routes_precios_sugeridos.py:58:    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
/app/backend/modules/comercial/routes_precios_sugeridos.py:85:        server_id=server_id,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:63:        server=host,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:65:        database=database,
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
/app/backend/modules/comercial/alertas_margen_repository.py:20:from core.db import execute_sql_query
/app/backend/modules/comercial/alertas_margen_repository.py:108:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/alertas_margen_repository.py:122:        CAST(ServerID AS NVARCHAR(36)) as server_id,
/app/backend/modules/comercial/alertas_margen_repository.py:148:    rows = execute_sql_query(*conn, data_query) or []
/app/backend/modules/comercial/alertas_margen_repository.py:161:            'server_id': row.get('server_id'),
/app/backend/modules/comercial/alertas_margen_repository.py:208:        CAST(ServerID AS NVARCHAR(36)) as server_id,
/app/backend/modules/comercial/alertas_margen_repository.py:225:    rows = execute_sql_query(*conn, query)
/app/backend/modules/comercial/alertas_margen_repository.py:239:        'server_id': row.get('server_id'),
/app/backend/modules/comercial/alertas_margen_repository.py:317:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/alertas_margen_repository.py:332:    server_id: Optional[str] = None,
/app/backend/modules/comercial/alertas_margen_repository.py:350:        server_id: Servidor (opcional)
/app/backend/modules/comercial/alertas_margen_repository.py:407:        {f"'{server_id}'" if server_id else 'NULL'},
/app/backend/modules/comercial/alertas_margen_repository.py:421:    execute_sql_query(*conn, query)
/app/backend/modules/comercial/alertas_margen_repository.py:486:    execute_sql_query(*conn, query)
/app/backend/modules/comercial/alertas_margen_repository.py:518:    execute_sql_query(*conn, query)
/app/backend/modules/comercial/alertas_margen_repository.py:536:    server_id: Optional[str] = None
/app/backend/modules/comercial/alertas_margen_repository.py:549:        server_id: Servidor (opcional)
/app/backend/modules/comercial/alertas_margen_repository.py:578:    if server_id:
/app/backend/modules/comercial/alertas_margen_repository.py:579:        alcance_clauses.append(f"(ServerID IS NULL OR ServerID = '{server_id}')")
/app/backend/modules/comercial/alertas_margen_repository.py:618:        rows = execute_sql_query(*conn, query)
/app/backend/modules/comercial/alertas_margen_repository.py:675:    rows = execute_sql_query(*conn, query) or []
/app/backend/modules/comercial/alertas_margen_repository.py:752:    rows = execute_sql_query(*conn, query)
/app/backend/modules/comercial/routes_alertas_margen.py:58:    server_id: Optional[str] = None
/app/backend/modules/comercial/routes_alertas_margen.py:84:    server_id: Optional[str] = None
/app/backend/modules/comercial/routes_alertas_margen.py:148:            server_id=regla.server_id,
/app/backend/modules/comercial/routes_alertas_margen.py:238:    server_id: Optional[str] = Query(None),
/app/backend/modules/comercial/routes_alertas_margen.py:263:            server_id=server_id
/app/backend/modules/comercial/routes_alertas_margen.py:295:            server_id=request.server_id
/app/backend/modules/comercial/repository.py:24:from core.db import execute_sql_query
/app/backend/modules/comercial/repository.py:48:def init_comercial_repository(database=None) -> None:
/app/backend/modules/comercial/repository.py:145:def _get_server_by_id_sql(server_id: str) -> Optional[Dict]:
/app/backend/modules/comercial/repository.py:153:        WHERE (id = '{server_id}' OR mongodb_id = '{server_id}')
/app/backend/modules/comercial/repository.py:156:        results = execute_sql_query(
/app/backend/modules/comercial/repository.py:165:            logging.info(f"[SQL] Servidor {server_id} obtenido desde EDARSAHUB SQL")
/app/backend/modules/comercial/repository.py:169:        logging.warning(f"[SQL] Error obteniendo servidor {server_id} desde SQL: {e}")
/app/backend/modules/comercial/repository.py:186:        results = execute_sql_query(
/app/backend/modules/comercial/repository.py:202:async def get_server_by_id(server_id: str) -> Optional[Dict]:
/app/backend/modules/comercial/repository.py:207:    server = _get_server_by_id_sql(server_id)
/app/backend/modules/comercial/repository.py:210:    logging.debug(f"[SQL-ONLY] Servidor {server_id} no encontrado")
/app/backend/modules/comercial/repository.py:224:async def get_sucursales_visibles_config(server_id: str) -> Dict[str, bool]:
/app/backend/modules/comercial/repository.py:238:        configs = execute_hub_query(query, (server_id,))
/app/backend/modules/comercial/repository.py:248:        logging.warning(f"Error obteniendo config de sucursales para {server_id}: {e}")
/app/backend/modules/comercial/repository.py:252:async def filtrar_unidades_por_visibilidad(unidades: List[Dict], server_id: str) -> List[Dict]:
/app/backend/modules/comercial/repository.py:260:    config = await get_sucursales_visibles_config(server_id)
/app/backend/modules/comercial/repository.py:283:def _get_sucursal_nombre_sql(server_id: str, sucursal_origen_id: str) -> Optional[str]:
/app/backend/modules/comercial/repository.py:296:            # Para SoftRestaurant sin código, buscar por server_id con sucursal_origen_id NULL
/app/backend/modules/comercial/repository.py:302:        WHERE server_id = '{server_id}'
/app/backend/modules/comercial/repository.py:306:        results = execute_sql_query(
/app/backend/modules/comercial/repository.py:316:            logging.info(f"[EDARSAHUB] Unidad encontrada: {nombre} (server: {server_id[:8]}..., suc: {sucursal_origen_id or 'NULL'})")
/app/backend/modules/comercial/repository.py:324:async def get_sucursal_nombre(server_id: str, sucursal_origen_id: str, server_name: str = "") -> tuple:
/app/backend/modules/comercial/repository.py:333:    nombre = _get_sucursal_nombre_sql(server_id, sucursal_origen_id)
/app/backend/modules/comercial/repository.py:355:            'server_id': server.get('id', '')
/app/backend/modules/comercial/repository.py:384:    return execute_sql_query(
/app/backend/modules/comercial/repository.py:413:    return execute_sql_query(
/app/backend/modules/comercial/repository.py:448:    return execute_sql_query(
/app/backend/modules/comercial/repository.py:458:async def get_metas_sucursal(server_id: str, sucursal: str, mes: int, anio: int) -> Optional[Dict]:
/app/backend/modules/comercial/repository.py:464:        SELECT ServerID as server_id, Sucursal as sucursal, Mes as mes, Anio as anio,
/app/backend/modules/comercial/repository.py:470:    result = execute_hub_query_single(query, (server_id, sucursal, mes, anio))
/app/backend/modules/comercial/repository.py:474:async def save_metas_sucursal(server_id: str, sucursal: str, mes: int, anio: int, metas: Dict) -> None:
/app/backend/modules/comercial/repository.py:484:    exists = execute_hub_query_single(check_query, (server_id, sucursal, mes, anio))
/app/backend/modules/comercial/repository.py:497:            server_id, sucursal, mes, anio
/app/backend/modules/comercial/repository.py:506:            server_id, sucursal, mes, anio,
/app/backend/modules/comercial/repository.py:516:async def get_cached_kpis(server_id: str, periodo_key: str) -> Optional[Dict]:
/app/backend/modules/comercial/repository.py:519:        SELECT ServerID as server_id, PeriodoKey as periodo_key, KPIsJSON as kpis,
/app/backend/modules/comercial/repository.py:524:    result = execute_hub_query_single(query, (server_id, periodo_key))
/app/backend/modules/comercial/repository.py:533:async def save_kpis_cache(server_id: str, periodo_key: str, kpis: dict) -> None:
/app/backend/modules/comercial/repository.py:542:    exists = execute_hub_query_single(check_query, (server_id, periodo_key))
/app/backend/modules/comercial/repository.py:550:        execute_hub_insert(update_query, (kpis_json, server_id, periodo_key))
/app/backend/modules/comercial/repository.py:556:        execute_hub_insert(insert_query, (server_id, periodo_key, kpis_json))
/app/backend/modules/comercial/repository.py:559:async def get_cached_kpis_by_prefix(server_id: str, periodo_prefix: str) -> List[Dict]:
/app/backend/modules/comercial/repository.py:562:        SELECT ServerID as server_id, PeriodoKey as periodo_key, KPIsJSON as kpis,
/app/backend/modules/comercial/repository.py:567:    results = execute_hub_query(query, (server_id, f"{periodo_prefix}%"))
/app/backend/modules/comercial/repository.py:577:async def save_server_connection_status(server_id: str, is_online: bool, response_time_ms: int = None) -> None:
/app/backend/modules/comercial/repository.py:584:    exists = execute_hub_query_single(check_query, (server_id,))
/app/backend/modules/comercial/repository.py:592:        execute_hub_insert(update_query, (1 if is_online else 0, response_time_ms, server_id))
/app/backend/modules/comercial/repository.py:598:        execute_hub_insert(insert_query, (server_id, 1 if is_online else 0, response_time_ms))
/app/backend/modules/comercial/repository.py:601:async def get_server_connection_status(server_id: str) -> Optional[Dict]:
/app/backend/modules/comercial/repository.py:604:        SELECT ServerID as server_id, IsOnline as is_online, ResponseTimeMs as response_time_ms,
/app/backend/modules/comercial/repository.py:609:    result = execute_hub_query_single(query, (server_id,))
/app/backend/modules/comercial/repository.py:619:async def is_server_recently_offline(server_id: str, minutes_threshold: int = 10) -> bool:
/app/backend/modules/comercial/repository.py:632:    status = await get_server_connection_status(server_id)
/app/backend/modules/comercial/repository.py:663:async def should_attempt_live_query(server_id: str, data_type: str = "HUB") -> bool:
/app/backend/modules/comercial/repository.py:668:        server_id: ID del servidor
/app/backend/modules/comercial/repository.py:684:        return not await is_server_recently_offline(server_id, minutes_threshold=2)
/app/backend/modules/comercial/repository.py:687:    return not await is_server_recently_offline(server_id, minutes_threshold=10)
/app/backend/modules/comercial/repository.py:694:async def save_dashboard_cache(server_id: str, periodo_key: str, dashboard_data: Dict) -> None:
/app/backend/modules/comercial/repository.py:703:    exists = execute_hub_query_single(check_query, (server_id, periodo_key))
/app/backend/modules/comercial/repository.py:711:        execute_hub_insert(update_query, (data_json, server_id, periodo_key))
/app/backend/modules/comercial/repository.py:717:        execute_hub_insert(insert_query, (server_id, periodo_key, data_json))
/app/backend/modules/comercial/repository.py:720:async def get_dashboard_cache(server_id: str, periodo_key: str) -> Optional[Dict]:
/app/backend/modules/comercial/repository.py:723:        SELECT ServerID as server_id, PeriodoKey as periodo_key, DataJSON as data, UpdatedAt as updated_at
/app/backend/modules/comercial/repository.py:727:    result = execute_hub_query_single(query, (server_id, periodo_key))
/app/backend/modules/comercial/repository.py:764:    'get_server_connection_status',
/app/backend/modules/comercial/historical_kpis_repository.py:31:from core.db import execute_sql_query
/app/backend/modules/comercial/historical_kpis_repository.py:41:EDARSAHUB_SERVER_ID = "f8a9049a-96e8-4210-84ae-595ffa2822fa"
/app/backend/modules/comercial/historical_kpis_repository.py:62:    server = await db.servers.find_one({'id': EDARSAHUB_SERVER_ID})
/app/backend/modules/comercial/historical_kpis_repository.py:66:        raise RuntimeError(f"Servidor EDARSAHUB ({EDARSAHUB_SERVER_ID}) no encontrado")
/app/backend/modules/comercial/historical_kpis_repository.py:95:    return execute_sql_query(
/app/backend/modules/comercial/historical_kpis_repository.py:182:    server_id = record.get('server_id')
/app/backend/modules/comercial/historical_kpis_repository.py:189:    if not all([server_id, fecha]):
/app/backend/modules/comercial/historical_kpis_repository.py:190:        return {'action': 'SKIP', 'error': 'Campos obligatorios faltantes (server_id, fecha)'}
/app/backend/modules/comercial/historical_kpis_repository.py:228:        WHERE server_id = {_escape_sql_string(server_id)}
/app/backend/modules/comercial/historical_kpis_repository.py:270:            WHERE server_id = {_escape_sql_string(server_id)}
/app/backend/modules/comercial/historical_kpis_repository.py:279:            logger.info(f"[HISTORICAL_KPI_SQL] UPDATE: server={server_id}, suc={sucursal_id}, fecha={fecha}")
/app/backend/modules/comercial/historical_kpis_repository.py:291:                run_id, server_id, sucursal_id, sucursal_nombre,
/app/backend/modules/comercial/historical_kpis_repository.py:299:                {_escape_sql_string(server_id)},
/app/backend/modules/comercial/historical_kpis_repository.py:324:            logger.info(f"[HISTORICAL_KPI_SQL] INSERT: server={server_id}, suc={sucursal_id}, fecha={fecha}")
/app/backend/modules/comercial/historical_kpis_repository.py:380:    server_id: str,
/app/backend/modules/comercial/historical_kpis_repository.py:391:    conditions = [f"server_id = {_escape_sql_string(server_id)}"]
/app/backend/modules/comercial/historical_kpis_repository.py:403:    SELECT server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo, source_hash
/app/backend/modules/comercial/historical_kpis_repository.py:434:    server_id: str = None,
/app/backend/modules/comercial/historical_kpis_repository.py:444:    if server_id:
/app/backend/modules/comercial/historical_kpis_repository.py:445:        conditions.append(f"server_id = {_escape_sql_string(server_id)}")
/app/backend/modules/comercial/historical_kpis_repository.py:455:        server_id,
/app/backend/modules/comercial/historical_kpis_repository.py:463:    GROUP BY server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo
/app/backend/modules/comercial/historical_kpis_repository.py:525:                'server_id': doc.get('server_id'),
/app/backend/modules/comercial/historical_kpis_repository.py:543:                    'server_id': record['server_id'],
/app/backend/modules/comercial/kpis_repository.py:31:def init_kpis_repository(database=None) -> None:
/app/backend/modules/comercial/kpis_repository.py:146:def _build_filter_key(server_id: str, empresa_id: str, sucursal_id: str, fecha: str) -> dict:
/app/backend/modules/comercial/kpis_repository.py:149:        "server_id": server_id,
/app/backend/modules/comercial/kpis_repository.py:166:    server_id: str,
/app/backend/modules/comercial/kpis_repository.py:187:        server_id: UUID del servidor origen
/app/backend/modules/comercial/kpis_repository.py:207:    filter_key = _build_filter_key(server_id, empresa_id, sucursal_id, fecha)
/app/backend/modules/comercial/kpis_repository.py:367:    server_id: str,
/app/backend/modules/comercial/kpis_repository.py:379:        server_id, empresa_id, sucursal_id, fecha: Clave del documento
/app/backend/modules/comercial/kpis_repository.py:388:    filter_key = _build_filter_key(server_id, empresa_id, sucursal_id, fecha)
/app/backend/modules/comercial/kpis_repository.py:428:    server_id: str,
/app/backend/modules/comercial/kpis_repository.py:435:    filter_key = _build_filter_key(server_id, empresa_id, sucursal_id, fecha)
/app/backend/modules/comercial/kpis_repository.py:465:    server_id: str,
/app/backend/modules/comercial/kpis_repository.py:476:        "server_id": server_id,
/app/backend/modules/comercial/services/impuestos_service.py:22:from core.db import execute_sql_query
/app/backend/modules/comercial/services/impuestos_service.py:82:    server_id: str,
/app/backend/modules/comercial/services/impuestos_service.py:103:        server_id: UUID del servidor origen
/app/backend/modules/comercial/services/impuestos_service.py:129:          (TipoOverride = 'PRODUCTO' AND CodigoProducto = '{codigo_producto}' AND ServerID = '{server_id}')
/app/backend/modules/comercial/services/impuestos_service.py:152:    override_result = execute_sql_query(*conn, override_query)
/app/backend/modules/comercial/services/impuestos_service.py:178:    WHERE ServerID = '{server_id}'
/app/backend/modules/comercial/services/impuestos_service.py:182:    producto_result = execute_sql_query(*conn, producto_query)
/app/backend/modules/comercial/services/impuestos_service.py:221:    WHERE ServerID = '{server_id}'
/app/backend/modules/comercial/services/impuestos_service.py:225:    sync_result = execute_sql_query(*conn, sync_query)
/app/backend/modules/comercial/services/impuestos_service.py:259:def get_estado_fiscal_producto(codigo_producto: str, server_id: str) -> Dict[str, Any]:
/app/backend/modules/comercial/services/impuestos_service.py:282:    WHERE m.ServerID = '{server_id}'
/app/backend/modules/comercial/services/impuestos_service.py:286:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/impuestos_service.py:313:def get_productos_sin_impuesto(server_id: Optional[str] = None, limit: int = 100) -> list:
/app/backend/modules/comercial/services/impuestos_service.py:322:    if server_id:
/app/backend/modules/comercial/services/impuestos_service.py:323:        where_clause += f" AND m.ServerID = '{server_id}'"
/app/backend/modules/comercial/services/impuestos_service.py:339:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/impuestos_service.py:346:            'server_id': r['ServerID'],
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
/app/backend/modules/comercial/services/benchmark_service.py:59:        server_id=str(row.get('ServerID', '')),
/app/backend/modules/comercial/services/benchmark_service.py:121:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/services/benchmark_service.py:158:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/benchmark_service.py:201:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/benchmark_service.py:211:    server_id: str
/app/backend/modules/comercial/services/benchmark_service.py:246:      AND b.ServerID = '{server_id}'
/app/backend/modules/comercial/services/benchmark_service.py:251:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/benchmark_service.py:289:        '{data.server_id}',
/app/backend/modules/comercial/services/benchmark_service.py:304:    execute_sql_query(*conn, insert_query)
/app/backend/modules/comercial/services/benchmark_service.py:352:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/benchmark_service.py:374:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/benchmark_service.py:394:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/benchmark_service.py:430:    result_benchmark = execute_sql_query(*conn, query_benchmark)
/app/backend/modules/comercial/services/benchmark_service.py:444:    JOIN Sistema_EmpresasServidores ses ON sp.ServerID = ses.server_id
/app/backend/modules/comercial/services/benchmark_service.py:449:    result_productos = execute_sql_query(*conn, query_productos)
/app/backend/modules/comercial/services/benchmark_service.py:523:    result = execute_sql_query(*conn, query_validados)
/app/backend/modules/comercial/services/benchmark_service.py:571:    result_menu = execute_sql_query(*conn, query_con_menu)
/app/backend/modules/comercial/services/benchmark_service.py:615:    server_id: str
/app/backend/modules/comercial/services/benchmark_service.py:622:    benchmarks = obtener_benchmarks_producto(codigo_producto, server_id)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:21:from core.db import execute_sql_query
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:75:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:112:    server_id: str = None,
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:151:    if server_id:
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:152:        where_clauses.append(f"p.ServerID = '{server_id}'")
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:208:        p.ServerID as server_id,
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:225:    productos_raw = execute_sql_query(*conn, query) or []
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:226:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:328:            'server_id': p.get('server_id'),
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:376:    rangos = execute_sql_query(*conn, query) or []
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:433:    regla = execute_sql_query(*conn, query_regla)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:451:    traslape = execute_sql_query(*conn, query_traslape)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:472:        execute_sql_query(*conn, insert_query)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:504:    rango = execute_sql_query(*conn, query_existe)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:537:        traslape = execute_sql_query(*conn, query_traslape)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:570:        execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/pricing_ai_service.py:33:from core.db import execute_sql_query
/app/backend/modules/comercial/services/pricing_ai_service.py:151:        execute_sql_query(*conn, ddl)
/app/backend/modules/comercial/services/pricing_ai_service.py:161:def _obtener_datos_producto(codigo_producto: str, server_id: str) -> Dict[str, Any]:
/app/backend/modules/comercial/services/pricing_ai_service.py:181:    WHERE CAST(sp.ServerID AS NVARCHAR(36)) = '{server_id}'
/app/backend/modules/comercial/services/pricing_ai_service.py:185:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/pricing_ai_service.py:365:    server_id: str,
/app/backend/modules/comercial/services/pricing_ai_service.py:451:        '{server_id}',
/app/backend/modules/comercial/services/pricing_ai_service.py:478:        execute_sql_query(*conn, insert_query)
/app/backend/modules/comercial/services/pricing_ai_service.py:525:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/pricing_ai_service.py:566:        'server_id': row.get('ServerID'),
/app/backend/modules/comercial/services/pricing_ai_service.py:597:    server_id: str,
/app/backend/modules/comercial/services/pricing_ai_service.py:651:    datos_producto = _obtener_datos_producto(codigo_producto, server_id)
/app/backend/modules/comercial/services/pricing_ai_service.py:666:    benchmark = obtener_precios_competencia_producto(codigo_producto, server_id)
/app/backend/modules/comercial/services/pricing_ai_service.py:671:        server_id=server_id,
/app/backend/modules/comercial/services/pricing_ai_service.py:824:            server_id=server_id,
/app/backend/modules/comercial/services/pricing_ai_service.py:879:            server_id=server_id,
/app/backend/modules/comercial/services/pricing_ai_service.py:913:    server_id: str,
/app/backend/modules/comercial/services/pricing_ai_service.py:927:    datos_producto = _obtener_datos_producto(codigo_producto, server_id)
/app/backend/modules/comercial/services/pricing_ai_service.py:1029:            server_id=server_id,
/app/backend/modules/comercial/services/pricing_ai_service.py:1081:    server_id: str,
/app/backend/modules/comercial/services/pricing_ai_service.py:1095:    datos_producto = _obtener_datos_producto(codigo_producto, server_id)
/app/backend/modules/comercial/services/pricing_ai_service.py:1105:    benchmark = obtener_precios_competencia_producto(codigo_producto, server_id)
/app/backend/modules/comercial/services/pricing_ai_service.py:1181:            server_id=server_id,
/app/backend/modules/comercial/services/pricing_ai_service.py:1400:            server_id='',
/app/backend/modules/comercial/services/perfil_unidad_service.py:20:from core.db import execute_sql_query
/app/backend/modules/comercial/services/perfil_unidad_service.py:49:        server_id=str(row.get('ServerID', '')) if row.get('ServerID') else None,
/app/backend/modules/comercial/services/perfil_unidad_service.py:115:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:159:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:210:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:261:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:285:    check_result = execute_sql_query(*conn, check_query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:294:    server_id_sql = f"'{data.server_id}'" if data.server_id else "NULL"
/app/backend/modules/comercial/services/perfil_unidad_service.py:356:        {server_id_sql},
/app/backend/modules/comercial/services/perfil_unidad_service.py:385:    execute_sql_query(*conn, insert_query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:476:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:496:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:27:from core.db import execute_sql_query
/app/backend/modules/comercial/services/pricing_sugerido_service.py:75:def _obtener_costo_producto(codigo_producto: str, server_id: str) -> Tuple[Optional[float], Optional[str]]:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:95:    WHERE ServerID = '{server_id}'
/app/backend/modules/comercial/services/pricing_sugerido_service.py:99:    result = execute_sql_query(*conn, query_receta)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:114:    WHERE ServerID = '{server_id}'
/app/backend/modules/comercial/services/pricing_sugerido_service.py:118:    result_insumos = execute_sql_query(*conn, query_insumos)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:138:def _obtener_nombre_producto(codigo_producto: str, server_id: str) -> Optional[str]:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:145:    WHERE ServerID = '{server_id}'
/app/backend/modules/comercial/services/pricing_sugerido_service.py:149:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:157:def _es_producto_vino(codigo_producto: str, server_id: str) -> bool:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:173:    WHERE ServerID = '{server_id}'
/app/backend/modules/comercial/services/pricing_sugerido_service.py:178:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:240:    nombre_producto = _obtener_nombre_producto(request.codigo_producto, request.server_id)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:247:        server_id=request.server_id,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:261:            if not _es_producto_vino(request.codigo_producto, request.server_id):
/app/backend/modules/comercial/services/pricing_sugerido_service.py:269:                request.server_id,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:302:            costo, fuente_costo = _obtener_costo_producto(request.codigo_producto, request.server_id)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:324:                server_id=request.server_id
/app/backend/modules/comercial/services/pricing_sugerido_service.py:375:                request.server_id
/app/backend/modules/comercial/services/pricing_sugerido_service.py:412:            costo, fuente_costo = _obtener_costo_producto(request.codigo_producto, request.server_id)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:428:                server_id=request.server_id
/app/backend/modules/comercial/services/pricing_sugerido_service.py:443:                request.server_id
/app/backend/modules/comercial/services/pricing_sugerido_service.py:498:    server_id: str,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:509:        server_id: UUID del servidor
/app/backend/modules/comercial/services/pricing_sugerido_service.py:522:    where_clauses = [f"ServerID = '{server_id}'"]
/app/backend/modules/comercial/services/pricing_sugerido_service.py:541:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:550:            server_id=server_id,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:561:def obtener_estadisticas_calculo(server_id: str, tipo_motor: TipoMotorPrecio = TipoMotorPrecio.COSTO_MARGEN) -> Dict[str, Any]:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:570:        server_id=server_id,
/app/backend/modules/comercial/services/metricas_ia_service.py:25:from core.db import execute_sql_query
/app/backend/modules/comercial/services/metricas_ia_service.py:105:        result = execute_sql_query(*conn, query_totales)
/app/backend/modules/comercial/services/metricas_ia_service.py:140:        result = execute_sql_query(*conn, query_por_dia)
/app/backend/modules/comercial/services/metricas_ia_service.py:163:        result = execute_sql_query(*conn, query_productos)
/app/backend/modules/comercial/services/metricas_ia_service.py:185:        result = execute_sql_query(*conn, query_competidores)
/app/backend/modules/comercial/services/metricas_ia_service.py:220:        result = execute_sql_query(*conn, query_ultimos)
/app/backend/modules/comercial/services/metricas_ia_service.py:251:        result = execute_sql_query(*conn, query_promedios)
/app/backend/modules/comercial/services/metricas_ia_service.py:274:        result = execute_sql_query(*conn, query_tipos)
/app/backend/modules/comercial/services/metricas_ia_service.py:324:        result = execute_sql_query(*conn, query_comp)
/app/backend/modules/comercial/services/metricas_ia_service.py:344:        result = execute_sql_query(*conn, query_items)
/app/backend/modules/comercial/services/precios_vinos_service.py:50:from core.db import execute_sql_query
/app/backend/modules/comercial/services/precios_vinos_service.py:79:    server_id: str
/app/backend/modules/comercial/services/precios_vinos_service.py:110:            'server_id': self.server_id,
/app/backend/modules/comercial/services/precios_vinos_service.py:229:def obtener_costo_base_vino(codigo_producto: str, server_id: str) -> Tuple[Optional[float], Optional[str]]:
/app/backend/modules/comercial/services/precios_vinos_service.py:254:    WHERE sp.ServerID = '{server_id}'
/app/backend/modules/comercial/services/precios_vinos_service.py:258:    result_cr = execute_sql_query(*conn, query_costo_receta)
/app/backend/modules/comercial/services/precios_vinos_service.py:274:    WHERE i.ServerID = '{server_id}'
/app/backend/modules/comercial/services/precios_vinos_service.py:278:    result_insumos = execute_sql_query(*conn, query_insumos)
/app/backend/modules/comercial/services/precios_vinos_service.py:326:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/precios_vinos_service.py:334:def obtener_tasa_impuesto(codigo_producto: str, server_id: str) -> Tuple[Optional[float], Optional[str]]:
/app/backend/modules/comercial/services/precios_vinos_service.py:349:    WHERE m.ServerID = '{server_id}'
/app/backend/modules/comercial/services/precios_vinos_service.py:353:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/precios_vinos_service.py:389:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/precios_vinos_service.py:399:    server_id: str,
/app/backend/modules/comercial/services/precios_vinos_service.py:423:        server_id: UUID del servidor
/app/backend/modules/comercial/services/precios_vinos_service.py:433:        server_id=server_id,
/app/backend/modules/comercial/services/precios_vinos_service.py:463:        costo, fuente = obtener_costo_base_vino(codigo_producto, server_id)
/app/backend/modules/comercial/services/precios_vinos_service.py:485:        tasa, mapeo_id = obtener_tasa_impuesto(codigo_producto, server_id)
/app/backend/modules/comercial/services/precios_vinos_service.py:529:    server_id: Optional[str] = None,
/app/backend/modules/comercial/services/precios_vinos_service.py:536:        server_id: Filtrar por servidor (opcional)
/app/backend/modules/comercial/services/precios_vinos_service.py:552:    where_server = f"AND sp.ServerID = '{server_id}'" if server_id else ""
/app/backend/modules/comercial/services/precios_vinos_service.py:567:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/precios_vinos_service.py:583:def get_estadisticas_calculo(server_id: Optional[str] = None) -> Dict[str, int]:
/app/backend/modules/comercial/services/precios_vinos_service.py:590:    resultados = calcular_precios_vinos_masivo(server_id, limit=2000)
/app/backend/modules/comercial/services/pricing_schemas.py:152:    server_id: Optional[str] = Field(None, description="UUID del servidor")
/app/backend/modules/comercial/services/pricing_schemas.py:188:    server_id: Optional[str] = None
/app/backend/modules/comercial/services/pricing_schemas.py:351:    server_id: str = Field(..., description="UUID del servidor")
/app/backend/modules/comercial/services/pricing_schemas.py:410:    server_id: str = Field(..., description="UUID del servidor")
/app/backend/modules/comercial/services/pricing_schemas.py:444:    server_id: str
/app/backend/modules/comercial/routes.py:13:║ - GET /comercial/dashboard/{server_id}                                     ║
/app/backend/modules/comercial/routes.py:14:║ - GET /comercial/sucursales/{server_id}                                    ║
/app/backend/modules/comercial/routes.py:15:║ - GET /comercial/metas/{server_id}                                         ║
/app/backend/modules/comercial/routes.py:52:   - GET /comercial/sucursales/{server_id} (Fase 5B-4A)
/app/backend/modules/comercial/routes.py:53:   - GET /comercial/metas/{server_id} (Fase 5B-4A)
/app/backend/modules/comercial/routes.py:54:   - GET /comercial/ticket-perfecto/{server_id} (Fase 5B-4C)
/app/backend/modules/comercial/routes.py:55:   - GET /comercial/ventas-tiempo/{server_id} (Fase 5B-4C)
/app/backend/modules/comercial/routes.py:56:   - GET /comercial/mesas/{server_id} (Fase 5B-4E)
/app/backend/modules/comercial/routes.py:57:   - GET /comercial/detalle-movimientos/{server_id} (Fase 5B-4E)
/app/backend/modules/comercial/routes.py:58:   - GET /comercial/precios-constantes/{server_id} (Fase 5B-4G)
/app/backend/modules/comercial/routes.py:59:   - GET /comercial/reporte-pax/{server_id} (Fase 5B-4H)
/app/backend/modules/comercial/routes.py:60:   - GET /comercial/dashboard/{server_id} (Fase 5B-5B)
/app/backend/modules/comercial/routes.py:72:from core.db import execute_sql_query
/app/backend/modules/comercial/routes.py:91:    execute_sql_query_params  # FASE SQL-SAFE: Queries parametrizadas
/app/backend/modules/comercial/routes.py:127:    get_server_connection_status,
/app/backend/modules/comercial/routes.py:183:# - /comercial/sucursales/{server_id} - Requiere: Sistema_Sucursales
/app/backend/modules/comercial/routes.py:184:# - /comercial/metas/{server_id} - Requiere: Sync_Metas_Comerciales (no existe)
/app/backend/modules/comercial/routes.py:185:# - /comercial/ticket-perfecto/{server_id} - Requiere: Sync_Ticket_Perfecto (no existe)
/app/backend/modules/comercial/routes.py:186:# - /comercial/mesas/{server_id} - Requiere: Sync_Mesas (no existe)
/app/backend/modules/comercial/routes.py:187:# - /comercial/detalle-movimientos/{server_id} - Requiere: tabla de detalle
/app/backend/modules/comercial/routes.py:188:# - /comercial/precios-constantes/{server_id} - Requiere: tablas de precios
/app/backend/modules/comercial/routes.py:189:# - /comercial/reporte-pax/{server_id} - Requiere: Sync_PAX (no existe)
/app/backend/modules/comercial/routes.py:192:# - /comercial/dashboard/{server_id} - Usa EDARSAHUB vía get_dashboard_kpis_from_edarsahub
/app/backend/modules/comercial/routes.py:193:# - /comercial/ventas-tiempo/{server_id} - Usa Sync_Ventas_PorHora
/app/backend/modules/comercial/routes.py:229:def check_live_guard_rail(endpoint_base: str, server_id: str = None) -> dict:
/app/backend/modules/comercial/routes.py:234:        endpoint_base: Ruta base del endpoint (sin server_id)
/app/backend/modules/comercial/routes.py:235:        server_id: ID del servidor solicitado
/app/backend/modules/comercial/routes.py:247:                f"[LIVE-GUARD-RAIL] Endpoint bloqueado: {endpoint_base}/{server_id} - "
/app/backend/modules/comercial/routes.py:258:                "server_id": server_id,
/app/backend/modules/comercial/routes.py:299:async def validate_server_access_rbac(current_user: Dict, server_id: str) -> UserAccessContext:
/app/backend/modules/comercial/routes.py:308:        server_id: ID del servidor a validar
/app/backend/modules/comercial/routes.py:320:    if has_server_access(context, server_id):
/app/backend/modules/comercial/routes.py:326:        f"sin acceso a servidor {server_id}. "
/app/backend/modules/comercial/routes.py:338:    Para endpoints que no requieren un server_id específico.
/app/backend/modules/comercial/routes.py:368:def get_ventas_dia_snapshot_from_edarsahub(server_id: str, fecha_operacion: str = None, unidad_negocio_id: str = None) -> Dict:
/app/backend/modules/comercial/routes.py:377:        server_id: ID del servidor
/app/backend/modules/comercial/routes.py:428:                f"[EDARSAHUB-SNAPSHOT] server_id={server_id}: FechaOperacion default = {fecha_operacion} "
/app/backend/modules/comercial/routes.py:437:        server_id,
/app/backend/modules/comercial/routes.py:451:    WHERE server_id = '{server_id}'
/app/backend/modules/comercial/routes.py:457:        result = execute_sql_query(
/app/backend/modules/comercial/routes.py:467:            logging.info(f"[EDARSAHUB-FALLBACK] Sin snapshot para server_id={server_id}, fecha={fecha_operacion}")
/app/backend/modules/comercial/routes.py:511:            f"[EDARSAHUB-FALLBACK] Snapshot encontrado para server_id={server_id}: "
/app/backend/modules/comercial/routes.py:903:                                    from core.unidades_registry import get_unidad_by_server_id
/app/backend/modules/comercial/routes.py:904:                                    unidad_info = get_unidad_by_server_id(server['id'])
/app/backend/modules/comercial/routes.py:925:                                # Criterio 1: Match por server_id exacto
/app/backend/modules/comercial/routes.py:926:                                if vd.get('server_id') == server['id']:
/app/backend/modules/comercial/routes.py:1016:                    logging.info(f"[P0-LOG] tablero_real_source_success: server={server['name']}, ventas={kpis.get('ventas', 0)}, source={source_period}, data_type={data_type}")
/app/backend/modules/comercial/routes.py:1019:                        server=server,
/app/backend/modules/comercial/routes.py:1051:                    logging.warning(f"[P0-LOG] tablero_real_source_query_error: server={server['name']}, error={error_code}")
/app/backend/modules/comercial/routes.py:1055:                        server=server,
/app/backend/modules/comercial/routes.py:1074:                    logging.warning(f"[P0-LOG] tablero_real_source_connection_error: server={server['name']}, live_status={live_status}")
/app/backend/modules/comercial/routes.py:1120:                                server=server,
/app/backend/modules/comercial/routes.py:1147:                                server=server,
/app/backend/modules/comercial/routes.py:1174:                                server=server,
/app/backend/modules/comercial/routes.py:1193:                                logging.info(f"[P0-LOG] tablero_cache_used_connection_fallback: server={server['name']}")
/app/backend/modules/comercial/routes.py:1196:                                    server=server,
/app/backend/modules/comercial/routes.py:1217:                                    server=server,
/app/backend/modules/comercial/routes.py:1234:                    logging.info(f"[P0-LOG] tablero_cache_lookup: server={server['name']}, reason=server_offline")
/app/backend/modules/comercial/routes.py:1241:                            server=server,
/app/backend/modules/comercial/routes.py:1260:                            server=server,
/app/backend/modules/comercial/routes.py:1276:                    logging.warning(f"[P0-LOG] tablero_real_source_connection_error: server={server['name']}, silent_fail=True")
/app/backend/modules/comercial/routes.py:1309:                                server=server,
/app/backend/modules/comercial/routes.py:1330:                                server=server,
/app/backend/modules/comercial/routes.py:1351:                                server=server,
/app/backend/modules/comercial/routes.py:1370:                                server=server,
/app/backend/modules/comercial/routes.py:1454:                                server=server, kpis=kpis_mpro,
/app/backend/modules/comercial/routes.py:1474:                                server=server, kpis={'ventas': 0, 'pax': 0, 'cheques': 0},
/app/backend/modules/comercial/routes.py:1490:                            server=server, kpis=None,
/app/backend/modules/comercial/routes.py:1519:                                    server=server,
/app/backend/modules/comercial/routes.py:1544:                                    server=server, kpis=unidad,
/app/backend/modules/comercial/routes.py:1574:                                server=server, kpis=None,
/app/backend/modules/comercial/routes.py:1594:                                        server=server, kpis=cached_kpi,
/app/backend/modules/comercial/routes.py:1612:                                    server=server, kpis=None,
/app/backend/modules/comercial/routes.py:1629:            logging.error(f"[P0-LOG] tablero_server_error: server={server.get('name', 'UNKNOWN')}, error={server_error}")
/app/backend/modules/comercial/routes.py:1635:                server=server,
/app/backend/modules/comercial/routes.py:1677:    # Construir mapa de server_id → codigo para resolver entradas con código vacío
/app/backend/modules/comercial/routes.py:1683:            sid = u.get('server_id', '')
/app/backend/modules/comercial/routes.py:1687:            # Para MPRO: usar server_id + sucursal_origen_id (ya corregido en P0)
/app/backend/modules/comercial/routes.py:1700:        2. Resolver desde EDARSAHUB por server_id (SoftRestaurant)
/app/backend/modules/comercial/routes.py:1701:        3. Fallback defensivo: UNKNOWN:{server_id}
/app/backend/modules/comercial/routes.py:1707:        # Intentar resolver por server_id desde EDARSAHUB
/app/backend/modules/comercial/routes.py:1708:        server_id = unidad.get('server_id', '')
/app/backend/modules/comercial/routes.py:1709:        if server_id and server_id in server_to_codigo_map:
/app/backend/modules/comercial/routes.py:1710:            codigo_resuelto = server_to_codigo_map[server_id]
/app/backend/modules/comercial/routes.py:1711:            logging.info(f"[P1-DEDUP] Código resuelto via EDARSAHUB: server_id={server_id[:8]}... → {codigo_resuelto}")
/app/backend/modules/comercial/routes.py:1715:        logging.warning(f"[P1-DEDUP] No se pudo resolver código para server_id={server_id[:8]}...")
/app/backend/modules/comercial/routes.py:1716:        return f"UNKNOWN:{server_id}" if server_id else "UNKNOWN"
/app/backend/modules/comercial/routes.py:1777:                uid = r.get('unidad_negocio_id') or r.get('server_id')
/app/backend/modules/comercial/routes.py:1788:                sid = snapshot.get('server_id', '')
/app/backend/modules/comercial/routes.py:1806:                    'server_id': sid,
/app/backend/modules/comercial/routes.py:1913:@router.get("/comercial/sucursales/{server_id}")
/app/backend/modules/comercial/routes.py:1915:    server_id: str,
/app/backend/modules/comercial/routes.py:1927:    server = await get_server_by_id(server_id)
/app/backend/modules/comercial/routes.py:1932:    await validate_server_access_rbac(current_user, server_id)
/app/backend/modules/comercial/routes.py:1955:        WHERE CAST(sm.ServidorID AS VARCHAR(50)) = '{server_id}'
/app/backend/modules/comercial/routes.py:1961:        result = execute_sql_query(
/app/backend/modules/comercial/routes.py:2014:@router.get("/comercial/metas/{server_id}")
/app/backend/modules/comercial/routes.py:2016:    server_id: str, 
/app/backend/modules/comercial/routes.py:2030:    server = await get_server_by_id(server_id)
/app/backend/modules/comercial/routes.py:2039:    await validate_server_access_rbac(current_user, server_id)
/app/backend/modules/comercial/routes.py:2045:            server='<REDACTED_EDARSAHUB_SQL_HOST>', port=1433, database='EDARSAHUB',
/app/backend/modules/comercial/routes.py:2059:            """, (server_id, sucursal, anio, mes))
/app/backend/modules/comercial/routes.py:2065:            """, (server_id, anio, mes))
/app/backend/modules/comercial/routes.py:2114:        server_id=server_id,
/app/backend/modules/comercial/routes.py:2160:            result_prod = execute_sql_query(
/app/backend/modules/comercial/routes.py:2192:            result_vend = execute_sql_query(
/app/backend/modules/comercial/routes.py:2245:            result_prod = execute_sql_query(
/app/backend/modules/comercial/routes.py:2278:            result_vend = execute_sql_query(
/app/backend/modules/comercial/routes.py:2349:@router.get("/comercial/ticket-perfecto/{server_id}")
/app/backend/modules/comercial/routes.py:2351:    server_id: str, 
/app/backend/modules/comercial/routes.py:2367:    server = await get_server_by_id(server_id)
/app/backend/modules/comercial/routes.py:2376:    await validate_server_access_rbac(current_user, server_id)
/app/backend/modules/comercial/routes.py:2382:            server='<REDACTED_EDARSAHUB_SQL_HOST>', port=1433, database='EDARSAHUB',
/app/backend/modules/comercial/routes.py:2405:            """, (server_id, sucursal, f_inicio, f_fin))
/app/backend/modules/comercial/routes.py:2411:            """, (server_id, f_inicio, f_fin))
/app/backend/modules/comercial/routes.py:2460:        server_id=server_id,
/app/backend/modules/comercial/routes.py:2505:                result = execute_sql_query(
/app/backend/modules/comercial/routes.py:2543:                    result_simple = execute_sql_query(
/app/backend/modules/comercial/routes.py:2581:            result_rent = execute_sql_query(
/app/backend/modules/comercial/routes.py:2645:@router.get("/comercial/ventas-tiempo/{server_id}")
/app/backend/modules/comercial/routes.py:2647:    server_id: str, 
/app/backend/modules/comercial/routes.py:2657:    server = await get_server_by_id(server_id)
/app/backend/modules/comercial/routes.py:2662:    await validate_server_access_rbac(current_user, server_id)
/app/backend/modules/comercial/routes.py:2684:                server='<REDACTED_EDARSAHUB_SQL_HOST>',
/app/backend/modules/comercial/routes.py:2687:                database='EDARSAHUB',
/app/backend/modules/comercial/routes.py:2705:            """, (server_id, fecha_ini, fecha_fin))
/app/backend/modules/comercial/routes.py:2720:            """, (server_id, fecha_ini, fecha_fin))
/app/backend/modules/comercial/routes.py:2730:            """, (server_id,))
/app/backend/modules/comercial/routes.py:2792:                    server='<REDACTED_EDARSAHUB_SQL_HOST>',
/app/backend/modules/comercial/routes.py:2795:                    database='EDARSAHUB',
/app/backend/modules/comercial/routes.py:2807:                """, (server_id, hoy_str))
/app/backend/modules/comercial/routes.py:2869:@router.get("/comercial/mesas/{server_id}")
/app/backend/modules/comercial/routes.py:2871:    server_id: str, 
/app/backend/modules/comercial/routes.py:2886:    server = await get_server_by_id(server_id)
/app/backend/modules/comercial/routes.py:2895:    await validate_server_access_rbac(current_user, server_id)
/app/backend/modules/comercial/routes.py:2901:            server='<REDACTED_EDARSAHUB_SQL_HOST>', port=1433, database='EDARSAHUB',
/app/backend/modules/comercial/routes.py:2917:            """, (server_id, sucursal, fecha_op))
/app/backend/modules/comercial/routes.py:2923:            """, (server_id, fecha_op))
/app/backend/modules/comercial/routes.py:2985:    nombre_unidad_mostrar, nombre_source = await get_sucursal_nombre(server_id, sucursal, server['name'])
/app/backend/modules/comercial/routes.py:3022:            result = execute_sql_query(
/app/backend/modules/comercial/routes.py:3078:            result_rot = execute_sql_query(
/app/backend/modules/comercial/routes.py:3136:            result = execute_sql_query(
/app/backend/modules/comercial/routes.py:3169:                        result_nombre = execute_sql_query(
/app/backend/modules/comercial/routes.py:3209:            result_rotacion = execute_sql_query(
/app/backend/modules/comercial/routes.py:3241:@router.get("/comercial/detalle-movimientos/{server_id}")
/app/backend/modules/comercial/routes.py:3243:    server_id: str, 
/app/backend/modules/comercial/routes.py:3257:    server = await get_server_by_id(server_id)
/app/backend/modules/comercial/routes.py:3262:    await validate_server_access_rbac(current_user, server_id)
/app/backend/modules/comercial/routes.py:3265:    guard_result = check_live_guard_rail('/comercial/detalle-movimientos', server_id)
/app/backend/modules/comercial/routes.py:3347:            result = execute_sql_query(
/app/backend/modules/comercial/routes.py:3362:            result_total = execute_sql_query(
/app/backend/modules/comercial/routes.py:3442:            result = execute_sql_query(
/app/backend/modules/comercial/routes.py:3458:            result_total = execute_sql_query(
/app/backend/modules/comercial/routes.py:3500:@router.get("/comercial/precios-constantes/{server_id}")
/app/backend/modules/comercial/routes.py:3502:    server_id: str,
/app/backend/modules/comercial/routes.py:3515:    server = await get_server_by_id(server_id)
/app/backend/modules/comercial/routes.py:3520:    await validate_server_access_rbac(current_user, server_id)
/app/backend/modules/comercial/routes.py:3523:    guard_result = check_live_guard_rail('/comercial/precios-constantes', server_id)
/app/backend/modules/comercial/routes.py:3598:            result_ventas_reales = execute_sql_query(
/app/backend/modules/comercial/routes.py:3646:            ventas_actual = execute_sql_query(
/app/backend/modules/comercial/routes.py:3651:            precios_base = execute_sql_query(
/app/backend/modules/comercial/routes.py:3745:                    info_result = execute_sql_query_params(
/app/backend/modules/comercial/routes.py:3884:            result_ventas_reales = execute_sql_query(
/app/backend/modules/comercial/routes.py:3924:            ventas_actual = execute_sql_query(
/app/backend/modules/comercial/routes.py:3929:            precios_base = execute_sql_query(
/app/backend/modules/comercial/routes.py:4097:@router.get("/comercial/reporte-pax/{server_id}")
/app/backend/modules/comercial/routes.py:4099:    server_id: str, 
/app/backend/modules/comercial/routes.py:4115:    server = await get_server_by_id(server_id)
/app/backend/modules/comercial/routes.py:4124:    await validate_server_access_rbac(current_user, server_id)
/app/backend/modules/comercial/routes.py:4130:            server='<REDACTED_EDARSAHUB_SQL_HOST>', port=1433, database='EDARSAHUB',
/app/backend/modules/comercial/routes.py:4153:            """, (server_id, sucursal, f_inicio, f_fin))
/app/backend/modules/comercial/routes.py:4159:            """, (server_id, f_inicio, f_fin))
/app/backend/modules/comercial/routes.py:4223:@router.get("/comercial/dashboard/{server_id}")
/app/backend/modules/comercial/routes.py:4225:    server_id: str, 
/app/backend/modules/comercial/routes.py:4245:    server = await get_server_by_id(server_id)
/app/backend/modules/comercial/routes.py:4256:    await validate_server_access_rbac(current_user, server_id)
/app/backend/modules/comercial/routes.py:4477:                server_id=server_id,
/app/backend/modules/comercial/routes.py:4533:            stale_snapshot = get_last_valid_snapshot_edarsahub(server_id)
/app/backend/modules/comercial/routes.py:4588:                server_id=server_id,
/app/backend/modules/comercial/routes.py:4644:            stale_snapshot_mpro = get_last_valid_snapshot_edarsahub(server_id)
/app/backend/modules/comercial/schemas.py:26:    server_id: Optional[str] = None
/app/backend/modules/comercial/schemas.py:69:    server_id: str
/app/backend/modules/fase2_operativo/sql_repository.py:42:        server=EDARSAHUB_CONFIG['host'],
/app/backend/modules/fase2_operativo/sql_repository.py:44:        database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/fase2_operativo/sql_repository.py:96:    server_id: str,
/app/backend/modules/fase2_operativo/sql_repository.py:116:    params = (server_id, sucursal_id or '', almacen_id, folio_final_key)
/app/backend/modules/fase2_operativo/sql_repository.py:124:    server_id: str,
/app/backend/modules/fase2_operativo/sql_repository.py:154:        server_id, server_name, sucursal_id or '', sucursal_nombre or '',
/app/backend/modules/fase2_operativo/sql_repository.py:195:            ServerID as server_id, ServerName as server_name,
/app/backend/modules/fase2_operativo/sql_repository.py:396:    server_id: str,
/app/backend/modules/fase2_operativo/sql_repository.py:420:        registro_id, server_id, server_name, sucursal_id or '', sucursal_nombre or '',
/app/backend/modules/fase2_operativo/sql_repository.py:519:async def obtener_config_asignacion(server_id: str, almacen_id: str) -> Optional[Dict]:
/app/backend/modules/fase2_operativo/sql_repository.py:526:            ConfigID as id, ServerID as server_id, AlmacenID as almacen_id,
/app/backend/modules/fase2_operativo/sql_repository.py:536:    params = (server_id, almacen_id, almacen_id)
/app/backend/modules/fase2_operativo/repositories/auditoria_programada_repository.py:55:            "ServerID": data.get("server_id", ""),
/app/backend/modules/fase2_operativo/repositories/auditoria_programada_repository.py:130:            "server_id": "ServerID",
/app/backend/modules/fase2_operativo/repositories/auditoria_programada_repository.py:584:            "server_id": row.get("ServerID"),
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:73:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:84:            server_ids: Lista opcional de server_ids para filtro RBAC
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:90:        if server_ids:
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:91:            filters["server_id"] = {"$in": server_ids}
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:104:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:110:            server_ids=server_ids
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:116:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:122:            server_ids=server_ids
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:128:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:134:            server_ids=server_ids
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:140:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:146:            server_ids=server_ids
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:152:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:157:        MIGRADO A SQL: Soporta filtrado por server_ids para RBAC.
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:161:            server_ids: Lista opcional de server_ids para filtro RBAC
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:169:            server_ids=server_ids
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:228:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:234:        FASE 3.1: Soporta filtrado por server_ids para RBAC.
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:237:            server_ids: Lista opcional de server_ids permitidos para filtrar
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:245:        # Match por server_ids si se especifica (RBAC)
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:246:        if server_ids:
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:247:            pipeline.append({"$match": {"server_id": {"$in": server_ids}}})
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:270:        server_ids: Optional[List[str]] = None,
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:284:            server_ids: Lista de server_ids para RBAC
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:297:        if server_ids:
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:298:            filters["server_id"] = {"$in": server_ids}
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:35:        server_id: str,
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:43:        1. Buscar por server_id + sucursal_id + almacen_id (si se proporciona)
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:44:        2. Buscar por server_id + sucursal_id (sin almacén)
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:61:                """, (server_id, sucursal_id))
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:67:                """, (server_id, sucursal_id))
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:83:        server_id: str,
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:101:            """, (datetime.now(timezone.utc), server_id, sucursal_id))
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:114:    async def get_todas_asignaciones(self, server_id: Optional[str] = None) -> List[Dict]:
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:122:            if server_id:
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:128:                """, (server_id,))
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:32:    NOTA: server_id no existe en Tareas_Inventario.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:33:    Para filtrar por server_id se requiere JOIN con Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:143:    async def get_vencidas(self, server_ids: Optional[List[str]] = None) -> List[Dict]:
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:150:        Para filtrar por server_ids se requiere JOIN con Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:151:        Actualmente retorna todas las tareas vencidas si server_ids se especifica,
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:155:            server_ids: Lista opcional de server_ids (filtrado en capa service)
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:167:        # NOTA: server_id no existe en Tareas_Inventario
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:169:        if server_ids:
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:171:                "[TAREA_REPO] get_vencidas: server_ids ignorado (campo no existe en tabla). "
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:252:    async def contar_por_estado(self, server_ids: Optional[List[str]] = None) -> Dict[str, int]:
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:258:        NOTA: server_ids requiere JOIN con Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:259:        Actualmente ignora server_ids y cuenta todas las tareas.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:263:            server_ids: Lista opcional de server_ids (filtrado en service)
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:270:        # NOTA: server_id no existe en Tareas_Inventario
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:271:        if server_ids:
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:273:                "[TAREA_REPO] contar_por_estado: server_ids ignorado (campo no existe). "
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:323:        server_ids: List[str],
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:335:        Este método hace JOIN para filtrar tareas por server_id,
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:339:            server_ids: Lista de server_ids para RBAC
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:362:        # Filtro RBAC por server_ids
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:363:        if server_ids:
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:364:            placeholders = ", ".join(["%s"] * len(server_ids))
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:366:            params.extend(server_ids)
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:191:        server_ids: Optional[List[str]] = None,
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:206:            server_ids: Lista de server_ids para RBAC
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:224:        if server_ids:
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:225:            filtro["server_id"] = {"$in": server_ids}
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:252:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:260:            server_ids: Lista opcional de server_ids para filtro RBAC
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:268:        if server_ids:
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:269:            pipeline.append({"$match": {"server_id": {"$in": server_ids}}})
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:377:        server_ids: Optional[List[str]] = None,
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:386:            server_ids: Lista opcional de server_ids para RBAC
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:394:        if server_ids:
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:395:            filters["server_id"] = {"$in": server_ids}
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:67:        "server_id": "ServerID",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:101:        "server_id": "ServerID",  # Puede no existir, manejar con cuidado
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:129:        "server_id": "ServerID",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:319:            server=self._sql_config["server"],
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:321:            database=self._sql_config["database"],
/app/backend/modules/fase2_operativo/services/orquestador_service.py:56:        server_id: str,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:118:                server_id, sucursal_id, almacen_id, folio_final_key
/app/backend/modules/fase2_operativo/services/orquestador_service.py:130:                server_id, almacen_id
/app/backend/modules/fase2_operativo/services/orquestador_service.py:139:                    f"No existe configuración de asignación para server={server_id}, almacen={almacen_id}. "
/app/backend/modules/fase2_operativo/services/orquestador_service.py:145:                    server_id=server_id,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:196:                server_id=server_id,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:271:        server_id: str,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:279:            config = await obtener_config_asignacion(server_id, almacen_id)
/app/backend/modules/fase2_operativo/services/orquestador_service.py:284:                    f"server={server_id}, almacen={almacen_id}"
/app/backend/modules/fase2_operativo/services/orquestador_service.py:301:                f"{usuario.get('name', usuario.get('email'))} para server={server_id}, almacen={almacen_id}"
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:97:        server_id: str,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:114:            "server_id": server_id,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:136:            "server_id": server_id,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:183:        inv_inicial = self._buscar_inventario_inicial(server_id, almacen_id, fecha_inicio_periodo)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:189:        inv_final = self._buscar_inventario_final(server_id, almacen_id, fecha_pedido)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:203:            self._marcar_pedido_procesado(server_id, pedido_id, origen_sistema, automatizacion_id)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:229:        self._marcar_pedido_procesado(server_id, pedido_id, origen_sistema, automatizacion_id)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:445:        server_id: Optional[str] = None,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:452:        if server_id:
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:453:            filtro["server_id"] = server_id
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:467:    def obtener_kpis(self, server_id: Optional[str] = None) -> Dict:
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:469:        filtro = {"server_id": server_id} if server_id else {}
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:593:        server_id: str,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:601:            "server_id": server_id,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:611:        server_id: str,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:620:            "server_id": server_id,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:632:    def _marcar_pedido_procesado(self, server_id: str, pedido_folio: str, origen: str, automatizacion_id: str):
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:636:            "server_id": server_id,
/app/backend/modules/fase2_operativo/services/operativo_service.py:360:    async def obtener_resumen_dashboard(self, server_ids: Optional[List[str]] = None) -> Dict[str, Any]:
/app/backend/modules/fase2_operativo/services/operativo_service.py:363:        FASE 3.1: Soporta filtrado por server_ids para RBAC.
/app/backend/modules/fase2_operativo/services/operativo_service.py:366:            server_ids: Lista opcional de server_ids permitidos para filtrar
/app/backend/modules/fase2_operativo/services/operativo_service.py:372:        workflows_por_estado = await self.workflow_service.resumen_por_estado(server_ids=server_ids)
/app/backend/modules/fase2_operativo/services/operativo_service.py:375:        tareas_por_estado = await self.tarea_service.resumen_por_estado(server_ids=server_ids)
/app/backend/modules/fase2_operativo/services/operativo_service.py:378:        tareas_vencidas = await self.tarea_service.obtener_tareas_vencidas(server_ids=server_ids)
/app/backend/modules/fase2_operativo/services/operativo_service.py:381:        workflows_escalados = await self.workflow_service.listar_escalados(server_ids=server_ids)
/app/backend/modules/fase2_operativo/services/operativo_service.py:402:    async def obtener_alertas_activas(self, server_ids: Optional[List[str]] = None) -> List[Dict]:
/app/backend/modules/fase2_operativo/services/operativo_service.py:405:        FASE 3.1: Soporta filtrado por server_ids para RBAC.
/app/backend/modules/fase2_operativo/services/operativo_service.py:408:            server_ids: Lista opcional de server_ids permitidos para filtrar
/app/backend/modules/fase2_operativo/services/operativo_service.py:416:        tareas_vencidas = await self.tarea_service.obtener_tareas_vencidas(server_ids=server_ids)
/app/backend/modules/fase2_operativo/services/operativo_service.py:427:        workflows_escalados = await self.workflow_service.listar_escalados(server_ids=server_ids)
/app/backend/modules/fase2_operativo/services/tarea_service.py:304:    async def obtener_tareas_vencidas(self, server_ids: Optional[List[str]] = None) -> List[Dict]:
/app/backend/modules/fase2_operativo/services/tarea_service.py:307:        FASE 3.1: Soporta filtrado por server_ids para RBAC.
/app/backend/modules/fase2_operativo/services/tarea_service.py:310:            server_ids: Lista opcional de server_ids permitidos para filtrar
/app/backend/modules/fase2_operativo/services/tarea_service.py:315:        return await self.tarea_repo.get_vencidas(server_ids=server_ids)
/app/backend/modules/fase2_operativo/services/tarea_service.py:329:    async def resumen_por_estado(self, server_ids: Optional[List[str]] = None) -> Dict[str, int]:
/app/backend/modules/fase2_operativo/services/tarea_service.py:332:        FASE 3.1: Soporta filtrado por server_ids para RBAC.
/app/backend/modules/fase2_operativo/services/tarea_service.py:335:            server_ids: Lista opcional de server_ids permitidos para filtrar
/app/backend/modules/fase2_operativo/services/tarea_service.py:340:        return await self.tarea_repo.contar_por_estado(server_ids=server_ids)
/app/backend/modules/fase2_operativo/services/workflow_service.py:278:    async def listar_escalados(self, limit: int = 100, server_ids: Optional[List[str]] = None) -> List[Dict]:
/app/backend/modules/fase2_operativo/services/workflow_service.py:279:        """Lista workflows escalados. Soporta filtrado por server_ids para RBAC."""
/app/backend/modules/fase2_operativo/services/workflow_service.py:280:        return await self.workflow_repo.get_escalados(limit, server_ids=server_ids)
/app/backend/modules/fase2_operativo/services/workflow_service.py:282:    async def resumen_por_estado(self, server_ids: Optional[List[str]] = None) -> Dict[str, int]:
/app/backend/modules/fase2_operativo/services/workflow_service.py:285:        FASE 3.1: Soporta filtrado por server_ids para RBAC.
/app/backend/modules/fase2_operativo/services/workflow_service.py:288:            server_ids: Lista opcional de server_ids permitidos para filtrar
/app/backend/modules/fase2_operativo/services/workflow_service.py:293:        return await self.workflow_repo.contar_por_estado(server_ids=server_ids)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:33:    server_id: str
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:297:    server_id: Optional[str] = Query(None),
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:304:    return service.obtener_kpis(server_id)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:309:    server_id: Optional[str] = Query(None),
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:319:    return service.listar_automatizaciones(server_id, sucursal_id, estado, limite)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:418:        server_id=request.server_id,
/app/backend/modules/fase2_operativo/routes/workflow_routes.py:41:async def get_user_server_ids(current_user: Dict[str, Any]) -> list:
/app/backend/modules/fase2_operativo/routes/workflow_routes.py:42:    """Obtiene los server_ids permitidos para el usuario."""
/app/backend/modules/fase2_operativo/routes/workflow_routes.py:101:        # Verificar acceso por server_id
/app/backend/modules/fase2_operativo/routes/workflow_routes.py:102:        server_ids = await get_user_server_ids(current_user)
/app/backend/modules/fase2_operativo/routes/workflow_routes.py:103:        workflow_server = workflow.get("server_id")
/app/backend/modules/fase2_operativo/routes/workflow_routes.py:104:        if workflow_server and server_ids and workflow_server not in server_ids:
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:31:async def get_user_server_ids(current_user: Dict[str, Any]) -> list:
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:33:    Obtiene los server_ids permitidos para el usuario basándose en sus empresas_permitidas.
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:39:    server_ids = await get_servers_for_empresas(empresas_permitidas)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:40:    return server_ids
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:60:        # Obtener server_ids permitidos para el usuario
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:61:        server_ids = await get_user_server_ids(current_user)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:64:        resumen = await operativo_svc.obtener_resumen_dashboard(server_ids=server_ids)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:85:        # Obtener server_ids permitidos para el usuario
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:86:        server_ids = await get_user_server_ids(current_user)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:89:        alertas = await operativo_svc.obtener_alertas_activas(server_ids=server_ids)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:110:        # Obtener server_ids permitidos para el usuario
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:111:        server_ids = await get_user_server_ids(current_user)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:114:        resumen = await workflow_svc.resumen_por_estado(server_ids=server_ids)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:136:        # Obtener server_ids permitidos para el usuario
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:137:        server_ids = await get_user_server_ids(current_user)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:140:        resumen = await tarea_svc.resumen_por_estado(server_ids=server_ids)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:162:        # Obtener server_ids permitidos para el usuario
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:163:        server_ids = await get_user_server_ids(current_user)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:166:        vencidas = await tarea_svc.obtener_tareas_vencidas(server_ids=server_ids)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:188:        # Obtener server_ids permitidos para el usuario
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:189:        server_ids = await get_user_server_ids(current_user)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:195:        workflows_por_estado = await workflow_svc.resumen_por_estado(server_ids=server_ids)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:196:        tareas_por_estado = await tarea_svc.resumen_por_estado(server_ids=server_ids)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:197:        tareas_vencidas = await tarea_svc.obtener_tareas_vencidas(server_ids=server_ids)
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:199:        # Métricas SLA (por ahora sin filtro de server_ids en SLA service)
/app/backend/modules/api_connections/repository.py:23:from core.db import execute_sql_query
/app/backend/modules/api_connections/repository.py:79:        execute_sql_query(
/app/backend/modules/api_connections/repository.py:165:        results = execute_sql_query(
/app/backend/modules/api_connections/repository.py:196:        results = execute_sql_query(
/app/backend/modules/api_connections/repository.py:230:        results = execute_sql_query(
/app/backend/modules/api_connections/repository.py:316:        execute_sql_query(
/app/backend/modules/api_connections/repository.py:411:        execute_sql_query(
/app/backend/modules/api_connections/repository.py:453:        execute_sql_query(
/app/backend/modules/api_connections/repository.py:632:        results = execute_sql_query(
/app/backend/modules/api_connections/repository.py:683:        results = execute_sql_query(
/app/backend/modules/api_connections/universal_test_routes.py:23:- Endpoint SQL: /api/servers/{server_id}/universal-query-test
/app/backend/modules/api_connections/universal_test_routes.py:143:            server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/modules/api_connections/universal_test_routes.py:145:            database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/modules/api_connections/universal_test_routes.py:182:            server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/modules/api_connections/universal_test_routes.py:184:            database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/modules/corporate_filters/router.py:6:from core.db import execute_sql_query
/app/backend/modules/corporate_filters/router.py:55:    return execute_sql_query(
/app/backend/modules/corporate_filters/router.py:143:        CAST(server_id AS VARCHAR(36)) AS id_empresa,
/app/backend/modules/sistema/estructura_service.py:130:                    "server_id": mapeo.get("server_id"),
/app/backend/modules/sistema/menu_service.py:30:            server=self.db_config['host'],
/app/backend/modules/sistema/menu_service.py:33:            database=self.db_config['database'],
/app/backend/modules/costos_margenes/schemas_precios.py:53:    server_id: str = Field(..., description="ID del servidor")
/app/backend/modules/costos_margenes/schemas_precios.py:64:    server_id: str
/app/backend/modules/costos_margenes/schemas_precios.py:100:    server_id: str = Field(..., description="ID del servidor")
/app/backend/modules/costos_margenes/schemas_precios.py:123:    server_id: str
/app/backend/modules/costos_margenes/repository.py:10:from core.db import execute_sql_query
/app/backend/modules/costos_margenes/repository.py:60:    productos_result = execute_sql_query(*conn, productos_query)
/app/backend/modules/costos_margenes/repository.py:64:    insumos_result = execute_sql_query(*conn, insumos_query)
/app/backend/modules/costos_margenes/repository.py:68:    recetas_result = execute_sql_query(*conn, recetas_query)
/app/backend/modules/costos_margenes/repository.py:72:    elaborados_result = execute_sql_query(*conn, elaborados_query)
/app/backend/modules/costos_margenes/repository.py:186:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/costos_margenes/repository.py:201:        CAST(p.ServerID AS NVARCHAR(36)) as server_id,
/app/backend/modules/costos_margenes/repository.py:232:    data_result = execute_sql_query(*conn, data_query) or []
/app/backend/modules/costos_margenes/repository.py:273:            'server_id': row.get('server_id', ''),
/app/backend/modules/costos_margenes/repository.py:310:        CAST(ServerID AS NVARCHAR(36)) as server_id,
/app/backend/modules/costos_margenes/repository.py:318:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository.py:322:def get_receta_producto(producto_id: str, server_id: Optional[str] = None) -> Tuple[Dict, List[Dict]]:
/app/backend/modules/costos_margenes/repository.py:333:        if server_id:
/app/backend/modules/costos_margenes/repository.py:340:                CAST(ServerID AS NVARCHAR(36)) as server_id,
/app/backend/modules/costos_margenes/repository.py:346:            AND ServerID = '{server_id}'
/app/backend/modules/costos_margenes/repository.py:348:            result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository.py:355:    srv_id = producto.get('server_id')
/app/backend/modules/costos_margenes/repository.py:378:    receta_result = execute_sql_query(*conn, receta_query) or []
/app/backend/modules/costos_margenes/repository.py:409:def get_receta_elaborado(codigo_elaborado: str, server_id: Optional[str] = None) -> Tuple[Optional[Dict], List[Dict]]:
/app/backend/modules/costos_margenes/repository.py:418:        server_id: ServerID para filtrar
/app/backend/modules/costos_margenes/repository.py:426:    where_srv = f"AND CAST(ServerID AS NVARCHAR(36)) = '{server_id}'" if server_id else ""
/app/backend/modules/costos_margenes/repository.py:434:        CAST(ServerID AS NVARCHAR(36)) as server_id,
/app/backend/modules/costos_margenes/repository.py:444:    insumo_result = execute_sql_query(*conn, insumo_query)
/app/backend/modules/costos_margenes/repository.py:454:            CAST(ServerID AS NVARCHAR(36)) as server_id,
/app/backend/modules/costos_margenes/repository.py:463:        insumo_result = execute_sql_query(*conn, producto_query)
/app/backend/modules/costos_margenes/repository.py:467:            return get_receta_producto(codigo_elaborado, server_id)
/app/backend/modules/costos_margenes/repository.py:473:    srv_id = insumo_info.get('server_id') or server_id
/app/backend/modules/costos_margenes/repository.py:499:    elaborado_result = execute_sql_query(*conn, elaborado_query) or []
/app/backend/modules/costos_margenes/repository.py:530:        'server_id': srv_id,
/app/backend/modules/costos_margenes/repository.py:542:def get_insumos_producto(producto_id: str, server_id: Optional[str] = None) -> Tuple[Dict, List[Dict]]:
/app/backend/modules/costos_margenes/repository.py:547:    producto, componentes = get_receta_producto(producto_id, server_id)
/app/backend/modules/costos_margenes/repository.py:599:    sync_result = execute_sql_query(*conn, sync_query)
/app/backend/modules/costos_margenes/repository.py:615:        result = execute_sql_query(*conn, count_query)
/app/backend/modules/costos_margenes/repository.py:626:    sistema_result = execute_sql_query(*conn, sistema_query) or []
/app/backend/modules/costos_margenes/repository.py:638:    servidor_result = execute_sql_query(*conn, servidor_query) or []
/app/backend/modules/costos_margenes/repository.py:697:        CAST(server_id AS NVARCHAR(36)) as server_id,
/app/backend/modules/costos_margenes/repository.py:707:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository.py:715:            'server_id': row.get('server_id', ''),
/app/backend/modules/costos_margenes/repository.py:759:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository.py:804:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/routes_precios.py:175:            data.server_id
/app/backend/modules/costos_margenes/routes_precios.py:198:                data.server_id,
/app/backend/modules/costos_margenes/routes_precios.py:210:            server_id=datos_producto['server_id'],
/app/backend/modules/costos_margenes/routes_precios.py:264:            server_id=data.server_id,
/app/backend/modules/costos_margenes/routes_precios.py:291:    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
/app/backend/modules/costos_margenes/routes_precios.py:310:            server_id=server_id,
/app/backend/modules/costos_margenes/routes.py:50:from core.db import execute_sql_query
/app/backend/modules/costos_margenes/routes.py:75:    Obtiene los server_id permitidos para el usuario desde Usuario_ServidoresAsignacion.
/app/backend/modules/costos_margenes/routes.py:78:        (lista_server_ids, es_corporativo)
/app/backend/modules/costos_margenes/routes.py:101:        user_result = execute_sql_query(*conn, user_query)
/app/backend/modules/costos_margenes/routes.py:111:        SELECT CAST(sa.ServidorID AS NVARCHAR(36)) as server_id
/app/backend/modules/costos_margenes/routes.py:116:        servers_result = execute_sql_query(*conn, servers_query) or []
/app/backend/modules/costos_margenes/routes.py:118:        server_ids = [r.get('server_id') for r in servers_result if r.get('server_id')]
/app/backend/modules/costos_margenes/routes.py:121:        if len(server_ids) == 0:
/app/backend/modules/costos_margenes/routes.py:125:        logger.info(f"[RBAC] Usuario {email} tiene acceso a {len(server_ids)} servidores: {server_ids[:3]}...")
/app/backend/modules/costos_margenes/routes.py:126:        return server_ids, False
/app/backend/modules/costos_margenes/routes.py:309:                server_id=p['server_id'],
/app/backend/modules/costos_margenes/routes.py:351:    server_id: Optional[str] = Query(None, description="ServerID para búsqueda por código fuente"),
/app/backend/modules/costos_margenes/routes.py:364:    - server_id: ServerID para filtrar (opcional pero recomendado para elaborados)
/app/backend/modules/costos_margenes/routes.py:380:        producto, componentes = get_receta_producto(producto_id, server_id)
/app/backend/modules/costos_margenes/routes.py:384:            producto, componentes = get_receta_elaborado(producto_id, server_id)
/app/backend/modules/costos_margenes/routes.py:388:            producto, componentes = get_receta_elaborado(producto_id, server_id)
/app/backend/modules/costos_margenes/routes.py:422:            server_id=producto.get('server_id', ''),
/app/backend/modules/costos_margenes/routes.py:444:    server_id: Optional[str] = Query(None, description="ServerID para búsqueda por código fuente"),
/app/backend/modules/costos_margenes/routes.py:465:        producto, insumos = get_insumos_producto(producto_id, server_id)
/app/backend/modules/costos_margenes/routes.py:572:    **Retorna**: Lista de unidades con código, nombre, server_id
/app/backend/modules/costos_margenes/routes.py:584:            unidades = [u for u in unidades if u.get('server_id') in allowed_servers]
/app/backend/modules/costos_margenes/repository_precios.py:16:from core.db import execute_sql_query
/app/backend/modules/costos_margenes/repository_precios.py:70:    server_id: str
/app/backend/modules/costos_margenes/repository_precios.py:80:    server_id_clean = server_id.replace('-', '').upper()
/app/backend/modules/costos_margenes/repository_precios.py:100:    AND REPLACE(CAST(p.ServerID AS VARCHAR(50)), '-', '') = '{server_id_clean}'
/app/backend/modules/costos_margenes/repository_precios.py:103:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository_precios.py:114:        'server_id': str(r['ServerID']),
/app/backend/modules/costos_margenes/repository_precios.py:190:    server_id: str,
/app/backend/modules/costos_margenes/repository_precios.py:225:        '{server_id}',
/app/backend/modules/costos_margenes/repository_precios.py:246:    execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository_precios.py:254:    server_id: str,
/app/backend/modules/costos_margenes/repository_precios.py:271:    datos_producto = obtener_datos_producto_para_simulacion(producto_id, server_id)
/app/backend/modules/costos_margenes/repository_precios.py:315:        '{server_id}', '{datos_producto["system_type"]}',
/app/backend/modules/costos_margenes/repository_precios.py:330:    execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository_precios.py:355:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository_precios.py:364:    server_id: Optional[str] = None,
/app/backend/modules/costos_margenes/repository_precios.py:375:    if server_id:
/app/backend/modules/costos_margenes/repository_precios.py:376:        where_clauses.append(f"ServerID = '{server_id}'")
/app/backend/modules/costos_margenes/repository_precios.py:385:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/costos_margenes/repository_precios.py:400:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository_precios.py:512:    execute_sql_query(*conn, update_query)
/app/backend/modules/costos_margenes/repository_precios.py:543:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository_precios.py:573:        'server_id': str(r['ServerID']),
/app/backend/modules/costos_margenes/repository_precios.py:649:    execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/schemas.py:78:    server_id: str
/app/backend/modules/costos_margenes/schemas.py:162:    server_id: str
/app/backend/modules/rh/importador/homologacion_service.py:31:        server=server['host'],
/app/backend/modules/rh/importador/homologacion_service.py:33:        database=server['database'],
/app/backend/modules/rh/importador/aprobacion_service.py:48:        server=server['host'],
/app/backend/modules/rh/importador/aprobacion_service.py:50:        database=server['database'],
/app/backend/modules/rh/importador/repository.py:20:from core.db import execute_sql_query
/app/backend/modules/rh/importador/repository.py:27:EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"
/app/backend/modules/rh/importador/repository.py:69:        {"id": EDARSA_HUB_SERVER_ID, "active": True},
/app/backend/modules/rh/importador/repository.py:79:    return execute_sql_query(
/app/backend/modules/rh/repository.py:10:- Reutiliza execute_sql_query de core.db
/app/backend/modules/rh/repository.py:29:from core.db import execute_sql_query
/app/backend/modules/rh/repository.py:52:EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"
/app/backend/modules/rh/repository.py:183:    return execute_sql_query(
/app/backend/modules/rh/repository.py:544:# IMPORTANTE: Estas funciones usan execute_sql_query_params() que pasa
/app/backend/modules/rh/repository.py:557:from core.db import execute_sql_query_params
/app/backend/modules/rh/repository.py:572:    return execute_sql_query_params(
/app/backend/modules/rh/repository.py:1231:# - Se usa execute_sql_query_params() para parámetros nativos donde es posible
/app/backend/modules/rh/repository.py:1415:# - execute_sql_query_params() para INSERT y UPDATE con IDs
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:38:        server=EDARSAHUB_CONFIG['host'],
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:40:        database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:206:            SELECT nombre, CAST(id AS VARCHAR(50)) as server_id
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:214:        empresa = empresas[0] if empresas else {"nombre": unidad_negocio_id, "server_id": unidad_negocio_id}
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:250:            empresa.get('server_id', ''),
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:339:        server_id: str,
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:360:        rows = await _execute_sql_async(query, (server_id, almacen_id, almacen_id))
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:376:            # Buscar el server_id asociado a la unidad
/app/backend/modules/configuracion/services/almacenes_sync_service.py:25:from core.db import execute_sql_query
/app/backend/modules/configuracion/services/almacenes_sync_service.py:92:    - server_id, system_type, sucursal_origen_id via context_resolver
/app/backend/modules/configuracion/services/almacenes_sync_service.py:124:        server_id = context.get("server_id")
/app/backend/modules/configuracion/services/almacenes_sync_service.py:129:        if not server_id:
/app/backend/modules/configuracion/services/almacenes_sync_service.py:140:        from core.server_registry import get_server_connection_info_with_secrets
/app/backend/modules/configuracion/services/almacenes_sync_service.py:141:        # ANTES: server = await db.servers.find_one({"id": server_id}, {"_id": 0})
/app/backend/modules/configuracion/services/almacenes_sync_service.py:142:        server = get_server_connection_info_with_secrets(server_id)
/app/backend/modules/configuracion/services/almacenes_sync_service.py:174:            almacenes_origen = execute_sql_query(
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:9:1. Solo conceptos de negocio en la API (NO server_id, NO sucursal_id)
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:584:    # Obtener server_id de la unidad
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:597:    server_id = context.get("server_id")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:598:    if not server_id:
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:609:    responsable = await repo.resolver_responsable(server_id, almacen_id)
/app/backend/modules/inventarios/repository.py:17:def get_inventarios_fisicos(server_id: str = None, almacen: str = None, 
/app/backend/modules/inventarios/repository.py:31:    if server_id:
/app/backend/modules/inventarios/repository.py:32:        query += " AND LOWER(server_id) = LOWER(%s)"
/app/backend/modules/inventarios/repository.py:33:        params.append(server_id)
/app/backend/modules/inventarios/repository.py:49:def get_inventario_by_folio(folio: str, server_id: str = None) -> Optional[Dict]:
/app/backend/modules/inventarios/repository.py:61:    if server_id:
/app/backend/modules/inventarios/repository.py:62:        query += " AND LOWER(server_id) = LOWER(%s)"
/app/backend/modules/inventarios/repository.py:63:        params.append(server_id)
/app/backend/modules/inventarios/repository.py:68:def get_inventarios_count_by_server(server_id: str) -> int:
/app/backend/modules/inventarios/repository.py:75:        WHERE LOWER(server_id) = LOWER(%s) AND sync_status = 'ACTIVE'
/app/backend/modules/inventarios/repository.py:77:    result = execute_hub_query_single(query, (server_id,))
/app/backend/modules/inventarios/repository.py:85:    def get_all(server_id: str = None, **filters) -> List[Dict]:
/app/backend/modules/inventarios/repository.py:86:        return get_inventarios_fisicos(server_id=server_id, **filters)
/app/backend/modules/inventarios/repository.py:89:    def get_by_folio(folio: str, server_id: str = None) -> Optional[Dict]:
/app/backend/modules/inventarios/repository.py:90:        return get_inventario_by_folio(folio, server_id)
/app/backend/modules/consultas_sql/repository.py:16:Usa core.db.execute_sql_query para ejecución.
/app/backend/modules/consultas_sql/repository.py:28:from core.db import execute_sql_query
/app/backend/modules/consultas_sql/repository.py:63:        return execute_sql_query(
/app/backend/modules/consultas_sql/repository.py:66:            database=self._config['database'],
/app/backend/modules/consultas_sql/routes.py:35:from core.db import execute_sql_query
/app/backend/modules/consultas_sql/routes.py:36:from core.server_registry import get_server_connection_info_with_secrets
/app/backend/modules/consultas_sql/routes.py:351:        from core.db import execute_sql_query
/app/backend/modules/consultas_sql/routes.py:353:        versiones_rows = execute_sql_query(
/app/backend/modules/consultas_sql/routes.py:443:        from core.db import execute_sql_query
/app/backend/modules/consultas_sql/routes.py:445:        servidores_rows = execute_sql_query(
/app/backend/modules/consultas_sql/routes.py:749:        server_info = get_server_connection_info_with_secrets(request.servidor_id)
/app/backend/modules/consultas_sql/routes.py:819:            rows = execute_sql_query(
/app/backend/modules/consultas_sql/routes.py:822:                database=server_info['database'],
/app/backend/modules/inteligencia_comercial/routes.py:80:        server=EDARSAHUB_CONFIG["host"],
/app/backend/modules/inteligencia_comercial/routes.py:84:        database=EDARSAHUB_CONFIG["database"],
/app/backend/modules/catalogos/repository.py:14:from core.db import execute_sql_query
/app/backend/modules/catalogos/repository.py:23:EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"
/app/backend/modules/catalogos/repository.py:54:    return execute_sql_query(
/app/backend/modules/catalogos/routes.py:70:    from core.db import execute_sql_query
/app/backend/modules/catalogos/routes.py:89:        rows = execute_sql_query(
/app/backend/modules/catalogos/routes.py:108:    from core.db import execute_sql_query
/app/backend/modules/catalogos/routes.py:118:        rows = execute_sql_query(
/app/backend/modules/catalogos/routes.py:151:    from core.db import execute_sql_query
/app/backend/modules/catalogos/routes.py:170:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:185:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:214:    from core.db import execute_sql_query
/app/backend/modules/catalogos/routes.py:235:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:250:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:286:    from core.db import execute_sql_query
/app/backend/modules/catalogos/routes.py:302:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:315:        execute_sql_query(
/app/backend/modules/catalogos/routes.py:338:    from core.db import execute_sql_query
/app/backend/modules/catalogos/routes.py:346:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:367:        execute_sql_query(
/app/backend/modules/catalogos/routes.py:391:    from core.db import execute_sql_query
/app/backend/modules/catalogos/routes.py:399:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:423:        execute_sql_query(
/app/backend/modules/catalogos/routes.py:450:    from core.db import execute_sql_query
/app/backend/modules/catalogos/routes.py:458:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:482:        execute_sql_query(
/app/backend/modules/sync_historicos/service.py:23:from core.db import execute_sql_query
/app/backend/modules/sync_historicos/service.py:144:            result = execute_sql_query(
/app/backend/modules/sync_historicos/service.py:202:            result = execute_sql_query(
/app/backend/modules/sync_historicos/service.py:257:        if config.server_ids:
/app/backend/modules/sync_historicos/service.py:258:            servers = [s for s in all_servers if s.get('id') in config.server_ids]
/app/backend/modules/sync_historicos/service.py:283:                    server_id=config.server_ids[0] if config.server_ids and len(config.server_ids) == 1 else None,
/app/backend/modules/sync_historicos/service.py:306:            server_id = server['id']
/app/backend/modules/sync_historicos/service.py:309:            logger.info(f"[SYNC-VENTAS] Procesando servidor {server_id} ({system_type})")
/app/backend/modules/sync_historicos/service.py:312:                'server_id': server_id,
/app/backend/modules/sync_historicos/service.py:322:                server_info = _get_server_by_id_from_sql(server_id)
/app/backend/modules/sync_historicos/service.py:324:                    raise Exception(f"No se encontró configuración para servidor {server_id}")
/app/backend/modules/sync_historicos/service.py:375:                            f"[SYNC-VENTAS] {server_id}/{fecha_actual}: "
/app/backend/modules/sync_historicos/service.py:388:                        server_id=server_id,
/app/backend/modules/sync_historicos/service.py:416:                            f"[SYNC-VENTAS] DRY-RUN {server_id}/{fecha_actual}: "
/app/backend/modules/sync_historicos/service.py:442:                logger.error(f"[SYNC-VENTAS] Error procesando servidor {server_id}: {e}")
/app/backend/modules/sync_historicos/service.py:446:            result.resultados_por_servidor[server_id] = server_result
/app/backend/modules/sync_historicos/service.py:510:            result = execute_sql_query(
/app/backend/modules/sync_historicos/service.py:573:            result = execute_sql_query(
/app/backend/modules/sync_historicos/service.py:619:        if config.server_ids:
/app/backend/modules/sync_historicos/service.py:620:            servers = [s for s in all_servers if s.get('id') in config.server_ids]
/app/backend/modules/sync_historicos/service.py:644:                    server_id=config.server_ids[0] if config.server_ids and len(config.server_ids) == 1 else None,
/app/backend/modules/sync_historicos/service.py:666:            server_id = server['id']
/app/backend/modules/sync_historicos/service.py:669:            logger.info(f"[SYNC-POR-HORA] Procesando servidor {server_id} ({system_type})")
/app/backend/modules/sync_historicos/service.py:672:                'server_id': server_id,
/app/backend/modules/sync_historicos/service.py:681:                server_info = _get_server_by_id_from_sql(server_id)
/app/backend/modules/sync_historicos/service.py:683:                    raise Exception(f"No se encontró configuración para servidor {server_id}")
/app/backend/modules/sync_historicos/service.py:728:                        logger.warning(f"[SYNC-POR-HORA] {server_id}/{fecha_actual}: Fuente falló")
/app/backend/modules/sync_historicos/service.py:735:                            server_id=server_id,
/app/backend/modules/sync_historicos/service.py:759:                                f"[SYNC-POR-HORA] DRY-RUN {server_id}/{fecha_actual}/{hora_data['hora']}h: "
/app/backend/modules/sync_historicos/service.py:784:                logger.error(f"[SYNC-POR-HORA] Error procesando servidor {server_id}: {e}")
/app/backend/modules/sync_historicos/service.py:788:            result.resultados_por_servidor[server_id] = server_result
/app/backend/modules/sync_historicos/service.py:848:        if config.server_ids:
/app/backend/modules/sync_historicos/service.py:849:            servers = [s for s in all_servers if s.get('id') in config.server_ids]
/app/backend/modules/sync_historicos/service.py:872:                    server_id=config.server_ids[0] if config.server_ids and len(config.server_ids) == 1 else None,
/app/backend/modules/sync_historicos/service.py:894:            server_id = server['id']
/app/backend/modules/sync_historicos/service.py:897:            logger.info(f"[SYNC-DIA-SEMANA] Procesando servidor {server_id} ({system_type})")
/app/backend/modules/sync_historicos/service.py:900:                'server_id': server_id,
/app/backend/modules/sync_historicos/service.py:909:                server_info = _get_server_by_id_from_sql(server_id)
/app/backend/modules/sync_historicos/service.py:911:                    raise Exception(f"No se encontró configuración para servidor {server_id}")
/app/backend/modules/sync_historicos/service.py:972:                        server_id=server_id,
/app/backend/modules/sync_historicos/service.py:996:                        'server_id': venta.server_id,
/app/backend/modules/sync_historicos/service.py:1007:                            f"[SYNC-DIA-SEMANA] DRY-RUN {server_id}/{self.DIAS_SEMANA_NOMBRES[dia_semana]}: "
/app/backend/modules/sync_historicos/service.py:1030:                logger.error(f"[SYNC-DIA-SEMANA] Error procesando servidor {server_id}: {e}")
/app/backend/modules/sync_historicos/service.py:1034:            result.resultados_por_servidor[server_id] = server_result
/app/backend/modules/sync_historicos/repository.py:25:from core.db import execute_sql_query
/app/backend/modules/sync_historicos/repository.py:61:        return execute_sql_query(
/app/backend/modules/sync_historicos/repository.py:364:        WHERE ServerID = '{venta.server_id}'
/app/backend/modules/sync_historicos/repository.py:372:            logger.debug(f"[SYNC-UPSERT] Venta ya existe con mismo hash: {venta.server_id}/{venta.fecha_operacion}")
/app/backend/modules/sync_historicos/repository.py:379:            '{venta.server_id}' AS ServerID,
/app/backend/modules/sync_historicos/repository.py:418:                '{venta.server_id}', {venta.empresa_id}, 
/app/backend/modules/sync_historicos/repository.py:452:            {f"'{ejecucion.server_id}'" if ejecucion.server_id else 'NULL'},
/app/backend/modules/sync_historicos/repository.py:491:    def get_ultimo_sync(self, server_id: str, sync_type: str) -> Optional[Dict]:
/app/backend/modules/sync_historicos/repository.py:496:        WHERE ServerID = '{server_id}'
/app/backend/modules/sync_historicos/repository.py:521:        WHERE ServerID = '{venta.server_id}'
/app/backend/modules/sync_historicos/repository.py:529:            logger.debug(f"[SYNC-UPSERT] VentaPorHora ya existe con mismo hash: {venta.server_id}/{venta.fecha_operacion}/{venta.hora}")
/app/backend/modules/sync_historicos/repository.py:536:            '{venta.server_id}' AS ServerID,
/app/backend/modules/sync_historicos/repository.py:573:                '{venta.server_id}', {venta.empresa_id}, 
/app/backend/modules/sync_historicos/repository.py:610:        WHERE ServerID = '{venta.server_id}'
/app/backend/modules/sync_historicos/repository.py:626:            '{venta.server_id}' AS ServerID,
/app/backend/modules/sync_historicos/repository.py:664:                '{venta.server_id}', {venta.empresa_id}, 
/app/backend/modules/sync_historicos/models.py:10:- server_id, empresa_id, sucursal_id
/app/backend/modules/sync_historicos/models.py:54:    server_id: str
/app/backend/modules/sync_historicos/models.py:94:            'server_id': self.server_id,
/app/backend/modules/sync_historicos/models.py:113:    server_id: str
/app/backend/modules/sync_historicos/models.py:150:            'server_id': self.server_id,
/app/backend/modules/sync_historicos/models.py:167:    server_id: str
/app/backend/modules/sync_historicos/models.py:214:    server_id: Optional[str]  # None si es todos
/app/backend/modules/sync_historicos/models.py:251:    server_ids: Optional[List[str]] = None  # None = todos
/app/backend/modules/sync_historicos/sync_ventas.py:29:    server_ids: Optional[List[str]] = None,
/app/backend/modules/sync_historicos/sync_ventas.py:40:        server_ids: Lista de IDs de servidores (None = todos)
/app/backend/modules/sync_historicos/sync_ventas.py:50:        f"Servidores: {server_ids or 'TODOS'}, "
/app/backend/modules/sync_historicos/sync_ventas.py:56:        server_ids=server_ids,
/app/backend/modules/sync_historicos/sync_ventas.py:68:    server_ids: List[str],  # OBLIGATORIO especificar servidores
/app/backend/modules/sync_historicos/sync_ventas.py:79:        server_ids: Lista de IDs de servidores (OBLIGATORIO)
/app/backend/modules/sync_historicos/sync_ventas.py:87:    if not server_ids:
/app/backend/modules/sync_historicos/sync_ventas.py:88:        raise ValueError("Debe especificar server_ids para escritura real")
/app/backend/modules/sync_historicos/sync_ventas.py:92:        f"Servidores: {server_ids}, "
/app/backend/modules/sync_historicos/sync_ventas.py:98:        server_ids=server_ids,
/app/backend/modules/sync_historicos/sync_ventas.py:127:    from core.db import execute_sql_query
/app/backend/modules/sync_historicos/sync_ventas.py:149:            result = execute_sql_query(
/app/backend/modules/sync_historicos/sync_ventas.py:164:            count = execute_sql_query(
/app/backend/modules/sync_historicos/sync_ventas.py:175:            count = execute_sql_query(
/app/backend/modules/sync_historicos/sync_ventas.py:186:            count = execute_sql_query(
/app/backend/modules/sync_historicos/sync_ventas.py:207:    server_ids: Optional[List[str]] = None,
/app/backend/modules/sync_historicos/sync_ventas.py:217:        f"Servidores: {server_ids or 'TODOS'}, "
/app/backend/modules/sync_historicos/sync_ventas.py:222:        server_ids=server_ids,
/app/backend/modules/sync_historicos/sync_ventas.py:234:    server_ids: List[str],
/app/backend/modules/sync_historicos/sync_ventas.py:242:    if not server_ids:
/app/backend/modules/sync_historicos/sync_ventas.py:243:        raise ValueError("Debe especificar server_ids para escritura real")
/app/backend/modules/sync_historicos/sync_ventas.py:247:        f"Servidores: {server_ids}, "
/app/backend/modules/sync_historicos/sync_ventas.py:252:        server_ids=server_ids,
/app/backend/modules/sync_historicos/sync_ventas.py:268:    server_ids: Optional[List[str]] = None,
/app/backend/modules/sync_historicos/sync_ventas.py:278:        f"Servidores: {server_ids or 'TODOS'}, "
/app/backend/modules/sync_historicos/sync_ventas.py:283:        server_ids=server_ids,
/app/backend/modules/sync_historicos/sync_ventas.py:295:    server_ids: List[str],
/app/backend/modules/sync_historicos/sync_ventas.py:303:    if not server_ids:
/app/backend/modules/sync_historicos/sync_ventas.py:304:        raise ValueError("Debe especificar server_ids para escritura real")
/app/backend/modules/sync_historicos/sync_ventas.py:308:        f"Servidores: {server_ids}, "
/app/backend/modules/sync_historicos/sync_ventas.py:313:        server_ids=server_ids,
/app/backend/modules/automatizacion/repository.py:43:    server_id: Optional[str] = None
/app/backend/modules/automatizacion/repository.py:51:        server_id: Filtrar por servidor específico (opcional)
/app/backend/modules/automatizacion/repository.py:59:            server_id,
/app/backend/modules/automatizacion/repository.py:71:    if server_id:
/app/backend/modules/automatizacion/repository.py:72:        query += f" AND server_id = '{server_id}'"
/app/backend/modules/automatizacion/repository.py:74:    query += " ORDER BY server_id, sucursal_id, almacen_id"
/app/backend/modules/automatizacion/repository.py:94:    server_id: str
/app/backend/modules/automatizacion/repository.py:104:        server_id: UUID del servidor
/app/backend/modules/automatizacion/repository.py:112:            server_id,
/app/backend/modules/automatizacion/repository.py:124:          AND server_id = '{server_id}'
/app/backend/modules/automatizacion/repository.py:140:    server_id: str,
/app/backend/modules/automatizacion/repository.py:156:        server_id or "",
/app/backend/modules/automatizacion/repository.py:169:    server_id: str,
/app/backend/modules/automatizacion/repository.py:184:        sistema_origen, server_id, sucursal_id, almacen_id,
/app/backend/modules/automatizacion/repository.py:191:            folio.get('server_id'),
/app/backend/modules/automatizacion/repository.py:221:    server_id: str,
/app/backend/modules/automatizacion/repository.py:234:        server_id or "",
/app/backend/modules/automatizacion/repository.py:253:    server_id: str,
/app/backend/modules/automatizacion/repository.py:273:            server_id,
/app/backend/modules/automatizacion/repository.py:285:          AND server_id = %s
/app/backend/modules/automatizacion/repository.py:296:        server_id,
/app/backend/modules/automatizacion/repository.py:345:            server=host_clean,
/app/backend/modules/automatizacion/repository.py:349:            database=database,
/app/backend/modules/automatizacion/repository.py:382:    server_id: str,
/app/backend/modules/automatizacion/repository.py:403:        sistema_origen, server_id, sucursal_id, almacen_id,
/app/backend/modules/automatizacion/repository.py:412:            server_id,
/app/backend/modules/automatizacion/repository.py:438:        server_id,
/app/backend/modules/automatizacion/repository.py:624:            id, server_id, sucursal_id, almacen_id,
/app/backend/modules/automatizacion/repository.py:676:    server_id: str,
/app/backend/modules/automatizacion/repository.py:689:        WHERE server_id = '{server_id}'
/app/backend/modules/automatizacion/schemas.py:39:    server_id: str = Field(..., max_length=50)
/app/backend/modules/automatizacion/schemas.py:71:    server_id: str = Field(..., max_length=50)
/app/backend/modules/automatizacion/schemas.py:109:    (sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario, fecha_inventario)
/app/backend/modules/automatizacion/schemas.py:112:    server_id: str = Field(..., max_length=50)
/app/backend/modules/automatizacion/schemas.py:213:    (sistema_origen, server_id, sucursal_id, almacen_id)
/app/backend/modules/automatizacion/schemas.py:216:    server_id: str = Field(..., max_length=50)
/app/backend/modules/auth/service.py:375:            server='<REDACTED_EDARSAHUB_SQL_HOST>',
/app/backend/modules/auth/service.py:379:            database='EDARSAHUB'
/app/backend/modules/auth/password_reset.py:56:        server='<REDACTED_EDARSAHUB_SQL_HOST>',
/app/backend/modules/auth/password_reset.py:60:        database='EDARSAHUB'
/app/backend/modules/auth/repository.py:29:def init_auth_repository(database=None) -> None:
/app/backend/modules/auth/repository.py:102:            server='<REDACTED_EDARSAHUB_SQL_HOST>',
/app/backend/modules/auth/repository.py:106:            database='EDARSAHUB'
/app/backend/modules/auth/repository.py:314:        server='<REDACTED_EDARSAHUB_SQL_HOST>',
/app/backend/modules/auth/repository.py:316:        database='EDARSAHUB',
/app/backend/modules/auth/context_service.py:48:        server='<REDACTED_EDARSAHUB_SQL_HOST>',
/app/backend/modules/auth/context_service.py:52:        database='EDARSAHUB'
/app/backend/modules/auth/context_service.py:273:        server_id = row[0]
/app/backend/modules/auth/context_service.py:275:        if server_id not in result:
/app/backend/modules/auth/context_service.py:276:            result[server_id] = []
/app/backend/modules/auth/context_service.py:277:        result[server_id].append(suc_codigo)
/app/backend/modules/auth/schemas.py:34:    allowed_sucursales: Dict[str, List[str]] = {}  # server_id -> [sucursal_ids]
/app/backend/modules/auth/schemas.py:35:    allowed_warehouses: Dict[str, List[str]] = {}  # server_id -> [warehouse_codes]
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:26:from core.db import execute_sql_query
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:61:def get_server_connection_config(server_id: str) -> Optional[Dict[str, Any]]:
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:90:    WHERE id = '{server_id}'
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:94:        result = execute_sql_query(
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:134:        logger.error(f"Error obteniendo config de servidor {server_id}: {e}")
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:146:    IMPORTANTE: execute_sql_query retorna [] tanto para errores como para 
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:163:        result = execute_sql_query(
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:172:        # execute_sql_query retorna [] tanto para error como para consulta vacía.
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:184:        test_result = execute_sql_query(host, port, database, username, password, test_query)
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:286:        server_config = get_server_connection_config(config.server_id)
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:288:            result.error_message = f"No se encontró configuración para server_id {config.server_id}"
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:305:                server_id=config.server_id,
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:351:            server_id=config.server_id,
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:393:        server_config = get_server_connection_config(config.server_id)
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:395:            result.error_message = f"No se encontró configuración para server_id {config.server_id}"
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:413:                server_id=config.server_id,
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:429:            server_id=config.server_id,
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:471:            server_id=config.server_id,
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:546:            sucursales = get_sucursales_mpro(config.server_id)
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:551:                    server_id=config.server_id,
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:588:        server_id='a5ff0e25-f029-43db-b634-d4ac814c904f',
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:616:        server_id='1b230a06-ffaf-4c70-bd27-b1be3579dea6',
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:42:from core.db import execute_sql_query, parse_sql_server_host
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:90:        'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b',  # ID correcto de EDARSAHUB
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:97:        'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f',  # ID correcto de EDARSAHUB
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:104:        'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6',  # ID correcto de EDARSAHUB
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:111:        'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',  # ID correcto de EDARSAHUB (ManagmentPro)
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:118:        'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',  # ID correcto de EDARSAHUB (ManagmentPro)
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:133:    server_id: str
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:177:def get_server_connection(server_id: str) -> Optional[Dict[str, Any]]:
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:194:    WHERE id = '{server_id}'
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:198:        result = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:207:            logger.error(f"No se encontró servidor {server_id}")
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:240:        logger.error(f"Error obteniendo config de servidor {server_id}: {e}")
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:293:        server_id=unidad['server_id'],
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:301:    server = get_server_connection(unidad['server_id'])
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:316:        rows = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:359:                unidad['server_id'],
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:374:                server_id=unidad['server_id'],
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:432:        server_id=unidad['server_id'],
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:461:        server_id=unidad['server_id'],
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:469:    server = get_server_connection(unidad['server_id'])
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:485:        rows = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:528:                unidad['server_id'],
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:543:                server_id=unidad['server_id'],
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:601:        server_id=unidad['server_id'],
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:646:        result = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:721:        result = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:852:        result = execute_sql_query(
/app/backend/modules/comercial_v2/repository_readonly.py:25:from core.db import execute_sql_query
/app/backend/modules/comercial_v2/repository_readonly.py:46:        result = execute_sql_query(
/app/backend/modules/comercial_v2/repository_readonly.py:95:        server_id,
/app/backend/modules/comercial_v2/repository_readonly.py:356:            server_id,
/app/backend/modules/comercial_v2/repository_readonly.py:380:        server_id,
/app/backend/modules/comercial_v2/repository_readonly.py:427:        server_id,
/app/backend/modules/comercial_v2/repository_readonly.py:495:        server_id,
/app/backend/modules/comercial_v2/repository_readonly.py:502:    GROUP BY unidad_negocio_id, unidad_negocio_nombre, sistema_origen, server_id
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:23:from core.db import execute_sql_query
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:54:        result = execute_sql_query(
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:82:        id as server_id,
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:117:            server_id=str(row['server_id']),  # Convertir UUID a string
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:127:def get_sucursales_mpro(server_id: str) -> List[Dict[str, str]]:
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:130:    MPRO tiene múltiples sucursales en un solo server_id.
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:209:            id, unidad_negocio_id, unidad_negocio_nombre, server_id, sucursal_id,
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:220:            '{kpi.server_id}', 
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:412:            server_id = '{ventas.server_id}',
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:434:            id, unidad_negocio_id, unidad_negocio_nombre, server_id, sucursal_id,
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:443:            '{ventas.server_id}',
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:473:        unidad_negocio_id, server_id, sucursal_id,
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:485:        {f"'{log.server_id}'" if log.server_id else 'NULL'},
/app/backend/modules/comercial_v2/mappers.py:33:    server_id: str,
/app/backend/modules/comercial_v2/mappers.py:45:    - server_id + sucursal_id + fecha + ventas + tickets + pax
/app/backend/modules/comercial_v2/mappers.py:47:    data_string = f"{server_id}|{sucursal_id}|{fecha.isoformat()}|{ventas_total}|{tickets_total}|{pax_total}"
/app/backend/modules/comercial_v2/mappers.py:52:    server_id: str,
/app/backend/modules/comercial_v2/mappers.py:61:    data_string = f"{server_id}|{sucursal_id}|{snapshot_timestamp.isoformat()}|{ventas_abiertas}"
/app/backend/modules/comercial_v2/mappers.py:101:        config.server_id,
/app/backend/modules/comercial_v2/mappers.py:112:        server_id=config.server_id,
/app/backend/modules/comercial_v2/mappers.py:174:        server_id=config.server_id,
/app/backend/modules/comercial_v2/mappers.py:232:        config.server_id,
/app/backend/modules/comercial_v2/mappers.py:243:        server_id=config.server_id,
/app/backend/modules/comercial_v2/mappers.py:305:        server_id=config.server_id,
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:46:from core.db import execute_sql_query, parse_sql_server_host, reset_server_cache
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:103:        'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b',
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:111:        'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f',
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:119:        'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6',
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:127:        'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:135:        'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:225:def get_server_connection(server_id: str) -> Optional[Dict[str, Any]]:
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:231:    WHERE id = '{server_id}'
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:235:        result = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:271:        logger.error(f"Error obteniendo config de servidor {server_id}: {e}")
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:326:    server = get_server_connection(unidad['server_id'])
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:339:        rows = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:381:                unidad['server_id'],
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:392:                server_id=unidad['server_id'],
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:475:    server = get_server_connection(unidad['server_id'])
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:489:        rows = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:529:                unidad['server_id'],
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:540:                server_id=unidad['server_id'],
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:661:        server_id="MULTIPLE",
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:710:    result = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:739:    result = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:777:    result = execute_sql_query(
/app/backend/modules/comercial_v2/routes.py:1270:                "server_id": d.get('server_id'),
/app/backend/modules/comercial_v2/schemas.py:62:    server_id: str
/app/backend/modules/comercial_v2/schemas.py:85:    server_id: str
/app/backend/modules/comercial_v2/schemas.py:107:    server_id: str
/app/backend/modules/comercial_v2/schemas.py:155:    server_id: str
/app/backend/modules/comercial_v2/schemas.py:190:    server_id: Optional[str] = None
/app/backend/modules/comercial_v2/schemas.py:221:    server_id: str
/app/backend/modules/tablajeria/ordenes_service.py:40:            server=self.db_config['host'],
/app/backend/modules/tablajeria/ordenes_service.py:42:            database=self.db_config['database'],
/app/backend/modules/tablajeria/dashboard_service.py:28:            server=self.db_config.get('host'),
/app/backend/modules/tablajeria/dashboard_service.py:30:            database=self.db_config.get('database'),
/app/backend/modules/tablajeria/fase6_service.py:82:            server=self.db_config['host'],
/app/backend/modules/tablajeria/fase6_service.py:84:            database=self.db_config['database'],
/app/backend/modules/tablajeria/sync_service.py:44:            server=self.db_config['host'],
/app/backend/modules/tablajeria/sync_service.py:46:            database=self.db_config['database'],
/app/backend/modules/tablajeria/sync_service.py:162:                server=servidor_config['host'],
/app/backend/modules/tablajeria/sync_service.py:164:                database=servidor_config['database_name'],
/app/backend/modules/tablajeria/sync_service.py:593:                server=f"{server},{port}",
/app/backend/modules/tablajeria/sync_service.py:594:                database=servidor_config['database_name'],
/app/backend/modules/tablajeria/routes.py:51:        server=DB_CONFIG['host'],
/app/backend/modules/tablajeria/routes.py:53:        database=DB_CONFIG['database'],
/app/backend/modules/universal_query/routes.py:160:async def get_server_and_validate(server_id: str, db=None) -> Dict:
/app/backend/modules/universal_query/routes.py:171:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/modules/universal_query/routes.py:174:    server = get_server_connection_info_with_secrets(server_id)
/app/backend/modules/universal_query/routes.py:185:            server=server.get('host'),
/app/backend/modules/universal_query/routes.py:189:            database=server.get('database'),
/app/backend/modules/universal_query/routes.py:232:@router.post("/servers/{server_id}/universal-query-test")
/app/backend/modules/universal_query/routes.py:234:    server_id: str,
/app/backend/modules/universal_query/routes.py:251:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/modules/universal_query/routes.py:256:    server = get_server_connection_info_with_secrets(server_id)
/app/backend/modules/universal_query/routes.py:268:            "id": server_id,
/app/backend/modules/sync_recetas/models.py:15:    server_ids: List[str]
/app/backend/modules/sync_recetas/sync_recetas.py:20:from core.db import execute_sql_query
/app/backend/modules/sync_recetas/sync_recetas.py:41:    server_ids: List[str] = None,
/app/backend/modules/sync_recetas/sync_recetas.py:53:        server_ids=server_ids or [],
/app/backend/modules/sync_recetas/sync_recetas.py:65:    server_ids: List[str],
/app/backend/modules/sync_recetas/sync_recetas.py:76:    if not server_ids:
/app/backend/modules/sync_recetas/sync_recetas.py:77:        raise ValueError("server_ids es requerido para sincronización real")
/app/backend/modules/sync_recetas/sync_recetas.py:80:        server_ids=server_ids,
/app/backend/modules/sync_recetas/sync_recetas.py:110:        if config.server_ids:
/app/backend/modules/sync_recetas/sync_recetas.py:111:            servers = [_get_server_by_id_from_sql(sid) for sid in config.server_ids]
/app/backend/modules/sync_recetas/sync_recetas.py:121:            server_id = server.get('id')
/app/backend/modules/sync_recetas/sync_recetas.py:127:                    server=server,
/app/backend/modules/sync_recetas/sync_recetas.py:132:                result.resultados_por_servidor[server_id] = server_result
/app/backend/modules/sync_recetas/sync_recetas.py:156:                result.resultados_por_servidor[server_id] = {
/app/backend/modules/sync_recetas/sync_recetas.py:183:    server_id = server.get('id')
/app/backend/modules/sync_recetas/sync_recetas.py:196:        'server_id': server_id,
/app/backend/modules/sync_recetas/sync_recetas.py:216:            server_id=server_id,
/app/backend/modules/sync_recetas/sync_recetas.py:217:            host=host, port=port, database=database,
/app/backend/modules/sync_recetas/sync_recetas.py:226:            server_id=server_id,
/app/backend/modules/sync_recetas/sync_recetas.py:227:            host=host, port=port, database=database,
/app/backend/modules/sync_recetas/sync_recetas.py:245:    server_id: str,
/app/backend/modules/sync_recetas/sync_recetas.py:261:            _guardar_familias(server_id, system_type, familias, sync_run_id, result)
/app/backend/modules/sync_recetas/sync_recetas.py:269:            _guardar_subfamilias(server_id, system_type, subfamilias, sync_run_id, result)
/app/backend/modules/sync_recetas/sync_recetas.py:277:            _guardar_insumos(server_id, system_type, insumos, sync_run_id, result)
/app/backend/modules/sync_recetas/sync_recetas.py:289:            _guardar_productos(server_id, system_type, productos, sync_run_id, result)
/app/backend/modules/sync_recetas/sync_recetas.py:297:            _guardar_recetas(server_id, system_type, recetas, sync_run_id, result)
/app/backend/modules/sync_recetas/sync_recetas.py:305:            _guardar_elaborados(server_id, system_type, elaborados, sync_run_id, result)
/app/backend/modules/sync_recetas/sync_recetas.py:316:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:340:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:362:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:394:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:417:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:436:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:474:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:502:    server_id: str,
/app/backend/modules/sync_recetas/sync_recetas.py:518:            _guardar_familias(server_id, system_type, familias, sync_run_id, result)
/app/backend/modules/sync_recetas/sync_recetas.py:526:            _guardar_subfamilias(server_id, system_type, subfamilias, sync_run_id, result)
/app/backend/modules/sync_recetas/sync_recetas.py:534:            _guardar_insumos(server_id, system_type, insumos, sync_run_id, result)
/app/backend/modules/sync_recetas/sync_recetas.py:546:            _guardar_productos(server_id, system_type, productos, sync_run_id, result)
/app/backend/modules/sync_recetas/sync_recetas.py:554:            _guardar_recetas(server_id, system_type, recetas, sync_run_id, result)
/app/backend/modules/sync_recetas/sync_recetas.py:565:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:584:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:606:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:700:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:752:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:769:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:796:def _guardar_familias(server_id: str, system_type: str, familias: List[FamiliaSync], 
/app/backend/modules/sync_recetas/sync_recetas.py:804:            USING (SELECT '{server_id}' as ServerID, '{fam.codigo_fuente}' as CodigoFuente) AS source
/app/backend/modules/sync_recetas/sync_recetas.py:819:                    CAST('{server_id}' AS UNIQUEIDENTIFIER),
/app/backend/modules/sync_recetas/sync_recetas.py:829:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:843:def _guardar_subfamilias(server_id: str, system_type: str, subfamilias: List[SubFamiliaSync],
/app/backend/modules/sync_recetas/sync_recetas.py:850:            USING (SELECT '{server_id}' as ServerID, '{sf.codigo_fuente}' as CodigoFuente) AS source
/app/backend/modules/sync_recetas/sync_recetas.py:864:                    CAST('{server_id}' AS UNIQUEIDENTIFIER),
/app/backend/modules/sync_recetas/sync_recetas.py:873:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:887:def _guardar_insumos(server_id: str, system_type: str, insumos: List[InsumoSync],
/app/backend/modules/sync_recetas/sync_recetas.py:895:            USING (SELECT '{server_id}' as ServerID, '{ins.codigo_fuente}' as CodigoFuente) AS source
/app/backend/modules/sync_recetas/sync_recetas.py:918:                    CAST('{server_id}' AS UNIQUEIDENTIFIER),
/app/backend/modules/sync_recetas/sync_recetas.py:931:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:946:def _guardar_productos(server_id: str, system_type: str, productos: List[ProductoSync],
/app/backend/modules/sync_recetas/sync_recetas.py:959:            USING (SELECT '{server_id}' as ServerID, '{prod.codigo_fuente}' as CodigoFuente) AS source
/app/backend/modules/sync_recetas/sync_recetas.py:980:                    CAST('{server_id}' AS UNIQUEIDENTIFIER),
/app/backend/modules/sync_recetas/sync_recetas.py:992:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:1007:def _guardar_recetas(server_id: str, system_type: str, recetas: List[RecetaLineaSync],
/app/backend/modules/sync_recetas/sync_recetas.py:1018:            USING (SELECT '{server_id}' as ServerID, 
/app/backend/modules/sync_recetas/sync_recetas.py:1045:                    CAST('{server_id}' AS UNIQUEIDENTIFIER),
/app/backend/modules/sync_recetas/sync_recetas.py:1059:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:1082:                    WHERE ServerID = CAST('{server_id}' AS UNIQUEIDENTIFIER)
/app/backend/modules/sync_recetas/sync_recetas.py:1085:            WHERE ServerID = CAST('{server_id}' AS UNIQUEIDENTIFIER)
/app/backend/modules/sync_recetas/sync_recetas.py:1088:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:1100:def _guardar_elaborados(server_id: str, system_type: str, elaborados: List[ElaboradoLineaSync],
/app/backend/modules/sync_recetas/sync_recetas.py:1109:            USING (SELECT '{server_id}' as ServerID, 
/app/backend/modules/sync_recetas/sync_recetas.py:1132:                    CAST('{server_id}' AS UNIQUEIDENTIFIER),
/app/backend/modules/sync_recetas/sync_recetas.py:1143:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:1180:        execute_sql_query(
/app/backend/modules/crm/automation_service.py:32:            server=self.db_config['host'],
/app/backend/modules/crm/automation_service.py:35:            database=self.db_config['database'],
/app/backend/modules/crm/comercial_routes.py:185:            server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/modules/crm/comercial_routes.py:189:            database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB')
/app/backend/modules/crm/trigger_service.py:74:            server=self.db_config['host'],
/app/backend/modules/crm/trigger_service.py:77:            database=self.db_config['database'],
/app/backend/modules/crm/comercial_service.py:34:            server=self.db_config['host'],
/app/backend/modules/crm/comercial_service.py:36:            database=self.db_config['database'],
/app/backend/modules/crm/repository.py:33:        server=EDARSAHUB_CONFIG['host'],
/app/backend/modules/crm/repository.py:35:        database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/crm/native_routes.py:82:            server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/modules/crm/native_routes.py:86:            database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB')
/app/backend/modules/crm/native_routes.py:312:            server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/modules/crm/native_routes.py:316:            database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB')
/app/backend/modules/crm/native_routes.py:423:            server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/modules/crm/native_routes.py:427:            database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB')
/app/backend/modules/crm/sql/execute_crm_migration.py:69:            server=EDARSAHUB_CONFIG['host'],
/app/backend/modules/crm/sql/execute_crm_migration.py:71:            database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/crm/sql/execute_crm_migration.py:167:            server=EDARSAHUB_CONFIG['host'],
/app/backend/modules/crm/sql/execute_crm_migration.py:169:            database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/crm/integration/staging_processor.py:77:            server=self.db_config['host'],
/app/backend/modules/crm/integration/staging_processor.py:79:            database=self.db_config['database'],
/app/backend/modules/crm/integration/staging_service.py:34:            server=self.db_config['host'],
/app/backend/modules/crm/integration/staging_service.py:36:            database=self.db_config['database'],
/app/backend/modules/crm/integration_routes.py:86:        server=DB_CONFIG['host'],
/app/backend/modules/crm/integration_routes.py:88:        database=DB_CONFIG['database'],
/app/backend/modules/finanzas/sql_subprocess_helper.py:19:        database='mydatabase',
/app/backend/modules/finanzas/sql_subprocess_helper.py:296:            database=conn['database'],
/app/backend/modules/finanzas/repository_bancarios.py:18:from core.db import execute_sql_query
/app/backend/modules/finanzas/repository_bancarios.py:50:        result = execute_sql_query(
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:54:        str(data.get('server_id', '')),
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:263:                data.get('server_id'),
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:739:            'server_id': row['ServerID'],
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:893:    # RESOLUCIÓN SERVER_ID → UNIDAD_NEGOCIO_ID
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:897:    def resolver_server_id_a_unidad(self, server_id: str) -> Optional[Dict]:
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:899:        Resuelve server_id (UUID) a UnidadNegocioID usando EDARSAHUB SQL.
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:902:        server_id → Servidores_Conexiones → Sistema_SucursalServidorMapeo → Sistema_Sucursales
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:905:            server_id: UUID del servidor (frontend)
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:911:        if not server_id:
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:918:            # Primero buscar si el server_id coincide directamente con UnidadNegocioID
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:919:            # (en algunos casos server_id = unidad_negocio_id)
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:927:            ''', (server_id,))
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:931:                logger.debug(f"[CUADRES_Z] server_id={server_id} resuelto desde Finanzas_CuadresZ")
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:950:            ''', (server_id,))
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:956:                logger.debug(f"[CUADRES_Z] server_id={server_id} resuelto desde Servidores_Conexiones: {unidad_id}")
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:963:            logger.warning(f"[CUADRES_Z] server_id={server_id} no encontrado en EDARSAHUB")
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:967:            logger.error(f"[CUADRES_Z] Error resolviendo server_id={server_id}: {e}")
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:972:    def listar_cuadres_z_por_server_id(self, server_id: str, filtros: Dict = None) -> List[Dict]:
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:974:        Lista Cuadres Z filtrando por server_id.
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:977:        que envía server_id en lugar de unidad_negocio_id.
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:980:            server_id: UUID del servidor
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:993:            params = [server_id]
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:1038:    def obtener_resumen_por_server_id(self, server_id: str, filtros: Dict = None) -> Dict:
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:1040:        Obtiene resumen de Cuadres Z para un server_id específico.
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:1045:            server_id: UUID del servidor
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:1058:            params = [server_id]
/app/backend/modules/finanzas/tesoreria.py:99:    server_id: Optional[str] = Query(None, description="Filtrar por server_id (UUID)"),
/app/backend/modules/finanzas/tesoreria.py:126:        if server_id:
/app/backend/modules/finanzas/tesoreria.py:129:                cortes = repo_cortes.listar_cortes_por_server_id(
/app/backend/modules/finanzas/tesoreria.py:130:                    server_id=server_id,
/app/backend/modules/finanzas/tesoreria.py:144:                logger.error(f"[CORTES_Z_SQL] Error conexión EDARSAHUB (server_id={server_id}): {e}")
/app/backend/modules/finanzas/tesoreria.py:289:    server_id: Optional[str] = Query(None, description="Filtrar por server_id (UUID de unidad de negocio)"),
/app/backend/modules/finanzas/tesoreria.py:302:    - server_id se resuelve desde EDARSAHUB SQL
/app/backend/modules/finanzas/tesoreria.py:320:        # Filtrar por server_id o unidad_negocio_id (SQL directo, sin MongoDB)
/app/backend/modules/finanzas/tesoreria.py:321:        if server_id:
/app/backend/modules/finanzas/tesoreria.py:322:            logger.info(f"[CUADRES_SQL] Filtrando por server_id={server_id}")
/app/backend/modules/finanzas/tesoreria.py:323:            cuadres = repo.listar_cuadres_z_por_server_id(server_id, filtros)
/app/backend/modules/finanzas/tesoreria.py:337:                "server_id": server_id,
/app/backend/modules/finanzas/tesoreria.py:350:    server_id: Optional[str] = Query(None, description="Filtrar por server_id (UUID de unidad de negocio)"),
/app/backend/modules/finanzas/tesoreria.py:370:        if server_id:
/app/backend/modules/finanzas/tesoreria.py:371:            logger.info(f"[RESUMEN_SQL] Obteniendo resumen para server_id={server_id}")
/app/backend/modules/finanzas/tesoreria.py:372:            resultado = repo.obtener_resumen_por_server_id(server_id, filtros)
/app/backend/modules/finanzas/tesoreria.py:393:                "server_id": server_id
/app/backend/modules/finanzas/tesoreria.py:461:            'unidad_negocio_id': corte_z.get('sucursal_id') or corte_z.get('server_id'),
/app/backend/modules/finanzas/tesoreria.py:464:            'server_id': corte_z.get('server_id') or corte_z.get('sucursal_id'),
/app/backend/modules/finanzas/tesoreria.py:761:        from core.db import execute_sql_query
/app/backend/modules/finanzas/tesoreria.py:782:        results = execute_sql_query(
/app/backend/modules/finanzas/sync_propinas_mpro.py:86:        server=EDARSAHUB_CONFIG['server'],
/app/backend/modules/finanzas/sync_propinas_mpro.py:88:        database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/finanzas/sync_propinas_mpro.py:112:                u.server_id,
/app/backend/modules/finanzas/sync_propinas_mpro.py:122:                ON CAST(u.server_id AS NVARCHAR(100)) = CAST(s.id AS NVARCHAR(100))
/app/backend/modules/finanzas/sync_propinas_mpro.py:149:            'server_id': str(unidad['server_id']),
/app/backend/modules/finanzas/sync_propinas_mpro.py:166:def get_mpro_connection(conn_info: Dict):
/app/backend/modules/finanzas/sync_propinas_mpro.py:169:        server=conn_info['host'],
/app/backend/modules/finanzas/sync_propinas_mpro.py:171:        database=conn_info['database'],
/app/backend/modules/finanzas/sync_propinas_mpro.py:235:        mpro_conn = get_mpro_connection(conn_info)
/app/backend/modules/finanzas/sync_propinas_mpro.py:300:                'ServerID': conn_info['server_id'],
/app/backend/modules/finanzas/sync_propinas_mpro.py:408:                            server_id, sucursal_id, folio_corte, fecha_corte,
/app/backend/modules/finanzas/sync_propinas_mpro.py:510:            conn_info['server_id'],
/app/backend/modules/finanzas/sync_propinas_mpro.py:588:        'server_id': conn_info['server_id'],
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:59:        server=EDARSAHUB_CONFIG['server'],
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:61:        database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:106:                u.server_id,
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:116:                ON CAST(u.server_id AS NVARCHAR(100)) = CAST(s.id AS NVARCHAR(100))
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:150:            'server_id': str(unidad['server_id']),
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:166:def get_softrestaurant_connection(conn_info: Dict):
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:188:            server=host,
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:190:            database=database,
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:206:            server=server_string,
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:208:            database=database,
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:301:        sr_conn = get_softrestaurant_connection(conn_info)
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:337:                'ServerID': conn_info['server_id'],
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:531:    server_id: str,
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:565:            unidad_id, server_id, sistema_origen,
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:639:        resultado['server_id'] = conn_info['server_id']
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:661:            server_id=conn_info['server_id'],
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:679:            if 'server_id' in resultado:
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:682:                    server_id=resultado.get('server_id', ''),
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:81:        server=EDARSAHUB_CONFIG['server'],
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:83:        database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:117:                u.server_id,
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:127:                ON CAST(u.server_id AS NVARCHAR(100)) = CAST(s.id AS NVARCHAR(100))
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:157:            'server_id': str(unidad['server_id']),
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:173:def get_softrestaurant_connection(conn_info: Dict):
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:189:            server=host,
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:191:            database=database,
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:205:            server=server_string,
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:207:            database=database,
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:295:        sr_conn = get_softrestaurant_connection(conn_info)
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:350:                'ServerID': conn_info['server_id'],
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:381:                'sucursal_id': conn_info.get('unidad_codigo', conn_info['server_id']),
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:463:                            server_id, sucursal_id, folio_corte, fecha_corte,
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:566:            conn_info['server_id'],
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:648:        'server_id': conn_info['server_id'],
/app/backend/modules/finanzas/repository_ingresos_edarsahub.py:46:        server=EDARSAHUB_CONFIG['server'],
/app/backend/modules/finanzas/repository_ingresos_edarsahub.py:48:        database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/finanzas/health.py:19:from core.server_registry import list_servers, get_server_connection_info, EDARSAHUB_CONFIG
/app/backend/modules/finanzas/health.py:20:from core.db import execute_sql_query, sql_health_check
/app/backend/modules/finanzas/health.py:62:        existing = execute_sql_query(
/app/backend/modules/finanzas/health.py:106:async def check_server_connectivity(server_id: str, server_name: str, system_type: str) -> Dict[str, Any]:
/app/backend/modules/finanzas/health.py:113:        "server_id": server_id,
/app/backend/modules/finanzas/health.py:124:        config = await get_server_connection_info(server_id, db=db)
/app/backend/modules/finanzas/health.py:150:                    test_result = execute_sql_query(
/app/backend/modules/finanzas/health.py:175:        logger.error(f"Error verificando servidor {server_id}: {e}")
/app/backend/modules/finanzas/health.py:425:@router.get("/servers/{server_id}")
/app/backend/modules/finanzas/health.py:427:    server_id: str,
/app/backend/modules/finanzas/health.py:436:    config = await get_server_connection_info(server_id, db=db)
/app/backend/modules/finanzas/health.py:440:            "server_id": server_id,
/app/backend/modules/finanzas/health.py:449:        server_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:1127:            from modules.finanzas.repository_mpro import MPRO_SERVER_ID
/app/backend/modules/finanzas/cuentas_por_pagar.py:1128:            config = await get_sucursales_visibles_config(MPRO_SERVER_ID)
/app/backend/modules/finanzas/repository_real.py:19:from core.db import execute_sql_query, sql_health_check, ResilientConfig
/app/backend/modules/finanzas/repository_real.py:25:EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"
/app/backend/modules/finanzas/repository_real.py:61:            'id': EDARSA_HUB_SERVER_ID,
/app/backend/modules/finanzas/repository_real.py:94:            results = execute_sql_query(
/app/backend/modules/finanzas/repository_real.py:97:                database=server['database'],
/app/backend/modules/finanzas/repository_cortes_z.py:22:from core.db import execute_sql_query
/app/backend/modules/finanzas/repository_cortes_z.py:38:    async def _get_server_config(self, server_id: str) -> Optional[Dict]:
/app/backend/modules/finanzas/repository_cortes_z.py:43:            server_id: UUID del servidor en MongoDB/EDARSAHUB
/app/backend/modules/finanzas/repository_cortes_z.py:50:            from core.server_registry import get_server_connection_info
/app/backend/modules/finanzas/repository_cortes_z.py:54:            config = await get_server_connection_info(server_id, db=db)
/app/backend/modules/finanzas/repository_cortes_z.py:57:                self.logger.warning(f"Servidor {server_id} no encontrado en registry")
/app/backend/modules/finanzas/repository_cortes_z.py:62:            self.logger.error(f"Error obteniendo config de servidor {server_id}: {e}")
/app/backend/modules/finanzas/repository_cortes_z.py:65:    async def _execute_query_with_server_id(
/app/backend/modules/finanzas/repository_cortes_z.py:67:        server_id: str,
/app/backend/modules/finanzas/repository_cortes_z.py:72:        Ejecuta una query usando el server_id para obtener configuración del registry.
/app/backend/modules/finanzas/repository_cortes_z.py:75:            server_id: UUID del servidor
/app/backend/modules/finanzas/repository_cortes_z.py:85:        config = await self._get_server_config(server_id)
/app/backend/modules/finanzas/repository_cortes_z.py:90:                source_id=server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:91:                error_message=f"Servidor {server_id} no encontrado en registry centralizado"
/app/backend/modules/finanzas/repository_cortes_z.py:96:            results = execute_sql_query(
/app/backend/modules/finanzas/repository_cortes_z.py:99:                database=config['database'],
/app/backend/modules/finanzas/repository_cortes_z.py:113:                    source_id=server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:119:                    source_id=server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:127:            self.logger.error(f"Error ejecutando query en servidor {server_id}: {e}")
/app/backend/modules/finanzas/repository_cortes_z.py:132:                    source_id=server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:138:                    source_id=server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:144:                    source_id=server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:148:    async def get_cortes_z_by_server_id(
/app/backend/modules/finanzas/repository_cortes_z.py:150:        server_id: str,
/app/backend/modules/finanzas/repository_cortes_z.py:156:        Obtiene Cortes Z de un servidor específico usando su server_id.
/app/backend/modules/finanzas/repository_cortes_z.py:160:            server_id: UUID del servidor
/app/backend/modules/finanzas/repository_cortes_z.py:169:        config = await self._get_server_config(server_id)
/app/backend/modules/finanzas/repository_cortes_z.py:174:                source_id=server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:175:                error_message=f"Servidor {server_id} no encontrado"
/app/backend/modules/finanzas/repository_cortes_z.py:179:        server_name = config.get('name', server_id)
/app/backend/modules/finanzas/repository_cortes_z.py:184:                server_id, server_name, config, fecha_inicio, fecha_fin, folio
/app/backend/modules/finanzas/repository_cortes_z.py:188:                server_id, server_name, config, fecha_inicio, fecha_fin
/app/backend/modules/finanzas/repository_cortes_z.py:193:                source_id=server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:199:        server_id: str,
/app/backend/modules/finanzas/repository_cortes_z.py:261:        result = await self._execute_query_with_server_id(server_id, query)
/app/backend/modules/finanzas/repository_cortes_z.py:273:                    'sucursal_id': server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:275:                    'server_id': server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:296:                    source_id=server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:302:                    source_id=server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:310:        server_id: str,
/app/backend/modules/finanzas/repository_cortes_z.py:357:        result = await self._execute_query_with_server_id(server_id, query)
/app/backend/modules/finanzas/repository_cortes_z.py:370:                    'sucursal_id': f"{server_id}_{suc_codigo}" if suc_codigo else server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:373:                    'server_id': server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:394:                    source_id=server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:400:                    source_id=server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:408:        server_ids: List[str],
/app/backend/modules/finanzas/repository_cortes_z.py:416:            server_ids: Lista de UUIDs de servidores
/app/backend/modules/finanzas/repository_cortes_z.py:433:        for server_id in server_ids:
/app/backend/modules/finanzas/repository_cortes_z.py:434:            tasks.append(self.get_cortes_z_by_server_id(server_id, fecha_inicio, fecha_fin))
/app/backend/modules/finanzas/repository_cortes_z.py:440:            server_id = server_ids[i]
/app/backend/modules/finanzas/repository_cortes_z.py:443:                self.logger.error(f"Error consultando servidor {server_id}: {result}")
/app/backend/modules/finanzas/repository_cortes_z.py:445:                    'source_id': server_id,
/app/backend/modules/finanzas/repository_cortes_z.py:494:        Preferir usar get_cortes_z_by_server_id con el UUID.
/app/backend/modules/finanzas/repository_cortes_z.py:496:        self.logger.warning(f"Uso de método legacy get_cortes_z_softrestaurant con nombre '{server_name}'. Migrar a get_cortes_z_by_server_id.")
/app/backend/modules/finanzas/repository_cortes_z.py:498:        # Buscar server_id por nombre
/app/backend/modules/finanzas/repository_cortes_z.py:499:        server_id = await self._find_server_id_by_name(server_name)
/app/backend/modules/finanzas/repository_cortes_z.py:501:        if not server_id:
/app/backend/modules/finanzas/repository_cortes_z.py:505:        result = await self.get_cortes_z_by_server_id(server_id, fecha_inicio, fecha_fin, folio)
/app/backend/modules/finanzas/repository_cortes_z.py:519:        Preferir usar get_cortes_z_by_server_id con el UUID.
/app/backend/modules/finanzas/repository_cortes_z.py:521:        self.logger.warning(f"Uso de método legacy get_cortes_z_mpro con nombre '{server_name}'. Migrar a get_cortes_z_by_server_id.")
/app/backend/modules/finanzas/repository_cortes_z.py:523:        server_id = await self._find_server_id_by_name(server_name)
/app/backend/modules/finanzas/repository_cortes_z.py:525:        if not server_id:
/app/backend/modules/finanzas/repository_cortes_z.py:529:        result = await self.get_cortes_z_by_server_id(server_id, fecha_inicio, fecha_fin)
/app/backend/modules/finanzas/repository_cortes_z.py:545:        server_ids = await self._get_active_server_ids()
/app/backend/modules/finanzas/repository_cortes_z.py:547:        if not server_ids:
/app/backend/modules/finanzas/repository_cortes_z.py:551:        result = await self.get_all_cortes_z_from_servers(server_ids, fecha_inicio, fecha_fin)
/app/backend/modules/finanzas/repository_cortes_z.py:563:        server_ids = await self._get_active_server_ids()
/app/backend/modules/finanzas/repository_cortes_z.py:565:        if not server_ids:
/app/backend/modules/finanzas/repository_cortes_z.py:576:        return await self.get_all_cortes_z_from_servers(server_ids, fecha_inicio, fecha_fin)
/app/backend/modules/finanzas/repository_cortes_z.py:578:    async def _find_server_id_by_name(self, name: str) -> Optional[str]:
/app/backend/modules/finanzas/repository_cortes_z.py:601:    async def _get_active_server_ids(self) -> List[str]:
/app/backend/modules/finanzas/repository_cortes_z.py:612:            server_ids = []
/app/backend/modules/finanzas/repository_cortes_z.py:619:                    server_ids.append(s.get('id'))
/app/backend/modules/finanzas/repository_cortes_z.py:621:            return server_ids
/app/backend/modules/finanzas/historical_kpis_repository.py:50:        server=config["host"],
/app/backend/modules/finanzas/historical_kpis_repository.py:52:        database=config["database"],
/app/backend/modules/finanzas/historical_kpis_repository.py:61:    server_id: str,
/app/backend/modules/finanzas/historical_kpis_repository.py:102:        WHERE server_id = %s AND sucursal_id = %s AND system_type_normalized = %s 
/app/backend/modules/finanzas/historical_kpis_repository.py:105:        cursor.execute(check_sql, (server_id, sucursal_id, system_type, fecha, kpi_tipo))
/app/backend/modules/finanzas/historical_kpis_repository.py:135:                run_id, server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo,
/app/backend/modules/finanzas/historical_kpis_repository.py:151:                run_id, server_id, sucursal_id, system_type, fecha, kpi_tipo,
/app/backend/modules/finanzas/historical_kpis_repository.py:168:        logger.error(f"[UPSERT_ERROR] server={server_id} fecha={fecha}: {e}")
/app/backend/modules/finanzas/historical_kpis_repository.py:181:                COUNT(DISTINCT server_id) as servers,
/app/backend/modules/finanzas/propinas_tpv/service.py:53:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/service.py:68:            server_id: Opcional - sincronizar solo un servidor
/app/backend/modules/finanzas/propinas_tpv/service.py:80:        # Filtrar por server_id específico si se proporciona
/app/backend/modules/finanzas/propinas_tpv/service.py:81:        if server_id:
/app/backend/modules/finanzas/propinas_tpv/service.py:82:            servers = [s for s in servers if s.get('id') == server_id]
/app/backend/modules/finanzas/propinas_tpv/service.py:105:            server_id_actual = server.get('id')
/app/backend/modules/finanzas/propinas_tpv/service.py:158:                        'server_id': server_id_actual,
/app/backend/modules/finanzas/propinas_tpv/service.py:237:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/service.py:251:            server_id=server_id,
/app/backend/modules/finanzas/propinas_tpv/service.py:261:            server_id=server_id,
/app/backend/modules/finanzas/propinas_tpv/service.py:326:        server_id: Optional[str] = None
/app/backend/modules/finanzas/propinas_tpv/service.py:334:            server_id
/app/backend/modules/finanzas/propinas_tpv/service.py:343:                server_id=server_id,
/app/backend/modules/finanzas/propinas_tpv/service.py:359:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/service.py:366:            server_id=server_id,
/app/backend/modules/finanzas/propinas_tpv/service.py:425:                    'server_id': None,
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:37:        server_id               VARCHAR(50)         NOT NULL,
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:123:            UNIQUE (server_id, sucursal_id, folio_corte, fecha_corte),
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:137:    ON propinas_tpv_control (server_id, fecha_corte DESC);
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:172:        alcance_server_id       VARCHAR(50)         NULL,
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:218:    ON propinas_tpv_config (alcance_tipo, alcance_server_id, activa);
/app/backend/modules/finanzas/propinas_tpv/schema_detector_subprocess.py:9:- Llave: (server_id, estacion_id, folio_corte, fecha_corte)
/app/backend/modules/finanzas/propinas_tpv/schema_detector_subprocess.py:70:                database=server['database'],
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:54:def _get_server_from_registry(server_id: str) -> Optional[Dict]:
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:60:    server = get_server_by_id(server_id)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:226:            server_id=request.server_id,
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:246:    server_id: Optional[str] = Query(None),
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:256:            server_id=server_id
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:271:    server_id: Optional[str] = Query(None),
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:285:            server_id=server_id,
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:306:    server_id: Optional[str] = Query(None),
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:315:            server_id=server_id,
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:460:    "/detectar-esquema/{server_id}",
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:464:    server_id: str,
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:471:        server = _get_server_from_registry(server_id)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:527:                    'server_id': server.get('id'),
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:536:                    'server_id': server.get('id'),
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:567:    server_id: Optional[str] = Query(None),
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:574:        if server_id:
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:575:            server = _get_server_from_registry(server_id)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:600:                'server_id': server.get('id'),
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:29:from core.db import execute_sql_query
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:37:EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:85:            'id': EDARSA_HUB_SERVER_ID,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:96:        return execute_sql_query(
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:170:        (server_id, sucursal_id, folio_corte, fecha_corte)
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:186:        server_id = self._escape_sql(propina_data['server_id'])
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:198:            {server_id} AS server_id,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:203:        ON target.server_id = source.server_id 
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:239:                id, server_id, sucursal_id, folio_corte, fecha_corte,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:249:                {server_id}, {sucursal_id}, {folio_corte}, {fecha_corte},
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:300:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:319:        if server_id:
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:320:            where_clauses.append(f"server_id = {self._escape_sql(server_id)}")
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:331:            server_id, sucursal_id, folio_corte,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:362:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:376:        if server_id:
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:377:            where_clauses.append(f"server_id = {self._escape_sql(server_id)}")
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:403:            server_id, sucursal_id, folio_corte,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:517:        server_id: Optional[str] = None
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:524:        where_server = f"AND server_id = {self._escape_sql(server_id)}" if server_id else ""
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:576:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:598:                    alcance_tipo, alcance_server_id, alcance_empresa_id, alcance_sucursal_id,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:643:                'server_id': row.get('alcance_server_id'),
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:728:                'server_id': row.get('server_id'),
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:793:                alcance_server_id,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:840:            alcance_server_id,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:854:            {self._escape_sql(config_data.get('alcance_server_id'))},
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:891:            alcance_server_id = {self._escape_sql(config_data.get('alcance_server_id'))},
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:925:                'server_id': row.get('alcance_server_id'),
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:952:                'server_id': None,
/app/backend/modules/finanzas/propinas_tpv/repository_edarsahub.py:85:            server=self.config['server'],
/app/backend/modules/finanzas/propinas_tpv/repository_edarsahub.py:87:            database=self.config['database'],
/app/backend/modules/finanzas/propinas_tpv/repository_edarsahub.py:174:                    id, server_id, sucursal_id, folio_corte, fecha_corte,
/app/backend/modules/finanzas/propinas_tpv/repository_edarsahub.py:539:                    id, server_id, sucursal_id, folio_corte, fecha_corte,
/app/backend/modules/finanzas/propinas_tpv/repository_edarsahub.py:735:            'server_id': row['server_id'],
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:122:        server_id: Optional[str],
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:137:            'server_id': server_id,
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:165:        server_id: Optional[str],
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:181:            'server_id': server_id,
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:199:                            'server_id': server_id,
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:222:        server_id: Optional[str]
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:230:            'server_id': server_id
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:253:        server_id: Optional[str],
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:262:            'server_id': server_id
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:326:        server_id: Optional[str],
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:332:            'server_id': server_id,
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:354:        server_id: Optional[str],
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:361:            'server_id': server_id,
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:386:    async def invalidar_listados(self, server_id: Optional[str] = None):
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:391:            server_id: Si se especifica, solo invalida ese servidor
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:395:            if server_id:
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:396:                filtro['params.server_id'] = server_id
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:404:    async def invalidar_resumenes(self, server_id: Optional[str] = None):
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:408:            if server_id:
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:409:                filtro['params.server_id'] = server_id
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:9:- Llave: (server_id, estacion_id, folio_corte, fecha_corte)
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:19:from core.db import execute_sql_query
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:62:            result = execute_sql_query(
/app/backend/modules/finanzas/propinas_tpv/repository.py:22:from core.db import execute_sql_query
/app/backend/modules/finanzas/propinas_tpv/repository.py:118:            result = execute_sql_query(
/app/backend/modules/finanzas/propinas_tpv/repository.py:201:            rows = execute_sql_query(
/app/backend/modules/finanzas/propinas_tpv/repository.py:331:                database=server['database'],
/app/backend/modules/finanzas/propinas_tpv/repository.py:396:        Llave única: server_id + sucursal_id + folio_corte + fecha_corte
/app/backend/modules/finanzas/propinas_tpv/repository.py:399:            'server_id': propina_data['server_id'],
/app/backend/modules/finanzas/propinas_tpv/repository.py:451:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/repository.py:467:        if server_id:
/app/backend/modules/finanzas/propinas_tpv/repository.py:468:            filtro['server_id'] = server_id
/app/backend/modules/finanzas/propinas_tpv/repository.py:485:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/repository.py:497:        if server_id:
/app/backend/modules/finanzas/propinas_tpv/repository.py:498:            filtro['server_id'] = server_id
/app/backend/modules/finanzas/propinas_tpv/repository.py:566:        server_id: Optional[str] = None
/app/backend/modules/finanzas/propinas_tpv/repository.py:575:        if server_id:
/app/backend/modules/finanzas/propinas_tpv/repository.py:576:            match_stage['server_id'] = server_id
/app/backend/modules/finanzas/propinas_tpv/repository.py:623:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/repository.py:645:        if sucursal_id and server_id:
/app/backend/modules/finanzas/propinas_tpv/repository.py:650:                    'alcance.server_id': server_id,
/app/backend/modules/finanzas/propinas_tpv/repository.py:659:        if empresa_id and server_id:
/app/backend/modules/finanzas/propinas_tpv/repository.py:664:                    'alcance.server_id': server_id,
/app/backend/modules/finanzas/propinas_tpv/repository.py:738:                ('server_id', 1),
/app/backend/modules/finanzas/propinas_tpv/repository.py:754:            [('server_id', 1), ('fecha_corte', -1)],
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:133:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:149:            server_id: Opcional - sincronizar solo un servidor
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:161:        # Filtrar por server_id específico si se proporciona
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:162:        if server_id:
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:163:            servers = [s for s in servers if s.get('id') == server_id]
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:186:            server_id_actual = server.get('id')
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:235:                        'server_id': server_id_actual,
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:331:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:349:            fecha_inicio, fecha_fin, server_id, sucursal_id, estado, page, limit
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:360:            server_id=server_id,
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:370:            server_id=server_id,
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:398:            fecha_inicio, fecha_fin, server_id, sucursal_id, estado, page, limit,
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:423:        server_id: Optional[str] = None
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:427:        cached = await self.cache.get_resumen_cache(fecha_inicio, fecha_fin, server_id)
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:434:        resumen = await self.sql_repo.obtener_resumen(fecha_inicio, fecha_fin, server_id)
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:442:                server_id=server_id,
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:458:        await self.cache.set_resumen_cache(fecha_inicio, fecha_fin, server_id, result)
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:529:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:534:        cached = await self.cache.get_config_cache(server_id, None, sucursal_id)
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:540:            server_id=server_id,
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:545:        await self.cache.set_config_cache(server_id, None, sucursal_id, config)
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:585:            'alcance_server_id': alcance.get('server_id'),
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:630:            'alcance_server_id': alcance.get('server_id'),
/app/backend/modules/finanzas/propinas_tpv/routes.py:57:def _get_server_from_registry(server_id: str) -> Optional[Dict]:
/app/backend/modules/finanzas/propinas_tpv/routes.py:63:    server = get_server_by_id(server_id)
/app/backend/modules/finanzas/propinas_tpv/routes.py:129:async def get_user_server_ids_permitidos(current_user: Dict[str, Any]) -> List[str]:
/app/backend/modules/finanzas/propinas_tpv/routes.py:220:            server_id=request.server_id,
/app/backend/modules/finanzas/propinas_tpv/routes.py:268:    "/detectar-esquema/{server_id}",
/app/backend/modules/finanzas/propinas_tpv/routes.py:280:    server_id: str,
/app/backend/modules/finanzas/propinas_tpv/routes.py:286:        server = _get_server_from_registry(server_id)
/app/backend/modules/finanzas/propinas_tpv/routes.py:353:                    'server_id': server.get('id'),
/app/backend/modules/finanzas/propinas_tpv/routes.py:365:                    'server_id': server.get('id'),
/app/backend/modules/finanzas/propinas_tpv/routes.py:409:    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
/app/backend/modules/finanzas/propinas_tpv/routes.py:415:        if server_id:
/app/backend/modules/finanzas/propinas_tpv/routes.py:416:            server = _get_server_from_registry(server_id)
/app/backend/modules/finanzas/propinas_tpv/routes.py:424:                "message": "No hay servidores SoftRestaurant" + (f" con id {server_id}" if server_id else ""),
/app/backend/modules/finanzas/propinas_tpv/routes.py:443:                'server_id': server.get('id'),
/app/backend/modules/finanzas/propinas_tpv/routes.py:479:    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
/app/backend/modules/finanzas/propinas_tpv/routes.py:488:            server_id=server_id
/app/backend/modules/finanzas/propinas_tpv/routes.py:504:    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
/app/backend/modules/finanzas/propinas_tpv/routes.py:517:            server_id=server_id,
/app/backend/modules/finanzas/propinas_tpv/routes.py:557:    server_id: Optional[str] = Query(None),
/app/backend/modules/finanzas/propinas_tpv/routes.py:565:            server_id=server_id,
/app/backend/modules/finanzas/propinas_tpv/models.py:112:    server_id: str = Field(..., description="ID del servidor en EDARSA HUB")
/app/backend/modules/finanzas/propinas_tpv/models.py:158:    server_id: Optional[str] = Field(None)
/app/backend/modules/finanzas/propinas_tpv/models.py:219:    server_id: Optional[str] = Field(None, description="Filtrar por servidor específico")
/app/backend/modules/finanzas/repository_softrestaurant.py:262:            database=srv['database'],
/app/backend/modules/finanzas/test_conn_cienfuegos.py:16:2. Existencia del server_id en Servidores_Conexiones
/app/backend/modules/finanzas/test_conn_cienfuegos.py:104:        server=EDARSAHUB_CONFIG['server'],
/app/backend/modules/finanzas/test_conn_cienfuegos.py:106:        database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/finanzas/test_conn_cienfuegos.py:196:                server_id,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:213:                    'server_id': str(row['server_id']) if row['server_id'] else None,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:242:        # Primero obtener el server_id de la unidad
/app/backend/modules/finanzas/test_conn_cienfuegos.py:244:            SELECT server_id FROM Unidades_Negocio WHERE id = %s
/app/backend/modules/finanzas/test_conn_cienfuegos.py:248:        if not unidad_row or not unidad_row['server_id']:
/app/backend/modules/finanzas/test_conn_cienfuegos.py:251:                "CIENFUEGOS no tiene server_id asignado",
/app/backend/modules/finanzas/test_conn_cienfuegos.py:252:                error_type="NO_SERVER_ID"
/app/backend/modules/finanzas/test_conn_cienfuegos.py:256:        server_id = str(unidad_row['server_id'])
/app/backend/modules/finanzas/test_conn_cienfuegos.py:272:        """, (server_id,))
/app/backend/modules/finanzas/test_conn_cienfuegos.py:287:                    'server_id': str(server_row['id']),
/app/backend/modules/finanzas/test_conn_cienfuegos.py:304:                f"Servidor con ID {server_id} NO encontrado en Servidores_Conexiones",
/app/backend/modules/finanzas/test_conn_cienfuegos.py:443:            server=server_string,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:445:            database=database,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:537:            server=host,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:539:            database=database,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:612:            server=server_string,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:614:            database='master',
/app/backend/modules/finanzas/test_conn_cienfuegos.py:680:            server=server_string,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:682:            database=database,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:754:            server=server_string,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:756:            database=database,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:822:            server=server_string,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:824:            database=database,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:893:            server=server_string,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:895:            database=database,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:959:def test_11_edarsahub_sync_status(unidad_negocio_id: str, server_id: str) -> DiagnosticResult:
/app/backend/modules/finanzas/test_conn_cienfuegos.py:1078:    server_id = None
/app/backend/modules/finanzas/test_conn_cienfuegos.py:1096:    server_id = r1.data.get('server_id')
/app/backend/modules/finanzas/test_conn_cienfuegos.py:1109:        report['recomendacion'] = "Verificar server_id en Servidores_Conexiones"
/app/backend/modules/finanzas/test_conn_cienfuegos.py:1113:    server_id = server_config.get('server_id')
/app/backend/modules/finanzas/test_conn_cienfuegos.py:1117:    print(f"    - server_id: {server_config.get('server_id')}")
/app/backend/modules/finanzas/test_conn_cienfuegos.py:1274:    r11 = test_11_edarsahub_sync_status(unidad_negocio_id, server_id)
/app/backend/modules/finanzas/sync_cortes_mpro.py:61:        server=EDARSAHUB_CONFIG['server'],
/app/backend/modules/finanzas/sync_cortes_mpro.py:63:        database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/finanzas/sync_cortes_mpro.py:90:                u.server_id,
/app/backend/modules/finanzas/sync_cortes_mpro.py:101:                ON CAST(u.server_id AS NVARCHAR(100)) = CAST(s.id AS NVARCHAR(100))
/app/backend/modules/finanzas/sync_cortes_mpro.py:137:            'server_id': str(unidad['server_id']),
/app/backend/modules/finanzas/sync_cortes_mpro.py:152:def get_mpro_connection(conn_info: Dict):
/app/backend/modules/finanzas/sync_cortes_mpro.py:155:        server=conn_info['host'],
/app/backend/modules/finanzas/sync_cortes_mpro.py:157:        database=conn_info['database'],
/app/backend/modules/finanzas/sync_cortes_mpro.py:216:        mpro_conn = get_mpro_connection(conn_info)
/app/backend/modules/finanzas/sync_cortes_mpro.py:269:                'ServerID': conn_info['server_id'],
/app/backend/modules/finanzas/sync_cortes_mpro.py:464:    server_id: str,
/app/backend/modules/finanzas/sync_cortes_mpro.py:497:            unidad_id, server_id, 'MPRO',
/app/backend/modules/finanzas/sync_cortes_mpro.py:561:        resultado['server_id'] = conn_info['server_id']
/app/backend/modules/finanzas/sync_cortes_mpro.py:584:            server_id=conn_info['server_id'],
/app/backend/modules/finanzas/sync_cortes_mpro.py:601:            if 'server_id' in resultado:
/app/backend/modules/finanzas/sync_cortes_mpro.py:604:                    server_id=resultado.get('server_id', ''),
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:48:                - server_id: UUID del servidor (alias de unidad_negocio_id)
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:74:            # Filtro por unidad de negocio (server_id o unidad_negocio_id)
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:75:            server_id = filtros.get('server_id') or filtros.get('unidad_negocio_id')
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:76:            if server_id:
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:79:                params.extend([server_id, server_id])
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:152:    def listar_cortes_por_server_id(
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:154:        server_id: str,
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:160:        Lista Cortes de Caja para un server_id específico.
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:166:            'server_id': server_id,
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:284:            server_id = filtros.get('server_id') or filtros.get('unidad_negocio_id')
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:285:            if server_id:
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:287:                params.extend([server_id, server_id])
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:351:            'server_id': row.get('ServerID') or row.get('UnidadNegocioID'),
/app/backend/modules/finanzas/repository_mpro.py:26:MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
/app/backend/modules/finanzas/repository_mpro.py:60:                server_id=MPRO_SERVER_ID,
/app/backend/modules/finanzas/repository_mpro.py:100:                database=credentials['database'],
/app/backend/modules/cava_socios/service.py:33:            server=self.db_config.get('host'),
/app/backend/modules/cava_socios/service.py:35:            database=self.db_config.get('database'),
/app/backend/modules/manuales_operativos/service.py:161:                "empresa_id": proceso.get("empresa_id", proceso.get("server_id", "")),
/app/backend/modules/manuales_operativos/triggers.py:356:        "empresa_id": proceso.get("empresa_id", proceso.get("server_id", "")),
/app/backend/modules/compras/service.py:40:    server_id: str,
/app/backend/modules/compras/service.py:51:    server = await repo.get_server_by_id(server_id)
/app/backend/modules/compras/service.py:60:            log_compras_adapter_selected("inventarios-fisicos", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:67:            log_compras_query_result("inventarios-fisicos", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:70:            log_compras_adapter_selected("inventarios-fisicos", server_id, system_type, "SR_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:76:            log_compras_query_result("inventarios-fisicos", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:80:            log_compras_error("inventarios-fisicos", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/modules/compras/service.py:103:        log_compras_error("inventarios-fisicos", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:111:async def obtener_pedidos_vigentes(server_id: str, sucursal_id: str = None) -> List[Dict]:
/app/backend/modules/compras/service.py:121:    server = await repo.get_server_by_id(server_id)
/app/backend/modules/compras/service.py:130:            log_compras_adapter_selected("pedidos-vigentes", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:134:            log_compras_query_result("pedidos-vigentes", server_id, "SUCCESS", len(data))
/app/backend/modules/compras/service.py:137:            log_compras_adapter_selected("pedidos-vigentes", server_id, system_type, "SR_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:142:                log_compras_query_result("pedidos-vigentes", server_id, "TABLE_NOT_FOUND", 0)
/app/backend/modules/compras/service.py:147:                log_compras_error("pedidos-vigentes", server_id, query_result.status, query_result.message, system_type)
/app/backend/modules/compras/service.py:152:            log_compras_query_result("pedidos-vigentes", server_id, "SUCCESS", len(data))
/app/backend/modules/compras/service.py:155:            log_compras_error("pedidos-vigentes", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/modules/compras/service.py:180:        log_compras_error("pedidos-vigentes", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:189:async def obtener_parametros(server_id: str, sucursal: str) -> Dict:
/app/backend/modules/compras/service.py:194:    params = await repo.get_compras_params(server_id, sucursal)
/app/backend/modules/compras/service.py:213:async def guardar_parametros(server_id: str, sucursal: str, params: Dict) -> Dict:
/app/backend/modules/compras/service.py:217:    await repo.save_compras_params(server_id, sucursal, params)
/app/backend/modules/compras/service.py:225:async def obtener_detalle_factura(server_id: str, folio: str) -> List[Dict]:
/app/backend/modules/compras/service.py:231:    server = await repo.get_server_by_id(server_id)
/app/backend/modules/compras/service.py:239:            log_compras_adapter_selected("detalle-factura", server_id, system_type, "MPRO_ADAPTER")
/app/backend/modules/compras/service.py:241:            log_compras_query_result("detalle-factura", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:255:        log_compras_adapter_selected("detalle-factura", server_id, system_type, "NO_ADAPTER_AVAILABLE")
/app/backend/modules/compras/service.py:264:        log_compras_error("detalle-factura", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:273:    server_id: str,
/app/backend/modules/compras/service.py:283:    server = await repo.get_server_by_id(server_id)
/app/backend/modules/compras/service.py:300:            log_compras_adapter_selected("facturas-proveedor", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:302:            log_compras_query_result("facturas-proveedor", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:317:        log_compras_adapter_selected("facturas-proveedor", server_id, system_type, "NO_ADAPTER_AVAILABLE")
/app/backend/modules/compras/service.py:326:        log_compras_error("facturas-proveedor", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/repository_compras_sql.py:43:        server=host,
/app/backend/modules/compras/repository_compras_sql.py:45:        database=database,
/app/backend/modules/compras/repository_compras_sql.py:128:def get_compras_params_sql(server_id: str, sucursal: str) -> Optional[Dict]:
/app/backend/modules/compras/repository_compras_sql.py:135:        server_id: ID del servidor
/app/backend/modules/compras/repository_compras_sql.py:148:                ServerID as server_id,
/app/backend/modules/compras/repository_compras_sql.py:161:        cursor.execute(query, (server_id, sucursal))
/app/backend/modules/compras/repository_compras_sql.py:178:                'server_id': row['server_id'],
/app/backend/modules/compras/repository_compras_sql.py:188:            logger.debug(f"[COMPRAS_SQL] Parámetros encontrados para {server_id}/{sucursal}")
/app/backend/modules/compras/repository_compras_sql.py:191:        logger.debug(f"[COMPRAS_SQL] No hay parámetros configurados para {server_id}/{sucursal}")
/app/backend/modules/compras/repository_compras_sql.py:201:def save_compras_params_sql(server_id: str, sucursal: str, params: Dict, usuario: str = None) -> bool:
/app/backend/modules/compras/repository_compras_sql.py:209:        server_id: ID del servidor
/app/backend/modules/compras/repository_compras_sql.py:254:            server_id, sucursal,
/app/backend/modules/compras/repository_compras_sql.py:258:            server_id, sucursal, dias_inventario, excluir_domingos, 
/app/backend/modules/compras/repository_compras_sql.py:266:        logger.info(f"[COMPRAS_SQL] Parámetros guardados para {server_id}/{sucursal}")
/app/backend/modules/compras/repository_compras_sql.py:289:                ServerID as server_id,
/app/backend/modules/compras/repository_compras_sql.py:320:                'server_id': row['server_id'],
/app/backend/modules/compras/repository_compras_sql.py:338:def delete_compras_params_sql(server_id: str, sucursal: str) -> bool:
/app/backend/modules/compras/repository_compras_sql.py:343:        server_id: ID del servidor
/app/backend/modules/compras/repository_compras_sql.py:359:        cursor.execute(query, (server_id, sucursal))
/app/backend/modules/compras/repository_compras_sql.py:366:        logger.info(f"[COMPRAS_SQL] Parámetros eliminados para {server_id}/{sucursal}")
/app/backend/modules/compras/eventos_compras.py:74:    server_id: str
/app/backend/modules/compras/eventos_compras.py:90:            "server_id": self.server_id,
/app/backend/modules/compras/eventos_compras.py:142:            server=EDARSAHUB_CONFIG['host'],
/app/backend/modules/compras/eventos_compras.py:144:            database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/compras/eventos_compras.py:165:                evento.server_id,
/app/backend/modules/compras/eventos_compras.py:175:            logger.info(f"[EVENTO] Dispatched: {evento.evento_tipo} - Server={evento.server_name}, Folio={evento.folio}")
/app/backend/modules/compras/eventos_compras.py:211:                    "server_id": e['ServerID'],
/app/backend/modules/compras/eventos_compras.py:310:            server=EDARSAHUB_CONFIG['host'],
/app/backend/modules/compras/eventos_compras.py:312:            database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/compras/eventos_compras.py:318:    def get_checkpoint(self, server_id: str, sync_type: SyncType) -> Dict:
/app/backend/modules/compras/eventos_compras.py:328:            """, (server_id, sync_type.value))
/app/backend/modules/compras/eventos_compras.py:353:        server_id: str, 
/app/backend/modules/compras/eventos_compras.py:383:                server_id, sync_type.value,  # Source
/app/backend/modules/compras/eventos_compras.py:385:                server_id, server_name, sync_type.value, last_folio, last_fecha, now, records_found, now, now  # Insert
/app/backend/modules/compras/eventos_compras.py:445:        server_id = server_info.get('id', '')
/app/backend/modules/compras/eventos_compras.py:450:        checkpoint = self.checkpoint_mgr.get_checkpoint(server_id, SyncType.INVENTARIOS)
/app/backend/modules/compras/eventos_compras.py:516:                        server_id=server_id,
/app/backend/modules/compras/eventos_compras.py:539:                    server_id, server_name, SyncType.INVENTARIOS,
/app/backend/modules/compras/eventos_compras.py:559:        server_id = server_info.get('id', '')
/app/backend/modules/compras/eventos_compras.py:563:        checkpoint = self.checkpoint_mgr.get_checkpoint(server_id, SyncType.REQUISICIONES)
/app/backend/modules/compras/eventos_compras.py:626:                        server_id=server_id,
/app/backend/modules/compras/eventos_compras.py:647:                    server_id, server_name, SyncType.REQUISICIONES,
/app/backend/modules/compras/system_type_utils.py:164:    server_id: str,
/app/backend/modules/compras/system_type_utils.py:173:        f"server_id={server_id} "
/app/backend/modules/compras/system_type_utils.py:183:    server_id: str,
/app/backend/modules/compras/system_type_utils.py:192:        f"server_id={server_id} status={status} "
/app/backend/modules/compras/system_type_utils.py:199:    server_id: str,
/app/backend/modules/compras/system_type_utils.py:207:        f"server_id={server_id} "
/app/backend/modules/compras/repository.py:28:from core.db import execute_sql_query
/app/backend/modules/compras/repository.py:58:        result = execute_sql_query(
/app/backend/modules/compras/repository.py:136:async def get_server_by_id(server_id: str) -> Optional[Dict]:
/app/backend/modules/compras/repository.py:144:    from core.server_registry import get_server_connection_info
/app/backend/modules/compras/repository.py:148:    server = await get_server_connection_info(server_id, db=db)
/app/backend/modules/compras/repository.py:149:    # get_server_connection_info ya descifra credenciales, no necesita _decrypt_server_password
/app/backend/modules/compras/repository.py:160:async def get_compras_params(server_id: str, sucursal: str) -> Optional[Dict]:
/app/backend/modules/compras/repository.py:167:        server_id: ID del servidor
/app/backend/modules/compras/repository.py:174:    return get_compras_params_sql(server_id, sucursal)
/app/backend/modules/compras/repository.py:177:async def save_compras_params(server_id: str, sucursal: str, params: Dict) -> None:
/app/backend/modules/compras/repository.py:184:        server_id: ID del servidor
/app/backend/modules/compras/repository.py:189:    success = save_compras_params_sql(server_id, sucursal, params)
/app/backend/modules/compras/repository.py:191:        logger.error(f"[COMPRAS_REPO] Error guardando parámetros en SQL para {server_id}/{sucursal}")
/app/backend/modules/compras/repository.py:193:        logger.info(f"[COMPRAS_REPO] Parámetros guardados en EDARSAHUB SQL para {server_id}/{sucursal}")
/app/backend/modules/compras/repository.py:223:    return execute_sql_query(
/app/backend/modules/compras/repository.py:249:    return execute_sql_query(
/app/backend/modules/compras/repository.py:284:    return execute_sql_query(
/app/backend/modules/compras/repository.py:332:        result = execute_sql_query(
/app/backend/modules/compras/repository.py:411:    return execute_sql_query(
/app/backend/modules/compras/repository.py:439:    return execute_sql_query(
/app/backend/modules/compras/repository.py:478:    return execute_sql_query(
/app/backend/modules/compras/historical_kpis_repository.py:51:        server=config["host"],
/app/backend/modules/compras/historical_kpis_repository.py:53:        database=config["database"],
/app/backend/modules/compras/historical_kpis_repository.py:90:                [server_id] NVARCHAR(50) NOT NULL,
/app/backend/modules/compras/historical_kpis_repository.py:125:            ON [dbo].[Compras_KPIs_Historico] (server_id, sucursal_id, fecha, kpi_tipo);
/app/backend/modules/compras/historical_kpis_repository.py:145:    server_id: str,
/app/backend/modules/compras/historical_kpis_repository.py:166:        WHERE server_id = %s AND sucursal_id = %s AND fecha = %s AND kpi_tipo = %s
/app/backend/modules/compras/historical_kpis_repository.py:168:        cursor.execute(check_sql, (server_id, sucursal_id, fecha, kpi_tipo))
/app/backend/modules/compras/historical_kpis_repository.py:192:            WHERE server_id = %s AND sucursal_id = %s AND fecha = %s AND kpi_tipo = %s
/app/backend/modules/compras/historical_kpis_repository.py:211:                server_id, sucursal_id, fecha, kpi_tipo
/app/backend/modules/compras/historical_kpis_repository.py:220:                run_id, server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo,
/app/backend/modules/compras/historical_kpis_repository.py:229:                run_id, server_id, sucursal_id, system_type, fecha, kpi_tipo,
/app/backend/modules/compras/sync_service.py:33:        server=EDARSAHUB_CONFIG['host'],
/app/backend/modules/compras/sync_service.py:36:        database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/compras/sync_service.py:48:    server_id: str = None,
/app/backend/modules/compras/sync_service.py:65:                unidad_negocio_codigo, server_id, system_type,
/app/backend/modules/compras/sync_service.py:76:        if server_id:
/app/backend/modules/compras/sync_service.py:77:            query += " AND LOWER(server_id) = LOWER(%s)"
/app/backend/modules/compras/sync_service.py:78:            params.append(server_id)
/app/backend/modules/compras/sync_service.py:111:    server_id: str = None,
/app/backend/modules/compras/sync_service.py:127:                unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
/app/backend/modules/compras/sync_service.py:138:        if server_id:
/app/backend/modules/compras/sync_service.py:139:            query += " AND server_id = %s"
/app/backend/modules/compras/sync_service.py:140:            params.append(server_id)
/app/backend/modules/compras/sync_service.py:173:    execute_sql_query_func
/app/backend/modules/compras/sync_service.py:182:        execute_sql_query_func: Función para ejecutar queries en el servidor origen
/app/backend/modules/compras/sync_service.py:189:    server_id = server_info.get('id')
/app/backend/modules/compras/sync_service.py:240:        rows = execute_sql_query_func(
/app/backend/modules/compras/sync_service.py:260:            WHERE server_id = %s AND sync_status = 'ACTIVE'
/app/backend/modules/compras/sync_service.py:261:        """, (server_id,))
/app/backend/modules/compras/sync_service.py:269:                    (unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
/app/backend/modules/compras/sync_service.py:274:                    unidad_id, unidad_codigo, server_id, system_type,
/app/backend/modules/compras/sync_service.py:303:    execute_sql_query_func
/app/backend/modules/compras/sync_service.py:310:    server_id = server_info.get('id')
/app/backend/modules/compras/sync_service.py:373:        rows = execute_sql_query_func(
/app/backend/modules/compras/sync_service.py:393:            WHERE server_id = %s AND sync_status = 'ACTIVE'
/app/backend/modules/compras/sync_service.py:394:        """, (server_id,))
/app/backend/modules/compras/sync_service.py:402:                    (unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
/app/backend/modules/compras/sync_service.py:408:                    unidad_id, unidad_codigo, server_id, system_type,
/app/backend/modules/compras/sync_service.py:438:    server_id: str,
/app/backend/modules/compras/sync_service.py:452:            (unidad_negocio_id, server_id, sync_type, sync_start, sync_end, 
/app/backend/modules/compras/sync_service.py:456:            unidad_negocio_id, server_id, sync_type,
/app/backend/modules/compras/sync_service.py:465:def get_last_sync_info(server_id: str, sync_type: str) -> Optional[Dict]:
/app/backend/modules/compras/sync_service.py:472:            WHERE server_id = %s AND sync_type = %s
/app/backend/modules/compras/sync_service.py:474:        """, (server_id, sync_type))
/app/backend/modules/compras/repository_pedidos_sql.py:49:            server=EDARSAHUB_CONFIG['host'],
/app/backend/modules/compras/repository_pedidos_sql.py:51:            database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/compras/repository_pedidos_sql.py:88:            server=EDARSAHUB_CONFIG['host'],
/app/backend/modules/compras/repository_pedidos_sql.py:90:            database=EDARSAHUB_CONFIG['database'],
/app/backend/modules/compras/repository_pedidos_sql.py:143:    server_id: str = None,
/app/backend/modules/compras/repository_pedidos_sql.py:180:                estado, now, server_id, sucursal_id, detalles_json,
/app/backend/modules/compras/repository_pedidos_sql.py:192:                origen, server_id, empresa_id, sucursal_id, folio,
/app/backend/modules/compras/repository_pedidos_sql.py:249:                'server_id': r['ServerID'],
/app/backend/modules/compras/routes.py:13:   - GET /compras/parametros/{server_id} (lectura de config)
/app/backend/modules/compras/routes.py:42:# @router.get("/compras/parametros/{server_id}")
/app/backend/modules/compras/routes.py:54:# - GET /compras/inventarios-fisicos/{server_id}
/app/backend/modules/compras/routes.py:55:# - GET /compras/pedidos-vigentes/{server_id}
/app/backend/modules/compras/routes.py:56:# - GET /compras/detalle-pedido/{server_id}/{folio}
/app/backend/modules/compras/routes.py:57:# - GET /compras/detalle-pedido-manual/{server_id}
/app/backend/modules/compras/routes.py:58:# - GET /compras/detalle-movimientos/{server_id}
/app/backend/modules/compras/routes.py:59:# - GET /compras/detalle-consumos/{server_id}
/app/backend/modules/compras/routes.py:60:# - GET /compras/detalle-factura/{server_id}/{folio}
/app/backend/modules/compras/routes.py:61:# - GET /compras/facturas-proveedor/{server_id}
/app/backend/modules/compras/routes.py:62:# - GET /compras/dashboard/{server_id}
/app/backend/modules/compras/schemas.py:25:    server_id: str
/app/backend/modules/compras/schemas.py:40:    server_id: str
/app/backend/modules/compras/schemas.py:60:    server_id: str
/app/backend/modules/compras/schemas.py:67:    server_id: str
/app/backend/modules/compras/schemas.py:79:    server_id: str
/app/backend/modules/compras/schemas.py:89:    server_id: str
/app/backend/scripts/sync_agent_piloto.py:63:    required = ['agent_id', 'hub_url', 'hub_token', 'server_id', 'sql_local']
/app/backend/scripts/sync_agent_piloto.py:97:            server=host,
/app/backend/scripts/sync_agent_piloto.py:99:            database=database,
/app/backend/scripts/sync_agent_piloto.py:116:            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
/app/backend/scripts/sync_agent_piloto.py:117:            f"SERVER={host},{port};"
/app/backend/scripts/sync_agent_piloto.py:118:            f"DATABASE={database};"
/app/backend/scripts/sync_agent_piloto.py:123:        conn = pyodbc.connect(conn_str)
/app/backend/scripts/sync_agent_piloto.py:214:        "server_id": config['server_id'],
/app/backend/scripts/sync_agent_piloto.py:250:        "server_id": config['server_id'],
/app/backend/scripts/sync_agent_piloto.py:322:    logger.info(f"Server ID: {config['server_id']}")
/app/backend/scripts/correccion_sistema_menus_y_fallbacks.py:24:        server=DATABASE_CONFIG['server'],
/app/backend/scripts/correccion_sistema_menus_y_fallbacks.py:26:        database=DATABASE_CONFIG['database'],
/app/backend/scripts/consultar_cache_finops.py:17:        server=DATABASE_CONFIG['server'],
/app/backend/scripts/consultar_cache_finops.py:19:        database=DATABASE_CONFIG['database'],
/app/backend/scripts/finops_shield_mitigacion.py:25:    "driver": "{ODBC Driver 17 for SQL Server}"
/app/backend/scripts/create_sesiones_tables.py:82:            server=EDARSAHUB_CONFIG['host'],
/app/backend/scripts/create_sesiones_tables.py:84:            database=EDARSAHUB_CONFIG['database'],
/app/backend/scripts/run_historical_load_finanzas.py:100:    server_id: str,
/app/backend/scripts/run_historical_load_finanzas.py:107:        "server_id": server_id,
/app/backend/scripts/run_historical_load_finanzas.py:119:        "server_id": server_id,
/app/backend/scripts/run_historical_load_finanzas.py:138:    server_id: str,
/app/backend/scripts/run_historical_load_finanzas.py:145:        {"server_id": server_id, "kpi_tipo": kpi_tipo, "status": {"$ne": STATUS_SUCCESS}},
/app/backend/scripts/run_historical_load_finanzas.py:224:            server=host,
/app/backend/scripts/run_historical_load_finanzas.py:226:            database=database,
/app/backend/scripts/run_historical_load_finanzas.py:290:            server=host,
/app/backend/scripts/run_historical_load_finanzas.py:292:            database=database,
/app/backend/scripts/run_historical_load_finanzas.py:364:            server=host,
/app/backend/scripts/run_historical_load_finanzas.py:366:            database=database,
/app/backend/scripts/run_historical_load_finanzas.py:430:            server=host,
/app/backend/scripts/run_historical_load_finanzas.py:432:            database=database,
/app/backend/scripts/run_historical_load_finanzas.py:479:    server_id = server.get("id")
/app/backend/scripts/run_historical_load_finanzas.py:484:    checkpoint = await get_or_create_checkpoint(db, server_id, server_name, run_id, kpi_tipo)
/app/backend/scripts/run_historical_load_finanzas.py:500:    await update_checkpoint(db, server_id, kpi_tipo, {"status": STATUS_RUNNING})
/app/backend/scripts/run_historical_load_finanzas.py:538:                server_id=server_id,
/app/backend/scripts/run_historical_load_finanzas.py:539:                sucursal_id=server.get("sucursal_id", server_id),
/app/backend/scripts/run_historical_load_finanzas.py:558:        await update_checkpoint(db, server_id, kpi_tipo, {
/app/backend/scripts/run_historical_load_finanzas.py:574:    await update_checkpoint(db, server_id, kpi_tipo, {"status": final_status})
/app/backend/scripts/run_historical_load_finanzas.py:707:                    server=server,
/app/backend/scripts/create_cava_socios_rbac.py:28:        server=DB_CONFIG['host'],
/app/backend/scripts/create_cava_socios_rbac.py:30:        database=DB_CONFIG['database'],
/app/backend/scripts/create_cava_socios_tables.py:29:        server=DB_CONFIG['host'],
/app/backend/scripts/create_cava_socios_tables.py:31:        database=DB_CONFIG['database'],
/app/backend/scripts/update_proyeccion_con_funcion.py:16:        server=DATABASE_CONFIG['server'],
/app/backend/scripts/update_proyeccion_con_funcion.py:18:        database=DATABASE_CONFIG['database'],
/app/backend/scripts/precheck_conectividad.py:88:                from core.db import execute_sql_query
/app/backend/scripts/precheck_conectividad.py:90:                result = execute_sql_query(
/app/backend/scripts/create_crm_automation_tables.py:15:        server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/scripts/create_crm_automation_tables.py:18:        database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/scripts/reconcile_servers_sql_mongo.py:47:from core.db import execute_sql_query
/app/backend/scripts/correccion_proyeccion_y_moneda_final.py:91:            server=DATABASE_CONFIG['server'],
/app/backend/scripts/correccion_proyeccion_y_moneda_final.py:93:            database=DATABASE_CONFIG['database'],
/app/backend/scripts/validate_encrypted_server_connectivity.py:61:from core.db import execute_sql_query
/app/backend/scripts/validate_encrypted_server_connectivity.py:115:    server_id_filter: Optional[str] = None
/app/backend/scripts/validate_encrypted_server_connectivity.py:139:    if server_id_filter:
/app/backend/scripts/validate_encrypted_server_connectivity.py:140:        safe_id = server_id_filter.replace("'", "''")
/app/backend/scripts/validate_encrypted_server_connectivity.py:164:    result = execute_sql_query(
/app/backend/scripts/validate_encrypted_server_connectivity.py:229:    server_id = server['id']
/app/backend/scripts/validate_encrypted_server_connectivity.py:232:    logger.info(f"[CONNECTIVITY][START] {server_name} ({server_id[:8]}...)")
/app/backend/scripts/validate_encrypted_server_connectivity.py:236:        'server_id': server_id,
/app/backend/scripts/validate_encrypted_server_connectivity.py:346:    server_id = server['id']
/app/backend/scripts/validate_encrypted_server_connectivity.py:349:    logger.info(f"[CONNECTIVITY][API][START] {server_name} ({server_id[:8]}...)")
/app/backend/scripts/validate_encrypted_server_connectivity.py:353:        'server_id': server_id,
/app/backend/scripts/validate_encrypted_server_connectivity.py:462:                'server_id': server['id'],
/app/backend/scripts/validate_encrypted_server_connectivity.py:639:        server_id_filter=args.server_id
/app/backend/scripts/seed_inteligencia_demo.py:23:        server=EDARSAHUB_HOST,
/app/backend/scripts/seed_inteligencia_demo.py:27:        database=EDARSAHUB_DB,
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:22:from core.db import execute_sql_query
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:37:    server_ids: List[str],
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:44:        server_ids: Lista de ServerIDs a procesar
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:66:    for server_id in server_ids:
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:67:        print(f"\n=== Procesando {server_id[:8]}... ===")
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:83:        WHERE ServerID = '{server_id}'
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:88:        registros = execute_sql_query(
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:98:            print(f"  ⚠️  Sin datos en Historicas para {server_id[:8]}")
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:99:            resultado['errores'].append(f"Sin datos para {server_id}")
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:148:            row_hash = f"{server_id}|{dia_iso}|{fecha_min}|{fecha_max}"
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:153:                'ServerID': server_id,
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:174:        resultado['detalle_servidores'][server_id] = detalle_servidor
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:238:                    execute_sql_query(
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:259:    server_ids = [
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:270:    result_dry = calcular_pordiasemana_desde_historicas(server_ids, dry_run=True)
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:288:    result_real = calcular_pordiasemana_desde_historicas(server_ids, dry_run=False)
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:297:    result_idem = calcular_pordiasemana_desde_historicas(server_ids, dry_run=False)
/app/backend/scripts/sync_response_cache_finops.py:17:        server=DATABASE_CONFIG['server'],
/app/backend/scripts/sync_response_cache_finops.py:19:        database=DATABASE_CONFIG['database'],
/app/backend/scripts/consolidado_general_sistema_comercial.py:37:    "driver": "{ODBC Driver 17 for SQL Server}"
/app/backend/scripts/consolidado_general_sistema_comercial.py:415:        server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/scripts/consolidado_general_sistema_comercial.py:419:        database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/scripts/carga_historica_fase23.py:164:        server_id: str,
/app/backend/scripts/carga_historica_fase23.py:195:                server_id=server_id,
/app/backend/scripts/carga_historica_fase23.py:310:                    "server_id": server.get('id'),
/app/backend/scripts/carga_historica_fase23.py:385:                        "server_id": "$server_id",
/app/backend/scripts/carga_historica_fase23.py:415:                {"$group": {"_id": "$server_id", "count": {"$sum": 1}}}
/app/backend/scripts/carga_historica_fase23.py:420:                    "server_id": s["_id"],
/app/backend/scripts/ddl_costos_alertas_001b.py:24:from core.db import execute_sql_query
/app/backend/scripts/ddl_costos_alertas_001b.py:526:            execute_sql_query(*conn, ddl)
/app/backend/scripts/ddl_costos_alertas_001b.py:530:            result = execute_sql_query(*conn, check_query)
/app/backend/scripts/ddl_costos_alertas_001b.py:551:        execute_sql_query(*conn, DDL_UMBRALES_SEMILLA)
/app/backend/scripts/ddl_costos_alertas_001b.py:555:        result = execute_sql_query(*conn, check_umbrales)
/app/backend/scripts/ddl_costos_alertas_001b.py:591:        result = execute_sql_query(*conn, query)
/app/backend/scripts/ddl_costos_alertas_001b.py:601:    umbrales = execute_sql_query(*conn, query_umbrales)
/app/backend/scripts/create_tablajeria_rbac.py:28:        server=DB_CONFIG['host'],
/app/backend/scripts/create_tablajeria_rbac.py:30:        database=DB_CONFIG['database'],
/app/backend/scripts/ddl_competidores_enterprise_unidad.py:22:from core.db import execute_sql_query
/app/backend/scripts/ddl_competidores_enterprise_unidad.py:340:            execute_sql_query(*conn, stmt)
/app/backend/scripts/seed_ventas_consolidadas.py:34:        server='<REDACTED_EDARSAHUB_SQL_HOST>',
/app/backend/scripts/seed_ventas_consolidadas.py:38:        database='EDARSAHUB',
/app/backend/scripts/ddl_competidores_nuevos_campos.py:12:from core.db import execute_sql_query
/app/backend/scripts/ddl_competidores_nuevos_campos.py:68:            execute_sql_query(*conn, stmt)
/app/backend/scripts/consolidado_general_sistema_comercial_v2.py:197:        server=DATABASE_CONFIG['server'],
/app/backend/scripts/consolidado_general_sistema_comercial_v2.py:199:        database=DATABASE_CONFIG['database'],
/app/backend/scripts/create_scheduler_tables.py:111:            server=EDARSAHUB_CONFIG['host'],
/app/backend/scripts/create_scheduler_tables.py:113:            database=EDARSAHUB_CONFIG['database'],
/app/backend/scripts/setup_kpis_indexes.py:38:    1. idx_unique_kpi_diario (ÚNICO): server_id + empresa_id + sucursal_id + fecha
/app/backend/scripts/setup_kpis_indexes.py:60:                ("server_id", 1),
/app/backend/scripts/setup_kpis_indexes.py:102:            [("server_id", 1), ("fecha", -1)],
/app/backend/scripts/audit_fecha_operativa_0600.py:49:        server=EDARSAHUB_CONFIG['server'],
/app/backend/scripts/audit_fecha_operativa_0600.py:53:        database=EDARSAHUB_CONFIG['database']
/app/backend/scripts/create_workflow_tables.py:44:        server=EDARSAHUB_CONFIG['host'],
/app/backend/scripts/create_workflow_tables.py:46:        database=EDARSAHUB_CONFIG['database'],
/app/backend/scripts/validar_post_carga.py:42:                "server_id": "$server_id",
/app/backend/scripts/validar_post_carga.py:108:        {"$group": {"_id": "$server_id", "count": {"$sum": 1}}},
/app/backend/scripts/encrypt_existing_server_secrets.py:38:from core.db import execute_sql_query
/app/backend/scripts/encrypt_existing_server_secrets.py:80:    result = execute_sql_query(
/app/backend/scripts/encrypt_existing_server_secrets.py:107:        server_id = str(server.get('id', ''))
/app/backend/scripts/encrypt_existing_server_secrets.py:137:                'id': server_id,
/app/backend/scripts/encrypt_existing_server_secrets.py:146:def encrypt_server_secrets_sql(server_id: str, encrypt_password: bool, encrypt_api_key: bool) -> dict:
/app/backend/scripts/encrypt_existing_server_secrets.py:151:        server_id: ID del servidor
/app/backend/scripts/encrypt_existing_server_secrets.py:162:    WHERE CAST(id AS VARCHAR(50)) = '{server_id}'
/app/backend/scripts/encrypt_existing_server_secrets.py:165:    result = execute_sql_query(
/app/backend/scripts/encrypt_existing_server_secrets.py:202:    WHERE CAST(id AS VARCHAR(50)) = '{server_id}'
/app/backend/scripts/encrypt_existing_server_secrets.py:210:async def encrypt_server_secrets_mongo(server_id: str, encrypt_password: bool, encrypt_api_key: bool) -> dict:
/app/backend/scripts/encrypt_existing_server_secrets.py:219:        server = await db.servers.find_one({'id': server_id})
/app/backend/scripts/encrypt_existing_server_secrets.py:238:            await db.servers.update_one({'id': server_id}, {'$set': updates})
/app/backend/scripts/encrypt_existing_server_secrets.py:310:        server_id = server_info['id']
/app/backend/scripts/encrypt_existing_server_secrets.py:317:            server_id,
/app/backend/scripts/encrypt_existing_server_secrets.py:330:            server_id,
/app/backend/scripts/encrypt_existing_server_secrets.py:342:            'id': server_id,
/app/backend/scripts/rotate_server_secret_key.py:152:    from core.db import execute_sql_query
/app/backend/scripts/rotate_server_secret_key.py:187:    result = execute_sql_query(
/app/backend/scripts/rotate_server_secret_key.py:288:    from core.db import execute_sql_query
/app/backend/scripts/rotate_server_secret_key.py:307:        server_id = server['id']
/app/backend/scripts/rotate_server_secret_key.py:310:        logger.info(f"[SECRET_ROTATION][ROTATE_START] {server_name} ({server_id[:8]}...)")
/app/backend/scripts/rotate_server_secret_key.py:314:            'id': server_id,
/app/backend/scripts/rotate_server_secret_key.py:354:                WHERE CAST(id AS VARCHAR(50)) = '{server_id}'
/app/backend/scripts/rotate_server_secret_key.py:357:                execute_sql_query(
/app/backend/scripts/rotate_server_secret_key.py:372:                        sync_to_mongodb(server_id, updates)
/app/backend/scripts/rotate_server_secret_key.py:393:def sync_to_mongodb(server_id: str, updates: Dict):
/app/backend/scripts/rotate_server_secret_key.py:414:            {'id': server_id},
/app/backend/scripts/actualizacion_kpi_proyeccion_comercial.py:26:        server=DATABASE_CONFIG['server'],
/app/backend/scripts/actualizacion_kpi_proyeccion_comercial.py:28:        database=DATABASE_CONFIG['database'],
/app/backend/scripts/create_unidades_negocio_table.py:14:from core.db import execute_sql_query
/app/backend/scripts/create_unidades_negocio_table.py:27:    return execute_sql_query(
/app/backend/scripts/create_unidades_negocio_table.py:58:            server_id NVARCHAR(100) NOT NULL,
/app/backend/scripts/create_unidades_negocio_table.py:67:            CONSTRAINT UQ_Unidades_Server_Sucursal UNIQUE (server_id, sucursal_origen_id)
/app/backend/scripts/create_unidades_negocio_table.py:71:        CREATE INDEX IX_Unidades_ServerID ON Unidades_Negocio(server_id);
/app/backend/scripts/create_unidades_negocio_table.py:101:            'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6',
/app/backend/scripts/create_unidades_negocio_table.py:109:            'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b',
/app/backend/scripts/create_unidades_negocio_table.py:117:            'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f',
/app/backend/scripts/create_unidades_negocio_table.py:126:            'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
/app/backend/scripts/create_unidades_negocio_table.py:134:            'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
/app/backend/scripts/create_unidades_negocio_table.py:148:            WHERE server_id = '{u['server_id']}' 
/app/backend/scripts/create_unidades_negocio_table.py:152:            INSERT INTO Unidades_Negocio (nombre, codigo, server_id, sucursal_origen_id, system_type, orden, activo)
/app/backend/scripts/create_unidades_negocio_table.py:153:            VALUES ('{u['nombre']}', '{u['codigo']}', '{u['server_id']}', {suc_id}, '{u['system_type']}', {u['orden']}, 1);
/app/backend/scripts/create_unidades_negocio_table.py:165:            WHERE server_id = '{u['server_id']}' 
/app/backend/scripts/create_unidades_negocio_table.py:186:        server_id,
/app/backend/scripts/validacion_propinas_tpv.py:55:def connect_and_query(server_id: str, query: str) -> List[Dict]:
/app/backend/scripts/validacion_propinas_tpv.py:59:    config = SOFTREST_SERVERS.get(server_id)
/app/backend/scripts/validacion_propinas_tpv.py:65:            server=config['host'],
/app/backend/scripts/validacion_propinas_tpv.py:67:            database=config['database'],
/app/backend/scripts/validacion_propinas_tpv.py:82:def validacion_1_extraccion(server_id: str, config: dict) -> Dict:
/app/backend/scripts/validacion_propinas_tpv.py:93:        'server_id': server_id,
/app/backend/scripts/validacion_propinas_tpv.py:119:    schema_result = connect_and_query(server_id, query_schema)
/app/backend/scripts/validacion_propinas_tpv.py:163:def validacion_2_no_duplicidad(server_id: str, config: dict) -> Dict:
/app/backend/scripts/validacion_propinas_tpv.py:197:    turno_result = connect_and_query(server_id, query_turno)
/app/backend/scripts/validacion_propinas_tpv.py:231:    corte_result = connect_and_query(server_id, query_corte)
/app/backend/scripts/validacion_propinas_tpv.py:245:def validacion_3_coherencia(server_id: str, config: dict) -> Dict:
/app/backend/scripts/validacion_propinas_tpv.py:284:    cortes = connect_and_query(server_id, query)
/app/backend/scripts/validacion_propinas_tpv.py:325:def validacion_4_cuadre_funcional(server_id: str, config: dict) -> Dict:
/app/backend/scripts/validacion_propinas_tpv.py:362:    cortes = connect_and_query(server_id, query)
/app/backend/scripts/validacion_propinas_tpv.py:428:    for server_id, data in resultados.items():
/app/backend/scripts/validacion_propinas_tpv.py:429:        nombre = SOFTREST_SERVERS[server_id]['nombre_display']
/app/backend/scripts/validacion_propinas_tpv.py:526:    for server_id, config in SOFTREST_SERVERS.items():
/app/backend/scripts/validacion_propinas_tpv.py:531:        resultados[server_id] = {
/app/backend/scripts/validacion_propinas_tpv.py:532:            'extraccion': validacion_1_extraccion(server_id, config),
/app/backend/scripts/validacion_propinas_tpv.py:533:            'no_duplicidad': validacion_2_no_duplicidad(server_id, config),
/app/backend/scripts/validacion_propinas_tpv.py:534:            'coherencia': validacion_3_coherencia(server_id, config),
/app/backend/scripts/validacion_propinas_tpv.py:535:            'cuadre': validacion_4_cuadre_funcional(server_id, config)
/app/backend/scripts/validacion_propinas_tpv.py:566:    for server_id, config in SOFTREST_SERVERS.items():
/app/backend/scripts/encrypt_core_server_secrets.py:50:from core.db import execute_sql_query
/app/backend/scripts/encrypt_core_server_secrets.py:89:    result = execute_sql_query(
/app/backend/scripts/encrypt_core_server_secrets.py:117:        server_id = server.get('id', '')
/app/backend/scripts/encrypt_core_server_secrets.py:149:                'id': server_id,
/app/backend/scripts/encrypt_core_server_secrets.py:160:def encrypt_core_server_sql(server_id: str, encrypt_password: bool, encrypt_api_key: bool) -> dict:
/app/backend/scripts/encrypt_core_server_secrets.py:165:        server_id: ID del servidor CORE
/app/backend/scripts/encrypt_core_server_secrets.py:176:    WHERE CAST(id AS VARCHAR(50)) = '{server_id}'
/app/backend/scripts/encrypt_core_server_secrets.py:180:    result = execute_sql_query(
/app/backend/scripts/encrypt_core_server_secrets.py:223:    WHERE CAST(id AS VARCHAR(50)) = '{server_id}'
/app/backend/scripts/encrypt_core_server_secrets.py:250:async def sync_core_to_mongo(server_id: str, mongodb_id: str) -> dict:
/app/backend/scripts/encrypt_core_server_secrets.py:367:        server_id = server_info['id']
/app/backend/scripts/encrypt_core_server_secrets.py:375:            server_id,
/app/backend/scripts/encrypt_core_server_secrets.py:396:        mongo_result = await sync_core_to_mongo(server_id, mongodb_id)
/app/backend/scripts/encrypt_core_server_secrets.py:405:            'id': server_id,
/app/backend/scripts/run_historical_load_compras.py:129:    server_id: str,
/app/backend/scripts/run_historical_load_compras.py:136:        "server_id": server_id,
/app/backend/scripts/run_historical_load_compras.py:148:        "server_id": server_id,
/app/backend/scripts/run_historical_load_compras.py:165:async def update_checkpoint(db, server_id: str, kpi_tipo: str, updates: Dict):
/app/backend/scripts/run_historical_load_compras.py:169:        {"server_id": server_id, "kpi_tipo": kpi_tipo, "status": {"$ne": STATUS_SUCCESS}},
/app/backend/scripts/run_historical_load_compras.py:206:            server=server.get('host'),
/app/backend/scripts/run_historical_load_compras.py:208:            database=server.get('database'),
/app/backend/scripts/run_historical_load_compras.py:257:            server=host,
/app/backend/scripts/run_historical_load_compras.py:259:            database=server.get('database'),
/app/backend/scripts/run_historical_load_compras.py:308:            server=server.get('host'),
/app/backend/scripts/run_historical_load_compras.py:310:            database=server.get('database'),
/app/backend/scripts/run_historical_load_compras.py:354:            server=host,
/app/backend/scripts/run_historical_load_compras.py:356:            database=server.get('database'),
/app/backend/scripts/run_historical_load_compras.py:409:            server=server.get('host'),
/app/backend/scripts/run_historical_load_compras.py:411:            database=server.get('database'),
/app/backend/scripts/run_historical_load_compras.py:455:            server=host,
/app/backend/scripts/run_historical_load_compras.py:457:            database=server.get('database'),
/app/backend/scripts/run_historical_load_compras.py:503:            server=server.get('host'),
/app/backend/scripts/run_historical_load_compras.py:505:            database=server.get('database'),
/app/backend/scripts/run_historical_load_compras.py:549:            server=host,
/app/backend/scripts/run_historical_load_compras.py:551:            database=server.get('database'),
/app/backend/scripts/run_historical_load_compras.py:593:    server_id = server.get("id")
/app/backend/scripts/run_historical_load_compras.py:598:    checkpoint = await get_or_create_checkpoint(db, server_id, server_name, run_id, kpi_tipo)
/app/backend/scripts/run_historical_load_compras.py:609:    await update_checkpoint(db, server_id, kpi_tipo, {"status": STATUS_RUNNING})
/app/backend/scripts/run_historical_load_compras.py:652:                server_id=server_id,
/app/backend/scripts/run_historical_load_compras.py:653:                sucursal_id=server.get("sucursal_id", server_id),
/app/backend/scripts/run_historical_load_compras.py:672:        await update_checkpoint(db, server_id, kpi_tipo, {
/app/backend/scripts/run_historical_load_compras.py:687:    await update_checkpoint(db, server_id, kpi_tipo, {"status": final_status})
/app/backend/scripts/run_historical_load_compras.py:816:                    server=server,
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py:68:            server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py:70:            database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py:84:            get_server_connection_config
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py:107:    from modules.comercial_v2.sync_comercial_edarsahub import get_server_connection_config
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py:109:    server_config = get_server_connection_config('6d053c22-523e-48c0-b72b-96081e2d781b')
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py:124:            server=server_config['host'],
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py:126:            database=server_config['database_name'],
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py:173:        server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py:175:        database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py:216:        server_id='6d053c22-523e-48c0-b72b-96081e2d781b',
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py:250:        server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py:252:        database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/scripts/generar_doc_diagnostico.py:192:code_cs.add_run('Server=IP_SUCURSAL,1433;Database=ManagementPro;User Id=usuario;Password=***;\n\n').font.name = 'Consolas'
/app/backend/scripts/generar_doc_diagnostico.py:194:code_cs.add_run('Server=IP_SUCURSAL,PUERTO;Database=ManagementPro;User Id=usuario;Password=***;\n\n').font.name = 'Consolas'
/app/backend/scripts/generar_doc_diagnostico.py:196:code_cs.add_run('Server=IP_SUCURSAL\\INSTANCIA,PUERTO;Database=...').font.name = 'Consolas'
/app/backend/scripts/run_historical_load_24_months.py:106:    server_id: str,
/app/backend/scripts/run_historical_load_24_months.py:119:        "server_id": server_id,
/app/backend/scripts/run_historical_load_24_months.py:147:    server_id: str,
/app/backend/scripts/run_historical_load_24_months.py:154:        {"run_id": run_id, "server_id": server_id},
/app/backend/scripts/run_historical_load_24_months.py:162:    server_id: str
/app/backend/scripts/run_historical_load_24_months.py:166:        {"run_id": run_id, "server_id": server_id},
/app/backend/scripts/run_historical_load_24_months.py:174:    server_id: str
/app/backend/scripts/run_historical_load_24_months.py:178:        {"module": module, "server_id": server_id}
/app/backend/scripts/run_historical_load_24_months.py:268:                    server=server,
/app/backend/scripts/run_historical_load_24_months.py:287:                    server=server,
/app/backend/scripts/run_historical_load_24_months.py:338:    server_id = server.get("id")
/app/backend/scripts/run_historical_load_24_months.py:362:                "server_id": server_id,
/app/backend/scripts/run_historical_load_24_months.py:435:            server=server,
/app/backend/scripts/run_historical_load_24_months.py:487:    server_id: Optional[str] = None,
/app/backend/scripts/run_historical_load_24_months.py:502:        server_id: UUID de servidor específico (opcional)
/app/backend/scripts/run_historical_load_24_months.py:548:    if server_id:
/app/backend/scripts/run_historical_load_24_months.py:549:        servers = [s for s in servers if s.get("id") == server_id]
/app/backend/scripts/run_historical_load_24_months.py:551:            logger.error(f"[ERROR] Servidor {server_id} no encontrado")
/app/backend/scripts/run_historical_load_24_months.py:552:            return {"status": "ERROR", "error": f"Servidor {server_id} no encontrado"}
/app/backend/scripts/run_historical_load_24_months.py:595:                "server_id": server.get("id"),
/app/backend/scripts/run_historical_load_24_months.py:615:        server_id_current = server.get("id")
/app/backend/scripts/run_historical_load_24_months.py:622:            db, run_id, module, server_id_current, server_name,
/app/backend/scripts/run_historical_load_24_months.py:626:        await update_checkpoint(db, run_id, server_id_current, {
/app/backend/scripts/run_historical_load_24_months.py:631:            "server_id": server_id_current,
/app/backend/scripts/run_historical_load_24_months.py:684:                await update_checkpoint(db, run_id, server_id_current, {
/app/backend/scripts/run_historical_load_24_months.py:705:            await update_checkpoint(db, run_id, server_id_current, {
/app/backend/scripts/run_historical_load_24_months.py:718:            await update_checkpoint(db, run_id, server_id_current, {
/app/backend/scripts/run_historical_load_24_months.py:828:        server_id=args.server_id,
/app/backend/scripts/paquete_piloto_sync_agent/sync_agent_piloto.py:68:    required = ['agent_id', 'hub_url', 'hub_token', 'server_id', 'sql_local']
/app/backend/scripts/paquete_piloto_sync_agent/sync_agent_piloto.py:102:            server=host,
/app/backend/scripts/paquete_piloto_sync_agent/sync_agent_piloto.py:104:            database=database,
/app/backend/scripts/paquete_piloto_sync_agent/sync_agent_piloto.py:204:        "server_id": config['server_id'],
/app/backend/scripts/paquete_piloto_sync_agent/sync_agent_piloto.py:242:        "server_id": config['server_id'],
/app/backend/scripts/paquete_piloto_sync_agent/sync_agent_piloto.py:288:            logger.info(f"✅ Autenticación OK: agent_id={result.get('agent_id')}, server_id={result.get('server_id')}")
/app/backend/scripts/paquete_piloto_sync_agent/sync_agent_piloto.py:320:        "server_id": config['server_id'],
/app/backend/scripts/paquete_piloto_sync_agent/sync_agent_piloto.py:383:        logger.info(f"  Server ID: {config['server_id']}")
/app/backend/scripts/paquete_piloto_sync_agent/sync_agent_piloto.py:388:        generate_report(config if 'config' in dir() else {"agent_id": "unknown", "server_id": "unknown", "hub_url": "unknown"}, results)
/app/backend/tests/test_automatizacion_compras_fase4.py:286:            # Verificar campos clave - empresa_id es el eje en Fase 4.1, pero puede haber datos legacy con server_id
/app/backend/tests/test_automatizacion_compras_fase4.py:291:            # empresa_id o server_id deben existir (empresa_id es el nuevo estándar)
/app/backend/tests/test_automatizacion_compras_fase4.py:292:            has_identifier = "empresa_id" in pedido or "server_id" in pedido
/app/backend/tests/test_automatizacion_compras_fase4.py:293:            assert has_identifier, "Pedido missing both 'empresa_id' and 'server_id'"
/app/backend/tests/test_automatizacion_compras_fase4.py:295:            identifier = pedido.get('empresa_id') or pedido.get('server_id')
/app/backend/tests/test_automatizacion_compras_fase4.py:401:        """GET /kpis - Debe aceptar filtro por server_id"""
/app/backend/tests/test_automatizacion_compras_fase4.py:404:            params={"server_id": "server_test"}
/app/backend/tests/test_automatizacion_compras_fase4.py:408:        print("✓ KPIs con filtro server_id")
/app/backend/tests/test_inventory_analysis_filters.py:25:MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
/app/backend/tests/test_inventory_analysis_filters.py:45:    """Tests for GET /api/servers/{server_id}/report-filters endpoint"""
/app/backend/tests/test_inventory_analysis_filters.py:63:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/report-filters",
/app/backend/tests/test_inventory_analysis_filters.py:83:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/report-filters",
/app/backend/tests/test_inventory_analysis_filters.py:103:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/report-filters",
/app/backend/tests/test_inventory_analysis_filters.py:123:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/report-filters",
/app/backend/tests/test_inventory_analysis_filters.py:183:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/report-filters",
/app/backend/tests/test_inventory_analysis_filters.py:190:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
/app/backend/tests/test_inventory_analysis_filters.py:201:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes",
/app/backend/tests/test_inventory_analysis_filters.py:213:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/inventarios",
/app/backend/tests/test_inventory_analysis_filters.py:229:            "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_inventory_analysis_filters.py:280:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
/app/backend/tests/test_inventory_analysis_filters.py:291:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes",
/app/backend/tests/test_inventory_analysis_filters.py:303:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/inventarios",
/app/backend/tests/test_inventory_analysis_filters.py:317:            "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_inventory_analysis_filters.py:383:            if server["id"] == MPRO_SERVER_ID:
/app/backend/tests/test_inventory_analysis_filters.py:387:        assert mpro_server is not None, f"MPRO server {MPRO_SERVER_ID} not found"
/app/backend/tests/test_compras_analisis.py:53:                "server_id": self.softrestaurant_server['id'],
/app/backend/tests/test_compras_analisis.py:69:                "server_id": self.softrestaurant_server['id'],
/app/backend/tests/test_compras_analisis.py:90:                "server_id": self.softrestaurant_server['id'],
/app/backend/tests/test_compras_analisis.py:113:                "server_id": self.softrestaurant_server['id'],
/app/backend/tests/test_compras_analisis.py:133:                "server_id": self.softrestaurant_server['id'],
/app/backend/tests/test_compras_analisis.py:157:                "server_id": self.softrestaurant_server['id'],
/app/backend/tests/test_compras_analisis.py:172:                "server_id": "invalid-server-id",
/app/backend/tests/test_compras_analisis.py:307:                "server_id": self.mpro_server['id'],
/app/backend/tests/test_health.py:32:        from core.db import execute_sql_query
/app/backend/tests/test_health.py:33:        assert callable(execute_sql_query)
/app/backend/tests/test_comercial.py:127:                server_id = servers[0].get("id")
/app/backend/tests/test_comercial.py:130:                    f"{api_base_url}/api/comercial/dashboard/{server_id}",
/app/backend/tests/test_comercial.py:141:        """Test: Dashboard con server_id inválido"""
/app/backend/tests/test_permissions_v5.py:91:        server_ids = [s["id"] for s in servers]
/app/backend/tests/test_permissions_v5.py:92:        assert MANAGMENT_PRO_ID in server_ids, "ManagmentPro should be visible"
/app/backend/tests/test_permissions_v5.py:93:        assert CIENFUEGOS_ID in server_ids, "Cienfuegos should be visible"
/app/backend/tests/test_permissions_v5.py:94:        assert LA_ESTELAR_ID in server_ids, "LA ESTELAR should be visible"
/app/backend/tests/test_sucursales_permissions.py:25:MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
/app/backend/tests/test_sucursales_permissions.py:100:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
/app/backend/tests/test_sucursales_permissions.py:118:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
/app/backend/tests/test_sucursales_permissions.py:157:            "allowed_servers": [MPRO_SERVER_ID],
/app/backend/tests/test_sucursales_permissions.py:159:                MPRO_SERVER_ID: ["0021", "0022"]
/app/backend/tests/test_sucursales_permissions.py:269:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
/app/backend/tests/test_simulacion_controlada.py:135:    from core.db import execute_sql_query
/app/backend/tests/test_simulacion_controlada.py:198:    print(f"  {'server_id':<30} │ {inv['server_id']}")
/app/backend/tests/test_simulacion_controlada.py:243:                execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:250:                server_id=server['id']
/app/backend/tests/test_simulacion_controlada.py:255:                execute_sql_query, server, folios_procesados
/app/backend/tests/test_simulacion_controlada.py:283:                execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:290:                server_id=server['id']
/app/backend/tests/test_simulacion_controlada.py:295:                execute_sql_query, server, folios_procesados
/app/backend/tests/test_simulacion_controlada.py:414:        inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:426:        execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:433:        inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:475:        execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:482:        inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:523:        execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:556:        execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:675:    Server ID:      {inv['server_id']}
/app/backend/tests/test_simulacion_controlada.py:685:        inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:706:    print(f"  {'server_id':<30} │ {inv['server_id']}")
/app/backend/tests/test_simulacion_controlada.py:741:            execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:748:            inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:807:            execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:814:            inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:848:            execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:883:                execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:954:    print(f"│  {'server_id':<28} │ {inv['server_id']:<45} │")
/app/backend/tests/test_simulacion_controlada.py:1062:            execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:1069:            inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:1129:            inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:1180:                execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:1187:                inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:1311:    print(f"│  {'server_id':<28} │ {inv['server_id']:<45} │")
/app/backend/tests/test_simulacion_controlada.py:1418:        execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:1425:        inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:1463:        inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:1494:            execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:1501:            inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:1596:    print(f"│  {'server_id':<28} │ {inv['server_id']:<45} │")
/app/backend/tests/test_simulacion_controlada.py:1707:            execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:1714:            inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:1776:            inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:1827:                execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:1834:                inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:1967:    print(f"│  {'server_id':<28} │ {inv['server_id']:<45} │")
/app/backend/tests/test_simulacion_controlada.py:2088:            execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:2095:            inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:2157:            inv['server_id'],
/app/backend/tests/test_simulacion_controlada.py:2211:                execute_sql_query,
/app/backend/tests/test_simulacion_controlada.py:2218:                inv['server_id'],
/app/backend/tests/test_mpro_inventory_analysis.py:21:MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
/app/backend/tests/test_mpro_inventory_analysis.py:61:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}",
/app/backend/tests/test_mpro_inventory_analysis.py:73:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
/app/backend/tests/test_mpro_inventory_analysis.py:85:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes",
/app/backend/tests/test_mpro_inventory_analysis.py:106:                "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_mpro_inventory_analysis.py:208:    SOFTRESTAURANT_SERVER_ID = "a5ff0e25-f029-43db-b634-d4ac814c904f"
/app/backend/tests/test_mpro_inventory_analysis.py:213:            f"{BASE_URL}/api/servers/{self.SOFTRESTAURANT_SERVER_ID}",
/app/backend/tests/test_mpro_inventory_analysis.py:224:            f"{BASE_URL}/api/servers/{self.SOFTRESTAURANT_SERVER_ID}/almacenes-softrestaurant",
/app/backend/tests/test_mpro_inventory_analysis.py:235:            f"{BASE_URL}/api/servers/{self.SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_mpro_inventory_analysis.py:250:                "server_id": self.SOFTRESTAURANT_SERVER_ID,
/app/backend/tests/test_core_db.py:4:Tests de cobertura para execute_sql_query, cooldown y parseo.
/app/backend/tests/test_core_db.py:166:    """Tests de execute_sql_query con mocks"""
/app/backend/tests/test_core_db.py:169:    def test_execute_sql_query_imports(self):
/app/backend/tests/test_core_db.py:171:        from core.db import execute_sql_query
/app/backend/tests/test_core_db.py:172:        assert callable(execute_sql_query)
/app/backend/tests/test_core_db.py:175:    def test_execute_sql_query_fallback_imports(self):
/app/backend/tests/test_core_db.py:177:        from core.db import _execute_sql_query_direct
/app/backend/tests/test_core_db.py:178:        assert callable(_execute_sql_query_direct)
/app/backend/tests/test_core_db.py:183:        from core.db import execute_sql_query, mark_server_offline, reset_server_cache
/app/backend/tests/test_core_db.py:189:        result = execute_sql_query(
/app/backend/tests/test_core_db.py:192:            database="TestDB",
/app/backend/tests/test_core_db.py:214:        # (El pool se importa dentro de execute_sql_query, no en nivel módulo)
/app/backend/tests/test_core_db.py:237:        # Convertir como hace execute_sql_query
/app/backend/tests/test_core_db.py:247:    """Tests de manejo de errores en execute_sql_query"""
/app/backend/tests/test_bloque5_paridad.py:4:Valida que el endpoint /comercial/dashboard/{server_id} migrado
/app/backend/tests/test_bloque5_paridad.py:8:Endpoint: /comercial/dashboard/{server_id}
/app/backend/tests/test_pool.py:128:    """Tests de la función execute_sql_query"""
/app/backend/tests/test_pool.py:131:    def test_execute_sql_query_import(self):
/app/backend/tests/test_pool.py:132:        """Test: execute_sql_query se importa correctamente"""
/app/backend/tests/test_pool.py:133:        from core.db import execute_sql_query
/app/backend/tests/test_pool.py:135:        assert callable(execute_sql_query)
/app/backend/tests/test_pool.py:138:    def test_execute_sql_query_fallback_exists(self):
/app/backend/tests/test_pool.py:140:        from core.db import _execute_sql_query_direct
/app/backend/tests/test_pool.py:142:        assert callable(_execute_sql_query_direct)
/app/backend/tests/test_dashboard_comercial.py:37:        """Test: Dashboard con server_id inválido"""
/app/backend/tests/test_dashboard_comercial.py:100:                # Mock de execute_sql_query para no conectar a SQL real
/app/backend/tests/test_dashboard_comercial.py:101:                with patch("core.db.execute_sql_query") as mock_sql:
/app/backend/tests/test_dashboard_servers.py:22:SERVER_IDS = {
/app/backend/tests/test_dashboard_servers.py:114:        server_id = SERVER_IDS["MPRO"]
/app/backend/tests/test_dashboard_servers.py:116:            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
/app/backend/tests/test_dashboard_servers.py:136:        server_id = SERVER_IDS["MPRO"]
/app/backend/tests/test_dashboard_servers.py:138:            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
/app/backend/tests/test_dashboard_servers.py:166:        server_id = SERVER_IDS["Cienfuegos"]
/app/backend/tests/test_dashboard_servers.py:168:            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
/app/backend/tests/test_dashboard_servers.py:183:        server_id = SERVER_IDS["Cienfuegos"]
/app/backend/tests/test_dashboard_servers.py:185:            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
/app/backend/tests/test_dashboard_servers.py:205:        server_id = SERVER_IDS["LA_ESTELAR"]
/app/backend/tests/test_dashboard_servers.py:207:            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
/app/backend/tests/test_dashboard_servers.py:222:        server_id = SERVER_IDS["LA_ESTELAR"]
/app/backend/tests/test_dashboard_servers.py:224:            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
/app/backend/tests/test_dashboard_servers.py:241:        server_id = SERVER_IDS["MPRO"]
/app/backend/tests/test_dashboard_servers.py:243:            f"{BASE_URL}/api/servers/{server_id}/tipos-movimiento",
/app/backend/tests/test_dashboard_servers.py:259:        server_id = SERVER_IDS["MPRO"]
/app/backend/tests/test_dashboard_servers.py:261:            f"{BASE_URL}/api/servers/{server_id}/categorias",
/app/backend/tests/test_dashboard_servers.py:272:        server_id = SERVER_IDS["MPRO"]
/app/backend/tests/test_dashboard_servers.py:274:            f"{BASE_URL}/api/servers/{server_id}/departamentos",
/app/backend/tests/test_dashboard_servers.py:289:        server_id = SERVER_IDS["LA_ESTELAR"]
/app/backend/tests/test_dashboard_servers.py:291:            f"{BASE_URL}/api/servers/{server_id}/tipos-movimiento",
/app/backend/tests/test_dashboard_servers.py:302:        server_id = SERVER_IDS["LA_ESTELAR"]
/app/backend/tests/test_dashboard_servers.py:304:            f"{BASE_URL}/api/servers/{server_id}/categorias",
/app/backend/tests/test_dashboard_servers.py:315:        server_id = SERVER_IDS["LA_ESTELAR"]
/app/backend/tests/test_dashboard_servers.py:317:            f"{BASE_URL}/api/servers/{server_id}/departamentos",
/app/backend/tests/test_comercial_rbac_blindaje.py:61:            assert "server_id" in unidad, "Unidad missing 'server_id'"
/app/backend/tests/test_comercial_rbac_blindaje.py:95:        # Get a valid server_id from unidades
/app/backend/tests/test_comercial_rbac_blindaje.py:103:        # Use first unidad's server_id
/app/backend/tests/test_comercial_rbac_blindaje.py:104:        server_id = unidades[0].get("server_id")
/app/backend/tests/test_comercial_rbac_blindaje.py:109:            f"{BASE_URL}/api/comercial/dashboard/{server_id}",
/app/backend/tests/test_comercial_rbac_blindaje.py:122:        # Use a fake server_id that doesn't exist
/app/backend/tests/test_comercial_rbac_blindaje.py:123:        fake_server_id = "00000000-0000-0000-0000-000000000000"
/app/backend/tests/test_comercial_rbac_blindaje.py:126:            f"{BASE_URL}/api/comercial/dashboard/{fake_server_id}",
/app/backend/tests/test_comercial_rbac_blindaje.py:158:        """Verify /api/comercial/sucursales/{server_id} validates access"""
/app/backend/tests/test_comercial_rbac_blindaje.py:159:        # Get a valid server_id
/app/backend/tests/test_comercial_rbac_blindaje.py:167:        server_id = unidades[0].get("server_id")
/app/backend/tests/test_comercial_rbac_blindaje.py:170:        response = self.session.get(f"{BASE_URL}/api/comercial/sucursales/{server_id}")
/app/backend/tests/test_comercial_rbac_blindaje.py:179:        """Verify /api/comercial/metas/{server_id} validates access"""
/app/backend/tests/test_comercial_rbac_blindaje.py:186:        server_id = unidades[0].get("server_id")
/app/backend/tests/test_comercial_rbac_blindaje.py:190:            f"{BASE_URL}/api/comercial/metas/{server_id}",
/app/backend/tests/test_comercial_rbac_blindaje.py:201:        """Verify /api/comercial/ticket-perfecto/{server_id} validates access"""
/app/backend/tests/test_comercial_rbac_blindaje.py:208:        server_id = unidades[0].get("server_id")
/app/backend/tests/test_comercial_rbac_blindaje.py:212:            f"{BASE_URL}/api/comercial/ticket-perfecto/{server_id}",
/app/backend/tests/test_comercial_rbac_blindaje.py:223:        """Verify /api/comercial/ventas-tiempo/{server_id} validates access"""
/app/backend/tests/test_comercial_rbac_blindaje.py:230:        server_id = unidades[0].get("server_id")
/app/backend/tests/test_comercial_rbac_blindaje.py:234:            f"{BASE_URL}/api/comercial/ventas-tiempo/{server_id}",
/app/backend/tests/test_comercial_rbac_blindaje.py:245:        """Verify /api/comercial/mesas/{server_id} validates access"""
/app/backend/tests/test_comercial_rbac_blindaje.py:252:        server_id = unidades[0].get("server_id")
/app/backend/tests/test_comercial_rbac_blindaje.py:256:            f"{BASE_URL}/api/comercial/mesas/{server_id}",
/app/backend/tests/test_comercial_rbac_blindaje.py:267:        """Verify /api/comercial/detalle-movimientos/{server_id} validates access"""
/app/backend/tests/test_comercial_rbac_blindaje.py:274:        server_id = unidades[0].get("server_id")
/app/backend/tests/test_comercial_rbac_blindaje.py:278:            f"{BASE_URL}/api/comercial/detalle-movimientos/{server_id}",
/app/backend/tests/test_comercial_rbac_blindaje.py:289:        """Verify /api/comercial/reporte-pax/{server_id} validates access"""
/app/backend/tests/test_comercial_rbac_blindaje.py:296:        server_id = unidades[0].get("server_id")
/app/backend/tests/test_comercial_rbac_blindaje.py:300:            f"{BASE_URL}/api/comercial/reporte-pax/{server_id}",
/app/backend/tests/test_comercial_rbac_blindaje.py:311:        """Verify /api/comercial/precios-constantes/{server_id} validates access"""
/app/backend/tests/test_comercial_rbac_blindaje.py:318:        server_id = unidades[0].get("server_id")
/app/backend/tests/test_comercial_rbac_blindaje.py:322:            f"{BASE_URL}/api/comercial/precios-constantes/{server_id}",
/app/backend/tests/test_cargos_economicos.py:293:            "server_id": "test-server-cargo",
/app/backend/tests/conftest.py:225:    Mock para execute_sql_query.
/app/backend/tests/conftest.py:230:            with patch("core.db.execute_sql_query", mock_sql_query):
/app/backend/tests/test_repositories.py:79:    def test_execute_sql_query_import(self):
/app/backend/tests/test_repositories.py:80:        """Test: execute_sql_query se puede importar"""
/app/backend/tests/test_repositories.py:81:        from core.db import execute_sql_query
/app/backend/tests/test_repositories.py:82:        assert callable(execute_sql_query)
/app/backend/tests/test_repositories.py:86:        """Test: Patch de execute_sql_query funciona"""
/app/backend/tests/test_repositories.py:87:        with patch("core.db.execute_sql_query") as mock:
/app/backend/tests/test_compras_module.py:25:MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
/app/backend/tests/test_compras_module.py:80:        mpro_server = next((s for s in servers if s['id'] == MPRO_SERVER_ID), None)
/app/backend/tests/test_compras_module.py:81:        assert mpro_server is not None, f"MPRO server {MPRO_SERVER_ID} not found"
/app/backend/tests/test_compras_module.py:88:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
/app/backend/tests/test_compras_module.py:111:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
/app/backend/tests/test_compras_module.py:121:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes?sucursal={sucursal_nombre}",
/app/backend/tests/test_compras_module.py:158:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
/app/backend/tests/test_compras_module.py:169:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes?sucursal={sucursal_nombre}",
/app/backend/tests/test_compras_module.py:186:                "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_compras_module.py:212:                "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_compras_module.py:249:                "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_compras_module.py:281:                "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_compras_module.py:318:                "server_id": "invalid-server-id",
/app/backend/tests/test_compras_module.py:334:                "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_compras_module.py:361:            f"{BASE_URL}/api/compras/parametros/{MPRO_SERVER_ID}",
/app/backend/tests/test_compras_module.py:368:        assert "server_id" in data
/app/backend/tests/test_movement_sales_details.py:15:MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
/app/backend/tests/test_movement_sales_details.py:47:            "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_movement_sales_details.py:69:            "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_movement_sales_details.py:77:            "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_movement_sales_details.py:109:            "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_movement_sales_details.py:130:            "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_movement_sales_details.py:138:            "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_movement_sales_details.py:169:        suc_response = api_client.get(f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales")
/app/backend/tests/test_movement_sales_details.py:176:            alm_response = api_client.get(f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes", 
/app/backend/tests/test_movement_sales_details.py:194:            "server_id": "invalid-server-id",
/app/backend/tests/test_movement_sales_details.py:206:            "server_id": "invalid-server-id",
/app/backend/tests/test_bloque2_paridad.py:26:from core.db import execute_sql_query
/app/backend/tests/test_bloque2_paridad.py:71:        result = execute_sql_query(
/app/backend/tests/test_user_permissions.py:26:SERVER_IDS = {
/app/backend/tests/test_user_permissions.py:217:        visible_server_ids = [s.get("id") for s in visible_servers]
/app/backend/tests/test_user_permissions.py:223:            for server_id in visible_server_ids:
/app/backend/tests/test_user_permissions.py:224:                assert server_id in allowed_servers, f"Server {server_id} visible but not in allowed_servers"
/app/backend/tests/test_user_permissions.py:258:            "allowed_servers": [SERVER_IDS["Cienfuegos"]],
/app/backend/tests/test_user_permissions.py:327:        for server_name, server_id in SERVER_IDS.items():
/app/backend/tests/test_user_permissions.py:329:                f"{BASE_URL}/api/servers/{server_id}",
/app/backend/tests/test_user_permissions.py:350:        for server_name, server_id in SERVER_IDS.items():
/app/backend/tests/test_user_permissions.py:351:            if server_id not in allowed_servers:
/app/backend/tests/test_user_permissions.py:353:                    f"{BASE_URL}/api/servers/{server_id}",
/app/backend/tests/test_bloque3_paridad_mpro.py:31:from core.db import execute_sql_query
/app/backend/tests/test_bloque3_paridad_mpro.py:79:        result = execute_sql_query(
/app/backend/tests/test_softrestaurant_inventory.py:19:SOFTRESTAURANT_SERVER_ID = "a5ff0e25-f029-43db-b634-d4ac814c904f"
/app/backend/tests/test_softrestaurant_inventory.py:60:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}",
/app/backend/tests/test_softrestaurant_inventory.py:71:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/almacenes-softrestaurant",
/app/backend/tests/test_softrestaurant_inventory.py:87:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_softrestaurant_inventory.py:106:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_softrestaurant_inventory.py:130:                "server_id": SOFTRESTAURANT_SERVER_ID,
/app/backend/tests/test_softrestaurant_inventory.py:159:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_softrestaurant_inventory.py:176:                "server_id": SOFTRESTAURANT_SERVER_ID,
/app/backend/tests/test_softrestaurant_inventory.py:217:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_softrestaurant_inventory.py:233:                "server_id": SOFTRESTAURANT_SERVER_ID,
/app/backend/tests/test_softrestaurant_inventory.py:274:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_softrestaurant_inventory.py:290:                "server_id": SOFTRESTAURANT_SERVER_ID,
/app/backend/tests/test_softrestaurant_inventory.py:332:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_softrestaurant_inventory.py:349:                "server_id": SOFTRESTAURANT_SERVER_ID,
/app/backend/tests/test_softrestaurant_inventory.py:374:                    "server_id": SOFTRESTAURANT_SERVER_ID,
/app/backend/tests/test_comparativo_inventarios.py:27:MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
/app/backend/tests/test_comparativo_inventarios.py:81:        mpro_server = next((s for s in servers if s.get('id') == MPRO_SERVER_ID), None)
/app/backend/tests/test_comparativo_inventarios.py:82:        assert mpro_server is not None, f"MPRO server {MPRO_SERVER_ID} not found"
/app/backend/tests/test_comparativo_inventarios.py:88:        response = self.session.get(f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales")
/app/backend/tests/test_comparativo_inventarios.py:104:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes",
/app/backend/tests/test_comparativo_inventarios.py:128:                "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_comparativo_inventarios.py:162:                "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_comparativo_inventarios.py:201:                "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_comparativo_inventarios.py:217:                "server_id": "invalid-server-id",
/app/backend/tests/test_comparativo_inventarios.py:237:                "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_comparativo_inventarios.py:274:        """Test that cache uses correct key structure (server_id, almacen_id, sucursal_id, comentario, folio)"""
/app/backend/tests/test_comparativo_inventarios.py:277:        # - server_id
/app/backend/tests/test_comparativo_inventarios.py:283:        expected_cache_key_fields = ['server_id', 'almacen_id', 'sucursal_id', 'comentario', 'folio']
/app/backend/tests/test_comparativo_inventarios.py:317:                "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_comparativo_inventarios.py:371:                "server_id": MPRO_SERVER_ID,
/app/backend/tests/test_macrofase2_kpis.py:83:    test_server_id = "test-server-001"
/app/backend/tests/test_macrofase2_kpis.py:90:        "server_id": {"$regex": "^test-"}
/app/backend/tests/test_macrofase2_kpis.py:133:            server_id=test_server_id,
/app/backend/tests/test_macrofase2_kpis.py:156:            server_id=test_server_id,
/app/backend/tests/test_macrofase2_kpis.py:185:            server_id=test_server_id,
/app/backend/tests/test_macrofase2_kpis.py:214:            server_id=test_server_id,
/app/backend/tests/test_macrofase2_kpis.py:237:            test_server_id, test_empresa_id, test_sucursal_id, test_fecha
/app/backend/tests/test_macrofase2_kpis.py:258:            test_server_id, test_empresa_id, test_sucursal_id, test_fecha
/app/backend/tests/test_macrofase2_kpis.py:277:            test_server_id, test_empresa_id, test_sucursal_id, test_fecha,
/app/backend/tests/test_macrofase2_kpis.py:284:            test_server_id, test_empresa_id, test_sucursal_id, test_fecha
/app/backend/tests/test_macrofase2_kpis.py:307:            server_id=test_server_id,
/app/backend/tests/test_macrofase2_kpis.py:331:            server_id=test_server_id,
/app/backend/tests/test_macrofase2_kpis.py:355:            test_server_id, test_empresa_id, test_sucursal_id, test_fecha,
/app/backend/tests/test_macrofase2_kpis.py:381:            server_id=test_server_id,
/app/backend/tests/test_macrofase2_kpis.py:405:            "server_id": test_server_id,
/app/backend/tests/test_macrofase2_kpis.py:428:                server_id="test-server-bulk",
/app/backend/tests/test_macrofase2_kpis.py:466:        "server_id": {"$regex": "^test-"}
/app/backend/server.py:294:async def validate_server_access_unified(current_user: Dict, server_id: str) -> UserAccessContext:
/app/backend/server.py:303:        server_id: ID del servidor a validar
/app/backend/server.py:313:    if has_server_access(context, server_id):
/app/backend/server.py:318:        f"sin acceso a servidor {server_id}. "
/app/backend/server.py:960:    allowed_sucursales: Dict[str, List[str]] = {}  # server_id -> [sucursal_ids]
/app/backend/server.py:961:    allowed_warehouses: Dict[str, List[str]] = {}  # server_id -> [warehouse_codes]
/app/backend/server.py:1046:    server_id: str
/app/backend/server.py:1117:    server_id: str  # FK a servers.id
/app/backend/server.py:1160:    server_id: str
/app/backend/server.py:1202:    server_id: str
/app/backend/server.py:1243:#   - execute_sql_query()
/app/backend/server.py:1257:    execute_sql_query,
/app/backend/server.py:1636:@api_router.get("/servers/{server_id}")
/app/backend/server.py:1637:async def get_server(server_id: str, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:1648:    await validate_server_access_unified(current_user, server_id)
/app/backend/server.py:1651:        server_id,
/app/backend/server.py:1663:@api_router.put("/servers/{server_id}")
/app/backend/server.py:1664:async def update_server(server_id: str, server_data: Dict, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:1683:    existing = await get_server_by_id(server_id, db=db, mask_secrets=False)
/app/backend/server.py:1700:        server_id=server_id,
/app/backend/server.py:1721:@api_router.delete("/servers/{server_id}")
/app/backend/server.py:1722:async def delete_server(server_id: str, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:1741:    existing = await get_server_by_id(server_id, db=db, mask_secrets=True)
/app/backend/server.py:1754:        server_id=server_id,
/app/backend/server.py:1776:@api_router.get("/servers/{server_id}/ping")
/app/backend/server.py:1777:async def ping_server(server_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:1783:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:1786:    from core.server_registry import get_server_connection_info
/app/backend/server.py:1790:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}))
/app/backend/server.py:1792:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:1795:        logging.warning(f"[PING_SERVER] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:1805:        result = execute_sql_query(
/app/backend/server.py:1819:                {"server_id": server_id},
/app/backend/server.py:1820:                {"$set": {"server_id": server_id, "is_online": True, "response_time_ms": elapsed_time, "last_check": datetime.now(timezone.utc).isoformat()}},
/app/backend/server.py:1846:            {"server_id": server_id},
/app/backend/server.py:1847:            {"$set": {"server_id": server_id, "is_online": False, "last_check": datetime.now(timezone.utc).isoformat()}},
/app/backend/server.py:1992:@api_router.post("/servers/{server_id}/queries/validate")
/app/backend/server.py:1994:    server_id: str, 
/app/backend/server.py:2008:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:2027:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:2028:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:2040:        logging.info(f"Validando consulta tipo '{query_type}' para servidor {server_id}")
/app/backend/server.py:2042:        results = execute_sql_query(
/app/backend/server.py:2099:@api_router.put("/servers/{server_id}/queries/{query_type}")
/app/backend/server.py:2101:    server_id: str,
/app/backend/server.py:2113:    from core.server_registry import get_server_connection_info_with_secrets, update_server as registry_update_server, get_server_by_id
/app/backend/server.py:2125:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:2126:    server = get_server_connection_info_with_secrets(server_id)
/app/backend/server.py:2140:    # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {field_name: query_config}})
/app/backend/server.py:2142:        server_id=server_id,
/app/backend/server.py:2153:    # ANTES: updated_server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}, {"_id": 0}))
/app/backend/server.py:2154:    updated_server = await get_server_by_id(server_id, db=db, mask_secrets=True)
/app/backend/server.py:2162:        # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {"queries_configured": all_configured}})
/app/backend/server.py:2164:            server_id=server_id,
/app/backend/server.py:2181:@api_router.get("/servers/{server_id}/queries")
/app/backend/server.py:2182:async def get_server_queries(server_id: str, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:2193:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:2194:    server = await get_server_by_id(server_id, db=db, mask_secrets=True)
/app/backend/server.py:2199:        "server_id": server_id,
/app/backend/server.py:2236:@api_router.delete("/servers/{server_id}/queries/{query_type}")
/app/backend/server.py:2238:    server_id: str,
/app/backend/server.py:2249:    from core.server_registry import get_server_connection_info_with_secrets, update_server as registry_update_server
/app/backend/server.py:2255:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:2256:    server = get_server_connection_info_with_secrets(server_id)
/app/backend/server.py:2262:    # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {field_name: None, "queries_configured": False}})
/app/backend/server.py:2264:        server_id=server_id,
/app/backend/server.py:2278:@api_router.get("/servers/{server_id}/tipos-movimiento")
/app/backend/server.py:2279:async def get_tipos_movimiento(server_id: str, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:2299:    from core.server_registry import get_server_connection_info
/app/backend/server.py:2302:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:2305:        logging.warning(f"[GET_TIPOS_MOVIMIENTO] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:2316:        logging.info(f"[GET_TIPOS_MOVIMIENTO] EDARSAHUB-FIRST: {len(result)} tipos. Server={server.get('name', 'N/A')}")
/app/backend/server.py:2321:    logging.info(f"[GET_TIPOS_MOVIMIENTO] Sin tipos en EDARSAHUB. Server={server.get('name', 'N/A')}")
/app/backend/server.py:2407:@api_router.get("/servers/{server_id}/categorias")
/app/backend/server.py:2408:async def get_categorias(server_id: str, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:2426:    server = await get_server_by_id(server_id, db=db)
/app/backend/server.py:2429:        logging.warning(f"[GET_CATEGORIAS] Servidor no encontrado. ID={server_id}")
/app/backend/server.py:2436:        logging.info(f"[GET_CATEGORIAS] EDARSAHUB-FIRST: {len(categorias)} categorías. Server={server.get('name', 'N/A')}")
/app/backend/server.py:2440:    logging.info(f"[GET_CATEGORIAS] Sin categorías en EDARSAHUB (pendiente sync). Server={server.get('name', 'N/A')}")
/app/backend/server.py:2444:@api_router.get("/servers/{server_id}/departamentos")
/app/backend/server.py:2445:async def get_departamentos(server_id: str, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:2463:    server = await get_server_by_id(server_id, db=db)
/app/backend/server.py:2466:        logging.warning(f"[GET_DEPARTAMENTOS] Servidor no encontrado. ID={server_id}")
/app/backend/server.py:2496:        logging.info(f"[GET_DEPARTAMENTOS] EDARSAHUB-FIRST: {len(departamentos)} departamentos. Server={server.get('name', 'N/A')}")
/app/backend/server.py:2500:    logging.info(f"[GET_DEPARTAMENTOS] Sin departamentos en EDARSAHUB (pendiente sync). Server={server.get('name', 'N/A')}")
/app/backend/server.py:2503:async def filter_sucursales_by_config(sucursales: List[Dict], server_id: str) -> List[Dict]:
/app/backend/server.py:2512:        {"server_id": server_id, "activa": True}
/app/backend/server.py:2528:        logging.warning(f"Todas las sucursales de {server_id} están ocultas, mostrando todas por seguridad")
/app/backend/server.py:2554:@api_router.get("/servers/{server_id}/sucursales")
/app/backend/server.py:2555:async def get_sucursales(server_id: str, include_hidden: bool = False, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:2560:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:2566:    from core.server_registry import get_server_connection_info
/app/backend/server.py:2568:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:2570:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:2573:        logging.warning(f"[GET_SUCURSALES] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:2586:                results = execute_sql_query(
/app/backend/server.py:2604:                    almacenes = execute_sql_query(
/app/backend/server.py:2628:                results = execute_sql_query(
/app/backend/server.py:2645:        sucursales_filtradas = filter_sucursales_by_permissions(sucursales_raw, current_user, server_id)
/app/backend/server.py:2649:            sucursales_filtradas = await filter_sucursales_by_config(sucursales_filtradas, server_id)
/app/backend/server.py:2658:@api_router.get("/servers/{server_id}/almacenes")
/app/backend/server.py:2659:async def get_almacenes(server_id: str, sucursal_id: Optional[str] = None, sucursal: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:2665:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:2668:    from core.server_registry import get_server_connection_info
/app/backend/server.py:2673:    if not has_server_access(context, server_id):
/app/backend/server.py:2674:        logging.warning(f"[RBAC-ALMACENES] {current_user.get('email')} sin acceso a servidor {server_id}")
/app/backend/server.py:2677:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:2679:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:2682:        logging.warning(f"[GET_ALMACENES] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:2688:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:2692:        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:2696:        # FASE 1B: Importar execute_sql_query_params para parametrización segura
/app/backend/server.py:2697:        from core.db import execute_sql_query_params
/app/backend/server.py:2707:            almacen_filter = get_almacenes_sql_filter(context, server_id, "Al_Cve_Almacen")
/app/backend/server.py:2712:                results = execute_sql_query_params(
/app/backend/server.py:2718:                results = execute_sql_query(
/app/backend/server.py:2727:            almacen_filter = get_almacenes_sql_filter(context, server_id, "idalmacen")
/app/backend/server.py:2738:            results = execute_sql_query(
/app/backend/server.py:2747:            almacen_filter = get_almacenes_sql_filter(context, server_id, "Al_Cve_Almacen")
/app/backend/server.py:2751:                results = execute_sql_query_params(
/app/backend/server.py:2757:                results = execute_sql_query(
/app/backend/server.py:2768:@api_router.get("/servers/{server_id}/sucursales-config")
/app/backend/server.py:2769:async def get_sucursales_config(server_id: str, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:2775:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:2778:    from core.server_registry import get_server_connection_info
/app/backend/server.py:2780:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:2782:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:2785:        logging.warning(f"[GET_SUCURSALES_CONFIG] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:2792:        {"server_id": server_id, "activa": True},
/app/backend/server.py:2797:        "server_id": server_id,
/app/backend/server.py:2803:@api_router.post("/servers/{server_id}/sucursales-config/sync")
/app/backend/server.py:2804:async def sync_sucursales_config(server_id: str, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:2812:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:2815:    from core.server_registry import get_server_connection_info
/app/backend/server.py:2820:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:2822:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:2825:        logging.warning(f"[SYNC_SUCURSALES_CONFIG] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:2835:            sucursales_sql = execute_sql_query(
/app/backend/server.py:2851:        {"server_id": server_id}
/app/backend/server.py:2868:                {"server_id": server_id, "sucursal_origen_id": suc_id},
/app/backend/server.py:2881:                "server_id": server_id,
/app/backend/server.py:2898:        {"server_id": server_id, "activa": True},
/app/backend/server.py:2910:@api_router.put("/servers/{server_id}/sucursales-config/{sucursal_origen_id}")
/app/backend/server.py:2912:    server_id: str, 
/app/backend/server.py:2923:        "server_id": server_id,
/app/backend/server.py:2941:        {"server_id": server_id, "sucursal_origen_id": sucursal_origen_id},
/app/backend/server.py:2947:@api_router.put("/servers/{server_id}/sucursales-config/bulk")
/app/backend/server.py:2949:    server_id: str, 
/app/backend/server.py:2975:            {"server_id": server_id, "sucursal_origen_id": suc_id},
/app/backend/server.py:2985:# ============= ENDPOINT GLOBAL DE SUCURSALES (para componentes que no tienen server_id) =============
/app/backend/server.py:2988:    server_id: Optional[str] = Query(None),
/app/backend/server.py:2994:    Endpoint global para componentes que necesitan listar sucursales sin conocer el server_id.
/app/backend/server.py:3000:    if server_id:
/app/backend/server.py:3001:        filtro["server_id"] = server_id
/app/backend/server.py:3009:    # ANTES: server_cursor = db.servers.find({"id": {"$in": server_ids}}, {"_id": 0, "id": 1, "name": 1})
/app/backend/server.py:3011:    server_ids = list(set(s.get("server_id") for s in sucursales if s.get("server_id")))
/app/backend/server.py:3013:    if server_ids:
/app/backend/server.py:3016:            if srv.get("id") in server_ids:
/app/backend/server.py:3020:        suc["server_nombre"] = servers.get(suc.get("server_id"), "")
/app/backend/server.py:3027:# El backend traduce unidad → server_id internamente
/app/backend/server.py:3052:        - server_id: ID técnico del servidor
/app/backend/server.py:3058:    from core.db import execute_sql_query
/app/backend/server.py:3069:            CAST(un.server_id AS VARCHAR(50)) as server_id,
/app/backend/server.py:3080:        INNER JOIN Servidores_Conexiones sc ON CAST(un.server_id AS VARCHAR(50)) = CAST(sc.id AS VARCHAR(50))
/app/backend/server.py:3086:        unidades_sql = execute_sql_query(
/app/backend/server.py:3117:            # Filtrar unidades cuyos server_id estén en allowed_servers
/app/backend/server.py:3121:                if u.get('server_id') in allowed_servers or u.get('id') in empresas_permitidas
/app/backend/server.py:3146:                "server_id": u.get('server_id'),
/app/backend/server.py:3175:@api_router.get("/servers/{server_id}/almacenes-softrestaurant")
/app/backend/server.py:3177:    server_id: str, 
/app/backend/server.py:3186:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:3189:    from core.server_registry import get_server_connection_info
/app/backend/server.py:3194:    if not has_server_access(context, server_id):
/app/backend/server.py:3195:        logging.warning(f"[RBAC-ALMACENES-SR] {current_user.get('email')} sin acceso a servidor {server_id}")
/app/backend/server.py:3198:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:3200:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:3203:        logging.warning(f"[GET_ALMACENES_SR] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:3212:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:3213:    almacen_filter = get_almacenes_sql_filter(context, server_id, "idalmacen")
/app/backend/server.py:3217:        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:3234:        results = execute_sql_query(
/app/backend/server.py:3248:@api_router.get("/servers/{server_id}/inventarios")
/app/backend/server.py:3250:    server_id: str, 
/app/backend/server.py:3260:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:3263:    from core.server_registry import get_server_connection_info
/app/backend/server.py:3268:    if not has_server_access(context, server_id):
/app/backend/server.py:3269:        logging.warning(f"[RBAC-INVENTARIOS-LIST] {current_user.get('email')} sin acceso a servidor {server_id}")
/app/backend/server.py:3272:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:3274:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:3277:        logging.warning(f"[GET_INVENTARIOS_LIST] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:3283:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:3287:        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:3293:            almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "F.Al_Cve_Almacen")
/app/backend/server.py:3322:            almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "INV.idalmacen1")
/app/backend/server.py:3347:        results = execute_sql_query(
/app/backend/server.py:3364:@api_router.get("/inventarios/pendientes/{server_id}")
/app/backend/server.py:3366:    server_id: str,
/app/backend/server.py:3377:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:3380:    from core.server_registry import get_server_connection_info
/app/backend/server.py:3385:    if not has_server_access(context, server_id):
/app/backend/server.py:3386:        logging.warning(f"[RBAC-PENDIENTES] {current_user.get('email')} sin acceso a servidor {server_id}")
/app/backend/server.py:3389:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:3391:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:3394:        logging.warning(f"[GET_PENDIENTES_DESCARGAR] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:3400:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:3412:        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:3418:            almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "ip.idalmacen")
/app/backend/server.py:3512:        results = execute_sql_query(
/app/backend/server.py:3612:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:3614:    server_id = report_params.get('server_id')
/app/backend/server.py:3619:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:3620:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:3639:    results = execute_sql_query(
/app/backend/server.py:3650:@api_router.get("/servers/{server_id}/report-filters")
/app/backend/server.py:3651:async def get_report_filters(server_id: str, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:3659:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:3662:    from core.server_registry import get_server_connection_info
/app/backend/server.py:3664:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:3666:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:3669:        logging.warning(f"[GET_REPORT_FILTERS] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:3683:            categorias = execute_sql_query(
/app/backend/server.py:3695:            familias = execute_sql_query(
/app/backend/server.py:3707:            subfamilias = execute_sql_query(
/app/backend/server.py:3739:            familias = execute_sql_query(
/app/backend/server.py:3752:            subfamilias = execute_sql_query(
/app/backend/server.py:3797:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:3799:    server_id = report_params.get('server_id')
/app/backend/server.py:3865:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:3866:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:3936:                    fecha_result = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], fecha_folio_query)
/app/backend/server.py:3949:                    fecha_result = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], fecha_folio_query)
/app/backend/server.py:3983:            almacen_result = execute_sql_query(
/app/backend/server.py:3988:                logging.error(f"Almacén(es) no encontrado(s) en MPRO - Sucursal: '{sucursal}', Almacenes: {lista_almacenes}, Servidor: {server.get('name', server_id)}")
/app/backend/server.py:4070:            productos = execute_sql_query(
/app/backend/server.py:4116:                ventas_result = execute_sql_query(
/app/backend/server.py:4161:            movimientos_result = execute_sql_query(
/app/backend/server.py:4185:            errores_result = execute_sql_query(
/app/backend/server.py:4275:                inv_detalle = execute_sql_query(
/app/backend/server.py:4428:                            "server_id": server_id,
/app/backend/server.py:4465:                    server_id=server_id,
/app/backend/server.py:4513:            fechas_result = execute_sql_query(
/app/backend/server.py:4580:            almacen_result = execute_sql_query(
/app/backend/server.py:4585:                logging.error(f"Almacén '{almacen}' no encontrado en servidor {server.get('name', server_id)} ({server['host']})")
/app/backend/server.py:4673:            productos_result = execute_sql_query(
/app/backend/server.py:4720:            inventarios_result = execute_sql_query(
/app/backend/server.py:4835:                movimientos_result = execute_sql_query(
/app/backend/server.py:4904:                    ventas_result = execute_sql_query(
/app/backend/server.py:4944:                    ventas_temp_result = execute_sql_query(
/app/backend/server.py:5076:                            "server_id": server_id,
/app/backend/server.py:5109:                    server_id=server_id,
/app/backend/server.py:5161:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:5163:    server_id = params.get('server_id')
/app/backend/server.py:5171:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:5172:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:5195:            almacen_result = execute_sql_query(
/app/backend/server.py:5261:            result = execute_sql_query(
/app/backend/server.py:5340:            result = execute_sql_query(
/app/backend/server.py:5372:                result = execute_sql_query(
/app/backend/server.py:5417:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:5419:    server_id = params.get('server_id')
/app/backend/server.py:5426:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:5427:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:5481:            result = execute_sql_query(
/app/backend/server.py:5550:            result = execute_sql_query(
/app/backend/server.py:5621:    server_id: str
/app/backend/server.py:5696:        cortes_result = execute_sql_query(
/app/backend/server.py:5719:                "server_id": server['id'],
/app/backend/server.py:5988:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:5993:    if not has_server_access(context, request.server_id):
/app/backend/server.py:5994:        logging.warning(f"[RBAC-EXPORT-INV] {current_user.get('email')} sin acceso a servidor {request.server_id}")
/app/backend/server.py:5998:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
/app/backend/server.py:5999:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(request.server_id))
/app/backend/server.py:6004:    almacenes_permitidos = get_almacenes_permitidos(context, request.server_id)
/app/backend/server.py:6008:        f"Server={request.server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:6050:                server=server,
/app/backend/server.py:6253:    - server_id: ID del servidor donde ejecutar
/app/backend/server.py:6258:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:6261:    from core.server_registry import get_server_connection_info
/app/backend/server.py:6263:    server_id = params.get('server_id')
/app/backend/server.py:6267:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:6269:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:6272:        logging.warning(f"[EJECUTAR_CONSULTA_CATALOGO] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:6296:        results = execute_sql_query(
/app/backend/server.py:6324:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:6330:    - server_id: ID del servidor donde ejecutar
/app/backend/server.py:6337:    server_id = params.get('server_id')
/app/backend/server.py:6344:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:6345:    from core.server_registry import get_server_connection_info
/app/backend/server.py:6346:    conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:6353:        results = execute_sql_query(
/app/backend/server.py:6399:        results = execute_sql_query(host, port, database, username, password, query)
/app/backend/server.py:6417:@api_router.get("/debug/tipos-movimiento-live/{server_id}")
/app/backend/server.py:6418:async def debug_tipos_movimiento_live(server_id: str, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:6423:    from core.server_registry import get_server_connection_info
/app/backend/server.py:6425:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:6453:        results = execute_sql_query(
/app/backend/server.py:6481:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:6484:    server_id = params.get('server_id')
/app/backend/server.py:6491:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:6492:    from core.server_registry import get_server_connection_info
/app/backend/server.py:6493:    conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:6508:            almacen_result = execute_sql_query(
/app/backend/server.py:6533:        mov_result = execute_sql_query(
/app/backend/server.py:6568:        ventas_result = execute_sql_query(
/app/backend/server.py:6595:        detalle = execute_sql_query(
/app/backend/server.py:6615:        detalle_kit = execute_sql_query(
/app/backend/server.py:6633:        detalle_directas = execute_sql_query(
/app/backend/server.py:6789:    server_id: Optional[str] = None,
/app/backend/server.py:6801:    from core.server_registry import get_server_connection_info_with_secrets, list_servers as registry_list_servers
/app/backend/server.py:6806:        # ANTES: if server_id: query["id"] = server_id
/app/backend/server.py:6810:        if server_id:
/app/backend/server.py:6812:            server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:6850:            results = execute_sql_query(
/app/backend/server.py:6967:                "server_id": server['id'],
/app/backend/server.py:7060:    server_id: str
/app/backend/server.py:7082:# - GET /compras/inventarios-fisicos/{server_id}
/app/backend/server.py:7083:# - GET /compras/pedidos-vigentes/{server_id}  
/app/backend/server.py:7084:# - GET /compras/parametros/{server_id}
/app/backend/server.py:7086:# - GET /compras/detalle-pedido/{server_id}/{folio}
/app/backend/server.py:7087:# - GET /compras/detalle-pedido-manual/{server_id}
/app/backend/server.py:7088:# - GET /compras/detalle-movimientos/{server_id}
/app/backend/server.py:7089:# - GET /compras/detalle-consumos/{server_id}
/app/backend/server.py:7095:# - GET /compras/dashboard/{server_id}
/app/backend/server.py:7097:# - GET /compras/facturas-proveedor/{server_id}
/app/backend/server.py:7098:# - GET /compras/detalle-factura/{server_id}/{folio}
/app/backend/server.py:7113:async def validate_server_access_by_empresa(server_id: str, credentials: HTTPAuthorizationCredentials) -> dict:
/app/backend/server.py:7121:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:7133:    from core.server_registry import get_server_connection_info
/app/backend/server.py:7138:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:7140:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:7143:        logging.warning(f"[VALIDATE_SERVER_ACCESS] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:7151:    if not has_server_access(context, server_id):
/app/backend/server.py:7154:            f"sin acceso a servidor {server_id}. "
/app/backend/server.py:7164:@api_router.get("/compras/inventarios-fisicos/{server_id}")
/app/backend/server.py:7165:async def obtener_inventarios_fisicos(server_id: str, sucursal: str = None, sucursal_id: str = None, almacen: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7176:    access = await validate_server_access_by_empresa(server_id, credentials)
/app/backend/server.py:7181:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:7185:        f"Usuario={access['user'].get('email')}, Server={server_id}, "
/app/backend/server.py:7195:            from core.unidades_registry import get_unidad_by_server_id
/app/backend/server.py:7196:            unidad_info = get_unidad_by_server_id(server_id)
/app/backend/server.py:7204:            server_id=server_id,
/app/backend/server.py:7242:        almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "A.Al_Cve_Almacen")
/app/backend/server.py:7274:            result = execute_sql_query(
/app/backend/server.py:7285:            log_compras_error("inventarios-fisicos", server_id, "CONNECTION_ERROR", error_msg[:200], server.get('system_type'))
/app/backend/server.py:7291:        almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "A.idalmacen")
/app/backend/server.py:7308:            result = execute_sql_query(
/app/backend/server.py:7317:            log_compras_error("inventarios-fisicos", server_id, "QUERY_ERROR", str(e), server.get('system_type'))
/app/backend/server.py:7322:    log_compras_error("inventarios-fisicos", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/server.py:7325:@api_router.get("/compras/pedidos-vigentes/{server_id}")
/app/backend/server.py:7326:async def obtener_pedidos_vigentes(server_id: str, sucursal: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7335:    access = await validate_server_access_by_empresa(server_id, credentials)
/app/backend/server.py:7340:        f"Usuario={access['user'].get('email')}, Server={server_id}"
/app/backend/server.py:7349:            from core.unidades_registry import get_unidad_by_server_id
/app/backend/server.py:7350:            unidad_info = get_unidad_by_server_id(server_id)
/app/backend/server.py:7358:            server_id=server_id,
/app/backend/server.py:7409:            result = execute_sql_query(
/app/backend/server.py:7420:            log_compras_error("pedidos-vigentes", server_id, "CONNECTION_ERROR", error_msg[:200], server.get('system_type'))
/app/backend/server.py:7442:            result = execute_sql_query(
/app/backend/server.py:7457:@api_router.get("/compras/detalle-pedido-manual/{server_id}")
/app/backend/server.py:7458:async def obtener_detalle_pedido_manual(server_id: str, folio: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7461:    access = await validate_server_access_by_empresa(server_id, credentials)
/app/backend/server.py:7475:        result = execute_sql_query(
/app/backend/server.py:7499:        result = execute_sql_query(
/app/backend/server.py:7512:@api_router.get("/compras/detalle-movimientos/{server_id}")
/app/backend/server.py:7513:async def obtener_detalle_movimientos(server_id: str, codigo_producto: str, almacenes: str, fecha_ini: str, fecha_fin: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7516:    access = await validate_server_access_by_empresa(server_id, credentials)
/app/backend/server.py:7540:        result = execute_sql_query(
/app/backend/server.py:7549:@api_router.get("/compras/detalle-consumos/{server_id}")
/app/backend/server.py:7550:async def obtener_detalle_consumos(server_id: str, codigo_producto: str, sucursal_codigo: str, fecha_ini: str, fecha_fin: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7553:    access = await validate_server_access_by_empresa(server_id, credentials)
/app/backend/server.py:7574:        result = execute_sql_query(
/app/backend/server.py:7584:@api_router.get("/compras/detalle-pedido/{server_id}/{folio}")
/app/backend/server.py:7585:async def obtener_detalle_pedido(server_id: str, folio: str, tipo: str = "PEDIDO", credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7591:    access = await validate_server_access_by_empresa(server_id, credentials)
/app/backend/server.py:7597:        f"Server={server_id}, Folio={folio}, Tipo={tipo}"
/app/backend/server.py:7625:        result = execute_sql_query(
/app/backend/server.py:7645:    access = await validate_server_access_by_empresa(request.server_id, credentials)
/app/backend/server.py:7650:    almacenes_permitidos = get_almacenes_permitidos(context, request.server_id)
/app/backend/server.py:7654:        f"Server={request.server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:7682:        almacen_rbac_filter = get_almacenes_sql_filter(context, request.server_id, "A.Al_Cve_Almacen")
/app/backend/server.py:7705:        almacen_result = execute_sql_query(
/app/backend/server.py:7745:            inv_result = execute_sql_query(
/app/backend/server.py:7788:        productos = execute_sql_query(
/app/backend/server.py:7803:            inv_detalle = execute_sql_query(
/app/backend/server.py:7831:        mov_result = execute_sql_query(
/app/backend/server.py:7865:            ventas_result = execute_sql_query(
/app/backend/server.py:7881:            salidas_result = execute_sql_query(
/app/backend/server.py:7899:        inv_final_result = execute_sql_query(
/app/backend/server.py:7913:            inv_final_detalle = execute_sql_query(
/app/backend/server.py:7931:            ped_result = execute_sql_query(
/app/backend/server.py:7945:                ped_result = execute_sql_query(
/app/backend/server.py:8065:@api_router.get("/compras/parametros/{server_id}")
/app/backend/server.py:8067:    server_id: str, 
/app/backend/server.py:8084:    params = await obtener_parametros(server_id, sucursal_id)
/app/backend/server.py:8085:    params['server_id'] = server_id  # Asegurar que siempre incluya server_id
/app/backend/server.py:8099:    server_id = params.get('server_id')
/app/backend/server.py:8100:    if not server_id:
/app/backend/server.py:8101:        raise HTTPException(status_code=400, detail="server_id es requerido")
/app/backend/server.py:8109:    result = await guardar_parametros(server_id, sucursal_id, params)
/app/backend/server.py:8117:    server_id: str
/app/backend/server.py:8136:    server_id: str
/app/backend/server.py:8149:    from core.server_registry import get_server_connection_info
/app/backend/server.py:8150:    server = await get_server_connection_info(request.server_id, db=db)
/app/backend/server.py:8175:                    result = execute_sql_query(
/app/backend/server.py:8202:                result = execute_sql_query(
/app/backend/server.py:8228:                    result = execute_sql_query(
/app/backend/server.py:8257:                    result = execute_sql_query(
/app/backend/server.py:8284:                        result = execute_sql_query(
/app/backend/server.py:8311:                        result = execute_sql_query(
/app/backend/server.py:8350:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:8354:    logging.info(f"[AUDITORIA] Iniciando auditoría - server: {request.server_id}, sucursal: {request.sucursal}")
/app/backend/server.py:8357:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
/app/backend/server.py:8358:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(request.server_id))
/app/backend/server.py:8367:            test_result = execute_sql_query(
/app/backend/server.py:8411:            tipos_alm_result = execute_sql_query(
/app/backend/server.py:8459:                requi_result = execute_sql_query(
/app/backend/server.py:8518:                    tipo_result = execute_sql_query(
/app/backend/server.py:8551:                    result_ini = execute_sql_query(
/app/backend/server.py:8626:                    mov_result = execute_sql_query(
/app/backend/server.py:8646:                    entrada_result = execute_sql_query(
/app/backend/server.py:8664:                    salida_result = execute_sql_query(
/app/backend/server.py:8688:                    mov_result = execute_sql_query(
/app/backend/server.py:8720:                    salidas_result = execute_sql_query(
/app/backend/server.py:8740:                consumos_result = execute_sql_query(
/app/backend/server.py:8777:                        tipo_result = execute_sql_query(
/app/backend/server.py:8807:                        result_fin = execute_sql_query(
/app/backend/server.py:9049:    server_id: str
/app/backend/server.py:9073:    server_id: str
/app/backend/server.py:9095:            server=EDARSAHUB_TABLERO_CONFIG['host'],
/app/backend/server.py:9098:            database=EDARSAHUB_TABLERO_CONFIG['database'],
/app/backend/server.py:9109:                (unidad_negocio_id, unidad_negocio_nombre, server_id, sucursal, 
/app/backend/server.py:9117:                request.server_id,
/app/backend/server.py:9161:            server=EDARSAHUB_TABLERO_CONFIG['host'],
/app/backend/server.py:9164:            database=EDARSAHUB_TABLERO_CONFIG['database'],
/app/backend/server.py:9171:            SELECT id, unidad_negocio_id, unidad_negocio_nombre, server_id, sucursal,
/app/backend/server.py:9220:            server=EDARSAHUB_TABLERO_CONFIG['host'],
/app/backend/server.py:9223:            database=EDARSAHUB_TABLERO_CONFIG['database'],
/app/backend/server.py:9265:            server=EDARSAHUB_TABLERO_CONFIG['host'],
/app/backend/server.py:9268:            database=EDARSAHUB_TABLERO_CONFIG['database'],
/app/backend/server.py:9314:    print("Server ID:", request.server_id)
/app/backend/server.py:9317:    from core.server_registry import get_server_connection_info
/app/backend/server.py:9318:    server = await get_server_connection_info(request.server_id, db=db)
/app/backend/server.py:9387:                result_pres = execute_sql_query(
/app/backend/server.py:9435:                result_ins = execute_sql_query(
/app/backend/server.py:9505:    server_id: str
/app/backend/server.py:9519:    from core.server_registry import get_server_connection_info
/app/backend/server.py:9520:    server = await get_server_connection_info(request.server_id, db=db)
/app/backend/server.py:9567:            result_ventas = execute_sql_query(
/app/backend/server.py:9615:    server_id: str
/app/backend/server.py:9621:@api_router.get("/compras/dashboard/{server_id}")
/app/backend/server.py:9623:    server_id: str, 
/app/backend/server.py:9634:    access = await validate_server_access_by_empresa(server_id, credentials)
/app/backend/server.py:9734:            result_compras = execute_sql_query(
/app/backend/server.py:9758:            result_req = execute_sql_query(
/app/backend/server.py:9773:            result_prov = execute_sql_query(
/app/backend/server.py:9794:            result_top = execute_sql_query(
/app/backend/server.py:9838:            logging.info(f"[COMPRAS_DASHBOARD_SR] Database={server.get('database')}, Filtros: ({anios_cond}) AND ({meses_cond})")
/app/backend/server.py:9850:            result_compras = execute_sql_query(
/app/backend/server.py:9868:                        "server_id": server_id,
/app/backend/server.py:9888:            result_prov = execute_sql_query(
/app/backend/server.py:9908:            result_top = execute_sql_query(
/app/backend/server.py:9948:    from core.server_registry import get_server_connection_info
/app/backend/server.py:9949:    server = await get_server_connection_info(request.server_id, db=db)
/app/backend/server.py:9994:            result = execute_sql_query(
/app/backend/server.py:10045:            result = execute_sql_query(
/app/backend/server.py:10082:        log_compras_error("analisis", request.server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/server.py:10094:@api_router.get("/compras/facturas-proveedor/{server_id}")
/app/backend/server.py:10095:async def obtener_facturas_proveedor(server_id: str, proveedor_codigo: str, anio: int, meses: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:10100:    from core.server_registry import get_server_connection_info
/app/backend/server.py:10101:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:10110:            log_compras_adapter_selected("facturas-proveedor", server_id, system_type, "MPRO_ADAPTER")
/app/backend/server.py:10130:            result = execute_sql_query(
/app/backend/server.py:10150:        log_compras_adapter_selected("facturas-proveedor", server_id, system_type, "NO_ADAPTER_AVAILABLE")
/app/backend/server.py:10161:@api_router.get("/compras/detalle-factura/{server_id}/{folio}")
/app/backend/server.py:10162:async def obtener_detalle_factura(server_id: str, folio: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:10167:    from core.server_registry import get_server_connection_info
/app/backend/server.py:10168:    server = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:10187:            result = execute_sql_query(
/app/backend/server.py:10205:        log_compras_adapter_selected("detalle-factura", server_id, system_type, "NO_ADAPTER_AVAILABLE")
/app/backend/server.py:10272:async def get_server_connection_status(server_id: str):
/app/backend/server.py:10274:    status = await db.server_status.find_one({"server_id": server_id})
/app/backend/server.py:10277:async def save_server_connection_status(server_id: str, is_online: bool, response_time_ms: int = None):
/app/backend/server.py:10280:        {"server_id": server_id},
/app/backend/server.py:10283:                "server_id": server_id,
/app/backend/server.py:10292:async def is_server_recently_offline(server_id: str, minutes_threshold: int = 10):
/app/backend/server.py:10294:    status = await get_server_connection_status(server_id)
/app/backend/server.py:10316:async def get_cached_kpis(server_id: str, periodo_key: str):
/app/backend/server.py:10319:        "server_id": server_id,
/app/backend/server.py:10324:async def save_kpis_cache(server_id: str, periodo_key: str, kpis: dict):
/app/backend/server.py:10327:        {"server_id": server_id, "periodo_key": periodo_key},
/app/backend/server.py:10330:                "server_id": server_id,
/app/backend/server.py:10407:    from core.db import execute_sql_query
/app/backend/server.py:10462:        results = execute_sql_query(
/app/backend/server.py:10567:@api_router.get("/explorador/tablas/{server_id}")
/app/backend/server.py:10569:    server_id: str,
/app/backend/server.py:10581:    from core.server_registry import get_server_connection_info
/app/backend/server.py:10591:        api_conn = await get_api_connection_by_id_full(server_id)
/app/backend/server.py:10595:        logging.debug(f"[EXPLORADOR] {server_id} no es API_LOCAL: {e}")
/app/backend/server.py:10599:        conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:10607:    await validate_server_access_unified(current_user, server_id)
/app/backend/server.py:10611:        return await _cargar_tablas_api_local(api_conn, server_id)
/app/backend/server.py:10620:async def _cargar_tablas_api_local(api_conn: Dict, server_id: str) -> Dict:
/app/backend/server.py:10658:            api_id=server_id,
/app/backend/server.py:10814:@api_router.get("/explorador/columnas/{server_id}/{tabla}")
/app/backend/server.py:10816:    server_id: str,
/app/backend/server.py:10830:    from core.server_registry import get_server_connection_info
/app/backend/server.py:10831:    from core.db import execute_sql_query_params
/app/backend/server.py:10841:        api_conn = await get_api_connection_by_id_full(server_id)
/app/backend/server.py:10845:        logging.debug(f"[EXPLORADOR][COLUMNAS] {server_id} no es API_LOCAL: {e}")
/app/backend/server.py:10849:        conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:10857:    await validate_server_access_unified(current_user, server_id)
/app/backend/server.py:10879:                api_id=server_id,
/app/backend/server.py:10923:            result = execute_sql_query_params(
/app/backend/server.py:10937:@api_router.get("/explorador/relaciones/{server_id}/{tabla}")
/app/backend/server.py:10939:    server_id: str,
/app/backend/server.py:10946:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:10950:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:10951:    from core.server_registry import get_server_connection_info
/app/backend/server.py:10952:    from core.db import execute_sql_query_params
/app/backend/server.py:10954:    conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:10959:    await validate_server_access_unified(current_user, server_id)
/app/backend/server.py:10986:        result = execute_sql_query_params(
/app/backend/server.py:10999:@api_router.get("/explorador/preview/{server_id}/{tabla}")
/app/backend/server.py:11001:    server_id: str,
/app/backend/server.py:11016:    from core.server_registry import get_server_connection_info
/app/backend/server.py:11026:        api_conn = await get_api_connection_by_id_full(server_id)
/app/backend/server.py:11030:        logging.debug(f"[EXPLORADOR][PREVIEW] {server_id} no es API_LOCAL: {e}")
/app/backend/server.py:11034:        conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:11042:    await validate_server_access_unified(current_user, server_id)
/app/backend/server.py:11055:                api_id=server_id,
/app/backend/server.py:11092:            result = execute_sql_query(
/app/backend/server.py:11107:@api_router.post("/explorador/query/{server_id}")
/app/backend/server.py:11109:    server_id: str,
/app/backend/server.py:11117:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:11127:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:11128:    from core.server_registry import get_server_connection_info
/app/backend/server.py:11131:    conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:11144:        result = execute_sql_query(
/app/backend/server.py:11158:@api_router.post("/explorador/ejecutar-script/{server_id}")
/app/backend/server.py:11160:    server_id: str,
/app/backend/server.py:11171:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:11187:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:11188:    from core.server_registry import get_server_connection_info
/app/backend/server.py:11189:    conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:11202:        f"Server: {server_id}, Titulo: {titulo}, Length: {len(script)} chars"
/app/backend/server.py:11272:            server=host,
/app/backend/server.py:11274:            database=conn_info['database'],
/app/backend/server.py:11333:        "server_id": server_id,
/app/backend/server.py:12156:EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"
/app/backend/server.py:12163:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:12166:    from core.server_registry import get_server_connection_info
/app/backend/server.py:12168:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True}))
/app/backend/server.py:12170:    conn_info = await get_server_connection_info(EDARSA_HUB_SERVER_ID, db=db)
/app/backend/server.py:12173:        logging.error(f"[EDARSA_HUB_QUERY] Servidor EDARSA HUB no encontrado via registry. ID={EDARSA_HUB_SERVER_ID}")
/app/backend/server.py:12179:        result = execute_sql_query(
/app/backend/server.py:13002:@api_router.post("/explorador/guardar-script/{server_id}")
/app/backend/server.py:13004:    server_id: str,
/app/backend/server.py:13012:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:13017:    El documento NO contiene credenciales, solo referencia al server_id y nombre.
/app/backend/server.py:13022:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:13023:    from core.server_registry import get_server_connection_info
/app/backend/server.py:13024:    conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:13042:    # IMPORTANTE: No incluir credenciales, solo server_id y nombre para referencia
/app/backend/server.py:13044:        "server_id": server_id,
/app/backend/server.py:13057:@api_router.get("/explorador/scripts-pendientes/{server_id}")
/app/backend/server.py:13059:    server_id: str,
/app/backend/server.py:13067:        {"server_id": server_id, "estado": "pendiente"},
/app/backend/server.py:13137:@api_router.post("/explorador/ejecutar-con-credenciales/{server_id}")
/app/backend/server.py:13139:    server_id: str,
/app/backend/server.py:13151:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:13157:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:13158:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:13238:            server=host,
/app/backend/server.py:13240:            database=server['database'],
/app/backend/server.py:13299:        "server_id": server_id,
/app/backend/server.py:13791:@api_router.get("/explorador/buscar/{server_id}")
/app/backend/server.py:13793:    server_id: str,
/app/backend/server.py:13804:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:13809:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:13810:    from core.server_registry import get_server_connection_info
/app/backend/server.py:13811:    conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:13816:    await validate_server_access_unified(current_user, server_id)
/app/backend/server.py:13842:            tablas = execute_sql_query(
/app/backend/server.py:13859:            columnas = execute_sql_query(
/app/backend/server.py:13878:            cols_texto = execute_sql_query(
/app/backend/server.py:13892:                datos = execute_sql_query(
/app/backend/server.py:13907:            tablas_texto = execute_sql_query(
/app/backend/server.py:13925:                cols = execute_sql_query(
/app/backend/server.py:13935:                        datos = execute_sql_query(
/app/backend/server.py:14027:    server_id: str = Query(...),
/app/backend/server.py:14077:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:14078:    from core.server_registry import get_server_connection_info_with_secrets
/app/backend/server.py:14079:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py:14099:    await validate_server_access_unified(current_user, server_id)
/app/backend/server.py:14143:        result = execute_sql_query(
/app/backend/server.py:14340:    server_id: str = Query(...),
/app/backend/server.py:14347:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:14356:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:14357:    from core.server_registry import get_server_connection_info
/app/backend/server.py:14358:    conn_info = await get_server_connection_info(server_id, db=db)
/app/backend/server.py:14377:        result = execute_sql_query(
/app/backend/server.py:14411:        "server_id": informe.server_id,
/app/backend/server.py:14447:    server_id: Optional[str] = None,
/app/backend/server.py:14462:    if server_id:
/app/backend/server.py:14463:        filtro["server_id"] = server_id
/app/backend/server.py:14969:EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"
/app/backend/server.py:14973:    server_id: str = Query(default=None, description="ID del servidor. Si no se especifica, usa EDARSA HUB"),
/app/backend/server.py:14984:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:14988:        server_id: ID del servidor a probar (default: EDARSA HUB)
/app/backend/server.py:15003:    from core.server_registry import get_server_connection_info
/app/backend/server.py:15006:    target_server_id = server_id or EDARSA_HUB_SERVER_ID
/app/backend/server.py:15007:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))
/app/backend/server.py:15008:    conn_info = await get_server_connection_info(target_server_id, db=db)
/app/backend/server.py:15013:            "error": f"Servidor con ID '{target_server_id}' no encontrado o inactivo",
/app/backend/server.py:15026:        database=conn_info['database'],
/app/backend/server.py:15032:    result["server_id"] = target_server_id
/app/backend/server.py:15042:    server_id: str = Query(default=None, description="ID del servidor"),
/app/backend/server.py:15051:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:15055:        server_id: ID del servidor (default: EDARSA HUB)
/app/backend/server.py:15061:    from core.db import execute_sql_query, ResilientConfig
/app/backend/server.py:15062:    from core.server_registry import get_server_connection_info
/app/backend/server.py:15064:    target_server_id = server_id or EDARSA_HUB_SERVER_ID
/app/backend/server.py:15065:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))
/app/backend/server.py:15066:    conn_info = await get_server_connection_info(target_server_id, db=db)
/app/backend/server.py:15071:            "error": f"Servidor '{target_server_id}' no encontrado",
/app/backend/server.py:15081:    results = execute_sql_query(
/app/backend/server.py:15084:        database=conn_info['database'],
/app/backend/server.py:17938:init_portal_db(db, JWT_SECRET, execute_sql_query)
/app/backend/api/catalogos_sistemas.py:209:    from core.db import execute_sql_query
/app/backend/api/catalogos_sistemas.py:236:        results = execute_sql_query(
/app/backend/api/configuracion_operativa_unidades.py:99:        server=EDARSAHUB_CONFIG['host'],
/app/backend/api/configuracion_operativa_unidades.py:101:        database=EDARSAHUB_CONFIG['database'],
/app/backend/api/admin_data_quality.py:29:from core.db import execute_sql_query
/app/backend/api/admin_data_quality.py:55:        result = execute_sql_query(
/app/backend/api/admin_scheduler_resync.py:57:            server=EDARSAHUB_CONFIG['host'],
/app/backend/api/admin_scheduler_resync.py:59:            database=EDARSAHUB_CONFIG['database'],
/app/backend/api/admin_scheduler_resync.py:157:        'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b',
/app/backend/api/admin_scheduler_resync.py:163:        'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6',
/app/backend/api/admin_scheduler_resync.py:169:        'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f',
/app/backend/api/admin_scheduler_resync.py:175:        'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
/app/backend/api/admin_scheduler_resync.py:181:        'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
/app/backend/api/admin_scheduler_resync.py:203:def _validar_conectividad(server_id: str) -> Dict[str, Any]:
/app/backend/api/admin_scheduler_resync.py:213:            get_server_connection_config,
/app/backend/api/admin_scheduler_resync.py:218:        config = get_server_connection_config(server_id)
/app/backend/api/admin_scheduler_resync.py:240:            recent_sync_ok = _verificar_syncs_recientes(server_id)
/app/backend/api/admin_scheduler_resync.py:255:def _verificar_syncs_recientes(server_id: str, minutos: int = 30) -> bool:
/app/backend/api/admin_scheduler_resync.py:261:        WHERE server_id = '{server_id}'
/app/backend/api/admin_scheduler_resync.py:330:    server_id: str = None,
/app/backend/api/admin_scheduler_resync.py:347:            job_name, run_id, accion, server_id,
/app/backend/api/admin_scheduler_resync.py:407:    validacion_conectividad = _validar_conectividad(unidad['server_id'])
/app/backend/api/admin_scheduler_resync.py:423:            'server_id': unidad['server_id'],
/app/backend/api/admin_scheduler_resync.py:480:        'conectividad': _validar_conectividad(unidad['server_id']),
/app/backend/api/admin_scheduler_resync.py:510:            server_id=unidad['server_id'],
/app/backend/api/admin_scheduler_resync.py:551:            server_id=unidad['server_id'],
/app/backend/api/admin_scheduler_resync.py:600:        server_id=unidad['server_id'],
/app/backend/api/admin_scheduler_resync.py:687:                'server_id': r.get('ServerID'),
/app/backend/api/admin_scheduler_resync.py:754:    from modules.comercial_v2.sync_comercial_edarsahub import get_server_connection_config
/app/backend/api/admin_scheduler_resync.py:758:        config = get_server_connection_config(unidad_config['server_id'])
/app/backend/api/admin_scheduler_resync.py:764:            server=config['host'],
/app/backend/api/admin_scheduler_resync.py:766:            database=config['database_name'],
/app/backend/api/admin_scheduler_resync.py:863:            server_id=unidad_config['server_id'],
/app/backend/api/sync_receiver.py:16:- Validación server_id en token == payload
/app/backend/api/sync_receiver.py:20:- Registra agent_id, server_id, timestamp
/app/backend/api/sync_receiver.py:76:def create_agent_token(server_id: str, agent_id: str) -> str:
/app/backend/api/sync_receiver.py:81:        "server_id": server_id,
/app/backend/api/sync_receiver.py:96:            "server_id": payload.get("server_id"),
/app/backend/api/sync_receiver.py:129:def validate_server_id_match(agent: Dict, payload_server_id: str) -> None:
/app/backend/api/sync_receiver.py:130:    """Valida que server_id en token coincida con payload."""
/app/backend/api/sync_receiver.py:131:    if agent["server_id"] != payload_server_id:
/app/backend/api/sync_receiver.py:132:        raise HTTPException(403, f"server_id mismatch: token={agent['server_id']}, payload={payload_server_id}")
/app/backend/api/sync_receiver.py:152:        "server_id": payload.server_id,
/app/backend/api/sync_receiver.py:160:        server_id=payload.server_id,
/app/backend/api/sync_receiver.py:185:    validate_server_id_match(agent, payload.server_id)
/app/backend/api/sync_receiver.py:187:    server = await db.sql_servers.find_one({"id": payload.server_id})
/app/backend/api/sync_receiver.py:189:        raise HTTPException(404, f"Servidor {payload.server_id} no encontrado")
/app/backend/api/sync_receiver.py:228:    validate_server_id_match(agent, payload.server_id)
/app/backend/api/sync_receiver.py:237:                "server_id": payload.server_id,
/app/backend/api/sync_receiver.py:262:        "server_id": agent["server_id"],
/app/backend/api/sync_receiver.py:276:    server = await db.sql_servers.find_one({"id": request.server_id})
/app/backend/api/sync_receiver.py:278:        raise HTTPException(404, f"Servidor {request.server_id} no encontrado")
/app/backend/api/sync_receiver.py:281:    agent_token = create_agent_token(request.server_id, agent_id)
/app/backend/api/sync_receiver.py:291:                "server_id": request.server_id,
/app/backend/api/sync_receiver.py:303:    logger.info(f"[{MODULE_NAME}] Token generated for {agent_id} server {request.server_id}")
/app/backend/api/sync_receiver.py:308:        server_id=request.server_id,
/app/backend/api/sync_receiver.py:321:    await coll.create_index("server_id", name="idx_server_id")
/app/backend/api/admin_core_connections.py:32:from core.db import execute_sql_query, get_mongo_db
/app/backend/api/admin_core_connections.py:153:    return execute_sql_query(
/app/backend/api/admin_core_connections.py:163:def get_core_connection_by_id(server_id: str) -> Optional[Dict]:
/app/backend/api/admin_core_connections.py:170:    safe_id = server_id.replace("'", "''")
/app/backend/api/admin_core_connections.py:197:    result = execute_sql_query(
/app/backend/api/admin_core_connections.py:291:        'server_id': conn.get('id'),
/app/backend/api/admin_core_connections.py:388:@router.get("/{server_id}")
/app/backend/api/admin_core_connections.py:390:    server_id: str,
/app/backend/api/admin_core_connections.py:399:    conn = get_core_connection_by_id(server_id)
/app/backend/api/admin_core_connections.py:424:@router.post("/{server_id}/test")
/app/backend/api/admin_core_connections.py:426:    server_id: str,
/app/backend/api/admin_core_connections.py:437:    conn = get_core_connection_by_id(server_id)
/app/backend/api/dba_credential_p0d.py:35:from core.db import execute_sql_query
/app/backend/api/dba_credential_p0d.py:63:EDARSAHUB_SERVER_ID = 'f8a9049a-96e8-4210-84ae-595ffa2822fa'
/app/backend/api/dba_credential_p0d.py:370:            server=DBA_SERVER_CONFIG['host'],
/app/backend/api/dba_credential_p0d.py:372:            database='msdb',  # Conectar a msdb para validar permisos
/app/backend/api/dba_credential_p0d.py:485:            server=DBA_SERVER_CONFIG['host'],
/app/backend/api/dba_credential_p0d.py:487:            database='msdb',
/app/backend/api/sync_schemas.py:23:    server_id: str
/app/backend/api/sync_schemas.py:32:    server_id: str
/app/backend/api/sync_schemas.py:42:    server_id: str
/app/backend/api/sync_schemas.py:50:    server_id: str
/app/backend/core/server_registry.py:285:        from core.db import execute_sql_query
/app/backend/core/server_registry.py:306:        results = execute_sql_query(
/app/backend/core/server_registry.py:324:def _get_server_by_id_from_sql(server_id: str) -> Optional[Dict]:
/app/backend/core/server_registry.py:330:        from core.db import execute_sql_query
/app/backend/core/server_registry.py:333:        safe_id = server_id.replace("'", "''")
/app/backend/core/server_registry.py:341:        results = execute_sql_query(
/app/backend/core/server_registry.py:351:            logger.info(f"[SERVER_REGISTRY][SQL_HIT] Servidor {server_id} obtenido desde SQL")
/app/backend/core/server_registry.py:354:        logger.debug(f"[SERVER_REGISTRY][SQL_MISS] Servidor {server_id} no encontrado en SQL")
/app/backend/core/server_registry.py:358:        logger.warning(f"[SERVER_REGISTRY][SQL_ERROR] Error buscando servidor {server_id}: {e}")
/app/backend/core/server_registry.py:428:async def _get_server_by_id_from_mongo(db, server_id: str) -> Optional[Dict]:
/app/backend/core/server_registry.py:434:            {'id': server_id, 'active': True},
/app/backend/core/server_registry.py:439:            logger.warning(f"[SERVER_REGISTRY][MONGODB_FALLBACK_USED] Servidor {server_id} obtenido desde MongoDB legacy")
/app/backend/core/server_registry.py:445:        logger.error(f"[SERVER_REGISTRY][MONGODB_ERROR] Error buscando servidor {server_id}: {e}")
/app/backend/core/server_registry.py:454:    server_id: str,
/app/backend/core/server_registry.py:468:        server_id: ID del servidor (UUID)
/app/backend/core/server_registry.py:481:        server = _get_server_by_id_from_sql(server_id)
/app/backend/core/server_registry.py:485:        server = await _get_server_by_id_from_mongo(db, server_id)
/app/backend/core/server_registry.py:589:    server_id: Optional[str] = None,
/app/backend/core/server_registry.py:611:    if not server_id:
/app/backend/core/server_registry.py:612:        context['errors'].append('server_id es requerido')
/app/backend/core/server_registry.py:616:    server = await get_server_by_id(server_id, db=db, mask_secrets=False)
/app/backend/core/server_registry.py:619:        context['errors'].append(f'Servidor {server_id} no encontrado')
/app/backend/core/server_registry.py:694:async def get_server_connection_info(
/app/backend/core/server_registry.py:695:    server_id: str,
/app/backend/core/server_registry.py:708:        server_id: ID del servidor
/app/backend/core/server_registry.py:717:    server = await get_server_by_id(server_id, db=db, mask_secrets=False)
/app/backend/core/server_registry.py:728:                logger.warning(f"[SERVER_REGISTRY][ACCESS_DENIED] Usuario sin permisos para servidor {server_id}")
/app/backend/core/server_registry.py:750:    server_id: str,
/app/backend/core/server_registry.py:763:        server_id: ID del servidor
/app/backend/core/server_registry.py:776:        server = _get_server_by_id_from_sql(server_id)
/app/backend/core/server_registry.py:780:            logger.info(f"[SERVER_REGISTRY][SUCURSALES][SQL_HIT] {len(sucursales)} sucursales para servidor {server_id}")
/app/backend/core/server_registry.py:787:                {'server_id': server_id, 'activo': {'$ne': False}},
/app/backend/core/server_registry.py:794:                server_mongo = await _get_server_by_id_from_mongo(db, server_id)
/app/backend/core/server_registry.py:800:                logger.warning(f"[SERVER_REGISTRY][SUCURSALES][MONGODB_FALLBACK] {len(sucursales)} sucursales para servidor {server_id}")
/app/backend/core/server_registry.py:830:    incluyendo aliases legacy (_id, server_id, nombre, etc.)
/app/backend/core/server_registry.py:848:        'server_id': str(record.get('id', record.get('server_id', ''))),  # Alias backend
/app/backend/core/server_registry.py:1060:    server_id = str(uuid.uuid4())
/app/backend/core/server_registry.py:1091:        server_id,
/app/backend/core/server_registry.py:1109:        server_id  # mongodb_id será el mismo inicialmente
/app/backend/core/server_registry.py:1124:    logger.info(f"[SERVER_REGISTRY][CREATE_SQL_SUCCESS] Servidor creado en SQL: {server_id}")
/app/backend/core/server_registry.py:1133:                'id': server_id,
/app/backend/core/server_registry.py:1151:            logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado a MongoDB: {server_id}")
/app/backend/core/server_registry.py:1160:        'id': server_id,
/app/backend/core/server_registry.py:1173:    server_id: str,
/app/backend/core/server_registry.py:1185:        server_id: ID del servidor (SQL id o mongodb_id)
/app/backend/core/server_registry.py:1194:    logger.info(f"[SERVER_REGISTRY][UPDATE_SQL_START] Actualizando servidor: {server_id}")
/app/backend/core/server_registry.py:1207:    existing = _get_server_by_id_from_sql(server_id)
/app/backend/core/server_registry.py:1211:            'error': f'Servidor {server_id} no encontrado en base de datos principal',
/app/backend/core/server_registry.py:1310:    update_values.append(server_id)  # Para WHERE
/app/backend/core/server_registry.py:1311:    update_values.append(server_id)  # Para mongodb_id fallback
/app/backend/core/server_registry.py:1329:    logger.info(f"[SERVER_REGISTRY][UPDATE_SQL_SUCCESS] Servidor actualizado en SQL: {server_id}")
/app/backend/core/server_registry.py:1347:                {'id': server_id},
/app/backend/core/server_registry.py:1350:            logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado a MongoDB: {server_id}")
/app/backend/core/server_registry.py:1358:        'id': server_id,
/app/backend/core/server_registry.py:1367:    server_id: str,
/app/backend/core/server_registry.py:1380:        server_id: ID del servidor
/app/backend/core/server_registry.py:1389:    logger.info(f"[SERVER_REGISTRY][DELETE_SQL_START] {'Desactivando' if soft_delete else 'Eliminando'} servidor: {server_id}")
/app/backend/core/server_registry.py:1392:    existing = _get_server_by_id_from_sql(server_id)
/app/backend/core/server_registry.py:1396:            'error': f'Servidor {server_id} no encontrado',
/app/backend/core/server_registry.py:1417:        params = (now, server_id, server_id)
/app/backend/core/server_registry.py:1423:        params = (server_id, server_id)
/app/backend/core/server_registry.py:1435:    logger.info(f"[SERVER_REGISTRY][DELETE_SQL_SUCCESS] Servidor {'desactivado' if soft_delete else 'eliminado'} en SQL: {server_id}")
/app/backend/core/server_registry.py:1445:                    {'id': server_id},
/app/backend/core/server_registry.py:1449:                await db.servers.delete_one({'id': server_id})
/app/backend/core/server_registry.py:1450:            logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado a MongoDB: {server_id}")
/app/backend/core/server_registry.py:1458:        'id': server_id,
/app/backend/core/server_registry.py:1467:async def sync_server_to_mongo(sql_server_id: str, db=None) -> Dict:
/app/backend/core/server_registry.py:1474:        sql_server_id: ID del servidor en SQL
/app/backend/core/server_registry.py:1488:    server = _get_server_by_id_from_sql(sql_server_id)
/app/backend/core/server_registry.py:1492:            'error': f'Servidor {sql_server_id} no encontrado en SQL',
/app/backend/core/server_registry.py:1496:    logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_START] Sincronizando servidor: {sql_server_id}")
/app/backend/core/server_registry.py:1526:        logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado: {sql_server_id}")
/app/backend/core/server_registry.py:1616:        'server_id': str(sql_record.get('id', '')),  # Alias backend
/app/backend/core/server_registry.py:1855:        from core.db import execute_sql_query
/app/backend/core/server_registry.py:1864:            CAST(server_id AS VARCHAR(50)) as server_id,
/app/backend/core/server_registry.py:1876:        results = execute_sql_query(
/app/backend/core/server_registry.py:1891:                'server_id': str(row.get('server_id', '')),
/app/backend/core/server_registry.py:1922:        - server_id: ID del servidor asociado
/app/backend/core/server_registry.py:1965:        from core.db import execute_sql_query
/app/backend/core/server_registry.py:1975:            CAST(u.server_id AS VARCHAR(50)) as server_id,
/app/backend/core/server_registry.py:1990:        LEFT JOIN Servidores_Conexiones s ON CAST(u.server_id AS uniqueidentifier) = s.id
/app/backend/core/server_registry.py:1995:        results = execute_sql_query(
/app/backend/core/server_registry.py:2014:            'server_id': str(row.get('server_id', '')),
/app/backend/core/server_registry.py:2041:def resolve_unidad_by_server_sucursal(server_id: str, sucursal_id: Optional[str] = None) -> Optional[Dict]:
/app/backend/core/server_registry.py:2043:    Resuelve la unidad de negocio por server_id y sucursal_id.
/app/backend/core/server_registry.py:2048:        server_id: ID del servidor
/app/backend/core/server_registry.py:2067:    if not server_id:
/app/backend/core/server_registry.py:2071:        from core.db import execute_sql_query
/app/backend/core/server_registry.py:2074:        safe_server_id = server_id.replace("'", "''")
/app/backend/core/server_registry.py:2084:                CAST(server_id AS VARCHAR(50)) as server_id,
/app/backend/core/server_registry.py:2090:            WHERE (CAST(server_id AS VARCHAR(50)) = '{safe_server_id}' 
/app/backend/core/server_registry.py:2091:                   OR server_id = '{safe_server_id}')
/app/backend/core/server_registry.py:2096:            # Sin sucursal, buscar por server_id donde sucursal sea null (SoftRestaurant)
/app/backend/core/server_registry.py:2102:                CAST(server_id AS VARCHAR(50)) as server_id,
/app/backend/core/server_registry.py:2108:            WHERE (CAST(server_id AS VARCHAR(50)) = '{safe_server_id}' 
/app/backend/core/server_registry.py:2109:                   OR server_id = '{safe_server_id}')
/app/backend/core/server_registry.py:2114:        results = execute_sql_query(
/app/backend/core/server_registry.py:2131:                    CAST(server_id AS VARCHAR(50)) as server_id,
/app/backend/core/server_registry.py:2137:                WHERE (CAST(server_id AS VARCHAR(50)) = '{safe_server_id}' 
/app/backend/core/server_registry.py:2138:                       OR server_id = '{safe_server_id}')
/app/backend/core/server_registry.py:2142:                results = execute_sql_query(
/app/backend/core/server_registry.py:2152:            logger.warning(f"[SERVER_REGISTRY][RESOLVE] No se encontró unidad para server={server_id}, sucursal={sucursal_id}")
/app/backend/core/server_registry.py:2161:            'server_id': str(row.get('server_id', '')),
/app/backend/core/server_registry.py:2169:        logger.info(f"[SERVER_REGISTRY][RESOLVE][SQL_HIT] Unidad {unidad['codigo']} resuelta para server={server_id}, sucursal={sucursal_id}")
/app/backend/core/server_registry.py:2186:    - Cada unidad tiene server_id
/app/backend/core/server_registry.py:2234:        # 3. Verificar que cada unidad tiene server_id
/app/backend/core/server_registry.py:2236:            if not u.get('server_id'):
/app/backend/core/server_registry.py:2237:                result['errors'].append(f"Unidad {u['codigo']} sin server_id")
/app/backend/core/server_registry.py:2262:        server_ids = set(u['server_id'] for u in unidades if u.get('server_id'))
/app/backend/core/server_registry.py:2264:        for server_id in server_ids:
/app/backend/core/server_registry.py:2265:            server = _get_server_by_id_from_sql(server_id)
/app/backend/core/server_registry.py:2268:                    'id': server_id,
/app/backend/core/server_registry.py:2273:                    result['warnings'].append(f"Servidor {server_id} ({server.get('name')}) está inactivo")
/app/backend/core/server_registry.py:2275:                result['errors'].append(f"Servidor no encontrado: {server_id}")
/app/backend/core/server_registry.py:2280:            logger.info(f"[SERVER_REGISTRY][INTEGRITY] Validación exitosa: {len(unidades)} unidades, {len(server_ids)} servidores")
/app/backend/core/server_registry.py:2315:def get_connection_config(server_id: str) -> Optional[Dict]:
/app/backend/core/server_registry.py:2321:    server = _get_server_by_id_from_sql(server_id)
/app/backend/core/server_registry.py:2338:def get_server_connection_info_with_secrets(server_id: str) -> Optional[Dict]:
/app/backend/core/server_registry.py:2361:    server = _get_server_by_id_from_sql(server_id)
/app/backend/core/server_registry.py:2363:        logger.debug(f"[SERVER_REGISTRY] Servidor {server_id} no encontrado para conexión")
/app/backend/core/server_registry.py:2418:    'get_server_connection_info_with_secrets',
/app/backend/core/connection_resolver.py:90:    server_id: Optional[str] = None
/app/backend/core/connection_resolver.py:118:            "server_id": self.server_id,
/app/backend/core/connection_resolver.py:245:            server_id="abc-123",
/app/backend/core/connection_resolver.py:251:                # Usar execute_sql_query con source.host, etc.
/app/backend/core/connection_resolver.py:287:    def _get_server_config(self, server_id: str) -> Optional[Dict[str, Any]]:
/app/backend/core/connection_resolver.py:292:                {"id": server_id, "active": True},
/app/backend/core/connection_resolver.py:297:            logger.error(f"[ConnectionResolver] Error obteniendo servidor {server_id}: {e}")
/app/backend/core/connection_resolver.py:320:        server_id: str,
/app/backend/core/connection_resolver.py:328:            server_id: UUID del servidor desde menú Servidores SQL
/app/backend/core/connection_resolver.py:335:        logger.info(f"[ConnectionResolver] Resolviendo: server={server_id}, metric={metric_type.value}")
/app/backend/core/connection_resolver.py:338:        server_config = self._get_server_config(server_id)
/app/backend/core/connection_resolver.py:349:                error_message=f"Servidor {server_id} no encontrado en menú Servidores SQL"
/app/backend/core/connection_resolver.py:364:                server_id=server_id,
/app/backend/core/connection_resolver.py:380:                server_id=server_id,
/app/backend/core/connection_resolver.py:403:                server_id=server_id,
/app/backend/core/connection_resolver.py:428:                    server_id=server_id,
/app/backend/core/connection_resolver.py:452:                        server_id=server_id,
/app/backend/core/connection_resolver.py:468:                        server_id=server_id,
/app/backend/core/connection_resolver.py:480:                server_id=server_id,
/app/backend/core/connection_resolver.py:522:    def health_check(self, server_id: str) -> Dict[str, Any]:
/app/backend/core/connection_resolver.py:529:        from core.db import execute_sql_query
/app/backend/core/connection_resolver.py:532:            "server_id": server_id,
/app/backend/core/connection_resolver.py:539:        sql_source = self.resolve_source(server_id, MetricType.ACCUMULATED_SALES)
/app/backend/core/connection_resolver.py:543:                test_result = execute_sql_query(
/app/backend/core/connection_resolver.py:576:    server_id: str,
/app/backend/core/connection_resolver.py:584:        server_id: UUID del servidor
/app/backend/core/connection_resolver.py:594:            result = execute_sql_query(source.host, source.port, ...)
/app/backend/core/connection_resolver.py:596:    return get_connection_resolver().resolve_source(server_id, metric_type, sucursal_nombre)
/app/backend/core/pool.py:42:- execute_sql_query() usa internamente este pool
/app/backend/core/pool.py:188:            server=server_string,
/app/backend/core/pool.py:192:            database=database,
/app/backend/core/pool.py:222:            server=host,
/app/backend/core/pool.py:226:            database=database,
/app/backend/core/providers.py:110:        from core.db import execute_sql_query
/app/backend/core/providers.py:134:            result = execute_sql_query(host, port, database, username, password, query)
/app/backend/core/providers.py:198:        from core.db import execute_sql_query
/app/backend/core/providers.py:215:            result = execute_sql_query(host, port, database, username, password, query_temp)
/app/backend/core/providers.py:254:            result = execute_sql_query(host, port, database, username, password, query_fallback)
/app/backend/core/providers.py:344:        from core.db import execute_sql_query
/app/backend/core/providers.py:371:            result = execute_sql_query(host, port, database, username, password, query)
/app/backend/core/providers.py:391:                        result_pax = execute_sql_query(host, port, database, username, password, query_pax)
/app/backend/core/__init__.py:6:# - db.py: Conexiones SQL Server, execute_sql_query()
/app/backend/core/source_resolver.py:97:        source_id: Identificador de la fuente (server_id, api_name)
/app/backend/core/policies/no_live_dashboard_policy.py:13:    "pyodbc.connect(",
/app/backend/core/auditoria.py:245:                server=host,
/app/backend/core/auditoria.py:247:                database=os.environ.get('EDARSA_HUB_SQL_DB', 'EDARSA_HUB'),
/app/backend/core/empresa_resolver.py:28:from core.db import execute_sql_query
/app/backend/core/empresa_resolver.py:52:        result = execute_sql_query(
/app/backend/core/refresh_tokens.py:195:    from core.db import execute_sql_query_params
/app/backend/core/refresh_tokens.py:201:            results = execute_sql_query_params(
/app/backend/core/refresh_tokens.py:204:                database=config['database'],
/app/backend/core/unidades_registry.py:18:- NO usar server_id como unidad_negocio_id
/app/backend/core/unidades_registry.py:42:    server_id: str                  # UUID del servidor
/app/backend/core/unidades_registry.py:52:        server='<REDACTED_EDARSAHUB_SQL_HOST>',
/app/backend/core/unidades_registry.py:54:        database='EDARSAHUB',
/app/backend/core/unidades_registry.py:68:            'by_server_sucursal': {(server_id, sucursal_id): UnidadNegocioConfig},
/app/backend/core/unidades_registry.py:90:                server_id,
/app/backend/core/unidades_registry.py:113:                server_id=str(row['server_id']),
/app/backend/core/unidades_registry.py:120:            key = (config.server_id, config.sucursal_id)
/app/backend/core/unidades_registry.py:136:def get_unidad_by_server_sucursal(server_id: str, sucursal_id: Optional[str] = None) -> Optional[UnidadNegocioConfig]:
/app/backend/core/unidades_registry.py:138:    Obtiene la configuración de unidad dado server_id y sucursal_id.
/app/backend/core/unidades_registry.py:141:        server_id: UUID del servidor
/app/backend/core/unidades_registry.py:152:    # Buscar por (server_id, sucursal_id)
/app/backend/core/unidades_registry.py:153:    key = (server_id, suc)
/app/backend/core/unidades_registry.py:161:        key_default = (server_id, 'DEFAULT')
/app/backend/core/unidades_registry.py:164:            logger.warning(f"[UNIDADES_REGISTRY] Fallback a DEFAULT para server={server_id}, sucursal={suc}")
/app/backend/core/unidades_registry.py:167:    logger.warning(f"[UNIDADES_REGISTRY] No encontrado: server={server_id}, sucursal={suc}")
/app/backend/core/security.py:493:            server='<REDACTED_EDARSAHUB_SQL_HOST>', port=1433,
/app/backend/core/security.py:495:            database='EDARSAHUB'
/app/backend/core/security.py:528:    Obtiene los server_ids asociados a una lista de empresas.
/app/backend/core/security.py:532:        Lista de server_ids (UUIDs lowercase)
/app/backend/core/security.py:540:        server='<REDACTED_EDARSAHUB_SQL_HOST>', port=1433,
/app/backend/core/security.py:542:        database='EDARSAHUB'
/app/backend/core/security.py:608:        return [i for i in items if i.get('id') in servers_permitidos or i.get('server_id') in servers_permitidos]
/app/backend/core/security.py:617:def user_has_server_access(user: Dict[str, Any], server_id: str) -> bool:
/app/backend/core/security.py:623:        server_id: ID del servidor a verificar
/app/backend/core/security.py:632:    return server_id in allowed if allowed else False
/app/backend/core/security.py:667:    server_id: str
/app/backend/core/security.py:675:        server_id: ID del servidor
/app/backend/core/security.py:685:    if server_id not in allowed_suc or not allowed_suc[server_id]:
/app/backend/core/security.py:688:    return [s for s in sucursales if s.get('id') in allowed_suc[server_id]]
/app/backend/core/scheduler/sql_repository.py:41:            server=EDARSAHUB_CONFIG['host'],
/app/backend/core/scheduler/sql_repository.py:43:            database=EDARSAHUB_CONFIG['database'],
/app/backend/core/scheduler/sql_repository.py:88:async def get_active_servers(server_id_filter: str = None) -> List[Dict]:
/app/backend/core/scheduler/sql_repository.py:93:        server_id_filter: ID de servidor específico (opcional)
/app/backend/core/scheduler/sql_repository.py:114:    if server_id_filter:
/app/backend/core/scheduler/sql_repository.py:116:        params = (server_id_filter,)
/app/backend/core/scheduler/sql_repository.py:156:async def get_server_by_id(server_id: str) -> Optional[Dict]:
/app/backend/core/scheduler/sql_repository.py:158:    servers = await get_active_servers(server_id)
/app/backend/core/scheduler/sql_repository.py:168:    server_id: str,
/app/backend/core/scheduler/sql_repository.py:183:    params = (sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
/app/backend/core/scheduler/sql_repository.py:191:    server_id: str,
/app/backend/core/scheduler/sql_repository.py:207:        sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario,
/app/backend/core/scheduler/sql_repository.py:221:    server_id: str,
/app/backend/core/scheduler/sql_repository.py:239:    params = (workflow_id, sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
/app/backend/core/scheduler/sql_repository.py:251:    server_id: str,
/app/backend/core/scheduler/sql_repository.py:270:    params = (error_mensaje, sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
/app/backend/core/scheduler/sql_repository.py:302:    server_id: str,
/app/backend/core/scheduler/sql_repository.py:315:    params = (sistema_origen, server_id, empresa_id, folio_pedido)
/app/backend/core/scheduler/sql_repository.py:323:    server_id: str,
/app/backend/core/scheduler/sql_repository.py:340:        sistema_origen, server_id, empresa_id, sucursal_id, folio_pedido,
/app/backend/core/scheduler/sql_repository.py:360:    server_id: str = None,
/app/backend/core/scheduler/sql_repository.py:374:        job_name, run_id, accion, server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:23:- server_id solo para uso interno (nunca expuesto)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:196:                        server_id = server["id"]  # Solo para uso interno
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:197:                        server_name = server.get("name", server_id)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:210:                            "server_id": server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:248:                                "server_id": server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:283:                            # ANTI-DUPLICADOS: Por empresa_id, no server_id
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:296:                                    server=server,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:485:        server_id = server["id"]
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:486:        server_name = server.get("name", server_id)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:494:            pedidos = await obtener_pedidos_vigentes(server_id)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:502:                    source_id=server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:510:                    source_id=server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:528:                    source_id=server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:537:                    source_id=server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:544:                    source_id=server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:551:                    source_id=server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:558:                    source_id=server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:582:        FASE 4.1: Anti-duplicado por empresa_id (no server_id).
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:595:        server_id: str = None,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:612:            server_id=server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:637:        server_id = server["id"]
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:656:                server_id=server_id
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:670:            server_id, almacen_id, productos
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:693:                server_id=server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:718:            server=server,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:727:            server_id=server_id
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:777:        server_id: str,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:894:            server_id=server["id"],  # Solo para uso interno
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:77:                server=EDARSAHUB_CONFIG["server"],
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:79:                database=EDARSAHUB_CONFIG["database"],
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:187:    def _get_sucursales_por_server(self, server_id: str) -> List[Dict]:
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:198:            """, (server_id, server_id))
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:229:            server_id = server["ServerID"]
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:230:            sucursales = self._get_sucursales_por_server(server_id)
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:244:                        WHERE server_id = %s 
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:248:                    """, (server_id, suc["SucursalID"], anio, mes))
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:253:                        meta_id = f"{server_id}-{suc['SucursalID']}-{anio}-{mes}"
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:289:                            server_id, suc["SucursalID"], anio, mes,
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:291:                            meta_id, server_id, suc["SucursalID"], suc.get("SucursalNombre", ""),
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:299:                            server_id, suc["SucursalID"], anio, mes
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:329:            server_id = server["ServerID"]
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:330:            sucursales = self._get_sucursales_por_server(server_id)
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:342:                        WHERE server_id = %s 
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:345:                    """, (server_id, suc["SucursalID"], fecha_inicio))
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:348:                        ticket_id = f"{server_id}-{suc['SucursalID']}-{row['FechaOperacion']}"
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:364:                            server_id, suc["SucursalID"], row["FechaOperacion"],
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:365:                            ticket_id, server_id, suc["SucursalID"], suc.get("SucursalNombre", ""),
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:396:            server_id = server["ServerID"]
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:397:            sucursales = self._get_sucursales_por_server(server_id)
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:411:                        WHERE server_id = %s AND sucursal_id = %s
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:414:                    """, (server_id, suc["SucursalID"], hoy))
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:417:                        mesa_id = f"{server_id}-{suc['SucursalID']}-{hoy}-resumen"
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:430:                            server_id, suc["SucursalID"], hoy, 'TOTAL',
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:431:                            mesa_id, server_id, suc["SucursalID"], row.get("sucursal_nombre", ""),
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:463:            server_id = server["ServerID"]
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:464:            sucursales = self._get_sucursales_por_server(server_id)
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:475:                        WHERE server_id = %s AND sucursal_id = %s
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:478:                    """, (server_id, suc["SucursalID"], fecha_inicio))
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:481:                        pax_id = f"{server_id}-{suc['SucursalID']}-{row['FechaOperacion']}"
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:496:                            server_id, suc["SucursalID"], row["FechaOperacion"],
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:497:                            pax_id, server_id, suc["SucursalID"], suc.get("SucursalNombre", ""),
/app/backend/core/scheduler/jobs/inteligencia_comercial_status_job.py:41:        server=host,
/app/backend/core/scheduler/jobs/inteligencia_comercial_status_job.py:43:        database=os.environ.get("EDARSA_HUB_SQL_DB") or os.environ.get("EDARSAHUB_SQL_DATABASE") or os.environ.get("EDARSAHUB_SQL_DB") or "EDARSA_HUB",
/app/backend/core/scheduler/jobs/vtiger_sync_job.py:24:        server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/core/scheduler/jobs/vtiger_sync_job.py:28:        database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB')
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:84:                "server_id": u.server_id,
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:94:                "server_id": u.server_id,
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:121:            "server_id": "a5547321-1139-4d2b-9d53-182ca737b6b6",
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:128:            "server_id": "6d053c22-523e-48c0-b72b-96081e2d781b",
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:135:            "server_id": "a5ff0e25-f029-43db-b634-d4ac814c904f",
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:145:            "server_id": "1b230a06-ffaf-4c70-bd27-b1be3579dea6",
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:152:            "server_id": "1b230a06-ffaf-4c70-bd27-b1be3579dea6",
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:178:        get_server_connection_config
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:237:                server_id=unidad["server_id"],
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:316:                server_id=unidad["server_id"],
/app/backend/core/scheduler/jobs/sync_short_comercial_job.py:85:        server_id = server.get("id")
/app/backend/core/scheduler/jobs/sync_short_comercial_job.py:91:        if not server_id:
/app/backend/core/scheduler/jobs/sync_short_comercial_job.py:95:            "server_id": server_id,
/app/backend/core/scheduler/jobs/sync_short_comercial_job.py:135:                    server_id=server_id,
/app/backend/core/scheduler/jobs/sync_short_comercial_job.py:206:                server=server,
/app/backend/core/scheduler/jobs/sync_short_comercial_job.py:225:                server=server,
/app/backend/core/scheduler/jobs/sync_compras_job.py:35:from core.db import execute_sql_query as _base_execute_sql_query
/app/backend/core/scheduler/jobs/sync_compras_job.py:73:            server=EDARSAHUB_CONFIG['host'],
/app/backend/core/scheduler/jobs/sync_compras_job.py:75:            database=EDARSAHUB_CONFIG['database'],
/app/backend/core/scheduler/jobs/sync_compras_job.py:133:            server=EDARSAHUB_CONFIG['host'],
/app/backend/core/scheduler/jobs/sync_compras_job.py:135:            database=EDARSAHUB_CONFIG['database'],
/app/backend/core/scheduler/jobs/sync_compras_job.py:184:        result = _base_execute_sql_query(host, port, database, username, password, query, timeout_seconds=timeout_seconds, context="jobs")
/app/backend/core/scheduler/jobs/sync_compras_job.py:218:            LEFT JOIN Unidades_Negocio u ON u.server_id = CAST(s.id AS NVARCHAR(36))
/app/backend/core/scheduler/jobs/sync_compras_job.py:368:                        server_id=server_info['id'],
/app/backend/core/scheduler/jobs/sync_compras_job.py:415:                        server_id=server_info['id'],
/app/backend/core/scheduler/jobs/sync_nightly_comercial_job.py:97:        server_id = server.get("id")
/app/backend/core/scheduler/jobs/sync_nightly_comercial_job.py:103:        if not server_id:
/app/backend/core/scheduler/jobs/sync_nightly_comercial_job.py:107:            "server_id": server_id,
/app/backend/core/scheduler/jobs/sync_nightly_comercial_job.py:128:                    server_id, empresa_id, str(sucursal_id), fecha
/app/backend/core/scheduler/jobs/sync_nightly_comercial_job.py:153:                    server_id=server_id,
/app/backend/core/scheduler/jobs/sync_nightly_comercial_job.py:261:                    server=server,
/app/backend/core/scheduler/jobs/sync_nightly_comercial_job.py:280:                    server=server,
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py:88:        server=EDARSAHUB_CONFIG["host"],
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py:92:        database=EDARSAHUB_CONFIG["database"],
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py:103:            server=config["host"],
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py:107:            database=config["database"],
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py:334:                    server_id, sucursal_id, sistema_origen,
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:67:            server=EDARSAHUB_CONFIG['host'],
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:69:            database=EDARSAHUB_CONFIG['database'],
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:119:            server=EDARSAHUB_CONFIG['host'],
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:121:            database=EDARSAHUB_CONFIG['database'],
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:160:            server=EDARSAHUB_CONFIG['host'],
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:162:            database=EDARSAHUB_CONFIG['database'],
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:175:            LEFT JOIN Unidades_Negocio u ON u.server_id = CAST(s.id AS NVARCHAR(36))
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:220:    from core.db import execute_sql_query
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:232:        result = execute_sql_query(host, port, database, username, password, query, timeout=timeout_seconds)
/app/backend/core/scheduler/jobs/crm_sync_job.py:25:        server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
/app/backend/core/scheduler/jobs/crm_sync_job.py:28:        database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:20:- server_id
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:124:    from core.db import execute_sql_query
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:132:        result = execute_sql_query(
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:178:    server_id: str
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:190:            "clave.server_id": self.server_id,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:257:    async def run(self, manual: bool = False, server_id_filter: str = None):
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:266:            server_id_filter: Filtrar por servidor específico (opcional)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:279:            detalles={"type": execution_type, "server_filter": server_id_filter}
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:287:                "server_filter": server_id_filter
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:296:            servidores = await self._obtener_servidores(server_id_filter)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:368:    async def _obtener_servidores(self, server_id_filter: str = None) -> List[Dict]:
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:372:        servidores = await get_active_servers(server_id_filter)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:409:                    'server_id': registro.get('ServerID'),
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:457:        from core.db import execute_sql_query
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:497:            result = execute_sql_query(
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:532:                    server_id=servidor['id'],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:582:        from core.db import execute_sql_query
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:599:            result = execute_sql_query(
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:656:            server_id=clave.server_id,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:698:                server_id=clave.server_id,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:727:        servidor = await get_server_by_id(registro["clave"]["server_id"])
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:763:                server_id=servidor['id'],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:804:                server_id=clave.server_id,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:833:                server_id=servidor['id'],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:868:            server_id=clave.get("server_id", ""),
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:122:            server=EDARSAHUB_LOCK_CONFIG['host'],
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:124:            database=EDARSAHUB_LOCK_CONFIG['database'],
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:180:            server=EDARSAHUB_LOCK_CONFIG['host'],
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:182:            database=EDARSAHUB_LOCK_CONFIG['database'],
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:218:    from core.db import execute_sql_query
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:227:        rows = execute_sql_query(
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:251:        # Convertir server_id a string si es UUID
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:252:        server_id = row['id']
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:253:        if hasattr(server_id, 'hex') or str(type(server_id)) == "<class 'uuid.UUID'>":
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:254:            server_id = str(server_id)
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:257:            "server_id": server_id,
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:323:    from core.db import execute_sql_query
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:338:        rows = execute_sql_query(
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:372:                "server_id": u.server_id,
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:382:                "server_id": u.server_id,  # Se reemplazará con el de API local
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:545:        get_server_connection_config,
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:618:            server_id = unidad["server_id"]
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:643:                server_config = get_server_connection_config(server_id)
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:645:                    raise Exception(f"No se encontró config para server_id {server_id}")
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:750:                    server_id=server_id,
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:791:                    server_id=server_id,
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:823:                    server_id=server_id,
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:849:                server_id = api_config['server_id']  # ID del servidor API_LOCAL
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:953:                        server_id=server_id,
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:1001:                            server_id=server_id,
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:1041:                    logger.info(f"  server_id: {server_id}")
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:1066:                    server_id=server_id,
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:1108:                    server_id=server_id,
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py:1141:                    server_id=unidad.get("server_id", "UNKNOWN"),
/app/backend/core/cache_key_builder.py:40:    server_id: Optional[str] = None
/app/backend/core/cache_key_builder.py:151:    server_id: str = None,
/app/backend/core/cache_key_builder.py:174:        server_id: ID del servidor (SQL id o mongodb_id)
/app/backend/core/cache_key_builder.py:198:            server_id="abc123",
/app/backend/core/cache_key_builder.py:211:    if server_id:
/app/backend/core/cache_key_builder.py:212:        parts.append(f"srv:{server_id[:12]}" if len(server_id) > 12 else f"srv:{server_id}")
/app/backend/core/cache_key_builder.py:289:            server_id="abc123",
/app/backend/core/cache_key_builder.py:297:        server_id=ctx.server_id,
/app/backend/core/cache_key_builder.py:325:        current_context: Contexto actual con server_id, system_type, etc.
/app/backend/core/cache_key_builder.py:341:    if 'server_id' in current_context:
/app/backend/core/cache_key_builder.py:342:        server_prefix = f"srv:{current_context['server_id'][:12]}"
/app/backend/core/cache_key_builder.py:344:            logger.warning("[CACHE][CONTEXT_MISMATCH] server_id no coincide")
/app/backend/core/system_type_utils.py:293:    server_id: str = None
/app/backend/core/system_type_utils.py:304:        f"server_id={server_id or 'N/A'} "
/app/backend/core/system_type_utils.py:336:    server_id: str,
/app/backend/core/system_type_utils.py:348:        server_id: ID del servidor
/app/backend/core/system_type_utils.py:365:    parts = [prefix, endpoint, server_id, normalized]
/app/backend/core/exceptions.py:12:    raise NotFoundError("Servidor", server_id)
/app/backend/core/context_resolver.py:8:- server_id
/app/backend/core/context_resolver.py:59:        server='<REDACTED_EDARSAHUB_SQL_HOST>',
/app/backend/core/context_resolver.py:63:        database='EDARSAHUB'
/app/backend/core/context_resolver.py:180:        Dict {sucursal_id_sql: {server_id, sucursal_origen_id, ...}}
/app/backend/core/context_resolver.py:208:            'server_id': row[2],  # UUID como string lowercase
/app/backend/core/context_resolver.py:216:def _get_servers_by_ids_sql(cursor, server_ids: List[str]) -> Dict[str, Dict]:
/app/backend/core/context_resolver.py:222:        server_ids: Lista de UUIDs de servidor (strings lowercase)
/app/backend/core/context_resolver.py:225:        Dict {server_id: {id, name, system_type, visible_en_operaciones}}
/app/backend/core/context_resolver.py:227:    if not server_ids:
/app/backend/core/context_resolver.py:230:    placeholders = ', '.join(['%s'] * len(server_ids))
/app/backend/core/context_resolver.py:241:    ''', tuple(server_ids))
/app/backend/core/context_resolver.py:245:        server_id = row[0]
/app/backend/core/context_resolver.py:246:        servers[server_id] = {
/app/backend/core/context_resolver.py:247:            'id': server_id,
/app/backend/core/context_resolver.py:256:def _get_server_by_id_sql(cursor, server_id: str) -> Optional[Dict]:
/app/backend/core/context_resolver.py:262:        server_id: UUID del servidor (string)
/app/backend/core/context_resolver.py:275:    ''', (server_id,))
/app/backend/core/context_resolver.py:289:def _get_sucursal_by_mapeo_server_sql(cursor, server_id: str) -> Optional[Dict]:
/app/backend/core/context_resolver.py:295:        server_id: UUID del servidor
/app/backend/core/context_resolver.py:315:    ''', (server_id,))
/app/backend/core/context_resolver.py:387:        - server_id: ID del servidor asociado
/app/backend/core/context_resolver.py:421:        server_ids = list(set(m['server_id'] for m in mapeos_dict.values() if m.get('server_id')))
/app/backend/core/context_resolver.py:422:        servers_dict = _get_servers_by_ids_sql(cursor, server_ids)
/app/backend/core/context_resolver.py:439:                server_id = mapeo.get('server_id')
/app/backend/core/context_resolver.py:440:                server_info = servers_dict.get(server_id, {})
/app/backend/core/context_resolver.py:447:                    'server_id': server_id,
/app/backend/core/context_resolver.py:479:            "server_id": str,
/app/backend/core/context_resolver.py:511:        'server_id': unidad['server_id'],
/app/backend/core/context_resolver.py:519:async def resolve_server_context(user: Dict[str, Any], server_id: str) -> Dict:
/app/backend/core/context_resolver.py:522:    COMPATIBILIDAD: Para endpoints que aún reciben server_id.
/app/backend/core/context_resolver.py:526:    El server_id se traduce internamente a unidad de negocio y se valida acceso.
/app/backend/core/context_resolver.py:530:        server_id: ID del servidor (UUID)
/app/backend/core/context_resolver.py:534:            "server_id": str,
/app/backend/core/context_resolver.py:554:        server = _get_server_by_id_sql(cursor, server_id)
/app/backend/core/context_resolver.py:565:        sucursal_info = _get_sucursal_by_mapeo_server_sql(cursor, server_id)
/app/backend/core/context_resolver.py:578:                logging.warning(f"[Context Resolver] Usuario {user.get('email')} sin acceso a servidor {server_id}")
/app/backend/core/context_resolver.py:595:            if server_id not in servers_permitidos:
/app/backend/core/context_resolver.py:599:            'server_id': server_id,
/app/backend/core/context_resolver.py:638:async def validate_user_access_to_server(user: Dict[str, Any], server_id: str) -> bool:
/app/backend/core/context_resolver.py:645:        server_id: ID del servidor
/app/backend/core/context_resolver.py:651:        await resolve_server_context(user, server_id)
/app/backend/core/user_access_context.py:70:        server='<REDACTED_EDARSAHUB_SQL_HOST>',
/app/backend/core/user_access_context.py:74:        database='EDARSAHUB'
/app/backend/core/user_access_context.py:288:        server_id = row[0]
/app/backend/core/user_access_context.py:290:        if server_id not in sucursales_por_server:
/app/backend/core/user_access_context.py:291:            sucursales_por_server[server_id] = []
/app/backend/core/user_access_context.py:292:        sucursales_por_server[server_id].append(sucursal_codigo)
/app/backend/core/user_access_context.py:311:        server_id = row[0]
/app/backend/core/user_access_context.py:313:        if server_id not in almacenes_por_server:
/app/backend/core/user_access_context.py:314:            almacenes_por_server[server_id] = []
/app/backend/core/user_access_context.py:315:        almacenes_por_server[server_id].append(almacen_codigo)
/app/backend/core/user_access_context.py:415:            for server_id, suc_list in sucursales.items():
/app/backend/core/user_access_context.py:417:                    context.sucursales_por_server[server_id] = suc_list
/app/backend/core/user_access_context.py:423:            for server_id, alm_list in almacenes.items():
/app/backend/core/user_access_context.py:425:                    context.almacenes_por_server[server_id] = alm_list
/app/backend/core/user_access_context.py:497:def has_server_access(context: UserAccessContext, server_id: str) -> bool:
/app/backend/core/user_access_context.py:503:        server_id: ID del servidor a verificar
/app/backend/core/user_access_context.py:510:    return server_id.lower() in [s.lower() for s in context.servers_ids]
/app/backend/core/user_access_context.py:522:def has_almacen_access(context: UserAccessContext, server_id: str, almacen_id: str) -> bool:
/app/backend/core/user_access_context.py:530:    if not has_server_access(context, server_id):
/app/backend/core/user_access_context.py:534:    almacenes_permitidos = context.almacenes_por_server.get(server_id.lower())
/app/backend/core/user_access_context.py:574:def get_almacenes_permitidos(context: UserAccessContext, server_id: str) -> List[str]:
/app/backend/core/user_access_context.py:582:        server_id: ID del servidor
/app/backend/core/user_access_context.py:590:    return context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:593:def get_almacenes_sql_filter(context: UserAccessContext, server_id: str, column_name: str) -> str:
/app/backend/core/user_access_context.py:599:        server_id: ID del servidor
/app/backend/core/user_access_context.py:608:    almacenes = context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:618:def get_almacenes_sql_filter_like(context: UserAccessContext, server_id: str, column_name: str) -> str:
/app/backend/core/user_access_context.py:625:        server_id: ID del servidor
/app/backend/core/user_access_context.py:634:    almacenes = context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:647:def validate_almacen_in_scope(context: UserAccessContext, server_id: str, almacen_id: str) -> bool:
/app/backend/core/user_access_context.py:653:        server_id: ID del servidor
/app/backend/core/user_access_context.py:662:    almacenes_permitidos = context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:671:    server_id: str, 
/app/backend/core/user_access_context.py:681:        server_id: ID del servidor
/app/backend/core/user_access_context.py:691:    almacenes_permitidos = context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/cerebro.py:219:    server_id: str
/app/backend/core/cerebro.py:251:    server_id: str = ""
/app/backend/core/cerebro.py:259:    server_id: str
/app/backend/core/cerebro.py:364:    server_id: str
/app/backend/core/cerebro.py:383:    server_id: str
/app/backend/core/cerebro.py:536:    server_id: str
/app/backend/core/cerebro.py:561:    server_id: str
/app/backend/core/cerebro.py:718:        {"keys": {"server_id": 1}, "options": {"name": "idx_server_status"}},
/app/backend/core/cerebro.py:721:        {"keys": {"server_id": 1, "periodo_key": 1}, "options": {"name": "idx_kpis_lookup"}},
/app/backend/core/cerebro.py:724:        {"keys": {"server_id": 1, "estado": 1}, "options": {"name": "idx_scripts_server_estado"}},
/app/backend/core/rbac_helper_sql.py:45:        server=_EDARSAHUB_CONFIG['host'],
/app/backend/core/rbac_helper_sql.py:47:        database=_EDARSAHUB_CONFIG['database'],
/app/backend/core/auth/user_repository_sql.py:44:            server=self.sql_host,
/app/backend/core/auth/user_repository_sql.py:48:            database=self.sql_db
/app/backend/core/resilient_sql.py:83:EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"
/app/backend/core/resilient_sql.py:143:        server = await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})
/app/backend/core/resilient_sql.py:169:            server=server['host'],
/app/backend/core/resilient_sql.py:173:            database=server['database'],
/app/backend/core/resilient_sql.py:213:            server=server['host'],
/app/backend/core/resilient_sql.py:217:            database=server['database'],
/app/backend/core/resilient_sql.py:279:                server=server['host'],
/app/backend/core/resilient_sql.py:283:                database=server['database'],
/app/backend/core/resilient_sql.py:356:                server=server['host'],
/app/backend/core/resilient_sql.py:360:                database=server['database'],
/app/backend/core/resilient_sql.py:476:    'EDARSA_HUB_SERVER_ID',
/app/backend/core/utils/operational_window.py:96:            server=EDARSAHUB_CONFIG['host'],
/app/backend/core/utils/operational_window.py:98:            database=EDARSAHUB_CONFIG['database'],
/app/backend/core/rbac/repository_sql.py:50:            server=self.sql_host,
/app/backend/core/rbac/repository_sql.py:54:            database=self.sql_db
/app/backend/core/security_v2_passive.py:93:def translate_server_to_sucursal(server_id: str, mapeos: List[Dict]) -> Optional[str]:
/app/backend/core/security_v2_passive.py:95:    Traduce un server_id al sucursal_id correspondiente.
/app/backend/core/security_v2_passive.py:101:        if mapeo.get('server_id') == server_id:
/app/backend/core/security_v2_passive.py:108:    Traduce un sucursal_id al server_id correspondiente.
/app/backend/core/security_v2_passive.py:114:            return mapeo.get('server_id')
/app/backend/core/alcance_helper.py:74:            server='<REDACTED_EDARSAHUB_SQL_HOST>', port=1433,
/app/backend/core/alcance_helper.py:76:            database='EDARSAHUB'
/app/backend/core/alcance_helper.py:119:            server='<REDACTED_EDARSAHUB_SQL_HOST>', port=1433,
/app/backend/core/alcance_helper.py:121:            database='EDARSAHUB'
/app/backend/core/system_capability_resolver.py:204:            from core.db import execute_sql_query
/app/backend/core/system_capability_resolver.py:206:            result = execute_sql_query(
/app/backend/core/system_capability_resolver.py:209:                database=self._config['database'],
/app/backend/core/inventory_analysis_core.py:44:    server_id: str
/app/backend/core/inventory_analysis_core.py:80:            'server_id': self.server_id,
/app/backend/core/inventory_analysis_core.py:153:        logging.info(f"[Core Service] Iniciando análisis para server_id={params.server_id}")
/app/backend/core/inventory_analysis_core.py:212:    server_id: str,
/app/backend/core/inventory_analysis_core.py:222:        server_id: ID del servidor
/app/backend/core/inventory_analysis_core.py:229:    params = {**report_params, 'server_id': server_id}
/app/backend/core/db.py:7:- Migrado: execute_sql_query() y funciones de soporte
/app/backend/core/db.py:23:    from core.db import execute_sql_query, test_sql_connection
/app/backend/core/db.py:342:        result = execute_sql_query(host, port, database, username, password, query)
/app/backend/core/db.py:522:            server=hostname,
/app/backend/core/db.py:524:            database=database,
/app/backend/core/db.py:540:            server=server_string, 
/app/backend/core/db.py:544:            database=database
/app/backend/core/db.py:554:def execute_sql_query(
/app/backend/core/db.py:673:        return _execute_sql_query_direct(
/app/backend/core/db.py:751:def execute_sql_query_params(
/app/backend/core/db.py:783:        execute_sql_query_params(
/app/backend/core/db.py:851:        return _execute_sql_query_params_direct(
/app/backend/core/db.py:856:def _execute_sql_query_params_direct(
/app/backend/core/db.py:875:            server=hostname,
/app/backend/core/db.py:877:            database=database,
/app/backend/core/db.py:917:            server=server_string, 
/app/backend/core/db.py:921:            database=database, 
/app/backend/core/db.py:952:def _execute_sql_query_direct(
/app/backend/core/db.py:1001:                server=hostname,
/app/backend/core/db.py:1003:                database=database,
/app/backend/core/db.py:1061:                server=server_string, 
/app/backend/core/db.py:1065:                database=database, 
/app/backend/core/db.py:1235:            server=hostname,
/app/backend/core/db.py:1237:            database=database,
/app/backend/core/db.py:1273:            server=server_string,
/app/backend/core/db.py:1277:            database=database,
/app/backend/core/db.py:1455:        results = execute_sql_query(
/app/backend/core/db.py:1536:    'execute_sql_query',
/app/backend/core/db.py:1537:    'execute_sql_query_params',
/app/backend/core/db.py:1540:    '_execute_sql_query_direct',  # Fallback interno con reintentos
/app/backend/tools/test_sql_connection_from_servidores.py:23:from core.db import execute_sql_query
/app/backend/tools/test_sql_connection_from_servidores.py:53:        ON CONVERT(NVARCHAR(100), u.server_id) = CONVERT(NVARCHAR(100), s.id)
/app/backend/tools/test_sql_connection_from_servidores.py:58:    result = execute_sql_query(
/app/backend/tools/test_sql_connection_from_servidores.py:85:    result = execute_sql_query(
/app/backend/tools/test_sql_connection_from_servidores.py:145:        test_result = execute_sql_query(
/app/backend/tools/test_sql_connection_from_servidores.py:263:        print(f"DATABASE={config.get('database_name')}")
/app/backend/tools/sync_sales_dry_run.py:9:- Usa get_server_connection_config() del módulo comercial_v2
/app/backend/tools/sync_sales_dry_run.py:37:from core.db import execute_sql_query
/app/backend/tools/sync_sales_dry_run.py:58:        result = execute_sql_query(
/app/backend/tools/sync_sales_dry_run.py:72:def get_server_connection_config(server_id: str) -> Optional[Dict[str, Any]]:
/app/backend/tools/sync_sales_dry_run.py:104:    WHERE id = '{server_id}'
/app/backend/tools/sync_sales_dry_run.py:152:        result = execute_sql_query(host, port, database, username, password, query)
/app/backend/tools/sync_sales_dry_run.py:161:        test_result = execute_sql_query(host, port, database, username, password, "SELECT 1 AS test")
/app/backend/tools/sync_sales_dry_run.py:193:    Patrón: Unidades_Negocio -> server_id -> Servidores_Conexiones
/app/backend/tools/sync_sales_dry_run.py:213:        server_id,
/app/backend/tools/sync_sales_dry_run.py:229:        server_id = unidad.get('server_id')
/app/backend/tools/sync_sales_dry_run.py:231:        if not server_id:
/app/backend/tools/sync_sales_dry_run.py:232:            logger.error(f"Unidad '{nombre_buscar}' no tiene server_id asignado")
/app/backend/tools/sync_sales_dry_run.py:236:        logger.info(f"Server ID: {server_id}")
/app/backend/tools/sync_sales_dry_run.py:240:        server_config = get_server_connection_config(str(server_id))
/app/backend/tools/sync_sales_dry_run.py:242:            logger.error(f"No se pudo obtener configuración del servidor {server_id}")
/app/backend/tools/sync_sales_dry_run.py:255:            "server_id": str(server_id),
/app/backend/tools/sync_sales_dry_run.py:890:            "server_id": config.get("server_id"),
/app/backend/tools/sync_sales_dry_run.py:964:            f"Server ID: {report['unidad']['server_id']}",
/app/backend/tools/edarsahub_sql_runner.py:62:        server=server,
/app/backend/tools/edarsahub_sql_runner.py:66:        database=database,
/app/backend/tools/check_mpro_server_config.py:53:                ON CONVERT(NVARCHAR(100), u.server_id) = CONVERT(NVARCHAR(100), s.id)
/app/backend/tools/validate_server_secret_key.py:22:from core.db import execute_sql_query
/app/backend/tools/validate_server_secret_key.py:46:    rows = execute_sql_query(
/app/backend/routes/portal_proveedores.py:174:def init_portal_db(database, jwt_secret, execute_sql_query_fn=None):
/app/backend/routes/portal_proveedores.py:179:    execute_sql_fn = execute_sql_query_fn
```

## ENDPOINTS OPERATIVOS SOSPECHOSOS

```text
/app/backend/modules/comercial/routes_pricing_ai.py:101:@router.post(
/app/backend/modules/comercial/routes_pricing_ai.py:165:@router.post(
/app/backend/modules/comercial/routes_pricing_ai.py:216:@router.post(
/app/backend/modules/comercial/routes_pricing_ai.py:273:@router.post(
/app/backend/modules/comercial/routes_pricing_ai.py:330:@router.get(
/app/backend/modules/comercial/routes_pricing_ai.py:364:@router.get(
/app/backend/modules/comercial/routes_pricing_ai.py:405:@router.get(
/app/backend/modules/comercial/routes_pricing_ai.py:451:@router.get(
/app/backend/modules/comercial/routes_precios_sugeridos.py:56:@router.get("/precios-sugeridos")
/app/backend/modules/comercial/routes_precios_sugeridos.py:107:@router.get("/reglas/vinos/rangos")
/app/backend/modules/comercial/routes_precios_sugeridos.py:117:@router.post("/reglas/vinos/rangos")
/app/backend/modules/comercial/routes_precios_sugeridos.py:142:@router.put("/reglas/vinos/rangos/{rango_id}")
/app/backend/modules/comercial/crm_router.py:27:@router.get("/cuentas")
/app/backend/modules/comercial/crm_router.py:33:@router.post("/cuentas")
/app/backend/modules/comercial/crm_router.py:54:@router.get("/clientes/solicitudes")
/app/backend/modules/comercial/crm_router.py:65:@router.post("/clientes/solicitudes")
/app/backend/modules/comercial/crm_router.py:102:@router.get("/actividades")
/app/backend/modules/comercial/crm_router.py:113:@router.post("/actividades")
/app/backend/modules/comercial/crm_router.py:130:@router.put("/actividades/{actividad_id}/estatus")
/app/backend/modules/comercial/crm_router.py:176:@router.get("/cotizaciones")
/app/backend/modules/comercial/crm_router.py:190:@router.post("/cotizaciones")
/app/backend/modules/comercial/crm_router.py:250:@router.get("/pedidos-venta")
/app/backend/modules/comercial/crm_router.py:258:@router.post("/pedidos-venta/convertir")
/app/backend/modules/comercial/crm_router.py:329:@router.get("/implementaciones")
/app/backend/modules/comercial/crm_router.py:339:@router.post("/implementaciones")
/app/backend/modules/comercial/crm_router.py:359:@router.get("/implementaciones/{implementacion_id}/entregables")
/app/backend/modules/comercial/crm_router.py:369:@router.put("/implementaciones/entregables/{entregable_id}/estatus")
/app/backend/modules/comercial/crm_router.py:395:@router.get("/kpis", response_model=KPISummaryResponse)
/app/backend/modules/comercial/crm_router.py:470:@router.get("/ia/forecast/{oportunidad_id}", response_model=IAForecastResponse)
/app/backend/modules/comercial/crm_router.py:521:@router.get("/ia/salud-comercial", response_model=IASeguimientoSalud)
/app/backend/modules/comercial/crm_router.py:572:@router.post("/integraciones/erp/transmitir")
/app/backend/modules/comercial/crm_router.py:596:@router.get("/integraciones/erp/backlog")
/app/backend/modules/comercial/inteligencia_comercial_routes.py:163:@router.get("/kpis")
/app/backend/modules/comercial/inteligencia_comercial_routes.py:206:@router.get("/ventas-comparativo")
/app/backend/modules/comercial/inteligencia_comercial_routes.py:259:@router.get("/pax")
/app/backend/modules/comercial/inteligencia_comercial_routes.py:307:@router.get("/unidades")
/app/backend/modules/comercial/inteligencia_comercial_routes.py:329:@router.get("/sync-status")
/app/backend/modules/comercial/inteligencia_comercial_routes.py:346:@router.get("/tendencia")
/app/backend/modules/comercial/inteligencia_comercial_routes.py:381:@router.get("/kpis-por-unidad")
/app/backend/modules/comercial/routes_pricing_ia.py:102:@router.get(
/app/backend/modules/comercial/routes_pricing_ia.py:132:@router.get(
/app/backend/modules/comercial/routes_pricing_ia.py:154:@router.post(
/app/backend/modules/comercial/routes_pricing_ia.py:176:@router.put(
/app/backend/modules/comercial/routes_pricing_ia.py:200:@router.get(
/app/backend/modules/comercial/routes_pricing_ia.py:234:@router.get(
/app/backend/modules/comercial/routes_pricing_ia.py:253:@router.post(
/app/backend/modules/comercial/routes_pricing_ia.py:273:@router.put(
/app/backend/modules/comercial/routes_pricing_ia.py:293:@router.delete(
/app/backend/modules/comercial/routes_pricing_ia.py:312:@router.get(
/app/backend/modules/comercial/routes_pricing_ia.py:342:@router.post(
/app/backend/modules/comercial/routes_pricing_ia.py:367:@router.put(
/app/backend/modules/comercial/routes_pricing_ia.py:387:@router.delete(
/app/backend/modules/comercial/routes_pricing_ia.py:406:@router.get(
/app/backend/modules/comercial/routes_pricing_ia.py:442:@router.get(
/app/backend/modules/comercial/routes_pricing_ia.py:461:@router.post(
/app/backend/modules/comercial/routes_pricing_ia.py:481:@router.put(
/app/backend/modules/comercial/routes_pricing_ia.py:501:@router.post(
/app/backend/modules/comercial/routes_pricing_ia.py:521:@router.delete(
/app/backend/modules/comercial/routes_pricing_ia.py:540:@router.get(
/app/backend/modules/comercial/routes_pricing_ia.py:567:@router.get(
/app/backend/modules/comercial/routes_pricing_ia.py:597:@router.post(
/app/backend/modules/comercial/routes_pricing_ia.py:639:@router.get(
/app/backend/modules/comercial/routes_competidores_enterprise.py:77:@router.post("/competidores-catalogo", summary="Crear competidor en catálogo maestro")
/app/backend/modules/comercial/routes_competidores_enterprise.py:112:@router.get("/competidores-catalogo", summary="Buscar en catálogo maestro")
/app/backend/modules/comercial/routes_competidores_enterprise.py:139:@router.post("/competidores-unidad/relacionar", summary="Relacionar competidor con unidad")
/app/backend/modules/comercial/routes_competidores_enterprise.py:178:@router.post("/competidores-unidad/desrelacionar", summary="Desrelacionar competidor de unidad")
/app/backend/modules/comercial/routes_competidores_enterprise.py:203:@router.get("/competidores-unidad/{competidor_catalogo_id}/unidades", summary="Unidades donde está el competidor")
/app/backend/modules/comercial/routes_competidores_enterprise.py:220:@router.get("/competidores", summary="Listar competidores por unidad (OBLIGATORIO)")
/app/backend/modules/comercial/routes_competidores_enterprise.py:260:@router.get("/competidores/{competidor_catalogo_id}", summary="Obtener competidor en contexto de unidad")
/app/backend/modules/comercial/routes_competidores_enterprise.py:287:@router.get("/competidores-estadisticas", summary="Estadísticas de competidores por unidad")
/app/backend/modules/comercial/routes_listas_competidores.py:71:@router.get(
/app/backend/modules/comercial/routes_listas_competidores.py:105:@router.post(
/app/backend/modules/comercial/routes_listas_competidores.py:138:@router.get(
/app/backend/modules/comercial/routes_listas_competidores.py:165:@router.put(
/app/backend/modules/comercial/routes_listas_competidores.py:198:@router.delete(
/app/backend/modules/comercial/routes_listas_competidores.py:228:@router.get(
/app/backend/modules/comercial/routes_listas_competidores.py:257:@router.post(
/app/backend/modules/comercial/routes_listas_competidores.py:290:@router.delete(
/app/backend/modules/comercial/routes_listas_competidores.py:322:@router.get(
/app/backend/modules/comercial/routes_alertas_margen.py:91:@router.get("/reglas")
/app/backend/modules/comercial/routes_alertas_margen.py:123:@router.post("/reglas")
/app/backend/modules/comercial/routes_alertas_margen.py:161:@router.get("/reglas/{regla_id}")
/app/backend/modules/comercial/routes_alertas_margen.py:176:@router.put("/reglas/{regla_id}")
/app/backend/modules/comercial/routes_alertas_margen.py:207:@router.delete("/reglas/{regla_id}")
/app/backend/modules/comercial/routes_alertas_margen.py:230:@router.get("/resolver-regla")
/app/backend/modules/comercial/routes_alertas_margen.py:270:@router.post("/evaluar")
/app/backend/modules/comercial/routes_alertas_margen.py:306:@router.get("/umbrales")
/app/backend/modules/comercial/routes_alertas_margen.py:324:@router.get("/estadisticas")
/app/backend/modules/comercial/routes.py:535:@router.get("/comercial/tablero-ejecutivo")
/app/backend/modules/comercial/routes.py:1913:@router.get("/comercial/sucursales/{server_id}")
/app/backend/modules/comercial/routes.py:2014:@router.get("/comercial/metas/{server_id}")
/app/backend/modules/comercial/routes.py:2349:@router.get("/comercial/ticket-perfecto/{server_id}")
/app/backend/modules/comercial/routes.py:2645:@router.get("/comercial/ventas-tiempo/{server_id}")
/app/backend/modules/comercial/routes.py:2869:@router.get("/comercial/mesas/{server_id}")
/app/backend/modules/comercial/routes.py:3241:@router.get("/comercial/detalle-movimientos/{server_id}")
/app/backend/modules/comercial/routes.py:3500:@router.get("/comercial/precios-constantes/{server_id}")
/app/backend/modules/comercial/routes.py:4097:@router.get("/comercial/reporte-pax/{server_id}")
/app/backend/modules/comercial/routes.py:4223:@router.get("/comercial/dashboard/{server_id}")
/app/backend/modules/comercial/routes.py:4714:@router.get("/comercial/ventas-tiempo/{unit_id}")
/app/backend/modules/fase2_operativo/routes/sla_routes.py:31:@router.get("/configuracion")
/app/backend/modules/fase2_operativo/routes/sla_routes.py:60:@router.put("/configuracion")
/app/backend/modules/fase2_operativo/routes/sla_routes.py:95:@router.get("/metricas")
/app/backend/modules/fase2_operativo/routes/sla_routes.py:124:@router.get("/tareas/proximas-vencer")
/app/backend/modules/fase2_operativo/routes/sla_routes.py:158:@router.get("/tareas/vencidas")
/app/backend/modules/fase2_operativo/routes/sla_routes.py:192:@router.post("/actualizar-estados")
/app/backend/modules/fase2_operativo/routes/sla_routes.py:227:@router.get("/tarea/{tarea_id}")
/app/backend/modules/fase2_operativo/routes/sla_routes.py:273:@router.get("/estados")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:83:@router.post("/compras/detector/ejecutar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:126:@router.get("/compras/detector/estado")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:167:@router.get("/compras/tareas")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:199:@router.get("/compras/tareas/{tarea_id}")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:219:@router.post("/compras/tareas/{tarea_id}/completar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:259:@router.post("/compras/tareas/{tarea_id}/asignar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:295:@router.get("/compras/kpis")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:307:@router.get("/compras")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:326:@router.get("/compras/detector/bitacora")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:350:@router.get("/compras/pedidos-procesados")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:386:@router.get("/compras/{automatizacion_id}")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:403:@router.post("/compras/procesar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:437:@router.post("/compras/{automatizacion_id}/gerencia")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:476:@router.post("/compras/{automatizacion_id}/tesoreria")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:513:@router.post("/compras/{automatizacion_id}/dias-objetivo")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:548:@router.post("/compras/{automatizacion_id}/parametros-consumo")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:596:@router.get("/compras/{automatizacion_id}/bitacora")
/app/backend/modules/fase2_operativo/routes/tarea_routes.py:38:@router.post("", response_model=OperacionResponse, status_code=201)
/app/backend/modules/fase2_operativo/routes/tarea_routes.py:70:@router.get("/{tarea_id}")
/app/backend/modules/fase2_operativo/routes/tarea_routes.py:94:@router.get("")
/app/backend/modules/fase2_operativo/routes/tarea_routes.py:257:@router.get("/{tarea_id}/historial")
/app/backend/modules/fase2_operativo/routes/tarea_routes.py:276:@router.post("/marcar-vencidas", response_model=OperacionResponse)
/app/backend/modules/fase2_operativo/routes/configuracion_routes.py:29:@router.get("")
/app/backend/modules/fase2_operativo/routes/configuracion_routes.py:51:@router.get("/todas")
/app/backend/modules/fase2_operativo/routes/configuracion_routes.py:68:@router.get("/{clave}")
/app/backend/modules/fase2_operativo/routes/configuracion_routes.py:125:@router.get("/umbral-justificacion/valor")
/app/backend/modules/fase2_operativo/routes/configuracion_routes.py:167:@router.get("/dias-limite-tarea/valor")
/app/backend/modules/fase2_operativo/routes/configuracion_routes.py:209:@router.get("/max-ciclos-reasignacion/valor")
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:67:@router.post(
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:102:@router.get(
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:133:@router.get(
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:147:@router.get(
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:161:@router.get(
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:175:@router.get(
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:198:@router.get(
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:216:@router.get(
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:236:@router.post(
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:272:@router.post(
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:307:@router.post(
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:341:@router.post(
/app/backend/modules/fase2_operativo/routes/cargos_routes.py:377:@router.post(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:62:@router.post(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:114:@router.get(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:145:@router.get(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:183:@router.get(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:214:@router.put(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:244:@router.post(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:272:@router.get(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:320:@router.post(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:354:@router.post(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:392:@router.post(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:428:@router.post(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:466:@router.post(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:504:@router.post(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:540:@router.get(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:560:@router.get(
/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py:580:@router.get(
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:23:@router.get("/status")
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:42:@router.get("/log")
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:78:@router.post("/verificar-vencidas")
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:184:@router.post("/test-email")
/app/backend/modules/fase2_operativo/routes/justificacion_routes.py:32:@router.post("", response_model=OperacionResponse, status_code=201)
/app/backend/modules/fase2_operativo/routes/justificacion_routes.py:73:@router.get("/{justificacion_id}")
/app/backend/modules/fase2_operativo/routes/justificacion_routes.py:96:@router.get("")
/app/backend/modules/fase2_operativo/routes/justificacion_routes.py:135:@router.get("/workflow/{workflow_id}")
/app/backend/modules/fase2_operativo/routes/justificacion_routes.py:153:@router.post("/workflow/{workflow_id}/verificar")
/app/backend/modules/fase2_operativo/routes/justificacion_routes.py:177:@router.get("/umbral")
/app/backend/modules/fase2_operativo/routes/justificacion_routes.py:197:@router.post("/determinar-tipo")
/app/backend/modules/fase2_operativo/routes/workflow_routes.py:49:@router.post("", response_model=OperacionResponse, status_code=201)
/app/backend/modules/fase2_operativo/routes/workflow_routes.py:84:@router.get("/{workflow_id}")
/app/backend/modules/fase2_operativo/routes/workflow_routes.py:114:@router.get("")
/app/backend/modules/fase2_operativo/routes/workflow_routes.py:179:@router.post("/{workflow_id}/escalar", response_model=OperacionResponse)
/app/backend/modules/fase2_operativo/routes/workflow_routes.py:212:@router.get("/{workflow_id}/resumen")
/app/backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:43:@router.get(
/app/backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:73:@router.get(
/app/backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:87:@router.get(
/app/backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:103:@router.get(
/app/backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:129:@router.get(
/app/backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:147:@router.post(
/app/backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:176:@router.put(
/app/backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:205:@router.delete(
/app/backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:234:@router.post(
/app/backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:260:@router.post(
/app/backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:286:@router.post(
/app/backend/modules/fase2_operativo/routes/documentos_routes.py:31:@router.get("/workflow/{workflow_id}/excel")
/app/backend/modules/fase2_operativo/routes/documentos_routes.py:103:@router.get("/workflow/{workflow_id}/pdf")
/app/backend/modules/fase2_operativo/routes/documentos_routes.py:177:@router.get("/workflow/{workflow_id}/datos")
/app/backend/modules/fase2_operativo/routes/documentos_routes.py:218:@router.get("/workflow/{workflow_id}/resumen")
/app/backend/modules/fase2_operativo/routes/documentos_routes.py:254:@router.get("/historial")
/app/backend/modules/fase2_operativo/routes/auditoria_routes.py:31:@router.post("/decisiones", response_model=OperacionResponse, status_code=201)
/app/backend/modules/fase2_operativo/routes/auditoria_routes.py:69:@router.post("/decisiones/procesar", response_model=OperacionResponse)
/app/backend/modules/fase2_operativo/routes/auditoria_routes.py:110:@router.get("/decisiones/{decision_id}")
/app/backend/modules/fase2_operativo/routes/auditoria_routes.py:133:@router.get("/workflow/{workflow_id}/decisiones")
/app/backend/modules/fase2_operativo/routes/auditoria_routes.py:151:@router.get("/workflow/{workflow_id}/ultima-decision")
/app/backend/modules/fase2_operativo/routes/auditoria_routes.py:172:@router.get("/pendientes")
/app/backend/modules/fase2_operativo/routes/auditoria_routes.py:190:@router.get("/resumen")
/app/backend/modules/fase2_operativo/routes/auditoria_routes.py:212:@router.get("")
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:43:@router.get("/resumen")
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:70:@router.get("/alertas")
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:99:@router.get("/workflows/por-estado")
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:125:@router.get("/tareas/por-estado")
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:151:@router.get("/tareas/vencidas/conteo")
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:176:@router.get("/kpis")
/app/backend/modules/api_connections/routes.py:108:@router.get("")
/app/backend/modules/api_connections/routes.py:131:@router.get("/{api_id}")
/app/backend/modules/api_connections/routes.py:155:@router.post("")
/app/backend/modules/api_connections/routes.py:187:@router.put("/{api_id}")
/app/backend/modules/api_connections/routes.py:225:@router.delete("/{api_id}")
/app/backend/modules/api_connections/routes.py:253:@router.post("/test")
/app/backend/modules/api_connections/routes.py:264:@router.post("/{api_id}/test")
/app/backend/modules/api_connections/routes.py:278:@router.post("/sync-cache")
/app/backend/modules/api_connections/routes.py:299:@router.get("/check-duplicate")
/app/backend/modules/api_connections/routes.py:321:@router.post("/{api_id}/test-query")
/app/backend/modules/api_connections/routes.py:366:@router.post("/test-query-draft")
/app/backend/modules/api_connections/universal_test_routes.py:477:@router.post("/api-connections/{connection_id}/universal-query-test")
/app/backend/modules/api_connections/universal_test_routes.py:677:@router.post("/api-connections/{connection_id}/test-connection")
/app/backend/modules/api_connections/universal_test_routes.py:896:@router.post("/api-connections/{connection_id}/test-connectivity")
/app/backend/modules/corporate_filters/router.py:253:@router.get("/health")
/app/backend/modules/corporate_filters/router.py:277:@router.get("/bootstrap")
/app/backend/modules/corporate_filters/router.py:401:@router.post("/resolve")
/app/backend/modules/sistema/menu_routes.py:19:@router.get("/modulos", summary="Listar Módulos")
/app/backend/modules/sistema/menu_routes.py:40:@router.get("/arbol", summary="Árbol Completo de Menús")
/app/backend/modules/sistema/menu_routes.py:58:@router.get("/usuario", summary="Menús del Usuario Actual")
/app/backend/modules/sistema/menu_routes.py:112:@router.get("/modulo/{modulo_id}", summary="Menús de un Módulo")
/app/backend/modules/costos_margenes/routes_precios.py:151:@router.post("/simulacion", response_model=SimulacionPrecioResponse)
/app/backend/modules/costos_margenes/routes_precios.py:239:@router.post("/solicitudes-precio", response_model=SolicitudCambioPrecioResponse)
/app/backend/modules/costos_margenes/routes_precios.py:287:@router.get("/solicitudes-precio", response_model=SolicitudesListResponse)
/app/backend/modules/costos_margenes/routes_precios.py:331:@router.get("/solicitudes-precio/{solicitud_id}", response_model=SolicitudCambioPrecioResponse)
/app/backend/modules/costos_margenes/routes_precios.py:363:@router.post("/solicitudes-precio/{solicitud_id}/enviar", response_model=AccionSolicitudResponse)
/app/backend/modules/costos_margenes/routes_precios.py:409:@router.post("/solicitudes-precio/{solicitud_id}/aprobar", response_model=AccionSolicitudResponse)
/app/backend/modules/costos_margenes/routes_precios.py:480:@router.post("/solicitudes-precio/{solicitud_id}/rechazar", response_model=AccionSolicitudResponse)
/app/backend/modules/costos_margenes/routes_precios.py:549:@router.post("/solicitudes-precio/{solicitud_id}/aplicar", response_model=AccionSolicitudResponse)
/app/backend/modules/costos_margenes/routes_precios.py:617:@router.post("/solicitudes-precio/{solicitud_id}/cancelar", response_model=AccionSolicitudResponse)
/app/backend/modules/costos_margenes/routes_precios.py:678:@router.get("/solicitudes-precio/{solicitud_id}/historial", response_model=HistorialSolicitudResponse)
/app/backend/modules/costos_margenes/routes.py:175:@router.get("/resumen", response_model=CostosMargenesResumen)
/app/backend/modules/costos_margenes/routes.py:221:@router.get("/productos", response_model=ProductosListResponse)
/app/backend/modules/costos_margenes/routes.py:348:@router.get("/productos/{producto_id}/receta", response_model=RecetaExpandida)
/app/backend/modules/costos_margenes/routes.py:441:@router.get("/productos/{producto_id}/insumos", response_model=InsumosProductoResponse)
/app/backend/modules/costos_margenes/routes.py:505:@router.get("/sync-status", response_model=SyncStatusResponse)
/app/backend/modules/costos_margenes/routes.py:559:@router.get("/unidades-negocio")
/app/backend/modules/costos_margenes/routes.py:598:@router.get("/familias")
/app/backend/modules/costos_margenes/routes.py:635:@router.get("/subfamilias")
/app/backend/modules/costos_margenes/routes.py:667:@router.get("/exportar")
/app/backend/modules/rh/importador/routes.py:93:@router.post("/tablas/crear", summary="Crear tablas de staging y bitácora")
/app/backend/modules/rh/importador/routes.py:117:@router.get("/tablas/script", summary="Obtener script DDL de tablas")
/app/backend/modules/rh/importador/routes.py:140:@router.post("/excel/preview", response_model=PreviewImportacion, summary="Preview de importación Excel")
/app/backend/modules/rh/importador/routes.py:182:@router.post("/excel/staging", summary="Cargar Excel a staging")
/app/backend/modules/rh/importador/routes.py:228:@router.get("/staging", summary="Listar registros en staging")
/app/backend/modules/rh/importador/routes.py:262:@router.put("/staging/{staging_id}", summary="Actualizar registro en staging")
/app/backend/modules/rh/importador/routes.py:292:@router.post("/staging/aprobar", response_model=ConfirmarCargaResponse, summary="Aprobar y cargar al maestro")
/app/backend/modules/rh/importador/routes.py:467:@router.get("/bitacora", summary="Ver historial de importaciones")
/app/backend/modules/rh/importador/routes.py:492:@router.get("/staging/estadisticas", summary="Estadísticas del staging")
/app/backend/modules/rh/importador/routes.py:513:@router.get("/staging/pendientes", summary="Listar candidatos a aprobación")
/app/backend/modules/rh/importador/routes.py:540:@router.get("/staging/incompletos", summary="Listar registros incompletos")
/app/backend/modules/rh/importador/routes.py:565:@router.get("/staging/excluidos", summary="Listar registros excluidos (auditoría)")
/app/backend/modules/rh/importador/routes.py:590:@router.get("/staging/{staging_id}", summary="Obtener detalle de un registro")
/app/backend/modules/rh/importador/routes.py:615:@router.post("/staging/aprobar/{staging_id}", summary="Aprobar un registro")
/app/backend/modules/rh/importador/routes.py:646:@router.post("/staging/rechazar/{staging_id}", summary="Rechazar un registro")
/app/backend/modules/rh/importador/routes.py:673:@router.post("/staging/observar/{staging_id}", summary="Marcar registro para revisión")
/app/backend/modules/rh/importador/routes.py:700:@router.post("/staging/aprobar-lote", summary="Aprobar múltiples registros")
/app/backend/modules/rh/importador/routes.py:740:@router.post("/homologacion/ejecutar", summary="Ejecutar homologación completa")
/app/backend/modules/rh/importador/routes.py:768:@router.get("/homologacion/estadisticas", summary="Estadísticas de homologación")
/app/backend/modules/rh/importador/routes.py:791:@router.get("/homologacion/equivalencias", summary="Listar equivalencias")
/app/backend/modules/rh/importador/routes.py:815:@router.get("/homologacion/verificar", summary="Verificar si homologación está completa")
/app/backend/modules/rh/importador/routes.py:842:@router.post("/homologacion/actualizar-staging", summary="Actualizar staging con IDs")
/app/backend/modules/rh/solicitudes_catalogo.py:89:@router.get("/catalogos-disponibles")
/app/backend/modules/rh/solicitudes_catalogo.py:100:@router.post("")
/app/backend/modules/rh/solicitudes_catalogo.py:149:@router.get("")
/app/backend/modules/rh/solicitudes_catalogo.py:200:@router.get("/pendientes-notificacion")
/app/backend/modules/rh/solicitudes_catalogo.py:232:@router.put("/{solicitud_id}")
/app/backend/modules/rh/solicitudes_catalogo.py:324:@router.get("/{solicitud_id}")
/app/backend/modules/rh/routes.py:158:@router.get("/catalogos/puestos")
/app/backend/modules/rh/routes.py:170:@router.post("/catalogos/puestos", response_model=SuccessResponse)
/app/backend/modules/rh/routes.py:183:@router.put("/catalogos/puestos/{puesto_id}", response_model=SuccessResponse)
/app/backend/modules/rh/routes.py:197:@router.delete("/catalogos/puestos/{puesto_id}", response_model=SuccessResponse)
/app/backend/modules/rh/routes.py:215:@router.get("/catalogos/sucursales")
/app/backend/modules/rh/routes.py:232:@router.get("/catalogos/tipos-incidencias")
/app/backend/modules/rh/routes.py:245:@router.post("/catalogos/tipos-incidencias", response_model=SuccessResponse)
/app/backend/modules/rh/routes.py:258:@router.put("/catalogos/tipos-incidencias/{tipo_id}", response_model=SuccessResponse)
/app/backend/modules/rh/routes.py:272:@router.delete("/catalogos/tipos-incidencias/{tipo_id}", response_model=SuccessResponse)
/app/backend/modules/rh/routes.py:289:@router.get("/catalogos/script-inicializacion")
/app/backend/modules/rh/routes.py:306:@router.get("/colaboradores")
/app/backend/modules/rh/routes.py:350:@router.get("/colaboradores/{colaborador_id}")
/app/backend/modules/rh/routes.py:369:@router.post("/colaboradores", response_model=SuccessWithIdResponse)
/app/backend/modules/rh/routes.py:393:@router.put("/colaboradores/{colaborador_id}", response_model=SuccessResponse)
/app/backend/modules/rh/routes.py:410:@router.delete("/colaboradores/{colaborador_id}", response_model=SuccessResponse)
/app/backend/modules/rh/routes.py:431:@router.get("/incidencias")
/app/backend/modules/rh/routes.py:473:@router.post("/incidencias")
/app/backend/modules/rh/routes.py:495:@router.post("/incidencias/importar-excel", response_model=ImportacionExcelResponse)
/app/backend/modules/rh/routes.py:521:@router.get("/incidencias/plantilla-excel")
/app/backend/modules/rh/routes.py:568:@router.get("/asistencia")
/app/backend/modules/rh/routes.py:606:@router.post("/asistencia")
/app/backend/modules/rh/routes.py:630:@router.put("/asistencia/{check_id}/validar")
/app/backend/modules/rh/routes.py:674:@router.get("/nominas/flujo")
/app/backend/modules/rh/routes.py:702:@router.post("/nominas/flujo")
/app/backend/modules/rh/routes.py:723:@router.put("/nominas/flujo/{flujo_id}/enviar-rh")
/app/backend/modules/rh/routes.py:740:@router.put("/nominas/flujo/{flujo_id}/validar-gerente")
/app/backend/modules/rh/routes.py:762:@router.put("/nominas/flujo/{flujo_id}/autorizar-dg")
/app/backend/modules/rh/routes.py:777:@router.put("/nominas/flujo/{flujo_id}/enviar-tesoreria")
/app/backend/modules/rh/routes.py:792:@router.put("/nominas/flujo/{flujo_id}/marcar-pagado")
/app/backend/modules/rh/routes.py:824:@router.get("/auditoria-fiscal")
/app/backend/modules/rh/routes.py:853:@router.get("/dashboard")
/app/backend/modules/rh/routes.py:912:@router.get("/vacantes")
/app/backend/modules/rh/routes.py:933:@router.post("/vacantes")
/app/backend/modules/rh/routes.py:959:@router.put("/vacantes/{vacante_id}")
/app/backend/modules/rh/routes.py:978:@router.delete("/vacantes/{vacante_id}")
/app/backend/modules/rh/routes.py:995:@router.get("/candidatos")
/app/backend/modules/rh/routes.py:1016:@router.post("/candidatos")
/app/backend/modules/rh/routes.py:1039:@router.put("/candidatos/{candidato_id}")
/app/backend/modules/rh/routes.py:1056:@router.delete("/candidatos/{candidato_id}")
/app/backend/modules/rh/routes.py:1071:@router.get("/reclutamiento/dashboard")
/app/backend/modules/rh/routes.py:1088:@router.get("/reclutamiento/script-inicializacion")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:172:@router.get("")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:224:@router.get("/unidades-negocio")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:247:@router.get("/almacenes/{unidad_negocio_id}")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:268:@router.get("/almacenes/{unidad_negocio_id}/sync-info")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:306:@router.get("/{config_id}")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:324:@router.post("", status_code=201)
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:403:@router.put("/{config_id}")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:522:@router.delete("/{config_id}")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:569:@router.get("/resolver/test")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:636:@router.post("/almacenes/sincronizar/{unidad_negocio_id}")
/app/backend/modules/consultas_sql/routes.py:145:@router.get("/catalogo", response_model=ConsultaCatalogoListResponse)
/app/backend/modules/consultas_sql/routes.py:222:@router.get("/catalogo/{codigo_consulta}", response_model=ConsultaDetalleResponse)
/app/backend/modules/consultas_sql/routes.py:312:@router.get("/catalogo/{codigo_consulta}/versiones", response_model=VersionesResponse)
/app/backend/modules/consultas_sql/routes.py:396:@router.get("/catalogo/{codigo_consulta}/servidores", response_model=ServidoresAsociadosResponse)
/app/backend/modules/consultas_sql/routes.py:486:@router.post("/validar-texto", response_model=ValidarTextoResponse)
/app/backend/modules/consultas_sql/routes.py:635:@router.post("/ejecutar", response_model=EjecucionResponse)
/app/backend/modules/consultas_sql/routes.py:880:@router.get("/sistemas", response_model=SistemasResponse)
/app/backend/modules/consultas_sql/routes.py:921:@router.get("/modulos", response_model=ModulosResponse)
/app/backend/modules/inteligencia_comercial/routes.py:112:@router.get("/dashboard")
/app/backend/modules/inteligencia_comercial/routes.py:263:@router.get("/dashboard/tendencia")
/app/backend/modules/inteligencia_comercial/routes.py:330:@router.get("/dashboard/horarios")
/app/backend/modules/inteligencia_comercial/routes.py:434:@router.get("/dashboard/pax")
/app/backend/modules/inteligencia_comercial/routes.py:565:@router.get("/productos")
/app/backend/modules/inteligencia_comercial/routes.py:631:@router.get("/familias")
/app/backend/modules/inteligencia_comercial/routes.py:693:@router.get("/casas")
/app/backend/modules/inteligencia_comercial/routes.py:754:@router.get("/unidades")
/app/backend/modules/inteligencia_comercial/routes.py:796:@router.get("/health")
/app/backend/modules/catalogos/routes.py:61:@router.get("/sistemas")
/app/backend/modules/catalogos/routes.py:98:@router.get("/sistemas/activos")
/app/backend/modules/catalogos/routes.py:140:@router.post("/sistemas/solicitar")
/app/backend/modules/catalogos/routes.py:203:@router.post("/sistemas")
/app/backend/modules/catalogos/routes.py:274:@router.put("/sistemas/{sistema_id}")
/app/backend/modules/catalogos/routes.py:502:@router.get("/dominios")
/app/backend/modules/catalogos/routes.py:515:@router.get("/tabla/{tabla}")
/app/backend/modules/catalogos/routes.py:536:@router.get("/tabla/{tabla}/{id}")
/app/backend/modules/catalogos/routes.py:554:@router.get("/estructura/{tabla}")
/app/backend/modules/catalogos/routes.py:572:@router.post("/tabla/{tabla}")
/app/backend/modules/catalogos/routes.py:599:@router.put("/tabla/{tabla}/{id}")
/app/backend/modules/catalogos/routes.py:629:@router.put("/tabla/{tabla}/{id}/desactivar")
/app/backend/modules/catalogos/routes.py:650:@router.put("/tabla/{tabla}/{id}/activar")
/app/backend/modules/catalogos/routes.py:673:@router.post("/admin/crear-tablas")
/app/backend/modules/catalogos/routes.py:701:@router.get("/admin/verificar-tablas")
/app/backend/modules/catalogos/routes.py:713:@router.get("/admin/script-ddl")
/app/backend/modules/auth/routes.py:84:@router.post("/auth/register")
/app/backend/modules/auth/routes.py:90:@router.post("/auth/login")
/app/backend/modules/auth/routes.py:167:@router.post("/auth/logout")
/app/backend/modules/auth/routes.py:211:@router.post("/auth/refresh")
/app/backend/modules/auth/routes.py:307:@router.post("/auth/logout-all")
/app/backend/modules/auth/routes.py:360:@router.get("/auth/me")
/app/backend/modules/auth/routes.py:389:@router.get("/auth/me/context")
/app/backend/modules/auth/routes.py:403:@router.post("/auth/context")
/app/backend/modules/auth/routes.py:435:@router.get("/auth/empresas")
/app/backend/modules/auth/routes.py:450:@router.get("/auth/me/access-context")
/app/backend/modules/auth/routes.py:472:@router.get("/auth/me/menu-permissions")
/app/backend/modules/auth/routes.py:593:@router.post("/users")
/app/backend/modules/auth/routes.py:618:@router.get("/users", response_model=List[User])
/app/backend/modules/auth/routes.py:624:@router.put("/users/{user_id}")
/app/backend/modules/auth/routes.py:630:@router.delete("/users/{user_id}")
/app/backend/modules/auth/routes.py:636:@router.put("/users/{user_id}/permissions")
/app/backend/modules/auth/routes.py:646:@router.get("/roles/modulos")
/app/backend/modules/auth/routes.py:656:@router.get("/roles")
/app/backend/modules/auth/routes.py:662:@router.post("/roles")
/app/backend/modules/auth/routes.py:668:@router.put("/roles/{role_id}")
/app/backend/modules/auth/routes.py:674:@router.delete("/roles/{role_id}")
/app/backend/modules/auth/routes.py:703:@router.post("/auth/forgot-password")
/app/backend/modules/auth/routes.py:746:@router.post("/auth/reset-password")
/app/backend/modules/comercial_v2/routes.py:547:@router.get("/health", response_model=HealthResponse)
/app/backend/modules/comercial_v2/routes.py:570:@router.get("/dashboard", response_model=DashboardResponse)
/app/backend/modules/comercial_v2/routes.py:992:@router.get("/kpis-diarios", response_model=KPIsDiariosResponse)
/app/backend/modules/comercial_v2/routes.py:1041:@router.get("/kpis-diarios/{unidad_negocio_id}")
/app/backend/modules/comercial_v2/routes.py:1118:@router.get("/kpis-mensuales", response_model=KPIsMensualesResponse)
/app/backend/modules/comercial_v2/routes.py:1164:@router.get("/ventas-dia", response_model=VentasDiaResponse)
/app/backend/modules/comercial_v2/routes.py:1357:@router.get("/unidades", response_model=UnidadesResponse)
/app/backend/modules/comercial_v2/routes.py:1388:@router.get("/sync-status", response_model=SyncStatusResponse)
/app/backend/modules/tablajeria/routes.py:66:@router.get("/plantillas")
/app/backend/modules/tablajeria/routes.py:146:@router.get("/plantillas/{plantilla_id}")
/app/backend/modules/tablajeria/routes.py:197:@router.put("/plantillas/{plantilla_id}/publicar")
/app/backend/modules/tablajeria/routes.py:229:@router.get("/sync/servidores")
/app/backend/modules/tablajeria/routes.py:257:@router.post("/sync/ejecutar")
/app/backend/modules/tablajeria/routes.py:286:@router.get("/sync/log")
/app/backend/modules/tablajeria/routes.py:331:@router.get("/stats")
/app/backend/modules/tablajeria/routes.py:397:@router.get("/ordenes")
/app/backend/modules/tablajeria/routes.py:441:@router.get("/ordenes/{orden_id}")
/app/backend/modules/tablajeria/routes.py:467:@router.post("/ordenes")
/app/backend/modules/tablajeria/routes.py:501:@router.post("/ordenes/captura-directa")
/app/backend/modules/tablajeria/routes.py:539:@router.put("/ordenes/{orden_id}/iniciar")
/app/backend/modules/tablajeria/routes.py:578:@router.put("/ordenes/{orden_id}/resultados")
/app/backend/modules/tablajeria/routes.py:634:@router.put("/ordenes/{orden_id}/cerrar")
/app/backend/modules/tablajeria/routes.py:724:@router.put("/ordenes/{orden_id}/cancelar")
/app/backend/modules/tablajeria/routes.py:766:@router.put("/ordenes/{orden_id}/autorizar")
/app/backend/modules/tablajeria/routes.py:808:@router.get("/ordenes-stats")
/app/backend/modules/tablajeria/routes.py:897:@router.post("/ordenes/{orden_id}/fase6/procesar-cierre")
/app/backend/modules/tablajeria/routes.py:942:@router.post("/ordenes/{orden_id}/fase6/afectar-inventario")
/app/backend/modules/tablajeria/routes.py:959:@router.post("/ordenes/{orden_id}/fase6/calcular-costeo")
/app/backend/modules/tablajeria/routes.py:996:@router.post("/ordenes/{orden_id}/fase6/generar-poliza")
/app/backend/modules/tablajeria/routes.py:1013:@router.get("/fase6/config-contable/{empresa_id}")
/app/backend/modules/tablajeria/routes.py:1044:@router.put("/fase6/config-contable/{empresa_id}")
/app/backend/modules/tablajeria/routes.py:1088:@router.get("/dashboard/kpis")
/app/backend/modules/tablajeria/routes.py:1111:@router.get("/dashboard/rendimientos-plantilla")
/app/backend/modules/tablajeria/routes.py:1132:@router.get("/dashboard/tendencia")
/app/backend/modules/tablajeria/routes.py:1153:@router.get("/dashboard/top-mermas")
/app/backend/modules/tablajeria/routes.py:1174:@router.get("/dashboard/alertas")
/app/backend/modules/tablajeria/routes.py:1195:@router.get("/dashboard/resumen-costeo")
/app/backend/modules/tablajeria/routes.py:1221:@router.get("/reportes/ordenes")
/app/backend/modules/tablajeria/routes.py:1314:@router.get("/reportes/mermas")
/app/backend/modules/tablajeria/routes.py:1392:@router.get("/reportes/costeo")
/app/backend/modules/universal_query/routes.py:232:@router.post("/servers/{server_id}/universal-query-test")
/app/backend/modules/crm/comercial_routes.py:139:@router.get("/cuentas")
/app/backend/modules/crm/comercial_routes.py:246:@router.post("/cuentas")
/app/backend/modules/crm/comercial_routes.py:270:@router.get("/cuentas/{cuenta_id}")
/app/backend/modules/crm/comercial_routes.py:291:@router.post("/cuentas/{cuenta_id}/ligar-cliente")
/app/backend/modules/crm/comercial_routes.py:320:@router.get("/clientes")
/app/backend/modules/crm/comercial_routes.py:346:@router.get("/clientes/solicitudes")
/app/backend/modules/crm/comercial_routes.py:368:@router.post("/clientes/solicitudes")
/app/backend/modules/crm/comercial_routes.py:392:@router.post("/clientes/solicitudes/{solicitud_id}/enviar")
/app/backend/modules/crm/comercial_routes.py:416:@router.post("/clientes/solicitudes/{solicitud_id}/autorizar")
/app/backend/modules/crm/comercial_routes.py:445:@router.post("/clientes/solicitudes/{solicitud_id}/rechazar")
/app/backend/modules/crm/comercial_routes.py:474:@router.get("/actividades")
/app/backend/modules/crm/comercial_routes.py:502:@router.post("/actividades")
/app/backend/modules/crm/comercial_routes.py:526:@router.post("/actividades/{actividad_id}/cerrar")
/app/backend/modules/crm/comercial_routes.py:558:@router.get("/catalogos/tipos-actividad")
/app/backend/modules/crm/comercial_routes.py:571:@router.get("/catalogos/estatus-actividad")
/app/backend/modules/crm/comercial_routes.py:584:@router.get("/catalogos/estatus-remision")
/app/backend/modules/crm/comercial_routes.py:625:@router.get("/cotizaciones")
/app/backend/modules/crm/comercial_routes.py:653:@router.get("/cotizaciones/{cotizacion_id}")
/app/backend/modules/crm/comercial_routes.py:672:@router.post("/cotizaciones")
/app/backend/modules/crm/comercial_routes.py:696:@router.post("/cotizaciones/{cotizacion_id}/enviar")
/app/backend/modules/crm/comercial_routes.py:716:@router.post("/cotizaciones/{cotizacion_id}/aprobar")
/app/backend/modules/crm/comercial_routes.py:762:@router.get("/pedidos-venta")
/app/backend/modules/crm/comercial_routes.py:790:@router.get("/pedidos-venta/{pedido_id}")
/app/backend/modules/crm/comercial_routes.py:809:@router.post("/pedidos-venta")
/app/backend/modules/crm/comercial_routes.py:833:@router.post("/pedidos-venta/{pedido_id}/confirmar")
/app/backend/modules/crm/comercial_routes.py:885:@router.get("/remisiones-venta")
/app/backend/modules/crm/comercial_routes.py:915:@router.get("/remisiones-venta/{remision_id}")
/app/backend/modules/crm/comercial_routes.py:934:@router.post("/remisiones-venta")
/app/backend/modules/crm/comercial_routes.py:958:@router.post("/remisiones-venta/{remision_id}/entregar")
/app/backend/modules/crm/vtiger_routes.py:87:@router.get("/connections")
/app/backend/modules/crm/vtiger_routes.py:112:@router.post("/connections")
/app/backend/modules/crm/vtiger_routes.py:150:@router.put("/connections/{connection_id}")
/app/backend/modules/crm/vtiger_routes.py:177:@router.delete("/connections/{connection_id}")
/app/backend/modules/crm/vtiger_routes.py:194:@router.post("/connections/{connection_id}/test")
/app/backend/modules/crm/vtiger_routes.py:233:@router.post("/test")
/app/backend/modules/crm/vtiger_routes.py:263:@router.get("/connections/{connection_id}/leads")
/app/backend/modules/crm/vtiger_routes.py:289:@router.get("/connections/{connection_id}/contacts")
/app/backend/modules/crm/vtiger_routes.py:315:@router.get("/connections/{connection_id}/accounts")
/app/backend/modules/crm/vtiger_routes.py:341:@router.get("/connections/{connection_id}/opportunities")
/app/backend/modules/crm/vtiger_routes.py:367:@router.get("/modules")
/app/backend/modules/crm/vtiger_routes.py:388:@router.post("/sync/execute")
/app/backend/modules/crm/vtiger_routes.py:405:@router.get("/sync/status")
/app/backend/modules/crm/vtiger_routes.py:418:@router.get("/sync/config")
/app/backend/modules/crm/automation_routes.py:43:@router.get("/reglas", summary="Listar Reglas de Automatización")
/app/backend/modules/crm/automation_routes.py:66:@router.post("/reglas", summary="Crear Regla de Automatización")
/app/backend/modules/crm/automation_routes.py:99:@router.get("/sla/verificar", summary="Verificar SLA de Oportunidades")
/app/backend/modules/crm/automation_routes.py:124:@router.get("/estadisticas", summary="Estadísticas de Automatizaciones")
/app/backend/modules/crm/automation_routes.py:146:@router.post("/ejecutar/cambio-etapa", summary="Ejecutar Trigger de Cambio de Etapa (Manual)")
/app/backend/modules/crm/native_routes.py:33:@router.post("/leads", response_model=LeadResponse, summary="Crear Lead")
/app/backend/modules/crm/native_routes.py:44:@router.get("/leads", summary="Listar Leads")
/app/backend/modules/crm/native_routes.py:160:@router.get("/leads/{lead_id}", response_model=LeadResponse, summary="Obtener Lead")
/app/backend/modules/crm/native_routes.py:172:@router.put("/leads/{lead_id}", response_model=LeadResponse, summary="Actualizar Lead")
/app/backend/modules/crm/native_routes.py:193:@router.delete("/leads/{lead_id}", summary="Eliminar Lead")
/app/backend/modules/crm/native_routes.py:211:@router.post("/leads/{lead_id}/descalificar", response_model=LeadResponse, summary="Descalificar Lead")
/app/backend/modules/crm/native_routes.py:232:@router.post("/leads/{lead_id}/convertir", summary="Convertir Lead")
/app/backend/modules/crm/native_routes.py:262:@router.post("/oportunidades", response_model=OportunidadResponse, summary="Crear Oportunidad")
/app/backend/modules/crm/native_routes.py:273:@router.get("/oportunidades", summary="Listar Oportunidades")
/app/backend/modules/crm/native_routes.py:391:@router.get("/contactos", summary="Listar Contactos")
/app/backend/modules/crm/native_routes.py:497:@router.get("/oportunidades/{oportunidad_id}", response_model=OportunidadResponse, summary="Obtener Oportunidad")
/app/backend/modules/crm/native_routes.py:509:@router.post("/oportunidades/{oportunidad_id}/cambiar-etapa", response_model=OportunidadResponse, summary="Cambiar Etapa")
/app/backend/modules/crm/native_routes.py:532:@router.post("/oportunidades/{oportunidad_id}/cerrar", response_model=OportunidadResponse, summary="Cerrar Oportunidad")
/app/backend/modules/crm/native_routes.py:558:@router.get("/pipelines", summary="Listar Pipelines")
/app/backend/modules/crm/native_routes.py:572:@router.get("/pipelines/{pipeline_id}/kanban", summary="Vista Kanban")
/app/backend/modules/crm/native_routes.py:595:@router.get("/catalogos", summary="Obtener todos los catálogos")
/app/backend/modules/crm/native_routes.py:606:@router.get("/catalogos/{nombre}", summary="Obtener catálogo específico")
/app/backend/modules/crm/native_routes.py:626:@router.get("/dashboard", summary="Dashboard CRM")
/app/backend/modules/crm/trigger_routes.py:59:@router.get("/", summary="Listar Triggers")
/app/backend/modules/crm/trigger_routes.py:79:@router.post("/", summary="Crear Trigger")
/app/backend/modules/crm/trigger_routes.py:175:@router.post("/dispatch", summary="Despachar Evento Manual")
/app/backend/modules/crm/trigger_routes.py:216:@router.get("/eventos", summary="Listar Tipos de Evento")
/app/backend/modules/crm/trigger_routes.py:230:@router.get("/acciones", summary="Listar Tipos de Acción")
/app/backend/modules/crm/integration_routes.py:101:@router.get("/conectores")
/app/backend/modules/crm/integration_routes.py:153:@router.get("/conectores/{conector_id}")
/app/backend/modules/crm/integration_routes.py:188:@router.post("/conectores")
/app/backend/modules/crm/integration_routes.py:247:@router.put("/conectores/{conector_id}")
/app/backend/modules/crm/integration_routes.py:302:@router.delete("/conectores/{conector_id}")
/app/backend/modules/crm/integration_routes.py:333:@router.post("/test-connection")
/app/backend/modules/crm/integration_routes.py:350:@router.post("/conectores/{conector_id}/test")
/app/backend/modules/crm/integration_routes.py:401:@router.post("/conectores/{conector_id}/sync")
/app/backend/modules/crm/integration_routes.py:504:@router.get("/conectores/{conector_id}/staging/stats")
/app/backend/modules/crm/integration_routes.py:516:@router.get("/conectores/{conector_id}/staging/leads")
/app/backend/modules/crm/integration_routes.py:565:@router.get("/conectores/{conector_id}/staging/oportunidades")
/app/backend/modules/crm/integration_routes.py:612:@router.get("/conectores/{conector_id}/staging/cuentas")
/app/backend/modules/crm/integration_routes.py:663:@router.get("/conectores/{conector_id}/sync-log")
/app/backend/modules/crm/integration_routes.py:702:@router.post("/conectores/{conector_id}/process-staging")
/app/backend/modules/crm/integration_routes.py:767:@router.get("/conectores/{conector_id}/conflictos")
/app/backend/modules/crm/integration_routes.py:815:@router.post("/conectores/{conector_id}/conflictos/{staging_id}/resolver")
/app/backend/modules/crm/integration_routes.py:879:@router.post("/conectores/{conector_id}/conflictos/resolver-todos")
/app/backend/modules/crm/routes.py:20:@router.get("/status")
/app/backend/modules/crm/routes.py:25:@router.get("/test-connection")
/app/backend/modules/crm/routes.py:30:@router.get("/stats")
/app/backend/modules/crm/routes.py:35:@router.get("/modules")
/app/backend/modules/finanzas/tesoreria.py:94:@router.get("/cortes-z")
/app/backend/modules/finanzas/tesoreria.py:247:@router.get("/cortes-z/{sucursal}/{folio}")
/app/backend/modules/finanzas/tesoreria.py:285:@router.get("/cuadres")
/app/backend/modules/finanzas/tesoreria.py:346:@router.get("/cuadres/resumen")
/app/backend/modules/finanzas/tesoreria.py:401:@router.get("/cuadres/{cuadre_id}")
/app/backend/modules/finanzas/tesoreria.py:437:@router.post("/cuadres")
/app/backend/modules/finanzas/tesoreria.py:523:@router.put("/cuadres/{cuadre_id}")
/app/backend/modules/finanzas/tesoreria.py:577:@router.delete("/cuadres/{cuadre_id}")
/app/backend/modules/finanzas/tesoreria.py:613:@router.post("/cuadres/{cuadre_id}/ficha-deposito")
/app/backend/modules/finanzas/tesoreria.py:663:@router.post("/cuadres/{cuadre_id}/validar-ficha")
/app/backend/modules/finanzas/tesoreria.py:870:@router.get("/sucursales")
/app/backend/modules/finanzas/health.py:182:@router.get("")
/app/backend/modules/finanzas/health.py:327:@router.get("/quick")
/app/backend/modules/finanzas/health.py:382:@router.get("/tables")
/app/backend/modules/finanzas/health.py:425:@router.get("/servers/{server_id}")
/app/backend/modules/finanzas/cuentas_por_pagar.py:224:@router.get("")
/app/backend/modules/finanzas/cuentas_por_pagar.py:809:@router.get("/resumen")
/app/backend/modules/finanzas/cuentas_por_pagar.py:991:@router.get("/proveedores")
/app/backend/modules/finanzas/cuentas_por_pagar.py:1052:@router.get("/sucursales")
/app/backend/modules/finanzas/cuentas_por_pagar.py:1161:@router.put("/{factura_id}/decision-pago")
/app/backend/modules/finanzas/cuentas_por_pagar.py:1264:@router.put("/decision-pago-masivo")
/app/backend/modules/finanzas/cuentas_por_pagar.py:1306:@router.get("/{factura_id}")
/app/backend/modules/finanzas/ingresos.py:320:@router.get("/cortes-caja")
/app/backend/modules/finanzas/ingresos.py:474:@router.get("/saldos-por-depositar")
/app/backend/modules/finanzas/ingresos.py:547:@router.get("/resumen-comisiones")
/app/backend/modules/finanzas/ingresos.py:617:@router.put("/cortes-caja/{corte_id}/deposito-efectivo")
/app/backend/modules/finanzas/ingresos.py:639:@router.put("/cortes-caja/{corte_id}/deposito-tarjetas")
/app/backend/modules/finanzas/ingresos.py:660:@router.post("/cargar-estado-cuenta")
/app/backend/modules/finanzas/ingresos.py:702:@router.get("/movimientos-banco")
/app/backend/modules/finanzas/ingresos.py:720:@router.get("/config-comisiones")
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:115:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:162:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:215:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:269:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:302:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:335:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:368:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:399:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes.py:161:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes.py:194:@router.post(
/app/backend/modules/finanzas/propinas_tpv/routes.py:229:@router.post(
/app/backend/modules/finanzas/propinas_tpv/routes.py:267:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes.py:308:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes.py:394:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes.py:471:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes.py:496:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes.py:533:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes.py:551:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes.py:574:@router.post(
/app/backend/modules/finanzas/propinas_tpv/routes.py:596:@router.put(
/app/backend/modules/finanzas/propinas_tpv/routes.py:628:@router.get(
/app/backend/modules/finanzas/propinas_tpv/routes.py:651:@router.put(
/app/backend/modules/finanzas/saldos_bancarios.py:95:@router.get("/cuentas-bancarias/{cuenta_id}/saldos")
/app/backend/modules/finanzas/saldos_bancarios.py:141:@router.get("/cuentas-bancarias/{cuenta_id}/saldo-actual")
/app/backend/modules/finanzas/saldos_bancarios.py:198:@router.post("/saldos-bancarios", status_code=201)
/app/backend/modules/finanzas/saldos_bancarios.py:269:@router.post("/saldos-bancarios/{saldo_id}/corregir")
/app/backend/modules/finanzas/saldos_bancarios.py:351:@router.post("/saldos-bancarios/{saldo_id}/cancelar")
/app/backend/modules/finanzas/saldos_bancarios.py:416:@router.get("/saldos-bancarios/{saldo_id}/historial")
/app/backend/modules/finanzas/saldos_bancarios.py:482:@router.get("/saldos-bancarios/total")
/app/backend/modules/finanzas/cuentas_bancarias.py:103:@router.get("/bancos")
/app/backend/modules/finanzas/cuentas_bancarias.py:133:@router.get("/cuentas-bancarias")
/app/backend/modules/finanzas/cuentas_bancarias.py:196:@router.get("/cuentas-bancarias/{cuenta_id}")
/app/backend/modules/finanzas/cuentas_bancarias.py:237:@router.post("/cuentas-bancarias", status_code=201)
/app/backend/modules/finanzas/cuentas_bancarias.py:314:@router.put("/cuentas-bancarias/{cuenta_id}")
/app/backend/modules/finanzas/cuentas_bancarias.py:377:@router.post("/cuentas-bancarias/{cuenta_id}/desactivar")
/app/backend/modules/cava_socios/routes.py:67:@router.get("/dashboard")
/app/backend/modules/cava_socios/routes.py:85:@router.get("/socios")
/app/backend/modules/cava_socios/routes.py:106:@router.get("/socios/{socio_id}")
/app/backend/modules/cava_socios/routes.py:129:@router.post("/socios")
/app/backend/modules/cava_socios/routes.py:153:@router.post("/socios/{socio_id}/botellas")
/app/backend/modules/cava_socios/routes.py:176:@router.post("/botellas/{botella_id}/consumo")
/app/backend/modules/cava_socios/routes.py:203:@router.get("/reportes/socio/{socio_id}/ficha", summary="Descargar Ficha de Socio PDF")
/app/backend/modules/cava_socios/routes.py:247:@router.get("/reportes/socio/{socio_id}/consumos", summary="Descargar Historial de Consumos PDF")
/app/backend/modules/cava_socios/routes.py:292:@router.get("/reportes/socio/{socio_id}/estado-cuenta", summary="Descargar Estado de Cuenta PDF")
/app/backend/modules/cava_socios/routes.py:350:@router.post("/socios/{socio_id}/enviar-reporte", summary="Enviar Reporte por Email/WhatsApp")
/app/backend/modules/cava_socios/routes.py:423:@router.post("/socios/{socio_id}/enviar-todos-reportes", summary="Enviar Todos los Reportes")
/app/backend/modules/manuales_operativos/routes.py:42:@router.get("", response_model=ManualOperativoListResponse)
/app/backend/modules/manuales_operativos/routes.py:66:@router.get("/{manual_id}", response_model=ManualOperativoResponse)
/app/backend/modules/manuales_operativos/routes.py:81:@router.get("/proceso/{proceso_id}", response_model=ManualOperativoResponse)
/app/backend/modules/manuales_operativos/routes.py:96:@router.get("/{manual_id}/exportar")
/app/backend/modules/manuales_operativos/routes.py:124:@router.post("/generar/{proceso_id}")
/app/backend/modules/compras/routes.py:42:# @router.get("/compras/parametros/{server_id}")
/app/backend/modules/compras/routes.py:45:# @router.post("/compras/parametros")
/app/backend/server.py:155:@app.get("/api/health")
/app/backend/server.py:168:@app.get("/api/comercial/tablero-ejecutivo-fallback")
/app/backend/server.py:198:@app.get("/api/v2/comercial/dashboard-fallback")
/app/backend/server.py:18263:@app.get("/api/download/schema")
/app/backend/server.py:18276:@app.get("/api/download/schema-sql")
/app/backend/server.py:18289:@app.get("/api/download/backup-full")
/app/backend/server.py:18302:@app.get("/api/download/manual-desarrollo")
/app/backend/api/admin_cache.py:142:@router.post("/clear-preview")
/app/backend/api/admin_cache.py:219:@router.get("/status")
/app/backend/api/catalogos_sistemas.py:134:@router.get("")
/app/backend/api/catalogos_sistemas.py:161:@router.get("/explorables")
/app/backend/api/catalogos_sistemas.py:190:@router.get("/explorables-dinamico")
/app/backend/api/catalogos_sistemas.py:265:@router.get("/sync-ventas")
/app/backend/api/catalogos_sistemas.py:295:@router.get("/meta/capacidades-disponibles")
/app/backend/api/catalogos_sistemas.py:315:@router.get("/meta/modulos-disponibles")
/app/backend/api/catalogos_sistemas.py:339:@router.get("/normalizar/{system_type}")
/app/backend/api/catalogos_sistemas.py:375:@router.get("/diagnostico/{system_type}")
/app/backend/api/catalogos_sistemas.py:408:@router.get("/capacidades/{capacidad}")
/app/backend/api/catalogos_sistemas.py:449:@router.get("/{codigo_sistema}/capacidades")
/app/backend/api/catalogos_sistemas.py:494:@router.get("/{codigo_sistema}")
/app/backend/api/configuracion_operativa_unidades.py:279:@router.get("/todas/configuracion-operativa")
/app/backend/api/configuracion_operativa_unidades.py:330:@router.get("/{unidad_id}/configuracion-operativa")
/app/backend/api/configuracion_operativa_unidades.py:355:@router.put("/{unidad_id}/configuracion-operativa")
/app/backend/api/configuracion_operativa_unidades.py:449:@router.post("/{unidad_id}/probar-fecha-operacion")
/app/backend/api/admin_data_quality.py:99:@router.get("/audit/merida-duplicates", response_model=DuplicateAuditResponse)
/app/backend/api/admin_data_quality.py:231:@router.get("/audit/generic-duplicates")
/app/backend/api/admin_data_quality.py:288:@router.get("/verify/merida-consolidation")
/app/backend/api/admin_scheduler_resync.py:364:@router.post("/resync/validate")
/app/backend/api/admin_scheduler_resync.py:436:@router.post("/resync/execute", response_model=ResyncResponse)
/app/backend/api/admin_scheduler_resync.py:632:@router.get("/resync/history")
/app/backend/api/admin_scheduler_resync.py:705:@router.get("/resync/options")
/app/backend/api/sync_receiver.py:181:@router.post("/sync/kpis", response_model=SyncResponse)
/app/backend/api/sync_receiver.py:224:@router.post("/sync/heartbeat")
/app/backend/api/sync_receiver.py:255:@router.get("/sync/test-auth")
/app/backend/api/sync_receiver.py:267:@router.post("/admin/agents/generate-token", response_model=GenerateTokenResponse)
/app/backend/api/admin_core_connections.py:353:@router.get("")
/app/backend/api/admin_core_connections.py:388:@router.get("/{server_id}")
/app/backend/api/admin_core_connections.py:424:@router.post("/{server_id}/test")
/app/backend/api/dba_credential_p0d.py:191:@router.get("/status")
/app/backend/api/dba_credential_p0d.py:216:@router.post("/register", response_model=DBACredentialResponse)
/app/backend/api/dba_credential_p0d.py:305:@router.delete("/clear")
/app/backend/api/dba_credential_p0d.py:336:@router.get("/test-connection")
/app/backend/api/dba_credential_p0d.py:450:@router.post("/execute-diagnostic")
/app/backend/core/security.py:465:        @router.get("/protected")
/app/backend/core/scheduler/routes.py:69:@router.get("/status")
/app/backend/core/scheduler/routes.py:94:@router.get("/jobs/{job_id}")
/app/backend/core/scheduler/routes.py:115:@router.post("/jobs/{job_id}/run")
/app/backend/core/scheduler/routes.py:136:@router.post("/jobs/{job_id}/pause")
/app/backend/core/scheduler/routes.py:153:@router.post("/jobs/{job_id}/resume")
/app/backend/core/scheduler/routes.py:174:@router.get("/logs")
/app/backend/core/scheduler/routes.py:215:@router.get("/logs/stats")
/app/backend/core/scheduler/routes.py:239:@router.get("/locks")
/app/backend/core/scheduler/routes.py:256:@router.delete("/locks/{job_name}")
/app/backend/core/scheduler/routes.py:282:@router.get("/config")
/app/backend/core/communications/routes.py:139:@router.get("/config")
/app/backend/core/communications/routes.py:155:@router.get("/config/{config_id}")
/app/backend/core/communications/routes.py:168:@router.post("/config")
/app/backend/core/communications/routes.py:205:@router.put("/config/{config_id}")
/app/backend/core/communications/routes.py:231:@router.get("/templates")
/app/backend/core/communications/routes.py:246:@router.get("/templates/{template_id}")
/app/backend/core/communications/routes.py:262:@router.post("/templates")
/app/backend/core/communications/routes.py:295:@router.put("/templates/{template_id}")
/app/backend/core/communications/routes.py:321:@router.get("/log")
/app/backend/core/communications/routes.py:354:@router.get("/stats")
/app/backend/core/communications/routes.py:373:@router.get("/queue-status")
/app/backend/core/communications/routes.py:389:@router.post("/test")
/app/backend/core/communications/routes.py:440:@router.post("/reprocesar")
/app/backend/core/communications/routes.py:464:@router.post("/inicializar")
/app/backend/core/communications/routes.py:488:@router.get("/providers")
/app/backend/core/communications/routes.py:502:@router.get("/providers/{provider_id}")
/app/backend/core/communications/routes.py:524:@router.get("/provider-status")
/app/backend/core/communications/routes.py:553:@router.post("/test-real")
/app/backend/core/communications/routes.py:639:@router.post("/config/set-twilio")
/app/backend/core/communications/routes.py:686:@router.put("/config/{config_id}/set-provider")
/app/backend/core/centro_control/routes.py:225:@router.get("/salud")
/app/backend/core/centro_control/routes.py:276:@router.get("/salud/resumen")
/app/backend/core/centro_control/routes.py:308:@router.post("/regresiones")
/app/backend/core/centro_control/routes.py:382:@router.get("/regresiones/{modulo}")
/app/backend/core/centro_control/routes.py:420:@router.get("/fuentes")
/app/backend/core/centro_control/routes.py:463:@router.get("/alertas")
/app/backend/core/centro_control/routes.py:488:@router.post("/alertas/acknowledge")
/app/backend/core/centro_control/routes.py:521:@router.get("/historial")
/app/backend/core/centro_control/routes.py:555:@router.get("/matriz-resolucion")
/app/backend/core/centro_control/routes.py:588:@router.get("/ping")
/app/backend/core/centro_control/routes.py:608:@router.get("/estado")
/app/backend/core/centro_control/routes.py:684:@router.get("/jobs")
/app/backend/core/centro_control/routes.py:743:@router.get("/bitacora")
/app/backend/core/centro_control/routes.py:775:@router.post("/bitacora")
/app/backend/core/centro_control/routes.py:832:@router.get("/metricas")
/app/backend/core/centro_control/routes.py:943:@router.get("/ws/status")
/app/backend/core/centro_control/routes.py:952:@router.post("/notificar/alerta-critica")
/app/backend/core/centro_control/routes.py:970:@router.post("/notificar/test")
/app/backend/core/centro_control/routes.py:1004:@router.get("/email/config")
/app/backend/core/centro_control/routes.py:1015:@router.post("/email/test")
/app/backend/core/centro_control/routes.py:1036:@router.post("/email/alerta-critica")
/app/backend/core/centro_control/routes.py:1075:@router.get("/whatsapp/config")
/app/backend/core/centro_control/routes.py:1086:@router.post("/whatsapp/test")
/app/backend/core/centro_control/routes.py:1110:@router.post("/whatsapp/alerta-critica")
/app/backend/core/centro_control/routes.py:1145:@router.get("/notificaciones/config")
/app/backend/core/centro_control/routes.py:1186:@router.get("/destinatarios")
/app/backend/core/centro_control/routes.py:1209:@router.get("/destinatarios/resumen")
/app/backend/core/centro_control/routes.py:1221:@router.post("/destinatarios")
/app/backend/core/centro_control/routes.py:1255:@router.put("/destinatarios/{recipient_id}")
/app/backend/core/centro_control/routes.py:1286:@router.delete("/destinatarios/{recipient_id}")
/app/backend/core/rbac/routes.py:77:@router.get("/roles", summary="Listar roles")
/app/backend/core/rbac/routes.py:90:@router.post("/roles", summary="Crear rol")
/app/backend/core/rbac/routes.py:106:@router.get("/roles/{rol_id}", summary="Obtener rol")
/app/backend/core/rbac/routes.py:119:@router.put("/roles/{rol_id}", summary="Actualizar rol")
/app/backend/core/rbac/routes.py:139:@router.delete("/roles/{rol_id}", summary="Eliminar rol")
/app/backend/core/rbac/routes.py:164:@router.get("/permisos", summary="Listar permisos")
/app/backend/core/rbac/routes.py:186:@router.post("/asignar", summary="Asignar rol a usuario")
/app/backend/core/rbac/routes.py:211:@router.post("/revocar", summary="Revocar rol de usuario")
/app/backend/core/rbac/routes.py:232:@router.get("/usuario/{user_id}/permisos", summary="Permisos de un usuario")
/app/backend/core/rbac/routes.py:244:@router.get("/mis-permisos", summary="Mis permisos")
/app/backend/core/rbac/routes.py:264:@router.get("/audit", summary="Logs de auditoría RBAC")
/app/backend/core/rbac/routes.py:284:@router.post("/verificar", summary="Verificar permiso")
/app/backend/core/rbac/middleware.py:9:    @router.post("/cargos/{id}/aplicar")
/app/backend/core/rbac/middleware.py:67:        @router.get("/endpoint")
/app/backend/core/rbac/middleware.py:253:        @router.post("/cargos/{id}/aplicar")
```

## CONSULTAS DE INVENTARIOS / COMPRAS

```text
/app/backend/init_queries.py:26:venta.Al_Cve_Almacen,
/app/backend/init_queries.py:55:venta.Al_Cve_Almacen
/app/backend/init_queries.py:58:venta.Al_Cve_Almacen,
/app/backend/init_queries.py:84:venta.Al_Cve_Almacen
/app/backend/init_queries.py:88:DECLARE @ALMACEN VARCHAR(20)
/app/backend/init_queries.py:94:SET @ALMACEN = '@almacen'
/app/backend/init_queries.py:119:e.Al_Cve_Almacen,
/app/backend/init_queries.py:136:INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = S.Sc_Cve_Sucursal
/app/backend/init_queries.py:143:AND a.Al_Descripcion like '%' + @ALMACEN + '%'
/app/backend/init_queries.py:225:    "inventarios": """DECLARE @SUCURSAL VARCHAR(20)
/app/backend/init_queries.py:239:f.Al_Cve_Almacen,
/app/backend/init_queries.py:240:a.Al_Descripcion [Almacen],
/app/backend/init_queries.py:256:inner join Almacen a on a.Al_Cve_Almacen = f.Al_Cve_Almacen AND F.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
/app/backend/init_queries.py:298:            "email": "admin@inventario.com",
/app/backend/init_queries.py:307:        print("Usuario administrador creado: admin@inventario.com / admin123")
/app/backend/modules/comercial/service.py:1676:    Query para MPRO que devuelve KPIs DIVIDIDOS POR SUCURSAL (como en Inventarios).
/app/backend/modules/comercial/queries/mpro.py:13:- Almacen (A): Catálogo de almacenes
/app/backend/modules/comercial/queries/mpro.py:14:- Requisicion_Compra: Requisiciones de compra
/app/backend/modules/comercial/queries/mpro.py:15:- Fisico: Inventarios físicos
/app/backend/modules/comercial/queries/mpro.py:84:    'Almacen',
/app/backend/modules/comercial/queries/mpro.py:85:    'Requisicion_Compra',
/app/backend/modules/comercial/queries/softrestaurant.py:16:- almacen: Almacenes
/app/backend/modules/comercial/queries/softrestaurant.py:17:- invfisico: Inventarios físicos
/app/backend/modules/comercial/queries/softrestaurant.py:64:    'almacen',
/app/backend/modules/comercial/queries/softrestaurant.py:65:    'invfisico',
/app/backend/modules/comercial/queries/softrestaurant.py:66:    'invfisicomovtos',
/app/backend/modules/comercial/queries/softrestaurant.py:68:    'comprasmovtos',
/app/backend/modules/comercial/crm_router.py:241:# MODELOS PYDANTIC: PEDIDOS (FASE 9)
/app/backend/modules/comercial/crm_router.py:243:class ConvertirPedidoCreate(BaseModel):
/app/backend/modules/comercial/crm_router.py:248:# ENDPOINTS: PEDIDOS Y REMISIONES (FASE 9)
/app/backend/modules/comercial/crm_router.py:250:@router.get("/pedidos-venta")
/app/backend/modules/comercial/crm_router.py:251:def obtener_pedidos_activos():
/app/backend/modules/comercial/crm_router.py:253:    Fase 9: Consulta los pedidos oficiales del maestro transaccional Venta_Pedidos.
/app/backend/modules/comercial/crm_router.py:255:    query = "SELECT * FROM dbo.Venta_Pedidos ORDER BY FechaCreacion DESC"
/app/backend/modules/comercial/crm_router.py:258:@router.post("/pedidos-venta/convertir")
/app/backend/modules/comercial/crm_router.py:259:def convertir_cotizacion_a_pedido(payload: ConvertirPedidoCreate):
/app/backend/modules/comercial/crm_router.py:261:    Fase 9: Flujo transaccional. Convierte una Cotización Oficial en un Pedido Maestro.
/app/backend/modules/comercial/crm_router.py:271:        raise HTTPException(status_code=400, detail="Esta cotización ya fue procesada previamente a pedido.")
/app/backend/modules/comercial/crm_router.py:273:    # 2. Inyectar datos en la tabla blindada de Pedidos
/app/backend/modules/comercial/crm_router.py:274:    folio_pedido = f"PED-{cot[0]['FolioCotizacion'].split('-')[-1]}"
/app/backend/modules/comercial/crm_router.py:275:    query_ins_pedido = """
/app/backend/modules/comercial/crm_router.py:276:        INSERT INTO dbo.Venta_Pedidos (CuentaID, FolioPedido, Subtotal, Impuesto, Total, Moneda, TipoCambio, UsuarioCreadorID, Estatus)
/app/backend/modules/comercial/crm_router.py:277:        OUTPUT INSERTED.PedidoID
/app/backend/modules/comercial/crm_router.py:280:    params_pedido = (
/app/backend/modules/comercial/crm_router.py:281:        cot[0]["CuentaID"], folio_pedido, cot[0]["Subtotal"], cot[0]["Impuesto"], 
/app/backend/modules/comercial/crm_router.py:284:    res_pedido = execute_hub_query(query_ins_pedido, params_pedido)
/app/backend/modules/comercial/crm_router.py:285:    if not res_pedido:
/app/backend/modules/comercial/crm_router.py:286:        raise HTTPException(status_code=400, detail="Error en la generación del Pedido Maestro.")
/app/backend/modules/comercial/crm_router.py:288:    pedido_id = res_pedido[0]["PedidoID"]
/app/backend/modules/comercial/crm_router.py:290:    # 3. Clonar las líneas de detalle hacia Venta_PedidosDetalle
/app/backend/modules/comercial/crm_router.py:295:        INSERT INTO dbo.Venta_PedidosDetalle (PedidoID, ProductoID, Cantidad, PrecioUnitario, TotalLinea)
/app/backend/modules/comercial/crm_router.py:299:        execute_hub_query(query_ins_linea, (pedido_id, linea["ProductoID"], linea["Cantidad"], linea["PrecioUnitario"], linea["TotalLinea"]))
/app/backend/modules/comercial/crm_router.py:306:        "mensaje": "Conversión a Pedido Maestro completada de forma exitosa",
/app/backend/modules/comercial/crm_router.py:307:        "PedidoID": pedido_id,
/app/backend/modules/comercial/crm_router.py:308:        "FolioPedido": folio_pedido,
/app/backend/modules/comercial/crm_router.py:316:    PedidoID: int
/app/backend/modules/comercial/crm_router.py:333:        SELECT ImplementacionID, PedidoID, CuentaID, NombreProyecto, Estatus, ProgresoPorcentaje, FechaEntregaEstimada
/app/backend/modules/comercial/crm_router.py:341:    """Fase 10: Da de alta un nuevo proyecto ligado a un Pedido Ganado en el CRM."""
/app/backend/modules/comercial/crm_router.py:343:        INSERT INTO dbo.CRM_Implementaciones (PedidoID, CuentaID, NombreProyecto, Estatus, UsuarioLiderID, ProgresoPorcentaje, FechaKickoff)
/app/backend/modules/comercial/crm_router.py:347:    params = (proyecto.PedidoID, proyecto.CuentaID, proyecto.NombreProyecto, proyecto.UsuarioLiderID)
/app/backend/modules/comercial/crm_router.py:564:    PedidoID: int = Field(..., description="ID del Pedido Maestro Blindado")
/app/backend/modules/comercial/crm_router.py:580:        INSERT INTO dbo.CRM_ERPSyncLog (PedidoID, SistemaERP, MetodoTransaccion, PayloadRaw, EstatusERP)
/app/backend/modules/comercial/crm_router.py:584:    params = (payload.PedidoID, payload.SistemaERP, payload.MetodoTransaccion, payload.PayloadRaw)
/app/backend/modules/comercial/crm_router.py:603:        SELECT ERPSyncID, PedidoID, SistemaERP, MetodoTransaccion, EstatusERP, FechaRegistro 
/app/backend/modules/comercial/rentabilidad.py:5:def evaluar_margen_pedido(pedido_id: int, umbral_minimo_margen: float = 15.0) -> Dict[str, Any]:
/app/backend/modules/comercial/rentabilidad.py:8:    Calcula el costo real y el margen de ganancia de un pedido en base a la 
/app/backend/modules/comercial/rentabilidad.py:9:    data consolidada de inventarios físicos y ventas en EDARSAHUB SQL.
/app/backend/modules/comercial/rentabilidad.py:11:    # 1. Obtener el detalle del pedido y sus precios de venta desde el módulo blindado
/app/backend/modules/comercial/rentabilidad.py:12:    query_pedido = """
/app/backend/modules/comercial/rentabilidad.py:13:        SELECT PedidoID, ProductoID, Cantidad, PrecioUnitario, (Cantidad * PrecioUnitario) as TotalLinea
/app/backend/modules/comercial/rentabilidad.py:14:        FROM dbo.Venta_PedidosDetalle
/app/backend/modules/comercial/rentabilidad.py:15:        WHERE PedidoID = %s
/app/backend/modules/comercial/rentabilidad.py:17:    lineas_pedido = execute_hub_query(query_pedido, (pedido_id,))
/app/backend/modules/comercial/rentabilidad.py:19:    if not lineas_pedido:
/app/backend/modules/comercial/rentabilidad.py:20:        raise HTTPException(status_code=404, detail=f"No se encontraron líneas de detalle para el Pedido ID {pedido_id}")
/app/backend/modules/comercial/rentabilidad.py:26:    # 2. Auditar cada producto contra el catálogo de costos consolidados de inventario
/app/backend/modules/comercial/rentabilidad.py:27:    for linea in lineas_pedido:
/app/backend/modules/comercial/rentabilidad.py:35:        # Consultar el costo unitario consolidado en el historial de inventarios físicos síncronos
/app/backend/modules/comercial/rentabilidad.py:38:            FROM dbo.Compras_Inventarios_Fisicos_Sync
/app/backend/modules/comercial/rentabilidad.py:59:    # 3. Consolidar métricas finales del pedido
/app/backend/modules/comercial/rentabilidad.py:65:        "PedidoID": pedido_id,
/app/backend/modules/comercial/repository.py:138:        'query_inventario': parse_json_field(row.get('query_inventario')),
/app/backend/modules/fase2_operativo/__init__.py:2:FASE 2A - Módulo Operativo de Automatización de Inventarios
/app/backend/modules/fase2_operativo/sql_repository.py:7:- Workflow_Inventarios
/app/backend/modules/fase2_operativo/sql_repository.py:8:- Tareas_Inventario
/app/backend/modules/fase2_operativo/sql_repository.py:10:- Inventarios_SinAsignar
/app/backend/modules/fase2_operativo/sql_repository.py:98:    almacen_id: str,
/app/backend/modules/fase2_operativo/sql_repository.py:109:        FROM Workflow_Inventarios
/app/backend/modules/fase2_operativo/sql_repository.py:112:          AND AlmacenID = %s
/app/backend/modules/fase2_operativo/sql_repository.py:116:    params = (server_id, sucursal_id or '', almacen_id, folio_final_key)
/app/backend/modules/fase2_operativo/sql_repository.py:128:    almacen_id: str,
/app/backend/modules/fase2_operativo/sql_repository.py:129:    almacen_nombre: str,
/app/backend/modules/fase2_operativo/sql_repository.py:138:    folio_inventario: str = None
/app/backend/modules/fase2_operativo/sql_repository.py:140:    """Crea un nuevo workflow de inventario."""
/app/backend/modules/fase2_operativo/sql_repository.py:142:        INSERT INTO Workflow_Inventarios (
/app/backend/modules/fase2_operativo/sql_repository.py:143:            WorkflowID, ProcesadoID, FolioInventario,
/app/backend/modules/fase2_operativo/sql_repository.py:145:            AlmacenID, AlmacenNombre, FoliosInicialesJSON, FoliosFinalesJSON,
/app/backend/modules/fase2_operativo/sql_repository.py:153:        workflow_id, folio_final_key, folio_inventario,
/app/backend/modules/fase2_operativo/sql_repository.py:155:        almacen_id, almacen_nombre,
/app/backend/modules/fase2_operativo/sql_repository.py:173:        UPDATE Workflow_Inventarios
/app/backend/modules/fase2_operativo/sql_repository.py:194:            WorkflowID as id, ProcesadoID as procesado_id, FolioInventario as folio_inventario,
/app/backend/modules/fase2_operativo/sql_repository.py:197:            AlmacenID as almacen_id, AlmacenNombre as almacen_nombre,
/app/backend/modules/fase2_operativo/sql_repository.py:205:        FROM Workflow_Inventarios
/app/backend/modules/fase2_operativo/sql_repository.py:227:    """Crea una nueva tarea de inventario."""
/app/backend/modules/fase2_operativo/sql_repository.py:229:        INSERT INTO Tareas_Inventario (
/app/backend/modules/fase2_operativo/sql_repository.py:268:        FROM Tareas_Inventario
/app/backend/modules/fase2_operativo/sql_repository.py:281:        UPDATE Tareas_Inventario
/app/backend/modules/fase2_operativo/sql_repository.py:310:        UPDATE Tareas_Inventario
/app/backend/modules/fase2_operativo/sql_repository.py:332:        FROM Tareas_Inventario
/app/backend/modules/fase2_operativo/sql_repository.py:392:# INVENTARIOS SIN ASIGNAR
/app/backend/modules/fase2_operativo/sql_repository.py:395:async def registrar_inventario_sin_asignar(
/app/backend/modules/fase2_operativo/sql_repository.py:400:    almacen_id: str,
/app/backend/modules/fase2_operativo/sql_repository.py:401:    almacen_nombre: str,
/app/backend/modules/fase2_operativo/sql_repository.py:402:    folio_inventario: str,
/app/backend/modules/fase2_operativo/sql_repository.py:406:    """Registra un inventario que no pudo ser procesado por falta de configuración."""
/app/backend/modules/fase2_operativo/sql_repository.py:411:        INSERT INTO Inventarios_SinAsignar (
/app/backend/modules/fase2_operativo/sql_repository.py:413:            AlmacenID, AlmacenNombre, FolioInventario,
/app/backend/modules/fase2_operativo/sql_repository.py:421:        almacen_id, almacen_nombre, folio_inventario or '',
/app/backend/modules/fase2_operativo/sql_repository.py:427:        logger.info(f"[FASE2_SQL] Inventario sin asignar registrado: {server_name}/{almacen_nombre}")
/app/backend/modules/fase2_operativo/sql_repository.py:519:async def obtener_config_asignacion(server_id: str, almacen_id: str) -> Optional[Dict]:
/app/backend/modules/fase2_operativo/sql_repository.py:526:            ConfigID as id, ServerID as server_id, AlmacenID as almacen_id,
/app/backend/modules/fase2_operativo/sql_repository.py:530:          AND (AlmacenID = %s OR AlmacenID = '')
/app/backend/modules/fase2_operativo/sql_repository.py:533:            CASE WHEN AlmacenID = %s THEN 0 ELSE 1 END,
/app/backend/modules/fase2_operativo/sql_repository.py:536:    params = (server_id, almacen_id, almacen_id)
/app/backend/modules/fase2_operativo/sql_repository.py:576:    'registrar_inventario_sin_asignar',
/app/backend/modules/fase2_operativo/router.py:37:        "description": "Módulo Operativo de Automatización de Inventarios"
/app/backend/modules/fase2_operativo/repositories/auditoria_programada_repository.py:57:            "AlmacenID": data.get("almacen_id", ""),
/app/backend/modules/fase2_operativo/repositories/auditoria_programada_repository.py:132:            "almacen_id": "AlmacenID",
/app/backend/modules/fase2_operativo/repositories/auditoria_programada_repository.py:586:            "almacen_id": row.get("AlmacenID"),
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:2:Repositorio para workflow_inventarios
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:10:Gestiona el acceso a datos de workflows de inventario.
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:26:    Repository para la tabla Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:50:        super().__init__(db, "workflow_inventarios")
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:37:        almacen_id: Optional[str] = None
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:43:        1. Buscar por server_id + sucursal_id + almacen_id (si se proporciona)
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:56:            if almacen_id:
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:86:        almacen_id: Optional[str] = None,
/app/backend/modules/fase2_operativo/repositories/justificacion_repository.py:2:Repositorio para justificaciones_inventario - VERSIÓN SQL
/app/backend/modules/fase2_operativo/repositories/justificacion_repository.py:26:        super().__init__("justificaciones_inventario")
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:2:Repositorio para tareas_inventario
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:10:Gestiona el acceso a datos de tareas de inventario.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:27:    Repository para la tabla Tareas_Inventario.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:32:    NOTA: server_id no existe en Tareas_Inventario.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:33:    Para filtrar por server_id se requiere JOIN con Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:52:        super().__init__(db, "tareas_inventario")
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:149:        NOTA: Tareas_Inventario no tiene ServerID directamente.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:150:        Para filtrar por server_ids se requiere JOIN con Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:167:        # NOTA: server_id no existe en Tareas_Inventario
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:172:                "Filtro RBAC debe aplicarse en service con JOIN a Workflow_Inventarios."
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:258:        NOTA: server_ids requiere JOIN con Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:270:        # NOTA: server_id no existe en Tareas_Inventario
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:331:        Obtiene tareas con filtro RBAC mediante JOIN a Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:336:        ya que Tareas_Inventario no tiene ese campo directamente.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:354:            FROM Tareas_Inventario t
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:355:            INNER JOIN Workflow_Inventarios w ON t.WorkflowID = w.WorkflowID
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:391:            FROM Tareas_Inventario t
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:392:            INNER JOIN Workflow_Inventarios w ON t.WorkflowID = w.WorkflowID
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:29:    "workflow_inventarios": "Workflow_Inventarios",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:30:    "tareas_inventario": "Tareas_Inventario",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:36:    "justificaciones_inventario": "Workflow_Justificaciones",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:45:    "pedidos_procesados_automatizacion": "Operativo_PedidosProcesados",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:56:    "pedidos_procesados_automatizacion": "Operativo_PedidosProcesados",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:57:    "inventarios_fisicos_procesados": "Compras_Inventarios_Fisicos_Sync",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:62:    "Workflow_Inventarios": {
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:71:        "folio_inventario": "FolioInventario",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:76:        "almacen_id": "AlmacenID",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:77:        "almacen_nombre": "AlmacenNombre",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:82:    "Tareas_Inventario": {
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:719:            "Workflow_Inventarios": "WorkflowID",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:720:            "Tareas_Inventario": "TareaID",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:732:            "Operativo_PedidosProcesados": "PedidoID",
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:33:        "descripcion": "Tolerancia absoluta en unidades para diferencias de inventario"
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:43:        "descripcion": "Precio unitario por defecto si no viene del análisis de inventario"
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:11:- NO toca automatizacion_inventarios_folios_procesados
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:26:    "workflow_inventarios",
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:28:    "tareas_inventario",
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:30:    "justificaciones_inventario",
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:37:    "automatizacion_inventarios_folios_procesados",
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:75:    # workflow_inventarios
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:77:        db.workflow_inventarios.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:82:        indices_creados.append("workflow_inventarios.idx_procesado_id_unique")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:83:        print("  ✓ Índice: workflow_inventarios.procesado_id (unique)")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:86:            print("  ⚠ Índice ya existe: workflow_inventarios.procesado_id")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:91:        db.workflow_inventarios.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:95:        indices_creados.append("workflow_inventarios.idx_estado_workflow")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:96:        print("  ✓ Índice: workflow_inventarios.estado_workflow")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:99:            print("  ⚠ Índice ya existe: workflow_inventarios.estado_workflow")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:104:        db.workflow_inventarios.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:108:        indices_creados.append("workflow_inventarios.idx_fecha_creacion")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:109:        print("  ✓ Índice: workflow_inventarios.fecha_creacion")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:112:            print("  ⚠ Índice ya existe: workflow_inventarios.fecha_creacion")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:130:    # tareas_inventario
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:132:        db.tareas_inventario.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:136:        indices_creados.append("tareas_inventario.idx_workflow_id")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:137:        print("  ✓ Índice: tareas_inventario.workflow_id")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:140:            print("  ⚠ Índice ya existe: tareas_inventario.workflow_id")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:145:        db.tareas_inventario.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:149:        indices_creados.append("tareas_inventario.idx_usuario_asignado")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:150:        print("  ✓ Índice: tareas_inventario.usuario_asignado_id")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:153:            print("  ⚠ Índice ya existe: tareas_inventario.usuario_asignado_id")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:158:        db.tareas_inventario.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:162:        indices_creados.append("tareas_inventario.idx_estado_tarea")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:163:        print("  ✓ Índice: tareas_inventario.estado_tarea")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:166:            print("  ⚠ Índice ya existe: tareas_inventario.estado_tarea")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:171:        db.tareas_inventario.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:175:        indices_creados.append("tareas_inventario.idx_fecha_limite")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:176:        print("  ✓ Índice: tareas_inventario.fecha_limite")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:179:            print("  ⚠ Índice ya existe: tareas_inventario.fecha_limite")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:197:    # justificaciones_inventario
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:199:        db.justificaciones_inventario.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:203:        indices_creados.append("justificaciones_inventario.idx_workflow_id")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:204:        print("  ✓ Índice: justificaciones_inventario.workflow_id")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:207:            print("  ⚠ Índice ya existe: justificaciones_inventario.workflow_id")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:212:        db.justificaciones_inventario.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:216:        indices_creados.append("justificaciones_inventario.idx_diferencia_id")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:217:        print("  ✓ Índice: justificaciones_inventario.diferencia_id")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:220:            print("  ⚠ Índice ya existe: justificaciones_inventario.diferencia_id")
/app/backend/modules/fase2_operativo/schemas/tarea_schemas.py:2:Schemas Pydantic para Tareas de Inventario
/app/backend/modules/fase2_operativo/schemas/tarea_schemas.py:47:    """Schema de tarea como está almacenada en BD."""
/app/backend/modules/fase2_operativo/schemas/tarea_schemas.py:96:    """Schema de historial como está almacenado en BD."""
/app/backend/modules/fase2_operativo/schemas/cargos_schemas.py:6:derivados de diferencias de inventario dictaminadas.
/app/backend/modules/fase2_operativo/schemas/auditoria_schemas.py:38:    """Schema de decisión como está almacenada en BD."""
/app/backend/modules/fase2_operativo/schemas/responsabilidad_schemas.py:6:de diferencias de inventario y flujo de aprobaciones.
/app/backend/modules/fase2_operativo/schemas/responsabilidad_schemas.py:84:    """Schema de responsabilidad como está almacenada en BD."""
/app/backend/modules/fase2_operativo/schemas/configuracion_schemas.py:31:    """Schema de configuración como está almacenada en BD."""
/app/backend/modules/fase2_operativo/schemas/workflow_schemas.py:2:Schemas Pydantic para Workflow de Inventarios
/app/backend/modules/fase2_operativo/schemas/workflow_schemas.py:35:    """Schema de workflow como está almacenado en BD."""
/app/backend/modules/fase2_operativo/schemas/justificacion_schemas.py:2:Schemas Pydantic para Justificaciones de Inventario
/app/backend/modules/fase2_operativo/schemas/justificacion_schemas.py:55:    """Schema de justificación como está almacenada en BD."""
/app/backend/modules/fase2_operativo/schemas/justificacion_schemas.py:116:    """Schema de detalle como está almacenado en BD."""
/app/backend/modules/fase2_operativo/schemas/auditoria_programada_schemas.py:27:    INVENTARIO_COMPLETO = "INVENTARIO_COMPLETO"
/app/backend/modules/fase2_operativo/schemas/auditoria_programada_schemas.py:28:    INVENTARIO_SELECTIVO = "INVENTARIO_SELECTIVO"
/app/backend/modules/fase2_operativo/schemas/auditoria_programada_schemas.py:57:    almacenes: List[str] = Field(default=[], description="IDs de almacenes específicos, vacío = todos")
/app/backend/modules/fase2_operativo/schemas/auditoria_programada_schemas.py:95:    almacenes: List[str] = []
/app/backend/modules/fase2_operativo/schemas/auditoria_programada_schemas.py:112:    almacenes: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/schemas/auditoria_programada_schemas.py:131:    almacenes: List[str]
/app/backend/modules/fase2_operativo/schemas/enums.py:6:de trabajo de inventarios.
/app/backend/modules/fase2_operativo/schemas/enums.py:12:    """Estados posibles de un workflow de inventario."""
/app/backend/modules/fase2_operativo/services/document_data_service.py:75:            repo = SQLBaseRepository("workflow_inventarios")
/app/backend/modules/fase2_operativo/services/document_data_service.py:96:            - diferencias: Lista de diferencias de inventario
/app/backend/modules/fase2_operativo/services/cargos_service.py:6:derivados de diferencias de inventario dictaminadas.
/app/backend/modules/fase2_operativo/services/orquestador_service.py:11:- Detecta si hay diferencias en análisis de inventario
/app/backend/modules/fase2_operativo/services/orquestador_service.py:29:    registrar_inventario_sin_asignar,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:41:    Servicio que orquesta la creación de workflows desde análisis de inventarios.
/app/backend/modules/fase2_operativo/services/orquestador_service.py:60:        almacen_id: str,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:61:        almacen_nombre: str,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:69:        folio_inventario: str = None
/app/backend/modules/fase2_operativo/services/orquestador_service.py:72:        Procesa los resultados del análisis de inventario y crea workflow si hay diferencias.
/app/backend/modules/fase2_operativo/services/orquestador_service.py:103:                logger.info(f"Orquestador: Sin diferencias para {sucursal_nombre}/{almacen_nombre}")
/app/backend/modules/fase2_operativo/services/orquestador_service.py:118:                server_id, sucursal_id, almacen_id, folio_final_key
/app/backend/modules/fase2_operativo/services/orquestador_service.py:130:                server_id, almacen_id
/app/backend/modules/fase2_operativo/services/orquestador_service.py:139:                    f"No existe configuración de asignación para server={server_id}, almacen={almacen_id}. "
/app/backend/modules/fase2_operativo/services/orquestador_service.py:140:                    f"Configure un responsable en Configuración → Asignaciones de Inventarios."
/app/backend/modules/fase2_operativo/services/orquestador_service.py:143:                # Registrar en inventarios_sin_asignar (SQL)
/app/backend/modules/fase2_operativo/services/orquestador_service.py:144:                await registrar_inventario_sin_asignar(
/app/backend/modules/fase2_operativo/services/orquestador_service.py:149:                    almacen_id=almacen_id,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:150:                    almacen_nombre=almacen_nombre,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:151:                    folio_inventario=folio_inventario,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:158:                    tipo="INVENTARIO_SIN_RESPONSABLE",
/app/backend/modules/fase2_operativo/services/orquestador_service.py:160:                    titulo="Inventario sin responsable configurado",
/app/backend/modules/fase2_operativo/services/orquestador_service.py:162:                        f"Se detectó inventario en {server_name} / {sucursal_nombre} / {almacen_nombre} "
/app/backend/modules/fase2_operativo/services/orquestador_service.py:163:                        f"(Folio: {folio_inventario}) con diferencias por ${valor_total:,.2f}, "
/app/backend/modules/fase2_operativo/services/orquestador_service.py:166:                    modulo="inventarios",
/app/backend/modules/fase2_operativo/services/orquestador_service.py:170:                        "almacen_nombre": almacen_nombre,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:171:                        "folio_inventario": folio_inventario,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:174:                    accion_sugerida="Configurar responsable en Configuración → Asignaciones de Inventarios"
/app/backend/modules/fase2_operativo/services/orquestador_service.py:179:                    f"para {server_name}/{sucursal_nombre}/{almacen_nombre}"
/app/backend/modules/fase2_operativo/services/orquestador_service.py:189:            # Determinar folio_inventario
/app/backend/modules/fase2_operativo/services/orquestador_service.py:190:            folio_inv = folio_inventario
/app/backend/modules/fase2_operativo/services/orquestador_service.py:200:                almacen_id=almacen_id,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:201:                almacen_nombre=almacen_nombre,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:210:                folio_inventario=folio_inv
/app/backend/modules/fase2_operativo/services/orquestador_service.py:230:                almacen_nombre=almacen_nombre,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:243:                    almacen_nombre=almacen_nombre,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:254:            logger.info(f"Orquestador: ✅ Workflow {workflow_id} creado para {sucursal_nombre}/{almacen_nombre}")
/app/backend/modules/fase2_operativo/services/orquestador_service.py:272:        almacen_id: str
/app/backend/modules/fase2_operativo/services/orquestador_service.py:279:            config = await obtener_config_asignacion(server_id, almacen_id)
/app/backend/modules/fase2_operativo/services/orquestador_service.py:284:                    f"server={server_id}, almacen={almacen_id}"
/app/backend/modules/fase2_operativo/services/orquestador_service.py:301:                f"{usuario.get('name', usuario.get('email'))} para server={server_id}, almacen={almacen_id}"
/app/backend/modules/fase2_operativo/services/orquestador_service.py:319:        almacen_nombre: str,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:338:                titulo=f"Justificar diferencias - {sucursal_nombre}/{almacen_nombre}",
/app/backend/modules/fase2_operativo/services/orquestador_service.py:360:        almacen_nombre: str,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:378:                    almacen_nombre=almacen_nombre,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:390:                        titulo=f"Justificar diferencias - {sucursal_nombre}/{almacen_nombre}",
/app/backend/modules/fase2_operativo/services/notification_service.py:46:        almacen_nombre: str,
/app/backend/modules/fase2_operativo/services/notification_service.py:72:                almacen_nombre=almacen_nombre,
/app/backend/modules/fase2_operativo/services/notification_service.py:101:                    "almacen": almacen_nombre,
/app/backend/modules/fase2_operativo/services/notification_service.py:429:        almacen_nombre: str,
/app/backend/modules/fase2_operativo/services/notification_service.py:460:        <p>Se ha detectado un nuevo análisis de inventario con diferencias que requiere tu atención.</p>
/app/backend/modules/fase2_operativo/services/notification_service.py:463:            <strong>📍 Ubicación:</strong> {sucursal_nombre} / {almacen_nombre}
/app/backend/modules/fase2_operativo/services/notification_service.py:658:                Se ha aplicado un cargo económico a tu cuenta derivado de diferencias de inventario.
/app/backend/modules/fase2_operativo/services/pdf_service.py:196:            "REPORTE DE WORKFLOW DE INVENTARIO",
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:80:            almacenes=data.almacenes,
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:197:            workflow_id = self._crear_workflow_inventario(auditoria)
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:235:    def _crear_workflow_inventario(self, auditoria: Dict) -> str:
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:236:        """Crea workflow de inventario (sync - usa PyMongo directamente)."""
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:249:            "almacenes": auditoria.get("almacenes", []),
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:258:        workflow_repo = SQLBaseRepository("workflow_inventarios")
/app/backend/modules/fase2_operativo/services/excel_service.py:133:        cell.value = "REPORTE DE WORKFLOW DE INVENTARIO"
/app/backend/modules/fase2_operativo/services/sla_service.py:518:            folio = workflow.get("folio_inventario", "N/A") if workflow else tarea.get("folio", "N/A")
/app/backend/modules/fase2_operativo/services/sla_service.py:561:            folio = workflow.get("folio_inventario", "N/A") if workflow else tarea.get("folio", "N/A")
/app/backend/modules/fase2_operativo/services/sla_service.py:601:            folio = workflow.get("folio_inventario", "N/A") if workflow else tarea.get("folio", "N/A")
/app/backend/modules/fase2_operativo/services/auditoria_service.py:2:Servicio de Auditoría de Inventario
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:7:1. PEDIDO_DETECTADO
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:8:2. PENDIENTE_INVENTARIO_FISICO (si no hay inv. final)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:17:- Operativo_PedidosProcesados (control anti-duplicado)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:40:    PEDIDO_DETECTADO = "PEDIDO_DETECTADO"
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:41:    PENDIENTE_INVENTARIO_FISICO = "PENDIENTE_INVENTARIO_FISICO"
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:50:    """Estado de inventario por producto."""
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:86:        self._pedidos_repo = SQLBaseRepository("pedidos_procesados_automatizacion")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:87:        self._inv_repo = SQLBaseRepository("inventarios_fisicos_procesados")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:94:    def procesar_pedido_operativo(
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:96:        pedido_id: str,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:100:        almacen_id: str,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:101:        almacen_nombre: str,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:106:        fecha_pedido: datetime = None,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:111:        """Procesa pedido capturado - FLUJO COMPLETO SQL."""
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:113:        ya_procesado = self._pedidos_repo.find_one({
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:115:            "pedido_folio": pedido_id,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:121:                logger.info(f"[{pedido_id}] Ya procesado - retornando existente")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:126:        fecha_pedido = fecha_pedido or now
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:128:        fecha_fin_periodo = fecha_pedido
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:129:        fecha_inicio_periodo = fecha_pedido - timedelta(days=self.DIAS_PERIODO_ANALISIS)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:135:            "pedido_id": pedido_id,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:141:            "almacen_id": almacen_id,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:142:            "almacen_nombre": almacen_nombre,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:146:            "estado": EstadoAutomatizacion.PEDIDO_DETECTADO.value,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:147:            "fecha_pedido": fecha_pedido.isoformat(),
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:155:            "inventario_inicial_id": None,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:156:            "inventario_inicial_fecha": None,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:157:            "inventario_final_id": None,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:158:            "inventario_final_fecha": None,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:159:            "tiene_inventario_final": False,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:182:        # 1. Buscar inventario inicial
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:183:        inv_inicial = self._buscar_inventario_inicial(server_id, almacen_id, fecha_inicio_periodo)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:185:            registro["inventario_inicial_id"] = inv_inicial.get("folio") or inv_inicial.get("id")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:186:            registro["inventario_inicial_fecha"] = inv_inicial.get("fecha")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:188:        # 2. Buscar inventario final
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:189:        inv_final = self._buscar_inventario_final(server_id, almacen_id, fecha_pedido)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:192:            # SIN INVENTARIO FINAL - DETENER FLUJO
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:193:            registro["estado"] = EstadoAutomatizacion.PENDIENTE_INVENTARIO_FISICO.value
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:194:            registro["tiene_inventario_final"] = False
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:196:                "mensaje": "Inventario físico requerido",
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:197:                "fecha_requerida": fecha_pedido.strftime("%Y-%m-%d"),
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:198:                "almacen": almacen_nombre,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:199:                "accion": "Capturar inventario físico del día del pedido"
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:203:            self._marcar_pedido_procesado(server_id, pedido_id, origen_sistema, automatizacion_id)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:204:            self._registrar_bitacora(automatizacion_id, "PENDIENTE_INVENTARIO", usuario_id, {
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:205:                "mensaje": "Flujo detenido - sin inventario final"
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:208:            logger.info(f"[{automatizacion_id}] PENDIENTE_INVENTARIO_FISICO")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:211:        # 3. CON INVENTARIO FINAL - EJECUTAR AUDITORÍA
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:212:        registro["inventario_final_id"] = inv_final.get("folio") or inv_final.get("id")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:213:        registro["inventario_final_fecha"] = inv_final.get("fecha")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:214:        registro["tiene_inventario_final"] = True
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:229:        self._marcar_pedido_procesado(server_id, pedido_id, origen_sistema, automatizacion_id)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:389:        resumen = {"criticos": 0, "faltantes": 0, "optimos": 0, "sobrantes": 0, "total_pedido_optimo": 0}
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:404:            resumen["total_pedido_optimo"] += resultado_prod.get("pedido_optimo", 0)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:480:            "pendientes_inventario": 0,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:493:            if estado == EstadoAutomatizacion.PENDIENTE_INVENTARIO_FISICO.value:
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:494:                kpis["pendientes_inventario"] = count
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:515:        resumen = {"criticos": 0, "faltantes": 0, "optimos": 0, "sobrantes": 0, "total_pedido_optimo": 0}
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:531:            resumen["total_pedido_optimo"] += resultado.get("pedido_optimo", 0)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:537:        inv_final = producto.get("inventario_final", 0)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:541:            dias_inventario = 999
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:543:            dias_inventario = inv_final / consumo_diario
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:545:        if dias_inventario <= 0:
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:548:        elif dias_inventario < dias_objetivo:
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:551:        elif dias_inventario <= dias_objetivo * (1 + self.TOLERANCIA_OPTIMO):
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:559:        pedido_optimo = max(0, inv_optimo - inv_final)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:563:            "dias_inventario": round(dias_inventario, 1),
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:566:            "inventario_optimo": round(inv_optimo, 2),
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:567:            "pedido_optimo": round(pedido_optimo, 2),
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:588:    # INVENTARIOS (SQL)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:591:    def _buscar_inventario_inicial(
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:594:        almacen_id: str,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:597:        """Busca inventario inicial más cercano - SQL."""
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:602:            "almacen_id": almacen_id,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:609:    def _buscar_inventario_final(
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:612:        almacen_id: str,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:613:        fecha_pedido: datetime
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:615:        """Busca inventario final del día del pedido - SQL."""
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:616:        fecha_inicio = fecha_pedido.replace(hour=0, minute=0, second=0, microsecond=0)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:617:        fecha_fin = fecha_pedido.replace(hour=23, minute=59, second=59)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:621:            "almacen_id": almacen_id,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:632:    def _marcar_pedido_procesado(self, server_id: str, pedido_folio: str, origen: str, automatizacion_id: str):
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:633:        """Marca pedido como procesado - SQL."""
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:634:        self._pedidos_repo.insert_one({
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:637:            "pedido_folio": pedido_folio,
/app/backend/modules/fase2_operativo/services/responsabilidad_service.py:6:de diferencias de inventario y flujo de aprobaciones.
/app/backend/modules/fase2_operativo/services/tarea_service.py:2:Servicio de Tareas de Inventario
/app/backend/modules/fase2_operativo/services/tarea_service.py:32:    Servicio para gestión de tareas de inventario.
/app/backend/modules/fase2_operativo/services/workflow_service.py:2:Servicio de Workflow de Inventarios
/app/backend/modules/fase2_operativo/services/workflow_service.py:35:    Servicio para gestión de workflows de inventario.
/app/backend/modules/fase2_operativo/services/justificacion_service.py:2:Servicio de Justificaciones de Inventario
/app/backend/modules/fase2_operativo/services/justificacion_service.py:38:    Servicio para gestión de justificaciones de inventario.
/app/backend/modules/fase2_operativo/routes/sla_routes.py:246:        tarea = db.tareas_inventario.find_one({"id": tarea_id}, {"_id": 0})
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:4:Endpoints para el flujo: Pedido → Gerencia → Tesorería → Aprobado
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:31:class ProcesarPedidoRequest(BaseModel):
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:32:    pedido_id: str
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:36:    almacen_id: str
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:37:    almacen_nombre: str
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:80:# ENDPOINTS FASE 4.1 y 4.2 - DETECTOR DE PEDIDOS
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:89:    FASE 4.1 y 4.2: Ejecuta el detector de pedidos manualmente.
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:108:    from core.scheduler.jobs.pedidos_detector_job import ejecutar_detector_manual as _ejecutar
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:131:    Obtiene el estado actual del detector de pedidos.
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:144:        {"job_name": "pedidos_detector"},
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:152:        job_info = manager.get_job_info("pedidos_detector")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:175:    FASE 4.2: Lista tareas operativas de captura de inventario.
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:227:    Esto debería dispararse automáticamente cuando se captura el inventario,
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:350:@router.get("/compras/pedidos-procesados")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:351:async def listar_pedidos_procesados(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:358:    FASE 4.1: Lista pedidos que ya fueron procesados.
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:371:    pedidos = list(db.pedidos_procesados_automatizacion.find(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:377:        "total": len(pedidos),
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:378:        "pedidos": pedidos
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:404:async def procesar_pedido(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:405:    request: ProcesarPedidoRequest,
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:409:    Procesa pedido capturado.
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:416:    resultado = service.procesar_pedido_operativo(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:417:        pedido_id=request.pedido_id,
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:421:        almacen_id=request.almacen_id,
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:422:        almacen_nombre=request.almacen_nombre,
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:561:    El periodo operativo (fecha inventario inicial y fecha pedido) NO se modifica.
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:99:    db.tareas_inventario.update_many(
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:130:    tareas_vencidas = list(db.tareas_inventario.find(filtro_tareas, {"_id": 0}).limit(50))
/app/backend/modules/fase2_operativo/routes/documentos_routes.py:41:    - Diferencias: Detalle de diferencias de inventario
/app/backend/modules/api_connections/routes.py:75:    tipo_uso: str = Field("Otro", description="Tipo de uso: Ventas del día, Inventario, Cortes, Compras, Otro")
/app/backend/modules/api_connections/universal_test_routes.py:25:- Módulos: Comercial, Tablero, KPIs, Inventarios, Compras, Finanzas, Operaciones
/app/backend/modules/corporate_filters/router.py:286:    /api/almacenes
/app/backend/modules/corporate_filters/router.py:295:        "almacenes": [],
/app/backend/modules/corporate_filters/router.py:307:        "almacenes": ["empresas", "sucursales"],
/app/backend/modules/corporate_filters/router.py:328:        filters["almacenes"] = get_optional_catalog(
/app/backend/modules/corporate_filters/router.py:329:            ["Inventario_Almacenes", "Sistema_Almacenes", "Almacenes", "Sync_Almacenes"],
/app/backend/modules/corporate_filters/router.py:330:            ["id", "id_almacen", "almacen_id", "AlmacenID"],
/app/backend/modules/corporate_filters/router.py:331:            ["nombre", "nombre_almacen", "Almacen", "descripcion"],
/app/backend/modules/corporate_filters/router.py:332:            ["codigo", "clave", "codigo_almacen"]
/app/backend/modules/corporate_filters/router.py:343:            ["Sync_Productos", "Comercial_Productos", "Inventarios_Productos", "Productos"],
/app/backend/modules/rh/importador/repository.py:96:-- Propósito: Almacena registros de importación pendientes de validación/aprobación
/app/backend/modules/rh/solicitudes_catalogo.py:28:# ALMACENAMIENTO EN MEMORIA (Producción: migrar a SQL Server)
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:136:                AlmacenID as almacen_id,
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:137:                AlmacenNombre as almacen_nombre,
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:169:                AlmacenID as almacen_id,
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:170:                AlmacenNombre as almacen_nombre,
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:188:        almacen_id: str,
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:198:            WHERE UnidadNegocioID = %s AND AlmacenID = %s
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:200:        existente = await _execute_sql_async(check_query, (unidad_negocio_id, almacen_id or ''))
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:229:        prioridad = 20 if almacen_id else 10
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:238:                AlmacenID, AlmacenNombre,
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:248:            almacen_id or '', '',  # almacen_nombre se dejará vacío por ahora
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:265:        almacen_id: Optional[str] = None,
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:284:        if almacen_id is not None:
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:285:            updates.append("AlmacenID = %s")
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:286:            params.append(almacen_id)
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:340:        almacen_id: str
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:354:              AND (AlmacenID = %s OR AlmacenID = '')
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:357:                CASE WHEN AlmacenID = %s THEN 0 ELSE 1 END,
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:360:        rows = await _execute_sql_async(query, (server_id, almacen_id, almacen_id))
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:364:    # CATÁLOGO DE ALMACENES
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:367:    async def listar_almacenes(self, unidad_negocio_id: str) -> List[Dict]:
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:369:        Lista almacenes disponibles para una unidad de negocio.
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:370:        Retorna opción "(Todos)" + almacenes del servidor.
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:372:        resultado = [{"id": "", "nombre": "(Todos los almacenes)"}]
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:374:        # Intentar obtener almacenes desde SQL Server (tablas del servidor)
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:387:                # Por ahora retornar lista vacía de almacenes específicos
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:391:            logger.debug(f"Error listando almacenes: {e}")
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:395:    async def sincronizar_almacenes_unidad(
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:398:        almacenes: List[Dict],
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:402:        Sincroniza almacenes - operación placeholder.
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:405:        logger.info(f"[CONFIG_ASIG] Sincronización de almacenes omitida (SQL-only mode)")
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:406:        return len(almacenes)
/app/backend/modules/configuracion/services/almacenes_sync_service.py:2:Servicio de Sincronización de Almacenes
/app/backend/modules/configuracion/services/almacenes_sync_service.py:6:Sincroniza almacenes desde sistemas origen (SoftRestaurant/MPRO) al catálogo local MongoDB.
/app/backend/modules/configuracion/services/almacenes_sync_service.py:29:from modules.automatizacion.queries_soft import QUERY_ALMACENES as QUERY_ALMACENES_SOFT
/app/backend/modules/configuracion/services/almacenes_sync_service.py:30:from modules.automatizacion.queries_mpro import QUERY_ALMACENES_SUCURSAL as QUERY_ALMACENES_MPRO
/app/backend/modules/configuracion/services/almacenes_sync_service.py:36:class SyncAlmacenesResult:
/app/backend/modules/configuracion/services/almacenes_sync_service.py:38:    Resultado de sincronización de almacenes con metadatos útiles.
/app/backend/modules/configuracion/services/almacenes_sync_service.py:82:async def sincronizar_almacenes_desde_origen(
/app/backend/modules/configuracion/services/almacenes_sync_service.py:87:) -> SyncAlmacenesResult:
/app/backend/modules/configuracion/services/almacenes_sync_service.py:89:    Sincroniza almacenes desde el sistema origen al catálogo local.
/app/backend/modules/configuracion/services/almacenes_sync_service.py:95:    - Persiste en MongoDB (almacenes_catalogo)
/app/backend/modules/configuracion/services/almacenes_sync_service.py:104:        SyncAlmacenesResult con metadatos completos de la operación
/app/backend/modules/configuracion/services/almacenes_sync_service.py:106:    result = SyncAlmacenesResult(
/app/backend/modules/configuracion/services/almacenes_sync_service.py:121:            logger.warning(f"[Sync Almacenes] Error resolviendo contexto {unidad_negocio_id}: {e}")
/app/backend/modules/configuracion/services/almacenes_sync_service.py:153:            query = QUERY_ALMACENES_SOFT
/app/backend/modules/configuracion/services/almacenes_sync_service.py:161:            query = QUERY_ALMACENES_MPRO.replace(":sucursal_id", f"'{sucursal_origen_id}'")
/app/backend/modules/configuracion/services/almacenes_sync_service.py:168:        logger.info(f"[Sync Almacenes] Ejecutando query {system_type} para {unidad_negocio_id}")
/app/backend/modules/configuracion/services/almacenes_sync_service.py:174:            almacenes_origen = execute_sql_query(
/app/backend/modules/configuracion/services/almacenes_sync_service.py:183:            if almacenes_origen is None:
/app/backend/modules/configuracion/services/almacenes_sync_service.py:184:                almacenes_origen = []
/app/backend/modules/configuracion/services/almacenes_sync_service.py:186:            result.leidos_origen = len(almacenes_origen)
/app/backend/modules/configuracion/services/almacenes_sync_service.py:187:            logger.info(f"[Sync Almacenes] Leídos {result.leidos_origen} almacenes de {system_type}")
/app/backend/modules/configuracion/services/almacenes_sync_service.py:194:            logger.error(f"[Sync Almacenes] Error SQL {unidad_negocio_id}: {e}")
/app/backend/modules/configuracion/services/almacenes_sync_service.py:201:        almacenes_collection = db.almacenes_catalogo
/app/backend/modules/configuracion/services/almacenes_sync_service.py:203:        # IDs de almacenes que vienen del origen (para detectar desactivados)
/app/backend/modules/configuracion/services/almacenes_sync_service.py:206:        for alm in almacenes_origen:
/app/backend/modules/configuracion/services/almacenes_sync_service.py:209:                alm_id = str(alm.get("almacen_id", ""))
/app/backend/modules/configuracion/services/almacenes_sync_service.py:210:                alm_nombre = alm.get("almacen_nombre", "")
/app/backend/modules/configuracion/services/almacenes_sync_service.py:212:                alm_id = str(alm.get("almacen_id", ""))
/app/backend/modules/configuracion/services/almacenes_sync_service.py:213:                alm_nombre = alm.get("almacen_nombre", "")
/app/backend/modules/configuracion/services/almacenes_sync_service.py:221:            existente = await almacenes_collection.find_one({
/app/backend/modules/configuracion/services/almacenes_sync_service.py:229:                    await almacenes_collection.update_one(
/app/backend/modules/configuracion/services/almacenes_sync_service.py:241:                await almacenes_collection.insert_one({
/app/backend/modules/configuracion/services/almacenes_sync_service.py:254:        # PASO 6: Desactivar almacenes que ya no existen en origen
/app/backend/modules/configuracion/services/almacenes_sync_service.py:257:            # Buscar almacenes activos que no están en el origen
/app/backend/modules/configuracion/services/almacenes_sync_service.py:258:            desactivar_result = await almacenes_collection.update_many(
/app/backend/modules/configuracion/services/almacenes_sync_service.py:277:            f"Sincronizados {result.total_sincronizados} almacenes para {result.unidad_negocio_nombre}"
/app/backend/modules/configuracion/services/almacenes_sync_service.py:282:        logger.info(f"[Sync Almacenes] {result.message}")
/app/backend/modules/configuracion/services/almacenes_sync_service.py:289:        logger.exception(f"[Sync Almacenes] Error inesperado sincronizando {unidad_negocio_id}")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:10:2. Almacenes desde catálogo local (NO consulta SQL en tiempo real)
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:61:    almacen_id: str = Field("", description="ID del almacén (vacío = todos)")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:68:    almacen_id: Optional[str] = Field(None, description="Nuevo almacén (vacío = todos)")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:76:    almacen_id: str = ""
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:247:@router.get("/almacenes/{unidad_negocio_id}")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:248:async def listar_almacenes(
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:253:    Lista almacenes de una unidad de negocio.
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:257:    Incluye opción "(Todos los almacenes)" como primera opción.
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:263:    almacenes = await repo.listar_almacenes(unidad_negocio_id)
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:265:    return {"success": True, "data": almacenes}
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:268:@router.get("/almacenes/{unidad_negocio_id}/sync-info")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:269:async def info_sincronizacion_almacenes(
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:274:    Obtiene información de la última sincronización de almacenes.
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:278:        - total_almacenes: cantidad en catálogo
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:285:    almacen_mas_reciente = await get_db().almacenes_catalogo.find_one(
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:291:    total = await get_db().almacenes_catalogo.count_documents({
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:299:            "ultima_sincronizacion": almacen_mas_reciente.get("fecha_sync") if almacen_mas_reciente else None,
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:300:            "usuario_sync": almacen_mas_reciente.get("usuario_sync") if almacen_mas_reciente else None,
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:301:            "total_almacenes": total
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:353:    if request.almacen_id:
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:355:        almacenes = await repo.listar_almacenes(request.unidad_negocio_id)
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:356:        almacen_ids = [a["id"] for a in almacenes if a["id"]]  # Excluir opción "todos"
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:358:        if request.almacen_id not in almacen_ids:
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:370:            almacen_id=request.almacen_id,
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:386:            "almacen": config.get("almacen_nombre") or "(todos)",
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:392:        f"Asignación creada: {config['unidad_negocio_nombre']}/{config.get('almacen_nombre') or '(todos)'} "
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:414:    - almacen_id
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:432:    nuevo_almacen = request.almacen_id if request.almacen_id is not None else config_actual.get("almacen_id", "")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:448:    if nuevo_almacen:
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:449:        almacenes = await repo.listar_almacenes(nueva_unidad)
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:450:        almacen_ids = [a["id"] for a in almacenes if a.get("id")]
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:451:        if nuevo_almacen not in almacen_ids:
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:464:        (request.almacen_id is not None and request.almacen_id != config_actual.get("almacen_id", "")) or
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:472:            "almacen_id": nuevo_almacen,
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:487:            almacen_id=request.almacen_id,
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:499:    if request.almacen_id is not None:
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:500:        cambios["nuevo_almacen"] = request.almacen_id or "(todos)"
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:530:    Advertencia: Los inventarios futuros de esta combinación
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:558:            "almacen": config_actual.get("almacen_nombre") or "(todos)",
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:572:    almacen_id: str = Query(""),
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:578:    Útil para verificar la configuración antes de que un inventario real
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:609:    responsable = await repo.resolver_responsable(server_id, almacen_id)
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:619:                "regla_aplicada": "específica" if almacen_id else "general"
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:633:# ENDPOINT DE SINCRONIZACIÓN DE ALMACENES (Admin only)
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:636:@router.post("/almacenes/sincronizar/{unidad_negocio_id}")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:637:async def sincronizar_almacenes(
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:642:    Sincroniza almacenes desde el servidor SQL al catálogo local.
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:656:        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede sincronizar almacenes")
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:664:    from ..services.almacenes_sync_service import sincronizar_almacenes_desde_origen
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:666:    result = await sincronizar_almacenes_desde_origen(
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:684:        entidad="almacenes_catalogo",
/app/backend/modules/inventarios/service.py:2:EDARSA HUB - Inventarios Service
/app/backend/modules/inventarios/service.py:4:Lógica de negocio de inventarios.
/app/backend/modules/inventarios/service.py:7:class InventariosService:
/app/backend/modules/inventarios/__init__.py:1:# EDARSA HUB - Módulo de Inventarios
/app/backend/modules/inventarios/__init__.py:2:# Control de inventarios, movimientos y existencias
/app/backend/modules/inventarios/repository.py:2:EDARSA HUB - Inventarios Repository
/app/backend/modules/inventarios/repository.py:4:Acceso a datos de inventarios desde SQL Server.
/app/backend/modules/inventarios/repository.py:9:- Datos sincronizados en tabla Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:17:def get_inventarios_fisicos(server_id: str = None, almacen: str = None, 
/app/backend/modules/inventarios/repository.py:20:    Obtiene inventarios físicos desde la tabla sincronizada de EDARSAHUB.
/app/backend/modules/inventarios/repository.py:21:    Reemplaza: mongo_db.inventarios.find(filtro)
/app/backend/modules/inventarios/repository.py:24:        SELECT folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
/app/backend/modules/inventarios/repository.py:26:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:35:    if almacen:
/app/backend/modules/inventarios/repository.py:36:        query += " AND almacen = %s"
/app/backend/modules/inventarios/repository.py:37:        params.append(almacen)
/app/backend/modules/inventarios/repository.py:49:def get_inventario_by_folio(folio: str, server_id: str = None) -> Optional[Dict]:
/app/backend/modules/inventarios/repository.py:51:    Obtiene un inventario físico específico por folio.
/app/backend/modules/inventarios/repository.py:54:        SELECT folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
/app/backend/modules/inventarios/repository.py:56:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:68:def get_inventarios_count_by_server(server_id: str) -> int:
/app/backend/modules/inventarios/repository.py:70:    Cuenta inventarios por servidor.
/app/backend/modules/inventarios/repository.py:74:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:81:class InventariosRepository:
/app/backend/modules/inventarios/repository.py:86:        return get_inventarios_fisicos(server_id=server_id, **filters)
/app/backend/modules/inventarios/repository.py:90:        return get_inventario_by_folio(folio, server_id)
/app/backend/modules/inventarios/repository.py:94:    'InventariosRepository',
/app/backend/modules/inventarios/repository.py:95:    'get_inventarios_fisicos',
/app/backend/modules/inventarios/repository.py:96:    'get_inventario_by_folio',
/app/backend/modules/inventarios/repository.py:97:    'get_inventarios_count_by_server',
/app/backend/modules/inventarios/routes.py:2:EDARSA HUB - Inventarios Routes
/app/backend/modules/inventarios/routes.py:4:Endpoints del módulo de inventarios.
/app/backend/modules/inventarios/routes.py:9:router = APIRouter(prefix="/inventarios", tags=["Inventarios"])
/app/backend/modules/inventarios/schemas.py:2:EDARSA HUB - Inventarios Schemas
/app/backend/modules/inventarios/schemas.py:4:Modelos Pydantic para inventarios.
/app/backend/modules/catalogos/__init__.py:17:- Inventarios (Tipos movimiento, etc.)
/app/backend/modules/catalogos/schemas.py:65:            {"tabla": "Compras_PedidosEstatus", "nombre": "Estatus de Pedidos", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:75:    "inventarios": {
/app/backend/modules/catalogos/schemas.py:76:        "nombre": "Inventarios",
/app/backend/modules/catalogos/schemas.py:77:        "descripcion": "Catálogos del módulo de Inventarios",
/app/backend/modules/catalogos/schemas.py:80:            {"tabla": "Inventario_TipoMovimiento", "nombre": "Tipos de Movimiento", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:120:            {"tabla": "Venta_PedidosEstatus", "nombre": "Estatus de Pedidos", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:320:    "Compras_PedidosEstatus": {
/app/backend/modules/catalogos/schemas.py:377:    # === INVENTARIOS ===
/app/backend/modules/catalogos/schemas.py:378:    "Inventario_TipoMovimiento": {
/app/backend/modules/catalogos/schemas.py:532:    "Venta_PedidosEstatus": {
/app/backend/modules/automatizacion/__init__.py:3:Módulo: Automatización de Análisis de Inventarios
/app/backend/modules/automatizacion/feature_flags.py:3:Feature Flags - Automatización de Análisis de Inventarios
/app/backend/modules/automatizacion/feature_flags.py:16:    "AUTOMATIZACION_INVENTARIOS_ENABLED": False,
/app/backend/modules/automatizacion/feature_flags.py:69:        bool: True si AUTOMATIZACION_INVENTARIOS_ENABLED está en True
/app/backend/modules/automatizacion/feature_flags.py:74:    return FEATURE_FLAGS.get("AUTOMATIZACION_INVENTARIOS_ENABLED", False)
/app/backend/modules/automatizacion/queries_mpro.py:4:# Constantes SQL para detección de inventarios válidos en MPRO
/app/backend/modules/automatizacion/queries_mpro.py:9:# - Inventario inicial: Último inventario válido del MES ANTERIOR
/app/backend/modules/automatizacion/queries_mpro.py:11:# - Clave incluye: almacen + sucursal + comentario + folio + fecha + estado
/app/backend/modules/automatizacion/queries_mpro.py:19:# QUERY: Último inventario válido por almacén/sucursal/comentario
/app/backend/modules/automatizacion/queries_mpro.py:21:QUERY_ULTIMO_INVENTARIO_VALIDO = """
/app/backend/modules/automatizacion/queries_mpro.py:22:WITH inventarios_validos AS (
/app/backend/modules/automatizacion/queries_mpro.py:26:        F.Al_Cve_Almacen AS almacen_id,
/app/backend/modules/automatizacion/queries_mpro.py:31:            PARTITION BY F.Al_Cve_Almacen, F.Sc_Cve_Sucursal, F.Fi_Comentario, CONVERT(date, F.Fi_Fecha), F.Es_Cve_Estado
/app/backend/modules/automatizacion/queries_mpro.py:35:    WHERE F.Al_Cve_Almacen = :almacen_id
/app/backend/modules/automatizacion/queries_mpro.py:41:SELECT TOP 1 folio, fecha, almacen_id, sucursal_id, comentario, estado
/app/backend/modules/automatizacion/queries_mpro.py:42:FROM inventarios_validos
/app/backend/modules/automatizacion/queries_mpro.py:48:# QUERY: Último inventario válido del mes anterior (inventario inicial)
/app/backend/modules/automatizacion/queries_mpro.py:50:QUERY_ULTIMO_INVENTARIO_MES_ANTERIOR = """
/app/backend/modules/automatizacion/queries_mpro.py:51:WITH inventarios_validos AS (
/app/backend/modules/automatizacion/queries_mpro.py:55:        F.Al_Cve_Almacen AS almacen_id,
/app/backend/modules/automatizacion/queries_mpro.py:60:            PARTITION BY F.Al_Cve_Almacen, F.Sc_Cve_Sucursal, F.Fi_Comentario, CONVERT(date, F.Fi_Fecha)
/app/backend/modules/automatizacion/queries_mpro.py:67:    WHERE F.Al_Cve_Almacen = :almacen_id
/app/backend/modules/automatizacion/queries_mpro.py:75:SELECT TOP 1 folio, fecha, almacen_id, sucursal_id, comentario, estado
/app/backend/modules/automatizacion/queries_mpro.py:76:FROM inventarios_validos
/app/backend/modules/automatizacion/queries_mpro.py:82:# QUERY: Listar inventarios válidos recientes por sucursal (para detección)
/app/backend/modules/automatizacion/queries_mpro.py:84:QUERY_INVENTARIOS_VALIDOS_SUCURSAL = """
/app/backend/modules/automatizacion/queries_mpro.py:88:    F.Al_Cve_Almacen AS almacen_id,
/app/backend/modules/automatizacion/queries_mpro.py:89:    A.Al_Descripcion AS almacen_nombre,
/app/backend/modules/automatizacion/queries_mpro.py:95:INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
/app/backend/modules/automatizacion/queries_mpro.py:102:    F.Al_Cve_Almacen, A.Al_Descripcion,
/app/backend/modules/automatizacion/queries_mpro.py:120:# QUERY: Listar almacenes por sucursal
/app/backend/modules/automatizacion/queries_mpro.py:122:QUERY_ALMACENES_SUCURSAL = """
/app/backend/modules/automatizacion/queries_mpro.py:124:    Al_Cve_Almacen AS almacen_id,
/app/backend/modules/automatizacion/queries_mpro.py:125:    Al_Descripcion AS almacen_nombre,
/app/backend/modules/automatizacion/queries_mpro.py:127:FROM Almacen
/app/backend/modules/automatizacion/queries_soft.py:4:# Constantes SQL para detección de inventarios válidos en SoftRestaurant
/app/backend/modules/automatizacion/queries_soft.py:7:# - Inventario válido: cancelado = 0
/app/backend/modules/automatizacion/queries_soft.py:8:# - Inventario inicial: Primer inventario válido del MES del inventario final
/app/backend/modules/automatizacion/queries_soft.py:13:# QUERY: Último inventario válido (inventario final detectado)
/app/backend/modules/automatizacion/queries_soft.py:15:QUERY_ULTIMO_INVENTARIO_VALIDO = """
/app/backend/modules/automatizacion/queries_soft.py:16:WITH inventarios_validos AS (
/app/backend/modules/automatizacion/queries_soft.py:20:        i.idalmacen1,
/app/backend/modules/automatizacion/queries_soft.py:22:            PARTITION BY i.idalmacen1, CONVERT(date, i.fecha)
/app/backend/modules/automatizacion/queries_soft.py:25:    FROM invfisico i
/app/backend/modules/automatizacion/queries_soft.py:26:    WHERE i.idalmacen1 = :almacen_id
/app/backend/modules/automatizacion/queries_soft.py:32:    idalmacen1 AS almacen_id
/app/backend/modules/automatizacion/queries_soft.py:33:FROM inventarios_validos
/app/backend/modules/automatizacion/queries_soft.py:39:# QUERY: Primer inventario válido del mes (inventario inicial)
/app/backend/modules/automatizacion/queries_soft.py:41:QUERY_PRIMER_INVENTARIO_MES = """
/app/backend/modules/automatizacion/queries_soft.py:42:WITH inventarios_validos AS (
/app/backend/modules/automatizacion/queries_soft.py:46:        i.idalmacen1,
/app/backend/modules/automatizacion/queries_soft.py:48:            PARTITION BY i.idalmacen1, CONVERT(date, i.fecha)
/app/backend/modules/automatizacion/queries_soft.py:51:    FROM invfisico i
/app/backend/modules/automatizacion/queries_soft.py:52:    WHERE i.idalmacen1 = :almacen_id
/app/backend/modules/automatizacion/queries_soft.py:60:    idalmacen1 AS almacen_id
/app/backend/modules/automatizacion/queries_soft.py:61:FROM inventarios_validos
/app/backend/modules/automatizacion/queries_soft.py:67:# QUERY: Listar todos los inventarios válidos de un almacén (para detección)
/app/backend/modules/automatizacion/queries_soft.py:69:QUERY_INVENTARIOS_VALIDOS_ALMACEN = """
/app/backend/modules/automatizacion/queries_soft.py:70:WITH inventarios_validos AS (
/app/backend/modules/automatizacion/queries_soft.py:74:        i.idalmacen1,
/app/backend/modules/automatizacion/queries_soft.py:76:            PARTITION BY i.idalmacen1, CONVERT(date, i.fecha)
/app/backend/modules/automatizacion/queries_soft.py:79:    FROM invfisico i
/app/backend/modules/automatizacion/queries_soft.py:80:    WHERE i.idalmacen1 = :almacen_id
/app/backend/modules/automatizacion/queries_soft.py:86:    idalmacen1 AS almacen_id
/app/backend/modules/automatizacion/queries_soft.py:87:FROM inventarios_validos
/app/backend/modules/automatizacion/queries_soft.py:93:# QUERY: Listar almacenes disponibles
/app/backend/modules/automatizacion/queries_soft.py:96:QUERY_ALMACENES = """
/app/backend/modules/automatizacion/queries_soft.py:98:    idalmacen AS almacen_id,
/app/backend/modules/automatizacion/queries_soft.py:99:    nombre AS almacen_nombre
/app/backend/modules/automatizacion/queries_soft.py:100:FROM almacen
/app/backend/modules/automatizacion/repository.py:46:    Lee configuración activa de automatizacion_inventarios_config.
/app/backend/modules/automatizacion/repository.py:61:            almacen_id,
/app/backend/modules/automatizacion/repository.py:67:        FROM automatizacion_inventarios_config
/app/backend/modules/automatizacion/repository.py:74:    query += " ORDER BY server_id, sucursal_id, almacen_id"
/app/backend/modules/automatizacion/repository.py:114:            almacen_id,
/app/backend/modules/automatizacion/repository.py:116:            folio_inventario,
/app/backend/modules/automatizacion/repository.py:117:            fecha_inventario,
/app/backend/modules/automatizacion/repository.py:118:            estado_inventario_origen,
/app/backend/modules/automatizacion/repository.py:122:        FROM automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/repository.py:125:        ORDER BY fecha_inventario DESC, folio_inventario DESC
/app/backend/modules/automatizacion/repository.py:142:    almacen_id: str,
/app/backend/modules/automatizacion/repository.py:144:    folio_inventario: str,
/app/backend/modules/automatizacion/repository.py:145:    fecha_inventario: date,
/app/backend/modules/automatizacion/repository.py:146:    estado_inventario_origen: Optional[str]
/app/backend/modules/automatizacion/repository.py:158:        almacen_id or "",
/app/backend/modules/automatizacion/repository.py:160:        folio_inventario or "",
/app/backend/modules/automatizacion/repository.py:161:        str(fecha_inventario) if fecha_inventario else "",
/app/backend/modules/automatizacion/repository.py:162:        estado_inventario_origen or ""
/app/backend/modules/automatizacion/repository.py:171:    almacen_id: str,
/app/backend/modules/automatizacion/repository.py:173:    folio_inventario: str,
/app/backend/modules/automatizacion/repository.py:174:    fecha_inventario: date,
/app/backend/modules/automatizacion/repository.py:175:    estado_inventario_origen: Optional[str]
/app/backend/modules/automatizacion/repository.py:178:    Verifica si un inventario ya fue procesado comparando la clave CAB-003.
/app/backend/modules/automatizacion/repository.py:184:        sistema_origen, server_id, sucursal_id, almacen_id,
/app/backend/modules/automatizacion/repository.py:185:        comentario, folio_inventario, fecha_inventario, estado_inventario_origen
/app/backend/modules/automatizacion/repository.py:193:            folio.get('almacen_id'),
/app/backend/modules/automatizacion/repository.py:195:            folio.get('folio_inventario'),
/app/backend/modules/automatizacion/repository.py:196:            folio.get('fecha_inventario'),
/app/backend/modules/automatizacion/repository.py:197:            folio.get('estado_inventario_origen')
/app/backend/modules/automatizacion/repository.py:223:    almacen_id: str,
/app/backend/modules/automatizacion/repository.py:225:    folio_inventario: str,
/app/backend/modules/automatizacion/repository.py:226:    fecha_inventario: str,
/app/backend/modules/automatizacion/repository.py:227:    estado_inventario_origen: Optional[str]
/app/backend/modules/automatizacion/repository.py:236:        almacen_id or "",
/app/backend/modules/automatizacion/repository.py:238:        folio_inventario or "",
/app/backend/modules/automatizacion/repository.py:239:        str(fecha_inventario) if fecha_inventario else "",
/app/backend/modules/automatizacion/repository.py:240:        estado_inventario_origen or ""
/app/backend/modules/automatizacion/repository.py:255:    almacen_id: str,
/app/backend/modules/automatizacion/repository.py:257:    folio_inventario: str,
/app/backend/modules/automatizacion/repository.py:258:    fecha_inventario: str,
/app/backend/modules/automatizacion/repository.py:259:    estado_inventario_origen: Optional[str]
/app/backend/modules/automatizacion/repository.py:275:            almacen_id,
/app/backend/modules/automatizacion/repository.py:277:            folio_inventario,
/app/backend/modules/automatizacion/repository.py:278:            fecha_inventario,
/app/backend/modules/automatizacion/repository.py:279:            estado_inventario_origen,
/app/backend/modules/automatizacion/repository.py:283:        FROM automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/repository.py:287:          AND almacen_id = %s
/app/backend/modules/automatizacion/repository.py:289:          AND folio_inventario = %s
/app/backend/modules/automatizacion/repository.py:290:          AND fecha_inventario = %s
/app/backend/modules/automatizacion/repository.py:291:          AND ISNULL(estado_inventario_origen, '') = ISNULL(%s, '')
/app/backend/modules/automatizacion/repository.py:298:        almacen_id,
/app/backend/modules/automatizacion/repository.py:300:        folio_inventario,
/app/backend/modules/automatizacion/repository.py:301:        fecha_inventario,
/app/backend/modules/automatizacion/repository.py:302:        estado_inventario_origen or ''
/app/backend/modules/automatizacion/repository.py:384:    almacen_id: str,
/app/backend/modules/automatizacion/repository.py:386:    folio_inventario: str,
/app/backend/modules/automatizacion/repository.py:387:    fecha_inventario: str,
/app/backend/modules/automatizacion/repository.py:388:    estado_inventario_origen: Optional[str],
/app/backend/modules/automatizacion/repository.py:392:    Inserta 1 registro en automatizacion_inventarios_folios_procesados.
/app/backend/modules/automatizacion/repository.py:403:        sistema_origen, server_id, sucursal_id, almacen_id,
/app/backend/modules/automatizacion/repository.py:404:        comentario, folio_inventario, fecha_inventario, estado_inventario_origen
/app/backend/modules/automatizacion/repository.py:409:        INSERT INTO automatizacion_inventarios_folios_procesados (
/app/backend/modules/automatizacion/repository.py:414:            almacen_id,
/app/backend/modules/automatizacion/repository.py:416:            folio_inventario,
/app/backend/modules/automatizacion/repository.py:417:            fecha_inventario,
/app/backend/modules/automatizacion/repository.py:418:            estado_inventario_origen,
/app/backend/modules/automatizacion/repository.py:440:        almacen_id,
/app/backend/modules/automatizacion/repository.py:442:        folio_inventario,
/app/backend/modules/automatizacion/repository.py:443:        fecha_inventario,
/app/backend/modules/automatizacion/repository.py:444:        estado_inventario_origen,  # Puede ser NULL
/app/backend/modules/automatizacion/repository.py:496:        FROM automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/repository.py:501:        DELETE FROM automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/repository.py:543:        FROM automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/repository.py:591:    Actualiza la marca de agua en automatizacion_inventarios_ultimo_folio_conocido.
/app/backend/modules/automatizacion/repository.py:624:            id, server_id, sucursal_id, almacen_id,
/app/backend/modules/automatizacion/repository.py:628:        FROM automatizacion_inventarios_config
/app/backend/modules/automatizacion/repository.py:678:    almacen_id: str
/app/backend/modules/automatizacion/repository.py:687:        SELECT folio_inventario, fecha_proceso, estado
/app/backend/modules/automatizacion/repository.py:688:        FROM automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/repository.py:691:          AND almacen_id = '{almacen_id}'
/app/backend/modules/automatizacion/schemas.py:3:Schemas Pydantic - Automatización de Análisis de Inventarios
/app/backend/modules/automatizacion/schemas.py:25:NivelOrigen = Literal["SERVER", "SUCURSAL", "ALMACEN"]
/app/backend/modules/automatizacion/schemas.py:34:# SCHEMA: automatizacion_inventarios_config
/app/backend/modules/automatizacion/schemas.py:41:    almacen_id: Optional[str] = Field(None, max_length=20)
/app/backend/modules/automatizacion/schemas.py:66:# SCHEMA: automatizacion_inventarios_destinatarios
/app/backend/modules/automatizacion/schemas.py:73:    almacen_id: Optional[str] = Field(None, max_length=20)
/app/backend/modules/automatizacion/schemas.py:101:# SCHEMA: automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/schemas.py:109:    (sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario, fecha_inventario)
/app/backend/modules/automatizacion/schemas.py:114:    almacen_id: str = Field(..., max_length=20)
/app/backend/modules/automatizacion/schemas.py:115:    folio_inventario: str = Field(..., max_length=50)
/app/backend/modules/automatizacion/schemas.py:116:    fecha_inventario: date
/app/backend/modules/automatizacion/schemas.py:143:# SCHEMA: automatizacion_inventarios_ejecuciones
/app/backend/modules/automatizacion/schemas.py:174:# SCHEMA: automatizacion_inventarios_envios
/app/backend/modules/automatizacion/schemas.py:205:# SCHEMA: automatizacion_inventarios_ultimo_folio_conocido
/app/backend/modules/automatizacion/schemas.py:213:    (sistema_origen, server_id, sucursal_id, almacen_id)
/app/backend/modules/automatizacion/schemas.py:218:    almacen_id: str = Field(..., max_length=20)
/app/backend/modules/edge/motor_reglas_comerciales.py:45:        Examina el estado de la bodega en caché local. Si el inventario toca el mínimo,
/app/backend/modules/edge/motor_reglas_comerciales.py:78:        Decide quirúrgicamente qué inventario de la barra lateral (40%) debe priorizarse.
/app/backend/modules/edge/servidor_local_contingencia.py:17:    las terminales para unificar el inventario y la contabilidad local[cite: 237, 285].
/app/backend/modules/edge/comandero_local_core.py:114:        Escribe la transacción directamente en el almacenamiento físico local.
/app/backend/modules/edge/motor_inventario_parametrico.py:1:# backend/modules/edge/motor_inventario_parametrico.py
/app/backend/modules/edge/motor_inventario_parametrico.py:7:class MotorInventarioParametrico:
/app/backend/modules/edge/motor_inventario_parametrico.py:14:        Crea la tabla que almacena las preferencias operativas del cliente
/app/backend/modules/edge/motor_inventario_parametrico.py:20:                CREATE TABLE IF NOT EXISTS configuracion_inventario_unidad (
/app/backend/modules/edge/motor_inventario_parametrico.py:22:                    control_inventario_activo INTEGER DEFAULT 0, -- 0 = Falso (Venta Libre), 1 = Verdadero
/app/backend/modules/edge/motor_inventario_parametrico.py:34:        Interroga primero la preferencia del cliente. Si el control de inventario
/app/backend/modules/edge/motor_inventario_parametrico.py:38:        query_config = "SELECT * FROM configuracion_inventario_unidad WHERE unidad_negocio = ?"
/app/backend/modules/edge/motor_inventario_parametrico.py:46:        if not config or config["control_inventario_activo"] == 0:
/app/backend/modules/edge/motor_inventario_parametrico.py:53:        # 2. Si el inventario SÍ está activo, evaluar los insumos de la receta
/app/backend/modules/auth/service.py:348:    - Usuario_AlmacenesAsignacion
/app/backend/modules/auth/service.py:459:        # 3. ACTUALIZAR ALMACENES
/app/backend/modules/auth/service.py:465:                UPDATE Usuario_AlmacenesAsignacion 
/app/backend/modules/auth/service.py:472:            for server_uuid, almacenes in allowed_warehouses.items():
/app/backend/modules/auth/service.py:480:                    for alm_codigo in (almacenes or []):
/app/backend/modules/auth/service.py:483:                                INSERT INTO Usuario_AlmacenesAsignacion 
/app/backend/modules/auth/service.py:484:                                (UsuarioID, ServidorID, AlmacenCodigo, LegacyMongoValue, Activo, FechaCreacion, Observaciones)
/app/backend/modules/auth/service.py:488:                    logging.warning(f"[RBAC-SCOPE-E] Servidor no encontrado para almacenes: {server_uuid}")
/app/backend/modules/auth/password_reset.py:74:    """Hashear token con SHA-256 para almacenamiento seguro"""
/app/backend/modules/auth/repository.py:151:        # 3. Almacenes asignados por usuario/servidor
/app/backend/modules/auth/repository.py:156:                a.AlmacenCodigo
/app/backend/modules/auth/repository.py:158:            JOIN Usuario_AlmacenesAsignacion a ON u.UsuarioID = a.UsuarioID AND a.Activo = 1
/app/backend/modules/auth/routes.py:465:    - Almacenes efectivos
/app/backend/modules/auth/schemas.py:47:    sec_roles_alcance: Dict[str, Dict] = {}  # rol_codigo -> {tipo, empresa_id, unidades_ids, sucursales_ids, almacenes_ids}
/app/backend/modules/auth/schemas.py:115:    {"id": "inventarios", "nombre": "Inventarios", "descripcion": "Análisis de inventarios, reportes"},
/app/backend/modules/auth/schemas.py:116:    {"id": "dashboard_inventarios", "nombre": "Dashboard Inventarios", "descripcion": "Gráficas de diferencias de inventario"},
/app/backend/modules/auth/schemas.py:140:        "permisos": ["tablero_ejecutivo", "comercial", "compras", "inventarios", "dashboard_inventarios", "catalogo_sql", "alertas"],
/app/backend/modules/auth/schemas.py:146:        "permisos": ["comercial", "compras", "inventarios", "dashboard_inventarios"],
/app/backend/modules/tablajeria/ordenes_service.py:144:                    OrigenOrden, AfectaInventario, Observaciones,
/app/backend/modules/tablajeria/ordenes_service.py:218:                    not det['EsMerma']  # Mermas no generan movimiento de inventario directo
/app/backend/modules/tablajeria/fase6_service.py:2:EDARSA HUB - Tablajería Fase 6: Inventarios, Costeo y Contabilidad
/app/backend/modules/tablajeria/fase6_service.py:4:Servicio que gestiona la afectación de inventarios, costeo de producción
/app/backend/modules/tablajeria/fase6_service.py:27:    AJUSTE_INVENTARIO = "AJUSTE_INVENTARIO"
/app/backend/modules/tablajeria/fase6_service.py:46:    cuenta_almacen_insumos: str = "1151-001"
/app/backend/modules/tablajeria/fase6_service.py:47:    cuenta_almacen_productos: str = "1152-001"
/app/backend/modules/tablajeria/fase6_service.py:54:    afectar_inventario_automatico: bool = True
/app/backend/modules/tablajeria/fase6_service.py:60:    Servicio de Fase 6: Inventarios, Costeo y Contabilidad.
/app/backend/modules/tablajeria/fase6_service.py:63:    - Afectación de inventarios al cerrar órdenes
/app/backend/modules/tablajeria/fase6_service.py:115:                    cuenta_almacen_insumos=row.get('CuentaAlmacenInsumos') or "1151-001",
/app/backend/modules/tablajeria/fase6_service.py:116:                    cuenta_almacen_productos=row.get('CuentaAlmacenProductos') or "1152-001",
/app/backend/modules/tablajeria/fase6_service.py:123:                    afectar_inventario_automatico=bool(row.get('AfectarInventarioAutomatico', True)),
/app/backend/modules/tablajeria/fase6_service.py:152:                        CuentaAlmacenInsumos = %s,
/app/backend/modules/tablajeria/fase6_service.py:153:                        CuentaAlmacenProductos = %s,
/app/backend/modules/tablajeria/fase6_service.py:160:                        AfectarInventarioAutomatico = %s,
/app/backend/modules/tablajeria/fase6_service.py:165:                    config.cuenta_almacen_insumos,
/app/backend/modules/tablajeria/fase6_service.py:166:                    config.cuenta_almacen_productos,
/app/backend/modules/tablajeria/fase6_service.py:173:                    config.afectar_inventario_automatico,
/app/backend/modules/tablajeria/fase6_service.py:181:                        EmpresaID, CuentaAlmacenInsumos, CuentaAlmacenProductos,
/app/backend/modules/tablajeria/fase6_service.py:185:                        AfectarInventarioAutomatico, ToleranciaVariacionPorcentaje
/app/backend/modules/tablajeria/fase6_service.py:189:                    config.cuenta_almacen_insumos,
/app/backend/modules/tablajeria/fase6_service.py:190:                    config.cuenta_almacen_productos,
/app/backend/modules/tablajeria/fase6_service.py:197:                    config.afectar_inventario_automatico,
/app/backend/modules/tablajeria/fase6_service.py:218:    # AFECTACIÓN DE INVENTARIOS
/app/backend/modules/tablajeria/fase6_service.py:221:    def afectar_inventario_orden(
/app/backend/modules/tablajeria/fase6_service.py:227:        Afecta el inventario basado en una orden cerrada.
/app/backend/modules/tablajeria/fase6_service.py:257:                raise ValueError(f"Solo se puede afectar inventario de órdenes cerradas. Estatus: {orden['EstatusOrden']}")
/app/backend/modules/tablajeria/fase6_service.py:261:            if not config.afectar_inventario_automatico:
/app/backend/modules/tablajeria/fase6_service.py:272:                    INSERT INTO Tablajeria_MovimientosInventario (
/app/backend/modules/tablajeria/fase6_service.py:275:                        AlmacenOrigenID, Cantidad, LoteProducto,
/app/backend/modules/tablajeria/fase6_service.py:306:                    INSERT INTO Tablajeria_MovimientosInventario (
/app/backend/modules/tablajeria/fase6_service.py:309:                        AlmacenDestinoID, Cantidad,
/app/backend/modules/tablajeria/fase6_service.py:329:                    INSERT INTO Tablajeria_MovimientosInventario (
/app/backend/modules/tablajeria/fase6_service.py:332:                        AlmacenOrigenID, Cantidad,
/app/backend/modules/tablajeria/fase6_service.py:351:                    AfectaInventario = 1,
/app/backend/modules/tablajeria/fase6_service.py:352:                    MovimientoInventarioGenerado = 1,
/app/backend/modules/tablajeria/fase6_service.py:359:            logger.info(f"[FASE6] Inventario afectado para orden {orden['FolioOrden']}: {len(movimientos)} movimientos")
/app/backend/modules/tablajeria/fase6_service.py:370:            logger.error(f"[FASE6] Error afectando inventario: {e}")
/app/backend/modules/tablajeria/fase6_service.py:655:                config.cuenta_almacen_productos, "Almacén Productos Terminados",
/app/backend/modules/tablajeria/fase6_service.py:660:                "linea": linea, "cuenta": config.cuenta_almacen_productos,
/app/backend/modules/tablajeria/fase6_service.py:697:                config.cuenta_almacen_insumos, "Almacén Materia Prima",
/app/backend/modules/tablajeria/fase6_service.py:702:                "linea": linea, "cuenta": config.cuenta_almacen_insumos,
/app/backend/modules/tablajeria/fase6_service.py:741:        1. Afectar inventarios
/app/backend/modules/tablajeria/fase6_service.py:750:            "inventario": None,
/app/backend/modules/tablajeria/fase6_service.py:757:            # 1. Afectar inventario
/app/backend/modules/tablajeria/fase6_service.py:759:                resultado["inventario"] = self.afectar_inventario_orden(orden_id, usuario_id)
/app/backend/modules/tablajeria/fase6_service.py:761:                resultado["errores"].append(f"Error inventario: {str(e)}")
/app/backend/modules/tablajeria/fase6_service.py:762:                logger.error(f"[FASE6] Error en inventario: {e}")
/app/backend/modules/tablajeria/routes.py:649:    1. Afectación de inventarios
/app/backend/modules/tablajeria/routes.py:690:                        mensaje += " | Fase 6 completada: Inventario, Costeo y Póliza procesados"
/app/backend/modules/tablajeria/routes.py:890:# FASE 6: INVENTARIOS, COSTEO Y CONTABILIDAD
/app/backend/modules/tablajeria/routes.py:908:    Procesa el cierre completo de Fase 6: Inventarios, Costeo y Contabilidad.
/app/backend/modules/tablajeria/routes.py:942:@router.post("/ordenes/{orden_id}/fase6/afectar-inventario")
/app/backend/modules/tablajeria/routes.py:943:async def afectar_inventario(
/app/backend/modules/tablajeria/routes.py:947:    """Afecta el inventario de una orden cerrada."""
/app/backend/modules/tablajeria/routes.py:950:        resultado = service.afectar_inventario_orden(orden_id, current_user.get('id'))
/app/backend/modules/tablajeria/routes.py:955:        logger.error(f"[FASE6] Error afectando inventario: {e}")
/app/backend/modules/tablajeria/routes.py:1025:                "almacen_insumos": config.cuenta_almacen_insumos,
/app/backend/modules/tablajeria/routes.py:1026:                "almacen_productos": config.cuenta_almacen_productos,
/app/backend/modules/tablajeria/routes.py:1035:                "afectar_inventario_automatico": config.afectar_inventario_automatico,
/app/backend/modules/tablajeria/routes.py:1056:            cuenta_almacen_insumos=config.get('almacen_insumos', '1151-001'),
/app/backend/modules/tablajeria/routes.py:1057:            cuenta_almacen_productos=config.get('almacen_productos', '1152-001'),
/app/backend/modules/tablajeria/routes.py:1064:            afectar_inventario_automatico=config.get('afectar_inventario_automatico', True),
/app/backend/modules/universal_query/routes.py:9:- NO asume dominio (no productos, no ventas, no inventarios)
/app/backend/modules/universal_query/routes.py:242:    - NO asume dominio (no productos, no ventas, no inventarios)
/app/backend/modules/sync_recetas/sync_recetas.py:636:    - MPRO almacena impuestos en Impuesto_Grupo_Impuesto (relación N:M con Producto)
/app/backend/modules/crm/service.py:62:            "Pedidos",      # Venta_Pedidos
/app/backend/modules/crm/comercial_routes.py:737:# PEDIDOS DE VENTA
/app/backend/modules/crm/comercial_routes.py:740:class PedidoCreate(BaseModel):
/app/backend/modules/crm/comercial_routes.py:762:@router.get("/pedidos-venta")
/app/backend/modules/crm/comercial_routes.py:763:async def listar_pedidos(
/app/backend/modules/crm/comercial_routes.py:773:    """Lista pedidos de venta"""
/app/backend/modules/crm/comercial_routes.py:776:        return service.listar_pedidos(
/app/backend/modules/crm/comercial_routes.py:786:        logger.error(f"[CRM] Error listando pedidos: {e}")
/app/backend/modules/crm/comercial_routes.py:790:@router.get("/pedidos-venta/{pedido_id}")
/app/backend/modules/crm/comercial_routes.py:791:async def obtener_pedido(
/app/backend/modules/crm/comercial_routes.py:792:    pedido_id: int,
/app/backend/modules/crm/comercial_routes.py:795:    """Obtiene detalle de un pedido"""
/app/backend/modules/crm/comercial_routes.py:798:        ped = service.obtener_pedido(pedido_id)
/app/backend/modules/crm/comercial_routes.py:800:            raise HTTPException(status_code=404, detail="Pedido no encontrado")
/app/backend/modules/crm/comercial_routes.py:805:        logger.error(f"[CRM] Error obteniendo pedido: {e}")
/app/backend/modules/crm/comercial_routes.py:809:@router.post("/pedidos-venta")
/app/backend/modules/crm/comercial_routes.py:810:async def crear_pedido(
/app/backend/modules/crm/comercial_routes.py:811:    data: PedidoCreate,
/app/backend/modules/crm/comercial_routes.py:814:    """Crea un pedido de venta"""
/app/backend/modules/crm/comercial_routes.py:819:        result = service.crear_pedido(data.dict(), usuario_id)
/app/backend/modules/crm/comercial_routes.py:823:            "mensaje": f"Pedido {result['folio_pedido']} creado",
/app/backend/modules/crm/comercial_routes.py:829:        logger.error(f"[CRM] Error creando pedido: {e}")
/app/backend/modules/crm/comercial_routes.py:833:@router.post("/pedidos-venta/{pedido_id}/confirmar")
/app/backend/modules/crm/comercial_routes.py:834:async def confirmar_pedido(
/app/backend/modules/crm/comercial_routes.py:835:    pedido_id: int,
/app/backend/modules/crm/comercial_routes.py:838:    """Confirma un pedido"""
/app/backend/modules/crm/comercial_routes.py:843:        result = service.confirmar_pedido(pedido_id, usuario_id)
/app/backend/modules/crm/comercial_routes.py:845:        return {"success": True, "mensaje": "Pedido confirmado", **result}
/app/backend/modules/crm/comercial_routes.py:849:        logger.error(f"[CRM] Error confirmando pedido: {e}")
/app/backend/modules/crm/comercial_routes.py:861:    almacen_id: Optional[int] = None
/app/backend/modules/crm/comercial_routes.py:862:    pedido_id: Optional[int] = None
/app/backend/modules/crm/vtiger_routes.py:59:# ==================== ALMACENAMIENTO EN MEMORIA ====================
/app/backend/modules/crm/vtiger_routes.py:380:            {"code": "SalesOrder", "name": "Pedidos", "description": "Órdenes de venta"},
/app/backend/modules/crm/comercial_service.py:12:- Wrapper Pedidos
/app/backend/modules/crm/comercial_service.py:874:                    c.PedidoID, c.Activo, c.CreatedAt,
/app/backend/modules/crm/comercial_service.py:1113:    # PEDIDOS (WRAPPER Venta_Pedidos)
/app/backend/modules/crm/comercial_service.py:1116:    def listar_pedidos(
/app/backend/modules/crm/comercial_service.py:1126:        """Lista pedidos de venta"""
/app/backend/modules/crm/comercial_service.py:1133:                    p.PedidoID, p.Serie, p.FolioPedido, p.FechaPedido,
/app/backend/modules/crm/comercial_service.py:1135:                    p.MonedaID, p.TipoCambio, p.EstatusPedidoID,
/app/backend/modules/crm/comercial_service.py:1140:                FROM Venta_Pedidos p
/app/backend/modules/crm/comercial_service.py:1153:                query += " AND p.EstatusPedidoID = %s"
/app/backend/modules/crm/comercial_service.py:1156:                query += " AND p.FechaPedido >= %s"
/app/backend/modules/crm/comercial_service.py:1159:                query += " AND p.FechaPedido <= %s"
/app/backend/modules/crm/comercial_service.py:1162:            query += " ORDER BY p.FechaPedido DESC"
/app/backend/modules/crm/comercial_service.py:1167:            pedidos = []
/app/backend/modules/crm/comercial_service.py:1174:                pedidos.append(ped)
/app/backend/modules/crm/comercial_service.py:1177:            count_query = "SELECT COUNT(*) as total FROM Venta_Pedidos WHERE Activo = 1"
/app/backend/modules/crm/comercial_service.py:1182:                "pedidos": pedidos,
/app/backend/modules/crm/comercial_service.py:1191:    def obtener_pedido(self, pedido_id: int) -> Optional[Dict[str, Any]]:
/app/backend/modules/crm/comercial_service.py:1192:        """Obtiene detalle de un pedido"""
/app/backend/modules/crm/comercial_service.py:1199:                FROM Venta_Pedidos p
/app/backend/modules/crm/comercial_service.py:1201:                WHERE p.PedidoID = %s
/app/backend/modules/crm/comercial_service.py:1202:            """, (pedido_id,))
/app/backend/modules/crm/comercial_service.py:1215:                SELECT * FROM Venta_PedidosDetalle WHERE PedidoID = %s ORDER BY Renglon
/app/backend/modules/crm/comercial_service.py:1216:            """, (pedido_id,))
/app/backend/modules/crm/comercial_service.py:1224:    def crear_pedido(self, data: Dict, usuario_id: str) -> Dict[str, Any]:
/app/backend/modules/crm/comercial_service.py:1225:        """Crea un pedido de venta"""
/app/backend/modules/crm/comercial_service.py:1234:                SELECT COALESCE(MAX(CAST(SUBSTRING(FolioPedido, 5, 10) AS INT)), 0) + 1 as seq
/app/backend/modules/crm/comercial_service.py:1235:                FROM Venta_Pedidos
/app/backend/modules/crm/comercial_service.py:1236:                WHERE FolioPedido LIKE 'PED-%'
/app/backend/modules/crm/comercial_service.py:1242:                INSERT INTO Venta_Pedidos (
/app/backend/modules/crm/comercial_service.py:1243:                    Serie, FolioPedido, FechaPedido, FechaCompromiso,
/app/backend/modules/crm/comercial_service.py:1245:                    MonedaID, TipoCambio, EstatusPedidoID,
/app/backend/modules/crm/comercial_service.py:1284:            cursor.execute("SELECT SCOPE_IDENTITY() as pedido_id")
/app/backend/modules/crm/comercial_service.py:1285:            pedido_id = cursor.fetchone()['pedido_id']
/app/backend/modules/crm/comercial_service.py:1290:                    UPDATE Venta_Cotizaciones SET PedidoID = %s WHERE CotizacionID = %s
/app/backend/modules/crm/comercial_service.py:1291:                """, (pedido_id, data['cotizacion_id']))
/app/backend/modules/crm/comercial_service.py:1297:                        INSERT INTO Venta_PedidosDetalle (
/app/backend/modules/crm/comercial_service.py:1298:                            PedidoID, Renglon, ProductoID, Descripcion, Cantidad,
/app/backend/modules/crm/comercial_service.py:1302:                        pedido_id, i, det['producto_id'], det.get('descripcion'),
/app/backend/modules/crm/comercial_service.py:1310:            logger.info(f"[CRM] Pedido creado: {folio}")
/app/backend/modules/crm/comercial_service.py:1313:                "pedido_id": pedido_id,
/app/backend/modules/crm/comercial_service.py:1314:                "folio_pedido": folio,
/app/backend/modules/crm/comercial_service.py:1320:            logger.error(f"[CRM] Error creando pedido: {e}")
/app/backend/modules/crm/comercial_service.py:1325:    def confirmar_pedido(self, pedido_id: int, usuario_id: str) -> Dict[str, Any]:
/app/backend/modules/crm/comercial_service.py:1326:        """Confirma un pedido"""
/app/backend/modules/crm/comercial_service.py:1332:                UPDATE Venta_Pedidos SET
/app/backend/modules/crm/comercial_service.py:1333:                    EstatusPedidoID = 2,
/app/backend/modules/crm/comercial_service.py:1338:                WHERE PedidoID = %s AND EstatusPedidoID = 1
/app/backend/modules/crm/comercial_service.py:1339:            """, (self._now_utc(), usuario_id, usuario_id, pedido_id))
/app/backend/modules/crm/comercial_service.py:1342:                raise ValueError("Pedido no encontrado o no está en borrador")
/app/backend/modules/crm/comercial_service.py:1346:            return {"pedido_id": pedido_id, "estatus": "CONFIRMADO"}
/app/backend/modules/crm/comercial_service.py:1378:                    r.PedidoID, r.ClienteID, cl.RazonSocial as ClienteRazonSocial,
/app/backend/modules/crm/comercial_service.py:1489:                    EmpresaID, SucursalID, AlmacenID, FolioRemision,
/app/backend/modules/crm/comercial_service.py:1490:                    PedidoID, CotizacionID, OportunidadID, CuentaID,
/app/backend/modules/crm/comercial_service.py:1502:                data.get('almacen_id'),
/app/backend/modules/crm/comercial_service.py:1504:                data.get('pedido_id'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:183:            "referencia": f"Pedido #{demo_randint(100, 999)} - {demo_choice(['Mercancía', 'Insumos', 'Servicios', 'Materiales'])}",
/app/backend/modules/finanzas/repository_cortes_z.py:227:            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
/app/backend/modules/finanzas/repository_cortes_z.py:230:            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
/app/backend/modules/finanzas/repository_cortes_z.py:233:            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
/app/backend/modules/finanzas/repository_cortes_z.py:236:            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
/app/backend/modules/finanzas/repository_cortes_z.py:239:            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
/app/backend/modules/finanzas/repository_cortes_z.py:242:            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
/app/backend/modules/finanzas/repository_cortes_z.py:245:            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
/app/backend/modules/finanzas/repository_cortes_z.py:248:            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
/app/backend/modules/finanzas/repository_cortes_z.py:253:            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
/app/backend/modules/finanzas/repository_cortes_z.py:255:        FROM movtoscaja mc
/app/backend/modules/finanzas/propinas_tpv/service.py:174:                            'formula_aplicada': 'movtoscajadetalles WHERE idconcepto=9',
/app/backend/modules/finanzas/propinas_tpv/schema_detector_subprocess.py:8:- Relación: cheques.idturno → turnos.idturno → movtoscaja (Corte Z)
/app/backend/modules/finanzas/propinas_tpv/schema_detector_subprocess.py:35:    - Relación: cheques.idturno → turnos.idturno → movtoscaja (Corte Z)
/app/backend/modules/finanzas/propinas_tpv/schema_detector_subprocess.py:48:        - Tabla movtoscaja
/app/backend/modules/finanzas/propinas_tpv/schema_detector_subprocess.py:63:            WHERE TABLE_NAME IN ('cheques', 'turnos', 'movtoscaja')
/app/backend/modules/finanzas/propinas_tpv/schema_detector_subprocess.py:152:        # Verificar tabla movtoscaja (para Cortes Z)
/app/backend/modules/finanzas/propinas_tpv/schema_detector_subprocess.py:153:        has_movtoscaja = 'movtoscaja' in tables
/app/backend/modules/finanzas/propinas_tpv/schema_detector_subprocess.py:154:        if not has_movtoscaja:
/app/backend/modules/finanzas/propinas_tpv/schema_detector_subprocess.py:155:            problems.append("CRÍTICO: No se encontró tabla 'movtoscaja'")
/app/backend/modules/finanzas/propinas_tpv/schema_detector_subprocess.py:173:            'tabla_cortes': 'movtoscaja' if has_movtoscaja else None,
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:8:- Relación: cheques.idturno → turnos.idturno → movtoscaja (Corte Z)
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:30:    - Relación: cheques.idturno → turnos.idturno → movtoscaja (Corte Z)
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:43:        - Tabla movtoscaja
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:58:            WHERE TABLE_NAME IN ('cheques', 'turnos', 'movtoscaja')
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:145:        # Verificar tabla movtoscaja
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:146:        if 'movtoscaja' in tables:
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:147:            schema['tabla_cortes'] = 'movtoscaja'
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:148:            cols = tables['movtoscaja']
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:177:        3. Tabla movtoscaja
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:200:            issues.append("CRÍTICO: No se encontró tabla 'movtoscaja'")
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:218:        - Relación: cheques → turnos → movtoscaja
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:257:        FROM movtoscaja mc
/app/backend/modules/finanzas/propinas_tpv/repository.py:58:        Fuente: movtoscajadetalles (concepto 9 = Propinas Pagadas)
/app/backend/modules/finanzas/propinas_tpv/repository.py:83:                FROM movtoscajadetalles d 
/app/backend/modules/finanzas/propinas_tpv/repository.py:91:                FROM movtoscajadetalles d 
/app/backend/modules/finanzas/propinas_tpv/repository.py:102:                FROM movtoscajadetalles d 
/app/backend/modules/finanzas/propinas_tpv/repository.py:107:        FROM movtoscaja mc
/app/backend/modules/finanzas/propinas_tpv/repository.py:315:            LEFT JOIN movtoscaja mc ON t.idturno = mc.idturno AND mc.idtipomovtocaja = 3
/app/backend/modules/finanzas/propinas_tpv/routes.py:206:    Lee concepto 9 (Propinas Pagadas) de movtoscajadetalles.
/app/backend/modules/finanzas/propinas_tpv/models.py:179:    conceptos: List[int] = Field(default=[10, 11, 12], description="IDs de concepto en movtoscajadetalles")
/app/backend/modules/finanzas/test_conn_cienfuegos.py:22:8. Existencia de tablas: turnos, movtoscaja
/app/backend/modules/finanzas/test_conn_cienfuegos.py:656:    """Prueba 7: Verificar existencia de tablas turnos y movtoscaja"""
/app/backend/modules/finanzas/test_conn_cienfuegos.py:676:    tables_to_check = ['turnos', 'movtoscaja']
/app/backend/modules/finanzas/test_conn_cienfuegos.py:776:        # Conteo de movtoscaja
/app/backend/modules/finanzas/test_conn_cienfuegos.py:777:        cursor.execute("SELECT COUNT(*) as total FROM movtoscaja")
/app/backend/modules/finanzas/test_conn_cienfuegos.py:779:        counts['movtoscaja_total'] = row['total'] if row else 0
/app/backend/modules/finanzas/test_conn_cienfuegos.py:784:            f"Conteos obtenidos: turnos={counts['turnos_cerrados']} cerrados, movtoscaja={counts['movtoscaja_total']}",
/app/backend/modules/finanzas/test_conn_cienfuegos.py:922:        # Muestra de movtoscaja (últimos 5)
/app/backend/modules/finanzas/test_conn_cienfuegos.py:930:            FROM movtoscaja
/app/backend/modules/finanzas/test_conn_cienfuegos.py:934:        movtos_sample = cursor.fetchall()
/app/backend/modules/finanzas/test_conn_cienfuegos.py:942:            f"Muestras obtenidas: {len(turnos_sample)} turnos, {len(movtos_sample)} movtos",
/app/backend/modules/finanzas/test_conn_cienfuegos.py:945:                'movtoscaja_sample': [serialize_row(r) for r in movtos_sample]
/app/backend/modules/finanzas/test_conn_cienfuegos.py:1206:                    "Las credenciales (usuario/contraseña) almacenadas en EDARSAHUB para CIENFUEGOS son incorrectas. "
/app/backend/modules/finanzas/test_conn_cienfuegos.py:1240:            print("\n--- PRUEBA 7: Tablas turnos y movtoscaja ---")
/app/backend/modules/cava_socios/__init__.py:5:Tipo: Módulo principal (Inventario en custodia de terceros)
/app/backend/modules/manuales_operativos/service.py:42:    - Almacenar y consultar manuales
/app/backend/modules/manuales_operativos/service.py:96:            almacen = proceso.get("almacen_nombre", "Sin almacén")
/app/backend/modules/manuales_operativos/service.py:97:            fecha_pedido = proceso.get("fecha_pedido", datetime.now(timezone.utc))
/app/backend/modules/manuales_operativos/service.py:98:            if isinstance(fecha_pedido, str):
/app/backend/modules/manuales_operativos/service.py:99:                fecha_pedido = datetime.fromisoformat(fecha_pedido.replace('Z', '+00:00'))
/app/backend/modules/manuales_operativos/service.py:101:            nombre_proceso = f"Auditoría Operativa de Compras - {sucursal} - {almacen}"
/app/backend/modules/manuales_operativos/service.py:106:                f"asegurando la correcta recepción de productos, verificación de inventarios "
/app/backend/modules/manuales_operativos/service.py:116:                f"para la sucursal {sucursal}, almacén {almacen}. "
/app/backend/modules/manuales_operativos/service.py:117:                f"Incluye validación de inventarios y autorizaciones requeridas."
/app/backend/modules/manuales_operativos/service.py:304:        politicas.append(f"Período de análisis de inventarios: {dias} días")
/app/backend/modules/manuales_operativos/service.py:308:        politicas.append(f"Días objetivo de inventario: {dias_obj} días")
/app/backend/modules/manuales_operativos/service.py:310:        # Política de inventario físico
/app/backend/modules/manuales_operativos/service.py:311:        if proceso.get("tiene_inventario_final"):
/app/backend/modules/manuales_operativos/service.py:312:            politicas.append("Se requiere inventario físico para validación")
/app/backend/modules/manuales_operativos/service.py:320:            if evento.get("evento") == "PENDIENTE_INVENTARIO":
/app/backend/modules/manuales_operativos/service.py:321:                politicas.append("Proceso detenido hasta captura de inventario físico")
/app/backend/modules/manuales_operativos/service.py:329:        # Inventarios
/app/backend/modules/manuales_operativos/service.py:330:        if proceso.get("inventario_inicial_id"):
/app/backend/modules/manuales_operativos/service.py:332:                tipo="Inventario Inicial",
/app/backend/modules/manuales_operativos/service.py:333:                descripcion="Inventario físico de inicio de período",
/app/backend/modules/manuales_operativos/service.py:334:                referencia=proceso.get("inventario_inicial_id"),
/app/backend/modules/manuales_operativos/service.py:335:                fecha=proceso.get("inventario_inicial_fecha")
/app/backend/modules/manuales_operativos/service.py:338:        if proceso.get("inventario_final_id"):
/app/backend/modules/manuales_operativos/service.py:340:                tipo="Inventario Final",
/app/backend/modules/manuales_operativos/service.py:341:                descripcion="Inventario físico de cierre de período",
/app/backend/modules/manuales_operativos/service.py:342:                referencia=proceso.get("inventario_final_id"),
/app/backend/modules/manuales_operativos/service.py:343:                fecha=proceso.get("inventario_final_fecha")
/app/backend/modules/manuales_operativos/triggers.py:235:    almacen = proceso.get("almacen_nombre", "Sin almacén")
/app/backend/modules/manuales_operativos/triggers.py:236:    nombre_proceso = f"Auditoría Operativa de Compras - {sucursal} - {almacen}"
/app/backend/modules/manuales_operativos/triggers.py:240:        f"asegurando la correcta recepción de productos, verificación de inventarios "
/app/backend/modules/manuales_operativos/triggers.py:246:        f"Este proceso cubre la auditoría de compras del período para la sucursal {sucursal}, almacén {almacen}. "
/app/backend/modules/manuales_operativos/triggers.py:247:        "Incluye validación de inventarios y autorizaciones requeridas."
/app/backend/modules/manuales_operativos/triggers.py:298:        f"Período de análisis de inventarios: {proceso.get('dias_periodo_analisis', 15)} días",
/app/backend/modules/manuales_operativos/triggers.py:299:        f"Días objetivo de inventario: {proceso.get('dias_objetivo', 10)} días"
/app/backend/modules/manuales_operativos/triggers.py:306:    if proceso.get("inventario_final_id"):
/app/backend/modules/manuales_operativos/triggers.py:308:            tipo="Inventario Final",
/app/backend/modules/manuales_operativos/triggers.py:309:            descripcion="Inventario físico de cierre de período",
/app/backend/modules/manuales_operativos/triggers.py:310:            referencia=proceso.get("inventario_final_id")
/app/backend/modules/manuales_operativos/schemas.py:143:    """Schema del manual como está almacenado en MongoDB."""
/app/backend/modules/manuales_operativos/schemas.py:178:    "PENDIENTE_INVENTARIO": "Se detectó que falta inventario físico para continuar",
/app/backend/modules/manuales_operativos/schemas.py:179:    "INVENTARIO_CAPTURADO": "Se capturó el inventario físico requerido",
/app/backend/modules/compras/service.py:7:- Lógica de inventarios físicos, pedidos, facturas
/app/backend/modules/compras/service.py:15:NOTA: La lógica compleja de auditoría operativa y cálculo de pedidos
/app/backend/modules/compras/service.py:36:# INVENTARIOS FÍSICOS
/app/backend/modules/compras/service.py:39:async def obtener_inventarios_fisicos(
/app/backend/modules/compras/service.py:43:    almacen: str = None
/app/backend/modules/compras/service.py:46:    Obtiene la lista de inventarios físicos disponibles.
/app/backend/modules/compras/service.py:60:            log_compras_adapter_selected("inventarios-fisicos", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:62:            almacen_filtro = ""
/app/backend/modules/compras/service.py:63:            if almacen and almacen != "TODOS":
/app/backend/modules/compras/service.py:64:                almacen_filtro = f"AND F.Al_Cve_Almacen = '{almacen}'"
/app/backend/modules/compras/service.py:66:            result = repo.query_inventarios_fisicos_mpro(server, almacen_filtro, sucursal_id)
/app/backend/modules/compras/service.py:67:            log_compras_query_result("inventarios-fisicos", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:70:            log_compras_adapter_selected("inventarios-fisicos", server_id, system_type, "SR_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:71:            almacen_filtro = ""
/app/backend/modules/compras/service.py:72:            if almacen and almacen != "TODOS":
/app/backend/modules/compras/service.py:73:                almacen_filtro = f"AND F.idalmacen = {almacen}"
/app/backend/modules/compras/service.py:75:            result = repo.query_inventarios_fisicos_sr(server, almacen_filtro)
/app/backend/modules/compras/service.py:76:            log_compras_query_result("inventarios-fisicos", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:80:            log_compras_error("inventarios-fisicos", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/modules/compras/service.py:83:                detail=f"El tipo de sistema '{system_type}' (normalizado: {normalized}) no está soportado para inventarios físicos"
/app/backend/modules/compras/service.py:92:                "almacen_id": str(r.get('almacen_id', '')),
/app/backend/modules/compras/service.py:93:                "almacen": r.get('almacen', ''),
/app/backend/modules/compras/service.py:103:        log_compras_error("inventarios-fisicos", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:108:# PEDIDOS VIGENTES
/app/backend/modules/compras/service.py:111:async def obtener_pedidos_vigentes(server_id: str, sucursal_id: str = None) -> List[Dict]:
/app/backend/modules/compras/service.py:113:    Obtiene pedidos/requisiciones vigentes.
/app/backend/modules/compras/service.py:130:            log_compras_adapter_selected("pedidos-vigentes", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:131:            result = repo.query_pedidos_vigentes_mpro(server, sucursal_id)
/app/backend/modules/compras/service.py:134:            log_compras_query_result("pedidos-vigentes", server_id, "SUCCESS", len(data))
/app/backend/modules/compras/service.py:137:            log_compras_adapter_selected("pedidos-vigentes", server_id, system_type, "SR_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:138:            query_result = repo.query_pedidos_vigentes_sr(server)
/app/backend/modules/compras/service.py:142:                log_compras_query_result("pedidos-vigentes", server_id, "TABLE_NOT_FOUND", 0)
/app/backend/modules/compras/service.py:143:                logging.info(f"[COMPRAS] Pedidos no disponibles en {server['name']}: {query_result.message}")
/app/backend/modules/compras/service.py:147:                log_compras_error("pedidos-vigentes", server_id, query_result.status, query_result.message, system_type)
/app/backend/modules/compras/service.py:148:                logging.warning(f"[COMPRAS] Error en pedidos: {query_result.message}")
/app/backend/modules/compras/service.py:152:            log_compras_query_result("pedidos-vigentes", server_id, "SUCCESS", len(data))
/app/backend/modules/compras/service.py:155:            log_compras_error("pedidos-vigentes", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/modules/compras/service.py:158:                detail=f"El tipo de sistema '{system_type}' (normalizado: {normalized}) no está soportado para pedidos"
/app/backend/modules/compras/service.py:167:                "almacen_id": str(r.get('almacen_id', '')),
/app/backend/modules/compras/service.py:168:                "almacen": r.get('almacen', ''),
/app/backend/modules/compras/service.py:180:        log_compras_error("pedidos-vigentes", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:198:            "dias_inventario": params.get("dias_inventario", 10),
/app/backend/modules/compras/service.py:206:        "dias_inventario": 10,
/app/backend/modules/compras/service.py:331:    'obtener_inventarios_fisicos',
/app/backend/modules/compras/service.py:332:    'obtener_pedidos_vigentes',
/app/backend/modules/compras/repository_compras_sql.py:59:-- Almacena parámetros de configuración de compras por servidor/sucursal
/app/backend/modules/compras/repository_compras_sql.py:71:        -- Parámetros de cálculo de pedidos
/app/backend/modules/compras/repository_compras_sql.py:72:        [DiasInventario] INT NOT NULL DEFAULT 10,
/app/backend/modules/compras/repository_compras_sql.py:150:                DiasInventario as dias_inventario,
/app/backend/modules/compras/repository_compras_sql.py:180:                'dias_inventario': row['dias_inventario'],
/app/backend/modules/compras/repository_compras_sql.py:224:        dias_inventario = params.get('dias_inventario', 10)
/app/backend/modules/compras/repository_compras_sql.py:239:                    DiasInventario = %s,
/app/backend/modules/compras/repository_compras_sql.py:247:                INSERT (ServerID, SucursalID, DiasInventario, ExcluirDomingos, 
/app/backend/modules/compras/repository_compras_sql.py:256:            dias_inventario, excluir_domingos, dias_inhabiles_json, dias_transito_proveedor, usuario,
/app/backend/modules/compras/repository_compras_sql.py:258:            server_id, sucursal, dias_inventario, excluir_domingos, 
/app/backend/modules/compras/repository_compras_sql.py:291:                DiasInventario as dias_inventario,
/app/backend/modules/compras/repository_compras_sql.py:322:                'dias_inventario': row['dias_inventario'],
/app/backend/modules/compras/__init__.py:4:Módulo de compras, pedidos e inventarios.
/app/backend/modules/compras/__init__.py:20:NOTA: Los endpoints complejos (calculo-pedido, auditoria-operativa, dashboard)
/app/backend/modules/compras/__init__.py:27:    CalculoPedidoRequest,
/app/backend/modules/compras/__init__.py:78:    'CalculoPedidoRequest',
/app/backend/modules/compras/eventos_compras.py:16:- NUEVO_INVENTARIO: Se detectó un nuevo inventario físico
/app/backend/modules/compras/eventos_compras.py:17:- NUEVA_REQUISICION: Se detectó una nueva requisición/orden de compra
/app/backend/modules/compras/eventos_compras.py:18:- INVENTARIO_MODIFICADO: Un inventario existente fue modificado
/app/backend/modules/compras/eventos_compras.py:19:- REQUISICION_AUTORIZADA: Una requisición cambió a estado autorizado
/app/backend/modules/compras/eventos_compras.py:59:    NUEVO_INVENTARIO = "NUEVO_INVENTARIO"
/app/backend/modules/compras/eventos_compras.py:60:    NUEVA_REQUISICION = "NUEVA_REQUISICION"
/app/backend/modules/compras/eventos_compras.py:61:    INVENTARIO_MODIFICADO = "INVENTARIO_MODIFICADO"
/app/backend/modules/compras/eventos_compras.py:62:    REQUISICION_AUTORIZADA = "REQUISICION_AUTORIZADA"
/app/backend/modules/compras/eventos_compras.py:66:    INVENTARIOS = "INVENTARIOS"
/app/backend/modules/compras/eventos_compras.py:67:    REQUISICIONES = "REQUISICIONES"
/app/backend/modules/compras/eventos_compras.py:134:    Los eventos se almacenan en tabla SQL y se procesan periódicamente.
/app/backend/modules/compras/eventos_compras.py:433:    def detectar_nuevos_inventarios(
/app/backend/modules/compras/eventos_compras.py:440:        Detecta inventarios nuevos desde el último checkpoint.
/app/backend/modules/compras/eventos_compras.py:450:        checkpoint = self.checkpoint_mgr.get_checkpoint(server_id, SyncType.INVENTARIOS)
/app/backend/modules/compras/eventos_compras.py:459:                               Al_Cve_Almacen as almacen_id, Sc_Cve_Sucursal as sucursal_id
/app/backend/modules/compras/eventos_compras.py:468:                               Al_Cve_Almacen as almacen_id, Sc_Cve_Sucursal as sucursal_id
/app/backend/modules/compras/eventos_compras.py:475:                        SELECT TOP 100 folio, fecha, idalmacen1 as almacen_id
/app/backend/modules/compras/eventos_compras.py:476:                        FROM invfisico
/app/backend/modules/compras/eventos_compras.py:482:                        SELECT TOP 10 folio, fecha, idalmacen1 as almacen_id
/app/backend/modules/compras/eventos_compras.py:483:                        FROM invfisico
/app/backend/modules/compras/eventos_compras.py:515:                        evento_tipo=EventoTipo.NUEVO_INVENTARIO,
/app/backend/modules/compras/eventos_compras.py:523:                            "almacen_id": row.get('almacen_id'),
/app/backend/modules/compras/eventos_compras.py:539:                    server_id, server_name, SyncType.INVENTARIOS,
/app/backend/modules/compras/eventos_compras.py:543:            logger.info(f"[DETECTOR] Inventarios {server_name}: {nuevos} nuevos, {eventos_generados} eventos")
/app/backend/modules/compras/eventos_compras.py:547:            logger.error(f"[DETECTOR] Error detectando inventarios en {server_name}: {e}")
/app/backend/modules/compras/eventos_compras.py:550:    def detectar_nuevas_requisiciones(
/app/backend/modules/compras/eventos_compras.py:557:        Detecta requisiciones nuevas desde el último checkpoint.
/app/backend/modules/compras/eventos_compras.py:563:        checkpoint = self.checkpoint_mgr.get_checkpoint(server_id, SyncType.REQUISICIONES)
/app/backend/modules/compras/eventos_compras.py:588:                        FROM ordenescompra
/app/backend/modules/compras/eventos_compras.py:596:                        FROM ordenescompra
/app/backend/modules/compras/eventos_compras.py:625:                        evento_tipo=EventoTipo.NUEVA_REQUISICION,
/app/backend/modules/compras/eventos_compras.py:647:                    server_id, server_name, SyncType.REQUISICIONES,
/app/backend/modules/compras/eventos_compras.py:651:            logger.info(f"[DETECTOR] Requisiciones {server_name}: {nuevos} nuevos, {eventos_generados} eventos")
/app/backend/modules/compras/eventos_compras.py:655:            logger.error(f"[DETECTOR] Error detectando requisiciones en {server_name}: {e}")
/app/backend/modules/compras/repository.py:20:por compatibilidad con otros módulos que aún usan StubDatabase (pedidos_detector_job).
/app/backend/modules/compras/repository.py:197:# QUERIES SQL - INVENTARIOS FÍSICOS
/app/backend/modules/compras/repository.py:200:def query_inventarios_fisicos_mpro(server: Dict, almacen_filtro: str = "", sucursal_id: str = None) -> List[Dict]:
/app/backend/modules/compras/repository.py:202:    Obtiene inventarios físicos de MPRO.
/app/backend/modules/compras/repository.py:212:        F.Al_Cve_Almacen as almacen_id,
/app/backend/modules/compras/repository.py:213:        A.Al_Nombre as almacen,
/app/backend/modules/compras/repository.py:214:        (SELECT COUNT(*) FROM Inventario_Fisico_Detalle D WHERE D.If_Folio = F.If_Folio) as productos,
/app/backend/modules/compras/repository.py:216:    FROM Inventario_Fisico F
/app/backend/modules/compras/repository.py:218:    INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
/app/backend/modules/compras/repository.py:219:    WHERE 1=1 {almacen_filtro} {sucursal_filtro}
/app/backend/modules/compras/repository.py:229:def query_inventarios_fisicos_sr(server: Dict, almacen_filtro: str = "") -> List[Dict]:
/app/backend/modules/compras/repository.py:231:    Obtiene inventarios físicos de SoftRestaurant.
/app/backend/modules/compras/repository.py:239:        CAST(F.idalmacen as VARCHAR) as almacen_id,
/app/backend/modules/compras/repository.py:240:        A.descripcion as almacen,
/app/backend/modules/compras/repository.py:244:    INNER JOIN almacen A ON A.idalmacen = F.idalmacen
/app/backend/modules/compras/repository.py:245:    WHERE 1=1 {almacen_filtro}
/app/backend/modules/compras/repository.py:256:# QUERIES SQL - PEDIDOS VIGENTES
/app/backend/modules/compras/repository.py:259:def query_pedidos_vigentes_mpro(server: Dict, sucursal_id: str = None) -> List[Dict]:
/app/backend/modules/compras/repository.py:261:    Obtiene pedidos/requisiciones vigentes de MPRO.
/app/backend/modules/compras/repository.py:271:        R.Al_Cve_Almacen as almacen_id,
/app/backend/modules/compras/repository.py:272:        A.Al_Nombre as almacen,
/app/backend/modules/compras/repository.py:275:        (SELECT COUNT(*) FROM Requisicion_Detalle D WHERE D.Rq_Folio = R.Rq_Folio) as productos,
/app/backend/modules/compras/repository.py:277:    FROM Requisicion R
/app/backend/modules/compras/repository.py:279:    INNER JOIN Almacen A ON A.Al_Cve_Almacen = R.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = R.Sc_Cve_Sucursal
/app/backend/modules/compras/repository.py:290:def query_pedidos_vigentes_sr(server: Dict) -> ComprasQueryResult:
/app/backend/modules/compras/repository.py:292:    Obtiene pedidos vigentes de SoftRestaurant.
/app/backend/modules/compras/repository.py:295:    - Valida existencia de tabla 'pedidocompra' antes de ejecutar
/app/backend/modules/compras/repository.py:299:    # Primero validar que exista la tabla pedidocompra
/app/backend/modules/compras/repository.py:300:    if not validate_table_exists(server, 'pedidocompra'):
/app/backend/modules/compras/repository.py:301:        logging.info(f"[COMPRAS] Tabla 'pedidocompra' no existe en {server['name']} - operación no soportada")
/app/backend/modules/compras/repository.py:306:            message=f"El servidor {server['name']} no tiene módulo de pedidos de compra instalado"
/app/backend/modules/compras/repository.py:311:        CAST(P.idpedidocompra as VARCHAR) as folio,
/app/backend/modules/compras/repository.py:315:        CAST(P.idalmacen as VARCHAR) as almacen_id,
/app/backend/modules/compras/repository.py:316:        A.descripcion as almacen,
/app/backend/modules/compras/repository.py:324:        (SELECT COUNT(*) FROM detallepedidocompra D WHERE D.idpedidocompra = P.idpedidocompra) as productos,
/app/backend/modules/compras/repository.py:326:    FROM pedidocompra P
/app/backend/modules/compras/repository.py:327:    INNER JOIN almacen A ON A.idalmacen = P.idalmacen
/app/backend/modules/compras/repository.py:328:    ORDER BY P.fecha DESC, P.idpedidocompra DESC
/app/backend/modules/compras/repository.py:342:                message=f"Se encontraron {len(result)} pedidos"
/app/backend/modules/compras/repository.py:349:                message="No hay pedidos de compra vigentes"
/app/backend/modules/compras/repository.py:353:        logging.error(f"[COMPRAS] Error en query_pedidos_vigentes_sr: {e}")
/app/backend/modules/compras/repository.py:373:# QUERIES SQL - DETALLE DE PEDIDO/REQUISICIÓN
/app/backend/modules/compras/repository.py:376:def query_detalle_pedido_mpro(server: Dict, folio: str) -> List[Dict]:
/app/backend/modules/compras/repository.py:378:    Obtiene el detalle de productos de un pedido/requisición en MPRO.
/app/backend/modules/compras/repository.py:389:            FROM Inventario_Fisico_Detalle ID
/app/backend/modules/compras/repository.py:390:            INNER JOIN Inventario_Fisico I ON I.If_Folio = ID.If_Folio
/app/backend/modules/compras/repository.py:392:            AND I.Al_Cve_Almacen = R.Al_Cve_Almacen
/app/backend/modules/compras/repository.py:400:            AND M.Al_Cve_Almacen = R.Al_Cve_Almacen
/app/backend/modules/compras/repository.py:404:    FROM Requisicion_Detalle RD
/app/backend/modules/compras/repository.py:405:    INNER JOIN Requisicion R ON R.Rq_Folio = RD.Rq_Folio
/app/backend/modules/compras/repository.py:490:    # Inventarios físicos
/app/backend/modules/compras/repository.py:491:    'query_inventarios_fisicos_mpro',
/app/backend/modules/compras/repository.py:492:    'query_inventarios_fisicos_sr',
/app/backend/modules/compras/repository.py:493:    # Pedidos
/app/backend/modules/compras/repository.py:494:    'query_pedidos_vigentes_mpro',
/app/backend/modules/compras/repository.py:495:    'query_pedidos_vigentes_sr',
/app/backend/modules/compras/repository.py:496:    'query_detalle_pedido_mpro',
/app/backend/modules/compras/historical_kpis_repository.py:11:- INVENTARIO_FISICO: Conteos de inventario por almacén/fecha
/app/backend/modules/compras/historical_kpis_repository.py:12:- PEDIDO: Pedidos/requisiciones por fecha
/app/backend/modules/compras/historical_kpis_repository.py:96:                -- Inventarios Físicos
/app/backend/modules/compras/historical_kpis_repository.py:99:                [inv_almacenes] NVARCHAR(500) DEFAULT '',
/app/backend/modules/compras/historical_kpis_repository.py:101:                -- Pedidos
/app/backend/modules/compras/historical_kpis_repository.py:102:                [ped_pedidos_count] INT DEFAULT 0,
/app/backend/modules/compras/historical_kpis_repository.py:179:                inv_almacenes = %s,
/app/backend/modules/compras/historical_kpis_repository.py:180:                ped_pedidos_count = %s,
/app/backend/modules/compras/historical_kpis_repository.py:199:                kpi_data.get('inv_almacenes', ''),
/app/backend/modules/compras/historical_kpis_repository.py:200:                kpi_data.get('ped_pedidos_count', 0),
/app/backend/modules/compras/historical_kpis_repository.py:221:                inv_conteos_count, inv_productos_count, inv_almacenes,
/app/backend/modules/compras/historical_kpis_repository.py:222:                ped_pedidos_count, ped_total_monto, ped_productos_count,
/app/backend/modules/compras/historical_kpis_repository.py:232:                kpi_data.get('inv_almacenes', ''),
/app/backend/modules/compras/historical_kpis_repository.py:233:                kpi_data.get('ped_pedidos_count', 0),
/app/backend/modules/compras/sync_service.py:2:COMPRAS SYNC SERVICE - Sincronización de Inventarios y Requisiciones a EDARSAHUB
/app/backend/modules/compras/sync_service.py:8:- Compras_Inventarios_Fisicos_Sync: Inventarios físicos sincronizados
/app/backend/modules/compras/sync_service.py:9:- Compras_Requisiciones_Sync: Requisiciones/pedidos sincronizados
/app/backend/modules/compras/sync_service.py:46:def obtener_inventarios_fisicos_sync(
/app/backend/modules/compras/sync_service.py:50:    almacen: str = None,
/app/backend/modules/compras/sync_service.py:54:    Obtiene inventarios físicos DESDE EDARSAHUB (sincronizados).
/app/backend/modules/compras/sync_service.py:63:                folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
/app/backend/modules/compras/sync_service.py:67:            FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/compras/sync_service.py:84:        if almacen and almacen != 'TODOS':
/app/backend/modules/compras/sync_service.py:85:            query += " AND almacen LIKE %s"
/app/backend/modules/compras/sync_service.py:86:            params.append(f'%{almacen}%')
/app/backend/modules/compras/sync_service.py:101:        logger.info(f"[SYNC-READ] Inventarios físicos: {len(rows)} registros desde EDARSAHUB")
/app/backend/modules/compras/sync_service.py:105:        logger.error(f"[SYNC-READ] Error obteniendo inventarios: {e}")
/app/backend/modules/compras/sync_service.py:109:def obtener_requisiciones_sync(
/app/backend/modules/compras/sync_service.py:116:    Obtiene requisiciones/pedidos DESDE EDARSAHUB (sincronizados).
/app/backend/modules/compras/sync_service.py:129:            FROM Compras_Requisiciones_Sync
/app/backend/modules/compras/sync_service.py:158:        logger.info(f"[SYNC-READ] Requisiciones: {len(rows)} registros desde EDARSAHUB")
/app/backend/modules/compras/sync_service.py:162:        logger.error(f"[SYNC-READ] Error obteniendo requisiciones: {e}")
/app/backend/modules/compras/sync_service.py:170:def sync_inventarios_fisicos_from_server(
/app/backend/modules/compras/sync_service.py:176:    Sincroniza inventarios físicos desde un servidor físico a EDARSAHUB.
/app/backend/modules/compras/sync_service.py:194:    logger.info(f"[SYNC] Iniciando sync inventarios: {unidad_codigo} ({system_type})")
/app/backend/modules/compras/sync_service.py:199:            # MPRO usa tabla "Fisico" (no Fisico_Inventario)
/app/backend/modules/compras/sync_service.py:204:                    A.Al_Descripcion as almacen,
/app/backend/modules/compras/sync_service.py:205:                    A.Al_Cve_Almacen as almacen_id,
/app/backend/modules/compras/sync_service.py:212:                INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
/app/backend/modules/compras/sync_service.py:215:                GROUP BY F.Fi_Folio, F.Fi_Fecha, A.Al_Descripcion, A.Al_Cve_Almacen, S.Sc_Descripcion, A.Sc_Cve_Sucursal
/app/backend/modules/compras/sync_service.py:219:            # SoftRestaurant usa tabla "invfisico"
/app/backend/modules/compras/sync_service.py:224:                    A.nombre as almacen,
/app/backend/modules/compras/sync_service.py:225:                    CAST(A.idalmacen AS VARCHAR) as almacen_id,
/app/backend/modules/compras/sync_service.py:231:                FROM invfisico INV
/app/backend/modules/compras/sync_service.py:232:                LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
/app/backend/modules/compras/sync_service.py:258:            UPDATE Compras_Inventarios_Fisicos_Sync 
/app/backend/modules/compras/sync_service.py:268:                    INSERT INTO Compras_Inventarios_Fisicos_Sync
/app/backend/modules/compras/sync_service.py:270:                     folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
/app/backend/modules/compras/sync_service.py:277:                    row.get('almacen', ''),
/app/backend/modules/compras/sync_service.py:278:                    str(row.get('almacen_id', '')),
/app/backend/modules/compras/sync_service.py:287:                logger.warning(f"[SYNC] Error insertando inventario {row.get('folio')}: {e}")
/app/backend/modules/compras/sync_service.py:292:        logger.info(f"[SYNC] Inventarios sincronizados: {records_synced} de {len(rows)}")
/app/backend/modules/compras/sync_service.py:296:        logger.error(f"[SYNC] Error sync inventarios {unidad_codigo}: {e}")
/app/backend/modules/compras/sync_service.py:300:def sync_requisiciones_from_server(
/app/backend/modules/compras/sync_service.py:306:    Sincroniza requisiciones/pedidos desde un servidor físico a EDARSAHUB.
/app/backend/modules/compras/sync_service.py:315:    logger.info(f"[SYNC] Iniciando sync requisiciones: {unidad_codigo} ({system_type})")
/app/backend/modules/compras/sync_service.py:355:                    (SELECT COUNT(*) FROM ordenescompramov WHERE idOrdenCompra = OC.idOrdenCompra) as total_productos,
/app/backend/modules/compras/sync_service.py:363:                FROM ordenescompra OC
/app/backend/modules/compras/sync_service.py:391:            UPDATE Compras_Requisiciones_Sync 
/app/backend/modules/compras/sync_service.py:401:                    INSERT INTO Compras_Requisiciones_Sync
/app/backend/modules/compras/sync_service.py:428:        logger.info(f"[SYNC] Requisiciones sincronizadas: {records_synced} de {len(rows)}")
/app/backend/modules/compras/sync_service.py:432:        logger.error(f"[SYNC] Error sync requisiciones {unidad_codigo}: {e}")
/app/backend/modules/compras/repository_pedidos_sql.py:2:EDARSA HUB - Repositorio SQL para Tracking de Pedidos
/app/backend/modules/compras/repository_pedidos_sql.py:7:- pedidos_procesados_automatizacion → Scheduler_PedidosProcesados  
/app/backend/modules/compras/repository_pedidos_sql.py:78:        logger.error(f"[PEDIDOS_SQL] Error EDARSAHUB: {e}")
/app/backend/modules/compras/repository_pedidos_sql.py:104:        logger.error(f"[PEDIDOS_SQL] Error INSERT EDARSAHUB: {e}")
/app/backend/modules/compras/repository_pedidos_sql.py:109:# TRACKING DE PEDIDOS PROCESADOS
/app/backend/modules/compras/repository_pedidos_sql.py:111:# Reemplaza: db['pedidos_procesados_automatizacion']
/app/backend/modules/compras/repository_pedidos_sql.py:112:# Tabla: Scheduler_PedidosProcesados
/app/backend/modules/compras/repository_pedidos_sql.py:114:async def pedido_ya_procesado_sql(
/app/backend/modules/compras/repository_pedidos_sql.py:120:    Verifica si el pedido ya fue procesado para esta empresa.
/app/backend/modules/compras/repository_pedidos_sql.py:122:    REEMPLAZA: db['pedidos_procesados_automatizacion'].find_one()
/app/backend/modules/compras/repository_pedidos_sql.py:127:        FROM Scheduler_PedidosProcesados
/app/backend/modules/compras/repository_pedidos_sql.py:128:        WHERE EmpresaID = %s AND FolioPedido = %s AND SistemaOrigen = %s
/app/backend/modules/compras/repository_pedidos_sql.py:133:        logger.error(f"[PEDIDOS_SQL] Error verificando pedido procesado: {e}")
/app/backend/modules/compras/repository_pedidos_sql.py:137:async def marcar_pedido_procesado_sql(
/app/backend/modules/compras/repository_pedidos_sql.py:149:    Marca pedido como procesado en SQL.
/app/backend/modules/compras/repository_pedidos_sql.py:151:    REEMPLAZA: db['pedidos_procesados_automatizacion'].update_one(..., upsert=True)
/app/backend/modules/compras/repository_pedidos_sql.py:163:        SELECT ID FROM Scheduler_PedidosProcesados
/app/backend/modules/compras/repository_pedidos_sql.py:164:        WHERE EmpresaID = %s AND FolioPedido = %s AND SistemaOrigen = %s
/app/backend/modules/compras/repository_pedidos_sql.py:171:            UPDATE Scheduler_PedidosProcesados
/app/backend/modules/compras/repository_pedidos_sql.py:177:            WHERE EmpresaID = %s AND FolioPedido = %s AND SistemaOrigen = %s
/app/backend/modules/compras/repository_pedidos_sql.py:186:            INSERT INTO Scheduler_PedidosProcesados (
/app/backend/modules/compras/repository_pedidos_sql.py:187:                SistemaOrigen, ServerID, EmpresaID, SucursalID, FolioPedido,
/app/backend/modules/compras/repository_pedidos_sql.py:193:                estado, now, now, 'PEDIDO', detalles_json
/app/backend/modules/compras/repository_pedidos_sql.py:197:        logger.error(f"[PEDIDOS_SQL] Error marcando pedido procesado: {e}")
/app/backend/modules/compras/repository_pedidos_sql.py:201:async def obtener_pedidos_procesados_sql(
/app/backend/modules/compras/repository_pedidos_sql.py:207:    Obtiene lista de pedidos procesados.
/app/backend/modules/compras/repository_pedidos_sql.py:209:    REEMPLAZA: db['pedidos_procesados_automatizacion'].find()
/app/backend/modules/compras/repository_pedidos_sql.py:226:            FolioPedido, Estado, FechaDeteccion, FechaProcesamiento, DetallesJSON
/app/backend/modules/compras/repository_pedidos_sql.py:227:        FROM Scheduler_PedidosProcesados
/app/backend/modules/compras/repository_pedidos_sql.py:234:        pedidos = []
/app/backend/modules/compras/repository_pedidos_sql.py:243:            pedidos.append({
/app/backend/modules/compras/repository_pedidos_sql.py:246:                'pedido_folio': r['FolioPedido'],
/app/backend/modules/compras/repository_pedidos_sql.py:258:        return pedidos
/app/backend/modules/compras/repository_pedidos_sql.py:261:        logger.error(f"[PEDIDOS_SQL] Error obteniendo pedidos procesados: {e}")
/app/backend/modules/compras/repository_pedidos_sql.py:269:# Tabla: Usa Scheduler_PedidosProcesados con DetallesJSON para tareas simples
/app/backend/modules/compras/repository_pedidos_sql.py:279:    almacen_id: str,
/app/backend/modules/compras/repository_pedidos_sql.py:280:    almacen_nombre: str,
/app/backend/modules/compras/repository_pedidos_sql.py:283:    tipo: str = "CAPTURA_INVENTARIO"
/app/backend/modules/compras/repository_pedidos_sql.py:291:    Para tracking simple, usamos DetallesJSON en Scheduler_PedidosProcesados.
/app/backend/modules/compras/repository_pedidos_sql.py:298:        # Si no, guardar en DetallesJSON del registro de pedido procesado
/app/backend/modules/compras/repository_pedidos_sql.py:308:            'almacen_id': almacen_id,
/app/backend/modules/compras/repository_pedidos_sql.py:309:            'almacen_nombre': almacen_nombre,
/app/backend/modules/compras/repository_pedidos_sql.py:311:            'titulo': f"Capturar inventario físico - {almacen_nombre}",
/app/backend/modules/compras/repository_pedidos_sql.py:319:                EventoID, TipoEvento, EmpresaID, SucursalID, FolioPedido,
/app/backend/modules/compras/repository_pedidos_sql.py:330:            logger.info(f"[PEDIDOS_SQL] Tarea operativa creada en SQL: {tarea_id}")
/app/backend/modules/compras/repository_pedidos_sql.py:333:            # Si la tabla no existe, no es crítico - lo guardamos en el pedido
/app/backend/modules/compras/repository_pedidos_sql.py:334:            logger.warning(f"[PEDIDOS_SQL] No se pudo insertar en Compras_Eventos_Pendientes: {e}")
/app/backend/modules/compras/repository_pedidos_sql.py:339:        logger.error(f"[PEDIDOS_SQL] Error creando tarea operativa: {e}")
/app/backend/modules/compras/repository_pedidos_sql.py:362:            EventoID, TipoEvento, EmpresaID, SucursalID, FolioPedido,
/app/backend/modules/compras/repository_pedidos_sql.py:385:                'folio_pedido': r['FolioPedido'],
/app/backend/modules/compras/repository_pedidos_sql.py:397:        logger.warning(f"[PEDIDOS_SQL] Error obteniendo tareas (tabla puede no existir): {e}")
/app/backend/modules/compras/repository_pedidos_sql.py:407:async def registrar_bitacora_pedidos_sql(
/app/backend/modules/compras/repository_pedidos_sql.py:432:        logger.error(f"[PEDIDOS_SQL] Error registrando bitácora: {e}")
/app/backend/modules/compras/repository_pedidos_sql.py:441:    # Tracking de pedidos
/app/backend/modules/compras/repository_pedidos_sql.py:442:    'pedido_ya_procesado_sql',
/app/backend/modules/compras/repository_pedidos_sql.py:443:    'marcar_pedido_procesado_sql',
/app/backend/modules/compras/repository_pedidos_sql.py:444:    'obtener_pedidos_procesados_sql',
/app/backend/modules/compras/repository_pedidos_sql.py:449:    'registrar_bitacora_pedidos_sql',
/app/backend/modules/compras/routes.py:54:# - GET /compras/inventarios-fisicos/{server_id}
/app/backend/modules/compras/routes.py:55:# - GET /compras/pedidos-vigentes/{server_id}
/app/backend/modules/compras/routes.py:56:# - GET /compras/detalle-pedido/{server_id}/{folio}
/app/backend/modules/compras/routes.py:57:# - GET /compras/detalle-pedido-manual/{server_id}
/app/backend/modules/compras/routes.py:63:# - POST /compras/calculo-pedido (~420 líneas)
/app/backend/modules/compras/schemas.py:8:- Schemas de pedidos, auditoría operativa, análisis de compras
/app/backend/modules/compras/schemas.py:16:    """Parámetros de configuración para cálculo de pedidos."""
/app/backend/modules/compras/schemas.py:17:    dias_inventario: int = 10  # Días de inventario a comprar
/app/backend/modules/compras/schemas.py:23:class CalculoPedidoRequest(BaseModel):
/app/backend/modules/compras/schemas.py:24:    """Request para cálculo de pedido sugerido."""
/app/backend/modules/compras/schemas.py:27:    almacenes: List[str]  # Puede ser uno, varios, o "TODOS"
/app/backend/modules/compras/schemas.py:28:    fecha_inventario_fisico: str  # Fecha del inventario físico inicial
/app/backend/modules/compras/schemas.py:30:    dias_inventario: int = 10  # Días de inventario a comprar
/app/backend/modules/compras/schemas.py:32:    folio_inventario_fisico: Optional[str] = None
/app/backend/modules/compras/schemas.py:35:    folio_pedido_comparar: Optional[str] = None  # Para comparar con pedido existente
/app/backend/modules/compras/schemas.py:42:    almacenes: List[str]
/app/backend/modules/compras/schemas.py:46:    fecha_auditoria: str  # Fecha del inventario final o actual
/app/backend/modules/compras/schemas.py:49:    folio_requisicion: Optional[str] = None  # Requisición a comparar (una sola)
/app/backend/modules/compras/schemas.py:50:    folios_requisiciones: Optional[List[str]] = None  # Múltiples requisiciones
/app/backend/modules/compras/schemas.py:51:    inventario_manual: Optional[List[Dict]] = None  # Para captura manual si no hay folio
/app/backend/modules/compras/schemas.py:52:    inventario_fisico_actual: Optional[List[Dict]] = None  # Captura manual del inv físico del día del pedido
/app/backend/modules/compras/schemas.py:53:    solo_skus_requisicion: bool = True  # Por defecto solo muestra SKUs de las requisiciones
/app/backend/modules/compras/schemas.py:54:    dias_objetivo_default: int = 10  # Días de inventario objetivo por defecto
/app/backend/modules/compras/schemas.py:62:    folios_requisiciones: Optional[List[str]] = None
/app/backend/modules/compras/schemas.py:69:    almacenes: List[str]
/app/backend/modules/compras/schemas.py:81:    almacenes: List[str]
/app/backend/modules/compras/schemas.py:98:    'CalculoPedidoRequest',
/app/backend/scripts/solucion_operaciones_analisis.py:7:           para solucionar la carga nula de Unidades de Negocio, Almacenes e 
/app/backend/scripts/solucion_operaciones_analisis.py:8:           Inventarios en la pestaña (tab) de Análisis de OperacionesPanel.
/app/backend/scripts/solucion_operaciones_analisis.py:34:los fallos que impedían la correcta carga de Unidades de Negocio, Almacenes y sus Inventarios asociados.
/app/backend/scripts/solucion_operaciones_analisis.py:41:2. Selectores (Dropdowns) Estáticos/Hardcodeados: Los Almacenes y los Inventarios Inicial/Final no reaccionaban 
/app/backend/scripts/solucion_operaciones_analisis.py:51:    Se diseña un diccionario reactivo de almacenes por defecto asimilados a las Unidades de Negocio:
/app/backend/scripts/solucion_operaciones_analisis.py:54:    - (Resto de Unidades) -> ['Almacén Estándar', 'Inventario Tránsito']
/app/backend/scripts/solucion_operaciones_analisis.py:57:    Alimentación de opciones de 'Inventario Inicial' e 'Inventario Final' basadas en el período 
/app/backend/scripts/solucion_operaciones_analisis.py:65:ALMACENES_POR_UNIDAD = {
/app/backend/scripts/solucion_operaciones_analisis.py:69:    "LA ESTELAR": ["Bodega Estelar Norte", "Inventario Tránsito"],
/app/backend/scripts/solucion_operaciones_analisis.py:73:INVENTARIOS_ASOCIADOS = {
/app/backend/scripts/solucion_operaciones_analisis.py:83:    almacenes = ALMACENES_POR_UNIDAD.get(unidad_nombre, ["Almacén Estándar"])
/app/backend/scripts/solucion_operaciones_analisis.py:85:    logger.info(f"--> Cargando almacenes validados para {unidad_nombre}: {', '.join(almacenes)}")
/app/backend/scripts/solucion_operaciones_analisis.py:86:    logger.info(f"--> Sincronizando cortes de inventarios para la sesión: {list(INVENTARIOS_ASOCIADOS.values())}")
/app/backend/scripts/solucion_operaciones_analisis.py:87:    return almacenes
/app/backend/scripts/correccion_sistema_menus_y_fallbacks.py:18:    ("Inventarios FinOps", "Inventarios FinOps", "Database", "costos-placeholder", 1, 4, "OPERADOR_EDARSA"),
/app/backend/scripts/finops_shield_mitigacion.py:29:    prompt = "Dame el resumen del inventario de Cienfuegos para FinOps"
/app/backend/scripts/create_cava_socios_rbac.py:7:Tipo: Módulo principal (Inventario en custodia de terceros)
/app/backend/scripts/create_cava_socios_rbac.py:47:            'descripcion': 'Gestión de inventario en custodia de terceros',
/app/backend/scripts/create_cava_socios_rbac.py:81:            'descripcion': 'Inventario de botellas en custodia',
/app/backend/scripts/create_cava_socios_tables.py:6:Tipo: Módulo principal (Inventario en custodia de terceros)
/app/backend/scripts/create_cava_socios_tables.py:168:            TipoCargo VARCHAR(50) NOT NULL,  -- SERVICIO_DESCORCHE, ALMACENAJE_MENSUAL, CONSUMO, EVENTO, OTRO
/app/backend/scripts/create_cava_socios_tables.py:209:            TarifaAlmacenajeMensual DECIMAL(18,2) DEFAULT 150,
/app/backend/scripts/create_cava_socios_tables.py:275:        print("  - CavaSocios_Botellas: Inventario en custodia")
/app/backend/scripts/validate_catalogo_sistemas_endpoints.py:32:TEST_EMAIL = "admin@inventario.com"
/app/backend/scripts/validate_encrypted_server_connectivity.py:10:    python validate_encrypted_server_connectivity.py --dry-run    # Solo inventario
/app/backend/scripts/validate_encrypted_server_connectivity.py:117:    """Obtiene inventario de servidores para probar."""
/app/backend/scripts/validate_encrypted_server_connectivity.py:459:        print("\n[DRY-RUN] Solo se mostrará inventario, no se ejecutarán pruebas\n")
/app/backend/scripts/validate_encrypted_server_connectivity.py:526:    """Imprime inventario de servidores de forma segura."""
/app/backend/scripts/validate_encrypted_server_connectivity.py:528:    print("INVENTARIO DE SERVIDORES A PROBAR")
/app/backend/scripts/validate_encrypted_server_connectivity.py:606:    parser.add_argument('--dry-run', action='store_true', help='Solo inventario, no ejecutar pruebas')
/app/backend/scripts/validate_encrypted_server_connectivity.py:633:    # 2. Obtener inventario
/app/backend/scripts/validate_encrypted_server_connectivity.py:634:    print("\n2. Obteniendo inventario de servidores...")
/app/backend/scripts/sync_response_cache_finops.py:172:        print(f"[FINOPS CACHED] Respuesta almacenada para {service_source}")
/app/backend/scripts/consolidado_general_sistema_comercial.py:11:             vistas consolidadas y procedimientos almacenados (SPs) de autocura.
/app/backend/scripts/consolidado_general_sistema_comercial.py:270:# Definición de Procedimientos Almacenados (SPs) de Autocura y Dashboard
/app/backend/scripts/consolidado_general_sistema_comercial.py:399:    ("Inventario", "inventario", "Package", "/inventario", 3, "OPERADOR_EDARSA"),
/app/backend/scripts/consolidado_general_sistema_comercial.py:494:        # 4. Crear procedimientos almacenados
/app/backend/scripts/consolidado_general_sistema_comercial.py:495:        execute_sql_batch(cursor, SQL_PROCEDURES, "PROCEDIMIENTOS ALMACENADOS")
/app/backend/scripts/sistema_menus_dinamicos.py:21:    ("Inventarios FinOps", "Inventarios FinOps", "Database", "costos-placeholder", 1, 4, "OPERADOR_EDARSA"),
/app/backend/scripts/validate_consultas_sql_endpoints_fase_4b.py:25:    "email": "admin@inventario.com",
/app/backend/scripts/consolidado_general_sistema_comercial_v2.py:10:             y procedimientos almacenados. Alimenta semillas iniciales de control y
/app/backend/scripts/consolidado_general_sistema_comercial_v2.py:45:    ("Inventarios FinOps", "Inventarios FinOps", "Database", "costos-placeholder", 1, 4, "OPERADOR_EDARSA"),
/app/backend/scripts/consolidado_general_sistema_comercial_v2.py:66:    ('C-9903', 'Carnes Supremas del Valle', 'Carnes del Valle', 'pedidos@carnesvalle.mx', '+52 55 8765-4321', 'SILVER')
/app/backend/scripts/create_scheduler_tables.py:18:CREATE_INVENTARIOS_PROCESADOS_SQL = """
/app/backend/scripts/create_scheduler_tables.py:19:-- Tabla para tracking de inventarios procesados automáticamente
/app/backend/scripts/create_scheduler_tables.py:20:IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Scheduler_InventariosProcesados' AND xtype='U')
/app/backend/scripts/create_scheduler_tables.py:22:    CREATE TABLE Scheduler_InventariosProcesados (
/app/backend/scripts/create_scheduler_tables.py:27:        AlmacenID VARCHAR(50) NOT NULL,
/app/backend/scripts/create_scheduler_tables.py:28:        FolioInventario VARCHAR(100) NOT NULL,
/app/backend/scripts/create_scheduler_tables.py:37:        CONSTRAINT UQ_Inventario_Clave UNIQUE (SistemaOrigen, ServerID, SucursalID, AlmacenID, FolioInventario),
/app/backend/scripts/create_scheduler_tables.py:38:        INDEX IX_Inventarios_Estado (Estado),
/app/backend/scripts/create_scheduler_tables.py:39:        INDEX IX_Inventarios_Server (ServerID),
/app/backend/scripts/create_scheduler_tables.py:40:        INDEX IX_Inventarios_Fecha (FechaDeteccion)
/app/backend/scripts/create_scheduler_tables.py:42:    PRINT 'Tabla Scheduler_InventariosProcesados creada';
/app/backend/scripts/create_scheduler_tables.py:46:    PRINT 'Tabla Scheduler_InventariosProcesados ya existe';
/app/backend/scripts/create_scheduler_tables.py:50:CREATE_PEDIDOS_PROCESADOS_SQL = """
/app/backend/scripts/create_scheduler_tables.py:51:-- Tabla para tracking de pedidos detectados automáticamente
/app/backend/scripts/create_scheduler_tables.py:52:IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Scheduler_PedidosProcesados' AND xtype='U')
/app/backend/scripts/create_scheduler_tables.py:54:    CREATE TABLE Scheduler_PedidosProcesados (
/app/backend/scripts/create_scheduler_tables.py:60:        FolioPedido VARCHAR(100) NOT NULL,
/app/backend/scripts/create_scheduler_tables.py:66:        CONSTRAINT UQ_Pedido_Clave UNIQUE (SistemaOrigen, ServerID, EmpresaID, FolioPedido),
/app/backend/scripts/create_scheduler_tables.py:67:        INDEX IX_Pedidos_Estado (Estado),
/app/backend/scripts/create_scheduler_tables.py:68:        INDEX IX_Pedidos_Server (ServerID),
/app/backend/scripts/create_scheduler_tables.py:69:        INDEX IX_Pedidos_Fecha (FechaDeteccion)
/app/backend/scripts/create_scheduler_tables.py:71:    PRINT 'Tabla Scheduler_PedidosProcesados creada';
/app/backend/scripts/create_scheduler_tables.py:75:    PRINT 'Tabla Scheduler_PedidosProcesados ya existe';
/app/backend/scripts/create_scheduler_tables.py:121:        print("\n--- Creando tabla Scheduler_InventariosProcesados ---")
/app/backend/scripts/create_scheduler_tables.py:122:        cursor.execute(CREATE_INVENTARIOS_PROCESADOS_SQL)
/app/backend/scripts/create_scheduler_tables.py:125:        print("\n--- Creando tabla Scheduler_PedidosProcesados ---")
/app/backend/scripts/create_scheduler_tables.py:126:        cursor.execute(CREATE_PEDIDOS_PROCESADOS_SQL)
/app/backend/scripts/create_workflow_tables.py:67:                'Workflow_Inventarios', 
/app/backend/scripts/create_workflow_tables.py:68:                'Tareas_Inventario', 
/app/backend/scripts/create_workflow_tables.py:70:                'Inventarios_SinAsignar',
/app/backend/scripts/create_workflow_tables.py:92:                   OR TABLE_NAME LIKE 'Inventarios_%'
/app/backend/scripts/solucion_cache_ventas.py:31:(JSON.parse) rechaza la memoria almacenada si no contiene actividad transaccional real.
/app/backend/scripts/validacion_propinas_tpv.py:151:    FROM movtoscaja mc
/app/backend/scripts/validacion_propinas_tpv.py:214:        FROM movtoscaja mc
/app/backend/scripts/validacion_propinas_tpv.py:274:    FROM movtoscaja mc
/app/backend/scripts/validacion_propinas_tpv.py:347:        ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
/app/backend/scripts/validacion_propinas_tpv.py:349:        ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
/app/backend/scripts/validacion_propinas_tpv.py:352:    FROM movtoscaja mc
/app/backend/scripts/validacion_propinas_tpv.py:556:FROM movtoscaja mc
/app/backend/scripts/run_historical_load_compras.py:7:- Inventarios Físicos
/app/backend/scripts/run_historical_load_compras.py:8:- Pedidos/Requisiciones
/app/backend/scripts/run_historical_load_compras.py:13:- SOFTRESTAURANT: Inventarios, Pedidos
/app/backend/scripts/run_historical_load_compras.py:14:- MANAGEMENTPRO: Inventarios, Pedidos, Facturas Proveedor
/app/backend/scripts/run_historical_load_compras.py:70:KPI_INVENTARIO = "INVENTARIO_FISICO"
/app/backend/scripts/run_historical_load_compras.py:71:KPI_PEDIDO = "PEDIDO"
/app/backend/scripts/run_historical_load_compras.py:175:# QUERIES - INVENTARIOS FÍSICOS
/app/backend/scripts/run_historical_load_compras.py:178:def query_inventarios_historico_mpro(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
/app/backend/scripts/run_historical_load_compras.py:179:    """Consulta inventarios físicos históricos de MPRO (PDA_Inventario)."""
/app/backend/scripts/run_historical_load_compras.py:182:    # MPRO usa PDA_Inventario para conteos de inventario
/app/backend/scripts/run_historical_load_compras.py:184:    IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'PDA_Inventario')
/app/backend/scripts/run_historical_load_compras.py:190:            '' as almacenes
/app/backend/scripts/run_historical_load_compras.py:191:        FROM PDA_Inventario I
/app/backend/scripts/run_historical_load_compras.py:194:            FROM PDA_Inventario_Detalle
/app/backend/scripts/run_historical_load_compras.py:221:                        "inv_almacenes": str(row[3] or '')[:500]
/app/backend/scripts/run_historical_load_compras.py:230:def query_inventarios_historico_sr(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
/app/backend/scripts/run_historical_load_compras.py:231:    """Consulta inventarios físicos históricos de SoftRestaurant (folioconteo)."""
/app/backend/scripts/run_historical_load_compras.py:242:        '' as almacenes
/app/backend/scripts/run_historical_load_compras.py:272:                        "inv_almacenes": str(row[3] or '')
/app/backend/scripts/run_historical_load_compras.py:285:# QUERIES - PEDIDOS
/app/backend/scripts/run_historical_load_compras.py:288:def query_pedidos_historico_mpro(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
/app/backend/scripts/run_historical_load_compras.py:289:    """Consulta requisiciones de compra históricos de MPRO (Requisicion_Compra)."""
/app/backend/scripts/run_historical_load_compras.py:292:    # MPRO usa Requisicion_Compra para pedidos internos
/app/backend/scripts/run_historical_load_compras.py:296:        COUNT(DISTINCT R.Rc_Folio) as pedidos_count,
/app/backend/scripts/run_historical_load_compras.py:299:    FROM Requisicion_Compra R
/app/backend/scripts/run_historical_load_compras.py:320:                    "ped_pedidos_count": int(row[1] or 0),
/app/backend/scripts/run_historical_load_compras.py:331:def query_pedidos_historico_sr(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
/app/backend/scripts/run_historical_load_compras.py:332:    """Consulta pedidos históricos de SoftRestaurant (tabla: pedidos)."""
/app/backend/scripts/run_historical_load_compras.py:337:    # SoftRestaurant usa tabla 'pedidos' con columna 'fechacaptura'
/app/backend/scripts/run_historical_load_compras.py:341:        COUNT(DISTINCT P.idpedido) as pedidos_count,
/app/backend/scripts/run_historical_load_compras.py:344:    FROM pedidos P
/app/backend/scripts/run_historical_load_compras.py:367:                        "ped_pedidos_count": int(row[1] or 0),
/app/backend/scripts/run_historical_load_compras.py:527:    """Consulta órdenes de compra históricas de SoftRestaurant (tabla: ordenescompra)."""
/app/backend/scripts/run_historical_load_compras.py:532:    # SoftRestaurant usa tabla 'ordenescompra' con columna 'fechacaptura'
/app/backend/scripts/run_historical_load_compras.py:536:        COUNT(DISTINCT O.idordencompra) as ordenes_count,
/app/backend/scripts/run_historical_load_compras.py:539:    FROM ordenescompra O
/app/backend/scripts/run_historical_load_compras.py:621:        if kpi_tipo == KPI_INVENTARIO:
/app/backend/scripts/run_historical_load_compras.py:623:                data = query_inventarios_historico_mpro(server, fecha_inicio, fecha_fin)
/app/backend/scripts/run_historical_load_compras.py:625:                data = query_inventarios_historico_sr(server, fecha_inicio, fecha_fin)
/app/backend/scripts/run_historical_load_compras.py:626:        elif kpi_tipo == KPI_PEDIDO:
/app/backend/scripts/run_historical_load_compras.py:628:                data = query_pedidos_historico_mpro(server, fecha_inicio, fecha_fin)
/app/backend/scripts/run_historical_load_compras.py:630:                data = query_pedidos_historico_sr(server, fecha_inicio, fecha_fin)
/app/backend/scripts/run_historical_load_compras.py:745:                       choices=['INVENTARIO_FISICO', 'PEDIDO', 'ORDEN_COMPRA', 'ENTRADA_COMPRA', 'ALL'], 
/app/backend/scripts/run_historical_load_compras.py:796:        kpi_tipos = [KPI_INVENTARIO, KPI_PEDIDO, KPI_ORDEN_COMPRA, KPI_ENTRADA]
/app/backend/tests/test_notificaciones_whatsapp.py:98:        """GET /api/v2/notificaciones/config?modulo=inventarios - filter by module"""
/app/backend/tests/test_notificaciones_whatsapp.py:99:        response = requests.get(f"{BASE_URL}/api/v2/notificaciones/config?modulo=inventarios")
/app/backend/tests/test_notificaciones_whatsapp.py:104:            assert item["modulo"] == "inventarios", f"Expected modulo=inventarios, got {item['modulo']}"
/app/backend/tests/test_notificaciones_whatsapp.py:178:            "modulo": "inventarios",
/app/backend/tests/test_notificaciones_whatsapp.py:182:            "template_codigo": "inventarios_asignacion_tarea",
/app/backend/tests/test_notificaciones_whatsapp.py:206:            "modulo": "inventarios",
/app/backend/tests/test_notificaciones_whatsapp.py:210:            "template_codigo": "inventarios_asignacion_tarea"
/app/backend/tests/test_notificaciones_whatsapp.py:340:            "codigo": "inventarios_asignacion_tarea",  # Already exists
/app/backend/tests/test_notificaciones_whatsapp.py:405:            "template_codigo": "inventarios_asignacion_tarea",
/app/backend/tests/test_notificaciones_whatsapp.py:431:            "template_codigo": "inventarios_sla_vencido",
/app/backend/tests/test_notificaciones_whatsapp.py:453:            "template_codigo": "inventarios_sla_por_vencer",
/app/backend/tests/test_notificaciones_whatsapp.py:477:            "template_codigo": "inventarios_asignacion_tarea",
/app/backend/tests/test_notificaciones_whatsapp.py:514:            "template_codigo": "inventarios_sla_escalado",
/app/backend/tests/test_notificaciones_whatsapp.py:546:            "template_codigo": "inventarios_asignacion_tarea",
/app/backend/tests/test_notificaciones_whatsapp.py:654:        """GET /api/v2/notificaciones/stats?modulo=inventarios"""
/app/backend/tests/test_notificaciones_whatsapp.py:655:        response = requests.get(f"{BASE_URL}/api/v2/notificaciones/stats?modulo=inventarios")
/app/backend/tests/test_notificaciones_whatsapp.py:710:            "inventarios_asignacion_tarea",
/app/backend/tests/test_notificaciones_whatsapp.py:711:            "inventarios_sla_por_vencer",
/app/backend/tests/test_notificaciones_whatsapp.py:712:            "inventarios_sla_vencido",
/app/backend/tests/test_notificaciones_whatsapp.py:713:            "inventarios_sla_escalado",
/app/backend/tests/test_notificaciones_whatsapp.py:714:            "inventarios_justificacion_rechazada",
/app/backend/tests/test_notificaciones_whatsapp.py:715:            "inventarios_decision_auditoria",
/app/backend/tests/test_notificaciones_whatsapp.py:716:            "inventarios_cierre_workflow"
/app/backend/tests/test_notificaciones_whatsapp.py:737:            "template_codigo": "inventarios_asignacion_tarea",
/app/backend/tests/test_notificaciones_whatsapp.py:750:            "template_codigo": "inventarios_asignacion_tarea",
/app/backend/tests/test_notificaciones_whatsapp.py:763:            "template_codigo": "inventarios_asignacion_tarea",
/app/backend/tests/test_notificaciones_whatsapp.py:776:            "template_codigo": "inventarios_asignacion_tarea",
/app/backend/tests/test_notificaciones_whatsapp.py:789:            "template_codigo": "inventarios_asignacion_tarea",
/app/backend/tests/test_automatizacion_compras_fase4.py:4:Tests para el detector automático de pedidos y tareas operativas.
/app/backend/tests/test_automatizacion_compras_fase4.py:10:- GET /api/v2/automatizaciones/operativas/compras/pedidos-procesados
/app/backend/tests/test_automatizacion_compras_fase4.py:16:- pedidos_procesados_automatizacion
/app/backend/tests/test_automatizacion_compras_fase4.py:39:    """Tests para Fase 4.1 y 4.2 - Detector de Pedidos y Tareas Operativas"""
/app/backend/tests/test_automatizacion_compras_fase4.py:60:    # FASE 4.1: DETECTOR DE PEDIDOS - ESTADO
/app/backend/tests/test_automatizacion_compras_fase4.py:100:    # FASE 4.1: DETECTOR DE PEDIDOS - EJECUCIÓN MANUAL
/app/backend/tests/test_automatizacion_compras_fase4.py:122:            "pedidos_detectados",
/app/backend/tests/test_automatizacion_compras_fase4.py:123:            "pedidos_nuevos",
/app/backend/tests/test_automatizacion_compras_fase4.py:222:    # FASE 4.1: PEDIDOS PROCESADOS (ANTI-DUPLICADOS)
/app/backend/tests/test_automatizacion_compras_fase4.py:225:    def test_pedidos_procesados_returns_200(self):
/app/backend/tests/test_automatizacion_compras_fase4.py:226:        """GET /pedidos-procesados - Debe retornar lista de pedidos procesados"""
/app/backend/tests/test_automatizacion_compras_fase4.py:228:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/pedidos-procesados"
/app/backend/tests/test_automatizacion_compras_fase4.py:235:        assert "pedidos" in data, "Missing 'pedidos' in response"
/app/backend/tests/test_automatizacion_compras_fase4.py:236:        assert isinstance(data["pedidos"], list), "pedidos should be a list"
/app/backend/tests/test_automatizacion_compras_fase4.py:238:        print(f"✓ Pedidos procesados: {data['total']} registros")
/app/backend/tests/test_automatizacion_compras_fase4.py:240:    def test_pedidos_procesados_filter_by_empresa(self):
/app/backend/tests/test_automatizacion_compras_fase4.py:241:        """GET /pedidos-procesados - Debe filtrar por empresa_id"""
/app/backend/tests/test_automatizacion_compras_fase4.py:243:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/pedidos-procesados",
/app/backend/tests/test_automatizacion_compras_fase4.py:250:        # Todos los pedidos deben ser de la empresa filtrada
/app/backend/tests/test_automatizacion_compras_fase4.py:251:        for pedido in data["pedidos"]:
/app/backend/tests/test_automatizacion_compras_fase4.py:252:            if "empresa_id" in pedido:
/app/backend/tests/test_automatizacion_compras_fase4.py:253:                assert pedido["empresa_id"] == "empresa_test", f"Pedido has wrong empresa_id: {pedido['empresa_id']}"
/app/backend/tests/test_automatizacion_compras_fase4.py:255:        print(f"✓ Pedidos filtrados por empresa: {data['total']}")
/app/backend/tests/test_automatizacion_compras_fase4.py:257:    def test_pedidos_procesados_filter_by_estado(self):
/app/backend/tests/test_automatizacion_compras_fase4.py:258:        """GET /pedidos-procesados - Debe filtrar por estado"""
/app/backend/tests/test_automatizacion_compras_fase4.py:260:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/pedidos-procesados",
/app/backend/tests/test_automatizacion_compras_fase4.py:261:            params={"estado": "PENDIENTE_INVENTARIO"}
/app/backend/tests/test_automatizacion_compras_fase4.py:267:        # Todos los pedidos deben tener el estado filtrado
/app/backend/tests/test_automatizacion_compras_fase4.py:268:        for pedido in data["pedidos"]:
/app/backend/tests/test_automatizacion_compras_fase4.py:269:            if "estado" in pedido:
/app/backend/tests/test_automatizacion_compras_fase4.py:270:                assert pedido["estado"] == "PENDIENTE_INVENTARIO", f"Pedido has wrong estado: {pedido['estado']}"
/app/backend/tests/test_automatizacion_compras_fase4.py:272:        print(f"✓ Pedidos filtrados por estado: {data['total']}")
/app/backend/tests/test_automatizacion_compras_fase4.py:274:    def test_pedidos_procesados_structure(self):
/app/backend/tests/test_automatizacion_compras_fase4.py:275:        """GET /pedidos-procesados - Pedidos deben tener estructura correcta"""
/app/backend/tests/test_automatizacion_compras_fase4.py:277:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/pedidos-procesados",
/app/backend/tests/test_automatizacion_compras_fase4.py:284:        if data["pedidos"]:
/app/backend/tests/test_automatizacion_compras_fase4.py:285:            pedido = data["pedidos"][0]
/app/backend/tests/test_automatizacion_compras_fase4.py:287:            assert "pedido_folio" in pedido, "Pedido missing 'pedido_folio'"
/app/backend/tests/test_automatizacion_compras_fase4.py:288:            assert "origen" in pedido, "Pedido missing 'origen'"
/app/backend/tests/test_automatizacion_compras_fase4.py:289:            assert "fecha_procesado" in pedido, "Pedido missing 'fecha_procesado'"
/app/backend/tests/test_automatizacion_compras_fase4.py:292:            has_identifier = "empresa_id" in pedido or "server_id" in pedido
/app/backend/tests/test_automatizacion_compras_fase4.py:293:            assert has_identifier, "Pedido missing both 'empresa_id' and 'server_id'"
/app/backend/tests/test_automatizacion_compras_fase4.py:295:            identifier = pedido.get('empresa_id') or pedido.get('server_id')
/app/backend/tests/test_automatizacion_compras_fase4.py:296:            estado = pedido.get('estado', 'N/A')
/app/backend/tests/test_automatizacion_compras_fase4.py:297:            print(f"✓ Pedido estructura: id={identifier}, folio={pedido['pedido_folio']}, estado={estado}")
/app/backend/tests/test_automatizacion_compras_fase4.py:299:            print("⚠ No hay pedidos procesados")
/app/backend/tests/test_automatizacion_compras_fase4.py:369:                "pedido_folio", "titulo", "descripcion",
/app/backend/tests/test_automatizacion_compras_fase4.py:375:            # Verificar que tipo es CAPTURA_INVENTARIO
/app/backend/tests/test_automatizacion_compras_fase4.py:376:            assert tarea["tipo"] == "CAPTURA_INVENTARIO", f"Expected tipo=CAPTURA_INVENTARIO, got {tarea['tipo']}"
/app/backend/tests/test_automatizacion_compras_fase4.py:477:            ("GET", "/api/v2/automatizaciones/operativas/compras/pedidos-procesados"),
/app/backend/tests/test_inventory_analysis_filters.py:188:        # Get sample sucursal and almacen
/app/backend/tests/test_inventory_analysis_filters.py:199:        # Get almacenes for sucursal
/app/backend/tests/test_inventory_analysis_filters.py:200:        almacenes_response = requests.get(
/app/backend/tests/test_inventory_analysis_filters.py:201:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes",
/app/backend/tests/test_inventory_analysis_filters.py:205:        almacenes = almacenes_response.json()
/app/backend/tests/test_inventory_analysis_filters.py:206:        if not almacenes:
/app/backend/tests/test_inventory_analysis_filters.py:207:            pytest.skip("No almacenes available")
/app/backend/tests/test_inventory_analysis_filters.py:209:        almacen = almacenes[0]["nombre"]
/app/backend/tests/test_inventory_analysis_filters.py:211:        # Get inventarios
/app/backend/tests/test_inventory_analysis_filters.py:212:        inventarios_response = requests.get(
/app/backend/tests/test_inventory_analysis_filters.py:213:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/inventarios",
/app/backend/tests/test_inventory_analysis_filters.py:214:            params={"sucursal_id": sucursales[0]["id"], "almacen_id": almacenes[0]["id"]},
/app/backend/tests/test_inventory_analysis_filters.py:217:        inventarios = inventarios_response.json()
/app/backend/tests/test_inventory_analysis_filters.py:218:        if len(inventarios) < 2:
/app/backend/tests/test_inventory_analysis_filters.py:219:            pytest.skip("Not enough inventarios for test")
/app/backend/tests/test_inventory_analysis_filters.py:221:        # Select first and last inventario
/app/backend/tests/test_inventory_analysis_filters.py:222:        folio_inicial = inventarios[-1]["folio"]  # Oldest
/app/backend/tests/test_inventory_analysis_filters.py:223:        folio_final = inventarios[0]["folio"]  # Newest
/app/backend/tests/test_inventory_analysis_filters.py:224:        fecha_ini = inventarios[-1].get("fecha", "2024-01-01")
/app/backend/tests/test_inventory_analysis_filters.py:225:        fecha_fin = inventarios[0].get("fecha", "2024-12-31")
/app/backend/tests/test_inventory_analysis_filters.py:231:            "almacen": almacen,
/app/backend/tests/test_inventory_analysis_filters.py:290:        almacenes_response = requests.get(
/app/backend/tests/test_inventory_analysis_filters.py:291:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes",
/app/backend/tests/test_inventory_analysis_filters.py:295:        almacenes = almacenes_response.json()
/app/backend/tests/test_inventory_analysis_filters.py:296:        if not almacenes:
/app/backend/tests/test_inventory_analysis_filters.py:297:            pytest.skip("No almacenes available")
/app/backend/tests/test_inventory_analysis_filters.py:299:        almacen = almacenes[0]["nombre"]
/app/backend/tests/test_inventory_analysis_filters.py:300:        almacen_id = almacenes[0]["id"]
/app/backend/tests/test_inventory_analysis_filters.py:302:        inventarios_response = requests.get(
/app/backend/tests/test_inventory_analysis_filters.py:303:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/inventarios",
/app/backend/tests/test_inventory_analysis_filters.py:304:            params={"sucursal_id": sucursal_id, "almacen_id": almacen_id},
/app/backend/tests/test_inventory_analysis_filters.py:307:        inventarios = inventarios_response.json()
/app/backend/tests/test_inventory_analysis_filters.py:308:        if len(inventarios) < 2:
/app/backend/tests/test_inventory_analysis_filters.py:309:            pytest.skip("Not enough inventarios")
/app/backend/tests/test_inventory_analysis_filters.py:311:        folio_inicial = inventarios[-1]["folio"]
/app/backend/tests/test_inventory_analysis_filters.py:312:        folio_final = inventarios[0]["folio"]
/app/backend/tests/test_inventory_analysis_filters.py:313:        fecha_ini = inventarios[-1].get("fecha", "2024-01-01")
/app/backend/tests/test_inventory_analysis_filters.py:314:        fecha_fin = inventarios[0].get("fecha", "2024-12-31")
/app/backend/tests/test_inventory_analysis_filters.py:319:            "almacen": almacen,
/app/backend/tests/test_config.py:24:    TEST_ADMIN_EMAIL = os.getenv('TEST_ADMIN_EMAIL', 'admin@inventario.com')
/app/backend/tests/test_equivalencia_fase1a.py:4:CAB-003: Automatización de Análisis de Inventarios
/app/backend/tests/test_config_asignaciones.py:10:- GET /api/config-asignaciones/almacenes/{unidad_id} - Get warehouses from local catalog
/app/backend/tests/test_config_asignaciones.py:179:    # TEST: GET /api/config-asignaciones/almacenes/{unidad_id}
/app/backend/tests/test_config_asignaciones.py:182:    def test_08_get_almacenes_success(self):
/app/backend/tests/test_config_asignaciones.py:193:        response = self.session.get(f"{BASE_URL}/api/config-asignaciones/almacenes/{unidad_id}")
/app/backend/tests/test_config_asignaciones.py:201:        # First option should always be "(Todos los almacenes)"
/app/backend/tests/test_config_asignaciones.py:206:        print(f"✓ Got {len(data['data'])} almacenes for {unidades[0]['nombre']}")
/app/backend/tests/test_config_asignaciones.py:208:    def test_09_get_almacenes_invalid_unidad(self):
/app/backend/tests/test_config_asignaciones.py:213:        response = self.session.get(f"{BASE_URL}/api/config-asignaciones/almacenes/{fake_id}")
/app/backend/tests/test_config_asignaciones.py:238:        existing_unidades = {c["unidad_negocio_id"] for c in existing if c["almacen_id"] == ""}
/app/backend/tests/test_config_asignaciones.py:256:            "almacen_id": "",  # Todos los almacenes
/app/backend/tests/test_config_asignaciones.py:299:            "almacen_id": config["almacen_id"],
/app/backend/tests/test_config_asignaciones.py:320:            "almacen_id": "",
/app/backend/tests/test_config_asignaciones.py:472:        existing_unidades = {c["unidad_negocio_id"] for c in existing if c["almacen_id"] == ""}
/app/backend/tests/test_config_asignaciones.py:490:                "almacen_id": "",
/app/backend/tests/test_auth.py:70:        assert data["email"] == "admin@inventario.com"
/app/backend/tests/test_sucursales_permissions.py:66:        """Admin login with admin@inventario.com / admin123"""
/app/backend/tests/test_sucursales_permissions.py:216:                "almacen": "ALMACEN CENTRAL",
/app/backend/tests/test_simulacion_controlada.py:138:        detectar_inventarios_soft,
/app/backend/tests/test_simulacion_controlada.py:139:        detectar_inventarios_mpro,
/app/backend/tests/test_simulacion_controlada.py:140:        InventarioDetectado
/app/backend/tests/test_simulacion_controlada.py:172:def print_inventario(inv: dict, index: int):
/app/backend/tests/test_simulacion_controlada.py:173:    """Imprime un inventario detectado de forma legible."""
/app/backend/tests/test_simulacion_controlada.py:174:    print(f"\n  [{index}] {inv['sistema_origen']} - {inv['folio_inventario']}")
/app/backend/tests/test_simulacion_controlada.py:175:    print(f"      Fecha: {inv['fecha_inventario']}")
/app/backend/tests/test_simulacion_controlada.py:176:    print(f"      Almacén: {inv['almacen_id']} ({inv.get('almacen_nombre', 'N/A')})")
/app/backend/tests/test_simulacion_controlada.py:180:        print(f"      Estado origen: {inv['estado_inventario_origen']}")
/app/backend/tests/test_simulacion_controlada.py:200:    print(f"  {'almacen_id':<30} │ {inv['almacen_id']}")
/app/backend/tests/test_simulacion_controlada.py:202:    print(f"  {'folio_inventario':<30} │ {inv['folio_inventario']}")
/app/backend/tests/test_simulacion_controlada.py:203:    print(f"  {'fecha_inventario':<30} │ {inv['fecha_inventario']}")
/app/backend/tests/test_simulacion_controlada.py:204:    print(f"  {'estado_inventario_origen':<30} │ {inv['estado_inventario_origen'] or 'NULL'}")
/app/backend/tests/test_simulacion_controlada.py:254:            detectados = detectar_inventarios_soft(
/app/backend/tests/test_simulacion_controlada.py:258:            print(f"  Inventarios detectados: {len(detectados)}")
/app/backend/tests/test_simulacion_controlada.py:262:                print_inventario(inv_dict, i)
/app/backend/tests/test_simulacion_controlada.py:294:            detectados = detectar_inventarios_mpro(
/app/backend/tests/test_simulacion_controlada.py:298:            print(f"  Inventarios detectados: {len(detectados)}")
/app/backend/tests/test_simulacion_controlada.py:302:                print_inventario(inv_dict, i)
/app/backend/tests/test_simulacion_controlada.py:324:    Total inventarios detectados: {total}
/app/backend/tests/test_simulacion_controlada.py:340:        'inventarios': todos_detectados
/app/backend/tests/test_simulacion_controlada.py:364:    candidatos = [i for i in resultado_dry['inventarios'] 
/app/backend/tests/test_simulacion_controlada.py:385:        print(f"  [{i:2d}] {sistema_short} | {c['folio_inventario']:<15} | {c['fecha_inventario']} | Alm: {c['almacen_id']}")
/app/backend/tests/test_simulacion_controlada.py:416:        inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:418:        inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:419:        inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:420:        inv['estado_inventario_origen']
/app/backend/tests/test_simulacion_controlada.py:435:        inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:437:        inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:438:        inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:439:        inv['estado_inventario_origen']
/app/backend/tests/test_simulacion_controlada.py:484:        inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:486:        inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:487:        inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:488:        inv['estado_inventario_origen'],
/app/backend/tests/test_simulacion_controlada.py:657:        i for i in resultado_dry['inventarios'] 
/app/backend/tests/test_simulacion_controlada.py:676:    Almacén:        {inv['almacen_id']} ({inv.get('almacen_nombre', 'N/A')})
/app/backend/tests/test_simulacion_controlada.py:677:    Folio:          {inv['folio_inventario']}
/app/backend/tests/test_simulacion_controlada.py:678:    Fecha:          {inv['fecha_inventario']}
/app/backend/tests/test_simulacion_controlada.py:687:        inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:689:        inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:690:        inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:691:        inv['estado_inventario_origen']
/app/backend/tests/test_simulacion_controlada.py:708:    print(f"  {'almacen_id':<30} │ {inv['almacen_id']}")
/app/backend/tests/test_simulacion_controlada.py:710:    print(f"  {'folio_inventario':<30} │ {inv['folio_inventario']}")
/app/backend/tests/test_simulacion_controlada.py:711:    print(f"  {'fecha_inventario':<30} │ {inv['fecha_inventario']}")
/app/backend/tests/test_simulacion_controlada.py:712:    print(f"  {'estado_inventario_origen':<30} │ {inv['estado_inventario_origen'] or 'NULL'}")
/app/backend/tests/test_simulacion_controlada.py:723:    print("   automatizacion_inventarios_folios_procesados")
/app/backend/tests/test_simulacion_controlada.py:750:            inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:752:            inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:753:            inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:754:            inv['estado_inventario_origen'],
/app/backend/tests/test_simulacion_controlada.py:779:    print(f"   Folio: {inv['folio_inventario']}")
/app/backend/tests/test_simulacion_controlada.py:780:    print(f"   Fecha: {inv['fecha_inventario']}")
/app/backend/tests/test_simulacion_controlada.py:781:    print(f"   Almacén: {inv['almacen_id']}")
/app/backend/tests/test_simulacion_controlada.py:816:            inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:818:            inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:819:            inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:820:            inv['estado_inventario_origen'],
/app/backend/tests/test_simulacion_controlada.py:956:    print(f"│  {'almacen_id':<28} │ {inv['almacen_id']:<45} │")
/app/backend/tests/test_simulacion_controlada.py:958:    print(f"│  {'folio_inventario':<28} │ {inv['folio_inventario']:<45} │")
/app/backend/tests/test_simulacion_controlada.py:959:    print(f"│  {'fecha_inventario':<28} │ {str(inv['fecha_inventario']):<45} │")
/app/backend/tests/test_simulacion_controlada.py:960:    print(f"│  {'estado_inventario_origen':<28} │ {(inv['estado_inventario_origen'] or 'NULL'):<45} │")
/app/backend/tests/test_simulacion_controlada.py:1025:        i for i in resultado_dry['inventarios'] 
/app/backend/tests/test_simulacion_controlada.py:1071:            inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:1073:            inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1074:            inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1075:            inv['estado_inventario_origen']
/app/backend/tests/test_simulacion_controlada.py:1079:            'inventario': inv,
/app/backend/tests/test_simulacion_controlada.py:1123:        inv = candidato['inventario']
/app/backend/tests/test_simulacion_controlada.py:1131:            inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:1133:            inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1134:            inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1135:            inv['estado_inventario_origen']
/app/backend/tests/test_simulacion_controlada.py:1145:                'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1161:                        'folio': candidatos_validados[j-1]['inventario']['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1170:                'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1189:                inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:1191:                inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1192:                inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1193:                inv['estado_inventario_origen'],
/app/backend/tests/test_simulacion_controlada.py:1201:                    'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1208:                    'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1216:                        'folio': candidatos_validados[j-1]['inventario']['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1225:                'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1233:                    'folio': candidatos_validados[j-1]['inventario']['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1313:    print(f"│  {'almacen_id':<28} │ {inv['almacen_id']:<45} │")
/app/backend/tests/test_simulacion_controlada.py:1315:    print(f"│  {'folio_inventario':<28} │ {inv['folio_inventario']:<45} │")
/app/backend/tests/test_simulacion_controlada.py:1316:    print(f"│  {'fecha_inventario':<28} │ {str(inv['fecha_inventario']):<45} │")
/app/backend/tests/test_simulacion_controlada.py:1317:    print(f"│  {'estado_inventario_origen':<28} │ {(inv['estado_inventario_origen'] or 'NULL'):<45} │")
/app/backend/tests/test_simulacion_controlada.py:1383:        i for i in resultado_dry['inventarios'] 
/app/backend/tests/test_simulacion_controlada.py:1427:        inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:1429:        inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1430:        inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1431:        inv['estado_inventario_origen']
/app/backend/tests/test_simulacion_controlada.py:1465:        inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:1467:        inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1468:        inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1469:        inv['estado_inventario_origen']
/app/backend/tests/test_simulacion_controlada.py:1503:            inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:1505:            inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1506:            inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1507:            inv['estado_inventario_origen'],
/app/backend/tests/test_simulacion_controlada.py:1536:      • Registro 1/1: {inv['folio_inventario']} → procesado_id: {procesado_id}
/app/backend/tests/test_simulacion_controlada.py:1540:      • Almacén: {inv['almacen_id']}
/app/backend/tests/test_simulacion_controlada.py:1542:      • Estado origen: {inv['estado_inventario_origen']}
/app/backend/tests/test_simulacion_controlada.py:1598:    print(f"│  {'almacen_id':<28} │ {inv['almacen_id']:<45} │")
/app/backend/tests/test_simulacion_controlada.py:1599:    almacen_nombre = inv.get('almacen_nombre', 'N/A')[:40]
/app/backend/tests/test_simulacion_controlada.py:1600:    print(f"│  {'almacen_nombre':<28} │ {almacen_nombre:<45} │")
/app/backend/tests/test_simulacion_controlada.py:1601:    print(f"│  {'folio_inventario':<28} │ {inv['folio_inventario']:<45} │")
/app/backend/tests/test_simulacion_controlada.py:1602:    print(f"│  {'fecha_inventario':<28} │ {str(inv['fecha_inventario']):<45} │")
/app/backend/tests/test_simulacion_controlada.py:1669:        i for i in resultado_dry['inventarios'] 
/app/backend/tests/test_simulacion_controlada.py:1716:            inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:1718:            inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1719:            inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1720:            inv['estado_inventario_origen']
/app/backend/tests/test_simulacion_controlada.py:1724:            'inventario': inv,
/app/backend/tests/test_simulacion_controlada.py:1770:        inv = candidato['inventario']
/app/backend/tests/test_simulacion_controlada.py:1778:            inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:1780:            inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1781:            inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1782:            inv['estado_inventario_origen']
/app/backend/tests/test_simulacion_controlada.py:1792:                'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1808:                        'folio': candidatos_validados[j-1]['inventario']['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1817:                'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1836:                inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:1838:                inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1839:                inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1840:                inv['estado_inventario_origen'],
/app/backend/tests/test_simulacion_controlada.py:1848:                    'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1849:                    'almacen': inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:1857:                    'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1865:                        'folio': candidatos_validados[j-1]['inventario']['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1876:                'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1884:                    'folio': candidatos_validados[j-1]['inventario']['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:1908:        print(f"      • Registro {r['numero']}: Folio {r['folio']}, Almacén {r['almacen']} → procesado_id: {r['procesado_id']}")
/app/backend/tests/test_simulacion_controlada.py:1971:    print(f"│  {'almacen_id':<28} │ {inv['almacen_id']:<45} │")
/app/backend/tests/test_simulacion_controlada.py:1972:    almacen_nombre = inv.get('almacen_nombre', 'N/A')[:40]
/app/backend/tests/test_simulacion_controlada.py:1973:    print(f"│  {'almacen_nombre':<28} │ {almacen_nombre:<45} │")
/app/backend/tests/test_simulacion_controlada.py:1976:    print(f"│  {'folio_inventario':<28} │ {inv['folio_inventario']:<45} │")
/app/backend/tests/test_simulacion_controlada.py:1977:    print(f"│  {'fecha_inventario':<28} │ {str(inv['fecha_inventario']):<45} │")
/app/backend/tests/test_simulacion_controlada.py:1978:    estado_origen = inv.get('estado_inventario_origen') or 'NULL'
/app/backend/tests/test_simulacion_controlada.py:1979:    print(f"│  {'estado_inventario_origen':<28} │ {estado_origen:<45} │")
/app/backend/tests/test_simulacion_controlada.py:2047:        i for i in resultado_dry['inventarios'] 
/app/backend/tests/test_simulacion_controlada.py:2083:        print(f"   Folio: {inv['folio_inventario']}")
/app/backend/tests/test_simulacion_controlada.py:2085:        print(f"   Almacén: {inv['almacen_id']} ({inv.get('almacen_nombre', 'N/A')})")
/app/backend/tests/test_simulacion_controlada.py:2097:            inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:2099:            inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2100:            inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2101:            inv['estado_inventario_origen']
/app/backend/tests/test_simulacion_controlada.py:2105:            'inventario': inv,
/app/backend/tests/test_simulacion_controlada.py:2151:        inv = candidato['inventario']
/app/backend/tests/test_simulacion_controlada.py:2159:            inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:2161:            inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2162:            inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2163:            inv['estado_inventario_origen']
/app/backend/tests/test_simulacion_controlada.py:2173:                'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2190:                        'folio': candidatos_validados[j-1]['inventario']['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2191:                        'sucursal': candidatos_validados[j-1]['inventario']['sucursal_id'],
/app/backend/tests/test_simulacion_controlada.py:2200:                'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2220:                inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:2222:                inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2223:                inv['fecha_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2224:                inv['estado_inventario_origen'],
/app/backend/tests/test_simulacion_controlada.py:2232:                    'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2234:                    'almacen': inv['almacen_id'],
/app/backend/tests/test_simulacion_controlada.py:2243:                    'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2252:                        'folio': candidatos_validados[j-1]['inventario']['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2253:                        'sucursal': candidatos_validados[j-1]['inventario']['sucursal_id'],
/app/backend/tests/test_simulacion_controlada.py:2264:                'folio': inv['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2273:                    'folio': candidatos_validados[j-1]['inventario']['folio_inventario'],
/app/backend/tests/test_simulacion_controlada.py:2274:                    'sucursal': candidatos_validados[j-1]['inventario']['sucursal_id'],
/app/backend/tests/test_simulacion_controlada.py:2298:        print(f"      • Registro {r['numero']}: Folio {r['folio']}, Sucursal {r['sucursal']}, Almacén {r['almacen']}")
/app/backend/tests/test_mpro_inventory_analysis.py:23:TEST_ALMACEN = "ALMACEN GENERAL"
/app/backend/tests/test_mpro_inventory_analysis.py:82:    def test_mpro_almacenes_available(self, auth_headers):
/app/backend/tests/test_mpro_inventory_analysis.py:83:        """Verify ALMACEN GENERAL is available for QUERETARO"""
/app/backend/tests/test_mpro_inventory_analysis.py:85:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes",
/app/backend/tests/test_mpro_inventory_analysis.py:90:        almacenes = response.json()
/app/backend/tests/test_mpro_inventory_analysis.py:91:        almacen_general = [a for a in almacenes if "ALMACEN GENERAL" in a["nombre"]]
/app/backend/tests/test_mpro_inventory_analysis.py:92:        assert len(almacen_general) > 0, "ALMACEN GENERAL not found"
/app/backend/tests/test_mpro_inventory_analysis.py:93:        print(f"✅ Found {len(almacenes)} almacenes, including ALMACEN GENERAL")
/app/backend/tests/test_mpro_inventory_analysis.py:108:                "almacen": TEST_ALMACEN,
/app/backend/tests/test_mpro_inventory_analysis.py:221:    def test_softrestaurant_almacenes_available(self, auth_headers):
/app/backend/tests/test_mpro_inventory_analysis.py:222:        """Verify SoftRestaurant almacenes are available"""
/app/backend/tests/test_mpro_inventory_analysis.py:224:            f"{BASE_URL}/api/servers/{self.SOFTRESTAURANT_SERVER_ID}/almacenes-softrestaurant",
/app/backend/tests/test_mpro_inventory_analysis.py:228:        almacenes = response.json()
/app/backend/tests/test_mpro_inventory_analysis.py:229:        assert len(almacenes) > 0, "SoftRestaurant should have almacenes"
/app/backend/tests/test_mpro_inventory_analysis.py:230:        print(f"✅ SoftRestaurant has {len(almacenes)} almacenes")
/app/backend/tests/test_mpro_inventory_analysis.py:232:    def test_softrestaurant_inventarios_available(self, auth_headers):
/app/backend/tests/test_mpro_inventory_analysis.py:233:        """Verify SoftRestaurant inventarios are available"""
/app/backend/tests/test_mpro_inventory_analysis.py:235:            f"{BASE_URL}/api/servers/{self.SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_mpro_inventory_analysis.py:237:            params={"almacen_id": "001"}  # 001 BODEGA
/app/backend/tests/test_mpro_inventory_analysis.py:240:        inventarios = response.json()
/app/backend/tests/test_mpro_inventory_analysis.py:241:        assert len(inventarios) > 0, "SoftRestaurant should have inventarios"
/app/backend/tests/test_mpro_inventory_analysis.py:242:        print(f"✅ SoftRestaurant has {len(inventarios)} inventarios")
/app/backend/tests/test_mpro_inventory_analysis.py:252:                "almacen": "001 BODEGA",
/app/backend/tests/test_dashboard_servers.py:2:Backend API tests for Sistema de Análisis de Inventarios Dashboard
/app/backend/tests/test_dashboard_servers.py:152:                "precision_inventario",
/app/backend/tests/test_cargos_economicos.py:297:            "almacen_id": "ALM-TEST-CARGO",
/app/backend/tests/test_cargos_economicos.py:298:            "almacen_nombre": "Almacén Test Cargos",
/app/backend/tests/test_e2e_flujo_completo.py:117:            "almacen_id": f"ALM-E2E-{str(uuid.uuid4())[:6]}",
/app/backend/tests/test_e2e_flujo_completo.py:118:            "almacen_nombre": "Almacén E2E Test",
/app/backend/tests/test_e2e_flujo_completo.py:147:            ("workflow_inventarios", {"sucursal_id": {"$regex": "SUC-E2E"}}),
/app/backend/tests/test_e2e_flujo_completo.py:172:        - Este método llama a _ejecutar_auditoria() → _crear_workflow_inventario()
/app/backend/tests/test_e2e_flujo_completo.py:173:        - _crear_workflow_inventario() crea el workflow en workflow_inventarios
/app/backend/tests/test_e2e_flujo_completo.py:187:            "almacenes": [self.test_data["almacen_id"]],
/app/backend/tests/test_e2e_flujo_completo.py:221:                    workflow = self.db.workflow_inventarios.find_one({"id": workflow_id})
/app/backend/tests/test_e2e_flujo_completo.py:229:                        count = self.db.workflow_inventarios.count_documents({})
/app/backend/tests/test_e2e_flujo_completo.py:232:                        last = self.db.workflow_inventarios.find_one(
/app/backend/tests/test_e2e_flujo_completo.py:281:                "almacen_id": self.test_data["almacen_id"],
/app/backend/tests/test_e2e_flujo_completo.py:282:                "almacen_nombre": self.test_data["almacen_nombre"],
/app/backend/tests/test_e2e_flujo_completo.py:291:            self.db.workflow_inventarios.insert_one(workflow_doc)
/app/backend/tests/test_e2e_flujo_completo.py:326:        self.db.workflow_inventarios.update_one(
/app/backend/tests/conftest.py:47:TEST_ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "admin@inventario.com")
/app/backend/tests/conftest.py:50:TEST_USER_EMAIL = os.environ.get("TEST_USER_EMAIL", "test@inventario.com")
/app/backend/tests/conftest.py:52:TEST_SUPERVISOR_EMAIL = os.environ.get("TEST_SUPERVISOR_EMAIL", "supervisor@inventario.com")
/app/backend/tests/test_compras_module.py:3:Tests the /api/compras/calculo-pedido endpoint and related functionality
/app/backend/tests/test_compras_module.py:9:- Almacenes loading
/app/backend/tests/test_compras_module.py:10:- Calculo-pedido endpoint with correct data structure
/app/backend/tests/test_compras_module.py:27:TEST_ALMACEN = "BODEGA"
/app/backend/tests/test_compras_module.py:107:    def test_get_almacenes_for_sucursal(self, auth_token):
/app/backend/tests/test_compras_module.py:108:        """Test loading almacenes for a sucursal"""
/app/backend/tests/test_compras_module.py:121:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes?sucursal={sucursal_nombre}",
/app/backend/tests/test_compras_module.py:125:        almacenes = response.json()
/app/backend/tests/test_compras_module.py:126:        assert len(almacenes) > 0, f"No almacenes found for sucursal {sucursal_nombre}"
/app/backend/tests/test_compras_module.py:129:        first_alm = almacenes[0]
/app/backend/tests/test_compras_module.py:131:        print(f"✓ Found {len(almacenes)} almacenes for {sucursal_nombre}")
/app/backend/tests/test_compras_module.py:134:        bodega = next((a for a in almacenes if 'BODEGA' in str(a.get('nombre', '')).upper()), None)
/app/backend/tests/test_compras_module.py:136:            print("✓ BODEGA almacen found")
/app/backend/tests/test_compras_module.py:138:            print(f"⚠ BODEGA not found, available: {[a.get('nombre') for a in almacenes[:5]]}")
/app/backend/tests/test_compras_module.py:141:class TestCalculoPedidoEndpoint:
/app/backend/tests/test_compras_module.py:142:    """Tests for /api/compras/calculo-pedido endpoint"""
/app/backend/tests/test_compras_module.py:154:    def valid_sucursal_almacen(self, auth_token):
/app/backend/tests/test_compras_module.py:155:        """Get valid sucursal and almacen names from the server"""
/app/backend/tests/test_compras_module.py:167:        # Get almacenes
/app/backend/tests/test_compras_module.py:169:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes?sucursal={sucursal_nombre}",
/app/backend/tests/test_compras_module.py:172:        almacenes = alm_response.json()
/app/backend/tests/test_compras_module.py:175:        bodega = next((a for a in almacenes if 'BODEGA' in str(a.get('nombre', '')).upper()), None)
/app/backend/tests/test_compras_module.py:176:        almacen_nombre = bodega['nombre'] if bodega else almacenes[0]['nombre']
/app/backend/tests/test_compras_module.py:178:        return {"sucursal": sucursal_nombre, "almacen": almacen_nombre}
/app/backend/tests/test_compras_module.py:180:    def test_calculo_pedido_returns_200(self, auth_token, valid_sucursal_almacen):
/app/backend/tests/test_compras_module.py:181:        """Test that calculo-pedido endpoint returns 200 with valid params"""
/app/backend/tests/test_compras_module.py:183:            f"{BASE_URL}/api/compras/calculo-pedido",
/app/backend/tests/test_compras_module.py:187:                "sucursal": valid_sucursal_almacen["sucursal"],
/app/backend/tests/test_compras_module.py:188:                "almacen": valid_sucursal_almacen["almacen"],
/app/backend/tests/test_compras_module.py:191:                "dias_inventario": 10
/app/backend/tests/test_compras_module.py:194:        assert response.status_code == 200, f"Calculo pedido failed: {response.text}"
/app/backend/tests/test_compras_module.py:200:        assert "tiene_inventario_fisico" in data, "Response missing 'tiene_inventario_fisico' field"
/app/backend/tests/test_compras_module.py:203:        print(f"✓ Calculo pedido returned {data['count']} products")
/app/backend/tests/test_compras_module.py:204:        print(f"✓ Tiene inventario físico: {data['tiene_inventario_fisico']}")
/app/backend/tests/test_compras_module.py:206:    def test_calculo_pedido_data_structure(self, auth_token, valid_sucursal_almacen):
/app/backend/tests/test_compras_module.py:209:            f"{BASE_URL}/api/compras/calculo-pedido",
/app/backend/tests/test_compras_module.py:213:                "sucursal": valid_sucursal_almacen["sucursal"],
/app/backend/tests/test_compras_module.py:214:                "almacen": valid_sucursal_almacen["almacen"],
/app/backend/tests/test_compras_module.py:217:                "dias_inventario": 10
/app/backend/tests/test_compras_module.py:229:                'Inventario_Fisico', 'Compras_Periodo', 'Consumos_Periodo',
/app/backend/tests/test_compras_module.py:230:                'Inventario_Teorico', 'Promedio_Diario', 'Dias_Inventario',
/app/backend/tests/test_compras_module.py:231:                'Consumo_Esperado', 'Cantidad_Pedir', 'Costo_Pedido',
/app/backend/tests/test_compras_module.py:232:                'Sin_Inventario_Fisico'
/app/backend/tests/test_compras_module.py:243:    def test_calculo_pedido_inventory_info(self, auth_token, valid_sucursal_almacen):
/app/backend/tests/test_compras_module.py:246:            f"{BASE_URL}/api/compras/calculo-pedido",
/app/backend/tests/test_compras_module.py:250:                "sucursal": valid_sucursal_almacen["sucursal"],
/app/backend/tests/test_compras_module.py:251:                "almacen": valid_sucursal_almacen["almacen"],
/app/backend/tests/test_compras_module.py:254:                "dias_inventario": 10
/app/backend/tests/test_compras_module.py:261:        assert "tiene_inventario_fisico" in data
/app/backend/tests/test_compras_module.py:262:        assert "folio_inventario_fisico" in data
/app/backend/tests/test_compras_module.py:263:        assert "fecha_inventario_fisico" in data
/app/backend/tests/test_compras_module.py:264:        assert "productos_sin_inventario" in data
/app/backend/tests/test_compras_module.py:267:        if data['tiene_inventario_fisico']:
/app/backend/tests/test_compras_module.py:268:            print(f"✓ Inventario físico: Folio {data['folio_inventario_fisico']}, Fecha {data['fecha_inventario_fisico']}")
/app/backend/tests/test_compras_module.py:270:            print("⚠ No hay inventario físico capturado")
/app/backend/tests/test_compras_module.py:272:        print(f"✓ Productos sin inventario: {data['productos_sin_inventario']}")
/app/backend/tests/test_compras_module.py:275:    def test_calculo_pedido_kpi_calculation(self, auth_token, valid_sucursal_almacen):
/app/backend/tests/test_compras_module.py:278:            f"{BASE_URL}/api/compras/calculo-pedido",
/app/backend/tests/test_compras_module.py:282:                "sucursal": valid_sucursal_almacen["sucursal"],
/app/backend/tests/test_compras_module.py:283:                "almacen": valid_sucursal_almacen["almacen"],
/app/backend/tests/test_compras_module.py:286:                "dias_inventario": 10
/app/backend/tests/test_compras_module.py:296:        costo_total_pedido = sum(p['Costo_Pedido'] for p in products)
/app/backend/tests/test_compras_module.py:297:        productos_stock_bajo = len([p for p in products if p['Dias_Inventario'] < 3])
/app/backend/tests/test_compras_module.py:298:        productos_sin_inv_fisico = len([p for p in products if p['Sin_Inventario_Fisico']])
/app/backend/tests/test_compras_module.py:303:        print(f"  - Costo total pedido: ${costo_total_pedido:,.2f}")
/app/backend/tests/test_compras_module.py:310:        assert costo_total_pedido >= 0
/app/backend/tests/test_compras_module.py:312:    def test_calculo_pedido_invalid_server(self, auth_token):
/app/backend/tests/test_compras_module.py:315:            f"{BASE_URL}/api/compras/calculo-pedido",
/app/backend/tests/test_compras_module.py:320:                "almacen": "TEST",
/app/backend/tests/test_compras_module.py:323:                "dias_inventario": 10
/app/backend/tests/test_compras_module.py:329:    def test_calculo_pedido_without_auth(self):
/app/backend/tests/test_compras_module.py:332:            f"{BASE_URL}/api/compras/calculo-pedido",
/app/backend/tests/test_compras_module.py:336:                "almacen": "TEST",
/app/backend/tests/test_compras_module.py:339:                "dias_inventario": 10
/app/backend/tests/test_compras_module.py:369:        assert "dias_inventario" in data
/app/backend/tests/test_compras_module.py:370:        print(f"✓ Parametros returned: dias_inventario={data.get('dias_inventario')}")
/app/backend/tests/test_movement_sales_details.py:50:            "almacen": "GENERAL",
/app/backend/tests/test_movement_sales_details.py:80:            "almacen": "GENERAL",
/app/backend/tests/test_movement_sales_details.py:163:class TestAlmacenGeneralLogic:
/app/backend/tests/test_movement_sales_details.py:166:    def test_get_almacenes_includes_general(self, api_client):
/app/backend/tests/test_movement_sales_details.py:167:        """Test that almacenes list includes GENERAL warehouse"""
/app/backend/tests/test_movement_sales_details.py:175:            # Get almacenes for this sucursal
/app/backend/tests/test_movement_sales_details.py:176:            alm_response = api_client.get(f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes", 
/app/backend/tests/test_movement_sales_details.py:179:            almacenes = alm_response.json()
/app/backend/tests/test_movement_sales_details.py:182:            general_exists = any('GENERAL' in str(a.get('nombre', '')).upper() for a in almacenes)
/app/backend/tests/test_movement_sales_details.py:183:            print(f"Found {len(almacenes)} almacenes for sucursal {sucursal_id}")
/app/backend/tests/test_movement_sales_details.py:185:            print(f"Almacenes: {[a.get('nombre') for a in almacenes]}")
/app/backend/tests/test_movement_sales_details.py:197:            "almacen": "GENERAL",
/app/backend/tests/test_softrestaurant_inventory.py:3:Tests the inventory analysis endpoint for LA ESTELAR server with almacen 001 BODEGA
/app/backend/tests/test_softrestaurant_inventory.py:20:TEST_ALMACEN = "001 BODEGA"
/app/backend/tests/test_softrestaurant_inventory.py:68:    def test_almacenes_softrestaurant(self, auth_headers):
/app/backend/tests/test_softrestaurant_inventory.py:69:        """Test that almacenes endpoint returns data"""
/app/backend/tests/test_softrestaurant_inventory.py:71:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/almacenes-softrestaurant",
/app/backend/tests/test_softrestaurant_inventory.py:77:        assert len(data) > 0, "No almacenes found"
/app/backend/tests/test_softrestaurant_inventory.py:81:        assert bodega is not None, "001 BODEGA not found in almacenes"
/app/backend/tests/test_softrestaurant_inventory.py:82:        print(f"✓ Found {len(data)} almacenes, including 001 BODEGA")
/app/backend/tests/test_softrestaurant_inventory.py:84:    def test_inventarios_list(self, auth_headers):
/app/backend/tests/test_softrestaurant_inventory.py:85:        """Test that inventarios endpoint returns data for almacen 001"""
/app/backend/tests/test_softrestaurant_inventory.py:87:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_softrestaurant_inventory.py:89:            params={"sucursal_id": "default", "almacen_id": "001"}
/app/backend/tests/test_softrestaurant_inventory.py:94:        assert len(data) > 0, "No inventarios found"
/app/backend/tests/test_softrestaurant_inventory.py:100:        print(f"✓ Found {len(data)} inventarios, including folios {TEST_FOLIO_INICIAL} and {TEST_FOLIO_FINAL}")
/app/backend/tests/test_softrestaurant_inventory.py:104:        # Get inventario dates first
/app/backend/tests/test_softrestaurant_inventory.py:106:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_softrestaurant_inventory.py:108:            params={"sucursal_id": "default", "almacen_id": "001"}
/app/backend/tests/test_softrestaurant_inventory.py:110:        inventarios = inv_response.json()
/app/backend/tests/test_softrestaurant_inventory.py:113:        inv_inicial = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_INICIAL), None)
/app/backend/tests/test_softrestaurant_inventory.py:114:        inv_final = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_FINAL), None)
/app/backend/tests/test_softrestaurant_inventory.py:116:        assert inv_inicial is not None, f"Inventario inicial {TEST_FOLIO_INICIAL} not found"
/app/backend/tests/test_softrestaurant_inventory.py:117:        assert inv_final is not None, f"Inventario final {TEST_FOLIO_FINAL} not found"
/app/backend/tests/test_softrestaurant_inventory.py:132:                "almacen": TEST_ALMACEN,
/app/backend/tests/test_softrestaurant_inventory.py:157:        # Get inventario dates first
/app/backend/tests/test_softrestaurant_inventory.py:159:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_softrestaurant_inventory.py:161:            params={"sucursal_id": "default", "almacen_id": "001"}
/app/backend/tests/test_softrestaurant_inventory.py:163:        inventarios = inv_response.json()
/app/backend/tests/test_softrestaurant_inventory.py:165:        inv_inicial = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_INICIAL), None)
/app/backend/tests/test_softrestaurant_inventory.py:166:        inv_final = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_FINAL), None)
/app/backend/tests/test_softrestaurant_inventory.py:178:                "almacen": TEST_ALMACEN,
/app/backend/tests/test_softrestaurant_inventory.py:217:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_softrestaurant_inventory.py:219:            params={"sucursal_id": "default", "almacen_id": "001"}
/app/backend/tests/test_softrestaurant_inventory.py:221:        inventarios = inv_response.json()
/app/backend/tests/test_softrestaurant_inventory.py:223:        inv_inicial = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_INICIAL), None)
/app/backend/tests/test_softrestaurant_inventory.py:224:        inv_final = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_FINAL), None)
/app/backend/tests/test_softrestaurant_inventory.py:235:                "almacen": TEST_ALMACEN,
/app/backend/tests/test_softrestaurant_inventory.py:274:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_softrestaurant_inventory.py:276:            params={"sucursal_id": "default", "almacen_id": "001"}
/app/backend/tests/test_softrestaurant_inventory.py:278:        inventarios = inv_response.json()
/app/backend/tests/test_softrestaurant_inventory.py:280:        inv_inicial = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_INICIAL), None)
/app/backend/tests/test_softrestaurant_inventory.py:281:        inv_final = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_FINAL), None)
/app/backend/tests/test_softrestaurant_inventory.py:292:                "almacen": TEST_ALMACEN,
/app/backend/tests/test_softrestaurant_inventory.py:332:            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
/app/backend/tests/test_softrestaurant_inventory.py:334:            params={"sucursal_id": "default", "almacen_id": "001"}
/app/backend/tests/test_softrestaurant_inventory.py:336:        inventarios = inv_response.json()
/app/backend/tests/test_softrestaurant_inventory.py:338:        inv_inicial = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_INICIAL), None)
/app/backend/tests/test_softrestaurant_inventory.py:339:        inv_final = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_FINAL), None)
/app/backend/tests/test_softrestaurant_inventory.py:351:                "almacen": TEST_ALMACEN,
/app/backend/tests/test_softrestaurant_inventory.py:377:                    "almacen": TEST_ALMACEN,
/app/backend/tests/test_sistema_tareas.py:91:                       "proveedores", "categorias_presupuesto", "almacenes", "familias", "categorias"]
/app/backend/tests/test_comparativo_inventarios.py:6:1. /api/reports/inventory-analysis - saves correctly to MongoDB cache (inventario_diferencias_detalle)
/app/backend/tests/test_comparativo_inventarios.py:7:2. /api/reports/export/comparativo-inventarios - reads from cache and generates Excel
/app/backend/tests/test_comparativo_inventarios.py:9:4. Frontend sends almacen_id and fecha in inventarios_finales_info
/app/backend/tests/test_comparativo_inventarios.py:30:TEST_ALMACEN_ID = "0001"  # ALMACEN GENERAL
/app/backend/tests/test_comparativo_inventarios.py:36:class TestComparativoInventarios:
/app/backend/tests/test_comparativo_inventarios.py:101:    def test_04_get_almacenes(self):
/app/backend/tests/test_comparativo_inventarios.py:102:        """Test that almacenes can be retrieved"""
/app/backend/tests/test_comparativo_inventarios.py:104:            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes",
/app/backend/tests/test_comparativo_inventarios.py:108:        assert response.status_code == 200, f"Failed to get almacenes: {response.text}"
/app/backend/tests/test_comparativo_inventarios.py:109:        almacenes = response.json()
/app/backend/tests/test_comparativo_inventarios.py:110:        assert isinstance(almacenes, list), "Almacenes should be a list"
/app/backend/tests/test_comparativo_inventarios.py:112:        # Find ALMACEN GENERAL
/app/backend/tests/test_comparativo_inventarios.py:113:        almacen_general = next((a for a in almacenes if a.get('id') == TEST_ALMACEN_ID), None)
/app/backend/tests/test_comparativo_inventarios.py:114:        if almacen_general:
/app/backend/tests/test_comparativo_inventarios.py:115:            print(f"✅ Almacen found: {almacen_general.get('nombre')}")
/app/backend/tests/test_comparativo_inventarios.py:117:            print(f"⚠️ Almacen {TEST_ALMACEN_ID} not found in {len(almacenes)} almacenes")
/app/backend/tests/test_comparativo_inventarios.py:126:            f"{BASE_URL}/api/reports/export/comparativo-inventarios",
/app/backend/tests/test_comparativo_inventarios.py:131:                "almacenes": [{
/app/backend/tests/test_comparativo_inventarios.py:132:                    "id": TEST_ALMACEN_ID,
/app/backend/tests/test_comparativo_inventarios.py:133:                    "nombre": "ALMACEN GENERAL",
/app/backend/tests/test_comparativo_inventarios.py:160:            f"{BASE_URL}/api/reports/export/comparativo-inventarios",
/app/backend/tests/test_comparativo_inventarios.py:165:                "almacenes": [{
/app/backend/tests/test_comparativo_inventarios.py:166:                    "id": TEST_ALMACEN_ID,
/app/backend/tests/test_comparativo_inventarios.py:167:                    "nombre": "ALMACEN GENERAL",
/app/backend/tests/test_comparativo_inventarios.py:196:    def test_07_export_without_almacen_fails(self):
/app/backend/tests/test_comparativo_inventarios.py:197:        """Test that export fails gracefully without almacen selection"""
/app/backend/tests/test_comparativo_inventarios.py:199:            f"{BASE_URL}/api/reports/export/comparativo-inventarios",
/app/backend/tests/test_comparativo_inventarios.py:203:                "almacenes": []  # Empty almacenes
/app/backend/tests/test_comparativo_inventarios.py:209:            f"Expected 400/422 for empty almacenes, got: {response.status_code}"
/app/backend/tests/test_comparativo_inventarios.py:210:        print("✅ Validation works - empty almacenes rejected")
/app/backend/tests/test_comparativo_inventarios.py:215:            f"{BASE_URL}/api/reports/export/comparativo-inventarios",
/app/backend/tests/test_comparativo_inventarios.py:219:                "almacenes": [{
/app/backend/tests/test_comparativo_inventarios.py:220:                    "id": TEST_ALMACEN_ID,
/app/backend/tests/test_comparativo_inventarios.py:221:                    "nombre": "ALMACEN GENERAL",
/app/backend/tests/test_comparativo_inventarios.py:239:                "almacen": "ALMACEN GENERAL",
/app/backend/tests/test_comparativo_inventarios.py:240:                "almacenes": ["ALMACEN GENERAL"],
/app/backend/tests/test_comparativo_inventarios.py:245:                "inventarios_iniciales_info": [{
/app/backend/tests/test_comparativo_inventarios.py:248:                    "almacen_id": "0001",
/app/backend/tests/test_comparativo_inventarios.py:251:                "inventarios_finales_info": [{
/app/backend/tests/test_comparativo_inventarios.py:254:                    "almacen_id": "0001",
/app/backend/tests/test_comparativo_inventarios.py:274:        """Test that cache uses correct key structure (server_id, almacen_id, sucursal_id, comentario, folio)"""
/app/backend/tests/test_comparativo_inventarios.py:278:        # - almacen_id
/app/backend/tests/test_comparativo_inventarios.py:283:        expected_cache_key_fields = ['server_id', 'almacen_id', 'sucursal_id', 'comentario', 'folio']
/app/backend/tests/test_comparativo_inventarios.py:315:            f"{BASE_URL}/api/reports/export/comparativo-inventarios",
/app/backend/tests/test_comparativo_inventarios.py:320:                "almacenes": [{
/app/backend/tests/test_comparativo_inventarios.py:321:                    "id": TEST_ALMACEN_ID,
/app/backend/tests/test_comparativo_inventarios.py:322:                    "nombre": "ALMACEN GENERAL",
/app/backend/tests/test_comparativo_inventarios.py:363:    def test_12_inventarios_finales_info_structure(self):
/app/backend/tests/test_comparativo_inventarios.py:364:        """Test that inventarios_finales_info accepts almacen_id and fecha"""
/app/backend/tests/test_comparativo_inventarios.py:366:        # Frontend should send: { folio, comentario, almacen_id, fecha }
/app/backend/tests/test_comparativo_inventarios.py:373:                "almacen": "ALMACEN GENERAL",
/app/backend/tests/test_comparativo_inventarios.py:378:                "inventarios_iniciales_info": [{
/app/backend/tests/test_comparativo_inventarios.py:381:                    "almacen_id": "0001",  # This field should be accepted
/app/backend/tests/test_comparativo_inventarios.py:384:                "inventarios_finales_info": [{
/app/backend/tests/test_comparativo_inventarios.py:387:                    "almacen_id": "0001",  # This field should be accepted
/app/backend/tests/test_comparativo_inventarios.py:397:            f"Backend rejected inventarios_finales_info structure: {response.text}"
/app/backend/tests/test_comparativo_inventarios.py:400:            print("✅ Backend accepts inventarios_finales_info with almacen_id and fecha")
/app/backend/tests/test_automatizacion_compras_fase43.py:93:        assert "fecha_pedido" in data, "Missing 'fecha_pedido' field"
/app/backend/tests/test_automatizacion_compras_fase43.py:720:        original_fecha_pedido = original.get("fecha_pedido")
/app/backend/tests/test_automatizacion_compras_fase43.py:748:        assert updated.get("fecha_pedido") == original_fecha_pedido, \
/app/backend/tests/test_automatizacion_compras_fase43.py:749:            f"fecha_pedido changed from {original_fecha_pedido} to {updated.get('fecha_pedido')}"
/app/backend/tests/test_automatizacion_compras_fase43.py:754:        print(f"  - fecha_pedido: {original_fecha_pedido}")
/app/backend/server.py:276:    has_almacen_access,
/app/backend/server.py:279:    # FASE 8: Enforcement de Almacenes
/app/backend/server.py:280:    get_almacenes_permitidos,
/app/backend/server.py:281:    get_almacenes_sql_filter,
/app/backend/server.py:282:    get_almacenes_sql_filter_like,
/app/backend/server.py:283:    validate_almacen_in_scope,
/app/backend/server.py:284:    filter_results_by_almacen,
/app/backend/server.py:418:    obtener_inventarios_fisicos_sync,
/app/backend/server.py:419:    obtener_requisiciones_sync,
/app/backend/server.py:747:    Ejecuta manualmente la sincronización de Compras (Inventarios y Requisiciones).
/app/backend/server.py:781:    Ejecuta manualmente la detección de nuevos inventarios/requisiciones.
/app/backend/server.py:1003:    # Consultas SQL personalizadas para el análisis de inventario
/app/backend/server.py:1004:    query_inventario: Optional[Dict] = None  # Consulta para obtener inventarios
/app/backend/server.py:1039:    query_inventario: Optional[Dict] = None
/app/backend/server.py:1047:    query_type: str  # "inventario", "ventas", "movimientos"
/app/backend/server.py:1065:    query_type: str  # "ventas", "movimientos", "productos", "inventarios"
/app/backend/server.py:1079:    almacen: str
/app/backend/server.py:1168:    # Datos del reporte de inventario
/app/backend/server.py:1169:    datos_inventario: List[Dict[str, Any]] = []
/app/backend/server.py:1181:    compromisos_almacen: str = ""
/app/backend/server.py:1194:    compromisos_almacen: Optional[str] = None
/app/backend/server.py:1213:    datos_inventario: List[Dict[str, Any]] = []
/app/backend/server.py:1225:    compromisos_almacen: str = ""
/app/backend/server.py:1274:    Genera archivo Excel con formato profesional para el reporte de inventario.
/app/backend/server.py:1285:    ws.title = "Reporte de Inventario"
/app/backend/server.py:1301:    almacen = meta.get('almacen', 'N/A')
/app/backend/server.py:1330:    ws.cell(row=row_num, column=1, value="REPORTE DE ANÁLISIS DE INVENTARIO").font = titulo_font
/app/backend/server.py:1338:        ("Almacén:", almacen),
/app/backend/server.py:1910:    "inventario": {
/app/backend/server.py:1912:        "optional": ["fecha", "sucursal", "almacen", "costo", "unidad", "grupo", "categoria"],
/app/backend/server.py:1913:        "description": "Consulta de inventarios (inicial y final). Obtiene el stock de productos en una fecha determinada."
/app/backend/server.py:1917:        "optional": ["fecha", "precio", "importe", "sucursal", "almacen", "folio"],
/app/backend/server.py:1922:        "optional": ["fecha", "tipo_movimiento", "sucursal", "almacen", "referencia", "costo"],
/app/backend/server.py:1923:        "description": "Consulta de movimientos (entradas, compras, traspasos, ajustes). Obtiene las entradas de productos al inventario."
/app/backend/server.py:1932:    "fecha": ["fecha", "date", "fecha_movimiento", "fecha_venta", "fecha_inventario"],
/app/backend/server.py:1934:    "almacen": ["almacen", "warehouse", "bodega", "almacen_id", "idalmacen"],
/app/backend/server.py:2011:    query_type = request.get("query_type")  # "inventario", "ventas", "movimientos"
/app/backend/server.py:2157:            (updated_server.get("query_inventario") or {}).get("validated", False),
/app/backend/server.py:2204:            "inventario": {
/app/backend/server.py:2205:                "configured": server.get("query_inventario") is not None,
/app/backend/server.py:2206:                "validated": (server.get("query_inventario") or {}).get("validated", False),
/app/backend/server.py:2207:                "sql": (server.get("query_inventario") or {}).get("sql", ""),
/app/backend/server.py:2208:                "last_validated": (server.get("query_inventario") or {}).get("last_validated"),
/app/backend/server.py:2209:                "description": REQUIRED_COLUMNS["inventario"]["description"],
/app/backend/server.py:2210:                "required_columns": REQUIRED_COLUMNS["inventario"]["required"],
/app/backend/server.py:2211:                "optional_columns": REQUIRED_COLUMNS["inventario"]["optional"]
/app/backend/server.py:2447:    Obtiene la lista de departamentos/almacenes.
/app/backend/server.py:2600:            # Si no hay sucursales en la tabla Sucursal, intentar usar Almacenes
/app/backend/server.py:2603:                    query_almacen = "SELECT DISTINCT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE Es_Cve_Estado <> 'BA'"
/app/backend/server.py:2604:                    almacenes = execute_sql_query(
/app/backend/server.py:2610:                        query_almacen
/app/backend/server.py:2612:                    if almacenes and len(almacenes) > 0:
/app/backend/server.py:2613:                        sucursales_raw = almacenes
/app/backend/server.py:2615:                    logging.warning(f"MPRO Almacenes query failed: {e}")
/app/backend/server.py:2658:@api_router.get("/servers/{server_id}/almacenes")
/app/backend/server.py:2659:async def get_almacenes(server_id: str, sucursal_id: Optional[str] = None, sucursal: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:2661:    Obtiene la lista de almacenes desde SQL Server.
/app/backend/server.py:2662:    FASE 8: Aplica filtro RBAC por almacenes permitidos.
/app/backend/server.py:2674:        logging.warning(f"[RBAC-ALMACENES] {current_user.get('email')} sin acceso a servidor {server_id}")
/app/backend/server.py:2682:        logging.warning(f"[GET_ALMACENES] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:2685:    logging.debug(f"[GET_ALMACENES] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
/app/backend/server.py:2687:    # FASE 8: Obtener almacenes permitidos
/app/backend/server.py:2688:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:2691:        f"[RBAC-ALMACENES] Usuario={current_user.get('email')}, "
/app/backend/server.py:2692:        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:2706:            # FASE 8: Filtro por almacenes permitidos
/app/backend/server.py:2707:            almacen_filter = get_almacenes_sql_filter(context, server_id, "Al_Cve_Almacen")
/app/backend/server.py:2711:                query = f"SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE Sc_Cve_Sucursal = %s AND Es_Cve_Estado <> 'BA'{almacen_filter}"
/app/backend/server.py:2717:                query = f"SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE Es_Cve_Estado <> 'BA'{almacen_filter}"
/app/backend/server.py:2722:            logging.info(f"[RBAC-ALMACENES] MPRO devolvió {len(results)} almacenes (filtrado RBAC)")
/app/backend/server.py:2726:            # FASE 8: Filtro por almacenes permitidos (usa ID numérico)
/app/backend/server.py:2727:            almacen_filter = get_almacenes_sql_filter(context, server_id, "idalmacen")
/app/backend/server.py:2731:    idalmacen as id, 
/app/backend/server.py:2734:FROM almacen
/app/backend/server.py:2735:WHERE 1=1{almacen_filter}
/app/backend/server.py:2742:            logging.info(f"[RBAC-ALMACENES] SoftRestaurant devolvió {len(results)} almacenes (filtrado RBAC)")
/app/backend/server.py:2747:            almacen_filter = get_almacenes_sql_filter(context, server_id, "Al_Cve_Almacen")
/app/backend/server.py:2750:                query = f"SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE Sc_Cve_Sucursal = %s{almacen_filter}"
/app/backend/server.py:2756:                query = f"SELECT Al_Cve_Almacen as id, Al_Descripcion as nombre FROM Almacen WHERE 1=1{almacen_filter}"
/app/backend/server.py:2763:        logging.error(f"Error obteniendo almacenes: {str(e)}")
/app/backend/server.py:3175:@api_router.get("/servers/{server_id}/almacenes-softrestaurant")
/app/backend/server.py:3176:async def get_almacenes_softrestaurant(
/app/backend/server.py:3178:    solo_consumo: bool = False,  # Filtrar solo almacenes de consumo (tipo=1)
/app/backend/server.py:3182:    Obtiene la lista de almacenes de SoftRestaurant (no requiere sucursal).
/app/backend/server.py:3183:    FASE 8: Aplica filtro RBAC por almacenes permitidos.
/app/backend/server.py:3195:        logging.warning(f"[RBAC-ALMACENES-SR] {current_user.get('email')} sin acceso a servidor {server_id}")
/app/backend/server.py:3203:        logging.warning(f"[GET_ALMACENES_SR] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:3206:    logging.debug(f"[GET_ALMACENES_SR] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
/app/backend/server.py:3211:    # FASE 8: Obtener almacenes permitidos
/app/backend/server.py:3212:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:3213:    almacen_filter = get_almacenes_sql_filter(context, server_id, "idalmacen")
/app/backend/server.py:3216:        f"[RBAC-ALMACENES-SR] Usuario={current_user.get('email')}, "
/app/backend/server.py:3217:        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:3221:        # Query para obtener almacenes de SoftRestaurant incluyendo el tipo
/app/backend/server.py:3227:    idalmacen as id, 
/app/backend/server.py:3230:FROM almacen
/app/backend/server.py:3231:{where_clause}{almacen_filter}
/app/backend/server.py:3242:        logging.info(f"[RBAC-ALMACENES-SR] Devolvió {len(results)} almacenes (filtrado RBAC)")
/app/backend/server.py:3245:        logging.error(f"Error obteniendo almacenes SoftRestaurant: {str(e)}")
/app/backend/server.py:3248:@api_router.get("/servers/{server_id}/inventarios")
/app/backend/server.py:3249:async def get_inventarios_list(
/app/backend/server.py:3252:    almacen_id: Optional[str] = None,
/app/backend/server.py:3256:    Obtiene la lista de inventarios físicos disponibles con sus fechas.
/app/backend/server.py:3257:    FASE 8: Aplica filtro RBAC por almacenes permitidos.
/app/backend/server.py:3269:        logging.warning(f"[RBAC-INVENTARIOS-LIST] {current_user.get('email')} sin acceso a servidor {server_id}")
/app/backend/server.py:3277:        logging.warning(f"[GET_INVENTARIOS_LIST] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:3280:    logging.debug(f"[GET_INVENTARIOS_LIST] Servidor obtenido via registry. Origin={server.get('config_origin', 'UNKNOWN')}")
/app/backend/server.py:3282:    # FASE 8: Obtener almacenes permitidos
/app/backend/server.py:3283:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:3286:        f"[RBAC-INVENTARIOS-LIST] Usuario={current_user.get('email')}, "
/app/backend/server.py:3287:        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:3293:            almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "F.Al_Cve_Almacen")
/app/backend/server.py:3298:            if almacen_id:
/app/backend/server.py:3299:                where_clause += f" AND F.Al_Cve_Almacen = '{almacen_id}'"
/app/backend/server.py:3301:            where_clause += almacen_rbac_filter
/app/backend/server.py:3309:                    F.Al_Cve_Almacen as almacen_id,
/app/backend/server.py:3310:                    A.Al_Descripcion as almacen,
/app/backend/server.py:3314:                INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND F.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
/app/backend/server.py:3316:                GROUP BY F.Fi_Folio, F.fi_fecha, F.Sc_Cve_Sucursal, S.Sc_Descripcion, F.Al_Cve_Almacen, A.Al_Descripcion, F.Fi_Comentario
/app/backend/server.py:3319:            logging.info(f"[RBAC-INVENTARIOS-LIST] MPRO Query con filtro RBAC aplicado")
/app/backend/server.py:3322:            almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "INV.idalmacen1")
/app/backend/server.py:3326:            if almacen_id:
/app/backend/server.py:3327:                where_clause += f" AND INV.idalmacen1 = '{almacen_id}'"
/app/backend/server.py:3329:            where_clause += almacen_rbac_filter
/app/backend/server.py:3335:                    INV.idalmacen1 as almacen_id,
/app/backend/server.py:3336:                    A.nombre as almacen,
/app/backend/server.py:3338:                FROM invfisico INV
/app/backend/server.py:3339:                LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
/app/backend/server.py:3343:            logging.info(f"[RBAC-INVENTARIOS-LIST] SR Query con filtro RBAC aplicado")
/app/backend/server.py:3357:        logging.error(f"Error obteniendo inventarios: {str(e)}")
/app/backend/server.py:3364:@api_router.get("/inventarios/pendientes/{server_id}")
/app/backend/server.py:3367:    almacen_id: Optional[str] = None,
/app/backend/server.py:3372:    FASE 8: Aplica filtro RBAC por almacenes permitidos.
/app/backend/server.py:3373:    - SoftRestaurant: Usa tabla inventariopendiente
/app/backend/server.py:3400:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:3401:    if almacen_id and almacenes_permitidos and almacen_id not in almacenes_permitidos:
/app/backend/server.py:3404:            f"Almacén solicitado={almacen_id}, Permitidos={almacenes_permitidos}"
/app/backend/server.py:3412:        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:3418:            almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "ip.idalmacen")
/app/backend/server.py:3422:            if almacen_id:
/app/backend/server.py:3423:                where_clause += f" AND ip.idalmacen = '{almacen_id}'"
/app/backend/server.py:3425:            where_clause += almacen_rbac_filter
/app/backend/server.py:3436:                    ip.idalmacen as almacen,
/app/backend/server.py:3439:                FROM inventariopendiente ip
/app/backend/server.py:3451:            almacen_filter = f"AND venta.Al_Cve_Almacen = '{almacen_id}'" if almacen_id else ""
/app/backend/server.py:3459:                    venta.Al_Cve_Almacen AS almacen,
/app/backend/server.py:3484:                    AND Movimiento.Al_Cve_Almacen = '0001'
/app/backend/server.py:3492:                {almacen_filter}
/app/backend/server.py:3500:                    venta.Al_Cve_Almacen,
/app/backend/server.py:3525:                "almacenes": []
/app/backend/server.py:3553:                    "almacen": str(item.get('almacen', '')).strip(),
/app/backend/server.py:3578:                    "almacen": str(item.get('almacen', '')).strip(),
/app/backend/server.py:3583:        # Obtener lista de almacenes únicos
/app/backend/server.py:3584:        almacenes_unicos = list(set(str(item.get('almacen', '')).strip() for item in results if item.get('almacen')))
/app/backend/server.py:3585:        almacenes_unicos.sort()
/app/backend/server.py:3594:            "almacenes": almacenes_unicos,
/app/backend/server.py:3606:    Genera un reporte de inventario usando queries predefinidas.
/app/backend/server.py:3615:    query_type = report_params.get('query_type')  # ventas, movimientos, productos, inventarios
/app/backend/server.py:3771:# FUNCIÓN REUTILIZABLE - Análisis de Inventarios
/app/backend/server.py:3784:    Genera un análisis completo de inventario con:
/app/backend/server.py:3785:    - Inventario Inicial (folio inicial)
/app/backend/server.py:3788:    - Inventario Final (folio final)
/app/backend/server.py:3801:    almacen = report_params.get('almacen')
/app/backend/server.py:3802:    almacenes = report_params.get('almacenes', [])  # Multi-almacén
/app/backend/server.py:3812:    # Info completa de inventarios (folio + comentario) para MPRO
/app/backend/server.py:3813:    inventarios_iniciales_info = report_params.get('inventarios_iniciales_info', [])
/app/backend/server.py:3814:    inventarios_finales_info = report_params.get('inventarios_finales_info', [])
/app/backend/server.py:3872:            logging.info(f"Generando análisis de inventario MPRO: {sucursal} - {almacen}")
/app/backend/server.py:3922:            # - Movimientos y Ventas: desde (fecha_inventario_inicial + 1 día) hasta fecha_inventario_final
/app/backend/server.py:3923:            # - Ejemplo: Si inventario inicial es 28-Feb-2026, movimientos/ventas desde 01-Mar-2026
/app/backend/server.py:3926:            # Obtener fechas de los inventarios si no se proporcionan explícitamente
/app/backend/server.py:3929:            # Si no hay fecha_ini, intentar obtenerla de inventarios_iniciales_info o del folio
/app/backend/server.py:3931:                if inventarios_iniciales_info and inventarios_iniciales_info[0].get('fecha'):
/app/backend/server.py:3932:                    fecha_ini = inventarios_iniciales_info[0]['fecha'][:10]  # YYYY-MM-DD
/app/backend/server.py:3942:                    raise HTTPException(status_code=400, detail="Se requiere fecha_ini o inventarios_iniciales_info")
/app/backend/server.py:3945:                if inventarios_finales_info and inventarios_finales_info[0].get('fecha'):
/app/backend/server.py:3946:                    fecha_fin = inventarios_finales_info[0]['fecha'][:10]
/app/backend/server.py:3955:                    raise HTTPException(status_code=400, detail="Se requiere fecha_fin o inventarios_finales_info")
/app/backend/server.py:3962:            # 1. Obtener códigos de TODOS los almacenes seleccionados
/app/backend/server.py:3963:            # Si hay almacenes múltiples, usarlos; si no, usar el almacén simple
/app/backend/server.py:3964:            lista_almacenes = almacenes if almacenes else [almacen] if almacen else []
/app/backend/server.py:3966:            if not lista_almacenes:
/app/backend/server.py:3970:            almacenes_like_conditions = " OR ".join([f"A.Al_Descripcion LIKE '%{_escape_like_pattern(alm)}%'" for alm in lista_almacenes])
/app/backend/server.py:3973:            almacen_query = f"""
/app/backend/server.py:3975:    A.Al_Cve_Almacen as codigo,
/app/backend/server.py:3978:FROM Almacen A
/app/backend/server.py:3980:WHERE ({almacenes_like_conditions})
/app/backend/server.py:3983:            almacen_result = execute_sql_query(
/app/backend/server.py:3985:                server['username'], server['password'], almacen_query
/app/backend/server.py:3987:            if not almacen_result:
/app/backend/server.py:3988:                logging.error(f"Almacén(es) no encontrado(s) en MPRO - Sucursal: '{sucursal}', Almacenes: {lista_almacenes}, Servidor: {server.get('name', server_id)}")
/app/backend/server.py:3992:            almacenes_codigos = [r['codigo'] for r in almacen_result]
/app/backend/server.py:3993:            almacenes_nombres = [r['nombre'] for r in almacen_result]
/app/backend/server.py:3994:            sucursal_codigo = almacen_result[0]['sucursal_codigo']
/app/backend/server.py:3997:            almacen_codigo = almacenes_codigos[0]
/app/backend/server.py:3998:            almacen_nombre = almacenes_nombres[0]
/app/backend/server.py:4000:            # Construir SQL IN clause para múltiples almacenes
/app/backend/server.py:4001:            almacenes_sql = ",".join([f"'{c}'" for c in almacenes_codigos])
/app/backend/server.py:4004:            es_almacen_bodega = any('BODEGA' in (n.upper() if n else '') for n in almacenes_nombres)
/app/backend/server.py:4006:            logging.info(f"Almacenes encontrados: {almacenes_codigos} - {almacenes_nombres} (Sucursal: {sucursal_codigo})")
/app/backend/server.py:4007:            logging.info(f"MPRO - Incluye almacén BODEGA: {es_almacen_bodega}")
/app/backend/server.py:4009:            # 2. Obtener productos que se controlan en inventario:
/app/backend/server.py:4012:            # NOTA: Traemos productos que tengan inventario físico O movimientos O ventas en el período
/app/backend/server.py:4047:    -- Productos que tienen: inventario físico O movimientos en el período
/app/backend/server.py:4049:        -- Tiene inventario físico capturado
/app/backend/server.py:4054:            AND FIS.Al_Cve_Almacen IN ({almacenes_sql})
/app/backend/server.py:4062:            AND MOV.Al_Cve_Almacen IN ({almacenes_sql})
/app/backend/server.py:4078:            # MPRO: Ventas desde (fecha_inventario_inicial + 1 día) hasta fecha_inventario_final
/app/backend/server.py:4079:            # NOTA: Los almacenes tipo BODEGA no tienen ventas
/app/backend/server.py:4082:            if not es_almacen_bodega:
/app/backend/server.py:4123:                logging.info(f"MPRO - Almacén BODEGA '{almacen_nombre}' - Ventas = 0 para todos los productos")
/app/backend/server.py:4130:            # MPRO: Movimientos desde (fecha_inventario_inicial + 1 día) hasta fecha_inventario_final
/app/backend/server.py:4137:INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = S.Sc_Cve_Sucursal
/app/backend/server.py:4141:    AND E.Al_Cve_Almacen IN ({almacenes_sql})
/app/backend/server.py:4168:            # 5. Detectar errores de captura de inventario
/app/backend/server.py:4170:            # Y también fue capturado en inventario físico, es un ERROR
/app/backend/server.py:4181:    AND F.Al_Cve_Almacen IN ({almacenes_sql})
/app/backend/server.py:4192:                    logging.warning(f"  - Presentación {err['Codigo_Presentacion']} ({err['Descripcion_Presentacion']}) capturada en inventario, pero debería capturarse como INSUMO {err['Codigo_Insumo']} ({err['Descripcion_Insumo']})")
/app/backend/server.py:4215:                    # Calcular inventario teórico: Inicial + Movimientos - Ventas
/app/backend/server.py:4226:                    folios_ini_str = ', '.join([i.get('folio', '') for i in inventarios_iniciales_info]) if inventarios_iniciales_info else ', '.join(lista_folios_ini)
/app/backend/server.py:4227:                    folios_fin_str = ', '.join([i.get('folio', '') for i in inventarios_finales_info]) if inventarios_finales_info else ', '.join(lista_folios_fin)
/app/backend/server.py:4228:                    comentarios_ini_str = ', '.join([i.get('comentario', '') for i in inventarios_iniciales_info if i.get('comentario')]) if inventarios_iniciales_info else ''
/app/backend/server.py:4229:                    comentarios_fin_str = ', '.join([i.get('comentario', '') for i in inventarios_finales_info if i.get('comentario')]) if inventarios_finales_info else ''
/app/backend/server.py:4261:                # MODO SIN AGRUPAR: Una fila por cada combinación producto + inventario
/app/backend/server.py:4262:                # Obtener inventarios detallados por folio, incluyendo el código de almacén
/app/backend/server.py:4268:    F.Al_Cve_Almacen as Almacen_Codigo,
/app/backend/server.py:4272:    AND F.Al_Cve_Almacen IN ({almacenes_sql})
/app/backend/server.py:4285:                folio_almacen_map = {}
/app/backend/server.py:4287:                    folio_almacen_map[row['Folio']] = row['Almacen_Codigo']
/app/backend/server.py:4289:                # Organizar inventarios por código y folio
/app/backend/server.py:4296:                    almacen_cod = row['Almacen_Codigo']
/app/backend/server.py:4302:                        inv_por_codigo[codigo]['ini'][folio] = {'cantidad': cantidad, 'comentario': comentario, 'almacen': almacen_cod}
/app/backend/server.py:4304:                        inv_por_codigo[codigo]['fin'][folio] = {'cantidad': cantidad, 'comentario': comentario, 'almacen': almacen_cod}
/app/backend/server.py:4306:                # Procesar productos con inventarios detallados
/app/backend/server.py:4314:                    # Si no hay inventarios, omitir
/app/backend/server.py:4345:                        # Calcular inventario teórico: Inicial + Movimientos - Ventas
/app/backend/server.py:4389:                    'mensaje': f"Presentación '{err['Descripcion_Presentacion']}' ({err['Codigo_Presentacion']}) capturada en inventario. Debería capturarse como INSUMO '{err['Descripcion_Insumo']}' ({err['Codigo_Insumo']})"
/app/backend/server.py:4396:                # Extraer info de los inventarios FINALES para el cache
/app/backend/server.py:4397:                # El comparativo requiere las diferencias del inventario FINAL (físico vs teórico)
/app/backend/server.py:4398:                logging.info(f"CACHE: Procesando {len(inventarios_finales_info)} inventarios finales para cache")
/app/backend/server.py:4400:                for inv_info in inventarios_finales_info:
/app/backend/server.py:4403:                    almacen_id_cache = inv_info.get('almacen_id', '') or almacen_codigo
/app/backend/server.py:4407:                        logging.warning(f"CACHE: Inventario sin folio, saltando")
/app/backend/server.py:4410:                    logging.info(f"CACHE: Procesando folio {folio_cache}, comentario: {comentario_cache}, almacen_id: {almacen_id_cache}")
/app/backend/server.py:4429:                            "almacen_id": almacen_id_cache,
/app/backend/server.py:4437:                            "fecha_inventario": fecha_cache,
/app/backend/server.py:4442:                        await db.inventario_diferencias_detalle.update_one(
/app/backend/server.py:4460:                # Determinar folio_inventario principal (el folio final más relevante)
/app/backend/server.py:4461:                folio_inventario_principal = lista_folios_fin[0] if lista_folios_fin else None
/app/backend/server.py:4469:                    almacen_id=almacen or "",
/app/backend/server.py:4470:                    almacen_nombre=almacen or "",
/app/backend/server.py:4478:                    folio_inventario=folio_inventario_principal  # NUEVO: Pasar folio explícito
/app/backend/server.py:4496:            # Análisis de inventario para SoftRestaurant
/app/backend/server.py:4497:            logging.info(f"Generando análisis de inventario SoftRestaurant: {almacen}")
/app/backend/server.py:4506:            # Obtener fechas de los folios de inventario
/app/backend/server.py:4509:FROM invfisico
/app/backend/server.py:4538:            logging.info(f"Fechas de inventarios: ini={fecha_ini}, fin={fecha_fin}")
/app/backend/server.py:4541:            # para no incluir el momento exacto del inventario
/app/backend/server.py:4550:                # Esto pasa cuando el usuario selecciona el inventario inicial con fecha más reciente
/app/backend/server.py:4565:            logging.info(f"Fechas calculadas de inventarios (con hora): {fecha_ini} a {fecha_fin}")
/app/backend/server.py:4571:            almacen_safe = _escape_like_pattern(almacen) if almacen else ""
/app/backend/server.py:4572:            almacen_query = f"""
/app/backend/server.py:4574:    idalmacen as codigo,
/app/backend/server.py:4577:FROM almacen
/app/backend/server.py:4578:WHERE nombre LIKE '%{almacen_safe}%'
/app/backend/server.py:4580:            almacen_result = execute_sql_query(
/app/backend/server.py:4582:                server['username'], server['password'], almacen_query
/app/backend/server.py:4584:            if not almacen_result:
/app/backend/server.py:4585:                logging.error(f"Almacén '{almacen}' no encontrado en servidor {server.get('name', server_id)} ({server['host']})")
/app/backend/server.py:4586:                raise HTTPException(status_code=404, detail=f"Almacén '{almacen}' no encontrado. Verifique la conexión al servidor SQL o que el almacén exista en la base de datos.")
/app/backend/server.py:4588:            almacen_id = almacen_result[0]['codigo']
/app/backend/server.py:4589:            almacen_nombre = almacen_result[0]['nombre']
/app/backend/server.py:4590:            almacen_tipo = almacen_result[0]['tipo']
/app/backend/server.py:4593:            es_almacen_consumo = (almacen_tipo == 1)
/app/backend/server.py:4594:            logging.info(f"Almacén: {almacen_nombre}, ID: {almacen_id}, Tipo: {almacen_tipo}, Es Consumo (tiene ventas): {es_almacen_consumo}")
/app/backend/server.py:4622:            if es_almacen_consumo:
/app/backend/server.py:4686:            # 3. Obtener inventarios (inicial y final) de invfisicomovtos
/app/backend/server.py:4688:            logging.info(f"Obteniendo inventarios de folios {folio_inicial} y {folio_final}")
/app/backend/server.py:4690:            inventarios_query = f"""
/app/backend/server.py:4700:    FMOV.fisicoalmacen1 as EXISTENCIA,
/app/backend/server.py:4703:FROM invfisicomovtos FMOV
/app/backend/server.py:4704:INNER JOIN invfisico FISICO ON FISICO.folio = FMOV.folio
/app/backend/server.py:4705:INNER JOIN almacen AL ON AL.idalmacen = FISICO.idalmacen1
/app/backend/server.py:4716:  AND AL.nombre LIKE '%{almacen_safe}%'
/app/backend/server.py:4720:            inventarios_result = execute_sql_query(
/app/backend/server.py:4722:                server['username'], server['password'], inventarios_query
/app/backend/server.py:4725:            # Separar inventarios inicial y final - SOLO productos con existencia != 0
/app/backend/server.py:4728:            for inv in inventarios_result:
/app/backend/server.py:4738:                # Acumular inventarios iniciales
/app/backend/server.py:4747:                # Acumular inventarios finales
/app/backend/server.py:4757:            logging.info(f"Inventario inicial: {len(inv_inicial_dict)} productos, Final: {len(inv_final_dict)} productos")
/app/backend/server.py:4759:            # DEBUG: Mostrar códigos de inventarios para verificar
/app/backend/server.py:4762:                logging.info(f"DEBUG Códigos con 130009 en INVENTARIOS: {inv_130009}")
/app/backend/server.py:4764:            # 4. Obtener TODOS los códigos que aparecen en inventarios (inicial o final)
/app/backend/server.py:4766:            logging.info(f"Total códigos únicos en inventarios: {len(todos_codigos)}")
/app/backend/server.py:4768:            # 5. Obtener movimientos - UNION de movsinv (INSUMOS) + movtosalmacen (PRESENTACIONES)
/app/backend/server.py:4774:            logging.info(f"Obteniendo movimientos entre {fecha_ini_fmt} y {fecha_fin_fmt} para almacén {almacen_nombre}")
/app/backend/server.py:4788:                    filtro_conceptos_insumos = f"AND movsinv.idconcepto IN ({conceptos_filter})"
/app/backend/server.py:4789:                    filtro_conceptos_presentaciones = f"AND movtosalmacen.idconcepto IN ({conceptos_filter})"
/app/backend/server.py:4798:                filtro_conceptos_insumos = f"AND movsinv.idconcepto NOT IN ('', 'SPV', 'SCP', 'SCS')"
/app/backend/server.py:4799:                filtro_conceptos_presentaciones = f"AND movtosalmacen.idconcepto NOT IN ('', 'SPV', 'SCP', 'SCS')"
/app/backend/server.py:4803:-- MOVIMIENTOS DE INSUMOS (movsinv) - usar código natural (ya incluye prefijo)
/app/backend/server.py:4805:    RTRIM(LTRIM(movsinv.idinsumo)) as CODIGO,
/app/backend/server.py:4806:    SUM(movsinv.cantidad) as CANTIDAD
/app/backend/server.py:4807:FROM movsinv
/app/backend/server.py:4808:INNER JOIN insumos ON insumos.idinsumo = movsinv.idinsumo
/app/backend/server.py:4811:LEFT JOIN almacen ON almacen.idalmacen = movsinv.idalmacen
/app/backend/server.py:4812:WHERE movsinv.fecha BETWEEN '{fecha_ini_fmt}' AND '{fecha_fin_fmt}'
/app/backend/server.py:4813:  AND almacen.nombre LIKE '%{almacen_safe}%'
/app/backend/server.py:4815:GROUP BY RTRIM(LTRIM(movsinv.idinsumo))
/app/backend/server.py:4819:-- MOVIMIENTOS DE PRESENTACIONES (movtosalmacen)
/app/backend/server.py:4821:    RTRIM(LTRIM(movtosalmacen.idinsumospresentaciones)) as CODIGO,
/app/backend/server.py:4822:    SUM(movtosalmacen.cantidad) as CANTIDAD
/app/backend/server.py:4823:FROM movtosalmacen
/app/backend/server.py:4824:INNER JOIN insumospresentaciones ON insumospresentaciones.idinsumospresentaciones = movtosalmacen.idinsumospresentaciones
/app/backend/server.py:4827:LEFT JOIN almacen ON almacen.idalmacen = movtosalmacen.idalmacen
/app/backend/server.py:4828:WHERE movtosalmacen.fecha BETWEEN '{fecha_ini_fmt}' AND '{fecha_fin_fmt}'
/app/backend/server.py:4829:  AND almacen.nombre LIKE '%{almacen_safe}%'
/app/backend/server.py:4831:GROUP BY RTRIM(LTRIM(movtosalmacen.idinsumospresentaciones))
/app/backend/server.py:4849:            # Consulta basada en recetasalmacenes + costos + turnos
/app/backend/server.py:4851:            if es_almacen_consumo:
/app/backend/server.py:4855:                # - fecha_ini: Día del inventario inicial a las 00:00:00
/app/backend/server.py:4856:                # - fecha_fin: Día ANTERIOR al inventario final a las 23:59:59
/app/backend/server.py:4863:                    # Fecha inicio: inicio del día del inventario inicial
/app/backend/server.py:4866:                    # Fecha fin: final del día ANTERIOR al inventario final (23:59:59)
/app/backend/server.py:4879:                # El filtro usa el día del inventario inicial hasta el final del día anterior al inventario final
/app/backend/server.py:4887:INNER JOIN recetasalmacenes RC ON RC.idproducto = venta.idproducto 
/app/backend/server.py:4891:INNER JOIN almacen AL ON AL.idalmacen = RC.idalmacen
/app/backend/server.py:4899:  AND AL.nombre LIKE '%{almacen_safe}%'
/app/backend/server.py:4903:                    logging.info(f"Ejecutando consulta ventas INSUMOS para almacén {almacen}")
/app/backend/server.py:4927:INNER JOIN recetasalmacenes RC ON RC.idproducto = venta.idproducto 
/app/backend/server.py:4931:INNER JOIN almacen AL ON AL.idalmacen = RC.idalmacen
/app/backend/server.py:4939:  AND AL.nombre LIKE '%{almacen_safe}%'
/app/backend/server.py:4958:                # NOTA: La tabla recetasalmacenes solo tiene idinsumo, no tiene idinsumospresentaciones
/app/backend/server.py:4960:                # Las presentaciones se descuentan del inventario a través de los INSUMOS que las componen
/app/backend/server.py:4961:                logging.info("Ventas de PRESENTACIONES no disponibles - recetasalmacenes solo tiene idinsumo")
/app/backend/server.py:4965:                logging.info(f"Almacén tipo {almacen_tipo} (NO es consumo) - ventas = 0 para todos los productos")
/app/backend/server.py:4967:            # 7. Combinar resultados - Solo productos que aparecen en inventarios Y están en el catálogo
/app/backend/server.py:4978:                # Obtener datos de inventarios
/app/backend/server.py:4985:                # El costo viene del inventario o del catálogo
/app/backend/server.py:5007:                almacen_nombre_soft = almacen or ''  # El almacén viene como nombre en SoftRestaurant
/app/backend/server.py:5011:                    'Comentario_Ini': almacen_nombre_soft,
/app/backend/server.py:5013:                    'Comentario_Fin': almacen_nombre_soft,
/app/backend/server.py:5060:                        almacen_id_sr = ""
/app/backend/server.py:5061:                        for alm in almacenes:
/app/backend/server.py:5063:                                if alm.get('nombre') == almacen or alm.get('id'):
/app/backend/server.py:5064:                                    almacen_id_sr = alm.get('id', '')
/app/backend/server.py:5068:                                if alm == almacen:
/app/backend/server.py:5069:                                    almacen_id_sr = alm
/app/backend/server.py:5077:                            "almacen_id": almacen_id_sr or almacen,
/app/backend/server.py:5085:                            "fecha_inventario": fecha_fin or "",
/app/backend/server.py:5090:                        await db.inventario_diferencias_detalle.update_one(
/app/backend/server.py:5104:                # Determinar folio_inventario principal para SR
/app/backend/server.py:5105:                folio_inventario_principal = lista_folios_fin[0] if lista_folios_fin else None
/app/backend/server.py:5113:                    almacen_id=almacen or "",
/app/backend/server.py:5114:                    almacen_nombre=almacen or "",
/app/backend/server.py:5122:                    folio_inventario=folio_inventario_principal  # NUEVO: Pasar folio explícito
/app/backend/server.py:5143:        logging.error(f"Error en análisis de inventario: {str(e)}")
/app/backend/server.py:5166:    almacen = params.get('almacen')
/app/backend/server.py:5178:            # MPRO: Movimientos desde (fecha_inventario_inicial + 1 día) hasta fecha_inventario_final
/app/backend/server.py:5184:            almacen_safe = _escape_like_pattern(almacen) if almacen else ""
/app/backend/server.py:5188:            almacen_query = f"""
/app/backend/server.py:5189:SELECT TOP 1 A.Al_Cve_Almacen as codigo
/app/backend/server.py:5190:FROM Almacen A
/app/backend/server.py:5192:WHERE A.Al_Descripcion LIKE '%{almacen_safe}%'
/app/backend/server.py:5195:            almacen_result = execute_sql_query(
/app/backend/server.py:5197:                server['username'], server['password'], almacen_query
/app/backend/server.py:5199:            if not almacen_result:
/app/backend/server.py:5201:            almacen_codigo = almacen_result[0]['codigo']
/app/backend/server.py:5233:    A.Al_Descripcion as Almacen,
/app/backend/server.py:5238:INNER JOIN Almacen A ON A.Al_Cve_Almacen = M.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = M.Sc_Cve_Sucursal
/app/backend/server.py:5242:    AND M.Al_Cve_Almacen = '{almacen_codigo}'
/app/backend/server.py:5289:                    'almacen': row.get('Almacen'),
/app/backend/server.py:5301:            almacen_safe = _escape_like_pattern(almacen) if almacen else ""
/app/backend/server.py:5314:            logging.info(f"Detalle movimientos SoftRestaurant - Código: {producto_codigo}, Almacén: {almacen}, Fechas: {fecha_ini_fmt} a {fecha_fin_fmt}")
/app/backend/server.py:5316:            # Primero intentar buscar en PRESENTACIONES (movtosalmacen)
/app/backend/server.py:5319:    COALESCE(CAST(M.idcompra AS VARCHAR(50)), CAST(M.traspaso AS VARCHAR(50)), CAST(M.invfisico AS VARCHAR(50)), '') as Folio,
/app/backend/server.py:5326:    A.nombre as Almacen,
/app/backend/server.py:5328:FROM movtosalmacen M
/app/backend/server.py:5331:LEFT JOIN almacen A ON A.idalmacen = M.idalmacen
/app/backend/server.py:5333:    AND A.nombre LIKE '%{almacen_safe}%'
/app/backend/server.py:5353:    COALESCE(CAST(M.foliocheque AS VARCHAR(50)), CAST(M.idcompra AS VARCHAR(50)), CAST(M.traspaso AS VARCHAR(50)), CAST(M.invfisico AS VARCHAR(50)), '') as Folio,
/app/backend/server.py:5360:    A.nombre as Almacen,
/app/backend/server.py:5362:FROM movsinv M
/app/backend/server.py:5365:LEFT JOIN almacen A ON A.idalmacen = M.idalmacen
/app/backend/server.py:5367:    AND A.nombre LIKE '%{almacen_safe}%'
/app/backend/server.py:5395:                    'almacen': row.get('Almacen'),
/app/backend/server.py:5502:            # Para SoftRestaurant - detalle de ventas usando recetasalmacenes
/app/backend/server.py:5504:            almacen = params.get('almacen', '')
/app/backend/server.py:5507:            almacen_safe = _escape_like_pattern(almacen) if almacen else ""
/app/backend/server.py:5519:            logging.info(f"Detalle ventas SoftRestaurant - Código: {producto_codigo}, Almacén: {almacen}, Fechas: {fecha_ini_fmt} a {fecha_fin_fmt}")
/app/backend/server.py:5521:            # La tabla recetasalmacenes solo tiene idinsumo, no tiene idinsumospresentaciones
/app/backend/server.py:5532:    AL.nombre as Almacen
/app/backend/server.py:5536:INNER JOIN recetasalmacenes RC ON RC.idproducto = venta.idproducto 
/app/backend/server.py:5540:INNER JOIN almacen AL ON AL.idalmacen = RC.idalmacen
/app/backend/server.py:5547:  AND AL.nombre LIKE '%{almacen_safe}%'
/app/backend/server.py:5567:                    'sucursal': row.get('Almacen', '')
/app/backend/server.py:5581:    filename = data.get('filename', 'reporte_inventario.xlsx')
/app/backend/server.py:5587:        'almacen': data.get('almacen', 'N/A'),
/app/backend/server.py:5603:    filename = data.get('filename', 'reporte_inventario.pdf')
/app/backend/server.py:5614:# ============= REPORTE COMPARATIVO DE 4 ÚLTIMOS INVENTARIOS (AUDITORÍA) =============
/app/backend/server.py:5615:class AlmacenComparativo(BaseModel):
/app/backend/server.py:5620:class ComparativoInventariosRequest(BaseModel):
/app/backend/server.py:5624:    # Soporta múltiples almacenes (multi-selección)
/app/backend/server.py:5625:    almacenes: List[AlmacenComparativo]
/app/backend/server.py:5629:    almacen_id: Optional[str] = None
/app/backend/server.py:5630:    almacen_nombre: Optional[str] = ""
/app/backend/server.py:5636:    almacen_id: str,
/app/backend/server.py:5637:    almacen_nombre: str,
/app/backend/server.py:5643:    Lee las diferencias del cache inventario_diferencias_detalle.
/app/backend/server.py:5648:        logging.info(f"get_diferencias_from_cache: almacen_id={almacen_id}, sucursal_id={sucursal_id}, comentario={comentario}, fecha_ref={fecha_referencia}")
/app/backend/server.py:5650:        # 1. Obtener los últimos 4 folios de inventario para este almacén/comentario
/app/backend/server.py:5665:                A.Al_Descripcion as almacen,
/app/backend/server.py:5668:            INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
/app/backend/server.py:5669:            WHERE A.Al_Cve_Almacen = '{almacen_id}'
/app/backend/server.py:5686:                A.nombre as almacen,
/app/backend/server.py:5688:            FROM invfisico INV
/app/backend/server.py:5689:            INNER JOIN almacen A ON A.idalmacen = INV.idalmacen1
/app/backend/server.py:5690:            WHERE INV.idalmacen1 = '{almacen_id}'
/app/backend/server.py:5702:            logging.warning(f"No se encontraron inventarios para almacén {almacen_id}/{comentario}")
/app/backend/server.py:5705:        logging.info(f"Encontrados {len(cortes_result)} cortes para {almacen_id}/{comentario}: {[c['folio'] for c in cortes_result]}")
/app/backend/server.py:5723:            cached = await db.inventario_diferencias_detalle.find_one(cache_key, {"_id": 0})
/app/backend/server.py:5748:                'almacen_nombre': almacen_nombre,
/app/backend/server.py:5783:            'almacen_nombre': almacen_nombre,
/app/backend/server.py:5795:def generate_excel_comparativo_inventarios(data: List[Dict], metadata: Dict) -> bytes:
/app/backend/server.py:5797:    Genera Excel comparativo de los últimos 4 cortes de inventario.
/app/backend/server.py:5838:    ws.cell(row=row_num, column=1, value="REPORTE COMPARATIVO DE AUDITORÍA - 4 ÚLTIMOS INVENTARIOS").font = titulo_font
/app/backend/server.py:5846:        ("Almacén:", metadata.get('almacen_nombre', 'N/A')),
/app/backend/server.py:5976:@api_router.post("/reports/export/comparativo-inventarios")
/app/backend/server.py:5977:async def export_comparativo_inventarios(request: ComparativoInventariosRequest, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:5979:    Genera un Excel comparativo con las diferencias de los últimos 4 cortes de inventario.
/app/backend/server.py:5981:    Soporta múltiples almacenes (multi-selección).
/app/backend/server.py:5982:    FASE 8: Aplica validación RBAC de servidor y almacenes.
/app/backend/server.py:6003:    # FASE 8: Obtener almacenes permitidos
/app/backend/server.py:6004:    almacenes_permitidos = get_almacenes_permitidos(context, request.server_id)
/app/backend/server.py:6008:        f"Server={request.server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:6012:        # Construir lista de almacenes a procesar
/app/backend/server.py:6013:        almacenes_a_procesar = []
/app/backend/server.py:6015:        # Soportar nuevo formato (lista de almacenes) y formato anterior (single almacén)
/app/backend/server.py:6016:        if request.almacenes and len(request.almacenes) > 0:
/app/backend/server.py:6017:            almacenes_a_procesar = request.almacenes
/app/backend/server.py:6018:        elif request.almacen_id:
/app/backend/server.py:6020:            almacenes_a_procesar = [AlmacenComparativo(
/app/backend/server.py:6021:                id=request.almacen_id,
/app/backend/server.py:6022:                nombre=request.almacen_nombre or '',
/app/backend/server.py:6026:        if not almacenes_a_procesar:
/app/backend/server.py:6029:        # FASE 8: Validar que todos los almacenes solicitados estén en el alcance
/app/backend/server.py:6030:        if almacenes_permitidos:
/app/backend/server.py:6031:            for almacen in almacenes_a_procesar:
/app/backend/server.py:6032:                if almacen.id not in almacenes_permitidos:
/app/backend/server.py:6035:                        f"Almacén fuera de alcance: {almacen.id}"
/app/backend/server.py:6039:                        detail=f"No tiene acceso al almacén {almacen.nombre or almacen.id}"
/app/backend/server.py:6045:        almacenes_procesados = []
/app/backend/server.py:6048:        for almacen in almacenes_a_procesar:
/app/backend/server.py:6051:                almacen_id=almacen.id,
/app/backend/server.py:6052:                almacen_nombre=almacen.nombre,
/app/backend/server.py:6054:                comentario=almacen.comentario,
/app/backend/server.py:6068:                    if len(almacenes_a_procesar) > 1:
/app/backend/server.py:6069:                        prefijo = f"{almacen.nombre}"
/app/backend/server.py:6070:                        if almacen.comentario:
/app/backend/server.py:6071:                            prefijo += f" ({almacen.comentario})"
/app/backend/server.py:6073:                            prod['almacen_comentario'] = prefijo
/app/backend/server.py:6082:                    almacenes_procesados.append({
/app/backend/server.py:6083:                        'nombre': almacen.nombre,
/app/backend/server.py:6084:                        'comentario': almacen.comentario or '',
/app/backend/server.py:6096:            raise HTTPException(status_code=404, detail="No se encontraron diferencias de inventario para los almacenes seleccionados")
/app/backend/server.py:6099:        if len(almacenes_procesados) == 1:
/app/backend/server.py:6100:            almacen_info = almacenes_procesados[0]['nombre']
/app/backend/server.py:6101:            comentario_info = almacenes_procesados[0]['comentario'] or 'TODOS'
/app/backend/server.py:6103:            almacen_info = f"{len(almacenes_procesados)} almacenes"
/app/backend/server.py:6104:            comentario_info = ', '.join([f"{a['nombre']}({a['comentario']})" if a['comentario'] else a['nombre'] for a in almacenes_procesados])
/app/backend/server.py:6109:            'almacen_nombre': almacen_info,
/app/backend/server.py:6116:        excel_bytes = generate_excel_comparativo_inventarios(all_productos, metadata)
/app/backend/server.py:6119:        if len(almacenes_procesados) == 1:
/app/backend/server.py:6120:            nombre_archivo = almacenes_procesados[0]['nombre']
/app/backend/server.py:6121:            if almacenes_procesados[0]['comentario']:
/app/backend/server.py:6122:                nombre_archivo += f"_{almacenes_procesados[0]['comentario']}"
/app/backend/server.py:6124:            nombre_archivo = f"{len(almacenes_procesados)}_almacenes"
/app/backend/server.py:6126:        filename = f"comparativo_inventarios_{nombre_archivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
/app/backend/server.py:6137:        logging.error(f"Error generando comparativo de inventarios: {str(e)}")
/app/backend/server.py:6146:        filename = 'reporte_inventario.xlsx'
/app/backend/server.py:6149:        filename = 'reporte_inventario.pdf'
/app/backend/server.py:6154:            <h2>Reporte de Inventario</h2>
/app/backend/server.py:6486:    almacen = params.get('almacen', '')  # Nombre del almacén para filtrar
/app/backend/server.py:6502:        almacen_safe = _escape_like_pattern(almacen) if almacen else ""
/app/backend/server.py:6505:        almacen_codigo = None
/app/backend/server.py:6506:        if almacen:
/app/backend/server.py:6507:            almacen_query = f"SELECT TOP 1 Al_Cve_Almacen as codigo FROM Almacen WHERE Al_Descripcion LIKE '%{almacen_safe}%'"
/app/backend/server.py:6508:            almacen_result = execute_sql_query(
/app/backend/server.py:6510:                conn_info['username'], conn_info['password'], almacen_query
/app/backend/server.py:6512:            if almacen_result:
/app/backend/server.py:6513:                almacen_codigo = almacen_result[0]['codigo']
/app/backend/server.py:6514:                results["almacen_codigo"] = almacen_codigo
/app/backend/server.py:6517:        filtro_almacen = f"AND E.Al_Cve_Almacen = '{almacen_codigo}'" if almacen_codigo else ""
/app/backend/server.py:6531:    {filtro_almacen}
/app/backend/server.py:6582:    A.Al_Descripcion as Almacen,
/app/backend/server.py:6583:    E.Al_Cve_Almacen as Almacen_Codigo
/app/backend/server.py:6586:INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = S.Sc_Cve_Sucursal
/app/backend/server.py:6650:    Consulta para obtener datos de inventario físico de SoftRestaurant
/app/backend/server.py:6652:    Aplica filtros de departamentos (almacenes) y categorías (gruposi).
/app/backend/server.py:6656:    filtro_almacen = ""
/app/backend/server.py:6658:        almacenes_sql = ",".join([f"'{d}'" for d in departamentos])
/app/backend/server.py:6659:        filtro_almacen = f"AND INV.idalmacen1 IN ({almacenes_sql})"
/app/backend/server.py:6667:    WITH InventariosMes AS (
/app/backend/server.py:6669:            idalmacen1 as idalmacen,
/app/backend/server.py:6674:        FROM invfisico
/app/backend/server.py:6678:            {filtro_almacen.replace('INV.', '')}
/app/backend/server.py:6679:        GROUP BY idalmacen1
/app/backend/server.py:6684:        INV.idalmacen1 as idalmacen,
/app/backend/server.py:6685:        ALM.nombre as almacen_nombre,
/app/backend/server.py:6690:        DET.existenciaalmacen1 as existencia_teorica,
/app/backend/server.py:6691:        DET.fisicoalmacen1 as existencia_fisica,
/app/backend/server.py:6692:        DET.diferenciaalmacen1 as diferencia,
/app/backend/server.py:6693:        (DET.diferenciaalmacen1 * DET.costo) as costo_diferencia,
/app/backend/server.py:6698:        END as tipo_inventario
/app/backend/server.py:6699:    FROM invfisico INV
/app/backend/server.py:6700:    INNER JOIN invfisicomovtos DET ON DET.folio = INV.folio
/app/backend/server.py:6701:    INNER JOIN InventariosMes IM ON IM.idalmacen = INV.idalmacen1 
/app/backend/server.py:6706:    LEFT JOIN almacen ALM ON ALM.idalmacen = INV.idalmacen1
/app/backend/server.py:6708:    {filtro_almacen}
/app/backend/server.py:6710:    ORDER BY INV.idalmacen1, INV.folio, DET.idpresentacion
/app/backend/server.py:6716:    Consulta para obtener datos de inventario físico de MPRO
/app/backend/server.py:6718:    - Inventario inicial = último inventario del mes ANTERIOR
/app/backend/server.py:6719:    - Inventario final = último inventario del mes ACTUAL
/app/backend/server.py:6733:    WITH InventarioMesAnterior AS (
/app/backend/server.py:6734:        -- Último inventario del mes anterior (INICIAL)
/app/backend/server.py:6736:            Al_Cve_Almacen as almacen,
/app/backend/server.py:6742:        GROUP BY Al_Cve_Almacen
/app/backend/server.py:6744:    InventarioMesActual AS (
/app/backend/server.py:6745:        -- Último inventario del mes actual (FINAL)
/app/backend/server.py:6747:            Al_Cve_Almacen as almacen,
/app/backend/server.py:6753:        GROUP BY Al_Cve_Almacen
/app/backend/server.py:6758:        F.Al_Cve_Almacen as idalmacen,
/app/backend/server.py:6759:        A.Al_Descripcion as almacen_nombre,
/app/backend/server.py:6772:        END as tipo_inventario
/app/backend/server.py:6774:    LEFT JOIN InventarioMesAnterior IMA ON IMA.almacen = F.Al_Cve_Almacen
/app/backend/server.py:6775:    LEFT JOIN InventarioMesActual IMC ON IMC.almacen = F.Al_Cve_Almacen
/app/backend/server.py:6776:    INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen
/app/backend/server.py:6783:    ORDER BY F.Al_Cve_Almacen, F.Fi_Folio, F.Pr_Cve_Producto
/app/backend/server.py:6793:    Obtiene resumen de inventarios para el dashboard.
/app/backend/server.py:6865:                    "almacenes": [],
/app/backend/server.py:6868:                    "resumen_por_almacen": [],
/app/backend/server.py:6877:                "message": "No hay datos de inventario para el mes actual",
/app/backend/server.py:6880:                    "almacenes": [],
/app/backend/server.py:6883:                    "resumen_por_almacen": [],
/app/backend/server.py:6901:        # Separar inventarios inicial y final
/app/backend/server.py:6902:        df_inicial = df[df['tipo_inventario'] == 'INICIAL'].copy()
/app/backend/server.py:6903:        df_final = df[df['tipo_inventario'] == 'FINAL'].copy()
/app/backend/server.py:6905:        # KPIs generales (basados en inventario final)
/app/backend/server.py:6914:            ['codigo', 'descripcion', 'almacen_nombre', 'diferencia', 'costo_unitario', 'costo_diferencia']
/app/backend/server.py:6919:            ['codigo', 'descripcion', 'almacen_nombre', 'diferencia', 'costo_unitario', 'costo_diferencia']
/app/backend/server.py:6923:        resumen_almacen = df_final.groupby(['idalmacen', 'almacen_nombre']).agg({
/app/backend/server.py:6928:        resumen_almacen.columns = ['idalmacen', 'almacen', 'total_diferencia', 'total_costo_diferencia', 'total_items']
/app/backend/server.py:6929:        resumen_almacen = resumen_almacen.to_dict('records')
/app/backend/server.py:6941:        comparativo_almacen = []
/app/backend/server.py:6942:        almacenes = df['idalmacen'].unique()
/app/backend/server.py:6943:        for alm in almacenes:
/app/backend/server.py:6944:            df_alm_ini = df_inicial[df_inicial['idalmacen'] == alm]
/app/backend/server.py:6945:            df_alm_fin = df_final[df_final['idalmacen'] == alm]
/app/backend/server.py:6948:                alm_nombre = df_alm_fin['almacen_nombre'].iloc[0] if len(df_alm_fin) > 0 else df_alm_ini['almacen_nombre'].iloc[0]
/app/backend/server.py:6949:                comparativo_almacen.append({
/app/backend/server.py:6950:                    'almacen': alm,
/app/backend/server.py:6951:                    'almacen_nombre': alm_nombre,
/app/backend/server.py:6960:        # Obtener lista de almacenes únicos
/app/backend/server.py:6961:        almacenes_list = df[['idalmacen', 'almacen_nombre']].drop_duplicates().to_dict('records')
/app/backend/server.py:6970:                "almacenes": almacenes_list,
/app/backend/server.py:6975:                    "precision_inventario": round(precision, 2),
/app/backend/server.py:6981:                "resumen_por_almacen": resumen_almacen,
/app/backend/server.py:6983:                "comparativo_almacen": comparativo_almacen
/app/backend/server.py:7054:    dias_inventario: int = 10  # Días de inventario a comprar
/app/backend/server.py:7059:class CalculoPedidoRequest(BaseModel):
/app/backend/server.py:7062:    almacenes: List[str]  # Puede ser uno, varios, o "TODOS"
/app/backend/server.py:7063:    fecha_inventario_fisico: str  # Fecha del inventario físico inicial
/app/backend/server.py:7065:    dias_inventario: int = 10  # Días de inventario a comprar
/app/backend/server.py:7067:    folio_inventario_fisico: Optional[str] = None
/app/backend/server.py:7070:    folio_pedido_comparar: Optional[str] = None  # Para comparar con pedido existente
/app/backend/server.py:7082:# - GET /compras/inventarios-fisicos/{server_id}
/app/backend/server.py:7083:# - GET /compras/pedidos-vigentes/{server_id}  
/app/backend/server.py:7086:# - GET /compras/detalle-pedido/{server_id}/{folio}
/app/backend/server.py:7087:# - GET /compras/detalle-pedido-manual/{server_id}
/app/backend/server.py:7090:# - POST /compras/calculo-pedido (~420 líneas)
/app/backend/server.py:7102:# - Cálculo de pedidos sugeridos
/app/backend/server.py:7164:@api_router.get("/compras/inventarios-fisicos/{server_id}")
/app/backend/server.py:7165:async def obtener_inventarios_fisicos(server_id: str, sucursal: str = None, sucursal_id: str = None, almacen: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7167:    Obtiene la lista de inventarios físicos disponibles para seleccionar.
/app/backend/server.py:7170:    1. Primero intenta leer de EDARSAHUB (tabla Compras_Inventarios_Fisicos_Sync)
/app/backend/server.py:7173:    FASE 8: Aplica filtro RBAC por almacenes permitidos.
/app/backend/server.py:7180:    # FASE 8: Obtener almacenes permitidos
/app/backend/server.py:7181:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:7184:        f"[COMPRAS-HIBRIDO] Inventarios físicos - "
/app/backend/server.py:7186:        f"AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:7202:        inventarios = obtener_inventarios_fisicos_sync(
/app/backend/server.py:7206:            almacen=almacen,
/app/backend/server.py:7210:        if inventarios and len(inventarios) > 0:
/app/backend/server.py:7212:            if almacenes_permitidos:
/app/backend/server.py:7213:                inventarios = [
/app/backend/server.py:7214:                    inv for inv in inventarios 
/app/backend/server.py:7215:                    if inv.get('almacen_id') in almacenes_permitidos 
/app/backend/server.py:7216:                    or not almacenes_permitidos
/app/backend/server.py:7219:            logging.info(f"[COMPRAS-HIBRIDO] ✅ Inventarios desde SYNC: {len(inventarios)} registros")
/app/backend/server.py:7224:                "almacen": inv.get('almacen', 'Sin almacén'),
/app/backend/server.py:7225:                "almacen_id": str(inv.get('almacen_id', '')),
/app/backend/server.py:7232:            } for inv in inventarios]
/app/backend/server.py:7242:        almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "A.Al_Cve_Almacen")
/app/backend/server.py:7243:        almacen_safe = _escape_like_pattern(almacen) if almacen else ""
/app/backend/server.py:7246:        almacen_filtro = ""
/app/backend/server.py:7247:        if almacen and almacen != "TODOS":
/app/backend/server.py:7248:            almacen_filtro = f"AND A.Al_Descripcion LIKE '%{almacen_safe}%'"
/app/backend/server.py:7262:    A.Al_Descripcion as almacen, A.Al_Cve_Almacen as almacen_id,
/app/backend/server.py:7267:INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
/app/backend/server.py:7269:WHERE {sucursal_filtro} {almacen_filtro} {almacen_rbac_filter}
/app/backend/server.py:7270:GROUP BY F.Fi_Folio, F.Fi_Fecha, A.Al_Descripcion, A.Al_Cve_Almacen, S.Sc_Descripcion, A.Sc_Cve_Sucursal, F.Fi_Comentario
/app/backend/server.py:7278:            logging.info(f"[COMPRAS-HIBRIDO] ✅ MPRO LIVE: {len(result)} inventarios")
/app/backend/server.py:7279:            return [{"folio": r['folio'], "fecha": str(r['fecha']), "almacen": r['almacen'], 
/app/backend/server.py:7280:                     "almacen_id": r.get('almacen_id', ''), "sucursal": r.get('sucursal', ''),
/app/backend/server.py:7285:            log_compras_error("inventarios-fisicos", server_id, "CONNECTION_ERROR", error_msg[:200], server.get('system_type'))
/app/backend/server.py:7288:            raise HTTPException(status_code=500, detail=f"Error consultando inventarios: {error_msg[:200]}")
/app/backend/server.py:7291:        almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "A.idalmacen")
/app/backend/server.py:7292:        almacen_safe = _escape_like_pattern(almacen) if almacen else ""
/app/backend/server.py:7294:        almacen_filtro = ""
/app/backend/server.py:7295:        if almacen and almacen != "TODOS":
/app/backend/server.py:7296:            almacen_filtro = f"AND A.nombre LIKE '%{almacen_safe}%'"
/app/backend/server.py:7301:    A.nombre as almacen, A.idalmacen as almacen_id, '' as comentario
/app/backend/server.py:7302:FROM invfisico INV
/app/backend/server.py:7303:LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
/app/backend/server.py:7304:WHERE 1=1 {almacen_filtro} {almacen_rbac_filter}
/app/backend/server.py:7312:            logging.info(f"[COMPRAS-HIBRIDO] ✅ SoftRestaurant LIVE: {len(result)} inventarios")
/app/backend/server.py:7314:                     "almacen": r['almacen'] or 'Sin almacén', "almacen_id": str(r.get('almacen_id', '')),
/app/backend/server.py:7317:            log_compras_error("inventarios-fisicos", server_id, "QUERY_ERROR", str(e), server.get('system_type'))
/app/backend/server.py:7318:            raise HTTPException(status_code=500, detail=f"Error consultando inventarios: {str(e)[:200]}")
/app/backend/server.py:7322:    log_compras_error("inventarios-fisicos", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/server.py:7325:@api_router.get("/compras/pedidos-vigentes/{server_id}")
/app/backend/server.py:7326:async def obtener_pedidos_vigentes(server_id: str, sucursal: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7328:    Obtiene la lista de REQUISICIONES de compra SIN AUTORIZAR (estado PXA) para comparar.
/app/backend/server.py:7331:    1. Primero intenta leer de EDARSAHUB (tabla Compras_Requisiciones_Sync)
/app/backend/server.py:7339:        f"[COMPRAS-HIBRIDO] Requisiciones - "
/app/backend/server.py:7356:        requisiciones = obtener_requisiciones_sync(
/app/backend/server.py:7363:        if requisiciones and len(requisiciones) > 0:
/app/backend/server.py:7364:            logging.info(f"[COMPRAS-HIBRIDO] ✅ Requisiciones desde SYNC: {len(requisiciones)} registros")
/app/backend/server.py:7377:            } for req in requisiciones]
/app/backend/server.py:7379:        logging.warning(f"[COMPRAS-HIBRIDO] Error leyendo Sync requisiciones, intentando LIVE: {e}")
/app/backend/server.py:7413:            logging.info(f"[COMPRAS-HIBRIDO] ✅ MPRO LIVE: {len(result)} requisiciones")
/app/backend/server.py:7420:            log_compras_error("pedidos-vigentes", server_id, "CONNECTION_ERROR", error_msg[:200], server.get('system_type'))
/app/backend/server.py:7423:            raise HTTPException(status_code=500, detail=f"Error consultando requisiciones: {error_msg[:200]}")
/app/backend/server.py:7433:FROM ordenescompra OC
/app/backend/server.py:7435:LEFT JOIN ordenescompramov OCM ON OCM.idordencompra = OC.idordencompra
/app/backend/server.py:7446:            logging.info(f"[COMPRAS-HIBRIDO] ✅ SoftRestaurant LIVE: {len(result)} requisiciones")
/app/backend/server.py:7452:            logging.warning(f"Error obteniendo pedidos SoftRestaurant: {e}")
/app/backend/server.py:7457:@api_router.get("/compras/detalle-pedido-manual/{server_id}")
/app/backend/server.py:7458:async def obtener_detalle_pedido_manual(server_id: str, folio: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7465:        # Buscar primero en REQUISICION_COMPRA_DETALLE (tabla principal)
/app/backend/server.py:7470:FROM Requisicion_Compra_Detalle RCD
/app/backend/server.py:7472:INNER JOIN Requisicion_Compra RC ON RC.Rc_Folio = RCD.Rc_Folio
/app/backend/server.py:7485:        # Si no encuentra en requisición, buscar en pedido/orden (legacy)
/app/backend/server.py:7487:SELECT 'PEDIDO' as tipo, PDD.Pr_Cve_Producto as codigo, P.Pr_Descripcion as producto,
/app/backend/server.py:7489:FROM Pedido_Detalle PDD
/app/backend/server.py:7513:async def obtener_detalle_movimientos(server_id: str, codigo_producto: str, almacenes: str, fecha_ini: str, fecha_fin: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7519:    almacen_list = almacenes.split(',')
/app/backend/server.py:7520:    almacen_codigos_str = ",".join([f"'{a}'" for a in almacen_list])
/app/backend/server.py:7530:    A.Al_Descripcion as almacen
/app/backend/server.py:7533:INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen
/app/backend/server.py:7535:    AND E.Al_Cve_Almacen IN ({almacen_codigos_str})
/app/backend/server.py:7545:                 "entrada_salida": r['tipo'], "cantidad": float(r['cantidad'] or 0), "almacen": r['almacen']} for r in result]
/app/backend/server.py:7584:@api_router.get("/compras/detalle-pedido/{server_id}/{folio}")
/app/backend/server.py:7585:async def obtener_detalle_pedido(server_id: str, folio: str, tipo: str = "PEDIDO", credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7587:    Obtiene el detalle de un pedido/orden de compra para comparar.
/app/backend/server.py:7596:        f"[RBAC-DETALLE-PEDIDO] Usuario={access['user'].get('email')}, "
/app/backend/server.py:7601:        if tipo == "PEDIDO":
/app/backend/server.py:7609:FROM Pedido_Detalle PDD
/app/backend/server.py:7631:@api_router.post("/compras/calculo-pedido")
/app/backend/server.py:7632:async def calcular_pedido_sugerido(request: CalculoPedidoRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7634:    Calcula el pedido sugerido basándose en:
/app/backend/server.py:7635:    1. Inventario inicial (físico capturado en fecha_inventario_fisico)
/app/backend/server.py:7638:    4. = Inventario Teórico Actual
/app/backend/server.py:7640:       - consumo: (Promedio Diario × Días Inventario) - Disponible
/app/backend/server.py:7642:    FASE 8: Aplica validación RBAC de servidor y almacenes.
/app/backend/server.py:7649:    # FASE 8: Obtener almacenes permitidos
/app/backend/server.py:7650:    almacenes_permitidos = get_almacenes_permitidos(context, request.server_id)
/app/backend/server.py:7653:        f"[RBAC-CALCULO-PEDIDO] Usuario={access['user'].get('email')}, "
/app/backend/server.py:7654:        f"Server={request.server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:7658:    almacenes = request.almacenes  # Lista de almacenes o ["TODOS"]
/app/backend/server.py:7659:    fecha_inv_fisico = request.fecha_inventario_fisico
/app/backend/server.py:7661:    dias_inventario = request.dias_inventario
/app/backend/server.py:7663:    folio_inv = request.folio_inventario_fisico
/app/backend/server.py:7676:    logging.info(f"[COMPRAS] Parámetros: sucursal={sucursal}, almacenes={almacenes}")
/app/backend/server.py:7678:    logging.info(f"[COMPRAS] Método: {metodo}, Días inventario: {dias_inventario}")
/app/backend/server.py:7681:        # FASE 8: Agregar filtro RBAC a la query de almacenes
/app/backend/server.py:7682:        almacen_rbac_filter = get_almacenes_sql_filter(context, request.server_id, "A.Al_Cve_Almacen")
/app/backend/server.py:7687:        # Obtener códigos de almacenes
/app/backend/server.py:7688:        if "TODOS" in almacenes:
/app/backend/server.py:7689:            almacen_query = f"""
/app/backend/server.py:7690:SELECT A.Al_Cve_Almacen as codigo, A.Al_Descripcion as nombre, A.Sc_Cve_Sucursal as sucursal_codigo
/app/backend/server.py:7691:FROM Almacen A
/app/backend/server.py:7693:WHERE S.Sc_Descripcion LIKE '%{sucursal_safe}%' AND A.Es_Cve_Estado <> 'BA'{almacen_rbac_filter}
/app/backend/server.py:7697:            almacen_likes = " OR ".join([f"A.Al_Descripcion LIKE '%{_escape_like_pattern(a)}%'" for a in almacenes])
/app/backend/server.py:7698:            almacen_query = f"""
/app/backend/server.py:7699:SELECT A.Al_Cve_Almacen as codigo, A.Al_Descripcion as nombre, A.Sc_Cve_Sucursal as sucursal_codigo
/app/backend/server.py:7700:FROM Almacen A
/app/backend/server.py:7702:WHERE S.Sc_Descripcion LIKE '%{sucursal_safe}%' AND ({almacen_likes}) AND A.Es_Cve_Estado <> 'BA'{almacen_rbac_filter}
/app/backend/server.py:7705:        almacen_result = execute_sql_query(
/app/backend/server.py:7707:            server['username'], server['password'], almacen_query
/app/backend/server.py:7709:        if not almacen_result:
/app/backend/server.py:7710:            raise HTTPException(status_code=404, detail=f"No se encontraron almacenes para sucursal '{sucursal}'")
/app/backend/server.py:7712:        almacen_codigos = [a['codigo'] for a in almacen_result]
/app/backend/server.py:7713:        almacen_nombres = [a['nombre'] for a in almacen_result]
/app/backend/server.py:7714:        sucursal_codigo = almacen_result[0]['sucursal_codigo']
/app/backend/server.py:7715:        # Solo es bodega si TODOS los almacenes seleccionados son bodegas (no solo algunos)
/app/backend/server.py:7716:        es_bodega = all('BODEGA' in (a['nombre'] or '').upper() for a in almacen_result)
/app/backend/server.py:7718:        almacen_codigos_str = ",".join([f"'{c}'" for c in almacen_codigos])
/app/backend/server.py:7720:        logging.info(f"[COMPRAS] Almacenes encontrados: {almacen_nombres}")
/app/backend/server.py:7733:        # Verificar folio de inventario físico
/app/backend/server.py:7735:            folio_inventario = folio_inv
/app/backend/server.py:7736:            fecha_inventario = fecha_inv_fisico
/app/backend/server.py:7737:            tiene_inventario_fisico = True
/app/backend/server.py:7742:FROM Fisico WHERE Al_Cve_Almacen IN ({almacen_codigos_str})
/app/backend/server.py:7749:            tiene_inventario_fisico = len(inv_result) > 0
/app/backend/server.py:7750:            folio_inventario = inv_result[0]['folio'] if tiene_inventario_fisico else None
/app/backend/server.py:7751:            fecha_inventario = inv_result[0]['fecha'] if tiene_inventario_fisico else None
/app/backend/server.py:7753:        logging.info(f"[COMPRAS] Inventario físico: folio={folio_inventario}, fecha={fecha_inventario}")
/app/backend/server.py:7755:        # 1. Obtener catálogo de productos - MISMA LÓGICA DEL REPORTE DE INVENTARIOS
/app/backend/server.py:7794:        # 2. Obtener inventario físico
/app/backend/server.py:7795:        inventario_dict = {}
/app/backend/server.py:7796:        if tiene_inventario_fisico:
/app/backend/server.py:7800:WHERE Al_Cve_Almacen IN ({almacen_codigos_str}) AND Fi_Folio = '{folio_inventario}'
/app/backend/server.py:7807:            inventario_dict = {i['Codigo']: float(i['Cantidad'] or 0) for i in inv_detalle}
/app/backend/server.py:7808:            logging.info(f"[COMPRAS] Inventario físico: {len(inventario_dict)} productos")
/app/backend/server.py:7811:        # Usa la misma lógica de fechas del reporte de inventarios: desde fecha_inv + 1
/app/backend/server.py:7816:WHERE E.Al_Cve_Almacen IN ({almacen_codigos_str})
/app/backend/server.py:7877:WHERE M.Al_Cve_Almacen IN ({almacen_codigos_str}) AND TM.Tm_Tipo = 'S'
/app/backend/server.py:7888:        # 5. Obtener inventario físico FINAL (si existe folio en fecha_fin)
/app/backend/server.py:7895:WHERE Al_Cve_Almacen IN ({almacen_codigos_str})
/app/backend/server.py:7906:            # Obtener detalle del inventario final
/app/backend/server.py:7910:WHERE Al_Cve_Almacen IN ({almacen_codigos_str}) AND Fi_Folio = '{folio_inv_final}'
/app/backend/server.py:7918:            logging.info(f"[COMPRAS] Inventario FINAL encontrado: folio={folio_inv_final}, {len(inv_final_dict)} productos")
/app/backend/server.py:7920:            logging.info(f"[COMPRAS] No hay inventario físico en fecha fin {fecha_fin}")
/app/backend/server.py:7922:        # 6. Obtener pedido existente para comparar (si se especificó)
/app/backend/server.py:7923:        pedido_existente = {}
/app/backend/server.py:7924:        productos_pedido = set()  # Para filtrar 1:1
/app/backend/server.py:7925:        if request.folio_pedido_comparar:
/app/backend/server.py:7926:            # Buscar primero en REQUISICION_COMPRA_DETALLE
/app/backend/server.py:7929:FROM Requisicion_Compra_Detalle RCD WHERE RCD.Rc_Folio = '{request.folio_pedido_comparar}'
/app/backend/server.py:7936:            # Si no encuentra en requisición, buscar en pedido/orden (legacy)
/app/backend/server.py:7940:FROM Pedido_Detalle PDD WHERE PDD.Pd_Folio = '{request.folio_pedido_comparar}'
/app/backend/server.py:7943:FROM Orden_Compra_Detalle OCD WHERE OCD.Oc_Folio = '{request.folio_pedido_comparar}'
/app/backend/server.py:7950:            pedido_existente = {p['codigo']: float(p['cantidad'] or 0) for p in ped_result}
/app/backend/server.py:7951:            productos_pedido = set(pedido_existente.keys())
/app/backend/server.py:7952:            logging.info(f"[COMPRAS] Pedido a comparar: {len(pedido_existente)} productos")
/app/backend/server.py:7954:        # 7. Calcular pedido sugerido
/app/backend/server.py:7956:        productos_sin_inventario = []
/app/backend/server.py:7961:            # FILTRO 1:1: Si se está comparando con un pedido, SOLO incluir productos de ese pedido
/app/backend/server.py:7962:            if productos_pedido and codigo not in productos_pedido:
/app/backend/server.py:7965:            inv_fisico = inventario_dict.get(codigo, 0)
/app/backend/server.py:7974:            # Inventario Teórico = Inv. Físico + Movimientos - Consumos
/app/backend/server.py:7975:            inventario_teorico = inv_fisico + movimientos - consumos
/app/backend/server.py:7983:                cantidad_pedir = max(0, stock_max - inventario_teorico)
/app/backend/server.py:7986:                consumo_esperado = promedio_diario * dias_inventario
/app/backend/server.py:7987:                cantidad_pedir = max(0, consumo_esperado - inventario_teorico)
/app/backend/server.py:7989:            # Días de inventario actual
/app/backend/server.py:7990:            dias_inv_actual = inventario_teorico / promedio_diario if promedio_diario > 0 else 999
/app/backend/server.py:7992:            # Flag sin inventario físico inicial
/app/backend/server.py:7994:            # Flag sin inventario final (existe folio pero el producto no está)
/app/backend/server.py:7997:            # Cantidad en pedido existente
/app/backend/server.py:7998:            cant_pedido_exist = pedido_existente.get(codigo, 0)
/app/backend/server.py:7999:            diferencia_pedido = cantidad_pedir - cant_pedido_exist if cant_pedido_exist > 0 else None
/app/backend/server.py:8002:            if inv_fisico > 0 or movimientos != 0 or consumos > 0 or cant_pedido_exist > 0 or (inv_final is not None and inv_final > 0):
/app/backend/server.py:8010:                    'Inventario_Inicial': round(inv_fisico, 2),
/app/backend/server.py:8013:                    'Inventario_Final': round(inv_final, 2) if inv_final is not None else None,
/app/backend/server.py:8014:                    'Inventario_Teorico': round(inventario_teorico, 2),
/app/backend/server.py:8016:                    'Dias_Inventario': round(dias_inv_actual, 1) if dias_inv_actual < 999 else 999,
/app/backend/server.py:8020:                    'Costo_Pedido': round(cantidad_pedir * costo, 2),
/app/backend/server.py:8021:                    'Sin_Inventario_Inicial': sin_inv_fisico_ini,
/app/backend/server.py:8022:                    'Sin_Inventario_Final': sin_inv_final,
/app/backend/server.py:8023:                    'Cantidad_Pedido_Existente': round(cant_pedido_exist, 2) if cant_pedido_exist > 0 else None,
/app/backend/server.py:8024:                    'Diferencia_Pedido': round(diferencia_pedido, 2) if diferencia_pedido is not None else None
/app/backend/server.py:8029:                    productos_sin_inventario.append(codigo)
/app/backend/server.py:8039:            "tiene_inventario_fisico": tiene_inventario_fisico,
/app/backend/server.py:8040:            "fecha_inventario_fisico": str(fecha_inventario) if fecha_inventario else fecha_inv_fisico,
/app/backend/server.py:8041:            "folio_inventario_fisico": folio_inventario,
/app/backend/server.py:8042:            "tiene_inventario_final": folio_inv_final is not None,
/app/backend/server.py:8043:            "fecha_inventario_final": str(fecha_inv_final) if fecha_inv_final else None,
/app/backend/server.py:8044:            "folio_inventario_final": folio_inv_final,
/app/backend/server.py:8045:            "productos_sin_inventario": len(productos_sin_inventario),
/app/backend/server.py:8047:            "almacenes": almacen_nombres,
/app/backend/server.py:8048:            "almacen_codigos": almacen_codigos,
/app/backend/server.py:8051:            "comparando_con_pedido": request.folio_pedido_comparar,
/app/backend/server.py:8054:                "fecha_inventario_fisico": fecha_inv_fisico,
/app/backend/server.py:8056:                "dias_inventario": dias_inventario,
/app/backend/server.py:8119:    almacenes: List[str]
/app/backend/server.py:8123:    fecha_auditoria: str  # Fecha del inventario final o actual
/app/backend/server.py:8126:    folio_requisicion: Optional[str] = None  # Requisición a comparar (una sola)
/app/backend/server.py:8127:    folios_requisiciones: Optional[List[str]] = None  # Múltiples requisiciones
/app/backend/server.py:8128:    inventario_manual: Optional[List[Dict]] = None  # Para captura manual si no hay folio
/app/backend/server.py:8129:    inventario_fisico_actual: Optional[List[Dict]] = None  # Captura manual del inv físico del día del pedido
/app/backend/server.py:8130:    solo_skus_requisicion: bool = True  # Por defecto solo muestra SKUs de las requisiciones
/app/backend/server.py:8131:    dias_objetivo_default: int = 10  # Días de inventario objetivo por defecto
/app/backend/server.py:8138:    folios_requisiciones: Optional[List[str]] = None
/app/backend/server.py:8143:    Obtiene la lista de productos de los inventarios iniciales y/o requisiciones
/app/backend/server.py:8144:    para inicializar la captura manual de inventario físico.
/app/backend/server.py:8158:            # Obtener productos de inventarios iniciales
/app/backend/server.py:8170:FROM invfisicomovtos INM
/app/backend/server.py:8188:            # Obtener productos de requisiciones
/app/backend/server.py:8189:            if request.folios_requisiciones:
/app/backend/server.py:8190:                folios_sql = ", ".join([f"'{f}'" for f in request.folios_requisiciones])
/app/backend/server.py:8196:FROM ordenescompramov OCM
/app/backend/server.py:8197:INNER JOIN ordenescompra OC ON OC.idordencompra = OCM.idordencompra
/app/backend/server.py:8216:            # Para MPRO - Obtener productos de inventarios iniciales
/app/backend/server.py:8241:            # MPRO - Obtener productos de requisiciones/órdenes de compra
/app/backend/server.py:8242:            if request.folios_requisiciones:
/app/backend/server.py:8243:                folios_sql = ", ".join([f"'{f}'" for f in request.folios_requisiciones])
/app/backend/server.py:8299:                # Último intento: Requisicion_Compra_Detalle
/app/backend/server.py:8306:FROM Requisicion_Compra_Detalle RCD
/app/backend/server.py:8324:                        logging.warning(f"[MPRO] Error en Requisicion_Compra_Detalle (esperado si no existe): {e}")
/app/backend/server.py:8340:    1. Inventario Inicial + Compras - Consumos = Existencia Teórica
/app/backend/server.py:8341:    2. Compara vs Inventario Físico (folio o captura manual)
/app/backend/server.py:8402:            # PASO 1: Determinar tipo de almacenes seleccionados
/app/backend/server.py:8405:            almacenes_str = ", ".join([f"'{a}'" for a in request.almacenes])
/app/backend/server.py:8407:SELECT idalmacen, nombre, ISNULL(tipo, 1) as tipo
/app/backend/server.py:8408:FROM almacen
/app/backend/server.py:8409:WHERE nombre IN ({almacenes_str}) OR idalmacen IN ({almacenes_str})
/app/backend/server.py:8416:            almacenes_bodega = [a['idalmacen'] for a in tipos_alm_result if a['tipo'] == 2]
/app/backend/server.py:8417:            almacenes_consumo = [a['idalmacen'] for a in tipos_alm_result if a['tipo'] == 1]
/app/backend/server.py:8419:            es_solo_bodega = len(almacenes_bodega) > 0 and len(almacenes_consumo) == 0
/app/backend/server.py:8420:            es_solo_consumo = len(almacenes_consumo) > 0 and len(almacenes_bodega) == 0
/app/backend/server.py:8421:            es_mixto = len(almacenes_bodega) > 0 and len(almacenes_consumo) > 0
/app/backend/server.py:8423:            logging.info(f"[AUDITORIA] Almacenes - Bodega: {almacenes_bodega}, Consumo: {almacenes_consumo}")
/app/backend/server.py:8426:            # PASO 2: Obtener SKUs de las requisiciones seleccionadas (para filtrar)
/app/backend/server.py:8427:            folios_req = request.folios_requisiciones if request.folios_requisiciones else ([request.folio_requisicion] if request.folio_requisicion else [])
/app/backend/server.py:8429:            skus_requisicion = set()
/app/backend/server.py:8431:            requi_list = []  # Lista para mantener el orden por proveedor-pedido
/app/backend/server.py:8436:                # Obtener cada línea de pedido con su folio y proveedor
/app/backend/server.py:8441:    OCM.cantidad as cantidad_pedido,
/app/backend/server.py:8446:    OC.folio as folio_pedido,
/app/backend/server.py:8449:FROM ordenescompramov OCM
/app/backend/server.py:8450:INNER JOIN ordenescompra OC ON OC.idordencompra = OCM.idordencompra
/app/backend/server.py:8465:                    skus_requisicion.add(codigo)
/app/backend/server.py:8467:                    # Guardar en lista para mantener orden por proveedor-pedido
/app/backend/server.py:8470:                        'cantidad': float(r['cantidad_pedido'] or 0),
/app/backend/server.py:8476:                        'folio_pedido': str(r.get('folio_pedido', '')).strip(),
/app/backend/server.py:8484:                            'cantidad': float(r['cantidad_pedido'] or 0),
/app/backend/server.py:8490:                            'folio_pedido': str(r.get('folio_pedido', '')).strip(),
/app/backend/server.py:8494:                logging.info(f"[AUDITORIA] SKUs en requisiciones: {len(skus_requisicion)}, Líneas de pedido: {len(requi_list)}")
/app/backend/server.py:8496:            # PASO 3: Obtener inventario inicial
/app/backend/server.py:8511:                    # Determinar el tipo de almacén de este inventario específico
/app/backend/server.py:8513:SELECT A.tipo, A.nombre, INV.idalmacen1
/app/backend/server.py:8514:FROM invfisico INV
/app/backend/server.py:8515:LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
/app/backend/server.py:8524:                    tipo_almacen = tipo_result[0]['tipo'] if tipo_result else 1
/app/backend/server.py:8525:                    es_bodega = tipo_almacen == 2
/app/backend/server.py:8527:                    logging.info(f"[AUDITORIA] Procesando inv inicial folio={folio_inv}, tipo_almacen={tipo_almacen}, es_bodega={es_bodega}")
/app/backend/server.py:8529:                    # Query para obtener datos del inventario
/app/backend/server.py:8540:    INM.fisicoalmacen1 as cantidad,
/app/backend/server.py:8544:FROM invfisicomovtos INM
/app/backend/server.py:8572:                        # Sumar al diccionario (puede haber mismo producto en múltiples inventarios)
/app/backend/server.py:8619:FROM movtosalmacen M
/app/backend/server.py:8640:FROM movsinv M
/app/backend/server.py:8658:FROM movsinv M
/app/backend/server.py:8681:FROM movtosalmacen M
/app/backend/server.py:8706:                # Para bodega, las salidas son traspasos a consumo (usa movtosalmacen)
/app/backend/server.py:8713:FROM movtosalmacen M
/app/backend/server.py:8750:            # PASO 6: Obtener inventario final (físico del día del pedido)
/app/backend/server.py:8753:            if request.inventario_fisico_actual:
/app/backend/server.py:8754:                # Captura manual del inventario físico del día del pedido
/app/backend/server.py:8759:                } for item in request.inventario_fisico_actual}
/app/backend/server.py:8770:                        # Determinar el tipo de almacén de este inventario específico
/app/backend/server.py:8772:SELECT A.tipo, A.nombre, INV.idalmacen1
/app/backend/server.py:8773:FROM invfisico INV
/app/backend/server.py:8774:LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
/app/backend/server.py:8782:                        tipo_almacen = tipo_result[0]['tipo'] if tipo_result else 1
/app/backend/server.py:8783:                        es_bodega = tipo_almacen == 2
/app/backend/server.py:8785:                        logging.info(f"[AUDITORIA] Procesando inv final folio={folio_inv}, tipo_almacen={tipo_almacen}, es_bodega={es_bodega}")
/app/backend/server.py:8796:    INM.fisicoalmacen1 as cantidad, 
/app/backend/server.py:8800:FROM invfisicomovtos INM
/app/backend/server.py:8839:                elif request.inventario_manual:
/app/backend/server.py:8844:                    } for item in request.inventario_manual}
/app/backend/server.py:8847:            # FILTRAR SOLO POR SKUs DE LA REQUISICIÓN (si solo_skus_requisicion está activo)
/app/backend/server.py:8853:            # Determinar qué procesar: usar requi_list para mantener orden por proveedor-pedido
/app/backend/server.py:8854:            if request.solo_skus_requisicion and requi_list:
/app/backend/server.py:8855:                # Procesar en orden por proveedor-pedido usando la lista de requisiciones
/app/backend/server.py:8856:                logging.info(f"[AUDITORIA] Procesando {len(requi_list)} líneas de pedido por proveedor-pedido")
/app/backend/server.py:8870:                    cantidad_pedido = item.get('cantidad', 0)
/app/backend/server.py:8872:                    folio_pedido = item.get('folio_pedido', '')
/app/backend/server.py:8898:                        "folio_pedido": folio_pedido,
/app/backend/server.py:8912:                        "dias_inventario": round(dias_inv, 1) if dias_inv < 999 else "N/A",
/app/backend/server.py:8914:                        "cantidad_pedido": cantidad_pedido,
/app/backend/server.py:8916:                        "recomendacion": "COMPRAR" if debe_comprar and cantidad_pedido > 0 else "OK" if not debe_comprar else "SIN PEDIDO",
/app/backend/server.py:8941:                    # Obtener producto desde requisición primero, luego de inventarios
/app/backend/server.py:8946:                    cantidad_pedido = requi_dict.get(codigo, {}).get('cantidad', 0) if isinstance(requi_dict.get(codigo), dict) else requi_dict.get(codigo, 0)
/app/backend/server.py:8961:                    # Días de inventario disponible
/app/backend/server.py:8979:                    if producto or codigo in skus_requisicion:
/app/backend/server.py:8980:                        # Obtener folio_pedido si existe
/app/backend/server.py:8981:                        folio_pedido = requi_dict.get(codigo, {}).get('folio_pedido', '') if isinstance(requi_dict.get(codigo), dict) else ''
/app/backend/server.py:8989:                            "folio_pedido": folio_pedido,
/app/backend/server.py:9003:                            "dias_inventario": round(dias_inv, 1) if dias_inv < 999 else "N/A",
/app/backend/server.py:9005:                            "cantidad_pedido": cantidad_pedido,
/app/backend/server.py:9007:                            "recomendacion": "COMPRAR" if debe_comprar and cantidad_pedido > 0 else "OK" if not debe_comprar else "SIN PEDIDO",
/app/backend/server.py:9025:            # (cuando se filtra, ya viene ordenado por proveedor-pedido)
/app/backend/server.py:9026:            if not (request.solo_skus_requisicion and requi_list):
/app/backend/server.py:9038:            "folios_requisiciones": folios_req
/app/backend/server.py:9054:    almacenes: Optional[List[str]] = None
/app/backend/server.py:9058:# INVENTARIOS PROVISIONALES - CAPTURA MANUAL
/app/backend/server.py:9059:# Tabla: EDARSAHUB.dbo.Auditoria_Inventario_Provisional
/app/backend/server.py:9062:class InventarioProvisionalItem(BaseModel):
/app/backend/server.py:9067:    almacen: Optional[str] = None
/app/backend/server.py:9070:class InventarioProvisionalRequest(BaseModel):
/app/backend/server.py:9076:    items: List[InventarioProvisionalItem]
/app/backend/server.py:9079:@api_router.post("/compras/inventarios-provisionales")
/app/backend/server.py:9080:async def guardar_inventario_provisional(
/app/backend/server.py:9081:    request: InventarioProvisionalRequest,
/app/backend/server.py:9085:    Guarda inventarios provisionales (captura manual) en EDARSAHUB.
/app/backend/server.py:9086:    Permite persistir la captura manual del inventario físico antes de ejecutar la auditoría.
/app/backend/server.py:9108:                INSERT INTO Auditoria_Inventario_Provisional 
/app/backend/server.py:9112:                 almacen, notas, estado)
/app/backend/server.py:9127:                item.almacen,
/app/backend/server.py:9148:@api_router.get("/compras/inventarios-provisionales/{unidad_negocio_id}")
/app/backend/server.py:9149:async def obtener_inventarios_provisionales(
/app/backend/server.py:9155:    Obtiene inventarios provisionales guardados para una unidad de negocio.
/app/backend/server.py:9174:                   almacen, notas, estado, auditoria_ejecutada
/app/backend/server.py:9175:            FROM Auditoria_Inventario_Provisional
/app/backend/server.py:9208:@api_router.delete("/compras/inventarios-provisionales/{item_id}")
/app/backend/server.py:9209:async def eliminar_inventario_provisional(
/app/backend/server.py:9214:    Elimina un item del inventario provisional.
/app/backend/server.py:9231:            DELETE FROM Auditoria_Inventario_Provisional 
/app/backend/server.py:9252:@api_router.delete("/compras/inventarios-provisionales/limpiar/{unidad_negocio_id}")
/app/backend/server.py:9253:async def limpiar_inventarios_provisionales(
/app/backend/server.py:9259:    Limpia todos los inventarios provisionales de una unidad (para una fecha específica o todos).
/app/backend/server.py:9276:                DELETE FROM Auditoria_Inventario_Provisional 
/app/backend/server.py:9281:                DELETE FROM Auditoria_Inventario_Provisional 
/app/backend/server.py:9311:    print("Almacenes:", getattr(request, 'almacenes', None))
/app/backend/server.py:9342:    # Filtro de almacenes
/app/backend/server.py:9343:    almacenes_limpios = []
/app/backend/server.py:9344:    if request.almacenes:
/app/backend/server.py:9345:        almacenes_limpios = [
/app/backend/server.py:9347:            for a in request.almacenes
/app/backend/server.py:9351:    filtro_almacenes_movtos = ""
/app/backend/server.py:9352:    filtro_almacenes_movsinv = ""
/app/backend/server.py:9354:    if almacenes_limpios:
/app/backend/server.py:9355:        almacenes_sql = ", ".join([f"'{a}'" for a in almacenes_limpios])
/app/backend/server.py:9356:        filtro_almacenes_movtos = f" AND RTRIM(LTRIM(M.idalmacen)) IN ({almacenes_sql}) "
/app/backend/server.py:9357:        filtro_almacenes_movsinv = f" AND RTRIM(LTRIM(M.idalmacen)) IN ({almacenes_sql}) "
/app/backend/server.py:9359:    logging.info(f"[DETALLE_MOV] Buscando movimientos para código: '{codigo_limpio}' (sin prefijo: '{codigo_sin_prefijo}'), fechas: {fecha_ini} a {fecha_fin}, almacenes: {almacenes_limpios}")
/app/backend/server.py:9364:                # Obtener movimientos de presentaciones (movtosalmacen)
/app/backend/server.py:9372:    A.nombre as almacen,
/app/backend/server.py:9375:FROM movtosalmacen M
/app/backend/server.py:9377:LEFT JOIN almacen A ON A.idalmacen = M.idalmacen
/app/backend/server.py:9382:    {filtro_almacenes_movtos}
/app/backend/server.py:9403:                        "almacen": m.get('almacen', ''),
/app/backend/server.py:9413:                # También buscar en movsinv (para insumos)
/app/backend/server.py:9420:    A.nombre as almacen,
/app/backend/server.py:9423:FROM movsinv M
/app/backend/server.py:9425:LEFT JOIN almacen A ON A.idalmacen = M.idalmacen
/app/backend/server.py:9430:    {filtro_almacenes_movsinv}
/app/backend/server.py:9451:                        "almacen": m.get('almacen', ''),
/app/backend/server.py:9510:    almacenes: Optional[List[str]] = None
/app/backend/server.py:9544:            # recetasalmacenes tiene la receta (qué insumos usa cada producto)
/app/backend/server.py:9554:    A.nombre as almacen
/app/backend/server.py:9558:INNER JOIN recetasalmacenes R ON R.idproducto = CD.idproducto
/app/backend/server.py:9559:LEFT JOIN almacen A ON A.idalmacen = R.idalmacen
/app/backend/server.py:9582:                    "almacen": r.get('almacen', '')
/app/backend/server.py:9638:        return {"kpis": {"total_compras_mes": 0, "requisiciones_pendientes": 0, "proveedores_activos": 0, "alertas_activas": 0}, "alertas": [], "top_proveedores": []}
/app/backend/server.py:9743:                    "kpis": {"total_compras_mes": 0, "facturas_mes": 0, "requisiciones_pendientes": 0, "proveedores_activos": 0, "alertas_activas": 0},
/app/backend/server.py:9752:            # Requisiciones pendientes FILTRADO POR SUCURSAL EXACTA
/app/backend/server.py:9754:SELECT COUNT(*) as total FROM Requisicion_Compra RC
/app/backend/server.py:9806:                    "requisiciones_pendientes": req_pendientes,
/app/backend/server.py:9861:                    "kpis": {"total_compras_mes": 0, "facturas_mes": 0, "requisiciones_pendientes": 0, "proveedores_activos": 0, "alertas_activas": 0},
/app/backend/server.py:9920:                    "requisiciones_pendientes": 0,  # SoftRestaurant no tiene este concepto
/app/backend/server.py:11364:# Directorio para almacenar evidencias
/app/backend/server.py:11373:    almacen_id: str
/app/backend/server.py:11374:    almacen_nombre: str
/app/backend/server.py:11379:    inventario_inicial_id: str
/app/backend/server.py:11380:    inventario_inicial_fecha: str
/app/backend/server.py:11381:    inventario_final_id: str
/app/backend/server.py:11382:    inventario_final_fecha: str
/app/backend/server.py:11413:    almacen_nombre: str
/app/backend/server.py:11442:            "almacen_id": body.get("almacen_id"),
/app/backend/server.py:11443:            "almacen_nombre": body.get("almacen_nombre"),
/app/backend/server.py:11448:            "inventario_inicial_id": body.get("inventario_inicial_id"),
/app/backend/server.py:11449:            "inventario_inicial_fecha": body.get("inventario_inicial_fecha"),
/app/backend/server.py:11450:            "inventario_final_id": body.get("inventario_final_id"),
/app/backend/server.py:11451:            "inventario_final_fecha": body.get("inventario_final_fecha"),
/app/backend/server.py:11541:                "almacen_nombre": inf.get("almacen_nombre"),
/app/backend/server.py:11542:                "periodo": f"{inf.get('inventario_inicial_fecha', '')} - {inf.get('inventario_final_fecha', '')}",
/app/backend/server.py:11900:        elements.append(Paragraph("INFORME DE AUDITORÍA DE INVENTARIOS", styles['TitleCustom']))
/app/backend/server.py:11910:            ['Almacén:', informe.get('almacen_nombre', 'N/A')],
/app/backend/server.py:11937:            ['Inventario Inicial:', f"{informe.get('inventario_inicial_fecha', 'N/A')}"],
/app/backend/server.py:11938:            ['Inventario Final:', f"{informe.get('inventario_final_fecha', 'N/A')}"],
/app/backend/server.py:12047:        # === ERRORES DE CAPTURA DE INVENTARIO ===
/app/backend/server.py:12052:                f"ERRORES DE CAPTURA DE INVENTARIO ({len(errores_captura)} detectados)", 
/app/backend/server.py:13703:    'almacen', 'cheques', 'cheqdet', 'productos', 'categorias', 'turnos',
/app/backend/server.py:13704:    'meseros', 'cuentas', 'folios', 'formasdepago', 'movsinventario', 
/app/backend/server.py:13705:    'movsalmacen', 'gruposi', 'gruposiclasificacion', 'productosreceta',
/app/backend/server.py:13708:    'producto', 'almacen', 'sucursal', 'proveedor', 'movimiento', 
/app/backend/server.py:14421:        "datos_inventario": informe.datos_inventario,
/app/backend/server.py:14430:        "compromisos_almacen": informe.compromisos_almacen,
/app/backend/server.py:14479:    cursor = db.informes_auditoria.find(filtro, {"_id": 0, "datos_inventario": 0, "datos_comparativo": 0, "evidencias": 0}).sort("fecha_emision", -1)
/app/backend/server.py:14719:    elements.append(Paragraph("INFORME DE AUDITORÍA DE INVENTARIO", styles['TitleCustom']))
/app/backend/server.py:14755:    datos_inv = informe.get('datos_inventario', [])
/app/backend/server.py:14759:        # Crear tabla de inventario (simplificada)
/app/backend/server.py:14823:    if informe.get('compromisos_almacen') or informe.get('compromisos_personal') or informe.get('compromisos_gerencia'):
/app/backend/server.py:14825:        if informe.get('compromisos_almacen'):
/app/backend/server.py:14826:            elements.append(Paragraph(f"<b>Almacén:</b> {informe.get('compromisos_almacen')}", styles['SmallText']))
/app/backend/server.py:14892:    {"id": "almacenes", "nombre": "Almacenes", "modulo": "Inventarios", "tabla": "Almacenes", "niveles_aprobacion": 1},
/app/backend/server.py:14893:    {"id": "familias", "nombre": "Familias de Productos", "modulo": "Inventarios", "tabla": "Familias", "niveles_aprobacion": 1},
/app/backend/server.py:14894:    {"id": "categorias", "nombre": "Categorías de Productos", "modulo": "Inventarios", "tabla": "Categorias", "niveles_aprobacion": 1},
/app/backend/server.py:17668:TIPOS_ALCANCE_PERMITIDOS = ["GLOBAL", "EMPRESA", "UNIDAD", "SUCURSAL", "ALMACEN"]
/app/backend/server.py:17742:    tipo: str  # GLOBAL | EMPRESA | UNIDAD | SUCURSAL | ALMACEN
/app/backend/server.py:17746:    almacenes_ids: List[str] = []
/app/backend/server.py:17800:        "almacenes_ids": request.almacenes_ids,
/app/backend/utils/migration_helpers.py:18:    "mongo_db.inventarios": "Compras_Inventarios_Fisicos_Sync",
/app/backend/utils/migration_helpers.py:30:    "mongo_db.pedidos": "Venta_Pedidos",
/app/backend/utils/migration_helpers.py:104:    - mongo_db.inventarios → Compras_Inventarios_Fisicos_Sync
/app/backend/utils/migration_helpers.py:143:- Compras_Inventarios_Fisicos_Sync
/app/backend/utils/migration_helpers.py:144:- Venta_Cotizaciones, Venta_Pedidos, Venta_Remisiones
/app/backend/catalogo/catalogo_consultas.py:243:FROM comprasmovtos cm
/app/backend/catalogo/catalogo_consultas.py:255:    # INVENTARIOS - SoftRestaurant
/app/backend/catalogo/catalogo_consultas.py:257:    "SR_INVENTARIO_ACTUAL": {
/app/backend/catalogo/catalogo_consultas.py:258:        "nombre": "Inventario Actual",
/app/backend/catalogo/catalogo_consultas.py:261:        "categoria": "Inventarios",
/app/backend/catalogo/catalogo_consultas.py:262:        "parametros": ["almacen"],
/app/backend/catalogo/catalogo_consultas.py:272:LEFT JOIN existenciasalmacen e ON e.idinsumo = i.idinsumo
/app/backend/catalogo/catalogo_consultas.py:273:LEFT JOIN almacen a ON a.idalmacen = e.idalmacen
/app/backend/catalogo/catalogo_consultas.py:274:WHERE a.nombre LIKE '%{almacen}%'
/app/backend/catalogo/catalogo_consultas.py:332:LEFT JOIN Almacen A ON A.Al_Cve_Almacen = V.Al_Cve_Almacen
/app/backend/catalogo/catalogo_consultas.py:376:FROM REQUISICION_COMPRA RC
/app/backend/catalogo/catalogo_consultas.py:377:INNER JOIN REQUISICION_COMPRA_DETALLE RCD ON RCD.Rc_Folio = RC.Rc_Folio
/app/backend/catalogo/catalogo_consultas.py:394:FROM REQUISICION_COMPRA RC
/app/backend/catalogo/catalogo_consultas.py:395:INNER JOIN REQUISICION_COMPRA_DETALLE RCD ON RCD.Rc_Folio = RC.Rc_Folio
/app/backend/catalogo/consultas_mpro.py:57:    A.Al_Descripcion as Almacen,
/app/backend/catalogo/consultas_mpro.py:67:INNER JOIN Almacen A ON A.Al_Cve_Almacen = V.Al_Cve_Almacen
/app/backend/catalogo/consultas_mpro.py:128:        "nombre": "Movimientos de Inventario",
/app/backend/catalogo/consultas_mpro.py:129:        "descripcion": "Obtiene los movimientos de inventario (entradas y salidas)",
/app/backend/catalogo/consultas_mpro.py:130:        "parametros": ["@SUCURSAL", "@ALMACEN", "@FECHA_INI", "@FECHA_FIN", "@TIPOS_MOVIMIENTO"],
/app/backend/catalogo/consultas_mpro.py:138:INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = S.Sc_Cve_Sucursal
/app/backend/catalogo/consultas_mpro.py:142:    AND A.Al_Descripcion LIKE '%{almacen}%'
/app/backend/catalogo/consultas_mpro.py:159:    A.Al_Descripcion as Almacen,
/app/backend/catalogo/consultas_mpro.py:170:INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen
/app/backend/catalogo/consultas_mpro.py:180:    # ============= PEDIDOS =============
/app/backend/catalogo/consultas_mpro.py:181:    "pedidos": {
/app/backend/catalogo/consultas_mpro.py:182:        "nombre": "Pedidos",
/app/backend/catalogo/consultas_mpro.py:183:        "descripcion": "Obtiene los pedidos a proveedores",
/app/backend/catalogo/consultas_mpro.py:195:FROM Pedido PD
/app/backend/catalogo/consultas_mpro.py:198:LEFT JOIN Pedido_Detalle PDD ON PDD.Pd_Folio = PD.Pd_Folio
/app/backend/catalogo/consultas_mpro.py:384:    # ============= ALMACENES =============
/app/backend/catalogo/consultas_mpro.py:385:    "almacenes": {
/app/backend/catalogo/consultas_mpro.py:386:        "nombre": "Catálogo de Almacenes",
/app/backend/catalogo/consultas_mpro.py:387:        "descripcion": "Obtiene el catálogo de almacenes por sucursal",
/app/backend/catalogo/consultas_mpro.py:391:    A.Al_Cve_Almacen as Codigo,
/app/backend/catalogo/consultas_mpro.py:395:FROM Almacen A
/app/backend/catalogo/consultas_mpro.py:403:    # ============= INVENTARIO FÍSICO =============
/app/backend/catalogo/consultas_mpro.py:404:    "inventario_fisico": {
/app/backend/catalogo/consultas_mpro.py:405:        "nombre": "Inventario Físico",
/app/backend/catalogo/consultas_mpro.py:406:        "descripcion": "Obtiene el inventario físico por folio",
/app/backend/catalogo/consultas_mpro.py:412:    A.Al_Descripcion as Almacen,
/app/backend/catalogo/consultas_mpro.py:419:INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen
/app/backend/catalogo/consultas_mpro.py:468:            "Al_Cve_Almacen - Almacén",
/app/backend/catalogo/consultas_mpro.py:492:        "descripcion": "Movimientos de inventario",
/app/backend/catalogo/consultas_mpro.py:497:            "Al_Cve_Almacen - Almacén",
/app/backend/catalogo/consultas_mpro.py:507:        "descripcion": "Inventario físico",
/app/backend/catalogo/consultas_mpro.py:509:            "Fi_Folio - Folio de inventario",
/app/backend/catalogo/consultas_mpro.py:510:            "Fi_Fecha - Fecha del inventario",
/app/backend/catalogo/consultas_mpro.py:511:            "Al_Cve_Almacen - Almacén",
/app/backend/catalogo/consultas_softrestaurant.py:62:FROM comprasmovtos CM
/app/backend/catalogo/consultas_softrestaurant.py:74:        "nombre": "Movimientos de Inventario",
/app/backend/catalogo/consultas_softrestaurant.py:75:        "descripcion": "Obtiene los movimientos de inventario",
/app/backend/catalogo/consultas_softrestaurant.py:83:FROM movtos M
/app/backend/catalogo/consultas_softrestaurant.py:212:    "comprasmovtos": {
/app/backend/catalogo/consultas_softrestaurant.py:222:    "movtos": {
/app/backend/catalogo/consultas_softrestaurant.py:223:        "descripcion": "Movimientos de inventario",
/app/backend/api/catalogos_sistemas.py:420:    - COMPRAS, INVENTARIOS, CORTES_Z, REPORTES
/app/backend/api/sync_receiver.py:183:    """Recibe KPIs de un Sync Agent y los almacena usando UPSERT idempotente."""
/app/backend/api/dba_credential_p0d.py:15:    - La contraseña se cifra con SERVER_SECRET_KEY antes de almacenar
/app/backend/api/dba_credential_p0d.py:22:    La contraseña se cifra y se almacena para diagnóstico.
/app/backend/api/dba_credential_p0d.py:183:# Almacenamiento temporal en memoria - se pierde al reiniciar
/app/backend/core/server_registry.py:19:- Módulo Operaciones/Inventarios
/app/backend/core/server_registry.py:259:        'query_inventario': _parse_json_field(row.get('query_inventario')),
/app/backend/core/server_registry.py:891:        'query_inventario': record.get('query_inventario'),
/app/backend/core/server_registry.py:1249:        'query_inventario': 'query_inventario',
/app/backend/core/server_registry.py:1587:        'query_inventario': sql_record.get('query_inventario'),
/app/backend/core/connection_resolver.py:48:    INVENTORY = "inventory"                        # Inventarios
/app/backend/core/connection_resolver.py:173:            "tables": ["almacen", "inventario"],
/app/backend/core/connection_resolver.py:174:            "description": "Inventarios desde SQL"
/app/backend/core/connection_resolver.py:219:            "tables": ["Almacen_General"],
/app/backend/core/connection_resolver.py:220:            "description": "Inventarios desde MPRO SQL"
/app/backend/core/auditoria.py:260:        """Serializa un valor para almacenamiento"""
/app/backend/core/empresa_resolver.py:178:    # Caso especial: quitar espacios para comparación con AliasNormalizado almacenado
/app/backend/core/refresh_tokens.py:10:- Hash SHA256 para almacenamiento (nunca el token plano)
/app/backend/core/refresh_tokens.py:17:- Solo se almacena el hash SHA256
/app/backend/core/refresh_tokens.py:68:    Genera el hash SHA256 del refresh token para almacenamiento.
/app/backend/core/refresh_tokens.py:70:    NUNCA se almacena el token plano en la base de datos.
/app/backend/core/refresh_tokens.py:83:    Verifica que un token coincide con su hash almacenado.
/app/backend/core/refresh_tokens.py:87:        stored_hash: Hash almacenado en BD
/app/backend/core/security.py:118:        hashed: Hash almacenado en BD
/app/backend/core/scheduler/scheduler_manager.py:27:from .jobs.pedidos_detector_job import create_pedidos_detector_job
/app/backend/core/scheduler/scheduler_manager.py:28:from .jobs.inventarios_detector_job import create_inventarios_detector_job
/app/backend/core/scheduler/scheduler_manager.py:175:    async def _run_pedidos_detector_job(self):
/app/backend/core/scheduler/scheduler_manager.py:176:        """Wrapper async para ejecutar job de detección de pedidos."""
/app/backend/core/scheduler/scheduler_manager.py:177:        job_config = self.config.jobs.get("pedidos_detector")
/app/backend/core/scheduler/scheduler_manager.py:181:        job = create_pedidos_detector_job(self.db, job_config)
/app/backend/core/scheduler/scheduler_manager.py:184:    async def _run_inventarios_detector_job(self):
/app/backend/core/scheduler/scheduler_manager.py:185:        """Wrapper async para ejecutar job de detección de inventarios."""
/app/backend/core/scheduler/scheduler_manager.py:186:        job_config = self.config.jobs.get("inventarios_detector")
/app/backend/core/scheduler/scheduler_manager.py:190:        job = create_inventarios_detector_job(self.db, job_config)
/app/backend/core/scheduler/scheduler_manager.py:888:        # Job Detector de Pedidos (Automatización Operativa)
/app/backend/core/scheduler/scheduler_manager.py:889:        pedidos_config = self.config.jobs.get("pedidos_detector")
/app/backend/core/scheduler/scheduler_manager.py:890:        if pedidos_config and pedidos_config.enabled:
/app/backend/core/scheduler/scheduler_manager.py:891:            if pedidos_config.cron_expression:
/app/backend/core/scheduler/scheduler_manager.py:892:                trigger = CronTrigger.from_crontab(pedidos_config.cron_expression)
/app/backend/core/scheduler/scheduler_manager.py:894:                trigger = IntervalTrigger(seconds=pedidos_config.interval_seconds)
/app/backend/core/scheduler/scheduler_manager.py:897:                self._run_pedidos_detector_job,
/app/backend/core/scheduler/scheduler_manager.py:899:                id="pedidos_detector",
/app/backend/core/scheduler/scheduler_manager.py:900:                name="Pedidos Detector",
/app/backend/core/scheduler/scheduler_manager.py:905:            self._jobs["pedidos_detector"] = pedidos_config
/app/backend/core/scheduler/scheduler_manager.py:906:            logger.info(f"Job Pedidos Detector registrado: intervalo={pedidos_config.interval_seconds}s")
/app/backend/core/scheduler/scheduler_manager.py:908:        # Job Detector de Inventarios (Automatización de Análisis)
/app/backend/core/scheduler/scheduler_manager.py:909:        inventarios_config = self.config.jobs.get("inventarios_detector")
/app/backend/core/scheduler/scheduler_manager.py:910:        if inventarios_config and inventarios_config.enabled:
/app/backend/core/scheduler/scheduler_manager.py:911:            if inventarios_config.cron_expression:
/app/backend/core/scheduler/scheduler_manager.py:912:                trigger = CronTrigger.from_crontab(inventarios_config.cron_expression)
/app/backend/core/scheduler/scheduler_manager.py:914:                trigger = IntervalTrigger(seconds=inventarios_config.interval_seconds)
/app/backend/core/scheduler/scheduler_manager.py:917:                self._run_inventarios_detector_job,
/app/backend/core/scheduler/scheduler_manager.py:919:                id="inventarios_detector",
/app/backend/core/scheduler/scheduler_manager.py:920:                name="Inventarios Detector",
/app/backend/core/scheduler/scheduler_manager.py:925:            self._jobs["inventarios_detector"] = inventarios_config
/app/backend/core/scheduler/scheduler_manager.py:926:            logger.info(f"Job Inventarios Detector registrado: intervalo={inventarios_config.interval_seconds}s")
/app/backend/core/scheduler/scheduler_manager.py:1295:        elif job_id == "pedidos_detector":
/app/backend/core/scheduler/scheduler_manager.py:1296:            await self._run_pedidos_detector_job()
/app/backend/core/scheduler/scheduler_manager.py:1298:        elif job_id == "inventarios_detector":
/app/backend/core/scheduler/scheduler_manager.py:1299:            await self._run_inventarios_detector_job()
/app/backend/core/scheduler/config.py:63:        # Pedidos Detector Job config (Automatización Operativa)
/app/backend/core/scheduler/config.py:64:        pedidos_interval = int(os.environ.get("SCHEDULER_PEDIDOS_INTERVAL_SECONDS", "300"))  # 5 minutos
/app/backend/core/scheduler/config.py:65:        pedidos_enabled = os.environ.get("SCHEDULER_PEDIDOS_ENABLED", "true").lower() == "true"
/app/backend/core/scheduler/config.py:67:        # Inventarios Detector Job config (Detección automática de inventarios)
/app/backend/core/scheduler/config.py:68:        inventarios_interval = int(os.environ.get("SCHEDULER_INVENTARIOS_INTERVAL_SECONDS", "600"))  # 10 minutos
/app/backend/core/scheduler/config.py:69:        inventarios_enabled = os.environ.get("SCHEDULER_INVENTARIOS_ENABLED", "true").lower() == "true"
/app/backend/core/scheduler/config.py:143:            "pedidos_detector": JobConfig(
/app/backend/core/scheduler/config.py:144:                job_id="pedidos_detector",
/app/backend/core/scheduler/config.py:145:                job_name="Pedidos Detector",
/app/backend/core/scheduler/config.py:146:                description="Detecta pedidos nuevos en MPro/Soft y dispara automatización operativa de compras",
/app/backend/core/scheduler/config.py:147:                enabled=pedidos_enabled,
/app/backend/core/scheduler/config.py:148:                interval_seconds=pedidos_interval,
/app/backend/core/scheduler/config.py:152:            "inventarios_detector": JobConfig(
/app/backend/core/scheduler/config.py:153:                job_id="inventarios_detector",
/app/backend/core/scheduler/config.py:154:                job_name="Inventarios Detector",
/app/backend/core/scheduler/config.py:155:                description="Detecta nuevos inventarios físicos en sistemas origen y dispara análisis automático",
/app/backend/core/scheduler/config.py:156:                enabled=inventarios_enabled,
/app/backend/core/scheduler/config.py:157:                interval_seconds=inventarios_interval,
/app/backend/core/scheduler/sql_repository.py:7:- Scheduler_InventariosProcesados
/app/backend/core/scheduler/sql_repository.py:8:- Scheduler_PedidosProcesados
/app/backend/core/scheduler/sql_repository.py:163:# INVENTARIOS PROCESADOS
/app/backend/core/scheduler/sql_repository.py:166:async def inventario_existe(
/app/backend/core/scheduler/sql_repository.py:170:    almacen_id: str,
/app/backend/core/scheduler/sql_repository.py:171:    folio_inventario: str
/app/backend/core/scheduler/sql_repository.py:173:    """Verifica si un inventario ya fue procesado."""
/app/backend/core/scheduler/sql_repository.py:176:        FROM Scheduler_InventariosProcesados
/app/backend/core/scheduler/sql_repository.py:180:          AND AlmacenID = %s
/app/backend/core/scheduler/sql_repository.py:181:          AND FolioInventario = %s
/app/backend/core/scheduler/sql_repository.py:183:    params = (sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
/app/backend/core/scheduler/sql_repository.py:189:async def registrar_inventario_procesando(
/app/backend/core/scheduler/sql_repository.py:193:    almacen_id: str,
/app/backend/core/scheduler/sql_repository.py:194:    folio_inventario: str,
/app/backend/core/scheduler/sql_repository.py:197:    """Registra un inventario como EN_PROCESO."""
/app/backend/core/scheduler/sql_repository.py:199:        INSERT INTO Scheduler_InventariosProcesados (
/app/backend/core/scheduler/sql_repository.py:200:            SistemaOrigen, ServerID, SucursalID, AlmacenID, FolioInventario,
/app/backend/core/scheduler/sql_repository.py:207:        sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario,
/app/backend/core/scheduler/sql_repository.py:215:        logger.error(f"[SCHEDULER_SQL] Error registrando inventario: {e}")
/app/backend/core/scheduler/sql_repository.py:219:async def actualizar_inventario_completado(
/app/backend/core/scheduler/sql_repository.py:223:    almacen_id: str,
/app/backend/core/scheduler/sql_repository.py:224:    folio_inventario: str,
/app/backend/core/scheduler/sql_repository.py:227:    """Marca un inventario como COMPLETADO."""
/app/backend/core/scheduler/sql_repository.py:229:        UPDATE Scheduler_InventariosProcesados
/app/backend/core/scheduler/sql_repository.py:236:          AND AlmacenID = %s
/app/backend/core/scheduler/sql_repository.py:237:          AND FolioInventario = %s
/app/backend/core/scheduler/sql_repository.py:239:    params = (workflow_id, sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
/app/backend/core/scheduler/sql_repository.py:245:        logger.error(f"[SCHEDULER_SQL] Error actualizando inventario: {e}")
/app/backend/core/scheduler/sql_repository.py:249:async def actualizar_inventario_error(
/app/backend/core/scheduler/sql_repository.py:253:    almacen_id: str,
/app/backend/core/scheduler/sql_repository.py:254:    folio_inventario: str,
/app/backend/core/scheduler/sql_repository.py:257:    """Marca un inventario como ERROR."""
/app/backend/core/scheduler/sql_repository.py:259:        UPDATE Scheduler_InventariosProcesados
/app/backend/core/scheduler/sql_repository.py:267:          AND AlmacenID = %s
/app/backend/core/scheduler/sql_repository.py:268:          AND FolioInventario = %s
/app/backend/core/scheduler/sql_repository.py:270:    params = (error_mensaje, sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
/app/backend/core/scheduler/sql_repository.py:276:        logger.error(f"[SCHEDULER_SQL] Error actualizando inventario: {e}")
/app/backend/core/scheduler/sql_repository.py:280:async def get_inventarios_pendientes_reintento(max_intentos: int = 3, limit: int = 5) -> List[Dict]:
/app/backend/core/scheduler/sql_repository.py:281:    """Obtiene inventarios en ERROR que pueden reintentarse."""
/app/backend/core/scheduler/sql_repository.py:284:            SistemaOrigen, ServerID, SucursalID, AlmacenID, FolioInventario,
/app/backend/core/scheduler/sql_repository.py:286:        FROM Scheduler_InventariosProcesados
/app/backend/core/scheduler/sql_repository.py:297:# PEDIDOS PROCESADOS
/app/backend/core/scheduler/sql_repository.py:300:async def pedido_existe(
/app/backend/core/scheduler/sql_repository.py:304:    folio_pedido: str
/app/backend/core/scheduler/sql_repository.py:306:    """Verifica si un pedido ya fue detectado."""
/app/backend/core/scheduler/sql_repository.py:309:        FROM Scheduler_PedidosProcesados
/app/backend/core/scheduler/sql_repository.py:313:          AND FolioPedido = %s
/app/backend/core/scheduler/sql_repository.py:315:    params = (sistema_origen, server_id, empresa_id, folio_pedido)
/app/backend/core/scheduler/sql_repository.py:321:async def registrar_pedido_detectado(
/app/backend/core/scheduler/sql_repository.py:325:    folio_pedido: str,
/app/backend/core/scheduler/sql_repository.py:330:    """Registra un pedido detectado."""
/app/backend/core/scheduler/sql_repository.py:332:        INSERT INTO Scheduler_PedidosProcesados (
/app/backend/core/scheduler/sql_repository.py:333:            SistemaOrigen, ServerID, EmpresaID, SucursalID, FolioPedido,
/app/backend/core/scheduler/sql_repository.py:340:        sistema_origen, server_id, empresa_id, sucursal_id, folio_pedido,
/app/backend/core/scheduler/sql_repository.py:348:        logger.error(f"[SCHEDULER_SQL] Error registrando pedido: {e}")
/app/backend/core/scheduler/sql_repository.py:457:    'inventario_existe',
/app/backend/core/scheduler/sql_repository.py:458:    'registrar_inventario_procesando',
/app/backend/core/scheduler/sql_repository.py:459:    'actualizar_inventario_completado',
/app/backend/core/scheduler/sql_repository.py:460:    'actualizar_inventario_error',
/app/backend/core/scheduler/sql_repository.py:461:    'get_inventarios_pendientes_reintento',
/app/backend/core/scheduler/sql_repository.py:462:    'pedido_existe',
/app/backend/core/scheduler/sql_repository.py:463:    'registrar_pedido_detectado',
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:2:EDARSA HUB - Job de Detección de Pedidos para Automatización Operativa
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:6:Job del scheduler para detectar pedidos nuevos en MPro/Soft y disparar
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:12:3. Consultar pedidos vigentes de cada servidor
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:13:4. Comparar contra pedidos ya procesados (anti-duplicado)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:14:5. Para pedidos nuevos:
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:16:   - FASE 4.2: Validar inventario
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:17:     - Si falta inventario → Crear tarea operativa (PENDIENTE_INVENTARIO)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:18:     - Si hay inventario → Ejecutar auditoría (EN_AUDITORIA)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:24:- Anti-duplicados por (empresa_id, pedido_folio, origen)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:50:class PedidosDetectorJob:
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:52:    Job para detectar pedidos nuevos y disparar automatización.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:55:    FASE 4.2: Validación de inventario + tareas operativas
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:58:    - Tabla `Scheduler_PedidosProcesados` en EDARSAHUB SQL
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:59:    - Índice único por (EmpresaID, FolioPedido, SistemaOrigen)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:64:    - SUCCESS_WITH_DATA: Consulta exitosa con pedidos encontrados
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:65:    - SUCCESS_EMPTY: Consulta exitosa, cero pedidos (resultado real)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:72:    # COLLECTION_PROCESADOS = "pedidos_procesados_automatizacion"  # -> Scheduler_PedidosProcesados
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:82:            logger.info("[PEDIDOS_DETECTOR] Usando StubDatabase para job_logger (tracking en SQL)")
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:97:        Ejecuta detección de pedidos nuevos.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:100:        FASE 4.2: Valida inventario y crea tareas si falta
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:115:        logger.info(f"[PEDIDOS_DETECTOR] Iniciando ejecución SQL Server - {started_at.isoformat()}")
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:119:            job_name="pedidos_detector",
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:127:            job_name="pedidos_detector",
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:143:            "pedidos_detectados": 0,         # Solo de consultas SUCCESS
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:144:            "pedidos_nuevos": 0,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:165:            logger.info(f"[PEDIDOS_DETECTOR] Empresas activas: {len(empresas)}")
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:190:                        logger.debug(f"[PEDIDOS_DETECTOR] {empresa_nombre}: Sin servidores asociados")
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:193:                    logger.info(f"[PEDIDOS_DETECTOR] {empresa_nombre}: {len(servidores)} servidores")
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:203:                        query_result = await self._consultar_pedidos_con_estado(server)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:228:                                    f"[PEDIDOS_DETECTOR] {server_name}: EN COOLDOWN - "
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:234:                                    f"[PEDIDOS_DETECTOR] {server_name}: NO ACCESIBLE - "
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:240:                                    f"[PEDIDOS_DETECTOR] {server_name}: ERROR - "
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:261:                        pedidos = query_result.data
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:263:                        if not pedidos:
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:266:                                f"[PEDIDOS_DETECTOR] {server_name}: "
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:267:                                f"Consulta exitosa - 0 pedidos vigentes (resultado real)"
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:271:                        # SUCCESS_WITH_DATA: Hay pedidos para procesar
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:273:                            f"[PEDIDOS_DETECTOR] {empresa_nombre}/{server_name}: "
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:274:                            f"{len(pedidos)} pedidos vigentes detectados"
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:277:                        for pedido in pedidos:
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:278:                            stats["pedidos_detectados"] += 1
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:279:                            folio = str(pedido.get("folio", pedido.get("Folio", "")))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:280:                            origen = pedido.get("origen", server.get("system_type", "MPRO"))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:291:                            # FASE 4.2: VALIDAR INVENTARIO
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:294:                                resultado = await self._procesar_pedido_nuevo(
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:297:                                    pedido=pedido
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:301:                                    stats["pedidos_nuevos"] += 1
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:306:                                            f"[PEDIDOS_DETECTOR] {folio}: "
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:307:                                            f"PENDIENTE_INVENTARIO - Tarea creada"
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:312:                                            f"[PEDIDOS_DETECTOR] {folio}: "
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:321:                                    f"[PEDIDOS_DETECTOR] Error procesando {folio}: {e}"
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:323:                                await self._registrar_bitacora_job("ERROR_PEDIDO", {
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:331:                        f"[PEDIDOS_DETECTOR] Error empresa {empresa_nombre}: {e}"
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:354:            elif stats["pedidos_nuevos"] > 0:
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:370:                processed_count=stats["pedidos_detectados"],
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:371:                success_count=stats["pedidos_nuevos"],
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:384:            logger.info(f"[PEDIDOS_DETECTOR] {message}")
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:394:                processed_count=stats["pedidos_detectados"],
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:395:                success_count=stats["pedidos_nuevos"],
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:406:            logger.error(f"[PEDIDOS_DETECTOR] Error general: {e}")
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:428:                f" | Pedidos detectados: {stats['pedidos_detectados']}, "
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:429:                f"Nuevos: {stats['pedidos_nuevos']}, "
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:474:    # CONSULTA DE PEDIDOS CON ENVELOPE DE RESULTADO
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:477:    async def _consultar_pedidos_con_estado(self, server: Dict) -> SourceQueryResult:
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:479:        Consulta pedidos vigentes de un servidor con envelope de resultado.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:491:            from modules.compras.service import obtener_pedidos_vigentes
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:494:            pedidos = await obtener_pedidos_vigentes(server_id)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:498:            if pedidos and len(pedidos) > 0:
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:500:                    data=pedidos,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:563:    async def _consultar_pedidos_vigentes(self, server: Dict) -> List[Dict]:
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:565:        DEPRECATED: Usar _consultar_pedidos_con_estado en su lugar.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:569:        result = await self._consultar_pedidos_con_estado(server)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:580:        Verifica si el pedido ya fue procesado para esta empresa.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:585:        from modules.compras.repository_pedidos_sql import pedido_ya_procesado_sql
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:586:        return await pedido_ya_procesado_sql(empresa_id, folio, origen)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:599:        Marca pedido como procesado.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:604:        from modules.compras.repository_pedidos_sql import marcar_pedido_procesado_sql
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:606:        await marcar_pedido_procesado_sql(
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:617:    # FASE 4.1 y 4.2: PROCESAMIENTO DE PEDIDO NUEVO
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:620:    async def _procesar_pedido_nuevo(
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:624:        pedido: Dict
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:627:        Procesa un pedido nuevo detectado.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:630:        FASE 4.2: Valida inventario y decide siguiente paso
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:639:        folio = str(pedido.get("folio", pedido.get("Folio", "")))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:640:        sucursal_id = str(pedido.get("sucursal_id", pedido.get("Sucursal_Id", "")))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:641:        sucursal_nombre = pedido.get("sucursal", pedido.get("Sucursal", ""))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:642:        almacen_id = str(pedido.get("almacen_id", pedido.get("Almacen_Id", "")))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:643:        almacen_nombre = pedido.get("almacen", pedido.get("Almacen", ""))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:644:        origen = pedido.get("origen", server.get("system_type", "MPRO"))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:649:        productos = await self._obtener_detalle_pedido(server, folio)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:658:            await self._registrar_bitacora_job("PEDIDO_SIN_PRODUCTOS", {
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:667:        # FASE 4.2: VALIDAR INVENTARIO
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:669:        tiene_inventario = await self._validar_inventario_disponible(
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:670:            server_id, almacen_id, productos
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:673:        if not tiene_inventario:
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:675:            # FALTA INVENTARIO → CREAR TAREA OPERATIVA
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:684:                almacen_id=almacen_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:685:                almacen_nombre=almacen_nombre,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:692:                automatizacion_id, "PENDIENTE_INVENTARIO",
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:703:                "motivo": "Falta inventario físico"
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:707:                "estado": "PENDIENTE_INVENTARIO",
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:714:        # HAY INVENTARIO → INICIAR AUDITORÍA
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:719:            pedido=pedido,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:747:    # OBTENCIÓN DE DETALLE DE PEDIDO
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:750:    async def _obtener_detalle_pedido(self, server: Dict, folio: str) -> List[Dict]:
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:751:        """Obtiene detalle de productos del pedido."""
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:754:                from modules.compras.repository import query_detalle_pedido_mpro
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:755:                detalle = query_detalle_pedido_mpro(server, folio)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:768:            logger.warning(f"[PEDIDOS_DETECTOR] Error detalle pedido {folio}: {e}")
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:772:    # FASE 4.2: VALIDACIÓN DE INVENTARIO
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:775:    async def _validar_inventario_disponible(
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:778:        almacen_id: str,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:782:        Valida si existe inventario físico reciente para el almacén.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:786:        NOTA: Esta función verificaba inventarios en MongoDB.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:788:        La validación de inventarios se hará posteriormente.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:791:            True si hay inventario disponible, False si falta
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:794:        # TODO: Implementar validación contra tabla SQL de inventarios
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:795:        logger.debug("[PEDIDOS_DETECTOR] _inventario_valido: Retornando True (MongoDB eliminado)")
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:810:        almacen_id: str,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:811:        almacen_nombre: str,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:816:        Crea una tarea operativa cuando falta inventario.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:818:        FASE 4.2: Estado PENDIENTE_INVENTARIO hasta que se capture inventario.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:824:        from modules.compras.repository_pedidos_sql import crear_tarea_operativa_sql
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:833:            almacen_id=almacen_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:834:            almacen_nombre=almacen_nombre,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:842:            'titulo': f"Capturar inventario físico - {almacen_nombre}",
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:853:                f"[PEDIDOS_DETECTOR] Tarea creada: {tarea['id']} - "
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:867:        pedido: Dict,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:872:        Inicia auditoría cuando hay inventario disponible.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:884:        folio = str(pedido.get("folio", pedido.get("Folio", "")))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:885:        sucursal_id = str(pedido.get("sucursal_id", pedido.get("Sucursal_Id", "")))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:886:        sucursal_nombre = pedido.get("sucursal", pedido.get("Sucursal", ""))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:887:        almacen_id = str(pedido.get("almacen_id", pedido.get("Almacen_Id", "")))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:888:        almacen_nombre = pedido.get("almacen", pedido.get("Almacen", ""))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:889:        origen = pedido.get("origen", server.get("system_type", "MPRO"))
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:892:        resultado = service.procesar_pedido_operativo(
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:893:            pedido_id=folio,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:897:            almacen_id=almacen_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:898:            almacen_nombre=almacen_nombre,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:921:        from modules.compras.repository_pedidos_sql import registrar_bitacora_pedidos_sql
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:922:        await registrar_bitacora_pedidos_sql("pedidos_detector", evento, datos)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:925:def create_pedidos_detector_job(db, config: Optional[dict] = None) -> PedidosDetectorJob:
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:926:    """Factory para crear el job de detección de pedidos."""
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:927:    return PedidosDetectorJob(db, config)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:939:    Ejecuta el detector de pedidos manualmente.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:950:    job = create_pedidos_detector_job(db)
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:16:- Almacena datos en EDARSAHUB SQL
/app/backend/core/scheduler/jobs/__init__.py:7:from .pedidos_detector_job import PedidosDetectorJob
/app/backend/core/scheduler/jobs/__init__.py:8:from .inventarios_detector_job import InventariosDetectorJob, create_inventarios_detector_job
/app/backend/core/scheduler/jobs/__init__.py:14:    'PedidosDetectorJob',
/app/backend/core/scheduler/jobs/__init__.py:15:    'InventariosDetectorJob',
/app/backend/core/scheduler/jobs/__init__.py:16:    'create_inventarios_detector_job',
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:3:from modules.comercial.rentabilidad import evaluar_margen_pedido
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:9:    Escanea pedidos CRM pendientes de validación fiscal y audita sus márgenes
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:12:    # 1. Consultar pedidos pendientes que no han sido validados o remisionados
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:13:    query_pedidos_pendientes = """
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:14:        SELECT PedidoID, FolioPedido, UsuarioCreadorID
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:15:        FROM dbo.Venta_Pedidos
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:18:    pedidos = execute_hub_query(query_pedidos_pendientes, ())
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:20:    if not pedidos:
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:21:        return {"status": "SUCCESS", "mensaje": "No se encontraron pedidos pendientes para auditar."}
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:23:    pedidos_auditados = 0
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:26:    # 2. Iterar y procesar cada pedido a través del motor blindado de rentabilidad
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:27:    for ped in pedidos:
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:28:        pedido_id = ped["PedidoID"]
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:29:        folio = ped["FolioPedido"]
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:33:            analisis = evaluar_margen_pedido(pedido_id=pedido_id, umbral_minimo_margen=15.0)
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:34:            pedidos_auditados += 1
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:43:                    "pedido_id": pedido_id,
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:58:                # Registrar el estatus de alerta en el historial del pedido para auditoría interna
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:69:            # Log de contingencia si un pedido específico falla en el parseo
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:74:        "pedidos_procesados": pedidos_auditados,
/app/backend/core/scheduler/jobs/vtiger_sync_job.py:5:Almacena datos en tablas Sync_Vtiger_* de EDARSAHUB SQL Server.
/app/backend/core/scheduler/jobs/sync_compras_job.py:2:EDARSA HUB - Job de Sincronización de Compras (Inventarios y Requisiciones)
/app/backend/core/scheduler/jobs/sync_compras_job.py:6:Sincroniza datos de inventarios físicos y requisiciones desde los servidores
/app/backend/core/scheduler/jobs/sync_compras_job.py:15:- Compras_Inventarios_Fisicos_Sync
/app/backend/core/scheduler/jobs/sync_compras_job.py:16:- Compras_Requisiciones_Sync
/app/backend/core/scheduler/jobs/sync_compras_job.py:37:    sync_inventarios_fisicos_from_server,
/app/backend/core/scheduler/jobs/sync_compras_job.py:38:    sync_requisiciones_from_server,
/app/backend/core/scheduler/jobs/sync_compras_job.py:289:        "inventarios": [],
/app/backend/core/scheduler/jobs/sync_compras_job.py:290:        "requisiciones": []
/app/backend/core/scheduler/jobs/sync_compras_job.py:335:            # Sincronizar Inventarios Físicos
/app/backend/core/scheduler/jobs/sync_compras_job.py:340:                    inv_result = sync_inventarios_fisicos_from_server(
/app/backend/core/scheduler/jobs/sync_compras_job.py:348:                results["inventarios"].append({
/app/backend/core/scheduler/jobs/sync_compras_job.py:358:                    logger.info(f"[SYNC-COMPRAS] ✅ Inventarios {server_name}: {inv_result.get('records_synced', 0)} registros")
/app/backend/core/scheduler/jobs/sync_compras_job.py:362:                    logger.warning(f"[SYNC-COMPRAS] ❌ Inventarios {server_name}: {inv_result.get('error')}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:369:                        sync_type="INVENTARIOS",
/app/backend/core/scheduler/jobs/sync_compras_job.py:378:                logger.error(f"[SYNC-COMPRAS] Error sincronizando inventarios {server_name}: {e}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:382:            # Sincronizar Requisiciones
/app/backend/core/scheduler/jobs/sync_compras_job.py:387:                    req_result = sync_requisiciones_from_server(
/app/backend/core/scheduler/jobs/sync_compras_job.py:395:                results["requisiciones"].append({
/app/backend/core/scheduler/jobs/sync_compras_job.py:405:                    logger.info(f"[SYNC-COMPRAS] ✅ Requisiciones {server_name}: {req_result.get('records_synced', 0)} registros")
/app/backend/core/scheduler/jobs/sync_compras_job.py:409:                    logger.warning(f"[SYNC-COMPRAS] ❌ Requisiciones {server_name}: {req_result.get('error')}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:416:                        sync_type="REQUISICIONES",
/app/backend/core/scheduler/jobs/sync_compras_job.py:425:                logger.error(f"[SYNC-COMPRAS] Error sincronizando requisiciones {server_name}: {e}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:492:        "job_name": "Sincronización Compras (Inventarios/Requisiciones)",
/app/backend/core/scheduler/jobs/sync_compras_job.py:496:        "description": "Sincroniza inventarios físicos y requisiciones desde servidores origen hacia EDARSAHUB SQL",
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:6:Detecta nuevos inventarios y requisiciones en tiempo casi-real usando
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:267:    results = {"inventarios": [], "requisiciones": []}
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:299:            # Detectar nuevos inventarios
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:301:                inv_result = detector.detectar_nuevos_inventarios(
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:307:            results["inventarios"].append({
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:316:            # Detectar nuevas requisiciones
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:318:                req_result = detector.detectar_nuevas_requisiciones(
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:324:            results["requisiciones"].append({
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:382:        "job_name": "Detección de Nuevos Inventarios/Requisiciones",
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:2:EDARSA HUB - Job de Detección Automática de Inventarios
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:4:Detecta nuevos inventarios físicos en sistemas origen (SoftRestaurant/MPRO),
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:9:2. Para cada servidor, consultar inventarios recientes
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:10:3. Comparar contra inventarios_procesados_auto (anti-duplicado)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:11:4. Para inventarios nuevos:
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:12:   a) Registrar en inventarios_procesados_auto (EN_PROCESO)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:13:   b) Ejecutar análisis de inventario
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:22:- almacen_id
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:23:- folio_inventario
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:54:    inventario_existe,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:55:    registrar_inventario_procesando,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:56:    actualizar_inventario_completado,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:57:    actualizar_inventario_error,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:58:    get_inventarios_pendientes_reintento,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:69:COLLECTION_PROCESADOS = "inventarios_procesados_auto"
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:80:# Tablas requeridas por sistema para detección de inventarios
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:82:    "SoftRestaurant": ["invfisico", "almacen"],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:83:    "MPRO": []  # MPRO no tiene estructura de inventarios compatible
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:142:        logger.debug(f"[INVENTARIOS_DETECTOR] Tabla '{tabla}' en {servidor['name']}: {'EXISTE' if existe else 'NO EXISTE'}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:146:        logger.warning(f"[INVENTARIOS_DETECTOR] Error verificando tabla '{tabla}' en {servidor['name']}: {e}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:165:            logger.warning(f"[INVENTARIOS_DETECTOR] Pool [jobs] invalidado para {servidor['name']} por error de estructura SQL")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:167:            logger.error(f"[INVENTARIOS_DETECTOR] Error invalidando pool [jobs]: {cleanup_error}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:180:    almacen_id: str
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:181:    folio_inventario: str
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:192:            "clave.almacen_id": self.almacen_id,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:193:            "clave.folio_inventario": self.folio_inventario
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:198:class InventarioDetectado:
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:199:    """Estructura para inventario detectado."""
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:202:    almacen_nombre: str
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:203:    fecha_inventario: str
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:213:class InventariosDetectorJob:
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:215:    Job para detectar inventarios nuevos y disparar análisis automático.
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:218:    - Colección `inventarios_procesados_auto` en MongoDB
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:227:            logger.info("[INVENTARIOS_DETECTOR] Usando StubDatabase")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:236:            "inventarios_detectados": 0,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:237:            "inventarios_nuevos": 0,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:238:            "inventarios_procesados": 0,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:239:            "inventarios_error": 0,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:240:            "inventarios_duplicados": 0,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:241:            "inventarios_reintentados": 0,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:247:            self.max_inventarios_por_ejecucion = getattr(config, 'batch_size', 20)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:249:            self.max_inventarios_por_ejecucion = 20
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:259:        Ejecuta detección de inventarios nuevos.
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:262:        Ya no depende de MongoDB para tracking de inventarios.
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:272:        logger.info(f"[INVENTARIOS_DETECTOR] Iniciando ejecución SQL Server - {started_at.isoformat()}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:276:            job_name="inventarios_detector",
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:284:            job_name="inventarios_detector",
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:297:            logger.info(f"[INVENTARIOS_DETECTOR] Servidores a escanear: {len(servidores)}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:303:                logger.warning(f"[INVENTARIOS_DETECTOR] Error procesando reintentos: {e}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:310:                    logger.error(f"[INVENTARIOS_DETECTOR] Error en servidor {servidor.get('name')}: {e}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:317:            if self.stats["inventarios_procesados"] > 0:
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:319:            elif self.stats["inventarios_detectados"] > 0:
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:328:                processed_count=self.stats["inventarios_procesados"],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:329:                success_count=self.stats["inventarios_procesados"],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:330:                failed_count=self.stats["inventarios_error"],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:331:                skipped_count=self.stats["inventarios_duplicados"],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:336:            logger.info(f"[INVENTARIOS_DETECTOR] Finalizado ({final_status}) - {self._generar_resumen()}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:344:            logger.error(f"[INVENTARIOS_DETECTOR] ERROR CRÍTICO: {e}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:351:                processed_count=self.stats["inventarios_procesados"],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:352:                failed_count=self.stats["inventarios_error"],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:365:        # La tabla Scheduler_InventariosProcesados ya tiene el UNIQUE constraint
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:370:        logger.info("[INVENTARIOS_DETECTOR] _obtener_servidores: Usando SQL Server")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:373:        logger.info(f"[INVENTARIOS_DETECTOR] Obtenidos {len(servidores)} servidores de SQL")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:385:        """Procesa inventarios en ERROR que pueden reintentarse."""
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:389:        # Buscar inventarios en ERROR con intentos < MAX desde SQL
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:390:        pendientes = await get_inventarios_pendientes_reintento(
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:397:            total_procesados = self.stats["inventarios_procesados"] + self.stats["inventarios_error"]
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:398:            if total_procesados >= self.max_inventarios_por_ejecucion:
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:399:                logger.info("[INVENTARIOS_DETECTOR] Límite alcanzado, saltando reintentos")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:402:            self.stats["inventarios_reintentados"] += 1
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:403:            logger.info(f"[INVENTARIOS_DETECTOR] Reintentando folio={registro.get('FolioInventario')}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:411:                    'almacen_id': registro.get('AlmacenID'),
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:412:                    'folio_inventario': registro.get('FolioInventario')
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:417:            await self._procesar_inventario_desde_registro(registro_compat)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:420:        """Escanea un servidor en busca de inventarios nuevos."""
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:425:        logger.info(f"[INVENTARIOS_DETECTOR] Escaneando {server_name} ({system_type})")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:428:            # Detectar inventarios según tipo de sistema
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:430:                inventarios = await self._detectar_soft(servidor)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:432:                inventarios = await self._detectar_mpro(servidor)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:434:                logger.warning(f"[INVENTARIOS_DETECTOR] Tipo de sistema desconocido: {system_type}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:437:            self.stats["inventarios_detectados"] += len(inventarios)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:438:            logger.info(f"[INVENTARIOS_DETECTOR] {server_name}: {len(inventarios)} inventarios detectados")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:440:            # Procesar cada inventario detectado
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:441:            for inv in inventarios:
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:442:                await self._procesar_inventario(inv, servidor)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:445:            logger.warning(f"[INVENTARIOS_DETECTOR] {server_name}: Conexión fallida - {e}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:447:    async def _detectar_soft(self, servidor: Dict) -> List[InventarioDetectado]:
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:449:        Detecta inventarios en SoftRestaurant.
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:453:        - Valida existencia de tabla invfisico
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:459:        inventarios = []
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:465:            logger.warning(f"[INVENTARIOS_DETECTOR] {server_name}: _detectar_soft llamado con system_type={system_type} (esperado: SoftRestaurant)")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:466:            return inventarios
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:468:        # BLINDAJE 2: Validar existencia de tabla invfisico
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:469:        if not _validar_tabla_existe(servidor, 'invfisico'):
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:470:            logger.info(f"[INVENTARIOS_DETECTOR] {server_name}: Tabla 'invfisico' no existe - saltando detección")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:471:            return inventarios
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:474:            # Query para obtener inventarios válidos recientes
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:476:                WITH inventarios_validos AS (
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:480:                        i.idalmacen1 AS almacen_id,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:481:                        a.nombre AS almacen_nombre,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:483:                            PARTITION BY i.idalmacen1, CONVERT(date, i.fecha)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:486:                    FROM invfisico i
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:487:                    LEFT JOIN almacen a ON a.idalmacen = i.idalmacen1
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:491:                SELECT folio, fecha, almacen_id, almacen_nombre
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:492:                FROM inventarios_validos
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:508:                logger.debug(f"[INVENTARIOS_DETECTOR] {server_name}: Sin inventarios recientes")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:509:                return inventarios
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:514:                almacen_id = str(row['almacen_id']) if row['almacen_id'] else ''
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:515:                almacen_nombre = row.get('almacen_nombre', almacen_id)
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:527:                    servidor, almacen_id, fecha_str
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:534:                    almacen_id=almacen_id,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:535:                    folio_inventario=folio
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:538:                inventarios.append(InventarioDetectado(
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:541:                    almacen_nombre=almacen_nombre,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:542:                    fecha_inventario=fecha_str,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:555:            logger.error(f"[INVENTARIOS_DETECTOR] Error detectando SOFT en {server_name}: {e}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:557:        return inventarios
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:559:    async def _detectar_mpro(self, servidor: Dict) -> List[InventarioDetectado]:
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:560:        """Detecta inventarios en MPRO.
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:562:        NOTA BLINDAJE (Abril 2026): MPRO no tiene la tabla 'invfisico'.
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:565:        # BLINDAJE: MPRO usa una estructura diferente de inventarios
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:566:        # La tabla invfisico NO existe en MPRO - retornar vacío para evitar contaminar el pool SQL
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:567:        logger.info(f"[INVENTARIOS_DETECTOR] MPRO {servidor.get('name')}: Saltando detección (tabla invfisico no existe en MPRO)")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:573:        almacen_id: str, 
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:592:                FROM invfisico
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:594:                  AND idalmacen1 = '{almacen_id}'
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:621:            logger.warning(f"[INVENTARIOS_DETECTOR] Error calculando folio inicial en {server_name}: {e}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:628:        almacen_id: str,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:635:        BLINDAJE (Abril 2026): MPRO no tiene tabla invfisico.
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:638:        # BLINDAJE: MPRO no tiene estructura de inventarios compatible
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:640:        logger.debug("[INVENTARIOS_DETECTOR] _calcular_folio_inicial_mpro no implementado para MPRO (tabla invfisico no existe)")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:643:    async def _procesar_inventario(self, inv: InventarioDetectado, servidor: Dict):
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:644:        """Procesa un inventario detectado."""
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:648:        total_procesados = self.stats["inventarios_procesados"] + self.stats["inventarios_error"]
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:649:        if total_procesados >= self.max_inventarios_por_ejecucion:
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:650:            logger.info(f"[INVENTARIOS_DETECTOR] Límite de {self.max_inventarios_por_ejecucion} alcanzado, saltando folio={clave.folio_inventario}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:654:        existe = await inventario_existe(
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:658:            almacen_id=clave.almacen_id,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:659:            folio_inventario=clave.folio_inventario
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:663:            self.stats["inventarios_duplicados"] += 1
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:664:            logger.debug(f"[INVENTARIOS_DETECTOR] Duplicado: folio={clave.folio_inventario}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:667:        self.stats["inventarios_nuevos"] += 1
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:668:        logger.info(f"[INVENTARIOS_DETECTOR] Nuevo inventario: folio={clave.folio_inventario}, almacen={inv.almacen_nombre}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:678:            "almacen_nombre": inv.almacen_nombre,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:679:            "fecha_inventario": inv.fecha_inventario,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:696:            success = await registrar_inventario_procesando(
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:700:                almacen_id=clave.almacen_id,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:701:                folio_inventario=clave.folio_inventario,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:704:                    "almacen_nombre": inv.almacen_nombre,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:710:                self.stats["inventarios_duplicados"] += 1
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:711:                logger.info(f"[INVENTARIOS_DETECTOR] Ya en proceso: folio={clave.folio_inventario}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:716:                self.stats["inventarios_duplicados"] += 1
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:717:                logger.info(f"[INVENTARIOS_DETECTOR] Ya en proceso: folio={clave.folio_inventario}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:724:    async def _procesar_inventario_desde_registro(self, registro: Dict):
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:725:        """Procesa un inventario desde un registro existente (reintento)."""
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:733:        # Reconstruir InventarioDetectado
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:735:        inv = InventarioDetectado(
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:738:            almacen_nombre=registro.get("almacen_nombre", ""),
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:739:            fecha_inventario=registro.get("fecha_inventario"),
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:747:    async def _ejecutar_analisis(self, registro: Dict, servidor: Dict, inv: InventarioDetectado):
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:748:        """Ejecuta el análisis de inventario y orquestación."""
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:752:            logger.info(f"[INVENTARIOS_DETECTOR] Ejecutando análisis folio={clave.folio_inventario}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:765:                almacen=inv.almacen_nombre,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:766:                almacenes=[inv.almacen_nombre],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:768:                fecha_fin=inv.fecha_inventario,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:770:                folio_final=clave.folio_inventario,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:772:                folios_finales=[clave.folio_inventario]
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:786:            logger.info(f"[INVENTARIOS_DETECTOR] Análisis completado: {len(productos_con_diferencia)} diferencias")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:802:            await actualizar_inventario_completado(
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:806:                almacen_id=clave.almacen_id,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:807:                folio_inventario=clave.folio_inventario,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:811:            self.stats["inventarios_procesados"] += 1
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:812:            logger.info(f"[INVENTARIOS_DETECTOR] Procesado exitosamente: folio={clave.folio_inventario}, workflow={workflow_id}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:815:            logger.error(f"[INVENTARIOS_DETECTOR] ERROR en análisis folio={clave.folio_inventario}: {e}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:821:        inv: InventarioDetectado,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:837:                almacen_id=inv.clave.almacen_id,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:838:                almacen_nombre=inv.almacen_nombre,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:841:                folios_finales=[inv.clave.folio_inventario],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:842:                fecha_ini=inv.fecha_inicial or inv.fecha_inventario,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:843:                fecha_fin=inv.fecha_inventario,
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:846:                # NUEVO: Pasar folio_inventario explícitamente
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:847:                folio_inventario=inv.clave.folio_inventario
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:851:                logger.info(f"[INVENTARIOS_DETECTOR] Workflow creado: {resumen.get('workflow_id')}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:854:                logger.info(f"[INVENTARIOS_DETECTOR] Workflow no creado: {resumen.get('mensaje', 'Sin detalles')}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:858:            logger.error(f"[INVENTARIOS_DETECTOR] Error en orquestación: {e}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:866:        await actualizar_inventario_error(
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:870:            almacen_id=clave.get("almacen_id", ""),
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:871:            folio_inventario=clave.get("folio_inventario", ""),
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:875:        self.stats["inventarios_error"] += 1
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:878:            logger.error(f"[INVENTARIOS_DETECTOR] ERROR CRÍTICO: Máximo de intentos alcanzado - {error_msg}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:880:            logger.warning(f"[INVENTARIOS_DETECTOR] Error (intento {intentos}/{MAX_INTENTOS}): {error_msg}")
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:885:            f"Detectados: {self.stats['inventarios_detectados']}, "
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:886:            f"Nuevos: {self.stats['inventarios_nuevos']}, "
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:887:            f"Procesados: {self.stats['inventarios_procesados']}, "
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:888:            f"Errores: {self.stats['inventarios_error']}, "
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:889:            f"Duplicados: {self.stats['inventarios_duplicados']}"
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:897:def create_inventarios_detector_job(db, config: Optional[dict] = None) -> InventariosDetectorJob:
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:899:    return InventariosDetectorJob(db, config)
/app/backend/core/system_type_utils.py:357:            "compras", "inventarios", "server-123", "MPRO",
/app/backend/core/system_type_utils.py:360:        → "compras:inventarios:server-123:MANAGEMENTPRO:sucursal_id=0021:fecha_inicio=2025-01-01"
/app/backend/core/secret_manager.py:288:    Prepara un secreto para almacenamiento.
/app/backend/core/communications/dispatcher/dispatcher.py:266:        config = await self.repository.get_config(canal, item.get("modulo", "inventarios"), evento)
/app/backend/core/communications/dispatcher/dispatcher.py:415:            modulo=item.get("modulo", "inventarios"),
/app/backend/core/communications/notifications/service.py:7:cualquier módulo del sistema (inventarios, compras, CxP, etc.).
/app/backend/core/communications/notifications/service.py:272:            modulo="inventarios",
/app/backend/core/communications/notifications/service.py:299:            modulo="inventarios",
/app/backend/core/communications/notifications/service.py:327:            modulo="inventarios",
/app/backend/core/communications/notifications/service.py:355:            modulo="inventarios",
/app/backend/core/communications/notifications/service.py:382:            modulo="inventarios",
/app/backend/core/communications/notifications/service.py:406:            modulo="inventarios",
/app/backend/core/communications/notifications/service.py:429:            modulo="inventarios",
/app/backend/core/communications/notifications/schemas.py:95:    modulo: str = "inventarios"  # inventarios, compras, cxp, etc.
/app/backend/core/communications/notifications/schemas.py:162:    codigo: str  # inventarios_sla_vencido, inventarios_asignacion_tarea
/app/backend/core/communications/notifications/schemas.py:193:    modulo: str = "inventarios"
/app/backend/core/communications/notifications/schemas.py:236:    modulo: str = "inventarios"
/app/backend/core/communications/notifications/schemas.py:289:    modulo: str = "inventarios"
/app/backend/core/communications/notifications/schemas.py:341:    modulo: str = "inventarios"
/app/backend/core/communications/templates/template_service.py:25:    "inventarios_asignacion_tarea": {
/app/backend/core/communications/templates/template_service.py:26:        "codigo": "inventarios_asignacion_tarea",
/app/backend/core/communications/templates/template_service.py:31:    "inventarios_diferencia_detectada": {
/app/backend/core/communications/templates/template_service.py:32:        "codigo": "inventarios_diferencia_detectada",
/app/backend/core/communications/templates/template_service.py:37:    "inventarios_sla_por_vencer": {
/app/backend/core/communications/templates/template_service.py:38:        "codigo": "inventarios_sla_por_vencer",
/app/backend/core/communications/templates/template_service.py:43:    "inventarios_sla_vencido": {
/app/backend/core/communications/templates/template_service.py:44:        "codigo": "inventarios_sla_vencido",
/app/backend/core/communications/templates/template_service.py:49:    "inventarios_sla_escalado": {
/app/backend/core/communications/templates/template_service.py:50:        "codigo": "inventarios_sla_escalado",
/app/backend/core/communications/templates/template_service.py:55:    "inventarios_justificacion_rechazada": {
/app/backend/core/communications/templates/template_service.py:56:        "codigo": "inventarios_justificacion_rechazada",
/app/backend/core/communications/templates/template_service.py:61:    "inventarios_decision_auditoria": {
/app/backend/core/communications/templates/template_service.py:62:        "codigo": "inventarios_decision_auditoria",
/app/backend/core/communications/templates/template_service.py:67:    "inventarios_cierre_workflow": {
/app/backend/core/communications/templates/template_service.py:68:        "codigo": "inventarios_cierre_workflow",
/app/backend/core/communications/templates/template_service.py:73:    "inventarios_responsabilidad_propuesta": {
/app/backend/core/communications/templates/template_service.py:74:        "codigo": "inventarios_responsabilidad_propuesta",
/app/backend/core/communications/templates/template_service.py:79:    "inventarios_responsabilidad_aprobada": {
/app/backend/core/communications/templates/template_service.py:80:        "codigo": "inventarios_responsabilidad_aprobada",
/app/backend/core/communications/scripts/__init__.py:126:        "modulo": "inventarios",
/app/backend/core/communications/scripts/__init__.py:131:        "template_codigo": "inventarios_asignacion_tarea",
/app/backend/core/communications/scripts/__init__.py:142:        "modulo": "inventarios",
/app/backend/core/communications/scripts/__init__.py:147:        "template_codigo": "inventarios_sla_por_vencer",
/app/backend/core/communications/scripts/__init__.py:158:        "modulo": "inventarios",
/app/backend/core/communications/scripts/__init__.py:163:        "template_codigo": "inventarios_sla_vencido",
/app/backend/core/communications/scripts/__init__.py:174:        "modulo": "inventarios",
/app/backend/core/communications/scripts/__init__.py:179:        "template_codigo": "inventarios_sla_escalado",
/app/backend/core/communications/scripts/__init__.py:190:        "modulo": "inventarios",
/app/backend/core/communications/scripts/__init__.py:195:        "template_codigo": "inventarios_justificacion_rechazada",
/app/backend/core/communications/scripts/__init__.py:221:        "codigo": "inventarios_asignacion_tarea",
/app/backend/core/communications/scripts/__init__.py:232:        "codigo": "inventarios_sla_por_vencer",
/app/backend/core/communications/scripts/__init__.py:243:        "codigo": "inventarios_sla_vencido",
/app/backend/core/communications/scripts/__init__.py:254:        "codigo": "inventarios_sla_escalado",
/app/backend/core/communications/scripts/__init__.py:265:        "codigo": "inventarios_justificacion_rechazada",
/app/backend/core/communications/scripts/__init__.py:276:        "codigo": "inventarios_decision_auditoria",
/app/backend/core/communications/scripts/__init__.py:287:        "codigo": "inventarios_cierre_workflow",
/app/backend/core/communications/routes.py:91:    modulo: str = "inventarios"
/app/backend/core/context_resolver.py:21:- Operaciones (Dashboard, Inventarios)
/app/backend/core/user_access_context.py:12:- ¿Qué almacenes tiene permitidos?
/app/backend/core/user_access_context.py:36:- Usuario_AlmacenesAsignacion
/app/backend/core/user_access_context.py:100:    # Almacenes por servidor (efectivos)
/app/backend/core/user_access_context.py:101:    almacenes_por_server: Dict[str, List[str]] = field(default_factory=dict)
/app/backend/core/user_access_context.py:135:            "almacenes_por_server": self.almacenes_por_server,
/app/backend/core/user_access_context.py:297:def _get_user_almacenes_sql(cursor, usuario_id: int) -> Dict[str, List[str]]:
/app/backend/core/user_access_context.py:299:    Obtiene almacenes asignados al usuario agrupados por servidor.
/app/backend/core/user_access_context.py:304:            AlmacenCodigo
/app/backend/core/user_access_context.py:305:        FROM Usuario_AlmacenesAsignacion
/app/backend/core/user_access_context.py:309:    almacenes_por_server: Dict[str, List[str]] = {}
/app/backend/core/user_access_context.py:312:        almacen_codigo = row[1]
/app/backend/core/user_access_context.py:313:        if server_id not in almacenes_por_server:
/app/backend/core/user_access_context.py:314:            almacenes_por_server[server_id] = []
/app/backend/core/user_access_context.py:315:        almacenes_por_server[server_id].append(almacen_codigo)
/app/backend/core/user_access_context.py:317:    return almacenes_por_server
/app/backend/core/user_access_context.py:333:    - Qué almacenes puede ver
/app/backend/core/user_access_context.py:420:            # PASO 5: Resolver almacenes permitidos desde SQL
/app/backend/core/user_access_context.py:422:            almacenes = _get_user_almacenes_sql(cursor, usuario_id)
/app/backend/core/user_access_context.py:423:            for server_id, alm_list in almacenes.items():
/app/backend/core/user_access_context.py:425:                    context.almacenes_por_server[server_id] = alm_list
/app/backend/core/user_access_context.py:485:        # Para acceso global, no hay restricciones de almacenes/sucursales
/app/backend/core/user_access_context.py:522:def has_almacen_access(context: UserAccessContext, server_id: str, almacen_id: str) -> bool:
/app/backend/core/user_access_context.py:533:    # Si no hay restricción de almacenes para este servidor, permitir todos
/app/backend/core/user_access_context.py:534:    almacenes_permitidos = context.almacenes_por_server.get(server_id.lower())
/app/backend/core/user_access_context.py:535:    if not almacenes_permitidos:
/app/backend/core/user_access_context.py:538:    return almacen_id in almacenes_permitidos
/app/backend/core/user_access_context.py:571:# FUNCIONES DE FILTRADO SQL PARA ALMACENES (Sin cambios - usan contexto)
/app/backend/core/user_access_context.py:574:def get_almacenes_permitidos(context: UserAccessContext, server_id: str) -> List[str]:
/app/backend/core/user_access_context.py:576:    Obtiene la lista de almacenes permitidos para un servidor.
/app/backend/core/user_access_context.py:585:        Lista de IDs de almacenes permitidos, o lista vacía si puede ver todos
/app/backend/core/user_access_context.py:590:    return context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:593:def get_almacenes_sql_filter(context: UserAccessContext, server_id: str, column_name: str) -> str:
/app/backend/core/user_access_context.py:595:    Genera cláusula SQL WHERE para filtrar por almacenes permitidos.
/app/backend/core/user_access_context.py:600:        column_name: Nombre de la columna SQL a filtrar (ej: 'A.Al_Cve_Almacen')
/app/backend/core/user_access_context.py:608:    almacenes = context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:609:    if not almacenes:
/app/backend/core/user_access_context.py:613:    safe_almacenes = [str(a).replace("'", "''") for a in almacenes]
/app/backend/core/user_access_context.py:614:    almacenes_str = "','".join(safe_almacenes)
/app/backend/core/user_access_context.py:615:    return f" AND {column_name} IN ('{almacenes_str}')"
/app/backend/core/user_access_context.py:618:def get_almacenes_sql_filter_like(context: UserAccessContext, server_id: str, column_name: str) -> str:
/app/backend/core/user_access_context.py:634:    almacenes = context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:635:    if not almacenes:
/app/backend/core/user_access_context.py:640:    for alm in almacenes:
/app/backend/core/user_access_context.py:647:def validate_almacen_in_scope(context: UserAccessContext, server_id: str, almacen_id: str) -> bool:
/app/backend/core/user_access_context.py:654:        almacen_id: ID del almacén a validar
/app/backend/core/user_access_context.py:662:    almacenes_permitidos = context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:663:    if not almacenes_permitidos:
/app/backend/core/user_access_context.py:666:    return almacen_id in almacenes_permitidos
/app/backend/core/user_access_context.py:669:def filter_results_by_almacen(
/app/backend/core/user_access_context.py:673:    almacen_field: str = 'almacen'
/app/backend/core/user_access_context.py:676:    Filtra resultados post-query por almacenes permitidos.
/app/backend/core/user_access_context.py:683:        almacen_field: Nombre del campo que contiene el almacén
/app/backend/core/user_access_context.py:691:    almacenes_permitidos = context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:692:    if not almacenes_permitidos:
/app/backend/core/user_access_context.py:698:        almacen_value = str(r.get(almacen_field, '')).strip().upper()
/app/backend/core/user_access_context.py:699:        for permitido in almacenes_permitidos:
/app/backend/core/user_access_context.py:700:            if str(permitido).upper() in almacen_value or almacen_value in str(permitido).upper():
/app/backend/core/user_access_context.py:716:    'has_almacen_access',
/app/backend/core/user_access_context.py:720:    # Nuevas funciones FASE 8 - Enforcement de Almacenes
/app/backend/core/user_access_context.py:721:    'get_almacenes_permitidos',
/app/backend/core/user_access_context.py:722:    'get_almacenes_sql_filter',
/app/backend/core/user_access_context.py:723:    'get_almacenes_sql_filter_like',
/app/backend/core/user_access_context.py:724:    'validate_almacen_in_scope',
/app/backend/core/user_access_context.py:725:    'filter_results_by_almacen',
/app/backend/core/centro_control/recipients_manager.py:4:Almacena y gestiona los destinatarios de notificaciones en MongoDB.
/app/backend/core/centro_control/routes.py:1195:    Los destinatarios se almacenan en MongoDB y son utilizados por los
/app/backend/core/cerebro.py:124:    {"id": "inventarios", "nombre": "Inventarios", "icono": "Package"},
/app/backend/core/cerebro.py:210:    query_inventario: Optional[QueryConfig] = None
/app/backend/core/cerebro.py:348:# MODELOS DE DATOS - INVENTARIOS
/app/backend/core/cerebro.py:352:    """Producto con diferencia de inventario"""
/app/backend/core/cerebro.py:362:class InventarioDiferenciaDetalle(BaseModel):
/app/backend/core/cerebro.py:363:    """Detalle de diferencias de inventario"""
/app/backend/core/cerebro.py:366:    almacen_id: str
/app/backend/core/cerebro.py:368:    fecha_inventario: str
/app/backend/core/cerebro.py:374:class CorteInventario(BaseModel):
/app/backend/core/cerebro.py:375:    """Corte de inventario para comparativo"""
/app/backend/core/cerebro.py:381:class InventarioDiferenciasCache(BaseModel):
/app/backend/core/cerebro.py:382:    """Caché de diferencias de inventario"""
/app/backend/core/cerebro.py:386:    almacen_id: str
/app/backend/core/cerebro.py:387:    almacen_nombre: str
/app/backend/core/cerebro.py:391:    cortes: List[CorteInventario]
/app/backend/core/cerebro.py:408:    """Informe de auditoría de inventario"""
/app/backend/core/cerebro.py:415:    almacen_id: str
/app/backend/core/cerebro.py:416:    almacen_nombre: str
/app/backend/core/cerebro.py:419:    inventario_inicial_id: str
/app/backend/core/cerebro.py:420:    inventario_inicial_fecha: str
/app/backend/core/cerebro.py:421:    inventario_final_id: str
/app/backend/core/cerebro.py:422:    inventario_final_fecha: str
/app/backend/core/cerebro.py:680:    # Inventarios
/app/backend/core/cerebro.py:681:    "inventario_diferencias_detalle": InventarioDiferenciaDetalle,
/app/backend/core/cerebro.py:682:    "inventario_diferencias_cache": InventarioDiferenciasCache,
/app/backend/core/cerebro.py:764:    # Modelos Inventarios
/app/backend/core/cerebro.py:765:    'ProductoDiferencia', 'InventarioDiferenciaDetalle', 'InventarioDiferenciasCache',
/app/backend/core/auth/user_repository_sql.py:879:            UPDATE Usuario_AlmacenesAsignacion SET Activo = 0, FechaModificacion = GETDATE()
/app/backend/core/alcance_helper.py:150:async def _resolver_almacen(alcance_data: Dict, _db) -> Set[str]:
/app/backend/core/alcance_helper.py:151:    """Resuelve empresas para alcance tipo ALMACEN."""
/app/backend/core/alcance_helper.py:161:    'ALMACEN': _resolver_almacen,
/app/backend/core/system_capability_resolver.py:82:    INVENTARIOS = "INVENTARIOS"
/app/backend/core/inventory_analysis_core.py:3:EDARSA HUB - Core Service: Análisis de Inventarios
/app/backend/core/inventory_analysis_core.py:7:Este Core Service permite reutilizar la lógica de análisis de inventarios
/app/backend/core/inventory_analysis_core.py:35:    Parámetros para generar análisis de inventario.
/app/backend/core/inventory_analysis_core.py:46:    almacen: Optional[str] = None
/app/backend/core/inventory_analysis_core.py:47:    almacenes: list = Field(default_factory=list)
/app/backend/core/inventory_analysis_core.py:61:    # Info completa de inventarios
/app/backend/core/inventory_analysis_core.py:62:    inventarios_iniciales_info: list = Field(default_factory=list)
/app/backend/core/inventory_analysis_core.py:63:    inventarios_finales_info: list = Field(default_factory=list)
/app/backend/core/inventory_analysis_core.py:82:            'almacen': self.almacen,
/app/backend/core/inventory_analysis_core.py:83:            'almacenes': self.almacenes,
/app/backend/core/inventory_analysis_core.py:90:            'inventarios_iniciales_info': self.inventarios_iniciales_info,
/app/backend/core/inventory_analysis_core.py:91:            'inventarios_finales_info': self.inventarios_finales_info,
/app/backend/core/inventory_analysis_core.py:105:    Core Service para análisis de inventarios.
/app/backend/core/inventory_analysis_core.py:143:        Genera el análisis de inventario.
/app/backend/core/inventory_analysis_core.py:191:        Genera el análisis de inventario usando Dict directamente.
/app/backend/core/inventory_analysis_core.py:211:async def ejecutar_analisis_inventario(
/app/backend/core/inventory_analysis_core.py:217:    Función de conveniencia para ejecutar análisis de inventario.
```
