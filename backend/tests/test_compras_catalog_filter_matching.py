import ast
from pathlib import Path


SERVER = (
    Path(__file__).resolve().parents[2]
    / "backend/server.py"
)


def _helper_source():
    text = SERVER.read_text(
        encoding="utf-8",
    )

    tree = ast.parse(text)
    lines = text.splitlines()

    nodes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "_matches_filter_set"
    ]

    assert len(nodes) == 1

    node = nodes[0]

    return "\n".join(
        lines[node.lineno - 1:node.end_lineno]
    )


def _build_helper():
    source = _helper_source()

    # La funcion esta anidada en server.py.
    # Se normaliza solo indentacion para probar
    # exactamente su cuerpo productivo.
    first = source.splitlines()[0]
    indent = len(first) - len(first.lstrip())

    normalized = "\n".join(
        line[indent:]
        if len(line) >= indent
        else line
        for line in source.splitlines()
    )

    namespace = {
        "_as_text": lambda value: (
            str(value).strip()
            if value is not None
            else ""
        )
    }

    exec(
        normalized,
        namespace,
    )

    return namespace["_matches_filter_set"]


def test_matches_exact_code():
    fn = _build_helper()

    assert fn(
        "12",
        "Bebidas",
        {"12"},
    )


def test_matches_name():
    fn = _build_helper()

    assert fn(
        "999",
        "Bebidas",
        {"BEBIDAS"},
    )


def test_matches_numeric_code_variants():
    fn = _build_helper()

    for selected in (
        {"1"},
        {"01"},
        {"001"},
        {"0001"},
    ):
        assert fn(
            "0001",
            "Categoria X",
            selected,
        )


def test_rejects_unrelated_filter():
    fn = _build_helper()

    assert not fn(
        "12",
        "Bebidas",
        {"99"},
    )


def test_empty_filter_allows_value():
    fn = _build_helper()

    assert fn(
        "12",
        "Bebidas",
        set(),
    )


def test_three_catalog_filters_use_helper():
    text = SERVER.read_text(
        encoding="utf-8",
    )

    expected = (
        (
            "CategoriaCodigo",
            "Categoria",
            "selected_categoria_codes",
        ),
        (
            "FamiliaCodigo",
            "Familia",
            "selected_familia_codes",
        ),
        (
            "SubFamiliaCodigo",
            "SubFamilia",
            "selected_subfamilia_codes",
        ),
    )

    for code, name, selected in expected:
        needle = (
            f"_matches_filter_set("
            f"prod.get('{code}'), "
            f"prod.get('{name}'), "
            f"{selected})"
        )

        assert needle in text
