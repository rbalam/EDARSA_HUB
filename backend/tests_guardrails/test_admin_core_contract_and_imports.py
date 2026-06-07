from pathlib import Path
import importlib.util

API_FILE = Path("/app/backend/api/admin_core_connections.py")


def test_admin_core_import_source_is_correct():
    txt = API_FILE.read_text(encoding="utf-8", errors="ignore")
    assert "from core.db import execute_sql_query, get_mongo_db" not in txt, \
        "No debe volver el import roto get_mongo_db desde core.db"
    # P5-3B-2: get_mongo_db retirado por completo del admin (NO-MONGO end-state)
    assert "get_mongo_db" not in txt, \
        "Admin CORE no debe referenciar get_mongo_db (sunset Mongo completado)"


def test_admin_core_router_defines_expected_routes():
    txt = API_FILE.read_text(encoding="utf-8", errors="ignore")
    assert '@router.get("")' in txt or "@router.get('')" in txt
    assert '@router.get("/{server_id}")' in txt or "@router.get('/{server_id}')" in txt
    assert '@router.post("/{server_id}/test")' in txt or "@router.post('/{server_id}/test')" in txt


def test_admin_core_module_imports_cleanly():
    spec = importlib.util.spec_from_file_location("admin_core_connections", str(API_FILE))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    assert hasattr(mod, "router")
