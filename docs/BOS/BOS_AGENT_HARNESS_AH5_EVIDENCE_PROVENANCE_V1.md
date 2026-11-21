# AH5 - Evidence + Provenance V1

## Scope
AH5 agrega evidencia inmutable y determinista dentro de `backend/modules/agent_harness`. No crea una base paralela ni agrega tablas. Correlaciona objetos que ya existen en el flujo: Plan, PlanStep, RouteDecision, SkillSpec, job AH4 y resultado terminal del Universal Worker.

## Evidencia
Contrato `edarsahub.bos-evidence.v1`. Registra request_id, hash canonico del plan, step, agent/version, skill/version/provenance/checksum, worker_job_id, hash canonico del job, estado/certificacion/quality gate/tests del resultado y hash canonico del resultado.

## Reglas fail-closed
- Step debe pertenecer al Plan.
- Route debe corresponder al mismo step y skill/version.
- Job debe ser `edarsahub.worker-job.v2`, apuntar a `rbalam/EDARSA_HUB` / `Edarsahub_Desarrollo` y mantener `production_allowed=false`.
- `harness_context` debe coincidir con step/route.
- Resultado debe tener el mismo job_id, repo y rama.
- Solo se acepta evidencia terminal.
- `production_touched` debe ser false.

## Hashes
Los SHA-256 se calculan sobre JSON canonico con claves ordenadas. Sirven para trazabilidad y deteccion de alteraciones; no sustituyen firma criptografica ni autoridad del Worker.

## Certificacion de exito
`is_certified_success` solo devuelve true cuando el resultado es INTEGRATED + CERTIFIED + PASS + tests PASS + Production no tocada. Un BLOCKED/FAILED puede conservarse como evidencia, pero nunca se convierte en exito.

## Persistencia
V1 permanece in-memory/composable y reutiliza `worker/requests` + `worker/results` como evidencia de ejecucion. Cualquier persistencia SQL futura requiere gate separado y evidencia de necesidad; AH5 no crea schema.

## Gate siguiente
AH6 Security + Red Team debe atacar Registry, Planner/Router, Worker Compiler y Evidence con pruebas negativas de privilege escalation, tampering, prompt/tool injection, egress, secrets, replay y cross-scope.
