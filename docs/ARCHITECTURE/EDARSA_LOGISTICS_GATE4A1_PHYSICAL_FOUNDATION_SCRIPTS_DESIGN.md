# EDARSA Logistics — Gate 4A1 Physical Foundation Scripts Design

Estado: SCRIPTS MATERIALIZED — NOT EXECUTED

## Base certificada
- Gate 3C multimodal: CERTIFIED.
- Gate 4A0 PRE-DDL exact contract audit: CERTIFIED_READ_ONLY / PASS / 100%.
- Produccion no tocada.

## Tipos canonicos usados
- Sistema_Empresas.EmpresaID = int.
- Sistema_Sucursales.SucursalID = int.
- Unidades_Negocio.id = uniqueidentifier.
- Usuario_Catalogo.UsuarioID = int.
- Gobierno_Persona.PersonaID = bigint.
- Cliente_Catalogo.ClienteID = int.
- Proveedor_Catalogo.ProveedorID = int.
- Producto_Catalogo.ProductoID = int.
- Inventario_Almacenes.AlmacenID = int.
- Gobierno_Documento.DocumentoID = bigint.
- ActivoFijo_Activos.ActivoID = bigint.

## Alcance de este primer par
Forward/rollback fisico, versionado y NO ejecutado para la foundation minima multimodal:
- Logistica_Cat_ModosTransporte.
- Logistica_Cat_PropositosServicio.
- Logistica_Ordenes.
- Logistica_MediosTransportePerfilOperativo.
- Logistica_Viajes.
- Logistica_ViajeLegs.

El objetivo es fijar el spine comun Order -> Journey/Trip -> Legs y el medio de transporte multimodal antes de subdominios ROAD/RAIL/AIR/MARITIME.

## Multimodal
Modos sembrados:
- ROAD
- RAIL
- AIR
- MARITIME
- INLAND_WATERWAY

Propositos:
- CARGO
- PASSENGER
- MIXED
- SPECIALIZED

## Protecciones
- aborta si DB_NAME() no es EDARSAHUB;
- HRLectura no puede actuar como writer;
- XACT_ABORT + transaccion + TRY/CATCH;
- CREATE solo cuando el objeto no existe;
- FK a maestros BOS exactos;
- idempotencia unique por Empresa/Viaje;
- rollback fail-closed si ya existe data operacional;
- no Mongo;
- no masters paralelos;
- no ejecucion en este Gate.

## Fuera de alcance deliberadamente
Aun NO se materializan:
- shipments/envios detallados;
- pasajeros/manifiestos;
- perfiles ROAD/RAIL/AIR/MARITIME especificos;
- nodos/terminales/puertos/aeropuertos/estaciones;
- maintenance;
- parts/tires;
- fuel/energy;
- telematics;
- rates;
- compliance;
- incident/claims;
- document relation bridge;
- RBAC seed;
- endpoints/backend/frontend.

Estos deben entrar en subgates posteriores para mantener cambios quirurgicos y reversibles.

## Siguiente Gate
Certificar los dos scripts por inspeccion READ_ONLY:
- sintaxis/estructura;
- ausencia de DML sobre datos existentes salvo seeds catalogo propios;
- FK exactas;
- orden forward/rollback;
- idempotencia;
- prohibicion de ejecucion.

Solo despues podra considerarse un Gate de ejecucion controlada fuera de Produccion.
