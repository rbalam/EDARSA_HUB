from __future__ import annotations

import pytest

from modules.finanzas import (
    canonical_sync_units as module,
)


def _row(
    *,
    pk,
    code,
    name,
    server,
    branch,
    unit_system,
    server_system,
):
    return {
        "unidad_negocio_pk": pk,
        "unidad_negocio_codigo": code,
        "unidad_negocio_nombre": name,
        "server_id": server,
        "sucursal_origen_id": branch,
        "unidad_system_type": unit_system,
        "servidor_system_type": server_system,
        "unidad_activo": 1,
        "servidor_activo": 1,
    }


def test_filtra_por_system_type_canonico(
    monkeypatch,
):
    rows = [
        _row(
            pk="u1",
            code="U-M",
            name="Unidad M",
            server="s1",
            branch="001",
            unit_system="MPRO",
            server_system="MANAGEMENTPRO",
        ),
        _row(
            pk="u2",
            code="U-S",
            name="Unidad S",
            server="s2",
            branch=None,
            unit_system="SoftRestaurant",
            server_system="SOFTRESTAURANT_PRO",
        ),
    ]

    monkeypatch.setattr(
        module,
        "fetch_all_dict_readonly",
        lambda sql: rows,
    )

    assert (
        module.get_canonical_finance_sync_unit_names(
            "MPRO"
        )
        == ("Unidad M",)
    )

    assert (
        module.get_canonical_finance_sync_unit_names(
            "SOFTRESTAURANT"
        )
        == ("Unidad S",)
    )


def test_mpro_sin_sucursal_falla_cerrado(
    monkeypatch,
):
    monkeypatch.setattr(
        module,
        "fetch_all_dict_readonly",
        lambda sql: [
            _row(
                pk="u1",
                code="U-M",
                name="Unidad M",
                server="s1",
                branch=None,
                unit_system="MPRO",
                server_system="MPRO",
            )
        ],
    )

    with pytest.raises(
        module.FinanzasCanonicalUnitError
    ):
        module.get_canonical_finance_sync_units(
            "MPRO"
        )


def test_conflicto_de_system_type_falla_cerrado(
    monkeypatch,
):
    monkeypatch.setattr(
        module,
        "fetch_all_dict_readonly",
        lambda sql: [
            _row(
                pk="u1",
                code="U-X",
                name="Unidad X",
                server="s1",
                branch="001",
                unit_system="MPRO",
                server_system="SoftRestaurant",
            )
        ],
    )

    with pytest.raises(
        module.FinanzasCanonicalUnitError
    ):
        module.get_canonical_finance_sync_units(
            "MPRO"
        )


def test_catalogo_vacio_falla_cerrado(
    monkeypatch,
):
    monkeypatch.setattr(
        module,
        "fetch_all_dict_readonly",
        lambda sql: [],
    )

    with pytest.raises(
        module.FinanzasCanonicalUnitError
    ):
        module.get_canonical_finance_sync_units(
            "SOFTRESTAURANT"
        )


def test_sql_exige_unidad_y_servidor_activos():
    sql = " ".join(
        module._CANONICAL_UNITS_SQL.split()
    ).upper()

    assert "UNIDADES_NEGOCIO" in sql
    assert "SERVIDORES_CONEXIONES" in sql
    assert "U.ACTIVO = 1" in sql
    assert "S.ACTIVO = 1" in sql


def test_no_contiene_unidades_productivas_hardcodeadas():
    import ast

    source = (
        __import__("pathlib")
        .Path(module.__file__)
        .read_text(
            encoding="utf-8",
            errors="strict",
        )
    )

    tree = ast.parse(source)

    string_literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
    }

    forbidden = {
        "130MID",
        "130QRO",
        "130° MERIDA",
        "130° QUERETARO",
        "CIENFUEGOS",
        "LA ESTELAR",
        "ORIGEN",
        "0021",
        "0023",
    }

    hits = string_literals.intersection(forbidden)

    assert hits == set()
