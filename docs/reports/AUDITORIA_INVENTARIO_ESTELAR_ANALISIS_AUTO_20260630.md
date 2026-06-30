# Auditoria inventario La Estelar - analisis automatico

- Fecha de auditoria: 2026-06-30
- Unidad: LA ESTELAR
- ServerID: `a5ff0e25-f029-43db-b634-d4ac814c904f`
- Base auditada: EDARSAHUB SQL
- Modo: solo lectura para datos; cambios de codigo aplicados en detector.

## Resumen ejecutivo

El analisis automatico no se genero porque La Estelar no estaba entrando al detector de inventarios.

La causa raiz principal es una incompatibilidad de `system_type`: el registro activo de La Estelar en `Servidores_Conexiones` usa `SOFTRESTAURANT_PRO`, pero `InventariosDetectorJob` solo aceptaba `softrestaurant`, `sr` y `mpro`, y luego validaba exactamente `SoftRestaurant` antes de consultar `invfisico`.

Tambien se detecto un segundo riesgo: `backend/core/scheduler/sql_repository.py` entregaba `password_encrypted` como `password` sin descifrarlo. Si el servidor tiene secreto cifrado, el job no puede conectar al origen aunque pase el filtro de sistema.

## Evidencia SQL

### Servidor La Estelar

- `nombre`: LA ESTELAR
- `system_type`: `SOFTRESTAURANT_PRO`
- `activo`: true
- `database_name`: `softrestaurant12`
- `port`: 6969
- `host`, `username` y `password` configurados.
- El password esta en formato cifrado.

### Bitacora del job hoy

Tabla: `Scheduler_BitacoraJobs`

- Job: `inventarios_detector`
- Eventos del 2026-06-30: 1
- Accion registrada: `INICIO`
- Primer/ultimo evento: `2026-06-30 04:53:17.570`

No hay registros posteriores de folios detectados/procesados para La Estelar en `Scheduler_InventariosProcesados`.

### Inventarios sincronizados en EDARSAHUB

Tabla: `Compras_Inventarios_Fisicos_Sync`

- Total historico Estelar: 131 folios
- Fecha minima: `2025-12-08 12:30:37`
- Fecha maxima: `2026-06-01 15:28:27`
- Ultima sincronizacion: `2026-06-03 23:48:32.107`
- Inventarios con fecha `2026-06-30`: 0
- Almacenes historicos: 6

Tabla: `Compras_Inventarios_Fisicos_Detalle_Sync`

- Detalle Estelar con fecha `2026-06-30`: 0 filas

### Historico legacy migrado

Tabla: `Inventarios_ProcesadosAuto`

- Registros legacy de Estelar: 44
- Registros con error en payload: 41
- Registros con error relacionado a almacen: 44
- Patron recurrente: analisis fallido por almacen no encontrado.

Este historico no explica el fallo de hoy por si solo, pero confirma que el flujo automatico de Estelar ya venia fragil desde antes de la migracion.

## Cambios aplicados

1. `backend/core/scheduler/jobs/inventarios_detector_job.py`
   - Se agrego normalizacion de `system_type`.
   - `SOFTRESTAURANT_PRO`, `softrestaurantpro`, `SoftRestaurant` y `sr` ahora convergen a `SoftRestaurant`.
   - `MANAGEMENTPRO` y `MPRO` convergen a `MPRO`.
   - El filtro de servidores y la validacion interna de `_detectar_soft()` usan el tipo canonico.

2. `backend/core/scheduler/sql_repository.py`
   - Se agrego descifrado interno de `password_encrypted` antes de entregar configuracion a jobs.
   - Si el valor es legacy en texto plano, se conserva compatibilidad.
   - No se imprime ni se expone el secreto.

3. `backend/tests/test_inventarios_detector_system_types.py`
   - Regresion para confirmar que La Estelar con `SOFTRESTAURANT_PRO` entra al detector como `SoftRestaurant`.

## Validacion local

```text
PYTHONPATH="$PWD/backend" .venv_codex/bin/python -m py_compile \
  backend/core/scheduler/jobs/inventarios_detector_job.py \
  backend/core/scheduler/sql_repository.py

PYTHONPATH="$PWD/backend" .venv_codex/bin/python -m pytest \
  backend/tests/test_inventarios_detector_system_types.py -q

Resultado: 3 passed
```

## Pendientes operativos

1. Desplegar el fix en el entorno donde corre el scheduler.
2. Verificar que ese entorno tenga `SERVER_SECRET_KEY` cargado para poder descifrar credenciales de `Servidores_Conexiones`.
3. Ejecutar manualmente `inventarios_detector` filtrando La Estelar o esperar el siguiente ciclo.
4. Confirmar lectura directa a `invfisico` en origen para el inventario del 2026-06-30.
5. Si el folio ya existe en origen, validar que se cree registro en `Scheduler_InventariosProcesados` y que cambie a `COMPLETADO` o `ERROR` con detalle.

## Dictamen

El problema de hoy no esta en la pantalla del frontend. La automatizacion no tuvo insumo procesable porque La Estelar quedaba fuera del detector por `system_type` y, adicionalmente, el detector no estaba descifrando credenciales externas. Tras el fix, el siguiente paso es ejecutar el job en ambiente con secretos reales para confirmar el folio de hoy y generar/reintentar el analisis.
