# EDARSAHUB · Universal Worker Console — README de Operación

## Qué es
Consola visual para **operar el Universal Worker** sin pegar bash, JSON crudo ni scripts.
**Fase 1 = SOLO LECTURA.** No toca Producción · No ejecuta SQL · No muta · No usa Mongo como fuente.

## Acceso
- Ruta frontend: **`/worker-console`** (requiere sesión iniciada).
- Backend: **`/api/worker/console/*`** (todos los endpoints exigen JWT).
- **RBAC:** consultar = cualquier usuario autenticado. Publicar / limpiar preferred_job = **solo SUPERADMIN** (Fase 2).

## Fuente de datos (solo lectura)
- `worker/requests/` (publicación futura — Fase 2)
- `.git/universal-worker-queue/{pending,processing,results,done,published,rejected}`
- `.git/universal-worker-queue/runtime/` (preferred_job.json, control_plane_status.json, reconciler.json, logs)

## Módulos (Fase 1)
| Tab | Función |
|-----|---------|
| **Dashboard** | Conteos por estado + runtime (current_job_id, generación, último ciclo, preferred_job huérfano). |
| **Lifecycle** | Rastrea un `job_id` por todas las colas + interpreta su result. |
| **Intérprete** | Lee el result de un `job_id` y extrae certification / quality_gate / blockers / production_touched / files_changed. |
| **Tablajerías** | Checklist de cierre precargado leyendo los results reales (R24E, R24F, R24E+R24F compat, Release Manifest/Patch/DryRun/Go-NoGo R1B). |
| **Auditoría** | Visor de evidencia de runtime (cert.log, launch.log, control_plane_status, reconciler). Solo lectura. |

## Endpoints
```
GET /api/worker/console/dashboard
GET /api/worker/console/jobs/{state}?limit=&offset=&q=
GET /api/worker/console/lifecycle/{job_id}
GET /api/worker/console/result/{job_id}
GET /api/worker/console/tablajerias/checklist
GET /api/worker/console/audit?tail=
POST /api/worker/console/validate        # valida contrato v2 SIN escribir (para Fase 2)
```

## Reglas de contrato (`edarsahub.worker-job.v2`)
- `READ_ONLY` **debe** tener `actions=[]` (el validador lo rechaza si no).
- No se publican gates nuevos automáticamente.
- Publicar (Fase 2) **solo** escribe en `worker/requests/*.json`; nunca en pending/processing/results/done/published/rejected.

## Caso Tablajerías (estado actual)
7 checks certificados → **GO técnico READ_ONLY**, `production_touched=false`.
➡ **Siguiente decisión: autorización humana explícita antes de Producción.** La consola NO autoriza Producción automáticamente.

## Fase 2 (pendiente, requiere SUPERADMIN + confirmación explícita)
Publicador visual de jobs · plantillas READ_ONLY/MUTATION · Go/No-Go operativo · limpieza reversible de preferred_job huérfano · checklist de cierre publicable · auditoría de escritura de acciones.

## Tests
```
cd /app/backend && python -m pytest tests/test_worker_console_contract.py -q
```
