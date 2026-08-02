from pathlib import Path


JOB = (
    Path(__file__).resolve().parents[1]
    / "core"
    / "scheduler"
    / "jobs"
    / "sync_comercial_abiertas_v2_job.py"
)


def test_mpro_open_queries_use_real_open_states():
    text = JOB.read_text(encoding="utf-8")

    assert text.count(
        "AND c.Es_Cve_Estado IN ('AC', 'IM')"
    ) == 2

    assert "AND c.Es_Cve_Estado = 'UN'" not in text


def test_mpro_closed_queries_keep_paid_state():
    text = JOB.read_text(encoding="utf-8")

    assert text.count(
        "AND c.Es_Cve_Estado = 'PA'"
    ) >= 2


def test_open_and_closed_states_do_not_overlap():
    text = JOB.read_text(encoding="utf-8")

    assert "IN ('AC', 'IM', 'PA')" not in text
    assert "IN ('AC','IM','PA')" not in text
