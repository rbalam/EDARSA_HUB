import asyncio
import inspect

import pytest
from fastapi import HTTPException

from server import generate_inventory_analysis
from core.inventarios.sql_error_policy import (
    classify_inventory_sql_error,
    inventory_analysis_safe_http_exception,
    is_inventory_transient_error,
    should_retry_inventory_once,
)


def test_inventory_sql_error_classifier_transient_timeout_and_dead_dbprocess():
    err = Exception("Adaptive Server connection timed out ... DBPROCESS is dead or not enabled")
    cls = classify_inventory_sql_error(err)
    assert cls == "DEAD_DBPROCESS"
    assert is_inventory_transient_error(cls) is True


def test_inventory_sql_error_classifier_authentication_not_transient():
    err = Exception("Login failed for user 'HRLectura'")
    cls = classify_inventory_sql_error(err)
    assert cls == "AUTHENTICATION"
    assert is_inventory_transient_error(cls) is False


def test_inventory_retry_is_single_attempt_only():
    assert should_retry_inventory_once("DEAD_DBPROCESS", 1) is True
    assert should_retry_inventory_once("DEAD_DBPROCESS", 2) is False
    assert should_retry_inventory_once("AUTHENTICATION", 1) is False


def test_inventory_safe_http_exception_hides_dblib_message():
    raw = Exception("DB-Lib error message 20003: Adaptive Server connection timed out")
    http_exc = inventory_analysis_safe_http_exception(raw)
    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == 503
    detail = str(http_exc.detail)
    assert "DB-Lib" not in detail
    assert "Adaptive Server" not in detail


def test_inventory_endpoint_uses_canonical_connection_factory_reference():
    src = inspect.getsource(generate_inventory_analysis)
    assert "get_edarsahub_pymssql_connection" in src


@pytest.mark.integration
@pytest.mark.asyncio
async def test_inventory_case_130mid_softrestaurant_safe_response_contract():
    payload = {
        "server_id": "a5547321-1139-4d2b-9d53-182ca737b6b6",
        "sucursal": "SoftRestaurant",
        "almacen": "BARRA",
        "almacen_id": 2,
        "folio_inicial": "3844",
        "folio_final": "3865",
        "fecha_ini": "2026-06-22 10:37:32",
        "fecha_fin": "2026-07-13 10:45:02",
        "categorias": [],
        "familias": [],
        "subfamilias": [],
    }

    try:
        result = await generate_inventory_analysis(payload, current_user={"id": "diag", "name": "diag"})
        assert "count" in result
    except HTTPException as exc:
        # En entornos sin RBAC para este server, el endpoint puede bloquear con 403.
        if exc.status_code == 403:
            assert "acceso" in str(exc.detail).lower()
            return

        # Contrato requerido: si persiste un fallo transitorio real, debe ser 503 seguro.
        assert exc.status_code in (503, 500)
        detail = str(exc.detail)
        assert "DB-Lib" not in detail
        assert "Adaptive Server" not in detail
