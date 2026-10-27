# COA Gate 6C - Lifecycle canonico de CFDI emitidos

## Alcance

Este documento define el lifecycle operativo de `dbo.Fiscal_DocumentosEmitidosEstatus`.

No modifica SQL.
No inserta seeds.
No cambia `EstatusSAT`.
No reutiliza catalogos de Compras o Proveedores.

## Principio de separacion

`EstatusDocumentoFiscalEmitidoID` representa el estado operativo del documento emitido dentro de EDARSAHUB.

`EstatusSAT` representa la observacion o respuesta fiscal proveniente del SAT o del proveedor de timbrado.

Ambos conceptos son independientes y no deben colapsarse en una sola columna.

## Catalogo propuesto

| ID | Codigo | Nombre | EsFinal | Uso |
|---:|---|---|:---:|---|
| 1 | BORRADOR | Borrador | 0 | Documento capturado o preparado, aun no enviado a timbrar. |
| 2 | PENDIENTE_TIMBRADO | Pendiente de timbrado | 0 | Listo para enviarse al proveedor de timbrado o esperando respuesta. |
| 3 | TIMBRADO | Timbrado | 0 | CFDI timbrado exitosamente; debe contar con UUID cuando aplique. |
| 4 | ERROR_TIMBRADO | Error de timbrado | 0 | Intento de timbrado rechazado o fallido; permite correccion y reintento. |
| 5 | CANCELACION_SOLICITADA | Cancelacion solicitada | 0 | Se inicio el proceso de cancelacion y aun no existe confirmacion final. |
| 6 | CANCELADO | Cancelado | 1 | CFDI cancelado de forma confirmada. |

Todos los registros del catalogo se consideran `Activo=1` en la propuesta inicial.

## Transiciones permitidas

- BORRADOR -> PENDIENTE_TIMBRADO
- PENDIENTE_TIMBRADO -> TIMBRADO
- PENDIENTE_TIMBRADO -> ERROR_TIMBRADO
- ERROR_TIMBRADO -> PENDIENTE_TIMBRADO
- TIMBRADO -> CANCELACION_SOLICITADA
- CANCELACION_SOLICITADA -> CANCELADO
- CANCELACION_SOLICITADA -> TIMBRADO si la cancelacion no se concreta y el CFDI continua vigente

No se permite transicion desde CANCELADO a estados activos.

## Invariantes

1. CANCELADO es estado final.
2. TIMBRADO no significa necesariamente que el SAT lo reporte como vigente en todo momento; `EstatusSAT` conserva esa observacion externa.
3. Un error de timbrado no elimina el documento ni crea uno nuevo automaticamente.
4. La cancelacion es un proceso separado del timbrado.
5. `FechaTimbrado` debe corresponder a estados TIMBRADO, CANCELACION_SOLICITADA o CANCELADO cuando exista.
6. `FechaCancelacion` debe existir para CANCELADO.
7. UUID debe mantenerse historicamente aun si el CFDI termina CANCELADO.
8. No se reutilizan `Compras_DocumentosFiscalesEstatus`, `Compras_ConciliacionSATEstatus` ni `Proveedor_EstatusSAT` como FK de documentos emitidos.
9. No se hardcodean significados del SAT en este catalogo.
10. Cualquier automatizacion futura debe validar transiciones, no solo escribir IDs.

## Evidencia previa

Gate 6A-R2 certifico:
- `Fiscal_DocumentosEmitidosEstatus` existe y esta vacia.
- `Fiscal_DocumentosEmitidos` existe y esta vacia.
- `Fiscal_DocumentosEmitidos` ya tiene columnas separadas para estado operativo, UUID, fechas de timbrado/cancelacion y `EstatusSAT`.

Gate 6B certifico:
- Compras_DocumentosFiscalesEstatus = PENDIENTE_DESCARGA, DESCARGADO_XML, DESCARGADO_XML_PDF, XML_INVALIDO, CANCELADO_SAT, CONCILIADO, DIFERENCIAS.
- Compras_ConciliacionSATEstatus = PENDIENTE, COINCIDE, diferencias varias, CANCELADO_SAT, REVISADO_MANUAL.
- Proveedor_EstatusSAT = PENDIENTE, OK, OBSERVADO, BLOQUEADO.

Estos catalogos no describen el lifecycle de un CFDI emitido.

## Siguiente Gate

Gate 6D debera diseñar un seed idempotente y reversible para Development, pero no ejecutarlo fisicamente hasta pasar preflight READ_ONLY.
