# EDARSAHUB BOS — Universal Worker Remote Canonical Ingress — Gate 0 R1

## Estado

**CERTIFIED_DESIGN / READ_ONLY DISCOVERY COMPLETE**

Este Gate no modifica runtime, SQL, Worker, Produccion ni permisos. Documenta el contrato canonico para exponer el Universal Worker a ChatGPT/Plugins sin usar GitHub `create_file` como interfaz operativa.

## Evidencia canonica reutilizada

1. `tools/mirror_sync/gate_chain_publisher.py`
   - Ya implementa `submit(job_spec)`.
   - Valida template y `worker-job.v2`.
   - Autoriza requester.
   - Verifica convergencia Git.
   - Publica a `worker/requests`.
   - Es idempotente sobre lifecycle local/remoto.

2. `tools/mirror_sync/worker_job_factory.py`
   - Es la fabrica canonica del envelope.
   - Fija repo `rbalam/EDARSA_HUB`.
   - Fija branch `Edarsahub_Desarrollo`.
   - Fija `production_allowed=False`.
   - Fija idioma `es`.
   - Normaliza requester y scheduling.

3. `tools/mirror_sync/worker_requester_rbac.py`
   - SQL-first via `AuthRepository`.
   - No hardcodea emails.
   - Autoriza solo usuario activo SUPERADMIN.
   - Mantiene autenticacion funcional separada del transporte GitHub.

4. `tools/mirror_sync/worker_control_plane.py`
   - Supervisa runtime/heartbeat/recovery.
   - No debe asumir responsabilidades de API/ingress.

5. `backend/modules/worker_runtime_wake/routes.py`
   - Endpoint interno de wake existente.
   - Contrato distinto: valida queue SHA y solo reinicia el servicio fijo.
   - No debe ampliarse para submit de jobs.

## Gap confirmado

No existe una API HTTP canonica para:

- enviar un job determinista a `gate_chain_publisher.submit()`;
- consultar lifecycle/result por `job_id`;
- exponer estas operaciones como Plugin/Connector de ChatGPT.

Por esta ausencia, ChatGPT termina intentando escribir archivos directamente en GitHub `worker_queue/inbox`, lo que:
- bypassa el boundary semantico de `submit()`;
- puede activar controles de seguridad externos;
- duplica responsabilidades de publicacion;
- obliga a scripts/manualidad en algunos chats.

## Arquitectura objetivo

```text
ChatGPT / Plugin
       |
       v
backend/modules/worker_ingress/
       |
       +-- POST /api/internal/worker/jobs
       |      |
       |      +-- auth EDARSAHUB
       |      +-- requester derivado de current_user
       |      +-- canonicalize_job()
       |      +-- gate_chain_publisher.submit()
       |
       +-- GET /api/internal/worker/jobs/{job_id}
              |
              +-- lifecycle/results canonicos
```

## Bounded context

Crear modulo dedicado:

```text
backend/modules/worker_ingress/
    __init__.py
    routes.py
    service.py
    schemas.py
```

No colocar submit remoto dentro de:
- `worker_runtime_wake`;
- `worker_control_plane`;
- CAVAS;
- scheduler;
- GitHub helpers.

## Contrato POST

Entrada minima recomendada:

- `job_id`
- `objective`
- `mode`
- `actions`
- `checks`
- `scheduling` opcional

El endpoint NO acepta requester arbitrario. Debe derivarlo del usuario autenticado:

- email
- UsuarioID
- role
- project/chat metadata cuando el conector la entregue

El envelope final siempre pasa por `canonicalize_job()` / `validate_template()` / `submit()`.

## Campos prohibidos en frontera

Rechazar explicitamente:
- `production_allowed=true`
- credenciales
- passwords
- secrets
- tokens
- raw Git commands
- shell
- force push
- repo/branch alternativos

SQL solo puede pasar por contratos ya permitidos por el Worker, por ejemplo `sql_readonly_audit`; no se agrega un ejecutor SQL nuevo.

## Contrato GET status

Debe resolver un job_id contra lifecycle canonico:

- drafts
- pending
- processing
- results
- done
- rejected

Respuesta:
- job_id
- lifecycle
- status
- certification
- quality_gate
- tests
- percent_complete
- blockers
- files_changed
- commit_sha
- git_sync_status
- production_touched
- summary_es

Nunca devolver payloads con secretos.

## Autorizacion

Fase inicial:
- autenticacion EDARSAHUB obligatoria;
- permiso/rol canonico existente de SuperAdmin;
- validacion adicional por `worker_requester_rbac.authorize_requester`.

No crear un segundo sistema de usuarios.

Si posteriormente se necesita delegacion no-SuperAdmin, debe ser un Gate RBAC separado y explicito.

## Plugin / Connector

El conector debe exponer solo:

1. `submit_job`
2. `get_job_status`

No exponer:
- filesystem;
- Git arbitrario;
- terminal;
- secretos;
- comandos;
- wake/restart directo.

## Criterios de Gate 1

Gate 1 queda certificado solo si:

- endpoint usa `gate_chain_publisher.submit()`;
- requester proviene de auth, no del body;
- fixed fields no pueden ser sobreescritos;
- no hay GitHub `create_file` desde el endpoint;
- no hay shell;
- no hay SQL writer;
- tests cubren deny/allow/idempotencia/status;
- Produccion no es tocada.

## Canaries globales posteriores

1. CAVAS — publicar un job READ_ONLY/MUTATION controlado.
2. Tablajeria — publicar un job de otro bounded context.

Solo si ambos usan el mismo ingress se considera resuelto globalmente para todos los chats.

## Siguiente Gate

`EDARSAHUB-BOS-UNIVERSAL-WORKER-REMOTE-CANONICAL-INGRESS-GATE1-R1`

Objetivo: implementar backend `worker_ingress` y tests, sin Plugin todavia.
