import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLISHER_DIR = ROOT / "tools" / "mirror_sync"


def test_result_publisher_imports_when_executed_directly_from_its_directory():
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import runpy; "
                "runpy.run_path("
                "'universal_job_result_publisher.py', "
                "run_name='publisher_import_contract'"
                ")"
            ),
        ],
        cwd=PUBLISHER_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
