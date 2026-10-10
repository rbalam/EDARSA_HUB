# P0 - Desacoplamiento del Scheduler Productivo de Emergent Preview

## Objetivo

Eliminar la dependencia operativa de Produccion respecto del ciclo de vida del
Preview/IDE de Emergent sin modificar la logica del job protegido
`sync_comercial_abiertas_v2`.

La correccion introduce propiedad explicita del runtime y una aplicacion
standalone para ejecutar el scheduler productivo como servicio always-on.

## Regla de arquitectura

Despues del cutover debe existir un unico propietario de los jobs periodicos
productivos:

```text
POS/APIs -> Production Scheduler Service -> EDARSAHUB -> Production Web
```

El Preview de Emergent queda fuera de esa cadena. Dormir, reiniciar o recrear
Preview no debe detener ni reactivar sincronizaciones productivas.

## Variables de entorno

### Servicio Scheduler de Produccion

```text
EDARSA_ENV=PRODUCTION
EDARSA_RUNTIME_ROLE=PRODUCTION_SCHEDULER
EDARSA_RUNTIME_ROLE_REQUIRED=1
SCHEDULER_ENABLED=true
SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED=true
```

Comando de arranque, con working directory `/app/backend`:

```text
uvicorn scheduler_service:app --host 0.0.0.0 --port <PORT>
```

### Backend web de Produccion

```text
EDARSA_ENV=PRODUCTION
EDARSA_RUNTIME_ROLE=PRODUCTION_WEB
EDARSA_RUNTIME_ROLE_REQUIRED=1
```

El backend web no inicia APScheduler cuando tiene ese rol.

### Preview / Desarrollo

```text
EDARSA_ENV=PREVIEW
EDARSA_RUNTIME_ROLE=PREVIEW_WEB
EDARSA_RUNTIME_ROLE_REQUIRED=1
SCHEDULER_ENABLED=false
```

Preview no debe poseer el scheduler que escribe datos consumidos por
Produccion.

## Cutover seguro

1. Desplegar primero el nuevo servicio Scheduler desde una release aprobada de
   Produccion. No apagar Preview todavia.
2. Confirmar `/api/health` del Scheduler con `status=ok`,
   `environment=PRODUCTION`, `runtime_role=PRODUCTION_SCHEDULER` y jobs
   registrados.
3. Confirmar al menos dos ciclos consecutivos de
   `sync_comercial_abiertas_v2` (10 minutos) con datos nuevos.
4. Cambiar el backend web de Produccion a
   `EDARSA_RUNTIME_ROLE=PRODUCTION_WEB` y
   `EDARSA_RUNTIME_ROLE_REQUIRED=1`.
5. Cambiar Preview a `PREVIEW_WEB` y `SCHEDULER_ENABLED=false`.
6. Dormir/reiniciar Preview deliberadamente y verificar que las ventas del dia
   siguen avanzando en Produccion durante al menos dos ciclos.
7. Solo entonces declarar `PRODUCTION_SCHEDULER_DECOUPLED=CERTIFIED`.

## Rollback

Si el servicio standalone no queda sano, no se deben dejar dos propietarios.

1. Detener el servicio standalone.
2. Restaurar temporalmente el backend productivo a
   `EDARSA_RUNTIME_ROLE=LEGACY_EMBEDDED` o retirar
   `EDARSA_RUNTIME_ROLE_REQUIRED`.
3. Verificar dos ciclos del scheduler embebido.
4. Mantener Preview sin escrituras productivas.

## Proteccion del sincronizador del dia

La correccion no cambia
`backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py`.
Existe una prueba de contrato que fija el blob Git
`47e7e005cf3c382c546ffc017a28a5c6d87796bc`; cualquier cambio byte-a-byte
rompe el gate.
