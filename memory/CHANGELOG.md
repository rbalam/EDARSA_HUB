# EDARSA HUB - Changelog

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
