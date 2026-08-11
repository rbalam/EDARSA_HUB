import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

AUDITORIA = ROOT / "backend/core/auditoria.py"
API_REPOSITORY = (
    ROOT
    / "backend/modules/api_connections/repository.py"
)
API_ROUTES = (
    ROOT
    / "backend/modules/api_connections/routes.py"
)


FORBIDDEN_DRIVER_TOKENS = (
    "pymongo",
    "motor",
    "MongoClient",
    "AsyncIOMotorClient",
)

FORBIDDEN_IO_CALLS = {
    "insert_one",
    "insert_many",
    "update_one",
    "update_many",
    "find",
    "find_one",
    "delete_one",
    "delete_many",
}


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _function_names(path: Path):
    tree = ast.parse(_source(path))

    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    }


def _calls(path: Path):
    tree = ast.parse(_source(path))
    result = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        if isinstance(node.func, ast.Name):
            result.append(node.func.id)

        elif isinstance(node.func, ast.Attribute):
            result.append(node.func.attr)

    return result


def test_dead_auditoria_mongo_helpers_are_absent():
    names = _function_names(AUDITORIA)

    assert "to_mongo_doc" not in names
    assert "_get_mongo_db" not in names
    assert "_guardar_mongo" not in names


def test_api_private_mongo_cache_helper_is_absent():
    names = _function_names(API_REPOSITORY)

    assert "_sync_to_mongo_cache" not in names


def test_no_real_mongo_drivers_or_io():
    for path in (
        AUDITORIA,
        API_REPOSITORY,
    ):
        text = _source(path)

        for token in FORBIDDEN_DRIVER_TOKENS:
            assert token not in text

        assert not (
            set(_calls(path))
            & FORBIDDEN_IO_CALLS
        )


def test_api_sync_compatibility_is_sql_only():
    text = _source(API_REPOSITORY)

    assert (
        "async def sync_all_to_mongo_cache"
        in text
    )

    assert "_sync_to_mongo_cache(" not in text

    assert '"errors": 0' in text
    assert '"synced": total' in text
    assert '"total": total' in text


def test_sync_cache_route_declares_sql_canonical():
    text = _source(API_ROUTES)

    assert '@router.post("/sync-cache")' in text

    assert (
        "Conexiones API verificadas en EDARSAHUB SQL"
        in text
    )

    assert (
        "Sincronización EDARSAHUB SQL → MongoDB completada"
        not in text
    )


def test_legacy_sql_column_names_are_not_mongo_runtime():
    audit = _source(AUDITORIA)

    # PayloadMongo es una columna SQL histórica.
    # Su nombre no constituye dependencia Mongo runtime.
    assert "PayloadMongo" in audit

    assert "pymongo" not in audit
    assert "motor" not in audit
