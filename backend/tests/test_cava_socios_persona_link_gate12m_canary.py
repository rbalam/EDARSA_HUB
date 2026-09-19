import os
import uuid

import pytest

from core.sql_first.connection_factory import get_edarsahub_pymssql_connection
from modules.cava_socios import routes


CANARY_JOB_ID = "CAVAS-GATE12M-PERSONA-LINK-E2E-CANARY-R1-20260918"


def _enabled_here() -> bool:
    return CANARY_JOB_ID in os.getcwd()


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _enabled_here(),
        reason="Gate12M canary only runs inside its dedicated Universal Worker worktree",
    ),
]


def _fetch_canary_context():
    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(
            """
            SELECT TOP (1)
                CONVERT(varchar(36), SocioID) AS SocioID,
                CONVERT(varchar(36), EmpresaID) AS EmpresaID,
                NumeroSocio,
                PersonaID
            FROM dbo.CavaSocios_Socios
            WHERE Activo = 1
              AND Estatus = 'ACTIVO'
              AND PersonaID IS NULL
            ORDER BY FechaCreacion, SocioID
            """
        )
        socio = cur.fetchone()
        if not socio:
            raise AssertionError("GATE12M_NO_ELIGIBLE_SOCIO")

        cur.execute(
            """
            SELECT TOP (1)
                UsuarioID,
                CONVERT(varchar(36), PublicUUID) AS PublicUUID
            FROM dbo.Usuario_Catalogo
            WHERE Activo = 1
              AND PublicUUID IS NOT NULL
            ORDER BY UsuarioID
            """
        )
        actor = cur.fetchone()
        if not actor:
            raise AssertionError("GATE12M_NO_ELIGIBLE_SQL_ACTOR")

        cur.execute("SELECT COUNT_BIG(*) AS n FROM dbo.Gobierno_Persona")
        personas_before = int(cur.fetchone()["n"])
        cur.execute("SELECT COUNT_BIG(*) AS n FROM dbo.Gobierno_PersonaVinculo")
        vinculos_before = int(cur.fetchone()["n"])
        cur.execute(
            """
            SELECT COUNT_BIG(*) AS n
            FROM dbo.CavaSocios_Socios
            WHERE PersonaID IS NOT NULL
            """
        )
        linked_before = int(cur.fetchone()["n"])

        return {
            "socio": dict(socio),
            "actor": dict(actor),
            "personas_before": personas_before,
            "vinculos_before": vinculos_before,
            "linked_before": linked_before,
        }
    finally:
        conn.close()


def _cleanup_canary(*, socio_id: str, empresa_id: str, rfc: str):
    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    try:
        cur = conn.cursor(as_dict=True)

        cur.execute(
            """
            SELECT PersonaID
            FROM dbo.Gobierno_Persona
            WHERE RFC = %s
            """,
            (rfc,),
        )
        row = cur.fetchone()
        persona_id = int(row["PersonaID"]) if row else None

        if persona_id is not None:
            cur.execute(
                """
                UPDATE dbo.CavaSocios_Socios
                SET PersonaID = NULL
                WHERE SocioID = %s
                  AND EmpresaID = %s
                  AND PersonaID = %s
                """,
                (socio_id, empresa_id, persona_id),
            )
            cur.execute(
                "DELETE FROM dbo.Gobierno_PersonaVinculo WHERE PersonaID = %s",
                (persona_id,),
            )
            cur.execute(
                "DELETE FROM dbo.Gobierno_Persona WHERE PersonaID = %s",
                (persona_id,),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_gate12m_single_controlled_persona_link_canary(monkeypatch):
    ctx = _fetch_canary_context()
    socio = ctx["socio"]
    actor = ctx["actor"]

    unit_code = "GATE12M-CANARY"
    rfc = ("CAN" + uuid.uuid4().hex[:10]).upper()
    curp = ("CANARY" + uuid.uuid4().hex[:12]).upper()

    fake_user = {
        "id": str(actor["PublicUUID"]),
        "PublicUUID": str(actor["PublicUUID"]),
        "UsuarioID": int(actor["UsuarioID"]),
        "email": "gate12m-canary@edarsahub.local",
    }

    def fake_get_user_context(_user):
        return {
            "unidad_activa": unit_code,
            "unidades_permitidas": [
                {
                    "UnidadNegocioID": unit_code,
                    "EmpresaID": socio["EmpresaID"],
                }
            ],
        }

    def fake_enrich(user):
        enriched = dict(user)
        enriched["UsuarioID"] = int(actor["UsuarioID"])
        enriched["_sql_usuario_id"] = int(actor["UsuarioID"])
        enriched["PublicUUID"] = str(actor["PublicUUID"])
        return enriched

    monkeypatch.setattr(routes.context_service, "get_user_context", fake_get_user_context)
    monkeypatch.setattr(routes, "enrich_current_user_with_sql_id", fake_enrich)

    created_persona_id = None
    try:
        before = await routes.obtener_persona_link(
            socio_id=socio["SocioID"],
            unidad_negocio_pk=unit_code,
            current_user=fake_user,
        )
        assert before["persona_id"] is None

        create_payload = routes.PersonaCreateLinkRequest(
            nombre="Canary Gate12M",
            apellido_paterno="EDARSAHUB",
            rfc=rfc,
            curp=curp,
            nacionalidad="MX",
            cliente_id=None,
        )
        created = await routes.crear_persona_y_vincular(
            socio_id=socio["SocioID"],
            data=create_payload,
            unidad_negocio_pk=unit_code,
            current_user=fake_user,
        )

        assert created["created_persona"] is True
        assert created["cliente_id"] is None
        created_persona_id = int(created["persona_id"])

        linked = await routes.obtener_persona_link(
            socio_id=socio["SocioID"],
            unidad_negocio_pk=unit_code,
            current_user=fake_user,
        )
        assert int(linked["persona_id"]) == created_persona_id
        assert int(linked["persona"]["persona_id"]) == created_persona_id
        assert linked["vinculos"] == []

        unlinked = await routes.desvincular_persona(
            socio_id=socio["SocioID"],
            unidad_negocio_pk=unit_code,
            current_user=fake_user,
        )
        assert int(unlinked["persona_id_anterior"]) == created_persona_id
        assert unlinked["canonical_records_deleted"] is False

        after_unlink = await routes.obtener_persona_link(
            socio_id=socio["SocioID"],
            unidad_negocio_pk=unit_code,
            current_user=fake_user,
        )
        assert after_unlink["persona_id"] is None

    finally:
        _cleanup_canary(
            socio_id=socio["SocioID"],
            empresa_id=socio["EmpresaID"],
            rfc=rfc,
        )

    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    try:
        cur = conn.cursor(as_dict=True)

        cur.execute("SELECT COUNT_BIG(*) AS n FROM dbo.Gobierno_Persona")
        assert int(cur.fetchone()["n"]) == ctx["personas_before"]

        cur.execute("SELECT COUNT_BIG(*) AS n FROM dbo.Gobierno_PersonaVinculo")
        assert int(cur.fetchone()["n"]) == ctx["vinculos_before"]

        cur.execute(
            """
            SELECT COUNT_BIG(*) AS n
            FROM dbo.CavaSocios_Socios
            WHERE PersonaID IS NOT NULL
            """
        )
        assert int(cur.fetchone()["n"]) == ctx["linked_before"]

        cur.execute(
            """
            SELECT PersonaID
            FROM dbo.CavaSocios_Socios
            WHERE SocioID = %s AND EmpresaID = %s
            """,
            (socio["SocioID"], socio["EmpresaID"]),
        )
        final_socio = cur.fetchone()
        assert final_socio is not None
        assert final_socio["PersonaID"] is None

        cur.execute(
            "SELECT COUNT_BIG(*) AS n FROM dbo.Gobierno_Persona WHERE RFC = %s",
            (rfc,),
        )
        assert int(cur.fetchone()["n"]) == 0
    finally:
        conn.close()
