from datetime import date
from unittest.mock import AsyncMock
import os

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

os.environ.setdefault("EDARSAHUB_SQL_HOST", "test.invalid")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "test_readonly")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "test_only_not_a_secret")
os.environ.setdefault("JWT_SECRET", "test_only_jwt_secret_not_for_runtime")

from modules.comercial_v2 import periodos_routes


def test_normaliza_periodos_duplicados():
    payload = [
        periodos_routes.PeriodoHistoricoSeleccionado(
            anio=2026,
            meses=[7, 8],
        ),
        periodos_routes.PeriodoHistoricoSeleccionado(
            anio=2026,
            meses=[7],
        ),
        periodos_routes.PeriodoHistoricoSeleccionado(
            anio=2025,
            meses=[12],
        ),
    ]

    assert periodos_routes._normalizar_periodos_historicos(payload) == [
        {"anio": 2026, "meses": [7, 8]},
        {"anio": 2025, "meses": [12]},
    ]


def test_where_sql_no_incluye_meses_intermedios():
    where_sql = periodos_routes._periodos_where_sql(
        [
            {"anio": 2026, "meses": [1]},
            {"anio": 2025, "meses": [7]},
        ],
        "k",
    )

    assert "YEAR(k.fecha_operacion) = 2026" in where_sql
    assert "MONTH(k.fecha_operacion) IN (1)" in where_sql
    assert "YEAR(k.fecha_operacion) = 2025" in where_sql
    assert "MONTH(k.fecha_operacion) IN (7)" in where_sql
    assert "BETWEEN" not in where_sql


def test_rechaza_mes_fuera_de_rango():
    with pytest.raises(ValidationError):
        periodos_routes.PeriodoHistoricoSeleccionado(
            anio=2026,
            meses=[13],
        )


def test_agregado_calcula_promedios_en_backend(monkeypatch):
    responses = iter([
        [{
            "dias": 2,
            "unidades_con_datos": 1,
            "fecha_min": date(2025, 7, 1),
            "fecha_max": date(2026, 1, 31),
            "ventas_total": 3000,
            "propinas_total": 300,
            "tickets_total": 3,
            "pax_total": 6,
        }],
        [{
            "unidad_negocio_pk": "pk-1",
            "unidad_negocio_codigo": "130MID",
            "unidad_negocio_nombre": "Unidad",
            "sistema_origen": "SOFT",
            "dias": 2,
            "ventas_total": 3000,
            "propinas_total": 300,
            "tickets_total": 3,
            "pax_total": 6,
        }],
    ])

    monkeypatch.setattr(
        periodos_routes,
        "_execute_readonly_query",
        lambda query: next(responses),
    )
    monkeypatch.setattr(
        periodos_routes,
        "_unidades_runtime_where_sql",
        lambda unidades: "1 = 1",
    )

    result = periodos_routes._consultar_periodos_agregados(
        periodos=[
            {"anio": 2026, "meses": [1]},
            {"anio": 2025, "meses": [7]},
        ],
        unidades=["130MID"],
    )

    assert result["totales"]["ventas_total"] == 3000
    assert result["totales"]["cheque_promedio"] == 1000
    assert result["totales"]["pax_promedio"] == 500
    assert result["unidades"][0]["ticket_promedio"] == 1000


@pytest.mark.asyncio
async def test_endpoint_no_incluye_overlay(monkeypatch):
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
        "_consultar_periodos_agregados",
        lambda periodos, unidades: {
            "totales": {},
            "unidades": [],
        },
    )

    payload = periodos_routes.PeriodosHistoricosRequest(
        periodos=[
            {"anio": 2026, "meses": [1]},
            {"anio": 2025, "meses": [7]},
        ]
    )

    response = await periodos_routes.obtener_periodos_agregados(
        payload=payload,
        current_user={"id": "test"},
    )

    data = response["data"]

    assert data["modo_periodo"] == "historical_periods"
    assert data["overlay_dia_actual_incluido"] is False
    assert data["trazabilidad"]["agregacion_frontend"] is False
    assert data["periodos_seleccionados"] == [
        {"anio": 2026, "meses": [1]},
        {"anio": 2025, "meses": [7]},
    ]
