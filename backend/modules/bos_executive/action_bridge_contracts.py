# E3D_AUTHORIZED_ACTION_BRIDGE_V1

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorizedActionRequest:
    recommendation_id: str
    action_type: str
    target_ref: str
    requested_by: str
    acting_scopes: tuple[str, ...]
    evaluated_at: str
    confirmation_granted: bool = False
    financial_gate_approved: bool = False
    idempotency_key: str | None = None
    dry_run: bool = True


@dataclass(frozen=True)
class AuthorizedActionDecision:
    allowed: bool
    reasons: tuple[str, ...]
    recommendation_id: str
    action_type: str
    target_ref: str
    capability: str | None
    procedure: str | None
    required_permission: str | None
    execution_channel: str | None
    idempotency_key: str | None
    audit_ref: str
    outcome_status: str
