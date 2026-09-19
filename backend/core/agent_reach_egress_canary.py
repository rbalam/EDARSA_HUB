from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

from core.agent_reach_policy_adapter import AgentReachDecision
from core.agent_reach_runtime_executor import load_agent_reach_image
from core.agent_runtime_activation import RuntimeActivationDecision

_CANARY_URL = 'https://example.com/'

@dataclass(frozen=True)
class AgentReachEgressCanaryResult:
    success: bool
    returncode: int
    stdout: str
    stderr: str
    argv: tuple[str, ...]

def execute_agent_reach_egress_canary(activation: RuntimeActivationDecision, agent_reach: AgentReachDecision, versions_lock_path: str | Path, *, timeout_seconds: int = 15, docker_binary: str | None = None) -> AgentReachEgressCanaryResult:
    if not activation.allowed or not activation.ready_for_executor:
        raise RuntimeError('RUNTIME_NOT_READY_FOR_EXECUTOR')
    if not activation.execution_gate.allowed:
        raise RuntimeError('EXECUTION_GATE_DENIED')
    if not agent_reach.allowed or agent_reach.prepared is None:
        raise RuntimeError('AGENT_REACH_POLICY_DENIED')
    if agent_reach.prepared.max_external_calls != 1:
        raise RuntimeError('AGENT_REACH_CANARY_REQUIRES_SINGLE_EXTERNAL_CALL')
    if timeout_seconds <= 0 or timeout_seconds > 30:
        raise RuntimeError('AGENT_REACH_CANARY_TIMEOUT_INVALID')
    docker = docker_binary or shutil.which('docker')
    if not docker:
        raise RuntimeError('DOCKER_COMMAND_NOT_AVAILABLE')
    image = load_agent_reach_image(versions_lock_path)
    argv = (docker, 'run', '--rm', '--network', 'bridge', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--entrypoint', '/usr/bin/curl', image, '--fail', '--silent', '--show-error', '--location', '--max-redirs', '0', '--proto', '=https', '--tlsv1.2', '--max-time', '10', _CANARY_URL)
    completed = subprocess.run(argv, shell=False, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    return AgentReachEgressCanaryResult(success=completed.returncode == 0, returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr, argv=argv)
