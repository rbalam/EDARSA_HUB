# BOS Enterprise Capability Map - Gate 1

Estado: CERTIFIED / DOCUMENTAL CLOSURE
Fecha de materializacion: 2026-09-17
Fuente de evidencia certificada: `EDARSAHUB-ENTERPRISE-CAPABILITY-MAP-GATE1-R2-20260914`
Certificacion fuente: `CERTIFIED_READ_ONLY`
Quality gate fuente: `PASS`
Production touched en discovery: `false`
Files changed en discovery: `[]`

## 1. Objetivo

Este dossier materializa la interpretacion arquitectonica del Enterprise Capability Map de EDARSAHUB BOS a partir de la evidencia READ_ONLY ya certificada. No agrega discovery adicional.

## 2. Principio rector

`REUSE -> CONSOLIDATE -> EXTRACT -> EXTEND -> CREATE_ONLY_WHEN_PROVEN_MISSING`

Crear una capacidad paralela queda prohibido cuando ya existe infraestructura canonica suficiente.

## 3. Matriz de capacidades

| Capability | Owner / implementacion observada | Estado | Decision vinculante |
|---|---|---|---|
| Identity / Auth | `backend/modules/auth` | CANONICAL | REUSE |
| RBAC / Effective permissions | Auth + RBAC middleware + `menu-permissions` | CANONICAL | REUSE |
| Enterprise menus | SQL + protected frontend layout | EXISTS | CONSOLIDATE |
| Empresa / unidad / sucursal context | Auth context + resolvers | TRANSVERSAL | REUSE |
| Connection resolution | `core.connection_resolver`, server registry, SQL-first factories | CANONICAL_INFRA | EXTEND/SLIM |
| Scheduler | `core/scheduler/scheduler_manager.py` | CANONICAL_INFRA | REUSE |
| Jobs / resync / backfill | Scheduler + administrative APIs | EXISTS | CONSOLIDATE_ON_SCHEDULER |
| System / capability registry | `catalogos_sistemas.py` + capability resolver | EXISTS_PARTIAL | EXTEND_EXISTING |
| SoftRestaurant | Integration adapter/pattern | EXISTS | ADAPTER |
| MPRO | Integration adapter/pattern | EXISTS | ADAPTER |
| NetPay | Scheduler/resync integration | EXISTS | ADAPTER |
| vtiger | CRM external integration references | EXISTS_PARTIAL | EXTEND |
| Twilio | Notification provider | EXISTS | REUSE_PROVIDER |
| SAP / Oracle / Dynamics | Enterprise connector references | PARTIAL | ADAPTER_PATTERN |
| BBVA / Banorte | Banking integrations | PARTIAL | UNIVERSAL_BANKING_ADAPTERS |
| Dashboards / KPIs | Multiple consumers over backend services | EXISTS | CONSOLIDATE_METRIC_TRUTH |
| Workflows | Multiple domain implementations | EXISTS_FRAGMENTED | CONSOLIDATE_PRIMITIVES |
| Audit / evidence | APIs, tests, dossiers and Worker evidence | EXISTS | REUSE_COMMON_PATTERN |
| Agent runtime | Multiple `core.agent_*` capabilities | EXISTS_CORE_HEAVY | EXTRACT_PROGRESSIVELY |
| Universal Worker | `tools/mirror_sync` | CANONICAL_EXTERNAL_EXECUTION | KEEP_OUTSIDE_CORE |
| Repository READ_ONLY audit | `READ_ONLY` + `repository_contract_audit` | CANONICAL | REUSE |

## 4. Binding rules

1. EDARSAHUB SQL Server remains the canonical operational brain.
2. MongoDB may not be introduced as operational truth or fallback.
3. Administrative dashboards may not depend directly on LIVE sources.
4. Reuse canonical Auth/RBAC; no domain RBAC forks.
5. Reuse canonical Scheduler; no parallel schedulers.
6. Extend the existing capability registry before creating a new registry or catalog.
7. Integration providers must be adapters of shared infrastructure, not independent subsystems.
8. BBVA and Banorte are adapters of a Universal Banking Connector.
9. KPI consumers must share canonical metric definitions and sources.
10. Domain workflows must reuse common primitives when repetition is proven.
11. New files under `backend/core` require explicit evidence that the capability is truly transversal.
12. Universal Worker remains outside application Core.
13. Any CREATE decision must document why REUSE, CONSOLIDATE, EXTRACT and EXTEND were insufficient.
14. Production changes require explicit authorization.

## 5. Gate 1 closure

`GATE_1=PASS`
`SOURCE_CERTIFICATION=CERTIFIED_READ_ONLY`
`EXISTING_CAPABILITIES=MANY`
`REUSABLE_INFRASTRUCTURE=HIGH`
`TRUE_GREENFIELD_NEED=LOW`
`DUPLICATION_RISK=MEDIUM_HIGH`
`ORPHAN_CAPABILITIES=PRESENT`
`CORE_OVERGROWTH=CONFIRMED`
`NEW_CORE_CAPABILITIES_REQUIRED=NO`
`NEW_PARALLEL_SYSTEMS_REQUIRED=NO`

Gate 1 queda documentalmente cerrado cuando este dossier sea integrado como unico cambio funcionalmente neutro, con `git_diff_check=PASS`, `production_touched=false` y sin DDL/DML.
