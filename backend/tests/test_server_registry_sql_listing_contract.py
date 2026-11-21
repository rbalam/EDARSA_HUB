from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "backend/core/server_registry.py"


def test_sql_server_registry_excludes_api_local_from_generic_servers_listing():
    source = REGISTRY.read_text(encoding="utf-8")
    assert 'conditions.append("(tipo_conexion != \'API_LOCAL\' OR tipo_conexion IS NULL)")' in source
    assert "R10A: El listado administrativo debe incluir API_LOCAL" not in source
