#!/usr/bin/env python3
"""Persistent deterministic orchestrator for registered EDARSAHUB gate chains.

Gate 4: one declared transition per chain per cycle. Dry-run by default.
"""
from __future__ import annotations
import argparse, json, os, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.mirror_sync.gate_chain_controller import (
    AUTONOMOUS_POLICY_SCHEMA,
    PolicyLimits,
    evaluate_autonomous_policy,
)
from tools.mirror_sync.gate_chain_reconciler import reconcile_chain, discover_state, load_json
from tools.mirror_sync.gate_chain_publisher import build_plan, publish

def now(): return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def atomic_json(path:Path,payload:dict[str,Any]):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as h:
        json.dump(payload,h,ensure_ascii=False,indent=2,sort_keys=True); h.write('\n'); temp=h.name
    os.replace(temp,path)
def read_state(path:Path)->dict[str,Any]:
    if not path.is_file(): return {}
    try: return load_json(path)
    except Exception: return {}
def existing_ids(state_root:Path)->set[str]: return set(discover_state(state_root).keys())
def cycle_chain(chain:dict[str,Any],state_root:Path,persist_root:Path,publish_enabled:bool=False)->dict[str,Any]:
    chain_id=str(chain.get('chain_id') or '').strip()
    if chain.get('enabled') is not True: return {'chain_id':chain_id,'action':'DISABLED'}
    state_path=persist_root/f'{chain_id}.json'
    prior=read_state(state_path)
    retry_counts=dict(prior.get('retry_counts') or {})
    consecutive_failures=int(prior.get('consecutive_failures') or 0)
    if chain.get('cancel_requested') is True:
        persisted={
            'schema':'edarsahub.gate-chain-runtime.v1','policy_schema':AUTONOMOUS_POLICY_SCHEMA,'chain_id':chain_id,'last_cycle_utc':now(),
            'hop_count':int(prior.get('hop_count') or 0),
            'last_gate_id':prior.get('last_gate_id'),
            'next_gate_id':prior.get('next_gate_id'),
            'last_job_id':prior.get('last_job_id'),
            'last_action':'CANCELLED_SAFELY',
            'cancelled_safely':True,
            'retry_counts':retry_counts,
            'consecutive_failures':consecutive_failures,
            'production_touched':False
        }
        atomic_json(state_path,persisted)
        return {'chain_id':chain_id,'action':'CANCELLED_SAFELY','reason':'SAFE_CANCELLATION_REQUESTED','published':False,'runtime_state':persisted}
    row=reconcile_chain(chain,state_root)
    action=row.get('state')
    result={'chain_id':chain_id,'action':action,'reason':row.get('reason'),'current_gate_id':row.get('current_gate_id'),'next_gate_id':row.get('next_gate_id'),'published':False}
    policy_record=None
    if action=='READY':
        next_gate_id=str(row.get('next_gate_id') or '').strip()
        target_gate=next((g for g in chain.get('gates',[]) if str(g.get('gate_id') or '').strip()==next_gate_id),None)
        raw_limits=chain.get('policy_limits') if isinstance(chain.get('policy_limits'),dict) else {}
        limits=PolicyLimits(
            max_hops=int(raw_limits.get('max_hops',chain.get('max_hops',10))),
            max_retries_per_gate=int(raw_limits.get('max_retries_per_gate',2)),
            max_parallelism=int(raw_limits.get('max_parallelism',1)),
            max_runtime_seconds=int(raw_limits.get('max_runtime_seconds',600)),
            max_actions_per_job=int(raw_limits.get('max_actions_per_job',15)),
            max_files_per_job=int(raw_limits.get('max_files_per_job',15)),
            circuit_breaker_threshold=int(raw_limits.get('circuit_breaker_threshold',3)),
        )
        if target_gate is not None:
            policy_record=evaluate_autonomous_policy(
                target_gate,
                limits=limits,
                hop_count=int(row.get('hop_count') or 0),
                retry_count=int(retry_counts.get(next_gate_id,0)),
                consecutive_failures=consecutive_failures,
                authorization_classes=chain.get('authorization_classes',[]),
                authorization_context=chain.get('authorization_context'),
            )
            result['policy_decision']=policy_record
            if not policy_record['allowed']:
                result['action']=policy_record['action']
                result['reason']=policy_record['reason']
        if result['action']=='READY':
            plan=build_plan(chain,row,existing_ids(state_root))
            result['plan_status']=plan.get('status')
            if plan.get('status')=='READY_TO_PUBLISH' and publish_enabled:
                pub=publish(plan)
                result['publish_result']=pub
                result['published']=pub.get('status')=='PUBLISHED'
                result['job_id']=pub.get('job_id')
            elif plan.get('status')=='EXISTS':
                result['action']='WAIT'; result['reason']='NEXT_JOB_ALREADY_EXISTS'; result['job_id']=plan.get('job_id')
    persisted={
        'schema':'edarsahub.gate-chain-runtime.v1','policy_schema':AUTONOMOUS_POLICY_SCHEMA,'chain_id':chain_id,'last_cycle_utc':now(),
        'hop_count':int(row.get('hop_count') or prior.get('hop_count') or 0),
        'last_gate_id':row.get('current_gate_id') or prior.get('last_gate_id'),
        'next_gate_id':row.get('next_gate_id'),
        'last_job_id':result.get('job_id') or prior.get('last_job_id'),
        'last_action':result.get('action'),
        'cancelled_safely':False,
        'retry_counts':retry_counts,
        'consecutive_failures':consecutive_failures,
        'last_decision_record':policy_record or prior.get('last_decision_record'),
        'production_touched':False
    }
    atomic_json(state_path,persisted)
    result['runtime_state']=persisted
    return result
def run_cycle(config_dir:Path,state_root:Path,persist_root:Path,publish_enabled:bool=False)->dict[str,Any]:
    rows=[]
    if config_dir.exists():
        for path in sorted(config_dir.glob('*.json')):
            chain=load_json(path)
            if chain.get('enabled') is True:
                rows.append(cycle_chain(chain,state_root,persist_root,publish_enabled))
    return {'schema':'edarsahub.gate-orchestrator-cycle.v1','generated_at_utc':now(),'publish_enabled':publish_enabled,'chains':rows,'production_touched':False}
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--config-dir',default=str(ROOT/'worker_queue'/'config'/'gate_chains')); p.add_argument('--state-root',default=str(ROOT/'.git'/'universal-worker-queue')); p.add_argument('--persist-root',default=str(ROOT/'.git'/'universal-worker-queue'/'orchestrator')); p.add_argument('--publish',action='store_true'); p.add_argument('--once',action='store_true'); p.add_argument('--interval',type=int,default=30); a=p.parse_args()
    if a.interval<10: raise SystemExit('INTERVAL_TOO_LOW')
    while True:
        print(json.dumps(run_cycle(Path(a.config_dir),Path(a.state_root),Path(a.persist_root),a.publish),ensure_ascii=False,indent=2,sort_keys=True),flush=True)
        if a.once: return 0
        time.sleep(a.interval)
if __name__=='__main__': raise SystemExit(main())
