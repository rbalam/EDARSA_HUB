import json, shutil
from pathlib import Path
from core.agent_external_research_service import execute_external_research
from tests.test_agent_external_research_service import context, request
OUT=Path('tests/agent_reach_live_network_diagnostic_evidence.json')
def test_diag():
 d=shutil.which('docker')
 ev={'diagnostic_only':True,'canary_certified':False,'production_touched':False,'docker_available':bool(d)}
 if not d:
  ev['exact_error']='DOCKER_COMMAND_NOT_AVAILABLE'
 else:
  r=execute_external_research({'allowed':True},'OpenAI official website',request(),context(),Path('../infra/agent-reach/versions.lock'),timeout_seconds=30,docker_binary=d)
  ev.update({'allowed':r.evidence.allowed,'success':r.evidence.success,'reason':r.evidence.reason,'returncode':r.evidence.returncode,'stdout_bytes':r.evidence.stdout_bytes,'stderr_bytes':r.evidence.stderr_bytes})
 OUT.write_text(json.dumps(ev,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 assert True
