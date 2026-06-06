# AUDITORÍA ORIGEN COMPRAS / ENTRADAS
Fecha: Thu Jun  4 04:39:08 UTC 2026

## 1. Queries SoftRestaurant relacionadas con compras/entradas
```text
/app/backend/modules/comercial/routes_pricing_ai.py:343:    - Datos de entrada utilizados
/app/backend/modules/comercial/routes_pricing_ai.py:381:        "proveedor": "OpenAI via Emergent LLM Key",
/app/backend/modules/comercial/cache_service.py:350:    Limpia entradas de cache expiradas.
/app/backend/modules/comercial/cache_service.py:379:        logging.info(f"Cache cleanup: {deleted_count} entradas eliminadas (antes: {total_before}, después: {total_after})")
/app/backend/modules/comercial/queries/mpro.py:88:    'Proveedor',
/app/backend/modules/comercial/queries/softrestaurant.py:67:    'compras',
/app/backend/modules/comercial/queries/softrestaurant.py:68:    'comprasmovtos',
/app/backend/modules/comercial/crm_router.py:10:# MODELOS PYDANTIC (Validación de Entrada)
/app/backend/modules/comercial/rentabilidad.py:38:            FROM dbo.Compras_Inventarios_Fisicos_Sync
/app/backend/modules/comercial/services/pricing_ai_service.py:18:PROVEEDOR IA:
/app/backend/modules/comercial/services/pricing_ai_service.py:131:            DatosEntradaJSON NVARCHAR(MAX) NULL,
/app/backend/modules/comercial/services/pricing_ai_service.py:372:    datos_entrada_json: Dict,
/app/backend/modules/comercial/services/pricing_ai_service.py:412:    datos_entrada_str = json.dumps(datos_entrada_json, ensure_ascii=False).replace("'", "''")
/app/backend/modules/comercial/services/pricing_ai_service.py:431:        DatosEntradaJSON,
/app/backend/modules/comercial/services/pricing_ai_service.py:458:        N'{datos_entrada_str}',
/app/backend/modules/comercial/services/pricing_ai_service.py:506:        DatosEntradaJSON,
/app/backend/modules/comercial/services/pricing_ai_service.py:533:    datos_entrada = None
/app/backend/modules/comercial/services/pricing_ai_service.py:539:        if row.get('DatosEntradaJSON'):
/app/backend/modules/comercial/services/pricing_ai_service.py:540:            datos_entrada = json.loads(row['DatosEntradaJSON'])
/app/backend/modules/comercial/services/pricing_ai_service.py:573:        'datos_entrada': datos_entrada,
/app/backend/modules/comercial/services/pricing_ai_service.py:686:    # 6. Preparar datos de entrada para IA
/app/backend/modules/comercial/services/pricing_ai_service.py:687:    datos_entrada = {
/app/backend/modules/comercial/services/pricing_ai_service.py:831:            datos_entrada_json=datos_entrada,
/app/backend/modules/comercial/services/pricing_ai_service.py:886:            datos_entrada_json=datos_entrada,
/app/backend/modules/comercial/services/pricing_ai_service.py:1036:            datos_entrada_json={
/app/backend/modules/comercial/services/pricing_ai_service.py:1188:            datos_entrada_json={
/app/backend/modules/comercial/services/pricing_ai_service.py:1407:            datos_entrada_json={
/app/backend/modules/comercial/services/precios_vinos_service.py:31:    6-9. Fuentes adicionales (futuro: compras, proveedor, override)
/app/backend/modules/comercial/services/precios_vinos_service.py:239:    6-9. Fuentes adicionales (futuro: compras, proveedor, override)
/app/backend/modules/comercial/services/precios_vinos_service.py:299:    # Jerarquías 6-9: Futuras fuentes (compras, proveedor, override)
/app/backend/modules/comercial/routes.py:1677:    # Construir mapa de server_id → codigo para resolver entradas con código vacío
/app/backend/modules/comercial/routes.py:1718:    # Prioridad de estados para elegir la mejor entrada
/app/backend/modules/comercial/routes.py:1740:                # La nueva entrada tiene mejor estado → reemplazar
/app/backend/modules/comercial/routes.py:1741:                logging.info(f"[P1-DEDUP] Reemplazando entrada: {codigo_key} ({existente.get('data_status')} → {unidad.get('data_status')})")
/app/backend/modules/comercial/routes.py:1747:                    logging.info(f"[P1-DEDUP] Descartando entrada duplicada con error: {codigo_key}")
/app/backend/modules/comercial/routes.py:1798:                # Crear entrada para esta unidad desde SQL
/app/backend/modules/comercial/routes.py:2432:                "promedio_entradas": float(row.get("PromedioEntradas") or 0),
/app/backend/modules/comercial/routes.py:2521:                        "con_entrada": con_alimentos,
/app/backend/modules/comercial/routes.py:2522:                        "pct_entrada": round((con_alimentos / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
/app/backend/modules/comercial/routes.py:2553:                            "con_entrada": 0, "pct_entrada": 0,
/app/backend/modules/hub/modulo_financiero_proyectos.py:31:            # Transacciones financieras vinculadas al proyecto (Ingresos, Compras, Gastos)
/app/backend/modules/hub/modulo_financiero_proyectos.py:46:    # INYECCIÓN DE FLUJOS (COMPRAS, GASTOS E INGRESOS)
/app/backend/modules/hub/modulo_financiero_proyectos.py:106:                "costo_compras_insumos": totales["COMPRA_INSUMO"],
/app/backend/modules/fase2_operativo/router.py:21:from .routes.automatizacion_compras_routes import router as automatizacion_compras_router
/app/backend/modules/fase2_operativo/router.py:111:    automatizacion_compras_router,
/app/backend/modules/fase2_operativo/repositories/cargos_repository.py:452:        Registra una entrada en el log de auditoría.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:43:    "tareas_operativas_compras": "Operativo_TareasCompras",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:44:    "auditoria_compras_bitacora": "Operativo_BitacoraCompras",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:53:    # FASE B-P2-B: Automatización Compras
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:54:    "automatizaciones_operativas_compras": "Operativo_TareasCompras",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:55:    "automatizaciones_bitacora": "Operativo_BitacoraCompras",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:57:    "inventarios_fisicos_procesados": "Compras_Inventarios_Fisicos_Sync",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:730:            "Operativo_TareasCompras": "TareaID",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:731:            "Operativo_BitacoraCompras": "BitacoraID",
/app/backend/modules/fase2_operativo/api_schemas.py:5:Define los modelos Pydantic para validación de entradas y salidas HTTP.
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:2:EDARSA HUB - Automatización Operativa de Compras
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:15:- Operativo_TareasCompras (automatizaciones principales)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:16:- Operativo_BitacoraCompras (bitácora de acciones)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:65:class AutomatizacionComprasService:
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:67:    Servicio de automatización operativa de compras.
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:84:        self._repo = SQLBaseRepository("automatizaciones_operativas_compras")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:88:        logger.info("[AUTO_COMPRAS] Inicializado con SQL → Operativo_TareasCompras")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:682:            manual_id = trigger_generar_manual_sync(self.db, automatizacion_id, modulo="compras")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:694:def get_automatizacion_compras_service(db=None) -> AutomatizacionComprasService:
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:696:    return AutomatizacionComprasService(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:2:EDARSA HUB - Routes de Automatización Operativa de Compras
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:19:from modules.fase2_operativo.services.automatizacion_compras_service import (
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:20:    get_automatizacion_compras_service,
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:83:@router.post("/compras/detector/ejecutar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:126:@router.get("/compras/detector/estado")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:167:@router.get("/compras/tareas")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:188:    tareas = list(db.tareas_operativas_compras.find(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:199:@router.get("/compras/tareas/{tarea_id}")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:208:    tarea = db.tareas_operativas_compras.find_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:219:@router.post("/compras/tareas/{tarea_id}/completar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:235:    tarea = db.tareas_operativas_compras.find_one({"id": tarea_id})
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:244:    db.tareas_operativas_compras.update_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:259:@router.post("/compras/tareas/{tarea_id}/asignar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:271:    tarea = db.tareas_operativas_compras.find_one({"id": tarea_id})
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:277:    db.tareas_operativas_compras.update_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:295:@router.get("/compras/kpis")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:303:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:307:@router.get("/compras")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:318:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:326:@router.get("/compras/detector/bitacora")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:339:    bitacora = list(db.auditoria_compras_bitacora.find(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:350:@router.get("/compras/pedidos-procesados")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:386:@router.get("/compras/{automatizacion_id}")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:394:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:403:@router.post("/compras/procesar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:414:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:437:@router.post("/compras/{automatizacion_id}/gerencia")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:451:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:476:@router.post("/compras/{automatizacion_id}/tesoreria")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:489:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:513:@router.post("/compras/{automatizacion_id}/dias-objetivo")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:525:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:548:@router.post("/compras/{automatizacion_id}/parametros-consumo")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:575:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:596:@router.get("/compras/{automatizacion_id}/bitacora")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:604:    service = get_automatizacion_compras_service(db)
/app/backend/modules/api_connections/routes.py:75:    tipo_uso: str = Field("Otro", description="Tipo de uso: Ventas del día, Inventario, Cortes, Compras, Otro")
/app/backend/modules/api_connections/universal_test_routes.py:25:- Módulos: Comercial, Tablero, KPIs, Inventarios, Compras, Finanzas, Operaciones
/app/backend/modules/corporate_filters/router.py:298:        "proveedores": [],
/app/backend/modules/corporate_filters/router.py:310:        "proveedores": ["empresas"],
/app/backend/modules/corporate_filters/router.py:349:        filters["proveedores"] = get_optional_catalog(
/app/backend/modules/corporate_filters/router.py:350:            ["Proveedor_Catalogo", "Compras_Proveedores", "Proveedores"],
/app/backend/modules/corporate_filters/router.py:351:            ["id_proveedor", "proveedor_id", "ProveedorID", "id"],
/app/backend/modules/corporate_filters/router.py:352:            ["nombre", "razon_social", "nombre_comercial", "Proveedor"],
/app/backend/modules/costos_margenes/repository_precios.py:626:    """Registra una entrada en el historial de la solicitud."""
/app/backend/modules/proveedores/service.py:2:EDARSA HUB - Proveedores Service
/app/backend/modules/proveedores/service.py:4:Lógica de negocio de proveedores.
/app/backend/modules/proveedores/service.py:7:class ProveedoresService:
/app/backend/modules/proveedores/__init__.py:1:# EDARSA HUB - Módulo de Proveedores
/app/backend/modules/proveedores/__init__.py:2:# Portal de proveedores, facturas, pagos y estados de cuenta
/app/backend/modules/proveedores/repository.py:2:EDARSA HUB - Proveedores Repository
/app/backend/modules/proveedores/repository.py:4:Acceso a datos de proveedores.
/app/backend/modules/proveedores/repository.py:7:class ProveedoresRepository:
/app/backend/modules/proveedores/routes.py:2:EDARSA HUB - Proveedores Routes
/app/backend/modules/proveedores/routes.py:4:Endpoints del portal de proveedores.
/app/backend/modules/proveedores/routes.py:6:NOTA: Los endpoints actuales están en routes/portal_proveedores.py y server.py.
/app/backend/modules/proveedores/routes.py:12:router = APIRouter(prefix="/proveedores", tags=["Proveedores"])
/app/backend/modules/proveedores/routes.py:14:# Endpoints a migrar desde portal_proveedores.py
/app/backend/modules/proveedores/schemas.py:2:EDARSA HUB - Proveedores Schemas
/app/backend/modules/proveedores/schemas.py:4:Modelos Pydantic para proveedores.
/app/backend/modules/rh/service.py:865:    - NO se validan duplicados de entrada/salida en el mismo día
/app/backend/modules/rh/service.py:919:        Registra una entrada o salida.
/app/backend/modules/rh/service.py:922:        - NO se validan duplicados de entrada/salida en el mismo día
/app/backend/modules/rh/service.py:923:        - El tipo_registro ya fue validado por Pydantic (Entrada/Salida)
/app/backend/modules/rh/importador/aprobacion_service.py:607:    """Registra una entrada en la bitácora de importación."""
/app/backend/modules/rh/importador/repository.py:553:    Actualiza métricas de una entrada en la bitácora.
/app/backend/modules/rh/importador/routes.py:314:    # Crear entrada en bitácora
/app/backend/modules/rh/repository.py:1236:# - NO se validan duplicados de entrada/salida por día
/app/backend/modules/rh/repository.py:1340:    Registra una entrada o salida en el reloj checador.
/app/backend/modules/rh/repository.py:1345:    - NO se validan duplicados de entrada/salida en el mismo día
/app/backend/modules/rh/routes.py:557:# - NO se validan duplicados de entrada/salida en el mismo día
/app/backend/modules/rh/routes.py:612:    Registra una entrada o salida.
/app/backend/modules/rh/routes.py:616:    - tipo_registro: "Entrada" o "Salida" (validado)
/app/backend/modules/rh/routes.py:622:    - NO se validan duplicados de entrada/salida en el mismo día
/app/backend/modules/rh/schemas.py:535:# - Solo se permiten valores "Entrada" y "Salida"
/app/backend/modules/rh/schemas.py:536:# - NO se agregan validaciones de duplicados de entrada/salida por día
/app/backend/modules/rh/schemas.py:544:TIPOS_REGISTRO_ASISTENCIA = ["Entrada", "Salida"]
/app/backend/modules/rh/schemas.py:550:    tipo_registro: str = Field(..., description="Tipo de registro: Entrada o Salida")
/app/backend/modules/rh/schemas.py:556:        """Valida que tipo_registro sea 'Entrada' o 'Salida'."""
/app/backend/modules/rh/schemas.py:564:    Modelo para registrar entrada o salida.
/app/backend/modules/rh/schemas.py:567:    - NO se validan duplicados de entrada/salida en el mismo día
/app/backend/modules/inventarios/repository.py:9:- Datos sincronizados en tabla Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:26:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:56:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:74:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/consultas_sql/schemas.py:24:    modulo: Optional[str] = Field(None, description="Módulo: Ventas, Compras, etc.")
/app/backend/modules/catalogos/__init__.py:10:- Acceso contextual desde módulos nativos (RH, Compras, etc.)
/app/backend/modules/catalogos/__init__.py:16:- Compras (Estatus órdenes, recepciones, etc.)
/app/backend/modules/catalogos/routes.py:508:    (Generales, RH, Nómina, Compras, etc.) con información de cada catálogo.
/app/backend/modules/catalogos/schemas.py:27:            {"tabla": "Proveedor_Monedas", "nombre": "Monedas", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:58:    "compras": {
/app/backend/modules/catalogos/schemas.py:59:        "nombre": "Compras",
/app/backend/modules/catalogos/schemas.py:60:        "descripcion": "Catálogos del módulo de Compras",
/app/backend/modules/catalogos/schemas.py:63:            {"tabla": "Compras_Estatus", "nombre": "Estatus de Compras", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:64:            {"tabla": "Compras_OrdenesEstatus", "nombre": "Estatus de Órdenes", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:65:            {"tabla": "Compras_PedidosEstatus", "nombre": "Estatus de Pedidos", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:66:            {"tabla": "Compras_RecepcionesEstatus", "nombre": "Estatus de Recepciones", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:67:            {"tabla": "Compras_DocumentosFiscalesEstatus", "nombre": "Estatus Docs. Fiscales", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:68:            {"tabla": "Compras_ConciliacionSATEstatus", "nombre": "Estatus Conciliación SAT", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:69:            {"tabla": "Proveedor_TipoProveedor", "nombre": "Tipos de Proveedor", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:70:            {"tabla": "Proveedor_TipoContacto", "nombre": "Tipos de Contacto", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:71:            {"tabla": "Proveedor_TipoDocumento", "nombre": "Tipos de Documento", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:72:            {"tabla": "Proveedor_EstatusProveedor", "nombre": "Estatus de Proveedor", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:195:    "Proveedor_Monedas": {
/app/backend/modules/catalogos/schemas.py:248:        "campos": ["TurnoID", "CodigoTurno", "Descripcion", "HoraEntrada", "HoraSalida", "ToleranciaMinutos", "Activo"],
/app/backend/modules/catalogos/schemas.py:249:        "campos_editables": ["CodigoTurno", "Descripcion", "HoraEntrada", "HoraSalida", "ToleranciaMinutos", "Activo"],
/app/backend/modules/catalogos/schemas.py:305:    # === COMPRAS / PROVEEDOR ===
/app/backend/modules/catalogos/schemas.py:306:    "Compras_Estatus": {
/app/backend/modules/catalogos/schemas.py:313:    "Compras_OrdenesEstatus": {
/app/backend/modules/catalogos/schemas.py:320:    "Compras_PedidosEstatus": {
/app/backend/modules/catalogos/schemas.py:327:    "Compras_RecepcionesEstatus": {
/app/backend/modules/catalogos/schemas.py:334:    "Compras_DocumentosFiscalesEstatus": {
/app/backend/modules/catalogos/schemas.py:341:    "Compras_ConciliacionSATEstatus": {
/app/backend/modules/catalogos/schemas.py:348:    "Proveedor_TipoProveedor": {
/app/backend/modules/catalogos/schemas.py:349:        "pk": "TipoProveedorID",
/app/backend/modules/catalogos/schemas.py:350:        "campos": ["TipoProveedorID", "Descripcion", "Activo"],
/app/backend/modules/catalogos/schemas.py:355:    "Proveedor_TipoContacto": {
/app/backend/modules/catalogos/schemas.py:362:    "Proveedor_TipoDocumento": {
/app/backend/modules/catalogos/schemas.py:369:    "Proveedor_EstatusProveedor": {
/app/backend/modules/catalogos/schemas.py:370:        "pk": "EstatusProveedorID",
/app/backend/modules/catalogos/schemas.py:371:        "campos": ["EstatusProveedorID", "Descripcion", "Activo"],
/app/backend/modules/catalogos/schemas.py:497:        "campos": ["ConfiguracionTPVID", "SucursalID", "ProveedorTPV", "ComisionDebito", "ComisionCredito", "ComisionAmex", "ComisionInternacional", "AplicaIVAComision", "PorcentajeIVA", "DiasDepositoDebito", "DiasDepositoCredito", "DiasDepositoAmex", "DiasDepositoInternacional", "DiasDepositoEfectivo", "EfectivoFinDeSemanaLunes", "CuentaBancariaID", "NumeroAfiliacion", "TerminalID", "Activo"],
/app/backend/modules/catalogos/schemas.py:498:        "campos_editables": ["SucursalID", "ProveedorTPV", "ComisionDebito", "ComisionCredito", "ComisionAmex", "ComisionInternacional", "AplicaIVAComision", "PorcentajeIVA", "DiasDepositoDebito", "DiasDepositoCredito", "DiasDepositoAmex", "DiasDepositoInternacional", "DiasDepositoEfectivo", "EfectivoFinDeSemanaLunes", "CuentaBancariaID", "NumeroAfiliacion", "TerminalID", "Activo"],
/app/backend/modules/catalogos/schemas.py:499:        "campo_nombre": "ProveedorTPV",
/app/backend/modules/edge/motor_reglas_comerciales.py:100:                        "argumento_script": f"¡Alerta de estancamiento! Ofrece inmediatamente {row['nombre']} como entrada de alta velocidad."
/app/backend/modules/auth/routes.py:502:        'compras': (
/app/backend/modules/auth/routes.py:505:            'COMPRAS_DASHBOARD_VER' in context.permisos
/app/backend/modules/auth/schemas.py:114:    {"id": "compras", "nombre": "Compras", "descripcion": "Dashboard de compras, autorización, análisis"},
/app/backend/modules/auth/schemas.py:140:        "permisos": ["tablero_ejecutivo", "comercial", "compras", "inventarios", "dashboard_inventarios", "catalogo_sql", "alertas"],
/app/backend/modules/auth/schemas.py:146:        "permisos": ["comercial", "compras", "inventarios", "dashboard_inventarios"],
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:871:# PUNTO DE ENTRADA PRINCIPAL
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:793:# PUNTO DE ENTRADA
/app/backend/modules/comercial_v2/schemas.py:55:# SCHEMAS DE ENTRADA (desde orígenes)
/app/backend/modules/tablajeria/fase6_service.py:25:    ENTRADA_DERIVADO = "ENTRADA_DERIVADO"
/app/backend/modules/tablajeria/fase6_service.py:231:        2. ENTRADA_DERIVADO: Suma productos derivados al almacén
/app/backend/modules/tablajeria/fase6_service.py:292:            # 2. ENTRADA_DERIVADO - Productos producidos
/app/backend/modules/tablajeria/fase6_service.py:313:                    mov_id, orden_id, TipoMovimiento.ENTRADA_DERIVADO.value,
/app/backend/modules/tablajeria/fase6_service.py:320:                    "tipo": TipoMovimiento.ENTRADA_DERIVADO.value,
/app/backend/modules/tablajeria/fase6_service.py:656:                f"Entrada producción {costeo['FolioOrden']}",
/app/backend/modules/crm/vtiger_routes.py:381:            {"code": "Invoice", "name": "Facturas", "description": "Facturas"}
/app/backend/modules/finanzas/utils_bancarios.py:22:    Entrada: '0123456789'
/app/backend/modules/finanzas/utils_bancarios.py:36:    Entrada: '012345678901234567'
/app/backend/modules/finanzas/cuentas_por_pagar.py:2:EDARSA HUB - Cuentas por Pagar (Facturas Pendientes)
/app/backend/modules/finanzas/cuentas_por_pagar.py:4:Módulo para gestionar facturas pendientes de pago agrupadas por proveedor.
/app/backend/modules/finanzas/cuentas_por_pagar.py:13:2. Proveedor
/app/backend/modules/finanzas/cuentas_por_pagar.py:133:def generar_facturas_demo():
/app/backend/modules/finanzas/cuentas_por_pagar.py:134:    """Genera facturas demo para pruebas"""
/app/backend/modules/finanzas/cuentas_por_pagar.py:135:    proveedores = [
/app/backend/modules/finanzas/cuentas_por_pagar.py:154:    facturas = []
/app/backend/modules/finanzas/cuentas_por_pagar.py:155:    folio_entrada = 1000
/app/backend/modules/finanzas/cuentas_por_pagar.py:157:    for _ in range(75):  # 75 facturas demo
/app/backend/modules/finanzas/cuentas_por_pagar.py:158:        proveedor = demo_choice(proveedores)
/app/backend/modules/finanzas/cuentas_por_pagar.py:163:        fecha_entrada = datetime.now() - timedelta(days=dias_atras)
/app/backend/modules/finanzas/cuentas_por_pagar.py:165:        fecha_vencimiento = fecha_entrada + timedelta(days=dias_credito)
/app/backend/modules/finanzas/cuentas_por_pagar.py:176:        facturas.append({
/app/backend/modules/finanzas/cuentas_por_pagar.py:177:            "factura_id": len(facturas) + 1,
/app/backend/modules/finanzas/cuentas_por_pagar.py:178:            "folio_entrada": f"ENT-{folio_entrada}",
/app/backend/modules/finanzas/cuentas_por_pagar.py:180:            "fecha_entrada": fecha_entrada.strftime("%Y-%m-%d"),
/app/backend/modules/finanzas/cuentas_por_pagar.py:191:            "tiene_pdf_entrada": demo_random() > 0.1,
/app/backend/modules/finanzas/cuentas_por_pagar.py:192:            "proveedor_id": proveedor["id"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:193:            "proveedor_nombre": proveedor["nombre"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:194:            "proveedor_rfc": proveedor["rfc"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:200:        folio_entrada += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:202:    return facturas
/app/backend/modules/finanzas/cuentas_por_pagar.py:204:_facturas_db = generar_facturas_demo()
/app/backend/modules/finanzas/cuentas_por_pagar.py:216:    """Actualizar decisión de pago de múltiples facturas"""
/app/backend/modules/finanzas/cuentas_por_pagar.py:217:    facturas_ids: List[str]  # Cambiado de int a str para soportar IDs compuestos de SoftRestaurant
/app/backend/modules/finanzas/cuentas_por_pagar.py:225:async def listar_facturas_pendientes(
/app/backend/modules/finanzas/cuentas_por_pagar.py:227:    proveedor_id: Optional[str] = None,
/app/backend/modules/finanzas/cuentas_por_pagar.py:228:    tipo_proveedor: Optional[str] = None,  # A=Alimentos, B=Bebidas, X=Otros
/app/backend/modules/finanzas/cuentas_por_pagar.py:236:    Listar facturas/cuentas pendientes de pago.
/app/backend/modules/finanzas/cuentas_por_pagar.py:242:    Filtros: sucursal, proveedor, tipo (A/B/X), fecha de corte, solo vencidas.
/app/backend/modules/finanzas/cuentas_por_pagar.py:243:    Agrupa por TIPO DE PROVEEDOR (A=Alimentos, B=Bebidas, X=Otros).
/app/backend/modules/finanzas/cuentas_por_pagar.py:250:        all_facturas = []
/app/backend/modules/finanzas/cuentas_por_pagar.py:268:                    tipo_proveedor=tipo_proveedor
/app/backend/modules/finanzas/cuentas_por_pagar.py:276:                    tipo = c.get('TipoProveedor', 'X')
/app/backend/modules/finanzas/cuentas_por_pagar.py:280:                    # FolioEntrada, FolioFactura, FechaVencimiento, FechaFactura, Referencia
/app/backend/modules/finanzas/cuentas_por_pagar.py:284:                        "proveedor_id": c.get('ProveedorID'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:285:                        "proveedor_nombre": c.get('ProveedorNombre', 'N/A'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:286:                        "proveedor_rfc": c.get('ProveedorRFC', ''),
/app/backend/modules/finanzas/cuentas_por_pagar.py:287:                        "tipo_proveedor": tipo,
/app/backend/modules/finanzas/cuentas_por_pagar.py:288:                        "tipo_proveedor_nombre": c.get('TipoProveedorNombre', 'OTROS'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:291:                        # Campos detallados desde tabla compras (SoftRestaurant)
/app/backend/modules/finanzas/cuentas_por_pagar.py:292:                        "folio_entrada": c.get('FolioEntrada') or '-',
/app/backend/modules/finanzas/cuentas_por_pagar.py:294:                        "fecha_entrada": c.get('FechaEntrada') if isinstance(c.get('FechaEntrada'), str) else (c.get('FechaEntrada').isoformat() if c.get('FechaEntrada') else None),
/app/backend/modules/finanzas/cuentas_por_pagar.py:311:                    all_facturas.append(factura)
/app/backend/modules/finanzas/cuentas_por_pagar.py:348:                    proveedor_id=proveedor_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:371:                    # ABRIL 2026 - CLASIFICACIÓN MPRO por Grupo_Proveedor:
/app/backend/modules/finanzas/cuentas_por_pagar.py:372:                    # Gp_Cve_Grupo_Proveedor = '0001' → ALIMENTOS (A)
/app/backend/modules/finanzas/cuentas_por_pagar.py:373:                    # Gp_Cve_Grupo_Proveedor = '0002' → BEBIDAS (B)
/app/backend/modules/finanzas/cuentas_por_pagar.py:375:                    grupo_prov = str(c.get('GrupoProveedor', '') or '').strip()
/app/backend/modules/finanzas/cuentas_por_pagar.py:387:                    # FolioEntrada = Cxp_Documento
/app/backend/modules/finanzas/cuentas_por_pagar.py:390:                    folio_entrada = c.get('FolioEntrada') or c.get('CuentaPorPagarID', 'N/A')
/app/backend/modules/finanzas/cuentas_por_pagar.py:396:                        "proveedor_id": c.get('ProveedorID'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:397:                        "proveedor_nombre": c.get('ProveedorNombre') or f"Proveedor {c.get('ProveedorID')}",
/app/backend/modules/finanzas/cuentas_por_pagar.py:398:                        "proveedor_rfc": c.get('ProveedorRFC', ''),
/app/backend/modules/finanzas/cuentas_por_pagar.py:399:                        "tipo_proveedor": tipo_prov,
/app/backend/modules/finanzas/cuentas_por_pagar.py:400:                        "tipo_proveedor_nombre": tipo_prov_nombre,
/app/backend/modules/finanzas/cuentas_por_pagar.py:403:                        "folio_entrada": folio_entrada,
/app/backend/modules/finanzas/cuentas_por_pagar.py:405:                        "fecha_entrada": str(c.get('FechaEntrada', ''))[:10] if c.get('FechaEntrada') else None,
/app/backend/modules/finanzas/cuentas_por_pagar.py:420:                    all_facturas.append(factura)
/app/backend/modules/finanzas/cuentas_por_pagar.py:428:        # 3. Si hay datos, APLICAR FILTROS y agrupar por TIPO DE PROVEEDOR (A, B, X)
/app/backend/modules/finanzas/cuentas_por_pagar.py:429:        # El frontend espera: { proveedor_id: "A", proveedor_nombre: "A - ALIMENTOS", facturas: [...] }
/app/backend/modules/finanzas/cuentas_por_pagar.py:430:        # El frontend luego reagrupa las facturas por proveedor_nombre dentro de cada categoría
/app/backend/modules/finanzas/cuentas_por_pagar.py:431:        if all_facturas:
/app/backend/modules/finanzas/cuentas_por_pagar.py:434:                all_facturas = [f for f in all_facturas if f.get('dias_vencida', 0) > 0]
/app/backend/modules/finanzas/cuentas_por_pagar.py:437:                all_facturas = [f for f in all_facturas if f.get('decision_pago', False)]
/app/backend/modules/finanzas/cuentas_por_pagar.py:439:            # Agrupar por TIPO DE PROVEEDOR (A, B, X)
/app/backend/modules/finanzas/cuentas_por_pagar.py:441:            # - SoftRestaurant: Según clave del proveedor (A = ALIMENTOS, B = BEBIDAS, X = OTROS)
/app/backend/modules/finanzas/cuentas_por_pagar.py:442:            # - MPRO: Según Grupo_Proveedor (0001 = ALIMENTOS, 0002 = BEBIDAS, otros = OTROS)
/app/backend/modules/finanzas/cuentas_por_pagar.py:450:            for factura in all_facturas:
/app/backend/modules/finanzas/cuentas_por_pagar.py:451:                tipo = factura.get('tipo_proveedor', 'X')
/app/backend/modules/finanzas/cuentas_por_pagar.py:456:                        "proveedor_id": tipo,
/app/backend/modules/finanzas/cuentas_por_pagar.py:457:                        "proveedor_nombre": f"{tipo} - {tipo_nombre}",
/app/backend/modules/finanzas/cuentas_por_pagar.py:458:                        "proveedor_rfc": "",
/app/backend/modules/finanzas/cuentas_por_pagar.py:459:                        "cantidad_facturas": 0,
/app/backend/modules/finanzas/cuentas_por_pagar.py:463:                        "facturas": []
/app/backend/modules/finanzas/cuentas_por_pagar.py:466:                tipos[tipo]["facturas"].append(factura)
/app/backend/modules/finanzas/cuentas_por_pagar.py:467:                tipos[tipo]["cantidad_facturas"] += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:475:            proveedores_ordenados = [tipos.get(t) for t in orden_tipos if t in tipos]
/app/backend/modules/finanzas/cuentas_por_pagar.py:478:                "total_saldo": sum(p["subtotal_saldo"] for p in proveedores_ordenados),
/app/backend/modules/finanzas/cuentas_por_pagar.py:479:                "total_importe": sum(p["subtotal_importe"] for p in proveedores_ordenados),
/app/backend/modules/finanzas/cuentas_por_pagar.py:480:                "total_proveedores": len(proveedores_ordenados),
/app/backend/modules/finanzas/cuentas_por_pagar.py:481:                "cantidad_facturas": sum(p["cantidad_facturas"] for p in proveedores_ordenados),
/app/backend/modules/finanzas/cuentas_por_pagar.py:482:                "cantidad_vencidas": sum(p["cantidad_vencidas"] for p in proveedores_ordenados)
/app/backend/modules/finanzas/cuentas_por_pagar.py:487:                "proveedores": proveedores_ordenados,
/app/backend/modules/finanzas/cuentas_por_pagar.py:488:                "total_facturas": totales["cantidad_facturas"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:500:                proveedor_id=proveedor_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:508:                facturas = []
/app/backend/modules/finanzas/cuentas_por_pagar.py:519:                        "proveedor_id": c.get('ProveedorID'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:520:                        "proveedor_nombre": c.get('ProveedorNombre') or c.get('ProveedorNombreComercial') or f"Proveedor {c.get('ProveedorID')}",
/app/backend/modules/finanzas/cuentas_por_pagar.py:521:                        "proveedor_rfc": c.get('ProveedorRFC'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:525:                        "folio_entrada": c.get('NumeroDocumento'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:528:                        "fecha_entrada": str(c.get('FechaDocumento', ''))[:10],
/app/backend/modules/finanzas/cuentas_por_pagar.py:545:                        "ruta_pdf_entrada": None,
/app/backend/modules/finanzas/cuentas_por_pagar.py:548:                    facturas.append(factura)
/app/backend/modules/finanzas/cuentas_por_pagar.py:550:                # Agrupar por proveedor
/app/backend/modules/finanzas/cuentas_por_pagar.py:551:                proveedores_dict = {}
/app/backend/modules/finanzas/cuentas_por_pagar.py:552:                for f in facturas:
/app/backend/modules/finanzas/cuentas_por_pagar.py:553:                    prov_id = f["proveedor_id"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:554:                    if prov_id not in proveedores_dict:
/app/backend/modules/finanzas/cuentas_por_pagar.py:555:                        proveedores_dict[prov_id] = {
/app/backend/modules/finanzas/cuentas_por_pagar.py:556:                            "proveedor_id": prov_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:557:                            "proveedor_nombre": f["proveedor_nombre"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:558:                            "proveedor_rfc": f["proveedor_rfc"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:559:                            "facturas": [],
/app/backend/modules/finanzas/cuentas_por_pagar.py:563:                            "cantidad_facturas": 0,
/app/backend/modules/finanzas/cuentas_por_pagar.py:567:                    proveedores_dict[prov_id]["facturas"].append(f)
/app/backend/modules/finanzas/cuentas_por_pagar.py:568:                    proveedores_dict[prov_id]["subtotal_importe"] += f["importe_total"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:569:                    proveedores_dict[prov_id]["subtotal_saldo"] += f["saldo"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:570:                    proveedores_dict[prov_id]["cantidad_facturas"] += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:572:                        proveedores_dict[prov_id]["cantidad_vencidas"] += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:574:                # Ordenar proveedores por saldo descendente
/app/backend/modules/finanzas/cuentas_por_pagar.py:575:                proveedores_list = sorted(
/app/backend/modules/finanzas/cuentas_por_pagar.py:576:                    proveedores_dict.values(),
/app/backend/modules/finanzas/cuentas_por_pagar.py:582:                total_importe = sum(f["importe_total"] for f in facturas)
/app/backend/modules/finanzas/cuentas_por_pagar.py:583:                total_saldo = sum(f["saldo"] for f in facturas)
/app/backend/modules/finanzas/cuentas_por_pagar.py:584:                total_vencidas = sum(1 for f in facturas if f["dias_vencida"] > 0)
/app/backend/modules/finanzas/cuentas_por_pagar.py:587:                    "proveedores": proveedores_list,
/app/backend/modules/finanzas/cuentas_por_pagar.py:588:                    "total_facturas": len(facturas),
/app/backend/modules/finanzas/cuentas_por_pagar.py:594:                        "cantidad_proveedores": len(proveedores_list),
/app/backend/modules/finanzas/cuentas_por_pagar.py:595:                        "cantidad_facturas": len(facturas),
/app/backend/modules/finanzas/cuentas_por_pagar.py:602:                    "proveedores": [],
/app/backend/modules/finanzas/cuentas_por_pagar.py:603:                    "total_facturas": 0,
/app/backend/modules/finanzas/cuentas_por_pagar.py:610:                        "cantidad_proveedores": 0,
/app/backend/modules/finanzas/cuentas_por_pagar.py:611:                        "cantidad_facturas": 0,
/app/backend/modules/finanzas/cuentas_por_pagar.py:620:    facturas = [f for f in _facturas_db if f["saldo"] > 0]  # Solo pendientes
/app/backend/modules/finanzas/cuentas_por_pagar.py:624:        facturas = [f for f in facturas if f["sucursal_id"] == sucursal_id]
/app/backend/modules/finanzas/cuentas_por_pagar.py:626:    if proveedor_id:
/app/backend/modules/finanzas/cuentas_por_pagar.py:627:        facturas = [f for f in facturas if f["proveedor_id"] == proveedor_id]
/app/backend/modules/finanzas/cuentas_por_pagar.py:630:        facturas = [f for f in facturas if f["fecha_entrada"] <= fecha_corte]
/app/backend/modules/finanzas/cuentas_por_pagar.py:633:        facturas = [f for f in facturas if f["dias_vencida"] > 0]
/app/backend/modules/finanzas/cuentas_por_pagar.py:636:        facturas = [f for f in facturas if f["decision_pago"]]
/app/backend/modules/finanzas/cuentas_por_pagar.py:639:    for f in facturas:
/app/backend/modules/finanzas/cuentas_por_pagar.py:642:    # Agrupar por proveedor
/app/backend/modules/finanzas/cuentas_por_pagar.py:643:    proveedores_dict = {}
/app/backend/modules/finanzas/cuentas_por_pagar.py:644:    for f in facturas:
/app/backend/modules/finanzas/cuentas_por_pagar.py:645:        prov_id = f["proveedor_id"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:646:        if prov_id not in proveedores_dict:
/app/backend/modules/finanzas/cuentas_por_pagar.py:647:            proveedores_dict[prov_id] = {
/app/backend/modules/finanzas/cuentas_por_pagar.py:648:                "proveedor_id": prov_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:649:                "proveedor_nombre": f["proveedor_nombre"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:650:                "proveedor_rfc": f["proveedor_rfc"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:651:                "facturas": [],
/app/backend/modules/finanzas/cuentas_por_pagar.py:655:                "cantidad_facturas": 0,
/app/backend/modules/finanzas/cuentas_por_pagar.py:659:        proveedores_dict[prov_id]["facturas"].append(f)
/app/backend/modules/finanzas/cuentas_por_pagar.py:660:        proveedores_dict[prov_id]["subtotal_importe"] += f["importe_total"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:661:        proveedores_dict[prov_id]["subtotal_saldo"] += f["saldo"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:662:        proveedores_dict[prov_id]["subtotal_a_pagar"] += f["importe_a_pagar"] if f["decision_pago"] else 0
/app/backend/modules/finanzas/cuentas_por_pagar.py:663:        proveedores_dict[prov_id]["cantidad_facturas"] += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:665:            proveedores_dict[prov_id]["cantidad_vencidas"] += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:667:    # Ordenar facturas dentro de cada proveedor por fecha de vencimiento
/app/backend/modules/finanzas/cuentas_por_pagar.py:668:    for prov in proveedores_dict.values():
/app/backend/modules/finanzas/cuentas_por_pagar.py:669:        prov["facturas"].sort(key=lambda x: x["fecha_vencimiento"])
/app/backend/modules/finanzas/cuentas_por_pagar.py:671:    # Convertir a lista ordenada por nombre de proveedor
/app/backend/modules/finanzas/cuentas_por_pagar.py:672:    proveedores_list = sorted(proveedores_dict.values(), key=lambda x: x["proveedor_nombre"])
/app/backend/modules/finanzas/cuentas_por_pagar.py:675:    total_importe = sum(p["subtotal_importe"] for p in proveedores_list)
/app/backend/modules/finanzas/cuentas_por_pagar.py:676:    total_saldo = sum(p["subtotal_saldo"] for p in proveedores_list)
/app/backend/modules/finanzas/cuentas_por_pagar.py:677:    total_a_pagar = sum(p["subtotal_a_pagar"] for p in proveedores_list)
/app/backend/modules/finanzas/cuentas_por_pagar.py:678:    total_facturas = sum(p["cantidad_facturas"] for p in proveedores_list)
/app/backend/modules/finanzas/cuentas_por_pagar.py:679:    total_vencidas = sum(p["cantidad_vencidas"] for p in proveedores_list)
/app/backend/modules/finanzas/cuentas_por_pagar.py:682:        "proveedores": proveedores_list,
/app/backend/modules/finanzas/cuentas_por_pagar.py:683:        "total_facturas": total_facturas,
/app/backend/modules/finanzas/cuentas_por_pagar.py:690:            "cantidad_facturas": total_facturas,
/app/backend/modules/finanzas/cuentas_por_pagar.py:692:            "cantidad_proveedores": len(proveedores_list)
/app/backend/modules/finanzas/cuentas_por_pagar.py:696:            "proveedor_id": proveedor_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:706:    Calcula la antigüedad de facturas EN MEMORIA a partir de una lista de CxP.
/app/backend/modules/finanzas/cuentas_por_pagar.py:725:            continue  # Solo facturas con saldo pendiente
/app/backend/modules/finanzas/cuentas_por_pagar.py:751:    total_facturas = len(corriente) + len(vencidas_1_30) + len(vencidas_31_60) + len(vencidas_61_90) + len(vencidas_90_plus)
/app/backend/modules/finanzas/cuentas_por_pagar.py:755:        "total_facturas": total_facturas,
/app/backend/modules/finanzas/cuentas_por_pagar.py:906:                    por_fuente[fuente] = {'facturas': 0, 'saldo': 0}
/app/backend/modules/finanzas/cuentas_por_pagar.py:907:                por_fuente[fuente]['facturas'] += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:915:                    "total_facturas": antiguedad['total_facturas'],
/app/backend/modules/finanzas/cuentas_por_pagar.py:918:                    "facturas_con_decision": 0
/app/backend/modules/finanzas/cuentas_por_pagar.py:930:                    "total_facturas": -1,  # Indicador de error, no $0 falso
/app/backend/modules/finanzas/cuentas_por_pagar.py:933:                    "facturas_con_decision": 0,
/app/backend/modules/finanzas/cuentas_por_pagar.py:941:    facturas = [f for f in _facturas_db if f["saldo"] > 0]
/app/backend/modules/finanzas/cuentas_por_pagar.py:947:            facturas = [f for f in facturas if f["sucursal_id"] == suc_id]
/app/backend/modules/finanzas/cuentas_por_pagar.py:952:    corriente = [f for f in facturas if f["dias_vencida"] == 0]
/app/backend/modules/finanzas/cuentas_por_pagar.py:953:    vencidas_1_30 = [f for f in facturas if 1 <= f["dias_vencida"] <= 30]
/app/backend/modules/finanzas/cuentas_por_pagar.py:954:    vencidas_31_60 = [f for f in facturas if 31 <= f["dias_vencida"] <= 60]
/app/backend/modules/finanzas/cuentas_por_pagar.py:955:    vencidas_61_90 = [f for f in facturas if 61 <= f["dias_vencida"] <= 90]
/app/backend/modules/finanzas/cuentas_por_pagar.py:956:    vencidas_90_plus = [f for f in facturas if f["dias_vencida"] > 90]
/app/backend/modules/finanzas/cuentas_por_pagar.py:961:            "total_facturas": len(facturas),
/app/backend/modules/finanzas/cuentas_por_pagar.py:962:            "total_saldo": round(sum(f["saldo"] for f in facturas), 2),
/app/backend/modules/finanzas/cuentas_por_pagar.py:963:            "total_decision_pago": round(sum(f["importe_a_pagar"] for f in facturas if f["decision_pago"]), 2),
/app/backend/modules/finanzas/cuentas_por_pagar.py:964:            "facturas_con_decision": len([f for f in facturas if f["decision_pago"]])
/app/backend/modules/finanzas/cuentas_por_pagar.py:991:@router.get("/proveedores")
/app/backend/modules/finanzas/cuentas_por_pagar.py:992:async def listar_proveedores_con_saldo(
/app/backend/modules/finanzas/cuentas_por_pagar.py:997:    """Lista proveedores que tienen facturas pendientes - CONECTADO A MPRO"""
/app/backend/modules/finanzas/cuentas_por_pagar.py:1003:            proveedores = await mpro_repo.get_resumen_por_proveedor(sucursal_id=sucursal_id)
/app/backend/modules/finanzas/cuentas_por_pagar.py:1005:            if proveedores:
/app/backend/modules/finanzas/cuentas_por_pagar.py:1008:                    "proveedores": [
/app/backend/modules/finanzas/cuentas_por_pagar.py:1010:                            "proveedor_id": p.get('ProveedorID'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:1011:                            "proveedor_nombre": p.get('ProveedorNombre') or f"Proveedor {p.get('ProveedorID')}",
/app/backend/modules/finanzas/cuentas_por_pagar.py:1012:                            "proveedor_rfc": p.get('ProveedorRFC'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:1014:                            "cantidad_facturas": int(p.get('CantidadFacturas', 0) or 0)
/app/backend/modules/finanzas/cuentas_por_pagar.py:1016:                        for p in proveedores
/app/backend/modules/finanzas/cuentas_por_pagar.py:1020:            logging.error(f"Error obteniendo proveedores CxP de MPRO: {e}")
/app/backend/modules/finanzas/cuentas_por_pagar.py:1023:    facturas = [f for f in _facturas_db if f["saldo"] > 0]
/app/backend/modules/finanzas/cuentas_por_pagar.py:1028:            facturas = [f for f in facturas if f["sucursal_id"] == suc_id]
/app/backend/modules/finanzas/cuentas_por_pagar.py:1032:    proveedores = {}
/app/backend/modules/finanzas/cuentas_por_pagar.py:1033:    for f in facturas:
/app/backend/modules/finanzas/cuentas_por_pagar.py:1034:        prov_id = f["proveedor_id"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:1035:        if prov_id not in proveedores:
/app/backend/modules/finanzas/cuentas_por_pagar.py:1036:            proveedores[prov_id] = {
/app/backend/modules/finanzas/cuentas_por_pagar.py:1037:                "proveedor_id": prov_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:1038:                "proveedor_nombre": f["proveedor_nombre"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:1039:                "proveedor_rfc": f["proveedor_rfc"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:1041:                "cantidad_facturas": 0
/app/backend/modules/finanzas/cuentas_por_pagar.py:1043:        proveedores[prov_id]["total_saldo"] += f["saldo"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:1044:        proveedores[prov_id]["cantidad_facturas"] += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:1048:        "proveedores": sorted(proveedores.values(), key=lambda x: x["proveedor_nombre"])
/app/backend/modules/finanzas/cuentas_por_pagar.py:1083:                        "CantidadFacturas": int(s.get('CantidadFacturas', 0) or 0),
/app/backend/modules/finanzas/cuentas_por_pagar.py:1114:                        "CantidadFacturas": int(s.get('CantidadFacturas', 0) or 0),
/app/backend/modules/finanzas/cuentas_por_pagar.py:1235:    factura = next((f for f in _facturas_db if f["factura_id"] == numeric_id), None)
/app/backend/modules/finanzas/cuentas_por_pagar.py:1270:    Actualizar decisión de pago de múltiples facturas.
/app/backend/modules/finanzas/cuentas_por_pagar.py:1277:    for factura_id in data.facturas_ids:
/app/backend/modules/finanzas/cuentas_por_pagar.py:1279:        factura = next((f for f in _facturas_db if str(f.get("factura_id", "")) == str(factura_id)), None)
/app/backend/modules/finanzas/cuentas_por_pagar.py:1290:        factura_id=f'MASIVO_{len(data.facturas_ids)}',
/app/backend/modules/finanzas/cuentas_por_pagar.py:1293:            'cantidad_facturas': actualizadas,
/app/backend/modules/finanzas/cuentas_por_pagar.py:1296:        motivo=f'Pago masivo: {actualizadas} facturas'
/app/backend/modules/finanzas/cuentas_por_pagar.py:1302:        "total_solicitadas": len(data.facturas_ids)
/app/backend/modules/finanzas/cuentas_por_pagar.py:1312:    factura = next((f for f in _facturas_db if f["factura_id"] == factura_id), None)
/app/backend/modules/finanzas/repository_real.py:8:- Finanzas_CuentasPorPagar: Facturas pendientes de pago
/app/backend/modules/finanzas/repository_real.py:346:        proveedor_id: Optional[int] = None,
/app/backend/modules/finanzas/repository_real.py:354:        Incluye JOIN con Proveedor_Catalogo para nombre y RFC.
/app/backend/modules/finanzas/repository_real.py:358:            proveedor_id: Filtrar por proveedor
/app/backend/modules/finanzas/repository_real.py:371:        if proveedor_id:
/app/backend/modules/finanzas/repository_real.py:372:            where_clauses.append(f"c.ProveedorID = {proveedor_id}")
/app/backend/modules/finanzas/repository_real.py:386:                c.ProveedorID,
/app/backend/modules/finanzas/repository_real.py:387:                p.RazonSocial AS ProveedorNombre,
/app/backend/modules/finanzas/repository_real.py:388:                p.NombreComercial AS ProveedorNombreComercial,
/app/backend/modules/finanzas/repository_real.py:389:                p.RFC AS ProveedorRFC,
/app/backend/modules/finanzas/repository_real.py:390:                p.DiasCredito AS ProveedorDiasCredito,
/app/backend/modules/finanzas/repository_real.py:411:            LEFT JOIN Proveedor_Catalogo p ON c.ProveedorID = p.ProveedorID
/app/backend/modules/finanzas/repository_real.py:474:    async def get_cxp_por_proveedor(
/app/backend/modules/finanzas/repository_real.py:479:        Obtiene cuentas por pagar agrupadas por proveedor.
/app/backend/modules/finanzas/repository_real.py:490:                c.ProveedorID,
/app/backend/modules/finanzas/repository_real.py:498:            GROUP BY c.ProveedorID
/app/backend/modules/finanzas/repository_real.py:524:                c.ProveedorTPV,
/app/backend/modules/finanzas/sql_query_worker_secure.py:16:ENTRADA (stdin JSON):
/app/backend/modules/finanzas/ingresos.py:21:3. Proveedor de terminales: NetPay
/app/backend/modules/finanzas/ingresos.py:736:        "proveedor": "NetPay",
/app/backend/modules/finanzas/repository.py:7:- Cuentas por pagar (facturas pendientes)
/app/backend/modules/finanzas/repository.py:30:        Proveedor VARCHAR(100) DEFAULT 'NetPay',
/app/backend/modules/finanzas/repository.py:92:-- Facturas pendientes de pago a proveedores
/app/backend/modules/finanzas/repository.py:99:        ProveedorID INT,
/app/backend/modules/finanzas/repository.py:100:        ProveedorNombre NVARCHAR(200) NOT NULL,
/app/backend/modules/finanzas/repository.py:101:        ProveedorRFC VARCHAR(20),
/app/backend/modules/finanzas/repository.py:103:        FolioEntrada VARCHAR(50),
/app/backend/modules/finanzas/repository.py:105:        FechaEntrada DATE NOT NULL,
/app/backend/modules/finanzas/repository.py:119:        RutaPDFEntrada VARCHAR(500),
/app/backend/modules/finanzas/repository.py:131:    CREATE INDEX IX_CxP_Proveedor ON FIN_Cuentas_Por_Pagar(ProveedorID);
/app/backend/modules/finanzas/repository.py:156:        TipoConciliacion VARCHAR(50),  -- efectivo, tarjetas, proveedor
/app/backend/modules/finanzas/repository.py:181:    INSERT INTO FIN_Configuracion_TPV (SucursalID, TipoTarjeta, ComisionPorcentaje, DiasDeposito, IVAPorcentaje, Proveedor)
/app/backend/modules/finanzas/repository.py:239:                ComisionPorcentaje, DiasDeposito, IVAPorcentaje, Proveedor
/app/backend/modules/finanzas/repository.py:252:                c.IVAPorcentaje, c.Proveedor
/app/backend/modules/finanzas/repository.py:277:    async def get_facturas_pendientes(
/app/backend/modules/finanzas/repository.py:280:        proveedor_id: Optional[int] = None,
/app/backend/modules/finanzas/repository.py:284:        """Obtener facturas pendientes de pago"""
/app/backend/modules/finanzas/repository.py:289:        if proveedor_id:
/app/backend/modules/finanzas/repository.py:290:            where_clauses.append(f"ProveedorID = {proveedor_id}")
/app/backend/modules/finanzas/repository.py:292:            where_clauses.append(f"FechaEntrada <= '{fecha_corte}'")
/app/backend/modules/finanzas/repository.py:301:                f.ProveedorID, f.ProveedorNombre, f.ProveedorRFC,
/app/backend/modules/finanzas/repository.py:302:                f.FolioEntrada, f.FolioFactura,
/app/backend/modules/finanzas/repository.py:303:                CONVERT(VARCHAR, f.FechaEntrada, 23) as FechaEntrada,
/app/backend/modules/finanzas/repository.py:310:                CASE WHEN f.RutaPDFEntrada IS NOT NULL THEN 1 ELSE 0 END as TienePDFEntrada
/app/backend/modules/finanzas/repository.py:314:            ORDER BY f.ProveedorNombre, f.FechaVencimiento
/app/backend/modules/finanzas/repository.py:336:    async def actualizar_decision_pago_masivo(self, facturas_ids: List[int], decision: bool) -> int:
/app/backend/modules/finanzas/repository.py:337:        """Actualizar decisión de pago de múltiples facturas"""
/app/backend/modules/finanzas/repository.py:338:        ids_str = ",".join(map(str, facturas_ids))
/app/backend/modules/finanzas/repository.py:348:        return len(facturas_ids)
/app/backend/modules/finanzas/historical_kpis_repository.py:91:        cxp_facturas_count = kpi_data.get("cxp_facturas_count", 0)
/app/backend/modules/finanzas/historical_kpis_repository.py:116:                cxp_facturas_count = %s, cxp_monto_total = %s, cxp_monto_alimentos = %s,
/app/backend/modules/finanzas/historical_kpis_repository.py:126:                cxp_facturas_count, cxp_monto_total, cxp_monto_alimentos,
/app/backend/modules/finanzas/historical_kpis_repository.py:139:                cxp_facturas_count, cxp_monto_total, cxp_monto_alimentos,
/app/backend/modules/finanzas/historical_kpis_repository.py:155:                cxp_facturas_count, cxp_monto_total, cxp_monto_alimentos,
/app/backend/modules/finanzas/repository_softrestaurant.py:12:AGRUPACIÓN DE PROVEEDORES:
/app/backend/modules/finanzas/repository_softrestaurant.py:17:Formato nombre proveedor: "[XXXX] TYYYY NOMBRE" donde T es el tipo (A, B, X)
/app/backend/modules/finanzas/repository_softrestaurant.py:66:def get_tipo_proveedor(nombre_proveedor: str) -> str:
/app/backend/modules/finanzas/repository_softrestaurant.py:68:    Extrae el tipo de proveedor del nombre.
/app/backend/modules/finanzas/repository_softrestaurant.py:82:    if not nombre_proveedor:
/app/backend/modules/finanzas/repository_softrestaurant.py:85:    nombre = nombre_proveedor.strip()
/app/backend/modules/finanzas/repository_softrestaurant.py:159:    Consulta múltiples sucursales y agrupa por tipo de proveedor.
/app/backend/modules/finanzas/repository_softrestaurant.py:308:        tipo_proveedor: Optional[str] = None,
/app/backend/modules/finanzas/repository_softrestaurant.py:316:        - El saldo se calcula: total - SUM(pagosproveedores.abono)
/app/backend/modules/finanzas/repository_softrestaurant.py:317:        - Ordenado por folio de entrada ASCENDENTE
/app/backend/modules/finanzas/repository_softrestaurant.py:323:            tipo_proveedor: A=Alimentos, B=Bebidas, X=Otros
/app/backend/modules/finanzas/repository_softrestaurant.py:345:            # DICIEMBRE 2026: Query principal - Compras con saldo individual calculado
/app/backend/modules/finanzas/repository_softrestaurant.py:350:            # SoftRestaurant marca compras como cancelado=1 cuando están cerradas/históricas
/app/backend/modules/finanzas/repository_softrestaurant.py:351:            # Solo mostrar compras activas (no canceladas) con saldo pendiente
/app/backend/modules/finanzas/repository_softrestaurant.py:352:            query_compras_con_saldo = f"""
/app/backend/modules/finanzas/repository_softrestaurant.py:355:                    c.folio AS FolioEntrada,
/app/backend/modules/finanzas/repository_softrestaurant.py:357:                    c.fechaaplicacion AS FechaEntrada,
/app/backend/modules/finanzas/repository_softrestaurant.py:361:                    c.idproveedor AS ProveedorID,
/app/backend/modules/finanzas/repository_softrestaurant.py:364:                    p.nombre AS ProveedorNombre,
/app/backend/modules/finanzas/repository_softrestaurant.py:365:                    p.rfc AS ProveedorRFC
/app/backend/modules/finanzas/repository_softrestaurant.py:366:                FROM compras c
/app/backend/modules/finanzas/repository_softrestaurant.py:367:                LEFT JOIN proveedores p ON c.idproveedor = p.idproveedor
/app/backend/modules/finanzas/repository_softrestaurant.py:368:                LEFT JOIN pagosproveedores pp ON pp.foliocompra = c.idcompra
/app/backend/modules/finanzas/repository_softrestaurant.py:371:                         c.fechavencimiento, c.referencia, c.idproveedor, c.total, p.nombre, p.rfc
/app/backend/modules/finanzas/repository_softrestaurant.py:376:            results_compras = await self._execute_query_subprocess(server_key, query_compras_con_saldo)
/app/backend/modules/finanzas/repository_softrestaurant.py:378:            if not results_compras:
/app/backend/modules/finanzas/repository_softrestaurant.py:379:                logging.warning(f"[SoftRestaurant] Sin compras con saldo para {server_key}")
/app/backend/modules/finanzas/repository_softrestaurant.py:382:            logging.info(f"[SoftRestaurant] {server_key}: {len(results_compras)} documentos con saldo > 0")
/app/backend/modules/finanzas/repository_softrestaurant.py:388:            for c in results_compras:
/app/backend/modules/finanzas/repository_softrestaurant.py:389:                proveedor_nombre = str(c.get('ProveedorNombre', '') or '').strip()
/app/backend/modules/finanzas/repository_softrestaurant.py:390:                proveedor_id = str(c.get('ProveedorID', '') or '').strip()
/app/backend/modules/finanzas/repository_softrestaurant.py:392:                # Determinar tipo de proveedor desde el nombre
/app/backend/modules/finanzas/repository_softrestaurant.py:393:                tipo = get_tipo_proveedor(proveedor_nombre)
/app/backend/modules/finanzas/repository_softrestaurant.py:394:                if tipo_proveedor and tipo != tipo_proveedor:
/app/backend/modules/finanzas/repository_softrestaurant.py:398:                folio_entrada = str(c.get('FolioEntrada', '') or '').strip()
/app/backend/modules/finanzas/repository_softrestaurant.py:400:                fecha_entrada = c.get('FechaEntrada')
/app/backend/modules/finanzas/repository_softrestaurant.py:404:                proveedor_rfc = str(c.get('ProveedorRFC', '') or '').strip()
/app/backend/modules/finanzas/repository_softrestaurant.py:409:                if isinstance(fecha_entrada, str) and 'T' in fecha_entrada:
/app/backend/modules/finanzas/repository_softrestaurant.py:410:                    fecha_entrada = fecha_entrada.split('T')[0]
/app/backend/modules/finanzas/repository_softrestaurant.py:437:                cuenta_id = f"{server_key}_{folio_entrada}"
/app/backend/modules/finanzas/repository_softrestaurant.py:443:                    "ProveedorID": proveedor_id,
/app/backend/modules/finanzas/repository_softrestaurant.py:444:                    "ProveedorNombre": proveedor_nombre,
/app/backend/modules/finanzas/repository_softrestaurant.py:445:                    "ProveedorRFC": proveedor_rfc,
/app/backend/modules/finanzas/repository_softrestaurant.py:446:                    "TipoProveedor": tipo,
/app/backend/modules/finanzas/repository_softrestaurant.py:447:                    "TipoProveedorNombre": get_nombre_tipo(tipo),
/app/backend/modules/finanzas/repository_softrestaurant.py:448:                    "FolioEntrada": folio_entrada or None,
/app/backend/modules/finanzas/repository_softrestaurant.py:450:                    "FechaEntrada": fecha_entrada,
/app/backend/modules/finanzas/repository_softrestaurant.py:476:            "total_facturas": 0,
/app/backend/modules/finanzas/repository_softrestaurant.py:485:            totales["total_facturas"] += 1
/app/backend/modules/finanzas/repository_softrestaurant.py:513:        """Obtiene resumen agrupado por tipo de proveedor (A, B, X)"""
/app/backend/modules/finanzas/repository_softrestaurant.py:518:            tipo = c.get('TipoProveedor', 'X')
/app/backend/modules/finanzas/repository_softrestaurant.py:521:                    "TipoProveedor": tipo,
/app/backend/modules/finanzas/repository_softrestaurant.py:523:                    "CantidadProveedores": 0,
/app/backend/modules/finanzas/repository_softrestaurant.py:525:                    "Proveedores": set()
/app/backend/modules/finanzas/repository_softrestaurant.py:527:            tipos[tipo]["Proveedores"].add(c.get('ProveedorNombre'))
/app/backend/modules/finanzas/repository_softrestaurant.py:534:                "TipoProveedor": data["TipoProveedor"],
/app/backend/modules/finanzas/repository_softrestaurant.py:536:                "CantidadProveedores": len(data["Proveedores"]),
/app/backend/modules/finanzas/repository_softrestaurant.py:554:                "CantidadFacturas": len(cxp),
/app/backend/modules/finanzas/test_conn_cienfuegos.py:1317:# PUNTO DE ENTRADA
/app/backend/modules/finanzas/repository_mpro.py:8:- Proveedor: Catálogo de proveedores
/app/backend/modules/finanzas/repository_mpro.py:131:        proveedor_id: Optional[str] = None,
/app/backend/modules/finanzas/repository_mpro.py:141:            proveedor_id: Clave de proveedor
/app/backend/modules/finanzas/repository_mpro.py:156:        if proveedor_id:
/app/backend/modules/finanzas/repository_mpro.py:157:            where_clauses.append(f"c.Pv_Cve_Proveedor = '{proveedor_id}'")
/app/backend/modules/finanzas/repository_mpro.py:166:        # - Cxp_Documento = Folio Entrada (folio del documento de entrada de compra)
/app/backend/modules/finanzas/repository_mpro.py:167:        # - Cxp_Referencia = Folio Factura (número de factura del proveedor)
/app/backend/modules/finanzas/repository_mpro.py:170:        # - Cxp_Fecha = Fecha de entrada
/app/backend/modules/finanzas/repository_mpro.py:173:        # CLASIFICACIÓN MPRO por Grupo_Proveedor:
/app/backend/modules/finanzas/repository_mpro.py:174:        # - Gp_Cve_Grupo_Proveedor = '0001' → ALIMENTOS (A)
/app/backend/modules/finanzas/repository_mpro.py:175:        # - Gp_Cve_Grupo_Proveedor = '0002' → BEBIDAS (B)
/app/backend/modules/finanzas/repository_mpro.py:180:                c.Cxp_Documento as FolioEntrada,
/app/backend/modules/finanzas/repository_mpro.py:184:                c.Pv_Cve_Proveedor as ProveedorID,
/app/backend/modules/finanzas/repository_mpro.py:185:                p.Pv_Razon_Social as ProveedorNombre,
/app/backend/modules/finanzas/repository_mpro.py:186:                p.Pv_R_F_C as ProveedorRFC,
/app/backend/modules/finanzas/repository_mpro.py:187:                p.Gp_Cve_Grupo_Proveedor as GrupoProveedor,
/app/backend/modules/finanzas/repository_mpro.py:188:                c.Cxp_Fecha as FechaEntrada,
/app/backend/modules/finanzas/repository_mpro.py:197:            LEFT JOIN Proveedor p ON c.Pv_Cve_Proveedor = p.Pv_Cve_Proveedor
/app/backend/modules/finanzas/repository_mpro.py:211:                COUNT(*) as CantidadFacturas,
/app/backend/modules/finanzas/repository_mpro.py:223:    async def get_resumen_por_proveedor(self, sucursal_id: Optional[str] = None) -> List[Dict]:
/app/backend/modules/finanzas/repository_mpro.py:224:        """Obtiene resumen de CxP agrupado por proveedor"""
/app/backend/modules/finanzas/repository_mpro.py:237:                c.Pv_Cve_Proveedor as ProveedorID,
/app/backend/modules/finanzas/repository_mpro.py:238:                p.Pv_Razon_Social as ProveedorNombre,
/app/backend/modules/finanzas/repository_mpro.py:239:                p.Pv_R_F_C as ProveedorRFC,
/app/backend/modules/finanzas/repository_mpro.py:240:                COUNT(*) as CantidadFacturas,
/app/backend/modules/finanzas/repository_mpro.py:245:            LEFT JOIN Proveedor p ON c.Pv_Cve_Proveedor = p.Pv_Cve_Proveedor
/app/backend/modules/finanzas/repository_mpro.py:247:            GROUP BY c.Pv_Cve_Proveedor, p.Pv_Razon_Social, p.Pv_R_F_C
/app/backend/modules/finanzas/repository_mpro.py:276:                COUNT(*) as TotalFacturas,
/app/backend/modules/finanzas/repository_mpro.py:306:                "total_facturas": int(r.get('TotalFacturas') or 0),
/app/backend/modules/finanzas/repository_mpro.py:316:            "total_facturas": 0,
/app/backend/modules/finanzas/repository_mpro.py:320:    async def get_proveedores(self) -> List[Dict]:
/app/backend/modules/finanzas/repository_mpro.py:321:        """Obtiene catálogo de proveedores con saldo pendiente"""
/app/backend/modules/finanzas/repository_mpro.py:324:                p.Pv_Cve_Proveedor as ProveedorID,
/app/backend/modules/finanzas/repository_mpro.py:327:            FROM Proveedor p
/app/backend/modules/finanzas/repository_mpro.py:328:            INNER JOIN Cuenta_X_Pagar c ON p.Pv_Cve_Proveedor = c.Pv_Cve_Proveedor
/app/backend/modules/cava_socios/service.py:9:- Registro de movimientos (entradas, consumos, retiros)
/app/backend/modules/cava_socios/service.py:271:            # Registrar movimiento de entrada
/app/backend/modules/cava_socios/service.py:283:                'ENTRADA', 0, 100, 'Ingreso de botella a cava', usuario_id
/app/backend/modules/manuales_operativos/service.py:67:    async def generar_manual_auditoria_compras(
/app/backend/modules/manuales_operativos/service.py:74:        Genera un manual operativo para Auditoría de Compras.
/app/backend/modules/manuales_operativos/service.py:77:            proceso: Documento de automatizaciones_operativas_compras
/app/backend/modules/manuales_operativos/service.py:101:            nombre_proceso = f"Auditoría Operativa de Compras - {sucursal} - {almacen}"
/app/backend/modules/manuales_operativos/service.py:105:                f"Validar y auditar el proceso de compras para {sucursal}, "
/app/backend/modules/manuales_operativos/service.py:114:                f"Este proceso cubre la auditoría de compras del período "
/app/backend/modules/manuales_operativos/service.py:158:                "modulo": ModuloOrigen.COMPRAS.value,
/app/backend/modules/manuales_operativos/service.py:160:                "proceso_tipo": "auditoria_compras",
/app/backend/modules/manuales_operativos/triggers.py:11:    await trigger_generar_manual(db, proceso_id, modulo="compras")
/app/backend/modules/manuales_operativos/triggers.py:14:    trigger_generar_manual_sync(db_sync, proceso_id, modulo="compras")
/app/backend/modules/manuales_operativos/triggers.py:34:    modulo: str = "compras",
/app/backend/modules/manuales_operativos/triggers.py:45:        modulo: Módulo del proceso (compras, operaciones, etc.)
/app/backend/modules/manuales_operativos/triggers.py:61:        if modulo == "compras":
/app/backend/modules/manuales_operativos/triggers.py:62:            return await _generar_manual_compras(db, service, proceso_id)
/app/backend/modules/manuales_operativos/triggers.py:72:async def _generar_manual_compras(
/app/backend/modules/manuales_operativos/triggers.py:77:    """Genera manual para auditoría de compras."""
/app/backend/modules/manuales_operativos/triggers.py:80:    proceso = await db.automatizaciones_operativas_compras.find_one({"id": proceso_id})
/app/backend/modules/manuales_operativos/triggers.py:82:        logger.error(f"Proceso de compras no encontrado: {proceso_id}")
/app/backend/modules/manuales_operativos/triggers.py:112:    manual = await service.generar_manual_auditoria_compras(proceso, bitacora, usuarios)
/app/backend/modules/manuales_operativos/triggers.py:136:    # Buscar procesos de compras completados sin manual
```
## 2. Queries MPRO relacionadas con compras/entradas/recepciones
```text
/app/backend/init_queries.py:87:    "movimientos": """DECLARE @SUCURSAL VARCHAR(50)
/app/backend/init_queries.py:103:    WHEN TM.Tm_Cve_Tipo_Movimiento IN('508','108') 
/app/backend/init_queries.py:108:                INNER JOIN COMPRA C ON C.Co_Folio = CN.Cp_Documento AND C.Pr_Cve_Producto = CN.Pr_Cve_Producto
/app/backend/init_queries.py:121:e.Tm_Cve_Tipo_Movimiento [Codigo],
/app/backend/init_queries.py:122:tm.Tm_Descripcion [Movimiento],
/app/backend/init_queries.py:134:Movimiento E
/app/backend/init_queries.py:137:inner join Tipo_Movimiento tm on tm.Tm_Cve_Tipo_Movimiento = e.Tm_Cve_Tipo_Movimiento
/app/backend/init_queries.py:148:    WHEN TM.Tm_Cve_Tipo_Movimiento IN('508','108') 
/app/backend/init_queries.py:153:                INNER JOIN COMPRA C ON C.Co_Folio = CN.Cp_Documento AND C.Pr_Cve_Producto = CN.Pr_Cve_Producto
/app/backend/init_queries.py:161:AND E.Tm_Cve_Tipo_Movimiento IN ('050','100', '106', '108','112','202','400','500','506','508','510','512')
/app/backend/init_queries.py:183:            AND Conversion_Unidad.Cu_Unidad_Origen = producto.Pr_Unidad_Compra AND Conversion_Unidad.Cu_Unidad_Destino = producto.Pr_Unidad_Control_1
/app/backend/init_queries.py:212:                AND Conversion_Unidad.Cu_Unidad_Origen = producto.Pr_Unidad_Compra AND Conversion_Unidad.Cu_Unidad_Destino = producto.Pr_Unidad_Control_1
/app/backend/modules/comercial/routes_pricing_ai.py:343:    - Datos de entrada utilizados
/app/backend/modules/comercial/routes_pricing_ai.py:381:        "proveedor": "OpenAI via Emergent LLM Key",
/app/backend/modules/comercial/cache_service.py:350:    Limpia entradas de cache expiradas.
/app/backend/modules/comercial/cache_service.py:379:        logging.info(f"Cache cleanup: {deleted_count} entradas eliminadas (antes: {total_before}, después: {total_after})")
/app/backend/modules/comercial/queries/mpro.py:14:- Requisicion_Compra: Requisiciones de compra
/app/backend/modules/comercial/queries/mpro.py:85:    'Requisicion_Compra',
/app/backend/modules/comercial/queries/mpro.py:88:    'Proveedor',
/app/backend/modules/comercial/queries/softrestaurant.py:67:    'compras',
/app/backend/modules/comercial/queries/softrestaurant.py:68:    'comprasmovtos',
/app/backend/modules/comercial/crm_router.py:10:# MODELOS PYDANTIC (Validación de Entrada)
/app/backend/modules/comercial/rentabilidad.py:38:            FROM dbo.Compras_Inventarios_Fisicos_Sync
/app/backend/modules/comercial/repository.py:139:        'query_movimientos': parse_json_field(row.get('query_movimientos')),
/app/backend/modules/comercial/services/pricing_ai_service.py:18:PROVEEDOR IA:
/app/backend/modules/comercial/services/pricing_ai_service.py:131:            DatosEntradaJSON NVARCHAR(MAX) NULL,
/app/backend/modules/comercial/services/pricing_ai_service.py:372:    datos_entrada_json: Dict,
/app/backend/modules/comercial/services/pricing_ai_service.py:412:    datos_entrada_str = json.dumps(datos_entrada_json, ensure_ascii=False).replace("'", "''")
/app/backend/modules/comercial/services/pricing_ai_service.py:431:        DatosEntradaJSON,
/app/backend/modules/comercial/services/pricing_ai_service.py:458:        N'{datos_entrada_str}',
/app/backend/modules/comercial/services/pricing_ai_service.py:506:        DatosEntradaJSON,
/app/backend/modules/comercial/services/pricing_ai_service.py:533:    datos_entrada = None
/app/backend/modules/comercial/services/pricing_ai_service.py:539:        if row.get('DatosEntradaJSON'):
/app/backend/modules/comercial/services/pricing_ai_service.py:540:            datos_entrada = json.loads(row['DatosEntradaJSON'])
/app/backend/modules/comercial/services/pricing_ai_service.py:573:        'datos_entrada': datos_entrada,
/app/backend/modules/comercial/services/pricing_ai_service.py:686:    # 6. Preparar datos de entrada para IA
/app/backend/modules/comercial/services/pricing_ai_service.py:687:    datos_entrada = {
/app/backend/modules/comercial/services/pricing_ai_service.py:831:            datos_entrada_json=datos_entrada,
/app/backend/modules/comercial/services/pricing_ai_service.py:886:            datos_entrada_json=datos_entrada,
/app/backend/modules/comercial/services/pricing_ai_service.py:1036:            datos_entrada_json={
/app/backend/modules/comercial/services/pricing_ai_service.py:1188:            datos_entrada_json={
/app/backend/modules/comercial/services/pricing_ai_service.py:1407:            datos_entrada_json={
/app/backend/modules/comercial/services/precios_vinos_service.py:31:    6-9. Fuentes adicionales (futuro: compras, proveedor, override)
/app/backend/modules/comercial/services/precios_vinos_service.py:239:    6-9. Fuentes adicionales (futuro: compras, proveedor, override)
/app/backend/modules/comercial/services/precios_vinos_service.py:241:    NOTA: Para vinos (botellas compradas), CostoReceta = 0 generalmente
/app/backend/modules/comercial/services/precios_vinos_service.py:299:    # Jerarquías 6-9: Futuras fuentes (compras, proveedor, override)
/app/backend/modules/comercial/routes.py:32:- ✅ Endpoints /comercial/mesas y /comercial/detalle-movimientos migrados (Fase 5B-4E)
/app/backend/modules/comercial/routes.py:57:   - GET /comercial/detalle-movimientos/{server_id} (Fase 5B-4E)
/app/backend/modules/comercial/routes.py:187:# - /comercial/detalle-movimientos/{server_id} - Requiere: tabla de detalle
/app/backend/modules/comercial/routes.py:216:    '/comercial/detalle-movimientos': {
/app/backend/modules/comercial/routes.py:217:        'tabla_requerida': 'Sync_Movimientos_Detalle',
/app/backend/modules/comercial/routes.py:218:        'job_requerido': 'sync_movimientos',
/app/backend/modules/comercial/routes.py:1677:    # Construir mapa de server_id → codigo para resolver entradas con código vacío
/app/backend/modules/comercial/routes.py:1718:    # Prioridad de estados para elegir la mejor entrada
/app/backend/modules/comercial/routes.py:1740:                # La nueva entrada tiene mejor estado → reemplazar
/app/backend/modules/comercial/routes.py:1741:                logging.info(f"[P1-DEDUP] Reemplazando entrada: {codigo_key} ({existente.get('data_status')} → {unidad.get('data_status')})")
/app/backend/modules/comercial/routes.py:1747:                    logging.info(f"[P1-DEDUP] Descartando entrada duplicada con error: {codigo_key}")
/app/backend/modules/comercial/routes.py:1798:                # Crear entrada para esta unidad desde SQL
/app/backend/modules/comercial/routes.py:2432:                "promedio_entradas": float(row.get("PromedioEntradas") or 0),
/app/backend/modules/comercial/routes.py:2521:                        "con_entrada": con_alimentos,
/app/backend/modules/comercial/routes.py:2522:                        "pct_entrada": round((con_alimentos / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
/app/backend/modules/comercial/routes.py:2553:                            "con_entrada": 0, "pct_entrada": 0,
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
/app/backend/modules/hub/bus_abstraccion_universal.py:34:                    "Tipo_Movimiento": "DEBITO",
/app/backend/modules/hub/bus_abstraccion_universal.py:41:                    "Tipo_Movimiento": "CREDITO",
/app/backend/modules/hub/bus_abstraccion_universal.py:48:                    "Tipo_Movimiento": "CREDITO",
/app/backend/modules/hub/modulo_financiero_proyectos.py:31:            # Transacciones financieras vinculadas al proyecto (Ingresos, Compras, Gastos)
/app/backend/modules/hub/modulo_financiero_proyectos.py:34:                    id_movimiento TEXT PRIMARY KEY,
/app/backend/modules/hub/modulo_financiero_proyectos.py:36:                    tipo_flujo TEXT NOT NULL, -- INGRESO_ANTICIPO, COMPRA_INSUMO, GASTO_OPERATIVO
/app/backend/modules/hub/modulo_financiero_proyectos.py:46:    # INYECCIÓN DE FLUJOS (COMPRAS, GASTOS E INGRESOS)
/app/backend/modules/hub/modulo_financiero_proyectos.py:48:    def registrar_movimiento_proyecto(self, id_proyecto: str, tipo_flujo: str, descripcion: str, monto: float) -> None:
/app/backend/modules/hub/modulo_financiero_proyectos.py:53:        id_movimiento = f"MOV-{int(time.time())}-{descripcion[:4].upper()}"
/app/backend/modules/hub/modulo_financiero_proyectos.py:57:                INSERT INTO transacciones_proyecto (id_movimiento, id_proyecto, tipo_flujo, descripcion, monto_neto, timestamp)
/app/backend/modules/hub/modulo_financiero_proyectos.py:59:            ''', (id_movimiento, id_proyecto, tipo_flujo, descripcion, monto, time.strftime("%Y-%m-%dT%H:%M:%SZ")))
/app/backend/modules/hub/modulo_financiero_proyectos.py:82:            movimientos = cursor.fetchall()
/app/backend/modules/hub/modulo_financiero_proyectos.py:84:            totales = {"INGRESO_ANTICIPO": 0.0, "COMPRA_INSUMO": 0.0, "GASTO_OPERATIVO": 0.0}
/app/backend/modules/hub/modulo_financiero_proyectos.py:85:            for mov in movimientos:
/app/backend/modules/hub/modulo_financiero_proyectos.py:90:        costos_totales = totales["COMPRA_INSUMO"] + totales["GASTO_OPERATIVO"]
/app/backend/modules/hub/modulo_financiero_proyectos.py:106:                "costo_compras_insumos": totales["COMPRA_INSUMO"],
/app/backend/modules/fase2_operativo/sql_repository.py:356:                Movimientos, Ventas, RequiereJustificacionCompleta
/app/backend/modules/fase2_operativo/sql_repository.py:376:            float(prod.get("Movimientos", 0) or 0),
/app/backend/modules/fase2_operativo/router.py:21:from .routes.automatizacion_compras_routes import router as automatizacion_compras_router
/app/backend/modules/fase2_operativo/router.py:111:    automatizacion_compras_router,
/app/backend/modules/fase2_operativo/repositories/cargos_repository.py:452:        Registra una entrada en el log de auditoría.
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:43:    "tareas_operativas_compras": "Operativo_TareasCompras",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:44:    "auditoria_compras_bitacora": "Operativo_BitacoraCompras",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:53:    # FASE B-P2-B: Automatización Compras
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:54:    "automatizaciones_operativas_compras": "Operativo_TareasCompras",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:55:    "automatizaciones_bitacora": "Operativo_BitacoraCompras",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:57:    "inventarios_fisicos_procesados": "Compras_Inventarios_Fisicos_Sync",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:730:            "Operativo_TareasCompras": "TareaID",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:731:            "Operativo_BitacoraCompras": "BitacoraID",
/app/backend/modules/fase2_operativo/api_schemas.py:5:Define los modelos Pydantic para validación de entradas y salidas HTTP.
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:2:EDARSA HUB - Automatización Operativa de Compras
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:15:- Operativo_TareasCompras (automatizaciones principales)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:16:- Operativo_BitacoraCompras (bitácora de acciones)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:58:    """Recomendación de compra."""
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:60:    COMPRAR = "COMPRAR"
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:61:    NO_COMPRAR = "NO_COMPRAR"
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:65:class AutomatizacionComprasService:
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:67:    Servicio de automatización operativa de compras.
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:84:        self._repo = SQLBaseRepository("automatizaciones_operativas_compras")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:88:        logger.info("[AUTO_COMPRAS] Inicializado con SQL → Operativo_TareasCompras")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:550:            recomendacion = Recomendacion.COMPRAR.value
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:553:            recomendacion = Recomendacion.NO_COMPRAR.value
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:582:            return Recomendacion.COMPRAR.value
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:585:        return Recomendacion.NO_COMPRAR.value
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:682:            manual_id = trigger_generar_manual_sync(self.db, automatizacion_id, modulo="compras")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:694:def get_automatizacion_compras_service(db=None) -> AutomatizacionComprasService:
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:696:    return AutomatizacionComprasService(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:2:EDARSA HUB - Routes de Automatización Operativa de Compras
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:19:from modules.fase2_operativo.services.automatizacion_compras_service import (
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:20:    get_automatizacion_compras_service,
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:83:@router.post("/compras/detector/ejecutar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:126:@router.get("/compras/detector/estado")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:167:@router.get("/compras/tareas")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:188:    tareas = list(db.tareas_operativas_compras.find(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:199:@router.get("/compras/tareas/{tarea_id}")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:208:    tarea = db.tareas_operativas_compras.find_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:219:@router.post("/compras/tareas/{tarea_id}/completar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:235:    tarea = db.tareas_operativas_compras.find_one({"id": tarea_id})
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:244:    db.tareas_operativas_compras.update_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:259:@router.post("/compras/tareas/{tarea_id}/asignar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:271:    tarea = db.tareas_operativas_compras.find_one({"id": tarea_id})
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:277:    db.tareas_operativas_compras.update_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:295:@router.get("/compras/kpis")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:303:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:307:@router.get("/compras")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:318:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:326:@router.get("/compras/detector/bitacora")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:339:    bitacora = list(db.auditoria_compras_bitacora.find(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:350:@router.get("/compras/pedidos-procesados")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:386:@router.get("/compras/{automatizacion_id}")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:394:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:403:@router.post("/compras/procesar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:414:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:437:@router.post("/compras/{automatizacion_id}/gerencia")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:451:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:476:@router.post("/compras/{automatizacion_id}/tesoreria")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:489:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:513:@router.post("/compras/{automatizacion_id}/dias-objetivo")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:525:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:548:@router.post("/compras/{automatizacion_id}/parametros-consumo")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:575:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:596:@router.get("/compras/{automatizacion_id}/bitacora")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:604:    service = get_automatizacion_compras_service(db)
/app/backend/modules/api_connections/routes.py:75:    tipo_uso: str = Field("Otro", description="Tipo de uso: Ventas del día, Inventario, Cortes, Compras, Otro")
/app/backend/modules/api_connections/universal_test_routes.py:25:- Módulos: Comercial, Tablero, KPIs, Inventarios, Compras, Finanzas, Operaciones
/app/backend/modules/corporate_filters/router.py:298:        "proveedores": [],
/app/backend/modules/corporate_filters/router.py:310:        "proveedores": ["empresas"],
/app/backend/modules/corporate_filters/router.py:349:        filters["proveedores"] = get_optional_catalog(
/app/backend/modules/corporate_filters/router.py:350:            ["Proveedor_Catalogo", "Compras_Proveedores", "Proveedores"],
/app/backend/modules/corporate_filters/router.py:351:            ["id_proveedor", "proveedor_id", "ProveedorID", "id"],
/app/backend/modules/corporate_filters/router.py:352:            ["nombre", "razon_social", "nombre_comercial", "Proveedor"],
/app/backend/modules/costos_margenes/repository_precios.py:626:    """Registra una entrada en el historial de la solicitud."""
/app/backend/modules/proveedores/service.py:2:EDARSA HUB - Proveedores Service
/app/backend/modules/proveedores/service.py:4:Lógica de negocio de proveedores.
/app/backend/modules/proveedores/service.py:7:class ProveedoresService:
/app/backend/modules/proveedores/__init__.py:1:# EDARSA HUB - Módulo de Proveedores
/app/backend/modules/proveedores/__init__.py:2:# Portal de proveedores, facturas, pagos y estados de cuenta
/app/backend/modules/proveedores/repository.py:2:EDARSA HUB - Proveedores Repository
/app/backend/modules/proveedores/repository.py:4:Acceso a datos de proveedores.
/app/backend/modules/proveedores/repository.py:7:class ProveedoresRepository:
/app/backend/modules/proveedores/routes.py:2:EDARSA HUB - Proveedores Routes
/app/backend/modules/proveedores/routes.py:4:Endpoints del portal de proveedores.
/app/backend/modules/proveedores/routes.py:6:NOTA: Los endpoints actuales están en routes/portal_proveedores.py y server.py.
/app/backend/modules/proveedores/routes.py:12:router = APIRouter(prefix="/proveedores", tags=["Proveedores"])
/app/backend/modules/proveedores/routes.py:14:# Endpoints a migrar desde portal_proveedores.py
/app/backend/modules/proveedores/schemas.py:2:EDARSA HUB - Proveedores Schemas
/app/backend/modules/proveedores/schemas.py:4:Modelos Pydantic para proveedores.
/app/backend/modules/rh/service.py:394:                "nomipaq": "Mapeo con nom10001 (empleados), nom10003 (conceptos), nom10007 (movimientos)",
/app/backend/modules/rh/service.py:865:    - NO se validan duplicados de entrada/salida en el mismo día
/app/backend/modules/rh/service.py:919:        Registra una entrada o salida.
/app/backend/modules/rh/service.py:922:        - NO se validan duplicados de entrada/salida en el mismo día
/app/backend/modules/rh/service.py:923:        - El tipo_registro ya fue validado por Pydantic (Entrada/Salida)
/app/backend/modules/rh/importador/aprobacion_service.py:607:    """Registra una entrada en la bitácora de importación."""
/app/backend/modules/rh/importador/repository.py:553:    Actualiza métricas de una entrada en la bitácora.
/app/backend/modules/rh/importador/routes.py:314:    # Crear entrada en bitácora
/app/backend/modules/rh/repository.py:1236:# - NO se validan duplicados de entrada/salida por día
/app/backend/modules/rh/repository.py:1340:    Registra una entrada o salida en el reloj checador.
/app/backend/modules/rh/repository.py:1345:    - NO se validan duplicados de entrada/salida en el mismo día
/app/backend/modules/rh/routes.py:557:# - NO se validan duplicados de entrada/salida en el mismo día
/app/backend/modules/rh/routes.py:612:    Registra una entrada o salida.
/app/backend/modules/rh/routes.py:616:    - tipo_registro: "Entrada" o "Salida" (validado)
/app/backend/modules/rh/routes.py:622:    - NO se validan duplicados de entrada/salida en el mismo día
/app/backend/modules/rh/schemas.py:535:# - Solo se permiten valores "Entrada" y "Salida"
/app/backend/modules/rh/schemas.py:536:# - NO se agregan validaciones de duplicados de entrada/salida por día
/app/backend/modules/rh/schemas.py:544:TIPOS_REGISTRO_ASISTENCIA = ["Entrada", "Salida"]
/app/backend/modules/rh/schemas.py:550:    tipo_registro: str = Field(..., description="Tipo de registro: Entrada o Salida")
/app/backend/modules/rh/schemas.py:556:        """Valida que tipo_registro sea 'Entrada' o 'Salida'."""
/app/backend/modules/rh/schemas.py:564:    Modelo para registrar entrada o salida.
/app/backend/modules/rh/schemas.py:567:    - NO se validan duplicados de entrada/salida en el mismo día
/app/backend/modules/inventarios/__init__.py:2:# Control de inventarios, movimientos y existencias
/app/backend/modules/inventarios/repository.py:9:- Datos sincronizados en tabla Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:26:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:56:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:74:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/consultas_sql/schemas.py:24:    modulo: Optional[str] = Field(None, description="Módulo: Ventas, Compras, etc.")
/app/backend/modules/catalogos/__init__.py:10:- Acceso contextual desde módulos nativos (RH, Compras, etc.)
/app/backend/modules/catalogos/__init__.py:16:- Compras (Estatus órdenes, recepciones, etc.)
/app/backend/modules/catalogos/__init__.py:17:- Inventarios (Tipos movimiento, etc.)
/app/backend/modules/catalogos/repository.py:227:    ('G02', 'Devoluciones, descuentos o bonificaciones', 1, 1),
/app/backend/modules/catalogos/routes.py:508:    (Generales, RH, Nómina, Compras, etc.) con información de cada catálogo.
/app/backend/modules/catalogos/schemas.py:27:            {"tabla": "Proveedor_Monedas", "nombre": "Monedas", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:58:    "compras": {
/app/backend/modules/catalogos/schemas.py:59:        "nombre": "Compras",
/app/backend/modules/catalogos/schemas.py:60:        "descripcion": "Catálogos del módulo de Compras",
/app/backend/modules/catalogos/schemas.py:63:            {"tabla": "Compras_Estatus", "nombre": "Estatus de Compras", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:64:            {"tabla": "Compras_OrdenesEstatus", "nombre": "Estatus de Órdenes", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:65:            {"tabla": "Compras_PedidosEstatus", "nombre": "Estatus de Pedidos", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:66:            {"tabla": "Compras_RecepcionesEstatus", "nombre": "Estatus de Recepciones", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:67:            {"tabla": "Compras_DocumentosFiscalesEstatus", "nombre": "Estatus Docs. Fiscales", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:68:            {"tabla": "Compras_ConciliacionSATEstatus", "nombre": "Estatus Conciliación SAT", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:69:            {"tabla": "Proveedor_TipoProveedor", "nombre": "Tipos de Proveedor", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:70:            {"tabla": "Proveedor_TipoContacto", "nombre": "Tipos de Contacto", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:71:            {"tabla": "Proveedor_TipoDocumento", "nombre": "Tipos de Documento", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:72:            {"tabla": "Proveedor_EstatusProveedor", "nombre": "Estatus de Proveedor", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:80:            {"tabla": "Inventario_TipoMovimiento", "nombre": "Tipos de Movimiento", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:195:    "Proveedor_Monedas": {
/app/backend/modules/catalogos/schemas.py:248:        "campos": ["TurnoID", "CodigoTurno", "Descripcion", "HoraEntrada", "HoraSalida", "ToleranciaMinutos", "Activo"],
/app/backend/modules/catalogos/schemas.py:249:        "campos_editables": ["CodigoTurno", "Descripcion", "HoraEntrada", "HoraSalida", "ToleranciaMinutos", "Activo"],
/app/backend/modules/catalogos/schemas.py:305:    # === COMPRAS / PROVEEDOR ===
/app/backend/modules/catalogos/schemas.py:306:    "Compras_Estatus": {
/app/backend/modules/catalogos/schemas.py:313:    "Compras_OrdenesEstatus": {
/app/backend/modules/catalogos/schemas.py:320:    "Compras_PedidosEstatus": {
/app/backend/modules/catalogos/schemas.py:327:    "Compras_RecepcionesEstatus": {
/app/backend/modules/catalogos/schemas.py:334:    "Compras_DocumentosFiscalesEstatus": {
/app/backend/modules/catalogos/schemas.py:341:    "Compras_ConciliacionSATEstatus": {
/app/backend/modules/catalogos/schemas.py:348:    "Proveedor_TipoProveedor": {
/app/backend/modules/catalogos/schemas.py:349:        "pk": "TipoProveedorID",
/app/backend/modules/catalogos/schemas.py:350:        "campos": ["TipoProveedorID", "Descripcion", "Activo"],
/app/backend/modules/catalogos/schemas.py:355:    "Proveedor_TipoContacto": {
/app/backend/modules/catalogos/schemas.py:362:    "Proveedor_TipoDocumento": {
/app/backend/modules/catalogos/schemas.py:369:    "Proveedor_EstatusProveedor": {
/app/backend/modules/catalogos/schemas.py:370:        "pk": "EstatusProveedorID",
/app/backend/modules/catalogos/schemas.py:371:        "campos": ["EstatusProveedorID", "Descripcion", "Activo"],
/app/backend/modules/catalogos/schemas.py:378:    "Inventario_TipoMovimiento": {
/app/backend/modules/catalogos/schemas.py:379:        "pk": "TipoMovimientoID",
/app/backend/modules/catalogos/schemas.py:380:        "campos": ["TipoMovimientoID", "Codigo", "Descripcion", "Naturaleza", "AfectaCostoPromedio", "Activo"],
/app/backend/modules/catalogos/schemas.py:497:        "campos": ["ConfiguracionTPVID", "SucursalID", "ProveedorTPV", "ComisionDebito", "ComisionCredito", "ComisionAmex", "ComisionInternacional", "AplicaIVAComision", "PorcentajeIVA", "DiasDepositoDebito", "DiasDepositoCredito", "DiasDepositoAmex", "DiasDepositoInternacional", "DiasDepositoEfectivo", "EfectivoFinDeSemanaLunes", "CuentaBancariaID", "NumeroAfiliacion", "TerminalID", "Activo"],
/app/backend/modules/catalogos/schemas.py:498:        "campos_editables": ["SucursalID", "ProveedorTPV", "ComisionDebito", "ComisionCredito", "ComisionAmex", "ComisionInternacional", "AplicaIVAComision", "PorcentajeIVA", "DiasDepositoDebito", "DiasDepositoCredito", "DiasDepositoAmex", "DiasDepositoInternacional", "DiasDepositoEfectivo", "EfectivoFinDeSemanaLunes", "CuentaBancariaID", "NumeroAfiliacion", "TerminalID", "Activo"],
/app/backend/modules/catalogos/schemas.py:499:        "campo_nombre": "ProveedorTPV",
/app/backend/modules/edge/motor_reglas_comerciales.py:100:                        "argumento_script": f"¡Alerta de estancamiento! Ofrece inmediatamente {row['nombre']} como entrada de alta velocidad."
/app/backend/modules/auth/routes.py:502:        'compras': (
/app/backend/modules/auth/routes.py:505:            'COMPRAS_DASHBOARD_VER' in context.permisos
/app/backend/modules/auth/schemas.py:114:    {"id": "compras", "nombre": "Compras", "descripcion": "Dashboard de compras, autorización, análisis"},
/app/backend/modules/auth/schemas.py:140:        "permisos": ["tablero_ejecutivo", "comercial", "compras", "inventarios", "dashboard_inventarios", "catalogo_sql", "alertas"],
/app/backend/modules/auth/schemas.py:146:        "permisos": ["comercial", "compras", "inventarios", "dashboard_inventarios"],
/app/backend/modules/comercial_v2/carga_historica_abril_2026.py:871:# PUNTO DE ENTRADA PRINCIPAL
/app/backend/modules/comercial_v2/carga_historica_24_meses.py:793:# PUNTO DE ENTRADA
/app/backend/modules/comercial_v2/schemas.py:55:# SCHEMAS DE ENTRADA (desde orígenes)
/app/backend/modules/tablajeria/ordenes_service.py:202:                        PorcentajeCostoAsignado, UnidadCodigo, GeneraMovimiento
/app/backend/modules/tablajeria/ordenes_service.py:218:                    not det['EsMerma']  # Mermas no generan movimiento de inventario directo
/app/backend/modules/tablajeria/ordenes_service.py:357:                        GeneraMovimiento
/app/backend/modules/tablajeria/fase6_service.py:23:class TipoMovimiento(str, Enum):
/app/backend/modules/tablajeria/fase6_service.py:25:    ENTRADA_DERIVADO = "ENTRADA_DERIVADO"
/app/backend/modules/tablajeria/fase6_service.py:229:        Movimientos:
/app/backend/modules/tablajeria/fase6_service.py:231:        2. ENTRADA_DERIVADO: Suma productos derivados al almacén
/app/backend/modules/tablajeria/fase6_service.py:235:            Dict con resumen de movimientos generados
/app/backend/modules/tablajeria/fase6_service.py:263:                return {"movimientos": 0, "mensaje": "Afectación automática deshabilitada"}
/app/backend/modules/tablajeria/fase6_service.py:265:            movimientos = []
/app/backend/modules/tablajeria/fase6_service.py:272:                    INSERT INTO Tablajeria_MovimientosInventario (
/app/backend/modules/tablajeria/fase6_service.py:273:                        MovimientoID, OrdenID, TipoMovimiento,
/app/backend/modules/tablajeria/fase6_service.py:276:                        FechaMovimiento, UsuarioID, Referencia
/app/backend/modules/tablajeria/fase6_service.py:279:                    mov_id, orden_id, TipoMovimiento.SALIDA_INSUMO.value,
/app/backend/modules/tablajeria/fase6_service.py:286:                movimientos.append({
/app/backend/modules/tablajeria/fase6_service.py:287:                    "tipo": TipoMovimiento.SALIDA_INSUMO.value,
/app/backend/modules/tablajeria/fase6_service.py:292:            # 2. ENTRADA_DERIVADO - Productos producidos
/app/backend/modules/tablajeria/fase6_service.py:293:            # Nota: OrdenesDetalle no tiene EsInventariable, usamos GeneraMovimiento y TipoDerivado
/app/backend/modules/tablajeria/fase6_service.py:297:                    CantidadReal, TipoDerivado, GeneraMovimiento
/app/backend/modules/tablajeria/fase6_service.py:299:                WHERE OrdenID = %s AND CantidadReal > 0 AND GeneraMovimiento = 1
/app/backend/modules/tablajeria/fase6_service.py:306:                    INSERT INTO Tablajeria_MovimientosInventario (
/app/backend/modules/tablajeria/fase6_service.py:307:                        MovimientoID, OrdenID, TipoMovimiento,
/app/backend/modules/tablajeria/fase6_service.py:310:                        FechaMovimiento, UsuarioID, Referencia
/app/backend/modules/tablajeria/fase6_service.py:313:                    mov_id, orden_id, TipoMovimiento.ENTRADA_DERIVADO.value,
/app/backend/modules/tablajeria/fase6_service.py:319:                movimientos.append({
/app/backend/modules/tablajeria/fase6_service.py:320:                    "tipo": TipoMovimiento.ENTRADA_DERIVADO.value,
/app/backend/modules/tablajeria/fase6_service.py:329:                    INSERT INTO Tablajeria_MovimientosInventario (
/app/backend/modules/tablajeria/fase6_service.py:330:                        MovimientoID, OrdenID, TipoMovimiento,
/app/backend/modules/tablajeria/fase6_service.py:333:                        FechaMovimiento, UsuarioID, Referencia
/app/backend/modules/tablajeria/fase6_service.py:336:                    mov_id, orden_id, TipoMovimiento.SALIDA_MERMA.value,
/app/backend/modules/tablajeria/fase6_service.py:342:                movimientos.append({
/app/backend/modules/tablajeria/fase6_service.py:343:                    "tipo": TipoMovimiento.SALIDA_MERMA.value,
/app/backend/modules/tablajeria/fase6_service.py:352:                    MovimientoInventarioGenerado = 1,
/app/backend/modules/tablajeria/fase6_service.py:359:            logger.info(f"[FASE6] Inventario afectado para orden {orden['FolioOrden']}: {len(movimientos)} movimientos")
/app/backend/modules/tablajeria/fase6_service.py:364:                "movimientos_generados": len(movimientos),
/app/backend/modules/tablajeria/fase6_service.py:365:                "detalle": movimientos
/app/backend/modules/tablajeria/fase6_service.py:447:                    GeneraMovimiento
/app/backend/modules/tablajeria/fase6_service.py:524:                # Inferir EsInventariable: si no es MERMA y genera movimiento
/app/backend/modules/tablajeria/fase6_service.py:525:                es_inventariable = det['TipoDerivado'] != 'MERMA' and det.get('GeneraMovimiento', True)
/app/backend/modules/tablajeria/fase6_service.py:656:                f"Entrada producción {costeo['FolioOrden']}",
/app/backend/modules/finanzas/utils_bancarios.py:22:    Entrada: '0123456789'
/app/backend/modules/finanzas/utils_bancarios.py:36:    Entrada: '012345678901234567'
/app/backend/modules/finanzas/cuentas_por_pagar.py:4:Módulo para gestionar facturas pendientes de pago agrupadas por proveedor.
/app/backend/modules/finanzas/cuentas_por_pagar.py:13:2. Proveedor
/app/backend/modules/finanzas/cuentas_por_pagar.py:135:    proveedores = [
/app/backend/modules/finanzas/cuentas_por_pagar.py:155:    folio_entrada = 1000
/app/backend/modules/finanzas/cuentas_por_pagar.py:158:        proveedor = demo_choice(proveedores)
/app/backend/modules/finanzas/cuentas_por_pagar.py:163:        fecha_entrada = datetime.now() - timedelta(days=dias_atras)
/app/backend/modules/finanzas/cuentas_por_pagar.py:165:        fecha_vencimiento = fecha_entrada + timedelta(days=dias_credito)
/app/backend/modules/finanzas/cuentas_por_pagar.py:178:            "folio_entrada": f"ENT-{folio_entrada}",
/app/backend/modules/finanzas/cuentas_por_pagar.py:180:            "fecha_entrada": fecha_entrada.strftime("%Y-%m-%d"),
/app/backend/modules/finanzas/cuentas_por_pagar.py:191:            "tiene_pdf_entrada": demo_random() > 0.1,
/app/backend/modules/finanzas/cuentas_por_pagar.py:192:            "proveedor_id": proveedor["id"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:193:            "proveedor_nombre": proveedor["nombre"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:194:            "proveedor_rfc": proveedor["rfc"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:200:        folio_entrada += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:227:    proveedor_id: Optional[str] = None,
/app/backend/modules/finanzas/cuentas_por_pagar.py:228:    tipo_proveedor: Optional[str] = None,  # A=Alimentos, B=Bebidas, X=Otros
/app/backend/modules/finanzas/cuentas_por_pagar.py:242:    Filtros: sucursal, proveedor, tipo (A/B/X), fecha de corte, solo vencidas.
/app/backend/modules/finanzas/cuentas_por_pagar.py:243:    Agrupa por TIPO DE PROVEEDOR (A=Alimentos, B=Bebidas, X=Otros).
/app/backend/modules/finanzas/cuentas_por_pagar.py:268:                    tipo_proveedor=tipo_proveedor
/app/backend/modules/finanzas/cuentas_por_pagar.py:276:                    tipo = c.get('TipoProveedor', 'X')
/app/backend/modules/finanzas/cuentas_por_pagar.py:280:                    # FolioEntrada, FolioFactura, FechaVencimiento, FechaFactura, Referencia
/app/backend/modules/finanzas/cuentas_por_pagar.py:284:                        "proveedor_id": c.get('ProveedorID'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:285:                        "proveedor_nombre": c.get('ProveedorNombre', 'N/A'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:286:                        "proveedor_rfc": c.get('ProveedorRFC', ''),
/app/backend/modules/finanzas/cuentas_por_pagar.py:287:                        "tipo_proveedor": tipo,
/app/backend/modules/finanzas/cuentas_por_pagar.py:288:                        "tipo_proveedor_nombre": c.get('TipoProveedorNombre', 'OTROS'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:291:                        # Campos detallados desde tabla compras (SoftRestaurant)
/app/backend/modules/finanzas/cuentas_por_pagar.py:292:                        "folio_entrada": c.get('FolioEntrada') or '-',
/app/backend/modules/finanzas/cuentas_por_pagar.py:294:                        "fecha_entrada": c.get('FechaEntrada') if isinstance(c.get('FechaEntrada'), str) else (c.get('FechaEntrada').isoformat() if c.get('FechaEntrada') else None),
/app/backend/modules/finanzas/cuentas_por_pagar.py:348:                    proveedor_id=proveedor_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:371:                    # ABRIL 2026 - CLASIFICACIÓN MPRO por Grupo_Proveedor:
/app/backend/modules/finanzas/cuentas_por_pagar.py:372:                    # Gp_Cve_Grupo_Proveedor = '0001' → ALIMENTOS (A)
/app/backend/modules/finanzas/cuentas_por_pagar.py:373:                    # Gp_Cve_Grupo_Proveedor = '0002' → BEBIDAS (B)
/app/backend/modules/finanzas/cuentas_por_pagar.py:375:                    grupo_prov = str(c.get('GrupoProveedor', '') or '').strip()
/app/backend/modules/finanzas/cuentas_por_pagar.py:387:                    # FolioEntrada = Cxp_Documento
/app/backend/modules/finanzas/cuentas_por_pagar.py:390:                    folio_entrada = c.get('FolioEntrada') or c.get('CuentaPorPagarID', 'N/A')
/app/backend/modules/finanzas/cuentas_por_pagar.py:396:                        "proveedor_id": c.get('ProveedorID'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:397:                        "proveedor_nombre": c.get('ProveedorNombre') or f"Proveedor {c.get('ProveedorID')}",
/app/backend/modules/finanzas/cuentas_por_pagar.py:398:                        "proveedor_rfc": c.get('ProveedorRFC', ''),
/app/backend/modules/finanzas/cuentas_por_pagar.py:399:                        "tipo_proveedor": tipo_prov,
/app/backend/modules/finanzas/cuentas_por_pagar.py:400:                        "tipo_proveedor_nombre": tipo_prov_nombre,
/app/backend/modules/finanzas/cuentas_por_pagar.py:403:                        "folio_entrada": folio_entrada,
/app/backend/modules/finanzas/cuentas_por_pagar.py:405:                        "fecha_entrada": str(c.get('FechaEntrada', ''))[:10] if c.get('FechaEntrada') else None,
/app/backend/modules/finanzas/cuentas_por_pagar.py:428:        # 3. Si hay datos, APLICAR FILTROS y agrupar por TIPO DE PROVEEDOR (A, B, X)
/app/backend/modules/finanzas/cuentas_por_pagar.py:429:        # El frontend espera: { proveedor_id: "A", proveedor_nombre: "A - ALIMENTOS", facturas: [...] }
/app/backend/modules/finanzas/cuentas_por_pagar.py:430:        # El frontend luego reagrupa las facturas por proveedor_nombre dentro de cada categoría
/app/backend/modules/finanzas/cuentas_por_pagar.py:439:            # Agrupar por TIPO DE PROVEEDOR (A, B, X)
/app/backend/modules/finanzas/cuentas_por_pagar.py:441:            # - SoftRestaurant: Según clave del proveedor (A = ALIMENTOS, B = BEBIDAS, X = OTROS)
/app/backend/modules/finanzas/cuentas_por_pagar.py:442:            # - MPRO: Según Grupo_Proveedor (0001 = ALIMENTOS, 0002 = BEBIDAS, otros = OTROS)
/app/backend/modules/finanzas/cuentas_por_pagar.py:451:                tipo = factura.get('tipo_proveedor', 'X')
/app/backend/modules/finanzas/cuentas_por_pagar.py:456:                        "proveedor_id": tipo,
/app/backend/modules/finanzas/cuentas_por_pagar.py:457:                        "proveedor_nombre": f"{tipo} - {tipo_nombre}",
/app/backend/modules/finanzas/cuentas_por_pagar.py:458:                        "proveedor_rfc": "",
/app/backend/modules/finanzas/cuentas_por_pagar.py:475:            proveedores_ordenados = [tipos.get(t) for t in orden_tipos if t in tipos]
/app/backend/modules/finanzas/cuentas_por_pagar.py:478:                "total_saldo": sum(p["subtotal_saldo"] for p in proveedores_ordenados),
/app/backend/modules/finanzas/cuentas_por_pagar.py:479:                "total_importe": sum(p["subtotal_importe"] for p in proveedores_ordenados),
/app/backend/modules/finanzas/cuentas_por_pagar.py:480:                "total_proveedores": len(proveedores_ordenados),
/app/backend/modules/finanzas/cuentas_por_pagar.py:481:                "cantidad_facturas": sum(p["cantidad_facturas"] for p in proveedores_ordenados),
/app/backend/modules/finanzas/cuentas_por_pagar.py:482:                "cantidad_vencidas": sum(p["cantidad_vencidas"] for p in proveedores_ordenados)
/app/backend/modules/finanzas/cuentas_por_pagar.py:487:                "proveedores": proveedores_ordenados,
/app/backend/modules/finanzas/cuentas_por_pagar.py:500:                proveedor_id=proveedor_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:519:                        "proveedor_id": c.get('ProveedorID'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:520:                        "proveedor_nombre": c.get('ProveedorNombre') or c.get('ProveedorNombreComercial') or f"Proveedor {c.get('ProveedorID')}",
/app/backend/modules/finanzas/cuentas_por_pagar.py:521:                        "proveedor_rfc": c.get('ProveedorRFC'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:525:                        "folio_entrada": c.get('NumeroDocumento'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:528:                        "fecha_entrada": str(c.get('FechaDocumento', ''))[:10],
/app/backend/modules/finanzas/cuentas_por_pagar.py:530:                        "fecha_recepcion": str(c.get('FechaRecepcion', ''))[:10] if c.get('FechaRecepcion') else None,
/app/backend/modules/finanzas/cuentas_por_pagar.py:545:                        "ruta_pdf_entrada": None,
/app/backend/modules/finanzas/cuentas_por_pagar.py:550:                # Agrupar por proveedor
/app/backend/modules/finanzas/cuentas_por_pagar.py:551:                proveedores_dict = {}
/app/backend/modules/finanzas/cuentas_por_pagar.py:553:                    prov_id = f["proveedor_id"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:554:                    if prov_id not in proveedores_dict:
/app/backend/modules/finanzas/cuentas_por_pagar.py:555:                        proveedores_dict[prov_id] = {
/app/backend/modules/finanzas/cuentas_por_pagar.py:556:                            "proveedor_id": prov_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:557:                            "proveedor_nombre": f["proveedor_nombre"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:558:                            "proveedor_rfc": f["proveedor_rfc"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:567:                    proveedores_dict[prov_id]["facturas"].append(f)
/app/backend/modules/finanzas/cuentas_por_pagar.py:568:                    proveedores_dict[prov_id]["subtotal_importe"] += f["importe_total"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:569:                    proveedores_dict[prov_id]["subtotal_saldo"] += f["saldo"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:570:                    proveedores_dict[prov_id]["cantidad_facturas"] += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:572:                        proveedores_dict[prov_id]["cantidad_vencidas"] += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:574:                # Ordenar proveedores por saldo descendente
/app/backend/modules/finanzas/cuentas_por_pagar.py:575:                proveedores_list = sorted(
/app/backend/modules/finanzas/cuentas_por_pagar.py:576:                    proveedores_dict.values(),
/app/backend/modules/finanzas/cuentas_por_pagar.py:587:                    "proveedores": proveedores_list,
/app/backend/modules/finanzas/cuentas_por_pagar.py:594:                        "cantidad_proveedores": len(proveedores_list),
/app/backend/modules/finanzas/cuentas_por_pagar.py:602:                    "proveedores": [],
/app/backend/modules/finanzas/cuentas_por_pagar.py:610:                        "cantidad_proveedores": 0,
/app/backend/modules/finanzas/cuentas_por_pagar.py:626:    if proveedor_id:
/app/backend/modules/finanzas/cuentas_por_pagar.py:627:        facturas = [f for f in facturas if f["proveedor_id"] == proveedor_id]
/app/backend/modules/finanzas/cuentas_por_pagar.py:630:        facturas = [f for f in facturas if f["fecha_entrada"] <= fecha_corte]
/app/backend/modules/finanzas/cuentas_por_pagar.py:642:    # Agrupar por proveedor
/app/backend/modules/finanzas/cuentas_por_pagar.py:643:    proveedores_dict = {}
/app/backend/modules/finanzas/cuentas_por_pagar.py:645:        prov_id = f["proveedor_id"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:646:        if prov_id not in proveedores_dict:
/app/backend/modules/finanzas/cuentas_por_pagar.py:647:            proveedores_dict[prov_id] = {
/app/backend/modules/finanzas/cuentas_por_pagar.py:648:                "proveedor_id": prov_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:649:                "proveedor_nombre": f["proveedor_nombre"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:650:                "proveedor_rfc": f["proveedor_rfc"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:659:        proveedores_dict[prov_id]["facturas"].append(f)
/app/backend/modules/finanzas/cuentas_por_pagar.py:660:        proveedores_dict[prov_id]["subtotal_importe"] += f["importe_total"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:661:        proveedores_dict[prov_id]["subtotal_saldo"] += f["saldo"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:662:        proveedores_dict[prov_id]["subtotal_a_pagar"] += f["importe_a_pagar"] if f["decision_pago"] else 0
/app/backend/modules/finanzas/cuentas_por_pagar.py:663:        proveedores_dict[prov_id]["cantidad_facturas"] += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:665:            proveedores_dict[prov_id]["cantidad_vencidas"] += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:667:    # Ordenar facturas dentro de cada proveedor por fecha de vencimiento
/app/backend/modules/finanzas/cuentas_por_pagar.py:668:    for prov in proveedores_dict.values():
/app/backend/modules/finanzas/cuentas_por_pagar.py:671:    # Convertir a lista ordenada por nombre de proveedor
/app/backend/modules/finanzas/cuentas_por_pagar.py:672:    proveedores_list = sorted(proveedores_dict.values(), key=lambda x: x["proveedor_nombre"])
/app/backend/modules/finanzas/cuentas_por_pagar.py:675:    total_importe = sum(p["subtotal_importe"] for p in proveedores_list)
/app/backend/modules/finanzas/cuentas_por_pagar.py:676:    total_saldo = sum(p["subtotal_saldo"] for p in proveedores_list)
/app/backend/modules/finanzas/cuentas_por_pagar.py:677:    total_a_pagar = sum(p["subtotal_a_pagar"] for p in proveedores_list)
/app/backend/modules/finanzas/cuentas_por_pagar.py:678:    total_facturas = sum(p["cantidad_facturas"] for p in proveedores_list)
/app/backend/modules/finanzas/cuentas_por_pagar.py:679:    total_vencidas = sum(p["cantidad_vencidas"] for p in proveedores_list)
/app/backend/modules/finanzas/cuentas_por_pagar.py:682:        "proveedores": proveedores_list,
/app/backend/modules/finanzas/cuentas_por_pagar.py:692:            "cantidad_proveedores": len(proveedores_list)
/app/backend/modules/finanzas/cuentas_por_pagar.py:696:            "proveedor_id": proveedor_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:991:@router.get("/proveedores")
/app/backend/modules/finanzas/cuentas_por_pagar.py:992:async def listar_proveedores_con_saldo(
/app/backend/modules/finanzas/cuentas_por_pagar.py:997:    """Lista proveedores que tienen facturas pendientes - CONECTADO A MPRO"""
/app/backend/modules/finanzas/cuentas_por_pagar.py:1003:            proveedores = await mpro_repo.get_resumen_por_proveedor(sucursal_id=sucursal_id)
/app/backend/modules/finanzas/cuentas_por_pagar.py:1005:            if proveedores:
/app/backend/modules/finanzas/cuentas_por_pagar.py:1008:                    "proveedores": [
/app/backend/modules/finanzas/cuentas_por_pagar.py:1010:                            "proveedor_id": p.get('ProveedorID'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:1011:                            "proveedor_nombre": p.get('ProveedorNombre') or f"Proveedor {p.get('ProveedorID')}",
/app/backend/modules/finanzas/cuentas_por_pagar.py:1012:                            "proveedor_rfc": p.get('ProveedorRFC'),
/app/backend/modules/finanzas/cuentas_por_pagar.py:1016:                        for p in proveedores
/app/backend/modules/finanzas/cuentas_por_pagar.py:1020:            logging.error(f"Error obteniendo proveedores CxP de MPRO: {e}")
/app/backend/modules/finanzas/cuentas_por_pagar.py:1032:    proveedores = {}
/app/backend/modules/finanzas/cuentas_por_pagar.py:1034:        prov_id = f["proveedor_id"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:1035:        if prov_id not in proveedores:
/app/backend/modules/finanzas/cuentas_por_pagar.py:1036:            proveedores[prov_id] = {
/app/backend/modules/finanzas/cuentas_por_pagar.py:1037:                "proveedor_id": prov_id,
/app/backend/modules/finanzas/cuentas_por_pagar.py:1038:                "proveedor_nombre": f["proveedor_nombre"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:1039:                "proveedor_rfc": f["proveedor_rfc"],
/app/backend/modules/finanzas/cuentas_por_pagar.py:1043:        proveedores[prov_id]["total_saldo"] += f["saldo"]
/app/backend/modules/finanzas/cuentas_por_pagar.py:1044:        proveedores[prov_id]["cantidad_facturas"] += 1
/app/backend/modules/finanzas/cuentas_por_pagar.py:1048:        "proveedores": sorted(proveedores.values(), key=lambda x: x["proveedor_nombre"])
/app/backend/modules/finanzas/repository_real.py:346:        proveedor_id: Optional[int] = None,
/app/backend/modules/finanzas/repository_real.py:354:        Incluye JOIN con Proveedor_Catalogo para nombre y RFC.
/app/backend/modules/finanzas/repository_real.py:358:            proveedor_id: Filtrar por proveedor
/app/backend/modules/finanzas/repository_real.py:371:        if proveedor_id:
/app/backend/modules/finanzas/repository_real.py:372:            where_clauses.append(f"c.ProveedorID = {proveedor_id}")
/app/backend/modules/finanzas/repository_real.py:386:                c.ProveedorID,
/app/backend/modules/finanzas/repository_real.py:387:                p.RazonSocial AS ProveedorNombre,
/app/backend/modules/finanzas/repository_real.py:388:                p.NombreComercial AS ProveedorNombreComercial,
/app/backend/modules/finanzas/repository_real.py:389:                p.RFC AS ProveedorRFC,
/app/backend/modules/finanzas/repository_real.py:390:                p.DiasCredito AS ProveedorDiasCredito,
/app/backend/modules/finanzas/repository_real.py:396:                c.FechaRecepcion,
/app/backend/modules/finanzas/repository_real.py:411:            LEFT JOIN Proveedor_Catalogo p ON c.ProveedorID = p.ProveedorID
/app/backend/modules/finanzas/repository_real.py:474:    async def get_cxp_por_proveedor(
/app/backend/modules/finanzas/repository_real.py:479:        Obtiene cuentas por pagar agrupadas por proveedor.
/app/backend/modules/finanzas/repository_real.py:490:                c.ProveedorID,
/app/backend/modules/finanzas/repository_real.py:498:            GROUP BY c.ProveedorID
/app/backend/modules/finanzas/repository_real.py:524:                c.ProveedorTPV,
/app/backend/modules/finanzas/sql_query_worker_secure.py:16:ENTRADA (stdin JSON):
/app/backend/modules/finanzas/repository_cortes_z.py:321:        where_clauses = ["c.tipo_movimiento = 'CIERRE'"]
/app/backend/modules/finanzas/ingresos.py:21:3. Proveedor de terminales: NetPay
/app/backend/modules/finanzas/ingresos.py:299:_movimientos_banco_db = []  # Para estados de cuenta cargados
/app/backend/modules/finanzas/ingresos.py:311:class ConciliarMovimiento(BaseModel):
/app/backend/modules/finanzas/ingresos.py:313:    movimiento_banco_id: int
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
/app/backend/modules/finanzas/ingresos.py:736:        "proveedor": "NetPay",
/app/backend/modules/finanzas/repository.py:30:        Proveedor VARCHAR(100) DEFAULT 'NetPay',
/app/backend/modules/finanzas/repository.py:92:-- Facturas pendientes de pago a proveedores
/app/backend/modules/finanzas/repository.py:99:        ProveedorID INT,
/app/backend/modules/finanzas/repository.py:100:        ProveedorNombre NVARCHAR(200) NOT NULL,
/app/backend/modules/finanzas/repository.py:101:        ProveedorRFC VARCHAR(20),
/app/backend/modules/finanzas/repository.py:103:        FolioEntrada VARCHAR(50),
/app/backend/modules/finanzas/repository.py:105:        FechaEntrada DATE NOT NULL,
/app/backend/modules/finanzas/repository.py:119:        RutaPDFEntrada VARCHAR(500),
/app/backend/modules/finanzas/repository.py:131:    CREATE INDEX IX_CxP_Proveedor ON FIN_Cuentas_Por_Pagar(ProveedorID);
/app/backend/modules/finanzas/repository.py:139:-- TABLA: FIN_Movimientos_Banco
/app/backend/modules/finanzas/repository.py:140:-- Movimientos bancarios para conciliación
/app/backend/modules/finanzas/repository.py:142:IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[FIN_Movimientos_Banco]') AND type in (N'U'))
/app/backend/modules/finanzas/repository.py:144:    CREATE TABLE [dbo].[FIN_Movimientos_Banco] (
/app/backend/modules/finanzas/repository.py:145:        MovimientoID INT IDENTITY(1,1) PRIMARY KEY,
/app/backend/modules/finanzas/repository.py:148:        FechaMovimiento DATE NOT NULL,
/app/backend/modules/finanzas/repository.py:156:        TipoConciliacion VARCHAR(50),  -- efectivo, tarjetas, proveedor
/app/backend/modules/finanzas/repository.py:167:    PRINT 'Tabla FIN_Movimientos_Banco creada';
/app/backend/modules/finanzas/repository.py:181:    INSERT INTO FIN_Configuracion_TPV (SucursalID, TipoTarjeta, ComisionPorcentaje, DiasDeposito, IVAPorcentaje, Proveedor)
/app/backend/modules/finanzas/repository.py:239:                ComisionPorcentaje, DiasDeposito, IVAPorcentaje, Proveedor
/app/backend/modules/finanzas/repository.py:252:                c.IVAPorcentaje, c.Proveedor
/app/backend/modules/finanzas/repository.py:280:        proveedor_id: Optional[int] = None,
/app/backend/modules/finanzas/repository.py:289:        if proveedor_id:
/app/backend/modules/finanzas/repository.py:290:            where_clauses.append(f"ProveedorID = {proveedor_id}")
/app/backend/modules/finanzas/repository.py:292:            where_clauses.append(f"FechaEntrada <= '{fecha_corte}'")
/app/backend/modules/finanzas/repository.py:301:                f.ProveedorID, f.ProveedorNombre, f.ProveedorRFC,
/app/backend/modules/finanzas/repository.py:302:                f.FolioEntrada, f.FolioFactura,
/app/backend/modules/finanzas/repository.py:303:                CONVERT(VARCHAR, f.FechaEntrada, 23) as FechaEntrada,
/app/backend/modules/finanzas/repository.py:310:                CASE WHEN f.RutaPDFEntrada IS NOT NULL THEN 1 ELSE 0 END as TienePDFEntrada
/app/backend/modules/finanzas/repository.py:314:            ORDER BY f.ProveedorNombre, f.FechaVencimiento
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:159:                schema['col_tipo_movimiento'] = 'idtipomovtocaja'
/app/backend/modules/finanzas/propinas_tpv/schema_detector.py:239:        col_tipo = schema.get('col_tipo_movimiento', 'idtipomovtocaja')
/app/backend/modules/finanzas/repository_softrestaurant.py:12:AGRUPACIÓN DE PROVEEDORES:
/app/backend/modules/finanzas/repository_softrestaurant.py:17:Formato nombre proveedor: "[XXXX] TYYYY NOMBRE" donde T es el tipo (A, B, X)
/app/backend/modules/finanzas/repository_softrestaurant.py:66:def get_tipo_proveedor(nombre_proveedor: str) -> str:
/app/backend/modules/finanzas/repository_softrestaurant.py:68:    Extrae el tipo de proveedor del nombre.
/app/backend/modules/finanzas/repository_softrestaurant.py:82:    if not nombre_proveedor:
/app/backend/modules/finanzas/repository_softrestaurant.py:85:    nombre = nombre_proveedor.strip()
/app/backend/modules/finanzas/repository_softrestaurant.py:159:    Consulta múltiples sucursales y agrupa por tipo de proveedor.
/app/backend/modules/finanzas/repository_softrestaurant.py:308:        tipo_proveedor: Optional[str] = None,
/app/backend/modules/finanzas/repository_softrestaurant.py:315:        - Cada compra es un documento INDIVIDUAL con su propio saldo
/app/backend/modules/finanzas/repository_softrestaurant.py:316:        - El saldo se calcula: total - SUM(pagosproveedores.abono)
/app/backend/modules/finanzas/repository_softrestaurant.py:317:        - Ordenado por folio de entrada ASCENDENTE
/app/backend/modules/finanzas/repository_softrestaurant.py:318:        - Match por folio de compra (único por documento)
/app/backend/modules/finanzas/repository_softrestaurant.py:323:            tipo_proveedor: A=Alimentos, B=Bebidas, X=Otros
/app/backend/modules/finanzas/repository_softrestaurant.py:345:            # DICIEMBRE 2026: Query principal - Compras con saldo individual calculado
/app/backend/modules/finanzas/repository_softrestaurant.py:350:            # SoftRestaurant marca compras como cancelado=1 cuando están cerradas/históricas
/app/backend/modules/finanzas/repository_softrestaurant.py:351:            # Solo mostrar compras activas (no canceladas) con saldo pendiente
/app/backend/modules/finanzas/repository_softrestaurant.py:352:            query_compras_con_saldo = f"""
/app/backend/modules/finanzas/repository_softrestaurant.py:354:                    c.idcompra,
/app/backend/modules/finanzas/repository_softrestaurant.py:355:                    c.folio AS FolioEntrada,
/app/backend/modules/finanzas/repository_softrestaurant.py:357:                    c.fechaaplicacion AS FechaEntrada,
/app/backend/modules/finanzas/repository_softrestaurant.py:361:                    c.idproveedor AS ProveedorID,
/app/backend/modules/finanzas/repository_softrestaurant.py:364:                    p.nombre AS ProveedorNombre,
/app/backend/modules/finanzas/repository_softrestaurant.py:365:                    p.rfc AS ProveedorRFC
/app/backend/modules/finanzas/repository_softrestaurant.py:366:                FROM compras c
/app/backend/modules/finanzas/repository_softrestaurant.py:367:                LEFT JOIN proveedores p ON c.idproveedor = p.idproveedor
/app/backend/modules/finanzas/repository_softrestaurant.py:368:                LEFT JOIN pagosproveedores pp ON pp.foliocompra = c.idcompra
/app/backend/modules/finanzas/repository_softrestaurant.py:370:                GROUP BY c.idcompra, c.folio, c.foliofactura, c.fechaaplicacion, c.fechafactura, 
/app/backend/modules/finanzas/repository_softrestaurant.py:371:                         c.fechavencimiento, c.referencia, c.idproveedor, c.total, p.nombre, p.rfc
/app/backend/modules/finanzas/repository_softrestaurant.py:376:            results_compras = await self._execute_query_subprocess(server_key, query_compras_con_saldo)
/app/backend/modules/finanzas/repository_softrestaurant.py:378:            if not results_compras:
/app/backend/modules/finanzas/repository_softrestaurant.py:379:                logging.warning(f"[SoftRestaurant] Sin compras con saldo para {server_key}")
/app/backend/modules/finanzas/repository_softrestaurant.py:382:            logging.info(f"[SoftRestaurant] {server_key}: {len(results_compras)} documentos con saldo > 0")
/app/backend/modules/finanzas/repository_softrestaurant.py:385:            # Cada compra es un documento ÚNICO con su propio saldo
/app/backend/modules/finanzas/repository_softrestaurant.py:388:            for c in results_compras:
/app/backend/modules/finanzas/repository_softrestaurant.py:389:                proveedor_nombre = str(c.get('ProveedorNombre', '') or '').strip()
/app/backend/modules/finanzas/repository_softrestaurant.py:390:                proveedor_id = str(c.get('ProveedorID', '') or '').strip()
/app/backend/modules/finanzas/repository_softrestaurant.py:392:                # Determinar tipo de proveedor desde el nombre
/app/backend/modules/finanzas/repository_softrestaurant.py:393:                tipo = get_tipo_proveedor(proveedor_nombre)
/app/backend/modules/finanzas/repository_softrestaurant.py:394:                if tipo_proveedor and tipo != tipo_proveedor:
/app/backend/modules/finanzas/repository_softrestaurant.py:398:                folio_entrada = str(c.get('FolioEntrada', '') or '').strip()
/app/backend/modules/finanzas/repository_softrestaurant.py:400:                fecha_entrada = c.get('FechaEntrada')
/app/backend/modules/finanzas/repository_softrestaurant.py:404:                proveedor_rfc = str(c.get('ProveedorRFC', '') or '').strip()
/app/backend/modules/finanzas/repository_softrestaurant.py:409:                if isinstance(fecha_entrada, str) and 'T' in fecha_entrada:
/app/backend/modules/finanzas/repository_softrestaurant.py:410:                    fecha_entrada = fecha_entrada.split('T')[0]
/app/backend/modules/finanzas/repository_softrestaurant.py:437:                cuenta_id = f"{server_key}_{folio_entrada}"
/app/backend/modules/finanzas/repository_softrestaurant.py:443:                    "ProveedorID": proveedor_id,
/app/backend/modules/finanzas/repository_softrestaurant.py:444:                    "ProveedorNombre": proveedor_nombre,
/app/backend/modules/finanzas/repository_softrestaurant.py:445:                    "ProveedorRFC": proveedor_rfc,
/app/backend/modules/finanzas/repository_softrestaurant.py:446:                    "TipoProveedor": tipo,
/app/backend/modules/finanzas/repository_softrestaurant.py:447:                    "TipoProveedorNombre": get_nombre_tipo(tipo),
/app/backend/modules/finanzas/repository_softrestaurant.py:448:                    "FolioEntrada": folio_entrada or None,
/app/backend/modules/finanzas/repository_softrestaurant.py:450:                    "FechaEntrada": fecha_entrada,
/app/backend/modules/finanzas/repository_softrestaurant.py:513:        """Obtiene resumen agrupado por tipo de proveedor (A, B, X)"""
/app/backend/modules/finanzas/repository_softrestaurant.py:518:            tipo = c.get('TipoProveedor', 'X')
/app/backend/modules/finanzas/repository_softrestaurant.py:521:                    "TipoProveedor": tipo,
/app/backend/modules/finanzas/repository_softrestaurant.py:523:                    "CantidadProveedores": 0,
/app/backend/modules/finanzas/repository_softrestaurant.py:525:                    "Proveedores": set()
/app/backend/modules/finanzas/repository_softrestaurant.py:527:            tipos[tipo]["Proveedores"].add(c.get('ProveedorNombre'))
/app/backend/modules/finanzas/repository_softrestaurant.py:534:                "TipoProveedor": data["TipoProveedor"],
/app/backend/modules/finanzas/repository_softrestaurant.py:536:                "CantidadProveedores": len(data["Proveedores"]),
/app/backend/modules/finanzas/test_conn_cienfuegos.py:1317:# PUNTO DE ENTRADA
/app/backend/modules/finanzas/sync_cortes_mpro.py:237:                Cc_Devolucion,
/app/backend/modules/finanzas/repository_mpro.py:8:- Proveedor: Catálogo de proveedores
/app/backend/modules/finanzas/repository_mpro.py:131:        proveedor_id: Optional[str] = None,
/app/backend/modules/finanzas/repository_mpro.py:141:            proveedor_id: Clave de proveedor
/app/backend/modules/finanzas/repository_mpro.py:156:        if proveedor_id:
/app/backend/modules/finanzas/repository_mpro.py:157:            where_clauses.append(f"c.Pv_Cve_Proveedor = '{proveedor_id}'")
/app/backend/modules/finanzas/repository_mpro.py:166:        # - Cxp_Documento = Folio Entrada (folio del documento de entrada de compra)
/app/backend/modules/finanzas/repository_mpro.py:167:        # - Cxp_Referencia = Folio Factura (número de factura del proveedor)
/app/backend/modules/finanzas/repository_mpro.py:170:        # - Cxp_Fecha = Fecha de entrada
/app/backend/modules/finanzas/repository_mpro.py:173:        # CLASIFICACIÓN MPRO por Grupo_Proveedor:
/app/backend/modules/finanzas/repository_mpro.py:174:        # - Gp_Cve_Grupo_Proveedor = '0001' → ALIMENTOS (A)
/app/backend/modules/finanzas/repository_mpro.py:175:        # - Gp_Cve_Grupo_Proveedor = '0002' → BEBIDAS (B)
/app/backend/modules/finanzas/repository_mpro.py:180:                c.Cxp_Documento as FolioEntrada,
/app/backend/modules/finanzas/repository_mpro.py:184:                c.Pv_Cve_Proveedor as ProveedorID,
/app/backend/modules/finanzas/repository_mpro.py:185:                p.Pv_Razon_Social as ProveedorNombre,
/app/backend/modules/finanzas/repository_mpro.py:186:                p.Pv_R_F_C as ProveedorRFC,
/app/backend/modules/finanzas/repository_mpro.py:187:                p.Gp_Cve_Grupo_Proveedor as GrupoProveedor,
/app/backend/modules/finanzas/repository_mpro.py:188:                c.Cxp_Fecha as FechaEntrada,
/app/backend/modules/finanzas/repository_mpro.py:197:            LEFT JOIN Proveedor p ON c.Pv_Cve_Proveedor = p.Pv_Cve_Proveedor
/app/backend/modules/finanzas/repository_mpro.py:223:    async def get_resumen_por_proveedor(self, sucursal_id: Optional[str] = None) -> List[Dict]:
/app/backend/modules/finanzas/repository_mpro.py:224:        """Obtiene resumen de CxP agrupado por proveedor"""
/app/backend/modules/finanzas/repository_mpro.py:237:                c.Pv_Cve_Proveedor as ProveedorID,
/app/backend/modules/finanzas/repository_mpro.py:238:                p.Pv_Razon_Social as ProveedorNombre,
/app/backend/modules/finanzas/repository_mpro.py:239:                p.Pv_R_F_C as ProveedorRFC,
/app/backend/modules/finanzas/repository_mpro.py:245:            LEFT JOIN Proveedor p ON c.Pv_Cve_Proveedor = p.Pv_Cve_Proveedor
/app/backend/modules/finanzas/repository_mpro.py:247:            GROUP BY c.Pv_Cve_Proveedor, p.Pv_Razon_Social, p.Pv_R_F_C
/app/backend/modules/finanzas/repository_mpro.py:320:    async def get_proveedores(self) -> List[Dict]:
```
## 3. Endpoints actuales relacionados
```text
/app/backend/modules/comercial/queries/mpro.py:14:- Requisicion_Compra: Requisiciones de compra
/app/backend/modules/comercial/queries/softrestaurant.py:67:    'compras',
/app/backend/modules/comercial/queries/softrestaurant.py:68:    'comprasmovtos',
/app/backend/modules/comercial/rentabilidad.py:38:            FROM dbo.Compras_Inventarios_Fisicos_Sync
/app/backend/modules/comercial/services/precios_vinos_service.py:31:    6-9. Fuentes adicionales (futuro: compras, proveedor, override)
/app/backend/modules/comercial/services/precios_vinos_service.py:239:    6-9. Fuentes adicionales (futuro: compras, proveedor, override)
/app/backend/modules/comercial/services/precios_vinos_service.py:299:    # Jerarquías 6-9: Futuras fuentes (compras, proveedor, override)
/app/backend/modules/hub/modulo_financiero_proyectos.py:31:            # Transacciones financieras vinculadas al proyecto (Ingresos, Compras, Gastos)
/app/backend/modules/hub/modulo_financiero_proyectos.py:46:    # INYECCIÓN DE FLUJOS (COMPRAS, GASTOS E INGRESOS)
/app/backend/modules/hub/modulo_financiero_proyectos.py:106:                "costo_compras_insumos": totales["COMPRA_INSUMO"],
/app/backend/modules/fase2_operativo/router.py:21:from .routes.automatizacion_compras_routes import router as automatizacion_compras_router
/app/backend/modules/fase2_operativo/router.py:111:    automatizacion_compras_router,
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:43:    "tareas_operativas_compras": "Operativo_TareasCompras",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:44:    "auditoria_compras_bitacora": "Operativo_BitacoraCompras",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:53:    # FASE B-P2-B: Automatización Compras
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:54:    "automatizaciones_operativas_compras": "Operativo_TareasCompras",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:55:    "automatizaciones_bitacora": "Operativo_BitacoraCompras",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:57:    "inventarios_fisicos_procesados": "Compras_Inventarios_Fisicos_Sync",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:730:            "Operativo_TareasCompras": "TareaID",
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:731:            "Operativo_BitacoraCompras": "BitacoraID",
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:2:EDARSA HUB - Automatización Operativa de Compras
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:15:- Operativo_TareasCompras (automatizaciones principales)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:16:- Operativo_BitacoraCompras (bitácora de acciones)
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:65:class AutomatizacionComprasService:
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:67:    Servicio de automatización operativa de compras.
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:84:        self._repo = SQLBaseRepository("automatizaciones_operativas_compras")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:88:        logger.info("[AUTO_COMPRAS] Inicializado con SQL → Operativo_TareasCompras")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:682:            manual_id = trigger_generar_manual_sync(self.db, automatizacion_id, modulo="compras")
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:694:def get_automatizacion_compras_service(db=None) -> AutomatizacionComprasService:
/app/backend/modules/fase2_operativo/services/automatizacion_compras_service.py:696:    return AutomatizacionComprasService(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:2:EDARSA HUB - Routes de Automatización Operativa de Compras
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:19:from modules.fase2_operativo.services.automatizacion_compras_service import (
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:20:    get_automatizacion_compras_service,
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:83:@router.post("/compras/detector/ejecutar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:126:@router.get("/compras/detector/estado")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:167:@router.get("/compras/tareas")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:188:    tareas = list(db.tareas_operativas_compras.find(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:199:@router.get("/compras/tareas/{tarea_id}")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:208:    tarea = db.tareas_operativas_compras.find_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:219:@router.post("/compras/tareas/{tarea_id}/completar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:235:    tarea = db.tareas_operativas_compras.find_one({"id": tarea_id})
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:244:    db.tareas_operativas_compras.update_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:259:@router.post("/compras/tareas/{tarea_id}/asignar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:271:    tarea = db.tareas_operativas_compras.find_one({"id": tarea_id})
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:277:    db.tareas_operativas_compras.update_one(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:295:@router.get("/compras/kpis")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:303:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:307:@router.get("/compras")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:318:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:326:@router.get("/compras/detector/bitacora")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:339:    bitacora = list(db.auditoria_compras_bitacora.find(
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:350:@router.get("/compras/pedidos-procesados")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:386:@router.get("/compras/{automatizacion_id}")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:394:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:403:@router.post("/compras/procesar")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:414:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:437:@router.post("/compras/{automatizacion_id}/gerencia")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:451:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:476:@router.post("/compras/{automatizacion_id}/tesoreria")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:489:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:513:@router.post("/compras/{automatizacion_id}/dias-objetivo")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:525:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:548:@router.post("/compras/{automatizacion_id}/parametros-consumo")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:575:    service = get_automatizacion_compras_service(db)
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:596:@router.get("/compras/{automatizacion_id}/bitacora")
/app/backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py:604:    service = get_automatizacion_compras_service(db)
/app/backend/modules/api_connections/routes.py:75:    tipo_uso: str = Field("Otro", description="Tipo de uso: Ventas del día, Inventario, Cortes, Compras, Otro")
/app/backend/modules/api_connections/universal_test_routes.py:25:- Módulos: Comercial, Tablero, KPIs, Inventarios, Compras, Finanzas, Operaciones
/app/backend/modules/corporate_filters/router.py:350:            ["Proveedor_Catalogo", "Compras_Proveedores", "Proveedores"],
/app/backend/modules/inventarios/repository.py:9:- Datos sincronizados en tabla Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:26:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:56:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/inventarios/repository.py:74:        FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/consultas_sql/schemas.py:24:    modulo: Optional[str] = Field(None, description="Módulo: Ventas, Compras, etc.")
/app/backend/modules/catalogos/__init__.py:10:- Acceso contextual desde módulos nativos (RH, Compras, etc.)
/app/backend/modules/catalogos/__init__.py:16:- Compras (Estatus órdenes, recepciones, etc.)
/app/backend/modules/catalogos/routes.py:508:    (Generales, RH, Nómina, Compras, etc.) con información de cada catálogo.
/app/backend/modules/catalogos/schemas.py:58:    "compras": {
/app/backend/modules/catalogos/schemas.py:59:        "nombre": "Compras",
/app/backend/modules/catalogos/schemas.py:60:        "descripcion": "Catálogos del módulo de Compras",
/app/backend/modules/catalogos/schemas.py:63:            {"tabla": "Compras_Estatus", "nombre": "Estatus de Compras", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:64:            {"tabla": "Compras_OrdenesEstatus", "nombre": "Estatus de Órdenes", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:65:            {"tabla": "Compras_PedidosEstatus", "nombre": "Estatus de Pedidos", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:66:            {"tabla": "Compras_RecepcionesEstatus", "nombre": "Estatus de Recepciones", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:67:            {"tabla": "Compras_DocumentosFiscalesEstatus", "nombre": "Estatus Docs. Fiscales", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:68:            {"tabla": "Compras_ConciliacionSATEstatus", "nombre": "Estatus Conciliación SAT", "nuevo": False},
/app/backend/modules/catalogos/schemas.py:305:    # === COMPRAS / PROVEEDOR ===
/app/backend/modules/catalogos/schemas.py:306:    "Compras_Estatus": {
/app/backend/modules/catalogos/schemas.py:313:    "Compras_OrdenesEstatus": {
/app/backend/modules/catalogos/schemas.py:320:    "Compras_PedidosEstatus": {
/app/backend/modules/catalogos/schemas.py:327:    "Compras_RecepcionesEstatus": {
/app/backend/modules/catalogos/schemas.py:334:    "Compras_DocumentosFiscalesEstatus": {
/app/backend/modules/catalogos/schemas.py:341:    "Compras_ConciliacionSATEstatus": {
/app/backend/modules/auth/routes.py:502:        'compras': (
/app/backend/modules/auth/routes.py:505:            'COMPRAS_DASHBOARD_VER' in context.permisos
/app/backend/modules/auth/schemas.py:114:    {"id": "compras", "nombre": "Compras", "descripcion": "Dashboard de compras, autorización, análisis"},
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
/app/backend/modules/tablajeria/fase6_service.py:248:                FROM Operaciones_Tablaje_Ordenes o
/app/backend/modules/tablajeria/fase6_service.py:293:            # Nota: OrdenesDetalle no tiene EsInventariable, usamos GeneraMovimiento y TipoDerivado
/app/backend/modules/tablajeria/fase6_service.py:298:                FROM Operaciones_Tablaje_OrdenesDetalle
/app/backend/modules/tablajeria/fase6_service.py:350:                UPDATE Operaciones_Tablaje_Ordenes SET
/app/backend/modules/tablajeria/fase6_service.py:411:                FROM Operaciones_Tablaje_Ordenes o
/app/backend/modules/tablajeria/fase6_service.py:442:            # Nota: OrdenesDetalle no tiene EsInventariable, se infiere de TipoDerivado
/app/backend/modules/tablajeria/fase6_service.py:448:                FROM Operaciones_Tablaje_OrdenesDetalle
/app/backend/modules/tablajeria/fase6_service.py:608:                JOIN Operaciones_Tablaje_Ordenes o ON c.OrdenID = o.OrdenID
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
/app/backend/modules/tablajeria/routes.py:897:@router.post("/ordenes/{orden_id}/fase6/procesar-cierre")
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
/app/backend/modules/finanzas/cuentas_por_pagar.py:291:                        # Campos detallados desde tabla compras (SoftRestaurant)
/app/backend/modules/finanzas/repository_softrestaurant.py:345:            # DICIEMBRE 2026: Query principal - Compras con saldo individual calculado
/app/backend/modules/finanzas/repository_softrestaurant.py:350:            # SoftRestaurant marca compras como cancelado=1 cuando están cerradas/históricas
/app/backend/modules/finanzas/repository_softrestaurant.py:351:            # Solo mostrar compras activas (no canceladas) con saldo pendiente
/app/backend/modules/finanzas/repository_softrestaurant.py:352:            query_compras_con_saldo = f"""
/app/backend/modules/finanzas/repository_softrestaurant.py:366:                FROM compras c
/app/backend/modules/finanzas/repository_softrestaurant.py:376:            results_compras = await self._execute_query_subprocess(server_key, query_compras_con_saldo)
/app/backend/modules/finanzas/repository_softrestaurant.py:378:            if not results_compras:
/app/backend/modules/finanzas/repository_softrestaurant.py:379:                logging.warning(f"[SoftRestaurant] Sin compras con saldo para {server_key}")
/app/backend/modules/finanzas/repository_softrestaurant.py:382:            logging.info(f"[SoftRestaurant] {server_key}: {len(results_compras)} documentos con saldo > 0")
/app/backend/modules/finanzas/repository_softrestaurant.py:388:            for c in results_compras:
/app/backend/modules/manuales_operativos/service.py:67:    async def generar_manual_auditoria_compras(
/app/backend/modules/manuales_operativos/service.py:74:        Genera un manual operativo para Auditoría de Compras.
/app/backend/modules/manuales_operativos/service.py:77:            proceso: Documento de automatizaciones_operativas_compras
/app/backend/modules/manuales_operativos/service.py:101:            nombre_proceso = f"Auditoría Operativa de Compras - {sucursal} - {almacen}"
/app/backend/modules/manuales_operativos/service.py:105:                f"Validar y auditar el proceso de compras para {sucursal}, "
/app/backend/modules/manuales_operativos/service.py:114:                f"Este proceso cubre la auditoría de compras del período "
/app/backend/modules/manuales_operativos/service.py:158:                "modulo": ModuloOrigen.COMPRAS.value,
/app/backend/modules/manuales_operativos/service.py:160:                "proceso_tipo": "auditoria_compras",
/app/backend/modules/manuales_operativos/triggers.py:11:    await trigger_generar_manual(db, proceso_id, modulo="compras")
/app/backend/modules/manuales_operativos/triggers.py:14:    trigger_generar_manual_sync(db_sync, proceso_id, modulo="compras")
/app/backend/modules/manuales_operativos/triggers.py:34:    modulo: str = "compras",
/app/backend/modules/manuales_operativos/triggers.py:45:        modulo: Módulo del proceso (compras, operaciones, etc.)
/app/backend/modules/manuales_operativos/triggers.py:61:        if modulo == "compras":
/app/backend/modules/manuales_operativos/triggers.py:62:            return await _generar_manual_compras(db, service, proceso_id)
/app/backend/modules/manuales_operativos/triggers.py:72:async def _generar_manual_compras(
/app/backend/modules/manuales_operativos/triggers.py:77:    """Genera manual para auditoría de compras."""
/app/backend/modules/manuales_operativos/triggers.py:80:    proceso = await db.automatizaciones_operativas_compras.find_one({"id": proceso_id})
/app/backend/modules/manuales_operativos/triggers.py:82:        logger.error(f"Proceso de compras no encontrado: {proceso_id}")
/app/backend/modules/manuales_operativos/triggers.py:112:    manual = await service.generar_manual_auditoria_compras(proceso, bitacora, usuarios)
/app/backend/modules/manuales_operativos/triggers.py:136:    # Buscar procesos de compras completados sin manual
/app/backend/modules/manuales_operativos/triggers.py:137:    cursor = db.automatizaciones_operativas_compras.find({
/app/backend/modules/manuales_operativos/triggers.py:150:        resultado = await _generar_manual_compras(db, service, proceso_id)
/app/backend/modules/manuales_operativos/triggers.py:163:    modulo: str = "compras"
/app/backend/modules/manuales_operativos/triggers.py:179:        if modulo == "compras":
/app/backend/modules/manuales_operativos/triggers.py:180:            return _generar_manual_compras_sync(db_sync, proceso_id)
/app/backend/modules/manuales_operativos/triggers.py:189:def _generar_manual_compras_sync(db_sync: PyMongoDatabase, proceso_id: str) -> Optional[str]:
/app/backend/modules/manuales_operativos/triggers.py:190:    """Genera manual para compras de forma síncrona."""
/app/backend/modules/manuales_operativos/triggers.py:207:    proceso = db_sync["automatizaciones_operativas_compras"].find_one({"id": proceso_id})
/app/backend/modules/manuales_operativos/triggers.py:236:    nombre_proceso = f"Auditoría Operativa de Compras - {sucursal} - {almacen}"
/app/backend/modules/manuales_operativos/triggers.py:239:        f"Validar y auditar el proceso de compras para {sucursal}, "
/app/backend/modules/manuales_operativos/triggers.py:246:        f"Este proceso cubre la auditoría de compras del período para la sucursal {sucursal}, almacén {almacen}. "
/app/backend/modules/manuales_operativos/triggers.py:353:        "modulo": ModuloOrigen.COMPRAS.value,
/app/backend/modules/manuales_operativos/triggers.py:355:        "proceso_tipo": "auditoria_compras",
/app/backend/modules/manuales_operativos/routes.py:44:    modulo: Optional[str] = Query(None, description="Filtrar por módulo (compras, operaciones, etc.)"),
/app/backend/modules/manuales_operativos/routes.py:54:    - modulo: compras, operaciones, finanzas, etc.
/app/backend/modules/manuales_operativos/routes.py:127:    modulo: str = Query(..., description="Módulo del proceso (compras, operaciones, etc.)"),
/app/backend/modules/manuales_operativos/routes.py:141:    if modulo == "compras":
/app/backend/modules/manuales_operativos/routes.py:143:        proceso = await _db.automatizaciones_operativas_compras.find_one({"id": proceso_id})
/app/backend/modules/manuales_operativos/routes.py:151:        manual = await service.generar_manual_auditoria_compras(proceso, bitacora)
/app/backend/modules/manuales_operativos/schemas.py:26:    COMPRAS = "compras"
/app/backend/modules/manuales_operativos/schemas.py:126:    proceso_tipo: str = Field(..., description="Tipo de proceso (auditoria_compras, etc.)")
/app/backend/modules/manuales_operativos/schemas.py:176:    # Eventos de Auditoría de Compras
/app/backend/modules/compras/service.py:2:EDARSA HUB - Compras Module Service
/app/backend/modules/compras/service.py:4:Lógica de negocio para el módulo de compras.
/app/backend/modules/compras/service.py:24:from modules.compras import repository as repo
/app/backend/modules/compras/service.py:25:from modules.compras.system_type_utils import (
/app/backend/modules/compras/service.py:29:    log_compras_adapter_selected,
/app/backend/modules/compras/service.py:30:    log_compras_query_result,
/app/backend/modules/compras/service.py:31:    log_compras_error,
/app/backend/modules/compras/service.py:60:            log_compras_adapter_selected("inventarios-fisicos", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:67:            log_compras_query_result("inventarios-fisicos", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:70:            log_compras_adapter_selected("inventarios-fisicos", server_id, system_type, "SR_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:76:            log_compras_query_result("inventarios-fisicos", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:80:            log_compras_error("inventarios-fisicos", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/modules/compras/service.py:103:        log_compras_error("inventarios-fisicos", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:113:    Obtiene pedidos/requisiciones vigentes.
/app/backend/modules/compras/service.py:117:    - Maneja resultado homologado de ComprasQueryResult
/app/backend/modules/compras/service.py:130:            log_compras_adapter_selected("pedidos-vigentes", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:132:            # MPRO retorna lista directamente (TODO: migrar a ComprasQueryResult)
/app/backend/modules/compras/service.py:134:            log_compras_query_result("pedidos-vigentes", server_id, "SUCCESS", len(data))
/app/backend/modules/compras/service.py:137:            log_compras_adapter_selected("pedidos-vigentes", server_id, system_type, "SR_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:142:                log_compras_query_result("pedidos-vigentes", server_id, "TABLE_NOT_FOUND", 0)
/app/backend/modules/compras/service.py:143:                logging.info(f"[COMPRAS] Pedidos no disponibles en {server['name']}: {query_result.message}")
/app/backend/modules/compras/service.py:147:                log_compras_error("pedidos-vigentes", server_id, query_result.status, query_result.message, system_type)
/app/backend/modules/compras/service.py:148:                logging.warning(f"[COMPRAS] Error en pedidos: {query_result.message}")
/app/backend/modules/compras/service.py:152:            log_compras_query_result("pedidos-vigentes", server_id, "SUCCESS", len(data))
/app/backend/modules/compras/service.py:155:            log_compras_error("pedidos-vigentes", server_id, "UNSUPPORTED_SYSTEM_TYPE", f"system_type={system_type}", system_type)
/app/backend/modules/compras/service.py:180:        log_compras_error("pedidos-vigentes", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:186:# PARÁMETROS DE COMPRAS
/app/backend/modules/compras/service.py:191:    Obtiene los parámetros de compras para un servidor/sucursal.
/app/backend/modules/compras/service.py:194:    params = await repo.get_compras_params(server_id, sucursal)
/app/backend/modules/compras/service.py:215:    Guarda los parámetros de compras para un servidor/sucursal.
/app/backend/modules/compras/service.py:217:    await repo.save_compras_params(server_id, sucursal, params)
/app/backend/modules/compras/service.py:239:            log_compras_adapter_selected("detalle-factura", server_id, system_type, "MPRO_ADAPTER")
/app/backend/modules/compras/service.py:241:            log_compras_query_result("detalle-factura", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:255:        log_compras_adapter_selected("detalle-factura", server_id, system_type, "NO_ADAPTER_AVAILABLE")
/app/backend/modules/compras/service.py:264:        log_compras_error("detalle-factura", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/service.py:300:            log_compras_adapter_selected("facturas-proveedor", server_id, system_type, "MPRO_ADAPTER", sucursal_id)
/app/backend/modules/compras/service.py:302:            log_compras_query_result("facturas-proveedor", server_id, "SUCCESS", len(result))
/app/backend/modules/compras/service.py:317:        log_compras_adapter_selected("facturas-proveedor", server_id, system_type, "NO_ADAPTER_AVAILABLE")
/app/backend/modules/compras/service.py:326:        log_compras_error("facturas-proveedor", server_id, "QUERY_ERROR", str(e), system_type)
/app/backend/modules/compras/repository_compras_sql.py:2:EDARSA HUB - Compras Module SQL Repository
/app/backend/modules/compras/repository_compras_sql.py:4:Repositorio SQL para parámetros de compras en EDARSAHUB.
/app/backend/modules/compras/repository_compras_sql.py:6:FASE: COMPRAS-MONGO-001-F1 (Mayo 2026)
/app/backend/modules/compras/repository_compras_sql.py:7:- Migración de compras_params de MongoDB a EDARSAHUB SQL
/app/backend/modules/compras/repository_compras_sql.py:8:- Tabla destino: Compras_Parametros_Sucursal
/app/backend/modules/compras/repository_compras_sql.py:13:- Reemplaza funciones get_compras_params y save_compras_params de MongoDB
/app/backend/modules/compras/repository_compras_sql.py:57:DDL_COMPRAS_PARAMETROS_SUCURSAL = """
/app/backend/modules/compras/repository_compras_sql.py:58:-- Tabla: Compras_Parametros_Sucursal
/app/backend/modules/compras/repository_compras_sql.py:59:-- Almacena parámetros de configuración de compras por servidor/sucursal
/app/backend/modules/compras/repository_compras_sql.py:60:-- Reemplaza colección MongoDB: compras_params
/app/backend/modules/compras/repository_compras_sql.py:62:IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Compras_Parametros_Sucursal]') AND type in (N'U'))
/app/backend/modules/compras/repository_compras_sql.py:64:    CREATE TABLE [dbo].[Compras_Parametros_Sucursal] (
/app/backend/modules/compras/repository_compras_sql.py:85:        CONSTRAINT [UQ_Compras_Parametros_Server_Sucursal] UNIQUE ([ServerID], [SucursalID])
/app/backend/modules/compras/repository_compras_sql.py:89:    CREATE INDEX [IX_Compras_Parametros_ServerID] ON [dbo].[Compras_Parametros_Sucursal] ([ServerID]);
/app/backend/modules/compras/repository_compras_sql.py:90:    CREATE INDEX [IX_Compras_Parametros_SucursalID] ON [dbo].[Compras_Parametros_Sucursal] ([SucursalID]);
/app/backend/modules/compras/repository_compras_sql.py:91:    CREATE INDEX [IX_Compras_Parametros_Activo] ON [dbo].[Compras_Parametros_Sucursal] ([Activo]) WHERE [Activo] = 1;
/app/backend/modules/compras/repository_compras_sql.py:93:    PRINT 'Tabla Compras_Parametros_Sucursal creada exitosamente';
/app/backend/modules/compras/repository_compras_sql.py:97:    PRINT 'Tabla Compras_Parametros_Sucursal ya existe';
/app/backend/modules/compras/repository_compras_sql.py:104:    Asegura que la tabla Compras_Parametros_Sucursal exista en EDARSAHUB.
/app/backend/modules/compras/repository_compras_sql.py:113:        cursor.execute(DDL_COMPRAS_PARAMETROS_SUCURSAL)
/app/backend/modules/compras/repository_compras_sql.py:117:        logger.info("[COMPRAS_SQL] Tabla Compras_Parametros_Sucursal verificada/creada")
/app/backend/modules/compras/repository_compras_sql.py:118:        return "Tabla Compras_Parametros_Sucursal creada/verificada exitosamente"
/app/backend/modules/compras/repository_compras_sql.py:120:        logger.error(f"[COMPRAS_SQL] Error creando tabla: {e}")
/app/backend/modules/compras/repository_compras_sql.py:125:# FUNCIONES CRUD - PARÁMETROS DE COMPRAS
/app/backend/modules/compras/repository_compras_sql.py:128:def get_compras_params_sql(server_id: str, sucursal: str) -> Optional[Dict]:
/app/backend/modules/compras/repository_compras_sql.py:130:    Obtiene los parámetros de compras desde EDARSAHUB SQL.
/app/backend/modules/compras/repository_compras_sql.py:132:    REEMPLAZA: get_compras_params() de MongoDB
/app/backend/modules/compras/repository_compras_sql.py:157:            FROM Compras_Parametros_Sucursal
/app/backend/modules/compras/repository_compras_sql.py:185:                '_table': 'Compras_Parametros_Sucursal'
/app/backend/modules/compras/repository_compras_sql.py:188:            logger.debug(f"[COMPRAS_SQL] Parámetros encontrados para {server_id}/{sucursal}")
/app/backend/modules/compras/repository_compras_sql.py:191:        logger.debug(f"[COMPRAS_SQL] No hay parámetros configurados para {server_id}/{sucursal}")
/app/backend/modules/compras/repository_compras_sql.py:195:        logger.error(f"[COMPRAS_SQL] Error obteniendo parámetros: {e}")
/app/backend/modules/compras/repository_compras_sql.py:201:def save_compras_params_sql(server_id: str, sucursal: str, params: Dict, usuario: str = None) -> bool:
/app/backend/modules/compras/repository_compras_sql.py:203:    Guarda los parámetros de compras en EDARSAHUB SQL.
/app/backend/modules/compras/repository_compras_sql.py:206:    REEMPLAZA: save_compras_params() de MongoDB
/app/backend/modules/compras/repository_compras_sql.py:234:            MERGE Compras_Parametros_Sucursal AS target
/app/backend/modules/compras/repository_compras_sql.py:266:        logger.info(f"[COMPRAS_SQL] Parámetros guardados para {server_id}/{sucursal}")
/app/backend/modules/compras/repository_compras_sql.py:270:        logger.error(f"[COMPRAS_SQL] Error guardando parámetros: {e}")
/app/backend/modules/compras/repository_compras_sql.py:274:def get_all_compras_params_sql() -> List[Dict]:
/app/backend/modules/compras/repository_compras_sql.py:276:    Obtiene todos los parámetros de compras configurados.
/app/backend/modules/compras/repository_compras_sql.py:298:            FROM Compras_Parametros_Sucursal
/app/backend/modules/compras/repository_compras_sql.py:334:        logger.error(f"[COMPRAS_SQL] Error listando parámetros: {e}")
/app/backend/modules/compras/repository_compras_sql.py:338:def delete_compras_params_sql(server_id: str, sucursal: str) -> bool:
/app/backend/modules/compras/repository_compras_sql.py:340:    Elimina (soft delete) parámetros de compras.
/app/backend/modules/compras/repository_compras_sql.py:354:            UPDATE Compras_Parametros_Sucursal
/app/backend/modules/compras/repository_compras_sql.py:366:        logger.info(f"[COMPRAS_SQL] Parámetros eliminados para {server_id}/{sucursal}")
/app/backend/modules/compras/repository_compras_sql.py:370:        logger.error(f"[COMPRAS_SQL] Error eliminando parámetros: {e}")
/app/backend/modules/compras/repository_compras_sql.py:380:    'get_compras_params_sql',
/app/backend/modules/compras/repository_compras_sql.py:381:    'save_compras_params_sql',
/app/backend/modules/compras/repository_compras_sql.py:382:    'get_all_compras_params_sql',
/app/backend/modules/compras/repository_compras_sql.py:383:    'delete_compras_params_sql',
/app/backend/modules/compras/__init__.py:2:EDARSA HUB - Compras Module
/app/backend/modules/compras/__init__.py:4:Módulo de compras, pedidos e inventarios.
/app/backend/modules/compras/__init__.py:17:    from modules.compras import init_compras_module
/app/backend/modules/compras/__init__.py:18:    init_compras_module(db)
/app/backend/modules/compras/__init__.py:20:NOTA: Los endpoints complejos (calculo-pedido, auditoria-operativa, dashboard)
/app/backend/modules/compras/__init__.py:25:from modules.compras.schemas import (
/app/backend/modules/compras/__init__.py:32:    AnalisisComprasRequest,
/app/backend/modules/compras/__init__.py:34:from modules.compras.system_type_utils import (
/app/backend/modules/compras/__init__.py:36:    ComprasStatus,
/app/backend/modules/compras/__init__.py:41:    ComprasResponse,
/app/backend/modules/compras/__init__.py:42:    log_compras_adapter_selected,
/app/backend/modules/compras/__init__.py:43:    log_compras_query_result,
/app/backend/modules/compras/__init__.py:44:    log_compras_error,
/app/backend/modules/compras/__init__.py:46:from modules.compras.repository import init_compras_repository
/app/backend/modules/compras/__init__.py:51:    from modules.compras.routes import router
/app/backend/modules/compras/__init__.py:55:def init_compras_module(database) -> None:
/app/backend/modules/compras/__init__.py:57:    Inicializa el módulo de compras con la conexión a MongoDB.
/app/backend/modules/compras/__init__.py:62:    init_compras_repository(database)
/app/backend/modules/compras/__init__.py:75:    'init_compras_module',
/app/backend/modules/compras/__init__.py:83:    'AnalisisComprasRequest',
/app/backend/modules/compras/__init__.py:86:    'ComprasStatus',
/app/backend/modules/compras/__init__.py:91:    'ComprasResponse',
/app/backend/modules/compras/__init__.py:92:    'log_compras_adapter_selected',
/app/backend/modules/compras/__init__.py:93:    'log_compras_query_result',
/app/backend/modules/compras/__init__.py:94:    'log_compras_error',
/app/backend/modules/compras/eventos_compras.py:2:EDARSA HUB - Sistema de Eventos de Compras
/app/backend/modules/compras/eventos_compras.py:51:POLLING_INTERVAL_SECONDS = int(os.environ.get('COMPRAS_POLLING_INTERVAL', '120'))
/app/backend/modules/compras/eventos_compras.py:67:    REQUISICIONES = "REQUISICIONES"
/app/backend/modules/compras/eventos_compras.py:71:class EventoCompras:
/app/backend/modules/compras/eventos_compras.py:72:    """Estructura de un evento de compras."""
/app/backend/modules/compras/eventos_compras.py:112:    def dispatch(self, evento: EventoCompras) -> bool:
/app/backend/modules/compras/eventos_compras.py:117:    def get_pending_events(self, limit: int = 100) -> List[EventoCompras]:
/app/backend/modules/compras/eventos_compras.py:150:    def dispatch(self, evento: EventoCompras) -> bool:
/app/backend/modules/compras/eventos_compras.py:159:                INSERT INTO Compras_Eventos_Pendientes (
/app/backend/modules/compras/eventos_compras.py:192:                FROM Compras_Eventos_Pendientes
/app/backend/modules/compras/eventos_compras.py:234:                UPDATE Compras_Eventos_Pendientes
/app/backend/modules/compras/eventos_compras.py:326:                FROM Compras_Sync_Checkpoint
/app/backend/modules/compras/eventos_compras.py:369:                MERGE Compras_Sync_Checkpoint AS target
/app/backend/modules/compras/eventos_compras.py:406:                FROM Compras_Sync_Checkpoint
/app/backend/modules/compras/eventos_compras.py:514:                    evento = EventoCompras(
/app/backend/modules/compras/eventos_compras.py:550:    def detectar_nuevas_requisiciones(
/app/backend/modules/compras/eventos_compras.py:557:        Detecta requisiciones nuevas desde el último checkpoint.
/app/backend/modules/compras/eventos_compras.py:563:        checkpoint = self.checkpoint_mgr.get_checkpoint(server_id, SyncType.REQUISICIONES)
/app/backend/modules/compras/eventos_compras.py:588:                        FROM ordenescompra
/app/backend/modules/compras/eventos_compras.py:596:                        FROM ordenescompra
/app/backend/modules/compras/eventos_compras.py:624:                    evento = EventoCompras(
/app/backend/modules/compras/eventos_compras.py:647:                    server_id, server_name, SyncType.REQUISICIONES,
/app/backend/modules/compras/eventos_compras.py:651:            logger.info(f"[DETECTOR] Requisiciones {server_name}: {nuevos} nuevos, {eventos_generados} eventos")
/app/backend/modules/compras/eventos_compras.py:655:            logger.error(f"[DETECTOR] Error detectando requisiciones en {server_name}: {e}")
/app/backend/modules/compras/eventos_compras.py:724:    def dispatch(self, evento: EventoCompras) -> bool:
/app/backend/modules/compras/eventos_compras.py:728:    def get_pending_events(self, limit: int = 100) -> List[EventoCompras]:
/app/backend/modules/compras/system_type_utils.py:2:EDARSA HUB - Compras System Type Utilities
/app/backend/modules/compras/system_type_utils.py:41:# ESTADOS DE RESPUESTA ESPECÍFICOS DE COMPRAS
/app/backend/modules/compras/system_type_utils.py:44:class ComprasStatus(str, Enum):
/app/backend/modules/compras/system_type_utils.py:45:    """Estados de respuesta para endpoints de Compras."""
/app/backend/modules/compras/system_type_utils.py:60:# ENVELOPE DE RESPUESTA DE COMPRAS
/app/backend/modules/compras/system_type_utils.py:64:class ComprasResponse:
/app/backend/modules/compras/system_type_utils.py:65:    """Envelope estándar de respuesta para endpoints de Compras."""
/app/backend/modules/compras/system_type_utils.py:84:    def success(cls, data: List[Dict], meta: Dict = None, warnings: List[str] = None) -> "ComprasResponse":
/app/backend/modules/compras/system_type_utils.py:87:        return cls(status=ComprasStatus.SUCCESS.value, data=data, meta=_meta, warnings=warnings or [])
/app/backend/modules/compras/system_type_utils.py:90:    def no_data(cls, meta: Dict = None, message: str = "No hay datos para los filtros seleccionados") -> "ComprasResponse":
/app/backend/modules/compras/system_type_utils.py:93:        return cls(status=ComprasStatus.NO_DATA.value, data=[], meta=_meta, warnings=[message])
/app/backend/modules/compras/system_type_utils.py:96:    def unsupported_system(cls, system_type: str, meta: Dict = None, endpoint: str = "") -> "ComprasResponse":
/app/backend/modules/compras/system_type_utils.py:98:            status=ComprasStatus.UNSUPPORTED_SYSTEM_TYPE.value,
/app/backend/modules/compras/system_type_utils.py:106:    def not_available(cls, system_type: str, feature: str, meta: Dict = None) -> "ComprasResponse":
/app/backend/modules/compras/system_type_utils.py:108:            status=ComprasStatus.NOT_AVAILABLE_FOR_SYSTEM.value,
/app/backend/modules/compras/system_type_utils.py:116:    def source_unreachable(cls, meta: Dict = None, error_detail: str = None) -> "ComprasResponse":
/app/backend/modules/compras/system_type_utils.py:118:            status=ComprasStatus.SOURCE_UNREACHABLE.value,
/app/backend/modules/compras/system_type_utils.py:130:    def query_error(cls, meta: Dict = None, error_detail: str = None) -> "ComprasResponse":
/app/backend/modules/compras/system_type_utils.py:132:            status=ComprasStatus.QUERY_ERROR.value,
/app/backend/modules/compras/system_type_utils.py:144:    def configuration_missing(cls, meta: Dict = None, detail: str = None) -> "ComprasResponse":
/app/backend/modules/compras/system_type_utils.py:146:            status=ComprasStatus.CONFIGURATION_MISSING.value,
/app/backend/modules/compras/system_type_utils.py:159:# LOGGING HELPERS ESPECÍFICOS DE COMPRAS
/app/backend/modules/compras/system_type_utils.py:162:def log_compras_adapter_selected(
/app/backend/modules/compras/system_type_utils.py:170:    """Log para selección de adapter de Compras."""
/app/backend/modules/compras/system_type_utils.py:172:        f"[COMPRAS][ADAPTER_SELECTED] endpoint={endpoint} "
/app/backend/modules/compras/system_type_utils.py:181:def log_compras_query_result(
/app/backend/modules/compras/system_type_utils.py:188:    """Log para resultado de query de Compras."""
/app/backend/modules/compras/system_type_utils.py:191:        f"[COMPRAS][QUERY_RESULT] endpoint={endpoint} "
/app/backend/modules/compras/system_type_utils.py:197:def log_compras_error(
/app/backend/modules/compras/system_type_utils.py:204:    """Log para errores de Compras."""
/app/backend/modules/compras/system_type_utils.py:206:        f"[COMPRAS][ERROR] endpoint={endpoint} "
/app/backend/modules/compras/system_type_utils.py:231:    # Específicos de Compras
/app/backend/modules/compras/system_type_utils.py:232:    'ComprasStatus',
/app/backend/modules/compras/system_type_utils.py:233:    'ComprasResponse',
/app/backend/modules/compras/system_type_utils.py:234:    'log_compras_adapter_selected',
/app/backend/modules/compras/system_type_utils.py:235:    'log_compras_query_result',
/app/backend/modules/compras/system_type_utils.py:236:    'log_compras_error',
/app/backend/modules/compras/repository.py:2:EDARSA HUB - Compras Module Repository
/app/backend/modules/compras/repository.py:4:Acceso a datos para el módulo de compras.
/app/backend/modules/compras/repository.py:9:FASE COMPRAS-MONGO-001-F1 (Mayo 2026):
/app/backend/modules/compras/repository.py:10:- Parámetros de compras migrados de MongoDB a EDARSAHUB SQL
/app/backend/modules/compras/repository.py:11:- Tabla: Compras_Parametros_Sucursal
/app/backend/modules/compras/repository.py:19:NOTA: Las funciones get_db(), init_compras_repository(), etc. permanecen
/app/backend/modules/compras/repository.py:21:Los parámetros de compras YA NO usan estas funciones.
/app/backend/modules/compras/repository.py:35:# BLINDAJE: RESULTADO HOMOLOGADO PARA QUERIES DE COMPRAS
/app/backend/modules/compras/repository.py:39:class ComprasQueryResult:
/app/backend/modules/compras/repository.py:40:    """Resultado homologado para queries del módulo de compras."""
/app/backend/modules/compras/repository.py:78:def init_compras_repository(database) -> None:
/app/backend/modules/compras/repository.py:88:        logger.warning("[COMPRAS_REPO] Inicializado en modo STUB - funcionalidad MongoDB limitada")
/app/backend/modules/compras/repository.py:101:        raise RuntimeError("Compras repository not initialized. Call init_compras_repository(db) first.")
/app/backend/modules/compras/repository.py:154:# PARÁMETROS DE COMPRAS (MIGRADO A EDARSAHUB SQL - Mayo 2026)
/app/backend/modules/compras/repository.py:156:# FASE: COMPRAS-MONGO-001-F1
/app/backend/modules/compras/repository.py:158:# Tabla destino: Compras_Parametros_Sucursal
/app/backend/modules/compras/repository.py:160:async def get_compras_params(server_id: str, sucursal: str) -> Optional[Dict]:
/app/backend/modules/compras/repository.py:162:    Obtiene los parámetros de compras para un servidor/sucursal.
/app/backend/modules/compras/repository.py:173:    from modules.compras.repository_compras_sql import get_compras_params_sql
/app/backend/modules/compras/repository.py:174:    return get_compras_params_sql(server_id, sucursal)
/app/backend/modules/compras/repository.py:177:async def save_compras_params(server_id: str, sucursal: str, params: Dict) -> None:
/app/backend/modules/compras/repository.py:179:    Guarda o actualiza los parámetros de compras.
/app/backend/modules/compras/repository.py:188:    from modules.compras.repository_compras_sql import save_compras_params_sql
/app/backend/modules/compras/repository.py:189:    success = save_compras_params_sql(server_id, sucursal, params)
/app/backend/modules/compras/repository.py:191:        logger.error(f"[COMPRAS_REPO] Error guardando parámetros en SQL para {server_id}/{sucursal}")
/app/backend/modules/compras/repository.py:193:        logger.info(f"[COMPRAS_REPO] Parámetros guardados en EDARSAHUB SQL para {server_id}/{sucursal}")
/app/backend/modules/compras/repository.py:261:    Obtiene pedidos/requisiciones vigentes de MPRO.
/app/backend/modules/compras/repository.py:290:def query_pedidos_vigentes_sr(server: Dict) -> ComprasQueryResult:
/app/backend/modules/compras/repository.py:301:        logging.info(f"[COMPRAS] Tabla 'pedidocompra' no existe en {server['name']} - operación no soportada")
/app/backend/modules/compras/repository.py:302:        return ComprasQueryResult(
/app/backend/modules/compras/repository.py:338:            return ComprasQueryResult(
/app/backend/modules/compras/repository.py:345:            return ComprasQueryResult(
/app/backend/modules/compras/repository.py:353:        logging.error(f"[COMPRAS] Error en query_pedidos_vigentes_sr: {e}")
/app/backend/modules/compras/repository.py:357:            return ComprasQueryResult(
/app/backend/modules/compras/repository.py:364:        return ComprasQueryResult(
/app/backend/modules/compras/repository.py:485:    'init_compras_repository',
/app/backend/modules/compras/repository.py:488:    'get_compras_params',
/app/backend/modules/compras/repository.py:489:    'save_compras_params',
/app/backend/modules/compras/historical_kpis_repository.py:2:EDARSA HUB - Compras Historical KPIs Repository
/app/backend/modules/compras/historical_kpis_repository.py:4:Repositorio para UPSERT idempotente de KPIs históricos de Compras
/app/backend/modules/compras/historical_kpis_repository.py:8:Tabla destino: Compras_KPIs_Historico
/app/backend/modules/compras/historical_kpis_repository.py:12:- PEDIDO: Pedidos/requisiciones por fecha
/app/backend/modules/compras/historical_kpis_repository.py:61:    """Verifica si la tabla Compras_KPIs_Historico existe."""
/app/backend/modules/compras/historical_kpis_repository.py:67:            WHERE object_id = OBJECT_ID(N'[dbo].[Compras_KPIs_Historico]') 
/app/backend/modules/compras/historical_kpis_repository.py:79:    """Crea la tabla Compras_KPIs_Historico si no existe."""
/app/backend/modules/compras/historical_kpis_repository.py:85:        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Compras_KPIs_Historico]') AND type in (N'U'))
/app/backend/modules/compras/historical_kpis_repository.py:87:            CREATE TABLE [dbo].[Compras_KPIs_Historico] (
/app/backend/modules/compras/historical_kpis_repository.py:107:                [oc_ordenes_count] INT DEFAULT 0,
/app/backend/modules/compras/historical_kpis_repository.py:124:            CREATE UNIQUE INDEX IX_Compras_KPIs_Unique 
/app/backend/modules/compras/historical_kpis_repository.py:125:            ON [dbo].[Compras_KPIs_Historico] (server_id, sucursal_id, fecha, kpi_tipo);
/app/backend/modules/compras/historical_kpis_repository.py:128:            CREATE INDEX IX_Compras_KPIs_Fecha ON [dbo].[Compras_KPIs_Historico] (fecha);
/app/backend/modules/compras/historical_kpis_repository.py:129:            CREATE INDEX IX_Compras_KPIs_Tipo ON [dbo].[Compras_KPIs_Historico] (kpi_tipo);
/app/backend/modules/compras/historical_kpis_repository.py:137:        return "Tabla Compras_KPIs_Historico creada/verificada exitosamente"
/app/backend/modules/compras/historical_kpis_repository.py:143:def upsert_compras_kpi_historico(
/app/backend/modules/compras/historical_kpis_repository.py:155:    Realiza UPSERT de un registro de KPI de Compras en SQL Server.
/app/backend/modules/compras/historical_kpis_repository.py:165:        SELECT id FROM Compras_KPIs_Historico 
/app/backend/modules/compras/historical_kpis_repository.py:174:            UPDATE Compras_KPIs_Historico SET
/app/backend/modules/compras/historical_kpis_repository.py:183:                oc_ordenes_count = %s,
/app/backend/modules/compras/historical_kpis_repository.py:203:                kpi_data.get('oc_ordenes_count', 0),
/app/backend/modules/compras/historical_kpis_repository.py:219:            INSERT INTO Compras_KPIs_Historico (
/app/backend/modules/compras/historical_kpis_repository.py:223:                oc_ordenes_count, oc_total_monto, oc_proveedores_count,
/app/backend/modules/compras/historical_kpis_repository.py:236:                kpi_data.get('oc_ordenes_count', 0),
/app/backend/modules/compras/historical_kpis_repository.py:249:        logger.error(f"Error en upsert Compras KPI: {e}")
/app/backend/modules/compras/sync_service.py:2:COMPRAS SYNC SERVICE - Sincronización de Inventarios y Requisiciones a EDARSAHUB
/app/backend/modules/compras/sync_service.py:8:- Compras_Inventarios_Fisicos_Sync: Inventarios físicos sincronizados
/app/backend/modules/compras/sync_service.py:9:- Compras_Requisiciones_Sync: Requisiciones/pedidos sincronizados
/app/backend/modules/compras/sync_service.py:10:- Compras_Sync_Log: Log de sincronizaciones
/app/backend/modules/compras/sync_service.py:67:            FROM Compras_Inventarios_Fisicos_Sync
/app/backend/modules/compras/sync_service.py:109:def obtener_requisiciones_sync(
/app/backend/modules/compras/sync_service.py:116:    Obtiene requisiciones/pedidos DESDE EDARSAHUB (sincronizados).
/app/backend/modules/compras/sync_service.py:129:            FROM Compras_Requisiciones_Sync
/app/backend/modules/compras/sync_service.py:158:        logger.info(f"[SYNC-READ] Requisiciones: {len(rows)} registros desde EDARSAHUB")
/app/backend/modules/compras/sync_service.py:162:        logger.error(f"[SYNC-READ] Error obteniendo requisiciones: {e}")
/app/backend/modules/compras/sync_service.py:258:            UPDATE Compras_Inventarios_Fisicos_Sync 
/app/backend/modules/compras/sync_service.py:268:                    INSERT INTO Compras_Inventarios_Fisicos_Sync
/app/backend/modules/compras/sync_service.py:300:def sync_requisiciones_from_server(
/app/backend/modules/compras/sync_service.py:306:    Sincroniza requisiciones/pedidos desde un servidor físico a EDARSAHUB.
/app/backend/modules/compras/sync_service.py:315:    logger.info(f"[SYNC] Iniciando sync requisiciones: {unidad_codigo} ({system_type})")
/app/backend/modules/compras/sync_service.py:355:                    (SELECT COUNT(*) FROM ordenescompramov WHERE idOrdenCompra = OC.idOrdenCompra) as total_productos,
/app/backend/modules/compras/sync_service.py:363:                FROM ordenescompra OC
/app/backend/modules/compras/sync_service.py:391:            UPDATE Compras_Requisiciones_Sync 
/app/backend/modules/compras/sync_service.py:401:                    INSERT INTO Compras_Requisiciones_Sync
/app/backend/modules/compras/sync_service.py:428:        logger.info(f"[SYNC] Requisiciones sincronizadas: {records_synced} de {len(rows)}")
/app/backend/modules/compras/sync_service.py:432:        logger.error(f"[SYNC] Error sync requisiciones {unidad_codigo}: {e}")
/app/backend/modules/compras/sync_service.py:451:            INSERT INTO Compras_Sync_Log
/app/backend/modules/compras/sync_service.py:471:            SELECT TOP 1 * FROM Compras_Sync_Log
/app/backend/modules/compras/repository_pedidos_sql.py:4:COMPRAS-MONGO-001-F2: Migración de MongoDB a EDARSAHUB SQL
/app/backend/modules/compras/repository_pedidos_sql.py:8:- tareas_operativas_compras → Compras_TareasOperativas (nueva)
/app/backend/modules/compras/repository_pedidos_sql.py:9:- auditoria_compras_bitacora → Compras_Bitacora_Jobs (nueva)
/app/backend/modules/compras/repository_pedidos_sql.py:266:# TAREAS OPERATIVAS DE COMPRAS
/app/backend/modules/compras/repository_pedidos_sql.py:268:# Reemplaza: db['tareas_operativas_compras']
/app/backend/modules/compras/repository_pedidos_sql.py:270:# Para tareas completas, usar Compras_Eventos_Pendientes
/app/backend/modules/compras/repository_pedidos_sql.py:288:    REEMPLAZA: db['tareas_operativas_compras'].insert_one()
/app/backend/modules/compras/repository_pedidos_sql.py:290:    NOTA: Para tareas complejas, usar tabla Compras_Eventos_Pendientes.
/app/backend/modules/compras/repository_pedidos_sql.py:297:        # Verificar si existe tabla Compras_Eventos_Pendientes
/app/backend/modules/compras/repository_pedidos_sql.py:315:        # Intentar insertar en Compras_Eventos_Pendientes si existe
/app/backend/modules/compras/repository_pedidos_sql.py:318:            INSERT INTO Compras_Eventos_Pendientes (
/app/backend/modules/compras/repository_pedidos_sql.py:334:            logger.warning(f"[PEDIDOS_SQL] No se pudo insertar en Compras_Eventos_Pendientes: {e}")
/app/backend/modules/compras/repository_pedidos_sql.py:350:    REEMPLAZA: db['tareas_operativas_compras'].find()
/app/backend/modules/compras/repository_pedidos_sql.py:364:        FROM Compras_Eventos_Pendientes
/app/backend/modules/compras/repository_pedidos_sql.py:404:# Reemplaza: db['auditoria_compras_bitacora']
/app/backend/modules/compras/repository_pedidos_sql.py:415:    REEMPLAZA: db['auditoria_compras_bitacora'].insert_one()
/app/backend/modules/compras/routes.py:2:EDARSA HUB - Compras Module Routes
/app/backend/modules/compras/routes.py:4:Endpoints del módulo de compras.
/app/backend/modules/compras/routes.py:9:Los endpoints de compras tienen lógica de negocio compleja (~2000 líneas).
/app/backend/modules/compras/routes.py:13:   - GET /compras/parametros/{server_id} (lectura de config)
/app/backend/modules/compras/routes.py:14:   - POST /compras/parametros (escritura de config)
/app/backend/modules/compras/routes.py:17:   - Todos los demás endpoints de compras permanecen en server.py
/app/backend/modules/compras/routes.py:29:from modules.compras import service
/app/backend/modules/compras/routes.py:30:from modules.compras.schemas import ParametrosCompra
/app/backend/modules/compras/routes.py:33:router = APIRouter(tags=["compras"])
/app/backend/modules/compras/routes.py:37:# PARÁMETROS DE COMPRAS (Migrado - lógica simple)
/app/backend/modules/compras/routes.py:42:# @router.get("/compras/parametros/{server_id}")
/app/backend/modules/compras/routes.py:45:# @router.post("/compras/parametros")
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
/app/backend/modules/compras/routes.py:64:# - POST /compras/auditoria-operativa (~710 líneas)
/app/backend/modules/compras/routes.py:65:# - POST /compras/analisis (~140 líneas)
/app/backend/modules/compras/routes.py:66:# - POST /compras/productos-para-captura
/app/backend/modules/compras/routes.py:67:# - POST /compras/detalle-movimientos
/app/backend/modules/compras/routes.py:68:# - POST /compras/detalle-consumos
/app/backend/modules/compras/schemas.py:2:EDARSA HUB - Compras Module Schemas
/app/backend/modules/compras/schemas.py:4:Modelos Pydantic para el módulo de compras.
/app/backend/modules/compras/schemas.py:8:- Schemas de pedidos, auditoría operativa, análisis de compras
/app/backend/modules/compras/schemas.py:39:    """Request para auditoría operativa de compras."""
/app/backend/modules/compras/schemas.py:50:    folios_requisiciones: Optional[List[str]] = None  # Múltiples requisiciones
/app/backend/modules/compras/schemas.py:53:    solo_skus_requisicion: bool = True  # Por defecto solo muestra SKUs de las requisiciones
/app/backend/modules/compras/schemas.py:62:    folios_requisiciones: Optional[List[str]] = None
/app/backend/modules/compras/schemas.py:87:class AnalisisComprasRequest(BaseModel):
/app/backend/modules/compras/schemas.py:88:    """Request para análisis de compras."""
/app/backend/modules/compras/schemas.py:103:    'AnalisisComprasRequest',
/app/backend/scripts/run_historical_load_finanzas.py:329:    CxP = Compras - Pagos (compras.total - SUM(pagosproveedores.abono))
/app/backend/scripts/run_historical_load_finanzas.py:340:    # Query: CxP = Compras - Pagos, usando LEFT JOIN para evitar subconsultas en agregados
/app/backend/scripts/run_historical_load_finanzas.py:345:        SUM(c.total) as monto_compras,
/app/backend/scripts/run_historical_load_finanzas.py:348:    FROM compras c
/app/backend/scripts/run_historical_load_finanzas.py:378:                    "cxp_monto_total": float(row[2] or 0),  # Total compras
/app/backend/scripts/run_historical_load_finanzas.py:383:                    "cxp_saldo_pendiente": float(row[4] or 0)  # Saldo = Compras - Pagos
/app/backend/scripts/consolidado_general_sistema_comercial.py:401:    ("Compras", "compras", "ShoppingCart", "/compras", 5, "OPERADOR_EDARSA"),
/app/backend/scripts/create_tablajeria_rbac.py:69:            'codigo': 'tablajeria.ordenes',
/app/backend/scripts/create_tablajeria_rbac.py:73:            'ruta': '/tablajeria/ordenes',
/app/backend/scripts/create_tablajeria_rbac.py:239:            'tablajeria.ordenes': ['VER', 'CREAR', 'EDITAR', 'ELIMINAR', 'EXPORTAR', 'AUTORIZAR', 'CANCELAR', 'EJECUTAR'],
/app/backend/scripts/create_tablajeria_rbac.py:253:            'tablajeria.ordenes': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'AUTORIZAR', 'CANCELAR', 'EJECUTAR'],
/app/backend/scripts/create_tablajeria_rbac.py:267:            'tablajeria.ordenes': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'AUTORIZAR'],
/app/backend/scripts/create_tablajeria_rbac.py:281:            'tablajeria.ordenes': ['VER', 'CREAR', 'EDITAR', 'EJECUTAR', 'CANCELAR'],
/app/backend/scripts/create_tablajeria_rbac.py:295:            'tablajeria.ordenes': ['VER', 'CREAR', 'EJECUTAR'],
/app/backend/scripts/create_tablajeria_rbac.py:307:            'tablajeria.ordenes': ['VER', 'EJECUTAR'],
/app/backend/scripts/create_tablajeria_rbac.py:317:            'tablajeria.ordenes': ['VER', 'EXPORTAR'],
/app/backend/scripts/create_tablajeria_rbac.py:331:            'tablajeria.ordenes': ['VER'],
/app/backend/scripts/run_historical_load_compras.py:3:EDARSA HUB - Carga Histórica de Compras (24 Meses)
/app/backend/scripts/run_historical_load_compras.py:6:Script para ejecutar carga histórica de KPIs de Compras:
/app/backend/scripts/run_historical_load_compras.py:8:- Pedidos/Requisiciones
/app/backend/scripts/run_historical_load_compras.py:18:    python run_historical_load_compras.py --dry-run
/app/backend/scripts/run_historical_load_compras.py:21:    HISTORICAL_LOAD_CONFIRM=YES python run_historical_load_compras.py --run
/app/backend/scripts/run_historical_load_compras.py:46:    format='[%(asctime)s][%(levelname)s][COMPRAS_HISTORICAL] %(message)s',
/app/backend/scripts/run_historical_load_compras.py:60:COLLECTION_CHECKPOINTS = "compras_historical_load_checkpoints"
/app/backend/scripts/run_historical_load_compras.py:236:    # Query basada en el repository existente de compras
/app/backend/scripts/run_historical_load_compras.py:289:    """Consulta requisiciones de compra históricos de MPRO (Requisicion_Compra)."""
/app/backend/scripts/run_historical_load_compras.py:385:    """Consulta compras/entradas históricas de MPRO (Compra_Encabezado)."""
/app/backend/scripts/run_historical_load_compras.py:433:    """Consulta compras históricas de SoftRestaurant agrupados por fecha."""
/app/backend/scripts/run_historical_load_compras.py:438:    # Query simplificada - SoftRestaurant solo tiene tabla 'compras', no 'detallecompras'
/app/backend/scripts/run_historical_load_compras.py:445:    FROM compras c
/app/backend/scripts/run_historical_load_compras.py:484:def query_ordenes_historico_mpro(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
/app/backend/scripts/run_historical_load_compras.py:491:        COUNT(DISTINCT O.Oc_Folio) as ordenes_count,
/app/backend/scripts/run_historical_load_compras.py:515:                    "oc_ordenes_count": int(row[1] or 0),
/app/backend/scripts/run_historical_load_compras.py:526:def query_ordenes_historico_sr(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
/app/backend/scripts/run_historical_load_compras.py:527:    """Consulta órdenes de compra históricas de SoftRestaurant (tabla: ordenescompra)."""
/app/backend/scripts/run_historical_load_compras.py:532:    # SoftRestaurant usa tabla 'ordenescompra' con columna 'fechacaptura'
/app/backend/scripts/run_historical_load_compras.py:536:        COUNT(DISTINCT O.idordencompra) as ordenes_count,
/app/backend/scripts/run_historical_load_compras.py:539:    FROM ordenescompra O
/app/backend/scripts/run_historical_load_compras.py:562:                        "oc_ordenes_count": int(row[1] or 0),
/app/backend/scripts/run_historical_load_compras.py:590:    from modules.compras.historical_kpis_repository import upsert_compras_kpi_historico
/app/backend/scripts/run_historical_load_compras.py:638:                data = query_ordenes_historico_mpro(server, fecha_inicio, fecha_fin)
/app/backend/scripts/run_historical_load_compras.py:640:                data = query_ordenes_historico_sr(server, fecha_inicio, fecha_fin)
/app/backend/scripts/run_historical_load_compras.py:650:            result = upsert_compras_kpi_historico(
/app/backend/scripts/run_historical_load_compras.py:692:async def get_servers_for_compras(db) -> List[Dict]:
/app/backend/scripts/run_historical_load_compras.py:693:    """Obtiene servidores candidatos para carga histórica de compras."""
/app/backend/scripts/run_historical_load_compras.py:739:    parser = argparse.ArgumentParser(description='Carga Histórica de Compras')
/app/backend/scripts/run_historical_load_compras.py:765:    logger.info("CARGA HISTÓRICA COMPRAS - INICIO")
/app/backend/scripts/run_historical_load_compras.py:772:    from modules.compras.historical_kpis_repository import check_table_exists, create_table_if_not_exists
/app/backend/scripts/run_historical_load_compras.py:775:        logger.info("[MIGRATION] Creando tabla Compras_KPIs_Historico...")
/app/backend/scripts/run_historical_load_compras.py:784:    servers = await get_servers_for_compras(db)
/app/backend/scripts/run_historical_load_compras.py:839:    logger.info("CARGA HISTÓRICA COMPRAS - RESUMEN")
/app/backend/scripts/run_historical_load_compras.py:849:        "phase": "COMPRAS_HISTORICAL_LOAD",
/app/backend/scripts/run_historical_load_compras.py:855:    report_path = f"/app/docs/reports/compras_historical_load_{run_id[:8]}.json"
/app/backend/scripts/run_historical_load_24_months.py:501:        module: Módulo a cargar (comercial|finanzas|compras)
/app/backend/scripts/run_historical_load_24_months.py:770:        choices=["comercial", "finanzas", "compras", "all"],
/app/backend/tests/test_automatizacion_compras_fase4.py:2:EDARSA HUB - Tests de Automatización Operativa de Compras (Fase 4.1 y 4.2)
/app/backend/tests/test_automatizacion_compras_fase4.py:7:- POST /api/v2/automatizaciones/operativas/compras/detector/ejecutar
/app/backend/tests/test_automatizacion_compras_fase4.py:8:- GET /api/v2/automatizaciones/operativas/compras/detector/estado
/app/backend/tests/test_automatizacion_compras_fase4.py:9:- GET /api/v2/automatizaciones/operativas/compras/detector/bitacora
/app/backend/tests/test_automatizacion_compras_fase4.py:10:- GET /api/v2/automatizaciones/operativas/compras/pedidos-procesados
/app/backend/tests/test_automatizacion_compras_fase4.py:11:- GET /api/v2/automatizaciones/operativas/compras/tareas
/app/backend/tests/test_automatizacion_compras_fase4.py:12:- GET /api/v2/automatizaciones/operativas/compras/kpis
/app/backend/tests/test_automatizacion_compras_fase4.py:13:- GET /api/v2/automatizaciones/operativas/compras
/app/backend/tests/test_automatizacion_compras_fase4.py:17:- auditoria_compras_bitacora
/app/backend/tests/test_automatizacion_compras_fase4.py:18:- tareas_operativas_compras
/app/backend/tests/test_automatizacion_compras_fase4.py:38:class TestAutomatizacionComprasFase4:
/app/backend/tests/test_automatizacion_compras_fase4.py:66:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/estado"
/app/backend/tests/test_automatizacion_compras_fase4.py:85:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/estado"
/app/backend/tests/test_automatizacion_compras_fase4.py:106:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/ejecutar",
/app/backend/tests/test_automatizacion_compras_fase4.py:137:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/ejecutar",
/app/backend/tests/test_automatizacion_compras_fase4.py:157:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/ejecutar",
/app/backend/tests/test_automatizacion_compras_fase4.py:172:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/bitacora"
/app/backend/tests/test_automatizacion_compras_fase4.py:187:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/bitacora",
/app/backend/tests/test_automatizacion_compras_fase4.py:202:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/bitacora",
/app/backend/tests/test_automatizacion_compras_fase4.py:228:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/pedidos-procesados"
/app/backend/tests/test_automatizacion_compras_fase4.py:243:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/pedidos-procesados",
/app/backend/tests/test_automatizacion_compras_fase4.py:260:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/pedidos-procesados",
/app/backend/tests/test_automatizacion_compras_fase4.py:277:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/pedidos-procesados",
/app/backend/tests/test_automatizacion_compras_fase4.py:308:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas"
/app/backend/tests/test_automatizacion_compras_fase4.py:323:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas",
/app/backend/tests/test_automatizacion_compras_fase4.py:340:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas",
/app/backend/tests/test_automatizacion_compras_fase4.py:356:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas",
/app/backend/tests/test_automatizacion_compras_fase4.py:389:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/kpis"
/app/backend/tests/test_automatizacion_compras_fase4.py:403:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/kpis",
/app/backend/tests/test_automatizacion_compras_fase4.py:415:        """GET /compras - Debe retornar lista de automatizaciones"""
/app/backend/tests/test_automatizacion_compras_fase4.py:417:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras"
/app/backend/tests/test_automatizacion_compras_fase4.py:431:        """GET /compras - Debe filtrar por estado"""
/app/backend/tests/test_automatizacion_compras_fase4.py:433:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras",
/app/backend/tests/test_automatizacion_compras_fase4.py:441:        """GET /compras - Debe filtrar por sucursal_id"""
/app/backend/tests/test_automatizacion_compras_fase4.py:443:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras",
/app/backend/tests/test_automatizacion_compras_fase4.py:451:        """GET /compras - Debe respetar parámetro limite"""
/app/backend/tests/test_automatizacion_compras_fase4.py:453:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras",
/app/backend/tests/test_automatizacion_compras_fase4.py:475:            ("GET", "/api/v2/automatizaciones/operativas/compras/detector/estado"),
/app/backend/tests/test_automatizacion_compras_fase4.py:476:            ("GET", "/api/v2/automatizaciones/operativas/compras/detector/bitacora"),
/app/backend/tests/test_automatizacion_compras_fase4.py:477:            ("GET", "/api/v2/automatizaciones/operativas/compras/pedidos-procesados"),
/app/backend/tests/test_automatizacion_compras_fase4.py:478:            ("GET", "/api/v2/automatizaciones/operativas/compras/tareas"),
/app/backend/tests/test_automatizacion_compras_fase4.py:479:            ("GET", "/api/v2/automatizaciones/operativas/compras/kpis"),
/app/backend/tests/test_automatizacion_compras_fase4.py:480:            ("GET", "/api/v2/automatizaciones/operativas/compras"),
/app/backend/tests/test_automatizacion_compras_fase4.py:517:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas/tarea_inexistente_123"
/app/backend/tests/test_automatizacion_compras_fase4.py:526:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas/tarea_inexistente_123/completar"
/app/backend/tests/test_automatizacion_compras_fase4.py:535:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas/tarea_inexistente_123/asignar",
/app/backend/tests/test_automatizacion_compras_fase4.py:546:            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas",
```
