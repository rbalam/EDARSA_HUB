# Diagnóstico de filtros actuales EDARSAHUB

Fecha: Wed Jun  3 07:03:00 UTC 2026

## 1. Endpoints backend relacionados con filtros
```text
/app/backend/server.py:1548:@api_router.post("/servers")
/app/backend/server.py:1605:@api_router.get("/servers", response_model=List[Server])
/app/backend/server.py:1632:@api_router.get("/servers/{server_id}")
/app/backend/server.py:1659:@api_router.put("/servers/{server_id}")
/app/backend/server.py:1717:@api_router.delete("/servers/{server_id}")
/app/backend/server.py:1772:@api_router.get("/servers/{server_id}/ping")
/app/backend/server.py:1988:@api_router.post("/servers/{server_id}/queries/validate")
/app/backend/server.py:2095:@api_router.put("/servers/{server_id}/queries/{query_type}")
/app/backend/server.py:2177:@api_router.get("/servers/{server_id}/queries")
/app/backend/server.py:2232:@api_router.delete("/servers/{server_id}/queries/{query_type}")
/app/backend/server.py:2274:@api_router.get("/servers/{server_id}/tipos-movimiento")
/app/backend/server.py:2403:@api_router.get("/servers/{server_id}/categorias")
/app/backend/server.py:2440:@api_router.get("/servers/{server_id}/departamentos")
/app/backend/server.py:2550:@api_router.get("/servers/{server_id}/sucursales")
/app/backend/server.py:2654:@api_router.get("/servers/{server_id}/almacenes")
/app/backend/server.py:2764:@api_router.get("/servers/{server_id}/sucursales-config")
/app/backend/server.py:2799:@api_router.post("/servers/{server_id}/sucursales-config/sync")
/app/backend/server.py:2906:@api_router.put("/servers/{server_id}/sucursales-config/{sucursal_origen_id}")
/app/backend/server.py:2943:@api_router.put("/servers/{server_id}/sucursales-config/bulk")
/app/backend/server.py:2982:@api_router.get("/sucursales")
/app/backend/server.py:3171:@api_router.get("/servers/{server_id}/almacenes-softrestaurant")
/app/backend/server.py:3244:@api_router.get("/servers/{server_id}/inventarios")
/app/backend/server.py:3646:@api_router.get("/servers/{server_id}/report-filters")
/app/backend/server.py:6992:@api_router.get("/dashboard/servers-configured")
/app/backend/server.py:8136:@api_router.post("/compras/productos-para-captura")
/app/backend/server.py:12190:# @api_router.get("/rrhh/catalogos/sucursales")
/app/backend/server.py:16742:@api_router.get("/sistema/mapeo-servidores")
/app/backend/server.py:17636:@api_router.get("/admin/alcance/empresas")
/app/backend/server.py:17679:@api_router.get("/admin/alcance/sucursales")
/app/backend/server.py.backup_pre_fase2a:893:@api_router.post("/servers")
/app/backend/server.py.backup_pre_fase2a:914:@api_router.get("/servers", response_model=List[Server])
/app/backend/server.py.backup_pre_fase2a:920:@api_router.get("/servers/{server_id}")
/app/backend/server.py.backup_pre_fase2a:930:@api_router.put("/servers/{server_id}")
/app/backend/server.py.backup_pre_fase2a:951:@api_router.delete("/servers/{server_id}")
/app/backend/server.py.backup_pre_fase2a:960:@api_router.get("/servers/{server_id}/ping")
/app/backend/server.py.backup_pre_fase2a:1164:@api_router.post("/servers/{server_id}/queries/validate")
/app/backend/server.py.backup_pre_fase2a:1255:@api_router.put("/servers/{server_id}/queries/{query_type}")
/app/backend/server.py.backup_pre_fase2a:1315:@api_router.get("/servers/{server_id}/queries")
/app/backend/server.py.backup_pre_fase2a:1362:@api_router.delete("/servers/{server_id}/queries/{query_type}")
/app/backend/server.py.backup_pre_fase2a:1388:@api_router.get("/servers/{server_id}/tipos-movimiento")
/app/backend/server.py.backup_pre_fase2a:1432:@api_router.get("/servers/{server_id}/categorias")
/app/backend/server.py.backup_pre_fase2a:1474:@api_router.get("/servers/{server_id}/departamentos")
/app/backend/server.py.backup_pre_fase2a:1567:@api_router.get("/servers/{server_id}/sucursales")
/app/backend/server.py.backup_pre_fase2a:1659:@api_router.get("/servers/{server_id}/almacenes")
/app/backend/server.py.backup_pre_fase2a:1711:@api_router.get("/servers/{server_id}/sucursales-config")
/app/backend/server.py.backup_pre_fase2a:1734:@api_router.post("/servers/{server_id}/sucursales-config/sync")
/app/backend/server.py.backup_pre_fase2a:1829:@api_router.put("/servers/{server_id}/sucursales-config/{sucursal_origen_id}")
/app/backend/server.py.backup_pre_fase2a:1866:@api_router.put("/servers/{server_id}/sucursales-config/bulk")
/app/backend/server.py.backup_pre_fase2a:1904:@api_router.get("/servers/{server_id}/almacenes-softrestaurant")
/app/backend/server.py.backup_pre_fase2a:1945:@api_router.get("/servers/{server_id}/inventarios")
/app/backend/server.py.backup_pre_fase2a:2256:@api_router.get("/servers/{server_id}/report-filters")
/app/backend/server.py.backup_pre_fase2a:5284:@api_router.get("/dashboard/servers-configured")
/app/backend/server.py.backup_pre_fase2a:6186:@api_router.post("/compras/productos-para-captura")
/app/backend/server.py.backup_pre_fase2a:9172:# @api_router.get("/rrhh/catalogos/sucursales")
```

## 2. Frontend con fetch directo a filtros
```text
/app/frontend/src/pages/Comercial.js:2807:  // NO hacer llamada adicional a /api/servers/.../sucursales que no respeta RBAC
/app/frontend/src/pages/AutorizacionCompras.js.backup:87:        const response = await axios.get(`${API_URL}/api/servers`, {
/app/frontend/src/pages/AutorizacionCompras.js.backup:218:      const response = await axios.get(`${API_URL}/api/servers/${serverId}/sucursales`, {
/app/frontend/src/pages/AutorizacionCompras.js.backup:230:      const response = await axios.get(`${API_URL}/api/servers/${serverId}/almacenes?sucursal=${encodeURIComponent(sucursal)}`, {
/app/frontend/src/components/PropinasTPV.jsx:107:      const res = await fetch(`${API_URL}/api/servers`, {
/app/frontend/src/components/PropinasTPV.jsx:130:      const resSuc = await fetch(`${API_URL}/api/sucursales`, {
/app/frontend/src/components/PropinasTPV.jsx:138:      const resServers = await fetch(`${API_URL}/api/servers`, {
/app/frontend/src/components/tesoreria/useTesoreriaCorteZData.js:6: * FIX BUG 2026-05-26: Usa fetchUnidadesNegocio centralizado en lugar de /api/servers
/app/frontend/src/services/serversService.js:4: * Servicio centralizado para el consumo de /api/servers
/app/frontend/src/services/serversService.js:12: * - NO modifica el endpoint /api/servers
/app/frontend/src/services/serversService.js:34: * @param {Array} servers - Array de servidores del endpoint /api/servers
/app/frontend/src/services/serversService.js:43: * Obtiene servidores operativos desde /api/servers
```

## 3. Posibles conexiones live en backend
```text
/app/backend/init_queries.py:4:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/init_queries.py:10:mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/init_queries.py:266:    client = AsyncIOMotorClient(mongo_url)
/app/backend/migrar_a_sql.py:24:            if 'pymongo' not in linea and 'motor' not in linea:
/app/backend/migrar_a_sql.py:26:    print("✅ Limpiado: requirements.txt (eliminado pymongo/motor)")
/app/backend/migrar_a_sql.py:28:# 3. Centralización del motor SQL en db.py
/app/backend/modules/comercial/service.py:128:        result = execute_sql_query(
/app/backend/modules/comercial/service.py:480:        result = execute_sql_query(
/app/backend/modules/comercial/service.py:1937:        result_ultimo = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/service.py:2063:            result_ultimo_suc = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/service.py:2126:            r_ant = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/service.py:2149:            r_año = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/service.py:2632:        conn = pymssql.connect(
/app/backend/modules/comercial/routes_pricing_ai.py:396:            "mongodb": False,
/app/backend/modules/comercial/cache_service.py:25:# Importar db desde server.py (motor async client)
/app/backend/modules/comercial/queries/mpro.py:199:        result = execute_sql_query(
/app/backend/modules/comercial/queries/mpro.py:380:        result = execute_sql_query(
/app/backend/modules/comercial/queries/mpro.py:690:        result = execute_sql_query(
/app/backend/modules/comercial/queries/softrestaurant.py:181:        result = execute_sql_query(
/app/backend/modules/comercial/crm_router.py:202:    # Nota: Se asume que el sistema genera el folio secuencial o via el motor SQL.
/app/backend/modules/comercial/inteligencia_comercial_routes.py:62:    return pytds.connect(
/app/backend/modules/comercial/alertas_margen_service.py:402:    NOTA: Este es un endpoint de prueba. El motor de evaluación masiva
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
/app/backend/modules/comercial/routes_pricing_ia.py:610:    Tipos de motor disponibles:
/app/backend/modules/comercial/routes_pricing_ia.py:622:    Para vinos, use tipo_motor=VINOS_RANGOS.
/app/backend/modules/comercial/routes_pricing_ia.py:629:        f"motor={request.tipo_motor.value} estado={resultado.estado.value}"
/app/backend/modules/comercial/routes.py.bak:457:        result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:1961:        result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:2044:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py.bak:2160:            result_prod = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:2192:            result_vend = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:2245:            result_prod = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:2278:            result_vend = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:2381:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py.bak:2505:                result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:2543:                    result_simple = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:2581:            result_rent = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:2683:            conn = pymssql.connect(
/app/backend/modules/comercial/routes.py.bak:2791:                conn_hoy = pymssql.connect(
/app/backend/modules/comercial/routes.py.bak:2900:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py.bak:3022:            result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3078:            result_rot = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3136:            result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3169:                        result_nombre = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3209:            result_rotacion = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3347:            result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3362:            result_total = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3442:            result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3458:            result_total = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3598:            result_ventas_reales = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3646:            ventas_actual = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3651:            precios_base = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3884:            result_ventas_reales = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3924:            ventas_actual = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:3929:            precios_base = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:4129:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py.bak:4268:                result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:4298:                    detalle_result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:4340:                result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:4384:                r = execute_sql_query(server['host'], server['port'], server['database'], 
/app/backend/modules/comercial/routes.py.bak:4427:                result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:4452:                    det_result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:4494:                result = execute_sql_query(
/app/backend/modules/comercial/routes.py.bak:4538:                r = execute_sql_query(server['host'], server['port'], server['database'],
/app/backend/modules/comercial/routes_alertas_margen.py:281:    NOTA: Este es un endpoint de prueba. El motor de evaluación masiva
/app/backend/modules/comercial/repository.py:9:- execute_hub_query como motor central
/app/backend/modules/comercial/repository.py:153:        WHERE (id = '{server_id}' OR mongodb_id = '{server_id}')
/app/backend/modules/comercial/repository.py:156:        results = execute_sql_query(
/app/backend/modules/comercial/repository.py:186:        results = execute_sql_query(
/app/backend/modules/comercial/repository.py:306:        results = execute_sql_query(
/app/backend/modules/comercial/repository.py:384:    return execute_sql_query(
/app/backend/modules/comercial/repository.py:413:    return execute_sql_query(
/app/backend/modules/comercial/repository.py:448:    return execute_sql_query(
/app/backend/modules/comercial/historical_kpis_repository.py:57:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/modules/comercial/historical_kpis_repository.py:59:    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
/app/backend/modules/comercial/historical_kpis_repository.py:95:    return execute_sql_query(
/app/backend/modules/comercial/historical_kpis_repository.py:492:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/modules/comercial/historical_kpis_repository.py:494:    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
/app/backend/modules/comercial/services/impuestos_service.py:152:    override_result = execute_sql_query(*conn, override_query)
/app/backend/modules/comercial/services/impuestos_service.py:182:    producto_result = execute_sql_query(*conn, producto_query)
/app/backend/modules/comercial/services/impuestos_service.py:225:    sync_result = execute_sql_query(*conn, sync_query)
/app/backend/modules/comercial/services/impuestos_service.py:286:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/impuestos_service.py:339:    result = execute_sql_query(*conn, query)
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
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:75:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:225:    productos_raw = execute_sql_query(*conn, query) or []
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:226:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:376:    rangos = execute_sql_query(*conn, query) or []
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:433:    regla = execute_sql_query(*conn, query_regla)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:451:    traslape = execute_sql_query(*conn, query_traslape)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:472:        execute_sql_query(*conn, insert_query)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:504:    rango = execute_sql_query(*conn, query_existe)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:537:        traslape = execute_sql_query(*conn, query_traslape)
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:570:        execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/pricing_ai_service.py:151:        execute_sql_query(*conn, ddl)
/app/backend/modules/comercial/services/pricing_ai_service.py:185:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/pricing_ai_service.py:478:        execute_sql_query(*conn, insert_query)
/app/backend/modules/comercial/services/pricing_ai_service.py:525:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/pricing_ai_service.py:672:        tipo_motor=TipoMotorPrecio.COSTO_MARGEN,
/app/backend/modules/comercial/services/perfil_unidad_service.py:5:que sirven como contexto para el motor de precios con IA y benchmark.
/app/backend/modules/comercial/services/perfil_unidad_service.py:115:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:159:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:210:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:261:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:285:    check_result = execute_sql_query(*conn, check_query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:385:    execute_sql_query(*conn, insert_query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:476:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/perfil_unidad_service.py:496:    execute_sql_query(*conn, update_query)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:4:Este módulo orquesta el cálculo de precios sugeridos usando diferentes motores:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:99:    result = execute_sql_query(*conn, query_receta)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:118:    result_insumos = execute_sql_query(*conn, query_insumos)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:149:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:178:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:248:        tipo_motor=request.tipo_motor,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:259:        if request.tipo_motor == TipoMotorPrecio.VINOS_RANGOS:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:263:                response.mensaje = "El producto no es vino. Use motor COSTO_MARGEN para productos generales."
/app/backend/modules/comercial/services/pricing_sugerido_service.py:300:        if request.tipo_motor == TipoMotorPrecio.COSTO_MARGEN:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:371:        if request.tipo_motor == TipoMotorPrecio.BENCHMARK_COMPETENCIA:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:410:        if request.tipo_motor == TipoMotorPrecio.MIXTO_COSTO_COMPETENCIA:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:487:        response.mensaje = f"Tipo de motor no reconocido: {request.tipo_motor}"
/app/backend/modules/comercial/services/pricing_sugerido_service.py:499:    tipo_motor: TipoMotorPrecio,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:510:        tipo_motor: Motor a usar para todos los productos
/app/backend/modules/comercial/services/pricing_sugerido_service.py:541:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:551:            tipo_motor=tipo_motor,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:561:def obtener_estadisticas_calculo(server_id: str, tipo_motor: TipoMotorPrecio = TipoMotorPrecio.COSTO_MARGEN) -> Dict[str, Any]:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:571:        tipo_motor=tipo_motor,
/app/backend/modules/comercial/services/metricas_ia_service.py:105:        result = execute_sql_query(*conn, query_totales)
/app/backend/modules/comercial/services/metricas_ia_service.py:140:        result = execute_sql_query(*conn, query_por_dia)
/app/backend/modules/comercial/services/metricas_ia_service.py:163:        result = execute_sql_query(*conn, query_productos)
/app/backend/modules/comercial/services/metricas_ia_service.py:185:        result = execute_sql_query(*conn, query_competidores)
/app/backend/modules/comercial/services/metricas_ia_service.py:220:        result = execute_sql_query(*conn, query_ultimos)
/app/backend/modules/comercial/services/metricas_ia_service.py:251:        result = execute_sql_query(*conn, query_promedios)
/app/backend/modules/comercial/services/metricas_ia_service.py:274:        result = execute_sql_query(*conn, query_tipos)
/app/backend/modules/comercial/services/metricas_ia_service.py:324:        result = execute_sql_query(*conn, query_comp)
/app/backend/modules/comercial/services/metricas_ia_service.py:344:        result = execute_sql_query(*conn, query_items)
/app/backend/modules/comercial/services/precios_vinos_service.py:258:    result_cr = execute_sql_query(*conn, query_costo_receta)
/app/backend/modules/comercial/services/precios_vinos_service.py:278:    result_insumos = execute_sql_query(*conn, query_insumos)
/app/backend/modules/comercial/services/precios_vinos_service.py:326:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/precios_vinos_service.py:353:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/precios_vinos_service.py:389:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/precios_vinos_service.py:567:    result = execute_sql_query(*conn, query)
/app/backend/modules/comercial/services/pricing_schemas.py:79:    """Tipos de motor de cálculo de precio."""
/app/backend/modules/comercial/services/pricing_schemas.py:413:    tipo_motor: TipoMotorPrecio = Field(
/app/backend/modules/comercial/services/pricing_schemas.py:415:        description="Tipo de motor de cálculo"
/app/backend/modules/comercial/services/pricing_schemas.py:432:        tipo = values.get('tipo_motor')
/app/backend/modules/comercial/services/pricing_schemas.py:447:    tipo_motor: TipoMotorPrecio
/app/backend/modules/comercial/routes.py:457:        result = execute_sql_query(
/app/backend/modules/comercial/routes.py:1961:        result = execute_sql_query(
/app/backend/modules/comercial/routes.py:2044:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:2160:            result_prod = execute_sql_query(
/app/backend/modules/comercial/routes.py:2192:            result_vend = execute_sql_query(
/app/backend/modules/comercial/routes.py:2245:            result_prod = execute_sql_query(
/app/backend/modules/comercial/routes.py:2278:            result_vend = execute_sql_query(
/app/backend/modules/comercial/routes.py:2381:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:2505:                result = execute_sql_query(
/app/backend/modules/comercial/routes.py:2543:                    result_simple = execute_sql_query(
/app/backend/modules/comercial/routes.py:2581:            result_rent = execute_sql_query(
/app/backend/modules/comercial/routes.py:2683:            conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:2791:                conn_hoy = pymssql.connect(
/app/backend/modules/comercial/routes.py:2900:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:3022:            result = execute_sql_query(
/app/backend/modules/comercial/routes.py:3078:            result_rot = execute_sql_query(
/app/backend/modules/comercial/routes.py:3136:            result = execute_sql_query(
/app/backend/modules/comercial/routes.py:3169:                        result_nombre = execute_sql_query(
/app/backend/modules/comercial/routes.py:3209:            result_rotacion = execute_sql_query(
/app/backend/modules/comercial/routes.py:3347:            result = execute_sql_query(
/app/backend/modules/comercial/routes.py:3362:            result_total = execute_sql_query(
/app/backend/modules/comercial/routes.py:3442:            result = execute_sql_query(
/app/backend/modules/comercial/routes.py:3458:            result_total = execute_sql_query(
/app/backend/modules/comercial/routes.py:3598:            result_ventas_reales = execute_sql_query(
/app/backend/modules/comercial/routes.py:3646:            ventas_actual = execute_sql_query(
/app/backend/modules/comercial/routes.py:3651:            precios_base = execute_sql_query(
/app/backend/modules/comercial/routes.py:3884:            result_ventas_reales = execute_sql_query(
/app/backend/modules/comercial/routes.py:3924:            ventas_actual = execute_sql_query(
/app/backend/modules/comercial/routes.py:3929:            precios_base = execute_sql_query(
/app/backend/modules/comercial/routes.py:4129:        conn = pymssql.connect(
/app/backend/modules/fase2_operativo/sql_repository.py:41:    return pymssql.connect(
/app/backend/modules/fase2_operativo/db_utils.py:8:from pymongo import MongoClient
/app/backend/modules/fase2_operativo/db_utils.py:26:        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/modules/fase2_operativo/db_utils.py:29:        _client = MongoClient(mongo_url)
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:318:        return pymssql.connect(
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:9:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:20:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:23:    client = AsyncIOMotorClient(mongo_url)
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:16:from pymongo import MongoClient, ASCENDING, DESCENDING
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:335:        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
/app/backend/modules/api_connections/repository.py:79:        execute_sql_query(
/app/backend/modules/api_connections/repository.py:165:        results = execute_sql_query(
/app/backend/modules/api_connections/repository.py:196:        results = execute_sql_query(
/app/backend/modules/api_connections/repository.py:230:        results = execute_sql_query(
/app/backend/modules/api_connections/repository.py:316:        execute_sql_query(
/app/backend/modules/api_connections/repository.py:411:        execute_sql_query(
/app/backend/modules/api_connections/repository.py:453:        execute_sql_query(
/app/backend/modules/api_connections/repository.py:632:        results = execute_sql_query(
/app/backend/modules/api_connections/repository.py:683:        results = execute_sql_query(
/app/backend/modules/api_connections/universal_test_routes.py:142:        conn = pymssql.connect(
/app/backend/modules/api_connections/universal_test_routes.py:181:        conn = pymssql.connect(
/app/backend/modules/sistema/menu_service.py:29:        return pymssql.connect(
/app/backend/modules/costos_margenes/repository.py:60:    productos_result = execute_sql_query(*conn, productos_query)
/app/backend/modules/costos_margenes/repository.py:64:    insumos_result = execute_sql_query(*conn, insumos_query)
/app/backend/modules/costos_margenes/repository.py:68:    recetas_result = execute_sql_query(*conn, recetas_query)
/app/backend/modules/costos_margenes/repository.py:72:    elaborados_result = execute_sql_query(*conn, elaborados_query)
/app/backend/modules/costos_margenes/repository.py:186:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/costos_margenes/repository.py:232:    data_result = execute_sql_query(*conn, data_query) or []
/app/backend/modules/costos_margenes/repository.py:318:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository.py:348:            result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository.py:378:    receta_result = execute_sql_query(*conn, receta_query) or []
/app/backend/modules/costos_margenes/repository.py:444:    insumo_result = execute_sql_query(*conn, insumo_query)
/app/backend/modules/costos_margenes/repository.py:463:        insumo_result = execute_sql_query(*conn, producto_query)
/app/backend/modules/costos_margenes/repository.py:499:    elaborado_result = execute_sql_query(*conn, elaborado_query) or []
/app/backend/modules/costos_margenes/repository.py:599:    sync_result = execute_sql_query(*conn, sync_query)
/app/backend/modules/costos_margenes/repository.py:615:        result = execute_sql_query(*conn, count_query)
/app/backend/modules/costos_margenes/repository.py:626:    sistema_result = execute_sql_query(*conn, sistema_query) or []
/app/backend/modules/costos_margenes/repository.py:638:    servidor_result = execute_sql_query(*conn, servidor_query) or []
/app/backend/modules/costos_margenes/repository.py:707:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository.py:759:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository.py:804:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/routes.py:101:        user_result = execute_sql_query(*conn, user_query)
/app/backend/modules/costos_margenes/routes.py:116:        servers_result = execute_sql_query(*conn, servers_query) or []
/app/backend/modules/costos_margenes/repository_precios.py:103:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository_precios.py:246:    execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository_precios.py:330:    execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository_precios.py:355:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository_precios.py:385:    count_result = execute_sql_query(*conn, count_query)
/app/backend/modules/costos_margenes/repository_precios.py:400:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository_precios.py:512:    execute_sql_query(*conn, update_query)
/app/backend/modules/costos_margenes/repository_precios.py:543:    result = execute_sql_query(*conn, query)
/app/backend/modules/costos_margenes/repository_precios.py:649:    execute_sql_query(*conn, query)
/app/backend/modules/rh/importador/homologacion_service.py:30:    return pymssql.connect(
/app/backend/modules/rh/importador/aprobacion_service.py:47:    return pymssql.connect(
/app/backend/modules/rh/importador/repository.py:79:    return execute_sql_query(
/app/backend/modules/rh/repository.py:183:    return execute_sql_query(
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:37:    return pymssql.connect(
/app/backend/modules/configuracion/services/almacenes_sync_service.py:174:            almacenes_origen = execute_sql_query(
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:25:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:43:        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:45:        client = AsyncIOMotorClient(mongo_url)
/app/backend/modules/consultas_sql/repository.py:63:        return execute_sql_query(
/app/backend/modules/consultas_sql/routes.py:353:        versiones_rows = execute_sql_query(
/app/backend/modules/consultas_sql/routes.py:445:        servidores_rows = execute_sql_query(
/app/backend/modules/consultas_sql/routes.py:819:            rows = execute_sql_query(
/app/backend/modules/inteligencia_comercial/routes.py:79:    return pymssql.connect(
/app/backend/modules/catalogos/__init__.py:26:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/catalogos/repository.py:54:    return execute_sql_query(
/app/backend/modules/catalogos/routes.py:89:        rows = execute_sql_query(
/app/backend/modules/catalogos/routes.py:118:        rows = execute_sql_query(
/app/backend/modules/catalogos/routes.py:170:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:185:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:235:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:250:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:302:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:315:        execute_sql_query(
/app/backend/modules/catalogos/routes.py:346:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:367:        execute_sql_query(
/app/backend/modules/catalogos/routes.py:399:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:423:        execute_sql_query(
/app/backend/modules/catalogos/routes.py:458:        result = execute_sql_query(
/app/backend/modules/catalogos/routes.py:482:        execute_sql_query(
/app/backend/modules/sync_historicos/service.py:144:            result = execute_sql_query(
/app/backend/modules/sync_historicos/service.py:202:            result = execute_sql_query(
/app/backend/modules/sync_historicos/service.py:510:            result = execute_sql_query(
/app/backend/modules/sync_historicos/service.py:573:            result = execute_sql_query(
/app/backend/modules/sync_historicos/repository.py:61:        return execute_sql_query(
/app/backend/modules/sync_historicos/sync_ventas.py:149:            result = execute_sql_query(
/app/backend/modules/sync_historicos/sync_ventas.py:164:            count = execute_sql_query(
/app/backend/modules/sync_historicos/sync_ventas.py:175:            count = execute_sql_query(
/app/backend/modules/sync_historicos/sync_ventas.py:186:            count = execute_sql_query(
/app/backend/modules/automatizacion/repository.py:344:        conn = pymssql.connect(
/app/backend/modules/edge/comandero_terminal_ui.ts:67:        motorReglasBackend: any
/app/backend/modules/edge/comandero_terminal_ui.ts:78:        const maridajeSugerido = motorReglasBackend.interceptar_producto_para_maridaje(producto.id_producto);
/app/backend/modules/edge/motor_inventario_parametrico.py:1:# backend/modules/edge/motor_inventario_parametrico.py
/app/backend/modules/auth/service.py:374:        conn = pymssql.connect(
/app/backend/modules/auth/password_reset.py:55:    return pymssql.connect(
/app/backend/modules/auth/repository.py:101:        conn = pymssql.connect(
/app/backend/modules/auth/repository.py:313:    return pymssql.connect(
/app/backend/modules/auth/context_service.py:47:    return pymssql.connect(
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:94:        result = execute_sql_query(
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:163:        result = execute_sql_query(
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:184:        test_result = execute_sql_query(host, port, database, username, password, test_query)
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:198:        result = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:316:        rows = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:485:        rows = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:646:        result = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:721:        result = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:852:        result = execute_sql_query(
/app/backend/modules/comercial_v2/repository_readonly.py:46:        result = execute_sql_query(
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:54:        result = execute_sql_query(
/app/backend/modules/comercial_v2/schemas_api.py:61:    mongodb_cache: bool = False
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:235:        result = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:339:        rows = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:489:        rows = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:710:    result = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:739:    result = execute_sql_query(
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:777:    result = execute_sql_query(
/app/backend/modules/tablajeria/ordenes_service.py:39:        return pymssql.connect(
/app/backend/modules/tablajeria/dashboard_service.py:27:        return pymssql.connect(
/app/backend/modules/tablajeria/fase6_service.py:81:        return pymssql.connect(
/app/backend/modules/tablajeria/sync_service.py:43:        return pymssql.connect(
/app/backend/modules/tablajeria/sync_service.py:161:            conn_mpro = pymssql.connect(
/app/backend/modules/tablajeria/sync_service.py:592:            conn_cf = pymssql.connect(
/app/backend/modules/tablajeria/routes.py:50:    return pymssql.connect(
/app/backend/modules/universal_query/routes.py:184:        conn = pymssql.connect(
/app/backend/modules/sync_recetas/sync_recetas.py:316:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:340:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:362:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:394:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:417:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:436:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:474:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:565:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:584:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:606:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:700:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:752:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:769:    rows = execute_sql_query(host, port, database, username, password, query) or []
/app/backend/modules/sync_recetas/sync_recetas.py:829:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:873:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:931:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:992:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:1059:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:1088:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:1143:            execute_sql_query(
/app/backend/modules/sync_recetas/sync_recetas.py:1180:        execute_sql_query(
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
/app/backend/modules/finanzas/repository_bancarios.py:50:        result = execute_sql_query(
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:37:    return pymssql.connect(**config, login_timeout=30)
/app/backend/modules/finanzas/tesoreria.py:782:        results = execute_sql_query(
/app/backend/modules/finanzas/repository_cuadres_z.py:18:        from pymongo import MongoClient
/app/backend/modules/finanzas/repository_cuadres_z.py:19:        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/modules/finanzas/repository_cuadres_z.py:21:        client = MongoClient(mongo_url)
/app/backend/modules/finanzas/sync_propinas_mpro.py:85:    return pymssql.connect(
/app/backend/modules/finanzas/sync_propinas_mpro.py:168:    return pymssql.connect(
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:58:    return pymssql.connect(
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:187:        conn = pytds.connect(
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:205:        conn = pymssql.connect(
/app/backend/modules/finanzas/sql_query_worker.py:133:        conn = pytds.connect(**conn_params)
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:80:    return pymssql.connect(
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:188:        conn = pytds.connect(
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:204:        conn = pymssql.connect(
/app/backend/modules/finanzas/repository_ingresos_edarsahub.py:45:    return pymssql.connect(
/app/backend/modules/finanzas/health.py:62:        existing = execute_sql_query(
/app/backend/modules/finanzas/health.py:150:                    test_result = execute_sql_query(
/app/backend/modules/finanzas/repository_real.py:94:            results = execute_sql_query(
/app/backend/modules/finanzas/sql_query_worker_secure.py:103:        conn = pytds.connect(**conn_params)
/app/backend/modules/finanzas/repository_cortes_z.py:96:            results = execute_sql_query(
/app/backend/modules/finanzas/historical_kpis_repository.py:49:    return pytds.connect(
/app/backend/modules/finanzas/propinas_tpv/service.py:18:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:32:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:147:            "mongodb_connected": True,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:96:        return execute_sql_query(
/app/backend/modules/finanzas/propinas_tpv/repository_edarsahub.py:84:        return pymssql.connect(
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:32:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:62:            result = execute_sql_query(
/app/backend/modules/finanzas/propinas_tpv/repository.py:20:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/finanzas/propinas_tpv/repository.py:118:            result = execute_sql_query(
/app/backend/modules/finanzas/propinas_tpv/repository.py:201:            rows = execute_sql_query(
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:28:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/finanzas/propinas_tpv/routes.py:34:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/finanzas/propinas_tpv/routes.py:180:            "mongodb_connected": True,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:103:    return pymssql.connect(
/app/backend/modules/finanzas/test_conn_cienfuegos.py:442:        conn = pymssql.connect(
/app/backend/modules/finanzas/test_conn_cienfuegos.py:536:        conn = pytds.connect(
/app/backend/modules/finanzas/test_conn_cienfuegos.py:611:        conn = pymssql.connect(
/app/backend/modules/finanzas/test_conn_cienfuegos.py:679:        conn = pymssql.connect(
/app/backend/modules/finanzas/test_conn_cienfuegos.py:753:        conn = pymssql.connect(
/app/backend/modules/finanzas/test_conn_cienfuegos.py:821:        conn = pymssql.connect(
/app/backend/modules/finanzas/test_conn_cienfuegos.py:892:        conn = pymssql.connect(
/app/backend/modules/finanzas/sync_cortes_mpro.py:60:    return pymssql.connect(
/app/backend/modules/finanzas/sync_cortes_mpro.py:154:    return pymssql.connect(
/app/backend/modules/cava_socios/service.py:32:        return pymssql.connect(
/app/backend/modules/manuales_operativos/service.py:16:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/manuales_operativos/triggers.py:20:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/compras/repository_compras_sql.py:42:    return pymssql.connect(
/app/backend/modules/compras/eventos_compras.py:141:        return pymssql.connect(
/app/backend/modules/compras/eventos_compras.py:309:        return pymssql.connect(
/app/backend/modules/compras/repository.py:58:        result = execute_sql_query(
/app/backend/modules/compras/repository.py:223:    return execute_sql_query(
/app/backend/modules/compras/repository.py:249:    return execute_sql_query(
/app/backend/modules/compras/repository.py:284:    return execute_sql_query(
/app/backend/modules/compras/repository.py:332:        result = execute_sql_query(
/app/backend/modules/compras/repository.py:411:    return execute_sql_query(
/app/backend/modules/compras/repository.py:439:    return execute_sql_query(
/app/backend/modules/compras/repository.py:478:    return execute_sql_query(
/app/backend/modules/compras/historical_kpis_repository.py:50:    return pytds.connect(
/app/backend/modules/compras/sync_service.py:32:    return pymssql.connect(
/app/backend/modules/compras/repository_pedidos_sql.py:48:        conn = pymssql.connect(
/app/backend/modules/compras/repository_pedidos_sql.py:87:        conn = pymssql.connect(
/app/backend/scripts/sync_agent_piloto.py:96:        conn = pymssql.connect(
/app/backend/scripts/sync_agent_piloto.py:123:        conn = pyodbc.connect(conn_str)
/app/backend/scripts/correccion_sistema_menus_y_fallbacks.py:23:    conn = pymssql.connect(
/app/backend/scripts/consultar_cache_finops.py:16:    return pymssql.connect(
/app/backend/scripts/create_sesiones_tables.py:81:        conn = pymssql.connect(
/app/backend/scripts/run_historical_load_finanzas.py:87:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/scripts/run_historical_load_finanzas.py:88:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/run_historical_load_finanzas.py:89:    client = AsyncIOMotorClient(mongo_url)
/app/backend/scripts/run_historical_load_finanzas.py:223:        with pytds.connect(
/app/backend/scripts/run_historical_load_finanzas.py:289:        with pytds.connect(
/app/backend/scripts/run_historical_load_finanzas.py:363:        with pytds.connect(
/app/backend/scripts/run_historical_load_finanzas.py:429:        with pytds.connect(
/app/backend/scripts/motor_consolidacion_circuit_breaker.py:30:    Simula el motor lógico del tablero ejecutivo, integrando:
/app/backend/scripts/create_cava_socios_rbac.py:27:    return pymssql.connect(
/app/backend/scripts/create_cava_socios_tables.py:28:    return pymssql.connect(
/app/backend/scripts/update_proyeccion_con_funcion.py:15:    conn = pymssql.connect(
/app/backend/scripts/precheck_conectividad.py:20:from pymongo import MongoClient
/app/backend/scripts/precheck_conectividad.py:23:MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/precheck_conectividad.py:34:        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
/app/backend/scripts/precheck_conectividad.py:90:                result = execute_sql_query(
/app/backend/scripts/create_crm_automation_tables.py:14:    conn = pymssql.connect(
/app/backend/scripts/reconcile_servers_sql_mongo.py:35:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/scripts/reconcile_servers_sql_mongo.py:101:        # Indexar por ID y mongodb_id
/app/backend/scripts/reconcile_servers_sql_mongo.py:103:        sql_by_mongodb_id = {s['mongodb_id']: s for s in sql_servers if s.get('mongodb_id')}
/app/backend/scripts/reconcile_servers_sql_mongo.py:107:        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/reconcile_servers_sql_mongo.py:110:        client = AsyncIOMotorClient(mongo_url)
/app/backend/scripts/reconcile_servers_sql_mongo.py:123:            mongo_server = mongo_by_id.get(sql_id) or mongo_by_id.get(sql_server.get('mongodb_id'))
/app/backend/scripts/reconcile_servers_sql_mongo.py:183:            if mongo_id not in sql_by_id and mongo_id not in sql_by_mongodb_id:
/app/backend/scripts/correccion_proyeccion_y_moneda_final.py:90:        conn = pymssql.connect(
/app/backend/scripts/correccion_proyeccion_y_moneda_final.py:145:        logger.info("Verificando funcionamiento óptimo en el motor SQL:")
/app/backend/scripts/validate_encrypted_server_connectivity.py:164:    result = execute_sql_query(
/app/backend/scripts/validate_encrypted_server_connectivity.py:283:        conn = pymssql.connect(
/app/backend/scripts/seed_inteligencia_demo.py:22:    conn = pymssql.connect(
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:88:        registros = execute_sql_query(
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py:238:                    execute_sql_query(
/app/backend/scripts/sync_response_cache_finops.py:16:    return pymssql.connect(
/app/backend/scripts/consolidado_general_sistema_comercial.py:29:# Configuración del motor SQL Server de EDARSAHUB (Puerto 1433 por defecto)
/app/backend/scripts/consolidado_general_sistema_comercial.py:361:                SET @LogMessage = 'Ventas intermedias vacías. El motor comercial preserva los valores de respaldo de EDARSA.';
```

## 4. Hardcodes críticos
```text
/app/backend/init_queries.py:13:# Consultas MPRO
/app/backend/init_queries.py:14:MPRO_QUERIES = {
/app/backend/init_queries.py:276:    # Insert MPRO queries
/app/backend/init_queries.py:277:    for query_type, sql_query in MPRO_QUERIES.items():
/app/backend/init_queries.py:280:            "name": f"MPRO - {query_type.capitalize()}",
/app/backend/init_queries.py:281:            "system_type": "MPRO",
/app/backend/modules/comercial/service.py:92:# CÓDIGOS OFICIALES: 130MID, 130QRO, CIENFUEGOS, ESTELAR, ORIGEN
/app/backend/modules/comercial/service.py:153:            # Mapeo por server_id (para SoftRestaurant sin sucursal)
/app/backend/modules/comercial/service.py:157:            # Mapeo por server_id:sucursal (para MPRO con sucursal)
/app/backend/modules/comercial/service.py:184:        sucursal: ID de sucursal (para MPRO)
/app/backend/modules/comercial/service.py:213:    CAMBIO B HELPER: Obtiene código y nombre canónico para una sucursal MPRO.
/app/backend/modules/comercial/service.py:221:        server_id: ID del servidor MPRO
/app/backend/modules/comercial/service.py:239:        # Los códigos MPRO deben estar en Sistema_EmpresasServidores
/app/backend/modules/comercial/service.py:278:        '0021': ('130QRO', '130° QUERETARO'),
/app/backend/modules/comercial/service.py:279:        '0023': ('ORIGEN', 'ORIGEN'),
/app/backend/modules/comercial/service.py:280:        'ORIGEN': ('ORIGEN', 'ORIGEN'),
/app/backend/modules/comercial/service.py:281:        '130_QRO': ('130QRO', '130° QUERETARO'),
/app/backend/modules/comercial/service.py:299:    - La identidad principal es unidad_negocio_id CANÓNICO (130MID, 130QRO, etc.)
/app/backend/modules/comercial/service.py:305:    - 130MID (130° MÉRIDA)
/app/backend/modules/comercial/service.py:306:    - 130QRO (130° QUERÉTARO)  
/app/backend/modules/comercial/service.py:307:    - CIENFUEGOS
/app/backend/modules/comercial/service.py:308:    - ESTELAR (LA ESTELAR)
/app/backend/modules/comercial/service.py:309:    - ORIGEN
/app/backend/modules/comercial/service.py:331:        # Mérida - todas las variantes resuelven a 130MID
/app/backend/modules/comercial/service.py:332:        '130-MER': '130MID',
/app/backend/modules/comercial/service.py:333:        '130-MID': '130MID',
/app/backend/modules/comercial/service.py:334:        '130MER': '130MID',
/app/backend/modules/comercial/service.py:335:        '130 MERIDA': '130MID',
/app/backend/modules/comercial/service.py:336:        '130 MÉRIDA': '130MID',
/app/backend/modules/comercial/service.py:337:        '130° MERIDA': '130MID',
/app/backend/modules/comercial/service.py:338:        '130° MÉRIDA': '130MID',
/app/backend/modules/comercial/service.py:339:        'MERIDA': '130MID',
/app/backend/modules/comercial/service.py:340:        'MÉRIDA': '130MID',
/app/backend/modules/comercial/service.py:341:        # Querétaro - todas las variantes resuelven a 130QRO
/app/backend/modules/comercial/service.py:342:        '130-QRO': '130QRO',
/app/backend/modules/comercial/service.py:343:        '130 QRO': '130QRO',
/app/backend/modules/comercial/service.py:344:        '130 QUERETARO': '130QRO',
/app/backend/modules/comercial/service.py:345:        '130 QUERÉTARO': '130QRO',
/app/backend/modules/comercial/service.py:346:        '130° QUERETARO': '130QRO',
/app/backend/modules/comercial/service.py:347:        '130° QUERÉTARO': '130QRO',
/app/backend/modules/comercial/service.py:348:        'QUERETARO': '130QRO',
/app/backend/modules/comercial/service.py:349:        'QUERÉTARO': '130QRO',
/app/backend/modules/comercial/service.py:351:        'LA-ESTELAR': 'ESTELAR',
/app/backend/modules/comercial/service.py:352:        'LA ESTELAR': 'ESTELAR',
/app/backend/modules/comercial/service.py:354:        '130MID': '130MID',
/app/backend/modules/comercial/service.py:355:        '130QRO': '130QRO',
/app/backend/modules/comercial/service.py:356:        'CIENFUEGOS': 'CIENFUEGOS',
/app/backend/modules/comercial/service.py:357:        'ESTELAR': 'ESTELAR',
/app/backend/modules/comercial/service.py:358:        'ORIGEN': 'ORIGEN',
/app/backend/modules/comercial/service.py:372:    FASE 5B HELPER: Obtiene la lista de sucursales MPRO desde EmpresaResolver.
/app/backend/modules/comercial/service.py:374:    Lee de Sistema_EmpresasServidores las empresas que tienen conexión MPRO
/app/backend/modules/comercial/service.py:389:            # Buscar empresas con conexiones MPRO (tienen NumeroSucursalSistema)
/app/backend/modules/comercial/service.py:448:            logging.warning(f"[SERVICE] Error obteniendo sucursales MPRO desde EmpresaResolver: {e}")
/app/backend/modules/comercial/service.py:456:            "codigo": "ORIGEN",
/app/backend/modules/comercial/service.py:463:            "codigo": "130QRO",
/app/backend/modules/comercial/service.py:527:    RAZÓN: Para MPRO, los datos en Comercial_KPIs_Diarios_v2 tienen un server_id
/app/backend/modules/comercial/service.py:542:        # FIX: Usar unidad_negocio_id para MPRO
/app/backend/modules/comercial/service.py:818:        unidad_negocio_id: ID de unidad (130MID, CIENFUEGOS, etc.)
/app/backend/modules/comercial/service.py:912:    # FIX: Pasar unidad_negocio_id para filtro más confiable (especialmente para MPRO)
/app/backend/modules/comercial/service.py:1036:# - NUNCA usar aliases legacy (130-MER, 130-QRO, LA-ESTELAR)
/app/backend/modules/comercial/service.py:1037:# - Los códigos canónicos son: 130MID, 130QRO, CIENFUEGOS, ESTELAR, ORIGEN
/app/backend/modules/comercial/service.py:1040:    # SoftRestaurant
/app/backend/modules/comercial/service.py:1041:    "a5547321-1139-4d2b-9d53-182ca737b6b6": {"unidad_negocio_id": "130MID", "nombre": "130° MÉRIDA", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
/app/backend/modules/comercial/service.py:1042:    "6d053c22-523e-48c0-b72b-96081e2d781b": {"unidad_negocio_id": "CIENFUEGOS", "nombre": "CIENFUEGOS", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
/app/backend/modules/comercial/service.py:1043:    "a5ff0e25-f029-43db-b634-d4ac814c904f": {"unidad_negocio_id": "ESTELAR", "nombre": "LA ESTELAR", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
/app/backend/modules/comercial/service.py:1044:    # MPRO (necesitan sucursal específica)
/app/backend/modules/comercial/service.py:1047:            "0021": {"unidad_negocio_id": "130QRO", "nombre": "130° QUERÉTARO"},
/app/backend/modules/comercial/service.py:1048:            "0023": {"unidad_negocio_id": "ORIGEN", "nombre": "ORIGEN"}
/app/backend/modules/comercial/service.py:1050:        "sistema": "MPRO"
/app/backend/modules/comercial/service.py:1210:    if system_type.upper() in ['MPRO', 'MANAGEMENTPRO']:
/app/backend/modules/comercial/service.py:1371:    TABLERO EJECUTIVO - KPIs SoftRestaurant desde EDARSAHUB
/app/backend/modules/comercial/service.py:1402:    nombre = unidad_negocio_nombre or server.get('name', 'SoftRestaurant')
/app/backend/modules/comercial/service.py:1410:    # El mapeo traduce códigos canónicos (130MID) a formatos legacy (130-MER)
/app/backend/modules/comercial/service.py:1501:    TABLERO EJECUTIVO - KPIs MPRO desde EDARSAHUB
/app/backend/modules/comercial/service.py:1509:    NOTA: MPRO tiene múltiples sucursales (0021 = 130° QUERETARO, 0023 = ORIGEN).
/app/backend/modules/comercial/service.py:1516:    nombre = server.get('name', 'MPRO')
/app/backend/modules/comercial/service.py:1518:    # Obtener configuración de unidades MPRO
/app/backend/modules/comercial/service.py:1522:        logging.warning(f"[TABLERO-EDARSAHUB] {nombre}: server_id {server_id} no tiene mapeo de unidad MPRO")
/app/backend/modules/comercial/service.py:1534:    # Agregar KPIs de todas las sucursales MPRO
/app/backend/modules/comercial/service.py:1592:    # FIX PROYECCIÓN MENSUAL MPRO: Usar días transcurridos OPERATIVOS
/app/backend/modules/comercial/service.py:1594:    # REGLA CANÓNICA: Misma que SoftRestaurant
/app/backend/modules/comercial/service.py:1627:        logging.info(f"[PROYECCION-FIX-MPRO] {nombre}: Mes cerrado, días={dias_transcurridos_calc}")
/app/backend/modules/comercial/service.py:1630:        logging.info(f"[PROYECCION-FIX-MPRO] {nombre}: Mes actual, FechaOp={fecha_operacion_actual}, días={dias_transcurridos_calc}")
/app/backend/modules/comercial/service.py:1676:    Query para MPRO que devuelve KPIs DIVIDIDOS POR SUCURSAL (como en Inventarios).
/app/backend/modules/comercial/service.py:1691:    logging.debug(f"MPRO {server['name']}: solo_ventas_dia={solo_ventas_dia}, fecha_ini={fecha_ini}, fecha_fin={fecha_fin}")
/app/backend/modules/comercial/service.py:1700:        logging.info(f"[FIX-P0] MPRO {server['name']}: Modo Ventas del Día - LEYENDO DE EDARSAHUB SQL (NO API local)")
/app/backend/modules/comercial/service.py:1703:        # FASE 5B: Obtener sucursales MPRO desde EmpresaResolver
/app/backend/modules/comercial/service.py:1737:                    "system_type": "MPRO",
/app/backend/modules/comercial/service.py:1767:                    f"[FIX-P0] MPRO {nombre_canonico}: EDARSAHUB SQL OK - "
/app/backend/modules/comercial/service.py:1775:                    "system_type": "MPRO",
/app/backend/modules/comercial/service.py:1804:                    f"[FIX-P0] MPRO {nombre_canonico}: Sin datos en EDARSAHUB SQL - "
/app/backend/modules/comercial/service.py:1815:    # - Para modo HUB (Tablero Ejecutivo), MPRO debe leer de EDARSAHUB SQL
/app/backend/modules/comercial/service.py:1816:    # - NO consultar servidores MPRO directamente (bases QUERETARO, ORIGEN)
/app/backend/modules/comercial/service.py:1817:    # - Usar la misma fuente que SoftRestaurant: Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:1820:    # Las bases MPRO (QUERETARO, ORIGEN) son fuentes de extracción, no de lectura.
/app/backend/modules/comercial/service.py:1823:    logging.info(f"[FIX-HUB] MPRO {server['name']}: Modo Histórico/Acumulado - LEYENDO DE EDARSAHUB SQL (NO bases MPRO)")
/app/backend/modules/comercial/service.py:1825:    # Obtener sucursales MPRO desde EmpresaResolver
/app/backend/modules/comercial/service.py:1843:        # Usar la misma función que SoftRestaurant para leer de EDARSAHUB
/app/backend/modules/comercial/service.py:1861:            kpis['system_type'] = "MPRO"
/app/backend/modules/comercial/service.py:1869:                f"[FIX-HUB] MPRO {nombre_canonico}: EDARSAHUB SQL OK - "
/app/backend/modules/comercial/service.py:1879:                "system_type": "MPRO",
/app/backend/modules/comercial/service.py:1905:                f"[FIX-HUB] MPRO {nombre_canonico}: Sin datos en EDARSAHUB SQL para período {fecha_ini} a {fecha_fin}"
/app/backend/modules/comercial/service.py:1913:        logging.error(f"MPRO {server['name']}: Rango de fechas inválido ({fecha_ini} > {fecha_fin})")
/app/backend/modules/comercial/service.py:1916:    # Formato YYYYMMDD para MPRO (SQL Server con configuración regional español)
/app/backend/modules/comercial/service.py:1920:        logging.error(f"MPRO {server['name']}: Error convirtiendo fechas: {e}")
/app/backend/modules/comercial/service.py:1923:    logging.info(f"[TABLERO] MPRO {server['name']}: Conexión OK - Fechas: {fecha_ini} a {fecha_fin}")
/app/backend/modules/comercial/service.py:1957:            logging.debug(f"MPRO por sucursal {server['name']} - Ultimo dia con ventas: {anio_ultimo}-{mes_ultimo:02d}-{dia_con_datos:02d}")
/app/backend/modules/comercial/service.py:1967:            logging.debug(f"MPRO por sucursal {server['name']} - Período ajustado: {fi} a {ff}, días: {dias_transcurridos}")
/app/backend/modules/comercial/service.py:1996:            logging.info(f"MPRO por sucursal Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
/app/backend/modules/comercial/service.py:1998:        logging.warning(f"MPRO por sucursal Error detectando último día: {e}")
/app/backend/modules/comercial/service.py:2005:    logging.info(f"MPRO {server['name']}: Consultando ventas del {fi} al {ff}")
/app/backend/modules/comercial/service.py:2008:    # ORIGEN ANTERIOR: SQL directo líneas 862-875 (ahora en queries/mpro.py)
/app/backend/modules/comercial/service.py:2015:            f"Error consultando MPRO por sucursal {server['name']}: {result_principal.error} "
/app/backend/modules/comercial/service.py:2021:        logging.warning(f"MPRO {server['name']}: No se encontraron sucursales con ventas")
/app/backend/modules/comercial/service.py:2024:    logging.info(f"MPRO {server['name']}: Query retornó {len(result_principal.sucursales)} sucursales")
/app/backend/modules/comercial/service.py:2039:            logging.info(f"[MPRO] Sucursal no visible omitida: sucursal_origen_id={sucursal_id}, nombre={sucursal_nombre}")
/app/backend/modules/comercial/service.py:2072:                logging.debug(f"MPRO {sucursal_nombre} - Ultimo dia con ventas: dia {dia_suc}")
/app/backend/modules/comercial/service.py:2212:        logging.debug(f"MPRO {sucursal_nombre}: Dia={dia_suc}, Actual={ventas:.2f}, MesAnt({fia_suc}-{ffa_suc})={ventas_ant:.2f} -> {var_vs_mes_ant}%, AnoAnt({fiaa_suc}-{ffaa_suc})={ventas_año:.2f} -> {var_vs_año_ant}%")
/app/backend/modules/comercial/service.py:2227:            "system_type": "MPRO",
/app/backend/modules/comercial/service.py:2252:        logging.info(f"MPRO {server['name']} - Sucursal '{nombre_canonico}' (origen_id={sucursal_id}): Ventas={ventas}, Cheques={cheques}")
/app/backend/modules/comercial/service.py:2268:    FASE 4.4: Obtiene KPIs de MPRO con envelope de estado.
/app/backend/modules/comercial/service.py:2352:# SoftRestaurant. Si la conexión fallaba, mostraba "Sin Datos" aunque EDARSAHUB
/app/backend/modules/comercial/service.py:2378:    NO consulta: Servidores remotos SoftRestaurant
/app/backend/modules/comercial/service.py:2489:    FIX MPRO: Si no encuentra por server_id, intenta buscar por unidad_negocio_id
/app/backend/modules/comercial/service.py:2490:    derivado del nombre del servidor. Esto maneja casos donde los datos MPRO
/app/backend/modules/comercial/service.py:2536:    # FIX MPRO: Buscar por unidad_negocio_id si no encontramos por server_id
/app/backend/modules/comercial/service.py:2538:    # Este fallback maneja el caso donde los datos MPRO en Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:2540:    # corresponde a la unidad correcta (ORIGEN, 130QRO, etc.)
/app/backend/modules/comercial/service.py:2546:        logging.info(f"[DASHBOARD-EDARSAHUB-MPRO-FIX] Intentando búsqueda por unidad_negocio_id: {unidad_ids}")
/app/backend/modules/comercial/service.py:2575:                    f"[DASHBOARD-EDARSAHUB-MPRO-FIX] Datos MPRO encontrados por unidad_negocio_id: "
/app/backend/modules/comercial/service.py:2600:    - ORIGEN LOCAL -> ['ORIGEN']
/app/backend/modules/comercial/service.py:2601:    - 130° QRO LOCAL -> ['130QRO', '130-QRO']
/app/backend/modules/comercial/service.py:2606:        # ORIGEN LOCAL
/app/backend/modules/comercial/service.py:2607:        '817a0aa8-6170-4738-a8f6-a72ac36ba0df': ['ORIGEN'],
/app/backend/modules/comercial/service.py:2609:        '72f6e9a7-8ea2-4eb2-802e-4ee31753435e': ['130QRO', '130-QRO'],
/app/backend/modules/comercial/service.py:2610:        # ManagmentPro (servidor MPRO principal) - no necesita fallback
/app/backend/modules/comercial/cache_service.py:14:entre SoftRestaurant y MPRO.
/app/backend/modules/comercial/cache_service.py:89:    SoftRestaurant y MPRO. Esto garantiza que:
/app/backend/modules/comercial/cache_service.py:90:    - SoftRestaurant NO comparta caché con MPRO
/app/backend/modules/comercial/cache_service.py:91:    - MPRO NO comparta caché con SoftRestaurant
/app/backend/modules/comercial/cache_service.py:92:    - Variantes de system_type (MPRO, ManagmentPro, etc.) se normalicen
/app/backend/modules/comercial/__init__.py:13:- adapters.py: Integración con APIs locales MPRO
/app/backend/modules/comercial/__init__.py:18:- APIS_MPRO_LOCALES (configuración)
/app/backend/modules/comercial/__init__.py:38:    APIS_MPRO_LOCALES,
/app/backend/modules/comercial/__init__.py:71:    # Adapters (APIs locales MPRO)
/app/backend/modules/comercial/__init__.py:72:    'APIS_MPRO_LOCALES',
/app/backend/modules/comercial/queries/__init__.py:17:- softrestaurant.py: Queries base para servidores SoftRestaurant
/app/backend/modules/comercial/queries/__init__.py:18:- mpro.py: Queries base para servidores MPRO
/app/backend/modules/comercial/queries/__init__.py:44:# Bloque 2: Query base de ventas SoftRestaurant
/app/backend/modules/comercial/queries/__init__.py:50:# Bloque 3: Query base de ventas MPRO
/app/backend/modules/comercial/queries/__init__.py:53:    VentasPeriodoResult as VentasPeriodoResultMPRO,
/app/backend/modules/comercial/queries/__init__.py:69:__phase__ = "BLOQUE_3_VENTAS_MPRO"
/app/backend/modules/comercial/queries/mpro.py:2:EDARSA HUB - Queries Base para MPRO (ManagementPro)
/app/backend/modules/comercial/queries/mpro.py:6:Centralizar las queries SQL homologadas para servidores MPRO.
/app/backend/modules/comercial/queries/mpro.py:9:TABLAS PRINCIPALES MPRO:
/app/backend/modules/comercial/queries/mpro.py:61:# Importar EmpresaResolver para resolución canónica de sucursales MPRO
/app/backend/modules/comercial/queries/mpro.py:71:    logging.warning(f"[MPRO] EmpresaResolver no disponible: {e}. Usando fallback.")
/app/backend/modules/comercial/queries/mpro.py:79:# Tablas conocidas de MPRO para validación
/app/backend/modules/comercial/queries/mpro.py:80:MPRO_KNOWN_TABLES = [
/app/backend/modules/comercial/queries/mpro.py:92:MODULE_NAME = "COMERCIAL_QUERIES_MPRO"
/app/backend/modules/comercial/queries/mpro.py:96:# RESULTADO HOMOLOGADO (igual que SoftRestaurant para consistencia)
/app/backend/modules/comercial/queries/mpro.py:124:    Query base ÚNICA de ventas para MPRO.
/app/backend/modules/comercial/queries/mpro.py:126:    ORIGEN: Extraída de service.py líneas 871-884 (get_kpis_mpro_por_sucursal)
/app/backend/modules/comercial/queries/mpro.py:146:    - /comercial/tablero-ejecutivo para servidores MPRO
/app/backend/modules/comercial/queries/mpro.py:163:            error=f"Server {server.get('name')} no es MPRO (es {system_type})"
/app/backend/modules/comercial/queries/mpro.py:245:# FUNCIÓN PARA DASHBOARD MPRO CON FILTRO FLEXIBLE
/app/backend/modules/comercial/queries/mpro.py:256:    Query de ventas MPRO con filtro flexible de sucursal.
/app/backend/modules/comercial/queries/mpro.py:258:    ORIGEN: Extraída de routes.py endpoint /comercial/dashboard/{server_id}
/app/backend/modules/comercial/queries/mpro.py:265:    - Usa la misma lógica que el endpoint dashboard MPRO
/app/backend/modules/comercial/queries/mpro.py:278:    - /comercial/dashboard/{server_id} (sección MPRO)
/app/backend/modules/comercial/queries/mpro.py:296:            error=f"Server {server.get('name')} no es MPRO (es {system_type})"
/app/backend/modules/comercial/queries/mpro.py:338:            logging.info(f"[MPRO] Filtro resuelto por EmpresaResolver: '{sucursal}' -> '{codigo_sucursal_resuelto}'")
/app/backend/modules/comercial/queries/mpro.py:352:                logging.warning(f"[MPRO] Filtro LIKE legacy para '{sucursal}' - considerar agregar alias a EmpresaResolver")
/app/backend/modules/comercial/queries/mpro.py:362:    # QUERY SQL - Basada en routes.py dashboard MPRO
/app/backend/modules/comercial/queries/mpro.py:379:        print(f"*** [MPRO Query] Ejecutando query para {server.get('name')} sucursal={sucursal} ***")
/app/backend/modules/comercial/queries/mpro.py:389:        print(f"*** [MPRO Query] Resultado: {result[:1] if result else 'None/Empty'} ***")
/app/backend/modules/comercial/queries/mpro.py:396:            print(f"*** [MPRO Query] Ventas={ventas:,.2f}, PAX={pax}, Cheques={cheques} ***")
/app/backend/modules/comercial/queries/mpro.py:441:    Convierte fecha ISO (YYYY-MM-DD) a formato SQL con hora para MPRO.
/app/backend/modules/comercial/queries/mpro.py:459:    Construye filtro SQL para sucursal en MPRO.
/app/backend/modules/comercial/queries/mpro.py:475:    FASE 5C HELPER: Resuelve un alias/nombre de sucursal a CodigoSucursalSistema MPRO.
/app/backend/modules/comercial/queries/mpro.py:478:    - Alias de empresa (ORIGEN, QRO, 130-QRO, etc.)
/app/backend/modules/comercial/queries/mpro.py:484:    - ORIGEN → EmpresaID=1 → CodigoSucursalSistema=0023
/app/backend/modules/comercial/queries/mpro.py:485:    - 130QRO → EmpresaID=2 → CodigoSucursalSistema=0021
/app/backend/modules/comercial/queries/mpro.py:512:                logging.debug(f"[MPRO] _resolver_codigo_sucursal_mpro: '{sucursal}' -> EmpresaID={empresa.empresa_id}")
/app/backend/modules/comercial/queries/mpro.py:518:                    logging.info(f"[MPRO] _resolver_codigo_sucursal_mpro: EmpresaID={empresa.empresa_id} -> CodigoSucursal={connection.codigo_sucursal_sistema}")
/app/backend/modules/comercial/queries/mpro.py:524:                    logging.info(f"[MPRO] _resolver_codigo_sucursal_mpro: EmpresaID={empresa.empresa_id} -> CodigoSucursal={connection_api.codigo_sucursal_sistema} (via API_LOCAL)")
/app/backend/modules/comercial/queries/mpro.py:528:            logging.warning(f"[MPRO] Error en _resolver_codigo_sucursal_mpro para '{sucursal}': {e}")
/app/backend/modules/comercial/queries/mpro.py:534:        'ORIGEN': '0023',
/app/backend/modules/comercial/queries/mpro.py:538:        '130QRO': '0021',
/app/backend/modules/comercial/queries/mpro.py:547:        logging.warning(f"[MPRO] _resolver_codigo_sucursal_mpro: Usando fallback hardcodeado para '{sucursal}' -> '{codigo}'")
/app/backend/modules/comercial/queries/mpro.py:559:    Construye filtro SQL flexible para sucursal en MPRO.
/app/backend/modules/comercial/queries/mpro.py:615:    Query base de ventas AGRUPADAS POR SUCURSAL para MPRO.
/app/backend/modules/comercial/queries/mpro.py:617:    ORIGEN: Extraída de service.py líneas 862-884 (get_kpis_mpro_por_sucursal)
/app/backend/modules/comercial/queries/mpro.py:654:            error=f"Server {server.get('name')} no es MPRO (es {system_type})"
/app/backend/modules/comercial/queries/softrestaurant.py:2:EDARSA HUB - Queries Base para SoftRestaurant
/app/backend/modules/comercial/queries/softrestaurant.py:6:Centralizar las queries SQL homologadas para servidores SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:56:# Tablas conocidas de SoftRestaurant para validación
/app/backend/modules/comercial/queries/softrestaurant.py:104:    Query base ÚNICA de ventas para SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:106:    ORIGEN: Extraída de service.py líneas 341-363 (get_kpis_softrestaurant)
/app/backend/modules/comercial/queries/softrestaurant.py:139:            error=f"Server {server.get('name')} no es SoftRestaurant (es {system_type})"
/app/backend/modules/comercial/queries/softrestaurant.py:222:    Convierte fecha ISO (YYYY-MM-DD) a formato SoftRestaurant (YYYYMMDD).
/app/backend/modules/comercial/queries/softrestaurant.py:235:    Construye filtro SQL para sucursal en SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:239:    - La columna idestacion puede no existir en algunas versiones de SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:240:    - Para bases de datos con una sola sucursal (CIENFUEGOS, LA ESTELAR), no aplicar filtro.
/app/backend/modules/comercial/queries/softrestaurant.py:262:    # Esto aplica para CIENFUEGOS, LA ESTELAR, ORIGEN, QUERETARO, MERIDA, ESTELAR, etc.
/app/backend/modules/comercial/queries/softrestaurant.py:263:    # La columna idestacion en SoftRestaurant tiene IDs como '130GRADOSCAJA', no nombres
/app/backend/modules/comercial/adapters.py:25:Adaptadores para integración con APIs locales MPRO.
/app/backend/modules/comercial/adapters.py:57:# CONFIGURACIÓN APIs LOCALES MPRO (FALLBACK LEGACY - SOLO SI EmpresaResolver FALLA)
/app/backend/modules/comercial/adapters.py:62:APIS_MPRO_LOCALES_LEGACY = {
/app/backend/modules/comercial/adapters.py:64:        "nombre": "ORIGEN LOCAL",
/app/backend/modules/comercial/adapters.py:65:        "url": os.environ.get("API_MPRO_ORIGEN_URL", "http://54.39.104.176:8000/query"),
/app/backend/modules/comercial/adapters.py:66:        "api_key": os.environ.get("API_MPRO_KEY", "EDARSA_2026_SECURE_KEY"),
/app/backend/modules/comercial/adapters.py:67:        "empresa_id": 1,  # ORIGEN
/app/backend/modules/comercial/adapters.py:73:        "url": os.environ.get("API_MPRO_QRO_URL", "http://54.39.104.176:8001/query"),
/app/backend/modules/comercial/adapters.py:74:        "api_key": os.environ.get("API_MPRO_KEY", "EDARSA_2026_SECURE_KEY"),
/app/backend/modules/comercial/adapters.py:75:        "empresa_id": 2,  # 130QRO
/app/backend/modules/comercial/adapters.py:82:APIS_MPRO_LOCALES = APIS_MPRO_LOCALES_LEGACY
/app/backend/modules/comercial/adapters.py:90:        alias: Cualquier variante de nombre (130-MER, QRO, LA ESTELAR, etc.)
/app/backend/modules/comercial/adapters.py:149:            if empresa.codigo_empresa == 'ORIGEN':
/app/backend/modules/comercial/adapters.py:150:                api_config["url"] = os.environ.get("API_MPRO_ORIGEN_URL", "http://54.39.104.176:8000/query")
/app/backend/modules/comercial/adapters.py:151:            elif empresa.codigo_empresa == '130QRO':
/app/backend/modules/comercial/adapters.py:152:                api_config["url"] = os.environ.get("API_MPRO_QRO_URL", "http://54.39.104.176:8001/query")
/app/backend/modules/comercial/adapters.py:157:            api_config["api_key"] = os.environ.get("API_MPRO_KEY", "EDARSA_2026_SECURE_KEY")
/app/backend/modules/comercial/adapters.py:170:    Consulta una API MPRO local y retorna los resultados.
/app/backend/modules/comercial/adapters.py:228:    Obtiene las ventas del día actual desde una API MPRO local.
/app/backend/modules/comercial/adapters.py:318:        sucursal_nombre: Nombre o código de la sucursal a buscar (ej: "ORIGEN", "0023", "130-QRO", etc.)
/app/backend/modules/comercial/adapters.py:406:    # ========== FALLBACK LEGACY: Buscar en APIS_MPRO_LOCALES_LEGACY ==========
/app/backend/modules/comercial/adapters.py:408:    print("*** API Local: Intentando fallback legacy (APIS_MPRO_LOCALES_LEGACY) ***")
/app/backend/modules/comercial/adapters.py:415:        "0023": 1,  # ORIGEN
/app/backend/modules/comercial/adapters.py:416:        "0021": 2,  # 130QRO
/app/backend/modules/comercial/adapters.py:417:        "ORIGEN": 1,
/app/backend/modules/comercial/adapters.py:418:        "130QRO": 2,
/app/backend/modules/comercial/adapters.py:437:        for api_id, api_cfg in APIS_MPRO_LOCALES_LEGACY.items():
/app/backend/modules/comercial/adapters.py:475:    'APIS_MPRO_LOCALES',
/app/backend/modules/comercial/inteligencia_comercial_routes.py:10:- No consulta SoftRestaurant/MPRO en vivo desde dashboard.
/app/backend/modules/comercial/inteligencia_comercial_routes.py:51:    NO conecta a SoftRestaurant, MPRO, MongoDB ni sistemas externos.
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:5:Este modulo contiene componentes legacy que pueden consultar fuentes externas, MongoDB, adaptadores MPRO/SoftRestaurant o configuracion de servidores.
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:39:- APIs SoftRestaurant/MPRO desde endpoints ejecutivos.
/app/backend/modules/comercial/routes.py.bak:27:- ✅ Adapters (APIs locales MPRO) migrados a adapters.py
/app/backend/modules/comercial/routes.py.bak:40:   - APIS_MPRO_LOCALES (configuración)
/app/backend/modules/comercial/routes.py.bak:114:# BLOQUE 5.2: Import de query MPRO centralizada con filtro flexible
/app/backend/modules/comercial/routes.py.bak:179:# remotos (SoftRestaurant/MPRO) desde la UI. Los endpoints afectados devolverán
/app/backend/modules/comercial/routes.py.bak:575:                {"id": "cienfuegos", "unidad": "CIENFUEGOS", "ventas": 4130000, "proyeccion": 4410000, "var_vs_mes_ant": 8.8, "var_vs_año_ant": -14.5, "pax": 3177, "cheques": 1052, "cheque_promedio": 3926, "pax_promedio": 1300, "data_status": "DATA_OK"},
/app/backend/modules/comercial/routes.py.bak:578:                {"id": "estelar", "unidad": "LA ESTELAR", "ventas": 2470000, "proyeccion": 2640000, "var_vs_mes_ant": 2.3, "var_vs_año_ant": 0.0, "pax": 4520, "cheques": 1658, "cheque_promedio": 1490, "pax_promedio": 546, "data_status": "DATA_OK"},
/app/backend/modules/comercial/routes.py.bak:579:                {"id": "origen", "unidad": "ORIGEN", "ventas": 2070000, "proyeccion": 2220000, "var_vs_mes_ant": 15.6, "var_vs_año_ant": 16.6, "pax": 2930, "cheques": 1015, "cheque_promedio": 2039, "pax_promedio": 706, "data_status": "DATA_OK"}
/app/backend/modules/comercial/routes.py.bak:994:                        logging.warning(f"[BLINDAJE] Error SoftRestaurant {server['name']}: {sr_error}")
/app/backend/modules/comercial/routes.py.bak:1388:                # FASE P0.5 MPRO: Ventas del Día lee EDARSAHUB SQL (NO API_LOCAL)
/app/backend/modules/comercial/routes.py.bak:1390:                logging.info(f"Procesando servidor MPRO: {server['name']}")
/app/backend/modules/comercial/routes.py.bak:1393:                    # MPRO Ventas del Día: Leer de EDARSAHUB SQL (NO API_LOCAL)
/app/backend/modules/comercial/routes.py.bak:1400:                        if 'ORIGEN' in server_name_upper:
/app/backend/modules/comercial/routes.py.bak:1401:                            unidad_codigo_mpro = 'ORIGEN'
/app/backend/modules/comercial/routes.py.bak:1403:                            unidad_codigo_mpro = '130QRO'
/app/backend/modules/comercial/routes.py.bak:1451:                            logging.info(f"[P0.5-MPRO] {server['name']}: EDARSAHUB SQL = ${total_estimado:,.2f}")
/app/backend/modules/comercial/routes.py.bak:1472:                            logging.warning(f"[P0.5-MPRO] {server['name']}: Sin datos en EDARSAHUB")
/app/backend/modules/comercial/routes.py.bak:1488:                        logging.error(f"[P0.5-MPRO] Error: {mpro_error}")
/app/backend/modules/comercial/routes.py.bak:1499:                            error_code="MPRO_EDARSAHUB_ERROR",
/app/backend/modules/comercial/routes.py.bak:1504:                    # MPRO modo HUB (NO ventas del día)
/app/backend/modules/comercial/routes.py.bak:1510:                        logging.info(f"MPRO {server['name']}: {len(unidades_mpro)} unidades")
/app/backend/modules/comercial/routes.py.bak:1534:                                    source_period_mpro, source_live_mpro = "MPRO_API_LOCAL", "LOCAL_API"
/app/backend/modules/comercial/routes.py.bak:1540:                                    source_period_mpro, source_live_mpro = "MPRO_SQL_DIRECT", "SQL_DIRECT"
/app/backend/modules/comercial/routes.py.bak:1567:                        logging.error(f"[P0-LOG] MPRO error: {server['name']}: {mpro_error}")
/app/backend/modules/comercial/routes.py.bak:1583:                                error_code="MPRO_ERROR",
/app/backend/modules/comercial/routes.py.bak:1584:                                error_message=f"MPRO no disponible: {str(mpro_error)[:100]}",
/app/backend/modules/comercial/routes.py.bak:1590:                                logging.info(f"[P0-LOG] MPRO caché: {len(cached_list)} unidades")
/app/backend/modules/comercial/routes.py.bak:1604:                                        cache_warning="MPRO caída, usando caché",
/app/backend/modules/comercial/routes.py.bak:1622:                                    error_message="Sin datos MPRO",
/app/backend/modules/comercial/routes.py.bak:1674:    # CASO: LA ESTELAR aparecía 2 veces (caché válido + error de conexión)
/app/backend/modules/comercial/routes.py.bak:1686:            # Para SoftRestaurant: 1 unidad por servidor (sucursal_origen_id es NULL)
/app/backend/modules/comercial/routes.py.bak:1687:            # Para MPRO: usar server_id + sucursal_origen_id (ya corregido en P0)
/app/backend/modules/comercial/routes.py.bak:1688:            if sid and not suc:  # SoftRestaurant
/app/backend/modules/comercial/routes.py.bak:1700:        2. Resolver desde EDARSAHUB por server_id (SoftRestaurant)
/app/backend/modules/comercial/routes.py.bak:1809:                    'system_type': snapshot.get('sistema_origen', 'MPRO'),
/app/backend/modules/comercial/routes.py.bak:2109:    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
/app/backend/modules/comercial/routes.py.bak:2211:            # IMPLEMENTACIÓN MPRO (Abril 2026)
/app/backend/modules/comercial/routes.py.bak:2216:            # Filtro de sucursal para MPRO
/app/backend/modules/comercial/routes.py.bak:2218:                'ORIGEN': '0023',
/app/backend/modules/comercial/routes.py.bak:2229:            # NOTA: En MPRO, la tabla Venta tiene Vn_Cantidad_1 y Vn_Precio_Neto_Importe
/app/backend/modules/comercial/routes.py.bak:2263:            # Ventas por vendedor (top 10) - En MPRO usar tabla Vendedor
/app/backend/modules/comercial/routes.py.bak:2455:    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
/app/backend/modules/comercial/routes.py.bak:2488:            # clasificacionventa puede no existir en algunas versiones de SoftRestaurant
/app/backend/modules/comercial/routes.py.bak:2668:        # PROHIBIDO: Abrir conexión a SoftRestaurant/MPRO/Enterprise
/app/backend/modules/comercial/routes.py.bak:3104:            # BLINDAJE: Definir f_fin para MPRO
/app/backend/modules/comercial/routes.py.bak:3107:            # Filtro de sucursal para MPRO - no filtrar si es "default" o nombre del servidor
/app/backend/modules/comercial/routes.py.bak:3120:            # KPIs generales de mesas para MPRO
/app/backend/modules/comercial/routes.py.bak:3159:            # BLINDAJE MPRO: Usar nombre de MongoDB (ya obtenido arriba), con fallback a SQL si no se encontró
/app/backend/modules/comercial/routes.py.bak:3192:            # Rotación por hora para MPRO
/app/backend/modules/comercial/routes.py.bak:3296:            # Formato de fecha para SoftRestaurant (YYYYMMDD)
/app/backend/modules/comercial/routes.py.bak:3395:            # Formato de fecha para MPRO (YYYYMMDD)
/app/backend/modules/comercial/routes.py.bak:3420:            logging.info(f"Detalle MPRO: f_ini={f_ini}, f_fin={f_fin}, sucursal={sucursal}, skip_filter={skip_sucursal_filter}, sucursal_filter={sucursal_filter}")
/app/backend/modules/comercial/routes.py.bak:3422:            # Query para MPRO - usa Venta_Encabezado con Comanda para PAX
/app/backend/modules/comercial/routes.py.bak:3441:            logging.info(f"Query MPRO detalle: {query_detalle[:200]}...")
/app/backend/modules/comercial/routes.py.bak:3573:            # Formato YYYYMMDD para SoftRestaurant - usando CONVERT para evitar errores de conversión
/app/backend/modules/comercial/routes.py.bak:3606:            # NOTA: En SoftRestaurant la tabla de detalle es 'cheqdet' (no 'chequedetalle')
/app/backend/modules/comercial/routes.py.bak:3612:    'SoftRestaurant' as categoria,
/app/backend/modules/comercial/routes.py.bak:3659:                logging.warning(f"Precios Constantes SoftRestaurant {server['name']}: Sin datos en período base {periodo_base}")
/app/backend/modules/comercial/routes.py.bak:3690:            logging.info(f"SoftRestaurant - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
/app/backend/modules/comercial/routes.py.bak:3852:            # Para MPRO - Las ventas están en la tabla 'venta' directamente
/app/backend/modules/comercial/routes.py.bak:3856:            # El frontend envía nombres (ORIGEN, QUERETARO) pero MPRO usa códigos (0023, 0021)
/app/backend/modules/comercial/routes.py.bak:3858:                'ORIGEN': '0023',
/app/backend/modules/comercial/routes.py.bak:3868:                logging.info(f"Precios Constantes MPRO: Traduciendo sucursal '{sucursal}' -> '{sucursal_codigo}'")
/app/backend/modules/comercial/routes.py.bak:3870:            # Filtro de sucursal - en MPRO se relaciona venta con sucursal
/app/backend/modules/comercial/routes.py.bak:3937:                logging.warning(f"Precios Constantes MPRO {server['name']}: Sin datos en período base {periodo_base}")
/app/backend/modules/comercial/routes.py.bak:3967:            logging.info(f"MPRO - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
/app/backend/modules/comercial/routes.py.bak:4403:            # Implementación para MPRO
/app/backend/modules/comercial/routes.py.bak:4406:            # BLINDAJE (Abril 2026): Campo de cancelación en MPRO es Es_Cve_Estado, NO Vn_Cancelacion
/app/backend/modules/comercial/routes.py.bak:4410:                # CORRECCIÓN (Abril 2026): En MPRO, el nombre del vendedor está en tabla Vendedor, NO en Empleado
/app/backend/modules/comercial/routes.py.bak:4528:            # Comparativos para MPRO - helper interno
/app/backend/modules/comercial/routes.py.bak:4625:    Soporta SoftRestaurant y MPRO.
/app/backend/modules/comercial/routes.py.bak:4839:            # PROHIBIDO: Abrir conexión remota a SoftRestaurant para obtener "último día"
/app/backend/modules/comercial/routes.py.bak:4849:            logging.info(f"[NO-LIVE] SoftRestaurant Query - Período: {f_ini} a {f_fin} (EDARSAHUB-ONLY)")
/app/backend/modules/comercial/routes.py.bak:4914:            # PROHIBIDO: Abrir conexión remota a SoftRestaurant/MPRO/Enterprise
/app/backend/modules/comercial/routes.py.bak:4967:            # FASE 7-FIX: EDARSAHUB COMO FUENTE PRINCIPAL PARA MPRO
/app/backend/modules/comercial/routes.py.bak:4969:            # MISMO FIX que SoftRestaurant: Usar EDARSAHUB primero.
/app/backend/modules/comercial/routes.py.bak:4988:                # EDARSAHUB tiene datos MPRO - usar estos como fuente principal
/app/backend/modules/comercial/routes.py.bak:4989:                logging.info(f"[DASHBOARD-FIX-MPRO] {server['name']}: Usando datos de EDARSAHUB (ventas=${edarsahub_kpis_mpro['ventas_periodo']:,.2f})")
/app/backend/modules/comercial/routes.py.bak:5023:            # FASE 1B-R1: CORRECCIÓN NO-LIVE DASHBOARD MPRO
/app/backend/modules/comercial/routes.py.bak:5025:            # PROHIBIDO: Abrir conexión remota a MPRO/Enterprise
/app/backend/modules/comercial/routes.py.bak:5028:            logging.warning(f"[DASHBOARD-NO-LIVE-MPRO] {server['name']}: EDARSAHUB sin datos vigentes, verificando snapshot histórico")
/app/backend/modules/comercial/routes.py.bak:5037:                logging.info(f"[DASHBOARD-NO-LIVE-MPRO] {server['name']}: Retornando datos STALE de {stale_snapshot_mpro['fecha_snapshot']}")
/app/backend/modules/comercial/routes.py.bak:5057:            logging.warning(f"[DASHBOARD-NO-LIVE-MPRO] {server['name']}: Sin datos en EDARSAHUB, retornando SIN_DATOS_EDARSAHUB")
/app/backend/modules/comercial/routes.py.bak:5113:    if "CIENFUEGOS" in clean_id:
/app/backend/modules/comercial/routes.py.bak:5115:    elif any(x in clean_id for x in ["MERIDA", "130MID", "MID"]):
/app/backend/modules/comercial/routes.py.bak:5117:    elif any(x in clean_id for x in ["QUERETARO", "130QRO", "QRO"]):
/app/backend/modules/comercial/routes.py.bak:5119:    elif "ESTELAR" in clean_id:
/app/backend/modules/comercial/routes.py.bak:5121:    elif "ORIGEN" in clean_id:
/app/backend/modules/comercial/routes_competidores_enterprise.py:2:FASE 1C-3I-B v2: Endpoints Enterprise de Competidores por Unidad de Negocio
/app/backend/modules/comercial/routes_competidores_enterprise.py:32:router = APIRouter(prefix="/comercial", tags=["Competidores Enterprise"])
/app/backend/modules/comercial/repository.py:128:        'visible_en_operaciones': bool(row.get('visible_en_operaciones', True)),
/app/backend/modules/comercial/repository.py:182:          AND (visible_en_operaciones = 1 OR visible_en_operaciones IS NULL)
/app/backend/modules/comercial/repository.py:230:        Dict con {sucursal_nombre: visible_en_operaciones}
/app/backend/modules/comercial/repository.py:258:    - Si SÍ hay configuración -> devuelve solo las marcadas como visible_en_operaciones=True
/app/backend/modules/comercial/repository.py:292:        # Construir condición para sucursal_origen_id (puede ser NULL para SoftRestaurant)
/app/backend/modules/comercial/repository.py:296:            # Para SoftRestaurant sin código, buscar por server_id con sucursal_origen_id NULL
/app/backend/modules/comercial/repository.py:361:# QUERIES SQL - VENTAS MPRO
/app/backend/modules/comercial/repository.py:366:    Obtiene ventas de MPRO para un mes/año específico.
/app/backend/modules/comercial/repository.py:392:    Obtiene ventas de SoftRestaurant para un mes/año específico.
/app/backend/modules/comercial/repository.py:425:    Obtiene datos de ticket perfecto para MPRO.
/app/backend/modules/comercial/README_BLINDAJE.md:28:| SoftRestaurant | SQL (cheques+turnos) | SQL (tempcheques) |
/app/backend/modules/comercial/README_BLINDAJE.md:29:| MPRO | SQL (Venta_Encabezado) | API local |
/app/backend/modules/comercial/services/competidores_enterprise_service.py:2:FASE 1C-3I-B v2: Servicio Enterprise de Competidores por Unidad de Negocio
/app/backend/modules/comercial/routes.py:27:- ✅ Adapters (APIs locales MPRO) migrados a adapters.py
/app/backend/modules/comercial/routes.py:40:   - APIS_MPRO_LOCALES (configuración)
/app/backend/modules/comercial/routes.py:114:# BLOQUE 5.2: Import de query MPRO centralizada con filtro flexible
/app/backend/modules/comercial/routes.py:179:# remotos (SoftRestaurant/MPRO) desde la UI. Los endpoints afectados devolverán
/app/backend/modules/comercial/routes.py:575:                {"id": "cienfuegos", "unidad": "CIENFUEGOS", "ventas": 4130000, "proyeccion": 4410000, "var_vs_mes_ant": 8.8, "var_vs_año_ant": -14.5, "pax": 3177, "cheques": 1052, "cheque_promedio": 3926, "pax_promedio": 1300, "data_status": "DATA_OK"},
/app/backend/modules/comercial/routes.py:578:                {"id": "estelar", "unidad": "LA ESTELAR", "ventas": 2470000, "proyeccion": 2640000, "var_vs_mes_ant": 2.3, "var_vs_año_ant": 0.0, "pax": 4520, "cheques": 1658, "cheque_promedio": 1490, "pax_promedio": 546, "data_status": "DATA_OK"},
/app/backend/modules/comercial/routes.py:579:                {"id": "origen", "unidad": "ORIGEN", "ventas": 2070000, "proyeccion": 2220000, "var_vs_mes_ant": 15.6, "var_vs_año_ant": 16.6, "pax": 2930, "cheques": 1015, "cheque_promedio": 2039, "pax_promedio": 706, "data_status": "DATA_OK"}
/app/backend/modules/comercial/routes.py:994:                        logging.warning(f"[BLINDAJE] Error SoftRestaurant {server['name']}: {sr_error}")
/app/backend/modules/comercial/routes.py:1388:                # FASE P0.5 MPRO: Ventas del Día lee EDARSAHUB SQL (NO API_LOCAL)
/app/backend/modules/comercial/routes.py:1390:                logging.info(f"Procesando servidor MPRO: {server['name']}")
/app/backend/modules/comercial/routes.py:1393:                    # MPRO Ventas del Día: Leer de EDARSAHUB SQL (NO API_LOCAL)
/app/backend/modules/comercial/routes.py:1400:                        if 'ORIGEN' in server_name_upper:
/app/backend/modules/comercial/routes.py:1401:                            unidad_codigo_mpro = 'ORIGEN'
/app/backend/modules/comercial/routes.py:1403:                            unidad_codigo_mpro = '130QRO'
/app/backend/modules/comercial/routes.py:1451:                            logging.info(f"[P0.5-MPRO] {server['name']}: EDARSAHUB SQL = ${total_estimado:,.2f}")
/app/backend/modules/comercial/routes.py:1472:                            logging.warning(f"[P0.5-MPRO] {server['name']}: Sin datos en EDARSAHUB")
/app/backend/modules/comercial/routes.py:1488:                        logging.error(f"[P0.5-MPRO] Error: {mpro_error}")
/app/backend/modules/comercial/routes.py:1499:                            error_code="MPRO_EDARSAHUB_ERROR",
/app/backend/modules/comercial/routes.py:1504:                    # MPRO modo HUB (NO ventas del día)
/app/backend/modules/comercial/routes.py:1510:                        logging.info(f"MPRO {server['name']}: {len(unidades_mpro)} unidades")
/app/backend/modules/comercial/routes.py:1534:                                    source_period_mpro, source_live_mpro = "MPRO_API_LOCAL", "LOCAL_API"
/app/backend/modules/comercial/routes.py:1540:                                    source_period_mpro, source_live_mpro = "MPRO_SQL_DIRECT", "SQL_DIRECT"
/app/backend/modules/comercial/routes.py:1567:                        logging.error(f"[P0-LOG] MPRO error: {server['name']}: {mpro_error}")
/app/backend/modules/comercial/routes.py:1583:                                error_code="MPRO_ERROR",
/app/backend/modules/comercial/routes.py:1584:                                error_message=f"MPRO no disponible: {str(mpro_error)[:100]}",
/app/backend/modules/comercial/routes.py:1590:                                logging.info(f"[P0-LOG] MPRO caché: {len(cached_list)} unidades")
/app/backend/modules/comercial/routes.py:1604:                                        cache_warning="MPRO caída, usando caché",
/app/backend/modules/comercial/routes.py:1622:                                    error_message="Sin datos MPRO",
/app/backend/modules/comercial/routes.py:1674:    # CASO: LA ESTELAR aparecía 2 veces (caché válido + error de conexión)
/app/backend/modules/comercial/routes.py:1686:            # Para SoftRestaurant: 1 unidad por servidor (sucursal_origen_id es NULL)
/app/backend/modules/comercial/routes.py:1687:            # Para MPRO: usar server_id + sucursal_origen_id (ya corregido en P0)
/app/backend/modules/comercial/routes.py:1688:            if sid and not suc:  # SoftRestaurant
/app/backend/modules/comercial/routes.py:1700:        2. Resolver desde EDARSAHUB por server_id (SoftRestaurant)
/app/backend/modules/comercial/routes.py:1809:                    'system_type': snapshot.get('sistema_origen', 'MPRO'),
/app/backend/modules/comercial/routes.py:2109:    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
/app/backend/modules/comercial/routes.py:2211:            # IMPLEMENTACIÓN MPRO (Abril 2026)
/app/backend/modules/comercial/routes.py:2216:            # Filtro de sucursal para MPRO
/app/backend/modules/comercial/routes.py:2218:                'ORIGEN': '0023',
/app/backend/modules/comercial/routes.py:2229:            # NOTA: En MPRO, la tabla Venta tiene Vn_Cantidad_1 y Vn_Precio_Neto_Importe
/app/backend/modules/comercial/routes.py:2263:            # Ventas por vendedor (top 10) - En MPRO usar tabla Vendedor
/app/backend/modules/comercial/routes.py:2455:    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
/app/backend/modules/comercial/routes.py:2488:            # clasificacionventa puede no existir en algunas versiones de SoftRestaurant
/app/backend/modules/comercial/routes.py:2668:        # PROHIBIDO: Abrir conexión a SoftRestaurant/MPRO/Enterprise
/app/backend/modules/comercial/routes.py:3104:            # BLINDAJE: Definir f_fin para MPRO
/app/backend/modules/comercial/routes.py:3107:            # Filtro de sucursal para MPRO - no filtrar si es "default" o nombre del servidor
/app/backend/modules/comercial/routes.py:3120:            # KPIs generales de mesas para MPRO
/app/backend/modules/comercial/routes.py:3159:            # BLINDAJE MPRO: Usar nombre de MongoDB (ya obtenido arriba), con fallback a SQL si no se encontró
/app/backend/modules/comercial/routes.py:3192:            # Rotación por hora para MPRO
/app/backend/modules/comercial/routes.py:3296:            # Formato de fecha para SoftRestaurant (YYYYMMDD)
/app/backend/modules/comercial/routes.py:3395:            # Formato de fecha para MPRO (YYYYMMDD)
/app/backend/modules/comercial/routes.py:3420:            logging.info(f"Detalle MPRO: f_ini={f_ini}, f_fin={f_fin}, sucursal={sucursal}, skip_filter={skip_sucursal_filter}, sucursal_filter={sucursal_filter}")
/app/backend/modules/comercial/routes.py:3422:            # Query para MPRO - usa Venta_Encabezado con Comanda para PAX
/app/backend/modules/comercial/routes.py:3441:            logging.info(f"Query MPRO detalle: {query_detalle[:200]}...")
/app/backend/modules/comercial/routes.py:3573:            # Formato YYYYMMDD para SoftRestaurant - usando CONVERT para evitar errores de conversión
/app/backend/modules/comercial/routes.py:3606:            # NOTA: En SoftRestaurant la tabla de detalle es 'cheqdet' (no 'chequedetalle')
/app/backend/modules/comercial/routes.py:3612:    'SoftRestaurant' as categoria,
/app/backend/modules/comercial/routes.py:3659:                logging.warning(f"Precios Constantes SoftRestaurant {server['name']}: Sin datos en período base {periodo_base}")
/app/backend/modules/comercial/routes.py:3690:            logging.info(f"SoftRestaurant - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
/app/backend/modules/comercial/routes.py:3852:            # Para MPRO - Las ventas están en la tabla 'venta' directamente
/app/backend/modules/comercial/routes.py:3856:            # El frontend envía nombres (ORIGEN, QUERETARO) pero MPRO usa códigos (0023, 0021)
/app/backend/modules/comercial/routes.py:3858:                'ORIGEN': '0023',
/app/backend/modules/comercial/routes.py:3868:                logging.info(f"Precios Constantes MPRO: Traduciendo sucursal '{sucursal}' -> '{sucursal_codigo}'")
/app/backend/modules/comercial/routes.py:3870:            # Filtro de sucursal - en MPRO se relaciona venta con sucursal
/app/backend/modules/comercial/routes.py:3937:                logging.warning(f"Precios Constantes MPRO {server['name']}: Sin datos en período base {periodo_base}")
/app/backend/modules/comercial/routes.py:3967:            logging.info(f"MPRO - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
/app/backend/modules/comercial/routes.py:4236:    Soporta SoftRestaurant y MPRO.
/app/backend/modules/comercial/routes.py:4450:            # PROHIBIDO: Abrir conexión remota a SoftRestaurant para obtener "último día"
/app/backend/modules/comercial/routes.py:4460:            logging.info(f"[NO-LIVE] SoftRestaurant Query - Período: {f_ini} a {f_fin} (EDARSAHUB-ONLY)")
/app/backend/modules/comercial/routes.py:4525:            # PROHIBIDO: Abrir conexión remota a SoftRestaurant/MPRO/Enterprise
/app/backend/modules/comercial/routes.py:4578:            # FASE 7-FIX: EDARSAHUB COMO FUENTE PRINCIPAL PARA MPRO
/app/backend/modules/comercial/routes.py:4580:            # MISMO FIX que SoftRestaurant: Usar EDARSAHUB primero.
/app/backend/modules/comercial/routes.py:4599:                # EDARSAHUB tiene datos MPRO - usar estos como fuente principal
/app/backend/modules/comercial/routes.py:4600:                logging.info(f"[DASHBOARD-FIX-MPRO] {server['name']}: Usando datos de EDARSAHUB (ventas=${edarsahub_kpis_mpro['ventas_periodo']:,.2f})")
/app/backend/modules/comercial/routes.py:4634:            # FASE 1B-R1: CORRECCIÓN NO-LIVE DASHBOARD MPRO
/app/backend/modules/comercial/routes.py:4636:            # PROHIBIDO: Abrir conexión remota a MPRO/Enterprise
/app/backend/modules/comercial/routes.py:4639:            logging.warning(f"[DASHBOARD-NO-LIVE-MPRO] {server['name']}: EDARSAHUB sin datos vigentes, verificando snapshot histórico")
/app/backend/modules/comercial/routes.py:4648:                logging.info(f"[DASHBOARD-NO-LIVE-MPRO] {server['name']}: Retornando datos STALE de {stale_snapshot_mpro['fecha_snapshot']}")
/app/backend/modules/comercial/routes.py:4668:            logging.warning(f"[DASHBOARD-NO-LIVE-MPRO] {server['name']}: Sin datos en EDARSAHUB, retornando SIN_DATOS_EDARSAHUB")
/app/backend/modules/comercial/routes.py:4724:    if "CIENFUEGOS" in clean_id:
/app/backend/modules/comercial/routes.py:4726:    elif any(x in clean_id for x in ["MERIDA", "130MID", "MID"]):
/app/backend/modules/comercial/routes.py:4728:    elif any(x in clean_id for x in ["QUERETARO", "130QRO", "QRO"]):
/app/backend/modules/comercial/routes.py:4730:    elif "ESTELAR" in clean_id:
/app/backend/modules/comercial/routes.py:4732:    elif "ORIGEN" in clean_id:
/app/backend/modules/fase2_operativo/schemas/justificacion_schemas.py:94:    cantidad_mpro: float = Field(..., description="Cantidad en MPRO")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:107:        origen_sistema: str = "MPRO",
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:40:    origen_sistema: Optional[str] = "MPRO"
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:427:        origen_sistema=request.origen_sistema or "MPRO"
/app/backend/modules/api_connections/__init__.py:4:Gestiona conexiones a APIs locales (MPRO, etc.) para obtener ventas del día
/app/backend/modules/api_connections/repository.py:129:        'tipo': row.get('system_type', 'MPRO'),
/app/backend/modules/api_connections/repository.py:137:        'visible_en_operaciones': bool(row.get('visible_en_operaciones', False)),
/app/backend/modules/api_connections/repository.py:290:        api_url, api_key_encrypted, activo, visible_en_operaciones,
/app/backend/modules/api_connections/repository.py:297:        N'{_escape_sql(data.get("tipo", "MPRO"))}',
/app/backend/modules/api_connections/repository.py:305:        {1 if data.get("visible_en_operaciones", False) else 0},
/app/backend/modules/api_connections/repository.py:394:    if 'visible_en_operaciones' in data:
/app/backend/modules/api_connections/repository.py:395:        set_parts.append(f"visible_en_operaciones = {1 if data['visible_en_operaciones'] else 0}")
/app/backend/modules/api_connections/repository.py:508:            'visible_en_operaciones': api['visible_en_operaciones'],
/app/backend/modules/api_connections/repository.py:661:            'tipo': row.get('system_type', 'MPRO'),
/app/backend/modules/api_connections/routes.py:43:    tipo: str = Field("MPRO", description="Tipo de sistema (MPRO, SoftRestaurant)")
/app/backend/modules/api_connections/routes.py:50:    visible_en_operaciones: bool = Field(False, description="Visible en módulo Operaciones")
/app/backend/modules/api_connections/routes.py:64:    visible_en_operaciones: Optional[bool] = None
/app/backend/modules/api_connections/universal_test_routes.py:155:                   activo, EmpresaID, visible_en_operaciones
/app/backend/modules/costos_margenes/routes_precios.py:564:    La modificación real del precio en sistema origen (SoftRestaurant/MPRO)
/app/backend/modules/costos_margenes/routes.py:226:    sistema_origen: Optional[str] = Query(None, description="Filtrar por sistema (SOFTRESTAURANT_PRO, MPRO)"),
/app/backend/modules/costos_margenes/routes.py:254:    - sistema_origen (SOFTRESTAURANT_PRO, MPRO)
/app/backend/modules/costos_margenes/routes.py:671:    sistema: Optional[str] = Query(None, description="Filtrar por sistema (SOFTRESTAURANT_PRO, MPRO)"),
/app/backend/modules/rh/service.py:49:-- Compatible con: NomiPAQ, MPRO, Excel
/app/backend/modules/rh/service.py:61:IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'RH_Cat_Puestos' AND COLUMN_NAME = 'MPRO_ID')
/app/backend/modules/rh/service.py:63:    ALTER TABLE RH_Cat_Puestos ADD MPRO_ID NVARCHAR(50) NULL;
/app/backend/modules/rh/service.py:64:    PRINT 'Columna MPRO_ID agregada a RH_Cat_Puestos';
/app/backend/modules/rh/service.py:92:        MPRO_ID NVARCHAR(50) NULL,  -- ID en MPRO
/app/backend/modules/rh/service.py:153:    ALTER TABLE RH_Incidencias_Nomina ADD Origen_Sistema NVARCHAR(20) DEFAULT 'EDARSA_HUB';  -- EDARSA_HUB, NomiPAQ, MPRO, Excel
/app/backend/modules/rh/service.py:165:        Sistema_Origen NVARCHAR(20) NOT NULL,  -- NomiPAQ, MPRO, Excel
/app/backend/modules/rh/service.py:195:PRINT 'Las tablas están listas para importar datos de NomiPAQ, MPRO o Excel';
/app/backend/modules/rh/service.py:389:                "   - Importar datos desde MPRO",
/app/backend/modules/rh/service.py:395:                "mpro": "Campos MPRO_ID en todas las tablas para vincular registros",
/app/backend/modules/rh/repository.py:247:        (Descripcion, Departamento, Sueldo_Base_Seman_SBC, NomiPAQ_ID, MPRO_ID, Fecha_Creacion, Creado_Por)
/app/backend/modules/rh/repository.py:295:        set_clauses.append(f"MPRO_ID = N'{val}'")
/app/backend/modules/rh/repository.py:401:            MPRO_ID
/app/backend/modules/rh/repository.py:449:        (Codigo, Descripcion, Categoria, Afectacion, Calculo_Monto, Activo, NomiPAQ_ID, MPRO_ID, Fecha_Creacion, Creado_Por)
/app/backend/modules/rh/repository.py:499:        set_clauses.append(f"MPRO_ID = N'{val}'")
/app/backend/modules/rh/routes.py:296:    Incluye instrucciones de uso y compatibilidad con NomiPAQ, MPRO y Excel.
/app/backend/modules/rh/schemas.py:31:    mpro_id: str = Field(default="", max_length=50, description="ID de mapeo con MPRO")
/app/backend/modules/rh/schemas.py:112:    mpro_id: str = Field(default="", max_length=50, description="ID de mapeo con MPRO")
/app/backend/modules/rh/schemas.py:178:    MPRO_ID: Optional[str] = None
/app/backend/modules/configuracion/services/almacenes_sync_service.py:6:Sincroniza almacenes desde sistemas origen (SoftRestaurant/MPRO) al catálogo local MongoDB.
/app/backend/modules/configuracion/services/almacenes_sync_service.py:30:from modules.automatizacion.queries_mpro import QUERY_ALMACENES_SUCURSAL as QUERY_ALMACENES_MPRO
/app/backend/modules/configuracion/services/almacenes_sync_service.py:152:        if system_type == "SoftRestaurant":
/app/backend/modules/configuracion/services/almacenes_sync_service.py:154:        elif system_type == "MPRO":
/app/backend/modules/configuracion/services/almacenes_sync_service.py:157:                result.error_message = "MPRO requiere sucursal_origen_id configurado"
/app/backend/modules/configuracion/services/almacenes_sync_service.py:160:            # Reemplazar parámetro en query MPRO
/app/backend/modules/configuracion/services/almacenes_sync_service.py:161:            query = QUERY_ALMACENES_MPRO.replace(":sucursal_id", f"'{sucursal_origen_id}'")
/app/backend/modules/configuracion/services/almacenes_sync_service.py:208:            if system_type == "SoftRestaurant":
/app/backend/modules/configuracion/services/almacenes_sync_service.py:211:            else:  # MPRO
/app/backend/modules/consultas_sql/service.py:69:            sistema: 'SOFTRESTAURANT', 'MPRO' o None para todos
/app/backend/modules/consultas_sql/service.py:340:            'sistemas': ['SOFTRESTAURANT', 'MPRO'],
/app/backend/modules/consultas_sql/service.py:375:                    'tipo': 'CONFIG_ORIGEN_VACIO',
/app/backend/modules/consultas_sql/validator.py:353:                code="CATALOG_NO_ORIGEN",
/app/backend/modules/consultas_sql/repository.py:105:                'MPRO': 2,
/app/backend/modules/consultas_sql/routes.py:147:    sistema: Optional[str] = Query(None, description="Sistema: SOFTRESTAURANT, MPRO"),
/app/backend/modules/consultas_sql/routes.py:429:                WHEN 2 THEN 'MPRO'
/app/backend/modules/consultas_sql/routes.py:889:    - MPRO (SistemaTipoID=2)
/app/backend/modules/consultas_sql/routes.py:900:                nombre="SoftRestaurant Pro",
/app/backend/modules/consultas_sql/routes.py:905:                codigo="MPRO",
/app/backend/modules/consultas_sql/models.py:12:TABLAS ORIGEN:
/app/backend/modules/consultas_sql/models.py:332:            2: "MPRO",
/app/backend/modules/consultas_sql/models.py:342:    codigo_sistema: Optional[str] = None  # 'SOFTRESTAURANT', 'MPRO'
/app/backend/modules/consultas_sql/schemas.py:23:    sistema: Optional[str] = Field(None, description="Sistema: SOFTRESTAURANT, MPRO")
/app/backend/modules/inteligencia_comercial/routes.py:13:- 130MID (130° MERIDA)
/app/backend/modules/inteligencia_comercial/routes.py:14:- 130QRO (130° QUERETARO)
/app/backend/modules/inteligencia_comercial/routes.py:15:- CIENFUEGOS
/app/backend/modules/inteligencia_comercial/routes.py:16:- ESTELAR (LA ESTELAR)
/app/backend/modules/inteligencia_comercial/routes.py:17:- ORIGEN
/app/backend/modules/inteligencia_comercial/routes.py:53:    "cienfuegos": "CIENFUEGOS",
/app/backend/modules/inteligencia_comercial/routes.py:54:    "estelar": "LA ESTELAR",
/app/backend/modules/inteligencia_comercial/routes.py:55:    "laestelar": "LA ESTELAR",
/app/backend/modules/inteligencia_comercial/routes.py:56:    "origen": "ORIGEN",
/app/backend/modules/inteligencia_comercial/routes.py:63:    "CIENFUEGOS": "CIENFUEGOS",
/app/backend/modules/inteligencia_comercial/routes.py:64:    "LA ESTELAR": "LA ESTELAR",
/app/backend/modules/inteligencia_comercial/routes.py:65:    "ORIGEN": "ORIGEN",
/app/backend/modules/inteligencia_comercial/routes.py:114:    unidad: Optional[str] = Query(None, description="Unidad de negocio (130MID, CIENFUEGOS, etc.)"),
```
