import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / 'tools' / 'mirror_sync' / 'universal_job_bridge.py'
DISPATCHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_dispatcher.py'

def load_bridge():
    spec = importlib.util.spec_from_file_location('gate6_bridge', BRIDGE)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod

def valid_job():
    q = {'type':'sql_readonly_audit','queries':[{'name':'identity','sql':'SELECT DB_NAME() AS db_name'}]}
    return {
        'schema':'edarsahub.worker-job.v2',
        'job_id':'gate6-test-job',
        'target_repo':'rbalam/EDARSA_HUB',
        'target_branch':'Edarsahub_Desarrollo',
        'production_allowed':False,
        'objective':'test',
        'human_summary_language':'es',
        'mode':'SQL_MIGRATION_DEVELOPMENT',
        'actions':[],
        'migration_path':'backend/database/migrations/20260914_gate6.sql',
        'migration_sha256':'a'*64,
        'confirm_sql_migration':True,
        'preflight_checks':[q],
        'checks':[q],
    }

def test_bridge_accepts_closed_migration_contract():
    mod = load_bridge()
    assert mod.validate(valid_job()) == []

def test_bridge_rejects_inline_sql_and_command():
    mod = load_bridge()
    job = valid_job(); job['sql'] = 'CREATE TABLE x(id int)'; job['command'] = 'sqlcmd'
    errors = mod.validate(job)
    assert 'SQL_MIGRATION_FORBIDDEN_FIELD:sql' in errors
    assert 'SQL_MIGRATION_FORBIDDEN_FIELD:command' in errors

def test_bridge_rejects_noncanonical_path_and_bad_hash():
    mod = load_bridge()
    job = valid_job(); job['migration_path'] = '../evil.sql'; job['migration_sha256'] = 'bad'
    errors = mod.validate(job)
    assert 'SQL_MIGRATION_PATH_INVALID' in errors
    assert 'SQL_MIGRATION_SHA256_INVALID' in errors

def test_bridge_requires_pre_and_post_readonly_audits():
    mod = load_bridge()
    job = valid_job(); job['preflight_checks'] = []; job['checks'] = []
    errors = mod.validate(job)
    assert 'SQL_MIGRATION_PREFLIGHT_REQUIRED' in errors
    assert 'SQL_MIGRATION_POST_AUDIT_REQUIRED' in errors

def test_dispatcher_contract_is_closed_and_ordered():
    text = DISPATCHER.read_text(encoding='utf-8')
    assert 'SQL_MIGRATION_DEVELOPMENT_MODE = "SQL_MIGRATION_DEVELOPMENT"' in text
    block = text.split('if mode == SQL_MIGRATION_DEVELOPMENT_MODE:', 1)[1].split('if mode == MPRO_FULL_HISTORY_MODE:', 1)[0]
    pre = block.index('for check in preflight_checks:')
    migration = block.index('sql_migration_development.py')
    post = block.index('for check in checks:')
    assert pre < migration < post
    assert 'job.get("sql")' not in block
    assert 'job.get("command")' not in block
    assert 'shell=True' not in block
    assert '--migration-path' in block
    assert '--migration-sha256' in block
    assert '--confirm' in block
    assert 'confirm_use_existing_sql_writer' in block
    assert '--allow-canonical-sql-writer' in block
    assert 'use_existing_sql_writer' in block
    assert 'CERTIFIED_OPERATIONAL' in block
    assert 'check_failed:sql_migration_preflight' in block
    assert 'sql_migration_failed:rc=' in block
    assert 'safe_migration_summary' in block
    assert 'result["operation_summary"] = safe_migration_summary' in block
    assert 'MigrationContractError:' in block
    assert 'credential_source' in block
    assert 'check_failed:sql_migration_post_audit' in block

def test_dispatcher_does_not_touch_production_contract():
    text = DISPATCHER.read_text(encoding='utf-8')
    block = text.split('if mode == SQL_MIGRATION_DEVELOPMENT_MODE:', 1)[1].split('if mode == MPRO_FULL_HISTORY_MODE:', 1)[0]
    assert 'Edarsahub_Produccion' not in block
    assert 'production_allowed=True' not in block
