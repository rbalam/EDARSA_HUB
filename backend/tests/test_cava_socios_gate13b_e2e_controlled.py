import uuid

import pytest
from fastapi import HTTPException

from core.sql_first.connection_factory import get_edarsahub_pymssql_connection
from modules.cava_socios import routes
from modules.cava_socios.report_service import get_cava_report_service
from modules.cava_socios.service import get_cava_socios_service


JOB_ID = "CAVAS-GATE13B-E2E-CONTROLLED-UAT-R2B-RERUN-R2-20260919"
SOCIO_ID = "62CA4D8A-F4B7-4C66-BE8C-2C13C7445A58"
UNIDAD_ID = "19E076FB-C6DE-4EA5-84AB-1CAA9E86082C"
SECOND_AUTHORIZED_UNIT = "23CA0B76-6580-4874-BA9B-672B122CA197"
UNAUTHORIZED_UNIT = "11111111-2222-4333-8444-555555555555"
PUBLIC_UUID = "A72B325B-662F-4777-83ED-4DDA6E8398A8"
EMAIL = "noxte@alpyc.com"


def _conn():
    return get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)


def _snapshot():
    conn = _conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(
            """
            SELECT CONVERT(varchar(36),SocioID) AS SocioID,
                   CONVERT(varchar(36),EmpresaID) AS UnidadNegocioID,
                   NumeroSocio, PersonaID, ClienteCRMID,
                   FechaModificacion,
                   CONVERT(varchar(36),UsuarioModificacionID) AS UsuarioModificacionID
            FROM dbo.CavaSocios_Socios
            WHERE SocioID=%s AND EmpresaID=%s
            """,
            (SOCIO_ID, UNIDAD_ID),
        )
        socio = cur.fetchone()
        assert socio is not None, "STAGE=PRECHECK;SOCIO_CANARY_NOT_FOUND"

        counts = {}
        for key, sql in {
            "botellas": "SELECT COUNT_BIG(*) n FROM dbo.CavaSocios_Botellas WHERE SocioID=%s AND EmpresaID=%s",
            "movimientos": "SELECT COUNT_BIG(*) n FROM dbo.CavaSocios_Movimientos WHERE SocioID=%s AND EmpresaID=%s",
            "cargos": "SELECT COUNT_BIG(*) n FROM dbo.CavaSocios_Cargos WHERE SocioID=%s AND EmpresaID=%s",
        }.items():
            cur.execute(sql, (SOCIO_ID, UNIDAD_ID))
            counts[key] = int(cur.fetchone()["n"])
        return {"socio": dict(socio), **counts}
    finally:
        conn.close()


def _cleanup(botella_id, persona_rfc, before):
    conn = _conn()
    try:
        cur = conn.cursor(as_dict=True)
        if botella_id:
            cur.execute("DELETE FROM dbo.CavaSocios_Cargos WHERE BotellaID=%s AND EmpresaID=%s", (botella_id, UNIDAD_ID))
            cur.execute("DELETE FROM dbo.CavaSocios_Movimientos WHERE BotellaID=%s AND EmpresaID=%s", (botella_id, UNIDAD_ID))
            cur.execute("DELETE FROM dbo.CavaSocios_Botellas WHERE BotellaID=%s AND EmpresaID=%s", (botella_id, UNIDAD_ID))

        cur.execute("SELECT PersonaID FROM dbo.Gobierno_Persona WHERE RFC=%s", (persona_rfc,))
        row = cur.fetchone()
        persona_id = int(row["PersonaID"]) if row else None
        if persona_id is not None:
            cur.execute(
                "UPDATE dbo.CavaSocios_Socios SET PersonaID=NULL WHERE SocioID=%s AND EmpresaID=%s AND PersonaID=%s",
                (SOCIO_ID, UNIDAD_ID, persona_id),
            )
            cur.execute("DELETE FROM dbo.Gobierno_PersonaVinculo WHERE PersonaID=%s", (persona_id,))
            cur.execute("DELETE FROM dbo.Gobierno_Persona WHERE PersonaID=%s", (persona_id,))

        cur.execute(
            """
            UPDATE dbo.CavaSocios_Socios
               SET PersonaID=%s, ClienteCRMID=%s,
                   FechaModificacion=%s, UsuarioModificacionID=%s
             WHERE SocioID=%s AND EmpresaID=%s
            """,
            (
                before["socio"]["PersonaID"],
                before["socio"]["ClienteCRMID"],
                before["socio"]["FechaModificacion"],
                before["socio"]["UsuarioModificacionID"],
                SOCIO_ID,
                UNIDAD_ID,
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _assert_no_residue(marker, persona_rfc, before):
    after = _snapshot()
    assert after["botellas"] == before["botellas"], "STAGE=CLEANUP;BOTTLE_COUNT_MISMATCH"
    assert after["movimientos"] == before["movimientos"], "STAGE=CLEANUP;MOVEMENT_COUNT_MISMATCH"
    assert after["cargos"] == before["cargos"], "STAGE=CLEANUP;CHARGE_COUNT_MISMATCH"
    assert after["socio"]["PersonaID"] == before["socio"]["PersonaID"], "STAGE=CLEANUP;PERSONA_NOT_RESTORED"
    assert after["socio"]["ClienteCRMID"] == before["socio"]["ClienteCRMID"], "STAGE=CLEANUP;CLIENT_NOT_RESTORED"

    conn = _conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("SELECT COUNT_BIG(*) n FROM dbo.Gobierno_Persona WHERE RFC=%s", (persona_rfc,))
        assert int(cur.fetchone()["n"]) == 0, "STAGE=CLEANUP;PERSONA_RESIDUE"
        cur.execute(
            "SELECT COUNT_BIG(*) n FROM dbo.CavaSocios_Botellas WHERE ProductoNombre=%s AND EmpresaID=%s",
            (marker, UNIDAD_ID),
        )
        assert int(cur.fetchone()["n"]) == 0, "STAGE=CLEANUP;BOTTLE_RESIDUE"
    finally:
        conn.close()


def _contains_value(value, needle):
    if isinstance(value, dict):
        return any(_contains_value(v, needle) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_value(v, needle) for v in value)
    return str(value).lower() == str(needle).lower()


def _assert_charge_trace(movimiento_id, cargo_id, expected_amount):
    conn = _conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(
            """
            SELECT m.GeneroCargo,m.MontoCargo,
                   CONVERT(varchar(36),c.CargoID) AS CargoID,
                   c.Monto AS CargoMonto,c.Impuesto,c.Total
            FROM dbo.CavaSocios_Movimientos m
            LEFT JOIN dbo.CavaSocios_Cargos c ON c.MovimientoID=m.MovimientoID
            WHERE m.MovimientoID=%s AND m.EmpresaID=%s
            """,
            (movimiento_id, UNIDAD_ID),
        )
        row = cur.fetchone()
        assert row is not None, "STAGE=CHARGE_TRACE;MOVEMENT_NOT_FOUND"
        assert bool(row["GeneroCargo"]) is True, "STAGE=CHARGE_TRACE;GENERO_CARGO_FALSE"
        assert round(float(row["MontoCargo"] or 0), 2) == round(expected_amount, 2), "STAGE=CHARGE_TRACE;MOVEMENT_AMOUNT_MISMATCH"
        assert str(row["CargoID"]).upper() == str(cargo_id).upper(), "STAGE=CHARGE_TRACE;CARGO_ID_MISMATCH"
        assert round(float(row["CargoMonto"] or 0), 2) == round(expected_amount, 2), "STAGE=CHARGE_TRACE;CARGO_AMOUNT_MISMATCH"
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_gate13b_e2e_controlled_r2_instrumented():
    stage = "PRECHECK"
    before = _snapshot()
    assert before["socio"]["PersonaID"] is None, "STAGE=PRECHECK;PERSONA_BASELINE_NOT_NULL"
    assert before["socio"]["ClienteCRMID"] is None, "STAGE=PRECHECK;CLIENT_BASELINE_NOT_NULL"
    assert before["socio"]["NumeroSocio"] == "SOC-00001", "STAGE=PRECHECK;WRONG_SOCIO"

    current_user = {"id": PUBLIC_UUID, "public_uuid": PUBLIC_UUID, "email": EMAIL}
    suffix = uuid.uuid4().hex.upper()
    marker = f"UAT13B-{suffix[:12]}"
    rfc = ("UAT13B" + suffix[:7])[:13]
    curp = ("UAT13B" + suffix[:12])[:18]
    botella_id = None

    try:
        try:
            stage = "DASHBOARD"
            dashboard_before = await routes.get_dashboard(unidad_negocio_pk=UNIDAD_ID, current_user=current_user)
            assert "socios" in dashboard_before, "STAGE=DASHBOARD;SOCIOS_KEY_MISSING"
            assert "botellas" in dashboard_before, "STAGE=DASHBOARD;BOTELLAS_KEY_MISSING"
            assert "financiero" in dashboard_before, "STAGE=DASHBOARD;FINANCIERO_KEY_MISSING"

            stage = "SOCIOS"
            socios = await routes.listar_socios(
                unidad_negocio_pk=UNIDAD_ID, estatus="ACTIVO", skip=0, limit=100, current_user=current_user
            )
            assert _contains_value(socios, SOCIO_ID), "STAGE=SOCIOS;CANARY_NOT_LISTED"

            socio = await routes.obtener_socio(
                socio_id=SOCIO_ID, unidad_negocio_pk=UNIDAD_ID, current_user=current_user
            )
            assert socio["numero_socio"] == "SOC-00001", "STAGE=SOCIOS;WRONG_NUMERO"

            stage = "MULTIUNIT"
            other_unit = await routes.listar_socios(
                unidad_negocio_pk=SECOND_AUTHORIZED_UNIT, estatus=None, skip=0, limit=100, current_user=current_user
            )
            assert not _contains_value(other_unit, SOCIO_ID), "STAGE=MULTIUNIT;CANARY_LEAKED_TO_OTHER_UNIT"

            stage = "ERROR_403"
            with pytest.raises(HTTPException) as forbidden:
                await routes.obtener_socio(
                    socio_id=SOCIO_ID, unidad_negocio_pk=UNAUTHORIZED_UNIT, current_user=current_user
                )
            assert forbidden.value.status_code == 403, "STAGE=ERROR_403;WRONG_STATUS"

            stage = "ERROR_404"
            with pytest.raises(HTTPException) as missing:
                await routes.obtener_socio(
                    socio_id=str(uuid.uuid4()), unidad_negocio_pk=UNIDAD_ID, current_user=current_user
                )
            assert missing.value.status_code == 404, "STAGE=ERROR_404;WRONG_STATUS"

            stage = "PERSONA_CREATE_LINK"
            created_persona = await routes.crear_persona_y_vincular(
                socio_id=SOCIO_ID,
                data=routes.PersonaCreateLinkRequest(
                    nombre="UAT Gate13B R2", apellido_paterno="EDARSAHUB",
                    rfc=rfc, curp=curp, nacionalidad="MX", cliente_id=None
                ),
                unidad_negocio_pk=UNIDAD_ID, current_user=current_user,
            )
            assert created_persona["created_persona"] is True, "STAGE=PERSONA_CREATE_LINK;NOT_CREATED"
            persona_id = int(created_persona["persona_id"])

            stage = "PERSONA_READ"
            linked = await routes.obtener_persona_link(
                socio_id=SOCIO_ID, unidad_negocio_pk=UNIDAD_ID, current_user=current_user
            )
            assert int(linked["persona_id"]) == persona_id, "STAGE=PERSONA_READ;LINK_MISMATCH"

            stage = "ERROR_409"
            with pytest.raises(HTTPException) as conflict:
                await routes.crear_persona_y_vincular(
                    socio_id=SOCIO_ID,
                    data=routes.PersonaCreateLinkRequest(
                        nombre="UAT Gate13B Duplicate", apellido_paterno="EDARSAHUB",
                        rfc=("U13BD" + suffix[:8])[:13], curp=("U13BD" + suffix[:13])[:18],
                        nacionalidad="MX", cliente_id=None
                    ),
                    unidad_negocio_pk=UNIDAD_ID, current_user=current_user,
                )
            assert conflict.value.status_code == 409, "STAGE=ERROR_409;WRONG_STATUS"

            stage = "BOTTLE_CREATE"
            bottle = await routes.registrar_botella(
                socio_id=SOCIO_ID,
                data=routes.BotellaCreate(
                    producto_nombre=marker, producto_codigo=marker, marca="EDARSAHUB-UAT",
                    tipo_bebida="VINO_TINTO", añada="2026", capacidad=1.0,
                    nivel_actual=100.0, ubicacion="UAT13B", valor_declarado=999.99,
                    observaciones=JOB_ID
                ),
                unidad_negocio_pk=UNIDAD_ID, current_user=current_user,
            )
            botella_id = str(bottle["botella_id"])
            assert botella_id, "STAGE=BOTTLE_CREATE;NO_ID"

            stage = "INVENTORY"
            inventario = await routes.obtener_inventario(
                ubicacion=None, tipo_bebida=None, estatus=None, socio_id=SOCIO_ID,
                skip=0, limit=100, unidad_negocio_pk=UNIDAD_ID, current_user=current_user
            )
            assert _contains_value(inventario, botella_id), "STAGE=INVENTORY;BOTTLE_NOT_FOUND"
            assert _contains_value(inventario, marker), "STAGE=INVENTORY;MARKER_NOT_FOUND"

            stage = "PHYSICAL_INVENTORY"
            hoja = await routes.obtener_hoja_inventario_fisico(
                ubicacion=None, socio_id=SOCIO_ID, unidad_negocio_pk=UNIDAD_ID, current_user=current_user
            )
            assert _contains_value(hoja, botella_id), "STAGE=PHYSICAL_INVENTORY;BOTTLE_NOT_FOUND"

            stage = "CONSUMPTION"
            consumo = await routes.registrar_consumo(
                botella_id=botella_id,
                data=routes.ConsumoCreate(
                    porcentaje_consumido=25.0, motivo=JOB_ID, generar_cargo_descorche=True,
                    monto_descorche=123.45, observaciones=marker
                ),
                unidad_negocio_pk=UNIDAD_ID, current_user=current_user,
            )
            assert float(consumo["nivel_anterior"]) == 100.0, "STAGE=CONSUMPTION;WRONG_PREVIOUS_LEVEL"
            assert float(consumo["nivel_nuevo"]) == 75.0, "STAGE=CONSUMPTION;WRONG_NEW_LEVEL"
            assert consumo["tipo_movimiento"] == "CONSUMO_PARCIAL", "STAGE=CONSUMPTION;WRONG_TYPE"
            assert consumo["cargo_id"] is not None, "STAGE=CONSUMPTION;NO_CHARGE"

            stage = "CHARGE_TRACE"
            _assert_charge_trace(consumo["movimiento_id"], consumo["cargo_id"], 123.45)

            stage = "KARDEX"
            kardex = await routes.obtener_kardex(
                socio_id=SOCIO_ID, botella_id=botella_id, fecha_inicio=None, fecha_fin=None,
                tipo_movimiento=None, skip=0, limit=100,
                unidad_negocio_pk=UNIDAD_ID, current_user=current_user
            )
            assert _contains_value(kardex, botella_id), "STAGE=KARDEX;BOTTLE_NOT_FOUND"
            assert _contains_value(kardex, "CONSUMO_PARCIAL"), "STAGE=KARDEX;CONSUMPTION_NOT_FOUND"

            stage = "CONSUMPTION_HISTORY"
            consumos = await routes.obtener_consumos(
                socio_id=SOCIO_ID, skip=0, limit=100,
                unidad_negocio_pk=UNIDAD_ID, current_user=current_user
            )
            assert _contains_value(consumos, consumo["movimiento_id"]), "STAGE=CONSUMPTION_HISTORY;MOVEMENT_NOT_FOUND"
            assert _contains_value(consumos, marker), "STAGE=CONSUMPTION_HISTORY;MARKER_NOT_FOUND"

            stage = "DASHBOARD_AFTER"
            dashboard_after = await routes.get_dashboard(unidad_negocio_pk=UNIDAD_ID, current_user=current_user)
            assert int(dashboard_after["botellas"]["total"]) >= int(dashboard_before["botellas"]["total"]) + 1, "STAGE=DASHBOARD_AFTER;BOTTLE_KPI_NOT_INCREMENTED"
            assert int(dashboard_after["financiero"]["cargos_pendientes"]) >= int(dashboard_before["financiero"]["cargos_pendientes"]) + 1, "STAGE=DASHBOARD_AFTER;CHARGE_KPI_NOT_INCREMENTED"

            stage = "REPORTS"
            service = get_cava_socios_service()
            report_service = get_cava_report_service()
            socio_report = service.obtener_socio(SOCIO_ID, UNIDAD_ID)
            movimientos_report = service.obtener_movimientos_socio(SOCIO_ID, UNIDAD_ID)
            cargos_report = service.obtener_cargos_socio(SOCIO_ID, UNIDAD_ID)
            pdfs = (
                report_service.generar_ficha_socio(socio_report),
                report_service.generar_historial_consumos(socio_report, movimientos_report),
                report_service.generar_estado_cuenta(socio_report, cargos_report),
            )
            for pdf in pdfs:
                assert isinstance(pdf, (bytes, bytearray)), "STAGE=REPORTS;NOT_BYTES"
                assert bytes(pdf).startswith(b"%PDF"), "STAGE=REPORTS;INVALID_PDF"
                assert len(pdf) > 500, "STAGE=REPORTS;PDF_TOO_SMALL"

            stage = "PERSONA_UNLINK"
            unlinked = await routes.desvincular_persona(
                socio_id=SOCIO_ID, unidad_negocio_pk=UNIDAD_ID, current_user=current_user
            )
            assert int(unlinked["persona_id_anterior"]) == persona_id, "STAGE=PERSONA_UNLINK;PREVIOUS_ID_MISMATCH"
            assert unlinked["canonical_records_deleted"] is False, "STAGE=PERSONA_UNLINK;CANONICAL_DELETE_OCCURRED"

            stage = "PERSONA_FINAL"
            final_link = await routes.obtener_persona_link(
                socio_id=SOCIO_ID, unidad_negocio_pk=UNIDAD_ID, current_user=current_user
            )
            assert final_link["persona_id"] is None, "STAGE=PERSONA_FINAL;STILL_LINKED"

        except Exception as exc:
            if isinstance(exc, AssertionError) and str(exc).startswith("STAGE="):
                raise
            raise AssertionError(f"STAGE={stage};EXCEPTION={type(exc).__name__}:{exc}") from exc
    finally:
        _cleanup(botella_id, rfc, before)

    _assert_no_residue(marker, rfc, before)
