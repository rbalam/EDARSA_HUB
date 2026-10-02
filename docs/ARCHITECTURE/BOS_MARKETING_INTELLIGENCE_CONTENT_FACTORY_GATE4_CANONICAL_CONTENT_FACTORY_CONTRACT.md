# BOS Marketing Intelligence & Content Factory — Gate 4 Canonical Content Factory Contract

Estado: CANONICAL CONTRACT — DOCUMENTATION ONLY

## 1. Objetivo

Definir el contrato canónico de Content Factory a partir de Gate 4 Discovery R1/R2. No autoriza tablas, migraciones, endpoints, jobs, UI, conectores ni despliegues.

SQL Server EDARSAHUB continúa como cerebro y fuente canónica. Content Factory es bounded context de Marketing y no debe crecer Core con lógica de negocio.

## 2. Decisiones de reutilización

- Object Storage: REUSE `core.object_storage`; no crear almacenamiento paralelo.
- Scheduler: REUSE infraestructura canónica, locks y bitácora; no scheduler paralelo.
- RBAC/Auth: REUSE.
- AI model/provider routing: REUSE contrato de Gate 3.
- Agent Harness / MarketingActivationRequest: ALIGN/REUSE como contrato de orquestación cuando aplique.
- Workflows/approvals: REUSE/EXTEND infraestructura existente; no motor paralelo.
- Direct LLM calls existentes: ALIGN gradualmente al AI Gateway, sin romper runtime.
- Content Assets, Briefs, Variants, Experiments, Rights y Generation Lineage: NEW_REQUIRED dentro de Marketing, sujetos a diseño físico posterior.
- Publishing: deferido a su gate; no crear conector en Gate 4.

## 3. Ownership

Marketing Content Factory owns:
- brief creativo;
- metadata del asset;
- variantes;
- lineage de generación;
- contexto Brand/Audience referenciado;
- experimento de contenido;
- derechos/licencias;
- estado creativo y de aprobación específico;
- correlación con campaña.

No owns:
- bytes/storage engine;
- usuarios/permisos;
- scheduler engine;
- CRM master data;
- ventas/KPIs comerciales;
- presupuestos financieros;
- secrets;
- provider/model policy kernel;
- publishing provider credentials.

## 4. Entidades conceptuales

### MarketingBrief
Contrato de intención creativa. Referencia campaña, objetivo, audiencia, marca, canal, restricciones, idioma/mercado y requester.

### ContentAsset
Registro canónico de metadata de una pieza. Los bytes viven en Object Storage y ContentAsset conserva únicamente referencia segura, tipo, checksum, tamaño, metadata y lineage.

### ContentVariant
Variante derivada de un asset o brief. Mantiene parent/root lineage y razón de variante.

### ContentGeneration
Traza de una ejecución generativa: request, route autorizado, provider/model efectivo cuando corresponda, prompt/context fingerprint, timestamps, resultado, costos/usage referenciables y assets producidos.

### ContentExperiment
Contrato A/B/n que relaciona variantes, hipótesis, audiencia, ventana, métricas y estado. No redefine KPIs de Comercial.

### CreativeRightsRecord
Derechos/licencias/procedencia/consentimientos/restricciones y vigencias asociados al asset o insumo creativo.

### BrandProfile / AudienceProfile
Contexto versionado de generación. AudienceProfile referencia datos CRM canónicos; no duplica clientes/contactos.

## 5. Lifecycle canónico

Brief:
DRAFT -> READY_FOR_GENERATION -> IN_GENERATION -> GENERATED -> IN_REVIEW -> APPROVED | REJECTED | CANCELLED

Asset:
CREATED -> VALIDATING -> READY -> IN_REVIEW -> APPROVED -> PUBLISHABLE -> ARCHIVED

Estados de publicación efectiva pertenecen al Publishing Orchestrator y no deben mezclarse con el lifecycle creativo.

Transiciones privilegiadas deben pasar por RBAC/workflow. No se autoriza aprobación implícita por IA.

## 6. Asset lineage

Cada asset/variant debe poder reconstruir:
- brief origen;
- parent asset;
- root asset;
- generación origen;
- provider/model efectivo si fue generado;
- usuario/agente solicitante;
- campaña;
- Brand/Audience profile versions;
- source references;
- transformaciones;
- checksum;
- timestamps.

Lineage es metadata SQL canónica. Los binarios permanecen en Object Storage.

## 7. Object Storage contract

Content Factory reutiliza `core.object_storage`.

Reglas:
- SQL guarda referencias, no blobs pesados salvo excepción explícita futura.
- checksum obligatorio para deduplicación/integridad.
- object key no debe contener secrets ni PII innecesaria.
- acceso a bytes debe estar autorizado.
- reemplazar contenido crea nueva versión/lineage; no destruir evidencia histórica silenciosamente.
- no asumir que el proveedor de storage es fuente de verdad.

## 8. Generación AI

Flujo:
1. validar requester/RBAC;
2. cargar Brief + contexto autorizado;
3. solicitar capability al AI Gateway;
4. obtener route autorizado;
5. ejecutar adapter permitido;
6. normalizar resultado;
7. almacenar bytes mediante Object Storage;
8. persistir metadata/lineage/usage;
9. enviar a revisión cuando aplique.

No hardcodear provider/model en nuevas capacidades de Marketing.

## 9. Variants

Una variante debe conservar:
- parent_asset_id;
- root_asset_id;
- variant_type;
- generation/transform reference;
- parámetros no sensibles;
- reason/purpose;
- version;
- status.

No sobrescribir el asset padre.

## 10. Experimentos

ContentExperiment no es un motor de ventas.

Debe referenciar:
- campaña;
- variantes;
- segmentos/audiencias;
- hypothesis;
- start/end;
- allocation;
- métricas canónicas;
- attribution contract.

Los resultados económicos deberán usar Comercial/Finance como fuentes canónicas.

## 11. Rights & compliance

CreativeRightsRecord debe soportar conceptualmente:
- source/provenance;
- owner/licensor;
- license type;
- permitted channels/markets;
- valid_from/valid_to;
- AI-generated indicator;
- talent/model consent reference cuando aplique;
- restrictions;
- evidence reference.

Un asset sin derechos suficientes no debe alcanzar PUBLISHABLE.

## 12. Approvals

Reutilizar workflow/RBAC existentes.

Separar:
- creative review;
- brand review;
- legal/rights review;
- budget approval cuando aplique;
- publication approval.

Las políticas serán configurables por empresa/unidad/mercado; no hardcodear IDs.

## 13. Scheduler

Reutilizar Scheduler canónico para tareas diferidas o recurrentes.

Content Factory define intención de trabajo; Scheduler define ejecución temporal, locks y bitácora.

No duplicar scheduler, retry engine ni job logging.

## 14. Multiempresa/global

Toda entidad futura deberá respetar relaciones oficiales de empresa/unidad y, cuando corresponda:
- market/country;
- language/locale;
- currency;
- timezone;
- FechaOperación.

No hardcodear alias ni IDs.

## 15. Idempotencia y auditoría

Futuros comandos mutantes deberán incluir idempotency/correlation cuando aplique.

Auditar:
- requester;
- action;
- before/after status;
- asset/brief/campaign;
- generation;
- approval;
- timestamps;
- error/retry;
- correlation id.

## 16. Límites explícitos

PROHIBIDO en Gate 4:
- segundo Object Storage;
- segundo Scheduler;
- segundo RBAC/workflow engine;
- segundo AI Provider Router;
- CRM duplicado;
- KPI comercial paralelo;
- secrets en tablas de dominio;
- Mongo como fuente operativa;
- LIVE para dashboards administrativos;
- lógica Content Factory dentro de Core.

## 17. Matriz final

| Capacidad | Decisión |
|---|---|
| Object Storage | REUSE |
| Scheduler | REUSE |
| RBAC/Auth | REUSE |
| AI Gateway | REUSE |
| Agent Harness Marketing contract | ALIGN/REUSE |
| Existing workflow/approvals | REUSE/EXTEND |
| Existing direct AI calls | ALIGN |
| ContentAsset | NEW_REQUIRED |
| MarketingBrief | NEW_REQUIRED |
| ContentVariant | NEW_REQUIRED |
| ContentGeneration lineage | NEW_REQUIRED |
| ContentExperiment | NEW_REQUIRED |
| CreativeRightsRecord | NEW_REQUIRED |
| Brand/Audience generation context | NEW_REQUIRED |
| Publishing connectors | DEFER |
| Attribution/ROI | DEFER |

## 18. Gate de salida

Gate 4 queda arquitectónicamente cerrado cuando este contrato esté integrado y pase checks.

El siguiente gate permitido es Campaign Orchestrator según la secuencia BOS vigente. Debe iniciar con READ_ONLY discovery y no con implementación física.
