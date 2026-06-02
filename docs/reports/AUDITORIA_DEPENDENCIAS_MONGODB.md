# Auditoría de Dependencias MongoDB

Generado: 2026-06-02T09:30:23+00:00

## Coincidencias en backend/frontend/docs

```text
/app/backend/init_queries.py:4:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/init_queries.py:10:mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/init_queries.py:266:    client = AsyncIOMotorClient(mongo_url)
/app/backend/init_queries.py:270:    existing = await db.queries.count_documents({})
/app/backend/init_queries.py:287:        await db.queries.insert_one(query_doc)
/app/backend/init_queries.py:291:    admin_exists = await db.users.count_documents({"role": "Administrador"})
/app/backend/init_queries.py:306:        await db.users.insert_one(admin_user)
/app/backend/migrar_a_sql.py:24:            if 'pymongo' not in linea and 'motor' not in linea:
/app/backend/migrar_a_sql.py:26:    print("✅ Limpiado: requirements.txt (eliminado pymongo/motor)")
/app/backend/migrar_a_sql.py:28:# 3. Centralización del motor SQL en db.py
/app/backend/migrar_a_sql.py:39:with open('backend/core/db.py', 'w') as f:
/app/backend/migrar_a_sql.py:41:print("✅ Actualizado: core/db.py ahora es SQL-Only")
/app/backend/limpiar_tests_dns.py:4:test_path = 'backend/tests/test_core_db.py'
/app/backend/limpiar_tests_dns.py:18:    print("✅ Tests de DNS marcados como skip en test_core_db.py")
/app/backend/limpiar_tests_dns.py:20:# 2. LIMPIEZA DE CÓDIGO INNECESARIO EN db.py
/app/backend/limpiar_tests_dns.py:21:db_path = 'backend/core/db.py'
/app/backend/limpiar_tests_dns.py:30:print("✅ Eliminada lógica obsoleta de hosts externos en db.py")
/app/backend/limpiar_tests_dns.py:37:        f.write("- Eliminación definitiva de dependencias MongoDB.\n")
/app/backend/db/migrations/create_comercial_kpis_historico.sql:12:-- MongoDB queda solo como checkpoint/log/cache/staging temporal.
/app/backend/db/migrations/create_comercial_kpis_historico.sql:15:-- EDARSAHUB SQL es el cerebro. MongoDB NO es destino final.
/app/backend/modules/comercial/service.py:77:# NO consulta servidores locales ni MongoDB para KPIs.
/app/backend/modules/comercial/service.py:93:# NO usar MongoDB como fuente funcional para unidades.
/app/backend/modules/comercial/service.py:102:    NO usa MongoDB.
/app/backend/modules/comercial/service.py:180:    NO usa MongoDB.
/app/backend/modules/comercial/service.py:201:    # Si no se encuentra, retornar estructura vacía (no usar MongoDB)
/app/backend/modules/comercial/service.py:477:    NO usa MongoDB. NO usa servidores locales.
/app/backend/modules/comercial/service.py:804:    - NO consulta MongoDB
/app/backend/modules/comercial/service.py:1185:    - NO usa MongoDB servers.name como nombre oficial
/app/backend/modules/comercial/service.py:1197:    # NO usar MongoDB servers.name como nombre funcional/oficial
/app/backend/modules/comercial/service.py:1366:# - NO consultan MongoDB como fuente de datos
/app/backend/modules/comercial/service.py:1377:    - NO consulta MongoDB
/app/backend/modules/comercial/service.py:1381:    - NO usa MongoDB servers.name como nombre oficial
/app/backend/modules/comercial/service.py:1394:    # NO usar MongoDB servers.name como nombre oficial
/app/backend/modules/comercial/service.py:1507:    - NO consulta MongoDB
/app/backend/modules/comercial/service.py:2379:    NO consulta: MongoDB
/app/backend/modules/comercial/routes_pricing_ai.py:16:- NO usar MongoDB
/app/backend/modules/comercial/routes_pricing_ai.py:396:            "mongodb": False,
/app/backend/modules/comercial/routes_pricing_ai.py:432:    - NO usa MongoDB
/app/backend/modules/comercial/cache_service.py:25:# Importar db desde server.py (motor async client)
/app/backend/modules/comercial/cache_service.py:33:# Referencia global a MongoDB (evita circular import con server.py)
/app/backend/modules/comercial/cache_service.py:38:    DEPRECADO: MongoDB ya no se usa.
/app/backend/modules/comercial/cache_service.py:44:    logging.warning("[COMERCIAL] Cache service - MongoDB deprecado, funcionalidad limitada")
/app/backend/modules/comercial/cache_service.py:48:    DEPRECADO: MongoDB ya no se usa.
/app/backend/modules/comercial/cache_service.py:54:        logging.debug("[COMERCIAL] get_db() - MongoDB deprecado")
/app/backend/modules/comercial/cache_service.py:135:        cached = await db.comercial_cache.find_one({"cache_key": cache_key})
/app/backend/modules/comercial/cache_service.py:201:        await db.comercial_cache.update_one(
/app/backend/modules/comercial/cache_service.py:341:        await db.comercial_cache.create_index("cache_key", unique=True)
/app/backend/modules/comercial/cache_service.py:342:        await db.comercial_cache.create_index("cached_at")
/app/backend/modules/comercial/cache_service.py:363:        total_before = await db.comercial_cache.count_documents({})
/app/backend/modules/comercial/cache_service.py:366:        result = await db.comercial_cache.delete_many({
/app/backend/modules/comercial/cache_service.py:371:        result2 = await db.comercial_cache.delete_many({
/app/backend/modules/comercial/cache_service.py:376:        total_after = await db.comercial_cache.count_documents({})
/app/backend/modules/comercial/cache_service.py:409:        total_entries = await db.comercial_cache.count_documents({})
/app/backend/modules/comercial/cache_service.py:417:        async for doc in db.comercial_cache.aggregate(pipeline):
/app/backend/modules/comercial/cache_service.py:421:        oldest = await db.comercial_cache.find_one(sort=[("cached_at", 1)])
/app/backend/modules/comercial/cache_service.py:422:        newest = await db.comercial_cache.find_one(sort=[("cached_at", -1)])
/app/backend/modules/comercial/__init__.py:12:- repository.py: Queries SQL y acceso a MongoDB
/app/backend/modules/comercial/__init__.py:53:    Inicializa el módulo comercial con la conexión a MongoDB.
/app/backend/modules/comercial/__init__.py:56:        database: Instancia de AsyncIOMotorDatabase
/app/backend/modules/comercial/queries/hub.py:2:EDARSA HUB - Lecturas desde EDARSA HUB (MongoDB)
/app/backend/modules/comercial/queries/hub.py:9:COLECCIONES MONGODB:
/app/backend/modules/comercial/queries/hub.py:59:# Los imports de MongoDB se agregarán cuando se implemente
/app/backend/modules/comercial/queries/hub.py:60:# from core.db import get_mongo_db
/app/backend/modules/comercial/queries/hub.py:67:COLLECTION_KPIS = "kpis_comercial"
/app/backend/modules/comercial/queries/hub.py:70:COLLECTION_CACHE = "dashboard_cache"
/app/backend/modules/comercial/queries/hub.py:73:COLLECTION_STATUS = "server_status"
/app/backend/modules/comercial/queries/hub.py:168:    Construye filtro MongoDB para consultas de KPIs.
/app/backend/modules/comercial/queries/hub.py:178:        Dict filtro para MongoDB find()
/app/backend/modules/comercial/queries/mpro.py:24:- Todas retornan SafeQueryResult del core/db.py
/app/backend/modules/comercial/queries/softrestaurant.py:26:- Todas retornan SafeQueryResult del core/db.py
/app/backend/modules/comercial/routes_precios_sugeridos.py:11:- CERO MongoDB
/app/backend/modules/comercial/crm_router.py:202:    # Nota: Se asume que el sistema genera el folio secuencial o via el motor SQL.
/app/backend/modules/comercial/inteligencia_comercial_routes.py:9:- No usa MongoDB como fuente de datos comerciales.
/app/backend/modules/comercial/alertas_margen_service.py:4:EDARSAHUB SQL es el cerebro. CERO MongoDB.
/app/backend/modules/comercial/alertas_margen_service.py:402:    NOTA: Este es un endpoint de prueba. El motor de evaluación masiva
/app/backend/modules/comercial/alertas_margen_repository.py:4:EDARSAHUB SQL es el cerebro. CERO MongoDB.
/app/backend/modules/comercial/routes_pricing_ia.py:610:    Tipos de motor disponibles:
/app/backend/modules/comercial/routes_pricing_ia.py:622:    Para vinos, use tipo_motor=VINOS_RANGOS.
/app/backend/modules/comercial/routes_pricing_ia.py:629:        f"motor={request.tipo_motor.value} estado={resultado.estado.value}"
/app/backend/modules/comercial/routes.py.bak:1165:                        # Para modo HUB, NO usar caché MongoDB como fallback.
/app/backend/modules/comercial/routes.py.bak:1167:                        # MongoDB NO debe ser fuente productiva de datos.
/app/backend/modules/comercial/routes.py.bak:1170:                            # HUB: Reportar error SQL, NO usar caché MongoDB
/app/backend/modules/comercial/routes.py.bak:1171:                            logging.warning(f"[HUB-EDARSAHUB-ERROR] {server['name']}: Error leyendo EDARSAHUB SQL - NO hay fallback MongoDB")
/app/backend/modules/comercial/routes.py.bak:1189:                            # LIVE-C: Mantener fallback a caché MongoDB (conexión real fallida)
/app/backend/modules/comercial/routes.py.bak:1678:    # FUENTE: EDARSAHUB.Unidades_Negocio (NO MongoDB)
/app/backend/modules/comercial/routes.py.bak:2984:    # ARQUITECTURA: Obtener nombre de unidad desde EDARSAHUB (primario) o MongoDB (LEGACY_FALLBACK)
/app/backend/modules/comercial/routes.py.bak:2986:    if nombre_source == 'MONGO_LEGACY_FALLBACK':
/app/backend/modules/comercial/routes.py.bak:2987:        logging.warning(f"[LEGACY_FALLBACK] Mesas: Nombre de sucursal {sucursal} obtenido de MongoDB")
/app/backend/modules/comercial/routes.py.bak:3048:            # BLINDAJE: Usar nombre obtenido de MongoDB
/app/backend/modules/comercial/routes.py.bak:3159:            # BLINDAJE MPRO: Usar nombre de MongoDB (ya obtenido arriba), con fallback a SQL si no se encontró
/app/backend/modules/comercial/routes.py.bak:3161:            # Si MongoDB no encontró el nombre (aún es server['name']), intentar con SQL
/app/backend/modules/comercial/rentabilidad.py:7:    COSTOS-ALERTAS-001-E: Motor de evaluación de rentabilidad local.
/app/backend/modules/comercial/routes_listas_competidores.py:8:- CERO MongoDB
/app/backend/modules/comercial/routes_alertas_margen.py:4:EDARSAHUB SQL es el cerebro. CERO MongoDB.
/app/backend/modules/comercial/routes_alertas_margen.py:281:    NOTA: Este es un endpoint de prueba. El motor de evaluación masiva
/app/backend/modules/comercial/repository.py:7:- ELIMINADA dependencia de MongoDB completamente
/app/backend/modules/comercial/repository.py:9:- execute_hub_query como motor central
/app/backend/modules/comercial/repository.py:45:# DEPRECADO: MongoDB ya no se usa (Mayo 2026)
/app/backend/modules/comercial/repository.py:49:    """DEPRECADO: MongoDB eliminado. No hace nada."""
/app/backend/modules/comercial/repository.py:54:    """DEPRECADO: MongoDB eliminado. Retorna None siempre."""
/app/backend/modules/comercial/repository.py:82:    Garantiza paridad estructural con el esquema original de MongoDB.
/app/backend/modules/comercial/repository.py:153:        WHERE (id = '{server_id}' OR mongodb_id = '{server_id}')
/app/backend/modules/comercial/repository.py:205:    MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.
/app/backend/modules/comercial/repository.py:218:    MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.
/app/backend/modules/comercial/repository.py:327:    MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.
/app/backend/modules/comercial/historical_kpis_repository.py:8:EDARSAHUB SQL es el cerebro. MongoDB NO es destino final de históricos.
/app/backend/modules/comercial/historical_kpis_repository.py:51:    """Obtiene credenciales de EDARSAHUB desde MongoDB servers."""
/app/backend/modules/comercial/historical_kpis_repository.py:57:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/modules/comercial/historical_kpis_repository.py:59:    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
/app/backend/modules/comercial/historical_kpis_repository.py:62:    server = await db.servers.find_one({'id': EDARSAHUB_SERVER_ID})
/app/backend/modules/comercial/historical_kpis_repository.py:475:# MIGRACIÓN DE STAGING MONGODB A SQL
/app/backend/modules/comercial/historical_kpis_repository.py:478:async def migrate_staging_mongo_kpis_to_sql(
/app/backend/modules/comercial/historical_kpis_repository.py:483:    Migra KPIs de staging en MongoDB a destino final en SQL.
/app/backend/modules/comercial/historical_kpis_repository.py:492:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/modules/comercial/historical_kpis_repository.py:494:    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
/app/backend/modules/comercial/historical_kpis_repository.py:498:    mongo_filter = {}
/app/backend/modules/comercial/historical_kpis_repository.py:500:        mongo_filter['source.run_id'] = run_id
/app/backend/modules/comercial/historical_kpis_repository.py:505:        'mongo_records_found': 0,
/app/backend/modules/comercial/historical_kpis_repository.py:514:        cursor = db.kpis_comercial.find(mongo_filter, {'_id': 0})
/app/backend/modules/comercial/historical_kpis_repository.py:517:            results['mongo_records_found'] += 1
/app/backend/modules/comercial/historical_kpis_repository.py:519:            # Mapear documento MongoDB a registro SQL
/app/backend/modules/comercial/historical_kpis_repository.py:524:                'run_id': source.get('run_id', 'MONGO_MIGRATION'),
/app/backend/modules/comercial/historical_kpis_repository.py:538:                'source_type': 'MONGO_MIGRATION'
/app/backend/modules/comercial/kpis_repository.py:25:# INYECCIÓN DE DEPENDENCIA: MongoDB
/app/backend/modules/comercial/kpis_repository.py:33:    DEPRECADO: MongoDB ya no se usa para KPIs.
/app/backend/modules/comercial/kpis_repository.py:39:    logging.warning("[COMERCIAL] KPIs repository - MongoDB deprecado")
/app/backend/modules/comercial/kpis_repository.py:44:    DEPRECADO: MongoDB ya no se usa.
/app/backend/modules/comercial/kpis_repository.py:49:        logging.debug("[COMERCIAL] KPIs get_db() - MongoDB deprecado, retornando None")
/app/backend/modules/comercial/kpis_repository.py:58:COLLECTION_NAME = "kpis_comercial"
/app/backend/modules/comercial/kpis_repository.py:210:    existing = await db[COLLECTION_NAME].find_one(filter_key)
/app/backend/modules/comercial/kpis_repository.py:253:            await db[COLLECTION_NAME].insert_one(new_doc)
/app/backend/modules/comercial/kpis_repository.py:260:                existing = await db[COLLECTION_NAME].find_one(filter_key)
/app/backend/modules/comercial/kpis_repository.py:356:    await db[COLLECTION_NAME].update_one(filter_key, update_doc)
/app/backend/modules/comercial/kpis_repository.py:390:    existing = await db[COLLECTION_NAME].find_one(filter_key)
/app/backend/modules/comercial/kpis_repository.py:409:    await db[COLLECTION_NAME].update_one(
/app/backend/modules/comercial/kpis_repository.py:436:    doc = await db[COLLECTION_NAME].find_one(filter_key, {"_id": 0})
/app/backend/modules/comercial/kpis_repository.py:460:    cursor = db[COLLECTION_NAME].find(query, {"_id": 0}).sort("fecha", -1)
/app/backend/modules/comercial/kpis_repository.py:480:    cursor = db[COLLECTION_NAME].find(query, {"_id": 0}).sort("fecha", -1)
/app/backend/modules/comercial/kpis_repository.py:501:    cursor = db[COLLECTION_NAME].find(query, {"_id": 0}).sort("fecha", 1).limit(limit)
/app/backend/modules/comercial/kpis_repository.py:522:    result = await db[COLLECTION_NAME].update_many(
/app/backend/modules/comercial/kpis_repository.py:557:    'COLLECTION_NAME',
/app/backend/modules/comercial/README_BLINDAJE.md:13:/app/backend/core/db.py                    🔴 CRÍTICO
/app/backend/modules/comercial/services/listas_competidores_service.py:10:- CERO MongoDB
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:13:- CERO MongoDB
/app/backend/modules/comercial/services/pricing_ai_service.py:15:- NO usar MongoDB (todo en EDARSAHUB SQL)
/app/backend/modules/comercial/services/pricing_ai_service.py:50:    TipoMotorPrecio,
/app/backend/modules/comercial/services/pricing_ai_service.py:672:        tipo_motor=TipoMotorPrecio.COSTO_MARGEN,
/app/backend/modules/comercial/services/perfil_unidad_service.py:5:que sirven como contexto para el motor de precios con IA y benchmark.
/app/backend/modules/comercial/services/pricing_sugerido_service.py:4:Este módulo orquesta el cálculo de precios sugeridos usando diferentes motores:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:33:    TipoMotorPrecio,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:214:    TIPOS DE MOTOR:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:248:        tipo_motor=request.tipo_motor,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:257:        # MOTOR VINOS_RANGOS: Delegar a servicio existente (INTOCABLE)
/app/backend/modules/comercial/services/pricing_sugerido_service.py:259:        if request.tipo_motor == TipoMotorPrecio.VINOS_RANGOS:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:263:                response.mensaje = "El producto no es vino. Use motor COSTO_MARGEN para productos generales."
/app/backend/modules/comercial/services/pricing_sugerido_service.py:298:        # MOTOR COSTO_MARGEN: Fórmula matemática pura
/app/backend/modules/comercial/services/pricing_sugerido_service.py:300:        if request.tipo_motor == TipoMotorPrecio.COSTO_MARGEN:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:369:        # MOTOR BENCHMARK_COMPETENCIA: Basado en posición vs competidores
/app/backend/modules/comercial/services/pricing_sugerido_service.py:371:        if request.tipo_motor == TipoMotorPrecio.BENCHMARK_COMPETENCIA:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:408:        # MOTOR MIXTO_COSTO_COMPETENCIA: Combina costo+margen con benchmark
/app/backend/modules/comercial/services/pricing_sugerido_service.py:410:        if request.tipo_motor == TipoMotorPrecio.MIXTO_COSTO_COMPETENCIA:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:485:        # Motor no reconocido
/app/backend/modules/comercial/services/pricing_sugerido_service.py:487:        response.mensaje = f"Tipo de motor no reconocido: {request.tipo_motor}"
/app/backend/modules/comercial/services/pricing_sugerido_service.py:499:    tipo_motor: TipoMotorPrecio,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:510:        tipo_motor: Motor a usar para todos los productos
/app/backend/modules/comercial/services/pricing_sugerido_service.py:551:            tipo_motor=tipo_motor,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:561:def obtener_estadisticas_calculo(server_id: str, tipo_motor: TipoMotorPrecio = TipoMotorPrecio.COSTO_MARGEN) -> Dict[str, Any]:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:571:        tipo_motor=tipo_motor,
/app/backend/modules/comercial/services/metricas_ia_service.py:16:- NO usar MongoDB
/app/backend/modules/comercial/services/pricing_schemas.py:2:FASE 1C-3I-B: Esquemas Pydantic para Motor de Precios Sugeridos y Benchmark
/app/backend/modules/comercial/services/pricing_schemas.py:78:class TipoMotorPrecio(str, Enum):
/app/backend/modules/comercial/services/pricing_schemas.py:79:    """Tipos de motor de cálculo de precio."""
/app/backend/modules/comercial/services/pricing_schemas.py:412:    # Motor a usar
/app/backend/modules/comercial/services/pricing_schemas.py:413:    tipo_motor: TipoMotorPrecio = Field(
/app/backend/modules/comercial/services/pricing_schemas.py:414:        default=TipoMotorPrecio.COSTO_MARGEN,
/app/backend/modules/comercial/services/pricing_schemas.py:415:        description="Tipo de motor de cálculo"
/app/backend/modules/comercial/services/pricing_schemas.py:432:        tipo = values.get('tipo_motor')
/app/backend/modules/comercial/services/pricing_schemas.py:433:        if tipo == TipoMotorPrecio.COSTO_MARGEN and v is None:
/app/backend/modules/comercial/services/pricing_schemas.py:446:    # Motor utilizado
/app/backend/modules/comercial/services/pricing_schemas.py:447:    tipo_motor: TipoMotorPrecio
/app/backend/modules/comercial/services/pricing_schemas.py:602:    'TipoMotorPrecio',
/app/backend/modules/comercial/routes.py:1165:                        # Para modo HUB, NO usar caché MongoDB como fallback.
/app/backend/modules/comercial/routes.py:1167:                        # MongoDB NO debe ser fuente productiva de datos.
/app/backend/modules/comercial/routes.py:1170:                            # HUB: Reportar error SQL, NO usar caché MongoDB
/app/backend/modules/comercial/routes.py:1171:                            logging.warning(f"[HUB-EDARSAHUB-ERROR] {server['name']}: Error leyendo EDARSAHUB SQL - NO hay fallback MongoDB")
/app/backend/modules/comercial/routes.py:1189:                            # LIVE-C: Mantener fallback a caché MongoDB (conexión real fallida)
/app/backend/modules/comercial/routes.py:1678:    # FUENTE: EDARSAHUB.Unidades_Negocio (NO MongoDB)
/app/backend/modules/comercial/routes.py:2984:    # ARQUITECTURA: Obtener nombre de unidad desde EDARSAHUB (primario) o MongoDB (LEGACY_FALLBACK)
/app/backend/modules/comercial/routes.py:2986:    if nombre_source == 'MONGO_LEGACY_FALLBACK':
/app/backend/modules/comercial/routes.py:2987:        logging.warning(f"[LEGACY_FALLBACK] Mesas: Nombre de sucursal {sucursal} obtenido de MongoDB")
/app/backend/modules/comercial/routes.py:3048:            # BLINDAJE: Usar nombre obtenido de MongoDB
/app/backend/modules/comercial/routes.py:3159:            # BLINDAJE MPRO: Usar nombre de MongoDB (ya obtenido arriba), con fallback a SQL si no se encontró
/app/backend/modules/comercial/routes.py:3161:            # Si MongoDB no encontró el nombre (aún es server['name']), intentar con SQL
/app/backend/modules/hub/modulo_financiero_proyectos.py:63:    # MOTOR DE RENTABILIDAD REAL (P&L POR EVENTO)
/app/backend/modules/fase2_operativo/sql_repository.py:4:Reemplazo completo de MongoDB para el módulo fase2_operativo.
/app/backend/modules/fase2_operativo/sql_repository.py:550:        WHERE UsuarioID = %s OR MongoLegacyID = %s
/app/backend/modules/fase2_operativo/db_utils.py:5:Proporciona acceso a la conexión de MongoDB para el módulo operativo.
/app/backend/modules/fase2_operativo/db_utils.py:8:from pymongo import MongoClient
/app/backend/modules/fase2_operativo/db_utils.py:10:# Conexión síncrona a MongoDB para los repositories
/app/backend/modules/fase2_operativo/db_utils.py:17:    Obtiene la conexión a la base de datos MongoDB.
/app/backend/modules/fase2_operativo/db_utils.py:21:        Database MongoDB
/app/backend/modules/fase2_operativo/db_utils.py:26:        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/modules/fase2_operativo/db_utils.py:29:        _client = MongoClient(mongo_url)
/app/backend/modules/fase2_operativo/repositories/__init__.py:6:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/__init__.py:17:    COLLECTION_TO_TABLE_MAP,
/app/backend/modules/fase2_operativo/repositories/__init__.py:39:    "COLLECTION_TO_TABLE_MAP",
/app/backend/modules/fase2_operativo/repositories/base_repository.py:7:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/base_repository.py:12:- El parámetro 'db' (MongoDB) se ignora completamente
/app/backend/modules/fase2_operativo/repositories/base_repository.py:21:    COLLECTION_TO_TABLE_MAP,
/app/backend/modules/fase2_operativo/repositories/base_repository.py:31:    "COLLECTION_TO_TABLE_MAP",
/app/backend/modules/fase2_operativo/repositories/cargos_repository.py:6:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/cargos_repository.py:25:    Reemplaza acceso MongoDB por SQL Server EDARSAHUB.
/app/backend/modules/fase2_operativo/repositories/cargos_repository.py:58:        # Mapeo de datos MongoDB → SQL
/app/backend/modules/fase2_operativo/repositories/cargos_repository.py:165:        # Mapear campos MongoDB → SQL
/app/backend/modules/fase2_operativo/repositories/cargos_repository.py:377:        Mapea campos SQL → formato MongoDB/API legacy.
/app/backend/modules/fase2_operativo/repositories/cargos_repository.py:417:    Reemplaza acceso MongoDB por SQL Server EDARSAHUB.
/app/backend/modules/fase2_operativo/repositories/configuracion_repository.py:6:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/configuracion_repository.py:17:    Migrado de MongoDB a SQL Server EDARSAHUB.
/app/backend/modules/fase2_operativo/repositories/auditoria_programada_repository.py:6:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/auditoria_programada_repository.py:27:    Migrado de MongoDB a SQL Server EDARSAHUB.
/app/backend/modules/fase2_operativo/repositories/auditoria_repository.py:6:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/auditoria_repository.py:17:    Migrado de MongoDB a SQL Server EDARSAHUB.
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:7:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:20:# Constante para ordenamiento descendente (reemplaza pymongo.DESCENDING)
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:202:        No usa $inc de MongoDB, hace SELECT + UPDATE.
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:233:        MIGRADO A SQL: Usa GROUP BY explícito en lugar de aggregate de MongoDB.
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:6:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:21:    Migrado de MongoDB a SQL Server EDARSAHUB.
/app/backend/modules/fase2_operativo/repositories/justificacion_repository.py:6:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/justificacion_repository.py:17:    Migrado de MongoDB a SQL Server EDARSAHUB.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:7:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:20:# Constantes para ordenamiento (reemplazan pymongo.ASCENDING/DESCENDING)
/app/backend/modules/fase2_operativo/repositories/detalle_diferencias_repository.py:6:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/detalle_diferencias_repository.py:17:    Migrado de MongoDB a SQL Server EDARSAHUB.
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:7:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/historial_responsabilidad_repository.py:6:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/historial_responsabilidad_repository.py:24:    Migrado de MongoDB a SQL Server EDARSAHUB.
/app/backend/modules/fase2_operativo/repositories/historial_repository.py:6:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/historial_repository.py:17:    Migrado de MongoDB a SQL Server EDARSAHUB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:6:usando EDARSAHUB SQL Server en lugar de MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:10:- CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:25:# MAPEO COLECCIÓN MONGODB → TABLA SQL
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:27:COLLECTION_TO_TABLE_MAP = {
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:60:# Mapeo de campos MongoDB → SQL para cada tabla
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:207:    Clase que simula el cursor de MongoDB con métodos encadenables.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:264:    def __init__(self, method: str, collection: str):
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:266:        self.collection = collection
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:268:            f"SQL_REPOSITORY_METHOD_NOT_IMPLEMENTED: {method}() en {collection}. "
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:279:    - CERO MongoDB productivo
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:283:    - Reemplaza BaseRepository (MongoDB)
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:287:    def __init__(self, collection_name: str):
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:292:            collection_name: Nombre de la colección MongoDB (se mapea a tabla SQL)
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:294:        self.collection_name = collection_name
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:295:        self.table_name = COLLECTION_TO_TABLE_MAP.get(collection_name)
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:299:                f"SQL_REPOSITORY_TABLE_NOT_MAPPED: Colección '{collection_name}' "
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:300:                f"no tiene mapeo a tabla SQL. Agregar a COLLECTION_TO_TABLE_MAP."
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:314:        logger.info(f"[SQL_REPO] Inicializado {collection_name} → {self.table_name}")
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:336:    def _map_field(self, mongo_field: str) -> str:
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:338:        Mapea un campo MongoDB a su equivalente SQL.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:341:        mapped = self._field_map.get(mongo_field)
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:345:        parts = mongo_field.split("_")
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:367:        Convierte una fila SQL a formato compatible con MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:373:        # Crear mapeo inverso SQL → MongoDB
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:375:        for mongo_key, sql_key in self._field_map.items():
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:376:            inverse_map[sql_key.lower()] = mongo_key
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:406:        Construye cláusula WHERE desde filtros estilo MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:429:                # Operadores MongoDB
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:493:        Construye cláusula ORDER BY desde formato MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:740:    # MÉTODOS DE COMPATIBILIDAD MONGODB (Síncronos)
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:745:        Versión síncrona de get para compatibilidad con código MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:783:        Versión síncrona para compatibilidad con código MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:847:        Versión síncrona de create para compatibilidad con código MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:858:        Versión síncrona de update para compatibilidad con código MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:897:        Versión síncrona de count para compatibilidad con código MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:909:        Versión síncrona para compatibilidad con MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:935:        Versión síncrona para compatibilidad con MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:980:        Versión síncrona para compatibilidad con MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1035:        Ejecuta una agregación estilo MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1184:def get_sql_repository(collection_name: str) -> SQLBaseRepository:
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1186:    Factory para obtener un repositorio SQL dado un nombre de colección MongoDB.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1189:        collection_name: Nombre de la colección MongoDB
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1194:    return SQLBaseRepository(collection_name)
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1210:    - El parámetro 'db' (MongoDB) se ignora
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1214:    def __init__(self, db, collection_name: str):
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1220:            collection_name: Nombre de la colección (se mapea a tabla SQL)
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1222:        # Ignoramos db (MongoDB) - Usamos SQL
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1223:        self._sql_repo = SQLBaseRepository(collection_name)
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1224:        self.collection_name = collection_name
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1227:        # Para compatibilidad: exponer métodos síncronos como 'collection'
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1228:        self.collection = self._sql_repo
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1231:            f"[BASE_REPO] Inicializado {collection_name} → SQL:{self.table_name} "
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:1232:            f"(MongoDB db ignorado, usando EDARSAHUB SQL)"
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:9:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:17:async def init_notificaciones_collections():
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:20:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:23:    client = AsyncIOMotorClient(mongo_url)
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:30:        await db.create_collection("notificaciones_log")
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:48:    for collection_name, index_spec in indices:
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:50:            await db[collection_name].create_index(index_spec)
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:51:            logger.info(f"✅ Índice creado en '{collection_name}': {index_spec}")
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:56:    test_doc = await db.notificaciones_log.find_one({"tipo_evento": "_INIT_TEST"})
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:58:        await db.notificaciones_log.insert_one({
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:74:    await db.notificaciones_log.delete_one({"tipo_evento": "_INIT_TEST"})
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:79:    count = await db.notificaciones_log.count_documents({})
/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py:86:    asyncio.run(init_notificaciones_collections())
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:65:        db: Conexión a MongoDB
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:70:    collection = db["configuracion_operativa"]
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:80:        existente = collection.find_one({"clave": clave})
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:95:            collection.insert_one(documento)
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:117:        db: Conexión a MongoDB
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:122:    collection = db["responsabilidad_economica"]
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:125:    total = collection.count_documents({})
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:132:        collection.create_index("workflow_id", unique=True, name="idx_workflow_id")
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:139:        collection.create_index("sucursal_id", name="idx_sucursal_id")
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:146:        collection.create_index("estado", name="idx_estado")
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:153:        collection.create_index("fecha_calculo", name="idx_fecha_calculo")
/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py:174:        db: Conexión a MongoDB (opcional, se obtiene si no se pasa)
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:16:from pymongo import MongoClient, ASCENDING, DESCENDING
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:17:from pymongo.errors import CollectionInvalid, OperationFailure
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:21:MONGO_URL = os.environ.get("MONGO_URL")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:51:    existentes = db.list_collection_names()
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:61:                db.create_collection(col)
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:64:            except CollectionInvalid:
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:77:        db.workflow_inventarios.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:91:        db.workflow_inventarios.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:104:        db.workflow_inventarios.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:118:        db.detalle_diferencias.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:132:        db.tareas_inventario.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:145:        db.tareas_inventario.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:158:        db.tareas_inventario.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:171:        db.tareas_inventario.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:185:        db.historial_asignaciones.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:199:        db.justificaciones_inventario.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:212:        db.justificaciones_inventario.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:226:        db.decisiones_auditoria.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:240:        db.configuracion_operativa.create_index(
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:283:        existente = db.configuracion_operativa.find_one({"clave": config["clave"]})
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:288:            db.configuracion_operativa.insert_one(config)
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:299:        if col in db.list_collection_names():
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:310:        if col in db.list_collection_names():
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:320:def init_fase2a_collections():
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:330:    if not MONGO_URL:
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:331:        print("ERROR: Variable de entorno MONGO_URL no definida")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:335:        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:338:        print("✓ Conexión a MongoDB establecida")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:340:        print(f"ERROR: No se pudo conectar a MongoDB: {e}")
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:385:    init_fase2a_collections()
/app/backend/modules/fase2_operativo/schemas/workflow_schemas.py:36:    id: str = Field(..., alias="_id", description="ID del documento MongoDB")
/app/backend/modules/fase2_operativo/services/document_data_service.py:39:    - Operaciones de MongoDB pasan por StubDatabase sin fallar
/app/backend/modules/fase2_operativo/services/document_data_service.py:47:            db: Instancia de la base de datos MongoDB
/app/backend/modules/fase2_operativo/services/document_data_service.py:62:            from core.mongo_stub import StubDatabase
/app/backend/modules/fase2_operativo/services/document_data_service.py:70:        FASE B-P2: SQL-only, sin fallback a MongoDB.
/app/backend/modules/fase2_operativo/services/cargos_service.py:117:            from core.mongo_stub import StubDatabase
/app/backend/modules/fase2_operativo/services/cargos_service.py:789:            # No consultamos MongoDB para usuarios/workflows - usamos datos ya disponibles
/app/backend/modules/fase2_operativo/services/orquestador_service.py:7:Este servicio ahora usa SQL Server (EDARSAHUB) en lugar de MongoDB.
/app/backend/modules/fase2_operativo/services/orquestador_service.py:46:    - Las operaciones de MongoDB fueron reemplazadas por sql_repository.py
/app/backend/modules/fase2_operativo/services/orquestador_service.py:74:        MIGRADO A SQL SERVER - Ya no depende de MongoDB.
/app/backend/modules/fase2_operativo/services/notification_service.py:32:    FASE B-P2: Migrado a SQL - usa repositorio SQL en lugar de MongoDB.
/app/backend/modules/fase2_operativo/services/notification_service.py:38:        # FASE B-P2: Usar SQLBaseRepository en lugar de MongoDB collection
/app/backend/modules/fase2_operativo/services/notification_service.py:420:            # FASE B-P2: Usar SQL repository en lugar de MongoDB
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:5:Usa PyMongo sync para compatibilidad con el módulo.
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:45:    - MongoDB pasa por StubDatabase
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:58:            from core.mongo_stub import StubDatabase
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:236:        """Crea workflow de inventario (sync - usa PyMongo directamente)."""
/app/backend/modules/fase2_operativo/services/sla_service.py:7:Este servicio ahora usa SQL Server (EDARSAHUB) en lugar de MongoDB.
/app/backend/modules/fase2_operativo/services/sla_service.py:72:    - Las operaciones de MongoDB fueron reemplazadas por sql_repository.py
/app/backend/modules/fase2_operativo/services/auditoria_service.py:44:            db: Instancia de la base de datos MongoDB
/app/backend/modules/fase2_operativo/services/configuracion_service.py:46:            db: Instancia de la base de datos MongoDB
/app/backend/modules/fase2_operativo/services/operativo_service.py:50:            db: Instancia de la base de datos MongoDB
/app/backend/modules/fase2_operativo/services/tarea_service.py:43:            db: Instancia de la base de datos MongoDB
/app/backend/modules/fase2_operativo/services/workflow_service.py:72:            db: Instancia de la base de datos MongoDB
/app/backend/modules/fase2_operativo/services/justificacion_service.py:52:            db: Instancia de la base de datos MongoDB
/app/backend/modules/fase2_operativo/routes/sla_routes.py:246:        tarea = db.tareas_inventario.find_one({"id": tarea_id}, {"_id": 0})
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:111:    db_async = manager.db  # Conexión async de MongoDB
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:143:    ultima = db.scheduler_job_logs.find_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:188:    tareas = list(db.tareas_operativas_compras.find(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:208:    tarea = db.tareas_operativas_compras.find_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:235:    tarea = db.tareas_operativas_compras.find_one({"id": tarea_id})
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:244:    db.tareas_operativas_compras.update_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:271:    tarea = db.tareas_operativas_compras.find_one({"id": tarea_id})
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:277:    db.tareas_operativas_compras.update_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:339:    bitacora = list(db.auditoria_compras_bitacora.find(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:371:    pedidos = list(db.pedidos_procesados_automatizacion.find(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:454:    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:492:    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:527:    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:64:    # Usar método síncrono para MongoDB síncrono
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:65:    items = list(db.notificaciones_log.find(
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:70:    total = db.notificaciones_log.count_documents(filtro)
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:99:    db.tareas_inventario.update_many(
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:111:    notificaciones_recientes = db.notificaciones_log.find(
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:130:    tareas_vencidas = list(db.tareas_inventario.find(filtro_tareas, {"_id": 0}).limit(50))
/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py:152:        usuario = db.users.find_one({"id": usuario_id}, {"_id": 0, "email": 1, "name": 1})
/app/backend/modules/fase2_operativo/routes/documentos_routes.py:70:            db.documentos_generados.insert_one({
/app/backend/modules/fase2_operativo/routes/documentos_routes.py:144:            db.documentos_generados.insert_one({
/app/backend/modules/fase2_operativo/routes/documentos_routes.py:282:            db.documentos_generados.find(
/app/backend/modules/fase2_operativo/routes/documentos_routes.py:288:        total = db.documentos_generados.count_documents(filtro)
/app/backend/modules/api_connections/__init__.py:9:- Caché/Fallback: MongoDB (colección api_connections)
/app/backend/modules/api_connections/__init__.py:15:- Sincronización automática con MongoDB
/app/backend/modules/api_connections/__init__.py:24:    sync_all_to_mongo_cache,
/app/backend/modules/api_connections/__init__.py:39:    'sync_all_to_mongo_cache',
/app/backend/modules/api_connections/repository.py:6:- MongoDB: Solo caché/log/estado auxiliar (NO autoritativo)
/app/backend/modules/api_connections/repository.py:7:- Sincronización: EDARSAHUB SQL → MongoDB (nunca al revés)
/app/backend/modules/api_connections/repository.py:11:2. Si EDARSAHUB SQL falla, NO se guarda en MongoDB
/app/backend/modules/api_connections/repository.py:12:3. Si MongoDB falla después de EDARSAHUB SQL, la operación es exitosa
/app/backend/modules/api_connections/repository.py:34:# Referencia a MongoDB (solo para caché, NO autoritativo)
/app/backend/modules/api_connections/repository.py:39:    """Inicializa el repositorio con la conexión a MongoDB (solo caché)."""
/app/backend/modules/api_connections/repository.py:45:def get_mongo_db():
/app/backend/modules/api_connections/repository.py:46:    """Obtiene la conexión a MongoDB (solo para caché)."""
/app/backend/modules/api_connections/repository.py:244:# ESCRITURA - PRIMERO EDARSAHUB SQL, LUEGO CACHÉ MONGODB
/app/backend/modules/api_connections/repository.py:256:    5. Actualizar caché MongoDB (opcional, no bloquea)
/app/backend/modules/api_connections/repository.py:329:    # 6. Actualizar caché MongoDB (no bloquea si falla)
/app/backend/modules/api_connections/repository.py:330:    await _sync_to_mongo_cache(api_id)
/app/backend/modules/api_connections/repository.py:346:    6. Actualizar caché MongoDB
/app/backend/modules/api_connections/repository.py:424:    # 7. Actualizar caché MongoDB
/app/backend/modules/api_connections/repository.py:425:    await _sync_to_mongo_cache(api_id)
/app/backend/modules/api_connections/repository.py:438:    4. Eliminar de caché MongoDB
/app/backend/modules/api_connections/repository.py:466:    # 4. Eliminar de caché MongoDB (no bloquea)
/app/backend/modules/api_connections/repository.py:468:        db = get_mongo_db()
/app/backend/modules/api_connections/repository.py:470:            await db.api_connections_cache.delete_one({"id": api_id})
/app/backend/modules/api_connections/repository.py:472:        logging.warning(f"[API_CONNECTIONS] Error eliminando caché MongoDB: {e}")
/app/backend/modules/api_connections/repository.py:478:# SINCRONIZACIÓN EDARSAHUB SQL → MONGODB (CACHÉ)
/app/backend/modules/api_connections/repository.py:481:async def _sync_to_mongo_cache(api_id: str) -> bool:
/app/backend/modules/api_connections/repository.py:483:    Sincroniza una conexión específica de EDARSAHUB SQL a MongoDB caché.
/app/backend/modules/api_connections/repository.py:487:        db = get_mongo_db()
/app/backend/modules/api_connections/repository.py:513:        await db.api_connections_cache.update_one(
/app/backend/modules/api_connections/repository.py:518:        logging.debug(f"[API_CONNECTIONS] Caché MongoDB actualizado para {api_id}")
/app/backend/modules/api_connections/repository.py:521:        logging.warning(f"[API_CONNECTIONS] Error sincronizando caché MongoDB: {e}")
/app/backend/modules/api_connections/repository.py:525:async def sync_all_to_mongo_cache() -> Dict:
/app/backend/modules/api_connections/repository.py:527:    Sincroniza todas las conexiones API de EDARSAHUB SQL a MongoDB caché.
/app/backend/modules/api_connections/repository.py:535:            success = await _sync_to_mongo_cache(api['id'])
/app/backend/modules/api_connections/repository.py:555:    Guarda el resultado en MongoDB como log de estado.
/app/backend/modules/api_connections/repository.py:600:    # Guardar resultado en MongoDB como log de estado (no bloquea)
/app/backend/modules/api_connections/repository.py:602:        db = get_mongo_db()
/app/backend/modules/api_connections/repository.py:604:            await db.api_health_logs.insert_one({
/app/backend/modules/api_connections/routes.py:8:- MongoDB solo se usa como caché/log (no autoritativo)
/app/backend/modules/api_connections/routes.py:10:- Errores de MongoDB se registran pero no bloquean la operación
/app/backend/modules/api_connections/routes.py:26:    sync_all_to_mongo_cache,
/app/backend/modules/api_connections/routes.py:162:    DESTINO: EDARSAHUB SQL (autoritativo), luego caché MongoDB.
/app/backend/modules/api_connections/routes.py:195:    DESTINO: EDARSAHUB SQL (autoritativo), luego caché MongoDB.
/app/backend/modules/api_connections/routes.py:279:async def sync_to_mongo(credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/modules/api_connections/routes.py:281:    Sincroniza conexiones API de EDARSAHUB SQL a MongoDB caché.
/app/backend/modules/api_connections/routes.py:282:    FLUJO: EDARSAHUB SQL → MongoDB (caché).
/app/backend/modules/api_connections/routes.py:286:        result = await sync_all_to_mongo_cache()
/app/backend/modules/api_connections/routes.py:289:            "message": "Sincronización EDARSAHUB SQL → MongoDB completada", 
/app/backend/modules/api_connections/universal_test_routes.py:22:- MongoDB
/app/backend/modules/sistema/estructura_service.py:39:        # MongoDB ELIMINADO - Retornar estructura vacía si db es None
/app/backend/modules/sistema/estructura_service.py:41:            logger.warning("[ESTRUCTURA] get_estructura_organizacional: Sin MongoDB - Retornando vacío")
/app/backend/modules/sistema/estructura_service.py:47:                "nota": "Modo SQL-only: Datos de estructura no disponibles sin MongoDB"
/app/backend/modules/sistema/estructura_service.py:52:            empresas = await self.db.sec_empresas.find(
/app/backend/modules/sistema/estructura_service.py:68:                unidades = await self.db.sec_unidades_negocio.find(
/app/backend/modules/sistema/estructura_service.py:84:                    sucursales = await self.db.sec_sucursales.find(
/app/backend/modules/sistema/estructura_service.py:122:            mapeos = await self.db.sec_mapeo_servidor_sucursal.find(
/app/backend/modules/sistema/estructura_service.py:159:            permisos = await self.db.sec_permisos_catalogo.find(
/app/backend/modules/sistema/estructura_service.py:218:            await self.db.sec_bitacora_acceso.insert_one(entry)
/app/backend/modules/sistema/estructura_service.py:231:    NOTA: MongoDB ELIMINADO - Este servicio puede recibir db=None.
/app/backend/modules/costos_margenes/__init__.py:9:- NO usa MongoDB
/app/backend/modules/costos_margenes/routes.py:10:- NO se usa MongoDB
/app/backend/modules/rh/importador/repository.py:38:    """Inicializa el repositorio con la conexión a MongoDB."""
/app/backend/modules/rh/importador/repository.py:45:    """Obtiene la conexión a MongoDB inyectada."""
/app/backend/modules/rh/__init__.py:103:        database: Instancia de AsyncIOMotorDatabase
/app/backend/modules/rh/solicitudes_catalogo.py:139:    _solicitudes_db.append(nueva_solicitud)
/app/backend/modules/rh/solicitudes_catalogo.py:165:    solicitudes = _solicitudes_db.copy()
/app/backend/modules/rh/repository.py:38:# NO depende del catálogo de servidores MongoDB con active=True.
/app/backend/modules/rh/repository.py:50:# ID del servidor EDARSA HUB en MongoDB (LEGACY - ya no se usa para conexión)
/app/backend/modules/rh/repository.py:66:# INYECCIÓN DE DEPENDENCIA: MongoDB
/app/backend/modules/rh/repository.py:73:    """Inicializa el repositorio con la conexión a MongoDB."""
/app/backend/modules/rh/repository.py:80:    """Obtiene la conexión a MongoDB inyectada."""
/app/backend/modules/rh/repository.py:145:    en lugar de buscar en MongoDB servers con active=True.
/app/backend/modules/rh/routes.py:138:    empresas = await db.empresas.find(
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:8:Las operaciones legacy de MongoDB pasan por StubDatabase sin fallar.
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:223:            WHERE UsuarioID = %s OR MongoLegacyID = %s
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:296:                WHERE UsuarioID = %s OR MongoLegacyID = %s
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:403:        En modo SQL-only, esta operación no persiste en MongoDB.
/app/backend/modules/configuracion/services/almacenes_sync_service.py:6:Sincroniza almacenes desde sistemas origen (SoftRestaurant/MPRO) al catálogo local MongoDB.
/app/backend/modules/configuracion/services/almacenes_sync_service.py:95:    - Persiste en MongoDB (almacenes_catalogo)
/app/backend/modules/configuracion/services/almacenes_sync_service.py:98:        db: Conexión a MongoDB
/app/backend/modules/configuracion/services/almacenes_sync_service.py:137:        # FASE P1.4-F (Dic 2025): Migrado de MongoDB db.servers a server_registry
/app/backend/modules/configuracion/services/almacenes_sync_service.py:141:        # ANTES: server = await db.servers.find_one({"id": server_id}, {"_id": 0})
/app/backend/modules/configuracion/services/almacenes_sync_service.py:198:        # PASO 5: Sincronizar al catálogo local MongoDB
/app/backend/modules/configuracion/services/almacenes_sync_service.py:201:        almacenes_collection = db.almacenes_catalogo
/app/backend/modules/configuracion/services/almacenes_sync_service.py:221:            existente = await almacenes_collection.find_one({
/app/backend/modules/configuracion/services/almacenes_sync_service.py:229:                    await almacenes_collection.update_one(
/app/backend/modules/configuracion/services/almacenes_sync_service.py:241:                await almacenes_collection.insert_one({
/app/backend/modules/configuracion/services/almacenes_sync_service.py:258:            desactivar_result = await almacenes_collection.update_many(
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:24:# Motor para conexión a MongoDB
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:25:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:36:# Conexión a MongoDB
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:40:    """Obtiene la conexión a la base de datos MongoDB."""
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:43:        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:45:        client = AsyncIOMotorClient(mongo_url)
/app/backend/modules/inventarios/repository.py:7:- ELIMINADA dependencia de MongoDB
/app/backend/modules/inventarios/repository.py:21:    Reemplaza: mongo_db.inventarios.find(filtro)
/app/backend/modules/consultas_sql/__init__.py:10:- Leer consultas desde EDARSAHUB SQL (no desde código/MongoDB)
/app/backend/modules/consultas_sql/README.md:12:- Leer consultas desde EDARSAHUB SQL (no desde código hardcodeado o MongoDB)
/app/backend/modules/consultas_sql/repository.py:16:Usa core.db.execute_sql_query para ejecución.
/app/backend/modules/catalogos/__init__.py:26:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/catalogos/__init__.py:28:# Referencia global a MongoDB (para logging/auditoría)
/app/backend/modules/catalogos/__init__.py:29:_db: AsyncIOMotorDatabase = None
/app/backend/modules/catalogos/__init__.py:32:def init_catalogos_module(db: AsyncIOMotorDatabase):
/app/backend/modules/catalogos/__init__.py:33:    """Inicializa el módulo de catálogos con la conexión a MongoDB."""
/app/backend/modules/catalogos/__init__.py:38:def get_db() -> AsyncIOMotorDatabase:
/app/backend/modules/catalogos/__init__.py:39:    """Obtiene la conexión a MongoDB."""
/app/backend/modules/catalogos/repository.py:7:FASE P1.2 (Dic 2025): Migrado de MongoDB db.servers a EDARSAHUB_CONFIG de server_registry.
/app/backend/modules/catalogos/repository.py:22:# FASE P1.2: La conexión ahora viene de EDARSAHUB_CONFIG, no de MongoDB
/app/backend/modules/catalogos/repository.py:37:    FASE P1.2 (Dic 2025): Migrado de MongoDB db.servers a server_registry.EDARSAHUB_CONFIG.
/app/backend/modules/catalogos/repository.py:41:    NO FUENTE: MongoDB db.servers
/app/backend/modules/catalogos/repository.py:341:        db: Conexión a MongoDB (para obtener credenciales SQL)
/app/backend/modules/edge/motor_reglas_comerciales.py:6:class MotorReglasComerciales:
/app/backend/modules/edge/comandero_terminal_ui.ts:67:        motorReglasBackend: any
/app/backend/modules/edge/comandero_terminal_ui.ts:78:        const maridajeSugerido = motorReglasBackend.interceptar_producto_para_maridaje(producto.id_producto);
/app/backend/modules/edge/comandero_local_core.py:103:    # MOTOR TRANSACCIONAL OFFLINE (Cola FIFO con Idempotencia)
/app/backend/modules/edge/motor_inventario_parametrico.py:1:# backend/modules/edge/motor_inventario_parametrico.py
/app/backend/modules/edge/motor_inventario_parametrico.py:7:class MotorInventarioParametrico:
/app/backend/modules/auth/service.py:58:    # Preparar documento para MongoDB
/app/backend/modules/auth/service.py:119:        # El ID puede venir como int (de SQL) o como string (MongoDB ObjectId)
/app/backend/modules/auth/service.py:345:    Ya NO escribe en MongoDB. Los permisos operativos se guardan en:
/app/backend/modules/auth/service.py:422:                        (UsuarioID, ServidorID, LegacyMongoValue, Activo, FechaCreacion, Observaciones)
/app/backend/modules/auth/service.py:453:                                (UsuarioID, ServidorID, SucursalCodigo, LegacyMongoValue, Activo, FechaCreacion, Observaciones)
/app/backend/modules/auth/service.py:484:                                (UsuarioID, ServidorID, AlmacenCodigo, LegacyMongoValue, Activo, FechaCreacion, Observaciones)
/app/backend/modules/auth/service.py:580:    # Retornar sin password ni _id (MongoDB agrega _id al dict después de insert)
/app/backend/modules/auth/__init__.py:12:- repository.py: Acceso a MongoDB
/app/backend/modules/auth/__init__.py:35:    Inicializa el módulo de auth con la conexión a MongoDB.
/app/backend/modules/auth/__init__.py:38:        database: Instancia de AsyncIOMotorDatabase
/app/backend/modules/auth/password_reset.py:15:- MongoDB ya NO se usa en este módulo
/app/backend/modules/auth/password_reset.py:115:    AUTH-RESET-P2: Reemplaza MongoDB rate_limit_password_reset.
/app/backend/modules/auth/password_reset.py:162:    AUTH-RESET-P2: Reemplaza MongoDB rate_limit_password_reset.
/app/backend/modules/auth/password_reset.py:209:    AUTH-RESET-P2: Reemplaza MongoDB audit_password_reset.
/app/backend/modules/auth/repository.py:6:MongoDB ya NO es fuente productiva para operaciones de usuarios.
/app/backend/modules/auth/repository.py:23:# INICIALIZACIÓN - YA NO REQUIERE MONGODB
/app/backend/modules/auth/repository.py:33:    MIGRACIÓN COMPLETA A SQL: MongoDB ya NO es requerido.
/app/backend/modules/auth/repository.py:40:    logging.info("[AUTH] Repository inicializado - 100% SQL Server (sin MongoDB)")
/app/backend/modules/auth/repository.py:45:    DEPRECADO: MongoDB ya no se usa.
/app/backend/modules/auth/repository.py:50:        logging.warning("[AUTH] get_db() llamado pero MongoDB está deprecado. Auth usa 100% SQL.")
/app/backend/modules/auth/repository.py:62:    MongoDB ya NO es fuente productiva.
/app/backend/modules/auth/repository.py:71:    MongoDB ya NO es fuente productiva.
/app/backend/modules/auth/repository.py:85:    MongoDB solo se consulta para campos RBAC piloto (sec_*, telefono)
/app/backend/modules/auth/repository.py:170:        # RBAC-SCOPE-D: MongoDB solo para campos RBAC piloto (sec_*), NO para permisos operativos
/app/backend/modules/auth/repository.py:171:        mongo_rbac_data = {}
/app/backend/modules/auth/repository.py:173:            mongo_users = await get_db().users.find(
/app/backend/modules/auth/repository.py:187:            for mu in mongo_users:
/app/backend/modules/auth/repository.py:188:                mongo_id = mu.get('id', '').lower()
/app/backend/modules/auth/repository.py:189:                if mongo_id:
/app/backend/modules/auth/repository.py:190:                    mongo_rbac_data[mongo_id] = mu
/app/backend/modules/auth/repository.py:191:        except Exception as mongo_err:
/app/backend/modules/auth/repository.py:192:            logging.warning(f"[AUTH-REPO] No se pudieron leer campos RBAC piloto de MongoDB: {mongo_err}")
/app/backend/modules/auth/repository.py:207:            # Obtener campos RBAC piloto de MongoDB (solo metadatos, no permisos operativos)
/app/backend/modules/auth/repository.py:208:            rbac_data = mongo_rbac_data.get(sql_id_lower, {})
/app/backend/modules/auth/repository.py:224:                # Campos RBAC piloto (desde MongoDB - solo metadatos)
/app/backend/modules/auth/repository.py:241:        # NO hacer fallback a MongoDB - reportar error
/app/backend/modules/auth/repository.py:282:    MongoDB ya NO es fuente productiva.
/app/backend/modules/auth/repository.py:291:    MongoDB ya NO es fuente productiva.
/app/backend/modules/auth/repository.py:300:    MongoDB ya NO es fuente productiva.
/app/backend/modules/auth/context_service.py:14:Este módulo ha sido migrado de MongoDB a EDARSAHUB SQL.
/app/backend/modules/auth/context_service.py:21:- Sistema_EmpresasMongoMap
/app/backend/modules/auth/context_service.py:24:MongoDB ya no es fuente de datos para contexto de usuario.
/app/backend/modules/auth/context_service.py:129:            m.EmpresaMongoUUID,
/app/backend/modules/auth/context_service.py:133:        JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
/app/backend/modules/auth/context_service.py:145:            'id': row[3],  # EmpresaMongoUUID (compatibilidad)
/app/backend/modules/auth/context_service.py:172:            m.EmpresaMongoUUID
/app/backend/modules/auth/context_service.py:174:        JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
/app/backend/modules/auth/context_service.py:182:            'id': row[3],  # EmpresaMongoUUID
/app/backend/modules/auth/context_service.py:200:            s.MongoUUID
/app/backend/modules/auth/context_service.py:210:            'id': row[3] or row[1],  # MongoUUID o Codigo como fallback
/app/backend/modules/auth/context_service.py:220:    Obtiene una empresa por UUID MongoDB.
/app/backend/modules/auth/context_service.py:227:            m.EmpresaMongoUUID
/app/backend/modules/auth/context_service.py:229:        JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
/app/backend/modules/auth/context_service.py:230:        WHERE LOWER(m.EmpresaMongoUUID) = LOWER(%s)
/app/backend/modules/auth/routes.py:106:    # Autenticar usuario (valida credenciales contra MongoDB)
/app/backend/modules/auth/routes.py:265:    # Buscar usuario en MongoDB para obtener email y role
/app/backend/modules/auth/routes.py:688:# - MongoDB es ubicacion TRANSITORIA/LEGACY para usuarios
/app/backend/modules/comercial_v2/__init__.py:13:- NO consultan SQL vivo ni MongoDB cache
/app/backend/modules/comercial_v2/repository_readonly.py:10:- MongoDB cache
/app/backend/modules/comercial_v2/schemas_api.py:61:    mongodb_cache: bool = False
/app/backend/modules/comercial_v2/routes.py:10:- MongoDB cache
/app/backend/modules/comercial_v2/routes.py:498:        unidades_mongo = await get_user_unidades_negocio(current_user)
/app/backend/modules/comercial_v2/routes.py:503:        for u in unidades_mongo:
/app/backend/modules/comercial_v2/routes.py:584:    Fuente: EDARSAHUB (NO SQL vivo, NO MongoDB)
/app/backend/modules/universal_query/routes.py:164:    FASE P1.3 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/modules/universal_query/routes.py:168:    NO FUENTE: MongoDB db.servers
/app/backend/modules/universal_query/routes.py:173:    # Obtener desde EDARSAHUB SQL (NO MongoDB)
/app/backend/modules/universal_query/routes.py:248:    FASE P1.3 (Dic 2025): Migrado de MongoDB a EDARSAHUB SQL via server_registry.
/app/backend/modules/universal_query/routes.py:255:    # Obtener servidor desde EDARSAHUB SQL (NO MongoDB)
/app/backend/modules/crm/integration/sync_engine.py:4:Motor de sincronización que orquesta la importación de datos
/app/backend/modules/crm/integration/sync_engine.py:32:    Motor de sincronización CRM.
/app/backend/modules/finanzas/repository_bancarios.py:4:Acceso a datos EDARSAHUB. NO usar MongoDB.
/app/backend/modules/finanzas/repository_bancarios.py:28:    IMPORTANTE: Solo usar EDARSAHUB, NO MongoDB.
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:75:    NO usa MongoDB como fuente financiera.
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:894:    # FINANZAS-TESORERIA-MONGO-002: Agregado 2026-05-25
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:976:        FINANZAS-TESORERIA-MONGO-002: Método agregado para compatibilidad con frontend
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:1042:        FINANZAS-TESORERIA-MONGO-002: Método agregado para compatibilidad con frontend.
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:1100:            # Formatear para compatibilidad con contrato anterior (MongoDB)
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:1147:    FINANZAS-TESORERIA-MONGO-002: Factory method para tesoreria.py
/app/backend/modules/finanzas/carga_historica_propinas_tpv.py:21:- NO usa MongoDB como fuente financiera
/app/backend/modules/finanzas/tesoreria.py:5:FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
/app/backend/modules/finanzas/tesoreria.py:7:- Ya NO usa MongoDB (tesoreria_cuadres_z) como fuente productiva
/app/backend/modules/finanzas/tesoreria.py:34:# FINANZAS-TESORERIA-MONGO-002: Migrado a repositorio SQL
/app/backend/modules/finanzas/tesoreria.py:59:    empresas = await db.empresas.find(
/app/backend/modules/finanzas/tesoreria.py:299:    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
/app/backend/modules/finanzas/tesoreria.py:300:    - Ya NO usa MongoDB tesoreria_cuadres_z
/app/backend/modules/finanzas/tesoreria.py:305:        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
/app/backend/modules/finanzas/tesoreria.py:320:        # Filtrar por server_id o unidad_negocio_id (SQL directo, sin MongoDB)
/app/backend/modules/finanzas/tesoreria.py:356:    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
/app/backend/modules/finanzas/tesoreria.py:357:    - Ya NO usa MongoDB tesoreria_cuadres_z
/app/backend/modules/finanzas/tesoreria.py:361:        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
/app/backend/modules/finanzas/tesoreria.py:409:    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
/app/backend/modules/finanzas/tesoreria.py:412:        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
/app/backend/modules/finanzas/tesoreria.py:445:    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
/app/backend/modules/finanzas/tesoreria.py:446:    - Ya NO usa MongoDB tesoreria_cuadres_z
/app/backend/modules/finanzas/tesoreria.py:452:        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
/app/backend/modules/finanzas/tesoreria.py:532:    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
/app/backend/modules/finanzas/tesoreria.py:537:        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
/app/backend/modules/finanzas/tesoreria.py:585:    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
/app/backend/modules/finanzas/tesoreria.py:588:        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
/app/backend/modules/finanzas/tesoreria.py:673:    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
/app/backend/modules/finanzas/tesoreria.py:676:        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
/app/backend/modules/finanzas/tesoreria.py:746:    FALLBACK: MongoDB (solo si EDARSAHUB falla, con warning)
/app/backend/modules/finanzas/tesoreria.py:754:    NOTA TÉCNICA: MongoDB se mantiene como registry legacy parcial para fallback.
/app/backend/modules/finanzas/tesoreria.py:819:            logger.warning("[TESORERIA][EDARSAHUB_EMPTY] EDARSAHUB no retornó servidores, intentando fallback MongoDB")
/app/backend/modules/finanzas/tesoreria.py:824:    # FALLBACK: server_registry.py (FASE T2.2: Reemplaza MongoDB)
/app/backend/modules/finanzas/tesoreria.py:878:    FASE T2.2: Fallback migrado a server_registry.py (elimina MongoDB).
/app/backend/modules/finanzas/repository_cuadres_z.py:2:Repositorio MongoDB para Cuadres de Cortes Z
/app/backend/modules/finanzas/repository_cuadres_z.py:12:# MongoDB connection
/app/backend/modules/finanzas/repository_cuadres_z.py:18:        from pymongo import MongoClient
/app/backend/modules/finanzas/repository_cuadres_z.py:19:        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/modules/finanzas/repository_cuadres_z.py:21:        client = MongoClient(mongo_url)
/app/backend/modules/finanzas/repository_cuadres_z.py:66:        self.collection_name = "tesoreria_cuadres_z"
/app/backend/modules/finanzas/repository_cuadres_z.py:69:    def collection(self):
/app/backend/modules/finanzas/repository_cuadres_z.py:70:        return get_db()[self.collection_name]
/app/backend/modules/finanzas/repository_cuadres_z.py:146:        result = self.collection.insert_one(documento)
/app/backend/modules/finanzas/repository_cuadres_z.py:156:            result = self.collection.find_one({'_id': ObjectId(cuadre_id)})
/app/backend/modules/finanzas/repository_cuadres_z.py:169:            result = self.collection.find_one({
/app/backend/modules/finanzas/repository_cuadres_z.py:253:            self.collection.update_one(
/app/backend/modules/finanzas/repository_cuadres_z.py:295:            cursor = self.collection.find(query).sort('created_at', -1).skip(skip).limit(limit)
/app/backend/modules/finanzas/repository_cuadres_z.py:349:            results = list(self.collection.aggregate(pipeline))
/app/backend/modules/finanzas/repository_cuadres_z.py:376:            result = self.collection.delete_one({'_id': ObjectId(cuadre_id)})
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:74:    - Usa core.db.parse_sql_server_host() para parsear correctamente instancias nombradas
/app/backend/modules/finanzas/cuentas_por_pagar.py:69:    empresas = await db.empresas.find(
/app/backend/modules/finanzas/repository_real.py:21:# FASE T2.1: Usar EDARSAHUB_CONFIG desde server_registry en lugar de MongoDB
/app/backend/modules/finanzas/repository_real.py:39:            db: Instancia de MongoDB (conservada por compatibilidad, no usada para conexión EDARSAHUB)
/app/backend/modules/finanzas/repository_real.py:49:        Ya no consulta MongoDB db.servers.
/app/backend/modules/finanzas/repository_cortes_z.py:43:            server_id: UUID del servidor en MongoDB/EDARSAHUB
/app/backend/modules/finanzas/ingresos.py:435:    cortes = _cortes_caja_db.copy()
/app/backend/modules/finanzas/ingresos.py:483:    cortes = _cortes_caja_db.copy()
/app/backend/modules/finanzas/ingresos.py:557:    cortes = _cortes_caja_db.copy()
/app/backend/modules/finanzas/ingresos.py:692:    _movimientos_banco_db.extend(movimientos_extraidos)
/app/backend/modules/finanzas/ingresos.py:708:    movimientos = _movimientos_banco_db.copy()
/app/backend/modules/finanzas/historical_kpis_repository.py:29:    Ya no consulta MongoDB db.servers.
/app/backend/modules/finanzas/propinas_tpv/service.py:18:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/finanzas/propinas_tpv/service.py:26:# FASE T2.4: Usar server_registry centralizado en lugar de MongoDB
/app/backend/modules/finanzas/propinas_tpv/service.py:45:    def __init__(self, db: AsyncIOMotorDatabase):
/app/backend/modules/finanzas/propinas_tpv/service.py:77:        # Ya no usar MongoDB: self.db['servers']
/app/backend/modules/finanzas/propinas_tpv/__init__.py:10:# - MongoDB = Solo cache de lectura rápida (propinas_cache_*)
/app/backend/modules/finanzas/propinas_tpv/__init__.py:23:# - NO toca colecciones existentes de MongoDB
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:6:FASE T2.3 (Mayo 2026): Migrado a server_registry.py (elimina MongoDB db.servers)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:10:- MongoDB = Solo cache
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:32:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:58:    FASE T2.3: Reemplaza db.servers.find_one()
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:82:    FASE T2.3: Reemplaza db.servers.find({system_type: 'SoftRestaurant'})
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:115:    """Obtiene la conexión a MongoDB."""
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:128:async def health_check_sql(db: AsyncIOMotorDatabase = Depends(get_db)):
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:131:        # Verificar MongoDB (cache)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:132:        await db.command('ping')
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:144:            "arquitectura": "SQL Server (persistencia) + MongoDB (cache)",
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:147:            "mongodb_connected": True,
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:169:    - Crea índices de cache en MongoDB
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:177:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:210:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:219:    4. Invalida cache MongoDB
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:248:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:277:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:309:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:330:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:349:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:387:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:424:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:426:    """Obtiene estadísticas del cache MongoDB."""
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:440:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:466:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:470:        # FASE T2.3: Usar server_registry en lugar de db.servers
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:499:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:503:        # FASE T2.3: Usar server_registry en lugar de db.servers
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:569:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:573:        # FASE T2.3: Usar server_registry en lugar de db.servers
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:631:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:655:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:15:- MongoDB = Solo cache (gestionado por cache_manager.py)
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:18:- Este repositorio NO toca colecciones MongoDB existentes
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:54:    def __init__(self, mongo_db):
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:59:            mongo_db: Conexión a MongoDB (conservada por compatibilidad, no usada para conexión EDARSAHUB)
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:61:        self.mongo_db = mongo_db
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:72:        Ya no consulta MongoDB db.servers.
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:722:        Estructura compatible con el formato anterior (MongoDB).
/app/backend/modules/finanzas/propinas_tpv/repository_edarsahub.py:5:Reemplaza la lectura de MongoDB para consultas financieras.
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:8:- Gestión de cache en MongoDB
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:13:- MongoDB = Solo cache de lectura rápida
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:32:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:39:    Gestor de cache MongoDB para el módulo de Propinas TPV.
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:53:    def __init__(self, db: AsyncIOMotorDatabase):
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:58:            db: Conexión a MongoDB
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:5:Reemplazan la lectura de MongoDB para consultas financieras.
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:75:    # Buscar en MongoDB las empresas y sus unidades
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:77:        empresas = await db.empresas.find(
/app/backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:220:    Compatible con formato anterior de MongoDB.
/app/backend/modules/finanzas/propinas_tpv/repository.py:9:- Operaciones CRUD en MongoDB (colecciones nuevas)
/app/backend/modules/finanzas/propinas_tpv/repository.py:20:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/finanzas/propinas_tpv/repository.py:36:    2. MongoDB: SOLO escribe en colecciones nuevas (propinas_control, propinas_config)
/app/backend/modules/finanzas/propinas_tpv/repository.py:40:    def __init__(self, db: AsyncIOMotorDatabase):
/app/backend/modules/finanzas/propinas_tpv/repository.py:42:        self.collection_control = db['propinas_control']
/app/backend/modules/finanzas/propinas_tpv/repository.py:43:        self.collection_config = db['propinas_config']
/app/backend/modules/finanzas/propinas_tpv/repository.py:385:    # OPERACIONES MONGODB - COLECCIÓN propinas_control
/app/backend/modules/finanzas/propinas_tpv/repository.py:436:        result = await self.collection_control.update_one(
/app/backend/modules/finanzas/propinas_tpv/repository.py:474:        cursor = self.collection_control.find(
/app/backend/modules/finanzas/propinas_tpv/repository.py:502:        return await self.collection_control.count_documents(filtro)
/app/backend/modules/finanzas/propinas_tpv/repository.py:506:        return await self.collection_control.find_one(
/app/backend/modules/finanzas/propinas_tpv/repository.py:537:        result = await self.collection_control.update_one(
/app/backend/modules/finanzas/propinas_tpv/repository.py:600:        result = await self.collection_control.aggregate(pipeline).to_list(length=1)
/app/backend/modules/finanzas/propinas_tpv/repository.py:618:    # OPERACIONES MONGODB - COLECCIÓN propinas_config
/app/backend/modules/finanzas/propinas_tpv/repository.py:646:            config = await self.collection_config.find_one(
/app/backend/modules/finanzas/propinas_tpv/repository.py:660:            config = await self.collection_config.find_one(
/app/backend/modules/finanzas/propinas_tpv/repository.py:673:        config = await self.collection_config.find_one(
/app/backend/modules/finanzas/propinas_tpv/repository.py:702:        await self.collection_config.insert_one(config_data)
/app/backend/modules/finanzas/propinas_tpv/repository.py:715:        result = await self.collection_config.update_one(
/app/backend/modules/finanzas/propinas_tpv/repository.py:723:        cursor = self.collection_config.find({}, {'_id': 0})
/app/backend/modules/finanzas/propinas_tpv/repository.py:736:        await self.collection_control.create_index(
/app/backend/modules/finanzas/propinas_tpv/repository.py:748:        await self.collection_control.create_index(
/app/backend/modules/finanzas/propinas_tpv/repository.py:753:        await self.collection_control.create_index(
/app/backend/modules/finanzas/propinas_tpv/repository.py:759:        await self.collection_config.create_index(
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:9:- Orquestación de SQL Server (escritura) + MongoDB (cache/lectura)
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:14:- ESCRITURA: Siempre a SQL Server → Invalidar cache MongoDB
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:15:- LECTURA: Cache MongoDB → Si miss, SQL Server → Actualizar cache
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:28:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:38:# FASE T2.4: Usar server_registry centralizado en lugar de MongoDB
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:51:    SoftRestaurant (Lectura) → SQL Server (Persistencia) → MongoDB (Cache)
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:61:    def __init__(self, db: AsyncIOMotorDatabase):
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:76:        2. Crea índices de cache en MongoDB
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:144:        5. Invalidar cache MongoDB
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:158:        # Ya no usar MongoDB: self.db['servers']
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:341:        1. Buscar en cache MongoDB
/app/backend/modules/finanzas/propinas_tpv/routes.py:20:FASE T2.3 (Mayo 2026): Migrado a server_registry.py (elimina MongoDB db.servers)
/app/backend/modules/finanzas/propinas_tpv/routes.py:34:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/finanzas/propinas_tpv/routes.py:61:    FASE T2.3: Reemplaza db.servers.find_one()
/app/backend/modules/finanzas/propinas_tpv/routes.py:87:    FASE T2.3: Reemplaza db.servers.find({system_type: 'SoftRestaurant'})
/app/backend/modules/finanzas/propinas_tpv/routes.py:122:    Obtiene la conexión a MongoDB.
/app/backend/modules/finanzas/propinas_tpv/routes.py:141:    empresas = await db.empresas.find(
/app/backend/modules/finanzas/propinas_tpv/routes.py:167:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:170:        await db.command('ping')
/app/backend/modules/finanzas/propinas_tpv/routes.py:171:        collections = await db.list_collection_names()
/app/backend/modules/finanzas/propinas_tpv/routes.py:172:        propinas_control_exists = 'propinas_control' in collections
/app/backend/modules/finanzas/propinas_tpv/routes.py:173:        propinas_config_exists = 'propinas_config' in collections
/app/backend/modules/finanzas/propinas_tpv/routes.py:180:            "mongodb_connected": True,
/app/backend/modules/finanzas/propinas_tpv/routes.py:213:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:234:    - Crea índices en MongoDB
/app/backend/modules/finanzas/propinas_tpv/routes.py:242:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:282:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:285:        # FASE T2.3: Usar server_registry en lugar de db.servers
/app/backend/modules/finanzas/propinas_tpv/routes.py:322:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:325:        # FASE T2.3: Usar server_registry en lugar de db.servers
/app/backend/modules/finanzas/propinas_tpv/routes.py:398:    FASE 1B: Consulta propinas de un período SIN guardar en MongoDB.
/app/backend/modules/finanzas/propinas_tpv/routes.py:411:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:414:        # FASE T2.3: Usar server_registry en lugar de db.servers
/app/backend/modules/finanzas/propinas_tpv/routes.py:481:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:510:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:540:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:560:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:582:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:605:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:636:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/routes.py:660:    db: AsyncIOMotorDatabase = Depends(get_db)
/app/backend/modules/finanzas/propinas_tpv/models.py:131:    """Schema completo del documento en MongoDB"""
/app/backend/modules/finanzas/propinas_tpv/models.py:197:    """Schema completo en MongoDB"""
/app/backend/modules/finanzas/repository_softrestaurant.py:187:            db: Instancia de MongoDB (opcional, para compatibilidad)
/app/backend/modules/finanzas/cuentas_bancarias.py:8:- NO usar MongoDB
/app/backend/modules/finanzas/repository_mpro.py:14:    - Credenciales desde EDARSAHUB/server_registry.py (no MongoDB)
/app/backend/modules/finanzas/repository_mpro.py:40:            db: Instancia de MongoDB (solo para fallback legacy, preferir SQL)
/app/backend/modules/finanzas/repository_mpro.py:50:        FALLBACK: MongoDB solo si SQL falla (config_origin = MONGODB_LEGACY)
/app/backend/modules/finanzas/repository_mpro.py:63:                allow_mongo_fallback=True,
/app/backend/modules/manuales_operativos/service.py:16:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/manuales_operativos/service.py:45:    COLLECTION_NAME = "manuales_operativos"
/app/backend/modules/manuales_operativos/service.py:48:    def __init__(self, db: AsyncIOMotorDatabase):
/app/backend/modules/manuales_operativos/service.py:50:        self.collection = db[self.COLLECTION_NAME]
/app/backend/modules/manuales_operativos/service.py:52:    async def init_collection(self):
/app/backend/modules/manuales_operativos/service.py:56:            await self.collection.create_index("proceso_id", unique=True)
/app/backend/modules/manuales_operativos/service.py:58:            await self.collection.create_index([("modulo", 1), ("empresa_id", 1)])
/app/backend/modules/manuales_operativos/service.py:60:            await self.collection.create_index("created_at")
/app/backend/modules/manuales_operativos/service.py:62:            await self.collection.create_index("nombre_proceso")
/app/backend/modules/manuales_operativos/service.py:63:            logger.info(f"Colección {self.COLLECTION_NAME} inicializada con índices")
/app/backend/modules/manuales_operativos/service.py:89:            existing = await self.collection.find_one({"proceso_id": proceso_id})
/app/backend/modules/manuales_operativos/service.py:176:            # Guardar en MongoDB
/app/backend/modules/manuales_operativos/service.py:177:            await self.collection.insert_one(manual_doc)
/app/backend/modules/manuales_operativos/service.py:472:        doc = await self.collection.find_one({"id": manual_id})
/app/backend/modules/manuales_operativos/service.py:480:        doc = await self.collection.find_one({"proceso_id": proceso_id})
/app/backend/modules/manuales_operativos/service.py:501:        total = await self.collection.count_documents(filtro)
/app/backend/modules/manuales_operativos/service.py:502:        cursor = self.collection.find(filtro).sort("created_at", -1).skip(skip).limit(limite)
/app/backend/modules/manuales_operativos/service.py:618:def get_manual_service(db: AsyncIOMotorDatabase) -> ManualOperativoService:
/app/backend/modules/manuales_operativos/__init__.py:33:    """Inicializa el módulo con la conexión a MongoDB."""
/app/backend/modules/manuales_operativos/triggers.py:20:from motor.motor_asyncio import AsyncIOMotorDatabase
/app/backend/modules/manuales_operativos/triggers.py:21:from pymongo.database import Database as PyMongoDatabase
/app/backend/modules/manuales_operativos/triggers.py:32:    db: AsyncIOMotorDatabase,
/app/backend/modules/manuales_operativos/triggers.py:43:        db: Conexión a MongoDB
/app/backend/modules/manuales_operativos/triggers.py:73:    db: AsyncIOMotorDatabase,
/app/backend/modules/manuales_operativos/triggers.py:80:    proceso = await db.automatizaciones_operativas_compras.find_one({"id": proceso_id})
/app/backend/modules/manuales_operativos/triggers.py:92:    bitacora = await db.automatizaciones_bitacora.find(
/app/backend/modules/manuales_operativos/triggers.py:107:        users_cursor = db.users.find({"id": {"$in": list(user_ids)}}, {"id": 1, "email": 1, "full_name": 1})
/app/backend/modules/manuales_operativos/triggers.py:121:async def verificar_y_generar_manuales_pendientes(db: AsyncIOMotorDatabase):
/app/backend/modules/manuales_operativos/triggers.py:137:    cursor = db.automatizaciones_operativas_compras.find({
/app/backend/modules/manuales_operativos/triggers.py:161:    db_sync: PyMongoDatabase,
/app/backend/modules/manuales_operativos/triggers.py:171:        db_sync: Conexión pymongo (síncrona)
/app/backend/modules/manuales_operativos/triggers.py:189:def _generar_manual_compras_sync(db_sync: PyMongoDatabase, proceso_id: str) -> Optional[str]:
/app/backend/modules/manuales_operativos/triggers.py:198:    collection = db_sync["manuales_operativos"]
/app/backend/modules/manuales_operativos/triggers.py:201:    existing = collection.find_one({"proceso_id": proceso_id})
/app/backend/modules/manuales_operativos/triggers.py:372:    collection.insert_one(manual_doc)
/app/backend/modules/manuales_operativos/routes.py:29:    """Inicializa el módulo con la conexión a MongoDB."""
/app/backend/modules/manuales_operativos/routes.py:143:        proceso = await _db.automatizaciones_operativas_compras.find_one({"id": proceso_id})
/app/backend/modules/manuales_operativos/routes.py:147:        bitacora = await _db.automatizaciones_bitacora.find(
/app/backend/modules/manuales_operativos/schemas.py:143:    """Schema del manual como está almacenado en MongoDB."""
/app/backend/modules/compras/repository_compras_sql.py:6:FASE: COMPRAS-MONGO-001-F1 (Mayo 2026)
/app/backend/modules/compras/repository_compras_sql.py:7:- Migración de compras_params de MongoDB a EDARSAHUB SQL
/app/backend/modules/compras/repository_compras_sql.py:12:- CERO dependencias de MongoDB
/app/backend/modules/compras/repository_compras_sql.py:13:- Reemplaza funciones get_compras_params y save_compras_params de MongoDB
/app/backend/modules/compras/repository_compras_sql.py:60:-- Reemplaza colección MongoDB: compras_params
/app/backend/modules/compras/repository_compras_sql.py:132:    REEMPLAZA: get_compras_params() de MongoDB
/app/backend/modules/compras/repository_compras_sql.py:206:    REEMPLAZA: save_compras_params() de MongoDB
/app/backend/modules/compras/__init__.py:13:- repository.py: Acceso a MongoDB y SQL Server
/app/backend/modules/compras/__init__.py:57:    Inicializa el módulo de compras con la conexión a MongoDB.
/app/backend/modules/compras/__init__.py:60:        database: Instancia de AsyncIOMotorDatabase
/app/backend/modules/compras/repository.py:9:FASE COMPRAS-MONGO-001-F1 (Mayo 2026):
/app/backend/modules/compras/repository.py:10:- Parámetros de compras migrados de MongoDB a EDARSAHUB SQL
/app/backend/modules/compras/repository.py:12:- CERO MongoDB productivo para parámetros
/app/backend/modules/compras/repository.py:71:# INYECCIÓN DE DEPENDENCIA: MongoDB
/app/backend/modules/compras/repository.py:75:_stub_mode = False  # Flag para indicar si estamos en modo stub (sin MongoDB)
/app/backend/modules/compras/repository.py:80:    Inicializa el repositorio con la conexión a MongoDB.
/app/backend/modules/compras/repository.py:88:        logger.warning("[COMPRAS_REPO] Inicializado en modo STUB - funcionalidad MongoDB limitada")
/app/backend/modules/compras/repository.py:93:    Obtiene la conexión a MongoDB inyectada.
/app/backend/modules/compras/repository.py:106:    """Retorna True si el repositorio está en modo stub (sin MongoDB)."""
/app/backend/modules/compras/repository.py:112:    Descifra el password de un servidor obtenido de MongoDB.
/app/backend/modules/compras/repository.py:141:    FASE T3.1: Migrado de MongoDB db.servers a server_registry (EDARSAHUB).
/app/backend/modules/compras/repository.py:143:    # FASE T3.1: Usar server_registry en lugar de MongoDB
/app/backend/modules/compras/repository.py:156:# FASE: COMPRAS-MONGO-001-F1
/app/backend/modules/compras/repository.py:157:# Migrado de MongoDB a EDARSAHUB SQL Server
/app/backend/modules/compras/repository.py:164:    MIGRADO: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
/app/backend/modules/compras/repository.py:181:    MIGRADO: Ahora escribe a EDARSAHUB SQL en lugar de MongoDB.
/app/backend/modules/compras/historical_kpis_repository.py:32:    FASE T3.1: Migrado de MongoDB db.servers a EDARSAHUB_CONFIG de server_registry.
/app/backend/modules/compras/historical_kpis_repository.py:33:    Ya no consulta MongoDB para obtener conexión EDARSAHUB.
/app/backend/modules/compras/repository_pedidos_sql.py:4:COMPRAS-MONGO-001-F2: Migración de MongoDB a EDARSAHUB SQL
/app/backend/modules/compras/repository_pedidos_sql.py:6:Migra las siguientes colecciones de MongoDB a SQL:
/app/backend/modules/compras/repository_pedidos_sql.py:13:- #2: CERO dependencias de MongoDB
/app/backend/.pytest_cache/v/cache/nodeids:2:  "tests/test_core_db.py::TestExecuteSqlQueryErrors::test_connection_error_handling",
/app/backend/.pytest_cache/v/cache/nodeids:3:  "tests/test_core_db.py::TestExecuteSqlQueryErrors::test_partial_result_handling",
/app/backend/.pytest_cache/v/cache/nodeids:4:  "tests/test_core_db.py::TestExecuteSqlQueryErrors::test_sql_error_handling",
/app/backend/.pytest_cache/v/cache/nodeids:5:  "tests/test_core_db.py::TestExecuteSqlQueryErrors::test_timeout_error_handling",
/app/backend/.pytest_cache/v/cache/nodeids:6:  "tests/test_core_db.py::TestExecuteSqlQueryWithMocks::test_datetime_conversion_in_results",
/app/backend/.pytest_cache/v/cache/nodeids:7:  "tests/test_core_db.py::TestExecuteSqlQueryWithMocks::test_empty_result_handling",
/app/backend/.pytest_cache/v/cache/nodeids:8:  "tests/test_core_db.py::TestExecuteSqlQueryWithMocks::test_execute_sql_query_fallback_imports",
/app/backend/.pytest_cache/v/cache/nodeids:9:  "tests/test_core_db.py::TestExecuteSqlQueryWithMocks::test_execute_sql_query_imports",
/app/backend/.pytest_cache/v/cache/nodeids:10:  "tests/test_core_db.py::TestExecuteSqlQueryWithMocks::test_execute_with_mock_pool_success",
/app/backend/.pytest_cache/v/cache/nodeids:11:  "tests/test_core_db.py::TestExecuteSqlQueryWithMocks::test_server_in_cooldown_returns_empty",
/app/backend/.pytest_cache/v/cache/nodeids:12:  "tests/test_core_db.py::TestParseSqlServerHost::test_custom_default_port",
/app/backend/.pytest_cache/v/cache/nodeids:13:  "tests/test_core_db.py::TestParseSqlServerHost::test_ddns_format",
/app/backend/.pytest_cache/v/cache/nodeids:14:  "tests/test_core_db.py::TestParseSqlServerHost::test_hostname_with_instance",
/app/backend/.pytest_cache/v/cache/nodeids:15:  "tests/test_core_db.py::TestParseSqlServerHost::test_hostname_with_port",
/app/backend/.pytest_cache/v/cache/nodeids:16:  "tests/test_core_db.py::TestParseSqlServerHost::test_instance_then_port",
/app/backend/.pytest_cache/v/cache/nodeids:17:  "tests/test_core_db.py::TestParseSqlServerHost::test_simple_hostname",
/app/backend/.pytest_cache/v/cache/nodeids:18:  "tests/test_core_db.py::TestParseSqlServerHost::test_with_spaces",
/app/backend/.pytest_cache/v/cache/nodeids:19:  "tests/test_core_db.py::TestServerCooldown::test_cooldown_info_structure",
/app/backend/.pytest_cache/v/cache/nodeids:20:  "tests/test_core_db.py::TestServerCooldown::test_get_server_cache_status",
/app/backend/.pytest_cache/v/cache/nodeids:21:  "tests/test_core_db.py::TestServerCooldown::test_mark_server_offline",
/app/backend/.pytest_cache/v/cache/nodeids:22:  "tests/test_core_db.py::TestServerCooldown::test_mark_server_online",
/app/backend/.pytest_cache/v/cache/nodeids:23:  "tests/test_core_db.py::TestServerCooldown::test_reset_server_cache",
/app/backend/.pytest_cache/v/cache/nodeids:24:  "tests/test_core_db.py::TestServerCooldown::test_server_not_in_cache",
/app/backend/.pytest_cache/v/cache/nodeids:25:  "tests/test_core_db.py::TestSqlQueryParameters::test_custom_timeout_accepted",
/app/backend/.pytest_cache/v/cache/nodeids:26:  "tests/test_core_db.py::TestSqlQueryParameters::test_default_timeout",
/app/backend/.pytest_cache/v/cache/nodeids:27:  "tests/test_core_db.py::TestSqlQueryParameters::test_port_is_integer",
/app/backend/.pytest_cache/v/cache/nodeids:28:  "tests/test_core_db.py::TestSqlQueryParameters::test_query_string_type"
/app/backend/scripts/solucion_operaciones_analisis.py:46:[A] Migración al Motor Robusto Centralizado: 
/app/backend/scripts/solucion_operaciones_analisis.py:63:# --- MOTOR DE CASCADA SIMULADO ---
/app/backend/scripts/run_historical_load_finanzas.py:61:COLLECTION_CHECKPOINTS = "finanzas_historical_load_checkpoints"
/app/backend/scripts/run_historical_load_finanzas.py:82:    """Obtiene conexión a MongoDB."""
/app/backend/scripts/run_historical_load_finanzas.py:87:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/scripts/run_historical_load_finanzas.py:88:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/run_historical_load_finanzas.py:89:    client = AsyncIOMotorClient(mongo_url)
/app/backend/scripts/run_historical_load_finanzas.py:106:    checkpoint = await db[COLLECTION_CHECKPOINTS].find_one({
/app/backend/scripts/run_historical_load_finanzas.py:131:    await db[COLLECTION_CHECKPOINTS].insert_one(new_checkpoint)
/app/backend/scripts/run_historical_load_finanzas.py:144:    await db[COLLECTION_CHECKPOINTS].update_one(
/app/backend/scripts/run_historical_load_finanzas.py:594:    cursor = db.servers.find({"active": True}, {"_id": 0})
/app/backend/scripts/motor_consolidacion_circuit_breaker.py:30:    Simula el motor lógico del tablero ejecutivo, integrando:
/app/backend/scripts/motor_consolidacion_circuit_breaker.py:66:        datos_historicos_unidad = monthly_data_db.get(unidad_id, monthly_data_db.get("cienfuegos"))
/app/backend/scripts/precheck_conectividad.py:11:    - Variable MONGO_URL configurada
/app/backend/scripts/precheck_conectividad.py:13:    - Acceso a la colección 'servers' en MongoDB
/app/backend/scripts/precheck_conectividad.py:20:from pymongo import MongoClient
/app/backend/scripts/precheck_conectividad.py:23:MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/precheck_conectividad.py:32:    # Conectar a MongoDB
/app/backend/scripts/precheck_conectividad.py:34:        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
/app/backend/scripts/precheck_conectividad.py:37:        print(f"\n✅ MongoDB conectado: {DB_NAME}")
/app/backend/scripts/precheck_conectividad.py:39:        print(f"\n❌ Error conectando a MongoDB: {e}")
/app/backend/scripts/precheck_conectividad.py:43:    servidores = list(db.servers.find({
/app/backend/scripts/reconcile_servers_sql_mongo.py:3:EDARSA HUB - Script de Reconciliación SQL ↔ MongoDB
/app/backend/scripts/reconcile_servers_sql_mongo.py:6:FASE 3B.2: Compara servidores entre EDARSAHUB SQL y MongoDB.
/app/backend/scripts/reconcile_servers_sql_mongo.py:9:    python reconcile_servers_sql_mongo.py [--apply]
/app/backend/scripts/reconcile_servers_sql_mongo.py:12:    Con --apply: sincroniza MongoDB para que sea espejo de SQL
/app/backend/scripts/reconcile_servers_sql_mongo.py:20:    - Solo escribe en MongoDB si --apply está presente
/app/backend/scripts/reconcile_servers_sql_mongo.py:35:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/scripts/reconcile_servers_sql_mongo.py:45:    build_legacy_mongo_server_document,
/app/backend/scripts/reconcile_servers_sql_mongo.py:67:    Ejecuta reconciliación SQL ↔ MongoDB.
/app/backend/scripts/reconcile_servers_sql_mongo.py:70:        apply: Si True, sincroniza MongoDB con SQL
/app/backend/scripts/reconcile_servers_sql_mongo.py:80:        'mongo_count': 0,
/app/backend/scripts/reconcile_servers_sql_mongo.py:83:        'mongo_only': [],
/app/backend/scripts/reconcile_servers_sql_mongo.py:101:        # Indexar por ID y mongodb_id
/app/backend/scripts/reconcile_servers_sql_mongo.py:103:        sql_by_mongodb_id = {s['mongodb_id']: s for s in sql_servers if s.get('mongodb_id')}
/app/backend/scripts/reconcile_servers_sql_mongo.py:105:        # 2. Obtener servidores desde MongoDB
/app/backend/scripts/reconcile_servers_sql_mongo.py:106:        print("Obteniendo servidores desde MongoDB...")
/app/backend/scripts/reconcile_servers_sql_mongo.py:107:        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/reconcile_servers_sql_mongo.py:110:        client = AsyncIOMotorClient(mongo_url)
/app/backend/scripts/reconcile_servers_sql_mongo.py:113:        mongo_servers = await db.servers.find({}, {'_id': 0}).to_list(1000)
/app/backend/scripts/reconcile_servers_sql_mongo.py:114:        report['mongo_count'] = len(mongo_servers)
/app/backend/scripts/reconcile_servers_sql_mongo.py:115:        print(f"  → {len(mongo_servers)} servidores en MongoDB")
/app/backend/scripts/reconcile_servers_sql_mongo.py:118:        mongo_by_id = {s['id']: s for s in mongo_servers}
/app/backend/scripts/reconcile_servers_sql_mongo.py:120:        # 3. Comparar SQL → MongoDB
/app/backend/scripts/reconcile_servers_sql_mongo.py:121:        print("\nComparando SQL → MongoDB...")
/app/backend/scripts/reconcile_servers_sql_mongo.py:123:            mongo_server = mongo_by_id.get(sql_id) or mongo_by_id.get(sql_server.get('mongodb_id'))
/app/backend/scripts/reconcile_servers_sql_mongo.py:125:            if not mongo_server:
/app/backend/scripts/reconcile_servers_sql_mongo.py:126:                # Servidor en SQL pero no en MongoDB
/app/backend/scripts/reconcile_servers_sql_mongo.py:132:                        mongo_doc = build_legacy_mongo_server_document(sql_server)
/app/backend/scripts/reconcile_servers_sql_mongo.py:134:                        await db.servers.insert_one(mongo_doc)
/app/backend/scripts/reconcile_servers_sql_mongo.py:136:                        print("    → Sincronizado a MongoDB")
/app/backend/scripts/reconcile_servers_sql_mongo.py:147:                mongo_name = mongo_server.get('name', mongo_server.get('nombre', ''))
/app/backend/scripts/reconcile_servers_sql_mongo.py:148:                if sql_name != mongo_name:
/app/backend/scripts/reconcile_servers_sql_mongo.py:149:                    diffs.append(f"name: SQL='{sql_name}' vs Mongo='{mongo_name}'")
/app/backend/scripts/reconcile_servers_sql_mongo.py:151:                if sql_server.get('system_type') != mongo_server.get('system_type'):
/app/backend/scripts/reconcile_servers_sql_mongo.py:152:                    diffs.append(f"system_type: SQL='{sql_server.get('system_type')}' vs Mongo='{mongo_server.get('system_type')}'")
/app/backend/scripts/reconcile_servers_sql_mongo.py:155:                mongo_active = mongo_server.get('active', mongo_server.get('activo'))
/app/backend/scripts/reconcile_servers_sql_mongo.py:156:                if sql_active != mongo_active:
/app/backend/scripts/reconcile_servers_sql_mongo.py:157:                    diffs.append(f"active: SQL={sql_active} vs Mongo={mongo_active}")
/app/backend/scripts/reconcile_servers_sql_mongo.py:159:                if sql_server.get('host') != mongo_server.get('host'):
/app/backend/scripts/reconcile_servers_sql_mongo.py:160:                    diffs.append(f"host: SQL='{sql_server.get('host')}' vs Mongo='{mongo_server.get('host')}'")
/app/backend/scripts/reconcile_servers_sql_mongo.py:172:                            mongo_doc = build_legacy_mongo_server_document(sql_server)
/app/backend/scripts/reconcile_servers_sql_mongo.py:173:                            await db.servers.update_one({'id': sql_id}, {'$set': mongo_doc})
/app/backend/scripts/reconcile_servers_sql_mongo.py:175:                            print("    → Actualizado en MongoDB")
/app/backend/scripts/reconcile_servers_sql_mongo.py:180:        # 4. Comparar MongoDB → SQL (detectar huérfanos)
/app/backend/scripts/reconcile_servers_sql_mongo.py:181:        print("\nComparando MongoDB → SQL...")
/app/backend/scripts/reconcile_servers_sql_mongo.py:182:        for mongo_id, mongo_server in mongo_by_id.items():
/app/backend/scripts/reconcile_servers_sql_mongo.py:183:            if mongo_id not in sql_by_id and mongo_id not in sql_by_mongodb_id:
/app/backend/scripts/reconcile_servers_sql_mongo.py:184:                report['mongo_only'].append(safe_server_summary(mongo_server))
/app/backend/scripts/reconcile_servers_sql_mongo.py:185:                report['warnings'].append(f"Servidor {mongo_id} existe en MongoDB pero NO en SQL (huérfano)")
/app/backend/scripts/reconcile_servers_sql_mongo.py:186:                print(f"  [MONGO_ONLY] {mongo_server.get('name', mongo_id)} (huérfano)")
/app/backend/scripts/reconcile_servers_sql_mongo.py:191:        elif report['sql_only'] or report['mongo_only'] or report['diffs']:
/app/backend/scripts/reconcile_servers_sql_mongo.py:207:    print("REPORTE DE RECONCILIACIÓN SQL ↔ MONGODB")
/app/backend/scripts/reconcile_servers_sql_mongo.py:213:    print(f"Servidores MongoDB: {report['mongo_count']}")
/app/backend/scripts/reconcile_servers_sql_mongo.py:216:    print(f"Solo en MongoDB: {len(report['mongo_only'])}")
/app/backend/scripts/reconcile_servers_sql_mongo.py:241:    print("EDARSA HUB - Reconciliación SQL ↔ MongoDB")
/app/backend/scripts/reconcile_servers_sql_mongo.py:242:    print(f"Modo: {'APPLY (sincronizará MongoDB)' if apply else 'DRY-RUN (solo reporta)'}")
/app/backend/scripts/ddl_fase2_operativo_tablas.sql:10:-- Reemplaza: MongoDB notificaciones_log
/app/backend/scripts/ddl_fase2_operativo_tablas.sql:47:-- Reemplaza: MongoDB justificaciones_inventario
/app/backend/scripts/ddl_fase2_operativo_tablas.sql:84:-- Reemplaza: MongoDB decisiones_auditoria
/app/backend/scripts/ddl_fase2_operativo_tablas.sql:115:-- Reemplaza: MongoDB historial_asignaciones
/app/backend/scripts/ddl_fase2_operativo_tablas.sql:148:-- Reemplaza: MongoDB responsabilidades
/app/backend/scripts/ddl_fase2_operativo_tablas.sql:189:-- Reemplaza: MongoDB cargos_responsabilidad
/app/backend/scripts/ddl_fase2_operativo_tablas.sql:233:-- Reemplaza: MongoDB historial de cargos
/app/backend/scripts/ddl_fase2_operativo_tablas.sql:269:-- Reemplaza: MongoDB tareas_operativas_compras
/app/backend/scripts/ddl_fase2_operativo_tablas.sql:307:-- Reemplaza: MongoDB auditoria_compras_bitacora
/app/backend/scripts/ddl_fase2_operativo_tablas.sql:337:-- Reemplaza: MongoDB pedidos_procesados_automatizacion
/app/backend/scripts/ddl_fase2_operativo_tablas.sql:367:-- Reemplaza: MongoDB auditorias programadas
/app/backend/scripts/ddl_fase2_operativo_tablas.sql:406:-- Reemplaza: MongoDB documentos_generados
/app/backend/scripts/correccion_proyeccion_y_moneda_final.py:145:        logger.info("Verificando funcionamiento óptimo en el motor SQL:")
/app/backend/scripts/consolidado_general_sistema_comercial.py:29:# Configuración del motor SQL Server de EDARSAHUB (Puerto 1433 por defecto)
/app/backend/scripts/consolidado_general_sistema_comercial.py:361:                SET @LogMessage = 'Ventas intermedias vacías. El motor comercial preserva los valores de respaldo de EDARSA.';
/app/backend/scripts/carga_historica_fase23.py:5:⚠️ DEPRECATED (Mayo 2026): Este script usa MongoDB que ha sido reemplazado por SQL Server.
/app/backend/scripts/carga_historica_fase23.py:6:Las referencias a self.db.* ya no funcionan en producción. Este archivo se mantiene
/app/backend/scripts/carga_historica_fase23.py:52:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/scripts/carga_historica_fase23.py:53:from pymongo import MongoClient
/app/backend/scripts/carga_historica_fase23.py:56:MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/carga_historica_fase23.py:96:                "comando": f"db.kpis_comercial.deleteMany({{created_by: '{UPDATED_BY}'}})",
/app/backend/scripts/carga_historica_fase23.py:102:        """Establece conexión a MongoDB."""
/app/backend/scripts/carga_historica_fase23.py:103:        self.client = AsyncIOMotorClient(MONGO_URL)
/app/backend/scripts/carga_historica_fase23.py:105:        logger.info(f"Conectado a MongoDB: {DB_NAME}")
/app/backend/scripts/carga_historica_fase23.py:108:        """Cierra conexión a MongoDB."""
/app/backend/scripts/carga_historica_fase23.py:111:            logger.info("Desconectado de MongoDB")
/app/backend/scripts/carga_historica_fase23.py:142:        cursor = self.db.servers.find({
/app/backend/scripts/carga_historica_fase23.py:153:        cursor = self.db.empresas.find({})
/app/backend/scripts/carga_historica_fase23.py:379:            validaciones["total_documentos"] = await self.db.kpis_comercial.count_documents({})
/app/backend/scripts/carga_historica_fase23.py:394:            duplicados = await self.db.kpis_comercial.aggregate(pipeline).to_list(100)
/app/backend/scripts/carga_historica_fase23.py:401:            estados = await self.db.kpis_comercial.aggregate(pipeline_estados).to_list(10)
/app/backend/scripts/carga_historica_fase23.py:406:            min_doc = await self.db.kpis_comercial.find_one(sort=[("fecha", 1)])
/app/backend/scripts/carga_historica_fase23.py:407:            max_doc = await self.db.kpis_comercial.find_one(sort=[("fecha", -1)])
/app/backend/scripts/carga_historica_fase23.py:417:            servers = await self.db.kpis_comercial.aggregate(pipeline_servers).to_list(20)
/app/backend/scripts/ddl_costos_alertas_001b.py:6:MÁXIMAS: EDARSAHUB SQL es el cerebro. CERO MongoDB.
/app/backend/scripts/ddl_costos_alertas_001b.py:618:    print("MÁXIMAS: EDARSAHUB SQL es el cerebro. CERO MongoDB.")
/app/backend/scripts/ddl_auth_reset_p2_rate_limit_audit.sql:6:-- OBJETIVO: Eliminar dependencias de MongoDB en password_reset.py
/app/backend/scripts/ddl_auth_reset_p2_rate_limit_audit.sql:14:-- Reemplaza: MongoDB collection rate_limit_password_reset
/app/backend/scripts/ddl_auth_reset_p2_rate_limit_audit.sql:54:-- Reemplaza: MongoDB collection audit_password_reset
/app/backend/scripts/consolidado_general_sistema_comercial_v2.py:11:             posee un motor de simulación local offline completo de alta resiliencia.
/app/backend/scripts/create_scheduler_tables.py:3:Reemplaza las colecciones MongoDB para los jobs de detección.
/app/backend/scripts/setup_kpis_indexes.py:22:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/scripts/setup_kpis_indexes.py:30:COLLECTION_NAME = "kpis_comercial"
/app/backend/scripts/setup_kpis_indexes.py:46:        db: Conexión a MongoDB
/app/backend/scripts/setup_kpis_indexes.py:51:    collection = db[COLLECTION_NAME]
/app/backend/scripts/setup_kpis_indexes.py:58:        await collection.create_index(
/app/backend/scripts/setup_kpis_indexes.py:85:        await collection.create_index(
/app/backend/scripts/setup_kpis_indexes.py:101:        await collection.create_index(
/app/backend/scripts/setup_kpis_indexes.py:117:        await collection.create_index(
/app/backend/scripts/setup_kpis_indexes.py:133:        await collection.create_index(
/app/backend/scripts/setup_kpis_indexes.py:149:        await collection.create_index(
/app/backend/scripts/setup_kpis_indexes.py:184:    collection = db[COLLECTION_NAME]
/app/backend/scripts/setup_kpis_indexes.py:185:    indexes = await collection.index_information()
/app/backend/scripts/setup_kpis_indexes.py:212:    # Obtener configuración de MongoDB
/app/backend/scripts/setup_kpis_indexes.py:213:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/setup_kpis_indexes.py:216:    logging.info(f"[SETUP-INDEX] Conectando a MongoDB: {db_name}")
/app/backend/scripts/setup_kpis_indexes.py:218:    client = AsyncIOMotorClient(mongo_url)
/app/backend/scripts/create_workflow_tables.sql:3:-- Migración de MongoDB a SQL Server
/app/backend/scripts/validar_post_carga.py:18:from pymongo import MongoClient
/app/backend/scripts/validar_post_carga.py:21:MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/validar_post_carga.py:32:    client = MongoClient(MONGO_URL)
/app/backend/scripts/validar_post_carga.py:51:    duplicados = list(db.kpis_comercial.aggregate(pipeline))
/app/backend/scripts/validar_post_carga.py:64:    total = db.kpis_comercial.count_documents({})
/app/backend/scripts/validar_post_carga.py:65:    nuevos = db.kpis_comercial.count_documents({"created_by": CARGA_MARKER})
/app/backend/scripts/validar_post_carga.py:80:    min_doc = db.kpis_comercial.find_one(sort=[("fecha", 1)])
/app/backend/scripts/validar_post_carga.py:81:    max_doc = db.kpis_comercial.find_one(sort=[("fecha", -1)])
/app/backend/scripts/validar_post_carga.py:111:    servidores = list(db.kpis_comercial.aggregate(pipeline_srv))
/app/backend/scripts/validar_post_carga.py:125:    estados = list(db.kpis_comercial.aggregate(pipeline_estado))
/app/backend/scripts/encrypt_existing_server_secrets.py:34:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/scripts/encrypt_existing_server_secrets.py:210:async def encrypt_server_secrets_mongo(server_id: str, encrypt_password: bool, encrypt_api_key: bool) -> dict:
/app/backend/scripts/encrypt_existing_server_secrets.py:211:    """Cifra los secretos de un servidor en MongoDB."""
/app/backend/scripts/encrypt_existing_server_secrets.py:212:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/encrypt_existing_server_secrets.py:215:    client = AsyncIOMotorClient(mongo_url)
/app/backend/scripts/encrypt_existing_server_secrets.py:219:        server = await db.servers.find_one({'id': server_id})
/app/backend/scripts/encrypt_existing_server_secrets.py:222:            return {'success': True, 'message': 'Server not in MongoDB'}
/app/backend/scripts/encrypt_existing_server_secrets.py:238:            await db.servers.update_one({'id': server_id}, {'$set': updates})
/app/backend/scripts/encrypt_existing_server_secrets.py:328:        # Cifrar en MongoDB
/app/backend/scripts/encrypt_existing_server_secrets.py:329:        mongo_result = await encrypt_server_secrets_mongo(
/app/backend/scripts/encrypt_existing_server_secrets.py:335:        if not mongo_result['success']:
/app/backend/scripts/encrypt_existing_server_secrets.py:336:            print("ERROR MONGO")
/app/backend/scripts/encrypt_existing_server_secrets.py:337:            report['warnings'].append(f"{name}: MongoDB error - {mongo_result.get('error', 'Unknown')}")
/app/backend/scripts/encrypt_existing_server_secrets.py:345:            'mongo': 'OK' if mongo_result['success'] else 'PARTIAL'
/app/backend/scripts/motor_acumulacion_estacional.py:2:Solución Analítica: Motor de Acumulación Comercial
/app/backend/scripts/motor_acumulacion_estacional.py:4:He ajustado el motor de acumulación de forma matemática y dinámica para que 
/app/backend/scripts/rotate_server_secret_key.py:23:    --include-mongo     Sincronizar MongoDB espejo
/app/backend/scripts/rotate_server_secret_key.py:24:    --only-sql          Solo SQL, ignorar MongoDB
/app/backend/scripts/rotate_server_secret_key.py:281:    include_mongo: bool = False
/app/backend/scripts/rotate_server_secret_key.py:301:        'mongo_synced': 0,
/app/backend/scripts/rotate_server_secret_key.py:369:                # Sincronizar MongoDB si aplica
/app/backend/scripts/rotate_server_secret_key.py:370:                if include_mongo:
/app/backend/scripts/rotate_server_secret_key.py:372:                        sync_to_mongodb(server_id, updates)
/app/backend/scripts/rotate_server_secret_key.py:373:                        result['mongo_synced'] += 1
/app/backend/scripts/rotate_server_secret_key.py:374:                        logger.info(f"[SECRET_ROTATION][MONGO_SYNC_SUCCESS] {server_name}")
/app/backend/scripts/rotate_server_secret_key.py:376:                        logger.warning(f"[SECRET_ROTATION][PARTIAL_SYNC] {server_name}: MongoDB sync failed")
/app/backend/scripts/rotate_server_secret_key.py:377:                        result['errors'].append(f"{server_name}: MongoDB sync failed - {type(e).__name__}")
/app/backend/scripts/rotate_server_secret_key.py:393:def sync_to_mongodb(server_id: str, updates: Dict):
/app/backend/scripts/rotate_server_secret_key.py:395:    Sincroniza secretos rotados a MongoDB.
/app/backend/scripts/rotate_server_secret_key.py:399:    from core.db import get_mongo_db
/app/backend/scripts/rotate_server_secret_key.py:401:    db = get_mongo_db()
/app/backend/scripts/rotate_server_secret_key.py:403:        raise Exception("MongoDB no disponible")
/app/backend/scripts/rotate_server_secret_key.py:405:    # Buscar y actualizar en MongoDB
/app/backend/scripts/rotate_server_secret_key.py:406:    mongo_updates = {}
/app/backend/scripts/rotate_server_secret_key.py:408:        # Mapear campos SQL a MongoDB
/app/backend/scripts/rotate_server_secret_key.py:409:        mongo_field = field.replace('_encrypted', '')
/app/backend/scripts/rotate_server_secret_key.py:410:        mongo_updates[mongo_field] = value
/app/backend/scripts/rotate_server_secret_key.py:412:    if mongo_updates:
/app/backend/scripts/rotate_server_secret_key.py:413:        db.servidores_conexiones.update_one(
/app/backend/scripts/rotate_server_secret_key.py:415:            {'$set': mongo_updates}
/app/backend/scripts/rotate_server_secret_key.py:447:        'mongo_synced': 0,
/app/backend/scripts/rotate_server_secret_key.py:474:        report['mongo_synced'] = rotation_result['mongo_synced']
/app/backend/scripts/rotate_server_secret_key.py:515:        print(f"MongoDB sincronizado: {report['mongo_synced']}")
/app/backend/scripts/rotate_server_secret_key.py:536:    parser.add_argument('--include-mongo', action='store_true', help='Sincronizar MongoDB espejo')
/app/backend/scripts/rotate_server_secret_key.py:537:    parser.add_argument('--only-sql', action='store_true', help='Solo SQL, ignorar MongoDB')
/app/backend/scripts/rotate_server_secret_key.py:610:            include_mongo=args.include_mongo and not args.only_sql
/app/backend/scripts/rotate_server_secret_key.py:616:        if args.include_mongo:
/app/backend/scripts/rotate_server_secret_key.py:617:            print(f"   → MongoDB sincronizado: {rotation_result['mongo_synced']}")
/app/backend/scripts/create_unidades_negocio_table.py:5:eliminando la dependencia de MongoDB para esta información.
/app/backend/scripts/encrypt_core_server_secrets.py:46:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/scripts/encrypt_core_server_secrets.py:84:        mongodb_id
/app/backend/scripts/encrypt_core_server_secrets.py:152:                'mongodb_id': server.get('mongodb_id'),
/app/backend/scripts/encrypt_core_server_secrets.py:250:async def sync_core_to_mongo(server_id: str, mongodb_id: str) -> dict:
/app/backend/scripts/encrypt_core_server_secrets.py:252:    Sincroniza el estado de cifrado CORE a MongoDB (si tiene secretos).
/app/backend/scripts/encrypt_core_server_secrets.py:254:    Note: MongoDB generalmente no tiene secretos de CORE, solo metadatos.
/app/backend/scripts/encrypt_core_server_secrets.py:257:    if not mongodb_id:
/app/backend/scripts/encrypt_core_server_secrets.py:258:        return {'success': True, 'message': 'No mongodb_id'}
/app/backend/scripts/encrypt_core_server_secrets.py:260:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/encrypt_core_server_secrets.py:263:    client = AsyncIOMotorClient(mongo_url)
/app/backend/scripts/encrypt_core_server_secrets.py:267:        server = await db.servers.find_one({'id': mongodb_id})
/app/backend/scripts/encrypt_core_server_secrets.py:270:            return {'success': True, 'message': 'CORE not in MongoDB (normal)'}
/app/backend/scripts/encrypt_core_server_secrets.py:284:            await db.servers.update_one({'id': mongodb_id}, {'$set': updates})
/app/backend/scripts/encrypt_core_server_secrets.py:285:            return {'success': True, 'encrypted_mongo': len(updates)}
/app/backend/scripts/encrypt_core_server_secrets.py:287:        return {'success': True, 'message': 'No secrets in MongoDB'}
/app/backend/scripts/encrypt_core_server_secrets.py:316:        'mongo_synced': 0,
/app/backend/scripts/encrypt_core_server_secrets.py:369:        mongodb_id = server_info.get('mongodb_id')
/app/backend/scripts/encrypt_core_server_secrets.py:395:        # Sincronizar MongoDB (generalmente no tiene secretos de CORE)
/app/backend/scripts/encrypt_core_server_secrets.py:396:        mongo_result = await sync_core_to_mongo(server_id, mongodb_id)
/app/backend/scripts/encrypt_core_server_secrets.py:398:        if mongo_result.get('encrypted_mongo'):
/app/backend/scripts/encrypt_core_server_secrets.py:399:            report['mongo_synced'] += 1
/app/backend/scripts/encrypt_core_server_secrets.py:400:            print(f"    ✓ MongoDB sincronizado")
/app/backend/scripts/encrypt_core_server_secrets.py:401:        elif mongo_result.get('message'):
/app/backend/scripts/encrypt_core_server_secrets.py:402:            print(f"    ✓ MongoDB: {mongo_result.get('message')}")
/app/backend/scripts/encrypt_core_server_secrets.py:409:            'mongo': mongo_result.get('message', 'OK'),
/app/backend/scripts/encrypt_core_server_secrets.py:436:    print(f"MongoDB sincronizado: {report['mongo_synced']}")
/app/backend/scripts/run_historical_load_compras.py:60:COLLECTION_CHECKPOINTS = "compras_historical_load_checkpoints"
/app/backend/scripts/run_historical_load_compras.py:111:    """Obtiene conexión a MongoDB."""
/app/backend/scripts/run_historical_load_compras.py:116:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/scripts/run_historical_load_compras.py:117:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/run_historical_load_compras.py:118:    client = AsyncIOMotorClient(mongo_url)
/app/backend/scripts/run_historical_load_compras.py:135:    checkpoint = await db[COLLECTION_CHECKPOINTS].find_one({
/app/backend/scripts/run_historical_load_compras.py:160:    await db[COLLECTION_CHECKPOINTS].insert_one(new_checkpoint)
/app/backend/scripts/run_historical_load_compras.py:168:    await db[COLLECTION_CHECKPOINTS].update_one(
/app/backend/scripts/run_historical_load_compras.py:698:    cursor = db.servers.find({"active": True}, {"_id": 0})
/app/backend/scripts/run_historical_load_24_months.py:62:COLLECTION_CHECKPOINTS = "historical_load_checkpoints"
/app/backend/scripts/run_historical_load_24_months.py:63:COLLECTION_KPIS = "kpis_comercial"  # Ahora solo como staging/cache, NO destino final
/app/backend/scripts/run_historical_load_24_months.py:67:DESTINATION_MONGO = "MONGODB"               # Solo checkpoint/log/staging
/app/backend/scripts/run_historical_load_24_months.py:86:    """Obtiene conexión a MongoDB."""
/app/backend/scripts/run_historical_load_24_months.py:91:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/scripts/run_historical_load_24_months.py:92:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/scripts/run_historical_load_24_months.py:93:    client = AsyncIOMotorClient(mongo_url)
/app/backend/scripts/run_historical_load_24_months.py:139:    await db[COLLECTION_CHECKPOINTS].insert_one(checkpoint)
/app/backend/scripts/run_historical_load_24_months.py:153:    await db[COLLECTION_CHECKPOINTS].update_one(
/app/backend/scripts/run_historical_load_24_months.py:165:    return await db[COLLECTION_CHECKPOINTS].find_one(
/app/backend/scripts/run_historical_load_24_months.py:177:    cursor = db[COLLECTION_CHECKPOINTS].find(
/app/backend/scripts/run_historical_load_24_months.py:194:    FASE 2.3: Necesario para carga histórica que lee directamente de MongoDB.
/app/backend/scripts/run_historical_load_24_months.py:218:    cursor = db.servers.find({}, {"_id": 0})
/app/backend/scripts/run_historical_load_24_months.py:332:    DESTINO FINAL - MongoDB queda solo como checkpoint/log.
/app/backend/scripts/run_historical_load_24_months.py:348:        "mongo_staging": 0  # Ya no se escribe a MongoDB como final
/app/backend/scripts/run_historical_load_24_months.py:400:async def upsert_kpi_batch_mongo_staging(
/app/backend/scripts/run_historical_load_24_months.py:410:    logger.warning("[DEPRECATED] upsert_kpi_batch_mongo_staging - MongoDB NO es destino final")
/app/backend/scripts/run_historical_load_24_months.py:412:    return {"mongo_staging": len(kpis_list), "warning": "DEPRECATED_MONGO_STAGING"}
/app/backend/scripts/run_historical_load_24_months.py:427:    MongoDB solo para checkpoint/log.
/app/backend/scripts/run_historical_load_24_months.py:442:        # DEPRECATED: MongoDB staging
/app/backend/scripts/run_historical_load_24_months.py:444:        return await upsert_kpi_batch_mongo_staging(db, server, kpis_list, run_id)
/app/backend/scripts/run_historical_load_24_months.py:567:        "mongo_role": "checkpoint_log_only",
/app/backend/scripts/run_historical_load_24_months.py:579:        "mongo_final_inserted": 0,  # Siempre 0 - REGLA MAESTRA
/app/backend/scripts/run_historical_load_24_months.py:603:                "mongo_role": "checkpoint_log_only",
/app/backend/scripts/run_historical_load_24_months.py:605:                "planned_mongo_final_write": False
/app/backend/scripts/run_historical_load_24_months.py:609:        logger.info(f"[DRY_RUN] Plan generado. Destino: {DESTINATION_SQL}. MongoDB: checkpoint/log only")
/app/backend/scripts/run_historical_load_24_months.py:640:            "mongo_final_inserted": 0,  # Siempre 0 - MongoDB no es destino final
/app/backend/scripts/run_historical_load_24_months.py:742:        f"mongo_final=0"
/app/backend/scripts/solucion_ventas_acumuladas_cero.py:11:           contiene la lógica abstracta del motor de agregación usado en React.
/app/backend/scripts/solucion_ventas_acumuladas_cero.py:46:[3] MOTOR DE AGREGACIÓN EN CALIENTE (accumulatedUnits):
/app/backend/scripts/solucion_ventas_acumuladas_cero.py:58:# --- LÓGICA ABSTRAÍDA EN PYTHON (MOTOR DE AGREGACIÓN) ---
/app/backend/tests/test_notificaciones_whatsapp.py:574:    - Old email notification system: /api/v2/notificaciones/log (notificaciones_log collection)
/app/backend/tests/test_notificaciones_whatsapp.py:575:    - New WhatsApp notification system: /api/v2/notificaciones/log (notification_log collection)
/app/backend/tests/test_automatizacion_compras_fase4.py:15:COLECCIONES MONGODB:
/app/backend/tests/test_tablero_ejecutivo.py:7:NO conecta a servicios reales (Mongo, SQL, APIs).
/app/backend/tests/test_config.py:33:    # MongoDB
/app/backend/tests/test_config.py:34:    TEST_MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/tests/test_auth_mocks.py:42:            mock_db.users.find_one = AsyncMock(return_value=mock_user_db)
/app/backend/tests/test_auth_mocks.py:45:            assert mock_db.users.find_one is not None
/app/backend/tests/test_simulacion_controlada.py:136:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/tests/test_simulacion_controlada.py:152:async def get_servers_from_mongo():
/app/backend/tests/test_simulacion_controlada.py:153:    """Obtiene servidores activos de MongoDB."""
/app/backend/tests/test_simulacion_controlada.py:154:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/tests/test_simulacion_controlada.py:155:    mongo_url = mongo_url.strip('"').strip("'")
/app/backend/tests/test_simulacion_controlada.py:157:    if not mongo_url:
/app/backend/tests/test_simulacion_controlada.py:158:        print("✗ MONGO_URL no configurada")
/app/backend/tests/test_simulacion_controlada.py:161:    client = AsyncIOMotorClient(mongo_url)
/app/backend/tests/test_simulacion_controlada.py:164:    cursor = db.servers.find(
/app/backend/tests/test_simulacion_controlada.py:219:    print("FASE 1: Obteniendo servidores de MongoDB...")
/app/backend/tests/test_simulacion_controlada.py:222:    servers = await get_servers_from_mongo()
/app/backend/tests/test_core_db.py:2:EDARSA HUB - Tests Ampliados para core/db.py
/app/backend/tests/test_migracion_servidores_sql.py:2:Test de Validación: Migración de Servidores MongoDB -> EDARSAHUB SQL
/app/backend/tests/test_migracion_servidores_sql.py:8:2. Que el fallback a MongoDB funcione si SQL falla
/app/backend/tests/test_migracion_servidores_sql.py:9:3. Paridad estructural entre SQL y MongoDB
/app/backend/tests/test_migracion_servidores_sql.py:32:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/tests/test_migracion_servidores_sql.py:33:from pymongo import MongoClient
/app/backend/tests/test_migracion_servidores_sql.py:79:def test_paridad_sql_mongodb():
/app/backend/tests/test_migracion_servidores_sql.py:80:    """Verifica paridad entre datos de SQL y MongoDB."""
/app/backend/tests/test_migracion_servidores_sql.py:81:    print("\n=== TEST: Paridad SQL vs MongoDB ===")
/app/backend/tests/test_migracion_servidores_sql.py:87:    # Obtener de MongoDB
/app/backend/tests/test_migracion_servidores_sql.py:88:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/tests/test_migracion_servidores_sql.py:89:    client = MongoClient(mongo_url)
/app/backend/tests/test_migracion_servidores_sql.py:92:    mongo_cursor = db.servers.find({
/app/backend/tests/test_migracion_servidores_sql.py:100:    mongo_servers = list(mongo_cursor)
/app/backend/tests/test_migracion_servidores_sql.py:101:    mongo_servers = [s for s in mongo_servers if s.get('tipo_conexion') != 'CORE']
/app/backend/tests/test_migracion_servidores_sql.py:102:    mongo_names = {s['name'] for s in mongo_servers}
/app/backend/tests/test_migracion_servidores_sql.py:105:    print(f"  MongoDB: {len(mongo_servers)} servidores")
/app/backend/tests/test_migracion_servidores_sql.py:108:    solo_sql = sql_names - mongo_names
/app/backend/tests/test_migracion_servidores_sql.py:109:    solo_mongo = mongo_names - sql_names
/app/backend/tests/test_migracion_servidores_sql.py:113:    if solo_mongo:
/app/backend/tests/test_migracion_servidores_sql.py:114:        print(f"  ⚠ Solo en MongoDB: {solo_mongo}")
/app/backend/tests/test_migracion_servidores_sql.py:116:    if sql_names == mongo_names:
/app/backend/tests/test_migracion_servidores_sql.py:129:    # Inicializar MongoDB
/app/backend/tests/test_migracion_servidores_sql.py:130:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/tests/test_migracion_servidores_sql.py:131:    client = AsyncIOMotorClient(mongo_url)
/app/backend/tests/test_migracion_servidores_sql.py:179:        results.append(("Paridad SQL/MongoDB", test_paridad_sql_mongodb()))
/app/backend/tests/test_migracion_servidores_sql.py:182:        results.append(("Paridad SQL/MongoDB", False))
/app/backend/tests/test_dashboard_comercial.py:45:                mock_db.servers.find_one = AsyncMock(return_value=None)
/app/backend/tests/test_dashboard_comercial.py:98:                mock_db.servers.find_one = AsyncMock(return_value=sample_server_config)
/app/backend/tests/test_dashboard_comercial.py:101:                with patch("core.db.execute_sql_query") as mock_sql:
/app/backend/tests/test_e2e_flujo_completo.py:6:⚠️ DEPRECATED (Mayo 2026): Este script usa MongoDB que ha sido reemplazado por SQL Server.
/app/backend/tests/test_e2e_flujo_completo.py:7:Las referencias a self.db.* y conexiones directas a MongoDB ya no funcionan en producción.
/app/backend/tests/test_e2e_flujo_completo.py:30:# Importar PyMongo
/app/backend/tests/test_e2e_flujo_completo.py:31:from pymongo import MongoClient
/app/backend/tests/test_e2e_flujo_completo.py:79:        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/tests/test_e2e_flujo_completo.py:95:        """Conecta a MongoDB."""
/app/backend/tests/test_e2e_flujo_completo.py:96:        print_info(f"Conectando a MongoDB: {self.mongo_url[:30]}...")
/app/backend/tests/test_e2e_flujo_completo.py:97:        self.client = MongoClient(self.mongo_url)
/app/backend/tests/test_e2e_flujo_completo.py:102:        """Desconecta de MongoDB."""
/app/backend/tests/test_e2e_flujo_completo.py:126:        self.db.users.insert_one({
/app/backend/tests/test_e2e_flujo_completo.py:143:        collections = [
/app/backend/tests/test_e2e_flujo_completo.py:155:        for col_name, query in collections:
/app/backend/tests/test_e2e_flujo_completo.py:198:        self.db.auditorias_programadas.insert_one(auditoria_doc)
/app/backend/tests/test_e2e_flujo_completo.py:221:                    workflow = self.db.workflow_inventarios.find_one({"id": workflow_id})
/app/backend/tests/test_e2e_flujo_completo.py:229:                        count = self.db.workflow_inventarios.count_documents({})
/app/backend/tests/test_e2e_flujo_completo.py:232:                        last = self.db.workflow_inventarios.find_one(
/app/backend/tests/test_e2e_flujo_completo.py:291:            self.db.workflow_inventarios.insert_one(workflow_doc)
/app/backend/tests/test_e2e_flujo_completo.py:321:            self.db.detalle_diferencias.insert_one(diferencia_doc)
/app/backend/tests/test_e2e_flujo_completo.py:326:        self.db.workflow_inventarios.update_one(
/app/backend/tests/test_e2e_flujo_completo.py:387:            resp_doc = self.db.responsabilidad_economica.find_one({"id": resultado.id})
/app/backend/tests/test_e2e_flujo_completo.py:531:        cargo_doc = self.db.cargos_economicos.find_one({"id": cargo_id})
/app/backend/tests/test_e2e_flujo_completo.py:611:            notif = self.db.notificaciones_log.find_one({
/app/backend/tests/test_e2e_flujo_completo.py:645:        auditoria_log = self.db.auditorias_programadas_log.find_one({
/app/backend/tests/test_e2e_flujo_completo.py:656:            historial = list(self.db.responsabilidad_historial.find({
/app/backend/tests/test_e2e_flujo_completo.py:671:            cargo_log = list(self.db.cargos_economicos_log.find({
/app/backend/tests/test_e2e_flujo_completo.py:686:            notif_log = list(self.db.notificaciones_log.find({
/app/backend/tests/test_comercial_adapters.py:300:    def test_busca_en_mongodb_primero(self):
/app/backend/tests/test_comercial_adapters.py:301:        """Test: Intenta buscar en MongoDB antes de hardcoded"""
/app/backend/tests/test_comercial_adapters.py:309:        # Mock MongoDB sin APIs - pymongo.MongoClient
/app/backend/tests/test_comercial_adapters.py:310:        with patch("pymongo.MongoClient") as mock_mongo:
/app/backend/tests/test_comercial_adapters.py:314:            mock_db.servers.find.return_value = []  # Sin APIs en MongoDB
/app/backend/tests/test_comercial_adapters.py:315:            mock_mongo.return_value = mock_client
/app/backend/tests/test_comercial_adapters.py:338:        # Mock MongoDB con API que matchea
/app/backend/tests/test_comercial_adapters.py:352:        with patch("pymongo.MongoClient") as mock_mongo:
/app/backend/tests/test_comercial_adapters.py:356:            mock_db.servers.find.return_value = [mock_api_doc]
/app/backend/tests/test_comercial_adapters.py:357:            mock_mongo.return_value = mock_client
/app/backend/tests/test_comercial_adapters.py:375:        """Test: Fallback a configuración hardcodeada si no hay MongoDB"""
/app/backend/tests/test_comercial_adapters.py:382:        # Simular error de MongoDB
/app/backend/tests/test_comercial_adapters.py:383:        with patch("pymongo.MongoClient", side_effect=Exception("DB Error")):
/app/backend/tests/test_comercial_adapters.py:427:        with patch("pymongo.MongoClient") as mock_mongo:
/app/backend/tests/test_comercial_adapters.py:431:            mock_db.servers.find.return_value = [mock_api_doc]
/app/backend/tests/test_comercial_adapters.py:432:            mock_mongo.return_value = mock_client
/app/backend/tests/conftest.py:11:- Base para mocks de MongoDB, SQL, Auth y APIs externas
/app/backend/tests/conftest.py:36:os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
/app/backend/tests/conftest.py:182:# FIXTURES: MOCKS BASE PARA MONGODB
/app/backend/tests/conftest.py:186:def mock_mongo_db():
/app/backend/tests/conftest.py:188:    Mock básico de la base de datos MongoDB.
/app/backend/tests/conftest.py:191:        def test_con_mongo(mock_mongo_db):
/app/backend/tests/conftest.py:192:            mock_mongo_db.users.find_one.return_value = {"email": "test@test.com"}
/app/backend/tests/conftest.py:197:    mock_db.users = MagicMock()
/app/backend/tests/conftest.py:198:    mock_db.servers = MagicMock()
/app/backend/tests/conftest.py:199:    mock_db.roles = MagicMock()
/app/backend/tests/conftest.py:200:    mock_db.kpis_cache = MagicMock()
/app/backend/tests/conftest.py:201:    mock_db.server_status = MagicMock()
/app/backend/tests/conftest.py:207:def mock_mongo_collection():
/app/backend/tests/conftest.py:208:    """Mock de una colección MongoDB individual"""
/app/backend/tests/conftest.py:209:    collection = MagicMock()
/app/backend/tests/conftest.py:210:    collection.find_one = AsyncMock(return_value=None)
/app/backend/tests/conftest.py:211:    collection.find = MagicMock(return_value=MagicMock())
/app/backend/tests/conftest.py:212:    collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test_id"))
/app/backend/tests/conftest.py:213:    collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
/app/backend/tests/conftest.py:214:    collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
/app/backend/tests/conftest.py:215:    return collection
/app/backend/tests/conftest.py:230:            with patch("core.db.execute_sql_query", mock_sql_query):
/app/backend/tests/test_repositories.py:7:NO conecta a servicios reales (Mongo, SQL).
/app/backend/tests/test_repositories.py:14:class TestRepositoryMongo:
/app/backend/tests/test_repositories.py:15:    """Tests de acceso a MongoDB con mocks"""
/app/backend/tests/test_repositories.py:18:    def test_mock_mongo_db_structure(self, mock_mongo_db):
/app/backend/tests/test_repositories.py:19:        """Test: Mock de MongoDB tiene estructura correcta"""
/app/backend/tests/test_repositories.py:21:        assert hasattr(mock_mongo_db, 'users')
/app/backend/tests/test_repositories.py:22:        assert hasattr(mock_mongo_db, 'servers')
/app/backend/tests/test_repositories.py:23:        assert hasattr(mock_mongo_db, 'roles')
/app/backend/tests/test_repositories.py:24:        assert hasattr(mock_mongo_db, 'kpis_cache')
/app/backend/tests/test_repositories.py:27:    def test_mock_find_one_returns_none(self, mock_mongo_collection):
/app/backend/tests/test_repositories.py:32:            mock_mongo_collection.find_one()
/app/backend/tests/test_repositories.py:37:    def test_mock_find_one_configured(self, mock_mongo_collection):
/app/backend/tests/test_repositories.py:40:        mock_mongo_collection.find_one = AsyncMock(return_value=expected)
/app/backend/tests/test_repositories.py:44:            mock_mongo_collection.find_one()
/app/backend/tests/test_repositories.py:49:    def test_mock_insert_one_returns_id(self, mock_mongo_collection):
/app/backend/tests/test_repositories.py:53:            mock_mongo_collection.insert_one({"test": "data"})
/app/backend/tests/test_repositories.py:87:        with patch("core.db.execute_sql_query") as mock:
/app/backend/tests/test_repositories.py:150:    def test_mock_mongo_raises_exception(self, mock_mongo_collection):
/app/backend/tests/test_repositories.py:151:        """Test: Mock de Mongo puede simular excepción"""
/app/backend/tests/test_repositories.py:152:        mock_mongo_collection.find_one = AsyncMock(
/app/backend/tests/test_repositories.py:159:                mock_mongo_collection.find_one()
/app/backend/tests/test_bloque4_paridad.py:43:db_module = load_module_isolated('core.db', '/app/backend/core/db.py')
/app/backend/tests/test_bloque2_paridad.py:23:from pymongo import MongoClient
/app/backend/tests/test_bloque2_paridad.py:36:def get_mongo_db():
/app/backend/tests/test_bloque2_paridad.py:37:    """Obtiene conexión a MongoDB."""
/app/backend/tests/test_bloque2_paridad.py:38:    client = MongoClient(os.environ.get('MONGO_URL'))
/app/backend/tests/test_bloque2_paridad.py:42:    """Obtiene un servidor SoftRestaurant de prueba desde MongoDB."""
/app/backend/tests/test_bloque2_paridad.py:43:    db = get_mongo_db()
/app/backend/tests/test_bloque2_paridad.py:44:    server = db.servers.find_one({
/app/backend/tests/test_bloque3_paridad_mpro.py:28:from pymongo import MongoClient
/app/backend/tests/test_bloque3_paridad_mpro.py:41:def get_mongo_db():
/app/backend/tests/test_bloque3_paridad_mpro.py:42:    """Obtiene conexión a MongoDB."""
/app/backend/tests/test_bloque3_paridad_mpro.py:43:    client = MongoClient(os.environ.get('MONGO_URL'))
/app/backend/tests/test_bloque3_paridad_mpro.py:47:    """Obtiene un servidor MPRO de prueba desde MongoDB."""
/app/backend/tests/test_bloque3_paridad_mpro.py:48:    db = get_mongo_db()
/app/backend/tests/test_bloque3_paridad_mpro.py:49:    server = db.servers.find_one({
/app/backend/tests/test_comparativo_inventarios.py:3:Tests the cache storage in MongoDB and Excel export endpoint.
/app/backend/tests/test_comparativo_inventarios.py:6:1. /api/reports/inventory-analysis - saves correctly to MongoDB cache (inventario_diferencias_detalle)
/app/backend/tests/test_comparativo_inventarios.py:120:        """Test that MongoDB cache has 4 documents for the test folios"""
/app/backend/tests/test_recipients_manager.py:2:Test Suite: Centro de Control - Recipients Manager (MongoDB)
/app/backend/tests/test_recipients_manager.py:4:Tests for CRUD operations on alert recipients stored in MongoDB.
/app/backend/tests/test_recipients_manager.py:12:- Verify email_notifications.py reads from MongoDB
/app/backend/tests/test_recipients_manager.py:13:- Verify whatsapp_notifications.py reads from MongoDB
/app/backend/tests/test_recipients_manager.py:24:    """CRUD operations for alert recipients in MongoDB"""
/app/backend/tests/test_recipients_manager.py:348:class TestNotificationServicesReadFromMongoDB:
/app/backend/tests/test_recipients_manager.py:349:    """Verify email and whatsapp services read recipients from MongoDB"""
/app/backend/tests/test_recipients_manager.py:361:    def test_email_config_shows_mongodb_recipients(self):
/app/backend/tests/test_recipients_manager.py:362:        """GET /email/config should show recipients from MongoDB"""
/app/backend/tests/test_recipients_manager.py:374:        print(f"✓ Email config shows {data['config']['recipients_count']} recipients from MongoDB")
/app/backend/tests/test_recipients_manager.py:376:    def test_whatsapp_config_shows_mongodb_recipients(self):
/app/backend/tests/test_recipients_manager.py:377:        """GET /whatsapp/config should show recipients from MongoDB"""
/app/backend/tests/test_recipients_manager.py:389:        print(f"✓ WhatsApp config shows {data['config']['recipients_count']} recipients from MongoDB")
/app/backend/tests/test_recipients_manager.py:404:        # Email should be configured with MongoDB recipients
/app/backend/tests/test_recipients_manager.py:409:        # WhatsApp should be configured with MongoDB recipients
/app/backend/tests/test_recipients_manager.py:414:        print("✓ All notification services configured with MongoDB recipients")
/app/backend/tests/test_recipients_manager.py:418:    """Verify seeded recipients exist in MongoDB"""
/app/backend/tests/test_macrofase2_kpis.py:33:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/tests/test_macrofase2_kpis.py:35:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/tests/test_macrofase2_kpis.py:38:    client = AsyncIOMotorClient(mongo_url)
/app/backend/tests/test_macrofase2_kpis.py:48:        COLLECTION_NAME,
/app/backend/tests/test_macrofase2_kpis.py:89:    await db[COLLECTION_NAME].delete_many({
/app/backend/tests/test_macrofase2_kpis.py:404:        count = await db[COLLECTION_NAME].count_documents({
/app/backend/tests/test_macrofase2_kpis.py:465:    await db[COLLECTION_NAME].delete_many({
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:1697:    [TipoMotorPrecio] VARCHAR(50) NULL DEFAULT ('VINOS_RANGOS'),
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4288:    [FuenteOriginal] NVARCHAR(20) NOT NULL DEFAULT ('MONGODB'),
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:6997:    [mongodb_id] NVARCHAR(100) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7011:    [mongodb_id] NVARCHAR(100) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7052:    [mongodb_id] NVARCHAR(100) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7203:-- TABLA: [dbo].[Sistema_EmpresasMongoMap]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7205:CREATE TABLE [dbo].[Sistema_EmpresasMongoMap] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7207:    [EmpresaMongoUUID] VARCHAR(50) NOT NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7208:    [EmpresaMongoLegacyID] VARCHAR(50) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7218:    CONSTRAINT [PK_Sistema_EmpresasMongoMap] PRIMARY KEY ([MapID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7347:    [MongoConfigID] VARCHAR(36) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7368:    [MongoUUID] VARCHAR(36) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7369:    [MongoEmpresaUUID] VARCHAR(36) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7403:    [MongoSucursalUUID] VARCHAR(36) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7404:    [MongoServidorUUID] VARCHAR(36) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8587:    [LegacyMongoValue] VARCHAR(100) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8682:    [MongoLegacyID] VARCHAR(50) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8804:-- TABLA: [dbo].[Usuario_MigracionMongoTrace]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8806:CREATE TABLE [dbo].[Usuario_MigracionMongoTrace] (
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8808:    [MongoID] VARCHAR(24) NOT NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8811:    [RolMongoDB] VARCHAR(50) NOT NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8812:    [ActivoMongoDB] BIT NOT NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8816:    CONSTRAINT [PK_Usuario_MigracionMongoTrace] PRIMARY KEY ([TraceID])
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8940:    [LegacyMongoValue] VARCHAR(100) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8983:    [LegacyMongoValue] VARCHAR(100) NULL,
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:10738:ALTER TABLE [dbo].[Sistema_EmpresasMongoMap] ADD CONSTRAINT [FK_EmpresaID_SQL]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:12578:CREATE UNIQUE NONCLUSTERED INDEX [UQ_EmpresaMongoUUID]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:12579:    ON [dbo].[Sistema_EmpresasMongoMap] (EmpresaMongoUUID);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:12800:CREATE UNIQUE NONCLUSTERED INDEX [IX_Usuario_MongoLegacyID]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:12801:    ON [dbo].[Usuario_Catalogo] (MongoLegacyID);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:12854:CREATE UNIQUE NONCLUSTERED INDEX [UQ_MigracionMongoTrace_Email]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:12855:    ON [dbo].[Usuario_MigracionMongoTrace] (Email);
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:12857:CREATE UNIQUE NONCLUSTERED INDEX [UQ_MigracionMongoTrace_MongoID]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:12858:    ON [dbo].[Usuario_MigracionMongoTrace] (MongoID);
/app/backend/server.py:74:# MongoDB import movido a bloque condicional más abajo
/app/backend/server.py:107:# MÁXIMA EDARSAHUB: SQL Server es el cerebro. MongoDB ELIMINADO.
/app/backend/server.py:111:# Los accesos a colecciones MongoDB retornan valores vacíos sin fallar.
/app/backend/server.py:115:# MongoDB ELIMINADO - Usar StubDatabase para evitar errores en código legacy
/app/backend/server.py:116:from core.mongo_stub import get_stub_database
/app/backend/server.py:118:logger.info("[DB] Sistema funcionando 100% SQL Server - MongoDB ELIMINADO (usando StubDatabase)")
/app/backend/server.py:288:init_security(None)  # MongoDB eliminado
/app/backend/server.py:366:    Descifra los secretos de un servidor obtenido de MongoDB/SQL.
/app/backend/server.py:439:init_compras_module(None)  # MongoDB eliminado
/app/backend/server.py:466:init_comercial_module(None)  # MongoDB eliminado
/app/backend/server.py:481:# FASE 1C-3I-B: Motor de Precios Sugeridos y Benchmark Competitivo
/app/backend/server.py:544:# - Fuente única: EDARSAHUB (no MongoDB)
/app/backend/server.py:555:# - ARQUITECTURA: SQL Server (persistencia) + MongoDB (cache)
/app/backend/server.py:578:init_manuales_module(None)  # MongoDB eliminado
/app/backend/server.py:581:init_rh_module(None)  # MongoDB eliminado
/app/backend/server.py:584:init_catalogos_module(None)  # MongoDB eliminado
/app/backend/server.py:585:init_catalogos_service(None)  # MongoDB eliminado
/app/backend/server.py:588:_finanzas_repo = FinanzasRepositoryReal(None)  # MongoDB eliminado
/app/backend/server.py:593:_mpro_repo = FinanzasRepositoryMPRO(None)  # MongoDB eliminado
/app/backend/server.py:597:_softrest_repo = FinanzasRepositorySoftRestaurant(None)  # MongoDB eliminado
/app/backend/server.py:623:# FUENTE: EDARSAHUB (no MongoDB)
/app/backend/server.py:635:# NO usa MongoDB
/app/backend/server.py:642:# ARQUITECTURA: SQL Server EDARSA HUB (persistencia) + MongoDB (cache)
/app/backend/server.py:660:init_sync_receiver(None)  # MongoDB eliminado
/app/backend/server.py:661:init_kpis_repository(None)  # MongoDB eliminado
/app/backend/server.py:670:init_api_connections_repository(None)  # MongoDB eliminado
/app/backend/server.py:704:# Cache service (100% SQL - MongoDB eliminado)
/app/backend/server.py:995:    # FASE P1.4-B (Dic 2025): Corregido para aceptar objetos JSON (EDARSAHUB) o strings (legacy MongoDB)
/app/backend/server.py:1015:    config_origin: Optional[str] = None  # "EDARSAHUB_SQL" | "MONGODB_LEGACY"
/app/backend/server.py:1234:# Las funciones de SQL Server han sido migradas a /core/db.py
/app/backend/server.py:1551:    FASE 3B.1: Crea servidor en EDARSAHUB SQL primero, sincroniza a MongoDB.
/app/backend/server.py:1554:    - MongoDB queda como espejo legacy
/app/backend/server.py:1555:    - Si MongoDB sync falla, devuelve PARTIAL_SYNC
/app/backend/server.py:1584:        sync_mongo=True
/app/backend/server.py:1612:    2. MongoDB (fallback legacy)
/app/backend/server.py:1623:        allow_mongo_fallback=True,
/app/backend/server.py:1639:    2. MongoDB (fallback legacy)
/app/backend/server.py:1650:        allow_mongo_fallback=True,
/app/backend/server.py:1662:    FASE 3B.1: Actualiza servidor en EDARSAHUB SQL primero, sincroniza a MongoDB.
/app/backend/server.py:1665:    - MongoDB queda como espejo legacy
/app/backend/server.py:1666:    - Si MongoDB sync falla, devuelve PARTIAL_SYNC
/app/backend/server.py:1700:        sync_mongo=True
/app/backend/server.py:1720:    FASE 3B.1: Desactiva servidor en EDARSAHUB SQL primero, sincroniza a MongoDB.
/app/backend/server.py:1724:    - MongoDB queda como espejo legacy
/app/backend/server.py:1725:    - Si MongoDB sync falla, devuelve PARTIAL_SYNC
/app/backend/server.py:1753:        sync_mongo=True,
/app/backend/server.py:1779:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:1786:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}))
/app/backend/server.py:1814:            await db.server_status.update_one(
/app/backend/server.py:1841:        await db.server_status.update_one(
/app/backend/server.py:1873:    await db.queries.insert_one(doc)
/app/backend/server.py:1883:    queries = await db.queries.find(filter_query, {"_id": 0}).to_list(1000)
/app/backend/server.py:1891:    await db.queries.update_one({"id": query_id}, {"$set": query_data})
/app/backend/server.py:1899:    await db.queries.delete_one({"id": query_id})
/app/backend/server.py:1998:    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/server.py:2000:    NO FUENTE: MongoDB db.servers
/app/backend/server.py:2023:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:2105:    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/server.py:2107:    NO FUENTE: MongoDB db.servers
/app/backend/server.py:2121:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:2136:    # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {field_name: query_config}})
/app/backend/server.py:2142:        sync_mongo=True  # Mantener espejo MongoDB para compatibilidad
/app/backend/server.py:2149:    # ANTES: updated_server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}, {"_id": 0}))
/app/backend/server.py:2158:        # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {"queries_configured": all_configured}})
/app/backend/server.py:2164:            sync_mongo=True
/app/backend/server.py:2182:    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/server.py:2184:    NO FUENTE: MongoDB db.servers
/app/backend/server.py:2189:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:2241:    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/server.py:2243:    NO FUENTE: MongoDB db.servers
/app/backend/server.py:2251:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:2258:    # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {field_name: None, "queries_configured": False}})
/app/backend/server.py:2264:        sync_mongo=True
/app/backend/server.py:2288:    - No usar MongoDB
/app/backend/server.py:2411:    NO consulta MongoDB.
/app/backend/server.py:2448:    NO consulta MongoDB.
/app/backend/server.py:2507:    configs = await db.server_sucursales_config.find(
/app/backend/server.py:2556:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:2564:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:2661:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:2673:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:2771:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:2776:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:2787:    configs = await db.server_sucursales_config.find(
/app/backend/server.py:2808:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:2816:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:2846:    existing_configs = await db.server_sucursales_config.find(
/app/backend/server.py:2863:            await db.server_sucursales_config.update_one(
/app/backend/server.py:2889:            await db.server_sucursales_config.insert_one(new_config)
/app/backend/server.py:2893:    configs = await db.server_sucursales_config.find(
/app/backend/server.py:2918:    existing = await db.server_sucursales_config.find_one({
/app/backend/server.py:2936:    await db.server_sucursales_config.update_one(
/app/backend/server.py:2970:        result = await db.server_sucursales_config.update_one(
/app/backend/server.py:2992:    Migrado de db.servers.find() a server_registry.list_servers()
/app/backend/server.py:3001:    cursor = db.server_sucursales_config.find(filtro, {"_id": 0})
/app/backend/server.py:3005:    # ANTES: server_cursor = db.servers.find({"id": {"$in": server_ids}}, {"_id": 0, "id": 1, "name": 1})
/app/backend/server.py:3037:    MongoDB NO se usa como fuente, ni como fallback, ni como respaldo.
/app/backend/server.py:3182:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:3194:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:3256:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:3268:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:3373:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:3385:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:3604:    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/server.py:3606:    NO FUENTE: MongoDB db.servers
/app/backend/server.py:3615:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:3621:    query_template = await db.queries.find_one({
/app/backend/server.py:3655:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:3660:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:3789:    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/server.py:3791:    NO FUENTE: MongoDB db.servers
/app/backend/server.py:3861:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:4438:                        await db.inventario_diferencias_detalle.update_one(
/app/backend/server.py:4459:                orquestador = get_orquestador_service(db)  # MongoDB ELIMINADO - StubDatabase
/app/backend/server.py:5086:                        await db.inventario_diferencias_detalle.update_one(
/app/backend/server.py:5103:                orquestador = get_orquestador_service(db)  # MongoDB ELIMINADO - StubDatabase
/app/backend/server.py:5153:    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/server.py:5155:    NO FUENTE: MongoDB db.servers
/app/backend/server.py:5167:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:5409:    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/server.py:5411:    NO FUENTE: MongoDB db.servers
/app/backend/server.py:5422:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:5719:            cached = await db.inventario_diferencias_detalle.find_one(cache_key, {"_id": 0})
/app/backend/server.py:5976:    Usa cache en MongoDB para evitar recalcular.
/app/backend/server.py:5980:    FASE P1.4-E3 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/server.py:5982:    NO FUENTE: MongoDB db.servers
/app/backend/server.py:5994:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
/app/backend/server.py:6176:    await db.alerts.insert_one(doc)
/app/backend/server.py:6182:    alerts = await db.alerts.find({"active": True}, {"_id": 0}).to_list(1000)
/app/backend/server.py:6187:    await db.alerts.update_one({"id": alert_id}, {"$set": alert_data})
/app/backend/server.py:6192:    await db.alerts.update_one({"id": alert_id}, {"$set": {"active": False}})
/app/backend/server.py:6254:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:6263:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:6320:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:6340:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:6477:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:6487:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/backend/server.py:6793:    FASE P1.4-E2 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/server.py:6795:    NO FUENTE: MongoDB db.servers
/app/backend/server.py:6803:        # ANTES: server = decrypt_server_secrets(await db.servers.find_one(query))
/app/backend/server.py:6997:    Migrado de db.servers.find() a server_registry.list_servers()
/app/backend/server.py:7000:    # ANTES: servers = await db.servers.find({"active": True, "queries_configured": True}, {...}).to_list(100)
/app/backend/server.py:7025:    NOTA: db.users y db.alerts aún usan MongoDB (fuera del alcance de P1.4-E4).
/app/backend/server.py:7030:    # ANTES: total_servers = await db.servers.count_documents({"active": True})
/app/backend/server.py:7031:    # ANTES: servers_configured = await db.servers.count_documents({"active": True, "queries_configured": True})
/app/backend/server.py:7036:    # NOTA: db.users y db.alerts aún usan MongoDB (migración en Fase 2)
/app/backend/server.py:7037:    total_users = await db.users.count_documents({"active": True})
/app/backend/server.py:7038:    total_alerts = await db.alerts.count_documents({"active": True})
/app/backend/server.py:7117:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:7120:    FASE 2-G FIX: Usar get_current_user que busca en SQL en lugar de db.users (MongoDB)
/app/backend/server.py:7131:    # FASE 2-G FIX: Usar get_current_user (SQL-only) en lugar de db.users (MongoDB)
/app/backend/server.py:7134:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:8144:    # FASE T3.3: Migrado de db.servers a server_registry (EDARSAHUB)
/app/backend/server.py:8342:    FASE P1.4-E1 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/server.py:8344:    NO FUENTE: MongoDB db.servers
/app/backend/server.py:8353:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
/app/backend/server.py:9304:    # FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
/app/backend/server.py:9483:    # FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
/app/backend/server.py:9912:    # FASE T3.3: Migrado de db.servers a server_registry (EDARSAHUB)
/app/backend/server.py:10064:    # FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
/app/backend/server.py:10131:    # FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
/app/backend/server.py:10239:    status = await db.server_status.find_one({"server_id": server_id})
/app/backend/server.py:10244:    await db.server_status.update_one(
/app/backend/server.py:10283:    cache = await db.kpis_cache.find_one({
/app/backend/server.py:10291:    await db.kpis_cache.update_one(
/app/backend/server.py:10354:    - No usa MongoDB
/app/backend/server.py:10911:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:10915:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:11082:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:11092:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:11136:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:11152:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:11296:    # Guardar log en MongoDB
/app/backend/server.py:11297:    await db.script_logs.insert_one({
/app/backend/server.py:11392:    """Crea un nuevo informe de auditoría y lo guarda en MongoDB"""
/app/backend/server.py:11446:        # Guardar en MongoDB
/app/backend/server.py:11447:        result = await db.informes_auditoria.insert_one(informe_doc)
/app/backend/server.py:11453:            "mongo_id": str(result.inserted_id)
/app/backend/server.py:11488:        total = await db.informes_auditoria.count_documents(filtro)
/app/backend/server.py:11492:        cursor = db.informes_auditoria.find(
/app/backend/server.py:11494:            {"_id": 0}  # Excluir _id de MongoDB
/app/backend/server.py:11538:        informe = await db.informes_auditoria.find_one(
/app/backend/server.py:11577:        result = await db.informes_auditoria.update_one(
/app/backend/server.py:11602:        informe = await db.informes_auditoria.find_one({"id": informe_id})
/app/backend/server.py:11616:        # Eliminar de MongoDB
/app/backend/server.py:11617:        await db.informes_auditoria.delete_one({"id": informe_id})
/app/backend/server.py:11638:        informe = await db.informes_auditoria.find_one({"id": informe_id})
/app/backend/server.py:11680:        await db.informes_auditoria.update_one(
/app/backend/server.py:11714:        informe = await db.informes_auditoria.find_one({"id": informe_id})
/app/backend/server.py:11733:        # Eliminar de MongoDB
/app/backend/server.py:11734:        await db.informes_auditoria.update_one(
/app/backend/server.py:11758:        result = await db.informes_auditoria.update_one(
/app/backend/server.py:11797:        informe = await db.informes_auditoria.find_one({"id": informe_id}, {"_id": 0})
/app/backend/server.py:12128:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:12133:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True}))
/app/backend/server.py:12977:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:12980:    NOTA: La escritura del script pendiente permanece en MongoDB como documento
/app/backend/server.py:12987:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:13006:    # Guardar en MongoDB como documento operativo temporal
/app/backend/server.py:13008:    result = await db.scripts_pendientes.insert_one({
/app/backend/server.py:13031:    scripts = await db.scripts_pendientes.find(
/app/backend/server.py:13053:    result = await db.scripts_pendientes.delete_one({"_id": ObjectId(script_id)})
/app/backend/server.py:13085:    result = await db.scripts_pendientes.update_one(
/app/backend/server.py:13112:    FASE P1.4-E4 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
/app/backend/server.py:13114:    NO FUENTE: MongoDB db.servers
/app/backend/server.py:13122:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:13136:    # Si hay script_id, cargar el script de MongoDB
/app/backend/server.py:13139:        script_doc = await db.scripts_pendientes.find_one({"_id": ObjectId(script_id)})
/app/backend/server.py:13263:    await db.script_logs.insert_one({
/app/backend/server.py:13280:        await db.scripts_pendientes.update_one(
/app/backend/server.py:13769:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:13774:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:13935:    Incluye consultas predefinidas y personalizadas (MongoDB).
/app/backend/server.py:13955:    # Agregar consultas personalizadas desde MongoDB
/app/backend/server.py:13962:    consultas_custom = await db.consultas_custom.find(filtro).to_list(500)
/app/backend/server.py:14014:        consulta_custom = await db.consultas_custom.find_one({"id": consulta_id})
/app/backend/server.py:14042:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:14127:# CRUD CONSULTAS PERSONALIZADAS (MongoDB)
/app/backend/server.py:14132:    """Lista todas las consultas personalizadas guardadas en MongoDB"""
/app/backend/server.py:14133:    consultas = await db.consultas_custom.find().to_list(1000)
/app/backend/server.py:14186:    await db.consultas_custom.insert_one(consulta)
/app/backend/server.py:14204:    consulta = await db.consultas_custom.find_one({"id": consulta_id})
/app/backend/server.py:14231:    await db.consultas_custom.update_one({"id": consulta_id}, {"$set": update_data})
/app/backend/server.py:14251:    consulta_custom = await db.consultas_custom.find_one({"id": consulta_id})
/app/backend/server.py:14254:        await db.consultas_custom.update_one(
/app/backend/server.py:14282:        await db.consultas_custom.insert_one(consulta_mod)
/app/backend/server.py:14295:    result = await db.consultas_custom.delete_one({"id": consulta_id})
/app/backend/server.py:14312:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:14315:    # Buscar consulta en MongoDB
/app/backend/server.py:14316:    consulta = await db.consultas_custom.find_one({"id": consulta_id})
/app/backend/server.py:14321:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/backend/server.py:14404:    await db.informes_auditoria.insert_one(informe_doc)
/app/backend/server.py:14444:    cursor = db.informes_auditoria.find(filtro, {"_id": 0, "datos_inventario": 0, "datos_comparativo": 0, "evidencias": 0}).sort("fecha_emision", -1)
/app/backend/server.py:14468:    informe = await db.informes_auditoria.find_one({"id": informe_id}, {"_id": 0})
/app/backend/server.py:14487:    informe = await db.informes_auditoria.find_one({"id": informe_id})
/app/backend/server.py:14501:    await db.informes_auditoria.update_one({"id": informe_id}, {"$set": update_data})
/app/backend/server.py:14504:    informe_updated = await db.informes_auditoria.find_one({"id": informe_id}, {"_id": 0})
/app/backend/server.py:14517:    result = await db.informes_auditoria.delete_one({"id": informe_id})
/app/backend/server.py:14536:    informe = await db.informes_auditoria.find_one({"id": informe_id})
/app/backend/server.py:14573:    await db.informes_auditoria.update_one(
/app/backend/server.py:14596:    result = await db.informes_auditoria.update_one(
/app/backend/server.py:14617:    informe = await db.informes_auditoria.find_one({"id": informe_id})
/app/backend/server.py:14644:    result = await db.informes_auditoria.update_one(
/app/backend/server.py:14668:    informe = await db.informes_auditoria.find_one({"id": informe_id}, {"_id": 0})
/app/backend/server.py:14867:    await db.solicitudes_catalogos.update_one(
/app/backend/server.py:14949:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:14972:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))
/app/backend/server.py:15016:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/backend/server.py:15030:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))
/app/backend/server.py:15090:    # Obtener configuración personalizada de niveles desde MongoDB
/app/backend/server.py:15091:    config = await db.config_catalogos.find_one({"tipo": "niveles_aprobacion"})
/app/backend/server.py:15115:    await db.config_catalogos.update_one(
/app/backend/server.py:15141:    permisos = await db.permisos_catalogos.find_one({"user_id": user_id})
/app/backend/server.py:15170:    usuario = await db.users.find_one({"id": user_id})
/app/backend/server.py:15175:    await db.permisos_catalogos.update_one(
/app/backend/server.py:15190:    await db.users.update_one(
/app/backend/server.py:15219:    permisos = await db.permisos_catalogos.find_one({"user_id": user_id})
/app/backend/server.py:15242:    permisos = await db.permisos_catalogos.find_one({"user_id": user_id})
/app/backend/server.py:15258:    config = await db.config_catalogos.find_one({"tipo": "niveles_aprobacion"})
/app/backend/server.py:15302:    await db.solicitudes_catalogos.insert_one(solicitud)
/app/backend/server.py:15319:    await db.tareas_sistema.insert_one(tarea)
/app/backend/server.py:15342:    solicitudes = await db.solicitudes_catalogos.find(filtro, {"_id": 0}).sort("fecha_solicitud", -1).to_list(100)
/app/backend/server.py:15350:    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id}, {"_id": 0})
/app/backend/server.py:15378:    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id})
/app/backend/server.py:15446:        await db.solicitudes_catalogos.update_one(
/app/backend/server.py:15484:        await db.tareas_sistema.insert_one(notificacion)
/app/backend/server.py:15492:        await db.solicitudes_catalogos.update_one(
/app/backend/server.py:15528:        await db.tareas_sistema.insert_one(tarea)
/app/backend/server.py:15533:    await db.tareas_sistema.update_many(
/app/backend/server.py:15549:    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id})
/app/backend/server.py:15560:    await db.solicitudes_catalogos.update_one(
/app/backend/server.py:15585:    await db.tareas_sistema.update_many(
/app/backend/server.py:15604:    await db.tareas_sistema.insert_one(notificacion)
/app/backend/server.py:15612:    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id})
/app/backend/server.py:15635:    await db.solicitudes_catalogos.update_one(
/app/backend/server.py:15677:    await db.tareas_sistema.insert_one(tarea)
/app/backend/server.py:15685:    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id}, {"_id": 0})
/app/backend/server.py:15728:    tareas = await db.tareas_sistema.find(
/app/backend/server.py:15739:    solicitudes_pendientes = await db.solicitudes_catalogos.count_documents({"estatus": "Pendiente"}) if user_role in ['Supervisor', 'Administrador'] else 0
/app/backend/server.py:15769:        solicitudes = await db.solicitudes_catalogos.find(
/app/backend/server.py:15798:        proveedores = await db.portal_proveedores.find(
/app/backend/server.py:15846:        ciclos = await db.nomina_ciclos.find(
/app/backend/server.py:15852:        config = await db.nomina_configuracion.find_one({}, {"_id": 0})
/app/backend/server.py:15932:    await db.tareas_sistema.update_one(
/app/backend/server.py:15951:        role_doc = await db.roles.find_one({"nombre": user_role}, {"_id": 0, "permisos": 1})
/app/backend/server.py:15959:    usuarios = await db.users.find(
/app/backend/server.py:15966:        permisos = await db.permisos_catalogos.find_one({"user_id": u["id"]})
/app/backend/server.py:15980:-- Base de datos: EDARSA HUB (Opcional - Las tareas se guardan en MongoDB)
/app/backend/server.py:15984:-- El sistema principal usa MongoDB para las tareas
/app/backend/server.py:16011:        "nota": "Este script es OPCIONAL. El sistema de tareas funciona con MongoDB. Use este script solo si desea mantener un log adicional en SQL Server."
/app/backend/server.py:16044:    await db.nomina_ciclos.update_one(
/app/backend/server.py:16085:    cursor = db.nomina_ciclos.find(filtro).sort("fecha_creacion", -1)
/app/backend/server.py:16088:    # Limpiar _id de MongoDB
/app/backend/server.py:16098:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
/app/backend/server.py:16131:    ciclo_existente = await db.nomina_ciclos.find_one({
/app/backend/server.py:16140:    config = await db.nomina_configuracion.find_one({"tipo": "general"})
/app/backend/server.py:16176:    await db.nomina_ciclos.insert_one(ciclo)
/app/backend/server.py:16191:    user = await db.users.find_one({"id": current_user.get("id")})
/app/backend/server.py:16196:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
/app/backend/server.py:16221:    config = await db.nomina_configuracion.find_one({"tipo": "general"})
/app/backend/server.py:16247:    await db.nomina_ciclos.update_one(
/app/backend/server.py:16282:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
/app/backend/server.py:16301:    await db.nomina_ciclos.update_one(
/app/backend/server.py:16329:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
/app/backend/server.py:16333:    cursor = db.nomina_movimientos.find({"ciclo_id": ciclo_id}).sort("fecha_registro", -1)
/app/backend/server.py:16346:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
/app/backend/server.py:16391:    await db.nomina_movimientos.insert_one(movimiento)
/app/backend/server.py:16394:    await db.nomina_ciclos.update_one(
/app/backend/server.py:16405:    movimiento = await db.nomina_movimientos.find_one({"id": movimiento_id})
/app/backend/server.py:16412:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
/app/backend/server.py:16416:    await db.nomina_movimientos.delete_one({"id": movimiento_id})
/app/backend/server.py:16419:    await db.nomina_ciclos.update_one(
/app/backend/server.py:16430:    config = await db.nomina_configuracion.find_one({"tipo": "general"})
/app/backend/server.py:16468:    await db.nomina_configuracion.update_one(
/app/backend/server.py:16480:    cursor = db.nomina_kpis_puestos.find({})
/app/backend/server.py:16522:    await db.nomina_kpis_puestos.update_one(
/app/backend/server.py:16538:-- NOTA: Las tablas principales se manejan en MongoDB.
/app/backend/server.py:16606:        CicloID NVARCHAR(50) NOT NULL, -- ID del ciclo en MongoDB
/app/backend/server.py:16626:        "nota": "Este script es OPCIONAL. El sistema de nóminas funciona principalmente con MongoDB. Use estas tablas para integración con NomiPAQ o reportes SQL."
/app/backend/server.py:16679:            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
/app/backend/server.py:16686:        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
/app/backend/server.py:16709:    service = get_estructura_service(db)  # MongoDB ELIMINADO - StubDatabase
/app/backend/server.py:16751:    service = get_estructura_service(db)  # MongoDB ELIMINADO - StubDatabase
/app/backend/server.py:16772:    service = get_estructura_service(db)  # MongoDB ELIMINADO - StubDatabase
/app/backend/server.py:16836:        await db.sec_bitacora_admin.insert_one({
/app/backend/server.py:16922:    permiso_catalogo = await db.sec_permisos_catalogo.find_one({"codigo": request.permiso})
/app/backend/server.py:16930:    usuario_destino = await db.users.find_one({"email": request.usuario_email})
/app/backend/server.py:16978:        await db.users.update_one(
/app/backend/server.py:17050:        await db.sec_bitacora_admin.insert_one({
/app/backend/server.py:17141:    rol_doc = await db.sec_roles.find_one({"codigo": request.rol, "activo": True})
/app/backend/server.py:17151:    usuario_destino = await db.users.find_one({"email": request.usuario_email})
/app/backend/server.py:17200:        await db.users.update_one(
/app/backend/server.py:17208:        rol = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
/app/backend/server.py:17326:    total = await db.sec_bitacora_admin.count_documents(filtro)
/app/backend/server.py:17329:    eventos_cursor = db.sec_bitacora_admin.find(
/app/backend/server.py:17366:    evento = await db.sec_bitacora_admin.find_one(
/app/backend/server.py:17412:    perfiles = await db.sec_perfiles.find(
/app/backend/server.py:17452:    perfil_doc = await db.sec_perfiles.find_one({"codigo": request.perfil, "activo": True})
/app/backend/server.py:17459:    usuario = await db.users.find_one({"email": request.usuario_email})
/app/backend/server.py:17462:        await db.sec_bitacora_admin.insert_one({
/app/backend/server.py:17487:    await db.users.update_one(
/app/backend/server.py:17497:    await db.sec_bitacora_admin.insert_one({
/app/backend/server.py:17556:    usuario = await db.users.find_one({"email": request.usuario_email})
/app/backend/server.py:17574:    await db.users.update_one(
/app/backend/server.py:17584:    await db.sec_bitacora_admin.insert_one({
/app/backend/server.py:17646:    empresas = await db.sec_empresas.find(
/app/backend/server.py:17671:    unidades = await db.sec_unidades_negocio.find(
/app/backend/server.py:17696:    sucursales = await db.sec_sucursales.find(
/app/backend/server.py:17743:    usuario = await db.users.find_one({"email": request.usuario_email})
/app/backend/server.py:17772:    await db.users.update_one(
/app/backend/server.py:17778:    await db.sec_bitacora_admin.insert_one({
/app/backend/server.py:17834:    usuario = await db.users.find_one({"email": request.usuario_email})
/app/backend/server.py:17854:    await db.users.update_one(
/app/backend/server.py:17860:    await db.sec_bitacora_admin.insert_one({
/app/backend/server.py:17930:    # MongoDB ELIMINADO - Este handler ya no es necesario
/app/backend/server.py:17931:    # La variable 'client' ya no existe (era el cliente de MongoDB)
/app/backend/server.py:17942:init_notifications_routes(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad
/app/backend/server.py:17948:init_scheduler_routes(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad
/app/backend/server.py:17989:    rbac_service = RBACService(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad
/app/backend/server.py:18207:        await start_scheduler(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad
/app/backend/utils/migration_helpers.py:2:EDARSA HUB - Utilidades de Migración MongoDB → SQL Server
/app/backend/utils/migration_helpers.py:4:Funciones helper para convertir código legacy MongoDB a SQL-First.
/app/backend/utils/migration_helpers.py:14:MONGO_TO_SQL_MAPPING = {
/app/backend/utils/migration_helpers.py:15:    # Colección MongoDB → Tabla SQL Server
/app/backend/utils/migration_helpers.py:16:    "mongo_db.servers": "Servidores_Conexiones",
/app/backend/utils/migration_helpers.py:17:    "mongo_db.ventas": "Comercial_Ventas_Sync",
/app/backend/utils/migration_helpers.py:18:    "mongo_db.inventarios": "Compras_Inventarios_Fisicos_Sync",
/app/backend/utils/migration_helpers.py:19:    "mongo_db.leads": "CRM_Leads",
/app/backend/utils/migration_helpers.py:20:    "mongo_db.accounts": "CRM_Cuentas",
/app/backend/utils/migration_helpers.py:21:    "mongo_db.cuentas": "CRM_Cuentas",
/app/backend/utils/migration_helpers.py:22:    "mongo_db.metas": "Comercial_Metas",
/app/backend/utils/migration_helpers.py:23:    "mongo_db.kpis_cache": "Comercial_KPIs_Cache",
/app/backend/utils/migration_helpers.py:24:    "mongo_db.dashboard_cache": "Comercial_Dashboard_Cache",
/app/backend/utils/migration_helpers.py:25:    "mongo_db.server_status": "Servidores_Status",
/app/backend/utils/migration_helpers.py:26:    "mongo_db.users": "Usuario_Catalogo",
/app/backend/utils/migration_helpers.py:27:    "mongo_db.roles": "Usuario_Roles",
/app/backend/utils/migration_helpers.py:28:    "mongo_db.clientes": "Cliente_Catalogo",
/app/backend/utils/migration_helpers.py:29:    "mongo_db.cotizaciones": "Venta_Cotizaciones",
/app/backend/utils/migration_helpers.py:30:    "mongo_db.pedidos": "Venta_Pedidos",
/app/backend/utils/migration_helpers.py:31:    "mongo_db.remisiones": "Venta_Remisiones",
/app/backend/utils/migration_helpers.py:32:    "mongo_db.solicitudes_alta": "CRM_ClientesSolicitudesAlta",
/app/backend/utils/migration_helpers.py:39:SYSTEM_PROMPT = """Eres un experto en migración de MongoDB a SQL Server para EDARSA HUB.
/app/backend/utils/migration_helpers.py:44:- MongoDB PROHIBIDO: Todo código debe usar execute_hub_query()
/app/backend/utils/migration_helpers.py:70:def migrar_mongo_a_sql(codigo_mongo: str) -> str:
/app/backend/utils/migration_helpers.py:72:    Convierte código MongoDB a SQL Server alineado al 
/app/backend/utils/migration_helpers.py:76:        codigo_mongo: Código Python con operaciones MongoDB
/app/backend/utils/migration_helpers.py:85:            return await db.servers.find({"active": True}).to_list(100)
/app/backend/utils/migration_helpers.py:88:        codigo_sql = migrar_mongo_a_sql(codigo_legacy)
/app/backend/utils/migration_helpers.py:99:    prompt = f"""Convierte este código MongoDB a SQL Server usando execute_hub_query():
/app/backend/utils/migration_helpers.py:102:    - mongo_db.servers     → Servidores_Conexiones
/app/backend/utils/migration_helpers.py:103:    - mongo_db.ventas      → Comercial_Ventas_Sync
/app/backend/utils/migration_helpers.py:104:    - mongo_db.inventarios → Compras_Inventarios_Fisicos_Sync
/app/backend/utils/migration_helpers.py:105:    - mongo_db.leads       → CRM_Leads
/app/backend/utils/migration_helpers.py:106:    - mongo_db.accounts    → CRM_Cuentas
/app/backend/utils/migration_helpers.py:107:    - mongo_db.metas       → Comercial_Metas
/app/backend/utils/migration_helpers.py:114:    CÓDIGO MONGO A TRANSFORMAR:
/app/backend/utils/migration_helpers.py:115:    {codigo_mongo}
/app/backend/utils/migration_helpers.py:159:    """Convierte mongo find() a SELECT SQL."""
/app/backend/utils/migration_helpers.py:160:    tabla = MONGO_TO_SQL_MAPPING.get(f"mongo_db.{coleccion}", coleccion)
/app/backend/utils/migration_helpers.py:182:    """Convierte mongo insert_one() a INSERT SQL."""
/app/backend/utils/migration_helpers.py:183:    tabla = MONGO_TO_SQL_MAPPING.get(f"mongo_db.{coleccion}", coleccion)
/app/backend/utils/migration_helpers.py:212:    for mongo, sql in MONGO_TO_SQL_MAPPING.items():
/app/backend/utils/migration_helpers.py:213:        print(f"  {mongo} → {sql}")
/app/backend/htmlcov/z_57760688d1f824db_cerebro_py.html:90:    <p class="pln"><span class="n"><a id="t8" href="#t8">8</a></span><span class="t"><span class="str">- Esquemas de MongoDB</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_cerebro_py.html:741:    <p class="pln"><span class="n"><a id="t659" href="#t659">659</a></span><span class="t"><span class="com"># MAPEO DE COLECCIONES MONGODB</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_cerebro_py.html:744:    <p class="run"><span class="n"><a id="t662" href="#t662">662</a></span><span class="t"><span class="nam">MONGODB_COLLECTIONS</span> <span class="op">=</span> <span class="op">{</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_cerebro_py.html:789:    <p class="pln"><span class="n"><a id="t707" href="#t707">707</a></span><span class="t"><span class="com"># &#205;NDICES MONGODB REQUERIDOS</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_cerebro_py.html:792:    <p class="run"><span class="n"><a id="t710" href="#t710">710</a></span><span class="t"><span class="nam">MONGODB_INDEXES</span> <span class="op">=</span> <span class="op">{</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_cerebro_py.html:869:    <p class="run run2"><span class="n"><a id="t787" href="#t787">787</a></span><span class="t">    <span class="str">'MONGODB_COLLECTIONS'</span><span class="op">,</span> <span class="str">'MONGODB_INDEXES'</span><span class="op">,</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/class_index.html:568:                <td class="name"><a href="z_57760688d1f824db_db_py.html">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/z_97abb2331ed8fa5c_repository_py.html:86:    <p class="pln"><span class="n"><a id="t4" href="#t4">4</a></span><span class="t"><span class="str">Acceso a datos para usuarios y roles en MongoDB.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_97abb2331ed8fa5c_repository_py.html:89:    <p class="pln"><span class="n"><a id="t7" href="#t7">7</a></span><span class="t"><span class="str">- Encapsula operaciones de MongoDB para auth</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_97abb2331ed8fa5c_repository_py.html:99:    <p class="pln"><span class="n"><a id="t17" href="#t17">17</a></span><span class="t"><span class="com"># INYECCI&#211;N DE DEPENDENCIA: MongoDB</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_97abb2331ed8fa5c_repository_py.html:107:    <p class="pln"><span class="n"><a id="t25" href="#t25">25</a></span><span class="t"><span class="str">    Inicializa el repositorio con la conexi&#243;n a MongoDB.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_97abb2331ed8fa5c_repository_py.html:110:    <p class="pln"><span class="n"><a id="t28" href="#t28">28</a></span><span class="t"><span class="str">        database: Instancia de AsyncIOMotorDatabase</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_97abb2331ed8fa5c_repository_py.html:117:    <p class="pln"><span class="n"><a id="t35" href="#t35">35</a></span><span class="t">    <span class="str">"""Obtiene la conexi&#243;n a MongoDB inyectada."""</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:5:    <title>Coverage for core/db.py: 47%</title>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:14:            <span class="text">Coverage for </span><b>core&#8201;/&#8201;db.py</b>:
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:86:    <p class="pln"><span class="n"><a id="t4" href="#t4">4</a></span><span class="t"><span class="str">Gesti&#243;n centralizada de conexiones a MongoDB y SQL Server.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:554:    <p class="pln"><span class="n"><a id="t472" href="#t472">472</a></span><span class="t"><span class="com"># FUNCIONES DE MONGODB (Placeholders para fases futuras)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:557:    <p class="run"><span class="n"><a id="t475" href="#t475">475</a></span><span class="t"><span class="key">from</span> <span class="nam">motor</span><span class="op">.</span><span class="nam">motor_asyncio</span> <span class="key">import</span> <span class="nam">AsyncIOMotorClient</span><span class="op">,</span> <span class="nam">AsyncIOMotorDatabase</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:558:    <p class="run"><span class="n"><a id="t476" href="#t476">476</a></span><span class="t"><span class="key">from</span> <span class="nam">pymongo</span> <span class="key">import</span> <span class="nam">MongoClient</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:560:    <p class="pln"><span class="n"><a id="t478" href="#t478">478</a></span><span class="t"><span class="com"># Variables globales para conexiones MongoDB (se inicializar&#225;n en migraci&#243;n futura)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:561:    <p class="run"><span class="n"><a id="t479" href="#t479">479</a></span><span class="t"><span class="nam">_mongo_client</span><span class="op">:</span> <span class="nam">Optional</span><span class="op">[</span><span class="nam">AsyncIOMotorClient</span><span class="op">]</span> <span class="op">=</span> <span class="key">None</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:562:    <p class="run"><span class="n"><a id="t480" href="#t480">480</a></span><span class="t"><span class="nam">_mongo_db</span><span class="op">:</span> <span class="nam">Optional</span><span class="op">[</span><span class="nam">AsyncIOMotorDatabase</span><span class="op">]</span> <span class="op">=</span> <span class="key">None</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:563:    <p class="run"><span class="n"><a id="t481" href="#t481">481</a></span><span class="t"><span class="nam">_sync_mongo_client</span><span class="op">:</span> <span class="nam">Optional</span><span class="op">[</span><span class="nam">MongoClient</span><span class="op">]</span> <span class="op">=</span> <span class="key">None</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:566:    <p class="run"><span class="n"><a id="t484" href="#t484">484</a></span><span class="t"><span class="key">async</span> <span class="key">def</span> <span class="nam">get_mongo_client</span><span class="op">(</span><span class="op">)</span> <span class="op">-></span> <span class="nam">AsyncIOMotorClient</span><span class="op">:</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:568:    <p class="pln"><span class="n"><a id="t486" href="#t486">486</a></span><span class="t"><span class="str">    Obtiene el cliente MongoDB async.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:571:    <p class="pln"><span class="n"><a id="t489" href="#t489">489</a></span><span class="t">    <span class="key">global</span> <span class="nam">_mongo_client</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:572:    <p class="mis show_mis"><span class="n"><a id="t490" href="#t490">490</a></span><span class="t">    <span class="key">if</span> <span class="nam">_mongo_client</span> <span class="key">is</span> <span class="key">None</span><span class="op">:</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:573:    <p class="mis show_mis"><span class="n"><a id="t491" href="#t491">491</a></span><span class="t">        <span class="key">raise</span> <span class="nam">RuntimeError</span><span class="op">(</span><span class="str">"MongoDB client not initialized. Use server.py connection."</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:574:    <p class="mis show_mis"><span class="n"><a id="t492" href="#t492">492</a></span><span class="t">    <span class="key">return</span> <span class="nam">_mongo_client</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:577:    <p class="run"><span class="n"><a id="t495" href="#t495">495</a></span><span class="t"><span class="key">async</span> <span class="key">def</span> <span class="nam">get_mongo_db</span><span class="op">(</span><span class="op">)</span> <span class="op">-></span> <span class="nam">AsyncIOMotorDatabase</span><span class="op">:</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:579:    <p class="pln"><span class="n"><a id="t497" href="#t497">497</a></span><span class="t"><span class="str">    Obtiene la base de datos MongoDB async.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:582:    <p class="pln"><span class="n"><a id="t500" href="#t500">500</a></span><span class="t">    <span class="key">global</span> <span class="nam">_mongo_db</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:583:    <p class="mis show_mis"><span class="n"><a id="t501" href="#t501">501</a></span><span class="t">    <span class="key">if</span> <span class="nam">_mongo_db</span> <span class="key">is</span> <span class="key">None</span><span class="op">:</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:584:    <p class="mis show_mis"><span class="n"><a id="t502" href="#t502">502</a></span><span class="t">        <span class="key">raise</span> <span class="nam">RuntimeError</span><span class="op">(</span><span class="str">"MongoDB database not initialized. Use server.py connection."</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:585:    <p class="mis show_mis"><span class="n"><a id="t503" href="#t503">503</a></span><span class="t">    <span class="key">return</span> <span class="nam">_mongo_db</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:588:    <p class="run"><span class="n"><a id="t506" href="#t506">506</a></span><span class="t"><span class="key">def</span> <span class="nam">get_sync_mongo_db</span><span class="op">(</span><span class="op">)</span><span class="op">:</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:590:    <p class="pln"><span class="n"><a id="t508" href="#t508">508</a></span><span class="t"><span class="str">    Obtiene la base de datos MongoDB s&#237;ncrona.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:593:    <p class="pln"><span class="n"><a id="t511" href="#t511">511</a></span><span class="t">    <span class="key">global</span> <span class="nam">_sync_mongo_client</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:594:    <p class="mis show_mis"><span class="n"><a id="t512" href="#t512">512</a></span><span class="t">    <span class="key">if</span> <span class="nam">_sync_mongo_client</span> <span class="key">is</span> <span class="key">None</span><span class="op">:</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:595:    <p class="mis show_mis"><span class="n"><a id="t513" href="#t513">513</a></span><span class="t">        <span class="key">raise</span> <span class="nam">RuntimeError</span><span class="op">(</span><span class="str">"Sync MongoDB client not initialized. Use server.py connection."</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:596:    <p class="mis show_mis"><span class="n"><a id="t514" href="#t514">514</a></span><span class="t">    <span class="key">return</span> <span class="nam">_sync_mongo_client</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:599:    <p class="run"><span class="n"><a id="t517" href="#t517">517</a></span><span class="t"><span class="key">def</span> <span class="nam">init_db_connections</span><span class="op">(</span><span class="nam">mongo_url</span><span class="op">:</span> <span class="nam">str</span><span class="op">,</span> <span class="nam">db_name</span><span class="op">:</span> <span class="nam">str</span><span class="op">)</span><span class="op">:</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:602:    <p class="pln"><span class="n"><a id="t520" href="#t520">520</a></span><span class="t"><span class="str">    NOTA: Se usar&#225; cuando se migre MongoDB desde server.py (fase futura)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:624:    <p class="run run2"><span class="n"><a id="t542" href="#t542">542</a></span><span class="t">    <span class="com"># MongoDB - Placeholders</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:625:    <p class="run run2"><span class="n"><a id="t543" href="#t543">543</a></span><span class="t">    <span class="str">'get_mongo_client'</span><span class="op">,</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:626:    <p class="run run2"><span class="n"><a id="t544" href="#t544">544</a></span><span class="t">    <span class="str">'get_mongo_db'</span><span class="op">,</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_db_py.html:627:    <p class="run run2"><span class="n"><a id="t545" href="#t545">545</a></span><span class="t">    <span class="str">'get_sync_mongo_db'</span><span class="op">,</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_97abb2331ed8fa5c_service_py.html:131:    <p class="pln"><span class="n"><a id="t49" href="#t49">49</a></span><span class="t">    <span class="com"># Preparar documento para MongoDB</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_routes_py.html:121:    <p class="pln"><span class="n"><a id="t39" href="#t39">39</a></span><span class="t"><span class="str">los helpers que usan la conexi&#243;n global a MongoDB.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_config_py.html:93:    <p class="pln"><span class="n"><a id="t11" href="#t11">11</a></span><span class="t"><span class="str">    print(settings.MONGO_URL)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_config_py.html:107:    <p class="pln"><span class="n"><a id="t25" href="#t25">25</a></span><span class="t">    <span class="com"># MongoDB</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_config_py.html:108:    <p class="mis show_mis"><span class="n"><a id="t26" href="#t26">26</a></span><span class="t">    <span class="nam">MONGO_URL</span><span class="op">:</span> <span class="nam">str</span> <span class="op">=</span> <span class="nam">os</span><span class="op">.</span><span class="nam">environ</span><span class="op">.</span><span class="nam">get</span><span class="op">(</span><span class="str">"MONGO_URL"</span><span class="op">,</span> <span class="str">"mongodb://localhost:27017"</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_repository_py.html:90:    <p class="pln"><span class="n"><a id="t8" href="#t8">8</a></span><span class="t"><span class="str">- Acceso a MongoDB para configuraci&#243;n de servidores</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_repository_py.html:105:    <p class="pln"><span class="n"><a id="t23" href="#t23">23</a></span><span class="t"><span class="com"># INYECCI&#211;N DE DEPENDENCIA: MongoDB</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_repository_py.html:112:    <p class="pln"><span class="n"><a id="t30" href="#t30">30</a></span><span class="t">    <span class="str">"""Inicializa el repositorio con la conexi&#243;n a MongoDB."""</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_repository_py.html:118:    <p class="pln"><span class="n"><a id="t36" href="#t36">36</a></span><span class="t">    <span class="str">"""Obtiene la conexi&#243;n a MongoDB inyectada."""</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_repository_py.html:242:    <p class="pln"><span class="n"><a id="t160" href="#t160">160</a></span><span class="t"><span class="str">    Obtiene las metas de una sucursal desde MongoDB.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_repository_py.html:252:    <p class="pln"><span class="n"><a id="t170" href="#t170">170</a></span><span class="t"><span class="str">    Guarda las metas de una sucursal en MongoDB.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:91:    <p class="pln"><span class="n"><a id="t9" href="#t9">9</a></span><span class="t"><span class="str">- Fallback entre MongoDB y configuraci&#243;n hardcodeada</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:316:    <p class="pln"><span class="n"><a id="t234" href="#t234">234</a></span><span class="t">    <span class="com"># ========== BUSCAR APIs LOCALES DESDE MONGODB ==========</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:317:    <p class="mis show_mis"><span class="n"><a id="t235" href="#t235">235</a></span><span class="t">    <span class="nam">print</span><span class="op">(</span><span class="str">f"*** API Local: Buscando APIs tipo 'api_mpro' en MongoDB ***"</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:319:    <p class="mis show_mis"><span class="n"><a id="t237" href="#t237">237</a></span><span class="t">        <span class="key">from</span> <span class="nam">pymongo</span> <span class="key">import</span> <span class="nam">MongoClient</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:320:    <p class="mis show_mis"><span class="n"><a id="t238" href="#t238">238</a></span><span class="t">        <span class="nam">sync_client</span> <span class="op">=</span> <span class="nam">MongoClient</span><span class="op">(</span><span class="nam">os</span><span class="op">.</span><span class="nam">environ</span><span class="op">.</span><span class="nam">get</span><span class="op">(</span><span class="str">'MONGO_URL'</span><span class="op">,</span> <span class="str">'mongodb://localhost:27017'</span><span class="op">)</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:324:    <p class="mis show_mis"><span class="n"><a id="t242" href="#t242">242</a></span><span class="t">        <span class="nam">print</span><span class="op">(</span><span class="str">f"*** API Local: Encontradas {len(apis_locales_db)} APIs en MongoDB ***"</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:326:    <p class="mis show_mis"><span class="n"><a id="t244" href="#t244">244</a></span><span class="t">        <span class="nam">print</span><span class="op">(</span><span class="str">f"*** API Local: Error buscando en MongoDB: {e} ***"</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:388:    <p class="mis show_mis"><span class="n"><a id="t306" href="#t306">306</a></span><span class="t">    <span class="nam">print</span><span class="op">(</span><span class="str">f"*** API Local: No encontrada en MongoDB, buscando en config hardcodeada ***"</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db___init___py.html:88:    <p class="pln"><span class="n"><a id="t6" href="#t6">6</a></span><span class="t"><span class="com"># - db.py: Conexiones SQL Server, execute_sql_query()</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db___init___py.html:131:    <p class="run run2"><span class="n"><a id="t49" href="#t49">49</a></span><span class="t">    <span class="nam">MONGODB_COLLECTIONS</span><span class="op">,</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db___init___py.html:132:    <p class="run run2"><span class="n"><a id="t50" href="#t50">50</a></span><span class="t">    <span class="nam">MONGODB_INDEXES</span><span class="op">,</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/function_index.html:138:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t43">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:148:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t111">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:158:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t137">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:168:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t154">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:178:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t185">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:188:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t219">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:198:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t229">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:208:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t244">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:218:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t297">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:228:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t383">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:238:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t484">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:239:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t484"><data value='get_mongo_client'>get_mongo_client</data></a></td>
/app/backend/htmlcov/function_index.html:248:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t495">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:249:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t495"><data value='get_mongo_db'>get_mongo_db</data></a></td>
/app/backend/htmlcov/function_index.html:258:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t506">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:259:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t506"><data value='get_sync_mongo_db'>get_sync_mongo_db</data></a></td>
/app/backend/htmlcov/function_index.html:268:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t517">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/function_index.html:278:                <td class="name"><a href="z_57760688d1f824db_db_py.html">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/z_57760688d1f824db_security_py.html:96:    <p class="pln"><span class="n"><a id="t14" href="#t14">14</a></span><span class="t"><span class="str">- La conexi&#243;n a MongoDB se inyecta v&#237;a init_security()</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_security_py.html:124:    <p class="pln"><span class="n"><a id="t42" href="#t42">42</a></span><span class="t"><span class="com"># INYECCI&#211;N DE DEPENDENCIA: MongoDB</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_security_py.html:126:    <p class="pln"><span class="n"><a id="t44" href="#t44">44</a></span><span class="t"><span class="com"># La conexi&#243;n a MongoDB se inyecta desde server.py para evitar imports circulares</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_security_py.html:134:    <p class="pln"><span class="n"><a id="t52" href="#t52">52</a></span><span class="t"><span class="str">    Inicializa el m&#243;dulo de seguridad con la conexi&#243;n a MongoDB.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_security_py.html:138:    <p class="pln"><span class="n"><a id="t56" href="#t56">56</a></span><span class="t"><span class="str">        database: Instancia de AsyncIOMotorDatabase</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_security_py.html:142:    <p class="run"><span class="n"><a id="t60" href="#t60">60</a></span><span class="t">    <span class="nam">logging</span><span class="op">.</span><span class="nam">info</span><span class="op">(</span><span class="str">"[SECURITY] M&#243;dulo de seguridad inicializado con conexi&#243;n a MongoDB"</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_security_py.html:146:    <p class="pln"><span class="n"><a id="t64" href="#t64">64</a></span><span class="t">    <span class="str">"""Obtiene la conexi&#243;n a MongoDB inyectada."""</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_57760688d1f824db_security_py.html:241:    <p class="pln"><span class="n"><a id="t159" href="#t159">159</a></span><span class="t"><span class="str">    Extrae el token del header Authorization, lo verifica, y busca el usuario en MongoDB.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/index.html:103:                <td class="name"><a href="z_57760688d1f824db_db_py.html">core&#8201;/&#8201;db.py</a></td>
/app/backend/htmlcov/z_97abb2331ed8fa5c___init___py.html:94:    <p class="pln"><span class="n"><a id="t12" href="#t12">12</a></span><span class="t"><span class="str">- repository.py: Acceso a MongoDB</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_97abb2331ed8fa5c___init___py.html:112:    <p class="pln"><span class="n"><a id="t30" href="#t30">30</a></span><span class="t"><span class="str">    Inicializa el m&#243;dulo de auth con la conexi&#243;n a MongoDB.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_97abb2331ed8fa5c___init___py.html:115:    <p class="pln"><span class="n"><a id="t33" href="#t33">33</a></span><span class="t"><span class="str">        database: Instancia de AsyncIOMotorDatabase</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_6b2bb3a826453387___init___py.html:94:    <p class="pln"><span class="n"><a id="t12" href="#t12">12</a></span><span class="t"><span class="str">- repository.py: Acceso a MongoDB y SQL Server</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_6b2bb3a826453387___init___py.html:119:    <p class="pln"><span class="n"><a id="t37" href="#t37">37</a></span><span class="t"><span class="str">    Inicializa el m&#243;dulo de compras con la conexi&#243;n a MongoDB.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_6b2bb3a826453387___init___py.html:122:    <p class="pln"><span class="n"><a id="t40" href="#t40">40</a></span><span class="t"><span class="str">        database: Instancia de AsyncIOMotorDatabase</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/status.json:1:{"note":"This file is an internal implementation detail to speed up HTML report generation. Its format can change at any time. You might be looking for the JSON report: https://coverage.rtfd.io/cmd.html#cmd-json","format":5,"version":"7.13.5","globals":"b9cbe3e2a925ac5704936e240af529ac","files":{"z_57760688d1f824db___init___py":{"hash":"e632a0169ec7d52e6477bb010e8103d7","index":{"url":"z_57760688d1f824db___init___py.html","file":"core/__init__.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":2,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_57760688d1f824db_cerebro_py":{"hash":"5b9d0c6721dad58a12b7cd19180b80f7","index":{"url":"z_57760688d1f824db_cerebro_py.html","file":"core/cerebro.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":408,"n_excluded":0,"n_missing":8,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_57760688d1f824db_config_py":{"hash":"e1ded291680e411b83b97cafd2473011","index":{"url":"z_57760688d1f824db_config_py.html","file":"core/config.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":18,"n_excluded":0,"n_missing":18,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_57760688d1f824db_db_py":{"hash":"29c8355449a7d67a2b6bbde338c36ef4","index":{"url":"z_57760688d1f824db_db_py.html","file":"core/db.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":199,"n_excluded":0,"n_missing":105,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_57760688d1f824db_exceptions_py":{"hash":"0677e56c54ca86f7338cf2ae9942c495","index":{"url":"z_57760688d1f824db_exceptions_py.html","file":"core/exceptions.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":33,"n_excluded":0,"n_missing":33,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_57760688d1f824db_pool_py":{"hash":"9bc0844e91b173e8a2c689d6d395d89c","index":{"url":"z_57760688d1f824db_pool_py.html","file":"core/pool.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":164,"n_excluded":1,"n_missing":69,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_57760688d1f824db_security_py":{"hash":"3a64216da7cf287d94b07596e5cf2ad9","index":{"url":"z_57760688d1f824db_security_py.html","file":"core/security.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":69,"n_excluded":0,"n_missing":41,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_57760688d1f824db_utils_py":{"hash":"e64a2b06515a290f431bd4799a5e6616","index":{"url":"z_57760688d1f824db_utils_py.html","file":"core/utils.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":48,"n_excluded":0,"n_missing":48,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_9b7b1f9db13f9215___init___py":{"hash":"296bcca9572f10dbfff58925b38f38e8","index":{"url":"z_9b7b1f9db13f9215___init___py.html","file":"modules/__init__.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":0,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_c348213887c64d5b___init___py":{"hash":"a36cdc8cf3265444f16fc0689ee7453a","index":{"url":"z_c348213887c64d5b___init___py.html","file":"modules/activos/__init__.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":0,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_c348213887c64d5b_repository_py":{"hash":"af89dc45beb9fb958ee2f56520374f4d","index":{"url":"z_c348213887c64d5b_repository_py.html","file":"modules/activos/repository.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":3,"n_excluded":0,"n_missing":3,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_c348213887c64d5b_routes_py":{"hash":"560c94d30e9d9822dd4624fbbcc50b93","index":{"url":"z_c348213887c64d5b_routes_py.html","file":"modules/activos/routes.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":2,"n_excluded":0,"n_missing":2,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_c348213887c64d5b_schemas_py":{"hash":"158b304924d2444127580e2e0a6eddf8","index":{"url":"z_c348213887c64d5b_schemas_py.html","file":"modules/activos/schemas.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":3,"n_excluded":0,"n_missing":3,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_c348213887c64d5b_service_py":{"hash":"8e99136d43fda04de1112bb6c999539c","index":{"url":"z_c348213887c64d5b_service_py.html","file":"modules/activos/service.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":3,"n_excluded":0,"n_missing":3,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_97abb2331ed8fa5c___init___py":{"hash":"917da5cbf1c937a64e9b29f17f4277ad","index":{"url":"z_97abb2331ed8fa5c___init___py.html","file":"modules/auth/__init__.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":6,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_97abb2331ed8fa5c_repository_py":{"hash":"9322e538d744e27ed73354a8b992f5b1","index":{"url":"z_97abb2331ed8fa5c_repository_py.html","file":"modules/auth/repository.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":56,"n_excluded":0,"n_missing":34,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_97abb2331ed8fa5c_routes_py":{"hash":"cb856cefb6b7537eeb18a27a9113052a","index":{"url":"z_97abb2331ed8fa5c_routes_py.html","file":"modules/auth/routes.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":46,"n_excluded":0,"n_missing":14,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_97abb2331ed8fa5c_schemas_py":{"hash":"dfbf4029c8ec5c65e00ff645495b5e1f","index":{"url":"z_97abb2331ed8fa5c_schemas_py.html","file":"modules/auth/schemas.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":59,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_97abb2331ed8fa5c_service_py":{"hash":"0ed2e4feec12aaf62b0a88da768d2cc2","index":{"url":"z_97abb2331ed8fa5c_service_py.html","file":"modules/auth/service.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":109,"n_excluded":0,"n_missing":91,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_342fa9d1c388b58c___init___py":{"hash":"8498fc338a14668b452ece41b3a4d3f7","index":{"url":"z_342fa9d1c388b58c___init___py.html","file":"modules/comercial/__init__.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":7,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_342fa9d1c388b58c_adapters_py":{"hash":"c1a33582dc921743ce36eda87bc08081","index":{"url":"z_342fa9d1c388b58c_adapters_py.html","file":"modules/comercial/adapters.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":150,"n_excluded":0,"n_missing":140,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_342fa9d1c388b58c_repository_py":{"hash":"65ffafb8fc1800d5982c77e77db1c56d","index":{"url":"z_342fa9d1c388b58c_repository_py.html","file":"modules/comercial/repository.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":32,"n_excluded":0,"n_missing":16,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_342fa9d1c388b58c_routes_py":{"hash":"99e4f5ec2eba4dfd5f1ac74ac20dac05","index":{"url":"z_342fa9d1c388b58c_routes_py.html","file":"modules/comercial/routes.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":3,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_342fa9d1c388b58c_schemas_py":{"hash":"791833f1eb5b8cbece3532386215cab7","index":{"url":"z_342fa9d1c388b58c_schemas_py.html","file":"modules/comercial/schemas.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":45,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_342fa9d1c388b58c_service_py":{"hash":"e50d7be40ce91ce1ebf7611179332dc9","index":{"url":"z_342fa9d1c388b58c_service_py.html","file":"modules/comercial/service.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":33,"n_excluded":0,"n_missing":33,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_6b2bb3a826453387___init___py":{"hash":"63a2749b5280e4856956d7b8f4f77cc3","index":{"url":"z_6b2bb3a826453387___init___py.html","file":"modules/compras/__init__.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":6,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_6b2bb3a826453387_repository_py":{"hash":"653a678c34b82bbf4d128b1b59faf6e2","index":{"url":"z_6b2bb3a826453387_repository_py.html","file":"modules/compras/repository.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":43,"n_excluded":0,"n_missing":26,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_6b2bb3a826453387_routes_py":{"hash":"67088c1261676171f4973b0e92569d68","index":{"url":"z_6b2bb3a826453387_routes_py.html","file":"modules/compras/routes.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":8,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_6b2bb3a826453387_schemas_py":{"hash":"5e3ca32a07640e65a591fff543ee05f0","index":{"url":"z_6b2bb3a826453387_schemas_py.html","file":"modules/compras/schemas.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":63,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_6b2bb3a826453387_service_py":{"hash":"c9e734da44eec108f988db69289a90c3","index":{"url":"z_6b2bb3a826453387_service_py.html","file":"modules/compras/service.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":78,"n_excluded":0,"n_missing":67,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_91ede755e2552dd3___init___py":{"hash":"042ca3c9116aa1c0529f0f17f5a61ac6","index":{"url":"z_91ede755e2552dd3___init___py.html","file":"modules/inventarios/__init__.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":0,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_91ede755e2552dd3_repository_py":{"hash":"e7b987fbe2f29b7c7c871f2b434158c8","index":{"url":"z_91ede755e2552dd3_repository_py.html","file":"modules/inventarios/repository.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":3,"n_excluded":0,"n_missing":3,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_91ede755e2552dd3_routes_py":{"hash":"87facbaaab4592aa48c4be09971c6150","index":{"url":"z_91ede755e2552dd3_routes_py.html","file":"modules/inventarios/routes.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":2,"n_excluded":0,"n_missing":2,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_91ede755e2552dd3_schemas_py":{"hash":"e98f42209f8bff5e8c248e3265e3a6c2","index":{"url":"z_91ede755e2552dd3_schemas_py.html","file":"modules/inventarios/schemas.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":3,"n_excluded":0,"n_missing":3,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_91ede755e2552dd3_service_py":{"hash":"e98a2e79d8871030159f17779b36b070","index":{"url":"z_91ede755e2552dd3_service_py.html","file":"modules/inventarios/service.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":3,"n_excluded":0,"n_missing":3,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_98101bc7a889e7a6___init___py":{"hash":"aa574e1a40f75aaa4c63506aa70a843a","index":{"url":"z_98101bc7a889e7a6___init___py.html","file":"modules/proveedores/__init__.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":0,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_98101bc7a889e7a6_repository_py":{"hash":"7c6fead2df10842f8107bfbfe04d0a2b","index":{"url":"z_98101bc7a889e7a6_repository_py.html","file":"modules/proveedores/repository.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":3,"n_excluded":0,"n_missing":3,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_98101bc7a889e7a6_routes_py":{"hash":"f4f74fdc7ab6689212de2353a1c38808","index":{"url":"z_98101bc7a889e7a6_routes_py.html","file":"modules/proveedores/routes.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":2,"n_excluded":0,"n_missing":2,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_98101bc7a889e7a6_schemas_py":{"hash":"af9f047a60b117f27e36e95bfb89e56f","index":{"url":"z_98101bc7a889e7a6_schemas_py.html","file":"modules/proveedores/schemas.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":3,"n_excluded":0,"n_missing":3,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_98101bc7a889e7a6_service_py":{"hash":"1b99a798a957d1872c211e8184b1cd2d","index":{"url":"z_98101bc7a889e7a6_service_py.html","file":"modules/proveedores/service.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":3,"n_excluded":0,"n_missing":3,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_d8ba6d3310d96e62___init___py":{"hash":"3633cc75e727e5ccb7cf11e24ae127f2","index":{"url":"z_d8ba6d3310d96e62___init___py.html","file":"modules/rh/__init__.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":0,"n_excluded":0,"n_missing":0,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_d8ba6d3310d96e62_repository_py":{"hash":"a246688d989919566766816a1d0d6d73","index":{"url":"z_d8ba6d3310d96e62_repository_py.html","file":"modules/rh/repository.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":3,"n_excluded":0,"n_missing":3,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_d8ba6d3310d96e62_routes_py":{"hash":"da660154a73df315987f4f3645ae6636","index":{"url":"z_d8ba6d3310d96e62_routes_py.html","file":"modules/rh/routes.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":2,"n_excluded":0,"n_missing":2,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_d8ba6d3310d96e62_schemas_py":{"hash":"cb76bfa16c4589d0c8ad7c8fd5c0e7ed","index":{"url":"z_d8ba6d3310d96e62_schemas_py.html","file":"modules/rh/schemas.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":10,"n_excluded":0,"n_missing":10,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}},"z_d8ba6d3310d96e62_service_py":{"hash":"b001b3171157c295b5d023ff7208c917","index":{"url":"z_d8ba6d3310d96e62_service_py.html","file":"modules/rh/service.py","description":"","nums":{"precision":0,"n_files":1,"n_statements":3,"n_excluded":0,"n_missing":3,"n_branches":0,"n_partial_branches":0,"n_missing_branches":0}}}}}
/app/backend/htmlcov/z_6b2bb3a826453387_repository_py.html:90:    <p class="pln"><span class="n"><a id="t8" href="#t8">8</a></span><span class="t"><span class="str">- Acceso a MongoDB para configuraci&#243;n de servidores</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_6b2bb3a826453387_repository_py.html:100:    <p class="pln"><span class="n"><a id="t18" href="#t18">18</a></span><span class="t"><span class="com"># INYECCI&#211;N DE DEPENDENCIA: MongoDB</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_6b2bb3a826453387_repository_py.html:107:    <p class="pln"><span class="n"><a id="t25" href="#t25">25</a></span><span class="t">    <span class="str">"""Inicializa el repositorio con la conexi&#243;n a MongoDB."""</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_6b2bb3a826453387_repository_py.html:113:    <p class="pln"><span class="n"><a id="t31" href="#t31">31</a></span><span class="t">    <span class="str">"""Obtiene la conexi&#243;n a MongoDB inyectada."""</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_6b2bb3a826453387_repository_py.html:129:    <p class="pln"><span class="n"><a id="t47" href="#t47">47</a></span><span class="t"><span class="com"># PAR&#193;METROS DE COMPRAS (MongoDB)</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c___init___py.html:94:    <p class="pln"><span class="n"><a id="t12" href="#t12">12</a></span><span class="t"><span class="str">- repository.py: Queries SQL y acceso a MongoDB</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c___init___py.html:130:    <p class="pln"><span class="n"><a id="t48" href="#t48">48</a></span><span class="t"><span class="str">    Inicializa el m&#243;dulo comercial con la conexi&#243;n a MongoDB.</span>&nbsp;</span><span class="r"></span></p>
/app/backend/htmlcov/z_342fa9d1c388b58c___init___py.html:133:    <p class="pln"><span class="n"><a id="t51" href="#t51">51</a></span><span class="t"><span class="str">        database: Instancia de AsyncIOMotorDatabase</span>&nbsp;</span><span class="r"></span></p>
/app/backend/.env.test.example:32:# MongoDB para tests (opcional, usa mock por defecto)
/app/backend/.env.test.example:33:# MONGO_URL=mongodb://localhost:27017
/app/backend/sql/auditoria_financiera.sql:6:-- Ubicación: SQL Server EDARSA HUB (fuente oficial, NO MongoDB)
/app/backend/.env:1:MONGO_URL="mongodb://localhost:27017"
/app/backend/.env:39:# FASE 2-E: ACTIVADO - SQL es fuente primaria con fallback MongoDB
/app/backend/.env:42:# Jobs deshabilitados temporalmente - Migración MongoDB->SQL incompleta
/app/backend/api/catalogos_sistemas.py:23:- NO usar MongoDB
/app/backend/api/admin_data_quality.py:13:- NO MongoDB
/app/backend/api/admin_scheduler_resync.py:18:NO USA MONGODB - 100% SQL Server
/app/backend/api/sync_receiver.py:59:    """Inicializa el módulo con la conexión a MongoDB."""
/app/backend/api/sync_receiver.py:66:    """Obtiene la conexión a MongoDB."""
/app/backend/api/sync_receiver.py:187:    server = await db.sql_servers.find_one({"id": payload.server_id})
/app/backend/api/sync_receiver.py:232:    await db.sync_agent_registry.update_one(
/app/backend/api/sync_receiver.py:276:    server = await db.sql_servers.find_one({"id": request.server_id})
/app/backend/api/sync_receiver.py:286:    await db.sync_agent_registry.update_one(
/app/backend/api/sync_receiver.py:319:    coll = db.sync_agent_registry
/app/backend/api/admin_core_connections.py:32:from core.db import execute_sql_query, get_mongo_db
/app/backend/api/admin_core_connections.py:111:    # Guardar en MongoDB si está disponible
/app/backend/api/admin_core_connections.py:113:        db = get_mongo_db()
/app/backend/api/admin_core_connections.py:115:            db.auditoria_core_admin.insert_one(log_data)
/app/backend/api/admin_core_connections.py:209:def format_core_connection(conn: Dict, include_mongo: bool = True) -> Dict:
/app/backend/api/admin_core_connections.py:245:    # Verificar MongoDB si aplica
/app/backend/api/admin_core_connections.py:246:    if include_mongo:
/app/backend/api/admin_core_connections.py:248:            db = get_mongo_db()
/app/backend/api/admin_core_connections.py:250:                mongo_server = db.servidores_conexiones.find_one({'id': conn.get('id')})
/app/backend/api/admin_core_connections.py:251:                formatted['mongodb_id'] = str(mongo_server.get('_id')) if mongo_server else None
/app/backend/api/admin_core_connections.py:252:                formatted['mongo_synced'] = mongo_server is not None
/app/backend/api/admin_core_connections.py:254:            formatted['mongodb_id'] = None
/app/backend/api/admin_core_connections.py:255:            formatted['mongo_synced'] = False
/app/backend/server.py.backup_pre_fase2a:6:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/server.py.backup_pre_fase2a:37:# MongoDB connection
/app/backend/server.py.backup_pre_fase2a:38:mongo_url = os.environ['MONGO_URL']
/app/backend/server.py.backup_pre_fase2a:39:client = AsyncIOMotorClient(mongo_url)
/app/backend/server.py.backup_pre_fase2a:87:# Inicializar módulo de seguridad con conexión a MongoDB
/app/backend/server.py.backup_pre_fase2a:100:# Inicializar módulo auth con conexión a MongoDB
/app/backend/server.py.backup_pre_fase2a:168:# - ARQUITECTURA: SQL Server (persistencia) + MongoDB (cache)
/app/backend/server.py.backup_pre_fase2a:186:# Inicializar módulo RH con conexión a MongoDB
/app/backend/server.py.backup_pre_fase2a:230:# ARQUITECTURA: SQL Server EDARSA HUB (persistencia) + MongoDB (cache)
/app/backend/server.py.backup_pre_fase2a:579:# Las funciones de SQL Server han sido migradas a /core/db.py
/app/backend/server.py.backup_pre_fase2a:910:    await db.servers.insert_one(doc)
/app/backend/server.py.backup_pre_fase2a:916:    servers = await db.servers.find({"active": True}, {"_id": 0, "password": 0}).to_list(1000)
/app/backend/server.py.backup_pre_fase2a:925:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0, "password": 0})
/app/backend/server.py.backup_pre_fase2a:936:    existing = await db.servers.find_one({"id": server_id})
/app/backend/server.py.backup_pre_fase2a:948:    await db.servers.update_one({"id": server_id}, {"$set": update_data})
/app/backend/server.py.backup_pre_fase2a:956:    await db.servers.update_one({"id": server_id}, {"$set": {"active": False}})
/app/backend/server.py.backup_pre_fase2a:968:    server = await db.servers.find_one({"id": server_id})
/app/backend/server.py.backup_pre_fase2a:990:            await db.server_status.update_one(
/app/backend/server.py.backup_pre_fase2a:1017:        await db.server_status.update_one(
/app/backend/server.py.backup_pre_fase2a:1049:    await db.queries.insert_one(doc)
/app/backend/server.py.backup_pre_fase2a:1059:    queries = await db.queries.find(filter_query, {"_id": 0}).to_list(1000)
/app/backend/server.py.backup_pre_fase2a:1067:    await db.queries.update_one({"id": query_id}, {"$set": query_data})
/app/backend/server.py.backup_pre_fase2a:1075:    await db.queries.delete_one({"id": query_id})
/app/backend/server.py.backup_pre_fase2a:1184:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:1275:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:1289:    update_result = await db.servers.update_one(
/app/backend/server.py.backup_pre_fase2a:1295:    updated_server = await db.servers.find_one({"id": server_id}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:1302:    await db.servers.update_one(
/app/backend/server.py.backup_pre_fase2a:1320:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:1374:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:1379:    await db.servers.update_one(
/app/backend/server.py.backup_pre_fase2a:1391:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:1435:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:1477:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:1524:    configs = await db.server_sucursales_config.find(
/app/backend/server.py.backup_pre_fase2a:1575:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:1662:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:1717:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:1722:    configs = await db.server_sucursales_config.find(
/app/backend/server.py.backup_pre_fase2a:1745:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:1769:    existing_configs = await db.server_sucursales_config.find(
/app/backend/server.py.backup_pre_fase2a:1786:            await db.server_sucursales_config.update_one(
/app/backend/server.py.backup_pre_fase2a:1812:            await db.server_sucursales_config.insert_one(new_config)
/app/backend/server.py.backup_pre_fase2a:1816:    configs = await db.server_sucursales_config.find(
/app/backend/server.py.backup_pre_fase2a:1841:    existing = await db.server_sucursales_config.find_one({
/app/backend/server.py.backup_pre_fase2a:1859:    await db.server_sucursales_config.update_one(
/app/backend/server.py.backup_pre_fase2a:1893:        result = await db.server_sucursales_config.update_one(
/app/backend/server.py.backup_pre_fase2a:1911:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:1953:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:2030:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:2226:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:2231:    query_template = await db.queries.find_one({
/app/backend/server.py.backup_pre_fase2a:2264:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:2431:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:3005:                        await db.inventario_diferencias_detalle.update_one(
/app/backend/server.py.backup_pre_fase2a:3601:                        await db.inventario_diferencias_detalle.update_one(
/app/backend/server.py.backup_pre_fase2a:3638:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:3871:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:4155:            cached = await db.inventario_diferencias_detalle.find_one(cache_key, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:4412:    Usa cache en MongoDB para evitar recalcular.
/app/backend/server.py.backup_pre_fase2a:4415:    server = await db.servers.find_one({"id": request.server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:4575:    await db.alerts.insert_one(doc)
/app/backend/server.py.backup_pre_fase2a:4581:    alerts = await db.alerts.find({"active": True}, {"_id": 0}).to_list(1000)
/app/backend/server.py.backup_pre_fase2a:4586:    await db.alerts.update_one({"id": alert_id}, {"$set": alert_data})
/app/backend/server.py.backup_pre_fase2a:4591:    await db.alerts.update_one({"id": alert_id}, {"$set": {"active": False}})
/app/backend/server.py.backup_pre_fase2a:4657:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:4723:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:4802:    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:5109:        server = await db.servers.find_one(query)
/app/backend/server.py.backup_pre_fase2a:5289:    servers = await db.servers.find(
/app/backend/server.py.backup_pre_fase2a:5300:    total_servers = await db.servers.count_documents({"active": True})
/app/backend/server.py.backup_pre_fase2a:5301:    total_users = await db.users.count_documents({"active": True})
/app/backend/server.py.backup_pre_fase2a:5302:    total_alerts = await db.alerts.count_documents({"active": True})
/app/backend/server.py.backup_pre_fase2a:5303:    servers_configured = await db.servers.count_documents({"active": True, "queries_configured": True})
/app/backend/server.py.backup_pre_fase2a:5375:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:5460:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:5531:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:5588:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:5627:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:5664:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:5715:    server = await db.servers.find_one({"id": request.server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:6126:    params = await db.parametros_compra.find_one({"server_id": server_id})
/app/backend/server.py.backup_pre_fase2a:6137:    # Excluir _id de MongoDB
/app/backend/server.py.backup_pre_fase2a:6151:    await db.parametros_compra.update_one(
/app/backend/server.py.backup_pre_fase2a:6194:    server = await db.servers.find_one({"id": request.server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:6309:    server = await db.servers.find_one({"id": request.server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:7014:    server = await db.servers.find_one({"id": request.server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:7191:    server = await db.servers.find_one({"id": request.server_id, "active": True}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:7306:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:7535:    server = await db.servers.find_one({"id": request.server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:7673:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:7727:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:7826:    status = await db.server_status.find_one({"server_id": server_id})
/app/backend/server.py.backup_pre_fase2a:7831:    await db.server_status.update_one(
/app/backend/server.py.backup_pre_fase2a:7870:    cache = await db.kpis_cache.find_one({
/app/backend/server.py.backup_pre_fase2a:7878:    await db.kpis_cache.update_one(
/app/backend/server.py.backup_pre_fase2a:7941:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:7981:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:8022:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:8069:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:8110:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:8156:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:8292:    # Guardar log en MongoDB
/app/backend/server.py.backup_pre_fase2a:8293:    await db.script_logs.insert_one({
/app/backend/server.py.backup_pre_fase2a:8388:    """Crea un nuevo informe de auditoría y lo guarda en MongoDB"""
/app/backend/server.py.backup_pre_fase2a:8442:        # Guardar en MongoDB
/app/backend/server.py.backup_pre_fase2a:8443:        result = await db.informes_auditoria.insert_one(informe_doc)
/app/backend/server.py.backup_pre_fase2a:8449:            "mongo_id": str(result.inserted_id)
/app/backend/server.py.backup_pre_fase2a:8484:        total = await db.informes_auditoria.count_documents(filtro)
/app/backend/server.py.backup_pre_fase2a:8488:        cursor = db.informes_auditoria.find(
/app/backend/server.py.backup_pre_fase2a:8490:            {"_id": 0}  # Excluir _id de MongoDB
/app/backend/server.py.backup_pre_fase2a:8534:        informe = await db.informes_auditoria.find_one(
/app/backend/server.py.backup_pre_fase2a:8573:        result = await db.informes_auditoria.update_one(
/app/backend/server.py.backup_pre_fase2a:8598:        informe = await db.informes_auditoria.find_one({"id": informe_id})
/app/backend/server.py.backup_pre_fase2a:8612:        # Eliminar de MongoDB
/app/backend/server.py.backup_pre_fase2a:8613:        await db.informes_auditoria.delete_one({"id": informe_id})
/app/backend/server.py.backup_pre_fase2a:8634:        informe = await db.informes_auditoria.find_one({"id": informe_id})
/app/backend/server.py.backup_pre_fase2a:8676:        await db.informes_auditoria.update_one(
/app/backend/server.py.backup_pre_fase2a:8710:        informe = await db.informes_auditoria.find_one({"id": informe_id})
/app/backend/server.py.backup_pre_fase2a:8729:        # Eliminar de MongoDB
/app/backend/server.py.backup_pre_fase2a:8730:        await db.informes_auditoria.update_one(
/app/backend/server.py.backup_pre_fase2a:8754:        result = await db.informes_auditoria.update_one(
/app/backend/server.py.backup_pre_fase2a:8793:        informe = await db.informes_auditoria.find_one({"id": informe_id}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:9121:    server = await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})
/app/backend/server.py.backup_pre_fase2a:9962:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:9979:    # Guardar en MongoDB
/app/backend/server.py.backup_pre_fase2a:9980:    result = await db.scripts_pendientes.insert_one({
/app/backend/server.py.backup_pre_fase2a:10003:    scripts = await db.scripts_pendientes.find(
/app/backend/server.py.backup_pre_fase2a:10025:    result = await db.scripts_pendientes.delete_one({"_id": ObjectId(script_id)})
/app/backend/server.py.backup_pre_fase2a:10057:    result = await db.scripts_pendientes.update_one(
/app/backend/server.py.backup_pre_fase2a:10087:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:10100:    # Si hay script_id, cargar el script de MongoDB
/app/backend/server.py.backup_pre_fase2a:10103:        script_doc = await db.scripts_pendientes.find_one({"_id": ObjectId(script_id)})
/app/backend/server.py.backup_pre_fase2a:10227:    await db.script_logs.insert_one({
/app/backend/server.py.backup_pre_fase2a:10244:        await db.scripts_pendientes.update_one(
/app/backend/server.py.backup_pre_fase2a:10601:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:10746:    Incluye consultas predefinidas y personalizadas (MongoDB).
/app/backend/server.py.backup_pre_fase2a:10766:    # Agregar consultas personalizadas desde MongoDB
/app/backend/server.py.backup_pre_fase2a:10773:    consultas_custom = await db.consultas_custom.find(filtro).to_list(500)
/app/backend/server.py.backup_pre_fase2a:10821:        consulta_custom = await db.consultas_custom.find_one({"id": consulta_id})
/app/backend/server.py.backup_pre_fase2a:10836:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:10920:# CRUD CONSULTAS PERSONALIZADAS (MongoDB)
/app/backend/server.py.backup_pre_fase2a:10925:    """Lista todas las consultas personalizadas guardadas en MongoDB"""
/app/backend/server.py.backup_pre_fase2a:10926:    consultas = await db.consultas_custom.find().to_list(1000)
/app/backend/server.py.backup_pre_fase2a:10962:    await db.consultas_custom.insert_one(consulta)
/app/backend/server.py.backup_pre_fase2a:10974:    consulta = await db.consultas_custom.find_one({"id": consulta_id})
/app/backend/server.py.backup_pre_fase2a:10989:    await db.consultas_custom.update_one({"id": consulta_id}, {"$set": update_data})
/app/backend/server.py.backup_pre_fase2a:11008:    consulta_custom = await db.consultas_custom.find_one({"id": consulta_id})
/app/backend/server.py.backup_pre_fase2a:11011:        await db.consultas_custom.update_one(
/app/backend/server.py.backup_pre_fase2a:11039:        await db.consultas_custom.insert_one(consulta_mod)
/app/backend/server.py.backup_pre_fase2a:11052:    result = await db.consultas_custom.delete_one({"id": consulta_id})
/app/backend/server.py.backup_pre_fase2a:11067:    # Buscar consulta en MongoDB
/app/backend/server.py.backup_pre_fase2a:11068:    consulta = await db.consultas_custom.find_one({"id": consulta_id})
/app/backend/server.py.backup_pre_fase2a:11073:    server = await db.servers.find_one({"id": server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:11154:    await db.informes_auditoria.insert_one(informe_doc)
/app/backend/server.py.backup_pre_fase2a:11194:    cursor = db.informes_auditoria.find(filtro, {"_id": 0, "datos_inventario": 0, "datos_comparativo": 0, "evidencias": 0}).sort("fecha_emision", -1)
/app/backend/server.py.backup_pre_fase2a:11218:    informe = await db.informes_auditoria.find_one({"id": informe_id}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:11237:    informe = await db.informes_auditoria.find_one({"id": informe_id})
/app/backend/server.py.backup_pre_fase2a:11251:    await db.informes_auditoria.update_one({"id": informe_id}, {"$set": update_data})
/app/backend/server.py.backup_pre_fase2a:11254:    informe_updated = await db.informes_auditoria.find_one({"id": informe_id}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:11267:    result = await db.informes_auditoria.delete_one({"id": informe_id})
/app/backend/server.py.backup_pre_fase2a:11286:    informe = await db.informes_auditoria.find_one({"id": informe_id})
/app/backend/server.py.backup_pre_fase2a:11323:    await db.informes_auditoria.update_one(
/app/backend/server.py.backup_pre_fase2a:11346:    result = await db.informes_auditoria.update_one(
/app/backend/server.py.backup_pre_fase2a:11367:    informe = await db.informes_auditoria.find_one({"id": informe_id})
/app/backend/server.py.backup_pre_fase2a:11394:    result = await db.informes_auditoria.update_one(
/app/backend/server.py.backup_pre_fase2a:11418:    informe = await db.informes_auditoria.find_one({"id": informe_id}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:11617:    await db.solicitudes_catalogos.update_one(
/app/backend/server.py.backup_pre_fase2a:11718:    server = await db.servers.find_one({"id": target_server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:11770:    server = await db.servers.find_one({"id": target_server_id, "active": True})
/app/backend/server.py.backup_pre_fase2a:11828:    # Obtener configuración personalizada de niveles desde MongoDB
/app/backend/server.py.backup_pre_fase2a:11829:    config = await db.config_catalogos.find_one({"tipo": "niveles_aprobacion"})
/app/backend/server.py.backup_pre_fase2a:11853:    await db.config_catalogos.update_one(
/app/backend/server.py.backup_pre_fase2a:11879:    permisos = await db.permisos_catalogos.find_one({"user_id": user_id})
/app/backend/server.py.backup_pre_fase2a:11906:    usuario = await db.users.find_one({"id": user_id})
/app/backend/server.py.backup_pre_fase2a:11911:    await db.permisos_catalogos.update_one(
/app/backend/server.py.backup_pre_fase2a:11942:    permisos = await db.permisos_catalogos.find_one({"user_id": user_id})
/app/backend/server.py.backup_pre_fase2a:11965:    permisos = await db.permisos_catalogos.find_one({"user_id": user_id})
/app/backend/server.py.backup_pre_fase2a:11981:    config = await db.config_catalogos.find_one({"tipo": "niveles_aprobacion"})
/app/backend/server.py.backup_pre_fase2a:12025:    await db.solicitudes_catalogos.insert_one(solicitud)
/app/backend/server.py.backup_pre_fase2a:12042:    await db.tareas_sistema.insert_one(tarea)
/app/backend/server.py.backup_pre_fase2a:12065:    solicitudes = await db.solicitudes_catalogos.find(filtro, {"_id": 0}).sort("fecha_solicitud", -1).to_list(100)
/app/backend/server.py.backup_pre_fase2a:12073:    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:12101:    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id})
/app/backend/server.py.backup_pre_fase2a:12169:        await db.solicitudes_catalogos.update_one(
/app/backend/server.py.backup_pre_fase2a:12207:        await db.tareas_sistema.insert_one(notificacion)
/app/backend/server.py.backup_pre_fase2a:12215:        await db.solicitudes_catalogos.update_one(
/app/backend/server.py.backup_pre_fase2a:12251:        await db.tareas_sistema.insert_one(tarea)
/app/backend/server.py.backup_pre_fase2a:12256:    await db.tareas_sistema.update_many(
/app/backend/server.py.backup_pre_fase2a:12272:    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id})
/app/backend/server.py.backup_pre_fase2a:12283:    await db.solicitudes_catalogos.update_one(
/app/backend/server.py.backup_pre_fase2a:12308:    await db.tareas_sistema.update_many(
/app/backend/server.py.backup_pre_fase2a:12327:    await db.tareas_sistema.insert_one(notificacion)
/app/backend/server.py.backup_pre_fase2a:12335:    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id})
/app/backend/server.py.backup_pre_fase2a:12358:    await db.solicitudes_catalogos.update_one(
/app/backend/server.py.backup_pre_fase2a:12400:    await db.tareas_sistema.insert_one(tarea)
/app/backend/server.py.backup_pre_fase2a:12408:    solicitud = await db.solicitudes_catalogos.find_one({"id": solicitud_id}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:12451:    tareas = await db.tareas_sistema.find(
/app/backend/server.py.backup_pre_fase2a:12462:    solicitudes_pendientes = await db.solicitudes_catalogos.count_documents({"estatus": "Pendiente"}) if user_role in ['Supervisor', 'Administrador'] else 0
/app/backend/server.py.backup_pre_fase2a:12492:        solicitudes = await db.solicitudes_catalogos.find(
/app/backend/server.py.backup_pre_fase2a:12521:        proveedores = await db.portal_proveedores.find(
/app/backend/server.py.backup_pre_fase2a:12569:        ciclos = await db.nomina_ciclos.find(
/app/backend/server.py.backup_pre_fase2a:12575:        config = await db.nomina_configuracion.find_one({}, {"_id": 0})
/app/backend/server.py.backup_pre_fase2a:12655:    await db.tareas_sistema.update_one(
/app/backend/server.py.backup_pre_fase2a:12669:    usuarios = await db.users.find(
/app/backend/server.py.backup_pre_fase2a:12676:        permisos = await db.permisos_catalogos.find_one({"user_id": u["id"]})
/app/backend/server.py.backup_pre_fase2a:12690:-- Base de datos: EDARSA HUB (Opcional - Las tareas se guardan en MongoDB)
/app/backend/server.py.backup_pre_fase2a:12694:-- El sistema principal usa MongoDB para las tareas
/app/backend/server.py.backup_pre_fase2a:12721:        "nota": "Este script es OPCIONAL. El sistema de tareas funciona con MongoDB. Use este script solo si desea mantener un log adicional en SQL Server."
/app/backend/server.py.backup_pre_fase2a:12754:    await db.nomina_ciclos.update_one(
/app/backend/server.py.backup_pre_fase2a:12795:    cursor = db.nomina_ciclos.find(filtro).sort("fecha_creacion", -1)
/app/backend/server.py.backup_pre_fase2a:12798:    # Limpiar _id de MongoDB
/app/backend/server.py.backup_pre_fase2a:12808:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
/app/backend/server.py.backup_pre_fase2a:12841:    ciclo_existente = await db.nomina_ciclos.find_one({
/app/backend/server.py.backup_pre_fase2a:12850:    config = await db.nomina_configuracion.find_one({"tipo": "general"})
/app/backend/server.py.backup_pre_fase2a:12886:    await db.nomina_ciclos.insert_one(ciclo)
/app/backend/server.py.backup_pre_fase2a:12901:    user = await db.users.find_one({"id": current_user.get("id")})
/app/backend/server.py.backup_pre_fase2a:12906:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
/app/backend/server.py.backup_pre_fase2a:12931:    config = await db.nomina_configuracion.find_one({"tipo": "general"})
/app/backend/server.py.backup_pre_fase2a:12957:    await db.nomina_ciclos.update_one(
/app/backend/server.py.backup_pre_fase2a:12992:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
/app/backend/server.py.backup_pre_fase2a:13011:    await db.nomina_ciclos.update_one(
/app/backend/server.py.backup_pre_fase2a:13039:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
/app/backend/server.py.backup_pre_fase2a:13043:    cursor = db.nomina_movimientos.find({"ciclo_id": ciclo_id}).sort("fecha_registro", -1)
/app/backend/server.py.backup_pre_fase2a:13056:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
/app/backend/server.py.backup_pre_fase2a:13101:    await db.nomina_movimientos.insert_one(movimiento)
/app/backend/server.py.backup_pre_fase2a:13104:    await db.nomina_ciclos.update_one(
/app/backend/server.py.backup_pre_fase2a:13115:    movimiento = await db.nomina_movimientos.find_one({"id": movimiento_id})
/app/backend/server.py.backup_pre_fase2a:13122:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
/app/backend/server.py.backup_pre_fase2a:13126:    await db.nomina_movimientos.delete_one({"id": movimiento_id})
/app/backend/server.py.backup_pre_fase2a:13129:    await db.nomina_ciclos.update_one(
/app/backend/server.py.backup_pre_fase2a:13140:    config = await db.nomina_configuracion.find_one({"tipo": "general"})
/app/backend/server.py.backup_pre_fase2a:13178:    await db.nomina_configuracion.update_one(
/app/backend/server.py.backup_pre_fase2a:13190:    cursor = db.nomina_kpis_puestos.find({})
/app/backend/server.py.backup_pre_fase2a:13232:    await db.nomina_kpis_puestos.update_one(
/app/backend/server.py.backup_pre_fase2a:13248:-- NOTA: Las tablas principales se manejan en MongoDB.
/app/backend/server.py.backup_pre_fase2a:13316:        CicloID NVARCHAR(50) NOT NULL, -- ID del ciclo en MongoDB
/app/backend/server.py.backup_pre_fase2a:13336:        "nota": "Este script es OPCIONAL. El sistema de nóminas funciona principalmente con MongoDB. Use estas tablas para integración con NomiPAQ o reportes SQL."
/app/backend/core/server_registry.py:9:2. MongoDB queda como fallback legacy temporal
/app/backend/core/server_registry.py:10:3. Todo fallback debe quedar marcado con config_origin = "MONGODB_LEGACY"
/app/backend/core/server_registry.py:214:    Garantiza paridad con el esquema de MongoDB.
/app/backend/core/server_registry.py:232:        'mongodb_id': str(row.get('mongodb_id', '')) if row.get('mongodb_id') else None,
/app/backend/core/server_registry.py:327:    Busca tanto por id como por mongodb_id para compatibilidad.
/app/backend/core/server_registry.py:337:        WHERE (CAST(id AS VARCHAR(50)) = '{safe_id}' OR mongodb_id = '{safe_id}')
/app/backend/core/server_registry.py:363:# LECTURA DESDE MONGODB (FALLBACK LEGACY)
/app/backend/core/server_registry.py:366:def _mongo_row_to_server_dict(row: Dict) -> Dict:
/app/backend/core/server_registry.py:368:    Convierte un documento MongoDB al formato normalizado.
/app/backend/core/server_registry.py:376:        'config_origin': 'MONGODB_LEGACY',
/app/backend/core/server_registry.py:377:        'warnings': ['Servidor obtenido desde MongoDB legacy; migrar a EDARSAHUB SQL.']
/app/backend/core/server_registry.py:380:    # Asegurar que no haya _id de MongoDB
/app/backend/core/server_registry.py:386:async def _get_servers_from_mongo(
/app/backend/core/server_registry.py:393:    Obtiene servidores desde MongoDB (fallback legacy).
/app/backend/core/server_registry.py:407:        cursor = db.servers.find(query, {'_id': 0})
/app/backend/core/server_registry.py:418:        normalized = [_mongo_row_to_server_dict(s) for s in servers]
/app/backend/core/server_registry.py:420:        logger.warning(f"[SERVER_REGISTRY][MONGODB_FALLBACK_USED] Obtenidos {len(normalized)} servidores desde MongoDB legacy")
/app/backend/core/server_registry.py:424:        logger.error(f"[SERVER_REGISTRY][MONGODB_ERROR] Error obteniendo servidores desde MongoDB: {e}")
/app/backend/core/server_registry.py:428:async def _get_server_by_id_from_mongo(db, server_id: str) -> Optional[Dict]:
/app/backend/core/server_registry.py:430:    Obtiene un servidor específico por ID desde MongoDB (fallback legacy).
/app/backend/core/server_registry.py:433:        server = await db.servers.find_one(
/app/backend/core/server_registry.py:439:            logger.warning(f"[SERVER_REGISTRY][MONGODB_FALLBACK_USED] Servidor {server_id} obtenido desde MongoDB legacy")
/app/backend/core/server_registry.py:440:            return _mongo_row_to_server_dict(server)
/app/backend/core/server_registry.py:445:        logger.error(f"[SERVER_REGISTRY][MONGODB_ERROR] Error buscando servidor {server_id}: {e}")
/app/backend/core/server_registry.py:457:    allow_mongo_fallback: bool = True,
/app/backend/core/server_registry.py:465:    2. MongoDB (si allow_mongo_fallback=True y no se encontró en SQL)
/app/backend/core/server_registry.py:469:        db: Conexión a MongoDB (requerido si allow_mongo_fallback=True)
/app/backend/core/server_registry.py:471:        allow_mongo_fallback: Permitir fallback a MongoDB
/app/backend/core/server_registry.py:483:    # Fallback a MongoDB
/app/backend/core/server_registry.py:484:    if not server and allow_mongo_fallback and db is not None:
/app/backend/core/server_registry.py:485:        server = await _get_server_by_id_from_mongo(db, server_id)
/app/backend/core/server_registry.py:498:    allow_mongo_fallback: bool = True,
/app/backend/core/server_registry.py:509:    2. MongoDB (si allow_mongo_fallback=True y SQL devuelve vacío)
/app/backend/core/server_registry.py:512:        db: Conexión a MongoDB (requerido si allow_mongo_fallback=True)
/app/backend/core/server_registry.py:515:        allow_mongo_fallback: Permitir fallback a MongoDB
/app/backend/core/server_registry.py:534:    # Fallback a MongoDB si SQL está vacío
/app/backend/core/server_registry.py:535:    if not servers and allow_mongo_fallback and db is not None:
/app/backend/core/server_registry.py:536:        servers = await _get_servers_from_mongo(
/app/backend/core/server_registry.py:577:    filtered = [s for s in servers if s.get('id') in allowed_ids or s.get('mongodb_id') in allowed_ids]
/app/backend/core/server_registry.py:636:            if server.get('id') not in allowed and server.get('mongodb_id') not in allowed:
/app/backend/core/server_registry.py:709:        db: Conexión MongoDB (opcional)
/app/backend/core/server_registry.py:727:            if server.get('id') not in allowed and server.get('mongodb_id') not in allowed:
/app/backend/core/server_registry.py:753:    allow_mongo_fallback: bool = True
/app/backend/core/server_registry.py:760:    2. MongoDB collection `server_sucursales_config` (fallback)
/app/backend/core/server_registry.py:764:        db: Conexión a MongoDB
/app/backend/core/server_registry.py:766:        allow_mongo_fallback: Permitir fallback a MongoDB
/app/backend/core/server_registry.py:782:    # Fallback a MongoDB si no hay sucursales en SQL
/app/backend/core/server_registry.py:783:    if not sucursales and allow_mongo_fallback and db is not None:
/app/backend/core/server_registry.py:786:            cursor = db.server_sucursales_config.find(
/app/backend/core/server_registry.py:793:                # Fallback al campo sucursales del servidor en MongoDB
/app/backend/core/server_registry.py:794:                server_mongo = await _get_server_by_id_from_mongo(db, server_id)
/app/backend/core/server_registry.py:795:                if server_mongo and server_mongo.get('sucursales'):
/app/backend/core/server_registry.py:796:                    sucursales = server_mongo['sucursales'] if isinstance(server_mongo['sucursales'], list) else []
/app/backend/core/server_registry.py:799:                source = 'MONGODB_LEGACY'
/app/backend/core/server_registry.py:800:                logger.warning(f"[SERVER_REGISTRY][SUCURSALES][MONGODB_FALLBACK] {len(sucursales)} sucursales para servidor {server_id}")
/app/backend/core/server_registry.py:802:            logger.error(f"[SERVER_REGISTRY][SUCURSALES][MONGODB_ERROR] Error obteniendo sucursales: {e}")
/app/backend/core/server_registry.py:834:        source: Fuente del registro ("EDARSAHUB_SQL" o "MONGODB_LEGACY")
/app/backend/core/server_registry.py:849:        'mongodb_id': record.get('mongodb_id'),  # Mapeo a MongoDB si existe
/app/backend/core/server_registry.py:923:    'sync_server_to_mongo',
/app/backend/core/server_registry.py:1028:    sync_mongo: bool = True
/app/backend/core/server_registry.py:1031:    Crea un servidor en EDARSAHUB SQL primero, luego sincroniza a MongoDB.
/app/backend/core/server_registry.py:1033:    FASE 3B.1: SQL-first con sync a MongoDB como espejo legacy.
/app/backend/core/server_registry.py:1037:        db: Conexión MongoDB (para sync)
/app/backend/core/server_registry.py:1039:        sync_mongo: Si True, sincroniza a MongoDB después
/app/backend/core/server_registry.py:1075:        created_at, updated_at, mongodb_id
/app/backend/core/server_registry.py:1109:        server_id  # mongodb_id será el mismo inicialmente
/app/backend/core/server_registry.py:1126:    # Sincronizar a MongoDB
/app/backend/core/server_registry.py:1130:    if sync_mongo and db is not None:
/app/backend/core/server_registry.py:1132:            mongo_doc = {
/app/backend/core/server_registry.py:1150:            await db.servers.insert_one(mongo_doc)
/app/backend/core/server_registry.py:1151:            logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado a MongoDB: {server_id}")
/app/backend/core/server_registry.py:1154:            sync_warnings.append(f"SQL exitoso pero MongoDB falló: {str(e)}")
/app/backend/core/server_registry.py:1155:            logger.warning(f"[SERVER_REGISTRY][SYNC_MONGO_ERROR] {e}")
/app/backend/core/server_registry.py:1177:    sync_mongo: bool = True
/app/backend/core/server_registry.py:1180:    Actualiza un servidor en EDARSAHUB SQL primero, luego sincroniza a MongoDB.
/app/backend/core/server_registry.py:1182:    FASE 3B.1: SQL-first con sync a MongoDB como espejo legacy.
/app/backend/core/server_registry.py:1185:        server_id: ID del servidor (SQL id o mongodb_id)
/app/backend/core/server_registry.py:1187:        db: Conexión MongoDB (para sync y para obtener password existente)
/app/backend/core/server_registry.py:1189:        sync_mongo: Si True, sincroniza a MongoDB después
/app/backend/core/server_registry.py:1311:    update_values.append(server_id)  # Para mongodb_id fallback
/app/backend/core/server_registry.py:1316:    WHERE CAST(id AS VARCHAR(50)) = %s OR mongodb_id = %s
/app/backend/core/server_registry.py:1331:    # Sincronizar a MongoDB
/app/backend/core/server_registry.py:1335:    if sync_mongo and db is not None:
/app/backend/core/server_registry.py:1337:            mongo_update = {k: v for k, v in payload.items() if k not in ['_validation_warnings'] and v is not None}
/app/backend/core/server_registry.py:1338:            mongo_update['updated_at'] = now
/app/backend/core/server_registry.py:1341:            if 'nombre' in mongo_update:
/app/backend/core/server_registry.py:1342:                mongo_update['name'] = mongo_update.pop('nombre')
/app/backend/core/server_registry.py:1343:            if 'database_name' in mongo_update:
/app/backend/core/server_registry.py:1344:                mongo_update['database'] = mongo_update.pop('database_name')
/app/backend/core/server_registry.py:1346:            await db.servers.update_one(
/app/backend/core/server_registry.py:1348:                {'$set': mongo_update}
/app/backend/core/server_registry.py:1350:            logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado a MongoDB: {server_id}")
/app/backend/core/server_registry.py:1353:            sync_warnings.append(f"SQL actualizado pero MongoDB falló: {str(e)}")
/app/backend/core/server_registry.py:1354:            logger.warning(f"[SERVER_REGISTRY][SYNC_MONGO_ERROR] {e}")
/app/backend/core/server_registry.py:1370:    sync_mongo: bool = True,
/app/backend/core/server_registry.py:1374:    Desactiva (soft delete) un servidor en EDARSAHUB SQL, luego sincroniza a MongoDB.
/app/backend/core/server_registry.py:1376:    FASE 3B.1: SQL-first con sync a MongoDB como espejo legacy.
/app/backend/core/server_registry.py:1381:        db: Conexión MongoDB (para sync)
/app/backend/core/server_registry.py:1383:        sync_mongo: Si True, sincroniza a MongoDB después
/app/backend/core/server_registry.py:1415:        WHERE CAST(id AS VARCHAR(50)) = %s OR mongodb_id = %s
/app/backend/core/server_registry.py:1421:        WHERE CAST(id AS VARCHAR(50)) = %s OR mongodb_id = %s
/app/backend/core/server_registry.py:1437:    # Sincronizar a MongoDB
/app/backend/core/server_registry.py:1441:    if sync_mongo and db is not None:
/app/backend/core/server_registry.py:1444:                await db.servers.update_one(
/app/backend/core/server_registry.py:1449:                await db.servers.delete_one({'id': server_id})
/app/backend/core/server_registry.py:1450:            logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado a MongoDB: {server_id}")
/app/backend/core/server_registry.py:1453:            sync_warnings.append(f"SQL actualizado pero MongoDB falló: {str(e)}")
/app/backend/core/server_registry.py:1454:            logger.warning(f"[SERVER_REGISTRY][SYNC_MONGO_ERROR] {e}")
/app/backend/core/server_registry.py:1467:async def sync_server_to_mongo(sql_server_id: str, db=None) -> Dict:
/app/backend/core/server_registry.py:1469:    Sincroniza un servidor específico desde SQL hacia MongoDB.
/app/backend/core/server_registry.py:1475:        db: Conexión MongoDB
/app/backend/core/server_registry.py:1483:            'error': 'Conexión MongoDB no disponible',
/app/backend/core/server_registry.py:1496:    logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_START] Sincronizando servidor: {sql_server_id}")
/app/backend/core/server_registry.py:1499:        # Construir documento MongoDB
/app/backend/core/server_registry.py:1500:        mongo_doc = {
/app/backend/core/server_registry.py:1519:        # Upsert en MongoDB
/app/backend/core/server_registry.py:1520:        await db.servers.update_one(
/app/backend/core/server_registry.py:1522:            {'$set': mongo_doc},
/app/backend/core/server_registry.py:1526:        logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado: {sql_server_id}")
/app/backend/core/server_registry.py:1532:            'message': 'Servidor sincronizado a MongoDB'
/app/backend/core/server_registry.py:1536:        logger.error(f"[SERVER_REGISTRY][SYNC_MONGO_ERROR] {e}")
/app/backend/core/server_registry.py:1548:def build_legacy_mongo_server_document(sql_record: Dict) -> Dict:
/app/backend/core/server_registry.py:1550:    Construye un documento MongoDB legacy a partir de un registro SQL.
/app/backend/core/server_registry.py:1552:    Usado para sincronizar servidores de SQL hacia MongoDB manteniendo
/app/backend/core/server_registry.py:1553:    compatibilidad con el esquema legacy de MongoDB.
/app/backend/core/server_registry.py:1559:        Dict compatible con colección MongoDB servers
/app/backend/core/server_registry.py:1617:        'mongodb_id': sql_record.get('mongodb_id'),
/app/backend/core/server_registry.py:1668:async def reconcile_sql_mongo_servers(db=None, dry_run: bool = True) -> Dict:
/app/backend/core/server_registry.py:1670:    Reconcilia servidores entre SQL y MongoDB.
/app/backend/core/server_registry.py:1673:    sincroniza MongoDB para que sea espejo de SQL.
/app/backend/core/server_registry.py:1676:        db: Conexión MongoDB
/app/backend/core/server_registry.py:1688:        'mongo_count': 0,
/app/backend/core/server_registry.py:1691:        'mongo_only': [],
/app/backend/core/server_registry.py:1703:        # Crear índice por ID y mongodb_id
/app/backend/core/server_registry.py:1705:        sql_by_mongodb_id = {s['mongodb_id']: s for s in sql_servers if s.get('mongodb_id')}
/app/backend/core/server_registry.py:1707:        # Obtener servidores de MongoDB
/app/backend/core/server_registry.py:1709:            report['warnings'].append('No se puede verificar MongoDB sin conexión')
/app/backend/core/server_registry.py:1712:        mongo_cursor = db.servers.find({}, {'_id': 0})
/app/backend/core/server_registry.py:1713:        mongo_servers = await mongo_cursor.to_list(1000)
/app/backend/core/server_registry.py:1714:        report['mongo_count'] = len(mongo_servers)
/app/backend/core/server_registry.py:1717:        mongo_by_id = {s['id']: s for s in mongo_servers}
/app/backend/core/server_registry.py:1719:        # Comparar: SQL que no están en Mongo
/app/backend/core/server_registry.py:1721:            mongo_server = mongo_by_id.get(sql_id) or mongo_by_id.get(sql_server.get('mongodb_id'))
/app/backend/core/server_registry.py:1723:            if not mongo_server:
/app/backend/core/server_registry.py:1733:                        mongo_doc = build_legacy_mongo_server_document(sql_server)
/app/backend/core/server_registry.py:1734:                        await db.servers.insert_one(mongo_doc)
/app/backend/core/server_registry.py:1736:                        logger.info(f"[SERVER_REGISTRY][RECONCILIATION_SYNC] Creado en MongoDB: {sql_id}")
/app/backend/core/server_registry.py:1744:                if sql_server.get('name') != mongo_server.get('name'):
/app/backend/core/server_registry.py:1745:                    diffs.append(f"name: SQL='{sql_server.get('name')}' vs Mongo='{mongo_server.get('name')}'")
/app/backend/core/server_registry.py:1746:                if sql_server.get('system_type') != mongo_server.get('system_type'):
/app/backend/core/server_registry.py:1747:                    diffs.append(f"system_type: SQL='{sql_server.get('system_type')}' vs Mongo='{mongo_server.get('system_type')}'")
/app/backend/core/server_registry.py:1748:                if sql_server.get('active') != mongo_server.get('active'):
/app/backend/core/server_registry.py:1749:                    diffs.append(f"active: SQL={sql_server.get('active')} vs Mongo={mongo_server.get('active')}")
/app/backend/core/server_registry.py:1761:                            mongo_doc = build_legacy_mongo_server_document(sql_server)
/app/backend/core/server_registry.py:1762:                            await db.servers.update_one({'id': sql_id}, {'$set': mongo_doc})
/app/backend/core/server_registry.py:1764:                            logger.info(f"[SERVER_REGISTRY][RECONCILIATION_SYNC] Actualizado en MongoDB: {sql_id}")
/app/backend/core/server_registry.py:1768:        # Comparar: Mongo que no están en SQL
/app/backend/core/server_registry.py:1769:        for mongo_id, mongo_server in mongo_by_id.items():
/app/backend/core/server_registry.py:1770:            if mongo_id not in sql_by_id and mongo_id not in sql_by_mongodb_id:
/app/backend/core/server_registry.py:1771:                report['mongo_only'].append({
/app/backend/core/server_registry.py:1772:                    'id': mongo_id,
/app/backend/core/server_registry.py:1773:                    'name': mongo_server.get('name', 'N/A'),
/app/backend/core/server_registry.py:1774:                    'system_type': mongo_server.get('system_type', 'N/A')
/app/backend/core/server_registry.py:1776:                report['warnings'].append(f"Servidor {mongo_id} existe en MongoDB pero no en SQL")
/app/backend/core/server_registry.py:1781:        elif report['sql_only'] or report['mongo_only'] or report['diffs']:
/app/backend/core/server_registry.py:1784:        logger.info(f"[SERVER_REGISTRY][RECONCILIATION_COMPLETE] matched={report['matched']}, sql_only={len(report['sql_only'])}, mongo_only={len(report['mongo_only'])}, diffs={len(report['diffs'])}")
/app/backend/core/server_registry.py:1797:# MÁXIMA: EDARSAHUB es el cerebro del sistema. No usar MongoDB.
/app/backend/core/server_registry.py:1846:    FASE M1: Fuente única EDARSAHUB, sin MongoDB.
/app/backend/core/server_registry.py:1913:    FASE M1: EDARSAHUB es el cerebro del sistema. No usa MongoDB.
/app/backend/core/server_registry.py:2346:    NO FUENTE: MongoDB db.servers
/app/backend/core/server_registry.py:2356:        - id, mongodb_id, name, system_type
/app/backend/core/server_registry.py:2369:        'mongodb_id': server.get('mongodb_id'),
/app/backend/core/server_registry.py:2402:    'sync_server_to_mongo',
/app/backend/core/server_registry.py:2405:    'build_legacy_mongo_server_document',
/app/backend/core/server_registry.py:2407:    'reconcile_sql_mongo_servers',
/app/backend/core/connection_resolver.py:274:        """Obtiene conexión a MongoDB"""
/app/backend/core/connection_resolver.py:277:                from pymongo import MongoClient
/app/backend/core/connection_resolver.py:279:                mongo_url = os.environ.get('MONGO_URL')
/app/backend/core/connection_resolver.py:280:                client = MongoClient(mongo_url)
/app/backend/core/connection_resolver.py:283:                logger.error(f"[ConnectionResolver] Error conectando a MongoDB: {e}")
/app/backend/core/connection_resolver.py:288:        """Obtiene configuración de servidor desde MongoDB (menú Servidores SQL)"""
/app/backend/core/connection_resolver.py:291:            server = db.servers.find_one(
/app/backend/core/connection_resolver.py:301:        """Obtiene configuración de API local desde MongoDB"""
/app/backend/core/connection_resolver.py:304:            api_config = db.apis_locales.find_one(
/app/backend/core/pool.py:605:# MOTOR CENTRAL SQL - execute_hub_query (Mayo 2026)
/app/backend/core/pool.py:610:    Motor central: Lee de SQL Server (EDARSAHUB) y devuelve el formato que el frontend espera.
/app/backend/core/pool.py:611:    NO requiere lógica de MongoDB - reemplazo directo.
/app/backend/core/pool.py:621:        # Reemplaza: mongo_db.servers.find()
/app/backend/core/pool.py:624:        # Reemplaza: mongo_db.ventas.find({"sucursal_id": id})
/app/backend/core/pool.py:654:    Equivalente a mongo_db.collection.find_one()
/app/backend/core/pool.py:703:    # Motor central SQL (Mayo 2026)
/app/backend/core/__init__.py:6:# - db.py: Conexiones SQL Server, execute_sql_query()
/app/backend/core/__init__.py:55:    MONGODB_COLLECTIONS,
/app/backend/core/__init__.py:56:    MONGODB_INDEXES,
/app/backend/core/source_resolver.py:96:        source_type: Tipo de fuente (MPRO, SoftRestaurant, MongoDB, API)
/app/backend/core/source_resolver.py:141:        """Serializa a diccionario para JSON/MongoDB."""
/app/backend/core/auditoria.py:7:guardan temporalmente en MongoDB como fallback y se sincronizan después.
/app/backend/core/auditoria.py:185:    def to_mongo_doc(self) -> dict:
/app/backend/core/auditoria.py:186:        """Retorna documento para MongoDB."""
/app/backend/core/auditoria.py:200:    Fallback a MongoDB si SQL no está disponible.
/app/backend/core/auditoria.py:219:        self._mongo_db = None
/app/backend/core/auditoria.py:221:    async def _get_mongo_db(self):
/app/backend/core/auditoria.py:222:        """Obtiene conexión a MongoDB para fallback"""
/app/backend/core/auditoria.py:223:        if self._mongo_db is None:
/app/backend/core/auditoria.py:225:                from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/core/auditoria.py:226:                mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/core/auditoria.py:227:                client = AsyncIOMotorClient(mongo_url)
/app/backend/core/auditoria.py:229:                self._mongo_db = client[db_name]
/app/backend/core/auditoria.py:231:                logger.error(f"Error conectando a MongoDB: {e}")
/app/backend/core/auditoria.py:233:        return self._mongo_db
/app/backend/core/auditoria.py:402:    async def _guardar_mongo(self, evento: EventoAuditoria) -> bool:
/app/backend/core/auditoria.py:403:        """Guarda en MongoDB como fallback."""
/app/backend/core/auditoria.py:404:        db = await self._get_mongo_db()
/app/backend/core/auditoria.py:409:            await db.auditoria_financiera.insert_one(evento.to_mongo_doc())
/app/backend/core/auditoria.py:410:            logger.debug(f"[AUDIT-MONGO] {evento.modulo}/{evento.entidad}/{evento.accion}")
/app/backend/core/auditoria.py:413:            logger.error(f"Error escribiendo auditoría a MongoDB: {e}")
/app/backend/core/auditoria.py:430:            if await self._guardar_mongo(evento):
/app/backend/core/auditoria.py:487:            db = await self._get_mongo_db()
/app/backend/core/auditoria.py:489:                cursor = db.auditoria_financiera.find(
/app/backend/core/auditoria.py:507:            db = await self._get_mongo_db()
/app/backend/core/auditoria.py:515:                cursor = db.auditoria_financiera.find(
/app/backend/core/empresa_resolver.py:9:NO CONSULTA: MongoDB
/app/backend/core/unidades_registry.py:16:- NO usar MongoDB como fuente funcional
/app/backend/core/security.py:14:- La conexión a MongoDB se inyecta vía init_security()
/app/backend/core/security.py:56:# Valor por defecto: false (MongoDB sigue siendo la fuente productiva)
/app/backend/core/security.py:61:# INYECCIÓN DE DEPENDENCIA: MongoDB
/app/backend/core/security.py:63:# La conexión a MongoDB se inyecta desde server.py para evitar imports circulares
/app/backend/core/security.py:71:    Inicializa el módulo de seguridad con la conexión a MongoDB.
/app/backend/core/security.py:75:        database: Instancia de AsyncIOMotorDatabase o None para usar stub
/app/backend/core/security.py:80:        from core.mongo_stub import get_stub_database
/app/backend/core/security.py:85:        logging.info("[SECURITY] Módulo de seguridad inicializado con conexión a MongoDB")
/app/backend/core/security.py:89:    """Obtiene la conexión a MongoDB inyectada."""
/app/backend/core/security.py:262:    FASE 2-G: SQL-only (sin fallback MongoDB).
/app/backend/core/security.py:283:    # FASE 2-G: SQL-only (sin fallback MongoDB)
/app/backend/core/security.py:309:    FASE 2-G: Obtiene usuario SOLO de EDARSAHUB SQL (sin fallback MongoDB).
/app/backend/core/security.py:436:    # FASE 2-G: SQL-only (sin fallback MongoDB)
/app/backend/core/security.py:486:        Lista de empresa_ids permitidos (UUIDs MongoDB para compatibilidad)
/app/backend/core/security.py:500:                SELECT m.EmpresaMongoUUID
/app/backend/core/security.py:502:                JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
/app/backend/core/security.py:547:        # Construir IN clause para empresas (UUIDs MongoDB)
/app/backend/core/security.py:554:            JOIN Sistema_EmpresasMongoMap em ON s.EmpresaID = em.EmpresaID_SQL
/app/backend/core/security.py:555:            WHERE em.EmpresaMongoUUID IN ({placeholders})
/app/backend/core/security.py:730:    'compare_user_mongo_vs_sql_passive',
/app/backend/core/security.py:732:    # FASE 2-G: SQL-Only (sin fallback MongoDB)
/app/backend/core/security.py:743:# - MongoDB sigue siendo la fuente de autenticación
/app/backend/core/security.py:767:def compare_user_mongo_vs_sql_passive(user_mongo: Dict[str, Any], email: str) -> Dict[str, Any]:
/app/backend/core/security.py:769:    FASE 2-D.1: Comparación pasiva MongoDB vs SQL.
/app/backend/core/security.py:775:        user_mongo: Usuario obtenido de MongoDB (actual productivo)
/app/backend/core/security.py:785:        'auth_source': 'MONGODB_CURRENT',
/app/backend/core/security.py:789:        'mongo': _safe_user_for_log(user_mongo, 'MONGODB'),
/app/backend/core/security.py:808:        # ID (PublicUUID vs MongoDB id)
/app/backend/core/security.py:809:        mongo_id = user_mongo.get('id')
/app/backend/core/security.py:811:        if mongo_id != sql_id:
/app/backend/core/security.py:812:            differences.append(f'id: mongo={mongo_id} vs sql={sql_id}')
/app/backend/core/security.py:815:        mongo_role = user_mongo.get('role', user_mongo.get('rol'))
/app/backend/core/security.py:817:        if mongo_role != sql_role:
/app/backend/core/security.py:818:            differences.append(f'role: mongo={mongo_role} vs sql={sql_role}')
/app/backend/core/security.py:821:        mongo_active = user_mongo.get('active', user_mongo.get('activo', False))
/app/backend/core/security.py:823:        if bool(mongo_active) != bool(sql_active):
/app/backend/core/security.py:824:            differences.append(f'active: mongo={mongo_active} vs sql={sql_active}')
/app/backend/core/security.py:827:        mongo_empresas = set(user_mongo.get('empresas_permitidas', []))
/app/backend/core/security.py:829:        if mongo_empresas != sql_empresas:
/app/backend/core/security.py:830:            only_mongo = len(mongo_empresas - sql_empresas)
/app/backend/core/security.py:831:            only_sql = len(sql_empresas - mongo_empresas)
/app/backend/core/security.py:832:            if only_mongo > 0:
/app/backend/core/security.py:833:                differences.append(f'empresas: {only_mongo} solo en mongo')
/app/backend/core/security.py:838:        mongo_default = user_mongo.get('empresa_default_id')
/app/backend/core/security.py:840:        if mongo_default != sql_default:
/app/backend/core/security.py:841:            differences.append(f'empresa_default: mongo={mongo_default} vs sql={sql_default}')
/app/backend/core/security.py:844:        mongo_has_hash = bool(user_mongo.get('password'))
/app/backend/core/security.py:846:        if mongo_has_hash != sql_has_hash:
/app/backend/core/security.py:847:            differences.append(f'has_password: mongo={mongo_has_hash} vs sql={sql_has_hash}')
/app/backend/core/security.py:860:def log_auth_preflight_status(user_mongo: Dict[str, Any], email: str) -> None:
/app/backend/core/security.py:870:        user_mongo: Usuario de MongoDB
/app/backend/core/security.py:876:            comparison = compare_user_mongo_vs_sql_passive(user_mongo, email)
/app/backend/core/rbac_helper.py:8:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/core/rbac_helper.py:11:# Conexión a MongoDB (reutiliza la existente del entorno)
/app/backend/core/rbac_helper.py:17:    """Obtiene conexión a MongoDB de forma lazy."""
/app/backend/core/rbac_helper.py:20:        _client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
/app/backend/core/rbac_helper.py:73:            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
/app/backend/core/rbac_helper.py:80:        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
/app/backend/core/scheduler/job_logger.py:43:    NOTA: Con StubDatabase, el collection será un StubCollection que retorna vacío.
/app/backend/core/scheduler/job_logger.py:46:    COLLECTION_NAME = "scheduler_job_log"
/app/backend/core/scheduler/job_logger.py:51:        self._is_stub = db is not None and hasattr(db, '_collections') and db.__class__.__name__ == 'StubDatabase'
/app/backend/core/scheduler/job_logger.py:54:            self.collection = db[self.COLLECTION_NAME]
/app/backend/core/scheduler/job_logger.py:58:                logger.info("[JOB_LOGGER] Inicializado con MongoDB")
/app/backend/core/scheduler/job_logger.py:60:            self.collection = None
/app/backend/core/scheduler/job_logger.py:81:        # MongoDB ELIMINADO - Solo persistir si db está disponible
/app/backend/core/scheduler/job_logger.py:82:        if self.collection is not None:
/app/backend/core/scheduler/job_logger.py:83:            await self.collection.insert_one(log_entry.model_dump())
/app/backend/core/scheduler/job_logger.py:122:        # MongoDB ELIMINADO - Solo persistir si db está disponible
/app/backend/core/scheduler/job_logger.py:123:        if self.collection is not None:
/app/backend/core/scheduler/job_logger.py:124:            await self.collection.update_one(
/app/backend/core/scheduler/job_logger.py:157:        # MongoDB ELIMINADO - Solo persistir si db está disponible
/app/backend/core/scheduler/job_logger.py:158:        if self.collection is not None:
/app/backend/core/scheduler/job_logger.py:159:            await self.collection.insert_one(log_entry.model_dump())
/app/backend/core/scheduler/job_logger.py:174:        # MongoDB ELIMINADO - Retornar lista vacía si no hay db
/app/backend/core/scheduler/job_logger.py:175:        if self.collection is None:
/app/backend/core/scheduler/job_logger.py:186:        cursor = self.collection.find(
/app/backend/core/scheduler/job_logger.py:194:        # MongoDB ELIMINADO - Retornar None si no hay db
/app/backend/core/scheduler/job_logger.py:195:        if self.collection is None:
/app/backend/core/scheduler/job_logger.py:197:        return await self.collection.find_one(
/app/backend/core/scheduler/job_logger.py:207:        # MongoDB ELIMINADO - Retornar stats vacío si no hay db
/app/backend/core/scheduler/job_logger.py:208:        if self.collection is None:
/app/backend/core/scheduler/job_logger.py:231:        cursor = self.collection.aggregate(pipeline)
/app/backend/core/scheduler/job_logger.py:260:        # MongoDB ELIMINADO - Retornar 0 si no hay db
/app/backend/core/scheduler/job_logger.py:261:        if self.collection is None:
/app/backend/core/scheduler/job_logger.py:265:        result = await self.collection.delete_many({
/app/backend/core/scheduler/job_logger.py:274:        # MongoDB ELIMINADO - No hacer nada si no hay db
/app/backend/core/scheduler/job_logger.py:275:        if self.collection is None:
/app/backend/core/scheduler/job_logger.py:279:            await self.collection.create_index([("job_name", 1), ("started_at", -1)])
/app/backend/core/scheduler/job_logger.py:284:            await self.collection.create_index("status")
/app/backend/core/scheduler/job_logger.py:291:            await self.collection.drop_index("started_at_1")
/app/backend/core/scheduler/job_logger.py:296:            await self.collection.create_index(
/app/backend/core/scheduler/__init__.py:7:- Procesamiento de motor SLA
/app/backend/core/scheduler/__init__.py:13:- Locks distribuidos vía MongoDB
/app/backend/core/scheduler/scheduler_manager.py:75:            db: Conexión MongoDB o StubDatabase (MongoDB ELIMINADO)
/app/backend/core/scheduler/scheduler_manager.py:79:            from core.mongo_stub import get_stub_database
/app/backend/core/scheduler/scheduler_manager.py:94:        is_stub = hasattr(db, '_collections') and db.__class__.__name__ == 'StubDatabase'
/app/backend/core/scheduler/scheduler_manager.py:96:        # NOTA: MongoDB ELIMINADO - Scheduler opera con StubDatabase
/app/backend/core/scheduler/scheduler_manager.py:98:            logger.info("[SCHEDULER] Inicializando con StubDatabase - MongoDB ELIMINADO")
/app/backend/core/scheduler/scheduler_manager.py:1373:    NOTA: MongoDB ELIMINADO - Siempre usa StubDatabase.
/app/backend/core/scheduler/scheduler_manager.py:1379:        from core.mongo_stub import get_stub_database
/app/backend/core/scheduler/scheduler_manager.py:1396:    NOTA: MongoDB ELIMINADO - Acepta db=None para modo SQL-only.
/app/backend/core/scheduler/sql_repository.py:4:Funciones SQL para los jobs del scheduler (reemplazo de MongoDB).
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:61:    COMPRAS-MONGO-001-F2: Migrado de MongoDB a SQL Server (Mayo 2026)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:71:    # Colecciones MongoDB removidas - ahora usa SQL
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:72:    # COLLECTION_PROCESADOS = "pedidos_procesados_automatizacion"  # -> Scheduler_PedidosProcesados
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:73:    # COLLECTION_TAREAS = "tareas_operativas_compras"              # -> Compras_Eventos_Pendientes  
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:74:    # COLLECTION_BITACORA = "auditoria_compras_bitacora"           # -> Scheduler_BitacoraJobs
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:80:            from core.mongo_stub import get_stub_database
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:87:        self._use_sql = True  # Flag para usar SQL en lugar de MongoDB
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:93:        return hasattr(self.db, '_collections') and self.db.__class__.__name__ == 'StubDatabase'
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:583:        COMPRAS-MONGO-001-F2: Migrado a SQL Server.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:602:        COMPRAS-MONGO-001-F2: Migrado a SQL Server.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:786:        NOTA: Esta función verificaba inventarios en MongoDB.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:793:        # MongoDB ELIMINADO - Por ahora siempre retorna True
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:795:        logger.debug("[PEDIDOS_DETECTOR] _inventario_valido: Retornando True (MongoDB eliminado)")
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:819:        COMPRAS-MONGO-001-F2: Migrado a SQL Server.
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:919:        COMPRAS-MONGO-001-F2: Migrado a SQL Server (Scheduler_BitacoraJobs).
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:944:        db: Conexión a MongoDB (async)
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:58:            db: Conexión MongoDB (IGNORADA - usamos SQL directo)
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:193:            # Usar MongoServidorUUID para hacer match con el ID del servidor
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py:197:                WHERE (ServidorID = %s OR MongoServidorUUID = %s) AND Activo = 1
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:10:    utilizando el motor determinista local.
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:26:    # 2. Iterar y procesar cada pedido a través del motor blindado de rentabilidad
/app/backend/core/scheduler/jobs/rentabilidad_scheduler_job.py:36:            # 3. Si el motor determina que requiere aprobación por bajo margen, disparar alerta
/app/backend/core/scheduler/jobs/notifications_job.py:121:        count = await self.db.notification_queue.count_documents({
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:14:- Lock distribuido (MongoDB) para evitar ejecuciones simultáneas
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:25:- MongoDB solo para locks técnicos, NO para datos de negocio
/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py:170:        db: Conexión MongoDB (para locks/logs técnicos, NO para datos de negocio)
/app/backend/core/scheduler/jobs/sync_short_comercial_job.py:37:        db: Conexión a MongoDB
/app/backend/core/scheduler/jobs/sla_job.py:4:Job para procesamiento automático del motor SLA.
/app/backend/core/scheduler/jobs/sync_propinas_tpv_job.py:22:- MongoDB NO es fuente financiera
/app/backend/core/scheduler/jobs/sync_propinas_tpv_job.py:55:        db: Conexión MongoDB (para locks/logs legacy, no para datos financieros)
/app/backend/core/scheduler/jobs/sync_nightly_comercial_job.py:39:        db: Conexión a MongoDB
/app/backend/core/scheduler/jobs/base_job.py:33:            db: Conexión MongoDB
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:69:COLLECTION_PROCESADOS = "inventarios_procesados_auto"
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:187:        """Genera query MongoDB para buscar por esta clave."""
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:218:    - Colección `inventarios_procesados_auto` en MongoDB
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:225:            from core.mongo_stub import get_stub_database
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:255:        return hasattr(self.db, '_collections') and self.db.__class__.__name__ == 'StubDatabase'
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:262:        Ya no depende de MongoDB para tracking de inventarios.
/app/backend/core/scheduler/jobs/sync_ingresos_job.py:43:        db: Conexión MongoDB (para locks/logs legacy, no para datos financieros)
/app/backend/core/scheduler/locks/distributed_lock.py:6:Usa MongoDB para locks persistentes que funcionan con múltiples
/app/backend/core/scheduler/locks/distributed_lock.py:21:    Lock distribuido basado en MongoDB.
/app/backend/core/scheduler/locks/distributed_lock.py:30:    COLLECTION_NAME = "scheduler_locks"
/app/backend/core/scheduler/locks/distributed_lock.py:35:            db: Conexión MongoDB
/app/backend/core/scheduler/locks/distributed_lock.py:42:        self.collection = db[self.COLLECTION_NAME]
/app/backend/core/scheduler/locks/distributed_lock.py:61:            await self.collection.update_one(
/app/backend/core/scheduler/locks/distributed_lock.py:82:            lock_doc = await self.collection.find_one({"job_name": self.job_name})
/app/backend/core/scheduler/locks/distributed_lock.py:120:            result = await self.collection.delete_one({
/app/backend/core/scheduler/locks/distributed_lock.py:155:            result = await self.collection.update_one(
/app/backend/core/scheduler/locks/distributed_lock.py:193:        lock_doc = await self.collection.find_one({
/app/backend/core/scheduler/locks/distributed_lock.py:201:        lock_doc = await self.collection.find_one(
/app/backend/core/scheduler/locks/distributed_lock.py:214:            result = await self.collection.delete_one({"job_name": self.job_name})
/app/backend/core/scheduler/locks/distributed_lock.py:249:        self._is_stub = db is not None and hasattr(db, '_collections') and db.__class__.__name__ == 'StubDatabase'
/app/backend/core/scheduler/locks/distributed_lock.py:252:            self.collection = db[DistributedLock.COLLECTION_NAME]
/app/backend/core/scheduler/locks/distributed_lock.py:253:            logger.info("[LOCK_MANAGER] Inicializado con MongoDB")
/app/backend/core/scheduler/locks/distributed_lock.py:255:            self.collection = None
/app/backend/core/scheduler/locks/distributed_lock.py:266:        if self.collection is None:
/app/backend/core/scheduler/locks/distributed_lock.py:269:        cursor = self.collection.find(
/app/backend/core/scheduler/locks/distributed_lock.py:277:        if self.collection is None:
/app/backend/core/scheduler/locks/distributed_lock.py:280:        result = await self.collection.delete_many({
/app/backend/core/scheduler/locks/distributed_lock.py:289:        if self.collection is None:
/app/backend/core/scheduler/locks/distributed_lock.py:291:        await self.collection.create_index("job_name", unique=True)
/app/backend/core/scheduler/locks/distributed_lock.py:292:        await self.collection.create_index("lock_until")
/app/backend/core/scheduler/locks/distributed_lock.py:293:        await self.collection.create_index("owner")
/app/backend/core/scheduler/locks/distributed_lock.py:299:    Se usa cuando MongoDB no está disponible (modo SQL-only).
/app/backend/core/scheduler/routes.py:30:    Inicializa las rutas con la conexión a MongoDB.
/app/backend/core/scheduler/routes.py:32:    NOTA: MongoDB ELIMINADO del sistema. Este módulo ahora opera con StubDatabase
/app/backend/core/scheduler/routes.py:38:    is_stub = hasattr(database, '_collections') and database.__class__.__name__ == 'StubDatabase'
/app/backend/core/scheduler/routes.py:40:        logger.info("[SCHEDULER_ROUTES] Inicializado con StubDatabase - MongoDB ELIMINADO")
/app/backend/core/scheduler/routes.py:47:    Obtiene la conexión a MongoDB.
/app/backend/core/scheduler/routes.py:54:def is_mongo_available() -> bool:
/app/backend/core/scheduler/routes.py:56:    Verifica si MongoDB real está disponible.
/app/backend/core/scheduler/routes.py:62:    return not (hasattr(_db, '_collections') and _db.__class__.__name__ == 'StubDatabase')
/app/backend/core/cache_key_builder.py:174:        server_id: ID del servidor (SQL id o mongodb_id)
/app/backend/core/config.py:11:    print(settings.MONGO_URL)
/app/backend/core/config.py:25:    # MongoDB
/app/backend/core/config.py:26:    MONGO_URL: str = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
/app/backend/core/communications/dispatcher/dispatcher.py:46:    - Operaciones de MongoDB pasan por StubDatabase
/app/backend/core/communications/dispatcher/dispatcher.py:63:            from core.mongo_stub import StubDatabase
/app/backend/core/communications/dispatcher/dispatcher.py:104:            logger.info("[DISPATCHER] Modo SQL-only: omitiendo carga de providers desde MongoDB")
/app/backend/core/communications/dispatcher/dispatcher.py:108:            providers = await self.db.notification_provider_config.find(
/app/backend/core/communications/notifications/service.py:45:    - Operaciones de MongoDB pasan por StubDatabase
/app/backend/core/communications/notifications/service.py:61:            from core.mongo_stub import StubDatabase
/app/backend/core/communications/notifications/service.py:249:        user = await self.db.users.find_one(
/app/backend/core/communications/notifications/dedup.py:35:        self.log_collection = db.notification_log
/app/backend/core/communications/notifications/dedup.py:111:        existente = await self.log_collection.find_one(filtro, {"_id": 0, "id": 1})
/app/backend/core/communications/notifications/dedup.py:182:        count = await self.log_collection.count_documents({
/app/backend/core/communications/notifications/repository.py:37:        self.config_collection = db.notification_config
/app/backend/core/communications/notifications/repository.py:38:        self.provider_collection = db.notification_provider_config
/app/backend/core/communications/notifications/repository.py:39:        self.template_collection = db.notification_templates
/app/backend/core/communications/notifications/repository.py:40:        self.queue_collection = db.notification_queue
/app/backend/core/communications/notifications/repository.py:41:        self.log_collection = db.notification_log
/app/backend/core/communications/notifications/repository.py:54:        return await self.config_collection.find_one(
/app/backend/core/communications/notifications/repository.py:79:        cursor = self.config_collection.find(filtro, {"_id": 0})
/app/backend/core/communications/notifications/repository.py:85:        await self.config_collection.insert_one(doc)
/app/backend/core/communications/notifications/repository.py:91:        await self.config_collection.update_one(
/app/backend/core/communications/notifications/repository.py:95:        return await self.config_collection.find_one({"id": config_id}, {"_id": 0})
/app/backend/core/communications/notifications/repository.py:99:        result = await self.config_collection.delete_one({"id": config_id})
/app/backend/core/communications/notifications/repository.py:108:        return await self.provider_collection.find_one(
/app/backend/core/communications/notifications/repository.py:115:        return await self.provider_collection.find_one(
/app/backend/core/communications/notifications/repository.py:123:        await self.provider_collection.insert_one(doc)
/app/backend/core/communications/notifications/repository.py:129:        await self.provider_collection.update_one(
/app/backend/core/communications/notifications/repository.py:133:        return await self.provider_collection.find_one({"id": config_id}, {"_id": 0})
/app/backend/core/communications/notifications/repository.py:141:        return await self.template_collection.find_one(
/app/backend/core/communications/notifications/repository.py:148:        return await self.template_collection.find_one(
/app/backend/core/communications/notifications/repository.py:165:        cursor = self.template_collection.find(filtro, {"_id": 0})
/app/backend/core/communications/notifications/repository.py:171:        await self.template_collection.insert_one(doc)
/app/backend/core/communications/notifications/repository.py:179:            await self.template_collection.update_one(
/app/backend/core/communications/notifications/repository.py:184:            await self.template_collection.update_one(
/app/backend/core/communications/notifications/repository.py:188:        return await self.template_collection.find_one({"id": template_id}, {"_id": 0})
/app/backend/core/communications/notifications/repository.py:192:        result = await self.template_collection.update_one(
/app/backend/core/communications/notifications/repository.py:205:        await self.queue_collection.insert_one(doc)
/app/backend/core/communications/notifications/repository.py:211:        cursor = self.queue_collection.find(
/app/backend/core/communications/notifications/repository.py:232:        result = await self.queue_collection.update_one(
/app/backend/core/communications/notifications/repository.py:253:        result = await self.queue_collection.update_one(
/app/backend/core/communications/notifications/repository.py:270:        result = await self.queue_collection.update_one(
/app/backend/core/communications/notifications/repository.py:289:        cursor = self.queue_collection.aggregate(pipeline)
/app/backend/core/communications/notifications/repository.py:302:        await self.log_collection.insert_one(doc)
/app/backend/core/communications/notifications/repository.py:337:        cursor = self.log_collection.find(
/app/backend/core/communications/notifications/repository.py:344:        return await self.log_collection.count_documents(filtro or {})
/app/backend/core/communications/notifications/repository.py:365:        cursor = self.log_collection.aggregate(pipeline)
/app/backend/core/communications/notifications/repository.py:399:        existente = await self.log_collection.find_one({
/app/backend/core/communications/notifications/schemas.py:6:Colecciones MongoDB:
/app/backend/core/communications/templates/template_service.py:95:        self.template_collection = db.notification_templates
/app/backend/core/communications/templates/template_service.py:125:        template = await self.template_collection.find_one(
/app/backend/core/communications/templates/template_service.py:280:            existing = await self.template_collection.find_one(
/app/backend/core/communications/templates/template_service.py:293:                await self.template_collection.insert_one(doc)
/app/backend/core/communications/audit/audit_service.py:26:    - Operaciones de MongoDB pasan por StubDatabase
/app/backend/core/communications/audit/audit_service.py:39:            from core.mongo_stub import StubDatabase
/app/backend/core/communications/audit/audit_service.py:180:        cursor = self.db.notification_log.aggregate(pipeline)
/app/backend/core/communications/scripts/__init__.py:22:from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/core/communications/scripts/__init__.py:302:    for collection_name, indexes in INDEXES.items():
/app/backend/core/communications/scripts/__init__.py:303:        collection = db[collection_name]
/app/backend/core/communications/scripts/__init__.py:313:                await collection.create_index(idx_config["keys"], **kwargs)
/app/backend/core/communications/scripts/__init__.py:314:                logger.info(f"  - Índice creado: {collection_name}.{idx_config['name']}")
/app/backend/core/communications/scripts/__init__.py:317:                    logger.info(f"  - Índice ya existe: {collection_name}.{idx_config['name']}")
/app/backend/core/communications/scripts/__init__.py:329:        existing = await db.notification_config.find_one({"id": config["id"]})
/app/backend/core/communications/scripts/__init__.py:332:            await db.notification_config.insert_one(config)
/app/backend/core/communications/scripts/__init__.py:338:    existing = await db.notification_provider_config.find_one({"id": DEFAULT_PROVIDER_CONFIG["id"]})
/app/backend/core/communications/scripts/__init__.py:341:        await db.notification_provider_config.insert_one(DEFAULT_PROVIDER_CONFIG)
/app/backend/core/communications/scripts/__init__.py:348:        existing = await db.notification_templates.find_one({"id": template["id"]})
/app/backend/core/communications/scripts/__init__.py:351:            await db.notification_templates.insert_one(template)
/app/backend/core/communications/scripts/__init__.py:362:        db: Conexión a MongoDB
/app/backend/core/communications/scripts/__init__.py:380:    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
/app/backend/core/communications/scripts/__init__.py:383:    client = AsyncIOMotorClient(mongo_url)
/app/backend/core/communications/routes.py:38:# INYECCIÓN DE DEPENDENCIA: MongoDB
/app/backend/core/communications/routes.py:46:    Inicializa las rutas con la conexión a MongoDB.
/app/backend/core/communications/routes.py:48:    NOTA: MongoDB ELIMINADO del sistema. Este módulo ahora opera con StubDatabase
/app/backend/core/communications/routes.py:52:        database: Instancia de AsyncIOMotorDatabase o StubDatabase
/app/backend/core/communications/routes.py:57:    is_stub = hasattr(database, '_collections') and database.__class__.__name__ == 'StubDatabase'
/app/backend/core/communications/routes.py:59:        logger.info("[NOTIFICATIONS] Inicializado con StubDatabase - MongoDB ELIMINADO")
/app/backend/core/communications/routes.py:66:    Obtiene la conexión a MongoDB inyectada.
/app/backend/core/communications/routes.py:73:def is_mongo_available() -> bool:
/app/backend/core/communications/routes.py:75:    Verifica si MongoDB real está disponible.
/app/backend/core/communications/routes.py:82:    return not (hasattr(_db, '_collections') and _db.__class__.__name__ == 'StubDatabase')
/app/backend/core/communications/routes.py:162:    config = await db.notification_config.find_one({"id": config_id}, {"_id": 0})
/app/backend/core/communications/routes.py:495:    providers = await db.notification_provider_config.find(
/app/backend/core/communications/routes.py:510:    provider = await db.notification_provider_config.find_one(
/app/backend/core/communications/routes.py:669:    result = await db.notification_provider_config.update_one(
/app/backend/core/communications/routes.py:711:    result = await db.notification_config.update_one(
/app/backend/core/communications/routes.py:726:    config = await db.notification_config.find_one({"id": config_id}, {"_id": 0})
/app/backend/core/context_resolver.py:27:Este módulo ha sido migrado de MongoDB a EDARSAHUB SQL.
/app/backend/core/context_resolver.py:33:- Sistema_EmpresasMongoMap
/app/backend/core/context_resolver.py:35:MongoDB ya no es fuente de datos para resolución de contexto.
/app/backend/core/context_resolver.py:81:    Obtiene empresas desde Sistema_Empresas + Sistema_EmpresasMongoMap
/app/backend/core/context_resolver.py:82:    por UUIDs de MongoDB (empresas_permitidas del usuario).
/app/backend/core/context_resolver.py:86:        empresa_uuids: Lista de UUIDs MongoDB de empresas
/app/backend/core/context_resolver.py:102:            m.EmpresaMongoUUID,
/app/backend/core/context_resolver.py:105:        JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
/app/backend/core/context_resolver.py:106:        WHERE m.EmpresaMongoUUID IN ({placeholders})
/app/backend/core/context_resolver.py:114:            'id': row[3],  # EmpresaMongoUUID (compatibilidad)
/app/backend/core/context_resolver.py:146:            s.MongoUUID,
/app/backend/core/context_resolver.py:148:            m.EmpresaMongoUUID
/app/backend/core/context_resolver.py:150:        JOIN Sistema_EmpresasMongoMap m ON s.EmpresaID = m.EmpresaID_SQL
/app/backend/core/context_resolver.py:159:            'id': row[4],  # MongoUUID sucursal (compatibilidad)
/app/backend/core/context_resolver.py:163:            'empresa_id': row[6],  # EmpresaMongoUUID (compatibilidad)
/app/backend/core/context_resolver.py:193:            m.MongoSucursalUUID,
/app/backend/core/context_resolver.py:206:            'sucursal_id': row[4],  # MongoSucursalUUID (compatibilidad)
/app/backend/core/context_resolver.py:306:            s.MongoUUID,
/app/backend/core/context_resolver.py:308:            em.EmpresaMongoUUID
/app/backend/core/context_resolver.py:311:        JOIN Sistema_EmpresasMongoMap em ON s.EmpresaID = em.EmpresaID_SQL
/app/backend/core/context_resolver.py:326:        'sucursal_id': row[4],  # MongoUUID
/app/backend/core/context_resolver.py:328:        'empresa_id': row[6]  # EmpresaMongoUUID
/app/backend/core/context_resolver.py:334:    Obtiene una empresa por UUID MongoDB desde Sistema_Empresas.
/app/backend/core/context_resolver.py:338:        empresa_uuid: UUID MongoDB de la empresa
/app/backend/core/context_resolver.py:348:            m.EmpresaMongoUUID,
/app/backend/core/context_resolver.py:351:        JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
/app/backend/core/context_resolver.py:352:        WHERE LOWER(m.EmpresaMongoUUID) = LOWER(%s)
/app/backend/core/context_resolver.py:377:    MIGRACIÓN FASE 3-C: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
/app/backend/core/context_resolver.py:384:        - id: ID de la empresa (UUID MongoDB)
/app/backend/core/context_resolver.py:394:    # 1. Obtener empresas permitidas (UUIDs MongoDB)
/app/backend/core/context_resolver.py:427:            empresa_id = empresa['id']  # UUID MongoDB
/app/backend/core/context_resolver.py:444:                    'id': empresa_id,  # UUID MongoDB (compatibilidad)
/app/backend/core/context_resolver.py:469:    MIGRACIÓN FASE 3-C: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
/app/backend/core/context_resolver.py:473:        unidad_id: ID de la unidad de negocio (empresa_id UUID MongoDB)
/app/backend/core/context_resolver.py:524:    MIGRACIÓN FASE 3-C: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
/app/backend/core/context_resolver.py:573:            empresa_id = sucursal_info.get('empresa_id')  # UUID MongoDB
/app/backend/core/user_access_context.py:29:Este módulo ha sido migrado de MongoDB a EDARSAHUB SQL.
/app/backend/core/user_access_context.py:39:- Sistema_EmpresasMongoMap
/app/backend/core/user_access_context.py:44:MongoDB ya no es fuente de datos para resolución de acceso.
/app/backend/core/user_access_context.py:182:    Obtiene todas las empresas activas (UUIDs MongoDB) para acceso global.
/app/backend/core/user_access_context.py:185:        SELECT m.EmpresaMongoUUID
/app/backend/core/user_access_context.py:187:        JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
/app/backend/core/user_access_context.py:209:    Obtiene empresas asignadas al usuario (UUIDs MongoDB).
/app/backend/core/user_access_context.py:216:            m.EmpresaMongoUUID,
/app/backend/core/user_access_context.py:219:        JOIN Sistema_EmpresasMongoMap m ON ea.EmpresaID = m.EmpresaID_SQL
/app/backend/core/user_access_context.py:252:    Traduce empresas (UUIDs MongoDB) a servidores vía mapeos SQL.
/app/backend/core/user_access_context.py:254:    Usa: Sistema_EmpresasMongoMap → Sistema_Sucursales → Sistema_SucursalServidorMapeo
/app/backend/core/user_access_context.py:265:        JOIN Sistema_EmpresasMongoMap em ON s.EmpresaID = em.EmpresaID_SQL
/app/backend/core/user_access_context.py:266:        WHERE em.EmpresaMongoUUID IN ({placeholders})
/app/backend/core/user_access_context.py:328:    MIGRACIÓN FASE 3-D: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
/app/backend/core/user_access_context.py:479:        # Todas las empresas activas (UUIDs MongoDB)
/app/backend/core/centro_control/email_notifications.py:7:1. MongoDB (colección alert_recipients) - Prioridad
/app/backend/core/centro_control/email_notifications.py:56:    Prioridad: MongoDB > Variable de entorno
/app/backend/core/centro_control/email_notifications.py:58:    # Intentar obtener de MongoDB primero
/app/backend/core/centro_control/email_notifications.py:65:        logger.debug(f"[EMAIL] No se pudo obtener recipients de MongoDB: {e}")
/app/backend/core/centro_control/recipients_manager.py:4:Almacena y gestiona los destinatarios de notificaciones en MongoDB.
/app/backend/core/centro_control/recipients_manager.py:23:from pymongo import MongoClient
/app/backend/core/centro_control/recipients_manager.py:28:# MongoDB connection
/app/backend/core/centro_control/recipients_manager.py:29:MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/core/centro_control/recipients_manager.py:39:        client = MongoClient(MONGO_URL)
/app/backend/core/centro_control/recipients_manager.py:44:def get_collection():
/app/backend/core/centro_control/recipients_manager.py:65:    collection = get_collection()
/app/backend/core/centro_control/recipients_manager.py:74:    for doc in collection.find(query).sort("created_at", -1):
/app/backend/core/centro_control/recipients_manager.py:118:    collection = get_collection()
/app/backend/core/centro_control/recipients_manager.py:137:    existing = collection.find_one({
/app/backend/core/centro_control/recipients_manager.py:154:    result = collection.insert_one(doc)
/app/backend/core/centro_control/recipients_manager.py:185:    collection = get_collection()
/app/backend/core/centro_control/recipients_manager.py:196:    result = collection.find_one_and_update(
/app/backend/core/centro_control/recipients_manager.py:228:    collection = get_collection()
/app/backend/core/centro_control/recipients_manager.py:230:    result = collection.delete_one({"_id": ObjectId(recipient_id)})
/app/backend/core/centro_control/whatsapp_notifications.py:7:1. MongoDB (colección alert_recipients) - Prioridad
/app/backend/core/centro_control/whatsapp_notifications.py:65:    Prioridad: MongoDB > Variable de entorno
/app/backend/core/centro_control/whatsapp_notifications.py:67:    # Intentar obtener de MongoDB primero
/app/backend/core/centro_control/whatsapp_notifications.py:74:        logger.debug(f"[WHATSAPP] No se pudo obtener recipients de MongoDB: {e}")
/app/backend/core/centro_control/routes.py:426:    - MongoDB (EDARSA HUB)
/app/backend/core/centro_control/routes.py:1195:    Los destinatarios se almacenan en MongoDB y son utilizados por los
/app/backend/core/mongo_stub.py:2:EDARSA HUB - MongoDB Stub Database
/app/backend/core/mongo_stub.py:4:Implementación stub de MongoDB que no falla cuando se accede a colecciones.
/app/backend/core/mongo_stub.py:6:Este módulo proporciona un objeto 'db' que simula la interfaz de MongoDB
/app/backend/core/mongo_stub.py:19:class StubCollection:
/app/backend/core/mongo_stub.py:21:    Colección stub que simula una colección de MongoDB.
/app/backend/core/mongo_stub.py:32:            logger.debug(f"[MONGO_STUB] Acceso a colección '{self.name}' - MongoDB eliminado")
/app/backend/core/mongo_stub.py:98:    Cursor stub que simula un cursor de MongoDB.
/app/backend/core/mongo_stub.py:101:    def __init__(self, collection_name: str):
/app/backend/core/mongo_stub.py:102:        self.collection_name = collection_name
/app/backend/core/mongo_stub.py:170:    Base de datos stub que simula una base de datos de MongoDB.
/app/backend/core/mongo_stub.py:171:    Acceder a cualquier colección retorna un StubCollection.
/app/backend/core/mongo_stub.py:175:        self._collections: Dict[str, StubCollection] = {}
/app/backend/core/mongo_stub.py:178:    def __getattr__(self, name: str) -> StubCollection:
/app/backend/core/mongo_stub.py:179:        """Acceder a cualquier atributo retorna una StubCollection."""
/app/backend/core/mongo_stub.py:184:            logger.info("[MONGO_STUB] Base de datos stub activa - MongoDB ELIMINADO")
/app/backend/core/mongo_stub.py:187:        if name not in self._collections:
/app/backend/core/mongo_stub.py:188:            self._collections[name] = StubCollection(name)
/app/backend/core/mongo_stub.py:190:        return self._collections[name]
/app/backend/core/mongo_stub.py:192:    def __getitem__(self, name: str) -> StubCollection:
/app/backend/core/mongo_stub.py:193:        """Acceso por índice también retorna StubCollection."""
/app/backend/core/mongo_stub.py:218:    'StubCollection',
/app/backend/core/cerebro.py:8:- Esquemas de MongoDB
/app/backend/core/cerebro.py:659:# MAPEO DE COLECCIONES MONGODB
/app/backend/core/cerebro.py:662:MONGODB_COLLECTIONS = {
/app/backend/core/cerebro.py:707:# ÍNDICES MONGODB REQUERIDOS
/app/backend/core/cerebro.py:710:MONGODB_INDEXES = {
/app/backend/core/cerebro.py:787:    'MONGODB_COLLECTIONS', 'MONGODB_INDEXES',
/app/backend/core/auth/__init__.py:5:NO reemplaza el flujo MongoDB actual.
/app/backend/core/auth/__init__.py:10:    compare_user_mongo_vs_sql,
/app/backend/core/auth/__init__.py:17:    'compare_user_mongo_vs_sql',
/app/backend/core/auth/user_repository_sql.py:8:- NO reemplaza el flujo actual de MongoDB
/app/backend/core/auth/user_repository_sql.py:10:- MongoDB sigue siendo la fuente productiva de autenticación
/app/backend/core/auth/user_repository_sql.py:58:                m.EmpresaMongoUUID
/app/backend/core/auth/user_repository_sql.py:60:            LEFT JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
/app/backend/core/auth/user_repository_sql.py:70:                'uuid_mongo': row[3]
/app/backend/core/auth/user_repository_sql.py:85:            empresas_uuids = [e['uuid_mongo'] for e in all_empresas if e['uuid_mongo']]
/app/backend/core/auth/user_repository_sql.py:93:                m.EmpresaMongoUUID,
/app/backend/core/auth/user_repository_sql.py:96:            JOIN Sistema_EmpresasMongoMap m ON ea.EmpresaID = m.EmpresaID_SQL
/app/backend/core/auth/user_repository_sql.py:136:        Construye diccionario de usuario compatible con estructura MongoDB.
/app/backend/core/auth/user_repository_sql.py:142:        usuario_id, email, nombre, password_hash, activo, public_uuid, mongo_legacy_id = sql_row
/app/backend/core/auth/user_repository_sql.py:144:        # Mapeo de rol SQL a rol MongoDB
/app/backend/core/auth/user_repository_sql.py:145:        ROL_SQL_TO_MONGO = {
/app/backend/core/auth/user_repository_sql.py:158:        rol_mongo = ROL_SQL_TO_MONGO.get(rol_codigo, rol_codigo) if rol_codigo else None
/app/backend/core/auth/user_repository_sql.py:161:            # Campos compatibles con MongoDB
/app/backend/core/auth/user_repository_sql.py:166:            'role': rol_mongo,
/app/backend/core/auth/user_repository_sql.py:167:            'rol': rol_mongo,
/app/backend/core/auth/user_repository_sql.py:178:            '_sql_mongo_legacy_id': mongo_legacy_id,
/app/backend/core/auth/user_repository_sql.py:197:            Dict con estructura compatible MongoDB o None si no existe
/app/backend/core/auth/user_repository_sql.py:211:                    MongoLegacyID
/app/backend/core/auth/user_repository_sql.py:242:            Dict con estructura compatible MongoDB o None si no existe
/app/backend/core/auth/user_repository_sql.py:256:                    MongoLegacyID
/app/backend/core/auth/user_repository_sql.py:314:                    MongoLegacyID
/app/backend/core/auth/user_repository_sql.py:341:# FUNCIONES DE COMPARACIÓN MONGODB VS SQL
/app/backend/core/auth/user_repository_sql.py:344:async def compare_user_mongo_vs_sql(email: str) -> Dict:
/app/backend/core/auth/user_repository_sql.py:346:    Compara usuario entre MongoDB y SQL.
/app/backend/core/auth/user_repository_sql.py:354:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/core/auth/user_repository_sql.py:360:    # Obtener de MongoDB
/app/backend/core/auth/user_repository_sql.py:361:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/core/auth/user_repository_sql.py:363:    mongo_client = AsyncIOMotorClient(mongo_url)
/app/backend/core/auth/user_repository_sql.py:364:    mongo_db = mongo_client[db_name]
/app/backend/core/auth/user_repository_sql.py:366:    user_mongo = await mongo_db.users.find_one({'email': email}, {'_id': 0})
/app/backend/core/auth/user_repository_sql.py:368:    mongo_client.close()
/app/backend/core/auth/user_repository_sql.py:373:    if not user_sql and not user_mongo:
/app/backend/core/auth/user_repository_sql.py:377:            'exists_mongo': False,
/app/backend/core/auth/user_repository_sql.py:386:            'exists_mongo': True,
/app/backend/core/auth/user_repository_sql.py:387:            'user_mongo': user_mongo,
/app/backend/core/auth/user_repository_sql.py:389:            'status': 'MONGO_ONLY'
/app/backend/core/auth/user_repository_sql.py:392:    if not user_mongo:
/app/backend/core/auth/user_repository_sql.py:396:            'exists_mongo': False,
/app/backend/core/auth/user_repository_sql.py:405:    mongo_id = user_mongo.get('id')
/app/backend/core/auth/user_repository_sql.py:406:    if sql_id != mongo_id:
/app/backend/core/auth/user_repository_sql.py:407:        differences.append(f"id: SQL='{sql_id}' vs Mongo='{mongo_id}'")
/app/backend/core/auth/user_repository_sql.py:411:    mongo_role = user_mongo.get('role')
/app/backend/core/auth/user_repository_sql.py:412:    if sql_role != mongo_role:
/app/backend/core/auth/user_repository_sql.py:413:        differences.append(f"role: SQL='{sql_role}' vs Mongo='{mongo_role}'")
/app/backend/core/auth/user_repository_sql.py:417:    mongo_active = user_mongo.get('active', user_mongo.get('activo', False))
/app/backend/core/auth/user_repository_sql.py:418:    if sql_active != mongo_active:
/app/backend/core/auth/user_repository_sql.py:419:        differences.append(f"active: SQL={sql_active} vs Mongo={mongo_active}")
/app/backend/core/auth/user_repository_sql.py:423:    mongo_has_hash = bool(user_mongo.get('password'))
/app/backend/core/auth/user_repository_sql.py:424:    if sql_has_hash != mongo_has_hash:
/app/backend/core/auth/user_repository_sql.py:425:        differences.append(f"has_password: SQL={sql_has_hash} vs Mongo={mongo_has_hash}")
/app/backend/core/auth/user_repository_sql.py:429:    mongo_empresas = set(user_mongo.get('empresas_permitidas', []))
/app/backend/core/auth/user_repository_sql.py:430:    if sql_empresas != mongo_empresas:
/app/backend/core/auth/user_repository_sql.py:431:        only_sql = sql_empresas - mongo_empresas
/app/backend/core/auth/user_repository_sql.py:432:        only_mongo = mongo_empresas - sql_empresas
/app/backend/core/auth/user_repository_sql.py:435:        if only_mongo:
/app/backend/core/auth/user_repository_sql.py:436:            differences.append(f"empresas solo en Mongo: {only_mongo}")
/app/backend/core/auth/user_repository_sql.py:440:    mongo_default = user_mongo.get('empresa_default_id')
/app/backend/core/auth/user_repository_sql.py:441:    if sql_default != mongo_default:
/app/backend/core/auth/user_repository_sql.py:442:        differences.append(f"empresa_default: SQL='{sql_default}' vs Mongo='{mongo_default}'")
/app/backend/core/auth/user_repository_sql.py:449:        'exists_mongo': True,
/app/backend/core/auth/user_repository_sql.py:458:        'user_mongo': {
/app/backend/core/auth/user_repository_sql.py:459:            'id': user_mongo.get('id'),
/app/backend/core/auth/user_repository_sql.py:460:            'role': user_mongo.get('role'),
/app/backend/core/auth/user_repository_sql.py:461:            'active': user_mongo.get('active', user_mongo.get('activo')),
/app/backend/core/auth/user_repository_sql.py:462:            'has_password': bool(user_mongo.get('password')),
/app/backend/core/auth/user_repository_sql.py:463:            'empresas_count': len(user_mongo.get('empresas_permitidas', [])),
/app/backend/core/auth/user_repository_sql.py:464:            'empresa_default': user_mongo.get('empresa_default_id'),
/app/backend/core/auth/user_repository_sql.py:473:    Lista diferencias de migración Auth entre MongoDB y SQL para todos los usuarios SQL.
/app/backend/core/auth/user_repository_sql.py:484:        comparison = await compare_user_mongo_vs_sql(email)
/app/backend/core/auth/user_repository_sql.py:585:    # Mapeo de rol MongoDB a SQL
/app/backend/core/auth/user_repository_sql.py:586:    ROL_MONGO_TO_SQL = {
/app/backend/core/auth/user_repository_sql.py:597:    rol_codigo = ROL_MONGO_TO_SQL.get(role, 'USUARIO')
/app/backend/core/auth/user_repository_sql.py:645:                    SELECT EmpresaID_SQL FROM Sistema_EmpresasMongoMap 
/app/backend/core/auth/user_repository_sql.py:646:                    WHERE EmpresaMongoUUID = %s
/app/backend/core/auth/user_repository_sql.py:748:            ROL_MONGO_TO_SQL = {
/app/backend/core/auth/user_repository_sql.py:759:            rol_codigo = ROL_MONGO_TO_SQL.get(update_data['role'], 'USUARIO')
/app/backend/core/auth/user_repository_sql.py:791:                    SELECT EmpresaID_SQL FROM Sistema_EmpresasMongoMap 
/app/backend/core/auth/user_repository_sql.py:792:                    WHERE EmpresaMongoUUID = %s
/app/backend/core/auth/user_repository_sql.py:899:    Reemplaza la función find_user_by_email de MongoDB.
/app/backend/core/auth/user_repository_sql.py:920:    Reemplaza la función find_user_by_id de MongoDB.
/app/backend/core/auth/user_repository_sql.py:944:    'compare_user_mongo_vs_sql',
/app/backend/core/resilient_sql.py:141:    """Obtiene la configuración del servidor EDARSA HUB desde MongoDB."""
/app/backend/core/resilient_sql.py:143:        server = await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})
/app/backend/core/resilient_sql.py:255:        db: Conexión a MongoDB (para obtener credenciales)
/app/backend/core/mongo_compat.py:2:EDARSA HUB - MongoDB Compatibility Layer
/app/backend/core/mongo_compat.py:4:Capa de compatibilidad para operaciones MongoDB durante la migración a SQL Server.
/app/backend/core/mongo_compat.py:6:Este módulo proporciona funciones helper que manejan el caso cuando MongoDB
/app/backend/core/mongo_compat.py:22:# Referencia global a la conexión MongoDB (puede ser None)
/app/backend/core/mongo_compat.py:23:_mongo_db = None
/app/backend/core/mongo_compat.py:26:def init_mongo_compat(db) -> None:
/app/backend/core/mongo_compat.py:28:    Inicializa el módulo con la conexión MongoDB.
/app/backend/core/mongo_compat.py:31:        db: Instancia de AsyncIOMotorDatabase o None
/app/backend/core/mongo_compat.py:33:    global _mongo_db
/app/backend/core/mongo_compat.py:34:    _mongo_db = db
/app/backend/core/mongo_compat.py:35:    if _mongo_db is None:
/app/backend/core/mongo_compat.py:36:        logger.warning("[MONGO_COMPAT] Inicializado SIN MongoDB - Operaciones retornarán datos vacíos")
/app/backend/core/mongo_compat.py:38:        logger.info("[MONGO_COMPAT] Inicializado con conexión MongoDB")
/app/backend/core/mongo_compat.py:41:def get_mongo_db():
/app/backend/core/mongo_compat.py:42:    """Obtiene la conexión MongoDB (puede ser None)."""
/app/backend/core/mongo_compat.py:43:    return _mongo_db
/app/backend/core/mongo_compat.py:46:def is_mongo_available() -> bool:
/app/backend/core/mongo_compat.py:47:    """Verifica si MongoDB está disponible."""
/app/backend/core/mongo_compat.py:48:    return _mongo_db is not None
/app/backend/core/mongo_compat.py:55:async def mongo_find_one(
/app/backend/core/mongo_compat.py:56:    collection_name: str,
/app/backend/core/mongo_compat.py:61:    Busca un documento en MongoDB.
/app/backend/core/mongo_compat.py:63:    Si MongoDB no está disponible, retorna None.
/app/backend/core/mongo_compat.py:65:    if _mongo_db is None:
/app/backend/core/mongo_compat.py:66:        logger.debug(f"[MONGO_COMPAT] find_one({collection_name}) - MongoDB no disponible")
/app/backend/core/mongo_compat.py:70:        collection = _mongo_db[collection_name]
/app/backend/core/mongo_compat.py:72:            return await collection.find_one(filter_query, projection)
/app/backend/core/mongo_compat.py:73:        return await collection.find_one(filter_query)
/app/backend/core/mongo_compat.py:75:        logger.error(f"[MONGO_COMPAT] Error en find_one({collection_name}): {e}")
/app/backend/core/mongo_compat.py:79:async def mongo_find(
/app/backend/core/mongo_compat.py:80:    collection_name: str,
/app/backend/core/mongo_compat.py:88:    Busca documentos en MongoDB.
/app/backend/core/mongo_compat.py:90:    Si MongoDB no está disponible, retorna lista vacía.
/app/backend/core/mongo_compat.py:92:    if _mongo_db is None:
/app/backend/core/mongo_compat.py:93:        logger.debug(f"[MONGO_COMPAT] find({collection_name}) - MongoDB no disponible")
/app/backend/core/mongo_compat.py:97:        collection = _mongo_db[collection_name]
/app/backend/core/mongo_compat.py:100:        cursor = collection.find(filter_query, projection or {"_id": 0})
/app/backend/core/mongo_compat.py:111:        logger.error(f"[MONGO_COMPAT] Error en find({collection_name}): {e}")
/app/backend/core/mongo_compat.py:115:async def mongo_count(
/app/backend/core/mongo_compat.py:116:    collection_name: str,
/app/backend/core/mongo_compat.py:120:    Cuenta documentos en MongoDB.
/app/backend/core/mongo_compat.py:122:    Si MongoDB no está disponible, retorna 0.
/app/backend/core/mongo_compat.py:124:    if _mongo_db is None:
/app/backend/core/mongo_compat.py:128:        collection = _mongo_db[collection_name]
/app/backend/core/mongo_compat.py:129:        return await collection.count_documents(filter_query or {})
/app/backend/core/mongo_compat.py:131:        logger.error(f"[MONGO_COMPAT] Error en count({collection_name}): {e}")
/app/backend/core/mongo_compat.py:139:async def mongo_insert_one(
/app/backend/core/mongo_compat.py:140:    collection_name: str,
/app/backend/core/mongo_compat.py:144:    Inserta un documento en MongoDB.
/app/backend/core/mongo_compat.py:146:    Si MongoDB no está disponible, retorna None y loguea warning.
/app/backend/core/mongo_compat.py:148:    if _mongo_db is None:
/app/backend/core/mongo_compat.py:149:        logger.warning(f"[MONGO_COMPAT] insert_one({collection_name}) - MongoDB no disponible, documento NO persistido")
/app/backend/core/mongo_compat.py:153:        collection = _mongo_db[collection_name]
/app/backend/core/mongo_compat.py:154:        result = await collection.insert_one(document)
/app/backend/core/mongo_compat.py:157:        logger.error(f"[MONGO_COMPAT] Error en insert_one({collection_name}): {e}")
/app/backend/core/mongo_compat.py:161:async def mongo_insert_many(
/app/backend/core/mongo_compat.py:162:    collection_name: str,
/app/backend/core/mongo_compat.py:166:    Inserta múltiples documentos en MongoDB.
/app/backend/core/mongo_compat.py:168:    Si MongoDB no está disponible, retorna lista vacía.
/app/backend/core/mongo_compat.py:170:    if _mongo_db is None:
/app/backend/core/mongo_compat.py:171:        logger.warning(f"[MONGO_COMPAT] insert_many({collection_name}) - MongoDB no disponible, {len(documents)} documentos NO persistidos")
/app/backend/core/mongo_compat.py:175:        collection = _mongo_db[collection_name]
/app/backend/core/mongo_compat.py:176:        result = await collection.insert_many(documents)
/app/backend/core/mongo_compat.py:179:        logger.error(f"[MONGO_COMPAT] Error en insert_many({collection_name}): {e}")
/app/backend/core/mongo_compat.py:187:async def mongo_update_one(
/app/backend/core/mongo_compat.py:188:    collection_name: str,
/app/backend/core/mongo_compat.py:194:    Actualiza un documento en MongoDB.
/app/backend/core/mongo_compat.py:196:    Si MongoDB no está disponible, retorna False.
/app/backend/core/mongo_compat.py:198:    if _mongo_db is None:
/app/backend/core/mongo_compat.py:199:        logger.warning(f"[MONGO_COMPAT] update_one({collection_name}) - MongoDB no disponible")
/app/backend/core/mongo_compat.py:203:        collection = _mongo_db[collection_name]
/app/backend/core/mongo_compat.py:204:        result = await collection.update_one(filter_query, update, upsert=upsert)
/app/backend/core/mongo_compat.py:207:        logger.error(f"[MONGO_COMPAT] Error en update_one({collection_name}): {e}")
/app/backend/core/mongo_compat.py:211:async def mongo_update_many(
/app/backend/core/mongo_compat.py:212:    collection_name: str,
/app/backend/core/mongo_compat.py:217:    Actualiza múltiples documentos en MongoDB.
/app/backend/core/mongo_compat.py:219:    Si MongoDB no está disponible, retorna 0.
/app/backend/core/mongo_compat.py:221:    if _mongo_db is None:
/app/backend/core/mongo_compat.py:222:        logger.warning(f"[MONGO_COMPAT] update_many({collection_name}) - MongoDB no disponible")
/app/backend/core/mongo_compat.py:226:        collection = _mongo_db[collection_name]
/app/backend/core/mongo_compat.py:227:        result = await collection.update_many(filter_query, update)
/app/backend/core/mongo_compat.py:230:        logger.error(f"[MONGO_COMPAT] Error en update_many({collection_name}): {e}")
/app/backend/core/mongo_compat.py:238:async def mongo_delete_one(
/app/backend/core/mongo_compat.py:239:    collection_name: str,
/app/backend/core/mongo_compat.py:243:    Elimina un documento de MongoDB.
/app/backend/core/mongo_compat.py:245:    Si MongoDB no está disponible, retorna False.
/app/backend/core/mongo_compat.py:247:    if _mongo_db is None:
/app/backend/core/mongo_compat.py:248:        logger.warning(f"[MONGO_COMPAT] delete_one({collection_name}) - MongoDB no disponible")
/app/backend/core/mongo_compat.py:252:        collection = _mongo_db[collection_name]
/app/backend/core/mongo_compat.py:253:        result = await collection.delete_one(filter_query)
/app/backend/core/mongo_compat.py:256:        logger.error(f"[MONGO_COMPAT] Error en delete_one({collection_name}): {e}")
/app/backend/core/mongo_compat.py:260:async def mongo_delete_many(
/app/backend/core/mongo_compat.py:261:    collection_name: str,
/app/backend/core/mongo_compat.py:265:    Elimina múltiples documentos de MongoDB.
/app/backend/core/mongo_compat.py:267:    Si MongoDB no está disponible, retorna 0.
/app/backend/core/mongo_compat.py:269:    if _mongo_db is None:
/app/backend/core/mongo_compat.py:270:        logger.warning(f"[MONGO_COMPAT] delete_many({collection_name}) - MongoDB no disponible")
/app/backend/core/mongo_compat.py:274:        collection = _mongo_db[collection_name]
/app/backend/core/mongo_compat.py:275:        result = await collection.delete_many(filter_query)
/app/backend/core/mongo_compat.py:278:        logger.error(f"[MONGO_COMPAT] Error en delete_many({collection_name}): {e}")
/app/backend/core/mongo_compat.py:286:async def mongo_aggregate(
/app/backend/core/mongo_compat.py:287:    collection_name: str,
/app/backend/core/mongo_compat.py:291:    Ejecuta un pipeline de agregación en MongoDB.
/app/backend/core/mongo_compat.py:293:    Si MongoDB no está disponible, retorna lista vacía.
/app/backend/core/mongo_compat.py:295:    if _mongo_db is None:
/app/backend/core/mongo_compat.py:296:        logger.debug(f"[MONGO_COMPAT] aggregate({collection_name}) - MongoDB no disponible")
/app/backend/core/mongo_compat.py:300:        collection = _mongo_db[collection_name]
/app/backend/core/mongo_compat.py:301:        cursor = collection.aggregate(pipeline)
/app/backend/core/mongo_compat.py:304:        logger.error(f"[MONGO_COMPAT] Error en aggregate({collection_name}): {e}")
/app/backend/core/mongo_compat.py:309:# HELPER PARA ENDPOINTS QUE REQUIEREN MONGO
/app/backend/core/mongo_compat.py:312:def require_mongo(func):
/app/backend/core/mongo_compat.py:314:    Decorador para endpoints que requieren MongoDB.
/app/backend/core/mongo_compat.py:316:    Si MongoDB no está disponible, retorna error 503.
/app/backend/core/mongo_compat.py:323:        if _mongo_db is None:
/app/backend/core/mongo_compat.py:326:                detail="Este endpoint requiere MongoDB que actualmente no está disponible. "
/app/backend/core/mongo_compat.py:333:def mongo_optional(default_value=None):
/app/backend/core/mongo_compat.py:335:    Decorador para endpoints donde MongoDB es opcional.
/app/backend/core/mongo_compat.py:337:    Si MongoDB no está disponible, retorna el valor por defecto.
/app/backend/core/mongo_compat.py:344:            if _mongo_db is None:
/app/backend/core/mongo_compat.py:345:                logger.info(f"[MONGO_COMPAT] {func.__name__} - Retornando valor por defecto (MongoDB no disponible)")
/app/backend/core/mongo_compat.py:357:    'init_mongo_compat',
/app/backend/core/mongo_compat.py:358:    'get_mongo_db',
/app/backend/core/mongo_compat.py:359:    'is_mongo_available',
/app/backend/core/mongo_compat.py:360:    'mongo_find_one',
/app/backend/core/mongo_compat.py:361:    'mongo_find',
/app/backend/core/mongo_compat.py:362:    'mongo_count',
/app/backend/core/mongo_compat.py:363:    'mongo_insert_one',
/app/backend/core/mongo_compat.py:364:    'mongo_insert_many',
/app/backend/core/mongo_compat.py:365:    'mongo_update_one',
/app/backend/core/mongo_compat.py:366:    'mongo_update_many',
/app/backend/core/mongo_compat.py:367:    'mongo_delete_one',
/app/backend/core/mongo_compat.py:368:    'mongo_delete_many',
/app/backend/core/mongo_compat.py:369:    'mongo_aggregate',
/app/backend/core/mongo_compat.py:370:    'require_mongo',
/app/backend/core/mongo_compat.py:371:    'mongo_optional',
/app/backend/core/health_checker.py:40:    MONGODB = "mongodb"
/app/backend/core/health_checker.py:147:    def _check_mongodb(self) -> SourceHealth:
/app/backend/core/health_checker.py:148:        """Verifica conexión a MongoDB"""
/app/backend/core/health_checker.py:151:            from pymongo import MongoClient
/app/backend/core/health_checker.py:154:            mongo_url = os.environ.get('MONGO_URL')
/app/backend/core/health_checker.py:155:            client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
/app/backend/core/health_checker.py:161:                name="MongoDB (EDARSA HUB)",
/app/backend/core/health_checker.py:162:                source_type=SourceType.MONGODB,
/app/backend/core/health_checker.py:169:                name="MongoDB (EDARSA HUB)",
/app/backend/core/health_checker.py:170:                source_type=SourceType.MONGODB,
/app/backend/core/health_checker.py:179:            from pymongo import MongoClient
/app/backend/core/health_checker.py:182:            mongo_url = os.environ.get('MONGO_URL')
/app/backend/core/health_checker.py:183:            client = MongoClient(mongo_url)
/app/backend/core/health_checker.py:186:            servers = list(db.servers.find(
/app/backend/core/health_checker.py:231:        # Verificar MongoDB
/app/backend/core/health_checker.py:232:        mongo_health = self._check_mongodb()
/app/backend/core/health_checker.py:233:        report.sources.append(mongo_health)
/app/backend/core/health_checker.py:234:        if mongo_health.status == HealthStatus.HEALTHY:
/app/backend/core/rbac/service.py:2:EDARSA HUB - RBAC Service (Motor de Autorización)
/app/backend/core/rbac/service.py:4:Motor central de autorización basado en roles.
/app/backend/core/rbac/service.py:87:    # MOTOR DE AUTORIZACIÓN
/app/backend/core/rbac/__init__.py:7:MongoDB ya NO es fuente de datos para RBAC.
/app/backend/core/rbac/__init__.py:13:- service.py: Motor de autorización central
/app/backend/core/rbac/repository_sql.py:181:                    "nombre": codigo,  # Usar código como nombre (compatible con MongoDB)
/app/backend/core/rbac/repository.py:7:MongoDB ya NO es fuente de datos para RBAC.
/app/backend/core/rbac/routes.py:28:from pymongo import MongoClient
/app/backend/core/rbac/routes.py:47:    """Obtiene conexión a MongoDB de forma síncrona."""
/app/backend/core/rbac/routes.py:48:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/core/rbac/routes.py:50:    client = MongoClient(mongo_url)
/app/backend/core/rbac/middleware.py:34:    """Obtiene conexión a MongoDB de forma síncrona."""
/app/backend/core/rbac/middleware.py:36:    from pymongo import MongoClient
/app/backend/core/rbac/middleware.py:37:    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/backend/core/rbac/middleware.py:39:    client = MongoClient(mongo_url)
/app/backend/core/rbac/schemas.py:6:Colecciones MongoDB:
/app/backend/core/alcance_helper.py:86:                SELECT DISTINCT m.EmpresaMongoUUID
/app/backend/core/alcance_helper.py:88:                JOIN Sistema_EmpresasMongoMap m ON s.EmpresaID = m.EmpresaID_SQL
/app/backend/core/alcance_helper.py:89:                WHERE s.MongoUUID IN ({placeholders})
/app/backend/core/alcance_helper.py:90:                   OR m.EmpresaMongoUUID IN ({placeholders})
/app/backend/core/alcance_helper.py:130:                SELECT DISTINCT m.EmpresaMongoUUID
/app/backend/core/alcance_helper.py:132:                JOIN Sistema_EmpresasMongoMap m ON s.EmpresaID = m.EmpresaID_SQL
/app/backend/core/alcance_helper.py:133:                WHERE s.MongoUUID IN ({placeholders})
/app/backend/core/alcance_helper.py:175:        db: Instancia de la base de datos MongoDB
/app/backend/core/system_capability_resolver.py:40:- NO usar MongoDB
/app/backend/core/inventory_analysis_core.py:18:- db: Cliente MongoDB (inyectado)
/app/backend/core/inventory_analysis_core.py:127:            db_client: Cliente de base de datos MongoDB
/app/backend/core/inventory_analysis_core.py:224:        db_client: Cliente MongoDB
/app/backend/core/db.py:4:Gestión centralizada de conexiones a MongoDB y SQL Server.
/app/backend/core/db.py:697:    # parse_sql_server_host está en este mismo módulo (db.py)
/app/backend/core/db.py:1117:# FUNCIONES DE MONGODB (Placeholders para fases futuras)
/app/backend/core/db.py:1120:from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
/app/backend/core/db.py:1121:from pymongo import MongoClient
/app/backend/core/db.py:1123:# Variables globales para conexiones MongoDB (se inicializarán en migración futura)
/app/backend/core/db.py:1124:_mongo_client: Optional[AsyncIOMotorClient] = None
/app/backend/core/db.py:1125:_mongo_db: Optional[AsyncIOMotorDatabase] = None
/app/backend/core/db.py:1126:_sync_mongo_client: Optional[MongoClient] = None
/app/backend/core/db.py:1129:async def get_mongo_client() -> AsyncIOMotorClient:
/app/backend/core/db.py:1131:    Obtiene el cliente MongoDB async.
/app/backend/core/db.py:1134:    global _mongo_client
/app/backend/core/db.py:1135:    if _mongo_client is None:
/app/backend/core/db.py:1136:        raise RuntimeError("MongoDB client not initialized. Use server.py connection.")
/app/backend/core/db.py:1137:    return _mongo_client
/app/backend/core/db.py:1140:async def get_mongo_db() -> AsyncIOMotorDatabase:
/app/backend/core/db.py:1142:    Obtiene la base de datos MongoDB async.
/app/backend/core/db.py:1145:    global _mongo_db
/app/backend/core/db.py:1146:    if _mongo_db is None:
/app/backend/core/db.py:1147:        raise RuntimeError("MongoDB database not initialized. Use server.py connection.")
/app/backend/core/db.py:1148:    return _mongo_db
/app/backend/core/db.py:1151:def get_sync_mongo_db():
/app/backend/core/db.py:1153:    Obtiene la base de datos MongoDB síncrona.
/app/backend/core/db.py:1156:    global _sync_mongo_client
/app/backend/core/db.py:1157:    if _sync_mongo_client is None:
/app/backend/core/db.py:1158:        raise RuntimeError("Sync MongoDB client not initialized. Use server.py connection.")
/app/backend/core/db.py:1159:    return _sync_mongo_client
/app/backend/core/db.py:1162:def init_db_connections(mongo_url: str, db_name: str):
/app/backend/core/db.py:1165:    NOTA: Se usará cuando se migre MongoDB desde server.py (fase futura)
/app/backend/core/db.py:1556:    # MongoDB - Placeholders
/app/backend/core/db.py:1557:    'get_mongo_client',
/app/backend/core/db.py:1558:    'get_mongo_db',
/app/backend/core/db.py:1559:    'get_sync_mongo_db',
/app/backend/routes/portal_proveedores.py:4:Usa la misma conexión MongoDB y los servidores configurados en EDARSA HUB
/app/backend/routes/portal_proveedores.py:206:        supplier = await db.portal_suppliers.find_one({"id": supplier_id}, {"_id": 0})
/app/backend/routes/portal_proveedores.py:252:        supplier = await db.portal_suppliers.find_one({"id": supplier_id}, {"_id": 0})
/app/backend/routes/portal_proveedores.py:285:    existing = await db.portal_suppliers.find_one({"rfc": rfc})
/app/backend/routes/portal_proveedores.py:311:    await db.portal_suppliers.insert_one(supplier)
/app/backend/routes/portal_proveedores.py:334:    supplier = await db.portal_suppliers.find_one({"rfc": rfc}, {"_id": 0})
/app/backend/routes/portal_proveedores.py:405:    invoices = await db.portal_invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
/app/backend/routes/portal_proveedores.py:446:        existing = await db.portal_invoices.find_one({"uuid": uuid_cfdi.upper()})
/app/backend/routes/portal_proveedores.py:496:        await db.portal_invoices.insert_one(invoice)
/app/backend/routes/portal_proveedores.py:519:    invoice = await db.portal_invoices.find_one({
/app/backend/routes/portal_proveedores.py:573:    invoices = await db.portal_invoices.find({
/app/backend/routes/portal_proveedores.py:621:    servers = await db.servers.find({
/app/backend/routes/portal_proveedores.py:970:    suppliers = await db.portal_suppliers.find(
/app/backend/routes/portal_proveedores.py:986:        suppliers = await db.portal_suppliers.find(
/app/backend/routes/portal_proveedores.py:1015:    supplier = await db.portal_suppliers.find_one({"id": supplier_id})
/app/backend/routes/portal_proveedores.py:1029:    await db.portal_suppliers.update_one(
/app/backend/routes/portal_proveedores.py:1067:    supplier = await db.portal_suppliers.find_one(query)
/app/backend/routes/portal_proveedores.py:1075:    await db.portal_suppliers.update_one(
/app/backend/routes/portal_proveedores.py:1104:    supplier = await db.portal_suppliers.find_one({"id": identifier}, {"_id": 0, "password": 0})
/app/backend/routes/portal_proveedores.py:1107:        supplier = await db.portal_suppliers.find_one(
/app/backend/routes/portal_proveedores.py:1136:    invoices = await db.portal_invoices.find(
/app/backend/routes/portal_proveedores.py:1159:    servers = await db.servers.find(
/app/backend/routes/portal_proveedores.py:1175:    supplier = await db.portal_suppliers.find_one({"id": supplier_id})
/app/backend/routes/portal_proveedores.py:1179:        supplier = await db.portal_suppliers.find_one({"rfc": supplier_id.upper()})
/app/backend/routes/portal_proveedores.py:1185:    result = await db.portal_suppliers.delete_one({"id": supplier["id"]})
/app/frontend/yarn.lock:1872:    "@radix-ui/react-collection" "1.1.7"
/app/frontend/yarn.lock:1945:"@radix-ui/react-collection@1.1.7":
/app/frontend/yarn.lock:1947:  resolved "https://registry.yarnpkg.com/@radix-ui/react-collection/-/react-collection-1.1.7.tgz#d05c25ca9ac4695cc19ba91f42f686e3ea2d9aec"
/app/frontend/yarn.lock:2080:    "@radix-ui/react-collection" "1.1.7"
/app/frontend/yarn.lock:2104:    "@radix-ui/react-collection" "1.1.7"
/app/frontend/yarn.lock:2120:    "@radix-ui/react-collection" "1.1.7"
/app/frontend/yarn.lock:2231:    "@radix-ui/react-collection" "1.1.7"
/app/frontend/yarn.lock:2262:    "@radix-ui/react-collection" "1.1.7"
/app/frontend/yarn.lock:2296:    "@radix-ui/react-collection" "1.1.7"
/app/frontend/yarn.lock:2353:    "@radix-ui/react-collection" "1.1.7"
/app/frontend/yarn.lock:11093:    which-collection "^1.0.2"
/app/frontend/yarn.lock:11096:which-collection@^1.0.2:
/app/frontend/yarn.lock:11098:  resolved "https://registry.yarnpkg.com/which-collection/-/which-collection-1.0.2.tgz#627ef76243920a107e7ce8e96191debe4b16c2a0"
/app/frontend/public/auditoria_edarsahub.pdf:96:Gat%#gN)%.%"7kOi%aJl/8q8Y^?+'la)*`>*^,]qA0t/gRpJ\3G5m"WRCXZ(/7gYu&F^56%KQoI5k/:5hfK$@QGAh;#)kq?!)+"3aV6@kaZgI$ObuKH3J&V;Dm[`V5TSQdNEJ*BWm"2b0Sda&V:Cbo_U5Hl\LHIWH=?f?`Pi]GZ=7=qg&9>5?]Q@UY.U_\*Pq2=<nrrYa)ZM.g%r[h9:]_(3!$]uA8!IA.&XZ+9Ddr&`II4G%cnAVjQ=:Cl-iq<djJ's:-Q5(DVg,A@ent:^0CKH39^7J0N4J+j].T_-$_+NIcNVZMh&Xl%Esl/*%8)'*adYWHcQb`fsN9k`s8.Fps*S?,K7P##ii0XIgMHnM%I@J*DbbUEKMs>*9:+18*:#XIS>s[lPWr4-C<o;l,E=sG?r3*;'9@K0-*FmQae:U0cD;]<&/!%l*\E%#pP6t"J8g"\UfN3BZWCpJ?(g5_&ujYi9e.J6DMFVA,9&d+[9ctfT0LWU=^"BFkd42W615i=B-U?[Fj/'+c-JD]:#T1o]YIC.'_DWD.h<YE(32-;q^/C-@[aq%lhAqB<&pgdqrFTjni^d'a[jpRf;(&R,*=!o_?:g,[:N?K^1D&`VWa\phSpXgsD,<3j+B\i_Qe-aquHTk,t]mS_KFOe#Y2P8!r5/`D<\`:T&VgKd7XpjYXg]*Jmdi&)Le0IG[C*VaRa!19I=`HcVMLant;`6r=81<)^*EFUti&`.Q,"0aqp_(]b(T&kB$S+rMd'rHKJKTs4mF;`-Vl`HJ`<\R$:c"&gJ>eWa:EZ$C&<q!dK%Hji@]5"7f&,%8\7BTd4Y$;PP8A0;h%mK5P@)a#IidB.XNks?1^pK$I8!BN@@&04@SiTf;fIsj?EnULoYNWOqPTTBWPEt8dZNe+GP=%-GlXRj[/*H:gjdVYDcoUW4FPLqn]VtE+*KKfTUEkqhgecpRmYk1*LVnj/4'YapT2^9RS@Su06CK9I`mno$BW"bVBeWe6ARjFZE$_,&e`B[&bi=iT\`'];Y@M">2.IK\8FM$1LZo*-fYs!A`"<b_cpqp!rF!6t;2dpmY(KYZKN+O1N8\bn?/r=7@7I6dS\+^^<SgPeV/6329^2LdF&H(;TGUq[r3-bh:8l$BXIAN\Z<'C6;I+K8pHB]@3p4&&Cj]Wb8B&[u&D!bshMR>?U>n5R'7D#5VXOgUX?7crF"M==VU%R,2:@6mYD=$[iQ+iF8&WW?bMgm*sR%`<]fh(kXc2Kjk7d?P6R1)</V>4[q]m#Apf*`%g]#TIZ1M[*3(2m8tP?E*ZR?b??i'+>OTr=DQG7??$PEogclS^j)qi2:H?@):4Fj\%dJ+326eG~>endstream
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:48:<a href="#MIGRACION_PROVEEDORES_MONGO_A_SQL">MIGRACION_PROVEEDORES_MONGO_A_SQL.sql</a>
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:85:-- MOTOR: Microsoft SQL Server 2019+ / Azure SQL (Base de datos: EDARSAHUB)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:263:-- ENTIDAD: EDARSA HUB MULTI-UNIDAD (MOTOR: SQL SERVER)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:382:IF OBJECT_ID('tempdb..#Series_Locales') IS NOT NULL DROP TABLE #Series_Locales;
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:498:IF OBJECT_ID('tempdb..#Sistemas_Software_Fuente') IS NOT NULL 
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:612:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:746:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:1430:    IF OBJECT_ID('tempdb..#Data_Fuente_Auditada') IS NOT NULL DROP TABLE #Data_Fuente_Auditada;
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:1503:IF OBJECT_ID('tempdb..#Data_Fuente_Auditada') IS NOT NULL DROP TABLE #Data_Fuente_Auditada;
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:1509:-- PROYECTO: EDARSA HUB ERP - MOTOR RESILIENTE Y ALTA DISPONIBILIDAD (EDGE OFFLINE CACHE)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:1510:-- MOTOR: Microsoft SQL Server 2019+ (Directo Puerto 1433 - Base de datos EDARSAHUB)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:1610:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:1882:    PRINT 'Aplicando Ajuste 6: Inicialización del motor de Metas y KPI Presupuestales...';
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2003:<h2 id="MIGRACION_PROVEEDORES_MONGO_A_SQL">📄 MIGRACION_PROVEEDORES_MONGO_A_SQL.sql</h2>
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2006:-- SCRIPT: CREACIÓN TABLA PROVEEDORES CENTRAL + MIGRACIÓN MONGO → SQL
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2007:-- OBJETIVO: Establecer estructura SQL para proveedores y migrar datos de MongoDB
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2019:-- 2. Script de Migración (Ejecutar desde tu backend tras leer de Mongo)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2020:-- Nota: La lógica de migración debe ser: Leer Mongo -&gt; Transformar -&gt; Insertar SQL
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2023:    -- Estos valores provendrán de la lectura previa de db.portal_suppliers
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2055:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2199:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2345:IF OBJECT_ID('tempdb..#BD_Fuentes_Sitio') IS NOT NULL DROP TABLE #BD_Fuentes_Sitio;
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2473:    IF OBJECT_ID('tempdb..#Barrido_Fuente_Tickets') IS NOT NULL DROP TABLE #Barrido_Fuente_Tickets;
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2556:IF OBJECT_ID('tempdb..#Barrido_Fuente_Tickets') IS NOT NULL DROP TABLE #Barrido_Fuente_Tickets;
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2584:-- MOTOR: Microsoft SQL Server 2019+ (Directo Puerto 1433 - Base de datos EDARSAHUB)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2730:ON CONFLICT (id_modulo) DO NOTHING; -- O tu equivalente según el motor de BD
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3000:-- 2. Limpiar vistas materializadas (según tu motor de BD)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3060:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3121:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3232:-- MOTOR: Microsoft SQL Server 2019+ (Directo Puerto 1433 - Base de datos EDARSAHUB)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3587:-- 7. VERIFICAR CONSISTENCIA DE mongodb_id
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3590:PRINT '=== VERIFICACIÓN DE mongodb_id ===';
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3594:    SUM(CASE WHEN mongodb_id IS NOT NULL AND mongodb_id = CAST(id AS VARCHAR(50)) THEN 1 ELSE 0 END) AS id_coincide_mongodb_id,
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3595:    SUM(CASE WHEN mongodb_id IS NULL OR mongodb_id = '' THEN 1 ELSE 0 END) AS sin_mongodb_id,
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3596:    SUM(CASE WHEN mongodb_id IS NOT NULL AND mongodb_id != CAST(id AS VARCHAR(50)) THEN 1 ELSE 0 END) AS id_diferente_mongodb_id
/app/frontend/src/App.js:68:// Motor de Precios IA y Benchmark (FASE 1C-3I-D)
/app/frontend/src/App.js:106:              {/* FASE 1C-3I-D: Motor de Precios IA y Benchmark */}
/app/frontend/src/pages/comercial/PricingIA.jsx:2: * FASE 1C-3I-D: Frontend Motor de Precios Sugeridos IA y Benchmark
/app/frontend/src/pages/comercial/PricingIA.jsx:17: * - CERO MongoDB
/app/frontend/src/pages/comercial/PricingIA.jsx:1668:              Motor de Precios con IA
/app/frontend/src/pages/comercial/PricingIA.jsx:1733:        <h4 className="font-semibold text-gray-800 mb-4">Como usar el Motor de Precios IA</h4>
/app/frontend/src/pages/comercial/PricingIA.jsx:1912:            y si requirio revision humana. No se usa MongoDB.
/app/frontend/src/pages/comercial/PricingIA.jsx:2390:            de EDARSAHUB SQL Server. No se usa MongoDB. Las metricas se calculan en tiempo real desde la base de datos.
/app/frontend/src/pages/comercial/PricingIA.jsx:2433:            Motor de Precios Sugeridos IA
/app/frontend/src/pages/comercial/PricingIA.jsx:2566:        <span>Datos de EDARSAHUB SQL Server | CERO MongoDB</span>
/app/frontend/src/pages/CentroControl.jsx:808:                        {fuente.tipo === 'mongodb' ? (
/app/frontend/src/components/PropinasTPV.jsx:230:      // Si falla v2, no usar fallback MongoDB (según máximas)
/app/frontend/src/components/edge/mapa_mesas_live3d.ts:4:import { MotorInventarioParametrico } from "../../backend/modules/edge/motor_inventario_parametrico";
/app/frontend/src/components/edge/mapa_mesas_live3d.ts:8:    private motorInventario: MotorInventarioParametrico;
/app/frontend/src/components/edge/mapa_mesas_live3d.ts:12:        this.motorInventario = new MotorInventarioParametrico();
/app/frontend/src/lib/sincronizacionEnVivo.js:9:    // Instanciamos el nuevo motor resiliente
/app/frontend/src/hooks/useLocalFirst.js:137:    await localDB.remove(storeName, cacheKey);
/app/frontend/src/hooks/useLocalFirst.js:210:    const exists = await localDB.has(storeName, cacheKey);
/app/frontend/src/hooks/useLocalFirst.js:214:        await localDB.set(storeName, cacheKey, data, syncManager.TTL_CONFIG[storeName] || 5);
/app/frontend/src/services/comprasUtils.js:13: * - MongoDB solo para cache/logs
/app/frontend/src/services/prefetchManager.js:54:  const cached = await localDB.has(task.store, key);
/app/frontend/src/services/prefetchManager.js:73:    await localDB.set(task.store, key, data, task.ttl);
/app/frontend/src/services/prefetchManager.js:168:  const cached = await localDB.get(task.store, key);
/app/frontend/src/services/prefetchManager.js:181:  return await localDB.has(task.store, key);
/app/frontend/src/services/prefetchManager.js:188:  await localDB.clearStore(STORES.PREFETCH_CACHE);
/app/frontend/src/services/syncManager.js:37:    localDB.cleanAllExpired();
/app/frontend/src/services/syncManager.js:41:  localDB.initDB();
/app/frontend/src/services/syncManager.js:105:    localData = await localDB.get(storeName, key, true); // ignoreExpiry = true para tener fallback
/app/frontend/src/services/syncManager.js:125:  const needsRefresh = forceRefresh || !localData || await localDB.isExpired(storeName, key);
/app/frontend/src/services/syncManager.js:146:    await localDB.set(storeName, key, serverData, ttl);
/app/frontend/src/services/syncManager.js:193:    localData = await localDB.get(storeName, key, true);
/app/frontend/src/services/syncManager.js:211:        await localDB.set(storeName, key, serverData, TTL_CONFIG[storeName] || 30);
/app/frontend/src/services/syncManager.js:280:  await localDB.clearStore(storeName);
/app/frontend/src/services/localDB.js:33:    const request = indexedDB.open(DB_NAME, DB_VERSION);
/app/frontend/src/services/localDB.js:51:        if (!db.objectStoreNames.contains(storeName)) {
/app/frontend/src/services/localDB.js:52:          const store = db.createObjectStore(storeName, { keyPath: 'id' });
/app/frontend/src/services/localDB.js:73:    const transaction = db.transaction(storeName, 'readwrite');
/app/frontend/src/services/localDB.js:109:    const transaction = db.transaction(storeName, 'readonly');
/app/frontend/src/services/localDB.js:163:    const transaction = db.transaction(storeName, 'readonly');
/app/frontend/src/services/localDB.js:196:    const transaction = db.transaction(storeName, 'readwrite');
/app/frontend/src/services/localDB.js:219:    const transaction = db.transaction(storeName, 'readonly');
/app/frontend/src/services/localDB.js:250:    const transaction = db.transaction(storeName, 'readwrite');
/app/frontend/src/services/localDB.js:291:    const transaction = db.transaction(storeName, 'readwrite');
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:18:Son **TRES ENTIDADES DISTINTAS** con **IDs DIFERENTES** en MongoDB:
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:20:| Entidad | Colección MongoDB | Registros | IDs Usados |
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:26:**Relación jerárquica en MongoDB:**
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:38:| `users.empresas_permitidas` | IDs de **Empresa** | `empresas` (MongoDB) |
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:40:| `Unidades_Negocio.id` (EDARSAHUB) | UUIDs de Unidad | Diferente a MongoDB |
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:43:- `users.empresas_permitidas` usa IDs de la colección `empresas` (MongoDB)
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:45:- Los IDs de `empresas` MongoDB **NO coinciden** con `Unidades_Negocio` EDARSAHUB
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:49:**MongoDB `empresas` (5 registros):**
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:67:**⚠️ CONCLUSIÓN:** Los IDs son COMPLETAMENTE DIFERENTES entre MongoDB y EDARSAHUB. Migración directa NO es posible.
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:73:│                           MONGODB (ACTUAL)                                   │
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:113:│  │  Unidades_Negocio   │  ← Existe, 5 registros, IDs diferentes a MongoDB   │
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:127:│  │ Servidores_Conexiones│  ← Existe, 17 registros, IDs coinciden con MongoDB│
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:137:| **user_access_context** | `empresas_ids` | UUID de `empresas` MongoDB | MongoDB |
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:141:| **Servidores** | `server_id` | UUID | EDARSAHUB/MongoDB |
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:184:**⚠️ PROBLEMA:** Los IDs de `empresas` MongoDB no coinciden con `Unidades_Negocio` EDARSAHUB. Se requiere mapeo previo.
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:288:| IDs de `empresas` MongoDB ≠ `Unidades_Negocio` EDARSAHUB | **P0_CRÍTICO** | Crear tabla de mapeo o normalizar IDs antes de migrar |
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:290:| `RH_Cat_Sucursales` usa INT, MongoDB usa UUID | **P2_MEDIO** | Usar mapeo por nombre o crear columna UUID |
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:309:| 1 | Mapear IDs `empresas` MongoDB → `Unidades_Negocio` EDARSAHUB | 5/5 mapeados por nombre |
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:334:2. **¿Cómo mapear IDs de `empresas` MongoDB a `Unidades_Negocio` EDARSAHUB?**
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:337:   - Opción C: Actualizar MongoDB para usar IDs de EDARSAHUB
/app/docs/PROPUESTA_DDL_AUTH_RBAC_EDARSAHUB.md:350:2. ✅ **IDs de MongoDB ≠ IDs de EDARSAHUB** (requiere mapeo)
/app/docs/FASE4_EVIDENCIA.md:180:3. Opcional: db.sec_bitacora_admin.drop()
/app/docs/DEPLOYMENT_ENV_VARS.md:12:### Base de Datos MongoDB
/app/docs/DEPLOYMENT_ENV_VARS.md:14:MONGO_URL=mongodb://localhost:27017
/app/docs/DEPLOYMENT_ENV_VARS.md:17:> ⚠️ Si usas MongoDB Atlas u otro servicio externo, cambia MONGO_URL
/app/docs/DEPLOYMENT_ENV_VARS.md:84:Los servidores SQL están configurados en MongoDB (colección `servers`).
/app/docs/DEPLOYMENT_ENV_VARS.md:105:1. **MongoDB**: El deployment de Emergent incluye MongoDB local. Si prefieres usar MongoDB Atlas, actualiza MONGO_URL.
/app/docs/DEPLOYMENT_ENV_VARS.md:110:   - Credenciales SQL correctas (ya almacenadas en MongoDB)
/app/docs/DEPLOYMENT_ENV_VARS.md:124:- [ ] Backup de MongoDB realizado
/app/docs/AUDITORIA_RH_NOMINAS_02.md:18:**Corrección:** Se modificó `/app/backend/core/db.py` para NO marcar el servidor offline cuando el error es de query (tabla/sintaxis), solo cuando es error de autenticación.
/app/docs/AUDITORIA_RH_NOMINAS_02.md:36:| Nóminas | Ciclos | Listado | — | `/nomina/ciclos` | 0 | MongoDB | ⚠️ TABLA VACÍA REAL | Colección vacía |
/app/docs/AUDITORIA_RH_NOMINAS_02.md:82:**Causa raíz:** En `/app/backend/core/db.py`, cuando `execute_sql_query_direct()` fallaba con un error de query (tabla no existe), marcaba el servidor completo como offline con `mark_server_offline(host)`.
/app/docs/AUDITORIA_RH_NOMINAS_02.md:99:**Archivo:** `/app/backend/core/db.py` líneas ~956-965
/app/docs/FASE_4E_FRONTEND_DESACOPLAMIENTO_COMPONENTES.md:133:Se implemento sistema de administracion de cache en MongoDB:
/app/docs/INCIDENCIAS_OPERACION.md:78:4. **MongoDB solo para cache** - Persistencia oficial en SQL Server.
/app/docs/COMERCIAL_DEPENDENCIAS_CACHE_3A3.md:124:| DuplicateKeyError MongoDB | ⚠️ Conocido/Inofensivo |
/app/docs/ARQUITECTURA_CLASIFICACION_DATOS_LIVE_VS_CONSOLIDADOS.md:34:- MongoDB cache
/app/docs/ARQUITECTURA_CLASIFICACION_DATOS_LIVE_VS_CONSOLIDADOS.md:60:**Importante**: EDARSA HUB es el cerebro del sistema. La tecnología de persistencia específica (SQL Server propio, almacenamiento estructurado, etc.) se decide según el caso de uso, pero la regla arquitectónica siempre habla de EDARSA HUB como fuente, no de una tecnología específica como MongoDB.
/app/docs/ARQUITECTURA_CLASIFICACION_DATOS_LIVE_VS_CONSOLIDADOS.md:105:| **Manuales Operativos** | `modules/manuales_operativos/` | MongoDB | ✅ CORRECTO | Documentos internos |
/app/docs/ARQUITECTURA_CLASIFICACION_DATOS_LIVE_VS_CONSOLIDADOS.md:106:| **Configuración - Asignaciones** | `modules/configuracion/` | MongoDB | ✅ CORRECTO | Configuración interna |
/app/docs/ARQUITECTURA_CLASIFICACION_DATOS_LIVE_VS_CONSOLIDADOS.md:107:| **Usuarios/Roles** | `modules/auth/` | MongoDB | ✅ CORRECTO | Datos internos del sistema |
/app/docs/ARQUITECTURA_CLASIFICACION_DATOS_LIVE_VS_CONSOLIDADOS.md:293:    result = await db.kpis_consolidados.find_one({
/app/docs/CENTRO_DE_CONTROL_EDARSA_WIREFRAME.md:798:│  │  │   MONGODB     │  │  SCHEDULER    │                            │ │
/app/docs/CENTRO_DE_CONTROL_EDARSA_WIREFRAME.md:818:│  │ MongoDB         │ TODOS              │ Config, Auth      │ CRÍTICO││
/app/docs/CENTRO_DE_CONTROL_EDARSA_WIREFRAME.md:923:│  │ • MongoDB (configuración)                                         │ │
/app/docs/DIAGNOSTICO_MPRO_FALLBACK_FECHAS_Y_CREDENCIALES.md:16:- Las credenciales en MongoDB eran válidas (HRLectura/National09$)
/app/docs/DIAGNOSTICO_MPRO_FALLBACK_FECHAS_Y_CREDENCIALES.md:69:### Fuente central (MongoDB - Menú Servidores):
/app/docs/DIAGNOSTICO_MPRO_FALLBACK_FECHAS_Y_CREDENCIALES.md:85:**Conclusión**: Ambas credenciales funcionan, pero la fuente autoritativa debe ser MongoDB.
/app/docs/DIAGNOSTICO_MPRO_FALLBACK_FECHAS_Y_CREDENCIALES.md:159:│ 6. Ejecutar query SQL con credenciales de MongoDB       │
/app/docs/AUDITORIA_FINANCIERA_PROPUESTA.md:15:| **MongoDB (edarsa_hub)** | ❌ NO existe tabla centralizada | Solo `bitacora_tecnica` (1 registro de refactorización) |
/app/docs/AUDITORIA_FINANCIERA_PROPUESTA.md:24:| **Propinas TPV - Config** | Crear/Editar % | ✅ SÍ | MongoDB `propinas_config` (campos `created_by`, `updated_by`, `motivo_cambio`) |
/app/docs/AUDITORIA_FINANCIERA_PROPUESTA.md:35:| Propinas Config (MongoDB) | ❌ NO | ❌ NO |
/app/docs/AUDITORIA_FINANCIERA_PROPUESTA.md:289:            await self.db.execute(query, [
/app/docs/AUDITORIA_FINANCIERA_PROPUESTA.md:316:        return await self.db.fetch_all(query, [limite, registro_id])
/app/docs/AUDITORIA_FINANCIERA_PROPUESTA.md:342:        return await self.db.fetch_all(query, params)
/app/docs/FASE10_EVIDENCIA.md:194:4. Opcional: db.sec_roles.deleteOne({codigo: "ADMIN_USUARIOS"})
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:17:| **Colecciones en MongoDB** | 72 |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:19:| **Dependencias MongoDB detectadas** | 15 colecciones críticas |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:24:**EDARSAHUB SQL Server ya tiene estructura completa para Usuarios, Roles, Permisos, Sesiones, Servidores, Unidades de Negocio, pero el código actual sigue leyendo mayoritariamente de MongoDB para estos módulos.**
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:163:## 4. INVENTARIO REAL DE MONGODB (72 COLECCIONES)
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:206:### 5.1 Uso de MongoDB por Archivo Principal (server.py)
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:209:| `db.servers` | 85 | ALTA - Crítico para operación |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:210:| `db.informes_auditoria` | 26 | MEDIA |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:211:| `db.users` | 18 | ALTA - Auth principal |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:212:| `db.nomina_ciclos` | 15 | MEDIA |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:213:| `db.solicitudes_catalogos` | 14 | BAJA |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:214:| `db.server_sucursales_config` | 10 | ALTA |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:215:| `db.sec_bitacora_admin` | 10 | BAJA (logs) |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:234:| USUARIOS/AUTH/RBAC | MongoDB | ❌ INCORRECTO | EDARSAHUB tiene tablas completas pero NO SE USAN |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:235:| SERVIDORES | MongoDB + EDARSAHUB | ⚠️ PARCIAL | EDARSAHUB tiene 17 servidores, MongoDB tiene 13 |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:236:| MIS TAREAS | MongoDB | ✅ CORRECTO | No hay equivalente en EDARSAHUB |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:239:| COMPRAS | SQL vivo + MongoDB | ⚠️ PARCIAL | EDARSAHUB tiene 19 tablas de Compras_ |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:244:| CENTRO DE CONTROL | MongoDB | ⚠️ PARCIAL | alert_recipients en MongoDB, no hay equivalente SQL |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:245:| SCHEDULER | MongoDB | ✅ CORRECTO TEMPORAL | scheduler_job_log es efímero |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:246:| ALERTAS | MongoDB | ⚠️ PARCIAL | EDARSAHUB tiene ActivoFijo_Alertas |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:247:| EMPRESAS/UNIDADES | MongoDB | ❌ INCORRECTO | EDARSAHUB tiene Unidades_Negocio |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:253:| # | Módulo | Fuente Actual | Tablas MongoDB | Tablas EDARSAHUB | SQL Vivo | ¿EDARSAHUB Principal? | Dependencia MongoDB | **DICTAMEN** |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:255:| 1 | **USUARIOS/AUTH/RBAC** | MongoDB | users, roles, rbac_* | Usuario_* (14 tablas) | NO | SÍ (estructura completa) | CRÍTICA | **MONGO_LEGACY_DEUDA_TÉCNICA** |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:256:| 2 | **SERVIDORES** | MongoDB + EDARSAHUB | servers | Servidores_Conexiones | NO | SÍ (17 registros) | ALTA | **EDARSAHUB_EXISTE_PERO_CÓDIGO_USA_MONGO** |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:257:| 3 | **MIS TAREAS** | MongoDB | fase2_operativo_* | NO EXISTE | NO | NO (workflow local) | LEGÍTIMA | **MONGO_LEGÍTIMO_TEMPORAL** |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:260:| 6 | **COMPRAS** | SQL vivo + MongoDB | compras_params | Compras_* (19 tablas) | SÍ | SÍ para histórico | BAJA | **SQL_VIVO_OPERATIVO_CORRECTO** |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:265:| 11 | **CENTRO DE CONTROL** | MongoDB | alert_recipients, notificaciones_log | NO EXISTE | SÍ (monitoreo) | NO | ALTA | **EDARSAHUB_NO_EXISTE_REQUIERE_PROPUESTA** |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:266:| 12 | **SCHEDULER** | MongoDB | scheduler_job_log, scheduler_locks | NO EXISTE | NO | NO (efímero) | LEGÍTIMA | **MONGO_LEGÍTIMO_TEMPORAL** |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:267:| 13 | **ALERTAS** | MongoDB | alertas_sistema | ActivoFijo_Alertas | NO | PARCIAL | MEDIA | **EDARSAHUB_EXISTE_PERO_CÓDIGO_USA_MONGO** |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:268:| 14 | **EMPRESAS/UNIDADES** | MongoDB | empresas, sec_unidades_* | Unidades_Negocio | NO | SÍ | ALTA | **EDARSAHUB_EXISTE_PERO_CÓDIGO_USA_MONGO** |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:272:## 8. CLASIFICACIÓN DE DEPENDENCIAS MONGODB
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:350:| Auth/RBAC en MongoDB mientras EDARSAHUB tiene estructura vacía | Inconsistencia de datos maestros | TODOS |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:351:| Servidores duplicados (13 en MongoDB, 17 en EDARSAHUB) | Configuraciones desincronizadas | Comercial, Compras, Operaciones |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:356:| Unidades de negocio en MongoDB sin sincronía con EDARSAHUB | Filtros RBAC incorrectos | Todos los dashboards |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:357:| Sucursales en MongoDB vs RH_Cat_Sucursales | Inconsistencia en reportes | RH, Finanzas |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:362:| Cache MongoDB sin TTL definido | Datos obsoletos | Comercial, Dashboard |
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:375:1. Poblar `Usuario_Catalogo` desde MongoDB `users`
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:380:6. Mantener MongoDB como fallback temporal
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:383:1. Validar paridad entre MongoDB `servers` y `Servidores_Conexiones`
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:385:3. Actualizar server_registry.py para eliminar fallback MongoDB
/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md:417:# Dependencias MongoDB en código
/app/docs/COMPRAS_BLINDAJE_SYSTEM_TYPE_MPRO.md:36:| 6666 | GET /compras/parametros/{server_id} | Sin SQL, MongoDB |
/app/docs/COMPRAS_BLINDAJE_SYSTEM_TYPE_MPRO.md:37:| 6687 | POST /compras/parametros | Sin SQL, MongoDB |
/app/docs/GUIA_PILOTO_SYNC_AGENT.md:152:# Desde ambiente con acceso a MongoDB
/app/docs/GUIA_PILOTO_SYNC_AGENT.md:153:mongosh --eval "db.kpis_comercial.find({'source.type': 'SYNC_AGENT'}).pretty()"
/app/docs/GUIA_PILOTO_SYNC_AGENT.md:158:mongosh --eval "db.sync_agent_registry.find({'agent_id': 'agent-piloto-sr-001'}).pretty()"
/app/docs/GUIA_PILOTO_SYNC_AGENT.md:259:db.kpis_comercial.find({"source.is_pilot": true})
/app/docs/GUIA_PILOTO_SYNC_AGENT.md:262:db.sync_agent_registry.find({"is_pilot": true})
/app/docs/GUIA_PILOTO_SYNC_AGENT.md:273:db.kpis_comercial.deleteMany({"source.is_pilot": true})
/app/docs/GUIA_PILOTO_SYNC_AGENT.md:276:db.sync_agent_registry.deleteMany({"is_pilot": true})
/app/docs/FASE7_EVIDENCIA.md:137:| Colecciones MongoDB | ✅ INTACTAS |
/app/docs/CACHE_CONTEXT_POLICY_3C1.md:38:| `comercial/cache_service.py` | MongoDB collection | Datos de dashboard, metas, etc. | endpoint, server_id, sucursal, fecha, system_type | user_id (si aplica) | BAJO | ✅ Ya incluye system_type |
/app/docs/CACHE_CONTEXT_POLICY_3C1.md:40:| `finanzas/propinas_tpv/cache_manager.py` | MongoDB collection | Datos de propinas | fecha, server_id, sucursal_id, params | - | BAJO | ✅ Ya contextualizado |
/app/docs/CACHE_CONTEXT_POLICY_3C1.md:318:3. **MongoDB sin TTL automático**: Los caches en MongoDB (`comercial_cache`) deben limpiarse manualmente o con job programado si se acumulan demasiados.
/app/docs/CODE_QUALITY_IMPROVEMENTS.md:19:3. **test_core_db.py**
/app/docs/POLITICA_FECHAS_EDARSA_HUB.md:43:| **MongoDB** | ISO 8601 con timezone | 2026-04-15T14:32:45+00:00 |
/app/docs/POLITICA_FECHAS_EDARSA_HUB.md:193:| **MongoDB** | UTC con conversión explícita |
/app/docs/POLITICA_FECHAS_EDARSA_HUB.md:216:| 2 | Timezone no explícito en MongoDB | Todos los módulos | MEDIO | BAJA |
/app/docs/CIERRE_Y_BLINDAJE_OPERACIONES_ANALISIS.md:93:| MongoDB | NoSQL | Local | Análisis, reportes |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:13:Se completaron exitosamente los 5 cambios del Lote 2, migrando los bypasses de `db.servers.find_one()` hacia `server_registry.get_server_connection_info()`.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:43:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:52:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:63:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:72:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:83:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:92:**Bypass eliminado:** `db.servers.find_one({"id": server_id})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:96:**Nota:** Esta función guarda estado en `db.server_status` - esto es uso legítimo de MongoDB para cache de estado.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:104:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:113:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:117:**Nota:** La función lee `db.server_sucursales_config` que es uso legítimo de MongoDB para configuración local.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:125:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:134:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:138:**Nota:** La función escribe a `db.server_sucursales_config` que es uso legítimo de MongoDB para configuración local.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:229:**Nota:** Los usos de MongoDB para `db.server_status` y `db.server_sucursales_config` son legítimos (cache y configuración local).
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:300:- 5 bypasses eliminados de `db.servers.find_one()`
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE2_REPORT.md:305:- MongoDB deja de ser fuente maestra en los 5 puntos corregidos
/app/docs/P0_PORTAL_PROVEEDORES_AUTH_01_REPORT.md:50:    3. Busca usuario en MongoDB
/app/docs/P0_PORTAL_PROVEEDORES_AUTH_01_REPORT.md:132:    suppliers = await db.portal_suppliers.find(...).to_list(500)
/app/docs/P0_PORTAL_PROVEEDORES_AUTH_01_REPORT.md:142:    suppliers = await db.portal_suppliers.find(...).to_list(500)
/app/docs/MATRIZ_CLASIFICACION_GRANULAR_DATOS.md:221:| "MongoDB first" como regla | **EDARSA HUB FIRST** - MongoDB es implementación, no arquitectura |
/app/docs/CAB_PROPINAS_TPV_VALIDACION_TECNICA.md:176:│                         EDARSA HUB (MongoDB)                        │
/app/docs/CAB_PROPINAS_TPV_VALIDACION_TECNICA.md:481:| ¿Es 100% desacoplado? | **SÍ** | Solo crea colecciones nuevas en MongoDB |
/app/docs/CAB_PROPINAS_TPV_VALIDACION_TECNICA.md:521:│  │           MongoDB (COLECCIONES NUEVAS)                        │ │
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:46:| **Pendientes** | Amarillo | `resumen.PENDIENTE.count` + `total_esperado` | MongoDB |
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:47:| **En Proceso** | Azul | `resumen.EN_PROCESO.count` + `total_esperado` | MongoDB |
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:48:| **Cuadrados** | Verde | `resumen.CUADRADO.count` + `total_depositado` | MongoDB |
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:49:| **Descuadre** | Rojo | `resumen.DESCUADRE.count` + `total_diferencia` | MongoDB |
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:146:| **Guardar Cuadre** | `handleGuardarCuadre()` | `POST /api/finanzas/tesoreria/cuadres` | Crea registro en MongoDB |
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:160:## 1.7 Colecciones MongoDB que Usa
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:184:| `pymongo` | DB | Conexión a MongoDB |
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:257:## 2.5 Colección MongoDB que NO DEBE Tocarse
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:318:| **RI-01**: Datos Mongo vs SQL difieren | Alta | CRÍTICO | Dual write sin sincronización |
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:336:║     → Misma colección MongoDB                                      ║
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:392:│      └── Colección: tesoreria_cuadres_z (MongoDB)                  │
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:430:│  MongoDB (ACTUAL - PROTEGIDO)                                      │
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:439:│  MongoDB Cache (NUEVO)                                              │
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:451:| Colección/Tabla | `tesoreria_cuadres_z` (Mongo) | `propinas_tpv_control` (SQL) | NINGUNA |
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:461:│  └── Lee de: MongoDB tesoreria_cuadres_z                        │
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:462:│  └── Escribe en: MongoDB tesoreria_cuadres_z                    │
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:472:│  └── Cache en: MongoDB                                          │
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:590:| **R5: Datos inconsistentes** | Mongo vs SQL difieren | Desactivar feature flag |
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:635:| Colección MongoDB | `mongoexport --db edarsahub --collection tesoreria_cuadres_z --out backup_cuadres.json` |
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:718:| Nuevas tablas SQL | ✅ SÍ | Sin tocar MongoDB actual |
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:720:| Cache MongoDB para nuevos módulos | ✅ SÍ | Colecciones con prefijo diferente |
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:750:║  ✓ No se tocará la colección MongoDB existente                    ║
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:785:├── Datos: tesoreria_cuadres_z (MongoDB)
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:791:├── Datos: propinas_tpv_* (SQL Server), propinas_cache_* (MongoDB)
/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md:797:├── Datos: Tablas SQL unificadas + Cache MongoDB
/app/docs/AUDITORIA_OPERACIONES_INVENTARIOS_01.md:16:Ambos niveles funcionan correctamente. Los datos residen en MongoDB (workflows, tareas) y SQL Server (inventarios físicos).
/app/docs/AUDITORIA_OPERACIONES_INVENTARIOS_01.md:27:| Auditoría | Informes | Lista | — | `/auditoria/informes` | 35 | MongoDB | ✅ OK | Informes históricos |
/app/docs/AUDITORIA_OPERACIONES_INVENTARIOS_01.md:28:| Auditoría | Informes v2 | Lista | — | `/informes-auditoria` | 35 | MongoDB | ✅ OK | Mismo endpoint |
/app/docs/AUDITORIA_OPERACIONES_INVENTARIOS_01.md:30:| Fase2 | Workflows | Lista | — | `/v2/workflows` | 18 | MongoDB | ✅ OK | workflow_inventarios |
/app/docs/AUDITORIA_OPERACIONES_INVENTARIOS_01.md:31:| Fase2 | Tareas | Lista | — | `/v2/tareas` | 18 | MongoDB | ✅ OK | tareas_inventario |
/app/docs/AUDITORIA_OPERACIONES_INVENTARIOS_01.md:32:| Fase2 | Config | Parámetros | — | `/v2/configuracion` | — | MongoDB | ✅ OK | umbral_justificacion=500 |
/app/docs/AUDITORIA_OPERACIONES_INVENTARIOS_01.md:33:| Fase2 | Aud. Programadas | Lista | — | `/v2/auditorias-programadas` | 0 | MongoDB | ✅ OK | Sin programar |
/app/docs/AUDITORIA_OPERACIONES_INVENTARIOS_01.md:40:## Colecciones MongoDB Verificadas
/app/docs/AUDITORIA_OPERACIONES_INVENTARIOS_01.md:106:| Fuentes correctamente identificadas | ✅ MongoDB/SQL |
/app/docs/MIGRACION_TECNICA_PROPINAS_SQL.md:14:Refactorización del módulo de Propinas TPV para usar SQL Server EDARSA HUB como fuente oficial de datos financieros, relegando MongoDB a un rol exclusivo de cache de lectura.
/app/docs/MIGRACION_TECNICA_PROPINAS_SQL.md:22:                           └──CACHE──► MongoDB ◄────┘
/app/docs/MIGRACION_TECNICA_PROPINAS_SQL.md:41:| `cache_manager.py` | Gestor de cache MongoDB | ~350 |
/app/docs/MIGRACION_TECNICA_PROPINAS_SQL.md:78:## 4. COLECCIONES MONGODB (SOLO CACHE)
/app/docs/MIGRACION_TECNICA_PROPINAS_SQL.md:111:5. Invalidar cache MongoDB
/app/docs/MIGRACION_TECNICA_PROPINAS_SQL.md:123:2. Verificar cache MongoDB
/app/docs/MIGRACION_TECNICA_PROPINAS_SQL.md:147:| `/api/finanzas/propinas/sincronizar` | POST | Escribe a SQL Server (antes: MongoDB) |
/app/docs/MIGRACION_TECNICA_PROPINAS_SQL.md:173:| MongoDB | `tesoreria_cuadres_z` | `propinas_cache_*` (nuevas) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:13:Este documento propone el **Lote 2** de migraciones de bypasses `db.servers.find_one()` hacia `server_registry.get_server_connection_info()`.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:31:| **Bypass actual** | `db.servers.find_one({"id": server_id})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:32:| **Dato tomado de MongoDB** | host, port, database, username, password, name |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:49:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:50:| **Dato tomado de MongoDB** | host, port, database, username, password |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:67:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` y lectura post-update |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:68:| **Dato tomado de MongoDB** | Verificación de existencia + lectura de config queries |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:74:| **NOTA** | Esta función también escribe a `db.servers.update_one()` - clasificada como C (REVISAR) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:86:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:87:| **Dato tomado de MongoDB** | name, system_type, queries_configured, query_inventario, query_ventas, query_movimientos |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:93:| **ALERTA** | ⚠️ Campos `query_*` se almacenan en MongoDB, no en EDARSAHUB. Requiere análisis adicional. |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:105:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:106:| **Dato tomado de MongoDB** | Verificación de existencia |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:123:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:124:| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:141:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:142:| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:159:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:160:| **Dato tomado de MongoDB** | name (para respuesta), verificación de existencia |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:177:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:178:| **Dato tomado de MongoDB** | host, port, database, username, password, system_type, name |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:195:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:196:| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:212:5. **Dependencias:** Evitar funciones con escrituras a MongoDB (categoría C)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE2_PLAN.md:249:2. **save_server_query (C3):** Tiene escrituras a MongoDB - clasificado como categoría C, requiere análisis adicional
/app/docs/FASE10_PROPUESTA.md:289:### 8.3 MongoDB
/app/docs/FASE10_PROPUESTA.md:338:4. Opcional: db.sec_roles.deleteOne({codigo: "ADMIN_USUARIOS"})
/app/docs/FASE15_EVIDENCIA.md:73:| Cualquier colección MongoDB | ❌ NO MODIFICADA |
/app/docs/DISENO_EDARSA_SYNC_AGENT.md:144:│  │  (MongoDB)          │    │  (MongoDB)          │                    │
/app/docs/DISENO_EDARSA_SYNC_AGENT.md:735:| Colección `sync_agent_registry` | MongoDB | Pendiente |
/app/docs/FASE7_PROPUESTA.md:431:| Colecciones MongoDB | ❌ NO SE MODIFICAN |
/app/docs/CAB_PROPINAS_TPV_ADENDA_FINAL.md:176:O en formato de índice MongoDB:
/app/docs/CAB_PROPINAS_TPV_ADENDA_FINAL.md:206:// Índice único compuesto en MongoDB
/app/docs/CAB_PROPINAS_TPV_ADENDA_FINAL.md:207:db.propinas_control.createIndex(
/app/docs/CAB_PROPINAS_TPV_ADENDA_FINAL.md:310:    config = await db.propinas_config.find_one({
/app/docs/CAB_PROPINAS_TPV_ADENDA_FINAL.md:325:    config = await db.propinas_config.find_one({
/app/docs/CAB_PROPINAS_TPV_ADENDA_FINAL.md:336:    config = await db.propinas_config.find_one({
/app/docs/CAB_PROPINAS_TPV_ADENDA_FINAL.md:496:║  ✓ NO modifica colecciones existentes en MongoDB                  ║
/app/docs/CAB_MODULO_PROPINAS_TPV.md:17:**Conclusión preliminar:** La implementación es factible como un módulo completamente desacoplado que consume datos operativos de solo lectura desde los sistemas fuente y almacena sus cálculos de auditoría exclusivamente en colecciones nuevas de MongoDB dentro de EDARSA HUB.
/app/docs/CAB_MODULO_PROPINAS_TPV.md:80:3. **ALMACENAMIENTO LOCAL:** Todos los datos calculados se guardan en MongoDB
/app/docs/CAB_MODULO_PROPINAS_TPV.md:102:│                         MongoDB                                      │
/app/docs/CAB_MODULO_PROPINAS_TPV.md:327:│  │              MongoDB (Colecciones Nuevas)              │    │
/app/docs/CAB_MODULO_PROPINAS_TPV.md:344:| RT3 | Timeout en consultas SQL por volumen de datos | Media | Medio | Implementar paginación y caché en MongoDB |
/app/docs/CAB_MODULO_PROPINAS_TPV.md:396:### 12.3 Colecciones MongoDB PROHIBIDAS de modificar estructura
/app/docs/CAB_MODULO_PROPINAS_TPV.md:421:│    4. Guarda en MongoDB colección propinas_registro                 │
/app/docs/CAB_MODULO_PROPINAS_TPV.md:742:Usuario        Frontend        Backend           MongoDB         SQL Server
/app/docs/CAB_MODULO_PROPINAS_TPV.md:775:Tesorero       Frontend        Backend           MongoDB
/app/docs/CAB_MODULO_PROPINAS_TPV.md:855:3. **SOLO nuevas colecciones** en MongoDB con prefijo `propinas_`
/app/docs/CAB_MODULO_PROPINAS_TPV.md:863:- [ ] Implementar feature flag en MongoDB para activar módulo
/app/docs/CAB_MODULO_PROPINAS_TPV.md:890:| PI1 | Sincronizar propinas de Cienfuegos | Registros creados en MongoDB |
/app/docs/CAB_MODULO_PROPINAS_TPV.md:913:// En MongoDB
/app/docs/CAB_MODULO_PROPINAS_TPV.md:914:db.propinas_config.updateOne(
/app/docs/CAB_MODULO_PROPINAS_TPV.md:928:db.propinas_registro.drop()
/app/docs/CAB_MODULO_PROPINAS_TPV.md:929:db.propinas_pagos.drop()
/app/docs/CAB_MODULO_PROPINAS_TPV.md:930:db.propinas_cuadres.drop()
/app/docs/CAB_MODULO_PROPINAS_TPV.md:952:2. Modelo de datos en MongoDB (4 colecciones)
/app/docs/DEPLOYMENT_CHECKLIST.md:54:MONGO_URL=mongodb://localhost:27017
/app/docs/DEPLOYMENT_CHECKLIST.md:178:4. Revisar credenciales SQL en MongoDB (colección `servers`)
/app/docs/ddl/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_DDL_FASE2.sql:6:-- OBJETIVO: Crear infraestructura SQL para motor de capacidades por sistema.
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:91:db.workflow_inventarios.updateOne(
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:141:from pymongo import MongoClient
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:145:    mongo_url = os.environ.get('MONGO_URL')
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:146:    client = MongoClient(mongo_url)
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:150:    backup_collection = f"workflow_inventarios_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:151:    workflows_all = list(db.workflow_inventarios.find())
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:152:    db[backup_collection].insert_many(workflows_all)
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:153:    print(f"Backup creado: {backup_collection}")
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:156:    workflows_null = list(db.workflow_inventarios.find({
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:180:        result = db.workflow_inventarios.update_one(
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:199:    restantes = db.workflow_inventarios.count_documents({
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:209:        'backup_collection': backup_collection,
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:227:null_folio_pre = db.workflow_inventarios.count_documents({'folio_inventario': None})
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:228:null_servidor_pre = db.workflow_inventarios.count_documents({'servidor_id': None})
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:238:null_folio_post = db.workflow_inventarios.count_documents({'folio_inventario': None})
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:239:null_servidor_post = db.workflow_inventarios.count_documents({'servidor_id': None})
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:246:    w = db.workflow_inventarios.find_one({'id': wid})
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:380:db.workflow_inventarios.drop()
/app/docs/PLAN_CORRECCION_HISTORICOS_NULL.md:386:    db.workflow_inventarios.replace_one({'id': wid}, original)
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:12:Este documento presenta el análisis de paridad completo entre MongoDB y EDARSAHUB para los módulos de Auth/RBAC y Servidores, junto con una propuesta de migración segura en fases que NO ha sido autorizada para ejecución.
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:16:| Categoría | MongoDB | EDARSAHUB | Paridad |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:28:- **Auth/RBAC:** Las tablas EDARSAHUB existen con estructura completa pero están VACÍAS. El sistema actual depende 100% de MongoDB para usuarios, permisos y sesiones.
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:30:- **Servidores:** Hay paridad completa de IDs (13/13 servidores MongoDB existen en EDARSAHUB). EDARSAHUB tiene 4 servidores adicionales que no están en MongoDB.
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:40:2. Backend → db.users.find_one({"email": ...}) ← MongoDB
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:46:**Dependencia:** 100% MongoDB para autenticación.
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:52:2. get_current_user() → db.users.find_one() ← MongoDB
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:53:3. resolve_user_access_context() → lee user.empresas_permitidas ← MongoDB
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:54:4. Validación de permisos contra user.sec_permisos ← MongoDB
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:57:**Dependencia:** 100% MongoDB para autorización.
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:63:2. Si falla → fallback a db.servers ← MongoDB
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:67:**Dependencia:** EDARSAHUB primario con fallback MongoDB.
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:71:## 3. PARIDAD MONGODB vs EDARSAHUB — AUTH/RBAC
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:75:| Campo MongoDB (users) | Campo EDARSAHUB (Usuario_Catalogo) | Paridad |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:96:| Campo MongoDB | Propósito | Riesgo si no se migra |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:106:### 3.3 Campos que EDARSAHUB tiene y MongoDB NO
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:123:| MongoDB (rbac_roles) | EDARSAHUB (Usuario_Roles) | Paridad |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:135:MongoDB rbac_roles:
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:154:| MongoDB (rbac_permisos) | EDARSAHUB (Usuario_PermisosRolModulo) | Paridad |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:162:- MongoDB: `{"codigo": "CARGOS_VER", "modulo": "cargos", "accion": "ver"}`
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:167:## 4. PARIDAD MONGODB vs EDARSAHUB — SERVIDORES/UNIDADES/SUCURSALES
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:174:| IDs solo en MongoDB | 0 |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:183:**Conclusión:** La paridad de servidores es BUENA. MongoDB es subconjunto de EDARSAHUB.
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:187:| MongoDB (sec_unidades_negocio) | EDARSAHUB (Unidades_Negocio) |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:195:| Campo MongoDB (servers) | Campo EDARSAHUB (Servidores_Conexiones) | Paridad |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:255:| R-P1-002 | Perder fallback MongoDB sin validar EDARSAHUB completo | TODOS |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:265:| R-P2-003 | 4 servidores en EDARSAHUB no visibles si código lee MongoDB | Configuración |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:271:| R-P3-001 | scheduler_job_log perdería histórico si se elimina MongoDB | Monitoreo |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:278:### 7.1 Endpoints que leen MongoDB para Auth/Users
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:282:| `POST /auth/login` | `server.py` | ~6375 | `db.users` |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:283:| `GET /auth/me` | `security.py` | 265 | `db.users` |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:284:| `GET /dashboard/metrics` | `server.py` | 6280 | `db.users` |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:285:| `PUT /users/{id}/permissions` | `server.py` | 13182-13202 | `db.users` |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:286:| `GET /usuarios/listar` | `server.py` | 13963-13971 | `db.users`, `db.roles` |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:287:| `POST /auth/forgot-password` | `password_reset.py` | - | `db.users` |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:288:| `POST /auth/reset-password` | `password_reset.py` | - | `db.users` |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:290:### 7.2 Endpoints que leen MongoDB para Servers
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:294:| `GET /servers` | `server.py` | 1186 | `db.servers` (fallback) |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:295:| `POST /servers` | `server.py` | 1129 | `db.servers` |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:296:| `PUT /servers/{id}` | `server.py` | 1239 | `db.servers` |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:297:| `DELETE /servers/{id}` | `server.py` | 1297 | `db.servers` |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:298:| `GET /servers/{id}/ping` | `server.py` | 1352 | `db.servers` |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:312:### 8.1 Archivos que usan db.users (17 archivos)
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:333:### 8.2 Archivos que usan db.servers (38 archivos)
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:370:| **Login** | Punto único de entrada | MongoDB users (NO TOCAR AÚN) |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:389:│  MongoDB ────────────────────────────► Sistema                  │
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:396:│  MongoDB ────────────────────────────► Sistema                  │
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:404:│  MongoDB ────────────────────────────► Sistema                  │
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:413:│  MongoDB ────────────────────────────► Sistema (mayoría)        │
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:424:│  MongoDB ◄──── fallback automático si EDARSAHUB falla           │
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:432:│  MongoDB (desactivado, backup histórico)                        │
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:450:    user = await db.users.find_one({"email": email})  # MongoDB original
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:465:        logger.warning(f"EDARSAHUB auth failed, falling back to MongoDB: {e}")
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:467:    # Fallback a MongoDB
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:468:    return await db.users.find_one({"email": email})
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:479:| A7 | ⚠️ Parcial | Restaurar MongoDB desde backup |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:489:| T-01 | Verificar todos los usuarios MongoDB existen en EDARSAHUB | 15/15 usuarios |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:529:| T-40 | Cambiar USE_EDARSAHUB_AUTH=false restaura MongoDB | Login funciona |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:541:| **A0** | Backup completo de MongoDB collections auth | NINGUNO | ✅ |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:544:| **A3** | Validación paralela login MongoDB vs EDARSAHUB (comparación) | BAJO | ✅ |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:547:| **A6** | Mantener MongoDB como fallback (2-4 semanas) | BAJO | ✅ |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:548:| **A7** | Retirar dependencia MongoDB (después de observación) | MEDIO | ⚠️ Parcial |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:556:| **B0** | Backup de MongoDB servers collection | NINGUNO | ✅ |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:558:| **B2** | Sincronizar 4 servidores faltantes de EDARSAHUB → MongoDB | BAJO | ✅ |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:559:| **B3** | Eliminar fallback MongoDB en server_registry.py | MEDIO | ✅ |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:561:| **B5** | Retiro gradual de MongoDB servers | MEDIO | ⚠️ Parcial |
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:571:Este documento presenta el análisis completo de paridad entre MongoDB y EDARSAHUB para Auth/RBAC y Servidores. Los hallazgos principales son:
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:573:1. **Auth/RBAC:** EDARSAHUB tiene tablas completas pero VACÍAS. El sistema depende 100% de MongoDB. Migración requiere poblar datos y agregar campos faltantes (empresas_permitidas).
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:575:2. **Servidores:** Paridad casi completa (13/17 IDs coinciden). EDARSAHUB ya es primario con fallback MongoDB funcional.
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:591:3. Ejecutar FASE A0 (backup de MongoDB)
/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md:599:- [ ] **AUTORIZACIÓN FASE A0:** Ejecutar backup de MongoDB auth collections
/app/docs/FASE14_PROPUESTA.md:276:        return await db.users.find({'sucursal_id': {'$in': alcance['sucursales_ids']}})
/app/docs/FASE14_PROPUESTA.md:277:    return await db.users.find({})  # GLOBAL
/app/docs/FASE14_PROPUESTA.md:289:| MongoDB users | +campo `sec_roles_alcance` | N/A |
/app/docs/HOMOLOGACION_CACHE_COMERCIAL.md:96:## 6. COLECCIÓN MONGODB
/app/docs/HOMOLOGACION_CACHE_COMERCIAL.md:99:Collection: comercial_cache
/app/docs/FASE_3C3_CORE_SECRET_ENCRYPTION.md:74:| `sync_core_to_mongo()` | Sincroniza cambios a MongoDB |
/app/docs/FASE_3C3_CORE_SECRET_ENCRYPTION.md:114:    ✓ MongoDB sincronizado
/app/docs/FASE_3C3_CORE_SECRET_ENCRYPTION.md:118:    ✓ MongoDB sincronizado
/app/docs/FASE_3C3_CORE_SECRET_ENCRYPTION.md:123:MongoDB sincronizado: 2
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_v1.md:69:| R-004 | MongoDB solo para cache temporal | ALTA |
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_v1.md:216:| `execute_sql_query()` | `core/db.py` | ✅ REUTILIZAR |
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_v1.md:436:### 6.3 Colecciones MongoDB (CACHE TEMPORAL)
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_v1.md:1165:### FASE 1: Motor de Detección (3-5 días)
/app/docs/POOL_POISON_FIX_01_REPORT.md:6:**Archivo:** `/app/backend/core/db.py`  
/app/docs/POOL_POISON_FIX_01_REPORT.md:21:**Archivo:** `/app/backend/core/db.py`  
/app/docs/POOL_POISON_FIX_01_REPORT.md:133:Para revertir el cambio, restaurar el bloque original en `/app/backend/core/db.py`:
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:54:**Verificar en MongoDB:**
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:57:db.inventarios_procesados_auto.countDocuments({})
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:60:db.inventarios_procesados_auto.aggregate([
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:65:db.inventarios_procesados_auto.find().sort({fecha_deteccion: -1}).limit(5)
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:77:**Verificar en MongoDB:**
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:80:db.workflow_inventarios.find().sort({fecha_creacion: -1}).limit(5).pretty()
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:83:db.workflow_inventarios.find({
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:103:**Verificar en MongoDB:**
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:106:db.detalle_diferencias.find().sort({fecha_creacion: -1}).limit(10).pretty()
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:109:db.detalle_diferencias.find({
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:135:db.inventarios_procesados_auto.aggregate([
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:158:**Verificar en MongoDB:**
/app/docs/INVENTARIOS_DETECTOR_VALIDACION.md:160:db.scheduler_job_logs.find({job_name: "inventarios_detector"}).sort({started_at: -1}).limit(5).pretty()
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:16:- **MongoDB** (colección `api_connections_cache`)
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:21:- Si MongoDB falla, la operación no se bloquea
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:25:EDARSAHUB SQL → MongoDB (caché)
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:36:| `/app/backend/modules/api_connections/routes.py` | **Reescrito** - Manejo correcto de errores SQL vs MongoDB |
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:44:| `create_api_connection()` | INSERT en SQL → Log → Caché MongoDB |
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:45:| `update_api_connection()` | UPDATE en SQL → Log → Caché MongoDB |
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:54:2. ✅ **MongoDB solo como caché/log/estado auxiliar**
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:56:4. ✅ **Después de SQL, opcionalmente actualiza MongoDB caché**
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:57:5. ✅ **Si MongoDB falla, no impide guardar en SQL**
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:58:6. ✅ **Si SQL falla, no guarda en MongoDB**
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:92:### Sincronización SQL → MongoDB
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:98:### Verificación MongoDB Caché
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:100:db.api_connections_cache.find()
/app/docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md:122:| POST | /api/api-connections/sync-cache | Sincroniza SQL → MongoDB |
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:207:db.kpis_comercial.createIndex(
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:235:db.kpis_comercial.createIndex(
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:241:db.kpis_comercial.createIndex(
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:247:db.kpis_comercial.createIndex(
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:253:db.kpis_comercial.createIndex(
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:259:db.kpis_comercial.createIndex(
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:303:    existing = await db.kpis_comercial.find_one(filter_key)
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:331:        await db.kpis_comercial.insert_one(new_doc)
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:378:    await db.kpis_comercial.update_one(filter_key, update_doc)
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:470:    existing = await db.kpis_comercial.find_one(filter_key)
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:495:    await db.kpis_comercial.update_one(
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:564:db.kpis_comercial.find({
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:571:db.kpis_comercial.aggregate([
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:583:db.kpis_comercial.find({
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:601:    collection = db.kpis_comercial
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:604:    await collection.create_index(
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:616:    await collection.create_index(
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:621:    await collection.create_index(
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:626:    await collection.create_index(
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:631:    await collection.create_index(
/app/docs/MACROFASE2_ESQUEMA_KPIS_CONSOLIDADOS.md:636:    await collection.create_index(
/app/docs/BACKEND_COMPLEXITY_REFACTOR_PLAN.md:185:- Eventos deben guardarse en SQL y/o MongoDB
/app/docs/reports/FIX_EXPLORADOR_BD_MULTISISTEMA_TABLAS.md:154:## 12. CONFIRMACIÓN DE NO MONGODB
/app/docs/reports/FIX_EXPLORADOR_BD_MULTISISTEMA_TABLAS.md:156:✅ **CONFIRMADO**: No se usa MongoDB para cargar tablas.
/app/docs/reports/FIX_EXPLORADOR_BD_MULTISISTEMA_TABLAS.md:228:| 11 | No se usa MongoDB | ✅ |
/app/docs/reports/FASE_1C_3I_H_LISTAS_COMPETIDORES_FILTRO_IA_BENCHMARK.md:16:- ✅ Motor de Precios IA y Benchmark operativos
/app/docs/reports/FASE_1C_3I_H_LISTAS_COMPETIDORES_FILTRO_IA_BENCHMARK.md:290:## 10. Confirmación CERO MongoDB
/app/docs/reports/FASE_1C_3I_H_LISTAS_COMPETIDORES_FILTRO_IA_BENCHMARK.md:296:- ✅ Footer de la aplicación muestra "CERO MongoDB"
/app/docs/reports/FASE_1C_3I_H_LISTAS_COMPETIDORES_FILTRO_IA_BENCHMARK.md:297:- ✅ Backend no usa MongoDB para esta funcionalidad
/app/docs/reports/FASE_1C_3I_H_LISTAS_COMPETIDORES_FILTRO_IA_BENCHMARK.md:349:| CERO MongoDB | ✅ |
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE4_RESOLVER_REPORTE.md:25:- ✅ No se usó MongoDB
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE4_RESOLVER_REPORTE.md:42:- `core.db.execute_sql_query` (conexión EDARSAHUB existente)
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE4_RESOLVER_REPORTE.md:278:## 10. CONFIRMACIÓN NO MONGODB
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE4_RESOLVER_REPORTE.md:280:El resolver **NO consulta MongoDB** en ningún momento:
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE4_RESOLVER_REPORTE.md:282:- No importa módulos de MongoDB
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE4_RESOLVER_REPORTE.md:283:- No tiene configuración de MongoDB
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE4_RESOLVER_REPORTE.md:369:- ✅ No MongoDB
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:1:# COMPRAS-MONGO-001-F1: Migración Parámetros de Compras a EDARSAHUB SQL
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:12:Migrar los parámetros de compras (`compras_params`) de MongoDB a EDARSAHUB SQL Server.
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:18:- MongoDB ya no es fuente productiva para parámetros de compras
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:26:| Fuente de datos | MongoDB colección `compras_params` |
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:102:# ANTES (MongoDB)
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:107:    return await db.compras_params.find_one(...)
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:119:params = await db.parametros_compra.find_one(...)  # ❌ MongoDB stub
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:211:### `compras_params` ya no usa MongoDB:
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:219:### No hay referencias activas a `db.compras_params`:
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:228:## 10. CONFIRMACIÓN CERO MONGODB PRODUCTIVO
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:235:| No hay `db.compras_params.find_one()` activo | ✅ |
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:236:| No hay `db.parametros_compra` activo | ✅ |
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:238:**CONFIRMADO**: MongoDB ya no es fuente productiva para parámetros de compras.
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:257:| Datos históricos en MongoDB | Baja | No hay datos históricos críticos - eran defaults |
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:258:| Tracking de pedidos aún usa MongoDB | P1 | Fase posterior |
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:264:### P1: COMPRAS-MONGO-001-F2 — Migración Tracking de Pedidos
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:302:| MongoDB no es fuente productiva | ✅ |
/app/docs/reports/COMPRAS_MONGO_001_F1_PARAMETROS_SUCURSAL_SQL.md:309:**FASE COMPRAS-MONGO-001-F1 COMPLETADA**
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE3_SEED_EJECUCION.md:249:| MongoDB usado | ❌ NO |
/app/docs/reports/BACKFILL_SYNC_VENTAS_PORHORA_2026_05_07.md:200:| No se usó MongoDB como fuente | ✅ CUMPLIDO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:1:# FASE 4A — Diagnóstico Pasivo de Reglas Vivas de Negocio y Dependencias MongoDB
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:12:- **775 líneas** con referencias a MongoDB/Motor/PyMongo
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:13:- **568 líneas** con acceso directo a colecciones (`db.`)
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:14:- **41 archivos** importan activamente motor/pymongo
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:17:- **~50 colecciones MongoDB** referenciadas
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:20:### Módulos con Mayor Dependencia MongoDB:
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:34:- **FASE2_OPERATIVO:** DEPENDENCIA FUERTE de MongoDB
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:35:- **RBAC repository:** DEPENDENCIA FUERTE de MongoDB
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:39:## 2. ESTADO GENERAL DE MONGODB EN EL SISTEMA
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:44:from motor.motor_asyncio import AsyncIOMotorClient
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:45:client = AsyncIOMotorClient(mongo_url)
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:49:- Variable: `MONGO_URL` desde `.env`
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:62:## 3. MATRIZ COMPLETA DE DEPENDENCIAS MONGODB ACTIVAS
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:68:| `db.servers` | 174 | Config | **MIGRADO** (comentarios/scripts) | BAJO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:69:| `db.users` | 43 | Auth | **MIGRADO PARCIAL** | MEDIO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:70:| `db.informes_auditoria` | 26 | Auditoría | ACTIVO | MEDIO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:71:| `db.tareas_inventario` | 20 | Operativo | **ACTIVO** | ALTO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:72:| `db.portal_suppliers` | 16 | Portal | ACTIVO | MEDIO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:73:| `db.nomina_ciclos` | 15 | Nómina | ACTIVO | MEDIO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:74:| `db.kpis_comercial` | 15 | Analítico | **ACTIVO** | ALTO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:75:| `db.solicitudes_catalogos` | 14 | Catálogos | ACTIVO | MEDIO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:76:| `db.workflow_inventarios` | 13 | Operativo | **ACTIVO** | ALTO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:77:| `db.server_sucursales_config` | 12 | Config | Migración parcial | BAJO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:78:| `db.comercial_cache` | 12 | Cache | **ACTIVO** | ALTO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:79:| `db.consultas_custom` | 11 | Queries | ACTIVO | BAJO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:80:| `db.sec_bitacora_admin` | 10 | Seguridad | ACTIVO | MEDIO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:81:| `db.notificaciones_log` | 10 | Notificaciones | ACTIVO | BAJO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:82:| `db.tareas_sistema` | 9 | Sistema | ACTIVO | MEDIO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:83:| `db.rbac_roles` | 9 | RBAC | **ACTIVO** | ALTO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:84:| `db.empresas` | 9 | Config | **MIGRADO** | BAJO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:85:| `db.rbac_usuarios_roles` | 8 | RBAC | **ACTIVO** | ALTO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:86:| `db.queries` | 7 | Queries | ACTIVO | BAJO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:87:| `db.rbac_permisos` | 6 | RBAC | **ACTIVO** | ALTO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:88:| `db.rbac_audit_log` | 5 | Auditoría | **ACTIVO** | MEDIO |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:119:## 4. MATRIZ DE DEPENDENCIAS MONGODB LEGACY/FALLBACK
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:133:/app/backend/scripts/reconcile_servers_sql_mongo.py
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:146:### 5.1 REGLAS EN RBAC MongoDB
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:150:| Permisos por módulo | `db.rbac_permisos` | Configuración |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:151:| Roles del sistema | `db.rbac_roles` | Configuración |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:152:| Asignación usuario-rol-sucursal | `db.rbac_usuarios_roles` | Relación |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:153:| Auditoría RBAC | `db.rbac_audit_log` | Log |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:161:| Flujos de inventario | `db.workflow_inventarios` | Proceso |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:162:| Tareas pendientes | `db.tareas_inventario` | Operativo |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:163:| Configuración operativa | `db.configuracion_operativa` | Config |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:164:| SLAs y alertas | `db.alertas_sistema` | Monitoreo |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:172:| KPIs cacheados | `db.comercial_cache` | Cache |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:173:| KPIs históricos | `db.kpis_comercial` | Analítico |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:181:| Módulo | Dependencia MongoDB | Estado | Prioridad Migración |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:196:### Endpoints con MongoDB Activo:
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:228:| Pantalla/Menú | Módulo Backend | Dependencia MongoDB |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:240:## 10. COLECCIONES MONGODB AÚN UTILIZADAS
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:278:| Colección MongoDB | Tabla SQL Sugerida | Existe |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:298:| RBAC MongoDB | **CRÍTICO** | Login y permisos dependen de esto |
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:320:### P0 - CRÍTICO (Bloquea eliminación MongoDB):
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:321:1. **RBAC MongoDB** (`rbac_permisos`, `rbac_roles`, `rbac_usuarios_roles`)
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:347:## 14. DEPENDENCIAS QUE BLOQUEAN ELIMINACIÓN FUTURA DE MONGODB
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:351:   - Todas las operaciones RBAC usan MongoDB
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:352:   - Sin migración, no se puede eliminar MongoDB
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:358:3. **`core/db.py`**
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:359:   - Inicializa conexión MongoDB global
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:413:### MongoDB aún es REQUERIDO para:
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:419:### MongoDB ya NO es requerido para:
/app/docs/reports/FASE_4A_DIAGNOSTICO_REGLAS_VIVAS_MONGODB.md:428:### Para eliminar MongoDB completamente se requiere:
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:15:# - Actualizar 9 usuarios existentes con PublicUUID y MongoLegacyID desde MongoDB
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:22:SET PublicUUID = <uuid_mongo>,
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:23:    MongoLegacyID = <objectid_mongo>,
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:27:  AND (PublicUUID IS NULL OR MongoLegacyID IS NULL)
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:32:    Nombre, Activo, FechaAlta, CreatedBy, PublicUUID, MongoLegacyID
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:36:INSERT INTO Usuario_MigracionMongoTrace (...)
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:43:| Idempotente | UPDATE solo si PublicUUID/MongoLegacyID es NULL |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:49:| Trazabilidad | INSERT en Usuario_MigracionMongoTrace |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:55:| UsuarioID | Email | Acción | PublicUUID | MongoLegacyID |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:57:| 1 | admin@edarsa.com | UPDATE_UUID_AND_MONGOID | F648DD3F-... | 69d88ca7cca4... |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:58:| 2 | admin@inventario.com | UPDATE_UUID_AND_MONGOID | 0DA77B7B-... | 69e4576bbfb5... |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:59:| 3 | carlosruz@edarsa.com.mx | UPDATE_UUID_AND_MONGOID | A5E56ED0-... | 69e4576bbfb5... |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:60:| 4 | noxte@alpyc.com | UPDATE_UUID_AND_MONGOID | A72B325B-... | 69e4576bbfb5... |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:61:| 5 | auditoria@edarsa.com.mx | UPDATE_UUID_AND_MONGOID | E200DE9E-... | 69e4576bbfb5... |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:62:| 6 | almacen@cienfuegos.mx | UPDATE_UUID_AND_MONGOID | 30702651-... | 69e4576bbfb5... |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:63:| 7 | administracion@cienfuegos.mx | UPDATE_UUID_AND_MONGOID | 57DBB5AD-... | 69e4576bbfb5... |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:64:| 8 | ricardo@edarsa.com.mx | UPDATE_UUID_AND_MONGOID | 1E18A085-... | 69e6f703a9e9... |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:65:| 9 | david.ricardez@cienfuegos.mx | UPDATE_UUID_AND_MONGOID | F3BA4A2F-... | 69e75b91bfb9... |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:67:**Resultado:** 9 usuarios actualizados con trazabilidad MongoDB completa.
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:73:| UsuarioID | Email | Role (MongoDB) | PublicUUID | MongoLegacyID |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:105:**NO MIGRAR** - El usuario no tiene `id` (PublicUUID) en MongoDB.
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:114:- **Opción A:** Crear manualmente en MongoDB con UUID y luego migrar
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:140:| 11 | carlos@alpuntoycoma.mx | $2b$12$... | MongoDB (copiado) |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:141:| 12 | eduardo@alpuntoycoma.mx | $2b$12$... | MongoDB (copiado) |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:160:## 8. VALIDACIÓN MongoLegacyID
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:165:| Con MongoLegacyID | 11 |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:166:| Sin MongoLegacyID | 0 |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:168:**RESULTADO:** ✓ Todos los usuarios tienen trazabilidad MongoDB.
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:174:### 9.1 MongoDB
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:189:| Con MongoLegacyID | 0 | 11 | +11 poblados |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:204:| Usuario_MigracionMongoTrace | 9 | 11 |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:222:✓ MongoDB sigue siendo fuente de login
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:223:✓ Usuario admin@inventario.com encontrado en MongoDB
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:224:✓ UUID en MongoDB: 0da77b7b-fe88-4e23-98bc-9cbf543d5ee3
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:225:✓ Usuario carlos@alpuntoycoma.mx existe en MongoDB (nuevo, puede hacer login)
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:238:- [x] MongoDB sigue siendo fuente de autenticación
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:259:Mapeo propuesto de roles MongoDB → SQL:
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:261:| Role MongoDB | RolID SQL | CodigoRol SQL |
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:271:2. Mapear `user.role` de MongoDB al `RolID` correspondiente en SQL
/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md:292:| MongoDB sigue siendo fuente de login | ✓ |
/app/docs/reports/FASE_SYNC_3A_R2_PORDIASEMANA_CONFIG_PENDIENTES_REPORTE.md:174:| No MongoDB | ✅ |
/app/docs/reports/INCIDENTE_CRITICO_VENTAS_DIA_DOBLE_RUTA_FECHAOPERACION_ANTI_CERO.md:135:| msdb.dbo.sysjobs | ❌ DENEGADO |
/app/docs/reports/INCIDENTE_CRITICO_VENTAS_DIA_DOBLE_RUTA_FECHAOPERACION_ANTI_CERO.md:193:FROM msdb.dbo.sysjobs j WHERE j.enabled = 1;
/app/docs/reports/INCIDENTE_CRITICO_VENTAS_DIA_DOBLE_RUTA_FECHAOPERACION_ANTI_CERO.md:197:FROM msdb.dbo.sysjobs j
/app/docs/reports/INCIDENTE_CRITICO_VENTAS_DIA_DOBLE_RUTA_FECHAOPERACION_ANTI_CERO.md:198:INNER JOIN msdb.dbo.sysjobsteps s ON j.job_id = s.job_id
/app/docs/reports/CRM_ENTERPRISE_DIAGNOSTICO_NO_DUPLICIDAD.md:17:- ✅ **Existe motor de actividades** (Usuario_LogActividades) - reutilizable
/app/docs/reports/CRM_ENTERPRISE_DIAGNOSTICO_NO_DUPLICIDAD.md:61:| `Usuario_LogActividades` | Motor de actividades | **EVALUAR EXTENSIÓN** |
/app/docs/reports/DIAGNOSTICO_TABLERO_EJECUTIVO_VENTAS_MAYO_2026_CIENFUEGOS_ORIGEN.md:272:Fuente: EDARSAHUB (NO SQL vivo, NO MongoDB)
/app/docs/reports/DIAGNOSTICO_TABLERO_EJECUTIVO_VENTAS_MAYO_2026_CIENFUEGOS_ORIGEN.md:277:## 8. CONFIRMACIÓN: ¿SE USA MONGODB?
/app/docs/reports/DIAGNOSTICO_TABLERO_EJECUTIVO_VENTAS_MAYO_2026_CIENFUEGOS_ORIGEN.md:279:### ✅ CONFIRMADO: NO se usa MongoDB como fuente de datos
/app/docs/reports/VALIDACION_CONEXION_EDARSAHUB_PERMISOS_MSDB.md:73:## 5. ERROR EXACTO AL CONSULTAR msdb.dbo.sysjobs
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:12:El endpoint `GET /api/users` fallaba con **HTTP 500** porque la función `get_all_users()` en `/app/backend/modules/auth/repository.py` todavía consultaba MongoDB (`db.users.find()`) después de la migración SQL-first de Auth/RBAC en FASE 2-G.
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:16:- `get_all_users()` seguía usando MongoDB
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:17:- MongoDB retornaba usuarios con campos `allowed_warehouses` conteniendo valores `None`
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:65:## 5. Respuesta ANTES (MongoDB - Error 500)
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:126:## 8. Referencias MongoDB Encontradas (Eliminadas)
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:149:- Eliminada consulta a MongoDB `db.users.find()`
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:153:- NO hace fallback a MongoDB si falla SQL
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:156:- Eliminada consulta a MongoDB
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:180:| 15 | No se reactivó MongoDB | ✅ Confirmado |
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:188:| Campos legacy (`allowed_servers`, `allowed_sucursales`, `allowed_warehouses`) devuelven vacíos | **Baja** | Estos campos eran heredados de MongoDB y no están migrados a SQL. El frontend los maneja como opcionales. |
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:189:| `create_user()`, `update_user()`, `deactivate_user()` siguen usando MongoDB | **Media** | Fuera del alcance de este bug fix. Operaciones de escritura de usuarios deben migrarse en fase futura. |
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:190:| `find_user_by_email()` y `find_user_by_id()` siguen usando MongoDB (para login) | **Media** | Login usa MongoDB para validación de password. Migración pendiente pero no bloquea este fix. |
/app/docs/reports/BUG_AUTH_USERS_001_ERROR_CARGAR_USUARIOS_SQL_FIRST.md:198:La pestaña "Usuarios y Roles" → "Usuarios" ahora carga correctamente 11 usuarios productivos desde EDARSAHUB SQL sin exponer información sensible y sin reactivar MongoDB como fuente primaria de datos de usuarios.
/app/docs/reports/FASE_4_ENDPOINTS_CONSULTAS_SQL_SQLFIRST.md:304:| No se tocó MongoDB | ✅ Catálogo leído desde EDARSAHUB |
/app/docs/reports/INCIDENTE_EDARSAHUB_SQL_DESAPARECIDO_MENU_SERVIDORES_CORRECCION.md:81:## INFORMACIÓN SOBRE MONGODB
/app/docs/reports/INCIDENTE_EDARSAHUB_SQL_DESAPARECIDO_MENU_SERVIDORES_CORRECCION.md:83:### ¿El endpoint GET /api/servers usa MongoDB actualmente?
/app/docs/reports/INCIDENTE_EDARSAHUB_SQL_DESAPARECIDO_MENU_SERVIDORES_CORRECCION.md:84:**SÍ, como fallback**. La función `list_servers` tiene `allow_mongo_fallback=True`.
/app/docs/reports/INCIDENTE_EDARSAHUB_SQL_DESAPARECIDO_MENU_SERVIDORES_CORRECCION.md:86:### ¿Existe fallback MongoDB en la ruta de servidores?
/app/docs/reports/INCIDENTE_EDARSAHUB_SQL_DESAPARECIDO_MENU_SERVIDORES_CORRECCION.md:87:**SÍ**. Si EDARSAHUB SQL falla, consulta MongoDB como respaldo.
/app/docs/reports/INCIDENTE_EDARSAHUB_SQL_DESAPARECIDO_MENU_SERVIDORES_CORRECCION.md:89:### ¿MongoDB contiene registros legacy de servidores?
/app/docs/reports/INCIDENTE_EDARSAHUB_SQL_DESAPARECIDO_MENU_SERVIDORES_CORRECCION.md:92:### ¿Esos registros MongoDB participan en la respuesta actual?
/app/docs/reports/INCIDENTE_EDARSAHUB_SQL_DESAPARECIDO_MENU_SERVIDORES_CORRECCION.md:98:### ¿Se detectó dependencia activa de MongoDB?
/app/docs/reports/INCIDENTE_EDARSAHUB_SQL_DESAPARECIDO_MENU_SERVIDORES_CORRECCION.md:99:**NO para este incidente**. MongoDB solo actúa como fallback legacy.
/app/docs/reports/INCIDENTE_EDARSAHUB_SQL_DESAPARECIDO_MENU_SERVIDORES_CORRECCION.md:107:| No se tocó MongoDB | ✅ |
/app/docs/reports/historical_load_24_months_dry_run.json:8:  "mongo_role": "checkpoint_log_only",
/app/docs/reports/historical_load_24_months_dry_run.json:20:  "mongo_final_inserted": 0,
/app/docs/reports/historical_load_24_months_dry_run.json:37:      "mongo_role": "checkpoint_log_only",
/app/docs/reports/historical_load_24_months_dry_run.json:39:      "planned_mongo_final_write": false
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:12:Preparar el cambio a SQL-first sin activarlo todavía, validando que el nuevo repositorio SQL puede reemplazar a MongoDB sin romper login, JWT, permisos, empresas, roles ni visibilidad de módulos.
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:28:| `compare_user_mongo_vs_sql_passive()` | Comparación pasiva entre MongoDB y SQL |
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:32:- `get_current_user()` - Sigue usando MongoDB
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:33:- `get_current_user_dual()` - Sigue usando MongoDB
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:50:| `false` (actual) | MongoDB es la fuente productiva. SQL solo se usa para comparación pasiva. |
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:51:| `true` (FASE 2-E) | SQL sería la fuente principal con fallback a MongoDB. **NO ACTIVAR sin autorización.** |
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:62:## 4. Comparación MongoDB vs SQL por Usuario
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:65:| Email | ID MongoDB | ID SQL | Match |
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:82:| Email | Rol MongoDB | Rol SQL | Mapeo |
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:97:| Email | Rol | Empresas Mongo | Empresas SQL | Estado |
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:124:**Comportamiento correcto:** `ricardo@edarsa.com.mx` tiene 0 empresas en MongoDB pero resuelve 5 en SQL gracias a la regla SUPERADMIN.
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:130:Los siguientes usuarios **NO tienen `empresas_permitidas`** en MongoDB ni en SQL:
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:163:### MongoDB sigue siendo fuente productiva:
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:166:- Todas las consultas de autenticación van a `db.users`
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:176:| SUPERADMIN sin empresas en Mongo | Resuelto con regla implícita | Mitigado |
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:185:- `auth_source` (MONGODB_CURRENT)
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:205:| 4 | PublicUUID == MongoDB id (normalizado) | ✅ |
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:220:   - Si SQL falla, fallback a MongoDB
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:242:| El sistema sigue autenticando productivamente con MongoDB | ✅ |
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:247:| Hay comparación pasiva MongoDB vs SQL | ✅ |
/app/docs/reports/FASE2D1_PREFLIGHT_AUTH_SQL_FIRST.md:253:*MongoDB sigue siendo la fuente productiva. SQL-first listo pero apagado.*  
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:1:# FASE 2-G: Eliminación de Fallback MongoDB en Auth/RBAC
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:11:Se eliminó el fallback MongoDB del flujo de autenticación. EDARSAHUB SQL es ahora la **única fuente de autenticación** para usuarios productivos.
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:17:| MONGODB_FALLBACK | 0 (eliminado) |
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:27:| `/app/backend/core/security.py` | Eliminado fallback MongoDB de `get_current_user()` y `get_current_user_dual()` |
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:33:| `get_current_user()` | SQL-first con fallback MongoDB | SQL-only |
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:34:| `get_current_user_dual()` | SQL-first con fallback MongoDB | SQL-only |
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:51:  SQL   MongoDB
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:60: OK  MongoDB Fallback ← ELIMINADO
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:90:**Sin fallback a MongoDB.**
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:94:## 5. Referencias MongoDB Eliminadas del Flujo Auth
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:99:| `MONGODB_FALLBACK` como auth_source | ✅ ELIMINADO |
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:101:| Fallback a `db.users` en `get_current_user()` | ✅ ELIMINADO |
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:102:| Fallback a `db.users` en `get_current_user_dual()` | ✅ ELIMINADO |
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:106:## 6. Referencias MongoDB Residuales (Fuera de Auth)
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:173:### db.users en Auth:
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:175:$ grep -R "db.users" /app/backend/core/security.py
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:178:$ grep -R "db.users" /app/backend/modules/auth/
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:179:/app/backend/modules/auth/password_reset.py:    user = db.users.find_one(...)  # Fuera de flujo principal
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:180:/app/backend/modules/auth/context_service.py:    user = await db.users.find_one(...)  # Fuera de flujo principal
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:183:### MONGODB_FALLBACK:
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:185:$ grep -R "MONGODB_FALLBACK" /app/backend/core/ /app/backend/modules/auth/
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:212:### Si se necesita revertir a fallback MongoDB:
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:222:- `/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md` (documentación del flujo anterior)
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:231:| password_reset.py usa MongoDB | Media | Deuda técnica para fase futura. No afecta login. |
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:232:| context_service.py usa MongoDB | Media | Deuda técnica para fase futura. No afecta login. |
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:242:✅ Fallback MongoDB eliminado de flujo principal  
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:250:1. Migrar `db.empresas` a `Sistema_Empresas`
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:251:2. Migrar `db.sucursales` a `Sistema_Sucursales`
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:252:3. Actualizar endpoints que leen de MongoDB
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:253:4. Mantener Sistema_EmpresasMongoMap como puente
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:261:| Auth/RBAC ya no usa MongoDB fallback | ✅ |
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:264:| No existe MONGODB_FALLBACK productivo | ✅ |
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:277:La migración de Auth/RBAC de MongoDB a EDARSAHUB SQL ha sido completada exitosamente:
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:286:- ✅ **Fallback MongoDB eliminado**
/app/docs/reports/FASE2G_ELIMINACION_FALLBACK_MONGODB_AUTH.md:293:*MongoDB ya no es parte del flujo de autenticación productivo.*
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:11:La migración base Auth/RBAC de MongoDB hacia EDARSAHUB SQL ha sido validada integralmente. Los datos son consistentes, no hay duplicados críticos, y los mapeos son correctos.
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:21:| MongoDB como fuente | Sigue activo |
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:24:**Usuarios sin empresas en SQL:** 4 (ninguno tenía empresas en MongoDB)
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:28:## 2. CONTEOS MONGODB VS SQL
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:32:| Métrica | MongoDB | SQL | Diferencia |
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:40:| Rol MongoDB | Cantidad | Rol SQL | Cantidad |
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:48:**Nota:** 2 SuperAdministradores MongoDB son @test.com y no fueron migrados.
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:52:| Métrica | MongoDB | SQL | Estado |
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:62:| UID | Email | SQL | Mongo | UUID | Hash | Rol SQL | Rol Mongo | Empresas |
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:78:## 4. MATRIZ ROL MONGODB → ROL SQL
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:80:| Rol MongoDB | RolID SQL | Código SQL | Usuarios Migrados | Validación |
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:90:## 5. MATRIZ EMPRESAS MONGODB → SQL
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:92:| UUID MongoDB | Código | EmpresaID SQL | Asignaciones | Validación |
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:122:| Email | Rol Mongo | UUID | Razón | Decisión |
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:130:| UID | Email | Rol SQL | Empresas Mongo | Riesgo SQL-first | Recomendación |
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:137:**Análisis:** Ninguno de estos 4 usuarios tenía `empresas_permitidas` en MongoDB, por lo que su situación actual en SQL es **consistente** con MongoDB.
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:166:1. En el código actual de MongoDB, `get_user_empresas_permitidas()` ya verifica:
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:195:- [x] MongoLegacyID presentes (11/11)
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:207:- [x] 4 usuarios sin empresas documentados (consistente con MongoDB)
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:219:4. ✓ MongoDB sigue como fuente (no regresión)
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:241:| Sistema_EmpresasMongoMap | 5 | Sin cambios |
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:252:- [x] Login sigue funcionando (MongoDB)
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:253:- [x] MongoDB sigue siendo fuente de autenticación
/app/docs/reports/FASE2C_VALIDACION_POST_MIGRACION_AUTH_RBAC_SQL.md:263:Los datos son consistentes, no hay duplicados críticos, y todos los mapeos son correctos. Los 4 usuarios sin empresas en SQL reflejan su estado original en MongoDB.
/app/docs/reports/FIX_PROYECCION_MENSUAL_DIAS_OPERATIVOS.md:146:| No MongoDB | ✅ |
/app/docs/reports/FIX_PROYECCION_MENSUAL_DIAS_OPERATIVOS.md:169:| MongoDB | ✅ No se usa |
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:13:El **Tablero Ejecutivo Comercial** actualmente **NO LEE DE EDARSAHUB** para obtener KPIs de ventas. En su lugar, consulta directamente los servidores SQL de cada sucursal en tiempo real, con fallback a **MongoDB (cache)** cuando la conexión falla.
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:18:3. Se usa un **fallback a MongoDB** con datos históricos
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:44:│      │            └──► Fallback: MongoDB (servers)                      │
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:64:│      │               └─► MongoDB CACHE (kpis_cache)                     │
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:81:| Configuración de servidores | EDARSAHUB SQL → MongoDB fallback | Tabla `Servidores_Conexiones` |
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:84:| Cache de fallback | MongoDB | Colección `kpis_cache` |
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:98:    DATA_FROM_CACHE = "DATA_FROM_CACHE"  # Usando MongoDB cache (FALLBACK)
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:119:El cache proviene de **MongoDB colección `kpis_cache`**, guardado la última vez que la conexión tuvo éxito.
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:123:Evidencia de MongoDB:
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:141:- Estado del cache en MongoDB
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:255:**Respuesta**: SQL vivo directo a cada servidor de sucursal (SoftRestaurant/MPRO), con fallback a MongoDB cache. **NO usa EDARSAHUB para KPIs.**
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:258:**Respuesta**: Significa que la consulta SQL en vivo falló y se están mostrando datos guardados en MongoDB (colección `kpis_cache`) de la última consulta exitosa.
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:272:### Pregunta 7: ¿Los $15.77M de abril 2026 vienen de EDARSAHUB, SQL vivo, MongoDB cache o mezcla?
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:276:**Respuesta**: El campo `updated_at` en MongoDB `kpis_cache`. Ejemplo: `2026-05-01T16:13:40`.
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:393:- NO se alteraron datos en MongoDB
/app/docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md:402:El Tablero Ejecutivo Comercial **no usa EDARSAHUB como fuente de verdad**. Depende de conexiones SQL en vivo a las sucursales, con fallback a MongoDB cache. Esta arquitectura es la causa raíz de las etiquetas "Datos en caché" incluso cuando los servidores aparecen "Online".
/app/docs/reports/FASE_1B_SANITIZACION_SQL_ALTAS_REPORTE.md:227:- MongoDB
/app/docs/reports/INCIDENTE_SERVER_SECRET_KEY_PREVIEW_CONFIGURACION.md:135:### ✅ Validación 8: No hay MongoDB fallback
/app/docs/reports/INCIDENTE_SERVER_SECRET_KEY_PREVIEW_CONFIGURACION.md:137:- El endpoint `/api/servers` no usa MongoDB
/app/docs/reports/historical_load_june_2024_validation_report.json:35:    "mongo_final_inserted": 0
/app/docs/reports/historical_load_june_2024_validation_report.json:61:    "mongo_not_final": "CONFIRMED",
/app/docs/reports/historical_load_june_2024_validation_report.json:68:    "mongo_final_zero": true,
/app/docs/reports/REVISION_DML_CATALOGO_EMPRESAS_SERVIDORES_SUCURSALES.md:20:- ❌ NO se usará MongoDB como fuente
/app/docs/reports/REVISION_DML_CATALOGO_EMPRESAS_SERVIDORES_SUCURSALES.md:515:| No se usó MongoDB como fuente | ✅ CONFIRMADO |
/app/docs/reports/DIAGNOSTICO_PORTAL_INTELIGENCIA_COMERCIAL.md:297:2. **NO usar MongoDB** para datos comerciales - Todo en EDARSAHUB SQL Server
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:30:| Cuadres de Cortes Z | **MongoDB** | EDARSAHUB |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:36:**⚠️ ALERTA**: El repositorio de cuadres (`repository_cuadres_z.py`) almacena en **MongoDB**, violando la máxima de que MongoDB no debe ser fuente de verdad financiera.
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:74:| `/cuadres` | GET | Lista cuadres registrados | **MongoDB** |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:75:| `/cuadres/resumen` | GET | Estadísticas de cuadres | **MongoDB** |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:76:| `/cuadres/{id}` | GET | Detalle de cuadre | **MongoDB** |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:77:| `/cuadres` | POST | Crear cuadre | **MongoDB** |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:78:| `/cuadres/{id}` | PUT | Actualizar cuadre | **MongoDB** |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:79:| `/cuadres/{id}` | DELETE | Eliminar cuadre | **MongoDB** |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:80:| `/cuadres/{id}/ficha-deposito` | POST | Subir ficha depósito | **MongoDB** |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:81:| `/cuadres/{id}/validar-ficha` | POST | Validar ficha | **MongoDB** |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:114:### MongoDB (VIOLACIÓN DE MÁXIMA)
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:116:| Collection | Contenido | Registros |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:126:        self.collection_name = "tesoreria_cuadres_z"
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:129:    def collection(self):
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:130:        return get_db()[self.collection_name]  # MongoDB
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:140:## 6. CONFIRMACIÓN DE USO/NO USO DE MONGODB
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:142:| Componente | Usa MongoDB | Debería Usar |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:151:**⚠️ Los cuadres de Cortes Z actualmente almacenan en MongoDB, lo cual viola la máxima "MongoDB NO es fuente de verdad financiera".**
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:281:Cuadre de Efectivo (actualmente en MongoDB)
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:421:| Migración de cuadres MongoDB → EDARSAHUB | Alta | Alto | Crear tabla y migrar datos existentes |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:439:| MongoDB | Reducción de uso | ✅ NINGUNO |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:450:| `/app/backend/modules/finanzas/repository_cuadres_z.py` | Cambiar de MongoDB a EDARSAHUB |
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:497:### Subfase 4.1 — Preparación EDARSAHUB (Sin afectar MongoDB)
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:505:4. NO modificar MongoDB aún
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:511:### Subfase 4.2 — Migración de Cuadres MongoDB → EDARSAHUB
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:513:**Objetivo:** Mover datos existentes de MongoDB a EDARSAHUB
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:516:1. Backup de collection `tesoreria_cuadres_z`
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:519:4. NO eliminar MongoDB aún (modo dual)
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:539:### Subfase 4.4 — Cambio de Fuente (MongoDB → EDARSAHUB)
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:546:3. Desactivar escritura a MongoDB
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:671:- ✅ MongoDB NO es fuente de verdad financiera
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:707:1. **URGENTE**: Migrar cuadres de MongoDB a EDARSAHUB (Subfases 4.1-4.4)
/app/docs/reports/auditoria_finanzas_fase4_tesoreria.md:728:**Siguiente paso:** Solicitar autorización para iniciar implementación de Subfases 4.1-4.4 (Migración de cuadres MongoDB → EDARSAHUB).
/app/docs/reports/FIX_EXPLORADOR_BD_ENTERPRISE_TIPOS_SISTEMA_DINAMICOS.md:476:| ¿Se usó MongoDB? | **NO** |
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:11:### Dependencias MongoDB:
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:13:from pymongo import DESCENDING
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:16:### Métodos con código MongoDB:
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:17:| Método | Código MongoDB |
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:19:| `get_by_procesado_id()` | `self.collection.find_one()` |
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:20:| `get_by_estado()` | `self.collection.find().skip().limit().sort()` |
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:21:| `get_escalados()` | `self.collection.find().limit().sort()` |
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:23:| `contar_por_estado()` | `self.collection.aggregate()` |
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:26:- Uso de `pymongo.DESCENDING`
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:29:- Dependencia implícita de `self.collection` (MongoDB)
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:38:# CERO pymongo
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:43:DESCENDING = -1  # Reemplaza pymongo.DESCENDING
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:130:$ grep -c "pymongo" workflow_repository.py
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:136:$ grep -n "self.collection" workflow_repository.py
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:140:### Referencias MongoDB restantes (solo documentación):
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:141:- Línea 7: Comentario "CERO MongoDB productivo"
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:142:- Línea 20: Comentario "reemplaza pymongo.DESCENDING"
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:143:- Línea 202: Comentario "No usa $inc de MongoDB"
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:144:- Línea 233: Comentario "en lugar de aggregate de MongoDB"
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:169:| CERO MongoDB productivo en el repositorio | ✅ Confirmado |
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:192:$ grep -c "self.collection" tarea_repository.py
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:193:~10 llamadas MongoDB directas
/app/docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md:213:4. **FASE B-P2**: Migrar services que acceden directamente a MongoDB
/app/docs/reports/MIGRACION_ENDPOINTS_COMERCIALES_SQL_FIRST.md:10:Se completó la migración de **4 endpoints comerciales** de arquitectura LIVE (MongoDB + conexiones remotas) a **SQL-First** (consultas directas a EDARSAHUB).
/app/docs/reports/MIGRACION_ENDPOINTS_COMERCIALES_SQL_FIRST.md:68:- `get_server_by_id()` - SQL-First, sin fallback MongoDB
/app/docs/reports/MIGRACION_ENDPOINTS_COMERCIALES_SQL_FIRST.md:69:- `get_servers_for_tablero()` - SQL-First, sin fallback MongoDB
/app/docs/reports/MIGRACION_ENDPOINTS_COMERCIALES_SQL_FIRST.md:107:- Fallback a MongoDB
/app/docs/reports/historical_load_softrestaurant_validation_report.json:21:  "mongo_role": "checkpoint_log_cache_only",
/app/docs/reports/historical_load_softrestaurant_validation_report.json:40:    "mongo_final_inserted": 0
/app/docs/reports/historical_load_softrestaurant_validation_report.json:48:    "mongo_not_final": "CONFIRMED"
/app/docs/reports/historical_load_softrestaurant_validation_report.json:67:    "mongo_final_zero": true,
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:21:    LegacyMongoValue    VARCHAR(100) NULL,
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:55:    LegacyMongoValue    VARCHAR(100) NULL,
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:89:    LegacyMongoValue    VARCHAR(100) NULL,
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:117:| # | Tabla | Propósito | Reemplaza MongoDB |
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:134:| `LegacyMongoValue` | VARCHAR(100) | NULL | UUID MongoDB original (trazabilidad) |
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:150:| `LegacyMongoValue` | VARCHAR(100) | NULL | Valor MongoDB original |
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:166:| `LegacyMongoValue` | VARCHAR(100) | NULL | Valor MongoDB original |
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:260:| GET /api/users | ✅ 11 usuarios | Hotfix MongoDB activo |
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:261:| PUT /api/users/{id}/permissions | ✅ HTTP 200 | MongoDB (hotfix) |
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:273:| Hotfix MongoDB sigue activo | **Medio** | Necesario hasta completar RBAC-SCOPE-D/E |
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:283:1. Script idempotente para poblar las 3 tablas desde MongoDB
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:286:4. Preservar valores legacy en `LegacyMongoValue`
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:287:5. Validar conteo: MongoDB vs SQL
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:290:**Usuarios a migrar (con permisos en MongoDB):**
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:311:- ✅ Campo `LegacyMongoValue` para preservar origen
/app/docs/reports/RBAC_SCOPE_B_CREACION_TABLAS_PERMISOS_SQL.md:316:**Próximo paso:** Esperar autorización para RBAC-SCOPE-C (Migración de Datos MongoDB → SQL)
/app/docs/reports/VENTAS_DIA_CAMBIO_ARQUITECTONICO.md:182:| 2 | Sin MongoDB como fuente de negocio | ✅ |
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:11:Se ejecutó el saneamiento de usuarios pendientes antes de eliminar el fallback MongoDB:
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:20:- 0 `MONGODB_FALLBACK` para usuarios productivos
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:76:| superadmin@test.com | Desactivar en MongoDB | ✅ active=false |
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:77:| superadmin2@test.com | Desactivar en MongoDB | ✅ active=false |
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:78:| usuario_test_portal@test.com | Desactivar en MongoDB | ✅ active=false |
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:159:## 9. Validación de MONGODB_FALLBACK
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:163:| Usuarios productivos con MONGODB_FALLBACK | **0** |
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:165:| Total usuarios usando MongoDB | 0 |
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:194:| david.ricardez@ ve 0 servidores | Media | No es problema de Auth. Los servidores no tienen `empresa_id` en MongoDB. El filtrado usa `allowed_servers` que no tiene. Requiere FASE 3 o asignación manual. |
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:195:| Usuarios @test.com eliminación física pendiente | Baja | Están desactivados pero aún existen en MongoDB. Eliminación física puede hacerse en limpieza posterior. |
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:204:4. Los servidores en MongoDB no tienen `empresa_id` para filtrar por empresas
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:212:### ¿Se puede proceder con FASE 2-G (Eliminar fallback MongoDB)?
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:218:- ✅ MONGODB_FALLBACK = 0 para productivos
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:221:- ✅ No hay dependencia de MongoDB para autenticación productiva
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:229:| 3 | MONGODB_FALLBACK = 0 para productivos | ✅ |
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:234:**MÍNIMO.** Si se elimina el fallback MongoDB ahora:
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:237:- No hay usuarios que dependan de MongoDB
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:256:| No hay usuarios productivos usando MongoDB fallback | ✅ |
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:265:### En MongoDB:
/app/docs/reports/FASE2F2_SANEAMIENTO_USUARIOS_PRE_FALLBACK_OFF.md:280:*Saneamiento completado. Sistema listo para FASE 2-G (eliminar fallback MongoDB).*
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:1:# FASE B-P0-A: Diagnóstico Migración fase2_operativo MongoDB → SQL
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:6:**Arquitectura Destino:** EDARSAHUB SQL Server (CERO MongoDB)
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:17:| `db_utils.py` | Conexión MongoDB activa | ❌ Eliminar |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:18:| Repositories (`/repositories/*.py`) | 100% MongoDB | ❌ Migrar a SQL |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:19:| Services | 80% MongoDB, 20% SQL | ❌ Migrar a SQL |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:20:| Routes | Llamadas directas a MongoDB | ❌ Migrar a SQL |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:22:**Impacto crítico:** 13 tablas SQL faltan para reemplazar completamente MongoDB.
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:26:## 2. COLECCIONES MONGODB USADAS
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:30:| Colección MongoDB | Usos Detectados | Tabla SQL Equivalente | Estado SQL |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:80:### 3.1 Archivos con Dependencia MongoDB DIRECTA
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:82:| Archivo | Líneas MongoDB | Prioridad Migración |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:84:| `/modules/fase2_operativo/db_utils.py` | L8-32 (MongoClient) | 🔴 CRÍTICO |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:85:| `/modules/fase2_operativo/repositories/base_repository.py` | L34-163 (self.collection) | 🔴 CRÍTICO |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:90:| `/modules/fase2_operativo/services/notification_service.py` | L36 (db.notificaciones_log) | 🟠 ALTO |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:98:| `/modules/fase2_operativo/scripts/init_collections_fase2a.py` | TODO | 🟢 ELIMINAR |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:101:### 3.2 Repositorios que Heredan de BaseRepository (MongoDB)
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:105:├── base_repository.py          # Clase base MongoDB → SQL
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:106:├── asignacion_repository.py    # db.server_sucursales_config
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:107:├── auditoria_repository.py     # db.decisiones_auditoria
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:124:### 4.1 Endpoints con Dependencia MongoDB
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:126:| Endpoint | Archivo | Colecciones MongoDB |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:140:| `POST /api/v2/automatizacion/aprobar-gerencia` | automatizacion_compras_routes.py | users, collection |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:141:| `POST /api/v2/automatizacion/aprobar-tesoreria` | automatizacion_compras_routes.py | users, collection |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:539:| B-P4 | Eliminar `db_utils.py` y scripts MongoDB | 🟢 P3 | Baja |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:545:# Script para migrar datos de MongoDB a SQL (ejecutar en producción)
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:548:from pymongo import MongoClient
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:551:def migrar_coleccion(coleccion_mongo, tabla_sql, mapeo_campos):
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:553:    Migra datos de una colección MongoDB a una tabla SQL.
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:556:        coleccion_mongo: Nombre de la colección MongoDB
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:558:        mapeo_campos: Dict {campo_mongo: campo_sql}
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:560:    # 1. Leer todos los documentos de MongoDB
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:588:8. Eliminar scripts init_collections_*.py
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:619:| 10 | Eliminar archivos MongoDB obsoletos | 🟢 P3 | Todos |
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:633:- ❌ No se amplió MongoDB
/app/docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md:643:| Se identificó toda dependencia MongoDB de fase2_operativo | ✅ Completado |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:1:# AUDITORÍA DE DEPENDENCIAS MONGODB → EDARSAHUB SQL
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:6:**Objetivo:** Mapear todas las dependencias de MongoDB para migración a EDARSAHUB SQL Server
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:14:| Archivos con AsyncIOMotorClient | 18 |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:15:| Referencias a MONGO_URL | 30+ |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:16:| Referencias a `db.servers` activas | 5 (después de P1.4-B/C/E) |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:17:| Referencias a `db.users` | 40+ |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:18:| Referencias a `db.empresas` | 18 |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:19:| Referencias a `db.sucursales_catalogo` | 12 |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:20:| Referencias a `db.sucursal_servidor_map` | 8 |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:21:| Referencias a `db.roles` / `rbac_*` | 28 |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:22:| Colecciones MongoDB identificadas | 22+ |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:29:⚠️ MONGODB ES AÚN FUENTE PRIMARIA PARA:
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:45:## 1. MATRIZ DE COLECCIONES MONGODB
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:51:| `db.users` | AUTH, USUARIOS | 15+ archivos | ❌ Parcial (`Usuarios` básico) | `Usuarios` completo con permisos | **ALTO** |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:52:| `db.roles` | RBAC | 1 archivo | ❌ No | `Roles`, `Permisos` | **ALTO** |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:53:| `db.rbac_roles` | RBAC | 3 archivos | ❌ No | `RBAC_Roles` | **ALTO** |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:54:| `db.rbac_usuarios_roles` | RBAC | 4 archivos | ❌ No | `RBAC_Usuarios_Roles` | **ALTO** |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:55:| `db.servers` | CONEXIONES | 5 activas, 82 total | ✅ `Servidores_Conexiones` | N/A | **MEDIO** (en migración) |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:56:| `db.empresas` | MULTI-EMPRESA | 18 archivos | ❌ Parcial | `Empresas` completo | **ALTO** |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:57:| `db.sucursales_catalogo` | MULTI-SUCURSAL | 12 archivos | ❌ No | `Sucursales_Catalogo` | **ALTO** |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:58:| `db.sucursal_servidor_map` | MAPEO SUC↔SRV | 8 archivos | ✅ Parcial (`Unidades_Negocio`) | Completar campos | **MEDIO** |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:64:| `db.server_sucursales_config` | CONFIG UI | 8 referencias | ❌ No | `Servidores_Sucursales_Config` | **MEDIO** |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:65:| `db.queries` | TEMPLATES SQL | 5 referencias | ❌ No | `Consultas_Templates` | **MEDIO** |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:66:| `db.consultas_custom` | QUERIES CUSTOM | 2 referencias | ❌ No | `Consultas_Custom` | **BAJO** |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:67:| `db.config_catalogos` | CONFIG CATÁLOGOS | 1 referencia | ❌ No | `Config_Catalogos` | **BAJO** |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:73:| `db.kpis_cache` | CACHE KPIs | 3 referencias | ✅ SÍ | Mantener como cache |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:74:| `db.inventario_diferencias_cache` | CACHE INV | 3 referencias | ✅ SÍ | Mantener como cache |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:75:| `db.inventario_diferencias_detalle` | CACHE DETALLE | 4 referencias | ✅ SÍ | Mantener como cache |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:76:| `db.server_status` | STATUS CONEXIÓN | 4 referencias | ✅ SÍ | Mantener como cache |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:82:| `db.alerts` | ALERTAS | 5 referencias | Migrar a SQL o mantener |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:83:| `db.script_logs` | LOGS SCRIPTS | 1 referencia | Mantener en Mongo |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:84:| `db.informes_auditoria` | AUDITORÍAS | 5 referencias | Migrar a SQL |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:90:### 2.1 Endpoints que usan `db.users` (P0)
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:105:### 2.2 Endpoints que usan `db.empresas` (P0)
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:116:### 2.3 Endpoints que usan `db.sucursales_catalogo` (P0)
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:127:### 2.4 Endpoints que usan `db.servers` (En migración)
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:238:### 5.1 Si se apaga MongoDB HOY:
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:242:| **Login/Auth** | 🔴 FATAL | `db.users` es fuente primaria |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:243:| **RBAC/Permisos** | 🔴 FATAL | `db.rbac_*` sin equivalente SQL |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:244:| **Multi-empresa** | 🔴 FATAL | `db.empresas` sin equivalente SQL |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:245:| **Multi-sucursal** | 🔴 FATAL | `db.sucursales_catalogo` sin equivalente SQL |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:260:1. `db.users` → Leer SQL primero, fallback Mongo
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:261:2. `db.empresas` → Leer SQL primero, fallback Mongo
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:262:3. `db.sucursales_catalogo` → Leer SQL primero, fallback Mongo
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:263:4. `db.rbac_*` → Leer SQL primero, fallback Mongo
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:267:1. `db.kpis_cache` — Cache analítico
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:268:2. `db.inventario_diferencias_*` — Cache de reportes
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:269:3. `db.server_status` — Status temporal
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:270:4. `db.script_logs` — Logs de scripts
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:276:### FASE 1: Completar migración de `db.servers` (EN CURSO)
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:289:**Resultado:** `db.servers` eliminado como fuente funcional en server.py
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:299:| 2.3 | Migrar datos existentes de MongoDB a SQL | MEDIO |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:301:| 2.5 | Implementar dual-read (SQL primero, Mongo fallback) | MEDIO |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:305:| 2.9 | Desactivar fallback MongoDB | MEDIO |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:335:| 4.2 | Migrar `db.server_sucursales_config` | MEDIO |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:337:| 4.4 | Migrar `db.queries` | BAJO |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:339:| 4.6 | Migrar `db.alerts` | BAJO |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:345:### FASE 5: Eliminación controlada de fallback MongoDB
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:350:| 5.2 | Agregar logging de cualquier acceso MongoDB | BAJO |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:355:| 5.7 | Mantener MongoDB solo para cache P2-P3 | BAJO |
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:380:- **MongoDB sigue siendo crítico** para auth, RBAC, empresas y sucursales
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:382:- **La migración de `db.servers`** está en 70% completada
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:388:3. **Implementar dual-read** antes de eliminar MongoDB
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:389:4. **Mantener cache en MongoDB** para KPIs y diferencias
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:392:### 7.3 Orden Exacto para Eliminar MongoDB Sin Romper el Sistema
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:395:1. ✅ Completar migración db.servers (Fase 1)
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:397:3. ⏸️ Migrar datos de MongoDB a SQL
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:401:7. ⏸️ Período de observación (logs de MongoDB access)
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:402:8. ⏸️ Desactivar fallback MongoDB por módulo
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:403:9. ⏸️ Mantener MongoDB solo para cache
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:404:10. ⏸️ Deprecar cache MongoDB (opcional, futuro)
/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md:416:| 4 | Iniciar migración de `db.users` | ✅ SÍ |
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:16:| Módulos con MongoDB activo | 5 | 🔴 P0-P1 |
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:49:                                ├─────►│  MongoDB        ││ 🔴 VIOLACIÓN
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:72:| 6 | CRM Leads | `/crm/leads` | `LeadsPage.jsx` | ⚠️ MongoDB? |
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:73:| 7 | CRM Oportunidades | `/crm/oportunidades` | `OportunidadesPage.jsx` | ⚠️ MongoDB? |
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:82:| 16 | Finanzas | `/finanzas` | `Finanzas.js` | 🔴 MongoDB |
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:131:### Endpoints con MongoDB (VIOLACIÓN 🔴)
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:227:- `db_utils.py` - `MongoClient` directo
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:228:- `repositories/*.py` - Todos usan MongoDB
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:233:mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:234:_client = MongoClient(mongo_url)
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:309:### FASE B: Eliminar MongoDB en módulos críticos (P0-P1)
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:310:1. Migrar `fase2_operativo` de MongoDB a SQL
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:312:3. Eliminar fallbacks MongoDB
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:340:| MongoDB en módulos operativos | 5 | 0 |
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:351:El sistema tiene una base sólida SQL-First en los módulos nuevos (`comercial_v2`, `scheduler`, `rbac`), pero conserva código legacy con conexiones LIVE y MongoDB en módulos antiguos.
/app/docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md:354:1. 🔴 Migrar módulo `fase2_operativo` de MongoDB a SQL
/app/docs/reports/CRM_ENTERPRISE_CERTIFICACION_FINAL.md:9:- **Máxima 1 (El Cerebro es SQL Server)**: [APROBADO]. Se erradicó MongoDB. Toda la persistencia de cuotas, leads, pipelines y tickets reside en EDARSAHUB SQL.
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:27:| Archivo | Referencias MongoDB | Estado |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:35:## 3. Dependencias MongoDB Eliminadas
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:37:| Colección MongoDB | Archivo Original | Tabla SQL Reemplazo |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:39:| `db.empresas` | context_resolver, context_service | `Sistema_Empresas` + `Sistema_EmpresasMongoMap` |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:40:| `db.sucursales_catalogo` | context_resolver, context_service | `Sistema_Sucursales` |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:41:| `db.sucursal_servidor_map` | context_resolver | `Sistema_SucursalServidorMapeo` |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:42:| `db.servers` | context_resolver | `Servidores_Conexiones` |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:43:| `db.users` | user_access_context, context_service | `Usuario_Catalogo` |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:44:| `db.rbac_usuarios_roles` | context_service | `Usuario_RolesAsignacion` |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:45:| `db.rbac_roles` | context_service | `Usuario_Roles` |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:49:## 4. Referencias MongoDB Residuales (Clasificadas)
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:51:### 4.1 `db.empresas` — FUERA DE ALCANCE FASE 3
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:64:### 4.2 `db.sucursales_catalogo` — FUERA DE ALCANCE FASE 3
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:73:### 4.3 `db.sucursal_servidor_map` — FUERA DE ALCANCE FASE 3
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:81:### 4.4 `db.server_sucursales_config` — NO PRODUCTIVO / LEGACY
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:89:### 4.5 `db.servers` (core + auth) — PARCIALMENTE PRODUCTIVO
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:93:| `core/server_registry.py` | varios | **SQL-FIRST con sync a MongoDB** — Documentado |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:100:**Nota:** `server_registry.py` tiene modelo SQL-FIRST donde SQL es fuente y se sincroniza a MongoDB para compatibilidad. No es fallback.
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:102:### 4.6 `db.users` (core + auth) — CLASIFICADO
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:124:| `server.py` | 15005-15008 | Query a `db.sec_roles` para permisos de rol |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:126:**Nota:** `sec_roles` como atributo viene del usuario resuelto. La query a `db.sec_roles` es para resolución de permisos del rol, no para contexto.
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:128:### 4.9 `AsyncIOMotorClient` (core + auth) — INFRAESTRUCTURA
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:132:| `core/db.py` | 1032, 1036, 1041 | Infraestructura de conexión |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:145:| `Sistema_EmpresasMongoMap` | Mapeo UUID MongoDB → ID SQL | 5 |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:245:**Los 3 archivos core de contexto tienen 0 referencias a colecciones MongoDB.**
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:253:| `security.py` aún lee de MongoDB para empresas/sucursales/mapeos | MEDIO | Migrar en FASE 4 |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:254:| `alcance_helper.py` aún lee de MongoDB | MEDIO | Migrar en FASE 4 |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:255:| `password_reset.py` aún lee/escribe de MongoDB | BAJO | Migrar en FASE 4 |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:257:| Scheduler jobs aún usan MongoDB | BAJO | Fuera de alcance FASE 3 |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:285:5. **Auditar módulos Finanzas/RH** — Identificar dependencias MongoDB para fases posteriores.
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:310:### ✅ MongoDB NO ES FUENTE PRODUCTIVA PARA:
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:312:- `context_resolver.py` — 0 referencias MongoDB
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:313:- `user_access_context.py` — 0 referencias MongoDB
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:314:- `context_service.py` — 0 referencias MongoDB
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:322:| Empresas/sucursales/mapeos/contexto no dependen productivamente de MongoDB | ✅ |
/app/docs/reports/FASE3FG_AUDITORIA_FINAL_EMPRESAS_SUCURSALES_CONTEXTO_SQL.md:327:| Referencias MongoDB residuales clasificadas | ✅ |
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE6_INTEGRACION_REPORTE.md:211:| No usar MongoDB | ✅ Solo SQL Server |
/app/docs/reports/FASE_4B_FASE2_OPERATIVO_PROPUESTA_TECNICA.md:19:Este módulo tiene **36 referencias directas** a colecciones MongoDB distribuidas en 6 archivos de servicios.
/app/docs/reports/FASE_4B_FASE2_OPERATIVO_PROPUESTA_TECNICA.md:29:## 2. ESTADO ACTUAL EN MONGODB
/app/docs/reports/FASE_4B_FASE2_OPERATIVO_PROPUESTA_TECNICA.md:33:| Colección MongoDB | Documentos | Descripción |
/app/docs/reports/FASE_4B_FASE2_OPERATIVO_PROPUESTA_TECNICA.md:49:### 2.2 Archivos con Referencias MongoDB
/app/docs/reports/FASE_4B_FASE2_OPERATIVO_PROPUESTA_TECNICA.md:74:| Tabla Propuesta | Equivale a MongoDB |
/app/docs/reports/FASE_4B_FASE2_OPERATIVO_PROPUESTA_TECNICA.md:86:## 4. ANÁLISIS DE ESTRUCTURA MONGODB
/app/docs/reports/FASE_4B_FASE2_OPERATIVO_PROPUESTA_TECNICA.md:312:FASE B: Migrar datos de MongoDB a SQL
/app/docs/reports/FASE_4B_FASE2_OPERATIVO_PROPUESTA_TECNICA.md:429:- MongoDB sigue teniendo los datos originales
/app/docs/reports/FASE_4B_FASE2_OPERATIVO_PROPUESTA_TECNICA.md:461:2. **¿Autoriza migrar los ~2,016 documentos de MongoDB a SQL?**
/app/docs/reports/FASE_4B_FASE2_OPERATIVO_PROPUESTA_TECNICA.md:465:4. **¿Confirma que MongoDB queda como histórico temporal (sin eliminar colecciones)?**
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:1:# RBAC-SCOPE-C: Migración de Permisos Legacy MongoDB → SQL
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:13:# Conexión a MongoDB (solo lectura)
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:14:mongo_users = await mongo_db.users.find({
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:19:# Mapeo de usuarios: MongoDB ID → SQL UsuarioID
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:22:# Mapeo de servidores: MongoDB UUID → SQL Servidores_Conexiones.id
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:27:    (UsuarioID, ServidorID, LegacyMongoValue, Activo, FechaCreacion, Observaciones)
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:28:VALUES (@UsuarioID, @ServidorID, @LegacyMongoValue, 1, GETDATE(), 
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:29:        'Migrado RBAC-SCOPE-C desde MongoDB 2025-12-14')
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:105:| Usuario | Servidor | SucursalCodigo | LegacyMongoValue |
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:166:### Antes de Migración (MongoDB)
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:203:## 11. Confirmación MongoDB No Modificado
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:207:| MongoDB solo fue leído (find) | ✅ |
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:208:| No se ejecutó update en MongoDB | ✅ |
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:209:| No se ejecutó delete en MongoDB | ✅ |
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:210:| No se ejecutó insert en MongoDB | ✅ |
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:225:| PUT /api/users/{id}/permissions | ✅ | HTTP 200 (hotfix MongoDB) |
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:226:| Hotfix MongoDB activo | ✅ | Carlos Ruz muestra permisos via API |
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:229:**✅ El comportamiento productivo NO cambió.** El sistema sigue usando el hotfix MongoDB para lectura/escritura de permisos. Las tablas SQL están pobladas pero aún no se usan productivamente.
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:237:| SQL y MongoDB podrían desincronizarse | **Media** | Próxima fase (RBAC-SCOPE-D/E) cambiará lectura/escritura a SQL |
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:238:| Hotfix MongoDB sigue activo | **Baja** | Intencionalmente preservado hasta RBAC-SCOPE-D |
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:249:   - Eliminar lectura de `allowed_servers`, `allowed_sucursales`, `allowed_warehouses` desde MongoDB
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:258:3. Preservar hotfix MongoDB como fallback temporal durante validación
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:273:Los permisos legacy han sido migrados de MongoDB a EDARSAHUB SQL:
/app/docs/reports/RBAC_SCOPE_C_MIGRACION_PERMISOS_LEGACY_SQL.md:280:- ✅ MongoDB solo fue leído, no modificado
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:1:# DIAGNÓSTICO: Migración Circuit Breaker de MongoDB a EDARSAHUB SQL
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:12:Se identificó que el módulo Comercial depende de MongoDB para:
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:19:**VIOLACIÓN ARQUITECTÓNICA:** EDARSAHUB SQL debe ser el cerebro del sistema. MongoDB NO debe usarse para decisiones operativas.
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:23:## 2. DEPENDENCIAS MONGODB IDENTIFICADAS
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:66:│                    FLUJO ACTUAL (CON MONGODB)                       │
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:75:│  3. is_server_recently_offline() ───► MongoDB: server_status        │
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:83:│      (Lee de EDARSAHUB!)             (MongoDB: kpis_cache)          │
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:93:- El resultado es DATA_FROM_CACHE con datos viejos de MongoDB
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:110:│     (No circuit breaker, no MongoDB)                                │
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:122:│                                    (NO usar caché MongoDB)          │
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:127:        NO hay fallback a MongoDB.
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:234:| ~939, 985, 1095 | Eliminar lógica de fallback a `kpis_cache` MongoDB |
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:245:| EDARSAHUB no disponible | Registrar error crítico, NO usar MongoDB |
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:253:2. Eliminar guardado de estado en MongoDB tras consultas exitosas
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:263:1. Eliminar funciones MongoDB obsoletas
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:264:2. Eliminar colecciones MongoDB: `server_status`, `kpis_cache`
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:273:- [ ] Tablero Ejecutivo V1 NO consulta MongoDB para circuit breaker
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:274:- [ ] Tablero Ejecutivo V1 NO usa MongoDB `server_status`
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md:301:**Próximo paso:** Autorizar Fase 1 para eliminar circuit breaker MongoDB del Tablero Ejecutivo V1
/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md:92:(UsuarioID, ServidorID, LegacyMongoValue, Activo, FechaCreacion, Observaciones)
/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md:105:(UsuarioID, ServidorID, AlmacenCodigo, LegacyMongoValue, Activo, FechaCreacion, Observaciones)
/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md:114:## 6. Confirmación de que MongoDB NO Cambió
/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md:116:### MongoDB antes de prueba
/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md:121:### MongoDB después de prueba
/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md:126:**Conclusión:** MongoDB NO fue modificado. Los datos legacy permanecen intactos.
/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md:184:| MongoDB no se modificó | ✅ |
/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md:193:| MongoDB contiene datos legacy desactualizados | Aceptable hasta RBAC-SCOPE-G | Bajo |
/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md:207:| MongoDB ya no se modifica para permisos | ✅ |
/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md:212:**RBAC-SCOPE-G puede ser autorizada.** Esta fase eliminará las dependencias residuales de MongoDB en el módulo Usuarios/Roles.
/app/docs/reports/RBAC_SCOPE_F_VALIDACION_E2E_MODAL_PERMISOS_SQL.md:223:| MongoDB no se modifica | ✅ |
/app/docs/reports/P0_IMPLEMENTACION_VENTAS_DIA_TURNOS_SQLONLY.md:209:| MongoDB | ❌ No usa | ❌ No usa |
/app/docs/reports/P0_IMPLEMENTACION_VENTAS_DIA_TURNOS_SQLONLY.md:220:| No MongoDB | ✅ Confirmado |
/app/docs/reports/FASE_1B_R3_SYNC_VENTAS_PORHORA_JOB_VALIDACION.md:243:| NO MongoDB | ✓ |
/app/docs/reports/FASE_1B_R3_SYNC_VENTAS_PORHORA_JOB_VALIDACION.md:281:| NO MongoDB | ✓ Confirmado |
/app/docs/reports/FASE_1B_R3_SYNC_VENTAS_PORHORA_JOB_VALIDACION.md:305:| 20 | No dependencia MongoDB | ✓ |
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:128:### 1.5 Usuario_MigracionMongoTrace (EXISTE - 9 registros)
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:132:| TraceID | MongoID | Email | UsuarioID_SQL | RolMongoDB | Activo | Clasificacion |
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:146:## 2. CAMPOS REALES EN MongoDB db.users
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:151:_id                    (ObjectId MongoDB - interno)
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:186:### 2.2 Total usuarios en MongoDB: 17
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:216:user = await db.users.find_one({"email": payload['email']}, {"_id": 0})
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:271:# Línea 50: Busca en MongoDB
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:275:**Fuente:** 100% MongoDB (`db.users`)
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:279:## 4. COMPARACIÓN CAMPO MongoDB → COLUMNA SQL
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:281:| Campo MongoDB | Columna SQL Existente | Transformación | Estado |
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:283:| `_id` (ObjectId) | - | Trazabilidad en `Usuario_MigracionMongoTrace.MongoID` | MIGRADO |
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:305:**MongoDB (db.users.password):**
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:317:| Email | Hash en MongoDB | Hash en SQL | Coincide |
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:338:**CONCLUSIÓN:** Los hashes bcrypt son portables entre MongoDB y SQL sin conversión.
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:349:    'user_id': user_id,      # ← user['id'] de MongoDB (UUID string)
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:361:user = await db.users.find_one({"email": payload['email']}, {"_id": 0})
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:365:- El JWT contiene `user_id` (UUID de MongoDB)
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:379:Agregar columna `PublicUUID` a `Usuario_Catalogo` para mantener el UUID original de MongoDB:
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:391:### 7.1 SuperAdministradores en MongoDB (4)
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:400:### 7.2 Roles en SQL vs MongoDB
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:402:| Rol MongoDB | Rol SQL Existente | RolID |
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:425:### 8.1 Emails duplicados en MongoDB
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:435:### 8.3 Usuarios en MongoDB que faltan en SQL (8)
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:452:### 9.1 Resumen MongoDB
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:485:| **R2** | Usuario sin UUID en MongoDB (`superadmin@test.com`) | Generar UUID durante migración |
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:492:| **R4** | Empresas UUID en MongoDB vs int en SQL | Crear tabla de mapeo `Empresas_MigracionMongoMap` |
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:510:IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Usuario_Catalogo' AND COLUMN_NAME = 'MongoLegacyID')
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:512:    ALTER TABLE dbo.Usuario_Catalogo ADD MongoLegacyID VARCHAR(50) NULL;
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:527:IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Usuario_MongoLegacyID')
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:529:    CREATE UNIQUE INDEX IX_Usuario_MongoLegacyID 
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:530:    ON dbo.Usuario_Catalogo(MongoLegacyID) WHERE MongoLegacyID IS NOT NULL;
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:547:IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Empresas_MigracionMongoMap')
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:549:    CREATE TABLE dbo.Empresas_MigracionMongoMap (
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:551:        MongoEmpresaID VARCHAR(50) NOT NULL UNIQUE,
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:582:-- UPDATE Usuario_Catalogo SET MongoLegacyID = NULL, PublicUUID = NULL;
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:584:-- Paso 4: Revertir código a MongoDB-only
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:614:- [ ] Poblar `PublicUUID` para los 9 usuarios existentes desde MongoDB
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:634:| Columnas faltantes | `PublicUUID`, `MongoLegacyID` | DDL pendiente |
/app/docs/reports/FASE2A1_VALIDACION_DDL_AUTH_RBAC_PRE_MIGRACION.md:639:| SuperAdministrador | 4 en Mongo, 2 en SQL | Preservar rol |
/app/docs/reports/server_secrets_encryption_report.json:17:      "mongo": "OK"
/app/docs/reports/server_secrets_encryption_report.json:23:      "mongo": "OK"
/app/docs/reports/server_secrets_encryption_report.json:29:      "mongo": "OK"
/app/docs/reports/server_secrets_encryption_report.json:35:      "mongo": "OK"
/app/docs/reports/server_secrets_encryption_report.json:41:      "mongo": "OK"
/app/docs/reports/server_secrets_encryption_report.json:47:      "mongo": "OK"
/app/docs/reports/server_secrets_encryption_report.json:53:      "mongo": "OK"
/app/docs/reports/server_secrets_encryption_report.json:59:      "mongo": "OK"
/app/docs/reports/server_secrets_encryption_report.json:65:      "mongo": "OK"
/app/docs/reports/server_secrets_encryption_report.json:71:      "mongo": "OK"
/app/docs/reports/BUG_USERS_LIST_002_USUARIOS_SQL_NO_VISIBLES.md:175:| Permisos granulares (allowed_*) | MongoDB (hotfix temporal) | ⚠️ Pendiente RBAC-SCOPE-D |
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:19:-- PASO 1: Agregar columna MongoLegacyID si no existe
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:22:    WHERE TABLE_NAME = 'Usuario_Catalogo' AND COLUMN_NAME = 'MongoLegacyID'
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:25:    ALTER TABLE dbo.Usuario_Catalogo ADD MongoLegacyID VARCHAR(50) NULL;
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:48:-- PASO 4: Crear índice único en MongoLegacyID si no existe
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:51:    WHERE name = 'IX_Usuario_MongoLegacyID' AND object_id = OBJECT_ID('Usuario_Catalogo')
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:54:    CREATE UNIQUE INDEX IX_Usuario_MongoLegacyID 
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:55:    ON dbo.Usuario_Catalogo(MongoLegacyID) 
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:56:    WHERE MongoLegacyID IS NOT NULL;
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:95:### 2.2 Mapeo MongoDB role → SQL RolID
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:97:| Rol en MongoDB (user.role) | Mapear a RolID |
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:113:| MongoLegacyID | VARCHAR(50) | YES | IX_Usuario_MongoLegacyID (UNIQUE) | **CREADA** |
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:120:| `MongoLegacyID` | Almacena el ObjectId de MongoDB (`_id`) para trazabilidad |
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:121:| `PublicUUID` | Almacena el UUID de MongoDB (`user.id`) usado en JWT |
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:171:### 5.2 Columnas PublicUUID y MongoLegacyID
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:175:Usuarios con MongoLegacyID poblado: 0
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:188:| `core/security.py` | Sin cambios | `db.users.find_one()` intacto |
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:197:grep -n "db.users" /app/backend/core/security.py
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:235:El usuario `superadmin@test.com` en MongoDB tiene:
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:271:| R2 | Empresas en MongoDB son UUIDs, en SQL son int | Media | Medio | Crear tabla de mapeo en FASE 2-B |
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:281:- [x] MongoLegacyID existe en Usuario_Catalogo
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:295:- [ ] Crear tabla de mapeo Empresas MongoDB→SQL
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:300:1. Poblar `PublicUUID` y `MongoLegacyID` para los 9 usuarios existentes desde MongoDB
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:313:| Columnas creadas | ✓ PublicUUID, MongoLegacyID |
/app/docs/reports/FASE2A2_PRECONDICIONES_DDL_AUTH_RBAC_SQL.md:314:| Índices creados | ✓ IX_Usuario_PublicUUID, IX_Usuario_MongoLegacyID |
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:1:# FASE 2-B2.1: MAPEO EMPRESAS MONGODB → SQL
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:9:## 1. EMPRESAS MONGODB ENCONTRADAS
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:21:### 1.2 UUIDs usados en `db.users.empresas_permitidas`
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:48:| Campo MongoDB | Campo SQL | Método |
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:56:## 4. TABLA DE EQUIVALENCIAS MONGODB → SQL
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:58:### 4.1 Mapeos creados en `Sistema_EmpresasMongoMap`
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:60:| MapID | UUID MongoDB | ObjectID MongoDB | EmpresaID SQL | Código | Nombre | Método |
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:72:**Ninguna.** Todas las 5 empresas de MongoDB tienen equivalencia en SQL.
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:78:**Ninguna.** Cada código de MongoDB tiene exactamente una correspondencia en SQL.
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:101:| david.ricardez@cienfuegos.mx | Usuario sin empresas asignadas en MongoDB |
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:105:**Nota:** Los usuarios sin `empresas_permitidas` en MongoDB podrían tener acceso global o requerir asignación manual.
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:112:-- FASE 2-B2.1: Crear tabla Sistema_EmpresasMongoMap
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:115:CREATE TABLE dbo.Sistema_EmpresasMongoMap (
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:117:    EmpresaMongoUUID VARCHAR(50) NOT NULL,
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:118:    EmpresaMongoLegacyID VARCHAR(50) NULL,
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:129:    CONSTRAINT UQ_EmpresaMongoUUID UNIQUE (EmpresaMongoUUID),
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:143:INSERT INTO Sistema_EmpresasMongoMap (
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:144:    EmpresaMongoUUID, EmpresaMongoLegacyID, EmpresaID_SQL, 
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:171:✓ MongoDB sigue siendo fuente de login
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:187:- [x] MongoDB sigue siendo fuente de autenticación
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:207:- [x] Tabla `Sistema_EmpresasMongoMap` creada
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:214:1. Para cada usuario SQL con `empresas_permitidas` en MongoDB:
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:215:   - Leer UUIDs de empresas desde MongoDB
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:216:   - Convertir a EmpresaID_SQL usando `Sistema_EmpresasMongoMap`
/app/docs/reports/FASE2B2_1_MAPEO_EMPRESAS_MONGO_SQL.md:247:| Mapeo validado MongoDB → SQL | ✓ |
/app/docs/reports/INCIDENTE_CACHE_PREVIEW_ESTADO_CORRUPTO_DIAGNOSTICO.md:64:| _server_status_cache | core/db.py | ALTO |
/app/docs/reports/INCIDENTE_EDARSAHUB_SQL_DESAPARECIDO_MENU_SERVIDORES_DIAGNOSTICO.md:88:| 7 | MongoDB como fuente | ❌ No, usa SQL |
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:9:## 1. VALORES ROLE/ROL ENCONTRADOS EN MONGODB
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:28:## 2. MAPEO MONGODB ROL → SQL ROL
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:32:| Role MongoDB | RolID SQL | CodigoRol SQL | NombreRol SQL |
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:42:| Role MongoDB | Razón |
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:54:# - Leer usuarios SQL con trazabilidad MongoDB
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:55:# - Leer rol de MongoDB usando email
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:90:| UsuarioID | Email | Role MongoDB | RolID SQL | CodigoRol SQL |
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:128:| UsuarioID | Email | Role MongoDB | RolID SQL |
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:196:✓ MongoDB sigue siendo fuente de login
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:197:✓ Usuario admin@inventario.com encontrado en MongoDB
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:211:- [x] MongoDB sigue siendo fuente de autenticación
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:230:El campo `empresas_permitidas` en MongoDB contiene UUIDs de empresas. Será necesario:
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:232:1. Crear tabla de mapeo `Empresas_MigracionMongoMap` si no existe
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:233:2. Mapear UUIDs de MongoDB a `EmpresaID` de SQL
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:237:### 12.2 Datos de MongoDB relevantes
/app/docs/reports/FASE2B2_POBLADO_USUARIO_ROLES_ASIGNACION.md:266:| MongoDB sigue siendo fuente de login | ✓ |
/app/docs/reports/FASE_B_P0_B_DDL_FASE2_OPERATIVO_SQL.md:487:| CERO MongoDB | ✅ Confirmado |
/app/docs/reports/FASE_B_P0_B_DDL_FASE2_OPERATIVO_SQL.md:495:## 10. MAPEO COLECCIÓN MONGODB → TABLA SQL FINAL
/app/docs/reports/FASE_B_P0_B_DDL_FASE2_OPERATIVO_SQL.md:497:| Colección MongoDB | Tabla SQL EDARSAHUB |
/app/docs/reports/FASE_B_P0_B_DDL_FASE2_OPERATIVO_SQL.md:527:1. Crear archivo `sql_tables_mapping.py` con mapeo MongoDB → SQL
/app/docs/reports/FASE_B_P0_B_DDL_FASE2_OPERATIVO_SQL.md:528:2. Refactorizar `base_repository.py` para soportar dual-mode (MongoDB/SQL)
/app/docs/reports/FASE_B_P0_B_DDL_FASE2_OPERATIVO_SQL.md:530:4. Mantener MongoDB activo hasta validación completa en SQL
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:13:Se eliminaron las referencias productivas a MongoDB en `security.py` y `alcance_helper.py`, reemplazándolas por consultas a EDARSAHUB SQL. Las funciones migradas resuelven empresas permitidas, servidores asociados y alcance de usuario desde las tablas canónicas SQL.
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:17:## 2. Referencias MongoDB Encontradas (ANTES)
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:23:| 485 | `db.empresas.find({'activa': True})` | get_user_empresas_permitidas (SuperAdmin) |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:24:| 495 | `db.empresas.find({'activa': True})` | get_user_empresas_permitidas (Admin) |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:25:| 515 | `db.sucursales_catalogo.find()` | get_servers_for_empresas |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:26:| 523 | `db.sucursal_servidor_map.find()` | get_servers_for_empresas |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:32:| 68 | `db.sucursales_catalogo.find()` | _resolver_unidad |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:33:| 87 | `db.sucursales_catalogo.find_one()` | _resolver_sucursal |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:43:| `get_user_empresas_permitidas()` | Migrada a SQL (`Sistema_Empresas` + `Sistema_EmpresasMongoMap`) |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:50:| `_resolver_unidad()` | Migrada a SQL (`Sistema_Sucursales` + `Sistema_EmpresasMongoMap`) |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:51:| `_resolver_sucursal()` | Migrada a SQL (`Sistema_Sucursales` + `Sistema_EmpresasMongoMap`) |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:55:## 4. Flujo Anterior (MongoDB)
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:59:   └─> db.empresas.find({'activa': True})
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:60:       └─> Retorna lista de empresa_ids de MongoDB
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:63:   └─> db.sucursales_catalogo.find({empresa_id: {$in: empresas}})
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:64:       └─> db.sucursal_servidor_map.find({sucursal_id: {$in: sucursales}})
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:68:   └─> db.sucursales_catalogo.find({unidad_negocio_id: unidad_id})
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:72:   └─> db.sucursales_catalogo.find_one({id: suc_id})
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:82:   └─> SELECT EmpresaMongoUUID FROM Sistema_Empresas e
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:83:       JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:85:       └─> Retorna lista de UUIDs MongoDB (compatibilidad)
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:90:       JOIN Sistema_EmpresasMongoMap em ON s.EmpresaID = em.EmpresaID_SQL
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:91:       WHERE em.EmpresaMongoUUID IN (...)
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:95:   └─> SELECT DISTINCT EmpresaMongoUUID FROM Sistema_Sucursales s
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:96:       JOIN Sistema_EmpresasMongoMap m ON s.EmpresaID = m.EmpresaID_SQL
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:97:       WHERE s.MongoUUID IN (...) OR m.EmpresaMongoUUID IN (...)
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:101:   └─> SELECT DISTINCT EmpresaMongoUUID FROM Sistema_Sucursales s
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:102:       JOIN Sistema_EmpresasMongoMap m ON s.EmpresaID = m.EmpresaID_SQL
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:103:       WHERE s.MongoUUID IN (...)
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:114:| `Sistema_EmpresasMongoMap` | Mapeo UUID MongoDB → ID SQL |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:123:$ grep -n "db.empresas" /app/backend/core/security.py
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:126:$ grep -n "db.sucursales_catalogo" /app/backend/core/security.py
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:129:$ grep -n "db.sucursal_servidor_map" /app/backend/core/security.py
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:132:$ grep -n "db.sucursales_catalogo" /app/backend/core/alcance_helper.py
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:142:**Total referencias `db.*` productivas: 0**
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:187:## 11. Referencias MongoDB Residuales (security.py)
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:193:| 14, 56-83 | Comentarios sobre MongoDB | NO PRODUCTIVO (documentación) |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:195:| 698-774 | Funciones de comparación SQL vs MongoDB | OBSERVABILIDAD (no productivo) |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:205:| `password_reset.py` aún usa MongoDB | BAJO | Migrar en siguiente fase |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:222:2. Auditar módulos Finanzas/RH que usan `db.empresas`
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:230:| `security.py` no depende productivamente de MongoDB para empresas/servidores | ✅ |
/app/docs/reports/FASE3H_SECURITY_ALCANCE_HELPER_SQL.md:231:| `alcance_helper.py` no depende productivamente de MongoDB | ✅ |
/app/docs/reports/FASE_1C_3I_B_SERVICIOS_BACKEND_PRICING_BENCHMARK.md:10:Se implementaron los servicios backend y endpoints CRUD para el Motor de Precios Sugeridos con IA y Benchmark Competitivo, sin ejecutar IA real.
/app/docs/reports/FASE_1C_3I_B_SERVICIOS_BACKEND_PRICING_BENCHMARK.md:19:- **NO se usó MongoDB**
/app/docs/reports/FASE_1C_3I_B_SERVICIOS_BACKEND_PRICING_BENCHMARK.md:38:- Enums: TipoRestaurante, SegmentoPrecio, MetodoObtencion, ConfianzaDato, TipoComparacion, TipoMotorPrecio, PosicionVsCompetencia, EstadoCalculo
/app/docs/reports/FASE_1C_3I_B_SERVICIOS_BACKEND_PRICING_BENCHMARK.md:227:    "tipo_motor": "COSTO_MARGEN",
/app/docs/reports/FASE_1C_3I_B_SERVICIOS_BACKEND_PRICING_BENCHMARK.md:250:| 12 | No se usa MongoDB | ✅ |
/app/docs/reports/FASE_1C_3I_B_SERVICIOS_BACKEND_PRICING_BENCHMARK.md:275:## 10. MOTORES DE PRECIO DISPONIBLES
/app/docs/reports/FASE_1C_3I_B_SERVICIOS_BACKEND_PRICING_BENCHMARK.md:277:| Motor | Estado | Descripción |
/app/docs/reports/FASE_1C_3I_B_SERVICIOS_BACKEND_PRICING_BENCHMARK.md:297:| 7 | NO se usó MongoDB | ✅ |
/app/docs/reports/FASE_1C_3I_B_SERVICIOS_BACKEND_PRICING_BENCHMARK.md:308:2. **Productos sin costo**: El motor COSTO_MARGEN requiere costo configurado. Sin costo, devuelve estado `COSTO_NO_CONFIGURADO`.
/app/docs/reports/FASE_1C_3I_B_SERVICIOS_BACKEND_PRICING_BENCHMARK.md:344:**MongoDB**: NO usado  
/app/docs/reports/FASE_1C_3G_E3_SYNC_COSTO_BASE_VINOS_ORIGEN.md:178:| 18 | Sin MongoDB | ✅ |
/app/docs/reports/FASE_1C_3G_E3_SYNC_COSTO_BASE_VINOS_ORIGEN.md:355:1. **Actualizar motor de cálculo** para clasificar automáticamente
/app/docs/reports/FASE_1C_3G_E3_SYNC_COSTO_BASE_VINOS_ORIGEN.md:368:**Siguiente Acción**: Esperar autorización para actualizar motor y FASE 1C-3G-F Frontend
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:12:Crear un repositorio SQL paralelo (`user_repository_sql.py`) que permita consultar datos de autenticación y RBAC desde EDARSAHUB SQL sin modificar el flujo productivo de MongoDB.
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:16:- ✅ Implementar funciones equivalentes a MongoDB (`get_user_by_email`, `get_user_by_uuid`)
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:19:- ✅ Incluir funciones de comparación MongoDB vs SQL
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:32:| `get_user_by_email_sql(email)` | Busca usuario por email, devuelve dict compatible MongoDB |
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:44:| `compare_user_mongo_vs_sql(email)` | Compara usuario entre ambas fuentes |
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:58:    empresas_uuids = [e['uuid_mongo'] for e in all_empresas if e['uuid_mongo']]
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:73:## 4. Mapeo de Estructura SQL → MongoDB
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:78:    # Campos compatibles con MongoDB
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:83:    'role': rol_mongo,               # Mapeo: SUPERADMIN → SuperAdministrador
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:84:    'rol': rol_mongo,
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:87:    'empresas_permitidas': [uuids],  # Lista de UUIDs MongoDB
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:94:    '_sql_mongo_legacy_id': str,
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:100:### Mapeo de roles SQL → MongoDB:
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:101:| Código SQL | Nombre MongoDB |
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:144:## 6. Usuarios Pendientes (Sin empresas_permitidas en MongoDB)
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:146:Los siguientes usuarios existen en SQL pero no tienen asignaciones de empresas porque sus registros originales en MongoDB tampoco las tenían:
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:161:Los siguientes archivos permanecen intactos y siguen usando MongoDB:
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:165:| `/app/backend/core/security.py` | `get_current_user()` | 🔒 INTACTO - Usa MongoDB |
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:166:| `/app/backend/modules/auth/service.py` | `login()`, `authenticate()` | 🔒 INTACTO - Usa MongoDB |
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:169:**El sistema productivo sigue operando 100% con MongoDB para autenticación.**
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:178:| Funciones equivalentes a MongoDB implementadas | ✅ |
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:190:### FASE 2-E: Cambiar `get_current_user` a SQL-first con fallback MongoDB
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:193:- Mantener fallback a MongoDB si SQL no encuentra el usuario
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:197:- Monitorear logs de fallback MongoDB
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:200:### FASE 2-G: Eliminar Fallback MongoDB
/app/docs/reports/FASE2D_AUTH_REPOSITORY_SQL_PARALELO.md:217:*MongoDB sigue siendo la fuente productiva de autenticación hasta que se autorice FASE 2-E.*
/app/docs/reports/DIAGNOSTICO_SCHEDULER_ESTADO_ACTUAL.md:43:- **sql_repository.py**: Repositorio SQL para jobs (reemplaza MongoDB)
/app/docs/reports/DIAGNOSTICO_SCHEDULER_ESTADO_ACTUAL.md:139:## 6. DEPENDENCIAS MONGODB
/app/docs/reports/DIAGNOSTICO_SCHEDULER_ESTADO_ACTUAL.md:142:- **MongoDB ELIMINADO del sistema**
/app/docs/reports/DIAGNOSTICO_SCHEDULER_ESTADO_ACTUAL.md:145:- `scheduler_manager.py` opera sin persistencia real en MongoDB
/app/docs/reports/DIAGNOSTICO_SCHEDULER_ESTADO_ACTUAL.md:147:### 6.2 Archivos con Referencias MongoDB (Comentarios Legacy)
/app/docs/reports/DIAGNOSTICO_SCHEDULER_ESTADO_ACTUAL.md:148:- `scheduler_manager.py`: Comentarios mencionan MongoDB para locks
/app/docs/reports/DIAGNOSTICO_SCHEDULER_ESTADO_ACTUAL.md:150:- `sync_comercial_v2_job.py`: Menciona "MongoDB solo para locks técnicos"
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:14:1. **4 colecciones MongoDB** son fuente productiva de empresas/sucursales:
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:15:   - `db.empresas` (19 referencias)
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:16:   - `db.sucursales_catalogo` (10 referencias)
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:17:   - `db.sucursal_servidor_map` (6 referencias)
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:18:   - `db.server_sucursales_config` (12 referencias)
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:22:   - `Sistema_EmpresasMongoMap` (5 mapeos UUID→SQL) ✅
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:31:   - **SE NECESITA** mapeo sucursal→servidor (equivalente a `db.sucursal_servidor_map`)
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:32:   - **SE NECESITA** configuración servidor→sucursales (equivalente a `db.server_sucursales_config`)
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:43:## 2. Dependencias MongoDB Encontradas
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:45:### 2.1. db.empresas (19 referencias)
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:63:### 2.2. db.sucursales_catalogo (10 referencias)
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:76:### 2.3. db.sucursal_servidor_map (6 referencias)
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:87:### 2.4. db.server_sucursales_config (12 referencias)
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:101:| Endpoint | Archivo | Colección MongoDB | Tipo | Prioridad |
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:118:| Archivo | Referencias MongoDB | Impacto |
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:126:| Archivo | Referencias MongoDB | Impacto |
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:134:| Archivo | Referencias MongoDB | Impacto |
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:141:| Archivo | Referencias MongoDB | Impacto |
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:159:**Uso:** Reemplaza `db.empresas` para catálogo de empresas.
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:161:### Sistema_EmpresasMongoMap ✅
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:163:MapID | EmpresaMongoUUID | EmpresaID_SQL | CodigoEmpresa
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:170:**Uso:** Traduce UUIDs de MongoDB a IDs de SQL.
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:184:**Uso:** YA EXISTE catálogo de sucursales. Puede reemplazar `db.sucursales_catalogo`.
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:225:    MongoUUID VARCHAR(36) NULL,
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:241:    MongoUUID VARCHAR(36) NULL,
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:251:**Propósito:** Reemplazar `db.sucursal_servidor_map`
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:253:-- Sigue patrón de Sistema_EmpresasMongoMap
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:259:    MongoMapUUID VARCHAR(36) NULL,
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:269:**Propósito:** Reemplazar `db.server_sucursales_config`
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:304:## 7. Matriz MongoDB → SQL
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:306:| Colección MongoDB | Tabla SQL Existente | Tabla SQL Faltante | Estado |
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:308:| `db.empresas` | `Sistema_Empresas` + `Sistema_EmpresasMongoMap` | - | ✅ Listo |
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:309:| `db.sucursales_catalogo` | - | `Sistema_Sucursales` | ❌ Crear |
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:310:| `db.sucursal_servidor_map` | - | `Sistema_SucursalServidorMap` | ❌ Crear |
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:311:| `db.server_sucursales_config` | - | `Sistema_ServidorSucursalesConfig` | ❌ Crear |
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:330:2. Migrar datos de MongoDB a SQL:
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:331:   - `db.sucursales_catalogo` → `Sistema_Sucursales`
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:332:   - `db.sucursal_servidor_map` → `Sistema_SucursalServidorMap`
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:333:   - `db.server_sucursales_config` → `Sistema_ServidorSucursalesConfig`
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:357:2. Documentar referencias MongoDB residuales
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:368:| Sistema/Config | `Sistema_` | `Sistema_Empresas`, `Sistema_EmpresasMongoMap` | FechaAlta, FechaModificacion, CreatedBy, UpdatedBy, Activo |
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:377:2. **Mapeos de migración:** Usar `Sistema_*MongoMap` o `Sistema_*Mapeo`
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:400:1. ✅ Se identificaron las 4 colecciones MongoDB afectadas
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:403:4. ✅ Se mapearon las 5 empresas existentes SQL ↔ MongoDB
/app/docs/reports/FASE3A_DIAGNOSTICO_EMPRESAS_SUCURSALES_MAPEOS_SQL.md:449:| Colecciones MongoDB identificadas | 4 |
/app/docs/reports/FASE_B_P2_B_DDL_COMERCIAL_SQL.md:11:Migrar el último servicio con dependencias MongoDB (`automatizacion_compras_service.py`) a SQL Server EDARSAHUB.
/app/docs/reports/FASE_B_P2_B_DDL_COMERCIAL_SQL.md:13:### Antes (MongoDB)
/app/docs/reports/FASE_B_P2_B_DDL_COMERCIAL_SQL.md:14:- 5 referencias a `self.db.*`
/app/docs/reports/FASE_B_P2_B_DDL_COMERCIAL_SQL.md:15:- 13 referencias a `.collection`
/app/docs/reports/FASE_B_P2_B_DDL_COMERCIAL_SQL.md:16:- 3 colecciones MongoDB directas:
/app/docs/reports/FASE_B_P2_B_DDL_COMERCIAL_SQL.md:22:- 0 referencias MongoDB
/app/docs/reports/FASE_B_P2_B_DDL_COMERCIAL_SQL.md:32:| Método | MongoDB → SQL |
/app/docs/reports/FASE_B_P2_B_DDL_COMERCIAL_SQL.md:157:- COSTOS-ALERTAS: Motor de evaluación
/app/docs/reports/p0_regresion_comercial_cienfuegos.md:512:| MongoDB | ❌ NO |
/app/docs/reports/DIAGNOSTICO_QRO_VENTAS_DIA_FECHA_OPERACION_INCORRECTA.md:270:- ✅ **MongoDB NO fue consultado** como fuente de datos
/app/docs/reports/DIAGNOSTICO_QRO_VENTAS_DIA_FECHA_OPERACION_INCORRECTA.md:562:- ✅ **MongoDB NO fue consultado** como fuente de datos
/app/docs/reports/FASE_0_5_VALIDACION_ARQUITECTURA_MENUS_Y_COMERCIAL.md:97:| No MongoDB | ✅ Sin dependencias |
/app/docs/reports/FASE_0_5_VALIDACION_ARQUITECTURA_MENUS_Y_COMERCIAL.md:170:| Sin MongoDB nuevo | ✅ |
/app/docs/reports/auditoria_finanzas_fase3_propinas_tpv.md:14:2. **El módulo actual usa MongoDB** como destino de datos (no EDARSAHUB).
/app/docs/reports/auditoria_finanzas_fase3_propinas_tpv.md:87:### MongoDB (colecciones actuales)
/app/docs/reports/auditoria_finanzas_fase3_propinas_tpv.md:140:| **MongoDB** | ✅ Almacenamiento de propinas_control |
/app/docs/reports/auditoria_finanzas_fase3_propinas_tpv.md:146:SoftRestaurant → Service → MongoDB (propinas_control)
/app/docs/reports/auditoria_finanzas_fase3_propinas_tpv.md:153:## 8. CONFIRMACIÓN DE USO O NO USO DE MONGODB
/app/docs/reports/auditoria_finanzas_fase3_propinas_tpv.md:157:| MongoDB como destino de sincronización | ✅ SÍ |
/app/docs/reports/auditoria_finanzas_fase3_propinas_tpv.md:158:| MongoDB como fuente para listados | ✅ SÍ |
/app/docs/reports/auditoria_finanzas_fase3_propinas_tpv.md:159:| MongoDB como fuente para KPIs | ✅ SÍ |
/app/docs/reports/auditoria_finanzas_fase3_propinas_tpv.md:161:**Problema:** Esto viola la Máxima #3: "MongoDB NO es fuente de verdad financiera".
/app/docs/reports/auditoria_finanzas_fase3_propinas_tpv.md:435:| 3 | Dashboard lee desde EDARSAHUB (no MongoDB para datos financieros) |
/app/docs/reports/auditoria_finanzas_fase3_propinas_tpv.md:466:2. **Migrar destino de MongoDB a EDARSAHUB** (siguiendo patrón de Fase 2).
/app/docs/reports/FIX_EXPLORADOR_BD_TABLAS_PRUEBAS_ENTERPRISE.md:22:### Backend (`core/db.py`)
/app/docs/reports/FIX_EXPLORADOR_BD_TABLAS_PRUEBAS_ENTERPRISE.md:38:La función `execute_sql_query()` en `core/db.py` **ocultaba los errores** retornando lista vacía `[]`. El Explorador no podía distinguir entre:
/app/docs/reports/FIX_EXPLORADOR_BD_TABLAS_PRUEBAS_ENTERPRISE.md:75:| `/app/backend/core/db.py` | Nueva función `_execute_sql_direct_with_error()` que retorna (result, error) en vez de ocultar errores |
/app/docs/reports/FIX_EXPLORADOR_BD_TABLAS_PRUEBAS_ENTERPRISE.md:185:| 7 | No se usa MongoDB | ✅ | |
/app/docs/reports/FASE_1C_3I_B_COMPETIDORES_ENTERPRISE_UNIDAD.md:191:- ✅ **CERO MongoDB**
/app/docs/reports/FIX_COMERCIAL_DASHBOARD_FUENTE_VENTAS_TABLERO_EJECUTIVO.md:134:// MongoDB usado: NO
/app/docs/reports/FIX_COMERCIAL_DASHBOARD_FUENTE_VENTAS_TABLERO_EJECUTIVO.md:192:| No se tocó MongoDB como fuente principal | ✅ Solo usa EDARSAHUB SQL |
/app/docs/reports/FIX_COMERCIAL_DASHBOARD_FUENTE_VENTAS_TABLERO_EJECUTIVO.md:285:6. ✅ Sin dependencia de MongoDB
/app/docs/reports/COSTOS_ALERTAS_001D_UI_REGLAS_MARGEN_DESTINATARIOS.md:145:| 10 | No MongoDB | ✅ |
/app/docs/reports/COSTOS_ALERTAS_001D_UI_REGLAS_MARGEN_DESTINATARIOS.md:155:- ✅ No se usa MongoDB
/app/docs/reports/COSTOS_ALERTAS_001D_UI_REGLAS_MARGEN_DESTINATARIOS.md:189:| COSTOS-ALERTAS-001-E | Motor de evaluación masiva | PENDIENTE |
/app/docs/reports/FASE_4_EMPRESARESOLVER_READONLY.md:21:- ✅ No se consulta MongoDB como fuente autoritativa
/app/docs/reports/FASE_4_EMPRESARESOLVER_READONLY.md:69:| No consulta MongoDB como fuente autoritativa | ✅ |
/app/docs/reports/SISTEMA_CATALOGO_IMPLEMENTACION.md:149:| 15 | MongoDB NO participa | ✅ |
/app/docs/reports/SISTEMA_CATALOGO_IMPLEMENTACION.md:187:- ✅ MongoDB NO participa
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:6:**Módulo Autorizado:** RBAC MongoDB → EDARSAHUB SQL
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:46:Si se requiere volver a MongoDB:
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:48:2. Las tablas SQL son aditivas, no afectan MongoDB
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:49:3. MongoDB sigue teniendo los datos originales
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:53:## 1. ESTADO ACTUAL DE RBAC EN MONGODB
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:55:### 1.1 Colecciones MongoDB Origen
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:64:### 1.2 Estructura rbac_permisos (MongoDB)
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:78:### 1.3 Estructura rbac_roles (MongoDB)
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:93:### 1.4 Estructura rbac_usuarios_roles (MongoDB)
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:107:### 1.5 Roles MongoDB Actuales
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:136:    CodigoRol VARCHAR(30) NOT NULL,      -- Equivale a "nombre" en MongoDB
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:214:## 3. MAPEO MONGODB → EDARSAHUB SQL
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:218:| MongoDB | SQL Destino | Acción |
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:225:### 3.2 Mapeo de Permisos MongoDB → SQL
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:227:El sistema MongoDB usa códigos compuestos (`MODULO_ACCION`), mientras que SQL usa una matriz `RolID × ModuloID × AccionID`.
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:231:MongoDB:  permiso.codigo = "CARGOS_VER"
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:235:### 3.3 Módulos MongoDB vs SQL (Análisis de Gaps)
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:237:| Módulo MongoDB | ModuloID SQL | Estado |
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:254:### 3.4 Acciones MongoDB vs SQL
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:256:| Acción MongoDB | AccionID SQL | Estado |
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:276:-- Equivalente a rbac_audit_log de MongoDB
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:353:### 5.2 Mapeo de Permisos MongoDB → SQL (Script)
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:356:MONGO_PERMISO = "CARGOS_APLICAR"
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:373:FASE A: Lectura paralela (SQL primero, MongoDB fallback)
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:374:FASE B: Lectura SQL exclusiva (MongoDB solo audit/log temporal)
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:375:FASE C: Eliminación de código MongoDB
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:380:# ANTES (MongoDB):
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:383:    return list(self.db.rbac_roles.find(filtro, {"_id": 0}))
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:390:        logger.warning(f"[RBAC] Fallback MongoDB: {e}")
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:392:        return self._get_roles_mongo_legacy(activos_only)
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:400:- MongoDB permanece como fuente secundaria
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:402:- Si SQL falla, usa MongoDB y registra warning
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:406:- 7 días sin fallbacks MongoDB
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:416:| `/app/backend/core/rbac/repository.py` | Agregar métodos SQL, mantener MongoDB como fallback | ALTO |
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:442:| Permisos incorrectos | MEDIA | Validar matriz SQL vs MongoDB |
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:444:| Errores de conexión SQL | BAJA | Fallback MongoDB temporal |
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:486:USE_SQL_RBAC = False  # Cambiar a False restaura MongoDB como fuente primaria
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:491:- Usuario_PermisosRolModulo puede vaciarse sin impacto (MongoDB sigue teniendo los datos)
/app/docs/reports/FASE_4B_RBAC_PROPUESTA_TECNICA.md:529:   - Opción B: No, mantener audit en MongoDB temporalmente
/app/docs/reports/MIGRACION_CODIGOS_CANONICOS_SISTEMAS_PRO_ENTERPRISE_SAP.md:705:| 11. MongoDB no fue usado como fuente principal | ✅ |
/app/docs/reports/FASE_1C_0_DIAGNOSTICO_COMERCIAL_VENTAS_SUBFASES.md:290:## 7. Dependencias MongoDB Detectadas
/app/docs/reports/FASE_1C_0_DIAGNOSTICO_COMERCIAL_VENTAS_SUBFASES.md:296:✓ No hay referencias a MongoDB en `comercial/routes.py` ni `crm/comercial_routes.py`.
/app/docs/reports/FASE_1C_0_DIAGNOSTICO_COMERCIAL_VENTAS_SUBFASES.md:579:| 14 | No se agregan dependencias MongoDB | ✓ |
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE7_FRONTEND_DINAMICO_REPORTE.md:245:| No tocar MongoDB | ✅ |
/app/docs/reports/DIAGNOSTICO_VENTAS_DIA_MES_14MAY2026.md:272:| No reintroducir MongoDB | ✅ |
/app/docs/reports/historical_load_may_2024_validation_report.json:38:    "mongo_final_inserted": 0
/app/docs/reports/historical_load_may_2024_validation_report.json:60:    "mongo_not_final": "CONFIRMED",
/app/docs/reports/historical_load_may_2024_validation_report.json:67:    "mongo_final_zero": true,
/app/docs/reports/historical_load_may_2024_validation_report.json:79:  "mongo_role": "checkpoint_log_cache_only",
/app/docs/reports/FASE_1C_3F_FRONTEND_SIMULACION_SOLICITUDES_PRECIO.md:185:- ❌ Uso de MongoDB
/app/docs/reports/FASE_1C_3F_FRONTEND_SIMULACION_SOLICITUDES_PRECIO.md:191:## 11. Validaciones Sin MongoDB
/app/docs/reports/FASE_1C_3F_FRONTEND_SIMULACION_SOLICITUDES_PRECIO.md:193:✅ **CONFIRMADO**: No hay ninguna referencia a MongoDB en el componente.
/app/docs/reports/FASE_1C_3F_FRONTEND_SIMULACION_SOLICITUDES_PRECIO.md:227:| Sin MongoDB | ✅ |
/app/docs/reports/plan_finanzas_fase2_control_ingresos_migracion_edarsahub.md:108:3. **MongoDB NO es fuente principal** - solo cache/logs
/app/docs/reports/plan_finanzas_fase2_control_ingresos_migracion_edarsahub.md:868:| 5 | MongoDB no es fuente principal | ✅ No se usa |
/app/docs/reports/FIX_EXPLORADOR_BD_CONEXIONES_EXPLORABLES_DINAMICAS.md:178:## 13. CONFIRMACIÓN DE NO MONGODB
/app/docs/reports/FIX_EXPLORADOR_BD_CONEXIONES_EXPLORABLES_DINAMICAS.md:180:✅ **CONFIRMADO**: Esta corrección NO utiliza MongoDB.
/app/docs/reports/FIX_EXPLORADOR_BD_CONEXIONES_EXPLORABLES_DINAMICAS.md:241:| 9 | No se usa MongoDB | ✅ |
/app/docs/reports/REGRESION_TABLERO_EJECUTIVO_QRO_VENTAS_DIA_CERO.md:152:- ✅ MongoDB no fue usado como fuente principal
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:12:- **8 repositorios** de MongoDB a SQL Server EDARSAHUB
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:13:- **16 servicios** de acceso directo MongoDB a SQL-only
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:19:| `asignacion_repository.py` | 5 refs MongoDB | SQL | ✅ |
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:20:| `configuracion_repository.py` | 1 ref MongoDB | SQL | ✅ |
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:21:| `detalle_diferencias_repository.py` | 4 refs MongoDB | SQL | ✅ |
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:22:| `historial_repository.py` | 3 refs MongoDB | SQL | ✅ |
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:23:| `justificacion_repository.py` | 4 refs MongoDB | SQL | ✅ |
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:24:| `auditoria_repository.py` | 5 refs MongoDB | SQL | ✅ |
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:25:| `historial_responsabilidad_repository.py` | 10 refs MongoDB | SQL | ✅ |
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:26:| `auditoria_programada_repository.py` | 18 refs MongoDB | SQL | ✅ |
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:28:**Total:** 50 referencias `self.collection` eliminadas
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:49:| Collection MongoDB | Tabla SQL |
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:65:### COLLECTION_TO_TABLE_MAP (sql_base_repository.py)
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:68:COLLECTION_TO_TABLE_MAP = {
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:94:### Repositories (CERO MongoDB)
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:154:**Razón:** Es un servicio auxiliar complejo (18 referencias MongoDB) que maneja automatizaciones de compras.
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:179:| Repositories sin MongoDB productivo | ✅ |
/app/docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md:180:| Services sin MongoDB productivo (16/17) | ⚠️ 94% |
/app/docs/reports/FASE_1C_3B_R3_FIX_DECIMAL_FAMILIAS_SR.md:215:| Sin MongoDB | ✅ |
/app/docs/reports/FASE_1C_3E_VALIDACION_RBAC_EXPORTACION.md:67:| Sin MongoDB | ✅ |
/app/docs/reports/FASE_1C_3E_VALIDACION_RBAC_EXPORTACION.md:86:- ✅ **NO** usan MongoDB
/app/docs/reports/FASE_1C_3E_VALIDACION_RBAC_EXPORTACION.md:210:| ✅ Sin MongoDB | Confirmado |
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:1:# P1.4-E4: MIGRACIÓN DB.SERVERS EXPLORADOR/CATÁLOGO — COMPLETADO
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:11:Se migraron exitosamente las referencias a `db.servers` en los endpoints de Explorador/Catálogo y el dashboard metrics, eliminando la dependencia directa de MongoDB y usando `server_registry` (fuente: EDARSAHUB SQL).
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:19:| `POST /explorador/ejecutar-con-credenciales/{server_id}` | 11608 | `db.servers.find_one()` | `server_registry.get_server_connection_info_with_secrets()` |
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:20:| `POST /catalogo/ejecutar-rich/{consulta_id}` | 12370 | `db.servers.find_one()` | `server_registry.get_server_connection_info_with_secrets()` |
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:21:| `GET /dashboard/metrics` | 6529-6532 | `db.servers.count_documents()` | `server_registry.list_servers()` |
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:42:server.py:6529:    total_servers = await db.servers.count_documents({"active": True})
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:43:server.py:6532:    servers_configured = await db.servers.count_documents({"active": True, "queries_configured": True})
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:44:server.py:11608:    server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:45:server.py:12370:    server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:55:✅ **0 referencias activas a `db.servers` en server.py**
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:75:**NOTA:** Estas referencias requieren autorización separada y están documentadas en el reporte de auditoría `/app/docs/reports/MONGODB_DEPENDENCY_AUDIT_EDARSAHUB_SQL.md`.
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:107:| MongoDB no usado como fuente en server.py | ✅ |
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:111:## 8. PROGRESO TOTAL MIGRACIÓN `db.servers`
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:123:**server.py está 100% libre de `db.servers` activo.**
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:131:| Referencias en módulos core/ aún usan MongoDB | Documentado para fases posteriores |
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:132:| Scheduler jobs aún dependen de db.servers | No crítico para operación normal |
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:133:| Scripts de carga histórica usan MongoDB | Solo batch, no afecta producción |
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:141:- ✅ 0 referencias activas a `db.servers` en server.py
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:148:**FASE P1.4 (Migración db.servers en server.py): 100% COMPLETADA**
/app/docs/reports/P1.4-E4_MIGRACION_DB_SERVERS_EXPLORADOR_CATALOGO.md:152:**CIERRE:** P1.4-E4 completado sin regresiones. server.py ya no depende de `db.servers` para ningún endpoint productivo.
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:1:# RBAC-SCOPE-G: Eliminación de Dependencia MongoDB en Usuarios/Roles
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:20:## 2. Flujo Anterior (MongoDB)
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:23:Frontend → API → service.py → repository.py → MongoDB (db.users)
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:26:### Operaciones en MongoDB:
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:27:- `find_user_by_email()` → `db.users.find_one({"email": email})`
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:28:- `find_user_by_id()` → `db.users.find_one({"id": user_id})`
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:29:- `create_user()` → `db.users.insert_one(doc)`
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:30:- `update_user()` → `db.users.update_one({"id": user_id}, {"$set": data})`
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:31:- `deactivate_user()` → `db.users.update_one({"id": user_id}, {"$set": {"active": False}})`
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:54:| `find_user_by_email()` | MongoDB via repository.py | `find_user_by_email_sql()` en user_repository_sql.py |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:55:| `find_user_by_id()` | MongoDB via repository.py | `find_user_by_id_sql()` en user_repository_sql.py |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:56:| `create_user()` | MongoDB via repository.py | `create_user_sql()` en user_repository_sql.py |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:57:| `update_user()` | MongoDB via repository.py | `update_user_sql()` en user_repository_sql.py |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:58:| `deactivate_user()` | MongoDB via repository.py | `deactivate_user_sql()` en user_repository_sql.py |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:63:## 5. Referencias MongoDB Eliminadas
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:77:## 6. Referencias MongoDB Residuales (Justificadas)
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:81:| `repository.py:get_all_users()` | Lee campos `sec_*` de MongoDB | Metadatos RBAC piloto, NO productivos |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:82:| `password_reset.py` | Lee/escribe `db.users` para reset | FUERA DE ALCANCE - Flujo de reset de passwords |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:83:| `context_service.py` | Lee `db.users` para contexto UI | FUERA DE ALCANCE - Contexto de navegación |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:84:| `user_repository_sql.py:compare_user_mongo_vs_sql()` | Comparación diagnóstica | Función pasiva, no productiva |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:114:### Verificación MongoDB:
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:116:db.users.find_one({'email': 'prueba.rbacg@edarsa.com.mx'})
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:117:-- ✅ None (NO existe en MongoDB)
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:162:- ✅ MongoDB no se modifica
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:193:| MongoDB no modificado en CRUD usuarios | ✅ |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:201:| `password_reset.py` sigue usando MongoDB | Migrar en fase futura dedicada | Medio |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:202:| `context_service.py` sigue usando MongoDB | Migrar en fase futura dedicada | Bajo |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:203:| Campos `sec_*` se leen de MongoDB | Son metadatos piloto, no productivos | Bajo |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:227:| Módulo Usuarios/Roles independiente de MongoDB | ✅ (para CRUD productivo) |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:233:| MongoDB no se modifica en CRUD usuarios | ✅ |
/app/docs/reports/RBAC_SCOPE_G_ELIMINACION_MONGODB_USUARIOS_ROLES.md:249:| Ubicación | Solo en SQL (no existe en MongoDB) |
/app/docs/reports/FASE_1C_3G_E2_COSTO_BASE_VINOS_SIN_COSTO.md:183:| 16 | Sin MongoDB | ✅ |
/app/docs/reports/FASE_1C_3A_COSTOS_MARGENES_DISENO_TECNICO.md:1005:| NO MongoDB | Cero dependencias de MongoDB | Grep en código |
/app/docs/reports/FASE_1C_3I_A_MODELO_DATOS_PRICING_IA_BENCHMARK.md:1:# FASE 1C-3I-A: Modelo de Datos para Motor de Precios Sugeridos con IA y Benchmark
/app/docs/reports/FASE_1C_3I_A_MODELO_DATOS_PRICING_IA_BENCHMARK.md:10:Se creó el modelo de datos base en EDARSAHUB SQL para soportar el motor de precios sugeridos con IA, benchmark competitivo y perfil digital de unidad de negocio.
/app/docs/reports/FASE_1C_3I_A_MODELO_DATOS_PRICING_IA_BENCHMARK.md:186:| TipoMotorPrecio | VARCHAR(50) | VINOS_RANGOS, COSTO_MARGEN, BENCHMARK_COMPETENCIA, MIXTO_COSTO_COMPETENCIA, MANUAL_AUTORIZADO |
/app/docs/reports/FASE_1C_3I_A_MODELO_DATOS_PRICING_IA_BENCHMARK.md:264:| 12 | No se usó MongoDB | ✅ |
/app/docs/reports/FASE_1C_3I_A_MODELO_DATOS_PRICING_IA_BENCHMARK.md:387:- ❌ Usar MongoDB como fuente de verdad
/app/docs/reports/FASE_5D_REFACTOR_SCHEDULER_EMPRESARESOLVER_FECHAOPERACION.md:424:4. **P2: FASE 4B** - Migración final fuera de MongoDB
/app/docs/reports/FASE_5D_REFACTOR_SCHEDULER_EMPRESARESOLVER_FECHAOPERACION.md:425:   - Desactivar escrituras a MongoDB
/app/docs/reports/historical_load_sql_destination_validation.json:14:  "mongo_role": "checkpoint_log_staging_only",
/app/docs/reports/historical_load_sql_destination_validation.json:25:    "mongo_final_inserted": 0
/app/docs/reports/historical_load_sql_destination_validation.json:47:  "mongodb_staging_records": {
/app/docs/reports/historical_load_sql_destination_validation.json:49:    "collection": "kpis_comercial",
/app/docs/reports/historical_load_sql_destination_validation.json:68:    "mongo_not_final_destination": true,
/app/docs/reports/historical_load_sql_destination_validation.json:71:    "staging_mongo_documented": true,
/app/docs/reports/historical_load_sql_destination_validation.json:81:    "Evaluar migración de 14 registros MongoDB staging a SQL",
/app/docs/reports/MATRIZ_DEFINITIVA_VENTAS_DIA_SOFTRESTAURANT_MPRO_TURNOS.md:400:| No usa MongoDB | ⚠️ Usa para caché/circuit breaker | ✅ SÍ |
/app/docs/reports/CRM_COMERCIAL_DIAGNOSTICO.md:195:-- Motor de actividades transversal
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:1:# DIAGNÓSTICO: Dependencia MongoDB en Tesorería Cuadres Z
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:3:**Fase:** FINANZAS-TESORERIA-MONGO-001  
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:9:## 1. DEPENDENCIAS MONGODB ENCONTRADAS
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:15:# Línea 18-21: Conexión MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:16:from pymongo import MongoClient
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:17:mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:19:client = MongoClient(mongo_url)
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:21:# Línea 66: Colección MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:22:self.collection_name = "tesoreria_cuadres_z"
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:25:### 1.2 Operaciones MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:26:- `collection.insert_one()` - Crear cuadre
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:27:- `collection.find_one()` - Buscar cuadre
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:28:- `collection.find()` - Listar cuadres
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:29:- `collection.update_one()` - Actualizar cuadre
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:30:- `collection.delete_one()` - Eliminar cuadre
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:31:- `collection.aggregate()` - Resumen estadístico
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:37:| Endpoint | Método | Usa MongoDB | Archivo |
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:54:El frontend usa `server_id` para filtrar por unidad de negocio, pero el backend MongoDB esperaba `sucursal_id`.
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:58:## 4. ESTRUCTURA DE tesoreria_cuadres_z (MongoDB)
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:137:Este repositorio YA EXISTE y NO usa MongoDB. Implementa operaciones CRUD contra `Finanzas_CuadresZ`.
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:144:Se agregaron cambios para soportar `server_id` **SOBRE MongoDB**:
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:149:# PROBLEMA: Estos cambios amplían la dependencia MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:152:### 6.2 En repository_cuadres_z.py (MongoDB)
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:158:# PROBLEMA: Amplía la lógica MongoDB en lugar de migrar a SQL
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:166:## 7. PLAN DE MIGRACIÓN MongoDB → SQL
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:170:# ANTES (MongoDB)
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:189:### Paso 4: Migrar datos existentes de MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:192:# 1. Leer todos los cuadres de MongoDB tesoreria_cuadres_z
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:196:# 5. Deshabilitar escritura en MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:222:| Datos existentes en MongoDB no migrados | Alto | Script de migración único |
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:224:| Cambios recientes ampliaron MongoDB | Medio | Revertir y reemplazar |
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:231:### 10.1 NO continuar ampliando MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:250:- [x] Se identificó exactamente cómo Finanzas/Tesorería usa MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:254:- [x] Se documentaron cambios ya hechos que amplían MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:255:- [x] Se confirma NO continuar ampliando dependencia MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:261:### FINANZAS-TESORERIA-MONGO-002 (Migración)
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:263:1. **Crear script de migración** MongoDB → SQL para cuadres existentes
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:266:4. **Desactivar escritura** en MongoDB para cuadres
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:267:5. **Mantener lectura MongoDB** como fallback temporal (solo lectura, con warning)
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:268:6. **Eliminar fallback MongoDB** después de validación en producción
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:273:- Eliminar colección MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:279:**La dependencia MongoDB en Tesorería Cuadres es REMEDIABLE.**
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:289:3. Validar y deprecar MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md:291:**Los cambios realizados el 2026-05-26 sobre MongoDB deben PAUSARSE y no continuarse.**
/app/docs/reports/RECONCILIACION_CIENFUEGOS_MAYO_2026_DIAS_FALTANTES.md:358:- Fuente: EDARSAHUB SQL (NO MongoDB)
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:13:Migrar el módulo `context_service.py` para que el contexto de navegación/UI deje de depender productivamente de MongoDB y use EDARSAHUB SQL como fuente.
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:21:| `get_db()` import | Conexión MongoDB | **ELIMINADA** - Reemplazada por `_get_sql_connection()` |
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:28:## 3. Colecciones MongoDB Eliminadas del Flujo
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:30:| Colección MongoDB | Tabla SQL Reemplazo |
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:32:| `db.users` | `Usuario_Catalogo` |
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:33:| `db.empresas` | `Sistema_Empresas` + `Sistema_EmpresasMongoMap` |
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:34:| `db.rbac_usuarios_roles` | `Usuario_RolesAsignacion` |
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:35:| `db.rbac_roles` | `Usuario_Roles` |
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:36:| `db.rbac_permisos` | (No migrado - permisos desde user dict) |
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:37:| `db.sucursales_catalogo` | `Sistema_Sucursales` |
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:50:| `Sistema_EmpresasMongoMap` | Mapeo UUID MongoDB → ID SQL | EmpresaMongoUUID, EmpresaID_SQL |
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:67:| `_get_empresa_by_uuid_sql()` | Empresa por UUID MongoDB |
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:77:**ANTES (MongoDB):**
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:102:    "empresa_default": {"id": "uuid-mongo", "nombre": "Empresa", "codigo": "EMP"},
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:103:    "empresas_permitidas": [{"id": "uuid-mongo", "nombre": "Empresa", "codigo": "EMP"}],
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:117:- IDs: Mantienen UUIDs MongoDB para compatibilidad con frontend
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:163:$ grep -R "db.empresas" /app/backend/modules/auth/context_service.py
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:166:$ grep -R "db.sucursales_catalogo" /app/backend/modules/auth/context_service.py
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:169:$ grep -R "db.sucursal_servidor_map" /app/backend/modules/auth/context_service.py
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:172:$ grep -R "db.server_sucursales_config" /app/backend/modules/auth/context_service.py
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:175:$ grep -R "db.servers" /app/backend/modules/auth/context_service.py
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:178:$ grep -R "db.users" /app/backend/modules/auth/context_service.py
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:181:$ grep -R "db.rbac_usuarios_roles" /app/backend/modules/auth/context_service.py
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:184:$ grep -R "db.rbac_roles" /app/backend/modules/auth/context_service.py
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:187:$ grep -R "db.rbac_permisos" /app/backend/modules/auth/context_service.py
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:193:$ grep -R "AsyncIOMotorClient" /app/backend/modules/auth/context_service.py
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:197:**Total referencias MongoDB productivas: 0**
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:222:| `db.rbac_permisos` | No hay tabla SQL equivalente | BAJO - Funcionalidad no afectada |
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:231:| RBAC MongoDB obsoleto pero existente | Considerar limpieza en fase posterior |
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:254:1. **Auditar todas las referencias MongoDB** en la capa de contexto (context_resolver, user_access_context, context_service).
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:260:   - `rbac_usuarios_roles` MongoDB obsoleto
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:262:4. **Considerar limpieza** de colecciones MongoDB que ya no son fuente productiva.
/app/docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md:271:| 0 referencias MongoDB productivas | ✅ |
/app/docs/reports/FASE_2_DML_CONSULTAS_SQL_CATALOGO_EJECUCION.md:182:| No se borró MongoDB | ✅ |
/app/docs/reports/FIX_P0_VENTAS_DIA_MPRO_EDARSAHUB_SQL.md:247:- [x] MongoDB NO fue usado como fuente autoritativa
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE1_DIAGNOSTICO.md:28:Diseñar e implementar un **Catálogo Maestro de Sistemas + Motor de Capacidades** donde:
/app/docs/reports/FIX_CIRCUIT_BREAKER_HUB_TABLERO_EJECUTIVO.md:36:is_server_recently_offline() ──► MongoDB: server_status
/app/docs/reports/FIX_CIRCUIT_BREAKER_HUB_TABLERO_EJECUTIVO.md:43:get_cached_kpis() ──► MongoDB: kpis_cache (datos viejos)
/app/docs/reports/FIX_CIRCUIT_BREAKER_HUB_TABLERO_EJECUTIVO.md:51:- El circuit breaker verificaba estado de conexión del **servidor local** en MongoDB
/app/docs/reports/FIX_CIRCUIT_BREAKER_HUB_TABLERO_EJECUTIVO.md:53:- Resultado: Se servían datos de caché MongoDB en lugar de datos frescos de EDARSAHUB SQL
/app/docs/reports/FIX_CIRCUIT_BREAKER_HUB_TABLERO_EJECUTIVO.md:88:### Cambio 2: No guardar estado MongoDB para HUB (líneas ~798-811)
/app/docs/reports/FIX_CIRCUIT_BREAKER_HUB_TABLERO_EJECUTIVO.md:183:### MongoDB NO es fuente primaria
/app/docs/reports/FIX_CIRCUIT_BREAKER_HUB_TABLERO_EJECUTIVO.md:184:- El circuit breaker de MongoDB (`server_status`) ya no bloquea lecturas HUB
/app/docs/reports/FIX_CIRCUIT_BREAKER_HUB_TABLERO_EJECUTIVO.md:185:- La caché MongoDB (`kpis_cache`) solo se usa si EDARSAHUB SQL falla
/app/docs/reports/CORRECCION_KPIS_COMPARATIVOS_GLOBAL.md:168:- ✅ MongoDB no participa
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:1:# AUDITORÍA: USOS DE MONGODB VS EDARSAHUB
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:16:| **MongoDB** | Infraestructura técnica + cache + legacy | ⚠️ Mixto (técnico + legacy) |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:18:**Hallazgo crítico:** La autenticación de usuarios actualmente usa **MongoDB** como fuente, NO EDARSAHUB. Esto es un **uso legacy** que debería migrarse eventualmente.
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:22:## 2. COLECCIONES MONGODB ENCONTRADAS
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:100:### A. USO ACEPTABLE / TÉCNICO (Mantener en MongoDB)
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:205:| ¿Dónde viven usuarios reales? | **MongoDB** (`users` collection) |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:206:| ¿Dónde vive RBAC real? | **MongoDB** (`rbac_roles`, `rbac_permisos`, `rbac_usuarios_roles`) |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:207:| Fuente actual de auth | **MongoDB** (100%) |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:210:### 5.9 La autenticación actual usa EDARSAHUB o MongoDB?
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:212:**RESPUESTA: MongoDB**
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:219:El login busca usuarios en `MongoDB.users`, NO en EDARSAHUB.
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:221:### 5.10 ¿Qué parte del código todavía busca usuarios en MongoDB?
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:234:| Tipo | Usa MongoDB | Usa EDARSAHUB |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:252:**Puede quedarse en MongoDB (técnico):**
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:259:- Guardar ventas, KPIs, cortes, propinas oficiales en MongoDB
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:260:- Usar MongoDB como fuente de verdad financiera/comercial
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:264:**Riesgo de quitar MongoDB de golpe:** 🔴 CRÍTICO
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:276:6. Mantener MongoDB solo para infraestructura técnica
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:286:| **MongoDB** | `users` | 15 | ✅ SÍ (actual) |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:290:**Conclusión:** Los usuarios reales viven en **MongoDB**. EDARSAHUB tiene tablas de usuarios pero NO se usan para autenticación.
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:296:| **MongoDB** | `rbac_roles`, `rbac_permisos`, `rbac_usuarios_roles` | ✅ SÍ |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:299:**Conclusión:** RBAC vive en **MongoDB**.
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:301:### 6.3 ¿Por qué un script buscó usuarios en MongoDB?
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:303:El script de diagnóstico ejecutado buscó en MongoDB porque:
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:304:1. El sistema de auth usa MongoDB para usuarios
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:305:2. El repositorio `modules/auth/repository.py` está configurado para MongoDB
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:310:No, el script refleja la realidad del sistema. El auth **actualmente** usa MongoDB.
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:312:### 6.5 ¿Hay endpoints de auth que todavía consultan MongoDB?
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:316:| Endpoint | Consulta MongoDB |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:323:### 6.6 ¿Hay fallback de auth a MongoDB?
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:325:No hay fallback porque MongoDB **ES** la fuente primaria de auth. No hay fuente secundaria.
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:327:### 6.7 ¿Hay riesgo de crear usuarios temporales en MongoDB otra vez?
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:329:**SÍ.** Cualquier llamada a `create_user()` en `modules/auth/repository.py` crea usuarios en MongoDB.
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:335:3. Documentar que MongoDB es temporal para auth
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:345:| Comercial v2 no usa MongoDB cache | ✅ CONFIRMADO | No hay imports de `get_db()` en módulo v2 |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:346:| Comercial v2 solo usa MongoDB para lock técnico | ✅ CONFIRMADO | Scheduler usa `DistributedLock` de MongoDB |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:347:| Frontend v2 no depende de MongoDB | ✅ CONFIRMADO | Frontend llama a `/api/v2/comercial/*` que lee EDARSAHUB |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:348:| Feature flag no depende de MongoDB | ✅ CONFIRMADO | Flag es variable de entorno |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:353:# Resultado: 0 líneas (no usa MongoDB)
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:360:| Módulo | Fuente principal | MongoDB usado para |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:367:**Nota:** `auditoria_financiera` (73 docs) en MongoDB es legacy y debería evaluarse para migración.
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:373:| Aspecto | MongoDB | EDARSAHUB |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:381:- MongoDB: Infraestructura técnica de coordinación
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:390:| Quitar MongoDB sin migrar auth | Alta | 🔴 Crítico | NO quitar MongoDB |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:391:| Inconsistencia usuarios MongoDB vs EDARSAHUB | Media | 🟡 Alto | Migrar auth a EDARSAHUB |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:393:| Crear usuarios en MongoDB accidentalmente | Media | 🟡 Alto | Documentar, no crear en scripts |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:406:- Mantener `servers` de MongoDB como fallback temporal
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:459:| `/app/backend/core/db.py` | ✅ INTACTO |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:460:| Colecciones MongoDB | ✅ SIN CAMBIOS |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:470:## 14. DECISIÓN DE CIERRE — AUTH/RBAC QUEDA EN MONGODB TEMPORALMENTE
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:483:| Usuarios no pueden ingresar | Alta | 🔴 CRÍTICO | Login depende de MongoDB |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:499:| `users` collection | ❌ NO TOCAR |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:500:| `rbac_*` collections | ❌ NO TOCAR |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:504:| `servers` collection | ❌ NO TOCAR |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:517:| 3 | Mantener MongoDB para Auth/RBAC | ✅ Temporal aceptado |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:518:| 4 | Mantener MongoDB para locks/logs | ✅ Técnico aceptado |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:537:| 1 | Auditoría de usuarios MongoDB vs EDARSAHUB |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:540:| 4 | Mapeo `MongoDB.users` → `EDARSAHUB.Usuario_*` |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:541:| 5 | Mapeo `MongoDB.rbac_*` → `EDARSAHUB.Usuario_Roles/Permisos` |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:546:| 10 | Rollback inmediato a MongoDB (< 1 min) |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:552:### 14.5 MONGODB PERMITIDO TEMPORALMENTE
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:570:### 14.6 MONGODB PROHIBIDO PARA NUEVOS DATOS DE NEGOCIO
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:572:**PROHIBIDO usar MongoDB como fuente para:**
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:600:| `/app/backend/core/db.py` | ✅ INTACTO |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:603:| Colecciones MongoDB | ✅ SIN CAMBIOS |
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:617:│  Auth/RBAC: QUEDA EN MONGODB (temporal)                    │
/app/docs/reports/auditoria_usos_mongodb_vs_edarsahub.md:619:│  Scheduler: MONGODB para locks/logs (correcto)             │
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:1:# FASE 1: Circuit Breaker HUB - EDARSAHUB SQL (No MongoDB)
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:15:El endpoint `/api/comercial/tablero-ejecutivo` consultaba MongoDB (`server_status`) para determinar si un servidor estaba "offline" mediante `should_attempt_live_query()`. Si el servidor estaba marcado como offline, el sistema usaba `kpis_cache` de MongoDB como fallback.
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:40:| 798-811 | `tablero_ejecutivo()` | NO guarda estado MongoDB para HUB |
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:42:| 967-1032 | `tablero_ejecutivo()` | Si error y HUB: `EDARSAHUB_SQL_ERROR`, NO caché MongoDB |
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:59:Request → should_attempt_live_query() → MongoDB server_status
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:65:  EDARSAHUB SQL      kpis_cache MongoDB ❌
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:100:## 5. CONFIRMACIÓN: MODO HUB NO USA MONGODB
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:105:- ✅ NO se consulta MongoDB `server_status`
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:109:- ✅ Si EDARSAHUB SQL falla → `EDARSAHUB_SQL_ERROR` (NO `kpis_cache` MongoDB)
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:168:### `server_status` (MongoDB circuit breaker)
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:175:### `kpis_cache` (MongoDB fallback)
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:195:| MongoDB fallback para LIVE | Preservado solo para LIVE-C | ✅ Aceptable |
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:196:| Dashboard individual (línea 4282) | Usa circuit breaker MongoDB | ⚠️ Fase 2 |
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:219:| Modo HUB no consulta MongoDB para circuit breaker | ✅ CUMPLIDO |
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:220:| Modo HUB no usa `kpis_cache`/`dashboard_cache` MongoDB | ✅ CUMPLIDO |
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:259:   - **Resultado:** La query no encontraba registros → Fallback a caché MongoDB con datos viejos
/app/docs/reports/COMERCIAL_CIRCUIT_BREAKER_FASE1_HUB_SQL_NO_MONGO.md:278:- MongoDB `kpis_cache` con datos desactualizados
/app/docs/reports/FASE_1C_3G_F_PRECIOS_SUGERIDOS_COSTOS_MARGENES_RANGOS_VINOS.md:235:## 10. Evidencia CERO MongoDB
/app/docs/reports/FASE_1C_3G_F_PRECIOS_SUGERIDOS_COSTOS_MARGENES_RANGOS_VINOS.md:238:- ✅ No hay importaciones de MongoDB en código nuevo
/app/docs/reports/FASE_1C_3G_F_PRECIOS_SUGERIDOS_COSTOS_MARGENES_RANGOS_VINOS.md:297:| CERO MongoDB | ✅ |
/app/docs/reports/MATRIZ_MENU_ENDPOINT_TABLA_SYNC_EDARSAHUB.csv:1:Modulo,Menu,RutaFrontend,ArchivoFrontend,Endpoint,ArchivoBackend,TablaEDARSAHUB,JobSync,OrigenSync,Frecuencia,UsaSelectedServer,SelectedServerModo,UsaUnidadNegocioID,UsaEmpresaID,UsaServidorConexionID,LeeMongoDB,FallbackMongoDB,CacheFrontend,CacheBackend,ConexionLive,Clasificacion,Riesgo,Correccion,Prioridad
/app/docs/reports/MATRIZ_MENU_ENDPOINT_TABLA_SYNC_EDARSAHUB.csv:22:Operaciones,Reportes/Dashboard,/reportes,Reportes.js,GET /api/operaciones/*,fase2_operativo/*.py,NINGUNA,NINGUNO,N/A,N/A,SI,FILTRO_LOGICO,SI,SI,NO,SI,SI,React Query,NO,NO,VIOLACION_MONGODB,ALTO,Migrar a SQL,P0
/app/docs/reports/MATRIZ_MENU_ENDPOINT_TABLA_SYNC_EDARSAHUB.csv:23:Operaciones,Tareas,/mis-tareas,MisTareas.js,GET /api/tareas/*,fase2_operativo/repositories/tarea_repository.py,NINGUNA,NINGUNO,N/A,N/A,NO,N/A,NO,NO,NO,SI,NO,React Query,NO,NO,VIOLACION_MONGODB,ALTO,Migrar a SQL,P0
/app/docs/reports/MATRIZ_MENU_ENDPOINT_TABLA_SYNC_EDARSAHUB.csv:24:Operaciones,Workflows,N/A,N/A,GET /api/workflows/*,fase2_operativo/repositories/workflow_repository.py,NINGUNA,NINGUNO,N/A,N/A,NO,N/A,NO,NO,NO,SI,NO,NO,NO,NO,VIOLACION_MONGODB,ALTO,Migrar a SQL,P0
/app/docs/reports/MATRIZ_MENU_ENDPOINT_TABLA_SYNC_EDARSAHUB.csv:26:Finanzas,Finanzas,/finanzas,Finanzas.js,GET /api/finanzas/*,finanzas/routes.py,Finanzas_*,N/A,Manual,N/A,SI,FILTRO_LOGICO,SI,SI,NO,PARCIAL,PARCIAL,React Query,NO,PARCIAL,RIESGO_MONGODB,MEDIO,Auditar y migrar,P1
/app/docs/reports/MATRIZ_MENU_ENDPOINT_TABLA_SYNC_EDARSAHUB.csv:27:Finanzas,Cuadres Z,N/A,N/A,GET /api/finanzas/cuadres-z,finanzas/repository_cuadres_z.py,NINGUNA,NINGUNO,N/A,N/A,SI,CONEXION_REAL,NO,NO,SI,SI,NO,NO,NO,PARCIAL,VIOLACION_MONGODB,ALTO,Migrar a SQL,P1
/app/docs/reports/FASE_ESTANDARIZACION_NOMBRES_UNIDADES_NEGOCIO.md:15:3. **`Sistema_EmpresasMongoMap`**: Mapeo MongoDB correcto ✅
/app/docs/reports/FASE_ESTANDARIZACION_NOMBRES_UNIDADES_NEGOCIO.md:211:    OrigenAlias NVARCHAR(50),                -- De dónde vino: 'MONGO', 'SOFTRESTAURANT', 'MPRO', 'MANUAL'
/app/docs/reports/FASE_1A_COMERCIAL_VENTAS_MENU_GOBERNADO.md:134:| 26 | No MongoDB como fuente | ✅ PASS |
/app/docs/reports/FASE_1A_COMERCIAL_VENTAS_MENU_GOBERNADO.md:162:| Endpoint `/api/comercial/dashboard/{id}` error 500 | BAJA | DOCUMENTADO (usa MongoDB internamente - fuera de alcance) |
/app/docs/reports/FASE_1A_COMERCIAL_VENTAS_MENU_GOBERNADO.md:187:| Dashboard Comercial usa MongoDB | BAJA | BAJO | Fuera de alcance FASE 1A |
/app/docs/reports/auditoria_parseo_conexiones_sqlserver.md:41:**Solución:** Usar `core.db.parse_sql_server_host()` que preserva hostname, puerto e instancia.
/app/docs/reports/auditoria_parseo_conexiones_sqlserver.md:50:3. No uso de `core.db.parse_sql_server_host()`
/app/docs/reports/auditoria_parseo_conexiones_sqlserver.md:88:- `/app/backend/core/db.py`
/app/docs/reports/auditoria_parseo_conexiones_sqlserver.md:285:### 9. Core (db.py, server_registry.py, resilient_sql.py)
/app/docs/reports/auditoria_parseo_conexiones_sqlserver.md:311:1. **Todos los módulos** deben usar `core.db.parse_sql_server_host()` para parsear hosts SQL Server.
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_SQLFIRST_REPORTE.md:26:**Catálogo Maestro de Sistemas + Motor de Capacidades** donde:
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_SQLFIRST_REPORTE.md:129:- EDARSAHUB SQL (NO MongoDB)
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_SQLFIRST_REPORTE.md:202:9. [ ] Confirmar no se usa MongoDB
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:70:| Fuente de datos | SQL vivo + MongoDB cache | EDARSAHUB (tablas v2) |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:232:| MongoDB | No se toca |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:423:| Fuente de datos | SQL vivo + MongoDB cache |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:609:| MongoDB | ✅ INTACTO |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:712:| Fuente | SQL vivo + MongoDB cache | EDARSAHUB (tablas v2) |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:1898:| MongoDB | ✅ Running |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:1976:| **Lock distribuido** | MongoDB (`sync_comercial_v2`) |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:2056:2. **Lock distribuido**: Evita ejecuciones simultáneas usando MongoDB
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:2191:- ❌ MongoDB cache
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:2333:| No MongoDB | Verificar código | Sin llamadas a MongoDB |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:2375:| MongoDB | Sigue funcionando como cache (aunque no se use en v2) |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:2421:5. [ ] Sin MongoDB como fuente
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:2510:| MongoDB cache | NO | NO | ✅ |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:2539:- [x] No consultan MongoDB cache
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:2621:4. **core.db.execute_sql_query()**: Fallaba porque el servidor estaba en **cooldown** (cache de estado offline) y el **pool de conexiones** estaba corrupto
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:2859:| MongoDB | ✅ Sin cambios |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:2874:- MongoDB
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:3025:| MongoDB legacy (servers) | ✅ | Existe pero no se requiere |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:3155:| MongoDB | ✅ Sin cambios |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:3412:| MongoDB NO modificado | ✅ |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:3445:- ✅ MongoDB: Sin cambios
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:3727:✅ MongoDB colecciones                           (sin cambios)
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:3813:Frontend → Backend → SQL VIVO (sucursales) → Cache MongoDB si falla
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:3843:                     │   MongoDB    │◀────│   Fallback   │
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:4212:| **v1** | SQL vivo | MongoDB cache | Confusión Online/Cache |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:4232:### 9.1 v1 (Actual): Fallback a MongoDB
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:4235:SQL sucursal FALLA → usar MongoDB cache (kpis_cache)
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:4835:| **Lock** | `sync_comercial_abiertas_v2` (MongoDB) |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:5205:| 12 | No MongoDB como fuente comercial | ✅ |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:5347:│  │      → NO usa MongoDB cache                               │   │
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:5393:| **Lock** | MongoDB (solo control técnico) |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:5430:    Fuente: EDARSAHUB (NO SQL vivo, NO MongoDB)
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:5446:### 21.7 CONFIRMACIÓN: NO USA MONGODB CACHE
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:5451:- No hay imports de `motor`, `pymongo`, ni funciones de MongoDB
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:5452:- MongoDB solo se usa para:
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:5500:| 3 | Auth/RBAC en MongoDB (deuda técnica) | ✅ Documentado, no afecta datos comerciales |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:5513:| 6 | ¿Hay ruta que use MongoDB cache? | ❌ No (solo locks técnicos) |
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:6256:- MongoDB: INTACTO
/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md:6647:- Cache MongoDB
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:12:Se completó la migración del archivo `cargos_repository.py` de MongoDB a SQL Server EDARSAHUB.
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:14:### Antes (MongoDB)
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:15:- 29 referencias a `self.collection`
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:17:- Herencia de `BaseRepository` (MongoDB)
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:18:- Operaciones síncronas con colecciones pymongo
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:21:- 0 referencias a `self.collection`
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:22:- 0 dependencias de MongoDB/bson/pymongo
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:31:| Campo SQL | Campo MongoDB Equivalente |
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:51:| Campo SQL | Campo MongoDB Equivalente |
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:86:## 4. Verificación GREP (CERO MongoDB)
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:89:$ grep -n "self.collection" cargos_repository.py
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:95:$ grep -n "pymongo" cargos_repository.py
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:112:   - collection_name: cargos_economicos
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:116:   - collection_name: cargos_economicos_log
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:149:| No queda MongoDB productivo en el repositorio | ✅ |
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:150:| No queda self.collection | ✅ |
/app/docs/reports/FASE_B_P1_D_CARGOS_REPOSITORY_SQL.md:160:- **FASE B-P2:** Auditar y migrar servicios con acceso directo a Mongo
/app/docs/reports/historical_load_cienfuegos_complete_report.json:13:    "mongo_final_inserted": 0
/app/docs/reports/historical_load_cienfuegos_complete_report.json:26:    "mongo_final_zero": "CONFIRMED",
/app/docs/reports/TABLAJERIA_VALIDACION_BLINDAJE_REPORTE.md:78:### ✅ NO USA MONGODB
/app/docs/reports/TABLAJERIA_VALIDACION_BLINDAJE_REPORTE.md:80:grep -rn "mongo|MongoDB|pymongo" /app/backend/modules/tablajeria/ 
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:14:- Modo: SQL-first con fallback MongoDB activo
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:30:| superadmin2@test.com | SuperAdministrador | 0 | MongoDB | Sí ✓ |
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:34:- 1 usuario @test.com: `MongoDB` (esperado - no migrado a SQL)
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:44:| MongoDB (fallback) | 1 | superadmin2@test.com |
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:57:## 5. Fallbacks MongoDB
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:67:## 6. Comparativa SQL-First vs MongoDB-First
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:71:| Campo | SQL-First | MongoDB-First |
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:86:| MongoDB-First | 4 | ORIGEN, 130QRO, CIENFUEGOS, 130MID |
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:143:- ✓ Tiene mapeo en `Sistema_EmpresasMongoMap` (UUID=e302e16f-2d97-4119-9ad9-bb5b00b71367)
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:194:### ¿Se puede eliminar el fallback MongoDB?
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:198:1. **Usuarios @test.com:** Aún existen usuarios @test.com activos en MongoDB que no fueron migrados (por diseño). Si se elimina el fallback, perderían acceso.
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:225:| 3 | Fallback MongoDB funciona | ✅ |
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:231:| 9 | No hay usuarios productivos usando MONGODB_FALLBACK | ✅ |
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:244:| No hay fallback MongoDB para usuarios productivos migrados | ✅ |
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:257:- El fallback MongoDB está operativo para usuarios @test.com (no migrados).
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:260:- El sistema puede volver a MongoDB-first inmediatamente cambiando el feature flag.
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:270:| `/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md` | Reporte FASE 2-E |
/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md:275:*SQL Server es la fuente primaria de autenticación. Fallback MongoDB activo para usuarios no migrados.*
/app/docs/reports/FASE_1B_SANITIZACION_SQL_VULNERABILIDADES_ALTAS.md:248:- MongoDB (no escritura)
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:23:| **Consultas Personalizadas** | MongoDB `db.consultas_custom` | ⚠️ PENDIENTE |
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:25:| **MongoDB db.servers** | **0 documentos** (desacoplado) | ✅ DESACTIVADO |
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:26:| **MongoDB db.consultas_custom** | **0 documentos** (sin uso actual) | ✅ SIN USO |
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:50:| `/app/backend/server.py` (líneas 12308-12630) | Endpoints `/api/catalogo/*` | **HÍBRIDO** (Python + MongoDB) |
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:84:| `/api/catalogo/consultas-rich` | GET | Python + MongoDB | ⚠️ HÍBRIDO |
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:85:| `/api/catalogo/ejecutar-rich/{id}` | POST | Python + MongoDB | ⚠️ HÍBRIDO |
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:86:| `/api/catalogo/consultas/{id}` | PUT | MongoDB | ⚠️ MONGODB |
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:87:| `/api/catalogo/consultas-custom` | POST | MongoDB | ⚠️ MONGODB |
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:88:| `/api/catalogo/consultas-custom/{id}` | DELETE | MongoDB | ⚠️ MONGODB |
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:94:### A) MongoDB `db.servers`
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:98:- El sistema ya NO depende de `db.servers` para operación normal
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:99:- El fallback a MongoDB sigue en código pero retorna vacío
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:102:### B) MongoDB `db.consultas_custom`
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:177:### MongoDB `db.servers` (Esquema Histórico)
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:203:-- Todos los campos de MongoDB más:
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:225:| B2 | 🟡 MEDIA | Fallback MongoDB | Código de fallback sigue presente aunque retorna vacío |
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:294:- Eliminar fallback MongoDB
/app/docs/reports/DIAGNOSTICO_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:321:5. ✅ **MongoDB db.servers** - Desacoplado (0 documentos)
/app/docs/reports/FASE_1C_3G_D_PRODUCTOS_CLASIFICADOS_VINO_EXTENSION_ATRIBUTOS.md:242:| 12 | Sin MongoDB | ✅ |
/app/docs/reports/FASE_1C_3G_B_DIAGNOSTICO_CORRECCION_IMPUESTOS_MPRO.md:188:| 7 | Sin uso de MongoDB | ✅ |
/app/docs/reports/FASE_1C_3I_G_LISTAS_MANUALES_COMPETIDORES_PRICING_IA.md:168:| CERO MongoDB | ✅ OK |
/app/docs/reports/FASE_1C_3I_G_LISTAS_MANUALES_COMPETIDORES_PRICING_IA.md:205:## 12. Validación de No Uso de MongoDB
/app/docs/reports/FASE_1C_3I_G_LISTAS_MANUALES_COMPETIDORES_PRICING_IA.md:264:- ✅ Sin dependencias de MongoDB
/app/docs/reports/FASE_1C_3G_B_SYNC_REAL_IMPUESTOS_MPRO.md:95:| 17 | No se usa MongoDB | ✅ |
/app/docs/reports/FASE_1B_R1_NO_LIVE_DASHBOARD_COMERCIAL_CORRECCION.md:115:| No se consulta MongoDB | ✅ PASS |
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:9:## 1. FLUJO ANTERIOR (MongoDB)
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:13:1. check_rate_limit() → MongoDB.rate_limit_password_reset.find_one()
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:14:2. increment_rate_limit() → MongoDB.rate_limit_password_reset.update_one()
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:15:3. audit_log() → MongoDB.audit_password_reset.insert_one()
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:20:2. audit_log() → MongoDB.audit_password_reset.insert_one()
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:23:**Dependencias MongoDB:**
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:24:- `db.rate_limit_password_reset` - Colección para rate limiting
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:25:- `db.audit_password_reset` - Colección para auditoría
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:26:- `MongoClient` - Cliente de conexión
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:50:**Dependencias MongoDB:** NINGUNA
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:59:**Reemplaza:** MongoDB collection `rate_limit_password_reset`
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:80:**Reemplaza:** MongoDB collection `audit_password_reset`
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:150:115:    AUTH-RESET-P2: Reemplaza MongoDB rate_limit_password_reset.
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:151:162:    AUTH-RESET-P2: Reemplaza MongoDB rate_limit_password_reset.
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:155:209:    AUTH-RESET-P2: Reemplaza MongoDB audit_password_reset.
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:161:$ grep -n "MongoClient" /app/backend/modules/auth/password_reset.py
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:167:$ grep -n "AsyncIOMotorClient" /app/backend/modules/auth/password_reset.py
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:171:**Resultado:** ✅ 0 referencias activas a MongoDB en password_reset.py
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:223:## 9. CONFIRMACIÓN: password_reset.py YA NO DEPENDE DE MONGODB
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:227:| `MongoClient` | ❌ Eliminado |
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:229:| `db.rate_limit_password_reset` | ❌ Eliminado |
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:230:| `db.audit_password_reset` | ❌ Eliminado |
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:235:**Declaración:** El módulo `password_reset.py` es ahora **100% SQL**. No tiene dependencias funcionales de MongoDB.
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:241:1. **Limpieza de datos históricos:** Las colecciones MongoDB `rate_limit_password_reset` y `audit_password_reset` siguen existiendo con datos históricos. No se eliminarán hasta fase de limpieza autorizada.
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:245:3. **RBAC-DUPKEY-001:** Error conocido en init de MongoDB (índices duplicados en RBAC). No afecta este módulo pero aparece en logs.
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:259:2. **MongoDB en password_reset.py:** ❌ Eliminado completamente
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:262:   - Auditar otros módulos que aún usen MongoDB
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:263:   - Identificar reglas de negocio en MongoDB
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:267:   - Colecciones MongoDB vacías sin uso
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:278:| 3 | password_reset.py sin MongoDB | ✅ |
/app/docs/reports/AUTH_RESET_P2_RATE_LIMIT_AUDIT_SQL.md:289:AUTH-RESET-P2 ha sido completado exitosamente. El módulo `password_reset.py` ahora es **100% EDARSAHUB SQL** sin dependencias de MongoDB. Las nuevas tablas `Usuario_RateLimitRecuperacion` y `Usuario_LogRecuperacion` manejan rate limiting y auditoría respectivamente, siguiendo el patrón de nomenclatura `Usuario_*` establecido en EDARSAHUB.
/app/docs/reports/auditoria_finanzas_fase2_control_ingresos.md:446:| 1 | No usar MongoDB como fuente principal de configuración | ✅ Confirmado - Usar EDARSAHUB SQL |
/app/docs/reports/auditoria_finanzas_fase2_control_ingresos.md:895:| 7 | No usar MongoDB como fuente | ✅ No se usa |
/app/docs/reports/FASE_3_DML_CATALOGO_EMPRESAS_SERVIDORES_SUCURSALES_EJECUTADO.md:253:| No se usó MongoDB como fuente | ✅ CONFIRMADO |
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:6:**Módulo Migrado:** RBAC MongoDB → EDARSAHUB SQL
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:87:Matriz de permisos migrada desde MongoDB `rbac_roles.permisos`:
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:100:- **Origen:** Colección MongoDB `rbac_audit_log`
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:289:## 16. GREP FINAL DE DEPENDENCIAS MONGODB EN RBAC
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:291:### 16.1 Referencias MongoDB en archivos RBAC:
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:293:/app/backend/core/rbac/middleware.py:36:    from pymongo import MongoClient
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:294:/app/backend/core/rbac/middleware.py:37:    mongo_url = os.environ.get('MONGO_URL', ...)
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:295:/app/backend/core/rbac/routes.py:28:from pymongo import MongoClient
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:296:/app/backend/core/rbac/routes.py:48:    mongo_url = os.environ.get('MONGO_URL', ...)
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:300:- **middleware.py y routes.py:** Obtienen conexión MongoDB para pasar a `RBACService(db)`
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:306:> Las referencias MongoDB en middleware.py y routes.py son **compatibilidad de firma**, no dependencia funcional.
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:312:## 17. CONFIRMACIÓN: CERO FALLBACK MONGODB FUNCIONAL EN RBAC
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:316:| Componente | Usa MongoDB | Usa SQL |
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:335:> **MongoDB NO participa como fuente de datos funcional para RBAC.**
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:337:> **No existe fallback a MongoDB en operaciones RBAC.**
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:346:| Referencias MongoDB legacy en middleware/routes | BAJA | NINGUNO | Son compatibilidad de firma, no funcionales |
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:347:| Error DuplicateKey en init MongoDB | BAJA | NINGUNO | RBAC-DUPKEY-001 conocido, no afecta operaciones |
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:353:### Rollback Inmediato (si se requiere volver a MongoDB):
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:371:- Las tablas SQL son **aditivas**, no destruyen datos MongoDB
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:372:- MongoDB **sigue teniendo** las colecciones RBAC originales
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:373:- No se eliminaron colecciones MongoDB
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:374:- No se modificó MongoDB
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:378:## 20. CONFIRMACIÓN: COLECCIONES MONGODB NO ELIMINADAS
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:382:| Colección MongoDB | Estado | Registros |
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:389:> **No se eliminaron colecciones MongoDB.**
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:390:> **No se modificaron datos MongoDB.**
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:391:> **MongoDB permanece como histórico legacy temporal.**
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:406:| Fallback MongoDB | ✅ ELIMINADO |
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:407:| Colecciones MongoDB | ✅ PRESERVADAS |
/app/docs/reports/FASE_4B_RBAC_EJECUCION_FINAL.md:412:> **MongoDB ya NO es fuente de datos funcional para RBAC.**
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:13:Migrar el módulo `context_resolver.py` para que lea empresas, sucursales, mapeos y servidores desde EDARSAHUB SQL en lugar de MongoDB.
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:21:| `_get_db()` | Conexión MongoDB | **ELIMINADA** - Reemplazada por `_get_sql_connection()` |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:30:## 3. Colecciones MongoDB Eliminadas del Flujo
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:32:| Colección MongoDB | Tabla SQL Reemplazo |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:34:| `db.empresas` | `Sistema_Empresas` + `Sistema_EmpresasMongoMap` |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:35:| `db.sucursales_catalogo` | `Sistema_Sucursales` |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:36:| `db.sucursal_servidor_map` | `Sistema_SucursalServidorMapeo` |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:37:| `db.servers` | `Servidores_Conexiones` |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:38:| `db.server_sucursales_config` | `Sistema_ServidorSucursalesConfig` (no usado directamente) |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:47:| `Sistema_EmpresasMongoMap` | Mapeo UUID MongoDB → ID SQL | EmpresaID_SQL, EmpresaMongoUUID |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:48:| `Sistema_Sucursales` | Catálogo sucursales | SucursalID, NombreSucursal, EmpresaID, MongoUUID |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:61:| `_get_empresas_by_uuids_sql()` | Empresas por UUIDs MongoDB |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:67:| `_get_empresa_by_id_sql()` | Empresa por UUID MongoDB |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:75:**ANTES (MongoDB):**
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:78:    "id": "uuid-empresa-mongo",
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:92:    "id": "31784356-6d0b-47ce-8fe8-c8a442e45a07",  # UUID MongoDB (compatibilidad)
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:103:**Diferencia:** El campo `id` mantiene UUID MongoDB para compatibilidad con el frontend y JWT existente.
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:126:$ grep -R "db.empresas" /app/backend/core/context_resolver.py
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:129:$ grep -R "db.sucursales_catalogo" /app/backend/core/context_resolver.py
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:132:$ grep -R "db.sucursal_servidor_map" /app/backend/core/context_resolver.py
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:135:$ grep -R "db.server_sucursales_config" /app/backend/core/context_resolver.py
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:138:$ grep -R "db.servers" /app/backend/core/context_resolver.py
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:141:$ grep -R "AsyncIOMotorClient" /app/backend/core/context_resolver.py
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:144:$ grep -R "motor.motor_asyncio" /app/backend/core/context_resolver.py
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:148:**Total referencias MongoDB productivas: 0**
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:169:| Campo | Valor MongoDB | Valor SQL | Impacto |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:173:**Nota:** La columna `SucursalOrigenID` en `Sistema_SucursalServidorMapeo` está vacía porque no se migró desde MongoDB en FASE 3-B. Si se requiere este valor para queries MPRO, debe poblarse manualmente.
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:182:| Otros módulos pueden tener sus propias llamadas MongoDB | Validar en FASE 3-D y 3-E |
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:202:   - Identificar colecciones MongoDB usadas
/app/docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md:217:| 0 referencias MongoDB productivas | ✅ |
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:27:| 8 | ricardo@edarsa.com.mx | Sin empresas_permitidas en MongoDB |
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:28:| 9 | david.ricardez@cienfuegos.mx | Sin empresas_permitidas en MongoDB |
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:29:| 11 | carlos@alpuntoycoma.mx | Sin empresas_permitidas en MongoDB |
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:30:| 12 | eduardo@alpuntoycoma.mx | Sin empresas_permitidas en MongoDB |
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:40:| Sin empresas_permitidas en MongoDB | 4 | No se asignaron empresas según directiva |
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:69:| Usuario | Empresa Principal | UUID MongoDB |
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:115:## 7. VALIDACIÓN CONTRA SISTEMA_EMPRESASMONGOMAP
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:117:| UUID MongoDB | EmpresaID SQL | Código | Asignaciones |
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:125:**Empresas no mapeadas:** 0 (todas resueltas vía Sistema_EmpresasMongoMap)
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:162:✓ MongoDB sigue siendo fuente de login
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:179:- [x] MongoDB sigue siendo fuente de autenticación
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:205:| Sistema_EmpresasMongoMap | 5 | ✓ Completo |
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:206:| Usuario_MigracionMongoTrace | 11 | ✓ Completo |
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:211:1. **Validación cruzada:** Comparar datos MongoDB vs SQL para cada usuario
/app/docs/reports/FASE2B3_POBLADO_USUARIO_EMPRESAS_ASIGNACION.md:236:| MongoDB sigue siendo fuente de login | ✓ |
/app/docs/reports/FIX_SYNC_MPRO_COMERCIAL_KPIS_DIARIOS_V2.md:202:| MongoDB | ✅ No se usa como fuente principal |
/app/docs/reports/FIX_SYNC_MPRO_COMERCIAL_KPIS_DIARIOS_V2.md:247:6. ✅ MongoDB no participa como fuente principal
/app/docs/reports/FASE_1C_3I_F_VISUALIZACION_EXPORTACION_PRICING_IA.md:84:| No usa MongoDB | ✅ OK |
/app/docs/reports/FASE_1C_3I_F_VISUALIZACION_EXPORTACION_PRICING_IA.md:89:## 8. Validación de No Uso de MongoDB
/app/docs/reports/FASE_1C_3I_F_VISUALIZACION_EXPORTACION_PRICING_IA.md:116:- ✅ Sin dependencias de MongoDB
/app/docs/reports/FASE_1C_3I_C_INTEGRACION_GPT52_PRICING_BENCHMARK.md:21:- **NO se usa MongoDB** (todo en EDARSAHUB SQL)
/app/docs/reports/FASE_1C_3I_C_INTEGRACION_GPT52_PRICING_BENCHMARK.md:213:| 8 | NO se usa MongoDB | ✅ |
/app/docs/reports/FASE_1C_3I_C_INTEGRACION_GPT52_PRICING_BENCHMARK.md:230:| 3 | NO se usa MongoDB | ✅ |
/app/docs/reports/FASE_1C_3I_C_INTEGRACION_GPT52_PRICING_BENCHMARK.md:253:### Siguiente Paso: Frontend de Motor de Precios IA
/app/docs/reports/FASE_1C_3I_C_INTEGRACION_GPT52_PRICING_BENCHMARK.md:287:**MongoDB**: NO usado  
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:47:get_current_user()      → usa _get_user_sql_only() (SQL-only, sin fallback MongoDB)
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:62:### Referencias a db.users:
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:73:### Referencias a AsyncIOMotorClient:
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:79:### Referencias a MONGODB_FALLBACK:
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:87:→ Sin referencias directas a db.users ✅
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:100:| Estado en MongoDB | **NO EXISTE** |
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:106:- ✅ Usuario NO fue creado en MongoDB (correcto)
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:115:## 5. Referencias MongoDB Residuales (Fuera del Alcance)
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:122:| `user_repository_sql.py:compare_user_mongo_vs_sql()` | Diagnóstico | Función pasiva | No migrar |
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:142:| 8 | MongoDB no se modifica | ✅ |
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:161:| password_reset.py falla si MongoDB cae | Baja | Medio | Migrar a SQL en fase futura |
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:162:| context_service.py falla si MongoDB cae | Baja | Bajo | Migrar a SQL en fase futura |
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:163:| Campos sec_* no disponibles si MongoDB cae | Baja | Muy bajo | Son metadatos piloto, no críticos |
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:174:| P2 | password_reset.py | Reset de passwords a SQL | Elimina dependencia MongoDB en flujo de recuperación |
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:175:| P3 | context_service.py | Contexto de UI a SQL | Elimina dependencia MongoDB en navegación |
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:177:| P5 | FASE 5/6 | Eliminación total MongoDB | Solo después de migrar todo |
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:188:| Auth/RBAC operativo independiente de MongoDB | ✅ |
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:190:| Referencias MongoDB residuales clasificadas | ✅ |
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:197:MongoDB ya NO participa en:
/app/docs/reports/RBAC_CLOSE_001_AUDITORIA_FINAL_AUTH_RBAC_SQL.md:206:MongoDB solo se usa para:
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:1:# FASE 2-E: Auth SQL-First con Fallback MongoDB
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:12:Cambiar `get_current_user()` para usar SQL Server (EDARSAHUB) como fuente primaria de autenticación, manteniendo MongoDB como fallback obligatorio.
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:27:| `get_current_user()` | Ahora usa SQL-first con fallback MongoDB |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:29:| `_get_user_sql_first_with_fallback()` | Nueva función que implementa el flujo SQL→MongoDB |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:42:| `true` | SQL primero → MongoDB fallback |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:43:| `false` | MongoDB directo (comportamiento legacy) |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:63:  SQL   MongoDB
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:79:    │ MongoDB Fallback│
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:87:    │ MONGODB_FALLBACK│
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:100:## 5. Flujo Fallback MongoDB
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:106:| Usuario no existe en SQL | `MONGODB_FALLBACK` |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:108:| Estructura SQL inválida | `MONGODB_FALLBACK` |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:112:- MongoDB siempre está disponible como respaldo
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:140:### Desde MongoDB (fallback):
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:154:**Nota:** MongoDB no tiene campo `_source`.
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:160:| Usuario | ID en SQL | ID en Mongo | Formato |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:166:**Diferencia:** SQL devuelve en MAYÚSCULAS, MongoDB en minúsculas. Ambos son UUIDs válidos.
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:172:| SUPERADMIN | Empresas Mongo | Empresas SQL | Regla Aplicada |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:197:| GET /api/auth/me (admin@inventario.com) | ✓ Sin `_source` (MongoDB) |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:198:| ID en respuesta | ✓ minúsculas (formato MongoDB) |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:205:| Usuario | En SQL | En Mongo | Resultado |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:207:| superadmin2@test.com | ❌ | ✓ | ✓ Resuelto desde MongoDB (sin `_source`) |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:209:**Comportamiento correcto:** Usuario que no está en SQL se resuelve desde MongoDB fallback.
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:230:[AUTH-FALLBACK] Usuario resuelto desde MongoDB: superadmin2@test.com, reason=MONGODB_FALLBACK
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:244:| SQL Server no disponible | Media | Fallback MongoDB automático |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:247:| Usuarios @test.com no migrados | Baja | Resuelven vía fallback MongoDB |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:257:| 3 | Medir % de requests SQL vs MongoDB | Pendiente |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:268:| SQL-first funciona con fallback MongoDB | ✅ |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:269:| MongoDB fallback sigue activo | ✅ |
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:286:### FASE 2-G: Eliminar Fallback MongoDB (Futuro)
/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md:305:*SQL Server es ahora la fuente primaria de autenticación con fallback MongoDB activo.*
/app/docs/reports/historical_load_destination_audit.json:11:    "mongo_inserted": 14,
/app/docs/reports/historical_load_destination_audit.json:12:    "mongo_collection": "kpis_comercial",
/app/docs/reports/historical_load_destination_audit.json:13:    "mongo_database": "edarsa_hub",
/app/docs/reports/historical_load_destination_audit.json:23:    "kpis_comercial_mongo": {
/app/docs/reports/historical_load_destination_audit.json:30:      "problem": "MongoDB NO debe ser destino final de históricos"
/app/docs/reports/historical_load_destination_audit.json:43:    "kpis_comercial_collection": "CACHE_LEGACY_NO_FINAL",
/app/docs/reports/historical_load_destination_audit.json:44:    "checkpoints": "MONGODB_PERMITIDO",
/app/docs/reports/historical_load_destination_audit.json:45:    "logs": "MONGODB_PERMITIDO"
/app/docs/reports/historical_load_destination_audit.json:64:      "description": "Marcar 14 registros MongoDB como staging de prueba",
/app/docs/reports/historical_load_destination_audit.json:70:      "description": "Evaluar migración de kpis_comercial MongoDB a SQL",
/app/docs/reports/historical_load_destination_audit.json:82:    "5. Clasificar kpis_comercial MongoDB como cache/staging",
/app/docs/reports/FASE_API_LOCAL_QUERY_EDITOR_REPORTE.md:555:- ✅ No se tocó MongoDB
/app/docs/reports/FASE_1C_SANITIZACION_SQL_LIKE_REPORTE.md:167:| MongoDB | ✅ Sin cambios |
/app/docs/reports/FASE_1C_SANITIZACION_SQL_LIKE_REPORTE.md:218:- ✅ Sin cambios en frontend, MongoDB, RBAC ni fecha operativa
/app/docs/reports/FASE_1C_3B_COSTOS_MARGENES_SYNC_RECETAS_IMPLEMENTACION.md:162:| No dependencia MongoDB | ✅ |
/app/docs/reports/FASE_1C_3B_COSTOS_MARGENES_SYNC_RECETAS_IMPLEMENTACION.md:375:| Sin MongoDB | ✅ |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:21:| Referencias MongoDB | 918 | 🟡 MEDIO |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:22:| Colecciones MongoDB específicas | 235 | 🟡 MEDIO |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:45:│   │   ├── db.py               1,478 líneas
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:90:| 6 | 🔴 ALTO | 918 referencias a MongoDB dispersas | Migración incompleta |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:118:| H007 | 🟡 MEDIO | Backend | Múltiples | 918 refs MongoDB | Migración parcial | Auditar y deprecar | Sí | 4 |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:127:| H016 | 🟢 BAJO | Core | db.py | 1,478 líneas | Complejidad | Mantener como está | No | - |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:135:## 5. MATRIZ MONGODB
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:141:| `db.servers` | 235 | FALLBACK_LEGACY_AUTORIZADO | 0 documentos, SQL-First |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:142:| `db.users` | 45 | FUNCIONAL_CRITICO_A_MIGRAR | Auth principal |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:143:| `db.consultas_custom` | 15 | CODIGO_MUERTO_ELIMINABLE | 0 documentos |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:144:| `db.sucursales` | 8 | FALLBACK_LEGACY_AUTORIZADO | SQL-First |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:145:| `db.query_templates` | 12 | CACHE_TEMPORAL_DOCUMENTAR | Histórico |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:146:| `db.alerts` | 6 | CACHE_TEMPORAL_DOCUMENTAR | Notificaciones |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:147:| `db.kpis_comerciales` | 25 | FALLBACK_LEGACY_AUTORIZADO | SQL-First |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:148:| `db.audit_logs` | 18 | CACHE_TEMPORAL_DOCUMENTAR | Bitácora |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:150:### Archivos con Mayor Dependencia MongoDB
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:163:# 8 módulos requieren inicialización MongoDB:
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:360:| /app/backups/20260508_1934_auth_rbac_mongodb/ | Auth migration | 2026-05-08 | Conservar |
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:402:### FASE 4: MongoDB Cleanup (BAJA)
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:404:- Marcar como MONGODB_LEGACY
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:430:5. 🟢 **FASE 4** - MongoDB cleanup (Deuda técnica)
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:482:/app/backend/core/db.py                          # Conexiones estables
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:522:/app/backups/20260508_1934_auth_rbac_mongodb/           # Migración auth
/app/docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md:535:- ✅ MongoDB desacoplado para servidores (0 documentos)
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:11:### Dependencias MongoDB:
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:13:from pymongo import ASCENDING, DESCENDING
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:16:### Métodos con código MongoDB:
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:17:| Método | Código MongoDB | Líneas |
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:19:| `get_by_workflow()` | `self.collection.find().sort()` | 29-33 |
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:20:| `get_by_usuario()` | `self.collection.find().sort()` | 55-56 |
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:21:| `get_pendientes_globales()` | `self.collection.find().sort().limit()` | 65-68 |
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:22:| `get_sin_asignar()` | `self.collection.find($or, $exists).limit()` | 78-84 |
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:23:| `get_vencidas()` | `self.collection.find()` | 108-109 |
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:24:| `contar_por_estado()` | `self.collection.aggregate()` | 184 |
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:25:| `contar_por_usuario()` | `self.collection.aggregate()` | 202 |
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:28:- 7 referencias directas a `self.collection` (MongoDB)
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:29:- Uso de `pymongo.ASCENDING/DESCENDING`
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:40:# CERO pymongo
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:45:ASCENDING = 1    # Reemplaza pymongo.ASCENDING
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:46:DESCENDING = -1  # Reemplaza pymongo.DESCENDING
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:148:$ grep -c "self.collection" tarea_repository.py
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:151:$ grep -c "pymongo" tarea_repository.py
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:161:### Referencias MongoDB restantes (solo documentación):
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:162:- Línea 7: Comentario "CERO MongoDB productivo"
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:163:- Línea 20: Comentario "reemplazan pymongo.ASCENDING/DESCENDING"
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:186:| CERO `self.collection` | ✅ Confirmado |
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:187:| CERO MongoDB productivo | ✅ Confirmado |
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:212:- Probable uso de MongoDB para cálculos y estados
/app/docs/reports/FASE_B_P1_B_TAREA_REPOSITORY_SQL.md:230:4. **FASE B-P2**: Migrar services con acceso directo a MongoDB
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:1:# FASE 2-F.1: Cierre de Pendientes Auth/RBAC Pre-Fallback MongoDB Off
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:6:**Objetivo:** Resolver formalmente usuarios pendientes antes de eliminar fallback MongoDB
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:17:**Hallazgo principal:** Solo los 5 usuarios @test.com dependen de MongoDB fallback. Los 3 usuarios productivos sin empresas ya resuelven desde SQL pero tienen acceso funcional limitado.
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:25:| Email | MongoDB | SQL | Activo | Rol | Empresas | auth_source | Clasificación |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:27:| superadmin@test.com | ✓ | ✗ | ✓ | SuperAdministrador | 0 | MongoDB | TEST |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:28:| superadmin2@test.com | ✓ | ✗ | ✓ | SuperAdministrador | 0 | MongoDB | TEST |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:29:| usuario_test_portal@test.com | ✓ | ✗ | ✓ | Usuario | 0 | MongoDB | TEST |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:34:- `superadmin@test.com` no tiene UUID en MongoDB (campo `id` vacío)
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:40:| Email | MongoDB | SQL | Activo | Rol | Empresas | auth_source | Clasificación |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:48:- Los 3 tienen 0 empresas tanto en MongoDB como en SQL (consistente)
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:59:| En MongoDB | ✓ SÍ |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:62:| Rol MongoDB | SuperAdministrador |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:65:| auth_source | MongoDB (fallback) |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:69:**Recomendación:** DESACTIVAR en MongoDB  
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:77:| En MongoDB | ✓ SÍ |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:80:| Rol MongoDB | SuperAdministrador |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:83:| auth_source | MongoDB (fallback) |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:86:**Recomendación:** DESACTIVAR en MongoDB  
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:94:| En MongoDB | ✓ SÍ |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:97:| Rol MongoDB | Usuario |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:100:| auth_source | MongoDB (fallback) |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:111:| En MongoDB | ✓ SÍ |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:125:| En MongoDB | ✓ SÍ |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:129:| Empresas MongoDB | 0 |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:145:| En MongoDB | ✓ SÍ |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:149:| Empresas MongoDB | 0 |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:165:| En MongoDB | ✓ SÍ |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:169:| Empresas MongoDB | 0 |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:197:## 5. Dependencia de MongoDB Fallback
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:199:### Usuarios que dependen de MongoDB fallback:
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:221:## 6. Impacto de Eliminar Fallback MongoDB Hoy
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:223:### Si se elimina fallback MongoDB:
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:241:| superadmin@test.com | DESACTIVAR en MongoDB | Alta |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:242:| superadmin2@test.com | DESACTIVAR en MongoDB | Alta |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:285:Mantener fallback MongoDB activo hasta:
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:295:| Desactivar superadmin@test.com en MongoDB | SÍ |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:296:| Desactivar superadmin2@test.com en MongoDB | SÍ |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:297:| Desactivar usuario_test_portal@test.com en MongoDB | SÍ |
/app/docs/reports/FASE2F1_CIERRE_PENDIENTES_AUTH_RBAC_PRE_FALLBACK_OFF.md:310:| Se sabe exactamente quién depende de MongoDB fallback | ✅ (3 @test.com activos) |
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:18:| **MongoDB legacy** (parcial) | Configuración histórica | Medio |
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:24:- MongoDB tiene configuración histórica pero no passwords válidos
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:79:│  PATRÓN C: MONGODB LEGACY (⚠️ DEPRECADO)                                     │
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:143:## 5. MÓDULOS QUE USAN MONGODB LEGACY
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:151:**Nota**: MongoDB NO contiene passwords válidos. El campo `password` no existe en los documentos.
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:163:La lógica de `core/db.py` (líneas 460-510):
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:174:| core/db.py | ✅ Implementado | ✅ Sí |
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:266:- Eliminar código legacy de MongoDB fallback
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:267:- Unificar toda la lógica de conexión en `core/db.py` + `server_registry.py`
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:308:1. **¿Cuántas lógicas de conexión existen?** 3 (EDARSAHUB, Hardcoded, MongoDB legacy)
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:311:4. **¿Qué módulos usan MongoDB legacy?** `comercial/repository.py` (solo fallback)
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:313:6. **¿Qué módulos usan pytds?** Todos (preferido en core/db.py)
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:314:7. **¿Qué módulos usan pymssql?** Todos (fallback en core/db.py)
/app/docs/reports/auditoria_homologacion_conexiones_sqlserver.md:316:9. **¿Qué módulos manejan instancia nombrada?** Todos los que usan core/db.py
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:68:## 3. Flujo Anterior (MongoDB)
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:72:  └─> db.users.find_one({"email": email})        [MongoDB]
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:74:          └─> db.password_reset_tokens.insert_one({  [MongoDB]
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:82:  └─> db.password_reset_tokens.find_one({"token": token})  [MongoDB]
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:83:      └─> db.users.update_one({"_id": user_id}, {          [MongoDB]
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:86:          └─> db.password_reset_tokens.delete_one()        [MongoDB]
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:90:- Token plano guardado en MongoDB
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:91:- Dependencia de `db.users` para lookup
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:92:- Dependencia de `db.password_reset_tokens` para tokens
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:129:## 5. Referencias MongoDB Eliminadas de password_reset.py
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:133:| `db.users.find_one()` | Buscar usuario | ✅ ELIMINADA → `Usuario_Catalogo` |
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:134:| `db.users.update_one()` | Actualizar password | ✅ ELIMINADA → `Usuario_Catalogo` |
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:135:| `db.password_reset_tokens.find_one()` | Buscar token | ✅ ELIMINADA → `Usuario_TokensRecuperacion` |
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:136:| `db.password_reset_tokens.insert_one()` | Guardar token | ✅ ELIMINADA → `Usuario_TokensRecuperacion` |
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:137:| `db.password_reset_tokens.delete_one()` | Eliminar token | ✅ ELIMINADA → UPDATE `Usado=1` |
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:155:## 7. Confirmación: MongoDB NO se Modifica en Flujo Crítico
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:159:| Buscar usuario | `db.users` | `Usuario_Catalogo` |
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:160:| Guardar token | `db.password_reset_tokens` | `Usuario_TokensRecuperacion` |
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:161:| Validar token | `db.password_reset_tokens` | `Usuario_TokensRecuperacion` |
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:162:| Actualizar password | `db.users.hashed_password` | `Usuario_Catalogo.PasswordHashTexto` |
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:164:**MongoDB NO se modifica para usuarios, passwords ni tokens. ✅**
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:170:| Colección MongoDB | Función | Estado | Plan |
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:190:3. Eliminar dependencia de colecciones MongoDB `rate_limit_password_reset` y `audit_password_reset`
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:227:$ grep -n "db.users" /app/backend/modules/auth/password_reset.py
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:230:$ grep -n "db.password_reset_tokens" /app/backend/modules/auth/password_reset.py
/app/docs/reports/FASE3I_PASSWORD_RESET_SQL.md:248:| `password_reset.py` no depende de MongoDB para usuarios/passwords/tokens | ✅ |
/app/docs/reports/DISENO_CONSOLA_GENERAL_SCHEDULER_SINCRONIZACIONES_EDARSAHUB.md:48:### NO usar MongoDB para configuración de jobs
/app/docs/reports/DISENO_CONSOLA_GENERAL_SCHEDULER_SINCRONIZACIONES_EDARSAHUB.md:49:MongoDB solo debe usarse para locks técnicos temporales, NO para configuración de negocio.
/app/docs/reports/DISENO_CONSOLA_GENERAL_SCHEDULER_SINCRONIZACIONES_EDARSAHUB.md:1047:**12. No usar MongoDB como fuente de verdad.**
/app/docs/reports/DISENO_CONSOLA_GENERAL_SCHEDULER_SINCRONIZACIONES_EDARSAHUB.md:1252:| 12. No MongoDB | ✅ Solo EDARSAHUB SQL |
/app/docs/reports/FASE_CATALOGO_EMPRESAS_SERVIDORES_SUCURSALES.md:50:| Sistema_EmpresasMongoMap | Mapeo MongoDB | 5 |
/app/docs/reports/historical_load_mpro_scaling_report.json:13:  "mongo_role": "checkpoint_log_cache_only",
/app/docs/reports/historical_load_mpro_scaling_report.json:34:    "mongo_final_inserted": 0,
/app/docs/reports/historical_load_mpro_scaling_report.json:50:    "mongo_not_final": "CONFIRMED",
/app/docs/reports/historical_load_mpro_scaling_report.json:54:  "mongodb_staging_records": {
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:1:# DIAGNÓSTICO: Dependencias MongoDB del Módulo Compras
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:13:El módulo de **Compras** tiene **dependencias residuales de MongoDB** que fueron parcheadas con un "modo stub" silencioso en lugar de ser migradas a EDARSAHUB SQL.
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:16:- ❌ `repository.py` tiene funciones que esperan MongoDB (`db.compras_params`)
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:17:- ❌ `pedidos_detector_job.py` usa colecciones MongoDB para tracking
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:22:El módulo Compras puede mostrar datos vacíos sin advertencia porque el stub ignora las operaciones de MongoDB en lugar de leer de SQL.
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:26:## 2. DEPENDENCIAS MONGODB ENCONTRADAS
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:30:| Línea | Código | Colección MongoDB | Descripción |
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:32:| 66 | `_db = None` | - | Variable global de conexión MongoDB |
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:33:| 67 | `_stub_mode = False` | - | Flag de modo stub (sin MongoDB) |
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:34:| 154 | `db.compras_params.find_one(...)` | `compras_params` | Lee parámetros de compras |
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:35:| 166 | `db.compras_params.update_one(...)` | `compras_params` | Guarda parámetros de compras |
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:43:| Línea | Código | Colección MongoDB | Descripción |
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:45:| 69 | `COLLECTION_PROCESADOS` | `pedidos_procesados_automatizacion` | Tracking de pedidos procesados |
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:46:| 70 | `COLLECTION_TAREAS` | `tareas_operativas_compras` | Tareas operativas creadas |
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:47:| 71 | `COLLECTION_BITACORA` | `auditoria_compras_bitacora` | Log de auditoría |
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:55:| Archivo | Dependencia MongoDB | Estado |
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:67:### 4.1 Funciones con dependencia directa de MongoDB
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:97:### 5.1 Endpoints que dependen de `compras_params` (MongoDB)
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:130:## 7. COLECCIONES MONGODB USADAS
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:169:### 9.1 Para reemplazar `compras_params` de MongoDB
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:196:### 9.2 Para tracking de pedidos (reemplazar MongoDB)
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:219:## 10. PLAN DE MIGRACIÓN MONGODB → SQL
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:236:### Fase 4: Eliminar código MongoDB (P2)
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:238:2. Remover imports de MongoDB
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:277:        logger.warning("[COMPRAS_REPO] MongoDB no disponible, operando en modo stub")
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:295:- **NO revertir** a código que explote sin MongoDB
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:298:- Modificar `repository.py` para llamar a SQL en lugar de MongoDB
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:309:| **4** | Eliminar código MongoDB de repository.py | P1 | repository.py |
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:341:grep -R "MongoDB" /app/backend/modules/compras --include="*.py"
/app/docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md:342:grep -R "AsyncIOMotorClient" /app/backend/modules/compras --include="*.py"
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:45:    MongoUUID VARCHAR(36) NULL,
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:46:    MongoEmpresaUUID VARCHAR(36) NULL,
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:64:    MongoSucursalUUID VARCHAR(36) NULL,
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:65:    MongoServidorUUID VARCHAR(36) NULL,
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:85:    MongoConfigID VARCHAR(36) NULL,
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:143:| Tabla SQL | Fuente MongoDB | Fuente SQL Auxiliar |
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:145:| `Sistema_Sucursales` | `db.sucursales_catalogo` | `Sistema_EmpresasMongoMap` (para EmpresaID) |
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:146:| `Sistema_SucursalServidorMapeo` | `db.sucursal_servidor_map` | - |
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:147:| `Sistema_ServidorSucursalesConfig` | `db.server_sucursales_config` | - |
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:157:| `MongoUUID` | UUID original de MongoDB |
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:158:| `MongoEmpresaUUID` | UUID de empresa en MongoDB |
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:159:| `MongoSucursalUUID` | UUID de sucursal en MongoDB |
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:160:| `MongoServidorUUID` | UUID de servidor en MongoDB |
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:161:| `FuenteMigracion` | Indica colección MongoDB origen |
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:203:| Sistema_EmpresasMongoMap conserva 5 mapeos | ✅ |
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:213:**FASE 3-C debe migrar el código de `context_resolver.py`** para que lea de las nuevas tablas SQL en lugar de MongoDB.
/app/docs/reports/FASE3B_DDL_MIGRACION_SUCURSALES_MAPEOS_SQL.md:227:- ✅ Trazabilidad MongoDB documentada
/app/docs/reports/FASE_1C_3B_R2_SYNC_RECETAS_CIENFUEGOS.md:26:El servidor CIENFUEGOS utiliza DDNS (Dynamic DNS), lo que significa que su IP puede cambiar. Se implementó resolución DNS dinámica en `/app/backend/core/db.py` para obtener siempre la IP actual.
/app/docs/reports/FASE_1C_3B_R2_SYNC_RECETAS_CIENFUEGOS.md:166:| Sin MongoDB | ✅ Confirmada |
/app/docs/reports/FASE_1C_3B_R2_SYNC_RECETAS_CIENFUEGOS.md:198:| `/app/backend/core/db.py` | Modificado (DNS dinámico) - sesión anterior |
/app/docs/reports/FASE_1C_3I_D_FRONTEND_PRICING_IA_BENCHMARK.md:1:# FASE 1C-3I-D: Frontend Motor de Precios Sugeridos IA y Benchmark
/app/docs/reports/FASE_1C_3I_D_FRONTEND_PRICING_IA_BENCHMARK.md:11:Se ha implementado exitosamente el frontend completo para el Motor de Precios Sugeridos IA y Benchmark, cumpliendo con todos los requisitos de la SUBFASE 1C-3I-D.
/app/docs/reports/FASE_1C_3I_D_FRONTEND_PRICING_IA_BENCHMARK.md:149:| No se usa MongoDB | OK |
/app/docs/reports/FASE_1C_3I_D_FRONTEND_PRICING_IA_BENCHMARK.md:157:## 9. Validacion de No Uso de MongoDB
/app/docs/reports/FASE_1C_3I_D_FRONTEND_PRICING_IA_BENCHMARK.md:163:- El footer del componente muestra: "Datos de EDARSAHUB SQL Server | CERO MongoDB"
/app/docs/reports/FASE_1C_3I_D_FRONTEND_PRICING_IA_BENCHMARK.md:164:- No existe ninguna importacion ni llamada a servicios MongoDB en el frontend
/app/docs/reports/FASE_1C_3I_D_FRONTEND_PRICING_IA_BENCHMARK.md:231:La SUBFASE 1C-3I-D se ha completado exitosamente, proporcionando una interfaz de usuario completa y funcional para el Motor de Precios Sugeridos IA. La implementacion cumple con todas las restricciones:
/app/docs/reports/FASE_1C_3I_D_FRONTEND_PRICING_IA_BENCHMARK.md:234:- CERO dependencias de MongoDB
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:28:- ❌ MongoDB (no tocado)
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:228:| FuenteOriginal | NVARCHAR(20) | 'MONGODB' | Fuente del dato |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:229:| IdOrigen | NVARCHAR(50) | NULL | ID en MongoDB |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:375:## 11. MAPEO FUTURO MONGODB → EDARSAHUB
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:377:### Collection Origen: tesoreria_cuadres_z
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:379:**Estructura estimada en MongoDB:**
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:420:| MongoDB | EDARSAHUB |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:449:| — | FuenteOriginal = 'MONGODB' |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:477:| MongoDB | ✅ NO TOCADO |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:494:| Tesorería frontend | ✅ INTACTO (sigue leyendo MongoDB) |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:499:| MongoDB | ✅ INTACTO |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:507:| Estructura de MongoDB diferente | Media | Medio | Validar estructura antes de migración |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:508:| Datos inconsistentes en MongoDB | Media | Medio | Limpieza durante migración |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:515:### Siguiente Paso: Migración de Cuadres MongoDB → EDARSAHUB
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:519:1. **Backup de collection** `tesoreria_cuadres_z` en MongoDB
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:522:   - Lee documentos de MongoDB
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:545:| **MongoDB modificado** | ❌ NO |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:557:# SUBFASE 4.2 — MIGRACIÓN CUADRES Z MONGODB → EDARSAHUB
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:568:**La colección `tesoreria_cuadres_z` en MongoDB está VACÍA (0 documentos).**
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:582:| MongoDB como legacy | N/A (vacío) |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:602:## 4. COLECCIONES MONGODB LEÍDAS
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:610:Se verificaron todas las colecciones de MongoDB (66 total) buscando:
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:622:## 5. CONFIRMACIÓN DE MONGODB NO MODIFICADO
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:632:**MongoDB permanece intacto.**
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:636:## 6. MAPEO MONGODB → EDARSAHUB
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:642:| Campo MongoDB | Campo EDARSAHUB |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:661:| Total documentos en MongoDB | 0 |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:704:| Unidad | Documentos MongoDB | Migrados |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:775:| Duplicados en MongoDB | 0 |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:821:| MongoDB | ✅ INTACTO |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:837:Dado que MongoDB está vacío para Cuadres Z, la arquitectura puede simplificarse:
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:842:| B | Mantener MongoDB como intermedio y sincronizar | ❌ NO NECESARIO |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:853:3. **Eliminar dependencia de MongoDB** para Cuadres Z (no hay datos que perder)
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:858:- Sin necesidad de sincronización MongoDB ↔ EDARSAHUB
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:869:| **Subfase** | 4.2 — Migración Cuadres Z MongoDB → EDARSAHUB |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:873:| **Documentos MongoDB** | 0 |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:875:| **MongoDB modificado** | ❌ NO |
/app/docs/reports/ejecucion_finanzas_fase4_tesoreria.md:884:**FIN SUBFASE 4.2 — MIGRACIÓN CUADRES Z MONGODB → EDARSAHUB**
/app/docs/reports/FASE_1C_3F_SIMULACION_PRECIOS_SOLICITUD_AUTORIZACION.md:189:| Sin MongoDB | ✅ |
/app/docs/reports/FASE_1C_3F_SIMULACION_PRECIOS_SOLICITUD_AUTORIZACION.md:213:| ❌ No usa MongoDB | ✅ Cumplido |
/app/docs/reports/COSTOS_ALERTAS_001C_SERVICIOS_REGLAS_MARGEN.md:222:| COSTOS-ALERTAS-001-E | Motor de evaluación masiva de margen | PENDIENTE |
/app/docs/reports/COSTOS_ALERTAS_001C_SERVICIOS_REGLAS_MARGEN.md:230:- ✅ CERO MongoDB
/app/docs/reports/FASE_1C_3C_COSTOS_MARGENES_ENDPOINTS_NO_LIVE.md:64:### 5.2 Sin MongoDB ✅
/app/docs/reports/FASE_1C_3C_COSTOS_MARGENES_ENDPOINTS_NO_LIVE.md:67:grep -r "mongodb\|MongoClient" /app/backend/modules/costos_margenes/
/app/docs/reports/FASE_1C_3C_COSTOS_MARGENES_ENDPOINTS_NO_LIVE.md:239:| Sin MongoDB | ✅ Confirmado |
/app/docs/reports/FASE_1C_3C_COSTOS_MARGENES_ENDPOINTS_NO_LIVE.md:299:4. Sin conexiones live, sin MongoDB
/app/docs/reports/correccion_comercial_ventas_dia_fuentes_por_unidad.md:44:MongoDB **NO** se usa para resolver:
/app/docs/reports/FASE_1C_3G_C_MODELO_CANONICO_IMPUESTOS_EDARSAHUB.md:272:| 15 | Sin MongoDB | ✅ |
/app/docs/reports/FASE_A_P1_DISENO_SYNC_ENDPOINTS_COMERCIAL_LEGACY.md:411:| ✅ CERO MongoDB | Confirmado |
/app/docs/reports/DIAGNOSTICO_QRO_VENTAS_DIA_SIN_CORTE_TABLERO_EJECUTIVO.md:112:- ✅ MongoDB no fue usado como fuente principal
/app/docs/reports/core_secrets_encryption_report.json:12:  "mongo_synced": 2,
/app/docs/reports/core_secrets_encryption_report.json:19:      "mongo": "OK",
/app/docs/reports/core_secrets_encryption_report.json:27:      "mongo": "OK",
/app/docs/reports/FIX_CATALOGO_CONSULTAS_SISTEMAS_DINAMICOS.md:125:## 11. CONFIRMACIÓN DE NO MONGODB
/app/docs/reports/FIX_CATALOGO_CONSULTAS_SISTEMAS_DINAMICOS.md:127:✅ **CONFIRMADO**: Esta corrección NO utiliza MongoDB.  
/app/docs/reports/FIX_CATALOGO_CONSULTAS_SISTEMAS_DINAMICOS.md:204:| 8 | No se usa MongoDB | ✅ |
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:1:# P1.4-F: MIGRACIÓN DB.SERVERS MÓDULO CONFIGURACIÓN — COMPLETADO
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:11:Se migraron exitosamente las 2 referencias a `db.servers` en el módulo `modules/configuracion/*`, eliminando la dependencia directa de MongoDB y usando `server_registry` (fuente: EDARSAHUB SQL).
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:19:| `config_asignaciones_repository.py` | 249 | `actualizar()` | `self.db.servers.find_one()` | `server_registry.get_server_by_id()` |
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:20:| `almacenes_sync_service.py` | 138 | `sincronizar_almacenes_desde_origen()` | `db.servers.find_one()` | `server_registry.get_server_connection_info_with_secrets()` |
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:32:server = await self.db.servers.find_one(
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:54:server = await db.servers.find_one({"id": server_id}, {"_id": 0})
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:72:modules/configuracion/repositories/config_asignaciones_repository.py:249:    server = await self.db.servers.find_one(
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:73:modules/configuracion/services/almacenes_sync_service.py:138:    server = await db.servers.find_one({"id": server_id}, {"_id": 0})
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:83:✅ **0 referencias activas a `db.servers` en modules/configuracion**
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:123:| MongoDB no usado como fuente | ✅ |
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:127:## 8. PROGRESO TOTAL MIGRACIÓN `db.servers`
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:143:- ✅ modules/configuracion/* tiene 0 referencias activas a db.servers
/app/docs/reports/P1.4-F_MIGRACION_DB_SERVERS_CONFIGURACION.md:154:**CIERRE:** P1.4-F completado sin regresiones. `modules/configuracion` ya no depende de `db.servers`.
/app/docs/reports/PORTAL_CLIENTES_AUTOFACTURACION_ARQUITECTURA.md:46:- **Fuente de verdad:** EDARSAHUB SQL (NO MongoDB, NO conexiones vivas)
/app/docs/reports/PORTAL_CLIENTES_AUTOFACTURACION_ARQUITECTURA.md:450:- Se pretende usar MongoDB como fuente de verdad
/app/docs/reports/BUG_COSTOS_001_R2_ESTADO_PRODUCTO_SUSPENDIDO_BAJA_NO_PRECIO_CERO.md:212:| 9 | CERO MongoDB | ✅ |
/app/docs/reports/BUG_COSTOS_001_R2_ESTADO_PRODUCTO_SUSPENDIDO_BAJA_NO_PRECIO_CERO.md:268:- ✅ **CERO MongoDB**
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:5:**Objetivo:** Migrar el repositorio base de fase2_operativo de MongoDB a SQL Server
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:13:- **Dependencias MongoDB:**
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:15:  - `self.collection = db[collection_name]`
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:16:  - `collection.find_one()`, `collection.insert_one()`, `collection.find_one_and_update()`
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:17:- **Comportamiento:** Todo acceso productivo a MongoDB
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:22:    def __init__(self, db, collection_name: str):
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:23:        self.collection = db[collection_name]  # MongoDB
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:43:    def __init__(self, collection_name: str):
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:44:        self.table_name = COLLECTION_TO_TABLE_MAP[collection_name]
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:48:    def __init__(self, db, collection_name: str):
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:49:        # db (MongoDB) IGNORADO
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:50:        self._sql_repo = SQLBaseRepository(collection_name)
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:61:- `SQLCursor`: Simulador de cursor MongoDB encadenable
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:63:- `COLLECTION_TO_TABLE_MAP`: Mapeo colección → tabla
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:64:- `FIELD_MAPPING`: Mapeo campos MongoDB → SQL por tabla
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:74:    COLLECTION_TO_TABLE_MAP,
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:85:- `COLLECTION_TO_TABLE_MAP`
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:92:| Método | MongoDB Original | SQL Nuevo | Estado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:94:| `create()` | `collection.insert_one()` | `INSERT INTO` | ✅ Migrado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:95:| `get_by_id()` | `collection.find_one(_id)` | `SELECT WHERE ID=` | ✅ Migrado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:96:| `get_all()` | `collection.find()` | `SELECT OFFSET FETCH` | ✅ Migrado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:97:| `update()` | `collection.find_one_and_update()` | `UPDATE SET` | ✅ Migrado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:98:| `delete()` | `collection.delete_one()` | `DELETE FROM` | ✅ Migrado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:99:| `count()` | `collection.count_documents()` | `SELECT COUNT(*)` | ✅ Migrado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:101:| `find()` | `collection.find()` | `SQLCursor` | ✅ Migrado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:102:| `find_one()` | `collection.find_one()` | `SELECT TOP 1` | ✅ Migrado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:103:| `aggregate()` | `collection.aggregate()` | `SELECT GROUP BY` | ✅ Migrado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:104:| `update_one()` | `collection.update_one()` | `UPDATE SET` | ✅ Migrado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:105:| `update_many()` | `collection.update_many()` | `UPDATE SET` | ✅ Migrado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:106:| `delete_one()` | `collection.delete_one()` | `DELETE TOP(1)` | ✅ Migrado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:121:| Colección MongoDB | Tabla SQL EDARSAHUB |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:146:### Imports MongoDB en base_repository.py:
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:148:$ grep -n "MongoDB\|ObjectId\|bson" base_repository.py
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:189:**Nota:** Tablas vacías (0 registros) porque aún no se migran datos de MongoDB.
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:197:| base_repository.py ya no depende de MongoDB productivo | ✅ Confirmado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:198:| Imports MongoDB eliminados del base_repository.py | ✅ Confirmado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:205:| CERO MongoDB productivo en BaseRepository | ✅ Confirmado |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:215:| Repositories individuales con lógica MongoDB específica | FASE B-P1 migrará uno a uno |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:216:| Servicios con acceso directo a db.collection | FASE B-P2 migrará services |
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:238:2. Revisar métodos específicos que usan `self.collection.aggregate()`
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:248:3. **FASE B-P2**: Migrar servicios que acceden directamente a MongoDB
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:249:4. **FASE B-P3**: Migrar rutas que acceden directamente a MongoDB
/app/docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md:250:5. **FASE B-P4**: Eliminar `db_utils.py` y scripts MongoDB
/app/docs/reports/COSTOS_ALERTAS_001_DIAGNOSTICO_PREVIO_IMPLEMENTACION.md:444:| CERO MongoDB | ✅ |
/app/docs/reports/FASE_1C_3I_E_DASHBOARD_METRICAS_IA_PRICING.md:177:| No se usa MongoDB | ✅ OK |
/app/docs/reports/FASE_1C_3I_E_DASHBOARD_METRICAS_IA_PRICING.md:195:## 9. Validación de No Uso de MongoDB
/app/docs/reports/FASE_1C_3I_E_DASHBOARD_METRICAS_IA_PRICING.md:256:La SUBFASE 1C-3I-E se ha completado exitosamente, proporcionando un dashboard ejecutivo completo para visualizar métricas de uso y calidad del Motor de Precios IA.
/app/docs/reports/FASE_1C_3I_E_DASHBOARD_METRICAS_IA_PRICING.md:260:- ✅ CERO MongoDB
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:16:- **Inconsistencia entre MongoDB y SQL** en nombres y códigos
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:32:- Nombres en MongoDB (`130 QRO`, `130° QUERETARO`)
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:86:| `130 QRO` | Con espacio | MongoDB empresas |
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:100:| `130 MID` | Con espacio | MongoDB empresas |
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:101:| `130° MERIDA` | Sin tilde | MongoDB servers |
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:112:| `CIENFUEGOS TABLAJERIA` | Relacionado | MongoDB servers |
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:120:| `LA ESTELAR` | Nombre completo | MongoDB servers |
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:193:## 6. Dependencias Encontradas en MongoDB
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:245:### 7.3 Tabla `Sistema_EmpresasMongoMap`
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:246:| CodigoEmpresa | NombreEmpresa | EmpresaMongoUUID |
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:341:    OrigenAlias NVARCHAR(100), -- MongoDB, Frontend, API_LOCAL
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:419:- [x] Escaneo de MongoDB
/app/docs/reports/DIAGNOSTICO_ALIASES_UNIDADES_NEGOCIO_EDARSAHUB.md:459:- [x] **No se eliminó MongoDB**
/app/docs/reports/FASE_1B_DASHBOARD_COMERCIAL_EDARSAHUB_SQL.md:101:    NO consulta: MongoDB
/app/docs/reports/FASE_1B_DASHBOARD_COMERCIAL_EDARSAHUB_SQL.md:128:## 5. CONFIRMACIÓN: NO USA MONGODB
/app/docs/reports/FASE_1B_DASHBOARD_COMERCIAL_EDARSAHUB_SQL.md:133:grep -ri "mongo" /app/backend/modules/comercial/
/app/docs/reports/FASE_1B_DASHBOARD_COMERCIAL_EDARSAHUB_SQL.md:136:**Resultados:** Solo comentarios indicando que NO se debe usar MongoDB:
/app/docs/reports/FASE_1B_DASHBOARD_COMERCIAL_EDARSAHUB_SQL.md:137:- "NO consulta: MongoDB"
/app/docs/reports/FASE_1B_DASHBOARD_COMERCIAL_EDARSAHUB_SQL.md:138:- "no se encuentra, retornar estructura vacía (no usar MongoDB)"
/app/docs/reports/FASE_1B_DASHBOARD_COMERCIAL_EDARSAHUB_SQL.md:140:✅ **CONFIRMADO: No hay dependencia funcional de MongoDB**
/app/docs/reports/FASE_1B_DASHBOARD_COMERCIAL_EDARSAHUB_SQL.md:273:| 8 | No usa MongoDB | ✅ PASS |
/app/docs/reports/FASE_1B_DASHBOARD_COMERCIAL_EDARSAHUB_SQL.md:337:2. ✅ **No usa MongoDB** como fuente de verdad
/app/docs/reports/server_secret_key_rotation_report.json:17:  "mongo_synced": 0,
/app/docs/reports/estabilizacion_compras_multi_unidad_multi_tab_report.md:39:**Archivo:** MongoDB `sucursal_servidor_map`
/app/docs/reports/estabilizacion_compras_multi_unidad_multi_tab_report.md:62:MongoDB solo actúa como caché del catálogo.
/app/docs/reports/estabilizacion_compras_multi_unidad_multi_tab_report.md:222:#### 3. Endpoint `/api/unidades-negocio` usaba MongoDB
/app/docs/reports/estabilizacion_compras_multi_unidad_multi_tab_report.md:224:**Síntoma:** Potencial inconsistencia de datos si MongoDB y EDARSAHUB SQL divergen
/app/docs/reports/estabilizacion_compras_multi_unidad_multi_tab_report.md:261:| 2026-04-29 | Corrección identificación 130 MID | MongoDB `sucursal_servidor_map` |
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:11:### Dependencias MongoDB:
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:13:# Comentario referenciando MongoDB ObjectId
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:14:# Use _id (MongoDB ObjectId) for update, not id (UUID)
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:17:### Métodos con código MongoDB:
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:18:| Método | Código MongoDB | Líneas |
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:20:| `get_by_workflow()` | `self.collection.find_one()` | 28 |
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:21:| `existe_calculo()` | `self.collection.count_documents()` | 41 |
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:22:| `actualizar_calculo()` | `self.collection.find_one_and_update()` | 76-80 |
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:23:| `obtener_metricas_globales()` | `self.collection.aggregate()` | 196 |
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:24:| `eliminar_por_workflow()` | `self.collection.delete_one()` | 220 |
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:27:- 5 referencias directas a `self.collection` (MongoDB)
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:30:- Comentario obsoleto referenciando MongoDB ObjectId
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:39:# CERO pymongo, CERO MongoDB directo
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:132:$ grep -c "self.collection" responsabilidad_repository.py
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:138:$ grep "MongoDB" responsabilidad_repository.py
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:139:7:- CERO MongoDB productivo  # Solo en comentario de documentación
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:142:### Referencias MongoDB eliminadas:
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:143:- Línea 75 original: `# Use _id (MongoDB ObjectId) for update` → Eliminado
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:144:- Línea 196 original: `list(self.collection.aggregate())` → Migrado a `_sql_repo.aggregate()`
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:166:| CERO `self.collection` | ✅ Confirmado |
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:167:| CERO MongoDB productivo | ✅ Confirmado |
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:212:3. **FASE B-P2**: Migrar services con acceso directo a MongoDB
/app/docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md:213:4. **FASE B-P3**: Migrar rutas con acceso directo a MongoDB
/app/docs/reports/DIAGNOSTICO_IMPUESTOS_COSTOS_MARGENES_EDARSAHUB.md:397:### I.2. Para Implementar Motor de Alertas de Margen
/app/docs/reports/FASE_1C_3D_COSTOS_MARGENES_FRONTEND.md:187:### 13.2 Sin MongoDB ✅
/app/docs/reports/FASE_1C_3D_COSTOS_MARGENES_FRONTEND.md:189:No hay referencias a MongoDB en el componente.
/app/docs/reports/FASE_1C_3D_COSTOS_MARGENES_FRONTEND.md:229:6. Sin MongoDB confirmado
/app/docs/reports/INCIDENTE_CACHE_PREVIEW_RESET_CORRECCION.md:99:- _server_status_cache (core/db.py)
/app/docs/reports/INCIDENTE_CACHE_PREVIEW_RESET_CORRECCION.md:117:| No MongoDB | ✅ Confirmado |
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:25:MongoDB.users.find() → permisos operativos (allowed_servers, allowed_sucursales, allowed_warehouses)
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:27:Merge: SQL base + MongoDB permisos
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:32:**Fuente de permisos operativos:** MongoDB ❌
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:47:MongoDB.users.find() → SOLO campos RBAC piloto (sec_*, telefono) - NO permisos operativos
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:49:Merge: SQL base + SQL permisos + MongoDB metadatos
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:131:## 6. Comparación SQL vs MongoDB por Usuario
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:133:| Email | SQL Srv | Mongo Srv | SQL Suc | Mongo Suc | SQL Alm | Mongo Alm | Match |
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:153:**Ninguna.** SQL y MongoDB tienen exactamente los mismos permisos operativos para todos los usuarios.
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:175:## 9. Confirmación: MongoDB NO Alimenta Permisos Productivos
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:179:| `allowed_servers` | MongoDB | **EDARSAHUB SQL** ✅ |
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:180:| `allowed_sucursales` | MongoDB | **EDARSAHUB SQL** ✅ |
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:181:| `allowed_warehouses` | MongoDB | **EDARSAHUB SQL** ✅ |
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:184:| `sec_permisos` (RBAC piloto) | MongoDB | MongoDB (metadatos) |
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:185:| `telefono` | MongoDB | MongoDB (metadatos) |
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:187:**MongoDB ahora solo se usa para:**
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:191:**MongoDB NO se usa para:**
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:213:| 12 | PUT /api/users/{id}/permissions = HTTP 200 | ✅ OK (MongoDB) |
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:222:| PUT permisos aún escribe en MongoDB | **Media** | RBAC-SCOPE-E migrará escritura a SQL |
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:223:| SQL y MongoDB pueden desincronizarse | **Media** | Validación post-RBAC-SCOPE-E |
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:234:2. En lugar de `repo.update_user()` (MongoDB), escribir en tablas SQL:
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:241:4. Preservar `LegacyMongoValue` en nuevas inserciones si aplica
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:242:5. NO modificar MongoDB durante la escritura
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:258:- ✅ Permisos coinciden con MongoDB (migración RBAC-SCOPE-C)
/app/docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md:260:- ✅ MongoDB NO alimenta permisos productivos
/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md:33:- **MongoDB almacena:** `a5e56ed0-89b2-4d50-92f4-568a2106ab50`
/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md:35:Las funciones `find_user_by_id()` y `update_user()` hacían búsquedas **case-sensitive** en MongoDB, resultando en:
/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md:102:## 8. Referencias MongoDB Encontradas (Deuda Técnica)
/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md:104:Las siguientes funciones aún usan MongoDB para escritura de permisos:
/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md:110:| `create_user()` | `repository.py` | ⚠️ Sigue MongoDB |
/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md:111:| `deactivate_user()` | `repository.py` | ⚠️ Sigue MongoDB |
/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md:172:- Enriquecimiento de permisos legacy (`allowed_servers`, `allowed_sucursales`, `allowed_warehouses`) desde MongoDB
/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md:185:| Permisos legacy | ⚠️ MongoDB (temporal) | `allowed_servers`, `allowed_sucursales`, `allowed_warehouses` |
/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md:199:| 6 | Permisos persistidos en MongoDB | ✅ OK |
/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md:221:# Verificación MongoDB
/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md:225:**Screenshot:** Las tarjetas de usuarios muestran correctamente "X servidor(es) asignado(s)" con los permisos cargados desde MongoDB enriqueciendo datos SQL.
/app/docs/reports/BUG_RBAC_PERM_001_DEPARTAMENTOS_GUARDAR_PERMISOS.md:238:5. ✅ Permisos legacy se leen/escriben en MongoDB (deuda técnica documentada)
/app/docs/reports/FASE_A_P0_COMERCIAL_ROUTES_LIVE_A_SQL.md:203:| ✅ No se usa MongoDB | Confirmado |
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:13:Migrar el módulo `user_access_context.py` para que el acceso efectivo del usuario se resuelva desde EDARSAHUB SQL en lugar de MongoDB.
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:21:| `_get_db()` | Conexión MongoDB | **ELIMINADA** - Reemplazada por `_get_sql_connection()` |
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:33:## 3. Colecciones MongoDB Eliminadas del Flujo
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:35:| Colección MongoDB | Tabla SQL Reemplazo |
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:37:| `db.empresas` | `Sistema_Empresas` + `Sistema_EmpresasMongoMap` |
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:38:| `db.sucursales_catalogo` | `Sistema_Sucursales` |
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:39:| `db.sucursal_servidor_map` | `Sistema_SucursalServidorMapeo` |
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:40:| `db.servers` | `Servidores_Conexiones` |
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:41:| `db.users` | `Usuario_Catalogo` |
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:42:| `db.sec_roles` | `Usuario_Roles` + `Usuario_RolesAsignacion` |
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:43:| `db.sec_permisos_catalogo` | (Permisos desde user dict) |
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:59:| `Sistema_EmpresasMongoMap` | Mapeo UUID → ID SQL | EmpresaMongoUUID, EmpresaID_SQL |
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:87:**ANTES (MongoDB):**
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:114:    "empresas_ids": ["uuid1", "uuid2"],  # UUIDs MongoDB (compatibilidad)
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:176:$ grep -R "db.empresas" /app/backend/core/user_access_context.py
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:179:$ grep -R "db.sucursales_catalogo" /app/backend/core/user_access_context.py
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:182:$ grep -R "db.sucursal_servidor_map" /app/backend/core/user_access_context.py
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:185:$ grep -R "db.server_sucursales_config" /app/backend/core/user_access_context.py
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:188:$ grep -R "db.servers" /app/backend/core/user_access_context.py
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:191:$ grep -R "db.users" /app/backend/core/user_access_context.py
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:194:$ grep -R "db.sec_roles" /app/backend/core/user_access_context.py
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:197:$ grep -R "db.sec_permisos_catalogo" /app/backend/core/user_access_context.py
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:203:$ grep -R "AsyncIOMotorClient" /app/backend/core/user_access_context.py
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:206:$ grep -R "motor.motor_asyncio" /app/backend/core/user_access_context.py
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:210:**Total referencias MongoDB productivas: 0**
/app/docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md:291:| 0 referencias MongoDB productivas | ✅ |
/app/docs/reports/FIX_CATALOGO_SQL_EXPLORADOR_BD_MATCHING_ENTERPRISE.md:215:| MongoDB no utilizado | ✅ Confirmado |
/app/docs/reports/FIX_CATALOGO_SQL_EXPLORADOR_BD_MATCHING_ENTERPRISE.md:238:| ¿Se usó MongoDB? | **NO** |
/app/docs/reports/FIX_CATALOGO_SQL_EXPLORADOR_BD_MATCHING_ENTERPRISE.md:329:- ✅ No se usó MongoDB
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE5_ENDPOINTS_REPORTE.md:29:- ✅ No MongoDB
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE5_ENDPOINTS_REPORTE.md:89:### Sin MongoDB
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE5_ENDPOINTS_REPORTE.md:90:El router y resolver **NO usan MongoDB** en ningún momento.
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE5_ENDPOINTS_REPORTE.md:188:## 9. CONFIRMACIÓN NO MONGODB
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE5_ENDPOINTS_REPORTE.md:191:- No importa `pymongo`
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE5_ENDPOINTS_REPORTE.md:192:- No importa `motor`
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE5_ENDPOINTS_REPORTE.md:193:- No usa colecciones de MongoDB
/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE5_ENDPOINTS_REPORTE.md:263:- ✅ No MongoDB
/app/docs/reports/servers_reconciliation_report.json:6:  "mongo_count": 11,
/app/docs/reports/servers_reconciliation_report.json:9:  "mongo_only": [],
/app/docs/reports/FASE_0_6_MIGRACION_LAYOUT_MENUS_SQL.md:188:| No dependencia MongoDB | PASS |
/app/docs/reports/FASE_3_REPOSITORY_CONSULTAS_SQL_SQLFIRST.md:258:| No se escribió en MongoDB | ✅ |
/app/docs/reports/RBAC_SCOPE_E_UPDATE_USER_PERMISSIONS_ESCRIBE_SQL.md:39:    Ya NO escribe en MongoDB. Los permisos operativos se guardan en:
/app/docs/reports/RBAC_SCOPE_E_UPDATE_USER_PERMISSIONS_ESCRIBE_SQL.md:63:2. Obtener usuario objetivo desde MongoDB (validación de existencia)
/app/docs/reports/RBAC_SCOPE_E_UPDATE_USER_PERMISSIONS_ESCRIBE_SQL.md:126:## 7. Evidencia de que MongoDB NO fue Modificado
/app/docs/reports/RBAC_SCOPE_E_UPDATE_USER_PERMISSIONS_ESCRIBE_SQL.md:128:Consulta directa a MongoDB tras operaciones de escritura:
/app/docs/reports/RBAC_SCOPE_E_UPDATE_USER_PERMISSIONS_ESCRIBE_SQL.md:131:MongoDB: carlosruz@edarsa.com.mx
/app/docs/reports/RBAC_SCOPE_E_UPDATE_USER_PERMISSIONS_ESCRIBE_SQL.md:137:Los valores en MongoDB son los **legacy migrados**, no reflejan las operaciones de RBAC-SCOPE-E.
/app/docs/reports/RBAC_SCOPE_E_UPDATE_USER_PERMISSIONS_ESCRIBE_SQL.md:183:| MongoDB contiene datos legacy que no se sincronizan | Aceptable: MongoDB será deprecado en fases posteriores |
/app/docs/reports/RBAC_SCOPE_E_UPDATE_USER_PERMISSIONS_ESCRIBE_SQL.md:184:| El código SQL está inline en service.py | Refactorizar en RBAC-SCOPE-G cuando se elimine MongoDB |
/app/docs/reports/RBAC_SCOPE_E_UPDATE_USER_PERMISSIONS_ESCRIBE_SQL.md:209:| MongoDB no recibe permisos operativos | ✅ Confirmado |
/app/docs/reports/COSTOS_ALERTAS_001B_DDL_ALERTAS_MARGEN_SNAPSHOTS.md:6:**Máximas:** EDARSAHUB SQL es el cerebro. CERO MongoDB.
/app/docs/reports/COSTOS_ALERTAS_001B_DDL_ALERTAS_MARGEN_SNAPSHOTS.md:320:| 8 | CERO MongoDB | ✅ |
/app/docs/reports/COSTOS_ALERTAS_001B_DDL_ALERTAS_MARGEN_SNAPSHOTS.md:337:- ✅ **CERO MongoDB:** Todo el DDL es SQL Server puro
/app/docs/reports/FASE_1C_3G_E_REGLAS_PRECIO_RANGO_VINOS.md:318:| 14 | Sin MongoDB | ✅ |
/app/docs/reports/historical_load_final_report.json:8:    "mongo_final_inserted": 0,
/app/docs/reports/historical_load_final_report.json:65:    "mongo_not_final": "CONFIRMED",
/app/docs/reports/historical_load_final_report.json:74:    "mongo_role": "checkpoint_log_cache_only"
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:37:- **MongoDB auditado** y plan de aislamiento definido
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:73:## 3. ESTADO DE MONGODB ACTUAL (Solo Auditoría)
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:84:### Diagnóstico MongoDB
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:94:1. **Subfase 3.2-3.3:** Sincronizar a EDARSAHUB en lugar de MongoDB
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:97:4. **Cache:** Se mantiene en MongoDB (no es fuente de verdad)
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:100:### Endpoints que Dependen de MongoDB
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:319:| Romper sincronización actual (MongoDB) | Baja | Bajo | No modificar flujo actual hasta Subfase 3.4 |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:371:4. **MongoDB auditado:** Plan de aislamiento definido
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:657:| MongoDB | ✅ INTACTO (no modificado) |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:981:| MongoDB | ✅ INTACTO (no modificado) |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:990:| **Subfase 3.4** | Endpoint lee de EDARSAHUB (no MongoDB) |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1072:## 4. LÓGICA ANTERIOR (MongoDB)
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1075:- MongoDB colección `propinas_control`
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1162:| No MongoDB | ✅ |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1175:| No MongoDB | ✅ |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1188:| No MongoDB | ✅ |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1201:| No MongoDB | ✅ |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1214:| No MongoDB | ✅ |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1251:| MongoDB NO es fuente principal | ✅ |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1286:| MongoDB | ✅ INTACTO | No modificado (solo lectura legacy) |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1330:| No usa MongoDB como fuente | ✅ Confirmado |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1354:- Modificar MongoDB para pruebas
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1389:1. **Identificación**: Usuario localizado en MongoDB colección `users`
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1415:| MongoDB financiero modificado | ❌ NO |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1479:| **No MongoDB financiero modificado** | ✅ |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1521:## 3. LÓGICA ANTERIOR (MongoDB)
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1524:- Endpoint: `/api/finanzas/propinas` (MongoDB `propinas_control`)
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1635:| No usa MongoDB como fuente | ✅ |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:1746:| MongoDB/RBAC modificado | ❌ NO |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2080:## 16. CONFIRMACIÓN NO MONGODB COMO FUENTE FINANCIERA
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2086:| MongoDB como fuente | ❌ NO |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2087:| MongoDB modificado | ❌ NO |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2212:| **DistributedLock** | ✅ Implementado (MongoDB técnico) |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2220:| **No MongoDB financiero** | ✅ |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2227:## 23. ESTADO SCHEDULER/LOCK Y DEPENDENCIA TÉCNICA MONGODB
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2239:### Qué parte usa MongoDB (Infraestructura técnica)
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2243:| DistributedLock | MongoDB.scheduler_locks | Coordinación de concurrencia |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2244:| JobLogger (auxiliar) | MongoDB.scheduler_job_logs | Logging técnico del scheduler |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2245:| LockManager | MongoDB | Gestión de locks distribuidos |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2247:### Confirmación: MongoDB NO es fuente financiera
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2251:| Propinas TPV se almacenan en MongoDB | ❌ NO |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2252:| Importes de propinas vienen de MongoDB | ❌ NO |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2253:| SyncLog financiero usa MongoDB | ❌ NO |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2254:| Decisiones financieras dependen de MongoDB | ❌ NO |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2255:| MongoDB solo para coordinación técnica | ✅ SÍ |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2257:**Conclusión:** MongoDB se usa **EXCLUSIVAMENTE** como infraestructura técnica para locks distribuidos del scheduler. No almacena ni decide datos financieros de Propinas TPV. EDARSAHUB es la única fuente de verdad financiera.
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2263:| MongoDB running | ✅ SÍ (pid 51, uptime 4+ horas) |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2273:| Lock | DistributedLock (MongoDB) | DistributedLock (MongoDB) |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2302:**✅ CONFIRMADO: SyncLog financiero registrado en EDARSAHUB, no en MongoDB.**
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2322:1. **Para ejecución automática en producción**: El scheduler manager iniciará con FastAPI y usará MongoDB para locks.
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2326:3. **MongoDB como lock técnico es aceptable**: Es consistente con los otros 8 jobs del sistema y no afecta la integridad financiera (EDARSAHUB sigue siendo la única fuente de verdad).
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2334:| Patrón de locks MongoDB | ✅ NO MODIFICADO |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2567:## 15. CONFIRMACIÓN NO MONGODB COMO FUENTE FINANCIERA
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2571:| Datos financieros en MongoDB | ❌ NO |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2574:| MongoDB solo para lock técnico | ✅ SÍ |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2622:| MongoDB financiero | ❌ NO USADO |
/app/docs/reports/ejecucion_finanzas_fase3_propinas_tpv.md:2689:| **No MongoDB financiero** | ✅ |
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:1:# FINANZAS-TESORERIA-MONGO-002: Migración Cuadres Z a SQL
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:3:**Fase:** FINANZAS-TESORERIA-MONGO-002  
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:11:### Dependencias MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:15:repo = await get_cuadres_repository()  # MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:19:- `tesoreria_cuadres_z` en MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:24:- Backend intentaba resolver a `sucursal_id` con lógica sobre MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:44:- Sin resolución compleja, sin MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:119:## 7. MIGRACIÓN DE DATOS MONGODB → SQL
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:125:db.tesoreria_cuadres_z.count_documents({})
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:129:La colección MongoDB estaba vacía. Todos los cuadres futuros se guardarán en `Finanzas_CuadresZ`.
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:135:### Confirmación: tesoreria.py NO usa MongoDB productivamente
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:138:# (ningún resultado - ya no importa el repositorio MongoDB)
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:158:## 9. CONFIRMACIÓN CERO MONGODB PRODUCTIVO
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:160:- [x] `tesoreria.py` ya NO importa `repository_cuadres_z.py` (MongoDB)
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:163:- [x] Filtro `server_id` se resuelve desde SQL, no MongoDB
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:164:- [x] No hay fallback a MongoDB para cuadres
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:166:**NOTA:** El archivo `repository_cuadres_z.py` (MongoDB) sigue existiendo pero NO se usa en endpoints productivos. Se mantiene como referencia legacy.
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:199:| Cuadres antiguos en MongoDB | N/A | Colección estaba vacía |
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:210:1. Eliminar `repository_cuadres_z.py` (MongoDB) si ya no se usa en ningún lugar
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:218:**FINANZAS-TESORERIA-MONGO-002 COMPLETADO**
/app/docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md:221:- `tesoreria.py` ya NO usa MongoDB productivamente para cuadres
/app/docs/reports/historical_load_24_months_execution_report.json:8:  "mongo_role": "checkpoint_log_only",
/app/docs/reports/historical_load_24_months_execution_report.json:20:  "mongo_final_inserted": 0,
/app/docs/reports/historical_load_24_months_execution_report.json:39:      "mongo_final_inserted": 0,
/app/docs/reports/INCIDENTE_FILTROS_UNIDAD_NEGOCIO_ROTOS_DIAGNOSTICO.md:48:### 2.3 Sistema_EmpresasMongoMap
/app/docs/reports/INCIDENTE_FILTROS_UNIDAD_NEGOCIO_ROTOS_DIAGNOSTICO.md:49:| EmpresaID_SQL | MongoUUID |
/app/docs/reports/INCIDENTE_FILTROS_UNIDAD_NEGOCIO_ROTOS_DIAGNOSTICO.md:128:2. Los datos provienen de EDARSAHUB SQL (no MongoDB)
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:972:El endpoint `/api/servers/{id}/ping` usa `core.db.parse_sql_server_host()` que **SÍ preserva la instancia**:
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:990:   - Usar `core.db.parse_sql_server_host()` en lugar de parseo manual
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1021:3. ✅ MONGODB NO ES FUENTE FINANCIERA — No se usó MongoDB
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1043:| Parseo | core.db.parse_sql_server_host() | Manual (incompleto) | core.db.parse_sql_server_host() |
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1051:1. **get_unidad_connection_info():** Ahora usa `core.db.parse_sql_server_host()` y retorna campo `instance`
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1162:3. ✅ MONGODB NO ES FUENTE FINANCIERA — No se usa MongoDB
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1208:    cortes = _cortes_caja_db.copy()  # Datos demo hardcodeados
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1265:| No usa MongoDB | ✅ CONFIRMADO |
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1299:3. ✅ MONGODB NO ES FUENTE FINANCIERA — N/A (frontend no consulta MongoDB directamente)
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1385:| No consulta MongoDB | ✅ CONFIRMADO |
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1413:3. ✅ MONGODB NO ES FUENTE FINANCIERA — Solo usado para locks (sistema existente)
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1575:| SyncLog a tabla EDARSAHUB | ⚠️ Usa MongoDB (sistema existente) |
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1750:| Sistema de locks | `get_lock_manager(db)` (MongoDB existente) |
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1790:## 15. CONFIRMACIÓN DE QUE NO USA MONGODB COMO FUENTE PRINCIPAL
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1795:| MongoDB usado para | Locks, logs de ejecución (sistema existente) |
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1796:| MongoDB como fuente de verdad financiera | ❌ NO |
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:1831:| Errores en logs del scheduler | ❌ NO (errores pre-existentes de RBAC/MongoDB no relacionados) |
/app/docs/reports/ejecucion_finanzas_fase2_control_ingresos.md:2273:| No usa MongoDB como fuente financiera | ✅ SÍ |
/app/docs/reports/historical_load_complete_report.json:52:    "mongo_final_inserted": 0
/app/docs/reports/historical_load_complete_report.json:63:    "mongo_not_final": "CONFIRMED",
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:13:| Componente | MongoDB | SQL Server | Gap |
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:15:| Usuarios | 17 registros (`db.users`) | 9 registros (`Usuario_Catalogo`) | 8 usuarios faltan en SQL |
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:20:| Trazabilidad Mongo→SQL | N/A | 9 (`Usuario_MigracionMongoTrace`) | Completar migración |
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:74:**Mapeo MongoDB → SQL:**
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:76:| Campo MongoDB | Campo SQL | Transformación |
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:114:**Roles faltantes (de MongoDB):**
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:161:### 2.5 Usuario_MigracionMongoTrace (✅ EXISTE)
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:165:CREATE TABLE dbo.Usuario_MigracionMongoTrace (
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:167:    MongoID VARCHAR(24) NOT NULL,         -- ObjectId MongoDB
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:170:    RolMongoDB VARCHAR(50) NOT NULL,
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:171:    ActivoMongoDB BIT NOT NULL,
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:187:-- Agregar campos para compatibilidad con MongoDB
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:190:-- Campo para UUID de MongoDB (trazabilidad)
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:192:ADD MongoLegacyID VARCHAR(50) NULL;
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:202:-- Índice único para búsqueda por MongoID
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:203:CREATE UNIQUE INDEX IX_Usuario_MongoLegacyID 
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:204:ON dbo.Usuario_Catalogo(MongoLegacyID) WHERE MongoLegacyID IS NOT NULL;
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:209:    @value = N'UUID público usado en JWT y APIs. Compatible con MongoDB user.id', 
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:224:-- Verificar y agregar roles que existen en MongoDB pero no en SQL
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:238:### 3.3 Tabla de mapeo Empresa MongoDB → SQL
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:245:CREATE TABLE dbo.Empresas_MigracionMongoMap (
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:247:    MongoEmpresaID VARCHAR(50) NOT NULL UNIQUE,   -- UUID de MongoDB
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:259:### 4.1 Fase 2-B: Poblar tablas SQL desde MongoDB
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:267:    Activo, FechaAlta, MongoLegacyID, PublicUUID
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:277:    u._id AS MongoLegacyID,
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:279:FROM MongoDB.db.users u
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:284:-- Paso 2: Actualizar MongoLegacyID y PublicUUID para usuarios existentes
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:286:    uc.MongoLegacyID = u._id,
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:289:INNER JOIN MongoDB.db.users u ON uc.Email = u.email
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:290:WHERE uc.MongoLegacyID IS NULL;
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:306:FROM MongoDB.db.users u
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:317:    CASE WHEN u.empresa_default_id = emp.MongoEmpresaID THEN 1 ELSE 0 END AS EsPrincipal,
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:320:FROM MongoDB.db.users u
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:323:INNER JOIN dbo.Empresas_MigracionMongoMap em ON em.MongoEmpresaID = emp.value
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:340:-- 1. Conteo usuarios MongoDB vs SQL
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:341:-- MongoDB: SELECT COUNT(*) FROM db.users
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:377:-- 8. Diferencias MongoDB vs SQL
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:380:    mt.RolMongoDB,
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:381:    mt.ActivoMongoDB,
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:384:FROM dbo.Usuario_MigracionMongoTrace mt
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:396:| **2-B** | Poblar tablas SQL desde MongoDB | BAJO |
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:399:| **2-E** | Modificar `get_current_user()` a SQL-first con Mongo fallback | MEDIO |
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:401:| **2-G** | Apagar fallback MongoDB | ALTO |
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:402:| **2-H** | Eliminar dependencias `db.users` | MEDIO |
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:409:async def get_user_by_email_sql_first(email: str, db_mongo=None) -> Optional[Dict]:
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:412:    Si falla o no existe, fallback a MongoDB.
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:419:    # 2. Fallback MongoDB (temporal)
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:420:    if db_mongo:
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:421:        logging.warning(f"[AUTH-FALLBACK] Usuario {email} no encontrado en SQL, usando MongoDB")
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:422:        user_mongo = await db_mongo.users.find_one({"email": email}, {"_id": 0})
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:423:        return user_mongo
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:432:| Campo MongoDB | Tabla SQL | Columna SQL | Transformación | Obligatorio |
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:434:| `_id` (ObjectId) | `Usuario_Catalogo` | `MongoLegacyID` | String | Sí (trazabilidad) |
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:457:| Fallback MongoDB falla | BAJA | BAJO | Período de observación antes de apagar |
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:472:- [ ] Conteo SQL = Conteo MongoDB activos
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:482:- [ ] Fallback MongoDB activo pero sin uso
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:498:-- 2. Revertir código a MongoDB-only
/app/docs/proposals/FASE2A_DDL_AUTH_RBAC_EDARSAHUB_SQL.md:513:| CREATE TABLE | 1 | Empresas_MigracionMongoMap |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:1:# RBAC-SCOPE-001: Migración de Permisos Legacy de MongoDB a EDARSAHUB SQL
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:12:Este documento propone la migración definitiva de los permisos operativos legacy (`allowed_servers`, `allowed_sucursales`, `allowed_warehouses`) desde MongoDB hacia EDARSAHUB SQL Server.
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:14:**Objetivo:** Eliminar toda dependencia funcional de MongoDB del módulo Usuarios/Roles/Auth/RBAC, consolidando EDARSAHUB SQL como la **única fuente de verdad** para permisos de usuario.
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:16:**Estado actual:** Hotfix funcional con lectura híbrida (datos base SQL + permisos MongoDB).
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:22:## 2. Causa Raíz de la Dependencia MongoDB
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:24:Después de la migración FASE 2 (Auth/RBAC SQL-first), los permisos granulares de acceso a recursos quedaron en MongoDB porque:
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:26:1. **Diseño original:** El sistema fue construido con MongoDB como almacén principal.
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:28:3. **Hotfix BUG-RBAC-PERM-001:** Se implementó enriquecimiento de datos SQL con permisos MongoDB para mantener funcionalidad.
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:32:- `get_all_users()` → SQL + MongoDB (híbrido) ⚠️
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:33:- `update_user(permissions)` → 100% MongoDB ❌
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:44:| `allowed_servers` | MongoDB | ⚠️ Hotfix |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:45:| `allowed_sucursales` | MongoDB | ⚠️ Hotfix |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:46:| `allowed_warehouses` | MongoDB | ⚠️ Hotfix |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:47:| Lectura de permisos | SQL + MongoDB | ⚠️ Híbrido |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:48:| Escritura de permisos | MongoDB | ❌ Inaceptable |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:52:## 4. Dependencias MongoDB que Quedaron
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:54:### 4.1 Campos Legacy en MongoDB (colección `users`)
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:62:### 4.2 Valores Reales por Usuario (MongoDB)
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:79:| `GET /api/users` | `routes.py:597` | Lectura | SQL + MongoDB | SQL |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:80:| `PUT /api/users/{id}/permissions` | `routes.py:615` | Escritura | MongoDB | SQL |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:114:// Estructura actual en MongoDB
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:126:// Estructura actual en MongoDB
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:138:// Estructura actual en MongoDB
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:196:## 10. Matriz Campo MongoDB → Tabla SQL
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:198:| Campo MongoDB | Archivo Uso | Endpoint | Tipo | Tabla SQL Destino | Columna SQL | Tipo SQL | Mapeo | Riesgo | Acción |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:230:-- MIGRACIÓN: Reemplaza MongoDB allowed_servers
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:240:        LegacyMongoValue    VARCHAR(100) NULL,      -- UUID original de MongoDB para trazabilidad
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:276:-- MIGRACIÓN: Reemplaza MongoDB allowed_sucursales
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:288:        LegacyMongoValue    VARCHAR(100) NULL,      -- Valor original de MongoDB
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:324:-- MIGRACIÓN: Reemplaza MongoDB allowed_warehouses
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:336:        LegacyMongoValue    VARCHAR(100) NULL,      -- Valor original de MongoDB
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:381:### 14.1 Servidores: MongoDB UUID → SQL ServidorID
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:384:-- Mapeo vía Servidores_Conexiones.uuid_mongo
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:385:SELECT id AS ServidorID, uuid_mongo AS MongoUUID, nombre
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:387:WHERE uuid_mongo IS NOT NULL;
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:391:| ServidorID | MongoUUID | Nombre |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:413:| Duplicados en MongoDB | **Baja** | Limpiar con script previo a migración |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:439:- Leer permisos de MongoDB
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:441:- Preservar `LegacyMongoValue` para trazabilidad
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:442:- Validar conteo: MongoDB vs SQL
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:448:- Eliminar lectura de MongoDB para permisos
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:456:- Eliminar escritura en MongoDB para permisos
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:469:- Eliminar código de lectura MongoDB en `get_all_users()`
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:470:- Eliminar código de escritura MongoDB en `update_user()`
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:487:- Restaurar lectura/escritura MongoDB
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:503:| 8 | `update_user()` no escribe en MongoDB | Log + inspección código |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:504:| 9 | `get_all_users()` no depende de MongoDB | Log + inspección código |
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:564:2. **MongoDB** quedará como:
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:570:   - Lectura de permisos desde MongoDB
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:571:   - Escritura de permisos hacia MongoDB
/app/docs/proposals/RBAC_SCOPE_001_MIGRACION_PERMISOS_LEGACY_SQL.md:572:   - Fallbacks hacia MongoDB para Auth/RBAC
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:13:## 1. MATRIZ DE CONCILIACIÓN EDARSAHUB vs MONGODB
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:20:| Total servidores en MongoDB | 13 |
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:22:| Campo falta en MongoDB | **2** (LA ESTELAR, 130° MÉRIDA) |
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:24:| Solo en MongoDB | 0 |
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:28:| Servidor | En EDARSA | En Mongo | vis_op EDARSA | vis_op Mongo | Diferencia | Acción |
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:56:> EDARSAHUB ya puede ser usado por Tesorería sin depender de MongoDB.
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:60:2. MongoDB tiene 13 registros, 2 de ellos sin el campo `visible_en_operaciones`
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:63:5. No hay servidores en MongoDB que no existan en EDARSAHUB
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:77:2. MongoDB (fallback si SQL devuelve vacío)
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:188:    FALLBACK: MongoDB (solo si EDARSAHUB falla)
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:208:## 6. PLAN DE FALLBACK LEGACY A MONGODB
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:210:**Solo si EDARSAHUB falla**, el fallback MongoDB debe:
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:215:4. Registrar warning: `"[TESORERIA][MONGODB_FALLBACK] Servidor {id} sin campo visible_en_operaciones"`
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:232:| 9 | No se modifica MongoDB | ✅ Confirmado |
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:279:> **"MongoDB se mantiene como registry legacy parcial para este módulo como fallback de emergencia únicamente. EDARSAHUB es la fuente maestra operativa. Esta corrección alinea el endpoint de Tesorería con la arquitectura definitiva del sistema sin requerir modificación de datos en ninguna base de datos."**
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:289:3. ✅ Priorizar EDARSAHUB como fuente con fallback controlado a MongoDB
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:295:- ❌ MongoDB (sin updates)
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:329:    FALLBACK: MongoDB (solo si EDARSAHUB falla, con warning)
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:384:| MongoDB no fue modificado | ✅ Campos sin cambios |
/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md:397:> "MongoDB se mantiene como registry legacy parcial para este módulo como fallback de emergencia únicamente. EDARSAHUB es la fuente maestra operativa. Esta corrección alinea el endpoint de Tesorería con la arquitectura definitiva del sistema sin requerir modificación de datos en ninguna base de datos."
/app/docs/proposals/PROP_SYNC_HISTORICOS_EDARSAHUB.md:366:- ❌ MongoDB
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:54:- ✅ `Sistema_EmpresasMongoMap` existe para transición
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:88:[Servidores_Conexiones] ←── FK ──→ [Sistema_EmpresasMongoMap]
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:228:    -- MONGO_ID: ID o nombre en MongoDB
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:232:    -- Ejemplos: MongoDB.empresas, Frontend, adapters.py, sync_job.py
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:391:                  ← FK ← [Sistema_EmpresasMongoMap]
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:395:                  ← FK ← [Sistema_EmpresasMongoMap] (mantener)
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:441:    (2, '130 QRO', 'NOMBRE_SISTEMA', 'MongoDB.empresas', 0, 'Nombre en MongoDB'),
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:471:    (5, '130 MID', 'NOMBRE_SISTEMA', 'MongoDB.empresas', 0, 'Nombre en MongoDB'),
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:474:    (5, '130° MERIDA', 'SUCURSAL_NOMBRE', 'MongoDB.servers', 0, 'Sin acento'),
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:518:    (4, 'LA ESTELAR', 'NOMBRE_SISTEMA', 'MongoDB.servers', 0, 'Nombre completo'),
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:1290:| 2 | 130 QRO | 130QRO | NOMBRE_SISTEMA | MongoDB |
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:1302:| 4 | LA ESTELAR | LAESTELAR | NOMBRE_SISTEMA | MongoDB |
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:1307:| 5 | 130 MID | 130MID | NOMBRE_SISTEMA | MongoDB |
/app/docs/proposals/PROPUESTA_TECNICA_ESTANDARIZACION_UNIDADES_NEGOCIO.md:1308:| 5 | 130° MERIDA | 130MERIDA | SUCURSAL_NOMBRE | MongoDB |
/app/docs/proposals/PROP-003-cierre.md:90:| MongoDB | ❌ NO MODIFICADO |
/app/docs/proposals/PROP_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:409:POST   /api/catalogo/consultas-custom               # Crea en SQL (no MongoDB)
/app/docs/proposals/PROP_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:451:| 7 | Deprecar fallback | Eliminar lecturas de MongoDB | 🟢 BAJO |
/app/docs/proposals/PROP_SERVIDORES_CONSULTAS_SQL_EDARSAHUB.md:476:And NO se guarda en MongoDB
/app/docs/proposals/PROP-002-correccion-merida-v2.md:8:| **Versión** | 2.0 (Actualizada con análisis de dependencia MongoDB) |
/app/docs/proposals/PROP-002-correccion-merida-v2.md:39:## 3. ANÁLISIS DE DEPENDENCIA MONGODB EN `get_user_unidades_negocio()`
/app/docs/proposals/PROP-002-correccion-merida-v2.md:45:**Función**: Obtiene las unidades de negocio disponibles para un usuario según RBAC. Traduce la estructura empresas→sucursales→servidores de MongoDB a un formato usable.
/app/docs/proposals/PROP-002-correccion-merida-v2.md:50:2. db.empresas.find({id: $in empresa_ids}) → Empresas del catálogo
/app/docs/proposals/PROP-002-correccion-merida-v2.md:51:3. db.sucursales_catalogo.find({empresa_id: $in empresa_ids}) → Sucursales
/app/docs/proposals/PROP-002-correccion-merida-v2.md:52:4. db.sucursal_servidor_map.find({sucursal_id: $in sucursal_ids}) → Mapeos
/app/docs/proposals/PROP-002-correccion-merida-v2.md:53:5. db.servers.find({id: $in server_ids}) → Info de servidores
/app/docs/proposals/PROP-002-correccion-merida-v2.md:57:### 3.2 ¿De qué colecciones de MongoDB lee?
/app/docs/proposals/PROP-002-correccion-merida-v2.md:95:| Empresa en MongoDB | Código | Nombre | Búsqueda en código |
/app/docs/proposals/PROP-002-correccion-merida-v2.md:101:- `MERIDA` en el nombre → MongoDB tiene `130 MID`
/app/docs/proposals/PROP-002-correccion-merida-v2.md:102:- `MER` en el código → MongoDB tiene `130MID` (contiene `MID`, no `MER`)
/app/docs/proposals/PROP-002-correccion-merida-v2.md:106:### 3.5 ¿Ese mapeo desde MongoDB aplica solo a Comercial V2 o también a otros módulos?
/app/docs/proposals/PROP-002-correccion-merida-v2.md:116:**Conclusión**: El mapeo problemático (`'MERIDA' in nombre`) es **exclusivo de Comercial V2**. Otros módulos usan la estructura directa de MongoDB sin traducción.
/app/docs/proposals/PROP-002-correccion-merida-v2.md:118:### 3.6 ¿Cuál debe ser la fuente oficial de unidades permitidas: MongoDB, EDARSAHUB o JWT?
/app/docs/proposals/PROP-002-correccion-merida-v2.md:130:│       │            MongoDB (catálogos)                              │
/app/docs/proposals/PROP-002-correccion-merida-v2.md:157:- **MongoDB**: Catálogos de configuración (empresas, sucursales, servidores)
/app/docs/proposals/PROP-002-correccion-merida-v2.md:160:**Fuente oficial de unidades V2**: Debería ser MongoDB → traducido a IDs de EDARSAHUB mediante mapeo correcto.
/app/docs/proposals/PROP-002-correccion-merida-v2.md:201:### 3.10 ¿Cuál es el plan para que Comercial V2 deje de depender de MongoDB como fuente final de mapeo?
/app/docs/proposals/PROP-002-correccion-merida-v2.md:203:**Estado actual**: Comercial V2 depende de MongoDB para resolver RBAC y luego traduce a IDs de EDARSAHUB mediante mapeo hardcodeado.
/app/docs/proposals/PROP-002-correccion-merida-v2.md:211:| 3 | Migrar RBAC de MongoDB a EDARSAHUB | Eliminar dependencia |
/app/docs/proposals/PROP-002-correccion-merida-v2.md:319:| MongoDB | No se modifica |
/app/docs/proposals/PROP-002-correccion-merida-v2.md:378:| MongoDB intacto | NO SE TOCA |
/app/docs/proposals/PROP-002-correccion-merida-v2.md:423:- Modificar datos en MongoDB
/app/docs/proposals/PROP-002-correccion-merida-v2.md:435:| **Bug #2** | Mapeo: código busca `'MER'`, MongoDB tiene `'MID'` |
/app/docs/proposals/PROP-002-correccion-merida-v2.md:449:*Versión: 2.0 (Actualizada con análisis de dependencia MongoDB)*
/app/docs/proposals/PROP-001-cierre.md:17:| MongoDB solo como ubicación transitoria | ✅ CUMPLIDO |
/app/docs/proposals/PROP-001-cierre.md:39:6. ✅ Token se genera y almacena en MongoDB
/app/docs/proposals/PROP-001-cierre.md:110:## 5. COLECCIONES MONGODB CREADAS
/app/docs/proposals/PROP-001-recuperar-contrasena.md:22:║  NO CONVIERTE a MongoDB en la fuente maestra definitiva de identidad.        ║
/app/docs/proposals/PROP-001-recuperar-contrasena.md:51:| 1 | EDARSA HUB es el cerebro | Los tokens de reset se almacenarán en MongoDB (fuente de usuarios). Futuro: migrar a EDARSAHUB SQL |
/app/docs/proposals/PROP-001-recuperar-contrasena.md:59:| 9 | Toda ejecución debe dejar evidencia | Auditoría en MongoDB + logs de backend |
/app/docs/proposals/PROP-001-recuperar-contrasena.md:75:│  Usuarios internos (MongoDB users)    │  Portal proveedores             │
/app/docs/proposals/PROP-001-recuperar-contrasena.md:86:| Usuarios | **SOLO usuarios internos** (colección `users` de MongoDB) | TEMPORAL |
/app/docs/proposals/PROP-001-recuperar-contrasena.md:131:| Usuarios internos | MongoDB `edarsa_hub.users` | **LEGACY/TRANSITORIO** |
/app/docs/proposals/PROP-001-recuperar-contrasena.md:133:| Password hash | MongoDB `users.password` | **LEGACY/TRANSITORIO** |
/app/docs/proposals/PROP-001-recuperar-contrasena.md:135:**Nota:** La ubicacion actual de usuarios en MongoDB es un estado **transitorio heredado**. La consolidacion de identidad en EDARSAHUB es una tarea pendiente separada de esta propuesta.
/app/docs/proposals/PROP-001-recuperar-contrasena.md:139:Esta propuesta opera sobre el estado actual transitorio (MongoDB users) SIN REDEFINIR la arquitectura oficial.
/app/docs/proposals/PROP-001-recuperar-contrasena.md:142:- MongoDB localhost:27017
/app/docs/proposals/PROP-001-recuperar-contrasena.md:144:- Collection: users
/app/docs/proposals/PROP-001-recuperar-contrasena.md:158:# El password se actualiza en MongoDB (ubicacion TRANSITORIA actual)
/app/docs/proposals/PROP-001-recuperar-contrasena.md:159:# Esta operacion es TEMPORAL mientras los usuarios vivan en MongoDB
/app/docs/proposals/PROP-001-recuperar-contrasena.md:160:db.users.update_one(
/app/docs/proposals/PROP-001-recuperar-contrasena.md:172:| **No redefine arquitectura** | Esta propuesta NO convierte a MongoDB en fuente maestra oficial |
/app/docs/proposals/PROP-001-recuperar-contrasena.md:192:| Colección MongoDB | `password_reset_tokens` |
/app/docs/proposals/PROP-001-recuperar-contrasena.md:221:| Índice TTL MongoDB | `expires_at` con `expireAfterSeconds: 0` |
/app/docs/proposals/PROP-001-recuperar-contrasena.md:222:| Limpieza automática | MongoDB elimina documentos expirados |
/app/docs/proposals/PROP-001-recuperar-contrasena.md:229:| Token expirado | MongoDB lo elimina automáticamente |
/app/docs/proposals/PROP-001-recuperar-contrasena.md:238:db.password_reset_tokens.update_many(
/app/docs/proposals/PROP-001-recuperar-contrasena.md:244:db.password_reset_tokens.update_many(
/app/docs/proposals/PROP-001-recuperar-contrasena.md:462:3. Buscar usuario en MongoDB
/app/docs/proposals/PROP-001-recuperar-contrasena.md:508:6. Actualizar en MongoDB `users.password`
/app/docs/proposals/PROP-001-recuperar-contrasena.md:518:### 9.1 MongoDB: password_reset_tokens
/app/docs/proposals/PROP-001-recuperar-contrasena.md:522:db.createCollection("password_reset_tokens")
/app/docs/proposals/PROP-001-recuperar-contrasena.md:525:db.password_reset_tokens.createIndex(
/app/docs/proposals/PROP-001-recuperar-contrasena.md:531:db.password_reset_tokens.createIndex(
/app/docs/proposals/PROP-001-recuperar-contrasena.md:537:db.password_reset_tokens.createIndex(
/app/docs/proposals/PROP-001-recuperar-contrasena.md:542:### 9.2 MongoDB: rate_limit_password_reset
/app/docs/proposals/PROP-001-recuperar-contrasena.md:545:db.createCollection("rate_limit_password_reset")
/app/docs/proposals/PROP-001-recuperar-contrasena.md:548:db.rate_limit_password_reset.createIndex(
/app/docs/proposals/PROP-001-recuperar-contrasena.md:554:db.rate_limit_password_reset.createIndex(
/app/docs/proposals/PROP-001-recuperar-contrasena.md:560:### 9.3 MongoDB: audit_password_reset
/app/docs/proposals/PROP-001-recuperar-contrasena.md:563:db.createCollection("audit_password_reset")
/app/docs/proposals/PROP-001-recuperar-contrasena.md:566:db.audit_password_reset.createIndex(
/app/docs/proposals/PROP-001-recuperar-contrasena.md:571:db.audit_password_reset.createIndex(
/app/docs/proposals/PROP-001-recuperar-contrasena.md:614:| MongoDB `users` estructura | Solo se actualiza campo `password` |
/app/docs/proposals/PROP-001-recuperar-contrasena.md:669:### 13.3 Limpiar MongoDB
/app/docs/proposals/PROP-001-recuperar-contrasena.md:673:db.password_reset_tokens.drop()
/app/docs/proposals/PROP-001-recuperar-contrasena.md:674:db.rate_limit_password_reset.drop()
/app/docs/proposals/PROP-001-recuperar-contrasena.md:675:db.audit_password_reset.drop()
/app/docs/proposals/PROP-001-recuperar-contrasena.md:765:| 1 | Crear colecciones MongoDB con indices | 10 min |
/app/docs/proposals/PROP-001-recuperar-contrasena.md:795:| MongoDB es fuente definitiva? | **NO** - es ubicacion transitoria/legacy |
/app/docs/proposals/PROP-002-cierre.md:102:- ✓ MongoDB (catálogos)
/app/docs/proposals/P1-FASE5-DASHBOARD-FINANZAS-TESORERIA-CONSOLIDADO.md:438:- MongoDB solo como fallback documentado
/app/docs/proposals/P1-FASE5-DASHBOARD-FINANZAS-TESORERIA-CONSOLIDADO.md:504:**EDARSAHUB** como fuente primaria. MongoDB solo fallback legacy documentado.
/app/docs/modules/TABLAJERIA_FASE0_DIAGNOSTICO.md:204:5. NO crear lógica en MongoDB
/app/docs/modules/TABLAJERIA_DDL_FASE1.sql:11:-- 4. Sin dependencia de MongoDB
/app/docs/modules/TABLAJERIA_SPEC.md:29:2. Nada crítico debe vivir en MongoDB
/app/docs/modules/TABLAJERIA_SPEC.md:30:3. MongoDB no debe ser fuente de verdad para plantillas, órdenes, recetas, costos, inventarios, autorizaciones, usuarios, roles, permisos, auditoría ni contabilidad
/app/docs/modules/TABLAJERIA_SPEC.md:280:El módulo de Tablajería debe permitir que **Cienfuegos, MPRO Origen, MPRO Querétaro, futuro 130 Mérida y La Estelar** operen bajo una misma arquitectura canónica en EDARSAHUB SQL, sin depender de MongoDB, sin romper módulos existentes y dejando preparado el camino para inventario, compras, costos, márgenes, auditoría, autorizaciones y contabilidad.
/app/docs/FASE8_EVIDENCIA.md:244:   - db.sec_roles.deleteOne({codigo: "VISOR_ADMIN"})
/app/docs/FASE8_EVIDENCIA.md:245:   - db.users.updateMany({}, {$pull: {sec_roles: "VISOR_ADMIN"}})
/app/docs/FASE8_EVIDENCIA.md:246:   - db.users.updateMany({}, {$pull: {sec_permisos: {$in: ["SISTEMA_USUARIOS_VER", "SISTEMA_ROLES_VER"]}}})
/app/docs/ENTREGA_FASE1A_PROPINAS_TPV.md:177:                   │ MongoDB          │
/app/docs/ENTREGA_FASE1A_PROPINAS_TPV.md:184:   │ Usuario  │───►│ GET /propinas    │───►│ MongoDB          │
/app/docs/ENTREGA_FASE1A_PROPINAS_TPV.md:218:  "mongodb_connected": true
/app/docs/ENTREGA_FASE1A_PROPINAS_TPV.md:309:| Índices MongoDB | ✅ PASS | 4 índices creados correctamente |
/app/docs/ENTREGA_FASE1A_PROPINAS_TPV.md:330:├── repository.py         # Queries SQL + MongoDB
/app/docs/FASE13_PROPUESTA.md:108:| MongoDB | +colección `sec_perfiles`, +campo `sec_perfil` en users |
/app/docs/FASE13_PROPUESTA.md:133:| MongoDB | +colección `sec_perfiles`, +campo `sec_perfil` en users |
/app/docs/FASE13_PROPUESTA.md:145:| MongoDB | +colección `sec_perfiles` |
/app/docs/FASE13_PROPUESTA.md:224:| MongoDB | +colección `sec_perfiles`, +campo `sec_perfil` en users | N/A |
/app/docs/FASE6_EVIDENCIA.md:145:Estado en MongoDB:
/app/docs/FASE6_EVIDENCIA.md:293:3. Opcional: db.sec_roles.deleteOne({codigo: "VISOR_SISTEMA"})
/app/docs/FASE6_EVIDENCIA.md:294:4. Opcional: db.users.updateMany({}, {$unset: {sec_roles: 1}})
/app/docs/CIERRE_FASE_4_SOURCE_RESOLVER.md:142:1. **Refactorizar `core/db.py`** para SourceQueryResult
/app/docs/ARQUITECTURA_SEGURIDAD_EDARSA_HUB.md:26:### 1.1 Colecciones de Seguridad en MongoDB
/app/docs/ARQUITECTURA_SEGURIDAD_EDARSA_HUB.md:205:│   └── Valida: permisos_catalogos collection
/app/docs/ARQUITECTURA_SEGURIDAD_EDARSA_HUB.md:577:  const users = await db.users.find({}).toArray();
/app/docs/ARQUITECTURA_SEGURIDAD_EDARSA_HUB.md:581:    await db.sec_usuarios.insertOne({
/app/docs/ARQUITECTURA_SEGURIDAD_EDARSA_HUB.md:599:    const role = await db.sec_roles.findOne({ codigo: newRoleCode });
/app/docs/ARQUITECTURA_SEGURIDAD_EDARSA_HUB.md:601:    await db.sec_usuarios_roles.insertOne({
/app/docs/ARQUITECTURA_SEGURIDAD_EDARSA_HUB.md:609:      await db.sec_usuarios_contexto_acceso.insertOne({
/app/docs/ARQUITECTURA_SEGURIDAD_EDARSA_HUB.md:639:Fase 3: Restaurar backup de MongoDB
/app/docs/ARQUITECTURA_SEGURIDAD_EDARSA_HUB.md:650:- [ ] Backup completo de MongoDB
/app/docs/NORMAS_TECNICAS.md:125:- Usar catálogos locales (MongoDB) como cache/espejo
/app/docs/NORMAS_TECNICAS.md:130:UI → API → MongoDB (lectura)
/app/docs/NORMAS_TECNICAS.md:131:Admin → API Sync → SQL Externo → MongoDB (escritura)
/app/docs/NORMAS_TECNICAS.md:136:## 3. MANEJO DE ObjectId EN MONGODB
/app/docs/NORMAS_TECNICAS.md:144:doc = await db.collection.find_one({"id": x})
/app/docs/NORMAS_TECNICAS.md:148:doc = await db.collection.find_one({"id": x}, {"_id": 0})
/app/docs/DISENO_TECNICO_MACROFASE2_v1_ARCHIVADO.md:403:    result = await db.kpis_comercial_diarios.update_one(
/app/docs/DISENO_TECNICO_MACROFASE2_v1_ARCHIVADO.md:513:    await db.kpis_comercial_historico.insert_one(historico_doc)
/app/docs/DISENO_TECNICO_MACROFASE2_v1_ARCHIVADO.md:543:    kpis = await db.kpis_comercial_diarios.find({
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_CONSOLIDACION_FINAL.md:795:- Colecciones en MongoDB (solo cache temporal nuevo)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:13:Se completaron los 5 cambios del Lote 3, migrando los bypasses de `db.servers.find_one()` hacia `server_registry.get_server_connection_info()`.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:17:| 1 | `get_inventarios_list()` | ~2603 | OK con observación | Brecha: usa MongoDB fallback |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:18:| 2 | `get_pendientes_descargar()` | ~2708 | OK con observación | Brecha: usa MongoDB fallback |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:19:| 3 | `get_report_filters()` | ~2961 | OK con observación | Brecha: usa MongoDB fallback |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:20:| 4 | `get_almacenes_softrestaurant()` | ~2541 | OK con observación | Brecha: usa MongoDB fallback |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:21:| 5 | `ejecutar_consulta_catalogo()` | ~5459 | OK con observación | Brecha: usa MongoDB fallback |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:25:**OBSERVACIÓN CRÍTICA:** Todos los endpoints usan `server_registry.py` correctamente (ya no hay bypass directo), pero el registry resuelve **TODOS** los servidores vía MongoDB fallback porque EDARSAHUB no tiene la configuración completa de estos servidores. Esto queda como **BRECHA DE CATÁLOGO MAESTRO** pendiente de sincronización.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:35:| `get_inventarios_list()` | Sí | `db.servers.find_one()` → `get_server_connection_info()` | OK con observación |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:36:| `get_pendientes_descargar()` | Sí | `db.servers.find_one()` → `get_server_connection_info()` | OK con observación |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:37:| `get_report_filters()` | Sí | `db.servers.find_one()` → `get_server_connection_info()` | OK con observación |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:38:| `get_almacenes_softrestaurant()` | Sí | `db.servers.find_one()` → `get_server_connection_info()` | OK con observación |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:39:| `ejecutar_consulta_catalogo()` | Sí | `db.servers.find_one()` → `get_server_connection_info()` | OK con observación |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:41:**Criterio:** Los 5 endpoints ya no hacen bypass directo a `db.servers.find_one()`. Usan `server_registry.get_server_connection_info()`. La migración técnica está completa. Se clasifica como "OK con observación" porque el registry resuelve vía MongoDB fallback.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:62:| Server ID | Existe en EDARSAHUB | Existe en MongoDB fallback | Fuente usada | Dictamen Arquitectura |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:64:| a5547321-1139-4d2b-9d53-182ca737b6b6 | No | Sí | MongoDB fallback | **BRECHA: usa MongoDB fallback** |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:65:| b5175237-5e57-41f3-ab6d-b5ae2f5e780b | No | Sí | MongoDB fallback | **BRECHA: usa MongoDB fallback** |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:69:WARNING:core.server_registry:[SERVER_REGISTRY][MONGODB_FALLBACK_USED] Servidor a5547321-1139-4d2b-9d53-182ca737b6b6 obtenido desde MongoDB legacy
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:70:WARNING:core.server_registry:[SERVER_REGISTRY][MONGODB_FALLBACK_USED] Servidor b5175237-5e57-41f3-ab6d-b5ae2f5e780b obtenido desde MongoDB legacy
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:77:| Endpoint/Función | Usa registry | Fuente usada por registry | Server ID | Existe en EDARSAHUB | Existe en MongoDB fallback | Conexión SQL externa | Dictamen migración | Dictamen arquitectura | Acción pendiente |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:79:| `get_inventarios_list()` | Sí | MongoDB fallback | a5547321-* | No | Sí | No verificable | OK con observación | Brecha: usa MongoDB fallback | Sincronizar servidor a EDARSAHUB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:80:| `get_inventarios_list()` | Sí | MongoDB fallback | b5175237-* | No | Sí | No verificable | OK con observación | Brecha: usa MongoDB fallback | Sincronizar servidor a EDARSAHUB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:81:| `get_pendientes_descargar()` | Sí | MongoDB fallback | a5547321-* | No | Sí | No verificable | OK con observación | Brecha: usa MongoDB fallback | Sincronizar servidor a EDARSAHUB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:82:| `get_pendientes_descargar()` | Sí | MongoDB fallback | b5175237-* | No | Sí | No verificable | OK con observación | Brecha: usa MongoDB fallback | Sincronizar servidor a EDARSAHUB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:83:| `get_report_filters()` | Sí | MongoDB fallback | a5547321-* | No | Sí | No verificable | OK con observación | Brecha: usa MongoDB fallback | Sincronizar servidor a EDARSAHUB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:84:| `get_report_filters()` | Sí | MongoDB fallback | b5175237-* | No | Sí | No verificable | OK con observación | Brecha: usa MongoDB fallback | Sincronizar servidor a EDARSAHUB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:85:| `get_almacenes_softrestaurant()` | Sí | MongoDB fallback | a5547321-* | No | Sí | No verificable | OK con observación | Brecha: usa MongoDB fallback | Sincronizar servidor a EDARSAHUB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:86:| `ejecutar_consulta_catalogo()` | Sí | MongoDB fallback | (variable) | No | Sí | No verificable | OK con observación | Brecha: usa MongoDB fallback | Sincronizar servidor a EDARSAHUB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:92:| Server ID | Endpoint/Función | Módulo | Existe en EDARSAHUB | Existe en MongoDB fallback | Campos faltantes en EDARSAHUB | Impacto sin fallback | Dictamen | Acción |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:105:| **¿Existe en MongoDB fallback?** | Sí |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:106:| **Campos en MongoDB** | id, name, host, port, database, username, password (encrypted), system_type, active |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:109:| **Impacto si se desactiva fallback MongoDB** | Servidor no resuelto → HTTP 404 en todos los endpoints |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:110:| **Acción recomendada** | Crear registro completo en EDARSAHUB.Servidores_Conexiones con los datos de MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:120:| **¿Existe en MongoDB fallback?** | Sí |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:121:| **Campos en MongoDB** | id, name, host, port, database, username, password (encrypted), system_type, active |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:124:| **Impacto si se desactiva fallback MongoDB** | Servidor no resuelto → HTTP 404 en todos los endpoints |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:125:| **Acción recomendada** | Crear registro completo en EDARSAHUB.Servidores_Conexiones con los datos de MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:156:| `/api/servers/{id}/sucursales` | 200 | MongoDB fallback | OK con observación (brecha catálogo) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:157:| `/api/servers/{id}/almacenes` | 200 | MongoDB fallback | OK con observación (brecha catálogo) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:158:| `/api/servers/{id}/tipos-movimiento` | 200 | MongoDB fallback | OK con observación (brecha catálogo) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:163:| `/api/servers/{id}/categorias` | 200 | MongoDB fallback | OK con observación (brecha catálogo) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:164:| `/api/servers/{id}/departamentos` | 200 | MongoDB fallback | OK con observación (brecha catálogo) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:165:| `/api/servers/{id}/ping` | 200 | MongoDB fallback | OK con observación (brecha catálogo) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:167:**Conclusión no regresión:** Los Lotes 1 y 2 no presentan regresión de código. Sin embargo, todos los servidores se resuelven vía MongoDB fallback, lo cual es una brecha de catálogo maestro preexistente.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:193:**El Lote 3 está migrado técnicamente.** Los 5 endpoints/funciones ya usan `server_registry.get_server_connection_info()` y ya no hacen bypass directo a `db.servers.find_one()`. Se clasifica como **"OK con observación"** porque el registry resuelve vía MongoDB fallback.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:199:**BRECHA DE CATÁLOGO MAESTRO.** Todos los servidores probados (a5547321-*, b5175237-*) NO existen en EDARSAHUB y se resuelven vía MongoDB fallback. El fallback funciona correctamente como tolerancia legacy temporal, pero **esto no es la arquitectura final correcta**. Debe sincronizarse la configuración de estos servidores a EDARSAHUB para que sea la fuente primaria.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:202:> "El Lote 3 puede considerarse migrado técnicamente porque los 5 puntos usan `server_registry.py` y ya no hacen bypass directo a MongoDB. Sin embargo, los casos que caen a MongoDB fallback quedan como **OK con observación** y se registran como **brecha de catálogo maestro** pendiente de sincronización a EDARSAHUB. Los errores de SQL externo se clasifican separadamente como **conectividad/credenciales/query** (no verificable), no como regresión del código."
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:218:Se recomienda esperar hasta regularizar las brechas de catálogo maestro antes de continuar con Lote 4, o bien continuar con la migración técnica documentando que todos los endpoints tendrán el mismo dictamen "OK con observación / Brecha: usa MongoDB fallback".
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:244:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:253:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:264:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:273:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:284:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:293:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:304:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:313:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:324:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:333:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:429:**Nota sobre ⚠️:** Los endpoints funcionan correctamente (no hay errores de código), pero las queries SQL externas no devuelven datos. Esto es un **problema de conectividad SQL preexistente**, no una regresión del código. El registry obtiene correctamente los servidores via MongoDB fallback.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:458:- El registry obtiene servidores correctamente via MongoDB fallback
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:479:| MongoDB no es fuente maestra en los 5 puntos | ✅ Confirmado |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:541:- 5 bypasses eliminados de `db.servers.find_one()`
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md:546:- MongoDB deja de ser fuente maestra en los 5 puntos corregidos
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:15:El módulo actual de Propinas TPV fue implementado usando **MongoDB como almacenamiento principal**. Esto viola los principios arquitectónicos de EDARSA HUB para módulos financieros:
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:19:| Persistencia principal | MongoDB | **SQL Server** |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:22:| Fuente de verdad | MongoDB | **SQL Server (cerebro)** |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:23:| MongoDB | Almacenamiento | **Solo cache** |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:28:2. **MongoDB** funcione exclusivamente como cache de lectura para acelerar consultas
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:51:### Datos que PUEDEN vivir en MongoDB (Cache/Temporales):
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:63:SI existe_discrepancia(MongoDB, SQL_Server):
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:66:        invalidar_cache(MongoDB)
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:383:# 3. USO DE MONGODB COMO CACHE
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:385:## 3.1 Qué SE QUEDA en MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:394:## 3.2 Qué NO SE QUEDA en MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:410:2. Verificar cache en MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:418:2. Invalidar cache relacionado en MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:431:│ Cliente │───►│ API Backend  │───►│   MongoDB    │───►│ SQL Server   │
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:450:│ Cliente │───►│ API Backend  │───►│ SQL Server   │───►│   MongoDB    │
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:510:│   SQL SERVER        │ │   SQL SERVER    │ │   MONGODB       │
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:543:   a. Detectar esquema (cache en Mongo por 24h)
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:548:   f. Invalidar cache Mongo relacionado
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:560:2. Backend verifica cache MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:571:    │    4. Guardar en cache MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:585:| Endpoint | Usa Mongo | Acción Requerida |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:595:| `GET /detectar-esquema-todos` | Sí (cache) | Mantener Mongo como cache |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:596:| `GET /preview` | Sí (temporal) | Mantener Mongo como temporal |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:606:    # 2. Escribir en MongoDB (SECUNDARIO - temporal)
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:608:        await mongo_repository.crear_propina(propina_data)
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:610:        logger.warning(f"Mongo secundario falló: {e}")
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:623:        logger.error(f"SQL falló, intentando Mongo: {e}")
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:624:        # Fallback a Mongo solo en emergencia
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:625:        return await mongo_repository.obtener_propinas(filtros)
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:628:### Fase 3: Deprecar Mongo como Storage
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:633:    cached = await mongo_cache.get(cache_key)
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:641:    await mongo_cache.set(cache_key, result, ttl=300)
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:646:## 5.3 Mapeo de Colecciones Mongo → Tablas SQL
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:648:| Colección Mongo (Actual) | Tabla SQL (Nueva) | Acción |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:671:| Operación | Antes (Mongo) | Después (SQL + Cache) | Delta |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:684:| MongoDB | ~100KB por día | ~10KB (solo cache) |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:693:| Inconsistencia SQL-Mongo | Media | Medio | Dual write, verificación periódica |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:718:1. Activar dual write (SQL + Mongo)
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:720:3. Lectura sigue siendo de Mongo
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:730:2. Mongo como fallback de emergencia
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:735:### FASE M4: Mongo como Cache Only
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:739:1. Remover escrituras a colecciones Mongo de datos
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:740:2. Mantener Mongo solo para cache
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:749:1. Eliminar código de escritura a Mongo
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:750:2. Eliminar colecciones de datos en Mongo
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:761:MONGO   ████████████████████████████████████████─ ─ ─ ─ ─ ─ ─ ─┤ (cache)
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:772:-- Script de migración de MongoDB a SQL Server
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:778:-- 2. Migrar datos desde archivo JSON exportado de MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:783:-- Comparar con: db.propinas_control.countDocuments()
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:789:-- Comparar con agregación de MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:802:| Cálculos son correctos | Tests de validación cruzada SQL vs Mongo |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:809:[ ] Backup completo de MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:822:[ ] Datos son consistentes SQL vs Mongo
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:834:2. Volver a Mongo-only
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:840:1. Cambiar lectura a Mongo
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:847:1. Reactivar escrituras a Mongo
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:862:| Cache MongoDB | ✅ Sí (solo para preview/dashboard) |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:876:| `GET /preview` | Temporal | Mongo (no persiste) |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:888:                                 └──INVALIDATE──► MongoDB Cache
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:891:   Frontend ──GET──► Backend ──CHECK──► MongoDB Cache
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:905:                                 └──INVALIDATE──► MongoDB Cache
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:919:| **Cache** | MongoDB | Acelerador de lectura |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:931:## 10.3 Rol Exacto de MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:934:MongoDB en este módulo:
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:940:MongoDB NO almacena:
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:955:                                    └──CACHE──► MongoDB ◄───────┘
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:965:| M2 | 2-3 días | Dual write SQL + Mongo |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:967:| M4 | 1 día | Mongo solo cache |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:968:| M5 | 1 día | Deprecar colecciones Mongo |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md:989:║  ✅ MongoDB = Solo cache de lectura                               ║
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:20:| **MongoDB** | Cache de lectura únicamente |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:24:| Módulo | Colección Mongo Actual | Acción |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:38:### Colección MongoDB: `tesoreria_cuadres_z`
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:74:| Datos financieros críticos en MongoDB | Sin garantías ACID |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:92:║  DEBE vivir en SQL Server, NUNCA en MongoDB.                      ║
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:540:# 3. INFORMACIÓN EN MONGODB (SOLO CACHE)
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:542:## 3.1 Qué SE QUEDA en MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:550:## 3.2 Qué NO SE QUEDA en MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:565:2. Verificar cache MongoDB (TTL: 5 min)
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:571:2. Invalidar cache relacionado en MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:725:4. Invalidar cache MongoDB:
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:768:| `repository_cuadres_z.py` | Migrar de MongoDB a SQL | Alto |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:786:| Operación | Antes (Mongo) | Después (SQL + Cache) | Delta |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:799:| MongoDB `tesoreria_cuadres_z` | ~200KB/día | ~20KB/día (solo cache) |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:840:├── Mantener escritura dual (SQL + Mongo)
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:846:├── Invalidación de cache MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:850:FASE U4: Deprecación MongoDB
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:851:├── Remover código de escritura a Mongo
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:901:| **Propinas TPV** | MongoDB | SQL Server + Cache Mongo |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:902:| **Cortes Z** | MongoDB | SQL Server + Cache Mongo |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:903:| **Conteo Efectivo** | Embebido en Mongo | Tabla SQL separada |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:904:| **Fichas Depósito** | Embebido en Mongo | Tabla SQL separada |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:925:| Degradación de rendimiento | Cache MongoDB + índices SQL optimizados |
/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md:940:║  ✅ Cache MongoDB unificado para ambos módulos                    ║
/app/docs/FASE_3C_SECRETOS_SERVIDORES.md:36:| MongoDB | servers | password | Conexión SQL Server | Texto plano | ALTO |
/app/docs/FASE_3C_SECRETOS_SERVIDORES.md:37:| MongoDB | servers | api_key | APIs REST | Vacío | BAJO |
/app/docs/FASE_3C_SECRETOS_SERVIDORES.md:212:| Password cifrado en MongoDB | ✅ `enc:v1:gAAAAAB...` |
/app/docs/FASE_3C_SECRETOS_SERVIDORES.md:247:| MongoDB sincronizado | ✅ Warnings documentados |
/app/docs/FASE_3C_SECRETOS_SERVIDORES.md:251:## 8. MONGODB LEGACY
/app/docs/FASE_3C_SECRETOS_SERVIDORES.md:255:- MongoDB recibe secretos cifrados desde sync SQL→MongoDB
/app/docs/FASE_3C_SECRETOS_SERVIDORES.md:261:⚠️ Si algún módulo accede directamente a MongoDB.password sin descifrar, la conexión fallará. Solución: migrar a usar `server_registry.get_server_connection_info()`.
/app/docs/FASE_3C_SECRETOS_SERVIDORES.md:282:2. **MongoDB espejo:** MongoDB ahora tiene passwords cifrados. Módulos que lean directamente de MongoDB sin descifrar fallarán.
/app/docs/FASE_4F_VALIDACION_POST_REFACTOR_CACHE.md:10:Validación integral de EDARSA HUB después de la FASE 4E (desacoplamiento de componentes frontend y gestión de cache MongoDB). El objetivo fue confirmar que no hay regresiones críticas en el sistema.
/app/docs/diagnosticos/FASE_1A_DIAGNOSTICO_COMERCIAL_VENTAS.md:160:### 1.6 Dependencias MongoDB
/app/docs/diagnosticos/FASE_1A_DIAGNOSTICO_COMERCIAL_VENTAS.md:166:# NO consulta servidores locales ni MongoDB para KPIs.
/app/docs/diagnosticos/FASE_1A_DIAGNOSTICO_COMERCIAL_VENTAS.md:167:# NO usar MongoDB como fuente funcional para unidades.
/app/docs/diagnosticos/FASE_1A_DIAGNOSTICO_COMERCIAL_VENTAS.md:338:| 13 | No dependencia MongoDB nueva | grep |
/app/docs/diagnosticos/FASE_1A_DIAGNOSTICO_COMERCIAL_VENTAS.md:348:- Se detecta dependencia MongoDB
/app/docs/diagnosticos/FASE_1A_DIAGNOSTICO_COMERCIAL_VENTAS.md:369:- Agregar dependencias MongoDB
/app/docs/FINANZAS_CXP_MPRO_CREDENTIALS_SECURITY_01_REPORT.md:25:| MongoDB usado para password | NO | NO (usa get_server_by_id con prefer_sql=True) | ✅ CUMPLE |
/app/docs/FINANZAS_CXP_MPRO_CREDENTIALS_SECURITY_01_REPORT.md:48:    allow_mongo_fallback=True, # Fallback solo si SQL falla
/app/docs/FIX_SERVIDORES_DUPLICADOS_20260419.md:1:# Corrección de Servidores Duplicados en MongoDB
/app/docs/FIX_SERVIDORES_DUPLICADOS_20260419.md:9:Se corrigió el problema de servidores duplicados en MongoDB que impedía el correcto funcionamiento del módulo Compras > Auditoría Operativa.
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:12:Se pobló exitosamente la tabla `Sistema_Empresas` en EDARSAHUB con las 5 empresas provenientes de MongoDB.
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:16:| Empresas en MongoDB | 5 |
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:21:**⚠️ Nota:** La tabla `Sistema_Empresas` NO tiene columna para almacenar el UUID de MongoDB. Se documenta la necesidad para fase futura, pero NO se ejecutó ALTER TABLE.
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:38:## 3. EMPRESAS ORIGEN EN MONGODB
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:53:| # | MongoDB_ID | Código | Nombre | Razón Social | Activa |
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:67:-- Para cada empresa de MongoDB:
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:79:- Se usó `NombreComercial` para almacenar `razon_social` de MongoDB
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:80:- `RFC` se dejó NULL porque MongoDB tiene valores vacíos
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:97:## 6. MATRIZ MongoDB vs EDARSAHUB
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:99:| MongoDB_ID | MongoDB_Nombre | MongoDB_Codigo | EDARSAHUB_EmpresaID | EDARSAHUB_NombreEmpresa | EDARSAHUB_Codigo | Coincidencia | Observaciones |
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:109:| MongoDB UUID | EDARSAHUB EmpresaID | Código |
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:137:| MongoDB | `empresas` | 5 |
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:148:| `Sistema_Empresas` no tiene columna para MongoDB_ID | P2 | **Documentado** - No se hizo ALTER TABLE |
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:150:| MongoDB sigue siendo fuente principal | P1 | Correcto por diseño |
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:155:Para trazabilidad completa, sería útil agregar columna `MongoDBUUID` a `Sistema_Empresas`:
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:159:ALTER TABLE Sistema_Empresas ADD MongoDBUUID UNIQUEIDENTIFIER NULL;
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:168:Crear tabla `Sistema_EmpresasEquivalencias` para mapear MongoDB UUID ↔ EDARSAHUB EmpresaID de forma persistente.
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:172:Actualizar `Usuario_Roles.NivelJerarquia` con valores de MongoDB `rbac_roles`:
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:196:| ⬜ | Agregar columna `MongoDBUUID` a `Sistema_Empresas` | **PENDIENTE AUTORIZACIÓN** |
/app/docs/FASE_A2_POBLADO_SISTEMA_EMPRESAS.md:212:| ✅ MongoDB sigue siendo fuente principal del sistema | CONFIRMADO |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:17:| 1 | `save_server_query()` | Config queries SQL | MongoDB `db.servers` | **EDARSAHUB** (`Servidores_Conexiones.query_*`) | ⚠️ REQUIERE ANÁLISIS |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:18:| 2 | `delete_server_query()` | Eliminación config | MongoDB `db.servers` | **EDARSAHUB** (`Servidores_Conexiones.query_*`) | ⚠️ REQUIERE ANÁLISIS |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:19:| 3 | `guardar_script_pendiente()` | Scripts stand-by | MongoDB `db.scripts_pendientes` | **MANTENER EN MONGODB** | ✅ MIGRAR SOLO LECTURA |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:31:- MongoDB es el destino correcto para este tipo de documentos operativos temporales
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:54:| **Dónde escribe actualmente** | MongoDB `db.servers` (campo `query_{type}`) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:61:| 1634 | `db.servers.find_one({"id": server_id, "active": True})` | Verificar que servidor existe |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:62:| 1648-1651 | `db.servers.update_one(...)` | **ESCRIBIR** query configurada |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:63:| 1654 | `db.servers.find_one({"id": server_id})` | Verificar si todas las queries están configuradas |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:64:| 1661-1664 | `db.servers.update_one(...)` | **ESCRIBIR** flag `queries_configured` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:105:1. Verificar que las queries en MongoDB estén sincronizadas a EDARSAHUB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:128:| **Dónde elimina actualmente** | MongoDB `db.servers` (campo `query_{type}` = null) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:135:| 1733 | `db.servers.find_one({"id": server_id, "active": True})` | Verificar que servidor existe |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:136:| 1738-1740 | `db.servers.update_one(...)` | **ESCRIBIR** null en query + flag |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:149:| Eliminación accidental | MEDIO | Ya existe el riesgo en MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:150:| Desincronización MongoDB/EDARSAHUB | MEDIO | Eliminar de ambos o solo EDARSAHUB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:177:| **Formato de datos** | Documento MongoDB con: server_id, titulo, script, estado, creado_por, fecha |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:178:| **Dónde escribe actualmente** | MongoDB `db.scripts_pendientes` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:179:| **Dónde debería escribir** | **MANTENER EN MONGODB** |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:181:#### Justificación de Mantener en MongoDB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:186:4. **MongoDB es apropiado** para este tipo de documentos de cola/workflow
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:192:| 11023 | `db.servers.find_one({"id": server_id, "active": True})` | Verificar que servidor existe |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:193:| 11041-11050 | `db.scripts_pendientes.insert_one(...)` | **ESCRIBIR** script pendiente (correcto en MongoDB) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:205:| Pérdida de scripts | BAJO | MongoDB tiene backups |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:212:El bypass en línea 11023 debe migrar a `get_server_connection_info()`, pero la escritura a `db.scripts_pendientes` debe **mantenerse en MongoDB**.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:214:**Clasificación: MANTENER TEMPORALMENTE EN MONGODB COMO DOCUMENTO OPERATIVO**
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:222:| `save_server_query()` | Config queries SQL | MongoDB `db.servers.query_*` | EDARSAHUB `Servidores_Conexiones.query_*` | `Servidores_Conexiones` | Usuario autenticado | **ALTO** | REQUIERE FUNCIÓN ESCRITURA | Restaurar de backup |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:223:| `delete_server_query()` | Eliminación config | MongoDB `db.servers.query_*` | EDARSAHUB `Servidores_Conexiones.query_*` | `Servidores_Conexiones` | Usuario autenticado | **MEDIO** | DEPENDE DE save_server_query | Restaurar de backup |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:224:| `guardar_script_pendiente()` | Scripts stand-by | MongoDB `db.scripts_pendientes` | **MongoDB** (correcto) | N/A | **Admin** | **BAJO** | MIGRAR SOLO LECTURA | Eliminar documento |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:240:- La escritura permanece en MongoDB (correcto)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:251:4. **Requieren sincronización previa** MongoDB → EDARSAHUB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:273:1. Exportar queries de MongoDB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:300:- [ ] Escribe en MongoDB `scripts_pendientes` (correcto)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:322:# (desde MongoDB shell o admin)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:323:db.scripts_pendientes.deleteOne({_id: ObjectId("...")})
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE6_PLAN.md:351:3. **Sincronizar queries existentes MongoDB → EDARSAHUB**
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:34:| **NO MIGRAR (Cat B original)** | 5 | Uso legítimo de MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:50:| **Bypass actual** | `db.servers.find({"id": {"$in": server_ids}}, ...)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:51:| **Dato de MongoDB** | Nombres de servidores para enriquecer respuesta |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:72:| **Bypass actual** | `db.servers.find({"active": True, ...})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:73:| **Dato de MongoDB** | Lista de servidores activos |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:92:| **Bypass actual** | `db.servers.find_one(query)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:93:| **Dato de MongoDB** | Configuración del servidor para consulta |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:112:| **Bypass actual** | `db.servers.find({"active": True, ...})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:113:| **Dato de MongoDB** | Lista de servidores para dashboard |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:136:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:137:| **Dato de MongoDB** | Conexión SQL para validar query |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:156:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:157:| **Dato de MongoDB** | Validación de servidor antes de guardar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:176:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:177:| **Dato de MongoDB** | Queries configuradas del servidor |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:195:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:196:| **Dato de MongoDB** | Validación antes de eliminar query |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:218:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:219:| **Dato de MongoDB** | Conexión SQL para generar reporte |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:239:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:240:| **Dato de MongoDB** | Conexión SQL para análisis |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:263:| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:264:| **Dato de MongoDB** | Conexión SQL para exportar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:288:| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:289:| **Dato de MongoDB** | Conexión SQL para análisis de compras |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:309:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:310:| **Dato de MongoDB** | Conexión SQL para facturas |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:330:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:331:| **Dato de MongoDB** | Conexión SQL para detalle |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:351:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:352:| **Dato de MongoDB** | Conexión SQL para detalle de ventas |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:376:| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:377:| **Dato de MongoDB** | Conexión SQL para productos |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:396:| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:397:| **Dato de MongoDB** | Conexión SQL para auditoría |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:416:| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:417:| **Dato de MongoDB** | Conexión SQL para movimientos |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:436:| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:437:| **Dato de MongoDB** | Conexión SQL para consumos |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:460:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:461:| **Dato de MongoDB** | Validación de servidor |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:479:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:480:| **Dato de MongoDB** | Conexión SQL para ejecutar script |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:498:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:499:| **Dato de MongoDB** | Conexión SQL para consulta |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:521:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:522:| **Dato de MongoDB** | Conexión SQL para consulta |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:540:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:541:| **Dato de MongoDB** | Conexión SQL para consulta |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:563:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE5_PLAN.md:564:| **Dato de MongoDB** | Conexión SQL para movimientos |
/app/docs/ENTREGABLES_AUDITORIA_RBAC.md:66:| `/app/backend/core/auditoria.py` | CREADO | Servicio de auditoría con fallback MongoDB |
/app/docs/ENTREGABLES_AUDITORIA_RBAC.md:98:- ✅ Fallback a MongoDB funciona cuando SQL Server no está disponible
/app/docs/ENTREGABLES_AUDITORIA_RBAC.md:149:- [ ] Sincronizar registros de MongoDB → SQL Server
/app/docs/ENTREGABLES_AUDITORIA_RBAC.md:170:from motor.motor_asyncio import AsyncIOMotorClient
/app/docs/ENTREGABLES_AUDITORIA_RBAC.md:172:    db = AsyncIOMotorClient('mongodb://localhost:27017')['edarsa_hub']
/app/docs/ENTREGABLES_AUDITORIA_RBAC.md:173:    async for doc in db.auditoria_financiera.find().sort('created_at', -1).limit(10):
/app/docs/FASE2_ALCANCE_CONTROLADO.md:308:- [ ] Backup de MongoDB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:14:**10 de 10 endpoints migrados exitosamente** de `db.servers.find_one()` a `server_registry.get_server_connection_info()`.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:46:| Bypass | `db.servers.find_one({"id": server_id, "active": True})` | `get_server_connection_info(server_id, db=db)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:54:| Bypass | `db.servers.find_one(...)` | `get_server_connection_info(...)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:61:| Bypass | `db.servers.find_one(...)` | `get_server_connection_info(...)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:68:| Bypass | `db.servers.find_one(...)` | `get_server_connection_info(...)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:74:| Bypass | `db.servers.find_one(...)` | `get_server_connection_info(...)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:82:| Bypass | `db.servers.find_one(...)` | `get_server_connection_info(...)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:84:| Log MongoDB | ✅ Usa `conn_info['name']` | ✅ Actualizado |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:90:| Bypass | `db.servers.find_one(...)` | `get_server_connection_info(...)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:97:| Bypass | `db.servers.find_one(...)` | `get_server_connection_info(...)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:104:| Bypass | `db.servers.find_one(...)` | `get_server_connection_info(...)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:111:| Bypass | `db.servers.find_one(...)` | `get_server_connection_info(...)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:189:| MongoDB no es fuente maestra en estos 10 puntos | ✅ Confirmado (`config_origin: EDARSAHUB_SQL`) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md:257:| MongoDB no es fuente maestra en los 10 puntos | ✅ |
/app/docs/governance/AGENTE_RECTOR_PROMPT.md:18:> Ningún dato operativo, comercial, financiero, contable, de usuarios, roles, permisos, servidores, tableros, KPIs, sincronizaciones o configuraciones críticas debe depender de MongoDB como fuente de verdad.
/app/docs/governance/AGENTE_RECTOR_PROMPT.md:25:2. No usar MongoDB para nuevos desarrollos salvo autorización explícita, justificación técnica documentada y ausencia real de alternativa SQL.
/app/docs/governance/AGENTE_RECTOR_PROMPT.md:59:   - Migración MongoDB a SQL
/app/docs/governance/AGENTE_RECTOR_PROMPT.md:100:- Usar MongoDB como solución rápida
/app/docs/CLASIFICACION_SERVIDORES_CORE_VS_DATASOURCE.md:54:servers = await db.servers.find({
/app/docs/AUDITORIA_FINANZAS.md:225:| Propinas TPV | cache | MongoDB | ✅ |
/app/docs/FASE_4C_ROTACION_CLAVES_SECRETOS.md:132:## 8. Manejo MongoDB Legacy
/app/docs/FASE_4C_ROTACION_CLAVES_SECRETOS.md:134:Si se usa `--include-mongo`:
/app/docs/FASE_4C_ROTACION_CLAVES_SECRETOS.md:136:1. Después de actualizar SQL, sincroniza a MongoDB
/app/docs/FASE_4C_ROTACION_CLAVES_SECRETOS.md:200:| `--include-mongo` | Sincronizar MongoDB espejo |
/app/docs/FASE_4C_ROTACION_CLAVES_SECRETOS.md:201:| `--only-sql` | Solo SQL, ignorar MongoDB |
/app/docs/FASE_4C_ROTACION_CLAVES_SECRETOS.md:230:  "mongo_synced": 0,
/app/docs/FASE_4C_ROTACION_CLAVES_SECRETOS.md:245:- `[SECRET_ROTATION][MONGO_SYNC_SUCCESS]`
/app/docs/FASE_4C_ROTACION_CLAVES_SECRETOS.md:263:| MongoDB desincronizado | Usar `--include-mongo` o sincronizar manual |
/app/docs/P1_REFRESH_TOKENS_TECHNICAL_PLAN.md:80:1. Valida credenciales contra MongoDB (`users` collection)
/app/docs/P1_REFRESH_TOKENS_TECHNICAL_PLAN.md:90:1. Valida RFC/contraseña contra MongoDB (`portal_suppliers`)
/app/docs/P1_REFRESH_TOKENS_TECHNICAL_PLAN.md:368:**¿Por qué EDARSAHUB (SQL Server) y no MongoDB?**
/app/docs/P1_REFRESH_TOKENS_TECHNICAL_PLAN.md:828:Los permisos se cargan desde MongoDB/SQL Server igual que antes.
/app/docs/P1_REFRESH_TOKENS_TECHNICAL_PLAN.md:1155:- ✅ **No usa MongoDB** como fuente maestra (usa EDARSAHUB SQL)
/app/docs/DIAGNOSTICO_COMERCIAL_TABLERO.md:70:│  (SoftRest/MPRO)│     │  (Caché MongoDB) │     │  (Dashboard)    │
/app/docs/DIAGNOSTICO_COMERCIAL_TABLERO.md:155:2. **Centralizar `SourceQueryResult`** en `core/db.py` para evitar parchear rutas individuales.
/app/docs/FINANZAS_CXP_MPRO_COMBINE_01_REPORT.md:24:| Fuente de credenciales | **MongoDB** (`db.servers`) | `repository_mpro.py:45-48` | BAJO | Servidor definido en MongoDB con ID fijo |
/app/docs/FINANZAS_CXP_MPRO_COMBINE_01_REPORT.md:25:| EDARSAHUB/server_registry usado | NO directamente | MPRO usa MongoDB, no server_registry | BAJO | Documentado |
/app/docs/FINANZAS_CXP_MPRO_COMBINE_01_REPORT.md:56:1. La contraseña en MongoDB está cifrada con formato `enc:v1:...`
/app/docs/FINANZAS_CXP_MPRO_COMBINE_01_REPORT.md:229:| Fuente credenciales | MongoDB (db.servers) | ✅ EDARSAHUB SQL (server_registry.py) |
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:17:| POST /api/servers | Crear en SQL, sync a MongoDB, sync_status=SYNCED | Servidor creado, sync_status=SYNCED | ✅ PASS | ID: 3f6ffbdf-1288-423d-aa42-3878b48e5022 |
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:18:| PUT /api/servers/{id} | Actualizar SQL, sync a MongoDB, no borrar password | Actualizado, password preservado | ✅ PASS | Host cambiado a 127.0.0.2 |
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:19:| DELETE /api/servers/{id} | Soft delete SQL+MongoDB (activo=false) | Registro existe, activo=false | ✅ PASS | Ambas BDs con activo=false |
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:23:| Reconciliación dry-run | Generar reporte | 11 SQL, 11 MongoDB, 0 diffs | ✅ PASS | servers_reconciliation_report.json |
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:70:- ✅ Registro existe en MongoDB con `active=True`
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:71:- ✅ `SQL.mongodb_id` apunta al mismo ID
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:99:- ✅ MongoDB actualizado: name, host, system_type
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:119:- ✅ MongoDB: `active = False` (registro existe)
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:227:## 5. RECONCILIACIÓN SQL ↔ MONGODB
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:229:**Script:** `/app/backend/scripts/reconcile_servers_sql_mongo.py`
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:233:python3 scripts/reconcile_servers_sql_mongo.py
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:243:  "mongo_count": 11,
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:246:  "mongo_only": 0,
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:255:- ✅ SQL y MongoDB sincronizados (11 = 11)
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:321:- ✅ POST crea SQL primero y MongoDB después
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:322:- ✅ PUT actualiza SQL primero y MongoDB después
/app/docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md:323:- ✅ DELETE aplica soft delete SQL primero y MongoDB después
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:1697:    [TipoMotorPrecio] VARCHAR(50) NULL DEFAULT ('VINOS_RANGOS'),
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:4288:    [FuenteOriginal] NVARCHAR(20) NOT NULL DEFAULT ('MONGODB'),
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:6997:    [mongodb_id] NVARCHAR(100) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:7011:    [mongodb_id] NVARCHAR(100) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:7052:    [mongodb_id] NVARCHAR(100) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:7203:-- TABLA: [dbo].[Sistema_EmpresasMongoMap]
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:7205:CREATE TABLE [dbo].[Sistema_EmpresasMongoMap] (
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:7207:    [EmpresaMongoUUID] VARCHAR(50) NOT NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:7208:    [EmpresaMongoLegacyID] VARCHAR(50) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:7218:    CONSTRAINT [PK_Sistema_EmpresasMongoMap] PRIMARY KEY ([MapID])
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:7347:    [MongoConfigID] VARCHAR(36) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:7368:    [MongoUUID] VARCHAR(36) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:7369:    [MongoEmpresaUUID] VARCHAR(36) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:7403:    [MongoSucursalUUID] VARCHAR(36) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:7404:    [MongoServidorUUID] VARCHAR(36) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:8587:    [LegacyMongoValue] VARCHAR(100) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:8682:    [MongoLegacyID] VARCHAR(50) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:8804:-- TABLA: [dbo].[Usuario_MigracionMongoTrace]
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:8806:CREATE TABLE [dbo].[Usuario_MigracionMongoTrace] (
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:8808:    [MongoID] VARCHAR(24) NOT NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:8811:    [RolMongoDB] VARCHAR(50) NOT NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:8812:    [ActivoMongoDB] BIT NOT NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:8816:    CONSTRAINT [PK_Usuario_MigracionMongoTrace] PRIMARY KEY ([TraceID])
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:8940:    [LegacyMongoValue] VARCHAR(100) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:8983:    [LegacyMongoValue] VARCHAR(100) NULL,
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:10738:ALTER TABLE [dbo].[Sistema_EmpresasMongoMap] ADD CONSTRAINT [FK_EmpresaID_SQL]
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:12578:CREATE UNIQUE NONCLUSTERED INDEX [UQ_EmpresaMongoUUID]
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:12579:    ON [dbo].[Sistema_EmpresasMongoMap] (EmpresaMongoUUID);
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:12800:CREATE UNIQUE NONCLUSTERED INDEX [IX_Usuario_MongoLegacyID]
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:12801:    ON [dbo].[Usuario_Catalogo] (MongoLegacyID);
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:12854:CREATE UNIQUE NONCLUSTERED INDEX [UQ_MigracionMongoTrace_Email]
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:12855:    ON [dbo].[Usuario_MigracionMongoTrace] (Email);
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:12857:CREATE UNIQUE NONCLUSTERED INDEX [UQ_MigracionMongoTrace_MongoID]
/app/docs/EDARSAHUB_SCHEMA_COMPLETO.sql:12858:    ON [dbo].[Usuario_MigracionMongoTrace] (MongoID);
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:76:| Cortes Caja | TODAS | - | Sí | /ingresos/cortes-caja | ninguno | 0 | MongoDB | **TABLA VACÍA REAL** | Sin sincronización |
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:77:| Cortes Caja | ManagementPro | MPRO | Sí | /ingresos/cortes-caja | server_id=... | 0 | MongoDB | **TABLA VACÍA REAL** | |
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:78:| Por Depositar | TODAS | - | Sí | /ingresos/saldos-por-depositar | ninguno | $0 | MongoDB | **TABLA VACÍA REAL** | |
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:79:| Comisiones | TODAS | - | Sí | /ingresos/resumen-comisiones | ninguno | $0 | MongoDB | **TABLA VACÍA REAL** | |
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:108:| Propinas | TODAS | - | Sí* | /finanzas/propinas | ninguno | 0 | MongoDB | **PENDIENTE SYNC** | |
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:109:| Propinas | LA ESTELAR | SR | Sí | /finanzas/propinas | server_id=... | 0 | MongoDB | **PENDIENTE SYNC** | |
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:110:| Propinas | CIENFUEGOS | SR | Sí | /finanzas/propinas | server_id=... | 0 | MongoDB | **PENDIENTE SYNC** | |
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:111:| Propinas | 130° MERIDA | SR | Sí | /finanzas/propinas | server_id=... | 0 | MongoDB | **PENDIENTE SYNC** | |
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:193:El archivo `/app/backend/modules/finanzas/repository_cortes_z.py` **NO utiliza** el sistema centralizado de conexiones (`core/server_registry.py` + credenciales cifradas en MongoDB).
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:217:| Credenciales | Cifradas en MongoDB (`edarsa_hub.servers`) | Hardcodeadas o env vars sin configurar |
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:219:| Filtro `server_id` | Usa UUID del registro en MongoDB | **NO USA** - consulta servidores fijos |
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:225:3. **Filtros por `server_id` inoperantes** → No consulta MongoDB para obtener servidor seleccionado
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:232:2. Usar `execute_sql_query()` de `core/db.py`
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:245:| Control Ingresos | EDARSAHUB.CortesCaja | EDARSAHUB.CortesCaja | MongoDB vacío | ❌ VACÍO |
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:247:| Propinas | SR.movtoscajadetalles | **N/A (excluido)** | MongoDB vacío | ❌ N/A MPRO |
/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md:370:| MongoDB usado para password | NO ✅ |
/app/docs/FASE5_HERENCIA_ROL_PROPUESTA.md:131:        rol = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
/app/docs/FASE5_HERENCIA_ROL_PROPUESTA.md:198:3. Opcional: db.sec_roles.drop()
/app/docs/FASE5_HERENCIA_ROL_PROPUESTA.md:199:4. Opcional: db.users.updateMany({}, {$unset: {sec_rol: 1}})
/app/docs/FASE5_HERENCIA_ROL_PROPUESTA.md:307:        rol = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
/app/docs/FASE5_HERENCIA_ROL_PROPUESTA.md:468:- db.sec_roles.drop()
/app/docs/FASE5_HERENCIA_ROL_PROPUESTA.md:469:- db.users.updateMany({}, {$unset: {sec_rol: 1}})
/app/docs/EDARSAHUB_SCHEMA_ONLY.sql:263:    [mongodb_id] NVARCHAR(100) NULL,
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:38:- [x] C2 - `get_inventarios_list()` - Línea 2603 - **OK con observación (MongoDB fallback)**
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:39:- [x] C3 - `get_pendientes_descargar()` - Línea 2708 - **OK con observación (MongoDB fallback)**
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:40:- [x] C5 - `get_report_filters()` - Línea 2961 - **OK con observación (MongoDB fallback)**
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:41:- [x] C1 - `get_almacenes_softrestaurant()` - Línea 2541 - **OK con observación (MongoDB fallback)**
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:42:- [x] C8 - `ejecutar_consulta_catalogo()` - Línea 5459 - **OK con observación (MongoDB fallback)**
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:57:- [x] `guardar_script_pendiente()` - Línea 11010 - Solo lectura servidor, escritura en MongoDB (documento operativo)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:75:- MongoDB `db.servers` está vacío (0 documentos)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:85:Se han analizado y clasificado los **56 accesos directos** a `db.servers.find_one(...)` o `db.servers.find(...)` en el archivo `/app/backend/server.py`. Estos bypasses ignoran el módulo centralizado `core/server_registry.py` que implementa correctamente la arquitectura EDARSAHUB-first.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:121:| ID | Línea | Endpoint/Función | Uso MongoDB | ¿Resuelve SQL? | Riesgo | Acción |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:123:| A01 | 1315 | `test_server_connection` | `db.servers.find_one({"id": server_id})` | Sí - host/port/user/pass para execute_sql_query | ALTO | Migrar a `get_server_connection_info()` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:124:| A02 | 1531 | `validate_server_query` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - conexión SQL para validar query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:125:| A03 | 1622 | `save_server_query` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - lectura de config servidor | MEDIO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:126:| A04 | 1667 | `get_server_queries` | `db.servers.find_one({"id": server_id, "active": True})` | Parcial - lee config queries | MEDIO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:127:| A05 | 1721 | `delete_server_query` | `db.servers.find_one({"id": server_id, "active": True})` | Parcial | BAJO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:128:| A06 | 1738 | `get_tipos_movimiento` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:129:| A07 | 1782 | `get_categorias` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:130:| A08 | 1824 | `get_departamentos` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:131:| A09 | 1922 | `get_sucursales` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:132:| A10 | 2019 | `get_almacenes` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:133:| A11 | 2091 | `get_sucursales_config` | `db.servers.find_one({"id": server_id, "active": True})` | Parcial - valida existencia | MEDIO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:134:| A12 | 2119 | `sync_sucursales_config` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:135:| A13 | 2439 | `get_almacenes_softrestaurant` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:136:| A14 | 2501 | `get_inventarios_list` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:137:| A15 | 2606 | `get_pendientes_descargar` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:138:| A16 | 2821 | `generate_inventory_report` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:139:| A17 | 2859 | `get_report_filters` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:140:| A18 | 3026 | `generar_analisis_inventario` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:141:| A19 | 4309 | `get_detalle_movimientos_producto` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:142:| A20 | 4542 | `get_detalle_ventas_producto` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:143:| A21 | 5094 | `export_inventario_comparativo` | `db.servers.find_one({"id": request.server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:144:| A22 | 5357 | `ejecutar_consulta_catalogo` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:145:| A23 | 5423 | `ejecutar_consulta_personalizada` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:146:| A24 | 5502 | `debug_mpro_calculo` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | MEDIO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:147:| A25 | 5809 | `get_dashboard_inventory` | `db.servers.find_one(query)` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:148:| A26 | 6096 | `validate_server_access_by_empresa` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - credenciales | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:149:| A27 | 6975 | `obtener_productos_para_captura` | `db.servers.find_one({"id": request.server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:150:| A28 | 7090 | `realizar_auditoria_operativa` | `db.servers.find_one({"id": request.server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:151:| A29 | 7794 | `obtener_detalle_movimientos_post` | `db.servers.find_one({"id": request.server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:152:| A30 | 7971 | `obtener_detalle_consumos_post` | `db.servers.find_one({"id": request.server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:153:| A31 | 8313 | `obtener_analisis_compras` | `db.servers.find_one({"id": request.server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:154:| A32 | 8460 | `obtener_facturas_proveedor` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:155:| A33 | 8525 | `obtener_detalle_factura` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:156:| A34 | 8746 | `listar_tablas` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | MEDIO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:157:| A35 | 8786 | `listar_columnas` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | MEDIO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:158:| A36 | 8827 | `listar_relaciones` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | MEDIO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:159:| A37 | 8874 | `preview_tabla` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | MEDIO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:160:| A38 | 8915 | `ejecutar_query_libre` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:161:| A39 | 8961 | `ejecutar_script_sql` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:162:| A40 | 9926 | `execute_edarsa_hub_query` | `db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})` | Sí - CRÍTICO: helper para EDARSA HUB | **CRÍTICO** | Migrar primero |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:163:| A41 | 10767 | `guardar_script_standby` | `db.servers.find_one({"id": server_id, "active": True})` | Parcial | BAJO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:164:| A42 | 10892 | `ejecutar_script_con_credenciales` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query con creds admin | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:165:| A43 | 11406 | `buscar_global_bd` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | MEDIO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:166:| A44 | 11641 | `ejecutar_consulta_catalogo_v2` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:167:| A45 | 11877 | `ejecutar_consulta_custom` | `db.servers.find_one({"id": server_id, "active": True})` | Sí - execute_sql_query | ALTO | Migrar |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:173:Estos casos usan MongoDB **legítimamente** para cache, conteos, métricas o listados sin resolver credenciales SQL.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:175:| ID | Línea | Endpoint/Función | Uso MongoDB | ¿Resuelve SQL? | ¿Cache/Log? | Clasificación | Justificación |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:177:| B01 | 5989 | `get_dashboard_servers` | `db.servers.find({"active": True, "queries_configured": True})` | No | Listado | NO MIGRAR | Solo lista servidores para selector UI, no conecta |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:178:| B02 | 6000 | `get_dashboard_metrics` | `db.servers.count_documents({"active": True})` | No | Conteo | NO MIGRAR | Solo cuenta servidores activos |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:179:| B03 | 6003 | `get_dashboard_metrics` | `db.servers.count_documents({"active": True, "queries_configured": True})` | No | Conteo | NO MIGRAR | Solo cuenta servidores configurados |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:180:| B04 | 2302 | `get_sucursales_globales` | `db.servers.find({"id": {"$in": server_ids}})` | No | Enriquecimiento | NO MIGRAR | Solo enriquece nombres de servidor en resultado |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:181:| B05 | 2368 | `get_unidades_negocio` | `db.servers.find({"id": {"$in": server_ids}})` | No | Metadata | NO MIGRAR | Solo obtiene system_type para respuesta |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:189:| ID | Línea | Endpoint/Función | Uso MongoDB | Duda | Acción Recomendada |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:191:| C01 | 1636 | `save_server_query` | `db.servers.update_one({"id": server_id}, ...)` | Escribe configuración de query en MongoDB | Revisar si la config de queries debe ir a EDARSAHUB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:192:| C02 | 1642 | `save_server_query` | `db.servers.find_one({"id": server_id})` | Lee servidor post-update | Depende de C01 |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:193:| C03 | 1649 | `save_server_query` | `db.servers.update_one({"id": server_id}, ...)` | Escribe flag queries_configured | Revisar si el flag debe ir a EDARSAHUB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:194:| C04 | 1726 | `delete_server_query` | `db.servers.update_one({"id": server_id}, ...)` | Elimina configuración de query | Revisar si la config de queries debe ir a EDARSAHUB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:196:**Nota sobre C01-C04:** Estas operaciones de escritura actualizan configuración de queries SQL en MongoDB. El diseño actual asume que `queries_configured`, `query_ventas`, `query_inventario`, etc. se almacenan en MongoDB. Si EDARSAHUB es el maestro, deberían escribirse allá primero y sincronizar a MongoDB.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:212:## 3. USOS LEGÍTIMOS DE MONGODB (NO TOCAR)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:214:Los siguientes usos de MongoDB son correctos y **NO deben migrarse**:
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:218:| `server_status` | Cache de estado de conexión | Línea 1337: `db.server_status.update_one(...)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:219:| `server_sucursales_config` | Configuración de visibilidad de sucursales | Línea 2096: `db.server_sucursales_config.find(...)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:258:| Falla de conexión a EDARSAHUB | Baja | Alto | `server_registry.py` ya tiene fallback a MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:261:| Performance degradada | Baja | Bajo | SQL es más rápido que MongoDB para lookups por ID |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:299:3. El registry automáticamente usará MongoDB como fallback
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:333:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:359:- Fallback automático a MongoDB si SQL falla
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md:372:- 9% (5/56) son usos legítimos de MongoDB que **NO** deben tocarse
/app/docs/DEFINICION_TECNICA_FINAL_SOFTRESTAURANT.md:176:| `server_id` | MongoDB (EDARSA HUB) | Identificador del servidor |
/app/docs/FASE14_EVIDENCIA.md:138:| MongoDB users | +campo `sec_roles_alcance` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:11:Se identificaron **múltiples módulos que hacen bypass** del `server_registry.py` y acceden directamente a MongoDB para resolver configuración de servidores.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:35:# 2. MongoDB (fallback legacy)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:46:El archivo principal del backend tiene 56 accesos directos a `db.servers`:
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:50:| 1315 | sync_server_data | `db.servers.find_one` | ALTO |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:51:| 1531 | get_server_data | `db.servers.find_one` | ALTO |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:52:| 1622-1782 | Múltiples endpoints | `db.servers.find_one` | ALTO |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:53:| 1824-2019 | Endpoints comercial | `db.servers.find_one` | ALTO |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:54:| 2091-2606 | Endpoints finanzas | `db.servers.find_one` | ALTO |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:55:| 2821-3026 | Endpoints compras | `db.servers.find_one` | ALTO |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:56:| 4309-4542 | Endpoints inventarios | `db.servers.find_one` | ALTO |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:58:**Impacto:** Estos endpoints **NUNCA** usan EDARSAHUB como fuente, siempre van a MongoDB.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:66:| `repository_real.py:47` | `__init__` | `db.servers.find_one` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:67:| `repository_mpro.py:42` | `_server_cache` | `db.servers.find_one` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:68:| `historical_kpis_repository.py:31` | búsqueda | `db.servers.find_one` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:70:| `propinas_tpv/routes_sql.py:408,440,516` | múltiples | `db.servers.find_one/find` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:71:| `propinas_tpv/routes.py:222,262,358` | múltiples | `db.servers.find_one/find` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:72:| `propinas_tpv/sql_repository.py:70` | búsqueda | `mongo_db.servers.find_one` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:81:| `repository.py:111` | `get_server_by_id` | `db.servers.find_one` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:82:| `historical_kpis_repository.py:37` | búsqueda | `db.servers.find_one` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:90:| `repository.py:224` | `get_server_by_id` | `db.servers.find_one` | Es FALLBACK después de SQL |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:91:| `repository.py:243` | `get_all_active_servers` | `db.servers.find` | Es FALLBACK |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:92:| `adapters.py:273` | apis locales | `sync_db.servers.find` | BYPASS directo |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:102:| `importador/repository.py:68` | búsqueda | `db.servers.find_one` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:103:| `repository.py:126` | búsqueda | `db.servers.find_one` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:111:| `repositories/config_asignaciones_repository.py:249` | búsqueda | `db.servers.find_one` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:112:| `services/almacenes_sync_service.py:138` | búsqueda | `db.servers.find_one` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:120:| `repository.py:31` | EDARSA HUB | `db.servers.find_one` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:128:| `routes/portal_proveedores.py` | 2 accesos | `db.servers.find_one` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:136:| `core/scheduler/jobs/inventarios_detector_job.py` | 2 accesos | `db.servers` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:144:| `core/context_resolver.py` | 2 accesos | `db.servers` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:152:| `fase2_operativo/repositories/asignacion_repository.py:20` | collection | `db.server_sucursales_config` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:161:| `scripts/reconcile_servers_sql_mongo.py` | Sincronización |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:168:## USOS LEGÍTIMOS DE MONGODB (NO TOCAR)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:206:2. Reemplazar todos los `db.servers.find_one({"id": server_id})` por `get_server_config(server_id)`
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:207:3. Registry se encarga de EDARSAHUB → MongoDB fallback
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:267:Los módulos que hacen bypass NUNCA consultan EDARSAHUB como fuente primaria. Siempre usan MongoDB directamente, violando la arquitectura definida.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:297:| Lote 1 | 5 | OK con observación | Brecha: usa MongoDB fallback |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:298:| Lote 2 | 5 | OK con observación | Brecha: usa MongoDB fallback |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:299:| Lote 3 | 5 | OK con observación | Brecha: usa MongoDB fallback |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:304:| Server ID | Servidor | Existe en EDARSAHUB | Existe en MongoDB | Acción |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:311:**CAPA A - Migración técnica:** Los 15 endpoints migrados usan `server_registry.py` y ya no hacen bypass directo a `db.servers.find_one()`. Migración técnica completa.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:315:**CAPA C - Arquitectura:** BRECHA DE CATÁLOGO MAESTRO. Todos los servidores se resuelven vía MongoDB fallback porque no existen en EDARSAHUB. El fallback funciona como tolerancia legacy temporal, pero no es arquitectura final correcta.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:333:| MongoDB | 0 | Colección vacía |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:337:2. MongoDB `db.servers` está vacío
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:340:5. **NO hay datos que migrar de MongoDB a EDARSAHUB**
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:412:- **Origen**: MongoDB (`db.servers`)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_DIAGNOSTICO.md:436:El repositorio MPRO (`repository_mpro.py`) leía credenciales desde MongoDB en lugar de EDARSAHUB SQL.
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:12:El módulo RH/Nóminas está bloqueado porque depende de un registro de servidor en MongoDB (`servers`) con `active=True`, cuando debería usar la **conexión interna directa** a EDARSAHUB como lo hace `server_registry.py`.
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:17:RH Repository → MongoDB.servers.find_one({id: X, active: True}) → FALLA (active=False)
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:32:| `/rrhh/catalogos/puestos` | routes.py:158 | `rrhh_listar_puestos` | `RHCatalogosService.listar_puestos` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:33:| `/rrhh/catalogos/sucursales` | routes.py:215 | `rrhh_listar_sucursales` | `RHCatalogosService.listar_sucursales` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:34:| `/rrhh/catalogos/tipos-incidencias` | routes.py:232 | `rrhh_listar_tipos_incidencias` | `RHCatalogosService.listar_tipos_incidencias` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:35:| `/rrhh/colaboradores` | routes.py:306 | `rrhh_listar_colaboradores` | `RHColaboradoresService.listar` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:36:| `/rrhh/incidencias` | routes.py:431 | `rrhh_listar_incidencias` | `RHIncidenciasService.listar` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:37:| `/rrhh/asistencia` | routes.py:568 | `rrhh_listar_asistencia` | `RHAsistenciaService.listar` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:38:| `/rrhh/nominas/flujo` | routes.py:674 | `rrhh_listar_flujos` | `RHNominasService.listar_flujos` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:39:| `/rrhh/dashboard` | routes.py:824+ | `rrhh_dashboard` | `RHDashboardService.obtener` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:40:| `/rrhh/reclutamiento/*` | routes.py:880+ | varios | `RHReclutamientoService` | `get_edarsa_hub_server` | EDARSAHUB interno | MongoDB servers | NO | SÍ | ⛔ BLOQUEADO | FALLA ARQUITECTURA |
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:41:| `/nomina/ciclos` | server.py:13901 | `listar_ciclos_nomina` | — | — | MongoDB `nomina_ciclos` | MongoDB | N/A | NO | ⚠️ SIN DATOS | OK (diferente fuente) |
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:62:**NO depende de:** MongoDB `servers` ni de `active=True/False`  
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:65:### 2. Conexión vía MongoDB servers (PROBLEMÁTICA)
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:75:    return await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:78:**Depende de:** Registro en MongoDB `servers` con `active: True`  
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:113:| Fuente de conexión | `EDARSAHUB_CONFIG` (variables de entorno) | MongoDB `servers` |
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:138:2. **Está usando:** Búsqueda en MongoDB `servers` con `active=True`
/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md:176:1. Activar registro en MongoDB
/app/docs/snapshots/diff_clasificacion_servidores.md:68:-    servers = await db.servers.find({"active": True}, {"_id": 0, "password": 0}).to_list(1000)
/app/docs/snapshots/diff_clasificacion_servidores.md:71:+    servers = await db.servers.find(
/app/docs/snapshots/diff_clasificacion_servidores.md:117:+    existing = await db.servers.find_one({"id": server_id})
/app/docs/snapshots/diff_clasificacion_servidores.md:124:     await db.servers.update_one({"id": server_id}, {"$set": {"active": False}})
/app/docs/P0_USUARIOS_VISIBILIDAD_FIX_REPORT.md:58:### Detalle de cambios en MongoDB:
/app/docs/P0_USUARIOS_VISIBILIDAD_FIX_REPORT.md:62:db.users.updateOne(
/app/docs/P0_USUARIOS_VISIBILIDAD_FIX_REPORT.md:68:db.users.updateOne(
/app/docs/P0_USUARIOS_VISIBILIDAD_FIX_REPORT.md:196:// En MongoDB shell o script Python
/app/docs/P0_USUARIOS_VISIBILIDAD_FIX_REPORT.md:197:db.users.updateOne(
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:13:Se completaron exitosamente los 5 cambios del Lote 1, migrando los bypasses de `db.servers.find_one()` hacia `server_registry.get_server_connection_info()`.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:42:    server = decrypt_server_secrets(await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:54:**Bypass eliminado:** `db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:65:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:74:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:85:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:94:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:105:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:114:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:125:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:134:**Bypass eliminado:** `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})`  
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:217:| DuplicateKey en índice MongoDB | Error preexistente; no afecta funcionalidad | N/A |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:263:- 5 bypasses eliminados de `db.servers.find_one()`
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE1_REPORT.md:268:- MongoDB deja de ser fuente maestra en los 5 puntos corregidos
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_B.md:316:            await self.db.execute("""
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_B.md:396:        existente = await self.db.fetch_one("""
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_B.md:446:                result = await self.db.execute("""
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_B.md:488:            result = await self.db.execute("""
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_B.md:529:                    result = await self.db.execute("""
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_B.md:575:        await self.db.execute("""
/app/docs/FASE_A1_7_DDL_BASE_ORGANIZACIONAL_AUTH_RBAC.md:285:| MongoDB sigue siendo fuente principal | P1 | Correcto por ahora |
/app/docs/FASE_A1_7_DDL_BASE_ORGANIZACIONAL_AUTH_RBAC.md:294:**Objetivo:** Insertar en `Sistema_Empresas` los datos de MongoDB `empresas`.
/app/docs/FASE_A1_7_DDL_BASE_ORGANIZACIONAL_AUTH_RBAC.md:299:-- Insertar empresas desde MongoDB
/app/docs/FASE_A1_7_DDL_BASE_ORGANIZACIONAL_AUTH_RBAC.md:311:**Objetivo:** Asignar valores de nivel a los roles según MongoDB `rbac_roles`.
/app/docs/FASE_A1_7_DDL_BASE_ORGANIZACIONAL_AUTH_RBAC.md:316:-- Actualizar NivelJerarquia según rbac_roles de MongoDB
/app/docs/FASE_A1_7_DDL_BASE_ORGANIZACIONAL_AUTH_RBAC.md:349:| ✅ MongoDB sigue siendo fuente principal | CONFIRMADO |
/app/docs/POLITICA_TRANSVERSAL_FECHAS_Y_CONEXIONES.md:68:**ÚNICA fuente de credenciales**: MongoDB (colección `servers`)
/app/docs/POLITICA_TRANSVERSAL_FECHAS_Y_CONEXIONES.md:82:# ✅ CORRECTO: Desde MongoDB vía parámetro server
/app/docs/POLITICA_TRANSVERSAL_FECHAS_Y_CONEXIONES.md:89:        server['password'],  # Viene de MongoDB
/app/docs/POLITICA_TRANSVERSAL_FECHAS_Y_CONEXIONES.md:113:Las siguientes credenciales hardcodeadas deben migrarse a MongoDB:
/app/docs/POLITICA_TRANSVERSAL_FECHAS_Y_CONEXIONES.md:123:2. Migrar configuración a MongoDB `servers`
/app/docs/POLITICA_TRANSVERSAL_FECHAS_Y_CONEXIONES.md:137:├── db.py                     # execute_sql_query
/app/docs/POLITICA_TRANSVERSAL_FECHAS_Y_CONEXIONES.md:148:- [ ] ¿Las credenciales vienen de MongoDB (parámetro `server`)?
/app/docs/ARQUITECTURA_SEGURIDAD_EDARSA_HUB_v2.md:437:- [ ] Backup completo de MongoDB
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:12:Este documento resuelve el bloqueo P0 de mapeo organizacional identificando las diferencias críticas entre las entidades Empresa, Unidad de Negocio, Sucursal y Servidor en MongoDB vs EDARSAHUB.
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:16:| Entidad | MongoDB | EDARSAHUB | ¿Tabla existe? | ¿IDs coinciden? |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:25:**`users.empresas_permitidas`** usa IDs de la colección `empresas` de MongoDB, pero **EDARSAHUB no tiene tabla de Empresas**. 
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:44:### Jerarquía en MongoDB (Actual)
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:84:│  Unidades_Negocio   │  ← Existe pero IDs NO coinciden con MongoDB
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:94:│  SucursalID: INT    │  ← Tipo incompatible con MongoDB
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:99:│ Servidores_Conexiones│  ← IDs SÍ coinciden con MongoDB
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:107:## 3. INVENTARIO MONGODB
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:199:**⚠️ Problema:** `SucursalID` es INT, pero MongoDB usa UUID para sucursales.
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:228:## 5. MATRIZ DE EQUIVALENCIAS MONGODB vs EDARSAHUB
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:232:| MongoDB ID | MongoDB Nombre | EDARSAHUB Tabla | EDARSAHUB ID | Coincidencia | Riesgo |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:242:| MongoDB Nombre | MongoDB ID | EDARSAHUB Nombre | EDARSAHUB ID | ¿Coincide ID? | ¿Coincide Nombre? |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:256:| MongoDB ID | MongoDB Nombre | EDARSAHUB ID | EDARSAHUB Nombre | ¿Coincide? |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:268:**✅ Los IDs de Servidores SÍ coinciden entre MongoDB y EDARSAHUB.**
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:274:| Entidad | MongoDB | EDARSAHUB | Coincidencia |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:286:| **Sucursales** | EDARSAHUB usa INT, MongoDB usa UUID | Tipos incompatibles |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:296:| R-P0-001 | `users.empresas_permitidas` usa IDs de `empresas` MongoDB que no existen en EDARSAHUB | **Login y filtros RBAC fallarían** |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:298:| R-P0-003 | `sec_unidades_negocio.empresa_id` apunta a empresa inexistente (`62786c07-...`) | **Inconsistencia de datos en MongoDB** |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:304:| R-P1-001 | IDs de `Unidades_Negocio` MongoDB ≠ EDARSAHUB | Requiere mapeo por nombre |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:305:| R-P1-002 | `RH_Cat_Sucursales` usa INT, no UUID | Tipos incompatibles con MongoDB |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:306:| R-P1-003 | EDARSAHUB tiene 2 unidades (ORIGEN, 130° QRO) que MongoDB no tiene | Datos incompletos |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:312:| R-P2-001 | MongoDB tiene 7 unidades, EDARSAHUB solo 5 | Mapeo parcial |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:313:| R-P2-002 | Sucursales en EDARSAHUB no coinciden con MongoDB | Filtros por sucursal incorrectos |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:332:| **D** | Mantener `empresas_permitidas` en MongoDB temporalmente | Sin cambios inmediatos | Deuda técnica persiste |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:367:| C | Redefinir `empresas_permitidas` en MongoDB para usar IDs de `Unidades_Negocio` |
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:383:Valores sugeridos (de `rbac_roles` MongoDB):
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:469:    EmpresaUUID_MongoDB     UNIQUEIDENTIFIER NOT NULL,
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:470:    EmpresaNombre_MongoDB   NVARCHAR(100) NOT NULL,
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:477:    CONSTRAINT UQ_Equivalencias_MongoDB UNIQUE (EmpresaUUID_MongoDB)
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:496:1. ✅ Backup MongoDB (COMPLETADO)
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:506:1. ⬜ INSERT `Sistema_Empresas` con datos de MongoDB `empresas`
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:517:2. ⬜ Mantener MongoDB como fallback
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:542:# Si 'false', el sistema sigue leyendo de MongoDB
/app/docs/MAPEO_ORGANIZACIONAL_AUTH_RBAC_EDARSAHUB.md:553:| 1 | ✅ Backup MongoDB | COMPLETADO |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:23:### 2.1 Colecciones MongoDB Existentes
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:293:Durante la ejecución safe-mode se detectó que los KPIs históricos se insertaron en **MongoDB** (`kpis_comercial`), violando la regla maestra de arquitectura:
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:295:> **EDARSAHUB SQL es el cerebro. MongoDB NO debe ser destino final de históricos ni KPIs definitivos.**
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:301:| **KPIs históricos comerciales** | MongoDB `kpis_comercial` | EDARSAHUB SQL | **CORREGIR SCRIPT** |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:302:| Checkpoints | MongoDB | MongoDB permitido | Documentar |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:303:| Logs del job | MongoDB | MongoDB permitido | Documentar |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:304:| Cache dashboard | MongoDB | MongoDB permitido | No fuente final |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:305:| Staging temporal | MongoDB | Promover a SQL | Controlar |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:360:Checkpoint/log en MongoDB (permitido)
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:362:MongoDB cache opcional (NO fuente final)
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:367:Los 14 registros insertados en MongoDB durante safe-mode se clasifican como:
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:381:4. ✅ MongoDB clasificado como cache/log/checkpoint/staging únicamente
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:404:| MongoDB `kpis_comercial` | EDARSAHUB SQL `Comercial_KPIs_Historico` |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:412:| `/app/backend/scripts/run_historical_load_24_months.py` | Modificado | Destino SQL, MongoDB solo checkpoint |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:445:| **MongoDB final** | **0** ✅ |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:448:### 13.5 14 Registros MongoDB de Prueba Anterior
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:450:Los 14 registros del run `HL_20260426_003155` en MongoDB `kpis_comercial` quedan:
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:454:- **Opción futura**: Migrar a SQL usando `migrate_staging_mongo_kpis_to_sql()`
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:463:| MongoDB no es destino final | ✅ |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:467:| MongoDB staging documentado | ✅ |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:472:2. Evaluar migración de MongoDB staging a SQL
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:487:| MongoDB final | **0** ✅ |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:514:| MongoDB no es destino final | ✅ |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:545:| **MongoDB final** | **0** ✅ |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:564:| MongoDB final = 0 | ✅ |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:589:| MongoDB final insertados | **0** ✅ |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:599:| MongoDB final = 0 | ✅ |
/app/docs/MACROFASE_2_FASE_2_3_CARGA_HISTORICA_24_MESES.md:632:| MongoDB final | **0** ✅ |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md:35:| `query_inventario` | MongoDB `db.servers` | EDARSAHUB `Servidores_Conexiones` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md:36:| `query_ventas` | MongoDB `db.servers` | EDARSAHUB `Servidores_Conexiones` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md:37:| `query_movimientos` | MongoDB `db.servers` | EDARSAHUB `Servidores_Conexiones` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md:38:| `queries_configured` | MongoDB `db.servers` | EDARSAHUB `Servidores_Conexiones` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md:42:Actualmente en MongoDB, cada `query_*` almacena un objeto JSON:
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md:123:| 1 | `query_{type}` con JSON | MongoDB `db.servers` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md:124:| 2 | `queries_configured` (recalculado) | MongoDB `db.servers` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md:154:| ¿Borra histórico? | No (MongoDB no tiene histórico) |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md:188:        db: Conexión MongoDB (para fallback si aplica)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md:227:        db: Conexión MongoDB (para fallback si aplica)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md:451:| `save_server_query()` | UPDATE MongoDB | `Servidores_Conexiones` | Autenticado → **Admin** | Whitelist, servidor existe, alcance RBAC | MEDIO | Migrar con auditoría |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_E_SERVER_QUERIES_WRITE_PLAN.md:452:| `delete_server_query()` | SET NULL MongoDB | `Servidores_Conexiones` | Autenticado → **Admin** | Whitelist, servidor existe, alcance RBAC | BAJO | Migrar con auditoría |
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:1:# FASE 3B.1 - Endpoints de Escritura SQL-First y Sincronización Legacy MongoDB
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:10:La FASE 3B.1 migró los endpoints de escritura de servidores (`POST`, `PUT`, `DELETE`) para que escriban primero en EDARSAHUB SQL y sincronicen MongoDB como espejo legacy.
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:14:- MongoDB se actualiza como espejo después de cada operación exitosa en SQL
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:15:- Si MongoDB sync falla, se devuelve `sync_status: PARTIAL_SYNC`
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:50:| `create_server(payload, db, user, sync_mongo)` | Crea servidor en SQL, sincroniza a MongoDB |
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:51:| `update_server(server_id, payload, db, user, sync_mongo)` | Actualiza en SQL, sincroniza a MongoDB |
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:52:| `delete_server(server_id, db, user, sync_mongo, soft_delete)` | Soft delete en SQL y MongoDB |
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:53:| `sync_server_to_mongo(sql_server_id, db)` | Sincroniza un servidor específico de SQL a MongoDB |
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:63:**Antes:** Escribía solo a MongoDB  
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:68:4. Sincroniza a MongoDB
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:87:**Antes:** Actualizaba solo MongoDB  
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:90:2. Verifica existencia en SQL (también busca por `mongodb_id`)
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:93:5. Sincroniza a MongoDB
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:108:**Antes:** Soft delete solo en MongoDB  
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:113:4. Sincroniza soft delete a MongoDB (`active=false`)
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:153:              │ Error 400  │         │ Sync MongoDB│
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:160:                          │ Mongo OK   │        │ Mongo FAIL │
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:173:Si SQL escribe exitosamente pero MongoDB falla:
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:178:- Se registra log `[SERVER_REGISTRY][SYNC_MONGO_ERROR]`
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:180:**Reconciliación:** Usar script de reconciliación o función `sync_server_to_mongo()` para sincronizar manualmente.
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:233:| `[SERVER_REGISTRY][SYNC_MONGO_START]` | Inicio de sync a MongoDB |
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:234:| `[SERVER_REGISTRY][SYNC_MONGO_SUCCESS]` | Sync exitoso a MongoDB |
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:235:| `[SERVER_REGISTRY][SYNC_MONGO_ERROR]` | Sync falló (PARTIAL_SYNC) |
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:245:| PARTIAL_SYNC no tiene reconciliación automática | BAJO | Función `sync_server_to_mongo()` disponible |
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:252:2. ~~**Crear script de reconciliación** `/app/backend/scripts/reconcile_servers_sql_mongo.py`~~ ✅ COMPLETADO (FASE 3B.2)
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:265:- ✅ POST crea SQL primero y MongoDB después
/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md:266:- ✅ PUT actualiza SQL primero y MongoDB después
/app/docs/P0_REGRESION_SQL_SERVERS_CORRECCION_REPORT.md:35:**Cambio 2 (línea ~318):** Agregar filtro en MongoDB fallback
/app/docs/P0_REGRESION_SQL_SERVERS_CORRECCION_REPORT.md:103:- ✅ MongoDB NO es fuente primaria
/app/docs/FASE15_PROPUESTA.md:520:│ - MongoDB: permisos en sec_roles, actualizar sec_perfiles   │
/app/docs/SYSTEM_TYPE_NORMALIZATION_CIERRE_3A1.md:194:2. Actualizar resolución de system_type desde SQL en lugar de MongoDB
/app/docs/CODE_QUALITY_FIXES_STOCK_TRACKER_990.md:89:- `test_core_db.py` - Usa valores de conexión mock
/app/docs/FASE4_ADMINISTRACION_PERMISOS_PROPUESTA.md:352:    existe = await db.sec_permisos_catalogo.find_one({"codigo": permiso})
/app/docs/FASE4_ADMINISTRACION_PERMISOS_PROPUESTA.md:357:    usuario = await db.users.find_one({"email": usuario_email})
/app/docs/FASE4_ADMINISTRACION_PERMISOS_PROPUESTA.md:374:    await db.users.update_one(
/app/docs/FASE4_ADMINISTRACION_PERMISOS_PROPUESTA.md:400:        await db.sec_bitacora_admin.insert_one({
/app/docs/FASE4_ADMINISTRACION_PERMISOS_PROPUESTA.md:546:db.sec_bitacora_admin.createIndex({ "timestamp": -1 })
/app/docs/FASE4_ADMINISTRACION_PERMISOS_PROPUESTA.md:547:db.sec_bitacora_admin.createIndex({ "usuario_afectado.email": 1 })
/app/docs/FASE4_ADMINISTRACION_PERMISOS_PROPUESTA.md:548:db.sec_bitacora_admin.createIndex({ "administrador.email": 1 })
/app/docs/FASE4_ADMINISTRACION_PERMISOS_PROPUESTA.md:549:db.sec_bitacora_admin.createIndex({ "tipo": 1, "timestamp": -1 })
/app/docs/FASE4_ADMINISTRACION_PERMISOS_PROPUESTA.md:599:- db.sec_bitacora_admin.drop() (solo si se desea)
/app/docs/FASE4_ADMINISTRACION_PERMISOS_PROPUESTA.md:656:4. **Consulta MongoDB** → Auditoría registrada en `sec_bitacora_admin`
/app/docs/FASE4_ADMINISTRACION_PERMISOS_PROPUESTA.md:669:| 2 | Crear colección `sec_bitacora_admin` | MongoDB |
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:15:Los módulos leían `server['password']` directamente de MongoDB o SQL, donde ahora los passwords están cifrados con formato `enc:v1:<ciphertext>`. Esto causaría fallos de conexión porque `enc:v1:xxx` no es un password válido para SQL Server.
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:19:1. Agregar descifrado automático en funciones que mapean servidores desde SQL/MongoDB
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:21:3. Actualizar ~50 llamadas a `db.servers.find_one` para aplicar descifrado
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:30:| `comercial/repository.py` | `get_server_by_id` | MongoDB fallback | ALTO | Agregar `_decrypt_server_password` | ✅ Corregido |
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:31:| `comercial/repository.py` | `get_servers_operaciones` | MongoDB fallback | ALTO | Agregar descifrado en lista | ✅ Corregido |
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:32:| `compras/repository.py` | `get_server_by_id` | MongoDB directo | ALTO | Agregar `_decrypt_server_password` | ✅ Corregido |
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:33:| `finanzas/repository_real.py` | `_get_server` | MongoDB directo | ALTO | Agregar descifrado | ✅ Corregido |
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:34:| `finanzas/propinas_tpv/sql_repository.py` | `get_edarsa_hub_server` | MongoDB directo | ALTO | Agregar descifrado | ✅ Corregido |
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:35:| `server.py` | ~50 endpoints | `db.servers.find_one` | ALTO | Envolver con `decrypt_server_secrets()` | ✅ Corregido |
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:46:    Descifra el password de un servidor obtenido de MongoDB.
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:69:    Descifra los secretos de un servidor obtenido de MongoDB/SQL.
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:85:- `get_server_by_id()`: MongoDB fallback ahora usa `_decrypt_server_password()`
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:86:- `get_servers_operaciones()`: Lista de MongoDB ahora descifra cada servidor
/app/docs/FASE_3C1_LEGACY_SECRET_ADOPTION.md:106:- ~48 llamadas a `db.servers.find_one` ahora envueltas con `decrypt_server_secrets()`
/app/docs/FASE8_PROPUESTA.md:142:2. Opcional: db.sec_roles.deleteOne({codigo: "VISOR_ADMIN"})
/app/docs/FASE8_PROPUESTA.md:323:### 9.3 Colecciones MongoDB
/app/docs/FASE8_PROPUESTA.md:407:   db.sec_roles.deleteOne({codigo: "VISOR_ADMIN"})
/app/docs/FASE8_PROPUESTA.md:408:   db.users.updateMany({}, {$pull: {sec_roles: "VISOR_ADMIN"}})
/app/docs/DICTAMEN_FINAL_PROPINAS_TPV_SIMULADO.md:312:║   ✅ Cache MongoDB configurado (cache_manager.py)                             ║
/app/docs/DICTAMEN_FINAL_PROPINAS_TPV_SIMULADO.md:370:║   • La colección `servers` en MongoDB está vacía en este entorno.             ║
/app/docs/DICTAMEN_FINAL_PROPINAS_TPV_SIMULADO.md:473:| `/app/backend/modules/finanzas/propinas_tpv/cache_manager.py` | Cache MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:78:| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:91:| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:104:| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:117:| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:130:| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:143:| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:156:| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:169:| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:182:| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:195:| **Bypass actual** | `server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:234:| `save_server_query()` | 1615 | Categoría C - escribe en MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:236:| `delete_server_query()` | 1722 | Categoría C - modifica MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:250:| `guardar_script_pendiente()` | 10941 | Escribe en MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:260:    server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:277:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:280:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE4_PLAN.md:347:5. **No hay escrituras a MongoDB** — Todos son endpoints de solo lectura SQL
/app/docs/sql/CORRECCION_SISTEMA_MENUS_Y_FALLBACKS.sql:4:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/sql/VALIDACION_SERVIDORES_EDARSAHUB.sql:121:-- 7. VERIFICAR CONSISTENCIA DE mongodb_id
/app/docs/sql/VALIDACION_SERVIDORES_EDARSAHUB.sql:124:PRINT '=== VERIFICACIÓN DE mongodb_id ===';
/app/docs/sql/VALIDACION_SERVIDORES_EDARSAHUB.sql:128:    SUM(CASE WHEN mongodb_id IS NOT NULL AND mongodb_id = CAST(id AS VARCHAR(50)) THEN 1 ELSE 0 END) AS id_coincide_mongodb_id,
/app/docs/sql/VALIDACION_SERVIDORES_EDARSAHUB.sql:129:    SUM(CASE WHEN mongodb_id IS NULL OR mongodb_id = '' THEN 1 ELSE 0 END) AS sin_mongodb_id,
/app/docs/sql/VALIDACION_SERVIDORES_EDARSAHUB.sql:130:    SUM(CASE WHEN mongodb_id IS NOT NULL AND mongodb_id != CAST(id AS VARCHAR(50)) THEN 1 ELSE 0 END) AS id_diferente_mongodb_id
/app/docs/sql/CORRECCION_PROYECCION_Y_MONEDA_FINAL.sql:4:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/sql/SYNC_LOGS_TABLA_AUDITORIA.sql:4:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/sql/AUDITORIA_CRUZADA_SERIES_VS_HUB.sql:9:IF OBJECT_ID('tempdb..#Series_Locales') IS NOT NULL DROP TABLE #Series_Locales;
/app/docs/sql/RECONCILIACION_SERIACION_KPI_VENTAS_MAYO2026.sql:10:IF OBJECT_ID('tempdb..#BD_Fuentes_Sitio') IS NOT NULL DROP TABLE #BD_Fuentes_Sitio;
/app/docs/sql/INTEGRADOR_PANEL_COMERCIAL_EDARSAHUB.sql:176:    PRINT 'Aplicando Ajuste 6: Inicialización del motor de Metas y KPI Presupuestales...';
/app/docs/sql/PROYECCION_ANUAL_MIGRACION_PROD.sql:3:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/sql/SYNC_LOGS_Y_MENUS_CONSOLIDADO.sql:4:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/sql/PROYECCION_ANUAL_MIGRACION_PEGA.sql:4:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/sql/REFRESH_VISTAS_TABLERO_COMERCIAL.sql:4:-- MOTOR: Microsoft SQL Server 2019+ (Directo Puerto 1433 - Base de datos EDARSAHUB)
/app/docs/sql/ACTUALIZACION_KPI_PROYECCION_COMERCIAL.sql:4:-- MOTOR: Microsoft SQL Server 2019+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/sql/ARQUITECTURA_FECHA_OPERATIVA_TURNO_BASE.sql:3:-- ENTIDAD: EDARSA HUB MULTI-UNIDAD (MOTOR: SQL SERVER)
/app/docs/sql/SINCRONIZACION_COMPLETA_5_UNIDADES.sql:11:-- 2. Limpiar vistas materializadas (según tu motor de BD)
/app/docs/sql/AUDITORIA_VERACIDAD_HISTORICA_VENTAS_CHEQUES.sql:14:IF OBJECT_ID('tempdb..#Sistemas_Software_Fuente') IS NOT NULL 
/app/docs/sql/SYNC_RESPONSE_CACHE_FINOPS.sql:4:-- MOTOR: Microsoft SQL Server 2019+ (Directo Puerto 1433 - Base de datos EDARSAHUB)
/app/docs/sql/INFRAESTRUCTURA_RESPALDO_CACHE_EDARSAHUB.sql:3:-- PROYECTO: EDARSA HUB ERP - MOTOR RESILIENTE Y ALTA DISPONIBILIDAD (EDGE OFFLINE CACHE)
/app/docs/sql/INFRAESTRUCTURA_RESPALDO_CACHE_EDARSAHUB.sql:4:-- MOTOR: Microsoft SQL Server 2019+ (Directo Puerto 1433 - Base de datos EDARSAHUB)
/app/docs/sql/FORZADO_SINCRONIZACION_HISTORICA_DIAGNOSTICO.sql:17:    IF OBJECT_ID('tempdb..#Data_Fuente_Auditada') IS NOT NULL DROP TABLE #Data_Fuente_Auditada;
/app/docs/sql/FORZADO_SINCRONIZACION_HISTORICA_DIAGNOSTICO.sql:90:IF OBJECT_ID('tempdb..#Data_Fuente_Auditada') IS NOT NULL DROP TABLE #Data_Fuente_Auditada;
/app/docs/sql/INTEGRACION_UNIDADES_SIN_DUPLICAR.sql:4:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/sql/MIGRACION_PROVEEDORES_MONGO_A_SQL.sql:2:-- SCRIPT: CREACIÓN TABLA PROVEEDORES CENTRAL + MIGRACIÓN MONGO → SQL
/app/docs/sql/MIGRACION_PROVEEDORES_MONGO_A_SQL.sql:3:-- OBJETIVO: Establecer estructura SQL para proveedores y migrar datos de MongoDB
/app/docs/sql/MIGRACION_PROVEEDORES_MONGO_A_SQL.sql:15:-- 2. Script de Migración (Ejecutar desde tu backend tras leer de Mongo)
/app/docs/sql/MIGRACION_PROVEEDORES_MONGO_A_SQL.sql:16:-- Nota: La lógica de migración debe ser: Leer Mongo -> Transformar -> Insertar SQL
/app/docs/sql/MIGRACION_PROVEEDORES_MONGO_A_SQL.sql:19:    -- Estos valores provendrán de la lectura previa de db.portal_suppliers
/app/docs/sql/RECONFIGURACION_JOB_BARRIDO_AUDITORIA_D10.sql:24:    IF OBJECT_ID('tempdb..#Barrido_Fuente_Tickets') IS NOT NULL DROP TABLE #Barrido_Fuente_Tickets;
/app/docs/sql/RECONFIGURACION_JOB_BARRIDO_AUDITORIA_D10.sql:107:IF OBJECT_ID('tempdb..#Barrido_Fuente_Tickets') IS NOT NULL DROP TABLE #Barrido_Fuente_Tickets;
/app/docs/sql/REGISTRO_MODULO_SATELITE_COMEDERO.sql:9:ON CONFLICT (id_modulo) DO NOTHING; -- O tu equivalente según el motor de BD
/app/docs/AUDITORIA_TABLEROS_KPIS_FILTROS_INVENTARIO.md:66:| **Fuente de Datos** | SoftRestaurant / ManagementPro vía SQL Server + MongoDB cache |
/app/docs/AUTH_HTTPONLY_COOKIE_MIGRATION_PLAN.md:90:- MongoDB como fuente de datos
/app/docs/AUTH_HTTPONLY_COOKIE_MIGRATION_PLAN.md:235:    user = await db.users.find_one({"email": payload['email']}, {"_id": 0})
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE5_REPORT.md:14:**5 de 5 endpoints migrados exitosamente** de `db.servers.find()` / `db.servers.find_one()` a `server_registry.list_servers()` / `server_registry.get_server_connection_info()`.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE5_REPORT.md:40:| Bypass | `db.servers.find({"id": {"$in": server_ids}}, ...)` | `list_servers(db=db, prefer_sql=True)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE5_REPORT.md:48:| Bypass | `db.servers.find({"id": {"$in": server_ids}}, ...)` | `list_servers(db=db, prefer_sql=True)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE5_REPORT.md:55:| Bypass | `db.servers.find({"active": True, "queries_configured": True}, ...)` | `list_servers(db=db, prefer_sql=True)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE5_REPORT.md:62:| Bypass | `db.servers.find_one({"id": server_id, "active": True})` | `get_server_connection_info(server_id, db=db)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE5_REPORT.md:70:| Bypass | `db.servers.find_one({"id": server_id, "active": True})` | `get_server_connection_info(server_id, db=db)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE5_REPORT.md:85:| 5 | `POST /api/catalogo/ejecutar-custom/{id}` | ⚠️ NOT TESTED | Requiere consulta preexistente en MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE5_REPORT.md:142:| MongoDB no es fuente maestra en estos 5 puntos | ✅ Confirmado |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE5_REPORT.md:217:| MongoDB no es fuente maestra en los 5 puntos | ✅ |
/app/docs/AUDITORIA_RH_NOMINAS_01.md:16:Se modificó `/app/backend/modules/rh/repository.py` para usar conexión directa a EDARSAHUB vía `EDARSAHUB_CONFIG` (variables de entorno), eliminando la dependencia incorrecta de MongoDB `servers` con `active=True`.
/app/docs/AUDITORIA_RH_NOMINAS_01.md:40:| `/api/nomina/ciclos` | 200 | 0 | MongoDB | ✅ OK | Colección vacía |
/app/docs/AUDITORIA_RH_NOMINAS_01.md:104:| Nóminas | Ciclos Nómina | Lista ciclos | — | `/nomina/ciclos` | 0 ciclos | MongoDB | ⚠️ SIN DATOS REAL | Colección vacía |
/app/docs/AUDITORIA_RH_NOMINAS_01.md:150:## Colecciones MongoDB
/app/docs/AUDITORIA_RH_NOMINAS_01.md:152:No existen colecciones de RH/Nóminas en MongoDB. Todos los datos residen en EDARSA HUB (SQL Server):
/app/docs/FASE_ASIGNACIONES_PROPUESTA.md:179:   empresa = db.empresas.find_one({"id": "emp-uuid-..."})
/app/docs/FASE_ASIGNACIONES_PROPUESTA.md:204:   config = db.config_asignaciones.find_one({
/app/docs/FASE_ASIGNACIONES_PROPUESTA.md:285:    empresa = await db.empresas.find_one({"id": unidad_negocio_id})
/app/docs/FASE_ASIGNACIONES_PROPUESTA.md:289:    server = await db.servers.find_one({"id": empresa["server_id"]})
/app/docs/FASE_ASIGNACIONES_PROPUESTA.md:755:- **Colección MongoDB**: `config_asignaciones` (índice único: unidad_negocio_id + almacen_id)
/app/docs/FASE3_PILOTO_FUNCIONAL_PROPUESTA.md:436:        await db.sec_bitacora_acceso.insert_one({
/app/docs/FASE3_PILOTO_FUNCIONAL_PROPUESTA.md:536:  db.sec_bitacora_acceso.deleteMany({fase: "FASE_3"})
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:10:La FASE 3B implementó el **Server Registry Central** que convierte EDARSAHUB SQL en la fuente primaria de configuración de servidores, dejando MongoDB como fallback legacy temporal.
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:12:**Hallazgo clave:** Los 9 servidores ya estaban sincronizados entre MongoDB y SQL mediante el campo `mongodb_id`. No se requirió migración de datos.
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:18:### Tabla de Mapeo MongoDB ↔ SQL
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:20:| MongoDB ID | SQL ID | Nombre | system_type | Sync Status |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:33:**Total MongoDB:** 9 servidores  
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:42:| Fuente primaria | MongoDB | EDARSAHUB SQL |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:43:| Fuente fallback | N/A | MongoDB (legacy) |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:44:| Endpoint `/api/servers` | Leía MongoDB | Lee SQL via registry |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:47:| Campo `config_origin` | No existía | `EDARSAHUB_SQL` o `MONGODB_LEGACY` |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:90:| mongodb_id | varchar | UUID original de MongoDB |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:104:| `get_server_by_id(server_id, db, prefer_sql, allow_mongo_fallback, mask_secrets)` | Obtiene un servidor por ID |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:105:| `list_servers(db, user, prefer_sql, allow_mongo_fallback, ...)` | Lista servidores con filtros |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:106:| `get_server_sucursales(server_id, db, prefer_sql, allow_mongo_fallback)` | Obtiene sucursales de un servidor |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:128:**Antes:** Leía directamente de MongoDB  
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:129:**Ahora:** Usa `server_registry.list_servers()` con SQL primero, fallback a MongoDB
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:133:- `config_origin`: Fuente de la configuración (EDARSAHUB_SQL o MONGODB_LEGACY)
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:140:**Antes:** Leía directamente de MongoDB  
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:141:**Ahora:** Usa `server_registry.get_server_by_id()` con SQL primero, fallback a MongoDB
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:145:## 8. Fallback MongoDB
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:147:El fallback a MongoDB se activa automáticamente cuando:
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:155:- `[SERVER_REGISTRY][MONGODB_FALLBACK_USED]`: Se usó MongoDB como fallback
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:160:  "config_origin": "MONGODB_LEGACY",
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:161:  "warnings": ["Servidor obtenido desde MongoDB legacy; migrar a EDARSAHUB SQL."]
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:224:| Módulos que aún leen MongoDB directamente | MEDIO | Migrar gradualmente usando registry |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:225:| Escritura a MongoDB aún activa | BAJO | POST/PUT/DELETE aún escriben a MongoDB; sincronizar manualmente |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:232:1. **Migrar endpoints de escritura** (POST, PUT, DELETE) para sincronizar SQL + MongoDB
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:233:2. **Migrar otros módulos** para usar `server_registry` en lugar de MongoDB directo
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:234:3. **Crear script de sincronización bidireccional** MongoDB ↔ SQL
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:243:| `USE_SQL_FOR_SERVERS` | `true` | Si es `false`, usa MongoDB directamente (rollback rápido) |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:254:## FASE 3B.1 — Escritura SQL-first y sincronización legacy MongoDB
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:265:| POST /api/servers | Solo MongoDB | SQL primero, sync MongoDB |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:266:| PUT /api/servers/{id} | Solo MongoDB | SQL primero, sync MongoDB |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:267:| DELETE /api/servers/{id} | Solo MongoDB | SQL primero, sync MongoDB |
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:271:- `create_server()` - Crea en SQL, sincroniza a MongoDB
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:272:- `update_server()` - Actualiza en SQL, sincroniza a MongoDB
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:273:- `delete_server()` - Soft delete en SQL, sincroniza a MongoDB
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:274:- `sync_server_to_mongo()` - Sincroniza servidor específico
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:279:- `SYNCED`: SQL + MongoDB actualizados
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:280:- `PARTIAL_SYNC`: SQL OK, MongoDB falló
/app/docs/FASE_3B_MIGRACION_SERVERS_EDARSAHUB.md:281:- `SQL_ERROR`: SQL falló, MongoDB no se tocó
/app/docs/FASE13_EVIDENCIA.md:55:| MongoDB `sec_perfiles` | Colección nueva con 5 perfiles |
/app/docs/FASE13_EVIDENCIA.md:56:| MongoDB `users` | +campo `sec_perfil` |
/app/docs/FASE13_EVIDENCIA.md:160:# 5. Opcional: Limpiar sec_perfil de usuarios en MongoDB
/app/docs/FASE6_MULTIPLES_ROLES_PROPUESTA.md:127:            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
/app/docs/FASE6_MULTIPLES_ROLES_PROPUESTA.md:134:        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
/app/docs/FASE6_MULTIPLES_ROLES_PROPUESTA.md:167:    await db.users.update_one(
/app/docs/FASE6_MULTIPLES_ROLES_PROPUESTA.md:216:3. Opcional: db.users.updateMany({}, {$unset: {sec_roles: 1}})
/app/docs/FASE6_MULTIPLES_ROLES_PROPUESTA.md:294:db.sec_roles.insertOne({
/app/docs/FASE6_MULTIPLES_ROLES_PROPUESTA.md:324:            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
/app/docs/FASE6_MULTIPLES_ROLES_PROPUESTA.md:331:        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
/app/docs/FASE6_MULTIPLES_ROLES_PROPUESTA.md:452:3. Opcional: db.sec_roles.deleteOne({codigo: "VISOR_SISTEMA"})
/app/docs/FASE6_MULTIPLES_ROLES_PROPUESTA.md:453:4. Opcional: db.users.updateMany({}, {$unset: {sec_roles: 1}})
/app/docs/CIERRE_Y_BLINDAJE_TABLERO_EJECUTIVO.md:177:CACHE_COLLECTION = "kpis_cache"
/app/docs/CIERRE_Y_BLINDAJE_TABLERO_EJECUTIVO.md:266:| `/app/backend/core/db.py` | Conexiones SQL | 🔴 CRÍTICO |
/app/docs/RH_NOMINAS_EDARSAHUB_CONNECTION_01_REPORT.md:12:Se corrigió la falla de arquitectura que bloqueaba el módulo RH/Nóminas. El módulo ahora usa conexión directa a EDARSAHUB vía variables de entorno (`EDARSAHUB_CONFIG`), eliminando la dependencia incorrecta del catálogo MongoDB `servers` con `active=True`.
/app/docs/RH_NOMINAS_EDARSAHUB_CONNECTION_01_REPORT.md:18:El módulo RH usaba `get_edarsa_hub_server()` que buscaba en MongoDB `servers` con filtro `active=True`. El servidor "EDARSA HUB" tenía `active=False`, bloqueando todos los endpoints.
/app/docs/RH_NOMINAS_EDARSAHUB_CONNECTION_01_REPORT.md:118:| `/api/nomina/ciclos` | 200 | 0 | ✅ OK (MongoDB vacío) |
/app/docs/RH_NOMINAS_EDARSAHUB_CONNECTION_01_REPORT.md:174:Y activar el servidor "EDARSA HUB" en MongoDB `servers` con `active=True`.
/app/docs/RH_NOMINAS_EDARSAHUB_CONNECTION_01_REPORT.md:184:| RH no depende de MongoDB servers | ✅ Corregido |
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_A.md:143:        Inicializa el core con conexión a MongoDB.
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_A.md:146:            db: Conexión a MongoDB (para obtener config de servidores)
/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_A.md:1156:**Entregable**: Motor de procesamiento completo.
/app/docs/CODE_QUALITY_STABILIZATION_AUDIT.md:239:- [x] MongoDB no reemplaza SQL
/app/docs/SISTEMA_RBAC_PROPUESTA.md:27:5. **SQL Server**: Toda persistencia en EDARSA HUB (MongoDB solo caché)
/app/docs/SISTEMA_RBAC_PROPUESTA.md:316:            -- Referencia a tabla users de MongoDB (sincronizado)
/app/docs/SISTEMA_RBAC_PROPUESTA.md:974:- [ ] Sincronizar usuarios de MongoDB → SQL Server
/app/docs/MANUALES_OPERATIVOS_CIENFUEGOS.md:37:## Colección MongoDB
/app/docs/MANUALES_OPERATIVOS_CIENFUEGOS.md:40:db.manuales_operativos
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:13:Este documento propone el **Lote 3** de migraciones de bypasses `db.servers.find_one()` hacia `server_registry.get_server_connection_info()`.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:31:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:32:| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:53:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:54:| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:75:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:76:| **Dato tomado de MongoDB** | host, port, database, username, password, system_type, name |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:97:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:98:| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:119:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:120:| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:141:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:142:| **Dato tomado de MongoDB** | host, port, database, username, password, system_type, tipos_movimiento, categorias |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:152:| **ALERTA** | ⚠️ Lee campos adicionales `tipos_movimiento`, `categorias` de MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:164:| **Bypass actual** | `db.servers.find_one({"id": request.server_id, "active": True})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:165:| **Dato tomado de MongoDB** | Todo el documento del servidor |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:186:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:187:| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:208:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:209:| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:230:| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:231:| **Dato tomado de MongoDB** | host, port, database, username, password |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:250:4. **Dependencias:** Evitar funciones que lean campos adicionales de MongoDB (como `tipos_movimiento`)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_LOTE3_PLAN.md:297:2. **generar_analisis_inventario (C6):** ⚠️ Lee campos adicionales `tipos_movimiento`, `categorias` de MongoDB - Requiere análisis
/app/docs/AUDITORIA_SEGURIDAD_RBAC.md:284:db.users.updateOne(
/app/docs/AUDITORIA_SEGURIDAD_RBAC.md:366:- [ ] Mes/año anterior: MongoDB consolidado
/app/docs/AUDITORIA_SEGURIDAD_RBAC.md:373:- [ ] Migrar endpoints de históricos a leer de MongoDB
/app/docs/AUDITORIA_SEGURIDAD_RBAC.md:378:- [ ] Migrar KPIs de dashboard a MongoDB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE6_REPORT.md:14:**1 de 1 endpoint migrado exitosamente** de `db.servers.find_one()` a `server_registry.get_server_connection_info()`.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE6_REPORT.md:22:| **C — MongoDB documento operativo** | ✅ OK | Script pendiente se guarda en MongoDB sin credenciales |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE6_REPORT.md:40:| Bypass | `server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))` | `conn_info = await get_server_connection_info(server_id, db=db)` |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE6_REPORT.md:49:server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE6_REPORT.md:64:## 4. CONFIRMACIÓN DE DOCUMENTO OPERATIVO EN MONGODB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE6_REPORT.md:95:**✅ CONFIRMADO: El documento MongoDB NO contiene credenciales.**
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE6_REPORT.md:220:3. **Sincronización previa** MongoDB → EDARSAHUB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE6_REPORT.md:273:| MongoDB solo como documento operativo | ✅ |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE6_REPORT.md:274:| No se guardan credenciales en MongoDB | ✅ |
/app/docs/FASE_3D_VALIDACION_CONECTIVIDAD_SECRETOS_CIFRADOS.md:208:Los endpoints de inventarios usan mongodb_id legacy. Validación estructural confirma que el código usa `decrypt_server_secrets()` para conexiones SQL.
/app/docs/FASE_3D_VALIDACION_CONECTIVIDAD_SECRETOS_CIFRADOS.md:253:| Módulos legacy usando mongodb_id | Migración gradual a SQL id en curso |
/app/docs/CENTRO_CONTROL_EDARSA.md:55:- MongoDB (EDARSA HUB)
/app/docs/CENTRO_CONTROL_EDARSA.md:184:| MongoDB no responde | CRITICAL | "Fuente caída: MongoDB" |
/app/docs/CENTRO_CONTROL_EDARSA.md:227:1. Verificar conexión a MongoDB
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:48:<a href="#MIGRACION_PROVEEDORES_MONGO_A_SQL">MIGRACION_PROVEEDORES_MONGO_A_SQL.sql</a>
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:85:-- MOTOR: Microsoft SQL Server 2019+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:263:-- ENTIDAD: EDARSA HUB MULTI-UNIDAD (MOTOR: SQL SERVER)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:382:IF OBJECT_ID('tempdb..#Series_Locales') IS NOT NULL DROP TABLE #Series_Locales;
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:498:IF OBJECT_ID('tempdb..#Sistemas_Software_Fuente') IS NOT NULL 
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:612:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:746:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:1430:    IF OBJECT_ID('tempdb..#Data_Fuente_Auditada') IS NOT NULL DROP TABLE #Data_Fuente_Auditada;
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:1503:IF OBJECT_ID('tempdb..#Data_Fuente_Auditada') IS NOT NULL DROP TABLE #Data_Fuente_Auditada;
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:1509:-- PROYECTO: EDARSA HUB ERP - MOTOR RESILIENTE Y ALTA DISPONIBILIDAD (EDGE OFFLINE CACHE)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:1510:-- MOTOR: Microsoft SQL Server 2019+ (Directo Puerto 1433 - Base de datos EDARSAHUB)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:1610:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:1882:    PRINT 'Aplicando Ajuste 6: Inicialización del motor de Metas y KPI Presupuestales...';
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2003:<h2 id="MIGRACION_PROVEEDORES_MONGO_A_SQL">📄 MIGRACION_PROVEEDORES_MONGO_A_SQL.sql</h2>
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2006:-- SCRIPT: CREACIÓN TABLA PROVEEDORES CENTRAL + MIGRACIÓN MONGO → SQL
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2007:-- OBJETIVO: Establecer estructura SQL para proveedores y migrar datos de MongoDB
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2019:-- 2. Script de Migración (Ejecutar desde tu backend tras leer de Mongo)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2020:-- Nota: La lógica de migración debe ser: Leer Mongo -&gt; Transformar -&gt; Insertar SQL
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2023:    -- Estos valores provendrán de la lectura previa de db.portal_suppliers
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2055:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2199:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2345:IF OBJECT_ID('tempdb..#BD_Fuentes_Sitio') IS NOT NULL DROP TABLE #BD_Fuentes_Sitio;
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2473:    IF OBJECT_ID('tempdb..#Barrido_Fuente_Tickets') IS NOT NULL DROP TABLE #Barrido_Fuente_Tickets;
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2556:IF OBJECT_ID('tempdb..#Barrido_Fuente_Tickets') IS NOT NULL DROP TABLE #Barrido_Fuente_Tickets;
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2584:-- MOTOR: Microsoft SQL Server 2019+ (Directo Puerto 1433 - Base de datos EDARSAHUB)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:2730:ON CONFLICT (id_modulo) DO NOTHING; -- O tu equivalente según el motor de BD
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3000:-- 2. Limpiar vistas materializadas (según tu motor de BD)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3060:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3121:-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3232:-- MOTOR: Microsoft SQL Server 2019+ (Directo Puerto 1433 - Base de datos EDARSAHUB)
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3587:-- 7. VERIFICAR CONSISTENCIA DE mongodb_id
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3590:PRINT '=== VERIFICACIÓN DE mongodb_id ===';
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3594:    SUM(CASE WHEN mongodb_id IS NOT NULL AND mongodb_id = CAST(id AS VARCHAR(50)) THEN 1 ELSE 0 END) AS id_coincide_mongodb_id,
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3595:    SUM(CASE WHEN mongodb_id IS NULL OR mongodb_id = '' THEN 1 ELSE 0 END) AS sin_mongodb_id,
/app/docs/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3596:    SUM(CASE WHEN mongodb_id IS NOT NULL AND mongodb_id != CAST(id AS VARCHAR(50)) THEN 1 ELSE 0 END) AS id_diferente_mongodb_id
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:17:Tras ejecutar el diagnóstico comparativo entre EDARSAHUB y MongoDB:
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:22:| **MongoDB** | 0 | Colección vacía |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:27:2. **MongoDB no tiene servidores** — La colección `db.servers` está vacía (0 documentos)
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:41:## 2. COMPARATIVO MONGODB vs EDARSAHUB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:43:### 2.1 Servidores en MongoDB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:75:### 3.1 Servidores Solo en MongoDB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:76:**Ninguno** — MongoDB está vacío.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:82:**Ninguno** — No hay intersección porque MongoDB está vacío.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:119:3. No hay sincronización desde MongoDB porque MongoDB está vacío
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:122:**No aplica** — MongoDB `server_sucursales_config` está vacío (0 documentos).
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:143:| Campo | Valor en EDARSAHUB | Valor en MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:146:| mongodb_id | a5547321-1139-4d2b-9d53-182ca737b6b6 | *(no existe)* |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:161:| Campo | Valor en EDARSAHUB | Valor en MongoDB |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:164:| mongodb_id | b5175237-5e57-41f3-ab6d-b5ae2f5e780b | *(no existe)* |
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:221:    mongodb_id               nvarchar(100)    NULL
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:236:1. MongoDB está vacío
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:240:**No hay datos que migrar de MongoDB a EDARSAHUB.**
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:255:Dado que MongoDB está vacío y EDARSAHUB ya contiene todos los servidores, **no hay script SQL necesario** para sincronizar datos.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:321:No hay datos en MongoDB que necesiten ser migrados o confirmados.
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:345:### 9.2 Verificación de Fallback MongoDB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:347:El fallback a MongoDB **no debe activarse** en operación normal porque:
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:350:3. MongoDB está vacío
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:357:3. NO usar fallback a MongoDB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:379:- MongoDB está vacío, no hay datos legacy que migrar
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:393:### Opción C: SINCRONIZAR MONGODB COMO CACHE
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:396:Si se desea usar MongoDB como cache/backup de EDARSAHUB:
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:398:1. Ejecutar `reconcile_sql_mongo_servers(db, dry_run=False)` desde `server_registry.py`
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:399:2. Esto copiará los 13 servidores de EDARSAHUB a MongoDB
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:414:# Rollback: Vaciar MongoDB y dejar EDARSAHUB como única fuente
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:415:await db.servers.delete_many({})
/app/docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_D_CATALOGO_SERVIDORES_PLAN.md:427:| MongoDB fallback NO se usa | ✅ Confirmado (MongoDB vacío) |
/app/docs/FASE5_EVIDENCIA.md:215:3. Opcional: db.sec_roles.drop()
/app/docs/FASE5_EVIDENCIA.md:216:4. Opcional: db.users.updateMany({}, {$unset: {sec_rol: 1}})
/app/docs/FASE9_PROPUESTA.md:315:from motor.motor_asyncio import AsyncIOMotorClient
/app/docs/FASE9_PROPUESTA.md:318:# Conexión a MongoDB
/app/docs/FASE9_PROPUESTA.md:319:client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
/app/docs/FASE9_PROPUESTA.md:338:            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
/app/docs/FASE9_PROPUESTA.md:345:        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
/app/docs/FASE3_EVIDENCIA.md:99:db.users.updateOne(
/app/docs/CIERRE_Y_BLINDAJE_AUDITORIA_COMPRAS.md:91:| MongoDB | NoSQL | Local | Auditorías, workflows |
```

## Archivos package/requirements

```text
```
