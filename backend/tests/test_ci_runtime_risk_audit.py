from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "ci_runtime_risk_audit.py"
)


def _write(
    root: Path,
    relative: str,
    content: str,
) -> None:
    path = root / relative
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        content,
        encoding="utf-8",
    )


def _run(
    root: Path,
    scope: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--scope",
            scope,
            "--strict",
            "true",
            "--repo-root",
            str(root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_sql_allows_only_canonical_factory(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        (
            "backend/core/sql_first/"
            "connection_factory.py"
        ),
        (
            "import pymssql\n"
            "def open_allowed():\n"
            "    return pymssql.connect()\n"
        ),
    )

    result = _run(
        tmp_path,
        "sql",
    )

    assert result.returncode == 0
    assert "allowed_direct_sql_count=1" in (
        result.stdout
    )
    assert "finding_count=0" in result.stdout


def test_sql_rejects_runtime_direct_driver(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        "backend/modules/example.py",
        (
            "import pymssql\n"
            "def open_forbidden():\n"
            "    return pymssql.connect()\n"
        ),
    )

    result = _run(
        tmp_path,
        "sql",
    )

    assert result.returncode == 1
    assert "direct_sql_call_count=1" in (
        result.stdout
    )


def test_scheduler_rejects_invalid_query_contract(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        (
            "backend/core/scheduler/jobs/"
            "example.py"
        ),
        (
            "from core.db import execute_sql_query\n"
            "def run():\n"
            "    return execute_sql_query("
            "'h', 1433, 'd', 'u', 'p', "
            "'SELECT 1', timeout=5)\n"
        ),
    )

    result = _run(
        tmp_path,
        "scheduler",
    )

    assert result.returncode == 1
    assert (
        "invalid_execute_sql_keyword_count=1"
        in result.stdout
    )
    assert (
        "missing_jobs_context_count=1"
        in result.stdout
    )


def test_scheduler_accepts_jobs_context(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        (
            "backend/core/scheduler/jobs/"
            "example.py"
        ),
        (
            "from core.db import execute_sql_query\n"
            "def run():\n"
            "    return execute_sql_query("
            "'h', 1433, 'd', 'u', 'p', "
            "'SELECT 1', "
            "timeout_seconds=5, "
            "context='jobs')\n"
        ),
    )

    result = _run(
        tmp_path,
        "scheduler",
    )

    assert result.returncode == 0
    assert "finding_count=0" in result.stdout


def test_menu_ignores_business_names_and_urls(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        "frontend/src/example.js",
        (
            "const unit = 'ORIGEN';\n"
            "const endpoint = 'https://example.test';\n"
            "const system = 'MPRO';\n"
        ),
    )

    result = _run(
        tmp_path,
        "menu",
    )

    assert result.returncode == 0
    assert "finding_count=0" in result.stdout


def test_menu_rejects_mongo_runtime_import(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        "backend/modules/example.py",
        (
            "from pymongo import MongoClient\n"
            "client = MongoClient()\n"
        ),
    )

    result = _run(
        tmp_path,
        "menu",
    )

    assert result.returncode == 1
    assert "mongo_import_count=1" in (
        result.stdout
    )
    assert "mongo_client_call_count=1" in (
        result.stdout
    )
