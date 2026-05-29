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

# ==========================================
# MODELOS PYDANTIC: ACTIVIDADES (FASE 7)
# ==========================================
from pydantic import Field
from uuid import UUID

class ActividadCreate(BaseModel):
    CuentaID: int
    TipoActividad: str = Field(..., description="Llamada, Correo, WhatsApp, Visita, Demo, Reunion")
    Asunto: str
    NotasInteraccion: Optional[str] = None
    UsuarioAsignadoID: int
    FechaProgramada: str  # Formato ISO string YYYY-MM-DD HH:MM:SS

class ActividadEstatusUpdate(BaseModel):
    EstatusNuevo: str  # Pendiente, Completada, Vencida, Cancelada
    UsuarioModificadorID: int
    Comentario: Optional[str] = None

# ==========================================
# ENDPOINTS: ACTIVIDADES
# ==========================================
@router.get("/actividades")
def obtener_actividades_propias(usuario_id: int):
    """Obtiene la agenda de actividades pendientes y asignadas a un ejecutivo."""
    query = """
        SELECT ActividadID, CuentaID, TipoActividad, Asunto, Estatus, FechaProgramada 
        FROM dbo.CRM_Actividades 
        WHERE UsuarioAsignadoID = %s 
        ORDER BY FechaProgramada ASC
    """
    return execute_hub_query(query, (usuario_id,))

@router.post("/actividades")
def registrar_actividad(actividad: ActividadCreate):
    """Registra una nueva actividad o minuta de seguimiento en el CRM."""
    query = """
        INSERT INTO dbo.CRM_Actividades (CuentaID, TipoActividad, Asunto, NotasInteraccion, UsuarioAsignadoID, FechaProgramada)
        OUTPUT INSERTED.ActividadID
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        actividad.CuentaID, actividad.TipoActividad, actividad.Asunto,
        actividad.NotasInteraccion, actividad.UsuarioAsignadoID, actividad.FechaProgramada
    )
    result = execute_hub_query(query, params)
    if not result:
        raise HTTPException(status_code=400, detail="Error al registrar la actividad comercial.")
    return {"mensaje": "Actividad programada correctamente", "ActividadID": result[0]['ActividadID']}

@router.put("/actividades/{actividad_id}/estatus")
def actualizar_estatus_actividad(actividad_id: int, update_data: ActividadEstatusUpdate):
    """Actualiza el estatus de una actividad e inyecta la auditoría en el historial."""
    # 1. Obtener estatus previo
    query_previo = "SELECT Estatus FROM dbo.CRM_Actividades WHERE ActividadID = %s"
    res_previo = execute_hub_query(query_previo, (actividad_id,))
    if not res_previo:
        raise HTTPException(status_code=404, detail="La actividad especificada no existe.")
    
    estatus_anterior = res_previo[0]["Estatus"]

    # 2. Actualizar el estatus de la actividad principal
    query_update = """
        UPDATE dbo.CRM_Actividades 
        SET Estatus = %s, FechaEjecucion = CASE WHEN %s = 'Completada' THEN GETDATE() ELSE FechaEjecucion END, FechaModificacion = GETDATE()
        WHERE ActividadID = %s
    """
    execute_hub_query(query_update, (update_data.EstatusNuevo, update_data.EstatusNuevo, actividad_id))

    # 3. Registrar de forma obligatoria en la tabla de historial de auditoría de la Fase 7
    query_historial = """
        INSERT INTO dbo.CRM_ActividadesHistorial (ActividadID, EstatusAnterior, EstatusNuevo, UsuarioModificadorID, Comentario)
        VALUES (%s, %s, %s, %s, %s)
    """
    execute_hub_query(query_historial, (actividad_id, estatus_anterior, update_data.EstatusNuevo, update_data.UsuarioModificadorID, update_data.Comentario))

    return {"mensaje": "Estatus de actividad actualizado y auditado correctamente."}
