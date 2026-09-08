from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "tools" / "mirror_sync" / "worker_concurrency.py"

spec = spec_from_file_location("worker_concurrency", POLICY_PATH)
module = module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

evaluate_scope_advance = module.evaluate_scope_advance


def test_exact_base_passes_without_rebase():
    result = evaluate_scope_advance("abc", "abc", ["a.py"], [])
    assert result["decision"] == "EXACT_BASE"
    assert result["scope_conflicts"] == []


def test_unrelated_head_advance_is_safe_replay():
    result = evaluate_scope_advance(
        "abc",
        "def",
        ["finanzas.py"],
        ["docs/cavas.md", "backend/core/bos.py"],
    )
    assert result["decision"] == "SAFE_REPLAY"
    assert result["scope_conflicts"] == []


def test_same_file_head_advance_blocks():
    result = evaluate_scope_advance(
        "abc",
        "def",
        ["frontend/src/pages/Finanzas.js"],
        ["frontend/src/pages/Finanzas.js", "docs/other.md"],
    )
    assert result["decision"] == "SCOPE_CONFLICT"
    assert result["scope_conflicts"] == ["frontend/src/pages/Finanzas.js"]


def test_read_only_empty_scope_can_advance_when_explicitly_allowed():
    result = evaluate_scope_advance(
        "abc",
        "def",
        [],
        ["backend/core/unrelated.py"],
        allow_empty_scope_advance=True,
    )
    assert result["decision"] == "SAFE_REPLAY"


def test_empty_scope_stays_strict_by_default():
    result = evaluate_scope_advance("abc", "def", [], ["x.py"])
    assert result["decision"] == "EMPTY_SCOPE_STRICT"
