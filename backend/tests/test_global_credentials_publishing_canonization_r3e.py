from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = [
    ROOT / '.github/workflows/communications-gate5d-development-migration.yml',
    ROOT / '.github/workflows/catalogo-ampliado-gate8f-development-migration.yml',
    ROOT / '.github/workflows/cavas-corporativas-menu-development-migration.yml',
    ROOT / '.github/workflows/cavas-gate12i-persona-link-development-migration.yml',
]

def test_active_workflows_use_only_readonly_canonical_secret_and_fail_closed():
    for path in WORKFLOWS:
        text = path.read_text(encoding='utf-8')
        assert 'EDARSAHUB_SQL_MIGRATION_USER' not in text
        assert 'EDARSAHUB_SQL_MIGRATION_PASSWORD' not in text
        assert 'MIGRATION_WRITER_STATUS=UNCONFIGURED' in text
        assert 'HRLECTURA_WRITER_FORBIDDEN=YES' in text
        assert 'MIGRATION_EXECUTED=NO' in text
        assert 'secrets.EDARSAHUB_SQL_PASSWORD' in text
        assert "EDARSAHUB_ALLOW_MIGRATIONS: 'false'" in text
