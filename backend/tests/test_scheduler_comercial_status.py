import ast
from pathlib import Path


SCHEDULER_PATH = (
    Path(__file__).resolve().parents[1]
    / "core"
    / "scheduler"
    / "scheduler_manager.py"
)


def _load_normalizer():
    source = SCHEDULER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    node = next(
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef)
        and item.name == "_normalize_comercial_sync_status"
    )

    module = ast.Module(
        body=[node],
        type_ignores=[],
    )

    namespace = {}
    exec(
        compile(
            module,
            str(SCHEDULER_PATH),
            "exec",
        ),
        namespace,
    )

    return namespace["_normalize_comercial_sync_status"]


def test_normaliza_estados_comercial_v2():
    normalize = _load_normalizer()

    assert normalize("COMPLETADO") == "success"
    assert normalize("SUCCESS") == "success"
    assert normalize("PARCIAL") == "partial"
    assert normalize("FALLIDO") == "failed"
    assert normalize(None) == "failed"
    assert normalize("DESCONOCIDO") == "failed"


def test_wrapper_usa_normalizador():
    source = SCHEDULER_PATH.read_text(encoding="utf-8")

    assert (
        "_normalize_comercial_sync_status("
        in source
    )

    assert (
        'result.get("estatus_general")'
        in source
    )
