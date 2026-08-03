from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from modules.comercial_v2.mappers import (
    map_mpro_ventas_cerradas,
    map_softrestaurant_ventas_cerradas,
)


def _config():
    return SimpleNamespace(
        unidad_negocio_pk="TEST",
        unidad_negocio_nombre="TEST",
        server_id="TEST-SERVER",
        sucursal_id="DEFAULT",
        sucursal_nombre="TEST",
    )


def test_soft_excluye_propina():
    kpi = map_softrestaurant_ventas_cerradas(
        {
            "fecha": "2026-08-01",
            "ventas_total": Decimal("100.00"),
            "propinas": Decimal("15.00"),
            "num_cheques": 2,
            "num_personas": 4,
        },
        _config(),
        "TEST-SOFT",
    )

    assert kpi.ventas_total == Decimal("85.00")
    assert kpi.ventas_sin_propina == Decimal("85.00")
    assert kpi.propinas_total == Decimal("15.00")


def test_mpro_conserva_venta_neta():
    kpi = map_mpro_ventas_cerradas(
        {
            "fecha": "2026-08-01",
            "Vn_Precio_Neto_Importe": Decimal("100.00"),
            "propinas": Decimal("15.00"),
            "num_folios": 2,
            "total_personas": 4,
        },
        _config(),
        "TEST-MPRO",
    )

    assert kpi.ventas_total == Decimal("100.00")
    assert kpi.ventas_sin_propina == Decimal("100.00")
    assert kpi.propinas_total == Decimal("15.00")


def test_repositorio_persiste_campo_canonico():
    text = Path(
        "/app/backend/modules/comercial_v2/"
        "repository_comercial_edarsahub.py"
    ).read_text(encoding="utf-8")

    assert "ventas_sin_propina = {ventas_sin_propina}" in text
    assert "ventas_total, ventas_sin_propina," in text
    assert "{kpi.ventas_total}, {ventas_sin_propina}," in text
