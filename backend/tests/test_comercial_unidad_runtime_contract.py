import ast
import asyncio
from pathlib import Path
from typing import Optional
from unittest.mock import Mock

from fastapi import HTTPException


BACKEND = Path(__file__).resolve().parents[1]
INTEL = (BACKEND / "modules/inteligencia_comercial/routes.py").read_text(
    encoding="utf-8"
)
REPORTEADOR = (BACKEND / "modules/reporteador_bi/routes.py").read_text(
    encoding="utf-8"
)
VALIDATION_020 = (
    BACKEND / "database/validation/20260717_020_comercial_runtime_contract_validation.sql"
).read_text(encoding="utf-8")

UUID = "9bc05ced-6b2b-4a0a-aa90-ce649b78e12c"
CODIGO = "130MID"


def _load_functions(source, names, namespace=None):
    wanted = set(names)
    nodes = []
    for node in ast.parse(source).body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in wanted
        ):
            node.decorator_list = []
            nodes.append(node)
    assert {node.name for node in nodes} == wanted
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    scope = {
        "Optional": Optional,
        "HTTPException": HTTPException,
        "Query": lambda default=None, **_kwargs: default,
    }
    scope.update(namespace or {})
    exec(compile(module, "<contract-functions>", "exec"), scope)
    return scope


def _if_exists_blocks(sql):
    marker = "IF EXISTS ("
    cursor = 0
    blocks = []
    while True:
        start = sql.find(marker, cursor)
        if start < 0:
            return blocks
        open_paren = sql.find("(", start)
        depth = 0
        in_string = False
        close_paren = None
        index = open_paren
        while index < len(sql):
            char = sql[index]
            if char == "'":
                if (
                    in_string
                    and index + 1 < len(sql)
                    and sql[index + 1] == "'"
                ):
                    index += 2
                    continue
                in_string = not in_string
            elif not in_string:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        close_paren = index
                        break
            index += 1
        assert close_paren is not None
        begin = sql.find("BEGIN", close_paren + 1)
        assert sql[close_paren + 1:begin].strip() == ""
        end = sql.find("END;", begin + len("BEGIN"))
        assert begin >= 0 and end >= 0
        blocks.append(
            {
                "start": start,
                "condition": sql[open_paren + 1:close_paren],
                "body": sql[begin + len("BEGIN"):end],
            }
        )
        cursor = end + len("END;")


def test_portal_resuelve_pk_con_servicio_sin_consultar_kpis(monkeypatch):
    resolver = Mock(return_value=UUID)
    forbidden_query = Mock(
        side_effect=AssertionError("No debe consultar KPIs para resolver unidad")
    )
    scope = _load_functions(INTEL, ["_unidad_pks_canonicas_portal"])
    monkeypatch.setitem(scope, "_resolver_unidad_pk_runtime", resolver)
    monkeypatch.setitem(scope, "execute_query", forbidden_query)

    assert scope["_unidad_pks_canonicas_portal"]("130° Mérida") == [UUID]
    resolver.assert_called_once_with("130° Mérida")
    forbidden_query.assert_not_called()


def test_detalle_where_traduce_uuid_a_codigo_legacy(monkeypatch):
    resolver_codigo = Mock(return_value=CODIGO)
    scope = _load_functions(
        INTEL,
        ["_unidad_codigo_filtro", "_detalle_where"],
    )
    monkeypatch.setitem(
        scope,
        "_resolver_unidad_codigo_runtime",
        resolver_codigo,
    )

    where, params = scope["_detalle_where"](
        UUID,
        "2026-07-01",
        "2026-07-17",
        alias="d",
    )

    resolver_codigo.assert_called_once_with(UUID)
    assert "d.unidad_negocio_id = %s" in where
    assert params == ("2026-07-01", "2026-07-17", CODIGO)
    assert UUID not in params


def test_ambientacion_envia_codigo_legacy_a_execute_query(monkeypatch):
    resolver_codigo = Mock(return_value=CODIGO)
    intel_scope = _load_functions(INTEL, ["_unidad_codigo_filtro"])
    monkeypatch.setitem(
        intel_scope,
        "_resolver_unidad_codigo_runtime",
        resolver_codigo,
    )

    execute_query = Mock(return_value=[])
    report_scope = _load_functions(
        REPORTEADOR,
        ["ambientacion"],
        {
            "_u": lambda _unidad: UUID,
            "_resolver_rango": lambda *_args: (
                "2026-07-01",
                "2026-07-17",
                None,
                None,
                "Julio 2026",
            ),
            "_unidad_codigo_filtro": intel_scope["_unidad_codigo_filtro"],
            "execute_query": execute_query,
            "_real_horario": lambda *_args: [],
            "_envelope": lambda disponible, **extra: {
                "disponible": disponible,
                **extra,
            },
        },
    )

    result = asyncio.run(
        report_scope["ambientacion"](
            unidad=UUID,
            periodo="mes",
            fecha_inicio="2026-07-01",
            fecha_fin="2026-07-17",
        )
    )

    resolver_codigo.assert_called_once_with(UUID)
    execute_query.assert_called_once()
    params = execute_query.call_args.args[1]
    assert params == ("2026-07-01", "2026-07-17", CODIGO)
    assert UUID not in params
    assert result["disponible"] is True


def test_validation_020_bloquea_historicos_antes_del_reporte():
    blocks = _if_exists_blocks(VALIDATION_020)
    report_position = VALIDATION_020.index(
        "COUNT_BIG(*) AS filas_historicas_activas"
    )

    expected = {
        "THROW 51111": ("ticket_promedio", "tickets_total"),
        "THROW 51112": ("pax_promedio", "pax_total"),
    }
    for throw, (ratio, denominator) in expected.items():
        matching = [block for block in blocks if throw in block["body"]]
        assert len(matching) == 1
        block = matching[0]
        assert block["start"] < report_position
        assert "FROM dbo.Comercial_KPIs_Diarios_v2" in block["condition"]
        assert "ISNULL(activo, 1) = 1" in block["condition"]
        assert "ISNULL(es_demo, 0) = 0" in block["condition"]
        assert f"{ratio} IS NULL" in block["condition"]
        assert f"ISNULL({denominator}, 0) > 0" in block["condition"]
        assert "ABS(" in block["condition"]
