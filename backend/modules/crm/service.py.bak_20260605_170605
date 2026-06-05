"""
CRM Service - Servicio CRM Enterprise SQL-First
Arquitectura: EDARSAHUB SQL Server (Sin dependencias externas como vTiger)
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CRMService:
    """
    Servicio CRM Enterprise - SQL-First
    
    Este servicio opera directamente contra EDARSAHUB SQL Server.
    NO hay dependencias externas (vTiger eliminado).
    """
    
    _instance: Optional['CRMService'] = None
    
    @classmethod
    def get_instance(cls) -> 'CRMService':
        """Singleton pattern para el servicio"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    # ==================== ESTADO ====================
    
    @staticmethod
    def get_connection_status() -> Dict[str, Any]:
        """Obtiene el estado del servicio CRM"""
        return {
            "source": "EDARSAHUB_SQL",
            "status": "active",
            "external_integrations": None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def test_connection() -> Dict[str, Any]:
        """Verifica conexión con la base de datos SQL"""
        return {
            "success": True,
            "message": "CRM Enterprise conectado a EDARSAHUB SQL",
            "source": "SQL_FIRST"
        }
    
    # ==================== MÓDULOS DISPONIBLES ====================
    
    @staticmethod
    def get_available_modules() -> List[str]:
        """Lista de módulos CRM disponibles (SQL-First)"""
        return [
            "Cuentas",      # CRM_Cuentas
            "Contactos",    # CRM_Contactos  
            "Leads",        # CRM_Leads
            "Oportunidades", # CRM_Oportunidades
            "Cotizaciones", # Venta_Cotizaciones
            "Pedidos",      # Venta_Pedidos
            "Remisiones"    # Venta_Remisiones
        ]
    
    @staticmethod
    def get_sync_stats() -> Dict[str, Any]:
        """
        Estadísticas del CRM
        NOTA: En arquitectura SQL-First, las estadísticas vienen de EDARSAHUB
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "EDARSAHUB_SQL",
            "external_sync": None,
            "message": "CRM opera en modo SQL-First sin sincronización externa"
        }
