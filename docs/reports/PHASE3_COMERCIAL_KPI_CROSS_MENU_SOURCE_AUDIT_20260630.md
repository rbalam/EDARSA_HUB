# Phase 3 Comercial KPI cross-menu/source audit

Fecha: 2026-06-30
Alcance: Tablero Ejecutivo, Comercial e Inteligencia Comercial.
Modo: solo lectura.

## Objetivo

Auditar si los KPIs visibles en los menus comerciales de EDARSAHUB salen de la misma verdad de negocio:

- Tablero Ejecutivo: ventas, cheques/tickets, PAX, cheque promedio, ticket/PAX promedio.
- Comercial: dashboard por unidad/servidor y detalle comercial.
- Inteligencia Comercial: dashboard IA, Reporteador BI e ISCAM.

La validacion compara la vista KPI diaria v2 contra las tablas sincronizadas de detalle:

- `dbo.vw_Comercial_KPIs_Diarios_v2_Runtime`
- `dbo.Comercial_KPIs_Diarios_v2`
- `dbo.Comercial_Inteligencia_VentasDetalleProducto`
- `dbo.Sync_Sales`
- `dbo.Sync_PAX_Detalle`
- `dbo.Unidades_Negocio`

No consulta POS live. La comparacion es contra EDARSAHUB SQL, que debe ser la fuente canonica para produccion.

## Hallazgos de codigo previos a ejecutar SQL

1. Hay drift semantico de `ticket_promedio`.

   La metrica canonica en `backend/migrations/comercial_metricas_canonicas_20260609.py` define:

   - `cheque_promedio` = ventas sin propina / cheques.
   - `ticket_promedio` = ventas sin propina / PAX.

   Pero algunos modulos legacy usan `ticket_promedio` como ventas / tickets. Ejemplos:

   - `backend/modules/comercial_v2/repository_readonly.py`: `ticket_promedio_avg` se calcula como ventas / tickets.
   - `backend/modules/comercial/kpis_repository.py`: `ticket_promedio` se calcula como ventas / tickets.
   - `backend/modules/comercial/service.py`: varios helpers legacy usan ticket como ventas / cheques.

   Inteligencia Comercial y Reporteador BI ya tienden a la definicion canonica: ticket = ventas / PAX y cheque = ventas / cuentas.

2. Hay mezcla de ventas netas y ventas brutas.

   - Backend v2 documenta que KPI ventas debe ser `ventas_sin_propina`.
   - Algunas series o pantallas usan `ventas_total`.
   - ISCAM usa `Sync_Sales.MontoTotal`.

   Para produccion debe quedar explicito:

   - KPI principal ventas = venta neta/sin propina.
   - Propinas = KPI separado.
   - Venta bruta solo si se etiqueta como ventas con propina.

3. El detalle por producto puede sobrecontar PAX.

   Las tablas de detalle tienen varias lineas por ticket. Si una consulta hace `SUM(pax)` directo sobre lineas de producto, puede multiplicar PAX por numero de productos. La auditoria SQL agrupa primero por ticket (`id_transaccion`, `numero_ticket`, `fecha_operacion`) y luego suma PAX una vez por ticket.

4. Inteligencia Comercial mezcla niveles de fuente.

   - Dashboard IA usa la vista KPI diaria.
   - Reporteador BI usa vista KPI diaria para KPIs y detalle para clasificacion/productos.
   - ISCAM usa `Sync_Sales`.

   Esto es correcto solo si las fuentes sincronizadas tienen la misma cobertura por fecha/unidad y la misma definicion de ventas/tickets/PAX. La auditoria detecta cuando no.

## Script creado

Archivo:

`backend/database/validation/phase3_comercial_kpi_cross_menu_source_audit.sql`

Batches principales:

1. Metadata de ejecucion.
2. Existencia de objetos SQL requeridos.
3. Contrato de fuente por menu.
4. Frescura y cobertura por fuente en ultimos 30 dias con datos KPI.
5. Comparativo agregado por unidad: KPI runtime vs detalle vs Sync_Sales.
6. Auditoria semantica de `ticket_promedio` y `pax_promedio` guardados.
7. Diferencias diarias KPI vs detalle.
8. Comparativo KPI PAX vs `Sync_PAX_Detalle`.

## Comando para ejecutar en Emergent/VSCode

```bash
cd /app
source /app/.venv/bin/activate
export PYTHONPATH=/app/backend
set -a
. backend/.env
set +a
export EDARSAHUB_SQL_SERVER="${EDARSAHUB_SQL_SERVER:-$EDARSAHUB_SQL_HOST}"

/app/.venv/bin/python backend/tools/edarsahub_sql_runner.py \
  --mode validate \
  --script backend/database/validation/phase3_comercial_kpi_cross_menu_source_audit.sql
```

## Como interpretar

- `SIN_DETALLE_INTELIGENCIA`: el menu que usa detalle no puede cuadrar con KPI agregado para ese rango.
- `SIN_SYNC_SALES`: ISCAM no puede cuadrar con KPI agregado para ese rango.
- `KPI_NETO_VS_DETALLE_DIFIERE`: ventas netas de KPI y detalle no cuadran.
- `KPI_BRUTO_VS_SYNC_SALES_DIFIERE`: venta bruta KPI y Sync_Sales no cuadran.
- `CAMPO_TICKET_PROMEDIO_ES_CHEQUE_PROMEDIO`: el campo heredado `ticket_promedio` realmente contiene cheque promedio.
- `CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE`: el campo heredado `pax_promedio` realmente contiene PAX por cheque, no venta por PAX.

## Correccion esperada despues del reporte SQL

1. Elegir nombres canonicos en API:
   - `ventas_netas`
   - `ventas_brutas`
   - `propinas`
   - `cheques_total`
   - `pax_total`
   - `cheque_promedio`
   - `ticket_promedio`

2. Mantener alias legacy solo como compatibilidad, no como definicion de negocio.

3. En consultas de detalle, agregar a nivel ticket antes de sumar PAX o calcular promedios.

4. Para historicos donde `Sync_Sales`/detalle no tenga cobertura completa, mostrar estado de cobertura incompleta o usar solo la vista KPI diaria para KPIs agregados.
