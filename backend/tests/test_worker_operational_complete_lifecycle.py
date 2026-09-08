from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_dispatcher.py'


def test_operational_complete_routes_to_done_not_rejected():
    text = DISPATCHER.read_text(encoding='utf-8')
    expected = 'target = DONE / path.name if result["status"] in {"INTEGRATED", "READ_ONLY_COMPLETE", "OPERATIONAL_COMPLETE"} else REJECTED / path.name'
    assert expected in text
