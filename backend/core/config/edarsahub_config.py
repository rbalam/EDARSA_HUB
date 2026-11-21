import os
from dataclasses import dataclass


@dataclass(frozen=True)
class EdarsaHubSQLConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    profile: str = "default"


_DEFAULT_PREFIX = "EDARSAHUB_SQL"
_WRITER_CREDENTIAL_PREFIX = "EDARSAHUB_SQL_WRITER"
_SUPPORTED_PROFILES = {"default", "writer"}


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Variable obligatoria no configurada: {name}"
        )
    return value


def _base_connection_fields() -> tuple[str, int, str]:
    return (
        _required(f"{_DEFAULT_PREFIX}_HOST"),
        int(os.getenv(f"{_DEFAULT_PREFIX}_PORT", "1433")),
        _required(f"{_DEFAULT_PREFIX}_DATABASE"),
    )


def get_edarsahub_sql_config(
    profile: str = "default",
) -> EdarsaHubSQLConfig:
    """
    Configuracion SQL canonica de EDARSAHUB.

    El perfil default conserva la identidad de lectura existente.
    El perfil writer reutiliza host, puerto y base del perfil default
    y solo resuelve credenciales dedicadas desde
    EDARSAHUB_SQL_WRITER_USER y EDARSAHUB_SQL_WRITER_PASSWORD.

    Ningun perfil lee archivos .env ni descifra secretos.
    """
    normalized = (profile or "default").lower()

    if normalized not in _SUPPORTED_PROFILES:
        raise ValueError(
            "Perfil EDARSAHUB SQL no soportado: "
            f"{profile}"
        )

    host, port, database = _base_connection_fields()

    if normalized == "default":
        user = _required(f"{_DEFAULT_PREFIX}_USER")
        password = _required(f"{_DEFAULT_PREFIX}_PASSWORD")
    else:
        user = _required(f"{_WRITER_CREDENTIAL_PREFIX}_USER")
        password = _required(f"{_WRITER_CREDENTIAL_PREFIX}_PASSWORD")

    return EdarsaHubSQLConfig(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        profile=normalized,
    )
