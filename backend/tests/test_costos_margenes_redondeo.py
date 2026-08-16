from decimal import Decimal

import pytest

from modules.costos_margenes.redondeo import (
    METODO_HACIA_ABAJO,
    METODO_HACIA_ARRIBA,
    METODO_MAS_CERCANO,
    redondear_a_multiplo,
)


@pytest.mark.parametrize(
    ("valor", "multiplo", "esperado"),
    [
        ("2.5", "1", "3"),
        ("7.5", "5", "10"),
        ("12.5", "5", "15"),
        ("17.5", "5", "20"),
        ("102.5", "5", "105"),
        ("107.5", "5", "110"),
        ("112.5", "5", "115"),
    ],
)
def test_mas_cercano_usa_half_up(
    valor,
    multiplo,
    esperado,
):
    assert redondear_a_multiplo(
        valor,
        multiplo,
        METODO_MAS_CERCANO,
    ) == Decimal(esperado)


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("102.01", "105"),
        ("102.99", "105"),
        ("105", "105"),
    ],
)
def test_hacia_arriba(
    valor,
    esperado,
):
    assert redondear_a_multiplo(
        valor,
        "5",
        METODO_HACIA_ARRIBA,
    ) == Decimal(esperado)


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("102.01", "100"),
        ("102.99", "100"),
        ("105", "105"),
    ],
)
def test_hacia_abajo(
    valor,
    esperado,
):
    assert redondear_a_multiplo(
        valor,
        "5",
        METODO_HACIA_ABAJO,
    ) == Decimal(esperado)


@pytest.mark.parametrize(
    "multiplo",
    [
        "0",
        "-1",
        "-5",
    ],
)
def test_rechaza_multiplo_no_positivo(
    multiplo,
):
    with pytest.raises(
        ValueError,
        match="mayor que cero",
    ):
        redondear_a_multiplo(
            "100",
            multiplo,
            METODO_MAS_CERCANO,
        )


def test_rechaza_metodo_desconocido():
    with pytest.raises(
        ValueError,
        match="método|metodo",
    ):
        redondear_a_multiplo(
            "100",
            "5",
            "NO_EXISTE",
        )


@pytest.mark.parametrize(
    "valor",
    [
        "NaN",
        "Infinity",
        "-Infinity",
        None,
        "abc",
    ],
)
def test_rechaza_valores_invalidos(
    valor,
):
    with pytest.raises(ValueError):
        redondear_a_multiplo(
            valor,
            "5",
            METODO_MAS_CERCANO,
        )


def test_preserva_decimal_sin_float_binario():
    resultado = redondear_a_multiplo(
        Decimal("102.5000000000"),
        Decimal("5.0000000000"),
        METODO_MAS_CERCANO,
    )

    assert resultado == Decimal("105.0000000000")
