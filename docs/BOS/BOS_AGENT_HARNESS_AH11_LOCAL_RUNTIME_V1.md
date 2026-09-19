# AH11 - Local Runtime V1

AH11 agrega una capa de preparacion local para desarrollo sin crear un segundo motor de autorizacion.

## Contratos canonicos reutilizados
- `core.agent_execution_gate.ExecutionGateDecision`
- `core.agent_runtime_activation.RuntimeActivationRequest`
- `core.agent_runtime_activation.authorize_runtime_activation`

## Estados permitidos
- DEVELOPMENT + DRY_RUN: permitido, no listo para executor.
- DEVELOPMENT + LOCAL_EXECUTE: permitido y listo para adaptador local solo si Execution Gate ya autorizo.

## Fail closed
- Execution Gate denied
- STAGING o PRODUCTION
- EXECUTE
- external_execution_enabled
- request_id/step_id invalidos

## Limites absolutos
AH11 no ejecuta shell, procesos, red, SQL, Mongo, comunicaciones, AI, Universal Worker ni Production. Solo produce un envelope determinista para un adaptador de desarrollo futuro. No modifica `backend/core`, no amplia RBAC y no crea policy paralela.

## Siguiente gate
AH12 debe ser certificacion final READ_ONLY de Development sobre AH0-AH11.
