from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / 'tools' / 'mirror_sync' / 'sql_readonly_audit.py'
DISPATCHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_dispatcher.py'

def load_helper():
    spec = importlib.util.spec_from_file_location('worker_pos_sql_readonly_audit', HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_pos_readonly_reuses_canonical_resolver_and_connection_factory():
    text = HELPER.read_text(encoding='utf-8')
    assert 'list_pos_runtime_contexts' in text
    assert 'get_external_sql_connection' in text
    assert 'PosRuntimeResolver+get_external_sql_connection' in text
    assert "choices=['EDARSAHUB', 'POS']" in text

def test_pos_readonly_has_no_job_supplied_connection_or_shell_contract():
    text = HELPER.read_text(encoding='utf-8')
    dispatcher = DISPATCHER.read_text(encoding='utf-8')
    for option in ('--host', '--database', '--username', '--password', '--command', '--path'):
        assert option not in text
    assert 'shell=True' not in dispatcher
    assert '--units-json' in dispatcher
    assert '--system-types-json' in dispatcher

def test_pos_readonly_rejects_mutation_sql_before_connection():
    helper = load_helper()
    for sql in ('UPDATE x SET a=1', 'DELETE FROM x', 'EXEC sp_who', 'SELECT * INTO x FROM y'):
        try:
            helper.validate_readonly_sql(sql)
        except ValueError:
            pass
        else:
            raise AssertionError(sql)
