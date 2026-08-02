from __future__ import annotations

import ast
from pathlib import Path


TARGET = Path(
    "/app/backend/core/scheduler/jobs/"
    "sync_comercial_abiertas_v2_job.py"
)


def function_source(name: str) -> str:
    text = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(text)
    lines = text.splitlines()

    node = next(
        item
        for item in ast.walk(tree)
        if isinstance(
            item,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
        and item.name == name
    )

    return "\n".join(
        lines[node.lineno - 1:node.end_lineno]
    )


def test_execute_accepts_explicit_date():
    block = function_source(
        "execute_sync_comercial_abiertas_v2"
    )

    assert "fecha_objetivo: date = None" in block
    assert (
        "fecha_hoy = fecha_objetivo "
        "or now_mexico.date()"
    ) in block
    assert block.count(
        "fecha_objetivo\n"
        "                    or "
        "resultado_ventana.fecha_operacion"
    ) == 2


def test_manual_execution_forwards_date():
    block = function_source(
        "run_sync_comercial_abiertas_v2_manual"
    )

    assert "fecha_objetivo=fecha" in block


def test_stale_values_are_not_reused():
    block = function_source(
        "execute_sync_comercial_abiertas_v2"
    )

    for forbidden in (
        "_get_existing_ventas_dia(",
        "SKIPPED_ZERO_PROTECTION",
        "SKIPPED_BOTH_NULL",
        "existing_total",
        "existing_fecha",
    ):
        assert forbidden not in block


def test_confirmed_zero_is_valid():
    block = function_source(
        "execute_sync_comercial_abiertas_v2"
    )

    assert block.count(
        'source_status = "NO_DATA_CONFIRMED"'
    ) == 2

    assert block.count(
        'source_status = "DATA_OK"'
    ) == 2

    assert block.count(
        "Se escribirá cero"
    ) == 2


def test_errors_are_not_converted_to_zero():
    block = function_source(
        "execute_sync_comercial_abiertas_v2"
    )

    assert "SOURCE_ERROR: consulta SoftRestaurant" in block
    assert "de ventas cerradas falló con estado" in block
    assert (
        "de ventas cerradas no devolvió "
        in block
    )
    assert "un contrato válido" in block

    assert "SOURCE_ERROR: consulta MPRO" in block
    assert "de ventas cerradas falló con estado" in block

    assert "SOURCE_ERROR: ambas consultas MPRO" in block
    assert "devolvieron NULL" in block


def test_source_status_is_propagated():
    block = function_source(
        "execute_sync_comercial_abiertas_v2"
    )

    assert block.count(
        "source_status=source_status"
    ) == 2

    assert block.count(
        '"source_status": source_status'
    ) == 2
