# Auditoría de Integridad Menú ↔ Route ↔ RBAC

Generado: `20260623_110603`

- Rutas frontend auditadas: **58**
- Menús SQL activos auditados: **63**
- Rutas frontend sin menú SQL: **11**
- Menús SQL sin route frontend: **16**
- Módulos RBAC con permisos pero sin menú SQL: **44**

## Rutas frontend sin menú SQL

- `/admin` → `AdminHub`
- `/admin/dashboard-ejecutivo` → `DashboardEjecutivo`
- `/proveedores` → `Proveedores`
- `/produccion` → `Produccion`
- `/produccion/tablajeria` → `TablajeriaDashboard`
- `/produccion/tablajeria/plantillas` → `PlantillasPage`
- `/produccion/tablajeria/ordenes` → `OrdenesPage`
- `/produccion/tablajeria/captura-directa` → `CapturaDirectaPage`
- `/tablajeria` → `TablajeriaDashboard`
- `/cava-socios/socios/nuevo` → `SocioForm`
- `/admin/dba-credential` → `DBACredentialManager`

## Menús SQL sin route frontend

- `/comercial/clientes` → `comercial.clientes` / `Clientes`
- `/comandero/mesas` → `comandero.mesas` / `Mesas`
- `/pos/generico` → `pos.dashboard` / `Punto de Venta`
- `/pos/caja` → `pos.caja` / `Caja`
- `/comandero/comandas` → `comandero.comandas` / `Comandas`
- `/comandero/cuentas` → `comandero.cuentas` / `Cuentas`
- `/comandero/cortes` → `comandero.cortes` / `Cortes`
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
- `SCHEDULER` → `Programador de Tareas`
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