# EDARSAHUB Services - Gate 4 Migration Package Design R1

## Entrada certificada
Gate 3B R2 = CERTIFIED / PASS / 100%, production_touched=false. El dossier fisico ya clasifica REUSE / EXTEND / NEW / DO_NOT_CREATE.

## Objetivo
Diseñar el paquete de migracion para Desarrollo sin ejecutar SQL. La ejecucion futura solo puede ocurrir mediante SQL_MIGRATION_DEVELOPMENT con writer canonico distinto de HRLectura.

## Canal canonico
Patron requerido:
- rama: Edarsahub_Desarrollo
- environment: development
- script versionado en repositorio
- rollback versionado separado
- XACT_ABORT + transaccion explicita + TRY/CATCH
- prechecks antes de DDL
- postchecks deterministas
- segunda ejecucion idempotente
- production_touched=false

Referencia de patron existente: docs/COA/COA_GATE4_SQL_MIGRATION_CHANNEL.md y workflows de migracion Development existentes.

## Orden de paquetes
1. Services Foundation
2. Services Engagement
3. Construction
4. Fabrication base, sin Fabrication_WorkOrders
5. Interiors
6. Land Parcel + lineage
7. Land legal/comercial
8. Extensiones COA solo si el gap queda probado
9. Fabrication_WorkOrders solo tras gate de compatibilidad ActivoFijo

## Archivos propuestos
Los scripts se materializaran en un Gate posterior, una vez cerrados los tipos exactos de cada FK y los subgates condicionales.

- backend/database/migrations/20260918_001_services_foundation.sql
- backend/database/migrations/20260918_001_services_foundation_rollback.sql
- backend/database/migrations/20260918_002_services_engagement.sql
- backend/database/migrations/20260918_002_services_engagement_rollback.sql
- backend/database/migrations/20260918_003_construction.sql
- backend/database/migrations/20260918_003_construction_rollback.sql
- backend/database/migrations/20260918_004_fabrication.sql
- backend/database/migrations/20260918_004_fabrication_rollback.sql
- backend/database/migrations/20260918_005_interiors.sql
- backend/database/migrations/20260918_005_interiors_rollback.sql
- backend/database/migrations/20260918_006_land_core.sql
- backend/database/migrations/20260918_006_land_core_rollback.sql
- backend/database/migrations/20260918_007_land_legal_commercial.sql
- backend/database/migrations/20260918_007_land_legal_commercial_rollback.sql

Las fechas/numeros son propuesta de versionado y deben revalidarse contra colisiones reales antes de crear los archivos.

## Prechecks obligatorios
Cada script futuro debe abortar si:
- DB_NAME() != EDARSAHUB
- environment no es Development
- login efectivo es HRLectura
- writer no coincide con el contrato de migracion autorizado
- objeto equivalente ya existe
- tipos de FK no coinciden exactamente
- existe colision de nombre/constraint/index
- backup/restore point no esta certificado
- el estado Git no corresponde al SHA autorizado

## Postchecks obligatorios
- objetos creados exactamente una vez
- PK/FK/UQ/CK e indices esperados
- cero referencias huerfanas
- conteos de tablas reutilizadas preservados
- segundo run = no-op/idempotente
- rollback evaluado
- topology Git 0/0
- build/tests PASS
- production_touched=false

## Rollback
Rollback por paquete, separado del forward migration.
- objetos nuevos: DROP solo si no contienen datos oficiales y no tienen consumidores
- extensiones: revertir solo la extension creada y validar dependencias
- si ya existen datos oficiales, bloquear rollback destructivo y preservar informacion

## Dry-run
Antes de ejecutar cualquier script:
1. validar sintaxis y dependencias en una base de Desarrollo restaurable;
2. ejecutar prechecks;
3. ejecutar forward migration;
4. ejecutar postchecks;
5. ejecutar segunda vez para certificar idempotencia;
6. ejecutar rollback en copia/entorno controlado;
7. ejecutar forward nuevamente;
8. certificar conteos, constraints y tiempos;
9. conservar evidencia de SHA de scripts y resultado.

## Bloqueadores de ejecucion
No se autoriza migracion hasta resolver:
- writer canonico de Development y credenciales por secret/environment;
- backup/restore point certificado;
- tipos exactos de FK para cada objeto nuevo;
- review de colisiones Land Notary/NotaryOffice;
- compatibilidad Fabrication WorkOrder vs ActivoFijo OrdenesTrabajo;
- cualquier extension COA contra schema real.

## Siguiente gate
Gate 4A = Migration Package Physical Scripts READ_ONLY DESIGN.
Debe crear los archivos SQL forward/rollback de manera versionada, sin ejecutarlos, y someterlos a auditoria de sintaxis/contratos. Gate 4B = Dry-run en Desarrollo solo despues de certificar writer, environment y backup.
