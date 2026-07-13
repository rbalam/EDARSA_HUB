from __future__ import annotations

from typing import Any

import pytest

from core.connections.hrlectura_connection_factory import (
    CANONICAL_PROFILE,
    EXPECTED_SQL_USER,
    ConfiguredLoginMismatch,
    ConnectionNotCreated,
    build_hrlectura_connection_factory,
)


def test_canonical_constants_are_fixed() -> None:
    assert CANONICAL_PROFILE == "default"
    assert EXPECTED_SQL_USER == "HRLectura"


def test_accepts_exact_hrlectura_login() -> None:
    expected_connection = object()
    calls: list[tuple[str, str]] = []

    def config_loader(profile: str) -> dict[str, str]:
        calls.append(("config", profile))
        return {"user": "HRLectura"}

    def connection_opener(profile: str) -> object:
        calls.append(("open", profile))
        return expected_connection

    factory = build_hrlectura_connection_factory(
        config_loader=config_loader,
        connection_opener=connection_opener,
    )

    assert factory() is expected_connection
    assert calls == [
        ("config", "default"),
        ("open", "default"),
    ]


def test_uses_exclusively_default_profile() -> None:
    loaded_profiles: list[str] = []
    opened_profiles: list[str] = []
    expected_connection = object()

    def config_loader(profile: str) -> dict[str, str]:
        loaded_profiles.append(profile)
        return {"user": "HRLectura"}

    def connection_opener(profile: str) -> object:
        opened_profiles.append(profile)
        return expected_connection

    factory = build_hrlectura_connection_factory(
        config_loader=config_loader,
        connection_opener=connection_opener,
    )

    assert factory() is expected_connection
    assert loaded_profiles == ["default"]
    assert opened_profiles == ["default"]


@pytest.mark.parametrize(
    "configured_login",
    [
        "GptLectura",
        "GptEscritura",
        "gptread",
        "sa",
        "",
        None,
    ],
)
def test_rejects_forbidden_logins_before_opening(
    configured_login: Any,
) -> None:
    opener_calls: list[str] = []

    def config_loader(profile: str) -> dict[str, Any]:
        assert profile == "default"
        return {"user": configured_login}

    def connection_opener(profile: str) -> object:
        opener_calls.append(profile)
        return object()

    factory = build_hrlectura_connection_factory(
        config_loader=config_loader,
        connection_opener=connection_opener,
    )

    with pytest.raises(ConfiguredLoginMismatch):
        factory()

    assert opener_calls == []


@pytest.mark.parametrize(
    "configured_login",
    [
        "hrlectura",
        "HRLECTURA",
        "HrLectura",
    ],
)
def test_rejects_hrlectura_with_incorrect_casing(
    configured_login: str,
) -> None:
    opener_calls: list[str] = []

    factory = build_hrlectura_connection_factory(
        config_loader=lambda profile: {
            "user": configured_login,
        },
        connection_opener=lambda profile: opener_calls.append(
            profile
        ),
    )

    with pytest.raises(ConfiguredLoginMismatch):
        factory()

    assert opener_calls == []


def test_accepts_username_field() -> None:
    expected_connection = object()

    factory = build_hrlectura_connection_factory(
        config_loader=lambda profile: {
            "username": "HRLectura",
        },
        connection_opener=lambda profile: expected_connection,
    )

    assert factory() is expected_connection


def test_aborts_when_opener_returns_none() -> None:
    opened_profiles: list[str] = []

    def connection_opener(profile: str) -> None:
        opened_profiles.append(profile)
        return None

    factory = build_hrlectura_connection_factory(
        config_loader=lambda profile: {
            "user": "HRLectura",
        },
        connection_opener=connection_opener,
    )

    with pytest.raises(ConnectionNotCreated):
        factory()

    assert opened_profiles == ["default"]


@pytest.mark.parametrize(
    "invalid_loader",
    [
        object(),
        "",
        False,
        0,
    ],
)
def test_requires_callable_config_loader(
    invalid_loader: Any,
) -> None:
    with pytest.raises(
        TypeError,
        match="config_loader debe ser invocable",
    ):
        build_hrlectura_connection_factory(
            config_loader=invalid_loader,
            connection_opener=lambda profile: object(),
        )


@pytest.mark.parametrize(
    "invalid_opener",
    [
        object(),
        "",
        False,
        0,
    ],
)
def test_requires_callable_connection_opener(
    invalid_opener: Any,
) -> None:
    with pytest.raises(
        TypeError,
        match="connection_opener debe ser invocable",
    ):
        build_hrlectura_connection_factory(
            config_loader=lambda profile: {
                "user": "HRLectura",
            },
            connection_opener=invalid_opener,
        )
