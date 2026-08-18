# EDARSAHUB — Arquitectura canónica de pausa administrativa persistente del Scheduler

Estado: vigente
Versión introducida: V1.0
Commit de referencia: `a7f063c68a0f62bf1ad83f104d5e79464b59ae7d`

## Objetivo

La acción administrativa de pausar o reanudar un job debe sobrevivir reinicios
del backend sin convertir el catálogo de jobs, el estado de ejecución o tablas
legacy en una segunda fuente de verdad.

## Fuente canónica

La persistencia administrativa vive exclusivamente en:

- `dbo.Sys_Scheduler_RuntimeState`

Responsabilidad de esta tabla:

- JobID;
- pausa administrativa;
- timestamp UTC de actualización.

No contiene ni debe contener:

- cron;
- intervalos;
- definición funcional del job;
- estado de ejecución;
- último resultado;
- catálogo operativo;
- configuración de negocio.

## Interfaz de escritura

El backend no realiza INSERT/UPDATE directo sobre la tabla.

La escritura se realiza mediante:

- `dbo.sp_Scheduler_SetAdministrativePause`

El repositorio Python autorizado es:

- `backend/core/scheduler/persistent_state_repository.py`

Esto mantiene una interfaz estrecha y permite reducir privilegios SQL sin
cambiar el contrato del Scheduler.

## Startup

Secuencia obligatoria:

1. registrar jobs runtime;
2. leer `get_paused_job_ids()`;
3. identificar IDs registrados;
4. advertir sobre estados persistentes sin job runtime;
5. restaurar pausa de jobs conocidos;
6. iniciar APScheduler.

La lectura del estado persistente es fail-closed: un error SQL no debe hacer que
el Scheduler arranque ignorando una decisión administrativa persistida.

## Pause / resume

`pause_job(job_id)`:

1. pausa runtime;
2. persiste `True`;
3. si SQL falla, intenta revertir runtime con resume;
4. devuelve fallo si no puede cerrar el contrato.

`resume_job(job_id)`:

1. reanuda runtime;
2. persiste `False`;
3. si SQL falla, intenta revertir runtime con pause;
4. devuelve fallo si no puede cerrar el contrato.

Runtime y persistencia no son dos verdades independientes.

## Tabla legacy Sys_Scheduler_Jobs

`Sys_Scheduler_Jobs` NO es la fuente de pausa administrativa del Scheduler
actual.

No debe:

- recibir columnas de pausa para resolver este problema;
- ser mutada por pause/resume;
- convertirse en fuente runtime solo porque contiene IDs históricos;
- forzar convergencia de jobs legacy que ya no tienen implementación runtime.

La existencia de filas legacy no demuestra que exista un job ejecutable actual.

## Validación requerida

Toda modificación futura debe validar como mínimo:

- pausa runtime real;
- persistencia SQL;
- restart real;
- `next_run = None` después del restart cuando está pausado;
- resume real;
- persistencia `False`;
- ausencia de ejecución activa durante la prueba;
- regresión de Scheduler;
- compile;
- `git diff --check`.

## Seguridad y RBAC

Los endpoints siguen sometidos a RBAC.

La persistencia SQL no sustituye autorización.

No se debe:

- fabricar JWT;
- saltar RBAC;
- usar credenciales alternativas;
- pedir password interactivo para auditorías server-side que puedan resolverse
  desde contexto canónico SQL/servidor.

## Invariantes

1. SQL EDARSAHUB es fuente persistente.
2. APScheduler es estado runtime.
3. Un restart no elimina una pausa administrativa.
4. Catálogos legacy no son fuente automática de runtime.
5. No MongoDB productivo en este flujo.
6. No DML SQL directo desde el repositorio.
7. No hardcodes de jobs como fuente de verdad persistente.
8. No fallback silencioso si SQL falla.
