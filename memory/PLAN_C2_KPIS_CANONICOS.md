# Plan C2 — Unificación de KPIs vía KPIsCanonicosService (pendiente, alto riesgo)

Fecha de análisis: 2026-06-10 · Régimen: SQL-First, NO-LIVE, sin hardcode

## Por qué se DIFIRIÓ (no se ejecutó a prisa)
C2 toca dashboards de PRODUCCIÓN muy usados. Hacerlo sin auditar backend+frontend de cada
pantalla consumidora introduce alto riesgo de regresión, justo lo contrario al objetivo de
"estabilizar V1.0". Se documenta para ejecutarlo en una sesión dedicada con pruebas por endpoint.

## Hallazgo clave: divergencia REAL de terminología/fórmula
Todos los módulos leen de la MISMA tabla `Comercial_KPIs_Diarios_v2` (los agregados base
Σventas/Σtickets/Σpax son consistentes). La inconsistencia está en las FÓRMULAS derivadas
y en QUÉ base de ventas usan:

| Ubicación | Campo | Fórmula actual | ¿Canónico? |
|---|---|---|---|
| `dashboard_ejecutivo/routes.py:87` | ticket_promedio | ventas / tickets | ✅ (= cheque_promedio) |
| `dashboard_ejecutivo/routes.py:88` | consumo_promedio_pax | ventas / pax | ✅ (= venta_por_pax) |
| `inteligencia_comercial/routes.py:706` | ticket_promedio | ventas / cheques | ✅ |
| `inteligencia_comercial/routes.py:759-763` | cheque_promedio / ticket_promedio | ventas_sin_propina/tickets ; ventas_sin_propina/**pax** | ⚠️ `ticket_promedio`=ventas/PAX (mislabel) y usa ventas_sin_propina |
| `comercial/service.py:985-986` | ticket_prom / cheque_prom | ventas/**pax** ; ventas/cheques | ⚠️ `ticket_prom`=ventas/pax |
| `comercial/service.py:1066` | calcular_ticket_promedio | ventas/cheques | ✅ |

→ El MISMO nombre (`ticket_promedio`/`ticket_prom`) significa **ventas/cheques** en unos lugares y
**ventas/pax** en otros, y a veces sobre `ventas` y otras sobre `ventas_sin_propina`.

## Glosario canónico (fuente única: `core/kpis_canonicos`)
- ventas = Σ ventas_total
- cheques = Σ tickets_total
- cheque_promedio (= ticket_promedio) = ventas / cheques
- pax = Σ pax_total
- venta_por_pax (= consumo per cápita) = ventas / pax
- cheques_por_pax = cheques / pax

## Pasos propuestos (por fases, cada una probada con cURL + screenshot)
1. **Inventario de consumidores frontend**: mapear qué pantalla lee cada campo y con qué
   etiqueta visible (para no romper significados al unificar).
2. **Fase A (bajo riesgo)**: alinear `inteligencia_comercial/routes.py:759-763` para que
   `ticket_promedio`=ventas/pax pase a llamarse `venta_por_pax` y `cheque_promedio` use la
   base de ventas canónica acordada (ventas vs ventas_sin_propina) — definir con el usuario.
3. **Fase B**: reemplazar cálculos ad-hoc por `KPIsCanonicosService.kpis_por_unidad()` en
   Tablero Ejecutivo, Compras e Inteligencia, devolviendo el bloque `metricas` canónico.
4. **Fase C**: ajustar etiquetas/labels del frontend a los nombres canónicos.
5. Regression: comparar totales por unidad antes/después (deben coincidir en agregados base).

## Decisión requerida del usuario antes de ejecutar
- ¿La base de "ventas" canónica para promedios es `ventas_total` o `ventas_sin_propina`?
  (Hoy hay mezcla; el servicio canónico expone ambas: `ventas` y `ventas_sin_propina`.)
