#!/usr/bin/env python3
"""Idempotent publisher for declared EDARSAHUB gate-chain jobs.

Gate 3: publication is opt-in with --publish. Default behavior is plan-only.
No arbitrary shell or SQL payload is accepted.
"""
from __future__ import annotations
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.mirror_sync.gate_chain_controller import validate_chain
JOB_ID_RE=re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$')
ALLOWED_ACTIONS={'replace_text','write_file','delete_file'}
ALLOWED_CHECKS={'git_diff_check','py_compile','pytest','frontend_build','sql_readonly_audit','repository_contract_audit'}
FORBIDDEN_KEYS={'sql','command','commands','shell','script_body','password','passwd','secret','token','credential'}

def _walk(value:Any):
    if isinstance(value,dict):
        for k,v in value.items():
            yield str(k).lower(),v
            yield from _walk(v)
    elif isinstance(value,list):
        for item in value: yield from _walk(item)

def validate_template(template:dict[str,Any])->dict[str,Any]:
    if not isinstance(template,dict) or template.get('schema')!='edarsahub.worker-job.v2': raise ValueError('INVALID_JOB_TEMPLATE_SCHEMA')
    job_id=str(template.get('job_id') or '').strip()
    if not JOB_ID_RE.fullmatch(job_id): raise ValueError('INVALID_JOB_ID')
    if template.get('production_allowed') is not False: raise ValueError('PRODUCTION_FORBIDDEN')
    for key,_ in _walk(template):
        if key in FORBIDDEN_KEYS: raise ValueError(f'FORBIDDEN_TEMPLATE_KEY:{key}')
    for action in template.get('actions') or []:
        if not isinstance(action,dict) or str(action.get('type')) not in ALLOWED_ACTIONS: raise ValueError('UNSUPPORTED_ACTION')
    for check in template.get('checks') or []:
        if not isinstance(check,dict) or str(check.get('type')) not in ALLOWED_CHECKS: raise ValueError('UNSUPPORTED_CHECK')
    return template

def gate_for(chain:dict[str,Any],gate_id:str)->dict[str,Any]:
    validate_chain(chain)
    for gate in chain.get('gates') or []:
        if str(gate.get('gate_id') or '').strip()==gate_id: return gate
    raise ValueError('NEXT_GATE_NOT_DECLARED')

def build_plan(chain:dict[str,Any],decision:dict[str,Any],existing_job_ids:set[str])->dict[str,Any]:
    if str(decision.get('state') or decision.get('action') or '').upper()!='READY': raise ValueError('DECISION_NOT_READY')
    gate_id=str(decision.get('next_gate_id') or '').strip()
    gate=gate_for(chain,gate_id)
    template=validate_template(gate.get('job_template'))
    job_id=str(template['job_id'])
    if job_id in existing_job_ids: return {'status':'EXISTS','job_id':job_id,'gate_id':gate_id,'publish':False}
    return {'status':'READY_TO_PUBLISH','job_id':job_id,'gate_id':gate_id,'publish':True,'template':template}

def run(args:list[str],cwd:Path|None=None):
    return subprocess.run(args,cwd=str(cwd or ROOT),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=False,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'})

def git(*args:str,cwd:Path|None=None,check:bool=True):
    r=run(['git',*args],cwd)
    if check and r.returncode: raise RuntimeError(f"GIT_FAILED:{' '.join(args)}:{r.stdout[-1200:]}")
    return r

def publish(plan:dict[str,Any],remote:str='origin',queue_branch:str='worker/requests')->dict[str,Any]:
    if plan.get('status')=='EXISTS': return {**plan,'result':'REMOTE_JOB=EXISTS'}
    if plan.get('status')!='READY_TO_PUBLISH': raise ValueError('PLAN_NOT_PUBLISHABLE')
    job_id=plan['job_id']; template=plan['template']; rel=f'worker_queue/inbox/{job_id}.json'
    git('fetch',remote,queue_branch)
    tmp=Path(tempfile.mkdtemp(prefix='edarsa-gate-publish-'))
    try:
        git('worktree','add','--detach',str(tmp),f'{remote}/{queue_branch}')
        target=tmp/rel
        if target.exists(): return {'status':'EXISTS','job_id':job_id,'result':'REMOTE_JOB=EXISTS'}
        target.parent.mkdir(parents=True,exist_ok=True); target.write_text(json.dumps(template,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        git('add','--',rel,cwd=tmp); git('commit','-m',f'orchestrator: enqueue {job_id}',cwd=tmp)
        sha=git('rev-parse','HEAD',cwd=tmp).stdout.strip()
        if not re.fullmatch(r'[0-9a-f]{40}',sha): raise RuntimeError('INVALID_COMMIT_SHA')
        pushed=git('push',remote,f'HEAD:{queue_branch}',cwd=tmp,check=False)
        if pushed.returncode!=0: raise RuntimeError(f'PUSH_FAILED:{pushed.stdout[-1200:]}')
        return {'status':'PUBLISHED','job_id':job_id,'commit_sha':sha,'result':'GATE_ENQUEUED=PASS'}
    finally:
        git('worktree','remove','--force',str(tmp),check=False); shutil.rmtree(tmp,ignore_errors=True)
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--chain-json',required=True); p.add_argument('--decision-json',required=True); p.add_argument('--existing-job-ids-json',default='[]'); p.add_argument('--publish',action='store_true'); a=p.parse_args()
    chain=json.loads(Path(a.chain_json).read_text(encoding='utf-8')); decision=json.loads(Path(a.decision_json).read_text(encoding='utf-8')); existing=set(json.loads(a.existing_job_ids_json)); plan=build_plan(chain,decision,existing)
    result=publish(plan) if a.publish else plan; print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
