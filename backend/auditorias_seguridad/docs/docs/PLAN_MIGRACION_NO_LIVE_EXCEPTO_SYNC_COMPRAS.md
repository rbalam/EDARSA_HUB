# PLAN MIGRACIÓN NO-LIVE EDARSAHUB

EDARSAHUB SQL es la única fuente de verdad.

SoftRestaurant, MPRO y futuros sistemas solo pueden usarse como origen de sincronización controlada.

## Único pendiente bloqueado

Solo queda pendiente Sync Compras:

POST /api/admin/sync/compras?dry_run=true
POST /api/admin/sync/compras?dry_run=false

No ejecutar dry_run=false de compras hasta autorización explícita.

## No bloquear

No bloquear otros dry-run o sincronizaciones ya funcionales:

/api/admin/sync/sales
/api/admin/sync/comercial-abiertas
/api/corporate-filters/bootstrap

## Prohibido

- Aumentar timeout como solución final
- Usar TOP 500 como solución final
- Consultar server['host'] desde pantallas
- Consultar SoftRestaurant/MPRO live desde reportes
- Crear tablas duplicadas

## Permitido

- Crear repositorios SQL-First
- Crear endpoints paralelos EDARSAHUB SQL
- Mantener Soft/MPRO solo en jobs sync
- Usar feature flag para activar lectura EDARSAHUB SQL cuando haya datos
