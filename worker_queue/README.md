# EDARSAHUB Universal Worker Queue

Esta rama es el buzón universal de órdenes para el worker de EDARSAHUB.

## Propósito

Permitir que ChatGPT, Claude, Copilot, Antigravity, Codex u otro agente con acceso autorizado a GitHub entregue una orden al mismo worker sin necesitar acceso directo a `/app`.

## Separación de responsabilidades

- `Edarsahub_Desarrollo`: única fuente canónica del código.
- `worker/requests`: transporte de órdenes, estados y resultados; no es rama de desarrollo.
- `EDARSAHUB_AUDIT_EVIDENCE`: evidencia y certificación; no recibe órdenes ejecutables.
- `Edarsahub_Produccion`: fuera de este flujo.

## Carpetas

- `worker_queue/inbox/`: órdenes nuevas.
- `worker_queue/processing/`: estado lógico reservado para una orden tomada por el worker.
- `worker_queue/results/`: resultado final o parcial.
- `worker_queue/rejected/`: órdenes inválidas o inseguras.

Los estados pueden representarse mediante archivos de resultado sin borrar la solicitud original. Esto conserva trazabilidad.

## Contrato de una orden

Cada orden es un JSON independiente llamado `<job_id>.json`.

Campos mínimos:

```json
{
  "schema": "edarsahub.worker-job.v1",
  "job_id": "identificador-unico",
  "created_at_utc": "ISO-8601",
  "requested_by": "chatgpt|claude|copilot|antigravity|codex|human|other",
  "target_repo": "rbalam/EDARSA_HUB",
  "target_branch": "Edarsahub_Desarrollo",
  "objective": "objetivo completo en lenguaje natural",
  "acceptance": ["condiciones para considerar correcto el trabajo"],
  "constraints": ["restricciones obligatorias"],
  "production_allowed": false,
  "human_summary_language": "es",
  "human_summary_level": "13yo-non-programmer"
}
```

## Reglas fail-closed

El worker debe rechazar una orden si:

- el schema no es reconocido;
- falta `job_id`, objetivo o rama;
- `target_repo` no es `rbalam/EDARSA_HUB`;
- `target_branch` no es `Edarsahub_Desarrollo`;
- `production_allowed` no es exactamente `false`;
- el job intenta incluir secretos o credenciales;
- el job pide `force push`, reset/clean destructivo o pérdida de trabajo;
- existe otro resultado final para el mismo `job_id`;
- no puede garantizar concurrencia segura.

## Regla de autonomía

El worker debe ejecutar el objetivo, no reinterpretarlo como una tarea distinta. Puede escoger los pasos técnicos necesarios siempre que respete el objetivo, las restricciones, las fuentes canónicas y RBAC.

Si una parte puede hacerse y otra está bloqueada, debe completar la parte segura y reportar exactamente lo que falta.

## Resultado

El worker debe escribir `worker_queue/results/<job_id>.json` con estado, versión resultante de Desarrollo, pruebas realmente ejecutadas, archivos modificados, bloqueos y un resumen en español natural.

Una orden procesada NO equivale automáticamente a trabajo certificado. La certificación final sigue las reglas de `EDARSAHUB_AUDIT_EVIDENCE`.
