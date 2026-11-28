#!/usr/bin/env python3
"""Controlled EDARSAHUB Development SQL migration wrapper.

This module never accepts inline SQL. It executes only a versioned migration
file under backend/database/migrations with an exact SHA-256 and dedicated
migration credentials injected only into the child process.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_ROOT = (ROOT / 'backend' / 'database' / 'migrations').resolve()
RUNNER = (ROOT / 'backend' / 'tools' / 'edarsahub_sql_runner.py').resolve()
RUNTIME_PYTHON = Path('/root/.venv/bin/python')

class MigrationContractError(RuntimeError):
    pass

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def resolve_migration_path(raw: str) -> Path:
    candidate = (ROOT / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    if candidate.suffix.lower() != '.sql':
        raise MigrationContractError('MIGRATION_SQL_FILE_REQUIRED')
    if candidate == MIGRATIONS_ROOT or MIGRATIONS_ROOT not in candidate.parents:
        raise MigrationContractError('MIGRATION_PATH_OUTSIDE_CANONICAL_ROOT')
    if not candidate.is_file():
        raise MigrationContractError('MIGRATION_FILE_NOT_FOUND')
    return candidate

def validate_request(*, migration_path: str, migration_sha256: str, confirm: bool, production_allowed: bool) -> Path:
    if production_allowed is not False:
        raise MigrationContractError('PRODUCTION_FORBIDDEN')
    if confirm is not True:
        raise MigrationContractError('MIGRATION_CONFIRMATION_REQUIRED')
    if len(migration_sha256) != 64 or any(ch not in '0123456789abcdef' for ch in migration_sha256.lower()):
        raise MigrationContractError('INVALID_MIGRATION_SHA256')
    path = resolve_migration_path(migration_path)
    actual = sha256_file(path)
    if actual != migration_sha256.lower():
        raise MigrationContractError('MIGRATION_SHA256_MISMATCH')
    return path

def build_child_env(source_env: dict[str, str] | None = None, *, allow_canonical_sql_writer: bool = False) -> dict[str, str]:
    source = dict(source_env or os.environ)
    dedicated_user = str(source.get('EDARSAHUB_MIGRATION_USER') or '').strip()
    dedicated_password = str(source.get('EDARSAHUB_MIGRATION_PASSWORD') or '')
    expected_user = str(source.get('EDARSAHUB_MIGRATION_EXPECTED_USER') or '').strip()
    if bool(dedicated_user) != bool(dedicated_password):
        raise MigrationContractError('MIGRATION_CREDENTIALS_INCOMPLETE')
    selected_source = 'dedicated'
    if dedicated_user and dedicated_password:
        user, password = dedicated_user, dedicated_password
    elif allow_canonical_sql_writer:
        selected_source = 'canonical'
        user = str(source.get('EDARSAHUB_SQL_USER') or '').strip()
        password = str(source.get('EDARSAHUB_SQL_PASSWORD') or '')
        if not user or not password:
            raise MigrationContractError('CANONICAL_SQL_WRITER_CREDENTIALS_REQUIRED')
    else:
        raise MigrationContractError('MIGRATION_CREDENTIALS_REQUIRED')
    if selected_source == 'dedicated' and user.lower() == 'hrlectura':
        raise MigrationContractError('HRLECTURA_CANNOT_BE_MIGRATION_WRITER')
    if selected_source == 'dedicated' and expected_user and user != expected_user:
        raise MigrationContractError('MIGRATION_WRITER_IDENTITY_MISMATCH')
    for required in ('EDARSAHUB_SQL_HOST','EDARSAHUB_SQL_DATABASE'):
        if not str(source.get(required) or '').strip():
            raise MigrationContractError(f'CANONICAL_SQL_CONFIG_REQUIRED:{required}')
    child = dict(source)
    child['EDARSAHUB_SQL_USER'] = user
    child['EDARSAHUB_SQL_PASSWORD'] = password
    child['EDARSAHUB_ALLOW_MIGRATIONS'] = 'true'
    child['EDARSAHUB_MIGRATION_CREDENTIAL_SOURCE'] = selected_source
    return child

def execute_migration(*, migration_path: str, migration_sha256: str, confirm: bool, production_allowed: bool, source_env: dict[str,str] | None = None, allow_canonical_sql_writer: bool = False) -> dict[str, Any]:
    path = validate_request(migration_path=migration_path, migration_sha256=migration_sha256, confirm=confirm, production_allowed=production_allowed)
    if not RUNNER.is_file():
        raise MigrationContractError('CANONICAL_SQL_RUNNER_NOT_FOUND')
    env = build_child_env(source_env, allow_canonical_sql_writer=allow_canonical_sql_writer)
    python_bin = str(RUNTIME_PYTHON if RUNTIME_PYTHON.is_file() else Path(os.sys.executable))
    result = subprocess.run([python_bin, str(RUNNER), '--mode', 'migrate', '--script', str(path)], cwd=str(ROOT), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False, check=False)
    return {
        'status': 'PASS' if result.returncode == 0 else 'FAIL',
        'returncode': result.returncode,
        'migration_path': str(path.relative_to(ROOT)),
        'migration_sha256': migration_sha256.lower(),
        'credential_source': env.get('EDARSAHUB_MIGRATION_CREDENTIAL_SOURCE'),
        'production_touched': False,
        'output': (result.stdout or '')[-8000:],
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--migration-path', required=True)
    parser.add_argument('--migration-sha256', required=True)
    parser.add_argument('--confirm', action='store_true')
    parser.add_argument('--allow-canonical-sql-writer', action='store_true')
    parser.add_argument('--production-allowed', action='store_true')
    args = parser.parse_args()
    try:
        payload = execute_migration(migration_path=args.migration_path, migration_sha256=args.migration_sha256, confirm=args.confirm, production_allowed=args.production_allowed, allow_canonical_sql_writer=args.allow_canonical_sql_writer)
    except Exception as exc:
        print(json.dumps({'status':'FAIL','error':type(exc).__name__ + ':' + str(exc),'production_touched':False}, ensure_ascii=False))
        return 1
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload['status'] == 'PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())
