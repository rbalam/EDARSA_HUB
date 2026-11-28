# EDARSAHUB BOS — Cavas Gate 16B
## Contrato canónico de interoperabilidad, homologación y migración histórica

Estado: DESIGN CONTRACT
Dominio propietario: Cavas / Integración Universal EDARSAHUB
Fuente de verdad: EDARSAHUB SQL Server
Producción: fuera de alcance de este Gate

## 1. Objetivo

Definir el contrato proveedor-neutral para que EDARSAHUB BOS Cavas pueda:

1. convivir de forma continua con Soft Restaurant, MPRO y futuros sistemas;
2. importar historia desde Kavasoft, legacy, CSV/Excel, APIs y otros orígenes autorizados;
3. preservar la historia disponible sin convertirla en un simple saldo inicial;
4. homologar personas, clientes, productos, botellas, ubicaciones y movimientos contra entidades canónicas EDARSAHUB;
5. garantizar idempotencia, procedencia, reconciliación, trazabilidad, rollback lógico y exportabilidad;
6. evitar lógica específica de proveedor dentro del dominio Cavas.

Este contrato no autoriza DDL, DML, endpoints, conectores ni sincronizaciones reales.

## 2. Principios vinculantes

- EDARSAHUB SQL Server es el cerebro y la única fuente operativa canónica.
- MongoDB no es fuente operativa.
- El dominio Cavas no conoce detalles de Soft Restaurant, MPRO, Kavasoft ni otro proveedor.
- Cada proveedor se implementa mediante adapter.
- Los conectores existentes de Soft Restaurant y MPRO deben reutilizar infraestructura canónica antes de crear cualquier nueva conexión.
- RBAC, empresa, unidad, usuario y permisos se resuelven con contratos existentes.
- Personas/clientes se homologan contra Gobierno_Persona, Gobierno_PersonaVinculo y Cliente_Catalogo cuando aplique.
- Productos se homologan contra el catálogo canónico existente; una importación no puede crear productos indiscriminadamente.
- Fecha original del hecho y fecha de importación son conceptos distintos.
- Reprocesar el mismo dato no puede duplicar entidades ni movimientos.
- Ninguna migración se certifica sin reconciliación cuantitativa y de identidad.
- Todo dato importado conserva procedencia suficiente para explicar de dónde vino y cómo fue transformado.
- Los datos del cliente deben poder exportarse mediante contratos documentados; no se usará lock-in por secuestro de información.

## 3. Modos de operación

### 3.1 CONTINUOUS_SYNC
El sistema externo continúa activo. EDARSAHUB recibe cambios incrementales y homologa al modelo canónico.

### 3.2 HISTORICAL_MIGRATION
El sistema anterior será reemplazado total o parcialmente. Se importa la historia disponible, preservando fechas y referencias originales.

### 3.3 HYBRID_CUTOVER
Se realiza backfill histórico y posteriormente sincronización incremental hasta una fecha/hora de corte. Después del delta final y la reconciliación, EDARSAHUB continúa como autoridad operativa definida para el alcance migrado.

### 3.4 MANUAL_FILE_IMPORT
Importación controlada desde CSV/XLSX/JSON u otro formato documentado. Siempre requiere dry-run y validación previa.

## 4. Contratos lógicos

Los siguientes nombres son contratos de dominio. Gate 16B no obliga a crear tablas con estos nombres.

### SourceSystem

Identifica la familia del proveedor u origen.

Campos lógicos mínimos:

- source_system_code
- display_name
- adapter_code
- adapter_version
- capabilities
- active

Ejemplos de códigos permitidos por adapters futuros: SOFTRESTAURANT, MPRO, KAVASOFT, CSV, LEGACY_API.
No se deben usar condicionales de proveedor dentro de Cavas.

### SourceInstance

Representa una instalación/origen concreto.

- source_instance_id
- source_system_code
- empresa_id
- unidad_negocio_id cuando aplique
- connection_reference o import_reference
- timezone
- currency
- locale
- operational_status

Las credenciales nunca viven en este contrato ni se hardcodean.

### MigrationBatch

Unidad auditable de migración o backfill.

- migration_batch_id
- source_instance_id
- mode
- requested_by
- started_at
- completed_at
- status
- mapping_version
- adapter_version
- dry_run
- cutoff_at opcional
- counts_received
- counts_accepted
- counts_rejected
- counts_conflicted
- reconciliation_status

Estados mínimos: DRAFT, DRY_RUN, REVIEW_REQUIRED, APPROVED, RUNNING, RECONCILING, CERTIFIED, FAILED, ROLLED_BACK.

### ExternalEntityReference

Mapea una entidad externa con su entidad canónica.

Clave lógica idempotente:

(source_instance_id, entity_type, source_record_id)

Campos:

- source_instance_id
- entity_type
- source_record_id
- canonical_entity_type
- canonical_entity_id
- mapping_status
- match_method
- match_confidence opcional
- first_seen_at
- last_seen_at
- source_checksum
- mapping_version

### ProvenanceRecord

Explica el linaje de un dato importado.

- source_system
- source_instance_id
- source_entity
- source_record_id
- source_transaction_id opcional
- source_line_id opcional
- original_occurred_at
- original_created_at opcional
- imported_at
- adapter_version
- mapping_version
- migration_batch_id
- source_checksum
- canonical_entity_type
- canonical_entity_id
- transformation_notes estructuradas

Regla: original_occurred_at nunca debe reemplazarse por imported_at.

### MappingDecision

Resultado de homologación.

Estados:

- EXACT_MATCH
- APPROVED_EQUIVALENCE
- PROBABLE_MATCH
- NEW_CANONICAL_REQUIRED
- CONFLICT
- REJECTED

PROBABLE_MATCH y CONFLICT requieren revisión humana cuando impliquen crear o fusionar identidad canónica.

### ReconciliationResult

Debe poder comparar por batch:

- personas/socios
- botellas
- movimientos
- cantidades/niveles
- cargos si aplican
- evidencias
- registros rechazados/conflictivos

La certificación exige explicar cualquier diferencia. Cero diferencia no es obligatoria cuando el origen contiene registros inválidos, pero toda diferencia debe quedar clasificada y aprobada.

### MigrationCheckpoint

Permite reanudar procesos sin duplicación.

- migration_batch_id
- stream/entity_type
- cursor/checkpoint
- source_high_watermark
- canonical_high_watermark
- updated_at

## 5. Identidad y deduplicación

### Personas y socios

Prioridad conceptual de matching:

1. identificador externo previamente vinculado;
2. identificadores oficiales válidos cuando el contrato legal lo permita;
3. email/teléfono normalizados como señales, nunca como prueba universal por sí solos;
4. nombre y otros atributos únicamente como match probabilístico;
5. revisión humana para ambigüedad.

No se deben crear catálogos paralelos a Gobierno_Persona / Cliente_Catalogo.

### Productos

El adapter entrega una referencia externa normalizada. El motor de homologación decide:

- producto canónico exacto;
- equivalencia aprobada;
- probable;
- requiere alta mediante flujo canónico de catálogo;
- rechazado.

La migración no crea SKUs arbitrariamente.

### Botellas

Una botella física requiere identidad propia aunque varias botellas compartan producto/SKU. La procedencia debe poder distinguir botella física, producto y movimiento.

## 6. Historia de Cavas

Gate 16A confirmó que el dominio existente ya contiene conceptos como REGULARIZACION_HISTORICA, source_system e historical_reference. Gate 16B los reconoce como base y exige extenderlos de forma compatible, no duplicarlos.

La historia disponible debe preservar, cuando el origen lo provea:

- socio/propietario;
- botella;
- producto;
- entrada/alta;
- movimientos;
- consumos;
- ajustes;
- cambios de ubicación;
- cargos/descorches;
- fechas originales;
- observaciones;
- referencias externas;
- evidencias y fotografías;
- estado/nivel resultante.

Una importación de saldo inicial es un fallback documentado, no equivalente a una migración histórica completa.

## 7. Evidencias

Las evidencias externas deben conservar:

- referencia del origen;
- checksum;
- fecha original;
- fecha de ingestión;
- tipo MIME;
- tamaño;
- relación con entidad/movimiento;
- estado de validación;
- referencia al almacenamiento canónico.

El binario no debe duplicarse en SQL si existe Object Storage canónico apto. Gate posterior certificará la implementación real.

## 8. Idempotencia

Toda operación de ingestión debe poder ser reintentada.

Reglas:

- misma SourceInstance + entity_type + source_record_id no crea una segunda entidad canónica;
- para eventos/transacciones se añade source_transaction_id/source_line_id cuando el proveedor lo soporte;
- checksum detecta cambios del mismo registro externo;
- una corrección del origen produce actualización/versionado controlado, no duplicación silenciosa;
- los adapters deben declarar su estrategia de high-watermark/cursor.

## 9. Dry-run obligatorio

Antes de escribir datos de una migración:

1. conectar o cargar archivo;
2. detectar esquema/versión;
3. parsear;
4. normalizar;
5. mapear;
6. calcular matches y conflictos;
7. producir resumen cuantitativo;
8. mostrar errores;
9. no escribir entidades operativas;
10. exigir aprobación para ejecutar cuando corresponda.

## 10. Cutover

Secuencia canónica:

BACKFILL -> DELTA -> PRE-CUTOVER RECONCILIATION -> FREEZE/CUTOFF -> FINAL DELTA -> FINAL RECONCILIATION -> CERTIFICATION -> GO-LIVE -> POSTCHECK

No se permite declarar completada una migración por el simple hecho de terminar el import.

## 11. Rollback

El rollback debe distinguir:

- rollback de batch aún no certificado;
- corrección de mapping;
- reversión de entidades creadas exclusivamente por el batch cuando sea seguro;
- preservación de entidades canónicas preexistentes;
- jamás borrar historia ajena al batch.

Cada registro escrito por un batch debe ser trazable al migration_batch_id o mecanismo equivalente.

## 12. Exportabilidad

EDARSAHUB debe poder entregar, según permisos:

- socios/personas referenciables;
- botellas;
- inventario;
- movimientos;
- cargos;
- ubicaciones;
- evidencias o referencias;
- provenance;
- mappings externos.

Los formatos concretos se definirán en gates de implementación.

## 13. Adapter Contract

Todo adapter debe implementar conceptualmente:

- discover()
- validate_connection_or_payload()
- capabilities()
- extract_full()
- extract_delta(checkpoint)
- normalize()
- source_identity()
- source_checksum()
- health()
- close()

El adapter no puede:

- escribir directamente a tablas Cavas;
- crear usuarios/roles/permisos;
- resolver por sí mismo identidades canónicas;
- almacenar secretos;
- saltarse el motor de homologación;
- declarar una migración certificada.

## 14. Reutilización obligatoria

Antes de implementar Gate 16C/16D se debe reutilizar o extender, cuando exista evidencia:

- core.sql_first.connection_factory;
- RBAC y scope corporativo canónicos;
- connection resolver/registry;
- infraestructura de adapters Soft Restaurant/MPRO;
- Gobierno_Persona y Gobierno_PersonaVinculo;
- Cliente_Catalogo;
- catálogo canónico de productos;
- Scheduler;
- Object Storage/evidencias;
- auditoría/logging;
- timezone, currency y locale canónicos.

Si una capacidad no está certificada como existente, Gate posterior debe marcarla NEW_REQUIRED en lugar de duplicarla silenciosamente.

## 15. Límites de bounded context

Cavas es propietario de:

- custodia;
- socio-cava;
- botella física;
- ubicación de cava;
- movimiento de cava;
- consumo;
- cargo propio del dominio;
- historia y reconciliación de Cavas.

Integración Universal es propietaria de:

- adapters;
- source instances;
- checkpoints;
- ingestion;
- provenance transversal;
- contratos de interoperabilidad.

CRM/Gobierno es propietario de identidad de persona/cliente.
Catálogo es propietario de producto/SKU.
Core conserva únicamente infraestructura transversal.

## 16. Criterios de cierre de Gate 16B

Gate 16B se considera cerrado cuando:

- este contrato existe en el repositorio;
- no introduce proveedor hardcodeado en lógica Cavas;
- no crea tablas/endpoints/jobs;
- pasa git diff check;
- el contrato es consistente con REGULARIZACION_HISTORICA/source_system/historical_reference existentes;
- deja explícitos idempotencia, provenance, dry-run, reconciliación, cutover, rollback y exportabilidad;
- Production no fue tocada.

Siguiente Gate autorizado tras certificación: Gate 16C — diseño/implementación mínima del Migration & History Engine conforme a este contrato.
