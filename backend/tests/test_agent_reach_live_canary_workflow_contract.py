from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[2] / '.github' / 'workflows' / 'agent-reach-live-canary.yml'

def test_live_canary_workflow_is_sha_bound_and_worker_autotrigger_is_one_path_only():
    text = WORKFLOW.read_text(encoding='utf-8')
    required = [
        'workflow_dispatch:', 'expected_sha:', 'push:',
        'branches:', '- Edarsahub_Desarrollo',
        '- backend/tests/live_canary_requests/gate5g_worker_autotrigger_20260914.json',
        "EXPECTED_SHA: ${{ github.event_name == 'workflow_dispatch' && inputs.expected_sha || github.sha }}",
        'runs-on: ubuntu-latest', 'persist-credentials: false',
        'infra/agent-reach/build.sh', 'test_agent_reach_live_network_canary.py',
        'actions/upload-artifact@v4', 'contents: read', 'if: always()',
    ]
    for token in required:
        assert token in text
    forbidden = ['secrets.', '/var/run/docker.sock', 'docker.sock', 'docker push', 'kubectl ', 'ssh ', 'scp ', 'schedule:', 'repository_dispatch:']
    for token in forbidden:
        assert token not in text
    assert text.count('backend/tests/live_canary_requests/gate5g_worker_autotrigger_20260914.json') == 1
