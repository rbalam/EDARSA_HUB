# AH9 - Control Plane V1

AH9 agrega una vista de observabilidad y gobierno sobre el Agent Harness. No es un segundo sistema de ejecucion ni una base paralela.

## Fuentes de verdad
- Gate state proviene de resultados canonicos del Universal Worker/gate chain.
- Evidence proviene de AH5.
- Budgets provienen de envelopes/policy existentes.

El Control Plane solo compone snapshots deterministas. No ejecuta jobs, no modifica registries, no reescribe worker/results y no concede permisos.

## Fail closed
Rechaza estados no terminales ambiguos, gates certificados incompletos, blockers en gates certificados, Production tocada, budgets negativos/excedidos y duplicados de identidad.

## Salud
`healthy=true` solo cuando no hay blockers agregados y ninguna evidencia marca Production tocada.

## Maximas
Fuera de backend/core; sin SQL/Mongo/red; sin bypass RBAC; sin Production; sin nuevo origen de verdad.

## Siguiente gate
AH10 E2E Simulation debe probar de punta a punta Registry -> Planner/Router -> Worker Compiler -> Evidence -> Red Team/Marketing/Mobile -> Control Plane, en simulacion determinista sin ejecucion externa.
