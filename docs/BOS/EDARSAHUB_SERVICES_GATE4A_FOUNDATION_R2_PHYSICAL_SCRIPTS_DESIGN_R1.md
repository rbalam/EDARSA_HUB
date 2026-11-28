# EDARSAHUB Services - Gate 4A Foundation R2 Physical Scripts Design R1

## Evidencia de tipos certificada
- Gobierno_Persona.PersonaID = bigint identity
- Proveedor_Catalogo.ProveedorID = int identity
- Cliente_Catalogo.ClienteID = int identity
- Sistema_Empresas.EmpresaID = int identity
- Sistema_Sucursales.SucursalID = int identity
- Usuario_Catalogo.UsuarioID = int identity
- Gobierno_Documento.DocumentoID = bigint identity
- Maestro real de unidad de negocio identificado: dbo.Unidades_Negocio

## Alcance
R2 agrega solamente:
- Services_Providers
- Services_ProviderSpecialties
- Services_Credentials

No ejecuta SQL.

## Modelo Provider
Provider es un rol operativo:
- INDIVIDUAL -> Gobierno_Persona
- ORGANIZATION -> Proveedor_Catalogo
- FACILITY -> Proveedor_Catalogo externo o Sistema_Empresas interno

No copia PII ni datos maestros.

## Auditoria temporal
Se alinea al precedente de Gobierno_Persona usando FechaAlta/FechaActualizacion y SYSUTCDATETIME para instantes tecnicos. FechaOperacion se reserva para hechos operativos posteriores; no se fuerza en catalogos maestros.

## Pendiente
Antes de ejecución real:
- certificar writer canonico Development;
- certificar environment development;
- backup/restore point;
- auditoria READ_ONLY de estos scripts;
- validar que la restriccion UNIQUE por Persona/Proveedor/Empresa coincide con la cardinalidad de negocio deseada;
- validar naming contra el resto de Services antes de ampliar mas tablas.

## Siguiente paso
Certificacion READ_ONLY de R2. No se autoriza migracion aun.
