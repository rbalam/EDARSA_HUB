"""Conexiones canónicas a fuentes POS para la sincronización de Cortes Z.

Separa EDARSAHUB SQL —catálogo, destino y bitácoras— de los SQL externos
SoftRestaurant y MPRO. Nunca permite usar EDARSAHUB como base origen.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from core.sql_first.connection_factory import get_external_sql_connection


_REQUIRED_KEYS = ("host", "port", "database", "user", "password")


def build_cortes_z_source_config(
    conn_info: Dict[str, Any],
    *,
    as_dict: bool = True,
) -> Dict[str, Any]:
    """Construye configuración externa validada, sin imprimir credenciales."""
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
            "La base EDARSAHUB no puede utilizarse como origen de Cortes Z"
        )

    return {
        "host": conn_info["host"],
        "port": int(conn_info["port"]),
        "database": database,
        "username": conn_info["user"],
        "password": conn_info["password"],
        "login_timeout": 30,
        "timeout": 30,
        "as_dict": as_dict,
    }


def open_cortes_z_source_connection(
    conn_info: Dict[str, Any],
    *,
    as_dict: bool = True,
    opener: Callable[[Dict[str, Any]], Any] = get_external_sql_connection,
):
    """Abre exclusivamente una conexión SQL externa al POS configurado."""
    return opener(
        build_cortes_z_source_config(conn_info, as_dict=as_dict)
    )


def sincronizar_unidad_softrestaurant_canonica(**kwargs):
    """Ejecuta el sincronizador existente usando conexión externa canónica."""
    from modules.finanzas import sync_cortes_softrestaurant as sync_module

    original = sync_module.get_softrestaurant_connection
    sync_module.get_softrestaurant_connection = lambda conn_info: (
        open_cortes_z_source_connection(conn_info, as_dict=False)
    )
    try:
        return sync_module.sincronizar_unidad_softrestaurant(**kwargs)
    finally:
        sync_module.get_softrestaurant_connection = original


def sincronizar_unidad_mpro_canonica(**kwargs):
    """Ejecuta el sincronizador existente usando conexión externa canónica."""
    from modules.finanzas import sync_cortes_mpro as sync_module

    original = sync_module.get_mpro_connection
    sync_module.get_mpro_connection = lambda conn_info: (
        open_cortes_z_source_connection(conn_info, as_dict=True)
    )
    try:
        return sync_module.sincronizar_unidad_mpro(**kwargs)
    finally:
        sync_module.get_mpro_connection = original
