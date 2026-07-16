from __future__ import annotations

import pytest

from modules.finanzas.cortes_z_source_connections import (
    build_cortes_z_source_config,
    open_cortes_z_source_connection,
)


def _valid_conn_info():
    return {
        "host": "pos.example.internal",
        "port": 1433,
        "database": "CENTRAL2020",
        "user": "pos_reader",
        "password": "secret-value",
    }


def test_rechaza_edarsahub_como_base_origen():
    conn_info = _valid_conn_info()
    conn_info["database"] = "EDARSAHUB"

    with pytest.raises(RuntimeError, match="no puede utilizarse como origen"):
        build_cortes_z_source_config(conn_info)


def test_exige_configuracion_pos_completa():
    conn_info = _valid_conn_info()
    conn_info["password"] = ""

    with pytest.raises(ValueError, match="password"):
        build_cortes_z_source_config(conn_info)


def test_abre_mediante_fabrica_externa_con_configuracion_canonica():
    received = []
    sentinel = object()

    def opener(config):
        received.append(config)
        return sentinel

    result = open_cortes_z_source_connection(
        _valid_conn_info(),
        opener=opener,
    )

    assert result is sentinel
    assert received == [{
        "host": "pos.example.internal",
        "port": 1433,
        "database": "CENTRAL2020",
        "username": "pos_reader",
        "password": "secret-value",
        "login_timeout": 30,
        "timeout": 30,
        "as_dict": True,
    }]
