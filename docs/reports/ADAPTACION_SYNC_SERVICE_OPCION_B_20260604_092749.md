# ADAPTACIÓN SYNC_SERVICE.PY - OPCIÓN B

Fecha: Thu Jun  4 09:27:49 UTC 2026
Backup: /app/backend/modules/compras/sync_service.py.backup_opcion_b_20260604_092749

## Reglas Aplicadas
1. No usar ServerID en MERGE destino
2. No usar OrigenSistema en MERGE destino
3. Usar EmpresaID + SucursalID + Folio como llave encabezados
4. Usar ID encabezado + ProductoID como llave detalle

## Funciones Modificadas
- _get_edarsahub_context(): Helper para resolver EmpresaID/SucursalID
- sync_existencias_from_server(): Reescrita con MERGE correcto

## Validación Sintaxis
```text
OK py_compile
```

## PENDIENTE: Reescribir funciones restantes
- sync_almacenes_from_server
- sync_movimientos_from_server
- sync_pedidos_from_server
- sync_ordenes_from_server
- sync_recepciones_from_server
