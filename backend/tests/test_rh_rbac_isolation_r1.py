"""RH-R1 acceptance tests: RBAC isolation for colaboradores and incidencias."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
import pytest
from fastapi import HTTPException

from modules.rh import repository as rh_repo
from modules.rh import routes as rh_routes
from modules.rh import service as rh_service
from modules.rh.schemas import ColaboradorCreate, IncidenciaCreate


def _ctx(*, global_access=False, sucursales_por_server=None, empresas_ids=None):
    return SimpleNamespace(
        tiene_acceso_global=global_access,
        sucursales_por_server=sucursales_por_server or {},
        empresas_ids=empresas_ids or [],
    )


def test_resolve_rh_scope_explicit_global_vs_fail_closed_without_scope(monkeypatch):
    # Global admin -> None (unrestricted)
    async def global_ctx(_user):
        return _ctx(global_access=True)

    monkeypatch.setattr(rh_routes, "resolve_user_access_context", global_ctx)
    assert asyncio.run(rh_routes.resolve_rh_allowed_sucursal_ids({"id": "1"})) is None

    # Restricted user WITHOUT any effective sucursal or empresa mapping -> HTTP 403 fail-closed
    async def empty_ctx(_user):
        return _ctx(global_access=False, sucursales_por_server={}, empresas_ids=[])

    monkeypatch.setattr(rh_routes, "resolve_user_access_context", empty_ctx)
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(rh_routes.resolve_rh_allowed_sucursal_ids({"id": "2"}))
    assert exc_info.value.status_code == 403

    # Restricted user with sucursales [10, 20] -> exact sorted list [10, 20]
    async def scoped_ctx(_user):
        return _ctx(global_access=False, sucursales_por_server={"srv1": ["20", "10"]})

    monkeypatch.setattr(rh_routes, "resolve_user_access_context", scoped_ctx)
    assert asyncio.run(rh_routes.resolve_rh_allowed_sucursal_ids({"id": "3"})) == [10, 20]


def test_colaboradores_and_incidencias_sql_filter_and_consistent_counts(monkeypatch):
    captured_queries: list[str] = []

    def fake_exec(_server, query):
        captured_queries.append(query)
        if "SELECT COUNT(*)" in query:
            return [{"total": 2}]
        return [{"ColaboradorID": 1, "SucursalID": 10}, {"ColaboradorID": 2, "SucursalID": 20}]

    monkeypatch.setattr(rh_repo, "execute_hub_query", fake_exec)

    res_col = rh_repo.query_listar_colaboradores({}, allowed_sucursal_ids=[10, 20])
    assert res_col["total"] == 2
    assert len(res_col["datos"]) == 2
    assert all("c.SucursalID IN (10,20)" in q for q in captured_queries[-2:])

    captured_queries.clear()
    res_inc = rh_repo.query_listar_incidencias({}, allowed_sucursal_ids=[10])
    assert res_inc["total"] == 2
    assert all("c.SucursalID IN (10)" in q for q in captured_queries[-2:])

    # Invalid negative filter rejected
    with pytest.raises(ValueError, match="INVALID_SUCURSAL_ID"):
        rh_repo.query_listar_colaboradores({}, sucursal_id=-5)
    with pytest.raises(ValueError, match="INVALID_COLABORADOR_ID"):
        rh_repo.query_listar_incidencias({}, colaborador_id=0)


def test_curp_rfc_clabe_protected_and_cross_sucursal_access_denied(monkeypatch):
    async def fake_server():
        return {"host": "mock"}

    monkeypatch.setattr(rh_service.rh_colaboradores_service, "_get_server", fake_server)
    monkeypatch.setattr(rh_service.rh_incidencias_service, "_get_server", fake_server)

    # Colaborador belongs to sucursal 99 with sensitive CURP/RFC/CLABE
    monkeypatch.setattr(
        rh_service,
        "query_obtener_colaborador",
        lambda _srv, cid: {
            "datos": {
                "ColaboradorID": cid,
                "SucursalID": 99,
                "CURP": "XXXX990101HDFXXX01",
                "RFC": "XXXX990101XXX",
                "CLABE_Bancaria": "012345678901234567",
            }
        },
    )

    # Restricted user allowed only sucursal [10] CANNOT read detail (CURP/RFC/CLABE protected -> 403)
    with pytest.raises(HTTPException) as exc_det:
        asyncio.run(
            rh_service.rh_colaboradores_service.obtener_colaborador_detalle(
                55, allowed_sucursal_ids=[10]
            )
        )
    assert exc_det.value.status_code == 403

    # Restricted user CANNOT filter list by forbidden sucursal 99 -> 403
    with pytest.raises(HTTPException) as exc_list:
        asyncio.run(
            rh_service.rh_colaboradores_service.listar_colaboradores(
                sucursal_id=99, allowed_sucursal_ids=[10]
            )
        )
    assert exc_list.value.status_code == 403

    # Restricted user CANNOT create colaborador in forbidden sucursal 99 -> 403
    with pytest.raises(HTTPException) as exc_create:
        asyncio.run(
            rh_service.rh_colaboradores_service.crear_colaborador(
                ColaboradorCreate(nombre_completo="Juan Perez", sucursal_id=99, puesto_id=1),
                allowed_sucursal_ids=[10],
            )
        )
    assert exc_create.value.status_code == 403

    # Restricted user CANNOT create incidencia for colaborador in forbidden sucursal 99 -> 403
    with pytest.raises(HTTPException) as exc_inc:
        asyncio.run(
            rh_service.rh_incidencias_service.crear_incidencia(
                IncidenciaCreate(
                    colaborador_id=55,
                    tipo_incidencia="Falta",
                    fecha_incidencia="2026-11-19",
                    monto=0,
                    unidades=1,
                ),
                {"email": "user@edarsa.com.mx"},
                allowed_sucursal_ids=[10],
            )
        )
    assert exc_inc.value.status_code == 403

    # Invalid sucursal_id=0 rejected with 400
    with pytest.raises(HTTPException) as exc_bad:
        asyncio.run(
            rh_service.rh_incidencias_service.listar_incidencias(
                sucursal_id=0, allowed_sucursal_ids=[10]
            )
        )
    assert exc_bad.value.status_code == 400
