from __future__ import annotations

import ast
from pathlib import Path
import unittest


BACKEND_PATH = Path(__file__).resolve().parents[1]

ROUTES_PATH = (
    BACKEND_PATH
    / "modules"
    / "comercial_v2"
    / "routes.py"
)

REPOSITORY_PATH = (
    BACKEND_PATH
    / "modules"
    / "comercial_v2"
    / "repository_readonly.py"
)

LEGACY_SQL = "SUM(ISNULL(ventas_sin_propina, 0)) as ventas"
CANONICAL_SQL = "SUM(ISNULL(ventas_total, 0)) as ventas"


def function_source(path: Path, function_name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    matches = [
        node
        for node in tree.body
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
        and node.name == function_name
    ]

    if len(matches) != 1:
        raise AssertionError(
            f"{function_name}: se localizaron {len(matches)} funciones"
        )

    segment = ast.get_source_segment(source, matches[0])

    if segment is None:
        raise AssertionError(
            f"No fue posible extraer {function_name}"
        )

    return segment


class VisibleSalesBasisTests(unittest.TestCase):
    def test_comparativos_por_unidad_usan_ventas_total(self):
        source = function_source(
            ROUTES_PATH,
            "_get_variaciones_comparativas",
        )

        self.assertEqual(
            source.count(CANONICAL_SQL),
            3,
        )
        self.assertNotIn(LEGACY_SQL, source)

    def test_comparativos_totales_usan_ventas_total(self):
        source = function_source(
            ROUTES_PATH,
            "_calcular_totales_variaciones",
        )

        self.assertEqual(
            source.count(CANONICAL_SQL),
            2,
        )
        self.assertNotIn(LEGACY_SQL, source)
        self.assertIn(
            "totales_actual.get('ventas_total')",
            source,
        )

    def test_documentacion_declara_ventas_visibles_con_iva(self):
        source = REPOSITORY_PATH.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "KPI visible de ventas = ventas_total "
            "con IVA incluido",
            source,
        )

        self.assertNotIn(
            "KPI de ventas = ventas_sin_propina",
            source,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
