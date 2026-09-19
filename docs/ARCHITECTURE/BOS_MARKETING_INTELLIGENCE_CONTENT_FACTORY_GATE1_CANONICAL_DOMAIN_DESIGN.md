# BOS Marketing Intelligence & Content Factory — Gate 1 Canonical Domain Design

Estado: CANONICAL DESIGN — NO IMPLEMENTATION

## 1. Principios obligatorios

- EDARSAHUB SQL Server es el cerebro y la fuente canonica.
- No Mongo como fuente operativa o de verdad.
- No LIVE para dashboards/reportes administrativos; usar datos canonicos sincronizados/snapshots.
- No hardcodear IDs de empresa, unidad, sucursal, margenes, proveedores ni aliases.
- No crecer `backend/core` salvo infraestructura genuinamente transversal.
- Marketing es un bounded context de BOS, no un ERP/CRM paralelo.
- Render de imagen, video y audio ocurre en proveedores externos; BOS orquesta, gobierna, audita y persiste metadata/costos/derechos.
- Toda capacidad nueva debe pasar por REUSE/ALIGN/CANONICALIZE/EXTEND/NEW_CAPABILITY_REQUIRED antes de crear objetos.

## 2. Evidencia Gate 0 usada como base

Gate 0A certifico infraestructura existente de SQL-first, RBAC, scheduler/jobs, Comercial/ventas, integraciones, multiempresa y contratos distribuidos entre backend/frontend/tools/docs.

Gate 0B certifico objetos SQL existentes relevantes, incluyendo `Cliente_Catalogo`, `Cliente_Contactos`, `Cliente_Direcciones`, `Venta_Cotizaciones`, `Venta_Pedidos`, `CRM_Leads`, `CRM_Oportunidades`, `Comercial_Competidores`, `Comercial_CompetidoresCatalogo`, `Comercial_CompetidoresListas`, `Comercial_CompetidoresListasDetalle`, `Comercial_CompetidoresMenuItems`, `Comercial_CompetidoresUnidad` y `Comercial_Ingesta_Competencia`, ademas de objetos comerciales, costos/margenes y presupuestos relacionados.

## 3. Bounded contexts y ownership

### 3.1 Marketing Intelligence
Owns:
- Trend Radar / Social Listening.
- Competitor Intelligence de marketing, reutilizando canon Comercial_Competidores*.
- Brand DNA.
- Audience DNA.
- Content DNA.
- Hook/Pattern Intelligence.
- recomendaciones de timing/canal/formato.
- learning loop de marketing.

No owns:
- cliente maestro, venta, pedido, cotizacion, lead u oportunidad canonica.
- costo financiero/contable canonico.
- autenticacion/RBAC.

### 3.2 Content Factory
Owns:
- briefs.
- guiones/copys/versiones.
- solicitudes de generacion AI.
- metadata de assets creativos.
- derechos/licencias/aprobaciones.
- variantes y experimentos A/B.

Regla: binarios pesados y rendering no viven en SQL ni en Core; SQL conserva referencias canonicas, ownership, hash/metadata, costo, proveedor, estado, derechos y auditoria.

### 3.3 Campaign Orchestrator
Owns:
- definicion de campana de marketing.
- objetivos/KPIs de campana.
- calendario y slots.
- asignacion de contenido/canal.
- workflow de aprobacion.
- estado de publicacion.

No duplica Finanzas_Presupuestos ni CRM. Referencia sus IDs canonicos.

### 3.4 Publishing Connectors
Owns:
- adaptadores por plataforma.
- publish/schedule/status/remote-id.
- errores/reintentos/idempotencia.

No owns credenciales: usar Secret Manager/configuracion canonica.

### 3.5 Attribution & ROI
Owns:
- modelos de atribucion de marketing.
- touchpoints de marketing.
- snapshots/resultados de atribucion.
- costo por campana/contenido/canal/proveedor.

No redefine venta/ingreso/margen. Consume KPIs canonicos de Comercial y costos/presupuestos canonicos de Finanzas. La verdad de ventas sigue siendo la definida por Comercial.

### 3.6 AI Provider Router de Marketing
Owns:
- seleccion de proveedor/modelo por capability, costo, SLA, calidad y politica.
- request metadata, usage, costo y trazabilidad.
- fallback controlado entre proveedores.

Debe implementarse dentro del bounded context o modulo transversal AI ya existente si Gate 2 demuestra ownership reusable. No crear un segundo router si ya existe uno canonico.

## 4. Clasificacion inicial de capacidades

| Capacidad | Clasificacion Gate 1 | Ownership canonico |
|---|---|---|
| Clientes/contactos/direcciones | REUSE | CRM/Comercial |
| Leads/oportunidades | REUSE | CRM |
| Cotizaciones/pedidos | REUSE | Venta/Comercial |
| Competidores | REUSE + EXTEND solo si falta metadata marketing | Comercial |
| Ventas/KPI ingreso | REUSE | Comercial |
| Costos/margenes | REUSE | Comercial/Finanzas segun contrato existente |
| Presupuesto | REUSE | Finanzas |
| RBAC | REUSE | Sistema/Core transversal |
| Scheduler | REUSE | infraestructura transversal |
| Trend radar/social listening | NEW_CAPABILITY_REQUIRED salvo evidencia posterior | Marketing Intelligence |
| Brand DNA | NEW_CAPABILITY_REQUIRED | Marketing Intelligence |
| Audience DNA | NEW_CAPABILITY_REQUIRED, referenciando CRM | Marketing Intelligence |
| Content DNA | NEW_CAPABILITY_REQUIRED | Marketing Intelligence |
| Content factory | NEW_CAPABILITY_REQUIRED | Marketing |
| Campaign orchestrator | NEW_CAPABILITY_REQUIRED con referencias canonicas | Marketing |
| Publishing connectors | NEW_CAPABILITY_REQUIRED/EXTEND segun integraciones existentes | Marketing Integrations |
| Attribution | NEW_CAPABILITY_REQUIRED | Marketing Analytics |
| ROI marketing | EXTEND/NEW segun contrato Finanzas, sin duplicar venta/costo | Marketing Analytics |
| AI virtual talent | NEW_CAPABILITY_REQUIRED como capability de Content Factory | Marketing |
| AI provider routing | ALIGN/REUSE primero; NEW solo si no existe router canonico | Marketing/AI infrastructure |

## 5. Entidades conceptuales nuevas permitidas para diseno

Estas son entidades conceptuales, NO autorizacion para crear tablas:

- MarketingCampaign
- MarketingBrief
- ContentAsset
- ContentVariant
- ContentExperiment
- BrandProfile
- AudienceProfile
- ContentPattern
- TrendSignal
- SocialListeningSignal
- PublishingTarget
- PublishingExecution
- MarketingTouchpoint
- AttributionResult
- AIContentRequest
- AIProviderUsage
- CreativeRightsRecord

Cada entidad debe incluir alcance multiempresa cuando corresponda y relaciones mediante IDs canonicos, nunca aliases hardcodeados.

## 6. Relaciones canonicas obligatorias

- Campaign -> empresa/unidad/sucursal mediante relaciones oficiales.
- Campaign -> presupuesto Finanzas por FK/logical reference canonica.
- Campaign/Audience -> CRM segment/cliente/lead/oportunidad por referencias canonicas.
- Attribution -> venta/pedido/cliente por identificadores canonicos.
- ContentAsset -> campaign/brief/provider/rights/audit.
- PublishingExecution -> asset/campaign/channel/remote id/idempotency key.
- AIProviderUsage -> provider/model/request/cost/currency/status.

## 7. Eventos de dominio propuestos

Solo contrato conceptual para Gate 1:

- MARKETING_CAMPAIGN_CREATED
- MARKETING_CAMPAIGN_APPROVED
- CONTENT_BRIEF_APPROVED
- CONTENT_GENERATION_REQUESTED
- CONTENT_ASSET_READY
- CONTENT_ASSET_APPROVED
- CONTENT_PUBLISH_REQUESTED
- CONTENT_PUBLISHED
- CONTENT_PUBLISH_FAILED
- MARKETING_TOUCHPOINT_RECORDED
- ATTRIBUTION_RECALCULATED
- MARKETING_EXPERIMENT_COMPLETED

Gate 2 debe decidir si estos eventos se persisten/transportan con mecanismos ya existentes antes de crear nueva infraestructura.

## 8. Fronteras que no deben cruzarse

- Marketing no escribe ventas canonicas.
- Marketing no duplica `CRM_Leads`/`CRM_Oportunidades`.
- Marketing no duplica clientes/contactos/direcciones.
- Marketing no duplica presupuesto/contabilidad.
- Marketing no crea scheduler paralelo.
- Marketing no crea sistema RBAC paralelo.
- Marketing no usa Mongo como verdad.
- Marketing no introduce conexiones LIVE para reporting administrativo.
- Marketing no almacena secretos en tablas de dominio ni archivos del repo.
- Marketing no mete rendering pesado en `backend/core`.

## 9. Gate de salida

Gate 1 se considera completo cuando este ownership sea aceptado como contrato de arquitectura y no existan duplicados evidentes contra los objetos canonicos detectados en Gate 0.

El siguiente Gate permitido es Gate 2 — Data & Integration Architecture. Gate 2 debe hacer discovery exacto de esquemas/columnas/relaciones, integraciones/provider infrastructure y decidir reutilizacion versus nuevas estructuras. No autoriza implementacion productiva.
