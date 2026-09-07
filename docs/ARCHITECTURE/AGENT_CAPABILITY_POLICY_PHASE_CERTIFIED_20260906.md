# EDARSAHUB — Capability / Policy Layer — Phase Certification

Fecha de cierre: 2026-09-06
Entorno: Edarsahub_Desarrollo
Produccion: NO tocada

## Contrato de autoridad
requested ∩ user_allowed ∩ agent_allowed ∩ environment_allowed ∩ policy_allowed

Skill es procedimiento, no autoridad. Agent Reach y AI Gateway son ejecutores sometidos a Policy.

## Cadena certificada
RBAC resuelto -> Capability/Policy -> Procedure/Skill -> Agent Reach o AI Gateway -> Execution Gate

## Evidencia terminal
- Gate 2A: WORKER-CAPABILITY-POLICY-ENGINE-GATE2A-20260906 — CERTIFIED SHA 575db30bf47e6f08d4730deab73bdb2f174a57c2
- Gate 2B: WORKER-SKILLS-POLICY-LAYER-GATE2B-20260906 — CERTIFIED SHA ba6bcaa2bf3156ee177fe8ba3db4b6cd0a512694
- Gate 2C R2: WORKER-AGENT-REACH-POLICY-ADAPTER-GATE2C-R2-20260906 — CERTIFIED SHA 73e09fa9ca548c9f949feb2e7a8887e7cae15630
- Gate 2D R2: WORKER-AI-GATEWAY-POLICY-GATE2D-R2-20260906 — CERTIFIED SHA 23b798ecf215dc04ab62f3a14bcace971a1022c5
- Gate 3: WORKER-CAPABILITY-POLICY-E2E-GATE3-20260906 — CERTIFIED SHA ccdeeb7e222c023e2c1ce05f30c984008d62a116

## Invariantes certificados
- Produccion prohibida por defecto.
- Sin autoescalacion de roles/capabilities/scopes.
- Skills no conceden autoridad.
- Agent Reach requiere EXTERNAL_RESEARCH y riesgo maximo R1.
- Egress sujeto a clasificacion y budgets.
- AI Gateway requiere AI_INFERENCE y scopes provider/model.
- Seleccion de modelo solo entre candidatos autorizados dentro de budget.
- Execution Gate falla cerrado si RBAC previo niega.
- Sin SQL, red, subprocess ni SDKs desde esta capa.

## Fuera de alcance
- Activacion real de runtime.
- Instalacion/conexion de OmniRoute.
- Proveedores AI reales.
- Produccion.
- Worker/bridge/dispatcher/Supervisor/watchdog.
- RBAC SQL canonico.

## Estado
La fase Capability/Policy queda certificada en desarrollo con evidencia SHA-bound. Cualquier activacion runtime u OmniRoute requiere fase nueva y debe mantener fail-closed.
