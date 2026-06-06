from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - CRM Staging Service
================================
Servicio para gestionar tablas de staging.
Inserta datos externos normalizados antes de pasarlos a producción.
"""

import logging
import pymssql
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
from zoneinfo import ZoneInfo

from .base_connector import (
    LeadExterno, OportunidadExterna, CuentaExterna,
    SyncDirection, SyncStatus
)

logger = logging.getLogger(__name__)

MEXICO_TZ = ZoneInfo("America/Mexico_City")


class StagingService:
    """Servicio para operaciones en tablas de staging CRM"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
    
    def _get_connection(self):
        """Obtiene conexión a SQL Server"""
        return pymssql.connect(
            server=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['username'],
            password=self.db_config['password'],
            login_timeout=30,
            timeout=60,
            autocommit=False
        )
    
    def _now(self) -> datetime:
        """Retorna datetime actual en zona horaria México"""
        return datetime.now(MEXICO_TZ).replace(tzinfo=None)
    
    # ============================================================
    # LEADS STAGING
    # ============================================================
    
    def upsert_staging_lead(
        self,
        conector_id: int,
        lead: LeadExterno,
        direccion: SyncDirection = SyncDirection.ENTRANTE
    ) -> Dict[str, Any]:
        """
        Inserta o actualiza un lead en staging
        
        Args:
            conector_id: ID del conector origen
            lead: Lead normalizado
            direccion: Dirección de sincronización
            
        Returns:
            Resultado de la operación
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            now = self._now()
            
            # Verificar si ya existe
            cursor.execute("""
                SELECT StagingID, EstadoSync 
                FROM CRM_Staging_Leads 
                WHERE ConectorID = %s AND ExternalID = %s
            """, (conector_id, lead.external_id))
            
            existing = cursor.fetchone()
            datos_json = json.dumps(lead.datos_adicionales or {}, default=str)
            
            if existing:
                # UPDATE
                cursor.execute("""
                    UPDATE CRM_Staging_Leads SET
                        NombreContacto = %s,
                        ApellidoPaterno = %s,
                        ApellidoMaterno = %s,
                        NombreEmpresa = %s,
                        Email = %s,
                        Telefono = %s,
                        TelefonoMovil = %s,
                        Puesto = %s,
                        Descripcion = %s,
                        Origen = %s,
                        Estatus = %s,
                        DatosExternosJSON = %s,
                        FechaExterna = %s,
                        EstadoSync = %s,
                        UpdatedAt = %s
                    WHERE StagingID = %s
                """, (
                    lead.nombre_contacto,
                    lead.apellido_paterno,
                    lead.apellido_materno,
                    lead.nombre_empresa,
                    lead.email,
                    lead.telefono,
                    lead.telefono_movil,
                    lead.puesto,
                    lead.descripcion,
                    lead.origen,
                    lead.estatus,
                    datos_json,
                    lead.fecha_modificacion,
                    SyncStatus.PENDIENTE.value,
                    now,
                    existing['StagingID']
                ))
                
                conn.commit()
                logger.debug(f"[Staging] Lead actualizado: {lead.external_id}")
                return {"success": True, "action": "updated", "staging_id": existing['StagingID']}
            
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO CRM_Staging_Leads (
                        ConectorID, ExternalID, NombreContacto, ApellidoPaterno,
                        ApellidoMaterno, NombreEmpresa, Email, Telefono, TelefonoMovil,
                        Puesto, Descripcion, Origen, Estatus, DatosExternosJSON,
                        DireccionSync, EstadoSync, FechaExterna, Intentos, CreatedAt, UpdatedAt
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    conector_id,
                    lead.external_id,
                    lead.nombre_contacto,
                    lead.apellido_paterno,
                    lead.apellido_materno,
                    lead.nombre_empresa,
                    lead.email,
                    lead.telefono,
                    lead.telefono_movil,
                    lead.puesto,
                    lead.descripcion,
                    lead.origen,
                    lead.estatus,
                    datos_json,
                    direccion.value,
                    SyncStatus.PENDIENTE.value,
                    lead.fecha_modificacion,
                    0,
                    now,
                    now
                ))
                
                # Obtener ID insertado
                cursor.execute("SELECT SCOPE_IDENTITY() as id")
                new_id = cursor.fetchone()['id']
                
                conn.commit()
                logger.debug(f"[Staging] Lead insertado: {lead.external_id}")
                return {"success": True, "action": "inserted", "staging_id": int(new_id)}
                
        except Exception as e:
            conn.rollback()
            logger.error(f"[Staging] Error upsert lead: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def bulk_upsert_leads(
        self,
        conector_id: int,
        leads: List[LeadExterno],
        direccion: SyncDirection = SyncDirection.ENTRANTE
    ) -> Dict[str, Any]:
        """
        Inserta/actualiza múltiples leads en staging
        
        Returns:
            Resumen de la operación
        """
        inserted = 0
        updated = 0
        errors = 0
        error_messages = []
        
        for lead in leads:
            result = self.upsert_staging_lead(conector_id, lead, direccion)
            if result['success']:
                if result['action'] == 'inserted':
                    inserted += 1
                else:
                    updated += 1
            else:
                errors += 1
                error_messages.append(f"{lead.external_id}: {result.get('error', 'Unknown')}")
        
        logger.info(f"[Staging] Bulk leads: {inserted} insertados, {updated} actualizados, {errors} errores")
        
        return {
            "success": errors == 0,
            "inserted": inserted,
            "updated": updated,
            "errors": errors,
            "total": len(leads),
            "error_messages": error_messages[:10]  # Solo primeros 10
        }
    
    # ============================================================
    # OPORTUNIDADES STAGING
    # ============================================================
    
    def upsert_staging_oportunidad(
        self,
        conector_id: int,
        opp: OportunidadExterna,
        direccion: SyncDirection = SyncDirection.ENTRANTE
    ) -> Dict[str, Any]:
        """Inserta o actualiza una oportunidad en staging"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            now = self._now()
            
            cursor.execute("""
                SELECT StagingID, EstadoSync 
                FROM CRM_Staging_Oportunidades 
                WHERE ConectorID = %s AND ExternalID = %s
            """, (conector_id, opp.external_id))
            
            existing = cursor.fetchone()
            datos_json = json.dumps(opp.datos_adicionales or {}, default=str)
            fecha_cierre = opp.fecha_estimada_cierre.date() if opp.fecha_estimada_cierre else None
            
            if existing:
                cursor.execute("""
                    UPDATE CRM_Staging_Oportunidades SET
                        NombreOportunidad = %s,
                        Descripcion = %s,
                        MontoEstimado = %s,
                        Moneda = %s,
                        FechaEstimadaCierre = %s,
                        Etapa = %s,
                        Probabilidad = %s,
                        Estatus = %s,
                        ExternalCuentaID = %s,
                        ExternalContactoID = %s,
                        ExternalLeadID = %s,
                        DatosExternosJSON = %s,
                        FechaExterna = %s,
                        EstadoSync = %s,
                        UpdatedAt = %s
                    WHERE StagingID = %s
                """, (
                    opp.nombre,
                    opp.descripcion,
                    opp.monto_estimado,
                    opp.moneda,
                    fecha_cierre,
                    opp.etapa,
                    opp.probabilidad,
                    opp.estatus,
                    opp.external_cuenta_id,
                    opp.external_contacto_id,
                    opp.external_lead_id,
                    datos_json,
                    opp.fecha_modificacion,
                    SyncStatus.PENDIENTE.value,
                    now,
                    existing['StagingID']
                ))
                
                conn.commit()
                return {"success": True, "action": "updated", "staging_id": existing['StagingID']}
            
            else:
                cursor.execute("""
                    INSERT INTO CRM_Staging_Oportunidades (
                        ConectorID, ExternalID, NombreOportunidad, Descripcion,
                        MontoEstimado, Moneda, FechaEstimadaCierre, Etapa, Probabilidad,
                        Estatus, ExternalCuentaID, ExternalContactoID, ExternalLeadID,
                        DatosExternosJSON, DireccionSync, EstadoSync, FechaExterna,
                        Intentos, CreatedAt, UpdatedAt
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    conector_id,
                    opp.external_id,
                    opp.nombre,
                    opp.descripcion,
                    opp.monto_estimado,
                    opp.moneda,
                    fecha_cierre,
                    opp.etapa,
                    opp.probabilidad,
                    opp.estatus,
                    opp.external_cuenta_id,
                    opp.external_contacto_id,
                    opp.external_lead_id,
                    datos_json,
                    direccion.value,
                    SyncStatus.PENDIENTE.value,
                    opp.fecha_modificacion,
                    0,
                    now,
                    now
                ))
                
                cursor.execute("SELECT SCOPE_IDENTITY() as id")
                new_id = cursor.fetchone()['id']
                
                conn.commit()
                return {"success": True, "action": "inserted", "staging_id": int(new_id)}
                
        except Exception as e:
            conn.rollback()
            logger.error(f"[Staging] Error upsert oportunidad: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def bulk_upsert_oportunidades(
        self,
        conector_id: int,
        opps: List[OportunidadExterna],
        direccion: SyncDirection = SyncDirection.ENTRANTE
    ) -> Dict[str, Any]:
        """Inserta/actualiza múltiples oportunidades en staging"""
        inserted = 0
        updated = 0
        errors = 0
        error_messages = []
        
        for opp in opps:
            result = self.upsert_staging_oportunidad(conector_id, opp, direccion)
            if result['success']:
                if result['action'] == 'inserted':
                    inserted += 1
                else:
                    updated += 1
            else:
                errors += 1
                error_messages.append(f"{opp.external_id}: {result.get('error', 'Unknown')}")
        
        logger.info(f"[Staging] Bulk opps: {inserted} insertados, {updated} actualizados, {errors} errores")
        
        return {
            "success": errors == 0,
            "inserted": inserted,
            "updated": updated,
            "errors": errors,
            "total": len(opps),
            "error_messages": error_messages[:10]
        }
    
    # ============================================================
    # CUENTAS STAGING
    # ============================================================
    
    def upsert_staging_cuenta(
        self,
        conector_id: int,
        cuenta: CuentaExterna,
        direccion: SyncDirection = SyncDirection.ENTRANTE
    ) -> Dict[str, Any]:
        """Inserta o actualiza una cuenta en staging"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            now = self._now()
            
            cursor.execute("""
                SELECT StagingID, EstadoSync 
                FROM CRM_Staging_Cuentas 
                WHERE ConectorID = %s AND ExternalID = %s
            """, (conector_id, cuenta.external_id))
            
            existing = cursor.fetchone()
            datos_json = json.dumps(cuenta.datos_adicionales or {}, default=str)
            
            if existing:
                cursor.execute("""
                    UPDATE CRM_Staging_Cuentas SET
                        RazonSocial = %s,
                        NombreComercial = %s,
                        RFC = %s,
                        Industria = %s,
                        SitioWeb = %s,
                        EmailPrincipal = %s,
                        TelefonoPrincipal = %s,
                        Direccion = %s,
                        DatosExternosJSON = %s,
                        FechaExterna = %s,
                        EstadoSync = %s,
                        UpdatedAt = %s
                    WHERE StagingID = %s
                """, (
                    cuenta.razon_social,
                    cuenta.nombre_comercial,
                    cuenta.rfc,
                    cuenta.industria,
                    cuenta.sitio_web,
                    cuenta.email_principal,
                    cuenta.telefono_principal,
                    cuenta.direccion,
                    datos_json,
                    cuenta.fecha_modificacion,
                    SyncStatus.PENDIENTE.value,
                    now,
                    existing['StagingID']
                ))
                
                conn.commit()
                return {"success": True, "action": "updated", "staging_id": existing['StagingID']}
            
            else:
                cursor.execute("""
                    INSERT INTO CRM_Staging_Cuentas (
                        ConectorID, ExternalID, RazonSocial, NombreComercial, RFC,
                        Industria, SitioWeb, EmailPrincipal, TelefonoPrincipal, Direccion,
                        DatosExternosJSON, DireccionSync, EstadoSync, FechaExterna,
                        Intentos, CreatedAt, UpdatedAt
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    conector_id,
                    cuenta.external_id,
                    cuenta.razon_social,
                    cuenta.nombre_comercial,
                    cuenta.rfc,
                    cuenta.industria,
                    cuenta.sitio_web,
                    cuenta.email_principal,
                    cuenta.telefono_principal,
                    cuenta.direccion,
                    datos_json,
                    direccion.value,
                    SyncStatus.PENDIENTE.value,
                    cuenta.fecha_modificacion,
                    0,
                    now,
                    now
                ))
                
                cursor.execute("SELECT SCOPE_IDENTITY() as id")
                new_id = cursor.fetchone()['id']
                
                conn.commit()
                return {"success": True, "action": "inserted", "staging_id": int(new_id)}
                
        except Exception as e:
            conn.rollback()
            logger.error(f"[Staging] Error upsert cuenta: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def bulk_upsert_cuentas(
        self,
        conector_id: int,
        cuentas: List[CuentaExterna],
        direccion: SyncDirection = SyncDirection.ENTRANTE
    ) -> Dict[str, Any]:
        """Inserta/actualiza múltiples cuentas en staging"""
        inserted = 0
        updated = 0
        errors = 0
        error_messages = []
        
        for cuenta in cuentas:
            result = self.upsert_staging_cuenta(conector_id, cuenta, direccion)
            if result['success']:
                if result['action'] == 'inserted':
                    inserted += 1
                else:
                    updated += 1
            else:
                errors += 1
                error_messages.append(f"{cuenta.external_id}: {result.get('error', 'Unknown')}")
        
        logger.info(f"[Staging] Bulk cuentas: {inserted} insertados, {updated} actualizados, {errors} errores")
        
        return {
            "success": errors == 0,
            "inserted": inserted,
            "updated": updated,
            "errors": errors,
            "total": len(cuentas),
            "error_messages": error_messages[:10]
        }
    
    # ============================================================
    # CONSULTAS
    # ============================================================
    
    def get_staging_stats(self, conector_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas de staging para un conector"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            stats = {"leads": {}, "oportunidades": {}, "cuentas": {}}
            
            # Leads
            cursor.execute("""
                SELECT EstadoSync, COUNT(*) as total
                FROM CRM_Staging_Leads
                WHERE ConectorID = %s
                GROUP BY EstadoSync
            """, (conector_id,))
            for row in cursor.fetchall():
                stats["leads"][row['EstadoSync'] or 'NULL'] = row['total']
            
            # Oportunidades
            cursor.execute("""
                SELECT EstadoSync, COUNT(*) as total
                FROM CRM_Staging_Oportunidades
                WHERE ConectorID = %s
                GROUP BY EstadoSync
            """, (conector_id,))
            for row in cursor.fetchall():
                stats["oportunidades"][row['EstadoSync'] or 'NULL'] = row['total']
            
            # Cuentas
            cursor.execute("""
                SELECT EstadoSync, COUNT(*) as total
                FROM CRM_Staging_Cuentas
                WHERE ConectorID = %s
                GROUP BY EstadoSync
            """, (conector_id,))
            for row in cursor.fetchall():
                stats["cuentas"][row['EstadoSync'] or 'NULL'] = row['total']
            
            return stats
            
        except Exception as e:
            logger.error(f"[Staging] Error getting stats: {e}")
            return {}
        finally:
            conn.close()
    
    def get_pending_leads(self, conector_id: int, limit: int = 100) -> List[Dict]:
        """Obtiene leads pendientes de procesar"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute("""
                SELECT TOP %s * 
                FROM CRM_Staging_Leads
                WHERE ConectorID = %s AND EstadoSync = 'PENDIENTE'
                ORDER BY CreatedAt ASC
            """, (limit, conector_id))
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"[Staging] Error getting pending leads: {e}")
            return []
        finally:
            conn.close()
    
    def mark_lead_processed(
        self,
        staging_id: int,
        local_lead_id: str,
        status: SyncStatus = SyncStatus.SINCRONIZADO,
        error_msg: str = None
    ) -> bool:
        """Marca un lead de staging como procesado"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE CRM_Staging_Leads SET
                    LocalLeadID = %s,
                    EstadoSync = %s,
                    FechaProcesado = %s,
                    FechaLocal = %s,
                    MensajeError = %s,
                    Intentos = Intentos + 1
                WHERE StagingID = %s
            """, (
                local_lead_id,
                status.value,
                self._now(),
                self._now() if status == SyncStatus.SINCRONIZADO else None,
                error_msg,
                staging_id
            ))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"[Staging] Error marking lead processed: {e}")
            return False
        finally:
            conn.close()
