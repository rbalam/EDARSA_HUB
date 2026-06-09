"""
Regresión Bloque C (2026-06-09): repositorio del Catálogo Comercial Enriquecido.
================================================================================
Valida (NO-LIVE, contra EDARSAHUB real) el repositorio SQL-first:
- listar con filtros + paginación + JOIN canónico a Sync_Productos.
- get_by_id, actualizar, set_activo (idempotente, restaura estado).
- catalogos_filtros (distincts + indicadores).
- RBAC scope: allowed_server_ids restringe; lista vacía = sin restricción.
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from modules.comercial_enriquecido.repository import ComercialEnriquecidoRepository as Repo  # noqa: E402


def test_listar_admin_sin_restriccion():
    res = Repo.listar({}, allowed_server_ids=[], limit=5, offset=0)
    assert res["total"] >= 3000
    assert len(res["items"]) == 5
    it = res["items"][0]
    # JOIN canónico a Sync_Productos expone campos base
    assert "es_vendible" in it and "tiene_receta" in it and "nombre_producto" in it


def test_listar_filtro_alcohol():
    res = Repo.listar({"es_alcoholico": True, "grado_alcohol_min": 35}, [], limit=1)
    assert res["total"] > 0


def test_rbac_scope_restringe_por_server():
    # Servidor inexistente => 0 resultados (scope vacío de datos)
    res = Repo.listar({}, allowed_server_ids=["00000000-0000-0000-0000-000000000000"], limit=5)
    assert res["total"] == 0


def test_get_actualizar_y_restaurar():
    res = Repo.listar({}, [], limit=1)
    item = res["items"][0]
    id_ = item["id"]
    original = item.get("observaciones")

    ok = Repo.actualizar(id_, {"observaciones": "QA_BLOQUE_C"}, "pytest")
    assert ok is True
    got = Repo.get_by_id(id_, [])
    assert got["observaciones"] == "QA_BLOQUE_C"

    # restaurar
    Repo.actualizar(id_, {"observaciones": original}, "pytest")
    got2 = Repo.get_by_id(id_, [])
    assert got2["observaciones"] == original


def test_set_activo_toggle():
    res = Repo.listar({}, [], limit=1)
    id_ = res["items"][0]["id"]
    activo_orig = bool(res["items"][0]["activo"])
    Repo.set_activo(id_, not activo_orig, "pytest")
    got = Repo.get_by_id(id_, [])
    assert bool(got["activo"]) == (not activo_orig)
    # restaurar
    Repo.set_activo(id_, activo_orig, "pytest")
    assert bool(Repo.get_by_id(id_, [])["activo"]) == activo_orig


def test_catalogos_filtros_indicadores():
    cat = Repo.catalogos_filtros([])
    assert len(cat["grupos_comerciales"]) > 0
    assert len(cat["marcas"]) > 0
    ind = cat["indicadores"]
    assert ind["total"] >= 3000
    assert ind["alcoholico_sin_grado"] == 0  # invariante de calidad del Excel
    assert ind["requiere_validacion"] >= 0


def test_get_by_id_inexistente():
    assert Repo.get_by_id("00000000-0000-0000-0000-000000000000", []) is None
