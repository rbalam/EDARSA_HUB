from core.rbac_sql import service


def test_superadmin_can_access_empresa_without_explicit_scope(monkeypatch):
    calls = []

    def fake_fetch_one_dict(sql, params):
        calls.append(sql)
        if "Usuario_EmpresasAsignacion" in sql:
            raise AssertionError("SUPERADMIN must not require explicit company scope")
        if "Usuario_RolesAsignacion AS ura" in sql and "Usuario_Roles AS r" in sql:
            return {"permitido": 1}
        return None

    monkeypatch.setattr(service, "fetch_one_dict", fake_fetch_one_dict)

    assert service.RBACSQLService.can_access_empresa(8, 2) is True
    assert any("Usuario_RolesAsignacion AS ura" in sql for sql in calls)


def test_can_access_empresa_fails_closed_for_missing_or_invalid_empresa(monkeypatch):
    def fake_fetch_one_dict(sql, params):
        raise AssertionError("No SQL should run for invalid empresa_id")

    monkeypatch.setattr(service, "fetch_one_dict", fake_fetch_one_dict)

    assert service.RBACSQLService.can_access_empresa(8, None) is False
    assert service.RBACSQLService.can_access_empresa(8, "") is False
    assert service.RBACSQLService.can_access_empresa(8, "   ") is False
    assert service.RBACSQLService.can_access_empresa(8, 0) is False
    assert service.RBACSQLService.can_access_empresa(8, "0") is False
    assert service.RBACSQLService.can_access_empresa(8, "abc") is False


def test_normal_user_requires_explicit_empresa_scope(monkeypatch):
    calls = []

    def fake_fetch_one_dict(sql, params):
        calls.append(sql)
        if "Usuario_RolesAsignacion AS ura" in sql and "Usuario_Roles AS r" in sql:
            return None
        if "Usuario_EmpresasAsignacion" in sql:
            return {"permitido": 1}
        return None

    monkeypatch.setattr(service, "fetch_one_dict", fake_fetch_one_dict)

    assert service.RBACSQLService.can_access_empresa(12, 3) is True
    assert any("Usuario_EmpresasAsignacion" in sql for sql in calls)


def test_normal_user_without_explicit_empresa_scope_is_denied(monkeypatch):
    def fake_fetch_one_dict(sql, params):
        return None

    monkeypatch.setattr(service, "fetch_one_dict", fake_fetch_one_dict)

    assert service.RBACSQLService.can_access_empresa(12, 3) is False
