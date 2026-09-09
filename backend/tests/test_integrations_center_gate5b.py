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
