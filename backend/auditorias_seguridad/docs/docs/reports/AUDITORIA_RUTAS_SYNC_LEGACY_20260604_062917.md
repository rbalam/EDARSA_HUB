# AUDITORÍA RUTAS SYNC LEGACY
Fecha: Thu Jun  4 06:29:17 UTC 2026

## Rutas correctas e incorrectas encontradas
```text
/app/backend/server.py:741:@api_router.post("/admin/sync/compras")
/app/backend/server.py:775:@api_router.post("/admin/sync/compras/force-unlock")
/app/backend/server.py:847:@api_router.get("/admin/sync/compras/table-counts")
/app/backend/server.py:914:@api_router.get("/admin/sync/compras/logs")
/app/docs/PENDIENTE_DRY_RUN_SYNC_COMPRAS.md:8:POST /api/admin/sync/compras?dry_run=true
/app/docs/PENDIENTE_DRY_RUN_SYNC_COMPRAS.md:14:GET /api/admin/sync/compras/table-counts
/app/docs/PENDIENTE_DRY_RUN_SYNC_COMPRAS.md:15:GET /api/admin/sync/compras/logs?limit=50
/app/docs/PENDIENTE_DRY_RUN_SYNC_COMPRAS.md:38:curl -s -X POST "http://localhost:8001/api/admin/sync/compras?dry_run=true" \
/app/docs/PENDIENTE_DRY_RUN_SYNC_COMPRAS.md:43:curl -s "http://localhost:8001/api/admin/sync/compras/table-counts" \
/app/docs/PENDIENTE_DRY_RUN_SYNC_COMPRAS.md:48:curl -s "http://localhost:8001/api/admin/sync/compras/logs?limit=50" \
/app/docs/PENDIENTE_DRY_RUN_SYNC_COMPRAS.md:76:curl -s -X POST "http://localhost:8001/api/admin/sync/compras?dry_run=false" \
/app/docs/reports/AUDITORIA_CONEXIONES_LIVE_20260604_042605.md:272:741:@api_router.post("/admin/sync/compras")
/app/docs/reports/AUDITORIA_RUTAS_SYNC_COMPRAS_20260604_060721.md:6:741:@api_router.post("/admin/sync/compras")
/app/docs/reports/AUDITORIA_RUTAS_SYNC_COMPRAS_20260604_060721.md:7:775:@api_router.post("/admin/sync/compras/force-unlock")
/app/docs/reports/AUDITORIA_RUTAS_SYNC_COMPRAS_20260604_060721.md:56:741:@api_router.post("/admin/sync/compras")
/app/docs/reports/AUDITORIA_RUTAS_SYNC_COMPRAS_20260604_060721.md:57:775:@api_router.post("/admin/sync/compras/force-unlock")
/app/docs/ENDPOINTS_OFICIALES_SYNC_EDARSAHUB.md:7:POST /api/admin/sync/compras?dry_run=true
/app/docs/ENDPOINTS_OFICIALES_SYNC_EDARSAHUB.md:8:POST /api/admin/sync/compras?dry_run=false
/app/docs/ENDPOINTS_OFICIALES_SYNC_EDARSAHUB.md:12:POST /api/admin/sync/compras/force-unlock
/app/docs/ENDPOINTS_OFICIALES_SYNC_EDARSAHUB.md:18:POST /api/admin/sync-compras
/app/docs/ENDPOINTS_OFICIALES_SYNC_EDARSAHUB.md:19:POST /api/admin/sync_compras
/app/docs/ENDPOINTS_OFICIALES_SYNC_EDARSAHUB.md:20:POST /api/admin/compras/sync
/app/docs/PLAN_MIGRACION_NO_LIVE_EXCEPTO_SYNC_COMPRAS.md:11:POST /api/admin/sync/compras?dry_run=true
/app/docs/PLAN_MIGRACION_NO_LIVE_EXCEPTO_SYNC_COMPRAS.md:12:POST /api/admin/sync/compras?dry_run=false
```
