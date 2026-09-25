# RRR Gate 2 - Correccion DDL V2

## Fuente
RRR-GATE2B-FK-TYPE-PREFLIGHT-READONLY-V1-20260908: CERTIFIED_READ_ONLY, PASS, 100%, production_touched=false.

## Correcciones aplicadas
- ClienteID: uniqueidentifier -> int; FK dbo.Cliente_Catalogo(ClienteID).
- VentaID: uniqueidentifier -> bigint; FK dbo.Venta_Encabezado(VentaID).
- EmpresaID: uniqueidentifier -> int; FK dbo.Sistema_Empresas(EmpresaID).
- UsuarioCreacionID: uniqueidentifier -> int; FK dbo.Usuario_Catalogo(UsuarioID).
- UnidadID: removido del DDL V2 hasta resolver identidad canonica de unidad/sucursal mediante preflight dedicado.

## Estado
V2 sigue siendo DESIGN_ONLY / NOT_EXECUTED. No autoriza migracion hasta cerrar la identidad canonica de unidad/sucursal y certificar una version ejecutable no-Production.
