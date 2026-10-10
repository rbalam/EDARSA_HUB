# EDARSAHUB - P0 Production HTTP Scheduler Trigger

Fecha: 2026-10-10

## Objetivo

Eliminar la dependencia operativa de Ventas del Dia respecto al ciclo de vida
de Emergent Preview, sin modificar la logica protegida de
`sync_comercial_abiertas_v2_job.py`.

Emergent Live no admite un segundo proceso always-on independiente dentro del
mismo deployment. Por ello, el servicio standalone agregado en el hotfix
anterior NO sera el mecanismo de ejecucion en Emergent.

## Arquitectura objetivo

```
Cron externo cada 5 min
        |
        v
POST Live /api/internal/scheduler-trigger/sync-comercial-abiertas-v2
        |
        v
SchedulerManager.run_job_now("sync_comercial_abiertas_v2")
        |
        v
wrapper canonico + lock distribuido SQL + bitacora SQL
        |
        v
sync_comercial_abiertas_v2 protegido
        |
        v
EDARSAHUB SQL
```

Preview deja de ser propietario del scheduler.

## Protecciones

1. El endpoint solo opera si `EDARSA_ENV=PRODUCTION`.
2. El trigger esta deshabilitado por defecto.
3. Requiere `EDARSA_SCHEDULER_TRIGGER_KEY`.
4. La comparacion del secreto usa `hmac.compare_digest`.
5. El endpoint no importa ni duplica el job protegido.
6. Solo invoca `SchedulerManager.run_job_now("sync_comercial_abiertas_v2")`.
7. El lock distribuido SQL del wrapper canonico sigue evitando concurrencia.
8. La bitacora SQL del scheduler sigue siendo la evidencia de ejecucion.
9. `sync_comercial_abiertas_v2_job.py` conserva exactamente el blob productivo
   protegido `e97b55a06b0adb5b447904c7643b99844f00aae7`.

## Variables Live requeridas para el cutover

Primera fase de canary, manteniendo temporalmente el scheduler embebido:

```
EDARSA_ENV=PRODUCTION
EDARSA_RUNTIME_ROLE=LEGACY_EMBEDDED
EDARSA_SCHEDULER_TRIGGER_ENABLED=true
EDARSA_SCHEDULER_TRIGGER_KEY=<secreto dedicado>
```

Despues de certificar el endpoint y antes de habilitar el cron externo:

```
EDARSA_ENV=PRODUCTION
EDARSA_RUNTIME_ROLE=PRODUCTION_WEB
EDARSA_RUNTIME_ROLE_REQUIRED=1
SCHEDULER_ENABLED=false
EDARSA_SCHEDULER_TRIGGER_ENABLED=true
EDARSA_SCHEDULER_TRIGGER_KEY=<mismo secreto dedicado>
```

La variable global `SCHEDULER_ENABLED=false` impide que el backend web sea
propietario de APScheduler. La llamada manual mediante SchedulerManager se
mantiene disponible para este trigger controlado.

## Preview despues del cutover

```
EDARSA_ENV=PREVIEW
EDARSA_RUNTIME_ROLE=PREVIEW_WEB
EDARSA_RUNTIME_ROLE_REQUIRED=1
SCHEDULER_ENABLED=false
```

Aunque el secreto se copiara accidentalmente a Preview, el endpoint falla
cerrado porque exige entorno PRODUCTION.

## Secuencia de cutover

1. Merge del hotfix aprobado a `Edarsahub_Produccion`.
2. Llevar Preview temporalmente al commit productivo exacto requerido por el
   mecanismo de publish de Emergent, sin mezclar Desarrollo.
3. Configurar variables Live de canary.
4. Publicar Live.
5. Validar `/api/internal/scheduler-trigger/health` con credencial.
6. Ejecutar un POST manual y certificar escritura/bitacora.
7. Cambiar Live a `PRODUCTION_WEB`, `ROLE_REQUIRED=1`,
   `SCHEDULER_ENABLED=false`.
8. Habilitar el cron externo cada 5 minutos.
9. Verificar al menos dos ciclos consecutivos en Produccion.
10. Configurar Preview como `PREVIEW_WEB` con scheduler deshabilitado.
11. Dormir/reiniciar Preview.
12. Verificar al menos dos ciclos adicionales en Produccion.
13. Declarar `PRODUCTION_SCHEDULER_DECOUPLED=CERTIFIED`.

## Rollback

Si el trigger externo no produce datos:

1. Deshabilitar el cron externo.
2. Restaurar temporalmente Live a `LEGACY_EMBEDDED` con
   `SCHEDULER_ENABLED=true`.
3. No modificar el job protegido.
4. Investigar endpoint/configuracion antes de repetir el cutover.

El rollback no requiere revertir datos ni tocar el sincronizador canonico.
