"""Conexiones canónicas a fuentes POS para la sincronización de Cortes Z.

Este adaptador separa explícitamente:
- EDARSAHUB SQL: catálogo, destino y bitácoras.
- SQL externo POS: lectura de SoftRestaurant y MPRO.

Nunca permite usar la base EDARSAHUB como origen de cortes.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from core.sql_first.connection_factory import get_external_sql_connection


_REQUIRED_KEYS = ("host", "port", "database", "user", "password")


def _build_external_config(conn_info: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(conn_info, dict):
        raise TypeError("conn_info debe ser un diccionario")

    missing = [key for key in _REQUIRED_KEYS if not conn_info.get(key)]
    if missing:
        raise ValueError(
            "Configuración POS incompleta: " + ", ".join(sorted(missing))
        )

    database = str(conn_info["database"]).strip()
    if database.upper() == "EDARSAHUB":
        raise RuntimeError(
            "Fuente POS inválida: la base EDARSAHUB no puede usarse como origen de Cortes Z"
        )

    return {
        "host": conn_info["host"],
        "port": int(conn_info["port"]),
        "database": database,
        "username": conn_info["user"],
