# AUDITORÍA P1 — ENDPOINTS VISUALES NO-LIVE

Fecha: 2026-06-04  
Proyecto: EDARSAHUB  
Criterio: Los endpoints visuales no deben consultar servidores operativos LIVE. Solo EDARSAHUB SQL.

## Resultado Ejecutivo

| Módulo | Estado | Observación |
|---|---|---|
| comercial | CUMPLE | Modal Detalle de Ventas y Precios Constantes migrados a SQL-first |
| costos_margenes | CUMPLE | Repository SQL-first contra EDARSAHUB |
| compras | CUMPLE | Endpoints LIVE comentados/desactivados; funciones LIVE no expuestas |
| reportes | CUMPLE | Sin conexiones LIVE detectadas |
| explorador_bd | CUMPLE | Sin conexiones LIVE detectadas |
| inventarios | CUMPLE | Sin conexiones LIVE detectadas |
| operaciones | CUMPLE | Sin conexiones LIVE detectadas |

## Comercial

### Modal Detalle de Ventas
Endpoint:
`/comercial/detalle-movimientos/{server_id}`

Estado:
SQL-first usando `Comercial_KPIs_Diarios_v2`.

Nota:
Cerrado como detalle agregado diario. Queda pendiente futuro si se requiere detalle real por ticket/cheque individual.

### Precios Constantes
Endpoint:
`/comercial/precios-constantes/{server_id}`

Estado:
SQL-first usando `Sync_Precios_Historicos`.

Tabla poblada:
5,642 registros.

Distribución:
- ManagmentPro: 1,925
- 130° MÉRIDA: 1,719
- CIENFUEGOS: 1,507
- LA ESTELAR: 491

## Costos y Márgenes

Archivos auditados:
- `backend/modules/comercial/costos_margenes/repository.py`
- `backend/modules/comercial/costos_margenes/repository_precios.py`
- `backend/modules/comercial/costos_margenes/routes.py`

Estado:
SQL-first. Sin conexiones LIVE directas en endpoints visuales.

## Compras

Archivo con funciones LIVE:
`backend/modules/compras/repository.py`

Funciones detectadas:
- `validate_table_exists`
- `query_inventarios_fisicos_mpro`
- `query_inventarios_fisicos_sr`
- `query_pedidos_vigentes_mpro`
- `query_pedidos_vigentes_sr`
- `query_detalle_pedido_mpro`
- `query_detalle_factura_mpro`
- `query_facturas_proveedor_mpro`

Estado:
No expuestas en endpoints visuales activos. Endpoints LIVE de `compras/routes.py` están comentados/desactivados.

Endpoints activos de automatización de compras usan datos sincronizados en EDARSAHUB SQL.

## Jobs de sincronización

Archivos con LIVE permitidos:
- `backend/modules/comercial/queries/mpro.py`
- `backend/modules/comercial/queries/softrestaurant.py`
- `backend/modules/compras/sync_service.py`

Clasificación:
Permitidos cuando operan como jobs de sincronización hacia EDARSAHUB SQL.

## Conclusión

La arquitectura NO-LIVE para endpoints visuales queda validada en los módulos auditados.

Pendientes:
1. Documentar P0-B: tabla de detalle real de tickets/cheques si se requiere drill-down individual.
2. Auditar MongoDB legacy y clasificar cada referencia como permitida temporalmente o prohibida.
3. Centralizar credenciales EDARSAHUB y eliminar referencias hardcodeadas.
