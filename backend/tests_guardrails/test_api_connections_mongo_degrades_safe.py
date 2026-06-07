import asyncio
from modules.api_connections import repository


def test_repository_file_no_direct_core_db_get_mongo_import():
    import inspect
    src = inspect.getsource(repository)
    assert "from core.db import get_mongo_db" not in src


def test_repository_still_contains_mongo_guards():
    import inspect
    src = inspect.getsource(repository)
    assert "if db is None" in src or "if db is not None" in src


async def _run():
    assert hasattr(repository, "create_api_connection")
    assert hasattr(repository, "update_api_connection")
    assert hasattr(repository, "delete_api_connection")


def test_repository_module_loads_and_exports():
    asyncio.run(_run())
