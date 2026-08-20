from pathlib import Path

import pytest

from modules.compras.sync_service import (
    INVENTORY_SYNC_MODE_FULL,
    INVENTORY_SYNC_MODE_ROLLING_6M,
    _inventarios_fisicos_detalle_query,
    _inventory_history_filter,
)


BACKEND = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "column",
    [
        "F.Fi_Fecha",
        "FISICO.fecha",
        "INV.fecha",
    ],
)
def test_full_preserva_historia_completa(column):
    assert (
        _inventory_history_filter(
            column,
            INVENTORY_SYNC_MODE_FULL,
        )
        == f"{column} IS NOT NULL"
    )


@pytest.mark.parametrize(
    "column",
    [
        "F.Fi_Fecha",
        "FISICO.fecha",
        "INV.fecha",
    ],
)
def test_rolling_6m_limita_operacion(column):
    value = _inventory_history_filter(
        column,
        INVENTORY_SYNC_MODE_ROLLING_6M,
    )

    assert f"{column} IS NOT NULL" in value
    assert (
        f"{column} >= DATEADD(MONTH, -6, GETDATE())"
        in value
    )


def test_invalid_mode_fail_closed():
    with pytest.raises(ValueError):
        _inventory_history_filter(
            "INV.fecha",
            "INVALID",
        )


def test_softrestaurant_full_no_cutoff():
    query = _inventarios_fisicos_detalle_query(
        "SOFTRESTAURANT_PRO",
        sync_mode=INVENTORY_SYNC_MODE_FULL,
    )

    assert "FISICO.fecha IS NOT NULL" in query
    assert "DATEADD(MONTH, -6, GETDATE())" not in query
    assert "ISNULL(FISICO.cancelado, 0) = 0" in query


def test_softrestaurant_default_rolling():
    query = _inventarios_fisicos_detalle_query(
        "SOFTRESTAURANT_PRO",
    )

    assert (
        "FISICO.fecha >= DATEADD(MONTH, -6, GETDATE())"
        in query
    )


def test_mpro_full_preserva_sucursal():
    query = _inventarios_fisicos_detalle_query(
        "MPRO",
        sucursal_origen_id="0021",
        sync_mode=INVENTORY_SYNC_MODE_FULL,
    )

    assert "F.Fi_Fecha IS NOT NULL" in query
    assert "DATEADD(MONTH, -6, GETDATE())" not in query
    assert "F.Sc_Cve_Sucursal = '0021'" in query
    assert "ISNULL(F.Es_Cve_Estado, '') <> 'CA'" in query


def test_resync_manual_es_full_explicito():
    source = (
        BACKEND
        / "tools"
        / "resync_inventarios_fisicos.py"
    ).read_text(encoding="utf-8")

    assert "INVENTORY_SYNC_MODE_FULL" in source
    assert (
        "sync_mode=INVENTORY_SYNC_MODE_FULL"
        in source
    )


def test_scheduler_no_solicita_full():
    source = (
        BACKEND
        / "core"
        / "scheduler"
        / "jobs"
        / "sync_compras_job.py"
    ).read_text(encoding="utf-8")

    assert (
        "sync_inventarios_fisicos_from_server("
        in source
    )

    assert "INVENTORY_SYNC_MODE_FULL" not in source
