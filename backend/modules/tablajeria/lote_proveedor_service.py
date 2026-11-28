"""
EDARSA HUB - Tablajeria R24
Rendimiento por Lote Proveedor y Reclamos.

Servicio de aplicacion. Reutiliza SQL Server canonico y no duplica Compras,
Proveedor_Catalogo, Scheduler ni Centro de Control.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import json
import logging

from core.sql_first.db import get_sql_connection

logger = logging.getLogger(__name__)


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _row_to_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in dict(row).items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = _to_str(value) if key.lower().endswith('id') and value is not None else value
    return result


class TablajeriaLoteProveedorService:
    """Consulta y opera trazabilidad lote-proveedor para tablajeria."""

    def listar_rendimientos_lote(
        self,
        empresa_id: Optional[str] = None,
        proveedor_id: Optional[str] = None,
        lote: Optional[str] = None,
        semaforo: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        conn = get_sql_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            where = ["Activo = 1"]
            params: List[Any] = []

            if empresa_id:
                where.append("EmpresaID = %s")
                params.append(empresa_id)
            if proveedor_id:
                where.append("ProveedorID = %s")
                params.append(proveedor_id)
            if lote:
                where.append("(LoteProveedor LIKE %s OR LoteInterno LIKE %s)")
                params.extend([f"%{lote}%", f"%{lote}%"])
            if semaforo:
                where.append("Semaforo = %s")
                params.append(semaforo)

            where_sql = " AND ".join(where)
            cursor.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM dbo.Tablajeria_LotesProveedorRendimiento
                WHERE {where_sql}
                """,
                tuple(params),
            )
            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT
                    LoteRendimientoID, EmpresaID, UnidadNegocioID, SucursalID,
                    ProveedorID, ProveedorNombre, LoteProveedor, LoteInterno,
                    OrdenCompraFolio, RecepcionFolio, FacturaFolio,
                    FolioOrdenTablaje, InsumoBaseCodigo, InsumoBaseNombre,
                    CantidadBaseKg, RendimientoEsperadoPorcentaje,
                    RendimientoRealPorcentaje, DesviacionPorcentaje, MermaRealKg,
                    CostoUnitario, ImpactoEconomico, Semaforo, Estatus,
                    FechaOperacionMexico, FechaCalculoUTC
                FROM dbo.Tablajeria_LotesProveedorRendimiento
                WHERE {where_sql}
                ORDER BY FechaOperacionMexico DESC, FechaCalculoUTC DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                """,
                tuple(params + [offset, limit]),
            )
            rows = [_row_to_dict(row) for row in cursor.fetchall()]
            return {"rendimientos": rows, "total": total, "limit": limit, "offset": offset}
        finally:
            conn.close()

    def obtener_drilldown_lote(self, lote_rendimiento_id: str) -> Dict[str, Any]:
        conn = get_sql_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(
                """
                SELECT TOP 1 *
                FROM dbo.Tablajeria_LotesProveedorRendimiento
                WHERE LoteRendimientoID = %s AND Activo = 1
                """,
                (lote_rendimiento_id,),
            )
            lote = cursor.fetchone()
            if not lote:
                raise ValueError("Lote proveedor no encontrado")

            cursor.execute(
                """
                SELECT TOP 50 *
                FROM dbo.Tablajeria_ReclamosProveedor
                WHERE LoteRendimientoID = %s AND Activo = 1
                ORDER BY FechaAperturaUTC DESC
                """,
                (lote_rendimiento_id,),
            )
            reclamos = [_row_to_dict(row) for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT TOP 50 *
                FROM dbo.Tablajeria_NotificacionesLote
                WHERE LoteRendimientoID = %s AND Activo = 1
                ORDER BY FechaAltaUTC DESC
                """,
                (lote_rendimiento_id,),
            )
            notificaciones = [_row_to_dict(row) for row in cursor.fetchall()]

            return {
                "lote": _row_to_dict(lote),
                "reclamos": reclamos,
                "notificaciones": notificaciones,
            }
        finally:
            conn.close()

    def crear_reclamo_proveedor(
        self,
        lote_rendimiento_id: str,
        motivo: str,
        descripcion: Optional[str],
        prioridad: str,
        evidencia: Optional[Dict[str, Any]],
        usuario_id: Optional[str],
    ) -> Dict[str, Any]:
        conn = get_sql_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(
                """
                SELECT TOP 1 *
                FROM dbo.Tablajeria_LotesProveedorRendimiento
                WHERE LoteRendimientoID = %s AND Activo = 1
                """,
                (lote_rendimiento_id,),
            )
            lote = cursor.fetchone()
            if not lote:
                raise ValueError("Lote proveedor no encontrado")

            cursor.execute(
                "SELECT CONCAT('RCL-TAB-', FORMAT(SYSUTCDATETIME(), 'yyyyMMddHHmmss')) AS folio"
            )
            folio = cursor.fetchone()["folio"]

            cursor.execute(
                """
                INSERT INTO dbo.Tablajeria_ReclamosProveedor (
                    LoteRendimientoID, EmpresaID, UnidadNegocioID, ProveedorID,
                    ProveedorNombre, FolioReclamo, Motivo, Descripcion,
                    ImpactoEconomico, EvidenciaJSON, Estatus, Prioridad, UsuarioAltaID
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ABIERTO', %s, %s)
                """,
                (
                    lote_rendimiento_id,
                    lote.get("EmpresaID"),
                    lote.get("UnidadNegocioID"),
                    lote.get("ProveedorID"),
                    lote.get("ProveedorNombre"),
                    folio,
                    motivo,
                    descripcion,
                    lote.get("ImpactoEconomico"),
                    json.dumps(evidencia or {}, ensure_ascii=False),
                    prioridad,
                    usuario_id,
                ),
            )
            conn.commit()
            return {"success": True, "folio_reclamo": folio, "lote_rendimiento_id": lote_rendimiento_id}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def listar_reclamos(self, estatus: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        conn = get_sql_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            params: List[Any] = []
            where = ["Activo = 1"]
            if estatus:
                where.append("Estatus = %s")
                params.append(estatus)
            cursor.execute(
                f"""
                SELECT TOP {int(limit)} *
                FROM dbo.Tablajeria_ReclamosProveedor
                WHERE {' AND '.join(where)}
                ORDER BY FechaAperturaUTC DESC
                """,
                tuple(params),
            )
            return {"reclamos": [_row_to_dict(row) for row in cursor.fetchall()]}
        finally:
            conn.close()


def get_tablajeria_lote_proveedor_service() -> TablajeriaLoteProveedorService:
    return TablajeriaLoteProveedorService()
