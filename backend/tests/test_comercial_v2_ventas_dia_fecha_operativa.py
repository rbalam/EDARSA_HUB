import os

os.environ.setdefault("EDARSAHUB_SQL_HOST", "localhost")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "test")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "test")
os.environ.setdefault(
    "JWT_SECRET",
    "test-only-secret-not-for-production",
)

import asyncio
from datetime import date

import pytest
from fastapi import HTTPException

from modules.comercial_v2 import routes


def _comparativos_vacios():
    return {
        "dia_anterior": {
            "ventas": 0,
            "pax": 0,
            "cheques": 0,
        },
        "dia_anio_ant": {
            "ventas": 0,
            "pax": 0,
            "cheques": 0,
        },
    }


def _fila(unidad: str, fecha_operacion: date):
    return {
        "unidad_negocio_pk": unidad,
        "unidad_negocio_codigo": unidad,
        "unidad_negocio_id": unidad,
        "unidad_negocio_nombre": unidad,
        "fecha_operacion": fecha_operacion,
        "server_id": f"SERVER-{unidad}",
        "sistema_origen": "TEST",
        "ventas_abiertas": 100,
        "tickets_abiertos": 1,
        "pax_abiertos": 2,
        "ventas_cerradas_dia": 200,
        "tickets_cerrados_dia": 2,
        "pax_cerrados_dia": 3,
        "total_estimado_dia": 300,
        "snapshot_timestamp": None,
        "fuente_original": "TEST_SQL",
        "sync_run_id": "TEST-RUN",
    }


def test_scope_vacio_falla_cerrado_antes_de_consultar_repositorio():
    with pytest.raises(HTTPException) as exc_info:
        routes._require_unidades_permitidas([])

    assert exc_info.value.status_code == 403


def test_scope_explicito_se_conserva_para_filtrar_repositorio():
    unidades = ["130QRO"]

    assert routes._require_unidades_permitidas(unidades) is unidades


def test_repositorio_no_consulta_cuando_scope_es_vacio():
    assert routes.get_unidades_disponibles([]) == []
    assert routes.get_sync_status([], limit=50) == []
    assert routes.get_last_sync_by_unidad([]) == []


def test_ventas_dia_conserva_fecha_operativa_por_unidad(
    monkeypatch,
):
    async def unidades_permitidas(_current_user):
        return ["U1", "U2", "U3"]

    fechas_motor = {
        "U1": date(2026, 7, 12),
        "U2": date(2026, 7, 11),
    }

    def fecha_operacion_now(unidad):
        if unidad == "U3":
            raise RuntimeError("motor operativo no disponible")

        return fechas_motor[unidad]

    def ultimas_fechas_sql(unidades):
        assert unidades == ["U1", "U2", "U3"]
        return {
            "U3": date(2026, 7, 10),
        }

    llamadas_consulta = []

    def ventas_dia(fecha_operacion, unidades):
        llamadas_consulta.append(
            (fecha_operacion, tuple(unidades))
        )

        return [
            _fila(unidad, fecha_operacion)
            for unidad in unidades
        ]

    llamadas_comparativos = []

    def comparativos(unidad, fecha_operacion):
        llamadas_comparativos.append(
            (unidad, fecha_operacion)
        )
        return _comparativos_vacios()

    monkeypatch.setattr(
        routes,
        "get_unidades_permitidas_v2",
        unidades_permitidas,
    )
    monkeypatch.setattr(
        routes,
        "get_ultimas_fechas_operacion_abiertas",
        ultimas_fechas_sql,
    )
    monkeypatch.setattr(
        routes,
        "get_ventas_dia_abiertas",
        ventas_dia,
    )
    monkeypatch.setattr(
        routes,
        "get_comparativos_diarios",
        comparativos,
    )
    monkeypatch.setattr(
        routes,
        "_resolver_unidad_codigo_runtime",
        lambda unidad: unidad,
    )

    from core.utils import operational_window

    monkeypatch.setattr(
        operational_window,
        "get_fecha_operacion_now",
        fecha_operacion_now,
    )

    response = asyncio.run(
        routes.comercial_v2_ventas_dia(
            fecha=None,
            current_user={"id": "TEST"},
        )
    )

    assert response.fecha == "2026-07-12"
    assert response.data["fecha_operacion"] == "2026-07-12"

    assert response.data["fechas_operacion"] == [
        "2026-07-10",
        "2026-07-11",
        "2026-07-12",
    ]

    assert response.data["fecha_operacion_multiple"] is True

    fechas_por_unidad = {
        fila["unidad_negocio_codigo"]: fila["fecha_operacion"]
        for fila in response.data["por_unidad"]
    }

    assert fechas_por_unidad == {
        "U1": "2026-07-12",
        "U2": "2026-07-11",
        "U3": "2026-07-10",
    }

    assert set(llamadas_comparativos) == {
        ("U1", date(2026, 7, 12)),
        ("U2", date(2026, 7, 11)),
        ("U3", date(2026, 7, 10)),
    }

    assert set(llamadas_consulta) == {
        (date(2026, 7, 12), ("U1",)),
        (date(2026, 7, 11), ("U2",)),
        (date(2026, 7, 10), ("U3",)),
    }


def test_ventas_dia_sin_fecha_canonica_ni_sql_devuelve_503(
    monkeypatch,
):
    async def unidades_permitidas(_current_user):
        return ["U404"]

    def fecha_operacion_now(_unidad):
        raise RuntimeError("motor operativo no disponible")

    monkeypatch.setattr(
        routes,
        "get_unidades_permitidas_v2",
        unidades_permitidas,
    )
    monkeypatch.setattr(
        routes,
        "get_ultimas_fechas_operacion_abiertas",
        lambda _unidades: {},
    )
    monkeypatch.setattr(
        routes,
        "_resolver_unidad_codigo_runtime",
        lambda unidad: unidad,
    )

    from core.utils import operational_window

    monkeypatch.setattr(
        operational_window,
        "get_fecha_operacion_now",
        fecha_operacion_now,
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            routes.comercial_v2_ventas_dia(
                fecha=None,
                current_user={"id": "TEST"},
            )
        )

    assert exc_info.value.status_code == 503

    assert (
        exc_info.value.detail["error"]
        == "FECHA_OPERACION_NO_DISPONIBLE"
    )

    assert exc_info.value.detail[
        "unidades_sin_fecha_operativa"
    ] == ["U404"]
