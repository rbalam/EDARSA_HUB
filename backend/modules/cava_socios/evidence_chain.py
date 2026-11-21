"""Cadena de custodia pura para evidencias de Cavas.

No almacena binarios, no resuelve URLs, no escribe SQL y no conoce proveedores.
Modela integridad, procedencia y encadenamiento auditable sobre referencias
externas/almacenadas por infraestructura canonica.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Optional


class EvidenceKind(str, Enum):
    BOTTLE_ENTRY = "BOTTLE_ENTRY"
    MOVEMENT = "MOVEMENT"
    CONSUMPTION = "CONSUMPTION"
    AUDIT = "AUDIT"
    HISTORICAL_IMPORT = "HISTORICAL_IMPORT"


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    kind: EvidenceKind
    subject_type: str
    subject_id: str
    occurred_at: datetime
    captured_at: datetime
    storage_reference: str
    content_sha256: str
    mime_type: str
    source_system: Optional[str] = None
    source_record_id: Optional[str] = None
    actor_id: Optional[str] = None
    device_reference: Optional[str] = None
    previous_chain_hash: Optional[str] = None
    metadata: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        for value, name in [
            (self.evidence_id, "evidence_id"),
            (self.subject_type, "subject_type"),
            (self.subject_id, "subject_id"),
            (self.storage_reference, "storage_reference"),
            (self.content_sha256, "content_sha256"),
            (self.mime_type, "mime_type"),
        ]:
            if not str(value or "").strip():
                raise ValueError(f"{name} es requerido")
        _require_aware(self.occurred_at, "occurred_at")
        _require_aware(self.captured_at, "captured_at")
        if len(self.content_sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in self.content_sha256):
            raise ValueError("content_sha256 debe ser SHA-256 hexadecimal")

    @property
    def chain_hash(self) -> str:
        payload = {
            "evidence_id": self.evidence_id,
            "kind": self.kind.value,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "occurred_at": self.occurred_at.isoformat(),
            "captured_at": self.captured_at.isoformat(),
            "storage_reference": self.storage_reference,
            "content_sha256": self.content_sha256.lower(),
            "mime_type": self.mime_type,
            "source_system": self.source_system,
            "source_record_id": self.source_record_id,
            "actor_id": self.actor_id,
            "device_reference": self.device_reference,
            "previous_chain_hash": self.previous_chain_hash,
            "metadata": dict(self.metadata or {}),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def build_evidence(
    *,
    evidence_id: str,
    kind: EvidenceKind,
    subject_type: str,
    subject_id: str,
    occurred_at: datetime,
    captured_at: datetime,
    storage_reference: str,
    content: bytes,
    mime_type: str,
    source_system: Optional[str] = None,
    source_record_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    device_reference: Optional[str] = None,
    previous: Optional[EvidenceReference] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=evidence_id,
        kind=kind,
        subject_type=subject_type,
        subject_id=subject_id,
        occurred_at=occurred_at,
        captured_at=captured_at,
        storage_reference=storage_reference,
        content_sha256=sha256_bytes(content),
        mime_type=mime_type,
        source_system=source_system,
        source_record_id=source_record_id,
        actor_id=actor_id,
        device_reference=device_reference,
        previous_chain_hash=previous.chain_hash if previous else None,
        metadata=metadata,
    )


def verify_chain(*items: EvidenceReference) -> bool:
    if not items:
        return False
    previous_hash: Optional[str] = None
    for item in items:
        if item.previous_chain_hash != previous_hash:
            return False
        previous_hash = item.chain_hash
    return True


def verify_content(reference: EvidenceReference, content: bytes) -> bool:
    return sha256_bytes(content) == reference.content_sha256.lower()


def historical_evidence_metadata(
    *,
    source_system: str,
    source_record_id: str,
    imported_at: datetime,
    migration_batch_id: Optional[str] = None,
) -> Mapping[str, str]:
    _require_aware(imported_at, "imported_at")
    result = {
        "source_system": str(source_system or "").strip(),
        "source_record_id": str(source_record_id or "").strip(),
        "imported_at": imported_at.isoformat(),
    }
    if not result["source_system"] or not result["source_record_id"]:
        raise ValueError("source_system y source_record_id son requeridos")
    if migration_batch_id:
        result["migration_batch_id"] = str(migration_batch_id)
    return result


def _require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} debe incluir zona horaria")
