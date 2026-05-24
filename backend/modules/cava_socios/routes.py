"""
EDARSA HUB - Cava de Socios Routes
===================================
Endpoints API para el módulo Cava de Socios.

Permisos RBAC: CAVA_SOCIOS_*
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging

from .service import get_cava_socios_service
from core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cava-socios", tags=["Cava de Socios"])


# ==================== SCHEMAS ====================

class SocioCreate(BaseModel):
    """Schema para crear socio."""
    nombre_completo: str = Field(..., min_length=3, max_length=200)
    numero_socio: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    cliente_crm_id: Optional[str] = None
    tipo_membresia: str = "ESTANDAR"
    fecha_alta: Optional[str] = None
    fecha_vencimiento: Optional[str] = None
    maximo_botellas: int = 12
    observaciones: Optional[str] = None


class BotellaCreate(BaseModel):
    """Schema para registrar botella."""
    producto_nombre: str = Field(..., min_length=2)
    producto_codigo: Optional[str] = None
    marca: Optional[str] = None
    tipo_bebida: Optional[str] = None  # VINO_TINTO, WHISKY, etc
    añada: Optional[str] = None
    capacidad: float = 750  # ml
    ubicacion: Optional[str] = None
    valor_declarado: float = 0
    foto_url: Optional[str] = None
    observaciones: Optional[str] = None


class ConsumoCreate(BaseModel):
    """Schema para registrar consumo."""
    porcentaje_consumido: float = Field(100, ge=0, le=100)
    motivo: Optional[str] = None
    reservacion_id: Optional[str] = None
    mesero_id: Optional[str] = None
    generar_cargo_descorche: bool = True
    monto_descorche: float = 350
    foto_evidencia: Optional[str] = None
    observaciones: Optional[str] = None


# ==================== ENDPOINTS SOCIOS ====================

@router.get("/dashboard")
async def get_dashboard(
    empresa_id: str = Query(..., description="ID de empresa"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene dashboard del módulo Cava de Socios.
    
    Permisos: CAVA_SOCIOS_VER
    """
    try:
        service = get_cava_socios_service()
        return service.obtener_dashboard(empresa_id)
    except Exception as e:
        logger.error(f"[CavaSocios] Error en dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/socios")
async def listar_socios(
    empresa_id: str = Query(...),
    estatus: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista socios de cava con paginación.
    
    Permisos: CAVA_SOCIOS_VER
    """
    try:
        service = get_cava_socios_service()
        return service.listar_socios(empresa_id, estatus, skip, limit)
    except Exception as e:
        logger.error(f"[CavaSocios] Error listando socios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/socios/{socio_id}")
async def obtener_socio(
    socio_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene detalle de un socio con sus botellas.
    
    Permisos: CAVA_SOCIOS_VER
    """
    try:
        service = get_cava_socios_service()
        socio = service.obtener_socio(socio_id)
        if not socio:
            raise HTTPException(status_code=404, detail="Socio no encontrado")
        return socio
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CavaSocios] Error obteniendo socio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/socios")
async def crear_socio(
    empresa_id: str = Query(...),
    data: SocioCreate = ...,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo socio de cava.
    
    Permisos: CAVA_SOCIOS_CREAR
    """
    try:
        service = get_cava_socios_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id', '')
        return service.crear_socio(empresa_id, data.model_dump(), usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CavaSocios] Error creando socio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS BOTELLAS ====================

@router.post("/socios/{socio_id}/botellas")
async def registrar_botella(
    socio_id: str,
    empresa_id: str = Query(...),
    data: BotellaCreate = ...,
    current_user: Dict = Depends(get_current_user)
):
    """
    Registra una botella nueva en la cava del socio.
    
    Permisos: CAVA_SOCIOS_CREAR
    """
    try:
        service = get_cava_socios_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id', '')
        return service.registrar_botella(socio_id, empresa_id, data.model_dump(), usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CavaSocios] Error registrando botella: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/botellas/{botella_id}/consumo")
async def registrar_consumo(
    botella_id: str,
    data: ConsumoCreate = ...,
    current_user: Dict = Depends(get_current_user)
):
    """
    Registra un consumo parcial o total de una botella.
    
    Permisos: CAVA_SOCIOS_EDITAR
    """
    try:
        service = get_cava_socios_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id', '')
        return service.registrar_consumo(botella_id, data.model_dump(), usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CavaSocios] Error registrando consumo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== REPORTES PDF ====================

from fastapi.responses import StreamingResponse
from .report_service import get_cava_report_service
import io


@router.get("/reportes/socio/{socio_id}/ficha", summary="Descargar Ficha de Socio PDF")
async def descargar_ficha_socio(
    socio_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Genera y descarga la ficha completa del socio en PDF.
    
    Incluye:
    - Datos personales y membresía
    - Resumen de cava
    - Lista de botellas en resguardo
    
    Permisos: CAVA_SOCIOS_VER
    """
    try:
        # Obtener datos del socio
        cava_service = get_cava_socios_service()
        socio = cava_service.obtener_socio(socio_id)
        
        if not socio:
            raise HTTPException(status_code=404, detail="Socio no encontrado")
        
        # Generar PDF
        report_service = get_cava_report_service()
        pdf_bytes = report_service.generar_ficha_socio(socio)
        
        # Nombre del archivo
        filename = f"ficha_socio_{socio.get('numero_socio', socio_id)}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CavaSocios] Error generando ficha PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reportes/socio/{socio_id}/consumos", summary="Descargar Historial de Consumos PDF")
async def descargar_historial_consumos(
    socio_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Genera y descarga el historial de consumos del socio en PDF.
    
    Incluye:
    - Datos resumidos del socio
    - Lista de todos los consumos
    - Total de cargos por descorche
    
    Permisos: CAVA_SOCIOS_VER
    """
    try:
        cava_service = get_cava_socios_service()
        socio = cava_service.obtener_socio(socio_id)
        
        if not socio:
            raise HTTPException(status_code=404, detail="Socio no encontrado")
        
        # Obtener movimientos del socio
        movimientos = cava_service.obtener_movimientos_socio(socio_id)
        
        # Generar PDF
        report_service = get_cava_report_service()
        pdf_bytes = report_service.generar_historial_consumos(socio, movimientos)
        
        filename = f"consumos_socio_{socio.get('numero_socio', socio_id)}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CavaSocios] Error generando historial consumos PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reportes/socio/{socio_id}/estado-cuenta", summary="Descargar Estado de Cuenta PDF")
async def descargar_estado_cuenta(
    socio_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Genera y descarga el estado de cuenta del socio en PDF.
    
    Incluye:
    - Resumen financiero
    - Detalle de cargos (pagados y pendientes)
    - Saldo total
    
    Permisos: CAVA_SOCIOS_VER
    """
    try:
        cava_service = get_cava_socios_service()
        socio = cava_service.obtener_socio(socio_id)
        
        if not socio:
            raise HTTPException(status_code=404, detail="Socio no encontrado")
        
        # Obtener cargos del socio
        cargos = cava_service.obtener_cargos_socio(socio_id)
        
        # Generar PDF
        report_service = get_cava_report_service()
        pdf_bytes = report_service.generar_estado_cuenta(socio, cargos)
        
        filename = f"estado_cuenta_{socio.get('numero_socio', socio_id)}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CavaSocios] Error generando estado de cuenta PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))
