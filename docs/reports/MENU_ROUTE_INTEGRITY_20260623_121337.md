# Auditoría de Integridad Menú ↔ Route ↔ RBAC

Generado: `20260623_121337`

- Rutas frontend auditadas: **67**
- Menús SQL activos auditados: **60**
- Rutas frontend sin menú SQL bruto: **10**
- Rutas frontend sin menú SQL accionables: **0**
- Rutas frontend técnicas/alias/formularios/sensibles: **10**
- Menús SQL sin route frontend: **11**
- Módulos RBAC con permisos pero sin menú SQL: **43**

## Rutas frontend sin menú SQL accionables

- Sin pendientes accionables.

## Rutas frontend sin menú SQL clasificadas como no accionables

- `/admin` → `AdminHub` / `hub_internal` / `no_menu_sql` / Hub interno de administracion; no debe contarse como menu operativo independiente.
- `/admin/dashboard-ejecutivo` → `DashboardEjecutivo` / `alias_redirect` / `no_menu_sql` / Duplicado legacy de /tablero-ejecutivo, que ya existe en SQL.
- `/produccion` → `Produccion` / `legacy_route` / `no_menu_sql` / Ruta contenedora legacy de produccion; no insertar sin validar menu funcional activo.
- `/produccion/tablajeria` → `TablajeriaDashboard` / `legacy_route` / `no_menu_sql` / Alias legacy de TablajeriaDashboard; evitar duplicar menu.
- `/produccion/tablajeria/plantillas` → `PlantillasPage` / `legacy_route` / `no_menu_sql` / Ruta legacy de plantillas de tablajeria; evitar duplicar menu.
- `/produccion/tablajeria/ordenes` → `OrdenesPage` / `legacy_route` / `no_menu_sql` / Ruta legacy de ordenes de tablajeria; evitar duplicar menu.
- `/produccion/tablajeria/captura-directa` → `CapturaDirectaPage` / `legacy_route` / `no_menu_sql` / Ruta legacy de captura directa de tablajeria; evitar duplicar menu.
- `/tablajeria` → `TablajeriaDashboard` / `alias_redirect` / `no_menu_sql` / Alias de /tablajeria/dashboard; no debe crear menu duplicado.
- `/cava-socios/socios/nuevo` → `SocioForm` / `internal_form` / `no_menu_sql` / Formulario interno de alta; debe abrir desde el flujo de socios, no como menu.
- `/admin/dba-credential` → `DBACredentialManager` / `sensitive_superadmin` / `no_menu_sql` / Herramienta sensible restringida a SuperAdministrador; no debe exponerse como menu general.

## Menús SQL sin route frontend

- `/pos/generico` → `pos.dashboard` / `Punto de Venta`
- `/pos/caja` → `pos.caja` / `Caja`
- `/compras/proveedores` → `compras.proveedores` / `Proveedores`
- `/compras/ordenes` → `compras.ordenes` / `Órdenes de Compra`
- `/inventarios/existencias` → `inventarios.existencias` / `Existencias`
- `/edarsa-go` → `edarsa_go.cobros` / `EDARSA GO`
- `/edarsa-go/links` → `edarsa_go.links` / `Links de Pago`
- `/portal/proveedores` → `portal.proveedores` / `Portal Proveedores`
- `/portal/comisionistas` → `portal.comisionistas` / `Portal Comisionistas`
- `/portal/clientes` → `portal.clientes` / `Portal Clientes`
- `/chef-ia` → `chef_ia.calidad` / `Chef IA`

## Módulos RBAC con permisos pero sin menú SQL

- `AUDITORIAS` → `Auditorías Programadas`
- `comercial.benchmark` → `Benchmark de Productos`
- `cava_socios.botellas` → `Botellas`
- `tablajeria.captura_directa` → `Captura Directa`
- `cava_socios.cargos` → `Cargos`
- `CARGOS` → `Cargos Económicos`
- `crm.clientes` → `Clientes`
- `comercial.competidores` → `Competidores`
- `COMPRAS_FACT` → `Compras`
- `crm.config` → `Configuración`
- `tablajeria.config` → `Configuración`
- `cava_socios.config` → `Configuración`
- `cava_socios.consumos` → `Consumos`
- `crm.contactos` → `Contactos`
- `tablajeria.costeo` → `Costeo`
- `crm.cotizaciones` → `Cotizaciones`
- `COMPRAS_COT` → `Cotizaciones de compra`
- `VENTA_COT` → `Cotizaciones de venta`
- `cava_socios.dashboard` → `Dashboard Cava`
- `RBAC` → `Gestión RBAC`
- `crm.integraciones` → `Integraciones`
- `INTELIGENCIA_COMERCIAL` → `Inteligencia Comercial`
- `VENTA_LISTAS` → `Listas de precios`
- `tablajeria.mermas` → `Mermas`
- `cava_socios.movimientos` → `Movimientos`
- `NOTIFICACIONES` → `Notificaciones`
- `COMPRAS_OC` → `Ordenes de compra`
- `TES_PAGOS` → `Pagos`
- `crm.pedidos` → `Pedidos`
- `VENTA_PED` → `Pedidos de venta`
- `comercial.perfil_unidad` → `Perfil Digital de Unidad`
- `tablajeria.polizas` → `Pólizas Contables`
- `comercial.precios_sugeridos` → `Precios Sugeridos`
- `crm.remisiones` → `Remisiones`
- `tablajeria.rendimientos` → `Rendimientos`
- `cava_socios.reportes` → `Reportes`
- `RESPONSABILIDAD` → `Responsabilidad Económica`
- `SEGURIDAD` → `Seguridad`
- `tablajeria.sync` → `Sincronización`
- `SLA` → `SLA y Métricas`
- `cava_socios.socios` → `Socios`
- `tablajeria` → `Tablajería`
- `WORKFLOW` → `Workflows`