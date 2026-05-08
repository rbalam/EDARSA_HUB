"""
ROUTES V2 - COMERCIAL V2
=========================

Endpoints v2 aislados para Comercial.
Leen EXCLUSIVAMENTE desde EDARSAHUB v2.

NO consultan:
- SQL vivo a SoftRestaurant/MPRO
- MongoDB cache
- Datos demo

FEATURE FLAG:
- COMERCIAL_V2_ENABLED=false (default OFF)
- Endpoints existen pero no reemplazan v1

RBAC:
- Respeta unidades permitidas por usuario
- No hardcodea unidades
"""

from datetime import date, datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
import logging

# SUBFASE 5 FIX: Usar get_current_user_dual para soportar cookie httpOnly
from core.security import get_current_user_dual_dependency
from core.context_resolver import get_user_unidades_negocio

from .feature_flag import is_comercial_v2_enabled, get_v2_status
from .repository_readonly import (
    check_v2_health,
    get_kpis_diarios,
    get_kpis_diarios_agregados,
    get_kpis_por_unidad,
    get_kpis_mensuales,
    get_ventas_dia_abiertas,
    get_sync_status,
    get_last_sync_by_unidad,
    get_unidades_disponibles
)
from .schemas_api import (
    HealthResponse,
    DashboardResponse,
    KPIsDiariosResponse,
    KPIsMensualesResponse,
    VentasDiaResponse,
    UnidadesResponse,
    SyncStatusResponse,
    MetadataV2
)

logger = logging.getLogger(__name__)

# Router v2 aislado
router = APIRouter(prefix="/comercial", tags=["Comercial V2"])


# =============================================================================
# HELPERS
# =============================================================================

async def get_unidades_permitidas_v2(current_user: dict) -> List[str]:
    """
    Obtiene las unidades de negocio permitidas por RBAC.
    Mapea a los IDs usados en Comercial v2.
    """
    try:
        unidades_mongo = await get_user_unidades_negocio(current_user)
        
        # Mapear códigos de unidad a los IDs de v2
        # Las unidades en v2 usan: CIENFUEGOS, LA-ESTELAR, 130-MER, 130-QRO, ORIGEN
        unidades_v2 = []
        
        for u in unidades_mongo:
            codigo = u.get('codigo', '').upper()
            nombre = u.get('nombre', '').upper()
            
            if 'CIENFUEGOS' in nombre and 'TABLAJERIA' not in nombre:
                unidades_v2.append('CIENFUEGOS')
            elif 'ESTELAR' in nombre:
                unidades_v2.append('LA-ESTELAR')
            elif 'MERIDA' in nombre or 'MER' in codigo or 'MID' in codigo:
                unidades_v2.append('130-MER')
            elif 'QUERETARO' in nombre or 'QRO' in codigo:
                unidades_v2.append('130-QRO')
            elif 'ORIGEN' in nombre:
                unidades_v2.append('ORIGEN')
        
        # Si es SuperAdmin, dar acceso a todas
        if current_user.get('role') in ['SuperAdministrador', 'Director']:
            return ['CIENFUEGOS', 'LA-ESTELAR', '130-MER', '130-QRO', 'ORIGEN']
        
        return list(set(unidades_v2)) if unidades_v2 else []
        
    except Exception as e:
        logger.warning(f"Error obteniendo unidades permitidas: {e}")
        return []


def serialize_response(data: any) -> any:
    """Serializa datos para respuesta JSON."""
    if isinstance(data, dict):
        return {k: serialize_response(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_response(item) for item in data]
    elif isinstance(data, (date, datetime)):
        return data.isoformat()
    elif hasattr(data, '__float__'):
        return float(data)
    else:
        return data


# =============================================================================
# ENDPOINT: HEALTH
# =============================================================================

@router.get("/health", response_model=HealthResponse)
async def comercial_v2_health():
    """
    Estado de salud de Comercial v2.
    
    Verifica:
    - Conexión a EDARSAHUB
    - Datos disponibles en tablas v2
    - Feature flag status
    """
    try:
        health = check_v2_health()
        health['feature_flag'] = get_v2_status()
        return health
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "error", "message": str(e)}


# =============================================================================
# ENDPOINT: DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=DashboardResponse)
async def comercial_v2_dashboard(
    fecha_inicio: date = Query(..., description="Fecha inicio del período"),
    fecha_fin: date = Query(..., description="Fecha fin del período"),
    unidad_negocio_id: Optional[str] = Query(None, description="Filtrar por unidad"),
    current_user: dict = Depends(get_current_user_dual_dependency())
):
    """
    Dashboard de KPIs comerciales v2.
    
    Lee desde: 
    - Comercial_KPIs_Diarios_v2 (ventas cerradas)
    - Comercial_Ventas_Dia_Abiertas_v2 (ventas del día en curso)
    
    Fuente: EDARSAHUB (NO SQL vivo, NO MongoDB)
    
    REGLA DE NEGOCIO:
    - Si fecha_fin >= hoy: incluye ventas abiertas del día actual
    - Las ventas abiertas se suman a los totales pero se identifican como estimadas
    - No hay duplicación: ventas_cerradas_dia + ventas_abiertas = total_estimado_dia
    """
    try:
        # Obtener unidades permitidas
        unidades_permitidas = await get_unidades_permitidas_v2(current_user)
        
        if not unidades_permitidas:
            raise HTTPException(
                status_code=403, 
                detail="No tiene unidades de negocio asignadas"
            )
        
        # Filtrar por unidad específica si se solicita
        if unidad_negocio_id:
            if unidad_negocio_id not in unidades_permitidas:
                raise HTTPException(
                    status_code=403,
                    detail=f"No tiene acceso a la unidad {unidad_negocio_id}"
                )
            unidades_permitidas = [unidad_negocio_id]
        
        # Obtener datos agregados de ventas cerradas
        totales = get_kpis_diarios_agregados(fecha_inicio, fecha_fin, unidades_permitidas)
        
        # Obtener datos por unidad (cerradas)
        por_unidad_cerradas = get_kpis_por_unidad(fecha_inicio, fecha_fin, unidades_permitidas)
        
        # =====================================================================
        # COMBINAR CON VENTAS ABIERTAS DEL DÍA ACTUAL
        # =====================================================================
        
        fecha_hoy = date.today()
        incluye_hoy = fecha_fin >= fecha_hoy
        ventas_abiertas_hoy = []
        
        if incluye_hoy:
            # Obtener ventas abiertas del día (actualizadas cada 5 min)
            ventas_abiertas_hoy = get_ventas_dia_abiertas(fecha_hoy, unidades_permitidas)
        
        # =====================================================================
        # UNIÓN DE UNIDADES: CERRADAS + ABIERTAS
        # Regla: Incluir unidad si tiene cerradas O abiertas O SyncLog exitoso
        # =====================================================================
        
        # Indexar unidades cerradas por ID
        cerradas_por_unidad = {
            u['unidad_negocio_id']: u for u in por_unidad_cerradas
        }
        
        # Indexar unidades abiertas por ID
        abiertas_por_unidad = {
            v['unidad_negocio_id']: v for v in ventas_abiertas_hoy
        } if ventas_abiertas_hoy else {}
        
        # Unión de todas las unidades (cerradas + abiertas)
        todas_unidades_ids = set(cerradas_por_unidad.keys()) | set(abiertas_por_unidad.keys())
        
        # Si no hay ninguna unidad con datos, incluir todas las permitidas (mostrar como "sin operación")
        if not todas_unidades_ids and unidades_permitidas:
            todas_unidades_ids = set(unidades_permitidas)
        
        # Construir lista combinada de unidades
        por_unidad = []
        for uid in sorted(todas_unidades_ids):
            tiene_cerradas = uid in cerradas_por_unidad
            tiene_abiertas = uid in abiertas_por_unidad
            
            if tiene_cerradas:
                # Usar datos de cerradas como base
                u = cerradas_por_unidad[uid].copy()
            elif tiene_abiertas:
                # Crear registro base desde abiertas
                ab = abiertas_por_unidad[uid]
                u = {
                    'unidad_negocio_id': uid,
                    'unidad_negocio_nombre': ab.get('unidad_negocio_nombre', uid),
                    'sistema_origen': ab.get('sistema_origen', 'DESCONOCIDO'),
                    'ventas_total': 0,
                    'ventas_sin_propina': 0,
                    'propinas_total': 0,
                    'tickets_total': 0,
                    'pax_total': 0,
                    'ticket_promedio_avg': 0,
                    'dias': 0,
                    'fecha_min': None,
                    'fecha_max': None
                }
            else:
                # Unidad sin datos (mostrar como "sin operación")
                u = {
                    'unidad_negocio_id': uid,
                    'unidad_negocio_nombre': uid,
                    'sistema_origen': 'DESCONOCIDO',
                    'ventas_total': 0,
                    'ventas_sin_propina': 0,
                    'propinas_total': 0,
                    'tickets_total': 0,
                    'pax_total': 0,
                    'ticket_promedio_avg': 0,
                    'dias': 0,
                    'fecha_min': None,
                    'fecha_max': None
                }
            
            # Enriquecer con datos de abiertas si existen
            if tiene_abiertas:
                ab = abiertas_por_unidad[uid]
                u['_ventas_abiertas_hoy'] = float(ab.get('ventas_abiertas') or 0)
                u['_ventas_cerradas_hoy'] = float(ab.get('ventas_cerradas_dia') or 0)
                u['_total_estimado_hoy'] = float(ab.get('total_estimado_dia') or 0)
                u['_tickets_abiertos_hoy'] = int(ab.get('tickets_abiertos') or 0)
                u['_pax_abiertos_hoy'] = int(ab.get('pax_abiertos') or 0)
                u['_snapshot_timestamp'] = str(ab.get('snapshot_timestamp') or '')
                u['_incluye_ventas_abiertas'] = True
                
                # Si NO tiene cerradas, sumar abiertas al total de la unidad
                if not tiene_cerradas:
                    total_dia = float(ab.get('total_estimado_dia') or 0)
                    tickets = int(ab.get('tickets_abiertos') or 0) + int(ab.get('tickets_cerrados_dia') or 0)
                    pax = int(ab.get('pax_abiertos') or 0) + int(ab.get('pax_cerrados_dia') or 0)
                    
                    u['ventas_total'] = total_dia
                    u['tickets_total'] = tickets
                    u['pax_total'] = pax
                    u['dias'] = 1 if total_dia > 0 else 0
                    u['fecha_min'] = fecha_hoy.isoformat()
                    u['fecha_max'] = fecha_hoy.isoformat()
            else:
                u['_ventas_abiertas_hoy'] = 0
                u['_ventas_cerradas_hoy'] = 0
                u['_total_estimado_hoy'] = 0
                u['_tickets_abiertos_hoy'] = 0
                u['_pax_abiertos_hoy'] = 0
                u['_snapshot_timestamp'] = ''
                u['_incluye_ventas_abiertas'] = False
            
            # =====================================================================
            # ESTADO V2 DE LA UNIDAD
            # =====================================================================
            ventas_total_unidad = float(u.get('ventas_total') or 0) + float(u.get('_total_estimado_hoy') or 0)
            
            if tiene_cerradas or (tiene_abiertas and ventas_total_unidad > 0):
                u['_status_v2'] = 'ACTUALIZADO'
                u['_status_v2_desc'] = 'Datos vigentes de EDARSAHUB'
            elif tiene_abiertas and ventas_total_unidad == 0:
                u['_status_v2'] = 'SIN_OPERACION'
                u['_status_v2_desc'] = 'Sin ventas pero sync exitoso'
            else:
                u['_status_v2'] = 'SIN_DATOS'
                u['_status_v2_desc'] = 'Sin registros en período'
            
            por_unidad.append(u)
        
        # =====================================================================
        # RECALCULAR TOTALES INCLUYENDO ABIERTAS
        # =====================================================================
        
        # Sumar totales de unidades que SOLO tienen abiertas (no están en cerradas)
        if incluye_hoy and ventas_abiertas_hoy:
            for venta in ventas_abiertas_hoy:
                uid = venta['unidad_negocio_id']
                # Solo sumar si la unidad NO tiene datos cerrados en el período
                if uid not in cerradas_por_unidad:
                    total_dia = float(venta.get('total_estimado_dia') or 0)
                    tickets = int(venta.get('tickets_abiertos') or 0) + int(venta.get('tickets_cerrados_dia') or 0)
                    pax = int(venta.get('pax_abiertos') or 0) + int(venta.get('pax_cerrados_dia') or 0)
                    
                    totales['ventas_total'] = float(totales.get('ventas_total') or 0) + total_dia
                    totales['tickets_total'] = int(totales.get('tickets_total') or 0) + tickets
                    totales['pax_total'] = int(totales.get('pax_total') or 0) + pax
        
        # Actualizar conteo de unidades
        totales['total_unidades'] = len(por_unidad)
        
        # Construir respuesta
        response_data = {
            "totales": serialize_response({
                "ventas_total": totales.get('ventas_total', 0),
                "tickets_total": totales.get('tickets_total', 0),
                "pax_total": totales.get('pax_total', 0),
                "total_registros": totales.get('total_registros', 0),
                "total_unidades": totales.get('total_unidades', 0),
                "total_dias": totales.get('total_dias', 0),
                "_incluye_ventas_abiertas": incluye_hoy and len(ventas_abiertas_hoy) > 0
            }),
            "unidades": serialize_response([
                {
                    "unidad_negocio_id": u['unidad_negocio_id'],
                    "unidad_negocio_nombre": u['unidad_negocio_nombre'],
                    "sistema_origen": u['sistema_origen'],
                    "ventas_total": u['ventas_total'],
                    "ventas_sin_propina": u.get('ventas_sin_propina'),
                    "propinas_total": u.get('propinas_total'),
                    "tickets_total": u['tickets_total'],
                    "pax_total": u['pax_total'],
                    "ticket_promedio": u.get('ticket_promedio_avg'),
                    "dias": u['dias'],
                    "fecha_min": u['fecha_min'],
                    "fecha_max": u['fecha_max'],
                    # Datos de ventas abiertas del día (si aplica)
                    "_ventas_abiertas_hoy": u.get('_ventas_abiertas_hoy', 0),
                    "_ventas_cerradas_hoy": u.get('_ventas_cerradas_hoy', 0),
                    "_total_estimado_hoy": u.get('_total_estimado_hoy', 0),
                    "_tickets_abiertos_hoy": u.get('_tickets_abiertos_hoy', 0),
                    "_pax_abiertos_hoy": u.get('_pax_abiertos_hoy', 0),
                    "_snapshot_timestamp": u.get('_snapshot_timestamp', ''),
                    "_incluye_ventas_abiertas": u.get('_incluye_ventas_abiertas', False),
                    # Estado V2 de la unidad
                    "_status_v2": u.get('_status_v2', 'DESCONOCIDO'),
                    "_status_v2_desc": u.get('_status_v2_desc', ''),
                    "_v2_fuente": "EDARSAHUB",
                    "_v2_tabla": "Comercial_KPIs_Diarios_v2" if u.get('dias', 0) > 0 else "Comercial_Ventas_Dia_Abiertas_v2"
                }
                for u in por_unidad
            ]),
            # Resumen de ventas abiertas del día
            "ventas_dia_actual": serialize_response({
                "fecha": fecha_hoy.isoformat(),
                "incluido_en_periodo": incluye_hoy,
                "unidades_con_datos": len(ventas_abiertas_hoy),
                "detalle": [
                    {
                        "unidad_negocio_id": v['unidad_negocio_id'],
                        "unidad_negocio_nombre": v['unidad_negocio_nombre'],
                        "ventas_abiertas": float(v.get('ventas_abiertas') or 0),
                        "ventas_cerradas_dia": float(v.get('ventas_cerradas_dia') or 0),
                        "total_estimado_dia": float(v.get('total_estimado_dia') or 0),
                        "tickets_abiertos": int(v.get('tickets_abiertos') or 0),
                        "pax_abiertos": int(v.get('pax_abiertos') or 0),
                        "snapshot_timestamp": str(v.get('snapshot_timestamp') or ''),
                        "_fuente": "Comercial_Ventas_Dia_Abiertas_v2"
                    }
                    for v in ventas_abiertas_hoy
                ] if ventas_abiertas_hoy else []
            }) if incluye_hoy else None,
            "periodo": {
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat()
            },
            "filtros_aplicados": {
                "unidades": unidades_permitidas,
                "unidad_especifica": unidad_negocio_id
            }
        }
        
        return DashboardResponse(
            success=True,
            data=response_data,
            metadata=MetadataV2()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard v2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINT: KPIS DIARIOS
# =============================================================================

@router.get("/kpis-diarios", response_model=KPIsDiariosResponse)
async def comercial_v2_kpis_diarios(
    fecha_inicio: date = Query(..., description="Fecha inicio"),
    fecha_fin: date = Query(..., description="Fecha fin"),
    unidad_negocio_id: Optional[str] = Query(None, description="Filtrar por unidad"),
    current_user: dict = Depends(get_current_user_dual_dependency())
):
    """
    KPIs diarios detallados v2.
    
    Lee desde: Comercial_KPIs_Diarios_v2
    """
    try:
        unidades_permitidas = await get_unidades_permitidas_v2(current_user)
        
        if not unidades_permitidas:
            raise HTTPException(status_code=403, detail="No tiene unidades asignadas")
        
        if unidad_negocio_id:
            if unidad_negocio_id not in unidades_permitidas:
                raise HTTPException(status_code=403, detail="No tiene acceso a esa unidad")
            unidades_permitidas = [unidad_negocio_id]
        
        # Obtener datos
        datos = get_kpis_diarios(fecha_inicio, fecha_fin, unidades_permitidas)
        
        return KPIsDiariosResponse(
            success=True,
            data=serialize_response(datos),
            total=len(datos),
            periodo={
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat()
            },
            metadata=MetadataV2()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"KPIs diarios v2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINT: KPIS MENSUALES
# =============================================================================

@router.get("/kpis-mensuales", response_model=KPIsMensualesResponse)
async def comercial_v2_kpis_mensuales(
    anio: int = Query(..., description="Año"),
    mes_inicio: int = Query(1, ge=1, le=12, description="Mes inicio"),
    mes_fin: int = Query(12, ge=1, le=12, description="Mes fin"),
    unidad_negocio_id: Optional[str] = Query(None, description="Filtrar por unidad"),
    current_user: dict = Depends(get_current_user_dual_dependency())
):
    """
    KPIs mensuales v2.
    
    Lee desde: Comercial_KPIs_Mensuales_v2
    """
    try:
        unidades_permitidas = await get_unidades_permitidas_v2(current_user)
        
        if not unidades_permitidas:
            raise HTTPException(status_code=403, detail="No tiene unidades asignadas")
        
        if unidad_negocio_id:
            if unidad_negocio_id not in unidades_permitidas:
                raise HTTPException(status_code=403, detail="No tiene acceso a esa unidad")
            unidades_permitidas = [unidad_negocio_id]
        
        # Obtener datos
        datos = get_kpis_mensuales(anio, mes_inicio, mes_fin, unidades_permitidas)
        
        return KPIsMensualesResponse(
            success=True,
            data=serialize_response(datos),
            total=len(datos),
            anio=anio,
            metadata=MetadataV2()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"KPIs mensuales v2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINT: VENTAS DIA
# =============================================================================

@router.get("/ventas-dia", response_model=VentasDiaResponse)
async def comercial_v2_ventas_dia(
    fecha: date = Query(default=None, description="Fecha (default: hoy)"),
    current_user: dict = Depends(get_current_user_dual_dependency())
):
    """
    Ventas del día v2.
    
    Lee desde: Comercial_Ventas_Dia_Abiertas_v2
    Actualizado cada 5 minutos por sync_comercial_abiertas_v2_job.py
    
    Retorna:
    - ventas_abiertas: Ventas sin cierre aún
    - ventas_cerradas_dia: Ventas ya cerradas del mismo día
    - total_estimado_dia: Total del día (abiertas + cerradas)
    """
    try:
        if fecha is None:
            fecha = date.today()
        
        unidades_permitidas = await get_unidades_permitidas_v2(current_user)
        
        if not unidades_permitidas:
            raise HTTPException(status_code=403, detail="No tiene unidades asignadas")
        
        # Obtener datos de ventas abiertas
        datos = get_ventas_dia_abiertas(fecha, unidades_permitidas)
        
        # Calcular totales
        total_ventas_abiertas = sum(float(d.get('ventas_abiertas') or 0) for d in datos)
        total_ventas_cerradas = sum(float(d.get('ventas_cerradas_dia') or 0) for d in datos)
        total_estimado = sum(float(d.get('total_estimado_dia') or 0) for d in datos)
        total_tickets = sum(int(d.get('tickets_abiertos') or 0) + int(d.get('tickets_cerrados_dia') or 0) for d in datos)
        total_pax = sum(int(d.get('pax_abiertos') or 0) + int(d.get('pax_cerrados_dia') or 0) for d in datos)
        
        return VentasDiaResponse(
            success=True,
            data=serialize_response({
                "resumen": {
                    "fecha": fecha.isoformat(),
                    "total_ventas_abiertas": total_ventas_abiertas,
                    "total_ventas_cerradas_dia": total_ventas_cerradas,
                    "total_estimado_dia": total_estimado,
                    "total_tickets": total_tickets,
                    "total_pax": total_pax,
                    "unidades_con_datos": len(datos)
                },
                "por_unidad": [
                    {
                        "unidad_negocio_id": d['unidad_negocio_id'],
                        "unidad_negocio_nombre": d['unidad_negocio_nombre'],
                        "sistema_origen": d['sistema_origen'],
                        "ventas_abiertas": float(d.get('ventas_abiertas') or 0),
                        "tickets_abiertos": int(d.get('tickets_abiertos') or 0),
                        "pax_abiertos": int(d.get('pax_abiertos') or 0),
                        "ventas_cerradas_dia": float(d.get('ventas_cerradas_dia') or 0),
                        "tickets_cerrados_dia": int(d.get('tickets_cerrados_dia') or 0),
                        "pax_cerrados_dia": int(d.get('pax_cerrados_dia') or 0),
                        "total_estimado_dia": float(d.get('total_estimado_dia') or 0),
                        "snapshot_timestamp": str(d.get('snapshot_timestamp') or ''),
                        "sync_run_id": d.get('sync_run_id'),
                        "_fuente": "Comercial_Ventas_Dia_Abiertas_v2"
                    }
                    for d in datos
                ]
            }),
            fecha=fecha.isoformat(),
            metadata=MetadataV2()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ventas día v2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINT: UNIDADES
# =============================================================================

@router.get("/unidades", response_model=UnidadesResponse)
async def comercial_v2_unidades(
    current_user: dict = Depends(get_current_user_dual_dependency())
):
    """
    Unidades de negocio disponibles en v2.
    
    Lee desde: Comercial_KPIs_Diarios_v2 (DISTINCT)
    """
    try:
        unidades_permitidas = await get_unidades_permitidas_v2(current_user)
        
        # Obtener unidades con datos
        unidades = get_unidades_disponibles(unidades_permitidas if unidades_permitidas else None)
        
        return UnidadesResponse(
            success=True,
            unidades=serialize_response(unidades),
            total=len(unidades),
            metadata=MetadataV2()
        )
        
    except Exception as e:
        logger.error(f"Unidades v2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINT: SYNC STATUS
# =============================================================================

@router.get("/sync-status", response_model=SyncStatusResponse)
async def comercial_v2_sync_status(
    limit: int = Query(50, ge=1, le=200, description="Límite de registros"),
    current_user: dict = Depends(get_current_user_dual_dependency())
):
    """
    Estado de sincronización v2.
    
    Lee desde: Comercial_SyncLog_v2
    """
    try:
        unidades_permitidas = await get_unidades_permitidas_v2(current_user)
        
        # Obtener logs
        logs = get_sync_status(unidades_permitidas, limit)
        
        # Obtener última sync por unidad
        ultima_sync = get_last_sync_by_unidad(unidades_permitidas)
        
        return SyncStatusResponse(
            success=True,
            logs=serialize_response(logs),
            ultima_sync_por_unidad=serialize_response(ultima_sync),
            metadata=MetadataV2()
        )
        
    except Exception as e:
        logger.error(f"Sync status v2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GETTER DEL ROUTER
# =============================================================================

def get_comercial_v2_router():
    """Retorna el router de Comercial v2."""
    return router
