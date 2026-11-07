"""HTTP contract for Worker Console audit; simulated RBAC, no SQL connectivity."""
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from modules.worker_console import routes


def _client(outcome):
    app = FastAPI()
    app.include_router(routes.router)

    async def mock_effective_sql_permission():
        if outcome == "missing":
            raise HTTPException(status_code=401, detail="TOKEN_REQUIRED")
        if outcome == "denied":
            raise HTTPException(status_code=403, detail="PERMISO_DENEGADO")
        return {"email": "ci-user@example.invalid"}

    app.dependency_overrides[routes.AUDIT_ADMIN_DEPENDENCY] = mock_effective_sql_permission
    return TestClient(app)


def test_worker_audit_http_401():
    with _client("missing") as client:
        response = client.get("/worker/console/audit")
    assert response.status_code == 401


def test_worker_audit_http_403():
    with _client("denied") as client:
        response = client.get("/worker/console/audit")
    assert response.status_code == 403


def test_worker_audit_http_200_for_mock_authorized_user(tmp_path, monkeypatch):
    from modules.worker_console import contract
    monkeypatch.setattr(contract, "QUEUE_ROOT", tmp_path)
    with _client("allowed") as client:
        response = client.get("/worker/console/audit")
    assert response.status_code == 200
    assert response.json()["cert_log"] == []
    assert response.json()["launch_log"] == []


def test_audit_depends_on_sql_explicit_not_legacy_admin():
    from core.rbac.middleware import RBACExplicitDependency
    assert isinstance(routes.AUDIT_ADMIN_DEPENDENCY, RBACExplicitDependency)
    assert routes.AUDIT_ADMIN_DEPENDENCY.permiso == "RBAC_ADMIN"
