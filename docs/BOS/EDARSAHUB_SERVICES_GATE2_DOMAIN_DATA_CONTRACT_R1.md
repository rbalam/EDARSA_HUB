# EDARSAHUB Services - Gate 2 Domain Data Contract R1

## 1. Entrada certificada
Gate0A SQL Discovery = 100% CERTIFIED_READ_ONLY. Gate0B Repository Contract + certificacion = 100% CERTIFIED_READ_ONLY. Gate1 Capability & Ownership Map = 100% CERTIFIED, COMPLETE, PASS, production_touched=false.

## 2. Principios de contrato
1. BOS conserva identidad, clientes, proveedores, RBAC, empresas/unidades, documentos, CRM, inventarios, finanzas, Scheduler/Notifications, ActivoFijo y COA.
2. Services solo persiste delta de dominio y referencias canonicas.
3. Todo FK a maestros BOS debe ser explicito y no copiar PII ni datos maestros.
4. Todo agregado debe tener clave estable, estado, auditoria, idempotencia y empresa/contexto cuando aplique.
5. DDL fisico se disena despues; este Gate no autoriza SQL de escritura.

## 3. Bounded contexts y agregados
### 3.1 Universal Services
Agregados logicos candidatos:
- `Services_Provider`: proveedor/prestador de servicio como rol operativo; tipos `INDIVIDUAL`, `ORGANIZATION`, `FACILITY`. Individual referencia `Gobierno_Persona`; organization/facility enlaza maestro corporativo/proveedor cuando semanticamente corresponda.
- `Services_ProviderSpecialty`: N:N Provider-Specialty.
- `Services_Profession`: catalogo configurable; no enum hardcodeado.
- `Services_Specialty`: catalogo jerarquico/configurable.
- `Services_Credential`: habilitacion/certificacion/licencia con emisor, vigencias y documento BOS opcional.
- `Services_ServiceCatalog`: servicio vendible/ejecutable, unidad, duracion estimada, reglas de disponibilidad y referencias comerciales.
- `Services_Resource`: abstraccion operativa `PERSON|TEAM|VEHICLE|ROOM|EQUIPMENT|TOOL|VENUE|RENTAL_ASSET`; enlaza ActivoFijo/persona/ubicacion cuando aplique.
- `Services_ServiceSubjectRef`: referencia tipada al objeto atendido; no copia el maestro destino.
- `Services_Engagement`: cabecera comun minima para ejecuciones de servicio cuando sea viable. `EngineType`: `APPOINTMENT|CASE|PROJECT|WORK_ORDER|EVENT|RECURRENCE`.
- `Services_EngagementParty`, `Services_EngagementResource`, `Services_EngagementEvidence`, `Services_EngagementStatusHistory` como relaciones/historial de negocio.

Decision Gate2: la cabecera comun solo contiene invariantes transversales; payload vertical debe vivir en su bounded context. No crear una mega-tabla polimorfica con cientos de columnas nulas.

### 3.2 Construction & Design
Agregados logicos candidatos:
- `Construction_Project`: extension vertical de proyecto/obra; referencia cliente, ubicacion, responsable y contrato comercial/documental.
- `Construction_Phase`, `Construction_Front`, `Construction_BudgetItem`, `Construction_Concept`: jerarquia operativa de obra.
- `Construction_Crew`: cuadrilla; miembros referencian Provider/Persona/Resource, no duplican trabajador.
- `Construction_Progress`: avance fisico por fecha/concepto/frente con cantidad, porcentaje y evidencia.
- `Construction_Estimate`: estimacion/generador contractual; separada de pago financiero.
- `Construction_ChangeOrder`: cambio con impacto costo/plazo/alcance y version/autorizacion.
- `Construction_QualityRecord`, `Construction_SafetyRecord`, `Construction_Handover`: hechos del dominio.

Invariantes:
- `physical_progress_pct` no deriva automaticamente de costo consumido.
- presupuesto original autorizado es inmutable; cambios entran por ChangeOrder/version.
- anticipos, retenciones y pagos reales se referencian a Finanzas BOS.

### 3.3 Fabrication
Agregados logicos candidatos:
- `Fabrication_ConfigurableProduct`: configuracion parametricamente resoluble.
- `Fabrication_BOM` + `Fabrication_BOMLine`: materiales/componentes referenciando catalogos canonicos.
- `Fabrication_CutPlan` + lineas de corte.
- `Fabrication_Remnant`: sobrante reutilizable con dimensiones/calidad/estado; no es merma por defecto.
- `Fabrication_WorkOrder`: orden de fabricacion de dominio solo si Gate3 demuestra insuficiencia semantica de ActivoFijo OT; de lo contrario adaptador/referencia.
- `Fabrication_Installation`: instalacion vinculada a Engagement/Construction Project.

### 3.4 Interiors & Fit-Out
Agregados logicos candidatos:
- `Interiors_Space`: espacio jerarquico de proyecto (cocina, sala, bano, oficina, etc.) sin tablas por tipo.
- `Interiors_DesignBrief`: necesidades, estilo, restricciones y presupuesto objetivo.
- `Interiors_Proposal`: propuesta versionada.
- `Interiors_Specification`: material/producto/mueble/equipo real con referencia canonica, cantidad y opcion/alternativa.
- `Interiors_VisualAssetRef`: referencia a imagen/render/video/documento BOS con tipo y version.
- `Interiors_Approval`: aprobacion/rechazo/solicitud de cambio.

Invariante: `VISUAL_CONCEPT`, `TECHNICAL_DRAWING` y `APPROVED_CONSTRUCTION_DOCUMENT` son estados/tipos distintos.

### 3.5 Real Estate & Land
Agregados logicos candidatos:
- `Land_Parcel`: nodo territorial jerarquico con `ParentParcelID`, `ParcelTypeID`, geometria/ref GIS, superficie canonica m2, unidad original, estado legal/catastral/comercial y referencias de propietario.
- `Land_ParcelType`: catalogo configurable (`PREDIO`, `MACROLOTE`, `SECTOR`, `ETAPA`, `FRACCIONAMIENTO`, `PRIVADA`, `MANZANA`, `LOTE`, `SUBLOTE`, `CONDOMINIO`, `UNIDAD_PRIVATIVA`, `AREA_COMUN`, `AREA_VERDE`, `PARQUE_PUBLICO`, `VIALIDAD`, `DONACION`, `EQUIPAMIENTO`, `SERVIDUMBRE`, `RESERVA`, `COMERCIAL`).
- `Land_ParcelEvent`: `SUBDIVISION|FUSION|SEGREGACION|LOTIFICACION|RELOTIFICACION|AFECTACION|DONACION|CESION|INCORPORACION|RECTIFICACION`.
- `Land_ParcelEventInput` / `Land_ParcelEventOutput`: lineage N:N para conservar genealogia.
- `Land_LegalDossier`: expediente juridico por parcela; referencias a escritura, registro, catastro y Gobierno Documento.
- `Land_NotaryOffice` / `Land_Notary`: crear solo si Gate3 confirma que no existe maestro compatible; evitar texto libre repetido.
- `Land_CommercialInventory`: disponibilidad comercial de parcela/unidad; no sustituye Parcel.
- `Land_Reservation`: apartado con vigencia/estado.
- `Land_PurchasePromise`: promesa de compraventa versionada.
- `Land_Sale`: hecho inmobiliario contractual; pagos/facturas/conciliacion permanecen en BOS/Finanzas.
- `Land_PaymentPlanRef`: referencias a plan/cartera financiera canonica; no segundo ledger.

Invariantes territoriales:
- no ciclos en `ParentParcelID`;
- superficie canonica > 0 para parcelas fisicas;
- una operacion territorial cerrada debe reconciliar superficie padre vs salidas + areas/reserva dentro de tolerancia parametrizada;
- parcela comercializable no puede quedar simultaneamente en estados incompatibles;
- lineage nunca se elimina por correccion; se versiona/rectifica.

## 4. Commission Contract
Owner: COA. Services/Land no crea motor paralelo. Extensiones candidatas:
- base: `PRECIO_VENTA|PRECIO_NETO|MONTO_COBRADO|ENGANCHE|UTILIDAD|MONTO_ESCRITURADO|MONTO_RECONOCIDO`;
- split por asesor/broker/coordinador/agencia/referidor;
- triggers/hitos de devengo;
- estados `CALCULADA|DEVENGADA|AUTORIZADA|PAGADA|PENDIENTE|REVERTIDA`;
- clawback como evento compensatorio, nunca borrado.
Gate3 debe mapear estas necesidades contra columnas/reglas COA reales antes de cualquier extension.

## 5. Claves, FK y unicidad - reglas logicas
- PK internas preferidas: bigint identity o uniqueidentifier solo donde el patron BOS del bounded context lo justifique; Gate3 selecciona tipo fisico por consistencia con vecinos canonicos.
- FK a `Gobierno_Persona(PersonaID)`, `Usuario_Catalogo(UsuarioID)`, `Sistema_Empresas(EmpresaID)`, Cliente/Proveedor/Documento/Activo/Producto segun evidencia real.
- Natural keys/config codes deben tener UNIQUE por contexto/empresa cuando aplique.
- `Land_Parcel`: UNIQUE logico `(Development/Context, ParcelCode, Version/Active)` segun modelo final; no asumir clave catastral universalmente unica si jurisdiccion/contexto no lo garantiza.
- `Credential`: evitar duplicado por provider + tipo + emisor + numero + vigencia.
- relaciones N:N con UNIQUE compuesto de sus FK activas.

## 6. Indices candidatos
Indexar FK de alto uso y filtros canonicos: EmpresaID, ProviderID, EngagementID, ProjectID, ParcelID, ParentParcelID, Status, FechaOperacion/fechas de vigencia, claves comerciales/catastrales y referencias externas idempotentes. No crear indices sin plan de consulta en Gate3/DDL dossier.

## 7. Estados y transiciones
Todos los agregados con workflow deben usar catalogo/enum de dominio versionado y transiciones validadas en servicio de dominio, no strings arbitrarios dispersos. Estados terminales no se reabren salvo transicion explicita/auditada.

## 8. Idempotencia
- comandos externos/importaciones: `ExternalSource + ExternalId` o idempotency key canonica con UNIQUE;
- eventos territoriales, comisiones, estimaciones y cambios de obra no pueden duplicarse por reintento;
- writes futuros deben ser transaccionales y reentrantes;
- Worker/Jobs no son fuente de verdad del dominio.

## 9. Auditoria
Cada agregado materializable debe conservar `CreatedAt/By`, `UpdatedAt/By` o patron BOS equivalente. Eventos con impacto legal/financiero requieren historial append-only de negocio. Usar auditoria transversal BOS para actor/sesion; no duplicarla.

## 10. PII, legal y retencion
- PII permanece preferentemente en maestros Gobierno/Cliente/Proveedor.
- Services referencia IDs y solo almacena atributos de dominio indispensables.
- documentos legales/credenciales/evidencias usan Gobierno documental y politicas de acceso/retencion.
- salud, valores, notariado u otros sectores regulados requieren subgate regulatorio antes de guardar datos sensibles adicionales.

## 11. Fechas, timezone, moneda e idioma
- usar helpers/convenciones BOS existentes; FechaOperacion y zona horaria empresarial cuando aplique; almacenar instantes tecnicos conforme patron canonico.
- moneda por FK/catalogo canonico, nunca string hardcodeado.
- textos/catalogos preparados para localizacion; no duplicar por idioma.
- horarios operativos/disponibilidad se modelan por calendario/reglas, no offsets fijos.

## 12. Migracion
Estrategia: additive-first, idempotente, reversible y por bounded context. Antes de DDL: auditar colisiones exactas, tipos de PK/FK vecinos, naming, columnas de auditoria y helpers/repositorios existentes. No backfill automatico sin fuente canonica y reconciliacion.

## 13. Rollback
Todo DDL futuro debe traer rollback separado, prechecks, postchecks y prohibicion de eliminar datos si ya existen registros productivos. Rollback destructivo solo con evidencia de vacio o plan de preservacion.

## 14. Gate 3 requerido
Siguiente gate: `Physical Schema & DDL Dossier READ_ONLY`. Debe:
1. mapear cada entidad logica a objetos SQL existentes o nuevos;
2. comprobar tipos reales de PK/FK y naming;
3. decidir `REUSE/EXTEND/NEW` por objeto fisico;
4. producir DDL propuesto + rollback + pre/post-checks como dossier, sin ejecutarlo;
5. resolver especialmente COA comisiones, ActivoFijo OT, Produccion/Tablajeria, Gobierno documental y maestros Land/Notaria antes de crear equivalentes.
