from pathlib import Path
import importlib.util
import inspect


ROOT = Path(__file__).resolve().parents[2]

GUARD_PATH = (
    ROOT
    / "scripts"
    / "agent_guardrails"
    / "validate_repository_artifacts.py"
)


def _load():
    spec = importlib.util.spec_from_file_location(
        "repository_artifact_guard_reseed_contract",
        GUARD_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _text():
    return GUARD_PATH.read_text(encoding="utf-8")


def test_reseed_guard_exists():
    text = _text()

    assert "EDARSA_MIRROR_RESEED_GUARD_V3" in text
    assert "_edarsa_is_certified_mirror_reseed" in text


def test_validate_accepts_explicit_pre_push_context():
    guard = _load()

    signature = inspect.signature(guard.validate)

    assert "pre_push_path" in signature.parameters
    assert signature.parameters["pre_push_path"].default is None


def test_validate_range_accepts_explicit_pre_push_context():
    guard = _load()

    signature = inspect.signature(guard.validate_range)

    assert "pre_push_path" in signature.parameters
    assert signature.parameters["pre_push_path"].default is None


def test_pre_push_path_is_forwarded_without_cli_global():
    text = _text()

    assert (
        "validate_range(base, local_sha, pre_push_path=path)"
        in text
    )

    validate_block = text[
        text.index("def validate("):
        text.index("def validate_staged(")
    ]

    assert "args.pre_push_input" not in validate_block
    assert "_edarsa_is_certified_mirror_reseed(pre_push_path)" in validate_block


def test_reseed_is_mirror_only():
    text = _text()

    assert "refs/heads/mirror/emergent-live" in text
    assert "origin/Edarsahub_Desarrollo" in text


def test_reseed_preserves_old_mirror_history():
    text = _text()

    assert "len(parents) != 2" in text
    assert "parents[1] != remote_sha" in text
    assert "--is-ancestor" in text


def test_reseed_tree_must_equal_development():
    text = _text()

    assert "candidate_tree" in text
    assert "development_tree" in text
    assert "candidate_tree != development_tree" in text


def test_normal_artifact_limit_remains_fail_closed():
    text = _text()

    assert "NEW_FILE_LIMIT = 50" in text
    assert "added_count > NEW_FILE_LIMIT" in text
    assert "demasiados archivos nuevos" in text


def test_no_generic_bypass():
    text = _text().lower()

    forbidden = (
        "--no-verify",
        "disable_guard",
        "skip_guard",
        "allow_all",
    )

    assert not any(
        token in text
        for token in forbidden
    )
