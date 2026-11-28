# EDARSAHUB BOS — Gate 5D Communications

Fecha: 2026-09-09
Rama: `Edarsahub_Desarrollo`
Producción: **NO TOCADA**

## Estado

Gate 5D deja integrada y probada la capa de código para Communications SQL-first y la fachada administrativa provider-neutral. La activación física de la cola y RBAC en Development queda bloqueada exclusivamente porque GitHub Actions abortó dos veces antes de asignar runner (`runner_id=0`, `steps=[]`), por lo que la migración SQL no llegó a ejecutarse.

No se declara Gate 5D al 100% mientras ese DDL/DML idempotente no sea aplicado y post-auditado.

## Preflight SQL certificado

Job `servers-integrations-gate5d-communications-preflight-r2-readonly-20260909`:

- `CERTIFIED_READ_ONLY`
- `PASS`
- `100%`
- identidad `EDARSAHUB / HRLectura`
- `Sistema_NotificacionesConfig`: existe, 6 filas
- `Operativo_Notificaciones_Log`: existe, 0 filas
- `Operativo_Notificaciones_Queue`: ausente
- conexiones Communications en `Servidores_Conexiones`: 0
- permisos `NOTIFICACIONES_*`: 0
- Producción: false

## Runtime SQL-first integrado

Job `servers-integrations-gate5d-communications-runtime-r2-20260909`:

- `INTEGRATED`
- `TESTS=PASS`
- `QUALITY_GATE=PASS`
- `BLOCKERS=[]`
- Production false

### Reutiliza

- `dbo.Sistema_NotificacionesConfig`
- `dbo.Operativo_Notificaciones_Log`
- `NotificationDispatcher`
- `TemplateService`
- providers existentes
- RBAC middleware existente

### Nuevo adapter SQL-first

`backend/core/communications/notifications/repository_sql.py`

Provee:

- config CRUD
- provider config CRUD/list
- template CRUD/list
- queue enqueue/lock/retry/status
- logs/auditoría

`repository.py` conserva compatibilidad de imports y delega el runtime al adapter SQL-first.

No se agregó dependencia Mongo, no se almacenan secretos de provider y no se crearon estructuras provider-specific.

## Fachada administrativa provider-neutral

Job `servers-integrations-gate5d-generic-admin-api-r4-20260909`:

- candidate/development SHA `70c512bc6098bc30048accd2ddab3239ce740136`
- `INTEGRATED`
- `TESTS=PASS`
- `QUALITY_GATE=PASS`
- `BLOCKERS=[]`
- Production false

Rutas bajo `integrations-center`:

- `GET /communications/configs`
- `POST /communications/configs`
- `PUT /communications/configs/{config_id}`
- `DELETE /communications/configs/{config_id}`
- `GET /communications/templates`
- `POST /communications/templates`
- `PUT /communications/templates/{template_id}`
- `DELETE /communications/templates/{template_id}`
- `GET /communications/providers`
- `POST /communications/providers`
- `PUT /communications/providers/{provider_id}`
- `GET /communications/queue`
- `GET /communications/logs`

No existen rutas nuevas Twilio/WhatsApp específicas. Las rutas legacy permanecen por compatibilidad.

El test Gate 5B fue evolucionado únicamente para exigir READ_ONLY en las cinco rutas base de Gate 5B; no bloquea el CRUD explícito de Gate 5D.

## Migración preparada

Archivo:

`backend/database/migrations/20260909_002_communications_queue_rbac.sql`

Es transaccional e idempotente y crea únicamente el objeto probado como ausente:

`dbo.Operativo_Notificaciones_Queue`

También registra los permisos ya requeridos por las rutas existentes:

- `NOTIFICACIONES_VER`
- `NOTIFICACIONES_CONFIGURAR`
- `NOTIFICACIONES_ENVIAR`

Asignación inicial conservadora: sólo `SUPERADMIN`. La ampliación por rol/perfil corresponde a Gate 5F.

Rollback:

`backend/database/migrations/20260909_002_communications_queue_rbac_rollback.sql`

## Intentos de migración Development

Workflow:

`.github/workflows/communications-gate5d-development-migration.yml`

Run 1: `34417698718`

- `conclusion=failure`
- `runner_id=0`
- `steps=[]`

Run 2: `34418250607`

- `conclusion=failure`
- `runner_id=0`
- `steps=[]`

Conclusión: ambos fallaron antes de checkout y antes de SQL. No hubo migración, rollback ni mutación de base.

## Post-audit SQL

Job `servers-integrations-gate5d-postaudit-r2-readonly-20260909`:

- `CERTIFIED_READ_ONLY`
- `PASS`
- `100%`
- config rows: 6
- log rows: 0
- queue present: 0
- queue columns: 0
- queue indexes: 0
- permisos `NOTIFICACIONES_*`: 0
- links SUPERADMIN: 0
- communication connections: 0
- Toast tables: 0
- Production false

Esto confirma que los fallos de Actions no dejaron cambios parciales.

## Bloqueador único

`GATE5D_BLOCKER=DEVELOPMENT_SQL_MIGRATION_NOT_EXECUTED`

Causa externa al código 5D:

`GITHUB_ACTIONS_RUNNER_NOT_ASSIGNED`

No se debe simular la cola, hacer backdoor DDL desde tests, crear otra tabla ni desactivar fail-closed del scheduler para ocultar el bloqueo.

## Estado de cierre

- `GATE_5D_CODE=100%`
- `GATE_5D_GENERIC_ADMIN_API=100%`
- `GATE_5D_TESTS=PASS`
- `GATE_5D_POST_AUDIT=CERTIFIED_READ_ONLY`
- `GATE_5D_SQL_ACTIVATION=0%`
- `GATE_5D_FUNCTIONAL_OVERALL=85%`
- `PRODUCTION_TOUCHED=NO`

Gate 5D podrá declararse `100% CERTIFIED` cuando la migración Development se ejecute por un runner/canal SQL operativo y el postcheck confirme queue=20 columnas, 2 índices, 0 filas iniciales, 3 permisos y 3 links SUPERADMIN, sin alterar las 6 configuraciones ni crear objetos provider-specific.
