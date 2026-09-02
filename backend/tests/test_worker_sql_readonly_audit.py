from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / 'tools' / 'mirror_sync' / 'sql_readonly_audit.py'
BRIDGE = ROOT / 'tools' / 'mirror_sync' / 'universal_job_bridge.py'
DISPATCHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_dispatcher.py'

def load_helper():
    spec = importlib.util.spec_from_file_location('worker_sql_readonly_audit', HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_readonly_validator_accepts_select_and_with():
    m = load_helper()
    assert m.validate_readonly_sql('SELECT TOP 1 name FROM sys.tables')
    assert m.validate_readonly_sql('WITH x AS (SELECT 1 AS n) SELECT n FROM x;')

def test_readonly_validator_rejects_mutation_and_multistatement():
    m = load_helper()
    blocked = [
        'INSERT INTO x VALUES (1)',
        'UPDATE x SET a=1',
        'DELETE FROM x',
        'MERGE x USING y ON 1=1 WHEN MATCHED THEN UPDATE SET a=1;',
        'EXEC sp_who',
        'CREATE TABLE x(a int)',
        'ALTER TABLE x ADD b int',
        'DROP TABLE x',
        'TRUNCATE TABLE x',
        'SELECT * INTO x FROM sys.tables',
        'SELECT 1; SELECT 2',
        'WITH x AS (SELECT 1 n) UPDATE t SET a=1',
    ]
    for sql in blocked:
        try:
            m.validate_readonly_sql(sql)
        except ValueError:
            pass
        else:
            raise AssertionError(sql)

def test_worker_contract_exposes_readonly_mode_without_shell_execution():
    bridge = BRIDGE.read_text(encoding='utf-8')
    dispatcher = DISPATCHER.read_text(encoding='utf-8')
    assert 'sql_readonly_audit' in bridge
    assert 'READ_ONLY_SQL_ACTIONS_FORBIDDEN' in bridge
    assert 'READ_ONLY_SQL_ONLY_AUDIT_CHECKS_ALLOWED' in bridge
    assert 'sql_readonly_audit' in dispatcher
    assert 'READ_ONLY_COMPLETE' in dispatcher
    assert 'readonly_sql_connection' in HELPER.read_text(encoding='utf-8')
    assert 'shell=True' not in dispatcher

def test_worker_python_precedence_is_repo_venv_then_sys_executable():
    dispatcher = DISPATCHER.read_text(encoding='utf-8')
    resolver = dispatcher.split('def resolve_canonical_python()', 1)[1].split('PYTHON_BIN =', 1)[0]
    assert 'ROOT / ".venv" / "bin" / "python"' in resolver
    assert 'return sys.executable' in resolver
    assert '/root/.venv/bin/python' not in resolver
