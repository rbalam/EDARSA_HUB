#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.mirror_sync.gate_chain_controller import decide_next, validate_chain
STATE_ORDER={'RESULT':5,'PROCESSING':4,'PENDING':3,'DONE':2,'REJECTED':1}
STATE_DIRS={'PENDING':'pending','PROCESSING':'processing','DONE':'done','REJECTED':'rejected','RESULT':'results'}
def load_json(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict): raise ValueError(f'JSON_NOT_OBJECT:{path}')
    return value
def discover_state(state_root:Path)->dict[str,list[dict[str,Any]]]:
    out={}
    for state_name,dirname in STATE_DIRS.items():
        folder=state_root/dirname
        if not folder.exists(): continue
        for path in sorted(folder.glob('*.json')):
            try: payload=load_json(path)
            except Exception: payload={}
            job_id=str(payload.get('job_id') or path.stem).strip()
            if job_id: out.setdefault(job_id,[]).append({'state':state_name,'path':str(path),'payload':payload})
    return out
def effective_entry(entries):
    return sorted(entries,key=lambda x:STATE_ORDER[x['state']],reverse=True)[0]
def reconcile_chain(chain:dict[str,Any],state_root:Path)->dict[str,Any]:
    validate_chain(chain)
    chain_id=str(chain['chain_id']).strip()
    if chain.get('enabled') is not True: return {'chain_id':chain_id,'state':'DISABLED','adopted_jobs':[],'conflicts':[]}
    discovered=discover_state(state_root)
    declared={str(g.get('job_id') or '').strip() for g in chain.get('gates',[])}; declared.discard('')
    explicit={str(x).strip() for x in chain.get('adopt_existing_job_ids',[]) if str(x).strip()}
    allowed=declared|explicit
    adopted=[]; conflicts=[]; completed_results=[]; existing=set()
    for job_id in sorted(allowed):
        entries=discovered.get(job_id,[])
        if not entries: continue
        states=sorted({e['state'] for e in entries})
        if len(states)>1: conflicts.append({'job_id':job_id,'states':states})
        chosen=effective_entry(entries)
        adopted.append({'job_id':job_id,'state':chosen['state'],'all_states':states}); existing.add(job_id)
        if chosen['state']=='RESULT':
            payload=chosen['payload']
            if 'job_id' not in payload: payload={**payload,'job_id':job_id}
            completed_results.append(payload)
    if conflicts: return {'chain_id':chain_id,'state':'STOP','reason':'STATE_CONFLICT','adopted_jobs':adopted,'conflicts':conflicts}
    hop_count=sum(1 for r in completed_results if str(r.get('certification') or '').upper().startswith('CERTIFIED'))
    decision=decide_next(chain,completed_results=completed_results,existing_job_ids=existing,hop_count=hop_count,authorization_classes=chain.get('authorization_classes',[]))
    return {'chain_id':chain_id,'state':decision.action,'current_gate_id':decision.current_gate_id,'next_gate_id':decision.next_gate_id,'reason':decision.reason,'hop_count':hop_count,'adopted_jobs':adopted,'conflicts':conflicts}
def reconcile_all(config_dir:Path,state_root:Path)->dict[str,Any]:
    rows=[]
    if config_dir.exists():
        for path in sorted(config_dir.glob('*.json')): rows.append(reconcile_chain(load_json(path),state_root))
    return {'schema':'edarsahub.gate-chain-reconcile.v1','mode':'READ_ONLY','chains':rows,'queue_mutated':False,'production_touched':False}
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--config-dir',default=str(ROOT/'worker_queue'/'config'/'gate_chains')); p.add_argument('--state-root',default=str(ROOT/'.git'/'universal-worker-queue')); a=p.parse_args(); print(json.dumps(reconcile_all(Path(a.config_dir),Path(a.state_root)),ensure_ascii=False,indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
