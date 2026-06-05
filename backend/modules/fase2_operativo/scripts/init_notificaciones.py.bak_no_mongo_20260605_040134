"""
Script de inicialización de colecciones para notificaciones.
CAB-003 | Fase 2B.1

Crea las colecciones e índices necesarios para el sistema de notificaciones.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_notificaciones_collections():
    """Inicializa las colecciones de notificaciones."""
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    logger.info("Iniciando configuración de colecciones de notificaciones...")
    
    # 1. Crear colección notificaciones_log
    try:
        await db.create_collection("notificaciones_log")
        logger.info("✅ Colección 'notificaciones_log' creada")
    except Exception as e:
        if "already exists" in str(e):
            logger.info("ℹ️ Colección 'notificaciones_log' ya existe")
        else:
            logger.warning(f"⚠️ Error creando colección: {e}")
    
    # 2. Crear índices
    indices = [
        ("notificaciones_log", [("tipo_evento", 1)]),
        ("notificaciones_log", [("workflow_id", 1)]),
        ("notificaciones_log", [("tarea_id", 1)]),
        ("notificaciones_log", [("fecha_envio", -1)]),
        ("notificaciones_log", [("estado", 1)]),
        ("notificaciones_log", [("destinatario", 1)]),
    ]
    
    for collection_name, index_spec in indices:
        try:
            await db[collection_name].create_index(index_spec)
            logger.info(f"✅ Índice creado en '{collection_name}': {index_spec}")
        except Exception as e:
            logger.warning(f"⚠️ Error creando índice: {e}")
    
    # 3. Insertar documento de prueba (opcional, para verificar estructura)
    test_doc = await db.notificaciones_log.find_one({"tipo_evento": "_INIT_TEST"})
    if not test_doc:
        await db.notificaciones_log.insert_one({
            "id": "init-test-001",
            "tipo_evento": "_INIT_TEST",
            "workflow_id": None,
            "tarea_id": None,
            "destinatario": "test@test.com",
            "canal": "email",
            "asunto": "Test de inicialización",
            "estado": "test",
            "error": None,
            "metadata": {"init": True},
            "fecha_envio": "2026-04-17T00:00:00Z"
        })
        logger.info("✅ Documento de prueba insertado")
    
    # 4. Eliminar documento de prueba
    await db.notificaciones_log.delete_one({"tipo_evento": "_INIT_TEST"})
    
    logger.info("✅ Inicialización de colecciones de notificaciones completada")
    
    # Mostrar estadísticas
    count = await db.notificaciones_log.count_documents({})
    logger.info(f"📊 Total documentos en notificaciones_log: {count}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(init_notificaciones_collections())
