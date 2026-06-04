# MAPEO TIPO MOVIMIENTO SOFTRESTAURANT → EDARSAHUB

Archivo: /app/backend/modules/compras/sync_service.py
Backup: /app/backend/modules/compras/sync_service.py.backup_tipo_movimiento_20260604_093656

## Validación sintaxis
```text
OK py_compile
```

## Mapeo detectado
```text
49:TIPO_MOVIMIENTO_SR_TO_EDARSAHUB = {
51:    "EPC": 1,  # ENTRADA_COMPRA
52:    "SPC": 2,  # SALIDA_DEV_PROV
55:    "ETA": 5,  # TRASPASO_ENTRADA
56:    "STA": 6,  # TRASPASO_SALIDA
59:    "ECI": 3,  # AJUSTE_ENTRADA
60:    "SCI": 4,  # AJUSTE_SALIDA
74:def map_tipo_movimiento_softrestaurant(idconcepto, cantidad=None):
81:    if concepto in TIPO_MOVIMIENTO_SR_TO_EDARSAHUB:
82:        return TIPO_MOVIMIENTO_SR_TO_EDARSAHUB[concepto]
443:                        WHEN 1 THEN 'RECIBIDO'
469:                        WHEN 2 THEN 'RECIBIDO'
783:# ADVERTENCIA: sync_movimientos_from_server debe usar map_tipo_movimiento_softrestaurant() antes de MERGE.
```
