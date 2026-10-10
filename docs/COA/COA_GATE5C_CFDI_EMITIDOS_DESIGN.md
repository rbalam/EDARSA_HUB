# COA Gate 5C - Diseno canonico minimo de CFDI emitidos

## Estado

DESIGN ONLY. Este Gate no ejecuta DDL ni modifica SQL. Produccion no se toca.

## Evidencia de entrada

Gate 5B certifico que `dbo.Venta_Encabezado` es la operacion comercial canonica y contiene `VentaID`, `ClienteID`, `Serie`, `Folio`, `NumeroFactura`, `UUIDFactura` y `Total`, pero no constituye un repositorio fiscal completo comparable con `dbo.Compras_DocumentosFiscales`.

## Decision de dominio

Se propone un dominio fiscal reutilizable de salida, no propiedad exclusiva de COA:

- `dbo.Fiscal_DocumentosEmitidosEstatus`
- `dbo.Fiscal_DocumentosEmitidos`

No se crea `DocumentoFiscalEmitidoRelacion` en V1. Gate 5B no demostro una relacion N:M entre CFDI emitido y ventas. Si posteriormente aparece evidencia de un CFDI ligado a multiples ventas u otros objetos fiscales, se auditara antes de crearla.

## Relaciones canonicas

`Fiscal_DocumentosEmitidos` referencia:

- `Sistema_Empresas(EmpresaID)` obligatorio.
- `Unidades_Negocio(id)` nullable.
- `Cliente_Catalogo(ClienteID)` obligatorio.
- `Venta_Encabezado(VentaID)` nullable.
- `Proveedor_Monedas(MonedaID)` para moneda canonica.
- `Usuario_Catalogo` para auditoria.
- `Fiscal_DocumentosEmitidosEstatus` para estado fiscal.

`VentaID` es nullable intencionalmente: Facturacion COA puede recibir solicitudes administrativas que aun no tengan una venta comercial/POS canonica asociada. No se debe inventar una Venta para poder timbrar o registrar el CFDI.

## Identidad fiscal

`DocumentoFiscalEmitidoID bigint IDENTITY` es la PK tecnica. `UUID` se mantiene nullable hasta timbrado y debe tener indice UNIQUE filtrado cuando exista.

## Snapshot fiscal

RFC emisor/receptor, serie, folio, importes y datos CFDI son atributos del documento emitido y pueden persistirse como snapshot fiscal. Esto no sustituye ni duplica los maestros de Cliente/Empresa; conserva lo efectivamente emitido/timbrado.

## Integracion con COA

`COA_ExpedienteReferencias` debe conservar `DocumentoFiscalID -> Compras_DocumentosFiscales` para compras/proveedor y sumar dos referencias separadas:

- `VentaID -> Venta_Encabezado(VentaID)`
- `DocumentoFiscalEmitidoID -> Fiscal_DocumentosEmitidos(DocumentoFiscalEmitidoID)`

La futura migracion debe actualizar `CK_COA_ExpedienteReferencias_UnSoloDestino` para incluir ambos nuevos destinos.

## Flujo funcional soportado

Solicitud COA -> expediente -> Cliente/Empresa/Unidad -> validacion -> referencia a Venta si existe -> envio a contador -> recepcion/timbrado -> alta de documento fiscal emitido -> UUID/XML/PDF/estatus SAT -> referencia desde COA -> envio al cliente -> comprobante de pago -> cierre.

## Fuera de alcance de Gate 5C

- Ejecutar DDL.
- Crear migracion fisica.
- Definir proveedor PAC/API de timbrado.
- Automatizar correo o WhatsApp.
- Definir RBAC final del flujo.
- Inventar cascadas o reglas de comision.

## Siguiente Gate sugerido

Gate 5D: preflight READ_ONLY del diseno Gate 5C contra tipos exactos, PK/UQ/FK, nombres de constraints/indexes, colisiones y contrato fisico actual de `COA_ExpedienteReferencias`, antes de autorizar una migracion.
