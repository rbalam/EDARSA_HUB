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
