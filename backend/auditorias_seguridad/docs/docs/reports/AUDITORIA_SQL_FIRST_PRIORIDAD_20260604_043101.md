# AUDITORÍA SQL-FIRST - PRIORIDAD DE MIGRACIÓN
Fecha: Thu Jun  4 04:31:01 UTC 2026

## 1. Endpoints críticos Compras / Inventarios / Movimientos
```text
/app/backend/init_queries.py:87:    "movimientos": """DECLARE @SUCURSAL VARCHAR(50)
/app/backend/init_queries.py:225:    "inventarios": """DECLARE @SUCURSAL VARCHAR(20)
/app/backend/modules/comercial/service.py:1676:    Query para MPRO que devuelve KPIs DIVIDIDOS POR SUCURSAL (como en Inventarios).
/app/backend/modules/comercial/queries/mpro.py:14:- Requisicion_Compra: Requisiciones de compra
/app/backend/modules/comercial/queries/mpro.py:15:- Fisico: Inventarios físicos
/app/backend/modules/comercial/queries/softrestaurant.py:17:- invfisico: Inventarios físicos
/app/backend/modules/comercial/rentabilidad.py:9:    data consolidada de inventarios físicos y ventas en EDARSAHUB SQL.
/app/backend/modules/comercial/rentabilidad.py:35:        # Consultar el costo unitario consolidado en el historial de inventarios físicos síncronos
/app/backend/modules/comercial/rentabilidad.py:38:            FROM dbo.Compras_Inventarios_Fisicos_Sync
/app/backend/modules/comercial/repository.py:139:        'query_movimientos': parse_json_field(row.get('query_movimientos')),
/app/backend/modules/comercial/routes.py:32:- ✅ Endpoints /comercial/mesas y /comercial/detalle-movimientos migrados (Fase 5B-4E)
/app/backend/modules/comercial/routes.py:57:   - GET /comercial/detalle-movimientos/{server_id} (Fase 5B-4E)
/app/backend/modules/comercial/routes.py:187:# - /comercial/detalle-movimientos/{server_id} - Requiere: tabla de detalle
/app/backend/modules/comercial/routes.py:216:    '/comercial/detalle-movimientos': {
/app/backend/modules/comercial/routes.py:217:        'tabla_requerida': 'Sync_Movimientos_Detalle',
/app/backend/modules/comercial/routes.py:218:        'job_requerido': 'sync_movimientos',
/app/backend/modules/comercial/routes.py:3241:@router.get("/comercial/detalle-movimientos/{server_id}")
/app/backend/modules/comercial/routes.py:3242:async def comercial_detalle_movimientos(
/app/backend/modules/comercial/routes.py:3252:    Detalle de movimientos para drill-down en KPIs.
/app/backend/modules/comercial/routes.py:3255:    Este endpoint requiere conexión LIVE. Bloqueado hasta migrar a Sync_Movimientos_Detalle.
/app/backend/modules/comercial/routes.py:3265:    guard_result = check_live_guard_rail('/comercial/detalle-movimientos', server_id)
/app/backend/modules/comercial/routes.py:3368:            movimientos = []
/app/backend/modules/comercial/routes.py:3372:                movimientos.append({
/app/backend/modules/comercial/routes.py:3384:                "movimientos": movimientos,
/app/backend/modules/comercial/routes.py:3464:            movimientos = []
/app/backend/modules/comercial/routes.py:3468:                movimientos.append({
/app/backend/modules/comercial/routes.py:3480:                "movimientos": movimientos,
/app/backend/modules/comercial/routes.py:3489:        return {"movimientos": [], "total": 0, "page": 1, "limit": limit, "pages": 0}
/app/backend/modules/comercial/routes.py:3492:        logging.error(f"Error en detalle movimientos: {e}")
/app/backend/modules/hub/modulo_financiero_proyectos.py:82:            movimientos = cursor.fetchall()
/app/backend/modules/hub/modulo_financiero_proyectos.py:85:            for mov in movimientos:
/app/backend/modules/fase2_operativo/__init__.py:2:FASE 2A - Módulo Operativo de Automatización de Inventarios
/app/backend/modules/fase2_operativo/sql_repository.py:7:- Workflow_Inventarios
/app/backend/modules/fase2_operativo/sql_repository.py:10:- Inventarios_SinAsignar
/app/backend/modules/fase2_operativo/sql_repository.py:109:        FROM Workflow_Inventarios
/app/backend/modules/fase2_operativo/sql_repository.py:142:        INSERT INTO Workflow_Inventarios (
/app/backend/modules/fase2_operativo/sql_repository.py:173:        UPDATE Workflow_Inventarios
/app/backend/modules/fase2_operativo/sql_repository.py:205:        FROM Workflow_Inventarios
/app/backend/modules/fase2_operativo/sql_repository.py:356:                Movimientos, Ventas, RequiereJustificacionCompleta
/app/backend/modules/fase2_operativo/sql_repository.py:376:            float(prod.get("Movimientos", 0) or 0),
/app/backend/modules/fase2_operativo/sql_repository.py:392:# INVENTARIOS SIN ASIGNAR
/app/backend/modules/fase2_operativo/sql_repository.py:411:        INSERT INTO Inventarios_SinAsignar (
/app/backend/modules/fase2_operativo/router.py:37:        "description": "Módulo Operativo de Automatización de Inventarios"
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:2:Repositorio para workflow_inventarios
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:26:    Repository para la tabla Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:50:        super().__init__(db, "workflow_inventarios")
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:33:    Para filtrar por server_id se requiere JOIN con Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:150:        Para filtrar por server_ids se requiere JOIN con Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:172:                "Filtro RBAC debe aplicarse en service con JOIN a Workflow_Inventarios."
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:258:        NOTA: server_ids requiere JOIN con Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:331:        Obtiene tareas con filtro RBAC mediante JOIN a Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:355:            INNER JOIN Workflow_Inventarios w ON t.WorkflowID = w.WorkflowID
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:392:            INNER JOIN Workflow_Inventarios w ON t.WorkflowID = w.WorkflowID
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:29:    "workflow_inventarios": "Workflow_Inventarios",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:57:    "inventarios_fisicos_procesados": "Compras_Inventarios_Fisicos_Sync",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:62:    "Workflow_Inventarios": {
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:719:            "Workflow_Inventarios": "WorkflowID",
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:11:- NO toca automatizacion_inventarios_folios_procesados
/app/backend/modules/fase2_operativo/scripts/init_collections_fase2a.py:26:    "workflow_inventarios",
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
/app/backend/modules/fase2_operativo/schemas/workflow_schemas.py:2:Schemas Pydantic para Workflow de Inventarios
/app/backend/modules/fase2_operativo/schemas/enums.py:6:de trabajo de inventarios.
/app/backend/modules/fase2_operativo/services/document_data_service.py:75:            repo = SQLBaseRepository("workflow_inventarios")
/app/backend/modules/fase2_operativo/services/orquestador_service.py:41:    Servicio que orquesta la creación de workflows desde análisis de inventarios.
/app/backend/modules/fase2_operativo/services/orquestador_service.py:140:                    f"Configure un responsable en Configuración → Asignaciones de Inventarios."
/app/backend/modules/fase2_operativo/services/orquestador_service.py:143:                # Registrar en inventarios_sin_asignar (SQL)
/app/backend/modules/fase2_operativo/services/orquestador_service.py:166:                    modulo="inventarios",
/app/backend/modules/fase2_operativo/services/orquestador_service.py:174:                    accion_sugerida="Configurar responsable en Configuración → Asignaciones de Inventarios"
/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py:258:        workflow_repo = SQLBaseRepository("workflow_inventarios")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:87:        self._inv_repo = SQLBaseRepository("inventarios_fisicos_procesados")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:588:    # INVENTARIOS (SQL)
/app/backend/modules/fase2_operativo/services/workflow_service.py:2:Servicio de Workflow de Inventarios
/app/backend/modules/api_connections/universal_test_routes.py:25:- Módulos: Comercial, Tablero, KPIs, Inventarios, Compras, Finanzas, Operaciones
/app/backend/modules/corporate_filters/router.py:343:            ["Sync_Productos", "Comercial_Productos", "Inventarios_Productos", "Productos"],
/app/backend/modules/rh/service.py:394:                "nomipaq": "Mapeo con nom10001 (empleados), nom10003 (conceptos), nom10007 (movimientos)",
/app/backend/modules/configuracion/routes/config_asignaciones_routes.py:530:    Advertencia: Los inventarios futuros de esta combinación
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
/app/backend/modules/inventarios/repository.py:26:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:56:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:68:def get_inventarios_count_by_server(server_id: str) -> int:
/app/backend/modules/inventarios/repository.py:70:    Cuenta inventarios por servidor.
/app/backend/modules/inventarios/repository.py:74:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:81:class InventariosRepository:
/app/backend/modules/inventarios/repository.py:86:        return get_inventarios_fisicos(server_id=server_id, **filters)
/app/backend/modules/inventarios/repository.py:94:    'InventariosRepository',
/app/backend/modules/inventarios/repository.py:95:    'get_inventarios_fisicos',
/app/backend/modules/inventarios/repository.py:97:    'get_inventarios_count_by_server',
/app/backend/modules/inventarios/routes.py:2:EDARSA HUB - Inventarios Routes
/app/backend/modules/inventarios/routes.py:4:Endpoints del módulo de inventarios.
/app/backend/modules/inventarios/routes.py:9:router = APIRouter(prefix="/inventarios", tags=["Inventarios"])
/app/backend/modules/inventarios/schemas.py:2:EDARSA HUB - Inventarios Schemas
/app/backend/modules/inventarios/schemas.py:4:Modelos Pydantic para inventarios.
/app/backend/modules/catalogos/__init__.py:17:- Inventarios (Tipos movimiento, etc.)
/app/backend/modules/catalogos/schemas.py:64:            {"tabla": "Compras_OrdenesEstatus", "nombre": "Estatus de Órdenes", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:75:    "inventarios": {
/app/backend/modules/catalogos/schemas.py:76:        "nombre": "Inventarios",
/app/backend/modules/catalogos/schemas.py:77:        "descripcion": "Catálogos del módulo de Inventarios",
/app/backend/modules/catalogos/schemas.py:313:    "Compras_OrdenesEstatus": {
/app/backend/modules/catalogos/schemas.py:377:    # === INVENTARIOS ===
/app/backend/modules/automatizacion/__init__.py:3:Módulo: Automatización de Análisis de Inventarios
/app/backend/modules/automatizacion/feature_flags.py:3:Feature Flags - Automatización de Análisis de Inventarios
/app/backend/modules/automatizacion/feature_flags.py:16:    "AUTOMATIZACION_INVENTARIOS_ENABLED": False,
/app/backend/modules/automatizacion/feature_flags.py:69:        bool: True si AUTOMATIZACION_INVENTARIOS_ENABLED está en True
/app/backend/modules/automatizacion/feature_flags.py:74:    return FEATURE_FLAGS.get("AUTOMATIZACION_INVENTARIOS_ENABLED", False)
/app/backend/modules/automatizacion/queries_mpro.py:4:# Constantes SQL para detección de inventarios válidos en MPRO
/app/backend/modules/automatizacion/queries_mpro.py:22:WITH inventarios_validos AS (
/app/backend/modules/automatizacion/queries_mpro.py:42:FROM inventarios_validos
/app/backend/modules/automatizacion/queries_mpro.py:51:WITH inventarios_validos AS (
/app/backend/modules/automatizacion/queries_mpro.py:76:FROM inventarios_validos
/app/backend/modules/automatizacion/queries_mpro.py:82:# QUERY: Listar inventarios válidos recientes por sucursal (para detección)
/app/backend/modules/automatizacion/queries_mpro.py:84:QUERY_INVENTARIOS_VALIDOS_SUCURSAL = """
/app/backend/modules/automatizacion/queries_soft.py:4:# Constantes SQL para detección de inventarios válidos en SoftRestaurant
/app/backend/modules/automatizacion/queries_soft.py:16:WITH inventarios_validos AS (
/app/backend/modules/automatizacion/queries_soft.py:33:FROM inventarios_validos
/app/backend/modules/automatizacion/queries_soft.py:42:WITH inventarios_validos AS (
/app/backend/modules/automatizacion/queries_soft.py:61:FROM inventarios_validos
/app/backend/modules/automatizacion/queries_soft.py:67:# QUERY: Listar todos los inventarios válidos de un almacén (para detección)
/app/backend/modules/automatizacion/queries_soft.py:69:QUERY_INVENTARIOS_VALIDOS_ALMACEN = """
/app/backend/modules/automatizacion/queries_soft.py:70:WITH inventarios_validos AS (
/app/backend/modules/automatizacion/queries_soft.py:87:FROM inventarios_validos
/app/backend/modules/automatizacion/repository.py:46:    Lee configuración activa de automatizacion_inventarios_config.
/app/backend/modules/automatizacion/repository.py:67:        FROM automatizacion_inventarios_config
/app/backend/modules/automatizacion/repository.py:122:        FROM automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/repository.py:283:        FROM automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/repository.py:392:    Inserta 1 registro en automatizacion_inventarios_folios_procesados.
/app/backend/modules/automatizacion/repository.py:409:        INSERT INTO automatizacion_inventarios_folios_procesados (
/app/backend/modules/automatizacion/repository.py:496:        FROM automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/repository.py:501:        DELETE FROM automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/repository.py:543:        FROM automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/repository.py:591:    Actualiza la marca de agua en automatizacion_inventarios_ultimo_folio_conocido.
/app/backend/modules/automatizacion/repository.py:628:        FROM automatizacion_inventarios_config
/app/backend/modules/automatizacion/repository.py:688:        FROM automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/schemas.py:3:Schemas Pydantic - Automatización de Análisis de Inventarios
/app/backend/modules/automatizacion/schemas.py:34:# SCHEMA: automatizacion_inventarios_config
/app/backend/modules/automatizacion/schemas.py:66:# SCHEMA: automatizacion_inventarios_destinatarios
/app/backend/modules/automatizacion/schemas.py:101:# SCHEMA: automatizacion_inventarios_folios_procesados
/app/backend/modules/automatizacion/schemas.py:143:# SCHEMA: automatizacion_inventarios_ejecuciones
/app/backend/modules/automatizacion/schemas.py:174:# SCHEMA: automatizacion_inventarios_envios
/app/backend/modules/automatizacion/schemas.py:205:# SCHEMA: automatizacion_inventarios_ultimo_folio_conocido
/app/backend/modules/auth/schemas.py:115:    {"id": "inventarios", "nombre": "Inventarios", "descripcion": "Análisis de inventarios, reportes"},
/app/backend/modules/auth/schemas.py:116:    {"id": "dashboard_inventarios", "nombre": "Dashboard Inventarios", "descripcion": "Gráficas de diferencias de inventario"},
/app/backend/modules/auth/schemas.py:140:        "permisos": ["tablero_ejecutivo", "comercial", "compras", "inventarios", "dashboard_inventarios", "catalogo_sql", "alertas"],
/app/backend/modules/auth/schemas.py:146:        "permisos": ["comercial", "compras", "inventarios", "dashboard_inventarios"],
/app/backend/modules/tablajeria/ordenes_service.py:29:class TablajeriaOrdenesService:
/app/backend/modules/tablajeria/ordenes_service.py:71:            FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/ordenes_service.py:137:                INSERT INTO Operaciones_Tablaje_Ordenes (
/app/backend/modules/tablajeria/ordenes_service.py:198:                    INSERT INTO Operaciones_Tablaje_OrdenesDetalle (
/app/backend/modules/tablajeria/ordenes_service.py:223:            logger.info(f"[TablajeriaOrdenes] Orden creada: {folio} (PlantillaID: {data.plantilla_id})")
/app/backend/modules/tablajeria/ordenes_service.py:238:            logger.error(f"[TablajeriaOrdenes] Error creando orden: {e}")
/app/backend/modules/tablajeria/ordenes_service.py:316:                INSERT INTO Operaciones_Tablaje_Ordenes (
/app/backend/modules/tablajeria/ordenes_service.py:352:                    INSERT INTO Operaciones_Tablaje_OrdenesDetalle (
/app/backend/modules/tablajeria/ordenes_service.py:375:            logger.info(f"[TablajeriaOrdenes] Orden Captura Directa creada: {folio}")
/app/backend/modules/tablajeria/ordenes_service.py:395:            logger.error(f"[TablajeriaOrdenes] Error creando orden captura directa: {e}")
/app/backend/modules/tablajeria/ordenes_service.py:414:                FROM Operaciones_Tablaje_Ordenes o
/app/backend/modules/tablajeria/ordenes_service.py:433:                SELECT * FROM Operaciones_Tablaje_OrdenesDetalle
/app/backend/modules/tablajeria/ordenes_service.py:458:    def listar_ordenes(
/app/backend/modules/tablajeria/ordenes_service.py:482:                FROM Operaciones_Tablaje_Ordenes o
/app/backend/modules/tablajeria/ordenes_service.py:511:            ordenes = []
/app/backend/modules/tablajeria/ordenes_service.py:517:                ordenes.append(o)
/app/backend/modules/tablajeria/ordenes_service.py:522:                FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/ordenes_service.py:537:                "ordenes": ordenes,
/app/backend/modules/tablajeria/ordenes_service.py:560:                SELECT EstatusOrden, FolioOrden FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/ordenes_service.py:573:                UPDATE Operaciones_Tablaje_Ordenes SET
/app/backend/modules/tablajeria/ordenes_service.py:591:            logger.info(f"[TablajeriaOrdenes] Orden iniciada: {orden['FolioOrden']}")
/app/backend/modules/tablajeria/ordenes_service.py:637:                FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/ordenes_service.py:665:                    FROM Operaciones_Tablaje_OrdenesDetalle
/app/backend/modules/tablajeria/ordenes_service.py:691:                    UPDATE Operaciones_Tablaje_OrdenesDetalle SET
/app/backend/modules/tablajeria/ordenes_service.py:734:                UPDATE Operaciones_Tablaje_Ordenes SET
/app/backend/modules/tablajeria/ordenes_service.py:760:            logger.info(f"[TablajeriaOrdenes] Resultados registrados: {orden['FolioOrden']}")
/app/backend/modules/tablajeria/ordenes_service.py:774:            logger.error(f"[TablajeriaOrdenes] Error registrando resultados: {e}")
/app/backend/modules/tablajeria/ordenes_service.py:801:                FROM Operaciones_Tablaje_Ordenes o
/app/backend/modules/tablajeria/ordenes_service.py:832:                UPDATE Operaciones_Tablaje_Ordenes SET
/app/backend/modules/tablajeria/ordenes_service.py:869:                    FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/ordenes_service.py:878:                logger.warning(f"[TablajeriaOrdenes] Orden {orden['FolioOrden']} cerrada sin rendimiento calculado - no se registra en histórico")
/app/backend/modules/tablajeria/ordenes_service.py:910:            logger.info(f"[TablajeriaOrdenes] Orden cerrada: {orden['FolioOrden']} -> {nuevo_estatus}")
/app/backend/modules/tablajeria/ordenes_service.py:924:            logger.error(f"[TablajeriaOrdenes] Error cerrando orden: {e}")
/app/backend/modules/tablajeria/ordenes_service.py:945:                SELECT EstatusOrden, FolioOrden FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/ordenes_service.py:958:                UPDATE Operaciones_Tablaje_Ordenes SET
/app/backend/modules/tablajeria/ordenes_service.py:974:            logger.info(f"[TablajeriaOrdenes] Orden cancelada: {orden['FolioOrden']}")
/app/backend/modules/tablajeria/ordenes_service.py:1007:                FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/ordenes_service.py:1022:                UPDATE Operaciones_Tablaje_Ordenes SET
/app/backend/modules/tablajeria/ordenes_service.py:1057:                FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/ordenes_service.py:1069:            logger.info(f"[TablajeriaOrdenes] Orden {'autorizada' if aprobado else 'rechazada'}: {orden['FolioOrden']}")
/app/backend/modules/tablajeria/dashboard_service.py:60:            query_ordenes = f"""
/app/backend/modules/tablajeria/dashboard_service.py:62:                    COUNT(*) as total_ordenes,
/app/backend/modules/tablajeria/dashboard_service.py:63:                    COUNT(CASE WHEN EstatusOrden = 'CERRADA' THEN 1 END) as ordenes_cerradas,
/app/backend/modules/tablajeria/dashboard_service.py:64:                    COUNT(CASE WHEN EstatusOrden = 'EN_EJECUCION' THEN 1 END) as ordenes_en_proceso,
/app/backend/modules/tablajeria/dashboard_service.py:65:                    COUNT(CASE WHEN EstatusOrden = 'BORRADOR' THEN 1 END) as ordenes_borrador,
/app/backend/modules/tablajeria/dashboard_service.py:66:                    COUNT(CASE WHEN EstatusOrden = 'PENDIENTE_AUTORIZACION' THEN 1 END) as ordenes_pendientes,
/app/backend/modules/tablajeria/dashboard_service.py:67:                    COUNT(CASE WHEN EstatusOrden = 'CANCELADA' THEN 1 END) as ordenes_canceladas,
/app/backend/modules/tablajeria/dashboard_service.py:72:                FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/dashboard_service.py:76:            cursor.execute(query_ordenes, params)
/app/backend/modules/tablajeria/dashboard_service.py:77:            kpis_ordenes = cursor.fetchone()
/app/backend/modules/tablajeria/dashboard_service.py:84:                FROM Operaciones_Tablaje_OrdenesDetalle d
/app/backend/modules/tablajeria/dashboard_service.py:85:                INNER JOIN Operaciones_Tablaje_Ordenes o ON d.OrdenID = o.OrdenID
/app/backend/modules/tablajeria/dashboard_service.py:106:                "ordenes": {
/app/backend/modules/tablajeria/dashboard_service.py:107:                    "total": kpis_ordenes['total_ordenes'] or 0,
/app/backend/modules/tablajeria/dashboard_service.py:108:                    "cerradas": kpis_ordenes['ordenes_cerradas'] or 0,
/app/backend/modules/tablajeria/dashboard_service.py:109:                    "en_proceso": kpis_ordenes['ordenes_en_proceso'] or 0,
/app/backend/modules/tablajeria/dashboard_service.py:110:                    "borrador": kpis_ordenes['ordenes_borrador'] or 0,
/app/backend/modules/tablajeria/dashboard_service.py:111:                    "pendientes_autorizacion": kpis_ordenes['ordenes_pendientes'] or 0,
/app/backend/modules/tablajeria/dashboard_service.py:112:                    "canceladas": kpis_ordenes['ordenes_canceladas'] or 0
/app/backend/modules/tablajeria/dashboard_service.py:115:                    "promedio_porcentaje": float(kpis_ordenes['rendimiento_promedio'] or 0),
/app/backend/modules/tablajeria/dashboard_service.py:116:                    "desviacion_promedio": float(kpis_ordenes['desviacion_promedio'] or 0),
/app/backend/modules/tablajeria/dashboard_service.py:117:                    "kg_planeados": float(kpis_ordenes['kg_procesados_planeados'] or 0),
/app/backend/modules/tablajeria/dashboard_service.py:118:                    "kg_reales": float(kpis_ordenes['kg_procesados_reales'] or 0)
/app/backend/modules/tablajeria/dashboard_service.py:151:                    COUNT(o.OrdenID) as total_ordenes,
/app/backend/modules/tablajeria/dashboard_service.py:158:                LEFT JOIN Operaciones_Tablaje_Ordenes o ON p.PlantillaID = o.PlantillaID
/app/backend/modules/tablajeria/dashboard_service.py:184:                    "total_ordenes": row['total_ordenes'],
/app/backend/modules/tablajeria/dashboard_service.py:208:                    COUNT(*) as ordenes,
/app/backend/modules/tablajeria/dashboard_service.py:212:                FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/dashboard_service.py:223:                    "ordenes": row['ordenes'],
/app/backend/modules/tablajeria/dashboard_service.py:253:                FROM Operaciones_Tablaje_OrdenesDetalle d
/app/backend/modules/tablajeria/dashboard_service.py:254:                INNER JOIN Operaciones_Tablaje_Ordenes o ON d.OrdenID = o.OrdenID
/app/backend/modules/tablajeria/dashboard_service.py:299:                FROM Operaciones_Tablaje_Ordenes o
/app/backend/modules/tablajeria/fase6_service.py:2:EDARSA HUB - Tablajería Fase 6: Inventarios, Costeo y Contabilidad
/app/backend/modules/tablajeria/fase6_service.py:4:Servicio que gestiona la afectación de inventarios, costeo de producción
/app/backend/modules/tablajeria/fase6_service.py:60:    Servicio de Fase 6: Inventarios, Costeo y Contabilidad.
/app/backend/modules/tablajeria/fase6_service.py:63:    - Afectación de inventarios al cerrar órdenes
/app/backend/modules/tablajeria/fase6_service.py:218:    # AFECTACIÓN DE INVENTARIOS
/app/backend/modules/tablajeria/fase6_service.py:229:        Movimientos:
/app/backend/modules/tablajeria/fase6_service.py:235:            Dict con resumen de movimientos generados
/app/backend/modules/tablajeria/fase6_service.py:248:                FROM Operaciones_Tablaje_Ordenes o
/app/backend/modules/tablajeria/fase6_service.py:263:                return {"movimientos": 0, "mensaje": "Afectación automática deshabilitada"}
/app/backend/modules/tablajeria/fase6_service.py:265:            movimientos = []
/app/backend/modules/tablajeria/fase6_service.py:272:                    INSERT INTO Tablajeria_MovimientosInventario (
/app/backend/modules/tablajeria/fase6_service.py:286:                movimientos.append({
/app/backend/modules/tablajeria/fase6_service.py:293:            # Nota: OrdenesDetalle no tiene EsInventariable, usamos GeneraMovimiento y TipoDerivado
/app/backend/modules/tablajeria/fase6_service.py:298:                FROM Operaciones_Tablaje_OrdenesDetalle
/app/backend/modules/tablajeria/fase6_service.py:306:                    INSERT INTO Tablajeria_MovimientosInventario (
/app/backend/modules/tablajeria/fase6_service.py:319:                movimientos.append({
/app/backend/modules/tablajeria/fase6_service.py:329:                    INSERT INTO Tablajeria_MovimientosInventario (
/app/backend/modules/tablajeria/fase6_service.py:342:                movimientos.append({
/app/backend/modules/tablajeria/fase6_service.py:350:                UPDATE Operaciones_Tablaje_Ordenes SET
/app/backend/modules/tablajeria/fase6_service.py:359:            logger.info(f"[FASE6] Inventario afectado para orden {orden['FolioOrden']}: {len(movimientos)} movimientos")
/app/backend/modules/tablajeria/fase6_service.py:364:                "movimientos_generados": len(movimientos),
/app/backend/modules/tablajeria/fase6_service.py:365:                "detalle": movimientos
/app/backend/modules/tablajeria/fase6_service.py:411:                FROM Operaciones_Tablaje_Ordenes o
/app/backend/modules/tablajeria/fase6_service.py:442:            # Nota: OrdenesDetalle no tiene EsInventariable, se infiere de TipoDerivado
/app/backend/modules/tablajeria/fase6_service.py:448:                FROM Operaciones_Tablaje_OrdenesDetalle
/app/backend/modules/tablajeria/fase6_service.py:608:                JOIN Operaciones_Tablaje_Ordenes o ON c.OrdenID = o.OrdenID
/app/backend/modules/tablajeria/fase6_service.py:741:        1. Afectar inventarios
/app/backend/modules/tablajeria/routes.py:28:from .ordenes_service import TablajeriaOrdenesService
/app/backend/modules/tablajeria/routes.py:392:def _get_ordenes_service():
/app/backend/modules/tablajeria/routes.py:394:    return TablajeriaOrdenesService(DB_CONFIG)
/app/backend/modules/tablajeria/routes.py:397:@router.get("/ordenes")
/app/backend/modules/tablajeria/routes.py:398:async def listar_ordenes(
/app/backend/modules/tablajeria/routes.py:414:        service = _get_ordenes_service()
/app/backend/modules/tablajeria/routes.py:424:        result = service.listar_ordenes(
/app/backend/modules/tablajeria/routes.py:441:@router.get("/ordenes/{orden_id}")
/app/backend/modules/tablajeria/routes.py:452:        service = _get_ordenes_service()
/app/backend/modules/tablajeria/routes.py:467:@router.post("/ordenes")
/app/backend/modules/tablajeria/routes.py:481:        service = _get_ordenes_service()
/app/backend/modules/tablajeria/routes.py:501:@router.post("/ordenes/captura-directa")
/app/backend/modules/tablajeria/routes.py:520:        service = _get_ordenes_service()
/app/backend/modules/tablajeria/routes.py:539:@router.put("/ordenes/{orden_id}/iniciar")
/app/backend/modules/tablajeria/routes.py:552:        service = _get_ordenes_service()
/app/backend/modules/tablajeria/routes.py:578:@router.put("/ordenes/{orden_id}/resultados")
/app/backend/modules/tablajeria/routes.py:596:        service = _get_ordenes_service()
/app/backend/modules/tablajeria/routes.py:634:@router.put("/ordenes/{orden_id}/cerrar")
/app/backend/modules/tablajeria/routes.py:649:    1. Afectación de inventarios
/app/backend/modules/tablajeria/routes.py:654:        service = _get_ordenes_service()
/app/backend/modules/tablajeria/routes.py:724:@router.put("/ordenes/{orden_id}/cancelar")
/app/backend/modules/tablajeria/routes.py:738:        service = _get_ordenes_service()
/app/backend/modules/tablajeria/routes.py:766:@router.put("/ordenes/{orden_id}/autorizar")
/app/backend/modules/tablajeria/routes.py:780:        service = _get_ordenes_service()
/app/backend/modules/tablajeria/routes.py:808:@router.get("/ordenes-stats")
/app/backend/modules/tablajeria/routes.py:809:async def obtener_estadisticas_ordenes(
/app/backend/modules/tablajeria/routes.py:841:            FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/routes.py:853:                COUNT(*) as ordenes_cerradas
/app/backend/modules/tablajeria/routes.py:854:            FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/routes.py:864:            FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/routes.py:871:            "ordenes_por_estatus": por_estatus,
/app/backend/modules/tablajeria/routes.py:872:            "total_ordenes": sum(por_estatus.values()),
/app/backend/modules/tablajeria/routes.py:877:                "ordenes_analizadas": metricas['ordenes_cerradas']
/app/backend/modules/tablajeria/routes.py:879:            "ordenes_recientes": recientes
/app/backend/modules/tablajeria/routes.py:890:# FASE 6: INVENTARIOS, COSTEO Y CONTABILIDAD
/app/backend/modules/tablajeria/routes.py:897:@router.post("/ordenes/{orden_id}/fase6/procesar-cierre")
/app/backend/modules/tablajeria/routes.py:908:    Procesa el cierre completo de Fase 6: Inventarios, Costeo y Contabilidad.
/app/backend/modules/tablajeria/routes.py:942:@router.post("/ordenes/{orden_id}/fase6/afectar-inventario")
/app/backend/modules/tablajeria/routes.py:959:@router.post("/ordenes/{orden_id}/fase6/calcular-costeo")
/app/backend/modules/tablajeria/routes.py:996:@router.post("/ordenes/{orden_id}/fase6/generar-poliza")
/app/backend/modules/tablajeria/routes.py:1221:@router.get("/reportes/ordenes")
/app/backend/modules/tablajeria/routes.py:1222:async def exportar_ordenes(
/app/backend/modules/tablajeria/routes.py:1262:            FROM Operaciones_Tablaje_Ordenes
/app/backend/modules/tablajeria/routes.py:1268:        ordenes = []
/app/backend/modules/tablajeria/routes.py:1270:            ordenes.append({
/app/backend/modules/tablajeria/routes.py:1295:            if ordenes:
/app/backend/modules/tablajeria/routes.py:1296:                writer = csv.DictWriter(output, fieldnames=ordenes[0].keys())
/app/backend/modules/tablajeria/routes.py:1298:                writer.writerows(ordenes)
/app/backend/modules/tablajeria/routes.py:1304:                headers={"Content-Disposition": "attachment; filename=ordenes_tablajeria.csv"}
/app/backend/modules/tablajeria/routes.py:1307:        return {"ordenes": ordenes, "total": len(ordenes)}
/app/backend/modules/tablajeria/routes.py:1349:            FROM Operaciones_Tablaje_OrdenesDetalle d
/app/backend/modules/tablajeria/routes.py:1350:            INNER JOIN Operaciones_Tablaje_Ordenes o ON d.OrdenID = o.OrdenID
/app/backend/modules/tablajeria/routes.py:1426:            INNER JOIN Operaciones_Tablaje_Ordenes o ON c.OrdenID = o.OrdenID
/app/backend/modules/universal_query/routes.py:9:- NO asume dominio (no productos, no ventas, no inventarios)
/app/backend/modules/universal_query/routes.py:242:    - NO asume dominio (no productos, no ventas, no inventarios)
/app/backend/modules/finanzas/ingresos.py:299:_movimientos_banco_db = []  # Para estados de cuenta cargados
/app/backend/modules/finanzas/ingresos.py:671:    # En producción: parsear el archivo y extraer movimientos
/app/backend/modules/finanzas/ingresos.py:675:    # Simular extracción de movimientos
/app/backend/modules/finanzas/ingresos.py:676:    movimientos_extraidos = [
/app/backend/modules/finanzas/ingresos.py:678:            "id": len(_movimientos_banco_db) + i + 1,
/app/backend/modules/finanzas/ingresos.py:692:    _movimientos_banco_db.extend(movimientos_extraidos)
/app/backend/modules/finanzas/ingresos.py:698:        "movimientos_extraidos": len(movimientos_extraidos)
/app/backend/modules/finanzas/ingresos.py:702:@router.get("/movimientos-banco")
/app/backend/modules/finanzas/ingresos.py:703:async def listar_movimientos_banco(
/app/backend/modules/finanzas/ingresos.py:707:    """Listar movimientos bancarios cargados"""
/app/backend/modules/finanzas/ingresos.py:708:    movimientos = _movimientos_banco_db.copy()
/app/backend/modules/finanzas/ingresos.py:711:        movimientos = [m for m in movimientos if not m["conciliado"]]
/app/backend/modules/finanzas/ingresos.py:714:        "movimientos": movimientos,
/app/backend/modules/finanzas/ingresos.py:715:        "total": len(movimientos),
/app/backend/modules/finanzas/ingresos.py:716:        "pendientes": len([m for m in _movimientos_banco_db if not m["conciliado"]])
/app/backend/modules/finanzas/repository.py:139:-- TABLA: FIN_Movimientos_Banco
/app/backend/modules/finanzas/repository.py:140:-- Movimientos bancarios para conciliación
/app/backend/modules/finanzas/repository.py:142:IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[FIN_Movimientos_Banco]') AND type in (N'U'))
/app/backend/modules/finanzas/repository.py:144:    CREATE TABLE [dbo].[FIN_Movimientos_Banco] (
/app/backend/modules/finanzas/repository.py:167:    PRINT 'Tabla FIN_Movimientos_Banco creada';
/app/backend/modules/cava_socios/service.py:9:- Registro de movimientos (entradas, consumos, retiros)
/app/backend/modules/cava_socios/service.py:274:                INSERT INTO CavaSocios_Movimientos (
/app/backend/modules/cava_socios/service.py:351:                INSERT INTO CavaSocios_Movimientos (
/app/backend/modules/cava_socios/service.py:463:            # Últimos movimientos
/app/backend/modules/cava_socios/service.py:468:                FROM CavaSocios_Movimientos m
/app/backend/modules/cava_socios/service.py:475:            ultimos_movimientos = []
/app/backend/modules/cava_socios/service.py:477:                ultimos_movimientos.append({
/app/backend/modules/cava_socios/service.py:502:                "ultimos_movimientos": ultimos_movimientos
/app/backend/modules/cava_socios/service.py:510:    def obtener_movimientos_socio(self, socio_id: str) -> List[Dict]:
/app/backend/modules/cava_socios/service.py:511:        """Obtiene todos los movimientos (consumos) de un socio."""
/app/backend/modules/cava_socios/service.py:528:                FROM CavaSocios_Movimientos m
/app/backend/modules/cava_socios/routes.py:269:        # Obtener movimientos del socio
/app/backend/modules/cava_socios/routes.py:270:        movimientos = cava_service.obtener_movimientos_socio(socio_id)
/app/backend/modules/cava_socios/routes.py:274:        pdf_bytes = report_service.generar_historial_consumos(socio, movimientos)
/app/backend/modules/cava_socios/routes.py:395:            movimientos = cava_service.obtener_movimientos_socio(socio_id)
/app/backend/modules/cava_socios/routes.py:396:            pdf_bytes = report_service.generar_historial_consumos(socio, movimientos)
/app/backend/modules/cava_socios/routes.py:459:        movimientos = cava_service.obtener_movimientos_socio(socio_id)
/app/backend/modules/cava_socios/routes.py:460:        pdf_consumos = report_service.generar_historial_consumos(socio, movimientos)
/app/backend/modules/cava_socios/report_service.py:297:    def generar_historial_consumos(self, socio: Dict[str, Any], movimientos: List[Dict]) -> bytes:
/app/backend/modules/cava_socios/report_service.py:332:        consumos = [m for m in movimientos if m.get('tipo_movimiento') in ['CONSUMO', 'CONSUMO_PARCIAL']]
/app/backend/modules/manuales_operativos/service.py:106:                f"asegurando la correcta recepción de productos, verificación de inventarios "
/app/backend/modules/manuales_operativos/service.py:117:                f"Incluye validación de inventarios y autorizaciones requeridas."
/app/backend/modules/manuales_operativos/service.py:304:        politicas.append(f"Período de análisis de inventarios: {dias} días")
/app/backend/modules/manuales_operativos/service.py:329:        # Inventarios
/app/backend/modules/manuales_operativos/triggers.py:240:        f"asegurando la correcta recepción de productos, verificación de inventarios "
/app/backend/modules/manuales_operativos/triggers.py:247:        "Incluye validación de inventarios y autorizaciones requeridas."
/app/backend/modules/manuales_operativos/triggers.py:298:        f"Período de análisis de inventarios: {proceso.get('dias_periodo_analisis', 15)} días",
/app/backend/modules/compras/service.py:7:- Lógica de inventarios físicos, pedidos, facturas
/app/backend/modules/compras/service.py:36:# INVENTARIOS FÍSICOS
/app/backend/modules/compras/service.py:39:async def obtener_inventarios_fisicos(
/app/backend/modules/compras/service.py:46:    Obtiene la lista de inventarios físicos disponibles.
/app/backend/modules/compras/service.py:60:            log_compras_adapter_selected("inventarios-fisicos", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:66:            result = repo.query_inventarios_fisicos_mpro(server, almacen_filtro, sucursal_id)
/app/backend/modules/compras/service.py:67:            log_compras_query_result("inventarios-fisicos", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:70:            log_compras_adapter_selected("inventarios-fisicos", server_id, system_type, "SR_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:75:            result = repo.query_inventarios_fisicos_sr(server, almacen_filtro)
/app/backend/modules/compras/service.py:76:            log_compras_query_result("inventarios-fisicos", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:80:            log_compras_error("inventarios-fisicos", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/modules/compras/service.py:83:                detail=f"El tipo de sistema '{system_type}' (normalizado: {normalized}) no está soportado para inventarios físicos"
/app/backend/modules/compras/service.py:103:        log_compras_error("inventarios-fisicos", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:113:    Obtiene pedidos/requisiciones vigentes.
/app/backend/modules/compras/service.py:130:            log_compras_adapter_selected("pedidos-vigentes", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:134:            log_compras_query_result("pedidos-vigentes", server_id, "SUCCESS", len(data))
/app/backend/modules/compras/service.py:137:            log_compras_adapter_selected("pedidos-vigentes", server_id, system_type, "SR_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:142:                log_compras_query_result("pedidos-vigentes", server_id, "TABLE_NOT_FOUND", 0)
/app/backend/modules/compras/service.py:147:                log_compras_error("pedidos-vigentes", server_id, query_result.status, query_result.message, system_type)
/app/backend/modules/compras/service.py:152:            log_compras_query_result("pedidos-vigentes", server_id, "SUCCESS", len(data))
/app/backend/modules/compras/service.py:155:            log_compras_error("pedidos-vigentes", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/modules/compras/service.py:180:        log_compras_error("pedidos-vigentes", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:331:    'obtener_inventarios_fisicos',
/app/backend/modules/compras/__init__.py:4:Módulo de compras, pedidos e inventarios.
/app/backend/modules/compras/__init__.py:20:NOTA: Los endpoints complejos (calculo-pedido, auditoria-operativa, dashboard)
/app/backend/modules/compras/__init__.py:30:    DetalleMovimientosRequest,
/app/backend/modules/compras/__init__.py:81:    'DetalleMovimientosRequest',
/app/backend/modules/compras/eventos_compras.py:66:    INVENTARIOS = "INVENTARIOS"
/app/backend/modules/compras/eventos_compras.py:67:    REQUISICIONES = "REQUISICIONES"
/app/backend/modules/compras/eventos_compras.py:433:    def detectar_nuevos_inventarios(
/app/backend/modules/compras/eventos_compras.py:440:        Detecta inventarios nuevos desde el último checkpoint.
/app/backend/modules/compras/eventos_compras.py:450:        checkpoint = self.checkpoint_mgr.get_checkpoint(server_id, SyncType.INVENTARIOS)
/app/backend/modules/compras/eventos_compras.py:539:                    server_id, server_name, SyncType.INVENTARIOS,
/app/backend/modules/compras/eventos_compras.py:543:            logger.info(f"[DETECTOR] Inventarios {server_name}: {nuevos} nuevos, {eventos_generados} eventos")
/app/backend/modules/compras/eventos_compras.py:547:            logger.error(f"[DETECTOR] Error detectando inventarios en {server_name}: {e}")
/app/backend/modules/compras/eventos_compras.py:550:    def detectar_nuevas_requisiciones(
/app/backend/modules/compras/eventos_compras.py:557:        Detecta requisiciones nuevas desde el último checkpoint.
/app/backend/modules/compras/eventos_compras.py:563:        checkpoint = self.checkpoint_mgr.get_checkpoint(server_id, SyncType.REQUISICIONES)
/app/backend/modules/compras/eventos_compras.py:588:                        FROM ordenescompra
/app/backend/modules/compras/eventos_compras.py:596:                        FROM ordenescompra
/app/backend/modules/compras/eventos_compras.py:647:                    server_id, server_name, SyncType.REQUISICIONES,
/app/backend/modules/compras/eventos_compras.py:651:            logger.info(f"[DETECTOR] Requisiciones {server_name}: {nuevos} nuevos, {eventos_generados} eventos")
/app/backend/modules/compras/eventos_compras.py:655:            logger.error(f"[DETECTOR] Error detectando requisiciones en {server_name}: {e}")
/app/backend/modules/compras/repository.py:197:# QUERIES SQL - INVENTARIOS FÍSICOS
/app/backend/modules/compras/repository.py:200:def query_inventarios_fisicos_mpro(server: Dict, almacen_filtro: str = "", sucursal_id: str = None) -> List[Dict]:
/app/backend/modules/compras/repository.py:202:    Obtiene inventarios físicos de MPRO.
/app/backend/modules/compras/repository.py:229:def query_inventarios_fisicos_sr(server: Dict, almacen_filtro: str = "") -> List[Dict]:
/app/backend/modules/compras/repository.py:231:    Obtiene inventarios físicos de SoftRestaurant.
/app/backend/modules/compras/repository.py:261:    Obtiene pedidos/requisiciones vigentes de MPRO.
/app/backend/modules/compras/repository.py:490:    # Inventarios físicos
/app/backend/modules/compras/repository.py:491:    'query_inventarios_fisicos_mpro',
/app/backend/modules/compras/repository.py:492:    'query_inventarios_fisicos_sr',
/app/backend/modules/compras/historical_kpis_repository.py:12:- PEDIDO: Pedidos/requisiciones por fecha
/app/backend/modules/compras/historical_kpis_repository.py:96:                -- Inventarios Físicos
/app/backend/modules/compras/historical_kpis_repository.py:107:                [oc_ordenes_count] INT DEFAULT 0,
/app/backend/modules/compras/historical_kpis_repository.py:183:                oc_ordenes_count = %s,
/app/backend/modules/compras/historical_kpis_repository.py:203:                kpi_data.get('oc_ordenes_count', 0),
/app/backend/modules/compras/historical_kpis_repository.py:223:                oc_ordenes_count, oc_total_monto, oc_proveedores_count,
/app/backend/modules/compras/historical_kpis_repository.py:236:                kpi_data.get('oc_ordenes_count', 0),
/app/backend/modules/compras/sync_service.py:2:COMPRAS SYNC SERVICE - Sincronización de Inventarios y Requisiciones a EDARSAHUB
/app/backend/modules/compras/sync_service.py:8:- Compras_Inventarios_Fisicos_Sync: Inventarios físicos sincronizados
/app/backend/modules/compras/sync_service.py:9:- Compras_Requisiciones_Sync: Requisiciones/pedidos sincronizados
/app/backend/modules/compras/sync_service.py:46:def obtener_inventarios_fisicos_sync(
/app/backend/modules/compras/sync_service.py:54:    Obtiene inventarios físicos DESDE EDARSAHUB (sincronizados).
/app/backend/modules/compras/sync_service.py:67:            FROM Compras_Inventarios_Fisicos_Sync
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
/app/backend/modules/compras/sync_service.py:258:            UPDATE Compras_Inventarios_Fisicos_Sync 
/app/backend/modules/compras/sync_service.py:268:                    INSERT INTO Compras_Inventarios_Fisicos_Sync
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
/app/backend/modules/compras/routes.py:54:# - GET /compras/inventarios-fisicos/{server_id}
/app/backend/modules/compras/routes.py:55:# - GET /compras/pedidos-vigentes/{server_id}
/app/backend/modules/compras/routes.py:56:# - GET /compras/detalle-pedido/{server_id}/{folio}
/app/backend/modules/compras/routes.py:57:# - GET /compras/detalle-pedido-manual/{server_id}
/app/backend/modules/compras/routes.py:58:# - GET /compras/detalle-movimientos/{server_id}
/app/backend/modules/compras/routes.py:59:# - GET /compras/detalle-consumos/{server_id}
/app/backend/modules/compras/routes.py:63:# - POST /compras/calculo-pedido (~420 líneas)
/app/backend/modules/compras/routes.py:64:# - POST /compras/auditoria-operativa (~710 líneas)
/app/backend/modules/compras/routes.py:66:# - POST /compras/productos-para-captura
/app/backend/modules/compras/routes.py:67:# - POST /compras/detalle-movimientos
/app/backend/modules/compras/routes.py:68:# - POST /compras/detalle-consumos
/app/backend/modules/compras/schemas.py:50:    folios_requisiciones: Optional[List[str]] = None  # Múltiples requisiciones
/app/backend/modules/compras/schemas.py:53:    solo_skus_requisicion: bool = True  # Por defecto solo muestra SKUs de las requisiciones
/app/backend/modules/compras/schemas.py:62:    folios_requisiciones: Optional[List[str]] = None
/app/backend/modules/compras/schemas.py:65:class DetalleMovimientosRequest(BaseModel):
/app/backend/modules/compras/schemas.py:66:    """Request para detalle de movimientos."""
/app/backend/modules/compras/schemas.py:101:    'DetalleMovimientosRequest',
/app/backend/scripts/solucion_operaciones_analisis.py:8:           Inventarios en la pestaña (tab) de Análisis de OperacionesPanel.
/app/backend/scripts/solucion_operaciones_analisis.py:34:los fallos que impedían la correcta carga de Unidades de Negocio, Almacenes y sus Inventarios asociados.
/app/backend/scripts/solucion_operaciones_analisis.py:41:2. Selectores (Dropdowns) Estáticos/Hardcodeados: Los Almacenes y los Inventarios Inicial/Final no reaccionaban 
/app/backend/scripts/solucion_operaciones_analisis.py:73:INVENTARIOS_ASOCIADOS = {
/app/backend/scripts/solucion_operaciones_analisis.py:86:    logger.info(f"--> Sincronizando cortes de inventarios para la sesión: {list(INVENTARIOS_ASOCIADOS.values())}")
/app/backend/scripts/correccion_sistema_menus_y_fallbacks.py:18:    ("Inventarios FinOps", "Inventarios FinOps", "Database", "costos-placeholder", 1, 4, "OPERADOR_EDARSA"),
/app/backend/scripts/create_cava_socios_rbac.py:90:            'codigo': 'cava_socios.movimientos',
/app/backend/scripts/create_cava_socios_rbac.py:91:            'nombre': 'Movimientos',
/app/backend/scripts/create_cava_socios_rbac.py:92:            'descripcion': 'Historial de movimientos de cava',
/app/backend/scripts/create_cava_socios_rbac.py:94:            'ruta': '/cava-socios/movimientos',
/app/backend/scripts/create_cava_socios_rbac.py:212:            'cava_socios.movimientos': ['VER', 'CREAR', 'EXPORTAR'],
/app/backend/scripts/create_cava_socios_rbac.py:224:            'cava_socios.movimientos': ['VER', 'CREAR', 'EXPORTAR'],
/app/backend/scripts/create_cava_socios_rbac.py:236:            'cava_socios.movimientos': ['VER', 'EXPORTAR'],
/app/backend/scripts/create_cava_socios_rbac.py:248:            'cava_socios.movimientos': ['VER', 'CREAR'],
/app/backend/scripts/create_cava_socios_rbac.py:259:            'cava_socios.movimientos': ['VER', 'CREAR'],
/app/backend/scripts/create_cava_socios_rbac.py:269:            'cava_socios.movimientos': ['VER', 'EXPORTAR'],
/app/backend/scripts/create_cava_socios_tables.py:117:    # 3. Tabla de Movimientos de Cava
/app/backend/scripts/create_cava_socios_tables.py:118:    tables.append(("CavaSocios_Movimientos", """
/app/backend/scripts/create_cava_socios_tables.py:119:        CREATE TABLE CavaSocios_Movimientos (
/app/backend/scripts/create_cava_socios_tables.py:154:            CONSTRAINT FK_CavaSocios_Movimientos_Botella FOREIGN KEY (BotellaID) 
/app/backend/scripts/create_cava_socios_tables.py:156:            CONSTRAINT FK_CavaSocios_Movimientos_Socio FOREIGN KEY (SocioID) 
/app/backend/scripts/create_cava_socios_tables.py:196:                REFERENCES CavaSocios_Movimientos(MovimientoID)
/app/backend/scripts/create_cava_socios_tables.py:230:        "CREATE INDEX IX_CavaSocios_Movimientos_Botella ON CavaSocios_Movimientos(BotellaID)",
/app/backend/scripts/create_cava_socios_tables.py:231:        "CREATE INDEX IX_CavaSocios_Movimientos_Fecha ON CavaSocios_Movimientos(FechaMovimiento)",
/app/backend/scripts/create_cava_socios_tables.py:276:        print("  - CavaSocios_Movimientos: Entradas, consumos, retiros")
/app/backend/scripts/sistema_menus_dinamicos.py:21:    ("Inventarios FinOps", "Inventarios FinOps", "Database", "costos-placeholder", 1, 4, "OPERADOR_EDARSA"),
/app/backend/scripts/create_tablajeria_rbac.py:69:            'codigo': 'tablajeria.ordenes',
/app/backend/scripts/create_tablajeria_rbac.py:73:            'ruta': '/tablajeria/ordenes',
```
## 2. Uso de conexión live dentro de endpoints críticos
```text
/app/backend/modules/comercial/routes.py:57:   - GET /comercial/detalle-movimientos/{server_id} (Fase 5B-4E)
/app/backend/modules/comercial/routes.py:187:# - /comercial/detalle-movimientos/{server_id} - Requiere: tabla de detalle
/app/backend/modules/comercial/routes.py:3241:@router.get("/comercial/detalle-movimientos/{server_id}")
/app/backend/modules/comercial/routes.py:3265:    guard_result = check_live_guard_rail('/comercial/detalle-movimientos', server_id)
/app/backend/modules/fase2_operativo/sql_repository.py:116:    params = (server_id, sucursal_id or '', almacen_id, folio_final_key)
/app/backend/modules/fase2_operativo/sql_repository.py:519:async def obtener_config_asignacion(server_id: str, almacen_id: str) -> Optional[Dict]:
/app/backend/modules/fase2_operativo/sql_repository.py:526:            ConfigID as id, ServerID as server_id, AlmacenID as almacen_id,
/app/backend/modules/fase2_operativo/sql_repository.py:536:    params = (server_id, almacen_id, almacen_id)
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:43:        1. Buscar por server_id + sucursal_id + almacen_id (si se proporciona)
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:32:    NOTA: server_id no existe en Tareas_Inventario.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:33:    Para filtrar por server_id se requiere JOIN con Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:150:        Para filtrar por server_ids se requiere JOIN con Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:167:        # NOTA: server_id no existe en Tareas_Inventario
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:258:        NOTA: server_ids requiere JOIN con Workflow_Inventarios.
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:270:        # NOTA: server_id no existe en Tareas_Inventario
/app/backend/modules/fase2_operativo/services/orquestador_service.py:118:                server_id, sucursal_id, almacen_id, folio_final_key
/app/backend/modules/fase2_operativo/services/orquestador_service.py:130:                server_id, almacen_id
/app/backend/modules/fase2_operativo/services/orquestador_service.py:139:                    f"No existe configuración de asignación para server={server_id}, almacen={almacen_id}. "
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
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:33:    server_id: str
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:297:    server_id: Optional[str] = Query(None),
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:304:    return service.obtener_kpis(server_id)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:309:    server_id: Optional[str] = Query(None),
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:319:    return service.listar_automatizaciones(server_id, sucursal_id, estado, limite)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:418:        server_id=request.server_id,
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:360:        rows = await _execute_sql_async(query, (server_id, almacen_id, almacen_id))
/app/backend/modules/configuracion/services/almacenes_sync_service.py:25:from core.db import execute_sql_query
/app/backend/modules/configuracion/services/almacenes_sync_service.py:92:    - server_id, system_type, sucursal_origen_id via context_resolver
/app/backend/modules/configuracion/services/almacenes_sync_service.py:124:        server_id = context.get("server_id")
/app/backend/modules/configuracion/services/almacenes_sync_service.py:129:        if not server_id:
/app/backend/modules/configuracion/services/almacenes_sync_service.py:140:        from core.server_registry import get_server_connection_info_with_secrets
/app/backend/modules/configuracion/services/almacenes_sync_service.py:141:        # ANTES: server = await db.servers.find_one({"id": server_id}, {"_id": 0})
/app/backend/modules/configuracion/services/almacenes_sync_service.py:142:        server = get_server_connection_info_with_secrets(server_id)
/app/backend/modules/configuracion/services/almacenes_sync_service.py:174:            almacenes_origen = execute_sql_query(
/app/backend/modules/configuracion/services/almacenes_sync_service.py:175:                server['host'],
/app/backend/modules/configuracion/services/almacenes_sync_service.py:177:                server['database'],
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
/app/backend/modules/automatizacion/repository.py:74:    query += " ORDER BY server_id, sucursal_id, almacen_id"
/app/backend/modules/automatizacion/repository.py:184:        sistema_origen, server_id, sucursal_id, almacen_id,
/app/backend/modules/automatizacion/repository.py:403:        sistema_origen, server_id, sucursal_id, almacen_id,
/app/backend/modules/automatizacion/repository.py:624:            id, server_id, sucursal_id, almacen_id,
/app/backend/modules/automatizacion/schemas.py:109:    (sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario, fecha_inventario)
/app/backend/modules/automatizacion/schemas.py:213:    (sistema_origen, server_id, sucursal_id, almacen_id)
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
/app/backend/modules/compras/eventos_compras.py:165:                evento.server_id,
/app/backend/modules/compras/eventos_compras.py:211:                    "server_id": e['ServerID'],
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
/app/backend/modules/compras/repository.py:59:            server['host'], server['port'], server['database'],
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
/app/backend/modules/compras/repository.py:224:        server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:249:    return execute_sql_query(
/app/backend/modules/compras/repository.py:250:        server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:284:    return execute_sql_query(
/app/backend/modules/compras/repository.py:285:        server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:332:        result = execute_sql_query(
/app/backend/modules/compras/repository.py:333:            server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:411:    return execute_sql_query(
/app/backend/modules/compras/repository.py:412:        server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:439:    return execute_sql_query(
/app/backend/modules/compras/repository.py:440:        server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:478:    return execute_sql_query(
/app/backend/modules/compras/repository.py:479:        server['host'], server['port'], server['database'],
/app/backend/modules/compras/repository.py:487:    'get_server_by_id',
/app/backend/modules/compras/historical_kpis_repository.py:90:                [server_id] NVARCHAR(50) NOT NULL,
/app/backend/modules/compras/historical_kpis_repository.py:125:            ON [dbo].[Compras_KPIs_Historico] (server_id, sucursal_id, fecha, kpi_tipo);
/app/backend/modules/compras/historical_kpis_repository.py:145:    server_id: str,
/app/backend/modules/compras/historical_kpis_repository.py:166:        WHERE server_id = %s AND sucursal_id = %s AND fecha = %s AND kpi_tipo = %s
/app/backend/modules/compras/historical_kpis_repository.py:168:        cursor.execute(check_sql, (server_id, sucursal_id, fecha, kpi_tipo))
/app/backend/modules/compras/historical_kpis_repository.py:192:            WHERE server_id = %s AND sucursal_id = %s AND fecha = %s AND kpi_tipo = %s
/app/backend/modules/compras/historical_kpis_repository.py:211:                server_id, sucursal_id, fecha, kpi_tipo
/app/backend/modules/compras/historical_kpis_repository.py:220:                run_id, server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo,
/app/backend/modules/compras/historical_kpis_repository.py:229:                run_id, server_id, sucursal_id, system_type, fecha, kpi_tipo,
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
/app/backend/scripts/create_unidades_negocio_table.py:152:            INSERT INTO Unidades_Negocio (nombre, codigo, server_id, sucursal_origen_id, system_type, orden, activo)
/app/backend/scripts/create_unidades_negocio_table.py:153:            VALUES ('{u['nombre']}', '{u['codigo']}', '{u['server_id']}', {suc_id}, '{u['system_type']}', {u['orden']}, 1);
/app/backend/scripts/run_historical_load_compras.py:129:    server_id: str,
/app/backend/scripts/run_historical_load_compras.py:136:        "server_id": server_id,
/app/backend/scripts/run_historical_load_compras.py:148:        "server_id": server_id,
/app/backend/scripts/run_historical_load_compras.py:165:async def update_checkpoint(db, server_id: str, kpi_tipo: str, updates: Dict):
/app/backend/scripts/run_historical_load_compras.py:169:        {"server_id": server_id, "kpi_tipo": kpi_tipo, "status": {"$ne": STATUS_SUCCESS}},
/app/backend/scripts/run_historical_load_compras.py:593:    server_id = server.get("id")
/app/backend/scripts/run_historical_load_compras.py:598:    checkpoint = await get_or_create_checkpoint(db, server_id, server_name, run_id, kpi_tipo)
/app/backend/scripts/run_historical_load_compras.py:609:    await update_checkpoint(db, server_id, kpi_tipo, {"status": STATUS_RUNNING})
/app/backend/scripts/run_historical_load_compras.py:652:                server_id=server_id,
/app/backend/scripts/run_historical_load_compras.py:653:                sucursal_id=server.get("sucursal_id", server_id),
/app/backend/scripts/run_historical_load_compras.py:672:        await update_checkpoint(db, server_id, kpi_tipo, {
/app/backend/scripts/run_historical_load_compras.py:687:    await update_checkpoint(db, server_id, kpi_tipo, {"status": final_status})
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
/app/backend/tests/test_dashboard_servers.py:116:            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
/app/backend/tests/test_dashboard_servers.py:138:            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
/app/backend/tests/test_dashboard_servers.py:168:            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
/app/backend/tests/test_dashboard_servers.py:185:            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
/app/backend/tests/test_dashboard_servers.py:207:            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
/app/backend/tests/test_dashboard_servers.py:224:            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
/app/backend/tests/test_dashboard_servers.py:243:            f"{BASE_URL}/api/servers/{server_id}/tipos-movimiento",
/app/backend/tests/test_dashboard_servers.py:291:            f"{BASE_URL}/api/servers/{server_id}/tipos-movimiento",
/app/backend/tests/test_comercial_rbac_blindaje.py:267:        """Verify /api/comercial/detalle-movimientos/{server_id} validates access"""
/app/backend/tests/test_comercial_rbac_blindaje.py:278:            f"{BASE_URL}/api/comercial/detalle-movimientos/{server_id}",
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
/app/backend/tests/test_movement_sales_details.py:176:            alm_response = api_client.get(f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes", 
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
/app/backend/server.py:2278:@api_router.get("/servers/{server_id}/tipos-movimiento")
/app/backend/server.py:2279:async def get_tipos_movimiento(server_id: str, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:2305:        logging.warning(f"[GET_TIPOS_MOVIMIENTO] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:2604:                    almacenes = execute_sql_query(
/app/backend/server.py:2658:@api_router.get("/servers/{server_id}/almacenes")
/app/backend/server.py:2659:async def get_almacenes(server_id: str, sucursal_id: Optional[str] = None, sucursal: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:2674:        logging.warning(f"[RBAC-ALMACENES] {current_user.get('email')} sin acceso a servidor {server_id}")
/app/backend/server.py:2682:        logging.warning(f"[GET_ALMACENES] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:2688:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:2692:        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:2707:            almacen_filter = get_almacenes_sql_filter(context, server_id, "Al_Cve_Almacen")
/app/backend/server.py:2727:            almacen_filter = get_almacenes_sql_filter(context, server_id, "idalmacen")
/app/backend/server.py:2747:            almacen_filter = get_almacenes_sql_filter(context, server_id, "Al_Cve_Almacen")
/app/backend/server.py:3175:@api_router.get("/servers/{server_id}/almacenes-softrestaurant")
/app/backend/server.py:3195:        logging.warning(f"[RBAC-ALMACENES-SR] {current_user.get('email')} sin acceso a servidor {server_id}")
/app/backend/server.py:3203:        logging.warning(f"[GET_ALMACENES_SR] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:3212:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:3213:    almacen_filter = get_almacenes_sql_filter(context, server_id, "idalmacen")
/app/backend/server.py:3217:        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:3248:@api_router.get("/servers/{server_id}/inventarios")
/app/backend/server.py:3269:        logging.warning(f"[RBAC-INVENTARIOS-LIST] {current_user.get('email')} sin acceso a servidor {server_id}")
/app/backend/server.py:3277:        logging.warning(f"[GET_INVENTARIOS_LIST] Servidor no encontrado via registry. ID={server_id}")
/app/backend/server.py:3283:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:3287:        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:3293:            almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "F.Al_Cve_Almacen")
/app/backend/server.py:3322:            almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "INV.idalmacen1")
/app/backend/server.py:3364:@api_router.get("/inventarios/pendientes/{server_id}")
/app/backend/server.py:3400:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:3412:        f"Server={server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:3418:            almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "ip.idalmacen")
/app/backend/server.py:3983:            almacen_result = execute_sql_query(
/app/backend/server.py:3988:                logging.error(f"Almacén(es) no encontrado(s) en MPRO - Sucursal: '{sucursal}', Almacenes: {lista_almacenes}, Servidor: {server.get('name', server_id)}")
/app/backend/server.py:4161:            movimientos_result = execute_sql_query(
/app/backend/server.py:4580:            almacen_result = execute_sql_query(
/app/backend/server.py:4585:                logging.error(f"Almacén '{almacen}' no encontrado en servidor {server.get('name', server_id)} ({server['host']})")
/app/backend/server.py:4720:            inventarios_result = execute_sql_query(
/app/backend/server.py:4835:                movimientos_result = execute_sql_query(
/app/backend/server.py:5195:            almacen_result = execute_sql_query(
/app/backend/server.py:6004:    almacenes_permitidos = get_almacenes_permitidos(context, request.server_id)
/app/backend/server.py:6008:        f"Server={request.server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:6417:@api_router.get("/debug/tipos-movimiento-live/{server_id}")
/app/backend/server.py:6418:async def debug_tipos_movimiento_live(server_id: str, current_user: Dict = Depends(get_current_user)):
/app/backend/server.py:6508:            almacen_result = execute_sql_query(
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
/app/backend/server.py:7164:@api_router.get("/compras/inventarios-fisicos/{server_id}")
/app/backend/server.py:7165:async def obtener_inventarios_fisicos(server_id: str, sucursal: str = None, sucursal_id: str = None, almacen: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7181:    almacenes_permitidos = get_almacenes_permitidos(context, server_id)
/app/backend/server.py:7242:        almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "A.Al_Cve_Almacen")
/app/backend/server.py:7285:            log_compras_error("inventarios-fisicos", server_id, "CONNECTION_ERROR", error_msg[:200], server.get('system_type'))
/app/backend/server.py:7291:        almacen_rbac_filter = get_almacenes_sql_filter(context, server_id, "A.idalmacen")
/app/backend/server.py:7317:            log_compras_error("inventarios-fisicos", server_id, "QUERY_ERROR", str(e), server.get('system_type'))
/app/backend/server.py:7322:    log_compras_error("inventarios-fisicos", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/server.py:7325:@api_router.get("/compras/pedidos-vigentes/{server_id}")
/app/backend/server.py:7326:async def obtener_pedidos_vigentes(server_id: str, sucursal: str = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7420:            log_compras_error("pedidos-vigentes", server_id, "CONNECTION_ERROR", error_msg[:200], server.get('system_type'))
/app/backend/server.py:7457:@api_router.get("/compras/detalle-pedido-manual/{server_id}")
/app/backend/server.py:7458:async def obtener_detalle_pedido_manual(server_id: str, folio: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7512:@api_router.get("/compras/detalle-movimientos/{server_id}")
/app/backend/server.py:7513:async def obtener_detalle_movimientos(server_id: str, codigo_producto: str, almacenes: str, fecha_ini: str, fecha_fin: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7549:@api_router.get("/compras/detalle-consumos/{server_id}")
/app/backend/server.py:7550:async def obtener_detalle_consumos(server_id: str, codigo_producto: str, sucursal_codigo: str, fecha_ini: str, fecha_fin: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7584:@api_router.get("/compras/detalle-pedido/{server_id}/{folio}")
/app/backend/server.py:7585:async def obtener_detalle_pedido(server_id: str, folio: str, tipo: str = "PEDIDO", credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:7650:    almacenes_permitidos = get_almacenes_permitidos(context, request.server_id)
/app/backend/server.py:7654:        f"Server={request.server_id}, AlmacenesPermitidos={almacenes_permitidos or 'TODOS'}"
/app/backend/server.py:7682:        almacen_rbac_filter = get_almacenes_sql_filter(context, request.server_id, "A.Al_Cve_Almacen")
/app/backend/server.py:7705:        almacen_result = execute_sql_query(
/app/backend/server.py:8065:@api_router.get("/compras/parametros/{server_id}")
/app/backend/server.py:8740:                consumos_result = execute_sql_query(
/app/backend/server.py:9621:@api_router.get("/compras/dashboard/{server_id}")
/app/backend/server.py:9734:            result_compras = execute_sql_query(
/app/backend/server.py:9850:            result_compras = execute_sql_query(
/app/backend/server.py:10082:        log_compras_error("analisis", request.server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/server.py:10094:@api_router.get("/compras/facturas-proveedor/{server_id}")
/app/backend/server.py:10095:async def obtener_facturas_proveedor(server_id: str, proveedor_codigo: str, anio: int, meses: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:10110:            log_compras_adapter_selected("facturas-proveedor", server_id, system_type, "MPRO_ADAPTER")
/app/backend/server.py:10150:        log_compras_adapter_selected("facturas-proveedor", server_id, system_type, "NO_ADAPTER_AVAILABLE")
/app/backend/server.py:10161:@api_router.get("/compras/detalle-factura/{server_id}/{folio}")
/app/backend/server.py:10162:async def obtener_detalle_factura(server_id: str, folio: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
/app/backend/server.py:10205:        log_compras_adapter_selected("detalle-factura", server_id, system_type, "NO_ADAPTER_AVAILABLE")
/app/backend/core/scheduler/sql_repository.py:183:    params = (sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
/app/backend/core/scheduler/sql_repository.py:207:        sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario,
/app/backend/core/scheduler/sql_repository.py:239:    params = (workflow_id, sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
/app/backend/core/scheduler/sql_repository.py:270:    params = (error_mensaje, sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
/app/backend/core/scheduler/sql_repository.py:315:    params = (sistema_origen, server_id, empresa_id, folio_pedido)
/app/backend/core/scheduler/sql_repository.py:340:        sistema_origen, server_id, empresa_id, sucursal_id, folio_pedido,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:23:- server_id solo para uso interno (nunca expuesto)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:196:                        server_id = server["id"]  # Solo para uso interno
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:197:                        server_name = server.get("name", server_id)
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:210:                            "server_id": server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:248:                                "server_id": server_id,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:283:                            # ANTI-DUPLICADOS: Por empresa_id, no server_id
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
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:727:            server_id=server_id
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:777:        server_id: str,
/app/backend/core/scheduler/jobs/pedidos_detector_job.py:894:            server_id=server["id"],  # Solo para uso interno
/app/backend/core/scheduler/jobs/sync_compras_job.py:35:from core.db import execute_sql_query as _base_execute_sql_query
/app/backend/core/scheduler/jobs/sync_compras_job.py:184:        result = _base_execute_sql_query(host, port, database, username, password, query, timeout_seconds=timeout_seconds, context="jobs")
/app/backend/core/scheduler/jobs/sync_compras_job.py:218:            LEFT JOIN Unidades_Negocio u ON u.server_id = CAST(s.id AS NVARCHAR(36))
/app/backend/core/scheduler/jobs/sync_compras_job.py:322:                'host': server['host'],
/app/backend/core/scheduler/jobs/sync_compras_job.py:324:                'database': server['database'],
/app/backend/core/scheduler/jobs/sync_compras_job.py:368:                        server_id=server_info['id'],
/app/backend/core/scheduler/jobs/sync_compras_job.py:415:                        server_id=server_info['id'],
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:175:            LEFT JOIN Unidades_Negocio u ON u.server_id = CAST(s.id AS NVARCHAR(36))
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:220:    from core.db import execute_sql_query
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:232:        result = execute_sql_query(host, port, database, username, password, query, timeout=timeout_seconds)
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:286:                'host': server['host'],
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:288:                'database': server['database'],
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:20:- server_id
/app/backend/core/scheduler/jobs/inventarios_detector_job.py:53:    get_server_by_id,
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
/app/backend/core/user_access_context.py:313:        if server_id not in almacenes_por_server:
/app/backend/core/user_access_context.py:314:            almacenes_por_server[server_id] = []
/app/backend/core/user_access_context.py:315:        almacenes_por_server[server_id].append(almacen_codigo)
/app/backend/core/user_access_context.py:423:            for server_id, alm_list in almacenes.items():
/app/backend/core/user_access_context.py:425:                    context.almacenes_por_server[server_id] = alm_list
/app/backend/core/user_access_context.py:522:def has_almacen_access(context: UserAccessContext, server_id: str, almacen_id: str) -> bool:
/app/backend/core/user_access_context.py:534:    almacenes_permitidos = context.almacenes_por_server.get(server_id.lower())
/app/backend/core/user_access_context.py:574:def get_almacenes_permitidos(context: UserAccessContext, server_id: str) -> List[str]:
/app/backend/core/user_access_context.py:590:    return context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:593:def get_almacenes_sql_filter(context: UserAccessContext, server_id: str, column_name: str) -> str:
/app/backend/core/user_access_context.py:608:    almacenes = context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:618:def get_almacenes_sql_filter_like(context: UserAccessContext, server_id: str, column_name: str) -> str:
/app/backend/core/user_access_context.py:634:    almacenes = context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:647:def validate_almacen_in_scope(context: UserAccessContext, server_id: str, almacen_id: str) -> bool:
/app/backend/core/user_access_context.py:662:    almacenes_permitidos = context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/user_access_context.py:691:    almacenes_permitidos = context.almacenes_por_server.get(server_id.lower(), [])
/app/backend/core/inventory_analysis_core.py:44:    server_id: str
/app/backend/core/inventory_analysis_core.py:80:            'server_id': self.server_id,
/app/backend/core/inventory_analysis_core.py:153:        logging.info(f"[Core Service] Iniciando análisis para server_id={params.server_id}")
/app/backend/core/inventory_analysis_core.py:212:    server_id: str,
/app/backend/core/inventory_analysis_core.py:222:        server_id: ID del servidor
/app/backend/core/inventory_analysis_core.py:229:    params = {**report_params, 'server_id': server_id}
```
## 3. Archivos backend más contaminados
```text
    546 /app/backend/server.py
    143 /app/backend/modules/comercial/routes.py
    123 /app/backend/core/server_registry.py
    109 /app/backend/modules/comercial/service.py
     72 /app/backend/modules/finanzas/repository_cortes_z.py
     71 /app/backend/modules/sync_recetas/sync_recetas.py
     64 /app/backend/modules/comercial/repository.py
     48 /app/backend/tests/test_simulacion_controlada.py
     45 /app/backend/modules/sync_historicos/service.py
     40 /app/backend/modules/costos_margenes/repository.py
     39 /app/backend/core/context_resolver.py
     34 /app/backend/modules/compras/service.py
     33 /app/backend/tests/test_comercial_rbac_blindaje.py
     33 /app/backend/core/user_access_context.py
     31 /app/backend/modules/sync_historicos/sync_ventas.py
     31 /app/backend/modules/compras/sync_service.py
     31 /app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py
     30 /app/backend/modules/finanzas/propinas_tpv/sql_repository.py
     29 /app/backend/modules/comercial/services/pricing_sugerido_service.py
     28 /app/backend/modules/automatizacion/repository.py
     28 /app/backend/core/connection_resolver.py
     27 /app/backend/modules/comercial_v2/carga_historica_abril_2026.py
     26 /app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py
     26 /app/backend/modules/fase2_operativo/repositories/workflow_repository.py
     26 /app/backend/core/scheduler/jobs/pedidos_detector_job.py
     26 /app/backend/core/scheduler/jobs/inventarios_detector_job.py
     25 /app/backend/tests/test_dashboard_servers.py
     25 /app/backend/scripts/run_historical_load_24_months.py
     25 /app/backend/modules/fase2_operativo/routes/dashboard_routes.py
     24 /app/backend/modules/comercial/services/pricing_ai_service.py
     24 /app/backend/modules/comercial/services/precios_vinos_service.py
     24 /app/backend/modules/comercial/historical_kpis_repository.py
     24 /app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py
     24 /app/backend/api/sync_receiver.py
     23 /app/backend/modules/finanzas/propinas_tpv/service_sql.py
     23 /app/backend/modules/fase2_operativo/repositories/tarea_repository.py
     23 /app/backend/modules/costos_margenes/repository_precios.py
     22 /app/backend/modules/comercial_v2/sync_comercial_edarsahub.py
     22 /app/backend/modules/comercial_v2/carga_historica_24_meses.py
     22 /app/backend/modules/comercial/alertas_margen_repository.py
```
