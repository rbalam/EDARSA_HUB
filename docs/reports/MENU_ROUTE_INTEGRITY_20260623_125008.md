# Auditoría de Integridad Menú ↔ Route ↔ RBAC

Generado: `20260623_125008`

- Rutas frontend auditadas: **78**
- Menús SQL activos auditados: **61**
- Rutas frontend sin menú SQL bruto: **10**
- Rutas frontend sin menú SQL accionables: **0**
- Rutas frontend técnicas/alias/formularios/sensibles: **10**
- Menús SQL sin route frontend: **0**
- Módulos RBAC con permisos pero sin menú SQL: **0**

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


## Módulos RBAC con permisos pero sin menú SQL
