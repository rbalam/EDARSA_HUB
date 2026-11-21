# EDARSAHUB Services - Gate 3B Physical Schema & DDL Dossier R1

## Entrada certificada
Gate 2 Domain Data Contract: CERTIFIED_READ_ONLY / PASS / 100%. Gate 3A Physical Schema SQL Discovery: CERTIFIED_READ_ONLY / PASS / 100%, files_changed=[], production_touched=false, identidad SQL EDARSAHUB / HRLectura / HRLectura.

## Hallazgos fisicos
1. Reutilizar Gobierno_Persona, Gobierno_PersonaVinculo, Gobierno_Documento/Version, Cliente, Proveedor, Usuario/RBAC, Sistema_Empresas/Sucursales/Unidades, CRM, Venta, ActivoFijo y COA.
2. ActivoFijo_Activos confirma bigint identity como patron real para PK de dominio.
3. COA ya tiene reglas, condiciones, comisiones y CHECK constraints: no crear segundo motor de comisiones.
4. Gobierno ya controla documentos, versiones, sensibilidad y ownership: no crear document store paralelo.
5. Gate3A no encontro objetos Land/Real Estate/Notaria existentes; Land es candidato NEW, sujeto a subgate de colision antes de DDL.
6. Services/Construction/Interiors no tienen bounded context fisico completo existente; Sistema_HorariosServicioUnidad debe evaluarse solo como horario operativo, no como agenda completa.
7. Inventarios/Produccion/Tablajeria ya existen y Fabrication debe integrarse a ellos.

## Clasificacion fisica
REUSE: maestros y motores BOS arriba listados.
EXTEND: COA, ActivoFijo OT, Gobierno Documento y horarios operativos cuando su semantica aplique.
NEW: prefijos Services_, Construction_, Fabrication_, Interiors_, Land_.
DO_NOT_CREATE: segundo maestro de personas, CRM, RBAC, inventario, ledger financiero, scheduler, document store o tablas por profesion/oficio.

## Universal Services propuesto
Services_Professions, Services_Specialties, Services_Providers, Services_ProviderSpecialties, Services_Credentials, Services_ServiceCatalog, Services_Resources, Services_Engagements, Services_EngagementParties, Services_EngagementResources, Services_EngagementEvidence, Services_EngagementStatusHistory.
PK preferida bigint identity salvo incompatibilidad medida. FKs a maestros BOS con tipos exactos medidos. Provider es rol operativo, no copia Persona/Proveedor. Engagement usa EngineType APPOINTMENT|CASE|PROJECT|WORK_ORDER|EVENT|RECURRENCE. Idempotencia con ExternalSource+ExternalId UNIQUE cuando aplique.

## Construction & Design propuesto
Construction_Projects, Construction_Phases, Construction_Fronts, Construction_BudgetItems, Construction_Concepts, Construction_Crews, Construction_CrewMembers, Construction_Progress, Construction_Estimates, Construction_ChangeOrders, Construction_QualityRecords, Construction_SafetyRecords, Construction_Handovers.
Avance fisico separado de costo/pago; ChangeOrder versiona y no reescribe presupuesto autorizado; documentos/evidencias por Gobierno Documento.

## Fabrication propuesto
Fabrication_ConfigurableProducts, Fabrication_BOMs, Fabrication_BOMLines, Fabrication_CutPlans, Fabrication_CutPlanLines, Fabrication_Remnants, Fabrication_Installations.
Fabrication_WorkOrders queda CONDICIONAL: antes de crearla debe demostrarse que ActivoFijo_OrdenesTrabajo no cubre su semantica. BOM referencia materiales/productos canonicos. Remnant no equivale a merma.

## Interiors & Fit-Out propuesto
Interiors_Spaces, Interiors_DesignBriefs, Interiors_Proposals, Interiors_Specifications, Interiors_VisualAssetRefs, Interiors_Approvals. No tablas por tipo de espacio. Visuales referencian Gobierno Documento. Distinguir VISUAL_CONCEPT, TECHNICAL_DRAWING y APPROVED_CONSTRUCTION_DOCUMENT.

## Real Estate & Land propuesto
Land_ParcelTypes, Land_Parcels, Land_ParcelEvents, Land_ParcelEventInputs, Land_ParcelEventOutputs, Land_LegalDossiers, Land_CommercialInventory, Land_Reservations, Land_PurchasePromises, Land_Sales.
Land_Parcels usa ParentParcelID para jerarquia sin profundidad hardcodeada, SuperficieM2 decimal positiva, estados legal/catastral/comercial separados y lineage append-only. Operaciones territoriales: SUBDIVISION, FUSION, SEGREGACION, LOTIFICACION, RELOTIFICACION, AFECTACION, DONACION, CESION, INCORPORACION, RECTIFICACION.
Land_NotaryOffices y Land_Notaries solo tras subgate de collision/public-master review. No texto libre repetido. Finanzas BOS conserva pagos/cartera/conciliacion.

## Comisiones inmobiliarias
Owner = COA. No crear Land_Commissions. Mapear base, split, milestone, devengo y clawback contra COA_ReglasComision, COA_ReglasComisionCondiciones, COA_ComisionAplicada y excepciones existentes; extender solo delta faltante.

## Indices, prechecks y postchecks
Indexar FK y filtros de uso real; UNIQUE para codigos por contexto e idempotencia; indices por EmpresaID, Status, FechaOperacion, vigencias y ParentID. Indices espaciales solo tras certificar GIS SQL Server.
Prechecks: DB_NAME=EDARSAHUB, writer canonico autorizado y distinto de HRLectura, colision OBJECT_ID/COL_LENGTH/sys.indexes, tipos FK exactos, no equivalente semantico, backup/rollback aprobado, Produccion fuera de alcance.
Postchecks: objetos una sola vez, PK/FK/UQ/CK correctos, sin huerfanos, segundo run idempotente, conteos preservados en tablas reutilizadas, build/tests sin regresion, production_touched=false.

## Rollback
Rollback separado por bounded context. DROP solo de objetos creados y vacios/no usados; si hay filas, bloquear rollback destructivo y preservar datos. Extensiones a objetos existentes requieren rollback especifico con verificacion de dependencias.

## Gate siguiente
Gate 4 = Migration Package Design & Dry-Run Plan. Debe generar DDL idempotente + rollback + pre/post checks por bounded context, sin ejecutar hasta certificar writer canonico, environment, backup y dry-run en Desarrollo.
