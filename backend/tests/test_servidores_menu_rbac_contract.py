from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

LAYOUT = (
    ROOT
    / "frontend"
    / "src"
    / "pages"
    / "Layout.js"
)

AUTH = (
    ROOT
    / "backend"
    / "modules"
    / "auth"
    / "routes.py"
)

MENU_SERVICE = (
    ROOT
    / "backend"
    / "modules"
    / "sistema"
    / "menu_service.py"
)


def test_servidores_no_tiene_item_legacy_por_rol():
    source = LAYOUT.read_text(
        encoding="utf-8"
    )

    assert (
        "{ name: 'Servidores', "
        "href: '/servidores'"
        not in source
    )


def test_enterprise_menu_sql_sigue_activo():
    source = LAYOUT.read_text(
        encoding="utf-8"
    )

    assert (
        "const USE_ENTERPRISE_MENU = true"
        in source
    )

    assert (
        "menuPermissions"
        in source
    )

    assert (
        "permissionsLoaded"
        in source
    )

    assert (
        "/auth/me/menu-permissions"
        in source
    )


def test_menu_permissions_mapea_servidores_a_ver():
    source = AUTH.read_text(
        encoding="utf-8"
    )

    start = source.index(
        'MENU_PERMISSION_MAP = {'
    )

    block = source[
        start:
        source.index(
            "\n}",
            start,
        ) + 2
    ]

    assert '"servidores": [' in block
    assert '"SERVIDORES_VER"' in block


def test_menu_sql_usa_codigo_modulo_como_candidato():
    source = MENU_SERVICE.read_text(
        encoding="utf-8"
    )

    assert (
        'self._norm(menu.get("RequierePermiso"))'
        in source
    )

    assert (
        'self._norm(menu.get("Codigo"))'
        in source
    )

    assert (
        "_norm_ruta_permiso("
        'menu.get("Ruta")'
        ")"
        in source
    )

    assert (
        "candidatos.intersection("
        "permisos_modulo"
        ")"
        in source
    )


def test_no_reemplazar_menu_sql_por_permiso_crud():
    source = MENU_SERVICE.read_text(
        encoding="utf-8"
    )

    # RequierePermiso pertenece a la resolución
    # modular del catálogo SQL. Los permisos CRUD
    # se resuelven en la capa funcional.
    assert "RequierePermiso" in source

def test_servidores_health_historico_sin_pings_automaticos():
    source = (ROOT / "frontend" / "src" / "pages" / "Servidores.js").read_text(encoding="utf-8")
    assert "conn.health?.has_evidence !== true" in source
    assert "historical: true" in source
    assert "Último: Conectado" in source
    assert "pingStatus[server.id]?.online" not in source
    assert "pingStatus[server.id]?.error" not in source
    assert "pingServerSilent(server.id);" not in source
    assert "await testApiConnection(apiConn);" in source
    assert "onPing={pingServer}" in source


def test_servidores_evidencia_historica_con_fecha_en_listas_y_tarjetas():
    source = (ROOT / "frontend" / "src" / "pages" / "Servidores.js").read_text(encoding="utf-8")
    assert "const historicalCheckLabel = (status)" in source
    assert "Última prueba registrada:" in source
    assert "fecha no disponible" in source
    assert "pingStatus[server.id]?.historical && (" in source
    assert "apiTestStatus[apiConn.id]?.historical && (" in source
    assert 'historicalCheckLabel(pingStatus) || "Online"' in source
    assert "historicalCheckLabel(pingStatus) || 'Offline'" in source
    assert "pingServerSilent(server.id);" not in source
