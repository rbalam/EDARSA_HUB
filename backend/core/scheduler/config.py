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
