from pathlib import Path

FILE = (
    Path(__file__).resolve().parents[2]
    / "tools"
    / "mirror_sync"
    / "universal_job_result_publisher.py"
)


def _text() -> str:
    return FILE.read_text(encoding="utf-8")


def test_result_publisher_has_runtime_git_helper():
    text = _text()
    assert "resolve_runtime_git_credential_helper" in text
    assert "runtime_git_command" in text


def test_result_publisher_has_persistent_fallback():
    text = _text()
    assert "/root/.git-credentials" in text
    assert "store --file=" in text


def test_result_clone_uses_runtime_helper():
    text = _text()
    assert 'runtime_git_command(' in text
    assert '"clone"' in text


def test_result_push_uses_runtime_helper():
    text = _text()
    assert '"push"' in text
    assert "runtime_git_command" in text


def test_result_publisher_disables_prompts():
    text = _text()
    assert "GIT_TERMINAL_PROMPT" in text
    assert '"0"' in text


def test_result_publisher_does_not_embed_tokens():
    text = _text()
    forbidden = (
        "github_pat_",
        "ghp_",
        "gho_",
        "ghu_",
        "ghs_",
    )
    assert not any(token in text for token in forbidden)
