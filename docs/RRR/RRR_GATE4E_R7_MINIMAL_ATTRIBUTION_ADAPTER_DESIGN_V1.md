# RRR Gate 4E R7 - Minimal Customer Attribution Adapter Design V1

## 1. Purpose

Design the minimum deterministic adapter required to attribute a canonical EDARSAHUB customer to a canonical commercial fact before writing any row to `dbo.RRR_Eventos`.

This gate is DESIGN ONLY. It does not implement code, DDL, DML, jobs, endpoints, migrations, Customer360 V3, or Production changes.

## 2. Certified input evidence

- Customer master remains `dbo.Cliente_Catalogo.ClienteID`.
- Commercial truth remains the Commercial domain, using `fecha_operacion`, valid/non-cancelled facts and monetary semantics reconciled with `ventas_sin_propina`.
- `dbo.Comercial_Inteligencia_VentasDetalleProducto` contains commercial detail and exposes native commercial identifiers such as `numero_ticket`, `id_transaccion`, `folio_origen`, `fecha_operacion`, `cancelado_origen` and `es_kpi_valido`, but it does not expose `ClienteID`.
- `dbo.RRR_Eventos` already supports `ClienteID`, `EmpresaID`, `UnidadNegocioID`, optional `VentaID`, `SourceSystem`, `SourceKey`, `FechaOperacion`, validation/antifraud status and uniqueness by `(SourceSystem, SourceKey)`.
- `backend/modules/edge/comandero_local_core.py` already creates an immutable `id_transaccion_global` UUID and an idempotent offline FIFO.
- The current Comandero payload does not capture canonical `ClienteID` and does not prove a deterministic join to the commercial fact.
- `backend/modules/edge/gestor_sincronizacion_rafagas.py` can transport the payload to the HUB, but transport success is not attribution success.
- CRM can resolve a known canonical `ClienteID`, but CRM must not be used to infer a POS customer heuristically.
- KPI sync and aggregated Comercial Runtime are not customer-attribution sources.

## 3. Design decision

Create one minimal attribution adapter in the RRR/application boundary. Do not create a new customer master, sale master or shadow ledger.

The adapter has two independent responsibilities:

1. **Identity capture**: carry an explicitly selected/authenticated `ClienteID` from the operating channel into the transaction envelope.
2. **Commercial correlation**: prove a 1:1 relation between the Comandero transaction UUID and a valid native commercial fact before any `RRR_Eventos` write.

Both conditions are mandatory. Possessing only a customer or only a ticket is insufficient.

## 4. SourceKey rule

For Comandero-originated events:

- Candidate `SourceSystem`: `COMANDERO` or a centrally registered equivalent code; the concrete code must come from configuration/catalog, not a hardcoded branch-specific alias.
- Candidate `SourceKey`: the existing immutable `id_transaccion_global` UUID generated when the comanda transaction is created.
- The UUID is the RRR origin idempotency key. It is not automatically the commercial ticket id.
- `UQ_RRR_Eventos_Source(SourceSystem, SourceKey)` is the final duplicate guard once the attribution is certified.

The UUID must remain stable through offline queueing, retries and synchronization.

## 5. Explicit ClienteID capture

The Comandero/POS transaction contract must be extended to accept an optional canonical `ClienteID int`.

Allowed sources for that field:
- authenticated customer session already mapped to `Cliente_Catalogo`;
- QR/member/customer selector that resolves directly to `Cliente_Catalogo.ClienteID`;
- explicit operator selection from a canonical customer search;
- an already-certified deterministic external identity mapping.

Forbidden:
- name similarity;
- approximate phone/email;
- amount/date matching;
- table/seat identity;
- device/IP identity;
- waiter inference;
- fuzzy CRM account matching.

Anonymous transactions remain anonymous and must not create attributed RRR events.

## 6. Minimal transaction envelope

The adapter input contract should carry, at minimum:

- `source_transaction_uuid` = Comandero `id_transaccion_global`;
- `cliente_id` = canonical `ClienteID`, nullable until explicitly captured;
- `source_system`;
- canonical unit context resolvable to `UnidadNegocioID`;
- canonical company context resolvable to `EmpresaID`;
- optional canonical branch context when the source provides it;
- `occurred_at_utc`;
- local/source timestamp only as trace evidence;
- native POS correlation fields once known:
  - `commercial_system`;
  - `native_transaction_id`;
  - `native_ticket_number`;
  - `native_folio`;
- payload hash for replay detection.

No company/unit/sucursal identifiers may be hardcoded in the adapter.

## 7. Deterministic commercial join

The adapter must not join `id_transaccion_global` directly to Comercial unless the commercial source actually persists that UUID.

The required bridge is:

`Comandero UUID -> certified native POS acknowledgement -> Comercial native key`

The native acknowledgement must return or persist an exact source identifier that the canonical commercial detail also contains.

### SoftRestaurant candidate

Current canonical detail derives:
- `numero_ticket = folio`;
- `id_transaccion = 'SOFT:' + folio`;
- `folio_origen = folio`;
- validity from non-cancelled cheque state.

Therefore a Comandero transaction can be attributed to SoftRestaurant only when the POS write/acknowledgement deterministically returns the exact SoftRestaurant folio/ticket created for that UUID.

A later consumer may then prove an exact join using the full commercial scope:
- source system = SoftRestaurant;
- official unit/server mapping;
- exact native folio/ticket/id_transaccion;
- operational date window derived by the canonical operational-date logic.

The folio alone must never be treated as globally unique across units/systems.

### MPRO and other systems

The same rule applies: the source adapter must return the exact native transaction key used by the canonical Comercial detail for that system. No synthetic mapping may be invented.

## 8. Correlation states

Before creating `RRR_Eventos`, the adapter should conceptually pass through these states:

1. `CAPTURED`
   - UUID exists.
   - Customer may or may not be present.

2. `CUSTOMER_IDENTIFIED`
   - Canonical `ClienteID` explicitly present and valid.

3. `COMMERCIAL_PENDING`
   - Waiting for native POS acknowledgement/correlation.

4. `COMMERCIAL_MATCHED`
   - Exactly one valid native commercial fact identified.

5. `COMMERCIAL_VALIDATED`
   - `es_kpi_valido = 1` or the canonical equivalent.
   - not cancelled.
   - operational date established.
   - source/unit/company context agrees.

6. `RRR_EVENT_ELIGIBLE`
   - identity + commercial fact + idempotency all certified.

Only state 6 may write `RRR_Eventos`.

These states are design semantics; R7 does not authorize a new table to store them. A later implementation gate must first decide whether existing queue/event infrastructure can carry them without duplication.

## 9. RRR_Eventos write contract

When all preconditions pass, the event must use:

- `ClienteID`: explicit canonical customer.
- `EmpresaID`: resolved by official corporate relations.
- `UnidadNegocioID`: resolved by official unit relations.
- `VentaID`: NULL unless a real certified mapping to `Venta_Encabezado.VentaID` exists.
- `TipoEvento`: configured RRR commercial-activity event code.
- `SourceSystem`: registered source code.
- `SourceKey`: Comandero UUID for Comandero-originated attribution.
- `FechaOperacion`: from the matched commercial fact/canonical operational-date semantics.
- `OcurridoAtUtc`: source occurrence timestamp normalized to UTC.
- `PayloadHash`: hash of the stable attribution payload/evidence.
- `EstadoValidacion`: valid only after deterministic commercial match.
- `EstadoAntifraude`: produced by the RRR antifraud layer before earning.
- `MotivoRechazo`: populated for rejected/replayed/conflicting attributions where applicable.

The adapter must not copy monetary truth into `RRR_Eventos`; monetary Customer360 metrics are derived from the canonical commercial fact.

## 10. Cancellation and reversal

If the native commercial fact is later cancelled/reversed:
- the attribution link remains auditable;
- the commercial event must cease to count as valid activity;
- any RRR earning generated from it must be reversed through the RRR ledger contract, never by deleting history;
- cancellation detection must use canonical commercial state, not only the Comandero local state.

## 11. Replay and conflict rules

Reject or quarantine:
- same `SourceSystem + SourceKey` with a different `ClienteID`;
- same Comandero UUID mapped to more than one native commercial transaction;
- one native transaction attributed to multiple customers unless a future explicit split-allocation contract exists;
- source retries with different material payload hashes;
- missing canonical unit/company resolution;
- commercial fact not found;
- more than one commercial fact for the supposed exact native key;
- cancelled/invalid commercial fact.

Retries with identical identity, correlation and payload evidence must be idempotent.

## 12. Customer360 boundary

R7 does not change `vw_RRR_ClienteActividadComercial` or `vw_RRR_Customer360`.

Customer360 V3 remains blocked until:
1. the producer/adapter is implemented;
2. deterministic correlation is exercised in Development;
3. `RRR_Eventos` has attributed events with certified commercial joins;
4. cancellation/reversal behavior is proven;
5. a READ_ONLY reconciliation demonstrates customer activity computed from attributed events matches the canonical commercial truth without propina and without invalid/cancelled facts.

## 13. Minimum implementation surface for the next gate

The next implementation/preflight gate should prefer extending existing components rather than creating parallel infrastructure:

- **EXTEND** `backend/modules/edge/comandero_local_core.py`
  - carry explicit canonical `ClienteID`;
  - preserve UUID unchanged;
  - remove hardcoded device/business identity from attribution logic and resolve through existing configuration.

- **EXTEND** `backend/modules/edge/gestor_sincronizacion_rafagas.py`
  - preserve the complete attribution envelope through retries;
  - treat HUB acceptance separately from commercial correlation success.

- **REUSE** canonical corporate/unit resolvers and operational-date helpers.

- **REUSE** Comercial canonical detail and source-specific native identifiers.

- **ADD only if absent after preflight** a cohesive RRR attribution service/adapter responsible for validation and `RRR_Eventos` persistence.
  It must not live in core and must not duplicate Comercial sync logic.

No new SQL table is authorized by this design.

## 14. Acceptance criteria for a future implementation

A Development canary must prove all of the following with synthetic/test-isolated or authorized non-production data:

- one Comandero UUID survives retries unchanged;
- one explicit `ClienteID` survives unchanged;
- exact native POS acknowledgement is persisted/carried;
- exact commercial fact is found 1:1;
- operational date equals canonical Comercial semantics;
- cancelled fact is rejected/reversed;
- repeated identical delivery does not duplicate `RRR_Eventos`;
- conflicting customer attribution is blocked;
- `VentaID` remains NULL when no certified mapping exists;
- no fuzzy matching is used;
- no MongoDB operational dependency;
- no Production touch.

## 15. Decision

Gate4E-R7 authorizes only this minimal adapter design.

The next gate must be a repository + SQL READ_ONLY preflight of the exact implementation points and receiver route before any code mutation. Customer360 V3 remains blocked.
