"""
EDARSA HUB - Vtiger Sync Job (SQL-First)
=========================================
Job de sincronización bidireccional con Vtiger CRM.
Almacena datos en tablas Sync_Vtiger_* de EDARSAHUB SQL Server.

Ejecución: Cada 15 minutos
Dirección: Bidireccional (Vtiger ↔ EDARSA SQL)
"""

import os
import logging
import pymssql
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()


logger = logging.getLogger(__name__)


def _get_sql_connection():
    """Obtiene conexión a EDARSAHUB SQL Server"""
    return pymssql.connect(
        server=_edarsa_cfg.host,
        port=int(os.environ.get('EDARSAHUB_PORT', 1433)),
        user=_edarsa_cfg.user,
        password=_edarsa_cfg.password,
        database=_edarsa_cfg.database
    )


# ==================== MAPEO VTIGER → SQL ====================

def _safe_str(value, max_len=500):
    """Convierte valor a string seguro"""
    if value is None:
        return None
    return str(value)[:max_len]

def _safe_decimal(value):
    """Convierte valor a decimal"""
    try:
        return float(value) if value else 0.0
    except:
        return 0.0

def _safe_int(value):
    """Convierte valor a entero"""
    try:
        return int(float(value)) if value else 0
    except:
        return 0


async def sync_leads_to_sql(client, conn) -> Dict[str, Any]:
    """Sincroniza leads de Vtiger a SQL"""
    stats = {"records_fetched": 0, "records_inserted": 0, "records_updated": 0, "errors": []}
    
    result = await client.get_leads(limit=500)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), **stats}
    
    records = result.get("records", [])
    stats["records_fetched"] = len(records)
    
    cursor = conn.cursor()
    
    for r in records:
        try:
            vtiger_id = r.get("id")
            if not vtiger_id:
                continue
            
            # Verificar si existe
            cursor.execute("SELECT SyncID FROM Sync_Vtiger_Leads WHERE VtigerID = %s", (vtiger_id,))
            existing = cursor.fetchone()
            
            if existing:
                # UPDATE
                cursor.execute("""
                    UPDATE Sync_Vtiger_Leads SET
                        LeadNo = %s, Nombre = %s, Apellido = %s, Empresa = %s,
                        Email = %s, Telefono = %s, Celular = %s, Website = %s,
                        Industria = %s, FuenteLead = %s, Estatus = %s,
                        IngresoAnual = %s, NumEmpleados = %s, Descripcion = %s,
                        Ciudad = %s, Estado = %s, Pais = %s,
                        FechaModificacionVtiger = %s, FechaUltimaSync = GETDATE()
                    WHERE VtigerID = %s
                """, (
                    _safe_str(r.get("lead_no")), _safe_str(r.get("firstname")), _safe_str(r.get("lastname")),
                    _safe_str(r.get("company")), _safe_str(r.get("email")), _safe_str(r.get("phone")),
                    _safe_str(r.get("mobile")), _safe_str(r.get("website")), _safe_str(r.get("industry")),
                    _safe_str(r.get("leadsource")), _safe_str(r.get("leadstatus")),
                    _safe_decimal(r.get("annualrevenue")), _safe_int(r.get("noofemployees")),
                    _safe_str(r.get("description"), 4000), _safe_str(r.get("city")),
                    _safe_str(r.get("state")), _safe_str(r.get("country")),
                    _safe_str(r.get("modifiedtime")), vtiger_id
                ))
                stats["records_updated"] += 1
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO Sync_Vtiger_Leads (
                        VtigerID, LeadNo, Nombre, Apellido, Empresa, Email, Telefono, Celular,
                        Website, Industria, FuenteLead, Estatus, IngresoAnual, NumEmpleados,
                        Descripcion, Ciudad, Estado, Pais, FechaCreacionVtiger, FechaModificacionVtiger
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    vtiger_id, _safe_str(r.get("lead_no")), _safe_str(r.get("firstname")),
                    _safe_str(r.get("lastname")), _safe_str(r.get("company")), _safe_str(r.get("email")),
                    _safe_str(r.get("phone")), _safe_str(r.get("mobile")), _safe_str(r.get("website")),
                    _safe_str(r.get("industry")), _safe_str(r.get("leadsource")), _safe_str(r.get("leadstatus")),
                    _safe_decimal(r.get("annualrevenue")), _safe_int(r.get("noofemployees")),
                    _safe_str(r.get("description"), 4000), _safe_str(r.get("city")),
                    _safe_str(r.get("state")), _safe_str(r.get("country")),
                    _safe_str(r.get("createdtime")), _safe_str(r.get("modifiedtime"))
                ))
                stats["records_inserted"] += 1
            
            conn.commit()
        except Exception as e:
            stats["errors"].append(f"Lead {vtiger_id}: {str(e)[:50]}")
    
    stats["success"] = True
    return stats


async def sync_contacts_to_sql(client, conn) -> Dict[str, Any]:
    """Sincroniza contactos de Vtiger a SQL"""
    stats = {"records_fetched": 0, "records_inserted": 0, "records_updated": 0, "errors": []}
    
    result = await client.get_contacts(limit=500)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), **stats}
    
    records = result.get("records", [])
    stats["records_fetched"] = len(records)
    
    cursor = conn.cursor()
    
    for r in records:
        try:
            vtiger_id = r.get("id")
            if not vtiger_id:
                continue
            
            cursor.execute("SELECT SyncID FROM Sync_Vtiger_Contactos WHERE VtigerID = %s", (vtiger_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE Sync_Vtiger_Contactos SET
                        ContactoNo = %s, Nombre = %s, Apellido = %s, Email = %s,
                        Telefono = %s, Celular = %s, Titulo = %s, Departamento = %s,
                        CuentaVtigerID = %s, Descripcion = %s, Ciudad = %s, Estado = %s, Pais = %s,
                        FechaModificacionVtiger = %s, FechaUltimaSync = GETDATE()
                    WHERE VtigerID = %s
                """, (
                    _safe_str(r.get("contact_no")), _safe_str(r.get("firstname")), _safe_str(r.get("lastname")),
                    _safe_str(r.get("email")), _safe_str(r.get("phone")), _safe_str(r.get("mobile")),
                    _safe_str(r.get("title")), _safe_str(r.get("department")), _safe_str(r.get("account_id")),
                    _safe_str(r.get("description"), 4000), _safe_str(r.get("mailingcity")),
                    _safe_str(r.get("mailingstate")), _safe_str(r.get("mailingcountry")),
                    _safe_str(r.get("modifiedtime")), vtiger_id
                ))
                stats["records_updated"] += 1
            else:
                cursor.execute("""
                    INSERT INTO Sync_Vtiger_Contactos (
                        VtigerID, ContactoNo, Nombre, Apellido, Email, Telefono, Celular,
                        Titulo, Departamento, CuentaVtigerID, Descripcion, Ciudad, Estado, Pais,
                        FechaCreacionVtiger, FechaModificacionVtiger
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    vtiger_id, _safe_str(r.get("contact_no")), _safe_str(r.get("firstname")),
                    _safe_str(r.get("lastname")), _safe_str(r.get("email")), _safe_str(r.get("phone")),
                    _safe_str(r.get("mobile")), _safe_str(r.get("title")), _safe_str(r.get("department")),
                    _safe_str(r.get("account_id")), _safe_str(r.get("description"), 4000),
                    _safe_str(r.get("mailingcity")), _safe_str(r.get("mailingstate")),
                    _safe_str(r.get("mailingcountry")), _safe_str(r.get("createdtime")),
                    _safe_str(r.get("modifiedtime"))
                ))
                stats["records_inserted"] += 1
            
            conn.commit()
        except Exception as e:
            stats["errors"].append(f"Contact {vtiger_id}: {str(e)[:50]}")
    
    stats["success"] = True
    return stats


async def sync_accounts_to_sql(client, conn) -> Dict[str, Any]:
    """Sincroniza cuentas de Vtiger a SQL"""
    stats = {"records_fetched": 0, "records_inserted": 0, "records_updated": 0, "errors": []}
    
    result = await client.get_accounts(limit=500)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), **stats}
    
    records = result.get("records", [])
    stats["records_fetched"] = len(records)
    
    cursor = conn.cursor()
    
    for r in records:
        try:
            vtiger_id = r.get("id")
            if not vtiger_id:
                continue
            
            cursor.execute("SELECT SyncID FROM Sync_Vtiger_Cuentas WHERE VtigerID = %s", (vtiger_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE Sync_Vtiger_Cuentas SET
                        CuentaNo = %s, NombreCuenta = %s, Website = %s, Telefono = %s,
                        Fax = %s, Email = %s, Industria = %s, TipoCuenta = %s,
                        IngresoAnual = %s, NumEmpleados = %s, Descripcion = %s,
                        Ciudad = %s, Estado = %s, Pais = %s,
                        FechaModificacionVtiger = %s, FechaUltimaSync = GETDATE()
                    WHERE VtigerID = %s
                """, (
                    _safe_str(r.get("account_no")), _safe_str(r.get("accountname")), _safe_str(r.get("website")),
                    _safe_str(r.get("phone")), _safe_str(r.get("fax")), _safe_str(r.get("email1")),
                    _safe_str(r.get("industry")), _safe_str(r.get("accounttype")),
                    _safe_decimal(r.get("annualrevenue")), _safe_int(r.get("employees")),
                    _safe_str(r.get("description"), 4000), _safe_str(r.get("bill_city")),
                    _safe_str(r.get("bill_state")), _safe_str(r.get("bill_country")),
                    _safe_str(r.get("modifiedtime")), vtiger_id
                ))
                stats["records_updated"] += 1
            else:
                cursor.execute("""
                    INSERT INTO Sync_Vtiger_Cuentas (
                        VtigerID, CuentaNo, NombreCuenta, Website, Telefono, Fax, Email,
                        Industria, TipoCuenta, IngresoAnual, NumEmpleados, Descripcion,
                        Ciudad, Estado, Pais, FechaCreacionVtiger, FechaModificacionVtiger
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    vtiger_id, _safe_str(r.get("account_no")), _safe_str(r.get("accountname")),
                    _safe_str(r.get("website")), _safe_str(r.get("phone")), _safe_str(r.get("fax")),
                    _safe_str(r.get("email1")), _safe_str(r.get("industry")), _safe_str(r.get("accounttype")),
                    _safe_decimal(r.get("annualrevenue")), _safe_int(r.get("employees")),
                    _safe_str(r.get("description"), 4000), _safe_str(r.get("bill_city")),
                    _safe_str(r.get("bill_state")), _safe_str(r.get("bill_country")),
                    _safe_str(r.get("createdtime")), _safe_str(r.get("modifiedtime"))
                ))
                stats["records_inserted"] += 1
            
            conn.commit()
        except Exception as e:
            stats["errors"].append(f"Account {vtiger_id}: {str(e)[:50]}")
    
    stats["success"] = True
    return stats


async def sync_opportunities_to_sql(client, conn) -> Dict[str, Any]:
    """Sincroniza oportunidades de Vtiger a SQL"""
    stats = {"records_fetched": 0, "records_inserted": 0, "records_updated": 0, "errors": []}
    
    result = await client.get_opportunities(limit=500)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), **stats}
    
    records = result.get("records", [])
    stats["records_fetched"] = len(records)
    
    cursor = conn.cursor()
    
    for r in records:
        try:
            vtiger_id = r.get("id")
            if not vtiger_id:
                continue
            
            cursor.execute("SELECT SyncID FROM Sync_Vtiger_Oportunidades WHERE VtigerID = %s", (vtiger_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE Sync_Vtiger_Oportunidades SET
                        OportunidadNo = %s, NombreOportunidad = %s, Monto = %s,
                        CuentaVtigerID = %s, ContactoVtigerID = %s, FechaCierre = %s,
                        EtapaVenta = %s, Probabilidad = %s, FuenteLead = %s,
                        SiguientePaso = %s, Descripcion = %s,
                        FechaModificacionVtiger = %s, FechaUltimaSync = GETDATE()
                    WHERE VtigerID = %s
                """, (
                    _safe_str(r.get("potential_no")), _safe_str(r.get("potentialname")),
                    _safe_decimal(r.get("amount")), _safe_str(r.get("related_to")),
                    _safe_str(r.get("contact_id")), _safe_str(r.get("closingdate")),
                    _safe_str(r.get("sales_stage")), _safe_int(r.get("probability")),
                    _safe_str(r.get("leadsource")), _safe_str(r.get("nextstep")),
                    _safe_str(r.get("description"), 4000), _safe_str(r.get("modifiedtime")),
                    vtiger_id
                ))
                stats["records_updated"] += 1
            else:
                cursor.execute("""
                    INSERT INTO Sync_Vtiger_Oportunidades (
                        VtigerID, OportunidadNo, NombreOportunidad, Monto, CuentaVtigerID,
                        ContactoVtigerID, FechaCierre, EtapaVenta, Probabilidad, FuenteLead,
                        SiguientePaso, Descripcion, FechaCreacionVtiger, FechaModificacionVtiger
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    vtiger_id, _safe_str(r.get("potential_no")), _safe_str(r.get("potentialname")),
                    _safe_decimal(r.get("amount")), _safe_str(r.get("related_to")),
                    _safe_str(r.get("contact_id")), _safe_str(r.get("closingdate")),
                    _safe_str(r.get("sales_stage")), _safe_int(r.get("probability")),
                    _safe_str(r.get("leadsource")), _safe_str(r.get("nextstep")),
                    _safe_str(r.get("description"), 4000), _safe_str(r.get("createdtime")),
                    _safe_str(r.get("modifiedtime"))
                ))
                stats["records_inserted"] += 1
            
            conn.commit()
        except Exception as e:
            stats["errors"].append(f"Potential {vtiger_id}: {str(e)[:50]}")
    
    stats["success"] = True
    return stats


# ==================== JOB PRINCIPAL ====================

async def execute_vtiger_sync(db) -> Dict[str, Any]:
    """
    Job principal de sincronización Vtiger → SQL Server.
    """
    from modules.crm.vtiger_client import create_vtiger_client
    
    inicio = datetime.now()
    run_id = f"VTIGER-{inicio.strftime('%Y%m%d-%H%M%S')}"
    
    logger.info(f"[VTIGER-SYNC] Iniciando sincronización (run_id={run_id})")
    
    resultados = {
        "run_id": run_id,
        "inicio": inicio.isoformat(),
        "modulos": {},
        "total_fetched": 0,
        "total_inserted": 0,
        "total_updated": 0,
        "errores": []
    }
    
    # Config Vtiger
    base_url = os.environ.get('VTIGER_BASE_URL')
    username = os.environ.get('VTIGER_USERNAME')
    access_key = os.environ.get('VTIGER_ACCESS_KEY')
    
    if not all([base_url, username, access_key]):
        return {"success": False, "error": "Configuración Vtiger incompleta", "run_id": run_id}
    
    client = create_vtiger_client(base_url, username, access_key)
    
    # Verificar conexión
    test_result = await client.test_connection()
    if not test_result.get("success"):
        await client.close()
        return {"success": False, "error": test_result.get("error"), "run_id": run_id}
    
    conn = None
    try:
        conn = _get_sql_connection()
        
        # Sincronizar cada módulo
        sync_functions = [
            ("Leads", sync_leads_to_sql),
            ("Contacts", sync_contacts_to_sql),
            ("Accounts", sync_accounts_to_sql),
            ("Potentials", sync_opportunities_to_sql)
        ]
        
        for module_name, sync_func in sync_functions:
            try:
                logger.info(f"[VTIGER-SYNC] Sincronizando {module_name}...")
                stats = await sync_func(client, conn)
                resultados["modulos"][module_name] = stats
                
                resultados["total_fetched"] += stats.get("records_fetched", 0)
                resultados["total_inserted"] += stats.get("records_inserted", 0)
                resultados["total_updated"] += stats.get("records_updated", 0)
                
                logger.info(f"[VTIGER-SYNC] {module_name}: {stats.get('records_fetched', 0)} obtenidos, "
                           f"{stats.get('records_inserted', 0)} insertados, {stats.get('records_updated', 0)} actualizados")
            except Exception as e:
                logger.error(f"[VTIGER-SYNC] Error en {module_name}: {e}")
                resultados["errores"].append(f"{module_name}: {str(e)}")
        
        # Registrar en log
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Sync_Vtiger_Log (RunID, Direccion, FechaInicio, FechaFin, TotalObtenidos, TotalInsertados, TotalActualizados, Errores, ResultadoJSON)
                VALUES (%s, 'vtiger_to_sql', %s, GETDATE(), %s, %s, %s, %s, %s)
            """, (run_id, inicio, resultados["total_fetched"], resultados["total_inserted"],
                  resultados["total_updated"], len(resultados["errores"]), json.dumps(resultados, default=str)[:4000]))
            conn.commit()
        except Exception as e:
            logger.warning(f"[VTIGER-SYNC] Error registrando log: {e}")
        
    except Exception as e:
        logger.error(f"[VTIGER-SYNC] Error general: {e}")
        resultados["errores"].append(str(e))
    finally:
        if conn:
            conn.close()
        await client.close()
    
    fin = datetime.now()
    resultados["fin"] = fin.isoformat()
    resultados["duracion_ms"] = int((fin - inicio).total_seconds() * 1000)
    resultados["success"] = len(resultados["errores"]) == 0
    
    logger.info(f"[VTIGER-SYNC] Completado: {resultados['total_inserted']} insertados, "
               f"{resultados['total_updated']} actualizados, {resultados['duracion_ms']}ms")
    
    return resultados


async def get_vtiger_sync_status() -> Dict[str, Any]:
    """Obtiene el estado de la última sincronización"""
    try:
        conn = _get_sql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 1 RunID, Direccion, FechaInicio, FechaFin, 
                   TotalObtenidos, TotalInsertados, TotalActualizados, Errores
            FROM Sync_Vtiger_Log ORDER BY FechaInicio DESC
        """)
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "last_sync": {
                    "run_id": row[0],
                    "direccion": row[1],
                    "fecha_inicio": row[2].isoformat() if row[2] else None,
                    "fecha_fin": row[3].isoformat() if row[3] else None,
                    "total_obtenidos": row[4],
                    "total_insertados": row[5],
                    "total_actualizados": row[6],
                    "errores": row[7]
                }
            }
        return {"last_sync": None}
    except Exception as e:
        return {"error": str(e)}
