import hashlib
from pathlib import Path


EXPECTED_BLOB_SHA1 = "e97b55a06b0adb5b447904c7643b99844f00aae7"


def test_production_sync_comercial_abiertas_v2_is_byte_for_byte_protected():
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
        "sync_comercial_abiertas_v2_job.py de Produccion esta protegido por "
        "contrato y no puede modificarse durante el desacoplamiento."
    )
