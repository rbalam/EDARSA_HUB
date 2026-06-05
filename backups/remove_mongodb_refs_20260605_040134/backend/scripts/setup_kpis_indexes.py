"""
EDARSA HUB - Script de Inicialización de Índices para KPIs Consolidados
========================================================================

Crea los índices necesarios para la colección `kpis_comercial`.
Ejecutar una vez en setup inicial o al agregar nuevos índices.

Fecha: 2026-04-22
Versión: 1.0

USO:
    python -m scripts.setup_kpis_indexes
    
    O desde el código:
    from scripts.setup_kpis_indexes import setup_kpis_comercial_indexes
    await setup_kpis_comercial_indexes(db)
"""

import asyncio
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

COLLECTION_NAME = "kpis_comercial"


async def setup_kpis_comercial_indexes(db) -> dict:
    """
    Crea índices para la colección kpis_comercial.
    
    Índices:
    1. idx_unique_kpi_diario (ÚNICO): server_id + empresa_id + sucursal_id + fecha
    2. idx_empresa_fecha: Consultas del Tablero Ejecutivo
    3. idx_server_fecha: Consultas de sincronización
    4. idx_estado_fecha: Filtrar por estado de período
    5. idx_unidad_fecha: Consultas por unidad de negocio
    6. idx_pendientes_reconciliacion: Buscar pendientes
    
    Args:
        db: Conexión a MongoDB
        
    Returns:
        dict con {index_name: status}
    """
    collection = db[COLLECTION_NAME]
    results = {}
    
    # ========================================
    # ÍNDICE ÚNICO (CLAVE PRIMARIA)
    # ========================================
    try:
        await collection.create_index(
            [
                ("server_id", 1),
                ("empresa_id", 1),
                ("sucursal_id", 1),
                ("fecha", 1)
            ],
            unique=True,
            name="idx_unique_kpi_diario",
            background=True
        )
        results["idx_unique_kpi_diario"] = "CREATED"
        logging.info("[SETUP-INDEX] idx_unique_kpi_diario (UNIQUE) creado")
    except Exception as e:
        if "already exists" in str(e).lower():
            results["idx_unique_kpi_diario"] = "EXISTS"
            logging.info("[SETUP-INDEX] idx_unique_kpi_diario ya existe")
        else:
            results["idx_unique_kpi_diario"] = f"ERROR: {e}"
            logging.error(f"[SETUP-INDEX] Error en idx_unique_kpi_diario: {e}")
    
    # ========================================
    # ÍNDICES DE CONSULTA
    # ========================================
    
    # idx_empresa_fecha: Tablero Ejecutivo por empresa
    try:
        await collection.create_index(
            [("empresa_id", 1), ("fecha", -1)],
            name="idx_empresa_fecha",
            background=True
        )
        results["idx_empresa_fecha"] = "CREATED"
        logging.info("[SETUP-INDEX] idx_empresa_fecha creado")
    except Exception as e:
        if "already exists" in str(e).lower():
            results["idx_empresa_fecha"] = "EXISTS"
        else:
            results["idx_empresa_fecha"] = f"ERROR: {e}"
            logging.error(f"[SETUP-INDEX] Error en idx_empresa_fecha: {e}")
    
    # idx_server_fecha: Sincronización por servidor
    try:
        await collection.create_index(
            [("server_id", 1), ("fecha", -1)],
            name="idx_server_fecha",
            background=True
        )
        results["idx_server_fecha"] = "CREATED"
        logging.info("[SETUP-INDEX] idx_server_fecha creado")
    except Exception as e:
        if "already exists" in str(e).lower():
            results["idx_server_fecha"] = "EXISTS"
        else:
            results["idx_server_fecha"] = f"ERROR: {e}"
            logging.error(f"[SETUP-INDEX] Error en idx_server_fecha: {e}")
    
    # idx_estado_fecha: Filtrar por estado de período
    try:
        await collection.create_index(
            [("estado_periodo", 1), ("fecha", -1)],
            name="idx_estado_fecha",
            background=True
        )
        results["idx_estado_fecha"] = "CREATED"
        logging.info("[SETUP-INDEX] idx_estado_fecha creado")
    except Exception as e:
        if "already exists" in str(e).lower():
            results["idx_estado_fecha"] = "EXISTS"
        else:
            results["idx_estado_fecha"] = f"ERROR: {e}"
            logging.error(f"[SETUP-INDEX] Error en idx_estado_fecha: {e}")
    
    # idx_unidad_fecha: Consultas por unidad de negocio
    try:
        await collection.create_index(
            [("unidad_negocio_id", 1), ("fecha", -1)],
            name="idx_unidad_fecha",
            background=True
        )
        results["idx_unidad_fecha"] = "CREATED"
        logging.info("[SETUP-INDEX] idx_unidad_fecha creado")
    except Exception as e:
        if "already exists" in str(e).lower():
            results["idx_unidad_fecha"] = "EXISTS"
        else:
            results["idx_unidad_fecha"] = f"ERROR: {e}"
            logging.error(f"[SETUP-INDEX] Error en idx_unidad_fecha: {e}")
    
    # idx_pendientes_reconciliacion: Buscar pendientes
    try:
        await collection.create_index(
            [("flags.requiere_reconciliacion", 1), ("fecha", -1)],
            name="idx_pendientes_reconciliacion",
            background=True
        )
        results["idx_pendientes_reconciliacion"] = "CREATED"
        logging.info("[SETUP-INDEX] idx_pendientes_reconciliacion creado")
    except Exception as e:
        if "already exists" in str(e).lower():
            results["idx_pendientes_reconciliacion"] = "EXISTS"
        else:
            results["idx_pendientes_reconciliacion"] = f"ERROR: {e}"
            logging.error(f"[SETUP-INDEX] Error en idx_pendientes_reconciliacion: {e}")
    
    # ========================================
    # RESUMEN
    # ========================================
    created = sum(1 for v in results.values() if v == "CREATED")
    existing = sum(1 for v in results.values() if v == "EXISTS")
    errors = sum(1 for v in results.values() if v.startswith("ERROR"))
    
    logging.info(
        f"[SETUP-INDEX] Resumen: {created} creados, {existing} existentes, {errors} errores"
    )
    
    return results


async def verify_indexes(db) -> dict:
    """
    Verifica que los índices existan y estén correctos.
    
    Returns:
        dict con información de cada índice
    """
    collection = db[COLLECTION_NAME]
    indexes = await collection.index_information()
    
    required_indexes = [
        "idx_unique_kpi_diario",
        "idx_empresa_fecha",
        "idx_server_fecha",
        "idx_estado_fecha",
        "idx_unidad_fecha",
        "idx_pendientes_reconciliacion"
    ]
    
    results = {}
    for idx_name in required_indexes:
        if idx_name in indexes:
            results[idx_name] = {
                "status": "OK",
                "keys": indexes[idx_name].get("key"),
                "unique": indexes[idx_name].get("unique", False)
            }
        else:
            results[idx_name] = {"status": "MISSING"}
    
    return results


async def main():
    """Ejecuta la creación de índices."""
    # Obtener configuración de MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'edarsa_hub')
    
    logging.info(f"[SETUP-INDEX] Conectando a MongoDB: {db_name}")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Crear índices
    logging.info("[SETUP-INDEX] Creando índices para kpis_comercial...")
    results = await setup_kpis_comercial_indexes(db)
    
    # Verificar
    logging.info("[SETUP-INDEX] Verificando índices...")
    verification = await verify_indexes(db)
    
    print("\n" + "=" * 60)
    print("RESULTADO DE CREACIÓN DE ÍNDICES")
    print("=" * 60)
    for idx_name, status in results.items():
        print(f"  {idx_name}: {status}")
    
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE ÍNDICES")
    print("=" * 60)
    for idx_name, info in verification.items():
        status = info.get("status", "UNKNOWN")
        unique = " (UNIQUE)" if info.get("unique") else ""
        print(f"  {idx_name}: {status}{unique}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
