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
    permission_aliases: tuple[str, ...] = ()
    side_effect: bool = False
    approval_required: bool = False

    def __post_init__(self) -> None:
        for field_name in ('code', 'domain', 'procedure', 'required_permission'):
            if not str(getattr(self, field_name) or '').strip():
                raise CapabilityRegistryError(f'{field_name.upper()}_REQUIRED')
        if not self.tool_codes:
            raise CapabilityRegistryError('TOOL_CODES_REQUIRED')
        if any(not str(value or '').strip() for value in self.permission_aliases):
            raise CapabilityRegistryError('PERMISSION_ALIAS_INVALID')
        if self.side_effect and not self.approval_required:
            raise CapabilityRegistryError('SIDE_EFFECT_REQUIRES_APPROVAL')

    @property
    def accepted_permissions(self) -> tuple[str, ...]:
        values = (self.required_permission, *self.permission_aliases)
        return tuple(dict.fromkeys(str(value).strip().upper() for value in values if str(value or '').strip()))


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
    'PURCHASE_ANALYZE': DomainCapabilitySpec(
        code='PURCHASE_ANALYZE',
        domain='COMPRAS',
        procedure='purchase-analyze',
        required_permission='COMPRAS_FACT_VER',
        risk=RiskLevel.R1,
        data_classification=DataClassification.CONFIDENTIAL,
        tool_codes=('edarsahub_sql_read', 'compras_read'),
    ),
    'PURCHASE_PROPOSE': DomainCapabilitySpec(
        code='PURCHASE_PROPOSE',
        domain='COMPRAS',
        procedure='purchase-propose',
        required_permission='COMPRAS_FACT_VER',
        risk=RiskLevel.R2,
        data_classification=DataClassification.CONFIDENTIAL,
        tool_codes=('edarsahub_sql_read', 'compras_read', 'ai_inference'),
    ),
    'INVENTORY_ANALYZE': DomainCapabilitySpec(
        code='INVENTORY_ANALYZE',
        domain='INVENTARIOS',
        procedure='inventory-analyze',
        required_permission='COMPRAS_INVENTARIOS_VER',
        risk=RiskLevel.R1,
        data_classification=DataClassification.CONFIDENTIAL,
        tool_codes=('edarsahub_sql_read', 'inventory_read'),
    ),
    'INVENTORY_REPLENISHMENT_PROPOSE': DomainCapabilitySpec(
        code='INVENTORY_REPLENISHMENT_PROPOSE',
        domain='INVENTARIOS',
        procedure='inventory-replenishment-propose',
        required_permission='COMPRAS_INVENTARIOS_VER',
        risk=RiskLevel.R2,
        data_classification=DataClassification.CONFIDENTIAL,
        tool_codes=('edarsahub_sql_read', 'inventory_read', 'compras_read', 'ai_inference'),
    ),
    'CRM_SUMMARIZE': DomainCapabilitySpec(
        code='CRM_SUMMARIZE',
        domain='CRM',
        procedure='crm-summarize',
        required_permission='COMERCIAL_VER',
        risk=RiskLevel.R1,
        data_classification=DataClassification.CONFIDENTIAL,
        tool_codes=('edarsahub_sql_read', 'crm_read', 'ai_inference'),
    ),
    'CRM_NEXT_ACTION_PROPOSE': DomainCapabilitySpec(
        code='CRM_NEXT_ACTION_PROPOSE',
        domain='CRM',
        procedure='crm-next-action-propose',
        required_permission='COMERCIAL_VER',
        risk=RiskLevel.R2,
        data_classification=DataClassification.CONFIDENTIAL,
        tool_codes=('edarsahub_sql_read', 'crm_read', 'ai_inference'),
    ),
    'COMMERCIAL_KPI_ANALYZE': DomainCapabilitySpec(
        code='COMMERCIAL_KPI_ANALYZE',
        domain='COMERCIAL',
        procedure='commercial-kpi-analyze',
        required_permission='COMERCIAL_VER',
        risk=RiskLevel.R1,
        data_classification=DataClassification.CONFIDENTIAL,
        tool_codes=('edarsahub_sql_read', 'commercial_read'),
    ),
    'COMMERCIAL_ACTION_PROPOSE': DomainCapabilitySpec(
        code='COMMERCIAL_ACTION_PROPOSE',
        domain='COMERCIAL',
        procedure='commercial-action-propose',
        required_permission='COMERCIAL_VER',
        risk=RiskLevel.R2,
        data_classification=DataClassification.CONFIDENTIAL,
        tool_codes=('edarsahub_sql_read', 'commercial_read', 'ai_inference'),
    ),
    'HR_DOCUMENT_ANALYZE': DomainCapabilitySpec(
        code='HR_DOCUMENT_ANALYZE',
        domain='RH',
        procedure='hr-document-analyze',
        required_permission='RH_VER',
        permission_aliases=('RECURSOS_HUMANOS_VER',),
        risk=RiskLevel.R1,
        data_classification=DataClassification.PII,
        tool_codes=('edarsahub_sql_read', 'hr_read', 'ai_inference'),
    ),
    'HR_EMPLOYEE_CASE_SUMMARIZE': DomainCapabilitySpec(
        code='HR_EMPLOYEE_CASE_SUMMARIZE',
        domain='RH',
        procedure='hr-employee-case-summarize',
        required_permission='RH_VER',
        permission_aliases=('RECURSOS_HUMANOS_VER',),
        risk=RiskLevel.R2,
        data_classification=DataClassification.PII,
        tool_codes=('edarsahub_sql_read', 'hr_read', 'ai_inference'),
    ),
    'HR_RECRUITMENT_ASSIST': DomainCapabilitySpec(
        code='HR_RECRUITMENT_ASSIST',
        domain='RH',
        procedure='hr-recruitment-assist',
        required_permission='RH_VER',
        permission_aliases=('RECURSOS_HUMANOS_VER',),
        risk=RiskLevel.R2,
        data_classification=DataClassification.PII,
        tool_codes=('edarsahub_sql_read', 'hr_read', 'ai_inference'),
    ),
    'HR_PAYROLL_EXPLAIN': DomainCapabilitySpec(
        code='HR_PAYROLL_EXPLAIN',
        domain='RH',
        procedure='hr-payroll-explain',
        required_permission='RH_VER',
        permission_aliases=('RECURSOS_HUMANOS_VER',),
        risk=RiskLevel.R2,
        data_classification=DataClassification.FINANCIAL_PRIVATE,
        tool_codes=('edarsahub_sql_read', 'hr_read', 'payroll_read', 'ai_inference'),
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
