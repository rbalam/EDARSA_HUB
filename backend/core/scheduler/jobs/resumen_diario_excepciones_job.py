"""
EDARSA HUB - Job Resumen Diario Ejecutivo de Excepciones
=========================================================
Envía cada mañana (cron parametrizable) UN correo a dirección con el conteo de
excepciones por unidad y por severidad. NO-LIVE (motor canónico SQL), sin hardcode.

Variables .env:
- SCHEDULER_RESUMEN_DIARIO_EXC_ENABLED / _CRON  (leídas en config.py)
- ALERT_EMAIL_TO / dbo.Sistema_AlertasDestinatarios  (destinatarios, reutilizados)
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def _build_resumen_html(por_unidad: List[Dict[str, Any]], totales: Dict[str, int]) -> str:
    filas = ""
    for u in por_unidad:
        filas += (
            f"<tr>"
            f"<td style='padding:8px;border-bottom:1px solid #e4e4e7;'>{u['unidad']}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #e4e4e7;text-align:center;color:#DC2626;font-weight:600;'>{u['criticas']}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #e4e4e7;text-align:center;color:#EA580C;font-weight:600;'>{u['altas']}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #e4e4e7;text-align:center;'>{u['total']}</td>"
            f"</tr>"
        )
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto;">
      <h2 style="color:#18181b;">Resumen Diario de Excepciones — EDARSA HUB</h2>
      <p style="color:#71717a;">{datetime.now(timezone.utc).strftime('%d/%m/%Y')} · Total:
        <b style="color:#DC2626;">{totales.get('criticas',0)} críticas</b>,
        <b style="color:#EA580C;">{totales.get('altas',0)} altas</b>
        ({totales.get('total',0)} en total)</p>
      <table style="width:100%;border-collapse:collapse;margin-top:12px;">
        <thead>
          <tr style="background:#f4f4f5;">
            <th style="padding:8px;text-align:left;">Unidad</th>
            <th style="padding:8px;text-align:center;">Críticas</th>
            <th style="padding:8px;text-align:center;">Altas</th>
            <th style="padding:8px;text-align:center;">Total</th>
          </tr>
        </thead>
        <tbody>{filas or '<tr><td colspan=4 style="padding:12px;text-align:center;color:#71717a;">Sin excepciones hoy 🎉</td></tr>'}</tbody>
      </table>
      <p style="color:#a1a1aa;font-size:12px;margin-top:16px;">Mensaje automático del Centro de Control EDARSA HUB.</p>
    </div>
    """


async def execute_resumen_diario_excepciones() -> Dict[str, Any]:
    """Calcula el resumen por unidad y lo envía por correo a dirección."""
    resultado = {"total": 0, "unidades": 0, "email_enviado": False, "errores": []}

    try:
        from modules.alertas_estrategicas.routes import resumen_alertas
        data = await resumen_alertas(server_id="", limite=1000, current_user={})
        alertas = data.get("alertas", []) if isinstance(data, dict) else []
    except Exception as e:
        logger.error(f"[RESUMEN_DIARIO_EXC] Error obteniendo excepciones: {e}")
        resultado["errores"].append(str(e))
        return resultado

    # Agrupar por unidad
    agrup: Dict[str, Dict[str, int]] = {}
    tot = {"criticas": 0, "altas": 0, "total": 0}
    for a in alertas:
        unidad = a.get("unidad") or a.get("server_id") or "N/D"
        sev = (a.get("severidad") or "").upper()
        g = agrup.setdefault(unidad, {"criticas": 0, "altas": 0, "total": 0})
        if sev == "CRITICA":
            g["criticas"] += 1; tot["criticas"] += 1
        elif sev == "ALTA":
            g["altas"] += 1; tot["altas"] += 1
        g["total"] += 1; tot["total"] += 1

    por_unidad = [
        {"unidad": k, **v} for k, v in sorted(agrup.items(), key=lambda x: -x[1]["total"])
    ]
    resultado["total"] = tot["total"]
    resultado["unidades"] = len(por_unidad)

    # Enviar correo (reutiliza el provider SMTP y sus destinatarios canónicos)
    try:
        from core.centro_control.email_notifications import (
            get_email_recipients, _send_email_sync, EMAIL_ENABLED,
        )
        import asyncio
        recipients = get_email_recipients()
        if not EMAIL_ENABLED or not recipients:
            resultado["errores"].append("email deshabilitado o sin destinatarios")
            return resultado

        subject = f"[Resumen Diario] {tot['criticas']} críticas / {tot['altas']} altas — EDARSA HUB"
        html = _build_resumen_html(por_unidad, tot)
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(None, _send_email_sync, r, subject, html, "Resumen diario de excepciones EDARSA HUB.")
            for r in recipients
        ]
        res = await asyncio.gather(*tasks, return_exceptions=True)
        enviados = sum(1 for x in res if isinstance(x, dict) and x.get("success"))
        resultado["email_enviado"] = enviados > 0
        if not enviados:
            resultado["errores"].append("no se pudo enviar a ningún destinatario")
        logger.info(f"[RESUMEN_DIARIO_EXC] Enviado a {enviados}/{len(recipients)} destinatarios")
    except Exception as e:
        logger.error(f"[RESUMEN_DIARIO_EXC] Error email: {e}")
        resultado["errores"].append(str(e))

    return resultado
