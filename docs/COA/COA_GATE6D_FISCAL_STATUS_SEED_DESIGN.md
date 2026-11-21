# COA Gate 6D - Seed design de estados de CFDI emitidos

## Modo
DESIGN ONLY. No ejecuta SQL.

## Objetivo
Definir un seed idempotente, reversible y fail-safe para `dbo.Fiscal_DocumentosEmitidosEstatus`.

## Estados
1. BORRADOR
2. PENDIENTE_TIMBRADO
3. TIMBRADO
4. ERROR_TIMBRADO
5. CANCELACION_SOLICITADA
6. CANCELADO

## Reglas
- No sobrescribir filas existentes.
- Fallar ante colision por ID con semantica distinta.
- Fallar ante colision por Codigo con ID distinto.
- Insertar unicamente filas faltantes sin conflicto.
- Mantener `Activo=1`.
- Solo `CANCELADO` tiene `EsFinal=1`.
- Rollback prohibido si existen documentos que referencien cualquiera de los seis IDs.
- Rollback elimina solo pares ID/Codigo canonicos.
- No modificar `EstatusSAT`.
- No reutilizar catalogos de Compras/Proveedor.
- Produccion fuera de alcance.

## Siguiente gate
Gate 6E debe ser READ_ONLY_SQL y validar colisiones, filas existentes, referencias y estructura exacta antes de cualquier ejecucion fisica en Development.
