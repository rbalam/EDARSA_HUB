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


def _query_origen(system_type: str, dias_atras: int, sucursal_origen: str = None) -> str:
    st = (system_type or "").upper()
    if "MPRO" in st or "MANAGEMENT" in st or "MANAGMENT" in st:
        # Esquema real ManagementPro (verificado): tabla Movimiento con prefijo Mv_/Pr_/Tm_.
        # (El esquema legacy usaba Mo_*/Ar_Cve_Articulo que NO existe -> 0 filas.)
        # MPRO es multisucursal en un mismo servidor: filtrar por Sc_Cve_Sucursal para
        # asignar cada movimiento a su unidad/sucursal canónica correcta.
        filtro_suc = ""
        if sucursal_origen:
            suc = str(sucursal_origen).replace("'", "''")
            filtro_suc = f" AND Sc_Cve_Sucursal = '{suc}' "
        return f"""
            SELECT
                Mv_Fecha            AS fecha,
                CAST(Al_Cve_Almacen AS VARCHAR(50)) AS almacen_cod,
                CAST(Tm_Cve_Tipo_Movimiento AS VARCHAR(50)) AS concepto,
                CAST(Pr_Cve_Producto AS VARCHAR(50)) AS producto_cod,
                ISNULL(Mv_Cantidad_1, 0) AS cantidad,
                ISNULL(Mv_Costo, 0)      AS costo,
                CAST(Mv_Documento AS VARCHAR(50)) AS folio
            FROM Movimiento
            WHERE Mv_Fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
              {filtro_suc}
        """
    # SoftRestaurant Pro (esquema real verificado): movtosalmacen no tiene 'cancelado'
    # ni 'idinsumo'; el código de producto se obtiene vía insumospresentaciones.idinsumo.
    return f"""
        SELECT
            m.fecha             AS fecha,
            CAST(m.idalmacen AS VARCHAR(50)) AS almacen_cod,
            RTRIM(LTRIM(m.idconcepto)) AS concepto,
            CAST(ip.idinsumo AS VARCHAR(50)) AS producto_cod,
            ISNULL(m.cantidad, 0) AS cantidad,
            ISNULL(m.costo, 0)    AS costo,
            CAST(m.movto AS VARCHAR(50)) AS folio
        FROM movtosalmacen m
        JOIN insumospresentaciones ip ON ip.idinsumospresentaciones = m.idinsumospresentaciones
        WHERE m.fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
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
        server_info["username"], server_info["password"], _query_origen(system_type, dias_atras, sucursal_origen),
    )
    if not rows:
        conn.close()
        return {"status": "OK", "encabezados_synced": 0, "detalles_synced": 0,
                "descartados": 0, "pendientes": pend, "message": "Sin datos o sin conexión en origen"}

    # 3) Leer y RESOLVER todo en memoria (resolvers cacheados -> rápido).
    # Precarga masiva del mapeo de productos (1 query) para evitar round-trips por producto.
    try:
        from core.inventarios.resolver_canonico import precargar_productos_mapeo
        precargar_productos_mapeo(unidad_codigo, system_type)
    except Exception as _e:
        logger.warning(f"[SYNC-MOV-CANONICO] Precarga productos falló (continúa): {str(_e)[:120]}")
    resueltos = []  # tuplas listas para staging
    for r in rows:
        concepto = r.get("concepto")
        producto_cod = str(r.get("producto_cod") or "").strip()
        almacen_cod = str(r.get("almacen_cod") or "").strip()
        fecha = r.get("fecha")
        folio = str(r.get("folio") or "").strip()[:30]
        # El signo (SoftRestaurant) indica dirección; la dirección la lleva el
        # TipoMovimiento canónico. El detalle exige Cantidad>0 y CostoUnitario>=0
        # (CK_Inventario_MovimientosDetalle_Valores) -> se almacena la MAGNITUD.
        cantidad = abs(float(r.get("cantidad") or 0))
        costo = abs(float(r.get("costo") or 0))
        if cantidad <= 0:
            pend["cantidad_cero"] = pend.get("cantidad_cero", 0) + 1
            continue
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
        resueltos.append((empresa_id, sucursal_id, alm.canonical_id, tip.canonical_id,
                          fecha, folio, prod.canonical_id, cantidad, costo))

    if not resueltos:
        conn.close()
        return {"status": "OK", "encabezados_synced": 0, "detalles_synced": 0,
                "descartados": 0, "pendientes": pend, "message": "Sin movimientos resolubles"}

    # 4) Escritura SET-BASED (staging temporal + INSERT..SELECT). Reduce miles de
    #    round-trips a unas pocas sentencias. Idempotente por llave natural.
    cur_w = conn.cursor()
    cur_w.execute("""
        CREATE TABLE #stg_mov (
            EmpresaID int, SucursalID int, AlmacenID int, TipoMovimientoID tinyint,
            FechaMovimiento datetime2, Folio varchar(30),
            ProductoID int, Cantidad decimal(18,6), CostoUnitario decimal(18,6)
        )
    """)
    ins = """INSERT INTO #stg_mov (EmpresaID,SucursalID,AlmacenID,TipoMovimientoID,FechaMovimiento,Folio,ProductoID,Cantidad,CostoUnitario)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    BATCH = 1000
    for i in range(0, len(resueltos), BATCH):
        cur_w.executemany(ins, resueltos[i:i + BATCH])

    # 4a) Insertar encabezados nuevos (uno por llave natural empresa+sucursal+almacen+tipo+fecha(día)+folio)
    cur_w.execute("""
        INSERT INTO Inventario_Movimientos
            (TipoMovimientoID, EmpresaID, SucursalID, AlmacenID, FechaMovimiento,
             ReferenciaTipo, FolioReferencia, Activo, CreatedAt)
        SELECT s.TipoMovimientoID, s.EmpresaID, s.SucursalID, s.AlmacenID,
               MIN(s.FechaMovimiento), 'MOVIMIENTO_POS', s.Folio, 1, GETDATE()
        FROM #stg_mov s
        WHERE NOT EXISTS (
            SELECT 1 FROM Inventario_Movimientos m
            WHERE m.EmpresaID=s.EmpresaID AND m.SucursalID=s.SucursalID AND m.AlmacenID=s.AlmacenID
              AND m.TipoMovimientoID=s.TipoMovimientoID
              AND CAST(m.FechaMovimiento AS DATE)=CAST(s.FechaMovimiento AS DATE)
              AND ISNULL(m.FolioReferencia,'')=ISNULL(s.Folio,'')
        )
        GROUP BY s.EmpresaID, s.SucursalID, s.AlmacenID, s.TipoMovimientoID,
                 CAST(s.FechaMovimiento AS DATE), s.Folio
    """)
    encabezados = cur_w.rowcount or 0

    # 4b) Insertar detalles nuevos (uno por movimiento+producto; agrega cantidades duplicadas del día)
    cur_w.execute("""
        INSERT INTO Inventario_MovimientosDetalle
            (MovimientoID, ProductoID, Cantidad, CostoUnitario, CreatedAt)
        SELECT m.MovimientoID, s.ProductoID, SUM(s.Cantidad),
               CASE WHEN SUM(s.Cantidad)=0 THEN MAX(s.CostoUnitario)
                    ELSE SUM(s.Cantidad*s.CostoUnitario)/NULLIF(SUM(s.Cantidad),0) END,
               GETDATE()
        FROM #stg_mov s
        JOIN Inventario_Movimientos m
          ON m.EmpresaID=s.EmpresaID AND m.SucursalID=s.SucursalID AND m.AlmacenID=s.AlmacenID
         AND m.TipoMovimientoID=s.TipoMovimientoID
         AND CAST(m.FechaMovimiento AS DATE)=CAST(s.FechaMovimiento AS DATE)
         AND ISNULL(m.FolioReferencia,'')=ISNULL(s.Folio,'')
        WHERE NOT EXISTS (
            SELECT 1 FROM Inventario_MovimientosDetalle d
            WHERE d.MovimientoID=m.MovimientoID AND d.ProductoID=s.ProductoID
        )
        GROUP BY m.MovimientoID, s.ProductoID
    """)
    detalles = cur_w.rowcount or 0

    cur_w.execute("DROP TABLE #stg_mov")
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
