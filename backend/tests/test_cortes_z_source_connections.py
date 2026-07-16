from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.connections.pos_runtime_resolver import (
    PosRuntimeContext,
    PosRuntimeMappingError,
)


BACKEND = Path(__file__).resolve().parents[1]
JOB_FILE = BACKEND / "core" / "scheduler" / "jobs" / "sync_ingresos_job.py"
SERVICE_FILE = BACKEND / "modules" / "finanzas" / "cortes_z_runtime_sync.py"


def _context(database: str = "CENTRAL2020") -> PosRuntimeContext:
    return PosRuntimeContext(
        unidad_negocio_pk="unit-pk",
        unidad_codigo="UNIT01",
        unidad_nombre="Unidad Uno",
        empresa_id="empresa-pk",
        server_id="server-pk",
        sucursal_origen_id="0021",
        sucursal_legacy_id=21,
        system_type="MANAGEMENTPRO",
        host="pos.example.internal",
        port=1433,
        instance=None,
        database=database,
        username="pos_reader",
        password="secret-value",
    )


def test_rechaza_edarsahub_como_base_origen_pos():
    with pytest.raises(PosRuntimeMappingError, match="base origen POS"):
        _context(database="EDARSAHUB").external_connection_config(as_dict=True)


def test_config_externa_no_contiene_alias_de_conexion_central():
    config = _context().external_connection_config(as_dict=True)
    assert config["database"] == "CENTRAL2020"
    assert config["username"] == "pos_reader"
    assert "EDARSAHUB_SQL_HOST" not in config
    assert "server_id" not in config


def test_job_descubre_unidades_desde_catalogo_canonico():
    source = JOB_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}

    assert "list_pos_runtime_contexts" in names
    assert "sync_cortes_z_context" in names
    assert "UNIDADES" not in names

    forbidden_literals = {
        "130° MERIDA",
        "130° QUERETARO",
        "CIENFUEGOS",
        "LA ESTELAR",
        "ORIGEN",
    }
    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert forbidden_literals.isdisjoint(literals)


def test_servicio_no_modifica_funciones_globales_de_sync():
    source = SERVICE_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                assert not isinstance(target, ast.Attribute)

    assert "get_external_sql_connection" in source
    assert "get_sql_connection" not in source
    assert "cortes_z_source_connections" not in source
