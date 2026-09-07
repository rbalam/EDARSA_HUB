# BOS Direction Recurrent Status - Gate 5

## Objetivo
Preparar el status de Direccion para ejecucion recurrente conservando historico y un puntero `latest`, sin duplicar logica de calculo ni modificar infraestructura del Worker.

## Contrato de ciclo
Cada ejecucion recibe `results-dir`, `status-root` y `generated-at-utc`. El ciclo usa el collector y publisher certificados previamente.

## Salidas
- `status-root/history/YYYYMMDDTHHMMSSZ.json`: snapshot inmutable.
- `status-root/latest.json`: ultimo snapshot mediante reemplazo atomico.

## Idempotencia
Repetir el mismo timestamp y contenido no crea duplicados. Si el mismo timestamp existe con contenido diferente, falla cerrado con `HISTORY_COLLISION`.

## Seguridad
No instala cron, no cambia Supervisor, Worker o watchdog, no usa SQL/Mongo/red y no toca Production ni el Tablero Ejecutivo congelado.

## Concurrencia de intake
El job de implementacion puede omitir `base_sha` para que el dispatcher capture el HEAD canónico en pickup. Esto evita carreras de HEAD sin reducir las validaciones de alcance, checks o integración.

## Activacion recurrente
La recurrencia debe ser activada por un scheduler autorizado que invoque `backend/tools/run_bos_direction_status_cycle.py`. La activacion operacional se certifica en el siguiente gate.
