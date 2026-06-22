# Graph Report - /app/frontend/src  (2026-06-16)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1274 nodes · 2660 edges · 110 communities (91 shown, 19 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 16 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ded4bc56`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 106|Community 106]]

## God Nodes (most connected - your core abstractions)
1. `logger` - 48 edges
2. `apiRequest()` - 44 edges
3. `Button` - 40 edges
4. `Card` - 33 edges
5. `CardContent` - 33 edges
6. `api` - 33 edges
7. `CardHeader` - 27 edges
8. `CardTitle` - 27 edges
9. `getSessionUser()` - 24 edges
10. `Input` - 23 edges

## Surprising Connections (you probably didn't know these)
- `handleSave()` --calls--> `Alert`  [INFERRED]
  lib/handleSaveOffline.js → components/ui/alert.jsx
- `Layout()` --calls--> `useAuth()`  [INFERRED]
  pages/Layout.js → contexts/AuthContext.jsx
- `Login()` --calls--> `useAuth()`  [INFERRED]
  pages/Login.js → contexts/AuthContext.jsx
- `Reportes()` --calls--> `useAuth()`  [INFERRED]
  pages/Reportes.js → contexts/AuthContext.jsx
- `Usuarios()` --calls--> `useAuth()`  [INFERRED]
  pages/Usuarios.js → contexts/AuthContext.jsx

## Import Cycles
- 1-file cycle: `App.js -> App.js`

## Communities (110 total, 19 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (67): useCatalogoConsultasData(), EDITABLES, GestionSolicitudesCatalogo(), BotonSolicitarAlta(), CAMPOS_CATALOGO, AlmacenesSelector(), EmptyState(), EstadoPedidoBadge() (+59 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (60): AccionesAuditoria(), CalendarioAuditorias(), EmptyState(), ESTADO_CONFIG, EstadoBadge(), KPIsGrid(), MESES, ConsultasList() (+52 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (40): DetalleSolicitudModal(), formatCurrency(), formatDate(), formatPercent(), InsumosModal(), RecetaModal(), SimulacionPrecioModal(), TabPreciosSugeridos() (+32 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (39): defaultFavoriteMenuIds, enterpriseMenuGroups, filterEnterpriseMenuByRole(), flattenEnterpriseMenu(), formatNombreSucursal(), NOMBRE_SUCURSAL_MAP, getIcon(), ICONS (+31 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (30): SyncStatusIndicator(), useSyncStatus(), cleanAllExpired(), cleanExpired(), clearStore(), get(), getAll(), getStats() (+22 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (16): formatCurrency(), formatDate(), formatPercent(), ResultadoAnalisisModal(), TabDashboardIA(), ChartAnalisisPorDia(), ChartDistribucionConfianza(), ChartProductosMasAnalizados() (+8 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (43): actualizarConfiguracion(), actualizarResponsabilidadConfiguracion(), apiRequest(), aprobarResponsabilidad(), asignarTarea(), calcularResponsabilidad(), cambiarEstadoWorkflow(), checkHealth() (+35 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (27): DetalleProductoModal(), useAuth(), withAuth(), ESTADO_INICIAL, useDetalleProducto(), fechaMinimaInventarios(), filtrarInventariosFinales(), AnalisisCompras() (+19 more)

### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (18): formatDate(), TabOperativasCompras(), COLORS, Dashboard(), formatCurrency(), formatNumber(), getAlmacenPlaceholder(), Reportes() (+10 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (13): RhAsistencia(), RhColaboradores(), RhDashboard(), RhIncidencias(), RhNominas(), ESTATUS_CANDIDATO, RhReclutamiento(), EstatusLaboralBadge() (+5 more)

### Community 10 - "Community 10"
Cohesion: 0.18
Nodes (20): apiGet(), ESTADO, EstadoVacio(), TEXTOS, ExportButtons(), PERIODOS, PeriodoSelector(), money() (+12 more)

### Community 11 - "Community 11"
Cohesion: 0.09
Nodes (8): App(), SUBDOMAIN_CONFIG, root, AdminHub(), CentroExcepciones(), DashboardEjecutivo(), PortalProveedoresApp(), PortalInteligenciaApp()

### Community 12 - "Community 12"
Cohesion: 0.10
Nodes (14): buildDescriptor(), DEFAULT_GROUP, GROUP_OPTS, MESES, money(), NOW, ReportesISCAMPage(), SUBTABS (+6 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (8): AlertasBanner(), severityConfig, KPICards(), estadoConfig, TareaList(), tipoConfig, estadoConfig, WorkflowList()

### Community 14 - "Community 14"
Cohesion: 0.12
Nodes (7): AccionesTesoreriaCard(), formatDate(), AprobadoCard(), formatDate(), RechazadoCard(), formatDate(), PeriodoEstadisticoCard()

### Community 15 - "Community 15"
Cohesion: 0.19
Nodes (15): apiPost(), clearIntelSessionFlag(), getMeIntel(), haySesion(), haySesionIntel(), intelApi, loginIntel(), logoutIntel() (+7 more)

### Community 16 - "Community 16"
Cohesion: 0.14
Nodes (13): PendienteSync(), AnalisisVentas(), chartTip, COLORS, ICONS, KCOLOR, KpisMes(), money() (+5 more)

### Community 17 - "Community 17"
Cohesion: 0.15
Nodes (5): api, refreshSubscribers, ICONOS_DOMINIO, fetchConexionesExplorables(), fetchMenusUsuario()

### Community 18 - "Community 18"
Cohesion: 0.17
Nodes (13): ACCIONES_CONFIG, formatMXN(), ResponsabilidadAccionesModal(), ROLES, ACCIONES_POR_ESTADO, ESTADO_CONFIG, formatMXN(), HistorialPanel() (+5 more)

### Community 19 - "Community 19"
Cohesion: 0.21
Nodes (4): logger, fetchUnidadesNegocio(), getServerIdFromUnidad(), getSucursalOrigenIdFromUnidad()

### Community 20 - "Community 20"
Cohesion: 0.24
Nodes (14): AuthContext, clearMemoryToken(), setMemoryToken(), clearBrowserCaches(), clearCacheOnLogout(), clearLocalStorage(), clearPreviewBackendCache(), clearPreviewFrontendCache() (+6 more)

### Community 21 - "Community 21"
Cohesion: 0.18
Nodes (13): getUser(), hasRole(), isAuthenticated(), logout(), MisTareas(), Nominas(), RecursosHumanos(), Scheduler() (+5 more)

### Community 22 - "Community 22"
Cohesion: 0.12
Nodes (10): Menubar, MenubarCheckboxItem, MenubarContent, MenubarItem, MenubarLabel, MenubarRadioItem, MenubarSeparator, MenubarSubContent (+2 more)

### Community 23 - "Community 23"
Cohesion: 0.20
Nodes (7): BatchUploadPage(), DashboardPage(), InvoicesPage(), LoginPage(), PaymentsPage(), RegisterPage(), UploadInvoicePage()

### Community 24 - "Community 24"
Cohesion: 0.20
Nodes (11): formatPercent(), getNivelConfig(), getSeveridadConfig(), ModalEvaluarMargen(), ModalRegla(), ModalResolverRegla(), NivelBadge(), NIVELES_APLICACION (+3 more)

### Community 25 - "Community 25"
Cohesion: 0.44
Nodes (11): TesoreriaCorteZ(), ComparativaCard(), ConteoEfectivo(), CorteCard(), CuadreCard(), EmptyState(), FichaDepositoForm(), formatCurrency() (+3 more)

### Community 26 - "Community 26"
Cohesion: 0.37
Nodes (9): BitacoraRBAC(), BitacoraDetailModal(), BitacoraFilters(), BitacoraPagination(), BitacoraTable(), formatearFecha(), getResultadoBadge(), getTipoBadge() (+1 more)

### Community 27 - "Community 27"
Cohesion: 0.17
Nodes (3): TIPOS_BEBIDA, MEMBRESIA_BOTELLAS, TIPOS_MEMBRESIA

### Community 28 - "Community 28"
Cohesion: 0.26
Nodes (8): UnidadNegocioContextSelector(), useAccessContext(), useMenusByContext(), ICON_MAP, Layout(), fetchAccessContext(), getAuthHeaders(), selectAccessUnit()

### Community 29 - "Community 29"
Cohesion: 0.20
Nodes (4): ResyncPanel(), RIESGO_COLOR, DataStatusBadge(), formatTime()

### Community 30 - "Community 30"
Cohesion: 0.25
Nodes (8): fMoney(), TicketDrilldownModal(), COLOR_CLS, DashboardIA(), formatMoney(), HORARIO_COLOR, HORARIO_ICON, money2()

### Community 32 - "Community 32"
Cohesion: 0.20
Nodes (3): getStatusConfig(), STATUS_CONFIG, StatusBadge()

### Community 33 - "Community 33"
Cohesion: 0.20
Nodes (5): useAuditoriasData(), AuditoriasProgramadas(), DIAS_SEMANA, FRECUENCIAS, TIPOS_AUDITORIA

### Community 34 - "Community 34"
Cohesion: 0.20
Nodes (6): API_TEST_TYPES, BLOCKED_API_PARAM_NAMES, MAX_ROWS_OPTIONS, SQL_PATTERN_KEYWORDS, SQL_TEST_TYPES, TIMEOUT_OPTIONS

### Community 35 - "Community 35"
Cohesion: 0.29
Nodes (9): actionTypes, addToRemoveQueue(), dispatch(), genId(), listeners, memoryState, reducer(), toast() (+1 more)

### Community 36 - "Community 36"
Cohesion: 0.20
Nodes (7): Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator

### Community 37 - "Community 37"
Cohesion: 0.20
Nodes (8): ContextMenuCheckboxItem, ContextMenuContent, ContextMenuItem, ContextMenuLabel, ContextMenuRadioItem, ContextMenuSeparator, ContextMenuSubContent, ContextMenuSubTrigger

### Community 38 - "Community 38"
Cohesion: 0.20
Nodes (8): DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuRadioItem, DropdownMenuSeparator, DropdownMenuSubContent, DropdownMenuSubTrigger

### Community 39 - "Community 39"
Cohesion: 0.20
Nodes (7): FormControl, FormDescription, FormFieldContext, FormItem, FormItemContext, FormLabel, FormMessage

### Community 40 - "Community 40"
Cohesion: 0.25
Nodes (5): Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage

### Community 41 - "Community 41"
Cohesion: 0.25
Nodes (6): Carousel, CarouselContent, CarouselContext, CarouselItem, CarouselNext, CarouselPrevious

### Community 42 - "Community 42"
Cohesion: 0.25
Nodes (4): DrawerContent, DrawerDescription, DrawerOverlay, DrawerTitle

### Community 43 - "Community 43"
Cohesion: 0.25
Nodes (7): NavigationMenu, NavigationMenuContent, NavigationMenuIndicator, NavigationMenuList, NavigationMenuTrigger, navigationMenuTriggerStyle, NavigationMenuViewport

### Community 44 - "Community 44"
Cohesion: 0.25
Nodes (5): SheetContent, SheetDescription, SheetOverlay, SheetTitle, sheetVariants

### Community 45 - "Community 45"
Cohesion: 0.25
Nodes (7): Toast, ToastAction, ToastClose, ToastDescription, ToastTitle, toastVariants, ToastViewport

### Community 47 - "Community 47"
Cohesion: 0.38
Nodes (4): BenchmarkGrupoPage(), fmtBy(), fmtNum(), FORMATTERS

### Community 49 - "Community 49"
Cohesion: 0.40
Nodes (4): PortalProveedoresTab(), Proveedores(), UsuariosInteligencia(), getFilterLabel()

### Community 52 - "Community 52"
Cohesion: 0.60
Nodes (5): formatMXN(), MetricaMini(), ResponsabilidadCard(), SucursalRow(), WorkflowRow()

### Community 53 - "Community 53"
Cohesion: 0.40
Nodes (4): InputOTP, InputOTPGroup, InputOTPSeparator, InputOTPSlot

### Community 58 - "Community 58"
Cohesion: 0.50
Nodes (3): AccordionContent, AccordionItem, AccordionTrigger

### Community 59 - "Community 59"
Cohesion: 0.50
Nodes (3): Avatar, AvatarFallback, AvatarImage

### Community 60 - "Community 60"
Cohesion: 0.50
Nodes (3): ToggleGroup, ToggleGroupContext, ToggleGroupItem

## Knowledge Gaps
- **206 isolated node(s):** `SUBDOMAIN_CONFIG`, `CAMPOS_CATALOGO`, `QUERY_TYPES`, `SQL_TEST_TYPES`, `API_TEST_TYPES` (+201 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `logger` connect `Community 19` to `Community 0`, `Community 1`, `Community 2`, `Community 33`, `Community 4`, `Community 3`, `Community 6`, `Community 7`, `Community 8`, `Community 13`, `Community 17`, `Community 18`, `Community 49`, `Community 23`, `Community 57`, `Community 29`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `api` connect `Community 17` to `Community 0`, `Community 1`, `Community 33`, `Community 3`, `Community 2`, `Community 7`, `Community 15`, `Community 49`, `Community 19`, `Community 20`, `Community 21`, `Community 57`, `Community 29`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `ExportButtons()` connect `Community 10` to `Community 0`, `Community 2`, `Community 7`, `Community 12`, `Community 16`, `Community 30`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **What connects `SUBDOMAIN_CONFIG`, `CAMPOS_CATALOGO`, `QUERY_TYPES` to the rest of the system?**
  _206 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05247376311844078 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.060398078242964996 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.06057945566286216 - nodes in this community are weakly interconnected._