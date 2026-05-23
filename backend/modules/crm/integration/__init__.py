"""
EDARSA HUB - CRM Integration Framework
======================================
Framework de integración para conectar CRMs externos con el CRM nativo.
"""

from .base_connector import (
    BaseCRMConnector,
    SyncDirection,
    SyncStatus,
    ConnectionStatus,
    SyncResult,
    LeadExterno,
    OportunidadExterna,
    CuentaExterna
)
from .vtiger_connector import VTigerConnector
from .staging_service import StagingService
from .sync_engine import SyncEngine, SyncJob

__all__ = [
    'BaseCRMConnector',
    'SyncDirection',
    'SyncStatus', 
    'ConnectionStatus',
    'SyncResult',
    'LeadExterno',
    'OportunidadExterna',
    'CuentaExterna',
    'VTigerConnector',
    'StagingService',
    'SyncEngine',
    'SyncJob'
]
