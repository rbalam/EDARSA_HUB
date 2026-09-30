from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "modules/comercial/routes.py"
FRONT = ROOT.parent / "frontend/src/pages/Comercial.js"
SCHEMA = ROOT / "modules/comercial_v2/schemas.py"
REPO = ROOT / "modules/comercial_v2/repository_comercial_edarsahub.py"
SYNC = ROOT / "core/scheduler/jobs/sync_comercial_abiertas_v2_job.py"
SNAPSHOT = ROOT / "modules/comercial_v2/ticket_snapshot.py"
SERVICE = ROOT / "modules/comercial/ticket_service.py"
MIGRATION = ROOT / "database/migrations/20260930_002_comercial_ticket_open_detail_json.sql"


def test_ticket_route_and_ui_contract():
    routes = ROUTES.read_text(encoding="utf-8")
    front = FRONT.read_text(encoding="utf-8")
    assert '/comercial/ticket-venta/{server_id}' in routes
    assert "TicketVentaModal" in front
    assert "/comercial/ticket-venta/" in front
    assert "TICKET DE SERVICIO" in front

    ticket_block = front[
        front.index("function TicketVentaModal"):
        front.index("function DetalleMovimientosModal")
    ]
    assert "AUTORIZÓ" not in ticket_block
    assert "autorizacion" not in ticket_block.lower()


def test_open_detail_reuses_existing_daily_sync():
    schema = SCHEMA.read_text(encoding="utf-8")
    repo = REPO.read_text(encoding="utf-8")
    sync = SYNC.read_text(encoding="utf-8")
    snapshot = SNAPSHOT.read_text(encoding="utf-8")

    assert "detalle_abiertas_json" in schema
    assert "COL_LENGTH" in repo
    assert "detalle_abiertas_json" in repo
    assert "QUERY_SOFTRESTAURANT_DETALLE_ABIERTAS" in sync
    assert "QUERY_MPRO_DETALLE_ABIERTAS" in sync
    assert "serialize_open_detail_rows" in sync
    assert "tempcheqdet" in snapshot
    assert "Comanda_Detalle" in snapshot


def test_ticket_service_is_no_live_and_migration_is_additive():
    service = SERVICE.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")

    assert "Comercial_Inteligencia_VentasDetalleProducto" in service
    assert "Comercial_Ventas_Dia_Abiertas_v2" in service
    assert "execute_query_on_server" not in service
    assert "_execute_query_via_api_local" not in service
    assert "ALTER TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2" in migration
    assert "detalle_abiertas_json NVARCHAR(MAX) NULL" in migration
    assert "DROP TABLE" not in migration.upper()
    assert "DELETE FROM" not in migration.upper()
