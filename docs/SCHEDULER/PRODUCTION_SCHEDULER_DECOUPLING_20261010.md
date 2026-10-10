# P0 - Desacoplamiento del Scheduler Productivo de Emergent Preview

## Objetivo

Eliminar la dependencia operativa de Produccion respecto del Preview/IDE de
Emergent sin modificar la logica ni el archivo protegido
`sync_comercial_abiertas_v2_job.py`.

Este hotfix parte de `Edarsahub_Produccion` y no incorpora el historial de
commits de Desarrollo.

## Arquitectura objetivo

```text
POS / APIs
    |
    v
Production Scheduler Service (always-on)
    |
    v
EDARSAHUB SQL
    |
    v
Production Web
```

Emergent Preview queda fuera del camino de escritura productivo.

## Runtime del Scheduler de Produccion

```text
EDARSA_ENV=PRODUCTION
EDARSA_RUNTIME_ROLE=PRODUCTION_SCHEDULER
EDARSA_RUNTIME_ROLE_REQUIRED=1
SCHEDULER_ENABLED=true
SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED=true
```

Con working directory `/app/backend`:

```text
uvicorn scheduler_service:app --host 0.0.0.0 --port <PORT>
```

## Backend web de Produccion

```text
EDARSA_ENV=PRODUCTION
EDARSA_RUNTIME_ROLE=PRODUCTION_WEB
EDARSA_RUNTIME_ROLE_REQUIRED=1
```

Con ese rol el backend web no inicia APScheduler.

## Preview

```text
EDARSA_ENV=PREVIEW
EDARSA_RUNTIME_ROLE=PREVIEW_WEB
EDARSA_RUNTIME_ROLE_REQUIRED=1
SCHEDULER_ENABLED=false
```

## Cutover

1. Preparar el servicio standalone desde este hotfix.
2. Configurar el runtime de Produccion con las variables anteriores.
3. Cambiar el backend web productivo a `PRODUCTION_WEB` en la misma ventana
   de cutover para evitar doble ownership.
4. Verificar `/api/health` del servicio standalone.
5. Confirmar dos ciclos consecutivos del sincronizador de ventas del dia.
6. Poner Preview en `PREVIEW_WEB` con scheduler apagado.
7. Dormir/reiniciar Preview y verificar dos ciclos adicionales en Produccion.
8. Declarar `PRODUCTION_SCHEDULER_DECOUPLED=CERTIFIED` solo con esa evidencia.

## Rollback

Si el scheduler standalone no queda sano:

1. Detener el standalone.
2. Restaurar el backend productivo a `LEGACY_EMBEDDED` o retirar temporalmente
   `EDARSA_RUNTIME_ROLE_REQUIRED`.
3. Verificar dos ciclos del scheduler embebido.
4. No habilitar Preview como escritor productivo.

## Proteccion del sincronizador del dia

El archivo productivo protegido conserva el blob Git:

`e97b55a06b0adb5b447904c7643b99844f00aae7`

Existe una prueba de contrato que falla si cambia un solo byte.
