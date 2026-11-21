"""GATE-ALIGN-1 tests: prepublish contract parity (Publisher/Bridge/Factory/Dispatcher) and Materializer mode safety."""
from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (str(ROOT), str(ROOT / "tools" / "mirror_sync")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tools.mirror_sync import gate_chain_publisher as gcp
from tools.mirror_sync import universal_job_bridge as ujb
from tools.mirror_sync import universal_job_dispatcher as ujd
from tools.mirror_sync.worker_job_factory import canonicalize_job
from tools.mirror_sync.worker_mutation_materializer import apply_mutation


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git(repo: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return res.stdout.strip()


def _init_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@edarsa.local")
    _git(repo, "config", "user.name", "Test")

    (repo / "backend/core").mkdir(parents=True)
    (repo / "tools/mirror_sync").mkdir(parents=True)
    (repo / "backend/tests").mkdir(parents=True)

    (repo / "backend/core/existing.py").write_text("VALUE = 1\n", encoding="utf-8")
    large_py = "# header\n" + ("x = 1\n" * 1000)
    (repo / "backend/tests/large_file.py").write_text(large_py, encoding="utf-8")
    (repo / "backend/tests/sample.py").write_text("def ok():\n    return 1\n", encoding="utf-8")

    sh_path = repo / "tools/mirror_sync/sample.sh"
    sh_path.write_text("#!/usr/bin/env bash\nset -euo pipefail\necho OK\n", encoding="utf-8")
    os.chmod(sh_path, 0o755)

    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "seed")
    head = _git(repo, "rev-parse", "HEAD")
    return repo, head


def _make_job(base_sha: str, actions: list[dict], job_id: str = "ALIGN1-TEST-JOB-001") -> dict:
    return canonicalize_job(
        {
            "job_id": job_id,
            "base_sha": base_sha,
            "mode": "MUTATION",
            "objective": "Prueba GATE-ALIGN-1",
            "requester": {
                "email": "ricardo@edarsa.com.mx",
                "source": "edarsahub-worker-ingress",
                "project": "EDARSAHUB-BOS",
                "chat": "ALIGN1-TESTS",
            },
            "actions": actions,
            "checks": [{"type": "git_diff_check"}],
        }
    )


def test_write_file_existing_without_expected_sha256_rejected_before_publish(tmp_path: Path) -> None:
    repo, head = _init_repo(tmp_path)
    job = _make_job(
        head,
        [
            {
                "type": "write_file",
                "path": "backend/tests/sample.py",
                "content": "def ok():\n    return 2\n",
            }
        ],
    )
    errors = ujb.validate_prepublish_contract(job, repo_root=repo)
    assert any("WRITE_EXISTING_REQUIRES_EXPECTED_SHA256" in e for e in errors)


def test_write_file_existing_with_correct_and_stale_expected_sha256(tmp_path: Path) -> None:
    repo, head = _init_repo(tmp_path)
    target = repo / "backend/tests/sample.py"
    good_sha = _sha_bytes(target.read_bytes())

    # SHA obsoleto -> rechazado antes de publicar
    stale_job = _make_job(
        head,
        [
            {
                "type": "write_file",
                "path": "backend/tests/sample.py",
                "expected_sha256": "0" * 64,
                "content": "def ok():\n    return 2\n",
            }
        ],
    )
    stale_errors = ujb.validate_prepublish_contract(stale_job, repo_root=repo)
    assert any("EXPECTED_SHA256_MISMATCH" in e for e in stale_errors)

    # SHA correcto -> aprobado y compatible con Dispatcher real
    valid_job = _make_job(
        head,
        [
            {
                "type": "write_file",
                "path": "backend/tests/sample.py",
                "expected_sha256": good_sha,
                "content": "def ok():\n    return 2\n",
            }
        ],
    )
    assert ujb.validate_prepublish_contract(valid_job, repo_root=repo) == []
    ujd.apply_action(repo, valid_job["actions"][0])
    assert target.read_text(encoding="utf-8") == "def ok():\n    return 2\n"


def test_write_file_new_and_missing_expected_sha_contract(tmp_path: Path) -> None:
    repo, head = _init_repo(tmp_path)

    # Archivo nuevo sin expected_sha256 -> valido
    new_job = _make_job(
        head,
        [
            {
                "type": "write_file",
                "path": "backend/tests/brand_new.py",
                "content": "def added():\n    return True\n",
            }
        ],
    )
    assert ujb.validate_prepublish_contract(new_job, repo_root=repo) == []

    # Archivo inexistente con expected_sha256 -> rechazado fail-closed
    bad_new = _make_job(
        head,
        [
            {
                "type": "write_file",
                "path": "backend/tests/nonexistent.py",
                "expected_sha256": "a" * 64,
                "content": "x = 1\n",
            }
        ],
    )
    errs = ujb.validate_prepublish_contract(bad_new, repo_root=repo)
    assert any("EXPECTED_FILE_MISSING" in e for e in errs)


def test_replace_text_and_append_once_sha_and_multistep_chain(tmp_path: Path) -> None:
    repo, head = _init_repo(tmp_path)
    target = repo / "backend/tests/sample.py"
    sha1 = _sha_bytes(target.read_bytes())
    after1 = "def ok():\n    return 2\n".encode("utf-8")
    sha2 = _sha_bytes(after1)

    # Cadena de 2 mutaciones V2 sobre el mismo archivo -> ambas validadas secuencialmente
    chained = _make_job(
        head,
        [
            {
                "type": "replace_text",
                "path": "backend/tests/sample.py",
                "source_sha256": sha1,
                "old_text": "return 1",
                "replacement": "return 2",
                "expected_occurrences": 1,
            },
            {
                "type": "append_once",
                "path": "backend/tests/sample.py",
                "source_sha256": sha2,
                "replacement": "\ndef extra():\n    return 3\n",
                "expected_occurrences": 1,
            },
        ],
    )
    assert ujb.validate_prepublish_contract(chained, repo_root=repo) == []

    # source_sha256 obsoleto en V2 -> rechazado antes de publicar
    stale_v2 = _make_job(
        head,
        [
            {
                "type": "replace_text",
                "path": "backend/tests/sample.py",
                "source_sha256": "f" * 64,
                "old_text": "return 1",
                "replacement": "return 2",
                "expected_occurrences": 1,
            }
        ],
    )
    errs = ujb.validate_prepublish_contract(stale_v2, repo_root=repo)
    assert any("SOURCE_SHA_MISMATCH" in e for e in errs)


def test_materializer_preserves_exec_0755_and_non_exec_0644_modes(tmp_path: Path) -> None:
    sh_file = tmp_path / "run.sh"
    sh_file.write_text("#!/usr/bin/env bash\necho OLD\n", encoding="utf-8")
    os.chmod(sh_file, 0o755)
    assert stat.S_IMODE(sh_file.stat().st_mode) == 0o755

    res_sh = apply_mutation(
        sh_file,
        {
            "type": "replace_text",
            "source_sha256": _sha_bytes(sh_file.read_bytes()),
            "old_text": "echo OLD",
            "replacement": "echo NEW",
            "expected_occurrences": 1,
        },
    )
    assert res_sh["state"] == "APPLIED"
    assert stat.S_IMODE(sh_file.stat().st_mode) == 0o755
    assert sh_file.stat().st_mode & 0o777 == 0o755

    py_file = tmp_path / "mod.py"
    py_file.write_text("A = 1\n", encoding="utf-8")
    os.chmod(py_file, 0o644)
    assert stat.S_IMODE(py_file.stat().st_mode) == 0o644

    res_py = apply_mutation(
        py_file,
        {
            "type": "append_once",
            "source_sha256": _sha_bytes(py_file.read_bytes()),
            "replacement": "B = 2\n",
            "expected_occurrences": 1,
        },
    )
    assert res_py["state"] == "APPLIED"
    assert stat.S_IMODE(py_file.stat().st_mode) == 0o644


def test_dispatcher_v2_on_executable_shell_preserves_0100755(tmp_path: Path) -> None:
    repo, head = _init_repo(tmp_path)
    sh = repo / "tools/mirror_sync/sample.sh"
    sha_sh = _sha_bytes(sh.read_bytes())

    job = _make_job(
        head,
        [
            {
                "type": "replace_text",
                "path": "tools/mirror_sync/sample.sh",
                "source_sha256": sha_sh,
                "old_text": "echo OK",
                "replacement": "echo UPDATED",
                "expected_occurrences": 1,
            }
        ],
    )
    assert ujb.validate_prepublish_contract(job, repo_root=repo) == []
    ujd.apply_action(repo, job["actions"][0])
    assert stat.S_IMODE(sh.stat().st_mode) == 0o755
    assert "echo UPDATED" in sh.read_text(encoding="utf-8")


def test_core_growth_and_large_shrink_blocked_before_publish(tmp_path: Path) -> None:
    repo, head = _init_repo(tmp_path)

    # Nuevo archivo en backend/core -> CORE_GROWTH_FORBIDDEN
    core_new = _make_job(
        head,
        [
            {
                "type": "write_file",
                "path": "backend/core/unauthorized_new.py",
                "content": "X = 1\n",
            }
        ],
    )
    errs_core = ujb.validate_prepublish_contract(core_new, repo_root=repo)
    assert any("CORE_GROWTH_FORBIDDEN" in e for e in errs_core)

    # Archivo existente en backend/core con expected_sha256 -> permitido
    existing_core = repo / "backend/core/existing.py"
    core_ok = _make_job(
        head,
        [
            {
                "type": "write_file",
                "path": "backend/core/existing.py",
                "expected_sha256": _sha_bytes(existing_core.read_bytes()),
                "content": "VALUE = 2\n",
            }
        ],
    )
    assert ujb.validate_prepublish_contract(core_ok, repo_root=repo) == []

    # Shrink > 25% en archivo >= 4096 bytes -> WRITE_FILE_LARGE_SHRINK_BLOCKED
    large = repo / "backend/tests/large_file.py"
    shrink_job = _make_job(
        head,
        [
            {
                "type": "write_file",
                "path": "backend/tests/large_file.py",
                "expected_sha256": _sha_bytes(large.read_bytes()),
                "content": "x = 1\n",
            }
        ],
    )
    errs_shrink = ujb.validate_prepublish_contract(shrink_job, repo_root=repo)
    assert any("WRITE_FILE_LARGE_SHRINK_BLOCKED" in e for e in errs_shrink)


def test_whitespace_and_python_bash_syntax_rejected_before_publish(tmp_path: Path) -> None:
    repo, head = _init_repo(tmp_path)
    py_sha = _sha_bytes((repo / "backend/tests/sample.py").read_bytes())
    sh_sha = _sha_bytes((repo / "tools/mirror_sync/sample.sh").read_bytes())

    # Trailing whitespace (equivalente a git diff --check)
    ws_job = _make_job(
        head,
        [
            {
                "type": "replace_text",
                "path": "backend/tests/sample.py",
                "source_sha256": py_sha,
                "old_text": "return 1",
                "replacement": "return 2   ",
                "expected_occurrences": 1,
            }
        ],
    )
    ws_errs = ujb.validate_prepublish_contract(ws_job, repo_root=repo)
    assert any("PREFLIGHT_WHITESPACE_ERROR" in e and "TRAILING_WHITESPACE" in e for e in ws_errs)

    # Sintaxis Python invalida
    bad_py = _make_job(
        head,
        [
            {
                "type": "write_file",
                "path": "backend/tests/broken.py",
                "content": "def broken(:\n    pass\n",
            }
        ],
    )
    py_errs = ujb.validate_prepublish_contract(bad_py, repo_root=repo)
    assert any("PREFLIGHT_PYTHON_SYNTAX_ERROR" in e for e in py_errs)

    # Sintaxis Bash invalida
    bad_sh = _make_job(
        head,
        [
            {
                "type": "replace_text",
                "path": "tools/mirror_sync/sample.sh",
                "source_sha256": sh_sha,
                "old_text": "echo OK",
                "replacement": "if true; then\necho UNCLOSED",
                "expected_occurrences": 1,
            }
        ],
    )
    sh_errs = ujb.validate_prepublish_contract(bad_sh, repo_root=repo)
    assert any("PREFLIGHT_BASH_SYNTAX_ERROR" in e for e in sh_errs)


def test_factory_base_sha_and_publisher_submit_fail_closed_and_concurrency(tmp_path: Path, monkeypatch) -> None:
    # base_sha malformado rechazado en worker_job_factory
    with pytest.raises(ValueError, match="INVALID_BASE_SHA"):
        canonicalize_job(
            {
                "job_id": "BAD-BASE-SHA-1",
                "base_sha": "not-a-sha",
                "objective": "test",
                "requester": {"email": "ricardo@edarsa.com.mx", "source": "test"},
            }
        )

    # gate_chain_publisher.submit() rechaza write_file existente sin expected_sha256 ANTES de escribir draft ni llamar RBAC
    called = {"draft": False, "rbac": False}
    monkeypatch.setattr(gcp, "_atomic_submit_draft", lambda *a, **k: called.__setitem__("draft", True))
    monkeypatch.setattr(gcp, "_submit_local_lifecycle", lambda *a, **k: None)
    monkeypatch.setattr(gcp, "_submit_remote_exists", lambda *a, **k: False)

    res = gcp.submit(
        {
            "job_id": "PREPUB-BLOCK-EXISTING-NO-SHA-1",
            "mode": "MUTATION",
            "objective": "Debe bloquearse antes de publicar",
            "requester": {"email": "ricardo@edarsa.com.mx", "source": "test"},
            "actions": [
                {
                    "type": "write_file",
                    "path": "tools/mirror_sync/worker_job_factory.py",
                    "content": "# overwrite without sha\n",
                }
            ],
            "checks": [{"type": "git_diff_check"}],
        }
    )
    assert res["status"] == "INVALID_JOB"
    assert res["production_touched"] is False
    assert any("WRITE_EXISTING_REQUIRES_EXPECTED_SHA256" in e for e in res.get("errors", []))
    assert called["draft"] is False

    # Concurrencia determinista: multiples hilos ejecutando validate_prepublish_contract en paralelo
    repo, head = _init_repo(tmp_path)
    job = _make_job(
        head,
        [
            {
                "type": "write_file",
                "path": "backend/tests/sample.py",
                "content": "def ok():\n    return 2\n",
            }
        ],
    )
    with ThreadPoolExecutor(max_workers=6) as pool:
        outcomes = list(pool.map(lambda _: ujb.validate_prepublish_contract(job, repo_root=repo), range(12)))
    assert all(any("WRITE_EXISTING_REQUIRES_EXPECTED_SHA256" in e for e in errs) for errs in outcomes)


def test_publisher_rbac_and_duplicate_fail_closed_preserved(monkeypatch, tmp_path: Path) -> None:
    # Duplicado remoto -> ALREADY_SUBMITTED
    monkeypatch.setattr(gcp, "_atomic_submit_draft", lambda tpl: tmp_path / "draft.json")
    monkeypatch.setattr(gcp, "_submit_local_lifecycle", lambda jid: None)
    monkeypatch.setattr(gcp, "_submit_remote_exists", lambda *a, **k: True)

    ro_job = {
        "job_id": "DUP-CHECK-RO-1",
        "mode": "READ_ONLY",
        "objective": "Solo lectura",
        "requester": {"email": "ricardo@edarsa.com.mx", "source": "test"},
        "actions": [],
        "checks": [{"type": "git_diff_check"}],
    }
    dup_res = gcp.submit(ro_job)
    assert dup_res["status"] == "ALREADY_SUBMITTED"
    assert dup_res["production_touched"] is False

    # RBAC denegado -> REQUESTER_DENIED
    monkeypatch.setattr(gcp, "_submit_remote_exists", lambda *a, **k: False)
    import tools.mirror_sync.worker_requester_rbac as rbac_mod
    monkeypatch.setattr(rbac_mod, "authorize_requester", lambda req: {"allowed": False, "reason": "REQUESTER_NOT_SUPERADMIN"})

    rbac_res = gcp.submit(ro_job)
    assert rbac_res["status"] == "REQUESTER_DENIED"
    assert rbac_res["reason"] == "REQUESTER_NOT_SUPERADMIN"
    assert rbac_res["production_touched"] is False
