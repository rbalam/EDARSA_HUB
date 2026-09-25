from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
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
import uuid

from .schemas import (
    Plantilla, PlantillaCreate, PlantillaUpdate, PlantillaDuplicateRequest,
    Orden, OrdenCreate, OrdenUpdate, OrdenCapturaDirectaCreate,
    SyncRequest, SyncResult,
    EstatusPlantilla, EstatusOrden, OrigenPlantilla
)
from .sync_service import TablajeriaSyncService
from .ordenes_service import TablajeriaOrdenesService
from core.security import get_current_user
from core.config.edarsahub_config import get_edarsahub_sql_config
from core.sql_first.db import get_sql_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tablajeria", tags=["Tablajería"])

# P2-01: Configuración DB centralizada
_edarsa_cfg = get_edarsahub_sql_config()
DB_CONFIG = {
    'host': _edarsa_cfg.host,
    'port': _edarsa_cfg.port,
    'database': _edarsa_cfg.database,
    'username': _edarsa_cfg.user,
    'password': _edarsa_cfg.password
}


def get_connection():
    return get_sql_connection()


def _current_user_id(current_user: Dict) -> Optional[str]:
    if not current_user:
        return None
    return str(
        current_user.get('usuario_id')
        or current_user.get('id')
        or current_user.get('UsuarioID')
        or current_user.get('sub')
        or ''
    ) or None


def _detalle_observaciones(detalle) -> Optional[str]:
    extra = {
        'sku_kg_codigo': getattr(detalle, 'sku_kg_codigo', None),
        'sku_pieza_codigo': getattr(detalle, 'sku_pieza_codigo', None),
        'gramaje_pieza_g': str(getattr(detalle, 'gramaje_pieza_g', None)) if getattr(detalle, 'gramaje_pieza_g', None) is not None else None,
        'captura_por_piezas': getattr(detalle, 'captura_por_piezas', False),
        'costo_fijo': getattr(detalle, 'costo_fijo', False),
        'costo_fijo_unitario': str(getattr(detalle, 'costo_fijo_unitario', None)) if getattr(detalle, 'costo_fijo_unitario', None) is not None else None,
        'prorratea_costo': getattr(detalle, 'prorratea_costo', True),
    }
    payload = {k: v for k, v in extra.items() if v is not None}
    if not payload:
        return getattr(detalle, 'observaciones', None)
    payload['observaciones'] = getattr(detalle, 'observaciones', None)
    return json.dumps({'uat_scope_lonja_plantillas': payload}, ensure_ascii=False)


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
        raise HTTPException(status_code=500, detail="Error interno del servidor")
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
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    finally:
        conn.close()


@router.post("/plantillas")
async def crear_plantilla(data: PlantillaCreate, current_user: Dict = Depends(get_current_user)):
    """Crea una plantilla editable en BORRADOR."""
    conn = get_connection()
    plantilla_id = str(uuid.uuid4())
    now_utc = datetime.utcnow()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Operaciones_Tablaje_Plantillas (
                PlantillaID, EmpresaID, UnidadNegocioID, SucursalID,
                CodigoPlantilla, NombrePlantilla, Descripcion,
                TipoTransformacion, InsumoBaseCodigo, InsumoBaseNombre,
                UnidadBaseCodigo, CantidadBaseEstandar,
                RendimientoEsperadoPorcentaje, MermaEsperadaPorcentaje,
                ToleranciaRendimiento, ReglaCosteo, OrigenPlantilla,
                VersionActual, Estatus, Activo, FechaAltaUTC,
                FechaOperacionMexico, UsuarioAltaID
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            plantilla_id, data.empresa_id, data.unidad_negocio_pk, data.sucursal_id,
            data.codigo_plantilla, data.nombre_plantilla, data.descripcion,
            data.tipo_transformacion, data.insumo_base_codigo, data.insumo_base_nombre,
            data.unidad_base_codigo, data.cantidad_base_estandar,
            data.rendimiento_esperado_porcentaje, data.merma_esperada_porcentaje,
            data.tolerancia_rendimiento, data.regla_costeo.value if data.regla_costeo else None,
            OrigenPlantilla.CAPTURA_DIRECTA_EDARSAHUB.value, 1,
            EstatusPlantilla.BORRADOR.value, True, now_utc, date.today(),
            _current_user_id(current_user)
        ))
        for detalle in data.detalles or []:
            cursor.execute("""
                INSERT INTO Operaciones_Tablaje_PlantillasDetalle (
                    PlantillaDetalleID, PlantillaID, ProductoDerivadoCodigo,
                    ProductoDerivadoNombre, TipoDerivado, UnidadDerivadoCodigo,
                    CantidadEsperada, PorcentajeRendimientoEsperado, PorcentajeCostoAsignado,
                    EsMerma, EsSubproducto, EsProductoVendible, EsInventariable,
                    OrdenVisual, Observaciones, Activo
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                str(uuid.uuid4()), plantilla_id, detalle.producto_derivado_codigo,
                detalle.producto_derivado_nombre, detalle.tipo_derivado.value,
                detalle.unidad_derivado_codigo, detalle.cantidad_esperada,
                detalle.porcentaje_rendimiento_esperado, detalle.porcentaje_costo_asignado,
                detalle.es_merma, detalle.es_subproducto, detalle.es_producto_vendible,
                detalle.es_inventariable, detalle.orden_visual, _detalle_observaciones(detalle), True
            ))
        conn.commit()
        return {"mensaje": "Plantilla creada en borrador", "plantilla_id": plantilla_id}
    except Exception as e:
        conn.rollback()
        logger.error(f"[Tablajeria] Error creando plantilla: {e}")
        raise HTTPException(status_code=500, detail="Error creando plantilla")
    finally:
        conn.close()


@router.put("/plantillas/{plantilla_id}")
async def editar_plantilla(plantilla_id: str, data: PlantillaUpdate, current_user: Dict = Depends(get_current_user)):
    """Edita una plantilla solo si esta en BORRADOR/OBSERVADA. Plantillas publicadas se versionan con /duplicar."""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT Estatus FROM Operaciones_Tablaje_Plantillas WHERE PlantillaID = %s AND Activo = 1", (plantilla_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        if row['Estatus'] not in ('BORRADOR', 'OBSERVADA'):
            raise HTTPException(status_code=409, detail="Plantilla ya usada/publicada: duplicar para crear nueva version")
        updates = []
        params = []
        mapping = {
            'nombre_plantilla': 'NombrePlantilla',
            'descripcion': 'Descripcion',
            'rendimiento_esperado_porcentaje': 'RendimientoEsperadoPorcentaje',
            'merma_esperada_porcentaje': 'MermaEsperadaPorcentaje',
            'tolerancia_rendimiento': 'ToleranciaRendimiento',
            'regla_costeo': 'ReglaCosteo',
            'estatus': 'Estatus'
        }
        for attr, column in mapping.items():
            value = getattr(data, attr, None)
            if value is not None:
                updates.append(f"{column} = %s")
                params.append(value.value if hasattr(value, 'value') else value)
        if updates:
            updates.append("FechaModificacionUTC = %s")
            updates.append("UsuarioModificacionID = %s")
            params.extend([datetime.utcnow(), _current_user_id(current_user)])
            params.append(plantilla_id)
            cursor.execute(f"UPDATE Operaciones_Tablaje_Plantillas SET {', '.join(updates)} WHERE PlantillaID = %s", tuple(params))
        if data.detalles is not None:
            cursor.execute("UPDATE Operaciones_Tablaje_PlantillasDetalle SET Activo = 0 WHERE PlantillaID = %s", (plantilla_id,))
            for detalle in data.detalles:
                cursor.execute("""
                    INSERT INTO Operaciones_Tablaje_PlantillasDetalle (
                        PlantillaDetalleID, PlantillaID, ProductoDerivadoCodigo, ProductoDerivadoNombre,
                        TipoDerivado, UnidadDerivadoCodigo, CantidadEsperada, PorcentajeRendimientoEsperado,
                        PorcentajeCostoAsignado, EsMerma, EsSubproducto, EsProductoVendible, EsInventariable,
                        OrdenVisual, Observaciones, Activo
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(uuid.uuid4()), plantilla_id, detalle.producto_derivado_codigo, detalle.producto_derivado_nombre,
                    detalle.tipo_derivado.value, detalle.unidad_derivado_codigo, detalle.cantidad_esperada,
                    detalle.porcentaje_rendimiento_esperado, detalle.porcentaje_costo_asignado,
                    detalle.es_merma, detalle.es_subproducto, detalle.es_producto_vendible, detalle.es_inventariable,
                    detalle.orden_visual, _detalle_observaciones(detalle), True
                ))
        conn.commit()
        return {"mensaje": "Plantilla actualizada", "plantilla_id": plantilla_id}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"[Tablajeria] Error editando plantilla: {e}")
        raise HTTPException(status_code=500, detail="Error editando plantilla")
    finally:
        conn.close()


@router.post("/plantillas/{plantilla_id}/duplicar")
async def duplicar_plantilla(plantilla_id: str, data: PlantillaDuplicateRequest, current_user: Dict = Depends(get_current_user)):
    """Duplica una plantilla para versionar sin reescribir historia operativa."""
    conn = get_connection()
    nueva_id = str(uuid.uuid4())
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT * FROM Operaciones_Tablaje_Plantillas WHERE PlantillaID = %s AND Activo = 1", (plantilla_id,))
        base = cursor.fetchone()
        if not base:
            raise HTTPException(status_code=404, detail="Plantilla base no encontrada")
        cursor.execute("""
            INSERT INTO Operaciones_Tablaje_Plantillas (
                PlantillaID, EmpresaID, UnidadNegocioID, SucursalID, CodigoPlantilla, NombrePlantilla,
                Descripcion, TipoTransformacion, InsumoBaseCodigo, InsumoBaseNombre, UnidadBaseCodigo,
                CantidadBaseEstandar, RendimientoEsperadoPorcentaje, MermaEsperadaPorcentaje,
                ToleranciaRendimiento, ReglaCosteo, OrigenPlantilla, PlantillaPadreID,
                VersionActual, Estatus, Activo, FechaAltaUTC, FechaOperacionMexico, UsuarioAltaID
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            nueva_id, base.get('EmpresaID'), base.get('UnidadNegocioID'), base.get('SucursalID'),
            data.codigo_plantilla or f"{base.get('CodigoPlantilla')}-V{int(base.get('VersionActual') or 1) + 1}",
            data.nombre_plantilla or f"{base.get('NombrePlantilla')} v{int(base.get('VersionActual') or 1) + 1}",
            data.descripcion or base.get('Descripcion'), base.get('TipoTransformacion'), base.get('InsumoBaseCodigo'),
            base.get('InsumoBaseNombre'), base.get('UnidadBaseCodigo'), base.get('CantidadBaseEstandar'),
            base.get('RendimientoEsperadoPorcentaje'), base.get('MermaEsperadaPorcentaje'), base.get('ToleranciaRendimiento'),
            base.get('ReglaCosteo'), OrigenPlantilla.CAPTURA_DIRECTA_EDARSAHUB.value, plantilla_id,
            int(base.get('VersionActual') or 1) + 1, EstatusPlantilla.BORRADOR.value, True, datetime.utcnow(),
            date.today(), _current_user_id(current_user)
        ))
        cursor.execute("SELECT * FROM Operaciones_Tablaje_PlantillasDetalle WHERE PlantillaID = %s AND Activo = 1 ORDER BY OrdenVisual", (plantilla_id,))
        for det in cursor.fetchall():
            cursor.execute("""
                INSERT INTO Operaciones_Tablaje_PlantillasDetalle (
                    PlantillaDetalleID, PlantillaID, ProductoDerivadoID, ProductoDerivadoCodigo, ProductoDerivadoNombre,
                    TipoDerivado, UnidadDerivadoCodigo, CantidadEsperada, PorcentajeRendimientoEsperado,
                    PorcentajeCostoAsignado, EsMerma, EsSubproducto, EsProductoVendible, EsInventariable,
                    OrdenVisual, Observaciones, Activo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()), nueva_id, det.get('ProductoDerivadoID'), det.get('ProductoDerivadoCodigo'),
                det.get('ProductoDerivadoNombre'), det.get('TipoDerivado'), det.get('UnidadDerivadoCodigo'),
                det.get('CantidadEsperada'), det.get('PorcentajeRendimientoEsperado'), det.get('PorcentajeCostoAsignado'),
                det.get('EsMerma'), det.get('EsSubproducto'), det.get('EsProductoVendible'), det.get('EsInventariable'),
                det.get('OrdenVisual'), det.get('Observaciones'), True
            ))
        conn.commit()
        return {"mensaje": "Plantilla duplicada como nueva version", "plantilla_id": nueva_id, "plantilla_padre_id": plantilla_id}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"[Tablajeria] Error duplicando plantilla: {e}")
        raise HTTPException(status_code=500, detail="Error duplicando plantilla")
    finally:
        conn.close()


@router.get("/lonjas-disponibles")
async def listar_lonjas_disponibles(
    empresa_id: Optional[str] = None,
    unidad_negocio_pk: Optional[str] = None,
    almacen_origen_id: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """Lista lonjas disponibles no procesadas para tablajear una por una."""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        query = """
            SELECT TOP (%s) *
            FROM dbo.Tablajeria_LonjasDisponibles
            WHERE Procesada = 0 AND Activo = 1
        """
        params = [limit]
        if empresa_id:
            query += " AND EmpresaID = %s"
            params.append(empresa_id)
        if unidad_negocio_pk:
            query += " AND UnidadNegocioID = %s"
            params.append(unidad_negocio_pk)
        if almacen_origen_id:
            query += " AND AlmacenOrigenID = %s"
            params.append(almacen_origen_id)
        query += " ORDER BY FechaAltaUTC DESC"
        cursor.execute(query, tuple(params))
        rows = []
        for row in cursor.fetchall():
            item = dict(row)
            for key, value in list(item.items()):
                if value is not None and not isinstance(value, (str, int, float, bool)):
                    item[key] = str(value)
            rows.append(item)
        return {"lonjas": rows, "total": len(rows), "modo": "NO_PROCESADAS"}
    except Exception as e:
        logger.error(f"[Tablajeria] Error listando lonjas disponibles: {e}")
        raise HTTPException(status_code=500, detail="Error listando lonjas disponibles")
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
        raise HTTPException(status_code=500, detail="Error interno del servidor")
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
        raise HTTPException(status_code=500, detail="Error interno del servidor")
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
                except Exception:
                    pass
            logs.append(log)
        
        return {"logs": logs, "total": len(logs)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")
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
        raise HTTPException(status_code=500, detail="Error interno del servidor")
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
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[Tablajeria] Error creando orden: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/ordenes/captura-directa")
async def crear_orden_captura_directa(
    data: OrdenCapturaDirectaCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 4: Captura Directa.
    
    Crea una orden de tablaje especificando manualmente el insumo base
    y los productos derivados esperados. No requiere plantilla predefinida.
    
    Útil para:
    - Órdenes únicas o especiales
    - Pruebas de nuevas recetas
    - Productos no estandarizados
    
    Permisos requeridos: TABLAJERIA_CREAR_ORDEN
    """
    try:
        service = _get_ordenes_service()
        
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        result = service.crear_orden_captura_directa(data, usuario_id)
        
        return {
            "success": True,
            "mensaje": f"Orden {result['folio_orden']} creada exitosamente (Captura Directa)",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[Tablajeria] Error creando orden captura directa: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[Tablajeria] Error iniciando orden: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[Tablajeria] Error registrando resultados: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


class CerrarOrdenRequest(BaseModel):
    """Request para cerrar orden con parámetros opcionales de Fase 6."""
    observaciones: Optional[str] = None
    # Fase 6 - Costeo (opcional, si se omite no se calcula costeo)
    costo_unitario_insumo: Optional[float] = None
    costo_mano_obra: Optional[float] = 0
    costo_indirectos: Optional[float] = 0
    costo_energia: Optional[float] = 0
    otros_costos: Optional[float] = 0
    # Flags de control
    ejecutar_fase6: bool = True  # Si True, ejecuta Fase 6 automáticamente


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
    
    FASE 6 (Integración automática):
    Si se proporciona costo_unitario_insumo y ejecutar_fase6=True, al cerrar la orden se ejecuta:
    1. Afectación de inventarios
    2. Cálculo de costeo
    3. Generación de póliza contable
    """
    try:
        service = _get_ordenes_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        
        # 1. Cerrar la orden primero
        result = service.cerrar_orden(
            orden_id=orden_id,
            usuario_id=usuario_id,
            observaciones=data.observaciones if data else None
        )
        
        mensaje = f"Orden {result['folio']} cerrada exitosamente"
        fase6_result = None
        
        if result.get('requiere_autorizacion'):
            mensaje = f"Orden {result['folio']} requiere autorización: {result.get('motivo_autorizacion')}"
        else:
            # 2. Si la orden está CERRADA (no pendiente), ejecutar Fase 6 si aplica
            if data and data.ejecutar_fase6 and data.costo_unitario_insumo is not None:
                try:
                    fase6_service = get_tablajeria_fase6_service()
                    
                    costos_adicionales = {
                        'mano_obra': Dec(str(data.costo_mano_obra or 0)),
                        'indirectos': Dec(str(data.costo_indirectos or 0)),
                        'energia': Dec(str(data.costo_energia or 0)),
                        'otros': Dec(str(data.otros_costos or 0))
                    }
                    
                    fase6_result = fase6_service.procesar_cierre_completo(
                        orden_id=orden_id,
                        costo_unitario_insumo=Dec(str(data.costo_unitario_insumo)),
                        costos_adicionales=costos_adicionales,
                        usuario_id=usuario_id
                    )
                    
                    if fase6_result.get('exito'):
                        mensaje += " | Fase 6 completada: Inventario, Costeo y Póliza procesados"
                    else:
                        mensaje += f" | Fase 6 con errores: {', '.join(fase6_result.get('errores', []))}"
                    
                    logger.info(f"[Tablajeria] Fase 6 ejecutada para orden {result['folio']}")
                    
                except Exception as e:
                    logger.error(f"[Tablajeria] Error en Fase 6 para orden {orden_id}: {e}")
                    fase6_result = {"exito": False, "errores": [str(e)]}
                    mensaje += f" | Fase 6 falló: {str(e)}"
        
        response = {
            "success": True,
            "mensaje": mensaje,
            **result
        }
        
        if fase6_result:
            response["fase6"] = fase6_result
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[Tablajeria] Error cerrando orden: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[Tablajeria] Error cancelando orden: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[Tablajeria] Error autorizando orden: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=500, detail="Error interno del servidor")
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
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[FASE6] Error afectando inventario: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[FASE6] Error calculando costeo: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[FASE6] Error generando póliza: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=500, detail="Error interno del servidor")



# ============================================================================
# DASHBOARD Y REPORTES DE TABLAJERÍA
# ============================================================================

from .dashboard_service import get_tablajeria_dashboard_service


@router.get("/dashboard/kpis")
async def get_dashboard_kpis(
    empresa_id: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene KPIs generales de tablajería.
    
    Permisos requeridos: TABLAJERIA_VER
    
    Returns:
        KPIs de órdenes, rendimientos, mermas y costeo
    """
    try:
        service = get_tablajeria_dashboard_service()
        return service.get_kpis_generales(empresa_id, fecha_inicio, fecha_fin)
    except Exception as e:
        logger.error(f"[Dashboard] Error obteniendo KPIs: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/dashboard/rendimientos-plantilla")
async def get_rendimientos_por_plantilla(
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene análisis de rendimientos agrupados por plantilla.
    
    Permisos requeridos: TABLAJERIA_VER
    
    Returns:
        Lista de plantillas con métricas de rendimiento
    """
    try:
        service = get_tablajeria_dashboard_service()
        return service.get_rendimientos_por_plantilla(limit)
    except Exception as e:
        logger.error(f"[Dashboard] Error obteniendo rendimientos por plantilla: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/dashboard/tendencia")
async def get_tendencia_rendimientos(
    dias: int = Query(30, ge=7, le=365),
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene tendencia de rendimientos en los últimos N días.
    
    Permisos requeridos: TABLAJERIA_VER
    
    Returns:
        Lista de puntos de datos para gráfico de tendencia
    """
    try:
        service = get_tablajeria_dashboard_service()
        return service.get_tendencia_rendimientos(dias)
    except Exception as e:
        logger.error(f"[Dashboard] Error obteniendo tendencia: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/dashboard/top-mermas")
async def get_top_mermas(
    limit: int = Query(10, ge=1, le=50),
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene los productos derivados con mayor merma.
    
    Permisos requeridos: TABLAJERIA_VER
    
    Returns:
        Lista de productos con análisis de mermas
    """
    try:
        service = get_tablajeria_dashboard_service()
        return service.get_top_mermas(limit)
    except Exception as e:
        logger.error(f"[Dashboard] Error obteniendo top mermas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/dashboard/alertas")
async def get_alertas_rendimiento(
    umbral: float = Query(5.0, ge=1.0, le=50.0, description="Umbral de desviación para generar alerta"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene alertas de órdenes con desviaciones fuera de umbral.
    
    Permisos requeridos: TABLAJERIA_VER
    
    Returns:
        Lista de alertas de rendimiento
    """
    try:
        service = get_tablajeria_dashboard_service()
        return service.get_alertas_rendimiento(umbral)
    except Exception as e:
        logger.error(f"[Dashboard] Error obteniendo alertas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/dashboard/resumen-costeo")
async def get_resumen_costeo(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene resumen de costeo de producción.
    
    Permisos requeridos: TABLAJERIA_VER
    
    Returns:
        Métricas de costeo con desglose
    """
    try:
        service = get_tablajeria_dashboard_service()
        return service.get_resumen_costeo(fecha_inicio, fecha_fin)
    except Exception as e:
        logger.error(f"[Dashboard] Error obteniendo resumen costeo: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ============================================================================
# REPORTES EXPORTABLES
# ============================================================================

@router.get("/reportes/ordenes")
async def exportar_ordenes(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    estatus: Optional[str] = None,
    formato: str = Query("json", enum=["json", "csv"]),
    current_user: Dict = Depends(get_current_user)
):
    """
    Exporta reporte de órdenes de tablajería.
    
    Permisos requeridos: TABLAJERIA_EXPORTAR
    
    Returns:
        Datos de órdenes en formato especificado
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(as_dict=True)
        
        where_clauses = ["1=1"]
        params = []
        
        if fecha_inicio:
            where_clauses.append("FechaOperacionMexico >= %s")
            params.append(fecha_inicio)
        if fecha_fin:
            where_clauses.append("FechaOperacionMexico <= %s")
            params.append(fecha_fin)
        if estatus:
            where_clauses.append("EstatusOrden = %s")
            params.append(estatus)
        
        query = f"""
            SELECT 
                FolioOrden, OrigenOrden, EstatusOrden,
                InsumoBaseCodigo, InsumoBaseNombre,
                CantidadBasePlaneada, CantidadBaseReal,
                RendimientoEsperadoPorcentaje, RendimientoRealPorcentaje,
                DesviacionRendimiento, FechaOperacionMexico,
                FechaInicioEjecucion, FechaCierreOrden, Observaciones
            FROM Operaciones_Tablaje_Ordenes
            WHERE {' AND '.join(where_clauses)}
            ORDER BY FechaOperacionMexico DESC
        """
        
        cursor.execute(query, params)
        ordenes = []
        for row in cursor.fetchall():
            ordenes.append({
                "folio": row['FolioOrden'],
                "origen": row['OrigenOrden'],
                "estatus": row['EstatusOrden'],
                "insumo_codigo": row['InsumoBaseCodigo'],
                "insumo_nombre": row['InsumoBaseNombre'],
                "cantidad_planeada": float(row['CantidadBasePlaneada'] or 0),
                "cantidad_real": float(row['CantidadBaseReal'] or 0),
                "rendimiento_esperado": float(row['RendimientoEsperadoPorcentaje'] or 0),
                "rendimiento_real": float(row['RendimientoRealPorcentaje'] or 0),
                "desviacion": float(row['DesviacionRendimiento'] or 0),
                "fecha_operacion": row['FechaOperacionMexico'].strftime('%Y-%m-%d') if row['FechaOperacionMexico'] else None,
                "fecha_inicio": row['FechaInicioEjecucion'].strftime('%Y-%m-%d %H:%M') if row['FechaInicioEjecucion'] else None,
                "fecha_cierre": row['FechaCierreOrden'].strftime('%Y-%m-%d %H:%M') if row['FechaCierreOrden'] else None,
                "observaciones": row['Observaciones']
            })
        
        conn.close()
        
        if formato == "csv":
            import csv
            import io
            from fastapi.responses import StreamingResponse
            
            output = io.StringIO()
            if ordenes:
                writer = csv.DictWriter(output, fieldnames=ordenes[0].keys())
                writer.writeheader()
                writer.writerows(ordenes)
            
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=ordenes_tablajeria.csv"}
            )
        
        return {"ordenes": ordenes, "total": len(ordenes)}
        
    except Exception as e:
        logger.error(f"[Reportes] Error exportando órdenes: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/reportes/mermas")
async def exportar_mermas(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Exporta reporte de mermas de producción.
    
    Permisos requeridos: TABLAJERIA_EXPORTAR
    
    Returns:
        Datos de mermas agrupados
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(as_dict=True)
        
        where_fecha = ""
        params = []
        if fecha_inicio and fecha_fin:
            where_fecha = "AND o.FechaOperacionMexico BETWEEN %s AND %s"
            params = [fecha_inicio, fecha_fin]
        
        cursor.execute(f"""
            SELECT 
                d.ProductoDerivadoNombre,
                d.ProductoDerivadoCodigo,
                o.FolioOrden,
                o.InsumoBaseNombre,
                d.CantidadEsperada,
                d.CantidadReal,
                d.PorcentajeEsperado,
                d.PorcentajeReal,
                o.FechaOperacionMexico
            FROM Operaciones_Tablaje_OrdenesDetalle d
            INNER JOIN Operaciones_Tablaje_Ordenes o ON d.OrdenID = o.OrdenID
            WHERE d.TipoDerivado = 'MERMA'
            AND o.EstatusOrden = 'CERRADA'
            {where_fecha}
            ORDER BY o.FechaOperacionMexico DESC
        """, params)
        
        mermas = []
        for row in cursor.fetchall():
            mermas.append({
                "producto": row['ProductoDerivadoNombre'],
                "codigo": row['ProductoDerivadoCodigo'],
                "folio_orden": row['FolioOrden'],
                "insumo_base": row['InsumoBaseNombre'],
                "cantidad_esperada_kg": float(row['CantidadEsperada'] or 0),
                "cantidad_real_kg": float(row['CantidadReal'] or 0),
                "porcentaje_esperado": float(row['PorcentajeEsperado'] or 0),
                "porcentaje_real": float(row['PorcentajeReal'] or 0),
                "fecha": row['FechaOperacionMexico'].strftime('%Y-%m-%d') if row['FechaOperacionMexico'] else None
            })
        
        conn.close()
        
        # Resumen
        total_esperado = sum(m['cantidad_esperada_kg'] for m in mermas)
        total_real = sum(m['cantidad_real_kg'] for m in mermas)
        
        return {
            "mermas": mermas,
            "total": len(mermas),
            "resumen": {
                "total_esperado_kg": total_esperado,
                "total_real_kg": total_real,
                "diferencia_kg": total_real - total_esperado
            }
        }
        
    except Exception as e:
        logger.error(f"[Reportes] Error exportando mermas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/reportes/costeo")
async def exportar_costeo(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Exporta reporte de costeo de producción.
    
    Permisos requeridos: TABLAJERIA_EXPORTAR
    
    Returns:
        Datos de costeo con desglose por orden
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(as_dict=True)
        
        cursor.execute("""
            SELECT 
                c.CosteoID,
                o.FolioOrden,
                o.InsumoBaseNombre,
                c.CostoTotalInsumo,
                c.CostoManoObra,
                c.CostoIndirectos,
                c.CostoEnergia,
                c.OtrosCostos,
                c.CostoTotalProduccion,
                c.CostoUnitarioPromedio,
                c.CantidadInsumoConsumida,
                c.ReglaCosteoAplicada,
                c.FechaCosteo
            FROM Tablajeria_CosteoProduccion c
            INNER JOIN Operaciones_Tablaje_Ordenes o ON c.OrdenID = o.OrdenID
            ORDER BY c.FechaCosteo DESC
        """)
        
        costeos = []
        for row in cursor.fetchall():
            costeos.append({
                "costeo_id": str(row['CosteoID']),
                "folio_orden": row['FolioOrden'],
                "insumo": row['InsumoBaseNombre'],
                "costo_insumo": float(row['CostoTotalInsumo'] or 0),
                "costo_mano_obra": float(row['CostoManoObra'] or 0),
                "costo_indirectos": float(row['CostoIndirectos'] or 0),
                "costo_energia": float(row['CostoEnergia'] or 0),
                "otros_costos": float(row['OtrosCostos'] or 0),
                "costo_total": float(row['CostoTotalProduccion'] or 0),
                "costo_unitario": float(row['CostoUnitarioPromedio'] or 0),
                "kg_producidos": float(row['CantidadInsumoConsumida'] or 0),
                "regla": row['ReglaCosteoAplicada'],
                "fecha": row['FechaCosteo'].strftime('%Y-%m-%d %H:%M') if row['FechaCosteo'] else None
            })
        
        conn.close()
        
        return {"costeos": costeos, "total": len(costeos)}
        
    except Exception as e:
        logger.error(f"[Reportes] Error exportando costeo: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ============================================================================
# R24: RENDIMIENTO POR LOTE PROVEEDOR Y RECLAMOS
# ============================================================================

from .lote_proveedor_service import get_tablajeria_lote_proveedor_service


class ReclamoProveedorCreateRequest(BaseModel):
    motivo: str
    descripcion: Optional[str] = None
    prioridad: str = "MEDIA"
    evidencia: Optional[Dict] = None


@router.get("/lotes-proveedor/rendimientos")
async def listar_rendimientos_lote_proveedor(
    empresa_id: Optional[str] = None,
    proveedor_id: Optional[str] = None,
    lote: Optional[str] = None,
    semaforo: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Dict = Depends(get_current_user)
):
    """Lista rendimientos de tablajeria por lote proveedor."""
    try:
        service = get_tablajeria_lote_proveedor_service()
        return service.listar_rendimientos_lote(empresa_id, proveedor_id, lote, semaforo, limit, offset)
    except Exception as e:
        logger.error(f"[R24] Error listando rendimientos por lote proveedor: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/lotes-proveedor/{lote_rendimiento_id}/drilldown")
async def obtener_drilldown_lote_proveedor(
    lote_rendimiento_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Drilldown lote -> proveedor -> compra -> recepcion -> tablajeria -> reclamos."""
    try:
        service = get_tablajeria_lote_proveedor_service()
        return service.obtener_drilldown_lote(lote_rendimiento_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[R24] Error obteniendo drilldown de lote proveedor: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/lotes-proveedor/{lote_rendimiento_id}/reclamos")
async def crear_reclamo_lote_proveedor(
    lote_rendimiento_id: str,
    data: ReclamoProveedorCreateRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Abre reclamo proveedor ligado a rendimiento de lote."""
    try:
        usuario_id = current_user.get('public_uuid') or current_user.get('id') or str(current_user.get('_id', ''))
        service = get_tablajeria_lote_proveedor_service()
        return service.crear_reclamo_proveedor(
            lote_rendimiento_id=lote_rendimiento_id,
            motivo=data.motivo,
            descripcion=data.descripcion,
            prioridad=data.prioridad,
            evidencia=data.evidencia,
            usuario_id=usuario_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[R24] Error creando reclamo proveedor: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/reclamos-proveedor")
async def listar_reclamos_proveedor(
    estatus: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """Lista reclamos proveedor de tablajeria."""
    try:
        service = get_tablajeria_lote_proveedor_service()
        return service.listar_reclamos(estatus=estatus, limit=limit)
    except Exception as e:
        logger.error(f"[R24] Error listando reclamos proveedor: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
