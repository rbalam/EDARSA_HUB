"""
Primitiva canónica de redondeo para Costos/Márgenes.

Responsabilidad única:
    aplicar un método de redondeo explícito a un múltiplo positivo.

No contiene:
    - configuración de negocio;
    - defaults funcionales;
    - acceso SQL;
    - RBAC;
    - lógica específica de vinos;
    - reglas de margen.

Los consumidores deben resolver previamente la configuración efectiva
desde la fuente canónica correspondiente.
"""

from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_CEILING,
    ROUND_FLOOR,
    ROUND_HALF_UP,
)
from typing import Any


METODO_MAS_CERCANO = "MAS_CERCANO"
METODO_HACIA_ARRIBA = "HACIA_ARRIBA"
METODO_HACIA_ABAJO = "HACIA_ABAJO"

METODOS_REDONDEO_VALIDOS = frozenset(
    {
        METODO_MAS_CERCANO,
        METODO_HACIA_ARRIBA,
        METODO_HACIA_ABAJO,
    }
)


def _decimal(value: Any, nombre: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(
            f"{nombre} debe ser un valor decimal válido"
        ) from exc

    if not result.is_finite():
        raise ValueError(
            f"{nombre} debe ser un valor decimal finito"
        )

    return result


def redondear_a_multiplo(
    valor: Any,
    multiplo: Any,
    metodo: str,
) -> Decimal:
    """
    Redondea ``valor`` al múltiplo positivo indicado.

    MAS_CERCANO
        Empates se resuelven con ROUND_HALF_UP.

    HACIA_ARRIBA
        Redondeo matemático hacia +infinito.

    HACIA_ABAJO
        Redondeo matemático hacia -infinito.

    El contrato es fail-closed:
        - múltiplo <= 0 -> ValueError
        - método desconocido -> ValueError
        - valores no finitos/inválidos -> ValueError
    """

    valor_decimal = _decimal(valor, "valor")
    multiplo_decimal = _decimal(
        multiplo,
        "multiplo",
    )

    if multiplo_decimal <= 0:
        raise ValueError(
            "multiplo debe ser mayor que cero"
        )

    if metodo not in METODOS_REDONDEO_VALIDOS:
        raise ValueError(
            f"metodo de redondeo inválido: {metodo!r}"
        )

    cociente = valor_decimal / multiplo_decimal

    if metodo == METODO_MAS_CERCANO:
        entero = cociente.quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    elif metodo == METODO_HACIA_ARRIBA:
        entero = cociente.quantize(
            Decimal("1"),
            rounding=ROUND_CEILING,
        )
    else:
        entero = cociente.quantize(
            Decimal("1"),
            rounding=ROUND_FLOOR,
        )

    return entero * multiplo_decimal
