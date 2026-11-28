from modules.integrations_center.routes import router
from modules.integrations_center.service import _attach_health, _normalize_connection
from modules.api_connections import api_universal_test_router


def test_gate5b_router_is_read_only():
    paths = {route.path for route in router.routes}
    assert "/integrations-center/overview" in paths
    assert "/integrations-center/connections" in paths
    assert "/integrations-center/connections/{connection_id}" in paths
    assert "/integrations-center/catalogs" in paths
    assert "/integrations-center/communications" in paths
    gate5b_paths = {
        "/integrations-center/overview",
        "/integrations-center/connections",
        "/integrations-center/connections/{connection_id}",
        "/integrations-center/catalogs",
        "/integrations-center/communications",
    }
    for route in router.routes:
        if route.path in gate5b_paths:
            assert set(route.methods or ()) <= {"GET"}


def test_gate5b_facade_is_mounted_on_existing_root_api_router():
    paths = {route.path for route in api_universal_test_router.routes}
    assert "/integrations-center/overview" in paths
    assert "/integrations-center/connections" in paths
    assert "/integrations-center/catalogs" in paths
    assert "/integrations-center/communications" in paths


def test_gate5b_never_projects_secret_values():
    raw = {
        "id": "11111111-1111-1111-1111-111111111111",
        "nombre": "Prueba",
        "tipo_conexion": "DATA_SOURCE",
        "system_type": "MPRO",
        "activo": True,
        "password": "NO_DEBE_SALIR",
        "password_encrypted": "enc:v1:NO_DEBE_SALIR",
        "api_key": "NO_DEBE_SALIR",
        "api_key_encrypted": "enc:v1:NO_DEBE_SALIR",
        "password_configured": True,
        "api_key_configured": True,
    }
    result = _normalize_connection(raw, "server_registry")
    serialized = repr(result)
    assert "NO_DEBE_SALIR" not in serialized
    assert "password" not in result
    assert "api_key" not in result
    assert result["secret_metadata"] == {
        "password_configured": True,
        "api_key_configured": True,
    }


def test_active_flag_does_not_invent_connection_health():
    result = _normalize_connection(
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "nombre": "Activo sin evidencia",
            "tipo_conexion": "DATA_SOURCE",
            "activo": True,
        },
        "server_registry",
    )
    assert result["active"] is True
    assert result["health"]["status"] == "UNKNOWN"
    assert result["health"]["has_evidence"] is False


def test_health_is_attached_only_from_canonical_evidence():
    result = _normalize_connection(
        {
            "id": "33333333-3333-3333-3333-333333333333",
            "nombre": "Con evidencia",
            "tipo_conexion": "API_LOCAL",
            "activo": False,
        },
        "api_connections",
    )
    _attach_health(
        result,
        {
            "EstadoConexion": "CONNECTED",
            "UltimaPruebaUTC": "2026-09-09T18:00:00Z",
            "LatenciaMs": 42,
        },
    )
    assert result["active"] is False
    assert result["health"]["status"] == "CONNECTED"
    assert result["health"]["has_evidence"] is True
    assert result["health"]["source"] == "dbo.Servidores_ConexionEstado"



def test_canonical_scope_contract_is_not_hardcoded():
    result = _normalize_connection(
        {
            "id": "44444444-4444-4444-4444-444444444444",
            "nombre": "Chapur Enterprise",
            "tipo_conexion": "DATA_SOURCE",
            "system_type": "SOFTRESTAURANT",
            "activo": True,
        },
        "server_registry",
    )
    assert result["scope"]["unidad_negocio_ids"] == []
    assert result["scope"]["unit_mapping_status"] == "NOT_EXPLICIT_IN_CONNECTION_CONTRACT"
    assert result["scope"]["source"] == "dbo.Servidores_Conexiones"



def test_connection_homologation_is_fail_closed_by_default():
    result = _normalize_connection(
        {
            "id": "55555555-5555-5555-5555-555555555555",
            "nombre": "SoftRestaurant Enterprise",
            "tipo_conexion": "DATA_SOURCE",
            "system_type": "SOFTRESTAURANT",
            "activo": True,
        },
        "server_registry",
    )

    assert result["homologation"]["status"] == "NOT_ASSESSED"
    assert result["homologation"]["profile_id"] is None
    assert result["homologation"]["certification_source"] is None


def test_gate5b_projects_persisted_inventory_filters_from_server_registry():
    # La fachada no debe esconder los conceptos guardados ni inventar vacios
    # que posteriormente se interpretan como una seleccion del usuario.
    source = {
        "id": "66666666-6666-6666-6666-666666666666",
        "nombre": "ManagementPro",
        "tipo_conexion": "DATA_SOURCE",
        "system_type": "MPRO",
        "tipos_movimiento": ["050", "106", "108", "109", "112", "506", "508", "509", "510", "512"],
        "categorias": ["C01"],
        "departamentos": ["D01"],
        "activo": True,
        "password": "NO_DEBE_SALIR",
    }
    projected = _normalize_connection(source, "server_registry")
    for key in ("tipos_movimiento", "categorias", "departamentos"):
        assert projected[key] == source[key]
    assert projected["tipos_movimiento"][1] == "106"
    assert "NO_DEBE_SALIR" not in repr(projected)


def test_gate5b_unconfigured_api_connection_keeps_empty_catalog_defaults():
    source = {"id": "77777777-7777-7777-7777-777777777777", "tipo_conexion": "API_LOCAL"}
    projected = _normalize_connection(source, "api_connections")
    assert projected["tipos_movimiento"] == []
    assert projected["categorias"] == []
    assert projected["departamentos"] == []
