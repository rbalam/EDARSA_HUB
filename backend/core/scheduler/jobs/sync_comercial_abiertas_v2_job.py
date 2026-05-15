"""
EDARSA HUB - Job de Sincronización de Ventas del Día Comercial V2
==================================================================

ACTUALIZACIÓN ARQUITECTÓNICA (2026-05-14):
- ORIGEN y QRO usan APIs locales (NO SQL Server MPRO central)
- NO escribir $0 falso si falla la conexión al origen
- Conservar último dato válido si falla la sincronización
- UPSERT idempotente para datos mutables durante el día
- source_status técnico para diagnóstico

REGLAS:
1. Ventas del Día es dato mutable durante el día (cancelaciones, reaperturas, etc.)
2. Cada sync recalcula el estado actual, no acumula
3. Si falla conexión: NO escribir $0, conservar dato anterior
4. SoftRestaurant: tabla tempcheques (abiertas) + cheques (cerradas)
5. MPRO ORIGEN/QRO: API local (NO SQL Server central)
6. El tablero lee SOLO desde EDARSAHUB SQL

FRECUENCIA: Cada 5 minutos (configurable)
TABLA DESTINO: Comercial_Ventas_Dia_Abiertas_v2

Autor: E1 Agent
Fecha: 2026-05-14
"""

import os
import uuid
import logging
import requests
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Configuración
JOB_NAME = "sync_comercial_abiertas_v2"
SYNC_INTERVAL_SECONDS = int(os.environ.get("SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_INTERVAL_SECONDS", "300"))


# =============================================================================
# CONFIGURACIÓN DE APIs LOCALES MPRO
# =============================================================================

# Mapeo de códigos de unidad a sus configuraciones de API local
MPRO_API_LOCAL_CONFIG = {
    "ORIGEN": {
        "server_config_name": "ORIGEN LOCAL",
        "sucursal_id": "0023"
    },
    "130QRO": {
        "server_config_name": "130° QRO LOCAL", 
        "sucursal_id": "0021"
    }
}


def _get_api_local_config(unidad_codigo: str) -> Optional[Dict]:
    """
    Obtiene la configuración de API local para una unidad MPRO desde EDARSAHUB.
    
    Returns:
        Dict con api_url, api_key, sucursal_id o None si no existe
    """
    from core.db import execute_sql_query
    from core.secret_manager import decrypt_secret
    
    config = MPRO_API_LOCAL_CONFIG.get(unidad_codigo)
    if not config:
        logger.warning(f"[SYNC_ABIERTAS_V2] Unidad {unidad_codigo} no tiene config en MPRO_API_LOCAL_CONFIG")
        return None
    
    try:
        rows = execute_sql_query(
            '54.39.104.176', 1433, 'EDARSAHUB', 'HRLectura', 'National09$',
            f'''
            SELECT id, nombre, api_url, api_key_encrypted
            FROM Servidores_Conexiones
            WHERE nombre = '{config["server_config_name"]}' 
              AND tipo_conexion = 'API_LOCAL'
              AND activo = 1
            '''
        )
        
        if not rows:
            logger.warning(f"[SYNC_ABIERTAS_V2] No se encontró servidor '{config['server_config_name']}' en EDARSAHUB")
            return None
        
        row = rows[0]
        api_key = ""
        if row.get('api_key_encrypted'):
            try:
                api_key = decrypt_secret(row['api_key_encrypted'])
            except Exception as e:
                logger.error(f"[SYNC_ABIERTAS_V2] Error descifrando API key: {e}")
                return None
        
        # Convertir server_id a string si es UUID
        server_id = row['id']
        if hasattr(server_id, 'hex') or str(type(server_id)) == "<class 'uuid.UUID'>":
            server_id = str(server_id)
        
        return {
            "server_id": server_id,
            "server_name": row['nombre'],
            "api_url": row['api_url'],
            "api_key": api_key,
            "sucursal_id": config["sucursal_id"]
        }
        
    except Exception as e:
        logger.error(f"[SYNC_ABIERTAS_V2] Error obteniendo config API local: {e}")
        return None


def _execute_query_via_api_local(api_config: Dict, query: str) -> Tuple[List[Dict], str]:
    """
    Ejecuta una query SQL via API local MPRO.
    
    Args:
        api_config: Dict con api_url, api_key, etc.
        query: Query SQL a ejecutar
        
    Returns:
        (rows, connection_status): Lista de resultados y estado de conexión
    """
    try:
        response = requests.get(
            api_config['api_url'],
            params={'sql': query},
            headers={'X-API-Key': api_config['api_key']},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            rows = data.get('data', [])
            return rows, "API_LOCAL_OK"
        elif response.status_code == 401:
            logger.error(f"[SYNC_ABIERTAS_V2] API Local no autorizado: {api_config['server_name']}")
            return [], "API_LOCAL_UNAUTHORIZED"
        else:
            logger.error(f"[SYNC_ABIERTAS_V2] API Local error {response.status_code}: {response.text[:200]}")
            return [], "API_LOCAL_ERROR"
            
    except requests.exceptions.Timeout:
        logger.error(f"[SYNC_ABIERTAS_V2] API Local timeout: {api_config['server_name']}")
        return [], "API_LOCAL_TIMEOUT"
    except requests.exceptions.ConnectionError:
        logger.error(f"[SYNC_ABIERTAS_V2] API Local sin conexión: {api_config['server_name']}")
        return [], "API_LOCAL_OFFLINE"
    except Exception as e:
        logger.error(f"[SYNC_ABIERTAS_V2] API Local error: {e}")
        return [], "API_LOCAL_FAILED"


# =============================================================================
# CONFIGURACIÓN DE UNIDADES
# =============================================================================

def _get_unidades_from_edarsahub() -> tuple:
    """
    Obtiene unidades desde EDARSAHUB.Unidades_Negocio.
    
    Returns:
        (unidades_softrestaurant, unidades_mpro) con códigos canónicos
    """
    try:
        from core.unidades_registry import get_unidades_by_sistema
        
        unidades_sr = []
        unidades_mpro = []
        
        # Obtener unidades SoftRestaurant
        for u in get_unidades_by_sistema('SoftRestaurant'):
            unidades_sr.append({
                "unidad_negocio_id": u.codigo,
                "nombre": u.nombre,
                "server_id": u.server_id,
                "sucursal_id": u.sucursal_id or "DEFAULT",
                "sistema": "SoftRestaurant"
            })
        
        # Obtener unidades MPRO - Usarán API local
        for u in get_unidades_by_sistema('MPRO'):
            unidades_mpro.append({
                "unidad_negocio_id": u.codigo,
                "nombre": u.nombre,
                "server_id": u.server_id,  # Se reemplazará con el de API local
                "sucursal_id": u.sucursal_id or "DEFAULT",
                "sistema": "MPRO"
            })
        
        logger.info(f"[SYNC_ABIERTAS_V2] Cargadas {len(unidades_sr)} SoftRestaurant, {len(unidades_mpro)} MPRO desde EDARSAHUB")
        
        return unidades_sr, unidades_mpro
        
    except Exception as e:
        logger.error(f"[SYNC_ABIERTAS_V2] Error cargando unidades: {e}")
        return [], []


# =============================================================================
# QUERIES PARA VENTAS DEL DÍA
# =============================================================================

# SoftRestaurant: Cuentas abiertas desde tempcheques
QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS = """
SELECT 
    CAST(GETDATE() AS DATE) as fecha,
    ISNULL(SUM(total), 0) as ventas_abiertas,
    COUNT(*) as tickets_abiertos,
    ISNULL(SUM(nopersonas), 0) as pax_abiertos,
    MAX(fecha) as ultima_venta
FROM tempcheques
WHERE cancelado = 0
  AND total > 0
"""

# SoftRestaurant: Ventas cerradas del día
QUERY_SOFTRESTAURANT_CERRADAS_HOY = """
SELECT 
    SUM(ISNULL(total, 0)) as ventas_cerradas_dia,
    COUNT(DISTINCT folio) as tickets_cerrados_dia,
    SUM(ISNULL(nopersonas, 1)) as pax_cerrados_dia
FROM cheques
WHERE cancelado = 0
  AND cierre IS NOT NULL
  AND CAST(fecha AS DATE) = CAST(GETDATE() AS DATE)
"""

# =============================================================================
# QUERIES MPRO - ORIGEN (usa Venta_Encabezado estándar)
# =============================================================================

# MPRO ORIGEN: Ventas abiertas (Comanda = sin cerrar)
QUERY_MPRO_VENTAS_ABIERTAS_ORIGEN = """
SELECT 
    CAST(GETDATE() AS DATE) as fecha,
    SUM(ISNULL(ve.Vn_Precio_Neto_Importe, 0)) as ventas_abiertas,
    COUNT(DISTINCT ve.Vn_Folio) as tickets_abiertos,
    SUM(ISNULL(c.Co_Personas, 1)) as pax_abiertos
FROM Venta_Encabezado ve
LEFT JOIN Comanda c ON ve.Vn_Documento = c.Co_Folio AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
WHERE CAST(ve.Vn_Fecha AS DATE) = CAST(GETDATE() AS DATE)
  AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
  AND ve.Vn_Tabla = 'Comanda'
"""

# MPRO ORIGEN: Ventas cerradas del día
QUERY_MPRO_CERRADAS_HOY_ORIGEN = """
SELECT 
    SUM(ISNULL(ve.Vn_Precio_Neto_Importe, 0)) as ventas_cerradas_dia,
    COUNT(DISTINCT ve.Vn_Folio) as tickets_cerrados_dia,
    SUM(ISNULL(c.Co_Personas, 1)) as pax_cerrados_dia
FROM Venta_Encabezado ve
LEFT JOIN Comanda c ON ve.Vn_Documento = c.Co_Folio AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
WHERE CAST(ve.Vn_Fecha AS DATE) = CAST(GETDATE() AS DATE)
  AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
  AND ve.Vn_Tabla <> 'Comanda'
"""

# =============================================================================
# QUERIES MPRO - QRO (usa Comanda + Comanda_Detalle directamente)
# NOTA: QRO no tiene datos en Venta_Encabezado, solo en Comanda/Comanda_Detalle
# =============================================================================
# FIX 2026-05-15: Usar {fecha_operacion} (calculada en México) en lugar de GETDATE()
# GETDATE() del servidor remoto puede estar en UTC o zona horaria diferente,
# causando que la query no encuentre datos y guarde $0 falso.
# La fecha_operacion DEBE ser la misma que se guarda en EDARSAHUB.
# =============================================================================

# MPRO QRO: Ventas abiertas (Comanda + Comanda_Detalle, estado 'AC', sin baja)
# {fecha_operacion} = fecha operativa calculada por backend en zona México
QUERY_MPRO_VENTAS_ABIERTAS_QRO = """
SELECT 
    '{fecha_operacion}' as fecha,
    SUM(ISNULL(cd.Cd_Importe, 0)) as ventas_abiertas,
    COUNT(DISTINCT c.Co_Folio) as tickets_abiertos,
    SUM(DISTINCT ISNULL(c.Co_Personas, 1)) as pax_abiertos
FROM Comanda c
INNER JOIN Comanda_Detalle cd ON c.Co_Folio = cd.Co_Folio
WHERE CAST(c.Co_Fecha AS DATE) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND cd.Es_Cve_Estado = 'AC'
  AND cd.Fecha_Baja IS NULL
  AND c.Es_Cve_Estado = 'AC'
"""

# MPRO QRO: Ventas cerradas del día (Comanda con cierre)
# NOTA: En QRO, las ventas cerradas se identifican por Es_Cve_Estado diferente o Fecha_Baja
# {fecha_operacion} = fecha operativa calculada por backend en zona México
QUERY_MPRO_CERRADAS_HOY_QRO = """
SELECT 
    SUM(ISNULL(cd.Cd_Importe, 0)) as ventas_cerradas_dia,
    COUNT(DISTINCT c.Co_Folio) as tickets_cerrados_dia,
    SUM(DISTINCT ISNULL(c.Co_Personas, 1)) as pax_cerrados_dia
FROM Comanda c
INNER JOIN Comanda_Detalle cd ON c.Co_Folio = cd.Co_Folio
WHERE CAST(c.Co_Fecha AS DATE) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND c.Es_Cve_Estado <> 'AC'
  AND cd.Es_Cve_Estado = 'AC'
  AND cd.Fecha_Baja IS NULL
"""


# =============================================================================
# FUNCIÓN PRINCIPAL DEL JOB
# =============================================================================

async def execute_sync_comercial_abiertas_v2(db=None) -> Dict[str, Any]:
    """
    Ejecuta sincronización de ventas del día actual.
    
    REGLAS IMPLEMENTADAS:
    - NO escribir $0 si falla la conexión al origen
    - Conservar último dato válido si falla sync
    - ORIGEN y QRO usan API local (NO SQL Server MPRO)
    - UPSERT idempotente (dato mutable durante el día)
    """
    from modules.comercial_v2.sync_comercial_edarsahub import (
        get_server_connection_config,
        execute_query_on_server,
        ConnectionStatus
    )
    from modules.comercial_v2.schemas import (
        VentasDiaAbiertasV2,
        SyncLogV2,
        SyncRunType,
        SyncStatus,
        SistemaOrigen,
        FuenteOriginal
    )
    from modules.comercial_v2.repository_comercial_edarsahub import (
        upsert_ventas_dia_abiertas,
        insert_sync_log
    )
    
    logger.info("[SYNC_ABIERTAS_V2] === INICIO SINCRONIZACIÓN ===")
    
    start_time = datetime.now(timezone.utc)
    run_id = f"ABIERTA-{start_time.strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:4]}"
    
    # CORRECCIÓN: Usar zona horaria de México para fecha operativa
    # En México, la fecha operativa corresponde a la hora local, no UTC
    import pytz
    mexico_tz = pytz.timezone('America/Mexico_City')
    fecha_hoy = datetime.now(mexico_tz).date()
    
    results = {
        "job_name": JOB_NAME,
        "run_id": run_id,
        "fecha": fecha_hoy.isoformat(),
        "inicio_ejecucion": start_time.isoformat(),
        "unidades_procesadas": 0,
        "unidades_exitosas": 0,
        "unidades_fallidas": 0,
        "total_ventas_abiertas": 0.0,
        "total_estimado_dia": 0.0,
        "detalles_unidades": [],
        "errores": []
    }
    
    # Cargar unidades desde EDARSAHUB
    unidades_sr, unidades_mpro = _get_unidades_from_edarsahub()
    
    # =========================================================================
    # SINCRONIZAR SOFTRESTAURANT
    # =========================================================================
    
    for unidad in unidades_sr:
        results["unidades_procesadas"] += 1
        unidad_id = unidad["unidad_negocio_id"]
        nombre = unidad["nombre"]
        server_id = unidad["server_id"]
        
        try:
            logger.info(f"[SYNC_ABIERTAS_V2] Procesando {nombre} (SoftRestaurant)...")
            
            server_config = get_server_connection_config(server_id)
            if not server_config:
                raise Exception(f"No se encontró config para server_id {server_id}")
            
            # Query ventas abiertas
            rows_abiertas, conn_status = execute_query_on_server(
                server_config, 
                QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS
            )
            
            # REGLA: Si falla conexión, NO escribir $0
            if conn_status != ConnectionStatus.ONLINE:
                raise Exception(f"Conexión fallida: {conn_status}")
            
            # Si la query retornó vacío o error silencioso, verificar
            if not rows_abiertas or rows_abiertas[0] is None:
                raise Exception("Query retornó vacío - posible error de credenciales")
            
            # Query ventas cerradas
            rows_cerradas, _ = execute_query_on_server(
                server_config, 
                QUERY_SOFTRESTAURANT_CERRADAS_HOY
            )
            
            # Extraer valores
            abiertas_data = rows_abiertas[0] if rows_abiertas else {}
            cerradas_data = rows_cerradas[0] if rows_cerradas else {}
            
            ventas_abiertas = Decimal(str(abiertas_data.get('ventas_abiertas') or 0))
            tickets_abiertos = int(abiertas_data.get('tickets_abiertos') or 0)
            pax_abiertos = int(abiertas_data.get('pax_abiertos') or 0)
            
            ventas_cerradas_dia = Decimal(str(cerradas_data.get('ventas_cerradas_dia') or 0))
            tickets_cerrados_dia = int(cerradas_data.get('tickets_cerrados_dia') or 0)
            pax_cerrados_dia = int(cerradas_data.get('pax_cerrados_dia') or 0)
            
            total_estimado_dia = ventas_abiertas + ventas_cerradas_dia
            
            # Crear modelo y upsert
            ventas_model = VentasDiaAbiertasV2(
                unidad_negocio_id=unidad_id,
                unidad_negocio_nombre=nombre,
                server_id=server_id,
                sucursal_id=unidad["sucursal_id"],
                sucursal_nombre=nombre,
                sistema_origen=SistemaOrigen.SOFTRESTAURANT,
                snapshot_timestamp=datetime.now(timezone.utc),
                fecha_operacion=fecha_hoy,
                ventas_abiertas=ventas_abiertas,
                tickets_abiertos=tickets_abiertos,
                pax_abiertos=pax_abiertos,
                ventas_cerradas_dia=ventas_cerradas_dia,
                tickets_cerrados_dia=tickets_cerrados_dia,
                pax_cerrados_dia=pax_cerrados_dia,
                total_estimado_dia=total_estimado_dia,
                fuente_original=FuenteOriginal.TEMPCHEQUES,
                sync_run_id=run_id,
                source_status="SYNC_OK"
            )
            
            upsert_result = upsert_ventas_dia_abiertas(ventas_model)
            
            results["unidades_exitosas"] += 1
            results["total_ventas_abiertas"] += float(ventas_abiertas)
            results["total_estimado_dia"] += float(total_estimado_dia)
            results["detalles_unidades"].append({
                "unidad_negocio_id": unidad_id,
                "unidad": nombre,
                "sistema": "SoftRestaurant",
                "estatus": "OK",
                "source_status": "SYNC_OK",
                "ventas_abiertas": float(ventas_abiertas),
                "total_estimado_dia": float(total_estimado_dia)
            })
            
            logger.info(f"[SYNC_ABIERTAS_V2] {nombre}: total=${total_estimado_dia:,.2f}")
            
            # Log exitoso
            log = SyncLogV2(
                run_id=run_id,
                run_type=SyncRunType.VENTAS_DIA,
                unidad_negocio_id=unidad_id,
                server_id=server_id,
                fecha_inicio=fecha_hoy,
                fecha_fin=fecha_hoy,
                status=SyncStatus.SUCCESS,
                records_processed=1,
                records_inserted=1 if upsert_result.get('action') == 'INSERT' else 0,
                records_updated=1 if upsert_result.get('action') == 'UPDATE' else 0,
                source_connection_status=ConnectionStatus.ONLINE
            )
            insert_sync_log(log)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[SYNC_ABIERTAS_V2] Error en {nombre}: {error_msg}")
            results["unidades_fallidas"] += 1
            results["errores"].append(f"{nombre}: {error_msg}")
            
            # REGLA: Conservar último dato válido, NO escribir $0
            results["detalles_unidades"].append({
                "unidad_negocio_id": unidad_id,
                "unidad": nombre,
                "sistema": "SoftRestaurant",
                "estatus": "ERROR",
                "source_status": "SYNC_FAILED",
                "mensaje_error": error_msg[:200]
            })
            
            # Log de error
            log = SyncLogV2(
                run_id=run_id,
                run_type=SyncRunType.VENTAS_DIA,
                unidad_negocio_id=unidad_id,
                server_id=server_id,
                fecha_inicio=fecha_hoy,
                fecha_fin=fecha_hoy,
                status=SyncStatus.FAILED,
                error_message=error_msg[:500],
                source_connection_status=ConnectionStatus.OFFLINE
            )
            insert_sync_log(log)
    
    # =========================================================================
    # SINCRONIZAR MPRO VIA API LOCAL
    # =========================================================================
    
    for unidad in unidades_mpro:
        results["unidades_procesadas"] += 1
        unidad_id = unidad["unidad_negocio_id"]
        nombre = unidad["nombre"]
        
        try:
            logger.info(f"[SYNC_ABIERTAS_V2] Procesando {nombre} (MPRO API Local)...")
            
            # Obtener configuración de API local desde EDARSAHUB
            api_config = _get_api_local_config(unidad_id)
            if not api_config:
                raise Exception(f"No se encontró configuración API local para {unidad_id}")
            
            server_id = api_config['server_id']  # ID del servidor API_LOCAL
            sucursal_id = api_config['sucursal_id']
            
            logger.info(f"[SYNC_ABIERTAS_V2] Usando API: {api_config['api_url']} para sucursal {sucursal_id}")
            
            # =================================================================
            # SELECCIONAR QUERY SEGÚN UNIDAD
            # ORIGEN: Usa Venta_Encabezado (estructura estándar MPRO)
            # 130QRO: Usa Comanda + Comanda_Detalle (estructura alternativa)
            # =================================================================
            # FIX 2026-05-15: fecha_operacion_str para queries de QRO
            fecha_operacion_str = fecha_hoy.isoformat()  # YYYY-MM-DD en zona México
            
            if unidad_id == '130QRO':
                # QRO usa estructura diferente: Comanda + Comanda_Detalle
                # FIX: Usar fecha_operacion calculada en México, NO GETDATE() remoto
                query_template_abiertas = QUERY_MPRO_VENTAS_ABIERTAS_QRO
                query_template_cerradas = QUERY_MPRO_CERRADAS_HOY_QRO
                logger.info(f"[SYNC_ABIERTAS_V2] {nombre}: Usando query Comanda+Comanda_Detalle con fecha_operacion={fecha_operacion_str}")
            else:
                # ORIGEN y otras unidades MPRO usan Venta_Encabezado estándar
                query_template_abiertas = QUERY_MPRO_VENTAS_ABIERTAS_ORIGEN
                query_template_cerradas = QUERY_MPRO_CERRADAS_HOY_ORIGEN
                logger.info(f"[SYNC_ABIERTAS_V2] {nombre}: Usando query Venta_Encabezado estándar")
            
            # Query ventas abiertas via API local
            # FIX: Incluir fecha_operacion para QRO (para ORIGEN no afecta, usa GETDATE)
            query_abiertas = query_template_abiertas.format(
                sucursal_id=sucursal_id,
                fecha_operacion=fecha_operacion_str
            )
            rows_abiertas, conn_status = _execute_query_via_api_local(api_config, query_abiertas)
            
            # REGLA: Si falla API, NO escribir $0
            if conn_status != "API_LOCAL_OK":
                raise Exception(f"API Local falló: {conn_status}")
            
            # REGLA ANTI-$0 FALSO: Primero obtener AMBAS queries antes de decidir
            abiertas_data = rows_abiertas[0] if rows_abiertas else {}
            
            # Query ventas cerradas via API local
            # FIX: Incluir fecha_operacion para QRO
            query_cerradas = query_template_cerradas.format(
                sucursal_id=sucursal_id,
                fecha_operacion=fecha_operacion_str
            )
            rows_cerradas, _ = _execute_query_via_api_local(api_config, query_cerradas)
            cerradas_data = rows_cerradas[0] if rows_cerradas else {}
            
            # Extraer valores ANTES de decidir
            ventas_abiertas_raw = abiertas_data.get('ventas_abiertas')
            ventas_cerradas_raw = cerradas_data.get('ventas_cerradas_dia')
            
            # FIX 2026-05-15: QRO - Si ambas son NULL, conservar último dato válido
            # Pero si ventas_cerradas tiene valor, es dato válido (aunque abiertas sea NULL)
            if unidad_id == '130QRO':
                logger.info(f"[SYNC_ABIERTAS_V2] QRO RAW: abiertas={ventas_abiertas_raw}, cerradas={ventas_cerradas_raw}")
                
                # Si ventas_cerradas tiene valor, es dato válido
                if ventas_cerradas_raw is not None and float(ventas_cerradas_raw) > 0:
                    logger.info(f"[SYNC_ABIERTAS_V2] QRO: Usando ventas_cerradas=${ventas_cerradas_raw:,.2f} (abiertas puede ser NULL)")
                elif ventas_abiertas_raw is None and ventas_cerradas_raw is None:
                    # AMBAS son NULL - conservar último dato válido
                    logger.warning(f"[SYNC_ABIERTAS_V2] {nombre}: AMBAS queries retornaron NULL - CONSERVANDO último dato válido")
                    log = SyncLogV2(
                        run_id=run_id,
                        run_type=SyncRunType.ABIERTAS,
                        unidad_negocio_id=unidad_id,
                        server_id=server_id,
                        sucursal_id=sucursal_id,
                        fecha_inicio=fecha_hoy,
                        fecha_fin=fecha_hoy,
                        status=SyncStatus.SKIPPED,
                        records_processed=0,
                        records_skipped=1,
                        error_message=f"AMBAS queries NULL para fecha {fecha_operacion_str}. Conservando último dato válido.",
                        source_connection_status="API_LOCAL_OK_BOTH_NULL"
                    )
                    insert_sync_log(log)
                    results["detalles_unidades"].append({
                        "unidad": unidad_id,
                        "nombre": nombre,
                        "status": "SKIPPED_BOTH_NULL",
                        "fecha_operacion": fecha_operacion_str,
                        "mensaje": "Conservando último dato válido"
                    })
                    continue  # NO sobrescribir con $0
            
            # Extraer valores finales (abiertas_data y cerradas_data ya están definidos arriba)
            ventas_abiertas = Decimal(str(abiertas_data.get('ventas_abiertas') or 0))
            tickets_abiertos = int(abiertas_data.get('tickets_abiertos') or 0)
            pax_abiertos = int(abiertas_data.get('pax_abiertos') or 0)
            
            ventas_cerradas_dia = Decimal(str(cerradas_data.get('ventas_cerradas_dia') or 0))
            tickets_cerrados_dia = int(cerradas_data.get('tickets_cerrados_dia') or 0)
            pax_cerrados_dia = int(cerradas_data.get('pax_cerrados_dia') or 0)
            
            total_estimado_dia = ventas_abiertas + ventas_cerradas_dia
            
            # FIX 2026-05-15: Log detallado para QRO (diagnóstico de bug $0)
            if unidad_id == '130QRO':
                logger.info(f"[SYNC_ABIERTAS_V2] QRO DETALLE:")
                logger.info(f"  fecha_operacion_backend: {fecha_operacion_str}")
                logger.info(f"  server_id: {server_id}")
                logger.info(f"  api_url: {api_config['api_url']}")
                logger.info(f"  raw_abiertas: {abiertas_data}")
                logger.info(f"  raw_cerradas: {cerradas_data}")
                logger.info(f"  ventas_abiertas: ${ventas_abiertas:,.2f}")
                logger.info(f"  ventas_cerradas_dia: ${ventas_cerradas_dia:,.2f}")
                logger.info(f"  total_estimado_dia: ${total_estimado_dia:,.2f}")
            
            # Crear modelo y upsert
            ventas_model = VentasDiaAbiertasV2(
                unidad_negocio_id=unidad_id,
                unidad_negocio_nombre=nombre,
                server_id=server_id,
                sucursal_id=sucursal_id,
                sucursal_nombre=nombre,
                sistema_origen=SistemaOrigen.MPRO,
                snapshot_timestamp=datetime.now(timezone.utc),
                fecha_operacion=fecha_hoy,
                ventas_abiertas=ventas_abiertas,
                tickets_abiertos=tickets_abiertos,
                pax_abiertos=pax_abiertos,
                ventas_cerradas_dia=ventas_cerradas_dia,
                tickets_cerrados_dia=tickets_cerrados_dia,
                pax_cerrados_dia=pax_cerrados_dia,
                total_estimado_dia=total_estimado_dia,
                fuente_original=FuenteOriginal.API_LOCAL,
                sync_run_id=run_id,
                source_status="SYNC_OK"
            )
            
            upsert_result = upsert_ventas_dia_abiertas(ventas_model)
            
            results["unidades_exitosas"] += 1
            results["total_ventas_abiertas"] += float(ventas_abiertas)
            results["total_estimado_dia"] += float(total_estimado_dia)
            results["detalles_unidades"].append({
                "unidad_negocio_id": unidad_id,
                "unidad": nombre,
                "sistema": "MPRO",
                "fuente": "API_LOCAL",
                "estatus": "OK",
                "source_status": "SYNC_OK",
                "ventas_abiertas": float(ventas_abiertas),
                "total_estimado_dia": float(total_estimado_dia)
            })
            
            logger.info(f"[SYNC_ABIERTAS_V2] {nombre} (API Local): total=${total_estimado_dia:,.2f}")
            
            # Log exitoso
            log = SyncLogV2(
                run_id=run_id,
                run_type=SyncRunType.VENTAS_DIA,
                unidad_negocio_id=unidad_id,
                server_id=server_id,
                fecha_inicio=fecha_hoy,
                fecha_fin=fecha_hoy,
                status=SyncStatus.SUCCESS,
                records_processed=1,
                records_inserted=1 if upsert_result.get('action') == 'INSERT' else 0,
                records_updated=1 if upsert_result.get('action') == 'UPDATE' else 0,
                source_connection_status=ConnectionStatus.ONLINE
            )
            insert_sync_log(log)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[SYNC_ABIERTAS_V2] Error en {nombre}: {error_msg}")
            results["unidades_fallidas"] += 1
            results["errores"].append(f"{nombre}: {error_msg}")
            
            # REGLA: Conservar último dato válido, NO escribir $0
            results["detalles_unidades"].append({
                "unidad_negocio_id": unidad_id,
                "unidad": nombre,
                "sistema": "MPRO",
                "fuente": "API_LOCAL",
                "estatus": "ERROR",
                "source_status": "SYNC_FAILED",
                "mensaje_error": error_msg[:200]
            })
            
            # Log de error
            log = SyncLogV2(
                run_id=run_id,
                run_type=SyncRunType.VENTAS_DIA,
                unidad_negocio_id=unidad_id,
                server_id=unidad.get("server_id", "UNKNOWN"),
                fecha_inicio=fecha_hoy,
                fecha_fin=fecha_hoy,
                status=SyncStatus.FAILED,
                error_message=error_msg[:500],
                source_connection_status=ConnectionStatus.OFFLINE
            )
            insert_sync_log(log)
    
    # Resumen final
    end_time = datetime.now(timezone.utc)
    results["fin_ejecucion"] = end_time.isoformat()
    results["duracion_segundos"] = (end_time - start_time).total_seconds()
    
    logger.info(
        f"[SYNC_ABIERTAS_V2] === FIN === "
        f"Procesadas: {results['unidades_procesadas']}, "
        f"Exitosas: {results['unidades_exitosas']}, "
        f"Fallidas: {results['unidades_fallidas']}, "
        f"Total día: ${results['total_estimado_dia']:,.2f}"
    )
    
    return results


# =============================================================================
# EJECUCIÓN MANUAL PARA TESTING
# =============================================================================

def run_sync_comercial_abiertas_v2_manual(fecha: date = None):
    """Ejecuta sincronización manualmente (para testing)."""
    import asyncio
    return asyncio.run(execute_sync_comercial_abiertas_v2())


# Exportar
__all__ = ['execute_sync_comercial_abiertas_v2', 'run_sync_comercial_abiertas_v2_manual', 'JOB_NAME']
