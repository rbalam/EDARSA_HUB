from dataclasses import asdict
import pytest
from modules.integrations_center.rdp_metadata_import import (
    MAX_BYTES, RdpMetadataError, parse_rdp_address, parse_rdp_metadata,
)


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "utf-16"])
def test_import_allowlisted_metadata_only(encoding):
    payload = ("full address:s:Example.NET:1379\r\n"
               "username:s:ignored\r\npassword 51:b:ignored\r\n"
               "alternate shell:s:ignored\r\ngatewayhostname:s:ignored").encode(encoding)
    assert asdict(parse_rdp_metadata(payload)) == {
        "host": "example.net", "port": 1379, "port_source": "address",
    }


@pytest.mark.parametrize("address,host,port", [
    ("example.net", "example.net", 3389),
    ("192.0.2.1:1234", "192.0.2.1", 1234),
    ("[2001:db8::1]:1234", "2001:db8::1", 1234),
    ("2001:db8::1", "2001:db8::1", 3389),
    ("server", "server", 3389),
])
def test_address(address, host, port):
    result = parse_rdp_address(address)
    assert (result.host, result.port) == (host, port)


@pytest.mark.parametrize("address", [
    "https://example.net", "user@example.net", "a/b", "a\\b",
    "a:0", "a:65536", "a:-1", "a:abc", "999.1.1.1",
    "[example.net]:3389", "a b", "a\x00b", "a..b", "fe80::1%eth0",
])
def test_invalid_address(address):
    with pytest.raises(RdpMetadataError):
        parse_rdp_address(address)


@pytest.mark.parametrize("payload,error", [
    (b"", "INVALID_SIZE"),
    (b"x" * (MAX_BYTES + 1), "INVALID_SIZE"),
    (b"\xff", "INVALID_ENCODING"),
    (b"username:s:ignored", "MISSING_ADDRESS"),
    (b"full address:s:a\nfull address:s:b", "DUPLICATE_FIELD"),
    (b"full address:i:a", "INVALID_FIELD"),
    (b"full address:s:a:1234\nserver port:i:3389", "CONFLICTING_PORT"),
    (b"full address:s:a\nserver port:i:0", "INVALID_PORT"),
])
def test_rejected_payload(payload, error):
    with pytest.raises(RdpMetadataError, match="^" + error + "$"):
        parse_rdp_metadata(payload)


def test_separate_port_and_default_provenance():
    assert asdict(parse_rdp_metadata(b"full address:s:example.net\nserver port:i:1234")) == {
        "host": "example.net", "port": 1234, "port_source": "file",
    }
    assert parse_rdp_metadata(b"full address:s:example.net").port_source == "protocol_default"


def test_errors_do_not_echo_input():
    with pytest.raises(RdpMetadataError) as error:
        parse_rdp_address("secret@example.net")
    assert "secret" not in str(error.value)
