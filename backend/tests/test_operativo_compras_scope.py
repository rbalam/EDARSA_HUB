import os

os.environ.setdefault("EDARSAHUB_SQL_HOST", "unit-test.invalid")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB_UNIT_TEST")
os.environ.setdefault("EDARSAHUB_SQL_USER", "UNIT_TEST_READONLY")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "UNIT_TEST_NOT_A_SECRET")

from modules.fase2_operativo import access
from modules.fase2_operativo.services import automatizacion_compras_service as service_mod


def test_legacy_server_ids_global_scope_returns_none():
    assert access.get_legacy_server_ids_for_unidad_scope() is None


def test_legacy_server_ids_are_derived_from_canonical_units(monkeypatch):
    monkeypatch.setattr(
        access.UnidadesService,
        "get_all",
        lambda: [
            {"unidad_negocio_pk": "pk-a", "server_id": "srv-a"},
            {"unidad_negocio_pk": "pk-b", "server_id": "srv-b"},
            {"unidad_negocio_pk": "pk-c", "server_id": ""},
        ],
    )

    assert access.get_legacy_server_ids_for_unidad_scope("pk-a") == ["srv-a"]
    assert access.get_legacy_server_ids_for_unidad_scope(
        unidades_permitidas=["pk-a", "pk-b", "pk-c"]
    ) == ["srv-a", "srv-b"]
    assert access.get_legacy_server_ids_for_unidad_scope(unidades_permitidas=[]) == []


def test_automatizacion_scope_filter_uses_legacy_server_ids(monkeypatch):
    monkeypatch.setattr(
        service_mod,
        "get_legacy_server_ids_for_unidad_scope",
        lambda **kwargs: ["srv-a", "srv-b"],
    )

    filtro = service_mod.AutomatizacionComprasService._build_scope_filter(
        object(),
        unidades_permitidas=["pk-a", "pk-b"],
        estado="PENDIENTE",
    )

    assert filtro == {
        "server_id": {"$in": ["srv-a", "srv-b"]},
        "estado": "PENDIENTE",
    }
