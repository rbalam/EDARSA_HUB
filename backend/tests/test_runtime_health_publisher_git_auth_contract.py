from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HEALTH = ROOT / "tools" / "mirror_sync" / "runtime_health_publisher.py"


def _text() -> str:
    return HEALTH.read_text()


def test_health_publisher_disables_interactive_git_prompts():
    text = _text()
    assert "GIT_TERMINAL_PROMPT" in text
    assert '"0"' in text


def test_health_publisher_has_runtime_git_credential_resolution():
    text = _text()
    assert "resolve_runtime_git_credential_helper" in text
    assert "runtime_git_command" in text


def test_health_clone_actually_uses_runtime_git_command():
    text = _text()
    assert 'runtime_git_command("clone"' in text


def test_health_runtime_helper_does_not_reference_unknown_app_root():
    text = _text()
    assert "cwd=str(APP_ROOT)" not in text


def test_health_publisher_has_non_ephemeral_credential_fallback():
    text = _text()
    assert "/root/.git-credentials" in text
    assert "store --file=" in text


def test_health_publisher_does_not_embed_github_token():
    text = _text()
    forbidden = (
        "ghp_",
        "github_pat_",
        "gho_",
        "ghu_",
        "ghs_",
    )
    assert not any(token in text for token in forbidden)
