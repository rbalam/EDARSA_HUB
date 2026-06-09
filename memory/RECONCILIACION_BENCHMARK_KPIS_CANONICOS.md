# RECONCILIACIÓN — Benchmark, Pricing y KPIs Canónicos
Fecha: 2026-06-09 · Régimen: SQL-First, NO-LIVE, sin hardcode, sin testing_agent_v3_fork

## 1. VALIDACIÓN DEL PLANTEAMIENTO DEL USUARIO
**¿Dupliqué un benchmark existente?** Parcialmente sí en NOMBRE, no en concepto:
- **Existente** `modules/comercial/services/benchmark_service.py` = **benchmark de PRECIOS vs COMPETIDORES externos** (tabla `Comercial_PricingBenchmarkProducto` ↔ `Comercial_Competidores`/`CompetidoresMenuItems`). Mapea producto propio ↔ producto de competencia + precio. Menús: Costos y Márgenes / Pricing IA.
- **Nuevo (este trabajo)** = **benchmark de DESEMPEÑO INTERNO de grupo** (ventas, cheque promedio, PAX entre unidades hermanas) + **confidencialidad/anonimización**. Es el requerimiento nuevo de "Gobierno de Acceso Comercial, Benchmark y Confidencialidad".
- **Conclusión:** son capacidades distintas, pero comparten el término "benchmark" y deben ALINEARSE (centralización) y consumir KPIs CANÓNICOS.

## 2. HALLAZGO: server_id OPERACIONAL EN EL MÓDULO EXISTENTE
`modules/comercial` usa `server_id` como parámetro operativo (viola máximas actuales):
- `routes_pricing_ai.py`: `PricingRequest.server_id` (Field obligatorio) en 3+ endpoints → debe ser `unidad` canónica.
- `services/pricing_ai_service.py`: `_obtener_datos_producto(codigo, server_id)`.
- `services/benchmark_service.py`: `obtener_benchmarks_producto(codigo, server_id)`, almacena `ServerID`.
- `routes_precios_sugeridos.py`: ya migrado (`unidad` + `server_id` DEPRECATED). ✅ patrón a seguir.
- `repository.py` (76), `routes.py` (133): mayoría son JOINs internos a Sistema_EmpresasServidores (plumbing aceptable) — auditar para separar operacional vs plumbing.

## 3. ENTREGADO EN ESTE TRABAJO (aditivo, sin romper nada)
- ✅ `core/confidencialidad/AnonymizerService` — capa central de enmascaramiento (6 tests).
- ✅ `core/kpis_canonicos/KPIsCanonicosService` — **definición ÚNICA** de KPIs: glosario canónico
  (cheque=ticket; cheque_promedio=ticket_promedio; ventas; pax; venta_por_pax; cheques_por_pax),
  desde `Comercial_KPIs_Diarios_v2` por `unidad_negocio_pk` (5 tests).
- ✅ Benchmark interno de grupo (`modules/comercial_benchmark`) consumiendo KPIs canónicos +
  AnonymizerService, con envelope completo (criterios 46–54). Frontend en Portal Inteligencia
  ("Benchmark Grupo"). Auth dual cookie+header corregida.
- ✅ ETL NO-LIVE `Comercial_Inteligencia_VentasDetalleProducto` desde `Sync_Sales.items` (130MID/130QRO
  completos; CIENFUEGOS/ESTELAR/ORIGEN en backfill).

## 4. ROADMAP DE CANONICALIZACIÓN (pendiente de confirmación — toca producción)
- **C1** Migrar `routes_pricing_ai` y `pricing_ai_service`: `server_id` → `unidad` canónica
  (resolver server_id internamente vía UnidadesService). Actualizar frontend PricingIA/CostosMargenes.
- **C2** Migrar consumidores de KPIs (Tablero Ejecutivo, Compras, Inteligencia) a `KPIsCanonicosService`
  para que ticket/cheque/promedio se calculen IGUAL en todos los menús.
- **C3** Auditar `repository.py`/`routes.py` (comercial) y separar server_id operacional vs plumbing;
  exponer siempre identidad canónica (no nombres/IDs técnicos denormalizados).
- **C4** (diferido) Grupo corporativo real, benchmark sectorial, siembra de permisos benchmark.

## 5. GLOSARIO CANÓNICO (fuente única: core/kpis_canonicos)
| Canónico | Sinónimos | Fórmula |
|---|---|---|
| ventas | venta_neta, ventas_total | Σ ventas_total |
| cheques | tickets, comandas, cuentas | Σ tickets_total |
| cheque_promedio | ticket_promedio, ticket_medio | ventas / cheques |
| pax | comensales | Σ pax_total |
| venta_por_pax | consumo_per_capita | ventas / pax |
| cheques_por_pax | rotacion_por_comensal | cheques / pax |
