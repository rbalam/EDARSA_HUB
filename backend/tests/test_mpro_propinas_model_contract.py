from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[2]

JOB = ROOT / (
    "backend/core/scheduler/jobs/"
    "sync_comercial_abiertas_v2_job.py"
)


def _mpro_constructor_and_segment():
    text = JOB.read_text(encoding="utf-8")
    tree = ast.parse(text)

    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "execute_sync_comercial_abiertas_v2"
    )

    calls = []

    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue

        if not (
            isinstance(node.func, ast.Name)
            and node.func.id == "VentasDiaAbiertasV2"
        ):
            continue

        for keyword in node.keywords:
            if (
                keyword.arg == "sistema_origen"
                and isinstance(keyword.value, ast.Attribute)
                and keyword.value.attr == "MPRO"
            ):
                calls.append(node)
                break

    assert len(calls) == 1

    call = calls[0]
    lines = text.splitlines()

    start = None

    for index in range(call.lineno - 2, -1, -1):
        if "Extraer valores finales" in lines[index]:
            start = index
            break

    assert start is not None

    segment = "\n".join(
        lines[start:call.end_lineno]
    )

    return call, segment


def test_mpro_transporta_propinas_al_modelo():
    call, _ = _mpro_constructor_and_segment()

    keywords = {
        keyword.arg
        for keyword in call.keywords
        if keyword.arg
    }

    assert {
        "propinas_abiertas",
        "propinas_cerradas_dia",
        "propinas_total",
    }.issubset(keywords)


def test_mpro_calcula_propinas_desde_respuestas_api():
    _, segment = _mpro_constructor_and_segment()

    assert (
        "abiertas_data.get('propinas_abiertas')"
        in segment
    )

    assert (
        "cerradas_data.get('propinas_cerradas_dia')"
        in segment
    )

    assert (
        "propinas_total = "
        "propinas_abiertas + propinas_cerradas_dia"
        in segment
    )


def test_mpro_no_mezcla_propinas_con_ventas():
    _, segment = _mpro_constructor_and_segment()

    assert (
        "total_estimado_dia = "
        "ventas_abiertas + ventas_cerradas_dia"
        in segment
    )

    assert (
        "propinas_total = "
        "propinas_abiertas + propinas_cerradas_dia"
        in segment
    )
