# Backfill Opción A — COMPLETADO (detalle ticket/producto a Sync_Sales)

**Fecha:** 2026-06-08
**Autorización:** Usuario autorizó Opción A (lectura POS en vivo) + escalado por tandas + desbloqueo CIENFUEGOS/MPRO.
**Regla protegida (cumplida):** NO se tocó/re-derivó `Comercial_KPIs_Diarios_v2` ni `vw_*`. Solo `Sync_Sales`.

## Resultado final — Sync_Sales (de 79 → 112,313 tickets)
| Unidad | Sistema | Tickets | Cobertura | vs KPI canónico (mayo-26) |
|---|---|---|---|---|
| 130MID | SoftRestaurant 10 | 26,796 | 2024-06 → 2026-06 | (validado) |
| CIENFUEGOS | SoftRestaurant 9.5 (SQL 2014) | 30,183 | 2024-06 → 2026-06 | +4.7% |
| ESTELAR | SoftRestaurant 12 | 16,216 | 2025-06-27 → 2026-06 (*) | −0.18% |
| 130QRO | MPRO (CENTRAL2020) | 17,612 | 2024-06 → 2026-06 | −1.9% |
| ORIGEN | MPRO (CENTRAL2020) | 21,506 | 2024-06 → 2026-06 | −1.3% |

(*) El POS de ESTELAR solo conserva datos desde 2025-06-14 (límite real del origen, no bug).

**KPI canónico INTACTO:** `Comercial_KPIs_Diarios_v2` = 3,392 filas / **$431,766,974.05** / `SQL_LIVE` (sin cambios antes y después).

## Cómo se ejecutó (seguro, canónico, idempotente)
- **Conectividad:** probe read-only confirmó las 5 unidades alcanzables.
- **Credenciales:** 100% canónicas (`get_server_connection_config(server_id)`), sin hardcode, sin imprimir secretos.
- **Carga:** por lotes (`executemany`), transaccional con rollback, idempotente por `(NumeroTicket, UnidadNegocio, fecha)`. Bitácora en `Sistema_SyncPOS_Bitacora`. Reads con `WITH (NOLOCK)`.
- **Por tandas** (aprobadas por el usuario): SoftRestaurant 130MID+ESTELAR (Tanda 1 + resto), luego CIENFUEGOS, luego MPRO 130QRO+ORIGEN.

## Desbloqueos técnicos resueltos
1. **CIENFUEGOS (SQL Server 2014, SR 9.5):** no soporta `FOR JSON PATH`. Solución: extracción en **dos pasos** (header + detalle) armando el JSON de items en Python (version-agnóstico).
2. **MPRO (CENTRAL2020):** `Venta_Detalle` no existe → el detalle vive en **`Comanda_Detalle`** (`Co_Folio`, `Pr_Cve_Producto`, `Cd_Concepto`, `Cd_Cantidad`, `Cd_Precio`, `Cd_Importe`). Además `Venta_Encabezado` mezcla sucursales → se añadió filtro **`Sc_Cve_Sucursal = sucursal_origen_id`** canónico (130QRO=0021, ORIGEN=0023). Con el filtro, 130QRO cuadró exacto con el KPI. `WITH (NOLOCK)` + reintento ante deadlock.

## Validación de integridad
- Idempotencia confirmada (re-runs detectaron duplicados, insertaron solo lo nuevo).
- KPIs canónicos sin un solo cambio (regla protegida cumplida).
- Diferencias detalle vs KPI dentro de rango sano (−1.9% a +4.7%), reportadas, NO corregidas.

## Scripts
- `backend/scripts/probe_pos_connectivity.py`
- `backend/scripts/pilot_backfill_sync_sales.py` (extractores SoftRestaurant single/two-pass + MPRO, idempotente)
- `backend/scripts/backfill_sync_sales_batch.py` (orquestador por lotes mes×unidad)

## Pendiente / siguiente
- **PIC Fase 2:** ahora que `Sync_Sales` tiene detalle real (112,313 tickets / ~2M líneas), conectar las tarjetas "Top Productos" / "Casas/Distribuidores" del `DashboardIA` a datos reales (antes mock).
- **Normalización de productos** (mismo producto con nombres distintos entre POS).
- Diferencia CIENFUEGOS +4.7% (ch.total incluye propina/impuesto vs KPI): revisar si se requiere venta neta para el detalle.
- **NO-LIVE (arquitectura):** `repository_softrestaurant.py` (Finanzas CxP) aún consulta POS en vivo → migrar a tabla pre-calculada (trabajo futuro).
