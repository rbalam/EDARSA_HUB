from pathlib import Path

from modules.sistema import sync_catalogo_service as service


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "database/migrations/20261009_001_sync_historical_capability_registry.sql"
SERVICE = ROOT / "modules/sistema/sync_catalogo_service.py"


def _base_row():
    return {
        "Codigo": "ventas_ticket",
        "Nombre": "Ventas por ticket",
        "Grupo": "Ventas",
        "Descripcion": "Detalle historico",
        "Orden": 20,
        "NivelRiesgo": "MEDIO",
        "PermiteResync": 1,
        "PermiteDryRun": 1,
        "RequiereUnidad": 1,
        "RequiereRangoFechas": 1,
        "RangoMaxDias": 31,
        "Handler": "sync_ventas_ticket",
        "HandlerImplementado": 1,
        "TablaDestino": "Sync_Sales",
        "Dependencias": "[]",
        "Activo": 1,
        "CategoriaCodigo": "VENTAS",
        "EntidadCodigo": "VENTA_TICKET",
        "CampoFecha": "FechaHora",
        "ClaveNegocio": '["unidad_negocio_pk","NumeroTicket","FechaHora"]',
        "SoportaIncremental": 1,
        "SoportaFullSync": 1,
        "SoportaResume": 1,
        "SoportaSafeStop": 1,
        "VersionContrato": "1",
        "MetadataJSON": '{"chunk_unit":"day"}',
        "SyncCapacidadID": 101,
        "VinculoObligatorio": 1,
        "VinculoActivo": 1,
        "SistemaCapacidadID": 201,
        "CodigoCapacidad": "SYNC_VENTAS_HISTORICAS",
        "CapacidadSistemaActiva": 1,
        "SistemaTipoID": 2,
        "CodigoSistema": "MPRO",
        "NombreSistema": "ManagementPro",
        "SistemaActivo": 1,
    }


def test_migration_extends_existing_catalog_instead_of_creating_parallel_catalog():
    source = MIGRATION.read_text(encoding="utf-8")
    assert "ALTER TABLE dbo.Sistema_Sync_Catalogo" in source
    assert "CREATE TABLE dbo.Sistema_Sync_Catalogo" not in source
    assert "Sistema_Sync_Capacidades" in source
    assert "SoportaResume" in source
    assert "SoportaSafeStop" in source


def test_registry_reuses_existing_semantics_and_adds_only_missing_metadata():
    item = service._historical_row_to_dict(_base_row())

    assert item["capability_key"] == "ventas_ticket"
    assert item["display_name"] == "Ventas por ticket"
    assert item["category_name"] == "Ventas"
    assert item["supports_historical"] is True
    assert item["execution_order"] == 20
    assert item["enabled"] is True
    assert item["system_id"] == 2
    assert item["system_code"] == "MPRO"
    assert item["business_key"] == [
        "unidad_negocio_pk",
        "NumeroTicket",
        "FechaHora",
    ]
    assert item["metadata"]["chunk_unit"] == "day"
    assert item["eligible_for_historical"] is True
    assert item["incomplete_reasons"] == []


def test_registry_fails_closed_when_binding_and_required_metadata_are_missing():
    row = _base_row()
    row.update({
        "CategoriaCodigo": None,
        "EntidadCodigo": None,
        "CampoFecha": None,
        "ClaveNegocio": None,
        "SyncCapacidadID": None,
        "VinculoActivo": None,
        "SistemaCapacidadID": None,
        "CodigoCapacidad": None,
        "CapacidadSistemaActiva": None,
        "SistemaTipoID": None,
        "CodigoSistema": None,
        "NombreSistema": None,
        "SistemaActivo": None,
    })

    item = service._historical_row_to_dict(row)

    assert item["eligible_for_historical"] is False
    assert "CATEGORY_KEY_MISSING" in item["incomplete_reasons"]
    assert "ENTITY_KEY_MISSING" in item["incomplete_reasons"]
    assert "DATE_FIELD_MISSING" in item["incomplete_reasons"]
    assert "BUSINESS_KEY_MISSING" in item["incomplete_reasons"]
    assert "SYSTEM_BINDING_MISSING" in item["incomplete_reasons"]


def test_protected_daily_sync_is_not_part_of_phase_1_or_phase_2_changes():
    source = (
        MIGRATION.read_text(encoding="utf-8")
        + "\n"
        + SERVICE.read_text(encoding="utf-8")
    ).lower()
    assert "sync_comercial_abiertas_v2" not in source
