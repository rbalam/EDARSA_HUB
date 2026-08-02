from datetime import date
from unittest.mock import AsyncMock
import os

import pytest
from fastapi import HTTPException

# Configuración ficticia exclusiva para importación del test.
# No abre conexiones ni utiliza secretos reales.
os.environ.setdefault("EDARSAHUB_SQL_HOST", "test.invalid")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "test_readonly")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "test_only_not_a_secret")

from modules.comercial_v2 import periodos_routes


def test_consultar_periodos_disponibles_agrupa_por_anio_y_mes(monkeypatch):
    rows = [
        {
            "anio": 2026,
            "mes": 7,
            "fecha_inicio": date(2026, 7, 1),
            "fecha_fin": date(2026, 7, 31),
            "dias_disponibles": 31,
        },
        {
            "anio": 2026,
            "mes": 8,
            "fecha_inicio": date(2026, 8, 1),
            "fecha_fin": date(2026, 8, 1),
            "dias_disponibles": 1,
        },
        {
            "anio": 2025,
            "mes": 12,
            "fecha_inicio": date(2025, 12, 1),
            "fecha_fin": date(2025, 12, 31),
            "dias_disponibles": 31,
        },
    ]

    monkeypatch.setattr(
        periodos_routes,
        "_execute_readonly_query",
        lambda query: rows,
    )
    monkeypatch.setattr(
        periodos_routes,
        "_unidades_runtime_where_sql",
        lambda unidades: "unidad_negocio_id IN ('130MID')",
    )

    result = periodos_routes._consultar_periodos_disponibles(
        unidades=["130MID"],
    )

    assert result["total_anios"] == 2
    assert result["total_periodos"] == 3
    assert result["fecha_minima"] == "2025-12-01"
    assert result["fecha_maxima"] == "2026-08-01"

    assert result["anios"][0]["anio"] == 2026
    assert [
        item["mes"]
        for item in result["anios"][0]["meses"]
    ] == [7, 8]

    assert result["anios"][1]["anio"] == 2025
    assert result["anios"][1]["meses"][0]["mes"] == 12


def test_consultar_periodos_disponibles_vacio(monkeypatch):
    monkeypatch.setattr(
        periodos_routes,
        "_execute_readonly_query",
        lambda query: [],
    )
    monkeypatch.setattr(
        periodos_routes,
        "_unidades_runtime_where_sql",
        lambda unidades: "1 = 1",
    )

    result = periodos_routes._consultar_periodos_disponibles(
        unidades=["A"],
    )

    assert result["anios"] == []
    assert result["fecha_minima"] is None
    assert result["fecha_maxima"] is None
    assert result["total_anios"] == 0
    assert result["total_periodos"] == 0

    traceability = result["traceability"]

    assert traceability["source"] == (
        "vw_Comercial_KPIs_Diarios_v2_Runtime"
    )
    assert traceability["temporal_field"] == "fecha_operacion"
    assert traceability["live"] is False
    assert traceability["mongodb"] is False
    assert traceability["hardcode"] is False
    assert traceability["units"] == ["A"]


@pytest.mark.asyncio
async def test_endpoint_periodos_disponibles_respeta_rbac(monkeypatch):
    monkeypatch.setattr(
        periodos_routes,
        "get_unidades_permitidas_v2",
        AsyncMock(return_value=["130MID"]),
    )
    monkeypatch.setattr(
        periodos_routes,
        "_require_unidades_permitidas",
        lambda unidades: unidades,
    )
    monkeypatch.setattr(
        periodos_routes,
        "_scope_unidades",
        lambda permitidas, solicitada: ["130MID"],
    )
    monkeypatch.setattr(
        periodos_routes,
        "_consultar_periodos_disponibles",
        lambda unidades: {
            "anios": [],
            "fecha_minima": None,
            "fecha_maxima": None,
            "total_anios": 0,
            "total_periodos": 0,
        },
    )

    response = await periodos_routes.obtener_periodos_disponibles(
        unidad_negocio_pk=None,
        current_user={"id": "test"},
    )

    assert response["success"] is True
    assert response["data"]["trazabilidad"]["hardcode"] is False
    assert response["data"]["trazabilidad"]["campo_temporal"] == (
        "fecha_operacion"
    )
    assert response["data"]["trazabilidad"]["unidades_rbac"] == [
        "130MID"
    ]


@pytest.mark.asyncio
async def test_endpoint_periodos_disponibles_propaga_http_exception(
    monkeypatch,
):
    monkeypatch.setattr(
        periodos_routes,
        "get_unidades_permitidas_v2",
        AsyncMock(return_value=["130MID"]),
    )
    monkeypatch.setattr(
        periodos_routes,
        "_require_unidades_permitidas",
        lambda unidades: unidades,
    )

    def raise_forbidden(permitidas, solicitada):
        raise HTTPException(status_code=403, detail="Sin acceso")

    monkeypatch.setattr(
        periodos_routes,
        "_scope_unidades",
        raise_forbidden,
    )

    with pytest.raises(HTTPException) as error:
        await periodos_routes.obtener_periodos_disponibles(
            unidad_negocio_pk="OTRA",
            current_user={"id": "test"},
        )

    assert error.value.status_code == 403
