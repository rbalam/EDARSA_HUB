# BOS Marketing Intelligence & Content Factory — Gate 3 AI Provider Routing Contract

Estado: CANONICAL CONTRACT — NO PRODUCTIVE IMPLEMENTATION

## 1. Decisión arquitectónica

Clasificación final:

- AI model routing policy kernel: REUSE.
- Existing direct LLM integrations: ALIGN.
- Provider/model registry, runtime execution, fallback and usage/cost accounting: EXTEND.
- New independent AI Provider Router: NOT AUTHORIZED.

No se crea un segundo router.

## 2. Evidencia que sustenta la decisión

### 2.1 Kernel canónico existente

`backend/core/ai_gateway_policy_adapter.py` ya implementa:
- `ModelCandidate` con provider, model, capabilities, clasificaciones de datos, riesgo y costos por token.
- `ModelRouteRequest` con capacidades requeridas y estimados de tokens.
- `authorize_model_route` para seleccionar provider/model por policy, scopes, riesgo, clasificación de datos y presupuesto.
- selección determinista del candidato compatible de menor costo.
- `PreparedModelRoute` con provider, model, costo estimado, scopes y procedure.

Por tanto, la decisión de routing ya existe como capacidad transversal y no debe duplicarse dentro de Marketing.

### 2.2 Execution gate existente

`backend/core/agent_execution_gate.py` ya obliga autorización del requester y delega a `authorize_model_route` para inferencia AI.

Marketing debe consumir ese gate, no saltárselo.

### 2.3 Router de agent_harness no es router de providers

`backend/modules/agent_harness/router.py` enruta agentes/skills según capabilities y privilege score.

Debe REUSE dentro de su dominio de agent orchestration, pero no sustituye ni debe duplicar el AI model routing kernel.

### 2.4 Integraciones LLM directas existentes

Se detectaron integraciones que llaman directamente a `emergentintegrations.llm.chat`, entre ellas:
- `backend/modules/ia_assistant/service.py`
- `backend/modules/comercial/services/pricing_ai_service.py`
- `backend/modules/comercial/services/ingesta_competencia_service.py`

Estas integraciones deben clasificarse como ALIGN: conservan su dominio funcional, pero la selección de provider/model, policy, budget y trazabilidad debe converger al gateway canónico.

No se autoriza reescribirlas en este Gate.

## 3. Frontera canónica

### Core transversal permitido

El Core conserva únicamente capacidades realmente transversales:
- policy de capability/risk/data classification;
- authorization gate;
- model-route decision;
- secret access abstractions existentes.

No debe incorporar prompts, briefs, campañas, assets, marketing rules ni provider-specific business logic.

### Marketing bounded context

Marketing owns:
- capability request;
- prompt/brief/context;
- purpose and expected output;
- campaign/content correlation;
- rights and approval workflow;
- marketing-specific quality metrics.

Marketing does not own:
- provider policy kernel;
- RBAC;
- secrets;
- global model selection rules;
- generic execution authorization.

## 4. Contrato canónico de solicitud

Conceptualmente, cada petición AI de Marketing debe aportar:
- capability requerida;
- data classification;
- risk level;
- estimated input/output tokens;
- requester authorization;
- enterprise/unit scope;
- budget envelope;
- correlation id;
- marketing context reference.

No debe aportar un provider/model hardcodeado como decisión final.

Un provider/model solicitado explícitamente puede ser una preferencia, pero el gateway decide si está autorizado.

## 5. Provider registry

La infraestructura existente cubre decisión de ruta, pero no demuestra todavía un catálogo canónico persistente completo de providers/models.

Clasificación: EXTEND.

El registry futuro debe ser único y reusable, con metadata como:
- provider_id;
- model_id;
- capabilities;
- enabled/disabled;
- supported data classifications;
- max risk;
- input/output cost;
- currency;
- countries/markets allowed;
- SLA/latency class;
- context limits;
- multimodal capabilities;
- effective dates.

No se autoriza tabla todavía.

## 6. Runtime execution

La decisión de policy y la ejecución del proveedor son responsabilidades distintas.

Contrato:
1. requester authorization;
2. policy evaluation;
3. route decision;
4. provider adapter execution;
5. response normalization;
6. usage/cost capture;
7. audit;
8. domain-specific handling.

Los adapters específicos de OpenAI/Gemini/etc. no deben contaminar Marketing domain logic.

## 7. Fallback

La capacidad actual demuestra selección de un candidato autorizado, pero no certifica una cadena runtime de fallback completa.

Clasificación: EXTEND.

Fallback debe:
- usar sólo candidatos previamente autorizables;
- no ampliar scopes;
- respetar data classification y risk;
- respetar presupuesto;
- registrar motivo del fallback;
- evitar loops;
- conservar correlation id;
- auditar provider/model efectivo.

## 8. Usage y costo

El gateway actual estima costo para routing, pero Gate 3 no encuentra evidencia suficiente de accounting canónico completo de uso real por request/provider/model.

Clasificación: EXTEND.

Se requiere contrato futuro para:
- input tokens;
- output tokens;
- cached tokens cuando aplique;
- actual provider/model;
- actual cost;
- currency;
- latency;
- status/error;
- retry/fallback count;
- campaign/content/request correlation;
- timestamps.

No se autoriza schema físico en este Gate.

## 9. Secret management

Las llamadas directas existentes leen `EMERGENT_LLM_KEY` desde entorno.

Dirección canónica:
- reutilizar Secret Manager/configuración oficial;
- no exponer secrets a frontend;
- no persistir secrets en tablas de dominio;
- no incluir secrets en logs;
- adapters reciben referencias/config segura, no business code hardcodeado.

Migración de llamadas directas se realizará en gates posteriores, con pruebas de regresión.

## 10. Hardcodes detectados a alinear

Ejemplos actuales:
- `MODELO_IA = "gpt-5.5"` / `PROVEEDOR_IA = "openai"` en IA Assistant.
- `MODELO_IA = "gemini-2.5-flash"` y `.with_model("gemini", ...)` en ingesta de competencia.
- referencias directas a versiones GPT en Pricing AI.

Estos hardcodes son deuda de alineación, no autorización para romper funcionalidad existente.

Hasta migrar, deben conservarse operativamente si son necesarios para no romper producción.

## 11. Plan de convergencia

Fase A — contract only:
- documentar gateway canonical contract;
- inventariar callers directos;
- definir compatibility adapter.

Fase B — provider registry:
- diseñar catálogo/configuración;
- sin duplicar Secret Manager.

Fase C — execution adapters:
- encapsular provider-specific SDK/integration.

Fase D — caller migration:
- migrar IA Assistant;
- migrar Pricing AI;
- migrar Ingesta Competencia;
- preservar comportamiento y rollback.

Fase E — usage/cost/fallback:
- persistencia y auditoría canónica;
- dashboards consumen snapshots, no LIVE.

## 12. Matriz final

| Componente | Decisión |
|---|---|
| core.ai_gateway_policy_adapter | REUSE |
| core.agent_execution_gate | REUSE |
| agent_harness/router | REUSE sólo para agent/skill routing |
| direct LLM calls | ALIGN |
| provider/model registry | EXTEND |
| provider execution adapters | EXTEND |
| runtime fallback | EXTEND |
| usage/cost accounting | EXTEND |
| secret handling | REUSE + ALIGN callers |
| segundo AI Provider Router de Marketing | FORBIDDEN |

## 13. Reglas de oro

- No crecer Core con lógica de Marketing.
- No crear router paralelo.
- No hardcodear provider/model en nuevas capacidades.
- No romper integraciones actuales durante convergencia.
- No Mongo como verdad.
- No LIVE para reporting administrativo.
- SQL Server EDARSAHUB sigue siendo cerebro.
- Multiempresa, país, moneda, timezone e idioma deben ser configurables.
- Toda migración futura debe ser reversible y probada.

## 14. Salida de Gate 3

Gate 3 queda arquitectónicamente completo cuando este contrato quede integrado y certificado.

El siguiente Gate permitido es Gate 4 — Content Factory Architecture, reutilizando este gateway como dependencia transversal y sin implementar todavía tablas/runtime productivo.
