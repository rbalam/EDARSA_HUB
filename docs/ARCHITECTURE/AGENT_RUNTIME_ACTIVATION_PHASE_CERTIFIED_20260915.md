# EDARSAHUB — Agent Runtime Activation — Phase Certification

Fecha de cierre: 2026-09-15
Entorno: Edarsahub_Desarrollo
Produccion: NO tocada

## Alcance certificado

Esta fase certifica la activacion controlada del runtime Agent Reach para investigacion externa publica bajo la cadena de autoridad EDARSAHUB. La capacidad sigue subordinada a RBAC, Capability/Policy, Procedure/Skill, Execution Gate, Runtime Activation y budgets. Mas capacidad no implica mas privilegio.

## Cadena certificada

Requester/RBAC -> Capability/Policy -> Procedure agent-reach-external-research -> Execution Gate -> Runtime Activation -> Agent Reach public search executor -> runtime Docker canonico -> egress publico controlado -> evidencia sanitizada.

## Evidencia terminal por Gate

- Gate 5A: WORKER-AGENT-RUNTIME-ACTIVATION-GATE5A-20260907 — CERTIFIED SHA 021b7581c878955ab9340266b830332b0c32caf6.
- Gate 5B R4: WORKER-AGENT-RUNTIME-ACTIVATION-GATE5B-R4-20260909 — CERTIFIED SHA efe2c06fc73e0c7306b05a7c260af3e3b369a66e.
- Gate 5C R2: WORKER-AGENT-RUNTIME-ACTIVATION-GATE5C-R2-20260909 — CERTIFIED SHA 7b58dc633e034ce5b1708775ab63a5e529900a62.
- Gate 5D R2: WORKER-AGENT-RUNTIME-ACTIVATION-GATE5D-R2-20260909 — CERTIFIED SHA e78f8ff4bcc9dbe42d822a0b8c6c047e28f6be8f.
- Gate 5E R3 deterministic: WORKER-AGENT-RUNTIME-ACTIVATION-GATE5E-R3-DETERMINISTIC-20260910 — CERTIFIED SHA 78016221668cbd045b645095a8f17147f4b0d14e.
- Gate 5F: WORKER-AGENT-RUNTIME-ACTIVATION-GATE5F-GITHUB-ACTIONS-LIVE-CANARY-HARNESS-R1-20260914 — CERTIFIED SHA 9ba7deecb25e09e3ccac22283651b7d6fe4e4a98.
- Gate 5G-R2: auto-trigger del Worker integrado y capaz de disparar GitHub Actions por marcador unico.
- Gate 5H: WORKER-AGENT-RUNTIME-ACTIVATION-GATE5H-PYTEST-HARNESS-R1-20260914 — CERTIFIED SHA bb5faa6d0a12483fc5f7c9023d21f74ed867b776.
- Gate 5I: WORKER-AGENT-RUNTIME-ACTIVATION-GATE5I-CANONICAL-PYTHON-DEPS-R1-20260914 — INTEGRATED SHA 74103f60837858e933dd6c64b3a8e39de9c46eb7; Worker terminal inicial 95% / PENDING_AUDIT_EVIDENCE. La evidencia externa vinculada a ese mismo SHA se detalla abajo y resuelve el pendiente de auditoria.

## Live canary SHA-bound

GitHub Actions workflow: Agent-Reach Live Canary
Run ID: 34934337406
Event: push
Head SHA: 74103f60837858e933dd6c64b3a8e39de9c46eb7
Conclusion: success
Artifact ID: 10382472368
Artifact name: agent-reach-live-canary-evidence-74103f60837858e933dd6c64b3a8e39de9c46eb7
Artifact digest: sha256:e4f23fed08f086e44084cc7aa594fb8ae0f7fa2fbdc448f828f2ced8a5e902b8

Todos los pasos del job live-canary terminaron success: checkout, verificacion SHA exacta, build de imagen canonica, setup Python, instalacion de dependencias publicas backend, ejecucion del canario real y carga del artifact sanitizado.

## Evidencia sanitizada del canario real

```json
{
  "schema": "edarsahub.agent-reach-live-canary.v1",
  "allowed": true,
  "canary_live": true,
  "docker_available": true,
  "duration_ms": 5012,
  "effective_scopes": ["external:web"],
  "external_calls_budget": 1,
  "output_limit_bytes": 65536,
  "procedure": "agent-reach-external-research",
  "production_touched": false,
  "reason": "OK",
  "returncode": 0,
  "stderr_bytes": 0,
  "stdout_bytes": 683,
  "success": true,
  "timeout_seconds": 30
}
```

## Invariantes certificados

- Produccion permanece prohibida y no fue tocada.
- El Universal Worker orquesta; no aloja Docker ni recibe docker.sock.
- GitHub Actions actua solo como host efimero del canario live, no como backend permanente.
- La imagen Agent Reach se construye desde infra/agent-reach/versions.lock mediante el build canonico.
- El canario esta SHA-bound al commit integrado.
- Se ejecuta exactamente con budget de 1 llamada externa.
- Timeout maximo del canario: 30 segundos.
- Limite de salida: 65536 bytes; evidencia observada: 683 bytes stdout y 0 bytes stderr.
- Scope efectivo: external:web.
- Procedure: agent-reach-external-research.
- No secrets, cookies, headers arbitrarios, mounts, docker.sock, docker push, deploy, SQL, Mongo ni OmniRoute forman parte del camino live certificado.
- AI_INFERENCE permanece separado de EXTERNAL_RESEARCH.
- La evidencia publicada es sanitizada.

## Resolucion de Gate 5I

El estado 95% / PENDING_AUDIT_EVIDENCE de Gate 5I correspondia exclusivamente a la espera de evidencia live externa. El run 34934337406, ligado exactamente al SHA integrado 74103f60837858e933dd6c64b3a8e39de9c46eb7, termino success y produjo el artifact sanitizado con success=true, reason=OK, returncode=0, external_calls_budget=1 y production_touched=false. Gate 5J usa esta evidencia como attestation terminal y resuelve ese pendiente sin reescribir el historico de worker/results.

## Fuera de alcance

- Despliegue de Agent Reach a Produccion.
- Uso de GitHub Actions como servicio runtime permanente.
- Activacion de OmniRoute o proveedores AI reales.
- Cambios a RBAC SQL canonico.
- Cambios a Worker, bridge, dispatcher, Supervisor o watchdog.
- Cambios funcionales adicionales en Agent Reach o backend.

## Estado final

Con la evidencia deterministica de Gates 5A-5I y el live canary real SHA-bound del run 34934337406, la fase Agent Runtime Activation queda CERTIFIED en Edarsahub_Desarrollo. Gate 5J constituye el cierre formal de la fase y la attestation terminal que resuelve el pendiente de auditoria de Gate 5I. Produccion permanece intacta.
