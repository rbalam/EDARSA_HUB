# ADR-20260804: Fuente canónica y fuente provisional de ventas MPRO

- Estado: Aceptado para EDARSAHUB V1.0
- Fecha: 2026-08-04
- Dominio: Comercial / KPIs / Ventas del día
- Sistema origen: MPRO
- Unidades: ORIGEN y 130QRO

## 1. Decisión

ORIGEN y 130QRO comparten la misma regla de negocio y la misma fuente canónica final para ventas cerradas:

    Venta_Encabezado.Vn_Precio_Neto_Importe

La relación validada es:

    Venta_Encabezado.Vn_Documento = Comanda.Co_Folio

`Comanda_Detalle.Cd_Importe` no es una fuente canónica final. Puede representar el importe previo a descuentos, mermas, cortesías u otros ajustes aplicados posteriormente.

130QRO puede utilizar temporalmente información provisional de Comanda o de la API local mientras `Venta_Encabezado` aún no esté sincronizado para la fecha operativa actual.

La información provisional debe sustituirse o reconciliarse contra `Venta_Encabezado` tan pronto como la venta final esté disponible.

## 2. Regla de negocio común

Para todas las unidades MPRO:

- ventas finales con IVA incluido;
- propinas separadas;
- descuentos, mermas, cortesías y ajustes reflejados en la venta final;
- tickets y PAX con semántica canónica;
- atribución por `fecha_operacion`;
- no restar propinas de ventas;
- no considerar `Comanda_Detalle.Cd_Importe` como cierre contable definitivo.

## 3. Evidencia de ORIGEN

Para ORIGEN, fecha operativa 2026-08-03:

| Concepto | Importe |
|---|---:|
| Comanda_Detalle.Cd_Importe | 25,596.51 |
| Venta final validada | 24,941.51 |
| Diferencia | 655.00 |

La diferencia correspondió a tres operaciones:

| Comanda | Importe previo | Venta final | Diferencia |
|---|---:|---:|---:|
| SB-0053395 | 130.00 | 65.00 | 65.00 |
| SB-0053403 | 770.00 | 385.00 | 385.00 |
| SB-0053406 | 205.00 | 0.00 | 205.00 |
| Total | 1,105.00 | 450.00 | 655.00 |

Esto confirmó que la comanda podía sobreestimar la venta final.

## 4. Evidencia de 130QRO

La auditoría comparó doce fechas entre junio, julio y agosto de 2026.

En todas las fechas con histórico disponible, el histórico canónico coincidió exactamente con:

    Venta_Encabezado.Vn_Precio_Neto_Importe

Se detectaron cinco días donde `Comanda_Detalle.Cd_Importe` fue mayor que la venta final:

| Fecha | Comanda | Venta final | Exceso |
|---|---:|---:|---:|
| 2026-06-04 | 123,825.00 | 123,645.00 | 180.00 |
| 2026-06-13 | 182,842.00 | 180,642.00 | 2,200.00 |
| 2026-06-19 | 196,216.00 | 195,556.00 | 660.00 |
| 2026-06-22 | 105,164.00 | 104,899.00 | 265.00 |
| 2026-08-01 | 221,766.00 | 219,346.00 | 2,420.00 |

Se localizaron seis tickets donde la comanda tenía importe positivo y la venta final terminó en cero.

Esto demuestra que 130QRO tiene el mismo riesgo funcional observado en ORIGEN.

## 5. Ventas del día e histórico

El histórico canónico utiliza la venta final y fue correcto en la muestra auditada.

El riesgo se encuentra en el proceso de Ventas del día cuando el scheduler usa información provisional basada en Comanda antes de que `Venta_Encabezado` esté disponible.

Para la fecha operativa 2026-08-03:

- el overlay de 130QRO contenía 84,671.00;
- `Venta_Encabezado` aún no contenía registros para esa fecha;
- el valor provisional coincidía con la fuente externa;
- esa coincidencia no convierte a Comanda en fuente canónica permanente.

## 6. Arquitectura requerida

Debe distinguirse entre:

### Fuente canónica final

    Venta_Encabezado.Vn_Precio_Neto_Importe

### Fuente provisional intradía

- API local;
- Comanda y Comanda_Detalle;
- otra fuente transitoria validada.

La fuente provisional debe identificarse explícitamente mediante metadatos como:

- `fuente_original`;
- `sync_run_id`;
- `estado_dato`;
- `es_provisional`;
- `fecha_ultima_actualizacion`.

## 7. Diseño futuro recomendado

    MproClosedSalesProvider
      - MproCanonicalClosedSalesAdapter
      - MproIntradayProvisionalSalesAdapter
      - MproClosedSalesReconciliationService

El servicio de conciliación deberá:

1. usar información provisional durante la operación;
2. detectar cuándo `Venta_Encabezado` ya está disponible;
3. sustituir el dato provisional por el canónico;
4. registrar la diferencia;
5. generar alerta cuando la diferencia exceda la tolerancia;
6. evitar doble conteo;
7. conservar trazabilidad del valor anterior y final.

## 8. Protección contra regresiones

No se debe:

- declarar `Comanda_Detalle.Cd_Importe` como venta final;
- publicar un dato provisional como definitivo;
- asumir equivalencia entre Comanda y Venta_Encabezado;
- mezclar propinas con ventas;
- perder descuentos, mermas o cortesías;
- sumar simultáneamente el provisional y el canónico;
- mantener indefinidamente un provisional cuando ya existe el canónico.

## 9. Criterio para V1.0

Para V1.0 se acepta una fuente provisional intradía únicamente cuando:

- la fuente canónica todavía no esté disponible;
- el dato esté identificado como provisional;
- se conserve la unidad, fecha_operacion y trazabilidad;
- se reemplace o concilie posteriormente;
- no se sume dos veces;
- exista control de diferencia.

## 10. Deuda técnica

Queda registrada para una versión posterior:

- formalizar los adaptadores canónico y provisional;
- automatizar la reconciliación;
- registrar estado provisional/final;
- documentar horarios de sincronización de cada servidor;
- crear pruebas contractuales para ORIGEN y 130QRO;
- alertar diferencias entre Comanda y Venta_Encabezado.

La deuda técnica no autoriza considerar la comanda como fuente canónica final.
