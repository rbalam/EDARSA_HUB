# AH3 - Planner + Router V1

## Scope
AH3 agrega exclusivamente planeacion side-effect-free y routing determinista dentro de `backend/modules/agent_harness`. No ejecuta jobs, no llama red, no toca SQL, no cambia RBAC y no agrega archivos a `backend/core`.

## Planner
Contrato `edarsahub.bos-plan.v1`. Cada PlanStep declara dominio, procedimiento/skill, capabilities, scopes, riesgo, clasificacion de datos, executor y dependencias. El planner valida IDs unicos, dependencias existentes y DAG sin ciclos. El orden topologico es estable y determinista.

## Router
Solo considera AgentSpec y SkillSpec APPROVED. Deben satisfacer simultaneamente dominio, procedimiento, capabilities, scopes, risk ceiling, data classification y executor. Si no existe una combinacion elegible, falla cerrado con `NO_ELIGIBLE_ROUTE`.

Cuando existen varias rutas validas, elige menor privilegio: menor risk ceiling del agente; menos capabilities; menos scopes; menor risk ceiling de la skill; menor superficie de scopes/capabilities de la skill; luego desempate lexicografico determinista.

## Limites
AH3 no evalua el RBAC del usuario final ni ejecuta side effects. Esas autoridades siguen perteneciendo a los gates/policies existentes y a Execution Gate. El router nunca amplifica privilegios y no sustituye a Agent Capability Policy ni Procedure Policy.

## Gate siguiente
AH4 compila una ruta y plan ya autorizables al contrato determinista del Worker Universal. AH4 no puede transformar texto libre en shell.
