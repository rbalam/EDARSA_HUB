import hashlib
from pathlib import Path


EXPECTED_BLOB_SHA1 = "47e7e005cf3c382c546ffc017a28a5c6d87796bc"


def test_sync_comercial_abiertas_v2_is_byte_for_byte_protected():
    path = (
        Path(__file__).resolve().parents[1]
        / "core"
        / "scheduler"
        / "jobs"
        / "sync_comercial_abiertas_v2_job.py"
    )
    data = path.read_bytes()
    git_blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    actual = hashlib.sha1(git_blob).hexdigest()

    assert actual == EXPECTED_BLOB_SHA1, (
        "sync_comercial_abiertas_v2_job.py esta protegido por contrato y no "
        "puede modificarse dentro de trabajos de Sincronizacion Historica ni "
        "de desacoplamiento del runtime."
    )
