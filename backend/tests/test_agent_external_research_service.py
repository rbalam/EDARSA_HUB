from pathlib import Path
from types import SimpleNamespace

from core.agent_capability_policy import BudgetRequest, DataClassification, PolicyContext, PolicyRequest, RiskLevel
from core.agent_external_research_service import execute_external_research
from core.agent_runtime_activation import RuntimeEnvironment

def context():
    caps=frozenset({'EXTERNAL_RESEARCH'}); scopes=frozenset({'external:web'})
    return PolicyContext(user_allowed_capabilities=caps,agent_allowed_capabilities=caps,environment_allowed_capabilities=caps,policy_allowed_capabilities=caps,user_allowed_scopes=scopes,agent_allowed_scopes=scopes,environment_allowed_scopes=scopes,policy_allowed_scopes=scopes,budget_limits={'runtime_seconds':60,'files_changed':0,'lines_changed':0,'external_calls':1,'sql_rows':0,'inference_cost_usd':0.0})

def request(capabilities=frozenset({'EXTERNAL_RESEARCH'}), calls=1):
    return PolicyRequest(capabilities=capabilities,scopes=frozenset({'external:web'}),risk=RiskLevel.R1,data_classification=DataClassification.PUBLIC,budgets=BudgetRequest(external_calls=calls),external_egress=True,production_allowed=False,privilege_expansion=False,procedure='agent-reach-external-research')

def lock(tmp_path: Path):
    p=tmp_path/'versions.lock'; p.write_text('IMAGE_REPOSITORY=edarsa/agent-reach-runtime\nIMAGE_TAG=test-tag\n',encoding='utf-8'); return p

def test_service_chains_authorization_policy_activation_and_executor(monkeypatch,tmp_path):
    fake=SimpleNamespace(success=True,returncode=0,stdout='public result',stderr='',argv=('docker',),query='public trends')
    monkeypatch.setattr('core.agent_external_research_service.execute_agent_reach_public_search',lambda *a,**k: fake)
    out=execute_external_research({'allowed':True},'public trends',request(),context(),lock(tmp_path),docker_binary='/usr/bin/docker')
    assert out.result is fake and out.evidence.allowed is True and out.evidence.success is True
    assert out.evidence.procedure=='agent-reach-external-research' and out.evidence.effective_scopes==('external:web',)
    assert out.evidence.external_calls_budget==1 and out.evidence.production_touched is False
    assert 'public trends' not in repr(out.evidence) and len(out.evidence.query_sha256)==64

def test_requester_denial_never_calls_executor(monkeypatch,tmp_path):
    called={'v':False}
    monkeypatch.setattr('core.agent_external_research_service.execute_agent_reach_public_search',lambda *a,**k: called.__setitem__('v',True))
    out=execute_external_research({'allowed':False,'reason':'RBAC_DENIED'},'public trends',request(),context(),lock(tmp_path))
    assert out.result is None and out.evidence.reason=='RBAC_DENIED' and called['v'] is False

def test_over_budget_denied_policy_first(tmp_path):
    out=execute_external_research({'allowed':True},'public trends',request(calls=2),context(),lock(tmp_path))
    assert out.result is None and out.evidence.allowed is False

def test_output_limit_is_fail_closed(monkeypatch,tmp_path):
    fake=SimpleNamespace(success=True,returncode=0,stdout='x'*65537,stderr='',argv=('docker',),query='public trends')
    monkeypatch.setattr('core.agent_external_research_service.execute_agent_reach_public_search',lambda *a,**k: fake)
    out=execute_external_research({'allowed':True},'public trends',request(),context(),lock(tmp_path),docker_binary='/usr/bin/docker')
    assert out.result is None and out.evidence.reason=='AGENT_REACH_OUTPUT_LIMIT_EXCEEDED'

def test_ai_capability_cannot_enter_external_research_path(tmp_path):
    out=execute_external_research({'allowed':True},'public trends',request(capabilities=frozenset({'AI_INFERENCE'})),context(),lock(tmp_path))
    assert out.result is None and out.evidence.allowed is False

def test_production_remains_fail_closed(monkeypatch,tmp_path):
    called={'v':False}
    monkeypatch.setattr('core.agent_external_research_service.execute_agent_reach_public_search',lambda *a,**k: called.__setitem__('v',True))
    out=execute_external_research({'allowed':True},'public trends',request(),context(),lock(tmp_path),environment=RuntimeEnvironment.PRODUCTION)
    assert out.result is None and out.evidence.allowed is False and called['v'] is False
