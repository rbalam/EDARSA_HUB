"""
Factory fail-closed para la conexión SQL read-only de EDARSAHUB.

Único login autorizado: HRLectura.
No usa gptread, GptLectura ni perfiles alternativos.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


CANONICAL_PROFILE = "default"
EXPECTED_SQL_USER = "HRLectura"


class HRLecturaFactoryError(RuntimeError):
    """Error base del factory HRLectura."""


class ConfiguredLoginMismatch(HRLecturaFactoryError):
    """El perfil configurado no corresponde a HRLectura."""


class ConnectionNotCreated(HRLecturaFactoryError):
    """El abridor no devolvió una conexión."""


def _configured_user(config: Any) -> str:
    if isinstance(config, Mapping):
        value = (
            config.get("user")
            or config.get("username")
            or config.get("usuario")
        )
    else:
        value = (
            getattr(config, "user", None)
            or getattr(config, "username", None)
            or getattr(config, "usuario", None)
        )

    return str(value or "").strip()


def _load_default_config(profile: str) -> Any:
    from core.config.edarsahub_config import get_edarsahub_sql_config

    return get_edarsahub_sql_config(profile=profile)


def _open_default_connection(profile: str) -> Any:
    from core.sql_first.db import get_sql_connection

    return get_sql_connection(profile=profile)


def build_hrlectura_connection_factory(
    *,
    config_loader: Callable[[str], Any] | None = None,
    connection_opener: Callable[[str], Any] | None = None,
) -> Callable[[], Any]:
    """
    Construye una factory que falla antes de conectar si el perfil
    default no está configurado exactamente con HRLectura.

    La identidad SQL efectiva completa se valida posteriormente mediante:
    DB_NAME(), SUSER_SNAME() y USER_NAME().
    """

    loader = (
        _load_default_config
        if config_loader is None
        else config_loader
    )
    opener = (
        _open_default_connection
        if connection_opener is None
        else connection_opener
    )

    if not callable(loader):
        raise TypeError("config_loader debe ser invocable")

    if not callable(opener):
        raise TypeError("connection_opener debe ser invocable")

    def connection_factory() -> Any:
        config = loader(CANONICAL_PROFILE)
        login = _configured_user(config)

        if login != EXPECTED_SQL_USER:
            raise ConfiguredLoginMismatch(
                "Perfil default no autorizado: "
                f"login={login!r}; esperado={EXPECTED_SQL_USER!r}"
            )

        connection = opener(CANONICAL_PROFILE)

        if connection is None:
            raise ConnectionNotCreated(
                "No se obtuvo una conexión SQL"
            )

        return connection

    return connection_factory
