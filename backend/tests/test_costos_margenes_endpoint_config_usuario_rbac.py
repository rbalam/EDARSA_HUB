from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from modules.costos_margenes import routes
from modules.costos_margenes.schemas import (
    ConfiguracionCostosMargenesUsuarioPatch,
)


UNIT_PK = "11111111-1111-1111-1111-111111111111"


def _user(usuario_id=99):
    return {
        "_sql_usuario_id": usuario_id,
        "email": "test@example.com",
    }


def _allowed_scope():
    return SimpleNamespace(
        access_denied=False,
        unidad_pk=UNIT_PK,
        server_id="SERVER-TEST",
    )


@pytest.mark.asyncio
async def test_autorizado_llega_writer_y_resolver(
    monkeypatch,
):
    calls = {
        "permission": [],
        "scope": [],
        "writer": [],
        "resolver": [],
    }

    def fake_verify(user, permission_code):
        calls["permission"].append(
            (
                user["_sql_usuario_id"],
                permission_code,
            )
        )
        return {
            "permitido": True,
            "restriccion_sucursal": False,
        }

    async def fake_scope(
        current_user,
        permission_code,
        unidad,
    ):
        calls["scope"].append(
            (
                current_user["_sql_usuario_id"],
                permission_code,
                unidad,
            )
        )
        return _allowed_scope()

    def fake_writer(usuario_id, cambios):
        calls["writer"].append(
            (
                usuario_id,
                dict(cambios),
            )
        )
        return {
            "UsuarioID": usuario_id,
        }

    def fake_resolver(
        unidad_pk,
        usuario_id=None,
    ):
        calls["resolver"].append(
            (
                unidad_pk,
                usuario_id,
            )
        )
        return {
            "unidad_negocio_pk": unidad_pk,
            "usuario_id": usuario_id,
            "margen_minimo_porcentaje": 72,
            "fuentes": {
                "margen_minimo_porcentaje":
                    "USUARIO",
            },
        }

    monkeypatch.setattr(
        routes,
        "_verify_costos_margenes_access",
        fake_verify,
    )

    monkeypatch.setattr(
        routes,
        "resolve_authorized_unidad_scope",
        fake_scope,
    )

    monkeypatch.setattr(
        routes,
        "guardar_configuracion_usuario",
        fake_writer,
    )

    monkeypatch.setattr(
        routes,
        "resolver_configuracion_efectiva",
        fake_resolver,
    )

    payload = ConfiguracionCostosMargenesUsuarioPatch(
        margen_minimo_porcentaje=72,
    )

    result = await routes.actualizar_configuracion_personal(
        payload=payload,
        unidad="ORIGEN",
        current_user=_user(99),
    )

    assert calls["permission"] == [
        (
            99,
            routes.COSTOS_MARGENES_CONFIGURAR,
        )
    ]

    assert calls["scope"] == [
        (
            99,
            routes.COSTOS_MARGENES_CONFIGURAR,
            "ORIGEN",
        )
    ]

    assert calls["writer"] == [
        (
            99,
            {
                "MargenMinimoPorcentaje": 72,
            },
        )
    ]

    assert calls["resolver"] == [
        (
            UNIT_PK,
            99,
        )
    ]

    assert result["ok"] is True

    assert (
        result["configuracion_efectiva"]
        ["fuentes"]
        ["margen_minimo_porcentaje"]
        == "USUARIO"
    )


@pytest.mark.asyncio
async def test_null_explicito_llega_writer(
    monkeypatch,
):
    captured = {}

    monkeypatch.setattr(
        routes,
        "_verify_costos_margenes_access",
        lambda user, permission_code: {
            "permitido": True,
        },
    )

    async def fake_scope(
        current_user,
        permission_code,
        unidad,
    ):
        return _allowed_scope()

    monkeypatch.setattr(
        routes,
        "resolve_authorized_unidad_scope",
        fake_scope,
    )

    def fake_writer(usuario_id, cambios):
        captured.update(cambios)
        return {}

    monkeypatch.setattr(
        routes,
        "guardar_configuracion_usuario",
        fake_writer,
    )

    monkeypatch.setattr(
        routes,
        "resolver_configuracion_efectiva",
        lambda unidad_pk, usuario_id=None: {},
    )

    payload = ConfiguracionCostosMargenesUsuarioPatch(
        margen_minimo_porcentaje=None,
    )

    await routes.actualizar_configuracion_personal(
        payload=payload,
        unidad="ORIGEN",
        current_user=_user(99),
    )

    assert "MargenMinimoPorcentaje" in captured
    assert captured["MargenMinimoPorcentaje"] is None

    assert "MultiploRedondeo" not in captured
    assert "MetodoRedondeo" not in captured


@pytest.mark.asyncio
async def test_payload_vacio_no_llega_writer(
    monkeypatch,
):
    writer_called = False

    monkeypatch.setattr(
        routes,
        "_verify_costos_margenes_access",
        lambda user, permission_code: {
            "permitido": True,
        },
    )

    async def fake_scope(
        current_user,
        permission_code,
        unidad,
    ):
        return _allowed_scope()

    monkeypatch.setattr(
        routes,
        "resolve_authorized_unidad_scope",
        fake_scope,
    )

    def fake_writer(*args, **kwargs):
        nonlocal writer_called
        writer_called = True

    monkeypatch.setattr(
        routes,
        "guardar_configuracion_usuario",
        fake_writer,
    )

    payload = ConfiguracionCostosMargenesUsuarioPatch()

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        await routes.actualizar_configuracion_personal(
            payload=payload,
            unidad="ORIGEN",
            current_user=_user(99),
        )

    assert exc_info.value.status_code == 422
    assert writer_called is False


@pytest.mark.asyncio
async def test_sin_configurar_no_llega_writer(
    monkeypatch,
):
    writer_called = False

    def deny(user, permission_code):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "PERMISO_DENEGADO",
                "permiso_requerido":
                    permission_code,
            },
        )

    monkeypatch.setattr(
        routes,
        "_verify_costos_margenes_access",
        deny,
    )

    def fake_writer(*args, **kwargs):
        nonlocal writer_called
        writer_called = True

    monkeypatch.setattr(
        routes,
        "guardar_configuracion_usuario",
        fake_writer,
    )

    payload = ConfiguracionCostosMargenesUsuarioPatch(
        margen_minimo_porcentaje=72,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        await routes.actualizar_configuracion_personal(
            payload=payload,
            unidad="ORIGEN",
            current_user=_user(99),
        )

    assert exc_info.value.status_code == 403
    assert writer_called is False


@pytest.mark.asyncio
async def test_fuera_alcance_no_llega_writer(
    monkeypatch,
):
    writer_called = False

    monkeypatch.setattr(
        routes,
        "_verify_costos_margenes_access",
        lambda user, permission_code: {
            "permitido": True,
        },
    )

    async def denied_scope(
        current_user,
        permission_code,
        unidad,
    ):
        return SimpleNamespace(
            access_denied=True,
            unidad_pk=None,
            server_id=None,
        )

    monkeypatch.setattr(
        routes,
        "resolve_authorized_unidad_scope",
        denied_scope,
    )

    def fake_writer(*args, **kwargs):
        nonlocal writer_called
        writer_called = True

    monkeypatch.setattr(
        routes,
        "guardar_configuracion_usuario",
        fake_writer,
    )

    payload = ConfiguracionCostosMargenesUsuarioPatch(
        margen_minimo_porcentaje=72,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        await routes.actualizar_configuracion_personal(
            payload=payload,
            unidad="NO_AUTORIZADA",
            current_user=_user(99),
        )

    assert exc_info.value.status_code == 403
    assert writer_called is False


@pytest.mark.asyncio
async def test_sin_identidad_sql_no_llega_writer(
    monkeypatch,
):
    writer_called = False

    monkeypatch.setattr(
        routes,
        "_verify_costos_margenes_access",
        lambda user, permission_code: {
            "permitido": True,
        },
    )

    async def fake_scope(
        current_user,
        permission_code,
        unidad,
    ):
        return _allowed_scope()

    monkeypatch.setattr(
        routes,
        "resolve_authorized_unidad_scope",
        fake_scope,
    )

    monkeypatch.setattr(
        routes,
        "_get_sql_usuario_id",
        lambda user: None,
    )

    def fake_writer(*args, **kwargs):
        nonlocal writer_called
        writer_called = True

    monkeypatch.setattr(
        routes,
        "guardar_configuracion_usuario",
        fake_writer,
    )

    payload = ConfiguracionCostosMargenesUsuarioPatch(
        margen_minimo_porcentaje=72,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        await routes.actualizar_configuracion_personal(
            payload=payload,
            unidad="ORIGEN",
            current_user={},
        )

    assert exc_info.value.status_code == 401
    assert writer_called is False


def test_endpoint_registrado_exactamente_una_vez():
    matching = [
        route
        for route in routes.router.routes
        if getattr(
            route,
            "path",
            None,
        ) == "/costos-margenes/configuracion/usuario"
    ]

    assert len(matching) == 1

    route = matching[0]

    assert "PATCH" in route.methods


def test_schema_no_admite_identidad_ni_scope():
    fields = set(
        ConfiguracionCostosMargenesUsuarioPatch
        .model_fields
    )

    assert fields == {
        "margen_minimo_porcentaje",
        "multiplo_redondeo",
        "metodo_redondeo",
    }
