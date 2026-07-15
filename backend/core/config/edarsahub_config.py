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


_PROFILE_PREFIXES = {
    "default": "EDARSAHUB_SQL",
    "writer": "EDARSAHUB_SQL_WRITER",
}


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variable obligatoria no configurada: {name}")
    return value


def get_edarsahub_sql_config(profile: str = "default") -> EdarsaHubSQLConfig:
    """
    Config canónica EDARSAHUB SQL.

    Perfiles permitidos:
    - default: configuracion canonica EDARSAHUB_SQL_*
    - writer: configuracion de escritura EDARSAHUB_SQL_WRITER_*

    Cualquier otro perfil esta prohibido.
    """
    normalized = (profile or "default").lower()
    prefix = _PROFILE_PREFIXES.get(normalized)
    if not prefix:
        raise ValueError(f"Perfil EDARSAHUB SQL no soportado: {profile}")

    return EdarsaHubSQLConfig(
        host=_required(f"{prefix}_HOST"),
        port=int(os.getenv(f"{prefix}_PORT", "1433")),
        database=_required(f"{prefix}_DATABASE"),
        user=_required(f"{prefix}_USER"),
        password=_required(f"{prefix}_PASSWORD"),
        profile=normalized,
    )
