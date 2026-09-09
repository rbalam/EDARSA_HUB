# EDARSAHUB BOS — Gate 5C Runtime Adoption

Fecha: 2026-09-09
Rama: `Edarsahub_Desarrollo`
Produccion: **NO TOCADA**

## Resultado

Gate 5C conecta la infraestructura universal de Gate 4 con los flujos reales existentes sin crear tablas paralelas ni reemplazar registry, resolvers o RBAC.

### Health real

Se agrego `backend/modules/integrations_runtime/health.py` con un writer comun sobre `dbo.Servidores_ConexionEstado`.

- `activo` sigue siendo flag administrativo, no health.
- API_LOCAL persiste health solamente cuando la prueba esta asociada a `api_id`/ConexionID canonico.
- Las pruebas ad-hoc por URL no fabrican identidad ni persisten estado.
- CORE persiste el resultado de `POST /api/admin/core-connections/{server_id}/test`.
- Se reutilizan los campos legacy y UTC de `Servidores_ConexionEstado`; no se crea otra tabla.
- UPDATE sobre la fila existente o INSERT si no existe, con transaccion SERIALIZABLE.

### Ledger universal

Se agrego `backend/modules/integrations_runtime/sync_ledger.py`.

El helper comun completa de forma fail-closed:

- `ConexionID` solo si el UUID existe realmente en `Servidores_Conexiones`.
- `UnidadNegocioID` solo si existe realmente en `Unidades_Negocio`.
- `CodigoSync` solo si existe y esta activo en `Sistema_Sync_Catalogo`.
- `StartedAtUTC`.
- `FinishedAtUTC`.
- `IdempotencyKey` deterministico y acotado a 200 caracteres.

No se inventa contexto faltante.

### Writers migrados in-place

1. `sync_compras_job.py`
2. `detect_nuevos_compras_job.py`
3. `sync_historicos/repository.py`
4. `sync_recetas/sync_recetas.py`
5. `sync_comercial_abiertas_v2_job.py`

Se conserva `SyncType` legacy y el comportamiento operativo existente. Los runs agregados multi-servidor pueden conservar `ConexionID`/`UnidadNegocioID` NULL porque no representan una sola conexion o unidad.

### CodigoSync

El preflight READ_ONLY demostro que los `SyncType` legacy (`COMPRAS_SYNC`, `DETECT_NUEVOS`, `SYNC_RECETAS`, `VENTAS_DIA_ABIERTAS`, variantes historicas) no tienen todos una equivalencia 1:1 certificada en `Sistema_Sync_Catalogo`. Por maxima **Nunca adivinar**, Gate 5C no asigna codigos aproximados. `CodigoSync` queda NULL hasta una homologacion explicita posterior.

## Evidencia

### Preflight

Job `servers-integrations-gate5c-preflight-readonly-20260909`:

- `CERTIFIED_READ_ONLY`
- `PASS`
- 100%
- `HRLectura` / `EDARSAHUB`
- Production false

### Implementacion

- R1 `servers-integrations-gate5c-health-ledger-r1-20260909`: INTEGRATED, tests PASS, quality PASS.
- R2 `servers-integrations-gate5c-ledger-r2-20260909`: INTEGRATED, tests PASS, quality PASS.
- R3 `servers-integrations-gate5c-ledger-r3-timeout-utc-20260909`: INTEGRATED, tests PASS, quality PASS.

### Post-audit READ_ONLY

Job `servers-integrations-gate5c-postaudit-readonly-20260909`:

- `CERTIFIED_READ_ONLY`
- `PASS`
- 100%
- `files_changed=[]`
- Production false

Estado real observado inmediatamente despues del cableado:

- `Servidores_ConexionEstado`: 0 filas.
- `Sync_Control_Ejecuciones`: 4712 filas legacy.
- filas con `ConexionID`: 0.
- filas con `UnidadNegocioID`: 0.
- filas con `CodigoSync`: 0.
- filas con `StartedAtUTC`: 0.
- filas con `FinishedAtUTC`: 0.
- filas con `IdempotencyKey`: 0.
- duplicados de IdempotencyKey: 0.
- referencias invalidas ConexionID: 0.
- referencias invalidas UnidadNegocioID: 0.
- CodigoSync invalidos: 0.
- tablas `Toast_*`: 0.

Esto es **EXPECTED**: Gate 5C cablea los writers futuros; no hace backfill de historia ni ejecuta artificialmente jobs/test de conectividad para fabricar datos. La adopcion aparecera en nuevas ejecuciones reales.

## No realizado deliberadamente

- No backfill de 4712 runs legacy.
- No asignacion aproximada de `CodigoSync`.
- No ejecucion forzada de jobs de negocio.
- No test de conexiones externas artificial para llenar health.
- No DDL.
- No tablas nuevas.
- No RBAC paralelo.
- No `Toast_*`.
- No Produccion.

## Cierre

`GATE_5C_IMPLEMENTATION=100%`

`GATE_5C_POST_AUDIT=CERTIFIED_READ_ONLY/PASS`

`RUNTIME_DATA_ADOPTION=AWAITING_NEXT_REAL_EXECUTION`
