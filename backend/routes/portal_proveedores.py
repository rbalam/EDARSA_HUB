"""
Rutas del Portal de Proveedores
NO modifica nada de EDARSA HUB - Router completamente separado
Usa la misma conexión MongoDB y los servidores configurados en EDARSA HUB
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Header
from typing import Optional, List, Dict
from datetime import datetime, timezone
from passlib.context import CryptContext
import jwt
import uuid
import logging
import os
import xml.etree.ElementTree as ET
import base64

# Importar db desde server.py (se configurará en el registro del router)
db = None
JWT_SECRET = None
execute_sql_fn = None  # Función de ejecución SQL (se configurará desde server.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Router del Portal de Proveedores
portal_router = APIRouter(prefix="/portal", tags=["Portal Proveedores"])


def init_portal_db(database, jwt_secret, execute_sql_query_fn=None):
    """Inicializa la conexión a la base de datos para el portal"""
    global db, JWT_SECRET, execute_sql_fn
    db = database
    JWT_SECRET = jwt_secret
    execute_sql_fn = execute_sql_query_fn


def create_portal_token(data: dict):
    """Crea un JWT token para proveedores"""
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc).timestamp() + (24 * 60 * 60)  # 24 horas
    to_encode["type"] = "portal_supplier"
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")


async def get_current_supplier(authorization: Optional[str] = Header(None)):
    """Obtiene el proveedor actual desde el token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        if payload.get("type") != "portal_supplier":
            raise HTTPException(status_code=401, detail="Token inválido para portal")
        
        supplier_id = payload.get("supplier_id")
        supplier = await db.portal_suppliers.find_one({"id": supplier_id}, {"_id": 0})
        
        if not supplier:
            raise HTTPException(status_code=401, detail="Proveedor no encontrado")
        
        if supplier.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="Cuenta suspendida")
        
        return supplier
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


# ============================================================================
# AUTENTICACIÓN
# ============================================================================

@portal_router.post("/auth/register")
async def register_supplier(data: dict):
    """Registro de nuevo proveedor"""
    rfc = data.get("rfc", "").upper().strip()
    
    if not rfc or len(rfc) < 12:
        raise HTTPException(status_code=400, detail="RFC inválido")
    
    # Verificar si ya existe
    existing = await db.portal_suppliers.find_one({"rfc": rfc})
    if existing:
        raise HTTPException(status_code=400, detail="Este RFC ya está registrado")
    
    # Crear proveedor
    supplier_id = str(uuid.uuid4())
    hashed_password = pwd_context.hash(data.get("password", ""))
    
    supplier = {
        "id": supplier_id,
        "rfc": rfc,
        "razon_social": data.get("razon_social", ""),
        "nombre_contacto": data.get("nombre_contacto", ""),
        "email": data.get("email", ""),
        "telefono": data.get("telefono", ""),
        "password": hashed_password,
        "banco": data.get("banco", ""),
        "clabe": data.get("clabe", ""),
        "cuenta": data.get("cuenta", ""),
        "status": "pending",  # Requiere aprobación
        "sucursales_asignadas": [],
        "created_at": datetime.now(timezone.utc),
        "approved_at": None,
        "approved_by": None
    }
    
    await db.portal_suppliers.insert_one(supplier)
    
    # No devolver password
    del supplier["password"]
    
    return {
        "message": "Registro exitoso. Tu cuenta está pendiente de aprobación.",
        "supplier_id": supplier_id
    }


@portal_router.post("/auth/login")
async def login_supplier(data: dict):
    """Login de proveedor por RFC"""
    rfc = data.get("rfc", "").upper().strip()
    password = data.get("password", "")
    
    supplier = await db.portal_suppliers.find_one({"rfc": rfc}, {"_id": 0})
    
    if not supplier:
        raise HTTPException(status_code=401, detail="RFC o contraseña incorrectos")
    
    if not pwd_context.verify(password, supplier.get("password", "")):
        raise HTTPException(status_code=401, detail="RFC o contraseña incorrectos")
    
    if supplier.get("status") == "pending":
        raise HTTPException(status_code=403, detail="Tu cuenta está pendiente de aprobación")
    
    if supplier.get("status") == "rejected":
        raise HTTPException(status_code=403, detail="Tu cuenta fue rechazada")
    
    if supplier.get("status") == "suspended":
        raise HTTPException(status_code=403, detail="Tu cuenta está suspendida")
    
    # Crear token
    token = create_portal_token({
        "supplier_id": supplier["id"],
        "rfc": supplier["rfc"]
    })
    
    # No devolver password
    supplier_data = {k: v for k, v in supplier.items() if k != "password"}
    
    return {
        "token": token,
        "supplier": supplier_data
    }


@portal_router.get("/auth/me")
async def get_supplier_profile(current_supplier: dict = Depends(get_current_supplier)):
    """Obtiene el perfil del proveedor actual"""
    return {k: v for k, v in current_supplier.items() if k != "password"}


# ============================================================================
# FACTURAS
# ============================================================================

@portal_router.get("/invoices")
async def get_supplier_invoices(
    status: Optional[str] = None,
    current_supplier: dict = Depends(get_current_supplier)
):
    """Obtiene las facturas del proveedor"""
    query = {"supplier_id": current_supplier["id"]}
    
    if status:
        query["status"] = status
    
    invoices = await db.portal_invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    return invoices


@portal_router.post("/invoices/upload")
async def upload_invoice(
    xml_file: UploadFile = File(...),
    pdf_file: Optional[UploadFile] = File(None),
    current_supplier: dict = Depends(get_current_supplier)
):
    """Sube una factura XML (y opcionalmente PDF)"""
    
    if current_supplier.get("status") != "approved":
        raise HTTPException(status_code=403, detail="Tu cuenta debe estar aprobada para subir facturas")
    
    # Leer XML
    xml_content = await xml_file.read()
    
    try:
        # Parsear XML CFDI
        root = ET.fromstring(xml_content)
        
        # Namespace de CFDI 4.0
        ns = {
            'cfdi': 'http://www.sat.gob.mx/cfd/4',
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
        }
        
        # Intentar CFDI 3.3 si no funciona 4.0
        if root.tag != '{http://www.sat.gob.mx/cfd/4}Comprobante':
            ns['cfdi'] = 'http://www.sat.gob.mx/cfd/3'
        
        # Extraer datos
        uuid_elem = root.find('.//tfd:TimbreFiscalDigital', ns)
        uuid_cfdi = uuid_elem.get('UUID') if uuid_elem is not None else None
        
        if not uuid_cfdi:
            raise HTTPException(status_code=400, detail="No se encontró UUID en el XML")
        
        # Verificar si ya existe
        existing = await db.portal_invoices.find_one({"uuid": uuid_cfdi.upper()})
        if existing:
            raise HTTPException(status_code=400, detail="Esta factura ya fue subida anteriormente")
        
        # Extraer más datos
        emisor = root.find('cfdi:Emisor', ns)
        receptor = root.find('cfdi:Receptor', ns)
        
        emisor_rfc = emisor.get('Rfc') if emisor is not None else None
        
        # Verificar que el RFC del emisor coincida con el proveedor
        if emisor_rfc and emisor_rfc.upper() != current_supplier["rfc"]:
            raise HTTPException(
                status_code=400, 
                detail=f"El RFC del emisor ({emisor_rfc}) no coincide con tu RFC ({current_supplier['rfc']})"
            )
        
        # Crear registro de factura
        invoice_id = str(uuid.uuid4())
        
        invoice = {
            "id": invoice_id,
            "supplier_id": current_supplier["id"],
            "supplier_rfc": current_supplier["rfc"],
            "uuid": uuid_cfdi.upper(),
            "serie": root.get('Serie', ''),
            "folio": root.get('Folio', ''),
            "fecha_emision": root.get('Fecha', ''),
            "subtotal": float(root.get('SubTotal', 0)),
            "iva": 0,  # Se calculará
            "total": float(root.get('Total', 0)),
            "moneda": root.get('Moneda', 'MXN'),
            "tipo_comprobante": root.get('TipoDeComprobante', 'I'),
            "receptor_rfc": receptor.get('Rfc') if receptor is not None else None,
            "receptor_nombre": receptor.get('Nombre') if receptor is not None else None,
            "status": "uploaded",
            "xml_content": base64.b64encode(xml_content).decode('utf-8'),
            "pdf_content": None,
            "orden_compra": None,
            "sucursal": None,
            "created_at": datetime.now(timezone.utc),
            "validated_at": None,
            "matched_at": None
        }
        
        # Guardar PDF si existe
        if pdf_file:
            pdf_content = await pdf_file.read()
            invoice["pdf_content"] = base64.b64encode(pdf_content).decode('utf-8')
        
        await db.portal_invoices.insert_one(invoice)
        
        # No devolver contenido de archivos en respuesta
        response_invoice = {k: v for k, v in invoice.items() if k not in ["xml_content", "pdf_content"]}
        
        return {
            "message": "Factura subida exitosamente",
            "invoice": response_invoice
        }
        
    except ET.ParseError:
        raise HTTPException(status_code=400, detail="El archivo XML no es válido")
    except Exception as e:
        logging.error(f"Error procesando factura: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando factura: {str(e)}")


@portal_router.get("/invoices/{invoice_id}")
async def get_invoice_detail(
    invoice_id: str,
    current_supplier: dict = Depends(get_current_supplier)
):
    """Obtiene detalle de una factura"""
    invoice = await db.portal_invoices.find_one({
        "id": invoice_id,
        "supplier_id": current_supplier["id"]
    }, {"_id": 0, "xml_content": 0, "pdf_content": 0})
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    return invoice


# ============================================================================
# ÓRDENES DE COMPRA (usando conexiones de EDARSA HUB)
# ============================================================================

@portal_router.get("/purchase-orders")
async def get_purchase_orders(
    current_supplier: dict = Depends(get_current_supplier)
):
    """Obtiene las órdenes de compra del proveedor desde los servidores configurados"""
    
    if current_supplier.get("status") != "approved":
        raise HTTPException(status_code=403, detail="Cuenta no aprobada")
    
    sucursales = current_supplier.get("sucursales_asignadas", [])
    
    if not sucursales:
        return []
    
    # Buscar el código de proveedor en los sistemas
    # Por ahora devolvemos vacío - se implementará la consulta a SQL Server
    # usando las conexiones de EDARSA HUB
    
    return {
        "message": "Funcionalidad en desarrollo",
        "sucursales_asignadas": sucursales,
        "orders": []
    }


# ============================================================================
# ESTADO DE CUENTA
# ============================================================================

@portal_router.get("/account-status")
async def get_account_status(
    current_supplier: dict = Depends(get_current_supplier)
):
    """Obtiene el estado de cuenta del proveedor"""
    
    if current_supplier.get("status") != "approved":
        raise HTTPException(status_code=403, detail="Cuenta no aprobada")
    
    # Resumen de facturas
    invoices = await db.portal_invoices.find({
        "supplier_id": current_supplier["id"]
    }, {"_id": 0}).to_list(1000)
    
    total_uploaded = len(invoices)
    total_matched = len([i for i in invoices if i.get("status") == "matched"])
    total_paid = len([i for i in invoices if i.get("status") == "paid"])
    
    sum_total = sum(i.get("total", 0) for i in invoices)
    sum_paid = sum(i.get("total", 0) for i in invoices if i.get("status") == "paid")
    
    return {
        "rfc": current_supplier["rfc"],
        "razon_social": current_supplier["razon_social"],
        "resumen": {
            "facturas_subidas": total_uploaded,
            "facturas_conciliadas": total_matched,
            "facturas_pagadas": total_paid,
            "total_facturado": sum_total,
            "total_pagado": sum_paid,
            "saldo_pendiente": sum_total - sum_paid
        }
    }


# ============================================================================
# SALDOS REALES (consulta a SQL Server de EDARSA HUB)
# ============================================================================

@portal_router.get("/saldos")
async def get_saldos_proveedor(
    current_supplier: dict = Depends(get_current_supplier)
):
    """
    Obtiene los saldos del proveedor desde los servidores SQL Server configurados.
    Agrupa por servidor y sucursal.
    """
    if current_supplier.get("status") != "approved":
        raise HTTPException(status_code=403, detail="Cuenta no aprobada")
    
    if not execute_sql_fn:
        raise HTTPException(status_code=500, detail="Función SQL no configurada")
    
    rfc_proveedor = current_supplier["rfc"]
    
    # Obtener solo servidores activos Y visibles en operaciones
    # Si visible_en_operaciones no está definido, asumimos True (visible por defecto)
    # Si está definido como False, no se muestra
    servers = await db.servers.find({
        "active": True,
        "$or": [
            {"visible_en_operaciones": True},
            {"visible_en_operaciones": {"$exists": False}}
        ]
    }, {"_id": 0}).to_list(50)
    
    # Filtrar también por system_type válidos (MPRO o SoftRestaurant)
    servers = [s for s in servers if s.get("system_type") in ["MPRO", "SoftRestaurant"]]
    
    if not servers:
        return {
            "sistemas": [],
            "sucursales": [],
            "facturas_pendientes": [],
            "totales": {"importe": 0, "pagado": 0, "saldo": 0, "facturas": 0}
        }
    
    sistemas_data = []
    sucursales_data = []
    facturas_pendientes = []
    
    for server in servers:
        server_name = server.get("name", "Desconocido")
        system_type = server.get("system_type", "UNKNOWN")
        
        try:
            if system_type == 'MPRO':
                # MPRO: Consultar saldos desde tabla Movimiento
                # Buscar el código de proveedor por RFC
                # Columnas correctas: Pv_R_F_C y Pv_Razon_Social
                query_proveedor = f"""
                SELECT TOP 1 Pv_Cve_Proveedor as codigo, Pv_Razon_Social as nombre
                FROM Proveedor 
                WHERE Pv_R_F_C = '{rfc_proveedor}'
                """
                
                prov_result = execute_sql_fn(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_proveedor
                )
                
                if not prov_result:
                    # Proveedor no encontrado en este servidor
                    sistemas_data.append({
                        "id": server['id'],
                        "name": server_name,
                        "system_type": system_type,
                        "facturas": 0,
                        "importe": 0,
                        "pagado": 0,
                        "saldo": 0,
                        "status": "not_found"
                    })
                    continue
                
                codigo_proveedor = prov_result[0]['codigo']
                
                # Obtener saldos por sucursal usando tabla Cuenta_X_Pagar
                # Sucursales en MPRO vienen de la tabla Sucursal
                query_sucursales = f"""
                SELECT 
                    S.Sc_Cve_Sucursal as sucursal_id,
                    S.Sc_Descripcion as sucursal,
                    COUNT(DISTINCT C.Cxp_Documento) as facturas,
                    ISNULL(SUM(C.Cxp_Precio_Neto_Importe), 0) as importe,
                    ISNULL(SUM(C.Cxp_Precio_Neto_Pago), 0) as pagado,
                    ISNULL(SUM(C.Cxp_Precio_Neto_Saldo), 0) as saldo
                FROM Cuenta_X_Pagar C
                INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = C.Sc_Cve_Sucursal
                WHERE C.Pv_Cve_Proveedor = '{codigo_proveedor}'
                    AND C.Es_Cve_Estado <> 'CA'
                GROUP BY S.Sc_Cve_Sucursal, S.Sc_Descripcion
                HAVING SUM(C.Cxp_Precio_Neto_Saldo) > 0 OR SUM(C.Cxp_Precio_Neto_Importe) > 0
                ORDER BY SUM(C.Cxp_Precio_Neto_Saldo) DESC
                """
                
                suc_result = execute_sql_fn(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_sucursales
                )
                
                total_facturas = 0
                total_importe = 0
                total_pagado = 0
                total_saldo = 0
                
                for suc in (suc_result or []):
                    facturas = int(suc['facturas'] or 0)
                    importe = float(suc['importe'] or 0)
                    pagado = float(suc['pagado'] or 0)
                    saldo = float(suc['saldo'] or 0)
                    
                    sucursales_data.append({
                        "id": f"{server['id']}_{suc['sucursal_id']}",
                        "name": suc['sucursal'],
                        "sistema": server_name,
                        "sistema_id": server['id'],
                        "system_type": system_type,
                        "facturas": facturas,
                        "importe": importe,
                        "pagado": pagado,
                        "saldo": saldo
                    })
                    
                    total_facturas += facturas
                    total_importe += importe
                    total_pagado += pagado
                    total_saldo += saldo
                
                # Obtener facturas pendientes con detalle desde Cuenta_X_Pagar
                query_facturas = f"""
                SELECT TOP 50
                    S.Sc_Descripcion as sucursal,
                    C.Cxp_Documento as folio,
                    LEFT(C.Cxp_Referencia, 8) as referencia,
                    C.Cxp_Documento as documento,
                    C.Cxp_Fecha as fecha,
                    C.Cxp_Fecha_Vencimiento as vencimiento,
                    DATEDIFF(DAY, C.Cxp_Fecha_Vencimiento, GETDATE()) as dias_vencido,
                    C.Cxp_Precio_Neto_Importe as importe,
                    C.Cxp_Precio_Neto_Saldo as saldo
                FROM Cuenta_X_Pagar C
                INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = C.Sc_Cve_Sucursal
                WHERE C.Pv_Cve_Proveedor = '{codigo_proveedor}'
                    AND C.Es_Cve_Estado <> 'CA'
                    AND C.Cxp_Precio_Neto_Saldo > 0
                ORDER BY S.Sc_Descripcion, C.Cxp_Fecha
                """
                
                fact_result = execute_sql_fn(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_facturas
                )
                
                for fact in (fact_result or []):
                    facturas_pendientes.append({
                        "sucursal": fact['sucursal'],
                        "sistema": server_name,
                        "sistema_id": server['id'],
                        "folio": fact['folio'],
                        "referencia": fact['referencia'] or '',
                        "documento": fact['documento'],
                        "fecha": str(fact['fecha'])[:10] if fact['fecha'] else '',
                        "vencimiento": str(fact['vencimiento'])[:10] if fact['vencimiento'] else '',
                        "dias_vencido": int(fact['dias_vencido'] or 0),
                        "importe": float(fact['importe'] or 0),
                        "saldo": float(fact['saldo'] or 0)
                    })
                
                sistemas_data.append({
                    "id": server['id'],
                    "name": server_name,
                    "system_type": system_type,
                    "facturas": total_facturas,
                    "importe": total_importe,
                    "pagado": total_pagado,
                    "saldo": total_saldo,
                    "status": "connected"
                })
                
            elif system_type == 'SoftRestaurant':
                # SoftRestaurant: Consultar saldos desde tabla compras
                # Columnas correctas: cancelado (no cancelada), total (no importetotal)
                # El status de pago se determina con JOIN a pagosproveedores
                query_proveedor = f"""
                SELECT TOP 1 idproveedor as codigo, nombre
                FROM proveedores 
                WHERE rfc = '{rfc_proveedor}'
                """
                
                prov_result = execute_sql_fn(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_proveedor
                )
                
                if not prov_result:
                    sistemas_data.append({
                        "id": server['id'],
                        "name": server_name,
                        "system_type": system_type,
                        "facturas": 0,
                        "importe": 0,
                        "pagado": 0,
                        "saldo": 0,
                        "status": "not_found"
                    })
                    continue
                
                id_proveedor = prov_result[0]['codigo']
                
                # SoftRestaurant no tiene sucursales típicamente (es monobranch)
                # pero obtenemos los totales
                # Columnas: cancelado (puede ser NULL), total; pagos en tabla pagosproveedores (JOIN por idcompra)
                query_totales = f"""
                SELECT 
                    COUNT(DISTINCT c.idcompra) as facturas,
                    ISNULL(SUM(c.total), 0) as importe,
                    ISNULL((
                        SELECT SUM(p.abono) 
                        FROM pagosproveedores p 
                        INNER JOIN compras c2 ON p.foliocompra = c2.idcompra
                        WHERE c2.idproveedor = '{id_proveedor}' AND ISNULL(c2.cancelado, 0) = 0
                    ), 0) as pagado,
                    ISNULL(SUM(c.total), 0) - ISNULL((
                        SELECT SUM(p.abono) 
                        FROM pagosproveedores p 
                        INNER JOIN compras c2 ON p.foliocompra = c2.idcompra
                        WHERE c2.idproveedor = '{id_proveedor}' AND ISNULL(c2.cancelado, 0) = 0
                    ), 0) as saldo
                FROM compras c
                WHERE c.idproveedor = '{id_proveedor}'
                    AND ISNULL(c.cancelado, 0) = 0
                """
                
                tot_result = execute_sql_fn(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_totales
                )
                
                if tot_result:
                    total_facturas = int(tot_result[0]['facturas'] or 0)
                    total_importe = float(tot_result[0]['importe'] or 0)
                    total_pagado = float(tot_result[0]['pagado'] or 0)
                    total_saldo = float(tot_result[0]['saldo'] or 0)
                    
                    # Agregar como una sola "sucursal"
                    sucursales_data.append({
                        "id": f"{server['id']}_main",
                        "name": server_name,
                        "sistema": server_name,
                        "sistema_id": server['id'],
                        "system_type": system_type,
                        "facturas": total_facturas,
                        "importe": total_importe,
                        "pagado": total_pagado,
                        "saldo": total_saldo
                    })
                    
                    sistemas_data.append({
                        "id": server['id'],
                        "name": server_name,
                        "system_type": system_type,
                        "facturas": total_facturas,
                        "importe": total_importe,
                        "pagado": total_pagado,
                        "saldo": total_saldo,
                        "status": "connected"
                    })
                    
                    # Facturas pendientes - SoftRestaurant
                    # Columnas: foliofactura, total, cancelado, referencia
                    # Saldo = total - abonos de pagosproveedores (JOIN por idcompra)
                    query_facturas = f"""
                    SELECT TOP 50
                        '{server_name}' as sucursal,
                        c.foliofactura as folio,
                        LEFT(c.referencia, 8) as referencia,
                        c.foliofactura as documento,
                        c.fechaaplicacion as fecha,
                        ISNULL(c.fechavencimiento, DATEADD(DAY, 30, c.fechaaplicacion)) as vencimiento,
                        DATEDIFF(DAY, ISNULL(c.fechavencimiento, DATEADD(DAY, 30, c.fechaaplicacion)), GETDATE()) as dias_vencido,
                        c.total as importe,
                        c.total - ISNULL((SELECT SUM(p.abono) FROM pagosproveedores p WHERE p.foliocompra = c.idcompra), 0) as saldo
                    FROM compras c
                    WHERE c.idproveedor = '{id_proveedor}'
                        AND ISNULL(c.cancelado, 0) = 0
                        AND c.total - ISNULL((SELECT SUM(p.abono) FROM pagosproveedores p WHERE p.foliocompra = c.idcompra), 0) > 0
                    ORDER BY c.fechaaplicacion
                    """
                    
                    fact_result = execute_sql_fn(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_facturas
                    )
                    
                    for fact in (fact_result or []):
                        facturas_pendientes.append({
                            "sucursal": fact['sucursal'],
                            "sistema": server_name,
                            "sistema_id": server['id'],
                            "folio": fact['folio'] or '',
                            "referencia": fact['referencia'] or '',
                            "documento": fact['documento'] or '',
                            "fecha": str(fact['fecha'])[:10] if fact['fecha'] else '',
                            "vencimiento": str(fact['vencimiento'])[:10] if fact['vencimiento'] else '',
                            "dias_vencido": int(fact['dias_vencido'] or 0),
                            "importe": float(fact['importe'] or 0),
                            "saldo": float(fact['saldo'] or 0)
                        })
                else:
                    sistemas_data.append({
                        "id": server['id'],
                        "name": server_name,
                        "system_type": system_type,
                        "facturas": 0,
                        "importe": 0,
                        "pagado": 0,
                        "saldo": 0,
                        "status": "not_found"
                    })
                    
        except Exception as e:
            logging.error(f"Error consultando saldos de {server_name}: {str(e)}")
            sistemas_data.append({
                "id": server['id'],
                "name": server_name,
                "system_type": system_type,
                "facturas": 0,
                "importe": 0,
                "pagado": 0,
                "saldo": 0,
                "status": "error",
                "error": str(e)
            })
    
    # Calcular totales generales
    total_importe = sum(s['importe'] for s in sistemas_data)
    total_pagado = sum(s['pagado'] for s in sistemas_data)
    total_saldo = sum(s['saldo'] for s in sistemas_data)
    total_facturas = sum(s['facturas'] for s in sistemas_data)
    
    return {
        "sistemas": sistemas_data,
        "sucursales": sucursales_data,
        "facturas_pendientes": facturas_pendientes,
        "totales": {
            "importe": total_importe,
            "pagado": total_pagado,
            "saldo": total_saldo,
            "facturas": total_facturas
        }
    }



# ============================================================================
# ADMINISTRACIÓN (para usuarios de EDARSA HUB)
# ============================================================================

@portal_router.get("/admin/pending-suppliers")
async def get_pending_suppliers():
    """Obtiene proveedores pendientes de aprobación (para admins de EDARSA HUB)"""
    suppliers = await db.portal_suppliers.find(
        {"status": "pending"}, 
        {"_id": 0, "password": 0}
    ).sort("created_at", -1).to_list(100)
    
    return suppliers


@portal_router.get("/admin/all-suppliers")
async def get_all_suppliers():
    """Obtiene todos los proveedores (para admins de EDARSA HUB)"""
    suppliers = await db.portal_suppliers.find(
        {}, 
        {"_id": 0, "password": 0}
    ).sort("created_at", -1).to_list(500)
    
    return suppliers


@portal_router.post("/admin/approve-supplier")
async def approve_supplier(data: dict):
    """Aprueba o rechaza un proveedor"""
    supplier_id = data.get("supplier_id")
    action = data.get("action")  # "approve" o "reject"
    sucursales = data.get("sucursales", [])
    notes = data.get("notes", "")
    approved_by = data.get("approved_by", "admin")
    
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Acción inválida")
    
    supplier = await db.portal_suppliers.find_one({"id": supplier_id})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    update_data = {
        "status": "approved" if action == "approve" else "rejected",
        "approved_at": datetime.now(timezone.utc),
        "approved_by": approved_by,
        "approval_notes": notes
    }
    
    if action == "approve":
        update_data["sucursales_asignadas"] = sucursales
    
    await db.portal_suppliers.update_one(
        {"id": supplier_id},
        {"$set": update_data}
    )
    
    return {"message": f"Proveedor {'aprobado' if action == 'approve' else 'rechazado'} exitosamente"}


@portal_router.post("/admin/reset-password")
async def admin_reset_supplier_password(data: dict):
    """
    Resetea/establece la contraseña de un proveedor.
    Solo para administradores de EDARSA HUB.
    
    Body:
        - supplier_id: ID del proveedor (opcional si se usa rfc)
        - rfc: RFC del proveedor (opcional si se usa supplier_id)
        - new_password: Nueva contraseña en texto plano
        - reset_by: Email/nombre del admin que hace el reset
    """
    supplier_id = data.get("supplier_id")
    rfc = data.get("rfc", "").upper().strip()
    new_password = data.get("new_password", "").strip()
    reset_by = data.get("reset_by", "admin")
    
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    
    # Buscar proveedor por ID o RFC
    query = {}
    if supplier_id:
        query["id"] = supplier_id
    elif rfc:
        query["rfc"] = rfc
    else:
        raise HTTPException(status_code=400, detail="Debe proporcionar supplier_id o rfc")
    
    supplier = await db.portal_suppliers.find_one(query)
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    # Hashear nueva contraseña
    hashed_password = pwd_context.hash(new_password)
    
    # Actualizar contraseña
    await db.portal_suppliers.update_one(
        {"id": supplier["id"]},
        {
            "$set": {
                "password": hashed_password,
                "password_reset_at": datetime.now(timezone.utc),
                "password_reset_by": reset_by
            }
        }
    )
    
    return {
        "message": "Contraseña actualizada exitosamente",
        "supplier_rfc": supplier["rfc"],
        "supplier_razon_social": supplier.get("razon_social", ""),
        "new_password": new_password,  # Devolver para que el admin la comunique
        "reset_by": reset_by,
        "reset_at": datetime.now(timezone.utc).isoformat()
    }


@portal_router.get("/admin/supplier/{identifier}")
async def admin_get_supplier_details(identifier: str):
    """
    Obtiene detalles completos de un proveedor por ID o RFC.
    Útil para ver información antes de resetear contraseña.
    """
    # Buscar por ID primero, luego por RFC
    supplier = await db.portal_suppliers.find_one({"id": identifier}, {"_id": 0, "password": 0})
    
    if not supplier:
        supplier = await db.portal_suppliers.find_one(
            {"rfc": identifier.upper()}, 
            {"_id": 0, "password": 0}
        )
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    return supplier


@portal_router.get("/admin/invoices")
async def admin_get_all_invoices(
    status: Optional[str] = None,
    supplier_rfc: Optional[str] = None
):
    """Obtiene todas las facturas (para admins de EDARSA HUB)"""
    query = {}
    
    if status:
        query["status"] = status
    if supplier_rfc:
        query["supplier_rfc"] = supplier_rfc.upper()
    
    invoices = await db.portal_invoices.find(
        query, 
        {"_id": 0, "xml_content": 0, "pdf_content": 0}
    ).sort("created_at", -1).to_list(500)
    
    return invoices


# ============================================================================
# SERVIDORES DISPONIBLES (usa los de EDARSA HUB)
# ============================================================================

@portal_router.get("/servers")
async def get_available_servers():
    """Obtiene los servidores disponibles (de EDARSA HUB)"""
    servers = await db.servers.find(
        {"active": True}, 
        {"_id": 0, "id": 1, "name": 1, "system_type": 1}
    ).to_list(50)
    
    return servers


@portal_router.delete("/admin/supplier/{supplier_id}")
async def delete_supplier(supplier_id: str):
    """
    Elimina un proveedor del portal.
    Solo para administradores de EDARSA HUB.
    """
    # Buscar proveedor
    supplier = await db.portal_suppliers.find_one({"id": supplier_id})
    
    if not supplier:
        # Intentar buscar por RFC
        supplier = await db.portal_suppliers.find_one({"rfc": supplier_id.upper()})
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    # Eliminar el proveedor
    result = await db.portal_suppliers.delete_one({"id": supplier["id"]})
    
    if result.deleted_count > 0:
        return {
            "message": "Proveedor eliminado exitosamente",
            "rfc": supplier.get("rfc"),
            "razon_social": supplier.get("razon_social")
        }
    else:
        raise HTTPException(status_code=500, detail="Error al eliminar proveedor")
