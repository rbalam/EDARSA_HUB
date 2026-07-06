---
applyTo: "backend/modules/comercial*/**,backend/modules/inteligencia_comercial/**,backend/modules/dashboard_ejecutivo/**,frontend/src/pages/Comercial.js,frontend/src/pages/TableroEjecutivo.js,frontend/src/pages/DashboardEjecutivo.js,frontend/src/portal-inteligencia/**"
---

# EDARSAHUB Comercial / Inteligencia / Ejecutivo

## KPIs

- Ventas = `ventas_total` con IVA.
- No usar `ventas_sin_propina` como venta principal.
- No usar subtotal, venta neta o venta sin IVA para KPI visible de Ventas.
- Consumo por persona = `ventas_total / pax_total`.
- `cheque_promedio` = `ventas_total / tickets_total` o `ventas_total / cheques_total`.
- `pax_promedio = pax / tickets` no es KPI válido.
- Backend calcula KPIs.
- Frontend solo pinta.

## Unidad de negocio

- Fuente canónica: `dbo.Unidades_Negocio`.
- Servicio: `UnidadesService` / `CorporateFilterService`.
- Llave: `unidad_negocio_pk`.
- `codigo` es legacy/display.
- `nombre` es display.
- No filtrar por `unidad_negocio_nombre` como llave principal.
- No generar selector desde runtime, ventas, KPIs o `SELECT DISTINCT`.

## Ausencia de datos

Si no hay registros para unidad/periodo:
- No devolver `$0.00` como dato real sin estado de ausencia.
- Reportar ausencia de datos, sync pendiente o unidad sin datos.
