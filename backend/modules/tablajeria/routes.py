"""
EDARSA HUB - Tablajería Routes
==============================
Endpoints API para el módulo de Tablajería.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import logging
import os
import pymssql
import json

from .schemas import (
    Plantilla, PlantillaCreate, PlantillaUpdate,
    Orden, OrdenCreate, OrdenUpdate,
    SyncRequest, SyncResult,
    EstatusPlantilla, OrigenPlantilla
)
from .sync_service import TablajeriaSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tablajeria", tags=["Tablajería"])

# Configuración DB
DB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
}


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
