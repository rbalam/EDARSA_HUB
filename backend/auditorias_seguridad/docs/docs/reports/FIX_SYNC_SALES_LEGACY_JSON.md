# FIX Sync_Sales Legacy JSON

Fecha: 2026-06-02T22:52:00+00:00

## Archivo corregido
/app/backend/tools/sync_sales_dry_run.py

## Cambios aplicados (ya realizados manualmente)
- Se modificó get_softrestaurant_query() para devolver filas planas SIN FOR JSON PATH
- Se creó build_sales_from_flat_rows() que agrupa en Python con json.dumps()
- Se modificó get_mpro_query() con JOIN correcto y Vn_Tabla='Comanda'
- Se eliminó choices hardcodeados en argparse
- Se agregó soporte para sucursal_origen_id en MPRO

## Validación
- FOR_JSON_PATH_COUNT=0 (activo en SQL)
- PY_COMPILE_RESULT=OK
- DRY-RUN: CIENFUEGOS ✅, 130QRO ✅, ORIGEN ✅

## Regla
SoftRestaurant legacy no debe construir JSON en SQL.
Debe traer filas planas y construir items con json.dumps() en Python.

## Comandos de ejecución verificados
```bash
export SERVER_SECRET_KEY="4HGEDzNpIv3pMoHXFtlXXYiTSt1SxU8dXHiTR5GOtd8="
cd /app/backend
python tools/sync_sales_dry_run.py --unidad CIENFUEGOS --fecha-inicio 2026-06-01 --fecha-fin 2026-06-01 --dry-run
python tools/sync_sales_dry_run.py --unidad 130QRO --fecha-inicio 2026-06-01 --fecha-fin 2026-06-01 --dry-run
python tools/sync_sales_dry_run.py --unidad ORIGEN --fecha-inicio 2026-06-01 --fecha-fin 2026-06-01 --dry-run
```
