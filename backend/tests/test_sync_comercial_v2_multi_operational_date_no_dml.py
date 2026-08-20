import sys
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import pytest


class FakeSyncResult:
    def __init__(self, success=True):
        self.success = success
        self.records_processed = 1
        self.records_inserted = 1
        self.records_updated = 0
        self.records_skipped = 0
        self.records_errored = 0
        self.duration_seconds = 0.01
        self.error_message = None


class FakeUnidadNegocioConfig:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeSistemaOrigen:
    SOFTRESTAURANT = "SOFTRESTAURANT"
    MPRO = "MPRO"


def _fake_units():
    return (
        [
            {
                "unidad_negocio_pk":
                    "11111111-1111-1111-1111-111111111111",
                "unidad_negocio_id": "UNIT_A",
                "nombre": "UNIT A",
                "server_id": "SERVER_A",
                "sucursal_id": None,
                "sistema": "SOFTRESTAURANT",
            },
            {
                "unidad_negocio_pk":
                    "22222222-2222-2222-2222-222222222222",
                "unidad_negocio_id": "UNIT_B",
                "nombre": "UNIT B",
                "server_id": "SERVER_B",
                "sucursal_id": None,
                "sistema": "SOFTRESTAURANT",
            },
        ],
        [],
    )


@pytest.mark.asyncio
async def test_each_unit_uses_its_own_operational_end_date():
    header_calls = []
    detail_calls = []

    fake_sync_module = SimpleNamespace()

    def fake_header_sync(
        config,
        fecha_inicio,
        fecha_fin,
        run_id,
    ):
        header_calls.append({
            "unidad": config.unidad_negocio_nombre,
            "pk": config.unidad_negocio_pk,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "run_id": run_id,
        })

        return FakeSyncResult(
            success=True,
        )

    fake_sync_module.sync_softrestaurant_ventas_cerradas = (
        fake_header_sync
    )

    fake_sync_module.sync_mpro_ventas_cerradas = (
        lambda **kwargs: FakeSyncResult(
            success=True
        )
    )

    fake_sync_module.get_server_connection_config = (
        lambda *args, **kwargs: {}
    )

    fake_schema_module = SimpleNamespace(
        UnidadNegocioConfig=FakeUnidadNegocioConfig,
        SistemaOrigen=FakeSistemaOrigen,
    )

    def get_unidades_negocio_pos(unidades=None):
        code = unidades[0]

        if code == "UNIT_A":
            pk = (
                "11111111-1111-1111-1111-111111111111"
            )
        elif code == "UNIT_B":
            pk = (
                "22222222-2222-2222-2222-222222222222"
            )
        else:
            raise AssertionError(
                f"UNEXPECTED_UNIT={code}"
            )

        return [{
            "unidad_pk": pk,
            "unidad_codigo": code,
            "unidad_nombre": code,
            "server_id": f"SERVER_{code}",
            "unidad_system_type": "SoftRestaurant",
            "servidor_system_type": "SoftRestaurant",
            "sucursal_origen_id": None,
            "tipo_conexion": "SQL",
            "host": "mock-host",
            "port": 1433,
            "database_name": "mock-db",
            "username": "mock-user",
            "password_encrypted": "mock-secret",
        }]

    def get_pos_config_for_unidad(row):
        return {
            "unidad_pk": row["unidad_pk"],
            "unidad_codigo": row["unidad_codigo"],
            "unidad_nombre": row["unidad_nombre"],
            "server_id": row["server_id"],
            "sucursal_origen_id": None,
            "system_type": "SOFTRESTAURANT",
            "tipo_conexion": "SQL",
            "host": "mock-host",
            "port": 1433,
            "database": "mock-db",
            "username": "mock-user",
            "password": "mock-secret",
        }

    def _load_runtime_rows(
        fecha_inicio,
        fecha_fin,
        unidad,
    ):
        return [{
            "fecha_operacion": fecha_inicio,
            "unidad_negocio_id": unidad,
            "ventas_total": 100,
            "tickets_total": 1,
            "pax_total": 2,
        }]

    def _runtime_for(
        runtime_rows,
        cfg,
        dia,
    ):
        return runtime_rows[0]

    def sync_detalle_producto_canonico_dia(
        cfg,
        dia,
        runtime_row,
        run_id,
        commit=False,
        excluir_abiertas=True,
    ):
        detail_calls.append({
            "unidad": cfg["unidad_codigo"],
            "dia": dia,
            "run_id": run_id,
            "commit": commit,
        })

        return {
            "status": "OK_HEADER_CANONICO",
            "fecha_operacion": dia,
            "filas_destino_preparadas": 5,
            "filas_insertadas": 0,
        }

    fake_detail_module = SimpleNamespace(
        get_unidades_negocio_pos=
            get_unidades_negocio_pos,
        get_pos_config_for_unidad=
            get_pos_config_for_unidad,
        _load_runtime_rows=
            _load_runtime_rows,
        _runtime_for=
            _runtime_for,
        sync_detalle_producto_canonico_dia=
            sync_detalle_producto_canonico_dia,
    )

    original_sync = sys.modules.get(
        "modules.comercial_v2.sync_comercial_edarsahub"
    )
    original_schema = sys.modules.get(
        "modules.comercial_v2.schemas"
    )
    original_detail = sys.modules.get(
        "scripts.poblar_ventas_detalle_producto_canonico"
    )

    sys.modules[
        "modules.comercial_v2.sync_comercial_edarsahub"
    ] = fake_sync_module

    sys.modules[
        "modules.comercial_v2.schemas"
    ] = fake_schema_module

    sys.modules[
        "scripts.poblar_ventas_detalle_producto_canonico"
    ] = fake_detail_module

    try:
        import core.scheduler.jobs.sync_comercial_v2_job as job

        operational_dates = {
            "11111111-1111-1111-1111-111111111111":
                date(2026, 8, 17),
            "22222222-2222-2222-2222-222222222222":
                date(2026, 8, 18),
        }

        def fake_get_fecha_operacion(pk):
            return operational_dates[pk]

        with patch.object(
            job,
            "_get_unidades_from_edarsahub",
            side_effect=_fake_units,
        ):
            with patch.object(
                job,
                "get_fecha_operacion",
                side_effect=fake_get_fecha_operacion,
            ):
                with patch.object(
                    job,
                    "SYNC_INCREMENTAL_DAYS",
                    3,
                ):
                    result = await job.execute_sync_comercial_v2(
                        detail_commit=False,
                    )

        assert result["unidades_procesadas"] == 2
        assert result["unidades_exitosas"] == 2
        assert result["unidades_fallidas"] == 0

        assert len(header_calls) == 2

        by_pk = {
            row["pk"]: row
            for row in header_calls
        }

        a = by_pk[
            "11111111-1111-1111-1111-111111111111"
        ]
        b = by_pk[
            "22222222-2222-2222-2222-222222222222"
        ]

        assert a["fecha_fin"] == date(
            2026, 8, 17
        )
        assert a["fecha_inicio"] == date(
            2026, 8, 14
        )

        assert b["fecha_fin"] == date(
            2026, 8, 18
        )
        assert b["fecha_inicio"] == date(
            2026, 8, 15
        )

        # 4 días inclusivos por unidad.
        assert len(detail_calls) == 8

        detail_a = [
            x["dia"]
            for x in detail_calls
            if x["unidad"] == "UNIT_A"
        ]

        detail_b = [
            x["dia"]
            for x in detail_calls
            if x["unidad"] == "UNIT_B"
        ]

        assert detail_a == [
            date(2026, 8, 14),
            date(2026, 8, 15),
            date(2026, 8, 16),
            date(2026, 8, 17),
        ]

        assert detail_b == [
            date(2026, 8, 15),
            date(2026, 8, 16),
            date(2026, 8, 17),
            date(2026, 8, 18),
        ]

        assert all(
            call["commit"] is False
            for call in detail_calls
        )

        details = {
            item["unidad_negocio_id"]: item
            for item in result["detalles_unidades"]
        }

        assert details["UNIT_A"]["fecha_inicio"] == (
            "2026-08-14"
        )
        assert details["UNIT_A"]["fecha_fin"] == (
            "2026-08-17"
        )

        assert details["UNIT_B"]["fecha_inicio"] == (
            "2026-08-15"
        )
        assert details["UNIT_B"]["fecha_fin"] == (
            "2026-08-18"
        )

        assert (
            result["rango_fecha_operacion_por_unidad"]
            is True
        )

        assert result["fecha_inicio"] is None
        assert result["fecha_fin"] is None

    finally:
        if original_sync is None:
            sys.modules.pop(
                "modules.comercial_v2.sync_comercial_edarsahub",
                None,
            )
        else:
            sys.modules[
                "modules.comercial_v2.sync_comercial_edarsahub"
            ] = original_sync

        if original_schema is None:
            sys.modules.pop(
                "modules.comercial_v2.schemas",
                None,
            )
        else:
            sys.modules[
                "modules.comercial_v2.schemas"
            ] = original_schema

        if original_detail is None:
            sys.modules.pop(
                "scripts.poblar_ventas_detalle_producto_canonico",
                None,
            )
        else:
            sys.modules[
                "scripts.poblar_ventas_detalle_producto_canonico"
            ] = original_detail
