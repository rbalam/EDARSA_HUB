# EDARSA — Scheduler / persistencia / referencias legacy

Regla obligatoria para cualquier agente que toque Scheduler.

## Antes de modificar

1. Verificar rama, HEAD y worktree.
2. Auditar job runtime real.
3. Auditar lock.
4. Identificar fuente canónica SQL.
5. No asumir que un catálogo legacy representa runtime vigente.

## Pausa administrativa

- Runtime: APScheduler.
- Persistencia: `dbo.Sys_Scheduler_RuntimeState`.
- Escritura: `dbo.sp_Scheduler_SetAdministrativePause`.
- Repositorio: `core.scheduler.persistent_state_repository`.
- Startup restaura pausas antes de iniciar scheduler.
- Fallo de lectura persistente: fail-closed.
- Fallo de persistencia pause/resume: revertir runtime cuando sea posible.

Prohibido resolver pausa persistente mediante:

- `Sys_Scheduler_Jobs`;
- MongoDB;
- hardcodes;
- variables solo en memoria;
- fuentes paralelas.

## Mongo

La presencia del texto `mongo` NO demuestra una dependencia.

Clasificar primero:

1. import/cliente runtime real;
2. stub de compatibilidad;
3. nombre histórico;
4. comentario/docstring;
5. test contractual;
6. documentación.

Solo (1) constituye por sí mismo evidencia de dependencia runtime.

`core.mongo_stub` / `get_stub_database` deben tratarse como referencias de
compatibilidad, no como prueba automática de conexión Mongo. Reabrir la
auditoría solo si su implementación cambia, aparece cliente externo real o
existe evidencia de I/O Mongo productivo.

## Tests

No usar asserts amplios como:

- `"mongo" not in text.lower()`
- `"Sys_Scheduler_Jobs" not in text`

si comentarios o documentación legítima pueden contener esos términos.

Validar imports, AST, llamadas, SQL y comportamiento.

## Git

- No `git add .`.
- No reset/stash global.
- Preservar cambios staged ajenos.
- Worktrees de agentes deben estar registrados.
- Agentes requieren claim.
- Push a Desarrollo solo desde integrator.
- No `--no-verify`.
- Outputs reproducibles en `/tmp/edarsahub-agents/<agent>/outputs/`.

## Regresión mínima

- tests Scheduler;
- py_compile;
- diff check;
- prueba restart cuando cambie persistencia/startup;
- estado SQL final;
- lock final;
- remote HEAD exacto antes de push.
