"""Resolución canónica y segura de conexiones por unidad de negocio."""

from .pos_connection_resolver import (
    AuthenticationRequired,
    CanonicalMappingError,
    ExplicitPermissionRequired,
    PosConnectionResolverError,
    ScopeDenied,
    UnsafeMetadataError,
    resolve_pos_connection_metadata,
)

__all__ = [
    "AuthenticationRequired",
    "CanonicalMappingError",
    "ExplicitPermissionRequired",
    "PosConnectionResolverError",
    "ScopeDenied",
    "UnsafeMetadataError",
    "resolve_pos_connection_metadata",
]
