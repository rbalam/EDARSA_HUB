from unittest.mock import patch

from modules.sync_recetas import sync_recetas


def _config(*, dry_run=False):
    return sync_recetas.SyncRecetasConfig(
        server_ids=[],
        sync_familias=False,
        sync_productos=False,
        sync_insumos=False,
        sync_recetas=True,
        sync_elaborados=False,
        dry_run=dry_run,
    )


def _result():
    return {
        "familias": 0,
        "subfamilias": 0,
        "productos": 0,
        "productos_con_receta": 0,
        "insumos": 0,
        "lineas_receta": 0,
        "elaborados": 0,
        "insertados": 0,
        "actualizados": 0,
        "errores_count": 0,
        "errores": [],
        "warnings": [],
    }


def test_soft_valid_empty_snapshot_calls_reconciliation():
    result = _result()

    with (
        patch.object(
            sync_recetas,
            "_obtener_recetas_sr",
            return_value=[],
        ),
        patch.object(
            sync_recetas,
            "_guardar_recetas",
        ) as guardar,
        patch.object(
            sync_recetas,
            "_obtener_compuestos_sr",
            return_value=[],
        ),
    ):
        sync_recetas._sync_softrestaurant(
            server_id="S1",
            host="host",
            port=1433,
            database="db",
            username="user",
            password="pwd",
            system_type="SOFTRESTAURANT_PRO",
            config=_config(dry_run=False),
            sync_run_id="RUN-1",
            result=result,
        )

    guardar.assert_called_once_with(
        "S1",
        "SOFTRESTAURANT_PRO",
        [],
        "RUN-1",
        result,
    )


def test_mpro_valid_empty_snapshot_calls_reconciliation():
    result = _result()

    with (
        patch.object(
            sync_recetas,
            "_obtener_recetas_mpro",
            return_value=[],
        ),
        patch.object(
            sync_recetas,
            "_guardar_recetas",
        ) as guardar,
        patch.object(
            sync_recetas,
            "_obtener_compuestos_mpro",
            return_value=[],
        ),
    ):
        sync_recetas._sync_mpro(
            server_id="S2",
            host="host",
            port=1433,
            database="db",
            username="user",
            password="pwd",
            system_type="MPRO",
            config=_config(dry_run=False),
            sync_run_id="RUN-2",
            result=result,
        )

    guardar.assert_called_once_with(
        "S2",
        "MPRO",
        [],
        "RUN-2",
        result,
    )


def test_soft_failed_extraction_never_reconciles():
    result = _result()

    with (
        patch.object(
            sync_recetas,
            "_obtener_recetas_sr",
            side_effect=RuntimeError("POS offline"),
        ),
        patch.object(
            sync_recetas,
            "_guardar_recetas",
        ) as guardar,
    ):
        try:
            sync_recetas._sync_softrestaurant(
                server_id="S1",
                host="host",
                port=1433,
                database="db",
                username="user",
                password="pwd",
                system_type="SOFTRESTAURANT_PRO",
                config=_config(dry_run=False),
                sync_run_id="RUN-3",
                result=result,
            )
        except RuntimeError as exc:
            assert "POS offline" in str(exc)
        else:
            raise AssertionError(
                "Expected RuntimeError"
            )

    guardar.assert_not_called()


def test_mpro_failed_extraction_never_reconciles():
    result = _result()

    with (
        patch.object(
            sync_recetas,
            "_obtener_recetas_mpro",
            side_effect=RuntimeError("query failed"),
        ),
        patch.object(
            sync_recetas,
            "_guardar_recetas",
        ) as guardar,
    ):
        try:
            sync_recetas._sync_mpro(
                server_id="S2",
                host="host",
                port=1433,
                database="db",
                username="user",
                password="pwd",
                system_type="MPRO",
                config=_config(dry_run=False),
                sync_run_id="RUN-4",
                result=result,
            )
        except RuntimeError as exc:
            assert "query failed" in str(exc)
        else:
            raise AssertionError(
                "Expected RuntimeError"
            )

    guardar.assert_not_called()


def test_dry_run_empty_snapshot_does_not_write():
    result = _result()

    with (
        patch.object(
            sync_recetas,
            "_obtener_recetas_sr",
            return_value=[],
        ),
        patch.object(
            sync_recetas,
            "_guardar_recetas",
        ) as guardar,
        patch.object(
            sync_recetas,
            "_obtener_compuestos_sr",
            return_value=[],
        ),
    ):
        sync_recetas._sync_softrestaurant(
            server_id="S1",
            host="host",
            port=1433,
            database="db",
            username="user",
            password="pwd",
            system_type="SOFTRESTAURANT_PRO",
            config=_config(dry_run=True),
            sync_run_id="RUN-5",
            result=result,
        )

    guardar.assert_not_called()
