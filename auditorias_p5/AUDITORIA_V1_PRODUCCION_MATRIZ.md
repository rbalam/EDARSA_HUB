# AUDITORÍA v1.0 — Blindaje para Producción (EDARSA HUB)
**Fase 0 — SOLO AUDITORÍA. No se realizaron cambios de código.**
Fecha: 2026-06-07 · Método: lectura de código + pruebas de endpoints con token admin (`admin@edarsa.com`) + análisis de logs de backend.

## Máximas evaluadas
1. **NO MongoDB** (ninguna fuente productiva en Mongo).
2. **NO-LIVE**: única conexión live permitida = **EDARSAHUB SQL** (cerebro). Prohibido consultar servidores operativos (POS/sucursales) en vivo.
3. **NO duplicar** flujos/tablas/endpoints/usuarios/unidades.
4. Todo evaluado contra: auth, RBAC, filtros, tablas canónicas, unidades de negocio, usuarios y flujos reales.

---

## 1) HALLAZGOS TRANSVERSALES (cross-cutting)

### 1.1 NO-MONGO — Estado: ✅ bloqueado en el núcleo, ⚠️ residual alcanzable en Comercial
- **Núcleo OK**: `core/db.py` → `get_mongo_db()` lanza `RuntimeError("MongoDB no es fuente productiva. Usar SQL Server.")` (línea ~608). `get_db()` en repos comerciales retorna `None` ("MongoDB deprecado").
- **Residual ALCANZABLE (riesgo de crash)**: `modules/comercial/cache_service.py`, `modules/comercial/kpis_repository.py`, `modules/comercial/historical_kpis_repository.py` aún ejecutan `db.coleccion.find_one/insert_one/update_one` con `db = get_db() = None` → `AttributeError` si el flujo se alcanza.
- **NO es Mongo**: `modules/fase2_operativo/*` usa un **repositorio SQL** con API estilo-Mongo (`find_one`/`insert_one` mapeados a SQL). Correcto, no es Mongo real.
- **Recomendación**: eliminar/guardar las llamadas Mongo de `cache_service`/`kpis_repository`/`historical_kpis_repository` (reemplazar por cache SQL o no-op).

### 1.2 NO-LIVE — Estado: ⚠️ enforced en Comercial, 🔴 violado en Reportes/Inventarios/Finanzas-sync/Explorador
- **Comercial legacy**: ENFORCED. `modules/comercial/routes.py:182` → `LEGACY_LIVE_DISABLED`; `/api/comercial/dashboard/{id}` responde `source_status: ERROR, "Servidor no encontrado en configuración"` (no conecta live). ✅
- **Intentos de conexión LIVE a servidores operativos detectados en logs** (🔴 violación activa, fallan):
  - `130mid.ddns.net` (`Invalid column name 'idcheque'`)
  - `servercienfuegos.ddns.net:6669/softrestaurant95pro` y `/Tablajeria` (`Adaptive Server is unavailable`)
  - `serverestelar.ddns.net,6969` (`idcheque`)
  - `54.39.104.176:1433/softrestaurant12` (`login HRLectura` rechazado; intento de abrir BD POS operativa)
  - Origen probable: `modules/finanzas` (sync cortes SoftRestaurant / propinas MPRO), reportes de inventario en `Reportes.js` (`/reports/*`, `/servers/{id}/inventarios`), tablajería sync, **Explorador BD**.
- **Recomendación**: identificar y deshabilitar en runtime web toda ruta/job que invoque `execute_sql_query(host_operativo,...)`; servir solo desde tablas `Sync_*` en EDARSAHUB.

### 1.3 Bug destructivo (regex) — Tablero Ejecutivo 🔴
- `modules/dashboard_ejecutivo/routes.py:32` referencia la vista corrupta `vw_vw_vw_vw_Comercial_KPIs_Diarios_v2_Runtime_Runtime_Runtime_Runtime` → **500** en `/api/dashboard-ejecutivo/resumen`.
- Vista canónica real existente: **`vw_Comercial_KPIs_Diarios_v2_Runtime`** (verificado en `sys.objects`).
- Patrón: find/replace destructivo que antepuso `vw_`×4 y agregó `_Runtime`×4. (Justo el tipo de regex destructiva que las máximas prohíben.)

### 1.4 Explorador BD roto 🔴
- Log: `[EXPLORADOR][SQL] 130° MERIDA: cannot import name '_execute_sql_direct_with_error' from 'core.db'` → import inexistente. Además consulta servidores operativos (live).

### 1.5 Infra / ruido
- `libodbc.so.2: cannot open shared object file` → driver pyodbc ausente; el fallback de `execute_sql_query` falla para algunas conexiones.
- Spam de fondo: `modules/fase2_operativo/services/sla_service` → `Error actualizando SLA de tarea None: 'NoneType' object has no attribute 'notification_config'` (repetitivo).

### 1.6 RBAC / filtros por Unidad de Negocio — ⚠️
- La mayoría de routers usan `Depends(get_current_user)` (solo autenticación). Endpoints como `dashboard_ejecutivo/resumen` y `rentabilidad` **no** aplican filtro por unidad de negocio ni rol a nivel de endpoint (retornan todas las unidades). RBAC se ejerce sobre todo en visibilidad de menús (`Sistema_Modulos`) y en algunos servicios.
- **Recomendación**: definir política de scope por unidad en endpoints de datos sensibles (ventas/finanzas).

---

## 2) MATRIZ POR MENÚ (orden de prioridad)

> Estados: **OK** = OK producción · **MENOR** = requiere ajuste menor · **MAYOR** = requiere ajuste mayor · **BLOQ** = bloqueado.

| # | Menú | Front principal | Back principal | Auth | RBAC | Filtros | Tablas SQL canónicas | Legacy/Stub | Live prohibido | Mongo residual | Estado | Riesgo |
|---|------|-----------------|----------------|------|------|---------|----------------------|-------------|----------------|----------------|--------|--------|
| 1 | **Dirección / Tablero Ejecutivo** | `pages/TableroEjecutivo.js` | `modules/dashboard_ejecutivo/routes.py` + `rentabilidad` + `v2/comercial` | get_current_user | Solo auth, sin scope unidad | Periodo (fechas); sin filtro unidad | `vw_Comercial_KPIs_Diarios_v2_Runtime`, `Sync_Precios_Historicos`, `Sync_Productos`, `Compras_*`, `Servidores_Conexiones` | Llama legacy `/comercial/{server_id}` (degradado) | NO conecta (controlado) | No | **BLOQ** | Alto: 500 por vista corrupta |
| 2 | **Comercial / Ventas** | `pages/Comercial.js` | `modules/comercial/routes.py` + `repository.py` | get_current_user | Solo auth | server/sucursal (selección) | `Comercial_KPIs_Diarios_v2`, `Sync_*`, `Servidores_Conexiones` | Endpoints legacy `/comercial/{id}` (LIVE disabled) | ENFORCED (controlado) | **SÍ** (`cache_service`, `kpis_repository`) | **MAYOR** | Medio-alto |
| 3 | **Portal Inteligencia Comercial** | `portal-inteligencia/App.jsx` | `inteligencia_router` (+fase1) | propia del portal | por portal | propios | EDARSAHUB (health 200) | Subapp separada | Verificar | Verificar | **MENOR** | Bajo |
| 4 | **Finanzas** | `pages/Finanzas.js` | `cxp/ingresos/tesoreria/cuentas/saldos/health` | (router) | parcial | servidor/fecha | `Finanzas_CortesCaja_SyncLog`, `Finanzas_PropinasTPV_SyncLog`, cuentas bancarias | `sql_subprocess_helper` | **SÍ** (sync cortes/propinas a operativos en logs) | No | **MAYOR/BLOQ** | Alto: `/finanzas/health` 502 |
| 5 | **Operación** | `pages/Reportes.js` (tab operativo) | `modules/fase2_operativo` (`/api/v2`) | authedFetch (Bearer) | RBAC por contexto v2 | unidad/servidor/fecha | `Workflow_Inventarios`, `Tareas_Inventario`, `Operativo_ResponsabilidadEconomica`, `Inventarios_*` | repo SQL estilo-Mongo (OK) | **SÍ** en reportes `/reports/*`, `/servers/{id}/inventarios` (operativos en logs) | No | Dashboard **OK**; reportes inventario **MAYOR** | Medio |
| 6 | **Tareas / Mis Tareas / Alertas** | `pages/MisTareas.js`, `pages/Alertas.js` | `fase2_operativo` v2, `sistema/tareas`, `/alerts`, `sistema/solicitudes` | get_user_dual/Bearer | sí (solicitudes/aprobación) | usuario/estado | `Sistema_Tareas`, `Tareas_Inventario`, alertas v2 | — | No | No | **OK** (verificar acciones solicitudes) | Bajo |
| 7a | **Servidores** | `pages/Servidores.js` | `api_connections_router`, `servers`, `catalogos/sistemas` | require_admin | admin | — | `Servidores_Conexiones`, `Sistema_Capacidades` | — | Funciones admin `test-connectivity/test-query` SÍ conectan (legítimo admin) | No | **OK** (acotar test a admin) | Bajo-medio |
| 7b | **Exploración de BD** | `pages/ExploradorBD.js` | `modules/explorador/routes.py` | get_current_user | — | server/tabla | metadata de servidor | import roto | **SÍ** (consulta tablas de operativos) | No | **BLOQ** | Alto: import inexistente |
| 7c | **Catálogos SQL** | `pages/CatalogoConsultas.js` | `consultas_sql_router`/`sql_compat_bridge` | get_current_user | — | consulta | SQL_COMPAT_BRIDGE (EDARSAHUB) | bridge compat | No (EDARSAHUB) | No | **MENOR** | Bajo |
| 7d | **Automatizaciones** | `pages/AuditoriasProgramadas.js` | `fase2_operativo` (auditorías/automatización) | Bearer | sí | unidad | `automatizacion_inventarios_*`, `Operativo_AuditoriasProgramadas` | repo SQL (OK) | No | No | **MENOR** (tablas vacías; verificar flujo) | Bajo |
| 7e | **Asignaciones** | `pages/ConfigAsignaciones.js` | asignaciones servidores/sucursales/almacenes | require_admin | admin | unidad | `Usuario_ServidoresAsignacion`, `Usuario_SucursalesAsignacion`, `Usuario_AlmacenesAsignacion` | — | No | No | **MENOR** (ruta corregida 2026-06-07) | Bajo |
| 7f | **Personas** | `pages/RecursosHumanos.js` | `rh_router`, `nomina`, `rh_importador` | (router) | parcial | — | `rrhh_*`, `nomina_*` (EDARSAHUB) | — | No | No | **MENOR** (200 en colaboradores/nómina) | Bajo |
| 7g | **Configuración Operativa** | `pages/ConfiguracionOperativaUnidades.js` | `config_operativa_router` | require_admin | admin | unidad | `Sistema_TurnosOperativosUnidad`, config operativa | — | No | No | **MENOR** (confirmar ruta/endpoint exacto) | Bajo |

---

## 3) PRUEBAS DE ENDPOINTS (evidencia, token admin)

| Endpoint | HTTP | Nota |
|----------|------|------|
| `/api/auth/access-context` | 200 | OK |
| `/api/sistema/menus/usuario` | 200 | OK |
| `/api/unidades-negocio` | 200 | OK |
| `/api/servers` | 200 | OK |
| `/api/v2/health` · `/v2/dashboard/resumen` · `/v2/tareas` · `/v2/workflows` · `/v2/dashboard/alertas` · `/v2/responsabilidad/metricas` | 200 | Operación v2 sano |
| `/api/dashboard-ejecutivo/resumen` | **500** | Vista corrupta `vw_vw_vw_vw_..._Runtime_Runtime...` |
| `/api/rentabilidad/resumen` | 200 | OK |
| `/api/v2/comercial/dashboard` | 422 | Requiere query params |
| `/api/v2/comercial/ventas-dia` | **403** | Revisar RBAC/scope |
| `/api/comercial/dashboard/{operativo}` | 200 | `source_status: ERROR` (LIVE disabled, controlado) |
| `/api/finanzas/health` | **502** | `sql_subprocess_helper` — investigar |
| `/api/alerts` · `/api/sistema/tareas` · `/api/catalogo/consultas-custom` · `/api/nomina/ciclos` · `/api/rrhh/colaboradores` | 200 | OK |
| `/api/sistema/solicitudes` (GET) | 405 | Método; usar POST/acciones |
| `/api/inteligencia/health` | 200 | `connected EDARSAHUB` |
| `/api/explorador/tablas/{operativo}` | 200* | *pero log muestra import roto + consulta a operativo |

---

## 4) BLOQUEADORES PRIORITARIOS (para Fase 1, previa aprobación)

- **P0-1 (Tablero Ejecutivo, BLOQ)**: corregir nombre de vista en `modules/dashboard_ejecutivo/routes.py:32` → `vw_Comercial_KPIs_Diarios_v2_Runtime`.
- **P0-2 (Explorador BD, BLOQ)**: corregir import inexistente `_execute_sql_direct_with_error` y reemplazar consultas a operativos por metadata desde EDARSAHUB.
- **P0-3 (Finanzas, 502)**: diagnosticar `/api/finanzas/health` (`sql_subprocess_helper`); garantizar lectura desde `Finanzas_*_SyncLog` (EDARSAHUB) y NO sync live en runtime web.
- **P0-4 (NO-LIVE)**: erradicar intentos de conexión a `130mid/cienfuegos/estelar/softrestaurant12` en Reportes/Inventarios/Finanzas-sync/Tablajería.
- **P1-1 (NO-MONGO residual)**: blindar `comercial/cache_service.py`, `kpis_repository.py`, `historical_kpis_repository.py`.
- **P1-2 (Comercial)**: migrar `Comercial.js` y `TableroEjecutivo.js` 100% a endpoints v2 SQL-First; retirar legacy `/comercial/{server_id}`.
- **P2-1 (RBAC)**: aplicar scope por unidad de negocio en endpoints de datos sensibles.
- **P2-2 (Ruido)**: corregir `sla_service` (tarea None) e instalar/retirar dependencia `libodbc.so.2`.

---

## 5) PENDIENTE DE VERIFICACIÓN (siguiente sub-fase de auditoría)
- Ruta/endpoint exacto de **Configuración Operativa** y **Centro de Control** (mis pruebas dieron 404 por prefijo asumido).
- Flujos internos del **Portal Inteligencia Comercial** (subapp) y de **Automatizaciones** (tablas `automatizacion_inventarios_*` vacías).
- Validación RBAC con **cuenta de rol limitado** (Supervisor/Usuario) — pendiente para medir visibilidad de menús y scope de datos.

**Conclusión Fase 0**: 2 menús **BLOQUEADOS** (Tablero Ejecutivo, Explorador BD), 1 con fallo grave (Finanzas 502), violaciones **NO-LIVE** activas en logs y **Mongo residual** alcanzable en Comercial. El resto está OK o requiere ajustes menores. No se aplicaron correcciones.

---

## 6) VERIFICACIÓN COMPLEMENTARIA (2026-06-07, cuenta `admin@edarsa.com`)

### 6.1 RBAC — contexto del usuario de prueba
- `admin@edarsa.com` → rol del sistema = **ADMIN (Administrador)**, `UsuarioID=1`, nombre "Admin Test Editado". *(Nota: se reporta ADMIN, no SuperAdministrador.)*
- `/api/auth/access-context` devuelve `unidad_activa` + `unidades_permitidas` (130° MERIDA y otras) → **RBAC de Unidad de Negocio funcional a nivel de CONTEXTO**.
- `/api/sistema/menus/usuario` → **28 módulos** visibles para ADMIN.
- Limitación: validación de **rol limitado** (Supervisor/Usuario) no ejecutada por instrucción de no crear usuarios; se evaluó RBAC por código + contexto admin. La brecha real es de **scope de DATOS por unidad en endpoints** (no de contexto): endpoints como `dashboard-ejecutivo/resumen` y `rentabilidad` no filtran por unidad.

### 6.2 Rutas reales resueltas (antes 404 por prefijo asumido)
- **Centro de Control** → `core/centro_control/routes.py`, prefix `/api/centro-control`. Endpoints `/salud/resumen`, `/fuentes`, `/ping` → **200 OK**. ⚠️ Background `health_checker` con bug: `Error verificando SQL servers: 'NoneType' object is not subscriptable`.
- **Configuración Operativa** → `api/configuracion_operativa_unidades.py`, prefix real `/api/admin/unidades-negocio`. Endpoint `/todas/configuracion-operativa` → **500**. Causa: `[CONFIG_OPERATIVA] ... tuple indices must be integers or slices, not str` (bug cursor **tupla-vs-dict** de PyMSSQL; mismo patrón ya resuelto en `SQLBaseRepository`). **Reclasificado: MENOR → MAYOR/BLOQ.**

### 6.3 Ajustes a la matriz tras verificación
- **7g Configuración Operativa**: estado **MAYOR/BLOQ** (500 por cursor tupla-vs-dict). Recomendación: usar cursor `as_dict=True` / `_row_to_dict` en `configuracion_operativa_unidades.py`.
- **Centro de Control** (no estaba en los 15, pero relevante): OK en API; corregir `health_checker` NoneType.
- **Ruido confirmado**: `sla_service` (tarea None) sigue emitiendo errores en bucle → P2 limpieza.

### 6.4 Bloqueadores actualizados (P0)
1. Tablero Ejecutivo — vista corrupta (500).
2. Explorador BD — import roto (`_execute_sql_direct_with_error`).
3. Finanzas — `/health` 502.
4. **Configuración Operativa — 500 (cursor tupla-vs-dict).**
5. NO-LIVE — erradicar conexiones a operativos.

### 6.5 Hallazgos adicionales (validación con SUPERADMIN QA — 2026-06-07)
- 🔴 **Creación de usuarios ROTA (menú Personas/Usuarios)**: `POST /api/users` → 500. Causa: `modules/auth/service.py:556` → `verificar_permiso_rbac(current_user,'SISTEMA_USUARIOS_CREAR')` lanza `TypeError: 'NoneType' object is not subscriptable`. Bloquea alta de usuarios desde la UI. **Recomendación**: corregir `verificar_permiso_rbac` (manejo de None en el contexto/permisos).
- ⚠️ **RBAC / unidades para SUPERADMIN**: un SUPERADMIN sin asignación explícita → `unidades_permitidas=0`, `unidad_activa=None`. Las pantallas con filtro por Unidad de Negocio podrían quedar sin contexto/datos para un SUPERADMIN. (admin@edarsa.com SÍ tiene unidades asignadas.) **Recomendación**: decidir política — auto-otorgar todas las unidades a SUPERADMIN en `access-context`, o exigir asignación explícita.
- ⚠️ **Ruido de fondo (P2)**: `core.scheduler.jobs.crm_sync_job` → `Invalid column name 'OportunidadID'`; `health_checker` → `'NoneType' object is not subscriptable`; `sla_service` (tarea None) en bucle.
- **Cuenta de prueba creada**: `qa.superadmin@edarsa.com` / `QaSuper2026!` (SUPERADMIN, UsuarioID=22) — registrada en `test_credentials.md`.
