# Auditoría STRICT runtime Mongo backend
Fecha: 20260623_014010

## 1. Runtime real db.<coleccion> en código productivo
```
backend/server.py:2139:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}))
backend/server.py:2167:            await db.server_status.update_one(
backend/server.py:2194:        await db.server_status.update_one(
backend/server.py:2252:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:2350:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:2365:    # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {field_name: query_config}})
backend/server.py:2378:    # ANTES: updated_server = decrypt_server_secrets(await db.servers.find_one({"id": server_id}, {"_id": 0}))
backend/server.py:2387:        # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {"queries_configured": all_configured}})
backend/server.py:2418:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:2480:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:2487:    # ANTES: await db.servers.update_one({"id": server_id}, {"$set": {field_name: None, "queries_configured": False}})
backend/server.py:3081:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:3204:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:3317:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:3354:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:3497:    # ANTES: server_cursor = db.servers.find({"id": {"$in": server_ids}}, {"_id": 0, "id": 1, "name": 1})
backend/server.py:3693:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:3767:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:3893:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:4297:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:4874:                        await db.inventario_diferencias_detalle.update_one(
backend/server.py:5522:                        await db.inventario_diferencias_detalle.update_one(
backend/server.py:5603:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:5858:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:6155:            cached = await db.inventario_diferencias_detalle.find_one(cache_key, {"_id": 0})
backend/server.py:6430:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
backend/server.py:6612:    await db.alerts.insert_one(doc)
backend/server.py:6618:    alerts = await db.alerts.find({"active": True}, {"_id": 0}).to_list(1000)
backend/server.py:6623:    await db.alerts.update_one({"id": alert_id}, {"$set": alert_data})
backend/server.py:6628:    await db.alerts.update_one({"id": alert_id}, {"$set": {"active": False}})
backend/server.py:6699:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:6776:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:6924:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0}))
backend/server.py:7254:        # ANTES: server = decrypt_server_secrets(await db.servers.find_one(query))
backend/server.py:7472:    # ANTES: servers = await db.servers.find({"active": True, "queries_configured": True}, {...}).to_list(100)
backend/server.py:7502:    # ANTES: total_servers = await db.servers.count_documents({"active": True})
backend/server.py:7503:    # ANTES: servers_configured = await db.servers.count_documents({"active": True, "queries_configured": True})
backend/server.py:7509:    total_users = await db.users.count_documents({"active": True})
backend/server.py:7510:    total_alerts = await db.alerts.count_documents({"active": True})
backend/server.py:7628:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:9113:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": request.server_id, "active": True}))
backend/server.py:11979:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:12156:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:12216:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:12361:    await db.script_logs.insert_one({
backend/server.py:13265:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:13403:    await db.script_logs.insert_one({
backend/server.py:13906:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:14089:    # consultas_custom = await db.consultas_custom.find(filtro).to_list(500)
backend/server.py:14153:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
backend/server.py:14391:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))
backend/server.py:14449:    # ANTES: server = decrypt_server_secrets(await db.servers.find_one({"id": target_server_id, "active": True}))
backend/server.py:14524:        solicitudes = await db.solicitudes_catalogos.find(
backend/server.py:14553:        proveedores = await db.portal_proveedores.find(
backend/server.py:14601:        ciclos = await db.nomina_ciclos.find(
backend/server.py:14607:        config = await db.nomina_configuracion.find_one({}, {"_id": 0})
backend/server.py:14687:    await db.tareas_sistema.update_one(
backend/server.py:14764:    await db.nomina_ciclos.update_one(
backend/server.py:14805:    cursor = db.nomina_ciclos.find(filtro).sort("fecha_creacion", -1)
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
backend/server.py:15399:            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
backend/server.py:15406:        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
backend/api/sync_receiver.py:187:    server = await db.sql_servers.find_one({"id": payload.server_id})
backend/api/sync_receiver.py:232:    await db.sync_agent_registry.update_one(
backend/api/sync_receiver.py:276:    server = await db.sql_servers.find_one({"id": request.server_id})
backend/api/sync_receiver.py:286:    await db.sync_agent_registry.update_one(
backend/core/auditoria.py:401:            await db.auditoria_financiera.insert_one(evento.to_mongo_doc())
backend/core/scheduler/jobs/notifications_job.py:121:        count = await self.db.notification_queue.count_documents({
backend/core/communications/dispatcher/dispatcher.py:110:            providers = await self.db.notification_provider_config.find(
backend/core/communications/notifications/service.py:251:        user = await self.db.users.find_one(
backend/core/communications/audit/audit_service.py:182:        cursor = self.db.notification_log.aggregate(pipeline)
backend/core/communications/scripts/__init__.py:330:        existing = await db.notification_config.find_one({"id": config["id"]})
backend/core/communications/scripts/__init__.py:333:            await db.notification_config.insert_one(config)
backend/core/communications/scripts/__init__.py:339:    existing = await db.notification_provider_config.find_one({"id": DEFAULT_PROVIDER_CONFIG["id"]})
backend/core/communications/scripts/__init__.py:342:        await db.notification_provider_config.insert_one(DEFAULT_PROVIDER_CONFIG)
backend/core/communications/scripts/__init__.py:349:        existing = await db.notification_templates.find_one({"id": template["id"]})
backend/core/communications/scripts/__init__.py:352:            await db.notification_templates.insert_one(template)
backend/core/communications/routes.py:164:    config = await db.notification_config.find_one({"id": config_id}, {"_id": 0})
backend/core/communications/routes.py:497:    providers = await db.notification_provider_config.find(
backend/core/communications/routes.py:512:    provider = await db.notification_provider_config.find_one(
backend/core/communications/routes.py:671:    result = await db.notification_provider_config.update_one(
backend/core/communications/routes.py:713:    result = await db.notification_config.update_one(
backend/core/communications/routes.py:728:    config = await db.notification_config.find_one({"id": config_id}, {"_id": 0})
backend/modules/comercial/cache_service.py:139:        cached = await db.comercial_cache.find_one({"cache_key": cache_key})
backend/modules/comercial/cache_service.py:207:        await db.comercial_cache.update_one(
backend/modules/comercial/cache_service.py:373:        total_before = await db.comercial_cache.count_documents({})
backend/modules/comercial/cache_service.py:386:        total_after = await db.comercial_cache.count_documents({})
backend/modules/comercial/cache_service.py:421:        total_entries = await db.comercial_cache.count_documents({})
backend/modules/comercial/cache_service.py:433:        oldest = await db.comercial_cache.find_one(sort=[("cached_at", 1)])
backend/modules/comercial/cache_service.py:434:        newest = await db.comercial_cache.find_one(sort=[("cached_at", -1)])
backend/modules/sistema/estructura_service.py:54:            empresas = await self.db.sec_empresas.find(
backend/modules/sistema/estructura_service.py:70:                unidades = await self.db.sec_unidades_negocio.find(
backend/modules/sistema/estructura_service.py:86:                    sucursales = await self.db.sec_sucursales.find(
backend/modules/sistema/estructura_service.py:124:            mapeos = await self.db.sec_mapeo_servidor_sucursal.find(
backend/modules/sistema/estructura_service.py:161:            permisos = await self.db.sec_permisos_catalogo.find(
backend/modules/sistema/estructura_service.py:220:            await self.db.sec_bitacora_acceso.insert_one(entry)
backend/modules/rh/routes.py:140:    empresas = await db.empresas.find(
backend/modules/configuracion/services/almacenes_sync_service.py:141:        # ANTES: server = await db.servers.find_one({"id": server_id}, {"_id": 0})
backend/modules/finanzas/tesoreria.py:61:    empresas = await db.empresas.find(
backend/modules/finanzas/cuentas_por_pagar.py:72:    empresas = await db.empresas.find(
backend/modules/finanzas/propinas_tpv/routes_edarsahub.py:79:        empresas = await db.empresas.find(
backend/modules/finanzas/propinas_tpv/routes.py:142:    empresas = await db.empresas.find(
backend/modules/manuales_operativos/triggers.py:80:    proceso = await db.automatizaciones_operativas_compras.find_one({"id": proceso_id})
backend/modules/manuales_operativos/triggers.py:92:    bitacora = await db.automatizaciones_bitacora.find(
backend/modules/manuales_operativos/triggers.py:107:        users_cursor = db.users.find({"id": {"$in": list(user_ids)}}, {"id": 1, "email": 1, "full_name": 1})
backend/modules/manuales_operativos/triggers.py:137:    cursor = db.automatizaciones_operativas_compras.find({
```

## 2. Imports/conectores Mongo reales
```
backend/core/sql_first/no_mongo.py:22:MongoClient = mongo_disabled
backend/core/sql_first/no_mongo.py:23:AsyncIOMotorClient = mongo_disabled
backend/core/auth/user_repository_sql.py:351:    pass  # P2-07: MongoDB eliminado (AsyncIOMotorClient)
backend/core/auth/user_repository_sql.py:358:    mongo_url = None  # P2-07: MongoDB eliminado
backend/core/rbac/routes.py:49:    mongo_url = None  # P2-07: MongoDB eliminado
backend/modules/fase2_operativo/db_utils.py:27:        mongo_url = None  # P2-07: MongoDB eliminado
```

## 3. Foco nómina / seguridad / notificaciones / sync_receiver
```
backend/server.py:14601:        ciclos = await db.nomina_ciclos.find(
backend/server.py:14607:        config = await db.nomina_configuracion.find_one({}, {"_id": 0})
backend/server.py:14764:    await db.nomina_ciclos.update_one(
backend/server.py:14805:    cursor = db.nomina_ciclos.find(filtro).sort("fecha_creacion", -1)
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
backend/server.py:15367:# FASE 6: + Múltiples roles (sec_roles array)
backend/server.py:15386:    2. Múltiples roles (sec_roles array) → FASE 6
backend/server.py:15396:    sec_roles = user.get('sec_roles', [])
backend/server.py:15397:    for rol_codigo in sec_roles:
backend/server.py:15399:            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
backend/server.py:15406:        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
backend/server.py:15570:    """RBAC piloto SQL-First: asigna/retira un rol (sec_roles)."""
backend/server.py:15635:# - sec_roles sigue siendo la fuente de verdad operativa
backend/server.py:15637:# - Asignar perfil = reemplazar sec_roles con los roles del perfil
backend/server.py:15669:    """RBAC piloto SQL-First: asigna un perfil (sobrescribe sec_roles con los del perfil)."""
backend/server.py:15688:    """RBAC piloto SQL-First: retira el perfil de un usuario (limpia sec_perfil y sec_roles)."""
backend/api/sync_receiver.py:187:    server = await db.sql_servers.find_one({"id": payload.server_id})
backend/api/sync_receiver.py:232:    await db.sync_agent_registry.update_one(
backend/api/sync_receiver.py:276:    server = await db.sql_servers.find_one({"id": request.server_id})
backend/api/sync_receiver.py:286:    await db.sync_agent_registry.update_one(
backend/api/sync_receiver.py:318:    """Crea índices para sync_agent_registry."""
backend/api/sync_receiver.py:319:    coll = db.sync_agent_registry
backend/core/auditoria.py:401:            await db.auditoria_financiera.insert_one(evento.to_mongo_doc())
backend/core/scheduler/jobs/notifications_job.py:121:        count = await self.db.notification_queue.count_documents({
backend/core/scheduler/jobs/cava_socios_monthly_job.py:29:    from modules.cava_socios.notification_service import get_notification_service
backend/core/scheduler/jobs/cava_socios_monthly_job.py:35:    notification_service = get_notification_service()
backend/core/scheduler/jobs/cava_socios_monthly_job.py:80:                    resultado = notification_service.enviar_reporte_email(
backend/core/communications/dispatcher/dispatcher.py:110:            providers = await self.db.notification_provider_config.find(
backend/core/communications/dispatcher/dispatcher.py:414:        """Registra el resultado en notification_log."""
backend/core/communications/notifications/service.py:251:        user = await self.db.users.find_one(
backend/core/communications/notifications/service.py:450:def get_notification_orchestrator(db) -> NotificationOrchestratorService:
backend/core/communications/notifications/service.py:458:def reset_notification_orchestrator():
backend/core/communications/notifications/__init__.py:18:from .service import NotificationOrchestratorService, get_notification_orchestrator
backend/core/communications/notifications/__init__.py:19:from .repository import NotificationRepository, get_notification_repository
backend/core/communications/notifications/__init__.py:34:    'get_notification_orchestrator',
backend/core/communications/notifications/__init__.py:36:    'get_notification_repository',
backend/core/communications/notifications/dedup.py:37:        self.log_collection = db.notification_log
backend/core/communications/notifications/repository.py:9:- notification_config
backend/core/communications/notifications/repository.py:10:- notification_provider_config
backend/core/communications/notifications/repository.py:11:- notification_templates
backend/core/communications/notifications/repository.py:12:- notification_queue
backend/core/communications/notifications/repository.py:13:- notification_log
backend/core/communications/notifications/repository.py:39:        self.config_collection = db.notification_config
backend/core/communications/notifications/repository.py:40:        self.provider_collection = db.notification_provider_config
backend/core/communications/notifications/repository.py:41:        self.template_collection = db.notification_templates
backend/core/communications/notifications/repository.py:42:        self.queue_collection = db.notification_queue
backend/core/communications/notifications/repository.py:43:        self.log_collection = db.notification_log
backend/core/communications/notifications/repository.py:424:def get_notification_repository(db) -> NotificationRepository:
backend/core/communications/notifications/repository.py:432:def reset_notification_repository():
backend/core/communications/notifications/schemas.py:9:- notification_config
backend/core/communications/notifications/schemas.py:10:- notification_provider_config
backend/core/communications/notifications/schemas.py:11:- notification_templates
backend/core/communications/notifications/schemas.py:12:- notification_queue
backend/core/communications/notifications/schemas.py:13:- notification_log
backend/core/communications/notifications/schemas.py:93:    Colección: notification_config
backend/core/communications/notifications/schemas.py:131:    Colección: notification_provider_config
backend/core/communications/notifications/schemas.py:160:    Colección: notification_templates
backend/core/communications/notifications/schemas.py:191:    Colección: notification_queue
backend/core/communications/notifications/schemas.py:234:    Colección: notification_log
backend/core/communications/__init__.py:31:from .notifications.service import NotificationOrchestratorService, get_notification_orchestrator
backend/core/communications/__init__.py:52:    'get_notification_orchestrator',
backend/core/communications/templates/template_service.py:97:        self.template_collection = db.notification_templates
backend/core/communications/audit/audit_service.py:182:        cursor = self.db.notification_log.aggregate(pipeline)
backend/core/communications/audit/audit_service.py:237:    async def get_notification_history(
backend/core/communications/scripts/__init__.py:11:- notification_config
backend/core/communications/scripts/__init__.py:12:- notification_provider_config
backend/core/communications/scripts/__init__.py:13:- notification_templates
backend/core/communications/scripts/__init__.py:14:- notification_queue
backend/core/communications/scripts/__init__.py:15:- notification_log
backend/core/communications/scripts/__init__.py:34:    "notification_config": [
backend/core/communications/scripts/__init__.py:41:    "notification_provider_config": [
backend/core/communications/scripts/__init__.py:52:    "notification_templates": [
backend/core/communications/scripts/__init__.py:64:    "notification_queue": [
backend/core/communications/scripts/__init__.py:83:    "notification_log": [
backend/core/communications/scripts/__init__.py:330:        existing = await db.notification_config.find_one({"id": config["id"]})
backend/core/communications/scripts/__init__.py:333:            await db.notification_config.insert_one(config)
backend/core/communications/scripts/__init__.py:339:    existing = await db.notification_provider_config.find_one({"id": DEFAULT_PROVIDER_CONFIG["id"]})
backend/core/communications/scripts/__init__.py:342:        await db.notification_provider_config.insert_one(DEFAULT_PROVIDER_CONFIG)
backend/core/communications/scripts/__init__.py:349:        existing = await db.notification_templates.find_one({"id": template["id"]})
backend/core/communications/scripts/__init__.py:352:            await db.notification_templates.insert_one(template)
backend/core/communications/scripts/__init__.py:358:async def init_notification_system(db):
backend/core/communications/routes.py:164:    config = await db.notification_config.find_one({"id": config_id}, {"_id": 0})
backend/core/communications/routes.py:324:async def get_notification_logs(
backend/core/communications/routes.py:357:async def get_notification_stats(
backend/core/communications/routes.py:467:async def initialize_notification_system(
backend/core/communications/routes.py:476:    from core.communications.scripts import init_notification_system
backend/core/communications/routes.py:478:    await init_notification_system(db)
backend/core/communications/routes.py:497:    providers = await db.notification_provider_config.find(
backend/core/communications/routes.py:512:    provider = await db.notification_provider_config.find_one(
backend/core/communications/routes.py:671:    result = await db.notification_provider_config.update_one(
backend/core/communications/routes.py:713:    result = await db.notification_config.update_one(
backend/core/communications/routes.py:728:    config = await db.notification_config.find_one({"id": config_id}, {"_id": 0})
backend/core/user_access_context.py:35:- Combina modelo RBAC (empresas_permitidas, sec_roles) con legacy (allowed_servers)
backend/core/user_access_context.py:112:    # Permisos funcionales (combinados de sec_roles y sec_permisos)
backend/core/user_access_context.py:116:    sec_roles: List[str] = field(default_factory=list)
backend/core/user_access_context.py:144:            "sec_roles": self.sec_roles,
backend/core/user_access_context.py:439:    # (Los sec_roles y sec_permisos vienen del usuario ya resuelto)
backend/core/user_access_context.py:441:    sec_roles = user.get('sec_roles') or []
backend/core/user_access_context.py:444:    context.sec_roles = sec_roles
backend/core/centro_control/websocket.py:218:notification_manager = NotificationManager()
backend/core/centro_control/websocket.py:221:def get_notification_manager() -> NotificationManager:
backend/core/centro_control/websocket.py:223:    return notification_manager
backend/core/centro_control/routes.py:68:from core.centro_control.websocket import get_notification_manager, NotificationManager
backend/core/centro_control/routes.py:368:        manager = get_notification_manager()
backend/core/centro_control/routes.py:1351:    manager = get_notification_manager()
backend/core/centro_control/routes.py:1382:    manager = get_notification_manager()
backend/core/centro_control/routes.py:1395:    manager = get_notification_manager()
backend/core/centro_control/routes.py:1409:    manager = get_notification_manager()
backend/core/centro_control/routes.py:1587:    manager = get_notification_manager()
backend/core/cerebro.py:677:    "nomina_ciclos": NominaCiclo,
backend/core/cerebro.py:678:    "nomina_movimientos": NominaMovimiento,
backend/core/cerebro.py:679:    "nomina_configuracion": NominaConfiguracion,
backend/core/cerebro.py:680:    "nomina_kpis_puestos": NominaKPIsPuesto,
backend/core/rbac_helper_sql.py:164:    - sec_roles (array de códigos)
backend/core/rbac_helper_sql.py:188:    # 3. Verificar por array de roles (sec_roles)
backend/core/rbac_helper_sql.py:189:    sec_roles = user.get('sec_roles', [])
backend/core/rbac_helper_sql.py:190:    for rol in sec_roles:
backend/core/auth/user_repository_sql.py:363:    user_mongo = await mongo_db.users.find_one({'email': email}, {'_id': 0})
backend/core/health_checker.py:159:    def _check_sql_servers(self) -> List[SourceHealth]:
backend/core/health_checker.py:200:        sql_healths = self._check_sql_servers()
backend/core/alcance_helper.py:24:2. sec_roles_alcance con tipo GLOBAL → acceso global
backend/core/alcance_helper.py:25:3. sec_roles_alcance con tipo específico → empresas calculadas (UNIÓN de todos los roles)
backend/core/alcance_helper.py:26:4. Sin sec_roles_alcance → fallback a empresas_permitidas del usuario
backend/core/alcance_helper.py:190:    # PASO 2: Verificar sec_roles_alcance
backend/core/alcance_helper.py:191:    sec_roles_alcance = current_user.get('sec_roles_alcance', {})
backend/core/alcance_helper.py:193:    if sec_roles_alcance:
backend/core/alcance_helper.py:196:        for rol_codigo, alcance_data in sec_roles_alcance.items():
backend/modules/fase2_operativo/services/cargos_service.py:780:            from .notification_service import get_notification_service
backend/modules/fase2_operativo/services/cargos_service.py:782:            notification_service = get_notification_service(self.db)
backend/modules/fase2_operativo/services/cargos_service.py:799:            await notification_service.notificar_cargo_aplicado(
backend/modules/fase2_operativo/services/__init__.py:64:from .notification_service import (
backend/modules/fase2_operativo/services/__init__.py:66:    get_notification_service,
backend/modules/fase2_operativo/services/__init__.py:134:    "get_notification_service",
backend/modules/fase2_operativo/services/orquestador_service.py:369:            from .notification_service import get_notification_service
backend/modules/fase2_operativo/services/orquestador_service.py:371:            # El notification_service puede seguir usando db legacy por ahora
backend/modules/fase2_operativo/services/orquestador_service.py:372:            notification_service = get_notification_service(self._db_legacy)
backend/modules/fase2_operativo/services/orquestador_service.py:377:                await notification_service.notificar_workflow_creado(
backend/modules/fase2_operativo/services/orquestador_service.py:388:                    await notification_service.notificar_tarea_asignada(
backend/modules/fase2_operativo/services/notification_service.py:690:def get_notification_service(db) -> NotificationService:
backend/modules/fase2_operativo/services/sla_service.py:90:        self._notification_service = None
backend/modules/fase2_operativo/services/sla_service.py:93:    def _get_notification_service(self):
backend/modules/fase2_operativo/services/sla_service.py:98:        if self._notification_service is None:
backend/modules/fase2_operativo/services/sla_service.py:100:                from core.communications.notifications.service import get_notification_orchestrator
backend/modules/fase2_operativo/services/sla_service.py:101:                self._notification_service = get_notification_orchestrator(self._db_legacy)
backend/modules/fase2_operativo/services/sla_service.py:104:                self._notification_service = None
backend/modules/fase2_operativo/services/sla_service.py:105:        return self._notification_service
backend/modules/fase2_operativo/services/sla_service.py:535:        notifier = self._get_notification_service()
backend/modules/fase2_operativo/services/sla_service.py:582:        notifier = self._get_notification_service()
backend/modules/fase2_operativo/services/sla_service.py:625:        notifier = self._get_notification_service()
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:456:    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:494:    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:529:    user = db.users.find_one({"id": payload.get("user_id")}, {"_id": 0, "role": 1})
backend/modules/fase2_operativo/routes/notificaciones_routes.py:14:from ..services.notification_service import get_notification_service
backend/modules/fase2_operativo/routes/notificaciones_routes.py:26:async def get_notification_status(
backend/modules/fase2_operativo/routes/notificaciones_routes.py:45:async def get_notification_log(
backend/modules/fase2_operativo/routes/notificaciones_routes.py:122:    notification_service = get_notification_service(db)
backend/modules/fase2_operativo/routes/notificaciones_routes.py:184:        usuario = db.users.find_one({"id": usuario_id}, {"_id": 0, "email": 1, "name": 1})
backend/modules/fase2_operativo/routes/notificaciones_routes.py:189:        resultado = await notification_service.notificar_tarea_vencida(
backend/modules/auth/service.py:213:    1. Si tiene permiso RBAC (sec_permisos/sec_roles/sec_rol/SuperAdmin) → ACCESO
backend/modules/auth/service.py:219:    2. sec_roles_alcance con GLOBAL → ve todos
backend/modules/auth/service.py:220:    3. sec_roles_alcance con tipo específico → filtra por empresas del alcance
backend/modules/auth/service.py:221:    4. Sin sec_roles_alcance → fallback a empresas_permitidas
backend/modules/auth/service.py:540:    1. Si tiene permiso RBAC (sec_permisos/sec_roles/sec_rol/SuperAdmin) → ACCESO
backend/modules/auth/service.py:625:    1. Si tiene permiso RBAC (sec_permisos/sec_roles/sec_rol/SuperAdmin) → ACCESO
backend/modules/auth/service.py:657:    1. Si tiene permiso RBAC (sec_permisos/sec_roles/sec_rol/SuperAdmin) → ACCESO
backend/modules/auth/routes.py:507:    - sec_roles RBAC
backend/modules/auth/routes.py:610:        'sec_roles': context.sec_roles,
backend/modules/auth/schemas.py:46:    sec_roles: List[str] = []  # FASE 6: Múltiples roles
backend/modules/auth/schemas.py:49:    sec_roles_alcance: Dict[str, Dict] = {}  # rol_codigo -> {tipo, empresa_id, unidades_ids, sucursales_ids, almacenes_ids}
backend/modules/crm/trigger_service.py:67:        self._notification_service = None
backend/modules/crm/trigger_service.py:82:    def notification_service(self):
backend/modules/crm/trigger_service.py:84:        if self._notification_service is None:
backend/modules/crm/trigger_service.py:86:                from modules.cava_socios.notification_service import get_notification_service
backend/modules/crm/trigger_service.py:87:                self._notification_service = get_notification_service()
backend/modules/crm/trigger_service.py:90:        return self._notification_service
backend/modules/crm/trigger_service.py:324:        if not self.notification_service:
backend/modules/crm/trigger_service.py:335:        resultado = self.notification_service.enviar_email(
backend/modules/crm/trigger_service.py:347:        if not self.notification_service:
backend/modules/crm/trigger_service.py:356:        resultado = self.notification_service.enviar_whatsapp(
backend/modules/admin_sql/rbac_pilot_service.py:4:Reemplaza la implementación legacy basada en MongoDB (`db.sec_perfiles`, `db.sec_roles`,
backend/modules/admin_sql/rbac_pilot_service.py:11:  - Asignar perfil = setea sec_perfil + sobrescribe sec_roles con los roles del perfil.
backend/modules/admin_sql/rbac_pilot_service.py:12:  - Retirar perfil = limpia sec_perfil y sec_roles.
backend/modules/admin_sql/rbac_pilot_service.py:92:    """Devuelve {usuario_id_str: {sec_perfil, sec_roles[], sec_permisos[]}}."""
backend/modules/admin_sql/rbac_pilot_service.py:100:            entry = out.setdefault(uid, {"sec_perfil": None, "sec_roles": [], "sec_permisos": []})
backend/modules/admin_sql/rbac_pilot_service.py:104:                entry["sec_roles"].append(codigo)
backend/modules/admin_sql/routes.py:187:        u["sec_roles"] = rbac.get("sec_roles", [])
backend/modules/cava_socios/notification_service.py:400:_notification_service = None
backend/modules/cava_socios/notification_service.py:402:def get_notification_service() -> NotificationService:
backend/modules/cava_socios/notification_service.py:404:    global _notification_service
backend/modules/cava_socios/notification_service.py:405:    if _notification_service is None:
backend/modules/cava_socios/notification_service.py:406:        _notification_service = NotificationService()
backend/modules/cava_socios/notification_service.py:407:    return _notification_service
backend/modules/cava_socios/routes.py:341:from .notification_service import get_notification_service
backend/modules/cava_socios/routes.py:406:        notification_service = get_notification_service()
backend/modules/cava_socios/routes.py:407:        resultado = notification_service.enviar_reporte_multicanal(
backend/modules/cava_socios/routes.py:446:        notification_service = get_notification_service()
backend/modules/cava_socios/routes.py:456:        resultados["reportes"]["ficha"] = notification_service.enviar_reporte_multicanal(
backend/modules/cava_socios/routes.py:463:        resultados["reportes"]["consumos"] = notification_service.enviar_reporte_multicanal(
backend/modules/cava_socios/routes.py:470:        resultados["reportes"]["estado_cuenta"] = notification_service.enviar_reporte_multicanal(
```

## 4. Graphify estado
```
48M	graphify-out
archivos graphify-out: 1433
Sin cambios pendientes Graphify
```

## 5. Compilación base
```
COMPILE_OK
```
