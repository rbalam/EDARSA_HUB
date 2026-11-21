# BOS Marketing Intelligence & Content Factory — Gate 2 Data & Integration Architecture

Estado: DATA & INTEGRATION ARCHITECTURE — NO PRODUCTIVE IMPLEMENTATION

## 1. Objetivo

Definir cómo Marketing se integra al canon existente de EDARSAHUB BOS sin duplicar dominios, fuentes de verdad, RBAC, Scheduler, Comercial, CRM ni Finanzas.

Este Gate no autoriza tablas, migraciones, endpoints, jobs, UI, conectores productivos ni despliegues.

## 2. Fuentes canónicas y ownership de datos

- SQL Server EDARSAHUB permanece como cerebro y única fuente canónica.
- Marketing no crea una segunda verdad de clientes, leads, oportunidades, ventas, pedidos, cotizaciones, costos ni presupuestos.
- Los datos operativos externos entran mediante adaptadores/syncs y se canonicalizan antes de ser usados por dashboards o analítica administrativa.
- No usar conexiones LIVE como fuente de reporting administrativo.
- No usar Mongo como fuente operativa o de verdad.

## 3. Reutilización obligatoria detectada

### CRM / Comercial
Reutilizar y referenciar, sin duplicar:
- Cliente_Catalogo
- Cliente_Contactos
- Cliente_Direcciones
- CRM_Leads
- CRM_Oportunidades
- Venta_Cotizaciones
- Venta_Pedidos
- Comercial_Competidores
- Comercial_CompetidoresCatalogo
- Comercial_CompetidoresListas
- Comercial_CompetidoresListasDetalle
- Comercial_CompetidoresMenuItems
- Comercial_CompetidoresUnidad
- Comercial_Ingesta_Competencia

### Comercial / KPIs
- Toda atribución de ingreso debe enlazar contra la verdad comercial canónica.
- Marketing no recalcula ni redefine ventas.
- Los KPIs de revenue atribuido son derivados; la venta base sigue siendo Comercial.

### Finanzas
- Presupuestos y costos financieros se referencian mediante contratos existentes.
- Marketing puede registrar costo propio de proveedor/campaña/contenido cuando no exista otra fuente canónica, pero debe enlazarlo a moneda, empresa y presupuesto oficiales.

### Seguridad / Plataforma
- Reutilizar RBAC existente.
- Reutilizar Scheduler existente.
- Reutilizar Secret Manager/configuración de integraciones.
- No crear scheduler, auth, permisos o vault paralelo.

## 4. Arquitectura lógica de datos propuesta

Las siguientes estructuras son conceptuales y requieren Gate posterior antes de crear tablas:

### MarketingCampaign
Relaciones:
- empresa_id / unidad / sucursal mediante relaciones oficiales
- presupuesto canónico de Finanzas
- owner/user/approval workflow
- objetivos/KPIs
- estado y vigencia

### MarketingBrief
Relaciones:
- campaign
- brand profile
- audience profile
- requester/approver
- idioma/mercado/canal

### ContentAsset
Persistir sólo metadata canónica:
- asset_id
- campaign_id
- brief_id
- provider/model
- storage reference
- checksum/hash
- mime/type
- rights/license
- cost/currency
- status
- audit timestamps

Los binarios pesados no se almacenan en SQL Server salvo una excepción futura explícitamente aprobada.

### ContentVariant / Experiment
- variante
- hipótesis
- segmentación
- canal
- periodo
- métricas
- winner/result sin alterar el dato comercial fuente

### BrandProfile / AudienceProfile / ContentPattern
- perfiles versionados
- alcance por empresa/unidad cuando aplique
- referencias a CRM/segmentos
- auditabilidad de cambios
- no duplicar cliente maestro

### TrendSignal / SocialListeningSignal
- source/provider
- external id
- observed_at
- topic/entity
- score/metrics
- raw reference
- normalized fields
- empresa/unidad/mercado aplicable
- retención y trazabilidad

### PublishingExecution
- campaign/asset
- provider/channel/account reference
- idempotency_key
- scheduled_at
- published_at
- remote_id
- status
- retry/error metadata
- audit

### MarketingTouchpoint / AttributionResult
- touchpoint enlaza campaña/contenido/canal con entidad canónica disponible
- attribution result es snapshot derivado
- nunca altera venta, pedido, cliente ni margen canónico

### AIContentRequest / AIProviderUsage
- capability
- provider/model
- request correlation id
- usage
- cost
- currency
- latency
- status
- fallback chain
- policy decision
- audit
- sin secretos

## 5. Patrones de integración

### 5.1 Inbound
External source -> provider adapter -> normalization -> canonical validation -> SQL canonical persistence/snapshot -> analytics.

### 5.2 Outbound publishing
Campaign/Content canonical state -> approval -> provider adapter -> idempotent publish -> remote status -> canonical execution log.

### 5.3 AI generation
Brief -> capability request -> AI provider router -> provider -> generated asset reference -> rights/cost/usage metadata -> approval.

### 5.4 Attribution
Touchpoints + canonical Comercial sales + canonical Finance costs -> attribution engine -> snapshot/result -> dashboard.

## 6. Idempotencia y correlación

Toda integración nueva debe contemplar:
- external_id/provider_id
- idempotency_key
- correlation_id
- source_system
- first_seen_at / last_seen_at
- checksum cuando aplique
- retry_count / last_error
- no duplicación por claves naturales o índices únicos definidos posteriormente

## 7. Multiempresa, país, moneda e idioma

- No hardcodear empresas/unidades/sucursales.
- Toda entidad debe heredar el alcance organizacional por relaciones oficiales.
- Costos deben conservar moneda original y, si aplica, referencia a conversión canónica.
- País/mercado/idioma deben ser configurables, no constantes.
- Fechas operativas deben respetar timezone/FechaOperación cuando corresponda.

## 8. Integraciones/proveedores

Gate 2 no autoriza proveedores específicos como dependencia única.

Los adapters deben ser capability-driven:
- social listening
- social publishing
- image generation
- video generation
- audio/voice
- LLM/text
- analytics/ad platforms
- storage/media delivery

Cada adapter debe exponer un contrato común y declarar:
- capabilities
- auth mechanism
- rate limits
- SLA
- cost model
- geographic restrictions
- supported media
- retry/idempotency behavior

## 9. AI Provider Router

Antes de crear uno nuevo, auditar si existe infraestructura AI/provider reusable.

Si no existe canon suficiente, el router deberá:
- vivir fuera de backend/core salvo capacidad verdaderamente transversal;
- resolver provider/model por capability y policy;
- soportar fallback;
- registrar usage/cost;
- no almacenar secretos;
- permitir deshabilitar proveedores por empresa/país;
- registrar auditoría de decisiones.

## 10. Eventos y mensajería

Los eventos definidos en Gate 1 son contratos de dominio, no autorización para crear un nuevo bus.

Orden de decisión:
1. reutilizar mecanismo de eventos/jobs ya existente;
2. extenderlo si cubre durabilidad/idempotencia/reintentos;
3. crear infraestructura nueva sólo con evidencia de gap.

## 11. Matriz REUSE / EXTEND / NEW

| Área | Decisión Gate 2 |
|---|---|
| Clientes/CRM | REUSE |
| Leads/Oportunidades | REUSE |
| Ventas/Pedidos/Cotizaciones | REUSE |
| Competidores | REUSE + EXTEND sólo metadata faltante |
| Presupuestos/Finanzas | REUSE |
| RBAC/Auth | REUSE |
| Scheduler | REUSE |
| Secret management | REUSE |
| Marketing campaign domain | NEW capability |
| Content factory domain | NEW capability |
| Publishing execution domain | NEW capability |
| Trend/Social signals | NEW capability |
| Attribution snapshots | NEW capability |
| AI usage/cost metadata | EXTEND/NEW según infraestructura existente |
| AI provider routing | REUSE/ALIGN first, NEW sólo si gap comprobado |

## 12. Prohibiciones explícitas

- No duplicar tablas CRM/Comercial/Finanzas.
- No crear Mongo operativo.
- No consultar LIVE para dashboards administrativos.
- No hardcodear IDs o aliases.
- No secretos en código o tablas de dominio.
- No crecer Core con lógica de Marketing.
- No crear scheduler paralelo.
- No crear un segundo sistema de permisos.
- No permitir que proveedor externo se convierta en fuente de verdad.

## 13. Salida de Gate 2

Gate 2 se considera completo cuando:
- la arquitectura de datos e integración esté documentada;
- las fronteras de ownership estén alineadas con Gate 1;
- las capacidades de reutilización estén explícitas;
- no se haya implementado runtime productivo;
- cualquier tabla/endpoints/migración futura quede diferida a gates posteriores y requiera evidencia exacta.

Siguiente Gate permitido: Gate 3 — AI Provider Router, empezando por discovery/contract y sólo después implementación controlada.
