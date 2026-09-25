# FOTO FINISH / PRODUCTION QUALITY
## Foundation Mutation Plan V1

Estado: GATE4 R3
Dominio: Production Quality
Incluye: Foto Finish + Bitácora de Parrilla
Fuente de verdad corporativa: SQL Server EDARSAHUB
Estado Edge/KDS: operacional, no fuente corporativa

---

# 01. FINAL REUSE MATRIX

## REUSE

### Productos / recetas / insumos
Evidencia:
- backend/modules/sync_recetas/models.py
- ProductoSync
- InsumoSync
- RecetaLineaSync
- ElaboradoLineaSync

Decisión:
Production Quality NO crea segundo catálogo de productos, recetas ni insumos.

### KDS / estaciones operativas
Evidencia:
- backend/modules/edge/orquestador_kds_core.py

Capacidades existentes:
- id_ticket_linea
- id_transaccion_global
- id_mesa
- unidad_negocio
- id_producto
- tiempo_coccion_minutos
- timestamp_liberacion
- estado_produccion
- RETENIDO / PREPARANDO / LISTO

Decisión:
NO crear segundo KDS.

### Tablajería
Evidencia:
- backend/modules/tablajeria/schemas.py
- backend/modules/tablajeria/routes.py
- backend/modules/tablajeria/ordenes_service.py
- backend/modules/tablajeria/fase6_service.py

Capacidades existentes:
- plantillas
- versionado
- órdenes
- pesos
- rendimiento
- merma
- derivados
- inventario
- costeo
- contabilidad
- idempotencia en movimientos/costeo/pólizas

Decisión:
REUSE / EXTEND, no duplicar.

### Object Storage
Evidencia:
- backend/core/object_storage.py

Contrato:
- binarios fuera de SQL
- metadata y referencia en SQL
- put_object()
- get_object()

Decisión:
REUSE.

### FechaOperación / timezone
Evidencia:
- backend/api/configuracion_operativa_unidades.py
- core.utils.operational_window

Contrato:
- motor canónico
- timezone America/Mexico_City
- turnos por unidad

Decisión:
REUSE.

### Navegación
Evidencia:
- frontend/src/config/enterpriseMenuConfig.js

Contrato:
- Production/Tablajería ya vive dentro de Operación
- no crear menú raíz adicional

Decisión:
EXTEND grupo Operación/Producción.

---

# 02. ENTITIES TO EXTEND

1. KDS production line
2. Tablajería
3. RBAC
4. Object Storage
5. Frontend Operación / Producción

---

# 03. ENTITIES TO CREATE

CREATE sujeto a verificación SQL física previa:

1. ProductionItem
2. ProductionStation
3. QualityStandard
4. QualityStandardVersion
5. Measurement
6. ProductionEvidence
7. QualityDecision
8. Rework
9. QualityOverride
10. Device
11. DeviceCalibration cuando no exista capacidad equivalente

Ninguna entidad se autoriza para DDL hasta Gate SQL metadata / anti-duplicación.

---

# 04. TABLES OR COLUMNS REQUIRED

Todavía NO se autoriza nombre SQL definitivo.

Familias lógicas candidatas:
- ProductionItem
- ProductionStation
- QualityStandard
- QualityStandardVersion
- Measurement
- ProductionEvidence
- QualityDecision
- Rework
- QualityOverride
- Device
- DeviceCalibration

Regla:
antes de CREATE físico se debe ejecutar SQL READ_ONLY metadata audit y demostrar inexistencia de tabla/columna/capacidad equivalente.

---

# 05. EXISTING TABLES VERIFIED

Verificadas por referencia en repositorio, no por metadata SQL física:

- Operaciones_Tablaje_Plantillas
- Operaciones_Tablaje_PlantillasDetalle
- Operaciones_Tablaje_Ordenes
- Operaciones_Tablaje_OrdenesDetalle
- Tablajeria_MovimientosInventario
- Tablajeria_CosteoProduccion
- Tablajeria_PolizasContables
- Tablajeria_PolizasDetalle
- Tablajeria_ConfigContable
- Sistema_TurnosOperativosUnidad

Estado:
REPOSITORY_EVIDENCE_ONLY.

Pendiente:
SQL_PHYSICAL_METADATA_CERTIFICATION.

---

# 06. BACKEND FILES TO EXTEND

Candidatos:
- backend/modules/edge/orquestador_kds_core.py
- backend/modules/tablajeria/*
- backend/core/object_storage.py solo por reutilización
- helpers canónicos RBAC
- helpers canónicos FechaOperación
- filtros corporativos

---

# 07. NEW BACKEND FILES IF REQUIRED

Bounded context propuesto:

backend/modules/production_quality/

Posibles componentes:
- schemas.py
- repository.py
- service.py
- routes.py
- events.py
- standards.py
- measurements.py
- evidence_service.py
- devices.py

Crear únicamente los que sobrevivan al Gate de anti-duplicación físico.

---

# 08. ENDPOINTS PLAN

Familias futuras:
- /api/production-quality/items
- /api/production-quality/stations
- /api/production-quality/standards
- /api/production-quality/measurements
- /api/production-quality/evidence
- /api/production-quality/decisions
- /api/production-quality/rework
- /api/production-quality/overrides
- /api/production-quality/devices

---

# 09. RBAC PERMISSIONS PLAN

Permisos lógicos candidatos:
- PRODUCTION_QUALITY_VER
- PRODUCTION_QUALITY_OPERAR
- PRODUCTION_QUALITY_CONFIGURAR
- PRODUCTION_QUALITY_APROBAR
- PRODUCTION_QUALITY_OVERRIDE
- PRODUCTION_QUALITY_EVIDENCIAS_VER
- PRODUCTION_QUALITY_DEVICES_CONFIGURAR

---

# 10. EVENT CONTRACTS

Eventos lógicos candidatos:
- PRODUCTION_ITEM_CREATED
- PRODUCTION_STARTED
- GRILL_STARTED
- GRILL_MEASUREMENT_CAPTURED
- GRILL_COMPLETED
- PLATING_STARTED
- FOTO_FINISH_CAPTURED
- QUALITY_EVALUATED
- QUALITY_PASSED
- QUALITY_WARNING
- QUALITY_FAILED
- REWORK_REQUIRED
- REWORK_COMPLETED
- OVERRIDE_REQUESTED
- OVERRIDE_APPROVED
- ITEM_RELEASED

---

# 11. MEASUREMENT CONTRACT

Entidad transversal Measurement.

Campos conceptuales:
- measurement_id
- production_item_id
- station_id
- measurement_type
- numeric_value
- unit_code
- captured_at_utc
- fecha_operacion
- device_id
- operator_user_id
- source
- quality_standard_version_id

Tipos:
- WEIGHT
- TEMPERATURE
- TIME
- YIELD

---

# 12. EVIDENCE CONTRACT

ProductionEvidence metadata en SQL.
Binario: object storage existente.

Campos conceptuales:
- evidence_id
- production_item_id
- station_id
- evidence_type
- storage_path
- content_type
- byte_size
- content_hash
- captured_at_utc
- fecha_operacion
- device_id
- operator_user_id

Tipos:
- GRILL_PHOTO
- FOTO_FINISH_PHOTO
- REWORK_PHOTO
- OVERRIDE_EVIDENCE

---

# 13. QUALITY GATE CONTRACT

QualityDecision:
- PASS
- WARNING
- FAIL

FAIL bloquea liberación y genera Rework o rechazo según política.

---

# 14. REWORK / OVERRIDE CONTRACT

Rework conserva decisión original y genera nueva evaluación.

Override:
- no borra FAIL
- permiso específico
- motivo
- aprobador
- evidencia
- timestamp
- audit trail

---

# 15. DEVICE CONTRACT

Device abstraction:
- CAMERA
- SCALE
- THERMOMETER
- SENSOR

No acoplar dominio a USB/serial/network directamente.

---

# 16. KDS INTEGRATION

KDS Edge se conserva.

id_ticket_linea
    -> ProductionItem
    -> Production Quality lifecycle

Edge:
ejecución local/resiliencia.

SQL Server:
verdad corporativa, auditoría, estándares, mediciones, decisiones y evidencias.

---

# 17. TABLAJERIA INTEGRATION

Tablajería:
insumo base -> derivados

Production Quality:
partida/plato -> validación operativa final

No fusionar bounded contexts.

---

# 18. INVENTORY / COST INTEGRATION

Production Quality NO implementa segundo motor de inventario/costos.

Quality genera eventos y delega a motores canónicos.

---

# 19. FRONTEND SCOPE

Operación
  -> Producción
      -> Dashboard
      -> Tablajería
      -> Parrilla
      -> Foto Finish
      -> Calidad
      -> Configuración

No menú raíz Foto Finish.

---

# 20. MIGRATION ORDER

1. SQL metadata audit
2. confirmar entidades existentes
3. resolver collisions
4. contratos SQL definitivos
5. migration foundation
6. RBAC
7. repository/service
8. eventos
9. KDS bridge
10. devices
11. evidence
12. quality gate
13. frontend
14. integration tests
15. UAT
16. Production readiness

---

# 21. ROLLBACK PLAN

Rollback no debe afectar:
- comandas
- KDS
- Tablajería
- inventarios
- costos
- ventas
- Scheduler
- NetPay

No borrar evidencia histórica.

---

# 22. TESTS REQUIRED

- schema contracts
- idempotency
- RBAC
- tenant isolation
- empresa/unidad
- FechaOperacion
- timezone
- Measurement units
- evidence hash
- QualityDecision lifecycle
- rework
- override segregation
- KDS linkage
- Tablajería non-regression
- inventory/cost non-regression
- object storage metadata
- device offline
- device calibration
- duplicate event replay
- concurrent updates
- frontend touch flow

---

# 23. MUTATION GATE RECOMMENDATION

Siguiente gate obligatorio:

GATE5A_SQL_PHYSICAL_ANTI_DUPLICATION_READONLY

Solo después:
GATE5B_FOUNDATION_MUTATION

Condiciones:
- SQL metadata PASS
- collisions=0
- blockers=0
- cada CREATE demostrado
- rollback definido
- exact scope definido
- production_allowed=false
- Development only

---

# DECISION

GATE4_R3_TARGET=DOCUMENTATION_ONLY
FUNCTIONAL_IMPLEMENTATION=NO
SQL_MUTATION=NO
PRODUCTION_TOUCH=NO

NEXT_GATE=
GATE5A_SQL_PHYSICAL_ANTI_DUPLICATION_READONLY
