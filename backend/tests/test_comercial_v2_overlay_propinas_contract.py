from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[2]

JOB = ROOT / (
    "backend/core/scheduler/jobs/"
    "sync_comercial_abiertas_v2_job.py"
)

SCHEMA = ROOT / (
    "backend/modules/comercial_v2/schemas.py"
)

REPOSITORY = ROOT / (
    "backend/modules/comercial_v2/"
    "repository_comercial_edarsahub.py"
)

MIGRATION = ROOT / (
    "backend/database/migrations/"
    "20260729_023_overlay_propinas_separadas_v1.sql"
)


def _function_source(path, function_name):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    lines = text.splitlines()

    for node in tree.body:
        if (
            isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            )
            and node.name == function_name
        ):
            return "\n".join(
                lines[
                    node.lineno - 1:
                    node.end_lineno
                ]
            )

    raise AssertionError(
        f"Función no encontrada: {function_name}"
    )


def test_modelo_overlay_no_es_tabla_duplicada_y_separa_propinas():
    text = SCHEMA.read_text(encoding="utf-8")

    assert "class VentasDiaAbiertasV2(BaseModel)" in text

    assert (
        "propinas_abiertas: Decimal"
        in text
    )

    assert (
        "propinas_cerradas_dia: Decimal"
        in text
    )

    assert "propinas_total: Decimal" in text


def test_softrestaurant_excluye_propinas_de_ventas():
    text = JOB.read_text(encoding="utf-8")

    assert (
        "ISNULL(total, 0) - ISNULL(propina, 0)"
        in text
    )

    assert (
        "AS propinas_abiertas"
        in text
    )

    assert (
        "AS propinas_cerradas_dia"
        in text
    )

    assert (
        "propinas_total = "
        "propinas_abiertas + propinas_cerradas_dia"
        in text
    )

    assert (
        "propinas_total=propinas_total"
        in text
    )


def test_repository_persiste_propinas_y_no_duplica_resolvedor():
    text = REPOSITORY.read_text(
        encoding="utf-8"
    )

    function_text = _function_source(
        REPOSITORY,
        "upsert_ventas_dia_abiertas",
    )

    assert (
        "# V1.0-COMPAT-UNIDAD-CODIGO"
        not in function_text
    )

    assert function_text.count(
        "UnidadesService.get_by_pk("
    ) == 1

    for field in (
        "propinas_abiertas",
        "propinas_cerradas_dia",
        "propinas_total",
    ):
        assert field in function_text

    assert (
        "CK_ComercialVentasDia_PropinasTotal"
        not in text
    )


def test_migracion_amplia_una_sola_tabla_y_actualiza_runtime():
    text = MIGRATION.read_text(
        encoding="utf-8"
    )

    assert (
        "ALTER TABLE "
        "dbo.Comercial_Ventas_Dia_Abiertas_v2"
        in text
    )

    assert "CREATE TABLE" not in text.upper()

    assert (
        "ISNULL(s.propinas_total, 0)"
        in text
    )

    assert (
        "CREATE OR ALTER VIEW"
        in text
    )

    assert (
        "CK_ComercialVentasDia_PropinasTotal"
        in text
    )



def test_mpro_usa_estados_reales_y_propina_por_folio():
    text = JOB.read_text(encoding="utf-8")
    tree = ast.parse(text)

    expected_names = {
        "QUERY_MPRO_VENTAS_ABIERTAS_ORIGEN",
        "QUERY_MPRO_CERRADAS_HOY_ORIGEN",
        "QUERY_MPRO_VENTAS_ABIERTAS_QRO",
        "QUERY_MPRO_CERRADAS_HOY_QRO",
    }

    queries = {}

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue

        if len(node.targets) != 1:
            continue

        target = node.targets[0]

        if (
            isinstance(target, ast.Name)
            and target.id in expected_names
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            queries[target.id] = node.value.value

    assert set(queries) == expected_names

    for name, query in queries.items():
        assert "Co_Propina" in query
        assert "GROUP BY" in query
        assert "c.Co_Folio" in query

        assert (
            "SUM(DISTINCT ISNULL(c.Co_Personas"
            not in query
        )

        assert (
            "c.Es_Cve_Estado = 'AC'"
            not in query
        )

        assert (
            "c.Es_Cve_Estado <> 'AC'"
            not in query
        )

        if "ABIERTAS" in name:
            assert "AS propinas_abiertas" in query
            assert "c.Es_Cve_Estado IN ('AC', 'IM')" in query

        if "CERRADAS" in name:
            assert "AS propinas_cerradas_dia" in query
            assert "c.Es_Cve_Estado = 'PA'" in query

    function_text = _function_source(
        JOB,
        "execute_sync_comercial_abiertas_v2",
    )

    for field in (
        "propinas_abiertas=propinas_abiertas",
        "propinas_cerradas_dia=propinas_cerradas_dia",
        "propinas_total=propinas_total",
    ):
        assert field in function_text
