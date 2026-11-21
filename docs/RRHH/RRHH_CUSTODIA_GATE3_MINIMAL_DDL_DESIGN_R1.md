# RRHH Custodia - Gate 3 Minimal DDL Design R1

## Estado
DDL mínimo materializado como artefacto de migración. Este Gate NO ejecuta SQL. Producción=false.

## Entrada certificada
Gate 2B y Gate 2C terminaron CERTIFIED_READ_ONLY / PASS / 100%, sin archivos modificados y sin tocar Producción.

Contratos:
- RH_Colaboradores_Expediente.ColaboradorID int
- RH_Cat_Puestos.PuestoID int
- Producto_Catalogo.ProductoID int
- ActivoFijo_Activos.ActivoID bigint
- Sistema_Empresas.EmpresaID int
- Unidades_Negocio.id uniqueidentifier
- Sistema_Sucursales.SucursalID int
- Usuario_Catalogo.UsuarioID int
- Gobierno_Documento.DocumentoID bigint
- RH_Nomina_Detalle.NominaDetalleID int

## Hallazgo de variantes
Gate 2C encontró Producto_Presentaciones y Sistema_TiposVariantes, pero no un contrato canónico Producto->talla/color. Por tanto este Gate no crea RH_Uniforme_Tallas ni tablas de variantes. La política de uniforme referencia ProductoID; una futura normalización de talla/color deberá resolverse en Producto mediante gate dedicado, no en RRHH.

## Objetos nuevos mínimos
- Custodia_Recurso
- Custodia_Resguardo
- Custodia_Movimiento
- Custodia_Devolucion
- Custodia_Incidencia
- Custodia_CargoPropuesto
- RH_UniformePolitica
- RH_UniformePoliticaDetalle

## Fronteras
Custodia no sustituye Inventarios, Activo Fijo, Gobierno Documental, RBAC, RRHH ni Nómina.

## Responsivas
Custodia_Resguardo.DocumentoResponsivaID referencia Gobierno_Documento.DocumentoID. Versiones y kardex permanecen en Gobierno Documental.

## Nómina
Custodia_CargoPropuesto es propuesta/autorización de negocio. NominaDetalleID solo se relaciona cuando Nómina canónica materialice el concepto. Custodia no descuenta por sí sola.

## Siguiente Gate
GATE 3B = SQL DDL PREFLIGHT READ_ONLY sobre Desarrollo: validar colisiones de nombres, tipos de FK, permisos DDL e inexistencia de objetos Custodia. Solo tras PASS se publica un job separado SQL_MIGRATION_DEVELOPMENT_MODE.
