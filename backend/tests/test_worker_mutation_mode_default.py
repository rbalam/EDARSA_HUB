from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync.worker_scheduling import normalize_metadata


def test_missing_mode_defaults_to_mutation_in_scheduling():
    metadata = normalize_metadata({
        "scheduling": {
            "project_id": "TEST",
            "bounded_context": "TEST",
        }
    })

    assert metadata.mode == "MUTATION"


def test_dispatcher_missing_mode_defaults_to_mutation():
    dispatcher = (
        ROOT
        / "tools"
        / "mirror_sync"
        / "universal_job_dispatcher.py"
    ).read_text(encoding="utf-8")

    assert (
        'mode = str(job.get("mode") or "MUTATION").upper().strip()'
        in dispatcher
    )
