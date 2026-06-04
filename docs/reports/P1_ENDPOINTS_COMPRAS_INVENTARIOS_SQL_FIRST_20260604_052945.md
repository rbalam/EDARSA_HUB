# P1 - ENDPOINTS COMPRAS / INVENTARIOS A MIGRAR SQL-FIRST
Fecha: Thu Jun  4 05:29:45 UTC 2026

## 1. Endpoints críticos en server.py
```text
3364:@api_router.get("/inventarios/pendientes/{server_id}")
7082:# - GET /compras/inventarios-fisicos/{server_id}
7083:# - GET /compras/pedidos-vigentes/{server_id}  
7086:# - GET /compras/detalle-pedido/{server_id}/{folio}
7087:# - GET /compras/detalle-pedido-manual/{server_id}
7088:# - GET /compras/detalle-movimientos/{server_id}
7089:# - GET /compras/detalle-consumos/{server_id}
7090:# - POST /compras/calculo-pedido (~420 líneas)
7091:# - POST /compras/productos-para-captura
7092:# - POST /compras/auditoria-operativa (~710 líneas)
7093:# - POST /compras/detalle-movimientos
7094:# - POST /compras/detalle-consumos
7164:@api_router.get("/compras/inventarios-fisicos/{server_id}")
7285:            log_compras_error("inventarios-fisicos", server_id, "CONNECTION_ERROR", error_msg[:200], server.get('system_type'))
7317:            log_compras_error("inventarios-fisicos", server_id, "QUERY_ERROR", str(e), server.get('system_type'))
7322:    log_compras_error("inventarios-fisicos", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
7325:@api_router.get("/compras/pedidos-vigentes/{server_id}")
7420:            log_compras_error("pedidos-vigentes", server_id, "CONNECTION_ERROR", error_msg[:200], server.get('system_type'))
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
10255:# ENDPOINT /comercial/detalle-movimientos - MIGRADO A modules/comercial/routes.py
```

## 2. Bloques de código con execute_sql_query en server.py relacionados con compras/inventarios
```text
1243:#   - execute_sql_query()
1257:    execute_sql_query,
1645:    from core.server_registry import get_server_by_id as registry_get_server
1680:    from core.server_registry import update_server as registry_update_server, get_server_by_id
1683:    existing = await get_server_by_id(server_id, db=db, mask_secrets=False)
1738:    from core.server_registry import delete_server as registry_delete_server, get_server_by_id
1741:    existing = await get_server_by_id(server_id, db=db, mask_secrets=True)
1805:        result = execute_sql_query(
1806:            server['host'], server['port'], server['database'],
2042:        results = execute_sql_query(
2043:            server['host'],
2045:            server['database'],
2113:    from core.server_registry import get_server_connection_info_with_secrets, update_server as registry_update_server, get_server_by_id
2154:    updated_server = await get_server_by_id(server_id, db=db, mask_secrets=True)
2190:    from core.server_registry import get_server_by_id
2194:    server = await get_server_by_id(server_id, db=db, mask_secrets=True)
2423:    from core.server_registry import get_server_by_id
2426:    server = await get_server_by_id(server_id, db=db)
2460:    from core.server_registry import get_server_by_id
2463:    server = await get_server_by_id(server_id, db=db)
2586:                results = execute_sql_query(
2587:                    server['host'],
2589:                    server['database'],
2604:                    almacenes = execute_sql_query(
2605:                        server['host'],
2607:                        server['database'],
2628:                results = execute_sql_query(
2629:                    server['host'],
2631:                    server['database'],
2696:        # FASE 1B: Importar execute_sql_query_params para parametrización segura
2697:        from core.db import execute_sql_query_params
2712:                results = execute_sql_query_params(
2713:                    server['host'], server['port'], server['database'],
2718:                results = execute_sql_query(
2719:                    server['host'], server['port'], server['database'],
2738:            results = execute_sql_query(
2739:                server['host'], server['port'], server['database'],
2751:                results = execute_sql_query_params(
2752:                    server['host'], server['port'], server['database'],
2757:                results = execute_sql_query(
2758:                    server['host'], server['port'], server['database'],
2835:            sucursales_sql = execute_sql_query(
2836:                server['host'], server['port'], server['database'],
3058:    from core.db import execute_sql_query
3086:        unidades_sql = execute_sql_query(
3234:        results = execute_sql_query(
3235:            server['host'],
3237:            server['database'],
3347:        results = execute_sql_query(
3348:            server['host'],
3350:            server['database'],
3512:        results = execute_sql_query(
3513:            server['host'],
3515:            server['database'],
3639:    results = execute_sql_query(
3640:        server['host'],
3642:        server['database'],
3683:            categorias = execute_sql_query(
3684:                server['host'], server['port'], server['database'],
3695:            familias = execute_sql_query(
3696:                server['host'], server['port'], server['database'],
3707:            subfamilias = execute_sql_query(
3708:                server['host'], server['port'], server['database'],
3739:            familias = execute_sql_query(
3740:                server['host'], server['port'], server['database'],
3752:            subfamilias = execute_sql_query(
3753:                server['host'], server['port'], server['database'],
3936:                    fecha_result = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], fecha_folio_query)
3949:                    fecha_result = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], fecha_folio_query)
3983:            almacen_result = execute_sql_query(
3984:                server['host'], server['port'], server['database'],
4070:            productos = execute_sql_query(
4071:                server['host'], server['port'], server['database'],
4116:                ventas_result = execute_sql_query(
4117:                    server['host'], server['port'], server['database'],
4161:            movimientos_result = execute_sql_query(
4162:                server['host'], server['port'], server['database'],
4185:            errores_result = execute_sql_query(
4186:                server['host'], server['port'], server['database'],
4275:                inv_detalle = execute_sql_query(
4276:                    server['host'], server['port'], server['database'],
4513:            fechas_result = execute_sql_query(
4514:                server['host'], server['port'], server['database'],
4580:            almacen_result = execute_sql_query(
4581:                server['host'], server['port'], server['database'],
4585:                logging.error(f"Almacén '{almacen}' no encontrado en servidor {server.get('name', server_id)} ({server['host']})")
4673:            productos_result = execute_sql_query(
4674:                server['host'], server['port'], server['database'],
4720:            inventarios_result = execute_sql_query(
4721:                server['host'], server['port'], server['database'],
4835:                movimientos_result = execute_sql_query(
4836:                    server['host'], server['port'], server['database'],
4904:                    ventas_result = execute_sql_query(
4905:                        server['host'], server['port'], server['database'],
4944:                    ventas_temp_result = execute_sql_query(
4945:                        server['host'], server['port'], server['database'],
5195:            almacen_result = execute_sql_query(
5196:                server['host'], server['port'], server['database'],
5261:            result = execute_sql_query(
5262:                server['host'], server['port'], server['database'],
5340:            result = execute_sql_query(
5341:                server['host'], server['port'], server['database'],
5372:                result = execute_sql_query(
5373:                    server['host'], server['port'], server['database'],
5481:            result = execute_sql_query(
5482:                server['host'], server['port'], server['database'],
5550:            result = execute_sql_query(
5551:                server['host'], server['port'], server['database'],
5696:        cortes_result = execute_sql_query(
5697:            server['host'], server['port'], server['database'],
6296:        results = execute_sql_query(
6297:            server['host'],
6299:            server['database'],
6353:        results = execute_sql_query(
6399:        results = execute_sql_query(host, port, database, username, password, query)
6453:        results = execute_sql_query(
6454:            server['host'],
6456:            server['database'],
6508:            almacen_result = execute_sql_query(
6533:        mov_result = execute_sql_query(
6568:        ventas_result = execute_sql_query(
6595:        detalle = execute_sql_query(
6615:        detalle_kit = execute_sql_query(
6633:        detalle_directas = execute_sql_query(
6850:            results = execute_sql_query(
6851:                server['host'],
6853:                server['database'],
7082:# - GET /compras/inventarios-fisicos/{server_id}
7083:# - GET /compras/pedidos-vigentes/{server_id}  
7086:# - GET /compras/detalle-pedido/{server_id}/{folio}
7087:# - GET /compras/detalle-pedido-manual/{server_id}
7088:# - GET /compras/detalle-movimientos/{server_id}
7089:# - GET /compras/detalle-consumos/{server_id}
7090:# - POST /compras/calculo-pedido (~420 líneas)
7091:# - POST /compras/productos-para-captura
7093:# - POST /compras/detalle-movimientos
7094:# - POST /compras/detalle-consumos
7164:@api_router.get("/compras/inventarios-fisicos/{server_id}")
7274:            result = execute_sql_query(
7275:                server['host'], server['port'], server['database'],
7285:            log_compras_error("inventarios-fisicos", server_id, "CONNECTION_ERROR", error_msg[:200], server.get('system_type'))
7287:                raise HTTPException(status_code=503, detail=f"Servidor temporalmente inaccesible: {server['host']}")
7308:            result = execute_sql_query(
7309:                server['host'], server['port'], server['database'],
7317:            log_compras_error("inventarios-fisicos", server_id, "QUERY_ERROR", str(e), server.get('system_type'))
7322:    log_compras_error("inventarios-fisicos", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
7325:@api_router.get("/compras/pedidos-vigentes/{server_id}")
7409:            result = execute_sql_query(
7410:                server['host'], server['port'], server['database'],
7420:            log_compras_error("pedidos-vigentes", server_id, "CONNECTION_ERROR", error_msg[:200], server.get('system_type'))
7422:                raise HTTPException(status_code=503, detail=f"Servidor temporalmente inaccesible: {server['host']}")
7442:            result = execute_sql_query(
7443:                server['host'], server['port'], server['database'],
7457:@api_router.get("/compras/detalle-pedido-manual/{server_id}")
7475:        result = execute_sql_query(
7476:            server['host'], server['port'], server['database'],
7499:        result = execute_sql_query(
7500:            server['host'], server['port'], server['database'],
7512:@api_router.get("/compras/detalle-movimientos/{server_id}")
7540:        result = execute_sql_query(
7541:            server['host'], server['port'], server['database'],
7549:@api_router.get("/compras/detalle-consumos/{server_id}")
7574:        result = execute_sql_query(
7575:            server['host'], server['port'], server['database'],
7584:@api_router.get("/compras/detalle-pedido/{server_id}/{folio}")
7625:        result = execute_sql_query(
7626:            server['host'], server['port'], server['database'],
7631:@api_router.post("/compras/calculo-pedido")
7705:        almacen_result = execute_sql_query(
7706:            server['host'], server['port'], server['database'],
7745:            inv_result = execute_sql_query(
7746:                server['host'], server['port'], server['database'],
7788:        productos = execute_sql_query(
7789:            server['host'], server['port'], server['database'],
7803:            inv_detalle = execute_sql_query(
7804:                server['host'], server['port'], server['database'],
7831:        mov_result = execute_sql_query(
7832:            server['host'], server['port'], server['database'],
7865:            ventas_result = execute_sql_query(
7866:                server['host'], server['port'], server['database'],
7881:            salidas_result = execute_sql_query(
7882:                server['host'], server['port'], server['database'],
7899:        inv_final_result = execute_sql_query(
7900:            server['host'], server['port'], server['database'],
7913:            inv_final_detalle = execute_sql_query(
7914:                server['host'], server['port'], server['database'],
7931:            ped_result = execute_sql_query(
7932:                server['host'], server['port'], server['database'],
7945:                ped_result = execute_sql_query(
7946:                    server['host'], server['port'], server['database'],
8140:@api_router.post("/compras/productos-para-captura")
8175:                    result = execute_sql_query(
8176:                        server['host'], server['port'], server['database'],
8202:                result = execute_sql_query(
8203:                    server['host'], server['port'], server['database'],
8228:                    result = execute_sql_query(
8229:                        server['host'], server['port'], server['database'],
8257:                    result = execute_sql_query(
8258:                        server['host'], server['port'], server['database'],
8284:                        result = execute_sql_query(
8285:                            server['host'], server['port'], server['database'],
8311:                        result = execute_sql_query(
8312:                            server['host'], server['port'], server['database'],
8367:            test_result = execute_sql_query(
8368:                server['host'], server['port'], server['database'],
8411:            tipos_alm_result = execute_sql_query(
8412:                server['host'], server['port'], server['database'],
8459:                requi_result = execute_sql_query(
8460:                    server['host'], server['port'], server['database'],
8518:                    tipo_result = execute_sql_query(
8519:                        server['host'], server['port'], server['database'],
8551:                    result_ini = execute_sql_query(
8552:                        server['host'], server['port'], server['database'],
8626:                    mov_result = execute_sql_query(
8627:                        server['host'], server['port'], server['database'],
8646:                    entrada_result = execute_sql_query(
8647:                        server['host'], server['port'], server['database'],
8664:                    salida_result = execute_sql_query(
8665:                        server['host'], server['port'], server['database'],
8688:                    mov_result = execute_sql_query(
8689:                        server['host'], server['port'], server['database'],
8720:                    salidas_result = execute_sql_query(
8721:                        server['host'], server['port'], server['database'],
8740:                consumos_result = execute_sql_query(
8741:                    server['host'], server['port'], server['database'],
8777:                        tipo_result = execute_sql_query(
8778:                            server['host'], server['port'], server['database'],
8807:                        result_fin = execute_sql_query(
8808:                            server['host'], server['port'], server['database'],
9302:@api_router.post("/compras/detalle-movimientos")
9387:                result_pres = execute_sql_query(
9388:                    server['host'], server['port'], server['database'],
9435:                result_ins = execute_sql_query(
9436:                    server['host'], server['port'], server['database'],
9512:@api_router.post("/compras/detalle-consumos")
9567:            result_ventas = execute_sql_query(
9568:                server['host'], server['port'], server['database'],
9734:            result_compras = execute_sql_query(
9735:                server['host'], server['port'], server['database'],
9758:            result_req = execute_sql_query(
9759:                server['host'], server['port'], server['database'],
9773:            result_prov = execute_sql_query(
9774:                server['host'], server['port'], server['database'],
9794:            result_top = execute_sql_query(
9795:                server['host'], server['port'], server['database'],
9850:            result_compras = execute_sql_query(
9851:                server['host'], server['port'], server['database'],
9888:            result_prov = execute_sql_query(
9889:                server['host'], server['port'], server['database'],
9908:            result_top = execute_sql_query(
9909:                server['host'], server['port'], server['database'],
9994:            result = execute_sql_query(
9995:                server['host'], server['port'], server['database'],
10045:            result = execute_sql_query(
10046:                server['host'], server['port'], server['database'],
10130:            result = execute_sql_query(
10131:                server['host'], server['port'], server['database'],
10187:            result = execute_sql_query(
10188:                server['host'], server['port'], server['database'],
10255:# ENDPOINT /comercial/detalle-movimientos - MIGRADO A modules/comercial/routes.py
10407:    from core.db import execute_sql_query
10462:        results = execute_sql_query(
10831:    from core.db import execute_sql_query_params
10923:            result = execute_sql_query_params(
10952:    from core.db import execute_sql_query_params
10986:        result = execute_sql_query_params(
11092:            result = execute_sql_query(
11144:        result = execute_sql_query(
12179:        result = execute_sql_query(
13224:        host_str = server['host']
13240:            database=server['database'],
13842:            tablas = execute_sql_query(
13859:            columnas = execute_sql_query(
13878:            cols_texto = execute_sql_query(
13892:                datos = execute_sql_query(
13907:            tablas_texto = execute_sql_query(
13925:                cols = execute_sql_query(
13935:                        datos = execute_sql_query(
14143:        result = execute_sql_query(
14144:            server['host'], server['port'], server['database'],
14377:        result = execute_sql_query(
15061:    from core.db import execute_sql_query, ResilientConfig
15081:    results = execute_sql_query(
17938:init_portal_db(db, JWT_SECRET, execute_sql_query)
```

## 3. Módulo backend/compras
```text
/app/backend/modules/compras/service.py:7:- Lógica de inventarios físicos, pedidos, facturas
/app/backend/modules/compras/service.py:15:NOTA: La lógica compleja de auditoría operativa y cálculo de pedidos
/app/backend/modules/compras/service.py:27:    is_mpro_system,
/app/backend/modules/compras/service.py:28:    is_softrestaurant_system,
/app/backend/modules/compras/service.py:36:# INVENTARIOS FÍSICOS
/app/backend/modules/compras/service.py:39:async def obtener_inventarios_fisicos(
/app/backend/modules/compras/service.py:40:    server_id: str,
/app/backend/modules/compras/service.py:46:    Obtiene la lista de inventarios físicos disponibles.
/app/backend/modules/compras/service.py:47:    Soporta MPRO y SoftRestaurant.
/app/backend/modules/compras/service.py:51:    server = await repo.get_server_by_id(server_id)
/app/backend/modules/compras/service.py:59:        if is_mpro_system(system_type):
/app/backend/modules/compras/service.py:60:            log_compras_adapter_selected("inventarios-fisicos", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:66:            result = repo.query_inventarios_fisicos_mpro(server, almacen_filtro, sucursal_id)
/app/backend/modules/compras/service.py:67:            log_compras_query_result("inventarios-fisicos", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:69:        elif is_softrestaurant_system(system_type):
/app/backend/modules/compras/service.py:70:            log_compras_adapter_selected("inventarios-fisicos", server_id, system_type, "SR_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:75:            result = repo.query_inventarios_fisicos_sr(server, almacen_filtro)
/app/backend/modules/compras/service.py:76:            log_compras_query_result("inventarios-fisicos", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:80:            log_compras_error("inventarios-fisicos", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/modules/compras/service.py:83:                detail=f"El tipo de sistema '{system_type}' (normalizado: {normalized}) no está soportado para inventarios físicos"
/app/backend/modules/compras/service.py:103:        log_compras_error("inventarios-fisicos", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:108:# PEDIDOS VIGENTES
/app/backend/modules/compras/service.py:111:async def obtener_pedidos_vigentes(server_id: str, sucursal_id: str = None) -> List[Dict]:
/app/backend/modules/compras/service.py:113:    Obtiene pedidos/requisiciones vigentes.
/app/backend/modules/compras/service.py:114:    Soporta MPRO y SoftRestaurant.
/app/backend/modules/compras/service.py:121:    server = await repo.get_server_by_id(server_id)
/app/backend/modules/compras/service.py:129:        if is_mpro_system(system_type):
/app/backend/modules/compras/service.py:130:            log_compras_adapter_selected("pedidos-vigentes", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:131:            result = repo.query_pedidos_vigentes_mpro(server, sucursal_id)
/app/backend/modules/compras/service.py:132:            # MPRO retorna lista directamente (TODO: migrar a ComprasQueryResult)
/app/backend/modules/compras/service.py:134:            log_compras_query_result("pedidos-vigentes", server_id, "SUCCESS", len(data))
/app/backend/modules/compras/service.py:136:        elif is_softrestaurant_system(system_type):
/app/backend/modules/compras/service.py:137:            log_compras_adapter_selected("pedidos-vigentes", server_id, system_type, "SR_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:138:            query_result = repo.query_pedidos_vigentes_sr(server)
/app/backend/modules/compras/service.py:142:                log_compras_query_result("pedidos-vigentes", server_id, "TABLE_NOT_FOUND", 0)
/app/backend/modules/compras/service.py:143:                logging.info(f"[COMPRAS] Pedidos no disponibles en {server['name']}: {query_result.message}")
/app/backend/modules/compras/service.py:147:                log_compras_error("pedidos-vigentes", server_id, query_result.status, query_result.message, system_type)
/app/backend/modules/compras/service.py:148:                logging.warning(f"[COMPRAS] Error en pedidos: {query_result.message}")
/app/backend/modules/compras/service.py:152:            log_compras_query_result("pedidos-vigentes", server_id, "SUCCESS", len(data))
/app/backend/modules/compras/service.py:155:            log_compras_error("pedidos-vigentes", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/modules/compras/service.py:158:                detail=f"El tipo de sistema '{system_type}' (normalizado: {normalized}) no está soportado para pedidos"
/app/backend/modules/compras/service.py:180:        log_compras_error("pedidos-vigentes", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:189:async def obtener_parametros(server_id: str, sucursal: str) -> Dict:
/app/backend/modules/compras/service.py:194:    params = await repo.get_compras_params(server_id, sucursal)
/app/backend/modules/compras/service.py:198:            "dias_inventario": params.get("dias_inventario", 10),
/app/backend/modules/compras/service.py:206:        "dias_inventario": 10,
/app/backend/modules/compras/service.py:213:async def guardar_parametros(server_id: str, sucursal: str, params: Dict) -> Dict:
/app/backend/modules/compras/service.py:217:    await repo.save_compras_params(server_id, sucursal, params)
/app/backend/modules/compras/service.py:225:async def obtener_detalle_factura(server_id: str, folio: str) -> List[Dict]:
/app/backend/modules/compras/service.py:229:    FASE 3A: Blindaje - Solo disponible en MPRO
/app/backend/modules/compras/service.py:231:    server = await repo.get_server_by_id(server_id)
/app/backend/modules/compras/service.py:238:        if is_mpro_system(system_type):
/app/backend/modules/compras/service.py:239:            log_compras_adapter_selected("detalle-factura", server_id, system_type, "MPRO_ADAPTER")
/app/backend/modules/compras/service.py:240:            result = repo.query_detalle_factura_mpro(server, folio)
/app/backend/modules/compras/service.py:241:            log_compras_query_result("detalle-factura", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:255:        log_compras_adapter_selected("detalle-factura", server_id, system_type, "NO_ADAPTER_AVAILABLE")
/app/backend/modules/compras/service.py:258:            detail=f"El detalle de factura solo está disponible para sistemas MPRO. Sistema actual: {system_type}"
/app/backend/modules/compras/service.py:264:        log_compras_error("detalle-factura", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:273:    server_id: str,
/app/backend/modules/compras/service.py:281:    FASE 3A: Blindaje - Solo disponible en MPRO
/app/backend/modules/compras/service.py:283:    server = await repo.get_server_by_id(server_id)
/app/backend/modules/compras/service.py:291:    if sucursal and is_mpro_system(system_type):
/app/backend/modules/compras/service.py:299:        if is_mpro_system(system_type):
/app/backend/modules/compras/service.py:300:            log_compras_adapter_selected("facturas-proveedor", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:301:            result = repo.query_facturas_proveedor_mpro(server, sucursal_id, meses, anio)
/app/backend/modules/compras/service.py:302:            log_compras_query_result("facturas-proveedor", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:317:        log_compras_adapter_selected("facturas-proveedor", server_id, system_type, "NO_ADAPTER_AVAILABLE")
/app/backend/modules/compras/service.py:320:            detail=f"Las facturas de proveedor solo están disponibles para sistemas MPRO. Sistema actual: {system_type}"
/app/backend/modules/compras/service.py:326:        log_compras_error("facturas-proveedor", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:331:    'obtener_inventarios_fisicos',
/app/backend/modules/compras/service.py:332:    'obtener_pedidos_vigentes',
/app/backend/modules/compras/repository_compras_sql.py:71:        -- Parámetros de cálculo de pedidos
/app/backend/modules/compras/repository_compras_sql.py:72:        [DiasInventario] INT NOT NULL DEFAULT 10,
/app/backend/modules/compras/repository_compras_sql.py:128:def get_compras_params_sql(server_id: str, sucursal: str) -> Optional[Dict]:
/app/backend/modules/compras/repository_compras_sql.py:135:        server_id: ID del servidor
/app/backend/modules/compras/repository_compras_sql.py:148:                ServerID as server_id,
/app/backend/modules/compras/repository_compras_sql.py:150:                DiasInventario as dias_inventario,
/app/backend/modules/compras/repository_compras_sql.py:161:        cursor.execute(query, (server_id, sucursal))
/app/backend/modules/compras/repository_compras_sql.py:178:                'server_id': row['server_id'],
/app/backend/modules/compras/repository_compras_sql.py:180:                'dias_inventario': row['dias_inventario'],
/app/backend/modules/compras/repository_compras_sql.py:188:            logger.debug(f"[COMPRAS_SQL] Parámetros encontrados para {server_id}/{sucursal}")
/app/backend/modules/compras/repository_compras_sql.py:191:        logger.debug(f"[COMPRAS_SQL] No hay parámetros configurados para {server_id}/{sucursal}")
/app/backend/modules/compras/repository_compras_sql.py:201:def save_compras_params_sql(server_id: str, sucursal: str, params: Dict, usuario: str = None) -> bool:
/app/backend/modules/compras/repository_compras_sql.py:209:        server_id: ID del servidor
/app/backend/modules/compras/repository_compras_sql.py:224:        dias_inventario = params.get('dias_inventario', 10)
/app/backend/modules/compras/repository_compras_sql.py:239:                    DiasInventario = %s,
/app/backend/modules/compras/repository_compras_sql.py:247:                INSERT (ServerID, SucursalID, DiasInventario, ExcluirDomingos, 
/app/backend/modules/compras/repository_compras_sql.py:254:            server_id, sucursal,
/app/backend/modules/compras/repository_compras_sql.py:256:            dias_inventario, excluir_domingos, dias_inhabiles_json, dias_transito_proveedor, usuario,
/app/backend/modules/compras/repository_compras_sql.py:258:            server_id, sucursal, dias_inventario, excluir_domingos, 
/app/backend/modules/compras/repository_compras_sql.py:266:        logger.info(f"[COMPRAS_SQL] Parámetros guardados para {server_id}/{sucursal}")
/app/backend/modules/compras/repository_compras_sql.py:289:                ServerID as server_id,
/app/backend/modules/compras/repository_compras_sql.py:291:                DiasInventario as dias_inventario,
/app/backend/modules/compras/repository_compras_sql.py:320:                'server_id': row['server_id'],
/app/backend/modules/compras/repository_compras_sql.py:322:                'dias_inventario': row['dias_inventario'],
/app/backend/modules/compras/repository_compras_sql.py:338:def delete_compras_params_sql(server_id: str, sucursal: str) -> bool:
/app/backend/modules/compras/repository_compras_sql.py:343:        server_id: ID del servidor
/app/backend/modules/compras/repository_compras_sql.py:359:        cursor.execute(query, (server_id, sucursal))
/app/backend/modules/compras/repository_compras_sql.py:366:        logger.info(f"[COMPRAS_SQL] Parámetros eliminados para {server_id}/{sucursal}")
/app/backend/modules/compras/__init__.py:4:Módulo de compras, pedidos e inventarios.
/app/backend/modules/compras/__init__.py:20:NOTA: Los endpoints complejos (calculo-pedido, auditoria-operativa, dashboard)
/app/backend/modules/compras/__init__.py:27:    CalculoPedidoRequest,
/app/backend/modules/compras/__init__.py:30:    DetalleMovimientosRequest,
/app/backend/modules/compras/__init__.py:38:    is_mpro_system,
/app/backend/modules/compras/__init__.py:39:    is_softrestaurant_system,
/app/backend/modules/compras/__init__.py:78:    'CalculoPedidoRequest',
/app/backend/modules/compras/__init__.py:81:    'DetalleMovimientosRequest',
/app/backend/modules/compras/__init__.py:88:    'is_mpro_system',
/app/backend/modules/compras/__init__.py:89:    'is_softrestaurant_system',
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
/app/backend/modules/compras/eventos_compras.py:74:    server_id: str
/app/backend/modules/compras/eventos_compras.py:90:            "server_id": self.server_id,
/app/backend/modules/compras/eventos_compras.py:165:                evento.server_id,
/app/backend/modules/compras/eventos_compras.py:211:                    "server_id": e['ServerID'],
/app/backend/modules/compras/eventos_compras.py:318:    def get_checkpoint(self, server_id: str, sync_type: SyncType) -> Dict:
/app/backend/modules/compras/eventos_compras.py:328:            """, (server_id, sync_type.value))
/app/backend/modules/compras/eventos_compras.py:353:        server_id: str, 
/app/backend/modules/compras/eventos_compras.py:383:                server_id, sync_type.value,  # Source
/app/backend/modules/compras/eventos_compras.py:385:                server_id, server_name, sync_type.value, last_folio, last_fecha, now, records_found, now, now  # Insert
/app/backend/modules/compras/eventos_compras.py:433:    def detectar_nuevos_inventarios(
/app/backend/modules/compras/eventos_compras.py:440:        Detecta inventarios nuevos desde el último checkpoint.
/app/backend/modules/compras/eventos_compras.py:445:        server_id = server_info.get('id', '')
/app/backend/modules/compras/eventos_compras.py:450:        checkpoint = self.checkpoint_mgr.get_checkpoint(server_id, SyncType.INVENTARIOS)
/app/backend/modules/compras/eventos_compras.py:455:            if 'MPRO' in system_type or 'MANAGEMENT' in system_type:
/app/backend/modules/compras/eventos_compras.py:472:            elif 'SOFTRESTAURANT' in system_type:
/app/backend/modules/compras/eventos_compras.py:515:                        evento_tipo=EventoTipo.NUEVO_INVENTARIO,
/app/backend/modules/compras/eventos_compras.py:516:                        server_id=server_id,
/app/backend/modules/compras/eventos_compras.py:539:                    server_id, server_name, SyncType.INVENTARIOS,
/app/backend/modules/compras/eventos_compras.py:543:            logger.info(f"[DETECTOR] Inventarios {server_name}: {nuevos} nuevos, {eventos_generados} eventos")
/app/backend/modules/compras/eventos_compras.py:547:            logger.error(f"[DETECTOR] Error detectando inventarios en {server_name}: {e}")
/app/backend/modules/compras/eventos_compras.py:550:    def detectar_nuevas_requisiciones(
/app/backend/modules/compras/eventos_compras.py:557:        Detecta requisiciones nuevas desde el último checkpoint.
/app/backend/modules/compras/eventos_compras.py:559:        server_id = server_info.get('id', '')
/app/backend/modules/compras/eventos_compras.py:563:        checkpoint = self.checkpoint_mgr.get_checkpoint(server_id, SyncType.REQUISICIONES)
/app/backend/modules/compras/eventos_compras.py:567:            if 'MPRO' in system_type or 'MANAGEMENT' in system_type:
/app/backend/modules/compras/eventos_compras.py:572:                        FROM Orden_Compra
/app/backend/modules/compras/eventos_compras.py:580:                        FROM Orden_Compra
/app/backend/modules/compras/eventos_compras.py:583:            elif 'SOFTRESTAURANT' in system_type:
/app/backend/modules/compras/eventos_compras.py:588:                        FROM ordenescompra
/app/backend/modules/compras/eventos_compras.py:596:                        FROM ordenescompra
/app/backend/modules/compras/eventos_compras.py:625:                        evento_tipo=EventoTipo.NUEVA_REQUISICION,
/app/backend/modules/compras/eventos_compras.py:626:                        server_id=server_id,
/app/backend/modules/compras/eventos_compras.py:647:                    server_id, server_name, SyncType.REQUISICIONES,
/app/backend/modules/compras/eventos_compras.py:651:            logger.info(f"[DETECTOR] Requisiciones {server_name}: {nuevos} nuevos, {eventos_generados} eventos")
/app/backend/modules/compras/eventos_compras.py:655:            logger.error(f"[DETECTOR] Error detectando requisiciones en {server_name}: {e}")
/app/backend/modules/compras/system_type_utils.py:18:    is_mpro_system,
/app/backend/modules/compras/system_type_utils.py:19:    is_softrestaurant_system,
/app/backend/modules/compras/system_type_utils.py:164:    server_id: str,
/app/backend/modules/compras/system_type_utils.py:173:        f"server_id={server_id} "
/app/backend/modules/compras/system_type_utils.py:183:    server_id: str,
/app/backend/modules/compras/system_type_utils.py:192:        f"server_id={server_id} status={status} "
/app/backend/modules/compras/system_type_utils.py:199:    server_id: str,
/app/backend/modules/compras/system_type_utils.py:207:        f"server_id={server_id} "
/app/backend/modules/compras/system_type_utils.py:222:    'is_mpro_system',
/app/backend/modules/compras/system_type_utils.py:223:    'is_softrestaurant_system',
/app/backend/modules/compras/repository.py:7:- Queries SQL para MPRO y SoftRestaurant
/app/backend/modules/compras/repository.py:20:por compatibilidad con otros módulos que aún usan StubDatabase (pedidos_detector_job).
/app/backend/modules/compras/repository.py:28:from core.db import execute_sql_query
/app/backend/modules/compras/repository.py:58:        result = execute_sql_query(
/app/backend/modules/compras/repository.py:59:            server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:136:async def get_server_by_id(server_id: str) -> Optional[Dict]:
/app/backend/modules/compras/repository.py:148:    server = await get_server_connection_info(server_id, db=db)
/app/backend/modules/compras/repository.py:160:async def get_compras_params(server_id: str, sucursal: str) -> Optional[Dict]:
/app/backend/modules/compras/repository.py:167:        server_id: ID del servidor
/app/backend/modules/compras/repository.py:174:    return get_compras_params_sql(server_id, sucursal)
/app/backend/modules/compras/repository.py:177:async def save_compras_params(server_id: str, sucursal: str, params: Dict) -> None:
/app/backend/modules/compras/repository.py:184:        server_id: ID del servidor
/app/backend/modules/compras/repository.py:189:    success = save_compras_params_sql(server_id, sucursal, params)
/app/backend/modules/compras/repository.py:191:        logger.error(f"[COMPRAS_REPO] Error guardando parámetros en SQL para {server_id}/{sucursal}")
/app/backend/modules/compras/repository.py:193:        logger.info(f"[COMPRAS_REPO] Parámetros guardados en EDARSAHUB SQL para {server_id}/{sucursal}")
/app/backend/modules/compras/repository.py:197:# QUERIES SQL - INVENTARIOS FÍSICOS
/app/backend/modules/compras/repository.py:200:def query_inventarios_fisicos_mpro(server: Dict, almacen_filtro: str = "", sucursal_id: str = None) -> List[Dict]:
/app/backend/modules/compras/repository.py:202:    Obtiene inventarios físicos de MPRO.
/app/backend/modules/compras/repository.py:214:        (SELECT COUNT(*) FROM Inventario_Fisico_Detalle D WHERE D.If_Folio = F.If_Folio) as productos,
/app/backend/modules/compras/repository.py:215:        'MPRO' as origen
/app/backend/modules/compras/repository.py:216:    FROM Inventario_Fisico F
/app/backend/modules/compras/repository.py:223:    return execute_sql_query(
/app/backend/modules/compras/repository.py:224:        server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:229:def query_inventarios_fisicos_sr(server: Dict, almacen_filtro: str = "") -> List[Dict]:
/app/backend/modules/compras/repository.py:231:    Obtiene inventarios físicos de SoftRestaurant.
/app/backend/modules/compras/repository.py:242:        'SoftRestaurant' as origen
/app/backend/modules/compras/repository.py:249:    return execute_sql_query(
/app/backend/modules/compras/repository.py:250:        server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:256:# QUERIES SQL - PEDIDOS VIGENTES
/app/backend/modules/compras/repository.py:259:def query_pedidos_vigentes_mpro(server: Dict, sucursal_id: str = None) -> List[Dict]:
/app/backend/modules/compras/repository.py:261:    Obtiene pedidos/requisiciones vigentes de MPRO.
/app/backend/modules/compras/repository.py:275:        (SELECT COUNT(*) FROM Requisicion_Detalle D WHERE D.Rq_Folio = R.Rq_Folio) as productos,
/app/backend/modules/compras/repository.py:276:        'MPRO' as origen
/app/backend/modules/compras/repository.py:277:    FROM Requisicion R
/app/backend/modules/compras/repository.py:284:    return execute_sql_query(
/app/backend/modules/compras/repository.py:285:        server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:290:def query_pedidos_vigentes_sr(server: Dict) -> ComprasQueryResult:
/app/backend/modules/compras/repository.py:292:    Obtiene pedidos vigentes de SoftRestaurant.
/app/backend/modules/compras/repository.py:295:    - Valida existencia de tabla 'pedidocompra' antes de ejecutar
/app/backend/modules/compras/repository.py:299:    # Primero validar que exista la tabla pedidocompra
/app/backend/modules/compras/repository.py:300:    if not validate_table_exists(server, 'pedidocompra'):
/app/backend/modules/compras/repository.py:301:        logging.info(f"[COMPRAS] Tabla 'pedidocompra' no existe en {server['name']} - operación no soportada")
/app/backend/modules/compras/repository.py:306:            message=f"El servidor {server['name']} no tiene módulo de pedidos de compra instalado"
/app/backend/modules/compras/repository.py:311:        CAST(P.idpedidocompra as VARCHAR) as folio,
/app/backend/modules/compras/repository.py:324:        (SELECT COUNT(*) FROM detallepedidocompra D WHERE D.idpedidocompra = P.idpedidocompra) as productos,
/app/backend/modules/compras/repository.py:325:        'SoftRestaurant' as origen
/app/backend/modules/compras/repository.py:326:    FROM pedidocompra P
/app/backend/modules/compras/repository.py:328:    ORDER BY P.fecha DESC, P.idpedidocompra DESC
/app/backend/modules/compras/repository.py:332:        result = execute_sql_query(
/app/backend/modules/compras/repository.py:333:            server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:342:                message=f"Se encontraron {len(result)} pedidos"
/app/backend/modules/compras/repository.py:349:                message="No hay pedidos de compra vigentes"
/app/backend/modules/compras/repository.py:353:        logging.error(f"[COMPRAS] Error en query_pedidos_vigentes_sr: {e}")
/app/backend/modules/compras/repository.py:373:# QUERIES SQL - DETALLE DE PEDIDO/REQUISICIÓN
/app/backend/modules/compras/repository.py:376:def query_detalle_pedido_mpro(server: Dict, folio: str) -> List[Dict]:
/app/backend/modules/compras/repository.py:378:    Obtiene el detalle de productos de un pedido/requisición en MPRO.
/app/backend/modules/compras/repository.py:389:            FROM Inventario_Fisico_Detalle ID
/app/backend/modules/compras/repository.py:390:            INNER JOIN Inventario_Fisico I ON I.If_Folio = ID.If_Folio
/app/backend/modules/compras/repository.py:397:            FROM Movimiento_Detalle MD
/app/backend/modules/compras/repository.py:398:            INNER JOIN Movimiento M ON M.Mv_Folio = MD.Mv_Folio
/app/backend/modules/compras/repository.py:401:            AND M.Tm_Cve_TipoMov IN (SELECT Tm_Cve_TipoMov FROM Tipo_Movimiento WHERE Tm_Tipo = 'S')
/app/backend/modules/compras/repository.py:404:    FROM Requisicion_Detalle RD
/app/backend/modules/compras/repository.py:405:    INNER JOIN Requisicion R ON R.Rq_Folio = RD.Rq_Folio
/app/backend/modules/compras/repository.py:411:    return execute_sql_query(
/app/backend/modules/compras/repository.py:412:        server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:421:def query_detalle_factura_mpro(server: Dict, folio: str) -> List[Dict]:
/app/backend/modules/compras/repository.py:423:    Obtiene el detalle de una factura/entrada en MPRO.
/app/backend/modules/compras/repository.py:432:    FROM Movimiento_Detalle MD
/app/backend/modules/compras/repository.py:433:    INNER JOIN Movimiento M ON M.Mv_Folio = MD.Mv_Folio
/app/backend/modules/compras/repository.py:439:    return execute_sql_query(
/app/backend/modules/compras/repository.py:440:        server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:449:def query_facturas_proveedor_mpro(server: Dict, sucursal_id: str = None, meses: str = None, anio: str = None) -> List[Dict]:
/app/backend/modules/compras/repository.py:451:    Obtiene facturas de proveedores en MPRO.
/app/backend/modules/compras/repository.py:469:        (SELECT COUNT(*) FROM Movimiento_Detalle MD WHERE MD.Mv_Folio = M.Mv_Folio) as productos
/app/backend/modules/compras/repository.py:470:    FROM Movimiento M
/app/backend/modules/compras/repository.py:473:    WHERE M.Tm_Cve_TipoMov IN (SELECT Tm_Cve_TipoMov FROM Tipo_Movimiento WHERE Tm_Tipo = 'E')
/app/backend/modules/compras/repository.py:478:    return execute_sql_query(
/app/backend/modules/compras/repository.py:479:        server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:487:    'get_server_by_id',
/app/backend/modules/compras/repository.py:490:    # Inventarios físicos
/app/backend/modules/compras/repository.py:491:    'query_inventarios_fisicos_mpro',
/app/backend/modules/compras/repository.py:492:    'query_inventarios_fisicos_sr',
/app/backend/modules/compras/repository.py:493:    # Pedidos
/app/backend/modules/compras/repository.py:494:    'query_pedidos_vigentes_mpro',
/app/backend/modules/compras/repository.py:495:    'query_pedidos_vigentes_sr',
/app/backend/modules/compras/repository.py:496:    'query_detalle_pedido_mpro',
/app/backend/modules/compras/repository.py:498:    'query_detalle_factura_mpro',
/app/backend/modules/compras/repository.py:499:    'query_facturas_proveedor_mpro',
/app/backend/modules/compras/historical_kpis_repository.py:11:- INVENTARIO_FISICO: Conteos de inventario por almacén/fecha
/app/backend/modules/compras/historical_kpis_repository.py:12:- PEDIDO: Pedidos/requisiciones por fecha
/app/backend/modules/compras/historical_kpis_repository.py:13:- ORDEN_COMPRA: Órdenes de compra por proveedor/fecha  
/app/backend/modules/compras/historical_kpis_repository.py:90:                [server_id] NVARCHAR(50) NOT NULL,
/app/backend/modules/compras/historical_kpis_repository.py:96:                -- Inventarios Físicos
/app/backend/modules/compras/historical_kpis_repository.py:101:                -- Pedidos
/app/backend/modules/compras/historical_kpis_repository.py:102:                [ped_pedidos_count] INT DEFAULT 0,
/app/backend/modules/compras/historical_kpis_repository.py:107:                [oc_ordenes_count] INT DEFAULT 0,
/app/backend/modules/compras/historical_kpis_repository.py:125:            ON [dbo].[Compras_KPIs_Historico] (server_id, sucursal_id, fecha, kpi_tipo);
/app/backend/modules/compras/historical_kpis_repository.py:145:    server_id: str,
/app/backend/modules/compras/historical_kpis_repository.py:166:        WHERE server_id = %s AND sucursal_id = %s AND fecha = %s AND kpi_tipo = %s
/app/backend/modules/compras/historical_kpis_repository.py:168:        cursor.execute(check_sql, (server_id, sucursal_id, fecha, kpi_tipo))
/app/backend/modules/compras/historical_kpis_repository.py:180:                ped_pedidos_count = %s,
/app/backend/modules/compras/historical_kpis_repository.py:183:                oc_ordenes_count = %s,
/app/backend/modules/compras/historical_kpis_repository.py:192:            WHERE server_id = %s AND sucursal_id = %s AND fecha = %s AND kpi_tipo = %s
/app/backend/modules/compras/historical_kpis_repository.py:200:                kpi_data.get('ped_pedidos_count', 0),
/app/backend/modules/compras/historical_kpis_repository.py:203:                kpi_data.get('oc_ordenes_count', 0),
/app/backend/modules/compras/historical_kpis_repository.py:211:                server_id, sucursal_id, fecha, kpi_tipo
/app/backend/modules/compras/historical_kpis_repository.py:220:                run_id, server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo,
/app/backend/modules/compras/historical_kpis_repository.py:222:                ped_pedidos_count, ped_total_monto, ped_productos_count,
/app/backend/modules/compras/historical_kpis_repository.py:223:                oc_ordenes_count, oc_total_monto, oc_proveedores_count,
/app/backend/modules/compras/historical_kpis_repository.py:229:                run_id, server_id, sucursal_id, system_type, fecha, kpi_tipo,
/app/backend/modules/compras/historical_kpis_repository.py:233:                kpi_data.get('ped_pedidos_count', 0),
/app/backend/modules/compras/historical_kpis_repository.py:236:                kpi_data.get('oc_ordenes_count', 0),
/app/backend/modules/compras/sync_service.py:2:COMPRAS SYNC SERVICE - Sincronización de Inventarios y Requisiciones a EDARSAHUB
/app/backend/modules/compras/sync_service.py:8:- Compras_Inventarios_Fisicos_Sync: Inventarios físicos sincronizados
/app/backend/modules/compras/sync_service.py:9:- Compras_Requisiciones_Sync: Requisiciones/pedidos sincronizados
/app/backend/modules/compras/sync_service.py:46:def obtener_inventarios_fisicos_sync(
/app/backend/modules/compras/sync_service.py:48:    server_id: str = None,
/app/backend/modules/compras/sync_service.py:54:    Obtiene inventarios físicos DESDE EDARSAHUB (sincronizados).
/app/backend/modules/compras/sync_service.py:65:                unidad_negocio_codigo, server_id, system_type,
/app/backend/modules/compras/sync_service.py:67:            FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/compras/sync_service.py:76:        if server_id:
/app/backend/modules/compras/sync_service.py:77:            query += " AND LOWER(server_id) = LOWER(%s)"
/app/backend/modules/compras/sync_service.py:78:            params.append(server_id)
/app/backend/modules/compras/sync_service.py:101:        logger.info(f"[SYNC-READ] Inventarios físicos: {len(rows)} registros desde EDARSAHUB")
/app/backend/modules/compras/sync_service.py:105:        logger.error(f"[SYNC-READ] Error obteniendo inventarios: {e}")
/app/backend/modules/compras/sync_service.py:109:def obtener_requisiciones_sync(
/app/backend/modules/compras/sync_service.py:111:    server_id: str = None,
/app/backend/modules/compras/sync_service.py:116:    Obtiene requisiciones/pedidos DESDE EDARSAHUB (sincronizados).
/app/backend/modules/compras/sync_service.py:127:                unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
/app/backend/modules/compras/sync_service.py:129:            FROM Compras_Requisiciones_Sync
/app/backend/modules/compras/sync_service.py:138:        if server_id:
/app/backend/modules/compras/sync_service.py:139:            query += " AND server_id = %s"
/app/backend/modules/compras/sync_service.py:140:            params.append(server_id)
/app/backend/modules/compras/sync_service.py:158:        logger.info(f"[SYNC-READ] Requisiciones: {len(rows)} registros desde EDARSAHUB")
/app/backend/modules/compras/sync_service.py:162:        logger.error(f"[SYNC-READ] Error obteniendo requisiciones: {e}")
/app/backend/modules/compras/sync_service.py:170:def sync_inventarios_fisicos_from_server(
/app/backend/modules/compras/sync_service.py:173:    execute_sql_query_func
/app/backend/modules/compras/sync_service.py:176:    Sincroniza inventarios físicos desde un servidor físico a EDARSAHUB.
/app/backend/modules/compras/sync_service.py:182:        execute_sql_query_func: Función para ejecutar queries en el servidor origen
/app/backend/modules/compras/sync_service.py:187:    from core.system_type_utils import is_mpro_system, is_softrestaurant_system
/app/backend/modules/compras/sync_service.py:189:    server_id = server_info.get('id')
/app/backend/modules/compras/sync_service.py:194:    logger.info(f"[SYNC] Iniciando sync inventarios: {unidad_codigo} ({system_type})")
/app/backend/modules/compras/sync_service.py:198:        if is_mpro_system(system_type):
/app/backend/modules/compras/sync_service.py:199:            # MPRO usa tabla "Fisico" (no Fisico_Inventario)
/app/backend/modules/compras/sync_service.py:218:        elif is_softrestaurant_system(system_type):
/app/backend/modules/compras/sync_service.py:219:            # SoftRestaurant usa tabla "invfisico"
/app/backend/modules/compras/sync_service.py:240:        rows = execute_sql_query_func(
/app/backend/modules/compras/sync_service.py:258:            UPDATE Compras_Inventarios_Fisicos_Sync 
/app/backend/modules/compras/sync_service.py:260:            WHERE server_id = %s AND sync_status = 'ACTIVE'
/app/backend/modules/compras/sync_service.py:261:        """, (server_id,))
/app/backend/modules/compras/sync_service.py:268:                    INSERT INTO Compras_Inventarios_Fisicos_Sync
/app/backend/modules/compras/sync_service.py:269:                    (unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
/app/backend/modules/compras/sync_service.py:274:                    unidad_id, unidad_codigo, server_id, system_type,
/app/backend/modules/compras/sync_service.py:287:                logger.warning(f"[SYNC] Error insertando inventario {row.get('folio')}: {e}")
/app/backend/modules/compras/sync_service.py:292:        logger.info(f"[SYNC] Inventarios sincronizados: {records_synced} de {len(rows)}")
/app/backend/modules/compras/sync_service.py:296:        logger.error(f"[SYNC] Error sync inventarios {unidad_codigo}: {e}")
/app/backend/modules/compras/sync_service.py:300:def sync_requisiciones_from_server(
/app/backend/modules/compras/sync_service.py:303:    execute_sql_query_func
/app/backend/modules/compras/sync_service.py:306:    Sincroniza requisiciones/pedidos desde un servidor físico a EDARSAHUB.
/app/backend/modules/compras/sync_service.py:308:    from core.system_type_utils import is_mpro_system, is_softrestaurant_system
/app/backend/modules/compras/sync_service.py:310:    server_id = server_info.get('id')
/app/backend/modules/compras/sync_service.py:315:    logger.info(f"[SYNC] Iniciando sync requisiciones: {unidad_codigo} ({system_type})")
/app/backend/modules/compras/sync_service.py:319:        if is_mpro_system(system_type):
/app/backend/modules/compras/sync_service.py:337:                FROM Orden_Compra OC
/app/backend/modules/compras/sync_service.py:344:        elif is_softrestaurant_system(system_type):
/app/backend/modules/compras/sync_service.py:355:                    (SELECT COUNT(*) FROM ordenescompramov WHERE idOrdenCompra = OC.idOrdenCompra) as total_productos,
/app/backend/modules/compras/sync_service.py:363:                FROM ordenescompra OC
/app/backend/modules/compras/sync_service.py:373:        rows = execute_sql_query_func(
/app/backend/modules/compras/sync_service.py:391:            UPDATE Compras_Requisiciones_Sync 
/app/backend/modules/compras/sync_service.py:393:            WHERE server_id = %s AND sync_status = 'ACTIVE'
/app/backend/modules/compras/sync_service.py:394:        """, (server_id,))
/app/backend/modules/compras/sync_service.py:401:                    INSERT INTO Compras_Requisiciones_Sync
/app/backend/modules/compras/sync_service.py:402:                    (unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
/app/backend/modules/compras/sync_service.py:408:                    unidad_id, unidad_codigo, server_id, system_type,
/app/backend/modules/compras/sync_service.py:428:        logger.info(f"[SYNC] Requisiciones sincronizadas: {records_synced} de {len(rows)}")
/app/backend/modules/compras/sync_service.py:432:        logger.error(f"[SYNC] Error sync requisiciones {unidad_codigo}: {e}")
/app/backend/modules/compras/sync_service.py:438:    server_id: str,
/app/backend/modules/compras/sync_service.py:452:            (unidad_negocio_id, server_id, sync_type, sync_start, sync_end, 
/app/backend/modules/compras/sync_service.py:456:            unidad_negocio_id, server_id, sync_type,
/app/backend/modules/compras/sync_service.py:465:def get_last_sync_info(server_id: str, sync_type: str) -> Optional[Dict]:
/app/backend/modules/compras/sync_service.py:472:            WHERE server_id = %s AND sync_type = %s
/app/backend/modules/compras/sync_service.py:474:        """, (server_id, sync_type))
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
/app/backend/modules/compras/repository_pedidos_sql.py:143:    server_id: str = None,
/app/backend/modules/compras/repository_pedidos_sql.py:149:    Marca pedido como procesado en SQL.
/app/backend/modules/compras/repository_pedidos_sql.py:151:    REEMPLAZA: db['pedidos_procesados_automatizacion'].update_one(..., upsert=True)
/app/backend/modules/compras/repository_pedidos_sql.py:163:        SELECT ID FROM Scheduler_PedidosProcesados
/app/backend/modules/compras/repository_pedidos_sql.py:164:        WHERE EmpresaID = %s AND FolioPedido = %s AND SistemaOrigen = %s
/app/backend/modules/compras/repository_pedidos_sql.py:171:            UPDATE Scheduler_PedidosProcesados
/app/backend/modules/compras/repository_pedidos_sql.py:177:            WHERE EmpresaID = %s AND FolioPedido = %s AND SistemaOrigen = %s
/app/backend/modules/compras/repository_pedidos_sql.py:180:                estado, now, server_id, sucursal_id, detalles_json,
/app/backend/modules/compras/repository_pedidos_sql.py:186:            INSERT INTO Scheduler_PedidosProcesados (
/app/backend/modules/compras/repository_pedidos_sql.py:187:                SistemaOrigen, ServerID, EmpresaID, SucursalID, FolioPedido,
/app/backend/modules/compras/repository_pedidos_sql.py:192:                origen, server_id, empresa_id, sucursal_id, folio,
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
/app/backend/modules/compras/repository_pedidos_sql.py:249:                'server_id': r['ServerID'],
/app/backend/modules/compras/repository_pedidos_sql.py:258:        return pedidos
/app/backend/modules/compras/repository_pedidos_sql.py:261:        logger.error(f"[PEDIDOS_SQL] Error obteniendo pedidos procesados: {e}")
/app/backend/modules/compras/repository_pedidos_sql.py:269:# Tabla: Usa Scheduler_PedidosProcesados con DetallesJSON para tareas simples
/app/backend/modules/compras/repository_pedidos_sql.py:283:    tipo: str = "CAPTURA_INVENTARIO"
/app/backend/modules/compras/repository_pedidos_sql.py:291:    Para tracking simple, usamos DetallesJSON en Scheduler_PedidosProcesados.
/app/backend/modules/compras/repository_pedidos_sql.py:298:        # Si no, guardar en DetallesJSON del registro de pedido procesado
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
/app/backend/modules/compras/routes.py:63:# - POST /compras/calculo-pedido (~420 líneas)
/app/backend/modules/compras/routes.py:67:# - POST /compras/detalle-movimientos
/app/backend/modules/compras/schemas.py:8:- Schemas de pedidos, auditoría operativa, análisis de compras
/app/backend/modules/compras/schemas.py:16:    """Parámetros de configuración para cálculo de pedidos."""
/app/backend/modules/compras/schemas.py:17:    dias_inventario: int = 10  # Días de inventario a comprar
/app/backend/modules/compras/schemas.py:23:class CalculoPedidoRequest(BaseModel):
/app/backend/modules/compras/schemas.py:24:    """Request para cálculo de pedido sugerido."""
/app/backend/modules/compras/schemas.py:25:    server_id: str
/app/backend/modules/compras/schemas.py:28:    fecha_inventario_fisico: str  # Fecha del inventario físico inicial
/app/backend/modules/compras/schemas.py:30:    dias_inventario: int = 10  # Días de inventario a comprar
/app/backend/modules/compras/schemas.py:32:    folio_inventario_fisico: Optional[str] = None
/app/backend/modules/compras/schemas.py:35:    folio_pedido_comparar: Optional[str] = None  # Para comparar con pedido existente
/app/backend/modules/compras/schemas.py:40:    server_id: str
/app/backend/modules/compras/schemas.py:46:    fecha_auditoria: str  # Fecha del inventario final o actual
/app/backend/modules/compras/schemas.py:49:    folio_requisicion: Optional[str] = None  # Requisición a comparar (una sola)
/app/backend/modules/compras/schemas.py:50:    folios_requisiciones: Optional[List[str]] = None  # Múltiples requisiciones
/app/backend/modules/compras/schemas.py:51:    inventario_manual: Optional[List[Dict]] = None  # Para captura manual si no hay folio
/app/backend/modules/compras/schemas.py:52:    inventario_fisico_actual: Optional[List[Dict]] = None  # Captura manual del inv físico del día del pedido
/app/backend/modules/compras/schemas.py:53:    solo_skus_requisicion: bool = True  # Por defecto solo muestra SKUs de las requisiciones
/app/backend/modules/compras/schemas.py:54:    dias_objetivo_default: int = 10  # Días de inventario objetivo por defecto
/app/backend/modules/compras/schemas.py:60:    server_id: str
/app/backend/modules/compras/schemas.py:62:    folios_requisiciones: Optional[List[str]] = None
/app/backend/modules/compras/schemas.py:65:class DetalleMovimientosRequest(BaseModel):
/app/backend/modules/compras/schemas.py:66:    """Request para detalle de movimientos."""
/app/backend/modules/compras/schemas.py:67:    server_id: str
/app/backend/modules/compras/schemas.py:72:    tipo_movimiento: Optional[str] = None  # "entradas", "salidas", "todos"
/app/backend/modules/compras/schemas.py:79:    server_id: str
/app/backend/modules/compras/schemas.py:89:    server_id: str
/app/backend/modules/compras/schemas.py:98:    'CalculoPedidoRequest',
/app/backend/modules/compras/schemas.py:101:    'DetalleMovimientosRequest',
```

