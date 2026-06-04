# PLAN MIGRACIÓN NO-LIVE EDARSAHUB

## Regla principal

EDARSAHUB SQL es la única fuente de verdad.

SoftRestaurant, MPRO y futuros sistemas solo pueden usarse como origen de sincronización controlada.

---

## Único pendiente bloqueado

Solo queda pendiente:

```http
POST /api/admin/sync/compras?dry_run=true
POST /api/admin/sync/compras?dry_run=false
GET /api/admin/sync/compras/table-counts
GET /api/admin/sync/compras/logs
```

**Motivo:** Firewall de EDARSAHUB SQL bloquea IP del pod Emergent (`54.39.104.176`).

**Solución:** Ejecutar desde ambiente de producción (ver `/app/docs/PENDIENTE_DRY_RUN_SYNC_COMPRAS.md`).

---

## Avances completados en esta sesión

### 1. Auditoría de conexiones LIVE
- ✅ Identificadas **169 violaciones NO-LIVE** en `/app/docs/reports/VIOLACIONES_NO_LIVE_SOFT_MPRO_*.csv`
- ✅ Plan priorizado generado en `/app/docs/reports/PLAN_PRIORIZADO_SQL_FIRST_*.md`
- ✅ Endpoints P1 de Compras/Inventarios listados en `/app/docs/reports/P1_ENDPOINTS_COMPRAS_INVENTARIOS_SQL_FIRST_*.md`

### 2. Jobs de sincronización
- ✅ Fix aplicado a `sync_compras_job.py` (eliminado `signal.alarm()` que causaba error en threads)
- ✅ Verificado que el job conecta correctamente a 9 servidores
- ✅ Dry-run exitoso desde API externa (Emergent preview)

### 3. Endpoints administrativos creados
| Endpoint | Método | Estado |
|----------|--------|--------|
| `/api/admin/sync/compras` | POST | ✅ Funciona |
| `/api/admin/sync/compras/force-unlock` | POST | ✅ Creado |
| `/api/admin/sync/compras/table-counts` | GET | ✅ Creado (requiere acceso SQL) |
| `/api/admin/sync/compras/logs` | GET | ✅ Creado (requiere acceso SQL) |

### 4. Migración AUTH/RBAC MongoDB → SQL
- ✅ Usuario `admin@inventario.com` desactivado en MongoDB
- ✅ Colección `users` eliminada (backup en `users_legacy_backup_auth_rbac_20260604`)
- ✅ **CERO usuarios productivos activos en MongoDB**

### 5. Documentación oficial
- ✅ `/app/docs/ENDPOINTS_OFICIALES_SYNC_EDARSAHUB.md` - Rutas blindadas
- ✅ `/app/docs/PENDIENTE_DRY_RUN_SYNC_COMPRAS.md` - Instrucciones pendientes

---

## Tablas destino para arquitectura NO-LIVE

Estas tablas deben llenarse mediante jobs de sincronización:

| Tabla | Propósito | Estado |
|-------|-----------|--------|
| `Compras_Inventarios_Fisicos_Sync` | Inventarios físicos | ⚠️ Pendiente verificar |
| `Compras_Requisiciones_Sync` | Requisiciones | ⚠️ Pendiente verificar |
| `Compras_Pedidos` | Pedidos de compra | ⚠️ Pendiente verificar |
| `Compras_Ordenes` | Órdenes de compra | ⚠️ Pendiente verificar |
| `Compras_Recepciones` | Recepciones | ⚠️ Pendiente verificar |
| `Inventario_Almacenes` | Catálogo almacenes | ⚠️ Pendiente verificar |
| `Inventario_Existencias` | Existencias | ⚠️ Pendiente verificar |
| `Inventario_Movimientos` | Movimientos | ⚠️ Pendiente verificar |

---

## Siguiente fase: Refactorización de endpoints

Una vez que las tablas estén llenas, los endpoints P1 deben refactorizarse para leer de EDARSAHUB en lugar de conectar LIVE a SoftRestaurant/MPRO.

Archivos principales a modificar:
- `/app/backend/server.py` (98 violaciones)
- `/app/backend/modules/compras/repository.py` (8 violaciones)
- `/app/backend/modules/compras/service.py` (4 violaciones)
- `/app/backend/modules/finanzas/repository_softrestaurant.py` (3 violaciones)

---

## Fecha de actualización

2026-06-04
