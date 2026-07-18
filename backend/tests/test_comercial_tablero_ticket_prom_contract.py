"""Contrato estatico para ticket_prom del tablero comercial legacy."""
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
SERVICE = BACKEND / "modules/comercial/service.py"
ROUTES = BACKEND / "modules/comercial/routes.py"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_service_ticket_prom_es_alias_de_cheque_promedio():
    source = _source(SERVICE)

    assert "ticket_prom = round(ventas / pax, 2)" not in source
    assert "ticket_prom = round(ventas_total / pax_total, 2)" not in source
    assert source.count(
        "ticket_prom = round(ventas / cheques, 2)"
    ) >= 4
    assert (
        "ticket_prom = round(ventas_total / cheques_total, 2)"
        in source
    )


def test_routes_totales_ticket_prom_es_alias_de_cheque_promedio():
    source = _source(ROUTES)

    assert (
        'totales["ticket_prom"] = round(totales["ventas"] / '
        'totales["pax"], 2)'
    ) not in source
    assert (
        'totales["ticket_prom"] = round(totales["ventas"] / '
        'totales["cheques"], 2)'
    ) in source
