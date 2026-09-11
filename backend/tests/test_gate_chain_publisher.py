import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.mirror_sync.gate_chain_publisher import build_plan, validate_template

def template(job='job-next'):
    return {'schema':'edarsahub.worker-job.v2','job_id':job,'target_repo':'rbalam/EDARSA_HUB','target_branch':'Edarsahub_Desarrollo','production_allowed':False,'objective':'test','actions':[],'checks':[{'type':'git_diff_check'}]}
def chain(t=None):
    return {'schema':'edarsahub.gate-chain.v1','chain_id':'T','enabled':True,'max_hops':5,'start_gate_id':'A','gates':[{'gate_id':'A','job_id':'done-a','mutation_class':'READ_ONLY','next_gate_ids':['B']},{'gate_id':'B','job_id':'job-next','mutation_class':'READ_ONLY','next_gate_ids':[],'job_template':t or template()}]}
def decision(state='READY'): return {'state':state,'next_gate_id':'B'}
def test_plan_ready(): assert build_plan(chain(),decision(),set())['status']=='READY_TO_PUBLISH'
def test_duplicate_is_exists():
    r=build_plan(chain(),decision(),{'job-next'}); assert r['status']=='EXISTS' and r['publish'] is False
def test_nonready_rejected():
    with pytest.raises(ValueError,match='DECISION_NOT_READY'): build_plan(chain(),decision('WAIT'),set())
def test_production_forbidden():
    t=template(); t['production_allowed']=True
    with pytest.raises(ValueError,match='PRODUCTION_FORBIDDEN'): build_plan(chain(t),decision(),set())
def test_invalid_schema():
    t=template(); t['schema']='x'
    with pytest.raises(ValueError,match='INVALID_JOB_TEMPLATE_SCHEMA'): validate_template(t)
def test_arbitrary_shell_forbidden():
    t=template(); t['command']='rm -rf /'
    with pytest.raises(ValueError,match='FORBIDDEN_TEMPLATE_KEY:command'): validate_template(t)
def test_arbitrary_sql_forbidden():
    t=template(); t['sql']='DELETE FROM x'
    with pytest.raises(ValueError,match='FORBIDDEN_TEMPLATE_KEY:sql'): validate_template(t)
def test_unsupported_action_rejected():
    t=template(); t['actions']=[{'type':'run_shell'}]
    with pytest.raises(ValueError,match='UNSUPPORTED_ACTION'): validate_template(t)
def test_unsupported_check_rejected():
    t=template(); t['checks']=[{'type':'execute_sql'}]
    with pytest.raises(ValueError,match='UNSUPPORTED_CHECK'): validate_template(t)
