from modules.bos_executive import (
    PriorityBand,
    adapt_crm_opportunity,
    adapt_operational_task,
    aggregate_priorities,
)


def test_e3b_operational_sla_reuses_existing_state_as_priority_signal():
    item = adapt_operational_task(
        {
            "id": "T-1",
            "titulo": "Revisar diferencia",
            "estado_sla": "VENCIDA",
            "prioridad": "MEDIA",
            "fecha_limite": "2026-09-19T08:00:00Z",
            "responsable_id": "user-1",
            "permission_refs": ["OPERATIVO_VER"],
        }
    )

    assert item is not None
    assert item.source_domain == "OPERATIVO"
    assert item.source_object_ref == "tarea:T-1"
    assert item.priority_band is PriorityBand.CRITICA
    assert "SLA_VENCIDA" in item.priority_score_explanation
    assert item.owner_ref == "user-1"
    assert item.permission_refs == ("OPERATIVO_VER",)


def test_e3b_crm_sla_adapter_normalizes_without_creating_task_lifecycle():
    item = adapt_crm_opportunity(
        {
            "OportunidadID": "OP-9",
            "Nombre": "Renovacion mayorista",
            "MontoEstimado": 250000,
            "EstatusSLA": "PROXIMO",
            "Prioridad": "BAJA",
            "ResponsableID": "crm-7",
        }
    )

    assert item is not None
    assert item.source_domain == "CRM"
    assert item.source_object_ref == "oportunidad:OP-9"
    assert item.priority_band is PriorityBand.ALTA
    assert item.impact == "monto_estimado:250000"
    assert "CRM_SLA_PROXIMO" in item.priority_score_explanation


def test_e3b_adapter_fails_closed_without_source_identity():
    assert adapt_operational_task({"estado_sla": "VENCIDA"}) is None
    assert adapt_crm_opportunity({"EstatusSLA": "VENCIDO"}) is None


def test_e3b_aggregator_is_cross_domain_deterministic_and_read_only():
    critical = adapt_operational_task(
        {
            "id": "T-2",
            "estado_sla": "ESCALADA",
            "fecha_limite": "2026-09-19T07:00:00Z",
        }
    )
    crm = adapt_crm_opportunity(
        {
            "OportunidadID": "OP-1",
            "EstatusSLA": "PROXIMO",
            "MontoEstimado": 1000,
        }
    )
    medium = adapt_operational_task(
        {
            "id": "T-3",
            "prioridad": "MEDIA",
            "fecha_limite": "2026-09-20T07:00:00Z",
        }
    )

    result = aggregate_priorities([medium, crm, critical])

    assert result.total == 3
    assert result.domains == ("CRM", "OPERATIVO")
    assert [item.source_object_ref for item in result.items] == [
        "tarea:T-2",
        "oportunidad:OP-1",
        "tarea:T-3",
    ]


def test_e3b_same_band_uses_due_date_not_global_numeric_weights():
    later = adapt_operational_task(
        {
            "id": "T-LATE",
            "prioridad": "ALTA",
            "fecha_limite": "2026-09-20T12:00:00Z",
        }
    )
    sooner = adapt_operational_task(
        {
            "id": "T-SOON",
            "prioridad": "ALTA",
            "fecha_limite": "2026-09-19T12:00:00Z",
        }
    )

    result = aggregate_priorities([later, sooner])

    assert [item.source_object_ref for item in result.items] == [
        "tarea:T-SOON",
        "tarea:T-LATE",
    ]


def test_e3b_aggregate_propagates_stale_without_hiding_priority():
    stale = adapt_operational_task(
        {
            "id": "T-STALE",
            "estado_sla": "VENCIDA",
            "stale": True,
        }
    )

    result = aggregate_priorities([stale])

    assert result.stale is True
    assert result.items[0].priority_band is PriorityBand.CRITICA
