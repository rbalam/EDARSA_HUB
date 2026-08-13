from types import SimpleNamespace
from unittest.mock import patch

from modules.sync_recetas import sync_recetas


def _base_server_result(
    *,
    errores_count=0,
    errores=None,
):
    return {
        "server_id": "SERVER",
        "server_name": "SERVER",
        "system_type": "SOFTRESTAURANT_PRO",
        "familias": 0,
        "subfamilias": 0,
        "productos": 0,
        "productos_con_receta": 0,
        "insumos": 0,
        "lineas_receta": 0,
        "elaborados": 0,
        "insertados": 0,
        "actualizados": 0,
        "errores_count": errores_count,
        "errores": errores or [],
        "warnings": [],
    }


def _config():
    return sync_recetas.SyncRecetasConfig(
        server_ids=[],
        sync_familias=False,
        sync_productos=False,
        sync_insumos=False,
        sync_recetas=False,
        sync_elaborados=False,
        dry_run=True,
    )


def _server(server_id, name):
    return {
        "id": server_id,
        "name": name,
        "nombre": name,
        "system_type": "SOFTRESTAURANT_PRO",
    }


def test_all_servers_clean_is_success():
    servers = [
        _server("S1", "UNO"),
        _server("S2", "DOS"),
    ]

    def fake_sync(server, config, sync_run_id):
        result = _base_server_result()
        result["server_id"] = server["id"]
        result["server_name"] = server["name"]
        return result

    with (
        patch.object(
            sync_recetas,
            "_get_servers_from_sql",
            return_value=servers,
        ),
        patch.object(
            sync_recetas,
            "_sync_servidor",
            side_effect=fake_sync,
        ),
    ):
        result = sync_recetas._ejecutar_sync(
            _config()
        )

    assert result.success is True
    assert result.servidores_exitosos == 2
    assert result.servidores_con_error == 0
    assert result.registros_error == 0


def test_internal_server_error_makes_run_unsuccessful():
    servers = [
        _server("S1", "UNO"),
        _server("S2", "DOS"),
    ]

    def fake_sync(server, config, sync_run_id):
        if server["id"] == "S2":
            result = _base_server_result(
                errores_count=1,
                errores=["query failed"],
            )
        else:
            result = _base_server_result()

        result["server_id"] = server["id"]
        result["server_name"] = server["name"]
        return result

    with (
        patch.object(
            sync_recetas,
            "_get_servers_from_sql",
            return_value=servers,
        ),
        patch.object(
            sync_recetas,
            "_sync_servidor",
            side_effect=fake_sync,
        ),
    ):
        result = sync_recetas._ejecutar_sync(
            _config()
        )

    assert result.success is False
    assert result.servidores_exitosos == 1
    assert result.servidores_con_error == 1
    assert result.registros_error == 1


def test_exception_server_makes_run_unsuccessful():
    servers = [
        _server("S1", "UNO"),
        _server("S2", "DOS"),
    ]

    def fake_sync(server, config, sync_run_id):
        if server["id"] == "S2":
            raise RuntimeError("POS offline")

        result = _base_server_result()
        result["server_id"] = server["id"]
        result["server_name"] = server["name"]
        return result

    with (
        patch.object(
            sync_recetas,
            "_get_servers_from_sql",
            return_value=servers,
        ),
        patch.object(
            sync_recetas,
            "_sync_servidor",
            side_effect=fake_sync,
        ),
    ):
        result = sync_recetas._ejecutar_sync(
            _config()
        )

    assert result.success is False
    assert result.servidores_exitosos == 1
    assert result.servidores_con_error == 1
    assert any(
        "POS offline" in str(error)
        for error in result.errores
    )
