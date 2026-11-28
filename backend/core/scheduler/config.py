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
        notif_enabled = os.environ.get("SCHEDULER_NOTIFICATIONS_ENABLED", "false").lower() == "true"
        
        # Catalogo Ampliado - alertas documentales
        catalogo_alertas_interval = int(os.environ.get("SCHEDULER_CATALOGO_AMPLIADO_ALERTAS_INTERVAL_SECONDS", "3600"))
        catalogo_alertas_enabled = os.environ.get("SCHEDULER_CATALOGO_AMPLIADO_ALERTAS_ENABLED", "true").lower() == "true"
        if catalogo_alertas_interval < 60:
            raise ValueError("SCHEDULER_CATALOGO_AMPLIADO_ALERTAS_INTERVAL_SECONDS must be >= 60")

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
        
        # Economía WorldClass - sincronización canónica
        economia_sync_interval = int(
            os.environ.get(
                "SCHEDULER_ECONOMIA_SYNC_INTERVAL_SECONDS",
                "86400",
            )
        )
        economia_sync_enabled = (
            os.environ.get(
                "SCHEDULER_ECONOMIA_SYNC_ENABLED",
                "false",
            ).lower()
            == "true"
        )

        # NetPay Sync Diario (posterior al corte operativo)
        netpay_sync_cron = os.environ.get("SCHEDULER_NETPAY_SYNC_CRON", "30 6 * * *")  # 06:30 diario
        netpay_sync_enabled = os.environ.get("SCHEDULER_NETPAY_SYNC_ENABLED", "true").lower() == "true"
        
        # SYNC Compras integral (inventarios, requisiciones, almacenes, existencias, movimientos, pedidos, ordenes, recepciones)
        sync_compras_interval = int(os.environ.get("SCHEDULER_SYNC_COMPRAS_INTERVAL_SECONDS", "1800"))  # 30 minutos
        sync_compras_enabled = os.environ.get("SCHEDULER_SYNC_COMPRAS_ENABLED", "true").lower() == "true"

        # Notificador de Excepciones Críticas (WhatsApp + Email) — parametrizable, sin hardcode
        alertas_exc_interval = int(os.environ.get("SCHEDULER_ALERTAS_EXCEPCIONES_INTERVAL_SECONDS", "3600"))  # 1 hora
        alertas_exc_enabled = os.environ.get("SCHEDULER_ALERTAS_EXCEPCIONES_ENABLED", "true").lower() == "true"

        # Resumen Diario Ejecutivo de Excepciones (correo matutino)
        resumen_diario_exc_cron = os.environ.get("SCHEDULER_RESUMEN_DIARIO_EXC_CRON", "0 8 * * *")  # 08:00 diario
        resumen_diario_exc_enabled = os.environ.get("SCHEDULER_RESUMEN_DIARIO_EXC_ENABLED", "true").lower() == "true"

        # BOS Direccion: snapshot vivo recurrente (default cada hora)
        bos_direction_status_interval = int(os.environ.get("SCHEDULER_BOS_DIRECTION_STATUS_INTERVAL_SECONDS", "3600"))
        bos_direction_status_enabled = os.environ.get("SCHEDULER_BOS_DIRECTION_STATUS_ENABLED", "true").lower() == "true"
        if bos_direction_status_interval < 60:
            raise ValueError("SCHEDULER_BOS_DIRECTION_STATUS_INTERVAL_SECONDS must be >= 60")
        
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
            "catalogo_ampliado_alertas": JobConfig(
                job_id="catalogo_ampliado_alertas",
                job_name="Catalogo Ampliado - Alertas",
                description="Planifica alertas documentales y materializa tareas canonicas; canales externos permanecen fail-closed",
                enabled=catalogo_alertas_enabled,
                interval_seconds=catalogo_alertas_interval,
                batch_size=50,
                timeout_seconds=300
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
            # Compras: sincronización integral canónica
            "sync_compras": JobConfig(
                job_id="sync_compras",
                job_name="SYNC Compras Integral",
                description="Sincroniza compras integralmente: inventarios, requisiciones, almacenes, existencias, movimientos, pedidos, ordenes y recepciones. Debe ejecutarse como grupo para evitar dependencias incompletas.",
                enabled=sync_compras_enabled,
                interval_seconds=sync_compras_interval,
                batch_size=2000,
                timeout_seconds=1800,
            ),
            # CxP: Sincronización de Cuentas por Pagar a tabla canónica (nocturno 04:30)
            "sync_cxp_facturas": JobConfig(
                job_id="sync_cxp_facturas",
                job_name="SYNC Cuentas por Pagar",
                description="Sincroniza facturas pendientes (SoftRestaurant + MPRO) hacia la tabla canónica dbo.Finanzas_CxP_Sync (NO-LIVE)",
                enabled=os.environ.get("SCHEDULER_SYNC_CXP_ENABLED", "true").lower() == "true",
                cron_expression=os.environ.get("SCHEDULER_SYNC_CXP_CRON", "30 4 * * *"),
                interval_seconds=86400,
                batch_size=2000,
                timeout_seconds=600,
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
            ),
            # Economía WorldClass: sincronización de indicadores
            "economia_sync": JobConfig(
                job_id="economia_sync",
                job_name="Economía - Sync Indicadores",
                description="Sincroniza series económicas activas mediante proveedores canónicos",
                enabled=economia_sync_enabled,
                interval_seconds=economia_sync_interval,
                batch_size=500,
                timeout_seconds=1800
            ),
            # Inteligencia Comercial: Sincronización de ventas desde POS
            # NetPay: Sincronización diaria de reportes conciliables
            "netpay_sync_diario": JobConfig(
                job_id="netpay_sync_diario",
                job_name="NetPay - Sync Diario",
                description="Ejecuta diariamente los reportes NetPay DETALLE_TRANSACCIONES y DETALLE_DEPOSITOS_MOVIMIENTOS para el día anterior completo",
                enabled=netpay_sync_enabled,
                cron_expression=netpay_sync_cron,
                interval_seconds=86400,
                batch_size=2,
                timeout_seconds=1800
            ),
            "inteligencia_comercial_sync": JobConfig(
                job_id="inteligencia_comercial_sync",
                job_name="Inteligencia Comercial - Sync Sales",
                description="Extrae ventas de SoftRestaurant/MPRO y las consolida en Sync_Sales y KPIs diarios (cada hora)",
                enabled=os.environ.get("SCHEDULER_INTELIGENCIA_SYNC_ENABLED", "true").lower() == "true",
                cron_expression="0 * * * *",  # Cada hora en el minuto 0
                interval_seconds=3600,  # Fallback: 1 hora
                batch_size=500,
                timeout_seconds=600  # 10 minutos max
            ),
            # Notificador de Excepciones Críticas (WhatsApp Twilio + Email SMTP)
            "alertas_excepciones_notifier": JobConfig(
                job_id="alertas_excepciones_notifier",
                job_name="Notificador Excepciones Críticas",
                description="Revisa excepciones estratégicas (rentabilidad, compras sin detalle) y notifica las nuevas por WhatsApp y Email. Destinatarios/severidades/intervalo desde .env.",
                enabled=alertas_exc_enabled,
                interval_seconds=alertas_exc_interval,
                batch_size=500,
                timeout_seconds=300
            ),
            # Resumen Diario Ejecutivo de Excepciones (correo matutino)
            "resumen_diario_excepciones": JobConfig(
                job_id="resumen_diario_excepciones",
                job_name="Resumen Diario de Excepciones",
                description="Envía cada mañana un correo a dirección con el conteo de excepciones por unidad y severidad (cron parametrizable).",
                enabled=resumen_diario_exc_enabled,
                cron_expression=resumen_diario_exc_cron,
                interval_seconds=86400,
                batch_size=1000,
                timeout_seconds=300
            ),
            # BOS Direccion: status vivo basado en evidencia certificada
            "bos_direction_status": JobConfig(
                job_id="bos_direction_status",
                job_name="BOS Direccion - Status Vivo",
                description="Genera snapshot BOS de Direccion, historico inmutable y latest desde evidencia certificada.",
                enabled=bos_direction_status_enabled,
                interval_seconds=bos_direction_status_interval,
                batch_size=1,
                timeout_seconds=300,
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300
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
