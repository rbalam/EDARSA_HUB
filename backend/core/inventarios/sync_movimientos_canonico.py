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

from modules.compras.sync_service import get_edarsahub_writer_connection
from core.inventarios.resolver_canonico import (
    resolver_producto_id,
    resolver_almacen_id,
    resolver_empresa_id,
    resolver_sucursal_id,
    resolver_tipo_movimiento_desde_concepto,
)

logger = logging.getLogger(__name__)

from core.inventarios.movement_filter_config import normalize_movement_codes


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
                ISNULL(Mv_Cantidad_Control_1, 0) AS cantidad,
                ISNULL(Mv_Costo, 0)      AS costo,
                CAST(Mv_Documento AS VARCHAR(50)) AS folio
            FROM Movimiento
            WHERE Mv_Fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
              {filtro_suc}
        """
    return _query_origen_soft_movsinv(dias_atras)


def _query_origen_soft_movsinv(dias_atras: int) -> str:
    """Lectura simple de movimientos directos por insumo."""
    return f"""
        SELECT
            i.fecha AS fecha,
            CAST(i.idalmacen AS VARCHAR(50)) AS almacen_cod,
            RTRIM(LTRIM(i.idconcepto)) AS concepto,
            RTRIM(LTRIM(i.idinsumo)) AS producto_cod,
            ISNULL(i.cantidad, 0) AS cantidad,
            ISNULL(i.costo, 0) AS costo,
            CAST(i.movto AS VARCHAR(30)) AS source_movto,
            CAST(
                CASE
                    WHEN i.movto IS NOT NULL
                        THEN 'I:M:' + CAST(i.movto AS VARCHAR(24))
                    WHEN NULLIF(i.traspaso, 0) IS NOT NULL
                        THEN 'I:T:' + CAST(i.traspaso AS VARCHAR(24))
                    WHEN NULLIF(i.idcompra, 0) IS NOT NULL
                        THEN 'I:C:' + CAST(i.idcompra AS VARCHAR(24))
                    WHEN NULLIF(i.invfisico, 0) IS NOT NULL
                        THEN 'I:F:' + CAST(i.invfisico AS VARCHAR(24))
                    WHEN NULLIF(i.foliocheque, 0) IS NOT NULL
                        THEN 'I:Q:' + CAST(i.foliocheque AS VARCHAR(24))
                    WHEN NULLIF(i.idpedido, 0) IS NOT NULL
                        THEN 'I:P:' + CAST(i.idpedido AS VARCHAR(24))
                    ELSE 'I:D:' + REPLACE(REPLACE(REPLACE(
                        CONVERT(VARCHAR(23), i.fecha, 121), '-', ''), ':', ''), ' ', '')
                END
                AS VARCHAR(30)
            ) AS folio
        FROM movsinv i
        WHERE i.fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
          AND NULLIF(RTRIM(LTRIM(i.idinsumo)), '') IS NOT NULL
    """


def _query_origen_soft_presentaciones(dias_atras: int) -> str:
    """Lectura simple de movimientos por presentación -> insumo.

    La deduplicación contra movsinv ocurre en Python para evitar un NOT EXISTS
    correlacionado costoso sobre el POS.
    """
    return f"""
        SELECT
            m.fecha AS fecha,
            CAST(m.idalmacen AS VARCHAR(50)) AS almacen_cod,
            RTRIM(LTRIM(m.idconcepto)) AS concepto,
            RTRIM(LTRIM(ip.idinsumo)) AS producto_cod,
            ISNULL(m.cantidad, 0) AS cantidad,
            ISNULL(m.costo, 0) AS costo,
            CAST(m.movto AS VARCHAR(30)) AS source_movto,
            CAST(m.movto AS VARCHAR(30)) AS folio
        FROM movtosalmacen m
        JOIN insumospresentaciones ip
          ON ip.idinsumospresentaciones = m.idinsumospresentaciones
        WHERE m.fecha >= DATEADD(DAY, -{int(dias_atras)}, GETDATE())
          AND NULLIF(RTRIM(LTRIM(ip.idinsumo)), '') IS NOT NULL
    """


def _soft_dedupe_key(row: Dict[str, Any]) -> tuple:
    return (
        str(row.get("fecha") or ""),
        str(row.get("almacen_cod") or "").strip(),
        str(row.get("concepto") or "").strip().upper(),
        str(row.get("producto_cod") or "").strip(),
        str(row.get("source_movto") or "").strip(),
    )


def _merge_soft_movement_sources(
    movsinv_rows: list,
    presentation_rows: list,
) -> tuple[list, int]:
    """movsinv tiene precedencia sobre movtosalmacen para la misma llave."""
    merged = list(movsinv_rows or [])
    seen = {_soft_dedupe_key(row) for row in merged}
    duplicates = 0

    for row in presentation_rows or []:
        key = _soft_dedupe_key(row)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        merged.append(row)

    return merged, duplicates


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
    system_type_upper = str(system_type or "").upper()
    is_softrestaurant = "SOFT" in system_type_upper
    # Los filtros de pantalla son una decisión de lectura, nunca de extracción.
    # Sincronizar todos los movimientos independientemente de la selección.

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

    conn = get_edarsahub_writer_connection()
    cur = conn.cursor(as_dict=True)

    # 3) Leer ORIGEN.
    # SoftRestaurant se lee en dos consultas simples; evita el NOT EXISTS
    # correlacionado que degradaba fuertemente ventanas de 30 días.
    source_duplicates = 0
    if is_softrestaurant:
        movsinv_rows = execute_sql_fn(
            server_info["host"],
            server_info["port"],
            server_info["database"],
            server_info["username"],
            server_info["password"],
            _query_origen_soft_movsinv(dias_atras),
        )
        if movsinv_rows is None:
            conn.close()
            return {
                "status": "ERROR",
                "encabezados_synced": 0,
                "detalles_synced": 0,
                "descartados": 0,
                "pendientes": pend,
                "message": "No fue posible leer movsinv; ledger conservado sin cambios",
            }

        presentation_rows = execute_sql_fn(
            server_info["host"],
            server_info["port"],
            server_info["database"],
            server_info["username"],
            server_info["password"],
            _query_origen_soft_presentaciones(dias_atras),
        )
        if presentation_rows is None:
            conn.close()
            return {
                "status": "ERROR",
                "encabezados_synced": 0,
                "detalles_synced": 0,
                "descartados": 0,
                "pendientes": pend,
                "message": "No fue posible leer movtosalmacen; ledger conservado sin cambios",
            }

        rows, source_duplicates = _merge_soft_movement_sources(
            movsinv_rows,
            presentation_rows,
        )
        logger.info(
            "[SYNC-MOV-CANONICO] %s fuentes Soft movsinv=%s "
            "movtosalmacen=%s duplicados=%s total=%s",
            unidad_codigo,
            len(movsinv_rows),
            len(presentation_rows),
            source_duplicates,
            len(rows),
        )
    else:
        rows = execute_sql_fn(
            server_info["host"],
            server_info["port"],
            server_info["database"],
            server_info["username"],
            server_info["password"],
            _query_origen(system_type, dias_atras, sucursal_origen),
        )
        if rows is None:
            conn.close()
            return {
                "status": "ERROR",
                "encabezados_synced": 0,
                "detalles_synced": 0,
                "descartados": 0,
                "pendientes": pend,
                "message": "No fue posible leer movimientos del origen; ledger conservado sin cambios",
            }

    # Una lista vacía es una lectura válida: no hay movimientos en la ventana.
    # SoftRestaurant puede reconciliar el ledger a cero; MPRO conserva el
    # comportamiento existente y simplemente termina sin cambios.
    if not rows and not is_softrestaurant:
        conn.close()
        return {"status": "OK", "encabezados_synced": 0, "detalles_synced": 0,
                "descartados": 0, "pendientes": pend, "message": "Sin movimientos en origen"}

    filtrados_no_autorizados = 0  # El filtro se aplica al consultar, no al guardar.

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
        # Se redondea a la escala del destino decimal(18,6); cantidades que
        # redondean a 0 se descartan (evitan violar la CHECK al agregar).
        cantidad = round(abs(float(r.get("cantidad") or 0)), 6)
        costo = round(abs(float(r.get("costo") or 0)), 6)
        if cantidad <= 0:
            pend["cantidad_cero"] = pend.get("cantidad_cero", 0) + 1
            continue
        tip = resolver_tipo_movimiento_desde_concepto(system_type, concepto)
        if not tip.resuelto:
            # Compatibilidad controlada para conceptos SoftRestaurant
            # ya verificados en el catálogo histórico. La tabla DB-driven
            # sigue siendo la primera autoridad; este fallback evita perder
            # movimientos válidos mientras se completa su seed persistente.
            st_upper = str(system_type or "").upper()
            if "SOFT" in st_upper:
                from modules.compras.sync_service import (
                    map_tipo_movimiento_softrestaurant,
                )
                fallback_tipo = map_tipo_movimiento_softrestaurant(
                    concepto,
                    cantidad,
                )
                if fallback_tipo is not None:
                    class _FallbackTipo:
                        resuelto = True
                        canonical_id = fallback_tipo
                    tip = _FallbackTipo()
                else:
                    pend["tipo"] += 1
                    continue
            else:
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
        concepto_origen = str(concepto or "").strip().upper()
        referencia_tipo = f"MOVIMIENTO_POS|{concepto_origen}"
        resueltos.append((
            empresa_id, sucursal_id, alm.canonical_id, tip.canonical_id,
            concepto_origen, referencia_tipo, fecha, folio,
            prod.canonical_id, cantidad, costo
        ))

    pendientes_criticos = (
        int(pend.get("tipo", 0))
        + int(pend.get("almacen", 0))
        + int(pend.get("producto", 0))
    )

    # SoftRestaurant no debe perder TODA la ventana por unas pocas filas
    # pendientes. Las filas resolubles se sincronizan; las no resolubles se
    # reportan explícitamente para corrección de catálogo/mapeo. Esto mantiene
    # el ledger operativo sin inventar IDs ni ocultar pendientes.
    if not resueltos and is_softrestaurant:
        conn.close()
        return {
            "status": "PENDIENTE",
            "encabezados_synced": 0,
            "detalles_synced": 0,
            "descartados": 0,
            "pendientes": pend,
            "filtrados_no_autorizados": filtrados_no_autorizados,
            "message": "No hay movimientos SoftRestaurant resolubles en la ventana",
        }

    if not resueltos and not is_softrestaurant:
        conn.close()
        return {"status": "OK", "encabezados_synced": 0, "detalles_synced": 0,
                "descartados": 0, "pendientes": pend, "message": "Sin movimientos resolubles"}

    # 4) Escritura SET-BASED (staging temporal + INSERT..SELECT). Reduce miles de
    #    round-trips a unas pocas sentencias. Idempotente por llave natural.
    cur_w = conn.cursor()

    # SoftRestaurant conserva siempre el upsert no destructivo.
    # MPRO puede reconstruir su ventana únicamente cuando la lectura fue válida
    # y no existen pendientes críticos de catálogo/mapeo.
    movimientos_reconciliados_eliminados = 0

    cur_w.execute("""
        CREATE TABLE #stg_mov (
            EmpresaID int, SucursalID int, AlmacenID int, TipoMovimientoID tinyint,
            ConceptoOrigen varchar(50), ReferenciaTipo varchar(80),
            FechaMovimiento datetime2, Folio varchar(30),
            ProductoID int, Cantidad decimal(18,6), CostoUnitario decimal(18,6)
        )
    """)
    ins = """INSERT INTO #stg_mov (EmpresaID,SucursalID,AlmacenID,TipoMovimientoID,ConceptoOrigen,ReferenciaTipo,FechaMovimiento,Folio,ProductoID,Cantidad,CostoUnitario)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    BATCH = 1000
    for i in range(0, len(resueltos), BATCH):
        cur_w.executemany(ins, resueltos[i:i + BATCH])

    # NO borrar históricos de ningún motor al cambiar filtros. El usuario
    # puede reactivar cualquier tipo sin resincronizar las fechas previas.

    # 4a) Insertar encabezados nuevos (uno por llave natural empresa+sucursal+almacen+tipo+fecha(día)+folio)
    cur_w.execute("""
        INSERT INTO Inventario_Movimientos
            (TipoMovimientoID, EmpresaID, SucursalID, AlmacenID, FechaMovimiento,
             ReferenciaTipo, FolioReferencia, Activo, CreatedAt)
        SELECT s.TipoMovimientoID, s.EmpresaID, s.SucursalID, s.AlmacenID,
               MIN(s.FechaMovimiento), s.ReferenciaTipo,
               s.Folio, 1, GETDATE()
        FROM #stg_mov s
        WHERE NOT EXISTS (
            SELECT 1 FROM Inventario_Movimientos m
            WHERE m.EmpresaID=s.EmpresaID AND m.SucursalID=s.SucursalID AND m.AlmacenID=s.AlmacenID
              AND m.TipoMovimientoID=s.TipoMovimientoID
              AND CAST(m.FechaMovimiento AS DATE)=CAST(s.FechaMovimiento AS DATE)
              AND ISNULL(m.FolioReferencia,'')=ISNULL(s.Folio,'')
              AND ISNULL(m.ReferenciaTipo,'')=ISNULL(s.ReferenciaTipo,'')
        )
        GROUP BY s.EmpresaID, s.SucursalID, s.AlmacenID, s.TipoMovimientoID,
                 s.ReferenciaTipo, CAST(s.FechaMovimiento AS DATE), s.Folio
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
         AND ISNULL(m.ReferenciaTipo,'')=ISNULL(s.ReferenciaTipo,'')
        WHERE NOT EXISTS (
            SELECT 1 FROM Inventario_MovimientosDetalle d
            WHERE d.MovimientoID=m.MovimientoID AND d.ProductoID=s.ProductoID
        )
        GROUP BY m.MovimientoID, s.ProductoID
        HAVING SUM(s.Cantidad) > 0
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
        "filtrados_no_autorizados": filtrados_no_autorizados,
        "duplicados_fuente_omitidos": source_duplicates,
        "movimientos_reconciliados_eliminados": movimientos_reconciliados_eliminados,
        "pendientes_criticos": pendientes_criticos,
        "status_detail": (
            "PARTIAL_WITH_PENDING"
            if pendientes_criticos > 0
            else "COMPLETE"
        ),
    }


__all__ = ["sync_movimientos_canonico"]
