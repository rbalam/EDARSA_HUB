"""
EDARSA HUB - Scheduler Configuration
====================================
Configuración central del scheduler y jobs.
"""

from typing import Optional, Dict
from pydantic import BaseModel
import os


class JobConfig(BaseModel):
    """Configuración de un job individual."""
    job_id: str
    job_name: str
    description: str
    enabled: bool = True
    interval_seconds: int = 300  # 5 minutos default
    cron_expression: Optional[str] = None  # Alternativa a interval
    max_instances: int = 1
    coalesce: bool = True
    misfire_grace_time: int = 60  # segundos
    timeout_seconds: int = 300  # 5 minutos max ejecución
    batch_size: int = 50
    
    class Config:
        extra = "allow"


class SchedulerConfig(BaseModel):
    """Configuración global del scheduler."""
    enabled: bool = True
    timezone: str = "America/Mexico_City"
    
    # Jobs configurados
    jobs: Dict[str, JobConfig] = {}
    
    # Lock settings
    lock_timeout_seconds: int = 600  # 10 minutos
    lock_heartbeat_interval: int = 30  # segundos
    
    # Logging
    log_retention_days: int = 30
    
    @classmethod
    def from_env(cls) -> "SchedulerConfig":
        """Crea configuración desde variables de entorno."""
        enabled = os.environ.get("SCHEDULER_ENABLED", "true").lower() == "true"
        timezone = os.environ.get("SCHEDULER_TIMEZONE", "America/Mexico_City")
        
        # SLA Job config
        sla_interval = int(os.environ.get("SCHEDULER_SLA_INTERVAL_SECONDS", "300"))
        sla_enabled = os.environ.get("SCHEDULER_SLA_ENABLED", "true").lower() == "true"
        
        # Notifications Job config
        notif_interval = int(os.environ.get("SCHEDULER_NOTIFICATIONS_INTERVAL_SECONDS", "120"))
        notif_enabled = os.environ.get("SCHEDULER_NOTIFICATIONS_ENABLED", "true").lower() == "true"
        
        # Auditorías Programadas Job config
        audit_interval = int(os.environ.get("SCHEDULER_AUDITORIAS_INTERVAL_SECONDS", "3600"))  # 1 hora
        audit_enabled = os.environ.get("SCHEDULER_AUDITORIAS_ENABLED", "true").lower() == "true"
        
        # Pedidos Detector Job config (Automatización Operativa)
        pedidos_interval = int(os.environ.get("SCHEDULER_PEDIDOS_INTERVAL_SECONDS", "300"))  # 5 minutos
        pedidos_enabled = os.environ.get("SCHEDULER_PEDIDOS_ENABLED", "true").lower() == "true"
        
        # Inventarios Detector Job config (Detección automática de inventarios)
        inventarios_interval = int(os.environ.get("SCHEDULER_INVENTARIOS_INTERVAL_SECONDS", "600"))  # 10 minutos
        inventarios_enabled = os.environ.get("SCHEDULER_INVENTARIOS_ENABLED", "true").lower() == "true"
        
        # SYNC-S KPIs Comerciales (cada 15 minutos) - MACROFASE 2
        sync_s_interval = int(os.environ.get("SCHEDULER_SYNC_S_INTERVAL_SECONDS", "900"))  # 15 minutos
        sync_s_enabled = os.environ.get("SCHEDULER_SYNC_S_ENABLED", "true").lower() == "true"
        
        # SYNC-N KPIs Comerciales (nocturno 03:00) - MACROFASE 2
        sync_n_cron = os.environ.get("SCHEDULER_SYNC_N_CRON", "0 3 * * *")  # 03:00 diario
        sync_n_enabled = os.environ.get("SCHEDULER_SYNC_N_ENABLED", "true").lower() == "true"
        
        # SYNC Control de Ingresos (cada 15 minutos) - FASE 2.6
        sync_ingresos_interval = int(os.environ.get("SCHEDULER_SYNC_INGRESOS_INTERVAL_SECONDS", "900"))  # 15 minutos
        sync_ingresos_enabled = os.environ.get("SCHEDULER_SYNC_INGRESOS_ENABLED", "true").lower() == "true"
        
        # SYNC Propinas TPV (cada 15 minutos) - FASE 3.6
        sync_propinas_interval = int(os.environ.get("SCHEDULER_SYNC_PROPINAS_INTERVAL_SECONDS", "900"))  # 15 minutos
        sync_propinas_enabled = os.environ.get("SCHEDULER_SYNC_PROPINAS_ENABLED", "true").lower() == "true"
        
        # SYNC Comercial V2 (cada 15 minutos) - SUBFASE 4 Comercial Blindado V2
        sync_comercial_v2_interval = int(os.environ.get("SCHEDULER_SYNC_COMERCIAL_V2_INTERVAL_SECONDS", "900"))  # 15 minutos
        sync_comercial_v2_enabled = os.environ.get("SCHEDULER_SYNC_COMERCIAL_V2_ENABLED", "true").lower() == "true"
        
        # SYNC Comercial Abiertas V2 (cada 5 minutos) - P0 Ventas del día en curso
        sync_comercial_abiertas_v2_interval = int(os.environ.get("SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_INTERVAL_SECONDS", "300"))  # 5 minutos
        sync_comercial_abiertas_v2_enabled = os.environ.get("SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED", "true").lower() == "true"
        
        # Cava de Socios Monthly (primer día del mes a las 9:00 AM)
        cava_monthly_cron = os.environ.get("SCHEDULER_CAVA_MONTHLY_CRON", "0 9 1 * *")  # 9:00 AM día 1 de cada mes
        cava_monthly_enabled = os.environ.get("SCHEDULER_CAVA_MONTHLY_ENABLED", "true").lower() == "true"
        
        # CRM Sync (sincronización con CRMs externos cada 30 min)
        crm_sync_interval = int(os.environ.get("SCHEDULER_CRM_SYNC_INTERVAL_SECONDS", "1800"))  # 30 minutos
        crm_sync_enabled = os.environ.get("SCHEDULER_CRM_SYNC_ENABLED", "true").lower() == "true"
        
        # CRM SLA Check (verificación de SLAs cada hora)
        crm_sla_interval = int(os.environ.get("SCHEDULER_CRM_SLA_INTERVAL_SECONDS", "3600"))  # 1 hora
        crm_sla_enabled = os.environ.get("SCHEDULER_CRM_SLA_ENABLED", "true").lower() == "true"
        
        # CRM Actividades Vencidas (cada 15 min)
        crm_actividades_interval = int(os.environ.get("SCHEDULER_CRM_ACTIVIDADES_INTERVAL_SECONDS", "900"))  # 15 min
        crm_actividades_enabled = os.environ.get("SCHEDULER_CRM_ACTIVIDADES_ENABLED", "true").lower() == "true"
        
        # Vtiger Sync (sincronización con Vtiger CRM cada 15 min)
        vtiger_sync_interval = int(os.environ.get("SCHEDULER_VTIGER_SYNC_INTERVAL_SECONDS", "900"))  # 15 minutos
        vtiger_sync_enabled = os.environ.get("SCHEDULER_VTIGER_SYNC_ENABLED", "true").lower() == "true"
        
        jobs = {
            "sla_processor": JobConfig(
                job_id="sla_processor",
                job_name="SLA Processor",
                description="Procesa estados SLA, alertas 80%, vencimientos 100%, escalamientos 150%",
                enabled=sla_enabled,
                interval_seconds=sla_interval,
                batch_size=100,
                timeout_seconds=300
            ),
            "notifications_dispatcher": JobConfig(
                job_id="notifications_dispatcher",
                job_name="Notifications Dispatcher",
                description="Despacha notificaciones pendientes de la cola",
                enabled=notif_enabled,
                interval_seconds=notif_interval,
                batch_size=50,
                timeout_seconds=180
            ),
            "auditorias_scheduler": JobConfig(
                job_id="auditorias_scheduler",
                job_name="Auditorias Scheduler",
                description="Ejecuta auditorías programadas cuya fecha de ejecución ha llegado",
                enabled=audit_enabled,
                interval_seconds=audit_interval,
                batch_size=20,
                timeout_seconds=600
            ),
            "pedidos_detector": JobConfig(
                job_id="pedidos_detector",
                job_name="Pedidos Detector",
                description="Detecta pedidos nuevos en MPro/Soft y dispara automatización operativa de compras",
                enabled=pedidos_enabled,
                interval_seconds=pedidos_interval,
                batch_size=50,
                timeout_seconds=300
            ),
            "inventarios_detector": JobConfig(
                job_id="inventarios_detector",
                job_name="Inventarios Detector",
                description="Detecta nuevos inventarios físicos en sistemas origen y dispara análisis automático",
                enabled=inventarios_enabled,
                interval_seconds=inventarios_interval,
                batch_size=50,
                timeout_seconds=600
            ),
            # MACROFASE 2: Jobs de sincronización KPIs
            "sync_short_comercial": JobConfig(
                job_id="sync_short_comercial",
                job_name="SYNC-S KPIs Comerciales",
                description="Sincronización corta de KPIs comerciales - ventana 48h, UPSERT idempotente",
                enabled=sync_s_enabled,
                interval_seconds=sync_s_interval,
                batch_size=100,
                timeout_seconds=600
            ),
            "sync_nightly_comercial": JobConfig(
                job_id="sync_nightly_comercial",
                job_name="SYNC-N KPIs Comerciales",
                description="Sincronización nocturna de KPIs comerciales - ventana 7 días, cierre de períodos",
                enabled=sync_n_enabled,
                cron_expression=sync_n_cron,
                interval_seconds=3600,  # Fallback si no hay cron
                batch_size=200,
                timeout_seconds=1800  # 30 minutos max
            ),
            # FASE 2.6: Sincronización Control de Ingresos
            "sync_ingresos_incremental": JobConfig(
                job_id="sync_ingresos_incremental",
                job_name="SYNC Control de Ingresos",
                description="Sincronización incremental de cortes de caja desde SoftRestaurant y MPRO hacia EDARSAHUB",
                enabled=sync_ingresos_enabled,
                interval_seconds=sync_ingresos_interval,
                batch_size=100,
                timeout_seconds=600  # 10 minutos max
            ),
            # FASE 3.6: Sincronización Propinas TPV
            "sync_propinas_tpv_incremental": JobConfig(
                job_id="sync_propinas_tpv_incremental",
                job_name="SYNC Propinas TPV",
                description="Sincronización incremental de propinas TPV desde SoftRestaurant y MPRO hacia EDARSAHUB",
                enabled=sync_propinas_enabled,
                interval_seconds=sync_propinas_interval,
                batch_size=100,
                timeout_seconds=600  # 10 minutos max
            ),
            # SUBFASE 4: Sincronización Comercial V2 (Tablero Ejecutivo Blindado)
            "sync_comercial_v2": JobConfig(
                job_id="sync_comercial_v2",
                job_name="SYNC Comercial V2",
                description="Sincronización incremental de KPIs comerciales V2 desde SoftRestaurant y MPRO hacia EDARSAHUB",
                enabled=sync_comercial_v2_enabled,
                interval_seconds=sync_comercial_v2_interval,
                batch_size=100,
                timeout_seconds=600  # 10 minutos max
            ),
            # P0: Sincronización Ventas Abiertas V2 (cada 5 minutos)
            "sync_comercial_abiertas_v2": JobConfig(
                job_id="sync_comercial_abiertas_v2",
                job_name="SYNC Ventas Abiertas V2",
                description="Sincronización de ventas del día en curso (abiertas) desde SoftRestaurant y MPRO hacia EDARSAHUB cada 5 minutos",
                enabled=sync_comercial_abiertas_v2_enabled,
                interval_seconds=sync_comercial_abiertas_v2_interval,
                batch_size=10,
                timeout_seconds=300  # 5 minutos max
            ),
            # Cava de Socios: Envío mensual de estados de cuenta
            "cava_socios_monthly": JobConfig(
                job_id="cava_socios_monthly",
                job_name="Cava Socios - Estado de Cuenta Mensual",
                description="Envío automático mensual de estados de cuenta por email a socios activos (día 1 de cada mes a las 9:00 AM)",
                enabled=cava_monthly_enabled,
                cron_expression=cava_monthly_cron,
                interval_seconds=86400,  # Fallback 24h si no hay cron
                batch_size=100,
                timeout_seconds=1800  # 30 minutos max (envío masivo)
            ),
            # CRM: Sincronización con CRMs externos
            "crm_sync": JobConfig(
                job_id="crm_sync",
                job_name="CRM - Sincronización Externa",
                description="Tareas automáticas del CRM Enterprise (SQL-First) cada 30 minutos",
                enabled=crm_sync_enabled,
                interval_seconds=crm_sync_interval,
                batch_size=100,
                timeout_seconds=600  # 10 minutos max
            ),
            # CRM: Verificación de SLAs
            "crm_sla_check": JobConfig(
                job_id="crm_sla_check",
                job_name="CRM - Verificación SLA",
                description="Verificación de SLAs de oportunidades y generación de alertas (cada hora)",
                enabled=crm_sla_enabled,
                interval_seconds=crm_sla_interval,
                batch_size=500,
                timeout_seconds=300
            ),
            # CRM: Actividades vencidas
            "crm_actividades_vencidas": JobConfig(
                job_id="crm_actividades_vencidas",
                job_name="CRM - Actividades Vencidas",
                description="Verificación de actividades vencidas y envío de recordatorios (cada 15 min)",
                enabled=crm_actividades_enabled,
                interval_seconds=crm_actividades_interval,
                batch_size=200,
                timeout_seconds=180
            ),
            # Vtiger: Sincronización bidireccional
            "vtiger_sync": JobConfig(
                job_id="vtiger_sync",
                job_name="Vtiger CRM - Sincronización",
                description="Sincronización bidireccional con Vtiger CRM (Leads, Contactos, Cuentas, Oportunidades) cada 15 minutos",
                enabled=vtiger_sync_enabled,
                interval_seconds=vtiger_sync_interval,
                batch_size=500,
                timeout_seconds=300  # 5 minutos max
            )
        }
        
        return cls(
            enabled=enabled,
            timezone=timezone,
            jobs=jobs
        )


# Configuración default singleton
_config: Optional[SchedulerConfig] = None


def get_scheduler_config() -> SchedulerConfig:
    """Obtiene la configuración del scheduler."""
    global _config
    if _config is None:
        _config = SchedulerConfig.from_env()
    return _config


def reload_scheduler_config():
    """Recarga la configuración."""
    global _config
    _config = None
    return get_scheduler_config()
