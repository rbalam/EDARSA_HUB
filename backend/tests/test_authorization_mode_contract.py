from pathlib import Path

ROOT = Path("/app/backend")

MIG = (
    ROOT
    / "database/migrations"
    / "20260819_037_authorization_mode_contract.sql"
)

VAL = (
    ROOT
    / "database/validation"
    / "20260819_037_authorization_mode_contract_validation.sql"
)

ROLL = (
    ROOT
    / "database/rollback"
    / "20260819_037_authorization_mode_contract_rollback.sql"
)


def test_mode_is_defined_on_authorization_type():
    src = MIG.read_text(encoding="utf-8")

    assert "Usuario_TiposAutorizacion" in src
    assert "ModoAutorizacion" in src
    assert "'ESCALABLE'" in src
    assert "'MANCOMUNADA'" in src


def test_request_snapshots_mode():
    src = MIG.read_text(encoding="utf-8")

    assert "Usuario_Autorizaciones" in src
    assert "ModoAutorizacion" in src


def test_existing_types_preserve_current_behavior():
    src = MIG.read_text(encoding="utf-8")

    assert "SET ModoAutorizacion = 'ESCALABLE'" in src


def test_validation_checks_both_tables():
    src = VAL.read_text(encoding="utf-8")

    assert "Usuario_TiposAutorizacion" in src
    assert "Usuario_Autorizaciones" in src


def test_rollback_removes_new_contract_only():
    src = ROLL.read_text(encoding="utf-8")

    assert "DROP COLUMN ModoAutorizacion" in src
    assert "Usuario_MatrizAutorizacion" not in src
    assert "Usuario_AutorizacionesDetalle" not in src


def test_legacy_requires_all_levels_not_removed_yet():
    src = MIG.read_text(encoding="utf-8")

    assert "DROP COLUMN RequiereTodosLosNiveles" not in src
