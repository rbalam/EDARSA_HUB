import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import tools.mirror_sync.gate_chain_orchestrator as orch

def template(job): return {'schema':'edarsahub.worker-job.v2','job_id':job,'target_repo':'rbalam/EDARSA_HUB','target_branch':'Edarsahub_Desarrollo','production_allowed':False,'objective':'x','actions':[],'checks':[{'type':'git_diff_check'}]}
def chain(enabled=True): return {'schema':'edarsahub.gate-chain.v1','chain_id':'T','enabled':enabled,'max_hops':5,'start_gate_id':'A','gates':[{'gate_id':'A','job_id':'job-a','mutation_class':'READ_ONLY','next_gate_ids':['B'],'job_template':template('job-a')},{'gate_id':'B','job_id':'job-b','mutation_class':'READ_ONLY','next_gate_ids':[],'job_template':template('job-b')}]}
def put(root,state,job_id,payload): f=root/state; f.mkdir(parents=True,exist_ok=True); (f/f'{job_id}.json').write_text(json.dumps(payload),encoding='utf-8')
def certified(job): return {'job_id':job,'status':'READ_ONLY_COMPLETE','certification':'CERTIFIED_READ_ONLY','quality_gate':'PASS','tests':'PASS','blockers':[],'production_touched':False}
def test_disabled_ignored(tmp_path): assert orch.cycle_chain(chain(False),tmp_path,tmp_path/'p')['action']=='DISABLED'
def test_dry_run_does_not_publish(tmp_path,monkeypatch):
    called=[]; monkeypatch.setattr(orch,'publish',lambda p: called.append(p)); r=orch.cycle_chain(chain(),tmp_path,tmp_path/'p',False); assert r['action']=='READY' and not r['published'] and called==[]
def test_ready_publishes_once_when_enabled(tmp_path,monkeypatch):
    calls=[]; monkeypatch.setattr(orch,'publish',lambda p:(calls.append(p) or {'status':'PUBLISHED','job_id':'job-a','commit_sha':'a'*40})); r=orch.cycle_chain(chain(),tmp_path,tmp_path/'p',True); assert r['published'] and len(calls)==1
def test_wait_does_not_publish(tmp_path,monkeypatch):
    put(tmp_path,'pending','job-a',{'job_id':'job-a'}); calls=[]; monkeypatch.setattr(orch,'publish',lambda p:calls.append(p)); r=orch.cycle_chain(chain(),tmp_path,tmp_path/'p',True); assert r['action']=='WAIT' and calls==[]
def test_complete_does_not_publish(tmp_path,monkeypatch):
    put(tmp_path,'results','job-a',certified('job-a')); put(tmp_path,'results','job-b',certified('job-b')); calls=[]; monkeypatch.setattr(orch,'publish',lambda p:calls.append(p)); r=orch.cycle_chain(chain(),tmp_path,tmp_path/'p',True); assert r['action']=='COMPLETE' and calls==[]
def test_restart_persists_state(tmp_path):
    p=tmp_path/'persist'; r1=orch.cycle_chain(chain(),tmp_path/'state',p,False); r2=orch.cycle_chain(chain(),tmp_path/'state',p,False); assert (p/'T.json').is_file(); assert r2['runtime_state']['chain_id']=='T'; assert r1['runtime_state']['production_touched'] is False
def test_duplicate_existing_prevents_publish(tmp_path,monkeypatch):
    put(tmp_path,'done','job-a',{'job_id':'job-a'}); calls=[]; monkeypatch.setattr(orch,'publish',lambda p:calls.append(p)); r=orch.cycle_chain(chain(),tmp_path,tmp_path/'p',True); assert r['action']=='WAIT' and calls==[]
def test_max_hops_fail_closed(tmp_path):
    c=chain(); c['max_hops']=1; put(tmp_path,'results','job-a',certified('job-a')); r=orch.cycle_chain(c,tmp_path,tmp_path/'p',False); assert r['action']=='STOP'
