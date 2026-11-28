"""Offline, allowlisted RDP metadata import. Never opens a connection."""
from dataclasses import dataclass
import ipaddress
import re

MAX_BYTES = 65536
DEFAULT_PORT = 3389  # RDP protocol default, not a deployment setting.
_DNS_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", re.ASCII)
_PORT = re.compile(r"[0-9]{1,5}", re.ASCII)


class RdpMetadataError(ValueError):
    """Stable error codes only; never include untrusted input."""


@dataclass(frozen=True)
class RdpMetadata:
    host: str
    port: int
    port_source: str


def _port(value: str) -> int:
    if not _PORT.fullmatch(value):
        raise RdpMetadataError("INVALID_PORT")
    port = int(value)
    if not 1 <= port <= 65535:
        raise RdpMetadataError("INVALID_PORT")
    return port


def _host(value: str) -> str:
    if not value or "%" in value:
        raise RdpMetadataError("INVALID_HOST")
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        pass
    value = value.rstrip(".")
    if not value or len(value) > 253 or not all(
        _DNS_LABEL.fullmatch(label) for label in value.split(".")
    ):
        raise RdpMetadataError("INVALID_HOST")
    if all(c in "0123456789." for c in value):
        raise RdpMetadataError("INVALID_HOST")
    return value.lower()


def parse_rdp_address(address: str, *, separate_port: int | None = None) -> RdpMetadata:
    """Parse endpoint syntax without DNS resolution or authorization claims."""
    if not isinstance(address, str) or len(address) > 300:
        raise RdpMetadataError("INVALID_ADDRESS")
    if separate_port is not None and (
        type(separate_port) is not int or not 1 <= separate_port <= 65535
    ):
        raise RdpMetadataError("INVALID_PORT")
    address = address.strip()
    if any(ord(c) < 33 or ord(c) == 127 for c in address):
        raise RdpMetadataError("INVALID_ADDRESS")
    inline = None
    if address.startswith("["):
        match = re.fullmatch(r"\[([^\]]+)\](?::([0-9]+))?", address)
        if match is None:
            raise RdpMetadataError("INVALID_ADDRESS")
        raw_host = match.group(1)
        try:
            if "%" in raw_host:
                raise ValueError
            ipaddress.IPv6Address(raw_host)
        except ValueError:
            raise RdpMetadataError("INVALID_HOST") from None
        if match.group(2) is not None:
            inline = _port(match.group(2))
    elif address.count(":") == 1:
        raw_host, raw_port = address.rsplit(":", 1)
        inline = _port(raw_port)
    else:
        raw_host = address
    host = _host(raw_host)
    if inline is not None and separate_port is not None and inline != separate_port:
        raise RdpMetadataError("CONFLICTING_PORT")
    if inline is not None:
        return RdpMetadata(host, inline, "address")
    if separate_port is not None:
        return RdpMetadata(host, separate_port, "file")
    return RdpMetadata(host, DEFAULT_PORT, "protocol_default")


def parse_rdp_metadata(payload: bytes) -> RdpMetadata:
    """Extract only full address and server port; discard all other fields."""
    if not isinstance(payload, bytes) or not 0 < len(payload) <= MAX_BYTES:
        raise RdpMetadataError("INVALID_SIZE")
    try:
        encoding = "utf-16" if payload.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
        text = payload.decode(encoding, errors="strict")
    except UnicodeError:
        raise RdpMetadataError("INVALID_ENCODING") from None
    if "\x00" in text:
        raise RdpMetadataError("INVALID_ENCODING")
    fields = {}
    for line in text.splitlines():
        parts = line.partition(":")
        key = parts[0].strip().lower()
        if key not in {"full address", "server port"}:
            continue
        if key in fields:
            raise RdpMetadataError("DUPLICATE_FIELD")
        kind, sep, value = parts[2].partition(":")
        expected = "s" if key == "full address" else "i"
        if not parts[1] or not sep or kind != expected:
            raise RdpMetadataError("INVALID_FIELD")
        fields[key] = value.strip()
    if "full address" not in fields:
        raise RdpMetadataError("MISSING_ADDRESS")
    port = _port(fields["server port"]) if "server port" in fields else None
    return parse_rdp_address(fields["full address"], separate_port=port)
