# Auditoría Menú SQL vs Rutas Frontend
- Fecha UTC: 2026-06-23T10:46:36.177370
- Rutas frontend auditadas: 58
- Rutas menú SQL activas: 54

## Frontend sin menú SQL
- `/admin` → `AdminHub`
- `/admin/centro-excepciones` → `CentroExcepciones`
- `/admin/dashboard-ejecutivo` → `DashboardEjecutivo`
- `/comercial/pricing-ia` → `PricingIA`
- `/crm/actividades` → `ActividadesPage`
- `/crm/operaciones` → `OperacionesPage`
- `/crm/implementaciones` → `ImplementacionesPage`
- `/crm/postventa` → `PostventaPage`
- `/crm/kpis` → `KPIsPage`
- `/proveedores` → `Proveedores`
- `/produccion` → `Produccion`
- `/produccion/tablajeria` → `TablajeriaDashboard`
- `/produccion/tablajeria/plantillas` → `PlantillasPage`
- `/produccion/tablajeria/ordenes` → `OrdenesPage`
- `/produccion/tablajeria/captura-directa` → `CapturaDirectaPage`
- `/tablajeria` → `TablajeriaDashboard`
- `/cava-socios/socios/nuevo` → `SocioForm`
- `/admin/dba-credential` → `DBACredentialManager`
- `/super-caja` → `SuperCajaPage`
- `/comandero` → `ComanderoPage`

## Menús SQL sin ruta frontend
- MenuID `26` `comercial.clientes` → `/comercial/clientes`
- MenuID `65` `comandero.mesas` → `/comandero/mesas`
- MenuID `63` `pos.dashboard` → `/pos/generico`
- MenuID `64` `pos.caja` → `/pos/caja`
- MenuID `66` `comandero.comandas` → `/comandero/comandas`
- MenuID `67` `comandero.cuentas` → `/comandero/cuentas`
- MenuID `68` `comandero.cortes` → `/comandero/cortes`
- MenuID `38` `compras.proveedores` → `/compras/proveedores`
- MenuID `39` `compras.ordenes` → `/compras/ordenes`
- MenuID `41` `inventarios.existencias` → `/inventarios/existencias`
- MenuID `72` `edarsa_go.cobros` → `/edarsa-go`
- MenuID `73` `edarsa_go.links` → `/edarsa-go/links`
- MenuID `69` `portal.proveedores` → `/portal/proveedores`
- MenuID `70` `portal.comisionistas` → `/portal/comisionistas`
- MenuID `71` `portal.clientes` → `/portal/clientes`
- MenuID `74` `chef_ia.calidad` → `/chef-ia`