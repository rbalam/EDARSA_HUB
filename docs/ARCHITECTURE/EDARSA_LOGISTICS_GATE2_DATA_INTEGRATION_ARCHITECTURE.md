# EDARSA Logistics — Gate 2 Data & Integration Architecture

Estado: DESIGN ONLY — NO RUNTIME IMPLEMENTATION

## 1. Alcance

Gate 2 transforma el contrato canonico de Gate 1C en arquitectura de datos e integracion para EDARSA Logistics.

No crea ni ejecuta:
- tablas;
- migraciones;
- endpoints;
- jobs;
- UI;
- adapters productivos;
- despliegues;
- cambios en Produccion.

EDARSAHUB SQL Server permanece como cerebro y fuente canonica. Gate 2 solo define estructuras conceptuales, ownership, referencias, idempotencia, eventos, retencion e integracion.

## 2. Principios heredados obligatorios

- SHARED_CAPABILITY_FIRST.
- ZERO_RECAPTURE.
- ONE CAPABILITY, ONE OWNER, MANY CONSUMERS.
- Primety = experiencia/UX de campo.
- BOS Field/Mobile Platform = owner tecnico transversal mobile/offline/device services.
- Logistics = semantica de dominio logistica.
- BOS/SQL = autoridad canonica.
- Mongo no puede ser runtime source of truth ni fallback.
- No hardcodear empresa, unidad, sucursal, IDs, alias, timezone, moneda, pais ni proveedor.
- No crecer backend/core con logica vertical Logistics.
- No duplicar clientes, proveedores, productos, almacenes, inventarios, documentos, usuarios, RBAC, scheduler, communications ni finanzas.

## 3. Bounded contexts internos de Logistics

- logistics_orders
- freight
- passenger_mobility
- fleet
- dispatch
- trips
- shipments
- delivery
- warehouse_ops
- maintenance
- parts_tires_lifecycle
- fuel_energy
- telematics
- rates
- safety_compliance_claims
- international_multimodal

Implementacion futura inicial recomendada: un solo modulo cohesionado `backend/modules/logistics/` con subdominios internos, no microservicios prematuros.

## 4. Agregados conceptuales y ownership

### 4.1 LogisticsOrder
Owner: logistics_orders.
Source of truth: Logistics SQL.
Proposito: representar la necesidad logistica comercial/operativa sin duplicar pedido/venta/compra.

Campos conceptuales:
- logistics_order_id
- external_reference nullable
- company_id -> Sistema_Empresas
- business_unit_id -> Unidades_Negocio
- branch_id nullable -> Sistema_Sucursales
- customer_id nullable -> Cliente_Catalogo
- provider_id nullable -> Proveedor_Catalogo
- order_type
- service_mode
- requested_window_start_utc / requested_window_end_utc
- operational_date / FechaOperacion segun owner
- origin_ref / destination_ref
- status
- idempotency_key
- created_by_user_id -> Usuario_Catalogo
- created_at_utc / updated_at_utc

No contiene maestro de cliente/proveedor/producto.

### 4.2 FreightShipment
Owner: freight/shipments.
Source of truth: Logistics SQL.
Referencias: LogisticsOrder, Producto_Catalogo, Cliente_Catalogo, Proveedor_Catalogo, Gobierno_Documento.
Incluye unidades logisticas, peso, volumen, temperatura/restricciones cuando apliquen.
No representa stock.

### 4.3 Trip
Owner: trips.
Source of truth: Logistics SQL.
Referencias: LogisticsOrder, VehicleOperationalProfile, DriverOperationalProfile.
Campos conceptuales:
- trip_id
- company_id
- route_plan_version
- planned_start_utc
- actual_start_utc nullable
- actual_end_utc nullable
- FechaOperacion
- status
- idempotency_key
- correlation_id

### 4.4 Stop
Owner: trips/delivery/passenger_mobility segun tipo.
Source of truth: Logistics SQL.
Referencias: Trip, Cliente_Direcciones u otra referencia canonica de ubicacion cuando exista.
Incluye secuencia, ventana, geofence_ref, planned/actual timestamps y outcome.
No crea un maestro paralelo de direcciones.

### 4.5 DispatchAssignment
Owner: dispatch.
Source of truth: Logistics SQL.
Asocia trip + vehicle + driver + trailer/equipment cuando aplique.
Debe ser temporal, versionado y auditable.

### 4.6 VehicleOperationalProfile
Owner: fleet.
Source of truth: Logistics SQL solo para atributos operativos.
Referencia maestra: Activo Fijo cuando corresponda.
Nunca duplica identidad corporativa del activo.
Campos operativos candidatos: vehicle_class, capacity, telematics_binding, availability_state, odometer_source_policy.

### 4.7 DriverOperationalProfile
Owner: fleet/passenger_mobility.
Source of truth: Logistics SQL para atributos operativos.
Referencia maestra: Gobierno_Persona.
Licencias/documentos deben referenciar Gobierno Documental, no blob propio.

### 4.8 WarehouseOperationalProfile
Owner: warehouse_ops.
Referencia maestra: Inventario_Almacenes.
Solo agrega capacidades Logistics: dock, staging, cross-dock, picking model, cutoffs, dock schedule.

### 4.9 MaintenanceWorkOrder
Owner: maintenance.
Source of truth: Logistics SQL.
Referencias: asset/vehicle, provider/workshop, Gobierno_Documento, Inventarios.
Consumir refacciones via Inventarios; no mantener existencia paralela.

### 4.10 InstalledPart / TireLifecycle
Owner: parts_tires_lifecycle.
Source of truth: Logistics SQL para instalacion, posicion, uso y retiro.
Producto/stock: Producto_Catalogo + Inventarios.
Movimiento fisico: Inventario_Movimientos.

### 4.11 FuelTransaction / EnergyCharge
Owner: fuel_energy.
Source of truth: Logistics SQL para hecho operativo.
Referencias: vehicle, provider, user, document/evidence.
Settlement/accounting: Finanzas BOS.

### 4.12 TelematicsDeviceBinding / TelematicsBusinessEvent
Owner: telematics.
Source of truth: Logistics SQL normalizado.
Raw vendor stream no se convierte automaticamente en fuente de verdad.
Debe existir adapter por proveedor.
Retencion diferenciada:
- raw/high-frequency: corta y parametrizable;
- normalized business events: larga segun politica/auditoria.

### 4.13 RateAgreement / RateRule
Owner: rates.
Source of truth: Logistics SQL.
Referencias: Cliente_Catalogo / Proveedor_Catalogo, country, currency, service mode.
No duplica presupuesto, factura, CxP o CxC.

### 4.14 Incident / Claim / ComplianceRequirement
Owner: safety_compliance_claims.
Source of truth: Logistics SQL para expediente operativo.
PII/documentos: Gobierno/Gobierno Documental segun corresponda.
Settlement: Finanzas.

### 4.15 PassengerService / PassengerManifest
Owner: passenger_mobility.
Source of truth: Logistics SQL.
Debe separar datos de pasajeros de carga.
Privacidad reforzada, minima retencion y RBAC especifico.
Identidad de persona solo por referencia canonica cuando exista.

## 5. Convenciones de claves

### 5.1 Identidad interna
Cada agregado nuevo debe usar PK tecnica estable y no reutilizar IDs de sistemas externos como PK.

### 5.2 Idempotencia
Toda operacion susceptible de retry debe tener idempotency_key estable y scoped por owner/empresa.

Ejemplos:
- create logistics order;
- dispatch trip;
- capture POD;
- field voice/photo submit;
- ingest telematics event;
- fuel import;
- provider callback.

### 5.3 Correlacion
Eventos y workflows deben transportar correlation_id / causation_id cuando exista infraestructura compatible.

### 5.4 Referencias BOS
Usar FK fisica cuando la frontera y deployment lo permitan; logical reference tipada cuando el owner este desacoplado.
No copiar nombre/alias como identidad.

## 6. Multiempresa / multipais / multimoneda / timezone

Cada agregado que tenga alcance empresarial debe guardar la referencia canonica de empresa/unidad correspondiente.

- timestamps tecnicos: UTC;
- experiencia de usuario: timezone de la unidad/empresa configurada;
- FechaOperacion: helper canonico existente cuando aplique;
- moneda: referencia/codigo canonico parametrizado;
- pais: referencia canonica, nunca inferencia fija de Mexico;
- reglas regulatorias: por pais/jurisdiccion.

## 7. Offline / Field-Mobile contract

Toda escritura mobile/offline usa el envelope canonico `edarsahub.bos-mobile-operation.v1`.

Server outcomes:
- ACCEPT
- REJECT
- CONFLICT
- RETRY
- REQUIRES_REVIEW

Prohibido generic last-write-wins en:
- inventarios;
- dinero;
- dispatch sensible;
- cierre de viaje;
- POD;
- incidentes;
- cambios auditables.

Primety solo presenta la UX; el Field/Mobile Platform administra cache/outbox/inbox/sync/device services.

## 8. AI-assisted field operations

Patron canonico:

```text
capture
 -> shared processing
 -> proposal
 -> human confirmation cuando corresponda
 -> domain command
 -> canonical fact
```

Ejemplos:
- voz: "cliente cerrado" -> propuesta DeliveryAttempted(reason=CLOSED) -> confirmacion -> hecho.
- foto de dano -> AI propone damage classification -> usuario confirma -> Incident.
- OCR ticket combustible -> AI extrae datos -> usuario confirma -> FuelTransaction.

IA no modifica directamente hechos criticos sin policy/autorizacion.

## 9. Eventos y contratos de integracion

Gate 2 define eventos conceptuales, no un bus nuevo.

### Core Logistics
- TransportOrderCreated
- ShipmentReady
- TripPlanned
- TripDispatched
- TripStarted
- StopArrived
- DeliveryAttempted
- DeliveryCompleted
- PODCaptured
- TripCompleted

### Mobility
- PassengerBoarded
- PassengerDroppedOff

### Fleet / Maintenance
- MaintenanceRequested
- PartRequested
- InventoryMovementCompleted
- PartInstalled
- TireInstalled
- VehicleFaultDetected

### Fuel / Telematics
- FuelCaptured
- EnergyChargeCaptured
- GeofenceEntered
- ETAChanged
- OdometerUpdated

### Safety
- IncidentReported
- ClaimOpened
- ComplianceExpired

### Field shared capabilities
- FieldVoiceCaptured
- VoiceIntentProposed
- VoiceIntentConfirmed
- PhotoEvidenceCaptured

Cada evento debe definir en Gate posterior:
- producer;
- schema version;
- idempotency;
- partition/scoping;
- consumers;
- retry/DLQ strategy usando infraestructura existente si aplica;
- audit.

## 10. Integraciones externas

Todo proveedor externo entra por adapter/capability boundary.

Categorias:
- GPS/telematics;
- mapping/routing;
- carriers;
- parcel networks;
- fuel/energy providers;
- tolls;
- workshops;
- insurance;
- customs/ports/air/rail providers;
- future ERP/TMS.

Reglas:
- vendor payload != canonical model;
- secrets en Secret Manager/configuracion canonica;
- provider IDs se almacenan como external references, nunca PK;
- retries idempotentes;
- raw payload retention limitada y configurable;
- no LIVE vendor DB como fuente de dashboards administrativos.

## 11. Inventarios / WMS boundary

BOS Inventarios mantiene:
- Producto_Catalogo;
- Inventario_Almacenes;
- Inventario_Existencias;
- Inventario_Movimientos;
- Inventario_MovimientosDetalle.

Logistics warehouse_ops agrega:
- dock;
- staging;
- put-away;
- picking;
- packing;
- loading;
- cross-dock;
- wave/task orchestration;
- yard/dock scheduling.

Cualquier entrada/salida que afecte stock termina en el owner Inventarios.

## 12. Finanzas boundary

Logistics puede originar facts:
- freight charge;
- carrier payable fact;
- toll;
- fuel;
- workshop cost;
- claim cost;
- billable service.

Finanzas posee:
- autorizacion financiera;
- CxP/CxC;
- bancos;
- pago;
- factura;
- contabilidad;
- presupuesto.

No crear subledger financiero paralelo dentro de Logistics.

## 13. Gobierno Documental boundary

Fotos, firmas, PDFs, licencias, PODs, evidencias y documentos regulatorios deben usar Gobierno_Documento* como owner documental.

Logistics conserva:
- semantic_relation_type;
- logistics_entity_type;
- logistics_entity_id;
- document_id;
- business metadata minima.

## 14. Seguridad / privacidad

- RBAC siempre desde BOS.
- Scope obligatorio Empresa/Unidad/almacen cuando aplique.
- Passenger Mobility: acceso minimo necesario.
- Location/geolocation: finalidad explicita y retencion limitada.
- Telemetry: acceso restringido y auditado.
- Device tokens/credentials: nunca en payload de dominio.
- Evidencia sensible: Gobierno Documental y controles existentes.

## 15. SQL conceptual — grupos de tablas futuras

Nombres son candidatos de diseño, NO autorizacion DDL.

Preferir un prefijo coherente `Logistica_` si el patron real del repositorio/SQL lo confirma antes de migrar.

Grupos conceptuales:
- Logistica_Ordenes
- Logistica_Envios
- Logistica_Viajes
- Logistica_Paradas
- Logistica_AsignacionesDespacho
- Logistica_VehiculosPerfilOperativo
- Logistica_ConductoresPerfilOperativo
- Logistica_AlmacenesPerfilOperativo
- Logistica_OrdenesMantenimiento
- Logistica_PartesInstaladas
- Logistica_LlantasCicloVida
- Logistica_Combustible
- Logistica_CargaEnergia
- Logistica_DispositivosTelemetria
- Logistica_EventosTelemetria
- Logistica_TarifasAcuerdos
- Logistica_TarifasReglas
- Logistica_Incidentes
- Logistica_Siniestros
- Logistica_Cumplimiento
- Logistica_ServiciosPasajeros
- Logistica_ManifiestosPasajeros

Gate posterior debe validar nombre exacto contra convenciones existentes antes de DDL.

## 16. Prohibiciones estructurales

No crear:
- Logistica_Empresas
- Logistica_Usuarios
- Logistica_Roles
- Logistica_Clientes
- Logistica_Proveedores
- Logistica_Productos
- Logistica_Almacenes como maestro paralelo
- Logistica_Existencias
- Logistica_Documentos
- Logistica_CuentasPorPagar
- Logistica_CuentasPorCobrar
- Logistica_Scheduler
- Logistica_Notificaciones
- Logistica_MobileEngine

No introducir Mongo, duplicar scheduler/communications/document manager, ni incorporar vendor schemas en contratos publicos.

## 17. Gate 2 outputs requeridos

Gate 2 se considera completo cuando quede documentado y validado:

- bounded context map;
- aggregate catalog;
- canonical references to BOS;
- conceptual data model;
- ownership de escritura;
- idempotency strategy;
- event catalog;
- integration adapter boundaries;
- field/mobile interaction contract;
- AI confirmation contract;
- retention strategy;
- privacy/RBAC rules;
- inventory/finance/document boundaries;
- SQL candidate groups;
- explicit anti-duplication list;
- riesgos y decisiones pendientes para Gate 3.

## 18. Gate 2 exit criteria

```text
DATA_ARCHITECTURE_DEFINED=YES
INTEGRATION_ARCHITECTURE_DEFINED=YES
BOS_REFERENCE_MAP_COMPLETE=YES
WRITE_OWNERSHIP_DEFINED=YES
IDEMPOTENCY_DEFINED=YES
EVENT_CATALOG_DEFINED=YES
FIELD_MOBILE_CONTRACT_PRESERVED=YES
PRIMETY_AS_UX_ONLY=YES
ZERO_RECAPTURE=ENFORCED
SHARED_CAPABILITY_FIRST=ENFORCED
DUPLICATED_MASTER_ENTITIES=0
DUPLICATED_FIELD_ENGINES=0
DUPLICATED_SCHEDULER=0
DUPLICATED_DOCUMENT_MANAGER=0
DUPLICATED_FINANCE_LEDGER=0
MONGO_SOURCE_OF_TRUTH=0
NEW_VERTICAL_CORE_LOGIC=0
PRODUCTION_TOUCHED=NO
```

Gate 2 NO autoriza DDL ni implementacion. El siguiente gate debe ser schema/contract validation detallada antes de cualquier migracion.
