# Auditoría runtime Mongo backend
Fecha: 20260623_013735

## 1. Git status
```
?? docs/reports/MONGO_RUNTIME_BACKEND_AUDIT_20260623_013735.md
```

## 2. Referencias runtime Mongo reales
```
backend/tests_guardrails/test_p5_auth_no_mongo_fallback.py:15:    if "pymongo" in txt or "mongoclient" in txt or "users.find" in txt:
backend/tests_guardrails/test_p5_auth_no_mongo_fallback.py:22:print("PASS Auth repository sin MongoDB")
backend/tests_guardrails/test_p2_10_repository_layer.py:26:    if "mongodb://" in txt or "MONGO_URL" in txt or "import pymongo" in txt:
backend/tests_guardrails/test_p5_1_no_mongo_residual_modules.py:4:  1) imports vivos de Mongo: `import pymongo`, `from pymongo`, `import motor`,
backend/tests_guardrails/test_p5_1_no_mongo_residual_modules.py:5:     `from motor`, `MongoClient`, `AsyncIOMotorClient`.
backend/tests_guardrails/test_p5_1_no_mongo_residual_modules.py:27:    re.compile(r"^\s*import\s+pymongo\b", re.M),
backend/tests_guardrails/test_p5_1_no_mongo_residual_modules.py:28:    re.compile(r"^\s*from\s+pymongo\b", re.M),
backend/tests_guardrails/test_p5_1_no_mongo_residual_modules.py:32:    re.compile(r"\bAsyncIOMotorClient\s*\(", re.M),
backend/tests_guardrails/test_p2_07_runtime.py:19:        mongo += txt.count("mongodb://")
backend/tests_guardrails/test_p2_sql_first_runtime_activo.py:13:forbidden = ["from pymongo import MongoClient", "import pymongo"]
backend/limpiar_tests_dns.py:37:        f.write("- Eliminación definitiva de dependencias MongoDB.\n")
backend/db/migrations/create_comercial_kpis_historico.sql:12:-- MongoDB queda solo como checkpoint/log/cache/staging temporal.
backend/db/migrations/create_comercial_kpis_historico.sql:15:-- EDARSAHUB SQL es el cerebro. MongoDB NO es destino final.
backend/modules/sync_monitor/service.py:11:NO usa MongoDB.
backend/modules/sync_monitor/routes.py:25:    NO usa MongoDB.
backend/modules/comercial/service.py:82:# NO consulta servidores locales ni MongoDB para KPIs.
backend/modules/comercial/service.py:104:# NO usar MongoDB como fuente funcional para unidades.
backend/modules/comercial/service.py:113:    NO usa MongoDB.
backend/modules/comercial/service.py:191:    NO usa MongoDB.
backend/modules/comercial/service.py:212:    # Si no se encuentra, retornar estructura vacía (no usar MongoDB)
backend/modules/comercial/service.py:488:    NO usa MongoDB. NO usa servidores locales.
backend/modules/comercial/service.py:818:    - NO consulta MongoDB
backend/modules/comercial/service.py:1198:    - NO usa MongoDB servers.name como nombre oficial
backend/modules/comercial/service.py:1210:    # NO usar MongoDB servers.name como nombre funcional/oficial
backend/modules/comercial/service.py:1379:# - NO consultan MongoDB como fuente de datos
backend/modules/comercial/service.py:1390:    - NO consulta MongoDB
backend/modules/comercial/service.py:1394:    - NO usa MongoDB servers.name como nombre oficial
backend/modules/comercial/service.py:1407:    # NO usar MongoDB servers.name como nombre oficial
backend/modules/comercial/service.py:1520:    - NO consulta MongoDB
backend/modules/comercial/service.py:2392:    NO consulta: MongoDB
backend/modules/comercial/routes_pricing_ai.py:19:- NO usar MongoDB
backend/modules/comercial/routes_pricing_ai.py:413:            "mongodb": False,
backend/modules/comercial/routes_pricing_ai.py:449:    - NO usa MongoDB
backend/modules/comercial/cache_service.py:35:# Referencia global a MongoDB (evita circular import con server.py)
backend/modules/comercial/cache_service.py:40:    DEPRECADO: MongoDB ya no se usa.
backend/modules/comercial/cache_service.py:46:    logging.warning("[COMERCIAL] Cache service - MongoDB deprecado, funcionalidad limitada")
backend/modules/comercial/cache_service.py:50:    DEPRECADO: MongoDB ya no se usa.
backend/modules/comercial/cache_service.py:56:        logging.debug("[COMERCIAL] get_db() - MongoDB deprecado")
backend/modules/comercial/cache_service.py:139:        cached = await db.comercial_cache.find_one({"cache_key": cache_key})
backend/modules/comercial/cache_service.py:207:        await db.comercial_cache.update_one(
backend/modules/comercial/cache_service.py:349:        await db.comercial_cache.create_index("cache_key", unique=True)
backend/modules/comercial/cache_service.py:350:        await db.comercial_cache.create_index("cached_at")
backend/modules/comercial/cache_service.py:373:        total_before = await db.comercial_cache.count_documents({})
backend/modules/comercial/cache_service.py:376:        result = await db.comercial_cache.delete_many({
backend/modules/comercial/cache_service.py:381:        result2 = await db.comercial_cache.delete_many({
backend/modules/comercial/cache_service.py:386:        total_after = await db.comercial_cache.count_documents({})
backend/modules/comercial/cache_service.py:421:        total_entries = await db.comercial_cache.count_documents({})
backend/modules/comercial/cache_service.py:429:        async for doc in db.comercial_cache.aggregate(pipeline):
backend/modules/comercial/cache_service.py:433:        oldest = await db.comercial_cache.find_one(sort=[("cached_at", 1)])
backend/modules/comercial/cache_service.py:434:        newest = await db.comercial_cache.find_one(sort=[("cached_at", -1)])
backend/modules/comercial/__init__.py:14:- repository.py: Queries SQL y acceso a MongoDB
backend/modules/comercial/__init__.py:55:    Inicializa el módulo comercial con la conexión a MongoDB.
backend/modules/comercial/queries/hub.py:4:EDARSA HUB - Lecturas desde EDARSA HUB (MongoDB)
backend/modules/comercial/queries/hub.py:11:COLECCIONES MONGODB:
backend/modules/comercial/queries/hub.py:168:    Construye filtro MongoDB para consultas de KPIs.
backend/modules/comercial/queries/hub.py:178:        Dict filtro para MongoDB find()
backend/modules/comercial/routes_precios_sugeridos.py:13:- CERO MongoDB
backend/modules/comercial/inteligencia_comercial_routes.py:11:- No usa MongoDB como fuente de datos comerciales.
backend/modules/comercial/alertas_margen_service.py:6:EDARSAHUB SQL es el cerebro. CERO MongoDB.
backend/modules/comercial/alertas_margen_repository.py:6:EDARSAHUB SQL es el cerebro. CERO MongoDB.
backend/modules/comercial/routes_listas_competidores.py:10:- CERO MongoDB
backend/modules/comercial/routes_alertas_margen.py:6:EDARSAHUB SQL es el cerebro. CERO MongoDB.
backend/modules/comercial/repository.py:9:- ELIMINADA dependencia de MongoDB completamente
backend/modules/comercial/repository.py:55:# DEPRECADO: MongoDB ya no se usa (Mayo 2026)
backend/modules/comercial/repository.py:59:    """DEPRECADO: MongoDB eliminado. No hace nada."""
backend/modules/comercial/repository.py:64:    """DEPRECADO: MongoDB eliminado. Retorna None siempre."""
backend/modules/comercial/repository.py:92:    Garantiza paridad estructural con el esquema original de MongoDB.
backend/modules/comercial/repository.py:167:        WHERE (id = '{safe_id}' OR mongodb_id = '{safe_id}')
backend/modules/comercial/repository.py:219:    MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.
backend/modules/comercial/repository.py:232:    MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.
backend/modules/comercial/repository.py:341:    MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.
backend/modules/comercial/historical_kpis_repository.py:8:EDARSAHUB SQL es el cerebro. MongoDB NO es destino final de históricos.
backend/modules/comercial/historical_kpis_repository.py:444:# MIGRACIÓN DE STAGING MONGODB A SQL
backend/modules/comercial/kpis_repository.py:27:# INYECCIÓN DE DEPENDENCIA: MongoDB
backend/modules/comercial/kpis_repository.py:35:    DEPRECADO: MongoDB ya no se usa para KPIs.
backend/modules/comercial/kpis_repository.py:41:    logging.warning("[COMERCIAL] KPIs repository - MongoDB deprecado")
backend/modules/comercial/kpis_repository.py:46:    DEPRECADO: MongoDB ya no se usa.
backend/modules/comercial/kpis_repository.py:51:        logging.debug("[COMERCIAL] KPIs get_db() - MongoDB deprecado, retornando None")
backend/modules/comercial/kpis_repository.py:232:    No usa MongoDB.
backend/modules/comercial/services/listas_competidores_service.py:12:- CERO MongoDB
backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:15:- CERO MongoDB
backend/modules/comercial/services/pricing_ai_service.py:17:- NO usar MongoDB (todo en EDARSAHUB SQL)
backend/modules/comercial/services/metricas_ia_service.py:18:- NO usar MongoDB
backend/modules/comercial/routes.py:1177:                        # Para modo HUB, NO usar caché MongoDB como fallback.
backend/modules/comercial/routes.py:1179:                        # MongoDB NO debe ser fuente productiva de datos.
backend/modules/comercial/routes.py:1182:                            # HUB: Reportar error SQL, NO usar caché MongoDB
backend/modules/comercial/routes.py:1183:                            logging.warning(f"[HUB-EDARSAHUB-ERROR] {server['name']}: Error leyendo EDARSAHUB SQL - NO hay fallback MongoDB")
backend/modules/comercial/routes.py:1201:                            # LIVE-C: Mantener fallback a caché MongoDB (conexión real fallida)
backend/modules/comercial/routes.py:1690:    # FUENTE: EDARSAHUB.Unidades_Negocio (NO MongoDB)
backend/modules/comercial/routes.py:2974:    # ARQUITECTURA: Obtener nombre de unidad desde EDARSAHUB (primario) o MongoDB (LEGACY_FALLBACK)
backend/modules/comercial/routes.py:2977:        logging.warning(f"[LEGACY_FALLBACK] Mesas: Nombre de sucursal {sucursal} obtenido de MongoDB")
backend/modules/comercial/routes.py:3038:            # BLINDAJE: Usar nombre obtenido de MongoDB
backend/modules/comercial/routes.py:3149:            # BLINDAJE MPRO: Usar nombre de MongoDB (ya obtenido arriba), con fallback a SQL si no se encontró
backend/modules/comercial/routes.py:3151:            # Si MongoDB no encontró el nombre (aún es server['name']), intentar con SQL
backend/modules/fase2_operativo/sql_repository.py:7:Reemplazo completo de MongoDB para el módulo fase2_operativo.
backend/modules/fase2_operativo/db_utils.py:7:Proporciona acceso a la conexión de MongoDB para el módulo operativo.
backend/modules/fase2_operativo/db_utils.py:11:# Conexión síncrona a MongoDB para los repositories
backend/modules/fase2_operativo/db_utils.py:16:def get_database():
backend/modules/fase2_operativo/db_utils.py:18:    Obtiene la conexión a la base de datos MongoDB.
backend/modules/fase2_operativo/db_utils.py:22:        Database MongoDB
backend/modules/fase2_operativo/db_utils.py:27:        mongo_url = None  # P2-07: MongoDB eliminado
backend/modules/fase2_operativo/db_utils.py:30:        _client = None  # P2-07: MongoDB eliminado
backend/modules/fase2_operativo/repositories/__init__.py:8:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/base_repository.py:9:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/base_repository.py:14:- El parámetro 'db' (MongoDB) se ignora completamente
backend/modules/fase2_operativo/repositories/cargos_repository.py:8:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/cargos_repository.py:27:    Reemplaza acceso MongoDB por SQL Server EDARSAHUB.
backend/modules/fase2_operativo/repositories/cargos_repository.py:60:        # Mapeo de datos MongoDB → SQL
backend/modules/fase2_operativo/repositories/cargos_repository.py:167:        # Mapear campos MongoDB → SQL
backend/modules/fase2_operativo/repositories/cargos_repository.py:379:        Mapea campos SQL → formato MongoDB/API legacy.
backend/modules/fase2_operativo/repositories/cargos_repository.py:419:    Reemplaza acceso MongoDB por SQL Server EDARSAHUB.
backend/modules/fase2_operativo/repositories/configuracion_repository.py:8:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/configuracion_repository.py:19:    Migrado de MongoDB a SQL Server EDARSAHUB.
backend/modules/fase2_operativo/repositories/auditoria_programada_repository.py:8:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/auditoria_programada_repository.py:29:    Migrado de MongoDB a SQL Server EDARSAHUB.
backend/modules/fase2_operativo/repositories/auditoria_repository.py:8:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/auditoria_repository.py:19:    Migrado de MongoDB a SQL Server EDARSAHUB.
backend/modules/fase2_operativo/repositories/workflow_repository.py:9:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/workflow_repository.py:22:# Constante para ordenamiento descendente (reemplaza pymongo.DESCENDING)
backend/modules/fase2_operativo/repositories/workflow_repository.py:228:        No usa $inc de MongoDB, hace SELECT + UPDATE.
backend/modules/fase2_operativo/repositories/workflow_repository.py:260:        MIGRADO A SQL: Usa GROUP BY explícito en lugar de aggregate de MongoDB.
backend/modules/fase2_operativo/repositories/asignacion_repository.py:8:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/asignacion_repository.py:23:    Migrado de MongoDB a SQL Server EDARSAHUB.
backend/modules/fase2_operativo/repositories/justificacion_repository.py:8:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/justificacion_repository.py:19:    Migrado de MongoDB a SQL Server EDARSAHUB.
backend/modules/fase2_operativo/repositories/tarea_repository.py:9:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/tarea_repository.py:22:# Constantes para ordenamiento (reemplazan pymongo.ASCENDING/DESCENDING)
backend/modules/fase2_operativo/repositories/detalle_diferencias_repository.py:8:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/detalle_diferencias_repository.py:19:    Migrado de MongoDB a SQL Server EDARSAHUB.
backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:9:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/historial_responsabilidad_repository.py:8:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/historial_responsabilidad_repository.py:26:    Migrado de MongoDB a SQL Server EDARSAHUB.
backend/modules/fase2_operativo/repositories/historial_repository.py:8:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/historial_repository.py:19:    Migrado de MongoDB a SQL Server EDARSAHUB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:8:usando EDARSAHUB SQL Server en lugar de MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:12:- CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/sql_base_repository.py:31:# MAPEO COLECCIÓN MONGODB → TABLA SQL
backend/modules/fase2_operativo/repositories/sql_base_repository.py:66:# Mapeo de campos MongoDB → SQL para cada tabla
backend/modules/fase2_operativo/repositories/sql_base_repository.py:213:    Clase que simula el cursor de MongoDB con métodos encadenables.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:285:    - CERO MongoDB productivo
backend/modules/fase2_operativo/repositories/sql_base_repository.py:289:    - Reemplaza BaseRepository (MongoDB)
backend/modules/fase2_operativo/repositories/sql_base_repository.py:298:            collection_name: Nombre de la colección MongoDB (se mapea a tabla SQL)
backend/modules/fase2_operativo/repositories/sql_base_repository.py:336:        Mapea un campo MongoDB a su equivalente SQL.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:366:        Convierte una fila SQL a formato compatible con MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:372:        # Crear mapeo inverso SQL → MongoDB
backend/modules/fase2_operativo/repositories/sql_base_repository.py:405:        Construye cláusula WHERE desde filtros estilo MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:428:                # Operadores MongoDB
backend/modules/fase2_operativo/repositories/sql_base_repository.py:492:        Construye cláusula ORDER BY desde formato MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:739:    # MÉTODOS DE COMPATIBILIDAD MONGODB (Síncronos)
backend/modules/fase2_operativo/repositories/sql_base_repository.py:744:        Versión síncrona de get para compatibilidad con código MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:782:        Versión síncrona para compatibilidad con código MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:869:        Versión síncrona de create para compatibilidad con código MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:875:        Versión síncrona de update para compatibilidad con código MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:914:        Versión síncrona de count para compatibilidad con código MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:921:        Versión síncrona para compatibilidad con MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:947:        Versión síncrona para compatibilidad con MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:992:        Versión síncrona para compatibilidad con MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:1047:        Ejecuta una agregación estilo MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:1198:    Factory para obtener un repositorio SQL dado un nombre de colección MongoDB.
backend/modules/fase2_operativo/repositories/sql_base_repository.py:1201:        collection_name: Nombre de la colección MongoDB
backend/modules/fase2_operativo/repositories/sql_base_repository.py:1222:    - El parámetro 'db' (MongoDB) se ignora
backend/modules/fase2_operativo/repositories/sql_base_repository.py:1234:        # Ignoramos db (MongoDB) - Usamos SQL
backend/modules/fase2_operativo/repositories/sql_base_repository.py:1244:            f"(MongoDB db ignorado, usando EDARSAHUB SQL)"
backend/modules/fase2_operativo/repositories/sql_base_repository.py:1275:    # Delegación de métodos síncronos estilo MongoDB (compatibilidad con services
backend/modules/fase2_operativo/schemas/workflow_schemas.py:38:    id: str = Field(..., alias="_id", description="ID del documento MongoDB")
backend/modules/fase2_operativo/services/document_data_service.py:41:    - Operaciones de MongoDB pasan por StubDatabase sin fallar
backend/modules/fase2_operativo/services/document_data_service.py:49:            db: Instancia de la base de datos MongoDB
backend/modules/fase2_operativo/services/document_data_service.py:72:        FASE B-P2: SQL-only, sin fallback a MongoDB.
backend/modules/fase2_operativo/services/cargos_service.py:791:            # No consultamos MongoDB para usuarios/workflows - usamos datos ya disponibles
backend/modules/fase2_operativo/services/orquestador_service.py:9:Este servicio ahora usa SQL Server (EDARSAHUB) en lugar de MongoDB.
backend/modules/fase2_operativo/services/orquestador_service.py:48:    - Las operaciones de MongoDB fueron reemplazadas por sql_repository.py
backend/modules/fase2_operativo/services/orquestador_service.py:76:        MIGRADO A SQL SERVER - Ya no depende de MongoDB.
backend/modules/fase2_operativo/services/notification_service.py:34:    FASE B-P2: Migrado a SQL - usa repositorio SQL en lugar de MongoDB.
backend/modules/fase2_operativo/services/notification_service.py:40:        # FASE B-P2: Usar SQLBaseRepository en lugar de MongoDB collection
backend/modules/fase2_operativo/services/notification_service.py:422:            # FASE B-P2: Usar SQL repository en lugar de MongoDB
backend/modules/fase2_operativo/services/auditoria_programada_service.py:7:Usa PyMongo sync para compatibilidad con el módulo.
backend/modules/fase2_operativo/services/auditoria_programada_service.py:47:    - MongoDB pasa por StubDatabase
backend/modules/fase2_operativo/services/auditoria_programada_service.py:238:        """Crea workflow de inventario (sync - usa PyMongo directamente)."""
backend/modules/fase2_operativo/services/sla_service.py:10:Este servicio ahora usa SQL Server (EDARSAHUB) en lugar de MongoDB.
backend/modules/fase2_operativo/services/sla_service.py:75:    - Las operaciones de MongoDB fueron reemplazadas por sql_repository.py
backend/modules/fase2_operativo/services/auditoria_service.py:46:            db: Instancia de la base de datos MongoDB
backend/modules/fase2_operativo/services/configuracion_service.py:48:            db: Instancia de la base de datos MongoDB
backend/modules/fase2_operativo/services/operativo_service.py:52:            db: Instancia de la base de datos MongoDB
backend/modules/fase2_operativo/services/tarea_service.py:45:            db: Instancia de la base de datos MongoDB
backend/modules/fase2_operativo/services/workflow_service.py:74:            db: Instancia de la base de datos MongoDB
backend/modules/fase2_operativo/services/justificacion_service.py:54:            db: Instancia de la base de datos MongoDB
backend/modules/fase2_operativo/routes/sla_routes.py:22:from ..db_utils import get_database
backend/modules/fase2_operativo/routes/sla_routes.py:44:        db = get_database()
backend/modules/fase2_operativo/routes/sla_routes.py:78:        db = get_database()
backend/modules/fase2_operativo/routes/sla_routes.py:108:        db = get_database()
backend/modules/fase2_operativo/routes/sla_routes.py:141:        db = get_database()
backend/modules/fase2_operativo/routes/sla_routes.py:175:        db = get_database()
backend/modules/fase2_operativo/routes/sla_routes.py:208:        db = get_database()
backend/modules/fase2_operativo/routes/sla_routes.py:244:        db = get_database()
backend/modules/fase2_operativo/routes/sla_routes.py:248:        tarea = db.tareas_inventario.find_one({"id": tarea_id}, {"_id": 0})
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:20:from ..db_utils import get_database
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:113:    db_async = manager.db  # Conexión async de MongoDB
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:140:    from ..db_utils import get_database
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:142:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:145:    ultima = db.scheduler_job_logs.find_one(
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:182:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:190:    tareas = list(db.tareas_operativas_compras.find(
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:208:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:210:    tarea = db.tareas_operativas_compras.find_one(
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:233:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:237:    tarea = db.tareas_operativas_compras.find_one({"id": tarea_id})
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:246:    db.tareas_operativas_compras.update_one(
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:269:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:273:    tarea = db.tareas_operativas_compras.find_one({"id": tarea_id})
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:279:    db.tareas_operativas_compras.update_one(
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:304:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:319:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:339:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:341:    bitacora = list(db.auditoria_compras_bitacora.find(
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:365:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:373:    pedidos = list(db.pedidos_procesados_automatizacion.find(
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:395:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:415:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:452:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:456:    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:490:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:494:    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:526:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:529:    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:576:    db = get_database()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:605:    db = get_database()
backend/modules/fase2_operativo/routes/tarea_routes.py:27:from ..db_utils import get_database
backend/modules/fase2_operativo/routes/tarea_routes.py:37:    return get_database()
backend/modules/fase2_operativo/routes/configuracion_routes.py:18:from ..db_utils import get_database
backend/modules/fase2_operativo/routes/configuracion_routes.py:28:    return get_database()
backend/modules/fase2_operativo/routes/cargos_routes.py:52:from ..db_utils import get_database
backend/modules/fase2_operativo/routes/cargos_routes.py:63:    db = get_database()
backend/modules/fase2_operativo/routes/responsabilidad_routes.py:49:from ..db_utils import get_database
backend/modules/fase2_operativo/routes/responsabilidad_routes.py:59:    return get_database()
backend/modules/fase2_operativo/routes/notificaciones_routes.py:54:    SQL-First: fuente canónica EDARSAHUB.Operativo_Notificaciones_Log (sin MongoDB).
backend/modules/fase2_operativo/routes/notificaciones_routes.py:106:    (SQL-First). El almacén MongoDB fue deprecado; si no hay backend de datos
backend/modules/fase2_operativo/routes/notificaciones_routes.py:109:    from ..db_utils import get_database
backend/modules/fase2_operativo/routes/notificaciones_routes.py:110:    db = get_database()
backend/modules/fase2_operativo/routes/notificaciones_routes.py:143:    notificaciones_recientes = db.notificaciones_log.find(
backend/modules/fase2_operativo/routes/notificaciones_routes.py:162:    tareas_vencidas = list(db.tareas_inventario.find(filtro_tareas, {"_id": 0}).limit(50))
backend/modules/fase2_operativo/routes/notificaciones_routes.py:184:        usuario = db.users.find_one({"id": usuario_id}, {"_id": 0, "email": 1, "name": 1})
backend/modules/fase2_operativo/routes/justificacion_routes.py:21:from ..db_utils import get_database
backend/modules/fase2_operativo/routes/justificacion_routes.py:31:    return get_database()
backend/modules/fase2_operativo/routes/workflow_routes.py:30:from ..db_utils import get_database
backend/modules/fase2_operativo/routes/workflow_routes.py:40:    return get_database()
backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:28:from ..db_utils import get_database
backend/modules/fase2_operativo/routes/auditoria_programada_routes.py:38:    return get_database()
backend/modules/fase2_operativo/routes/documentos_routes.py:17:from ..db_utils import get_database
backend/modules/fase2_operativo/routes/documentos_routes.py:58:        db = get_database()
backend/modules/fase2_operativo/routes/documentos_routes.py:72:            db.documentos_generados.insert_one({
backend/modules/fase2_operativo/routes/documentos_routes.py:132:        db = get_database()
backend/modules/fase2_operativo/routes/documentos_routes.py:146:            db.documentos_generados.insert_one({
backend/modules/fase2_operativo/routes/documentos_routes.py:199:        db = get_database()
backend/modules/fase2_operativo/routes/documentos_routes.py:235:        db = get_database()
backend/modules/fase2_operativo/routes/auditoria_routes.py:20:from ..db_utils import get_database
backend/modules/fase2_operativo/routes/auditoria_routes.py:30:    return get_database()
backend/modules/fase2_operativo/routes/dashboard_routes.py:20:from ..db_utils import get_database
backend/modules/fase2_operativo/routes/dashboard_routes.py:32:    return get_database()
backend/modules/api_connections/__init__.py:11:- Caché/Fallback: MongoDB (colección api_connections)
backend/modules/api_connections/__init__.py:17:- Sincronización automática con MongoDB
backend/modules/api_connections/repository.py:8:- MongoDB: Solo caché/log/estado auxiliar (NO autoritativo)
backend/modules/api_connections/repository.py:9:- Sincronización: EDARSAHUB SQL → MongoDB (nunca al revés)
backend/modules/api_connections/repository.py:13:2. Si EDARSAHUB SQL falla, NO se guarda en MongoDB
backend/modules/api_connections/repository.py:14:3. Si MongoDB falla después de EDARSAHUB SQL, la operación es exitosa
backend/modules/api_connections/repository.py:36:# Referencia a MongoDB (solo para caché, NO autoritativo)
backend/modules/api_connections/repository.py:41:    """Inicializa el repositorio con la conexión a MongoDB (solo caché)."""
backend/modules/api_connections/repository.py:241:# ESCRITURA - PRIMERO EDARSAHUB SQL, LUEGO CACHÉ MONGODB
backend/modules/api_connections/repository.py:253:    5. Actualizar caché MongoDB (opcional, no bloquea)
backend/modules/api_connections/repository.py:326:    # 6. Actualizar caché MongoDB (no bloquea si falla)
backend/modules/api_connections/repository.py:343:    6. Actualizar caché MongoDB
backend/modules/api_connections/repository.py:421:    # 7. Actualizar caché MongoDB
backend/modules/api_connections/repository.py:435:    4. Eliminar de caché MongoDB
backend/modules/api_connections/repository.py:467:# SINCRONIZACIÓN EDARSAHUB SQL → MONGODB (CACHÉ)
backend/modules/api_connections/repository.py:477:    Sincroniza todas las conexiones API de EDARSAHUB SQL a MongoDB caché.
backend/modules/api_connections/repository.py:505:    Guarda el resultado en MongoDB como log de estado.
backend/modules/api_connections/routes.py:10:- MongoDB solo se usa como caché/log (no autoritativo)
backend/modules/api_connections/routes.py:12:- Errores de MongoDB se registran pero no bloquean la operación
backend/modules/api_connections/routes.py:164:    DESTINO: EDARSAHUB SQL (autoritativo), luego caché MongoDB.
backend/modules/api_connections/routes.py:197:    DESTINO: EDARSAHUB SQL (autoritativo), luego caché MongoDB.
backend/modules/api_connections/routes.py:283:    Sincroniza conexiones API de EDARSAHUB SQL a MongoDB caché.
backend/modules/api_connections/routes.py:284:    FLUJO: EDARSAHUB SQL → MongoDB (caché).
backend/modules/api_connections/routes.py:291:            "message": "Sincronización EDARSAHUB SQL → MongoDB completada", 
backend/modules/api_connections/universal_test_routes.py:24:- MongoDB
backend/modules/scripts_pendientes/repository.py:3:Reemplaza endpoints MongoDB legacy
backend/modules/scripts_pendientes/routes.py:3:Reemplaza endpoints MongoDB legacy
backend/modules/sistema/sync_catalogo_service.py:13:NO USA MONGODB - 100% SQL Server (EDARSAHUB).
backend/modules/sistema/estructura_service.py:41:        # MongoDB ELIMINADO - Retornar estructura vacía si db es None
backend/modules/sistema/estructura_service.py:43:            logger.warning("[ESTRUCTURA] get_estructura_organizacional: Sin MongoDB - Retornando vacío")
backend/modules/sistema/estructura_service.py:49:                "nota": "Modo SQL-only: Datos de estructura no disponibles sin MongoDB"
backend/modules/sistema/estructura_service.py:54:            empresas = await self.db.sec_empresas.find(
backend/modules/sistema/estructura_service.py:70:                unidades = await self.db.sec_unidades_negocio.find(
backend/modules/sistema/estructura_service.py:86:                    sucursales = await self.db.sec_sucursales.find(
backend/modules/sistema/estructura_service.py:124:            mapeos = await self.db.sec_mapeo_servidor_sucursal.find(
backend/modules/sistema/estructura_service.py:161:            permisos = await self.db.sec_permisos_catalogo.find(
backend/modules/sistema/estructura_service.py:220:            await self.db.sec_bitacora_acceso.insert_one(entry)
backend/modules/sistema/estructura_service.py:233:    NOTA: MongoDB ELIMINADO - Este servicio puede recibir db=None.
backend/modules/costos_margenes/__init__.py:11:- NO usa MongoDB
backend/modules/costos_margenes/routes.py:13:- NO se usa MongoDB
backend/modules/rh/importador/repository.py:40:    """Inicializa el repositorio con la conexión a MongoDB."""
backend/modules/rh/importador/repository.py:47:    """Obtiene la conexión a MongoDB inyectada."""
backend/modules/rh/repository.py:44:# NO depende del catálogo de servidores MongoDB con active=True.
backend/modules/rh/repository.py:56:# ID del servidor EDARSA HUB en MongoDB (LEGACY - ya no se usa para conexión)
backend/modules/rh/repository.py:72:# INYECCIÓN DE DEPENDENCIA: MongoDB
backend/modules/rh/repository.py:79:    """Inicializa el repositorio con la conexión a MongoDB."""
backend/modules/rh/repository.py:86:    """Obtiene la conexión a MongoDB inyectada."""
backend/modules/rh/repository.py:151:    en lugar de buscar en MongoDB servers con active=True.
backend/modules/rh/routes.py:140:    empresas = await db.empresas.find(
backend/modules/configuracion/repositories/config_asignaciones_repository.py:11:Las operaciones legacy de MongoDB pasan por StubDatabase sin fallar.
backend/modules/configuracion/repositories/config_asignaciones_repository.py:310:    # VALIDACIONES SQL (reemplazan validaciones legacy MongoDB)
backend/modules/configuracion/repositories/config_asignaciones_repository.py:432:        En modo SQL-only, esta operación no persiste en MongoDB.
backend/modules/configuracion/services/almacenes_sync_service.py:6:Sincroniza almacenes desde sistemas origen (SoftRestaurant/MPRO) al catálogo local MongoDB.
backend/modules/configuracion/services/almacenes_sync_service.py:95:    - Persiste en MongoDB (almacenes_catalogo)
backend/modules/configuracion/services/almacenes_sync_service.py:98:        db: Conexión a MongoDB
backend/modules/configuracion/services/almacenes_sync_service.py:137:        # FASE P1.4-F (Dic 2025): Migrado de MongoDB db.servers a server_registry
backend/modules/configuracion/services/almacenes_sync_service.py:141:        # ANTES: server = await db.servers.find_one({"id": server_id}, {"_id": 0})
backend/modules/configuracion/services/almacenes_sync_service.py:198:        # PASO 5: Sincronizar al catálogo local MongoDB
backend/modules/configuracion/routes/config_asignaciones_routes.py:26:# Motor para conexión a MongoDB
backend/modules/configuracion/routes/config_asignaciones_routes.py:38:# Conexión a MongoDB
backend/modules/configuracion/routes/config_asignaciones_routes.py:42:    """DEPRECADO: MongoDB ya no se usa. Retorna None (NO-MONGO / P5-1 sunset)."""
backend/modules/configuracion/routes/config_asignaciones_routes.py:43:    logging.debug("[CONFIG_ASIGNACIONES] get_db() - MongoDB deprecado, retornando None")
backend/modules/configuracion/routes/config_asignaciones_routes.py:129:    SQL-First: las validaciones legacy de alcance/roles MongoDB fueron removidas.
backend/modules/inventarios/repository.py:9:- ELIMINADA dependencia de MongoDB
backend/modules/inventarios/repository.py:23:    Reemplaza: mongo_db.inventarios.find(filtro)
backend/modules/consultas_sql/repository.py:3:Reemplaza endpoints MongoDB legacy
backend/modules/consultas_sql/routes.py:3:Reemplaza endpoints MongoDB legacy (/queries, /consultas-custom)
backend/modules/catalogos/__init__.py:30:# Referencia global a MongoDB (para logging/auditoría)
backend/modules/catalogos/__init__.py:35:    """Inicializa el módulo de catálogos con la conexión a MongoDB."""
backend/modules/catalogos/__init__.py:41:    """Obtiene la conexión a MongoDB."""
backend/modules/catalogos/repository.py:9:FASE P1.2 (Dic 2025): Migrado de MongoDB db.servers a EDARSAHUB_CONFIG de server_registry.
backend/modules/catalogos/repository.py:24:# FASE P1.2: La conexión ahora viene de EDARSAHUB_CONFIG, no de MongoDB
backend/modules/catalogos/repository.py:39:    FASE P1.2 (Dic 2025): Migrado de MongoDB db.servers a server_registry.EDARSAHUB_CONFIG.
backend/modules/catalogos/repository.py:43:    NO FUENTE: MongoDB db.servers
backend/modules/catalogos/repository.py:343:        db: Conexión a MongoDB (para obtener credenciales SQL)
backend/modules/auth/service.py:74:    # Preparar documento para MongoDB
backend/modules/auth/service.py:135:        # El ID puede venir como int (de SQL) o como string (MongoDB ObjectId)
backend/modules/auth/service.py:376:    Ya NO escribe en MongoDB. Los permisos operativos se guardan en:
backend/modules/auth/service.py:608:    # Retornar sin password ni _id (MongoDB agrega _id al dict después de insert)
backend/modules/auth/__init__.py:14:- repository.py: Acceso a MongoDB
backend/modules/auth/__init__.py:37:    Inicializa el módulo de auth con la conexión a MongoDB.
backend/modules/auth/password_reset.py:15:- MongoDB ya NO se usa en este módulo
backend/modules/auth/password_reset.py:133:    AUTH-RESET-P2: Reemplaza MongoDB rate_limit_password_reset.
backend/modules/auth/password_reset.py:181:    AUTH-RESET-P2: Reemplaza MongoDB rate_limit_password_reset.
backend/modules/auth/password_reset.py:228:    AUTH-RESET-P2: Reemplaza MongoDB audit_password_reset.
backend/modules/auth/repository.py:5:Sin fallback a MongoDB.
backend/modules/auth/repository.py:15:    """Inicializa el repositorio (compatibilidad legacy, no usa MongoDB)."""
backend/modules/auth/repository.py:380:    """Compatibilidad legacy: ya no hay MongoDB (SQL-First)."""
backend/modules/auth/context_service.py:16:Este módulo ha sido migrado de MongoDB a EDARSAHUB SQL.
backend/modules/auth/context_service.py:26:MongoDB ya no es fuente de datos para contexto de usuario.
backend/modules/auth/context_service.py:216:    Obtiene una empresa por UUID MongoDB.
backend/modules/auth/routes.py:122:    # Autenticar usuario (valida credenciales contra MongoDB)
backend/modules/auth/routes.py:284:    # Buscar usuario en MongoDB para obtener email y role
backend/modules/auth/routes.py:715:# - MongoDB es ubicacion TRANSITORIA/LEGACY para usuarios
backend/modules/comercial_v2/__init__.py:15:- NO consultan SQL vivo ni MongoDB cache
backend/modules/comercial_v2/repository_readonly.py:13:- MongoDB cache
backend/modules/comercial_v2/schemas_api.py:63:    mongodb_cache: bool = False
backend/modules/comercial_v2/routes.py:10:- MongoDB cache
backend/modules/comercial_v2/routes.py:643:    Fuente: EDARSAHUB (NO SQL vivo, NO MongoDB)
backend/modules/universal_query/routes.py:167:    FASE P1.3 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/modules/universal_query/routes.py:171:    NO FUENTE: MongoDB db.servers
backend/modules/universal_query/routes.py:176:    # Obtener desde EDARSAHUB SQL (NO MongoDB)
backend/modules/universal_query/routes.py:243:    FASE P1.3 (Dic 2025): Migrado de MongoDB a EDARSAHUB SQL via server_registry.
backend/modules/universal_query/routes.py:250:    # Obtener servidor desde EDARSAHUB SQL (NO MongoDB)
backend/modules/informes_auditoria/repository.py:3:Reemplaza endpoints MongoDB legacy
backend/modules/informes_auditoria/routes.py:3:Reemplaza endpoints MongoDB legacy en server.py
backend/modules/finanzas/repository_bancarios.py:6:Acceso a datos EDARSAHUB. NO usar MongoDB.
backend/modules/finanzas/repository_bancarios.py:30:    IMPORTANTE: Solo usar EDARSAHUB, NO MongoDB.
backend/modules/finanzas/repository_cuadres_z_edarsahub.py:81:    NO usa MongoDB como fuente financiera.
backend/modules/finanzas/repository_cuadres_z_edarsahub.py:1106:            # Formatear para compatibilidad con contrato anterior (MongoDB)
backend/modules/finanzas/carga_historica_propinas_tpv.py:21:- NO usa MongoDB como fuente financiera
backend/modules/finanzas/tesoreria.py:9:- Ya NO usa MongoDB (tesoreria_cuadres_z) como fuente productiva
backend/modules/finanzas/tesoreria.py:61:    empresas = await db.empresas.find(
backend/modules/finanzas/tesoreria.py:302:    - Ya NO usa MongoDB tesoreria_cuadres_z
backend/modules/finanzas/tesoreria.py:322:        # Filtrar por server_id o unidad_negocio_pk (SQL directo, sin MongoDB)
backend/modules/finanzas/tesoreria.py:359:    - Ya NO usa MongoDB tesoreria_cuadres_z
backend/modules/finanzas/tesoreria.py:448:    - Ya NO usa MongoDB tesoreria_cuadres_z
backend/modules/finanzas/tesoreria.py:748:    FALLBACK: MongoDB (solo si EDARSAHUB falla, con warning)
backend/modules/finanzas/tesoreria.py:756:    NOTA TÉCNICA: MongoDB se mantiene como registry legacy parcial para fallback.
backend/modules/finanzas/tesoreria.py:821:            logger.warning("[TESORERIA][EDARSAHUB_EMPTY] EDARSAHUB no retornó servidores, intentando fallback MongoDB")
backend/modules/finanzas/tesoreria.py:826:    # FALLBACK: server_registry.py (FASE T2.2: Reemplaza MongoDB)
backend/modules/finanzas/tesoreria.py:880:    FASE T2.2: Fallback migrado a server_registry.py (elimina MongoDB).
backend/modules/finanzas/repository_cuadres_z.py:3:Repositorio MongoDB para Cuadres de Cortes Z
backend/modules/finanzas/repository_cuadres_z.py:14:# MongoDB connection
backend/modules/finanzas/repository_cuadres_z.py:18:    """DEPRECADO: MongoDB ya no se usa. Retorna None (NO-MONGO / P5-1 sunset)."""
backend/modules/finanzas/repository_cuadres_z.py:19:    logging.debug("[CUADRES_Z] get_db() - MongoDB deprecado, retornando None")
backend/modules/finanzas/cuentas_por_pagar.py:72:    empresas = await db.empresas.find(
backend/modules/finanzas/repository_real.py:23:# FASE T2.1: Usar EDARSAHUB_CONFIG desde server_registry en lugar de MongoDB
backend/modules/finanzas/repository_real.py:41:            db: Instancia de MongoDB (conservada por compatibilidad, no usada para conexión EDARSAHUB)
backend/modules/finanzas/repository_real.py:51:        Ya no consulta MongoDB db.servers.
backend/modules/finanzas/repository_cortes_z.py:45:            server_id: UUID del servidor en MongoDB/EDARSAHUB
backend/modules/finanzas/historical_kpis_repository.py:29:    Ya no consulta MongoDB db.servers.
backend/modules/finanzas/propinas_tpv/service.py:27:# FASE T2.4: Usar server_registry centralizado en lugar de MongoDB
backend/modules/finanzas/propinas_tpv/service.py:78:        # Ya no usar MongoDB: self.db['servers']
backend/modules/finanzas/propinas_tpv/__init__.py:12:# - MongoDB = Solo cache de lectura rápida (propinas_cache_*)
backend/modules/finanzas/propinas_tpv/__init__.py:25:# - NO toca colecciones existentes de MongoDB
backend/modules/finanzas/propinas_tpv/routes_sql.py:8:FASE T2.3 (Mayo 2026): Migrado a server_registry.py (elimina MongoDB db.servers)
backend/modules/finanzas/propinas_tpv/routes_sql.py:12:- MongoDB = Solo cache
backend/modules/finanzas/propinas_tpv/routes_sql.py:59:    FASE T2.3: Reemplaza db.servers.find_one()
backend/modules/finanzas/propinas_tpv/routes_sql.py:83:    FASE T2.3: Reemplaza db.servers.find({system_type: 'SoftRestaurant'})
backend/modules/finanzas/propinas_tpv/routes_sql.py:116:    """Obtiene la conexión a MongoDB."""
backend/modules/finanzas/propinas_tpv/routes_sql.py:132:        # Verificar MongoDB (cache)
backend/modules/finanzas/propinas_tpv/routes_sql.py:133:        await db.command('ping')
backend/modules/finanzas/propinas_tpv/routes_sql.py:145:            "arquitectura": "SQL Server (persistencia) + MongoDB (cache)",
backend/modules/finanzas/propinas_tpv/routes_sql.py:148:            "mongodb_connected": True,
backend/modules/finanzas/propinas_tpv/routes_sql.py:170:    - Crea índices de cache en MongoDB
backend/modules/finanzas/propinas_tpv/routes_sql.py:220:    4. Invalida cache MongoDB
backend/modules/finanzas/propinas_tpv/routes_sql.py:427:    """Obtiene estadísticas del cache MongoDB."""
backend/modules/finanzas/propinas_tpv/sql_repository.py:17:- MongoDB = Solo cache (gestionado por cache_manager.py)
backend/modules/finanzas/propinas_tpv/sql_repository.py:20:- Este repositorio NO toca colecciones MongoDB existentes
backend/modules/finanzas/propinas_tpv/sql_repository.py:61:            mongo_db: Conexión a MongoDB (conservada por compatibilidad, no usada para conexión EDARSAHUB)
backend/modules/finanzas/propinas_tpv/sql_repository.py:74:        Ya no consulta MongoDB db.servers.
backend/modules/finanzas/propinas_tpv/sql_repository.py:724:        Estructura compatible con el formato anterior (MongoDB).
backend/modules/finanzas/propinas_tpv/repository_edarsahub.py:7:Reemplaza la lectura de MongoDB para consultas financieras.
backend/modules/finanzas/propinas_tpv/cache_manager.py:10:- Gestión de cache en MongoDB
backend/modules/finanzas/propinas_tpv/cache_manager.py:15:- MongoDB = Solo cache de lectura rápida
backend/modules/finanzas/propinas_tpv/cache_manager.py:40:    Gestor de cache MongoDB para el módulo de Propinas TPV.
backend/modules/finanzas/propinas_tpv/cache_manager.py:59:            db: Conexión a MongoDB
backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:7:Reemplazan la lectura de MongoDB para consultas financieras.
backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:77:    # Buscar en MongoDB las empresas y sus unidades
backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:79:        empresas = await db.empresas.find(
backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:222:    Compatible con formato anterior de MongoDB.
backend/modules/finanzas/propinas_tpv/repository.py:11:- Operaciones CRUD en MongoDB (colecciones nuevas)
backend/modules/finanzas/propinas_tpv/repository.py:37:    2. MongoDB: SOLO escribe en colecciones nuevas (propinas_control, propinas_config)
backend/modules/finanzas/propinas_tpv/repository.py:386:    # OPERACIONES MONGODB - COLECCIÓN propinas_control
backend/modules/finanzas/propinas_tpv/repository.py:619:    # OPERACIONES MONGODB - COLECCIÓN propinas_config
backend/modules/finanzas/propinas_tpv/service_sql.py:11:- Orquestación de SQL Server (escritura) + MongoDB (cache/lectura)
backend/modules/finanzas/propinas_tpv/service_sql.py:16:- ESCRITURA: Siempre a SQL Server → Invalidar cache MongoDB
backend/modules/finanzas/propinas_tpv/service_sql.py:17:- LECTURA: Cache MongoDB → Si miss, SQL Server → Actualizar cache
backend/modules/finanzas/propinas_tpv/service_sql.py:39:# FASE T2.4: Usar server_registry centralizado en lugar de MongoDB
backend/modules/finanzas/propinas_tpv/service_sql.py:52:    SoftRestaurant (Lectura) → SQL Server (Persistencia) → MongoDB (Cache)
backend/modules/finanzas/propinas_tpv/service_sql.py:77:        2. Crea índices de cache en MongoDB
backend/modules/finanzas/propinas_tpv/service_sql.py:145:        5. Invalidar cache MongoDB
backend/modules/finanzas/propinas_tpv/service_sql.py:159:        # Ya no usar MongoDB: self.db['servers']
backend/modules/finanzas/propinas_tpv/service_sql.py:342:        1. Buscar en cache MongoDB
backend/modules/finanzas/propinas_tpv/routes.py:22:FASE T2.3 (Mayo 2026): Migrado a server_registry.py (elimina MongoDB db.servers)
backend/modules/finanzas/propinas_tpv/routes.py:62:    FASE T2.3: Reemplaza db.servers.find_one()
backend/modules/finanzas/propinas_tpv/routes.py:88:    FASE T2.3: Reemplaza db.servers.find({system_type: 'SoftRestaurant'})
backend/modules/finanzas/propinas_tpv/routes.py:123:    Obtiene la conexión a MongoDB.
backend/modules/finanzas/propinas_tpv/routes.py:142:    empresas = await db.empresas.find(
backend/modules/finanzas/propinas_tpv/routes.py:171:        await db.command('ping')
backend/modules/finanzas/propinas_tpv/routes.py:172:        collections = await db.list_collection_names()
backend/modules/finanzas/propinas_tpv/routes.py:181:            "mongodb_connected": True,
backend/modules/finanzas/propinas_tpv/routes.py:235:    - Crea índices en MongoDB
backend/modules/finanzas/propinas_tpv/routes.py:399:    FASE 1B: Consulta propinas de un período SIN guardar en MongoDB.
backend/modules/finanzas/propinas_tpv/models.py:133:    """Schema completo del documento en MongoDB"""
backend/modules/finanzas/propinas_tpv/models.py:199:    """Schema completo en MongoDB"""
backend/modules/finanzas/repository_softrestaurant.py:225:            db: Instancia de MongoDB (opcional, para compatibilidad)
backend/modules/finanzas/cuentas_bancarias.py:10:- NO usar MongoDB
backend/modules/finanzas/repository_mpro.py:16:    - Credenciales desde EDARSAHUB/server_registry.py (no MongoDB)
backend/modules/finanzas/repository_mpro.py:42:            db: Instancia de MongoDB (solo para fallback legacy, preferir SQL)
backend/modules/finanzas/repository_mpro.py:52:        FALLBACK: MongoDB solo si SQL falla (config_origin = MONGODB_LEGACY)
backend/modules/sqlfirst_health/routes.py:26:    - Referencias MongoDB activas
backend/modules/sqlfirst_health/routes.py:57:                "mongodb": "LEGACY_CACHE_ONLY",
backend/modules/admin_sql/rbac_pilot_service.py:4:Reemplaza la implementación legacy basada en MongoDB (`db.sec_perfiles`, `db.sec_roles`,
backend/modules/manuales_operativos/service.py:177:            # Guardar en MongoDB
backend/modules/manuales_operativos/__init__.py:35:    """Inicializa el módulo con la conexión a MongoDB."""
backend/modules/manuales_operativos/triggers.py:43:        db: Conexión a MongoDB
backend/modules/manuales_operativos/triggers.py:80:    proceso = await db.automatizaciones_operativas_compras.find_one({"id": proceso_id})
backend/modules/manuales_operativos/triggers.py:92:    bitacora = await db.automatizaciones_bitacora.find(
backend/modules/manuales_operativos/triggers.py:107:        users_cursor = db.users.find({"id": {"$in": list(user_ids)}}, {"id": 1, "email": 1, "full_name": 1})
backend/modules/manuales_operativos/triggers.py:137:    cursor = db.automatizaciones_operativas_compras.find({
backend/modules/manuales_operativos/triggers.py:171:        db_sync: Conexión pymongo (síncrona)
backend/modules/manuales_operativos/routes.py:31:    """Inicializa el módulo con la conexión a MongoDB."""
backend/modules/manuales_operativos/routes.py:145:        proceso = await _db.automatizaciones_operativas_compras.find_one({"id": proceso_id})
backend/modules/manuales_operativos/routes.py:149:        bitacora = await _db.automatizaciones_bitacora.find(
backend/modules/manuales_operativos/schemas.py:145:    """Schema del manual como está almacenado en MongoDB."""
backend/modules/compras/repository_compras_sql.py:9:- Migración de compras_params de MongoDB a EDARSAHUB SQL
backend/modules/compras/repository_compras_sql.py:14:- CERO dependencias de MongoDB
backend/modules/compras/repository_compras_sql.py:15:- Reemplaza funciones get_compras_params y save_compras_params de MongoDB
backend/modules/compras/repository_compras_sql.py:58:-- Reemplaza colección MongoDB: compras_params
backend/modules/compras/repository_compras_sql.py:130:    REEMPLAZA: get_compras_params() de MongoDB
backend/modules/compras/repository_compras_sql.py:204:    REEMPLAZA: save_compras_params() de MongoDB
backend/modules/compras/__init__.py:15:- repository.py: Acceso a MongoDB y SQL Server
backend/modules/compras/__init__.py:59:    Inicializa el módulo de compras con la conexión a MongoDB.
backend/modules/compras/repository.py:12:- Parámetros de compras migrados de MongoDB a EDARSAHUB SQL
backend/modules/compras/repository.py:14:- CERO MongoDB productivo para parámetros
backend/modules/compras/repository.py:73:# INYECCIÓN DE DEPENDENCIA: MongoDB
backend/modules/compras/repository.py:77:_stub_mode = False  # Flag para indicar si estamos en modo stub (sin MongoDB)
backend/modules/compras/repository.py:82:    Inicializa el repositorio con la conexión a MongoDB.
backend/modules/compras/repository.py:90:        logger.debug("[COMPRAS_REPO] Inicializado en modo STUB - funcionalidad MongoDB limitada")
backend/modules/compras/repository.py:95:    Obtiene la conexión a MongoDB inyectada.
backend/modules/compras/repository.py:108:    """Retorna True si el repositorio está en modo stub (sin MongoDB)."""
backend/modules/compras/repository.py:114:    Descifra el password de un servidor obtenido de MongoDB.
backend/modules/compras/repository.py:143:    FASE T3.1: Migrado de MongoDB db.servers a server_registry (EDARSAHUB).
backend/modules/compras/repository.py:145:    # FASE T3.1: Usar server_registry en lugar de MongoDB
backend/modules/compras/repository.py:159:# Migrado de MongoDB a EDARSAHUB SQL Server
backend/modules/compras/repository.py:166:    MIGRADO: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
backend/modules/compras/repository.py:183:    MIGRADO: Ahora escribe a EDARSAHUB SQL en lugar de MongoDB.
backend/modules/compras/historical_kpis_repository.py:32:    FASE T3.1: Migrado de MongoDB db.servers a EDARSAHUB_CONFIG de server_registry.
backend/modules/compras/historical_kpis_repository.py:33:    Ya no consulta MongoDB para obtener conexión EDARSAHUB.
backend/modules/compras/repository_pedidos_sql.py:7:COMPRAS-MONGO-001-F2: Migración de MongoDB a EDARSAHUB SQL
backend/modules/compras/repository_pedidos_sql.py:9:Migra las siguientes colecciones de MongoDB a SQL:
backend/modules/compras/repository_pedidos_sql.py:16:- #2: CERO dependencias de MongoDB
backend/scripts/p5_audit_cleanup_mongo.py:22:    if re.search(r'from pymongo|import pymongo|MongoClient', txt):
backend/scripts/p5_audit_cleanup_mongo.py:28:print("=== IMPORTS PYMONGO / MONGOCLIENT ===")
backend/scripts/security/audit_secret_leaks_safe.py:11:    "MONGO_URL",
backend/scripts/audit_rbac_connection_runtime_usage.py:26:print("ANÁLISIS: RBACDependency - ¿usa MongoDB o SQL?")
backend/scripts/audit_rbac_connection_runtime_usage.py:45:# Verificar si get_current_user_from_token usa MongoDB
backend/scripts/ddl_fase2_operativo_tablas.sql:10:-- Reemplaza: MongoDB notificaciones_log
backend/scripts/ddl_fase2_operativo_tablas.sql:47:-- Reemplaza: MongoDB justificaciones_inventario
backend/scripts/ddl_fase2_operativo_tablas.sql:84:-- Reemplaza: MongoDB decisiones_auditoria
backend/scripts/ddl_fase2_operativo_tablas.sql:115:-- Reemplaza: MongoDB historial_asignaciones
backend/scripts/ddl_fase2_operativo_tablas.sql:148:-- Reemplaza: MongoDB responsabilidades
backend/scripts/ddl_fase2_operativo_tablas.sql:189:-- Reemplaza: MongoDB cargos_responsabilidad
backend/scripts/ddl_fase2_operativo_tablas.sql:233:-- Reemplaza: MongoDB historial de cargos
backend/scripts/ddl_fase2_operativo_tablas.sql:269:-- Reemplaza: MongoDB tareas_operativas_compras
backend/scripts/ddl_fase2_operativo_tablas.sql:307:-- Reemplaza: MongoDB auditoria_compras_bitacora
backend/scripts/ddl_fase2_operativo_tablas.sql:337:-- Reemplaza: MongoDB pedidos_procesados_automatizacion
backend/scripts/ddl_fase2_operativo_tablas.sql:367:-- Reemplaza: MongoDB auditorias programadas
backend/scripts/ddl_fase2_operativo_tablas.sql:406:-- Reemplaza: MongoDB documentos_generados
backend/scripts/ddl_costos_alertas_001b.py:6:MÁXIMAS: EDARSAHUB SQL es el cerebro. CERO MongoDB.
backend/scripts/ddl_costos_alertas_001b.py:618:    print("MÁXIMAS: EDARSAHUB SQL es el cerebro. CERO MongoDB.")
backend/scripts/ddl_auth_reset_p2_rate_limit_audit.sql:6:-- OBJETIVO: Eliminar dependencias de MongoDB en password_reset.py
backend/scripts/ddl_auth_reset_p2_rate_limit_audit.sql:14:-- Reemplaza: MongoDB collection rate_limit_password_reset
backend/scripts/ddl_auth_reset_p2_rate_limit_audit.sql:54:-- Reemplaza: MongoDB collection audit_password_reset
backend/scripts/migrate_legacy_mongo_to_sql.py:8:# from pymongo import MongoClient  # P5: legacy migration only
backend/scripts/migrate_legacy_mongo_to_sql.py:18:def get_mongo_client() -> MongoClient:
backend/scripts/migrate_legacy_mongo_to_sql.py:19:    mongo_uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI") or os.getenv("MONGO_URL")
backend/scripts/migrate_legacy_mongo_to_sql.py:21:        raise RuntimeError("No existe MONGO_URI, MONGODB_URI ni MONGO_URL para migración controlada")
backend/scripts/migrate_legacy_mongo_to_sql.py:288:    mongo = get_mongo_client()
backend/scripts/create_scheduler_tables.py:4:Reemplaza las colecciones MongoDB para los jobs de detección.
backend/scripts/create_workflow_tables.sql:3:-- Migración de MongoDB a SQL Server
backend/scripts/rotate_server_secret_key.py:23:    --include-mongo     Sincronizar MongoDB espejo
backend/scripts/rotate_server_secret_key.py:24:    --only-sql          Solo SQL, ignorar MongoDB
backend/scripts/rotate_server_secret_key.py:369:                # Sincronizar MongoDB si aplica
backend/scripts/rotate_server_secret_key.py:372:                        sync_to_mongodb(server_id, updates)
backend/scripts/rotate_server_secret_key.py:376:                        logger.warning(f"[SECRET_ROTATION][PARTIAL_SYNC] {server_name}: MongoDB sync failed")
backend/scripts/rotate_server_secret_key.py:377:                        result['errors'].append(f"{server_name}: MongoDB sync failed - {type(e).__name__}")
backend/scripts/rotate_server_secret_key.py:393:def sync_to_mongodb(server_id: str, updates: Dict):
backend/scripts/rotate_server_secret_key.py:494:        print(f"MongoDB sincronizado: {report['mongo_synced']}")
backend/scripts/rotate_server_secret_key.py:515:    parser.add_argument('--include-mongo', action='store_true', help='Sincronizar MongoDB espejo')
backend/scripts/rotate_server_secret_key.py:516:    parser.add_argument('--only-sql', action='store_true', help='Solo SQL, ignorar MongoDB')
backend/scripts/rotate_server_secret_key.py:596:            print(f"   → MongoDB sincronizado: {rotation_result['mongo_synced']}")
backend/scripts/create_unidades_negocio_table.py:5:eliminando la dependencia de MongoDB para esta información.
backend/tests/test_automatizacion_compras_fase4.py:15:COLECCIONES MONGODB:
backend/tests/test_auth_mocks.py:42:            mock_db.users.find_one = AsyncMock(return_value=mock_user_db)
backend/tests/test_auth_mocks.py:45:            assert mock_db.users.find_one is not None
backend/tests/test_dashboard_comercial.py:45:                mock_db.servers.find_one = AsyncMock(return_value=None)
backend/tests/test_dashboard_comercial.py:98:                mock_db.servers.find_one = AsyncMock(return_value=sample_server_config)
backend/tests/test_repositories.py:15:    """Tests de acceso a MongoDB con mocks"""
backend/tests/test_repositories.py:19:        """Test: Mock de MongoDB tiene estructura correcta"""
backend/tests/test_comparativo_inventarios.py:3:Tests the cache storage in MongoDB and Excel export endpoint.
backend/tests/test_comparativo_inventarios.py:6:1. /api/reports/inventory-analysis - saves correctly to MongoDB cache (inventario_diferencias_detalle)
backend/tests/test_comparativo_inventarios.py:120:        """Test that MongoDB cache has 4 documents for the test folios"""
backend/tests/test_recipients_manager.py:2:Test Suite: Centro de Control - Recipients Manager (MongoDB)
backend/tests/test_recipients_manager.py:4:Tests for CRUD operations on alert recipients stored in MongoDB.
backend/tests/test_recipients_manager.py:12:- Verify email_notifications.py reads from MongoDB
backend/tests/test_recipients_manager.py:13:- Verify whatsapp_notifications.py reads from MongoDB
backend/tests/test_recipients_manager.py:24:    """CRUD operations for alert recipients in MongoDB"""
backend/tests/test_recipients_manager.py:348:class TestNotificationServicesReadFromMongoDB:
backend/tests/test_recipients_manager.py:349:    """Verify email and whatsapp services read recipients from MongoDB"""
backend/tests/test_recipients_manager.py:361:    def test_email_config_shows_mongodb_recipients(self):
backend/tests/test_recipients_manager.py:362:        """GET /email/config should show recipients from MongoDB"""
backend/tests/test_recipients_manager.py:374:        print(f"✓ Email config shows {data['config']['recipients_count']} recipients from MongoDB")
backend/tests/test_recipients_manager.py:376:    def test_whatsapp_config_shows_mongodb_recipients(self):
backend/tests/test_recipients_manager.py:377:        """GET /whatsapp/config should show recipients from MongoDB"""
backend/tests/test_recipients_manager.py:389:        print(f"✓ WhatsApp config shows {data['config']['recipients_count']} recipients from MongoDB")
backend/tests/test_recipients_manager.py:404:        # Email should be configured with MongoDB recipients
backend/tests/test_recipients_manager.py:409:        # WhatsApp should be configured with MongoDB recipients
backend/tests/test_recipients_manager.py:414:        print("✓ All notification services configured with MongoDB recipients")
backend/tests/test_recipients_manager.py:418:    """Verify seeded recipients exist in MongoDB"""
backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:4288:    [FuenteOriginal] NVARCHAR(20) NOT NULL DEFAULT ('MONGODB'),
backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:6997:    [mongodb_id] NVARCHAR(100) NULL,
backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7011:    [mongodb_id] NVARCHAR(100) NULL,
backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:7052:    [mongodb_id] NVARCHAR(100) NULL,
backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8811:    [RolMongoDB] VARCHAR(50) NOT NULL,
backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:8812:    [ActivoMongoDB] BIT NOT NULL,
backend/server.py:74:# MongoDB import movido a bloque condicional más abajo
backend/server.py:107:# MÁXIMA EDARSAHUB: SQL Server es el cerebro. MongoDB ELIMINADO.
backend/server.py:111:# Los accesos a colecciones MongoDB retornan valores vacíos sin fallar.
backend/server.py:115:# MongoDB ELIMINADO - Usar StubDatabase para evitar errores en código legacy
backend/server.py:118:logger.info("[DB] Sistema funcionando 100% SQL Server - MongoDB ELIMINADO (usando StubDatabase)")
backend/server.py:294:init_security(None)  # MongoDB eliminado
backend/server.py:379:    Descifra los secretos de un servidor obtenido de MongoDB/SQL.
backend/server.py:452:init_compras_module(None)  # MongoDB eliminado
backend/server.py:479:init_comercial_module(None)  # MongoDB eliminado
backend/server.py:595:# - Fuente única: EDARSAHUB (no MongoDB)
backend/server.py:630:init_manuales_module(None)  # MongoDB eliminado
backend/server.py:633:init_rh_module(None)  # MongoDB eliminado
backend/server.py:636:init_catalogos_module(None)  # MongoDB eliminado
backend/server.py:637:init_catalogos_service(None)  # MongoDB eliminado
backend/server.py:640:_finanzas_repo = FinanzasRepositoryReal(None)  # MongoDB eliminado
backend/server.py:645:_mpro_repo = FinanzasRepositoryMPRO(None)  # MongoDB eliminado
backend/server.py:649:_softrest_repo = FinanzasRepositorySoftRestaurant(None)  # MongoDB eliminado
backend/server.py:675:# FUENTE: EDARSAHUB (no MongoDB)
backend/server.py:687:# NO usa MongoDB
backend/server.py:715:init_sync_receiver(None)  # MongoDB eliminado
backend/server.py:716:init_kpis_repository(None)  # MongoDB eliminado
backend/server.py:725:init_api_connections_repository(None)  # MongoDB eliminado
backend/server.py:753:# junto con los otros módulos SQL-first migrados de MongoDB
backend/server.py:759:# NO usa MongoDB. NO usa conexiones LIVE.
backend/server.py:786:# Cache service (100% SQL - MongoDB eliminado)
backend/server.py:1348:    # FASE P1.4-B (Dic 2025): Corregido para aceptar objetos JSON (EDARSAHUB) o strings (legacy MongoDB)
backend/server.py:1368:    config_origin: Optional[str] = None  # "EDARSAHUB_SQL" | "MONGODB_LEGACY"
backend/server.py:1904:    FASE 3B.1: Crea servidor en EDARSAHUB SQL primero, NO sincroniza a MongoDB.
backend/server.py:1907:    - MongoDB no se usa en flujo productivo
backend/server.py:1937:        sync_mongo=False  # P5: MongoDB sync deshabilitado
backend/server.py:1965:    2. Sin fallback MongoDB
backend/server.py:1976:        allow_mongo_fallback=False,  # P5: Fallback MongoDB deshabilitado
backend/server.py:1992:    2. Sin fallback MongoDB
backend/server.py:2003:        allow_mongo_fallback=False,  # P5: Fallback MongoDB deshabilitado
backend/server.py:2015:    FASE 3B.1: Actualiza servidor en EDARSAHUB SQL primero, NO sincroniza a MongoDB.
backend/server.py:2018:    - MongoDB no se usa en flujo productivo
backend/server.py:2053:        sync_mongo=False  # P5: MongoDB sync deshabilitado
backend/server.py:2073:    FASE 3B.1: Desactiva servidor en EDARSAHUB SQL primero, NO sincroniza a MongoDB.
backend/server.py:2077:    - MongoDB no se usa en flujo productivo
backend/server.py:2106:        sync_mongo=False,  # P5: MongoDB sync deshabilitado
backend/server.py:2132:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:2139:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}))
backend/server.py:2167:            await db.server_status.update_one(
backend/server.py:2194:        await db.server_status.update_one(
backend/server.py:2227:    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:2229:    NO FUENTE: MongoDB db.servers
backend/server.py:2252:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:2334:    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:2336:    NO FUENTE: MongoDB db.servers
backend/server.py:2350:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:2365:    # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {field_name: query_config}})
backend/server.py:2371:        sync_mongo=False  # P5: MongoDB sync deshabilitado  # Mantener espejo MongoDB para compatibilidad
backend/server.py:2378:    # ANTES: updated_server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}, {"_id": 0}))
backend/server.py:2387:        # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {"queries_configured": all_configured}})
backend/server.py:2393:            sync_mongo=False  # P5: MongoDB sync deshabilitado
backend/server.py:2411:    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:2413:    NO FUENTE: MongoDB db.servers
backend/server.py:2418:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:2470:    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:2472:    NO FUENTE: MongoDB db.servers
backend/server.py:2480:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:2487:    # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {field_name: None, "queries_configured": False}})
backend/server.py:2493:        sync_mongo=False  # P5: MongoDB sync deshabilitado
backend/server.py:2517:    - No usar MongoDB
backend/server.py:2640:    NO consulta MongoDB.
backend/server.py:2677:    NO consulta MongoDB.
backend/server.py:3073:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3081:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:3192:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3204:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:3312:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3317:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:3346:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3354:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:3491:    Migrado de db.servers.find() a server_registry.list_servers()
backend/server.py:3497:    # ANTES: server_cursor = db.servers.find({"id": {"$in": server_ids}}, {"_id": 0, "id": 1, "name": 1})
backend/server.py:3529:    MongoDB NO se usa como fuente, ni como fallback, ni como respaldo.
backend/server.py:3681:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3693:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:3755:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3767:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:3872:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3893:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:4225:    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:4227:    NO FUENTE: MongoDB db.servers
backend/server.py:4297:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:4874:                        await db.inventario_diferencias_detalle.update_one(
backend/server.py:4895:                orquestador = get_orquestador_service(db)  # MongoDB ELIMINADO - StubDatabase
backend/server.py:5522:                        await db.inventario_diferencias_detalle.update_one(
backend/server.py:5539:                orquestador = get_orquestador_service(db)  # MongoDB ELIMINADO - StubDatabase
backend/server.py:5589:    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:5591:    NO FUENTE: MongoDB db.servers
backend/server.py:5603:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:5845:    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:5847:    NO FUENTE: MongoDB db.servers
backend/server.py:5858:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:6155:            cached = await db.inventario_diferencias_detalle.find_one(cache_key, {"_id": 0})
backend/server.py:6412:    Usa cache en MongoDB para evitar recalcular.
backend/server.py:6416:    FASE P1.4-E3 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:6418:    NO FUENTE: MongoDB db.servers
backend/server.py:6430:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
backend/server.py:6612:    await db.alerts.insert_one(doc)
backend/server.py:6618:    alerts = await db.alerts.find({"active": True}, {"_id": 0}).to_list(1000)
backend/server.py:6623:    await db.alerts.update_one({"id": alert_id}, {"$set": alert_data})
backend/server.py:6628:    await db.alerts.update_one({"id": alert_id}, {"$set": {"active": False}})
backend/server.py:6690:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:6699:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:6756:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:6776:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:6914:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:6924:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:7231:    FASE P1.4-E2 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:7233:    NO FUENTE: MongoDB db.servers
backend/server.py:7254:        # ANTES: server = decrypt_server_secrets(await db.servers.find_one(query))
backend/server.py:7469:    Migrado de db.servers.find() a server_registry.list_servers()
backend/server.py:7472:    # ANTES: servers = await db.servers.find({"active": True, "queries_configured": True}, {...}).to_list(100)
backend/server.py:7497:    NOTA: db.users y db.alerts aún usan MongoDB (fuera del alcance de P1.4-E4).
backend/server.py:7502:    # ANTES: total_servers = await db.servers.count_documents({"active": True})
backend/server.py:7503:    # ANTES: servers_configured = await db.servers.count_documents({"active": True, "queries_configured": True})
backend/server.py:7508:    # NOTA: db.users y db.alerts aún usan MongoDB (migración en Fase 2)
backend/server.py:7509:    total_users = await db.users.count_documents({"active": True})
backend/server.py:7510:    total_alerts = await db.alerts.count_documents({"active": True})
backend/server.py:7589:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:7592:    FASE 2-G FIX: Usar get_current_user que busca en SQL en lugar de db.users (MongoDB)
backend/server.py:7603:    # FASE 2-G FIX: Usar get_current_user (SQL-only) en lugar de db.users (MongoDB)
backend/server.py:7628:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:9098:    FASE P1.4-E1 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:9100:    NO FUENTE: MongoDB db.servers
backend/server.py:9113:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
backend/server.py:11418:    - No usa MongoDB
backend/server.py:11975:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:11979:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:12146:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:12156:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:12200:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:12216:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:12360:    # Guardar log en MongoDB
backend/server.py:12361:    await db.script_logs.insert_one({
backend/server.py:13255:    FASE P1.4-E4 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:13257:    NO FUENTE: MongoDB db.servers
backend/server.py:13265:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:13279:    # FASE P5: MongoDB deprecado - scripts_pendientes migrado a SQL
backend/server.py:13403:    await db.script_logs.insert_one({
backend/server.py:13418:    # FASE P5: MongoDB deprecado - scripts_pendientes migrado a SQL
backend/server.py:13420:        pass  # P5: db.scripts_pendientes.update_one eliminado - usar API SQL
backend/server.py:13901:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:13906:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:14067:    Incluye consultas predefinidas y personalizadas (MongoDB).
backend/server.py:14087:    # FASE P5: MongoDB deprecado - consultas_custom migrado a SQL
backend/server.py:14089:    # consultas_custom = await db.consultas_custom.find(filtro).to_list(500)
backend/server.py:14126:        # FASE P5: MongoDB deprecado - consultas_custom migrado a SQL
backend/server.py:14153:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:14238:# CRUD CONSULTAS PERSONALIZADAS - FASE P5: MongoDB deprecado
backend/server.py:14244:    FASE P5: MongoDB deprecado - usar Sistema_ConsultasSQL via API SQL
backend/server.py:14256:    FASE P5: MongoDB deprecado - usar Sistema_ConsultasSQL via API SQL
backend/server.py:14368:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:14391:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))
backend/server.py:14435:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:14449:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))
backend/server.py:14524:        solicitudes = await db.solicitudes_catalogos.find(
backend/server.py:14553:        proveedores = await db.portal_proveedores.find(
backend/server.py:14601:        ciclos = await db.nomina_ciclos.find(
backend/server.py:14607:        config = await db.nomina_configuracion.find_one({}, {"_id": 0})
backend/server.py:14687:    await db.tareas_sistema.update_one(
backend/server.py:14700:-- Base de datos: EDARSA HUB (Opcional - Las tareas se guardan en MongoDB)
backend/server.py:14704:-- El sistema principal usa MongoDB para las tareas
backend/server.py:14731:        "nota": "Este script es OPCIONAL. El sistema de tareas funciona con MongoDB. Use este script solo si desea mantener un log adicional en SQL Server."
backend/server.py:14764:    await db.nomina_ciclos.update_one(
backend/server.py:14805:    cursor = db.nomina_ciclos.find(filtro).sort("fecha_creacion", -1)
backend/server.py:14808:    # Limpiar _id de MongoDB
backend/server.py:14818:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
backend/server.py:14851:    ciclo_existente = await db.nomina_ciclos.find_one({
backend/server.py:14860:    config = await db.nomina_configuracion.find_one({"tipo": "general"})
backend/server.py:14896:    await db.nomina_ciclos.insert_one(ciclo)
backend/server.py:14911:    user = await db.users.find_one({"id": current_user.get("id")})
backend/server.py:14916:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
backend/server.py:14941:    config = await db.nomina_configuracion.find_one({"tipo": "general"})
backend/server.py:14967:    await db.nomina_ciclos.update_one(
backend/server.py:15002:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
backend/server.py:15021:    await db.nomina_ciclos.update_one(
backend/server.py:15049:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
backend/server.py:15053:    cursor = db.nomina_movimientos.find({"ciclo_id": ciclo_id}).sort("fecha_registro", -1)
backend/server.py:15066:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
backend/server.py:15111:    await db.nomina_movimientos.insert_one(movimiento)
backend/server.py:15114:    await db.nomina_ciclos.update_one(
backend/server.py:15125:    movimiento = await db.nomina_movimientos.find_one({"id": movimiento_id})
backend/server.py:15132:    ciclo = await db.nomina_ciclos.find_one({"id": ciclo_id})
backend/server.py:15136:    await db.nomina_movimientos.delete_one({"id": movimiento_id})
backend/server.py:15139:    await db.nomina_ciclos.update_one(
backend/server.py:15150:    config = await db.nomina_configuracion.find_one({"tipo": "general"})
backend/server.py:15188:    await db.nomina_configuracion.update_one(
backend/server.py:15200:    cursor = db.nomina_kpis_puestos.find({})
backend/server.py:15242:    await db.nomina_kpis_puestos.update_one(
backend/server.py:15258:-- NOTA: Las tablas principales se manejan en MongoDB.
backend/server.py:15326:        CicloID NVARCHAR(50) NOT NULL, -- ID del ciclo en MongoDB
backend/server.py:15346:        "nota": "Este script es OPCIONAL. El sistema de nóminas funciona principalmente con MongoDB. Use estas tablas para integración con NomiPAQ o reportes SQL."
backend/server.py:15399:            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
backend/server.py:15406:        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
backend/server.py:15429:    service = get_estructura_service(db)  # MongoDB ELIMINADO - StubDatabase
backend/server.py:15471:    service = get_estructura_service(db)  # MongoDB ELIMINADO - StubDatabase
backend/server.py:15492:    service = get_estructura_service(db)  # MongoDB ELIMINADO - StubDatabase
backend/server.py:15741:    # MongoDB ELIMINADO - Este handler ya no es necesario
backend/server.py:15742:    # La variable 'client' ya no existe (era el cliente de MongoDB)
backend/server.py:15753:init_notifications_routes(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad
backend/server.py:15759:init_scheduler_routes(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad
backend/server.py:15806:    rbac_service = RBACService(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad
backend/server.py:16061:# MÓDULOS SQL-FIRST (Migración MongoDB Legacy)
backend/server.py:16133:        await start_scheduler(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad
backend/utils/migration_helpers.py:3:EDARSA HUB - Utilidades de Migración MongoDB → SQL Server
backend/utils/migration_helpers.py:5:Funciones helper para convertir código legacy MongoDB a SQL-First.
backend/utils/migration_helpers.py:16:    # Colección MongoDB → Tabla SQL Server
backend/utils/migration_helpers.py:40:SYSTEM_PROMPT = """Eres un experto en migración de MongoDB a SQL Server para EDARSA HUB.
backend/utils/migration_helpers.py:45:- MongoDB PROHIBIDO: Todo código debe usar execute_hub_query()
backend/utils/migration_helpers.py:74:    Convierte código MongoDB a SQL Server alineado al 
backend/utils/migration_helpers.py:78:        codigo_mongo: Código Python con operaciones MongoDB
backend/utils/migration_helpers.py:87:            return await db.servers.find({"active": True}).to_list(100)
backend/utils/migration_helpers.py:101:    prompt = f"""Convierte este código MongoDB a SQL Server usando execute_hub_query():
backend/htmlcov/z_57760688d1f824db_cerebro_py.html:90:    <p class="pln"><span class="n"><a id="t8" href="#t8">8</a></span><span class="t"><span class="str">- Esquemas de MongoDB</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_cerebro_py.html:741:    <p class="pln"><span class="n"><a id="t659" href="#t659">659</a></span><span class="t"><span class="com"># MAPEO DE COLECCIONES MONGODB</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_cerebro_py.html:744:    <p class="run"><span class="n"><a id="t662" href="#t662">662</a></span><span class="t"><span class="nam">MONGODB_COLLECTIONS</span> <span class="op">=</span> <span class="op">{</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_cerebro_py.html:789:    <p class="pln"><span class="n"><a id="t707" href="#t707">707</a></span><span class="t"><span class="com"># &#205;NDICES MONGODB REQUERIDOS</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_cerebro_py.html:792:    <p class="run"><span class="n"><a id="t710" href="#t710">710</a></span><span class="t"><span class="nam">MONGODB_INDEXES</span> <span class="op">=</span> <span class="op">{</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_cerebro_py.html:869:    <p class="run run2"><span class="n"><a id="t787" href="#t787">787</a></span><span class="t">    <span class="str">'MONGODB_COLLECTIONS'</span><span class="op">,</span> <span class="str">'MONGODB_INDEXES'</span><span class="op">,</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_97abb2331ed8fa5c_repository_py.html:86:    <p class="pln"><span class="n"><a id="t4" href="#t4">4</a></span><span class="t"><span class="str">Acceso a datos para usuarios y roles en MongoDB.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_97abb2331ed8fa5c_repository_py.html:89:    <p class="pln"><span class="n"><a id="t7" href="#t7">7</a></span><span class="t"><span class="str">- Encapsula operaciones de MongoDB para auth</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_97abb2331ed8fa5c_repository_py.html:99:    <p class="pln"><span class="n"><a id="t17" href="#t17">17</a></span><span class="t"><span class="com"># INYECCI&#211;N DE DEPENDENCIA: MongoDB</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_97abb2331ed8fa5c_repository_py.html:107:    <p class="pln"><span class="n"><a id="t25" href="#t25">25</a></span><span class="t"><span class="str">    Inicializa el repositorio con la conexi&#243;n a MongoDB.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_97abb2331ed8fa5c_repository_py.html:117:    <p class="pln"><span class="n"><a id="t35" href="#t35">35</a></span><span class="t">    <span class="str">"""Obtiene la conexi&#243;n a MongoDB inyectada."""</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:86:    <p class="pln"><span class="n"><a id="t4" href="#t4">4</a></span><span class="t"><span class="str">Gesti&#243;n centralizada de conexiones a MongoDB y SQL Server.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:554:    <p class="pln"><span class="n"><a id="t472" href="#t472">472</a></span><span class="t"><span class="com"># FUNCIONES DE MONGODB (Placeholders para fases futuras)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:557:    <p class="run"><span class="n"><a id="t475" href="#t475">475</a></span><span class="t"><span class="key">from</span> <span class="nam">motor</span><span class="op">.</span><span class="nam">motor_asyncio</span> <span class="key">import</span> <span class="nam">AsyncIOMotorClient</span><span class="op">,</span> <span class="nam">AsyncIOMotorDatabase</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:558:    <p class="run"><span class="n"><a id="t476" href="#t476">476</a></span><span class="t"><span class="key">from</span> <span class="nam">pymongo</span> <span class="key">import</span> <span class="nam">MongoClient</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:560:    <p class="pln"><span class="n"><a id="t478" href="#t478">478</a></span><span class="t"><span class="com"># Variables globales para conexiones MongoDB (se inicializar&#225;n en migraci&#243;n futura)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:561:    <p class="run"><span class="n"><a id="t479" href="#t479">479</a></span><span class="t"><span class="nam">_mongo_client</span><span class="op">:</span> <span class="nam">Optional</span><span class="op">[</span><span class="nam">AsyncIOMotorClient</span><span class="op">]</span> <span class="op">=</span> <span class="key">None</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:563:    <p class="run"><span class="n"><a id="t481" href="#t481">481</a></span><span class="t"><span class="nam">_sync_mongo_client</span><span class="op">:</span> <span class="nam">Optional</span><span class="op">[</span><span class="nam">MongoClient</span><span class="op">]</span> <span class="op">=</span> <span class="key">None</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:566:    <p class="run"><span class="n"><a id="t484" href="#t484">484</a></span><span class="t"><span class="key">async</span> <span class="key">def</span> <span class="nam">get_mongo_client</span><span class="op">(</span><span class="op">)</span> <span class="op">-></span> <span class="nam">AsyncIOMotorClient</span><span class="op">:</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:568:    <p class="pln"><span class="n"><a id="t486" href="#t486">486</a></span><span class="t"><span class="str">    Obtiene el cliente MongoDB async.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:571:    <p class="pln"><span class="n"><a id="t489" href="#t489">489</a></span><span class="t">    <span class="key">global</span> <span class="nam">_mongo_client</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:572:    <p class="mis show_mis"><span class="n"><a id="t490" href="#t490">490</a></span><span class="t">    <span class="key">if</span> <span class="nam">_mongo_client</span> <span class="key">is</span> <span class="key">None</span><span class="op">:</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:573:    <p class="mis show_mis"><span class="n"><a id="t491" href="#t491">491</a></span><span class="t">        <span class="key">raise</span> <span class="nam">RuntimeError</span><span class="op">(</span><span class="str">"MongoDB client not initialized. Use server.py connection."</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:574:    <p class="mis show_mis"><span class="n"><a id="t492" href="#t492">492</a></span><span class="t">    <span class="key">return</span> <span class="nam">_mongo_client</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:579:    <p class="pln"><span class="n"><a id="t497" href="#t497">497</a></span><span class="t"><span class="str">    Obtiene la base de datos MongoDB async.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:584:    <p class="mis show_mis"><span class="n"><a id="t502" href="#t502">502</a></span><span class="t">        <span class="key">raise</span> <span class="nam">RuntimeError</span><span class="op">(</span><span class="str">"MongoDB database not initialized. Use server.py connection."</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:590:    <p class="pln"><span class="n"><a id="t508" href="#t508">508</a></span><span class="t"><span class="str">    Obtiene la base de datos MongoDB s&#237;ncrona.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:593:    <p class="pln"><span class="n"><a id="t511" href="#t511">511</a></span><span class="t">    <span class="key">global</span> <span class="nam">_sync_mongo_client</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:594:    <p class="mis show_mis"><span class="n"><a id="t512" href="#t512">512</a></span><span class="t">    <span class="key">if</span> <span class="nam">_sync_mongo_client</span> <span class="key">is</span> <span class="key">None</span><span class="op">:</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:595:    <p class="mis show_mis"><span class="n"><a id="t513" href="#t513">513</a></span><span class="t">        <span class="key">raise</span> <span class="nam">RuntimeError</span><span class="op">(</span><span class="str">"Sync MongoDB client not initialized. Use server.py connection."</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:596:    <p class="mis show_mis"><span class="n"><a id="t514" href="#t514">514</a></span><span class="t">    <span class="key">return</span> <span class="nam">_sync_mongo_client</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:599:    <p class="run"><span class="n"><a id="t517" href="#t517">517</a></span><span class="t"><span class="key">def</span> <span class="nam">init_db_connections</span><span class="op">(</span><span class="nam">mongo_url</span><span class="op">:</span> <span class="nam">str</span><span class="op">,</span> <span class="nam">db_name</span><span class="op">:</span> <span class="nam">str</span><span class="op">)</span><span class="op">:</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:602:    <p class="pln"><span class="n"><a id="t520" href="#t520">520</a></span><span class="t"><span class="str">    NOTA: Se usar&#225; cuando se migre MongoDB desde server.py (fase futura)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:624:    <p class="run run2"><span class="n"><a id="t542" href="#t542">542</a></span><span class="t">    <span class="com"># MongoDB - Placeholders</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_db_py.html:625:    <p class="run run2"><span class="n"><a id="t543" href="#t543">543</a></span><span class="t">    <span class="str">'get_mongo_client'</span><span class="op">,</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_97abb2331ed8fa5c_service_py.html:131:    <p class="pln"><span class="n"><a id="t49" href="#t49">49</a></span><span class="t">    <span class="com"># Preparar documento para MongoDB</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_routes_py.html:121:    <p class="pln"><span class="n"><a id="t39" href="#t39">39</a></span><span class="t"><span class="str">los helpers que usan la conexi&#243;n global a MongoDB.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_config_py.html:93:    <p class="pln"><span class="n"><a id="t11" href="#t11">11</a></span><span class="t"><span class="str">    print(settings.MONGO_URL)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_config_py.html:107:    <p class="pln"><span class="n"><a id="t25" href="#t25">25</a></span><span class="t">    <span class="com"># MongoDB</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_config_py.html:108:    <p class="mis show_mis"><span class="n"><a id="t26" href="#t26">26</a></span><span class="t">    <span class="nam">MONGO_URL</span><span class="op">:</span> <span class="nam">str</span> <span class="op">=</span> <span class="nam">os</span><span class="op">.</span><span class="nam">environ</span><span class="op">.</span><span class="nam">get</span><span class="op">(</span><span class="str">"MONGO_URL"</span><span class="op">,</span> <span class="str">"mongodb://localhost:27017"</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_repository_py.html:90:    <p class="pln"><span class="n"><a id="t8" href="#t8">8</a></span><span class="t"><span class="str">- Acceso a MongoDB para configuraci&#243;n de servidores</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_repository_py.html:105:    <p class="pln"><span class="n"><a id="t23" href="#t23">23</a></span><span class="t"><span class="com"># INYECCI&#211;N DE DEPENDENCIA: MongoDB</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_repository_py.html:112:    <p class="pln"><span class="n"><a id="t30" href="#t30">30</a></span><span class="t">    <span class="str">"""Inicializa el repositorio con la conexi&#243;n a MongoDB."""</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_repository_py.html:118:    <p class="pln"><span class="n"><a id="t36" href="#t36">36</a></span><span class="t">    <span class="str">"""Obtiene la conexi&#243;n a MongoDB inyectada."""</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_repository_py.html:242:    <p class="pln"><span class="n"><a id="t160" href="#t160">160</a></span><span class="t"><span class="str">    Obtiene las metas de una sucursal desde MongoDB.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_repository_py.html:252:    <p class="pln"><span class="n"><a id="t170" href="#t170">170</a></span><span class="t"><span class="str">    Guarda las metas de una sucursal en MongoDB.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:91:    <p class="pln"><span class="n"><a id="t9" href="#t9">9</a></span><span class="t"><span class="str">- Fallback entre MongoDB y configuraci&#243;n hardcodeada</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:316:    <p class="pln"><span class="n"><a id="t234" href="#t234">234</a></span><span class="t">    <span class="com"># ========== BUSCAR APIs LOCALES DESDE MONGODB ==========</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:317:    <p class="mis show_mis"><span class="n"><a id="t235" href="#t235">235</a></span><span class="t">    <span class="nam">print</span><span class="op">(</span><span class="str">f"*** API Local: Buscando APIs tipo 'api_mpro' en MongoDB ***"</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:319:    <p class="mis show_mis"><span class="n"><a id="t237" href="#t237">237</a></span><span class="t">        <span class="key">from</span> <span class="nam">pymongo</span> <span class="key">import</span> <span class="nam">MongoClient</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:320:    <p class="mis show_mis"><span class="n"><a id="t238" href="#t238">238</a></span><span class="t">        <span class="nam">sync_client</span> <span class="op">=</span> <span class="nam">MongoClient</span><span class="op">(</span><span class="nam">os</span><span class="op">.</span><span class="nam">environ</span><span class="op">.</span><span class="nam">get</span><span class="op">(</span><span class="str">'MONGO_URL'</span><span class="op">,</span> <span class="str">'mongodb://localhost:27017'</span><span class="op">)</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:324:    <p class="mis show_mis"><span class="n"><a id="t242" href="#t242">242</a></span><span class="t">        <span class="nam">print</span><span class="op">(</span><span class="str">f"*** API Local: Encontradas {len(apis_locales_db)} APIs en MongoDB ***"</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:326:    <p class="mis show_mis"><span class="n"><a id="t244" href="#t244">244</a></span><span class="t">        <span class="nam">print</span><span class="op">(</span><span class="str">f"*** API Local: Error buscando en MongoDB: {e} ***"</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c_adapters_py.html:388:    <p class="mis show_mis"><span class="n"><a id="t306" href="#t306">306</a></span><span class="t">    <span class="nam">print</span><span class="op">(</span><span class="str">f"*** API Local: No encontrada en MongoDB, buscando en config hardcodeada ***"</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db___init___py.html:131:    <p class="run run2"><span class="n"><a id="t49" href="#t49">49</a></span><span class="t">    <span class="nam">MONGODB_COLLECTIONS</span><span class="op">,</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db___init___py.html:132:    <p class="run run2"><span class="n"><a id="t50" href="#t50">50</a></span><span class="t">    <span class="nam">MONGODB_INDEXES</span><span class="op">,</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/function_index.html:239:                <td class="name"><a href="z_57760688d1f824db_db_py.html#t484"><data value='get_mongo_client'>get_mongo_client</data></a></td>
backend/htmlcov/z_57760688d1f824db_security_py.html:96:    <p class="pln"><span class="n"><a id="t14" href="#t14">14</a></span><span class="t"><span class="str">- La conexi&#243;n a MongoDB se inyecta v&#237;a init_security()</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_security_py.html:124:    <p class="pln"><span class="n"><a id="t42" href="#t42">42</a></span><span class="t"><span class="com"># INYECCI&#211;N DE DEPENDENCIA: MongoDB</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_security_py.html:126:    <p class="pln"><span class="n"><a id="t44" href="#t44">44</a></span><span class="t"><span class="com"># La conexi&#243;n a MongoDB se inyecta desde server.py para evitar imports circulares</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_security_py.html:134:    <p class="pln"><span class="n"><a id="t52" href="#t52">52</a></span><span class="t"><span class="str">    Inicializa el m&#243;dulo de seguridad con la conexi&#243;n a MongoDB.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_security_py.html:142:    <p class="run"><span class="n"><a id="t60" href="#t60">60</a></span><span class="t">    <span class="nam">logging</span><span class="op">.</span><span class="nam">info</span><span class="op">(</span><span class="str">"[SECURITY] M&#243;dulo de seguridad inicializado con conexi&#243;n a MongoDB"</span><span class="op">)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_security_py.html:146:    <p class="pln"><span class="n"><a id="t64" href="#t64">64</a></span><span class="t">    <span class="str">"""Obtiene la conexi&#243;n a MongoDB inyectada."""</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_57760688d1f824db_security_py.html:241:    <p class="pln"><span class="n"><a id="t159" href="#t159">159</a></span><span class="t"><span class="str">    Extrae el token del header Authorization, lo verifica, y busca el usuario en MongoDB.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_97abb2331ed8fa5c___init___py.html:94:    <p class="pln"><span class="n"><a id="t12" href="#t12">12</a></span><span class="t"><span class="str">- repository.py: Acceso a MongoDB</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_97abb2331ed8fa5c___init___py.html:112:    <p class="pln"><span class="n"><a id="t30" href="#t30">30</a></span><span class="t"><span class="str">    Inicializa el m&#243;dulo de auth con la conexi&#243;n a MongoDB.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_6b2bb3a826453387___init___py.html:94:    <p class="pln"><span class="n"><a id="t12" href="#t12">12</a></span><span class="t"><span class="str">- repository.py: Acceso a MongoDB y SQL Server</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_6b2bb3a826453387___init___py.html:119:    <p class="pln"><span class="n"><a id="t37" href="#t37">37</a></span><span class="t"><span class="str">    Inicializa el m&#243;dulo de compras con la conexi&#243;n a MongoDB.</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_6b2bb3a826453387_repository_py.html:90:    <p class="pln"><span class="n"><a id="t8" href="#t8">8</a></span><span class="t"><span class="str">- Acceso a MongoDB para configuraci&#243;n de servidores</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_6b2bb3a826453387_repository_py.html:100:    <p class="pln"><span class="n"><a id="t18" href="#t18">18</a></span><span class="t"><span class="com"># INYECCI&#211;N DE DEPENDENCIA: MongoDB</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_6b2bb3a826453387_repository_py.html:107:    <p class="pln"><span class="n"><a id="t25" href="#t25">25</a></span><span class="t">    <span class="str">"""Inicializa el repositorio con la conexi&#243;n a MongoDB."""</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_6b2bb3a826453387_repository_py.html:113:    <p class="pln"><span class="n"><a id="t31" href="#t31">31</a></span><span class="t">    <span class="str">"""Obtiene la conexi&#243;n a MongoDB inyectada."""</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_6b2bb3a826453387_repository_py.html:129:    <p class="pln"><span class="n"><a id="t47" href="#t47">47</a></span><span class="t"><span class="com"># PAR&#193;METROS DE COMPRAS (MongoDB)</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c___init___py.html:94:    <p class="pln"><span class="n"><a id="t12" href="#t12">12</a></span><span class="t"><span class="str">- repository.py: Queries SQL y acceso a MongoDB</span>&nbsp;</span><span class="r"></span></p>
backend/htmlcov/z_342fa9d1c388b58c___init___py.html:130:    <p class="pln"><span class="n"><a id="t48" href="#t48">48</a></span><span class="t"><span class="str">    Inicializa el m&#243;dulo comercial con la conexi&#243;n a MongoDB.</span>&nbsp;</span><span class="r"></span></p>
backend/.env.test.example:32:# MongoDB para tests (opcional, usa mock por defecto)
backend/.env.test.example:33:# MONGO_URL=mongodb://localhost:27017
backend/migrations/cxp_sync_canonico_20260613.py:8:Idempotente. NO MongoDB. 100% SQL Server (EDARSAHUB).
backend/migrations/enrich_tiposervicio_detallepagos_20260613.py:20:NO USA MONGODB - 100% SQL Server (EDARSAHUB).
backend/migrations/sync_catalogo_canonico_20260612.py:15:NO USA MONGODB - 100% SQL Server (EDARSAHUB).
backend/sql/auditoria_financiera.sql:6:-- Ubicación: SQL Server EDARSA HUB (fuente oficial, NO MongoDB)
backend/.env:1:MONGO_URL="mongodb://localhost:27017"
backend/.env:39:# FASE 2-E: ACTIVADO - SQL es fuente primaria con fallback MongoDB
backend/.env:42:# Jobs deshabilitados temporalmente - Migración MongoDB->SQL incompleta
backend/api/catalogos_sistemas.py:23:- NO usar MongoDB
backend/api/admin_data_quality.py:13:- NO MongoDB
backend/api/admin_scheduler_resync.py:18:NO USA MONGODB - 100% SQL Server
backend/api/sync_receiver.py:59:    """Inicializa el módulo con la conexión a MongoDB."""
backend/api/sync_receiver.py:66:    """Obtiene la conexión a MongoDB."""
backend/api/sync_receiver.py:187:    server = await db.sql_servers.find_one({"id": payload.server_id})
backend/api/sync_receiver.py:232:    await db.sync_agent_registry.update_one(
backend/api/sync_receiver.py:276:    server = await db.sql_servers.find_one({"id": request.server_id})
backend/api/sync_receiver.py:286:    await db.sync_agent_registry.update_one(
backend/api/admin_core_connections.py:281:    # P5-3B-2: residual Mongo retirado. mongodb_id/mongo_synced eran no-op
backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:10:   No toca MongoDB
backend/database/migrations/023_rbac_inteligencia_comercial_matriz_ideal.sql:26:   - No toca MongoDB.
backend/database/migrations/007_crear_tabla_migracion_mongosql_mapeo.sql:2:   MIGRACIÓN: Tabla de Mapeo MongoDB -> SQL
backend/database/migrations/007_crear_tabla_migracion_mongosql_mapeo.sql:6:   Registra el estado de migración de colecciones MongoDB a tablas SQL.
backend/database/migrations/006_crear_vista_servidores_conexiones_publico.sql:61:    mongodb_id
backend/database/migrations/030_diagnostico_mapeo_rbac_mongo_a_sql.sql:2:   EDARSAHUB - DIAGNÓSTICO RBAC MongoDB → Usuario_* SQL
backend/database/migrations/030_diagnostico_mapeo_rbac_mongo_a_sql.sql:11:   - No tocar MongoDB
backend/database/migrations/030_diagnostico_mapeo_rbac_mongo_a_sql.sql:17:PRINT 'DIAGNÓSTICO RBAC MongoDB → Usuario_* SQL';
backend/database/migrations/030_diagnostico_mapeo_rbac_mongo_a_sql.sql:291:    'No se migraron usuarios. No se modificó MongoDB.' AS nota;
backend/core/server_registry.py:10:3. No usar MongoDB como fallback operativo
backend/core/server_registry.py:218:    Garantiza paridad con el esquema de MongoDB.
backend/core/server_registry.py:236:        'mongodb_id': str(row.get('mongodb_id', '')) if row.get('mongodb_id') else None,
backend/core/server_registry.py:331:    Busca tanto por id como por mongodb_id para compatibilidad.
backend/core/server_registry.py:341:        WHERE (CAST(id AS VARCHAR(50)) = '{safe_id}' OR mongodb_id = '{safe_id}')
backend/core/server_registry.py:382:    2. Sin fallback MongoDB operativo
backend/core/server_registry.py:388:        allow_mongo_fallback: Ignorado; MongoDB deshabilitado
backend/core/server_registry.py:400:    # MongoDB fallback deshabilitado por política SQL-only.
backend/core/server_registry.py:425:    2. Sin fallback MongoDB operativo
backend/core/server_registry.py:431:        allow_mongo_fallback: Ignorado; MongoDB deshabilitado
backend/core/server_registry.py:450:    # MongoDB fallback deshabilitado por política SQL-only.
backend/core/server_registry.py:487:    filtered = [s for s in servers if s.get('id') in allowed_ids or s.get('mongodb_id') in allowed_ids]
backend/core/server_registry.py:546:            if server.get('id') not in allowed and server.get('mongodb_id') not in allowed:
backend/core/server_registry.py:619:        db: Conexión MongoDB (opcional)
backend/core/server_registry.py:637:            if server.get('id') not in allowed and server.get('mongodb_id') not in allowed:
backend/core/server_registry.py:670:    2. MongoDB collection `server_sucursales_config` (fallback)
backend/core/server_registry.py:674:        db: Conexión a MongoDB
backend/core/server_registry.py:676:        allow_mongo_fallback: Ignorado; MongoDB deshabilitado
backend/core/server_registry.py:692:    # MongoDB fallback deshabilitado por política SQL-only.
backend/core/server_registry.py:740:        'mongodb_id': record.get('mongodb_id'),  # Mapeo a MongoDB si existe
backend/core/server_registry.py:914:    Crea un servidor en EDARSAHUB SQL primero, luego sincroniza a MongoDB.
backend/core/server_registry.py:916:    FASE 3B.1: SQL-first con sync a MongoDB como espejo legacy.
backend/core/server_registry.py:920:        db: Conexión MongoDB (para sync)
backend/core/server_registry.py:922:        sync_mongo: Si True, sincroniza a MongoDB después
backend/core/server_registry.py:958:        created_at, updated_at, mongodb_id
backend/core/server_registry.py:992:        server_id  # mongodb_id será el mismo inicialmente
backend/core/server_registry.py:1035:    Actualiza un servidor en EDARSAHUB SQL primero, luego sincroniza a MongoDB.
backend/core/server_registry.py:1037:    FASE 3B.1: SQL-first con sync a MongoDB como espejo legacy.
backend/core/server_registry.py:1040:        server_id: ID del servidor (SQL id o mongodb_id)
backend/core/server_registry.py:1042:        db: Conexión MongoDB (para sync y para obtener password existente)
backend/core/server_registry.py:1044:        sync_mongo: Si True, sincroniza a MongoDB después
backend/core/server_registry.py:1166:    update_values.append(server_id)  # Para mongodb_id fallback
backend/core/server_registry.py:1171:    WHERE CAST(id AS VARCHAR(50)) = %s OR mongodb_id = %s
backend/core/server_registry.py:1207:    Desactiva (soft delete) un servidor en EDARSAHUB SQL, luego sincroniza a MongoDB.
backend/core/server_registry.py:1209:    FASE 3B.1: SQL-first con sync a MongoDB como espejo legacy.
backend/core/server_registry.py:1214:        db: Conexión MongoDB (para sync)
backend/core/server_registry.py:1216:        sync_mongo: Si True, sincroniza a MongoDB después
backend/core/server_registry.py:1248:        WHERE CAST(id AS VARCHAR(50)) = %s OR mongodb_id = %s
backend/core/server_registry.py:1254:        WHERE CAST(id AS VARCHAR(50)) = %s OR mongodb_id = %s
backend/core/server_registry.py:1313:        'mongodb_id': sql_record.get('mongodb_id'),
backend/core/server_registry.py:1367:# MÁXIMA: EDARSAHUB es el cerebro del sistema. No usar MongoDB.
backend/core/server_registry.py:1417:    FASE M1: Fuente única EDARSAHUB, sin MongoDB.
backend/core/server_registry.py:1484:    FASE M1: EDARSAHUB es el cerebro del sistema. No usa MongoDB.
backend/core/server_registry.py:1926:    NO FUENTE: MongoDB db.servers
backend/core/server_registry.py:1936:        - id, mongodb_id, name, system_type
backend/core/server_registry.py:1949:        'mongodb_id': server.get('mongodb_id'),
backend/core/connection_resolver.py:277:        """MongoDB DEPRECADO - SQL Server es fuente única (P2-02)"""
backend/core/connection_resolver.py:278:        logger.warning("[ConnectionResolver] _get_db() llamado pero MongoDB está deprecado")
backend/core/connection_resolver.py:284:        P2-02: Migrado de MongoDB a SQL Server (Servidores_Conexiones).
backend/core/connection_resolver.py:330:        P2-02: Migrado de MongoDB a SQL Server (Servidores_Conexiones con tipo_conexion='API_LOCAL').
backend/core/pool.py:616:    NO requiere lógica de MongoDB - reemplazo directo.
backend/core/pool.py:626:        # Reemplaza: mongo_db.servers.find()
backend/core/pool.py:629:        # Reemplaza: mongo_db.ventas.find({"sucursal_id": id})
backend/core/pool.py:661:    Equivalente a mongo_db.collection.find_one()
backend/core/__init__.py:57:    MONGODB_COLLECTIONS,
backend/core/__init__.py:58:    MONGODB_INDEXES,
backend/core/source_resolver.py:98:        source_type: Tipo de fuente (MPRO, SoftRestaurant, MongoDB, API)
backend/core/source_resolver.py:143:        """Serializa a diccionario para JSON/MongoDB."""
backend/core/auditoria.py:9:guardan temporalmente en MongoDB como fallback y se sincronizan después.
backend/core/auditoria.py:188:        """Retorna documento para MongoDB."""
backend/core/auditoria.py:202:    Fallback a MongoDB si SQL no está disponible.
backend/core/auditoria.py:224:        """P5-3D: MongoDB retirado (NO-MONGO). La auditoría persiste en SQL. Retorna None."""
backend/core/auditoria.py:395:        """Guarda en MongoDB como fallback."""
backend/core/auditoria.py:401:            await db.auditoria_financiera.insert_one(evento.to_mongo_doc())
backend/core/auditoria.py:405:            logger.error(f"Error escribiendo auditoría a MongoDB: {e}")
backend/core/empresa_resolver.py:11:NO CONSULTA: MongoDB
backend/core/unidades_registry.py:19:- NO usar MongoDB como fuente funcional
backend/core/security.py:36:- La conexión a MongoDB se inyecta vía init_security()
backend/core/security.py:78:# Valor por defecto: false (MongoDB sigue siendo la fuente productiva)
backend/core/security.py:83:# INYECCIÓN DE DEPENDENCIA: MongoDB
backend/core/security.py:85:# La conexión a MongoDB se inyecta desde server.py para evitar imports circulares
backend/core/security.py:93:    Inicializa el módulo de seguridad con la conexión a MongoDB.
backend/core/security.py:107:        logging.info("[SECURITY] Módulo de seguridad inicializado con conexión a MongoDB")
backend/core/security.py:111:    """Obtiene la conexión a MongoDB inyectada."""
backend/core/security.py:284:    FASE 2-G: SQL-only (sin fallback MongoDB).
backend/core/security.py:305:    # FASE 2-G: SQL-only (sin fallback MongoDB)
backend/core/security.py:332:    Sin fallback a MongoDB.
backend/core/security.py:450:    # FASE 2-G: SQL-only (sin fallback MongoDB)
backend/core/security.py:500:        Lista de empresa_ids permitidos (UUIDs MongoDB para compatibilidad)
backend/core/security.py:553:        # Construir IN clause para empresas (UUIDs MongoDB)
backend/core/security.py:739:    # FASE 2-G: SQL-Only (sin fallback MongoDB)
backend/core/security.py:750:# - MongoDB sigue siendo la fuente de autenticación
backend/core/security.py:776:    FASE 2-D.1: Comparación pasiva MongoDB vs SQL.
backend/core/security.py:782:        user_mongo: Usuario obtenido de MongoDB (actual productivo)
backend/core/security.py:792:        'auth_source': 'MONGODB_CURRENT',
backend/core/security.py:796:        'mongo': _safe_user_for_log(user_mongo, 'MONGODB'),
backend/core/security.py:815:        # ID (PublicUUID vs MongoDB id)
backend/core/security.py:877:        user_mongo: Usuario de MongoDB
backend/core/rbac_helper.py:8:- NO MongoDB. Sin dependencia del stub legacy.
backend/core/scheduler/scheduler_manager.py:100:            logger.info("[SCHEDULER] Inicializando con StubDatabase - MongoDB ELIMINADO")
backend/core/scheduler/sql_repository.py:5:Funciones SQL para los jobs del scheduler (reemplazo de MongoDB).
backend/core/scheduler/jobs/pedidos_detector_job.py:876:        from modules.fase2_operativo.db_utils import get_database
backend/core/scheduler/jobs/pedidos_detector_job.py:881:        db_sync = get_database()
backend/core/scheduler/jobs/inteligencia_comercial_enrich.py:18:NO toca KPIs canónicos. NO imprime secretos. NO usa MongoDB.
backend/core/scheduler/jobs/notifications_job.py:121:        count = await self.db.notification_queue.count_documents({
backend/core/scheduler/jobs/cxp_sync_job.py:11:NO MongoDB. NO toca KPIs canónicos.
backend/core/scheduler/routes.py:39:    NOTA: MongoDB ELIMINADO del sistema. Este módulo ahora opera con StubDatabase
backend/core/scheduler/routes.py:47:        logger.info("[SCHEDULER_ROUTES] Inicializado con StubDatabase - MongoDB ELIMINADO")
backend/core/sql_first/no_mongo.py:6:P2-05: Bloquea uso de MongoDB en runtime productivo.
backend/core/sql_first/no_mongo.py:7:Importar en lugar de pymongo para forzar migración a SQL.
backend/core/sql_first/no_mongo.py:11:    """Excepción cuando se intenta usar MongoDB en runtime SQL-First."""
backend/core/sql_first/no_mongo.py:15:    """Función que lanza error cuando se intenta usar MongoDB."""
backend/core/sql_first/no_mongo.py:17:        "MongoDB está deshabilitado en runtime productivo EDARSAHUB. "
backend/core/sql_first/no_mongo.py:21:# Stubs para reemplazar imports de pymongo
backend/core/sql_first/no_mongo.py:23:AsyncIOMotorClient = mongo_disabled
backend/core/cache_key_builder.py:176:        server_id: ID del servidor (SQL id o mongodb_id)
backend/core/config.py:13:    # print(settings.MONGO_DISABLED)  # P2-07: MongoDB eliminado
backend/core/config.py:27:    # MongoDB
backend/core/config.py:28:    MONGO_DISABLED: str = ""  # P2-07: MongoDB eliminado
backend/core/communications/dispatcher/dispatcher.py:48:    - Operaciones de MongoDB pasan por StubDatabase
backend/core/communications/dispatcher/dispatcher.py:106:            logger.info("[DISPATCHER] Modo SQL-only: omitiendo carga de providers desde MongoDB")
backend/core/communications/dispatcher/dispatcher.py:110:            providers = await self.db.notification_provider_config.find(
backend/core/communications/notifications/service.py:47:    - Operaciones de MongoDB pasan por StubDatabase
backend/core/communications/notifications/service.py:251:        user = await self.db.users.find_one(
backend/core/communications/notifications/schemas.py:8:Colecciones MongoDB:
backend/core/communications/audit/audit_service.py:28:    - Operaciones de MongoDB pasan por StubDatabase
backend/core/communications/audit/audit_service.py:182:        cursor = self.db.notification_log.aggregate(pipeline)
backend/core/communications/scripts/__init__.py:330:        existing = await db.notification_config.find_one({"id": config["id"]})
backend/core/communications/scripts/__init__.py:333:            await db.notification_config.insert_one(config)
backend/core/communications/scripts/__init__.py:339:    existing = await db.notification_provider_config.find_one({"id": DEFAULT_PROVIDER_CONFIG["id"]})
backend/core/communications/scripts/__init__.py:342:        await db.notification_provider_config.insert_one(DEFAULT_PROVIDER_CONFIG)
backend/core/communications/scripts/__init__.py:349:        existing = await db.notification_templates.find_one({"id": template["id"]})
backend/core/communications/scripts/__init__.py:352:            await db.notification_templates.insert_one(template)
backend/core/communications/scripts/__init__.py:363:        db: Conexión a MongoDB
backend/core/communications/scripts/__init__.py:379:    El sistema de notificaciones ya no depende de MongoDB."""
backend/core/communications/routes.py:40:# INYECCIÓN DE DEPENDENCIA: MongoDB
backend/core/communications/routes.py:48:    Inicializa las rutas con la conexión a MongoDB.
backend/core/communications/routes.py:50:    NOTA: MongoDB ELIMINADO del sistema. Este módulo ahora opera con StubDatabase
backend/core/communications/routes.py:61:        logger.info("[NOTIFICATIONS] Inicializado con StubDatabase - MongoDB ELIMINADO")
backend/core/communications/routes.py:68:    Obtiene la conexión a MongoDB inyectada.
backend/core/communications/routes.py:77:    Verifica si MongoDB real está disponible.
backend/core/communications/routes.py:164:    config = await db.notification_config.find_one({"id": config_id}, {"_id": 0})
backend/core/communications/routes.py:497:    providers = await db.notification_provider_config.find(
backend/core/communications/routes.py:512:    provider = await db.notification_provider_config.find_one(
backend/core/communications/routes.py:671:    result = await db.notification_provider_config.update_one(
backend/core/communications/routes.py:713:    result = await db.notification_config.update_one(
backend/core/communications/routes.py:728:    config = await db.notification_config.find_one({"id": config_id}, {"_id": 0})
backend/core/context_resolver.py:36:Este módulo ha sido migrado de MongoDB a EDARSAHUB SQL.
backend/core/context_resolver.py:44:MongoDB ya no es fuente de datos para resolución de contexto.
backend/core/context_resolver.py:85:    por UUIDs de MongoDB (empresas_permitidas del usuario).
backend/core/context_resolver.py:89:        empresa_uuids: Lista de UUIDs MongoDB de empresas
backend/core/context_resolver.py:337:    Obtiene una empresa por UUID MongoDB desde Sistema_Empresas.
backend/core/context_resolver.py:341:        empresa_uuid: UUID MongoDB de la empresa
backend/core/context_resolver.py:380:    MIGRACIÓN FASE 3-C: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
backend/core/context_resolver.py:387:        - id: ID de la empresa (UUID MongoDB)
backend/core/context_resolver.py:397:    # 1. Obtener empresas permitidas (UUIDs MongoDB)
backend/core/context_resolver.py:430:            empresa_id = empresa['id']  # UUID MongoDB
backend/core/context_resolver.py:447:                    'id': empresa_id,  # UUID MongoDB (compatibilidad)
backend/core/context_resolver.py:472:    MIGRACIÓN FASE 3-C: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
backend/core/context_resolver.py:476:        unidad_id: ID de la unidad de negocio (empresa_id UUID MongoDB)
backend/core/context_resolver.py:527:    MIGRACIÓN FASE 3-C: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
backend/core/context_resolver.py:576:            empresa_id = sucursal_info.get('empresa_id')  # UUID MongoDB
backend/core/user_access_context.py:41:Este módulo ha sido migrado de MongoDB a EDARSAHUB SQL.
backend/core/user_access_context.py:56:MongoDB ya no es fuente de datos para resolución de acceso.
backend/core/user_access_context.py:188:    Obtiene todas las empresas activas (UUIDs MongoDB) para acceso global.
backend/core/user_access_context.py:215:    Obtiene empresas asignadas al usuario (UUIDs MongoDB).
backend/core/user_access_context.py:258:    Traduce empresas (UUIDs MongoDB) a servidores vía mapeos SQL.
backend/core/user_access_context.py:334:    MIGRACIÓN FASE 3-D: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
backend/core/user_access_context.py:486:        # Todas las empresas activas (UUIDs MongoDB)
backend/core/centro_control/email_notifications.py:9:1. MongoDB (colección alert_recipients) - Prioridad
backend/core/centro_control/email_notifications.py:58:    Prioridad: MongoDB > Variable de entorno
backend/core/centro_control/email_notifications.py:60:    # Intentar obtener de MongoDB primero
backend/core/centro_control/email_notifications.py:67:        logger.debug(f"[EMAIL] No se pudo obtener recipients de MongoDB: {e}")
backend/core/centro_control/whatsapp_notifications.py:9:1. MongoDB (colección alert_recipients) - Prioridad
backend/core/centro_control/whatsapp_notifications.py:67:    Prioridad: MongoDB > Variable de entorno
backend/core/centro_control/whatsapp_notifications.py:69:    # Intentar obtener de MongoDB primero
backend/core/centro_control/whatsapp_notifications.py:76:        logger.debug(f"[WHATSAPP] No se pudo obtener recipients de MongoDB: {e}")
backend/core/centro_control/routes.py:613:    - MongoDB (EDARSA HUB)
backend/core/centro_control/routes.py:1629:    Los destinatarios se almacenan en MongoDB y son utilizados por los
backend/core/mongo_stub.py:4:EDARSA HUB - MongoDB Stub Database
backend/core/mongo_stub.py:6:Implementación stub de MongoDB que no falla cuando se accede a colecciones.
backend/core/mongo_stub.py:8:Este módulo proporciona un objeto 'db' que simula la interfaz de MongoDB
backend/core/mongo_stub.py:23:    Colección stub que simula una colección de MongoDB.
backend/core/mongo_stub.py:34:            logger.debug(f"[MONGO_STUB] Acceso a colección '{self.name}' - MongoDB eliminado")
backend/core/mongo_stub.py:100:    Cursor stub que simula un cursor de MongoDB.
backend/core/mongo_stub.py:172:    Base de datos stub que simula una base de datos de MongoDB.
backend/core/mongo_stub.py:186:            logger.info("[MONGO_STUB] Base de datos stub activa - MongoDB ELIMINADO")
backend/core/cerebro.py:10:- Esquemas de MongoDB
backend/core/cerebro.py:661:# MAPEO DE COLECCIONES MONGODB
backend/core/cerebro.py:664:MONGODB_COLLECTIONS = {
backend/core/cerebro.py:709:# ÍNDICES MONGODB REQUERIDOS
backend/core/cerebro.py:712:MONGODB_INDEXES = {
backend/core/cerebro.py:789:    'MONGODB_COLLECTIONS', 'MONGODB_INDEXES',
backend/core/auth/user_repository_sql.py:10:- NO reemplaza el flujo actual de MongoDB
backend/core/auth/user_repository_sql.py:12:- MongoDB sigue siendo la fuente productiva de autenticación
backend/core/auth/user_repository_sql.py:133:        Construye diccionario de usuario compatible con estructura MongoDB.
backend/core/auth/user_repository_sql.py:141:        # Mapeo de rol SQL a rol MongoDB
backend/core/auth/user_repository_sql.py:158:            # Campos compatibles con MongoDB
backend/core/auth/user_repository_sql.py:194:            Dict con estructura compatible MongoDB o None si no existe
backend/core/auth/user_repository_sql.py:239:            Dict con estructura compatible MongoDB o None si no existe
backend/core/auth/user_repository_sql.py:338:# FUNCIONES DE COMPARACIÓN MONGODB VS SQL
backend/core/auth/user_repository_sql.py:343:    Compara usuario entre MongoDB y SQL.
backend/core/auth/user_repository_sql.py:351:    pass  # P2-07: MongoDB eliminado (AsyncIOMotorClient)
backend/core/auth/user_repository_sql.py:357:    # Obtener de MongoDB
backend/core/auth/user_repository_sql.py:358:    mongo_url = None  # P2-07: MongoDB eliminado
backend/core/auth/user_repository_sql.py:360:    mongo_client = None  # P2-07: MongoDB eliminado
backend/core/auth/user_repository_sql.py:361:    mongo_db = mongo_client[db_name]
backend/core/auth/user_repository_sql.py:363:    user_mongo = await mongo_db.users.find_one({'email': email}, {'_id': 0})
backend/core/auth/user_repository_sql.py:365:    mongo_client.close()
backend/core/auth/user_repository_sql.py:470:    Lista diferencias de migración Auth entre MongoDB y SQL para todos los usuarios SQL.
backend/core/auth/user_repository_sql.py:582:    # Mapeo de rol MongoDB a SQL
backend/core/auth/user_repository_sql.py:896:    Reemplaza la función find_user_by_email de MongoDB.
backend/core/auth/user_repository_sql.py:917:    Reemplaza la función find_user_by_id de MongoDB.
backend/core/health_checker.py:43:    MONGODB = "mongodb"
backend/core/health_checker.py:150:    def _check_mongodb(self) -> SourceHealth:
backend/core/health_checker.py:151:        """MongoDB eliminado del camino productivo. Se reporta solo como residual deshabilitado."""
backend/core/health_checker.py:153:            name="MongoDB (EDARSA HUB)",
backend/core/health_checker.py:154:            source_type=SourceType.MONGODB,
backend/core/health_checker.py:156:            last_error="MongoDB eliminado del flujo productivo (SQL-First / NO-MONGO)"
backend/core/health_checker.py:191:        # Verificar MongoDB
backend/core/health_checker.py:192:        mongo_health = self._check_mongodb()
backend/core/rbac/__init__.py:9:MongoDB ya NO es fuente de datos para RBAC.
backend/core/rbac/repository_sql.py:183:                    "nombre": codigo,  # Usar código como nombre (compatible con MongoDB)
backend/core/rbac/repository.py:9:MongoDB ya NO es fuente de datos para RBAC.
backend/core/rbac/routes.py:48:    """Obtiene conexión a MongoDB de forma síncrona."""
backend/core/rbac/routes.py:49:    mongo_url = None  # P2-07: MongoDB eliminado
backend/core/rbac/routes.py:51:    client = None  # P2-07: MongoDB eliminado
backend/core/rbac/schemas.py:8:Colecciones MongoDB:
backend/core/alcance_helper.py:178:        db: Instancia de la base de datos MongoDB
backend/core/object_storage.py:6:NO en MongoDB. No hay API de borrado: el borrado es logico en SQL.
backend/core/system_capability_resolver.py:43:- NO usar MongoDB
backend/core/inventory_analysis_core.py:20:- db: Cliente MongoDB (inyectado)
backend/core/inventory_analysis_core.py:129:            db_client: Cliente de base de datos MongoDB
backend/core/inventory_analysis_core.py:226:        db_client: Cliente MongoDB
backend/core/db.py:608:    raise RuntimeError("MongoDB no es fuente productiva. Usar SQL Server.")
backend/routes/portal_proveedores.py:4:SQL-only: usa tablas canónicas EDARSA HUB; MongoDB/LIVE deshabilitado
```

## 3. Server registry / server.py focal
```
backend/server.py:2132:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:2139:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}))
backend/server.py:2227:    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:2229:    NO FUENTE: MongoDB db.servers
backend/server.py:2252:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:2334:    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:2336:    NO FUENTE: MongoDB db.servers
backend/server.py:2350:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:2365:    # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {field_name: query_config}})
backend/server.py:2378:    # ANTES: updated_server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}, {"_id": 0}))
backend/server.py:2387:        # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {"queries_configured": all_configured}})
backend/server.py:2411:    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:2413:    NO FUENTE: MongoDB db.servers
backend/server.py:2418:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:2470:    FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:2472:    NO FUENTE: MongoDB db.servers
backend/server.py:2480:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:2487:    # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {field_name: None, "queries_configured": False}})
backend/server.py:3073:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3081:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:3192:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3204:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:3312:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3317:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:3346:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3354:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:3491:    Migrado de db.servers.find() a server_registry.list_servers()
backend/server.py:3497:    # ANTES: server_cursor = db.servers.find({"id": {"$in": server_ids}}, {"_id": 0, "id": 1, "name": 1})
backend/server.py:3681:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3693:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:3755:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3767:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:3872:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:3893:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:4225:    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:4227:    NO FUENTE: MongoDB db.servers
backend/server.py:4297:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:5589:    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:5591:    NO FUENTE: MongoDB db.servers
backend/server.py:5603:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:5845:    FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:5847:    NO FUENTE: MongoDB db.servers
backend/server.py:5858:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:6416:    FASE P1.4-E3 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:6418:    NO FUENTE: MongoDB db.servers
backend/server.py:6430:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
backend/server.py:6690:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:6699:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:6756:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:6776:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:6914:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:6924:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:7231:    FASE P1.4-E2 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:7233:    NO FUENTE: MongoDB db.servers
backend/server.py:7254:        # ANTES: server = decrypt_server_secrets(await db.servers.find_one(query))
backend/server.py:7469:    Migrado de db.servers.find() a server_registry.list_servers()
backend/server.py:7472:    # ANTES: servers = await db.servers.find({"active": True, "queries_configured": True}, {...}).to_list(100)
backend/server.py:7502:    # ANTES: total_servers = await db.servers.count_documents({"active": True})
backend/server.py:7503:    # ANTES: servers_configured = await db.servers.count_documents({"active": True, "queries_configured": True})
backend/server.py:7589:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:7628:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:8790:    # FASE T3.3: Migrado de db.servers a server_registry (EDARSAHUB)
backend/server.py:9098:    FASE P1.4-E1 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:9100:    NO FUENTE: MongoDB db.servers
backend/server.py:9113:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
backend/server.py:10048:    # FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
backend/server.py:10680:    # FASE T3.3: Migrado de db.servers a server_registry (EDARSAHUB)
backend/server.py:10836:    # FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
backend/server.py:10907:    # FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
backend/server.py:11975:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:11979:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:12146:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:12156:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:12200:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:12216:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:13255:    FASE P1.4-E4 (Dic 2025): Migrado de MongoDB db.servers a server_registry.
backend/server.py:13257:    NO FUENTE: MongoDB db.servers
backend/server.py:13265:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:13901:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:13906:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:14153:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:14368:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:14391:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))
backend/server.py:14435:    Migrado de db.servers.find_one() a server_registry.get_server_connection_info()
backend/server.py:14449:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))
backend/core/server_registry.py:1926:    NO FUENTE: MongoDB db.servers
```

## 4. Graphify estado
```
48M	graphify-out
archivos graphify-out: 1433
Sin cambios pendientes Graphify
```

## 5. Compilación
```
COMPILE_OK
```
