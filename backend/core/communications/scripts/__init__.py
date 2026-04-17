"""
EDARSA HUB - Notification System Initialization
===============================================
Subfase 2B.5 - Script de inicialización de colecciones e índices.

Este script es idempotente - puede ejecutarse múltiples veces sin problemas.

Colecciones:
- notification_config
- notification_provider_config
- notification_templates
- notification_queue
- notification_log

Uso:
    python -m core.communications.scripts.init_notifications
"""

import asyncio
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)


# =============================================================================
# ÍNDICES
# =============================================================================

INDEXES = {
    "notification_config": [
        {
            "keys": [("canal", 1), ("modulo", 1), ("evento", 1), ("activo", 1)],
            "unique": True,
            "name": "idx_config_lookup"
        }
    ],
    "notification_provider_config": [
        {
            "keys": [("canal", 1), ("provider", 1)],
            "unique": True,
            "name": "idx_provider_lookup"
        },
        {
            "keys": [("canal", 1), ("activo", 1)],
            "name": "idx_active_provider"
        }
    ],
    "notification_templates": [
        {
            "keys": [("canal", 1), ("codigo", 1), ("activo", 1)],
            "unique": False,
            "name": "idx_template_lookup"
        },
        {
            "keys": [("codigo", 1)],
            "unique": True,
            "name": "idx_template_code"
        }
    ],
    "notification_queue": [
        {
            "keys": [("estado", 1), ("proximo_intento", 1)],
            "name": "idx_queue_pending"
        },
        {
            "keys": [("workflow_id", 1), ("estado", 1)],
            "name": "idx_queue_workflow"
        },
        {
            "keys": [("referencia_id", 1), ("estado", 1)],
            "name": "idx_queue_referencia"
        },
        {
            "keys": [("created_at", 1)],
            "name": "idx_queue_created",
            "expireAfterSeconds": 604800  # 7 días TTL
        }
    ],
    "notification_log": [
        {
            "keys": [("workflow_id", 1), ("fecha_intento", -1)],
            "name": "idx_log_workflow"
        },
        {
            "keys": [("referencia_id", 1), ("fecha_intento", -1)],
            "name": "idx_log_referencia"
        },
        {
            "keys": [("destinatario", 1), ("fecha_intento", -1)],
            "name": "idx_log_destinatario"
        },
        {
            "keys": [("evento_negocio", 1), ("fecha_intento", -1)],
            "name": "idx_log_evento"
        },
        {
            "keys": [("estado_envio", 1), ("fecha_intento", -1)],
            "name": "idx_log_estado"
        },
        {
            "keys": [
                ("evento_negocio", 1),
                ("referencia_id", 1),
                ("workflow_id", 1),
                ("destinatario", 1),
                ("template_codigo", 1),
                ("fecha_intento", -1)
            ],
            "name": "idx_log_dedup"
        }
    ]
}


# =============================================================================
# DATOS INICIALES
# =============================================================================

DEFAULT_CONFIGS = [
    {
        "id": "cfg_asignacion_tarea",
        "canal": "whatsapp",
        "modulo": "inventarios",
        "evento": "ASIGNACION_TAREA",
        "activo": True,
        "provider": "mock",
        "modo_envio": "mock",
        "template_codigo": "inventarios_asignacion_tarea",
        "enviar_a_responsable": True,
        "enviar_a_supervisor": False,
        "enviar_a_gerente": False,
        "permite_reintentos": True,
        "max_reintentos": 3,
        "ventana_duplicidad_minutos": 60
    },
    {
        "id": "cfg_sla_por_vencer",
        "canal": "whatsapp",
        "modulo": "inventarios",
        "evento": "SLA_POR_VENCER",
        "activo": True,
        "provider": "mock",
        "modo_envio": "mock",
        "template_codigo": "inventarios_sla_por_vencer",
        "enviar_a_responsable": True,
        "enviar_a_supervisor": False,
        "enviar_a_gerente": False,
        "permite_reintentos": True,
        "max_reintentos": 2,
        "ventana_duplicidad_minutos": 120
    },
    {
        "id": "cfg_sla_vencido",
        "canal": "whatsapp",
        "modulo": "inventarios",
        "evento": "SLA_VENCIDO",
        "activo": True,
        "provider": "mock",
        "modo_envio": "mock",
        "template_codigo": "inventarios_sla_vencido",
        "enviar_a_responsable": True,
        "enviar_a_supervisor": True,
        "enviar_a_gerente": False,
        "permite_reintentos": True,
        "max_reintentos": 3,
        "ventana_duplicidad_minutos": 60
    },
    {
        "id": "cfg_sla_escalado",
        "canal": "whatsapp",
        "modulo": "inventarios",
        "evento": "SLA_ESCALADO",
        "activo": True,
        "provider": "mock",
        "modo_envio": "mock",
        "template_codigo": "inventarios_sla_escalado",
        "enviar_a_responsable": False,
        "enviar_a_supervisor": True,
        "enviar_a_gerente": True,
        "permite_reintentos": True,
        "max_reintentos": 3,
        "ventana_duplicidad_minutos": 30
    },
    {
        "id": "cfg_justificacion_rechazada",
        "canal": "whatsapp",
        "modulo": "inventarios",
        "evento": "JUSTIFICACION_RECHAZADA",
        "activo": True,
        "provider": "mock",
        "modo_envio": "mock",
        "template_codigo": "inventarios_justificacion_rechazada",
        "enviar_a_responsable": True,
        "enviar_a_supervisor": False,
        "enviar_a_gerente": False,
        "permite_reintentos": True,
        "max_reintentos": 2,
        "ventana_duplicidad_minutos": 30
    }
]

DEFAULT_PROVIDER_CONFIG = {
    "id": "provider_mock",
    "canal": "whatsapp",
    "provider": "mock",
    "activo": True,
    "base_url": None,
    "account_id": None,
    "token_ref": "WHATSAPP_API_TOKEN",
    "remitente": None,
    "metadata": {"description": "Mock provider para desarrollo y pruebas"}
}

DEFAULT_TEMPLATES = [
    {
        "id": "tpl_asignacion_tarea",
        "canal": "whatsapp",
        "codigo": "inventarios_asignacion_tarea",
        "nombre": "Asignación de Tarea",
        "activo": True,
        "idioma": "es",
        "template_texto": "EDARSA HUB: Tienes una tarea asignada del folio {{folio}} en {{sucursal}}. Fecha limite: {{fecha_limite}}. Ingresa al sistema para atenderla.",
        "variables": ["folio", "sucursal", "fecha_limite"],
        "version": 1
    },
    {
        "id": "tpl_sla_por_vencer",
        "canal": "whatsapp",
        "codigo": "inventarios_sla_por_vencer",
        "nombre": "SLA Por Vencer",
        "activo": True,
        "idioma": "es",
        "template_texto": "EDARSA HUB: El caso {{folio}} en {{sucursal}} esta por vencer. Etapa: {{evento}}. Limite: {{fecha_limite}}. Horas restantes: {{horas_restantes}}.",
        "variables": ["folio", "sucursal", "evento", "fecha_limite", "horas_restantes"],
        "version": 1
    },
    {
        "id": "tpl_sla_vencido",
        "canal": "whatsapp",
        "codigo": "inventarios_sla_vencido",
        "nombre": "SLA Vencido",
        "activo": True,
        "idioma": "es",
        "template_texto": "EDARSA HUB: El caso {{folio}} en {{sucursal}} vencio su SLA en la etapa {{evento}}. Se requiere atencion inmediata.",
        "variables": ["folio", "sucursal", "evento"],
        "version": 1
    },
    {
        "id": "tpl_sla_escalado",
        "canal": "whatsapp",
        "codigo": "inventarios_sla_escalado",
        "nombre": "SLA Escalado",
        "activo": True,
        "idioma": "es",
        "template_texto": "EDARSA HUB: ESCALAMIENTO - El caso {{folio}} en {{sucursal}} fue escalado por incumplimiento SLA en {{evento}}. Tiempo excedido: {{porcentaje_excedido}}%. Revisar de inmediato.",
        "variables": ["folio", "sucursal", "evento", "porcentaje_excedido"],
        "version": 1
    },
    {
        "id": "tpl_justificacion_rechazada",
        "canal": "whatsapp",
        "codigo": "inventarios_justificacion_rechazada",
        "nombre": "Justificación Rechazada",
        "activo": True,
        "idioma": "es",
        "template_texto": "EDARSA HUB: Tu justificacion para el folio {{folio}} en {{sucursal}} fue rechazada. Motivo: {{motivo}}. Debes corregirla.",
        "variables": ["folio", "sucursal", "motivo"],
        "version": 1
    },
    {
        "id": "tpl_decision_auditoria",
        "canal": "whatsapp",
        "codigo": "inventarios_decision_auditoria",
        "nombre": "Decisión de Auditoría",
        "activo": True,
        "idioma": "es",
        "template_texto": "EDARSA HUB: El folio {{folio}} en {{sucursal}} ha sido {{decision}} por auditoria. {{comentario}}",
        "variables": ["folio", "sucursal", "decision", "comentario"],
        "version": 1
    },
    {
        "id": "tpl_cierre_workflow",
        "canal": "whatsapp",
        "codigo": "inventarios_cierre_workflow",
        "nombre": "Cierre de Workflow",
        "activo": True,
        "idioma": "es",
        "template_texto": "EDARSA HUB: El caso {{folio}} en {{sucursal}} ha sido cerrado. Estado final: {{estado_final}}. Gracias por tu atencion.",
        "variables": ["folio", "sucursal", "estado_final"],
        "version": 1
    }
]


async def create_indexes(db):
    """Crea índices en las colecciones."""
    logger.info("Creando índices...")
    
    for collection_name, indexes in INDEXES.items():
        collection = db[collection_name]
        
        for idx_config in indexes:
            try:
                kwargs = {"name": idx_config["name"]}
                if idx_config.get("unique"):
                    kwargs["unique"] = True
                if idx_config.get("expireAfterSeconds"):
                    kwargs["expireAfterSeconds"] = idx_config["expireAfterSeconds"]
                
                await collection.create_index(idx_config["keys"], **kwargs)
                logger.info(f"  - Índice creado: {collection_name}.{idx_config['name']}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"  - Índice ya existe: {collection_name}.{idx_config['name']}")
                else:
                    logger.error(f"  - Error creando índice {idx_config['name']}: {e}")


async def seed_default_data(db):
    """Siembra datos iniciales."""
    logger.info("Sembrando datos iniciales...")
    ahora = datetime.now(timezone.utc).isoformat()
    
    # Configuraciones
    for config in DEFAULT_CONFIGS:
        existing = await db.notification_config.find_one({"id": config["id"]})
        if not existing:
            config["created_at"] = ahora
            await db.notification_config.insert_one(config)
            logger.info(f"  - Config creada: {config['evento']}")
        else:
            logger.info(f"  - Config ya existe: {config['evento']}")
    
    # Provider config
    existing = await db.notification_provider_config.find_one({"id": DEFAULT_PROVIDER_CONFIG["id"]})
    if not existing:
        DEFAULT_PROVIDER_CONFIG["created_at"] = ahora
        await db.notification_provider_config.insert_one(DEFAULT_PROVIDER_CONFIG)
        logger.info("  - Provider mock creado")
    else:
        logger.info("  - Provider mock ya existe")
    
    # Templates
    for template in DEFAULT_TEMPLATES:
        existing = await db.notification_templates.find_one({"id": template["id"]})
        if not existing:
            template["created_at"] = ahora
            await db.notification_templates.insert_one(template)
            logger.info(f"  - Template creado: {template['codigo']}")
        else:
            logger.info(f"  - Template ya existe: {template['codigo']}")


async def init_notification_system(db):
    """
    Inicializa el sistema de notificaciones completo.
    
    Args:
        db: Conexión a MongoDB
    """
    logger.info("=" * 60)
    logger.info("INICIALIZACIÓN DEL SISTEMA DE NOTIFICACIONES - SUBFASE 2B.5")
    logger.info("=" * 60)
    
    await create_indexes(db)
    await seed_default_data(db)
    
    logger.info("=" * 60)
    logger.info("INICIALIZACIÓN COMPLETADA")
    logger.info("=" * 60)


async def main():
    """Ejecuta la inicialización standalone."""
    logging.basicConfig(level=logging.INFO)
    
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "edarsa_hub")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        await init_notification_system(db)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
