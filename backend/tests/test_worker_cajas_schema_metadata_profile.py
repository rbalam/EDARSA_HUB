from modules.worker_ingress import semantic_capabilities as sem
import pytest


def test_cajas_profile_metadata_only():
    p = sem.sql_readonly_profiles()["CAJAS_INCIDENCIAS_SCHEMA_METADATA"]
    assert p.bounded_contexts == ("COMERCIAL_POS",)
    assert p.source == "EDARSAHUB" and p.login_policy == "HRLectura" and p.read_only
    assert len(p.queries) == 9
    discovery = {q["name"] for q in p.queries if q["name"].startswith("cajas_expedientes_")}
    assert discovery == {"cajas_expedientes_tables", "cajas_expedientes_columns", "cajas_expedientes_indexes", "cajas_expedientes_relationships"}
    for q in p.queries:
        assert q["sql"].startswith("SELECT ")
        assert "FROM dbo." not in q["sql"]
        if q["name"] != "cajas_identity":
            assert "FROM sys.tables" in q["sql"]
            if q["name"].startswith("cajas_expedientes_"):
                assert "t.name LIKE" in q["sql"]
            else:
                for name in ["Finanzas_CortesCaja","Finanzas_CuadresZ","Usuario_Autorizaciones","Sistema_Tareas","Operativo_Notificaciones_Queue"]:
                    assert name in q["sql"]


def test_cajas_profile_rejects_other_domain_and_arbitrary_sql():
    request = {"bounded_context": "RH", "constraints": {"profile_code": "CAJAS_INCIDENCIAS_SCHEMA_METADATA"}}
    with pytest.raises(sem.SemanticCapabilityError):
        sem._sql_readonly_profile_audit_builder(request)
    request["bounded_context"] = "COMERCIAL_POS"
    request["constraints"]["sql"] = "SELECT 1"
    with pytest.raises(sem.SemanticCapabilityError):
        sem._sql_readonly_profile_audit_builder(request)


def test_rh_integridad_profile_metadata_only():
    p = sem.sql_readonly_profiles()["RH_INTEGRIDAD_DENUNCIAS_SCHEMA_METADATA"]
    assert p.bounded_contexts == ("RH",)
    assert p.source == "EDARSAHUB" and p.login_policy == "HRLectura" and p.read_only
    assert len(p.queries) == 3
    for query in p.queries:
        assert query["sql"].startswith("SELECT ")
        assert "FROM sys.tables" in query["sql"]
        assert not any(fragment in query["sql"] for fragment in ("RH_Incidencias_Nomina WHERE", "SELECT *", "FROM dbo."))
    req = {"bounded_context": "RH", "constraints": {"profile_code": p.profile_code}}
    plan = sem._sql_readonly_profile_audit_builder(req)
    assert plan["actions"] == []
    assert len(plan["checks"]) == 1
    assert plan["checks"][0]["type"] == "sql_readonly_audit"


def test_rh_integridad_profile_fail_closed_for_domain_and_caller_sql():
    req = {"bounded_context": "COMERCIAL_POS", "constraints": {"profile_code": "RH_INTEGRIDAD_DENUNCIAS_SCHEMA_METADATA"}}
    with pytest.raises(sem.SemanticCapabilityError):
        sem._sql_readonly_profile_audit_builder(req)
    req["bounded_context"] = "RH"
    req["constraints"]["sql"] = "SELECT * FROM dbo.Usuario_Catalogo"
    with pytest.raises(sem.SemanticCapabilityError):
        sem._sql_readonly_profile_audit_builder(req)
