# P1 ENDPOINTS A MIGRAR A SQL-FIRST

## Estado

No activar reemplazo todavía hasta validar datos sincronizados.

## Endpoints P1

1. POST /api/compras/productos-para-captura
2. POST /api/compras/detalle-movimientos
3. POST /api/compras/detalle-consumos
4. GET /api/compras/inventarios-fisicos/{server_id}
5. GET /api/compras/pedidos-vigentes/{server_id}
6. GET /api/compras/facturas-proveedor/{server_id}

## Regla

Estos endpoints deberán leer EDARSAHUB SQL.

Queda prohibido que usen:
- server['host']
- server['database']
- execute_sql_query contra POS
- conexión directa SoftRestaurant/MPRO

## Bloqueo

No activar reemplazo hasta que las tablas destino tengan datos validados.
