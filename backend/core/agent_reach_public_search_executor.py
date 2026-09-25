from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus
import shutil
import subprocess

from core.agent_reach_policy_adapter import AgentReachDecision
from core.agent_reach_runtime_executor import load_agent_reach_image
from core.agent_runtime_activation import RuntimeActivationDecision

_SEARCH_PREFIX = 'https://r.jina.ai/http://www.google.com/search?q='
_REQUIRED_PROCEDURE = 'agent-reach-external-research'
_REQUIRED_SCOPE = 'external:web'
_MAX_DOWNLOAD_BYTES = 65536

@dataclass(frozen=True)
class AgentReachPublicSearchResult:
    success: bool
    returncode: int
    stdout: str
    stderr: str
    argv: tuple[str, ...]
    query: str

def execute_agent_reach_public_search(activation: RuntimeActivationDecision, agent_reach: AgentReachDecision, versions_lock_path: str | Path, *, timeout_seconds: int = 20, docker_binary: str | None = None) -> AgentReachPublicSearchResult:
    if not activation.allowed or not activation.ready_for_executor:
        raise RuntimeError('RUNTIME_NOT_READY_FOR_EXECUTOR')
    if not activation.execution_gate.allowed:
        raise RuntimeError('EXECUTION_GATE_DENIED')
    if not agent_reach.allowed or agent_reach.prepared is None:
        raise RuntimeError('AGENT_REACH_POLICY_DENIED')
    prepared = agent_reach.prepared
    if prepared.procedure != _REQUIRED_PROCEDURE:
        raise RuntimeError('AGENT_REACH_PROCEDURE_INVALID')
    if _REQUIRED_SCOPE not in prepared.effective_scopes:
        raise RuntimeError('AGENT_REACH_SCOPE_INVALID')
    if prepared.max_external_calls != 1:
        raise RuntimeError('AGENT_REACH_SEARCH_REQUIRES_SINGLE_EXTERNAL_CALL')
    if timeout_seconds <= 0 or timeout_seconds > 30:
        raise RuntimeError('AGENT_REACH_SEARCH_TIMEOUT_INVALID')
    query = prepared.query.strip()
    if not query:
        raise RuntimeError('AGENT_REACH_QUERY_REQUIRED')
    docker = docker_binary or shutil.which('docker')
    if not docker:
        raise RuntimeError('DOCKER_COMMAND_NOT_AVAILABLE')
    image = load_agent_reach_image(versions_lock_path)
    target = _SEARCH_PREFIX + quote_plus(query, safe='')
    argv = (docker, 'run', '--rm', '--network', 'bridge', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--entrypoint', '/usr/bin/curl', image, '--fail', '--silent', '--show-error', '--location', '--max-redirs', '0', '--proto', '=https', '--tlsv1.2', '--max-time', '15', '--max-filesize', str(_MAX_DOWNLOAD_BYTES), target)
    completed = subprocess.run(argv, shell=False, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    return AgentReachPublicSearchResult(success=completed.returncode == 0, returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr, argv=argv, query=query)
