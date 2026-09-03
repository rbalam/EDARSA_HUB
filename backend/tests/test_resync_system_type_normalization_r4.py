from pathlib import Path


TEXT = (
    Path(__file__).resolve().parents[1]
    / 'api'
    / 'admin_scheduler_resync.py'
).read_text(encoding='utf-8')


def test_softrestaurant_variants_are_normalized_in_dry_and_real():
    assert 'from core.system_type_utils import normalize_system_type' in TEXT
    assert TEXT.count('sistema_normalizado = normalize_system_type(sistema_raw)') == 2
    assert TEXT.count("if sistema == 'SOFTRESTAURANT'") >= 2


def test_dry_run_exposes_unambiguous_contract_markers():
    assert "query_source = 'SOFTRESTAURANT_REPORTE_TURNOS'" in TEXT
    assert "'system_type_raw': sistema_raw" in TEXT
    assert "'system_type_normalized': sistema_normalizado" in TEXT
    assert "'backend_contract_version': 'softrestaurant-turnos-v2'" in TEXT
