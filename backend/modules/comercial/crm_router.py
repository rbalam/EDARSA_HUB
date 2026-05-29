from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.pool import execute_hub_query

router = APIRouter(prefix="/api/crm", tags=["CRM Comercial"])

# ==========================================
# MODELOS PYDANTIC (Validación de Entrada)
# ==========================================
class CuentaCreate(BaseModel):
    NombreComercial: str
    RazonSocial: Optional[str] = None
    RFC: Optional[str] = None
    EmailContacto: Optional[str] = None
    TelefonoContacto: Optional[str] = None
    UsuarioPropietarioID: int

class SolicitudCreate(BaseModel):
    CuentaID: int
    UsuarioSolicitanteID: int

# ==========================================
# ENDPOINTS: CUENTAS
# ==========================================
@router.get("/cuentas")
def obtener_cuentas():
    """Obtiene todas las cuentas comerciales / prospectos."""
    query = "SELECT * FROM CRM_Cuentas ORDER BY FechaCreacion DESC"
    return execute_hub_query(query, ())

@router.post("/cuentas")
def crear_cuenta(cuenta: CuentaCreate):
    """Crea una nueva cuenta comercial."""
    query = """
        INSERT INTO CRM_Cuentas (NombreComercial, RazonSocial, RFC, EmailContacto, TelefonoContacto, UsuarioPropietarioID)
        OUTPUT INSERTED.CuentaID
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        cuenta.NombreComercial, cuenta.RazonSocial, cuenta.RFC, 
        cuenta.EmailContacto, cuenta.TelefonoContacto, cuenta.UsuarioPropietarioID
    )
    result = execute_hub_query(query, params)
    
    if not result:
        raise HTTPException(status_code=400, detail="Error al crear la cuenta comercial.")
    return {"mensaje": "Cuenta creada exitosamente", "CuentaID": result[0]['CuentaID']}

# ==========================================
# ENDPOINTS: SOLICITUDES DE ALTA (WORKFLOW)
# ==========================================
@router.get("/clientes/solicitudes")
def obtener_solicitudes():
    """Obtiene el histórico y estado de las solicitudes de alta de clientes."""
    query = """
        SELECT s.*, c.NombreComercial, c.RFC
        FROM CRM_ClientesSolicitudesAlta s
        INNER JOIN CRM_Cuentas c ON s.CuentaID = c.CuentaID
        ORDER BY s.FechaSolicitud DESC
    """
    return execute_hub_query(query, ())

@router.post("/clientes/solicitudes")
def crear_solicitud(solicitud: SolicitudCreate):
    """Inicia un workflow para convertir una Cuenta en Cliente Maestro."""
    query = """
        INSERT INTO CRM_ClientesSolicitudesAlta (CuentaID, UsuarioSolicitanteID)
        OUTPUT INSERTED.SolicitudID
        VALUES (%s, %s)
    """
    params = (solicitud.CuentaID, solicitud.UsuarioSolicitanteID)
    result = execute_hub_query(query, params)
    
    if not result:
        raise HTTPException(status_code=400, detail="Error al generar la solicitud de alta.")
    return {"mensaje": "Solicitud de alta generada exitosamente", "SolicitudID": result[0]['SolicitudID']}
