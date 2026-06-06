import os
from dataclasses import dataclass

@dataclass(frozen=True)
class EdarsaHubSQLConfig:
    host: str
    port: int
    database: str
    user: str
    password: str

def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variable obligatoria no configurada: {name}")
    return value

def get_edarsahub_sql_config() -> EdarsaHubSQLConfig:
    return EdarsaHubSQLConfig(
        host=_required("EDARSAHUB_SQL_HOST"),
        port=int(os.getenv("EDARSAHUB_SQL_PORT", "1433")),
        database=_required("EDARSAHUB_SQL_DATABASE"),
        user=_required("EDARSAHUB_SQL_USER"),
        password=_required("EDARSAHUB_SQL_PASSWORD"),
    )
