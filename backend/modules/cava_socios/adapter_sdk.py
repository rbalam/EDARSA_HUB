"""SDK proveedor-neutral para adapters de Cavas.

No resuelve conexiones, no contiene secretos, no escribe SQL y no conoce
proveedores concretos. Las conexiones se obtienen fuera de este SDK mediante
la infraestructura canonica de EDARSAHUB.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, Protocol, Sequence, runtime_checkable

from .migration_engine import ExternalRecord


@dataclass(frozen=True)
class AdapterCapabilities:
    full_extract: bool
    delta_extract: bool
    evidence_extract: bool = False
    supports_checkpoint: bool = False
    supports_historical_timestamps: bool = True


@dataclass(frozen=True)
class AdapterContext:
    source_instance_id: str
    connection_reference: Optional[str]
    timezone: str
    currency: Optional[str] = None
    locale: Optional[str] = None

    def __post_init__(self) -> None:
        if not str(self.source_instance_id or "").strip():
            raise ValueError("source_instance_id es requerido")
        if not str(self.timezone or "").strip():
            raise ValueError("timezone es requerido")


@dataclass(frozen=True)
class AdapterHealth:
    ok: bool
    code: str = "OK"
    message: Optional[str] = None


@dataclass(frozen=True)
class AdapterCheckpoint:
    value: str

    def __post_init__(self) -> None:
        if not str(self.value or "").strip():
            raise ValueError("checkpoint vacio")


@dataclass(frozen=True)
class ExtractionBatch:
    records: tuple[ExternalRecord, ...]
    next_checkpoint: Optional[AdapterCheckpoint] = None

    def __post_init__(self) -> None:
        keys = [record.identity.idempotency_key() for record in self.records]
        if len(keys) != len(set(keys)):
            raise ValueError("adapter produjo identidades externas duplicadas")


@runtime_checkable
class CavasSourceAdapter(Protocol):
    """Contrato implementado por adapters SoftRestaurant/MPRO/legacy futuros."""

    @property
    def adapter_code(self) -> str: ...

    @property
    def adapter_version(self) -> str: ...

    def capabilities(self) -> AdapterCapabilities: ...

    def validate_context(self, context: AdapterContext) -> None: ...

    def health(self, context: AdapterContext) -> AdapterHealth: ...

    def discover(self, context: AdapterContext) -> Mapping[str, object]: ...

    def extract_full(self, context: AdapterContext) -> ExtractionBatch: ...

    def extract_delta(
        self,
        context: AdapterContext,
        checkpoint: AdapterCheckpoint,
    ) -> ExtractionBatch: ...


def validate_adapter_contract(adapter: CavasSourceAdapter) -> None:
    """Valida identidad/capacidades sin abrir conexiones."""
    code = str(getattr(adapter, "adapter_code", "") or "").strip()
    version = str(getattr(adapter, "adapter_version", "") or "").strip()
    if not code:
        raise ValueError("adapter_code es requerido")
    if not version:
        raise ValueError("adapter_version es requerido")

    caps = adapter.capabilities()
    if caps.delta_extract and not caps.supports_checkpoint:
        raise ValueError("delta_extract requiere supports_checkpoint")


def validate_extraction(
    batch: ExtractionBatch,
    *,
    expected_source_instance_id: str,
) -> None:
    """Impide que un adapter mezcle instancias en un mismo contexto."""
    wanted = str(expected_source_instance_id or "").strip()
    if not wanted:
        raise ValueError("expected_source_instance_id es requerido")

    for record in batch.records:
        if record.identity.source_instance_id != wanted:
            raise ValueError("adapter devolvio registro de otra source_instance")


def adapter_manifest(adapter: CavasSourceAdapter) -> Mapping[str, object]:
    validate_adapter_contract(adapter)
    caps = adapter.capabilities()
    return {
        "adapter_code": adapter.adapter_code,
        "adapter_version": adapter.adapter_version,
        "capabilities": {
            "full_extract": caps.full_extract,
            "delta_extract": caps.delta_extract,
            "evidence_extract": caps.evidence_extract,
            "supports_checkpoint": caps.supports_checkpoint,
            "supports_historical_timestamps": caps.supports_historical_timestamps,
        },
    }
