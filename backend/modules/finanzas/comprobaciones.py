"""
EDARSA HUB - Comprobaciones financieras
=======================================

V1.0: lectura SQL-first no-live desde tablas canonicas EDARSAHUB.
- CFDI vive en Compras_DocumentosFiscales / Detalle.
- Comprobaciones agregan contexto financiero, no duplican facturas.
- Sin MongoDB, sin SAT live y sin lectura directa de carpetas desde pantallas.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.security import get_current_user
from core.sql_first.db import fetch_all_dict
from modules.finanzas.access import FINANZAS_VER, resolve_finanzas_unit_filter


router = APIRouter(prefix="/finanzas/comprobaciones", tags=["Comprobaciones"])

REQUIRED_TABLES = (
    "dbo.Finanzas_Comprobaciones",
    "dbo.Finanzas_ComprobacionesDocumentos",
    "dbo.Compras_DocumentosFiscales",
    "dbo.Compras_DocumentosFiscalesDetalle",
    "dbo.Compras_DocumentosFiscalesRelaciones",
)

TIPOS_COMPROBACION = {
    "CAJA_CHICA",
    "FONDO_REVOLVENTE",
    "VIATICO",
    "GASTO_POR_COMPROBAR",
    "REEMBOLSO",
}

ESTADOS_COMPROBACION = {
    "ABIERTA",
    "PENDIENTE_AUTORIZACION",
    "AUTORIZADA",
    "OBSERVADA",
    "RECHAZADA",
    "CERRADA",
    "CANCELADA",
}


def _schema_status() -> Dict[str, Any]:
    rows = fetch_all_dict(
        """
        SELECT
            v.Tabla,
            CASE WHEN OBJECT_ID(v.Tabla, 'U') IS NOT NULL THEN 1 ELSE 0 END AS Existe
        FROM (VALUES
            ('dbo.Finanzas_Comprobaciones'),
            ('dbo.Finanzas_ComprobacionesDocumentos'),
            ('dbo.Compras_DocumentosFiscales'),
            ('dbo.Compras_DocumentosFiscalesDetalle'),
            ('dbo.Compras_DocumentosFiscalesRelaciones')
        ) AS v(Tabla)
        """
    )
    tables = {str(row.get("Tabla")): bool(row.get("Existe")) for row in rows}
    missing = [table for table in REQUIRED_TABLES if not tables.get(table)]
    return {
        "ready": not missing,
        "missing_tables": missing,
        "tables": tables,
        "fuente": "CANONICO_EDARSAHUB",
    }


def _require_schema_ready() -> None:
    status = _schema_status()
    if status["ready"]:
        return
    raise HTTPException(
        status_code=409,
        detail={
            "message": (
                "Faltan tablas canonicas de comprobaciones CFDI. "
                "Revise y aplique la migracion "
                "backend/database/migrations/"
                "20260722_002_cfdi_portal_comprobaciones_contract.sql."
            ),
            "missing_tables": status["missing_tables"],
        },
    )


def _normalize_filter(value: Optional[str], allowed: set[str], field: str) -> Optional[str]:
    if not value:
        return None
    normalized = str(value).strip().upper()
    if not normalized:
        return None
    if normalized not in allowed:
        raise HTTPException(status_code=400, detail=f"{field} no canonico.")
    return normalized


@router.get("/status")
async def get_comprobaciones_status(current_user: Dict = Depends(get_current_user)):
    """Estado de contrato canonico para el tab de comprobaciones."""
    resolve_finanzas_unit_filter(current_user, permission_code=FINANZAS_VER)
    status = _schema_status()
    return {
        **status,
        "no_live": True,
        "sat_live": False,
        "facturas_duplicadas": False,
    }


@router.get("")
async def listar_comprobaciones(
    unidad_negocio_pk: Optional[str] = None,
    tipo_comprobacion: Optional[str] = Query(default=None),
    estado_comprobacion: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: Dict = Depends(get_current_user),
):
    """
    Lista comprobaciones internas.

    Lee exclusivamente EDARSAHUB SQL y respeta alcance RBAC por unidad_negocio_pk.
    Los CFDI relacionados se cuentan desde las tablas canonicas de compras.
    """
    _require_schema_ready()
    unidad_pk, unidades_permitidas = resolve_finanzas_unit_filter(
        current_user,
        unidad_negocio_pk,
        permission_code=FINANZAS_VER,
    )
    tipo = _normalize_filter(tipo_comprobacion, TIPOS_COMPROBACION, "tipo_comprobacion")
    estado = _normalize_filter(estado_comprobacion, ESTADOS_COMPROBACION, "estado_comprobacion")

    where = ["fc.Activo = 1"]
    params: list[Any] = []

    if unidad_pk:
        where.append("CONVERT(varchar(36), fc.UnidadNegocioID) = %s")
        params.append(str(unidad_pk))
    elif unidades_permitidas is not None:
        allowed = [str(unit) for unit in unidades_permitidas if unit]
        if allowed:
            placeholders = ",".join(["%s"] * len(allowed))
            where.append(f"CONVERT(varchar(36), fc.UnidadNegocioID) IN ({placeholders})")
            params.extend(allowed)
        else:
            where.append("1 = 0")

    if tipo:
        where.append("fc.TipoComprobacion = %s")
        params.append(tipo)
    if estado:
        where.append("fc.EstadoComprobacion = %s")
        params.append(estado)

    sql = f"""
        SELECT TOP {int(limit)}
            fc.ComprobacionID,
            CONVERT(varchar(36), fc.UnidadNegocioID) AS unidad_negocio_pk,
            u.codigo AS unidad_negocio_codigo,
            u.nombre AS unidad_negocio_nombre,
            fc.UsuarioResponsableID,
            fc.TipoComprobacion,
            fc.ReferenciaOperacion,
            fc.MontoEntregado,
            fc.MontoComprobado,
            fc.MontoReembolsar,
            fc.MontoReintegrar,
            fc.EstadoComprobacion,
            fc.RequiereAutorizacion,
            fc.FechaAlta,
            fc.FechaCierre,
            COUNT(fcd.ComprobacionDocumentoID) AS documentos_count,
            ISNULL(SUM(CASE WHEN fcd.Activo = 1 THEN fcd.MontoAplicado ELSE 0 END), 0) AS monto_documentos
        FROM dbo.Finanzas_Comprobaciones fc
        INNER JOIN dbo.Unidades_Negocio u
            ON u.id = fc.UnidadNegocioID
           AND ISNULL(u.activo, 1) = 1
        LEFT JOIN dbo.Finanzas_ComprobacionesDocumentos fcd
            ON fcd.ComprobacionID = fc.ComprobacionID
           AND fcd.Activo = 1
        WHERE {" AND ".join(where)}
        GROUP BY
            fc.ComprobacionID,
            fc.UnidadNegocioID,
            u.codigo,
            u.nombre,
            fc.UsuarioResponsableID,
            fc.TipoComprobacion,
            fc.ReferenciaOperacion,
            fc.MontoEntregado,
            fc.MontoComprobado,
            fc.MontoReembolsar,
            fc.MontoReintegrar,
            fc.EstadoComprobacion,
            fc.RequiereAutorizacion,
            fc.FechaAlta,
            fc.FechaCierre
        ORDER BY fc.FechaAlta DESC, fc.ComprobacionID DESC
    """
    rows = fetch_all_dict(sql, tuple(params))
    comprobaciones = [
        {
            "comprobacion_id": row.get("ComprobacionID"),
            "unidad_negocio_pk": row.get("unidad_negocio_pk"),
            "unidad_negocio_codigo": row.get("unidad_negocio_codigo"),
            "unidad_negocio_nombre": row.get("unidad_negocio_nombre"),
            "usuario_responsable_id": row.get("UsuarioResponsableID"),
            "tipo_comprobacion": row.get("TipoComprobacion"),
            "referencia_operacion": row.get("ReferenciaOperacion"),
            "monto_entregado": float(row.get("MontoEntregado") or 0),
            "monto_comprobado": float(row.get("MontoComprobado") or 0),
            "monto_reembolsar": float(row.get("MontoReembolsar") or 0),
            "monto_reintegrar": float(row.get("MontoReintegrar") or 0),
            "estado_comprobacion": row.get("EstadoComprobacion"),
            "requiere_autorizacion": bool(row.get("RequiereAutorizacion")),
            "fecha_alta": row.get("FechaAlta"),
            "fecha_cierre": row.get("FechaCierre"),
            "documentos_count": int(row.get("documentos_count") or 0),
            "monto_documentos": float(row.get("monto_documentos") or 0),
        }
        for row in rows
    ]

    return {
        "fuente": "CANONICO_EDARSAHUB",
        "no_live": True,
        "sat_live": False,
        "total": len(comprobaciones),
        "comprobaciones": comprobaciones,
    }
