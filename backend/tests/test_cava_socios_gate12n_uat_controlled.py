import uuid

import pytest
from fastapi import HTTPException

from core.sql_first.connection_factory import get_edarsahub_pymssql_connection
from modules.cava_socios import routes


JOB_ID = "CAVAS-GATE12N-UAT-CONTROLLED-EXECUTION-R3-20260918"
SOCIO_ID = "62CA4D8A-F4B7-4C66-BE8C-2C13C7445A58"
UNIDAD_ID = "19E076FB-C6DE-4EA5-84AB-1CAA9E86082C"
PUBLIC_UUID = "A72B325B-662F-4777-83ED-4DDA6E8398A8"
EMAIL = "noxte@alpyc.com"


def _snapshot():
    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(
            """
            SELECT
              CONVERT(varchar(36),SocioID) AS SocioID,
              CONVERT(varchar(36),EmpresaID) AS UnidadNegocioID,
              NumeroSocio,
              NombreCompleto,
              Estatus,
              Activo,
              PersonaID,
              ClienteCRMID
            FROM dbo.CavaSocios_Socios
            WHERE SocioID=%s AND EmpresaID=%s
            """,
            (SOCIO_ID, UNIDAD_ID),
        )
        socio = cur.fetchone()
        assert socio is not None, "UAT_PRECHECK_SOCIO_NOT_FOUND"

        cur.execute("SELECT COUNT_BIG(*) AS n FROM dbo.Gobierno_Persona")
        personas = int(cur.fetchone()["n"])
        cur.execute("SELECT COUNT_BIG(*) AS n FROM dbo.Gobierno_PersonaVinculo")
        vinculos = int(cur.fetchone()["n"])
        cur.execute("SELECT COUNT_BIG(*) AS n FROM dbo.CavaSocios_Socios WHERE PersonaID IS NOT NULL")
        linked = int(cur.fetchone()["n"])

        return {
            "socio": dict(socio),
            "personas": personas,
            "vinculos": vinculos,
            "linked": linked,
        }
    finally:
        conn.close()


def _cleanup_uat(rfc: str):
    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(
            "SELECT PersonaID FROM dbo.Gobierno_Persona WHERE RFC=%s",
            (rfc,),
        )
        row = cur.fetchone()
        persona_id = int(row["PersonaID"]) if row else None

        if persona_id is not None:
            cur.execute(
                """
                UPDATE dbo.CavaSocios_Socios
                   SET PersonaID=NULL
                 WHERE SocioID=%s
                   AND EmpresaID=%s
                   AND PersonaID=%s
                """,
                (SOCIO_ID, UNIDAD_ID, persona_id),
            )
            cur.execute(
                "DELETE FROM dbo.Gobierno_PersonaVinculo WHERE PersonaID=%s",
                (persona_id,),
            )
            cur.execute(
                "DELETE FROM dbo.Gobierno_Persona WHERE PersonaID=%s",
                (persona_id,),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_gate12n_controlled_uat_exact_candidate_and_cleanup():
    before = _snapshot()
    socio_before = before["socio"]

    assert socio_before["SocioID"].upper() == SOCIO_ID
    assert socio_before["UnidadNegocioID"].upper() == UNIDAD_ID
    assert socio_before["NumeroSocio"] == "SOC-00001"
    assert socio_before["Estatus"] == "ACTIVO"
    assert bool(socio_before["Activo"]) is True
    assert socio_before["PersonaID"] is None

    current_user = {
        "id": PUBLIC_UUID,
        "public_uuid": PUBLIC_UUID,
        "email": EMAIL,
    }

    suffix = uuid.uuid4().hex.upper()
    rfc = ("UAT12N" + suffix[:7])[:13]
    curp = ("UAT12N" + suffix[:12])[:18]

    created_persona_id = None
    try:
        initial = await routes.obtener_persona_link(
            socio_id=SOCIO_ID,
            unidad_negocio_pk=UNIDAD_ID,
            current_user=current_user,
        )
        assert initial["persona_id"] is None

        payload = routes.PersonaCreateLinkRequest(
            nombre="UAT Gate12N",
            apellido_paterno="EDARSAHUB",
            rfc=rfc,
            curp=curp,
            nacionalidad="MX",
            cliente_id=None,
        )

        created = await routes.crear_persona_y_vincular(
            socio_id=SOCIO_ID,
            data=payload,
            unidad_negocio_pk=UNIDAD_ID,
            current_user=current_user,
        )
        assert created["created_persona"] is True
        assert created["cliente_id"] is None
        created_persona_id = int(created["persona_id"])

        linked = await routes.obtener_persona_link(
            socio_id=SOCIO_ID,
            unidad_negocio_pk=UNIDAD_ID,
            current_user=current_user,
        )
        assert int(linked["persona_id"]) == created_persona_id

        unlinked = await routes.desvincular_persona(
            socio_id=SOCIO_ID,
            unidad_negocio_pk=UNIDAD_ID,
            current_user=current_user,
        )
        assert int(unlinked["persona_id_anterior"]) == created_persona_id
        assert unlinked["canonical_records_deleted"] is False

        final_link = await routes.obtener_persona_link(
            socio_id=SOCIO_ID,
            unidad_negocio_pk=UNIDAD_ID,
            current_user=current_user,
        )
        assert final_link["persona_id"] is None

    finally:
        _cleanup_uat(rfc)

    after = _snapshot()
    socio_after = after["socio"]

    assert after["personas"] == before["personas"]
    assert after["vinculos"] == before["vinculos"]
    assert after["linked"] == before["linked"]
    assert socio_after["PersonaID"] is None
    assert socio_after["ClienteCRMID"] == socio_before["ClienteCRMID"]
    assert socio_after["SocioID"] == socio_before["SocioID"]
    assert socio_after["UnidadNegocioID"] == socio_before["UnidadNegocioID"]
