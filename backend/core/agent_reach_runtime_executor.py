from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess

from core.agent_runtime_activation import RuntimeActivationDecision

_REPOSITORY_RE = re.compile(r'^[A-Za-z0-9._/-]+$')
_TAG_RE = re.compile(r'^[A-Za-z0-9._-]+$')

@dataclass(frozen=True)
class AgentReachRuntimeResult:
    success: bool
    returncode: int
    stdout: str
    stderr: str
    argv: tuple[str, ...]

def load_agent_reach_image(versions_lock_path: str | Path) -> str:
    values: dict[str, str] = {}
    for raw_line in Path(versions_lock_path).read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip()
    repository = values.get('IMAGE_REPOSITORY', '')
    tag = values.get('IMAGE_TAG', '')
    if not repository or not tag:
        raise RuntimeError('AGENT_REACH_IMAGE_LOCK_INCOMPLETE')
    if not _REPOSITORY_RE.fullmatch(repository) or not _TAG_RE.fullmatch(tag):
        raise RuntimeError('AGENT_REACH_IMAGE_LOCK_INVALID')
    return f'{repository}:{tag}'

def execute_agent_reach_healthcheck(activation: RuntimeActivationDecision, versions_lock_path: str | Path, *, timeout_seconds: int = 30, docker_binary: str | None = None) -> AgentReachRuntimeResult:
    if not activation.allowed or not activation.ready_for_executor:
        raise RuntimeError('RUNTIME_NOT_READY_FOR_EXECUTOR')
    if not activation.execution_gate.allowed:
        raise RuntimeError('EXECUTION_GATE_DENIED')
    if timeout_seconds <= 0 or timeout_seconds > 120:
        raise RuntimeError('AGENT_REACH_EXECUTOR_TIMEOUT_INVALID')
    docker = docker_binary or shutil.which('docker')
    if not docker:
        raise RuntimeError('DOCKER_COMMAND_NOT_AVAILABLE')
    image = load_agent_reach_image(versions_lock_path)
    argv = (docker, 'run', '--rm', '--network', 'none', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--entrypoint', '/usr/local/bin/agent-reach-healthcheck', image)
    completed = subprocess.run(argv, shell=False, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    return AgentReachRuntimeResult(success=completed.returncode == 0, returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr, argv=argv)
