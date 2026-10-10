# EDARSA Logistics — Gate 3C Physical Schema Design Dossier

Estado: DESIGN DOSSIER ONLY — NO DDL / NO MIGRATION / NO RUNTIME

## 1. Base certificada

Este dossier parte exclusivamente de:
- Gate 2 Data & Integration Architecture certificado.
- Gate 3A Repository Schema Contract Validation certificado READ ONLY.
- Gate 3B SQL Schema Contract Validation certificado READ ONLY.

Hallazgos SQL confirmados:
- Existen los maestros BOS requeridos: Sistema_Empresas, Sistema_Sucursales, Unidades_Negocio, Gobierno_Persona, Gobierno_Documento*, Usuario_Catalogo, Cliente_Catalogo, Proveedor_Catalogo, Producto_Catalogo, Inventario_Almacenes, Inventario_Existencias, Inventario_Movimientos, Inventario_MovimientosDetalle.
- Las convenciones de FK reales referencian esos owners por sus PK canonicas.
- Existen familias maduras Compras_*, Finanzas_*, Gobierno_Documento*, Sistema_RBAC_* y Usuario_RBAC_*.
- Existe al menos infraestructura relacionada con mantenimiento de activos, por ejemplo ActivoFijo_PlanesMantenimiento.
- Los candidatos exactos Logistica_* de Gate 2 no colisionan actualmente con tablas existentes: collision_exact row_count=0.
- Produccion no fue tocada.

## 2. Decisiones fisicas permitidas en este dossier

Se permite definir candidatos de tablas, columnas, PK/FK, indices, unique constraints, estados, claves de idempotencia, auditoria y referencias.
No se permite crear DDL ejecutable ni migraciones.

## 3. Convencion de nombres

Prefijo candidato: Logistica_.

El prefijo queda aceptado como candidato porque Gate 3B no encontro colisiones exactas en los nombres propuestos. Antes de una migracion real, el gate de DDL debe volver a verificar colision exacta contra el HEAD/SQL vigente.

## 4. Tablas candidatas y ownership

### Logistica_Ordenes
PK: OrdenLogisticaID bigint.
Columnas conceptuales:
- OrdenLogisticaID bigint
- PublicUUID uniqueidentifier
- EmpresaID int
- UnidadNegocioID int
- SucursalID int nullable
- ClienteID int nullable
- ProveedorID int nullable
- TipoOrden varchar
- ModoServicio varchar
- VentanaInicioUTC datetime2
- VentanaFinUTC datetime2
- FechaOperacion date
- Estado varchar
- IdempotencyKey varchar
- CorrelationID uniqueidentifier nullable
- UsuarioAltaID int
- FechaAltaUTC datetime2
- FechaModificacionUTC datetime2 nullable

FK candidatas:
- EmpresaID -> Sistema_Empresas.EmpresaID
- SucursalID -> Sistema_Sucursales.SucursalID
- UnidadNegocioID -> Unidades_Negocio.id
- ClienteID -> Cliente_Catalogo.ClienteID
- ProveedorID -> Proveedor_Catalogo.ProveedorID
- UsuarioAltaID -> Usuario_Catalogo.UsuarioID

Unique candidato:
- EmpresaID + IdempotencyKey

### Logistica_Envios
PK: EnvioID bigint.
Refs: OrdenLogisticaID, ClienteID/ProveedorID solo cuando aplique.
No duplica stock ni producto maestro.
Detalle de unidades logisticas puede vivir en Logistica_EnviosDetalle en gate posterior si se confirma necesidad.

### Logistica_Viajes
PK: ViajeID bigint.
Columnas: EmpresaID, OrdenLogisticaID nullable, FechaOperacion, InicioPlaneadoUTC, InicioRealUTC, FinRealUTC, Estado, IdempotencyKey, CorrelationID, version/auditoria.
Unique candidato: EmpresaID + IdempotencyKey.

### Logistica_Paradas
PK: ParadaID bigint.
FK: ViajeID.
Columnas: Secuencia, TipoParada, VentanaInicioUTC, VentanaFinUTC, LlegadaUTC, SalidaUTC, Resultado, ReferenciaUbicacionTipo, ReferenciaUbicacionID, GeofenceRef nullable.
No crea maestro paralelo de direcciones.

### Logistica_AsignacionesDespacho
PK: AsignacionDespachoID bigint.
FK: ViajeID.
Refs: MedioTransportePerfilOperativoID y PersonaOperativaPerfilID/TripulacionID segun modo.
Versionado temporal con VigenteDesdeUTC/VigenteHastaUTC y auditoria.

### Logistica_MediosTransportePerfilOperativo
PK: MedioTransportePerfilOperativoID bigint.
Debe referenciar el owner canonico de activo que el Gate DDL confirme exactamente.
Es el perfil logistico comun y NO presupone transporte carretero.
ModoTransporte candidato: ROAD | RAIL | AIR | MARITIME | INLAND_WATERWAY.
Servicio candidato: CARGO | PASSENGER | MIXED | SPECIALIZED.
Atributos comunes: capacidad, disponibilidad, estado operacional, operador/owner refs, telemetria cuando aplique y restricciones regulatorias.
No duplica el activo corporativo.

Extensiones por modo, solo cuando el dato sea realmente especifico:
- ROAD: Logistica_MedioRoadPerfil (tractocamion, camion, autobus, van, auto, moto, remolque).
- RAIL: Logistica_MedioRailPerfil (locomotora, vagon de carga, coche de pasajeros, composicion/consist refs).
- AIR: Logistica_MedioAirPerfil (avion, helicoptero u otra aeronave; carga/pasajeros/mixta/especializada).
- MARITIME / INLAND_WATERWAY: Logistica_MedioMaritimePerfil (buque, barco, ferry, remolcador, embarcacion fluvial y clases especializadas).

No modelar locomotoras, aeronaves o buques como vehiculos carreteros.

### Logistica_ConductoresPerfilOperativo
PK: ConductorPerfilOperativoID bigint.
FK: PersonaID -> Gobierno_Persona.PersonaID.
No duplica nombre, CURP, RFC ni identidad de persona.
Licencias/evidencias referencian Gobierno_Documento.

### Logistica_AlmacenesPerfilOperativo
PK: AlmacenPerfilOperativoID bigint.
FK: AlmacenID -> Inventario_Almacenes.AlmacenID.
Solo dock/staging/cross-dock/picking/cutoffs/scheduling.

### Logistica_OrdenesMantenimiento
PK: OrdenMantenimientoID bigint.
Refs: perfil operativo del medio/activo, ProveedorID nullable, UsuarioAltaID.
Partes se consumen por Inventarios.
Evidencias por Gobierno_Documento.
No crea existencia paralela.

### Logistica_PartesInstaladas
PK: ParteInstaladaID bigint.
Refs: ProductoID -> Producto_Catalogo.ProductoID, MovimientoInventarioID -> Inventario_Movimientos.
Guarda instalacion/retiro/posicion/fechas/medio o activo.
No guarda stock.

### Logistica_LlantasCicloVida
PK: LlantaCicloVidaID bigint.
Refs: ProductoID, MovimientoInventarioID, vehiculo/activo.
Guarda serial si aplica, posicion, instalacion, retiro, kilometraje/horas, causa retiro.

### Logistica_Combustible
PK: CombustibleID bigint.
Refs: medio/activo, ProveedorID, DocumentoID nullable, UsuarioID.
Montos con CurrencyCode/MonedaID canonico a definir por Gate DDL segun catalogo vigente.
No contabiliza por si misma.

### Logistica_CargaEnergia
Mismo ownership que combustible para EV/energia.

### Logistica_DispositivosTelemetria
PK: DispositivoTelemetriaID bigint.
Refs: medio/activo.
Proveedor y external device id tipados.
Unique candidato: ProviderID + ExternalDeviceID.

### Logistica_EventosTelemetria
PK: EventoTelemetriaID bigint.
Solo eventos normalizados de negocio.
Unique candidato: ProviderID + ExternalEventID o hash idempotente.
Raw high-frequency retention fuera del modelo administrativo principal si corresponde.

### Logistica_TarifasAcuerdos
PK: TarifaAcuerdoID bigint.
Refs: ClienteID o ProveedorID, EmpresaID, currency, vigencias, service mode.
No duplica presupuesto/factura/CxP/CxC.

### Logistica_TarifasReglas
PK: TarifaReglaID bigint.
FK: TarifaAcuerdoID.
Reglas parametrizadas, sin hardcode por cliente/empresa.

### Logistica_Incidentes
PK: IncidenteID bigint.
Refs: ViajeID nullable, PersonaID nullable, medio/activo nullable, DocumentoID nullable.
Estado auditable.

### Logistica_Siniestros
PK: SiniestroID bigint.
FK/logical ref: IncidenteID.
Settlement/contabilidad en Finanzas.

### Logistica_Cumplimiento
PK: CumplimientoID bigint.
Refs tipadas a persona/activo/empresa.
Jurisdiccion y pais parametrizados.

### Logistica_ServiciosPasajeros
PK: ServicioPasajerosID bigint.
Separado de Freight.
Refs: ViajeID, EmpresaID, unidad.
Privacidad/RBAC reforzado.

### Logistica_ManifiestosPasajeros
PK: ManifiestoPasajeroID bigint.
FK: ServicioPasajerosID.
PersonaID nullable cuando exista identidad BOS.
No almacenar PII duplicada salvo minima evidencia operacional justificada.

## 5. Tabla de relaciones documentales

No crear Logistica_Documentos.
Usar Gobierno_Documento como owner.

Si el modelo de Gobierno no permite una relacion generica suficiente, candidato permitido:
- Logistica_EntidadesDocumentos

Columnas:
- EntidadDocumentoID
- EntidadTipo
- EntidadID
- DocumentoID -> Gobierno_Documento.DocumentoID
- RelacionTipo
- FechaAltaUTC
- UsuarioAltaID

Esta tabla solo relaciona; no almacena archivo ni metadata documental duplicada.

## 6. Estados

No hardcodear estados dispersos.
Gate DDL debe decidir si reutiliza catalogos BOS existentes o crea catalogos Logistica_* por bounded context.

Candidatos conceptuales:
- Orden: DRAFT, PLANNED, READY, IN_PROGRESS, COMPLETED, CANCELLED, EXCEPTION.
- Viaje: PLANNED, READY, DISPATCHED, IN_PROGRESS, ARRIVED, COMPLETED, CANCELLED, EXCEPTION.
- Parada: PENDING, ARRIVED, SERVICED, FAILED, SKIPPED.
- Mantenimiento: OPEN, APPROVED, IN_PROGRESS, WAITING_PARTS, COMPLETED, CANCELLED.

No se autoriza DDL de estos catalogos en este gate.

## 7. Indices conceptuales

Indices candidatos por:
- EmpresaID + FechaOperacion
- EmpresaID + Estado + FechaOperacion
- FK frecuentes
- idempotency keys
- external provider keys
- ViajeID + Secuencia para paradas
- vehiculo + rango temporal para telemetria/eventos
- PersonaID/medio de transporte para compliance activo

Evitar sobreindexar antes de workloads reales.

## 8. Auditoria

Todas las mutaciones futuras deben ser auditables.
Campos base candidatos:
- FechaAltaUTC
- UsuarioAltaID
- FechaModificacionUTC
- UsuarioModificacionID nullable
- RowVersion/timestamp si patron BOS lo confirma
- CorrelationID cuando aplique

## 9. Timezone y FechaOperacion

- UTC para timestamps tecnicos.
- FechaOperacion derivada por helper canonico.
- Timezone no hardcodeado; usar configuracion de unidad/empresa.
- Multi-pais y DST soportados por configuracion.

## 10. Idempotencia

Unique scope recomendado:
- EmpresaID + IdempotencyKey por agregado.
- ProviderID + ExternalEventID para integraciones cuando exista.
- Hash/canonical key para eventos sin external id.

No reutilizar IDs externos como PK.

## 11. Boundaries no negociables

Inventarios:
- stock y movimientos siguen en Inventario_*.

Finanzas:
- pago, CxP/CxC, factura, contabilidad y presupuesto siguen en Finanzas_*.

Documentos:
- archivos/evidencias siguen en Gobierno_Documento*.

Usuarios/RBAC:
- Usuario_* / Sistema_RBAC_*.

Mobile:
- Field/Mobile Platform.

Primety:
- UX.

Logistics:
- solo semantica y estado operacional logistico.

## 12. Prohibiciones

No DDL.
No migration scripts.
No endpoints.
No ORM/runtime models.
No Mongo.
No scheduler paralelo.
No notification dispatcher paralelo.
No document manager paralelo.
No finance ledger paralelo.
No product/customer/provider/warehouse masters paralelos.
No crecimiento de core.

## 13. Pendientes que deben cerrar antes de DDL

- Confirmar owner fisico exacto del activo corporativo y PK a referenciar para ROAD/RAIL/AIR/MARITIME/INLAND_WATERWAY.
- Confirmar catalogo canonico de moneda/pais/timezone a usar.
- Confirmar si Gobierno Documental ya soporta relacion generica suficiente o si Logistica_EntidadesDocumentos es realmente necesaria.
- Confirmar convencion RowVersion/auditoria a reutilizar.
- Confirmar si estados deben usar catalogos existentes o nuevos catalogos de dominio.
- Confirmar estrategia fisica para raw telematics fuera de reporting administrativo.
- Confirmar FK fisica vs logical reference para cada frontera desacoplada.

## 14. Contrato multimodal mundial

El agregado de ejecucion debe soportar Journey/Trip compuesto por Legs.
Cada Leg declara:
- Mode: ROAD | RAIL | AIR | MARITIME | INLAND_WATERWAY.
- Purpose: CARGO | PASSENGER | MIXED | SPECIALIZED.
- OriginNodeRef / DestinationNodeRef.
- ScheduledDepartureUTC / ScheduledArrivalUTC.
- ActualDepartureUTC / ActualArrivalUTC.
- Carrier/OperatorRef.
- MedioTransportePerfilOperativoID nullable segun modelo de operacion.
- Estado e idempotencia.

Un mismo servicio puede encadenar, sin crear ordenes independientes:
ROAD -> RAIL -> MARITIME -> RAIL -> ROAD
o
ROAD -> AIR -> ROAD.

Nodos/terminales especializados deben extender una referencia comun de nodo logistico, sin duplicar maestros geograficos:
- ROAD terminal / patio / dock.
- RAIL station / yard / terminal.
- AIR airport / cargo terminal.
- MARITIME port / terminal.
- INLAND_WATERWAY port / dock.

Recursos humanos:
- ROAD puede usar conductor.
- RAIL usa personal operativo/tripulacion ferroviaria segun rol.
- AIR usa tripulacion/licencias/roles aeronauticos.
- MARITIME usa tripulacion/licencias/roles maritimos.
La identidad siempre referencia Gobierno_Persona; Logistics solo mantiene perfil, habilitaciones y asignaciones operativas.

Carga:
- Shipment sigue siendo comun.
- Container, pallet, ULD, wagon allocation, hold/deck allocation u otras unidades son extensiones logisticas, no Producto_Catalogo paralelo.

Pasajeros:
- PassengerService y manifest permanecen separados de Freight pero comparten Journey/Leg, nodos, scheduling y execution.
- PII minima; Gobierno_Persona cuando exista identidad BOS.

Mantenimiento:
- MaintenanceWorkOrder debe aceptar cualquier medio/activo.
- Llantas son extension ROAD/ciertos equipos, no requisito de AIR/RAIL/MARITIME.
- Parts usa Producto_Catalogo + Inventario_* para todos los modos.

Energia:
- Fuel/Energy es generalizable: diesel/gasolina/Jet fuel/marine fuel/electricidad u otras energias parametrizadas.
- No hardcodear combustible carretero.

Telemetria:
- Modelo normalizado acepta GPS/AVL/rail telemetry/ADS-B u otros feeds aeronauticos/AIS u otros feeds maritimos mediante adapters; vendor payload nunca es modelo canonico.

Regulacion:
- Jurisdiccion, documentos, licencias, certificados e inspecciones son parametrizados por pais y modo.
- No hardcodear regulacion mexicana como modelo global.

## 15. Exit criteria

PHYSICAL_SCHEMA_DOSSIER_DEFINED=YES
MULTIMODAL_FROM_ORIGIN=YES
ROAD_SUPPORTED=YES
RAIL_CARGO_PASSENGER_SUPPORTED=YES
AIR_CARGO_PASSENGER_SUPPORTED=YES
MARITIME_CARGO_PASSENGER_SUPPORTED=YES
INLAND_WATERWAY_SUPPORTED=YES
JOURNEY_LEG_MODEL=REQUIRED
ROAD_ONLY_ASSUMPTIONS=0
EXACT_DDL_EXECUTED=NO
MIGRATIONS_CREATED=NO
ENDPOINTS_CREATED=NO
RUNTIME_CODE_CHANGED=NO
EXACT_LOGISTICA_COLLISIONS_AT_GATE3B=0
CANONICAL_MASTERS_REUSED=YES
INVENTORY_OWNER_PRESERVED=YES
FINANCE_OWNER_PRESERVED=YES
DOCUMENT_OWNER_PRESERVED=YES
RBAC_OWNER_PRESERVED=YES
FIELD_MOBILE_OWNER_PRESERVED=YES
PRIMETY_AS_UX_ONLY=YES
MONGO_SOURCE_OF_TRUTH=0
PRODUCTION_TOUCHED=NO
