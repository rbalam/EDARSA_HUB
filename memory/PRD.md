# EDARSA HUB - CRM COMERCIAL ENTERPRISE
## Product Requirements Document

### Original Problem Statement
Construir el CRM COMERCIAL ENTERPRISE y módulos satélite integrados al ecosistema EDARSA HUB.

### Core Requirements
- **ESTRICTA PROHIBICIÓN**: Uso del subagente `testing_agent_v3_fork` totalmente prohibido
- **MÁXIMA ARQUITECTÓNICA (NO-LIVE)**: EDARSAHUB SQL es la ÚNICA fuente de verdad productiva
- **MÁXIMA DE ORO**: NO DUPLICAR tablas, conexiones, filtros, flujos, usuarios, ni unidades de negocio

### User's Preferred Language
Spanish (Español)

---

## Architecture

### SQL-FIRST Architecture
- `core/sql_first/connection_factory.py` - Hub central para todas las conexiones SQL
- `core/sql_first/db.py` - Funciones base de conexión EDARSAHUB
- `core/db.py` - Wrapper de compatibilidad legacy (sin conexiones directas)
- `core/rbac_sql/service.py` - Servicio RBAC usando tablas canónicas

### Canonical SQL Tables
| Tabla | Propósito |
|-------|-----------|
| `Usuario_Catalogo` | Fuente única de usuarios (reemplaza Sys_Usuarios) |
| `Usuario_Roles` | Catálogo de roles |
| `Usuario_RolesAsignacion` | Asignación usuario-rol |
| `Usuario_EmpresasAsignacion` | Asignación usuario-empresa |
| `Usuario_SucursalesAsignacion` | Asignación usuario-sucursal |
| `Usuario_ServidoresAsignacion` | Asignación usuario-servidor |
| `Usuario_Modulos` | Catálogo de módulos para permisos |
| `Usuario_Acciones` | Catálogo de acciones RBAC |
| `Usuario_PermisosRolModulo` | Permisos rol-módulo-acción |
| `Sistema_Modulos` | Módulos del sistema (para menú) |
| `Sistema_ModulosMenus` | Menús por módulo |
| `Sistema_DeudaTecnica_TablasDuplicadas` | Registro de tablas obsoletas |

### Technical Debt (Tracked)
- `RBAC_Roles` - 6 rows (datos de transición)
- `RBAC_Permisos` - 9 rows (datos de transición)

---

## Implementation Status

### Phase P4 - SQL-FIRST Migration ✅ COMPLETE
- [x] P4-02: Centralización conexiones SQL
- [x] P4-03: Ajuste schema canónico
- [x] P4-04/05/06/07: Config segura y RBAC SQL
- [x] P4-09/09B: Aplicación Máxima de Oro, roles canónicos
- [x] P4-10/11/12: Validación contexto e integridad
- [x] P4-13: Backup colecciones Mongo candidatas
- [x] P4-14: Corrección huérfanos/duplicados (0 encontrados)
- [x] P4-15: Validación Mongo vs SQL (9 candidatas, 7 pendientes)
- [x] P4-16: Eliminación tablas RBAC_* vacías (6 eliminadas)
- [x] P4-17/17B: Dictamen Final APROBADO, core/db.py refactorizado

### P0-D - Una Sola Verdad Comercial ✅ COMPLETE (2026-06-XX)
Menú Comercial (`/api/comercial/tablero-ejecutivo`) devolvía $0. Causa raíz: `service.py`
filtraba la vista `vw_Comercial_KPIs_Diarios_v2_Runtime` por `unidad_negocio_pk` (que en la
vista es un GUID, NO el código) y forzaba `sucursal_id='DEFAULT'` (rompía 130QRO=0021 y
ORIGEN=0023). Fix quirúrgico en `_get_kpis_periodo_edarsahub` y el "portero" `query_ultimo_dia`
de `_obtener_kpis_tablero_desde_edarsahub`: filtro por `unidad_negocio_id` (texto canónico),
sin forzar `sucursal_id`, KPI = `ventas_sin_propina`. Los 3 módulos comerciales ahora cuadran
en **$1,573,660.81** (Junio 2026). Verificado vía cURL + SQL directo. Regresión:
`backend/tests/test_p0d_menu_comercial_filtro_canonico.py` (4 tests, estáticos). Script del
usuario AUDITADO y RECHAZADO (regex frágil que dejaba `sucursal_id` a medias, `yarn build`
innecesario, validación a endpoint inexistente `/api/inteligencia-comercial/resumen` sin JWT);
intención aplicada manualmente.

### Phase V1.0 - Estabilización Producción ✅ COMPLETE (2026-06-07)
Los 5 bloqueadores P0 del Dictamen cerrados y verificados (cURL/pytest, sin testing_agent):
- [x] P0-1: Vistas corruptas `vw_vw...Runtime` normalizadas (Tablero Ejecutivo + Comercial) → 200
- [x] P0-2: `rbac_helper.py` SQL-First async + 11 funciones module-level en `repository.py` + alcance SuperAdmin por CodigoRol → CRUD Usuarios/Roles 200
- [x] P0-3: Configuración Operativa cursor tupla-vs-dict (`_rows_dicts`/`_one_dict`) → 200
- [x] P0-4: Explorador BD `_execute_sql_direct_with_error` repuesto en `core/db.py` → 200
- [x] P0-5: Finanzas `/health` 502 → canónico NO-LIVE (externos opt-in) → 200/0.28s
- Detalle completo en CHANGELOG.md [2026-06-07] Fase 1.

### Phase P5 - MongoDB Sunset ✅ IN PROGRESS
- [x] P5-01: Backup controlado y eliminación de 9 colecciones Mongo
- [x] P5-02: Consolidación RBAC_Roles en Usuario_Roles
- [x] P5-05: Fix /auth/me token parsing
- [x] P5-06: Migración completa de usuarios Mongo a Usuario_Catalogo
- [x] P5-07: Cierre migración Auth SQL (AuthRepository creado, MongoDB fallback eliminado)
- [x] P5-10B: Menú 100% SQL canónico sin hardcodes (2026-06-06)
  - MenuService lee de Sistema_Modulos + Sistema_ModulosMenus
  - SUPERADMIN detectado por CodigoRol o NivelJerarquia >= 100
  - Frontend delegado al backend SQL
  - password_hash eliminado de respuestas API
- [x] P5-1 (2026-06-07): Sunset mínimo `comercial/historical_kpis_repository.py` — 3 funciones Mongo rotas neutralizadas a stubs + import huérfano `secret_manager` removido. Módulo era código muerto inerte (sin importadores). health/v1 → healthy.
- [ ] Eliminar 28 colecciones Mongo restantes (pendiente script usuario)
  - [x] (2026-06-07) RESPALDO COMPLETO NO destructivo realizado vía `mongodump` de las 5 bases locales (edarsa_hub=28, test_database=61, cab003=10, edarsahub=6, stock_tracker=2 → 107 colecciones, 3066 docs, 2.4MB). Ruta: `/app/backups/mongo_sunset_20260607_181350/`. Reporte: `REPORTE_RESPALDO_MONGO.md` + `MANIFEST_SHA256.json` (SHA256 por archivo + global). NADA borrado/desinstalado: pendiente decisión de borrado quirúrgico del usuario tras revisar el reporte.
  - [x] (2026-06-07) VALIDACIÓN POR MUESTREO DE LLAVES (Fase 6-ter, SOLO LECTURA): 27 colecciones CUBIERTA_PARCIALMENTE validadas doc-por-doc contra su tabla SQL (COUNT parametrizado). Veredicto duro: **6 CUBIERTA_CONFIRMADA** (toda la muestra hallada unívocamente → candidatas a borrado CON respaldo): `users`→Usuario_Catalogo, `inventarios_procesados_auto`→Inventarios_ProcesadosAuto (vía col MongoId), `portal_suppliers`→Portal_Proveedores (vía MongoId), `consultas_custom`→Sistema_ConsultasCustom, `sec_modulos_sistema`→Sistema_Modulos, `server_status`→Sistema_ServidoresEstado. **18 NO_CUBIERTA + 3 SIN_LLAVE** (NO borrar): destacan rbac_roles/sec_roles/roles/rbac_usuarios_roles (nombres no coinciden en Sistema_RBAC_Roles) y rbac_permisos/sec_permisos_catalogo (AMBIGUO en RBAC_Permisos). Reportes en `/app/docs/reports/mongo_validacion_muestra_llaves_20260607_191439/` (MD/JSON + CSV detalle por doc + CSV resumen). NADA borrado/modificado.
### P0 - Bitácora RBAC → SQL-First + Eliminación de Alcance legacy ✅ COMPLETE (2026-06-07)
Completadas las 2 features hermanas que seguían en Mongo stub (tras auditar y RECHAZAR el
script del usuario por: colisión de rutas con endpoints legacy no eliminados, `UsuarioID
UNIQUEIDENTIFIER` incompatible con el INT real, y crear un 3er sistema de alcance paralelo):
- **Bitácora RBAC → SQL**: nueva tabla `dbo.Usuario_RBAC_Bitacora` (UsuarioID INT,
  `migrations/rbac_bitacora_sql_20260607.py`); en `rbac_pilot_service.py` se añadieron
  `registrar_bitacora()` (no-fatal), `get_bitacora()` (filtros fecha/email/resultado/tipo +
  paginación OFFSET/FETCH) y `get_bitacora_evento()`. Se **re-instrumentaron** los 5 endpoints
  de perfiles/roles/permisos para escribir auditoría. Los endpoints legacy `GET /admin/bitacora`
  y `/admin/bitacora/{id}` (Mongo) fueron **reemplazados** por versiones SQL (gate `es_superadmin`).
  Contrato de respuesta idéntico al que espera el frontend (`useBitacoraRBACData.js`:
  skip/limit/fecha_inicio/fecha_fin/email/resultado/tipo → {total,pagina,paginas_total,eventos[]}).
- **Alcance legacy → ELIMINADO**: borrados `GET/POST /admin/alcance/*` (Mongo muerto, 0
  consumidores) porque el alcance canónico ya vive en `/api/config-asignaciones`
  (`Usuario_EmpresasAsignacion`/`Usuario_SucursalesAsignacion`). NO se creó tabla nueva.
- Eliminados 2 helpers de auditoría Mongo huérfanos (`registrar_auditoria_*_fase*`).
- NOTA: durante el borrado de helpers se eliminaron por error los endpoints
  `/admin/permisos/asignar` y `/admin/roles/asignar` (estaban intercalados); fueron
  **restaurados** en su versión SQL-First.
Verificado: cURL E2E (asignar perfil/rol/permiso generan bitácora; filtros OK; detalle OK;
`/admin/alcance/*` → 404; `/admin-sql/users` 26 usuarios). 19/19 tests, lint limpio,
regresión role-migration OK (pool-stats 200, config-asignaciones 200).

### P0 - Consolidación RBAC Canónica (helper SQL central) ✅ COMPLETE (2026-06-07)
A petición del usuario (tras auditar y RECHAZAR su script por crear un 3er helper con
niveles hardcodeados de solo 5 roles + reemplazo masivo ciego), se implementó la versión
segura reusando la infraestructura existente:
- **(A) Helpers canónicos en `core/rbac_helper_sql.py`** (sin 3er archivo, sin hardcodear
  niveles): `get_role_code()` (resuelve el código canónico desde los 23 roles de
  `Usuario_Roles` vía SQL + compatibilidad con role_code/_sql_rol_codigo/CodigoRol/role/
  NombreRol/rol), `es_superadmin()`, `es_admin()` (={SUPERADMIN,ADMIN}),
  `es_supervisor_o_superior()` (={SUPERADMIN,ADMIN,SUPERVISOR}). Conjuntos explícitos que
  preservan la semántica legacy y corrigen la **negación falsa al SUPERADMIN**.
- **(B) Migración quirúrgica** (no `text.replace` ciego) de porteros en 4 archivos:
  `server.py` (24 gates), `routes_competidores_enterprise.py` (5, con rename de var local
  `es_superadmin`→`es_super` para evitar colisión), `config_asignaciones_routes.py` (4),
  `catalogos/routes.py` (9). **Bug corregido**: endpoints con `!= 'Administrador'` /
  `not in ['Administrador','Supervisor']` que NEGABAN al SUPERADMIN (ej. `/api/sistema/pool-stats`
  daba 403, ahora 200). Se DEJÓ INTACTO `auth/routes.py` (ya correcto vía `tiene_acceso_global`,
  listas heterogéneas con Director/Gerente/Auditor → riesgo sin beneficio).
- **(C) Auditoría** `migrations/auditar_hardcodes_rbac.py` → CSV con hardcodes restantes
  clasificados por riesgo en `/app/docs/reports/P0_RBAC_HARDCODES_RESTANTES_*.csv`.
- Bonus: corregidos 2 bugs pre-existentes en `catalogos/routes.py` (`Descripcion`/`Codigo`
  indefinidos → NameError) y 2 corrupciones de cola de archivo.
Verificado: cURL per-rol (SUPERADMIN pasa gates antes denegados; comercial intacto
$1,573,660.81), 15/15 tests (`test_rbac_helpers_canonicos.py` + `test_rbac_helper.py` +
`test_rol_canonicidad_normalize_user.py`), lint limpio.
BACKLOG (en CSV): porteros restantes en `rh/solicitudes_catalogo.py`, `costos_margenes/*`,
`core/security.py`, `core/rbac/middleware.py`, frontend `Layout.js`.

### P0 - RBAC Piloto (Perfiles/Roles/Permisos) → SQL-First ✅ COMPLETE (2026-06-07)
Bug reportado por el usuario: "no encuentra los perfiles RBAC" → toast "Perfil
PERFIL_GESTOR_SISTEMA no encontrado o inactivo" al asignar un perfil en la pantalla
Usuarios. Causa raíz: el panel "Seguridad RBAC" (perfiles `sec_perfiles`, roles
`sec_roles`, permisos `sec_permisos`) corría 100% sobre MongoDB (`db = get_stub_database()`
en server.py:117), deshabilitado en la arquitectura SQL-First.
Migración SQL-First (opción (b) elegida por el usuario):
- Nuevas tablas SQL: `dbo.Sistema_RBAC_PerfilCatalogo` (catálogo perfil→roles CSV, 5 perfiles
  FASE 13 sembrados desde el respaldo mongodump `sec_perfiles.bson`) y
  `dbo.Usuario_RBAC_Asignacion` (asignación por usuario, Tipo: PERFIL|ROL|PERMISO).
- Nuevo servicio `modules/admin_sql/rbac_pilot_service.py` (get_perfiles_catalogo,
  asignar_perfil, retirar_perfil, toggle_asignacion, get_rbac_map).
- 5 endpoints reescritos a SQL en server.py (sin Mongo): `GET /admin/perfiles`,
  `POST /admin/perfiles/asignar|retirar`, `POST /admin/roles/asignar`,
  `POST /admin/permisos/asignar`. `/admin-sql/users` ahora devuelve `sec_perfil`,
  `sec_roles`, `sec_permisos` desde SQL.
- Semántica preservada del modelo legacy: asignar perfil = setea sec_perfil + sobrescribe
  sec_roles; retirar perfil = limpia sec_perfil+sec_roles (conserva permisos directos).
Verificado: cURL E2E (listar/asignar/estado/toggle rol/toggle permiso/retirar) sobre Carlos
Ruz (carlosruz@edarsa.com.mx) + screenshot (panel carga sin el error). Migración idempotente
en `migrations/rbac_pilot_sql_20260607.py`.
PENDIENTE (features separadas aún en Mongo stub, NO reportadas): visor "Bitácora RBAC"
(`/admin/bitacora`) y asignación de "Alcance" empresas/unidades/sucursales (`/admin/alcance/*`).

- [ ] Remover pymongo de dependencias (requirements)

### P0 - Canonicidad de Rol (SUPERADMIN ↔ SuperAdministrador) ✅ COMPLETE (2026-06-07)
Bug urgente reportado por el usuario: `role` en current_user/JWT llevaba el **CodigoRol**
canónico (`SUPERADMIN`), pero ~185 guards de backend y ~47 del frontend comparan por
igualdad contra el **NombreRol** legacy (`SuperAdministrador`). Resultado: el
SuperAdministrador era rechazado en decenas de endpoints (p.ej. `/api/config-asignaciones`
devolvía 403). Causa raíz adicional ("dos claves distintas"): 5 sitios en
`routes_competidores_enterprise.py` leían la clave equivocada `current_user.get('rol')`
(no existe; la clave es `'role'`).
Fix de punto único en `modules/auth/repository.py::_normalize_user`:
- `role` = `NombreRol` legacy (lo que esperan guards + frontend).
- Se conserva el CodigoRol canónico en `role_code` y `_sql_rol_codigo` (para RBAC canónico-aware).
- Ajuste puntual `inteligencia_comercial_routes.py:113` (set acepta `SUPERADMINISTRADOR`).
- 5x `current_user.get('rol')` → `current_user.get('role')` en competidores enterprise.
Verificado vía cURL: login Ricardo OK, `/api/config-asignaciones` 200 (antes 403),
`/api/inteligencia/dashboard` 200, total comercial canónico intacto **$1,573,660.81**.
Regresión: `tests/test_rol_canonicidad_normalize_user.py` (4 tests) + `tests/test_rbac_helper.py` (5).
Equivalencia respetada: SUPERADMIN↔SuperAdministrador, ADMIN↔Administrador,
SUPERVISOR↔Supervisor, USUARIO↔Usuario, VISOR↔Visor.
También: password de `ricardo@edarsa.com.mx` restablecido a `Ricardo2835!` (bcrypt) y verificado.

---

## Testing Protocol
- **Permitido**: bash, cURL, python -c, screenshots
- **PROHIBIDO**: testing_agent_v3_fork

---

## Key Files Reference
- `/app/backend/core/sql_first/db.py`
- `/app/backend/core/sql_first/connection_factory.py`
- `/app/backend/core/db.py` (wrapper legacy)
- `/app/backend/core/rbac_sql/service.py`
- `/app/backend/core/config/edarsahub_config.py`
- `/app/backend/modules/auth/repository.py` (AuthRepository SQL-only)
- `/app/backend/modules/sistema/menu_service.py` (MenuService SQL canónico)
- `/app/backend/modules/sistema/menu_routes.py` (Rutas de menú)
- `/app/backend/auditorias_p4/` (logs y backups P4)
- `/app/backend/auditorias_p5/` (logs y backups P5)

---

## Environment Variables
```
EDARSAHUB_SQL_HOST=54.39.104.176
EDARSAHUB_SQL_PORT=1433
EDARSAHUB_SQL_DATABASE=EDARSAHUB
EDARSAHUB_SQL_USER=HRLectura
EDARSAHUB_SQL_PASSWORD=******
```

---

*Last Updated: 2026-06-06*
*Phase: P4 Complete, P5-10B Complete (Menu SQL + Enterprise Menu)*
*Pending: Final MongoDB Sunset*

## Enterprise Menu System
El sistema ahora tiene un menú Enterprise organizado por grupos:
- **Operación**: Ventas, Compras, Inventarios, Producción
- **Finanzas**: Flujo, Bancos, Contabilidad, Comisiones
- **Personas**: RH, CRM, Cava de Socios
- **Inteligencia**: Dirección, BI, IA, Auditoría
- **Gestión**: Proyectos, Marketing
- **Corporativo**: Activos, Catálogos
- **Integraciones**: Conectores, APIs
- **Administración/Sistema**: Control, Infraestructura, Seguridad
- **Satélites**: Comandero, Super Caja, PIC

Archivos clave:
- `/app/frontend/src/config/enterpriseMenuConfig.js` - Configuración canónica
- `/app/frontend/src/components/navigation/EnterpriseSidebarMenu.jsx` - Componente visual
- Flag `USE_ENTERPRISE_MENU` en Layout.js para activar/desactivar
