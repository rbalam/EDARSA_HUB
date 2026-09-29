"""Adapter canónico READ_ONLY para CAVAS Cienfuegos.

Este adapter pertenece al bounded context existente ``cava_socios``.

Responsabilidades:
- convertir registros legacy al contrato provider-neutral de migration_engine;
- preservar identidad legacy e idempotencia;
- normalizar semántica CAVAS;
- conservar historia aun cuando la entidad legacy actual ya no exista.

No es responsable de:
- crear otro motor de migración;
- escribir en la base legacy;
- escribir directamente en EDARSAHUB;
- resolver por sí mismo Persona/Cliente/Socio;
- migrar passwords o RBAC legacy;
- convertir attendance.ticket_total en Venta canónica.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from .adapter_sdk import (
    AdapterCapabilities,
    AdapterCheckpoint,
    AdapterContext,
    CavasSourceAdapter,
    ExtractionBatch,
)
from .migration_engine import (
    ExternalRecord,
    SourceIdentity,
)


ADAPTER_CODE = "CAVAS_CIENFUEGOS"
ADAPTER_VERSION = "1.0"

MIGRATABLE_ENTITIES = frozenset(
    {
        "clients",
        "cellars",
        "cellars_clients",
        "bottles",
        "bottle_logs",
        "attendances",
        "client_notes",
        "media",
    }
)

HISTORICAL_ONLY_ENTITIES = frozenset(
    {
        "logs",
    }
)

DO_NOT_MIGRATE_ENTITIES = frozenset(
    {
        "users",
        "roles",
        "acos",
        "aros",
        "aros_acos",
    }
)

BOTTLE_ACTIONS = frozenset(
    {
        "add",
        "in",
        "out",
    }
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _require(value: Any, code: str) -> str:
    result = _clean(value)

    if not result:
        raise ValueError(code)

    return result


def _require_aware(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(
            "CAVAS_ORIGINAL_OCCURRED_AT_REQUIRED"
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(
            "CAVAS_ORIGINAL_OCCURRED_AT_TIMEZONE_REQUIRED"
        )

    return value


def normalize_email(
    value: Any,
) -> str | None:
    result = _clean(value).lower()
    return result or None


def normalize_phone(
    value: Any,
) -> str | None:
    text = _clean(value)

    if not text:
        return None

    digits = "".join(
        char
        for char in text
        if char.isdigit()
    )

    if not digits:
        return None

    return (
        "+" + digits
        if text.startswith("+")
        else digits
    )


def normalize_capacity_ml(
    value: Any,
) -> int | None:
    text = _clean(value)

    if not text:
        return None

    try:
        amount = Decimal(text)
    except InvalidOperation:
        return None

    if amount <= 0:
        return None

    integer = int(amount)

    if Decimal(integer) != amount:
        return None

    return integer


def entity_disposition(
    entity_type: str,
) -> str:
    entity = _clean(
        entity_type
    ).lower()

    if entity in MIGRATABLE_ENTITIES:
        return "MIGRATE_CANONICALLY"

    if entity in HISTORICAL_ONLY_ENTITIES:
        return "HISTORICAL_ONLY"

    if entity in DO_NOT_MIGRATE_ENTITIES:
        return "DO_NOT_MIGRATE"

    raise ValueError(
        "CAVAS_LEGACY_ENTITY_UNSUPPORTED"
    )


def source_identity(
    *,
    source_instance_id: str,
    entity_type: str,
    source_record_id: Any,
    source_transaction_id: Any = None,
    source_line_id: Any = None,
) -> SourceIdentity:
    entity = _require(
        entity_type,
        "CAVAS_ENTITY_TYPE_REQUIRED",
    ).lower()

    if entity not in (
        MIGRATABLE_ENTITIES
        | HISTORICAL_ONLY_ENTITIES
        | DO_NOT_MIGRATE_ENTITIES
    ):
        raise ValueError(
            "CAVAS_LEGACY_ENTITY_UNSUPPORTED"
        )

    return SourceIdentity(
        source_instance_id=_require(
            source_instance_id,
            "CAVAS_SOURCE_INSTANCE_REQUIRED",
        ),
        entity_type=entity,
        source_record_id=_require(
            source_record_id,
            "CAVAS_SOURCE_RECORD_ID_REQUIRED",
        ),
        source_transaction_id=(
            _clean(source_transaction_id)
            or None
        ),
        source_line_id=(
            _clean(source_line_id)
            or None
        ),
    )


def normalize_client(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "legacy_id": _require(
            row.get("id"),
            "CAVAS_CLIENT_ID_REQUIRED",
        ),
        "name": (
            _clean(row.get("name"))
            or None
        ),
        "last_name": (
            _clean(row.get("last_name"))
            or None
        ),
        "email": normalize_email(
            row.get("email")
        ),
        "phone": normalize_phone(
            row.get("phone")
        ),
        "birthday": row.get("birthday"),
        "active": row.get("active"),
        "vip": row.get("vip"),
        "type": (
            _clean(row.get("type"))
            or None
        ),
        "relation_id": (
            _clean(row.get("relation_id"))
            or None
        ),
        "relation_type": (
            _clean(row.get("relation_type"))
            or None
        ),

        # El profiling encontró 13 emails duplicados.
        # Email es evidencia, nunca autorización de merge.
        "auto_merge_allowed": False,
    }


def normalize_cellar(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "legacy_id": _require(
            row.get("id"),
            "CAVAS_CELLAR_ID_REQUIRED",
        ),
        "name": (
            _clean(row.get("name"))
            or None
        ),
        "alias": (
            _clean(row.get("alias"))
            or None
        ),
        "active": row.get("active"),
        "comments": row.get("comments"),
    }


def normalize_cellar_client(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "legacy_id": _require(
            row.get("id"),
            "CAVAS_CELLAR_CLIENT_ID_REQUIRED",
        ),
        "legacy_cellar_id": _require(
            row.get("cellar_id"),
            "CAVAS_CELLAR_ID_REQUIRED",
        ),
        "legacy_client_id": _require(
            row.get("client_id"),
            "CAVAS_CLIENT_ID_REQUIRED",
        ),
    }


def normalize_bottle(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    status = _require(
        row.get("status"),
        "CAVAS_BOTTLE_STATUS_REQUIRED",
    ).lower()

    if status not in {"in", "out"}:
        raise ValueError(
            "CAVAS_BOTTLE_STATUS_UNSUPPORTED"
        )

    return {
        "legacy_id": _require(
            row.get("id"),
            "CAVAS_BOTTLE_ID_REQUIRED",
        ),
        "name": (
            _clean(row.get("name"))
            or None
        ),
        "capacity_ml": normalize_capacity_ml(
            row.get("capacity")
        ),
        "contents": row.get("contents"),
        "legacy_cellar_id": _require(
            row.get("cellar_id"),
            "CAVAS_CELLAR_ID_REQUIRED",
        ),
        "comments": row.get("comments"),
        "legacy_status": status,
        "created": row.get("created"),
        "modified": row.get("modified"),
    }


def normalize_bottle_log(
    row: Mapping[str, Any],
    *,
    current_bottle_exists: bool,
) -> dict[str, Any]:
    action = _require(
        row.get("action"),
        "CAVAS_BOTTLE_ACTION_REQUIRED",
    ).lower()

    if action not in BOTTLE_ACTIONS:
        raise ValueError(
            "CAVAS_BOTTLE_ACTION_UNSUPPORTED"
        )

    return {
        "legacy_id": _require(
            row.get("id"),
            "CAVAS_BOTTLE_LOG_ID_REQUIRED",
        ),
        "legacy_bottle_id": _require(
            row.get("bottle_id"),
            "CAVAS_BOTTLE_ID_REQUIRED",
        ),
        "legacy_cellar_id": (
            _clean(row.get("cellar_id"))
            or None
        ),
        "legacy_client_id": (
            _clean(row.get("client_id"))
            or None
        ),
        "legacy_user_id": (
            _clean(row.get("user_id"))
            or None
        ),
        "legacy_attendance_id": (
            _clean(row.get("attendance_id"))
            or None
        ),
        "action": action,
        "contents": row.get("contents"),
        "created": row.get("created"),

        # El legacy borra físicamente botellas.
        # Ausencia actual != corrupción histórica.
        "historical_reference": (
            not current_bottle_exists
        ),
    }


def normalize_attendance(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    raw_amount = row.get(
        "ticket_total"
    )

    ticket_total = None

    if raw_amount not in (
        None,
        "",
    ):
        try:
            ticket_total = Decimal(
                str(raw_amount)
            )
        except InvalidOperation:
            ticket_total = None

    return {
        "legacy_id": _require(
            row.get("id"),
            "CAVAS_ATTENDANCE_ID_REQUIRED",
        ),
        "legacy_client_id": _require(
            row.get("client_id"),
            "CAVAS_CLIENT_ID_REQUIRED",
        ),
        "name": row.get("name"),
        "ticket_total_evidence": (
            ticket_total
        ),
        "person_amount": row.get(
            "person_amount"
        ),
        "created": row.get("created"),
        "modified": row.get("modified"),

        # No convertirlo en Venta EDARSAHUB.
        "canonical_sale": False,
    }


def external_record(
    *,
    source_instance_id: str,
    entity_type: str,
    source_record_id: Any,
    payload: Mapping[str, Any],
    original_occurred_at: datetime,
    original_created_at: datetime | None = None,
    source_transaction_id: Any = None,
    source_line_id: Any = None,
) -> ExternalRecord:
    return ExternalRecord(
        identity=source_identity(
            source_instance_id=(
                source_instance_id
            ),
            entity_type=entity_type,
            source_record_id=(
                source_record_id
            ),
            source_transaction_id=(
                source_transaction_id
            ),
            source_line_id=(
                source_line_id
            ),
        ),
        source_system=ADAPTER_CODE,
        payload=dict(payload),
        original_occurred_at=(
            _require_aware(
                original_occurred_at
            )
        ),
        original_created_at=(
            _require_aware(
                original_created_at
            )
            if original_created_at
            is not None
            else None
        ),
    )


class CienfuegosLegacyAdapter(
    CavasSourceAdapter
):
    """Adapter provider-neutral para la fuente legacy Cienfuegos.

    Gate 1 materializa contrato y semántica.
    Gate 2 conectará el extractor al Server Registry canónico.
    """

    def adapter_code(self) -> str:
        return ADAPTER_CODE

    def adapter_version(self) -> str:
        return ADAPTER_VERSION

    def capabilities(
        self,
    ) -> AdapterCapabilities:
        return AdapterCapabilities(
            full_extract=True,
            delta_extract=False,
            evidence_extract=True,
            supports_checkpoint=False,
            supports_historical_timestamps=True,
        )

    def validate_context(
        self,
        context: AdapterContext,
    ) -> None:
        if not _clean(
            context.source_instance_id
        ):
            raise ValueError(
                "CAVAS_SOURCE_INSTANCE_REQUIRED"
            )

        if not _clean(
            context.timezone
        ):
            raise ValueError(
                "CAVAS_TIMEZONE_REQUIRED"
            )

    def health(
        self,
        context: AdapterContext,
    ):
        raise NotImplementedError(
            "CAVAS_GATE2_SOURCE_HEALTH"
        )

    def discover(
        self,
        context: AdapterContext,
    ) -> Mapping[str, object]:
        self.validate_context(
            context
        )

        return {
            "adapter_code": (
                self.adapter_code()
            ),
            "adapter_version": (
                self.adapter_version()
            ),
            "source_instance_id": (
                context.source_instance_id
            ),
            "read_only": True,
            "entities": sorted(
                MIGRATABLE_ENTITIES
            ),
        }

    def extract_full(
        self,
        context: AdapterContext,
    ) -> ExtractionBatch:
        raise NotImplementedError(
            "CAVAS_GATE2_FULL_EXTRACTION"
        )

    def extract_delta(
        self,
        context: AdapterContext,
        checkpoint: AdapterCheckpoint,
    ) -> ExtractionBatch:
        raise NotImplementedError(
            "CAVAS_DELTA_NOT_SUPPORTED"
        )
