from pathlib import Path
import subprocess

import pytest

from tools.mirror_sync import git_divergence_guard as guard


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return proc.stdout.strip()


def init_repo(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"

    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    subprocess.run(
        ["git", "init", str(repo)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    git(repo, "config", "user.name", "EDARSAHUB Worker")
    git(repo, "config", "user.email", "worker@edarsahub.local")
    git(repo, "remote", "add", "origin", str(remote))

    return remote, repo


def commit_file(
    repo: Path,
    name: str,
    content: str,
    message: str,
) -> str:
    target = repo / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    git(repo, "add", "--", name)
    git(repo, "commit", "-m", message)

    return git(repo, "rev-parse", "HEAD")


def test_reseed_contract_exists():
    assert callable(
        guard.reseed_mirror_from_development
    )


def test_reseed_source_has_expected_safety_contract():
    source = (
        Path(__file__).resolve().parents[2]
        / "tools"
        / "mirror_sync"
        / "git_divergence_guard.py"
    ).read_text(encoding="utf-8")

    block = source.split(
        "def reseed_mirror_from_development(",
        1,
    )[1].split(
        "\ndef main() -> int:",
        1,
    )[0]

    assert '"commit-tree"' in block
    assert "authorized_push(" in block

    assert '"reset"' not in block
    assert '"rebase"' not in block

    assert (
        'f"{reseed_commit}:refs/heads/{MIRROR_BRANCH}"'
        in block
    )

    assert (
        'f"{reseed_commit}:refs/heads/{DEV_BRANCH}"'
        not in block
    )


def test_reseed_preserves_mirror_history_and_dev_tree(
    tmp_path,
    monkeypatch,
):
    _remote, repo = init_repo(tmp_path)

    base = commit_file(
        repo,
        "shared.txt",
        "base\n",
        "base",
    )

    git(repo, "branch", "-M", guard.DEV_BRANCH)

    git(
        repo,
        "push",
        "origin",
        f"{base}:refs/heads/{guard.DEV_BRANCH}",
    )

    git(repo, "checkout", "-b", "mirror-local", base)

    mirror = commit_file(
        repo,
        "preview-only.txt",
        "preview\n",
        "preview",
    )

    git(
        repo,
        "push",
        "origin",
        f"{mirror}:refs/heads/{guard.MIRROR_BRANCH}",
    )

    git(repo, "checkout", guard.DEV_BRANCH)

    development = commit_file(
        repo,
        "development-only.txt",
        "development\n",
        "development",
    )

    git(
        repo,
        "push",
        "origin",
        f"{development}:refs/heads/{guard.DEV_BRANCH}",
    )

    git(repo, "fetch", "origin")

    result = guard.reseed_mirror_from_development(
        repo,
        development=development,
        mirror=mirror,
        job_id="TEST-MIRROR-RESEED",
        owner="pytest",
    )

    assert result["status"] == "CERTIFIED_MIRROR_RESEEDED"
    assert result["development_moved"] is False
    assert result["history_preserved"] is True
    assert result["tree_matches_development"] is True
    assert result["development_ref_updated"] is False

    git(repo, "fetch", "origin")

    remote_dev = git(
        repo,
        "rev-parse",
        f"origin/{guard.DEV_BRANCH}",
    )

    remote_mirror = git(
        repo,
        "rev-parse",
        f"origin/{guard.MIRROR_BRANCH}",
    )

    assert remote_dev == development
    assert remote_mirror == result["reseed_commit"]

    dev_tree = git(
        repo,
        "rev-parse",
        f"{remote_dev}^{{tree}}",
    )

    mirror_tree = git(
        repo,
        "rev-parse",
        f"{remote_mirror}^{{tree}}",
    )

    assert mirror_tree == dev_tree

    parents = git(
        repo,
        "show",
        "-s",
        "--format=%P",
        remote_mirror,
    ).split()

    assert parents == [development, mirror]

    subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            mirror,
            remote_mirror,
        ],
        cwd=str(repo),
        check=True,
    )


def test_reseed_fails_closed_when_remote_moves(tmp_path):
    _remote, repo = init_repo(tmp_path)

    base = commit_file(
        repo,
        "base.txt",
        "base\n",
        "base",
    )

    git(repo, "branch", "-M", guard.DEV_BRANCH)

    git(
        repo,
        "push",
        "origin",
        f"{base}:refs/heads/{guard.DEV_BRANCH}",
    )

    git(
        repo,
        "push",
        "origin",
        f"{base}:refs/heads/{guard.MIRROR_BRANCH}",
    )

    with pytest.raises(
        guard.GitGuardError,
        match="REMOTE_MOVED_RETRY_REQUIRED",
    ):
        guard.reseed_mirror_from_development(
            repo,
            development="0" * 40,
            mirror=base,
            job_id="TEST-REMOTE-MOVED",
            owner="pytest",
        )
