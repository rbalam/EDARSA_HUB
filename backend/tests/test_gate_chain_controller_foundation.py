import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync.gate_chain_controller import GateChainContractError, decide_next, validate_chain

def chain():
    return {'schema':'edarsahub.gate-chain.v1','chain_id':'TEST','max_hops':5,'start_gate_id':'A','gates':[{'gate_id':'A','job_id':'job-a','mutation_class':'READ_ONLY','next_gate_ids':['B']},{'gate_id':'B','job_id':'job-b','mutation_class':'CODE_MUTATION','authorization_class':'PREAUTHORIZED_CODE_MUTATION','next_gate_ids':[]}]}

def certified(job_id):
    return {'job_id':job_id,'status':'READ_ONLY_COMPLETE','certification':'CERTIFIED_READ_ONLY','quality_gate':'PASS','tests':'PASS','blockers':[],'production_touched':False}

def test_start_gate_ready_without_existing_job():
    d=decide_next(chain(),completed_results=[],existing_job_ids=[],hop_count=0); assert d.action=='READY' and d.next_gate_id=='A'

def test_existing_start_job_is_not_duplicated():
    assert decide_next(chain(),completed_results=[],existing_job_ids=['job-a'],hop_count=0).action=='WAIT'

def test_certified_gate_advances_only_to_declared_next_gate():
    d=decide_next(chain(),completed_results=[certified('job-a')],existing_job_ids=[],hop_count=1,authorization_classes=['PREAUTHORIZED_CODE_MUTATION']); assert d.action=='READY' and d.next_gate_id=='B'

def test_mutation_requires_declared_authorization():
    d=decide_next(chain(),completed_results=[certified('job-a')],existing_job_ids=[],hop_count=1); assert d.action=='STOP' and d.reason=='AUTHORIZATION_REQUIRED'

def test_existing_next_job_is_never_duplicated():
    d=decide_next(chain(),completed_results=[certified('job-a')],existing_job_ids=['job-b'],hop_count=1,authorization_classes=['PREAUTHORIZED_CODE_MUTATION']); assert d.action=='WAIT' and d.reason=='NEXT_JOB_ALREADY_EXISTS'

def test_max_hops_stops_chain():
    d=decide_next(chain(),completed_results=[],existing_job_ids=[],hop_count=5); assert d.action=='STOP' and d.reason=='MAX_HOPS_REACHED'

def test_unknown_next_gate_is_invalid():
    cfg=chain(); cfg['gates'][0]['next_gate_ids']=['DOES_NOT_EXIST']
    try:
        validate_chain(cfg)
    except GateChainContractError as exc:
        assert 'UNKNOWN_NEXT_GATE' in str(exc)
    else:
        raise AssertionError('expected contract error')

def test_production_gate_is_fail_closed():
    cfg=chain(); cfg['gates'][1]['mutation_class']='PRODUCTION'; cfg['gates'][1]['authorization_class']=''
    d=decide_next(cfg,completed_results=[certified('job-a')],existing_job_ids=[],hop_count=1); assert d.action=='STOP' and d.reason=='PRODUCTION_FORBIDDEN'


def test_start_gate_enforces_same_authorization_and_security_controls_as_subsequent_gates():
    # Start gate PRODUCTION forbidden
    cfg_prod = chain()
    cfg_prod['gates'][0]['mutation_class'] = 'PRODUCTION'
    d = decide_next(cfg_prod, completed_results=[], existing_job_ids=[], hop_count=0)
    assert d.action == 'STOP' and d.reason == 'PRODUCTION_FORBIDDEN'

    # Start gate production_allowed=True forbidden
    cfg_pa = chain()
    cfg_pa['gates'][0]['production_allowed'] = True
    d = decide_next(cfg_pa, completed_results=[], existing_job_ids=[], hop_count=0)
    assert d.action == 'STOP' and d.reason == 'PRODUCTION_FORBIDDEN'

    # Start gate requires_human_decision forbidden
    cfg_hum = chain()
    cfg_hum['gates'][0]['requires_human_decision'] = True
    d = decide_next(cfg_hum, completed_results=[], existing_job_ids=[], hop_count=0)
    assert d.action == 'STOP' and d.reason == 'HUMAN_DECISION_REQUIRED'

    # Start gate authorization_class required
    cfg_auth = chain()
    cfg_auth['gates'][0]['mutation_class'] = 'CODE_MUTATION'
    cfg_auth['gates'][0]['authorization_class'] = 'PREAUTHORIZED_CODE_MUTATION'
    d_denied = decide_next(cfg_auth, completed_results=[], existing_job_ids=[], hop_count=0)
    assert d_denied.action == 'STOP' and d_denied.reason == 'AUTHORIZATION_REQUIRED'
    d_ok = decide_next(
        cfg_auth,
        completed_results=[],
        existing_job_ids=[],
        hop_count=0,
        authorization_classes=['PREAUTHORIZED_CODE_MUTATION'],
    )
    assert d_ok.action == 'READY' and d_ok.next_gate_id == 'A' and len(d_ok.decision_digest) == 64


def test_rbac_scope_and_traceable_authorization_enforcement():
    from datetime import datetime, timezone

    cfg = chain()
    cfg['gates'][0].update({
        'mutation_class': 'CODE_MUTATION',
        'authorization_class': 'PREAUTHORIZED_CODE_MUTATION',
        'require_traceable_authorization': True,
        'required_rbac': {'roles': ['SuperAdministrador'], 'permissions': ['worker:submit']},
        'required_scope': {'empresa_id': '1', 'unidad_negocio_pk': '10', 'domain': 'RH'},
    })
    now = datetime(2026, 11, 19, 10, 0, 0, tzinfo=timezone.utc)

    # Missing context -> fail closed
    assert decide_next(
        cfg, completed_results=[], existing_job_ids=[], hop_count=0,
        authorization_classes=['PREAUTHORIZED_CODE_MUTATION'], now_utc=now,
    ).reason == 'AUTHORIZATION_NOT_TRACEABLE'

    # Expired authorization -> fail closed
    base_ctx = {
        'authorization_id': 'AUTH-2026-001',
        'expires_at_utc': '2026-11-19T12:00:00Z',
        'revoked': False,
        'actor_role': 'SuperAdministrador',
        'actor_permissions': ['worker:submit', 'worker:status'],
        'scope': {'empresa_id': '1', 'unidad_negocio_pk': '10', 'domain': 'RH'},
    }
    assert decide_next(
        cfg, completed_results=[], existing_job_ids=[], hop_count=0,
        authorization_classes=['PREAUTHORIZED_CODE_MUTATION'],
        authorization_context={**base_ctx, 'expires_at_utc': '2026-11-19T09:00:00Z'},
        now_utc=now,
    ).reason == 'AUTHORIZATION_EXPIRED'

    # Revoked authorization -> fail closed
    assert decide_next(
        cfg, completed_results=[], existing_job_ids=[], hop_count=0,
        authorization_classes=['PREAUTHORIZED_CODE_MUTATION'],
        authorization_context={**base_ctx, 'revoked': True},
        now_utc=now,
    ).reason == 'AUTHORIZATION_REVOKED'

    # Wrong RBAC role -> fail closed
    assert decide_next(
        cfg, completed_results=[], existing_job_ids=[], hop_count=0,
        authorization_classes=['PREAUTHORIZED_CODE_MUTATION'],
        authorization_context={**base_ctx, 'actor_role': 'Operador'},
        now_utc=now,
    ).reason == 'RBAC_AUTHORIZATION_DENIED'

    # Wrong empresa/unidad/domain scope -> fail closed
    assert decide_next(
        cfg, completed_results=[], existing_job_ids=[], hop_count=0,
        authorization_classes=['PREAUTHORIZED_CODE_MUTATION'],
        authorization_context={**base_ctx, 'scope': {'empresa_id': '2', 'unidad_negocio_pk': '10', 'domain': 'RH'}},
        now_utc=now,
    ).reason == 'SCOPE_AUTHORIZATION_DENIED'

    # Valid traceable RBAC + scope -> READY
    d_ok = decide_next(
        cfg, completed_results=[], existing_job_ids=[], hop_count=0,
        authorization_classes=['PREAUTHORIZED_CODE_MUTATION'],
        authorization_context=base_ctx,
        now_utc=now,
    )
    assert d_ok.action == 'READY' and d_ok.next_gate_id == 'A'
