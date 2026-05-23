"""
EDARSA HUB - CRM Sync Engine
============================
Motor de sincronización que orquesta la importación de datos
desde CRMs externos hacia las tablas de staging y producción.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import json

from .base_connector import BaseCRMConnector, SyncResult, SyncDirection, SyncStatus
from .staging_service import StagingService
from .vtiger_connector import VTigerConnector

logger = logging.getLogger(__name__)


@dataclass
class SyncJob:
    """Representa un trabajo de sincronización"""
    conector_id: int
    empresa_id: str
    tipo_conector: str
    entidades: List[str]  # ['leads', 'oportunidades', 'cuentas']
    desde_fecha: Optional[datetime] = None


class SyncEngine:
    """
    Motor de sincronización CRM.
    Coordina la extracción desde CRMs externos y carga a staging.
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.staging_service = StagingService(db_config)
        self._connectors: Dict[int, BaseCRMConnector] = {}
    
    def _get_connector(self, conector_id: int, config: Dict[str, Any]) -> Optional[BaseCRMConnector]:
        """Obtiene o crea instancia de conector"""
        tipo = config.get('tipo_conector', '').upper()
        
        if tipo == 'VTIGER':
            return VTigerConnector(conector_id, config)
        # Agregar más conectores aquí: SALESFORCE, HUBSPOT, etc.
        
        logger.error(f"[SyncEngine] Tipo de conector no soportado: {tipo}")
        return None
    
    def run_sync(self, job: SyncJob, config: Dict[str, Any]) -> SyncResult:
        """
        Ejecuta sincronización completa para un conector
        
        Args:
            job: Configuración del trabajo
            config: Configuración del conector (URL, credenciales, etc.)
            
        Returns:
            SyncResult con estadísticas
        """
        start_time = datetime.now()
        result = SyncResult(success=True)
        
        # Obtener conector
        connector = self._get_connector(job.conector_id, {
            'tipo_conector': job.tipo_conector,
            **config
        })
        
        if not connector:
            result.success = False
            result.errores.append(f"No se pudo crear conector tipo: {job.tipo_conector}")
            return result
        
        # Conectar
        if not connector.connect():
            result.success = False
            result.errores.append(f"Error de conexión: {connector.last_error}")
            return result
        
        logger.info(f"[SyncEngine] Iniciando sync para conector {job.conector_id}")
        
        try:
            # Sincronizar cada entidad solicitada
            for entidad in job.entidades:
                if entidad == 'leads':
                    self._sync_leads(connector, job, result)
                elif entidad == 'oportunidades':
                    self._sync_oportunidades(connector, job, result)
                elif entidad == 'cuentas':
                    self._sync_cuentas(connector, job, result)
            
        except Exception as e:
            logger.error(f"[SyncEngine] Error durante sync: {e}")
            result.errores.append(str(e))
            result.success = False
        
        finally:
            connector.disconnect()
        
        result.duracion_segundos = int((datetime.now() - start_time).total_seconds())
        
        logger.info(
            f"[SyncEngine] Sync completado: "
            f"{result.registros_creados} creados, "
            f"{result.registros_actualizados} actualizados, "
            f"{result.registros_error} errores "
            f"en {result.duracion_segundos}s"
        )
        
        return result
    
    def _sync_leads(self, connector: BaseCRMConnector, job: SyncJob, result: SyncResult):
        """Sincroniza leads desde el CRM externo"""
        logger.info(f"[SyncEngine] Extrayendo leads...")
        
        leads = connector.pull_leads(since=job.desde_fecha)
        result.registros_procesados += len(leads)
        
        if not leads:
            logger.info("[SyncEngine] No hay leads para sincronizar")
            return
        
        # Insertar en staging
        staging_result = self.staging_service.bulk_upsert_leads(
            conector_id=job.conector_id,
            leads=leads,
            direccion=SyncDirection.ENTRANTE
        )
        
        result.registros_creados += staging_result['inserted']
        result.registros_actualizados += staging_result['updated']
        result.registros_error += staging_result['errors']
        result.errores.extend(staging_result.get('error_messages', []))
    
    def _sync_oportunidades(self, connector: BaseCRMConnector, job: SyncJob, result: SyncResult):
        """Sincroniza oportunidades desde el CRM externo"""
        logger.info(f"[SyncEngine] Extrayendo oportunidades...")
        
        opps = connector.pull_opportunities(since=job.desde_fecha)
        result.registros_procesados += len(opps)
        
        if not opps:
            logger.info("[SyncEngine] No hay oportunidades para sincronizar")
            return
        
        staging_result = self.staging_service.bulk_upsert_oportunidades(
            conector_id=job.conector_id,
            opps=opps,
            direccion=SyncDirection.ENTRANTE
        )
        
        result.registros_creados += staging_result['inserted']
        result.registros_actualizados += staging_result['updated']
        result.registros_error += staging_result['errors']
        result.errores.extend(staging_result.get('error_messages', []))
    
    def _sync_cuentas(self, connector: BaseCRMConnector, job: SyncJob, result: SyncResult):
        """Sincroniza cuentas desde el CRM externo"""
        logger.info(f"[SyncEngine] Extrayendo cuentas...")
        
        cuentas = connector.pull_accounts(since=job.desde_fecha)
        result.registros_procesados += len(cuentas)
        
        if not cuentas:
            logger.info("[SyncEngine] No hay cuentas para sincronizar")
            return
        
        staging_result = self.staging_service.bulk_upsert_cuentas(
            conector_id=job.conector_id,
            cuentas=cuentas,
            direccion=SyncDirection.ENTRANTE
        )
        
        result.registros_creados += staging_result['inserted']
        result.registros_actualizados += staging_result['updated']
        result.registros_error += staging_result['errors']
        result.errores.extend(staging_result.get('error_messages', []))
    
    def test_connector(self, tipo: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prueba conexión con un conector
        
        Args:
            tipo: Tipo de conector (VTIGER, SALESFORCE, etc.)
            config: Configuración de conexión
            
        Returns:
            Resultado de la prueba
        """
        connector = self._get_connector(0, {'tipo_conector': tipo, **config})
        
        if not connector:
            return {"success": False, "error": f"Tipo no soportado: {tipo}"}
        
        success, error = connector.test_connection()
        
        return {
            "success": success,
            "error": error,
            "tipo": tipo,
            "mensaje": "Conexión exitosa" if success else f"Error: {error}"
        }
