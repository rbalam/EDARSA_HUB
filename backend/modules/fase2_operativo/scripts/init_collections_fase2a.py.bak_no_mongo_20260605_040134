"""
Script de Inicialización de Colecciones para Fase 2A
CAB-003 | EDARSA HUB

Este script crea las colecciones necesarias para el módulo operativo.
Es IDEMPOTENTE: puede ejecutarse múltiples veces sin efectos adversos.

IMPORTANTE:
- Solo crea colecciones NUEVAS
- NO modifica colecciones existentes
- NO toca automatizacion_inventarios_folios_procesados
"""
import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import CollectionInvalid, OperationFailure


# Configuración desde variables de entorno
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "edarsa_hub")

# Colecciones a crear para Fase 2A
COLECCIONES_FASE2A = [
    "workflow_inventarios",
    "detalle_diferencias", 
    "tareas_inventario",
    "historial_asignaciones",
    "justificaciones_inventario",
    "decisiones_auditoria",
    "configuracion_operativa",
]

# Colecciones PROTEGIDAS que NO se deben tocar
COLECCIONES_PROTEGIDAS = [
    "automatizacion_inventarios_folios_procesados",
]


def verificar_no_tocar_protegidas(db):
    """Verifica que no se intente modificar colecciones protegidas."""
    for col in COLECCIONES_PROTEGIDAS:
        if col in COLECCIONES_FASE2A:
            raise ValueError(f"ERROR CRÍTICO: Se intentó incluir colección protegida '{col}' en la lista de creación")
    print("✓ Verificación de colecciones protegidas: OK")


def crear_colecciones(db):
    """Crea las colecciones si no existen."""
    existentes = db.list_collection_names()
    creadas = []
    ya_existentes = []
    
    for col in COLECCIONES_FASE2A:
        if col in existentes:
            ya_existentes.append(col)
            print(f"  ⚠ Colección ya existe: {col}")
        else:
            try:
                db.create_collection(col)
                creadas.append(col)
                print(f"  ✓ Colección creada: {col}")
            except CollectionInvalid:
                ya_existentes.append(col)
                print(f"  ⚠ Colección ya existe: {col}")
    
    return creadas, ya_existentes


def crear_indices(db):
    """Crea los índices necesarios para las colecciones."""
    indices_creados = []
    
    # workflow_inventarios
    try:
        db.workflow_inventarios.create_index(
            [("procesado_id", ASCENDING)], 
            unique=True,
            name="idx_procesado_id_unique"
        )
        indices_creados.append("workflow_inventarios.idx_procesado_id_unique")
        print("  ✓ Índice: workflow_inventarios.procesado_id (unique)")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: workflow_inventarios.procesado_id")
        else:
            raise
    
    try:
        db.workflow_inventarios.create_index(
            [("estado_workflow", ASCENDING)],
            name="idx_estado_workflow"
        )
        indices_creados.append("workflow_inventarios.idx_estado_workflow")
        print("  ✓ Índice: workflow_inventarios.estado_workflow")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: workflow_inventarios.estado_workflow")
        else:
            raise
    
    try:
        db.workflow_inventarios.create_index(
            [("fecha_creacion", DESCENDING)],
            name="idx_fecha_creacion"
        )
        indices_creados.append("workflow_inventarios.idx_fecha_creacion")
        print("  ✓ Índice: workflow_inventarios.fecha_creacion")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: workflow_inventarios.fecha_creacion")
        else:
            raise
    
    # detalle_diferencias
    try:
        db.detalle_diferencias.create_index(
            [("workflow_id", ASCENDING)],
            name="idx_workflow_id"
        )
        indices_creados.append("detalle_diferencias.idx_workflow_id")
        print("  ✓ Índice: detalle_diferencias.workflow_id")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: detalle_diferencias.workflow_id")
        else:
            raise
    
    # tareas_inventario
    try:
        db.tareas_inventario.create_index(
            [("workflow_id", ASCENDING)],
            name="idx_workflow_id"
        )
        indices_creados.append("tareas_inventario.idx_workflow_id")
        print("  ✓ Índice: tareas_inventario.workflow_id")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: tareas_inventario.workflow_id")
        else:
            raise
    
    try:
        db.tareas_inventario.create_index(
            [("usuario_asignado_id", ASCENDING)],
            name="idx_usuario_asignado"
        )
        indices_creados.append("tareas_inventario.idx_usuario_asignado")
        print("  ✓ Índice: tareas_inventario.usuario_asignado_id")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: tareas_inventario.usuario_asignado_id")
        else:
            raise
    
    try:
        db.tareas_inventario.create_index(
            [("estado_tarea", ASCENDING)],
            name="idx_estado_tarea"
        )
        indices_creados.append("tareas_inventario.idx_estado_tarea")
        print("  ✓ Índice: tareas_inventario.estado_tarea")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: tareas_inventario.estado_tarea")
        else:
            raise
    
    try:
        db.tareas_inventario.create_index(
            [("fecha_limite", ASCENDING)],
            name="idx_fecha_limite"
        )
        indices_creados.append("tareas_inventario.idx_fecha_limite")
        print("  ✓ Índice: tareas_inventario.fecha_limite")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: tareas_inventario.fecha_limite")
        else:
            raise
    
    # historial_asignaciones
    try:
        db.historial_asignaciones.create_index(
            [("tarea_id", ASCENDING)],
            name="idx_tarea_id"
        )
        indices_creados.append("historial_asignaciones.idx_tarea_id")
        print("  ✓ Índice: historial_asignaciones.tarea_id")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: historial_asignaciones.tarea_id")
        else:
            raise
    
    # justificaciones_inventario
    try:
        db.justificaciones_inventario.create_index(
            [("workflow_id", ASCENDING)],
            name="idx_workflow_id"
        )
        indices_creados.append("justificaciones_inventario.idx_workflow_id")
        print("  ✓ Índice: justificaciones_inventario.workflow_id")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: justificaciones_inventario.workflow_id")
        else:
            raise
    
    try:
        db.justificaciones_inventario.create_index(
            [("diferencia_id", ASCENDING)],
            name="idx_diferencia_id"
        )
        indices_creados.append("justificaciones_inventario.idx_diferencia_id")
        print("  ✓ Índice: justificaciones_inventario.diferencia_id")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: justificaciones_inventario.diferencia_id")
        else:
            raise
    
    # decisiones_auditoria
    try:
        db.decisiones_auditoria.create_index(
            [("workflow_id", ASCENDING)],
            name="idx_workflow_id"
        )
        indices_creados.append("decisiones_auditoria.idx_workflow_id")
        print("  ✓ Índice: decisiones_auditoria.workflow_id")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: decisiones_auditoria.workflow_id")
        else:
            raise
    
    # configuracion_operativa
    try:
        db.configuracion_operativa.create_index(
            [("clave", ASCENDING)],
            unique=True,
            name="idx_clave_unique"
        )
        indices_creados.append("configuracion_operativa.idx_clave_unique")
        print("  ✓ Índice: configuracion_operativa.clave (unique)")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("  ⚠ Índice ya existe: configuracion_operativa.clave")
        else:
            raise
    
    return indices_creados


def insertar_configuracion_inicial(db):
    """Inserta la configuración inicial si no existe."""
    config_inicial = [
        {
            "clave": "UMBRAL_JUSTIFICACION_SIMPLE",
            "valor": "500",
            "descripcion": "Monto máximo en MXN para justificación simple (sin evidencia documental obligatoria)",
            "fecha_creacion": datetime.now(timezone.utc)
        },
        {
            "clave": "DIAS_LIMITE_TAREA_DEFAULT",
            "valor": "3",
            "descripcion": "Días límite por defecto para completar una tarea asignada",
            "fecha_creacion": datetime.now(timezone.utc)
        },
        {
            "clave": "MAX_CICLOS_REASIGNACION",
            "valor": "3",
            "descripcion": "Número máximo de ciclos de reasignación antes de escalamiento automático",
            "fecha_creacion": datetime.now(timezone.utc)
        },
    ]
    
    insertados = []
    existentes = []
    
    for config in config_inicial:
        existente = db.configuracion_operativa.find_one({"clave": config["clave"]})
        if existente:
            existentes.append(config["clave"])
            print(f"  ⚠ Configuración ya existe: {config['clave']}")
        else:
            db.configuracion_operativa.insert_one(config)
            insertados.append(config["clave"])
            print(f"  ✓ Configuración insertada: {config['clave']} = {config['valor']}")
    
    return insertados, existentes


def verificar_colecciones_protegidas_intactas(db):
    """Verifica que las colecciones protegidas no fueron modificadas."""
    print("\n=== VERIFICACIÓN DE COLECCIONES PROTEGIDAS ===")
    for col in COLECCIONES_PROTEGIDAS:
        if col in db.list_collection_names():
            count = db[col].count_documents({})
            print(f"  ✓ {col}: EXISTE con {count} documentos (NO TOCADA)")
        else:
            print(f"  ⚠ {col}: No existe (esto es esperado si Fase 1 no se ejecutó)")


def mostrar_resumen(db):
    """Muestra resumen de las colecciones del módulo."""
    print("\n=== RESUMEN DE COLECCIONES FASE 2A ===")
    for col in COLECCIONES_FASE2A:
        if col in db.list_collection_names():
            count = db[col].count_documents({})
            indices = list(db[col].list_indexes())
            print(f"  {col}:")
            print(f"    - Documentos: {count}")
            print(f"    - Índices: {len(indices)}")
        else:
            print(f"  {col}: NO EXISTE (error)")


def init_fase2a_collections():
    """Función principal de inicialización."""
    print("=" * 70)
    print("INICIALIZACIÓN DE COLECCIONES - FASE 2A")
    print("CAB-003 | EDARSA HUB")
    print("=" * 70)
    print(f"\nFecha/Hora: {datetime.now(timezone.utc).isoformat()}")
    print(f"Base de datos: {DB_NAME}")
    print()
    
    if not MONGO_URL:
        print("ERROR: Variable de entorno MONGO_URL no definida")
        sys.exit(1)
    
    try:
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        # Verificar conexión
        client.admin.command('ping')
        print("✓ Conexión a MongoDB establecida")
    except Exception as e:
        print(f"ERROR: No se pudo conectar a MongoDB: {e}")
        sys.exit(1)
    
    db = client[DB_NAME]
    
    # Paso 1: Verificar que no se tocan colecciones protegidas
    print("\n=== PASO 1: VERIFICACIÓN DE SEGURIDAD ===")
    verificar_no_tocar_protegidas(db)
    
    # Paso 2: Crear colecciones
    print("\n=== PASO 2: CREACIÓN DE COLECCIONES ===")
    creadas, ya_existentes = crear_colecciones(db)
    
    # Paso 3: Crear índices
    print("\n=== PASO 3: CREACIÓN DE ÍNDICES ===")
    indices = crear_indices(db)
    
    # Paso 4: Insertar configuración inicial
    print("\n=== PASO 4: CONFIGURACIÓN INICIAL ===")
    config_insertadas, config_existentes = insertar_configuracion_inicial(db)
    
    # Paso 5: Verificar que colecciones protegidas están intactas
    verificar_colecciones_protegidas_intactas(db)
    
    # Mostrar resumen
    mostrar_resumen(db)
    
    # Resultado final
    print("\n" + "=" * 70)
    print("RESULTADO DE INICIALIZACIÓN")
    print("=" * 70)
    print(f"Colecciones creadas: {len(creadas)}")
    print(f"Colecciones ya existentes: {len(ya_existentes)}")
    print(f"Índices procesados: {len(indices)}")
    print(f"Configuraciones insertadas: {len(config_insertadas)}")
    print(f"Configuraciones ya existentes: {len(config_existentes)}")
    print()
    print("✅ INICIALIZACIÓN FASE 2A COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    
    client.close()
    return True


if __name__ == "__main__":
    init_fase2a_collections()
