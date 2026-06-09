"""
Reporteador BI — Informe Gerencial MECA MPRO (SQL-First, NO-LIVE).
====================================================================
Reconstrucción del tablero Power BI "Informe Gerencial MECA MPRO" (9 páginas)
sobre EDARSAHUB SQL. Reutiliza KPIs canónicos y clasificación canónica de producto.

Disponibilidad de datos en EDARSAHUB (auditado 2026-06-09):
- ✅ Ventas (detalle + KPIs diarios v2), por hora, por familia/clasificación, tickets.
- ⛔ NO sincronizados aún: Compras/Costos, Documentos_Capturados, Metas, Capacidad/Mesas,
  Vendedores, bandera de Ambientación. Esas páginas/medidas devuelven disponible=false
  con estado PENDIENTE_SINCRONIZACION (NO se inventan datos — regla NO-LIVE).

Fuente única: EDARSAHUB SQL. Prefijo: /api/reporteador-bi
"""
import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Query

# Reutiliza helpers canónicos del módulo de inteligencia (misma fuente SQL).
from modules.inteligencia_comercial.routes import (
    execute_query, normalizar_unidad, _resolver_rango,
    _real_top_productos, _real_clasificacion_nested, _real_tickets, _real_horario,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reporteador-bi", tags=["Reporteador BI (MECA MPRO)"])

_KPIS_VIEW = "vw_Comercial_KPIs_Diarios_v2_Runtime"

# Nota canónica para fuentes aún no sincronizadas a EDARSAHUB (NO-LIVE).
_NOTA_PENDIENTE = ("Esta sección depende de una fuente que aún NO está sincronizada en "
                   "EDARSAHUB SQL. Por la regla NO-LIVE no se consulta el POS en vivo ni se "
                   "inventan datos. Se habilitará al sincronizar la fuente origen.")

PAGINAS = [
    {"id": "analisis-ventas",   "nombre": "Análisis de Ventas",    "icono": "BarChart3",   "disponible": True},
    {"id": "ventas-semana",     "nombre": "Ventas por Semana",     "icono": "CalendarRange","disponible": True},
    {"id": "ventas-mes",        "nombre": "Ventas por Mes",        "icono": "CalendarDays", "disponible": True},
    {"id": "ambientacion",      "nombre": "Análisis Ambientación", "icono": "Music",        "disponible": True},
    {"id": "gastos",            "nombre": "Gastos / Costos",       "icono": "Wallet",       "disponible": False},
    {"id": "revision-tickets",  "nombre": "Revisión de Tickets",   "icono": "Receipt",      "disponible": True},
    {"id": "rotacion-mesas",    "nombre": "Rotación de Mesas",     "icono": "Armchair",     "disponible": False},
    {"id": "analisis-documentos","nombre": "Análisis de Documentos","icono": "FileText",    "disponible": False},
    {"id": "kpis-mes",          "nombre": "KPIs Mes Actual",       "icono": "Gauge",        "disponible": True},
]


def _u(unidad: Optional[str]) -> Optional[str]:
    return normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None


def _kwhere(unidad_db: Optional[str], fi: str, ff: str) -> str:
    parts = [f"fecha_operacion BETWEEN '{fi}' AND '{ff}'"]
    if unidad_db:
        parts.append(f"unidad_negocio_nombre = '{unidad_db}'")
    return " AND ".join(parts)


def _kpis_rango(unidad_db: Optional[str], fi: str, ff: str) -> Dict[str, float]:
    """KPIs canónicos del rango (ticket=ventas÷pax, cheque=ventas÷cuentas)."""
    rows = execute_query(f"""
        SELECT ISNULL(SUM(ventas_total),0) ventas, ISNULL(SUM(ventas_sin_propina),0) ventas_sp,
               ISNULL(SUM(propinas_total),0) propinas, ISNULL(SUM(tickets_total),0) cuentas,
               ISNULL(SUM(pax_total),0) pax
        FROM {_KPIS_VIEW} WHERE {_kwhere(unidad_db, fi, ff)}
    """)
    r = rows[0] if rows else {}
    ventas = float(r.get("ventas") or 0)
    ventas_sp = float(r.get("ventas_sp") or 0)
    cuentas = float(r.get("cuentas") or 0)
    pax = float(r.get("pax") or 0)
    return {
        "ventas": round(ventas, 2),
        "ventas_sin_propina": round(ventas_sp, 2),
        "propinas": round(float(r.get("propinas") or 0), 2),
        "cuentas": int(cuentas),
        "pax": int(pax),
        "ticket_promedio": round(ventas_sp / pax, 2) if pax else 0,
        "cheque_promedio": round(ventas_sp / cuentas, 2) if cuentas else 0,
    }


def _serie_diaria(unidad_db, fi, ff) -> List[Dict]:
    rows = execute_query(f"""
        SELECT fecha_operacion AS fecha, SUM(ventas_total) ventas, SUM(pax_total) pax,
               SUM(tickets_total) cuentas
        FROM {_KPIS_VIEW} WHERE {_kwhere(unidad_db, fi, ff)}
        GROUP BY fecha_operacion ORDER BY fecha_operacion
    """)
    return [{"fecha": str(r["fecha"])[:10], "ventas": round(float(r["ventas"] or 0), 2),
             "pax": int(r["pax"] or 0), "cuentas": int(r["cuentas"] or 0)} for r in rows]


def _envelope(disponible: bool, **extra) -> Dict[str, Any]:
    base = {"success": True, "disponible": disponible, "_source": "EDARSAHUB SQL (NO-LIVE)"}
    if not disponible:
        base["nota"] = _NOTA_PENDIENTE
    base.update(extra)
    return base


# ============================================================================
@router.get("/paginas")
async def listar_paginas():
    """Metadatos de las 9 páginas del reporteador (incluye disponibilidad)."""
    return {"success": True, "paginas": PAGINAS}


# ---- 1) ANÁLISIS DE VENTAS -------------------------------------------------
@router.get("/analisis-ventas")
async def analisis_ventas(unidad: Optional[str] = Query(None), periodo: Optional[str] = Query("mes"),
                          fecha_inicio: Optional[str] = Query(None), fecha_fin: Optional[str] = Query(None)):
    udb = _u(unidad)
    fi, ff, _, _, label = _resolver_rango(udb, periodo, fecha_inicio, fecha_fin)
    try:
        return _envelope(True,
            filtros={"fecha_inicio": fi, "fecha_fin": ff, "periodo": periodo, "periodo_label": label},
            kpis=_kpis_rango(udb, fi, ff),
            serie_diaria=_serie_diaria(udb, fi, ff),
            clasificacion=_real_clasificacion_nested(udb, fi, ff),
            top_productos=_real_top_productos(udb, fi, ff, limit=15),
        )
    except Exception as e:
        logger.error(f"[REPORTEADOR-BI] analisis-ventas: {e}")
        return {"success": False, "_error": str(e)}


# ---- 2) VENTAS POR SEMANA --------------------------------------------------
@router.get("/ventas-semana")
async def ventas_semana(unidad: Optional[str] = Query(None), periodo: Optional[str] = Query("anio"),
                        fecha_inicio: Optional[str] = Query(None), fecha_fin: Optional[str] = Query(None)):
    udb = _u(unidad)
    fi, ff, _, _, label = _resolver_rango(udb, periodo, fecha_inicio, fecha_fin)
    try:
        rows = execute_query(f"""
            SELECT YEAR(fecha_operacion) anio, DATEPART(ISO_WEEK, fecha_operacion) semana,
                   MIN(fecha_operacion) ini, MAX(fecha_operacion) fin,
                   SUM(ventas_total) ventas, SUM(pax_total) pax, SUM(tickets_total) cuentas
            FROM {_KPIS_VIEW} WHERE {_kwhere(udb, fi, ff)}
            GROUP BY YEAR(fecha_operacion), DATEPART(ISO_WEEK, fecha_operacion)
            ORDER BY anio, semana
        """)
        serie = []
        prev = None
        for r in rows:
            ventas = round(float(r["ventas"] or 0), 2)
            var = round((ventas - prev) / prev * 100, 1) if prev else None
            serie.append({"label": f"Sem {int(r['semana'])} ({str(r['ini'])[5:10]})",
                          "anio": int(r["anio"]), "semana": int(r["semana"]),
                          "ventas": ventas, "pax": int(r["pax"] or 0), "cuentas": int(r["cuentas"] or 0),
                          "var_vs_anterior": var})
            prev = ventas
        return _envelope(True,
            filtros={"fecha_inicio": fi, "fecha_fin": ff, "periodo": periodo, "periodo_label": label},
            kpis=_kpis_rango(udb, fi, ff), series=serie)
    except Exception as e:
        logger.error(f"[REPORTEADOR-BI] ventas-semana: {e}")
        return {"success": False, "_error": str(e)}


# ---- 3) VENTAS POR MES -----------------------------------------------------
@router.get("/ventas-mes")
async def ventas_mes(unidad: Optional[str] = Query(None), meses: int = Query(24, ge=3, le=48)):
    udb = _u(unidad)
    MESES_ES = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    try:
        where = "1=1" + (f" AND unidad_negocio_nombre = '{udb}'" if udb else "")
        rows = execute_query(f"""
            SELECT TOP {int(meses)} anio, mes, SUM(ventas_total) ventas, SUM(ventas_sin_propina) ventas_sp,
                   SUM(pax_total) pax, SUM(tickets_total) cuentas
            FROM {_KPIS_VIEW} WHERE {where}
            GROUP BY anio, mes ORDER BY anio DESC, mes DESC
        """)
        rows = list(reversed(rows))
        serie = []
        for r in rows:
            ventas = round(float(r["ventas"] or 0), 2)
            pax = int(r["pax"] or 0)
            cuentas = int(r["cuentas"] or 0)
            ventas_sp = float(r["ventas_sp"] or 0)
            serie.append({"anio": int(r["anio"]), "mes": int(r["mes"]),
                          "label": f"{MESES_ES[int(r['mes'])]} {int(r['anio'])}",
                          "ventas": ventas, "pax": pax, "cuentas": cuentas,
                          "ticket_promedio": round(ventas_sp / pax, 2) if pax else 0,
                          "cheque_promedio": round(ventas_sp / cuentas, 2) if cuentas else 0})
        # Comparativos mes actual vs anterior vs año anterior
        comp = {}
        if serie:
            act = serie[-1]
            ant = serie[-2] if len(serie) >= 2 else None
            ay = next((s for s in serie if s["anio"] == act["anio"] - 1 and s["mes"] == act["mes"]), None)
            comp = {
                "mes_actual": act,
                "var_mes_anterior": round((act["ventas"] - ant["ventas"]) / ant["ventas"] * 100, 1) if ant and ant["ventas"] else None,
                "var_anio_anterior": round((act["ventas"] - ay["ventas"]) / ay["ventas"] * 100, 1) if ay and ay["ventas"] else None,
            }
        return _envelope(True, series=serie, comparativos=comp)
    except Exception as e:
        logger.error(f"[REPORTEADOR-BI] ventas-mes: {e}")
        return {"success": False, "_error": str(e)}


# ---- 4) ANÁLISIS AMBIENTACIÓN (ventas por hora real; split de evento PENDIENTE) ----
@router.get("/ambientacion")
async def ambientacion(unidad: Optional[str] = Query(None), periodo: Optional[str] = Query("mes"),
                       fecha_inicio: Optional[str] = Query(None), fecha_fin: Optional[str] = Query(None)):
    udb = _u(unidad)
    fi, ff, _, _, label = _resolver_rango(udb, periodo, fecha_inicio, fecha_fin)
    try:
        # Ventas por hora del día (real, desde fecha_hora del detalle)
        rows = execute_query(f"""
            SELECT DATEPART(HOUR, d.fecha_hora) AS hora, SUM(d.importe_neto) ventas,
                   SUM(d.pax) pax, COUNT(DISTINCT d.numero_ticket) cuentas
            FROM Comercial_Inteligencia_VentasDetalleProducto d
            WHERE ISNULL(d.activo,1)=1 AND d.fecha_hora IS NOT NULL
              AND d.fecha_operacion BETWEEN '{fi}' AND '{ff}'
              {"AND d.unidad_negocio_nombre = '" + udb + "'" if udb else ""}
            GROUP BY DATEPART(HOUR, d.fecha_hora) ORDER BY hora
        """)
        por_hora = [{"hora": f"{int(r['hora']):02d}:00", "hora_num": int(r["hora"]),
                     "ventas": round(float(r["ventas"] or 0), 2), "pax": int(r["pax"] or 0),
                     "cuentas": int(r["cuentas"] or 0)} for r in rows]
        return _envelope(True,
            filtros={"fecha_inicio": fi, "fecha_fin": ff, "periodo": periodo, "periodo_label": label},
            ventas_por_hora=por_hora,
            ventas_por_turno=_real_horario(udb, fi, ff),
            ambientacion_evento={"disponible": False, "nota":
                "El desglose con/sin Ambientación (bandera de evento) no está sincronizado en EDARSAHUB. "
                "Se muestra la distribución horaria real como base."})
    except Exception as e:
        logger.error(f"[REPORTEADOR-BI] ambientacion: {e}")
        return {"success": False, "_error": str(e)}


# ---- 5) GASTOS / COSTOS (PENDIENTE: compras no sincronizadas) --------------
@router.get("/gastos")
async def gastos(unidad: Optional[str] = Query(None), periodo: Optional[str] = Query("mes")):
    return _envelope(False, fuente_requerida="COMPRAS_DETALLE / Compras (MPRO)",
                     medidas_pendientes=["%Costo", "Total Compras", "%Costo Piezas", "Costo vs Ventas"])


# ---- 6) REVISIÓN DE TICKETS (reutiliza reconstrucción de tickets) ----------
@router.get("/revision-tickets")
async def revision_tickets(unidad: Optional[str] = Query(None), periodo: Optional[str] = Query("mes"),
                           fecha_inicio: Optional[str] = Query(None), fecha_fin: Optional[str] = Query(None),
                           limit: int = Query(300, ge=1, le=1000)):
    udb = _u(unidad)
    fi, ff, _, _, label = _resolver_rango(udb, periodo, fecha_inicio, fecha_fin)
    try:
        tickets = _real_tickets(udb, fi, ff, limit=limit)
        resumen = {
            "num_tickets": len(tickets),
            "venta_total": round(sum(t["ventas"] for t in tickets), 2),
            "pax_total": sum(t["pax"] for t in tickets),
            "ticket_max": max((t["ventas"] for t in tickets), default=0),
            "ticket_min": min((t["ventas"] for t in tickets), default=0),
        }
        return _envelope(True,
            filtros={"fecha_inicio": fi, "fecha_fin": ff, "periodo": periodo, "periodo_label": label},
            resumen=resumen, tickets=tickets)
    except Exception as e:
        logger.error(f"[REPORTEADOR-BI] revision-tickets: {e}")
        return {"success": False, "_error": str(e)}


# ---- 7) ROTACIÓN DE MESAS (PENDIENTE: capacidad/mesas no sincronizadas) ----
@router.get("/rotacion-mesas")
async def rotacion_mesas(unidad: Optional[str] = Query(None), periodo: Optional[str] = Query("mes"),
                         fecha_inicio: Optional[str] = Query(None), fecha_fin: Optional[str] = Query(None)):
    udb = _u(unidad)
    fi, ff, _, _, label = _resolver_rango(udb, periodo, fecha_inicio, fecha_fin)
    # Proxy informativo (pax/cuentas) pero la ROTACIÓN requiere capacidad de sillas (no sincronizada).
    try:
        k = _kpis_rango(udb, fi, ff)
    except Exception:
        k = {}
    return _envelope(False, fuente_requerida="Capacidad Restaurante / Comanda_Mesa (sillas por sucursal)",
                     medidas_pendientes=["Rotación de Mesas", "Sillas para Rotación", "Rotación Promedio"],
                     proxy={"pax": k.get("pax"), "cuentas": k.get("cuentas"),
                            "periodo_label": label, "fecha_inicio": fi, "fecha_fin": ff})


# ---- 8) ANÁLISIS DE DOCUMENTOS (PENDIENTE: documentos no sincronizados) ----
@router.get("/analisis-documentos")
async def analisis_documentos(unidad: Optional[str] = Query(None), periodo: Optional[str] = Query("mes")):
    return _envelope(False, fuente_requerida="Documentos_Capturados / Movimiento (MPRO)",
                     medidas_pendientes=["Documentos Promedio", "Promedio Doc", "Documentos por operador/semana"])


# ---- 9) KPIs MES ACTUAL ----------------------------------------------------
@router.get("/kpis-mes")
async def kpis_mes(unidad: Optional[str] = Query(None)):
    udb = _u(unidad)
    # Ancla al último mes con datos (NO-LIVE), igual que el dashboard.
    fi, ff, prev_i, prev_f, label = _resolver_rango(udb, "mes", None, None)
    try:
        actual = _kpis_rango(udb, fi, ff)
        anterior = _kpis_rango(udb, prev_i.strftime("%Y-%m-%d"), prev_f.strftime("%Y-%m-%d")) if prev_i else {}

        def _var(a, b):
            return round((a - b) / b * 100, 1) if b else None
        comp = {}
        if anterior:
            comp = {
                "ventas": _var(actual["ventas"], anterior["ventas"]),
                "pax": _var(actual["pax"], anterior["pax"]),
                "cuentas": _var(actual["cuentas"], anterior["cuentas"]),
                "ticket_promedio": _var(actual["ticket_promedio"], anterior["ticket_promedio"]),
                "cheque_promedio": _var(actual["cheque_promedio"], anterior["cheque_promedio"]),
            }
        return _envelope(True,
            filtros={"fecha_inicio": fi, "fecha_fin": ff, "periodo_label": label},
            kpis=actual, mes_anterior=anterior, variaciones=comp,
            metas={"disponible": False, "nota":
                   "Las metas (Metas de Ventas / Metas de Pax) no están sincronizadas en EDARSAHUB; "
                   "el % de alcance y la proyección se habilitarán al cargarlas."})
    except Exception as e:
        logger.error(f"[REPORTEADOR-BI] kpis-mes: {e}")
        return {"success": False, "_error": str(e)}
