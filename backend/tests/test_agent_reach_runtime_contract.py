from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INFRA = ROOT / 'infra' / 'agent-reach'
WORKFLOW = ROOT / '.github' / 'workflows' / 'agent-reach-runtime-audit.yml'
VENDORED = ROOT / 'third_party' / 'agent-reach'

def read(path: Path) -> str:
    return path.read_text(encoding='utf-8')

def test_canonical_files_exist():
    required = [INFRA / 'Dockerfile', INFRA / 'README.md', INFRA / 'build.sh', INFRA / 'healthcheck.sh', INFRA / 'requirements.lock', INFRA / 'versions.lock', INFRA / 'yt-dlp.conf', WORKFLOW, VENDORED / 'pyproject.toml']
    missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    assert not missing, missing

def test_versions_and_runtime_isolation():
    versions = read(INFRA / 'versions.lock')
    requirements = read(INFRA / 'requirements.lock')
    assert 'AGENT_REACH_VERSION=1.5.0' in versions
    assert 'DENO_VERSION=2.9.4' in versions
    assert 'YTDLP_VERSION=2026.07.04' in versions
    assert 'yt-dlp==2026.7.4' in requirements
    assert 'PIP_VERSION=26.1.2' in versions
    dockerfile = read(INFRA / 'Dockerfile')
    assert 'USER edarsa-agent-reach' in dockerfile
    assert 'VIRTUAL_ENV=/opt/edarsa/agent-reach/venv' in dockerfile
    assert '/root/.agent-reach' not in dockerfile
    assert 'ffmpeg' in dockerfile and 'ffprobe' in dockerfile

def test_healthcheck_contract():
    health = read(INFRA / 'healthcheck.sh')
    for cmd in ('agent-reach', 'python', 'yt-dlp', 'deno', 'ffmpeg', 'ffprobe', 'curl'):
        assert f'require_command {cmd}' in health
    assert 'AGENT_REACH_HEALTHCHECK=PASS' in health

def test_build_and_ci_are_non_publishing_non_deploying():
    build = read(INFRA / 'build.sh')
    workflow = read(WORKFLOW)
    for text in (build, workflow):
        assert 'docker push' not in text
        assert 'kubectl' not in text
        assert 'helm ' not in text
        assert 'IMAGE_PUSHED=0' in text
        assert 'DEPLOY_EXECUTED=0' in text
    assert 'contents: read' in workflow

def test_runtime_has_no_direct_backend_sql_or_mongo_contract():
    combined = read(INFRA / 'Dockerfile') + '\n' + read(INFRA / 'build.sh')
    assert 'backend/' not in combined
    assert 'sqlcmd' not in combined.lower()
    assert 'mongo' not in combined.lower()
