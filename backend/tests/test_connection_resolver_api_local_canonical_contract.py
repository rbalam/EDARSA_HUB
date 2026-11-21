from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESOLVER = ROOT / "backend" / "core" / "connection_resolver.py"


def _text():
    return RESOLVER.read_text(encoding="utf-8")


def test_api_local_resolution_does_not_match_legacy_host_or_url_substrings():
    text = _text()

    assert "host = %s OR api_url LIKE %s" not in text
    assert "api_url LIKE %s" not in text
    assert "self._get_api_config(server_config.get('host'" not in text


def test_api_local_resolution_uses_canonical_company_role_and_server_id():
    text = _text()

    assert "Sistema_EmpresasServidores" in text
    assert "ses.ServidorID = %s" in text
    assert '"VENTAS_DIA_API_LOCAL"' in text
    assert "get_connection_for_role(" in text
    assert "WHERE id = %s" in text
    assert "tipo_conexion = 'API_LOCAL'" in text


def test_resolved_api_url_comes_from_canonical_api_url_field():
    text = _text()

    assert '"api_url": api_url' in text
    assert '"api_base_url": api_url' in text
    assert "api_base_url=api_config.get('api_url')" in text
