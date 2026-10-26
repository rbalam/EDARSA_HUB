from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GITIGNORE = ROOT / ".gitignore"


def test_preview_local_runtime_artifacts_are_ignored():
    text = GITIGNORE.read_text(encoding="utf-8")
    required = (
        "/EJECUTAR_GATE_WORKER_UNICO*.sh",
        "/.emergent/testing/.runtime/",
        "/.emergent/testing/browser_runs/**",
    )
    for pattern in required:
        assert pattern in text


def test_preview_local_artifact_rules_do_not_ignore_application_code():
    text = GITIGNORE.read_text(encoding="utf-8")
    forbidden = (
        "/backend/",
        "/frontend/",
        "/tools/",
        "/.github/",
    )
    for pattern in forbidden:
        assert pattern not in text
