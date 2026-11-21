import pytest
from unittest.mock import MagicMock, patch

from modules.cava_socios.persona_link_service import CavaSociosPersonaLinkService
from modules.cava_socios.routes import (
    PersonaCreateLinkRequest,
    PersonaExistingLinkRequest,
)


@pytest.mark.unit
def test_persona_link_schemas_are_explicit():
    existing = PersonaExistingLinkRequest(persona_id=7, cliente_id=9)
    assert existing.persona_id == 7
    assert existing.cliente_id == 9

    created = PersonaCreateLinkRequest(nombre="Ana", cliente_id=9)
    assert created.nombre == "Ana"
    assert created.cliente_id == 9


@pytest.mark.unit
def test_vincular_persona_existing_rejects_implicit_replacement():
    service = CavaSociosPersonaLinkService()
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.fetchone.return_value = {"SocioID": "S1", "PersonaID": 22}

    with patch.object(service, "_get_connection", return_value=conn):
        with pytest.raises(ValueError, match="desvincule explícitamente"):
            service.vincular_persona_existente(
                socio_id="S1",
                empresa_id="E1",
                persona_id=23,
                cliente_id=None,
                usuario_sql_id=1,
                usuario_public_uuid=None,
            )

    conn.rollback.assert_called_once()


@pytest.mark.unit
def test_desvincular_persona_never_deletes_canonical_records():
    service = CavaSociosPersonaLinkService()
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.fetchone.return_value = {"SocioID": "S1", "PersonaID": 22}

    with patch.object(service, "_get_connection", return_value=conn):
        result = service.desvincular_persona(
            socio_id="S1",
            empresa_id="E1",
            usuario_public_uuid=None,
        )

    sql_calls = " ".join(str(call.args[0]) for call in cur.execute.call_args_list)
    assert "DELETE" not in sql_calls.upper()
    assert result["persona_id_anterior"] == 22
    assert result["canonical_records_deleted"] is False
    conn.commit.assert_called_once()


@pytest.mark.unit
def test_persona_link_routes_registered():
    from server import app

    paths = [route.path for route in app.routes if hasattr(route, "path")]
    assert "/api/cava-socios/personas-canonicas" in paths
    assert "/api/cava-socios/socios/{socio_id}/persona-link" in paths
    assert "/api/cava-socios/socios/{socio_id}/persona-link/crear-persona" in paths
