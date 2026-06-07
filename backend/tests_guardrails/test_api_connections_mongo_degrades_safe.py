import asyncio
import inspect
from modules.api_connections import repository


def test_repository_has_no_mongo_remaining():
    src = inspect.getsource(repository)
    assert "get_mongo_db" not in src
    assert "api_connections_cache" not in src
    assert "api_health_logs" not in src


def test_repository_keeps_sql_first_exports():
    async def _run():
        assert hasattr(repository, "create_api_connection")
        assert hasattr(repository, "update_api_connection")
        assert hasattr(repository, "delete_api_connection")
    asyncio.run(_run())
