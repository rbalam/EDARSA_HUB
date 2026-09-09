"""Repositorio SQL canonico para Cavas Corporativas.

Usa exclusivamente las tablas dbo.CavasCorporativas_* ya certificadas. No crea
esquema, no contiene datos semilla y permite inyectar la fabrica de conexion
para pruebas deterministas.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal
from typing import Callable, Iterable, Optional

from .domain import BenefitKind, BenefitRule, BenefitScope, PolicyRestrictions, ScopeKind


@dataclass(frozen=True)
class AuthorizedReference:
    autorizado_id: str
    convenio_id: str


@dataclass(frozen=True)
class ApplicationRecord:
    convenio_id: str
    beneficio_id: str
    autorizado_id: Optional[str]
    unidad_referencia: str
    operacion_tipo: str
    operacion_referencia: str
    evento_temporal_tipo: Optional[str] = None
    evento_temporal_utc: Optional[datetime] = None
    importe_base: Optional[Decimal] = None
    importe_beneficio: Optional[Decimal] = None
    moneda_codigo: Optional[str] = None
    evaluacion: Optional[dict] = None
    applied_by_referencia: Optional[str] = None


def _default_connection_factory():
    from core.sql_first.connection_factory import get_edarsahub_pymssql_connection
    return get_edarsahub_pymssql_connection(timeout=30, login_timeout=10, autocommit=False)


def _parse_time(value: object) -> Optional[time]:
    if value in (None, ""):
        return None
    if isinstance(value, time):
        return value
    return time.fromisoformat(str(value))


def _policy_from_json(payloads: Iterable[str]) -> PolicyRestrictions:
    weekdays = frozenset()
    start = None
    end = None
    requires_reservation = False
    max_guests = None
    for raw in payloads:
        try:
            data = json.loads(raw or "{}")
        except (TypeError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        if "allowed_weekdays" in data:
            weekdays = frozenset(int(v) for v in data.get("allowed_weekdays") or [])
        if "start_time" in data:
            start = _parse_time(data.get("start_time"))
        if "end_time" in data:
            end = _parse_time(data.get("end_time"))
        if "requires_reservation" in data:
            requires_reservation = bool(data.get("requires_reservation"))
        if "max_guests" in data:
            value = data.get("max_guests")
            max_guests = None if value is None else int(value)
    return PolicyRestrictions(
        allowed_weekdays=weekdays,
        start_time=start,
        end_time=end,
        requires_reservation=requires_reservation,
        max_guests=max_guests,
    )


class CavasCorporativasRepository:
    def __init__(self, connection_factory: Optional[Callable[[], object]] = None):
        self._connection_factory = connection_factory or _default_connection_factory

    def find_active_authorized(
        self, identidad_fuente: str, identidad_referencia: str, occurred_at: datetime
    ) -> Optional[AuthorizedReference]:
        conn = self._connection_factory()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT TOP 1 CAST(a.AutorizadoID AS varchar(36)) AS autorizado_id,
                             CAST(a.ConvenioID AS varchar(36)) AS convenio_id
                FROM dbo.CavasCorporativas_Autorizados a
                INNER JOIN dbo.CavasCorporativas_Convenios c ON c.ConvenioID=a.ConvenioID
                WHERE a.IdentidadFuente=%s AND a.IdentidadReferencia=%s
                  AND a.Activo=1 AND c.Activo=1
                  AND c.Estado='ACTIVO'
                  AND (a.VigenciaDesde IS NULL OR a.VigenciaDesde<=%s)
                  AND (a.VigenciaHasta IS NULL OR a.VigenciaHasta>=%s)
                  AND c.VigenciaDesde<=%s
                  AND (c.VigenciaHasta IS NULL OR c.VigenciaHasta>=%s)
                ORDER BY c.VigenciaDesde DESC, a.CreatedAt DESC
                """,
                (identidad_fuente, identidad_referencia, occurred_at, occurred_at, occurred_at, occurred_at),
            )
            row = cur.fetchone()
            if not row:
                return None
            return AuthorizedReference(str(row["autorizado_id"]), str(row["convenio_id"]))
        finally:
            conn.close()

    def load_benefit_rules(self, convenio_id: str) -> list[BenefitRule]:
        conn = self._connection_factory()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT CAST(b.BeneficioID AS varchar(36)) AS beneficio_id, b.TipoBeneficio,
                       b.Activo, b.VigenciaDesde, b.VigenciaHasta
                FROM dbo.CavasCorporativas_Beneficios b
                WHERE b.ConvenioID=%s AND b.Activo=1
                ORDER BY b.Prioridad ASC, b.CodigoBeneficio ASC
                """,
                (convenio_id,),
            )
            benefits = list(cur.fetchall() or [])
            rules: list[BenefitRule] = []
            for benefit in benefits:
                benefit_id = str(benefit["beneficio_id"])
                cur.execute(
                    """
                    SELECT UnidadReferencia, LineaComercialCodigo, NivelDetalle, ReferenciaDetalle
                    FROM dbo.CavasCorporativas_BeneficioAlcances
                    WHERE BeneficioID=%s AND Incluido=1
                    """,
                    (benefit_id,),
                )
                scope_rows = list(cur.fetchall() or [])
                units = frozenset(str(r["UnidadReferencia"]) for r in scope_rows if r.get("UnidadReferencia"))
                scopes = []
                for row in scope_rows:
                    level = str(row["NivelDetalle"]).upper()
                    ref = row.get("ReferenciaDetalle")
                    if level == "LINEA":
                        ref = row.get("LineaComercialCodigo")
                    mapping = {
                        "LINEA": ScopeKind.SALES_LINE,
                        "CATEGORIA": ScopeKind.CATEGORY,
                        "FAMILIA": ScopeKind.FAMILY,
                        "SKU": ScopeKind.SKU,
                    }
                    if level in mapping and ref:
                        scopes.append(BenefitScope(mapping[level], str(ref)))
                cur.execute(
                    """
                    SELECT ConfiguracionJson
                    FROM dbo.CavasCorporativas_Politicas
                    WHERE ConvenioID=%s AND Activa=1 AND (BeneficioID IS NULL OR BeneficioID=%s)
                    ORDER BY CASE WHEN BeneficioID IS NULL THEN 0 ELSE 1 END, Prioridad ASC
                    """,
                    (convenio_id, benefit_id),
                )
                policy_json = [str(r["ConfiguracionJson"]) for r in (cur.fetchall() or [])]
                kind = BenefitKind(str(benefit["TipoBeneficio"]))
                valid_from = benefit.get("VigenciaDesde")
                valid_to = benefit.get("VigenciaHasta")
                rules.append(BenefitRule(
                    benefit_id=benefit_id,
                    kind=kind,
                    active=bool(benefit["Activo"]),
                    valid_from=valid_from.date() if valid_from else None,
                    valid_to=valid_to.date() if valid_to else None,
                    unit_references=units,
                    scopes=tuple(scopes),
                    restrictions=_policy_from_json(policy_json),
                ))
            return rules
        finally:
            conn.close()

    def application_exists(
        self, beneficio_id: str, unidad_referencia: str, operacion_tipo: str, operacion_referencia: str
    ) -> bool:
        conn = self._connection_factory()
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT 1 FROM dbo.CavasCorporativas_AplicacionesBeneficio
                WHERE BeneficioID=%s AND UnidadReferencia=%s AND OperacionTipo=%s AND OperacionReferencia=%s""",
                (beneficio_id, unidad_referencia, operacion_tipo, operacion_referencia),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()

    def record_application(self, record: ApplicationRecord) -> bool:
        """Inserta una aplicacion una sola vez. True=insertada, False=ya existia."""
        conn = self._connection_factory()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM dbo.CavasCorporativas_AplicacionesBeneficio WITH (UPDLOCK, HOLDLOCK)
                    WHERE BeneficioID=%s AND UnidadReferencia=%s AND OperacionTipo=%s AND OperacionReferencia=%s
                )
                BEGIN
                    INSERT INTO dbo.CavasCorporativas_AplicacionesBeneficio
                    (ConvenioID, BeneficioID, AutorizadoID, UnidadReferencia, OperacionTipo, OperacionReferencia,
                     EventoTemporalTipo, EventoTemporalUtc, ImporteBase, ImporteBeneficio, MonedaCodigo,
                     EvaluacionJson, AppliedByReferencia)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                    SELECT CAST(1 AS int);
                END
                ELSE SELECT CAST(0 AS int);
                """,
                (record.beneficio_id, record.unidad_referencia, record.operacion_tipo, record.operacion_referencia,
                 record.convenio_id, record.beneficio_id, record.autorizado_id, record.unidad_referencia,
                 record.operacion_tipo, record.operacion_referencia, record.evento_temporal_tipo,
                 record.evento_temporal_utc, record.importe_base, record.importe_beneficio, record.moneda_codigo,
                 json.dumps(record.evaluacion, ensure_ascii=False, sort_keys=True) if record.evaluacion is not None else None,
                 record.applied_by_referencia),
            )
            row = cur.fetchone()
            inserted = bool(row and int(row[0]) == 1)
            conn.commit()
            return inserted
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
