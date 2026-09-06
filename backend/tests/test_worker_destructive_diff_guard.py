from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "tools" / "mirror_sync" / "universal_job_bridge.py"
GUARD = ROOT / "scripts" / "agent_guardrails" / "validate_repository_artifacts.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_delete_file_requires_expected_sha256():
    bridge = load_module("worker_bridge_destructive_guard", BRIDGE)
    errors = bridge.validate_action({"type": "delete_file", "path": "tmp/example.txt"}, 1)
    assert "ACTION_1_EXPECTED_SHA256_REQUIRED" in errors

    errors = bridge.validate_action(
        {"type": "delete_file", "path": "tmp/example.txt", "expected_sha256": "bad"},
        1,
    )
    assert "ACTION_1_INVALID_SHA256" in errors

    errors = bridge.validate_action(
        {"type": "delete_file", "path": "tmp/example.txt", "expected_sha256": "a" * 64},
        1,
    )
    assert errors == []


def test_guard_blocks_critical_delete():
    guard = load_module("repository_destructive_guard_critical", GUARD)
    rc = guard.validate(
        [("D", "backend/server.py")],
        lambda _path: 0,
        lambda _path: 682735,
    )
    assert rc == 1


def test_guard_blocks_large_shrink():
    guard = load_module("repository_destructive_guard_shrink", GUARD)
    rc = guard.validate(
        [("M", "backend/example.py")],
        lambda _path: 2000,
        lambda _path: 10000,
    )
    assert rc == 1


def test_guard_blocks_mass_delete():
    guard = load_module("repository_destructive_guard_mass_delete", GUARD)
    changes = [("D", f"backend/tmp/file_{i}.py") for i in range(11)]
    rc = guard.validate(changes, lambda _path: 0, lambda _path: 100)
    assert rc == 1


def test_guard_allows_non_destructive_modify():
    guard = load_module("repository_destructive_guard_safe", GUARD)
    rc = guard.validate(
        [("M", "backend/example.py")],
        lambda _path: 9000,
        lambda _path: 10000,
    )
    assert rc == 0


def test_guard_diff_filters_include_deletions():
    source = GUARD.read_text(encoding="utf-8")
    assert source.count("--diff-filter=ACMRD") == 2
    assert "CRITICAL_DELETE_PATHS" in source
    assert "DELETE_FILE_LIMIT = 10" in source
    assert "DELETE_BYTES_LIMIT = 5 * 1024 * 1024" in source
