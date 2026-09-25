# COA Gate 5E - Migracion CFDI emitidos

## Estado

DESIGN ONLY. No ejecutar en este Gate. Produccion no se toca.

## Base certificada

Gate 5D certifico en READ_ONLY: 0 colisiones de tablas/constraints/indices propuestos; tipos exactos y PK/UQ compatibles para Empresa, Unidad, Cliente, Venta, Moneda y Usuario; ausencia de VentaID y DocumentoFiscalEmitidoID en COA_ExpedienteReferencias; existencia del CHECK actual de un solo destino; y ausencia de un objeto fiscal de salida equivalente.

## Migracion propuesta

Archivo: `backend/database/migrations/20260910_coa_cfdi_emitidos.sql`.

La migracion:
1. Verifica colisiones y precondiciones.
2. Crea `Fiscal_DocumentosEmitidosEstatus`.
3. Crea `Fiscal_DocumentosEmitidos`.
4. Crea indices del dominio fiscal.
5. Agrega `VentaID` y `DocumentoFiscalEmitidoID` a `COA_ExpedienteReferencias`.
6. Crea FKs e indices para ambas referencias.
7. Reemplaza `CK_COA_ExpedienteReferencias_UnSoloDestino` incluyendo los dos nuevos destinos.
8. Conserva `DocumentoFiscalID -> Compras_DocumentosFiscales`.
9. Usa transaccion y `XACT_ABORT ON`; ante error hace rollback y relanza.

No se insertan valores de catalogo de estatus: la semantica funcional debe aprobarse antes de seedear estados.

## Rollback

Archivo: `backend/database/migrations/20260910_coa_cfdi_emitidos_rollback.sql`.

Orden inverso:
1. Quitar CHECK ampliado.
2. Quitar indices/FKs COA nuevos.
3. Quitar columnas COA nuevas.
4. Restaurar CHECK original.
5. Eliminar tabla principal fiscal.
6. Eliminar catalogo de estatus.

El rollback no toca `DocumentoFiscalID` ni objetos de Compras.

## Riesgos que deben auditarse antes de ejecutar

- Drift de esquema entre Gate 5D y el momento de migrar.
- Colision posterior de nombres de objetos.
- Datos nuevos en COA que violen la expresion de destino unico ampliada.
- Semantica pendiente de catalogo de estatus para habilitar escritura funcional.
- Permisos DDL del canal de migracion en Desarrollo.

## Gate siguiente

Gate 5F: READ_ONLY preflight sobre el estado actual de SQL y auditoria estatica de los dos archivos de migracion. Solo si ambos pasan se puede solicitar autorizacion separada para ejecucion fisica en Desarrollo.
