# Procedimiento obligatorio para ejecutar comandos por Universal Worker

## Objetivo

Toda solicitud emitida desde ChatGPT hacia EDARSAHUB debe seguir el mismo circuito verificable. El objetivo es evitar que un job quede publicado pero sin pickup, y evitar interpretar un wake exitoso como si el job ya hubiera sido ejecutado.

## Secuencia obligatoria

1. Construir un job con `schema: edarsahub.worker-job.v2`, requester, target_repo, target_branch, production_allowed=false, acciones deterministas y checks.
2. Publicar el job en `worker/requests:worker_queue/inbox/<job_id>.json`.
3. Volver a leer el archivo publicado y confirmar que el contenido y el `job_id` coinciden.
4. Resolver el HEAD actual de `worker/requests`.
5. Crear un trigger en `Edarsahub_Desarrollo:worker_queue/triggers/runtime-recovery/<job_id>.json` con `existing_job_id=<job_id>`.
6. El workflow de runtime-recovery debe extraer `existing_job_id` del trigger y llamar `POST /api/internal/worker/wake` enviando:
   - `X-Worker-Queue-Sha: <HEAD worker/requests>`
   - `X-Worker-Preferred-Job-Id: <job_id>`
7. El endpoint debe validar el SHA de la cola, registrar el job preferido con expiracion y preservar cualquier job activo sano. Nunca debe interrumpir un job activo.
8. El dispatcher debe:
   - ejecutar primero el job preferido cuando aparezca en `pending`;
   - esperar brevemente por ese job si el intake aun no lo materializo;
   - eliminar la preferencia cuando expire;
   - volver al orden normal cuando no exista preferencia valida.
9. Confirmar pickup por evidencia terminal del Worker. Un wake verde NO equivale a job ejecutado.
10. No marcar un trabajo como completado hasta tener:
    - resultado en `worker_queue/results/<job_id>.json`;
    - status terminal satisfactorio;
    - commit integrado cuando el job sea MUTATION;
    - checks requeridos en PASS;
    - `production_touched=false`.

## Estados que debe reportar ChatGPT

- VERDE: resultado terminal satisfactorio y evidencia publicada.
- NARANJA: el job fue tomado y existe evidencia de ejecucion/processing.
- AMARILLO: job publicado pero aun no tomado.
- ROJO: rechazo, bloqueo, timeout, resultado fallido o infraestructura que impide pickup.

## Regla de preferencia

La preferencia no es preemption. Si existe otro job activo con heartbeat sano, el endpoint lo preserva y registra nuestro job como el siguiente preferido. Esto evita corromper ejecuciones en curso y al mismo tiempo evita que nuestro trabajo quede indefinidamente detras del orden alfabetico.

## Regla para ChatGPT

Para cada nuevo comando que requiera Universal Worker, ChatGPT debe ejecutar la secuencia completa de publicacion, verificacion, wake preferido y comprobacion de resultado. No debe crear variantes R2/R3/R4 de forma repetitiva mientras exista un job valido en curso o pendiente, salvo que exista un rechazo terminal que requiera una correccion de contrato.
