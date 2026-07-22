# EDARSAHUB V1.0 - CFDI, Portal Proveedores y Comprobaciones

## Contrato

- No MongoDB.
- No conexiones live desde tableros, reportes, portal ni CxP.
- No conexion SAT en V1.0.
- SAT queda preparado como validador/auditor posterior sobre metadata ya canonizada.
- Las carpetas del servidor son solo fuente de ingesta inicial.
- Despues de la ingesta, Portal Proveedores, Finanzas CxP y Comprobaciones consumen solo EDARSAHUB SQL.
- No duplicar facturas por modulo: todo CFDI vive en `dbo.Compras_DocumentosFiscales` y `dbo.Compras_DocumentosFiscalesDetalle`.

## Evidencia usada

- `dbo.Compras_DocumentosFiscales` ya tiene UUID, RFC emisor/receptor, totales, rutas XML/PDF y hashes.
- `dbo.Compras_DocumentosFiscalesDetalle` ya tiene conceptos del XML.
- `dbo.Compras_ConciliacionSAT` ya modela conciliacion fiscal sin requerir SAT live.
- `dbo.Proveedor_UsuariosPortal` ya permite identidad de usuario externo.
- `dbo.Finanzas_CxP_Sync` es la fuente CxP canonica para saldos.

## Decision de modelo

La factura fiscal no pertenece a Portal Proveedores, Caja, Viaticos ni Fondo. Pertenece al libro canonico de CFDI.

La diferencia entre flujos esta en el contexto:

- `PORTAL_PROVEEDOR`: proveedor externo carga o consulta CFDI ligados a pedido, requisito, OC, recepcion o CxP.
- `CAJA_CHICA`: usuario interno comprueba contra caja.
- `FONDO_REVOLVENTE`: usuario interno comprueba contra fondo fijo.
- `VIATICO`: usuario interno comprueba anticipo de viaje.
- `GASTO_POR_COMPROBAR`: usuario interno comprueba un importe entregado previamente.
- `REEMBOLSO`: usuario interno solicita reembolso posterior.

## Tablas nuevas propuestas

### `dbo.Compras_CFDI_RutasIngesta`

Configuracion canonica de carpetas de ingesta. Evita hardcodear rutas en backend.

Usos:

- registrar carpetas actuales del servidor por empresa/unidad;
- definir storage destino administrado por EDARSAHUB;
- soportar origen futuro `PORTAL_PROVEEDOR` o `TAB_COMPROBACION`;
- mantener la carpeta como bandeja de entrada, no como fuente funcional.

### `dbo.Compras_DocumentosFiscalesRelaciones`

Tabla puente canonica para relacionar un CFDI con su contexto sin duplicar la factura.

Contextos previstos:

- `ORDEN_COMPRA`
- `PEDIDO`
- `REQUISITO`
- `RECEPCION`
- `CXP`
- `COMPROBACION`
- `FONDO_REVOLVENTE`
- `VIATICO`
- `GASTO_POR_COMPROBAR`
- `REEMBOLSO`

### `dbo.Finanzas_Comprobaciones`

Encabezado financiero de caja, fondo, viatico, gasto por comprobar o reembolso.

Esta tabla no almacena facturas. Almacena el dinero entregado, comprobado, por reembolsar o por reintegrar.

Regla V1.0:

- no se entrega otro importe por comprobar si el usuario tiene una comprobacion abierta del mismo tipo/unidad.

### `dbo.Finanzas_ComprobacionesDocumentos`

Relaciona comprobaciones con CFDI canonicos ya existentes en `Compras_DocumentosFiscales`.

Permite que una misma comprobacion tenga varios proveedores/RFC sin duplicar registros fiscales.

## Portal Proveedores V1.0

Contrato actual:

- un proveedor puede tener solo un usuario activo en V1.0;
- `Proveedor_UsuariosPortal` conserva el modelo multiusuario futuro;
- login por RFC sigue siendo valido bajo la restriccion de un usuario activo por proveedor;
- el token mantiene `UsuarioPortalID` para bitacora y crecimiento posterior.

## Flujo CFDI V1.0

1. Configurar rutas en `Compras_CFDI_RutasIngesta`.
2. Job/manual ingestion lee XML/PDF desde carpetas autorizadas.
3. Parsear XML y calcular hash.
4. Insertar o actualizar metadata canonica en `Compras_DocumentosFiscales`.
5. Insertar conceptos en `Compras_DocumentosFiscalesDetalle`.
6. Relacionar CFDI con OC, recepcion, CxP o comprobacion mediante `Compras_DocumentosFiscalesRelaciones`.
7. Portal y Finanzas consultan solo SQL EDARSAHUB.

## Preparacion SAT posterior

V1.0 no consulta SAT. Las columnas existentes `EstatusSAT` y `FechaConsultaSAT` quedan para fases futuras.

La integracion futura SAT debe:

- correr como proceso controlado;
- guardar resultado en EDARSAHUB;
- no ser dependencia live de pantallas;
- auditar cambios de estatus y errores.

## Validaciones requeridas antes de ejecutar SQL

- `SELECT` de existencia real de tablas canonicas en EDARSAHUB.
- `SELECT` para detectar proveedores con mas de un usuario activo antes de crear el indice V1.0.
- Inventario de rutas reales de CFDI/XML visibles al host productivo.
- Revision DBA de indices filtrados y nombres de constraints.

## Migracion preparada

- `backend/database/migrations/20260722_002_cfdi_portal_comprobaciones_contract.sql`

No fue ejecutada.
