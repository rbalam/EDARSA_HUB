# EDARSA Logistics — Gate 1C Primety / Field-Mobile Platform / Gate 2 Input Contract

Estado: CANONICAL ARCHITECTURE CONTRACT — NO IMPLEMENTATION

## 1. Decision canonica: Primety vs Field/Mobile Platform

La relacion queda cerrada asi:

- **Primety** es la capa de experiencia humana/UX de campo de EDARSAHUB: simple, amigable, guiada y orientada a personas sin experiencia en sistemas.
- **BOS Field/Mobile Platform** es la capacidad tecnica transversal compartida para operacion movil y de campo.
- **EDARSA Logistics** consume ambas capas y conserva unicamente la semantica de negocio logistica.
- **EDARSAHUB BOS / SQL Server** conserva la autoridad canonica y la fuente de verdad.

No son dos plataformas competidoras. Primety no duplica Device Services, offline/sync, seguridad, documentos, comunicaciones ni IA transversal. Field/Mobile Platform no posee la logica de Freight, Trips, Dispatch, Maintenance, WMS, Fleet o Passenger Mobility.

Modelo:

```text
EDARSAHUB BOS / SQL canonico
        |
        +-- Gobierno / RBAC / Documents / Communications / Scheduler
        |
        +-- BOS Field/Mobile Platform
        |     +-- Mobile operation envelope
        |     +-- Offline cache + Outbox/Inbox + Sync Engine
        |     +-- Device Services
        |     |     +-- camera/photo
        |     |     +-- QR/barcode/NFC
        |     |     +-- location/GPS
        |     |     +-- push
        |     |     +-- biometrics
        |     +-- shared capture
        |     +-- shared AI processing
        |           +-- OCR
        |           +-- transcription
        |           +-- extraction/classification
        |
        +-- Primety
        |     +-- Field Experience
        |     +-- simple guided UX
        |     +-- zero-recapture interaction
        |
        +-- Domain bounded contexts
              +-- Logistics
              +-- RH
              +-- Services
              +-- Inventarios
              +-- ARBITROA
              +-- others
```

## 2. Evidencia que sustenta la decision

- `backend/modules/agent_harness/mobile.py` define `edarsahub.bos-mobile-operation.v1` y declara `mobile_is_source_of_truth=false` y `server_authoritative=true`.
- `docs/BOS/BOS_AGENT_HARNESS_AH8_MOBILE_V1.md` define el envelope offline y la autoridad del servidor.
- `docs/BOS/BOS_AGENT_HARNESS_MASTER_ARCHITECTURE_V1.md` define Mobile UI -> Application/Use Cases -> BOS API Client -> Encrypted Local Cache + Outbox/Inbox -> Sync Engine -> Device Services(camera/QR/barcode/NFC/location/push/biometrics) -> BOS APIs -> SQL canonico.
- `docs/BOS/ARBITROA_BOS_A3_DOMAIN_DATA_CONTRACT_V1.md` aporta el patron voz -> transcripcion -> propuesta -> confirmacion humana.
- No se encontro un runtime/namespace tecnico canonico denominado Primety que deba competir con Agent Harness Mobile. Por tanto Primety se canoniza como experiencia/producto de campo sobre la plataforma tecnica compartida, no como segundo engine.

## 3. Maximas obligatorias

### SHARED_CAPABILITY_FIRST
Antes de crear una capacidad:
1. REUSE si ya existe.
2. EXTEND en su owner canonico si existe parcialmente.
3. SHARE si es transversal y nueva.
4. NEW solo si es especifica del bounded context.

### ZERO_RECAPTURE
Si BOS ya conoce un dato canonico, la UI no debe volver a pedirlo salvo correccion autorizada.

### SIMPLE_FIELD_UX
Cualquier persona, aun sin experiencia en sistemas, debe poder operar:
- lenguaje humano;
- captura minima;
- foto/voz/scan cuando reduzca pasos;
- contexto autocompletado;
- solo decisiones necesarias;
- confirmacion humana para hechos/acciones sensibles.

### ONE CAPABILITY, ONE OWNER, MANY CONSUMERS
Una mejora transversal desarrollada por cualquier proyecto EDARSAHUB debe poder ser reutilizada por los demas sin duplicacion.

## 4. Ownership de capacidades compartidas

| Capacidad | Owner canonico | Primety | Logistics |
|---|---|---|---|
| Mobile operation envelope | BOS Field/Mobile Platform | Consume | Consume |
| Offline cache/outbox/inbox/sync | BOS Field/Mobile Platform | Consume | Consume |
| Camera/photo capture | BOS Field/Mobile Platform | Presenta UX | Aporta contexto de negocio |
| QR/barcode/NFC | BOS Field/Mobile Platform | Presenta UX | Aporta contexto de negocio |
| Location/GPS capture | BOS Field/Mobile Platform | Presenta UX | Aporta contexto de negocio |
| Push/device services | BOS Field/Mobile Platform | Presenta UX | Consume eventos |
| Voice/audio capture | BOS Field/Mobile Platform | Presenta UX | Aporta contexto |
| Transcription/OCR/extraction | BOS shared AI/processing | Presenta propuesta | Interpreta en dominio |
| Human confirmation pattern | BOS workflow/policy + Primety UX | Facilita confirmacion | Aplica regla de dominio |
| Documents/evidence record | Gobierno Documental | Facilita captura | Referencia evidencia |
| Notifications | Communications BOS | Presenta | Solicita notificacion |
| Identity/RBAC | BOS | Consume | Consume |
| Business semantics | bounded context correspondiente | No posee | Logistics posee solo semantica logistica |

## 5. Gate 2 — contrato de entrada congelado

Gate 2 recibe como invariantes:

### 5.1 DOMAIN -> OWNER
- Organization / Identity / RBAC / Gobierno / Documents / Customers / Providers / Purchasing / Inventory / Finance / Scheduler / Communications / Field-Mobile Platform: BOS y bounded contexts existentes.
- Freight / Passenger Mobility / Fleet Operations / Dispatch / Trips / Shipments / Delivery / Warehouse Ops delta / Maintenance / Tires-Parts lifecycle / Fuel-Energy / Telematics normalization / Rates / Safety-Compliance-Claims / International-Multimodal: EDARSA Logistics.

### 5.2 AGGREGATE -> SOURCE OF TRUTH
- TransportOrder, FreightShipment, Trip, Stop, DispatchAssignment, PassengerService, PassengerManifest, VehicleOperationalProfile, DriverOperationalProfile, CarrierOperationalProfile, WarehouseOperationalProfile, MaintenanceWorkOrder, MaintenancePlan, VehicleInspection, InstalledPart, TireLifecycle, FuelTransaction, EnergyCharge, TelematicsDeviceBinding, TelematicsBusinessEvent, RateAgreement, RateRule, Incident, Claim, ComplianceRequirement -> Logistics SQL, con referencias a maestros BOS.
- Evidencia documental -> Gobierno Documental.
- Existencia y movimientos -> Inventarios.
- Pago/contabilidad -> Finanzas.
- Personas -> Gobierno.
- Empresas/sucursales/unidades -> BOS.
- Usuarios/RBAC -> BOS.

### 5.3 LOGISTICS ENTITY -> BOS REFERENCE
- DriverOperationalProfile -> Gobierno_Persona.
- CarrierOperationalProfile -> Proveedor_Catalogo.
- Customer context -> Cliente_Catalogo.
- WarehouseOperationalProfile -> Inventario_Almacenes.
- Parts/Tires/Consumables -> Producto_Catalogo.
- Stock -> Inventario_Existencias.
- Inventory movement -> Inventario_Movimientos + Inventario_MovimientosDetalle.
- Company -> Sistema_Empresas.
- Branch -> Sistema_Sucursales.
- Business unit -> Unidades_Negocio.
- User -> Usuario_Catalogo.
- Authorization -> Sistema_RBAC_* + Usuario_*.
- Evidence -> Gobierno_Documento*.

### 5.4 EVENT -> PRODUCER -> CONSUMER
Gate 2 debe modelar contratos de eventos sin crear bus paralelo:
- TransportOrderCreated -> Logistics -> Dispatch/Control Tower.
- ShipmentReady -> Shipments -> Dispatch.
- TripPlanned/TripDispatched/TripStarted -> Dispatch/Trips -> Field UX/Telematics/Control Tower.
- StopArrived/DeliveryAttempted/DeliveryCompleted -> Trips/Delivery -> Control Tower/Documents/Billing facts.
- PODCaptured -> Field/Mobile + Delivery -> Gobierno Documental + Logistics.
- PassengerBoarded/PassengerDroppedOff -> Passenger Mobility -> Trip/Control Tower.
- MaintenanceRequested/PartRequested -> Fleet/Maintenance -> Workshop/Inventarios.
- InventoryMovementCompleted -> Inventarios -> Maintenance.
- PartInstalled/TireInstalled -> Maintenance -> Fleet lifecycle.
- FuelCaptured -> Fuel/Energy -> Fleet/Finanzas.
- VehicleFaultDetected/GeofenceEntered/ETAChanged -> Telematics -> Maintenance/Trips/Notifications.
- IncidentReported/ClaimOpened -> Safety -> Documents/Finanzas/Notifications.
- FieldVoiceCaptured -> Field/Mobile -> shared AI.
- VoiceIntentProposed -> shared AI -> domain.
- VoiceIntentConfirmed -> user -> domain.
- PhotoEvidenceCaptured -> Field/Mobile -> Gobierno Documental + domain.

### 5.5 REUSE | EXTEND | SHARE | DECOUPLE | NEW
REUSE:
Sistema_Empresas, Sistema_Sucursales, Unidades_Negocio, Gobierno_Persona, Gobierno_Documento*, Usuario_*, Sistema_RBAC_*, Cliente_Catalogo, Proveedor_Catalogo, Producto_Catalogo, Inventario_Almacenes, Inventario_Existencias, Inventario_Movimientos*, Compras, Finanzas, Scheduler, Communications, operational_window/FechaOperacion.

EXTEND:
Activo Fijo -> vehicle/equipment operational profile; Gobierno_Persona -> driver profile; Proveedor_Catalogo -> carrier/workshop profile; Inventario_Almacenes -> warehouse operational capabilities; Inventarios -> installation/removal trace without duplicating stock; Gobierno Documents -> logistics evidence relations; Field/Mobile Platform -> Logistics field use cases.

SHARE:
camera, photo, files, audio, voice, transcription, OCR, QR, barcode, scan, NFC, location, GPS capture, signature/evidence, offline, sync, push, notifications, AI assistance, human confirmation.

DECOUPLE:
Mongo/pymongo/MongoClient as source of truth; vendor schemas; SoftRestaurant/MPRO/NetPay/GPS/ERP/TMS provider internals; vertical Logistics logic from backend/core.

NEW:
Logistics Orders, Freight, Passenger Mobility, Fleet Operations, Trips, Dispatch, Stops, Shipments, Delivery/POD semantics, WMS delta, Maintenance/Workshop, Installed Parts/Tire lifecycle, Fuel/Energy, Telematics normalization, Logistics Rates/Carrier contracts, Safety/Compliance/Claims, International and Multimodal orchestration.

## 6. Prohibiciones para Gate 2

Gate 2 NO puede proponer:
- Logistics_Empresas, Logistics_Usuarios, Logistics_Roles, Logistics_Clientes, Logistics_Proveedores, Logistics_Productos, Logistics_Almacenes, Logistics_Existencias.
- segundo scheduler.
- segundo NotificationDispatcher.
- segundo gestor documental.
- segunda plataforma mobile/offline.
- motor privado de camera/voice/OCR/scan/location en Logistics.
- Mongo como fuente operativa o fallback.
- hardcode de IDs, aliases, empresas, unidades, timezone, moneda o pais.
- crecimiento de backend/core con logica vertical Logistics.
- tablas duplicadas de capacidades BOS existentes.

## 7. Requisitos de diseno para Gate 2

Gate 2 debe producir solamente arquitectura de datos e integracion, aun no implementacion productiva:
- esquema conceptual/SQL propuesto;
- claves naturales/idempotency keys;
- FK/logical references exactas a BOS;
- ownership de escritura;
- eventos y consumidores;
- multiempresa/multipais/multimoneda/multitimezone;
- UTC para timestamps y FechaOperacion segun owner/unidad;
- retencion para telemetria de alta frecuencia;
- politicas offline/conflict/retry/review;
- privacidad/PII y consentimiento para pasajeros/geolocation;
- auditable human confirmation para IA;
- estrategia de adapters para providers externos;
- migraciones propuestas pero no ejecutadas hasta gate posterior.

## 8. Criterios de salida hacia Gate 2

PRIMETY_RELATION_CANONICALIZED=YES
FIELD_MOBILE_SINGLE_TECHNICAL_OWNER=YES
PRIMETY_ROLE=FIELD_EXPERIENCE_UX
LOGISTICS_ROLE=DOMAIN_SEMANTICS
BOS_SQL_AUTHORITY=PRESERVED
SHARED_CAPABILITY_FIRST=ENFORCED
ZERO_RECAPTURE=ENFORCED
DUPLICATED_FIELD_ENGINES=0
DUPLICATED_MASTER_ENTITIES=0
MONGO_SOURCE_OF_TRUTH=0
NEW_VERTICAL_CORE_LOGIC=0
PRODUCTION_TOUCHED=NO

Este documento es el contrato de entrada de Gate 2. No autoriza por si mismo la creacion de tablas, endpoints, migraciones ni codigo funcional.
