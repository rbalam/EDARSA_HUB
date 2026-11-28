"""SQL Server repository for Production Quality.

This module is the only Production Quality layer allowed to issue SQL.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from core.sql_first.db import get_sql_connection


def _normalize(row: Any) -> Optional[dict]:
    if row is None:
        return None
    return dict(row)


class ProductionQualityRepository:
    def _connection(self):
        return get_sql_connection()

    def resolve_usuario_id(self, public_uuid: str) -> Optional[int]:
        conn = self._connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT TOP 1 UsuarioID
                FROM dbo.Usuario_Catalogo
                WHERE LOWER(CAST(PublicUUID AS varchar(36))) = LOWER(%s)
                  AND ISNULL(Activo, 1) = 1
                """,
                (str(public_uuid),),
            )
            row = cur.fetchone()
            return int(row["UsuarioID"]) if row else None
        finally:
            conn.close()

    def get_item_scope(self, production_item_id: UUID) -> Optional[dict]:
        conn = self._connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT
                    ProductionItemID,
                    EmpresaID,
                    UnidadNegocioID,
                    FechaOperacion,
                    ProductionStationID,
                    EstadoProduccion
                FROM dbo.Production_Item
                WHERE ProductionItemID = %s
                """,
                (str(production_item_id),),
            )
            return _normalize(cur.fetchone())
        finally:
            conn.close()

    def list_items(
        self,
        empresa_id: int,
        unidad_negocio_id: UUID,
        fecha_operacion,
        limit: int,
        offset: int,
    ) -> list[dict]:
        conn = self._connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT
                    ProductionItemID,
                    EmpresaID,
                    UnidadNegocioID,
                    ServerID,
                    FechaOperacion,
                    SourceSystem,
                    SourceTransactionID,
                    SourceLineID,
                    KDSTicketLineID,
                    ProductoCodigo,
                    ProductionStationID,
                    EstadoProduccion,
                    CreatedAtUTC,
                    UpdatedAtUTC
                FROM dbo.Production_Item
                WHERE EmpresaID = %s
                  AND UnidadNegocioID = %s
                  AND FechaOperacion = %s
                ORDER BY CreatedAtUTC DESC
                OFFSET %s ROWS
                FETCH NEXT %s ROWS ONLY
                """,
                (
                    empresa_id,
                    str(unidad_negocio_id),
                    fecha_operacion,
                    offset,
                    limit,
                ),
            )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def list_standards(
        self,
        empresa_id: int,
        unidad_negocio_id: UUID,
    ) -> list[dict]:
        conn = self._connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT
                    s.QualityStandardID,
                    s.EmpresaID,
                    s.UnidadNegocioID,
                    s.ProductoCodigo,
                    s.Nombre,
                    s.Activo,
                    s.CreatedAtUTC
                FROM dbo.Production_QualityStandard AS s
                WHERE s.EmpresaID = %s
                  AND (
                        s.UnidadNegocioID IS NULL
                     OR s.UnidadNegocioID = %s
                  )
                  AND ISNULL(s.Activo, 1) = 1
                ORDER BY s.Nombre
                """,
                (empresa_id, str(unidad_negocio_id)),
            )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def list_devices(
        self,
        empresa_id: int,
        unidad_negocio_id: UUID,
    ) -> list[dict]:
        conn = self._connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT
                    DeviceID,
                    EmpresaID,
                    UnidadNegocioID,
                    ServerID,
                    ProductionStationID,
                    DeviceType,
                    Codigo,
                    Nombre,
                    AdapterType,
                    ConnectionRef,
                    Estado,
                    LastHeartbeatAtUTC,
                    CalibrationRequired,
                    Activo
                FROM dbo.Production_Device
                WHERE EmpresaID = %s
                  AND UnidadNegocioID = %s
                  AND ISNULL(Activo, 1) = 1
                ORDER BY Nombre
                """,
                (empresa_id, str(unidad_negocio_id)),
            )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def create_measurement(
        self,
        payload: dict,
        usuario_id: int,
        fecha_operacion,
    ) -> dict:
        measurement_id = str(uuid4())
        captured = payload.get("captured_at_utc") or datetime.now(timezone.utc)

        conn = self._connection()
        try:
            cur = conn.cursor(as_dict=True)

            cur.execute(
                """
                SELECT TOP 1 *
                FROM dbo.Production_Measurement
                WHERE IdempotencyKey = %s
                """,
                (payload["idempotency_key"],),
            )
            existing = cur.fetchone()
            if existing:
                return dict(existing)

            cur.execute(
                """
                INSERT INTO dbo.Production_Measurement (
                    MeasurementID,
                    ProductionItemID,
                    ProductionStationID,
                    QualityStandardVersionID,
                    DeviceID,
                    EmpresaID,
                    UnidadNegocioID,
                    FechaOperacion,
                    MeasurementType,
                    NumericValue,
                    UnitCode,
                    CapturedAtUTC,
                    OperatorUserID,
                    Source,
                    IdempotencyKey
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                """,
                (
                    measurement_id,
                    str(payload["production_item_id"]),
                    str(payload["production_station_id"])
                    if payload.get("production_station_id") else None,
                    str(payload["quality_standard_version_id"])
                    if payload.get("quality_standard_version_id") else None,
                    str(payload["device_id"])
                    if payload.get("device_id") else None,
                    payload["empresa_id"],
                    str(payload["unidad_negocio_id"]),
                    fecha_operacion,
                    payload["measurement_type"],
                    payload["numeric_value"],
                    payload["unit_code"],
                    captured,
                    usuario_id,
                    payload["source"],
                    payload["idempotency_key"],
                ),
            )

            conn.commit()

            cur.execute(
                """
                SELECT *
                FROM dbo.Production_Measurement
                WHERE MeasurementID = %s
                """,
                (measurement_id,),
            )
            return dict(cur.fetchone())
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_evidence(
        self,
        payload: dict,
        usuario_id: int,
        fecha_operacion,
    ) -> dict:
        evidence_id = str(uuid4())
        captured = payload.get("captured_at_utc") or datetime.now(timezone.utc)

        conn = self._connection()
        try:
            cur = conn.cursor(as_dict=True)

            cur.execute(
                """
                SELECT TOP 1 *
                FROM dbo.Production_Evidence
                WHERE IdempotencyKey = %s
                """,
                (payload["idempotency_key"],),
            )
            existing = cur.fetchone()
            if existing:
                return dict(existing)

            cur.execute(
                """
                INSERT INTO dbo.Production_Evidence (
                    EvidenceID,
                    ProductionItemID,
                    ProductionStationID,
                    DeviceID,
                    EmpresaID,
                    UnidadNegocioID,
                    FechaOperacion,
                    EvidenceType,
                    StoragePath,
                    ContentType,
                    ByteSize,
                    ContentHash,
                    CapturedAtUTC,
                    OperatorUserID,
                    IdempotencyKey
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                """,
                (
                    evidence_id,
                    str(payload["production_item_id"]),
                    str(payload["production_station_id"])
                    if payload.get("production_station_id") else None,
                    str(payload["device_id"])
                    if payload.get("device_id") else None,
                    payload["empresa_id"],
                    str(payload["unidad_negocio_id"]),
                    fecha_operacion,
                    payload["evidence_type"],
                    payload["storage_path"],
                    payload["content_type"],
                    payload.get("byte_size"),
                    payload["content_hash"],
                    captured,
                    usuario_id,
                    payload["idempotency_key"],
                ),
            )

            conn.commit()

            cur.execute(
                """
                SELECT *
                FROM dbo.Production_Evidence
                WHERE EvidenceID = %s
                """,
                (evidence_id,),
            )
            return dict(cur.fetchone())
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_decision(
        self,
        payload: dict,
        usuario_id: int,
    ) -> dict:
        decision_id = str(uuid4())

        conn = self._connection()
        try:
            cur = conn.cursor(as_dict=True)

            cur.execute(
                """
                SELECT TOP 1 *
                FROM dbo.Production_QualityDecision
                WHERE IdempotencyKey = %s
                """,
                (payload["idempotency_key"],),
            )
            existing = cur.fetchone()
            if existing:
                return dict(existing)

            cur.execute(
                """
                SELECT ISNULL(MAX(AttemptNumber), 0) + 1 AS AttemptNumber
                FROM dbo.Production_QualityDecision
                WHERE ProductionItemID = %s
                """,
                (str(payload["production_item_id"]),),
            )
            attempt = int(cur.fetchone()["AttemptNumber"])

            cur.execute(
                """
                INSERT INTO dbo.Production_QualityDecision (
                    QualityDecisionID,
                    ProductionItemID,
                    QualityStandardVersionID,
                    Decision,
                    ReasonCode,
                    ReasonText,
                    AttemptNumber,
                    PreviousDecisionID,
                    EvaluatedAtUTC,
                    EvaluatorUserID,
                    ReleasedAtUTC,
                    IdempotencyKey
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, SYSUTCDATETIME(), %s, %s, %s
                )
                """,
                (
                    decision_id,
                    str(payload["production_item_id"]),
                    str(payload["quality_standard_version_id"])
                    if payload.get("quality_standard_version_id") else None,
                    payload["decision"],
                    payload.get("reason_code"),
                    payload.get("reason_text"),
                    attempt,
                    str(payload["previous_decision_id"])
                    if payload.get("previous_decision_id") else None,
                    usuario_id,
                    datetime.now(timezone.utc)
                    if payload["decision"] == "PASS" else None,
                    payload["idempotency_key"],
                ),
            )

            conn.commit()

            cur.execute(
                """
                SELECT *
                FROM dbo.Production_QualityDecision
                WHERE QualityDecisionID = %s
                """,
                (decision_id,),
            )
            return dict(cur.fetchone())
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_action(
        self,
        payload: dict,
        usuario_id: int,
    ) -> dict:
        action_id = str(uuid4())

        conn = self._connection()
        try:
            cur = conn.cursor(as_dict=True)

            cur.execute(
                """
                SELECT TOP 1 *
                FROM dbo.Production_QualityAction
                WHERE IdempotencyKey = %s
                """,
                (payload["idempotency_key"],),
            )
            existing = cur.fetchone()
            if existing:
                return dict(existing)

            cur.execute(
                """
                INSERT INTO dbo.Production_QualityAction (
                    QualityActionID,
                    ProductionItemID,
                    QualityDecisionID,
                    EvidenceID,
                    ActionType,
                    Estado,
                    ReasonCode,
                    ReasonText,
                    RequestedByUserID,
                    ApprovedByUserID,
                    RequestedAtUTC,
                    ApprovedAtUTC,
                    CompletedAtUTC,
                    IdempotencyKey
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    SYSUTCDATETIME(), %s, %s, %s
                )
                """,
                (
                    action_id,
                    str(payload["production_item_id"]),
                    str(payload["quality_decision_id"]),
                    str(payload["evidence_id"])
                    if payload.get("evidence_id") else None,
                    payload["action_type"],
                    "APPROVED"
                    if payload["action_type"] == "OVERRIDE"
                    else "REQUESTED",
                    payload.get("reason_code"),
                    payload.get("reason_text"),
                    usuario_id,
                    usuario_id
                    if payload["action_type"] == "OVERRIDE"
                    else None,
                    datetime.now(timezone.utc)
                    if payload["action_type"] == "OVERRIDE"
                    else None,
                    None,
                    payload["idempotency_key"],
                ),
            )

            conn.commit()

            cur.execute(
                """
                SELECT *
                FROM dbo.Production_QualityAction
                WHERE QualityActionID = %s
                """,
                (action_id,),
            )
            return dict(cur.fetchone())
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_calibration(
        self,
        payload: dict,
        usuario_id: int,
    ) -> dict:
        calibration_id = str(uuid4())
        calibrated = payload.get("calibrated_at_utc") or datetime.now(timezone.utc)

        conn = self._connection()
        try:
            cur = conn.cursor(as_dict=True)

            cur.execute(
                """
                INSERT INTO dbo.Production_DeviceCalibration (
                    DeviceCalibrationID,
                    DeviceID,
                    EvidenceID,
                    CalibrationType,
                    CalibrationValue,
                    UnitCode,
                    CalibratedAtUTC,
                    ValidUntilUTC,
                    CalibratedByUserID,
                    Notes
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                """,
                (
                    calibration_id,
                    str(payload["device_id"]),
                    str(payload["evidence_id"])
                    if payload.get("evidence_id") else None,
                    payload["calibration_type"],
                    payload.get("calibration_value"),
                    payload.get("unit_code"),
                    calibrated,
                    payload.get("valid_until_utc"),
                    usuario_id,
                    payload.get("notes"),
                ),
            )

            conn.commit()

            cur.execute(
                """
                SELECT *
                FROM dbo.Production_DeviceCalibration
                WHERE DeviceCalibrationID = %s
                """,
                (calibration_id,),
            )
            return dict(cur.fetchone())
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
