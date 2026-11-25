from modules.worker_ingress import semantic_capabilities as sem
import pytest


def test_cajas_profile_metadata_only():
    p = sem.sql_readonly_profiles()["CAJAS_INCIDENCIAS_SCHEMA_METADATA"]
    assert p.bounded_contexts == ("COMERCIAL_POS",)
    assert p.source == "EDARSAHUB" and p.login_policy == "HRLectura" and p.read_only
    assert len(p.queries) == 5
    for q in p.queries:
        assert q["sql"].startswith("SELECT ")
        if q["name"] != "cajas_identity":
            assert "FROM sys.tables" in q["sql"]
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
