"""
EDARSA HUB - Tablajería Routes
==============================
Endpoints API para el módulo de Tablajería.

FASE 5: Órdenes de tablaje (crear, ejecutar, cerrar)
- Autenticación requerida en todos los endpoints
- RBAC con permisos TABLAJERIA_*
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, date
from decimal import Decimal
import logging
import os
import pymssql
import json

from .schemas import (
    Plantilla, PlantillaCreate, PlantillaUpdate,
    Orden, OrdenCreate, OrdenUpdate,
    SyncRequest, SyncResult,
    EstatusPlantilla, EstatusOrden, OrigenPlantilla
)
from .sync_service import TablajeriaSyncService
from .ordenes_service import TablajeriaOrdenesService
from core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tablajeria", tags=["Tablajería"])

# Configuración DB desde variables de entorno
DB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    'password': os.environ.get('EDARSAHUB_PASSWORD', '')
}

# Validar que el password esté configurado
if not DB_CONFIG['password']:
    logger.warning("[TABLAJERIA] EDARSAHUB_PASSWORD no configurado en variables de entorno")


def get_connection():
    return pymssql.connect(
        server=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        login_timeout=30,
        timeout=60,
        autocommit=False
    )


# ============================================================
# PLANTILLAS
# ============================================================

@router.get("/plantillas")
async def listar_plantillas(
    empresa_id: Optional[str] = None,
    estatus: Optional[str] = None,
    origen: Optional[str] = None,
    activo: bool = True,
    limit: int = Query(default=50, le=200),
    offset: int = 0
):
    """Lista plantillas de tablajería"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        query = """
            SELECT 
                PlantillaID, EmpresaID, UnidadNegocioID,
                CodigoPlantilla, NombrePlantilla, Descripcion,
                TipoTransformacion, InsumoBaseCodigo, InsumoBaseNombre,
                CantidadBaseEstandar, RendimientoEsperadoPorcentaje,
                MermaEsperadaPorcentaje, ReglaCosteo,
                OrigenPlantilla, SistemaOrigen, IDLegacyPlantilla,
                VersionActual, Estatus, Activo,
                FechaAltaUTC, FechaSincronizacionUTC, FechaOperacionMexico
            FROM Operaciones_Tablaje_Plantillas
            WHERE 1=1
        """
        params = []
        
        if empresa_id:
            query += " AND EmpresaID = %s"
            params.append(empresa_id)
        if estatus:
            query += " AND Estatus = %s"
            params.append(estatus)
        if origen:
            query += " AND OrigenPlantilla = %s"
            params.append(origen)
        if activo is not None:
            query += " AND Activo = %s"
            params.append(1 if activo else 0)
        
        query += " ORDER BY NombrePlantilla OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
        params.extend([offset, limit])
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        # Convertir UUIDs a string
        plantillas = []
        for row in rows:
            p = dict(row)
            for field in ['PlantillaID', 'EmpresaID', 'UnidadNegocioID']:
                if p.get(field):
                    p[field] = str(p[field])
            plantillas.append(p)
        
        # Contar total
        count_query = """
            SELECT COUNT(*) as total
            FROM Operaciones_Tablaje_Plantillas
            WHERE Activo = %s
        """
        cursor.execute(count_query, (1 if activo else 0,))
        total = cursor.fetchone()['total']
        
        return {
            "plantillas": plantillas,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"[Tablajeria] Error listando plantillas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/plantillas/{plantilla_id}")
async def obtener_plantilla(plantilla_id: str):
    """Obtiene una plantilla con sus detalles"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Header
        cursor.execute("""
            SELECT * FROM Operaciones_Tablaje_Plantillas
            WHERE PlantillaID = %s
        """, (plantilla_id,))
        
        plantilla = cursor.fetchone()
        if not plantilla:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Convertir a dict y UUIDs
        result = dict(plantilla)
        for field in ['PlantillaID', 'EmpresaID', 'UnidadNegocioID', 'PlantillaPadreID',
                      'AutorizadoPor', 'UsuarioAltaID', 'UsuarioModificacionID']:
            if result.get(field):
                result[field] = str(result[field])
        
        # Detalles
        cursor.execute("""
            SELECT * FROM Operaciones_Tablaje_PlantillasDetalle
            WHERE PlantillaID = %s AND Activo = 1
            ORDER BY OrdenVisual
        """, (plantilla_id,))
        
        detalles = []
        for row in cursor.fetchall():
            d = dict(row)
            d['PlantillaDetalleID'] = str(d['PlantillaDetalleID'])
            d['PlantillaID'] = str(d['PlantillaID'])
            detalles.append(d)
        
        result['detalles'] = detalles
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Tablajeria] Error obteniendo plantilla: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.put("/plantillas/{plantilla_id}/publicar")
async def publicar_plantilla(plantilla_id: str):
    """Publica una plantilla (cambia estatus a PUBLICADA)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Operaciones_Tablaje_Plantillas
            SET Estatus = %s, FechaModificacionUTC = %s
            WHERE PlantillaID = %s AND Estatus IN ('BORRADOR', 'SINCRONIZADA', 'VALIDADA')
        """, (EstatusPlantilla.PUBLICADA.value, datetime.utcnow(), plantilla_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=400, detail="No se puede publicar: estatus inválido o plantilla no encontrada")
        
        conn.commit()
        return {"mensaje": "Plantilla publicada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# SINCRONIZACIÓN
# ============================================================

@router.get("/sync/servidores")
async def listar_servidores_tablajeria():
    """Lista servidores de tablajería disponibles"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        cursor.execute("""
            SELECT id, nombre, system_type, host, port, database_name, activo
            FROM Servidores_Conexiones
            WHERE nombre LIKE '%TABLAJ%' OR database_name LIKE '%tablaj%'
            ORDER BY nombre
        """)
        
        servidores = []
        for row in cursor.fetchall():
            srv = dict(row)
            srv['id'] = str(srv['id'])
            servidores.append(srv)
        
        return {"servidores": servidores, "total": len(servidores)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/sync/ejecutar")
async def ejecutar_sincronizacion(data: SyncRequest):
    """
    Ejecuta sincronización desde un servidor legacy.
    Extrae plantillas y las guarda en EDARSAHUB SQL.
    """
    sync_service = TablajeriaSyncService(DB_CONFIG)
    
    result = sync_service.sync_servidor(
        servidor_id=data.servidor_id,
        entidades=data.entidades,
        forzar_actualizacion=data.forzar_actualizacion
    )
    
    return {
        "success": result.success,
        "servidor_id": result.servidor_id,
        "servidor_nombre": result.servidor_nombre,
        "entidades_procesadas": result.entidades_procesadas,
        "registros_leidos": result.registros_leidos,
        "registros_creados": result.registros_creados,
        "registros_actualizados": result.registros_actualizados,
        "registros_sin_cambios": result.registros_sin_cambios,
        "registros_error": result.registros_error,
        "duracion_segundos": result.duracion_segundos,
        "errores": result.errores[:10]
    }


@router.get("/sync/log")
async def obtener_sync_log(
    servidor_id: Optional[str] = None,
    limit: int = Query(default=20, le=100)
):
    """Obtiene historial de sincronizaciones"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        query = """
            SELECT TOP %s *
            FROM Operaciones_Tablaje_SyncLog
        """
        params = [limit]
        
        if servidor_id:
            query += " WHERE ServidorID = %s"
            params.append(servidor_id)
        
        query += " ORDER BY FechaInicioUTC DESC"
        
        cursor.execute(query, tuple(params))
        logs = []
        for row in cursor.fetchall():
            log = dict(row)
            if log.get('DetallesJSON'):
                try:
                    log['DetallesJSON'] = json.loads(log['DetallesJSON'])
                except:
                    pass
            logs.append(log)
        
        return {"logs": logs, "total": len(logs)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# ESTADÍSTICAS
# ============================================================

@router.get("/stats")
async def obtener_estadisticas(empresa_id: Optional[str] = None):
    """Obtiene estadísticas del módulo de tablajería"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Plantillas por estatus
        query_plantillas = """
            SELECT Estatus, COUNT(*) as total
            FROM Operaciones_Tablaje_Plantillas
            WHERE Activo = 1
        """
        if empresa_id:
            query_plantillas += f" AND EmpresaID = '{empresa_id}'"
        query_plantillas += " GROUP BY Estatus"
        
        cursor.execute(query_plantillas)
        plantillas_estatus = {row['Estatus']: row['total'] for row in cursor.fetchall()}
        
        # Plantillas por origen
        query_origen = """
            SELECT OrigenPlantilla, COUNT(*) as total
            FROM Operaciones_Tablaje_Plantillas
            WHERE Activo = 1
        """
        if empresa_id:
            query_origen += f" AND EmpresaID = '{empresa_id}'"
        query_origen += " GROUP BY OrigenPlantilla"
        
        cursor.execute(query_origen)
        plantillas_origen = {row['OrigenPlantilla']: row['total'] for row in cursor.fetchall()}
        
        # Última sincronización
        cursor.execute("""
            SELECT TOP 1 ServidorNombre, FechaInicioUTC, Estado, RegistrosCreados, RegistrosActualizados
            FROM Operaciones_Tablaje_SyncLog
            ORDER BY FechaInicioUTC DESC
        """)
        ultima_sync = cursor.fetchone()
        
        return {
            "plantillas": {
                "por_estatus": plantillas_estatus,
                "por_origen": plantillas_origen,
                "total": sum(plantillas_estatus.values())
            },
            "ultima_sincronizacion": dict(ultima_sync) if ultima_sync else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()



# ============================================================
# ÓRDENES DE TABLAJE (FASE 5)
# ============================================================

def _get_ordenes_service():
    """Obtiene instancia del servicio de órdenes"""
    return TablajeriaOrdenesService(DB_CONFIG)


@router.get("/ordenes")
async def listar_ordenes(
    empresa_id: Optional[str] = None,
    estatus: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    plantilla_id: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista órdenes de tablaje con filtros.
    
    Permisos requeridos: TABLAJERIA_VER
    """
    try:
        service = _get_ordenes_service()
        
        # Parsear fechas si vienen
        fecha_desde_date = None
        fecha_hasta_date = None
        if fecha_desde:
            fecha_desde_date = date.fromisoformat(fecha_desde)
        if fecha_hasta:
            fecha_hasta_date = date.fromisoformat(fecha_hasta)
        
        result = service.listar_ordenes(
            empresa_id=empresa_id,
            estatus=estatus,
            fecha_desde=fecha_desde_date,
            fecha_hasta=fecha_hasta_date,
            plantilla_id=plantilla_id,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except Exception as e:
        logger.error(f"[Tablajeria] Error listando órdenes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ordenes/{orden_id}")
async def obtener_orden(
    orden_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene una orden con sus detalles.
    
    Permisos requeridos: TABLAJERIA_VER
    """
    try:
        service = _get_ordenes_service()
        orden = service.obtener_orden(orden_id)
        
        if not orden:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        
        return orden
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Tablajeria] Error obteniendo orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ordenes")
async def crear_orden(
    data: OrdenCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea una nueva orden de tablaje basada en una plantilla.
    
    Permisos requeridos: TABLAJERIA_CREAR_ORDEN
    
    La orden se crea en estatus BORRADOR.
    Los detalles se copian automáticamente de la plantilla.
    """
    try:
        service = _get_ordenes_service()
        
        # Obtener UUID del usuario
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.crear_orden(data, usuario_id)
        
        return {
            "success": True,
            "mensaje": f"Orden {result['folio_orden']} creada exitosamente",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Tablajeria] Error creando orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/ordenes/{orden_id}/iniciar")
async def iniciar_ejecucion_orden(
    orden_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Inicia la ejecución de una orden.
    
    Permisos requeridos: TABLAJERIA_EJECUTAR_ORDEN
    
    Cambia estatus de BORRADOR/PLANEADA a EN_EJECUCION.
    """
    try:
        service = _get_ordenes_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.iniciar_ejecucion(orden_id, usuario_id)
        
        return {
            "success": True,
            "mensaje": f"Orden {result['folio']} iniciada",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Tablajeria] Error iniciando orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ResultadosOrdenRequest(BaseModel):
    """Request para registrar resultados de ejecución"""
    cantidad_base_real: Decimal
    peso_inicial_kg: Optional[Decimal] = None
    peso_final_kg: Optional[Decimal] = None
    detalles: List[Dict] = []  # [{orden_detalle_id, cantidad_real, peso_real_kg}]


@router.put("/ordenes/{orden_id}/resultados")
async def registrar_resultados_orden(
    orden_id: str,
    data: ResultadosOrdenRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Registra los resultados reales del tablaje.
    
    Permisos requeridos: TABLAJERIA_EJECUTAR_ORDEN
    
    Body:
    - cantidad_base_real: Cantidad real de insumo procesado
    - peso_inicial_kg: Peso inicial en kg (opcional)
    - peso_final_kg: Peso final en kg (opcional)
    - detalles: Lista de resultados por derivado
    """
    try:
        service = _get_ordenes_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.registrar_resultados(
            orden_id=orden_id,
            cantidad_base_real=data.cantidad_base_real,
            peso_inicial_kg=data.peso_inicial_kg,
            peso_final_kg=data.peso_final_kg,
            detalles=data.detalles,
            usuario_id=usuario_id
        )
        
        return {
            "success": True,
            "mensaje": "Resultados registrados exitosamente",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Tablajeria] Error registrando resultados: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CerrarOrdenRequest(BaseModel):
    """Request para cerrar orden"""
    observaciones: Optional[str] = None


@router.put("/ordenes/{orden_id}/cerrar")
async def cerrar_orden(
    orden_id: str,
    data: Optional[CerrarOrdenRequest] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Cierra una orden después de la ejecución.
    
    Permisos requeridos: TABLAJERIA_CERRAR_ORDEN
    
    Si hay desviaciones fuera de tolerancia, la orden quedará en PENDIENTE_AUTORIZACION.
    """
    try:
        service = _get_ordenes_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.cerrar_orden(
            orden_id=orden_id,
            usuario_id=usuario_id,
            observaciones=data.observaciones if data else None
        )
        
        mensaje = f"Orden {result['folio']} cerrada exitosamente"
        if result.get('requiere_autorizacion'):
            mensaje = f"Orden {result['folio']} requiere autorización: {result.get('motivo_autorizacion')}"
        
        return {
            "success": True,
            "mensaje": mensaje,
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Tablajeria] Error cerrando orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CancelarOrdenRequest(BaseModel):
    """Request para cancelar orden"""
    motivo: str


@router.put("/ordenes/{orden_id}/cancelar")
async def cancelar_orden(
    orden_id: str,
    data: CancelarOrdenRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Cancela una orden.
    
    Permisos requeridos: TABLAJERIA_CANCELAR_ORDEN
    
    Solo se pueden cancelar órdenes que no estén CERRADAS.
    """
    try:
        service = _get_ordenes_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.cancelar_orden(
            orden_id=orden_id,
            usuario_id=usuario_id,
            motivo=data.motivo
        )
        
        return {
            "success": True,
            "mensaje": f"Orden {result['folio']} cancelada",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Tablajeria] Error cancelando orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AutorizarOrdenRequest(BaseModel):
    """Request para autorizar orden"""
    aprobado: bool
    comentarios: Optional[str] = None


@router.put("/ordenes/{orden_id}/autorizar")
async def autorizar_orden(
    orden_id: str,
    data: AutorizarOrdenRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Autoriza o rechaza una orden pendiente.
    
    Permisos requeridos: TABLAJERIA_AUTORIZAR_MERMA
    
    Solo aplica a órdenes en estatus PENDIENTE_AUTORIZACION.
    """
    try:
        service = _get_ordenes_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.autorizar_orden(
            orden_id=orden_id,
            usuario_id=usuario_id,
            aprobado=data.aprobado,
            comentarios=data.comentarios
        )
        
        accion = "aprobada" if data.aprobado else "rechazada"
        return {
            "success": True,
            "mensaje": f"Orden {result['folio']} {accion}",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Tablajeria] Error autorizando orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ESTADÍSTICAS DE ÓRDENES
# ============================================================

@router.get("/ordenes-stats")
async def obtener_estadisticas_ordenes(
    empresa_id: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene estadísticas de órdenes de tablaje.
    
    Permisos requeridos: TABLAJERIA_VER
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Filtro base
        where_clause = "WHERE Activo = 1"
        params = []
        
        if empresa_id:
            where_clause += " AND EmpresaID = %s"
            params.append(empresa_id)
        if fecha_desde:
            where_clause += " AND FechaOperacionMexico >= %s"
            params.append(fecha_desde)
        if fecha_hasta:
            where_clause += " AND FechaOperacionMexico <= %s"
            params.append(fecha_hasta)
        
        # Órdenes por estatus
        cursor.execute(f"""
            SELECT EstatusOrden, COUNT(*) as total
            FROM Operaciones_Tablaje_Ordenes
            {where_clause}
            GROUP BY EstatusOrden
        """, tuple(params) if params else None)
        por_estatus = {row['EstatusOrden']: row['total'] for row in cursor.fetchall()}
        
        # Rendimiento promedio
        cursor.execute(f"""
            SELECT 
                AVG(RendimientoRealPorcentaje) as rendimiento_promedio,
                AVG(MermaRealPorcentaje) as merma_promedio,
                AVG(ABS(DesviacionRendimiento)) as desviacion_promedio,
                COUNT(*) as ordenes_cerradas
            FROM Operaciones_Tablaje_Ordenes
            {where_clause} AND EstatusOrden IN ('CERRADA', 'PENDIENTE_AUTORIZACION')
        """, tuple(params) if params else None)
        metricas = cursor.fetchone()
        
        # Órdenes recientes
        cursor.execute(f"""
            SELECT TOP 5 
                FolioOrden, FechaOperacionMexico, EstatusOrden,
                RendimientoRealPorcentaje, DesviacionRendimiento
            FROM Operaciones_Tablaje_Ordenes
            {where_clause}
            ORDER BY FechaAltaUTC DESC
        """, tuple(params) if params else None)
        recientes = [dict(row) for row in cursor.fetchall()]
        
        return {
            "ordenes_por_estatus": por_estatus,
            "total_ordenes": sum(por_estatus.values()),
            "metricas": {
                "rendimiento_promedio": float(metricas['rendimiento_promedio']) if metricas['rendimiento_promedio'] else None,
                "merma_promedio": float(metricas['merma_promedio']) if metricas['merma_promedio'] else None,
                "desviacion_promedio": float(metricas['desviacion_promedio']) if metricas['desviacion_promedio'] else None,
                "ordenes_analizadas": metricas['ordenes_cerradas']
            },
            "ordenes_recientes": recientes
        }
        
    except Exception as e:
        logger.error(f"[Tablajeria] Error obteniendo stats órdenes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# =============================================================================
# FASE 6: INVENTARIOS, COSTEO Y CONTABILIDAD
# =============================================================================

from .fase6_service import get_tablajeria_fase6_service, ConfigContable
from decimal import Decimal as Dec


@router.post("/ordenes/{orden_id}/fase6/procesar-cierre")
async def procesar_cierre_fase6(
    orden_id: str,
    costo_unitario_insumo: float,
    costo_mano_obra: float = 0,
    costo_indirectos: float = 0,
    costo_energia: float = 0,
    otros_costos: float = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Procesa el cierre completo de Fase 6: Inventarios, Costeo y Contabilidad.
    
    Args:
        orden_id: ID de la orden cerrada
        costo_unitario_insumo: Costo por unidad del insumo base
        costo_mano_obra: Costo de mano de obra (opcional)
        costo_indirectos: Costos indirectos (opcional)
        costo_energia: Costo de energía (opcional)
        otros_costos: Otros costos (opcional)
    """
    try:
        service = get_tablajeria_fase6_service()
        
        costos_adicionales = {
            'mano_obra': Dec(str(costo_mano_obra)),
            'indirectos': Dec(str(costo_indirectos)),
            'energia': Dec(str(costo_energia)),
            'otros': Dec(str(otros_costos))
        }
        
        resultado = service.procesar_cierre_completo(
            orden_id=orden_id,
            costo_unitario_insumo=Dec(str(costo_unitario_insumo)),
            costos_adicionales=costos_adicionales,
            usuario_id=current_user.get('id')
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"[FASE6] Error en proceso cierre: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ordenes/{orden_id}/fase6/afectar-inventario")
async def afectar_inventario(
    orden_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Afecta el inventario de una orden cerrada."""
    try:
        service = get_tablajeria_fase6_service()
        resultado = service.afectar_inventario_orden(orden_id, current_user.get('id'))
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[FASE6] Error afectando inventario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ordenes/{orden_id}/fase6/calcular-costeo")
async def calcular_costeo(
    orden_id: str,
    costo_unitario_insumo: float,
    costo_mano_obra: float = 0,
    costo_indirectos: float = 0,
    costo_energia: float = 0,
    otros_costos: float = 0,
    current_user: dict = Depends(get_current_user)
):
    """Calcula el costeo de producción de una orden."""
    try:
        service = get_tablajeria_fase6_service()
        
        costos = {
            'mano_obra': Dec(str(costo_mano_obra)),
            'indirectos': Dec(str(costo_indirectos)),
            'energia': Dec(str(costo_energia)),
            'otros': Dec(str(otros_costos))
        }
        
        resultado = service.calcular_costeo_orden(
            orden_id=orden_id,
            costo_unitario_insumo=Dec(str(costo_unitario_insumo)),
            costos_adicionales=costos,
            usuario_id=current_user.get('id')
        )
        
        return resultado
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[FASE6] Error calculando costeo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ordenes/{orden_id}/fase6/generar-poliza")
async def generar_poliza(
    orden_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Genera la póliza contable de una orden."""
    try:
        service = get_tablajeria_fase6_service()
        resultado = service.generar_poliza_produccion(orden_id, current_user.get('id'))
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[FASE6] Error generando póliza: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fase6/config-contable/{empresa_id}")
async def obtener_config_contable(
    empresa_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtiene la configuración contable de una empresa."""
    try:
        service = get_tablajeria_fase6_service()
        config = service.obtener_config_contable(empresa_id)
        return {
            "empresa_id": config.empresa_id,
            "cuentas": {
                "almacen_insumos": config.cuenta_almacen_insumos,
                "almacen_productos": config.cuenta_almacen_productos,
                "produccion_proceso": config.cuenta_produccion_proceso,
                "costo_ventas": config.cuenta_costo_ventas,
                "merma_operativa": config.cuenta_merma_operativa,
                "merma_extraordinaria": config.cuenta_merma_extraordinaria,
                "variacion_costo": config.cuenta_variacion_costo
            },
            "opciones": {
                "generar_poliza_automatica": config.generar_poliza_automatica,
                "afectar_inventario_automatico": config.afectar_inventario_automatico,
                "tolerancia_variacion": config.tolerancia_variacion
            }
        }
    except Exception as e:
        logger.error(f"[FASE6] Error obteniendo config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/fase6/config-contable/{empresa_id}")
async def guardar_config_contable(
    empresa_id: str,
    config: dict,
    current_user: dict = Depends(get_current_user)
):
    """Guarda la configuración contable de una empresa."""
    try:
        service = get_tablajeria_fase6_service()
        
        config_obj = ConfigContable(
            empresa_id=empresa_id,
            cuenta_almacen_insumos=config.get('almacen_insumos', '1151-001'),
            cuenta_almacen_productos=config.get('almacen_productos', '1152-001'),
            cuenta_produccion_proceso=config.get('produccion_proceso', '1153-001'),
            cuenta_costo_ventas=config.get('costo_ventas', '5101-001'),
            cuenta_merma_operativa=config.get('merma_operativa', '5102-001'),
            cuenta_merma_extraordinaria=config.get('merma_extraordinaria', '5103-001'),
            cuenta_variacion_costo=config.get('variacion_costo', '5104-001'),
            generar_poliza_automatica=config.get('generar_poliza_automatica', True),
            afectar_inventario_automatico=config.get('afectar_inventario_automatico', True),
            tolerancia_variacion=float(config.get('tolerancia_variacion', 5.0))
        )
        
        exito = service.guardar_config_contable(config_obj, current_user.get('id'))
        
        if exito:
            return {"mensaje": "Configuración guardada exitosamente"}
        else:
            raise HTTPException(status_code=500, detail="Error guardando configuración")
            
    except Exception as e:
        logger.error(f"[FASE6] Error guardando config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

