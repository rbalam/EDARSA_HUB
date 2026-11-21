from core.rbac_sql import service as service_module
from core.rbac_sql.service import RBACSQLService


def test_get_empresas_uses_canonical_server_branch_scope(monkeypatch):
    captured = {}

    def fake_fetch_all(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return [{"EmpresaID": 2}, {"EmpresaID": 5}]

    monkeypatch.setattr(
        service_module,
        "fetch_all_dict",
        fake_fetch_all,
    )

    result = RBACSQLService.get_empresas(9)

    assert result == [
        {"EmpresaID": 2},
        {"EmpresaID": 5},
    ]
    assert captured["params"] == [9, 9, 9]

    sql = captured["sql"]
    assert "Usuario_EmpresasAsignacion" in sql
    assert "Usuario_ServidoresAsignacion" in sql
    assert "Usuario_SucursalesAsignacion" in sql
    assert "Unidades_Negocio" in sql
    assert "Servidores_Conexiones" in sql
    assert "Sistema_SucursalServidorMapeo" in sql
    assert "Sistema_Sucursales" in sql
    assert "ActiveUnitsOnServer > 1" in sql
    assert "SucursalCodigo" in sql
    assert "EmpresaID IS NOT NULL" in sql


def test_get_empresas_does_not_use_legacy_mongo_mapping(monkeypatch):
    captured = {}

    def fake_fetch_all(sql, params):
        captured["sql"] = sql
        return []

    monkeypatch.setattr(
        service_module,
        "fetch_all_dict",
        fake_fetch_all,
    )

    assert RBACSQLService.get_empresas(28) == []

    assert "Sistema_EmpresasMongoMap" not in captured["sql"]
    assert "MongoUUID" not in captured["sql"]


def test_can_access_empresa_uses_effective_company_scope(monkeypatch):
    monkeypatch.setattr(
        RBACSQLService,
        "_has_superadmin_role",
        staticmethod(lambda usuario_id: False),
    )
    monkeypatch.setattr(
        RBACSQLService,
        "get_empresas",
        staticmethod(
            lambda usuario_id: [
                {"EmpresaID": 2},
                {"EmpresaID": 5},
            ]
        ),
    )

    assert RBACSQLService.can_access_empresa(9, 2) is True
    assert RBACSQLService.can_access_empresa(9, 5) is True
    assert RBACSQLService.can_access_empresa(9, 4) is False


def test_can_access_empresa_keeps_superadmin_rule(monkeypatch):
    monkeypatch.setattr(
        RBACSQLService,
        "_has_superadmin_role",
        staticmethod(lambda usuario_id: True),
    )

    assert RBACSQLService.can_access_empresa(3, 5) is True
