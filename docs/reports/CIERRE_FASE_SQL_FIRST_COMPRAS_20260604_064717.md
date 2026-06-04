# CIERRE DE FASE - SQL-FIRST COMPRAS / INVENTARIOS

## Estado general

Se preparó la migración SQL-First para Compras e Inventarios sin afectar producción.

## Regla principal

EDARSAHUB SQL es la única fuente de verdad.

SoftRestaurant, MPRO y futuros sistemas operativos solo pueden usarse como origen de sincronización controlada.

## Endpoints SQL-First creados

- GET /api/compras/inventarios-fisicos-sql-first/{server_id}
- GET /api/compras/pedidos-vigentes-sql-first/{server_id}
- POST /api/compras/productos-para-captura-sql-first
- POST /api/compras/detalle-movimientos-sql-first
- GET /api/compras/facturas-proveedor-sql-first/{server_id}
- GET /api/compras/detalle-factura-sql-first/{server_id}/{folio}
- POST /api/compras/detalle-consumos-sql-first
- GET /api/compras/dashboard-sql-first/{server_id}

## Seguridad operativa

- Endpoints originales no fueron reemplazados.
- Endpoints nuevos quedan detrás de COMPRAS_SQL_FIRST_ENABLED=false.
- No hay fallback LIVE.
- No se ejecutó sync real de compras.
- No se activó lectura SQL-First en producción.

## Validación NO-LIVE

Resultado:

OK: Endpoints SQL-First sin conexión LIVE.

No hay código ejecutable con:

- server['host']
- execute_sql_query
- get_server_by_id
- conexión directa a SoftRestaurant
- conexión directa a MPRO

## Pendiente específico

Queda pendiente únicamente Sync Compras:

- POST /api/admin/sync/compras?dry_run=true
- POST /api/admin/sync/compras?dry_run=false

No ejecutar dry_run=false hasta validar:

- /api/admin/sync/compras/table-counts
- /api/admin/sync/compras/logs
- resultado completo de dry_run=true
- autorización explícita del usuario

## Próximo paso

Cuando Sync Compras tenga datos validados en EDARSAHUB SQL:

1. Activar COMPRAS_SQL_FIRST_ENABLED=true en ambiente controlado.
2. Probar endpoints SQL-First paralelos.
3. Comparar resultados contra endpoints originales.
4. Reemplazar endpoints originales gradualmente.
5. Eliminar conexiones LIVE de pantallas operativas.
