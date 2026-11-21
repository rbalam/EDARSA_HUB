"""Orquestacion minima, sin escrituras, para auditoria ciega de Cavas.

Gate 16I mantiene este servicio stateless: lee inventario canonico por medio del
servicio existente y reconcilia observaciones con blind_audit. No persiste,
no ajusta inventario y no crea movimientos.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, Mapping

from .blind_audit import BlindObservation, ExpectedBottle, reconcile_blind_audit


class CavaBlindAuditOperationalService:
    """Adapta inventario canonico existente al dominio puro de auditoria ciega."""

    def reconcile(
        self,
        *,
        inventory_rows: Iterable[Mapping[str, Any]],
        observations: Iterable[Mapping[str, Any]],
        observation_to_bottle: Mapping[str, str],
        idempotency_key: str,
        level_tolerance_pct: float = 5.0,
        min_recognition_confidence: float = 0.90,
    ) -> Dict[str, Any]:
        key = str(idempotency_key or "").strip()
        if not key:
            raise ValueError("idempotency_key es requerido")

        inventory = tuple(inventory_rows)
        observed = tuple(observations)

        expected = tuple(
            ExpectedBottle(
                bottle_id=str(row.get("botella_id") or "").strip(),
                expected_quantity=1,
                expected_level_pct=(
                    float(row["porcentaje_restante"])
                    if row.get("porcentaje_restante") is not None
                    else None
                ),
            )
            for row in inventory
            if str(row.get("botella_id") or "").strip()
        )

        blind_observations = tuple(
            BlindObservation(
                observation_id=str(row.get("observation_id") or "").strip(),
                observed_reference=str(row.get("observed_reference") or "").strip(),
                observed_quantity=int(row.get("observed_quantity", 1)),
                observed_level_pct=(
                    float(row["observed_level_pct"])
                    if row.get("observed_level_pct") is not None
                    else None
                ),
                evidence_id=(
                    str(row["evidence_id"]).strip()
                    if row.get("evidence_id") is not None
                    else None
                ),
                recognition_confidence=(
                    float(row["recognition_confidence"])
                    if row.get("recognition_confidence") is not None
                    else None
                ),
            )
            for row in observed
        )

        result = reconcile_blind_audit(
            expected,
            blind_observations,
            observation_to_bottle=dict(observation_to_bottle),
            level_tolerance_pct=level_tolerance_pct,
            min_recognition_confidence=min_recognition_confidence,
        )

        statuses = [finding.status.value for finding in result.findings]
        if statuses and all(status == "MATCH" for status in statuses):
            outcome = "CONFIRMED"
        elif "REVIEW_REQUIRED" in statuses:
            outcome = "REVIEW_REQUIRED"
        else:
            outcome = "DIFFERENCE"

        fingerprint_payload = {
            "idempotency_key": key,
            "expected": [
                {
                    "bottle_id": item.bottle_id,
                    "expected_quantity": item.expected_quantity,
                    "expected_level_pct": item.expected_level_pct,
                }
                for item in expected
            ],
            "observations": [
                {
                    "observation_id": item.observation_id,
                    "observed_reference": item.observed_reference,
                    "observed_quantity": item.observed_quantity,
                    "observed_level_pct": item.observed_level_pct,
                    "evidence_id": item.evidence_id,
                    "recognition_confidence": item.recognition_confidence,
                }
                for item in blind_observations
            ],
            "mapping": dict(sorted(observation_to_bottle.items())),
        }
        fingerprint = hashlib.sha256(
            json.dumps(
                fingerprint_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()

        return {
            "outcome": outcome,
            "requires_review": result.requires_review,
            "clean": result.clean,
            "idempotency_key": key,
            "request_fingerprint": fingerprint,
            "findings": [
                {
                    "status": finding.status.value,
                    "expected_bottle_id": finding.expected_bottle_id,
                    "observation_id": finding.observation_id,
                    "expected_quantity": finding.expected_quantity,
                    "observed_quantity": finding.observed_quantity,
                    "expected_level_pct": finding.expected_level_pct,
                    "observed_level_pct": finding.observed_level_pct,
                    "reason": finding.reason,
                }
                for finding in result.findings
            ],
            "automatic_inventory_adjustment": False,
            "automatic_inventory_movement": False,
        }


_service = CavaBlindAuditOperationalService()


def get_cava_blind_audit_operational_service() -> CavaBlindAuditOperationalService:
    return _service
