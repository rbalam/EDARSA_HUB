"""Regresion de perfil SQL READ_ONLY del estado historico de conexiones."""
from modules.worker_ingress import semantic_capabilities as sem

PROFILE = "SERVIDORES_HEALTH_FRESHNESS_CONFIG_METADATA"


def test_profile_registered_for_connections_and_worker_owner():
    p = sem.sql_readonly_profiles()[PROFILE]
    assert p.source == "EDARSAHUB"
    assert p.login_policy == "HRLectura"
    assert p.read_only is True
    assert "CONEXIONES_COMUNICACIONES" in p.bounded_contexts
    assert "WORKER_CONTROL_PLANE" in p.bounded_contexts
    assert len(p.queries) == 3


def test_profile_contains_only_sealed_schema_metadata():
    p = sem.sql_readonly_profiles()[PROFILE]
    for query in p.queries:
        sql = query["sql"].upper()
        assert sql.startswith("SELECT ")
        assert "SELECT *" not in sql
        assert "DBO.SERVIDORES_CONEXIONES" not in sql
        assert "PASSWORD" not in sql
        assert "API_KEY" not in sql
        assert "OPENROWSET" not in sql
        assert sem._validate_readonly_sql_query(query) == query
    assert "SYS.TABLES" in p.queries[1]["sql"].upper()
    assert "SYS.COLUMNS" in p.queries[2]["sql"].upper()
