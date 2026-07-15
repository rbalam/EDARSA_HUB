import pytest

from core.corporate_filters import request_resolver


VALID_METADATA = {
    "unidad_negocio_pk": "unit-pk",
    "unidad_negocio_codigo": "UNIT-A",
    "unidad_negocio_nombre": "Unit A",
    "server_id": "server-a",
    "sucursal_origen_id": "branch-a",
    "system_type": "SYSTEM-A",
    "unidad_activo": True,
    "servidor_activo": True,
    "active_units_on_server": 2,
    "empresa_id": "company-a",
    "visible_en_operaciones": True,
}


@pytest.mark.asyncio
async def test_requires_internal_sql_user_id(monkeypatch):
    called = False

    def repository(**kwargs):
        nonlocal called
        called = True
        return dict(VALID_METADATA)

    monkeypatch.setattr(
        request_resolver,
        "get_unit_scope_metadata_readonly",
        repository,
    )

    scope = await (
        request_resolver.resolve_authorized_unidad_scope(
            {"id": "public-id"},
            "COMPRAS_FACT_VER",
            "UNIT-A",
        )
    )

    assert scope.access_denied is True
    assert (
        scope.denial_reason
        == "sql_usuario_id_required"
    )
    assert called is False


@pytest.mark.asyncio
async def test_uses_canonical_metadata_and_returns_scope(
    monkeypatch,
):
    factory = object()
    captured = {}

    monkeypatch.setattr(
        request_resolver,
        "build_hrlectura_connection_factory",
        lambda: factory,
    )

    def repository(*, unidad, connection_factory):
        captured["unidad"] = unidad
        captured["factory"] = connection_factory
        return dict(VALID_METADATA)

    monkeypatch.setattr(
        request_resolver,
        "get_unit_scope_metadata_readonly",
        repository,
    )

    def authorize(
        usuario_id,
        permission_code,
        metadata,
    ):
        captured["usuario_id"] = usuario_id
        captured["permission_code"] = permission_code
        captured["metadata"] = metadata
        return True

    monkeypatch.setattr(
        request_resolver,
        "can_access_unit_metadata_sql",
        authorize,
    )

    scope = await (
        request_resolver.resolve_authorized_unidad_scope(
            {"_sql_usuario_id": 17},
            "COMPRAS_FACT_VER",
            "UNIT-A",
        )
    )

    assert scope.access_denied is False
    assert scope.unidad_codigo == "UNIT-A"
    assert scope.server_id == "server-a"
    assert scope.sucursal_origen_id == "branch-a"
    assert scope.active_units_on_server == 2
    assert captured["unidad"] == "UNIT-A"
    assert captured["factory"] is factory
    assert captured["usuario_id"] == 17
    assert (
        captured["permission_code"]
        == "COMPRAS_FACT_VER"
    )
    assert captured["metadata"] == VALID_METADATA


@pytest.mark.asyncio
async def test_denied_permission_returns_sentinel(
    monkeypatch,
):
    monkeypatch.setattr(
        request_resolver,
        "build_hrlectura_connection_factory",
        lambda: object(),
    )

    monkeypatch.setattr(
        request_resolver,
        "get_unit_scope_metadata_readonly",
        lambda **kwargs: dict(VALID_METADATA),
    )

    monkeypatch.setattr(
        request_resolver,
        "can_access_unit_metadata_sql",
        lambda *args, **kwargs: False,
    )

    scope = await (
        request_resolver.resolve_authorized_unidad_scope(
            {"UsuarioID": 17},
            "COMPRAS_FACT_VER",
            "UNIT-A",
        )
    )

    assert scope.access_denied is True
    assert scope.denial_reason == "unit_scope_denied"
    assert scope.effective_server_ids == [
        request_resolver.NO_ACCESS_SENTINEL_SERVER_ID
    ]


@pytest.mark.asyncio
async def test_sql_error_fails_closed(monkeypatch):
    monkeypatch.setattr(
        request_resolver,
        "build_hrlectura_connection_factory",
        lambda: object(),
    )

    def repository(**kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        request_resolver,
        "get_unit_scope_metadata_readonly",
        repository,
    )

    scope = await (
        request_resolver.resolve_authorized_unidad_scope(
            {"_sql_usuario_id": 17},
            "COMPRAS_FACT_VER",
            "UNIT-A",
        )
    )

    assert scope.access_denied is True
    assert scope.denial_reason == "authorization_error"


def test_ambiguous_server_does_not_select_first_unit(
    monkeypatch,
):
    monkeypatch.setattr(
        request_resolver.UnidadesService,
        "get_all",
        staticmethod(
            lambda: [
                {
                    "codigo": "UNIT-A",
                    "server_id": "shared-server",
                },
                {
                    "codigo": "UNIT-B",
                    "server_id": "shared-server",
                },
            ]
        ),
    )

    assert (
        request_resolver._find_unidad_by_server(
            "shared-server"
        )
        is None
    )


def test_unique_server_keeps_legacy_compatibility(
    monkeypatch,
):
    unit = {
        "codigo": "UNIT-A",
        "server_id": "single-server",
    }

    monkeypatch.setattr(
        request_resolver.UnidadesService,
        "get_all",
        staticmethod(lambda: [unit]),
    )

    assert (
        request_resolver._find_unidad_by_server(
            "single-server"
        )
        == unit
    )


@pytest.mark.asyncio
async def test_empty_unit_is_rejected_before_repository(
    monkeypatch,
):
    called = False

    def repository(**kwargs):
        nonlocal called
        called = True
        return dict(VALID_METADATA)

    monkeypatch.setattr(
        request_resolver,
        "get_unit_scope_metadata_readonly",
        repository,
    )

    scope = await (
        request_resolver.resolve_authorized_unidad_scope(
            {"_sql_usuario_id": 17},
            "COMPRAS_FACT_VER",
            "",
        )
    )

    assert scope.access_denied is True
    assert (
        scope.denial_reason
        == "canonical_unit_required"
    )
    assert called is False

@pytest.mark.asyncio
async def test_legacy_global_empty_allowed_contract_is_preserved(
    monkeypatch,
):
    async def empty_allowed(current_user):
        return []

    monkeypatch.setattr(
        request_resolver,
        "_get_allowed_server_ids",
        empty_allowed,
    )

    scope = await request_resolver.resolve_unidad_scope(
        {"email": "legacy@example.invalid"}
    )

    assert scope.is_global is True
    assert scope.access_denied is False
    assert scope.allowed_server_ids == []
    assert scope.effective_server_ids == []


@pytest.mark.asyncio
async def test_legacy_allowed_lookup_error_still_returns_empty_list(
    monkeypatch,
):
    from core import security

    async def fail_lookup(current_user):
        raise RuntimeError("legacy lookup unavailable")

    monkeypatch.setattr(
        security,
        "get_user_empresas_permitidas",
        fail_lookup,
    )

    result = await request_resolver._get_allowed_server_ids(
        {"email": "legacy@example.invalid"}
    )

    assert result == []
