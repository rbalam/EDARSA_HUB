import pytest

from modules.api_connections import universal_test_routes as module


@pytest.mark.asyncio
async def test_validate_access_allows_with_permission_and_empresa(
    monkeypatch,
):
    monkeypatch.setattr(
        module,
        "resolve_sql_usuario_id",
        lambda user: 101,
    )

    monkeypatch.setattr(
        module,
        "can_access_permission_sql",
        lambda usuario_id, permission: (
            usuario_id == 101
            and permission == "SERVIDORES_VER"
        ),
    )

    monkeypatch.setattr(
        module,
        "can_access_empresa_sql",
        lambda usuario_id, empresa_id: (
            usuario_id == 101
            and empresa_id == 7
        ),
    )

    result = await module.validate_api_connection_access(
        {"email": "test@example.com"},
        {
            "id": "connection-1",
            "EmpresaID": 7,
        },
    )

    assert result is True


@pytest.mark.asyncio
async def test_validate_access_denies_without_sql_identity(
    monkeypatch,
):
    monkeypatch.setattr(
        module,
        "resolve_sql_usuario_id",
        lambda user: None,
    )

    permission_called = False
    empresa_called = False

    def permission(*args, **kwargs):
        nonlocal permission_called
        permission_called = True
        return True

    def empresa(*args, **kwargs):
        nonlocal empresa_called
        empresa_called = True
        return True

    monkeypatch.setattr(
        module,
        "can_access_permission_sql",
        permission,
    )

    monkeypatch.setattr(
        module,
        "can_access_empresa_sql",
        empresa,
    )

    result = await module.validate_api_connection_access(
        {"email": "test@example.com"},
        {
            "id": "connection-1",
            "EmpresaID": 7,
        },
    )

    assert result is False
    assert permission_called is False
    assert empresa_called is False


@pytest.mark.asyncio
async def test_validate_access_denies_without_servidores_ver(
    monkeypatch,
):
    monkeypatch.setattr(
        module,
        "resolve_sql_usuario_id",
        lambda user: 101,
    )

    monkeypatch.setattr(
        module,
        "can_access_permission_sql",
        lambda usuario_id, permission: False,
    )

    empresa_called = False

    def empresa(*args, **kwargs):
        nonlocal empresa_called
        empresa_called = True
        return True

    monkeypatch.setattr(
        module,
        "can_access_empresa_sql",
        empresa,
    )

    result = await module.validate_api_connection_access(
        {"email": "test@example.com"},
        {
            "id": "connection-1",
            "EmpresaID": 7,
        },
    )

    assert result is False
    assert empresa_called is False


@pytest.mark.asyncio
async def test_validate_access_denies_without_empresa(
    monkeypatch,
):
    monkeypatch.setattr(
        module,
        "resolve_sql_usuario_id",
        lambda user: 101,
    )

    monkeypatch.setattr(
        module,
        "can_access_permission_sql",
        lambda usuario_id, permission: True,
    )

    empresa_called = False

    def empresa(*args, **kwargs):
        nonlocal empresa_called
        empresa_called = True
        return True

    monkeypatch.setattr(
        module,
        "can_access_empresa_sql",
        empresa,
    )

    result = await module.validate_api_connection_access(
        {"email": "test@example.com"},
        {
            "id": "connection-1",
            "EmpresaID": None,
        },
    )

    assert result is False
    assert empresa_called is False


@pytest.mark.asyncio
async def test_validate_access_denies_without_empresa_scope(
    monkeypatch,
):
    monkeypatch.setattr(
        module,
        "resolve_sql_usuario_id",
        lambda user: 101,
    )

    monkeypatch.setattr(
        module,
        "can_access_permission_sql",
        lambda usuario_id, permission: True,
    )

    monkeypatch.setattr(
        module,
        "can_access_empresa_sql",
        lambda usuario_id, empresa_id: False,
    )

    result = await module.validate_api_connection_access(
        {"email": "test@example.com"},
        {
            "id": "connection-1",
            "EmpresaID": 7,
        },
    )

    assert result is False


@pytest.mark.asyncio
async def test_validate_access_fails_closed_on_exception(
    monkeypatch,
):
    def explode(user):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(
        module,
        "resolve_sql_usuario_id",
        explode,
    )

    result = await module.validate_api_connection_access(
        {"email": "test@example.com"},
        {
            "id": "connection-1",
            "EmpresaID": 7,
        },
    )

    assert result is False


def test_validate_access_has_no_runtime_role_bypass():
    import ast
    import inspect
    import textwrap

    source = textwrap.dedent(
        inspect.getsource(
            module.validate_api_connection_access
        )
    )

    tree = ast.parse(source)

    runtime_strings = {
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
    }

    runtime_names = {
        n.id
        for n in ast.walk(tree)
        if isinstance(n, ast.Name)
    }

    assert "SuperAdministrador" not in runtime_strings
    assert "Administrador" not in runtime_strings
    assert "CONEXIONES_VER" not in runtime_strings

    assert "user_role" not in runtime_names
    assert "user_allowed_servers" not in runtime_names
    assert "allowed_servers" not in runtime_names

    assert "SERVIDORES_VER" in runtime_strings
