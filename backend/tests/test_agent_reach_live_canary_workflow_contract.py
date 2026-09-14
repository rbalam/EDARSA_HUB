from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[2] / '.github' / 'workflows' / 'agent-reach-live-canary.yml'

def test_live_canary_workflow_is_manual_sha_bound_and_non_production():
    text = WORKFLOW.read_text(encoding='utf-8')
    required = [
        'workflow_dispatch:', 'expected_sha:', 'runs-on: ubuntu-latest',
        'persist-credentials: false', 'infra/agent-reach/build.sh',
        'test_agent_reach_live_network_canary.py', 'actions/upload-artifact@v4',
        'contents: read', 'if: always()',
    ]
    for token in required:
        assert token in text
    forbidden = ['secrets.', '/var/run/docker.sock', 'docker.sock', 'docker push', 'kubectl ', 'ssh ', 'scp ']
    for token in forbidden:
        assert token not in text
    assert '\n  push:' not in text
    assert '\n  pull_request:' not in text
