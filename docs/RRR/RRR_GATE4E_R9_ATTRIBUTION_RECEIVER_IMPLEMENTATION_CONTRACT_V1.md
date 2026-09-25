# RRR Gate 4E R9 - Attribution Receiver Implementation Contract V1

## 1. Scope
Design only. No code mutation, no DDL, no DML, no Customer360 V3, no Production.

## 2. R8 certified matrix
- EXTEND: backend/modules/edge/comandero_local_core.py
- EXTEND: backend/modules/edge/gestor_sincronizacion_rafagas.py
- REUSE: api.sync_receiver sync_agent JWT helpers and server_id validation contract
- REUSE: core.unidades_service.UnidadesService
- REUSE: core.corporate_filters.service.CorporateFilterService
- REUSE: canonical operational-date helpers
- REUSE: Comercial_Inteligencia_VentasDetalleProducto and its native identifiers
- ADD: bounded context backend/modules/rrr
- DO_NOT_TOUCH: Customer360 V2 until attribution is proven
- DO_NOT_TOUCH: KPI sync semantics
- DO_NOT_TOUCH: core for RRR domain logic

## 3. Route decision
The existing Edge client calls POST /v1/sync/transaccion, but no runtime route exists and the backend ingress contract routes /api/*.
Do not create a root-level /v1 exception.

Canonical endpoint:
POST /api/rrr/attribution/transactions

The Edge sender must be updated to call this canonical route.

## 4. Authentication
Reuse machine-to-machine sync_agent JWT semantics:
- Bearer token
- type=sync_agent
- server_id bound to token
- payload server_id must equal token server_id

Do not duplicate token generation or JWT verification code.
If direct import from api.sync_receiver would create unacceptable coupling, extract only the generic sync-agent auth helper to an existing neutral integration/auth location in a later implementation gate; do not grow core with RRR business logic.

## 5. New bounded context
Add only if implementation gate is approved:
backend/modules/rrr/
- __init__.py
- schemas.py
- attribution_service.py
- routes.py

Responsibilities:
- schemas.py: transport contract only
- routes.py: auth, HTTP validation, status mapping
- attribution_service.py: canonical customer validation, org resolution, deterministic commercial correlation, idempotent RRR_Eventos persistence

No duplicate repository abstraction unless required by existing module conventions.

## 6. Request contract
Required:
- server_id
- agent_id or token-derived agent identity
- source_transaction_uuid
- source_system
- occurred_at_utc
- unit source identifier resolvable canonically

Optional until known:
- cliente_id
- commercial_system
- native_transaction_id
- native_ticket_number
- native_folio
- payload_hash

The server must reject payload server_id mismatch.

## 7. Customer identity
cliente_id is accepted only when:
- present in dbo.Cliente_Catalogo
- explicitly captured by the operating channel
- not inferred by fuzzy rules

Anonymous transaction:
- transport may be acknowledged
- no attributed RRR_Eventos row is created

## 8. Org resolution
Resolve canonical organization using existing helpers:
- UnidadNegocioID -> dbo.Unidades_Negocio.id
- EmpresaID -> official relationship
- Sucursal only when source supplies an official mapping

No hardcoded business IDs.

## 9. Commercial correlation
Do not correlate by time/amount/name.

Required exact bridge:
Comandero UUID -> native POS acknowledgement -> canonical Comercial native key

For SoftRestaurant:
- exact folio/ticket returned by the POS acknowledgement
- canonical detail uses numero_ticket/folio_origen and id_transaccion SOFT:<folio>
- scope by system + official unit + operational date

For MPRO:
- exact native key returned by source adapter
- canonical detail uses system-specific id_transaccion

The service must require exactly one valid commercial fact.

## 10. Commercial validity
Before RRR eligibility:
- es_kpi_valido = 1
- cancelado_origen = 0
- fecha_operacion from canonical commercial fact
- organization scope consistent
- exact key yields one logical ticket/transaction

Multiple product-detail rows for one ticket are not multiple commercial transactions; correlation must collapse on the canonical transaction identity.

## 11. RRR_Eventos write
Use existing table and constraints:
- ClienteID canonical
- EmpresaID canonical
- UnidadNegocioID canonical
- VentaID NULL unless certified mapping exists
- SourceSystem from registered/configured source
- SourceKey = Comandero UUID for Comandero-originated transaction
- FechaOperacion from Comercial
- OcurridoAtUtc normalized UTC
- PayloadHash stable when provided/computed
- EstadoValidacion
- EstadoAntifraude
- MotivoRechazo when applicable

Rely on UQ_RRR_Eventos_Source(SourceSystem,SourceKey) for final duplicate guard.

## 12. Response semantics
Return explicit states:
- ACCEPTED_PENDING_CUSTOMER
- ACCEPTED_PENDING_COMMERCIAL
- ATTRIBUTED
- IDEMPOTENT_REPLAY
- REJECTED_CONFLICT
- REJECTED_INVALID_CUSTOMER
- REJECTED_INVALID_COMMERCIAL
- REJECTED_ORG_SCOPE

HTTP acceptance is not equivalent to RRR attribution success.

## 13. Edge changes
comandero_local_core.py:
- carry cliente_id when explicitly known
- preserve id_transaccion_global unchanged
- remove attribution dependence on hardcoded device/business IDs

gestor_sincronizacion_rafagas.py:
- call /api/rrr/attribution/transactions
- send Authorization Bearer sync_agent token via canonical secret/config mechanism
- preserve attribution envelope through retries
- mark local queue synchronized only according to the agreed transport/attribution state contract

## 14. Server registration
Mount modules.rrr.routes.router through api_router so the final route is under /api.
Do not add a root-level app route.

## 15. Tests required before non-production canary
- UUID preserved across retries
- explicit ClienteID preserved
- missing ClienteID does not create RRR_Eventos
- invalid ClienteID rejected
- server_id mismatch rejected
- exact SoftRestaurant correlation succeeds
- exact MPRO correlation succeeds when fixture exists
- no exact commercial match => no event
- multiple logical matches => conflict
- cancelled/invalid fact => no earning-eligible event
- duplicate identical replay => no duplicate row
- same SourceKey with different ClienteID => conflict
- VentaID remains NULL without certified mapping
- org resolution uses canonical helpers
- no Mongo operational dependency
- no Production touch

## 16. Next gate
R10 may implement only this surface in Development after certifying this document. Customer360 V3 remains blocked until a non-production canary proves attributed events and a READ_ONLY reconciliation.
