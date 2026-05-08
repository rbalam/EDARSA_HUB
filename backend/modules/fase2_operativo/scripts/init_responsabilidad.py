"""
Script de Inicialización - Responsabilidad Económica
CAB-003 | EDARSA HUB - Fase 2C.1

Inicializa las claves de configuración del módulo de responsabilidad
en la colección configuracion_operativa (EXISTENTE).

Uso:
    python -m modules.fase2_operativo.scripts.init_responsabilidad

O importar y ejecutar:
    from modules.fase2_operativo.scripts.init_responsabilidad import inicializar
    await inicializar()
"""
import asyncio
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Claves de configuración para responsabilidad económica
CONFIGURACION_RESPONSABILIDAD = [
    {
        "clave": "CARGO_MINIMO_MXN",
        "valor": "50.0",
        "descripcion": "Monto mínimo en MXN para generar un cargo por responsabilidad económica"
    },
    {
        "clave": "TOLERANCIA_UNIDADES",
        "valor": "2",
        "descripcion": "Tolerancia absoluta en unidades para diferencias de inventario"
    },
    {
        "clave": "TOLERANCIA_PORCENTAJE_DIFERENCIA",
        "valor": "1.5",
        "descripcion": "Tolerancia relativa en porcentaje sobre cantidad esperada"
    },
    {
        "clave": "PRECIO_FALTANTE_DEFAULT",
        "valor": "0.0",
        "descripcion": "Precio unitario por defecto si no viene del análisis de inventario"
    },
    {
        "clave": "MODULO_RESPONSABILIDAD_ACTIVO",
        "valor": "true",
        "descripcion": "Indica si el módulo de responsabilidad económica está habilitado"
    },
    {
        "clave": "PERMITIR_COMPENSACION_FALTANTES_SOBRANTES",
        "valor": "false",
        "descripcion": "Permitir que sobrantes compensen faltantes (default: NO)"
    },
]


async def inicializar_configuracion(db) -> dict:
    """
    Inicializa las claves de configuración en configuracion_operativa.
    
    NO sobrescribe claves existentes.
    
    Args:
        db: Conexión a MongoDB
        
    Returns:
        Resumen de la operación
    """
    collection = db["configuracion_operativa"]
    now = datetime.now(timezone.utc)
    
    claves_creadas = []
    claves_existentes = []
    
    for config in CONFIGURACION_RESPONSABILIDAD:
        clave = config["clave"]
        
        # Verificar si ya existe
        existente = collection.find_one({"clave": clave})
        
        if existente:
            claves_existentes.append(clave)
            logger.info(f"Clave existente (no modificada): {clave} = {existente.get('valor')}")
        else:
            # Crear nueva
            documento = {
                "clave": clave,
                "valor": config["valor"],
                "descripcion": config["descripcion"],
                "fecha_creacion": now,
                "modulo": "responsabilidad_economica",
                "fase": "2C.1"
            }
            collection.insert_one(documento)
            claves_creadas.append(clave)
            logger.info(f"Clave creada: {clave} = {config['valor']}")
    
    resumen = {
        "claves_creadas": claves_creadas,
        "claves_existentes": claves_existentes,
        "total_creadas": len(claves_creadas),
        "total_existentes": len(claves_existentes),
        "fecha_ejecucion": now.isoformat()
    }
    
    logger.info(f"Inicialización completada: {len(claves_creadas)} creadas, {len(claves_existentes)} existentes")
    
    return resumen


async def verificar_coleccion_responsabilidad(db) -> dict:
    """
    Verifica el estado de la colección responsabilidad_economica.
    
    Args:
        db: Conexión a MongoDB
        
    Returns:
        Estado de la colección
    """
    collection = db["responsabilidad_economica"]
    
    # Contar documentos
    total = collection.count_documents({})
    
    # Crear índices si no existen
    indices_creados = []
    
    # Índice por workflow_id (único)
    try:
        collection.create_index("workflow_id", unique=True, name="idx_workflow_id")
        indices_creados.append("idx_workflow_id")
    except Exception:
        pass  # Ya existe
    
    # Índice por sucursal_id
    try:
        collection.create_index("sucursal_id", name="idx_sucursal_id")
        indices_creados.append("idx_sucursal_id")
    except Exception:
        pass
    
    # Índice por estado
    try:
        collection.create_index("estado", name="idx_estado")
        indices_creados.append("idx_estado")
    except Exception:
        pass
    
    # Índice por fecha_calculo
    try:
        collection.create_index("fecha_calculo", name="idx_fecha_calculo")
        indices_creados.append("idx_fecha_calculo")
    except Exception:
        pass
    
    return {
        "coleccion": "responsabilidad_economica",
        "documentos": total,
        "indices_creados": indices_creados
    }


async def inicializar(db=None):
    """
    Función principal de inicialización.
    
    Ejecuta:
    1. Inicialización de configuración
    2. Verificación/creación de índices
    
    Args:
        db: Conexión a MongoDB (opcional, se obtiene si no se pasa)
    """
    if db is None:
        from ..db_utils import get_database
        db = get_database()
    
    logger.info("=" * 60)
    logger.info("INICIALIZACIÓN FASE 2C.1 - RESPONSABILIDAD ECONÓMICA")
    logger.info("=" * 60)
    
    # 1. Inicializar configuración
    logger.info("\n[1/2] Inicializando configuración...")
    config_resultado = await inicializar_configuracion(db)
    
    # 2. Verificar colección
    logger.info("\n[2/2] Verificando colección responsabilidad_economica...")
    coleccion_resultado = await verificar_coleccion_responsabilidad(db)
    
    logger.info("\n" + "=" * 60)
    logger.info("INICIALIZACIÓN COMPLETADA")
    logger.info("=" * 60)
    
    return {
        "configuracion": config_resultado,
        "coleccion": coleccion_resultado
    }


# Ejecución directa
if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/app/backend")
    
    from modules.fase2_operativo.db_utils import get_database
    
    db = get_database()
    resultado = asyncio.run(inicializar(db))
    
    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    print(f"Configuración: {resultado['configuracion']['total_creadas']} claves creadas")
    print(f"Colección: {resultado['coleccion']['documentos']} documentos existentes")
    print(f"Índices: {len(resultado['coleccion']['indices_creados'])} creados/verificados")
