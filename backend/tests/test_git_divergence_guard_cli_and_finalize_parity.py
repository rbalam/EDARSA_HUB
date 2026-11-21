"""Regression tests for git_divergence_guard CLI exit codes and finalize_local_snapshot parity."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "tools/mirror_sync/git_divergence_guard.py"
FINALIZER = ROOT / "tools/mirror_sync/finalize_local_snapshot.sh"
PUBLISHER = ROOT / "tools/mirror_sync/publish_local_snapshot.sh"
SAFETY_GUARD = ROOT / "tools/mirror_sync/shared_app_safety_guard.sh"


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    res = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and res.returncode != 0:
        raise AssertionError(res.stdout)
    return res


def _setup_repo_pair(tmp_path: Path) -> tuple[Path, Path, Path]:
    remote = tmp_path / "remote.git"
    local = tmp_path / "local"
    peer = tmp_path / "peer"
    _git(tmp_path, "init", "--bare", str(remote))
    local.mkdir()
    _git(local, "init")
    _git(local, "config", "user.email", "test@edarsa.local")
    _git(local, "config", "user.name", "Test")
    (local / ".emergent").mkdir(parents=True, exist_ok=True)
    (local / ".emergent/system_deps.txt").write_text("git\n", encoding="utf-8")
    (local / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(local, "add", ".emergent/system_deps.txt", "seed.txt")
    _git(local, "commit", "-m", "seed")
    _git(local, "branch", "-M", "Edarsahub_Desarrollo")
    _git(local, "remote", "add", "origin", str(remote))
    _git(local, "push", "-u", "origin", "Edarsahub_Desarrollo")
    _git(tmp_path, "clone", "-b", "Edarsahub_Desarrollo", str(remote), str(peer))
    _git(peer, "config", "user.email", "peer@edarsa.local")
    _git(peer, "config", "user.name", "Peer")
    return remote, local, peer


def _run_guard(*args: str) -> tuple[int, dict]:
    res = subprocess.run(
        [sys.executable, str(GUARD), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    lines = [ln for ln in res.stdout.splitlines() if ln.strip()]
    payload = json.loads(lines[-1]) if lines else {}
    return res.returncode, payload


def test_cli_acquire_and_release_lock_exit_zero_and_busy_fails_closed(tmp_path: Path) -> None:
    _, local, _ = _setup_repo_pair(tmp_path)

    rc_acq, acq = _run_guard(
        "acquire-lock",
        "--repo", str(local),
        "--job-id", "parity-job-1",
        "--owner", "test-owner",
        "--owner-pid", str(os.getpid()),
    )
    assert rc_acq == 0, f"acquire-lock debe retornar 0: {acq}"
    assert acq.get("job_id") == "parity-job-1"
    assert acq.get("lock_dir")

    # Segundo writer concurrente debe fallar cerrado con exit 1 y GIT_LOCK_BUSY
    rc_busy, busy = _run_guard(
        "acquire-lock",
        "--repo", str(local),
        "--job-id", "parity-job-2",
        "--owner", "other-owner",
        "--owner-pid", str(os.getpid()),
    )
    assert rc_busy == 1
    assert busy.get("status") == "GIT_LOCK_BUSY"

    # Liberar lock valido retorna exit 0
    rc_rel, rel = _run_guard(
        "release-lock",
        "--repo", str(local),
        "--job-id", "parity-job-1",
        "--owner", "test-owner",
    )
    assert rc_rel == 0, f"release-lock debe retornar 0: {rel}"
    assert rel == {"released": True}

    # Segunda liberacion sobre lock inexistente falla cerrado con exit 1
    rc_rel2, rel2 = _run_guard(
        "release-lock",
        "--repo", str(local),
        "--job-id", "parity-job-1",
        "--owner", "test-owner",
    )
    assert rc_rel2 == 1
    assert rel2.get("status") == "GIT_LOCK_BUSY"


def test_cli_inspect_refresh_and_doctor_exit_codes(tmp_path: Path) -> None:
    _, local, peer = _setup_repo_pair(tmp_path)

    rc_insp, insp = _run_guard("inspect", "--repo", str(local), "--no-fetch")
    assert rc_insp == 0, f"inspect debe retornar 0: {insp}"
    assert insp.get("local_head")
    assert insp.get("classification") == "SYNC"

    # Doctor sin --auto-fix sigue retornando 2
    rc_doc_no_fix, doc_no_fix = _run_guard("doctor", "--repo", str(local))
    assert rc_doc_no_fix == 2
    assert doc_no_fix.get("status") == "AUTO_FIX_REQUIRED"

    # Peer avanza remoto -> refresh CLI debe avanzar y retornar 0
    (peer / "remote_update.txt").write_text("ok\n", encoding="utf-8")
    _git(peer, "add", "remote_update.txt")
    _git(peer, "commit", "-m", "remote advance")
    _git(peer, "push", "origin", "Edarsahub_Desarrollo")
    remote_sha = _git(peer, "rev-parse", "HEAD").stdout.strip()

    rc_ref, ref = _run_guard(
        "refresh",
        "--repo", str(local),
        "--expected-remote", remote_sha,
        "--job-id", "parity-refresh-1",
        "--owner", "test-owner",
        "--owner-pid", str(os.getpid()),
    )
    assert rc_ref == 0, f"refresh debe retornar 0: {ref}"
    assert ref.get("local_head") == remote_sha

    # Doctor fail-closed en conflicto/divergencia no resuelta sigue retornando != 0
    (local / "dirty.txt").write_text("untracked\n", encoding="utf-8")
    _git(local, "push", "origin", "HEAD:refs/heads/mirror/emergent-live")
    rc_doc_dirty, doc_dirty = _run_guard("doctor", "--repo", str(local), "--auto-fix")
    assert rc_doc_dirty == 1
    assert doc_dirty.get("converged") is False


def test_shared_app_safety_guard_lock_wrappers_work_under_strict_bash(tmp_path: Path) -> None:
    _, local, _ = _setup_repo_pair(tmp_path)
    script = (
        "set -euo pipefail\n"
        f"export EDARSAHUB_APP={str(local)!r}\n"
        f"mkdir -p {str(local / 'tools/mirror_sync')!r}\n"
        f"cp {str(GUARD)!r} {str(local / 'tools/mirror_sync/git_divergence_guard.py')!r}\n"
        f". {str(SAFETY_GUARD)!r}\n"
        "edarsahub_acquire_git_writer_lock wrap-job-1 wrap-owner >/dev/null\n"
        "edarsahub_release_git_writer_lock wrap-job-1 wrap-owner >/dev/null\n"
        "echo WRAPPER_OK=YES\n"
    )
    res = subprocess.run(["bash", "-c", script], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    assert res.returncode == 0, res.stdout
    assert "WRAPPER_OK=YES" in res.stdout


def test_finalize_local_snapshot_parity_with_publish_and_safety_guard(tmp_path: Path) -> None:
    # 1. Validacion sintactica bash
    for sh in (FINALIZER, PUBLISHER, SAFETY_GUARD):
        chk = subprocess.run(["bash", "-n", str(sh)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        assert chk.returncode == 0, f"bash -n fallo en {sh}: {chk.stdout}"

    # 2. Contrato de paridad explicito en finalize_local_snapshot.sh
    fin_txt = FINALIZER.read_text(encoding="utf-8")
    assert "edarsahub_expected_platform_system_deps_drift" in fin_txt
    assert "git add -u -- . ':(exclude).emergent/system_deps.txt'" in fin_txt
    assert "edarsahub_effective_unstaged_names" in fin_txt
    assert 'TRACKED_AFTER="$(git diff --name-only | wc -l)"' not in fin_txt

    # 3. Comportamiento real de exclusion solo para drift vacio esperado vs fail-closed en drift inesperado
    _, local, _ = _setup_repo_pair(tmp_path)
    (local / ".emergent/system_deps.txt").write_text("", encoding="utf-8")
    res_expected = subprocess.run(
        [
            "bash",
            "-c",
            (
                f"set -euo pipefail; export EDARSAHUB_APP={str(local)!r}; "
                f". {str(SAFETY_GUARD)!r}; "
                "edarsahub_expected_platform_system_deps_drift; "
                "COUNT=$(edarsahub_effective_unstaged_names | awk 'NF' | wc -l); echo COUNT=$COUNT"
            ),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert res_expected.returncode == 0, res_expected.stdout
    assert "COUNT=0" in res_expected.stdout

    # Drift inesperado (contenido no vacio) debe seguir bloqueando fail-closed
    (local / ".emergent/system_deps.txt").write_text("curl\n", encoding="utf-8")
    res_unexpected = subprocess.run(
        [
            "bash",
            "-c",
            (
                f"export EDARSAHUB_APP={str(local)!r}; "
                f". {str(SAFETY_GUARD)!r}; "
                "if edarsahub_expected_platform_system_deps_drift; then echo EXPECTED=YES; else echo EXPECTED=NO; fi; "
                "COUNT=$(edarsahub_effective_unstaged_names | awk 'NF' | wc -l); echo COUNT=$COUNT"
            ),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert res_unexpected.returncode == 0, res_unexpected.stdout
    assert "EXPECTED=NO" in res_unexpected.stdout
    assert "COUNT=1" in res_unexpected.stdout
