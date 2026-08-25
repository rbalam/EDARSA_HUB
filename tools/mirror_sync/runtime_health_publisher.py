#!/usr/bin/env python3
"""Publica salud del worker en la rama worker/requests sin exponer secretos."""
from __future__ import annotations
import json, os, shutil, subprocess, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(os.environ.get("EDARSAHUB_ROOT","/app"))
STATE=ROOT/".git"/"universal-worker-queue"
REMOTE=os.environ.get("EDARSAHUB_QUEUE_REMOTE","origin")
BRANCH=os.environ.get("EDARSAHUB_QUEUE_BRANCH","worker/requests")
WT=Path("/tmp/edarsahub-worker-health-publish")
MIN_INTERVAL=int(os.environ.get("EDARSAHUB_HEARTBEAT_SECONDS","300"))
STALE_SECONDS=int(os.environ.get("EDARSAHUB_JOB_STALE_SECONDS","180"))
STAMP=STATE/"last_health_publish_epoch"

def now(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def run(args,cwd=ROOT): return subprocess.run(args,cwd=str(cwd),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=False,env={**os.environ,"GIT_TERMINAL_PROMPT":"0"})
def git(*args,cwd=ROOT,check=True):
 r=run(["git",*args],cwd)
 if check and r.returncode: raise RuntimeError(f"GIT_FAILED:{' '.join(args)}:{r.stdout[-800:]}")
 return r

def pending_jobs():
 inbox=STATE/"inbox"; processing=STATE/"processing"; results=STATE/"results"
 done={p.stem for p in results.glob("*.json")} if results.exists() else set()
 rows=[]
 for folder,state in ((inbox,"PENDING"),(processing,"RUNNING")):
  if not folder.exists(): continue
  for p in folder.glob("*.json"):
   if p.stem in done: continue
   age=max(0,int(time.time()-p.stat().st_mtime))
   rows.append({"job_id":p.stem,"state":"BLOCKED" if age>=STALE_SECONDS else state,"age_seconds":age,"reason":"El worker no termino esta orden dentro del tiempo esperado." if age>=STALE_SECONDS else None})
 return sorted(rows,key=lambda x:x["job_id"])

def payload():
 head=git("rev-parse","HEAD").stdout.strip()
 jobs=pending_jobs()
 return {"schema":"edarsahub.worker-health.v1","generated_at_utc":now(),"worker":"ONLINE","development_sha":head,"branch":git("branch","--show-current").stdout.strip(),"queue_pending":sum(j["state"]=="PENDING" for j in jobs),"queue_running":sum(j["state"]=="RUNNING" for j in jobs),"queue_blocked":sum(j["state"]=="BLOCKED" for j in jobs),"jobs":jobs,"summary_es":"El worker esta activo. Este archivo permite comprobar desde GitHub que sigue trabajando y detectar ordenes detenidas.","production_touched":False}

def main():
 STATE.mkdir(parents=True,exist_ok=True)
 last=int(STAMP.read_text().strip()) if STAMP.exists() and STAMP.read_text().strip().isdigit() else 0
 if int(time.time())-last<MIN_INTERVAL: print("WORKER_HEALTH_PUBLISH=SKIPPED_INTERVAL"); return 0
 git("fetch",REMOTE,BRANCH); base=git("rev-parse",f"{REMOTE}/{BRANCH}").stdout.strip()
 if WT.exists(): git("worktree","remove","--force",str(WT),check=False); shutil.rmtree(WT,ignore_errors=True)
 git("worktree","add","--detach",str(WT),base)
 try:
  dst=WT/"worker_queue"/"status"/"latest.json"; dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_text(json.dumps(payload(),ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  git("add","--",str(dst.relative_to(WT)),cwd=WT)
  if git("diff","--cached","--quiet",cwd=WT,check=False).returncode==0: STAMP.write_text(str(int(time.time()))); return 0
  git("-c","user.name=EDARSAHUB Worker","-c","user.email=worker@edarsahub.local","commit","-m","worker-health: publish runtime heartbeat",cwd=WT)
  commit=git("rev-parse","HEAD",cwd=WT).stdout.strip(); git("fetch",REMOTE,BRANCH)
  if git("rev-parse",f"{REMOTE}/{BRANCH}").stdout.strip()!=base: raise RuntimeError("QUEUE_BRANCH_MOVED")
  push=run(["git","push",REMOTE,f"{commit}:refs/heads/{BRANCH}"],WT)
  if push.returncode: raise RuntimeError(f"HEALTH_PUSH_FAILED:{push.stdout[-800:]}")
  STAMP.write_text(str(int(time.time()))); print(f"WORKER_HEALTH_PUBLISHED={commit}")
 finally:
  git("worktree","remove","--force",str(WT),check=False); shutil.rmtree(WT,ignore_errors=True)
 return 0
if __name__=="__main__": raise SystemExit(main())
