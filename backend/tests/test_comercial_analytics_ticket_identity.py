import os

import pytest

os.environ.setdefault(
    "JWT_SECRET",
    "test-ticket-identity-secret",
)

from modules.comercial_analytics.ticket_identity import (
    TicketIdentityError,
    create_ticket_pk,
    parse_ticket_pk,
)


def test_roundtrip_ticket_identity():
    ticket_pk = create_ticket_pk(
        unidad_negocio_id="CIENFUEGOS",
        fecha_operacion="2026-07-15",
        numero_ticket="18452",
    )

    identity = parse_ticket_pk(ticket_pk)

    assert identity.unidad_negocio_id == "CIENFUEGOS"
    assert identity.fecha_operacion == "2026-07-15"
    assert identity.numero_ticket == "18452"
    assert identity.version == 1


def test_same_identity_is_deterministic():
    first = create_ticket_pk(
        unidad_negocio_id="130MID",
        fecha_operacion="2026-07-15",
        numero_ticket="100",
    )
    second = create_ticket_pk(
        unidad_negocio_id="130MID",
        fecha_operacion="2026-07-15",
        numero_ticket="100",
    )

    assert first == second


def test_different_unit_produces_different_identity():
    first = create_ticket_pk(
        unidad_negocio_id="130MID",
        fecha_operacion="2026-07-15",
        numero_ticket="100",
    )
    second = create_ticket_pk(
        unidad_negocio_id="CIENFUEGOS",
        fecha_operacion="2026-07-15",
        numero_ticket="100",
    )

    assert first != second


def test_rejects_modified_ticket_pk():
    ticket_pk = create_ticket_pk(
        unidad_negocio_id="130MID",
        fecha_operacion="2026-07-15",
        numero_ticket="100",
    )

    modified = ticket_pk[:-1] + (
        "A" if ticket_pk[-1] != "A" else "B"
    )

    with pytest.raises(TicketIdentityError):
        parse_ticket_pk(modified)


@pytest.mark.parametrize(
    "field,value",
    [
        ("unidad_negocio_id", ""),
        ("numero_ticket", ""),
        ("fecha_operacion", "2026-99-99"),
    ],
)
def test_rejects_invalid_fields(field, value):
    payload = {
        "unidad_negocio_id": "130MID",
        "fecha_operacion": "2026-07-15",
        "numero_ticket": "100",
    }
    payload[field] = value

    with pytest.raises(TicketIdentityError):
        create_ticket_pk(**payload)
