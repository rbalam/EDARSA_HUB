from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADAPTERS = ROOT / "backend" / "modules" / "comercial" / "adapters.py"
ENV_DOC = ROOT / "docs" / "DEPLOYMENT_ENV_VARS.md"
DIAG_DOC = ROOT / "docs" / "DIAGNOSTICO_SQL_SUCURSALES.md"
GENERATOR = ROOT / "backend" / "scripts" / "generar_doc_diagnostico.py"


def test_mpro_runtime_key_has_no_default_fallback():
    source = ADAPTERS.read_text(encoding="utf-8")
    assert 'os.environ.get("API_MPRO_KEY",' not in source
    assert source.count('os.environ.get("API_MPRO_KEY")') >= 3


def test_mpro_docs_use_secret_placeholder_or_environment_reference():
    env_doc = ENV_DOC.read_text(encoding="utf-8")
    diag_doc = DIAG_DOC.read_text(encoding="utf-8")
    generator = GENERATOR.read_text(encoding="utf-8")
    assert "API_MPRO_KEY=[CONFIGURAR_EN_SECRET_STORE]" in env_doc
    assert diag_doc.count("x-api-key: ${API_MPRO_KEY}") == 2
    assert generator.count("x-api-key: ${API_MPRO_KEY}") == 2
