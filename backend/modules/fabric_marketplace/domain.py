"""Pure Marketplace domain contracts; no persistence or execution authority."""
from dataclasses import dataclass
from enum import Enum
import re


class Visibility(str, Enum):
    PRIVATE = "PRIVATE"
    ORGANIZATION = "ORGANIZATION"
    PUBLIC = "PUBLIC"


def _required(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Non-empty reference required")


@dataclass(frozen=True)
class Product:
    product_id: str
    publisher_ref: str
    owner_organization_ref: str

    def __post_init__(self):
        for value in (self.product_id, self.publisher_ref, self.owner_organization_ref):
            _required(value)


@dataclass(frozen=True)
class Release:
    release_id: str
    product_id: str
    version: str
    artifact_sha256: str
    manifest_sha256: str

    def __post_init__(self):
        for value in (self.release_id, self.product_id, self.version):
            _required(value)
        for digest in (self.artifact_sha256, self.manifest_sha256):
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("Invalid SHA-256 digest")


@dataclass(frozen=True)
class Listing:
    product_id: str
    release_id: str
    visibility: Visibility
    certification_ref: str

    def __post_init__(self):
        for value in (self.product_id, self.release_id, self.certification_ref):
            _required(value)
        if not isinstance(self.visibility, Visibility):
            raise ValueError("Invalid visibility")


@dataclass(frozen=True)
class InstallationRequest:
    release_id: str
    organization_ref: str
    entitlement_ref: str
    authorization_ref: str

    def __post_init__(self):
        for value in (self.release_id, self.organization_ref, self.entitlement_ref, self.authorization_ref):
            _required(value)
