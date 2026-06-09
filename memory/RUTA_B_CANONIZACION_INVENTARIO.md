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

## 7. Avance 2026-06-09 (sesión 2) — Código aprobado (sin POS)
- 🔌 **Conectividad POS (evidencia definitiva):** sonda `SELECT 1` vía helper canónico → **SIN_CONEXION en las 5 unidades**. El "conectividad SI" previo era falso positivo (`execute_sql_query` retorna `[]` en error y en tabla vacía). Diagnóstico endurecido con sonda real. **El run de movimientos debe hacerse en red productiva.**
- ✅ **Sub-fase B (código, DB-driven):** `resolver_tipo_movimiento_desde_concepto(system_type, concepto)` en `resolver_canonico.py` (cero hardcode; si catálogo ausente→PENDIENTE). DDL+seed propuestos en `migrations/PROPUESTA_concepto_mapeo_origen.sql` (**NO ejecutado**, pendiente aprobación).
- ✅ **4a (código):** `core/inventarios/sync_movimientos_canonico.py` — lee POS y escribe `Inventario_Movimientos`+`Detalle` en **esquema real**, usando los 4 resolvers; no resueltos→pendientes (sucursal/tipo/almacén/producto), **descartados=0**, idempotente (NOT EXISTS). `modules/compras/sync_service.sync_movimientos_from_server` ahora **delega** en esta capa común (bug del MERGE eliminado).
- ✅ **Validación de esquema (rollback):** `migrations/validar_esquema_sync_movimientos.py` inserta encabezado+detalle con IDs reales y hace ROLLBACK → 0 errores de columna/FK, 0 filas persistidas. (`Importe` es columna calculada → excluida del INSERT.)
- ✅ Imports sin circular (lazy import). Tests resolver **8/8**. Backend sano.

### Avance 2026-06-09 (sesión 3) — Resolver empresa/sucursal canónico (sin POS)
- ✅ `resolver_empresa_id(unidad_codigo)` vía `Sistema_Empresas.CodigoEmpresa` (1:1). **EmpresaID 5/5**.
- ✅ `resolver_sucursal_id` revisado (deriva de tablas canónicas). **SucursalID 3/5** auto (130MID→5, CIENFUEGOS→3, ESTELAR→4). MPRO (ORIGEN, 130QRO) → AMBIGUO.
- ✅ `sync_movimientos_canonico` usa `resolver_empresa_id`. Tests **12/12**.
- 🔴 Pendiente decisión: `SucursalID`(RH) de ORIGEN/130QRO. `Sistema_SucursalServidorMapeo` del server MPRO compartido tiene SucursalID 1,2 ('130 QUERETARO','130 TULUM') que NO son las unidades reales (ORIGEN=RH 7).

### Avance 2026-06-09 (sesión 4) — Sucursal/Empresa 5/5 + decisión catálogos
- 🔎 **Raíz:** existen 2 catálogos de sucursal: `Sistema_Sucursales` (LIMPIO, 1:1 con unidades + EmpresaID; FK del mapeo) vs `RH_Cat_Sucursales` (RRHH, desalineado; FK de `Inventario_Movimientos`).
- ✅ **UPDATE MPRO PERSISTIDO** (autorizado, additive): `Sistema_SucursalServidorMapeo` server MPRO → SucursalOrigenID ORIGEN(SucursalID 1)='0023', 130QRO(SucursalID 2)='0021'. Validado: 2 filas, global 5→5, ServerID intacto, acceso sin cambio (seguridad filtra por EmpresaID, no SucursalOrigenID). Script: `migrations/aplicar_sucursalorigen_mpro.py`.
- ✅ **Resolución 5/5** (Sistema_Sucursales): ORIGEN=1, 130QRO=2, CIENFUEGOS=3, ESTELAR=4, 130MID=5. EmpresaID 5/5. Tests **13/13**.
- 🟡 **DDL propuesto (NO ejecutado, decisión 🅐 aprobada):** re-apuntar `FK_Inventario_Movimientos_Sucursal` de `RH_Cat_Sucursales` → `Sistema_Sucursales` (`migrations/PROPUESTA_repuntar_fk_sucursal_sistema_sucursales.sql`, con rollback). Tablas vacías → bajo riesgo. **Pendiente tu OK para ejecutar.**
- 🔴 **Almacenes** (`Inventario_Almacenes`): siguen sin poblar por unidad (39 filas mis-atribuidas a Emp5/Suc1). Fuente canónica por confirmar (¿POS en prod o tabla canónica?).

### Avance 2026-06-09 (sesión 5) — FK re-apuntado + almacén sync corregido
- ✅ **DDL EJECUTADO Y VALIDADO:** `FK_Inventario_Movimientos_Sucursal` re-apuntado `RH_Cat_Sucursales` → `Sistema_Sucursales` (pre-check 0 violaciones, transacción, commit, validado). Script: `migrations/ejecutar_repuntar_fk_sucursal.py`. Rollback en `migrations/PROPUESTA_repuntar_fk_sucursal_sistema_sucursales.sql`.
- ✅ **`sync_almacenes_from_server` corregido:** usa `resolver_empresa_id`+`resolver_sucursal_id` (empresa/sucursal canónicos alineados); elimina el fallback legacy empresa=1/sucursal=1 que mis-atribuía. No resuelto → PENDIENTE.
- ✅ **Almacenes: fuente = POS** (no hay catálogo canónico alterno; `Inventario_Almacenes` se puebla desde origen vía el sync corregido en prod). 13/13 tests, backend sano.
- 🎯 **Cadena canónica COMPLETA en código:** producto + empresa(5/5) + sucursal(5/5) + tipo + concepto resueltos en EDARSAHUB. Solo resta el run en PROD (POS): sync almacenes → sync movimientos 4a → endpoint NO-LIVE 4b.

### Pendiente (gates)
- ✅ DDL+seed `Inventario_ConceptoMapeoOrigen` EJECUTADO (12 conceptos SR, FK ok, idempotente, resolver EPC→1). Tests **10/10**.
- **PROD (equipo):** correr `scripts/diag_origen_almacenes_sucursal_safe.py` (Paso 3) → poblar almacenes/SucursalOrigenID → correr sync 4a (`sync_compras_job`/`sync_movimientos_canonico`) → activar endpoint NO-LIVE (4b, diferido por el usuario hasta el sync productivo para no mostrar vacío).
- Conceptos MPRO (`Mo_Tipo`) NO sembrados (sin evidencia de origen) → quedan PENDIENTE hasta validar en prod (descartados=0).
