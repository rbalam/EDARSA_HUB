"""
EDARSA HUB - CRM Enterprise Native Routes
==========================================
Endpoints REST para CRM nativo (SQL Server EDARSAHUB).
Prefijo: /api/crm/native

Opera con arquitectura SQL-First sin dependencias externas
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Optional, List
from uuid import UUID
import logging

from core.security import get_current_user
from .schemas import (
    LeadCreate, LeadUpdate, LeadResponse, LeadListResponse,
    LeadConvertir, LeadDescalificar,
    OportunidadCreate, OportunidadUpdate, OportunidadResponse, OportunidadListResponse,
    OportunidadCambiarEtapa, OportunidadCerrar,
    PipelineResponse, PipelineKanban, CatalogoItem, CRMDashboardResponse
)
from .native_service import CRMNativeService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/crm/native", tags=["CRM - Native (EDARSAHUB SQL)"])


# ============================================================================
# LEADS ENDPOINTS
# ============================================================================

@router.post("/leads", response_model=LeadResponse, summary="Crear Lead")
async def crear_lead(data: LeadCreate, current_user: dict = Depends(get_current_user)):
    """Crea un nuevo Lead en EDARSAHUB"""
    try:
        result = CRMNativeService.crear_lead(data.model_dump(), current_user['id'])
        return result
    except Exception as e:
        logger.error(f"[CRM] Error creando lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads", summary="Listar Leads")
async def listar_leads(
    empresa_id: UUID = Query(..., description="ID de la empresa"),
    estatus_id: Optional[int] = Query(None, description="Filtrar por estatus"),
    ejecutivo_id: Optional[UUID] = Query(None, description="Filtrar por ejecutivo"),
    origen_id: Optional[int] = Query(None, description="Filtrar por origen"),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre, email o folio"),
    source: Optional[str] = Query("vtiger", description="Fuente de datos: vtiger o local"),
    page: int = Query(1, ge=1, description="Página"),
    page_size: int = Query(20, ge=1, le=100, description="Items por página"),
    current_user: dict = Depends(get_current_user)
):
    """Lista Leads con filtros y paginación. Por defecto lee de Vtiger sincronizado."""
    try:
        # Si source=vtiger, obtener leads desde Vtiger sincronizado
        if source == "vtiger":
            return await _get_vtiger_leads_as_native(busqueda, page, page_size)
        
        # Fallback a datos locales SQL
        result = CRMNativeService.listar_leads(
            empresa_id, estatus_id, ejecutivo_id, origen_id, busqueda, page, page_size
        )
        return result
    except Exception as e:
        logger.error(f"[CRM] Error listando leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_vtiger_leads_as_native(busqueda: Optional[str], page: int, page_size: int):
    """Obtiene leads de Vtiger y los mapea al formato nativo"""
    from .vtiger_client import create_vtiger_client
    import os
    
    base_url = os.environ.get('VTIGER_BASE_URL')
    username = os.environ.get('VTIGER_USERNAME')
    access_key = os.environ.get('VTIGER_ACCESS_KEY')
    
    if not all([base_url, username, access_key]):
        return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
    
    client = create_vtiger_client(base_url, username, access_key)
    
    try:
        result = await client.get_leads(limit=100)
        await client.close()
        
        if not result.get('success'):
            logger.error(f"[CRM] Error obteniendo leads de Vtiger: {result.get('error')}")
            return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
        
        records = result.get('records', [])
        
        # Filtrar por búsqueda si aplica
        if busqueda:
            busqueda_lower = busqueda.lower()
            records = [
                r for r in records 
                if busqueda_lower in (r.get('firstname', '') + ' ' + r.get('lastname', '')).lower()
                or busqueda_lower in r.get('company', '').lower()
                or busqueda_lower in r.get('email', '').lower()
            ]
        
        # Mapear a formato nativo
        items = []
        for idx, r in enumerate(records):
            items.append({
                'lead_id': r.get('id', f'vtiger-{idx}'),
                'folio_lead': r.get('lead_no', f'VT-{idx+1:04d}'),
                'nombre_contacto': f"{r.get('firstname', '')} {r.get('lastname', '')}".strip(),
                'apellido_paterno': r.get('lastname', ''),
                'apellido_materno': '',
                'nombre_empresa': r.get('company', ''),
                'puesto': r.get('designation', ''),
                'email': r.get('email', ''),
                'telefono': r.get('phone', ''),
                'telefono_movil': r.get('mobile', ''),
                'descripcion': r.get('description', ''),
                'origen_nombre': r.get('leadsource', 'Vtiger'),
                'estatus_nombre': r.get('leadstatus', 'Nuevo'),
                'estatus_color': '#10b981' if r.get('leadstatus') == 'Hot' else '#6b7280',
                'prioridad_nombre': 'Media',
                'ejecutivo_nombre': r.get('assigned_user_id', ''),
                'created_at': r.get('createdtime', ''),
                'updated_at': r.get('modifiedtime', ''),
                'source': 'vtiger'
            })
        
        # Paginación
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = items[start:end]
        total_pages = (total + page_size - 1) // page_size
        
        return {
            'items': paginated_items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        }
        
    except Exception as e:
        logger.error(f"[CRM] Error obteniendo leads de Vtiger: {e}")
        await client.close()
        return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}


@router.get("/leads/{lead_id}", response_model=LeadResponse, summary="Obtener Lead")
async def obtener_lead(
    lead_id: UUID = Path(..., description="ID del Lead"),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene un Lead por ID"""
    result = CRMNativeService.obtener_lead(lead_id)
    if not result:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    return result


@router.put("/leads/{lead_id}", response_model=LeadResponse, summary="Actualizar Lead")
async def actualizar_lead(
    lead_id: UUID,
    data: LeadUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Actualiza un Lead existente"""
    try:
        # Filtrar campos None
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        result = CRMNativeService.actualizar_lead(lead_id, update_data, current_user['id'])
        if not result:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CRM] Error actualizando lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/leads/{lead_id}", summary="Eliminar Lead")
async def eliminar_lead(
    lead_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Elimina (soft delete) un Lead"""
    try:
        success = CRMNativeService.eliminar_lead(lead_id, current_user['id'])
        if not success:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        return {"success": True, "message": "Lead eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CRM] Error eliminando lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leads/{lead_id}/descalificar", response_model=LeadResponse, summary="Descalificar Lead")
async def descalificar_lead(
    lead_id: UUID,
    data: LeadDescalificar,
    current_user: dict = Depends(get_current_user)
):
    """Descalifica un Lead con motivo"""
    try:
        result = CRMNativeService.descalificar_lead(
            lead_id, data.motivo_descalificacion_id, data.notas, current_user['id']
        )
        if not result:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CRM] Error descalificando lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leads/{lead_id}/convertir", summary="Convertir Lead")
async def convertir_lead(
    lead_id: UUID,
    data: LeadConvertir,
    current_user: dict = Depends(get_current_user)
):
    """Convierte un Lead a Cuenta/Contacto/Oportunidad"""
    try:
        result = CRMNativeService.convertir_lead(
            lead_id,
            data.crear_cuenta,
            data.crear_contacto,
            data.crear_oportunidad,
            data.nombre_oportunidad,
            data.monto_estimado,
            data.pipeline_id,
            current_user['id']
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error convirtiendo lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# OPORTUNIDADES ENDPOINTS
# ============================================================================

@router.post("/oportunidades", response_model=OportunidadResponse, summary="Crear Oportunidad")
async def crear_oportunidad(data: OportunidadCreate, current_user: dict = Depends(get_current_user)):
    """Crea una nueva Oportunidad en EDARSAHUB"""
    try:
        result = CRMNativeService.crear_oportunidad(data.model_dump(), current_user['id'])
        return result
    except Exception as e:
        logger.error(f"[CRM] Error creando oportunidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oportunidades", summary="Listar Oportunidades")
async def listar_oportunidades(
    empresa_id: UUID = Query(..., description="ID de la empresa"),
    pipeline_id: Optional[int] = Query(None, description="Filtrar por pipeline"),
    etapa_id: Optional[int] = Query(None, description="Filtrar por etapa"),
    estatus_id: Optional[int] = Query(None, description="Filtrar por estatus"),
    ejecutivo_id: Optional[UUID] = Query(None, description="Filtrar por ejecutivo"),
    cuenta_id: Optional[UUID] = Query(None, description="Filtrar por cuenta"),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre o folio"),
    page: int = Query(1, ge=1, description="Página"),
    page_size: int = Query(20, ge=1, le=100, description="Items por página"),
    source: str = Query("vtiger", description="Fuente: vtiger o local"),
    current_user: dict = Depends(get_current_user)
):
    """Lista Oportunidades con filtros y paginación. Por defecto lee de Vtiger."""
    try:
        if source == "vtiger":
            return await _get_vtiger_oportunidades(busqueda, page, page_size)
        
        result = CRMNativeService.listar_oportunidades(
            empresa_id, pipeline_id, etapa_id, estatus_id,
            ejecutivo_id, cuenta_id, busqueda, page, page_size
        )
        return result
    except Exception as e:
        logger.error(f"[CRM] Error listando oportunidades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_vtiger_oportunidades(busqueda: Optional[str], page: int, page_size: int):
    """Obtiene oportunidades desde Vtiger sincronizado"""
    from .vtiger_client import create_vtiger_client
    import os
    
    base_url = os.environ.get('VTIGER_BASE_URL')
    username = os.environ.get('VTIGER_USERNAME')
    access_key = os.environ.get('VTIGER_ACCESS_KEY')
    
    if not all([base_url, username, access_key]):
        return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
    
    client = create_vtiger_client(base_url, username, access_key)
    
    try:
        result = await client.get_opportunities(limit=100)
        await client.close()
        
        if not result.get('success'):
            return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
        
        records = result.get('records', [])
        
        if busqueda:
            busqueda_lower = busqueda.lower()
            records = [r for r in records if busqueda_lower in r.get('potentialname', '').lower()]
        
        items = []
        for idx, r in enumerate(records):
            monto = 0
            try:
                monto = float(r.get('amount', 0))
            except:
                pass
            
            items.append({
                'oportunidad_id': r.get('id', f'vtiger-{idx}'),
                'folio_oportunidad': r.get('potential_no', f'VT-OPP-{idx+1:04d}'),
                'nombre_oportunidad': r.get('potentialname', ''),
                'cuenta_nombre': r.get('related_to', ''),
                'contacto_nombre': r.get('contact_id', ''),
                'monto_estimado': monto,
                'fecha_cierre_estimada': r.get('closingdate', ''),
                'etapa_nombre': r.get('sales_stage', 'Nueva'),
                'probabilidad': int(float(r.get('probability', 0))) if r.get('probability') else 0,
                'pipeline_nombre': 'Vtiger Pipeline',
                'ejecutivo_nombre': r.get('assigned_user_id', ''),
                'descripcion': r.get('description', ''),
                'created_at': r.get('createdtime', ''),
                'source': 'vtiger'
            })
        
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = items[start:end]
        total_pages = (total + page_size - 1) // page_size
        
        return {
            'items': paginated,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        }
    except Exception as e:
        logger.error(f"[CRM] Error obteniendo oportunidades de Vtiger: {e}")
        await client.close()
        return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}


# ==================== CONTACTOS ====================

@router.get("/contactos", summary="Listar Contactos")
async def listar_contactos(
    empresa_id: UUID = Query(..., description="ID de la empresa"),
    cuenta_id: Optional[UUID] = Query(None, description="Filtrar por cuenta"),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre o email"),
    page: int = Query(1, ge=1, description="Página"),
    page_size: int = Query(20, ge=1, le=100, description="Items por página"),
    source: str = Query("vtiger", description="Fuente: vtiger o local"),
    current_user: dict = Depends(get_current_user)
):
    """Lista Contactos. Por defecto lee de Vtiger sincronizado."""
    try:
        if source == "vtiger":
            return await _get_vtiger_contactos(busqueda, page, page_size)
        
        # TODO: Implementar fuente local si es necesario
        return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
    except Exception as e:
        logger.error(f"[CRM] Error listando contactos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_vtiger_contactos(busqueda: Optional[str], page: int, page_size: int):
    """Obtiene contactos desde Vtiger sincronizado"""
    from .vtiger_client import create_vtiger_client
    import os
    
    base_url = os.environ.get('VTIGER_BASE_URL')
    username = os.environ.get('VTIGER_USERNAME')
    access_key = os.environ.get('VTIGER_ACCESS_KEY')
    
    if not all([base_url, username, access_key]):
        return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
    
    client = create_vtiger_client(base_url, username, access_key)
    
    try:
        result = await client.get_contacts(limit=100)
        await client.close()
        
        if not result.get('success'):
            return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
        
        records = result.get('records', [])
        
        if busqueda:
            busqueda_lower = busqueda.lower()
            records = [
                r for r in records 
                if busqueda_lower in f"{r.get('firstname', '')} {r.get('lastname', '')}".lower()
                or busqueda_lower in r.get('email', '').lower()
            ]
        
        items = []
        for idx, r in enumerate(records):
            items.append({
                'contacto_id': r.get('id', f'vtiger-{idx}'),
                'folio_contacto': r.get('contact_no', f'VT-CON-{idx+1:04d}'),
                'nombre_completo': f"{r.get('firstname', '')} {r.get('lastname', '')}".strip(),
                'nombre': r.get('firstname', ''),
                'apellido': r.get('lastname', ''),
                'email': r.get('email', ''),
                'telefono': r.get('phone', ''),
                'celular': r.get('mobile', ''),
                'titulo': r.get('title', ''),
                'departamento': r.get('department', ''),
                'cuenta_id': r.get('account_id', ''),
                'direccion': f"{r.get('mailingcity', '')} {r.get('mailingstate', '')} {r.get('mailingcountry', '')}".strip(),
                'created_at': r.get('createdtime', ''),
                'source': 'vtiger'
            })
        
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = items[start:end]
        total_pages = (total + page_size - 1) // page_size
        
        return {
            'items': paginated,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        }
    except Exception as e:
        logger.error(f"[CRM] Error obteniendo contactos de Vtiger: {e}")
        await client.close()
        return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}


@router.get("/oportunidades/{oportunidad_id}", response_model=OportunidadResponse, summary="Obtener Oportunidad")
async def obtener_oportunidad(
    oportunidad_id: UUID = Path(..., description="ID de la Oportunidad"),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene una Oportunidad por ID"""
    result = CRMNativeService.obtener_oportunidad(oportunidad_id)
    if not result:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return result


@router.post("/oportunidades/{oportunidad_id}/cambiar-etapa", response_model=OportunidadResponse, summary="Cambiar Etapa")
async def cambiar_etapa_oportunidad(
    oportunidad_id: UUID,
    data: OportunidadCambiarEtapa,
    current_user: dict = Depends(get_current_user)
):
    """Cambia la etapa de una oportunidad (move en Kanban)"""
    try:
        result = CRMNativeService.cambiar_etapa_oportunidad(
            oportunidad_id, data.etapa_nueva_id, data.comentario, data.monto_nuevo, current_user['id']
        )
        if not result:
            raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CRM] Error cambiando etapa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oportunidades/{oportunidad_id}/cerrar", response_model=OportunidadResponse, summary="Cerrar Oportunidad")
async def cerrar_oportunidad(
    oportunidad_id: UUID,
    data: OportunidadCerrar,
    current_user: dict = Depends(get_current_user)
):
    """Cierra una oportunidad como ganada o perdida"""
    try:
        result = CRMNativeService.cerrar_oportunidad(
            oportunidad_id, data.es_ganada, data.motivo_id,
            data.razon_texto, data.monto_final, current_user['id']
        )
        if not result:
            raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CRM] Error cerrando oportunidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PIPELINE ENDPOINTS
# ============================================================================

@router.get("/pipelines", summary="Listar Pipelines")
async def listar_pipelines(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene los pipelines disponibles con sus etapas"""
    try:
        result = CRMNativeService.obtener_pipelines(empresa_id)
        return {"pipelines": result}
    except Exception as e:
        logger.error(f"[CRM] Error obteniendo pipelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipelines/{pipeline_id}/kanban", summary="Vista Kanban")
async def obtener_kanban(
    pipeline_id: int,
    empresa_id: UUID = Query(..., description="ID de la empresa"),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene vista Kanban del pipeline con oportunidades agrupadas por etapa"""
    try:
        result = CRMNativeService.obtener_kanban(empresa_id, pipeline_id)
        if not result:
            raise HTTPException(status_code=404, detail="Pipeline no encontrado")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CRM] Error obteniendo kanban: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CATÁLOGOS ENDPOINTS
# ============================================================================

@router.get("/catalogos", summary="Obtener todos los catálogos")
async def obtener_catalogos(current_user: dict = Depends(get_current_user)):
    """Obtiene todos los catálogos CRM en una sola llamada"""
    try:
        result = CRMNativeService.obtener_catalogos()
        return result
    except Exception as e:
        logger.error(f"[CRM] Error obteniendo catálogos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catalogos/{nombre}", summary="Obtener catálogo específico")
async def obtener_catalogo(
    nombre: str = Path(..., description="Nombre del catálogo (ej: origenes_lead, estatus_oportunidad)"),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene un catálogo específico por nombre"""
    try:
        result = CRMNativeService.obtener_catalogo(nombre)
        return {"catalogo": nombre, "items": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[CRM] Error obteniendo catálogo {nombre}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/dashboard", summary="Dashboard CRM")
async def obtener_dashboard(
    empresa_id: UUID = Query(..., description="ID de la empresa"),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene métricas y KPIs del dashboard CRM"""
    try:
        result = CRMNativeService.obtener_dashboard(empresa_id)
        return result
    except Exception as e:
        logger.error(f"[CRM] Error obteniendo dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))
