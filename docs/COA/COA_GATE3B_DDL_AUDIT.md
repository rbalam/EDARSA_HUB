# COA Gate 3B - Auditoria del DDL minimo

## Alcance
Este gate genera y audita el archivo `docs/COA/COA_GATE3B_MINIMAL_DDL.sql`. El SQL es un artefacto de diseno. NO se ejecuta en este gate.

## Evidencia de entrada
- `docs/COA/COA_GATE2_CANONICAL_MODEL_DOSSIER.md`
- `worker_queue/results/coa-gate3a-ddl-key-contract-audit-v1-20260909.json`

Gate 3A certifico los tipos canonicos usados por las FK de este DDL:
- EmpresaID = int
- UnidadNegocioID = uniqueidentifier
- UsuarioID = int
- ClienteID = int
- ProveedorID = int
- DocumentoFiscalID = bigint
- PagoID = bigint
- DecisionPagoID = bigint
- NominaID = int
- DispersionNominaID = int
- NominaReciboID = int
- ColaboradorID = int
- ContratoID = uniqueidentifier

## Objetos nuevos y justificacion
1. `COA_Expedientes`: agregado transversal de operacion administrativa.
2. `COA_ExpedienteEventos`: trazabilidad cronologica del expediente.
3. `COA_ExpedienteReferencias`: relaciones hacia entidades canonicas, con FK reales y check de un solo destino por fila.
4. `COA_ReglasComision`: encabezado versionado de reglas de comision.
5. `COA_ReglasComisionCondiciones`: condiciones configurables por dimension y valores tipados.
6. `COA_ExcepcionesRegla`: negociaciones especiales/excepciones con motivo y autorizacion.
7. `COA_ComisionAplicada`: snapshot historico del calculo para reproducibilidad.

## No duplicacion
El DDL no crea tablas de proveedor, cliente, empresa, unidad, usuario, documento fiscal, pago, nomina, dispersion, recibo, colaborador o contrato. Todas esas entidades se referencian mediante sus PK canonicas auditadas.

## Comisiones
No existe `DEFAULT 6.5`, `0.065`, `6.5` ni ningun porcentaje comercial fijo en el DDL. `Porcentaje`, `ImporteFijo`, `BaseCalculoCodigo`, vigencias, prioridad y condiciones son datos de configuracion.

El motor admite que una regla dependa de empresa, unidad, cliente, proveedor, contrato y dimensiones textuales o rangos adicionales. Las negociaciones especiales quedan separadas en `COA_ExcepcionesRegla`; por tanto no requieren hardcodes en backend o SQL.

## Integridad referencial
Las FK hacia objetos existentes respetan los tipos certificados por Gate 3A. No se ejecuta `ALTER TABLE` sobre ningun objeto canonico. Las nuevas tablas solo se relacionan hacia los maestros existentes.

## Auditoria temporal
Se usa `datetime2(3)` y `sysutcdatetime()` para eventos/alta/calculo, siguiendo el patron auditado en estructuras financieras modernas. Las acciones sensibles conservan UsuarioID canonico cuando aplica.

## Riesgos y decisiones diferidas
- Los codigos de estado, tipo de operacion, canal, dimension y operador quedan como codigos declarativos sin CHECK con listas hardcodeadas. Los catalogos correspondientes se decidiran en un gate funcional posterior si la operacion real los necesita.
- Gate 3C certifico `dbo.Proveedor_Monedas` como catalogo monetario canonico candidato y confirmo `MonedaID` como `smallint`; el repositorio ya contiene FK existentes hacia `dbo.Proveedor_Monedas(MonedaID)`. Gate 3B-R2 reemplaza `MonedaCodigo char(3)` por `MonedaID smallint` y agrega FK canonica en `COA_ReglasComision` y `COA_ComisionAplicada`. `ClaveMoneda` queda derivable del catalogo y no se duplica en COA.
- `SnapshotResolucion` es evidencia de calculo; el formato JSON/estructura se definira en contrato de servicio antes de persistir datos.
- No se agregan tablas de mensajeria en este DDL minimo. Gmail/WhatsApp se modelaran despues de auditar infraestructura transversal y contratos de integracion.

## Veredicto Gate 3B-R2
DDL MINIMO CORREGIDO CON MONEDA CANONICA Y NO EJECUTADO. Gate 3C confirmo ausencia de colisiones de tablas/constraints/indices y validez de las dependencias canonicas. El siguiente paso debe ser un preflight final READ_ONLY sobre esta revision R2 antes de autorizar cualquier CREATE TABLE.
