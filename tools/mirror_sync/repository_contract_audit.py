#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MAX_FILE_BYTES = 2_000_000
DEFAULT_EXCLUDED_PARTS = {".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv", "coverage"}
SENSITIVE_NAMES = {".env", "id_rsa", "id_ed25519"}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


def _safe_relative(value: str) -> Path:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError("INVALID_PATH")
    path = Path(value.strip())
    if path.is_absolute() or ".." in path.parts or (path.parts and path.parts[0] == ".git"):
        raise ValueError("INVALID_PATH")
    return path


def validate_request(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("REQUEST_REQUIRED")
    paths = request.get("paths")
    if not isinstance(paths, list) or not paths:
        raise ValueError("PATHS_REQUIRED")
    normalized_paths = [str(_safe_relative(str(p))) for p in paths]
    terms = request.get("search_terms")
    if not isinstance(terms, list) or not terms or not all(isinstance(t, str) and t.strip() for t in terms):
        raise ValueError("SEARCH_TERMS_REQUIRED")
    include_patterns = request.get("include_patterns", [])
    exclude_patterns = request.get("exclude_patterns", [])
    if not isinstance(include_patterns, list) or not all(isinstance(x, str) and x.strip() for x in include_patterns):
        raise ValueError("INCLUDE_PATTERNS_INVALID")
    if not isinstance(exclude_patterns, list) or not all(isinstance(x, str) and x.strip() for x in exclude_patterns):
        raise ValueError("EXCLUDE_PATTERNS_INVALID")
    max_results = request.get("max_results", 500)
    if not isinstance(max_results, int) or not 1 <= max_results <= 5000:
        raise ValueError("MAX_RESULTS_INVALID")
    return {
        "paths": normalized_paths,
        "search_terms": sorted({t.strip().lower() for t in terms}),
        "include_patterns": list(include_patterns),
        "exclude_patterns": list(exclude_patterns),
        "max_results": max_results,
    }


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(Path(path).name, pattern) for pattern in patterns)


def _is_sensitive(path: Path) -> bool:
    if path.name in SENSITIVE_NAMES or path.suffix.lower() in SENSITIVE_SUFFIXES:
        return True
    return any(part in DEFAULT_EXCLUDED_PARTS for part in path.parts)


def _python_metadata(text: str) -> tuple[list[str], list[str]]:
    symbols: set[str] = set()
    imports: set[str] = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [], []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return sorted(symbols), sorted(imports)


def _ownership(relative: str) -> str:
    parts = Path(relative).parts
    if len(parts) >= 3 and parts[:2] == ("backend", "modules"):
        return f"backend.modules.{parts[2]}"
    if len(parts) >= 3 and parts[:2] == ("backend", "core"):
        return f"backend.core.{parts[2]}"
    if parts and parts[0] == "frontend":
        return "frontend"
    if parts and parts[0] == "tools":
        return "tools"
    if parts and parts[0] == "docs":
        return "docs"
    if parts and parts[0] == "memory":
        return "memory"
    return parts[0] if parts else "root"


def scan_repository(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    cfg = validate_request(request)
    evidence: list[dict[str, Any]] = []
    scanned_files = 0
    skipped_sensitive = 0
    terms = cfg["search_terms"]
    table_re = re.compile(r"\bdbo\.([A-Za-z_][A-Za-z0-9_]*)", re.I)
    route_re = re.compile(r"@(?:[A-Za-z_][A-Za-z0-9_]*\.)?(?:get|post|put|patch|delete)\(\s*[\"']([^\"']+)", re.I)
    helper_tokens = ("get_sql_connection", "readonly_sql_connection", "corporate_identity_resolver", "resolver_canonico", "load_catalog_real")
    connection_tokens = ("readonly_sql_connection", "get_sql_connection", "sql_first", "pyodbc", "pymongo", "MongoClient")
    rbac_tokens = ("Usuario_Roles", "Usuario_RolesContexto", "Sistema_RBAC", "RBAC_Permisos", "get_current_user", "menu-permissions")
    scheduler_tokens = ("scheduler_manager", "AsyncIOScheduler", "APScheduler", "scheduler")
    integration_tokens = ("softrestaurant", "mpro", "netpay", "vtiger", "twilio", "sap", "oracle", "dynamics", "bbva", "banorte")

    for requested_root in cfg["paths"]:
        base = (root / requested_root).resolve()
        try:
            base.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError("PATH_OUTSIDE_REPOSITORY") from exc
        if not base.exists():
            continue
        candidates = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for path in candidates:
            try:
                relative = path.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                continue
            if _is_sensitive(Path(relative)):
                skipped_sensitive += 1
                continue
            if cfg["include_patterns"] and not _matches_any(relative, cfg["include_patterns"]):
                continue
            if cfg["exclude_patterns"] and _matches_any(relative, cfg["exclude_patterns"]):
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            scanned_files += 1
            lowered = text.lower()
            path_lower = relative.lower()
            matched_terms = sorted({term for term in terms if term in lowered or term in path_lower})
            if not matched_terms:
                continue
            symbols: list[str] = []
            imports: list[str] = []
            if path.suffix.lower() == ".py":
                symbols, imports = _python_metadata(text)
            routes = sorted(set(route_re.findall(text)))
            tables = sorted(set(table_re.findall(text)))
            record = {
                "path": relative,
                "matched_terms": matched_terms,
                "candidate_ownership": _ownership(relative),
                "symbols": symbols[:200],
                "imports": imports[:200],
                "routes": routes[:200],
                "tables_referenced": tables[:200],
                "helpers": sorted(token for token in helper_tokens if token.lower() in lowered),
                "connections": sorted(token for token in connection_tokens if token.lower() in lowered),
                "rbac_contracts": sorted(token for token in rbac_tokens if token.lower() in lowered),
                "scheduler_contracts": sorted(token for token in scheduler_tokens if token.lower() in lowered),
                "integrations": sorted(token for token in integration_tokens if token.lower() in lowered),
            }
            evidence.append(record)
            if len(evidence) >= cfg["max_results"]:
                return {
                    "status": "PASS",
                    "mode": "READ_ONLY_REPOSITORY",
                    "summary": {"scanned_files": scanned_files, "matched_files": len(evidence), "skipped_sensitive": skipped_sensitive},
                    "truncated": True,
                    "evidence": evidence,
                }
    return {
        "status": "PASS",
        "mode": "READ_ONLY_REPOSITORY",
        "summary": {"scanned_files": scanned_files, "matched_files": len(evidence), "skipped_sensitive": skipped_sensitive},
        "truncated": False,
        "evidence": evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-json", required=True)
    args = parser.parse_args()
    try:
        request = json.loads(args.request_json)
        result = scan_repository(ROOT, request)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": f"{type(exc).__name__}:{exc}"}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
