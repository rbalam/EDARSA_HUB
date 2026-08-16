from pathlib import Path
import ast
import importlib


ROOT = Path("/app")

COST_ROOT = (
    ROOT / "backend/modules/costos_margenes"
)

COMMERCIAL_SERVICE = (
    ROOT
    / "backend/modules/comercial/alertas_margen_service.py"
)

COMMERCIAL_REPO = (
    ROOT
    / "backend/modules/comercial/alertas_margen_repository.py"
)

CANONICAL_SERVICE = (
    COST_ROOT / "reglas_margen_service.py"
)

CANONICAL_REPO = (
    COST_ROOT / "reglas_margen_repository.py"
)


def _imports(path):
    source = path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    result = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                result.append(node.module)

        elif isinstance(node, ast.Import):
            result.extend(
                alias.name
                for alias in node.names
            )

    return result


def test_costos_no_depende_de_comercial():
    edges = []

    for path in COST_ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        for module in _imports(path):
            if module.startswith(
                "modules.comercial"
            ):
                edges.append(
                    (
                        str(path),
                        module,
                    )
                )

    assert edges == []


def test_service_canonico_esta_en_costos():
    assert CANONICAL_SERVICE.is_file()

    imports = _imports(
        CANONICAL_SERVICE
    )

    assert (
        "modules.costos_margenes."
        "configuracion_repository"
        in imports
    )

    assert (
        "modules.costos_margenes."
        "reglas_margen_repository"
        in imports
    )


def test_repository_canonico_esta_en_costos():
    assert CANONICAL_REPO.is_file()

    imports = _imports(
        CANONICAL_REPO
    )

    assert not any(
        module.startswith(
            "modules.comercial"
        )
        for module in imports
    )


def test_comercial_service_es_solo_adaptador():
    source = COMMERCIAL_SERVICE.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    functions = [
        node.name
        for node in tree.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
    ]

    assert functions == []

    assert (
        "modules.costos_margenes."
        "reglas_margen_service"
        in source
    )


def test_comercial_repository_es_solo_adaptador():
    source = COMMERCIAL_REPO.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    functions = [
        node.name
        for node in tree.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
    ]

    assert functions == []

    assert (
        "modules.costos_margenes."
        "reglas_margen_repository"
        in source
    )


def test_import_canonical_service():
    module = importlib.import_module(
        "modules.costos_margenes."
        "reglas_margen_service"
    )

    assert callable(
        module.resolver_margen_esperado
    )

    assert callable(
        module.resolver_margenes_esperados_batch
    )


def test_legacy_service_path_sigue_funcionando():
    module = importlib.import_module(
        "modules.comercial."
        "alertas_margen_service"
    )

    assert callable(
        module.resolver_margen_esperado
    )

    assert callable(
        module.resolver_margenes_esperados_batch
    )


def test_lazy_router_compatibility():
    module = importlib.import_module(
        "modules.costos_margenes"
    )

    router = module.router

    assert router is not None
