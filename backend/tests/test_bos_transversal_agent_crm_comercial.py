import pytest

from core.agent_capability_policy import PolicyContext
from modules.agent_harness.crm_adapter import CRMAgentRequest, authorize_crm_agent
from modules.agent_harness.commercial_adapter import CommercialAgentRequest, authorize_commercial_agent
from modules.agent_harness.transversal_capability_registry import list_domain_capabilities


def context(capability, scopes):
    caps=frozenset({capability}); scope_set=frozenset(scopes)
    limits={'runtime_seconds':60,'files_changed':0,'lines_changed':0,'external_calls':0,'sql_rows':1000,'inference_cost_usd':1.0}
    return PolicyContext(caps,caps,caps,caps,scope_set,scope_set,scope_set,scope_set,limits)


def test_gate3_registry_extends_same_registry_without_side_effects():
    crm=list_domain_capabilities('CRM'); commercial=list_domain_capabilities('COMERCIAL')
    assert {x.code for x in crm} == {'CRM_SUMMARIZE','CRM_NEXT_ACTION_PROPOSE'}
    assert {x.code for x in commercial} == {'COMMERCIAL_KPI_ANALYZE','COMMERCIAL_ACTION_PROPOSE'}
    assert all(not x.side_effect for x in crm + commercial)


def test_crm_uses_comercial_permission_and_scope():
    req=CRMAgentRequest('crm-1',1,2,'CRM_SUMMARIZE')
    scopes={'empresa:1','unidad:2','domain:crm','resource:crm'}
    gate,policy=authorize_crm_agent(req,{'allowed':True,'permission':'COMERCIAL_VER','empresa_id':1,'unidad_id':2},context(req.capability,scopes))
    assert gate.allowed is True
    assert policy.external_egress is False and policy.production_allowed is False


def test_crm_fails_closed_on_permission_mismatch():
    req=CRMAgentRequest('crm-2',1,2)
    scopes={'empresa:1','unidad:2','domain:crm','resource:crm'}
    gate,_=authorize_crm_agent(req,{'allowed':True,'permission':'COMERCIAL_DASHBOARD_VER','empresa_id':1,'unidad_id':2},context(req.capability,scopes))
    assert gate.allowed is False
    assert gate.reasons == ('REQUESTER_PERMISSION_MISMATCH',)


def test_commercial_kpi_uses_comercial_permission_and_scope():
    req=CommercialAgentRequest('com-1',1,2,'COMMERCIAL_KPI_ANALYZE')
    scopes={'empresa:1','unidad:2','domain:comercial','resource:commercial-kpis'}
    gate,policy=authorize_commercial_agent(req,{'allowed':True,'permission':'COMERCIAL_VER','empresa_id':1,'unidad_id':2},context(req.capability,scopes))
    assert gate.allowed is True
    assert policy.external_egress is False and policy.production_allowed is False


def test_commercial_fails_closed_on_business_scope():
    req=CommercialAgentRequest('com-2',1,2)
    scopes={'empresa:1','unidad:2','domain:comercial','resource:commercial-kpis'}
    gate,_=authorize_commercial_agent(req,{'allowed':True,'permission':'COMERCIAL_VER','empresa_id':1,'unidad_id':99},context(req.capability,scopes))
    assert gate.allowed is False
    assert gate.reasons == ('REQUESTER_BUSINESS_SCOPE_MISMATCH',)


def test_cross_domain_capabilities_rejected():
    with pytest.raises(Exception, match='CRM_CAPABILITY_REQUIRED'):
        CRMAgentRequest('crm-3',1,2,'COMMERCIAL_KPI_ANALYZE')
    with pytest.raises(Exception, match='COMMERCIAL_CAPABILITY_REQUIRED'):
        CommercialAgentRequest('com-3',1,2,'CRM_SUMMARIZE')
