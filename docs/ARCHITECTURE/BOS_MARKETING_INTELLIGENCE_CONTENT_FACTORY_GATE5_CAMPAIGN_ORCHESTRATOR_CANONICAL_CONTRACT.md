# BOS Marketing Intelligence & Content Factory — Gate 5 Campaign Orchestrator Canonical Contract

Estado: CANONICAL CONTRACT — DOCUMENTATION ONLY

## 1. Objetivo
Definir el contrato canónico del Campaign Orchestrator usando la evidencia READ_ONLY certificada de Gate 5 R1. No autoriza implementación física.

EDARSAHUB SQL Server continúa como cerebro y fuente canónica. Campaign Orchestrator pertenece al bounded context Marketing y coordina capacidades existentes; no reemplaza CRM, Finance, Scheduler, RBAC, Workflow, Content Factory ni AI Gateway.

## 2. Evidencia y decisiones
- Agent Harness ya expone MarketingActivationRequest: ALIGN/REUSE como envelope de activación cuando aplique.
- CRM ya posee leads, oportunidades, automatizaciones, triggers y SLA: REUSE; no duplicar pipeline CRM.
- Scheduler canónico existe: REUSE para ejecución temporal, locks y bitácora.
- Content Factory Gate 4: REUSE para briefs/assets/variants/experiments/rights.
- Finance/presupuestos: REUSE como autoridad económica; Marketing sólo referencia/envelope de presupuesto.
- RBAC/Auth y workflow/approvals: REUSE/EXTEND.
- Campaign aggregate/orchestration state: NEW_REQUIRED dentro de Marketing.
- Audience targeting/segment references: ALIGN/NEW metadata de Marketing, referenciando CRM canónico sin copiar clientes.
- Publishing provider execution: DEFER al gate de Publishing.
- Attribution/ROI: DEFER al gate correspondiente.

## 3. Ownership
Campaign Orchestrator owns:
- MarketingCampaign aggregate y estado;
- objetivos y ventanas de campaña;
- referencias a audiencia/segmentos;
- channel plan conceptual;
- content assignments;
- activation plan;
- experiment assignments;
- orchestration state;
- correlation/idempotency;
- referencias de presupuesto;
- reglas de readiness específicas de campaña.

No owns:
- clientes/contactos/leads/oportunidades;
- ventas/KPIs;
- presupuesto financiero maestro;
- scheduler engine;
- workflow/RBAC;
- assets/binarios;
- AI provider/model routing;
- credenciales de canales;
- delivery adapters externos;
- attribution económica final.

## 4. MarketingCampaign conceptual
Campos conceptuales mínimos:
- campaign_id;
- empresa/unidad scope;
- name;
- objective;
- status;
- start/end;
- market/country;
- language/locale;
- timezone;
- budget_reference;
- audience references;
- content/experiment references;
- channel plan;
- owner/requester;
- approval state;
- correlation/idempotency metadata;
- audit timestamps.

No se autoriza todavía tabla ni esquema físico.

## 5. Lifecycle
DRAFT -> PLANNING -> READY_FOR_REVIEW -> APPROVED -> SCHEDULED -> ACTIVE -> PAUSED -> COMPLETED | CANCELLED

Reglas:
- DRAFT/PLANNING no publica.
- APPROVED requiere políticas/RBAC/workflow aplicables.
- SCHEDULED usa Scheduler canónico.
- ACTIVE no significa que cada canal haya publicado; estados de delivery pertenecen a Publishing.
- PAUSED impide nuevas activaciones sin destruir evidencia.
- COMPLETED conserva trazabilidad.

## 6. Activation plan
Una activación debe referenciar:
- campaign;
- audience/segment;
- channel intent;
- content asset/variant;
- experiment cuando aplique;
- desired schedule/window;
- budget envelope/reference;
- policy/approval context;
- correlation id.

MarketingActivationRequest existente debe alinearse/reutilizarse, no clonarse sin evidencia de gap.

## 7. CRM boundary
CRM es autoridad para Cliente_Catalogo, contactos, leads, oportunidades, pipeline y automatizaciones CRM.

Campaign Orchestrator puede:
- resolver audiencias mediante referencias;
- emitir intención/actividad autorizada;
- correlacionar respuestas con campaña.

No puede:
- copiar el maestro de clientes;
- crear un pipeline alterno de leads/oportunidades;
- redefinir estados CRM.

## 8. Finance boundary
Finance conserva autoridad de presupuesto/costo real. Campaign Orchestrator almacena referencias y límites operativos necesarios para policy/readiness.

No calcular ROI final ni crear ledger financiero paralelo.

## 9. Content Factory boundary
Campaign Orchestrator selecciona/referencia briefs, assets, variants y experiments de Gate 4.

No duplica lifecycle creativo, storage, rights ni generation lineage.

Un asset no PUBLISHABLE o sin rights suficientes no puede formar una activación publicable.

## 10. Scheduler boundary
Toda activación diferida/recurrente usa Scheduler canónico.

Campaign Orchestrator define intención temporal; Scheduler maneja clock, ejecución, locks, retries/bitácora según capacidades existentes.

## 11. Workflow/RBAC
Separar aprobación de:
- campaña;
- contenido;
- presupuesto cuando aplique;
- publicación.

No asumir que una aprobación implica las demás. No hardcodear usuarios, roles, IDs o empresas.

## 12. Readiness
Antes de SCHEDULED/ACTIVE validar conceptualmente:
- campaign approved;
- empresa/unidad válida;
- ventana válida;
- audiencia autorizada;
- contenido aprobado/PUBLISHABLE;
- rights válidos;
- budget reference/envelope válido;
- channel capability disponible;
- policy/RBAC;
- correlation/idempotency.

## 13. Idempotencia
Activaciones deben tener clave/correlation estable para evitar publicaciones o ejecuciones duplicadas.

Reintentos no deben crear una nueva intención comercial salvo comando explícito.

## 14. Eventos conceptuales
- MarketingCampaignCreated
- MarketingCampaignApproved
- MarketingCampaignScheduled
- MarketingCampaignActivated
- MarketingCampaignPaused
- MarketingCampaignCompleted
- MarketingActivationRequested
- MarketingActivationBlocked
- MarketingActivationReady

Reutilizar mecanismo de eventos existente antes de introducir infraestructura nueva.

## 15. Multiempresa
Usar relaciones oficiales empresa/unidad y soportar market/country/language/currency/timezone cuando aplique. FechaOperación se usa cuando la semántica operativa lo requiera. No hardcodear IDs ni alias.

## 16. Matriz
| Capacidad | Decisión |
|---|---|
| CRM customers/leads/opportunities | REUSE |
| CRM automation/triggers/SLA | REUSE |
| MarketingActivationRequest | ALIGN/REUSE |
| Scheduler | REUSE |
| RBAC/Auth | REUSE |
| Workflow/approvals | REUSE/EXTEND |
| Finance budget authority | REUSE |
| Content Factory | REUSE |
| AI Gateway | REUSE |
| MarketingCampaign aggregate | NEW_REQUIRED |
| Campaign orchestration state | NEW_REQUIRED |
| Audience targeting metadata | ALIGN/NEW |
| Channel activation intent | NEW_REQUIRED |
| Publishing adapters | DEFER |
| Attribution/ROI | DEFER |

## 17. Prohibiciones
- segundo CRM;
- segundo Scheduler;
- segundo workflow/RBAC;
- ledger financiero paralelo;
- storage paralelo;
- segundo AI Router;
- credenciales de canal en dominio Marketing;
- Mongo como fuente operativa;
- LIVE para dashboards administrativos;
- lógica Marketing específica dentro de Core.

## 18. Gate de salida
Gate 5 queda cerrado cuando este contrato se integre y certifique. El gate siguiente deberá iniciar con READ_ONLY discovery de la siguiente capacidad de la secuencia BOS antes de cualquier implementación.
