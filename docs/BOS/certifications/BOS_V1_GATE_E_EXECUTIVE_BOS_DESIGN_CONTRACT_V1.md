# BOS V1 Gate E - Executive BOS Design Contract V1

Estado: DESIGN CONTRACT / NO IMPLEMENTATION
Fecha: 2026-09-17

Fuentes:
- BOS-V1-GATE-E-EXECUTIVE-BOS-CERTIFICATION-R2-READONLY-20260917
- BOS-V1-GATE-E-EXECUTIVE-BOS-GAP-MATRIX-R1-20260917

## 1. Objetivo

Definir el contrato minimo y gobernado para cerrar los cuatro gaps funcionales probados de Gate E sin duplicar capacidades BOS existentes.

Regla obligatoria:

`REUSE -> CONSOLIDATE -> EXTRACT -> EXTEND -> CREATE_ONLY_WHEN_PROVEN_MISSING`

Este documento NO autoriza implementacion, tablas, endpoints, permisos, jobs ni cambios de Produccion.

## 2. Gap A - CAUSAL_EXPLANATION_LAYER

### Proposito
Responder "por que ocurre" un problema ejecutivo usando evidencia rastreable, no solo drilldown.

### Inputs
- KPI/metric_id canonico.
- empresa/unidad/sucursal y periodo.
- observacion/problema detectado.
- datos canonicos SQL-first.
- eventos/auditorias/workflows relacionados.
- provenance y freshness disponibles.

### Output minimo
- finding_id.
- claim: explicacion concreta.
- evidence_refs: referencias verificables.
- contributing_factors: factores observados.
- confidence_class: determinista / correlacional / inferido.
- as_of / freshness / stale.
- limitations.
- suggested_next_checks.

### Reglas
- No declarar causalidad si solo existe correlacion o drilldown.
- Toda explicacion debe distinguir hecho, correlacion e inferencia.
- Sin evidencia suficiente: `NOT_ENOUGH_EVIDENCE`.
- No usar Mongo como fuente operativa.
- No consultar LIVE para dashboards administrativos.
- Reutilizar auditoria/provenance, KPIs y fuentes SQL canonicas.
- No crear un root cause engine paralelo si la capacidad puede extender servicios existentes.

## 3. Gap B - EXECUTIVE_PRIORITY_AGGREGATION

### Proposito
Responder "que debe atenderse primero" consolidando pendientes cross-domain.

### Inputs
- workflows y SLA existentes.
- severidad/impacto.
- vencimiento.
- valor economico expuesto.
- riesgo operativo.
- dependencias.
- empresa/unidad/scope autorizado.

### Output minimo
- priority_item_id.
- source_domain.
- source_object_ref.
- priority_band.
- score_components explicables.
- due_at / sla_state.
- impact.
- owner/responsible_ref.
- required_permission.
- reason_for_priority.

### Reglas
- No sustituir workflows/SLA existentes.
- No hardcodear pesos globales sin configuracion canonica.
- Empates deben ser deterministicamente explicables.
- La prioridad no concede permiso de accion.
- El agregador ejecutivo solo referencia objetos fuente; no duplica su lifecycle.

## 4. Gap C - BOS_RECOMMENDATION_CONTRACT

### Proposito
Responder "que recomienda el BOS" con recomendaciones basadas en evidencia canonica.

### Input minimo
- executive finding o priority item.
- datos canonicos usados.
- contexto empresa/unidad.
- policies aplicables.
- restricciones.
- freshness/provenance.

### Output minimo
- recommendation_id.
- recommendation_type.
- title.
- rationale.
- evidence_refs.
- expected_impact.
- risk_level.
- confidence_class.
- generated_at / valid_until.
- required_permissions.
- eligible_actions.
- human_confirmation_required.
- stale/provenance metadata.

### Reglas
- Una recomendacion nunca equivale a autorizacion.
- Debe ser explicable.
- Debe señalar datos stale o incompletos.
- IA generativa puede redactar/explicar, pero no inventar hechos empresariales.
- Preferir reglas deterministas para recomendaciones repetibles.
- No ejecutar SQL generado por LLM.
- Si no hay evidencia suficiente: no recomendar.

## 5. Gap D - RECOMMENDATION_TO_AUTHORIZED_ACTION_BRIDGE

### Proposito
Conectar una recomendacion con una accion elegible sin saltarse RBAC, policy, workflow ni confirmacion humana.

### Flujo canonico

```text
Recommendation
  -> Eligible Action
  -> Capability/Procedure Policy
  -> RBAC + scope
  -> Preconditions
  -> Human confirmation when required
  -> Existing workflow / Universal Worker / domain service
  -> Audit evidence
  -> Outcome
  -> Recommendation feedback
```

### Contrato de accion
- action_type.
- recommendation_id.
- target_ref.
- requested_by.
- acting_scope.
- required_permission.
- required_policy.
- preconditions.
- dry_run_supported.
- confirmation_required.
- execution_channel.
- idempotency_key.
- audit_ref.
- outcome_status.

### Reglas
- Default = no ejecutar.
- Toda accion debe ser allowlisted.
- No accion por texto libre del LLM.
- No bypass de RBAC/policy.
- No usar HRLectura como writer.
- Universal Worker conserva sus contratos y guardas.
- Acciones financieras/pagos requieren Gate especifico y controles adicionales.
- Production permanece fuera de alcance salvo autorizacion humana expresa.

## 6. Reutilizacion obligatoria

Los cuatro gaps deben apoyarse en:
- Auth/RBAC canonico.
- capability policy / procedure policy existentes.
- workflows/SLA existentes.
- Scheduler y Universal Worker.
- SQL-first / sources canonicas.
- auditoria y evidencia existentes.
- catalogo/capability registry existente.
- contratos de empresa/unidad/sucursal.
- Decision Dashboard y Tablero Ejecutivo como consumidores, no como nuevas fuentes de verdad.

## 7. No crear todavia

Este Gate NO autoriza:
- nuevas tablas.
- nuevas columnas.
- nuevos endpoints.
- nuevos permisos.
- nuevos jobs.
- nuevo scheduler.
- nuevo workflow engine.
- nuevo recommendation engine fisico.
- nuevo action executor.
- cambios en backend/core.

Todo CREATE futuro debe demostrar por evidencia exacta que REUSE/EXTEND no son suficientes.

## 8. Gates siguientes propuestos

E1 - Contract-to-existing-capability mapping:
mapear cada campo/flujo de este contrato a implementaciones reales existentes y marcar REUSE/EXTEND/MISSING.

E2 - Minimal implementation plan:
solo para gaps MISSING probados, con owners y archivos exactos.

E3 - Surgical implementation:
cambios minimos con tests y rollback.

E4 - Executive E2E certification:
validar las seis preguntas de Direccion con casos reales/sinteticos controlados, sin Production.

## 9. Criterio de cierre de Gate E

Gate E solo puede cerrarse cuando las seis preguntas de Direccion tengan evidencia funcional:

1. Como estamos.
2. Donde estan los problemas.
3. Por que ocurren.
4. Que debe atenderse.
5. Que recomienda el BOS.
6. Que acciones autorizadas puede ejecutar.

`GATE_E_CERTIFIED=NO`
`DESIGN_CONTRACT_READY=YES`
`PRODUCTION_TOUCHED=false`
