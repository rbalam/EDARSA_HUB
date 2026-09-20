import importlib.util, os, subprocess
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]; GUARD=ROOT/'tools/mirror_sync/git_divergence_guard.py'; DISPATCHER=ROOT/'tools/mirror_sync/universal_job_dispatcher.py'; APPLY=ROOT/'tools/mirror_sync/apply_remote_update.sh'; FINALIZER=ROOT/'tools/mirror_sync/finalize_local_snapshot.sh'; SUPERVISOR=ROOT/'tools/mirror_sync/supervisor/edarsahub-mirror-sync.conf'; BACKUP=ROOT/'backup_a_github.sh'
def load_guard():
 s=importlib.util.spec_from_file_location('g',GUARD); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def g(repo,*args,check=True,env=None):
 r=subprocess.run(['git',*args],cwd=repo,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env,check=False)
 if check and r.returncode!=0: raise AssertionError(r.stdout)
 return r
def setup_pair(t):
 remote=t/'remote.git'; local=t/'local'; peer=t/'peer'; g(t,'init','--bare',str(remote)); local.mkdir(); g(local,'init'); g(local,'config','user.email','t@example.com'); g(local,'config','user.name','T'); (local/'seed.txt').write_text('seed\n'); g(local,'add','seed.txt'); g(local,'commit','-m','seed'); g(local,'branch','-M','Edarsahub_Desarrollo'); g(local,'remote','add','origin',str(remote)); g(local,'push','-u','origin','Edarsahub_Desarrollo'); g(t,'clone','-b','Edarsahub_Desarrollo',str(remote),str(peer)); g(peer,'config','user.email','p@example.com'); g(peer,'config','user.name','P'); return remote,local,peer
def commit(repo,name,content): (repo/name).write_text(content); g(repo,'add',name); g(repo,'commit','-m',name)
def test_case_1_sync_pass(tmp_path):
 m=load_guard();_,l,_=setup_pair(tmp_path);s=m.inspect_repository(l,fetch=True);assert s['classification']=='SYNC' and m.mutation_policy(s)['allowed']
def test_case_2_local_ahead_controlled_policy(tmp_path):
 m=load_guard();_,l,_=setup_pair(tmp_path);commit(l,'a','a');commit(l,'b','b');s=m.inspect_repository(l,fetch=True);assert (s['ahead_count'],s['behind_count'])==(2,0);assert not m.mutation_policy(s)['allowed'];assert m.mutation_policy(s,allow_local_ahead=True)['allowed']
def test_case_3_remote_ahead_blocks_write(tmp_path):
 m=load_guard();_,l,p=setup_pair(tmp_path);commit(p,'r1','1');commit(p,'r2','2');g(p,'push','origin','Edarsahub_Desarrollo');s=m.inspect_repository(l,fetch=True);q=m.mutation_policy(s);assert (s['ahead_count'],s['behind_count'])==(0,2) and q['reason']=='NEEDS_FAST_FORWARD_REFRESH'
def test_case_4_diverged_3_6_blocked(tmp_path):
 m=load_guard();_,l,p=setup_pair(tmp_path);[commit(l,f'l{i}',str(i)) for i in range(3)];[commit(p,f'r{i}',str(i)) for i in range(6)];g(p,'push','origin','Edarsahub_Desarrollo');s=m.inspect_repository(l,fetch=True);assert (s['ahead_count'],s['behind_count'])==(3,6) and m.mutation_policy(s)['terminal_status']=='GIT_DIVERGENCE_BLOCKED'
def test_case_5_staged_blocks(tmp_path):
 m=load_guard();_,l,_=setup_pair(tmp_path);(l/'seed.txt').write_text('x');g(l,'add','seed.txt');s=m.inspect_repository(l,fetch=True);assert s['staged_count']==1 and m.mutation_policy(s)['terminal_status']=='GIT_WORKTREE_NOT_CLEAN'
def test_case_6_untracked_blocks(tmp_path):
 m=load_guard();_,l,_=setup_pair(tmp_path);(l/'x').write_text('x');s=m.inspect_repository(l,fetch=True);assert s['untracked_count']==1 and m.mutation_policy(s)['terminal_status']=='GIT_WORKTREE_NOT_CLEAN'
def test_case_7_remote_moves_cancels_push(tmp_path):
 m=load_guard();_,l,p=setup_pair(tmp_path);start=m.inspect_repository(l,fetch=True)['remote_head'];commit(p,'moved','x');g(p,'push','origin','Edarsahub_Desarrollo')
 with pytest.raises(m.GitGuardError,match='REMOTE_MOVED_RETRY_REQUIRED'): m.compare_and_swap(l,start)
def install_push_guard(repo):
 h=repo/'.git/hooks/pre-push';h.write_text('#!/bin/sh\n[ "${EDARSA_ALLOW_PUSH:-}" = 1 ] || { echo PUSH_DENIED; exit 9; }\n');h.chmod(0o755)
def test_case_8_push_without_guard_fails_no_pass(tmp_path):
 _,l,_=setup_pair(tmp_path);install_push_guard(l);commit(l,'guard','x');r=g(l,'push','origin','HEAD:Edarsahub_Desarrollo',check=False,env={k:v for k,v in os.environ.items() if k!='EDARSA_ALLOW_PUSH'});assert r.returncode!=0 and 'PASS' not in r.stdout
def test_case_9_authorized_fast_forward_topology_zero(tmp_path):
 m=load_guard();_,l,_=setup_pair(tmp_path);install_push_guard(l);commit(l,'ok','x');r=m.authorized_push(l,args=['push','origin','HEAD:refs/heads/Edarsahub_Desarrollo'],job_id='case9',owner='test');assert r.returncode==0;e=m.post_push_verify(l,g(l,'rev-parse','HEAD').stdout.strip());assert e['topology']=='0/0' and e['terminal_status']=='CERTIFIED_GIT_SYNC'
def test_case_10_two_writers_only_one_lock(tmp_path):
 m=load_guard();_,l,_=setup_pair(tmp_path);a=m.acquire_writer_lock(l,job_id='a',owner='one',owner_pid=os.getpid())
 with pytest.raises(m.GitGuardError,match='GIT_LOCK_BUSY'): m.acquire_writer_lock(l,job_id='b',owner='two',owner_pid=os.getpid())
 m.release_writer_lock(l,a)
def test_case_11_readonly_does_not_require_writer_lock(tmp_path):
 m=load_guard();_,l,_=setup_pair(tmp_path);a=m.acquire_writer_lock(l,job_id='w',owner='one',owner_pid=os.getpid());assert m.requires_writer_lock('READ_ONLY') is False and m.requires_writer_lock('MUTATION') is True;m.release_writer_lock(l,a)
def test_case_12_out_of_scope_file_fails(tmp_path):
 m=load_guard();_,l,_=setup_pair(tmp_path);base=g(l,'rev-parse','HEAD').stdout.strip();commit(l,'allowed','a');commit(l,'extra','b');head=g(l,'rev-parse','HEAD').stdout.strip()
 with pytest.raises(m.GitGuardError,match='GIT_SCOPE_VIOLATION'): m.validate_commit_scope(l,base,head,{'allowed'})
def test_case_13_authorized_local_ahead_recovery_preserves_and_converges(tmp_path):
 m=load_guard();_,l,_=setup_pair(tmp_path);install_push_guard(l);g(l,'config','user.email','worker-publisher@edarsahub.local');g(l,'config','user.name','EDARSAHUB Worker Publisher');commit(l,'owned','x');state=m.inspect_repository(l,fetch=True);token=m.acquire_writer_lock(l,job_id='case13',owner='universal-worker',owner_pid=os.getpid())
 try:
  evidence=m.recover_authorized_local_ahead(l,state,job_id='case13',owner='universal-worker')
  assert evidence['post_push']['topology']=='0/0';head=g(l,'rev-parse','HEAD').stdout.strip();assert g(l,'rev-parse','origin/Edarsahub_Desarrollo').stdout.strip()==head;assert g(l,'ls-remote','origin',f"refs/heads/{evidence['recovery_branch']}").stdout.split()[0]==head
 finally:m.release_writer_lock(l,token)
def test_case_14_unknown_local_ahead_owner_is_rejected(tmp_path):
 m=load_guard();_,l,_=setup_pair(tmp_path);commit(l,'unknown','x');state=m.inspect_repository(l,fetch=True);token=m.acquire_writer_lock(l,job_id='case14',owner='universal-worker',owner_pid=os.getpid())
 try:
  with pytest.raises(m.GitGuardError,match='LOCAL_AHEAD_OWNERSHIP_UNPROVEN'):m.recover_authorized_local_ahead(l,state,job_id='case14',owner='universal-worker')
 finally:m.release_writer_lock(l,token)
def executable_lines(path): return '\n'.join(x.strip() for x in path.read_text().splitlines() if x.strip() and not x.lstrip().startswith('#'))
def test_runtime_contract_has_no_destructive_commands_or_persistent_push_guard():
 c=executable_lines(APPLY);assert 'git merge --ff-only' not in c and 'git pull' not in c and 'reset --hard' not in c and 'git clean' not in c;assert 'EDARSA_ALLOW_PUSH="1"' not in SUPERVISOR.read_text();assert 'export EDARSA_ALLOW_PUSH=1' not in BACKUP.read_text();assert 'export EDARSA_ALLOW_PUSH=1' not in FINALIZER.read_text();assert 'edarsahub_acquire_git_writer_lock' in FINALIZER.read_text() and 'edarsahub_release_git_writer_lock' in FINALIZER.read_text()
def test_dispatcher_uses_cas_and_no_replay_on_remote_move():
 text=DISPATCHER.read_text();block=text.split('def integrate(',1)[1].split('def release_agent_guard_claim',1)[0];assert 'compare_and_swap' in block and 'CONCURRENT_REPLAY_REQUIRED' not in block and 'EDARSA_ALLOW_PUSH' in block and 'force-with-lease' not in text
