# AH4 - Worker Compiler Adapter V1

## Scope
AH4 agrega un adaptador determinista entre el Plan/Route certificados por AH3 y el contrato `edarsahub.worker-job.v2`. Vive en `backend/modules/agent_harness`, no en `backend/core`.

## Regla principal
El compilador NO es un agente y NO interpreta intenciones. Recibe un `PlanStep`, un `RouteDecision`, acciones estructuradas y checks estructurados ya decididos. Solo empaqueta y valida.

## Invariantes
- Solo `executor=worker`.
- `step.id == route.step_id`.
- Repo fijo: `rbalam/EDARSA_HUB`.
- Rama fija: `Edarsahub_Desarrollo`.
- `production_allowed=false` fijo.
- Acciones permitidas: replace_text, write_file, delete_file.
- Checks de mutacion permitidos: git_diff_check, py_compile, pytest, frontend_build.
- Shell/command/script y overrides de repo/rama/Production son rechazados.
- El job compilado se valida otra vez con `tools/mirror_sync/universal_job_bridge.validate`, de modo que conserva los candados canonicos del Worker, incluido Core Slimming.

## Harness context
El job incluye evidencia no autoritativa de plan_step, dominio, procedure, riesgo, clasificacion, agente, skill y executor. Es trazabilidad; no sustituye RBAC ni policies.

## Exclusiones
AH4 no ejecuta el job, no publica en la cola, no llama APIs/red, no toca SQL/Mongo, no crea permisos y no habilita Production. `READ_ONLY_SQL` queda fuera de este adaptador de mutacion y mantiene su flujo canonico separado.

## Gate siguiente
AH5 agrega Evidence + Provenance para correlacionar plan, route, skill/version/checksum, job y resultado terminal sin crear una fuente paralela innecesaria.
