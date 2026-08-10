"""
EDARSA HUB - Job Notificador de Excepciones Críticas
=====================================================
Revisa periódicamente las excepciones estratégicas (rentabilidad, compras sin
detalle, etc.) provenientes del MISMO motor que /api/alertas-estrategicas/resumen
(NO-LIVE, tablas canónicas SQL) y notifica las NUEVAS por WhatsApp (Twilio) y
Correo (SMTP).

Reglas duras:
- CERO hardcode: destinatarios, severidades e intervalo vienen del .env.
- NO MongoDB: el estado de notificación se persiste en dbo.Sistema_Excepciones_Estado.
- Anti-spam: cada excepción se notifica UNA sola vez (NotificadoCanales). Si se
  marca como REVISADA o desaparece, deja de molestar; si reaparece una nueva, avisa.

Variables .env:
- ALERTAS_EXCEPCIONES_SEVERIDADES  (ej. "CRITICA,ALTA")
- ALERT_EMAIL_TO / ALERT_WHATSAPP_TO  (destinatarios, ya usados por los servicios)
- SCHEDULER_ALERTAS_EXCEPCIONES_ENABLED / _INTERVAL_SECONDS  (leídos en config.py)
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from core.config.edarsahub_sql import get_edarsahub_connection

logger = logging.getLogger(__name__)


def _severidades_configuradas() -> List[str]:
    """Lee del .env las severidades que disparan notificación (sin hardcode)."""
    raw = os.environ.get("ALERTAS_EXCEPCIONES_SEVERIDADES", "CRITICA,ALTA")
    return [s.strip().upper() for s in raw.split(",") if s.strip()]


def _excepcion_key(a: Dict[str, Any]) -> str:
    """Mismo formato de llave que usa /sistema/pendientes-unificados y revisar."""
    ident = a.get("entidad_id") or a.get("entidad_codigo") or a.get("server_id")
    return f"{a.get('tipo_alerta', 'EXC')}-{ident}"


def _keys_ya_gestionadas() -> set:
    """Devuelve llaves ya REVISADAS o ya NOTIFICADAS (para no repetir)."""
    keys = set()
    try:
        cn = get_edarsahub_connection()
        cur = cn.cursor()
        cur.execute(
            """IF OBJECT_ID('dbo.Sistema_Excepciones_Estado','U') IS NOT NULL
               SELECT ExcepcionKey FROM dbo.Sistema_Excepciones_Estado
               WHERE Estado = 'REVISADA' OR NotificadoCanales IS NOT NULL"""
        )
        keys = set((r[0] or "") for r in (cur.fetchall() or []))
        cn.close()
    except Exception as e:
        logger.warning(f"[ALERTAS_EXC] No se pudieron leer llaves gestionadas: {e}")
    return keys


def obtener_excepciones_revisadas() -> set:
    """Devuelve llaves marcadas explícitamente como REVISADA."""
    conn = get_edarsahub_connection()

    try:
        cur = conn.cursor()
        cur.execute(
            """IF OBJECT_ID('dbo.Sistema_Excepciones_Estado','U') IS NOT NULL
               SELECT ExcepcionKey
               FROM dbo.Sistema_Excepciones_Estado
               WHERE Estado = 'REVISADA'"""
        )
        return {
            (row[0] or "")
            for row in (cur.fetchall() or [])
            if row and row[0]
        }
    finally:
        conn.close()


def marcar_excepcion_revisada_estado(
    key: str,
    titulo: str | None,
    server_id: str | None,
    revisado_por: str,
) -> None:
    """Persiste el estado REVISADA de una excepción estratégica."""
    if not key:
        raise ValueError("key requerido")

    conn = get_edarsahub_connection()

    try:
        cur = conn.cursor()
        cur.execute(
            """MERGE dbo.Sistema_Excepciones_Estado AS t
               USING (SELECT %s AS k) AS s
                  ON t.ExcepcionKey = s.k
               WHEN MATCHED THEN
                   UPDATE SET
                       Estado = 'REVISADA',
                       Titulo = %s,
                       ServerID = %s,
                       RevisadoPor = %s,
                       FechaRevision = SYSUTCDATETIME()
               WHEN NOT MATCHED THEN
                   INSERT (
                       ExcepcionKey,
                       Estado,
                       Titulo,
                       ServerID,
                       RevisadoPor
                   )
                   VALUES (
                       %s,
                       'REVISADA',
                       %s,
                       %s,
                       %s
                   );""",
            (
                key,
                titulo,
                server_id,
                revisado_por,
                key,
                titulo,
                server_id,
                revisado_por,
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _marcar_notificada(key: str, titulo: str, server_id: str, canales: str):
    """Persiste en SQL que la excepción ya fue notificada (idempotente vía MERGE)."""
    try:
        cn = get_edarsahub_connection()
        cur = cn.cursor()
        cur.execute(
            """MERGE dbo.Sistema_Excepciones_Estado AS t
               USING (SELECT %s AS k) AS s ON t.ExcepcionKey = s.k
               WHEN MATCHED THEN UPDATE SET NotificadoCanales=%s, FechaNotificacion=SYSUTCDATETIME(),
                    Titulo=COALESCE(t.Titulo,%s), ServerID=COALESCE(t.ServerID,%s)
               WHEN NOT MATCHED THEN INSERT (ExcepcionKey, Estado, Titulo, ServerID, NotificadoCanales, FechaNotificacion)
                    VALUES (%s, 'PENDIENTE', %s, %s, %s, SYSUTCDATETIME());""",
            (key, canales, titulo, server_id, key, titulo, server_id, canales),
        )
        cn.commit()
        cn.close()
    except Exception as e:
        logger.error(f"[ALERTAS_EXC] No se pudo marcar notificada {key}: {e}")


def _build_digest_alerta(nuevas: List[Dict[str, Any]], severidades: List[str]) -> Dict[str, Any]:
    """Construye una única 'alerta' resumen (digest) para el envío."""
    total = len(nuevas)
    top_sev = "CRITICA" if any(x.get("severidad") == "CRITICA" for x in nuevas) else (severidades[0] if severidades else "ALTA")
    lineas = []
    for a in nuevas[:25]:
        lineas.append(
            f"• [{a.get('severidad')}] {a.get('tipo_alerta')} — "
            f"{(a.get('descripcion') or a.get('entidad_codigo') or '').strip()[:80]} "
            f"(Unidad: {a.get('unidad') or a.get('server_id') or 'N/D'})"
        )
    if total > 25:
        lineas.append(f"… y {total - 25} más.")
    detalle = (
        f"Se detectaron {total} excepción(es) comercial(es) nueva(s) "
        f"(severidades: {', '.join(severidades)}) que requieren atención directiva:\n\n"
        + "\n".join(lineas)
    )
    return {
        "id": f"exc_digest_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "titulo": f"{total} excepción(es) crítica(s) nueva(s) detectada(s)",
        "severidad": top_sev.lower(),
        "modulo": "Alertas Estratégicas",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detalle": detalle,
    }


async def execute_alertas_excepciones_notifier() -> Dict[str, Any]:
    """
    Ejecuta la revisión y notificación de excepciones críticas nuevas.
    Devuelve un resumen del resultado (para bitácora del scheduler).
    """
    resultado = {
        "severidades": _severidades_configuradas(),
        "total_evaluadas": 0,
        "nuevas": 0,
        "notificadas": 0,
        "email_enviado": False,
        "whatsapp_enviado": False,
        "errores": [],
    }
    severidades = resultado["severidades"]

    # 1) Obtener excepciones desde el motor canónico (NO-LIVE)
    try:
        from modules.alertas_estrategicas.routes import resumen_alertas
        data = await resumen_alertas(server_id="", limite=500, current_user={})
        alertas = data.get("alertas", []) if isinstance(data, dict) else []
    except Exception as e:
        logger.error(f"[ALERTAS_EXC] Error obteniendo excepciones: {e}")
        resultado["errores"].append(f"resumen_alertas: {e}")
        return resultado

    # 2) Filtrar por severidad configurada
    criticas = [a for a in alertas if (a.get("severidad") or "").upper() in severidades]
    resultado["total_evaluadas"] = len(criticas)

    # 3) Descartar las ya revisadas o ya notificadas
    gestionadas = _keys_ya_gestionadas()
    nuevas = []
    for a in criticas:
        key = _excepcion_key(a)
        if key in gestionadas:
            continue
        a["_key"] = key
        nuevas.append(a)

    resultado["nuevas"] = len(nuevas)
    if not nuevas:
        logger.info("[ALERTAS_EXC] Sin excepciones nuevas por notificar")
        return resultado

    # 4) Enviar digest por Email y WhatsApp
    digest = _build_digest_alerta(nuevas, severidades)
    canales_ok = []

    try:
        from core.centro_control.email_notifications import send_critical_alert_email
        r_email = await send_critical_alert_email(digest)
        resultado["email_enviado"] = bool(r_email.get("success"))
        if r_email.get("success"):
            canales_ok.append("email")
        elif r_email.get("message"):
            resultado["errores"].append(f"email: {r_email.get('message')}")
    except Exception as e:
        logger.error(f"[ALERTAS_EXC] Error email: {e}")
        resultado["errores"].append(f"email: {e}")

    try:
        from core.centro_control.whatsapp_notifications import send_critical_alert_whatsapp
        r_wa = await send_critical_alert_whatsapp(digest)
        resultado["whatsapp_enviado"] = bool(r_wa.get("success"))
        if r_wa.get("success"):
            canales_ok.append("whatsapp")
        elif r_wa.get("message"):
            resultado["errores"].append(f"whatsapp: {r_wa.get('message')}")
    except Exception as e:
        logger.error(f"[ALERTAS_EXC] Error whatsapp: {e}")
        resultado["errores"].append(f"whatsapp: {e}")

    # 5) Marcar como notificadas SOLO si al menos un canal tuvo éxito
    if canales_ok:
        canales_str = ",".join(canales_ok)
        for a in nuevas:
            _marcar_notificada(
                a["_key"],
                (a.get("descripcion") or a.get("tipo_alerta") or "")[:200],
                str(a.get("server_id") or ""),
                canales_str,
            )
            resultado["notificadas"] += 1
        logger.info(
            f"[ALERTAS_EXC] {resultado['notificadas']} excepciones notificadas por {canales_str}"
        )
    else:
        logger.warning("[ALERTAS_EXC] Ningún canal envió; no se marcan como notificadas (se reintentará)")

    return resultado


async def _obtener_excepciones_por_severidad() -> List[Dict[str, Any]]:
    """Devuelve las excepciones actuales filtradas por las severidades configuradas."""
    severidades = _severidades_configuradas()
    from modules.alertas_estrategicas.routes import resumen_alertas
    data = await resumen_alertas(server_id="", limite=500, current_user={})
    alertas = data.get("alertas", []) if isinstance(data, dict) else []
    return [a for a in alertas if (a.get("severidad") or "").upper() in severidades]


async def silenciar_backlog_excepciones() -> Dict[str, Any]:
    """
    Marca TODAS las excepciones actuales (según severidades configuradas) como ya
    notificadas, para que el primer aviso real solo traiga las NUEVAS de aquí en adelante.
    """
    criticas = await _obtener_excepciones_por_severidad()
    ya = _keys_ya_gestionadas()
    silenciadas = 0
    for a in criticas:
        key = _excepcion_key(a)
        if key in ya:
            continue
        _marcar_notificada(
            key,
            (a.get("descripcion") or a.get("tipo_alerta") or "")[:200],
            str(a.get("server_id") or ""),
            "backlog_inicial",
        )
        silenciadas += 1
    logger.info(f"[ALERTAS_EXC] Backlog silenciado: {silenciadas} excepciones pre-marcadas")
    return {"total_evaluadas": len(criticas), "silenciadas": silenciadas}


async def enviar_prueba_canales() -> Dict[str, Any]:
    """
    Envía un mensaje de PRUEBA por Email y WhatsApp a los destinatarios configurados
    para validar la conectividad al instante (no toca el estado de las excepciones).
    """
    from core.centro_control.email_notifications import send_critical_alert_email
    from core.centro_control.whatsapp_notifications import send_critical_alert_whatsapp
    prueba = {
        "id": f"prueba_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "titulo": "Prueba de Notificador de Excepciones",
        "severidad": "medium",
        "modulo": "Alertas Estratégicas",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detalle": "Mensaje de prueba del Notificador de Excepciones Críticas. Si lo recibes, el canal está operativo.",
    }
    out = {"email": {}, "whatsapp": {}}
    try:
        out["email"] = await send_critical_alert_email(prueba)
    except Exception as e:
        out["email"] = {"success": False, "message": str(e)[:150]}
    try:
        out["whatsapp"] = await send_critical_alert_whatsapp(prueba)
    except Exception as e:
        out["whatsapp"] = {"success": False, "message": str(e)[:150]}
    return {
        "email_enviado": bool(out["email"].get("success")),
        "email_mensaje": out["email"].get("message"),
        "whatsapp_enviado": bool(out["whatsapp"].get("success")),
        "whatsapp_mensaje": out["whatsapp"].get("message"),
    }
