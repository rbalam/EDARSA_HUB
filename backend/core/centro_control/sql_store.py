"""Persistencia SQL canónica para Centro de Control.

P2B usa únicamente estructuras certificadas en Gate 2 P2A-R2:
- dbo.Alertas_Sistema
- dbo.Scheduler_BitacoraJobs
No crea tablas y no consulta fuentes LIVE.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.sql_first.connection_factory import get_edarsahub_pymssql_connection


EVENT_JOB = "CENTRO_CONTROL_EVENT"
BITACORA_JOB = "CENTRO_CONTROL_BITACORA"
ALERT_PREFIX = "alrt_"


def _conn():
    return get_edarsahub_pymssql_connection(autocommit=False)


def _fetchall(sql: str, params: tuple = ()):
    conn = _conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def _fetchone(sql: str, params: tuple = ()):
    rows = _fetchall(sql, params)
    return rows[0] if rows else None


def _execute(sql: str, params: tuple = ()):
    conn = _conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def _now_id(prefix: str) -> str:
    return f"{prefix}{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:18]}"


def _dt(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def create_alert(titulo: str, modulo: str, severidad: str, detalle: str) -> Dict[str, Any]:
    alert_id = _now_id(ALERT_PREFIX)
    _execute(
        """
        INSERT INTO dbo.Alertas_Sistema
            (AlertaID, Tipo, Severidad, Titulo, Mensaje, Modulo, FechaCreacion, DatosJSON, AccionSugerida, Acknowledged)
        VALUES (%s, %s, %s, %s, %s, %s, SYSUTCDATETIME(), %s, %s, 0)
        """,
        (alert_id, "CENTRO_CONTROL", severidad, titulo, detalle, modulo, json.dumps({}, ensure_ascii=False), None),
    )
    return {
        "id": alert_id, "timestamp": datetime.now(timezone.utc).isoformat(),
        "titulo": titulo, "modulo": modulo, "severidad": severidad,
        "detalle": detalle, "reconocida": False, "reconocida_por": None,
        "reconocida_at": None,
    }


def list_alerts(active_only: bool = True, limit: int = 20) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    where = "AND ISNULL(Acknowledged,0)=0" if active_only else ""
    rows = _fetchall(f"""
        SELECT TOP {limit} AlertaID, Severidad, Titulo, Mensaje, Modulo, FechaCreacion,
               Acknowledged, AcknowledgedBy, AcknowledgedAt, DatosJSON
        FROM dbo.Alertas_Sistema
        WHERE AlertaID LIKE %s {where}
        ORDER BY FechaCreacion DESC, ID DESC
    """, (f"{ALERT_PREFIX}%",))
    return [{
        "id": r.get("AlertaID"), "timestamp": _dt(r.get("FechaCreacion")),
        "titulo": r.get("Titulo"), "modulo": r.get("Modulo"),
        "severidad": r.get("Severidad"), "detalle": r.get("Mensaje"),
        "reconocida": bool(r.get("Acknowledged")),
        "reconocida_por": r.get("AcknowledgedBy"),
        "reconocida_at": _dt(r.get("AcknowledgedAt")),
    } for r in rows]


def active_alert_count() -> int:
    row = _fetchone("SELECT COUNT(*) AS total FROM dbo.Alertas_Sistema WHERE AlertaID LIKE %s AND ISNULL(Acknowledged,0)=0", (f"{ALERT_PREFIX}%",))
    return int((row or {}).get("total") or 0)


def acknowledge_alert(alert_id: str, email: Optional[str], comentario: Optional[str]) -> Optional[Dict[str, Any]]:
    existing = _fetchone("SELECT AlertaID FROM dbo.Alertas_Sistema WHERE AlertaID=%s AND AlertaID LIKE %s", (alert_id, f"{ALERT_PREFIX}%"))
    if not existing:
        return None
    datos = json.dumps({"comentario_ack": comentario} if comentario else {}, ensure_ascii=False)
    _execute("""
        UPDATE dbo.Alertas_Sistema
        SET Acknowledged=1, AcknowledgedBy=%s, AcknowledgedAt=SYSUTCDATETIME(), DatosJSON=%s
        WHERE AlertaID=%s
    """, (email, datos, alert_id))
    rows = list_alerts(active_only=False, limit=100)
    return next((r for r in rows if r.get("id") == alert_id), None)


def record_event(tipo: str, modulo: str, mensaje: str, severidad: str = "info", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    event_id = _now_id("evt_")
    details = json.dumps({"mensaje": mensaje, "severidad": severidad, "data": data or {}}, ensure_ascii=False, default=str)
    _execute("""
        INSERT INTO dbo.Scheduler_BitacoraJobs
            (JobName, RunID, Accion, FechaAccion, ServerID, DetallesJSON, Exito, MensajeError)
        VALUES (%s, %s, %s, SYSUTCDATETIME(), %s, %s, %s, %s)
    """, (EVENT_JOB, event_id, tipo[:50], (modulo or "sistema")[:50], details, 0 if severidad == "critical" and tipo == "error" else 1, mensaje[:1000] if tipo == "error" else None))
    return {"id": event_id, "timestamp": datetime.now(timezone.utc).isoformat(), "tipo": tipo, "modulo": modulo, "mensaje": mensaje, "severidad": severidad, "data": data or {}}


def list_events(limit: int = 50, tipo: Optional[str] = None, modulo: Optional[str] = None) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit), 200))
    sql = f"SELECT TOP {limit} RunID, Accion, FechaAccion, ServerID, DetallesJSON FROM dbo.Scheduler_BitacoraJobs WHERE JobName=%s"
    params: List[Any] = [EVENT_JOB]
    if tipo:
        sql += " AND Accion=%s"; params.append(tipo)
    if modulo:
        sql += " AND ServerID=%s"; params.append(modulo)
    sql += " ORDER BY FechaAccion DESC, ID DESC"
    rows = _fetchall(sql, tuple(params))
    out = []
    for r in rows:
        try: payload = json.loads(r.get("DetallesJSON") or "{}")
        except Exception: payload = {}
        out.append({"id": r.get("RunID"), "timestamp": _dt(r.get("FechaAccion")), "tipo": r.get("Accion"), "modulo": r.get("ServerID"), "mensaje": payload.get("mensaje"), "severidad": payload.get("severidad", "info"), "data": payload.get("data") or {}})
    return out


def record_bitacora(tipo: str, modulo: str, descripcion: str, impacto: Optional[str], autor: Optional[str], referencias: List[str], registrado_por: Optional[str]) -> Dict[str, Any]:
    entry_id = _now_id("btc_")
    payload = {"descripcion": descripcion, "impacto": impacto, "autor": autor, "referencias": referencias, "registrado_por": registrado_por}
    _execute("""
        INSERT INTO dbo.Scheduler_BitacoraJobs
            (JobName, RunID, Accion, FechaAccion, ServerID, DetallesJSON, Exito, MensajeError)
        VALUES (%s, %s, %s, SYSUTCDATETIME(), %s, %s, 1, NULL)
    """, (BITACORA_JOB, entry_id, tipo[:50], (modulo or "sistema")[:50], json.dumps(payload, ensure_ascii=False, default=str)))
    return {"id": entry_id, "timestamp": datetime.now(timezone.utc).isoformat(), "tipo": tipo, "modulo": modulo, **payload}


def list_bitacora(limit: int = 50, tipo: Optional[str] = None, modulo: Optional[str] = None) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit), 200))
    sql = f"SELECT TOP {limit} RunID, Accion, FechaAccion, ServerID, DetallesJSON FROM dbo.Scheduler_BitacoraJobs WHERE JobName=%s"
    params: List[Any] = [BITACORA_JOB]
    if tipo:
        sql += " AND Accion=%s"; params.append(tipo)
    if modulo:
        sql += " AND ServerID=%s"; params.append(modulo)
    sql += " ORDER BY FechaAccion DESC, ID DESC"
    rows = _fetchall(sql, tuple(params))
    out = []
    for r in rows:
        try: payload = json.loads(r.get("DetallesJSON") or "{}")
        except Exception: payload = {}
        out.append({"id": r.get("RunID"), "timestamp": _dt(r.get("FechaAccion")), "tipo": r.get("Accion"), "modulo": r.get("ServerID"), **payload})
    return out


def latest_event_timestamp(tipo: str) -> Optional[str]:
    row = _fetchone("SELECT MAX(FechaAccion) AS ts FROM dbo.Scheduler_BitacoraJobs WHERE JobName=%s AND Accion=%s", (EVENT_JOB, tipo))
    return _dt((row or {}).get("ts"))


def bitacora_summary() -> Dict[str, Any]:
    row = _fetchone("SELECT COUNT(*) AS total, MAX(FechaAccion) AS ultimo FROM dbo.Scheduler_BitacoraJobs WHERE JobName=%s", (BITACORA_JOB,)) or {}
    return {"entradas_recientes": int(row.get("total") or 0), "ultimo_cambio": _dt(row.get("ultimo"))}


def metrics() -> Dict[str, Any]:
    checks = _fetchone("SELECT COUNT(*) AS total, MIN(FechaAccion) AS inicio, MAX(FechaAccion) AS ultima FROM dbo.Scheduler_BitacoraJobs WHERE JobName=%s AND Accion='regression_check'", (EVENT_JOB,)) or {}
    alerts = _fetchone("SELECT COUNT(*) AS total, SUM(CASE WHEN ISNULL(Acknowledged,0)=1 THEN 1 ELSE 0 END) AS ack FROM dbo.Alertas_Sistema WHERE AlertaID LIKE %s", (f"{ALERT_PREFIX}%",)) or {}
    total_checks = int(checks.get("total") or 0)
    alert_total = int(alerts.get("total") or 0)
    alert_ack = int(alerts.get("ack") or 0)
    start = checks.get("inicio")
    uptime = round((datetime.now(timezone.utc).replace(tzinfo=None) - start).total_seconds()/3600, 2) if start else 0.0
    # P2B-R2: Scheduler_BitacoraJobs certifica que hubo una ejecución, pero no
    # contiene el resultado granular necesario para afirmar cuántos checks pasaron.
    # Por contrato de verdad, esos KPIs quedan NULL hasta tener evidencia canónica.
    tasa_ack = (alert_ack / alert_total * 100) if alert_total else None
    return {
        "uptime_horas": uptime,
        "checks_ejecutados": total_checks,
        "checks_exitosos": None,
        "alertas_generadas": alert_total,
        "alertas_reconocidas": alert_ack,
        "ultima_regresion": _dt(checks.get("ultima")),
        "inicio_monitoreo": _dt(start),
        "tasa_exito_checks": None,
        "tasa_alertas_reconocidas": round(tasa_ack, 1) if tasa_ack is not None else None,
        "score_estabilidad": None,
        "metricas_calidad": "INSUFFICIENT_CANONICAL_CHECK_RESULT_EVIDENCE",
    }


def blindaje_registry_status() -> Dict[str, Any]:
    # P2A-R2 no certificó una tabla exacta que sea el registro canónico de blindaje.
    # Un nombre parecido no constituye evidencia. No usar LIKE/sys.tables para inferirlo.
    return {
        "source": "EDARSAHUB_SQL",
        "status": "NO_CANONICAL_SQL_REGISTRY",
        "registry_tables": [],
        "registry_evidence": "P2A_R2_NO_EXPLICIT_REGISTRY_CERTIFIED",
        "modulos": [],
    }
