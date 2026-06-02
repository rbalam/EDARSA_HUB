# MATRIZ DE CANONICIDAD - TABLAS EDARSAHUB
**Generado:** 2026-06-02T10:04:26.298025
**Estado:** ANÁLISIS - NO MODIFICAR ESTRUCTURA

---

## 1. CLASIFICACIÓN GENERAL DE TABLAS

### Resumen por Clasificación

| Clasificación | Tablas | Registros | Descripción |
|---------------|--------|-----------|-------------|
| CANONICA | 48 | 74,163 | Fuente de verdad única |
| SINCRONIZADA | 31 | 42,845 | Datos de sistemas externos |
| DERIVADA | 90 | 90,728 | Calculada/agregada de canónicas |
| LEGADO_REVISION | 3 | 10 | Pendiente de migración |
| NO_USAR_NUEVO | 3 | 3,362 | Deprecada, usar alternativa |
| EXTERNA_REFERENCIADA | 46 | 109 | Integración externa (CRM) |
| SIN_CLASIFICAR | 202 | 76,120 | Requiere análisis |

### CANONICA (48 tablas)

| Tabla | Registros |
|-------|-----------|
| `Finanzas_Cat_CuentasBancarias` | 1 |
| `Finanzas_Cat_EstatusCuadreZ` | 6 |
| `Finanzas_Cat_EstatusTesoreria` | 4 |
| `Global_Cat_Bancos` | 5 |
| `Global_Cat_FormaPagoSAT` | 6 |
| `RH_Cat_Areas` | 0 |
| `RH_Cat_Beneficios` | 0 |
| `RH_Cat_ConceptosNomina` | 10 |
| `RH_Cat_Departamentos` | 11 |
| `RH_Cat_EstatusPeriodoNomina` | 6 |
| `RH_Cat_Jornadas` | 0 |
| `RH_Cat_MotivosBaja` | 3 |
| `RH_Cat_Puestos` | 37 |
| `RH_Cat_RegimenContratacion` | 0 |
| `RH_Cat_Sucursales` | 8 |
| `RH_Cat_SucursalesFiscal` | 0 |
| `RH_Cat_TiposAusencia` | 5 |
| `RH_Cat_TiposConceptoNomina` | 4 |
| `RH_Cat_TiposContrato` | 3 |
| `RH_Cat_TiposPeriodoNomina` | 4 |
| `RH_Cat_Turnos` | 0 |
| `Sistema_Capacidades` | 40 |
| `Sistema_Catalogo` | 5 |
| `Sistema_Empresas` | 5 |
| `Sistema_EmpresasAlias` | 12 |
| `Sistema_EmpresasMongoMap` | 5 |
| `Sistema_EmpresasServidores` | 7 |
| `Sistema_Gobierno_Tablas` | 21 |
| `Sistema_HorariosServicioUnidad` | 35 |
| `Sistema_Migracion_MongoSQL_Mapeo` | 8 |
| `Sistema_Modulos` | 28 |
| `Sistema_ModulosMenus` | 52 |
| `Sistema_ModulosPermisos` | 13 |
| `Sistema_ModulosVisibilidad` | 16 |
| `Sistema_RBAC_Permisos` | 5 |
| `Sistema_RBAC_Roles` | 0 |
| `Sistema_RBAC_RolesPermisos` | 0 |
| `Sistema_ServidorSucursalesConfig` | 7 |
| `Sistema_SucursalServidorConfig` | 0 |
| `Sistema_SucursalServidorMapeo` | 5 |
| `Sistema_Sucursales` | 5 |
| `Sistema_Tipos` | 6 |
| `Sistema_TiposVariantes` | 19 |
| `Sistema_TurnosOperativosUnidad` | 20 |
| `Sistema_UnidadesNegocioPerfilDigital` | 5 |
| `propinas_tpv_config` | 0 |
| `propinas_tpv_control` | 73,731 |
| `propinas_tpv_historial` | 0 |

### SINCRONIZADA (31 tablas)

| Tabla | Registros |
|-------|-----------|
| `Sync_Control_Ejecuciones` | 2,264 |
| `Sync_Customers` | 0 |
| `Sync_Impuestos_Origen` | 0 |
| `Sync_Inventory` | 0 |
| `Sync_KPI_Ventas_Unidades` | 0 |
| `Sync_Logs` | 3 |
| `Sync_Menus` | 6 |
| `Sync_Mesas` | 0 |
| `Sync_Metas_Comerciales` | 0 |
| `Sync_Movimientos_Detalle` | 0 |
| `Sync_PAX_Detalle` | 0 |
| `Sync_Precios_Historicos` | 0 |
| `Sync_Productos` | 9,905 |
| `Sync_Productos_Elaborados` | 3,893 |
| `Sync_Productos_Familias` | 189 |
| `Sync_Productos_Insumos` | 11,735 |
| `Sync_Productos_Recetas` | 13,313 |
| `Sync_Productos_SubFamilias` | 264 |
| `Sync_Purchases` | 0 |
| `Sync_Response_Cache` | 2 |
| `Sync_Sales` | 0 |
| `Sync_Ticket_Perfecto` | 0 |
| `Sync_Token_Ledger` | 0 |
| `Sync_Ventas_Historicas` | 33 |
| `Sync_Ventas_PorDiaSemana` | 28 |
| `Sync_Ventas_PorHora` | 605 |
| `Sync_Vtiger_Contactos` | 1 |
| `Sync_Vtiger_Cuentas` | 2 |
| `Sync_Vtiger_Leads` | 3 |
| `Sync_Vtiger_Log` | 598 |
| `Sync_Vtiger_Oportunidades` | 1 |

### DERIVADA (90 tablas)

| Tabla | Registros |
|-------|-----------|
| `Auditoria_Inventario_Provisional` | 7 |
| `Comercial_AlertasMargenDestinatarios` | 0 |
| `Comercial_AlertasMargenEnvios` | 0 |
| `Comercial_AlertasMargenEventos` | 0 |
| `Comercial_AlertasMargenReglas` | 3 |
| `Comercial_AlertasUmbralesSeveridad` | 4 |
| `Comercial_Competidores` | 3 |
| `Comercial_CompetidoresCatalogo` | 4 |
| `Comercial_CompetidoresListas` | 1 |
| `Comercial_CompetidoresListasDetalle` | 1 |
| `Comercial_CompetidoresMenuItems` | 6 |
| `Comercial_CompetidoresUnidad` | 5 |
| `Comercial_Dashboard_Cache` | 0 |
| `Comercial_ImpuestosCatalogo` | 8 |
| `Comercial_ImpuestosMapeo` | 9,905 |
| `Comercial_ImpuestosOverrides` | 0 |
| `Comercial_ImpuestosTasas` | 7 |
| `Comercial_Inteligencia_VentasDetalleProducto` | 0 |
| `Comercial_KPIs_Cache` | 0 |
| `Comercial_KPIs_Diarios_v2` | 3,373 |
| `Comercial_KPIs_Diarios_v2_backup_migracion_codigos_20260513_0558` | 1,801 |
| `Comercial_KPIs_Historico` | 3,647 |
| `Comercial_KPIs_Mensuales_v2` | 0 |
| `Comercial_Metas` | 0 |
| `Comercial_PreciosSugeridos` | 0 |
| `Comercial_PricingAnalisisIA` | 2 |
| `Comercial_PricingBenchmarkProducto` | 1 |
| `Comercial_RecetasSnapshot` | 0 |
| `Comercial_RecetasSnapshotDetalle` | 0 |
| `Comercial_ReglasPrecio` | 1 |
| `Comercial_ReglasPrecioRangos` | 13 |
| `Comercial_SimulacionesPrecios` | 0 |
| `Comercial_SolicitudesCambioPrecio` | 3 |
| `Comercial_SolicitudesCambioPrecioHistorial` | 11 |
| `Comercial_SyncLog_v2` | 42,913 |
| `Comercial_SyncLog_v2_backup_migracion_codigos_20260513_0558` | 2,647 |
| `Comercial_Ventas_Dia_Abiertas_v2` | 8 |
| `Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521` | 5 |
| `Comercial_Ventas_Dia_Abiertas_v2_backup_migracion_codigos_20260513_0558` | 3 |
| `Finanzas_ConfiguracionTPV_Sucursal` | 8 |
| `Finanzas_CortesCaja` | 4,108 |
| `Finanzas_CortesCaja_Backup_Demo_20260501` | 70 |
| `Finanzas_CortesCaja_DetallePagos` | 0 |
| `Finanzas_CortesCaja_SyncLog` | 8,010 |
| `Finanzas_CuadresZ` | 0 |
| `Finanzas_CuadresZ_SyncLog` | 0 |
| `Finanzas_CuentasPorPagar` | 25 |
| `Finanzas_Depositos` | 0 |
| `Finanzas_EstatusCierre` | 3 |
| `Finanzas_EstatusPago` | 5 |
| `Finanzas_KPIs_Historico` | 4,707 |
| `Finanzas_Pagos` | 0 |
| `Finanzas_Presupuestos` | 0 |
| `Finanzas_PropinasTPV_SyncLog` | 8,266 |
| `Finanzas_SaldosBancarios` | 0 |
| `RH_Auditoria_Fiscal` | 0 |
| `RH_Ausencias` | 0 |
| `RH_Calendario_Laboral` | 0 |
| `RH_Colaboradores_Beneficios` | 0 |
| `RH_Colaboradores_ContactosEmergencia` | 0 |
| `RH_Colaboradores_Dependientes` | 0 |
| `RH_Colaboradores_Documentos` | 0 |
| `RH_Colaboradores_Domicilios` | 0 |
| `RH_Colaboradores_Expediente` | 510 |
| `RH_Contratos` | 0 |
| `RH_Finiquitos` | 0 |
| `RH_Finiquitos_Detalle` | 0 |
| `RH_Flujo_Nomina_Sucursal` | 0 |
| `RH_GruposNomina` | 0 |
| `RH_Historial_Puestos` | 0 |
| `RH_Historial_Salarios` | 0 |
| `RH_Homologacion_Equivalencias` | 56 |
| `RH_IMSS_Movimientos` | 0 |
| `RH_Importacion_Bitacora` | 7 |
| `RH_Importacion_Staging` | 571 |
| `RH_Incidencias_Nomina` | 0 |
| `RH_Nomina` | 0 |
| `RH_Nomina_Detalle` | 0 |
| `RH_Nomina_Dispersion` | 0 |
| `RH_Nomina_Recibos` | 0 |
| `RH_Periodos_Nomina` | 0 |
| `RH_Prestamos` | 0 |
| `RH_Prestamos_Detalle` | 0 |
| `RH_Reloj_Checador` | 0 |
| `RH_Vacaciones_Movimientos` | 0 |
| `RH_Vacaciones_Saldos` | 0 |
| `Workflow_DecisionesAuditoria` | 0 |
| `Workflow_DetalleDiferencias` | 0 |
| `Workflow_Inventarios` | 0 |
| `Workflow_Justificaciones` | 0 |

### LEGADO_REVISION (3 tablas)

| Tabla | Registros |
|-------|-----------|
| `Sys_Roles` | 4 |
| `Sys_Scheduler_Jobs` | 6 |
| `Sys_Usuarios` | 0 |

### NO_USAR_NUEVO (3 tablas)

| Tabla | Registros |
|-------|-----------|
| `Config_Horarios` | 3 |
| `Fact_Ventas_Consolidadas` | 3,322 |
| `Products` | 37 |

### EXTERNA_REFERENCIADA (46 tablas)

| Tabla | Registros |
|-------|-----------|
| `CRM_Actividades` | 0 |
| `CRM_ActividadesHistorial` | 0 |
| `CRM_Automation_Log` | 0 |
| `CRM_Automation_Reglas` | 3 |
| `CRM_Cat_EstatusActividad` | 5 |
| `CRM_Cat_EstatusContrato` | 7 |
| `CRM_Cat_EstatusLead` | 5 |
| `CRM_Cat_EstatusOportunidad` | 5 |
| `CRM_Cat_EstatusPropuesta` | 7 |
| `CRM_Cat_MotivosGanada` | 8 |
| `CRM_Cat_MotivosPerdida` | 9 |
| `CRM_Cat_OrigenLead` | 11 |
| `CRM_Cat_Prioridades` | 4 |
| `CRM_Cat_Sectores` | 9 |
| `CRM_Cat_TamanosCliente` | 5 |
| `CRM_Cat_TiposActividad` | 6 |
| `CRM_Cat_TiposPipeline` | 4 |
| `CRM_ClientesSolicitudesAlta` | 0 |
| `CRM_ClientesSolicitudesAltaHistorial` | 0 |
| `CRM_Config_PipelineEtapas` | 7 |
| `CRM_Config_Pipelines` | 1 |
| `CRM_Contratos` | 0 |
| `CRM_Cuentas` | 0 |
| `CRM_ERPSyncLog` | 0 |
| `CRM_Implementaciones` | 0 |
| `CRM_ImplementacionesEntregables` | 0 |
| `CRM_Integracion_Conectores` | 1 |
| `CRM_Integracion_MapeoEtapas` | 0 |
| `CRM_Integracion_SyncLog` | 1 |
| `CRM_IntegracionesConflictos` | 0 |
| `CRM_IntegracionesSyncLog` | 0 |
| `CRM_Leads` | 0 |
| `CRM_Oportunidad_Contactos` | 0 |
| `CRM_Oportunidad_Documentos` | 0 |
| `CRM_Oportunidades` | 0 |
| `CRM_OportunidadesHistorial` | 0 |
| `CRM_Oportunidades_HistorialEtapas` | 4 |
| `CRM_PostventaEncuestas` | 0 |
| `CRM_PostventaTickets` | 0 |
| `CRM_Propuestas` | 0 |
| `CRM_Staging_Cuentas` | 2 |
| `CRM_Staging_Leads` | 2 |
| `CRM_Staging_Oportunidades` | 0 |
| `CRM_Tareas` | 0 |
| `CRM_Trigger_Log` | 0 |
| `CRM_Triggers` | 3 |

### SIN_CLASIFICAR (202 tablas)

| Tabla | Registros |
|-------|-----------|
| `ActivoFijo_ActivoMedidores` | 0 |
| `ActivoFijo_Activos` | 0 |
| `ActivoFijo_ActivosLibros` | 0 |
| `ActivoFijo_Alertas` | 0 |
| `ActivoFijo_Archivos` | 0 |
| `ActivoFijo_Autorizaciones` | 0 |
| `ActivoFijo_BajasActivos` | 0 |
| `ActivoFijo_ClaseActivo` | 8 |
| `ActivoFijo_Cotizaciones` | 0 |
| `ActivoFijo_DepreciacionMovimientos` | 0 |
| `ActivoFijo_EstadoUsoActivo` | 5 |
| `ActivoFijo_EstatusActivo` | 6 |
| `ActivoFijo_EstatusOT` | 5 |
| `ActivoFijo_HistorialAsignaciones` | 0 |
| `ActivoFijo_LecturasMedidor` | 0 |
| `ActivoFijo_LibrosDepreciacion` | 3 |
| `ActivoFijo_Medidores` | 0 |
| `ActivoFijo_MetodosDepreciacion` | 3 |
| `ActivoFijo_MovimientosActivo` | 0 |
| `ActivoFijo_OrdenTrabajoCostos` | 0 |
| `ActivoFijo_OrdenesTrabajo` | 0 |
| `ActivoFijo_PlanesMantenimiento` | 0 |
| `ActivoFijo_PrioridadOT` | 4 |
| `ActivoFijo_ReemplazosActivos` | 0 |
| `ActivoFijo_ReglasClaseLibro` | 9 |
| `ActivoFijo_TipoActivo` | 9 |
| `ActivoFijo_TipoBaja` | 7 |
| `ActivoFijo_TipoMedidor` | 3 |
| `ActivoFijo_TipoOT` | 3 |
| `ActivoFijo_TipoUbicacion` | 9 |
| `ActivoFijo_Ubicaciones` | 0 |
| `Alertas_Sistema` | 14 |
| `CavaSocios_Botellas` | 2 |
| `CavaSocios_Cargos` | 1 |
| `CavaSocios_Configuracion` | 0 |
| `CavaSocios_Movimientos` | 3 |
| `CavaSocios_Socios` | 2 |
| `Cliente_Catalogo` | 2 |
| `Cliente_Contactos` | 0 |
| `Cliente_Direcciones` | 0 |
| `Cliente_Grupos` | 0 |
| `Cliente_RolUsuarioPortal` | 3 |
| `Cliente_UsuariosPortal` | 0 |
| `Compras` | 0 |
| `Compras_ConciliacionSAT` | 0 |
| `Compras_ConciliacionSATDetalle` | 0 |
| `Compras_ConciliacionSATEstatus` | 11 |
| `Compras_Detalle` | 0 |
| `Compras_DocumentosFiscales` | 0 |
| `Compras_DocumentosFiscalesDetalle` | 0 |
| `Compras_DocumentosFiscalesEstatus` | 7 |
| `Compras_Estatus` | 8 |
| `Compras_Eventos_Pendientes` | 0 |
| `Compras_Informes_Config` | 0 |
| `Compras_Inventarios_Fisicos_Sync` | 599 |
| `Compras_KPIs_Historico` | 7,035 |
| `Compras_Ordenes` | 0 |
| `Compras_OrdenesDetalle` | 0 |
| `Compras_OrdenesEstatus` | 8 |
| `Compras_Parametros_Sucursal` | 1 |
| `Compras_Pedidos` | 0 |
| `Compras_PedidosDetalle` | 0 |
| `Compras_PedidosEstatus` | 8 |
| `Compras_Recepciones` | 0 |
| `Compras_RecepcionesDetalle` | 0 |
| `Compras_RecepcionesEstatus` | 6 |
| `Compras_Requisiciones_Sync` | 0 |
| `Compras_Sync_Checkpoint` | 0 |
| `Compras_Sync_Log` | 53 |
| `Config_Asignaciones` | 0 |
| `Configuracion_Operativa` | 9 |
| `ConsultasSQL_Catalogo` | 20 |
| `ConsultasSQL_EjecucionesLog` | 0 |
| `ConsultasSQL_Parametros` | 38 |
| `ConsultasSQL_Permisos` | 0 |
| `ConsultasSQL_Servidores` | 0 |
| `ConsultasSQL_Versiones` | 0 |
| `Inventario_Almacenes` | 0 |
| `Inventario_Existencias` | 0 |
| `Inventario_Movimientos` | 0 |
| `Inventario_MovimientosDetalle` | 0 |
| `Inventario_TipoMovimiento` | 6 |
| `Inventarios_SinAsignar` | 14 |
| `Operaciones_Tablaje_Auditoria` | 0 |
| `Operaciones_Tablaje_Autorizaciones` | 0 |
| `Operaciones_Tablaje_Costos` | 0 |
| `Operaciones_Tablaje_Documentos` | 0 |
| `Operaciones_Tablaje_EventosContables` | 0 |
| `Operaciones_Tablaje_Mermas` | 7 |
| `Operaciones_Tablaje_Ordenes` | 8 |
| `Operaciones_Tablaje_OrdenesDetalle` | 22 |
| `Operaciones_Tablaje_Plantillas` | 37 |
| `Operaciones_Tablaje_PlantillasDetalle` | 151 |
| `Operaciones_Tablaje_PlantillasVersiones` | 0 |
| `Operaciones_Tablaje_Rendimientos` | 6 |
| `Operaciones_Tablaje_SyncErrores` | 0 |
| `Operaciones_Tablaje_SyncLog` | 1 |
| `Operativo_AuditoriasProgramadas` | 0 |
| `Operativo_BitacoraCompras` | 0 |
| `Operativo_CargosResponsabilidad` | 0 |
| `Operativo_DocumentosGenerados` | 0 |
| `Operativo_HistorialAsignaciones` | 0 |
| `Operativo_HistorialCargos` | 0 |
| `Operativo_Notificaciones_Log` | 0 |
| `Operativo_PedidosProcesados` | 0 |
| `Operativo_ResponsabilidadEconomica` | 0 |
| `Operativo_TareasCompras` | 0 |
| `Producto_Catalogo` | 0 |
| `Producto_Equivalentes` | 0 |
| `Producto_Familias` | 0 |
| `Producto_Lineas` | 0 |
| `Producto_Marcas` | 0 |
| `Producto_Presentaciones` | 0 |
| `Producto_SubFamilias` | 0 |
| `Producto_Sustitutos` | 0 |
| `Proveedor_Bancos` | 0 |
| `Proveedor_Catalogo` | 5 |
| `Proveedor_Categorias` | 0 |
| `Proveedor_CategoriasCatalogo` | 0 |
| `Proveedor_Contactos` | 0 |
| `Proveedor_CuentasBancarias` | 0 |
| `Proveedor_Documentos` | 0 |
| `Proveedor_EstatusProveedor` | 4 |
| `Proveedor_EstatusSAT` | 4 |
| `Proveedor_EstatusSincronizacion` | 3 |
| `Proveedor_Evaluaciones` | 0 |
| `Proveedor_Integracion` | 0 |
| `Proveedor_Monedas` | 3 |
| `Proveedor_RegimenFiscal` | 0 |
| `Proveedor_RiesgoProveedor` | 4 |
| `Proveedor_RolUsuarioPortal` | 4 |
| `Proveedor_SistemasIntegracion` | 4 |
| `Proveedor_TipoContacto` | 5 |
| `Proveedor_TipoDocumento` | 8 |
| `Proveedor_TipoProveedor` | 7 |
| `Proveedor_UsuariosPortal` | 0 |
| `Scheduler_BitacoraJobs` | 63,648 |
| `Scheduler_InventariosProcesados` | 0 |
| `Scheduler_PedidosProcesados` | 0 |
| `Servidores_Conexiones` | 23 |
| `Servidores_Conexiones_Log` | 40 |
| `Servidores_Conexiones_backup_tipos_enriq_20260513_0840` | 3 |
| `Servidores_Conexiones_backup_tipos_mov_20260513_0729` | 4 |
| `Servidores_Status` | 0 |
| `Sesiones` | 760 |
| `SesionesHistorico` | 757 |
| `Tablajeria_ConfigContable` | 0 |
| `Tablajeria_CosteoDetalle` | 5 |
| `Tablajeria_CosteoProduccion` | 2 |
| `Tablajeria_MovimientosInventario` | 3 |
| `Tablajeria_PolizasContables` | 2 |
| `Tablajeria_PolizasDetalle` | 6 |
| `TableroEjecutivoCache` | 5 |
| `Tareas_Inventario` | 0 |
| `Unidades_Negocio` | 5 |
| `Usuario_Acciones` | 16 |
| `Usuario_AlmacenesAsignacion` | 129 |
| `Usuario_Autorizaciones` | 2 |
| `Usuario_AutorizacionesDetalle` | 0 |
| `Usuario_Catalogo` | 12 |
| `Usuario_EmpresasAsignacion` | 38 |
| `Usuario_LogAccesos` | 0 |
| `Usuario_LogActividades` | 10 |
| `Usuario_LogRBACVerificacion` | 1,440 |
| `Usuario_LogRecuperacion` | 4 |
| `Usuario_MatrizAutorizacion` | 0 |
| `Usuario_MigracionMongoTrace` | 11 |
| `Usuario_Modulos` | 55 |
| `Usuario_PermisosRolModulo` | 432 |
| `Usuario_PortalConfiguracion` | 0 |
| `Usuario_RateLimitRecuperacion` | 6 |
| `Usuario_Roles` | 16 |
| `Usuario_RolesAsignacion` | 27 |
| `Usuario_ServidoresAsignacion` | 194 |
| `Usuario_Sesiones` | 0 |
| `Usuario_SucursalesAsignacion` | 216 |
| `Usuario_TiposAutorizacion` | 7 |
| `Usuario_TokensRecuperacion` | 2 |
| `Venta_Cat_EstatusRemision` | 7 |
| `Venta_CondicionesPago` | 2 |
| `Venta_Cotizaciones` | 0 |
| `Venta_CotizacionesDetalle` | 0 |
| `Venta_CotizacionesEstatus` | 6 |
| `Venta_Detalle` | 0 |
| `Venta_Encabezado` | 0 |
| `Venta_Estatus` | 6 |
| `Venta_FormaPago` | 4 |
| `Venta_ListasPrecios` | 1 |
| `Venta_ListasPreciosDetalle` | 0 |
| `Venta_Pagos` | 0 |
| `Venta_Pedidos` | 0 |
| `Venta_PedidosDetalle` | 0 |
| `Venta_PedidosEstatus` | 6 |
| `Venta_Remisiones` | 0 |
| `Venta_RemisionesDetalle` | 0 |
| `Venta_RemisionesHistorial` | 0 |
| `automatizacion_inventarios_config` | 0 |
| `automatizacion_inventarios_destinatarios` | 0 |
| `automatizacion_inventarios_ejecuciones` | 0 |
| `automatizacion_inventarios_envios` | 0 |
| `automatizacion_inventarios_folios_procesados` | 1 |
| `automatizacion_inventarios_ultimo_folio_conocido` | 0 |

---

## 2. ANÁLISIS COMPARATIVO ESPECÍFICO

### 2.1 FIN_* vs Finanzas_*

| Tabla | Registros | Versión | Acción Sugerida |
|-------|-----------|---------|-----------------|
| `Finanzas_Cat_CuentasBancarias` | 1 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_Cat_EstatusCuadreZ` | 6 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_Cat_EstatusTesoreria` | 4 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_ConfiguracionTPV_Sucursal` | 8 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_CortesCaja` | 4,108 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_CortesCaja_Backup_Demo_20260501` | 70 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_CortesCaja_DetallePagos` | 0 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_CortesCaja_SyncLog` | 8,010 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_CuadresZ` | 0 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_CuadresZ_SyncLog` | 0 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_CuentasPorPagar` | 25 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_Depositos` | 0 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_EstatusCierre` | 3 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_EstatusPago` | 5 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_KPIs_Historico` | 4,707 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_Pagos` | 0 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_Presupuestos` | 0 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_PropinasTPV_SyncLog` | 8,266 | LEGACY | ⚠️ Migrar a Finanzas_* |
| `Finanzas_SaldosBancarios` | 0 | LEGACY | ⚠️ Migrar a Finanzas_* |

### 2.2 Products vs Sync_Productos

- **Products**: 37 registros (LEGACY)
- **Sync_Productos**: 9,905 registros (NUEVA)

**Recomendación:** `Products` → NO_USAR_NUEVO. Usar `Sync_Productos` como fuente.

### 2.3 Fact_Ventas_Consolidadas vs Comercial_KPIs_Diarios_v2

| Tabla | Registros | Última Fecha | Versión |
|-------|-----------|--------------|---------|
| `Fact_Ventas_Consolidadas` | 3,322 | 2026-06-01 | LEGACY |
| `Comercial_KPIs_Diarios_v2` | 3,373 | 2026-06-01 | NUEVA |

**Recomendación:** `Fact_Ventas_Consolidadas` → NO_USAR_NUEVO. Usar `Comercial_KPIs_Diarios_v2`.

### 2.4 Sys_* vs Sistema_*

| Tabla | Registros | Versión | Acción |
|-------|-----------|---------|--------|
| `Sys_Roles` | 4 | LEGACY | ⚠️ Migrar a Sistema_* |
| `Sys_Scheduler_Jobs` | 6 | LEGACY | ⚠️ Migrar a Sistema_* |
| `Sys_Usuarios` | 0 | LEGACY | ⚠️ Migrar a Sistema_* |
| `Sistema_Capacidades` | 40 | NUEVA | ✅ OK |
| `Sistema_Catalogo` | 5 | NUEVA | ✅ OK |
| `Sistema_Empresas` | 5 | NUEVA | ✅ OK |
| `Sistema_EmpresasAlias` | 12 | NUEVA | ✅ OK |
| `Sistema_EmpresasMongoMap` | 5 | NUEVA | ✅ OK |
| `Sistema_EmpresasServidores` | 7 | NUEVA | ✅ OK |
| `Sistema_Gobierno_Tablas` | 21 | NUEVA | ✅ OK |
| `Sistema_HorariosServicioUnidad` | 35 | NUEVA | ✅ OK |
| `Sistema_Migracion_MongoSQL_Mapeo` | 8 | NUEVA | ✅ OK |
| `Sistema_Modulos` | 28 | NUEVA | ✅ OK |
| `Sistema_ModulosMenus` | 52 | NUEVA | ✅ OK |
| `Sistema_ModulosPermisos` | 13 | NUEVA | ✅ OK |
| `Sistema_ModulosVisibilidad` | 16 | NUEVA | ✅ OK |
| `Sistema_RBAC_Permisos` | 5 | NUEVA | ✅ OK |
| `Sistema_RBAC_Roles` | 0 | NUEVA | ✅ OK |
| `Sistema_RBAC_RolesPermisos` | 0 | NUEVA | ✅ OK |
| `Sistema_ServidorSucursalesConfig` | 7 | NUEVA | ✅ OK |
| `Sistema_Sucursales` | 5 | NUEVA | ✅ OK |
| `Sistema_SucursalServidorConfig` | 0 | NUEVA | ✅ OK |
| `Sistema_SucursalServidorMapeo` | 5 | NUEVA | ✅ OK |
| `Sistema_Tipos` | 6 | NUEVA | ✅ OK |
| `Sistema_TiposVariantes` | 19 | NUEVA | ✅ OK |
| `Sistema_TurnosOperativosUnidad` | 20 | NUEVA | ✅ OK |
| `Sistema_UnidadesNegocioPerfilDigital` | 5 | NUEVA | ✅ OK |

### 2.5 Config_Horarios vs Sistema_HorariosServicioUnidad

- **Config_Horarios**: 3 registros (LEGACY)
- **Sistema_HorariosServicioUnidad**: 35 registros (NUEVA)

**Recomendación:** `Config_Horarios` → NO_USAR_NUEVO. Usar `Sistema_HorariosServicioUnidad`.

---

## 3. MAPEO MONGODB COLLECTIONS → SQL

| Colección MongoDB | Tabla SQL Destino | Módulo | Prioridad | Estado |
|-------------------|-------------------|--------|-----------|--------|
| `empresas` | `Global_Cat_Empresas` | Global | P0 | PENDIENTE |
| `rbac_permisos` | `*(por definir)*` | RBAC | P0 | PENDIENTE |
| `rbac_roles` | `*(por definir)*` | RBAC | P0 | PENDIENTE |
| `rbac_usuarios_roles` | `*(por definir)*` | RBAC | P0 | PENDIENTE |
| `servers` | `Servidores_Conexiones` | Sistema/Conexiones | P0 | PENDIENTE |
| `sucursal_servidor_map` | `Unidades_Negocio` | Sistema/Unidades | P0 | PENDIENTE |
| `rbac_audit_log` | `*(por definir)*` | RBAC/Auditoría | P1 | PENDIENTE |
| `sucursales_catalogo` | `RH_Cat_Sucursales` | Global/RH | P1 | PENDIENTE |

---

## 4. TABLAS REGISTRADAS EN GOBIERNO

| Tabla | Módulo | Categoría | Estado | Fuente |
|-------|--------|-----------|--------|--------|
| `Comercial_KPIs_Diarios_v2` | Comercial | DERIVADA | ACTIVA | EDARSAHUB SQL |
| `Comercial_Ventas_Dia_Abiertas_v2` | Comercial | DERIVADA | ACTIVA | EDARSAHUB SQL |
| `Config_Horarios` | Comercial | LEGADO_REVISION | NO_USAR_NUEVO | Pendiente validar |
| `Fact_Ventas_Consolidadas` | Comercial | LEGADO_REVISION | NO_USAR_NUEVO | Pendiente validar |
| `Products` | Comercial | LEGADO_REVISION | NO_USAR_NUEVO | Pendiente validar |
| `Sync_PAX_Detalle` | Comercial | SINCRONIZADA | ACTIVA | SoftRestaurant/MPRO sincronizado |
| `Sync_Productos` | Comercial | SINCRONIZADA | ACTIVA | SoftRestaurant/MPRO sincronizado |
| `Sync_Productos_Familias` | Comercial | SINCRONIZADA | ACTIVA | SoftRestaurant/MPRO sincronizado |
| `Sync_Productos_SubFamilias` | Comercial | SINCRONIZADA | ACTIVA | SoftRestaurant/MPRO sincronizado |
| `Sync_Sales` | Comercial | SINCRONIZADA | ACTIVA | SoftRestaurant/MPRO sincronizado |
| `Finanzas_Cat_CuentasBancarias` | Finanzas | CANONICA | ACTIVA | EDARSAHUB SQL |
| `propinas_tpv_config` | Finanzas/PropinasTPV | CANONICA | ACTIVA | EDARSAHUB SQL |
| `propinas_tpv_control` | Finanzas/PropinasTPV | CANONICA | ACTIVA | EDARSAHUB SQL |
| `propinas_tpv_historial` | Finanzas/PropinasTPV | CANONICA | ACTIVA | EDARSAHUB SQL |
| `Global_Cat_Bancos` | Global | CANONICA | ACTIVA | EDARSAHUB SQL |
| `Global_Cat_CentrosCosto` | Global | CANONICA | ACTIVA | EDARSAHUB SQL |
| `Global_Cat_Empresas` | Global | CANONICA | ACTIVA | EDARSAHUB SQL |
| `Global_Cat_UnidadesMedida` | Global | CANONICA | ACTIVA | EDARSAHUB SQL |
| `RH_Colaboradores_Expediente` | RH | CANONICA | ACTIVA | EDARSAHUB SQL |
| `RH_Importacion_Bitacora` | RH | LOG | ACTIVA | EDARSAHUB SQL |
| `RH_Importacion_Staging` | RH | STAGING | ACTIVA | EDARSAHUB SQL |

---

## 5. TABLAS SIN GOBIERNO REGISTRADO

**Total:** 405 tablas sin registro en `Sistema_Gobierno_Tablas`

<details>
<summary>Ver lista completa</summary>

- `ActivoFijo_ActivoMedidores`
- `ActivoFijo_Activos`
- `ActivoFijo_ActivosLibros`
- `ActivoFijo_Alertas`
- `ActivoFijo_Archivos`
- `ActivoFijo_Autorizaciones`
- `ActivoFijo_BajasActivos`
- `ActivoFijo_ClaseActivo`
- `ActivoFijo_Cotizaciones`
- `ActivoFijo_DepreciacionMovimientos`
- `ActivoFijo_EstadoUsoActivo`
- `ActivoFijo_EstatusActivo`
- `ActivoFijo_EstatusOT`
- `ActivoFijo_HistorialAsignaciones`
- `ActivoFijo_LecturasMedidor`
- `ActivoFijo_LibrosDepreciacion`
- `ActivoFijo_Medidores`
- `ActivoFijo_MetodosDepreciacion`
- `ActivoFijo_MovimientosActivo`
- `ActivoFijo_OrdenesTrabajo`
- `ActivoFijo_OrdenTrabajoCostos`
- `ActivoFijo_PlanesMantenimiento`
- `ActivoFijo_PrioridadOT`
- `ActivoFijo_ReemplazosActivos`
- `ActivoFijo_ReglasClaseLibro`
- `ActivoFijo_TipoActivo`
- `ActivoFijo_TipoBaja`
- `ActivoFijo_TipoMedidor`
- `ActivoFijo_TipoOT`
- `ActivoFijo_TipoUbicacion`
- `ActivoFijo_Ubicaciones`
- `Alertas_Sistema`
- `Auditoria_Inventario_Provisional`
- `automatizacion_inventarios_config`
- `automatizacion_inventarios_destinatarios`
- `automatizacion_inventarios_ejecuciones`
- `automatizacion_inventarios_envios`
- `automatizacion_inventarios_folios_procesados`
- `automatizacion_inventarios_ultimo_folio_conocido`
- `CavaSocios_Botellas`
- `CavaSocios_Cargos`
- `CavaSocios_Configuracion`
- `CavaSocios_Movimientos`
- `CavaSocios_Socios`
- `Cliente_Catalogo`
- `Cliente_Contactos`
- `Cliente_Direcciones`
- `Cliente_Grupos`
- `Cliente_RolUsuarioPortal`
- `Cliente_UsuariosPortal`
- `Comercial_AlertasMargenDestinatarios`
- `Comercial_AlertasMargenEnvios`
- `Comercial_AlertasMargenEventos`
- `Comercial_AlertasMargenReglas`
- `Comercial_AlertasUmbralesSeveridad`
- `Comercial_Competidores`
- `Comercial_CompetidoresCatalogo`
- `Comercial_CompetidoresListas`
- `Comercial_CompetidoresListasDetalle`
- `Comercial_CompetidoresMenuItems`
- `Comercial_CompetidoresUnidad`
- `Comercial_Dashboard_Cache`
- `Comercial_ImpuestosCatalogo`
- `Comercial_ImpuestosMapeo`
- `Comercial_ImpuestosOverrides`
- `Comercial_ImpuestosTasas`
- `Comercial_Inteligencia_VentasDetalleProducto`
- `Comercial_KPIs_Cache`
- `Comercial_KPIs_Diarios_v2_backup_migracion_codigos_20260513_0558`
- `Comercial_KPIs_Historico`
- `Comercial_KPIs_Mensuales_v2`
- `Comercial_Metas`
- `Comercial_PreciosSugeridos`
- `Comercial_PricingAnalisisIA`
- `Comercial_PricingBenchmarkProducto`
- `Comercial_RecetasSnapshot`
- `Comercial_RecetasSnapshotDetalle`
- `Comercial_ReglasPrecio`
- `Comercial_ReglasPrecioRangos`
- `Comercial_SimulacionesPrecios`
- `Comercial_SolicitudesCambioPrecio`
- `Comercial_SolicitudesCambioPrecioHistorial`
- `Comercial_SyncLog_v2`
- `Comercial_SyncLog_v2_backup_migracion_codigos_20260513_0558`
- `Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521`
- `Comercial_Ventas_Dia_Abiertas_v2_backup_migracion_codigos_20260513_0558`
- `Compras`
- `Compras_ConciliacionSAT`
- `Compras_ConciliacionSATDetalle`
- `Compras_ConciliacionSATEstatus`
- `Compras_Detalle`
- `Compras_DocumentosFiscales`
- `Compras_DocumentosFiscalesDetalle`
- `Compras_DocumentosFiscalesEstatus`
- `Compras_Estatus`
- `Compras_Eventos_Pendientes`
- `Compras_Informes_Config`
- `Compras_Inventarios_Fisicos_Sync`
- `Compras_KPIs_Historico`
- `Compras_Ordenes`
- `Compras_OrdenesDetalle`
- `Compras_OrdenesEstatus`
- `Compras_Parametros_Sucursal`
- `Compras_Pedidos`
- `Compras_PedidosDetalle`
- `Compras_PedidosEstatus`
- `Compras_Recepciones`
- `Compras_RecepcionesDetalle`
- `Compras_RecepcionesEstatus`
- `Compras_Requisiciones_Sync`
- `Compras_Sync_Checkpoint`
- `Compras_Sync_Log`
- `Config_Asignaciones`
- `Configuracion_Operativa`
- `ConsultasSQL_Catalogo`
- `ConsultasSQL_EjecucionesLog`
- `ConsultasSQL_Parametros`
- `ConsultasSQL_Permisos`
- `ConsultasSQL_Servidores`
- `ConsultasSQL_Versiones`
- `CRM_Actividades`
- `CRM_ActividadesHistorial`
- `CRM_Automation_Log`
- `CRM_Automation_Reglas`
- `CRM_Cat_EstatusActividad`
- `CRM_Cat_EstatusContrato`
- `CRM_Cat_EstatusLead`
- `CRM_Cat_EstatusOportunidad`
- `CRM_Cat_EstatusPropuesta`
- `CRM_Cat_MotivosGanada`
- `CRM_Cat_MotivosPerdida`
- `CRM_Cat_OrigenLead`
- `CRM_Cat_Prioridades`
- `CRM_Cat_Sectores`
- `CRM_Cat_TamanosCliente`
- `CRM_Cat_TiposActividad`
- `CRM_Cat_TiposPipeline`
- `CRM_ClientesSolicitudesAlta`
- `CRM_ClientesSolicitudesAltaHistorial`
- `CRM_Config_PipelineEtapas`
- `CRM_Config_Pipelines`
- `CRM_Contratos`
- `CRM_Cuentas`
- `CRM_ERPSyncLog`
- `CRM_Implementaciones`
- `CRM_ImplementacionesEntregables`
- `CRM_Integracion_Conectores`
- `CRM_Integracion_MapeoEtapas`
- `CRM_Integracion_SyncLog`
- `CRM_IntegracionesConflictos`
- `CRM_IntegracionesSyncLog`
- `CRM_Leads`
- `CRM_Oportunidad_Contactos`
- `CRM_Oportunidad_Documentos`
- `CRM_Oportunidades`
- `CRM_Oportunidades_HistorialEtapas`
- `CRM_OportunidadesHistorial`
- `CRM_PostventaEncuestas`
- `CRM_PostventaTickets`
- `CRM_Propuestas`
- `CRM_Staging_Cuentas`
- `CRM_Staging_Leads`
- `CRM_Staging_Oportunidades`
- `CRM_Tareas`
- `CRM_Trigger_Log`
- `CRM_Triggers`
- `Finanzas_Cat_EstatusCuadreZ`
- `Finanzas_Cat_EstatusTesoreria`
- `Finanzas_ConfiguracionTPV_Sucursal`
- `Finanzas_CortesCaja`
- `Finanzas_CortesCaja_Backup_Demo_20260501`
- `Finanzas_CortesCaja_DetallePagos`
- `Finanzas_CortesCaja_SyncLog`
- `Finanzas_CuadresZ`
- `Finanzas_CuadresZ_SyncLog`
- `Finanzas_CuentasPorPagar`
- `Finanzas_Depositos`
- `Finanzas_EstatusCierre`
- `Finanzas_EstatusPago`
- `Finanzas_KPIs_Historico`
- `Finanzas_Pagos`
- `Finanzas_Presupuestos`
- `Finanzas_PropinasTPV_SyncLog`
- `Finanzas_SaldosBancarios`
- `Global_Cat_FormaPagoSAT`
- `Inventario_Almacenes`
- `Inventario_Existencias`
- `Inventario_Movimientos`
- `Inventario_MovimientosDetalle`
- `Inventario_TipoMovimiento`
- `Inventarios_SinAsignar`
- `Operaciones_Tablaje_Auditoria`
- `Operaciones_Tablaje_Autorizaciones`
- `Operaciones_Tablaje_Costos`
- `Operaciones_Tablaje_Documentos`
- `Operaciones_Tablaje_EventosContables`
- `Operaciones_Tablaje_Mermas`
- `Operaciones_Tablaje_Ordenes`
- `Operaciones_Tablaje_OrdenesDetalle`
- `Operaciones_Tablaje_Plantillas`
- `Operaciones_Tablaje_PlantillasDetalle`
- `Operaciones_Tablaje_PlantillasVersiones`
- `Operaciones_Tablaje_Rendimientos`
- `Operaciones_Tablaje_SyncErrores`
- `Operaciones_Tablaje_SyncLog`
- `Operativo_AuditoriasProgramadas`
- `Operativo_BitacoraCompras`
- `Operativo_CargosResponsabilidad`
- `Operativo_DocumentosGenerados`
- `Operativo_HistorialAsignaciones`
- `Operativo_HistorialCargos`
- `Operativo_Notificaciones_Log`
- `Operativo_PedidosProcesados`
- `Operativo_ResponsabilidadEconomica`
- `Operativo_TareasCompras`
- `Producto_Catalogo`
- `Producto_Equivalentes`
- `Producto_Familias`
- `Producto_Lineas`
- `Producto_Marcas`
- `Producto_Presentaciones`
- `Producto_SubFamilias`
- `Producto_Sustitutos`
- `Proveedor_Bancos`
- `Proveedor_Catalogo`
- `Proveedor_Categorias`
- `Proveedor_CategoriasCatalogo`
- `Proveedor_Contactos`
- `Proveedor_CuentasBancarias`
- `Proveedor_Documentos`
- `Proveedor_EstatusProveedor`
- `Proveedor_EstatusSAT`
- `Proveedor_EstatusSincronizacion`
- `Proveedor_Evaluaciones`
- `Proveedor_Integracion`
- `Proveedor_Monedas`
- `Proveedor_RegimenFiscal`
- `Proveedor_RiesgoProveedor`
- `Proveedor_RolUsuarioPortal`
- `Proveedor_SistemasIntegracion`
- `Proveedor_TipoContacto`
- `Proveedor_TipoDocumento`
- `Proveedor_TipoProveedor`
- `Proveedor_UsuariosPortal`
- `RH_Auditoria_Fiscal`
- `RH_Ausencias`
- `RH_Calendario_Laboral`
- `RH_Cat_Areas`
- `RH_Cat_Beneficios`
- `RH_Cat_ConceptosNomina`
- `RH_Cat_Departamentos`
- `RH_Cat_EstatusPeriodoNomina`
- `RH_Cat_Jornadas`
- `RH_Cat_MotivosBaja`
- `RH_Cat_Puestos`
- `RH_Cat_RegimenContratacion`
- `RH_Cat_Sucursales`
- `RH_Cat_SucursalesFiscal`
- `RH_Cat_TiposAusencia`
- `RH_Cat_TiposConceptoNomina`
- `RH_Cat_TiposContrato`
- `RH_Cat_TiposPeriodoNomina`
- `RH_Cat_Turnos`
- `RH_Colaboradores_Beneficios`
- `RH_Colaboradores_ContactosEmergencia`
- `RH_Colaboradores_Dependientes`
- `RH_Colaboradores_Documentos`
- `RH_Colaboradores_Domicilios`
- `RH_Contratos`
- `RH_Finiquitos`
- `RH_Finiquitos_Detalle`
- `RH_Flujo_Nomina_Sucursal`
- `RH_GruposNomina`
- `RH_Historial_Puestos`
- `RH_Historial_Salarios`
- `RH_Homologacion_Equivalencias`
- `RH_IMSS_Movimientos`
- `RH_Incidencias_Nomina`
- `RH_Nomina`
- `RH_Nomina_Detalle`
- `RH_Nomina_Dispersion`
- `RH_Nomina_Recibos`
- `RH_Periodos_Nomina`
- `RH_Prestamos`
- `RH_Prestamos_Detalle`
- `RH_Reloj_Checador`
- `RH_Vacaciones_Movimientos`
- `RH_Vacaciones_Saldos`
- `Scheduler_BitacoraJobs`
- `Scheduler_InventariosProcesados`
- `Scheduler_PedidosProcesados`
- `Servidores_Conexiones`
- `Servidores_Conexiones_backup_tipos_enriq_20260513_0840`
- `Servidores_Conexiones_backup_tipos_mov_20260513_0729`
- `Servidores_Conexiones_Log`
- `Servidores_Status`
- `Sesiones`
- `SesionesHistorico`
- `Sistema_Capacidades`
- `Sistema_Catalogo`
- `Sistema_Empresas`
- `Sistema_EmpresasAlias`
- `Sistema_EmpresasMongoMap`
- `Sistema_EmpresasServidores`
- `Sistema_Gobierno_Tablas`
- `Sistema_HorariosServicioUnidad`
- `Sistema_Migracion_MongoSQL_Mapeo`
- `Sistema_Modulos`
- `Sistema_ModulosMenus`
- `Sistema_ModulosPermisos`
- `Sistema_ModulosVisibilidad`
- `Sistema_RBAC_Permisos`
- `Sistema_RBAC_Roles`
- `Sistema_RBAC_RolesPermisos`
- `Sistema_ServidorSucursalesConfig`
- `Sistema_Sucursales`
- `Sistema_SucursalServidorConfig`
- `Sistema_SucursalServidorMapeo`
- `Sistema_Tipos`
- `Sistema_TiposVariantes`
- `Sistema_TurnosOperativosUnidad`
- `Sistema_UnidadesNegocioPerfilDigital`
- `Sync_Control_Ejecuciones`
- `Sync_Customers`
- `Sync_Impuestos_Origen`
- `Sync_Inventory`
- `Sync_KPI_Ventas_Unidades`
- `Sync_Logs`
- `Sync_Menus`
- `Sync_Mesas`
- `Sync_Metas_Comerciales`
- `Sync_Movimientos_Detalle`
- `Sync_Precios_Historicos`
- `Sync_Productos_Elaborados`
- `Sync_Productos_Insumos`
- `Sync_Productos_Recetas`
- `Sync_Purchases`
- `Sync_Response_Cache`
- `Sync_Ticket_Perfecto`
- `Sync_Token_Ledger`
- `Sync_Ventas_Historicas`
- `Sync_Ventas_PorDiaSemana`
- `Sync_Ventas_PorHora`
- `Sync_Vtiger_Contactos`
- `Sync_Vtiger_Cuentas`
- `Sync_Vtiger_Leads`
- `Sync_Vtiger_Log`
- `Sync_Vtiger_Oportunidades`
- `Sys_Roles`
- `Sys_Scheduler_Jobs`
- `Sys_Usuarios`
- `Tablajeria_ConfigContable`
- `Tablajeria_CosteoDetalle`
- `Tablajeria_CosteoProduccion`
- `Tablajeria_MovimientosInventario`
- `Tablajeria_PolizasContables`
- `Tablajeria_PolizasDetalle`
- `TableroEjecutivoCache`
- `Tareas_Inventario`
- `Unidades_Negocio`
- `Usuario_Acciones`
- `Usuario_AlmacenesAsignacion`
- `Usuario_Autorizaciones`
- `Usuario_AutorizacionesDetalle`
- `Usuario_Catalogo`
- `Usuario_EmpresasAsignacion`
- `Usuario_LogAccesos`
- `Usuario_LogActividades`
- `Usuario_LogRBACVerificacion`
- `Usuario_LogRecuperacion`
- `Usuario_MatrizAutorizacion`
- `Usuario_MigracionMongoTrace`
- `Usuario_Modulos`
- `Usuario_PermisosRolModulo`
- `Usuario_PortalConfiguracion`
- `Usuario_RateLimitRecuperacion`
- `Usuario_Roles`
- `Usuario_RolesAsignacion`
- `Usuario_ServidoresAsignacion`
- `Usuario_Sesiones`
- `Usuario_SucursalesAsignacion`
- `Usuario_TiposAutorizacion`
- `Usuario_TokensRecuperacion`
- `Venta_Cat_EstatusRemision`
- `Venta_CondicionesPago`
- `Venta_Cotizaciones`
- `Venta_CotizacionesDetalle`
- `Venta_CotizacionesEstatus`
- `Venta_Detalle`
- `Venta_Encabezado`
- `Venta_Estatus`
- `Venta_FormaPago`
- `Venta_ListasPrecios`
- `Venta_ListasPreciosDetalle`
- `Venta_Pagos`
- `Venta_Pedidos`
- `Venta_PedidosDetalle`
- `Venta_PedidosEstatus`
- `Venta_Remisiones`
- `Venta_RemisionesDetalle`
- `Venta_RemisionesHistorial`
- `Workflow_DecisionesAuditoria`
- `Workflow_DetalleDiferencias`
- `Workflow_Inventarios`
- `Workflow_Justificaciones`

</details>

---

## 6. REGLAS DE ARQUITECTURA MÁXIMAS

### 🔴 REGLA INQUEBRANTABLE

> **Cualquier tabla nueva debe validarse contra `Sistema_Gobierno_Tablas` antes de crearse.**

### Checklist Obligatorio para Nuevas Tablas:

1. ✅ Verificar que no existe tabla similar en `Sistema_Gobierno_Tablas`
2. ✅ Verificar que no existe tabla LEGADO con mismo propósito
3. ✅ Definir clasificación: CANONICA, SINCRONIZADA, DERIVADA
4. ✅ Registrar en `Sistema_Gobierno_Tablas` ANTES de CREATE TABLE
5. ✅ Documentar fuente de verdad y relación con otras tablas

### Query de Validación:

```sql
-- Antes de crear cualquier tabla nueva, ejecutar:
SELECT * FROM Sistema_Gobierno_Tablas
WHERE nombre_tabla LIKE '%<nombre_similar>%'
   OR modulo = '<modulo_destino>';

-- Si no existe conflicto, registrar primero:
INSERT INTO Sistema_Gobierno_Tablas (nombre_tabla, modulo, categoria, estado)
VALUES ('<nueva_tabla>', '<modulo>', '<categoria>', 'ACTIVA');
```

---

## 7. ACCIONES RECOMENDADAS (NO EJECUTAR AÚN)

### Prioridad P0 (Crítico)

1. **NO crear tablas sin validar** contra `Sistema_Gobierno_Tablas`
2. **Deprecar uso de** `Products`, `Fact_Ventas_Consolidadas`, `Config_Horarios`
3. **Migrar queries** que usen tablas LEGADO a tablas NUEVA

### Prioridad P1 (Alto)

1. Registrar las 253+ tablas sin clasificar en `Sistema_Gobierno_Tablas`
2. Definir plan de migración para tablas `FIN_*` → `Finanzas_*`
3. Completar migración `Sys_*` → `Sistema_*`

### Prioridad P2 (Medio)

1. Documentar tablas CRM (EXTERNA_REFERENCIADA)
2. Clasificar tablas ActivoFijo_*, Compras_*, Almacen_*
3. Crear vistas de compatibilidad para código legacy

---

*Documento generado automáticamente. NO MODIFICAR ESTRUCTURA SIN APROBACIÓN.*

**Última actualización:** 2026-06-02T10:04:26.785621