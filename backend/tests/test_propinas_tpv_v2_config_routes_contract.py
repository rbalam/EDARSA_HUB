from pathlib import Path


ROOT = Path(__file__).parents[2]

FRONTEND = (
    ROOT
    / "frontend"
    / "src"
    / "components"
    / "PropinasTPV.jsx"
)

SERVER = ROOT / "backend" / "server.py"

ROUTES_V2 = (
    ROOT
    / "backend"
    / "modules"
    / "finanzas"
    / "propinas_tpv"
    / "routes_edarsahub.py"
)


def test_propinas_frontend_config_usa_solo_v2():
    src = FRONTEND.read_text(encoding="utf-8")

    assert "/api/finanzas/propinas/v2/config/all" in src
    assert "/api/finanzas/propinas/v2/config`" in src
    assert (
        "/api/finanzas/propinas/v2/config/${configData.id}"
        in src
    )

    assert "/api/finanzas/propinas/config/all" not in src
    assert "/api/finanzas/propinas/config`" not in src
    assert (
        "/api/finanzas/propinas/config/${configData.id}"
        not in src
    )


def test_server_monta_router_edarsahub_v2():
    src = SERVER.read_text(encoding="utf-8")

    assert (
        "api_router.include_router("
        "get_propinas_tpv_edarsahub_router()"
        ")"
        in src
    )


def test_router_v2_expone_config_completa():
    src = ROUTES_V2.read_text(encoding="utf-8")

    for token in (
        '"/config"',
        '"/config/all"',
        '"/config/{config_id}"',
        "obtener_config_v2",
        "listar_configs_v2",
        "crear_config_v2",
        "actualizar_config_v2",
    ):
        assert token in src


def test_no_rehabilita_router_legacy():
    src = SERVER.read_text(encoding="utf-8")

    assert "get_propinas_tpv_edarsahub_router()" in src

    forbidden = (
        "get_propinas_tpv_router()",
        "get_propinas_tpv_sql_router()",
    )

    for token in forbidden:
        assert token not in src
