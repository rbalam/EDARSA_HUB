from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from modules.finanzas import tesoreria_access as module


def _unit(
    *,
    unit_id="unit-a",
    code="UNIT-A",
    name="Unidad A",
    company="company-a",
    server="server-a",
    branch="branch-a",
    active_units=1,
):
    return module.TesoreriaUnit(
        unidad_negocio_pk=unit_id,
        unidad_negocio_codigo=code,
        unidad_negocio_nombre=name,
        empresa_id=company,
        server_id=server,
        sucursal_origen_id=branch,
        system_type="SOFTRESTAURANT",
        active_units_on_server=active_units,
    )


def _context(
    *,
    companies=(),
    servers=(),
    units=(),
    branches=(),
):
    return {
        "empresas": [
            {"EmpresaID": value}
            for value in companies
        ],
        "servidores": [
            {"ServidorID": value}
            for value in servers
        ],
        "unidades_negocio": [
            {"UnidadNegocioID": value}
            for value in units
        ],
        "sucursales": [
            {
                "ServidorID": server,
                "SucursalCodigo": branch,
            }
            for server, branch in branches
        ],
    }


def test_scope_global_con_decision_funcional(
    monkeypatch,
):
    catalog = (_unit(),)

    monkeypatch.setattr(
        module,
        "_load_canonical_units",
        lambda: catalog,
    )

    monkeypatch.setattr(
        module,
        "_has_global_access",
        lambda user, permission_code=None: True,
    )

    scope = module.require_tesoreria_access_scope(
        {"_sql_usuario_id": 1},
        module.TES_CUADRES_Z_VER,
    )

    assert scope.global_access is True
    assert scope.units == catalog


def test_empresa_asignada_limita_a_sus_unidades(monkeypatch):
    unit_a = _unit()
    unit_b = _unit(
        unit_id="unit-b",
        code="UNIT-B",
        name="Unidad B",
        company="company-b",
        server="server-b",
        branch="branch-b",
    )

    monkeypatch.setattr(
        module,
        "_load_canonical_units",
        lambda: (unit_a, unit_b),
    )
    monkeypatch.setattr(module, "_has_global_access", lambda user, permission_code=None: False)
    monkeypatch.setattr(
        module.RBACSQLService,
        "build_context",
        staticmethod(
            lambda user_id: _context(
                companies=("company-a",),
            )
        ),
    )

    scope = module.require_tesoreria_access_scope(
        {"_sql_usuario_id": 17}
    )

    assert scope.global_access is False
    assert scope.unit_ids == frozenset({"unit-a"})


def test_servidor_compartido_exige_sucursal_exacta(monkeypatch):
    unit_a = _unit(
        server="shared-server",
        branch="001",
        active_units=2,
    )
    unit_b = _unit(
        unit_id="unit-b",
        code="UNIT-B",
        name="Unidad B",
        company="company-b",
        server="shared-server",
        branch="002",
        active_units=2,
    )

    monkeypatch.setattr(
        module,
        "_load_canonical_units",
        lambda: (unit_a, unit_b),
    )
    monkeypatch.setattr(module, "_has_global_access", lambda user, permission_code=None: False)
    monkeypatch.setattr(
        module.RBACSQLService,
        "build_context",
        staticmethod(
            lambda user_id: _context(
                servers=("shared-server",),
                branches=(("shared-server", "002"),),
            )
        ),
    )

    scope = module.require_tesoreria_access_scope(
        {"_sql_usuario_id": 17}
    )

    assert scope.unit_ids == frozenset({"unit-b"})


def test_servidor_compartido_solo_por_servidor_se_deniega(
    monkeypatch,
):
    catalog = (
        _unit(
            server="shared-server",
            branch="001",
            active_units=2,
        ),
        _unit(
            unit_id="unit-b",
            code="UNIT-B",
            name="Unidad B",
            company="company-b",
            server="shared-server",
            branch="002",
            active_units=2,
        ),
    )

    monkeypatch.setattr(
        module,
        "_load_canonical_units",
        lambda: catalog,
    )
    monkeypatch.setattr(module, "_has_global_access", lambda user, permission_code=None: False)
    monkeypatch.setattr(
        module.RBACSQLService,
        "build_context",
        staticmethod(
            lambda user_id: _context(
                servers=("shared-server",),
            )
        ),
    )

    with pytest.raises(HTTPException) as exc:
        module.require_tesoreria_access_scope(
            {"_sql_usuario_id": 17}
        )

    assert exc.value.status_code == 403


def test_usuario_sin_asignaciones_no_obtiene_acceso_global(
    monkeypatch,
):
    monkeypatch.setattr(
        module,
        "_load_canonical_units",
        lambda: (_unit(),),
    )
    monkeypatch.setattr(module, "_has_global_access", lambda user, permission_code=None: False)
    monkeypatch.setattr(
        module.RBACSQLService,
        "build_context",
        staticmethod(lambda user_id: _context()),
    )

    with pytest.raises(HTTPException) as exc:
        module.require_tesoreria_access_scope(
            {"_sql_usuario_id": 17}
        )

    assert exc.value.status_code == 403


def test_fallo_sql_rbac_cierra_acceso(monkeypatch):
    monkeypatch.setattr(
        module,
        "_load_canonical_units",
        lambda: (_unit(),),
    )
    monkeypatch.setattr(module, "_has_global_access", lambda user, permission_code=None: False)

    def fail_context(user_id):
        raise RuntimeError("rbac unavailable")

    monkeypatch.setattr(
        module.RBACSQLService,
        "build_context",
        staticmethod(fail_context),
    )

    with pytest.raises(HTTPException) as exc:
        module.require_tesoreria_access_scope(
            {"_sql_usuario_id": 17}
        )

    assert exc.value.status_code == 503


def test_server_id_fuera_del_alcance_se_deniega():
    scope = module.TesoreriaAccessScope(
        global_access=False,
        units=(_unit(),),
    )

    with pytest.raises(HTTPException) as exc:
        scope.require_server_id("server-b")

    assert exc.value.status_code == 403


def test_filtrado_es_exacto_y_no_por_substring():
    scope = module.TesoreriaAccessScope(
        global_access=False,
        units=(_unit(code="ORIGEN"),),
    )

    records = [
        {
            "unidad_negocio_pk": "unit-a",
            "sucursal_nombre": "ORIGEN",
        },
        {
            "unidad_negocio_pk": "unit-b",
            "sucursal_nombre": "ORIGEN ALTERNO",
        },
    ]

    filtered = scope.filter_records(records)

    assert len(filtered) == 1
    assert filtered[0]["unidad_negocio_pk"] == "unit-a"


def test_tesoreria_routes_usan_permiso_por_operacion():
    backend = Path(__file__).resolve().parents[1]
    source = (
        backend
        / "modules"
        / "finanzas"
        / "tesoreria.py"
    ).read_text(encoding="utf-8")

    expected = {
        "TES_CUADRES_Z_VER": 6,
        "TES_CUADRES_Z_CREAR": 1,
        "TES_CUADRES_Z_EDITAR": 2,
        "TES_CUADRES_Z_ELIMINAR": 1,
        "TES_CUADRES_Z_VALIDAR": 1,
    }

    for permission, count in expected.items():
        marker = (
            "require_tesoreria_access_scope("
            f"current_user, {permission})"
        )

        assert source.count(marker) == count

    assert (
        "require_tesoreria_access_scope(current_user)"
        not in source
    )

    assert "_get_empresas_codigos_sql" not in source
    assert "get_user_sucursales_permitidas" not in source
    assert "filtrar_cortes_por_permisos" not in source
    assert "get_tesoreria_sucursales_operativas" not in source
    assert "server_registry" not in source
    assert "list_operational_servers" not in source

    assert "scope.require_server_id(server_id)" in source
    assert "scope.require_record(corte_z)" in source
    assert "canonical_unit.unidad_negocio_pk" in source
    assert "canonical_unit.server_id" in source


def test_import_no_requiere_configuracion_sql():
    import os
    import subprocess
    import sys

    environment = os.environ.copy()

    for key in (
        "EDARSAHUB_SQL_HOST",
        "EDARSAHUB_SQL_PORT",
        "EDARSAHUB_SQL_DATABASE",
        "EDARSAHUB_SQL_USER",
        "EDARSAHUB_SQL_PASSWORD",
    ):
        environment.pop(key, None)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from modules.finanzas import tesoreria_access; "
                "print('IMPORT_OK')"
            ),
        ],
        cwd="/app/backend",
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "IMPORT_OK" in result.stdout


def test_record_no_autorizado_no_coincide_por_empresa():
    scope = module.TesoreriaAccessScope(
        global_access=False,
        units=(
            _unit(
                unit_id="unit-a",
                company="company-shared",
                server="server-a",
                branch="001",
            ),
        ),
    )

    unauthorized = {
        "unidad_negocio_pk": "unit-b",
        "empresa_id": "company-shared",
        "server_id": "server-b",
    }

    assert scope.match_record(unauthorized) is None

    with pytest.raises(HTTPException) as exc:
        scope.require_record(unauthorized)

    assert exc.value.status_code == 403


def test_record_solo_con_empresa_se_deniega():
    scope = module.TesoreriaAccessScope(
        global_access=False,
        units=(
            _unit(
                company="company-a",
            ),
        ),
    )

    assert scope.match_record(
        {"empresa_id": "company-a"}
    ) is None


def test_server_compartido_requiere_alcance_completo():
    scope = module.TesoreriaAccessScope(
        global_access=False,
        units=(
            _unit(
                unit_id="unit-a",
                server="shared-server",
                branch="001",
                active_units=2,
            ),
        ),
    )

    with pytest.raises(HTTPException) as exc:
        scope.require_server_id("shared-server")

    assert exc.value.status_code == 403


def test_server_compartido_acepta_alcance_completo():
    unit_a = _unit(
        unit_id="unit-a",
        server="shared-server",
        branch="001",
        active_units=2,
    )
    unit_b = _unit(
        unit_id="unit-b",
        code="UNIT-B",
        name="Unidad B",
        company="company-b",
        server="shared-server",
        branch="002",
        active_units=2,
    )

    scope = module.TesoreriaAccessScope(
        global_access=False,
        units=(unit_a, unit_b),
    )

    assert (
        scope.require_server_id(
            "shared-server"
        )
        is None
    )


def test_rol_superadmin_sin_permiso_funcional_se_deniega(
    monkeypatch,
):
    monkeypatch.setattr(
        module.RBACSQLService,
        "get_permission_scope_by_code",
        staticmethod(
            lambda user_id, permission_code: None
        ),
    )

    with pytest.raises(HTTPException) as exc:
        module._has_global_access(
            {
                "role_code": "SUPERADMIN",
                "_sql_usuario_id": 1,
            }
        )

    assert exc.value.status_code == 403


def test_permiso_sin_restriccion_otorga_alcance_global(
    monkeypatch,
):
    monkeypatch.setattr(
        module.RBACSQLService,
        "get_permission_scope_by_code",
        staticmethod(
            lambda user_id, permission_code: {
                "permission_code": permission_code,
                "permitido": True,
                "restriccion_sucursal": False,
            }
        ),
    )

    assert module._has_global_access(
        {"_sql_usuario_id": 1}
    ) is True


def test_permiso_restringido_no_otorga_alcance_global(
    monkeypatch,
):
    monkeypatch.setattr(
        module.RBACSQLService,
        "get_permission_scope_by_code",
        staticmethod(
            lambda user_id, permission_code: {
                "permission_code": permission_code,
                "permitido": 1,
                "restriccion_sucursal": 1,
            }
        ),
    )

    assert module._has_global_access(
        {"_sql_usuario_id": 1}
    ) is False


def test_permiso_funcional_incompleto_falla_cerrado(
    monkeypatch,
):
    monkeypatch.setattr(
        module.RBACSQLService,
        "get_permission_scope_by_code",
        staticmethod(
            lambda user_id, permission_code: {
                "permitido": True,
            }
        ),
    )

    with pytest.raises(
        module.TesoreriaAccessResolutionError
    ):
        module._has_global_access(
            {"_sql_usuario_id": 1}
        )


def test_fallo_lookup_permiso_funcional_falla_cerrado(
    monkeypatch,
):
    def fail_permission(
        user_id,
        permission_code,
    ):
        raise RuntimeError(
            "permission unavailable"
        )

    monkeypatch.setattr(
        module.RBACSQLService,
        "get_permission_scope_by_code",
        staticmethod(fail_permission),
    )

    with pytest.raises(
        module.TesoreriaAccessResolutionError
    ):
        module._has_global_access(
            {"_sql_usuario_id": 1}
        )


def test_sucursales_exponen_id_unico_de_unidad():
    unit_a = _unit(
        unit_id="unit-a",
        server="shared-server",
        branch="001",
        active_units=2,
    )
    unit_b = _unit(
        unit_id="unit-b",
        code="UNIT-B",
        name="Unidad B",
        company="company-b",
        server="shared-server",
        branch="002",
        active_units=2,
    )

    rows = module.TesoreriaAccessScope(
        global_access=True,
        units=(unit_a, unit_b),
    ).to_sucursales()

    assert [
        row["id"]
        for row in rows
    ] == [
        "unit-a",
        "unit-b",
    ]

    assert {
        row["server_id"]
        for row in rows
    } == {
        "shared-server",
    }


def test_permission_code_se_propaga_al_scope(
    monkeypatch,
):
    captured = {}

    monkeypatch.setattr(
        module,
        "_load_canonical_units",
        lambda: (_unit(),),
    )

    def has_global_access(
        current_user,
        permission_code,
    ):
        captured["permission_code"] = permission_code
        return True

    monkeypatch.setattr(
        module,
        "_has_global_access",
        has_global_access,
    )

    scope = module.resolve_tesoreria_access_scope(
        {"_sql_usuario_id": 1},
        module.TES_CUADRES_Z_CREAR,
    )

    assert scope.global_access is True
    assert (
        captured["permission_code"]
        == module.TES_CUADRES_Z_CREAR
    )
