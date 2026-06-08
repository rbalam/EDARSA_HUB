# PILOTO Opción A — Backfill de detalle a Sync_Sales (ESTELAR, mayo 2026)

**Fecha:** 2026-06-08
**Autorización:** Usuario autorizó Opción A (lectura POS en vivo) + piloto controlado (1 unidad, 1 mes, solo detalle).
**Regla protegida:** PROHIBIDO tocar/re-derivar `Comercial_KPIs_Diarios_v2` / `vw_*`. Solo `Sync_Sales` (staging).

## Conectividad (paso previo)
Las **5 unidades POS son alcanzables** desde el pod (probe read-only `SELECT 1`, ~0.6s c/u),
credenciales canónicas OK: 130MID, ESTELAR, CIENFUEGOS (SoftRestaurant `.ddns.net`) y
130QRO/ORIGEN (MPRO `54.39.104.176/CENTRAL2020`).

## Hallazgo clave
El histórico de **KPIs YA estaba completo** en `Comercial_KPIs_Diarios_v2`
(3,392 filas, 2024-05→2026-06, $431,766,974.05, fuente `SQL_LIVE`). Lo único faltante es el
**DETALLE ticket/producto en `Sync_Sales`**. Por eso el backfill puebla SOLO `Sync_Sales`.

## Resultados del piloto (ESTELAR · 2026-05-01 a 2026-06-01)
| Métrica | Valor |
|---|---|
| Tickets extraídos | 1,881 |
| Líneas (productos) extraídas | 25,541 |
| Venta detalle total | $2,924,063.00 |
| Tickets sin detalle | 0 |
| Tiempo de extracción | 1.6 s |
| Tickets nuevos insertados | 1,881 |
| Tickets duplicados | 0 (primera corrida) |
| Tiempo total (extracción + carga) | 63.7 s |

### Comparación contra KPI canónico (SOLO LECTURA — no se modificó nada)
| | Sync_Sales (detalle) | KPI canónico (`SQL_LIVE`) | Diferencia |
|---|---|---|---|
| Venta | $2,924,063.00 | $2,929,406.00 | **−$5,343 (−0.18%)** |
| Tickets | 1,881 | 1,942 | −61 |

La diferencia menor es esperada (la extracción filtra `cancelado=0` y `total>0`). El detalle
**cuadra muy bien** con el KPI canónico → la fuente de datos es correcta.

## Validaciones de seguridad/integridad
- **Idempotencia confirmada:** re-ejecución insertó **0** (1,881 duplicados detectados).
- **KPIs canónicos INTACTOS:** `Comercial_KPIs_Diarios_v2` sin cambios (3,392 filas / $431,766,974.05) post-piloto.
- **Solo `Sync_Sales`** tocado (79 → 1,960 filas totales). No se tocó `vw_*`, KPIs, Venta_Encabezado/Detalle, Mongo, usuarios.
- **Credenciales canónicas** (`get_server_connection_config`), sin hardcodes, sin imprimir password.
- Carga por lotes (`executemany`, batch=500), transaccional con rollback. Bitácora en `Sistema_SyncPOS_Bitacora`.

## Estimación de escalado (24 meses × 5 unidades)
- ~**225,720 tickets** estimados (lineal desde 1,881/mes/unidad).
- Tiempo de carga: ~32 ms/fila (latencia a SQL remoto) → estimado **~2 h** de inserción total.
- **Estrategia recomendada:** loader por lotes **mes × unidad**, idempotente, commit por mes,
  bitácora por corrida, ejecución en background con checkpoints. SoftRestaurant: CIENFUEGOS/ESTELAR/130MID;
  MPRO: 130QRO/ORIGEN (query MPRO aún por validar en piloto separado antes de escalar esa rama).

## Archivos
- `backend/scripts/probe_pos_connectivity.py` (probe conectividad read-only)
- `backend/scripts/pilot_backfill_sync_sales.py` (loader piloto idempotente, soporta `--dry-run`)

## Recomendación
Piloto exitoso. Listo para escalar **bajo autorización explícita**: cargar 24 meses por lotes
mes×unidad, empezando por las 3 SoftRestaurant (query validada) y validando la query MPRO en un
mini-piloto antes de 130QRO/ORIGEN.
