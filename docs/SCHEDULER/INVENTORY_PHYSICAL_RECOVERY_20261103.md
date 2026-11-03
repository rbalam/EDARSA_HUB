# Incidente P0: inventarios físicos no visibles (30-oct / 01-nov / 02-nov 2026)

## Estado y evidencia, 03-nov-2026

- `Production Inventory Sync Trigger`: los 19 runs programados inspeccionados
  entre 30-oct y 03-nov fallaron en el health check con
  `INVENTORY_SCHEDULER_TRIGGER_DISABLED`, antes de ejecutar `sync_compras`.
- `Inventory SoftRestaurant Clock`: los runs con `SUCCESS` tienen
  `results.inventarios=[]`. Su configuración explícita
  `SYNC_COMPRAS_SCOPE=INVENTORY_MOVEMENTS` y
  `SYNC_COMPRAS_SYSTEM_FILTER=SOFT` excluye inventarios físicos y MPRO.
- El 02/03-nov se observaron cancelaciones durante sincronizaciones de
  movimientos. Este cambio evita que un nuevo run programado cancele al
  anterior y extiende el timeout a 90 minutos **solo en ese clock**.
- Evidencia: runs 41124893745, 41517099506, 41615290119,
  41249873618 y 41348825530.

## Propietario canónico y prohibiciones

1. **No modificar** `sync_comercial_abiertas_v2`,
   `sync_comercial_v2`, sus workflows, endpoints de tickets, Tablero
   Comercial, Tablero Ejecutivo ni Inteligencia Comercial.
2. El propietario de inventarios físicos es `sync_compras` en modo
   `FULL` y usa `modules.compras.sync_service.sync_inventarios_fisicos_from_server`.
   Los datos se publican en `dbo.Compras_Inventarios_Fisicos_Sync` y
   `dbo.Compras_Inventarios_Fisicos_Detalle_Sync`.
3. No iniciar un segundo Scheduler ni cambiar el scope del clock
   `inventory-softrestaurant-clock.yml` a FULL: compite por el mismo
   lock/datos y excluye MPRO.
4. Los tableros son NO-LIVE: solo consultas al SQL EDARSAHUB canónico.
5. Cualquier cambio productivo de runtime o credenciales requiere
   autorización operativa y comprobación de ownership; NO lo realiza
   este PR.

## Recuperación operativa segura (solo por operador autorizado)

### Gate A: identificar el único dueño runtime

- Comprobar el estado real de `scheduler_service:app` con rol
  `PRODUCTION_SCHEDULER`, y el registro/pausa de `sync_compras`
  mediante APScheduler, `dbo.Sys_Scheduler_RuntimeState` y
  `dbo.Sync_Control_Ejecuciones`.
- Comprobar que no hay una corrida activa ni lock vigente; conservar
  `max_instances=1` y el lock SQL existente.
- Si el servicio standalone ya ejecuta `sync_compras` FULL correctamente,
  **NO** habilitar un disparador alternativo en `PRODUCTION_WEB`.
  En ese caso, deshabilitar el workflow de disparo redundante mediante
  el control operativo autorizado, no crear otro owner.
- Si el despliegue aprobado usa el disparador HTTP productivo existente
  como único owner, verificar en `PRODUCTION_WEB`:
  `EDARSA_INVENTORY_SCHEDULER_TRIGGER_ENABLED=true`,
  `SCHEDULER_SYNC_COMPRAS_ENABLED=true`,
  `SCHEDULER_SYNC_COMPRAS_EXECUTION_ENABLED=true`,
  el secreto servidor `EDARSA_SCHEDULER_TRIGGER_KEY` y su correspondencia
  con `EDARSA_PROD_SCHEDULER_TRIGGER_KEY` de GitHub.
  Nunca mostrar ni copiar secretos a los logs.
- Verificar el estado `GET /api/internal/inventory-scheduler-trigger/health`
  por la vía autenticada ya existente: HTTP 200, `status=ready`,
  `PRODUCTION`, `PRODUCTION_WEB`, `trigger_enabled=true`,
  `job_enabled=true`, `execution_enabled=true`. No omitir estos gates.

### Gate B: correr el mecanismo existente

- Usar SOLO la ejecución programada/autorizada de `sync_compras` FULL,
  con el writer SQL canónico y los adaptadores SR/MPRO existentes.
- Rechazar `DISABLED`, `WARNING`, `ERROR`, `FAILED`,
  `SKIPPED_LOCKED` y respuestas parciales; `SUCCESS` del clock de
  movimientos NO acredita inventarios físicos.
- La recuperación por unidad usa el handler existente
  `backend/tools/resync_inventarios_fisicos.py`, pero la ruta manual
  `--all --execute` está sujeta a autorización y a exclusión mutua
  del job productivo; no ejecutar concurrentemente ni indiscriminadamente.
  No afirmar que `/resync/execute` aplica exactamente un rango de fechas
  mientras su handler no lo pase al sincronizador subyacente.

### Gate C: certificar SQL y vista por unidad

- Mediante `HRLectura`, comparar los encabezados capturados en POS
  el 30-oct, 01-nov y 02-nov de **cada unidad configurada** con
  `Compras_Inventarios_Fisicos_Sync`, y sus detalles en
  `Compras_Inventarios_Fisicos_Detalle_Sync`.
- Comparar por unidad, sistema, servidor, sucursal MPRO canónica,
  almacén, fecha y folio. Respetar fecha operativa local, estado
  `ACTIVE`/`REPLACED`, deduplicación canónica y totales por producto.
- Aceptación: 100% de documentos físicos reales, sin faltantes de detalle,
  duplicaciones o cambio de identidad; usuario autorizado puede elegir
  los tres días en los selectores Inicial/Final del Tablero Operativo.
- Si un POS no tiene inventarios capturados esos días, registrar
  `NO_SOURCE_INVENTORY` y NO inventar un documento.
- Registrar evidencia en los mecanismos existentes de
  `Compras_Sync_Log` / `Sync_Control_Ejecuciones`; cero cambios a
  sincronizadores comerciales.

## Rollback

- Cambios de clock: revertir este PR; no cambia SQL ni infraestructura.
- Operación: revertir solo la configuración de inventory trigger al valor
  previo *si se habilitó expresamente* y deja de cumplir los gates;
  no revertir ni pausar servicios comerciales.
- Datos: snapshots físicos son atómicos; no editar directamente filas
  `ACTIVE`/`REPLACED` ni inventar transacciones compensatorias.

## Certificación

La corrección del clock de movimientos es **código preparado**, no
`PRODUCTION_INTEGRATED` ni `CERTIFIED`. La recuperación de inventarios
solo puede declararse `CERTIFIED` después del Gate C con evidencias SQL
de todas las sucursales, y de confirmar el único owner productivo.
