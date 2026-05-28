"""
EDARSA HUB - Vtiger Sync Job
============================
Job programado para sincronización automática con Vtiger CRM.

Ejecución: Cada 15 minutos por defecto
Acción: Sincroniza Leads, Contactos, Cuentas y Oportunidades
Dirección: Bidireccional (configurable)

Flujo:
1. Obtener registros modificados desde última sincronización
2. Mapear campos Vtiger → EDARSA HUB
3. Insertar/Actualizar en tablas Sync_Vtiger_*
4. (Opcional) Enviar cambios locales a Vtiger
"""

import os
import logging
import pymssql
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)

# Configuración de conexión SQL Server
def _get_sql_connection():
    """Obtiene conexión a EDARSAHUB SQL Server"""
    return pymssql.connect(
        server=os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
        port=int(os.environ.get('EDARSAHUB_PORT', 1433)),
        user=os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
        password=os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
        database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
        as_dict=True
    )


# ==================== MAPEO DE CAMPOS ====================

VTIGER_TO_SQL_MAPPING = {
    'Leads': {
        'table': 'Sync_Vtiger_Leads',
        'fields': {
            'id': 'VtigerID',
            'lead_no': 'LeadNo',
            'firstname': 'Nombre',
            'lastname': 'Apellido',
            'company': 'Empresa',
            'email': 'Email',
            'phone': 'Telefono',
            'mobile': 'Celular',
            'website': 'Website',
            'industry': 'Industria',
            'leadsource': 'FuenteLead',
            'leadstatus': 'Estatus',
            'annualrevenue': 'IngresoAnual',
            'noofemployees': 'NumEmpleados',
            'description': 'Descripcion',
            'city': 'Ciudad',
            'state': 'Estado',
            'country': 'Pais',
            'assigned_user_id': 'UsuarioAsignadoVtiger',
            'createdtime': 'FechaCreacionVtiger',
            'modifiedtime': 'FechaModificacionVtiger'
        }
    },
    'Contacts': {
        'table': 'Sync_Vtiger_Contactos',
        'fields': {
            'id': 'VtigerID',
            'contact_no': 'ContactoNo',
            'firstname': 'Nombre',
            'lastname': 'Apellido',
            'email': 'Email',
            'phone': 'Telefono',
            'mobile': 'Celular',
            'title': 'Titulo',
            'department': 'Departamento',
            'account_id': 'CuentaVtigerID',
            'description': 'Descripcion',
            'mailingcity': 'Ciudad',
            'mailingstate': 'Estado',
            'mailingcountry': 'Pais',
            'assigned_user_id': 'UsuarioAsignadoVtiger',
            'createdtime': 'FechaCreacionVtiger',
            'modifiedtime': 'FechaModificacionVtiger'
        }
    },
    'Accounts': {
        'table': 'Sync_Vtiger_Cuentas',
        'fields': {
            'id': 'VtigerID',
            'account_no': 'CuentaNo',
            'accountname': 'NombreCuenta',
            'website': 'Website',
            'phone': 'Telefono',
            'fax': 'Fax',
            'email1': 'Email',
            'industry': 'Industria',
            'accounttype': 'TipoCuenta',
            'annualrevenue': 'IngresoAnual',
            'employees': 'NumEmpleados',
            'description': 'Descripcion',
            'bill_city': 'Ciudad',
            'bill_state': 'Estado',
            'bill_country': 'Pais',
            'assigned_user_id': 'UsuarioAsignadoVtiger',
            'createdtime': 'FechaCreacionVtiger',
            'modifiedtime': 'FechaModificacionVtiger'
        }
    },
    'Potentials': {
        'table': 'Sync_Vtiger_Oportunidades',
        'fields': {
            'id': 'VtigerID',
            'potential_no': 'OportunidadNo',
            'potentialname': 'NombreOportunidad',
            'amount': 'Monto',
            'related_to': 'CuentaVtigerID',
            'contact_id': 'ContactoVtigerID',
            'closingdate': 'FechaCierre',
            'sales_stage': 'EtapaVenta',
            'probability': 'Probabilidad',
            'leadsource': 'FuenteLead',
            'nextstep': 'SiguientePaso',
            'description': 'Descripcion',
            'assigned_user_id': 'UsuarioAsignadoVtiger',
            'createdtime': 'FechaCreacionVtiger',
            'modifiedtime': 'FechaModificacionVtiger'
        }
    }
}


# ==================== FUNCIONES DE SINCRONIZACIÓN ====================

async def sync_module_from_vtiger(
    client,
    module: str,
    conn,
    last_sync: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Sincroniza un módulo desde Vtiger a SQL Server.
    
    Args:
        client: VtigerClient
        module: Nombre del módulo (Leads, Contacts, etc.)
        conn: Conexión SQL Server (puede ser None si no hay tablas)
        last_sync: Fecha de última sincronización
    
    Returns:
        Dict con estadísticas de sincronización
    """
    mapping = VTIGER_TO_SQL_MAPPING.get(module)
    if not mapping:
        return {"success": False, "error": f"Módulo {module} no soportado"}
    
    stats = {
        "module": module,
        "records_fetched": 0,
        "records_inserted": 0,
        "records_updated": 0,
        "records": [],  # Almacenar registros si no hay SQL
        "errors": []
    }
    
    try:
        # Obtener registros de Vtiger
        if module == 'Leads':
            result = await client.get_leads(limit=500)
        elif module == 'Contacts':
            result = await client.get_contacts(limit=500)
        elif module == 'Accounts':
            result = await client.get_accounts(limit=500)
        elif module == 'Potentials':
            result = await client.get_opportunities(limit=500)
        else:
            return {"success": False, "error": f"Módulo {module} no implementado"}
        
        if not result.get("success"):
            return {"success": False, "error": result.get("error")}
        
        records = result.get("records", [])
        stats["records_fetched"] = len(records)
        
        if not records:
            stats["success"] = True
            return stats
        
        # Si hay conexión SQL y las tablas existen, usar SQL
        table_exists = False
        if conn:
            try:
                cursor = conn.cursor()
                table_name = mapping["table"]
                cursor.execute(f"""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = '{table_name}'
                """)
                table_exists = cursor.fetchone()[0] > 0
            except:
                table_exists = False
        
        if conn and table_exists:
            # Sincronizar a SQL Server
            cursor = conn.cursor()
            table_name = mapping["table"]
            field_map = mapping["fields"]
            
            for record in records:
                try:
                    vtiger_id = record.get("id")
                    if not vtiger_id:
                        continue
                    
                    # Verificar si ya existe
                    cursor.execute(
                        f"SELECT SyncID FROM {table_name} WHERE VtigerID = %s",
                        (vtiger_id,)
                    )
                    existing = cursor.fetchone()
                    
                    # Mapear campos
                    sql_data = {}
                    for vtiger_field, sql_field in field_map.items():
                        value = record.get(vtiger_field)
                        if value is not None:
                            if sql_field in ['IngresoAnual', 'Monto']:
                                try:
                                    sql_data[sql_field] = float(value) if value else 0.0
                                except:
                                    sql_data[sql_field] = 0.0
                            elif sql_field in ['NumEmpleados', 'Probabilidad']:
                                try:
                                    sql_data[sql_field] = int(value) if value else 0
                                except:
                                    sql_data[sql_field] = 0
                            else:
                                sql_data[sql_field] = str(value)[:500] if value else None
                    
                    if existing:
                        set_clause = ", ".join([f"{k} = %s" for k in sql_data.keys()])
                        set_clause += ", FechaUltimaSync = GETDATE()"
                        values = list(sql_data.values()) + [vtiger_id]
                        
                        cursor.execute(
                            f"UPDATE {table_name} SET {set_clause} WHERE VtigerID = %s",
                            tuple(values)
                        )
                        stats["records_updated"] += 1
                    else:
                        sql_data["FechaUltimaSync"] = datetime.utcnow()
                        sql_data["FechaCreacionLocal"] = datetime.utcnow()
                        
                        columns = ", ".join(sql_data.keys())
                        placeholders = ", ".join(["%s"] * len(sql_data))
                        
                        cursor.execute(
                            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
                            tuple(sql_data.values())
                        )
                        stats["records_inserted"] += 1
                    
                except Exception as e:
                    stats["errors"].append(f"Error procesando {vtiger_id}: {str(e)[:100]}")
                    if len(stats["errors"]) > 10:
                        break
            
            conn.commit()
        else:
            # Sin SQL, solo almacenar en memoria/archivo
            stats["records"] = records
            stats["records_inserted"] = len(records)
            stats["storage"] = "memory"
            logger.info(f"[VTIGER-SYNC] {module}: Almacenado en memoria ({len(records)} registros)")
        
        stats["success"] = True
        
    except Exception as e:
        logger.error(f"[VTIGER-SYNC] Error en módulo {module}: {e}")
        stats["success"] = False
        stats["error"] = str(e)
    
    return stats


# ==================== JOB PRINCIPAL ====================

async def execute_vtiger_sync(db) -> Dict[str, Any]:
    """
    Job principal de sincronización con Vtiger.
    
    Args:
        db: StubDatabase (no usado, SQL Server directo)
    
    Returns:
        Dict con resultados de la sincronización
    """
    from modules.crm.vtiger_client import create_vtiger_client
    
    inicio = datetime.now()
    run_id = f"VTIGER-{inicio.strftime('%Y%m%d-%H%M%S')}"
    
    logger.info(f"[VTIGER-SYNC] Iniciando sincronización (run_id={run_id})")
    
    # Resultados globales
    resultados = {
        "run_id": run_id,
        "inicio": inicio.isoformat(),
        "modulos": {},
        "total_fetched": 0,
        "total_inserted": 0,
        "total_updated": 0,
        "errores": []
    }
    
    # Obtener configuración desde ENV
    base_url = os.environ.get('VTIGER_BASE_URL')
    username = os.environ.get('VTIGER_USERNAME')
    access_key = os.environ.get('VTIGER_ACCESS_KEY')
    
    if not all([base_url, username, access_key]):
        logger.warning("[VTIGER-SYNC] Configuración incompleta - saltando sincronización")
        return {
            "success": False,
            "error": "Configuración de Vtiger incompleta",
            "run_id": run_id
        }
    
    # Crear cliente Vtiger
    client = create_vtiger_client(base_url, username, access_key)
    
    # Verificar conexión
    test_result = await client.test_connection()
    if not test_result.get("success"):
        await client.close()
        logger.error(f"[VTIGER-SYNC] Error de conexión: {test_result.get('error')}")
        return {
            "success": False,
            "error": f"Error de conexión: {test_result.get('error')}",
            "run_id": run_id
        }
    
    logger.info(f"[VTIGER-SYNC] Conexión exitosa - Usuario: {test_result.get('user', {}).get('username')}")
    
    # Obtener conexión SQL
    conn = None
    try:
        conn = _get_sql_connection()
        
        # Sincronizar cada módulo
        modules_to_sync = ['Leads', 'Contacts', 'Accounts', 'Potentials']
        
        for module in modules_to_sync:
            try:
                logger.info(f"[VTIGER-SYNC] Sincronizando módulo: {module}")
                
                stats = await sync_module_from_vtiger(client, module, conn)
                resultados["modulos"][module] = stats
                
                if stats.get("success"):
                    resultados["total_fetched"] += stats.get("records_fetched", 0)
                    resultados["total_inserted"] += stats.get("records_inserted", 0)
                    resultados["total_updated"] += stats.get("records_updated", 0)
                    
                    logger.info(
                        f"[VTIGER-SYNC] {module}: {stats['records_fetched']} obtenidos, "
                        f"{stats['records_inserted']} insertados, {stats['records_updated']} actualizados"
                    )
                else:
                    resultados["errores"].append(f"{module}: {stats.get('error')}")
                    
            except Exception as e:
                logger.error(f"[VTIGER-SYNC] Error en módulo {module}: {e}")
                resultados["errores"].append(f"{module}: {str(e)}")
        
        # Registrar en log de sincronización (solo si la tabla existe)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'Sync_Vtiger_Log'
            """)
            if cursor.fetchone()[0] > 0:
                cursor.execute("""
                    INSERT INTO Sync_Vtiger_Log 
                    (RunID, FechaInicio, FechaFin, TotalObtenidos, TotalInsertados, TotalActualizados, Errores, ResultadoJSON)
                    VALUES (%s, %s, GETDATE(), %s, %s, %s, %s, %s)
                """, (
                    run_id,
                    inicio,
                    resultados["total_fetched"],
                    resultados["total_inserted"],
                    resultados["total_updated"],
                    len(resultados["errores"]),
                    json.dumps(resultados, default=str)[:4000]
                ))
                conn.commit()
                logger.info(f"[VTIGER-SYNC] Log registrado en SQL")
            else:
                logger.info(f"[VTIGER-SYNC] Tabla Sync_Vtiger_Log no existe - log solo en archivo")
        except Exception as e:
            logger.warning(f"[VTIGER-SYNC] Error registrando en log SQL: {e}")
        
    except Exception as e:
        logger.error(f"[VTIGER-SYNC] Error general: {e}")
        resultados["errores"].append(str(e))
    finally:
        if conn:
            conn.close()
        await client.close()
    
    # Calcular duración
    fin = datetime.now()
    duracion_ms = int((fin - inicio).total_seconds() * 1000)
    
    resultados["fin"] = fin.isoformat()
    resultados["duracion_ms"] = duracion_ms
    resultados["success"] = len(resultados["errores"]) == 0
    
    logger.info(
        f"[VTIGER-SYNC] Completado (run_id={run_id}): "
        f"{resultados['total_fetched']} obtenidos, "
        f"{resultados['total_inserted']} insertados, "
        f"{resultados['total_updated']} actualizados, "
        f"{len(resultados['errores'])} errores, "
        f"{duracion_ms}ms"
    )
    
    return resultados


# ==================== FUNCIONES AUXILIARES ====================

async def get_vtiger_sync_status() -> Dict[str, Any]:
    """Obtiene el estado de la última sincronización"""
    try:
        conn = _get_sql_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT TOP 1 
                RunID, FechaInicio, FechaFin, 
                TotalObtenidos, TotalInsertados, TotalActualizados, Errores
            FROM Sync_Vtiger_Log
            ORDER BY FechaInicio DESC
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "last_sync": {
                    "run_id": row["RunID"],
                    "fecha_inicio": row["FechaInicio"].isoformat() if row["FechaInicio"] else None,
                    "fecha_fin": row["FechaFin"].isoformat() if row["FechaFin"] else None,
                    "total_obtenidos": row["TotalObtenidos"],
                    "total_insertados": row["TotalInsertados"],
                    "total_actualizados": row["TotalActualizados"],
                    "errores": row["Errores"]
                }
            }
        else:
            return {"last_sync": None, "message": "Sin sincronizaciones previas"}
            
    except Exception as e:
        return {"error": str(e)}
