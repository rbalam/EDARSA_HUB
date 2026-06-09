"""
EDARSA HUB - Sync Canónico de Movimientos de Inventario (Ruta B - int estricta)
================================================================================
Capa COMÚN reutilizable. Lee movimientos del ORIGEN (POS) y los escribe en el
modelo canónico int de EDARSAHUB:
  - Encabezado: Inventario_Movimientos
  - Detalle:    Inventario_MovimientosDetalle

PRINCIPIOS:
- Usa el RESOLVER CENTRALIZADO (core/inventarios/resolver_canonico). NO duplica lógica.
- NUNCA inventa IDs. Lo no resoluble (producto/almacén/sucursal/tipo) -> PENDIENTE.
- descartados = 0 (no se fuerza ningún insert con ID inventado).
- Idempotente: dedup por llave natural de encabezado y de detalle.
- Sin hardcode de clasificaciones (tipo de movimiento vía catálogo DB-driven).

NOTA: la conexión al POS la provee `execute_sql_fn` (helper canónico). Este módulo
NO abre conexiones al POS por su cuenta. Las escrituras van a EDARSAHUB.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Callable, Optional

from modules.compras.sync_service import get_edarsahub_connection
from core.inventarios.resolver_canonico import (
    resolver_producto_id,
    resolver_almacen_id,
    resolver_empresa_id,
    resolver_sucursal_id,
    resolver_tipo_movimiento_desde_concepto,
)

logger = logging.getLogger(__name__)


def _query_origen(system_type: str, dias_atras: int) -> str:
    st = (system_type or "").upper()
    if "MPRO" in st or "MANAGEMENT" in st or "MANAGMENT" in st:
        return f"""
            SELECT
                Mo_Fecha            AS fecha,
                CAST(Al_Cve_Almacen AS VARCHAR(50)) AS almacen_cod,
                Mo_Tipo             AS concepto,
                CAST(Ar_Cve_Articulo AS VARCHAR(50)) AS producto_cod,
                ISNULL(Mo_Cantidad, 0) AS cantidad,
                ISNULL(Mo_Costo, 0)    AS costo,
                CAST(Mo_Documento AS VARCHAR(50)) AS folio
            FROM Movimiento
            WHERE Mo_Fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
        """
    return f"""
        SELECT
            m.fecha             AS fecha,
            CAST(m.idalmacen AS VARCHAR(50)) AS almacen_cod,
            RTRIM(LTRIM(m.idconcepto)) AS concepto,
            CAST(m.idinsumo AS VARCHAR(50)) AS producto_cod,
            ISNULL(m.cantidad, 0) AS cantidad,
            ISNULL(m.costo, 0)    AS costo,
            CAST(m.movto AS VARCHAR(50)) AS folio
        FROM movtosalmacen m
        WHERE m.fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
          AND m.cancelado = 0
    """


def sync_movimientos_canonico(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    dias_atras: int = 30,
) -> Dict[str, Any]:
    """
    Sincroniza movimientos POS -> Inventario_Movimientos + Inventario_MovimientosDetalle.

    Returns dict con: status, encabezados_synced, detalles_synced, pendientes (desglose),
    descartados (=0 siempre).
    """
    system_type = server_info.get("system_type", "")
    server_id = server_info.get("id") or server_info.get("server_id")
    unidad_codigo = (unidad_info or {}).get("codigo", "")
    sucursal_origen = (unidad_info or {}).get("sucursal_origen_id")

    pend = {"sucursal": 0, "tipo": 0, "almacen": 0, "producto": 0}

    # 1) Resolver sucursal canónica (si ambiguo/sin mapeo -> no sincroniza, queda pendiente)
    suc = resolver_sucursal_id(str(server_id), sucursal_origen)
    if not suc.resuelto:
        return {"status": "PENDIENTE", "encabezados_synced": 0, "detalles_synced": 0,
                "descartados": 0, "pendientes": {"sucursal": "TODO", "motivo": suc.motivo}}
    sucursal_id = suc.canonical_id

    # 2) EmpresaID canónico vía Sistema_Empresas (CodigoEmpresa = código de unidad)
    emp = resolver_empresa_id(unidad_codigo)
    if not emp.resuelto:
        return {"status": "PENDIENTE", "encabezados_synced": 0, "detalles_synced": 0,
                "descartados": 0, "pendientes": {"empresa": "TODO", "motivo": emp.motivo}}
    empresa_id = emp.canonical_id

    conn = get_edarsahub_connection()
    cur = conn.cursor(as_dict=True)

    # 3) Leer ORIGEN
    rows = execute_sql_fn(
        server_info["host"], server_info["port"], server_info["database"],
        server_info["username"], server_info["password"], _query_origen(system_type, dias_atras),
    )
    if not rows:
        conn.close()
        return {"status": "OK", "encabezados_synced": 0, "detalles_synced": 0,
                "descartados": 0, "pendientes": pend, "message": "Sin datos o sin conexión en origen"}

    encabezados = 0
    detalles = 0
    cur_w = conn.cursor()

    for r in rows:
        concepto = r.get("concepto")
        producto_cod = str(r.get("producto_cod") or "").strip()
        almacen_cod = str(r.get("almacen_cod") or "").strip()
        fecha = r.get("fecha")
        folio = str(r.get("folio") or "").strip()[:30]
        cantidad = float(r.get("cantidad") or 0)
        costo = float(r.get("costo") or 0)

        # Resolver tipo (DB-driven), almacén y producto. Si algo falla -> pendiente, descartados=0.
        tip = resolver_tipo_movimiento_desde_concepto(system_type, concepto)
        if not tip.resuelto:
            pend["tipo"] += 1
            continue
        alm = resolver_almacen_id(empresa_id, sucursal_id, almacen_cod)
        if not alm.resuelto:
            pend["almacen"] += 1
            continue
        prod = resolver_producto_id(unidad_codigo, system_type, producto_cod)
        if not prod.resuelto:
            pend["producto"] += 1
            continue

        tipo_id, almacen_id, producto_id = tip.canonical_id, alm.canonical_id, prod.canonical_id

        try:
            # Encabezado idempotente (NOT EXISTS por llave natural)
            cur_w.execute(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM Inventario_Movimientos
                    WHERE EmpresaID=%s AND SucursalID=%s AND AlmacenID=%s AND TipoMovimientoID=%s
                      AND CAST(FechaMovimiento AS DATE)=CAST(%s AS DATE)
                      AND ISNULL(FolioReferencia,'')=%s
                )
                INSERT INTO Inventario_Movimientos
                    (TipoMovimientoID, EmpresaID, SucursalID, AlmacenID, FechaMovimiento,
                     ReferenciaTipo, FolioReferencia, Activo, CreatedAt)
                VALUES (%s,%s,%s,%s,%s,'MOVIMIENTO_POS',%s,1,GETDATE());
                """,
                (empresa_id, sucursal_id, almacen_id, tipo_id, fecha, folio,
                 tipo_id, empresa_id, sucursal_id, almacen_id, fecha, folio),
            )
            # Obtener MovimientoID (existente o recién insertado)
            cur_w.execute(
                """SELECT TOP 1 MovimientoID FROM Inventario_Movimientos
                   WHERE EmpresaID=%s AND SucursalID=%s AND AlmacenID=%s AND TipoMovimientoID=%s
                     AND CAST(FechaMovimiento AS DATE)=CAST(%s AS DATE) AND ISNULL(FolioReferencia,'')=%s
                   ORDER BY MovimientoID DESC""",
                (empresa_id, sucursal_id, almacen_id, tipo_id, fecha, folio),
            )
            mid_row = cur_w.fetchone()
            if not mid_row:
                continue
            movimiento_id = mid_row[0]
            encabezados += 1

            # Detalle idempotente (NOT EXISTS por MovimientoID + ProductoID)
            cur_w.execute(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM Inventario_MovimientosDetalle
                    WHERE MovimientoID=%s AND ProductoID=%s
                )
                INSERT INTO Inventario_MovimientosDetalle
                    (MovimientoID, ProductoID, Cantidad, CostoUnitario, CreatedAt)
                VALUES (%s,%s,%s,%s,GETDATE());
                """,
                (movimiento_id, producto_id, movimiento_id, producto_id, cantidad, costo),
            )
            detalles += 1
        except Exception as e:
            logger.warning(f"[SYNC-MOV-CANONICO] Error insertando movimiento: {str(e)[:120]}")

    conn.commit()
    conn.close()

    total_pend = sum(pend.values())
    logger.info(f"[SYNC-MOV-CANONICO] {unidad_codigo}: enc={encabezados} det={detalles} pendientes={total_pend}")
    return {
        "status": "OK",
        "encabezados_synced": encabezados,
        "detalles_synced": detalles,
        "descartados": 0,
        "pendientes": pend,
    }


__all__ = ["sync_movimientos_canonico"]
