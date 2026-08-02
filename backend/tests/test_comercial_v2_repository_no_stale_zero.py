from __future__ import annotations

import ast
from pathlib import Path


TARGET = Path(
    "/app/backend/modules/comercial_v2/"
    "repository_comercial_edarsahub.py"
)


def upsert_source() -> str:
    text = TARGET.read_text(encoding="utf-8")
    lines = text.splitlines()
    tree = ast.parse(text)

    node = next(
        item
        for item in ast.walk(tree)
        if isinstance(item, ast.FunctionDef)
        and item.name == "upsert_ventas_dia_abiertas"
    )

    return "\n".join(
        lines[node.lineno - 1:node.end_lineno]
    )


def test_repository_does_not_preserve_positive_value_over_confirmed_zero():
    block = upsert_source()

    forbidden = (
        "SKIP_ANTI_ZERO",
        "preserved_total",
        "NO se sobrescribe",
        "ANTI-$0 FALSO",
    )

    for token in forbidden:
        assert token not in block


def test_confirmed_zero_continues_to_update():
    block = upsert_source()

    assert "UPSERT-CERO-CONFIRMADO" in block
    assert "actualizando misma fecha" in block

    zero_log_position = block.index(
        "UPSERT-CERO-CONFIRMADO"
    )
    update_position = block.index(
        'update_query = f"""'
    )

    assert zero_log_position < update_position


def test_different_operational_date_still_updates():
    block = upsert_source()

    assert "if existing_fecha != new_fecha:" in block
    assert "[UPSERT-FECHA]" in block


def test_repository_keeps_business_invariants():
    block = upsert_source()

    assert (
        "total_estimado_dia debe ser igual a "
        in block
    )
    assert "propinas_total" in block
    assert "BLOCKED_WRONG_FECHA" in block
    assert "BLOCKED_FUTURE_DATE" in block
