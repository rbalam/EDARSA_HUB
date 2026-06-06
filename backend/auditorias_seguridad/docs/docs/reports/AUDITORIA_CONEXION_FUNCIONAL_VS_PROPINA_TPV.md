# Auditoría conexión funcional SoftRestaurant vs Propinas TPV

Fecha: Thu Jun  4 18:38:58 UTC 2026

## Objetivo

Determinar por qué CIENFUEGOS y LA ESTELAR sí sincronizan otras tablas SoftRestaurant, pero Propinas TPV no.

La corrección correcta es reutilizar el mismo helper/método de conexión que ya funciona para las demás sincronizaciones.

No crear conexión paralela para propinas.
No hardcodear host/puerto.
No asumir puerto 1433.
No tocar frontend.
## 1. Helpers de conexión SQL
```text
/app/backend/server.py.backup_env_connection_20260604_075317:15:# P0-INCIDENTE-SERVER_SECRET_KEY: load_dotenv() DEBE ejecutarse antes de que
/app/backend/server.py.backup_env_connection_20260604_075317:24:# VALIDACIÓN DE SERVER_SECRET_KEY - Entorno Preview/Staging/Production
/app/backend/server.py.backup_env_connection_20260604_075317:26:# MÁXIMA: SERVER_SECRET_KEY es obligatoria para cifrado de credenciales.
/app/backend/server.py.backup_env_connection_20260604_075317:33:    Valida que SERVER_SECRET_KEY esté configurada correctamente.
/app/backend/server.py.backup_env_connection_20260604_075317:37:    key = os.environ.get('SERVER_SECRET_KEY')
/app/backend/server.py.backup_env_connection_20260604_075317:47:        print(f"[ENCRYPTION] SERVER_SECRET_KEY loaded: true")
/app/backend/server.py.backup_env_connection_20260604_075317:51:        # En preview/staging/production, la ausencia de SERVER_SECRET_KEY es CRÍTICA
/app/backend/server.py.backup_env_connection_20260604_075317:53:            print("[ENCRYPTION] ⚠️  WARNING: SERVER_SECRET_KEY not configured")
/app/backend/server.py.backup_env_connection_20260604_075317:54:            print("[ENCRYPTION] Encrypted credentials will NOT be decryptable")
/app/backend/server.py.backup_env_connection_20260604_075317:60:            print("[ENCRYPTION] SERVER_SECRET_KEY not configured (development mode)")
/app/backend/server.py.backup_env_connection_20260604_075317:364:def decrypt_server_secrets(server: Optional[Dict]) -> Optional[Dict]:
/app/backend/server.py.backup_env_connection_20260604_075317:382:        from core.secret_manager import decrypt_secret, is_encrypted_secret
/app/backend/server.py.backup_env_connection_20260604_075317:387:            server['password'] = decrypt_secret(password)
/app/backend/server.py.backup_env_connection_20260604_075317:395:            server['api_key'] = decrypt_secret(api_key)
/app/backend/server.py.backup_env_connection_20260604_075317:800:        conn = pymssql.connect(
/app/backend/server.py.backup_env_connection_20260604_075317:887:        conn = pymssql.connect(
/app/backend/server.py.backup_env_connection_20260604_075317:971:        conn = pymssql.connect(
/app/backend/server.py.backup_env_connection_20260604_075317:1052:        conn = pymssql.connect(
/app/backend/server.py.backup_env_connection_20260604_075317:1207:async def test_api_connection(request: TestApiRequest):
/app/backend/server.py.backup_env_connection_20260604_075317:1566:#   - execute_sql_query()
/app/backend/server.py.backup_env_connection_20260604_075317:1568:#   - parse_sql_server_host()
/app/backend/server.py.backup_env_connection_20260604_075317:1580:    execute_sql_query,
/app/backend/server.py.backup_env_connection_20260604_075317:1582:    parse_sql_server_host,
/app/backend/server.py.backup_env_connection_20260604_075317:2113:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}))
/app/backend/server.py.backup_env_connection_20260604_075317:2128:        result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:2350:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:2351:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py.backup_env_connection_20260604_075317:2365:        results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:2448:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py.backup_env_connection_20260604_075317:2476:    # ANTES: updated_server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:2516:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:2578:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py.backup_env_connection_20260604_075317:2891:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:2909:                results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:2927:                    almacenes = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:2951:                results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:3000:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:3019:        # FASE 1B: Importar execute_sql_query_params para parametrización segura
/app/backend/server.py.backup_env_connection_20260604_075317:3020:        from core.db import execute_sql_query_params
/app/backend/server.py.backup_env_connection_20260604_075317:3035:                results = execute_sql_query_params(
/app/backend/server.py.backup_env_connection_20260604_075317:3041:                results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:3061:            results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:3074:                results = execute_sql_query_params(
/app/backend/server.py.backup_env_connection_20260604_075317:3080:                results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:3103:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py.backup_env_connection_20260604_075317:3143:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py.backup_env_connection_20260604_075317:3158:            sucursales_sql = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:3381:    from core.db import execute_sql_query
/app/backend/server.py.backup_env_connection_20260604_075317:3409:        unidades_sql = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:3521:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:3557:        results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:3595:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:3670:        results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:3712:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:3835:        results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:3942:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:3943:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py.backup_env_connection_20260604_075317:3962:    results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:3987:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:4006:            categorias = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4018:            familias = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4030:            subfamilias = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4062:            familias = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4075:            subfamilias = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4188:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:4189:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py.backup_env_connection_20260604_075317:4259:                    fecha_result = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], fecha_folio_query)
/app/backend/server.py.backup_env_connection_20260604_075317:4272:                    fecha_result = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], fecha_folio_query)
/app/backend/server.py.backup_env_connection_20260604_075317:4306:            almacen_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4393:            productos = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4439:                ventas_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4484:            movimientos_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4508:            errores_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4598:                inv_detalle = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4836:            fechas_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4903:            almacen_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:4996:            productos_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:5043:            inventarios_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:5158:                movimientos_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:5227:                    ventas_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:5267:                    ventas_temp_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:5494:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:5495:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py.backup_env_connection_20260604_075317:5518:            almacen_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:5584:            result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:5663:            result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:5695:                result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:5749:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:5750:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py.backup_env_connection_20260604_075317:5804:            result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:5873:            result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:6019:        cortes_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:6321:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
/app/backend/server.py.backup_env_connection_20260604_075317:6322:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(request.server_id))
/app/backend/server.py.backup_env_connection_20260604_075317:6590:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:6619:        results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:6667:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:6676:        results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:6697:async def debug_test_connection(params: Dict, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py.backup_env_connection_20260604_075317:6712:    hostname, parsed_port, instance = parse_sql_server_host(host, port)
/app/backend/server.py.backup_env_connection_20260604_075317:6722:        results = execute_sql_query(host, port, database, username, password, query)
/app/backend/server.py.backup_env_connection_20260604_075317:6776:        results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:6814:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py.backup_env_connection_20260604_075317:6831:            almacen_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:6856:        mov_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:6891:        ventas_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:6918:        detalle = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:6938:        detalle_kit = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:6956:        detalle_directas = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:7130:        # ANTES: server = decrypt_server_secrets(await db.servers.find_one(query))
/app/backend/server.py.backup_env_connection_20260604_075317:7135:            server = decrypt_server_secrets(get_server_connection_info_with_secrets(server_id))
/app/backend/server.py.backup_env_connection_20260604_075317:7143:                    server = decrypt_server_secrets(s)
/app/backend/server.py.backup_env_connection_20260604_075317:7173:            results = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:7461:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py.backup_env_connection_20260604_075317:7597:            result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:7631:            result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:7687:        conn = pymssql.connect(
/app/backend/server.py.backup_env_connection_20260604_075317:7846:            result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:7879:            result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:7912:        result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:7936:        result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:7987:        conn = pymssql.connect(
/app/backend/server.py.backup_env_connection_20260604_075317:8090:        result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8124:        result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8175:        result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8255:        almacen_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8295:            inv_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8338:        productos = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8353:            inv_detalle = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8381:        mov_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8415:            ventas_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8431:            salidas_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8449:        inv_final_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8463:            inv_final_detalle = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8481:            ped_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8495:                ped_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8725:                    result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8752:                result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8778:                    result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8807:                    result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8834:                        result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8861:                        result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:8929:        conn = pymssql.connect(
/app/backend/server.py.backup_env_connection_20260604_075317:9030:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
/app/backend/server.py.backup_env_connection_20260604_075317:9031:    server = decrypt_server_secrets(get_server_connection_info_with_secrets(request.server_id))
/app/backend/server.py.backup_env_connection_20260604_075317:9040:            test_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:9084:            tipos_alm_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:9132:                requi_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:9191:                    tipo_result = execute_sql_query(
/app/backend/server.py.backup_env_connection_20260604_075317:9224:                    result_ini = execute_sql_query(
```

## 2. Syncs SoftRestaurant existentes
```text
/app/backend/server.py.backup_env_connection_20260604_075317:97:from catalogo.consultas_softrestaurant import CONSULTAS_SOFTRESTAURANT, ESTRUCTURA_TABLAS_SOFTRESTAURANT
/app/backend/server.py.backup_env_connection_20260604_075317:552:# - FASE 1 MVP: Solo SoftRestaurant (La Estelar, Cienfuegos, 130 Mérida)
/app/backend/server.py.backup_env_connection_20260604_075317:571:from modules.finanzas.repository_softrestaurant import FinanzasRepositorySoftRestaurant
/app/backend/server.py.backup_env_connection_20260604_075317:597:# SOFTRESTAURANT (CF, Estelar, 130 Mid - principal para CxP)
/app/backend/server.py.backup_env_connection_20260604_075317:598:_softrest_repo = FinanzasRepositorySoftRestaurant(None)  # MongoDB eliminado
/app/backend/server.py.backup_env_connection_20260604_075317:641:# MÓDULO PROPINAS TPV: Registrar router de propinas TPV (FASE 1 MVP - Solo SoftRestaurant)
/app/backend/server.py.backup_env_connection_20260604_075317:742:async def admin_sync_compras_manual(
/app/backend/server.py.backup_env_connection_20260604_075317:764:    from core.scheduler.jobs.sync_compras_job import execute_sync_compras
/app/backend/server.py.backup_env_connection_20260604_075317:770:    result = await loop.run_in_executor(None, execute_sync_compras, dry_run)
/app/backend/server.py.backup_env_connection_20260604_075317:776:async def admin_sync_compras_force_unlock(
/app/backend/server.py.backup_env_connection_20260604_075317:848:async def admin_sync_compras_table_counts(
/app/backend/server.py.backup_env_connection_20260604_075317:915:async def admin_sync_compras_validate_columns(
/app/backend/server.py.backup_env_connection_20260604_075317:1030:async def admin_sync_compras_logs(
/app/backend/server.py.backup_env_connection_20260604_075317:1209:    Prueba la conexión a una API local (SoftRestaurant o MPRO).
/app/backend/server.py.backup_env_connection_20260604_075317:1226:        # NO usa tablas específicas de MPRO (Comanda) ni SoftRestaurant (cheques)
/app/backend/server.py.backup_env_connection_20260604_075317:1317:    system_type: str  # "MPRO", "SoftRestaurant", "Otro", "EDARSA_HUB"
/app/backend/server.py.backup_env_connection_20260604_075317:2694:    - SoftRestaurant: E* = EN (entrada), S* = SA (salida)
/app/backend/server.py.backup_env_connection_20260604_075317:2714:    # SoftRestaurant: E* = EN (entrada), S* = SA (salida)
/app/backend/server.py.backup_env_connection_20260604_075317:2945:            # SoftRestaurant NO tiene tabla Sucursal - devolvemos una sucursal virtual con el nombre del servidor
/app/backend/server.py.backup_env_connection_20260604_075317:3065:            logging.info(f"[RBAC-ALMACENES] SoftRestaurant devolvió {len(results)} almacenes (filtrado RBAC)")
/app/backend/server.py.backup_env_connection_20260604_075317:3163:            # SoftRestaurant no tiene tabla Sucursal, crear virtual
/app/backend/server.py.backup_env_connection_20260604_075317:3376:        - system_type: Tipo de sistema (MPRO, SoftRestaurant)
/app/backend/server.py.backup_env_connection_20260604_075317:3458:            # Para SoftRestaurant (single-tenant), sucursal_origen_id debe ser null
/app/backend/server.py.backup_env_connection_20260604_075317:3459:            if system_type == 'SoftRestaurant' and sucursal_origen_id:
/app/backend/server.py.backup_env_connection_20260604_075317:3461:                    f"[UNIDADES_NEGOCIO] Inconsistencia: {u['nombre']} es SoftRestaurant pero tiene sucursal_origen_id={sucursal_origen_id}"
/app/backend/server.py.backup_env_connection_20260604_075317:3505:    Obtiene la lista de almacenes de SoftRestaurant (no requiere sucursal).
/app/backend/server.py.backup_env_connection_20260604_075317:3532:        raise HTTPException(status_code=400, detail="Este endpoint es solo para SoftRestaurant")
/app/backend/server.py.backup_env_connection_20260604_075317:3544:        # Query para obtener almacenes de SoftRestaurant incluyendo el tipo
/app/backend/server.py.backup_env_connection_20260604_075317:3568:        logging.error(f"Error obteniendo almacenes SoftRestaurant: {str(e)}")
/app/backend/server.py.backup_env_connection_20260604_075317:3644:            # FASE 8: Filtro RBAC para SoftRestaurant
/app/backend/server.py.backup_env_connection_20260604_075317:3647:            # Query para SoftRestaurant - fecha en formato YYYY-MM-DD HH:MM:SS
/app/backend/server.py.backup_env_connection_20260604_075317:3685:# INSUMOS PENDIENTES DE DESCARGAR (SoftRestaurant)
/app/backend/server.py.backup_env_connection_20260604_075317:3696:    - SoftRestaurant: Usa tabla inventariopendiente
/app/backend/server.py.backup_env_connection_20260604_075317:3743:            # Query para SoftRestaurant
/app/backend/server.py.backup_env_connection_20260604_075317:3880:            # Para SoftRestaurant
/app/backend/server.py.backup_env_connection_20260604_075317:3977:    Soporta MPRO y SoftRestaurant con equivalencias:
/app/backend/server.py.backup_env_connection_20260604_075317:3979:    - SoftRestaurant: clasificacionventa (CATEGORIA), gruposiclasificacion (FAMILIA), gruposi (SUBFAMILIA)
/app/backend/server.py.backup_env_connection_20260604_075317:4042:            # Para SoftRestaurant:
/app/backend/server.py.backup_env_connection_20260604_075317:4819:            # Análisis de inventario para SoftRestaurant
/app/backend/server.py.backup_env_connection_20260604_075317:4820:            logging.info(f"Generando análisis de inventario SoftRestaurant: {almacen}")
/app/backend/server.py.backup_env_connection_20260604_075317:4919:            # Construir filtros SQL para SoftRestaurant
/app/backend/server.py.backup_env_connection_20260604_075317:5242:                # Estas tablas pueden no existir en todas las instalaciones de SoftRestaurant
/app/backend/server.py.backup_env_connection_20260604_075317:5326:                # Construir strings de folios para SoftRestaurant
/app/backend/server.py.backup_env_connection_20260604_075317:5330:                almacen_nombre_soft = almacen or ''  # El almacén viene como nombre en SoftRestaurant
/app/backend/server.py.backup_env_connection_20260604_075317:5364:            logging.info(f"Reporte SoftRestaurant generado: {len(results)} productos")
/app/backend/server.py.backup_env_connection_20260604_075317:5619:            # Para SoftRestaurant - detectar si es INSUMO o PRESENTACIÓN
/app/backend/server.py.backup_env_connection_20260604_075317:5637:            logging.info(f"Detalle movimientos SoftRestaurant - Código: {producto_codigo}, Almacén: {almacen}, Fechas: {fecha_ini_fmt} a {fecha_fin_fmt}")
/app/backend/server.py.backup_env_connection_20260604_075317:5825:            # Para SoftRestaurant - detalle de ventas usando recetasalmacenes
/app/backend/server.py.backup_env_connection_20260604_075317:5842:            logging.info(f"Detalle ventas SoftRestaurant - Código: {producto_codigo}, Almacén: {almacen}, Fechas: {fecha_ini_fmt} a {fecha_fin_fmt}")
/app/backend/server.py.backup_env_connection_20260604_075317:6001:        else:  # SoftRestaurant
/app/backend/server.py.backup_env_connection_20260604_075317:6528:    Puede filtrar por tipo de sistema (MPRO o SoftRestaurant).
/app/backend/server.py.backup_env_connection_20260604_075317:6543:        result["SoftRestaurant"] = {
/app/backend/server.py.backup_env_connection_20260604_075317:6549:            for nombre, consulta in CONSULTAS_SOFTRESTAURANT.items()
/app/backend/server.py.backup_env_connection_20260604_075317:6566:        result["SoftRestaurant"] = ESTRUCTURA_TABLAS_SOFTRESTAURANT
/app/backend/server.py.backup_env_connection_20260604_075317:6604:        consultas = CONSULTAS_SOFTRESTAURANT
/app/backend/server.py.backup_env_connection_20260604_075317:6973:    Consulta para obtener datos de inventario físico de SoftRestaurant
/app/backend/server.py.backup_env_connection_20260604_075317:7635:            logging.info(f"[COMPRAS-HIBRIDO] ✅ SoftRestaurant LIVE: {len(result)} inventarios")
/app/backend/server.py.backup_env_connection_20260604_075317:7660:    NO conecta a SoftRestaurant/MPRO directamente.
/app/backend/server.py.backup_env_connection_20260604_075317:7883:            logging.info(f"[COMPRAS-HIBRIDO] ✅ SoftRestaurant LIVE: {len(result)} requisiciones")
/app/backend/server.py.backup_env_connection_20260604_075317:7889:            logging.warning(f"Error obteniendo pedidos SoftRestaurant: {e}")
/app/backend/server.py.backup_env_connection_20260604_075317:7960:    NO conecta a SoftRestaurant/MPRO directamente.
/app/backend/server.py.backup_env_connection_20260604_075317:8611:    # SoftRestaurant - Por implementar
/app/backend/server.py.backup_env_connection_20260604_075317:8612:    return {"detail": "SoftRestaurant no implementado aún", "data": [], "count": 0}
/app/backend/server.py.backup_env_connection_20260604_075317:8895:    NO conecta a SoftRestaurant/MPRO directamente.
/app/backend/server.py.backup_env_connection_20260604_075317:8897:    Requiere que el job sync_compras haya llenado las tablas:
/app/backend/server.py.backup_env_connection_20260604_075317:9108:                # Las órdenes de compra en SoftRestaurant usan códigos que pueden ser presentaciones
/app/backend/server.py.backup_env_connection_20260604_075317:10186:    NO conecta a SoftRestaurant/MPRO directamente.
/app/backend/server.py.backup_env_connection_20260604_075317:10188:    Requiere que el job sync_compras haya llenado las tablas:
/app/backend/server.py.backup_env_connection_20260604_075317:10316:    Para SoftRestaurant: ventas directas o a través de recetas.
/app/backend/server.py.backup_env_connection_20260604_075317:10626:            # SoftRestaurant - Usando tabla compras del catálogo
/app/backend/server.py.backup_env_connection_20260604_075317:10720:                    "requisiciones_pendientes": 0,  # SoftRestaurant no tiene este concepto
/app/backend/server.py.backup_env_connection_20260604_075317:10732:                    "system_type": "SoftRestaurant"
/app/backend/server.py.backup_env_connection_20260604_075317:10826:            # SoftRestaurant - Compras por proveedor usando tabla compras
/app/backend/server.py.backup_env_connection_20260604_075317:11551:    - No está hardcodeado a SoftRestaurant/MPRO
/app/backend/server.py.backup_env_connection_20260604_075317:11559:        - sistema_codigo: Código del sistema (MPRO, SOFTRESTAURANT, etc.)
/app/backend/server.py.backup_env_connection_20260604_075317:11596:                WHEN UPPER(sc.system_type) = 'SOFTRESTAURANT_PRO' THEN 'SoftRestaurant Pro'
/app/backend/server.py.backup_env_connection_20260604_075317:11597:                WHEN UPPER(sc.system_type) = 'SOFTRESTAURANT' THEN 'SoftRestaurant Pro'
/app/backend/server.py.backup_env_connection_20260604_075317:11598:                WHEN UPPER(sc.system_type) IN ('SOFT_RESTAURANT', 'SR') THEN 'SoftRestaurant Pro'
/app/backend/server.py.backup_env_connection_20260604_075317:11740:    No limitado a SoftRestaurant. Soporta MPRO, Enterprise, NOMIPAQ, EDARSAHUB, etc.
/app/backend/server.py.backup_env_connection_20260604_075317:11807:    # Query compatible con Enterprise y SoftRestaurant - TOP 500 para metadata completa
/app/backend/server.py.backup_env_connection_20260604_075317:11873:    Funciona para SoftRestaurant, NOMIPAQ, EDARSAHUB, cualquier SQL Server.
/app/backend/server.py.backup_env_connection_20260604_075317:14863:    # SoftRestaurant
/app/backend/server.py.backup_env_connection_20260604_075317:14883:        system_type: Tipo de sistema (SoftRestaurant, MPRO, etc.)
/app/backend/server.py.backup_env_connection_20260604_075317:15125:    sistema: str = Query(default=None),  # SoftRestaurant, MPRO
/app/backend/server.py.backup_env_connection_20260604_075317:15253:            raise HTTPException(status_code=400, detail=f"Esta consulta es para {sistema_consulta}, no para SoftRestaurant")
/app/backend/db/migrations/create_finanzas_kpis_historico.sql:17:        system_type_normalized VARCHAR(50) NOT NULL, -- SOFTRESTAURANT, MANAGEMENTPRO
/app/backend/modules/comercial/service.py:153:            # Mapeo por server_id (para SoftRestaurant sin sucursal)
/app/backend/modules/comercial/service.py:1040:    # SoftRestaurant
/app/backend/modules/comercial/service.py:1041:    "a5547321-1139-4d2b-9d53-182ca737b6b6": {"unidad_negocio_id": "130MID", "nombre": "130° MÉRIDA", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
/app/backend/modules/comercial/service.py:1042:    "6d053c22-523e-48c0-b72b-96081e2d781b": {"unidad_negocio_id": "CIENFUEGOS", "nombre": "CIENFUEGOS", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
/app/backend/modules/comercial/service.py:1043:    "a5ff0e25-f029-43db-b634-d4ac814c904f": {"unidad_negocio_id": "ESTELAR", "nombre": "LA ESTELAR", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
/app/backend/modules/comercial/service.py:1212:    elif system_type.upper() in ['SOFTRESTAURANT', 'SR']:
/app/backend/modules/comercial/service.py:1371:    TABLERO EJECUTIVO - KPIs SoftRestaurant desde EDARSAHUB
/app/backend/modules/comercial/service.py:1402:    nombre = unidad_negocio_nombre or server.get('name', 'SoftRestaurant')
/app/backend/modules/comercial/service.py:1594:    # REGLA CANÓNICA: Misma que SoftRestaurant
/app/backend/modules/comercial/service.py:1817:    # - Usar la misma fuente que SoftRestaurant: Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:1843:        # Usar la misma función que SoftRestaurant para leer de EDARSAHUB
/app/backend/modules/comercial/service.py:2352:# SoftRestaurant. Si la conexión fallaba, mostraba "Sin Datos" aunque EDARSAHUB
/app/backend/modules/comercial/service.py:2378:    NO consulta: Servidores remotos SoftRestaurant
/app/backend/modules/comercial/cache_service.py:14:entre SoftRestaurant y MPRO.
/app/backend/modules/comercial/cache_service.py:89:    SoftRestaurant y MPRO. Esto garantiza que:
/app/backend/modules/comercial/cache_service.py:90:    - SoftRestaurant NO comparta caché con MPRO
/app/backend/modules/comercial/cache_service.py:91:    - MPRO NO comparta caché con SoftRestaurant
/app/backend/modules/comercial/queries/__init__.py:17:- softrestaurant.py: Queries base para servidores SoftRestaurant
/app/backend/modules/comercial/queries/__init__.py:44:# Bloque 2: Query base de ventas SoftRestaurant
/app/backend/modules/comercial/queries/mpro.py:30:DIFERENCIAS CON SOFTRESTAURANT:
/app/backend/modules/comercial/queries/mpro.py:96:# RESULTADO HOMOLOGADO (igual que SoftRestaurant para consistencia)
/app/backend/modules/comercial/queries/mpro.py:134:    DIFERENCIAS VS SOFTRESTAURANT:
/app/backend/modules/comercial/queries/softrestaurant.py:2:EDARSA HUB - Queries Base para SoftRestaurant
/app/backend/modules/comercial/queries/softrestaurant.py:6:Centralizar las queries SQL homologadas para servidores SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:9:TABLAS PRINCIPALES SOFTRESTAURANT:
/app/backend/modules/comercial/queries/softrestaurant.py:56:# Tablas conocidas de SoftRestaurant para validación
/app/backend/modules/comercial/queries/softrestaurant.py:104:    Query base ÚNICA de ventas para SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:139:            error=f"Server {server.get('name')} no es SoftRestaurant (es {system_type})"
/app/backend/modules/comercial/queries/softrestaurant.py:222:    Convierte fecha ISO (YYYY-MM-DD) a formato SoftRestaurant (YYYYMMDD).
/app/backend/modules/comercial/queries/softrestaurant.py:235:    Construye filtro SQL para sucursal en SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:239:    - La columna idestacion puede no existir en algunas versiones de SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:263:    # La columna idestacion en SoftRestaurant tiene IDs como '130GRADOSCAJA', no nombres
/app/backend/modules/comercial/inteligencia_comercial_routes.py:10:- No consulta SoftRestaurant/MPRO en vivo desde dashboard.
/app/backend/modules/comercial/inteligencia_comercial_routes.py:51:    NO conecta a SoftRestaurant, MPRO, MongoDB ni sistemas externos.
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:5:Este modulo contiene componentes legacy que pueden consultar fuentes externas, MongoDB, adaptadores MPRO/SoftRestaurant o configuracion de servidores.
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:39:- APIs SoftRestaurant/MPRO desde endpoints ejecutivos.
/app/backend/modules/comercial/routes.py.bak:179:# remotos (SoftRestaurant/MPRO) desde la UI. Los endpoints afectados devolverán
/app/backend/modules/comercial/routes.py.bak:218:        'job_requerido': 'sync_movimientos',
/app/backend/modules/comercial/routes.py.bak:994:                        logging.warning(f"[BLINDAJE] Error SoftRestaurant {server['name']}: {sr_error}")
/app/backend/modules/comercial/routes.py.bak:1686:            # Para SoftRestaurant: 1 unidad por servidor (sucursal_origen_id es NULL)
/app/backend/modules/comercial/routes.py.bak:1688:            if sid and not suc:  # SoftRestaurant
/app/backend/modules/comercial/routes.py.bak:1700:        2. Resolver desde EDARSAHUB por server_id (SoftRestaurant)
/app/backend/modules/comercial/routes.py.bak:2109:    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
/app/backend/modules/comercial/routes.py.bak:2455:    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
/app/backend/modules/comercial/routes.py.bak:2488:            # clasificacionventa puede no existir en algunas versiones de SoftRestaurant
/app/backend/modules/comercial/routes.py.bak:2668:        # PROHIBIDO: Abrir conexión a SoftRestaurant/MPRO/Enterprise
/app/backend/modules/comercial/routes.py.bak:3296:            # Formato de fecha para SoftRestaurant (YYYYMMDD)
/app/backend/modules/comercial/routes.py.bak:3573:            # Formato YYYYMMDD para SoftRestaurant - usando CONVERT para evitar errores de conversión
/app/backend/modules/comercial/routes.py.bak:3606:            # NOTA: En SoftRestaurant la tabla de detalle es 'cheqdet' (no 'chequedetalle')
/app/backend/modules/comercial/routes.py.bak:3612:    'SoftRestaurant' as categoria,
/app/backend/modules/comercial/routes.py.bak:3659:                logging.warning(f"Precios Constantes SoftRestaurant {server['name']}: Sin datos en período base {periodo_base}")
/app/backend/modules/comercial/routes.py.bak:3690:            logging.info(f"SoftRestaurant - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
/app/backend/modules/comercial/routes.py.bak:4625:    Soporta SoftRestaurant y MPRO.
/app/backend/modules/comercial/routes.py.bak:4839:            # PROHIBIDO: Abrir conexión remota a SoftRestaurant para obtener "último día"
/app/backend/modules/comercial/routes.py.bak:4849:            logging.info(f"[NO-LIVE] SoftRestaurant Query - Período: {f_ini} a {f_fin} (EDARSAHUB-ONLY)")
/app/backend/modules/comercial/routes.py.bak:4914:            # PROHIBIDO: Abrir conexión remota a SoftRestaurant/MPRO/Enterprise
/app/backend/modules/comercial/routes.py.bak:4969:            # MISMO FIX que SoftRestaurant: Usar EDARSAHUB primero.
/app/backend/modules/comercial/repository.py:292:        # Construir condición para sucursal_origen_id (puede ser NULL para SoftRestaurant)
/app/backend/modules/comercial/repository.py:296:            # Para SoftRestaurant sin código, buscar por server_id con sucursal_origen_id NULL
/app/backend/modules/comercial/repository.py:392:    Obtiene ventas de SoftRestaurant para un mes/año específico.
/app/backend/modules/comercial/README_BLINDAJE.md:28:| SoftRestaurant | SQL (cheques+turnos) | SQL (tempcheques) |
/app/backend/modules/comercial/routes.py:179:# remotos (SoftRestaurant/MPRO) desde la UI. Los endpoints afectados devolverán
/app/backend/modules/comercial/routes.py:218:        'job_requerido': 'sync_movimientos',
/app/backend/modules/comercial/routes.py:994:                        logging.warning(f"[BLINDAJE] Error SoftRestaurant {server['name']}: {sr_error}")
```

## 3. Sync Propinas TPV
```text
/app/backend/server.py.backup_env_connection_20260604_075317:557:from modules.finanzas.propinas_tpv import get_router_sql as get_propinas_tpv_router
/app/backend/server.py.backup_env_connection_20260604_075317:645:api_router.include_router(get_propinas_tpv_router())
/app/backend/server.py.backup_env_connection_20260604_075317:649:# Fuente de verdad: EDARSAHUB.propinas_tpv_control
/app/backend/server.py.backup_env_connection_20260604_075317:650:from modules.finanzas.propinas_tpv import get_router_edarsahub as get_propinas_tpv_edarsahub_router
/app/backend/server.py.backup_env_connection_20260604_075317:651:api_router.include_router(get_propinas_tpv_edarsahub_router())
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:205:                    TotalPropinasTPV, TotalPropinasEfectivo, TotalRetiros, FondoInicial,
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:286:                data.get('total_propinas_tpv', 0),
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:760:                'propinas_tpv': float(row.get('TotalPropinasTPV') or 0),
/app/backend/modules/finanzas/carga_historica_propinas_tpv.py:12:- EDARSAHUB.propinas_tpv_control
/app/backend/modules/finanzas/carga_historica_propinas_tpv.py:13:- EDARSAHUB.Finanzas_PropinasTPV_SyncLog
/app/backend/modules/finanzas/carga_historica_propinas_tpv.py:108:    from modules.finanzas.sync_propinas_softrestaurant import sincronizar_propinas_softrestaurant
/app/backend/modules/finanzas/carga_historica_propinas_tpv.py:239:    from modules.finanzas.sync_propinas_mpro import sincronizar_propinas_mpro
/app/backend/modules/finanzas/sync_propinas_mpro.py:5:y las sincroniza hacia EDARSAHUB.propinas_tpv_control.
/app/backend/modules/finanzas/sync_propinas_mpro.py:21:- EDARSAHUB.propinas_tpv_control
/app/backend/modules/finanzas/sync_propinas_mpro.py:22:- EDARSAHUB.Finanzas_PropinasTPV_SyncLog
/app/backend/modules/finanzas/sync_propinas_mpro.py:213:def extraer_propinas_tpv_mpro(
/app/backend/modules/finanzas/sync_propinas_mpro.py:310:                # Fechas - Usar folio_comanda + Cp_ID para unicidad (UK_propinas_tpv_corte)
/app/backend/modules/finanzas/sync_propinas_mpro.py:318:                'propinas_tpv': Decimal(str(row['Cp_Propina'] or 0)),
/app/backend/modules/finanzas/sync_propinas_mpro.py:370:    Carga propinas TPV de MPRO en EDARSAHUB.propinas_tpv_control
/app/backend/modules/finanzas/sync_propinas_mpro.py:378:            'total_propinas_tpv': Decimal('0')
/app/backend/modules/finanzas/sync_propinas_mpro.py:389:        'total_propinas_tpv': Decimal('0')
/app/backend/modules/finanzas/sync_propinas_mpro.py:397:                    SELECT id FROM propinas_tpv_control 
/app/backend/modules/finanzas/sync_propinas_mpro.py:407:                        INSERT INTO propinas_tpv_control (
/app/backend/modules/finanzas/sync_propinas_mpro.py:411:                            propinas_tpv, ventas_tarjeta, ventas_totales, ventas_efectivo,
/app/backend/modules/finanzas/sync_propinas_mpro.py:435:                        float(registro['propinas_tpv']),
/app/backend/modules/finanzas/sync_propinas_mpro.py:462:                    stats['total_propinas_tpv'] += registro['propinas_tpv']
/app/backend/modules/finanzas/sync_propinas_mpro.py:480:def registrar_synclog_propinas_mpro(
/app/backend/modules/finanzas/sync_propinas_mpro.py:489:    """Registra en Finanzas_PropinasTPV_SyncLog"""
/app/backend/modules/finanzas/sync_propinas_mpro.py:496:            INSERT INTO Finanzas_PropinasTPV_SyncLog (
/app/backend/modules/finanzas/sync_propinas_mpro.py:502:                TotalPropinasTPV, Estatus, ErrorMensaje, TipoEjecucion
/app/backend/modules/finanzas/sync_propinas_mpro.py:520:            float(stats.get('total_propinas_tpv', 0)),
/app/backend/modules/finanzas/sync_propinas_mpro.py:528:        cursor.execute("SELECT MAX(LogID) FROM Finanzas_PropinasTPV_SyncLog")
/app/backend/modules/finanzas/sync_propinas_mpro.py:561:    logger.info(f"[SYNC_PROPINAS_MPRO] === Iniciando sync de propinas TPV: {unidad_nombre} ===")
/app/backend/modules/finanzas/sync_propinas_mpro.py:599:        registros = extraer_propinas_tpv_mpro(conn_info, fecha_desde, fecha_hasta)
/app/backend/modules/finanzas/sync_propinas_mpro.py:603:        suma_origen = sum(r['propinas_tpv'] for r in registros)
/app/backend/modules/finanzas/sync_propinas_mpro.py:613:            formas_pago[fp]['total'] += r['propinas_tpv']
/app/backend/modules/finanzas/sync_propinas_mpro.py:639:        log_id = registrar_synclog_propinas_mpro(
/app/backend/modules/finanzas/sync_propinas_mpro.py:652:                    'PropinasTPV': float(r['propinas_tpv']),
/app/backend/modules/finanzas/sync_propinas_mpro.py:665:            registrar_synclog_propinas_mpro(
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:5:y las sincroniza hacia EDARSAHUB.propinas_tpv_control.
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:16:- EDARSAHUB.propinas_tpv_control
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:17:- EDARSAHUB.Finanzas_PropinasTPV_SyncLog
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:273:def extraer_propinas_tpv_softrestaurant(
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:344:            # Construir registro para propinas_tpv_control
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:369:                'propinas_tpv': Decimal(str(row.get('propinatarjeta', 0) or 0)),
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:421:    Carga propinas TPV en EDARSAHUB.propinas_tpv_control
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:431:            'total_propinas_tpv': Decimal('0')
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:442:        'total_propinas_tpv': Decimal('0')
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:450:                    SELECT id FROM propinas_tpv_control 
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:462:                        INSERT INTO propinas_tpv_control (
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:466:                            propinas_tpv, ventas_tarjeta, ventas_totales, ventas_efectivo,
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:490:                        float(registro['propinas_tpv']),
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:517:                    stats['total_propinas_tpv'] += registro['propinas_tpv']
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:535:def registrar_synclog_propinas(
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:544:    """Registra en Finanzas_PropinasTPV_SyncLog"""
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:551:            INSERT INTO Finanzas_PropinasTPV_SyncLog (
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:557:                TotalPropinasTPV, Estatus, ErrorMensaje, TipoEjecucion
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:576:            float(stats.get('total_propinas_tpv', 0)),
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:585:        cursor.execute("SELECT MAX(LogID) FROM Finanzas_PropinasTPV_SyncLog")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:618:    logger.info(f"[SYNC_PROPINAS_SR] === Iniciando sync de propinas TPV: {unidad_nombre} ===")
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:658:        registros = extraer_propinas_tpv_softrestaurant(conn_info, fecha_desde, fecha_hasta)
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:662:        suma_origen = sum(r['propinas_tpv'] for r in registros)
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:684:        log_id = registrar_synclog_propinas(
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:697:                    'PropinasTPV': float(r['propinas_tpv']),
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:710:            registrar_synclog_propinas(
/app/backend/modules/finanzas/propinas_tpv/service.py:20:from .repository import PropinasTPVRepository
/app/backend/modules/finanzas/propinas_tpv/service.py:32:class PropinasTPVService:
/app/backend/modules/finanzas/propinas_tpv/service.py:47:        self.repository = PropinasTPVRepository(db)
/app/backend/modules/finanzas/propinas_tpv/service.py:49:    async def sincronizar_propinas(
/app/backend/modules/finanzas/propinas_tpv/service.py:146:                    propinas_tpv = propinas_totales
/app/backend/modules/finanzas/propinas_tpv/service.py:149:                    comision = round(propinas_tpv * porcentaje_comision, 2)
/app/backend/modules/finanzas/propinas_tpv/service.py:150:                    monto_a_pagar = round(propinas_tpv - comision, 2)
/app/backend/modules/finanzas/propinas_tpv/service.py:173:                            'propinas_tpv': propinas_tpv,
/app/backend/modules/finanzas/propinas_tpv/service.py:233:    async def obtener_propinas(
/app/backend/modules/finanzas/propinas_tpv/service.py:267:            'total_propinas_tpv': sum(p['origen']['propinas_tpv'] for p in propinas),
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:14:1. propinas_tpv_control - Registro principal de propinas
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:15:2. propinas_tpv_config - Configuración jerárquica
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:16:3. propinas_tpv_historial - Auditoría de cambios
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:25:-- TABLA: propinas_tpv_control
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:30:IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'propinas_tpv_control')
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:32:    CREATE TABLE propinas_tpv_control (
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:56:        propinas_tpv            DECIMAL(18,2)       NOT NULL DEFAULT 0,
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:119:        CONSTRAINT PK_propinas_tpv_control 
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:122:        CONSTRAINT UK_propinas_tpv_corte 
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:134:    ON propinas_tpv_control (fecha_corte DESC, cuadre_estado);
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:137:    ON propinas_tpv_control (server_id, fecha_corte DESC);
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:140:    ON propinas_tpv_control (cuadre_estado, fecha_corte DESC);
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:143:    ON propinas_tpv_control (pago_usuario_id, cuadre_usuario_id);
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:145:    PRINT 'Tabla propinas_tpv_control creada exitosamente';
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:149:    PRINT 'Tabla propinas_tpv_control ya existe';
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:155:-- TABLA: propinas_tpv_config
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:160:IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'propinas_tpv_config')
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:162:    CREATE TABLE propinas_tpv_config (
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:209:        CONSTRAINT PK_propinas_tpv_config 
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:218:    ON propinas_tpv_config (alcance_tipo, alcance_server_id, activa);
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:220:    PRINT 'Tabla propinas_tpv_config creada exitosamente';
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:224:    PRINT 'Tabla propinas_tpv_config ya existe';
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:230:-- TABLA: propinas_tpv_historial
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:234:IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'propinas_tpv_historial')
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py:236:    CREATE TABLE propinas_tpv_historial (
```

## 4. Uso de execute_sql_query por archivo
```text
    120 /app/backend/server.py.backup_pre_fase2a
    120 /app/backend/server.py.backup_env_connection_20260604_075317
    120 /app/backend/server.py.backup_before_corporate_filters_20260603_070655
    120 /app/backend/server.py
     32 /app/backend/modules/comercial/routes.py.bak
     24 /app/backend/modules/comercial/routes.py
     21 /app/backend/modules/sync_recetas/sync_recetas.py
     19 /app/backend/modules/costos_margenes/repository.py
     15 /app/backend/modules/comercial/services/listas_competidores_service.py
     15 /app/backend/modules/comercial/services/competidores_service.py
     14 /app/backend/modules/catalogos/routes.py
     13 /app/backend/modules/comercial/services/competidores_enterprise_service.py
     12 /app/backend/modules/comercial/services/benchmark_service.py
     10 /app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py
     10 /app/backend/modules/comercial/alertas_margen_repository.py
      9 /app/backend/modules/costos_margenes/repository_precios.py
      9 /app/backend/modules/comercial/services/metricas_ia_service.py
      9 /app/backend/modules/api_connections/repository.py
      8 /app/backend/modules/compras/repository.py
      8 /app/backend/modules/comercial/services/perfil_unidad_service.py
      6 /app/backend/scripts/ddl_costos_alertas_001b.py
      6 /app/backend/modules/comercial_v2/carga_historica_abril_2026.py
      6 /app/backend/modules/comercial_v2/carga_historica_24_meses.py
      6 /app/backend/modules/comercial/services/precios_vinos_service.py
      6 /app/backend/modules/comercial/service.py
      6 /app/backend/modules/comercial/repository.py
      6 /app/backend/core/server_registry.py
      5 /app/backend/modules/comercial/services/pricing_sugerido_service.py
      5 /app/backend/modules/comercial/services/impuestos_service.py
      5 /app/backend/core/providers.py
      4 /app/backend/modules/sync_historicos/sync_ventas.py
      4 /app/backend/modules/sync_historicos/service.py
      4 /app/backend/modules/comercial/services/pricing_ai_service.py
      4 /app/backend/core/db.py
      3 /app/backend/tools/test_sql_connection_from_servidores.py
      3 /app/backend/tools/sync_sales_dry_run.py
      3 /app/backend/modules/consultas_sql/routes.py
      3 /app/backend/modules/comercial_v2/sync_comercial_edarsahub.py
      3 /app/backend/modules/comercial/queries/mpro.py
      3 /app/backend/core/scheduler/jobs/inventarios_detector_job.py
      2 /app/backend/scripts/rotate_server_secret_key.py
      2 /app/backend/scripts/fase_sync_3a_r2_pordiasemana.py
      2 /app/backend/scripts/encrypt_existing_server_secrets.py
      2 /app/backend/scripts/encrypt_core_server_secrets.py
      2 /app/backend/modules/finanzas/propinas_tpv/repository.py
      2 /app/backend/modules/finanzas/health.py
      2 /app/backend/modules/costos_margenes/routes.py
      2 /app/backend/htmlcov/z_57760688d1f824db_db_py.html
      2 /app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py
      2 /app/backend/core/connection_resolver.py
      2 /app/backend/api/admin_core_connections.py
      1 /app/backend/tools/validate_server_secret_key.py
      1 /app/backend/tests/test_core_db.py
      1 /app/backend/tests/test_bloque3_paridad_mpro.py
      1 /app/backend/tests/test_bloque2_paridad.py
      1 /app/backend/scripts/validate_encrypted_server_connectivity.py
      1 /app/backend/scripts/precheck_conectividad.py
      1 /app/backend/scripts/ddl_competidores_nuevos_campos.py
      1 /app/backend/scripts/ddl_competidores_enterprise_unidad.py
      1 /app/backend/scripts/create_unidades_negocio_table.py
      1 /app/backend/modules/sync_historicos/repository.py
      1 /app/backend/modules/rh/repository.py
      1 /app/backend/modules/rh/importador/repository.py
      1 /app/backend/modules/finanzas/tesoreria.py
      1 /app/backend/modules/finanzas/repository_real.py
      1 /app/backend/modules/finanzas/repository_cortes_z.py
      1 /app/backend/modules/finanzas/repository_bancarios.py
      1 /app/backend/modules/finanzas/propinas_tpv/sql_repository.py
      1 /app/backend/modules/finanzas/propinas_tpv/schema_detector.py
      1 /app/backend/modules/corporate_filters/router.py.backup_versiones_20260604_163017
      1 /app/backend/modules/corporate_filters/router.py.backup_mapeo_real_20260604_164525
      1 /app/backend/modules/corporate_filters/router.py.backup_admin_versiones_20260604_163329
      1 /app/backend/modules/corporate_filters/router.py
      1 /app/backend/modules/consultas_sql/repository.py
      1 /app/backend/modules/configuracion/services/almacenes_sync_service.py
      1 /app/backend/modules/comercial_v2/repository_readonly.py
      1 /app/backend/modules/comercial_v2/repository_comercial_edarsahub.py
      1 /app/backend/modules/comercial/queries/softrestaurant.py
      1 /app/backend/modules/comercial/historical_kpis_repository.py
      1 /app/backend/modules/catalogos/repository.py
      1 /app/backend/htmlcov/z_57760688d1f824db_pool_py.html
      1 /app/backend/htmlcov/z_57760688d1f824db___init___py.html
      1 /app/backend/core/system_capability_resolver.py
      1 /app/backend/core/scheduler/jobs/sync_compras_job.py.backup_20260604_072402
      1 /app/backend/core/scheduler/jobs/sync_compras_job.py
      1 /app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py
      1 /app/backend/core/pool.py
      1 /app/backend/core/empresa_resolver.py
      1 /app/backend/core/__init__.py
      1 /app/backend/api/catalogos_sistemas.py
      1 /app/backend/api/admin_data_quality.py
```

## 5. Contexto sync_service
```text
/app/backend/api/admin_core_connections.py
/app/backend/api/admin_scheduler_resync.py
/app/backend/api/sync_receiver.py
/app/backend/api/sync_schemas.py
/app/backend/catalogo/consultas_softrestaurant.py
/app/backend/core/connection_resolver.py
/app/backend/core/guards/server_secret_guard.py
/app/backend/core/scheduler/jobs/crm_sync_job.py
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py
/app/backend/core/scheduler/jobs/sync_compras_job.py
/app/backend/core/scheduler/jobs/sync_ingresos_job.py
/app/backend/core/scheduler/jobs/sync_nightly_comercial_job.py
/app/backend/core/scheduler/jobs/sync_propinas_tpv_job.py
/app/backend/core/scheduler/jobs/sync_short_comercial_job.py
/app/backend/core/scheduler/jobs/vtiger_sync_job.py
/app/backend/core/server_registry.py
/app/backend/modules/api_connections/__init__.py
/app/backend/modules/api_connections/repository.py
/app/backend/modules/api_connections/routes.py
/app/backend/modules/api_connections/universal_test_routes.py
/app/backend/modules/automatizacion/queries_soft.py
/app/backend/modules/comercial/queries/softrestaurant.py
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py
/app/backend/modules/compras/adapters/softrestaurant_pro_adapter.py
/app/backend/modules/compras/sync_service.py
/app/backend/modules/configuracion/services/almacenes_sync_service.py
/app/backend/modules/crm/integration/sync_engine.py
/app/backend/modules/finanzas/__init__.py
/app/backend/modules/finanzas/carga_historica_ingresos.py
/app/backend/modules/finanzas/carga_historica_propinas_tpv.py
/app/backend/modules/finanzas/cuentas_bancarias.py
/app/backend/modules/finanzas/cuentas_por_pagar.py
/app/backend/modules/finanzas/health.py
/app/backend/modules/finanzas/historical_kpis_repository.py
/app/backend/modules/finanzas/ingresos.py
/app/backend/modules/finanzas/models_bancarios.py
/app/backend/modules/finanzas/propinas_tpv/__init__.py
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py
/app/backend/modules/finanzas/propinas_tpv/models.py
/app/backend/modules/finanzas/propinas_tpv/repository.py
/app/backend/modules/finanzas/propinas_tpv/repository_edarsahub.py
/app/backend/modules/finanzas/propinas_tpv/routes.py
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py
/app/backend/modules/finanzas/propinas_tpv/schema_detector_subprocess.py
/app/backend/modules/finanzas/propinas_tpv/service.py
/app/backend/modules/finanzas/propinas_tpv/service_sql.py
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py
/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py
/app/backend/modules/finanzas/repository.py
/app/backend/modules/finanzas/repository_bancarios.py
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py
/app/backend/modules/finanzas/repository_cortes_z.py
/app/backend/modules/finanzas/repository_cuadres_z.py
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py
/app/backend/modules/finanzas/repository_ingresos_edarsahub.py
/app/backend/modules/finanzas/repository_mpro.py
/app/backend/modules/finanzas/repository_real.py
/app/backend/modules/finanzas/repository_softrestaurant.py
/app/backend/modules/finanzas/saldos_bancarios.py
/app/backend/modules/finanzas/sql_query_worker.py
/app/backend/modules/finanzas/sql_query_worker_secure.py
/app/backend/modules/finanzas/sql_subprocess_helper.py
/app/backend/modules/finanzas/sync_cortes_mpro.py
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py
/app/backend/modules/finanzas/sync_propinas_mpro.py
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py
/app/backend/modules/finanzas/tesoreria.py
/app/backend/modules/finanzas/tesoreria_models.py
/app/backend/modules/finanzas/test_conn_cienfuegos.py
/app/backend/modules/finanzas/utils_bancarios.py
/app/backend/modules/sync_historicos/__init__.py
/app/backend/modules/sync_historicos/models.py
/app/backend/modules/sync_historicos/repository.py
/app/backend/modules/sync_historicos/service.py
/app/backend/modules/sync_historicos/sync_ventas.py
/app/backend/modules/sync_recetas/__init__.py
/app/backend/modules/sync_recetas/models.py
/app/backend/modules/sync_recetas/sync_recetas.py
/app/backend/modules/tablajeria/sync_service.py
/app/backend/scripts/encrypt_core_server_secrets.py
/app/backend/scripts/encrypt_existing_server_secrets.py
/app/backend/scripts/fase_sync_3a_r2_pordiasemana.py
/app/backend/scripts/paquete_piloto_sync_agent/sync_agent_piloto.py
/app/backend/scripts/reconcile_servers_sql_mongo.py
/app/backend/scripts/rotate_server_secret_key.py
/app/backend/scripts/run_historical_load_finanzas.py
/app/backend/scripts/sync_agent_piloto.py
/app/backend/scripts/sync_response_cache_finops.py
/app/backend/scripts/validacion_propinas_tpv.py
/app/backend/scripts/validate_encrypted_server_connectivity.py
/app/backend/server.py
/app/backend/tests/test_dashboard_servers.py
/app/backend/tests/test_servers.py
/app/backend/tests/test_softrestaurant_inventory.py
/app/backend/tools/check_mpro_server_config.py
/app/backend/tools/sync_sales_dry_run.py
/app/backend/tools/test_sql_connection_from_servidores.py
/app/backend/tools/validate_server_secret_key.py
/app/scripts/audit_live_connections.sh
/app/scripts/run_sync_sales_dry_run_backfill_7_dias.sh
/app/scripts/run_sync_sales_dry_run_todas_unidades.sh
/app/scripts/validar_server_secret_key_edarsahub.sh
/app/scripts/validate_sync_sales_softrestaurant_legacy_rules.sh
```

## 6. Fragmentos relevantes
