# BOS Direction Status - Gate 6 Scheduler Activation

## Objetivo
Activar el status vivo de Direccion dentro del Scheduler central de EDARSAHUB. No se crea un cron, proceso, Worker, Supervisor o watchdog adicional.

## Job canónico
`bos_direction_status` ejecuta el ciclo certificado de Gate 5. El intervalo se controla con `SCHEDULER_BOS_DIRECTION_STATUS_INTERVAL_SECONDS` y por defecto es 3600 segundos. Puede desactivarse con `SCHEDULER_BOS_DIRECTION_STATUS_ENABLED=false`.

## Rutas
El job usa `EDARSAHUB_ROOT` como raíz. Se pueden sobreescribir `BOS_DIRECTION_RESULTS_DIR` y `BOS_DIRECTION_STATUS_ROOT`. Sin overrides, usa rutas runtime dentro de `.git`; no escribe artefactos en el árbol versionado.

## Gobierno operacional
- Un único Scheduler central APScheduler.
- `max_instances=1`.
- `coalesce=true`.
- Lock distribuido canónico `bos_direction_status`.
- Bitácora canónica mediante JobLogger.
- Excepciones fallan cerrado y quedan registradas.
- Production no se toca por este Gate.

## Evidencia de recurrencia
Las pruebas del Gate ejecutan APScheduler y requieren al menos tres ciclos automáticos consecutivos, cada uno generando histórico y actualizando `latest.json`.

## Siguiente Gate
Gate 7 debe certificar el E2E del informe ejecutivo diario: snapshot generado por scheduler, propuesta de informe, revisión/confirmación de gerente, ajustes auditados y preparación para distribución a Dirección por los canales autorizados.
