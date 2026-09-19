from __future__ import annotations

from dataclasses import dataclass

CUSTOMER360_SCHEMA = 'edarsahub.bos-customer360-view.v1'
MARKETING_ACTIVATION_SCHEMA = 'edarsahub.bos-marketing-activation.v1'
CUSTOMER_MASTER = 'dbo.Cliente_Catalogo'
CANONICAL_CUSTOMER_SOURCES = (
    'dbo.Cliente_Catalogo',
    'dbo.Cliente_Contactos',
    'dbo.Cliente_Direcciones',
    'dbo.Cliente_UsuariosPortal',
    'dbo.CRM_Cuentas',
    'dbo.CRM_PostventaEncuestas',
    'dbo.RRR_Eventos',
    'dbo.RRR_LedgerMovimientos',
    'dbo.RRR_ScoreHistorial',
    'dbo.RRR_RankingHistorial',
)
ALLOWED_CHANNELS = frozenset({'email', 'whatsapp', 'sms', 'push', 'ads'})


class MarketingPolicyError(ValueError):
    pass


def _required(value: object, field: str) -> str:
    token = str(value or '').strip()
    if not token:
        raise MarketingPolicyError(f'{field}_REQUIRED')
    return token


@dataclass(frozen=True)
class Customer360Request:
    customer_id: int
    empresa_id: int
    unidad_id: int

    def __post_init__(self) -> None:
        if self.customer_id <= 0:
            raise MarketingPolicyError('CUSTOMER_ID_INVALID')
        if self.empresa_id <= 0:
            raise MarketingPolicyError('EMPRESA_ID_INVALID')
        if self.unidad_id <= 0:
            raise MarketingPolicyError('UNIDAD_ID_INVALID')

    def view_contract(self) -> dict[str, object]:
        return {
            'schema': CUSTOMER360_SCHEMA,
            'customer_master': CUSTOMER_MASTER,
            'customer_id': self.customer_id,
            'empresa_id': self.empresa_id,
            'unidad_id': self.unidad_id,
            'sources': CANONICAL_CUSTOMER_SOURCES,
            'materialized_customer_copy': False,
        }


@dataclass(frozen=True)
class MarketingActivationRequest:
    activation_id: str
    customer_id: int
    empresa_id: int
    unidad_id: int
    purpose: str
    legal_basis: str
    consent_granted: bool
    channel: str
    scope: str
    budget_limit: float
    quiet_hours_respected: bool = True
    opted_out: bool = False

    def __post_init__(self) -> None:
        _required(self.activation_id, 'ACTIVATION_ID')
        if self.customer_id <= 0:
            raise MarketingPolicyError('CUSTOMER_ID_INVALID')
        if self.empresa_id <= 0 or self.unidad_id <= 0:
            raise MarketingPolicyError('BUSINESS_SCOPE_INVALID')
        _required(self.purpose, 'PURPOSE')
        _required(self.legal_basis, 'LEGAL_BASIS')
        _required(self.scope, 'SCOPE')
        if not self.consent_granted:
            raise MarketingPolicyError('CONSENT_REQUIRED')
        if self.opted_out:
            raise MarketingPolicyError('CUSTOMER_OPTED_OUT')
        if not self.quiet_hours_respected:
            raise MarketingPolicyError('QUIET_HOURS_VIOLATION')
        if self.channel not in ALLOWED_CHANNELS:
            raise MarketingPolicyError('CHANNEL_NOT_APPROVED')
        if self.budget_limit <= 0:
            raise MarketingPolicyError('BUDGET_LIMIT_INVALID')

    def to_envelope(self) -> dict[str, object]:
        return {
            'schema': MARKETING_ACTIVATION_SCHEMA,
            'activation_id': self.activation_id,
            'customer_master': CUSTOMER_MASTER,
            'customer_id': self.customer_id,
            'empresa_id': self.empresa_id,
            'unidad_id': self.unidad_id,
            'purpose': self.purpose,
            'legal_basis': self.legal_basis,
            'consent_granted': True,
            'channel': self.channel,
            'scope': self.scope,
            'budget_limit': float(self.budget_limit),
            'communications_executor_required': True,
            'direct_send_allowed': False,
        }
