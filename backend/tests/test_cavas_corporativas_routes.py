from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from modules.cavas_corporativas.domain import EvaluationDecision
from modules.cavas_corporativas.routes import (
    CAN_APPLY,
    CAN_EVALUATE,
    get_cavas_corporativas_service,
    router,
)
from modules.cavas_corporativas.service import BenefitEvaluation


PAYLOAD = {
    "identidad_fuente": "CRM_CANONICO",
    "identidad_referencia": "persona-1",
    "occurred_at": "2026-09-08T18:00:00",
    "unit_reference": "130MID",
    "sales_line_reference": "ALIMENTOS",
    "has_reservation": True,
    "guest_count": 4,
}


class FakeService:
    def __init__(self):
        self.applied = set()

    def evaluate_for_identity(self, identidad_fuente, identidad_referencia, context):
        return BenefitEvaluation(
            "convenio-1",
            "autorizado-1",
            (EvaluationDecision(True, "APPLICABLE", "benefit-1"),),
        )

    def record_applied_benefit(self, **kwargs):
        key = (kwargs["benefit_id"], kwargs["operacion_tipo"], kwargs["operacion_referencia"])
        if key in self.applied:
            return False
        self.applied.add(key)
        return True


def _app(auth_dependency, service=None):
    app = FastAPI()
    app.include_router(router, prefix="/api")
    if auth_dependency is not None:
        app.dependency_overrides[CAN_EVALUATE] = auth_dependency
        app.dependency_overrides[CAN_APPLY] = auth_dependency
    if service is not None:
        app.dependency_overrides[get_cavas_corporativas_service] = lambda: service
    return app


def test_rbac_contract_reuses_certified_existing_permissions():
    assert CAN_EVALUATE.permiso == "cava_socios.VER"
    assert CAN_APPLY.permiso == "cava_socios.consumos.CREAR"


def test_api_returns_401_when_auth_dependency_denies():
    def deny():
        raise HTTPException(status_code=401, detail="Token requerido")
    client = TestClient(_app(deny, FakeService()))
    response = client.post("/api/cavas/corporativas/evaluar", json=PAYLOAD)
    assert response.status_code == 401


def test_api_returns_403_when_rbac_denies():
    def deny():
        raise HTTPException(status_code=403, detail="PERMISO_DENEGADO")
    client = TestClient(_app(deny, FakeService()))
    response = client.post("/api/cavas/corporativas/evaluar", json=PAYLOAD)
    assert response.status_code == 403


def test_evaluate_returns_200_with_applicable_decision():
    service = FakeService()
    client = TestClient(_app(lambda: {"id": "u1", "email": "user@example.com"}, service))
    response = client.post("/api/cavas/corporativas/evaluar", json=PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["convenio_id"] == "convenio-1"
    assert body["decisions"][0]["applicable"] is True


def test_apply_is_idempotent_end_to_end_at_api_boundary():
    service = FakeService()
    client = TestClient(_app(lambda: {"id": "u1", "email": "user@example.com"}, service))
    payload = {**PAYLOAD, "benefit_id": "benefit-1", "operacion_tipo": "TICKET", "operacion_referencia": "ticket-42"}
    first = client.post("/api/cavas/corporativas/aplicar", json=payload)
    second = client.post("/api/cavas/corporativas/aplicar", json=payload)
    assert first.status_code == 200
    assert first.json()["inserted"] is True
    assert first.json()["idempotent_replay"] is False
    assert second.status_code == 200
    assert second.json()["inserted"] is False
    assert second.json()["idempotent_replay"] is True
