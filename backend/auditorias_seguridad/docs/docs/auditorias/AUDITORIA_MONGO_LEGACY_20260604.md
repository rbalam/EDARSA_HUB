# AUDITORÍA MONGO LEGACY — EDARSAHUB

Fecha: 2026-06-04 23:55:46

Objetivo: localizar referencias MongoDB/pymongo/motor y clasificarlas para eliminación o justificación temporal.

## Resumen

- Hallazgos totales: **1254**
- Riesgo alto: **1069**
- Revisar permitido temporal: **185**

## Hallazgos RIESGO_ALTO

| Archivo | Línea | Código |
|---|---:|---|
| `backend/init_queries.py` | 4 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/init_queries.py` | 10 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/init_queries.py` | 266 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/migrar_a_sql.py` | 24 | `if 'pymongo' not in linea and 'motor' not in linea:` |
| `backend/migrar_a_sql.py` | 26 | `print("✅ Limpiado: requirements.txt (eliminado pymongo/motor)")` |
| `backend/migrar_a_sql.py` | 28 | `# 3. Centralización del motor SQL en db.py` |
| `backend/server.py` | 74 | `# MongoDB import movido a bloque condicional más abajo` |
| `backend/server.py` | 107 | `# MÁXIMA EDARSAHUB: SQL Server es el cerebro. MongoDB ELIMINADO.` |
| `backend/server.py` | 111 | `# Los accesos a colecciones MongoDB retornan valores vacíos sin fallar.` |
| `backend/server.py` | 118 | `logger.info("[DB] Sistema funcionando 100% SQL Server - MongoDB ELIMINADO (usando StubDatabase)")` |
| `backend/server.py` | 288 | `init_security(None)  # MongoDB eliminado` |
| `backend/server.py` | 366 | `Descifra los secretos de un servidor obtenido de MongoDB/SQL.` |
| `backend/server.py` | 439 | `init_compras_module(None)  # MongoDB eliminado` |
| `backend/server.py` | 466 | `init_comercial_module(None)  # MongoDB eliminado` |
| `backend/server.py` | 481 | `# FASE 1C-3I-B: Motor de Precios Sugeridos y Benchmark Competitivo` |
| `backend/server.py` | 544 | `# - Fuente única: EDARSAHUB (no MongoDB)` |
| `backend/server.py` | 579 | `init_manuales_module(None)  # MongoDB eliminado` |
| `backend/server.py` | 582 | `init_rh_module(None)  # MongoDB eliminado` |
| `backend/server.py` | 585 | `init_catalogos_module(None)  # MongoDB eliminado` |
| `backend/server.py` | 586 | `init_catalogos_service(None)  # MongoDB eliminado` |
| `backend/server.py` | 589 | `_finanzas_repo = FinanzasRepositoryReal(None)  # MongoDB eliminado` |
| `backend/server.py` | 594 | `_mpro_repo = FinanzasRepositoryMPRO(None)  # MongoDB eliminado` |
| `backend/server.py` | 598 | `_softrest_repo = FinanzasRepositorySoftRestaurant(None)  # MongoDB eliminado` |
| `backend/server.py` | 624 | `# FUENTE: EDARSAHUB (no MongoDB)` |
| `backend/server.py` | 636 | `# NO usa MongoDB` |
| `backend/server.py` | 664 | `init_sync_receiver(None)  # MongoDB eliminado` |
| `backend/server.py` | 665 | `init_kpis_repository(None)  # MongoDB eliminado` |
| `backend/server.py` | 674 | `init_api_connections_repository(None)  # MongoDB eliminado` |
| `backend/server.py` | 1878 | `FASE 3B.1: Crea servidor en EDARSAHUB SQL primero, sincroniza a MongoDB.` |
| `backend/server.py` | 1882 | `- Si MongoDB sync falla, devuelve PARTIAL_SYNC` |
| `backend/server.py` | 1989 | `FASE 3B.1: Actualiza servidor en EDARSAHUB SQL primero, sincroniza a MongoDB.` |
| `backend/server.py` | 1993 | `- Si MongoDB sync falla, devuelve PARTIAL_SYNC` |
| `backend/server.py` | 2047 | `FASE 3B.1: Desactiva servidor en EDARSAHUB SQL primero, sincroniza a MongoDB.` |
| `backend/server.py` | 2052 | `- Si MongoDB sync falla, devuelve PARTIAL_SYNC` |
| `backend/server.py` | 2325 | `FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/server.py` | 2327 | `NO FUENTE: MongoDB db.servers` |
| `backend/server.py` | 2432 | `FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/server.py` | 2434 | `NO FUENTE: MongoDB db.servers` |
| `backend/server.py` | 2469 | `sync_mongo=True  # Mantener espejo MongoDB para compatibilidad` |
| `backend/server.py` | 2509 | `FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/server.py` | 2511 | `NO FUENTE: MongoDB db.servers` |
| `backend/server.py` | 2568 | `FASE P1.4-B (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/server.py` | 2570 | `NO FUENTE: MongoDB db.servers` |
| `backend/server.py` | 2615 | `- No usar MongoDB` |
| `backend/server.py` | 2738 | `NO consulta MongoDB.` |
| `backend/server.py` | 2775 | `NO consulta MongoDB.` |
| `backend/server.py` | 3364 | `MongoDB NO se usa como fuente, ni como fallback, ni como respaldo.` |
| `backend/server.py` | 3931 | `FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/server.py` | 3933 | `NO FUENTE: MongoDB db.servers` |
| `backend/server.py` | 4116 | `FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/server.py` | 4118 | `NO FUENTE: MongoDB db.servers` |
| `backend/server.py` | 4786 | `orquestador = get_orquestador_service(db)  # MongoDB ELIMINADO - StubDatabase` |
| `backend/server.py` | 5430 | `orquestador = get_orquestador_service(db)  # MongoDB ELIMINADO - StubDatabase` |
| `backend/server.py` | 5480 | `FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/server.py` | 5482 | `NO FUENTE: MongoDB db.servers` |
| `backend/server.py` | 5736 | `FASE P1.4-C (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/server.py` | 5738 | `NO FUENTE: MongoDB db.servers` |
| `backend/server.py` | 6307 | `FASE P1.4-E3 (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/server.py` | 6309 | `NO FUENTE: MongoDB db.servers` |
| `backend/server.py` | 7120 | `FASE P1.4-E2 (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/server.py` | 7122 | `NO FUENTE: MongoDB db.servers` |
| `backend/server.py` | 7352 | `NOTA: db.users y db.alerts aún usan MongoDB (fuera del alcance de P1.4-E4).` |
| `backend/server.py` | 7363 | `# NOTA: db.users y db.alerts aún usan MongoDB (migración en Fase 2)` |
| `backend/server.py` | 7447 | `FASE 2-G FIX: Usar get_current_user que busca en SQL en lugar de db.users (MongoDB)` |
| `backend/server.py` | 7458 | `# FASE 2-G FIX: Usar get_current_user (SQL-only) en lugar de db.users (MongoDB)` |
| `backend/server.py` | 9019 | `FASE P1.4-E1 (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/server.py` | 9021 | `NO FUENTE: MongoDB db.servers` |
| `backend/server.py` | 11550 | `- No usa MongoDB` |
| `backend/server.py` | 12492 | `# Guardar log en MongoDB` |
| `backend/server.py` | 12588 | `"""Crea un nuevo informe de auditoría y lo guarda en MongoDB"""` |
| `backend/server.py` | 12642 | `# Guardar en MongoDB` |
| `backend/server.py` | 12690 | `{"_id": 0}  # Excluir _id de MongoDB` |
| `backend/server.py` | 12812 | `# Eliminar de MongoDB` |
| `backend/server.py` | 12929 | `# Eliminar de MongoDB` |
| `backend/server.py` | 14176 | `NOTA: La escritura del script pendiente permanece en MongoDB como documento` |
| `backend/server.py` | 14202 | `# Guardar en MongoDB como documento operativo temporal` |
| `backend/server.py` | 14308 | `FASE P1.4-E4 (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/server.py` | 14310 | `NO FUENTE: MongoDB db.servers` |
| `backend/server.py` | 14332 | `# Si hay script_id, cargar el script de MongoDB` |
| `backend/server.py` | 15131 | `Incluye consultas predefinidas y personalizadas (MongoDB).` |
| `backend/server.py` | 15151 | `# Agregar consultas personalizadas desde MongoDB` |
| `backend/server.py` | 15323 | `# CRUD CONSULTAS PERSONALIZADAS (MongoDB)` |
| `backend/server.py` | 15328 | `"""Lista todas las consultas personalizadas guardadas en MongoDB"""` |
| `backend/server.py` | 15511 | `# Buscar consulta en MongoDB` |
| `backend/server.py` | 16286 | `# Obtener configuración personalizada de niveles desde MongoDB` |
| `backend/server.py` | 17176 | `-- Base de datos: EDARSA HUB (Opcional - Las tareas se guardan en MongoDB)` |
| `backend/server.py` | 17180 | `-- El sistema principal usa MongoDB para las tareas` |
| `backend/server.py` | 17207 | `"nota": "Este script es OPCIONAL. El sistema de tareas funciona con MongoDB. Use este script solo si desea mantener un l...` |
| `backend/server.py` | 17284 | `# Limpiar _id de MongoDB` |
| `backend/server.py` | 17734 | `-- NOTA: Las tablas principales se manejan en MongoDB.` |
| `backend/server.py` | 17802 | `CicloID NVARCHAR(50) NOT NULL, -- ID del ciclo en MongoDB` |
| `backend/server.py` | 17822 | `"nota": "Este script es OPCIONAL. El sistema de nóminas funciona principalmente con MongoDB. Use estas tablas para integ...` |
| `backend/server.py` | 17905 | `service = get_estructura_service(db)  # MongoDB ELIMINADO - StubDatabase` |
| `backend/server.py` | 17947 | `service = get_estructura_service(db)  # MongoDB ELIMINADO - StubDatabase` |
| `backend/server.py` | 17968 | `service = get_estructura_service(db)  # MongoDB ELIMINADO - StubDatabase` |
| `backend/server.py` | 19126 | `# MongoDB ELIMINADO - Este handler ya no es necesario` |
| `backend/server.py` | 19127 | `# La variable 'client' ya no existe (era el cliente de MongoDB)` |
| `backend/server.py` | 19138 | `init_notifications_routes(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad` |
| `backend/server.py` | 19144 | `init_scheduler_routes(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad` |
| `backend/server.py` | 19185 | `rbac_service = RBACService(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad` |
| `backend/server.py` | 19403 | `await start_scheduler(db)  # MongoDB ELIMINADO - StubDatabase para compatibilidad` |
| `backend/modules/comercial/service.py` | 77 | `# NO consulta servidores locales ni MongoDB para KPIs.` |
| `backend/modules/comercial/service.py` | 93 | `# NO usar MongoDB como fuente funcional para unidades.` |
| `backend/modules/comercial/service.py` | 102 | `NO usa MongoDB.` |
| `backend/modules/comercial/service.py` | 180 | `NO usa MongoDB.` |
| `backend/modules/comercial/service.py` | 201 | `# Si no se encuentra, retornar estructura vacía (no usar MongoDB)` |
| `backend/modules/comercial/service.py` | 477 | `NO usa MongoDB. NO usa servidores locales.` |
| `backend/modules/comercial/service.py` | 804 | `- NO consulta MongoDB` |
| `backend/modules/comercial/service.py` | 1185 | `- NO usa MongoDB servers.name como nombre oficial` |
| `backend/modules/comercial/service.py` | 1197 | `# NO usar MongoDB servers.name como nombre funcional/oficial` |
| `backend/modules/comercial/service.py` | 1366 | `# - NO consultan MongoDB como fuente de datos` |
| `backend/modules/comercial/service.py` | 1377 | `- NO consulta MongoDB` |
| `backend/modules/comercial/service.py` | 1381 | `- NO usa MongoDB servers.name como nombre oficial` |
| `backend/modules/comercial/service.py` | 1394 | `# NO usar MongoDB servers.name como nombre oficial` |
| `backend/modules/comercial/service.py` | 1507 | `- NO consulta MongoDB` |
| `backend/modules/comercial/service.py` | 2379 | `NO consulta: MongoDB` |
| `backend/modules/comercial/routes_pricing_ai.py` | 16 | `- NO usar MongoDB` |
| `backend/modules/comercial/routes_pricing_ai.py` | 396 | `"mongodb": False,` |
| `backend/modules/comercial/routes_pricing_ai.py` | 432 | `- NO usa MongoDB` |
| `backend/modules/comercial/__init__.py` | 12 | `- repository.py: Queries SQL y acceso a MongoDB` |
| `backend/modules/comercial/__init__.py` | 53 | `Inicializa el módulo comercial con la conexión a MongoDB.` |
| `backend/modules/comercial/__init__.py` | 56 | `database: Instancia de AsyncIOMotorDatabase` |
| `backend/modules/comercial/routes_precios_sugeridos.py` | 11 | `- CERO MongoDB` |
| `backend/modules/comercial/crm_router.py` | 202 | `# Nota: Se asume que el sistema genera el folio secuencial o via el motor SQL.` |
| `backend/modules/comercial/inteligencia_comercial_routes.py` | 11 | `- No usa MongoDB como fuente de datos comerciales.` |
| `backend/modules/comercial/inteligencia_comercial_routes.py` | 51 | `NO conecta a SoftRestaurant, MPRO, MongoDB ni sistemas externos.` |
| `backend/modules/comercial/alertas_margen_service.py` | 4 | `EDARSAHUB SQL es el cerebro. CERO MongoDB.` |
| `backend/modules/comercial/alertas_margen_service.py` | 402 | `NOTA: Este es un endpoint de prueba. El motor de evaluación masiva` |
| `backend/modules/comercial/alertas_margen_repository.py` | 4 | `EDARSAHUB SQL es el cerebro. CERO MongoDB.` |
| `backend/modules/comercial/routes_pricing_ia.py` | 610 | `Tipos de motor disponibles:` |
| `backend/modules/comercial/routes_pricing_ia.py` | 622 | `Para vinos, use tipo_motor=VINOS_RANGOS.` |
| `backend/modules/comercial/routes_pricing_ia.py` | 629 | `f"motor={request.tipo_motor.value} estado={resultado.estado.value}"` |
| `backend/modules/comercial/rentabilidad.py` | 7 | `COSTOS-ALERTAS-001-E: Motor de evaluación de rentabilidad local.` |
| `backend/modules/comercial/routes_listas_competidores.py` | 8 | `- CERO MongoDB` |
| `backend/modules/comercial/routes_alertas_margen.py` | 4 | `EDARSAHUB SQL es el cerebro. CERO MongoDB.` |
| `backend/modules/comercial/routes_alertas_margen.py` | 281 | `NOTA: Este es un endpoint de prueba. El motor de evaluación masiva` |
| `backend/modules/comercial/repository.py` | 7 | `- ELIMINADA dependencia de MongoDB completamente` |
| `backend/modules/comercial/repository.py` | 9 | `- execute_hub_query como motor central` |
| `backend/modules/comercial/repository.py` | 82 | `Garantiza paridad estructural con el esquema original de MongoDB.` |
| `backend/modules/comercial/repository.py` | 153 | `WHERE (id = '{server_id}' OR mongodb_id = '{server_id}')` |
| `backend/modules/comercial/repository.py` | 205 | `MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.` |
| `backend/modules/comercial/repository.py` | 218 | `MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.` |
| `backend/modules/comercial/repository.py` | 327 | `MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.` |
| `backend/modules/comercial/historical_kpis_repository.py` | 8 | `EDARSAHUB SQL es el cerebro. MongoDB NO es destino final de históricos.` |
| `backend/modules/comercial/historical_kpis_repository.py` | 51 | `"""Obtiene credenciales de EDARSAHUB desde MongoDB servers."""` |
| `backend/modules/comercial/historical_kpis_repository.py` | 57 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/modules/comercial/historical_kpis_repository.py` | 59 | `client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))` |
| `backend/modules/comercial/historical_kpis_repository.py` | 475 | `# MIGRACIÓN DE STAGING MONGODB A SQL` |
| `backend/modules/comercial/historical_kpis_repository.py` | 483 | `Migra KPIs de staging en MongoDB a destino final en SQL.` |
| `backend/modules/comercial/historical_kpis_repository.py` | 492 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/modules/comercial/historical_kpis_repository.py` | 494 | `client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))` |
| `backend/modules/comercial/historical_kpis_repository.py` | 519 | `# Mapear documento MongoDB a registro SQL` |
| `backend/modules/comercial/kpis_repository.py` | 25 | `# INYECCIÓN DE DEPENDENCIA: MongoDB` |
| `backend/modules/comercial/routes.py` | 1165 | `# Para modo HUB, NO usar caché MongoDB como fallback.` |
| `backend/modules/comercial/routes.py` | 1167 | `# MongoDB NO debe ser fuente productiva de datos.` |
| `backend/modules/comercial/routes.py` | 1170 | `# HUB: Reportar error SQL, NO usar caché MongoDB` |
| `backend/modules/comercial/routes.py` | 1171 | `logging.warning(f"[HUB-EDARSAHUB-ERROR] {server['name']}: Error leyendo EDARSAHUB SQL - NO hay fallback MongoDB")` |
| `backend/modules/comercial/routes.py` | 1189 | `# LIVE-C: Mantener fallback a caché MongoDB (conexión real fallida)` |
| `backend/modules/comercial/routes.py` | 1678 | `# FUENTE: EDARSAHUB.Unidades_Negocio (NO MongoDB)` |
| `backend/modules/comercial/routes.py` | 3048 | `# BLINDAJE: Usar nombre obtenido de MongoDB` |
| `backend/modules/comercial/routes.py` | 3159 | `# BLINDAJE MPRO: Usar nombre de MongoDB (ya obtenido arriba), con fallback a SQL si no se encontró` |
| `backend/modules/comercial/routes.py` | 3161 | `# Si MongoDB no encontró el nombre (aún es server['name']), intentar con SQL` |
| `backend/modules/comercial/queries/hub.py` | 2 | `EDARSA HUB - Lecturas desde EDARSA HUB (MongoDB)` |
| `backend/modules/comercial/queries/hub.py` | 9 | `COLECCIONES MONGODB:` |
| `backend/modules/comercial/queries/hub.py` | 59 | `# Los imports de MongoDB se agregarán cuando se implemente` |
| `backend/modules/comercial/queries/hub.py` | 168 | `Construye filtro MongoDB para consultas de KPIs.` |
| `backend/modules/comercial/queries/hub.py` | 178 | `Dict filtro para MongoDB find()` |
| `backend/modules/comercial/services/listas_competidores_service.py` | 10 | `- CERO MongoDB` |
| `backend/modules/comercial/services/precios_sugeridos_consolidado_service.py` | 13 | `- CERO MongoDB` |
| `backend/modules/comercial/services/pricing_ai_service.py` | 15 | `- NO usar MongoDB (todo en EDARSAHUB SQL)` |
| `backend/modules/comercial/services/pricing_ai_service.py` | 50 | `TipoMotorPrecio,` |
| `backend/modules/comercial/services/pricing_ai_service.py` | 672 | `tipo_motor=TipoMotorPrecio.COSTO_MARGEN,` |
| `backend/modules/comercial/services/perfil_unidad_service.py` | 5 | `que sirven como contexto para el motor de precios con IA y benchmark.` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 4 | `Este módulo orquesta el cálculo de precios sugeridos usando diferentes motores:` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 33 | `TipoMotorPrecio,` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 214 | `TIPOS DE MOTOR:` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 248 | `tipo_motor=request.tipo_motor,` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 257 | `# MOTOR VINOS_RANGOS: Delegar a servicio existente (INTOCABLE)` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 259 | `if request.tipo_motor == TipoMotorPrecio.VINOS_RANGOS:` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 263 | `response.mensaje = "El producto no es vino. Use motor COSTO_MARGEN para productos generales."` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 298 | `# MOTOR COSTO_MARGEN: Fórmula matemática pura` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 300 | `if request.tipo_motor == TipoMotorPrecio.COSTO_MARGEN:` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 369 | `# MOTOR BENCHMARK_COMPETENCIA: Basado en posición vs competidores` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 371 | `if request.tipo_motor == TipoMotorPrecio.BENCHMARK_COMPETENCIA:` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 408 | `# MOTOR MIXTO_COSTO_COMPETENCIA: Combina costo+margen con benchmark` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 410 | `if request.tipo_motor == TipoMotorPrecio.MIXTO_COSTO_COMPETENCIA:` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 485 | `# Motor no reconocido` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 487 | `response.mensaje = f"Tipo de motor no reconocido: {request.tipo_motor}"` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 499 | `tipo_motor: TipoMotorPrecio,` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 510 | `tipo_motor: Motor a usar para todos los productos` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 551 | `tipo_motor=tipo_motor,` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 561 | `def obtener_estadisticas_calculo(server_id: str, tipo_motor: TipoMotorPrecio = TipoMotorPrecio.COSTO_MARGEN) -> Dict[str...` |
| `backend/modules/comercial/services/pricing_sugerido_service.py` | 571 | `tipo_motor=tipo_motor,` |
| `backend/modules/comercial/services/metricas_ia_service.py` | 16 | `- NO usar MongoDB` |
| `backend/modules/comercial/services/pricing_schemas.py` | 2 | `FASE 1C-3I-B: Esquemas Pydantic para Motor de Precios Sugeridos y Benchmark` |
| `backend/modules/comercial/services/pricing_schemas.py` | 78 | `class TipoMotorPrecio(str, Enum):` |
| `backend/modules/comercial/services/pricing_schemas.py` | 79 | `"""Tipos de motor de cálculo de precio."""` |
| `backend/modules/comercial/services/pricing_schemas.py` | 412 | `# Motor a usar` |
| `backend/modules/comercial/services/pricing_schemas.py` | 413 | `tipo_motor: TipoMotorPrecio = Field(` |
| `backend/modules/comercial/services/pricing_schemas.py` | 414 | `default=TipoMotorPrecio.COSTO_MARGEN,` |
| `backend/modules/comercial/services/pricing_schemas.py` | 415 | `description="Tipo de motor de cálculo"` |
| `backend/modules/comercial/services/pricing_schemas.py` | 432 | `tipo = values.get('tipo_motor')` |
| `backend/modules/comercial/services/pricing_schemas.py` | 433 | `if tipo == TipoMotorPrecio.COSTO_MARGEN and v is None:` |
| `backend/modules/comercial/services/pricing_schemas.py` | 446 | `# Motor utilizado` |
| `backend/modules/comercial/services/pricing_schemas.py` | 447 | `tipo_motor: TipoMotorPrecio` |
| `backend/modules/comercial/services/pricing_schemas.py` | 602 | `'TipoMotorPrecio',` |
| `backend/modules/hub/modulo_financiero_proyectos.py` | 63 | `# MOTOR DE RENTABILIDAD REAL (P&L POR EVENTO)` |
| `backend/modules/fase2_operativo/sql_repository.py` | 4 | `Reemplazo completo de MongoDB para el módulo fase2_operativo.` |
| `backend/modules/fase2_operativo/db_utils.py` | 5 | `Proporciona acceso a la conexión de MongoDB para el módulo operativo.` |
| `backend/modules/fase2_operativo/db_utils.py` | 8 | `from pymongo import MongoClient` |
| `backend/modules/fase2_operativo/db_utils.py` | 10 | `# Conexión síncrona a MongoDB para los repositories` |
| `backend/modules/fase2_operativo/db_utils.py` | 17 | `Obtiene la conexión a la base de datos MongoDB.` |
| `backend/modules/fase2_operativo/db_utils.py` | 21 | `Database MongoDB` |
| `backend/modules/fase2_operativo/db_utils.py` | 26 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/modules/fase2_operativo/db_utils.py` | 29 | `_client = MongoClient(mongo_url)` |
| `backend/modules/fase2_operativo/repositories/__init__.py` | 6 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/base_repository.py` | 7 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/base_repository.py` | 12 | `- El parámetro 'db' (MongoDB) se ignora completamente` |
| `backend/modules/fase2_operativo/repositories/cargos_repository.py` | 6 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/cargos_repository.py` | 25 | `Reemplaza acceso MongoDB por SQL Server EDARSAHUB.` |
| `backend/modules/fase2_operativo/repositories/cargos_repository.py` | 58 | `# Mapeo de datos MongoDB → SQL` |
| `backend/modules/fase2_operativo/repositories/cargos_repository.py` | 165 | `# Mapear campos MongoDB → SQL` |
| `backend/modules/fase2_operativo/repositories/cargos_repository.py` | 417 | `Reemplaza acceso MongoDB por SQL Server EDARSAHUB.` |
| `backend/modules/fase2_operativo/repositories/configuracion_repository.py` | 6 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/configuracion_repository.py` | 17 | `Migrado de MongoDB a SQL Server EDARSAHUB.` |
| `backend/modules/fase2_operativo/repositories/auditoria_programada_repository.py` | 6 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/auditoria_programada_repository.py` | 27 | `Migrado de MongoDB a SQL Server EDARSAHUB.` |
| `backend/modules/fase2_operativo/repositories/auditoria_repository.py` | 6 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/auditoria_repository.py` | 17 | `Migrado de MongoDB a SQL Server EDARSAHUB.` |
| `backend/modules/fase2_operativo/repositories/workflow_repository.py` | 7 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/workflow_repository.py` | 20 | `# Constante para ordenamiento descendente (reemplaza pymongo.DESCENDING)` |
| `backend/modules/fase2_operativo/repositories/workflow_repository.py` | 202 | `No usa $inc de MongoDB, hace SELECT + UPDATE.` |
| `backend/modules/fase2_operativo/repositories/workflow_repository.py` | 233 | `MIGRADO A SQL: Usa GROUP BY explícito en lugar de aggregate de MongoDB.` |
| `backend/modules/fase2_operativo/repositories/asignacion_repository.py` | 6 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/asignacion_repository.py` | 21 | `Migrado de MongoDB a SQL Server EDARSAHUB.` |
| `backend/modules/fase2_operativo/repositories/justificacion_repository.py` | 6 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/justificacion_repository.py` | 17 | `Migrado de MongoDB a SQL Server EDARSAHUB.` |
| `backend/modules/fase2_operativo/repositories/tarea_repository.py` | 7 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/tarea_repository.py` | 20 | `# Constantes para ordenamiento (reemplazan pymongo.ASCENDING/DESCENDING)` |
| `backend/modules/fase2_operativo/repositories/detalle_diferencias_repository.py` | 6 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/detalle_diferencias_repository.py` | 17 | `Migrado de MongoDB a SQL Server EDARSAHUB.` |
| `backend/modules/fase2_operativo/repositories/responsabilidad_repository.py` | 7 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/historial_responsabilidad_repository.py` | 6 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/historial_responsabilidad_repository.py` | 24 | `Migrado de MongoDB a SQL Server EDARSAHUB.` |
| `backend/modules/fase2_operativo/repositories/historial_repository.py` | 6 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/historial_repository.py` | 17 | `Migrado de MongoDB a SQL Server EDARSAHUB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 6 | `usando EDARSAHUB SQL Server en lugar de MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 10 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 25 | `# MAPEO COLECCIÓN MONGODB → TABLA SQL` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 60 | `# Mapeo de campos MongoDB → SQL para cada tabla` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 207 | `Clase que simula el cursor de MongoDB con métodos encadenables.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 279 | `- CERO MongoDB productivo` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 283 | `- Reemplaza BaseRepository (MongoDB)` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 292 | `collection_name: Nombre de la colección MongoDB (se mapea a tabla SQL)` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 338 | `Mapea un campo MongoDB a su equivalente SQL.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 367 | `Convierte una fila SQL a formato compatible con MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 373 | `# Crear mapeo inverso SQL → MongoDB` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 406 | `Construye cláusula WHERE desde filtros estilo MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 429 | `# Operadores MongoDB` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 493 | `Construye cláusula ORDER BY desde formato MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 740 | `# MÉTODOS DE COMPATIBILIDAD MONGODB (Síncronos)` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 745 | `Versión síncrona de get para compatibilidad con código MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 783 | `Versión síncrona para compatibilidad con código MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 847 | `Versión síncrona de create para compatibilidad con código MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 858 | `Versión síncrona de update para compatibilidad con código MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 897 | `Versión síncrona de count para compatibilidad con código MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 909 | `Versión síncrona para compatibilidad con MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 935 | `Versión síncrona para compatibilidad con MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 980 | `Versión síncrona para compatibilidad con MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 1035 | `Ejecuta una agregación estilo MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 1186 | `Factory para obtener un repositorio SQL dado un nombre de colección MongoDB.` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 1189 | `collection_name: Nombre de la colección MongoDB` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 1210 | `- El parámetro 'db' (MongoDB) se ignora` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 1222 | `# Ignoramos db (MongoDB) - Usamos SQL` |
| `backend/modules/fase2_operativo/repositories/sql_base_repository.py` | 1232 | `f"(MongoDB db ignorado, usando EDARSAHUB SQL)"` |
| `backend/modules/fase2_operativo/scripts/init_notificaciones.py` | 9 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/modules/fase2_operativo/scripts/init_notificaciones.py` | 20 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/modules/fase2_operativo/scripts/init_notificaciones.py` | 23 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/modules/fase2_operativo/scripts/init_responsabilidad.py` | 65 | `db: Conexión a MongoDB` |
| `backend/modules/fase2_operativo/scripts/init_responsabilidad.py` | 117 | `db: Conexión a MongoDB` |
| `backend/modules/fase2_operativo/scripts/init_responsabilidad.py` | 174 | `db: Conexión a MongoDB (opcional, se obtiene si no se pasa)` |
| `backend/modules/fase2_operativo/scripts/init_collections_fase2a.py` | 16 | `from pymongo import MongoClient, ASCENDING, DESCENDING` |
| `backend/modules/fase2_operativo/scripts/init_collections_fase2a.py` | 17 | `from pymongo.errors import CollectionInvalid, OperationFailure` |
| `backend/modules/fase2_operativo/scripts/init_collections_fase2a.py` | 335 | `client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)` |
| `backend/modules/fase2_operativo/scripts/init_collections_fase2a.py` | 338 | `print("✓ Conexión a MongoDB establecida")` |
| `backend/modules/fase2_operativo/scripts/init_collections_fase2a.py` | 340 | `print(f"ERROR: No se pudo conectar a MongoDB: {e}")` |
| `backend/modules/fase2_operativo/schemas/workflow_schemas.py` | 36 | `id: str = Field(..., alias="_id", description="ID del documento MongoDB")` |
| `backend/modules/fase2_operativo/services/document_data_service.py` | 39 | `- Operaciones de MongoDB pasan por StubDatabase sin fallar` |
| `backend/modules/fase2_operativo/services/document_data_service.py` | 47 | `db: Instancia de la base de datos MongoDB` |
| `backend/modules/fase2_operativo/services/document_data_service.py` | 70 | `FASE B-P2: SQL-only, sin fallback a MongoDB.` |
| `backend/modules/fase2_operativo/services/cargos_service.py` | 789 | `# No consultamos MongoDB para usuarios/workflows - usamos datos ya disponibles` |
| `backend/modules/fase2_operativo/services/orquestador_service.py` | 7 | `Este servicio ahora usa SQL Server (EDARSAHUB) en lugar de MongoDB.` |
| `backend/modules/fase2_operativo/services/orquestador_service.py` | 46 | `- Las operaciones de MongoDB fueron reemplazadas por sql_repository.py` |
| `backend/modules/fase2_operativo/services/orquestador_service.py` | 74 | `MIGRADO A SQL SERVER - Ya no depende de MongoDB.` |
| `backend/modules/fase2_operativo/services/notification_service.py` | 32 | `FASE B-P2: Migrado a SQL - usa repositorio SQL en lugar de MongoDB.` |
| `backend/modules/fase2_operativo/services/notification_service.py` | 38 | `# FASE B-P2: Usar SQLBaseRepository en lugar de MongoDB collection` |
| `backend/modules/fase2_operativo/services/notification_service.py` | 420 | `# FASE B-P2: Usar SQL repository en lugar de MongoDB` |
| `backend/modules/fase2_operativo/services/auditoria_programada_service.py` | 5 | `Usa PyMongo sync para compatibilidad con el módulo.` |
| `backend/modules/fase2_operativo/services/auditoria_programada_service.py` | 45 | `- MongoDB pasa por StubDatabase` |
| `backend/modules/fase2_operativo/services/auditoria_programada_service.py` | 236 | `"""Crea workflow de inventario (sync - usa PyMongo directamente)."""` |
| `backend/modules/fase2_operativo/services/sla_service.py` | 7 | `Este servicio ahora usa SQL Server (EDARSAHUB) en lugar de MongoDB.` |
| `backend/modules/fase2_operativo/services/sla_service.py` | 72 | `- Las operaciones de MongoDB fueron reemplazadas por sql_repository.py` |
| `backend/modules/fase2_operativo/services/auditoria_service.py` | 44 | `db: Instancia de la base de datos MongoDB` |
| `backend/modules/fase2_operativo/services/configuracion_service.py` | 46 | `db: Instancia de la base de datos MongoDB` |
| `backend/modules/fase2_operativo/services/operativo_service.py` | 50 | `db: Instancia de la base de datos MongoDB` |
| `backend/modules/fase2_operativo/services/tarea_service.py` | 43 | `db: Instancia de la base de datos MongoDB` |
| `backend/modules/fase2_operativo/services/workflow_service.py` | 72 | `db: Instancia de la base de datos MongoDB` |
| `backend/modules/fase2_operativo/services/justificacion_service.py` | 52 | `db: Instancia de la base de datos MongoDB` |
| `backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py` | 111 | `db_async = manager.db  # Conexión async de MongoDB` |
| `backend/modules/fase2_operativo/routes/notificaciones_routes.py` | 64 | `# Usar método síncrono para MongoDB síncrono` |
| `backend/modules/api_connections/__init__.py` | 9 | `- Caché/Fallback: MongoDB (colección api_connections)` |
| `backend/modules/api_connections/__init__.py` | 15 | `- Sincronización automática con MongoDB` |
| `backend/modules/api_connections/repository.py` | 6 | `- MongoDB: Solo caché/log/estado auxiliar (NO autoritativo)` |
| `backend/modules/api_connections/repository.py` | 7 | `- Sincronización: EDARSAHUB SQL → MongoDB (nunca al revés)` |
| `backend/modules/api_connections/repository.py` | 11 | `2. Si EDARSAHUB SQL falla, NO se guarda en MongoDB` |
| `backend/modules/api_connections/repository.py` | 12 | `3. Si MongoDB falla después de EDARSAHUB SQL, la operación es exitosa` |
| `backend/modules/api_connections/repository.py` | 34 | `# Referencia a MongoDB (solo para caché, NO autoritativo)` |
| `backend/modules/api_connections/repository.py` | 39 | `"""Inicializa el repositorio con la conexión a MongoDB (solo caché)."""` |
| `backend/modules/api_connections/repository.py` | 46 | `"""Obtiene la conexión a MongoDB (solo para caché)."""` |
| `backend/modules/api_connections/repository.py` | 244 | `# ESCRITURA - PRIMERO EDARSAHUB SQL, LUEGO CACHÉ MONGODB` |
| `backend/modules/api_connections/repository.py` | 256 | `5. Actualizar caché MongoDB (opcional, no bloquea)` |
| `backend/modules/api_connections/repository.py` | 329 | `# 6. Actualizar caché MongoDB (no bloquea si falla)` |
| `backend/modules/api_connections/repository.py` | 346 | `6. Actualizar caché MongoDB` |
| `backend/modules/api_connections/repository.py` | 424 | `# 7. Actualizar caché MongoDB` |
| `backend/modules/api_connections/repository.py` | 438 | `4. Eliminar de caché MongoDB` |
| `backend/modules/api_connections/repository.py` | 466 | `# 4. Eliminar de caché MongoDB (no bloquea)` |
| `backend/modules/api_connections/repository.py` | 472 | `logging.warning(f"[API_CONNECTIONS] Error eliminando caché MongoDB: {e}")` |
| `backend/modules/api_connections/repository.py` | 478 | `# SINCRONIZACIÓN EDARSAHUB SQL → MONGODB (CACHÉ)` |
| `backend/modules/api_connections/repository.py` | 483 | `Sincroniza una conexión específica de EDARSAHUB SQL a MongoDB caché.` |
| `backend/modules/api_connections/repository.py` | 518 | `logging.debug(f"[API_CONNECTIONS] Caché MongoDB actualizado para {api_id}")` |
| `backend/modules/api_connections/repository.py` | 521 | `logging.warning(f"[API_CONNECTIONS] Error sincronizando caché MongoDB: {e}")` |
| `backend/modules/api_connections/repository.py` | 527 | `Sincroniza todas las conexiones API de EDARSAHUB SQL a MongoDB caché.` |
| `backend/modules/api_connections/repository.py` | 555 | `Guarda el resultado en MongoDB como log de estado.` |
| `backend/modules/api_connections/repository.py` | 600 | `# Guardar resultado en MongoDB como log de estado (no bloquea)` |
| `backend/modules/api_connections/routes.py` | 8 | `- MongoDB solo se usa como caché/log (no autoritativo)` |
| `backend/modules/api_connections/routes.py` | 10 | `- Errores de MongoDB se registran pero no bloquean la operación` |
| `backend/modules/api_connections/routes.py` | 162 | `DESTINO: EDARSAHUB SQL (autoritativo), luego caché MongoDB.` |
| `backend/modules/api_connections/routes.py` | 195 | `DESTINO: EDARSAHUB SQL (autoritativo), luego caché MongoDB.` |
| `backend/modules/api_connections/routes.py` | 281 | `Sincroniza conexiones API de EDARSAHUB SQL a MongoDB caché.` |
| `backend/modules/api_connections/routes.py` | 282 | `FLUJO: EDARSAHUB SQL → MongoDB (caché).` |
| `backend/modules/api_connections/routes.py` | 289 | `"message": "Sincronización EDARSAHUB SQL → MongoDB completada",` |
| `backend/modules/corporate_filters/router.py` | 424 | `sql = "SELECT sistema_version_id, tipo_sistema, nombre_sistema, version_sistema, descripcion, proveedor, motor_base_dato...` |
| `backend/modules/corporate_filters/router.py` | 453 | `allowed = ["nombre_sistema", "version_sistema", "descripcion", "proveedor", "motor_base_datos", "es_version_default", "a...` |
| `backend/modules/sistema/estructura_service.py` | 39 | `# MongoDB ELIMINADO - Retornar estructura vacía si db es None` |
| `backend/modules/sistema/estructura_service.py` | 41 | `logger.warning("[ESTRUCTURA] get_estructura_organizacional: Sin MongoDB - Retornando vacío")` |
| `backend/modules/sistema/estructura_service.py` | 47 | `"nota": "Modo SQL-only: Datos de estructura no disponibles sin MongoDB"` |
| `backend/modules/sistema/estructura_service.py` | 231 | `NOTA: MongoDB ELIMINADO - Este servicio puede recibir db=None.` |
| `backend/modules/costos_margenes/__init__.py` | 9 | `- NO usa MongoDB` |
| `backend/modules/costos_margenes/routes.py` | 10 | `- NO se usa MongoDB` |
| `backend/modules/rh/__init__.py` | 103 | `database: Instancia de AsyncIOMotorDatabase` |
| `backend/modules/rh/repository.py` | 38 | `# NO depende del catálogo de servidores MongoDB con active=True.` |
| `backend/modules/rh/repository.py` | 66 | `# INYECCIÓN DE DEPENDENCIA: MongoDB` |
| `backend/modules/rh/repository.py` | 73 | `"""Inicializa el repositorio con la conexión a MongoDB."""` |
| `backend/modules/rh/repository.py` | 80 | `"""Obtiene la conexión a MongoDB inyectada."""` |
| `backend/modules/rh/repository.py` | 145 | `en lugar de buscar en MongoDB servers con active=True.` |
| `backend/modules/rh/importador/repository.py` | 38 | `"""Inicializa el repositorio con la conexión a MongoDB."""` |
| `backend/modules/rh/importador/repository.py` | 45 | `"""Obtiene la conexión a MongoDB inyectada."""` |
| `backend/modules/configuracion/repositories/config_asignaciones_repository.py` | 403 | `En modo SQL-only, esta operación no persiste en MongoDB.` |
| `backend/modules/configuracion/services/almacenes_sync_service.py` | 6 | `Sincroniza almacenes desde sistemas origen (SoftRestaurant/MPRO) al catálogo local MongoDB.` |
| `backend/modules/configuracion/services/almacenes_sync_service.py` | 95 | `- Persiste en MongoDB (almacenes_catalogo)` |
| `backend/modules/configuracion/services/almacenes_sync_service.py` | 98 | `db: Conexión a MongoDB` |
| `backend/modules/configuracion/services/almacenes_sync_service.py` | 137 | `# FASE P1.4-F (Dic 2025): Migrado de MongoDB db.servers a server_registry` |
| `backend/modules/configuracion/services/almacenes_sync_service.py` | 198 | `# PASO 5: Sincronizar al catálogo local MongoDB` |
| `backend/modules/configuracion/routes/config_asignaciones_routes.py` | 24 | `# Motor para conexión a MongoDB` |
| `backend/modules/configuracion/routes/config_asignaciones_routes.py` | 25 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/modules/configuracion/routes/config_asignaciones_routes.py` | 36 | `# Conexión a MongoDB` |
| `backend/modules/configuracion/routes/config_asignaciones_routes.py` | 40 | `"""Obtiene la conexión a la base de datos MongoDB."""` |
| `backend/modules/configuracion/routes/config_asignaciones_routes.py` | 43 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/modules/configuracion/routes/config_asignaciones_routes.py` | 45 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/modules/inventarios/repository.py` | 7 | `- ELIMINADA dependencia de MongoDB` |
| `backend/modules/consultas_sql/__init__.py` | 10 | `- Leer consultas desde EDARSAHUB SQL (no desde código/MongoDB)` |
| `backend/modules/catalogos/__init__.py` | 26 | `from motor.motor_asyncio import AsyncIOMotorDatabase` |
| `backend/modules/catalogos/__init__.py` | 28 | `# Referencia global a MongoDB (para logging/auditoría)` |
| `backend/modules/catalogos/__init__.py` | 29 | `_db: AsyncIOMotorDatabase = None` |
| `backend/modules/catalogos/__init__.py` | 32 | `def init_catalogos_module(db: AsyncIOMotorDatabase):` |
| `backend/modules/catalogos/__init__.py` | 33 | `"""Inicializa el módulo de catálogos con la conexión a MongoDB."""` |
| `backend/modules/catalogos/__init__.py` | 38 | `def get_db() -> AsyncIOMotorDatabase:` |
| `backend/modules/catalogos/__init__.py` | 39 | `"""Obtiene la conexión a MongoDB."""` |
| `backend/modules/catalogos/repository.py` | 7 | `FASE P1.2 (Dic 2025): Migrado de MongoDB db.servers a EDARSAHUB_CONFIG de server_registry.` |
| `backend/modules/catalogos/repository.py` | 22 | `# FASE P1.2: La conexión ahora viene de EDARSAHUB_CONFIG, no de MongoDB` |
| `backend/modules/catalogos/repository.py` | 37 | `FASE P1.2 (Dic 2025): Migrado de MongoDB db.servers a server_registry.EDARSAHUB_CONFIG.` |
| `backend/modules/catalogos/repository.py` | 41 | `NO FUENTE: MongoDB db.servers` |
| `backend/modules/catalogos/repository.py` | 341 | `db: Conexión a MongoDB (para obtener credenciales SQL)` |
| `backend/modules/edge/motor_reglas_comerciales.py` | 6 | `class MotorReglasComerciales:` |
| `backend/modules/edge/comandero_local_core.py` | 103 | `# MOTOR TRANSACCIONAL OFFLINE (Cola FIFO con Idempotencia)` |
| `backend/modules/edge/motor_inventario_parametrico.py` | 1 | `# backend/modules/edge/motor_inventario_parametrico.py` |
| `backend/modules/edge/motor_inventario_parametrico.py` | 7 | `class MotorInventarioParametrico:` |
| `backend/modules/auth/service.py` | 58 | `# Preparar documento para MongoDB` |
| `backend/modules/auth/service.py` | 119 | `# El ID puede venir como int (de SQL) o como string (MongoDB ObjectId)` |
| `backend/modules/auth/service.py` | 345 | `Ya NO escribe en MongoDB. Los permisos operativos se guardan en:` |
| `backend/modules/auth/service.py` | 580 | `# Retornar sin password ni _id (MongoDB agrega _id al dict después de insert)` |
| `backend/modules/auth/__init__.py` | 12 | `- repository.py: Acceso a MongoDB` |
| `backend/modules/auth/__init__.py` | 35 | `Inicializa el módulo de auth con la conexión a MongoDB.` |
| `backend/modules/auth/__init__.py` | 38 | `database: Instancia de AsyncIOMotorDatabase` |
| `backend/modules/auth/password_reset.py` | 15 | `- MongoDB ya NO se usa en este módulo` |
| `backend/modules/auth/password_reset.py` | 115 | `AUTH-RESET-P2: Reemplaza MongoDB rate_limit_password_reset.` |
| `backend/modules/auth/password_reset.py` | 162 | `AUTH-RESET-P2: Reemplaza MongoDB rate_limit_password_reset.` |
| `backend/modules/auth/password_reset.py` | 209 | `AUTH-RESET-P2: Reemplaza MongoDB audit_password_reset.` |
| `backend/modules/auth/repository.py` | 6 | `MongoDB ya NO es fuente productiva para operaciones de usuarios.` |
| `backend/modules/auth/repository.py` | 23 | `# INICIALIZACIÓN - YA NO REQUIERE MONGODB` |
| `backend/modules/auth/repository.py` | 33 | `MIGRACIÓN COMPLETA A SQL: MongoDB ya NO es requerido.` |
| `backend/modules/auth/repository.py` | 40 | `logging.info("[AUTH] Repository inicializado - 100% SQL Server (sin MongoDB)")` |
| `backend/modules/auth/repository.py` | 62 | `MongoDB ya NO es fuente productiva.` |
| `backend/modules/auth/repository.py` | 71 | `MongoDB ya NO es fuente productiva.` |
| `backend/modules/auth/repository.py` | 85 | `MongoDB solo se consulta para campos RBAC piloto (sec_*, telefono)` |
| `backend/modules/auth/repository.py` | 170 | `# RBAC-SCOPE-D: MongoDB solo para campos RBAC piloto (sec_*), NO para permisos operativos` |
| `backend/modules/auth/repository.py` | 192 | `logging.warning(f"[AUTH-REPO] No se pudieron leer campos RBAC piloto de MongoDB: {mongo_err}")` |
| `backend/modules/auth/repository.py` | 207 | `# Obtener campos RBAC piloto de MongoDB (solo metadatos, no permisos operativos)` |
| `backend/modules/auth/repository.py` | 224 | `# Campos RBAC piloto (desde MongoDB - solo metadatos)` |
| `backend/modules/auth/repository.py` | 241 | `# NO hacer fallback a MongoDB - reportar error` |
| `backend/modules/auth/repository.py` | 282 | `MongoDB ya NO es fuente productiva.` |
| `backend/modules/auth/repository.py` | 291 | `MongoDB ya NO es fuente productiva.` |
| `backend/modules/auth/repository.py` | 300 | `MongoDB ya NO es fuente productiva.` |
| `backend/modules/auth/context_service.py` | 14 | `Este módulo ha sido migrado de MongoDB a EDARSAHUB SQL.` |
| `backend/modules/auth/context_service.py` | 24 | `MongoDB ya no es fuente de datos para contexto de usuario.` |
| `backend/modules/auth/context_service.py` | 220 | `Obtiene una empresa por UUID MongoDB.` |
| `backend/modules/auth/routes.py` | 106 | `# Autenticar usuario (valida credenciales contra MongoDB)` |
| `backend/modules/auth/routes.py` | 265 | `# Buscar usuario en MongoDB para obtener email y role` |
| `backend/modules/comercial_v2/routes.py` | 584 | `Fuente: EDARSAHUB (NO SQL vivo, NO MongoDB)` |
| `backend/modules/universal_query/routes.py` | 164 | `FASE P1.3 (Dic 2025): Migrado de MongoDB db.servers a server_registry.` |
| `backend/modules/universal_query/routes.py` | 168 | `NO FUENTE: MongoDB db.servers` |
| `backend/modules/universal_query/routes.py` | 173 | `# Obtener desde EDARSAHUB SQL (NO MongoDB)` |
| `backend/modules/universal_query/routes.py` | 248 | `FASE P1.3 (Dic 2025): Migrado de MongoDB a EDARSAHUB SQL via server_registry.` |
| `backend/modules/universal_query/routes.py` | 255 | `# Obtener servidor desde EDARSAHUB SQL (NO MongoDB)` |
| `backend/modules/crm/integration/sync_engine.py` | 4 | `Motor de sincronización que orquesta la importación de datos` |
| `backend/modules/crm/integration/sync_engine.py` | 32 | `Motor de sincronización CRM.` |
| `backend/modules/finanzas/repository_bancarios.py` | 4 | `Acceso a datos EDARSAHUB. NO usar MongoDB.` |
| `backend/modules/finanzas/repository_bancarios.py` | 28 | `IMPORTANTE: Solo usar EDARSAHUB, NO MongoDB.` |
| `backend/modules/finanzas/repository_cuadres_z_edarsahub.py` | 75 | `NO usa MongoDB como fuente financiera.` |
| `backend/modules/finanzas/repository_cuadres_z_edarsahub.py` | 1100 | `# Formatear para compatibilidad con contrato anterior (MongoDB)` |
| `backend/modules/finanzas/carga_historica_propinas_tpv.py` | 21 | `- NO usa MongoDB como fuente financiera` |
| `backend/modules/finanzas/tesoreria.py` | 7 | `- Ya NO usa MongoDB (tesoreria_cuadres_z) como fuente productiva` |
| `backend/modules/finanzas/tesoreria.py` | 300 | `- Ya NO usa MongoDB tesoreria_cuadres_z` |
| `backend/modules/finanzas/tesoreria.py` | 320 | `# Filtrar por server_id o unidad_negocio_id (SQL directo, sin MongoDB)` |
| `backend/modules/finanzas/tesoreria.py` | 357 | `- Ya NO usa MongoDB tesoreria_cuadres_z` |
| `backend/modules/finanzas/tesoreria.py` | 446 | `- Ya NO usa MongoDB tesoreria_cuadres_z` |
| `backend/modules/finanzas/tesoreria.py` | 746 | `FALLBACK: MongoDB (solo si EDARSAHUB falla, con warning)` |
| `backend/modules/finanzas/tesoreria.py` | 819 | `logger.warning("[TESORERIA][EDARSAHUB_EMPTY] EDARSAHUB no retornó servidores, intentando fallback MongoDB")` |
| `backend/modules/finanzas/tesoreria.py` | 824 | `# FALLBACK: server_registry.py (FASE T2.2: Reemplaza MongoDB)` |
| `backend/modules/finanzas/tesoreria.py` | 878 | `FASE T2.2: Fallback migrado a server_registry.py (elimina MongoDB).` |
| `backend/modules/finanzas/repository_cuadres_z.py` | 2 | `Repositorio MongoDB para Cuadres de Cortes Z` |
| `backend/modules/finanzas/repository_cuadres_z.py` | 12 | `# MongoDB connection` |
| `backend/modules/finanzas/repository_cuadres_z.py` | 18 | `from pymongo import MongoClient` |
| `backend/modules/finanzas/repository_cuadres_z.py` | 19 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/modules/finanzas/repository_cuadres_z.py` | 21 | `client = MongoClient(mongo_url)` |
| `backend/modules/finanzas/repository_real.py` | 21 | `# FASE T2.1: Usar EDARSAHUB_CONFIG desde server_registry en lugar de MongoDB` |
| `backend/modules/finanzas/repository_real.py` | 39 | `db: Instancia de MongoDB (conservada por compatibilidad, no usada para conexión EDARSAHUB)` |
| `backend/modules/finanzas/repository_real.py` | 49 | `Ya no consulta MongoDB db.servers.` |
| `backend/modules/finanzas/repository_cortes_z.py` | 43 | `server_id: UUID del servidor en MongoDB/EDARSAHUB` |
| `backend/modules/finanzas/historical_kpis_repository.py` | 29 | `Ya no consulta MongoDB db.servers.` |
| `backend/modules/finanzas/repository_softrestaurant.py` | 187 | `db: Instancia de MongoDB (opcional, para compatibilidad)` |
| `backend/modules/finanzas/cuentas_bancarias.py` | 8 | `- NO usar MongoDB` |
| `backend/modules/finanzas/repository_mpro.py` | 14 | `- Credenciales desde EDARSAHUB/server_registry.py (no MongoDB)` |
| `backend/modules/finanzas/propinas_tpv/service.py` | 18 | `from motor.motor_asyncio import AsyncIOMotorDatabase` |
| `backend/modules/finanzas/propinas_tpv/service.py` | 26 | `# FASE T2.4: Usar server_registry centralizado en lugar de MongoDB` |
| `backend/modules/finanzas/propinas_tpv/service.py` | 45 | `def __init__(self, db: AsyncIOMotorDatabase):` |
| `backend/modules/finanzas/propinas_tpv/service.py` | 77 | `# Ya no usar MongoDB: self.db['servers']` |
| `backend/modules/finanzas/propinas_tpv/__init__.py` | 23 | `# - NO toca colecciones existentes de MongoDB` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 6 | `FASE T2.3 (Mayo 2026): Migrado a server_registry.py (elimina MongoDB db.servers)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 32 | `from motor.motor_asyncio import AsyncIOMotorDatabase` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 115 | `"""Obtiene la conexión a MongoDB."""` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 128 | `async def health_check_sql(db: AsyncIOMotorDatabase = Depends(get_db)):` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 147 | `"mongodb_connected": True,` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 177 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 210 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 248 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 277 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 309 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 330 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 349 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 387 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 424 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 440 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 466 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 499 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 569 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 631 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 655 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/sql_repository.py` | 18 | `- Este repositorio NO toca colecciones MongoDB existentes` |
| `backend/modules/finanzas/propinas_tpv/sql_repository.py` | 59 | `mongo_db: Conexión a MongoDB (conservada por compatibilidad, no usada para conexión EDARSAHUB)` |
| `backend/modules/finanzas/propinas_tpv/sql_repository.py` | 72 | `Ya no consulta MongoDB db.servers.` |
| `backend/modules/finanzas/propinas_tpv/sql_repository.py` | 722 | `Estructura compatible con el formato anterior (MongoDB).` |
| `backend/modules/finanzas/propinas_tpv/repository_edarsahub.py` | 5 | `Reemplaza la lectura de MongoDB para consultas financieras.` |
| `backend/modules/finanzas/propinas_tpv/routes_edarsahub.py` | 5 | `Reemplazan la lectura de MongoDB para consultas financieras.` |
| `backend/modules/finanzas/propinas_tpv/routes_edarsahub.py` | 75 | `# Buscar en MongoDB las empresas y sus unidades` |
| `backend/modules/finanzas/propinas_tpv/routes_edarsahub.py` | 220 | `Compatible con formato anterior de MongoDB.` |
| `backend/modules/finanzas/propinas_tpv/repository.py` | 9 | `- Operaciones CRUD en MongoDB (colecciones nuevas)` |
| `backend/modules/finanzas/propinas_tpv/repository.py` | 20 | `from motor.motor_asyncio import AsyncIOMotorDatabase` |
| `backend/modules/finanzas/propinas_tpv/repository.py` | 36 | `2. MongoDB: SOLO escribe en colecciones nuevas (propinas_control, propinas_config)` |
| `backend/modules/finanzas/propinas_tpv/repository.py` | 40 | `def __init__(self, db: AsyncIOMotorDatabase):` |
| `backend/modules/finanzas/propinas_tpv/repository.py` | 385 | `# OPERACIONES MONGODB - COLECCIÓN propinas_control` |
| `backend/modules/finanzas/propinas_tpv/repository.py` | 618 | `# OPERACIONES MONGODB - COLECCIÓN propinas_config` |
| `backend/modules/finanzas/propinas_tpv/service_sql.py` | 28 | `from motor.motor_asyncio import AsyncIOMotorDatabase` |
| `backend/modules/finanzas/propinas_tpv/service_sql.py` | 38 | `# FASE T2.4: Usar server_registry centralizado en lugar de MongoDB` |
| `backend/modules/finanzas/propinas_tpv/service_sql.py` | 61 | `def __init__(self, db: AsyncIOMotorDatabase):` |
| `backend/modules/finanzas/propinas_tpv/service_sql.py` | 158 | `# Ya no usar MongoDB: self.db['servers']` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 20 | `FASE T2.3 (Mayo 2026): Migrado a server_registry.py (elimina MongoDB db.servers)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 34 | `from motor.motor_asyncio import AsyncIOMotorDatabase` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 122 | `Obtiene la conexión a MongoDB.` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 167 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 180 | `"mongodb_connected": True,` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 213 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 234 | `- Crea índices en MongoDB` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 242 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 282 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 322 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 398 | `FASE 1B: Consulta propinas de un período SIN guardar en MongoDB.` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 411 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 481 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 510 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 540 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 560 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 582 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 605 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 636 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/routes.py` | 660 | `db: AsyncIOMotorDatabase = Depends(get_db)` |
| `backend/modules/finanzas/propinas_tpv/models.py` | 131 | `"""Schema completo del documento en MongoDB"""` |
| `backend/modules/finanzas/propinas_tpv/models.py` | 197 | `"""Schema completo en MongoDB"""` |
| `backend/modules/manuales_operativos/service.py` | 16 | `from motor.motor_asyncio import AsyncIOMotorDatabase` |
| `backend/modules/manuales_operativos/service.py` | 48 | `def __init__(self, db: AsyncIOMotorDatabase):` |
| `backend/modules/manuales_operativos/service.py` | 176 | `# Guardar en MongoDB` |
| `backend/modules/manuales_operativos/service.py` | 618 | `def get_manual_service(db: AsyncIOMotorDatabase) -> ManualOperativoService:` |
| `backend/modules/manuales_operativos/__init__.py` | 33 | `"""Inicializa el módulo con la conexión a MongoDB."""` |
| `backend/modules/manuales_operativos/triggers.py` | 20 | `from motor.motor_asyncio import AsyncIOMotorDatabase` |
| `backend/modules/manuales_operativos/triggers.py` | 21 | `from pymongo.database import Database as PyMongoDatabase` |
| `backend/modules/manuales_operativos/triggers.py` | 32 | `db: AsyncIOMotorDatabase,` |
| `backend/modules/manuales_operativos/triggers.py` | 43 | `db: Conexión a MongoDB` |
| `backend/modules/manuales_operativos/triggers.py` | 73 | `db: AsyncIOMotorDatabase,` |
| `backend/modules/manuales_operativos/triggers.py` | 121 | `async def verificar_y_generar_manuales_pendientes(db: AsyncIOMotorDatabase):` |
| `backend/modules/manuales_operativos/triggers.py` | 161 | `db_sync: PyMongoDatabase,` |
| `backend/modules/manuales_operativos/triggers.py` | 171 | `db_sync: Conexión pymongo (síncrona)` |
| `backend/modules/manuales_operativos/triggers.py` | 189 | `def _generar_manual_compras_sync(db_sync: PyMongoDatabase, proceso_id: str) -> Optional[str]:` |
| `backend/modules/manuales_operativos/routes.py` | 29 | `"""Inicializa el módulo con la conexión a MongoDB."""` |
| `backend/modules/manuales_operativos/schemas.py` | 143 | `"""Schema del manual como está almacenado en MongoDB."""` |
| `backend/modules/compras/repository_compras_sql.py` | 7 | `- Migración de compras_params de MongoDB a EDARSAHUB SQL` |
| `backend/modules/compras/repository_compras_sql.py` | 12 | `- CERO dependencias de MongoDB` |
| `backend/modules/compras/repository_compras_sql.py` | 13 | `- Reemplaza funciones get_compras_params y save_compras_params de MongoDB` |
| `backend/modules/compras/repository_compras_sql.py` | 60 | `-- Reemplaza colección MongoDB: compras_params` |
| `backend/modules/compras/repository_compras_sql.py` | 132 | `REEMPLAZA: get_compras_params() de MongoDB` |
| `backend/modules/compras/repository_compras_sql.py` | 206 | `REEMPLAZA: save_compras_params() de MongoDB` |
| `backend/modules/compras/__init__.py` | 13 | `- repository.py: Acceso a MongoDB y SQL Server` |
| `backend/modules/compras/__init__.py` | 57 | `Inicializa el módulo de compras con la conexión a MongoDB.` |
| `backend/modules/compras/__init__.py` | 60 | `database: Instancia de AsyncIOMotorDatabase` |
| `backend/modules/compras/repository.py` | 10 | `- Parámetros de compras migrados de MongoDB a EDARSAHUB SQL` |
| `backend/modules/compras/repository.py` | 12 | `- CERO MongoDB productivo para parámetros` |
| `backend/modules/compras/repository.py` | 71 | `# INYECCIÓN DE DEPENDENCIA: MongoDB` |
| `backend/modules/compras/repository.py` | 75 | `_stub_mode = False  # Flag para indicar si estamos en modo stub (sin MongoDB)` |
| `backend/modules/compras/repository.py` | 80 | `Inicializa el repositorio con la conexión a MongoDB.` |
| `backend/modules/compras/repository.py` | 88 | `logger.warning("[COMPRAS_REPO] Inicializado en modo STUB - funcionalidad MongoDB limitada")` |
| `backend/modules/compras/repository.py` | 93 | `Obtiene la conexión a MongoDB inyectada.` |
| `backend/modules/compras/repository.py` | 106 | `"""Retorna True si el repositorio está en modo stub (sin MongoDB)."""` |
| `backend/modules/compras/repository.py` | 112 | `Descifra el password de un servidor obtenido de MongoDB.` |
| `backend/modules/compras/repository.py` | 141 | `FASE T3.1: Migrado de MongoDB db.servers a server_registry (EDARSAHUB).` |
| `backend/modules/compras/repository.py` | 143 | `# FASE T3.1: Usar server_registry en lugar de MongoDB` |
| `backend/modules/compras/repository.py` | 157 | `# Migrado de MongoDB a EDARSAHUB SQL Server` |
| `backend/modules/compras/repository.py` | 164 | `MIGRADO: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.` |
| `backend/modules/compras/repository.py` | 181 | `MIGRADO: Ahora escribe a EDARSAHUB SQL en lugar de MongoDB.` |
| `backend/modules/compras/historical_kpis_repository.py` | 32 | `FASE T3.1: Migrado de MongoDB db.servers a EDARSAHUB_CONFIG de server_registry.` |
| `backend/modules/compras/historical_kpis_repository.py` | 33 | `Ya no consulta MongoDB para obtener conexión EDARSAHUB.` |
| `backend/modules/compras/repository_pedidos_sql.py` | 4 | `COMPRAS-MONGO-001-F2: Migración de MongoDB a EDARSAHUB SQL` |
| `backend/modules/compras/repository_pedidos_sql.py` | 6 | `Migra las siguientes colecciones de MongoDB a SQL:` |
| `backend/modules/compras/repository_pedidos_sql.py` | 13 | `- #2: CERO dependencias de MongoDB` |
| `backend/scripts/solucion_operaciones_analisis.py` | 46 | `[A] Migración al Motor Robusto Centralizado:` |
| `backend/scripts/solucion_operaciones_analisis.py` | 63 | `# --- MOTOR DE CASCADA SIMULADO ---` |
| `backend/scripts/run_historical_load_finanzas.py` | 82 | `"""Obtiene conexión a MongoDB."""` |
| `backend/scripts/run_historical_load_finanzas.py` | 87 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/scripts/run_historical_load_finanzas.py` | 88 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/scripts/run_historical_load_finanzas.py` | 89 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/scripts/motor_consolidacion_circuit_breaker.py` | 30 | `Simula el motor lógico del tablero ejecutivo, integrando:` |
| `backend/scripts/precheck_conectividad.py` | 13 | `- Acceso a la colección 'servers' en MongoDB` |
| `backend/scripts/precheck_conectividad.py` | 20 | `from pymongo import MongoClient` |
| `backend/scripts/precheck_conectividad.py` | 23 | `MONGO_URL = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/scripts/precheck_conectividad.py` | 32 | `# Conectar a MongoDB` |
| `backend/scripts/precheck_conectividad.py` | 34 | `client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)` |
| `backend/scripts/precheck_conectividad.py` | 37 | `print(f"\n✅ MongoDB conectado: {DB_NAME}")` |
| `backend/scripts/precheck_conectividad.py` | 39 | `print(f"\n❌ Error conectando a MongoDB: {e}")` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 3 | `EDARSA HUB - Script de Reconciliación SQL ↔ MongoDB` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 6 | `FASE 3B.2: Compara servidores entre EDARSAHUB SQL y MongoDB.` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 12 | `Con --apply: sincroniza MongoDB para que sea espejo de SQL` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 20 | `- Solo escribe en MongoDB si --apply está presente` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 35 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 67 | `Ejecuta reconciliación SQL ↔ MongoDB.` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 70 | `apply: Si True, sincroniza MongoDB con SQL` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 101 | `# Indexar por ID y mongodb_id` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 103 | `sql_by_mongodb_id = {s['mongodb_id']: s for s in sql_servers if s.get('mongodb_id')}` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 105 | `# 2. Obtener servidores desde MongoDB` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 106 | `print("Obteniendo servidores desde MongoDB...")` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 107 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 110 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 115 | `print(f"  → {len(mongo_servers)} servidores en MongoDB")` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 120 | `# 3. Comparar SQL → MongoDB` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 121 | `print("\nComparando SQL → MongoDB...")` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 123 | `mongo_server = mongo_by_id.get(sql_id) or mongo_by_id.get(sql_server.get('mongodb_id'))` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 126 | `# Servidor en SQL pero no en MongoDB` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 136 | `print("    → Sincronizado a MongoDB")` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 175 | `print("    → Actualizado en MongoDB")` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 180 | `# 4. Comparar MongoDB → SQL (detectar huérfanos)` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 181 | `print("\nComparando MongoDB → SQL...")` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 183 | `if mongo_id not in sql_by_id and mongo_id not in sql_by_mongodb_id:` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 185 | `report['warnings'].append(f"Servidor {mongo_id} existe en MongoDB pero NO en SQL (huérfano)")` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 207 | `print("REPORTE DE RECONCILIACIÓN SQL ↔ MONGODB")` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 213 | `print(f"Servidores MongoDB: {report['mongo_count']}")` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 216 | `print(f"Solo en MongoDB: {len(report['mongo_only'])}")` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 241 | `print("EDARSA HUB - Reconciliación SQL ↔ MongoDB")` |
| `backend/scripts/reconcile_servers_sql_mongo.py` | 242 | `print(f"Modo: {'APPLY (sincronizará MongoDB)' if apply else 'DRY-RUN (solo reporta)'}")` |
| `backend/scripts/correccion_proyeccion_y_moneda_final.py` | 145 | `logger.info("Verificando funcionamiento óptimo en el motor SQL:")` |
| `backend/scripts/consolidado_general_sistema_comercial.py` | 29 | `# Configuración del motor SQL Server de EDARSAHUB (Puerto 1433 por defecto)` |
| `backend/scripts/consolidado_general_sistema_comercial.py` | 361 | `SET @LogMessage = 'Ventas intermedias vacías. El motor comercial preserva los valores de respaldo de EDARSA.';` |
| `backend/scripts/carga_historica_fase23.py` | 52 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/scripts/carga_historica_fase23.py` | 53 | `from pymongo import MongoClient` |
| `backend/scripts/carga_historica_fase23.py` | 56 | `MONGO_URL = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/scripts/carga_historica_fase23.py` | 102 | `"""Establece conexión a MongoDB."""` |
| `backend/scripts/carga_historica_fase23.py` | 103 | `self.client = AsyncIOMotorClient(MONGO_URL)` |
| `backend/scripts/carga_historica_fase23.py` | 105 | `logger.info(f"Conectado a MongoDB: {DB_NAME}")` |
| `backend/scripts/carga_historica_fase23.py` | 108 | `"""Cierra conexión a MongoDB."""` |
| `backend/scripts/carga_historica_fase23.py` | 111 | `logger.info("Desconectado de MongoDB")` |
| `backend/scripts/ddl_costos_alertas_001b.py` | 6 | `MÁXIMAS: EDARSAHUB SQL es el cerebro. CERO MongoDB.` |
| `backend/scripts/ddl_costos_alertas_001b.py` | 618 | `print("MÁXIMAS: EDARSAHUB SQL es el cerebro. CERO MongoDB.")` |
| `backend/scripts/consolidado_general_sistema_comercial_v2.py` | 11 | `posee un motor de simulación local offline completo de alta resiliencia.` |
| `backend/scripts/create_scheduler_tables.py` | 3 | `Reemplaza las colecciones MongoDB para los jobs de detección.` |
| `backend/scripts/setup_kpis_indexes.py` | 22 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/scripts/setup_kpis_indexes.py` | 46 | `db: Conexión a MongoDB` |
| `backend/scripts/setup_kpis_indexes.py` | 212 | `# Obtener configuración de MongoDB` |
| `backend/scripts/setup_kpis_indexes.py` | 213 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/scripts/setup_kpis_indexes.py` | 216 | `logging.info(f"[SETUP-INDEX] Conectando a MongoDB: {db_name}")` |
| `backend/scripts/setup_kpis_indexes.py` | 218 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/scripts/validar_post_carga.py` | 18 | `from pymongo import MongoClient` |
| `backend/scripts/validar_post_carga.py` | 21 | `MONGO_URL = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/scripts/validar_post_carga.py` | 32 | `client = MongoClient(MONGO_URL)` |
| `backend/scripts/encrypt_existing_server_secrets.py` | 34 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/scripts/encrypt_existing_server_secrets.py` | 211 | `"""Cifra los secretos de un servidor en MongoDB."""` |
| `backend/scripts/encrypt_existing_server_secrets.py` | 212 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/scripts/encrypt_existing_server_secrets.py` | 215 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/scripts/encrypt_existing_server_secrets.py` | 222 | `return {'success': True, 'message': 'Server not in MongoDB'}` |
| `backend/scripts/encrypt_existing_server_secrets.py` | 328 | `# Cifrar en MongoDB` |
| `backend/scripts/encrypt_existing_server_secrets.py` | 337 | `report['warnings'].append(f"{name}: MongoDB error - {mongo_result.get('error', 'Unknown')}")` |
| `backend/scripts/motor_acumulacion_estacional.py` | 2 | `Solución Analítica: Motor de Acumulación Comercial` |
| `backend/scripts/motor_acumulacion_estacional.py` | 4 | `He ajustado el motor de acumulación de forma matemática y dinámica para que` |
| `backend/scripts/rotate_server_secret_key.py` | 23 | `--include-mongo     Sincronizar MongoDB espejo` |
| `backend/scripts/rotate_server_secret_key.py` | 24 | `--only-sql          Solo SQL, ignorar MongoDB` |
| `backend/scripts/rotate_server_secret_key.py` | 369 | `# Sincronizar MongoDB si aplica` |
| `backend/scripts/rotate_server_secret_key.py` | 372 | `sync_to_mongodb(server_id, updates)` |
| `backend/scripts/rotate_server_secret_key.py` | 376 | `logger.warning(f"[SECRET_ROTATION][PARTIAL_SYNC] {server_name}: MongoDB sync failed")` |
| `backend/scripts/rotate_server_secret_key.py` | 377 | `result['errors'].append(f"{server_name}: MongoDB sync failed - {type(e).__name__}")` |
| `backend/scripts/rotate_server_secret_key.py` | 393 | `def sync_to_mongodb(server_id: str, updates: Dict):` |
| `backend/scripts/rotate_server_secret_key.py` | 395 | `Sincroniza secretos rotados a MongoDB.` |
| `backend/scripts/rotate_server_secret_key.py` | 403 | `raise Exception("MongoDB no disponible")` |
| `backend/scripts/rotate_server_secret_key.py` | 405 | `# Buscar y actualizar en MongoDB` |
| `backend/scripts/rotate_server_secret_key.py` | 408 | `# Mapear campos SQL a MongoDB` |
| `backend/scripts/rotate_server_secret_key.py` | 515 | `print(f"MongoDB sincronizado: {report['mongo_synced']}")` |
| `backend/scripts/rotate_server_secret_key.py` | 536 | `parser.add_argument('--include-mongo', action='store_true', help='Sincronizar MongoDB espejo')` |
| `backend/scripts/rotate_server_secret_key.py` | 537 | `parser.add_argument('--only-sql', action='store_true', help='Solo SQL, ignorar MongoDB')` |
| `backend/scripts/rotate_server_secret_key.py` | 617 | `print(f"   → MongoDB sincronizado: {rotation_result['mongo_synced']}")` |
| `backend/scripts/create_unidades_negocio_table.py` | 5 | `eliminando la dependencia de MongoDB para esta información.` |
| `backend/scripts/encrypt_core_server_secrets.py` | 46 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/scripts/encrypt_core_server_secrets.py` | 84 | `mongodb_id` |
| `backend/scripts/encrypt_core_server_secrets.py` | 152 | `'mongodb_id': server.get('mongodb_id'),` |
| `backend/scripts/encrypt_core_server_secrets.py` | 250 | `async def sync_core_to_mongo(server_id: str, mongodb_id: str) -> dict:` |
| `backend/scripts/encrypt_core_server_secrets.py` | 252 | `Sincroniza el estado de cifrado CORE a MongoDB (si tiene secretos).` |
| `backend/scripts/encrypt_core_server_secrets.py` | 254 | `Note: MongoDB generalmente no tiene secretos de CORE, solo metadatos.` |
| `backend/scripts/encrypt_core_server_secrets.py` | 257 | `if not mongodb_id:` |
| `backend/scripts/encrypt_core_server_secrets.py` | 258 | `return {'success': True, 'message': 'No mongodb_id'}` |
| `backend/scripts/encrypt_core_server_secrets.py` | 260 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/scripts/encrypt_core_server_secrets.py` | 263 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/scripts/encrypt_core_server_secrets.py` | 267 | `server = await db.servers.find_one({'id': mongodb_id})` |
| `backend/scripts/encrypt_core_server_secrets.py` | 270 | `return {'success': True, 'message': 'CORE not in MongoDB (normal)'}` |
| `backend/scripts/encrypt_core_server_secrets.py` | 284 | `await db.servers.update_one({'id': mongodb_id}, {'$set': updates})` |
| `backend/scripts/encrypt_core_server_secrets.py` | 287 | `return {'success': True, 'message': 'No secrets in MongoDB'}` |
| `backend/scripts/encrypt_core_server_secrets.py` | 369 | `mongodb_id = server_info.get('mongodb_id')` |
| `backend/scripts/encrypt_core_server_secrets.py` | 395 | `# Sincronizar MongoDB (generalmente no tiene secretos de CORE)` |
| `backend/scripts/encrypt_core_server_secrets.py` | 396 | `mongo_result = await sync_core_to_mongo(server_id, mongodb_id)` |
| `backend/scripts/encrypt_core_server_secrets.py` | 400 | `print(f"    ✓ MongoDB sincronizado")` |
| `backend/scripts/encrypt_core_server_secrets.py` | 402 | `print(f"    ✓ MongoDB: {mongo_result.get('message')}")` |
| `backend/scripts/encrypt_core_server_secrets.py` | 436 | `print(f"MongoDB sincronizado: {report['mongo_synced']}")` |
| `backend/scripts/run_historical_load_compras.py` | 111 | `"""Obtiene conexión a MongoDB."""` |
| `backend/scripts/run_historical_load_compras.py` | 116 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/scripts/run_historical_load_compras.py` | 117 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/scripts/run_historical_load_compras.py` | 118 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/scripts/run_historical_load_24_months.py` | 67 | `DESTINATION_MONGO = "MONGODB"               # Solo checkpoint/log/staging` |
| `backend/scripts/run_historical_load_24_months.py` | 86 | `"""Obtiene conexión a MongoDB."""` |
| `backend/scripts/run_historical_load_24_months.py` | 91 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/scripts/run_historical_load_24_months.py` | 92 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/scripts/run_historical_load_24_months.py` | 93 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/scripts/run_historical_load_24_months.py` | 194 | `FASE 2.3: Necesario para carga histórica que lee directamente de MongoDB.` |
| `backend/scripts/run_historical_load_24_months.py` | 332 | `DESTINO FINAL - MongoDB queda solo como checkpoint/log.` |
| `backend/scripts/run_historical_load_24_months.py` | 348 | `"mongo_staging": 0  # Ya no se escribe a MongoDB como final` |
| `backend/scripts/run_historical_load_24_months.py` | 427 | `MongoDB solo para checkpoint/log.` |
| `backend/scripts/run_historical_load_24_months.py` | 609 | `logger.info(f"[DRY_RUN] Plan generado. Destino: {DESTINATION_SQL}. MongoDB: checkpoint/log only")` |
| `backend/scripts/run_historical_load_24_months.py` | 640 | `"mongo_final_inserted": 0,  # Siempre 0 - MongoDB no es destino final` |
| `backend/scripts/solucion_ventas_acumuladas_cero.py` | 11 | `contiene la lógica abstracta del motor de agregación usado en React.` |
| `backend/scripts/solucion_ventas_acumuladas_cero.py` | 46 | `[3] MOTOR DE AGREGACIÓN EN CALIENTE (accumulatedUnits):` |
| `backend/scripts/solucion_ventas_acumuladas_cero.py` | 58 | `# --- LÓGICA ABSTRAÍDA EN PYTHON (MOTOR DE AGREGACIÓN) ---` |
| `backend/api/catalogos_sistemas.py` | 23 | `- NO usar MongoDB` |
| `backend/api/admin_data_quality.py` | 13 | `- NO MongoDB` |
| `backend/api/admin_scheduler_resync.py` | 18 | `NO USA MONGODB - 100% SQL Server` |
| `backend/api/sync_receiver.py` | 59 | `"""Inicializa el módulo con la conexión a MongoDB."""` |
| `backend/api/sync_receiver.py` | 66 | `"""Obtiene la conexión a MongoDB."""` |
| `backend/api/admin_core_connections.py` | 111 | `# Guardar en MongoDB si está disponible` |
| `backend/api/admin_core_connections.py` | 245 | `# Verificar MongoDB si aplica` |
| `backend/api/admin_core_connections.py` | 251 | `formatted['mongodb_id'] = str(mongo_server.get('_id')) if mongo_server else None` |
| `backend/api/admin_core_connections.py` | 254 | `formatted['mongodb_id'] = None` |
| `backend/core/server_registry.py` | 214 | `Garantiza paridad con el esquema de MongoDB.` |
| `backend/core/server_registry.py` | 232 | `'mongodb_id': str(row.get('mongodb_id', '')) if row.get('mongodb_id') else None,` |
| `backend/core/server_registry.py` | 327 | `Busca tanto por id como por mongodb_id para compatibilidad.` |
| `backend/core/server_registry.py` | 337 | `WHERE (CAST(id AS VARCHAR(50)) = '{safe_id}' OR mongodb_id = '{safe_id}')` |
| `backend/core/server_registry.py` | 368 | `Convierte un documento MongoDB al formato normalizado.` |
| `backend/core/server_registry.py` | 380 | `# Asegurar que no haya _id de MongoDB` |
| `backend/core/server_registry.py` | 424 | `logger.error(f"[SERVER_REGISTRY][MONGODB_ERROR] Error obteniendo servidores desde MongoDB: {e}")` |
| `backend/core/server_registry.py` | 445 | `logger.error(f"[SERVER_REGISTRY][MONGODB_ERROR] Error buscando servidor {server_id}: {e}")` |
| `backend/core/server_registry.py` | 465 | `2. MongoDB (si allow_mongo_fallback=True y no se encontró en SQL)` |
| `backend/core/server_registry.py` | 469 | `db: Conexión a MongoDB (requerido si allow_mongo_fallback=True)` |
| `backend/core/server_registry.py` | 471 | `allow_mongo_fallback: Permitir fallback a MongoDB` |
| `backend/core/server_registry.py` | 483 | `# Fallback a MongoDB` |
| `backend/core/server_registry.py` | 509 | `2. MongoDB (si allow_mongo_fallback=True y SQL devuelve vacío)` |
| `backend/core/server_registry.py` | 512 | `db: Conexión a MongoDB (requerido si allow_mongo_fallback=True)` |
| `backend/core/server_registry.py` | 515 | `allow_mongo_fallback: Permitir fallback a MongoDB` |
| `backend/core/server_registry.py` | 534 | `# Fallback a MongoDB si SQL está vacío` |
| `backend/core/server_registry.py` | 577 | `filtered = [s for s in servers if s.get('id') in allowed_ids or s.get('mongodb_id') in allowed_ids]` |
| `backend/core/server_registry.py` | 636 | `if server.get('id') not in allowed and server.get('mongodb_id') not in allowed:` |
| `backend/core/server_registry.py` | 709 | `db: Conexión MongoDB (opcional)` |
| `backend/core/server_registry.py` | 727 | `if server.get('id') not in allowed and server.get('mongodb_id') not in allowed:` |
| `backend/core/server_registry.py` | 760 | `2. MongoDB collection `server_sucursales_config` (fallback)` |
| `backend/core/server_registry.py` | 764 | `db: Conexión a MongoDB` |
| `backend/core/server_registry.py` | 766 | `allow_mongo_fallback: Permitir fallback a MongoDB` |
| `backend/core/server_registry.py` | 782 | `# Fallback a MongoDB si no hay sucursales en SQL` |
| `backend/core/server_registry.py` | 793 | `# Fallback al campo sucursales del servidor en MongoDB` |
| `backend/core/server_registry.py` | 800 | `logger.warning(f"[SERVER_REGISTRY][SUCURSALES][MONGODB_FALLBACK] {len(sucursales)} sucursales para servidor {server_id}"...` |
| `backend/core/server_registry.py` | 802 | `logger.error(f"[SERVER_REGISTRY][SUCURSALES][MONGODB_ERROR] Error obteniendo sucursales: {e}")` |
| `backend/core/server_registry.py` | 849 | `'mongodb_id': record.get('mongodb_id'),  # Mapeo a MongoDB si existe` |
| `backend/core/server_registry.py` | 1031 | `Crea un servidor en EDARSAHUB SQL primero, luego sincroniza a MongoDB.` |
| `backend/core/server_registry.py` | 1037 | `db: Conexión MongoDB (para sync)` |
| `backend/core/server_registry.py` | 1039 | `sync_mongo: Si True, sincroniza a MongoDB después` |
| `backend/core/server_registry.py` | 1075 | `created_at, updated_at, mongodb_id` |
| `backend/core/server_registry.py` | 1109 | `server_id  # mongodb_id será el mismo inicialmente` |
| `backend/core/server_registry.py` | 1126 | `# Sincronizar a MongoDB` |
| `backend/core/server_registry.py` | 1151 | `logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado a MongoDB: {server_id}")` |
| `backend/core/server_registry.py` | 1154 | `sync_warnings.append(f"SQL exitoso pero MongoDB falló: {str(e)}")` |
| `backend/core/server_registry.py` | 1180 | `Actualiza un servidor en EDARSAHUB SQL primero, luego sincroniza a MongoDB.` |
| `backend/core/server_registry.py` | 1185 | `server_id: ID del servidor (SQL id o mongodb_id)` |
| `backend/core/server_registry.py` | 1187 | `db: Conexión MongoDB (para sync y para obtener password existente)` |
| `backend/core/server_registry.py` | 1189 | `sync_mongo: Si True, sincroniza a MongoDB después` |
| `backend/core/server_registry.py` | 1311 | `update_values.append(server_id)  # Para mongodb_id fallback` |
| `backend/core/server_registry.py` | 1316 | `WHERE CAST(id AS VARCHAR(50)) = %s OR mongodb_id = %s` |
| `backend/core/server_registry.py` | 1331 | `# Sincronizar a MongoDB` |
| `backend/core/server_registry.py` | 1350 | `logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado a MongoDB: {server_id}")` |
| `backend/core/server_registry.py` | 1353 | `sync_warnings.append(f"SQL actualizado pero MongoDB falló: {str(e)}")` |
| `backend/core/server_registry.py` | 1374 | `Desactiva (soft delete) un servidor en EDARSAHUB SQL, luego sincroniza a MongoDB.` |
| `backend/core/server_registry.py` | 1381 | `db: Conexión MongoDB (para sync)` |
| `backend/core/server_registry.py` | 1383 | `sync_mongo: Si True, sincroniza a MongoDB después` |
| `backend/core/server_registry.py` | 1415 | `WHERE CAST(id AS VARCHAR(50)) = %s OR mongodb_id = %s` |
| `backend/core/server_registry.py` | 1421 | `WHERE CAST(id AS VARCHAR(50)) = %s OR mongodb_id = %s` |
| `backend/core/server_registry.py` | 1437 | `# Sincronizar a MongoDB` |
| `backend/core/server_registry.py` | 1450 | `logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado a MongoDB: {server_id}")` |
| `backend/core/server_registry.py` | 1453 | `sync_warnings.append(f"SQL actualizado pero MongoDB falló: {str(e)}")` |
| `backend/core/server_registry.py` | 1469 | `Sincroniza un servidor específico desde SQL hacia MongoDB.` |
| `backend/core/server_registry.py` | 1475 | `db: Conexión MongoDB` |
| `backend/core/server_registry.py` | 1483 | `'error': 'Conexión MongoDB no disponible',` |
| `backend/core/server_registry.py` | 1499 | `# Construir documento MongoDB` |
| `backend/core/server_registry.py` | 1519 | `# Upsert en MongoDB` |
| `backend/core/server_registry.py` | 1532 | `'message': 'Servidor sincronizado a MongoDB'` |
| `backend/core/server_registry.py` | 1552 | `Usado para sincronizar servidores de SQL hacia MongoDB manteniendo` |
| `backend/core/server_registry.py` | 1559 | `Dict compatible con colección MongoDB servers` |
| `backend/core/server_registry.py` | 1617 | `'mongodb_id': sql_record.get('mongodb_id'),` |
| `backend/core/server_registry.py` | 1670 | `Reconcilia servidores entre SQL y MongoDB.` |
| `backend/core/server_registry.py` | 1673 | `sincroniza MongoDB para que sea espejo de SQL.` |
| `backend/core/server_registry.py` | 1676 | `db: Conexión MongoDB` |
| `backend/core/server_registry.py` | 1703 | `# Crear índice por ID y mongodb_id` |
| `backend/core/server_registry.py` | 1705 | `sql_by_mongodb_id = {s['mongodb_id']: s for s in sql_servers if s.get('mongodb_id')}` |
| `backend/core/server_registry.py` | 1707 | `# Obtener servidores de MongoDB` |
| `backend/core/server_registry.py` | 1709 | `report['warnings'].append('No se puede verificar MongoDB sin conexión')` |
| `backend/core/server_registry.py` | 1721 | `mongo_server = mongo_by_id.get(sql_id) or mongo_by_id.get(sql_server.get('mongodb_id'))` |
| `backend/core/server_registry.py` | 1736 | `logger.info(f"[SERVER_REGISTRY][RECONCILIATION_SYNC] Creado en MongoDB: {sql_id}")` |
| `backend/core/server_registry.py` | 1764 | `logger.info(f"[SERVER_REGISTRY][RECONCILIATION_SYNC] Actualizado en MongoDB: {sql_id}")` |
| `backend/core/server_registry.py` | 1770 | `if mongo_id not in sql_by_id and mongo_id not in sql_by_mongodb_id:` |
| `backend/core/server_registry.py` | 1776 | `report['warnings'].append(f"Servidor {mongo_id} existe en MongoDB pero no en SQL")` |
| `backend/core/server_registry.py` | 1797 | `# MÁXIMA: EDARSAHUB es el cerebro del sistema. No usar MongoDB.` |
| `backend/core/server_registry.py` | 1846 | `FASE M1: Fuente única EDARSAHUB, sin MongoDB.` |
| `backend/core/server_registry.py` | 1913 | `FASE M1: EDARSAHUB es el cerebro del sistema. No usa MongoDB.` |
| `backend/core/server_registry.py` | 2355 | `NO FUENTE: MongoDB db.servers` |
| `backend/core/server_registry.py` | 2365 | `- id, mongodb_id, name, system_type` |
| `backend/core/server_registry.py` | 2378 | `'mongodb_id': server.get('mongodb_id'),` |
| `backend/core/connection_resolver.py` | 274 | `"""Obtiene conexión a MongoDB"""` |
| `backend/core/connection_resolver.py` | 277 | `from pymongo import MongoClient` |
| `backend/core/connection_resolver.py` | 280 | `client = MongoClient(mongo_url)` |
| `backend/core/connection_resolver.py` | 283 | `logger.error(f"[ConnectionResolver] Error conectando a MongoDB: {e}")` |
| `backend/core/connection_resolver.py` | 288 | `"""Obtiene configuración de servidor desde MongoDB (menú Servidores SQL)"""` |
| `backend/core/connection_resolver.py` | 301 | `"""Obtiene configuración de API local desde MongoDB"""` |
| `backend/core/pool.py` | 605 | `# MOTOR CENTRAL SQL - execute_hub_query (Mayo 2026)` |
| `backend/core/pool.py` | 610 | `Motor central: Lee de SQL Server (EDARSAHUB) y devuelve el formato que el frontend espera.` |
| `backend/core/pool.py` | 611 | `NO requiere lógica de MongoDB - reemplazo directo.` |
| `backend/core/pool.py` | 703 | `# Motor central SQL (Mayo 2026)` |
| `backend/core/__init__.py` | 55 | `MONGODB_COLLECTIONS,` |
| `backend/core/__init__.py` | 56 | `MONGODB_INDEXES,` |
| `backend/core/source_resolver.py` | 96 | `source_type: Tipo de fuente (MPRO, SoftRestaurant, MongoDB, API)` |
| `backend/core/source_resolver.py` | 141 | `"""Serializa a diccionario para JSON/MongoDB."""` |
| `backend/core/auditoria.py` | 7 | `guardan temporalmente en MongoDB como fallback y se sincronizan después.` |
| `backend/core/auditoria.py` | 186 | `"""Retorna documento para MongoDB."""` |
| `backend/core/auditoria.py` | 200 | `Fallback a MongoDB si SQL no está disponible.` |
| `backend/core/auditoria.py` | 222 | `"""Obtiene conexión a MongoDB para fallback"""` |
| `backend/core/auditoria.py` | 225 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/core/auditoria.py` | 226 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/core/auditoria.py` | 227 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/core/auditoria.py` | 231 | `logger.error(f"Error conectando a MongoDB: {e}")` |
| `backend/core/auditoria.py` | 403 | `"""Guarda en MongoDB como fallback."""` |
| `backend/core/auditoria.py` | 413 | `logger.error(f"Error escribiendo auditoría a MongoDB: {e}")` |
| `backend/core/empresa_resolver.py` | 9 | `NO CONSULTA: MongoDB` |
| `backend/core/unidades_registry.py` | 16 | `- NO usar MongoDB como fuente funcional` |
| `backend/core/security.py` | 14 | `- La conexión a MongoDB se inyecta vía init_security()` |
| `backend/core/security.py` | 56 | `# Valor por defecto: false (MongoDB sigue siendo la fuente productiva)` |
| `backend/core/security.py` | 61 | `# INYECCIÓN DE DEPENDENCIA: MongoDB` |
| `backend/core/security.py` | 63 | `# La conexión a MongoDB se inyecta desde server.py para evitar imports circulares` |
| `backend/core/security.py` | 71 | `Inicializa el módulo de seguridad con la conexión a MongoDB.` |
| `backend/core/security.py` | 75 | `database: Instancia de AsyncIOMotorDatabase o None para usar stub` |
| `backend/core/security.py` | 85 | `logging.info("[SECURITY] Módulo de seguridad inicializado con conexión a MongoDB")` |
| `backend/core/security.py` | 89 | `"""Obtiene la conexión a MongoDB inyectada."""` |
| `backend/core/security.py` | 262 | `FASE 2-G: SQL-only (sin fallback MongoDB).` |
| `backend/core/security.py` | 283 | `# FASE 2-G: SQL-only (sin fallback MongoDB)` |
| `backend/core/security.py` | 309 | `FASE 2-G: Obtiene usuario SOLO de EDARSAHUB SQL (sin fallback MongoDB).` |
| `backend/core/security.py` | 436 | `# FASE 2-G: SQL-only (sin fallback MongoDB)` |
| `backend/core/security.py` | 486 | `Lista de empresa_ids permitidos (UUIDs MongoDB para compatibilidad)` |
| `backend/core/security.py` | 547 | `# Construir IN clause para empresas (UUIDs MongoDB)` |
| `backend/core/security.py` | 732 | `# FASE 2-G: SQL-Only (sin fallback MongoDB)` |
| `backend/core/security.py` | 743 | `# - MongoDB sigue siendo la fuente de autenticación` |
| `backend/core/security.py` | 769 | `FASE 2-D.1: Comparación pasiva MongoDB vs SQL.` |
| `backend/core/security.py` | 775 | `user_mongo: Usuario obtenido de MongoDB (actual productivo)` |
| `backend/core/security.py` | 785 | `'auth_source': 'MONGODB_CURRENT',` |
| `backend/core/security.py` | 789 | `'mongo': _safe_user_for_log(user_mongo, 'MONGODB'),` |
| `backend/core/security.py` | 808 | `# ID (PublicUUID vs MongoDB id)` |
| `backend/core/security.py` | 870 | `user_mongo: Usuario de MongoDB` |
| `backend/core/rbac_helper.py` | 8 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/core/rbac_helper.py` | 11 | `# Conexión a MongoDB (reutiliza la existente del entorno)` |
| `backend/core/rbac_helper.py` | 17 | `"""Obtiene conexión a MongoDB de forma lazy."""` |
| `backend/core/rbac_helper.py` | 20 | `_client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))` |
| `backend/core/config.py` | 25 | `# MongoDB` |
| `backend/core/config.py` | 26 | `MONGO_URL: str = os.environ.get("MONGO_URL", "<REDACTED_MONGO_URL>")` |
| `backend/core/context_resolver.py` | 27 | `Este módulo ha sido migrado de MongoDB a EDARSAHUB SQL.` |
| `backend/core/context_resolver.py` | 35 | `MongoDB ya no es fuente de datos para resolución de contexto.` |
| `backend/core/context_resolver.py` | 82 | `por UUIDs de MongoDB (empresas_permitidas del usuario).` |
| `backend/core/context_resolver.py` | 86 | `empresa_uuids: Lista de UUIDs MongoDB de empresas` |
| `backend/core/context_resolver.py` | 334 | `Obtiene una empresa por UUID MongoDB desde Sistema_Empresas.` |
| `backend/core/context_resolver.py` | 338 | `empresa_uuid: UUID MongoDB de la empresa` |
| `backend/core/context_resolver.py` | 377 | `MIGRACIÓN FASE 3-C: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.` |
| `backend/core/context_resolver.py` | 384 | `- id: ID de la empresa (UUID MongoDB)` |
| `backend/core/context_resolver.py` | 394 | `# 1. Obtener empresas permitidas (UUIDs MongoDB)` |
| `backend/core/context_resolver.py` | 427 | `empresa_id = empresa['id']  # UUID MongoDB` |
| `backend/core/context_resolver.py` | 444 | `'id': empresa_id,  # UUID MongoDB (compatibilidad)` |
| `backend/core/context_resolver.py` | 469 | `MIGRACIÓN FASE 3-C: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.` |
| `backend/core/context_resolver.py` | 473 | `unidad_id: ID de la unidad de negocio (empresa_id UUID MongoDB)` |
| `backend/core/context_resolver.py` | 524 | `MIGRACIÓN FASE 3-C: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.` |
| `backend/core/context_resolver.py` | 573 | `empresa_id = sucursal_info.get('empresa_id')  # UUID MongoDB` |
| `backend/core/user_access_context.py` | 29 | `Este módulo ha sido migrado de MongoDB a EDARSAHUB SQL.` |
| `backend/core/user_access_context.py` | 44 | `MongoDB ya no es fuente de datos para resolución de acceso.` |
| `backend/core/user_access_context.py` | 182 | `Obtiene todas las empresas activas (UUIDs MongoDB) para acceso global.` |
| `backend/core/user_access_context.py` | 209 | `Obtiene empresas asignadas al usuario (UUIDs MongoDB).` |
| `backend/core/user_access_context.py` | 252 | `Traduce empresas (UUIDs MongoDB) a servidores vía mapeos SQL.` |
| `backend/core/user_access_context.py` | 328 | `MIGRACIÓN FASE 3-D: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.` |
| `backend/core/user_access_context.py` | 479 | `# Todas las empresas activas (UUIDs MongoDB)` |
| `backend/core/mongo_stub.py` | 2 | `EDARSA HUB - MongoDB Stub Database` |
| `backend/core/mongo_stub.py` | 4 | `Implementación stub de MongoDB que no falla cuando se accede a colecciones.` |
| `backend/core/mongo_stub.py` | 6 | `Este módulo proporciona un objeto 'db' que simula la interfaz de MongoDB` |
| `backend/core/mongo_stub.py` | 21 | `Colección stub que simula una colección de MongoDB.` |
| `backend/core/mongo_stub.py` | 32 | `logger.debug(f"[MONGO_STUB] Acceso a colección '{self.name}' - MongoDB eliminado")` |
| `backend/core/mongo_stub.py` | 98 | `Cursor stub que simula un cursor de MongoDB.` |
| `backend/core/mongo_stub.py` | 170 | `Base de datos stub que simula una base de datos de MongoDB.` |
| `backend/core/mongo_stub.py` | 184 | `logger.info("[MONGO_STUB] Base de datos stub activa - MongoDB ELIMINADO")` |
| `backend/core/cerebro.py` | 8 | `- Esquemas de MongoDB` |
| `backend/core/cerebro.py` | 659 | `# MAPEO DE COLECCIONES MONGODB` |
| `backend/core/cerebro.py` | 662 | `MONGODB_COLLECTIONS = {` |
| `backend/core/cerebro.py` | 707 | `# ÍNDICES MONGODB REQUERIDOS` |
| `backend/core/cerebro.py` | 710 | `MONGODB_INDEXES = {` |
| `backend/core/cerebro.py` | 787 | `'MONGODB_COLLECTIONS', 'MONGODB_INDEXES',` |
| `backend/core/resilient_sql.py` | 141 | `"""Obtiene la configuración del servidor EDARSA HUB desde MongoDB."""` |
| `backend/core/resilient_sql.py` | 255 | `db: Conexión a MongoDB (para obtener credenciales)` |
| `backend/core/mongo_compat.py` | 2 | `EDARSA HUB - MongoDB Compatibility Layer` |
| `backend/core/mongo_compat.py` | 4 | `Capa de compatibilidad para operaciones MongoDB durante la migración a SQL Server.` |
| `backend/core/mongo_compat.py` | 6 | `Este módulo proporciona funciones helper que manejan el caso cuando MongoDB` |
| `backend/core/mongo_compat.py` | 22 | `# Referencia global a la conexión MongoDB (puede ser None)` |
| `backend/core/mongo_compat.py` | 28 | `Inicializa el módulo con la conexión MongoDB.` |
| `backend/core/mongo_compat.py` | 31 | `db: Instancia de AsyncIOMotorDatabase o None` |
| `backend/core/mongo_compat.py` | 36 | `logger.warning("[MONGO_COMPAT] Inicializado SIN MongoDB - Operaciones retornarán datos vacíos")` |
| `backend/core/mongo_compat.py` | 38 | `logger.info("[MONGO_COMPAT] Inicializado con conexión MongoDB")` |
| `backend/core/mongo_compat.py` | 42 | `"""Obtiene la conexión MongoDB (puede ser None)."""` |
| `backend/core/mongo_compat.py` | 47 | `"""Verifica si MongoDB está disponible."""` |
| `backend/core/mongo_compat.py` | 61 | `Busca un documento en MongoDB.` |
| `backend/core/mongo_compat.py` | 63 | `Si MongoDB no está disponible, retorna None.` |
| `backend/core/mongo_compat.py` | 66 | `logger.debug(f"[MONGO_COMPAT] find_one({collection_name}) - MongoDB no disponible")` |
| `backend/core/mongo_compat.py` | 88 | `Busca documentos en MongoDB.` |
| `backend/core/mongo_compat.py` | 90 | `Si MongoDB no está disponible, retorna lista vacía.` |
| `backend/core/mongo_compat.py` | 93 | `logger.debug(f"[MONGO_COMPAT] find({collection_name}) - MongoDB no disponible")` |
| `backend/core/mongo_compat.py` | 120 | `Cuenta documentos en MongoDB.` |
| `backend/core/mongo_compat.py` | 122 | `Si MongoDB no está disponible, retorna 0.` |
| `backend/core/mongo_compat.py` | 144 | `Inserta un documento en MongoDB.` |
| `backend/core/mongo_compat.py` | 146 | `Si MongoDB no está disponible, retorna None y loguea warning.` |
| `backend/core/mongo_compat.py` | 149 | `logger.warning(f"[MONGO_COMPAT] insert_one({collection_name}) - MongoDB no disponible, documento NO persistido")` |
| `backend/core/mongo_compat.py` | 166 | `Inserta múltiples documentos en MongoDB.` |
| `backend/core/mongo_compat.py` | 168 | `Si MongoDB no está disponible, retorna lista vacía.` |
| `backend/core/mongo_compat.py` | 171 | `logger.warning(f"[MONGO_COMPAT] insert_many({collection_name}) - MongoDB no disponible, {len(documents)} documentos NO p...` |
| `backend/core/mongo_compat.py` | 194 | `Actualiza un documento en MongoDB.` |
| `backend/core/mongo_compat.py` | 196 | `Si MongoDB no está disponible, retorna False.` |
| `backend/core/mongo_compat.py` | 199 | `logger.warning(f"[MONGO_COMPAT] update_one({collection_name}) - MongoDB no disponible")` |
| `backend/core/mongo_compat.py` | 217 | `Actualiza múltiples documentos en MongoDB.` |
| `backend/core/mongo_compat.py` | 219 | `Si MongoDB no está disponible, retorna 0.` |
| `backend/core/mongo_compat.py` | 222 | `logger.warning(f"[MONGO_COMPAT] update_many({collection_name}) - MongoDB no disponible")` |
| `backend/core/mongo_compat.py` | 243 | `Elimina un documento de MongoDB.` |
| `backend/core/mongo_compat.py` | 245 | `Si MongoDB no está disponible, retorna False.` |
| `backend/core/mongo_compat.py` | 248 | `logger.warning(f"[MONGO_COMPAT] delete_one({collection_name}) - MongoDB no disponible")` |
| `backend/core/mongo_compat.py` | 265 | `Elimina múltiples documentos de MongoDB.` |
| `backend/core/mongo_compat.py` | 267 | `Si MongoDB no está disponible, retorna 0.` |
| `backend/core/mongo_compat.py` | 270 | `logger.warning(f"[MONGO_COMPAT] delete_many({collection_name}) - MongoDB no disponible")` |
| `backend/core/mongo_compat.py` | 291 | `Ejecuta un pipeline de agregación en MongoDB.` |
| `backend/core/mongo_compat.py` | 293 | `Si MongoDB no está disponible, retorna lista vacía.` |
| `backend/core/mongo_compat.py` | 296 | `logger.debug(f"[MONGO_COMPAT] aggregate({collection_name}) - MongoDB no disponible")` |
| `backend/core/mongo_compat.py` | 314 | `Decorador para endpoints que requieren MongoDB.` |
| `backend/core/mongo_compat.py` | 316 | `Si MongoDB no está disponible, retorna error 503.` |
| `backend/core/mongo_compat.py` | 326 | `detail="Este endpoint requiere MongoDB que actualmente no está disponible. "` |
| `backend/core/mongo_compat.py` | 335 | `Decorador para endpoints donde MongoDB es opcional.` |
| `backend/core/mongo_compat.py` | 337 | `Si MongoDB no está disponible, retorna el valor por defecto.` |
| `backend/core/mongo_compat.py` | 345 | `logger.info(f"[MONGO_COMPAT] {func.__name__} - Retornando valor por defecto (MongoDB no disponible)")` |
| `backend/core/health_checker.py` | 40 | `MONGODB = "mongodb"` |
| `backend/core/health_checker.py` | 147 | `def _check_mongodb(self) -> SourceHealth:` |
| `backend/core/health_checker.py` | 148 | `"""Verifica conexión a MongoDB"""` |
| `backend/core/health_checker.py` | 151 | `from pymongo import MongoClient` |
| `backend/core/health_checker.py` | 155 | `client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)` |
| `backend/core/health_checker.py` | 161 | `name="MongoDB (EDARSA HUB)",` |
| `backend/core/health_checker.py` | 162 | `source_type=SourceType.MONGODB,` |
| `backend/core/health_checker.py` | 169 | `name="MongoDB (EDARSA HUB)",` |
| `backend/core/health_checker.py` | 170 | `source_type=SourceType.MONGODB,` |
| `backend/core/health_checker.py` | 179 | `from pymongo import MongoClient` |
| `backend/core/health_checker.py` | 183 | `client = MongoClient(mongo_url)` |
| `backend/core/health_checker.py` | 231 | `# Verificar MongoDB` |
| `backend/core/health_checker.py` | 232 | `mongo_health = self._check_mongodb()` |
| `backend/core/alcance_helper.py` | 175 | `db: Instancia de la base de datos MongoDB` |
| `backend/core/system_capability_resolver.py` | 40 | `- NO usar MongoDB` |
| `backend/core/inventory_analysis_core.py` | 18 | `- db: Cliente MongoDB (inyectado)` |
| `backend/core/inventory_analysis_core.py` | 127 | `db_client: Cliente de base de datos MongoDB` |
| `backend/core/inventory_analysis_core.py` | 224 | `db_client: Cliente MongoDB` |
| `backend/core/db.py` | 4 | `Gestión centralizada de conexiones a MongoDB y SQL Server.` |
| `backend/core/db.py` | 1117 | `# FUNCIONES DE MONGODB (Placeholders para fases futuras)` |
| `backend/core/db.py` | 1120 | `from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase` |
| `backend/core/db.py` | 1121 | `from pymongo import MongoClient` |
| `backend/core/db.py` | 1123 | `# Variables globales para conexiones MongoDB (se inicializarán en migración futura)` |
| `backend/core/db.py` | 1124 | `_mongo_client: Optional[AsyncIOMotorClient] = None` |
| `backend/core/db.py` | 1125 | `_mongo_db: Optional[AsyncIOMotorDatabase] = None` |
| `backend/core/db.py` | 1126 | `_sync_mongo_client: Optional[MongoClient] = None` |
| `backend/core/db.py` | 1129 | `async def get_mongo_client() -> AsyncIOMotorClient:` |
| `backend/core/db.py` | 1131 | `Obtiene el cliente MongoDB async.` |
| `backend/core/db.py` | 1136 | `raise RuntimeError("MongoDB client not initialized. Use server.py connection.")` |
| `backend/core/db.py` | 1140 | `async def get_mongo_db() -> AsyncIOMotorDatabase:` |
| `backend/core/db.py` | 1142 | `Obtiene la base de datos MongoDB async.` |
| `backend/core/db.py` | 1147 | `raise RuntimeError("MongoDB database not initialized. Use server.py connection.")` |
| `backend/core/db.py` | 1153 | `Obtiene la base de datos MongoDB síncrona.` |
| `backend/core/db.py` | 1158 | `raise RuntimeError("Sync MongoDB client not initialized. Use server.py connection.")` |
| `backend/core/db.py` | 1165 | `NOTA: Se usará cuando se migre MongoDB desde server.py (fase futura)` |
| `backend/core/db.py` | 1556 | `# MongoDB - Placeholders` |
| `backend/core/scheduler/job_logger.py` | 58 | `logger.info("[JOB_LOGGER] Inicializado con MongoDB")` |
| `backend/core/scheduler/job_logger.py` | 81 | `# MongoDB ELIMINADO - Solo persistir si db está disponible` |
| `backend/core/scheduler/job_logger.py` | 122 | `# MongoDB ELIMINADO - Solo persistir si db está disponible` |
| `backend/core/scheduler/job_logger.py` | 157 | `# MongoDB ELIMINADO - Solo persistir si db está disponible` |
| `backend/core/scheduler/job_logger.py` | 174 | `# MongoDB ELIMINADO - Retornar lista vacía si no hay db` |
| `backend/core/scheduler/job_logger.py` | 194 | `# MongoDB ELIMINADO - Retornar None si no hay db` |
| `backend/core/scheduler/job_logger.py` | 207 | `# MongoDB ELIMINADO - Retornar stats vacío si no hay db` |
| `backend/core/scheduler/job_logger.py` | 260 | `# MongoDB ELIMINADO - Retornar 0 si no hay db` |
| `backend/core/scheduler/job_logger.py` | 274 | `# MongoDB ELIMINADO - No hacer nada si no hay db` |
| `backend/core/scheduler/__init__.py` | 7 | `- Procesamiento de motor SLA` |
| `backend/core/scheduler/__init__.py` | 13 | `- Locks distribuidos vía MongoDB` |
| `backend/core/scheduler/scheduler_manager.py` | 75 | `db: Conexión MongoDB o StubDatabase (MongoDB ELIMINADO)` |
| `backend/core/scheduler/scheduler_manager.py` | 96 | `# NOTA: MongoDB ELIMINADO - Scheduler opera con StubDatabase` |
| `backend/core/scheduler/scheduler_manager.py` | 98 | `logger.info("[SCHEDULER] Inicializando con StubDatabase - MongoDB ELIMINADO")` |
| `backend/core/scheduler/scheduler_manager.py` | 1373 | `NOTA: MongoDB ELIMINADO - Siempre usa StubDatabase.` |
| `backend/core/scheduler/scheduler_manager.py` | 1396 | `NOTA: MongoDB ELIMINADO - Acepta db=None para modo SQL-only.` |
| `backend/core/scheduler/sql_repository.py` | 4 | `Funciones SQL para los jobs del scheduler (reemplazo de MongoDB).` |
| `backend/core/scheduler/routes.py` | 30 | `Inicializa las rutas con la conexión a MongoDB.` |
| `backend/core/scheduler/routes.py` | 32 | `NOTA: MongoDB ELIMINADO del sistema. Este módulo ahora opera con StubDatabase` |
| `backend/core/scheduler/routes.py` | 40 | `logger.info("[SCHEDULER_ROUTES] Inicializado con StubDatabase - MongoDB ELIMINADO")` |
| `backend/core/scheduler/routes.py` | 47 | `Obtiene la conexión a MongoDB.` |
| `backend/core/scheduler/routes.py` | 56 | `Verifica si MongoDB real está disponible.` |
| `backend/core/scheduler/jobs/pedidos_detector_job.py` | 61 | `COMPRAS-MONGO-001-F2: Migrado de MongoDB a SQL Server (Mayo 2026)` |
| `backend/core/scheduler/jobs/pedidos_detector_job.py` | 71 | `# Colecciones MongoDB removidas - ahora usa SQL` |
| `backend/core/scheduler/jobs/pedidos_detector_job.py` | 87 | `self._use_sql = True  # Flag para usar SQL en lugar de MongoDB` |
| `backend/core/scheduler/jobs/pedidos_detector_job.py` | 786 | `NOTA: Esta función verificaba inventarios en MongoDB.` |
| `backend/core/scheduler/jobs/pedidos_detector_job.py` | 793 | `# MongoDB ELIMINADO - Por ahora siempre retorna True` |
| `backend/core/scheduler/jobs/pedidos_detector_job.py` | 795 | `logger.debug("[PEDIDOS_DETECTOR] _inventario_valido: Retornando True (MongoDB eliminado)")` |
| `backend/core/scheduler/jobs/pedidos_detector_job.py` | 944 | `db: Conexión a MongoDB (async)` |
| `backend/core/scheduler/jobs/sync_comercial_endpoints_job.py` | 58 | `db: Conexión MongoDB (IGNORADA - usamos SQL directo)` |
| `backend/core/scheduler/jobs/rentabilidad_scheduler_job.py` | 10 | `utilizando el motor determinista local.` |
| `backend/core/scheduler/jobs/rentabilidad_scheduler_job.py` | 26 | `# 2. Iterar y procesar cada pedido a través del motor blindado de rentabilidad` |
| `backend/core/scheduler/jobs/rentabilidad_scheduler_job.py` | 36 | `# 3. Si el motor determina que requiere aprobación por bajo margen, disparar alerta` |
| `backend/core/scheduler/jobs/sync_comercial_v2_job.py` | 14 | `- Lock distribuido (MongoDB) para evitar ejecuciones simultáneas` |
| `backend/core/scheduler/jobs/sync_comercial_v2_job.py` | 25 | `- MongoDB solo para locks técnicos, NO para datos de negocio` |
| `backend/core/scheduler/jobs/sync_comercial_v2_job.py` | 170 | `db: Conexión MongoDB (para locks/logs técnicos, NO para datos de negocio)` |
| `backend/core/scheduler/jobs/sync_short_comercial_job.py` | 37 | `db: Conexión a MongoDB` |
| `backend/core/scheduler/jobs/sla_job.py` | 4 | `Job para procesamiento automático del motor SLA.` |
| `backend/core/scheduler/jobs/sync_propinas_tpv_job.py` | 22 | `- MongoDB NO es fuente financiera` |
| `backend/core/scheduler/jobs/sync_nightly_comercial_job.py` | 39 | `db: Conexión a MongoDB` |
| `backend/core/scheduler/jobs/base_job.py` | 33 | `db: Conexión MongoDB` |
| `backend/core/scheduler/jobs/inventarios_detector_job.py` | 187 | `"""Genera query MongoDB para buscar por esta clave."""` |
| `backend/core/scheduler/jobs/inventarios_detector_job.py` | 218 | `- Colección `inventarios_procesados_auto` en MongoDB` |
| `backend/core/scheduler/jobs/inventarios_detector_job.py` | 262 | `Ya no depende de MongoDB para tracking de inventarios.` |
| `backend/core/scheduler/locks/distributed_lock.py` | 6 | `Usa MongoDB para locks persistentes que funcionan con múltiples` |
| `backend/core/scheduler/locks/distributed_lock.py` | 21 | `Lock distribuido basado en MongoDB.` |
| `backend/core/scheduler/locks/distributed_lock.py` | 35 | `db: Conexión MongoDB` |
| `backend/core/scheduler/locks/distributed_lock.py` | 253 | `logger.info("[LOCK_MANAGER] Inicializado con MongoDB")` |
| `backend/core/scheduler/locks/distributed_lock.py` | 299 | `Se usa cuando MongoDB no está disponible (modo SQL-only).` |
| `backend/core/communications/routes.py` | 38 | `# INYECCIÓN DE DEPENDENCIA: MongoDB` |
| `backend/core/communications/routes.py` | 46 | `Inicializa las rutas con la conexión a MongoDB.` |
| `backend/core/communications/routes.py` | 48 | `NOTA: MongoDB ELIMINADO del sistema. Este módulo ahora opera con StubDatabase` |
| `backend/core/communications/routes.py` | 52 | `database: Instancia de AsyncIOMotorDatabase o StubDatabase` |
| `backend/core/communications/routes.py` | 59 | `logger.info("[NOTIFICATIONS] Inicializado con StubDatabase - MongoDB ELIMINADO")` |
| `backend/core/communications/routes.py` | 66 | `Obtiene la conexión a MongoDB inyectada.` |
| `backend/core/communications/routes.py` | 75 | `Verifica si MongoDB real está disponible.` |
| `backend/core/communications/dispatcher/dispatcher.py` | 46 | `- Operaciones de MongoDB pasan por StubDatabase` |
| `backend/core/communications/dispatcher/dispatcher.py` | 104 | `logger.info("[DISPATCHER] Modo SQL-only: omitiendo carga de providers desde MongoDB")` |
| `backend/core/communications/notifications/service.py` | 45 | `- Operaciones de MongoDB pasan por StubDatabase` |
| `backend/core/communications/notifications/schemas.py` | 6 | `Colecciones MongoDB:` |
| `backend/core/communications/audit/audit_service.py` | 26 | `- Operaciones de MongoDB pasan por StubDatabase` |
| `backend/core/communications/scripts/__init__.py` | 22 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/core/communications/scripts/__init__.py` | 362 | `db: Conexión a MongoDB` |
| `backend/core/communications/scripts/__init__.py` | 380 | `mongo_url = os.environ.get("MONGO_URL", "<REDACTED_MONGO_URL>")` |
| `backend/core/communications/scripts/__init__.py` | 383 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/core/centro_control/email_notifications.py` | 7 | `1. MongoDB (colección alert_recipients) - Prioridad` |
| `backend/core/centro_control/email_notifications.py` | 56 | `Prioridad: MongoDB > Variable de entorno` |
| `backend/core/centro_control/email_notifications.py` | 58 | `# Intentar obtener de MongoDB primero` |
| `backend/core/centro_control/email_notifications.py` | 65 | `logger.debug(f"[EMAIL] No se pudo obtener recipients de MongoDB: {e}")` |
| `backend/core/centro_control/recipients_manager.py` | 4 | `Almacena y gestiona los destinatarios de notificaciones en MongoDB.` |
| `backend/core/centro_control/recipients_manager.py` | 23 | `from pymongo import MongoClient` |
| `backend/core/centro_control/recipients_manager.py` | 28 | `# MongoDB connection` |
| `backend/core/centro_control/recipients_manager.py` | 29 | `MONGO_URL = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/core/centro_control/recipients_manager.py` | 39 | `client = MongoClient(MONGO_URL)` |
| `backend/core/centro_control/whatsapp_notifications.py` | 7 | `1. MongoDB (colección alert_recipients) - Prioridad` |
| `backend/core/centro_control/whatsapp_notifications.py` | 65 | `Prioridad: MongoDB > Variable de entorno` |
| `backend/core/centro_control/whatsapp_notifications.py` | 67 | `# Intentar obtener de MongoDB primero` |
| `backend/core/centro_control/whatsapp_notifications.py` | 74 | `logger.debug(f"[WHATSAPP] No se pudo obtener recipients de MongoDB: {e}")` |
| `backend/core/centro_control/routes.py` | 426 | `- MongoDB (EDARSA HUB)` |
| `backend/core/centro_control/routes.py` | 1195 | `Los destinatarios se almacenan en MongoDB y son utilizados por los` |
| `backend/core/auth/__init__.py` | 5 | `NO reemplaza el flujo MongoDB actual.` |
| `backend/core/auth/user_repository_sql.py` | 8 | `- NO reemplaza el flujo actual de MongoDB` |
| `backend/core/auth/user_repository_sql.py` | 10 | `- MongoDB sigue siendo la fuente productiva de autenticación` |
| `backend/core/auth/user_repository_sql.py` | 136 | `Construye diccionario de usuario compatible con estructura MongoDB.` |
| `backend/core/auth/user_repository_sql.py` | 144 | `# Mapeo de rol SQL a rol MongoDB` |
| `backend/core/auth/user_repository_sql.py` | 161 | `# Campos compatibles con MongoDB` |
| `backend/core/auth/user_repository_sql.py` | 197 | `Dict con estructura compatible MongoDB o None si no existe` |
| `backend/core/auth/user_repository_sql.py` | 242 | `Dict con estructura compatible MongoDB o None si no existe` |
| `backend/core/auth/user_repository_sql.py` | 341 | `# FUNCIONES DE COMPARACIÓN MONGODB VS SQL` |
| `backend/core/auth/user_repository_sql.py` | 346 | `Compara usuario entre MongoDB y SQL.` |
| `backend/core/auth/user_repository_sql.py` | 354 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/core/auth/user_repository_sql.py` | 360 | `# Obtener de MongoDB` |
| `backend/core/auth/user_repository_sql.py` | 361 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/core/auth/user_repository_sql.py` | 363 | `mongo_client = AsyncIOMotorClient(mongo_url)` |
| `backend/core/auth/user_repository_sql.py` | 473 | `Lista diferencias de migración Auth entre MongoDB y SQL para todos los usuarios SQL.` |
| `backend/core/auth/user_repository_sql.py` | 585 | `# Mapeo de rol MongoDB a SQL` |
| `backend/core/auth/user_repository_sql.py` | 899 | `Reemplaza la función find_user_by_email de MongoDB.` |
| `backend/core/auth/user_repository_sql.py` | 920 | `Reemplaza la función find_user_by_id de MongoDB.` |
| `backend/core/rbac/service.py` | 2 | `EDARSA HUB - RBAC Service (Motor de Autorización)` |
| `backend/core/rbac/service.py` | 4 | `Motor central de autorización basado en roles.` |
| `backend/core/rbac/service.py` | 87 | `# MOTOR DE AUTORIZACIÓN` |
| `backend/core/rbac/__init__.py` | 7 | `MongoDB ya NO es fuente de datos para RBAC.` |
| `backend/core/rbac/__init__.py` | 13 | `- service.py: Motor de autorización central` |
| `backend/core/rbac/repository_sql.py` | 181 | `"nombre": codigo,  # Usar código como nombre (compatible con MongoDB)` |
| `backend/core/rbac/repository.py` | 7 | `MongoDB ya NO es fuente de datos para RBAC.` |
| `backend/core/rbac/routes.py` | 28 | `from pymongo import MongoClient` |
| `backend/core/rbac/routes.py` | 47 | `"""Obtiene conexión a MongoDB de forma síncrona."""` |
| `backend/core/rbac/routes.py` | 48 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/core/rbac/routes.py` | 50 | `client = MongoClient(mongo_url)` |
| `backend/core/rbac/middleware.py` | 34 | `"""Obtiene conexión a MongoDB de forma síncrona."""` |
| `backend/core/rbac/middleware.py` | 36 | `from pymongo import MongoClient` |
| `backend/core/rbac/middleware.py` | 37 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/core/rbac/middleware.py` | 39 | `client = MongoClient(mongo_url)` |
| `backend/core/rbac/schemas.py` | 6 | `Colecciones MongoDB:` |
| `backend/routes/portal_proveedores.py` | 4 | `Usa la misma conexión MongoDB y los servidores configurados en EDARSA HUB` |

## Hallazgos REVISAR_PERMITIDO_TEMPORAL

| Archivo | Línea | Código |
|---|---:|---|
| `backend/limpiar_tests_dns.py` | 37 | `f.write("- Eliminación definitiva de dependencias MongoDB.\n")` |
| `backend/server.py` | 115 | `# MongoDB ELIMINADO - Usar StubDatabase para evitar errores en código legacy` |
| `backend/server.py` | 555 | `# - ARQUITECTURA: SQL Server (persistencia) + MongoDB (cache)` |
| `backend/server.py` | 643 | `# ARQUITECTURA: SQL Server EDARSA HUB (persistencia) + MongoDB (cache)` |
| `backend/server.py` | 708 | `# Cache service (100% SQL - MongoDB eliminado)` |
| `backend/server.py` | 1322 | `# FASE P1.4-B (Dic 2025): Corregido para aceptar objetos JSON (EDARSAHUB) o strings (legacy MongoDB)` |
| `backend/server.py` | 1342 | `config_origin: Optional[str] = None  # "EDARSAHUB_SQL" \| "MONGODB_LEGACY"` |
| `backend/server.py` | 1881 | `- MongoDB queda como espejo legacy` |
| `backend/server.py` | 1939 | `2. MongoDB (fallback legacy)` |
| `backend/server.py` | 1966 | `2. MongoDB (fallback legacy)` |
| `backend/server.py` | 1992 | `- MongoDB queda como espejo legacy` |
| `backend/server.py` | 2051 | `- MongoDB queda como espejo legacy` |
| `backend/server.py` | 6303 | `Usa cache en MongoDB para evitar recalcular.` |
| `backend/modules/comercial/cache_service.py` | 25 | `# Importar db desde server.py (motor async client)` |
| `backend/modules/comercial/cache_service.py` | 33 | `# Referencia global a MongoDB (evita circular import con server.py)` |
| `backend/modules/comercial/cache_service.py` | 38 | `DEPRECADO: MongoDB ya no se usa.` |
| `backend/modules/comercial/cache_service.py` | 44 | `logging.warning("[COMERCIAL] Cache service - MongoDB deprecado, funcionalidad limitada")` |
| `backend/modules/comercial/cache_service.py` | 48 | `DEPRECADO: MongoDB ya no se usa.` |
| `backend/modules/comercial/cache_service.py` | 54 | `logging.debug("[COMERCIAL] get_db() - MongoDB deprecado")` |
| `backend/modules/comercial/repository.py` | 45 | `# DEPRECADO: MongoDB ya no se usa (Mayo 2026)` |
| `backend/modules/comercial/repository.py` | 49 | `"""DEPRECADO: MongoDB eliminado. No hace nada."""` |
| `backend/modules/comercial/repository.py` | 54 | `"""DEPRECADO: MongoDB eliminado. Retorna None siempre."""` |
| `backend/modules/comercial/kpis_repository.py` | 33 | `DEPRECADO: MongoDB ya no se usa para KPIs.` |
| `backend/modules/comercial/kpis_repository.py` | 39 | `logging.warning("[COMERCIAL] KPIs repository - MongoDB deprecado")` |
| `backend/modules/comercial/kpis_repository.py` | 44 | `DEPRECADO: MongoDB ya no se usa.` |
| `backend/modules/comercial/kpis_repository.py` | 49 | `logging.debug("[COMERCIAL] KPIs get_db() - MongoDB deprecado, retornando None")` |
| `backend/modules/comercial/routes.py` | 2984 | `# ARQUITECTURA: Obtener nombre de unidad desde EDARSAHUB (primario) o MongoDB (LEGACY_FALLBACK)` |
| `backend/modules/comercial/routes.py` | 2987 | `logging.warning(f"[LEGACY_FALLBACK] Mesas: Nombre de sucursal {sucursal} obtenido de MongoDB")` |
| `backend/modules/fase2_operativo/repositories/cargos_repository.py` | 377 | `Mapea campos SQL → formato MongoDB/API legacy.` |
| `backend/modules/api_connections/universal_test_routes.py` | 22 | `- MongoDB` |
| `backend/modules/rh/repository.py` | 50 | `# ID del servidor EDARSA HUB en MongoDB (LEGACY - ya no se usa para conexión)` |
| `backend/modules/configuracion/repositories/config_asignaciones_repository.py` | 8 | `Las operaciones legacy de MongoDB pasan por StubDatabase sin fallar.` |
| `backend/modules/auth/repository.py` | 45 | `DEPRECADO: MongoDB ya no se usa.` |
| `backend/modules/auth/repository.py` | 50 | `logging.warning("[AUTH] get_db() llamado pero MongoDB está deprecado. Auth usa 100% SQL.")` |
| `backend/modules/auth/routes.py` | 688 | `# - MongoDB es ubicacion TRANSITORIA/LEGACY para usuarios` |
| `backend/modules/comercial_v2/__init__.py` | 13 | `- NO consultan SQL vivo ni MongoDB cache` |
| `backend/modules/comercial_v2/repository_readonly.py` | 10 | `- MongoDB cache` |
| `backend/modules/comercial_v2/schemas_api.py` | 61 | `mongodb_cache: bool = False` |
| `backend/modules/comercial_v2/routes.py` | 10 | `- MongoDB cache` |
| `backend/modules/finanzas/tesoreria.py` | 754 | `NOTA TÉCNICA: MongoDB se mantiene como registry legacy parcial para fallback.` |
| `backend/modules/finanzas/repository_mpro.py` | 40 | `db: Instancia de MongoDB (solo para fallback legacy, preferir SQL)` |
| `backend/modules/finanzas/repository_mpro.py` | 50 | `FALLBACK: MongoDB solo si SQL falla (config_origin = MONGODB_LEGACY)` |
| `backend/modules/finanzas/propinas_tpv/__init__.py` | 10 | `# - MongoDB = Solo cache de lectura rápida (propinas_cache_*)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 10 | `- MongoDB = Solo cache` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 131 | `# Verificar MongoDB (cache)` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 144 | `"arquitectura": "SQL Server (persistencia) + MongoDB (cache)",` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 169 | `- Crea índices de cache en MongoDB` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 219 | `4. Invalida cache MongoDB` |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 426 | `"""Obtiene estadísticas del cache MongoDB."""` |
| `backend/modules/finanzas/propinas_tpv/sql_repository.py` | 15 | `- MongoDB = Solo cache (gestionado por cache_manager.py)` |
| `backend/modules/finanzas/propinas_tpv/cache_manager.py` | 8 | `- Gestión de cache en MongoDB` |
| `backend/modules/finanzas/propinas_tpv/cache_manager.py` | 13 | `- MongoDB = Solo cache de lectura rápida` |
| `backend/modules/finanzas/propinas_tpv/cache_manager.py` | 32 | `from motor.motor_asyncio import AsyncIOMotorDatabase` |
| `backend/modules/finanzas/propinas_tpv/cache_manager.py` | 39 | `Gestor de cache MongoDB para el módulo de Propinas TPV.` |
| `backend/modules/finanzas/propinas_tpv/cache_manager.py` | 53 | `def __init__(self, db: AsyncIOMotorDatabase):` |
| `backend/modules/finanzas/propinas_tpv/cache_manager.py` | 58 | `db: Conexión a MongoDB` |
| `backend/modules/finanzas/propinas_tpv/service_sql.py` | 9 | `- Orquestación de SQL Server (escritura) + MongoDB (cache/lectura)` |
| `backend/modules/finanzas/propinas_tpv/service_sql.py` | 14 | `- ESCRITURA: Siempre a SQL Server → Invalidar cache MongoDB` |
| `backend/modules/finanzas/propinas_tpv/service_sql.py` | 15 | `- LECTURA: Cache MongoDB → Si miss, SQL Server → Actualizar cache` |
| `backend/modules/finanzas/propinas_tpv/service_sql.py` | 51 | `SoftRestaurant (Lectura) → SQL Server (Persistencia) → MongoDB (Cache)` |
| `backend/modules/finanzas/propinas_tpv/service_sql.py` | 76 | `2. Crea índices de cache en MongoDB` |
| `backend/modules/finanzas/propinas_tpv/service_sql.py` | 144 | `5. Invalidar cache MongoDB` |
| `backend/modules/finanzas/propinas_tpv/service_sql.py` | 341 | `1. Buscar en cache MongoDB` |
| `backend/scripts/carga_historica_fase23.py` | 5 | `⚠️ DEPRECATED (Mayo 2026): Este script usa MongoDB que ha sido reemplazado por SQL Server.` |
| `backend/scripts/audit_mongo_legacy.py` | 9 | `r"pymongo",` |
| `backend/scripts/audit_mongo_legacy.py` | 10 | `r"motor",` |
| `backend/scripts/audit_mongo_legacy.py` | 11 | `r"mongodb",` |
| `backend/scripts/audit_mongo_legacy.py` | 12 | `r"MongoClient",` |
| `backend/scripts/audit_mongo_legacy.py` | 13 | `r"AsyncIOMotorClient",` |
| `backend/scripts/audit_mongo_legacy.py` | 63 | `md.append("Objetivo: localizar referencias MongoDB/pymongo/motor y clasificarlas para eliminación o justificación tempor...` |
| `backend/scripts/audit_mongo_legacy.py` | 93 | `md.append("- MongoDB no debe ser fuente de verdad productiva.\n")` |
| `backend/scripts/audit_mongo_legacy.py` | 94 | `md.append("- Endpoints visuales no deben depender de MongoDB.\n")` |
| `backend/scripts/run_historical_load_24_months.py` | 410 | `logger.warning("[DEPRECATED] upsert_kpi_batch_mongo_staging - MongoDB NO es destino final")` |
| `backend/scripts/run_historical_load_24_months.py` | 442 | `# DEPRECATED: MongoDB staging` |
| `backend/tests/test_automatizacion_compras_fase4.py` | 15 | `COLECCIONES MONGODB:` |
| `backend/tests/test_config.py` | 33 | `# MongoDB` |
| `backend/tests/test_config.py` | 34 | `TEST_MONGO_URL = os.getenv('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/tests/test_simulacion_controlada.py` | 136 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/tests/test_simulacion_controlada.py` | 153 | `"""Obtiene servidores activos de MongoDB."""` |
| `backend/tests/test_simulacion_controlada.py` | 154 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/tests/test_simulacion_controlada.py` | 161 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/tests/test_simulacion_controlada.py` | 219 | `print("FASE 1: Obteniendo servidores de MongoDB...")` |
| `backend/tests/test_migracion_servidores_sql.py` | 2 | `Test de Validación: Migración de Servidores MongoDB -> EDARSAHUB SQL` |
| `backend/tests/test_migracion_servidores_sql.py` | 8 | `2. Que el fallback a MongoDB funcione si SQL falla` |
| `backend/tests/test_migracion_servidores_sql.py` | 9 | `3. Paridad estructural entre SQL y MongoDB` |
| `backend/tests/test_migracion_servidores_sql.py` | 32 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/tests/test_migracion_servidores_sql.py` | 33 | `from pymongo import MongoClient` |
| `backend/tests/test_migracion_servidores_sql.py` | 79 | `def test_paridad_sql_mongodb():` |
| `backend/tests/test_migracion_servidores_sql.py` | 80 | `"""Verifica paridad entre datos de SQL y MongoDB."""` |
| `backend/tests/test_migracion_servidores_sql.py` | 81 | `print("\n=== TEST: Paridad SQL vs MongoDB ===")` |
| `backend/tests/test_migracion_servidores_sql.py` | 87 | `# Obtener de MongoDB` |
| `backend/tests/test_migracion_servidores_sql.py` | 88 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/tests/test_migracion_servidores_sql.py` | 89 | `client = MongoClient(mongo_url)` |
| `backend/tests/test_migracion_servidores_sql.py` | 105 | `print(f"  MongoDB: {len(mongo_servers)} servidores")` |
| `backend/tests/test_migracion_servidores_sql.py` | 114 | `print(f"  ⚠ Solo en MongoDB: {solo_mongo}")` |
| `backend/tests/test_migracion_servidores_sql.py` | 129 | `# Inicializar MongoDB` |
| `backend/tests/test_migracion_servidores_sql.py` | 130 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/tests/test_migracion_servidores_sql.py` | 131 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/tests/test_migracion_servidores_sql.py` | 179 | `results.append(("Paridad SQL/MongoDB", test_paridad_sql_mongodb()))` |
| `backend/tests/test_migracion_servidores_sql.py` | 182 | `results.append(("Paridad SQL/MongoDB", False))` |
| `backend/tests/test_e2e_flujo_completo.py` | 6 | `⚠️ DEPRECATED (Mayo 2026): Este script usa MongoDB que ha sido reemplazado por SQL Server.` |
| `backend/tests/test_e2e_flujo_completo.py` | 7 | `Las referencias a self.db.* y conexiones directas a MongoDB ya no funcionan en producción.` |
| `backend/tests/test_e2e_flujo_completo.py` | 30 | `# Importar PyMongo` |
| `backend/tests/test_e2e_flujo_completo.py` | 31 | `from pymongo import MongoClient` |
| `backend/tests/test_e2e_flujo_completo.py` | 79 | `self.mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/tests/test_e2e_flujo_completo.py` | 95 | `"""Conecta a MongoDB."""` |
| `backend/tests/test_e2e_flujo_completo.py` | 96 | `print_info(f"Conectando a MongoDB: {self.mongo_url[:30]}...")` |
| `backend/tests/test_e2e_flujo_completo.py` | 97 | `self.client = MongoClient(self.mongo_url)` |
| `backend/tests/test_e2e_flujo_completo.py` | 102 | `"""Desconecta de MongoDB."""` |
| `backend/tests/test_comercial_adapters.py` | 300 | `def test_busca_en_mongodb_primero(self):` |
| `backend/tests/test_comercial_adapters.py` | 301 | `"""Test: Intenta buscar en MongoDB antes de hardcoded"""` |
| `backend/tests/test_comercial_adapters.py` | 309 | `# Mock MongoDB sin APIs - pymongo.MongoClient` |
| `backend/tests/test_comercial_adapters.py` | 310 | `with patch("pymongo.MongoClient") as mock_mongo:` |
| `backend/tests/test_comercial_adapters.py` | 314 | `mock_db.servers.find.return_value = []  # Sin APIs en MongoDB` |
| `backend/tests/test_comercial_adapters.py` | 338 | `# Mock MongoDB con API que matchea` |
| `backend/tests/test_comercial_adapters.py` | 352 | `with patch("pymongo.MongoClient") as mock_mongo:` |
| `backend/tests/test_comercial_adapters.py` | 375 | `"""Test: Fallback a configuración hardcodeada si no hay MongoDB"""` |
| `backend/tests/test_comercial_adapters.py` | 382 | `# Simular error de MongoDB` |
| `backend/tests/test_comercial_adapters.py` | 383 | `with patch("pymongo.MongoClient", side_effect=Exception("DB Error")):` |
| `backend/tests/test_comercial_adapters.py` | 427 | `with patch("pymongo.MongoClient") as mock_mongo:` |
| `backend/tests/conftest.py` | 11 | `- Base para mocks de MongoDB, SQL, Auth y APIs externas` |
| `backend/tests/conftest.py` | 36 | `os.environ.setdefault("MONGO_URL", "<REDACTED_MONGO_URL>")` |
| `backend/tests/conftest.py` | 182 | `# FIXTURES: MOCKS BASE PARA MONGODB` |
| `backend/tests/conftest.py` | 188 | `Mock básico de la base de datos MongoDB.` |
| `backend/tests/conftest.py` | 208 | `"""Mock de una colección MongoDB individual"""` |
| `backend/tests/test_repositories.py` | 15 | `"""Tests de acceso a MongoDB con mocks"""` |
| `backend/tests/test_repositories.py` | 19 | `"""Test: Mock de MongoDB tiene estructura correcta"""` |
| `backend/tests/test_bloque2_paridad.py` | 23 | `from pymongo import MongoClient` |
| `backend/tests/test_bloque2_paridad.py` | 37 | `"""Obtiene conexión a MongoDB."""` |
| `backend/tests/test_bloque2_paridad.py` | 38 | `client = MongoClient(os.environ.get('MONGO_URL'))` |
| `backend/tests/test_bloque2_paridad.py` | 42 | `"""Obtiene un servidor SoftRestaurant de prueba desde MongoDB."""` |
| `backend/tests/test_bloque3_paridad_mpro.py` | 28 | `from pymongo import MongoClient` |
| `backend/tests/test_bloque3_paridad_mpro.py` | 42 | `"""Obtiene conexión a MongoDB."""` |
| `backend/tests/test_bloque3_paridad_mpro.py` | 43 | `client = MongoClient(os.environ.get('MONGO_URL'))` |
| `backend/tests/test_bloque3_paridad_mpro.py` | 47 | `"""Obtiene un servidor MPRO de prueba desde MongoDB."""` |
| `backend/tests/test_comparativo_inventarios.py` | 3 | `Tests the cache storage in MongoDB and Excel export endpoint.` |
| `backend/tests/test_comparativo_inventarios.py` | 6 | `1. /api/reports/inventory-analysis - saves correctly to MongoDB cache (inventario_diferencias_detalle)` |
| `backend/tests/test_comparativo_inventarios.py` | 120 | `"""Test that MongoDB cache has 4 documents for the test folios"""` |
| `backend/tests/test_recipients_manager.py` | 2 | `Test Suite: Centro de Control - Recipients Manager (MongoDB)` |
| `backend/tests/test_recipients_manager.py` | 4 | `Tests for CRUD operations on alert recipients stored in MongoDB.` |
| `backend/tests/test_recipients_manager.py` | 12 | `- Verify email_notifications.py reads from MongoDB` |
| `backend/tests/test_recipients_manager.py` | 13 | `- Verify whatsapp_notifications.py reads from MongoDB` |
| `backend/tests/test_recipients_manager.py` | 24 | `"""CRUD operations for alert recipients in MongoDB"""` |
| `backend/tests/test_recipients_manager.py` | 348 | `class TestNotificationServicesReadFromMongoDB:` |
| `backend/tests/test_recipients_manager.py` | 349 | `"""Verify email and whatsapp services read recipients from MongoDB"""` |
| `backend/tests/test_recipients_manager.py` | 361 | `def test_email_config_shows_mongodb_recipients(self):` |
| `backend/tests/test_recipients_manager.py` | 362 | `"""GET /email/config should show recipients from MongoDB"""` |
| `backend/tests/test_recipients_manager.py` | 374 | `print(f"✓ Email config shows {data['config']['recipients_count']} recipients from MongoDB")` |
| `backend/tests/test_recipients_manager.py` | 376 | `def test_whatsapp_config_shows_mongodb_recipients(self):` |
| `backend/tests/test_recipients_manager.py` | 377 | `"""GET /whatsapp/config should show recipients from MongoDB"""` |
| `backend/tests/test_recipients_manager.py` | 389 | `print(f"✓ WhatsApp config shows {data['config']['recipients_count']} recipients from MongoDB")` |
| `backend/tests/test_recipients_manager.py` | 404 | `# Email should be configured with MongoDB recipients` |
| `backend/tests/test_recipients_manager.py` | 409 | `# WhatsApp should be configured with MongoDB recipients` |
| `backend/tests/test_recipients_manager.py` | 414 | `print("✓ All notification services configured with MongoDB recipients")` |
| `backend/tests/test_recipients_manager.py` | 418 | `"""Verify seeded recipients exist in MongoDB"""` |
| `backend/tests/test_macrofase2_kpis.py` | 33 | `from motor.motor_asyncio import AsyncIOMotorClient` |
| `backend/tests/test_macrofase2_kpis.py` | 35 | `mongo_url = os.environ.get('MONGO_URL', '<REDACTED_MONGO_URL>')` |
| `backend/tests/test_macrofase2_kpis.py` | 38 | `client = AsyncIOMotorClient(mongo_url)` |
| `backend/utils/migration_helpers.py` | 2 | `EDARSA HUB - Utilidades de Migración MongoDB → SQL Server` |
| `backend/utils/migration_helpers.py` | 4 | `Funciones helper para convertir código legacy MongoDB a SQL-First.` |
| `backend/utils/migration_helpers.py` | 15 | `# Colección MongoDB → Tabla SQL Server` |
| `backend/utils/migration_helpers.py` | 39 | `SYSTEM_PROMPT = """Eres un experto en migración de MongoDB a SQL Server para EDARSA HUB.` |
| `backend/utils/migration_helpers.py` | 44 | `- MongoDB PROHIBIDO: Todo código debe usar execute_hub_query()` |
| `backend/utils/migration_helpers.py` | 72 | `Convierte código MongoDB a SQL Server alineado al` |
| `backend/utils/migration_helpers.py` | 76 | `codigo_mongo: Código Python con operaciones MongoDB` |
| `backend/utils/migration_helpers.py` | 99 | `prompt = f"""Convierte este código MongoDB a SQL Server usando execute_hub_query():` |
| `backend/core/server_registry.py` | 9 | `2. MongoDB queda como fallback legacy temporal` |
| `backend/core/server_registry.py` | 10 | `3. Todo fallback debe quedar marcado con config_origin = "MONGODB_LEGACY"` |
| `backend/core/server_registry.py` | 363 | `# LECTURA DESDE MONGODB (FALLBACK LEGACY)` |
| `backend/core/server_registry.py` | 376 | `'config_origin': 'MONGODB_LEGACY',` |
| `backend/core/server_registry.py` | 377 | `'warnings': ['Servidor obtenido desde MongoDB legacy; migrar a EDARSAHUB SQL.']` |
| `backend/core/server_registry.py` | 393 | `Obtiene servidores desde MongoDB (fallback legacy).` |
| `backend/core/server_registry.py` | 420 | `logger.warning(f"[SERVER_REGISTRY][MONGODB_FALLBACK_USED] Obtenidos {len(normalized)} servidores desde MongoDB legacy")` |
| `backend/core/server_registry.py` | 430 | `Obtiene un servidor específico por ID desde MongoDB (fallback legacy).` |
| `backend/core/server_registry.py` | 439 | `logger.warning(f"[SERVER_REGISTRY][MONGODB_FALLBACK_USED] Servidor {server_id} obtenido desde MongoDB legacy")` |
| `backend/core/server_registry.py` | 799 | `source = 'MONGODB_LEGACY'` |
| `backend/core/server_registry.py` | 834 | `source: Fuente del registro ("EDARSAHUB_SQL" o "MONGODB_LEGACY")` |
| `backend/core/server_registry.py` | 1033 | `FASE 3B.1: SQL-first con sync a MongoDB como espejo legacy.` |
| `backend/core/server_registry.py` | 1182 | `FASE 3B.1: SQL-first con sync a MongoDB como espejo legacy.` |
| `backend/core/server_registry.py` | 1376 | `FASE 3B.1: SQL-first con sync a MongoDB como espejo legacy.` |
| `backend/core/server_registry.py` | 1550 | `Construye un documento MongoDB legacy a partir de un registro SQL.` |
| `backend/core/server_registry.py` | 1553 | `compatibilidad con el esquema legacy de MongoDB.` |
| `backend/core/cache_key_builder.py` | 174 | `server_id: ID del servidor (SQL id o mongodb_id)` |
| `backend/core/scheduler/jobs/sync_propinas_tpv_job.py` | 55 | `db: Conexión MongoDB (para locks/logs legacy, no para datos financieros)` |
| `backend/core/scheduler/jobs/sync_ingresos_job.py` | 43 | `db: Conexión MongoDB (para locks/logs legacy, no para datos financieros)` |

## Regla de cierre

- MongoDB no debe ser fuente de verdad productiva.
- Endpoints visuales no deben depender de MongoDB.
- Usos permitidos temporalmente solo si están documentados como migración, backup, cache no autoritativo o pruebas.
- Todo hallazgo RIESGO_ALTO debe migrarse a EDARSAHUB SQL o eliminarse.
