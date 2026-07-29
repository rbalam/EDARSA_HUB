"""Nucleo canonico de integraciones de EDARSAHUB."""

from .models import ConnectionRecord, ProviderDefinition, ConnectionScope
from .provider_registry import ProviderRegistry, provider_registry
from .registry import ConnectionRegistry

__all__ = [
    "ConnectionRecord",
    "ProviderDefinition",
    "ConnectionScope",
    "ProviderRegistry",
    "provider_registry",
    "ConnectionRegistry",
]
