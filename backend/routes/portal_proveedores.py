"""
Rutas del Portal de Proveedores
NO modifica nada de EDARSA HUB - Router completamente separado
SQL-only: usa tablas canónicas EDARSA HUB; MongoDB/LIVE deshabilitado

FASE AUTH-SECURITY-01 / FASE 3:
- Cookie httpOnly separada: edarsa_portal_access_token
- Soporte dual: Header Authorization O Cookie
- Endpoint /auth/logout agregado

P0-PORTAL-PROVEEDORES-AUTH-01:
- Endpoints /admin/* protegidos con autenticación interna EDARSA HUB
- Requiere rol SuperAdministrador o Administrador para acceso admin
- Proveedor externo NO puede acceder a endpoints admin
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Header, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict
from datetime import datetime, timezone
import warnings
# Suprimir DeprecationWarning de passlib sobre módulo 'crypt' (Python 3.13)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="passlib")
    from passlib.context import CryptContext
import jwt
import uuid
import logging
import os
import xml.etree.ElementTree as ET
import base64

logger = logging.getLogger(__name__)

from routes import portal_proveedores_repository_sql as portal_sql

# P0-PORTAL-PROVEEDORES-AUTH-01: Importar autenticación interna EDARSA HUB
from core.security import get_current_user

# Importar db desde server.py (se configurará en el registro del router)
db = None
JWT_SECRET = None
execute_sql_fn = None  # Función de ejecución SQL (se configurará desde server.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================================
# P0-PORTAL-PROVEEDORES-AUTH-01: Helper para endpoints admin
# P5-10B: Incluir variantes de nombres de rol (SQL usa SUPERADMIN, legacy usa SuperAdministrador)
# ============================================================================
ADMIN_ROLES = ['SuperAdministrador', 'Administrador', 'SUPERADMIN', 'ADMIN', 'ADMINISTRADOR']


async def require_portal_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True))
) -> dict:
    """
    Dependency para endpoints admin del Portal de Proveedores.
    
    Requiere:
    1. Token JWT válido de usuario interno EDARSA HUB
    2. Rol SuperAdministrador o Administrador
    
    Rechaza:
    - Usuarios no autenticados (401)
    - Tokens de proveedor externo (type=portal_supplier) (401)
    - Usuarios internos sin rol admin (403)
    
    Returns:
        dict: Datos del usuario autenticado
        
    Raises:
        HTTPException 401: No autenticado, token inválido, o token de proveedor
        HTTPException 403: Usuario sin permiso administrativo
    """
    from core.security import verify_token, get_db
    
    # 1. Verificar y decodificar token
    try:
        token = credentials.credentials
        payload = verify_token(token)
    except HTTPException:
        raise HTTPException(
            status_code=401,
            detail="Token de autenticación inválido o expirado"
        )
    
    # 2. Rechazar tokens de proveedor externo
    token_type = payload.get('type', 'internal')
    if token_type == 'portal_supplier':
        logging.warning(
            f"[PORTAL-ADMIN] Token de proveedor rechazado. "
            f"RFC: {payload.get('rfc', '?')}, supplier_id: {payload.get('supplier_id', '?')}"
        )
        raise HTTPException(
            status_code=401,
            detail={
                "error": "TOKEN_TIPO_INVALIDO",
                "mensaje": "Este endpoint requiere autenticación de usuario interno EDARSA HUB. "
                           "Los proveedores externos no pueden acceder a funciones administrativas."
            }
        )
    
    # 3. Extraer información del usuario desde el token (modo SQL)
    user_email = payload.get('email')
    user_role = payload.get('role', '')
    user_id = payload.get('user_id')
    
    if not user_email:
        raise HTTPException(
            status_code=401,
            detail="Token inválido: falta información de usuario"
        )
    
    # Construir objeto de usuario desde el payload del token
    user = {
        'id': user_id,
        'email': user_email,
        'role': user_role,
        'nombre': payload.get('nombre', user_email.split('@')[0])
    }
    
    # 4. Verificar rol administrativo
    if user_role not in ADMIN_ROLES:
        logging.warning(
            f"[PORTAL-ADMIN] Acceso denegado: Usuario {user_email} "
            f"con rol '{user_role}' intentó acceder a endpoint admin"
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "PERMISO_DENEGADO",
                "mensaje": "Se requiere rol administrativo para acceder al Portal de Proveedores Admin",
                "rol_actual": user_role,
                "roles_permitidos": ADMIN_ROLES
            }
        )
    
    logging.info(f"[PORTAL-ADMIN] Acceso permitido: {user_email} ({user_role})")
    return user

# Router del Portal de Proveedores
portal_router = APIRouter(prefix="/portal", tags=["Portal Proveedores"])

# ============================================================================
# FASE AUTH-SECURITY-01: Configuración de cookies para portal
# ============================================================================
PORTAL_COOKIE_NAME = "edarsa_portal_access_token"
PORTAL_COOKIE_MAX_AGE = 24 * 60 * 60  # 24 horas (igual que token portal actual)


def set_portal_auth_cookie(response: Response, token: str) -> None:
    """
    Establece la cookie httpOnly para el portal de proveedores.
    Cookie separada de usuarios internos.
    """
    is_production = os.environ.get("ENV", "production").lower() == "production"
    
    response.set_cookie(
        key=PORTAL_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/api/portal",  # Solo para endpoints del portal
        max_age=PORTAL_COOKIE_MAX_AGE
    )


def clear_portal_auth_cookie(response: Response) -> None:
    """Elimina la cookie del portal de proveedores."""
    response.delete_cookie(
        key=PORTAL_COOKIE_NAME,
        path="/api/portal"
    )


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
    """
    Obtiene el proveedor actual desde el token (método legacy via header).
    Mantiene compatibilidad con código existente.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        if payload.get("type") != "portal_supplier":
            raise HTTPException(status_code=401, detail="Token inválido para portal")
        
        supplier_id = payload.get("supplier_id")
        supplier = await portal_sql.get_supplier_by_id(supplier_id)
        
        if not supplier:
            raise HTTPException(status_code=401, detail="Proveedor no encontrado")
        
        if supplier.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="Cuenta suspendida")
        
        return supplier
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


async def get_current_supplier_dual(request: Request):
    """
    FASE AUTH-SECURITY-01: Obtiene proveedor desde Header O Cookie.
    Prioridad: Header > Cookie > 401
    FASE 4: Ignora tokens inválidos (null, undefined) para fallback a cookie
    """
    token = None
    
    # Prioridad 1: Header Authorization
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        extracted_token = auth_header.replace("Bearer ", "").strip()
        # Ignorar tokens inválidos del frontend legacy
        if extracted_token and extracted_token not in ("null", "undefined", ""):
            token = extracted_token
    
    # Prioridad 2: Cookie del portal
    if not token:
        token = request.cookies.get(PORTAL_COOKIE_NAME)
    
    # Sin autenticación
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        if payload.get("type") != "portal_supplier":
            raise HTTPException(status_code=401, detail="Token inválido para portal")
        
        supplier_id = payload.get("supplier_id")
        supplier = await portal_sql.get_supplier_by_id(supplier_id)
        
        if not supplier:
            raise HTTPException(status_code=401, detail="Proveedor no encontrado")
        
        if supplier.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="Cuenta suspendida")
        
        return supplier
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


async def get_supplier_dual_dep(request: Request) -> dict:
    """Dependencia wrapper para usar con Depends()."""
    return await get_current_supplier_dual(request)


# ============================================================================
# AUTENTICACIÓN
# ============================================================================

@portal_router.post("/auth/register")
async def register_supplier(data: dict):
    """
    SQL-only guardrail.
    El alta debe implementarse contra Proveedor_Catalogo y Proveedor_UsuariosPortal.
    """
    rfc = data.get("rfc", "").upper().strip()

    if not rfc or len(rfc) < 12:
        raise HTTPException(status_code=400, detail="RFC inválido")

    raise HTTPException(
        status_code=501,
        detail="Registro de proveedores pendiente de flujo SQL canónico con Proveedor_Catalogo y Proveedor_UsuariosPortal."
    )

@portal_router.post("/auth/login")
async def login_supplier(data: dict, response: Response):
    """
    Login de proveedor por RFC.
    
    FASE AUTH-SECURITY-01:
    - Retorna {token, supplier} para compatibilidad con frontend actual
    - TAMBIÉN setea cookie httpOnly para futura migración
    """
    rfc = data.get("rfc", "").upper().strip()
    password = data.get("password", "")
    
    supplier = await portal_sql.get_supplier_by_rfc(rfc, include_password=True)
    
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
    
    # FASE AUTH-SECURITY-01: Setear cookie httpOnly
    set_portal_auth_cookie(response, token)
    
    # No devolver password
    supplier_data = {k: v for k, v in supplier.items() if k != "password"}
    
    return {
        "token": token,
        "supplier": supplier_data
    }


@portal_router.post("/auth/logout")
async def logout_supplier(response: Response):
    """
    FASE AUTH-SECURITY-01: Logout del portal de proveedores.
    Elimina la cookie httpOnly.
    """
    clear_portal_auth_cookie(response)
    return {"message": "Sesión cerrada correctamente"}


@portal_router.get("/auth/me")
async def get_supplier_profile(request: Request):
    """
    Obtiene el perfil del proveedor actual.
    
    FASE AUTH-SECURITY-01: Soporta autenticación dual (Header O Cookie).
    """
    current_supplier = await get_current_supplier_dual(request)
    return {k: v for k, v in current_supplier.items() if k != "password"}


# ============================================================================
# FACTURAS
# ============================================================================

@portal_router.get("/invoices")
async def get_supplier_invoices(
    status: Optional[str] = None,
    current_supplier: dict = Depends(get_supplier_dual_dep)
):
    """Obtiene las facturas del proveedor"""
    return await portal_sql.list_supplier_invoices(current_supplier["id"], status=status, limit=500)


@portal_router.post("/invoices/upload")
async def upload_invoice(
    xml_file: UploadFile = File(...),
    pdf_file: Optional[UploadFile] = File(None),
    current_supplier: dict = Depends(get_supplier_dual_dep)
):
    """
    SQL-only guardrail.
    La recepción de CFDI debe implementarse contra Compras_DocumentosFiscales,
    Compras_DocumentosFiscalesDetalle y storage canónico de archivos.
    """
    raise HTTPException(
        status_code=501,
        detail="Carga de facturas pendiente de implementación SQL canónica. Mongo/base64 deshabilitado."
    )


@portal_router.get("/invoices/{invoice_id}")
async def get_invoice_detail(
    invoice_id: str,
    current_supplier: dict = Depends(get_supplier_dual_dep)
):
    """Obtiene detalle de una factura"""
    invoice = await portal_sql.get_supplier_invoice(invoice_id, current_supplier["id"])
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    return invoice


# ============================================================================
# ÓRDENES DE COMPRA (usando conexiones de EDARSA HUB)
# ============================================================================

@portal_router.get("/purchase-orders")
async def get_purchase_orders(
    current_supplier: dict = Depends(get_supplier_dual_dep)
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
    current_supplier: dict = Depends(get_supplier_dual_dep)
):
    """Obtiene el estado de cuenta del proveedor"""
    
    if current_supplier.get("status") != "approved":
        raise HTTPException(status_code=403, detail="Cuenta no aprobada")
    
    # Resumen de facturas desde SQL canónico
    invoices = await portal_sql.list_supplier_invoices(current_supplier["id"], limit=1000)
    
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
    current_supplier: dict = Depends(get_supplier_dual_dep)
):
    """
    SQL-only guardrail.
    Este endpoint no puede consultar servidores LIVE ni credenciales por db.servers.
    Debe leer de Finanzas_CxP_Sync / Finanzas_CuentasPorPagar.
    """
    raise HTTPException(
        status_code=501,
        detail="Saldos de proveedor pendientes de migración a CxP SQL canónico. Consulta LIVE deshabilitada."
    )



# ============================================================================
# ADMINISTRACIÓN (para usuarios de EDARSA HUB)
# P0-PORTAL-PROVEEDORES-AUTH-01: Todos los endpoints admin requieren require_portal_admin
# ============================================================================

@portal_router.get("/admin/pending-suppliers")
async def get_pending_suppliers(current_user: dict = Depends(require_portal_admin)):
    """
    Obtiene proveedores pendientes de aprobación.
    
    P0-PORTAL-PROVEEDORES-AUTH-01: Requiere autenticación interna + rol admin.
    """
    return await portal_sql.list_suppliers(status="pending", limit=100)


@portal_router.get("/admin/all-suppliers")
async def get_all_suppliers(current_user: dict = Depends(require_portal_admin)):
    """
    Obtiene todos los proveedores.
    
    P0-PORTAL-PROVEEDORES-AUTH-01: Requiere autenticación interna + rol admin.
    """
    try:
        return await portal_sql.list_suppliers(limit=500)
    except Exception as e:
        logger.error(f"[PORTAL] Error obteniendo proveedores: {e}")
        # Retornar lista vacía en lugar de error 500
        return []


@portal_router.post("/admin/approve-supplier")
async def approve_supplier(data: dict, current_user: dict = Depends(require_portal_admin)):
    """
    Aprueba o rechaza un proveedor.
    
    P0-PORTAL-PROVEEDORES-AUTH-01: Requiere autenticación interna + rol admin.
    """
    supplier_id = data.get("supplier_id")
    action = data.get("action")  # "approve" o "reject"
    sucursales = data.get("sucursales", [])
    notes = data.get("notes", "")
    # Usar email del admin autenticado en lugar de valor del body
    approved_by = current_user.get("email", "admin")
    
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Acción inválida")
    
    supplier = await portal_sql.get_supplier_by_id(supplier_id)
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
    
    ok = await portal_sql.update_supplier_portal_status(supplier_id, approved=(action == "approve"))
    if not ok:
        raise HTTPException(status_code=500, detail="No se pudo actualizar proveedor en SQL")
    
    return {"message": f"Proveedor {'aprobado' if action == 'approve' else 'rechazado'} exitosamente"}


@portal_router.post("/admin/reset-password")
async def admin_reset_supplier_password(data: dict, current_user: dict = Depends(require_portal_admin)):
    """
    Resetea/establece la contraseña de un proveedor.
    
    P0-PORTAL-PROVEEDORES-AUTH-01: Requiere autenticación interna + rol admin.
    
    Body:
        - supplier_id: ID del proveedor (opcional si se usa rfc)
        - rfc: RFC del proveedor (opcional si se usa supplier_id)
        - new_password: Nueva contraseña en texto plano
    """
    supplier_id = data.get("supplier_id")
    rfc = data.get("rfc", "").upper().strip()
    new_password = data.get("new_password", "").strip()
    # Usar email del admin autenticado
    reset_by = current_user.get("email", "admin")
    
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
    
    supplier = await portal_sql.get_supplier_by_id(supplier_id) if supplier_id else await portal_sql.get_supplier_by_rfc(rfc)
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    # Hashear nueva contraseña
    hashed_password = pwd_context.hash(new_password)
    
    # Actualizar contraseña
    ok = await portal_sql.update_supplier_password(supplier["id"], hashed_password)
    if not ok:
        raise HTTPException(status_code=500, detail="No se pudo actualizar contraseña en SQL")
    
    return {
        "message": "Contraseña actualizada exitosamente",
        "supplier_rfc": supplier["rfc"],
        "supplier_razon_social": supplier.get("razon_social", ""),
        "new_password": new_password,  # Devolver para que el admin la comunique
        "reset_by": reset_by,
        "reset_at": datetime.now(timezone.utc).isoformat()
    }


@portal_router.get("/admin/supplier/{identifier}")
async def admin_get_supplier_details(identifier: str, current_user: dict = Depends(require_portal_admin)):
    """
    Obtiene detalles completos de un proveedor por ID o RFC.
    
    P0-PORTAL-PROVEEDORES-AUTH-01: Requiere autenticación interna + rol admin.
    """
    # Buscar por ID primero, luego por RFC
    supplier = await portal_sql.get_supplier_by_id(identifier)
    
    if not supplier:
        supplier = await portal_sql.get_supplier_by_rfc(identifier.upper())
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    return supplier


@portal_router.get("/admin/invoices")
async def admin_get_all_invoices(
    status: Optional[str] = None,
    supplier_rfc: Optional[str] = None,
    current_user: dict = Depends(require_portal_admin)
):
    """
    Obtiene todas las facturas.
    
    P0-PORTAL-PROVEEDORES-AUTH-01: Requiere autenticación interna + rol admin.
    """
    if not supplier_rfc:
        raise HTTPException(
            status_code=501,
            detail="Consulta global de facturas pendiente de repositorio SQL paginado. Use supplier_rfc."
        )

    supplier = await portal_sql.get_supplier_by_rfc(supplier_rfc.upper())
    if not supplier:
        return []

    return await portal_sql.list_supplier_invoices(supplier["id"], status=status, limit=500)
    
    return invoices


# ============================================================================
# SERVIDORES DISPONIBLES (usa los de EDARSA HUB)
# P0-PORTAL-PROVEEDORES-AUTH-01: Protegido - expone configuración de servidores
# ============================================================================

@portal_router.get("/servers")
async def get_available_servers(current_user: dict = Depends(require_portal_admin)):
    """
    SQL-only guardrail.
    No exponer servidores ni conexiones legacy desde Portal.
    """
    raise HTTPException(
        status_code=501,
        detail="Listado de servidores deshabilitado. Usar unidades de negocio/sucursales canónicas SQL."
    )


@portal_router.delete("/admin/supplier/{supplier_id}")
async def delete_supplier(supplier_id: str, current_user: dict = Depends(require_portal_admin)):
    """
    SQL-only guardrail.
    La eliminación debe ser baja lógica en Proveedor_Catalogo / Proveedor_UsuariosPortal.
    """
    raise HTTPException(
        status_code=501,
        detail="Eliminación de proveedor pendiente de baja lógica SQL canónica."
    )
