"""
Tests AnonymizerService — capa central de confidencialidad.
Ejecutar: cd /app/backend && python -m pytest tests/test_anonymizer_service.py -q
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.confidencialidad import AnonymizerService, NivelConfidencialidad  # noqa: E402

SRV_A = "aaaaaaaa-0000-0000-0000-000000000001"  # propia del usuario
SRV_B = "bbbbbbbb-0000-0000-0000-000000000002"  # hermana
SRV_C = "cccccccc-0000-0000-0000-000000000003"  # hermana

ROWS = [
    {"server_id": SRV_A, "unidad_negocio_nombre": "LA ESTELAR", "sucursal_id": "0021", "ventas": 100},
    {"server_id": SRV_B, "unidad_negocio_nombre": "130 MERIDA", "sucursal_id": "0023", "ventas": 200},
    {"server_id": SRV_C, "unidad_negocio_nombre": "CIENFUEGOS", "host": "10.0.0.1", "ventas": 300},
]


def _user(role):
    return {"role": role}


def test_superadmin_ve_todo_y_tecnicos():
    ctx = AnonymizerService.build_context(_user("SUPERADMIN"), allowed_server_ids=[])
    assert ctx.nivel == NivelConfidencialidad.COMPLETO
    out = AnonymizerService.anonymize_rows(ROWS, ctx)
    nombres = {r["unidad_negocio_nombre"] for r in out}
    assert nombres == {"LA ESTELAR", "130 MERIDA", "CIENFUEGOS"}
    # conserva técnicos
    assert any("sucursal_id" in r for r in out)
    assert all(r["nivel_anonimizacion_aplicado"] == "REAL" for r in out)


def test_gerente_unidad_ve_propia_anonimiza_resto_sin_tecnicos():
    ctx = AnonymizerService.build_context(_user("GERENTE_UNIDAD"), allowed_server_ids=[SRV_A])
    assert ctx.nivel == NivelConfidencialidad.PROPIO_NOMBRES
    out = AnonymizerService.anonymize_rows(ROWS, ctx, salt="req1")
    by_id = {r["server_id"] if "server_id" in r else None: r for r in out}
    # su unidad: nombre real
    propia = next(r for r in out if r.get("ventas") == 100)
    assert propia["unidad_negocio_nombre"] == "LA ESTELAR"
    assert propia["nivel_anonimizacion_aplicado"] == "REAL"
    # hermanas: anónimas
    hermanas = [r for r in out if r.get("ventas") in (200, 300)]
    assert all(r["unidad_negocio_nombre"].startswith("Unidad comparable") for r in hermanas)
    assert all(r["nivel_anonimizacion_aplicado"] == "ANONIMO" for r in hermanas)
    # SIN campos técnicos
    assert all("server_id" not in r and "sucursal_id" not in r and "host" not in r for r in out)


def test_analista_todo_anonimo():
    ctx = AnonymizerService.build_context(_user("ANALISTA_COMERCIAL"), allowed_server_ids=[SRV_A])
    assert ctx.nivel == NivelConfidencialidad.ANONIMO
    out = AnonymizerService.anonymize_rows(ROWS, ctx, salt="req1")
    assert all(r["unidad_negocio_nombre"].startswith("Unidad comparable") for r in out)
    assert all(r["nivel_anonimizacion_aplicado"] == "ANONIMO" for r in out)


def test_admin_comercial_ve_nombres_grupo_sin_tecnicos():
    ctx = AnonymizerService.build_context(_user("ADMIN_COMERCIAL"), allowed_server_ids=[SRV_A])
    assert ctx.nivel == NivelConfidencialidad.GRUPO_NOMBRES
    out = AnonymizerService.anonymize_rows(ROWS, ctx)
    assert {r["unidad_negocio_nombre"] for r in out} == {"LA ESTELAR", "130 MERIDA", "CIENFUEGOS"}
    assert all("server_id" not in r for r in out)  # sin técnicos


def test_alias_determinista_mismo_salt():
    ctx = AnonymizerService.build_context(_user("ANALISTA_COMERCIAL"), allowed_server_ids=[SRV_A])
    o1 = AnonymizerService.anonymize_rows(ROWS, ctx, salt="X")
    o2 = AnonymizerService.anonymize_rows(ROWS, ctx, salt="X")
    map1 = {r["ventas"]: r["unidad_negocio_nombre"] for r in o1}
    map2 = {r["ventas"]: r["unidad_negocio_nombre"] for r in o2}
    assert map1 == map2  # determinista dentro del mismo salt


def test_externo_portal_es_agregado():
    ctx = AnonymizerService.build_context({"role": "VISOR", "EsUsuarioPortal": True}, allowed_server_ids=[SRV_A])
    assert ctx.nivel == NivelConfidencialidad.AGREGADO
    assert ctx.es_externo is True
    out = AnonymizerService.anonymize_rows(ROWS, ctx, salt="X")
    assert all(r["unidad_negocio_nombre"].startswith("Unidad comparable") for r in out)
