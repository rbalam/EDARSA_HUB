from pathlib import Path
import ast
import re


ROOT = Path(__file__).resolve().parents[2]

REPO = (
    ROOT
    / "backend/modules/comercial_v2/"
      "repository_comercial_edarsahub.py"
)

SYNC = (
    ROOT
    / "backend/modules/comercial_v2/"
      "sync_comercial_edarsahub.py"
)

JOB = (
    ROOT
    / "backend/core/scheduler/jobs/"
      "sync_comercial_abiertas_v2_job.py"
)


def _function_block(path: Path, function_name: str) -> str:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    lines = text.splitlines()

    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ) and node.name == function_name:
            return "\n".join(
                lines[node.lineno - 1 : node.end_lineno]
            )

    raise AssertionError(
        f"No se encontró {function_name} en {path}"
    )


def test_kpi_comercial_resuelve_codigo_fail_closed():
    text = REPO.read_text(encoding="utf-8")

    assert "# V1.0-COMERCIAL-KPI-UNIDAD-CODIGO" in text
    assert (
        "UnidadesService.get_by_pk(kpi.unidad_negocio_pk)"
        in text
    )
    assert (
        "_unidad_info.get('codigo') "
        "or kpi.unidad_negocio_pk"
        not in text
    )


def test_ventas_abiertas_escribe_codigo_legacy():
    block = _function_block(
        REPO,
        "upsert_ventas_dia_abiertas",
    )

    assert (
        "# V1.0-COMERCIAL-ABIERTAS-UNIDAD-CODIGO"
        in block
    )
    assert (
        "get_operational_window(unidad_codigo)"
        in block
    )
    assert (
        "WHERE unidad_negocio_id = '{unidad_codigo}'"
        in block
    )
    assert (
        "WHERE unidad_negocio_id = "
        "'{ventas.unidad_negocio_pk}'"
        not in block
    )

    assert re.search(
        r"""
        INSERT\s+INTO\s+
        Comercial_Ventas_Dia_Abiertas_v2
        .*?
        VALUES\s*\(
        \s*'\{new_id\}',
        \s*'\{unidad_codigo\}',
        """,
        block,
        re.DOTALL | re.VERBOSE,
    )


def test_resolver_pk_no_acepta_aliases_legacy():
    block = _function_block(
        SYNC,
        "_resolver_unidad_negocio_pk_from_config",
    )

    forbidden = (
        '"unidad_negocio_id"',
        '"UnidadNegocioID"',
        '"id_unidad_negocio"',
        '"unidad_id"',
        '"UnidadID"',
    )

    for value in forbidden:
        assert value not in block

    assert '"unidad_negocio_pk"' in block
    assert '"UnidadNegocioPK"' in block


def test_job_abiertas_transporta_pk_y_codigo():
    loader = _function_block(
        JOB,
        "_get_unidades_from_edarsahub",
    )

    text = JOB.read_text(encoding="utf-8")

    assert "UnidadesService.get_all()" in loader
    assert "core.unidades_registry" not in loader
    assert '"unidad_negocio_pk": unidad_pk' in loader
    assert '"unidad_negocio_id": unidad_codigo' in loader

    assert not re.search(
        r"unidad_negocio_pk\s*=\s*unidad_id",
        text,
    )

    assert (
        'unidad_negocio_pk=unidad["unidad_negocio_pk"]'
        in text
    )


def test_no_uuid_unidad_hardcodeado_en_flujos_corregidos():
    uuid_pattern = re.compile(
        r"\b[0-9a-fA-F]{8}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{12}\b"
    )

    for path in (REPO, SYNC, JOB):
        assert not uuid_pattern.search(
            path.read_text(encoding="utf-8")
        )


# V1.0-COMERCIAL-POS-RUNTIME-RESOLVER

def test_sync_comercial_usa_pos_runtime_resolver():
    block = _function_block(
        SYNC,
        "get_server_connection_config",
    )

    assert (
        "core.connections.pos_runtime_resolver"
        in block
    )
    assert "list_pos_runtime_contexts" in block
    assert "external_connection_config" in block

    assert "FROM Servidores_Conexiones" not in block
    assert "JOIN Servidores_Conexiones" not in block
    assert "password_encrypted" not in block
    assert "decrypt_secret" not in block
    assert "password = pwd_enc" not in block


def test_sync_comercial_resuelve_por_pk_y_server():
    text = SYNC.read_text(encoding="utf-8")

    assert text.count(
        "config.unidad_negocio_pk,"
    ) >= 2

    assert (
        "get_server_connection_config("
        in text
    )

    assert (
        "get_server_connection_config(config.server_id)"
        not in text
    )


# V1.0-COMERCIAL-PYTDS-POS

def test_sync_comercial_usa_drivers_sql_sin_odbc():
    block = _function_block(
        SYNC,
        "execute_query_on_server",
    )

    assert "import pytds" in block
    assert "import pymssql" in block
    assert "pytds.connect" in block

    assert '"PYTDS_DIRECT_PORT"' in block
    assert '"PYTDS_NAMED_INSTANCE"' in block
    assert '"PYMSSQL_DIRECT_PORT"' in block

    assert "pyodbc" not in block
    assert "pymssql.connect" in block
    assert "execute_sql_query" not in block


def test_sync_comercial_no_combina_instancia_y_puerto():
    block = _function_block(
        SYNC,
        "execute_query_on_server",
    )

    assert 'f"{host}\\\\{instance}"' in block
    assert '"port": None' in block


# V1.0-COMERCIAL-HYBRID-DRIVER

def test_sync_comercial_selecciona_driver_por_topologia():
    block = _function_block(
        SYNC,
        "execute_query_on_server",
    )

    assert '"PYTDS_DIRECT_PORT"' in block
    assert '"PYTDS_NAMED_INSTANCE"' in block
    assert '"PYMSSQL_DIRECT_PORT"' in block

    assert "if instance:" in block
    assert "pymssql.connect" in block
    assert "pytds.connect" in block

    assert "pyodbc" not in block
    assert "execute_sql_query" not in block


# V1.0-COMERCIAL-SQL-DATE-112

def test_queries_comerciales_usan_fecha_sql_112():
    text = SYNC.read_text(encoding="utf-8")

    old_start = "CAST('{fecha_inicio}' AS DATETIME)"
    old_end = "CAST('{fecha_fin}' AS DATETIME)"

    new_start = (
        "CONVERT("
        "DATETIME, "
        "REPLACE('{fecha_inicio}', '-', ''), "
        "112"
        ")"
    )

    new_end = (
        "CONVERT("
        "DATETIME, "
        "REPLACE('{fecha_fin}', '-', ''), "
        "112"
        ")"
    )

    assert old_start not in text
    assert old_end not in text

    assert text.count(new_start) >= 2
    assert text.count(new_end) >= 2


# V1.0-VENTAS-DIA-SIN-PROPINA-DATE112

def test_ventas_dia_soft_excluye_propina_y_usa_date112():
    from pathlib import Path as _Path

    job_text = _Path(
        "backend/core/scheduler/jobs/"
        "sync_comercial_abiertas_v2_job.py"
    ).read_text(encoding="utf-8")

    assert "FROM tempcheques" in job_text

    assert (
        "ISNULL(total, 0) - ISNULL(propina, 0)"
        in job_text
    )

    assert (
        "REPLACE('{fecha_operacion}', '-', '')"
        in job_text
    )

    assert (
        "CAST(c.Co_Fecha AS DATE) = "
        "'{fecha_operacion}'"
        not in job_text
    )

    assert "unidad_negocio_pk=unidad_id" not in job_text
