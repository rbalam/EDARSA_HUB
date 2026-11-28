# BOS V1 Gate E - E2 Minimal Implementation Plan V1

Estado: PLAN ONLY / NO IMPLEMENTATION
Fecha: 2026-09-17

Fuentes certificadas:
- BOS-V1-GATE-E-E1-CONTRACT-CAPABILITY-MAPPING-R1-20260917
- BOS-V1-GATE-E-EXECUTIVE-BOS-DESIGN-CONTRACT-R2-20260917
- BOS-V1-GATE-E-EXECUTIVE-BOS-GAP-MATRIX-R1-20260917

## Regla

`REUSE -> CONSOLIDATE -> EXTRACT -> EXTEND -> CREATE_ONLY_WHEN_PROVEN_MISSING`

Este Gate no autoriza codigo, DDL, endpoints, permisos, jobs ni Produccion.

## 1. Resultado E1

### A. CAUSAL_EXPLANATION_LAYER

Clasificacion:
`EXTEND_EXISTING + MISSING_ORCHESTRATION`

REUSE probado:
- Decision Dashboard y drilldowns existentes.
- auditoria SQL-first.
- provenance/evidence patterns.
- freshness/stale/FechaOperacion.
- eventos y trazabilidad existentes.

MISSING probado:
- una orquestacion ejecutiva que produzca claim, evidence_refs, contributing_factors, confidence_class, limitations y NOT_ENOUGH_EVIDENCE.
- no existe un runtime general de causalidad; drilldown no es causalidad.

Implementacion minima propuesta:
- bounded context nuevo o extension dentro de un modulo BOS ejecutivo/direction, NO backend/core.
- servicio puro que reciba evidencias ya resueltas y clasifique HECHO/CORRELACION/INFERENCIA.
- no persistir inicialmente si puede ser derivado on-demand de fuentes canonicas.
- sin LLM obligatorio; LLM solo podria redactar sobre una estructura determinista ya construida.

## 2. EXECUTIVE_PRIORITY_AGGREGATION

Clasificacion:
`EXTEND_EXISTING + MISSING_CROSS_DOMAIN_AGGREGATOR`

REUSE probado:
- workflows.
- SLA.
- prioridades.
- tareas/responsables.
- vencimientos y escalamiento.
- notificaciones.
- objetos fuente por dominio.

MISSING probado:
- agregador ejecutivo cross-domain.
- normalizacion comun de severidad/impacto/vencimiento sin duplicar lifecycle.

Implementacion minima propuesta:
- adaptadores de lectura por dominio hacia un DTO ejecutivo comun.
- agregador read-only que referencia source_domain + source_object_ref.
- prioridad explicable; no hardcodear pesos globales.
- configuracion futura solo si evidencia demuestra necesidad.
- no nueva tabla de tareas ejecutivas.

## 3. BOS_RECOMMENDATION_CONTRACT

Clasificacion:
`MISSING_RUNTIME_CONTRACT + REUSE_INFRASTRUCTURE`

REUSE probado:
- agent_capability_policy.
- agent_procedure_policy.
- agent_execution_gate.
- AI gateway/routing.
- IA Assistant como superficie conversacional.
- auditoria/evidence.
- fuentes SQL-first.

MISSING probado:
- runtime con recommendation_id, rationale, evidence_refs, expected_impact, risk_level, confidence_class, validity, eligible_actions y confirmation requirements.
- no existe evidencia de recommendation runtime empresarial operativo.

Implementacion minima propuesta:
- recomendaciones deterministas primero.
- LLM nunca fuente de hechos.
- LLM opcional solo para explicacion/redaccion.
- recomendacion sin evidencia suficiente => no emitir.
- stale/freshness obligatorio.
- no persistencia nueva hasta demostrar necesidad de historial operacional.

## 4. RECOMMENDATION_TO_AUTHORIZED_ACTION_BRIDGE

Clasificacion:
`EXTEND_EXISTING`

REUSE probado:
- RBAC.
- agent_capability_policy.
- agent_procedure_policy.
- agent_execution_gate.
- workflows de dominio.
- Universal Worker.
- idempotencia/guardas y auditoria existentes.

MISSING minimo:
- adaptador que traduzca eligible_action declarativa a una capacidad/procedure ya allowlisted.
- enlace auditable recommendation_id -> requested action -> policy decision -> outcome.

Regla:
NO crear nuevo executor.
El bridge selecciona y solicita una capacidad existente; la ejecucion sigue perteneciendo al workflow/domain service/Universal Worker canonico.

## 5. Ownership propuesto

No crecer `backend/core`.

Candidatos preferidos:
- `backend/modules/bos_executive/` o bounded context equivalente si ya existe owner canonico al momento de E3.
- adaptadores dentro de modulos fuente cuando solo expongan un DTO read-only.
- frontend: extender Tablero Ejecutivo/Direccion como consumidor, no fuente de verdad.

Core existente solo se REUSA:
- policy.
- execution gate.
- auditoria comun.
- scheduler kernel.
- SQL/identity/context abstractions.

## 6. Secuencia E3 atomica

### E3A - Executive Evidence DTO + causal explanation
Solo contratos/servicio read-only + tests.
Sin persistencia.

### E3B - Cross-domain priority adapters + aggregator
Solo lectura.
Sin duplicar tareas/workflows.

### E3C - Deterministic recommendation service
Construye recomendacion desde finding/priority item.
Sin ejecucion.

### E3D - Authorized action bridge
Mapeo allowlisted hacia policy/procedure/execution channel existente.
Default deny.
Sin nuevo executor.

### E3E - Frontend executive integration
Mostrar:
- por que.
- que atender.
- recomendacion.
- acciones elegibles/autorizables.
No ejecutar automaticamente.

### E3F - E2E certification
Validar las seis preguntas con fixtures/casos controlados en Desarrollo.
Produccion prohibida.

## 7. Condiciones fail-closed

- sin evidencia => NOT_ENOUGH_EVIDENCE.
- datos stale => marcar stale.
- sin permiso => accion no elegible.
- policy deny => no ejecutar.
- procedure desconocida => no ejecutar.
- recomendacion expirada => no ejecutar.
- ausencia de idempotencia cuando sea requerida => no ejecutar.
- acciones de pago/financieras => Gate especifico adicional.

## 8. Prohibiciones

- no nuevo RBAC.
- no nuevo scheduler.
- no nuevo workflow engine.
- no nuevo Worker.
- no nuevo action executor.
- no Mongo operativo.
- no LIVE administrativo.
- no LLM generando SQL.
- no tablas nuevas sin evidencia posterior.
- no crecimiento de backend/core.

## 9. Estado

`E1_MAPPING=CERTIFIED_READ_ONLY`
`E2_PLAN_READY=YES`
`E3_IMPLEMENTATION_STARTED=NO`
`GATE_E_CERTIFIED=NO`
`PRODUCTION_TOUCHED=false`
