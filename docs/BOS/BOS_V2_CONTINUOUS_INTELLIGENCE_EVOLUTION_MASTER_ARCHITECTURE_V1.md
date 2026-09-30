# EDARSAHUB BOS V2 — Continuous Intelligence & Evolution — Master Architecture V1

Status: PROPOSED CANONICAL ARCHITECTURE CONTRACT
Scope: Development architecture/documentation only
Production: OUT OF SCOPE
Core policy: NO NEW FUNCTIONAL GROWTH UNDER `backend/core/**`

## 1. Purpose

Extend BOS V1 without creating a parallel platform. BOS V2 adds governed continuous improvement while preserving SQL Server canonical truth, RBAC/policies, Agent Harness, Universal Worker, existing registries, Evidence/Provenance, Control Plane, E2E Simulation, Red Team, BOS Executive and the existing AI routing kernel.

BOS V1 learns to operate under governance. BOS V2 learns to improve how it operates, also under governance.

## 2. Constitution

1. SQL Server remains canonical business truth.
2. No duplicate source of truth.
3. No new Mongo operational truth/cache/fallback/lock by normal architecture.
4. No user-facing LIVE source unless explicitly governed.
5. AI never grants authority.
6. Authority remains RBAC + Capability Policy + Procedure Policy + Execution Gate.
7. Domain Services own canonical business mutation.
8. Models, providers, agents, skills and adapters are replaceable implementations.
9. Evidence and provenance are mandatory for governed execution.
10. Critical changes must be reversible or safely disableable.
11. Production requires explicit governed authorization.
12. Learning may observe, evaluate, simulate and propose; it may not autonomously redefine canonical business truth.
13. New functional growth under `backend/core/**` is prohibited unless a future formal architecture exception explicitly changes this policy.

## 3. Stable and fast layers

Stable layer:
- business identity
- canonical entities/data
- domain contracts
- authority/RBAC
- policies
- audit
- business processes
- durable knowledge and decision lineage

Fast layer:
- models
- AI providers
- agent implementations
- skills
- prompts
- frameworks
- SDKs
- UI technology
- search/vector engines
- external adapters

Fast-layer components must depend on stable contracts, not the reverse.

## 4. Existing owners to REUSE/EXTEND

REUSE:
- Agent Registry
- Skill Registry
- Planner/Router
- Evidence + Provenance
- AH9 Control Plane
- AH10 E2E Simulation
- AH6 Security/Red Team
- Universal Worker
- Capability Policy / Procedure Policy / Execution Gate
- BOS Enterprise Capability Map
- BOS Executive causal/evidence contracts

EXTEND/ALIGN:
- existing provider/model registry and model-routing policy kernel
- Context Resolver toward a governed Context Compiler
- BOS Executive recommendation -> requested action -> policy decision -> outcome lineage
- EKS toward formal Architecture Memory/ADR governance
- AH9 Control Plane toward evolution observability
- AH10 simulation toward candidate/experiment simulation
- AH5 Evidence toward experiment/model/decision outcome provenance

DO NOT CREATE:
- second Agent Registry
- second Skill Registry
- second Executor Registry
- independent AI Provider Router
- parallel evidence ledger
- parallel source of business truth
- parallel BOS execution engine

## 5. New bounded capability candidates

The following are candidates only after evidence-based design; they must live outside `backend/core/**`:

- Technology Radar
- Architecture Guardian
- Dependency / Blast Radius / Obsolescence Intelligence
- Improvement Lifecycle / Experiment orchestration
- Decision / Outcome / Learning extension
- Continuous model/agent evaluation and benchmark orchestration
- Rollout intelligence: shadow/canary/safe-disable/retirement
- Architecture Memory / ADR formalization
- capability health/SLO/drift extensions
- Digital Architecture Twin as derived metadata, never source of truth

## 6. Context and knowledge

Existing Context Resolver remains the owner boundary. BOS V2 may extend it into a Context Compiler that constructs minimum-sufficient context from canonical facts, EKS knowledge, applicable policies, decision history, capability ownership, scopes and provenance.

Obsidian or any future workspace may be a human knowledge interface/adapter only. It is not canonical truth and must remain replaceable.

Knowledge promotion lifecycle:
RAW -> REVIEWED -> VERIFIED -> CANONICAL -> SUPERSEDED/RETIRED

## 7. Memory boundaries

Evidence Memory:
- owner: Agent Harness / audit patterns

Operational History:
- owner: canonical domain SQL

Decision Memory:
- extension of BOS Executive/governance lineage

Architecture Memory:
- owner: EKS / architecture governance

Learning Memory:
- owner: BOS Evolution bounded context

No generic catch-all "memory" table is authorized by this contract.

## 8. Intelligence and model fabric

The existing AI routing kernel/provider-model registry is extended, not duplicated.

Deployment classes may include:
- CLOUD_MANAGED
- PRIVATE_CLOUD
- SELF_HOSTED
- LOCAL_SERVER
- EDGE

Certification must be capability-specific, never global.

Competence does not imply authority.

## 9. Evolution loop

OBSERVE
-> DETECT
-> ASSESS
-> SIMULATE
-> BENCHMARK
-> PROPOSE
-> GOVERN
-> EXECUTE THROUGH EXISTING AUTHORIZED PATHS
-> MEASURE
-> LEARN
-> IMPROVE

Evolution Engine does not directly mutate canonical business truth or Production.

## 10. Improvement lifecycle

DISCOVERED
-> ASSESSED
-> EXPERIMENTAL
-> VALIDATED
-> APPROVED
-> ROLLOUT
-> MEASURED
-> ADOPTED | REJECTED | RETIRED

Every improvement should carry:
- capability
- owner
- current baseline
- hypothesis
- candidate
- expected benefit
- risk
- affected dependencies
- tests/benchmarks
- rollback/safe-disable
- evidence
- outcome

## 11. Architecture Guardian

Architecture Guardian compares actual implementation against EKS, ADRs, canonical contracts, ownership and policy.

Finding modes:
- ADVISE
- WARN
- DENY

Critical examples:
- new operational Mongo dependency
- new functional file under backend/core
- duplicate canonical catalog/master
- direct AI-to-SQL mutation bypass
- independent AI provider router
- unrestricted provider SDK inside domain business logic
- user-facing LIVE source without governed exception

## 12. Architecture Memory / ADR

ADR minimum contract:
- id
- title
- date
- status
- context
- decision
- alternatives
- consequences
- evidence
- owner
- supersedes
- related incidents

States:
PROPOSED / ACCEPTED / SUPERSEDED / DEPRECATED / REJECTED

Machine-enforceable rules may be compiled from accepted ADRs where deterministic enforcement is possible.

## 13. Rollout and safe evolution

Candidate promotion:
LAB -> BENCHMARK -> CERTIFIED_CANDIDATE -> SHADOW -> CANARY -> LIMITED -> GENERAL

Rollout never grants authority beyond existing RBAC/policy.

Rollback options:
- ROLLBACK
- ROLL_FORWARD
- SAFE_DISABLE

History/evidence/canonical data must be preserved.

## 14. Health and observability

Three levels:
- system health
- capability health
- business outcome health

Future capability health may expose:
HEALTHY / DEGRADED / STALE / PARTIAL / BLOCKED / UNKNOWN

A stale source must never be silently converted to zero/null when a last valid value exists.

## 15. Anti-obsolescence

Each replaceable technology should expose:
- owner
- consumers
- version
- support/EOL horizon
- security/license status
- replacement path
- data portability
- contract boundary

Architecture goal:
preserve business meaning, authority, history and contracts while replacing implementations.

## 16. Core Slimming rule

`backend/core/**` is frozen for new functional growth.

If future discovery identifies relevant legacy/core behavior, classify only as:
- KEEP_CORE
- EXTRACT_PLATFORM_CANDIDATE
- EXTRACT_DOMAIN_CANDIDATE
- ADAPTER_CANDIDATE

No extraction is authorized by this document. Extraction requires separate evidence, characterization tests, dependency graph, rollback and surgical gates.

## 17. Gates

H0 — AS-IS Capability Gap Discovery — completed READ_ONLY
H1 — Master Architecture / Constitution
H2 — Architecture Memory / ADR
H3 — Knowledge + Context Evolution
H4 — Decision / Outcome / Learning
H5 — Technology + Dependency Radar
H6 — Continuous AI/Agent Evaluation
H7 — Architecture Guardian
H8 — Improvement Lifecycle
H9 — Rollout / Shadow / Canary
H10 — Evolution Engine E2E Certification

Each implementation gate must preserve:
- Production untouched unless separately and explicitly authorized
- no parallel source of truth
- no duplicate registry/router/executor
- no new functional growth in backend/core
- evidence and terminal certification before next physical gate

## 18. Governing maxim

EDARSAHUB MAY AUTONOMOUSLY OBSERVE, LEARN, TEST, SIMULATE AND PROPOSE.

EDARSAHUB MAY NOT AUTONOMOUSLY CHANGE BUSINESS TRUTH OR CRITICAL PRODUCTION STATE WITHOUT GOVERNED AUTHORIZATION.

The BOS must be able to replace every technology it uses without losing the business it understands.
