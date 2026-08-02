from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


_VERSION = 1
_NAMESPACE = "commercial_ticket"


class TicketIdentityError(ValueError):
    pass


@dataclass(frozen=True)
class TicketIdentity:
    unidad_negocio_id: str
    fecha_operacion: str
    numero_ticket: str
    version: int = _VERSION


def _secret() -> bytes:
    value = os.getenv("JWT_SECRET")
    if not value:
        raise RuntimeError(
            "JWT_SECRET no configurado para firmar ticket_pk"
        )
    return value.encode("utf-8")


def _required(value: Any, field: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise TicketIdentityError(f"{field} es obligatorio")
    return normalized


def _date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    normalized = str(value or "").strip()[:10]

    try:
        return datetime.strptime(
            normalized,
            "%Y-%m-%d",
        ).date().isoformat()
    except ValueError as exc:
        raise TicketIdentityError(
            "fecha_operacion inválida"
        ) from exc


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(
        value
    ).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)

    try:
        return base64.urlsafe_b64decode(value + padding)
    except Exception as exc:
        raise TicketIdentityError(
            "ticket_pk tiene codificación inválida"
        ) from exc


def create_ticket_pk(
    *,
    unidad_negocio_id: Any,
    fecha_operacion: Any,
    numero_ticket: Any,
) -> str:
    payload = {
        "v": _VERSION,
        "ns": _NAMESPACE,
        "u": _required(
            unidad_negocio_id,
            "unidad_negocio_id",
        ),
        "f": _date(fecha_operacion),
        "t": _required(
            numero_ticket,
            "numero_ticket",
        ),
    }

    payload_bytes = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    signature = hmac.new(
        _secret(),
        payload_bytes,
        hashlib.sha256,
    ).digest()

    return f"{_encode(payload_bytes)}.{_encode(signature)}"


def parse_ticket_pk(ticket_pk: str) -> TicketIdentity:
    value = str(ticket_pk or "").strip()

    try:
        payload_part, signature_part = value.split(".", 1)
    except ValueError as exc:
        raise TicketIdentityError(
            "ticket_pk tiene formato inválido"
        ) from exc

    payload_bytes = _decode(payload_part)
    supplied_signature = _decode(signature_part)

    expected_signature = hmac.new(
        _secret(),
        payload_bytes,
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(
        supplied_signature,
        expected_signature,
    ):
        raise TicketIdentityError(
            "ticket_pk inválido o alterado"
        )

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TicketIdentityError(
            "ticket_pk contiene un payload inválido"
        ) from exc

    if payload.get("v") != _VERSION:
        raise TicketIdentityError(
            "versión de ticket_pk no soportada"
        )

    if payload.get("ns") != _NAMESPACE:
        raise TicketIdentityError(
            "namespace de ticket_pk inválido"
        )

    return TicketIdentity(
        unidad_negocio_id=_required(
            payload.get("u"),
            "unidad_negocio_id",
        ),
        fecha_operacion=_date(payload.get("f")),
        numero_ticket=_required(
            payload.get("t"),
            "numero_ticket",
        ),
        version=int(payload["v"]),
    )
