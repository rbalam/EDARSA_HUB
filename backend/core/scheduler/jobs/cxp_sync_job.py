"""
EDARSA HUB - Job de Sincronización de Cuentas por Pagar (CxP)
=============================================================
Extrae facturas pendientes (SOLO LECTURA) de las fuentes operativas
(SoftRestaurant: CIENFUEGOS/ESTELAR/130MID + MPRO: ORIGEN/130QRO) y las persiste
en la tabla CANÓNICA `dbo.Finanzas_CxP_Sync` (EDARSAHUB).

La pantalla de Cuentas por Pagar lee EXCLUSIVAMENTE de esa tabla (NO-LIVE).
- Mapeo de unidades 100% canónico desde dbo.Unidades_Negocio (sin hardcode).
- Refresh idempotente: DELETE total + INSERT (EsDemo=0).
NO MongoDB. NO toca KPIs canónicos.
"""
import asyncio
import hashlib
import logging
import time
from datetime import datetime

from core.sql_first.db import get_sql_connection, fetch_all_dict
from modules.finanzas.repository_mpro import FinanzasRepositoryMPRO
from modules.finanzas.repository_softrestaurant import FinanzasRepositorySoftRestaurant

logger = logging.getLogger(__name__)


def _mpro_code_to_canonical():
    """Mapeo {Sc_Cve_Sucursal MPRO -> (codigo, nombre)} desde Unidades_Negocio (canónico)."""
    rows = fetch_all_dict(
        "SELECT codigo, nombre, sucursal_origen_id FROM dbo.Unidades_Negocio "
        "WHERE activo=1 AND system_type='MPRO' AND sucursal_origen_id IS NOT NULL"
    )
    return {str(r["sucursal_origen_id"]).strip(): (r["codigo"], r["nombre"]) for r in rows}


def _tipo_mpro(grupo_proveedor):
    g = str(grupo_proveedor or "").strip()
    if g == "0001":
        return "A", "ALIMENTOS"
    if g == "0002":
        return "B", "BEBIDAS"
    return "X", "OTROS"


def _hash(*parts):
    return hashlib.sha256("|".join(str(p or "") for p in parts).encode()).hexdigest()


def _fecha(v):
    if not v:
        return None
    s = str(v)
    return s[:10] if len(s) >= 10 else None


async def _extract():
    """Extrae CxP de ambas fuentes (live, solo lectura) y normaliza a filas canónicas."""
    sr_repo = FinanzasRepositorySoftRestaurant(None)
    mpro_repo = FinanzasRepositoryMPRO(None)
    canon = _mpro_code_to_canonical()
    filas = []
    metrics = {"softrestaurant": 0, "mpro": 0, "mpro_omitidas_no_canonicas": 0, "errores": []}

    # --- SoftRestaurant (server_key = código canónico) ---
    try:
        sr = await sr_repo.get_cuentas_por_pagar(sucursal_id=None, limit=5000)
        for c in sr:
            saldo = float(c.get("Saldo", 0) or 0)
            if saldo <= 0:
                continue
            unidad = str(c.get("SucursalID") or "").strip()  # CIENFUEGOS / ESTELAR / 130MID
            filas.append({
                "Fuente": "SOFTRESTAURANT", "UnidadNegocio": unidad,
                "UnidadNegocioNombre": c.get("SucursalNombre"),
                "SucursalCodigoOrigen": unidad,
                "ProveedorID": str(c.get("ProveedorID") or "")[:60],
                "ProveedorNombre": (c.get("ProveedorNombre") or "")[:250],
                "ProveedorRFC": (c.get("ProveedorRFC") or "")[:30],
                "TipoProveedor": c.get("TipoProveedor") or "X",
                "TipoProveedorNombre": c.get("TipoProveedorNombre") or "OTROS",
                "FolioEntrada": (str(c.get("FolioEntrada")) if c.get("FolioEntrada") else None),
                "FolioFactura": (str(c.get("FolioFactura")) if c.get("FolioFactura") else None),
                "Referencia": (c.get("Referencia") or "")[:300] or None,
                "FechaEntrada": _fecha(c.get("FechaEntrada")),
                "FechaVencimiento": _fecha(c.get("FechaVencimiento")),
                "DiasVencido": int(c.get("DiasVencido", 0) or 0),
                "MontoOriginal": float(c.get("MontoOriginal", 0) or 0),
                "MontoPagado": round(float(c.get("MontoOriginal", 0) or 0) - saldo, 2),
                "Saldo": saldo,
            })
        metrics["softrestaurant"] = sum(1 for f in filas if f["Fuente"] == "SOFTRESTAURANT")
    except Exception as e:
        logger.error(f"[CxP SYNC] SoftRestaurant: {e}")
        metrics["errores"].append(f"SOFTRESTAURANT: {str(e)[:120]}")

    # --- MPRO (mapear código -> canónico; omitir sucursales no canónicas) ---
    try:
        mpro = await mpro_repo.get_cuentas_por_pagar(sucursal_id=None, limit=5000)
        for c in mpro:
            saldo = float(c.get("Saldo", 0) or 0)
            if saldo <= 0:
                continue
            suc = str(c.get("SucursalID") or "").strip()
            if suc not in canon:
                metrics["mpro_omitidas_no_canonicas"] += 1
                continue
            codigo, nombre = canon[suc]
            tipo, tipo_nombre = _tipo_mpro(c.get("GrupoProveedor"))
            filas.append({
                "Fuente": "MANAGEMENTPRO", "UnidadNegocio": codigo, "UnidadNegocioNombre": nombre,
                "SucursalCodigoOrigen": suc,
                "ProveedorID": str(c.get("ProveedorID") or "")[:60],
                "ProveedorNombre": (c.get("ProveedorNombre") or f"Proveedor {c.get('ProveedorID')}")[:250],
                "ProveedorRFC": (c.get("ProveedorRFC") or "")[:30],
                "TipoProveedor": tipo, "TipoProveedorNombre": tipo_nombre,
                "FolioEntrada": (str(c.get("FolioEntrada")) if c.get("FolioEntrada") else None),
                "FolioFactura": (str(c.get("FolioFactura")) if c.get("FolioFactura") else None),
                "Referencia": (c.get("Referencia") or "")[:300] or None,
                "FechaEntrada": _fecha(c.get("FechaEntrada")),
                "FechaVencimiento": _fecha(c.get("FechaVencimiento")),
                "DiasVencido": max(0, int(c.get("DiasVencido", 0) or 0)),
                "MontoOriginal": float(c.get("MontoOriginal", 0) or 0),
                "MontoPagado": float(c.get("MontoPagado", 0) or 0),
                "Saldo": saldo,
            })
        metrics["mpro"] = sum(1 for f in filas if f["Fuente"] == "MANAGEMENTPRO")
    except Exception as e:
        logger.error(f"[CxP SYNC] MPRO: {e}")
        metrics["errores"].append(f"MANAGEMENTPRO: {str(e)[:120]}")

    return filas, metrics


def _persist(filas):
    """Refresh idempotente de Finanzas_CxP_Sync (DELETE total + INSERT multi-fila)."""
    conn = get_sql_connection()
    cur = conn.cursor()
    now = datetime.now()
    rows = []
    for f in filas:
        h = _hash(f["Fuente"], f["SucursalCodigoOrigen"], f["FolioEntrada"], f["FolioFactura"], f["ProveedorID"])
        rows.append((f["Fuente"], f["UnidadNegocio"], f["UnidadNegocioNombre"], f["SucursalCodigoOrigen"],
                     f["ProveedorID"], f["ProveedorNombre"], f["ProveedorRFC"], f["TipoProveedor"],
                     f["TipoProveedorNombre"], f["FolioEntrada"], f["FolioFactura"], f["Referencia"],
                     f["FechaEntrada"], f["FechaVencimiento"], f["DiasVencido"], f["MontoOriginal"],
                     f["MontoPagado"], f["Saldo"], h, 0, 1, now))
    try:
        cur.execute("DELETE FROM dbo.Finanzas_CxP_Sync WHERE EsDemo = 0")
        ncols = 22
        prefix = ("INSERT INTO dbo.Finanzas_CxP_Sync "
                  "(Fuente, UnidadNegocio, UnidadNegocioNombre, SucursalCodigoOrigen, ProveedorID, "
                  " ProveedorNombre, ProveedorRFC, TipoProveedor, TipoProveedorNombre, FolioEntrada, "
                  " FolioFactura, Referencia, FechaEntrada, FechaVencimiento, DiasVencido, MontoOriginal, "
                  " MontoPagado, Saldo, HashOrigen, EsDemo, Activo, FechaSync)")
        ph = "(" + ",".join(["%s"] * ncols) + ")"
        chunk = max(1, 2000 // ncols)
        inserted = 0
        for i in range(0, len(rows), chunk):
            batch = rows[i:i + chunk]
            cur.execute(prefix + " VALUES " + ",".join([ph] * len(batch)), tuple(v for r in batch for v in r))
            inserted += len(batch)
        conn.commit()
        return inserted
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close(); conn.close()


async def run_cxp_sync_async(dry_run: bool = False) -> dict:
    """Entrada ASYNC (para el scheduler / event loop)."""
    t0 = time.time()
    filas, metrics = await _extract()
    res = {"facturas_extraidas": len(filas), "softrestaurant": metrics["softrestaurant"],
           "mpro": metrics["mpro"], "mpro_omitidas_no_canonicas": metrics["mpro_omitidas_no_canonicas"],
           "errores": metrics["errores"], "dry_run": dry_run}
    if dry_run:
        res["mensaje"] = "DRY RUN: extracción OK, NO se escribió en EDARSAHUB."
        res["tiempo_s"] = round(time.time() - t0, 1)
        return res
    # GUARD anti-borrado: si la extracción no trajo filas y hubo errores (p.ej. POS no
    # alcanzable / subprocess fallido), NO ejecutar el refresh para no vaciar la canónica.
    if not filas and metrics["errores"]:
        res["facturas_persistidas"] = 0
        res["mensaje"] = "Extracción vacía con errores: refresh OMITIDO (no se borró la tabla canónica)."
        res["tiempo_s"] = round(time.time() - t0, 1)
        try:
            from core.scheduler.jobs.inteligencia_comercial_sync_job import registrar_syncpos_bitacora
            registrar_syncpos_bitacora("CXP_SYNC", "OMITIDO",
                                       f"Refresh omitido (extracción vacía con errores): {metrics['errores']}")
        except Exception:
            pass
        return res
    res["facturas_persistidas"] = await asyncio.to_thread(_persist, filas)
    res["tiempo_s"] = round(time.time() - t0, 1)
    try:
        from core.scheduler.jobs.inteligencia_comercial_sync_job import registrar_syncpos_bitacora
        registrar_syncpos_bitacora(
            "CXP_SYNC", "OK" if not metrics["errores"] else "PARCIAL",
            f"CxP: SR={metrics['softrestaurant']} MPRO={metrics['mpro']} persistidas={res['facturas_persistidas']}",
            lineas=res["facturas_persistidas"],
        )
    except Exception as e:
        logger.warning(f"[CxP SYNC] bitácora: {e}")
    return res


def run_cxp_sync(dry_run: bool = False) -> dict:
    """Entrada SÍNCRONA (para CLI / scripts). Envuelve la versión async."""
    return asyncio.run(run_cxp_sync_async(dry_run=dry_run))
