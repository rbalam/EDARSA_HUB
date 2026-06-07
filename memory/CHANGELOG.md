# EDARSA HUB - Changelog

## [2026-06-07] Bugfix server nombre + Fase 8B P2-2B (frontend Mis Tareas/Asignaciones)
- `modules/comercial/repository.py::_sql_row_to_server_dict`: agregado alias `'nombre'` (= `row['nombre']`) junto a `'name'` (consumidores que esperan `nombre`). Verificado: name/nombre poblados (130° MERIDA, CIENFUEGOS, LA ESTELAR, ManagmentPro). Nota: el "nombre None" reportado antes fue un falso positivo (la clave de salida es `name`).
- `frontend/src/pages/ConfigAsignaciones.jsx`: FIX bug real `getUserRole()` usaba `token` no declarado → `ReferenceError`. Ahora `const token = getToken()` (import `{ getToken }` de `lib/api`). + hardening `ensureArray`/`asString` en setters y Radix Selects (value string).
- `frontend/src/pages/MisTareas.js`: helpers `ensureArray`/`normalizeTareas`/`normalizePendientes`, null-safety en setters y derivados. Corregidos 3 lint bloqueantes preexistentes (comillas sin escapar `&quot;`; `set-state-in-effect` → efecto envuelto en `init()` async).
- Validado: `yarn build` BUILD_OK=1, lint 0 bloqueantes, consola sin `ReferenceError`. Captura autenticada bloqueada por PREVIEW_CACHE_RESET (limitación del preview). Scripts/back.: `/app/scripts/fase8b_*`, `.bak_*`.


## [2026-06-07] Bugfix — Dashboard Comercial "Servidor no encontrado en configuración"
- Causa raíz: `modules/comercial/repository.py::_get_server_by_id_sql` interpolaba `{id}` (función builtin `id` de Python → `'<built-in function id>'`) en el f-string del query en vez de `{server_id}`. La consulta a `Servidores_Conexiones` nunca encontraba el servidor → `get_server_by_id` retornaba None → el endpoint `/api/comercial/dashboard/{server_id}` respondía `source_status=ERROR, "Servidor no encontrado en configuración"`.
- Fix: usar `{server_id}` con escape de comillas (`safe_id = server_id.replace("'", "''")`) para evitar inyección SQL.
- Verificado: `GET /api/comercial/dashboard/{server_id}` → 200 `source_status=SUCCESS` en los 4 servidores (3 SoftRestaurant + 1 MPRO). `health/v1` → healthy. Backup `.bak_*`.


## [2026-06-07] Fase 8 — P2-2A Contención de ruido backend no bloqueante
- `core/health_checker.py`: `_check_mongodb` → `UNKNOWN` (residual deshabilitado, ya no `CRITICAL`); `_check_sql_servers` → `[]` (catálogo legacy dependía de Mongo); conteo no suma fallo por fuentes `UNKNOWN`. Resultado: `OVERALL=healthy, sources_failed=0`.
- `core/scheduler/jobs/crm_sync_job.py`: helper `_is_missing_schema_error` + `_skip_result`; `execute_crm_sla_check`/`execute_crm_actividades_vencidas` devuelven `SKIP` controlado ante esquema CRM incompleto (`Invalid column 'OportunidadID'`) en vez de spamear errores. Verificado: CRM_ACT=SKIP.
- `modules/fase2_operativo/services/sla_service.py`: guards `if not tarea or not isinstance(tarea,dict)` en `calcular_estado_sla`, loops y `notify_sla_warning/expired/escalated` (→ False). Sin crash con tarea None.
- Patches por `txt.replace()` de cadena exacta (fail-safe). Validado: 3/3 compile OK, backend RUNNING, `health/v1` (auth) → healthy. Script: `/app/scripts/fase8_p2_2a_contencion_ruido_backend.sh`.


## [2026-06-07] Fase 7 — P2-1 Neutralización residual Mongo en Comercial
- `modules/comercial/kpis_repository.py :: upsert_kpi_comercial`: guard temprano `if db is None -> return {"action":"SKIP","disabled":True,"reason":"MONGO_COMMERCIAL_DEPRECATED"}`. Elimina el crash `None[COLLECTION].find_one(...)` en cada sync (la función la importa `api/sync_receiver.py:147`, que solo lee `result["action"]`).
- Hallazgo: el script original apuntaba a 4 funciones inexistentes y omitía la única Mongo viva; se implementó la neutralización correcta. Las `get_*`/`cerrar_periodos_anteriores` no las importa ningún router (código muerto inerte).
- Verificado: smoke `upsert_kpi_comercial` → SKIP no-op sin crash; `health/v1` → healthy.
- Script: `/app/scripts/fase7_p2_1_neutralizar_mongo_comercial.sh` (versión corregida).


## [2026-06-07] Fase 6 — Endpoint semáforo `/api/health/v1` (SQL-First / NO-LIVE)
- Nuevo módulo `backend/modules/health_v1/routes.py` + registro en `server.py` (import tras finanzas.health; include tras `app.include_router(api_router)`).
- `GET /api/health/v1` agrega salud canónica de los 6 dominios estabilizados: sql_canonic, tablero_comercial (vistas v2_Runtime queryables), users_roles, config_operativa, explorador_bd (helper local), finanzas (tablas requeridas). NO consulta operativos externos.
- Resultado: `overall_status=healthy`, 200 en ~1.7s. Probe de vistas = queryability estructural (vista vacía ≠ rota).
- NOTA: bloqueado el registro del script del usuario (prepend de import en línea 1 → antes de `load_dotenv()` → habría roto el arranque). Registrado de forma segura.
- Scripts: `/app/scripts/fase6_crear_health_v1.sh` (versión corregida) y `/app/scripts/fase6_validar_health_v1.sh`.


## [2026-06-07] Fase 1 — Estabilización V1.0: 5 P0 cerrados (SQL-First / NO-MONGO / NO-LIVE)
Todos validados con cURL/pytest (sin testing_agent, por prohibición). Backups `.bak_*` por archivo.
- **P0-1 Vistas corruptas (Tablero/Comercial)**: normalizadas `vw_vw_..._Runtime_Runtime` → `vw_Comercial_KPIs_Diarios_v2_Runtime` y `..._Mensuales_v2_Runtime` en 10 archivos vivos. `GET /api/comercial/tablero-ejecutivo` y `/api/dashboard-ejecutivo/resumen` → 200 con datos EDARSAHUB_SQL.
- **P0-2 RBAC + CRUD Usuarios/Roles**: `core/rbac_helper.py` reescrito SQL-First **async** (`run_in_threadpool`, bypass por CodigoRol `SUPERADMIN`/`ADMIN`+NivelJerarquia, fail-closed). Añadidas 11 funciones **module-level** SQL-First en `modules/auth/repository.py` (get_db→None, get_users_by_empresas, get_all_roles, find_role_by_id/by_name, create/update/delete_role, count_users_with_role, create_default_roles, deactivate_user). `core/alcance_helper.py`: SuperAdmin reconoce CodigoRol `SUPERADMIN`. CRUD users/roles GET/POST/PUT/DELETE → 200. pytest `tests/test_rbac_helper.py` 5/5.
- **P0-3 Configuración Operativa (cursor tupla-vs-dict)**: helpers `_rows_dicts`/`_one_dict` en `api/configuracion_operativa_unidades.py` (3 sitios fetch, incl. `/todas/`). Endpoints config-operativa + probar-fecha-operacion → 200.
- **P0-4 Explorador BD**: repuesto `_execute_sql_direct_with_error` en `core/db.py` (async, `asyncio.to_thread(execute_sql_query)`). `/api/explorador/conexiones-explorables` (13) y `/api/explorador/tablas/{server_id}` → 200.
- **P0-5 Finanzas /health 502**: `include_server_details` default `True→False` en `modules/finanzas/health.py`. Health canónico solo EDARSAHUB (NO-LIVE) → 200 en 0.28s; sondeo externo ahora opt-in (`?include_server_details=true`).
- NOTA scripts del usuario: 3 de 5 traían defectos detectados antes de ejecutar (líneas no cubiertas en FASE1/FASE3; métodos de clase vs module-level en FASE2b; **SyntaxError** en FASE5). Se implementaron versiones corregidas. FASE4 estaba correcto.


## [2026-06-07] Fase 0 — Auditorías profundas A/B/C (SIN cambios de código de app)
- Doc actualizado: `/app/auditorias_p5/AUDITORIA_V1_PRODUCCION_MATRIZ.md` (secciones 6 y 7).
- **A (UI smoke, 12 menús)**: ningún logout ni crash; KPIs Tablero/Comercial vacíos (403+vista); Config.Operativa atascada (500); Mis Tareas 12 JS-err, Asignaciones 8 JS-err.
- **B (NO-LIVE)**: guard rail `LEGACY_LIVE_DISABLED` OK; intentos live en logs = jobs de sync (ETL); **vista corrupta `vw_vw...` en 88 referencias** (Comercial/Tablero KPIs).
- **C (RBAC)**: `core/rbac_helper.verificar_permiso_rbac` es Mongo y crashea → rompe CRUD usuarios/roles (NO-MONGO + 500); SUPERADMIN no bypassa scope de unidad en `comercial_v2` (403); enforcement disperso.
- Test users (autorizados): `qa.superadmin@edarsa.com`/`QaSuper2026!` (nuevo) y `admin@edarsa.com`/`pruebas123` (promovido a SUPERADMIN).


## [2026-06-07] Fase 0 — Auditoría v1.0 producción (SIN cambios de código)
- Entregable: `/app/auditorias_p5/AUDITORIA_V1_PRODUCCION_MATRIZ.md` (matriz por menú: front/back, endpoints, auth, RBAC, filtros, tablas canónicas, legacy/stub, live prohibido, mongo residual, estado, riesgo, recomendación).
- Bloqueadores hallados: **Tablero Ejecutivo 500** (vista corrupta `vw_vw_vw_vw_..._Runtime_Runtime...` → real `vw_Comercial_KPIs_Diarios_v2_Runtime`); **Explorador BD** import roto `_execute_sql_direct_with_error`; **Finanzas /health 502**; intentos **NO-LIVE** a operativos en logs; **Mongo residual** alcanzable en `comercial/cache_service|kpis_repository|historical_kpis_repository`.
- Sin correcciones aplicadas (a la espera de aprobación de Fase 1).


## [2026-06-07] Limpieza de menú: rutas rotas → "Pronto" + 2 rutas corregidas

- **2 ítems con ruta mal escrita corregidos** (apuntaban a rutas inexistentes pese a tener pantalla):
  - `Asignaciones`: `/asignaciones` → `/configuracion/asignaciones` (validado: abre "Asignaciones de Inventarios").
  - `Config. Operativa`: `/configuracion-operativa` → `/admin/configuracion-operativa`.
- **11 módulos sin pantalla marcados `comingSoon: true`** (Inventarios, Host to Host, Contabilidad, Comisiones, Inteligencia Artificial, Calidad/Auditoría, Proyectos, Marketing, Activos Fijos, Integraciones, Programación). `EnterpriseSidebarMenu` los renderiza **deshabilitados** (no clicables) con badge **"Pronto"** y tooltip "— Próximamente". `go()` ignora ítems `comingSoon`.
- **Validado (playwright)**: clic en ítem `comingSoon` (Contabilidad) NO navega ni expulsa; ítem corregido (Asignaciones) abre su pantalla. Lint limpio.


## [2026-06-07] FIX lote: Permisos 403, crash Select, logout navegación (Issue #1) y race recarga (Issue #2)

### 🐞 Guardar permisos de usuario → "Error al guardar permisos" (backend, 403/404)
- `PUT /api/users/{id}/permissions` devolvía **403** porque `ROLE_HIERARCHY` (modules/auth/service.py) solo reconocía `NombreRol` legacy ('SuperAdministrador'), pero el JWT usa `CodigoRol` canónico ('SUPERADMIN'/'ADMIN'). → Mapeados AMBOS (NombreRol + CodigoRol) a la escala legacy y `_get_role_level` ahora tolera mayúsculas.
- Tras el 403, había un **404 latente**: el servicio resolvía el usuario solo por `PublicUUID`, pero el frontend envía el `UsuarioID` numérico. → Resolución por `TRY_CONVERT(INT)` OR `PublicUUID`.
- **Validado (curl)**: 200 "Permisos actualizados" con id numérico + payload de sucursales/almacenes (inserts confirmados en SQL). Datos de prueba limpiados.

### 🐞 Crash runtime `<Select.Item /> value=""` (frontend)
- `BitacoraComponents.jsx` tenía 2 `SelectItem value=""` (Radix lo prohíbe). → Centinela `value="todos"` mapeado a `''` en `onValueChange` (preserva la lógica del filtro). Lint limpio.

### 🐞 Issue #1: logout al navegar Operaciones → Tablero Ejecutivo (frontend, sin 401/403)
- Causa raíz: el favorito "Dirección / Tablero Ejecutivo" (`enterpriseMenuConfig.js`) apuntaba a `/dashboard-ejecutivo`, ruta **inexistente** en App.js → catch-all `*` → `/login`. (~13 ítems de menú más apuntan a rutas no construidas con el mismo efecto.)
- Fix: (1) corregido path → `/tablero-ejecutivo`; (2) catch-all `*` ahora usa `CatchAllRedirect`: si hay sesión → `/tablero-ejecutivo`, si no → `/login` (evita logout espurio en CUALQUIER ruta desconocida).
- **Validado (playwright)**: clic en Tablero y ruta rota `/inventarios` ya NO expulsan.

### 🐞 Issue #2: race 403 en recarga dura del dashboard (frontend)
- `accessContextService.getAuthHeaders()` leía el token de la llave `'token'` (inexistente) en vez de la canónica `'edarsa_memory_token'` → `/auth/access-context` iba SIN Bearer → 403. → Usa `getToken()` canónico.
- `previewCacheUtils.shouldClearKey` borraba `edarsa_memory_token` (prefijo 'edarsa') en cada carga (BUILD_VERSION=Date.now()) → token perdido en recarga. → Lista `NEVER_CLEAR` protege token/usuario/marcador.
- **Validado (playwright)**: recarga dura + reload puro de Operaciones → 0×401/403, sin logout; access-context = 200.

### 🐞 Enlace de reset apuntaba a host bloqueado (backend)
- `forgot_password` usaba el `Origin`/`Referer` de la request; si el usuario entraba por `*.preview.emergentcf.cloud` (bloqueado, 403), el correo armaba ese enlace. → Siempre usa `FRONTEND_URL` canónico.

## [2026-06-07] FIX: Pantalla "Restablecer contraseña" saltaba al login

### 🐞 Bug (P0 reportado por usuario)
- **Síntoma**: El correo de recuperación llega y el enlace abre la pantalla de nueva contraseña, pero ésta "no se detiene": se muestra un instante y de inmediato salta a la ventana de iniciar sesión, sin poder capturar la nueva contraseña.
- **Causa raíz (frontend)**: `ResetPassword`/`ForgotPassword` se renderizan dentro de `<AuthProvider>`, que al montar llama a `GET /auth/me`. Sin sesión → 401. El interceptor de `lib/api.js` redirigía a `/login` para toda ruta que no fuera login/portales (no contemplaba el flujo de recuperación).
- **Fix**: En `lib/api.js` se añadió `isAuthFlowPage` (`/forgot-password`, `/reset-password`) a la lista de exclusión del redirect forzado en 401. El backend NO se tocó (el token, SMTP y reset SQL ya funcionaban).
- **Validado (screenshot)**: `/reset-password?token=...` permanece estable 4s, sin redirect; el input `reset-password-new` queda disponible para escribir la nueva contraseña.

## [2026-06-06] FASE AUTH-V2-ALIGN: Operaciones v2 (401/403/500) + forgot-password

### ✅ Capa 1 — Auth frontend (alineación canónica)
- **Problema**: `operativoApi.js` y 5 componentes hacían `fetch` crudo solo con `credentials:'include'` (cookie). El backend v2 solo lee el header Bearer → 401 (require_permission) / 403 (HTTPBearer de get_current_user).
- **Fix**: `getToken()` exportado desde `lib/api.js` (fuente única). Helper `authedFetch()` en `operativoApi.js` inyecta `Authorization: Bearer` + mantiene cookie. Migrados SLACard, ResponsabilidadCard, ResponsabilidadPendientesPanel, ResponsabilidadAccionesModal, WorkflowList a `authedFetch`.
- **Validado (browser)**: las 8 rutas v2 ahora envían `auth_header=True`; 401/403 → resueltos.

### ✅ Capa 2 — RBAC roto a nivel app
- **Bug A (isoformat)**: `core/rbac/repository_sql.py:445/693` hacía `fecha.isoformat()` sobre string (FreeTDS tds_version 7.0 devuelve DATETIME2 como string). → `hasattr(...,'isoformat')`.
- **Bug B (seed por request)**: `RBACService` usaba flag de instancia; `middleware.py` instancia por request → `seed_permisos+seed_roles` corrían en CADA petición (≈6s + timeouts intermitentes → 500). → flag a nivel de **clase** (`_seeded`), seeding una sola vez por proceso.
- **Validado (curl)**: `require_permission` ahora pasa para Ricardo (SUPERADMIN). v2/health=200; sla sin token=401, con token=500 (Capa 3).

### ✅ forgot-password (mismo origen datetime-string)
- `password_reset.py:138` `ventana_exp.replace(tzinfo=...)` sobre string → `TypeError`. Helper `_coerce_aware_dt()` (maneja str DATETIME2 de 7 decimales, datetime naive/aware, None).
- **Validado**: endpoint → 200, envía correo real vía SMTP `mail.edarsa.com.mx`. SMTP confirmado OK (login + sendmail).
- Test regresión: `backend/tests/test_password_reset_datetime.py` (6/6 passed).

### ⏸ Capa 3 — DIFERIDA por decisión del usuario (bloque separado y auditado)
- `dashboard/tareas/workflows/sla/responsabilidad` dependen de Mongo eliminado: `db_utils.py:30-31` hace `None[db_name]` → `'NoneType' subscriptable` → 500. NO se aplicó degradación por stub ni migración SQL (acuerdo explícito).

### Lint pre-existente (NO introducido en esta sesión)
- `react-hooks/set-state-in-effect` (SLACard, ResponsabilidadCard, ResponsabilidadPendientesPanel) y `react/no-unescaped-entities` (ResponsabilidadPendientesPanel:215) ya existían; mi diff solo cambió `fetch`→`authedFetch` e imports. No se refactorizó (fuera de alcance / riesgo).

## [2026-05-25] Sesión Actual

### ✅ CORTES-Z-RESILIENCIA-001: Mejora de Resiliencia Arquitectónica
- **Problema**: El health check anterior reportaba timeout como "normal", lo cual fue rechazado
- **Diagnóstico**: Confirmado que Cortes Z ya era SQL-FIRST (lee de `Finanzas_CortesCaja`)
- **Causa real**: Intermitencias del servidor EDARSAHUB SQL, no arquitectura
- **Mejora**: Endpoint ya no lanza error 500, retorna estado controlado `EDARSAHUB_UNREACHABLE`
- **Archivos**: `repository_cortes_caja_edarsahub.py`, `tesoreria.py`

## [2026-05-25] Sesión Anterior

### ✅ FINANZAS-TESORERIA-SQL-001: Cortes Z migrados a SQL
- Creado `repository_cortes_caja_edarsahub.py`
- Endpoint lee de `Finanzas_CortesCaja`
- 4,083 cortes históricos disponibles

### ✅ FINANZAS-TESORERIA-MONGO-002: Cuadres Z migrados a SQL
- Modificado `tesoreria.py` para usar repositorio SQL
- Agregados métodos `listar_cuadres_z_por_server_id()`, `obtener_resumen_por_server_id()`

### ✅ Migración credenciales hardcodeadas
- Movidas credenciales de `server.py` a `.env`
- CORS origin para producción agregado

### ✅ BUG-COMPETIDORES-001 resuelto
- Corregido mapeo de campos en CompetidorModal
- Agregados campos de redes sociales

## Problemas conocidos de infraestructura
- **EDARSAHUB SQL (54.39.104.176)**: Intermitencias de conectividad ocasionales
- **SoftRestaurant (189.162.155.142)**: Connection refused intermitente
