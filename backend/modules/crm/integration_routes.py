"""
EDARSA HUB - CRM Integration Routes
====================================
Endpoints API para gestionar conectores CRM y sincronizaciones.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import json
import os
import pymssql

from .integration import (
    SyncEngine, SyncJob, StagingService,
    SyncDirection, SyncStatus, StagingProcessor, MatchAction
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/crm/integration", tags=["CRM Integration"])

# Configuración DB
DB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
}


# ============================================================
# SCHEMAS
# ============================================================

class ConectorCreate(BaseModel):
    empresa_id: str
    codigo: str = Field(..., max_length=50, description="Código único: VTIGER, SALESFORCE, etc.")
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    tipo_conector: str = Field(..., description="Tipo: VTIGER, SALESFORCE, HUBSPOT")
    configuracion: dict = Field(default_factory=dict, description="Config JSON: url, username, access_key")
    activo: bool = True
    es_principal: bool = False


class ConectorUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    configuracion: Optional[dict] = None
    activo: Optional[bool] = None
    es_principal: Optional[bool] = None


class TestConnectionRequest(BaseModel):
    tipo: str = Field(..., description="VTIGER, SALESFORCE, etc.")
    base_url: str
    username: str
    access_key: str


class SyncRequest(BaseModel):
    entidades: List[str] = Field(default=['leads', 'oportunidades', 'cuentas'])
    desde_fecha: Optional[datetime] = None


class ProcessStagingRequest(BaseModel):
    entidades: List[str] = Field(default=['leads', 'cuentas', 'oportunidades'])
    accion_duplicados: str = Field(default='MARCAR_CONFLICTO', 
        description="CREAR_NUEVO, ACTUALIZAR_EXISTENTE, MARCAR_CONFLICTO, OMITIR")
    limit: int = Field(default=100, le=500)


class ResolveConflictRequest(BaseModel):
    accion: str = Field(..., description="CREAR_NUEVO, ACTUALIZAR_EXISTENTE, OMITIR")


# ============================================================
# HELPERS
# ============================================================

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
# CONECTORES CRUD
# ============================================================

@router.get("/conectores")
async def listar_conectores(
    empresa_id: Optional[str] = None,
    activo: Optional[bool] = None
):
    """Lista todos los conectores configurados"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        query = "SELECT * FROM CRM_Integracion_Conectores WHERE 1=1"
        params = []
        
        if empresa_id:
            query += " AND EmpresaID = %s"
            params.append(empresa_id)
        if activo is not None:
            query += " AND Activo = %s"
            params.append(1 if activo else 0)
        
        query += " ORDER BY Nombre"
        
        cursor.execute(query, tuple(params) if params else None)
        rows = cursor.fetchall()
        
        # Parsear JSON de configuración
        conectores = []
        for row in rows:
            conector = dict(row)
            # Convertir campos JSON
            for field in ['ConfiguracionJSON', 'MapeoLeadsJSON', 'MapeoOportunidadesJSON', 
                         'MapeoCuentasJSON', 'MapeoContactosJSON']:
                if conector.get(field):
                    try:
                        conector[field] = json.loads(conector[field])
                    except:
                        pass
            # Convertir UUIDs a string
            for field in ['EmpresaID', 'CreatedBy', 'UpdatedBy']:
                if conector.get(field):
                    conector[field] = str(conector[field])
            conectores.append(conector)
        
        return {"conectores": conectores, "total": len(conectores)}
        
    except Exception as e:
        logger.error(f"[Integration] Error listando conectores: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/conectores/{conector_id}")
async def obtener_conector(conector_id: int):
    """Obtiene un conector por ID"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT * FROM CRM_Integracion_Conectores WHERE ConectorID = %s", (conector_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Conector no encontrado")
        
        conector = dict(row)
        for field in ['ConfiguracionJSON', 'MapeoLeadsJSON', 'MapeoOportunidadesJSON']:
            if conector.get(field):
                try:
                    conector[field] = json.loads(conector[field])
                except:
                    pass
        
        for field in ['EmpresaID', 'CreatedBy', 'UpdatedBy']:
            if conector.get(field):
                conector[field] = str(conector[field])
        
        return conector
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Integration] Error obteniendo conector: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/conectores")
async def crear_conector(data: ConectorCreate):
    """Crea un nuevo conector"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        now = datetime.now()
        
        # Verificar código único por empresa
        cursor.execute("""
            SELECT ConectorID FROM CRM_Integracion_Conectores 
            WHERE EmpresaID = %s AND Codigo = %s
        """, (data.empresa_id, data.codigo))
        
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Ya existe un conector con código {data.codigo}")
        
        config_json = json.dumps(data.configuracion)
        
        cursor.execute("""
            INSERT INTO CRM_Integracion_Conectores (
                EmpresaID, Codigo, Nombre, Descripcion, TipoConector,
                ConfiguracionJSON, Activo, EsPrincipal, EstadoConexion,
                CreatedAt, UpdatedAt
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            data.empresa_id,
            data.codigo.upper(),
            data.nombre,
            data.descripcion,
            data.tipo_conector.upper(),
            config_json,
            1 if data.activo else 0,
            1 if data.es_principal else 0,
            'PENDIENTE',
            now,
            now
        ))
        
        cursor.execute("SELECT SCOPE_IDENTITY() as id")
        new_id = cursor.fetchone()['id']
        
        conn.commit()
        
        logger.info(f"[Integration] Conector creado: {data.codigo} (ID: {new_id})")
        return {"conector_id": int(new_id), "mensaje": "Conector creado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"[Integration] Error creando conector: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.put("/conectores/{conector_id}")
async def actualizar_conector(conector_id: int, data: ConectorUpdate):
    """Actualiza un conector existente"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Verificar existencia
        cursor.execute("SELECT ConectorID FROM CRM_Integracion_Conectores WHERE ConectorID = %s", (conector_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Conector no encontrado")
        
        # Construir UPDATE dinámico
        updates = []
        params = []
        
        if data.nombre is not None:
            updates.append("Nombre = %s")
            params.append(data.nombre)
        if data.descripcion is not None:
            updates.append("Descripcion = %s")
            params.append(data.descripcion)
        if data.configuracion is not None:
            updates.append("ConfiguracionJSON = %s")
            params.append(json.dumps(data.configuracion))
        if data.activo is not None:
            updates.append("Activo = %s")
            params.append(1 if data.activo else 0)
        if data.es_principal is not None:
            updates.append("EsPrincipal = %s")
            params.append(1 if data.es_principal else 0)
        
        if not updates:
            return {"mensaje": "No hay cambios"}
        
        updates.append("UpdatedAt = %s")
        params.append(datetime.now())
        params.append(conector_id)
        
        query = f"UPDATE CRM_Integracion_Conectores SET {', '.join(updates)} WHERE ConectorID = %s"
        cursor.execute(query, tuple(params))
        
        conn.commit()
        return {"mensaje": "Conector actualizado"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"[Integration] Error actualizando conector: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.delete("/conectores/{conector_id}")
async def eliminar_conector(conector_id: int):
    """Elimina un conector (soft delete = desactivar)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE CRM_Integracion_Conectores 
            SET Activo = 0, UpdatedAt = %s 
            WHERE ConectorID = %s
        """, (datetime.now(), conector_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conector no encontrado")
        
        conn.commit()
        return {"mensaje": "Conector desactivado"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# TEST CONNECTION
# ============================================================

@router.post("/test-connection")
async def test_connection(data: TestConnectionRequest):
    """Prueba conexión con un CRM externo"""
    engine = SyncEngine(DB_CONFIG)
    
    result = engine.test_connector(
        tipo=data.tipo.upper(),
        config={
            'base_url': data.base_url,
            'username': data.username,
            'access_key': data.access_key
        }
    )
    
    return result


@router.post("/conectores/{conector_id}/test")
async def test_conector_guardado(conector_id: int):
    """Prueba conexión de un conector guardado"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
            SELECT TipoConector, ConfiguracionJSON 
            FROM CRM_Integracion_Conectores 
            WHERE ConectorID = %s AND Activo = 1
        """, (conector_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Conector no encontrado o inactivo")
        
        config = json.loads(row['ConfiguracionJSON']) if row['ConfiguracionJSON'] else {}
        
        engine = SyncEngine(DB_CONFIG)
        result = engine.test_connector(row['TipoConector'], config)
        
        # Actualizar estado de conexión
        cursor.execute("""
            UPDATE CRM_Integracion_Conectores SET
                EstadoConexion = %s,
                MensajeError = %s,
                UpdatedAt = %s
            WHERE ConectorID = %s
        """, (
            'CONECTADO' if result['success'] else 'ERROR',
            result.get('error'),
            datetime.now(),
            conector_id
        ))
        conn.commit()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Integration] Error testing conector: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# SINCRONIZACIÓN
# ============================================================

@router.post("/conectores/{conector_id}/sync")
async def ejecutar_sync(conector_id: int, data: SyncRequest):
    """
    Ejecuta sincronización para un conector.
    Extrae datos del CRM externo y los guarda en staging.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Obtener conector
        cursor.execute("""
            SELECT ConectorID, EmpresaID, TipoConector, ConfiguracionJSON, Activo
            FROM CRM_Integracion_Conectores 
            WHERE ConectorID = %s
        """, (conector_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Conector no encontrado")
        
        if not row['Activo']:
            raise HTTPException(status_code=400, detail="Conector inactivo")
        
        config = json.loads(row['ConfiguracionJSON']) if row['ConfiguracionJSON'] else {}
        
        # Crear job de sync
        job = SyncJob(
            conector_id=conector_id,
            empresa_id=str(row['EmpresaID']),
            tipo_conector=row['TipoConector'],
            entidades=data.entidades,
            desde_fecha=data.desde_fecha
        )
        
        # Ejecutar sync
        engine = SyncEngine(DB_CONFIG)
        result = engine.run_sync(job, config)
        
        # Actualizar última sincronización
        cursor.execute("""
            UPDATE CRM_Integracion_Conectores SET
                UltimaSincronizacion = %s,
                EstadoConexion = %s,
                MensajeError = %s,
                UpdatedAt = %s
            WHERE ConectorID = %s
        """, (
            datetime.now(),
            'CONECTADO' if result.success else 'ERROR',
            result.errores[0] if result.errores else None,
            datetime.now(),
            conector_id
        ))
        
        # Registrar en log
        cursor.execute("""
            INSERT INTO CRM_Integracion_SyncLog (
                ConectorID, TipoEntidad, Operacion, FechaInicio, FechaFin,
                Duracion, RegistrosProcesados, RegistrosCreados, RegistrosActualizados,
                RegistrosError, Estado, DetallesJSON
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            conector_id,
            ','.join(data.entidades),
            'SYNC_ENTRANTE',
            datetime.now(),
            datetime.now(),
            result.duracion_segundos,
            result.registros_procesados,
            result.registros_creados,
            result.registros_actualizados,
            result.registros_error,
            'COMPLETADO' if result.success else 'ERROR',
            json.dumps({"entidades": data.entidades, "errores": result.errores[:5]})
        ))
        
        conn.commit()
        
        return {
            "success": result.success,
            "procesados": result.registros_procesados,
            "creados": result.registros_creados,
            "actualizados": result.registros_actualizados,
            "errores": result.registros_error,
            "duracion_segundos": result.duracion_segundos,
            "mensajes_error": result.errores[:10]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"[Integration] Error en sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# STAGING
# ============================================================

@router.get("/conectores/{conector_id}/staging/stats")
async def obtener_staging_stats(conector_id: int):
    """Obtiene estadísticas de staging para un conector"""
    staging = StagingService(DB_CONFIG)
    stats = staging.get_staging_stats(conector_id)
    
    return {
        "conector_id": conector_id,
        "stats": stats
    }


@router.get("/conectores/{conector_id}/staging/leads")
async def listar_staging_leads(
    conector_id: int,
    estado: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """Lista leads en staging"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        query = """
            SELECT TOP %s * 
            FROM CRM_Staging_Leads 
            WHERE ConectorID = %s
        """
        params = [limit, conector_id]
        
        if estado:
            query += " AND EstadoSync = %s"
            params.append(estado)
        
        query += " ORDER BY CreatedAt DESC"
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        # Convertir datos
        leads = []
        for row in rows:
            lead = dict(row)
            if lead.get('LocalLeadID'):
                lead['LocalLeadID'] = str(lead['LocalLeadID'])
            if lead.get('DatosExternosJSON'):
                try:
                    lead['DatosExternosJSON'] = json.loads(lead['DatosExternosJSON'])
                except:
                    pass
            leads.append(lead)
        
        return {"leads": leads, "total": len(leads)}
        
    except Exception as e:
        logger.error(f"[Integration] Error listando staging leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/conectores/{conector_id}/staging/oportunidades")
async def listar_staging_oportunidades(
    conector_id: int,
    estado: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """Lista oportunidades en staging"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        query = """
            SELECT TOP %s * 
            FROM CRM_Staging_Oportunidades 
            WHERE ConectorID = %s
        """
        params = [limit, conector_id]
        
        if estado:
            query += " AND EstadoSync = %s"
            params.append(estado)
        
        query += " ORDER BY CreatedAt DESC"
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        opps = []
        for row in rows:
            opp = dict(row)
            if opp.get('LocalOportunidadID'):
                opp['LocalOportunidadID'] = str(opp['LocalOportunidadID'])
            if opp.get('DatosExternosJSON'):
                try:
                    opp['DatosExternosJSON'] = json.loads(opp['DatosExternosJSON'])
                except:
                    pass
            opps.append(opp)
        
        return {"oportunidades": opps, "total": len(opps)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/conectores/{conector_id}/staging/cuentas")
async def listar_staging_cuentas(
    conector_id: int,
    estado: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """Lista cuentas en staging"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        query = """
            SELECT TOP %s * 
            FROM CRM_Staging_Cuentas 
            WHERE ConectorID = %s
        """
        params = [limit, conector_id]
        
        if estado:
            query += " AND EstadoSync = %s"
            params.append(estado)
        
        query += " ORDER BY CreatedAt DESC"
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        cuentas = []
        for row in rows:
            cuenta = dict(row)
            if cuenta.get('LocalCuentaID'):
                cuenta['LocalCuentaID'] = str(cuenta['LocalCuentaID'])
            if cuenta.get('DatosExternosJSON'):
                try:
                    cuenta['DatosExternosJSON'] = json.loads(cuenta['DatosExternosJSON'])
                except:
                    pass
            cuentas.append(cuenta)
        
        return {"cuentas": cuentas, "total": len(cuentas)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# SYNC LOG
# ============================================================

@router.get("/conectores/{conector_id}/sync-log")
async def obtener_sync_log(
    conector_id: int,
    limit: int = Query(default=20, le=100)
):
    """Obtiene historial de sincronizaciones"""
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
            SELECT TOP %s * 
            FROM CRM_Integracion_SyncLog 
            WHERE ConectorID = %s
            ORDER BY FechaInicio DESC
        """, (limit, conector_id))
        
        rows = cursor.fetchall()
        logs = []
        for row in rows:
            log = dict(row)
            if log.get('Detalles'):
                try:
                    log['Detalles'] = json.loads(log['Detalles'])
                except:
                    pass
            logs.append(log)
        
        return {"logs": logs, "total": len(logs)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# PROCESS STAGING -> PRODUCTION
# ============================================================

@router.post("/conectores/{conector_id}/process-staging")
async def procesar_staging(conector_id: int, data: ProcessStagingRequest):
    """
    Procesa registros de staging y los mueve a tablas de producción.
    Incluye lógica de deduplicación y matching.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Obtener empresa del conector
        cursor.execute("""
            SELECT EmpresaID FROM CRM_Integracion_Conectores 
            WHERE ConectorID = %s AND Activo = 1
        """, (conector_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Conector no encontrado o inactivo")
        
        empresa_id = str(row['EmpresaID'])
        
        # Mapear acción de duplicados
        accion_map = {
            'CREAR_NUEVO': MatchAction.CREAR_NUEVO,
            'ACTUALIZAR_EXISTENTE': MatchAction.ACTUALIZAR_EXISTENTE,
            'MARCAR_CONFLICTO': MatchAction.MARCAR_CONFLICTO,
            'OMITIR': MatchAction.OMITIR
        }
        accion = accion_map.get(data.accion_duplicados, MatchAction.MARCAR_CONFLICTO)
        
        # Procesar staging
        processor = StagingProcessor(DB_CONFIG)
        result = processor.process_staging(
            conector_id=conector_id,
            empresa_id=empresa_id,
            entidades=data.entidades,
            accion_duplicados=accion,
            limit=data.limit
        )
        
        return {
            "success": result.success,
            "total_procesados": result.total_procesados,
            "creados": result.creados,
            "actualizados": result.actualizados,
            "conflictos": result.conflictos,
            "errores": result.errores,
            "omitidos": result.omitidos,
            "mensajes": result.mensajes[:10]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Integration] Error procesando staging: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# CONFLICTOS
# ============================================================

@router.get("/conectores/{conector_id}/conflictos")
async def listar_conflictos(
    conector_id: int,
    entidad: str = Query(default='leads', description="leads, cuentas, oportunidades")
):
    """Lista registros en conflicto que requieren resolución manual"""
    processor = StagingProcessor(DB_CONFIG)
    conflicts = processor.get_conflicts(conector_id, entidad)
    
    # Formatear para respuesta
    formatted = []
    for c in conflicts:
        item = {
            "staging_id": c['StagingID'],
            "external_id": c['ExternalID'],
            "estado": c['EstadoSync'],
            "created_at": str(c['CreatedAt']) if c.get('CreatedAt') else None,
        }
        
        # Datos según entidad
        if entidad == 'leads':
            item.update({
                "nombre": f"{c.get('NombreContacto', '')} {c.get('ApellidoPaterno', '')}".strip(),
                "email": c.get('Email'),
                "telefono": c.get('Telefono'),
                "empresa": c.get('NombreEmpresa')
            })
        elif entidad == 'cuentas':
            item.update({
                "razon_social": c.get('RazonSocial'),
                "rfc": c.get('RFC'),
                "email": c.get('EmailPrincipal')
            })
        elif entidad == 'oportunidades':
            item.update({
                "nombre": c.get('NombreOportunidad'),
                "monto": c.get('MontoEstimado')
            })
        
        # Detalles del conflicto
        if c.get('ConflictDetails'):
            item['conflicto'] = c['ConflictDetails']
        
        formatted.append(item)
    
    return {"conflictos": formatted, "total": len(formatted), "entidad": entidad}


@router.post("/conectores/{conector_id}/conflictos/{staging_id}/resolver")
async def resolver_conflicto(
    conector_id: int,
    staging_id: int,
    data: ResolveConflictRequest,
    entidad: str = Query(default='leads')
):
    """
    Resuelve un conflicto específico.
    
    Acciones disponibles:
    - CREAR_NUEVO: Crea un nuevo registro ignorando el duplicado
    - ACTUALIZAR_EXISTENTE: Actualiza el registro existente con los datos del staging
    - OMITIR: Descarta el registro de staging
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Obtener empresa del conector
        cursor.execute("""
            SELECT EmpresaID FROM CRM_Integracion_Conectores 
            WHERE ConectorID = %s
        """, (conector_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Conector no encontrado")
        
        empresa_id = str(row['EmpresaID'])
        
        # Mapear acción
        accion_map = {
            'CREAR_NUEVO': MatchAction.CREAR_NUEVO,
            'ACTUALIZAR_EXISTENTE': MatchAction.ACTUALIZAR_EXISTENTE,
            'OMITIR': MatchAction.OMITIR
        }
        accion = accion_map.get(data.accion)
        
        if not accion:
            raise HTTPException(status_code=400, detail="Acción no válida")
        
        processor = StagingProcessor(DB_CONFIG)
        result = processor.resolve_conflict(
            staging_id=staging_id,
            entidad=entidad,
            accion=accion,
            empresa_id=empresa_id
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Error desconocido'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Integration] Error resolviendo conflicto: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/conectores/{conector_id}/conflictos/resolver-todos")
async def resolver_todos_conflictos(
    conector_id: int,
    data: ResolveConflictRequest,
    entidad: str = Query(default='leads')
):
    """Resuelve todos los conflictos de una entidad con la misma acción"""
    processor = StagingProcessor(DB_CONFIG)
    conflicts = processor.get_conflicts(conector_id, entidad)
    
    if not conflicts:
        return {"mensaje": "No hay conflictos pendientes", "resueltos": 0}
    
    conn = get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
            SELECT EmpresaID FROM CRM_Integracion_Conectores WHERE ConectorID = %s
        """, (conector_id,))
        row = cursor.fetchone()
        empresa_id = str(row['EmpresaID']) if row else None
    finally:
        conn.close()
    
    if not empresa_id:
        raise HTTPException(status_code=404, detail="Conector no encontrado")
    
    accion_map = {
        'CREAR_NUEVO': MatchAction.CREAR_NUEVO,
        'ACTUALIZAR_EXISTENTE': MatchAction.ACTUALIZAR_EXISTENTE,
        'OMITIR': MatchAction.OMITIR
    }
    accion = accion_map.get(data.accion)
    
    resueltos = 0
    errores = 0
    
    for conflict in conflicts:
        result = processor.resolve_conflict(
            staging_id=conflict['StagingID'],
            entidad=entidad,
            accion=accion,
            empresa_id=empresa_id
        )
        if result['success']:
            resueltos += 1
        else:
            errores += 1
    
    return {
        "mensaje": f"Conflictos procesados",
        "resueltos": resueltos,
        "errores": errores,
        "total": len(conflicts)
    }

