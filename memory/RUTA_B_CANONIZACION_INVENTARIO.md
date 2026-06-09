# RUTA B — Canonización Inventario (int estricta): Cimientos + Cobertura

**Fecha:** 2026-06-09
**Decisión usuario:** Ruta B (int estricta) · resolver centralizado · paso a paso (proponer→autorizar→ejecutar→validar→reportar) · cero DDL/DML sin autorización.

## 1. Auditoría MongoDB (6 puntos) — RESUELTO
- `[COMPRAS_REPO] STUB` = log informativo (`modules/compras/repository.py:90`). Bajado a `debug` (cosmético).
- **No hay conexión real a Mongo**: `core/sql_first/no_mongo.py` bloquea (`MongoDisabledError`) y `core/mongo_stub.py` es no-op. No afecta flujo productivo.
- Helper canónico POS: `core/server_registry.py` (`get_server_connection_info`, `get_server_connection_info_with_secrets`, `get_server_by_unidad_codigo`) + `core/connection_resolver.py`.
- Sunset Mongo definitivo = tarea P2 dedicada.

## 2. Causa raíz tablas de movimientos vacías
`sync_movimientos_from_server` insertaba columnas inexistentes (`ProductoID/Cantidad/CostoUnitario/CostoTotal`) en `Inventario_Movimientos` → "Invalid column" → 0 filas. (Pendiente de corregir tras canonización.)

## 3. CISMA CANÓNICO (bloqueante)
- Catálogo vivo = `Sync_Productos` (12,460) / `Sync_Productos_Insumos` (11,735), **GUID**, keyed por `ServerID`+`CodigoFuente`.
- Modelo de movimientos exige **int**: `Inventario_MovimientosDetalle.ProductoID → Producto_Catalogo.ProductoID` (**0 filas**, master de 17 tablas de detalle del ERP).
- `Inventario_Almacenes`: 39 filas solo `SucursalID=1` (0 para las 5 unidades activas).
- `Sistema_SucursalServidorMapeo.SucursalOrigenID` = NULL (MPRO ORIGEN/130QRO ambiguo; pero `Unidades_Negocio.sucursal_origen_id` ya tiene '0023'/'0021' como evidencia).
- **Probado**: ninguna tabla puente POS→ProductoID(int) existe (`scripts/diag_prueba_no_puente_safe.py`).

## 4. Cimientos entregados (cero escritura)
- `core/inventarios/resolver_canonico.py` — resolver centralizado (solo lectura; interfaz por unidad/sistema/código; nunca inventa IDs).
- `core/inventarios/canonizacion_productos_service.py` — canonización BLOQUEADA en escritura; calcula cobertura dry-run.
- `tests/test_resolver_canonico.py` — **7/7 PASS**.
- `migrations/PROPUESTA_puente_producto_mapeoorigen.sql` — DDL + rollback (PK/FK/UNIQUE/índice) **propuesto, NO ejecutado**.
- `scripts/diag_origen_almacenes_sucursal_safe.py` — diagnóstico de origen READ-ONLY validado (py_compile + AST + sin escrituras), conforme a 10 condiciones; **listo para correr en red con acceso POS**.

## 5. Cobertura dry-run por unidad
| Unidad | Sist | Insumos | Canonizables | Almacenes canón. | Sucursal |
|---|---|---|---|---|---|
| 130MID | SR | 2,629 | 2,629 | 0 ❌ | ID=5 ✅ |
| CIENFUEGOS | SR | 2,493 | 2,493 | 0 ❌ | ID=3 ✅ |
| ESTELAR | SR | 1,199 | 1,199 | 0 ❌ | ID=4 ✅ |
| 130QRO | MPRO | 5,414 | 5,414 | 0 ❌ | AMBIGUO ❌ |
| ORIGEN | MPRO | 5,414 | 5,414 | 0 ❌ | AMBIGUO ❌ |
`Producto_Catalogo`=0 · tipos=6 · descartados=0.

## 6. Estado de pasos (cadencia: proponer→autorizar→ejecutar→validar→reportar)
- ✅ **PASO 1 (DDL) HECHO (2026-06-09):** `Producto_MapeoOrigen` creada (PK, UQ(ServerID,SystemType,CodigoFuente), IX_PMO_Producto, FK→Producto_Catalogo). 0 filas. Script: `migrations/ejecutar_ddl_producto_mapeoorigen.py`.
- ✅ **PASO 2 (DML) HECHO (2026-06-09):** Canonización insumos → `Producto_Catalogo` 0→**11,735** + puente 0→**11,735**. SKU=GUID(InsumoID), CodigoProducto='INS-#######'. descartados=0, FK huérfanos=0, dups=0. **Idempotente** (re-run +0). Script: `migrations/ejecutar_dml_canonizacion_insumos.py`. Resolver operativo (test A100025→ProductoID=5). Tests: **8/8 PASS**.
  - Reparto puente: 1b230a06/MPRO=5414, a5547321/SR=2629, 6d053c22/SR=2493, a5ff0e25/SR=1199.
- ⏳ **PASO 3 (DATA, requiere POS):** completar `Inventario_Almacenes` + `SucursalOrigenID` MPRO **desde origen**. Diagnóstico listo: `scripts/diag_origen_almacenes_sucursal_safe.py` (correr en red productiva).
- ⏳ **PASO 4:** corregir `sync_movimientos_from_server` (header+detalle, esquema real, usar resolver) + migrar endpoint `detalle-movimientos` a NO-LIVE. Código factible aquí; datos dependen de Paso 3 (POS).
