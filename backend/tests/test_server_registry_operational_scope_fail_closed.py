from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "backend" / "core" / "server_registry.py"
SCOPE = ROOT / "backend" / "core" / "connections" / "operational_scope.py"


def test_operational_scope_exposes_single_refresh_server_set():
    text = SCOPE.read_text(encoding="utf-8")
    assert "def operational_server_ids()" in text
    assert "UnidadesService.get_all(force_refresh=True)" in text


def test_operational_server_list_fails_closed_without_scope():
    text = REGISTRY.read_text(encoding="utf-8")
    block = text.split("def list_operational_servers(", 1)[1].split(
        "def get_visible_servers_for_operaciones(", 1
    )[0]
    assert "scoped_ids = operational_server_ids()" in block
    assert "in scoped_ids" in block


def test_visible_operational_list_requires_flag_and_scope():
    text = REGISTRY.read_text(encoding="utf-8")
    block = text.split("def get_visible_servers_for_operaciones(", 1)[1].split(
        "def get_connection_config(", 1
    )[0]
    assert "scoped_ids = operational_server_ids()" in block
    assert "visible_en_operaciones" in block
    assert "in scoped_ids" in block
