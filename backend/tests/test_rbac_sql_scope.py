from pathlib import Path

from core.rbac_sql import service as service_module
from core.rbac_sql.service import RBACSQLService


def _metadata(
    *,
    active_units=1,
    branch=None,
    unit_active=True,
    server_active=True,
):
    return {
        "unidad_negocio_pk": "unit-pk",
        "unidad_negocio_codigo": "UNIT-A",
        "server_id": "server-a",
        "sucursal_origen_id": branch,
        "unidad_activo": unit_active,
        "servidor_activo": server_active,
        "active_units_on_server": active_units,
    }


def _install_scope_mocks(
    monkeypatch,
    *,
    permission,
    server_count=0,
    branch_count=0,
    server_allowed=False,
    branch_allowed=False,
):
    monkeypatch.setattr(
        RBACSQLService,
        "get_permission_scope_by_code",
        staticmethod(
            lambda usuario_id, permission_code: permission
        ),
    )

    monkeypatch.setattr(
        RBACSQLService,
        "get_scope_assignment_state",
        staticmethod(
            lambda usuario_id: {
                "server_assignment_count": server_count,
                "branch_assignment_count": branch_count,
            }
        ),
    )

    monkeypatch.setattr(
        RBACSQLService,
        "can_access_servidor",
        staticmethod(
            lambda usuario_id, server_id: server_allowed
        ),
    )

    monkeypatch.setattr(
        RBACSQLService,
        "can_access_sucursal",
        staticmethod(
            lambda usuario_id, server_id, branch_id: (
                branch_allowed
            )
        ),
    )


def test_permission_lookup_is_parameterized(monkeypatch):
    captured = {}

    def fake_fetch(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return {
            "permitido": 1,
            "restriccion_sucursal": 0,
        }

    monkeypatch.setattr(
        service_module,
        "fetch_one_dict",
        fake_fetch,
    )

    result = (
        RBACSQLService.get_permission_scope_by_code(
            17,
            "COMPRAS_FACT_VER",
        )
    )

    assert result["permitido"] is True
    assert captured["params"] == [
        17,
        "COMPRAS_FACT_VER",
    ]
    assert "%s" in captured["sql"]
    assert "COMPRAS_FACT_VER" not in captured["sql"]


def test_missing_permission_fails_closed(monkeypatch):
    monkeypatch.setattr(
        service_module,
        "fetch_one_dict",
        lambda sql, params: {
            "permitido": 0,
            "restriccion_sucursal": 0,
        },
    )

    assert (
        RBACSQLService.get_permission_scope_by_code(
            17,
            "COMPRAS_FACT_VER",
        )
        is None
    )


def test_unrestricted_without_assignments_allows_canonical_unit(
    monkeypatch,
):
    _install_scope_mocks(
        monkeypatch,
        permission={
            "permitido": True,
            "restriccion_sucursal": False,
        },
    )

    assert RBACSQLService.can_access_unit_metadata(
        17,
        "COMPRAS_FACT_VER",
        _metadata(),
    )


def test_restricted_without_assignments_denies(monkeypatch):
    _install_scope_mocks(
        monkeypatch,
        permission={
            "permitido": True,
            "restriccion_sucursal": True,
        },
    )

    assert not RBACSQLService.can_access_unit_metadata(
        17,
        "COMPRAS_FACT_VER",
        _metadata(),
    )


def test_explicit_scope_limits_unrestricted_permission(
    monkeypatch,
):
    _install_scope_mocks(
        monkeypatch,
        permission={
            "permitido": True,
            "restriccion_sucursal": False,
        },
        server_count=1,
        server_allowed=False,
    )

    assert not RBACSQLService.can_access_unit_metadata(
        17,
        "COMPRAS_FACT_VER",
        _metadata(),
    )


def test_single_unit_server_accepts_exact_server_assignment(
    monkeypatch,
):
    _install_scope_mocks(
        monkeypatch,
        permission={
            "permitido": True,
            "restriccion_sucursal": False,
        },
        server_count=1,
        server_allowed=True,
    )

    assert RBACSQLService.can_access_unit_metadata(
        17,
        "COMPRAS_FACT_VER",
        _metadata(active_units=1),
    )


def test_shared_server_rejects_server_only_assignment(
    monkeypatch,
):
    _install_scope_mocks(
        monkeypatch,
        permission={
            "permitido": True,
            "restriccion_sucursal": False,
        },
        server_count=1,
        server_allowed=True,
        branch_allowed=False,
    )

    assert not RBACSQLService.can_access_unit_metadata(
        17,
        "COMPRAS_FACT_VER",
        _metadata(
            active_units=2,
            branch="branch-a",
        ),
    )


def test_shared_server_accepts_exact_branch(monkeypatch):
    _install_scope_mocks(
        monkeypatch,
        permission={
            "permitido": True,
            "restriccion_sucursal": False,
        },
        server_count=1,
        branch_count=1,
        server_allowed=True,
        branch_allowed=True,
    )

    assert RBACSQLService.can_access_unit_metadata(
        17,
        "COMPRAS_FACT_VER",
        _metadata(
            active_units=2,
            branch="branch-a",
        ),
    )


def test_inactive_unit_or_server_denies(monkeypatch):
    _install_scope_mocks(
        monkeypatch,
        permission={
            "permitido": True,
            "restriccion_sucursal": False,
        },
    )

    assert not RBACSQLService.can_access_unit_metadata(
        17,
        "COMPRAS_FACT_VER",
        _metadata(unit_active=False),
    )

    assert not RBACSQLService.can_access_unit_metadata(
        17,
        "COMPRAS_FACT_VER",
        _metadata(server_active=False),
    )


def test_invalid_topology_denies(monkeypatch):
    _install_scope_mocks(
        monkeypatch,
        permission={
            "permitido": True,
            "restriccion_sucursal": False,
        },
    )

    assert not RBACSQLService.can_access_unit_metadata(
        17,
        "COMPRAS_FACT_VER",
        _metadata(active_units=0),
    )


def test_service_contains_no_role_name_authorization():
    path = (
        Path(__file__).parents[1]
        / "core/rbac_sql/service.py"
    )

    source = path.read_text(
        encoding="utf-8",
        errors="strict",
    )

    assert "NivelJerarquia >=" not in source
    assert "CodigoRol =" not in source
