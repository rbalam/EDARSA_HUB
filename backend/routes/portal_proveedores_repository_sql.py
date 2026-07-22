"""
Repositorio SQL-only para Portal de Proveedores.

Usa tablas canónicas:
- Proveedor_Catalogo
- Proveedor_UsuariosPortal
- Proveedor_RolUsuarioPortal
- Proveedor_Contactos
- Proveedor_CuentasBancarias
- Compras_DocumentosFiscales
- Finanzas_CxP_Sync
"""

from typing import Optional, Dict, List, Any
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

    has_portal_user = bool(row.get("UsuarioPortalID")) and bool(row.get("UsuarioPortalActivo"))
    role_active = row.get("RolPortalID") is None or bool(row.get("RolPortalActivo"))
    is_enabled = bool(row.get("Activo")) and bool(row.get("PortalHabilitado"))
    is_blocked = bool(row.get("Bloqueado"))

    if is_enabled and has_portal_user and role_active and not is_blocked:
        status = "approved"
    elif bool(row.get("Activo")) and not bool(row.get("PortalHabilitado")):
        status = "pending"
    else:
        status = "suspended"

    contacto_nombre = " ".join(
        str(part or "").strip()
        for part in (row.get("NombreContacto"), row.get("ApellidosContacto"))
        if str(part or "").strip()
    )

    data = {
        "id": str(row.get("ProveedorID")),
        "proveedor_id": row.get("ProveedorID"),
        "usuario_portal_id": row.get("UsuarioPortalID"),
        "rfc": row.get("RFC"),
        "razon_social": row.get("RazonSocial") or "",
        "nombre_contacto": row.get("NombreUsuario") or contacto_nombre or "",
        "email": row.get("Email") or row.get("EmailContacto") or row.get("EmailPrincipal") or "",
        "telefono": row.get("TelefonoContacto") or row.get("CelularContacto") or row.get("TelefonoPrincipal") or "",
        "status": status,
        "rol_portal_id": row.get("RolPortalID"),
        "rol_portal": row.get("RolPortalDescripcion") or "",
        "sucursales_asignadas": [],
        "created_at": row.get("FechaAlta"),
        "approved_at": row.get("FechaAlta") if is_enabled else None,
        "approved_by": None,
        "approval_notes": "",
        "cuenta_bancaria_id": row.get("CuentaBancariaID"),
        "banco": row.get("NombreBanco") or "",
        "clabe": row.get("CLABE") or "",
        "cuenta": row.get("Cuenta") or "",
        "titular_cuenta": row.get("TitularCuenta") or "",
        "cuenta_bancaria_validada": bool(row.get("CuentaValidada")) if row.get("CuentaValidada") is not None else False,
        "cuenta_moneda": row.get("CuentaMoneda") or "",
    }

    if include_password:
        data["password"] = row.get("PasswordHash") or ""

    return data


_SUPPLIER_COLUMNS = """
            p.ProveedorID, p.RFC, p.RazonSocial, p.NombreComercial,
            p.EmailPrincipal, p.TelefonoPrincipal, p.PortalHabilitado,
            p.Activo, p.FechaAlta,
            u.UsuarioPortalID, u.RolPortalID, u.NombreUsuario,
            u.Email, u.PasswordHash, u.Bloqueado,
            u.Activo AS UsuarioPortalActivo,
            rp.Descripcion AS RolPortalDescripcion,
            rp.Activo AS RolPortalActivo,
            pc.Nombre AS NombreContacto,
            pc.Apellidos AS ApellidosContacto,
            pc.Email AS EmailContacto,
            pc.Telefono AS TelefonoContacto,
            pc.Celular AS CelularContacto,
            cb.CuentaBancariaID,
            cb.Cuenta,
            cb.CLABE,
            cb.TitularCuenta,
            cb.Validada AS CuentaValidada,
            cb.NombreBanco,
            cb.ClaveMoneda AS CuentaMoneda
"""

_SUPPLIER_FROM = """
        FROM dbo.Proveedor_Catalogo p
        OUTER APPLY (
            SELECT TOP 1
                up.UsuarioPortalID,
                up.RolPortalID,
                up.NombreUsuario,
                up.Email,
                up.PasswordHash,
                up.Bloqueado,
                up.Activo
            FROM dbo.Proveedor_UsuariosPortal up
            WHERE up.ProveedorID = p.ProveedorID
              AND ISNULL(up.Activo, 1) = 1
            ORDER BY ISNULL(up.Bloqueado, 0) ASC, up.UsuarioPortalID ASC
        ) u
        LEFT JOIN dbo.Proveedor_RolUsuarioPortal rp
            ON rp.RolPortalID = u.RolPortalID
        OUTER APPLY (
            SELECT TOP 1
                c.Nombre,
                c.Apellidos,
                c.Email,
                c.Telefono,
                c.Celular
            FROM dbo.Proveedor_Contactos c
            WHERE c.ProveedorID = p.ProveedorID
              AND ISNULL(c.Activo, 1) = 1
            ORDER BY ISNULL(c.EsPrincipal, 0) DESC, c.ContactoID ASC
        ) pc
        OUTER APPLY (
            SELECT TOP 1
                cuenta.CuentaBancariaID,
                cuenta.Cuenta,
                cuenta.CLABE,
                cuenta.TitularCuenta,
                cuenta.Validada,
                banco.NombreBanco,
                moneda.ClaveMoneda
            FROM dbo.Proveedor_CuentasBancarias cuenta
            LEFT JOIN dbo.Proveedor_Bancos banco
                ON banco.BancoID = cuenta.BancoID
               AND ISNULL(banco.Activo, 1) = 1
            LEFT JOIN dbo.Proveedor_Monedas moneda
                ON moneda.MonedaID = cuenta.MonedaID
               AND ISNULL(moneda.Activo, 1) = 1
            WHERE cuenta.ProveedorID = p.ProveedorID
              AND ISNULL(cuenta.Activa, 1) = 1
            ORDER BY ISNULL(cuenta.EsPrincipal, 0) DESC, cuenta.CuentaBancariaID ASC
        ) cb
"""


def _supplier_sql(where_sql: str, limit: int = 1, order_by: str = "p.FechaAlta DESC") -> str:
    return f"""
        SELECT TOP {int(limit)}
{_SUPPLIER_COLUMNS}
{_SUPPLIER_FROM}
        WHERE {where_sql}
        ORDER BY {order_by}
    """


async def get_supplier_by_id(supplier_id: str, include_password: bool = False) -> Optional[Dict[str, Any]]:
    row = _fetch_one(
        _supplier_sql("CAST(p.ProveedorID AS VARCHAR(50)) = %s"),
        (str(supplier_id),),
    )
    return _supplier_row_to_portal(row, include_password) if row else None


async def get_supplier_by_rfc(rfc: str, include_password: bool = False) -> Optional[Dict[str, Any]]:
    row = _fetch_one(
        _supplier_sql("UPPER(p.RFC) = UPPER(%s)"),
        (str(rfc),),
    )
    return _supplier_row_to_portal(row, include_password) if row else None


async def get_supplier_by_portal_user(
    usuario_portal_id: str,
    supplier_id: Optional[str] = None,
    include_password: bool = False,
) -> Optional[Dict[str, Any]]:
    where = ["CAST(u.UsuarioPortalID AS VARCHAR(50)) = %s"]
    params: List[str] = [str(usuario_portal_id)]

    if supplier_id:
        where.append("CAST(p.ProveedorID AS VARCHAR(50)) = %s")
        params.append(str(supplier_id))

    row = _fetch_one(_supplier_sql(" AND ".join(where)), tuple(params))
    return _supplier_row_to_portal(row, include_password) if row else None


async def list_suppliers(status: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
    where = ["p.Activo = 1"]
    if status == "pending":
        where.append("(p.PortalHabilitado = 0 OR p.PortalHabilitado IS NULL)")
    elif status == "approved":
        where.append("p.PortalHabilitado = 1")

    sql = _supplier_sql(" AND ".join(where), limit=limit, order_by="p.FechaAlta DESC")
    return [_supplier_row_to_portal(r, include_password=False) for r in _fetch_all(sql)]



async def update_supplier_portal_status(supplier_id: str, approved: bool) -> bool:
    affected = _execute("""
        UPDATE dbo.Proveedor_Catalogo
        SET PortalHabilitado = %s,
            FechaModificacion = SYSDATETIME()
        WHERE CAST(ProveedorID AS VARCHAR(50)) = %s
    """, (1 if approved else 0, str(supplier_id)))
    return affected > 0


async def update_supplier_password(
    supplier_id: str,
    password_hash: str,
    usuario_portal_id: Optional[str] = None,
) -> bool:
    where = ["CAST(ProveedorID AS VARCHAR(50)) = %s", "Activo = 1"]
    params: List[str] = [password_hash, str(supplier_id)]

    if usuario_portal_id:
        where.append("CAST(UsuarioPortalID AS VARCHAR(50)) = %s")
        params.append(str(usuario_portal_id))

    affected = _execute(f"""
        UPDATE dbo.Proveedor_UsuariosPortal
        SET PasswordHash = %s,
            FechaModificacion = SYSDATETIME()
        WHERE {' AND '.join(where)}
    """, tuple(params))
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


async def get_supplier_balances(
    supplier_id: str,
    supplier_rfc: Optional[str] = None,
    limit: int = 500,
) -> Dict[str, Any]:
    """
    Saldos CxP SQL-only del proveedor.
    Fuente canónica: dbo.Finanzas_CxP_Sync + dbo.Unidades_Negocio.
    No consulta Mongo ni servidores LIVE.
    """
    supplier_filters = ["CAST(c.ProveedorID AS VARCHAR(50)) = %s"]
    params = [str(supplier_id)]

    normalized_rfc = str(supplier_rfc or "").strip().upper()
    if normalized_rfc:
        supplier_filters.append("UPPER(LTRIM(RTRIM(c.ProveedorRFC))) = %s")
        params.append(normalized_rfc)

    sql = f"""
        SELECT TOP {int(limit)}
            c.CxpSyncID,
            c.HashOrigen,
            c.ProveedorID,
            c.ProveedorNombre,
            c.ProveedorRFC,
            c.UnidadNegocio,
            c.UnidadNegocioNombre,
            c.FolioEntrada,
            c.FolioFactura,
            c.FechaEntrada,
            c.FechaVencimiento,
            c.Referencia,
            c.MontoOriginal,
            c.Saldo,
            c.TipoProveedor,
            c.TipoProveedorNombre,
            c.Fuente,
            c.DiasVencido,
            CONVERT(varchar(36), u.id) AS UnidadNegocioIDCanonica,
            u.codigo AS UnidadNegocioCodigoCanonico,
            u.nombre AS UnidadNegocioNombreCanonico
        FROM dbo.Finanzas_CxP_Sync c
        INNER JOIN dbo.Unidades_Negocio u
            ON UPPER(LTRIM(RTRIM(c.UnidadNegocio))) = UPPER(LTRIM(RTRIM(u.codigo)))
           AND ISNULL(u.activo, 1) = 1
        WHERE ({' OR '.join(supplier_filters)})
          AND c.Activo = 1
          AND c.Saldo > 0
          AND ISNULL(c.EsDemo, 0) = 0
        ORDER BY c.FechaVencimiento ASC, c.FechaEntrada ASC
    """
    rows = _fetch_all(sql, tuple(params))

    facturas = []
    sucursales_map: Dict[str, Dict[str, Any]] = {}
    total_importe = 0.0
    total_pagado = 0.0
    total_saldo = 0.0

    for r in rows:
        importe = float(r.get("MontoOriginal") or 0)
        saldo = float(r.get("Saldo") or 0)
        pagado = max(0.0, importe - saldo)
        dias_vencido = int(r.get("DiasVencido") or 0)
        hash_origen = str(r.get("HashOrigen") or "").strip()
        cxp_sync_id = r.get("CxpSyncID")
        unidad_pk = str(
            r.get("UnidadNegocioIDCanonica")
            or r.get("UnidadNegocioCodigoCanonico")
            or r.get("UnidadNegocio")
            or "SIN_UNIDAD"
        )
        unidad_nombre = (
            r.get("UnidadNegocioNombreCanonico")
            or r.get("UnidadNegocioNombre")
            or r.get("UnidadNegocio")
            or "Sin unidad"
        )

        total_importe += importe
        total_pagado += pagado
        total_saldo += saldo

        sucursal = sucursales_map.setdefault(
            unidad_pk,
            {
                "id": unidad_pk,
                "name": unidad_nombre,
                "sistema_id": "EDARSAHUB_SQL",
                "system_type": "EDARSAHUB_SQL",
                "facturas": 0,
                "importe": 0.0,
                "pagado": 0.0,
                "saldo": 0.0,
            },
        )
        sucursal["facturas"] += 1
        sucursal["importe"] += importe
        sucursal["pagado"] += pagado
        sucursal["saldo"] += saldo

        folio = r.get("FolioFactura") or r.get("FolioEntrada") or r.get("Referencia") or ""
        documento = r.get("FolioEntrada") or r.get("Referencia") or str(cxp_sync_id or "")
        facturas.append({
            "cuenta_por_pagar_id": f"CXP_{hash_origen or cxp_sync_id}",
            "factura_sync_id": cxp_sync_id,
            "hash_origen": hash_origen or None,
            "documento_fiscal_id": None,
            "supplier_id": str(r.get("ProveedorID")),
            "supplier_rfc": r.get("ProveedorRFC") or "",
            "sucursal_id": unidad_pk,
            "sucursal": unidad_nombre,
            "unidad_negocio_pk": unidad_pk,
            "unidad_negocio_codigo": r.get("UnidadNegocioCodigoCanonico") or r.get("UnidadNegocio"),
            "folio": folio,
            "documento": documento,
            "referencia": r.get("Referencia") or str(cxp_sync_id or ""),
            "uuid": None,
            "fecha": str(r.get("FechaEntrada") or "")[:10],
            "vencimiento": str(r.get("FechaVencimiento") or "")[:10],
            "dias_vencido": dias_vencido,
            "importe": importe,
            "pagado": pagado,
            "saldo": saldo,
            "estatus_pago_id": None,
            "estatus": "Vencida" if dias_vencido > 0 else "Pendiente",
            "fuente": r.get("Fuente"),
        })

    sucursales = sorted(
        sucursales_map.values(),
        key=lambda item: item.get("saldo", 0),
        reverse=True,
    )

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
        "sucursales": sucursales,
        "facturas_pendientes": [f for f in facturas if f.get("saldo", 0) > 0],
        "totales": {
            "importe": total_importe,
            "pagado": total_pagado,
            "saldo": total_saldo,
            "facturas": len(facturas)
        },
        "source_type": "EDARSAHUB_SQL_CANONICO"
    }
