# Lógica de negocio de ventas por tiempo, salud y áreas

**Dominio:** Comercial
**Versión:** EDARSAHUB V1.0
**Estado:** Regla canónica en evolución

## Objetivo empresarial

Permitir que Dirección y Gerencia determinen:

- cuándo vende más una unidad;
- qué días concentran la venta;
- qué áreas físicas generan ingresos;
- si el resultado mejora frente a periodos equivalentes;
- si el cambio proviene de tráfico, cuentas o consumo;
- si la información es confiable y vigente.

## Fuente de verdad temporal

La fuente canónica de turnos es:

`dbo.Sistema_TurnosOperativosUnidad`

Solo se considerarán turnos:

- activos;
- aplicables a ventas del día;
- pertenecientes a la unidad efectiva.

`dbo.Sistema_HorariosServicioUnidad` no sustituirá a los turnos sin una
definición semántica documentada.

## Historial

Los hechos históricos utilizarán la ventana almacenada cuando fueron
sincronizados.

Un cambio actual de horarios no deberá reclasificar datos históricos.

## Orden operativo de horas

Las horas se mostrarán desde la apertura operativa hasta el cierre.

Para 19:00–05:59:

`19, 20, 21, 22, 23, 00, 01, 02, 03, 04, 05`

No se utilizará orden civil cuando el turno cruce medianoche.

## Fecha operativa

Una venta posterior a medianoche pertenecerá al día operativo anterior
cuando se encuentre dentro de una ventana que cruza medianoche.

La fecha civil no sustituirá a `fecha_operacion`.

## Hora pico

La hora pico será la hora operativa con mayor venta válida.

Deberá incluir:

- monto;
- tickets;
- orden operativo;
- periodo;
- fuente;
- cobertura;
- última sincronización.

Los empates deberán mostrarse explícitamente.

## Comparativos

El periodo actual se comparará contra:

1. Semana anterior: menos 7 días.
2. Semana equivalente del mes anterior: menos 28 días.
3. Semana equivalente del año anterior: menos 364 días.

Estos desplazamientos preservan el día de la semana.

Un periodo parcial deberá compararse contra el mismo corte operativo.

## Ventas

La venta comercial visible:

- incluye IVA;
- excluye propinas.

Las propinas se presentan por separado.

## Fórmulas

- Cheque promedio: `ventas / tickets`
- PAX promedio: `ventas / pax`
- Participación del área: `ventas_area / ventas_unidad`
- Variación: `((actual - referencia) / referencia) * 100`

Cuando la referencia sea cero, la variación será `N/D`.

## Salud comercial

La salud considera como mínimo:

- ventas;
- tickets;
- PAX;
- cobertura;
- antigüedad.

No se emitirá una calificación cuando:

- la fuente esté vencida;
- falte cobertura;
- falten comparativos;
- la referencia sea inválida;
- exista inconsistencia material.

El estado será:

`SIN_DATOS_SUFICIENTES`

## Áreas físicas

Una zona de origen solo podrá convertirse en área comercial cuando exista:

- identificador de origen;
- nombre de origen;
- servidor;
- unidad;
- fecha operativa;
- trazabilidad;
- regla de normalización aprobada.

No se inferirán áreas mediante:

- número de mesa;
- nombre del mesero;
- texto parcial;
- horario;
- canal;
- catálogo de recursos humanos.

## Dimensiones independientes

No se mezclarán:

- área física;
- canal;
- turno;
- centro de consumo;
- unidad;
- zona comercial geográfica.

## Fuente candidata de áreas

`dbo.Sync_Mesas` es candidata, pero no queda aprobada hasta confirmar:

- cobertura;
- vigencia;
- IVA;
- propinas;
- duplicados;
- relación cuenta-mesa-zona;
- estabilidad de `ZonaID`;
- estabilidad de `ZonaNombre`.

Las áreas sin equivalencia se mostrarán como:

`SIN_AREA_MAPEADA`

## KPI por área

Cada área deberá devolver:

- área de origen;
- área canónica;
- ventas;
- participación;
- tickets;
- PAX;
- cheque promedio;
- PAX promedio;
- hora pico;
- comparativos;
- cobertura;
- estado de sincronización.

## Criterios de aceptación

El módulo será aceptable cuando:

1. Use el horario operativo real.
2. Ordene correctamente cruces de medianoche.
3. Respete `fecha_operacion`.
4. Preserve el histórico.
5. Compare periodos equivalentes.
6. Excluya propinas.
7. Muestre cobertura y antigüedad.
8. Bloquee salud con datos vencidos.
9. Use áreas auditadas.
10. Mantenga trazabilidad.
11. Comercial, Ejecutivo e Inteligencia coincidan.
