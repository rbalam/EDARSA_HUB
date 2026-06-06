# AUDITORÍA SQL-FIRST - PRIORIDAD DE MIGRACIÓN

Fuente: /app/docs/reports/AUDITORIA_CONEXIONES_LIVE_20260604_042819.md
Fecha: Thu Jun  4 04:30:28 UTC 2026

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

## 3. Tablas externas detectadas en queries live
```text
/app/backend/init_queries.py:15:    "ventas": """declare @sucursal nvarchar(50)
/app/backend/init_queries.py:18:declare @codigo_venta nvarchar(10)
/app/backend/init_queries.py:23:set @codigo_venta = '0913'
/app/backend/init_queries.py:26:venta.Al_Cve_Almacen,
/app/backend/init_queries.py:32:sum(venta.Vn_Cantidad_1*Producto_Kit.Pk_Cantidad) cantidad
/app/backend/init_queries.py:33:from venta
/app/backend/init_queries.py:34:LEFT join producto_kit on Producto_Kit.Pr_Cve_Producto = venta.Pr_Cve_Producto
/app/backend/init_queries.py:36:LEFT JOIN PRODUCTO P2 ON P2.Pr_Cve_Producto = VENTA.Pr_Cve_Producto
/app/backend/init_queries.py:39:inner join sucursal on sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
/app/backend/init_queries.py:42:and venta.Es_Cve_Estado <>'CA' and
/app/backend/init_queries.py:43:venta.Vn_Fecha between @fecha_ini and @fecha_fin
/app/backend/init_queries.py:45:and venta.Es_Cve_Estado <> 'CA'
/app/backend/init_queries.py:55:venta.Al_Cve_Almacen
/app/backend/init_queries.py:58:venta.Al_Cve_Almacen,
/app/backend/init_queries.py:59:VENTA.Pr_Cve_Producto [Pk_Producto],
/app/backend/init_queries.py:63:VENTA.Vn_Unidad_Control_1 [UN_Cve_Unidad],
/app/backend/init_queries.py:64:sum(venta.Vn_Cantidad_Control_1) cantidad
/app/backend/init_queries.py:65:from venta
/app/backend/init_queries.py:66:INNER join producto on producto.Pr_Cve_Producto = VENTA.Pr_Cve_Producto
/app/backend/init_queries.py:69:inner join sucursal on sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
/app/backend/init_queries.py:72:and venta.Es_Cve_Estado <>'CA' and
/app/backend/init_queries.py:73:venta.Vn_Fecha between @fecha_ini and @fecha_fin
/app/backend/init_queries.py:74:and venta.Es_Cve_Estado <> 'CA'
/app/backend/init_queries.py:78:venta.Pr_Cve_Producto,
/app/backend/init_queries.py:79:VENTA.Vn_Unidad_Control_1,
/app/backend/init_queries.py:84:venta.Al_Cve_Almacen
/app/backend/init_queries.py:87:    "movimientos": """DECLARE @SUCURSAL VARCHAR(50)
/app/backend/init_queries.py:103:    WHEN TM.Tm_Cve_Tipo_Movimiento IN('508','108') 
/app/backend/init_queries.py:121:e.Tm_Cve_Tipo_Movimiento [Codigo],
/app/backend/init_queries.py:122:tm.Tm_Descripcion [Movimiento],
/app/backend/init_queries.py:134:Movimiento E
/app/backend/init_queries.py:137:inner join Tipo_Movimiento tm on tm.Tm_Cve_Tipo_Movimiento = e.Tm_Cve_Tipo_Movimiento
/app/backend/init_queries.py:148:    WHEN TM.Tm_Cve_Tipo_Movimiento IN('508','108') 
/app/backend/init_queries.py:161:AND E.Tm_Cve_Tipo_Movimiento IN ('050','100', '106', '108','112','202','400','500','506','508','510','512')
/app/backend/init_queries.py:225:    "inventarios": """DECLARE @SUCURSAL VARCHAR(20)
/app/backend/init_queries.py:255:FROM Fisico F
/app/backend/init_queries.py:298:            "email": "admin@inventario.com",
/app/backend/init_queries.py:307:        print("Usuario administrador creado: admin@inventario.com / admin123")
/app/backend/modules/comercial/service.py:18:- obtener_ventas_dia_api_local() -> modules/comercial/adapters.py
/app/backend/modules/comercial/service.py:19:- sumar_ventas_api_local_a_sucursal() -> modules/comercial/adapters.py
/app/backend/modules/comercial/service.py:36:from core.db import execute_sql_query, check_column_exists, get_propina_safe_column, get_propina_safe_column_tempcheques
/app/backend/modules/comercial/service.py:43:from modules.comercial.adapters import sumar_ventas_api_local_a_sucursal
/app/backend/modules/comercial/service.py:48:from modules.comercial.queries.softrestaurant import query_ventas_periodo_sr
/app/backend/modules/comercial/service.py:49:from modules.comercial.queries.mpro import query_ventas_periodo_mpro, query_ventas_por_sucursal_mpro
/app/backend/modules/comercial/service.py:375:    (RolConexion = PRINCIPAL_SQL o VENTAS_DIA_API_LOCAL) con NumeroSucursalSistema.
/app/backend/modules/comercial/service.py:390:            # Usar ROW_NUMBER para obtener solo una conexión por empresa, preferir VENTAS_DIA_API_LOCAL
/app/backend/modules/comercial/service.py:406:                                WHEN 'VENTAS_DIA_API_LOCAL' THEN 1 
/app/backend/modules/comercial/service.py:414:                  AND es.RolConexion IN ('PRINCIPAL_SQL', 'VENTAS_DIA_API_LOCAL')
/app/backend/modules/comercial/service.py:476:    Fuente: Comercial_KPIs_Diarios_v2 y Comercial_Ventas_Dia_Abiertas_v2.
/app/backend/modules/comercial/service.py:496:    Obtiene el último día con ventas registradas en Comercial_KPIs_Diarios_v2.
/app/backend/modules/comercial/service.py:505:      AND ventas_total > 0
/app/backend/modules/comercial/service.py:533:            'ventas': float,
/app/backend/modules/comercial/service.py:535:            'cheques': int,
/app/backend/modules/comercial/service.py:552:        ISNULL(SUM(ventas_total), 0) as ventas,
/app/backend/modules/comercial/service.py:554:        ISNULL(SUM(tickets_total), 0) as cheques,
/app/backend/modules/comercial/service.py:561:      AND ventas_total > 0
/app/backend/modules/comercial/service.py:567:        ventas = float(row.get('ventas') or 0)
/app/backend/modules/comercial/service.py:569:        cheques = int(row.get('cheques') or 0)
/app/backend/modules/comercial/service.py:573:            'ventas': ventas,
/app/backend/modules/comercial/service.py:575:            'cheques': cheques,
/app/backend/modules/comercial/service.py:581:        'ventas': 0,
/app/backend/modules/comercial/service.py:583:        'cheques': 0,
/app/backend/modules/comercial/service.py:589:def _get_ventas_abiertas_edarsahub(server_id: str, sucursal_id: str = 'DEFAULT', unidad_negocio_id: str = None) -> Dict:
/app/backend/modules/comercial/service.py:591:    Obtiene ventas abiertas del día desde Comercial_Ventas_Dia_Abiertas_v2.
/app/backend/modules/comercial/service.py:592:    Para modo "Ventas del Día" en Tablero Ejecutivo.
/app/backend/modules/comercial/service.py:604:    - Toma el snapshot más reciente con ventas > 0
/app/backend/modules/comercial/service.py:617:        # Usar ventana operativa de la unidad específica
/app/backend/modules/comercial/service.py:622:            f"[TABLERO-EDARSAHUB] _get_ventas_abiertas: {unidad_negocio_id} FechaOperacion={fecha_operacion} "
/app/backend/modules/comercial/service.py:638:            f"[TABLERO-EDARSAHUB] _get_ventas_abiertas: server_id={server_id} FechaOperacion default={fecha_operacion} "
/app/backend/modules/comercial/service.py:659:            ventas_abiertas,
/app/backend/modules/comercial/service.py:662:            ventas_cerradas_dia,
/app/backend/modules/comercial/service.py:668:        FROM Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/service.py:679:            ventas_abiertas,
/app/backend/modules/comercial/service.py:682:            ventas_cerradas_dia,
/app/backend/modules/comercial/service.py:688:        FROM Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/service.py:706:            ventas_abiertas,
/app/backend/modules/comercial/service.py:709:            ventas_cerradas_dia,
/app/backend/modules/comercial/service.py:715:        FROM Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/service.py:729:        ventas_total = float(row.get('ventas_abiertas') or 0) + float(row.get('ventas_cerradas_dia') or 0)
/app/backend/modules/comercial/service.py:732:            f"[TABLERO-EDARSAHUB] _get_ventas_abiertas: server_id={server_id} "
/app/backend/modules/comercial/service.py:733:            f"fecha_op_calculada={fecha_operacion}, fecha_op_db={fecha_op_usada}, ventas=${ventas_total:,.2f}, is_stale={is_stale}"
/app/backend/modules/comercial/service.py:737:            'ventas': ventas_total,
/app/backend/modules/comercial/service.py:739:            'cheques': int(row.get('tickets_abiertos') or 0) + int(row.get('tickets_cerrados_dia') or 0),
/app/backend/modules/comercial/service.py:748:        f"[TABLERO-EDARSAHUB] _get_ventas_abiertas: Sin datos para server_id={server_id}, "
/app/backend/modules/comercial/service.py:753:        'ventas': 0,
/app/backend/modules/comercial/service.py:755:        'cheques': 0,
/app/backend/modules/comercial/service.py:810:    - ProyecciónMensual = ventas / dias_transcurridos * dias_mes
/app/backend/modules/comercial/service.py:838:    # 1. DETECTAR ÚLTIMO DÍA CON VENTAS EN EL PERÍODO ACTUAL
/app/backend/modules/comercial/service.py:840:    SELECT MAX(fecha_operacion) as ultimo_dia_venta, MAX(dia) as dia_max
/app/backend/modules/comercial/service.py:846:      AND ventas_total > 0
/app/backend/modules/comercial/service.py:850:    if not result_ultimo or not result_ultimo[0].get('ultimo_dia_venta'):
/app/backend/modules/comercial/service.py:854:    ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
/app/backend/modules/comercial/service.py:855:    if isinstance(ultimo_dia_venta, str):
/app/backend/modules/comercial/service.py:856:        partes = ultimo_dia_venta.split('T')[0].split('-') if 'T' in ultimo_dia_venta else ultimo_dia_venta.split('-')
/app/backend/modules/comercial/service.py:861:        anio_ultimo = ultimo_dia_venta.year
/app/backend/modules/comercial/service.py:862:        mes_ultimo = ultimo_dia_venta.month
/app/backend/modules/comercial/service.py:863:        dia_ultimo = ultimo_dia_venta.day
/app/backend/modules/comercial/service.py:872:    # Período actual: desde inicio hasta último día con ventas
/app/backend/modules/comercial/service.py:919:    ventas = kpis_actual['ventas']
/app/backend/modules/comercial/service.py:921:    cheques = kpis_actual['cheques']
/app/backend/modules/comercial/service.py:924:    # PROYECCIÓN MENSUAL: Usar ÚLTIMO DÍA CON VENTAS REGISTRADAS
/app/backend/modules/comercial/service.py:929:    # ProyeccionMensual = VentasAcumuladas / DiasTranscurridosOperativos * DiasMes
/app/backend/modules/comercial/service.py:939:    # - proyección = ventas / 16 * 31
/app/backend/modules/comercial/service.py:955:        ventas_ant = kpis_mes_ant['ventas']
/app/backend/modules/comercial/service.py:957:        cheques_ant = kpis_mes_ant['cheques']
/app/backend/modules/comercial/service.py:959:        ventas_ant = None
/app/backend/modules/comercial/service.py:961:        cheques_ant = None
/app/backend/modules/comercial/service.py:968:        ventas_año = kpis_anio_ant['ventas']
/app/backend/modules/comercial/service.py:970:        cheques_año = kpis_anio_ant['cheques']
/app/backend/modules/comercial/service.py:972:        ventas_año = None
/app/backend/modules/comercial/service.py:974:        cheques_año = None
/app/backend/modules/comercial/service.py:978:    ticket_prom = round(ventas / pax, 2) if pax and pax > 0 else 0
/app/backend/modules/comercial/service.py:979:    cheque_prom = round(ventas / cheques, 2) if cheques and cheques > 0 else 0
/app/backend/modules/comercial/service.py:980:    proyeccion = round((ventas / dias_transcurridos) * dias_mes, 2) if dias_transcurridos > 0 else 0
/app/backend/modules/comercial/service.py:983:    var_vs_mes_ant = _calcular_variacion_pct(ventas, ventas_ant)
/app/backend/modules/comercial/service.py:984:    var_vs_año_ant = _calcular_variacion_pct(ventas, ventas_año)
/app/backend/modules/comercial/service.py:987:    var_cheques_mes = _calcular_variacion_pct(cheques, cheques_ant)
/app/backend/modules/comercial/service.py:988:    var_cheques_año = _calcular_variacion_pct(cheques, cheques_año)
/app/backend/modules/comercial/service.py:990:    logging.info(f"[TABLERO-EDARSAHUB] {nombre_unidad}: Ventas=${ventas:,.0f}, vs Mes Ant={var_vs_mes_ant}%, vs Año Ant={var_vs_año_ant}%")
/app/backend/modules/comercial/service.py:998:        "ventas": ventas,
/app/backend/modules/comercial/service.py:999:        "ventas_ant": ventas_ant,  # null si no existe
/app/backend/modules/comercial/service.py:1000:        "ventas_año": ventas_año,  # null si no existe
/app/backend/modules/comercial/service.py:1009:        "cheques": cheques,
/app/backend/modules/comercial/service.py:1010:        "cheques_ant": cheques_ant,  # null si no existe
/app/backend/modules/comercial/service.py:1011:        "cheques_año": cheques_año,  # null si no existe
/app/backend/modules/comercial/service.py:1012:        "var_cheques_mes": var_cheques_mes,  # null si no existe base
/app/backend/modules/comercial/service.py:1013:        "var_cheques_año": var_cheques_año,  # null si no existe base
/app/backend/modules/comercial/service.py:1025:            "tiene_datos_mes_ant": ventas_ant is not None,
/app/backend/modules/comercial/service.py:1026:            "tiene_datos_anio_ant": ventas_año is not None
/app/backend/modules/comercial/service.py:1059:def calcular_ticket_promedio(ventas: float, cheques: int) -> float:
/app/backend/modules/comercial/service.py:1061:    return round(ventas / cheques, 2) if cheques > 0 else 0.0
/app/backend/modules/comercial/service.py:1064:def calcular_consumo_promedio(ventas: float, pax: int) -> float:
/app/backend/modules/comercial/service.py:1066:    return round(ventas / pax, 2) if pax > 0 else 0.0
/app/backend/modules/comercial/service.py:1078:def procesar_ventas_sucursal(data: Dict, nombre_sucursal: str = "") -> Dict:
/app/backend/modules/comercial/service.py:1080:    Procesa y normaliza datos de ventas de una sucursal.
/app/backend/modules/comercial/service.py:1082:    ventas = float(data.get('ventas', 0) or 0)
/app/backend/modules/comercial/service.py:1084:    cheques = int(data.get('cheques', 0) or 0)
/app/backend/modules/comercial/service.py:1088:        "ventas": ventas,
/app/backend/modules/comercial/service.py:1090:        "cheques": cheques,
/app/backend/modules/comercial/service.py:1091:        "ticket_promedio": calcular_ticket_promedio(ventas, cheques),
/app/backend/modules/comercial/service.py:1092:        "consumo_promedio": calcular_consumo_promedio(ventas, pax),
/app/backend/modules/comercial/service.py:1102:    total_ventas = sum(s.get('ventas', 0) for s in sucursales)
/app/backend/modules/comercial/service.py:1104:    total_cheques = sum(s.get('cheques', 0) for s in sucursales)
/app/backend/modules/comercial/service.py:1107:        "ventas": total_ventas,
/app/backend/modules/comercial/service.py:1109:        "cheques": total_cheques,
/app/backend/modules/comercial/service.py:1110:        "ticket_promedio": calcular_ticket_promedio(total_ventas, total_cheques),
/app/backend/modules/comercial/service.py:1111:        "consumo_promedio": calcular_consumo_promedio(total_ventas, total_pax),
/app/backend/modules/comercial/service.py:1171:    source_live: str = "TEMPCHEQUES",
/app/backend/modules/comercial/service.py:1253:        "data_type": data_type,  # P0: EDARSAHUB_VENTAS_DIA | HUB | LIVE-C
/app/backend/modules/comercial/service.py:1262:        "ventas": kpis.get('ventas', 0) if kpis else None,
/app/backend/modules/comercial/service.py:1263:        "ventas_ant": kpis.get('ventas_ant', 0) if kpis else None,
/app/backend/modules/comercial/service.py:1264:        "ventas_año": kpis.get('ventas_año', 0) if kpis else None,
/app/backend/modules/comercial/service.py:1268:        "cheques": kpis.get('cheques', 0) if kpis else None,
/app/backend/modules/comercial/service.py:1269:        "cheques_ant": kpis.get('cheques_ant', 0) if kpis else None,
/app/backend/modules/comercial/service.py:1270:        "cheques_año": kpis.get('cheques_año', 0) if kpis else None,
/app/backend/modules/comercial/service.py:1348:    return metas or {"meta_ventas": 0, "meta_pax": 0, "meta_cheques": 0}
/app/backend/modules/comercial/service.py:1369:def get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia=False):
/app/backend/modules/comercial/service.py:1384:    Para solo_ventas_dia=True:
/app/backend/modules/comercial/service.py:1385:    - Lee de Comercial_Ventas_Dia_Abiertas_v2 en EDARSAHUB
/app/backend/modules/comercial/service.py:1418:    # MODO VENTAS DEL DÍA: Leer de Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/service.py:1420:    if solo_ventas_dia:
/app/backend/modules/comercial/service.py:1421:        logging.info(f"[TABLERO-EDARSAHUB] {nombre}: Modo Ventas del Día - consultando snapshot EDARSAHUB")
/app/backend/modules/comercial/service.py:1424:        ventas_abiertas = _get_ventas_abiertas_edarsahub(server_id, sucursal_id, unidad_negocio_id=unidad_negocio_codigo)
/app/backend/modules/comercial/service.py:1426:        if ventas_abiertas['existe']:
/app/backend/modules/comercial/service.py:1427:            ventas = ventas_abiertas['ventas']
/app/backend/modules/comercial/service.py:1428:            pax = ventas_abiertas['pax']
/app/backend/modules/comercial/service.py:1429:            cheques = ventas_abiertas['cheques']
/app/backend/modules/comercial/service.py:1431:            if pax == 0 and cheques > 0:
/app/backend/modules/comercial/service.py:1432:                pax = cheques
/app/backend/modules/comercial/service.py:1434:            ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
/app/backend/modules/comercial/service.py:1435:            cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
/app/backend/modules/comercial/service.py:1438:                "ventas": ventas,
/app/backend/modules/comercial/service.py:1439:                "ventas_ant": 0,
/app/backend/modules/comercial/service.py:1440:                "ventas_año": 0,
/app/backend/modules/comercial/service.py:1449:                "cheques": cheques,
/app/backend/modules/comercial/service.py:1450:                "cheques_ant": 0,
/app/backend/modules/comercial/service.py:1451:                "cheques_año": 0,
/app/backend/modules/comercial/service.py:1452:                "var_cheques_mes": 0,
/app/backend/modules/comercial/service.py:1453:                "var_cheques_año": 0,
/app/backend/modules/comercial/service.py:1456:                "es_ventas_dia": True,
/app/backend/modules/comercial/service.py:1464:            logging.warning(f"[TABLERO-EDARSAHUB] {nombre}: Sin snapshot de ventas abiertas disponible")
/app/backend/modules/comercial/service.py:1535:    ventas_total = 0
/app/backend/modules/comercial/service.py:1537:    cheques_total = 0
/app/backend/modules/comercial/service.py:1538:    ventas_ant_total = 0
/app/backend/modules/comercial/service.py:1540:    cheques_ant_total = 0
/app/backend/modules/comercial/service.py:1541:    ventas_año_total = 0
/app/backend/modules/comercial/service.py:1543:    cheques_año_total = 0
/app/backend/modules/comercial/service.py:1565:            ventas_total += kpis.get('ventas', 0)
/app/backend/modules/comercial/service.py:1567:            cheques_total += kpis.get('cheques', 0)
/app/backend/modules/comercial/service.py:1572:                ventas_ant_total += kpis.get('ventas_ant', 0)
/app/backend/modules/comercial/service.py:1574:                cheques_ant_total += kpis.get('cheques_ant', 0)
/app/backend/modules/comercial/service.py:1579:                ventas_año_total += kpis.get('ventas_año', 0)
/app/backend/modules/comercial/service.py:1581:                cheques_año_total += kpis.get('cheques_año', 0)
/app/backend/modules/comercial/service.py:1588:    ticket_prom = round(ventas_total / pax_total, 2) if pax_total > 0 else 0
/app/backend/modules/comercial/service.py:1589:    cheque_prom = round(ventas_total / cheques_total, 2) if cheques_total > 0 else 0
/app/backend/modules/comercial/service.py:1595:    # ProyeccionMensual = VentasAcumuladas / DiasTranscurridosOperativos * DiasMes
/app/backend/modules/comercial/service.py:1634:    proyeccion = round((ventas_total / dias_transcurridos_calc) * dias_mes, 2) if dias_transcurridos_calc > 0 else 0
/app/backend/modules/comercial/service.py:1637:    var_vs_mes_ant = _calcular_variacion_pct(ventas_total, ventas_ant_total if tiene_datos_mes_ant else None)
/app/backend/modules/comercial/service.py:1638:    var_vs_año_ant = _calcular_variacion_pct(ventas_total, ventas_año_total if tiene_datos_anio_ant else None)
/app/backend/modules/comercial/service.py:1641:    var_cheques_mes = _calcular_variacion_pct(cheques_total, cheques_ant_total if tiene_datos_mes_ant else None)
/app/backend/modules/comercial/service.py:1642:    var_cheques_año = _calcular_variacion_pct(cheques_total, cheques_año_total if tiene_datos_anio_ant else None)
/app/backend/modules/comercial/service.py:1644:    logging.info(f"[TABLERO-EDARSAHUB] {nombre}: Consolidado ${ventas_total:,.0f}, vs Mes Ant={var_vs_mes_ant}%, vs Año Ant={var_vs_año_ant}%")
/app/backend/modules/comercial/service.py:1647:        "ventas": ventas_total,
/app/backend/modules/comercial/service.py:1648:        "ventas_ant": ventas_ant_total if tiene_datos_mes_ant else 0,
/app/backend/modules/comercial/service.py:1649:        "ventas_año": ventas_año_total if tiene_datos_anio_ant else 0,
/app/backend/modules/comercial/service.py:1658:        "cheques": cheques_total,
/app/backend/modules/comercial/service.py:1659:        "cheques_ant": cheques_ant_total if tiene_datos_mes_ant else 0,
/app/backend/modules/comercial/service.py:1660:        "cheques_año": cheques_año_total if tiene_datos_anio_ant else 0,
/app/backend/modules/comercial/service.py:1661:        "var_cheques_mes": var_cheques_mes if var_cheques_mes is not None else 0,
/app/backend/modules/comercial/service.py:1662:        "var_cheques_año": var_cheques_año if var_cheques_año is not None else 0,
/app/backend/modules/comercial/service.py:1674:def get_kpis_mpro_por_sucursal(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia=False):
/app/backend/modules/comercial/service.py:1676:    Query para MPRO que devuelve KPIs DIVIDIDOS POR SUCURSAL (como en Inventarios).
/app/backend/modules/comercial/service.py:1683:    - Ventas del día debe leerse desde Comercial_Ventas_Dia_Abiertas_v2 (EDARSAHUB SQL)
/app/backend/modules/comercial/service.py:1687:    - solo_ventas_dia=True → Lee de EDARSAHUB SQL (Comercial_Ventas_Dia_Abiertas_v2)
/app/backend/modules/comercial/service.py:1688:    - solo_ventas_dia=False → Lee de EDARSAHUB SQL (ventas históricas/acumuladas)
/app/backend/modules/comercial/service.py:1691:    logging.debug(f"MPRO {server['name']}: solo_ventas_dia={solo_ventas_dia}, fecha_ini={fecha_ini}, fecha_fin={fecha_fin}")
/app/backend/modules/comercial/service.py:1694:    # FIX P0 (15-May-2026): VENTAS DEL DÍA - LEER DE EDARSAHUB SQL
/app/backend/modules/comercial/service.py:1697:    # OBLIGATORIO: Leer desde Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/service.py:1699:    if solo_ventas_dia:
/app/backend/modules/comercial/service.py:1700:        logging.info(f"[FIX-P0] MPRO {server['name']}: Modo Ventas del Día - LEYENDO DE EDARSAHUB SQL (NO API local)")
/app/backend/modules/comercial/service.py:1719:            # FIX P0: Leer de EDARSAHUB SQL usando _get_ventas_abiertas_edarsahub()
/app/backend/modules/comercial/service.py:1720:            datos_edarsahub = _get_ventas_abiertas_edarsahub(
/app/backend/modules/comercial/service.py:1727:                ventas = datos_edarsahub.get('ventas', 0)
/app/backend/modules/comercial/service.py:1728:                cheques = datos_edarsahub.get('cheques', 0)
/app/backend/modules/comercial/service.py:1729:                pax = datos_edarsahub.get('pax', 0) or cheques
/app/backend/modules/comercial/service.py:1731:                ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
/app/backend/modules/comercial/service.py:1732:                cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
/app/backend/modules/comercial/service.py:1738:                    "ventas": ventas,
/app/backend/modules/comercial/service.py:1739:                    "ventas_ant": 0,
/app/backend/modules/comercial/service.py:1740:                    "ventas_año": 0,
/app/backend/modules/comercial/service.py:1749:                    "cheques": cheques,
/app/backend/modules/comercial/service.py:1750:                    "cheques_ant": 0,
/app/backend/modules/comercial/service.py:1751:                    "cheques_año": 0,
/app/backend/modules/comercial/service.py:1752:                    "var_cheques_mes": 0,
/app/backend/modules/comercial/service.py:1753:                    "var_cheques_año": 0,
/app/backend/modules/comercial/service.py:1756:                    "es_ventas_dia": True,
/app/backend/modules/comercial/service.py:1768:                    f"${ventas:,.2f}, fecha_op={datos_edarsahub.get('fecha_operacion')}"
/app/backend/modules/comercial/service.py:1776:                    "ventas": None,  # None indica "sin dato", no $0
/app/backend/modules/comercial/service.py:1777:                    "ventas_ant": 0,
/app/backend/modules/comercial/service.py:1778:                    "ventas_año": 0,
/app/backend/modules/comercial/service.py:1787:                    "cheques": None,
/app/backend/modules/comercial/service.py:1788:                    "cheques_ant": 0,
/app/backend/modules/comercial/service.py:1789:                    "cheques_año": 0,
/app/backend/modules/comercial/service.py:1790:                    "var_cheques_mes": 0,
/app/backend/modules/comercial/service.py:1791:                    "var_cheques_año": 0,
/app/backend/modules/comercial/service.py:1794:                    "es_ventas_dia": True,
/app/backend/modules/comercial/service.py:1812:    # VENTAS HISTÓRICAS / ACUMULADAS PARA MODO HUB
/app/backend/modules/comercial/service.py:1870:                f"${kpis.get('ventas', 0):,.2f}"
/app/backend/modules/comercial/service.py:1880:                "ventas": None,
/app/backend/modules/comercial/service.py:1881:                "ventas_ant": 0,
/app/backend/modules/comercial/service.py:1882:                "ventas_año": 0,
/app/backend/modules/comercial/service.py:1891:                "cheques": None,
/app/backend/modules/comercial/service.py:1892:                "cheques_ant": 0,
/app/backend/modules/comercial/service.py:1893:                "cheques_año": 0,
/app/backend/modules/comercial/service.py:1894:                "var_cheques_mes": 0,
/app/backend/modules/comercial/service.py:1895:                "var_cheques_año": 0,
/app/backend/modules/comercial/service.py:1929:    # PASO 1: Detectar el último día real con ventas en el período
/app/backend/modules/comercial/service.py:1931:SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
/app/backend/modules/comercial/service.py:1932:FROM Venta_Encabezado VE
/app/backend/modules/comercial/service.py:1939:        if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
/app/backend/modules/comercial/service.py:1940:            ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
/app/backend/modules/comercial/service.py:1941:            if isinstance(ultimo_dia_venta, str):
/app/backend/modules/comercial/service.py:1943:                partes = ultimo_dia_venta.split('-') if '-' in ultimo_dia_venta else None
/app/backend/modules/comercial/service.py:1949:                    dia_con_datos = int(ultimo_dia_venta[-2:])
/app/backend/modules/comercial/service.py:1953:                dia_con_datos = ultimo_dia_venta.day
/app/backend/modules/comercial/service.py:1954:                mes_ultimo = ultimo_dia_venta.month
/app/backend/modules/comercial/service.py:1955:                anio_ultimo = ultimo_dia_venta.year
/app/backend/modules/comercial/service.py:1957:            logging.debug(f"MPRO por sucursal {server['name']} - Ultimo dia con ventas: {anio_ultimo}-{mes_ultimo:02d}-{dia_con_datos:02d}")
/app/backend/modules/comercial/service.py:1959:            # CORRECCIÓN: Usar el mes y año del último día con ventas, no del mes inicial
/app/backend/modules/comercial/service.py:1962:            # Calcular días transcurridos desde fecha_ini hasta el último día con ventas
/app/backend/modules/comercial/service.py:1970:            mes_actual = mes_ultimo  # Usar el mes del último día con ventas
/app/backend/modules/comercial/service.py:2005:    logging.info(f"MPRO {server['name']}: Consultando ventas del {fi} al {ff}")
/app/backend/modules/comercial/service.py:2007:    # BLOQUE 4: Migrado a query centralizada query_ventas_por_sucursal_mpro()
/app/backend/modules/comercial/service.py:2009:    result_principal = query_ventas_por_sucursal_mpro(server, fecha_ini, fecha_fin)
/app/backend/modules/comercial/service.py:2021:        logging.warning(f"MPRO {server['name']}: No se encontraron sucursales con ventas")
/app/backend/modules/comercial/service.py:2046:        ventas = float(row.get('ventas') or 0)
/app/backend/modules/comercial/service.py:2047:        cheques = int(row.get('cheques') or 0)
/app/backend/modules/comercial/service.py:2050:        # Si PAX es 0 pero hay cheques, estimamos PAX = cheques (1 persona por ticket mínimo)
/app/backend/modules/comercial/service.py:2051:        if pax == 0 and cheques > 0:
/app/backend/modules/comercial/service.py:2052:            pax = cheques
/app/backend/modules/comercial/service.py:2054:        # PASO 2: Detectar el último día con ventas PARA ESTA SUCURSAL específica
/app/backend/modules/comercial/service.py:2056:SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
/app/backend/modules/comercial/service.py:2057:FROM Venta_Encabezado VE
/app/backend/modules/comercial/service.py:2065:            if result_ultimo_suc and result_ultimo_suc[0]['ultimo_dia_venta']:
/app/backend/modules/comercial/service.py:2066:                ultimo_dia_suc = result_ultimo_suc[0]['ultimo_dia_venta']
/app/backend/modules/comercial/service.py:2072:                logging.debug(f"MPRO {sucursal_nombre} - Ultimo dia con ventas: dia {dia_suc}")
/app/backend/modules/comercial/service.py:2095:                # Obtener el mes final del rango (mes del último día con ventas global)
/app/backend/modules/comercial/service.py:2116:    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas, 
/app/backend/modules/comercial/service.py:2117:    COUNT(DISTINCT VE.Vn_Folio) as cheques,
/app/backend/modules/comercial/service.py:2119:FROM Venta_Encabezado VE
/app/backend/modules/comercial/service.py:2128:            ventas_ant = float(r_ant[0]['ventas'] or 0) if r_ant else 0
/app/backend/modules/comercial/service.py:2129:            cheques_ant = int(r_ant[0]['cheques'] or 0) if r_ant else 0
/app/backend/modules/comercial/service.py:2131:            if pax_ant == 0 and cheques_ant > 0:
/app/backend/modules/comercial/service.py:2132:                pax_ant = cheques_ant
/app/backend/modules/comercial/service.py:2134:            ventas_ant, cheques_ant, pax_ant = 0, 0, 0
/app/backend/modules/comercial/service.py:2139:    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas, 
/app/backend/modules/comercial/service.py:2140:    COUNT(DISTINCT VE.Vn_Folio) as cheques,
/app/backend/modules/comercial/service.py:2142:FROM Venta_Encabezado VE
/app/backend/modules/comercial/service.py:2151:            ventas_año = float(r_año[0]['ventas'] or 0) if r_año else 0
/app/backend/modules/comercial/service.py:2152:            cheques_año = int(r_año[0]['cheques'] or 0) if r_año else 0
/app/backend/modules/comercial/service.py:2154:            if pax_año == 0 and cheques_año > 0:
/app/backend/modules/comercial/service.py:2155:                pax_año = cheques_año
/app/backend/modules/comercial/service.py:2157:            ventas_año, cheques_año, pax_año = 0, 0, 0
/app/backend/modules/comercial/service.py:2160:        # Sumar ventas del día desde API local si aplica
/app/backend/modules/comercial/service.py:2162:        # En modo "Ventas del Día" (solo_ventas_dia=True): las ventas de API local REEMPLAZAN las de nube
/app/backend/modules/comercial/service.py:2163:        ventas_api_local = sumar_ventas_api_local_a_sucursal(
/app/backend/modules/comercial/service.py:2169:            solo_ventas_dia=solo_ventas_dia  # Pasar flag para modo Ventas del Día
/app/backend/modules/comercial/service.py:2172:        if ventas_api_local.get("aplicado", False):
/app/backend/modules/comercial/service.py:2173:            if ventas_api_local.get("reemplazar", False):
/app/backend/modules/comercial/service.py:2174:                # Modo "Ventas del Día": REEMPLAZAR datos de nube con API local
/app/backend/modules/comercial/service.py:2175:                # Si hay ventas reales en la API local, usar esas
/app/backend/modules/comercial/service.py:2176:                if ventas_api_local["ventas"] > 0 or ventas_api_local["cheques"] > 0:
/app/backend/modules/comercial/service.py:2177:                    ventas = ventas_api_local["ventas"]
/app/backend/modules/comercial/service.py:2178:                    cheques = ventas_api_local["cheques"]
/app/backend/modules/comercial/service.py:2179:                    pax = ventas_api_local["pax"]
/app/backend/modules/comercial/service.py:2180:                    logging.info(f"API Local REEMPLAZÓ datos de {sucursal_nombre}: ${ventas_api_local['ventas']:,.2f} de {ventas_api_local.get('api', 'N/A')}")
/app/backend/modules/comercial/service.py:2182:                    # API local retornó $0 - en modo Ventas del Día, usar $0 (no hay ventas hoy)
/app/backend/modules/comercial/service.py:2183:                    ventas = 0
/app/backend/modules/comercial/service.py:2184:                    cheques = 0
/app/backend/modules/comercial/service.py:2186:                    logging.info(f"API Local retornó $0 para {sucursal_nombre} - Ventas del día = $0")
/app/backend/modules/comercial/service.py:2188:                # Modo normal: SUMAR ventas de API local a las de nube
/app/backend/modules/comercial/service.py:2189:                ventas += ventas_api_local["ventas"]
/app/backend/modules/comercial/service.py:2190:                cheques += ventas_api_local["cheques"]
/app/backend/modules/comercial/service.py:2191:                pax += ventas_api_local["pax"]
/app/backend/modules/comercial/service.py:2192:                logging.info(f"API Local sumada a {sucursal_nombre}: +${ventas_api_local['ventas']:,.2f} de {ventas_api_local.get('api', 'N/A')}")
/app/backend/modules/comercial/service.py:2193:        elif solo_ventas_dia:
/app/backend/modules/comercial/service.py:2194:            # Modo "Ventas del Día" pero no hay API local configurada o no aplicó
/app/backend/modules/comercial/service.py:2195:            # Las ventas deben ser $0 (no mostrar el acumulado del mes)
/app/backend/modules/comercial/service.py:2196:            ventas = 0
/app/backend/modules/comercial/service.py:2197:            cheques = 0
/app/backend/modules/comercial/service.py:2199:            logging.info(f"Modo Ventas del Día pero sin API local para {sucursal_nombre} - Ventas = $0")
/app/backend/modules/comercial/service.py:2200:        # Si no es modo ventas del día y no hay API local, mantener datos de la nube (ya asignados)
/app/backend/modules/comercial/service.py:2204:        ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
/app/backend/modules/comercial/service.py:2205:        cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
/app/backend/modules/comercial/service.py:2206:        proyeccion = round((ventas / dias_transcurridos) * dias_mes, 2) if dias_transcurridos > 0 else 0
/app/backend/modules/comercial/service.py:2209:        var_vs_mes_ant = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
/app/backend/modules/comercial/service.py:2210:        var_vs_año_ant = round(((ventas - ventas_año) / ventas_año * 100), 1) if ventas_año > 0 else 0
/app/backend/modules/comercial/service.py:2212:        logging.debug(f"MPRO {sucursal_nombre}: Dia={dia_suc}, Actual={ventas:.2f}, MesAnt({fia_suc}-{ffa_suc})={ventas_ant:.2f} -> {var_vs_mes_ant}%, AnoAnt({fiaa_suc}-{ffaa_suc})={ventas_año:.2f} -> {var_vs_año_ant}%")
/app/backend/modules/comercial/service.py:2215:        var_cheques_mes = round(((cheques - cheques_ant) / cheques_ant * 100), 1) if cheques_ant > 0 else 0
/app/backend/modules/comercial/service.py:2216:        var_cheques_año = round(((cheques - cheques_año) / cheques_año * 100), 1) if cheques_año > 0 else 0
/app/backend/modules/comercial/service.py:2229:            "ventas": ventas,
/app/backend/modules/comercial/service.py:2230:            "ventas_ant": ventas_ant,
/app/backend/modules/comercial/service.py:2231:            "ventas_año": ventas_año,
/app/backend/modules/comercial/service.py:2240:            "cheques": cheques,
/app/backend/modules/comercial/service.py:2241:            "cheques_ant": cheques_ant,
/app/backend/modules/comercial/service.py:2242:            "cheques_año": cheques_año,
/app/backend/modules/comercial/service.py:2243:            "var_cheques_mes": var_cheques_mes,
/app/backend/modules/comercial/service.py:2244:            "var_cheques_año": var_cheques_año,
/app/backend/modules/comercial/service.py:2252:        logging.info(f"MPRO {server['name']} - Sucursal '{nombre_canonico}' (origen_id={sucursal_id}): Ventas={ventas}, Cheques={cheques}")
/app/backend/modules/comercial/service.py:2265:    solo_ventas_dia: bool = False
/app/backend/modules/comercial/service.py:2271:    - SUCCESS_WITH_DATA: Consulta exitosa con ventas
/app/backend/modules/comercial/service.py:2272:    - SUCCESS_EMPTY: Consulta exitosa, sin ventas (cero real)
/app/backend/modules/comercial/service.py:2287:        unidades = get_kpis_mpro_por_sucursal(server, fecha_ini, fecha_fin, solo_ventas_dia)
/app/backend/modules/comercial/service.py:2328:    'procesar_ventas_sucursal',
/app/backend/modules/comercial/service.py:2407:    ventas = kpis_actual['ventas']
/app/backend/modules/comercial/service.py:2409:    cheques = kpis_actual['cheques']
/app/backend/modules/comercial/service.py:2413:        f"ventas=${ventas:,.2f}, pax={pax}, cheques={cheques}"
/app/backend/modules/comercial/service.py:2417:    ticket_promedio = ventas / cheques if cheques > 0 else 0
/app/backend/modules/comercial/service.py:2418:    pax_promedio = pax / cheques if cheques > 0 else 0
/app/backend/modules/comercial/service.py:2419:    consumo_persona = ventas / pax if pax > 0 else 0
/app/backend/modules/comercial/service.py:2422:    ventas_ant = 0
/app/backend/modules/comercial/service.py:2424:    cheques_ant = 0
/app/backend/modules/comercial/service.py:2429:            ventas_ant = kpis_ant['ventas']
/app/backend/modules/comercial/service.py:2431:            cheques_ant = kpis_ant['cheques']
/app/backend/modules/comercial/service.py:2434:    ventas_ano_ant = 0
/app/backend/modules/comercial/service.py:2436:    cheques_ano_ant = 0
/app/backend/modules/comercial/service.py:2441:            ventas_ano_ant = kpis_ano['ventas']
/app/backend/modules/comercial/service.py:2443:            cheques_ano_ant = kpis_ano['cheques']
/app/backend/modules/comercial/service.py:2446:    vs_periodo_anterior = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
/app/backend/modules/comercial/service.py:2447:    vs_ano_anterior = round(((ventas - ventas_ano_ant) / ventas_ano_ant * 100), 1) if ventas_ano_ant > 0 else 0
/app/backend/modules/comercial/service.py:2451:        'ventas_periodo': ventas,
/app/backend/modules/comercial/service.py:2453:        'cheques_total': cheques,
/app/backend/modules/comercial/service.py:2457:        'mesas_atendidas': cheques,  # Aproximación
/app/backend/modules/comercial/service.py:2459:        'venta_por_hora': 0,  # No disponible en datos consolidados
/app/backend/modules/comercial/service.py:2461:        'ventas_anterior': ventas_ant,
/app/backend/modules/comercial/service.py:2463:        'cheques_anterior': cheques_ant,
/app/backend/modules/comercial/service.py:2464:        'ventas_ano_anterior': ventas_ano_ant,
/app/backend/modules/comercial/service.py:2466:        'cheques_ano_anterior': cheques_ano_ant,
/app/backend/modules/comercial/service.py:2503:            ISNULL(SUM(ventas_total), 0) as ventas,
/app/backend/modules/comercial/service.py:2505:            ISNULL(SUM(tickets_total), 0) as cheques,
/app/backend/modules/comercial/service.py:2511:          AND ventas_total > 0
/app/backend/modules/comercial/service.py:2517:            ventas = float(row.get('ventas') or 0)
/app/backend/modules/comercial/service.py:2519:            cheques = int(row.get('cheques') or 0)
/app/backend/modules/comercial/service.py:2525:                    f"ventas=${ventas:,.2f}, registros={registros}"
/app/backend/modules/comercial/service.py:2528:                    'ventas': ventas,
/app/backend/modules/comercial/service.py:2530:                    'cheques': cheques,
/app/backend/modules/comercial/service.py:2553:            ISNULL(SUM(ventas_total), 0) as ventas,
/app/backend/modules/comercial/service.py:2555:            ISNULL(SUM(tickets_total), 0) as cheques,
/app/backend/modules/comercial/service.py:2561:          AND ventas_total > 0
/app/backend/modules/comercial/service.py:2568:            ventas = float(row.get('ventas') or 0)
/app/backend/modules/comercial/service.py:2570:            cheques = int(row.get('cheques') or 0)
/app/backend/modules/comercial/service.py:2576:                    f"ventas=${ventas:,.2f}, registros={registros}"
/app/backend/modules/comercial/service.py:2579:                    'ventas': ventas,
/app/backend/modules/comercial/service.py:2581:                    'cheques': cheques,
/app/backend/modules/comercial/service.py:2587:        'ventas': 0,
/app/backend/modules/comercial/service.py:2589:        'cheques': 0,
/app/backend/modules/comercial/service.py:2649:                ventas_total,
/app/backend/modules/comercial/service.py:2650:                ventas_sin_propina,
/app/backend/modules/comercial/service.py:2677:                'ventas_periodo': float(row['ventas_sin_propina'] or row['ventas_total'] or 0),
/app/backend/modules/comercial/service.py:2679:                'cheques_total': int(row['tickets_total'] or 0),
/app/backend/modules/comercial/service.py:2685:                'venta_por_hora': 0
/app/backend/modules/comercial/service.py:2692:                'ventas_anterior': 0,
/app/backend/modules/comercial/service.py:2693:                'ventas_ano_anterior': 0
/app/backend/modules/comercial/cache_service.py:63:    "ventas_tiempo": 180,   # 3 minutos
/app/backend/modules/comercial/__init__.py:4:Módulo comercial: dashboards, ventas, metas, ticket perfecto.
/app/backend/modules/comercial/__init__.py:20:- obtener_ventas_dia_api_local()
/app/backend/modules/comercial/__init__.py:21:- sumar_ventas_api_local_a_sucursal()
/app/backend/modules/comercial/__init__.py:30:    VentaSucursal,
/app/backend/modules/comercial/__init__.py:40:    obtener_ventas_dia_api_local,
/app/backend/modules/comercial/__init__.py:41:    sumar_ventas_api_local_a_sucursal,
/app/backend/modules/comercial/__init__.py:65:    'VentaSucursal',
/app/backend/modules/comercial/__init__.py:74:    'obtener_ventas_dia_api_local',
/app/backend/modules/comercial/__init__.py:75:    'sumar_ventas_api_local_a_sucursal',
/app/backend/modules/comercial/queries/__init__.py:22:- VENTAS_TOTAL: query_ventas_periodo_sr/mpro
/app/backend/modules/comercial/queries/__init__.py:23:- PAX_COMENSALES: Incluido en query_ventas_periodo
/app/backend/modules/comercial/queries/__init__.py:24:- CONTEO_CHEQUES: Incluido en query_ventas_periodo
/app/backend/modules/comercial/queries/__init__.py:25:- CORTES_TURNOS: query_ventas_sin_corte_sr/mpro
/app/backend/modules/comercial/queries/__init__.py:34:PRÓXIMO: Bloque 2 - Implementar query_ventas_periodo_sr
/app/backend/modules/comercial/queries/__init__.py:44:# Bloque 2: Query base de ventas SoftRestaurant
/app/backend/modules/comercial/queries/__init__.py:46:    query_ventas_periodo_sr,
/app/backend/modules/comercial/queries/__init__.py:47:    VentasPeriodoResult as VentasPeriodoResultSR,
/app/backend/modules/comercial/queries/__init__.py:50:# Bloque 3: Query base de ventas MPRO
/app/backend/modules/comercial/queries/__init__.py:52:    query_ventas_periodo_mpro,
/app/backend/modules/comercial/queries/__init__.py:53:    VentasPeriodoResult as VentasPeriodoResultMPRO,
/app/backend/modules/comercial/queries/__init__.py:57:VentasPeriodoResult = VentasPeriodoResultSR
/app/backend/modules/comercial/queries/__init__.py:69:__phase__ = "BLOQUE_3_VENTAS_MPRO"
/app/backend/modules/comercial/queries/hub.py:32:        "ventas": float,
/app/backend/modules/comercial/queries/hub.py:34:        "cheques": int,
/app/backend/modules/comercial/queries/mpro.py:10:- Venta_Encabezado (VE): Ventas (folio, fecha, totales)
/app/backend/modules/comercial/queries/mpro.py:14:- Requisicion_Compra: Requisiciones de compra
/app/backend/modules/comercial/queries/mpro.py:15:- Fisico: Inventarios físicos
/app/backend/modules/comercial/queries/mpro.py:18:- query_ventas_periodo_mpro: Ventas totales, PAX, cheques para un período
/app/backend/modules/comercial/queries/mpro.py:19:- query_ventas_sin_corte_mpro: Ventas del día sin cierre
/app/backend/modules/comercial/queries/mpro.py:20:- query_ventas_por_sucursal_mpro: Ventas desglosadas por sucursal
/app/backend/modules/comercial/queries/mpro.py:31:- Campo de ventas: Vn_Precio_Neto_Importe (no 'total')
/app/backend/modules/comercial/queries/mpro.py:81:    'Venta_Encabezado',
/app/backend/modules/comercial/queries/mpro.py:85:    'Requisicion_Compra',
/app/backend/modules/comercial/queries/mpro.py:86:    'Fisico',
/app/backend/modules/comercial/queries/mpro.py:100:class VentasPeriodoResult:
/app/backend/modules/comercial/queries/mpro.py:102:    Resultado homologado de query de ventas por período.
/app/backend/modules/comercial/queries/mpro.py:106:    total_venta: float = 0.0
/app/backend/modules/comercial/queries/mpro.py:108:    cheques: int = 0
/app/backend/modules/comercial/queries/mpro.py:117:def query_ventas_periodo_mpro(
/app/backend/modules/comercial/queries/mpro.py:122:) -> VentasPeriodoResult:
/app/backend/modules/comercial/queries/mpro.py:124:    Query base ÚNICA de ventas para MPRO.
/app/backend/modules/comercial/queries/mpro.py:130:    - total_venta: SUM(VE.Vn_Precio_Neto_Importe) - Venta total en pesos
/app/backend/modules/comercial/queries/mpro.py:132:    - cheques: COUNT(DISTINCT VE.Vn_Folio) - Número de tickets/folios
/app/backend/modules/comercial/queries/mpro.py:135:    - Usa tabla Venta_Encabezado (no cheques)
/app/backend/modules/comercial/queries/mpro.py:141:    - Si PAX real (Comanda.Co_Personas) es 0 pero hay cheques, estima PAX = cheques
/app/backend/modules/comercial/queries/mpro.py:156:        VentasPeriodoResult con métricas o error
/app/backend/modules/comercial/queries/mpro.py:161:        return VentasPeriodoResult(
/app/backend/modules/comercial/queries/mpro.py:170:        return VentasPeriodoResult(
/app/backend/modules/comercial/queries/mpro.py:188:    COUNT(DISTINCT VE.Vn_Folio) as cheques,
/app/backend/modules/comercial/queries/mpro.py:189:    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
/app/backend/modules/comercial/queries/mpro.py:191:FROM Venta_Encabezado VE
/app/backend/modules/comercial/queries/mpro.py:209:            ventas = float(result[0].get('ventas') or 0)
/app/backend/modules/comercial/queries/mpro.py:210:            cheques = int(result[0].get('cheques') or 0)
/app/backend/modules/comercial/queries/mpro.py:214:            # Si PAX es 0 pero hay cheques, estimamos PAX = cheques
/app/backend/modules/comercial/queries/mpro.py:215:            if pax == 0 and cheques > 0:
/app/backend/modules/comercial/queries/mpro.py:216:                pax = cheques
/app/backend/modules/comercial/queries/mpro.py:217:                logging.debug(f"[{MODULE_NAME}] PAX estimado como cheques para {server.get('name')}")
/app/backend/modules/comercial/queries/mpro.py:219:            return VentasPeriodoResult(
/app/backend/modules/comercial/queries/mpro.py:221:                total_venta=ventas,
/app/backend/modules/comercial/queries/mpro.py:223:                cheques=cheques,
/app/backend/modules/comercial/queries/mpro.py:228:            return VentasPeriodoResult(
/app/backend/modules/comercial/queries/mpro.py:230:                total_venta=0.0,
/app/backend/modules/comercial/queries/mpro.py:232:                cheques=0,
/app/backend/modules/comercial/queries/mpro.py:237:        logging.warning(f"[{MODULE_NAME}] Error en query_ventas_periodo_mpro para {server.get('name')}: {e}")
/app/backend/modules/comercial/queries/mpro.py:238:        return VentasPeriodoResult(
/app/backend/modules/comercial/queries/mpro.py:248:def query_ventas_periodo_mpro_con_filtro_flexible(
/app/backend/modules/comercial/queries/mpro.py:254:) -> VentasPeriodoResult:
/app/backend/modules/comercial/queries/mpro.py:256:    Query de ventas MPRO con filtro flexible de sucursal.
/app/backend/modules/comercial/queries/mpro.py:261:    A diferencia de query_ventas_periodo_mpro():
/app/backend/modules/comercial/queries/mpro.py:273:    - ventas: SUM(VE.Vn_Precio_Neto_Importe)
/app/backend/modules/comercial/queries/mpro.py:275:    - cheques: COUNT(DISTINCT VE.Vn_Folio)
/app/backend/modules/comercial/queries/mpro.py:289:        VentasPeriodoResult con métricas o error
/app/backend/modules/comercial/queries/mpro.py:294:        return VentasPeriodoResult(
/app/backend/modules/comercial/queries/mpro.py:303:        return VentasPeriodoResult(
/app/backend/modules/comercial/queries/mpro.py:367:    COUNT(DISTINCT VE.Vn_Folio) as cheques,
/app/backend/modules/comercial/queries/mpro.py:368:    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
/app/backend/modules/comercial/queries/mpro.py:370:FROM Venta_Encabezado VE
/app/backend/modules/comercial/queries/mpro.py:392:            ventas = float(result[0].get('ventas') or 0)
/app/backend/modules/comercial/queries/mpro.py:393:            cheques = int(result[0].get('cheques') or 0)
/app/backend/modules/comercial/queries/mpro.py:396:            print(f"*** [MPRO Query] Ventas={ventas:,.2f}, PAX={pax}, Cheques={cheques} ***")
/app/backend/modules/comercial/queries/mpro.py:398:            # Lógica de estimación PAX (igual que query_ventas_periodo_mpro)
/app/backend/modules/comercial/queries/mpro.py:399:            if pax == 0 and cheques > 0:
/app/backend/modules/comercial/queries/mpro.py:400:                pax = cheques
/app/backend/modules/comercial/queries/mpro.py:401:                logging.debug(f"[{MODULE_NAME}] PAX estimado como cheques para {server.get('name')} (filtro flexible)")
/app/backend/modules/comercial/queries/mpro.py:403:            logging.info(f"[{MODULE_NAME}] query_ventas_periodo_mpro_con_filtro_flexible: "
/app/backend/modules/comercial/queries/mpro.py:404:                        f"Ventas={ventas:,.2f}, PAX={pax}, Cheques={cheques} "
/app/backend/modules/comercial/queries/mpro.py:407:            return VentasPeriodoResult(
/app/backend/modules/comercial/queries/mpro.py:409:                total_venta=ventas,
/app/backend/modules/comercial/queries/mpro.py:411:                cheques=cheques,
/app/backend/modules/comercial/queries/mpro.py:416:            logging.info(f"[{MODULE_NAME}] query_ventas_periodo_mpro_con_filtro_flexible: "
/app/backend/modules/comercial/queries/mpro.py:418:            return VentasPeriodoResult(
/app/backend/modules/comercial/queries/mpro.py:420:                total_venta=0.0,
/app/backend/modules/comercial/queries/mpro.py:422:                cheques=0,
/app/backend/modules/comercial/queries/mpro.py:427:        logging.warning(f"[{MODULE_NAME}] Error en query_ventas_periodo_mpro_con_filtro_flexible "
/app/backend/modules/comercial/queries/mpro.py:429:        return VentasPeriodoResult(
/app/backend/modules/comercial/queries/mpro.py:463:        alias: Alias de la tabla (default: VE para Venta_Encabezado)
/app/backend/modules/comercial/queries/mpro.py:521:                # Si no tiene PRINCIPAL_SQL, intentar con VENTAS_DIA_API_LOCAL
/app/backend/modules/comercial/queries/mpro.py:522:                connection_api = get_connection_for_role(empresa.empresa_id, 'VENTAS_DIA_API_LOCAL')
/app/backend/modules/comercial/queries/mpro.py:555:    alias_venta: str = "VE",
/app/backend/modules/comercial/queries/mpro.py:566:        alias_venta: Alias de tabla Venta_Encabezado
/app/backend/modules/comercial/queries/mpro.py:580:        return f"{alias_venta}.Sc_Cve_Sucursal = '{codigo_resuelto}'"
/app/backend/modules/comercial/queries/mpro.py:594:class VentasPorSucursalResult:
/app/backend/modules/comercial/queries/mpro.py:596:    Resultado de query de ventas agrupadas por sucursal.
/app/backend/modules/comercial/queries/mpro.py:600:    sucursales: List[Dict] = None  # Lista de {sucursal_id, sucursal_nombre, ventas, pax, cheques}
/app/backend/modules/comercial/queries/mpro.py:609:def query_ventas_por_sucursal_mpro(
/app/backend/modules/comercial/queries/mpro.py:613:) -> VentasPorSucursalResult:
/app/backend/modules/comercial/queries/mpro.py:615:    Query base de ventas AGRUPADAS POR SUCURSAL para MPRO.
/app/backend/modules/comercial/queries/mpro.py:620:    DIFERENCIA CON query_ventas_periodo_mpro():
/app/backend/modules/comercial/queries/mpro.py:623:    - Ordena por ventas DESC
/app/backend/modules/comercial/queries/mpro.py:629:    - ventas: SUM(VE.Vn_Precio_Neto_Importe)
/app/backend/modules/comercial/queries/mpro.py:631:    - cheques: COUNT(DISTINCT VE.Vn_Folio)
/app/backend/modules/comercial/queries/mpro.py:635:    - Si PAX es 0 pero hay cheques, el consumidor debe estimar PAX = cheques
/app/backend/modules/comercial/queries/mpro.py:647:        VentasPorSucursalResult con lista de sucursales o error
/app/backend/modules/comercial/queries/mpro.py:652:        return VentasPorSucursalResult(
/app/backend/modules/comercial/queries/mpro.py:661:        return VentasPorSucursalResult(
/app/backend/modules/comercial/queries/mpro.py:678:    COUNT(DISTINCT VE.Vn_Folio) as cheques,
/app/backend/modules/comercial/queries/mpro.py:679:    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
/app/backend/modules/comercial/queries/mpro.py:681:FROM Venta_Encabezado VE
/app/backend/modules/comercial/queries/mpro.py:705:                    "ventas": float(row.get('ventas') or 0),
/app/backend/modules/comercial/queries/mpro.py:707:                    "cheques": int(row.get('cheques') or 0)
/app/backend/modules/comercial/queries/mpro.py:710:            logging.info(f"[{MODULE_NAME}] query_ventas_por_sucursal_mpro: {len(sucursales)} sucursales para {server.get('name')}")
/app/backend/modules/comercial/queries/mpro.py:711:            return VentasPorSucursalResult(
/app/backend/modules/comercial/queries/mpro.py:718:            logging.info(f"[{MODULE_NAME}] query_ventas_por_sucursal_mpro: Sin sucursales con ventas para {server.get('name')}")
/app/backend/modules/comercial/queries/mpro.py:719:            return VentasPorSucursalResult(
/app/backend/modules/comercial/queries/mpro.py:726:        logging.warning(f"[{MODULE_NAME}] Error en query_ventas_por_sucursal_mpro para {server.get('name')}: {e}")
/app/backend/modules/comercial/queries/mpro.py:727:        return VentasPorSucursalResult(
/app/backend/modules/comercial/queries/softrestaurant.py:10:- cheques: Ventas cerradas (con turno)
/app/backend/modules/comercial/queries/softrestaurant.py:11:- tempcheques: Ventas abiertas (sin corte)
/app/backend/modules/comercial/queries/softrestaurant.py:13:- cheqdet: Detalle de productos vendidos
/app/backend/modules/comercial/queries/softrestaurant.py:17:- invfisico: Inventarios físicos
/app/backend/modules/comercial/queries/softrestaurant.py:20:- query_ventas_periodo_sr: Ventas totales, PAX, cheques para un período
/app/backend/modules/comercial/queries/softrestaurant.py:21:- query_ventas_sin_corte_sr: Ventas del día sin corte (tempcheques)
/app/backend/modules/comercial/queries/softrestaurant.py:22:- query_ventas_por_sucursal_sr: Ventas desglosadas por sucursal
/app/backend/modules/comercial/queries/softrestaurant.py:30:- Filtrar cheques.cancelado = 0 siempre
/app/backend/modules/comercial/queries/softrestaurant.py:58:    'cheques',
/app/backend/modules/comercial/queries/softrestaurant.py:59:    'tempcheques', 
/app/backend/modules/comercial/queries/softrestaurant.py:61:    'cheqdet',
/app/backend/modules/comercial/queries/softrestaurant.py:65:    'invfisico',
/app/backend/modules/comercial/queries/softrestaurant.py:66:    'invfisicomovtos',
/app/backend/modules/comercial/queries/softrestaurant.py:80:class VentasPeriodoResult:
/app/backend/modules/comercial/queries/softrestaurant.py:82:    Resultado homologado de query de ventas por período.
/app/backend/modules/comercial/queries/softrestaurant.py:83:    Esta estructura es la ÚNICA que debe usarse para retornar métricas de ventas.
/app/backend/modules/comercial/queries/softrestaurant.py:86:    total_venta: float = 0.0
/app/backend/modules/comercial/queries/softrestaurant.py:88:    cheques: int = 0
/app/backend/modules/comercial/queries/softrestaurant.py:97:def query_ventas_periodo_sr(
/app/backend/modules/comercial/queries/softrestaurant.py:102:) -> VentasPeriodoResult:
/app/backend/modules/comercial/queries/softrestaurant.py:104:    Query base ÚNICA de ventas para SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:110:    - total_venta: SUM(cheques.total - cheques.propina) - Venta total en pesos (SIN propinas)
/app/backend/modules/comercial/queries/softrestaurant.py:111:    - pax: SUM(cheques.nopersonas) - Total de comensales/personas
/app/backend/modules/comercial/queries/softrestaurant.py:112:    - cheques: COUNT(DISTINCT cheques.folio) - Número de tickets/cuentas
/app/backend/modules/comercial/queries/softrestaurant.py:117:    - Filtro cheques.cancelado = 0 para excluir cancelados
/app/backend/modules/comercial/queries/softrestaurant.py:132:        VentasPeriodoResult con métricas o error
/app/backend/modules/comercial/queries/softrestaurant.py:137:        return VentasPeriodoResult(
/app/backend/modules/comercial/queries/softrestaurant.py:146:        return VentasPeriodoResult(
/app/backend/modules/comercial/queries/softrestaurant.py:156:    filtro_suc = _build_sucursal_filter_sr(sucursal_id, alias="cheques")
/app/backend/modules/comercial/queries/softrestaurant.py:158:    # Verificar si la tabla cheques tiene columna 'propina'
/app/backend/modules/comercial/queries/softrestaurant.py:161:        server['username'], server['password'], 'cheques', 'propina'
/app/backend/modules/comercial/queries/softrestaurant.py:166:    # NOTA: Se excluyen propinas de las ventas SI la columna existe
/app/backend/modules/comercial/queries/softrestaurant.py:169:    COUNT(DISTINCT cheques.folio) as cheques,
/app/backend/modules/comercial/queries/softrestaurant.py:170:    ISNULL(SUM(cheques.total{propina_expr}), 0) as ventas,
/app/backend/modules/comercial/queries/softrestaurant.py:171:    ISNULL(SUM(cheques.nopersonas), 0) as pax
/app/backend/modules/comercial/queries/softrestaurant.py:172:FROM cheques
/app/backend/modules/comercial/queries/softrestaurant.py:173:INNER JOIN turnos ON turnos.idturno = cheques.idturno
/app/backend/modules/comercial/queries/softrestaurant.py:176:  AND cheques.cancelado = 0
/app/backend/modules/comercial/queries/softrestaurant.py:191:            return VentasPeriodoResult(
/app/backend/modules/comercial/queries/softrestaurant.py:193:                total_venta=float(result[0].get('ventas') or 0),
/app/backend/modules/comercial/queries/softrestaurant.py:195:                cheques=int(result[0].get('cheques') or 0),
/app/backend/modules/comercial/queries/softrestaurant.py:200:            return VentasPeriodoResult(
/app/backend/modules/comercial/queries/softrestaurant.py:202:                total_venta=0.0,
/app/backend/modules/comercial/queries/softrestaurant.py:204:                cheques=0,
/app/backend/modules/comercial/queries/softrestaurant.py:209:        logging.warning(f"[{MODULE_NAME}] Error en query_ventas_periodo_sr para {server.get('name')}: {e}")
/app/backend/modules/comercial/queries/softrestaurant.py:210:        return VentasPeriodoResult(
/app/backend/modules/comercial/queries/softrestaurant.py:233:def _build_sucursal_filter_sr(sucursal_id: Optional[str], alias: str = "cheques") -> str:
/app/backend/modules/comercial/queries/softrestaurant.py:244:        alias: Alias de la tabla (default: cheques)
/app/backend/modules/comercial/adapters.py:17:║ - Resolución por RolConexion (EmpresaID + VENTAS_DIA_API_LOCAL)            ║
/app/backend/modules/comercial/adapters.py:113:    Busca la conexión con RolConexion = 'VENTAS_DIA_API_LOCAL'.
/app/backend/modules/comercial/adapters.py:125:        # Buscar conexión con rol VENTAS_DIA_API_LOCAL
/app/backend/modules/comercial/adapters.py:126:        connection = get_connection_for_role(empresa_id, 'VENTAS_DIA_API_LOCAL')
/app/backend/modules/comercial/adapters.py:226:def obtener_ventas_dia_api_local(api_config: dict, forzar_consulta: bool = False) -> dict:
/app/backend/modules/comercial/adapters.py:228:    Obtiene las ventas del día actual desde una API MPRO local.
/app/backend/modules/comercial/adapters.py:232:        forzar_consulta: Si True (modo Ventas del Día), ignora la restricción de hora de réplica
/app/backend/modules/comercial/adapters.py:235:        dict con ventas, cheques, pax
/app/backend/modules/comercial/adapters.py:248:        return {"ventas": 0, "cheques": 0, "pax": 0, "omitido": True, "razon": "post_replica"}
/app/backend/modules/comercial/adapters.py:251:        logging.info(f"API Local {api_config['nombre']}: FORZANDO consulta (modo Ventas del Día)")
/app/backend/modules/comercial/adapters.py:253:        logging.info(f"API Local {api_config['nombre']}: Consultando ventas del día (hora {hora_actual} < {hora_replica})")
/app/backend/modules/comercial/adapters.py:255:    # Query para obtener ventas del día actual
/app/backend/modules/comercial/adapters.py:257:    sql_ventas_hoy = """
/app/backend/modules/comercial/adapters.py:259:        ISNULL(SUM(cd_importe), 0) as ventas,
/app/backend/modules/comercial/adapters.py:260:        COUNT(DISTINCT Comanda.co_folio) as cheques,
/app/backend/modules/comercial/adapters.py:267:    result = query_api_mpro_local(api_config, sql_ventas_hoy)
/app/backend/modules/comercial/adapters.py:286:        ventas = float(row.get("ventas", 0) or 0)
/app/backend/modules/comercial/adapters.py:287:        cheques = int(row.get("cheques", 0) or 0)
/app/backend/modules/comercial/adapters.py:290:        logging.info(f"API Local {api_config['nombre']}: Ventas HOY = ${ventas:,.2f}, Cheques = {cheques}, PAX = {pax}")
/app/backend/modules/comercial/adapters.py:291:        print(f"*** API Local {api_config['nombre']}: Ventas HOY = ${ventas:,.2f}, Cheques = {cheques}, PAX = {pax} ***")
/app/backend/modules/comercial/adapters.py:292:        return {"ventas": ventas, "cheques": cheques, "pax": pax, "omitido": False}
/app/backend/modules/comercial/adapters.py:295:        logging.warning(f"API Local {api_config['nombre']}: Error obteniendo ventas - {error_msg}")
/app/backend/modules/comercial/adapters.py:297:        return {"ventas": 0, "cheques": 0, "pax": 0, "omitido": True, "razon": "error", "error": error_msg}
/app/backend/modules/comercial/adapters.py:300:def sumar_ventas_api_local_a_sucursal(
/app/backend/modules/comercial/adapters.py:306:    solo_ventas_dia: bool = False
/app/backend/modules/comercial/adapters.py:310:    y si el período solicitado incluye HOY, suma las ventas del día.
/app/backend/modules/comercial/adapters.py:314:    Cuando solo_ventas_dia=True, las ventas de API local REEMPLAZAN (no suman) las de la nube.
/app/backend/modules/comercial/adapters.py:322:        solo_ventas_dia: Si True, modo "Ventas del Día" - reemplazar datos nube
/app/backend/modules/comercial/adapters.py:325:        dict con ventas_adicionales, cheques_adicionales, pax_adicionales
/app/backend/modules/comercial/adapters.py:334:    print(f"*** API Local Check: server_host={server_host}, sucursal={sucursal_nombre}, fecha_fin={fecha_fin}, hoy_mexico={hoy}, MODO_VENTAS_DIA={solo_ventas_dia} ***")
/app/backend/modules/comercial/adapters.py:350:        return {"ventas": 0, "cheques": 0, "pax": 0, "aplicado": False, "reemplazar": False, "razon": "fecha_no_incluye_hoy"}
/app/backend/modules/comercial/adapters.py:365:            # Paso 2: Obtener API local para esta empresa (RolConexion = VENTAS_DIA_API_LOCAL)
/app/backend/modules/comercial/adapters.py:372:                ventas_api = obtener_ventas_dia_api_local(api_config, forzar_consulta=solo_ventas_dia)
/app/backend/modules/comercial/adapters.py:374:                if not ventas_api.get("omitido", True):
/app/backend/modules/comercial/adapters.py:375:                    modo = "REEMPLAZANDO" if solo_ventas_dia else "SUMANDO"
/app/backend/modules/comercial/adapters.py:376:                    print(f"*** API Local {modo}: +${ventas_api['ventas']:,.2f} de {api_config['nombre']} (via EmpresaResolver) ***")
/app/backend/modules/comercial/adapters.py:378:                        "ventas": ventas_api["ventas"],
/app/backend/modules/comercial/adapters.py:379:                        "cheques": ventas_api["cheques"],
/app/backend/modules/comercial/adapters.py:380:                        "pax": ventas_api["pax"],
/app/backend/modules/comercial/adapters.py:382:                        "reemplazar": solo_ventas_dia,
/app/backend/modules/comercial/adapters.py:388:                    razon = ventas_api.get("razon", "omitido")
/app/backend/modules/comercial/adapters.py:391:                        "ventas": 0, "cheques": 0, "pax": 0,
/app/backend/modules/comercial/adapters.py:393:                        "reemplazar": solo_ventas_dia,
/app/backend/modules/comercial/adapters.py:400:                print(f"*** API Local: EmpresaID={empresa_id} no tiene API local configurada (VENTAS_DIA_API_LOCAL) ***")
/app/backend/modules/comercial/adapters.py:441:                ventas_api = obtener_ventas_dia_api_local(api_cfg, forzar_consulta=solo_ventas_dia)
/app/backend/modules/comercial/adapters.py:443:                if not ventas_api.get("omitido", True):
/app/backend/modules/comercial/adapters.py:444:                    modo = "REEMPLAZANDO" if solo_ventas_dia else "SUMANDO"
/app/backend/modules/comercial/adapters.py:445:                    print(f"*** API Local LEGACY {modo}: +${ventas_api['ventas']:,.2f} de {api_cfg['nombre']} ***")
/app/backend/modules/comercial/adapters.py:447:                        "ventas": ventas_api["ventas"],
/app/backend/modules/comercial/adapters.py:448:                        "cheques": ventas_api["cheques"],
/app/backend/modules/comercial/adapters.py:449:                        "pax": ventas_api["pax"],
/app/backend/modules/comercial/adapters.py:451:                        "reemplazar": solo_ventas_dia,
/app/backend/modules/comercial/adapters.py:457:                    razon = ventas_api.get("razon", "omitido")
/app/backend/modules/comercial/adapters.py:460:                        "ventas": 0, "cheques": 0, "pax": 0,
/app/backend/modules/comercial/adapters.py:462:                        "reemplazar": solo_ventas_dia,
/app/backend/modules/comercial/adapters.py:471:    return {"ventas": 0, "cheques": 0, "pax": 0, "aplicado": False, "reemplazar": False, "razon": "sin_api_local"}
/app/backend/modules/comercial/adapters.py:477:    'obtener_ventas_dia_api_local',
/app/backend/modules/comercial/adapters.py:478:    'sumar_ventas_api_local_a_sucursal',
/app/backend/modules/comercial/crm_router.py:180:    a una cuenta comercial específica en el maestro de ventas.
/app/backend/modules/comercial/crm_router.py:184:        FROM dbo.Venta_Cotizaciones 
/app/backend/modules/comercial/crm_router.py:207:        INSERT INTO dbo.Venta_Cotizaciones (CuentaID, FolioCotizacion, Version, Subtotal, Impuesto, Total, Moneda, TipoCambio, UsuarioCreadorID, Estatus)
/app/backend/modules/comercial/crm_router.py:224:        INSERT INTO dbo.Venta_CotizacionesDetalle (CotizacionID, ProductoID, Cantidad, PrecioUnitario, TotalLinea)
/app/backend/modules/comercial/crm_router.py:250:@router.get("/pedidos-venta")
/app/backend/modules/comercial/crm_router.py:253:    Fase 9: Consulta los pedidos oficiales del maestro transaccional Venta_Pedidos.
/app/backend/modules/comercial/crm_router.py:255:    query = "SELECT * FROM dbo.Venta_Pedidos ORDER BY FechaCreacion DESC"
/app/backend/modules/comercial/crm_router.py:258:@router.post("/pedidos-venta/convertir")
/app/backend/modules/comercial/crm_router.py:265:    query_cot = "SELECT * FROM dbo.Venta_Cotizaciones WHERE CotizacionID = %s"
/app/backend/modules/comercial/crm_router.py:276:        INSERT INTO dbo.Venta_Pedidos (CuentaID, FolioPedido, Subtotal, Impuesto, Total, Moneda, TipoCambio, UsuarioCreadorID, Estatus)
/app/backend/modules/comercial/crm_router.py:290:    # 3. Clonar las líneas de detalle hacia Venta_PedidosDetalle
/app/backend/modules/comercial/crm_router.py:291:    query_lineas = "SELECT * FROM dbo.Venta_CotizacionesDetalle WHERE CotizacionID = %s"
/app/backend/modules/comercial/crm_router.py:295:        INSERT INTO dbo.Venta_PedidosDetalle (PedidoID, ProductoID, Cantidad, PrecioUnitario, TotalLinea)
/app/backend/modules/comercial/crm_router.py:302:    query_up_cot = "UPDATE dbo.Venta_Cotizaciones SET Estatus = 'Convertida' WHERE CotizacionID = %s"
/app/backend/modules/comercial/crm_router.py:433:    # 4. Índice de Satisfacción del Cliente (CSAT) de Postventa (Fase 11)
/app/backend/modules/comercial/crm_router.py:436:        FROM dbo.CRM_PostventaEncuestas
/app/backend/modules/comercial/crm_router.py:476:    y el comportamiento general de postventa (CSAT).
/app/backend/modules/comercial/crm_router.py:494:    query_csat = "SELECT COALESCE(AVG(CAST(PuntuacionCSAT AS DECIMAL(18,2))), 4.0) as Promedio FROM dbo.CRM_PostventaEncuestas"
/app/backend/modules/comercial/crm_router.py:522:def agente_seguimiento_salud_ventas(usuario_id: int, mes: int, anio: int):
/app/backend/modules/comercial/crm_router.py:528:    query_meta = "SELECT COALESCE(meta_venta, 0.0) as Meta FROM dbo.Comercial_Metas WHERE mes = %s AND anio = %s"
/app/backend/modules/comercial/inteligencia_comercial_routes.py:181:        SUM(ventas_total) AS ventas_total,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:182:        SUM(ventas_sin_propina) AS ventas_sin_propina,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:187:             THEN SUM(ventas_sin_propina) / SUM(tickets_total)
/app/backend/modules/comercial/inteligencia_comercial_routes.py:190:             THEN SUM(ventas_sin_propina) / SUM(pax_total)
/app/backend/modules/comercial/inteligencia_comercial_routes.py:193:        SUM(ventas_cerradas) AS ventas_cerradas,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:194:        SUM(ventas_abiertas) AS ventas_abiertas,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:206:@router.get("/ventas-comparativo")
/app/backend/modules/comercial/inteligencia_comercial_routes.py:207:async def get_ventas_comparativo(
/app/backend/modules/comercial/inteligencia_comercial_routes.py:215:    Comparativo de ventas por período.
/app/backend/modules/comercial/inteligencia_comercial_routes.py:241:        SUM(ventas_total) AS ventas_total,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:242:        SUM(ventas_sin_propina) AS ventas_sin_propina,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:247:             THEN SUM(ventas_sin_propina) / SUM(tickets_total) ELSE 0 END AS ticket_promedio,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:249:             THEN SUM(ventas_sin_propina) / SUM(pax_total) ELSE 0 END AS consumo_promedio_pax,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:294:        SUM(ISNULL(VentaCuenta, 0)) AS venta_cuenta,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:296:             THEN SUM(ISNULL(VentaCuenta, 0)) / SUM(ISNULL(NumeroComensales, 0)) ELSE 0 END AS consumo_promedio_pax,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:353:    Tendencia diaria de ventas.
/app/backend/modules/comercial/inteligencia_comercial_routes.py:368:        SUM(ventas_total) AS ventas_total,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:372:             THEN SUM(ventas_total) / SUM(tickets_total) ELSE 0 END AS ticket_promedio
/app/backend/modules/comercial/inteligencia_comercial_routes.py:403:        SUM(ventas_total) AS ventas_total,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:404:        SUM(ventas_sin_propina) AS ventas_sin_propina,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:409:             THEN SUM(ventas_sin_propina) / SUM(tickets_total) ELSE 0 END AS ticket_promedio,
/app/backend/modules/comercial/inteligencia_comercial_routes.py:414:    ORDER BY ventas_total DESC;
/app/backend/modules/comercial/alertas_margen_service.py:393:    precio_venta: Optional[float] = None,
/app/backend/modules/comercial/alertas_margen_service.py:411:        precio_venta: Precio de venta
/app/backend/modules/comercial/alertas_margen_service.py:455:    if precio_venta is not None and costo_receta is not None:
/app/backend/modules/comercial/alertas_margen_service.py:456:        utilidad = precio_venta - costo_receta
/app/backend/modules/comercial/alertas_margen_service.py:458:        costo_mayor_precio = costo_receta > precio_venta
/app/backend/modules/comercial/alertas_margen_service.py:467:    if tiene_alerta and precio_venta and costo_receta:
/app/backend/modules/comercial/alertas_margen_service.py:468:        utilidad_actual = precio_venta - costo_receta
/app/backend/modules/comercial/alertas_margen_service.py:469:        utilidad_esperada = precio_venta * (margen_esperado / 100)
/app/backend/modules/comercial/inteligencia_repository.py:64:                SUM(ventas_total) AS ventas_total,
/app/backend/modules/comercial/inteligencia_repository.py:65:                SUM(ventas_sin_propina) AS ventas_sin_propina,
/app/backend/modules/comercial/inteligencia_repository.py:70:                    THEN SUM(ventas_sin_propina) / SUM(tickets_total)
/app/backend/modules/comercial/inteligencia_repository.py:73:                    THEN SUM(ventas_sin_propina) / SUM(pax_total)
/app/backend/modules/comercial/inteligencia_repository.py:75:                SUM(ventas_cerradas) AS ventas_cerradas,
/app/backend/modules/comercial/inteligencia_repository.py:76:                SUM(ventas_abiertas) AS ventas_abiertas,
/app/backend/modules/comercial/inteligencia_repository.py:112:                SUM(ventas_total) AS ventas_total,
/app/backend/modules/comercial/inteligencia_repository.py:113:                SUM(ventas_sin_propina) AS ventas_sin_propina,
/app/backend/modules/comercial/inteligencia_repository.py:118:                    THEN SUM(ventas_sin_propina) / SUM(tickets_total)
/app/backend/modules/comercial/inteligencia_repository.py:124:            ORDER BY ventas_total DESC
/app/backend/modules/comercial/inteligencia_repository.py:135:        Obtiene tendencia diaria de ventas.
/app/backend/modules/comercial/inteligencia_repository.py:149:                SUM(ventas_total) AS ventas_total,
/app/backend/modules/comercial/inteligencia_repository.py:212:                SUM(ventas_total) AS ventas_total,
/app/backend/modules/comercial/inteligencia_repository.py:223:                SUM(ventas_total) AS ventas_total,
```

## 4. Archivos backend más contaminados
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

## 5. Endpoints HTTP con server_id
```text
/app/backend/modules/comercial/service.py:175:def obtener_unidad_negocio_edarsahub(server_id: str, sucursal: str = None) -> Dict:
/app/backend/modules/comercial/service.py:211:def _obtener_codigo_canonico_mpro(server_id: str, sucursal_id: str, sucursal_nombre: str) -> tuple:
/app/backend/modules/comercial/service.py:494:def _get_ultimo_dia_con_datos_edarsahub(server_id: str, mes: int, anio: int) -> Optional[int]:
/app/backend/modules/comercial/service.py:514:    server_id: str,
/app/backend/modules/comercial/service.py:589:def _get_ventas_abiertas_edarsahub(server_id: str, sucursal_id: str = 'DEFAULT', unidad_negocio_id: str = None) -> Dict:
/app/backend/modules/comercial/service.py:788:    server_id: str,
/app/backend/modules/comercial/service.py:1332:async def obtener_sucursales_servidor(server_id: str) -> List[Dict]:
/app/backend/modules/comercial/service.py:1343:async def obtener_metas(server_id: str, sucursal: str, mes: int, anio: int) -> Dict:
/app/backend/modules/comercial/service.py:1351:async def guardar_metas(server_id: str, sucursal: str, mes: int, anio: int, metas: Dict) -> Dict:
/app/backend/modules/comercial/service.py:2362:    server_id: str,
/app/backend/modules/comercial/service.py:2478:    server_id: str,
/app/backend/modules/comercial/service.py:2595:def _obtener_unidad_ids_desde_servidor(server_id: str) -> List[str]:
/app/backend/modules/comercial/service.py:2618:def get_last_valid_snapshot_edarsahub(server_id: str) -> Dict:
/app/backend/modules/comercial/routes_pricing_ai.py:55:    server_id: str = Field(..., description="UUID del servidor")
/app/backend/modules/comercial/routes_pricing_ai.py:65:    server_id: str = Field(..., description="UUID del servidor")
/app/backend/modules/comercial/routes_pricing_ai.py:74:    server_id: str = Field(..., description="UUID del servidor")
/app/backend/modules/comercial/cache_service.py:79:    server_id: str,
/app/backend/modules/comercial/queries/hub.py:27:    "server_id": str,
/app/backend/modules/comercial/queries/hub.py:96:#     server_id: str,
/app/backend/modules/comercial/queries/hub.py:120:#     server_id: str,
/app/backend/modules/comercial/queries/hub.py:142:#     server_id: str,
/app/backend/modules/comercial/queries/hub.py:161:    server_id: str,
/app/backend/modules/comercial/routes_precios_sugeridos.py:58:    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
/app/backend/modules/comercial/alertas_margen_service.py:163:    server_id: Optional[str] = None,
/app/backend/modules/comercial/alertas_margen_service.py:337:    server_id: Optional[str] = None
/app/backend/modules/comercial/alertas_margen_service.py:397:    server_id: Optional[str] = None
/app/backend/modules/comercial/alertas_margen_repository.py:332:    server_id: Optional[str] = None,
/app/backend/modules/comercial/alertas_margen_repository.py:536:    server_id: Optional[str] = None
/app/backend/modules/comercial/routes_alertas_margen.py:58:    server_id: Optional[str] = None
/app/backend/modules/comercial/routes_alertas_margen.py:84:    server_id: Optional[str] = None
/app/backend/modules/comercial/routes_alertas_margen.py:238:    server_id: Optional[str] = Query(None),
/app/backend/modules/comercial/repository.py:145:def _get_server_by_id_sql(server_id: str) -> Optional[Dict]:
/app/backend/modules/comercial/repository.py:202:async def get_server_by_id(server_id: str) -> Optional[Dict]:
/app/backend/modules/comercial/repository.py:224:async def get_sucursales_visibles_config(server_id: str) -> Dict[str, bool]:
/app/backend/modules/comercial/repository.py:252:async def filtrar_unidades_por_visibilidad(unidades: List[Dict], server_id: str) -> List[Dict]:
/app/backend/modules/comercial/repository.py:283:def _get_sucursal_nombre_sql(server_id: str, sucursal_origen_id: str) -> Optional[str]:
/app/backend/modules/comercial/repository.py:324:async def get_sucursal_nombre(server_id: str, sucursal_origen_id: str, server_name: str = "") -> tuple:
/app/backend/modules/comercial/repository.py:458:async def get_metas_sucursal(server_id: str, sucursal: str, mes: int, anio: int) -> Optional[Dict]:
/app/backend/modules/comercial/repository.py:474:async def save_metas_sucursal(server_id: str, sucursal: str, mes: int, anio: int, metas: Dict) -> None:
/app/backend/modules/comercial/repository.py:516:async def get_cached_kpis(server_id: str, periodo_key: str) -> Optional[Dict]:
/app/backend/modules/comercial/repository.py:533:async def save_kpis_cache(server_id: str, periodo_key: str, kpis: dict) -> None:
/app/backend/modules/comercial/repository.py:559:async def get_cached_kpis_by_prefix(server_id: str, periodo_prefix: str) -> List[Dict]:
/app/backend/modules/comercial/repository.py:577:async def save_server_connection_status(server_id: str, is_online: bool, response_time_ms: int = None) -> None:
/app/backend/modules/comercial/repository.py:601:async def get_server_connection_status(server_id: str) -> Optional[Dict]:
/app/backend/modules/comercial/repository.py:619:async def is_server_recently_offline(server_id: str, minutes_threshold: int = 10) -> bool:
/app/backend/modules/comercial/repository.py:663:async def should_attempt_live_query(server_id: str, data_type: str = "HUB") -> bool:
/app/backend/modules/comercial/repository.py:694:async def save_dashboard_cache(server_id: str, periodo_key: str, dashboard_data: Dict) -> None:
/app/backend/modules/comercial/repository.py:720:async def get_dashboard_cache(server_id: str, periodo_key: str) -> Optional[Dict]:
/app/backend/modules/comercial/historical_kpis_repository.py:228:        WHERE server_id = {_escape_sql_string(server_id)}
/app/backend/modules/comercial/historical_kpis_repository.py:270:            WHERE server_id = {_escape_sql_string(server_id)}
/app/backend/modules/comercial/historical_kpis_repository.py:380:    server_id: str,
/app/backend/modules/comercial/historical_kpis_repository.py:391:    conditions = [f"server_id = {_escape_sql_string(server_id)}"]
/app/backend/modules/comercial/historical_kpis_repository.py:434:    server_id: str = None,
/app/backend/modules/comercial/historical_kpis_repository.py:445:        conditions.append(f"server_id = {_escape_sql_string(server_id)}")
/app/backend/modules/comercial/kpis_repository.py:146:def _build_filter_key(server_id: str, empresa_id: str, sucursal_id: str, fecha: str) -> dict:
/app/backend/modules/comercial/kpis_repository.py:166:    server_id: str,
/app/backend/modules/comercial/kpis_repository.py:367:    server_id: str,
/app/backend/modules/comercial/kpis_repository.py:428:    server_id: str,
/app/backend/modules/comercial/kpis_repository.py:465:    server_id: str,
/app/backend/modules/comercial/services/impuestos_service.py:82:    server_id: str,
/app/backend/modules/comercial/services/impuestos_service.py:259:def get_estado_fiscal_producto(codigo_producto: str, server_id: str) -> Dict[str, Any]:
/app/backend/modules/comercial/services/impuestos_service.py:313:def get_productos_sin_impuesto(server_id: Optional[str] = None, limit: int = 100) -> list:
/app/backend/modules/comercial/services/benchmark_service.py:59:        server_id=str(row.get('ServerID', '')),
/app/backend/modules/comercial/services/benchmark_service.py:211:    server_id: str
/app/backend/modules/comercial/services/benchmark_service.py:615:    server_id: str
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:112:    server_id: str = None,
/app/backend/modules/comercial/services/pricing_ai_service.py:161:def _obtener_datos_producto(codigo_producto: str, server_id: str) -> Dict[str, Any]:
/app/backend/modules/comercial/services/pricing_ai_service.py:365:    server_id: str,
/app/backend/modules/comercial/services/pricing_ai_service.py:597:    server_id: str,
/app/backend/modules/comercial/services/pricing_ai_service.py:913:    server_id: str,
/app/backend/modules/comercial/services/pricing_ai_service.py:1081:    server_id: str,
/app/backend/modules/comercial/services/perfil_unidad_service.py:49:        server_id=str(row.get('ServerID', '')) if row.get('ServerID') else None,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:75:def _obtener_costo_producto(codigo_producto: str, server_id: str) -> Tuple[Optional[float], Optional[str]]:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:138:def _obtener_nombre_producto(codigo_producto: str, server_id: str) -> Optional[str]:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:157:def _es_producto_vino(codigo_producto: str, server_id: str) -> bool:
/app/backend/modules/comercial/services/pricing_sugerido_service.py:498:    server_id: str,
/app/backend/modules/comercial/services/pricing_sugerido_service.py:561:def obtener_estadisticas_calculo(server_id: str, tipo_motor: TipoMotorPrecio = TipoMotorPrecio.COSTO_MARGEN) -> Dict[str, Any]:
/app/backend/modules/comercial/services/precios_vinos_service.py:79:    server_id: str
/app/backend/modules/comercial/services/precios_vinos_service.py:229:def obtener_costo_base_vino(codigo_producto: str, server_id: str) -> Tuple[Optional[float], Optional[str]]:
/app/backend/modules/comercial/services/precios_vinos_service.py:334:def obtener_tasa_impuesto(codigo_producto: str, server_id: str) -> Tuple[Optional[float], Optional[str]]:
/app/backend/modules/comercial/services/precios_vinos_service.py:399:    server_id: str,
/app/backend/modules/comercial/services/precios_vinos_service.py:529:    server_id: Optional[str] = None,
/app/backend/modules/comercial/services/precios_vinos_service.py:583:def get_estadisticas_calculo(server_id: Optional[str] = None) -> Dict[str, int]:
/app/backend/modules/comercial/services/pricing_schemas.py:152:    server_id: Optional[str] = Field(None, description="UUID del servidor")
/app/backend/modules/comercial/services/pricing_schemas.py:188:    server_id: Optional[str] = None
/app/backend/modules/comercial/services/pricing_schemas.py:351:    server_id: str = Field(..., description="UUID del servidor")
/app/backend/modules/comercial/services/pricing_schemas.py:410:    server_id: str = Field(..., description="UUID del servidor")
/app/backend/modules/comercial/services/pricing_schemas.py:444:    server_id: str
/app/backend/modules/comercial/routes.py:229:def check_live_guard_rail(endpoint_base: str, server_id: str = None) -> dict:
/app/backend/modules/comercial/routes.py:299:async def validate_server_access_rbac(current_user: Dict, server_id: str) -> UserAccessContext:
/app/backend/modules/comercial/routes.py:368:def get_ventas_dia_snapshot_from_edarsahub(server_id: str, fecha_operacion: str = None, unidad_negocio_id: str = None) -> Dict:
/app/backend/modules/comercial/routes.py:1913:@router.get("/comercial/sucursales/{server_id}")
/app/backend/modules/comercial/routes.py:1915:    server_id: str,
/app/backend/modules/comercial/routes.py:2014:@router.get("/comercial/metas/{server_id}")
/app/backend/modules/comercial/routes.py:2016:    server_id: str, 
/app/backend/modules/comercial/routes.py:2349:@router.get("/comercial/ticket-perfecto/{server_id}")
/app/backend/modules/comercial/routes.py:2351:    server_id: str, 
/app/backend/modules/comercial/routes.py:2645:@router.get("/comercial/ventas-tiempo/{server_id}")
/app/backend/modules/comercial/routes.py:2647:    server_id: str, 
/app/backend/modules/comercial/routes.py:2807:                """, (server_id, hoy_str))
/app/backend/modules/comercial/routes.py:2869:@router.get("/comercial/mesas/{server_id}")
/app/backend/modules/comercial/routes.py:2871:    server_id: str, 
/app/backend/modules/comercial/routes.py:3241:@router.get("/comercial/detalle-movimientos/{server_id}")
/app/backend/modules/comercial/routes.py:3243:    server_id: str, 
/app/backend/modules/comercial/routes.py:3500:@router.get("/comercial/precios-constantes/{server_id}")
/app/backend/modules/comercial/routes.py:3502:    server_id: str,
/app/backend/modules/comercial/routes.py:4097:@router.get("/comercial/reporte-pax/{server_id}")
/app/backend/modules/comercial/routes.py:4099:    server_id: str, 
/app/backend/modules/comercial/routes.py:4223:@router.get("/comercial/dashboard/{server_id}")
/app/backend/modules/comercial/routes.py:4225:    server_id: str, 
/app/backend/modules/comercial/schemas.py:26:    server_id: Optional[str] = None
/app/backend/modules/comercial/schemas.py:69:    server_id: str
/app/backend/modules/fase2_operativo/sql_repository.py:96:    server_id: str,
/app/backend/modules/fase2_operativo/sql_repository.py:124:    server_id: str,
/app/backend/modules/fase2_operativo/sql_repository.py:396:    server_id: str,
/app/backend/modules/fase2_operativo/sql_repository.py:519:async def obtener_config_asignacion(server_id: str, almacen_id: str) -> Optional[Dict]:
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:73:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:104:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:116:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:128:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:140:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:152:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:228:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/workflow_repository.py:270:        server_ids: Optional[List[str]] = None,
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:35:        server_id: str,
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:83:        server_id: str,
/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py:114:    async def get_todas_asignaciones(self, server_id: Optional[str] = None) -> List[Dict]:
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:143:    async def get_vencidas(self, server_ids: Optional[List[str]] = None) -> List[Dict]:
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:252:    async def contar_por_estado(self, server_ids: Optional[List[str]] = None) -> Dict[str, int]:
/app/backend/modules/fase2_operativo/repositories/tarea_repository.py:323:        server_ids: List[str],
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:191:        server_ids: Optional[List[str]] = None,
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:252:        server_ids: Optional[List[str]] = None
/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py:377:        server_ids: Optional[List[str]] = None,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:56:        server_id: str,
/app/backend/modules/fase2_operativo/services/orquestador_service.py:271:        server_id: str,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:97:        server_id: str,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:445:        server_id: Optional[str] = None,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:467:    def obtener_kpis(self, server_id: Optional[str] = None) -> Dict:
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:593:        server_id: str,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:611:        server_id: str,
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:632:    def _marcar_pedido_procesado(self, server_id: str, pedido_folio: str, origen: str, automatizacion_id: str):
/app/backend/modules/fase2_operativo/services/operativo_service.py:360:    async def obtener_resumen_dashboard(self, server_ids: Optional[List[str]] = None) -> Dict[str, Any]:
/app/backend/modules/fase2_operativo/services/operativo_service.py:402:    async def obtener_alertas_activas(self, server_ids: Optional[List[str]] = None) -> List[Dict]:
/app/backend/modules/fase2_operativo/services/tarea_service.py:304:    async def obtener_tareas_vencidas(self, server_ids: Optional[List[str]] = None) -> List[Dict]:
/app/backend/modules/fase2_operativo/services/tarea_service.py:329:    async def resumen_por_estado(self, server_ids: Optional[List[str]] = None) -> Dict[str, int]:
/app/backend/modules/fase2_operativo/services/workflow_service.py:278:    async def listar_escalados(self, limit: int = 100, server_ids: Optional[List[str]] = None) -> List[Dict]:
/app/backend/modules/fase2_operativo/services/workflow_service.py:282:    async def resumen_por_estado(self, server_ids: Optional[List[str]] = None) -> Dict[str, int]:
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:33:    server_id: str
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:297:    server_id: Optional[str] = Query(None),
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:309:    server_id: Optional[str] = Query(None),
/app/backend/modules/fase2_operativo/routes/workflow_routes.py:41:async def get_user_server_ids(current_user: Dict[str, Any]) -> list:
/app/backend/modules/fase2_operativo/routes/dashboard_routes.py:31:async def get_user_server_ids(current_user: Dict[str, Any]) -> list:
/app/backend/modules/costos_margenes/schemas_precios.py:53:    server_id: str = Field(..., description="ID del servidor")
/app/backend/modules/costos_margenes/schemas_precios.py:64:    server_id: str
/app/backend/modules/costos_margenes/schemas_precios.py:100:    server_id: str = Field(..., description="ID del servidor")
/app/backend/modules/costos_margenes/schemas_precios.py:123:    server_id: str
/app/backend/modules/costos_margenes/repository.py:322:def get_receta_producto(producto_id: str, server_id: Optional[str] = None) -> Tuple[Dict, List[Dict]]:
/app/backend/modules/costos_margenes/repository.py:409:def get_receta_elaborado(codigo_elaborado: str, server_id: Optional[str] = None) -> Tuple[Optional[Dict], List[Dict]]:
/app/backend/modules/costos_margenes/repository.py:542:def get_insumos_producto(producto_id: str, server_id: Optional[str] = None) -> Tuple[Dict, List[Dict]]:
/app/backend/modules/costos_margenes/routes_precios.py:291:    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
/app/backend/modules/costos_margenes/routes.py:351:    server_id: Optional[str] = Query(None, description="ServerID para búsqueda por código fuente"),
/app/backend/modules/costos_margenes/routes.py:444:    server_id: Optional[str] = Query(None, description="ServerID para búsqueda por código fuente"),
/app/backend/modules/costos_margenes/repository_precios.py:70:    server_id: str
/app/backend/modules/costos_margenes/repository_precios.py:114:        'server_id': str(r['ServerID']),
/app/backend/modules/costos_margenes/repository_precios.py:190:    server_id: str,
/app/backend/modules/costos_margenes/repository_precios.py:254:    server_id: str,
/app/backend/modules/costos_margenes/repository_precios.py:364:    server_id: Optional[str] = None,
/app/backend/modules/costos_margenes/repository_precios.py:573:        'server_id': str(r['ServerID']),
/app/backend/modules/costos_margenes/schemas.py:78:    server_id: str
/app/backend/modules/costos_margenes/schemas.py:162:    server_id: str
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py:339:        server_id: str,
/app/backend/modules/inventarios/repository.py:17:def get_inventarios_fisicos(server_id: str = None, almacen: str = None, 
/app/backend/modules/inventarios/repository.py:49:def get_inventario_by_folio(folio: str, server_id: str = None) -> Optional[Dict]:
/app/backend/modules/inventarios/repository.py:68:def get_inventarios_count_by_server(server_id: str) -> int:
/app/backend/modules/inventarios/repository.py:85:    def get_all(server_id: str = None, **filters) -> List[Dict]:
/app/backend/modules/inventarios/repository.py:89:    def get_by_folio(folio: str, server_id: str = None) -> Optional[Dict]:
/app/backend/modules/sync_historicos/repository.py:491:    def get_ultimo_sync(self, server_id: str, sync_type: str) -> Optional[Dict]:
/app/backend/modules/sync_historicos/models.py:54:    server_id: str
/app/backend/modules/sync_historicos/models.py:113:    server_id: str
/app/backend/modules/sync_historicos/models.py:167:    server_id: str
/app/backend/modules/sync_historicos/models.py:214:    server_id: Optional[str]  # None si es todos
/app/backend/modules/sync_historicos/models.py:251:    server_ids: Optional[List[str]] = None  # None = todos
/app/backend/modules/sync_historicos/sync_ventas.py:29:    server_ids: Optional[List[str]] = None,
/app/backend/modules/sync_historicos/sync_ventas.py:68:    server_ids: List[str],  # OBLIGATORIO especificar servidores
/app/backend/modules/sync_historicos/sync_ventas.py:207:    server_ids: Optional[List[str]] = None,
/app/backend/modules/sync_historicos/sync_ventas.py:234:    server_ids: List[str],
/app/backend/modules/sync_historicos/sync_ventas.py:268:    server_ids: Optional[List[str]] = None,
/app/backend/modules/sync_historicos/sync_ventas.py:295:    server_ids: List[str],
/app/backend/modules/automatizacion/repository.py:43:    server_id: Optional[str] = None
/app/backend/modules/automatizacion/repository.py:94:    server_id: str
/app/backend/modules/automatizacion/repository.py:140:    server_id: str,
/app/backend/modules/automatizacion/repository.py:169:    server_id: str,
/app/backend/modules/automatizacion/repository.py:221:    server_id: str,
/app/backend/modules/automatizacion/repository.py:253:    server_id: str,
/app/backend/modules/automatizacion/repository.py:382:    server_id: str,
/app/backend/modules/automatizacion/repository.py:676:    server_id: str,
/app/backend/modules/automatizacion/schemas.py:39:    server_id: str = Field(..., max_length=50)
/app/backend/modules/automatizacion/schemas.py:71:    server_id: str = Field(..., max_length=50)
/app/backend/modules/automatizacion/schemas.py:112:    server_id: str = Field(..., max_length=50)
/app/backend/modules/automatizacion/schemas.py:216:    server_id: str = Field(..., max_length=50)
/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py:61:def get_server_connection_config(server_id: str) -> Optional[Dict[str, Any]]:
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:133:    server_id: str
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:177:def get_server_connection(server_id: str) -> Optional[Dict[str, Any]]:
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:117:            server_id=str(row['server_id']),  # Convertir UUID a string
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py:127:def get_sucursales_mpro(server_id: str) -> List[Dict[str, str]]:
/app/backend/modules/comercial_v2/mappers.py:33:    server_id: str,
/app/backend/modules/comercial_v2/mappers.py:52:    server_id: str,
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:225:def get_server_connection(server_id: str) -> Optional[Dict[str, Any]]:
/app/backend/modules/comercial_v2/schemas.py:62:    server_id: str
/app/backend/modules/comercial_v2/schemas.py:85:    server_id: str
/app/backend/modules/comercial_v2/schemas.py:107:    server_id: str
/app/backend/modules/comercial_v2/schemas.py:155:    server_id: str
/app/backend/modules/comercial_v2/schemas.py:190:    server_id: Optional[str] = None
/app/backend/modules/comercial_v2/schemas.py:221:    server_id: str
/app/backend/modules/universal_query/routes.py:160:async def get_server_and_validate(server_id: str, db=None) -> Dict:
/app/backend/modules/universal_query/routes.py:232:@router.post("/servers/{server_id}/universal-query-test")
/app/backend/modules/universal_query/routes.py:234:    server_id: str,
/app/backend/modules/sync_recetas/models.py:15:    server_ids: List[str]
/app/backend/modules/sync_recetas/sync_recetas.py:41:    server_ids: List[str] = None,
/app/backend/modules/sync_recetas/sync_recetas.py:65:    server_ids: List[str],
/app/backend/modules/sync_recetas/sync_recetas.py:245:    server_id: str,
/app/backend/modules/sync_recetas/sync_recetas.py:502:    server_id: str,
/app/backend/modules/sync_recetas/sync_recetas.py:796:def _guardar_familias(server_id: str, system_type: str, familias: List[FamiliaSync], 
/app/backend/modules/sync_recetas/sync_recetas.py:843:def _guardar_subfamilias(server_id: str, system_type: str, subfamilias: List[SubFamiliaSync],
/app/backend/modules/sync_recetas/sync_recetas.py:887:def _guardar_insumos(server_id: str, system_type: str, insumos: List[InsumoSync],
/app/backend/modules/sync_recetas/sync_recetas.py:946:def _guardar_productos(server_id: str, system_type: str, productos: List[ProductoSync],
/app/backend/modules/sync_recetas/sync_recetas.py:1007:def _guardar_recetas(server_id: str, system_type: str, recetas: List[RecetaLineaSync],
/app/backend/modules/sync_recetas/sync_recetas.py:1100:def _guardar_elaborados(server_id: str, system_type: str, elaborados: List[ElaboradoLineaSync],
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:897:    def resolver_server_id_a_unidad(self, server_id: str) -> Optional[Dict]:
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:972:    def listar_cuadres_z_por_server_id(self, server_id: str, filtros: Dict = None) -> List[Dict]:
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py:1038:    def obtener_resumen_por_server_id(self, server_id: str, filtros: Dict = None) -> Dict:
/app/backend/modules/finanzas/tesoreria.py:99:    server_id: Optional[str] = Query(None, description="Filtrar por server_id (UUID)"),
/app/backend/modules/finanzas/tesoreria.py:289:    server_id: Optional[str] = Query(None, description="Filtrar por server_id (UUID de unidad de negocio)"),
/app/backend/modules/finanzas/tesoreria.py:350:    server_id: Optional[str] = Query(None, description="Filtrar por server_id (UUID de unidad de negocio)"),
/app/backend/modules/finanzas/sync_propinas_mpro.py:149:            'server_id': str(unidad['server_id']),
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:150:            'server_id': str(unidad['server_id']),
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py:531:    server_id: str,
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py:157:            'server_id': str(unidad['server_id']),
/app/backend/modules/finanzas/health.py:106:async def check_server_connectivity(server_id: str, server_name: str, system_type: str) -> Dict[str, Any]:
/app/backend/modules/finanzas/health.py:425:@router.get("/servers/{server_id}")
/app/backend/modules/finanzas/health.py:427:    server_id: str,
/app/backend/modules/finanzas/repository_cortes_z.py:38:    async def _get_server_config(self, server_id: str) -> Optional[Dict]:
/app/backend/modules/finanzas/repository_cortes_z.py:57:                self.logger.warning(f"Servidor {server_id} no encontrado en registry")
/app/backend/modules/finanzas/repository_cortes_z.py:67:        server_id: str,
/app/backend/modules/finanzas/repository_cortes_z.py:72:        Ejecuta una query usando el server_id para obtener configuración del registry.
/app/backend/modules/finanzas/repository_cortes_z.py:91:                error_message=f"Servidor {server_id} no encontrado en registry centralizado"
/app/backend/modules/finanzas/repository_cortes_z.py:150:        server_id: str,
/app/backend/modules/finanzas/repository_cortes_z.py:199:        server_id: str,
/app/backend/modules/finanzas/repository_cortes_z.py:310:        server_id: str,
/app/backend/modules/finanzas/repository_cortes_z.py:408:        server_ids: List[str],
/app/backend/modules/finanzas/repository_cortes_z.py:578:    async def _find_server_id_by_name(self, name: str) -> Optional[str]:
/app/backend/modules/finanzas/repository_cortes_z.py:601:    async def _get_active_server_ids(self) -> List[str]:
/app/backend/modules/finanzas/historical_kpis_repository.py:61:    server_id: str,
/app/backend/modules/finanzas/propinas_tpv/service.py:53:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/service.py:237:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/service.py:326:        server_id: Optional[str] = None
/app/backend/modules/finanzas/propinas_tpv/service.py:359:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:54:def _get_server_from_registry(server_id: str) -> Optional[Dict]:
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:246:    server_id: Optional[str] = Query(None),
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:271:    server_id: Optional[str] = Query(None),
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:306:    server_id: Optional[str] = Query(None),
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:464:    server_id: str,
/app/backend/modules/finanzas/propinas_tpv/routes_sql.py:567:    server_id: Optional[str] = Query(None),
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:300:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:362:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:517:        server_id: Optional[str] = None
/app/backend/modules/finanzas/propinas_tpv/sql_repository.py:576:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:122:        server_id: Optional[str],
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:165:        server_id: Optional[str],
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:222:        server_id: Optional[str]
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:253:        server_id: Optional[str],
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:326:        server_id: Optional[str],
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:354:        server_id: Optional[str],
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:386:    async def invalidar_listados(self, server_id: Optional[str] = None):
/app/backend/modules/finanzas/propinas_tpv/cache_manager.py:404:    async def invalidar_resumenes(self, server_id: Optional[str] = None):
/app/backend/modules/finanzas/propinas_tpv/repository.py:451:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/repository.py:485:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/repository.py:566:        server_id: Optional[str] = None
/app/backend/modules/finanzas/propinas_tpv/repository.py:623:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:133:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:331:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:423:        server_id: Optional[str] = None
/app/backend/modules/finanzas/propinas_tpv/service_sql.py:529:        server_id: Optional[str] = None,
/app/backend/modules/finanzas/propinas_tpv/routes.py:57:def _get_server_from_registry(server_id: str) -> Optional[Dict]:
/app/backend/modules/finanzas/propinas_tpv/routes.py:129:async def get_user_server_ids_permitidos(current_user: Dict[str, Any]) -> List[str]:
/app/backend/modules/finanzas/propinas_tpv/routes.py:280:    server_id: str,
/app/backend/modules/finanzas/propinas_tpv/routes.py:409:    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
/app/backend/modules/finanzas/propinas_tpv/routes.py:479:    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
/app/backend/modules/finanzas/propinas_tpv/routes.py:504:    server_id: Optional[str] = Query(None, description="Filtrar por servidor"),
/app/backend/modules/finanzas/propinas_tpv/routes.py:557:    server_id: Optional[str] = Query(None),
/app/backend/modules/finanzas/propinas_tpv/models.py:112:    server_id: str = Field(..., description="ID del servidor en EDARSA HUB")
/app/backend/modules/finanzas/propinas_tpv/models.py:158:    server_id: Optional[str] = Field(None)
/app/backend/modules/finanzas/propinas_tpv/models.py:219:    server_id: Optional[str] = Field(None, description="Filtrar por servidor específico")
/app/backend/modules/finanzas/test_conn_cienfuegos.py:213:                    'server_id': str(row['server_id']) if row['server_id'] else None,
/app/backend/modules/finanzas/test_conn_cienfuegos.py:256:        server_id = str(unidad_row['server_id'])
/app/backend/modules/finanzas/test_conn_cienfuegos.py:287:                    'server_id': str(server_row['id']),
/app/backend/modules/finanzas/test_conn_cienfuegos.py:959:def test_11_edarsahub_sync_status(unidad_negocio_id: str, server_id: str) -> DiagnosticResult:
/app/backend/modules/finanzas/sync_cortes_mpro.py:137:            'server_id': str(unidad['server_id']),
/app/backend/modules/finanzas/sync_cortes_mpro.py:464:    server_id: str,
/app/backend/modules/finanzas/repository_cortes_caja_edarsahub.py:154:        server_id: str,
```
