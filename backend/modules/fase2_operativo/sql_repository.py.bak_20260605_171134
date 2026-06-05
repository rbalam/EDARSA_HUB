from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - SQL Repository para Workflows y Tareas
====================================================
Reemplazo completo de MongoDB para el módulo fase2_operativo.

Tablas:
- Workflow_Inventarios
- Tareas_Inventario
- Workflow_DetalleDiferencias
- Inventarios_SinAsignar
- Alertas_Sistema
- Configuracion_Operativa
- Config_Asignaciones

Autor: Agente E1
Fecha: Mayo 2026
"""

import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Configuración EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'HRLectura',
    'password': 'National09$'
}


def _get_connection():
    """Obtiene una conexión a EDARSAHUB."""
    import pymssql
    return pymssql.connect(
        server=EDARSAHUB_CONFIG['host'],
        port=EDARSAHUB_CONFIG['port'],
        database=EDARSAHUB_CONFIG['database'],
        user=EDARSAHUB_CONFIG['username'],
        password=EDARSAHUB_CONFIG['password'],
        timeout=30,
        login_timeout=15
    )


def _execute_sql(query: str, params: tuple = None, fetch: bool = True) -> List[Dict]:
    """Ejecuta una query SQL de forma síncrona."""
    try:
        conn = _get_connection()
        cursor = conn.cursor(as_dict=True)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            try:
                results = list(cursor.fetchall())
            except Exception:
                results = []
        else:
            conn.commit()
            results = []
        
        cursor.close()
        conn.close()
        return results
        
    except Exception as e:
        logger.error(f"[FASE2_SQL] Error ejecutando query: {e}")
        return []


async def _execute_sql_async(query: str, params: tuple = None, fetch: bool = True) -> List[Dict]:
    """Ejecuta una query SQL de forma asíncrona."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(
            executor, 
            lambda: _execute_sql(query, params, fetch)
        )


# =============================================================================
# WORKFLOWS
# =============================================================================

async def workflow_existe(
    server_id: str,
    sucursal_id: str,
    almacen_id: str,
    folio_final_key: str
) -> Optional[str]:
    """
    Verifica si ya existe un workflow activo para esta combinación.
    
    Returns:
        WorkflowID si existe, None si no
    """
    query = """
        SELECT WorkflowID
        FROM Workflow_Inventarios
        WHERE ServerID = %s
          AND SucursalID = %s
          AND AlmacenID = %s
          AND FolioFinalKey = %s
          AND Estado NOT IN ('completado', 'cancelado')
    """
    params = (server_id, sucursal_id or '', almacen_id, folio_final_key)
    
    rows = await _execute_sql_async(query, params)
    return rows[0]['WorkflowID'] if rows else None


async def crear_workflow(
    workflow_id: str,
    server_id: str,
    server_name: str,
    sucursal_id: str,
    sucursal_nombre: str,
    almacen_id: str,
    almacen_nombre: str,
    folios_iniciales: List[str],
    folios_finales: List[str],
    folio_final_key: str,
    fecha_ini: str,
    fecha_fin: str,
    total_productos: int,
    valor_total_diferencias: float,
    usuario_creador_id: str,
    folio_inventario: str = None
) -> bool:
    """Crea un nuevo workflow de inventario."""
    query = """
        INSERT INTO Workflow_Inventarios (
            WorkflowID, ProcesadoID, FolioInventario,
            ServerID, ServerName, SucursalID, SucursalNombre,
            AlmacenID, AlmacenNombre, FoliosInicialesJSON, FoliosFinalesJSON,
            FolioFinalKey, FechaAnalisisIni, FechaAnalisisFin,
            TotalProductosDiferencia, ValorTotalDiferencias, UsuarioCreadorID
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    params = (
        workflow_id, folio_final_key, folio_inventario,
        server_id, server_name, sucursal_id or '', sucursal_nombre or '',
        almacen_id, almacen_nombre,
        json.dumps(folios_iniciales), json.dumps(folios_finales),
        folio_final_key, fecha_ini, fecha_fin,
        total_productos, valor_total_diferencias, usuario_creador_id
    )
    
    try:
        await _execute_sql_async(query, params, fetch=False)
        logger.info(f"[FASE2_SQL] Workflow creado: {workflow_id}")
        return True
    except Exception as e:
        logger.error(f"[FASE2_SQL] Error creando workflow: {e}")
        return False


async def actualizar_workflow_estado(workflow_id: str, estado: str) -> bool:
    """Actualiza el estado de un workflow."""
    query = """
        UPDATE Workflow_Inventarios
        SET Estado = %s, EstadoWorkflow = %s, FechaUltimaActualizacion = GETUTCDATE()
        WHERE WorkflowID = %s
    """
    params = (estado, estado.upper(), workflow_id)
    
    try:
        await _execute_sql_async(query, params, fetch=False)
        return True
    except Exception as e:
        logger.error(f"[FASE2_SQL] Error actualizando workflow: {e}")
        return False


async def obtener_workflow(workflow_id: str) -> Optional[Dict]:
    """Obtiene un workflow por ID."""
    if not workflow_id:
        return None
    
    query = """
        SELECT 
            WorkflowID as ID, ProcesadoID as procesado_id, FolioInventario as folio_inventario,
            ServerID as ServerID, ServerName as server_name,
            SucursalID as SucursalID, SucursalNombre as sucursal_nombre,
            AlmacenID as AlmacenID, AlmacenNombre as almacen_nombre,
            FolioFinalKey as folio_final_key,
            Estado as Estado, EstadoWorkflow as estado_workflow,
            CicloActual as ciclo_actual,
            TotalProductosDiferencia as total_productos_diferencia,
            ValorTotalDiferencias as valor_total_diferencias,
            FechaCreacion as fecha_creacion, FechaUltimaActualizacion as fecha_ultima_actualizacion,
            UsuarioCreadorID as usuario_creador_id
        FROM Workflow_Inventarios
        WHERE WorkflowID = %s
    """
    rows = await _execute_sql_async(query, (workflow_id,))
    return rows[0] if rows else None


# =============================================================================
# TAREAS
# =============================================================================

async def crear_tarea(
    tarea_id: str,
    workflow_id: str,
    tipo_tarea: str,
    titulo: str,
    descripcion: str,
    prioridad: str,
    usuario_asignado_id: str,
    usuario_asignado_nombre: str,
    fecha_limite: str
) -> bool:
    """Crea una nueva tarea de inventario."""
    query = """
        INSERT INTO Tareas_Inventario (
            TareaID, WorkflowID, TipoTarea, Titulo, Descripcion,
            Prioridad, UsuarioAsignadoID, UsuarioAsignadoNombre,
            FechaAsignacion, FechaLimite
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, GETUTCDATE(), %s
        )
    """
    params = (
        tarea_id, workflow_id, tipo_tarea, titulo, descripcion,
        prioridad, usuario_asignado_id, usuario_asignado_nombre, fecha_limite
    )
    
    try:
        await _execute_sql_async(query, params, fetch=False)
        logger.info(f"[FASE2_SQL] Tarea creada: {tarea_id}")
        return True
    except Exception as e:
        logger.error(f"[FASE2_SQL] Error creando tarea: {e}")
        return False


async def obtener_tareas_activas() -> List[Dict]:
    """Obtiene todas las tareas activas."""
    query = """
        SELECT 
            TareaID as ID, WorkflowID as workflow_id,
            TipoTarea as tipo_tarea, Titulo as Titulo, Descripcion as Descripcion,
            EstadoTarea as estado_tarea, Prioridad as Prioridad,
            UsuarioAsignadoID as usuario_asignado_id,
            UsuarioAsignadoNombre as usuario_asignado_nombre,
            FechaCreacion as fecha_creacion, FechaAsignacion as fecha_asignacion,
            FechaLimite as fecha_limite, FechaActualizacion as fecha_actualizacion,
            FechaPrimeraAccion as fecha_primera_accion,
            FechaCompletada as fecha_completada,
            Ciclo as Ciclo, Vencida as Vencida, EstadoSLA as estado_sla,
            NotificacionWarningEnviada as notificacion_warning_enviada,
            NotificacionVencidoEnviada as notificacion_vencido_enviada,
            NotificacionEscaladoEnviada as notificacion_escalado_enviada
        FROM Tareas_Inventario
        WHERE EstadoTarea IN ('PENDIENTE', 'EN_PROGRESO')
    """
    return await _execute_sql_async(query)


async def actualizar_tarea_estado_sla(
    tarea_id: str,
    estado_sla: str,
    vencida: bool = False
) -> bool:
    """Actualiza el estado SLA de una tarea."""
    query = """
        UPDATE Tareas_Inventario
        SET EstadoSLA = %s, Vencida = %s, FechaActualizacionSLA = GETUTCDATE()
        WHERE TareaID = %s
    """
    params = (estado_sla, 1 if vencida else 0, tarea_id)
    
    try:
        await _execute_sql_async(query, params, fetch=False)
        return True
    except Exception as e:
        logger.error(f"[FASE2_SQL] Error actualizando SLA tarea: {e}")
        return False


async def marcar_notificacion_enviada(
    tarea_id: str,
    tipo_notificacion: str  # 'warning', 'vencido', 'escalado'
) -> bool:
    """Marca que una notificación fue enviada."""
    campo = {
        'warning': 'NotificacionWarningEnviada',
        'vencido': 'NotificacionVencidoEnviada',
        'escalado': 'NotificacionEscaladoEnviada'
    }.get(tipo_notificacion)
    
    if not campo:
        return False
    
    query = f"""
        UPDATE Tareas_Inventario
        SET {campo} = 1
        WHERE TareaID = %s
    """
    
    try:
        await _execute_sql_async(query, (tarea_id,), fetch=False)
        return True
    except Exception as e:
        logger.error(f"[FASE2_SQL] Error marcando notificación: {e}")
        return False


async def obtener_tareas_completadas() -> List[Dict]:
    """Obtiene todas las tareas completadas."""
    query = """
        SELECT 
            TareaID as ID, WorkflowID as workflow_id,
            TipoTarea as tipo_tarea, EstadoTarea as estado_tarea,
            FechaCreacion as fecha_creacion, FechaLimite as fecha_limite,
            FechaPrimeraAccion as fecha_primera_accion,
            FechaCompletada as fecha_completada, EstadoSLA as estado_sla
        FROM Tareas_Inventario
        WHERE EstadoTarea = 'COMPLETADA'
    """
    return await _execute_sql_async(query)


# =============================================================================
# DETALLE DIFERENCIAS
# =============================================================================

async def crear_detalles_diferencias(workflow_id: str, productos: List[Dict]) -> int:
    """Crea los detalles de diferencias para un workflow."""
    count = 0
    
    for prod in productos:
        import uuid
        detalle_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO Workflow_DetalleDiferencias (
                DetalleID, WorkflowID, CodigoProducto, NombreProducto,
                Categoria, Familia, SubFamilia, Unidad, CostoUnitario,
                InvInicialCantidad, InvFinalCantidad, InvTeoricoCantidad,
                DiferenciaCantidad, DiferenciaCosto, DiferenciaPorcentaje,
                Movimientos, Ventas, RequiereJustificacionCompleta
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        params = (
            detalle_id, workflow_id,
            prod.get("Codigo", ""),
            prod.get("Producto", ""),
            prod.get("Categoria", ""),
            prod.get("Familia", ""),
            prod.get("SubFamilia", ""),
            prod.get("Unidad", ""),
            float(prod.get("Costo_Unitario", 0) or 0),
            float(prod.get("Inv_Inicial_Cantidad", 0) or 0),
            float(prod.get("Inv_Final_Cantidad", 0) or 0),
            float(prod.get("Inv_Teorico_Cantidad", 0) or 0),
            float(prod.get("Diferencia_Cantidad", 0) or 0),
            float(prod.get("Diferencia_Costo", 0) or 0),
            float(prod.get("Diferencia_Porcentaje", 0) or 0),
            float(prod.get("Movimientos", 0) or 0),
            float(prod.get("Ventas", 0) or 0),
            1 if abs(float(prod.get("Diferencia_Costo", 0) or 0)) > 500 else 0
        )
        
        try:
            await _execute_sql_async(query, params, fetch=False)
            count += 1
        except Exception as e:
            logger.error(f"[FASE2_SQL] Error creando detalle: {e}")
    
    logger.info(f"[FASE2_SQL] Detalles creados: {count} para workflow {workflow_id}")
    return count


# =============================================================================
# INVENTARIOS SIN ASIGNAR
# =============================================================================

async def registrar_inventario_sin_asignar(
    server_id: str,
    server_name: str,
    sucursal_id: str,
    sucursal_nombre: str,
    almacen_id: str,
    almacen_nombre: str,
    folio_inventario: str,
    total_diferencias: int,
    valor_diferencias: float
) -> bool:
    """Registra un inventario que no pudo ser procesado por falta de configuración."""
    import uuid
    registro_id = str(uuid.uuid4())
    
    query = """
        INSERT INTO Inventarios_SinAsignar (
            RegistroID, ServerID, ServerName, SucursalID, SucursalNombre,
            AlmacenID, AlmacenNombre, FolioInventario,
            TotalDiferencias, ValorDiferencias
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    params = (
        registro_id, server_id, server_name, sucursal_id or '', sucursal_nombre or '',
        almacen_id, almacen_nombre, folio_inventario or '',
        total_diferencias, valor_diferencias
    )
    
    try:
        await _execute_sql_async(query, params, fetch=False)
        logger.info(f"[FASE2_SQL] Inventario sin asignar registrado: {server_name}/{almacen_nombre}")
        return True
    except Exception as e:
        logger.error(f"[FASE2_SQL] Error registrando inv sin asignar: {e}")
        return False


# =============================================================================
# ALERTAS SISTEMA
# =============================================================================

async def crear_alerta_sistema(
    tipo: str,
    severidad: str,
    titulo: str,
    mensaje: str,
    modulo: str,
    datos: Dict = None,
    accion_sugerida: str = None
) -> bool:
    """Crea una alerta en el sistema."""
    import uuid
    alerta_id = str(uuid.uuid4())
    
    query = """
        INSERT INTO Alertas_Sistema (
            AlertaID, Tipo, Severidad, Titulo, Mensaje, Modulo,
            DatosJSON, AccionSugerida
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    params = (
        alerta_id, tipo, severidad, titulo, mensaje, modulo,
        json.dumps(datos) if datos else None, accion_sugerida
    )
    
    try:
        await _execute_sql_async(query, params, fetch=False)
        logger.info(f"[FASE2_SQL] Alerta creada: {tipo}")
        return True
    except Exception as e:
        logger.error(f"[FASE2_SQL] Error creando alerta: {e}")
        return False


# =============================================================================
# CONFIGURACIÓN OPERATIVA
# =============================================================================

async def obtener_configuracion_sla() -> Dict[str, Any]:
    """Obtiene la configuración SLA desde SQL."""
    query = """
        SELECT Clave, Valor
        FROM Configuracion_Operativa
        WHERE Clave LIKE 'SLA_%' OR Clave = 'DIAS_LIMITE_TAREA_DEFAULT'
    """
    
    rows = await _execute_sql_async(query)
    
    config = {}
    for row in rows:
        clave = row.get('Clave')
        valor = row.get('Valor')
        try:
            config[clave] = int(valor) if valor else 0
        except (ValueError, TypeError):
            config[clave] = valor
    
    return config


async def actualizar_configuracion_sla(clave: str, valor: Any) -> bool:
    """Actualiza una configuración SLA."""
    query = """
        UPDATE Configuracion_Operativa
        SET Valor = %s, FechaActualizacion = GETUTCDATE()
        WHERE Clave = %s
    """
    
    try:
        await _execute_sql_async(query, (str(valor), clave), fetch=False)
        return True
    except Exception as e:
        logger.error(f"[FASE2_SQL] Error actualizando config: {e}")
        return False


# =============================================================================
# CONFIG ASIGNACIONES
# =============================================================================

async def obtener_config_asignacion(server_id: str, almacen_id: str) -> Optional[Dict]:
    """
    Obtiene la configuración de asignación para un servidor/almacén.
    Busca primero específico, luego general.
    """
    query = """
        SELECT TOP 1
            ConfigID as ID, ServerID as ServerID, AlmacenID as AlmacenID,
            UsuarioResponsableID as usuario_responsable_id, Prioridad as Prioridad
        FROM Config_Asignaciones
        WHERE ServerID = %s
          AND (AlmacenID = %s OR AlmacenID = '')
          AND Activa = 1
        ORDER BY 
            CASE WHEN AlmacenID = %s THEN 0 ELSE 1 END,
            Prioridad DESC
    """
    params = (server_id, almacen_id, almacen_id)
    
    rows = await _execute_sql_async(query, params)
    return rows[0] if rows else None


async def obtener_usuario_por_id(usuario_id: str) -> Optional[Dict]:
    """Obtiene un usuario desde la tabla Usuarios."""
    query = """
        SELECT 
            CAST(UsuarioID AS VARCHAR(50)) as id,
            NombreCompleto as name,
            Email as email
        FROM Usuarios
        WHERE UsuarioID = %s OR MongoLegacyID = %s
          AND Activo = 1
    """
    rows = await _execute_sql_async(query, (usuario_id, usuario_id))
    return rows[0] if rows else None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Workflows
    'workflow_existe',
    'crear_workflow',
    'actualizar_workflow_estado',
    'obtener_workflow',
    # Tareas
    'crear_tarea',
    'obtener_tareas_activas',
    'actualizar_tarea_estado_sla',
    'marcar_notificacion_enviada',
    'obtener_tareas_completadas',
    # Detalles
    'crear_detalles_diferencias',
    # Sin asignar
    'registrar_inventario_sin_asignar',
    # Alertas
    'crear_alerta_sistema',
    # Config
    'obtener_configuracion_sla',
    'actualizar_configuracion_sla',
    # Asignaciones
    'obtener_config_asignacion',
    'obtener_usuario_por_id',
]
