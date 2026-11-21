import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.mirror_sync.gate_chain_reconciler import reconcile_chain
def chain(enabled=True):
    return {'schema':'edarsahub.gate-chain.v1','chain_id':'TEST','enabled':enabled,'max_hops':5,'start_gate_id':'A','adopt_existing_job_ids':[],'gates':[{'gate_id':'A','job_id':'job-a','mutation_class':'READ_ONLY','next_gate_ids':['B']},{'gate_id':'B','job_id':'job-b','mutation_class':'READ_ONLY','next_gate_ids':[]}]}
def put(root,state,job_id,payload=None):
    f=root/state; f.mkdir(parents=True,exist_ok=True); (f/f'{job_id}.json').write_text(json.dumps(payload or {'job_id':job_id}),encoding='utf-8')
def certified(job_id): return {'job_id':job_id,'status':'READ_ONLY_COMPLETE','certification':'CERTIFIED_READ_ONLY','quality_gate':'PASS','tests':'PASS','blockers':[],'production_touched':False}
def test_disabled_chain_is_ignored(tmp_path): assert reconcile_chain(chain(False),tmp_path)['state']=='DISABLED'
def test_pending_registered_job_is_adopted_and_waits(tmp_path): put(tmp_path,'pending','job-a'); assert reconcile_chain(chain(),tmp_path)['state']=='WAIT'
def test_processing_registered_job_is_adopted_and_waits(tmp_path): put(tmp_path,'processing','job-a'); assert reconcile_chain(chain(),tmp_path)['state']=='WAIT'
def test_certified_terminal_advances(tmp_path): put(tmp_path,'results','job-a',certified('job-a')); r=reconcile_chain(chain(),tmp_path); assert r['state']=='READY' and r['next_gate_id']=='B'
def test_rejected_registered_job_waits(tmp_path): put(tmp_path,'rejected','job-a',{'job_id':'job-a','status':'REJECTED'}); assert reconcile_chain(chain(),tmp_path)['state']=='WAIT'
def test_noncertified_result_does_not_advance(tmp_path): put(tmp_path,'results','job-a',{'job_id':'job-a','status':'BLOCKED','certification':'NOT_CERTIFIED','quality_gate':'FAIL','tests':'FAIL','blockers':['x'],'production_touched':False}); assert reconcile_chain(chain(),tmp_path)['state']=='WAIT'
def test_unregistered_job_is_ignored(tmp_path): put(tmp_path,'processing','random-job'); r=reconcile_chain(chain(),tmp_path); assert r['state']=='READY' and r['adopted_jobs']==[]
def test_multiple_states_fail_closed(tmp_path): put(tmp_path,'pending','job-a'); put(tmp_path,'processing','job-a'); r=reconcile_chain(chain(),tmp_path); assert r['state']=='STOP' and r['reason']=='STATE_CONFLICT'
def test_result_plus_processing_conflict_fail_closed(tmp_path): put(tmp_path,'processing','job-a'); put(tmp_path,'results','job-a',certified('job-a')); r=reconcile_chain(chain(),tmp_path); assert r['state']=='STOP' and r['reason']=='STATE_CONFLICT'
