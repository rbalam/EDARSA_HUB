from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.agent_capability_policy import DataClassification, RiskLevel


class CapabilityRegistryError(ValueError):
    pass


@dataclass(frozen=True)
class DomainCapabilitySpec:
    code: str
    domain: str
    procedure: str
    required_permission: str
    risk: RiskLevel
    data_classification: DataClassification
    tool_codes: tuple[str, ...]
    side_effect: bool = False
    approval_required: bool = False

    def __post_init__(self) -> None:
        for field_name in ('code', 'domain', 'procedure', 'required_permission'):
            if not str(getattr(self, field_name) or '').strip():
                raise CapabilityRegistryError(f'{field_name.upper()}_REQUIRED')
        if not self.tool_codes:
            raise CapabilityRegistryError('TOOL_CODES_REQUIRED')
        if self.side_effect and not self.approval_required:
            raise CapabilityRegistryError('SIDE_EFFECT_REQUIRES_APPROVAL')


_CAPABILITIES: Mapping[str, DomainCapabilitySpec] = {
    'FINANCE_RECONCILIATION_ANALYZE': DomainCapabilitySpec(
        code='FINANCE_RECONCILIATION_ANALYZE',
        domain='FINANZAS',
        procedure='finance-reconciliation-analyze',
        required_permission='TES_CUADRES_Z_VER',
        risk=RiskLevel.R1,
        data_classification=DataClassification.FINANCIAL_PRIVATE,
        tool_codes=('edarsahub_sql_read', 'finance_reconciliation_read'),
    ),
    'FINANCE_RECONCILIATION_PROPOSE': DomainCapabilitySpec(
        code='FINANCE_RECONCILIATION_PROPOSE',
        domain='FINANZAS',
        procedure='finance-reconciliation-propose',
        required_permission='TES_CUADRES_Z_VER',
        risk=RiskLevel.R2,
        data_classification=DataClassification.FINANCIAL_PRIVATE,
        tool_codes=('edarsahub_sql_read', 'finance_reconciliation_read', 'ai_inference'),
    ),
    'COMMUNICATION_READ': DomainCapabilitySpec(
        code='COMMUNICATION_READ',
        domain='COMMUNICATIONS',
        procedure='communication-read',
        required_permission='NOTIFICACIONES_VER',
        risk=RiskLevel.R1,
        data_classification=DataClassification.CONFIDENTIAL,
        tool_codes=('communications_read',),
    ),
    'COMMUNICATION_CLASSIFY': DomainCapabilitySpec(
        code='COMMUNICATION_CLASSIFY',
        domain='COMMUNICATIONS',
        procedure='communication-classify',
        required_permission='NOTIFICACIONES_VER',
        risk=RiskLevel.R1,
        data_classification=DataClassification.CONFIDENTIAL,
        tool_codes=('communications_read', 'ai_inference'),
    ),
    'COMMUNICATION_DRAFT_REPLY': DomainCapabilitySpec(
        code='COMMUNICATION_DRAFT_REPLY',
        domain='COMMUNICATIONS',
        procedure='communication-draft-reply',
        required_permission='NOTIFICACIONES_VER',
        risk=RiskLevel.R2,
        data_classification=DataClassification.CONFIDENTIAL,
        tool_codes=('communications_read', 'ai_inference'),
    ),
}


def get_domain_capability(code: str) -> DomainCapabilitySpec:
    key = str(code or '').strip().upper()
    try:
        return _CAPABILITIES[key]
    except KeyError as exc:
        raise CapabilityRegistryError('CAPABILITY_NOT_REGISTERED') from exc


def list_domain_capabilities(domain: str | None = None) -> tuple[DomainCapabilitySpec, ...]:
    items = tuple(_CAPABILITIES.values())
    if domain is None:
        return tuple(sorted(items, key=lambda item: item.code))
    token = str(domain or '').strip().upper()
    return tuple(sorted((item for item in items if item.domain == token), key=lambda item: item.code))
