# ENDPOINTS OFICIALES DE SINCRONIZACIÓN EDARSAHUB

## Regla obligatoria

EDARSAHUB SQL es la única fuente de verdad para pantallas, reportes, auditorías, dashboards y exportaciones.

SoftRestaurant, MPRO y futuros sistemas operativos solo pueden ser origen de sincronización controlada.

---

## Sync Compras / Inventarios

### Endpoint oficial actual

```http
POST /api/admin/sync/compras?dry_run=true
POST /api/admin/sync/compras?dry_run=false
```

### Force unlock oficial

```http
POST /api/admin/sync/compras/force-unlock
```

### Rutas prohibidas / legacy

No usar:

```
POST /api/admin/sync-compras
POST /api/admin/sync_compras
POST /api/admin/compras/sync
```

Si alguna documentación, script, prueba o prompt usa esas rutas, debe corregirse a:
`/api/admin/sync/compras`

---

## Sync Ventas (Sales)

### Endpoint oficial

```http
POST /api/admin/sync/sales?dry_run=true
POST /api/admin/sync/sales?dry_run=false
POST /api/admin/sync/sales/backfill?days=7&dry_run=true
```

---

## Sync Comercial Abiertas

```http
POST /api/admin/sync/comercial-abiertas?dry_run=true
POST /api/admin/sync/comercial-abiertas?dry_run=false
```

---

## Scheduler / Jobs

```http
GET /api/admin/scheduler/status
POST /api/admin/scheduler/trigger/{job_name}
```

---

## Filtros Corporativos (SQL-FIRST)

```http
GET /api/corporate-filters/bootstrap?scope=compras.dashboard
GET /api/corporate-filters/bootstrap?scope=inventarios.dashboard
```

---

## Fecha de blindaje

Este documento fue generado automáticamente.
Fecha: $(date)

