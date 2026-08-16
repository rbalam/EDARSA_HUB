import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

ROUTER = (
    ROOT
    / "backend/modules/comercial/"
      "routes_precios_sugeridos.py"
)

SERVICE = (
    ROOT
    / "backend/modules/comercial/services/"
      "precios_sugeridos_consolidado_service.py"
)


def _source(path):
    return path.read_text(encoding="utf-8")


def _function_source(path, name):
    text = _source(path)
    tree = ast.parse(text)

    matches = [
        n
        for n in ast.walk(tree)
        if isinstance(
            n,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and n.name == name
    ]

    assert len(matches) == 1

    return ast.get_source_segment(
        text,
        matches[0],
    )


def test_router_resuelve_configuracion_efectiva():
    source = _function_source(
        ROUTER,
        "get_precios_sugeridos",
    )

    assert "resolve_authorized_unidad_scope(" in source
    assert "scope.unidad_pk" in source
    assert "resolver_configuracion_efectiva(" in source
    assert "multiplo_redondeo" in source
    assert "metodo_redondeo" in source
    assert "REDONDEO_NO_CONFIGURADO" in source


def test_service_recibe_redondeo_resuelto():
    source = _function_source(
        SERVICE,
        "obtener_precios_sugeridos",
    )

    assert "multiplo_redondeo" in source
    assert "metodo_redondeo" in source
    assert (
        "REDONDEO_EFECTIVO_NO_CONFIGURADO"
        in source
    )


def test_no_quedan_round5_en_motor():
    source = _source(SERVICE)

    assert "round(precio_sugerido / 5) * 5" not in source
    assert "round(precio_minimo / 5) * 5" not in source


def test_service_usa_primitiva_canonica():
    source = _source(SERVICE)

    assert (
        "from modules.costos_margenes.redondeo import ("
        in source
    )

    assert source.count(
        "redondear_a_multiplo("
    ) >= 2


def test_vinos_rangos_permanece():
    source = _source(SERVICE)

    assert "VINOS_RANGOS_MX" in source
    assert "MargenMultiplicador" in source
    assert (
        "precio_sugerido = costo_botella * multiplicador"
        in source
    )


def test_redondeo_no_reintroduce_margen_legacy():
    source = _source(SERVICE)

    assert "margen_objetivo: float = 0.35" not in source
    assert "costo_receta / (1 - margen_objetivo)" not in source
    assert ") < 20" not in source
    assert "<20" not in source
    assert "_margen_efectivo" in source
    assert "redondear_a_multiplo(" in source


def test_no_default_redondeo_en_signature():
    source = _function_source(
        SERVICE,
        "obtener_precios_sugeridos",
    )

    assert "multiplo_redondeo=5" not in source
    assert 'metodo_redondeo="MAS_CERCANO"' not in source
    assert "metodo_redondeo='MAS_CERCANO'" not in source
