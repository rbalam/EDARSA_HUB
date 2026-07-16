import pytest

from modules.finanzas import repository_cortes_caja_edarsahub as module


class BrokenConnection:
    def cursor(self, *args, **kwargs):
        raise RuntimeError("sql query failed")

    def close(self):
        pass


def test_connection_error_is_not_reported_as_empty(monkeypatch):
    def fail_connection():
        raise RuntimeError("sql unavailable")

    monkeypatch.setattr(module, "get_edarsahub_connection", fail_connection)

    repository = module.RepositoryCortesCajaEdarsahub()

    with pytest.raises(module.CortesCajaRepositoryError):
        repository.listar_cortes_caja()


def test_query_error_is_not_reported_as_empty(monkeypatch):
    monkeypatch.setattr(
        module,
        "get_edarsahub_connection",
        lambda: BrokenConnection(),
    )

    repository = module.RepositoryCortesCajaEdarsahub()

    with pytest.raises(module.CortesCajaRepositoryError):
        repository.listar_cortes_caja()


def test_all_servers_contract_reports_error(monkeypatch):
    repository = module.RepositoryCortesCajaEdarsahub()

    def fail_query(_filters):
        raise module.CortesCajaRepositoryError("sql unavailable")

    monkeypatch.setattr(repository, "listar_cortes_caja", fail_query)

    result = repository.obtener_cortes_todos_servidores()

    assert result["cortes"] == []
    assert result["estado_general"] == "EDARSAHUB_UNREACHABLE"
    assert result["source_status"] == "ERROR"
    assert result["fuentes_detalle"][0]["query_executed"] is False


def test_valid_empty_result_remains_success_empty(monkeypatch):
    repository = module.RepositoryCortesCajaEdarsahub()
    monkeypatch.setattr(repository, "listar_cortes_caja", lambda _filters: [])

    result = repository.obtener_cortes_todos_servidores()

    assert result["cortes"] == []
    assert result["estado_general"] == "SUCCESS_EMPTY"
    assert result["source_status"] == "FRESH"
    assert result["fuentes_detalle"][0]["query_executed"] is True
