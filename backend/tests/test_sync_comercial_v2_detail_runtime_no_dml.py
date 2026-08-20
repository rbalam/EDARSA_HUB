import sys
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import pytest


MODULE = "core.scheduler.jobs.sync_comercial_v2_job"


class FakeSyncResult:
    def __init__(
        self,
        success=True,
        records_processed=1,
        records_inserted=1,
        records_updated=0,
        records_skipped=0,
        records_errored=0,
        duration_seconds=0.01,
        error_message=None,
    ):
        self.success = success
        self.records_processed = records_processed
        self.records_inserted = records_inserted
        self.records_updated = records_updated
        self.records_skipped = records_skipped
        self.records_errored = records_errored
        self.duration_seconds = duration_seconds
        self.error_message = error_message


class FakeUnidadNegocioConfig:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeSistemaOrigen:
    SOFTRESTAURANT = "SOFTRESTAURANT"
    MPRO = "MPRO"


@pytest.fixture
def fake_sync_module():
    fake = SimpleNamespace(
        sync_softrestaurant_ventas_cerradas=lambda **kwargs: FakeSyncResult(),
        sync_mpro_ventas_cerradas=lambda **kwargs: FakeSyncResult(),
        get_server_connection_config=lambda *args, **kwargs: {},
    )

    return fake


@pytest.fixture
def fake_schema_module():
    return SimpleNamespace(
        UnidadNegocioConfig=FakeUnidadNegocioConfig,
        SistemaOrigen=FakeSistemaOrigen,
    )


@pytest.fixture
def fake_detail_module():
    calls = []

    def get_unidades_negocio_pos(unidades=None):
        code = unidades[0]

        return [{
            "unidad_pk": "00000000-0000-0000-0000-000000000001",
            "unidad_codigo": code,
            "unidad_nombre": f"NOMBRE {code}",
            "server_id": "SERVER-1",
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
            "sucursal_origen_id": row["sucursal_origen_id"],
            "system_type": "SOFTRESTAURANT",
            "tipo_conexion": "SQL",
            "host": row["host"],
            "port": row["port"],
            "database": row["database_name"],
            "username": row["username"],
            "password": "mock-secret",
        }

    def _load_runtime_rows(fecha_inicio, fecha_fin, unidad):
        return [{
            "fecha_operacion": fecha_inicio,
            "unidad_negocio_id": unidad,
            "ventas_total": 100,
            "tickets_total": 1,
            "pax_total": 2,
        }]

    def _runtime_for(runtime_rows, cfg, dia):
        if not runtime_rows:
            return None

        return runtime_rows[0]

    def sync_detalle_producto_canonico_dia(
        cfg,
        dia,
        runtime_row,
        run_id,
        commit=False,
        excluir_abiertas=True,
    ):
        calls.append({
            "unidad": cfg["unidad_codigo"],
            "dia": dia,
            "run_id": run_id,
            "commit": commit,
            "excluir_abiertas": excluir_abiertas,
        })

        return {
            "status": "OK_HEADER_CANONICO",
            "unidad": cfg["unidad_codigo"],
            "fecha_operacion": dia,
            "filas_destino_preparadas": 7,
            "filas_insertadas": 0 if not commit else 7,
        }

    module = SimpleNamespace(
        get_unidades_negocio_pos=get_unidades_negocio_pos,
        get_pos_config_for_unidad=get_pos_config_for_unidad,
        _load_runtime_rows=_load_runtime_rows,
        _runtime_for=_runtime_for,
        sync_detalle_producto_canonico_dia=
            sync_detalle_producto_canonico_dia,
        calls=calls,
    )

    return module


def _fake_units():
    return (
        [{
            "unidad_negocio_id": "TEST_SR",
            "unidad_negocio_pk":
                "00000000-0000-0000-0000-000000000001",
            "nombre": "TEST SR",
            "server_id": "SERVER-1",
            "sucursal_id": None,
            "sistema": "SOFTRESTAURANT",
        }],
        [],
    )


@pytest.mark.asyncio
async def test_header_success_runs_detail_with_commit_false(
    fake_sync_module,
    fake_schema_module,
    fake_detail_module,
):
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

        with patch.object(
            job,
            "_get_unidades_from_edarsahub",
            side_effect=_fake_units,
        ):
            with patch.object(
                job,
                "SYNC_INCREMENTAL_DAYS",
                0,
            ):
                result = await job.execute_sync_comercial_v2(
                    detail_commit=False,
                )

        assert result["unidades_procesadas"] == 1
        assert result["unidades_exitosas"] == 1
        assert result["unidades_fallidas"] == 0

        assert len(fake_detail_module.calls) == 1

        call = fake_detail_module.calls[0]

        assert call["unidad"] == "TEST_SR"
        assert call["commit"] is False
        assert call["excluir_abiertas"] is True

        assert result["detalle_producto_exitosos"] == 1
        assert result["detalle_producto_fallidos"] == 0
        assert result["detalle_producto_filas_insertadas"] == 0

        unit = result["detalles_unidades"][0]

        assert unit["estatus"] == "SUCCESS"
        assert unit["detalle_producto_status"] == "OK_HEADER_CANONICO"

        assert len(unit["detalle_producto_dias"]) == 1

        trace = unit["detalle_producto_dias"][0]

        assert trace["status"] == "OK_HEADER_CANONICO"
        assert trace["filas_preparadas"] == 7
        assert trace["filas_insertadas"] == 0

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


@pytest.mark.asyncio
async def test_failed_header_does_not_run_detail(
    fake_sync_module,
    fake_schema_module,
    fake_detail_module,
):
    fake_sync_module.sync_softrestaurant_ventas_cerradas = (
        lambda **kwargs: FakeSyncResult(
            success=False,
            records_processed=1,
            records_inserted=0,
            records_errored=1,
            error_message="HEADER_FAIL",
        )
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

        with patch.object(
            job,
            "_get_unidades_from_edarsahub",
            side_effect=_fake_units,
        ):
            with patch.object(
                job,
                "SYNC_INCREMENTAL_DAYS",
                0,
            ):
                result = await job.execute_sync_comercial_v2(
                    detail_commit=False,
                )

        assert result["unidades_procesadas"] == 1
        assert result["unidades_exitosas"] == 0
        assert result["unidades_fallidas"] == 1

        assert fake_detail_module.calls == []

        unit = result["detalles_unidades"][0]

        assert unit["estatus"] == "FAILED"
        assert "detalle_producto_dias" not in unit

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


@pytest.mark.asyncio
async def test_detail_failure_does_not_invalidate_successful_header(
    fake_sync_module,
    fake_schema_module,
    fake_detail_module,
):
    def fail_detail(
        cfg,
        dia,
        runtime_row,
        run_id,
        commit=False,
        excluir_abiertas=True,
    ):
        raise RuntimeError("DETAIL_FAIL")

    fake_detail_module.sync_detalle_producto_canonico_dia = (
        fail_detail
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

        with patch.object(
            job,
            "_get_unidades_from_edarsahub",
            side_effect=_fake_units,
        ):
            with patch.object(
                job,
                "SYNC_INCREMENTAL_DAYS",
                0,
            ):
                result = await job.execute_sync_comercial_v2(
                    detail_commit=False,
                )

        assert result["unidades_exitosas"] == 1
        assert result["unidades_fallidas"] == 0

        assert result["detalle_producto_exitosos"] == 0
        assert result["detalle_producto_fallidos"] == 1

        unit = result["detalles_unidades"][0]

        assert unit["estatus"] == "SUCCESS"
        assert unit["detalle_producto_status"] == "ERROR"
        assert unit["detalle_producto_error"] == "DETAIL_FAIL"

        assert len(unit["detalle_producto_dias"]) == 1

        trace = unit["detalle_producto_dias"][0]

        assert trace["status"] == "ERROR"
        assert trace["error"] == "DETAIL_FAIL"
        assert trace["filas_insertadas"] == 0

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
