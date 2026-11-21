from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = ROOT / "backend/modules/integrations_center/api_factory_repository.py"
ROUTES = ROOT / "backend/modules/integrations_center/routes.py"


def test_repository_reads_all_h8_tables_without_writes_or_credentials():
    text = REPOSITORY.read_text(encoding="utf-8")
    for table in (
        "Sistema_ApiFactoryApi",
        "Sistema_ApiFactoryVersion",
        "Sistema_ApiFactoryConsumer",
        "Sistema_ApiFactoryConsumerGrant",
    ):
        assert table in text
    upper = text.upper()
    for forbidden in (" INSERT ", " UPDATE ", " DELETE ", " MERGE ", " DROP ", " ALTER ", " CREATE "):
        assert forbidden not in f" {upper} "
    assert "CredentialReference AS" not in text
    assert "credential_reference" not in text


def test_api_factory_admin_routes_are_read_only_and_rbac_protected():
    text = ROUTES.read_text(encoding="utf-8")
    routes = (
        "/api-factory/overview",
        "/api-factory/apis",
        "/api-factory/apis/{api_id}/versions",
        "/api-factory/consumers",
        "/api-factory/consumers/{consumer_id}/grants",
    )
    for route in routes:
        assert f'@router.get("{route}")' in text
    block = text.split('@router.get("/api-factory/overview")', 1)[1]
    assert block.count('Depends(require_permission("SERVIDORES_VER"))') >= 5
    assert "@router.post(" not in block
    assert "@router.put(" not in block
    assert "@router.patch(" not in block
    assert "@router.delete(" not in block
