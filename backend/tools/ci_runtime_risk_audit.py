#!/usr/bin/env python3
"""
Auditoría determinista de riesgos ejecutables en runtime.

No ejecuta módulos del proyecto, no abre conexiones y no lee secretos.
Analiza Python mediante AST y frontend mediante patrones de imports/clientes.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


DIRECT_SQL_CALLS = {
    "pymssql.connect",
    "pyodbc.connect",
}

MONGO_PREFIXES = (
    "pymongo",
    "motor",
)

MONGO_CLIENT_CALLS = {
    "pymongo.MongoClient",
    "motor.motor_asyncio.AsyncIOMotorClient",
}

ALLOWED_DIRECT_SQL_FILES = {
    "backend/core/sql_first/connection_factory.py",
}

EXCLUDED_PARTS = {
    "__pycache__",
    "graphify-out",
    "auditorias",
    "auditorias_p2",
    "auditorias_p4",
    "tests",
    "tests_guardrails",
    "scripts",
    "migrations",
    "database",
    "docs",
}

EXCLUDED_NAME_MARKERS = (
    ".backup",
    "_backup_",
    ".bak",
    ".old",
    ".orig",
)

FRONTEND_MONGO_PATTERNS = {
    "frontend_mongodb_import": re.compile(
        r"""(?x)
        (?:from\s+["']mongodb["'])
        |
        (?:require\(\s*["']mongodb["']\s*\))
        |
        (?:import\(\s*["']mongodb["']\s*\))
        """
    ),
    "frontend_mongo_client": re.compile(
        r"\bMongoClient\s*\("
    ),
    "frontend_mongodb_uri": re.compile(
        r"mongodb(?:\+srv)?://",
        re.IGNORECASE,
    ),
}


@dataclass(frozen=True)
class Finding:
    category: str
    path: str
    line: int
    symbol: str
    detail: str


def _is_excluded(
    path: Path,
    repo_root: Path,
) -> bool:
    relative = path.relative_to(repo_root)

    if any(
        part in EXCLUDED_PARTS
        for part in relative.parts
    ):
        return True

    lowered = path.name.lower()

    return any(
        marker in lowered
        for marker in EXCLUDED_NAME_MARKERS
    )


def _runtime_roots(
    repo_root: Path,
    scope: str,
) -> tuple[Path, ...]:
    backend = repo_root / "backend"

    if scope == "scheduler":
        return (
            backend / "core" / "scheduler",
        )

    return (
        backend / "core",
        backend / "modules",
        backend / "api",
        backend / "server.py",
    )


def _collect_python_files(
    repo_root: Path,
    scope: str,
) -> list[Path]:
    files: set[Path] = set()

    for root in _runtime_roots(
        repo_root,
        scope,
    ):
        if root.is_file():
            if (
                root.suffix == ".py"
                and not _is_excluded(
                    root,
                    repo_root,
                )
            ):
                files.add(root)
            continue

        if not root.exists():
            continue

        for path in root.rglob("*.py"):
            if not _is_excluded(
                path,
                repo_root,
            ):
                files.add(path)

    return sorted(files)


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)

        if parent:
            return f"{parent}.{node.attr}"

        return node.attr

    return ""


class PythonScanner(ast.NodeVisitor):
    def __init__(
        self,
        *,
        path: Path,
        repo_root: Path,
        scope: str,
        source_lines: list[str],
    ) -> None:
        self.path = path
        self.repo_root = repo_root
        self.scope = scope
        self.source_lines = source_lines
        self.aliases: dict[str, str] = {}
        self.findings: list[Finding] = []
        self.allowed_direct_sql_count = 0

    @property
    def relative_path(self) -> str:
        return self.path.relative_to(
            self.repo_root
        ).as_posix()

    def _source_line(self, line: int) -> str:
        if 1 <= line <= len(self.source_lines):
            return self.source_lines[
                line - 1
            ].strip()

        return ""

    def _add(
        self,
        category: str,
        symbol: str,
        node: ast.AST,
        detail: str | None = None,
    ) -> None:
        line = int(
            getattr(node, "lineno", 0)
        )

        self.findings.append(
            Finding(
                category=category,
                path=self.relative_path,
                line=line,
                symbol=symbol,
                detail=(
                    detail
                    if detail is not None
                    else self._source_line(line)
                ),
            )
        )

    def _resolve(self, symbol: str) -> str:
        first, separator, remainder = (
            symbol.partition(".")
        )
        resolved = self.aliases.get(
            first,
            first,
        )

        if separator:
            return f"{resolved}.{remainder}"

        return resolved

    def visit_Import(
        self,
        node: ast.Import,
    ) -> None:
        for alias in node.names:
            local = (
                alias.asname
                or alias.name.split(".")[0]
            )
            self.aliases[local] = alias.name

            if alias.name.startswith(
                MONGO_PREFIXES
            ):
                self._add(
                    "mongo_import",
                    alias.name,
                    node,
                )

        self.generic_visit(node)

    def visit_ImportFrom(
        self,
        node: ast.ImportFrom,
    ) -> None:
        module = node.module or ""

        for alias in node.names:
            local = (
                alias.asname
                or alias.name
            )
            full = (
                f"{module}.{alias.name}"
                if module
                else alias.name
            )
            self.aliases[local] = full

        if module.startswith(
            MONGO_PREFIXES
        ):
            imported = ",".join(
                alias.name
                for alias in node.names
            )
            self._add(
                "mongo_import",
                f"{module}:{imported}",
                node,
            )

        self.generic_visit(node)

    def visit_Call(
        self,
        node: ast.Call,
    ) -> None:
        raw_symbol = _dotted_name(
            node.func
        )
        symbol = self._resolve(
            raw_symbol
        )

        if (
            self.scope in {"sql", "scheduler"}
            and symbol in DIRECT_SQL_CALLS
        ):
            if (
                self.scope == "sql"
                and self.relative_path
                in ALLOWED_DIRECT_SQL_FILES
            ):
                self.allowed_direct_sql_count += 1
            else:
                self._add(
                    "direct_sql_call",
                    symbol,
                    node,
                )

        if symbol in MONGO_CLIENT_CALLS:
            self._add(
                "mongo_client_call",
                symbol,
                node,
            )

        is_execute_sql_query = (
            raw_symbol == "execute_sql_query"
            or symbol.endswith(
                ".execute_sql_query"
            )
        )

        if (
            self.scope == "scheduler"
            and is_execute_sql_query
        ):
            keywords = {
                keyword.arg: keyword.value
                for keyword in node.keywords
                if keyword.arg is not None
            }

            if "timeout" in keywords:
                self._add(
                    "invalid_execute_sql_keyword",
                    raw_symbol,
                    node,
                    "Usa timeout=; el contrato "
                    "requiere timeout_seconds=",
                )

            context_node = keywords.get(
                "context"
            )

            valid_context = (
                isinstance(
                    context_node,
                    ast.Constant,
                )
                and context_node.value
                == "jobs"
            )

            if not valid_context:
                self._add(
                    "missing_jobs_context",
                    raw_symbol,
                    node,
                    "execute_sql_query dentro "
                    "del scheduler debe declarar "
                    'context="jobs"',
                )

        self.generic_visit(node)


def _scan_python(
    repo_root: Path,
    scope: str,
) -> tuple[
    list[Finding],
    int,
    int,
]:
    findings: list[Finding] = []
    parse_errors = 0
    allowed_direct_sql_count = 0

    files = _collect_python_files(
        repo_root,
        scope,
    )

    for path in files:
        source = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        try:
            tree = ast.parse(
                source,
                filename=str(path),
            )
        except SyntaxError as exc:
            parse_errors += 1
            findings.append(
                Finding(
                    category="parse_error",
                    path=path.relative_to(
                        repo_root
                    ).as_posix(),
                    line=int(
                        exc.lineno or 0
                    ),
                    symbol="SyntaxError",
                    detail=exc.msg,
                )
            )
            continue

        scanner = PythonScanner(
            path=path,
            repo_root=repo_root,
            scope=scope,
            source_lines=source.splitlines(),
        )
        scanner.visit(tree)

        findings.extend(
            scanner.findings
        )
        allowed_direct_sql_count += (
            scanner.allowed_direct_sql_count
        )

    return (
        findings,
        parse_errors,
        allowed_direct_sql_count,
    )


def _scan_frontend(
    repo_root: Path,
) -> list[Finding]:
    findings: list[Finding] = []
    frontend_root = (
        repo_root / "frontend" / "src"
    )

    if not frontend_root.exists():
        return findings

    for path in sorted(
        frontend_root.rglob("*")
    ):
        if (
            not path.is_file()
            or path.suffix.lower()
            not in {
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
            }
            or "node_modules" in path.parts
            or any(
                marker in path.name.lower()
                for marker
                in EXCLUDED_NAME_MARKERS
            )
        ):
            continue

        lines = path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()

        for line_number, line in enumerate(
            lines,
            start=1,
        ):
            for category, pattern in (
                FRONTEND_MONGO_PATTERNS.items()
            ):
                if pattern.search(line):
                    findings.append(
                        Finding(
                            category=category,
                            path=path.relative_to(
                                repo_root
                            ).as_posix(),
                            line=line_number,
                            symbol=category,
                            detail=line.strip(),
                        )
                    )

    return findings


def audit_repository(
    repo_root: Path,
    scope: str,
) -> tuple[
    list[Finding],
    dict[str, int],
]:
    findings, parse_errors, allowed = (
        _scan_python(
            repo_root,
            scope,
        )
    )

    if scope == "menu":
        findings.extend(
            _scan_frontend(repo_root)
        )

    findings.sort(
        key=lambda item: (
            item.category,
            item.path,
            item.line,
            item.symbol,
        )
    )

    counts = Counter(
        finding.category
        for finding in findings
    )

    summary = {
        "python_parse_error_count": (
            parse_errors
        ),
        "allowed_direct_sql_count": (
            allowed
        ),
        "finding_count": len(findings),
    }

    for category, count in sorted(
        counts.items()
    ):
        summary[
            f"{category}_count"
        ] = count

    return findings, summary


def _parse_strict(value: str) -> bool:
    normalized = str(value).strip().lower()

    if normalized == "true":
        return True

    if normalized == "false":
        return False

    raise argparse.ArgumentTypeError(
        "strict debe ser true o false"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scope",
        choices=(
            "menu",
            "scheduler",
            "sql",
        ),
        required=True,
    )
    parser.add_argument(
        "--strict",
        type=_parse_strict,
        default=False,
    )
    parser.add_argument(
        "--repo-root",
        default=".",
    )

    args = parser.parse_args()
    repo_root = Path(
        args.repo_root
    ).resolve()

    findings, summary = (
        audit_repository(
            repo_root,
            args.scope,
        )
    )

    print(f"scope={args.scope}")
    print(
        f"strict={str(args.strict).lower()}"
    )

    for key, value in sorted(
        summary.items()
    ):
        print(f"{key}={value}")

    for finding in findings:
        print(
            f"{finding.category} | "
            f"{finding.path}:{finding.line} | "
            f"{finding.symbol} | "
            f"{finding.detail}"
        )

    if findings and args.strict:
        print("runtime_risk_audit=FAIL")
        return 1

    print("runtime_risk_audit=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
