import hashlib
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import tools.mirror_sync.sql_migration_development as mod

def env(user='MigrationWriter'):
    return {'EDARSAHUB_SQL_HOST':'db','EDARSAHUB_SQL_DATABASE':'EDARSAHUB','EDARSAHUB_MIGRATION_USER':user,'EDARSAHUB_MIGRATION_PASSWORD':'secret'}

def make_sql(tmp_path, monkeypatch):
    root=tmp_path/'repo'; migrations=root/'backend'/'database'/'migrations'; migrations.mkdir(parents=True); path=migrations/'001_test.sql'; path.write_text('SELECT 1;\n',encoding='utf-8'); monkeypatch.setattr(mod,'ROOT',root); monkeypatch.setattr(mod,'MIGRATIONS_ROOT',migrations.resolve()); monkeypatch.setattr(mod,'RUNNER',root/'backend'/'tools'/'edarsahub_sql_runner.py'); return path

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def test_path_must_be_under_canonical_migrations(tmp_path,monkeypatch):
    root=tmp_path/'repo'; root.mkdir(); outside=root/'outside.sql'; outside.write_text('SELECT 1'); monkeypatch.setattr(mod,'ROOT',root); monkeypatch.setattr(mod,'MIGRATIONS_ROOT',(root/'backend'/'database'/'migrations').resolve())
    with pytest.raises(mod.MigrationContractError,match='OUTSIDE_CANONICAL_ROOT'): mod.resolve_migration_path(str(outside))

def test_hash_must_match(tmp_path,monkeypatch):
    path=make_sql(tmp_path,monkeypatch)
    with pytest.raises(mod.MigrationContractError,match='SHA256_MISMATCH'): mod.validate_request(migration_path=str(path),migration_sha256='0'*64,confirm=True,production_allowed=False)

def test_confirmation_required(tmp_path,monkeypatch):
    path=make_sql(tmp_path,monkeypatch)
    with pytest.raises(mod.MigrationContractError,match='CONFIRMATION_REQUIRED'): mod.validate_request(migration_path=str(path),migration_sha256=digest(path),confirm=False,production_allowed=False)

def test_production_forbidden(tmp_path,monkeypatch):
    path=make_sql(tmp_path,monkeypatch)
    with pytest.raises(mod.MigrationContractError,match='PRODUCTION_FORBIDDEN'): mod.validate_request(migration_path=str(path),migration_sha256=digest(path),confirm=True,production_allowed=True)

def test_dedicated_credentials_required():
    with pytest.raises(mod.MigrationContractError,match='MIGRATION_CREDENTIALS_REQUIRED'): mod.build_child_env({'EDARSAHUB_SQL_HOST':'db','EDARSAHUB_SQL_DATABASE':'EDARSAHUB'})

def test_hrlectura_forbidden_as_dedicated_writer():
    with pytest.raises(mod.MigrationContractError,match='HRLECTURA_CANNOT_BE_MIGRATION_WRITER'): mod.build_child_env(env('HRLectura'))

def test_expected_dedicated_writer_identity_matches():
    source=env('GptEscritura'); source['EDARSAHUB_MIGRATION_EXPECTED_USER']='GptEscritura'
    child=mod.build_child_env(source); assert child['EDARSAHUB_SQL_USER']=='GptEscritura'; assert child['EDARSAHUB_MIGRATION_CREDENTIAL_SOURCE']=='dedicated'

def test_expected_dedicated_writer_identity_mismatch_fails_closed():
    source=env('OtherWriter'); source['EDARSAHUB_MIGRATION_EXPECTED_USER']='GptEscritura'
    with pytest.raises(mod.MigrationContractError,match='MIGRATION_WRITER_IDENTITY_MISMATCH'): mod.build_child_env(source)

def test_existing_canonical_writer_requires_explicit_opt_in():
    source={'EDARSAHUB_SQL_HOST':'db','EDARSAHUB_SQL_DATABASE':'EDARSAHUB','EDARSAHUB_SQL_USER':'HRLectura','EDARSAHUB_SQL_PASSWORD':'existing'}
    with pytest.raises(mod.MigrationContractError,match='MIGRATION_CREDENTIALS_REQUIRED'): mod.build_child_env(source)

def test_explicit_canonical_writer_reuses_existing_sql_credentials():
    source={'EDARSAHUB_SQL_HOST':'db','EDARSAHUB_SQL_DATABASE':'EDARSAHUB','EDARSAHUB_SQL_USER':'HRLectura','EDARSAHUB_SQL_PASSWORD':'existing'}
    child=mod.build_child_env(source,allow_canonical_sql_writer=True); assert child['EDARSAHUB_SQL_USER']=='HRLectura'; assert child['EDARSAHUB_SQL_PASSWORD']=='existing'; assert child['EDARSAHUB_MIGRATION_CREDENTIAL_SOURCE']=='canonical'; assert child['EDARSAHUB_ALLOW_MIGRATIONS']=='true'

def test_child_env_reuses_host_db_and_overrides_only_credentials():
    source=env(); source['EDARSAHUB_SQL_PORT']='1433'; source['EDARSAHUB_SQL_USER']='HRLectura'; source['EDARSAHUB_SQL_PASSWORD']='readonly'
    child=mod.build_child_env(source); assert child['EDARSAHUB_SQL_HOST']=='db'; assert child['EDARSAHUB_SQL_DATABASE']=='EDARSAHUB'; assert child['EDARSAHUB_SQL_PORT']=='1433'; assert child['EDARSAHUB_SQL_USER']=='MigrationWriter'; assert child['EDARSAHUB_SQL_PASSWORD']=='secret'; assert child['EDARSAHUB_ALLOW_MIGRATIONS']=='true'; assert source['EDARSAHUB_SQL_USER']=='HRLectura'

def test_execute_uses_argv_no_shell(tmp_path,monkeypatch):
    path=make_sql(tmp_path,monkeypatch); runner=mod.RUNNER; runner.parent.mkdir(parents=True); runner.write_text('x',encoding='utf-8'); calls=[]
    class R: returncode=0; stdout='ok'
    def fake_run(args,**kwargs): calls.append((args,kwargs)); return R()
    monkeypatch.setattr(mod.subprocess,'run',fake_run); result=mod.execute_migration(migration_path=str(path),migration_sha256=digest(path),confirm=True,production_allowed=False,source_env=env()); assert result['status']=='PASS'; assert len(calls)==1; assert calls[0][1]['shell'] is False; assert calls[0][0][2:4]==['--mode','migrate']; assert calls[0][1]['env']['EDARSAHUB_SQL_USER']=='MigrationWriter'
