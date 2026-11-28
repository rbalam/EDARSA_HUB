# EDARSAHUB BOS Agent Harness / Agent Control Plane V1

## Objetivo
Construir una capa gobernada para registrar, seleccionar, coordinar, ejecutar y auditar agentes, skills, modelos, herramientas y dominios de negocio sin sustituir fuentes canonicas, RBAC ni Worker Universal. Mobile y Marketing/Customer Intelligence son dominios formales de primera clase.

## Principios
- SQL-first para datos empresariales persistentes; no Mongo como fuente nueva, primaria ni cache canonica.
- Ningun agente, skill, modelo o herramienta concede autoridad. La autoridad efectiva procede de RBAC + Capability Policy + Procedure/Skill Policy + Execution Gate.
- Worker Universal sigue siendo el ejecutor determinista de cambios de repositorio; no shell arbitrario.
- Production fuera de alcance V1 hasta autorizacion humana separada.
- Los agentes describen capacidades requeridas y no quedan amarrados a un proveedor de IA.
- Skills externas entran por cuarentena, procedencia, checksum, licencia, validacion, sandbox y aprobacion.
- Catalogos canonicos no se duplican. Cliente_Catalogo sigue siendo identidad canonica; RRR/Customer360, CRM, ventas y Communications se reutilizan.
- Mobile nunca es fuente de verdad; cache/outbox locales son temporales.
- Marketing no crea maestro de clientes ni cola paralela si la infraestructura actual puede extenderse.
- Toda ejecucion produce evidencia, correlacion, pruebas, findings y certificacion.
- `backend/core` queda congelado para crecimiento funcional nuevo; Agent Harness, Mobile y Marketing/CX deben vivir fuera del Core salvo excepcion formal posterior.

## Arquitectura logica
Intent -> Context Resolver -> Canonical Source Guard -> RBAC -> Capability Policy -> Procedure/Skill Policy -> Planner -> Agent/Skill Router -> Plan DAG -> Execution Compiler -> Execution Gate -> Executor Registry -> Tests -> Security/Red Team -> Repair Gate -> Regression -> Certification -> Human Release Decision.

Executors V1: Worker Universal, AI Gateway, Agent Reach y Communications. Futuros conectores/MCP solo mediante adaptador y policy.

## Agent Registry
Contrato `edarsahub.bos-agent.v1`: id, version, role, domains, status, allowed_skills, capability_ceiling, scope_ceiling, max_risk, allowed_data_classifications, model_requirements, budgets, max_concurrency, red_team_required, human_approval_thresholds y provenance.

Agentes V1: bos-architect, bos-backend, bos-frontend, bos-database, bos-rbac, bos-security, bos-test, bos-redteam, bos-reviewer, bos-release-certifier, bos-mobile-architect, bos-mobile-developer, bos-mobile-security, bos-marketing-strategist, bos-customer-intelligence, bos-campaign-orchestrator, bos-content, bos-experimentation y bos-attribution.

## Skill Registry
Contrato `edarsahub.bos-skill.v1`: id, version, source/provider, origin, provenance, checksum, license, domain, description, entrypoint, required_capabilities, allowed_scopes, max_risk, allowed_data_classifications, external_egress, allowed_executors/tools, dependencies, conflicts, validations, lifecycle y adoption. Skills son procedimientos gobernados, nunca permisos.

Fuentes posibles: BOS Native, ECC, OpenAI, Anthropic, GitHub, Community y Custom. Flujo obligatorio: SOURCE -> QUARANTINE -> provenance/license/checksum -> manifest parse -> forbidden capability/egress scan -> dependency scan -> sandbox tests -> BOS adaptation -> approval -> registry.

## Planner y Router
Planner side-effect-free y reproducible produce `edarsahub.bos-plan.v1`. Router selecciona el agente/skill de menor privilegio capaz de cumplir cada paso. Nunca expande scopes, capacidades, riesgo o presupuesto.

## Execution Compiler
Para Worker Universal genera solo `edarsahub.worker-job.v2` con acciones/checks allow-listed, paths exactos y production_allowed=false. No convierte texto libre en shell. Para AI Gateway y Agent Reach reutiliza sus contratos actuales. Para Communications usara policy de egress transaccional purpose-bound.

## Evidence / Session Ledger
Correlacionar request_id, plan_id, execution_id, gate_id, agent_id, skill/version/checksum, executor, branch/worktree, source revisions, files changed, checks, findings, budgets/cost, timestamps y certification. Reutilizar worker/requests y worker/results mientras sean suficientes. Persistencia SQL adicional prohibida hasta evidencia AH1.

## Red Team
Verificador separado del corrector. Cobertura minima: RBAC, cross-tenant Empresa/Unidad, fuentes canonicas, SQL injection, secretos, idempotencia, concurrencia, replay, prompt/tool injection, supply-chain, PII/consentimiento, egress, abuso de campanas, atribucion/fraude, mobile storage/tokens y offline sync.

## Marketing / Customer Intelligence
Cliente_Catalogo + Cliente_Contactos + CRM + Ventas + RRR/Customer360 -> Customer Intelligence -> Segmentation/propensity/churn/CLV -> Campaign/Journey Orchestrator -> Consent+Purpose+Budget+Policy -> Communications/Ads Adapter -> Email/WhatsApp/SMS/Push/Ads -> Delivery/Conversion -> Attribution/Experimentation/ROI.

No crear cliente paralelo. Reutilizar RRR para loyalty, reputation, engagement, segmentacion, activacion y atribucion. Reutilizar Communications para providers, retry, dedup y logs segun evidencia AH1.

La regla global que bloquea egress no-PUBLIC no se relaja. Se disena `ApprovedProcessorEgressPolicy` separado para comunicaciones reales, exigiendo capability explicita, RBAC, finalidad, consentimiento/base valida, proveedor/canal aprobado, minimizacion PII, scopes Empresa/Unidad/cliente, presupuesto/rate-limit, quiet hours, opt-out, retencion y audit_id. Envio real deshabilitado durante bootstrap.

## Mobile
Baseline recomendado: React Native + TypeScript con Expo development builds/prebuild, conservando ADR y escape hatch. Arquitectura: Mobile UI -> Application/Use Cases -> BOS API Client -> Encrypted Local Cache + Outbox/Inbox -> Sync Engine -> Device Services(camera/QR/barcode/NFC/location/push/biometrics) -> BOS APIs -> SQL canonico.

Toda escritura offline incluye operation_uuid, idempotency_key, user_id, installation_id, empresa/unidad, base_version cuando aplique, timestamp, payload_hash y operation_type. Servidor decide ACCEPT/REJECT/CONFLICT/RETRY/REVIEW. No last-write-wins generico para dinero, inventarios o decisiones auditables. Tokens en Keychain/Keystore, sin secretos en SQLite, minimizacion/TTL, device revoke, logout remoto y logs sin PII/secretos.

## Core Slimming
No agregar archivos funcionales nuevos a `backend/core`. Antes de cualquier extraccion del Core existente: grafo de imports, consumidores, clasificacion KEEP_CORE/EXTRACT_DOMAIN/EXTRACT_PLATFORM/ADAPTER/LEGACY_REMOVE, pruebas de caracterizacion y migracion incremental. No big-bang ni pseudo-Core shared/common/utils.

## Gates
AH0 Master Architecture.
AH1 SQL Discovery READ ONLY.
AH2 Registry Foundation fuera de backend/core.
AH3 Planner + Router.
AH4 Worker Compiler Adapter.
AH5 Evidence + Provenance.
AH6 Security + Red Team.
AH7 Marketing/CX en MOCK/DRY_RUN.
AH8 Mobile contracts/scaffold.
AH9 Control Plane.
AH10 E2E Simulation.
AH11 LOCAL_EXECUTE solo Development.
AH12 Development Certification.

Cada gate pasa solo con status terminal, quality_gate=PASS, tests=PASS, production_touched=false y blockers=[]. Production queda excluida.

## Bootstrap
El Worker actual es determinista. Cada gate posterior debe convertirse en acciones exactas usando evidencia del anterior. No se adivina schema ni se duplica infraestructura. AH1 certificado es la base para AH2.
