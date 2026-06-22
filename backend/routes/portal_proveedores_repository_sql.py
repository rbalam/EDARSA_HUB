"""
Repositorio SQL-only para Portal de Proveedores.

Usa tablas canónicas:
- Proveedor_Catalogo
- Proveedor_UsuariosPortal
- Proveedor_RolUsuarioPortal
- Proveedor_Contactos
- Proveedor_CuentasBancarias
- Compras_DocumentosFiscales
- Finanzas_CuentasPorPagar
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _fetch_all(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    from core.sql_first.db import fetch_all_dict
    return fetch_all_dict(sql, list(params))


def _fetch_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


def _execute(sql: str, params: tuple = ()) -> int:
    from core.sql_first.db import execute_sql
    return execute_sql(sql, list(params))


def _supplier_row_to_portal(row: Dict[str, Any], include_password: bool = False) -> Dict[str, Any]:
    if not row:
        return {}

    status = "approved" if row.get("Activo") and row.get("PortalHabilitado") and not row.get("Bloqueado") else "suspended"

    data = {
        "id": str(row.get("ProveedorID")),
        "proveedor_id": row.get("ProveedorID"),
        "rfc": row.get("RFC"),
        "razon_social": row.get("RazonSocial") or "",
        "nombre_contacto": row.get("NombreUsuario") or row.get("NombreContacto") or "",
        "email": row.get("Email") or row.get("EmailPrincipal") or "",
        "telefono": row.get("Telefono") or row.get("TelefonoPrincipal") or "",
        "status": status,
        "rol_portal_id": row.get("RolPortalID"),
        "sucursales_asignadas": [],
        "created_at": row.get("FechaAlta"),
        "approved_at": row.get("FechaAlta"),
        "approved_by": None,
        "approval_notes": "",
    }

    if include_password:
        data["password"] = row.get("PasswordHash") or ""

    return data


async def get_supplier_by_id(supplier_id: str, include_password: bool = False) -> Optional[Dict[str, Any]]:
    row = _fetch_one("""
        SELECT TOP 1
            p.ProveedorID, p.RFC, p.RazonSocial, p.NombreComercial,
            p.EmailPrincipal, p.TelefonoPrincipal, p.PortalHabilitado,
            p.Activo, p.FechaAlta,
            u.UsuarioPortalID, u.RolPortalID, u.NombreUsuario,
            u.Email, u.PasswordHash, u.Bloqueado
        FROM dbo.Proveedor_Catalogo p
        LEFT JOIN dbo.Proveedor_UsuariosPortal u
            ON u.ProveedorID = p.ProveedorID AND u.Activo = 1
        WHERE CAST(p.ProveedorID AS VARCHAR(50)) = %s
    """, (str(supplier_id),))
    return _supplier_row_to_portal(row, include_password) if row else None


async def get_supplier_by_rfc(rfc: str, include_password: bool = False) -> Optional[Dict[str, Any]]:
    row = _fetch_one("""
        SELECT TOP 1
            p.ProveedorID, p.RFC, p.RazonSocial, p.NombreComercial,
            p.EmailPrincipal, p.TelefonoPrincipal, p.PortalHabilitado,
            p.Activo, p.FechaAlta,
            u.UsuarioPortalID, u.RolPortalID, u.NombreUsuario,
            u.Email, u.PasswordHash, u.Bloqueado
        FROM dbo.Proveedor_Catalogo p
        LEFT JOIN dbo.Proveedor_UsuariosPortal u
            ON u.ProveedorID = p.ProveedorID AND u.Activo = 1
        WHERE UPPER(p.RFC) = UPPER(%s)
    """, (str(rfc),))
    return _supplier_row_to_portal(row, include_password) if row else None


async def list_suppliers(status: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
    where = ["p.Activo = 1"]
    if status == "pending":
        where.append("(p.PortalHabilitado = 0 OR p.PortalHabilitado IS NULL)")
    elif status == "approved":
        where.append("p.PortalHabilitado = 1")

    sql = f"""
        SELECT TOP {int(limit)}
            p.ProveedorID, p.RFC, p.RazonSocial, p.NombreComercial,
            p.EmailPrincipal, p.TelefonoPrincipal, p.PortalHabilitado,
            p.Activo, p.FechaAlta,
            u.UsuarioPortalID, u.RolPortalID, u.NombreUsuario,
            u.Email, u.PasswordHash, u.Bloqueado
        FROM dbo.Proveedor_Catalogo p
        LEFT JOIN dbo.Proveedor_UsuariosPortal u
            ON u.ProveedorID = p.ProveedorID AND u.Activo = 1
        WHERE {' AND '.join(where)}
        ORDER BY p.FechaAlta DESC
    """
    return [_supplier_row_to_portal(r, include_password=False) for r in _fetch_all(sql)]


async def update_supplier_portal_status(supplier_id: str, approved: bool) -> bool:
    affected = _execute("""
        UPDATE dbo.Proveedor_Catalogo
        SET PortalHabilitado = %s,
            FechaModificacion = SYSDATETIME()
        WHERE CAST(ProveedorID AS VARCHAR(50)) = %s
    """, (1 if approved else 0, str(supplier_id)))
    return affected > 0


async def update_supplier_password(supplier_id: str, password_hash: str) -> bool:
    affected = _execute("""
        UPDATE dbo.Proveedor_UsuariosPortal
        SET PasswordHash = %s,
            FechaModificacion = SYSDATETIME()
        WHERE CAST(ProveedorID AS VARCHAR(50)) = %s
          AND Activo = 1
    """, (password_hash, str(supplier_id)))
    return affected > 0


async def list_supplier_invoices(supplier_id: str, status: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
    where = ["CAST(df.ProveedorID AS VARCHAR(50)) = %s", "df.Activo = 1"]
    params = [str(supplier_id)]

    if status:
        where.append("e.Descripcion = %s")
        params.append(status)

    sql = f"""
        SELECT TOP {int(limit)}
            df.DocumentoFiscalID,
            df.ProveedorID,
            df.UUID,
            df.Serie,
            df.Folio,
            df.FechaEmision,
            df.RFCEmisor,
            df.NombreEmisor,
            df.RFCReceptor,
            df.NombreReceptor,
            df.Subtotal,
            df.ImpuestoTrasladado,
            df.Total,
            df.Moneda,
            df.TipoComprobante,
            df.RutaXML,
            df.RutaPDF,
            e.Descripcion AS Estatus
        FROM dbo.Compras_DocumentosFiscales df
        LEFT JOIN dbo.Compras_DocumentosFiscalesEstatus e
            ON e.EstatusDocumentoFiscalID = df.EstatusDocumentoFiscalID
        WHERE {' AND '.join(where)}
        ORDER BY df.CreatedAt DESC
    """
    rows = _fetch_all(sql, tuple(params))
    return [
        {
            "id": str(r.get("DocumentoFiscalID")),
            "supplier_id": str(r.get("ProveedorID")),
            "uuid": r.get("UUID"),
            "serie": r.get("Serie") or "",
            "folio": r.get("Folio") or "",
            "fecha_emision": r.get("FechaEmision"),
            "subtotal": float(r.get("Subtotal") or 0),
            "iva": float(r.get("ImpuestoTrasladado") or 0),
            "total": float(r.get("Total") or 0),
            "moneda": r.get("Moneda") or "MXN",
            "tipo_comprobante": r.get("TipoComprobante"),
            "receptor_rfc": r.get("RFCReceptor"),
            "receptor_nombre": r.get("NombreReceptor"),
            "status": r.get("Estatus") or "",
        }
        for r in rows
    ]


async def get_supplier_invoice(invoice_id: str, supplier_id: str) -> Optional[Dict[str, Any]]:
    rows = await list_supplier_invoices(str(supplier_id), limit=500)
    return next((i for i in rows if str(i.get("id")) == str(invoice_id)), None)


async def get_supplier_balances(supplier_id: str, limit: int = 500) -> Dict[str, Any]:
    """
    Saldos CxP SQL-only del proveedor.
    Fuente canónica: dbo.Finanzas_CuentasPorPagar.
    No consulta Mongo ni servidores LIVE.
    """
    sql = f"""
        SELECT TOP {int(limit)}
            cxp.CuentaPorPagarID,
            cxp.DocumentoFiscalID,
            cxp.ProveedorID,
            cxp.SucursalID,
            cxp.NumeroDocumento,
            cxp.FechaDocumento,
            cxp.FechaVencimiento,
            cxp.FechaRecepcion,
            cxp.MontoOriginal,
            cxp.MontoPagado,
            (cxp.MontoOriginal - cxp.MontoPagado) AS Saldo,
            cxp.MonedaID,
            cxp.TipoCambio,
            cxp.EstatusPagoID,
            ep.Codigo AS EstatusCodigo,
            ep.Descripcion AS EstatusDescripcion,
            df.UUID,
            df.Serie,
            df.Folio
        FROM dbo.Finanzas_CuentasPorPagar cxp
        LEFT JOIN dbo.Finanzas_EstatusPago ep
            ON ep.EstatusPagoID = cxp.EstatusPagoID
        LEFT JOIN dbo.Compras_DocumentosFiscales df
            ON df.DocumentoFiscalID = cxp.DocumentoFiscalID
        WHERE CAST(cxp.ProveedorID AS VARCHAR(50)) = %s
          AND cxp.Activo = 1
        ORDER BY cxp.FechaVencimiento ASC, cxp.FechaDocumento ASC
    """
    rows = _fetch_all(sql, (str(supplier_id),))

    facturas = []
    total_importe = 0.0
    total_pagado = 0.0
    total_saldo = 0.0

    for r in rows:
        importe = float(r.get("MontoOriginal") or 0)
        pagado = float(r.get("MontoPagado") or 0)
        saldo = float(r.get("Saldo") or 0)

        total_importe += importe
        total_pagado += pagado
        total_saldo += saldo

        facturas.append({
            "cuenta_por_pagar_id": str(r.get("CuentaPorPagarID")),
            "documento_fiscal_id": str(r.get("DocumentoFiscalID")) if r.get("DocumentoFiscalID") is not None else None,
            "supplier_id": str(r.get("ProveedorID")),
            "sucursal_id": str(r.get("SucursalID")),
            "folio": r.get("NumeroDocumento") or r.get("Folio") or "",
            "uuid": r.get("UUID"),
            "fecha": str(r.get("FechaDocumento") or "")[:10],
            "vencimiento": str(r.get("FechaVencimiento") or "")[:10],
            "importe": importe,
            "pagado": pagado,
            "saldo": saldo,
            "estatus_pago_id": r.get("EstatusPagoID"),
            "estatus": r.get("EstatusDescripcion") or r.get("EstatusCodigo") or "",
        })

    return {
        "sistemas": [{
            "id": "EDARSAHUB_SQL",
            "name": "EDARSAHUB SQL",
            "system_type": "EDARSAHUB_SQL",
            "facturas": len(facturas),
            "importe": total_importe,
            "pagado": total_pagado,
            "saldo": total_saldo,
            "status": "connected"
        }],
        "sucursales": [],
        "facturas_pendientes": [f for f in facturas if f.get("saldo", 0) > 0],
        "totales": {
            "importe": total_importe,
            "pagado": total_pagado,
            "saldo": total_saldo,
            "facturas": len(facturas)
        },
        "source_type": "EDARSAHUB_SQL"
    }
