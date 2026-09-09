# RRR Gate 2 - DDL V3 Final Design

## Contratos externos certificados
- Cliente: dbo.Cliente_Catalogo(ClienteID int).
- Empresa: dbo.Sistema_Empresas(EmpresaID int).
- Unidad de negocio: dbo.Unidades_Negocio(id uniqueidentifier).
- Venta: dbo.Venta_Encabezado(VentaID bigint).
- Usuario: dbo.Usuario_Catalogo(UsuarioID int).
- Sucursal fisica: dbo.Sistema_Sucursales(SucursalID int), dimension distinta de unidad de negocio.

## Evidencia de unidad
RRR Gate 2D R2B certifico PK dbo.Unidades_Negocio(id). Gate 2D R2C certifico patrones FK reales desde Comercial, Compras, Economia y Finanzas hacia dbo.Unidades_Negocio(id). La migracion canonica existente de Compras utiliza unidad_negocio_pk uniqueidentifier y FK a dbo.Unidades_Negocio(id).

## Decision
RRR_Eventos incorpora UnidadNegocioID uniqueidentifier NULL con FK FK_RRR_Eventos_UnidadNegocio -> dbo.Unidades_Negocio(id). No usa SucursalID como identidad principal de unidad.

## Estado
V3 es candidato final de diseño. DESIGN_ONLY / NOT_EXECUTED. No autoriza por si mismo ejecucion SQL. La autorizacion no-Production requiere un job separado de certificacion final de Gate 2. Production permanece prohibida.
