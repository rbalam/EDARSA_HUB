#!/usr/bin/env python3
# =============================================================================
# CAB-003 FASE 1B.2A - SCRIPT DE SIMULACIÓN CONTROLADA
# =============================================================================
#
#   ██████╗ ██████╗ ██╗████████╗██╗ ██████╗ ██████╗ 
#  ██╔════╝██╔═══██╗██║╚══██╔══╝██║██╔════╝██╔═══██╗
#  ██║     ██████╔╝██║   ██║   ██║██║     ██║   ██║
#  ██║     ██╔══██╗██║   ██║   ██║██║     ██║   ██║
#  ╚██████╗██║  ██║██║   ██║   ██║╚██████╗╚██████╔╝
#   ╚═════╝╚═╝  ╚═╝╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═════╝ 
#
# =============================================================================
#
# ⚠️  ADVERTENCIAS CRÍTICAS:
#    
#     1. Este script es de EJECUCIÓN MANUAL ÚNICAMENTE
#     2. NO forma parte del arranque del backend
#     3. NO se ejecuta automáticamente
#     4. NO está registrado en ningún scheduler
#     5. NO forma parte de la suite de tests automáticos (pytest)
#    
#     MODOS DE EJECUCIÓN:
#     $ python tests/test_simulacion_controlada.py                          # Dry-run
#     $ python tests/test_simulacion_controlada.py --persistir-uno          # Persistir 1
#     $ python tests/test_simulacion_controlada.py --rollback ID            # Rollback
#     $ python tests/test_simulacion_controlada.py --test-secuencia-controlada  # Prueba completa
#    
#     Requiere supervisión humana antes, durante y después.
#
# =============================================================================

# Protección contra importación como módulo
if __name__ != "__main__":
    raise RuntimeError(
        "\n\n"
        "╔═══════════════════════════════════════════════════════════════════╗\n"
        "║  ERROR: Este script solo puede ejecutarse directamente.          ║\n"
        "║  NO importar como módulo.                                        ║\n"
        "║                                                                   ║\n"
        "║  Uso correcto:                                                    ║\n"
        "║    $ cd /app/backend                                              ║\n"
        "║    $ python tests/test_simulacion_controlada.py                   ║\n"
        "╚═══════════════════════════════════════════════════════════════════╝\n"
    )

import sys
import os
import json
import asyncio
import argparse
from datetime import datetime
from dataclasses import asdict

# Agregar path del backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

EDARSAHUB_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'HRLectura',
    'password': 'National09$'
}

# =============================================================================
# ARGUMENTOS DE LÍNEA DE COMANDOS
# =============================================================================

parser = argparse.ArgumentParser(
    description='CAB-003 Fase 1B.2A - Simulación Controlada',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Ejemplos:
  python tests/test_simulacion_controlada.py                              # Dry-run
  python tests/test_simulacion_controlada.py --persistir-uno              # Persistir 1 registro
  python tests/test_simulacion_controlada.py --rollback ID                # Rollback por ID
  python tests/test_simulacion_controlada.py --test-secuencia-controlada  # Prueba INSERT→DUP→ROLLBACK
    """
)
parser.add_argument('--persistir-uno', action='store_true', 
                    help='Modo de persistencia: insertar 1 registro manual')
parser.add_argument('--rollback', type=str, metavar='ID',
                    help='Rollback por identificador de ejecución')
parser.add_argument('--sistema', type=str, choices=['SOFT', 'MPRO'],
                    help='Filtrar por sistema (solo para --persistir-uno y --test-secuencia-controlada)')
parser.add_argument('--test-secuencia-controlada', action='store_true',
                    help='Prueba controlada: INSERT → DUPLICADO → ROLLBACK con confirmación en cada paso')
parser.add_argument('--persistir-lote-soft', action='store_true',
                    help='Fase 1B.3A: Persistir lote de máximo 2 registros SOFT con confirmación por registro')
parser.add_argument('--persistir-lote-mpro', action='store_true',
                    help='Fase 1B.3B: Persistir lote de 1 registro MPRO con confirmación obligatoria')

args = parser.parse_args()

# Determinar modo
if args.rollback:
    MODO = 'ROLLBACK'
elif args.persistir_uno:
    MODO = 'PERSISTIR_UNO'
elif args.test_secuencia_controlada:
    MODO = 'TEST_SECUENCIA_CONTROLADA'
elif args.persistir_lote_soft:
    MODO = 'PERSISTIR_LOTE_SOFT'
elif args.persistir_lote_mpro:
    MODO = 'PERSISTIR_LOTE_MPRO'
else:
    MODO = 'DRY_RUN'

print("=" * 80)
print(f"CAB-003 FASE 1B.2A - SIMULACIÓN CONTROLADA ({MODO})")
print("=" * 80)
print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
print(f"Modo: {MODO}")
print("=" * 80)
print()

# =============================================================================
# IMPORTACIONES
# =============================================================================

try:
    from core.db import execute_sql_query
    from motor.motor_asyncio import AsyncIOMotorClient
    from modules.automatizacion.detection_service import (
        detectar_inventarios_soft,
        detectar_inventarios_mpro,
        InventarioDetectado
    )
    from modules.automatizacion import repository
    print("✓ Módulos importados correctamente")
except ImportError as e:
    print(f"✗ Error importando módulos: {e}")
    sys.exit(1)

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

async def get_servers_from_mongo():
    """Obtiene servidores activos de MongoDB."""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    mongo_url = mongo_url.strip('"').strip("'")
    
    if not mongo_url:
        print("✗ MONGO_URL no configurada")
        return []
    
    client = AsyncIOMotorClient(mongo_url)
    db = client['test_database']
    
    cursor = db.servers.find(
        {'active': True},
        {'_id': 0}
    )
    servers = await cursor.to_list(length=100)
    return servers


def print_inventario(inv: dict, index: int):
    """Imprime un inventario detectado de forma legible."""
    print(f"\n  [{index}] {inv['sistema_origen']} - {inv['folio_inventario']}")
    print(f"      Fecha: {inv['fecha_inventario']}")
    print(f"      Almacén: {inv['almacen_id']} ({inv.get('almacen_nombre', 'N/A')})")
    if inv['sistema_origen'] == 'MPRO':
        print(f"      Sucursal: {inv['sucursal_id']} ({inv.get('sucursal_nombre', 'N/A')})")
        print(f"      Comentario: {inv['comentario']}")
        print(f"      Estado origen: {inv['estado_inventario_origen']}")
    print(f"      Ya procesado: {'SÍ' if inv['ya_procesado'] else 'NO'}")
    print(f"      Acción sugerida: {inv['accion_sugerida']}")
    if inv['razon_omision']:
        print(f"      Razón omisión: {inv['razon_omision']}")
    if inv['folio_inicial_calculado']:
        print(f"      Folio inicial calculado: {inv['folio_inicial_calculado']} ({inv['fecha_inicial_calculada']})")


def mostrar_payload_completo(inv: dict, identificador: str, hash_verif: str):
    """Muestra el payload completo antes de insertar."""
    print("\n" + "=" * 80)
    print("REGISTRO A INSERTAR")
    print("=" * 80)
    print()
    print(f"  {'Campo':<30} │ Valor")
    print(f"  {'─' * 30}┼{'─' * 45}")
    print(f"  {'sistema_origen':<30} │ {inv['sistema_origen']}")
    print(f"  {'server_id':<30} │ {inv['server_id']}")
    print(f"  {'sucursal_id':<30} │ {inv['sucursal_id'] or '(vacío)'}")
    print(f"  {'almacen_id':<30} │ {inv['almacen_id']}")
    print(f"  {'comentario':<30} │ {inv['comentario'] or 'NULL'}")
    print(f"  {'folio_inventario':<30} │ {inv['folio_inventario']}")
    print(f"  {'fecha_inventario':<30} │ {inv['fecha_inventario']}")
    print(f"  {'estado_inventario_origen':<30} │ {inv['estado_inventario_origen'] or 'NULL'}")
    print(f"  {'hash_verificacion':<30} │ {hash_verif[:32]}...")
    print(f"  {'estado':<30} │ EN_PROCESO")
    print(f"  {'created_by':<30} │ {identificador}")
    print()
    print("=" * 80)


# =============================================================================
# MODO DRY-RUN
# =============================================================================

async def ejecutar_dry_run():
    """Ejecuta detección sin persistencia."""
    print("\n" + "=" * 80)
    print("FASE 1: Obteniendo servidores de MongoDB...")
    print("=" * 80)
    
    servers = await get_servers_from_mongo()
    print(f"✓ Servidores encontrados: {len(servers)}")
    
    soft_servers = [s for s in servers if s.get('system_type') == 'SoftRestaurant']
    mpro_servers = [s for s in servers if s.get('system_type') == 'MPRO']
    
    print(f"  - SoftRestaurant: {len(soft_servers)}")
    print(f"  - MPRO: {len(mpro_servers)}")
    
    todos_detectados = []
    
    # DRY-RUN SOFT
    print("\n" + "=" * 80)
    print("FASE 2: Detección DRY-RUN en SoftRestaurant")
    print("=" * 80)
    
    for server in soft_servers:
        print(f"\n▶ Escaneando: {server['name']}")
        
        try:
            folios_procesados = repository.get_folios_ya_procesados(
                execute_sql_query,
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                sistema_origen='SOFTRESTAURANT',
                server_id=server['id']
            )
            print(f"  Folios ya procesados en EDARSAHUB: {len(folios_procesados)}")
            
            detectados = detectar_inventarios_soft(
                execute_sql_query, server, folios_procesados
            )
            
            print(f"  Inventarios detectados: {len(detectados)}")
            
            for i, det in enumerate(detectados[:5], 1):
                inv_dict = asdict(det)
                print_inventario(inv_dict, i)
                todos_detectados.append(inv_dict)
            
            if len(detectados) > 5:
                for det in detectados[5:]:
                    todos_detectados.append(asdict(det))
                print(f"\n  ... y {len(detectados) - 5} más")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # DRY-RUN MPRO
    print("\n" + "=" * 80)
    print("FASE 3: Detección DRY-RUN en MPRO")
    print("=" * 80)
    
    for server in mpro_servers:
        print(f"\n▶ Escaneando: {server['name']}")
        
        try:
            folios_procesados = repository.get_folios_ya_procesados(
                execute_sql_query,
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                sistema_origen='MPRO',
                server_id=server['id']
            )
            print(f"  Folios ya procesados en EDARSAHUB: {len(folios_procesados)}")
            
            detectados = detectar_inventarios_mpro(
                execute_sql_query, server, folios_procesados
            )
            
            print(f"  Inventarios detectados: {len(detectados)}")
            
            for i, det in enumerate(detectados[:5], 1):
                inv_dict = asdict(det)
                print_inventario(inv_dict, i)
                todos_detectados.append(inv_dict)
            
            if len(detectados) > 5:
                for det in detectados[5:]:
                    todos_detectados.append(asdict(det))
                print(f"\n  ... y {len(detectados) - 5} más")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # RESUMEN
    print("\n" + "=" * 80)
    print("RESUMEN DRY-RUN")
    print("=" * 80)
    
    total = len(todos_detectados)
    a_procesar = len([d for d in todos_detectados if d['accion_sugerida'] == 'PROCESAR'])
    a_omitir = len([d for d in todos_detectados if d['accion_sugerida'] == 'OMITIR'])
    ya_procesados = len([d for d in todos_detectados if d['ya_procesado']])
    
    print(f"""
    Total inventarios detectados: {total}
    ├── A procesar:    {a_procesar}
    ├── A omitir:      {a_omitir}
    └── Ya procesados: {ya_procesados}
    """)
    
    # Guardar resultado
    resultado = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'modo': 'DRY_RUN',
        'resumen': {
            'total_detectados': total,
            'a_procesar': a_procesar,
            'a_omitir': a_omitir,
            'ya_procesados': ya_procesados
        },
        'inventarios': todos_detectados
    }
    
    output_file = '/app/backend/tests/dry_run_result.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✓ Resultado guardado en: {output_file}")
    
    return resultado


# =============================================================================
# MODO PERSISTIR UNO
# =============================================================================

async def ejecutar_persistir_uno():
    """Permite persistir 1 solo registro manualmente."""
    
    # Primero ejecutar dry-run para obtener candidatos
    print("\n⏳ Ejecutando detección para obtener candidatos...")
    resultado_dry = await ejecutar_dry_run()
    
    # Filtrar candidatos a procesar
    candidatos = [i for i in resultado_dry['inventarios'] 
                  if i['accion_sugerida'] == 'PROCESAR']
    
    # Aplicar filtro de sistema si se especificó
    if args.sistema:
        sistema_filtro = 'SOFTRESTAURANT' if args.sistema == 'SOFT' else 'MPRO'
        candidatos = [c for c in candidatos if c['sistema_origen'] == sistema_filtro]
    
    if not candidatos:
        print("\n⚠️  No hay candidatos para persistir.")
        return
    
    print("\n" + "=" * 80)
    print("PERSISTENCIA MANUAL DE 1 REGISTRO")
    print("=" * 80)
    print(f"\nCandidatos disponibles: {len(candidatos)}")
    
    # Mostrar lista de candidatos
    print("\nSeleccione el registro a persistir:\n")
    for i, c in enumerate(candidatos[:20], 1):
        sistema_short = 'SOFT' if c['sistema_origen'] == 'SOFTRESTAURANT' else 'MPRO'
        print(f"  [{i:2d}] {sistema_short} | {c['folio_inventario']:<15} | {c['fecha_inventario']} | Alm: {c['almacen_id']}")
    
    if len(candidatos) > 20:
        print(f"\n  ... y {len(candidatos) - 20} más (solo se muestran los primeros 20)")
    
    # Solicitar selección
    print()
    try:
        seleccion = input("Ingrese el número del registro (o 'q' para salir): ").strip()
        
        if seleccion.lower() == 'q':
            print("\n⚠️  Operación cancelada por usuario")
            return
        
        indice = int(seleccion) - 1
        if indice < 0 or indice >= len(candidatos):
            print(f"\n✗ Selección inválida. Debe ser entre 1 y {min(len(candidatos), 20)}")
            return
        
        inv = candidatos[indice]
        
    except (ValueError, EOFError):
        print("\n✗ Entrada inválida")
        return
    
    # Generar identificador y hash
    identificador = repository.generar_identificador_ejecucion()
    hash_verif = repository.generar_hash_verificacion(
        inv['sistema_origen'],
        inv['server_id'],
        inv['sucursal_id'],
        inv['almacen_id'],
        inv['comentario'],
        inv['folio_inventario'],
        inv['fecha_inventario'],
        inv['estado_inventario_origen']
    )
    
    # Verificar duplicado en BD
    print("\n⏳ Verificando si ya existe en EDARSAHUB...")
    existe, registro = repository.verificar_duplicado_en_bd(
        execute_sql_query,
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        inv['sistema_origen'],
        inv['server_id'],
        inv['sucursal_id'],
        inv['almacen_id'],
        inv['comentario'],
        inv['folio_inventario'],
        inv['fecha_inventario'],
        inv['estado_inventario_origen']
    )
    
    if existe:
        print("\n" + "=" * 80)
        print("⚠️  REGISTRO YA EXISTE EN EDARSAHUB")
        print("=" * 80)
        print(f"  procesado_id: {registro.get('procesado_id')}")
        print(f"  created_at: {registro.get('created_at')}")
        print(f"  created_by: {registro.get('created_by')}")
        print("\nNo se puede insertar duplicado.")
        return
    
    print("✓ Registro no existe - puede insertarse")
    
    # Mostrar payload completo
    mostrar_payload_completo(inv, identificador, hash_verif)
    
    print("\n⚠️  ADVERTENCIA: Esta operación insertará 1 registro en EDARSAHUB.")
    
    # Pedir confirmación
    try:
        confirmacion = input("\n¿Confirmar inserción? [s/n]: ").strip().lower()
        
        if confirmacion != 's':
            print("\n⚠️  Inserción cancelada por usuario")
            return
            
    except EOFError:
        print("\n⚠️  Inserción cancelada")
        return
    
    # Ejecutar INSERT
    print("\n⏳ Insertando registro...")
    
    exito, mensaje, procesado_id = repository.insertar_folio_procesado(
        execute_sql_query,
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        inv['sistema_origen'],
        inv['server_id'],
        inv['sucursal_id'],
        inv['almacen_id'],
        inv['comentario'],
        inv['folio_inventario'],
        inv['fecha_inventario'],
        inv['estado_inventario_origen'],
        identificador
    )
    
    if exito:
        print("\n" + "=" * 80)
        print("✓ REGISTRO INSERTADO CORRECTAMENTE")
        print("=" * 80)
        print(f"  procesado_id: {procesado_id}")
        print(f"  created_by: {identificador}")
        print("\n  Para rollback usar:")
        print(f"  $ python tests/test_simulacion_controlada.py --rollback {identificador}")
    else:
        print("\n" + "=" * 80)
        print("✗ ERROR AL INSERTAR")
        print("=" * 80)
        print(f"  {mensaje}")


# =============================================================================
# MODO ROLLBACK
# =============================================================================

async def ejecutar_rollback(identificador: str):
    """Ejecuta rollback por identificador."""
    
    print("\n" + "=" * 80)
    print("ROLLBACK CONTROLADO")
    print("=" * 80)
    print(f"\nIdentificador: {identificador}")
    
    # Contar registros
    print("\n⏳ Buscando registros...")
    
    total = repository.contar_registros_por_identificador(
        execute_sql_query,
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        identificador
    )
    
    print(f"Registros encontrados: {total}")
    
    if total == 0:
        print("\n⚠️  No se encontraron registros con ese identificador")
        return
    
    print(f"\n⚠️  Se eliminarán {total} registro(s) de EDARSAHUB.")
    
    # Pedir confirmación
    try:
        confirmacion = input("\n¿Confirmar eliminación? [s/n]: ").strip().lower()
        
        if confirmacion != 's':
            print("\n⚠️  Rollback cancelado por usuario")
            return
            
    except EOFError:
        print("\n⚠️  Rollback cancelado")
        return
    
    # Ejecutar rollback
    print("\n⏳ Ejecutando rollback...")
    
    exito, eliminados, mensaje = repository.rollback_por_identificador(
        execute_sql_query,
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        identificador
    )
    
    if exito:
        print("\n" + "=" * 80)
        print(f"✓ {mensaje}")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print(f"✗ {mensaje}")
        print("=" * 80)


# =============================================================================
# MODO TEST SECUENCIA CONTROLADA
# =============================================================================

def solicitar_confirmacion(mensaje_accion: str) -> str:
    """
    Solicita confirmación al usuario antes de cada acción.
    
    Returns:
        's' = continuar, 'n' = cancelar este paso, 'salir' = abortar todo
    """
    print("\n" + "─" * 80)
    print(f"🔒 PRÓXIMA ACCIÓN: {mensaje_accion}")
    print("─" * 80)
    print("\n  [s] Continuar con esta acción")
    print("  [n] Cancelar este paso (continuar con siguiente)")
    print("  [salir] Abortar toda la secuencia")
    print()
    
    try:
        respuesta = input("Seleccione opción: ").strip().lower()
        if respuesta in ['s', 'n', 'salir']:
            return respuesta
        print("⚠️  Opción no válida. Asumiendo 'n' (cancelar paso)")
        return 'n'
    except (EOFError, KeyboardInterrupt):
        return 'salir'


async def ejecutar_test_secuencia_controlada():
    """
    Ejecuta secuencia de pruebas controlada:
    1. INSERT de 1 registro SOFT
    2. Intento de duplicado (debe fallar)
    3. ROLLBACK del registro insertado
    
    Cada paso requiere confirmación humana.
    """
    print("\n" + "=" * 80)
    print("🔒 TEST SECUENCIA CONTROLADA - CAB-003 FASE 1B.2A")
    print("=" * 80)
    print("""
    Esta secuencia ejecutará 3 pasos con confirmación en cada uno:
    
    PASO 1: Insertar 1 registro SOFT en EDARSAHUB
    PASO 2: Intentar insertar el MISMO registro (debe rechazar por duplicado)
    PASO 3: Ejecutar ROLLBACK para eliminar el registro insertado
    
    ⚠️  Puede cancelar en cualquier momento escribiendo 'salir'
    """)
    print("=" * 80)
    
    # Confirmar inicio
    inicio = solicitar_confirmacion("INICIAR secuencia de pruebas controlada")
    if inicio == 'salir':
        print("\n🛑 Secuencia abortada por usuario")
        return
    if inicio == 'n':
        print("\n⚠️  Inicio cancelado")
        return
    
    # =========================================================================
    # FASE PRELIMINAR: Obtener candidatos
    # =========================================================================
    print("\n" + "=" * 80)
    print("FASE PRELIMINAR: Obteniendo candidatos mediante DRY-RUN...")
    print("=" * 80)
    
    resultado_dry = await ejecutar_dry_run()
    
    # Determinar sistema a usar (SOFT por defecto, o MPRO si se especifica)
    if args.sistema == 'MPRO':
        sistema_filtro = 'MPRO'
        sistema_nombre = 'MPRO'
    else:
        sistema_filtro = 'SOFTRESTAURANT'
        sistema_nombre = 'SOFT'
    
    print(f"\n🔍 Filtrando candidatos para sistema: {sistema_nombre}")
    
    # Filtrar candidatos del sistema seleccionado
    candidatos = [
        i for i in resultado_dry['inventarios'] 
        if i['accion_sugerida'] == 'PROCESAR' and i['sistema_origen'] == sistema_filtro
    ]
    
    if not candidatos:
        print(f"\n⚠️  No hay candidatos {sistema_nombre} disponibles para la prueba")
        return
    
    print(f"✓ Candidatos {sistema_nombre} encontrados: {len(candidatos)}")
    
    # Seleccionar primer candidato
    inv = candidatos[0]
    
    print("\n" + "=" * 80)
    print("CANDIDATO SELECCIONADO PARA PRUEBA")
    print("=" * 80)
    print(f"""
    Sistema:        {inv['sistema_origen']}
    Server ID:      {inv['server_id']}
    Almacén:        {inv['almacen_id']} ({inv.get('almacen_nombre', 'N/A')})
    Folio:          {inv['folio_inventario']}
    Fecha:          {inv['fecha_inventario']}
    """)
    
    # Generar identificador único para esta ejecución
    identificador = repository.generar_identificador_ejecucion()
    hash_verif = repository.generar_hash_verificacion(
        inv['sistema_origen'],
        inv['server_id'],
        inv['sucursal_id'],
        inv['almacen_id'],
        inv['comentario'],
        inv['folio_inventario'],
        inv['fecha_inventario'],
        inv['estado_inventario_origen']
    )
    
    # =========================================================================
    # PASO 1: INSERT DE 1 REGISTRO
    # =========================================================================
    print("\n" + "=" * 80)
    print("PASO 1 DE 3: INSERTAR REGISTRO")
    print("=" * 80)
    
    print("\n📋 PAYLOAD COMPLETO A INSERTAR:")
    print("─" * 60)
    print(f"  {'Campo':<30} │ Valor")
    print(f"  {'─' * 30}┼{'─' * 45}")
    print(f"  {'sistema_origen':<30} │ {inv['sistema_origen']}")
    print(f"  {'server_id':<30} │ {inv['server_id']}")
    print(f"  {'sucursal_id':<30} │ {inv['sucursal_id'] or '(vacío)'}")
    print(f"  {'almacen_id':<30} │ {inv['almacen_id']}")
    print(f"  {'comentario':<30} │ {inv['comentario'] or 'NULL'}")
    print(f"  {'folio_inventario':<30} │ {inv['folio_inventario']}")
    print(f"  {'fecha_inventario':<30} │ {inv['fecha_inventario']}")
    print(f"  {'estado_inventario_origen':<30} │ {inv['estado_inventario_origen'] or 'NULL'}")
    print(f"  {'hash_verificacion':<30} │ {hash_verif[:32]}...")
    print(f"  {'estado':<30} │ EN_PROCESO")
    print(f"  {'created_by':<30} │ {identificador}")
    print("─" * 60)
    
    print(f"\n🔑 IDENTIFICADOR DE EJECUCIÓN: {identificador}")
    print("   (Se usará para ROLLBACK en Paso 3)")
    
    print("\n📝 EXPLICACIÓN:")
    print("   Se insertará 1 registro en la tabla:")
    print("   automatizacion_inventarios_folios_procesados")
    print("   con estado EN_PROCESO y el identificador único mostrado.")
    
    paso1 = solicitar_confirmacion("EJECUTAR INSERT en EDARSAHUB")
    
    registro_insertado = False
    procesado_id = None
    
    if paso1 == 'salir':
        print("\n🛑 Secuencia abortada por usuario")
        return
    elif paso1 == 'n':
        print("\n⚠️  PASO 1 cancelado - no se insertó nada")
    else:
        # Ejecutar INSERT
        print("\n⏳ Ejecutando INSERT...")
        
        exito, mensaje, procesado_id = repository.insertar_folio_procesado(
            execute_sql_query,
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            inv['sistema_origen'],
            inv['server_id'],
            inv['sucursal_id'],
            inv['almacen_id'],
            inv['comentario'],
            inv['folio_inventario'],
            inv['fecha_inventario'],
            inv['estado_inventario_origen'],
            identificador
        )
        
        if exito:
            registro_insertado = True
            print("\n" + "═" * 60)
            print("✅ PASO 1 EXITOSO: REGISTRO INSERTADO")
            print("═" * 60)
            print(f"   procesado_id: {procesado_id}")
            print(f"   created_by:   {identificador}")
        else:
            print("\n" + "═" * 60)
            print("❌ PASO 1 FALLIDO: ERROR AL INSERTAR")
            print("═" * 60)
            print(f"   Error: {mensaje}")
    
    # =========================================================================
    # PASO 2: INTENTO DE DUPLICADO
    # =========================================================================
    print("\n" + "=" * 80)
    print("PASO 2 DE 3: INTENTAR DUPLICADO")
    print("=" * 80)
    
    print("\n📋 Se intentará insertar el MISMO registro:")
    print(f"   Folio: {inv['folio_inventario']}")
    print(f"   Fecha: {inv['fecha_inventario']}")
    print(f"   Almacén: {inv['almacen_id']}")
    
    print("\n📝 EXPLICACIÓN:")
    print("   La constraint UNIQUE de 8 campos debe RECHAZAR este insert.")
    print("   Esto valida que la BD protege contra duplicados.")
    print("   RESULTADO ESPERADO: Error de duplicado")
    
    paso2 = solicitar_confirmacion("INTENTAR INSERT DUPLICADO (debe fallar)")
    
    if paso2 == 'salir':
        print("\n🛑 Secuencia abortada por usuario")
        if registro_insertado:
            print(f"\n⚠️  ATENCIÓN: Quedó 1 registro insertado con ID: {identificador}")
            print("   Para eliminarlo ejecutar:")
            print(f"   $ python tests/test_simulacion_controlada.py --rollback {identificador}")
        return
    elif paso2 == 'n':
        print("\n⚠️  PASO 2 omitido")
    else:
        # Intentar duplicado
        print("\n⏳ Intentando INSERT duplicado...")
        
        # Generar nuevo identificador (diferente) para el intento
        identificador_dup = repository.generar_identificador_ejecucion()
        
        exito_dup, mensaje_dup, _ = repository.insertar_folio_procesado(
            execute_sql_query,
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            inv['sistema_origen'],
            inv['server_id'],
            inv['sucursal_id'],
            inv['almacen_id'],
            inv['comentario'],
            inv['folio_inventario'],
            inv['fecha_inventario'],
            inv['estado_inventario_origen'],
            identificador_dup
        )
        
        if not exito_dup:
            print("\n" + "═" * 60)
            print("✅ PASO 2 EXITOSO: DUPLICADO RECHAZADO (comportamiento correcto)")
            print("═" * 60)
            print(f"   Mensaje: {mensaje_dup}")
        else:
            print("\n" + "═" * 60)
            print("❌ PASO 2 FALLIDO: DUPLICADO FUE ACEPTADO (ERROR CRÍTICO)")
            print("═" * 60)
            print("   La constraint UNIQUE no funcionó correctamente")
    
    # =========================================================================
    # PASO 3: ROLLBACK
    # =========================================================================
    print("\n" + "=" * 80)
    print("PASO 3 DE 3: EJECUTAR ROLLBACK")
    print("=" * 80)
    
    if not registro_insertado:
        print("\n⚠️  No hay registro para eliminar (Paso 1 fue cancelado o falló)")
        print("   Saltando Paso 3...")
    else:
        # Contar registros antes
        total_antes = repository.contar_registros_por_identificador(
            execute_sql_query,
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            identificador
        )
        
        print("\n📋 ROLLBACK A EJECUTAR:")
        print(f"   Identificador: {identificador}")
        print(f"   Registros a eliminar: {total_antes}")
        
        print("\n📝 EXPLICACIÓN:")
        print(f"   Se ejecutará DELETE WHERE created_by = '{identificador}'")
        print("   Esto eliminará únicamente los registros insertados en esta sesión.")
        
        paso3 = solicitar_confirmacion("EJECUTAR ROLLBACK (eliminar registro)")
        
        if paso3 == 'salir':
            print("\n🛑 Secuencia abortada por usuario")
            print(f"\n⚠️  ATENCIÓN: Quedó 1 registro insertado con ID: {identificador}")
            print("   Para eliminarlo ejecutar:")
            print(f"   $ python tests/test_simulacion_controlada.py --rollback {identificador}")
            return
        elif paso3 == 'n':
            print("\n⚠️  PASO 3 omitido")
            print(f"\n⚠️  ATENCIÓN: Quedó 1 registro insertado con ID: {identificador}")
            print("   Para eliminarlo ejecutar:")
            print(f"   $ python tests/test_simulacion_controlada.py --rollback {identificador}")
        else:
            # Ejecutar rollback
            print("\n⏳ Ejecutando ROLLBACK...")
            
            exito_rb, eliminados, mensaje_rb = repository.rollback_por_identificador(
                execute_sql_query,
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                identificador
            )
            
            if exito_rb and eliminados > 0:
                print("\n" + "═" * 60)
                print("✅ PASO 3 EXITOSO: ROLLBACK COMPLETADO")
                print("═" * 60)
                print(f"   Registros eliminados: {eliminados}")
                print(f"   Identificador: {identificador}")
            elif exito_rb and eliminados == 0:
                print("\n" + "═" * 60)
                print("⚠️  PASO 3: NO SE ENCONTRARON REGISTROS")
                print("═" * 60)
            else:
                print("\n" + "═" * 60)
                print("❌ PASO 3 FALLIDO: ERROR EN ROLLBACK")
                print("═" * 60)
                print(f"   Error: {mensaje_rb}")
    
    # =========================================================================
    # RESUMEN FINAL
    # =========================================================================
    print("\n" + "=" * 80)
    print("RESUMEN DE SECUENCIA CONTROLADA")
    print("=" * 80)
    print(f"""
    Identificador de ejecución: {identificador}
    
    PASO 1 (INSERT):     {'✅ Exitoso' if registro_insertado else '⏭️  Omitido/Fallido'}
    PASO 2 (DUPLICADO):  {'✅ Rechazado correctamente' if paso2 == 's' else '⏭️  Omitido'}
    PASO 3 (ROLLBACK):   {'✅ Ejecutado' if (registro_insertado and paso3 == 's') else '⏭️  Omitido'}
    """)
    print("=" * 80)


# =============================================================================
# MODO PERSISTIR LOTE SOFT (FASE 1B.3A)
# =============================================================================
# Límites estrictos:
#   - SOLO sistema SOFT (MPRO no habilitado)
#   - MÁXIMO 2 registros por lote
#   - Confirmación individual por cada registro
#   - Detenerse inmediatamente ante cualquier error
#   - Rollback por identificador único de lote
# =============================================================================

LIMITE_LOTE_FASE_1B3A = 2  # Máximo 2 registros - NO MODIFICAR


def generar_identificador_lote() -> str:
    """
    Genera identificador único para lote Fase 1B.3A.
    Formato: CAB003_FASE1B3A_LOTE_YYYYMMDD_HHMMSS
    """
    return f"CAB003_FASE1B3A_LOTE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def mostrar_payload_registro_lote(inv: dict, numero: int, total: int, identificador: str, hash_verif: str, es_duplicado: bool):
    """Muestra el payload completo de un registro del lote."""
    print("\n" + "┌" + "─" * 78 + "┐")
    print(f"│ REGISTRO {numero} de {total}".ljust(79) + "│")
    print("├" + "─" * 78 + "┤")
    print(f"│  {'Campo':<28} │ {'Valor':<45} │")
    print("├" + "─" * 30 + "┼" + "─" * 47 + "┤")
    print(f"│  {'sistema_origen':<28} │ {inv['sistema_origen']:<45} │")
    print(f"│  {'server_id':<28} │ {inv['server_id']:<45} │")
    print(f"│  {'sucursal_id':<28} │ {(inv['sucursal_id'] or '(vacío)'):<45} │")
    print(f"│  {'almacen_id':<28} │ {inv['almacen_id']:<45} │")
    print(f"│  {'comentario':<28} │ {(inv['comentario'] or 'NULL'):<45} │")
    print(f"│  {'folio_inventario':<28} │ {inv['folio_inventario']:<45} │")
    print(f"│  {'fecha_inventario':<28} │ {str(inv['fecha_inventario']):<45} │")
    print(f"│  {'estado_inventario_origen':<28} │ {(inv['estado_inventario_origen'] or 'NULL'):<45} │")
    print(f"│  {'hash_verificacion':<28} │ {hash_verif[:40]+'...':<45} │")
    print(f"│  {'estado':<28} │ {'EN_PROCESO':<45} │")
    print(f"│  {'created_by':<28} │ {identificador:<45} │")
    print("├" + "─" * 30 + "┼" + "─" * 47 + "┤")
    
    if es_duplicado:
        print(f"│  {'VALIDACIÓN DUPLICADO':<28} │ {'❌ YA EXISTE - SE OMITIRÁ':<45} │")
    else:
        print(f"│  {'VALIDACIÓN DUPLICADO':<28} │ {'✅ NO EXISTE - PUEDE INSERTARSE':<45} │")
    
    print("└" + "─" * 30 + "┴" + "─" * 47 + "┘")


async def ejecutar_persistir_lote_soft():
    """
    Fase 1B.3A: Persistir lote de máximo 2 registros SOFT.
    
    Características:
    - SOLO SOFT (MPRO no habilitado)
    - Máximo 2 registros
    - Confirmación individual por cada registro
    - Detenerse inmediatamente ante error
    - Rollback por identificador único
    """
    print("\n" + "=" * 80)
    print("🔒 FASE 1B.3A - PERSISTIR LOTE SOFT (MÁXIMO 2 REGISTROS)")
    print("=" * 80)
    print("""
    Este proceso insertará hasta 2 registros SOFT con:
    
    • Verificación previa de candidatos elegibles
    • Validación de duplicados por cada registro
    • Confirmación INDIVIDUAL antes de cada inserción
    • Detención INMEDIATA ante cualquier error
    • Identificador único de lote para rollback
    
    ⚠️  Sistema: SOLO SOFTRESTAURANT (MPRO no habilitado)
    ⚠️  Puede cancelar en cualquier momento con 'salir'
    """)
    print("=" * 80)
    
    # =========================================================================
    # PASO 0: CONFIRMACIÓN DE INICIO
    # =========================================================================
    inicio = solicitar_confirmacion("INICIAR proceso de lote SOFT (máximo 2 registros)")
    if inicio == 'salir':
        print("\n🛑 Proceso abortado por usuario")
        return
    if inicio == 'n':
        print("\n⚠️  Inicio cancelado")
        return
    
    # =========================================================================
    # PASO 1: VERIFICACIÓN PREVIA DE CANDIDATOS
    # =========================================================================
    print("\n" + "=" * 80)
    print("PASO 1: VERIFICACIÓN PREVIA DE CANDIDATOS SOFT")
    print("=" * 80)
    print("\n⏳ Ejecutando dry-run para identificar candidatos elegibles...")
    
    resultado_dry = await ejecutar_dry_run()
    
    # Filtrar SOLO SOFT con accion_sugerida='PROCESAR'
    candidatos_soft = [
        i for i in resultado_dry['inventarios'] 
        if i['accion_sugerida'] == 'PROCESAR' and i['sistema_origen'] == 'SOFTRESTAURANT'
    ]
    
    print("\n" + "─" * 80)
    print(f"CANDIDATOS SOFT ELEGIBLES (accion_sugerida = 'PROCESAR'): {len(candidatos_soft)}")
    print(f"REGISTROS A PROCESAR EN ESTE LOTE: {min(len(candidatos_soft), LIMITE_LOTE_FASE_1B3A)} (máximo {LIMITE_LOTE_FASE_1B3A})")
    print("─" * 80)
    
    if len(candidatos_soft) == 0:
        print("\n⚠️  No hay candidatos SOFT elegibles para procesar")
        return
    
    # Limitar a máximo 2
    candidatos_lote = candidatos_soft[:LIMITE_LOTE_FASE_1B3A]
    
    continuar = solicitar_confirmacion(f"CONTINUAR con selección de {len(candidatos_lote)} registro(s)")
    if continuar == 'salir':
        print("\n🛑 Proceso abortado por usuario")
        return
    if continuar == 'n':
        print("\n⚠️  Proceso cancelado")
        return
    
    # =========================================================================
    # PASO 2: VALIDACIÓN DE DUPLICADOS
    # =========================================================================
    print("\n" + "=" * 80)
    print("PASO 2: VALIDACIÓN PREVIA DE DUPLICADOS")
    print("=" * 80)
    
    candidatos_validados = []
    
    for i, inv in enumerate(candidatos_lote, 1):
        print(f"\n⏳ Verificando registro {i}/{len(candidatos_lote)}...")
        
        existe, registro = repository.verificar_duplicado_en_bd(
            execute_sql_query,
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            inv['sistema_origen'],
            inv['server_id'],
            inv['sucursal_id'],
            inv['almacen_id'],
            inv['comentario'],
            inv['folio_inventario'],
            inv['fecha_inventario'],
            inv['estado_inventario_origen']
        )
        
        candidatos_validados.append({
            'inventario': inv,
            'es_duplicado': existe,
            'registro_existente': registro
        })
        
        if existe:
            print(f"   ❌ Registro {i}: YA EXISTE en EDARSAHUB - se omitirá")
        else:
            print(f"   ✅ Registro {i}: No existe - puede insertarse")
    
    # Filtrar solo los no duplicados
    candidatos_insertables = [c for c in candidatos_validados if not c['es_duplicado']]
    
    if len(candidatos_insertables) == 0:
        print("\n⚠️  Todos los candidatos ya existen en EDARSAHUB")
        print("   No hay registros nuevos para insertar")
        return
    
    print(f"\n✓ Registros válidos para insertar: {len(candidatos_insertables)}")
    
    # =========================================================================
    # PASO 3: GENERAR IDENTIFICADOR ÚNICO DE LOTE
    # =========================================================================
    identificador_lote = generar_identificador_lote()
    
    print("\n" + "=" * 80)
    print("PASO 3: IDENTIFICADOR DE LOTE GENERADO")
    print("=" * 80)
    print(f"\n🔑 IDENTIFICADOR: {identificador_lote}")
    print("   (Se usará para ROLLBACK si es necesario)")
    
    # =========================================================================
    # PASO 4: MOSTRAR PAYLOADS Y CONFIRMAR CADA REGISTRO
    # =========================================================================
    print("\n" + "=" * 80)
    print("PASO 4: INSERCIÓN CON CONFIRMACIÓN POR REGISTRO")
    print("=" * 80)
    
    registros_insertados = []
    registros_omitidos = []
    registros_fallidos = []
    error_ocurrido = False
    
    for i, candidato in enumerate(candidatos_validados, 1):
        inv = candidato['inventario']
        es_duplicado = candidato['es_duplicado']
        
        # Generar hash para mostrar
        hash_verif = repository.generar_hash_verificacion(
            inv['sistema_origen'],
            inv['server_id'],
            inv['sucursal_id'],
            inv['almacen_id'],
            inv['comentario'],
            inv['folio_inventario'],
            inv['fecha_inventario'],
            inv['estado_inventario_origen']
        )
        
        # Mostrar payload completo
        mostrar_payload_registro_lote(inv, i, len(candidatos_validados), identificador_lote, hash_verif, es_duplicado)
        
        if es_duplicado:
            print(f"\n⏭️  Registro {i}/{len(candidatos_validados)}: OMITIDO (ya existe)")
            registros_omitidos.append({
                'numero': i,
                'folio': inv['folio_inventario'],
                'razon': 'Duplicado'
            })
            continue
        
        # Solicitar confirmación para este registro específico
        confirmacion = solicitar_confirmacion(f"Registro {i}/{len(candidatos_validados)} → ¿Insertar este registro?")
        
        if confirmacion == 'salir':
            print("\n🛑 LOTE DETENIDO POR USUARIO")
            error_ocurrido = True
            # Marcar restantes como no insertados
            for j in range(i, len(candidatos_validados) + 1):
                if j > i or (j == i and not candidatos_validados[j-1]['es_duplicado']):
                    registros_fallidos.append({
                        'numero': j,
                        'folio': candidatos_validados[j-1]['inventario']['folio_inventario'],
                        'error': 'Abortado por usuario'
                    })
            break
        
        if confirmacion == 'n':
            print(f"\n⏭️  Registro {i}/{len(candidatos_validados)}: OMITIDO por usuario")
            registros_omitidos.append({
                'numero': i,
                'folio': inv['folio_inventario'],
                'razon': 'Omitido por usuario'
            })
            continue
        
        # Ejecutar INSERT
        print(f"\n⏳ Insertando registro {i}/{len(candidatos_validados)}...")
        
        try:
            exito, mensaje, procesado_id = repository.insertar_folio_procesado(
                execute_sql_query,
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                inv['sistema_origen'],
                inv['server_id'],
                inv['sucursal_id'],
                inv['almacen_id'],
                inv['comentario'],
                inv['folio_inventario'],
                inv['fecha_inventario'],
                inv['estado_inventario_origen'],
                identificador_lote
            )
            
            if exito:
                print(f"   ✅ INSERTADO: procesado_id = {procesado_id}")
                registros_insertados.append({
                    'numero': i,
                    'folio': inv['folio_inventario'],
                    'procesado_id': procesado_id
                })
            else:
                print(f"   ❌ ERROR: {mensaje}")
                registros_fallidos.append({
                    'numero': i,
                    'folio': inv['folio_inventario'],
                    'error': mensaje
                })
                error_ocurrido = True
                # Marcar restantes como no insertados
                for j in range(i + 1, len(candidatos_validados) + 1):
                    registros_fallidos.append({
                        'numero': j,
                        'folio': candidatos_validados[j-1]['inventario']['folio_inventario'],
                        'error': 'No procesado (lote detenido por error anterior)'
                    })
                break  # DETENERSE INMEDIATAMENTE
                
        except Exception as e:
            print(f"   ❌ EXCEPCIÓN: {e}")
            registros_fallidos.append({
                'numero': i,
                'folio': inv['folio_inventario'],
                'error': str(e)
            })
            error_ocurrido = True
            # Marcar restantes como no insertados
            for j in range(i + 1, len(candidatos_validados) + 1):
                registros_fallidos.append({
                    'numero': j,
                    'folio': candidatos_validados[j-1]['inventario']['folio_inventario'],
                    'error': 'No procesado (lote detenido por error anterior)'
                })
            break  # DETENERSE INMEDIATAMENTE
    
    # =========================================================================
    # PASO 5: RESUMEN FINAL
    # =========================================================================
    print("\n" + "=" * 80)
    if error_ocurrido:
        print("🛑 LOTE DETENIDO - RESUMEN PARCIAL")
    else:
        print("✅ LOTE COMPLETADO - RESUMEN FINAL")
    print("=" * 80)
    
    print(f"""
    Identificador de lote: {identificador_lote}
    Sistema: SOFTRESTAURANT
    
    INSERTADOS EXITOSAMENTE: {len(registros_insertados)}""")
    
    for r in registros_insertados:
        print(f"      • Registro {r['numero']}: {r['folio']} → procesado_id: {r['procesado_id']}")
    
    print(f"""
    OMITIDOS: {len(registros_omitidos)}""")
    
    for r in registros_omitidos:
        print(f"      • Registro {r['numero']}: {r['folio']} → {r['razon']}")
    
    print(f"""
    NO INSERTADOS (error/abortado): {len(registros_fallidos)}""")
    
    for r in registros_fallidos:
        print(f"      • Registro {r['numero']}: {r['folio']} → {r['error']}")
    
    # Mostrar comando de rollback si hubo inserciones
    if len(registros_insertados) > 0:
        print(f"""
    ─────────────────────────────────────────────────────────────────────────────
    Para ROLLBACK de este lote ejecutar:
    $ python tests/test_simulacion_controlada.py --rollback {identificador_lote}
    ─────────────────────────────────────────────────────────────────────────────
    """)
    
    print("=" * 80)


# =============================================================================
# MODO PERSISTIR LOTE MPRO (FASE 1B.3B)
# =============================================================================
# Límites estrictos HARDCODEADOS:
#   - SOLO sistema MPRO (SOFT no habilitado)
#   - MÁXIMO 1 registro (lote mínimo)
#   - Confirmación obligatoria
#   - Detenerse inmediatamente ante cualquier error
#   - Rollback por identificador único de lote
# =============================================================================

LIMITE_LOTE_FASE_1B3B = 1  # Máximo 1 registro MPRO - NO MODIFICAR


def generar_identificador_lote_mpro() -> str:
    """
    Genera identificador único para lote MPRO Fase 1B.3B.
    Formato: CAB003_FASE1B3B_LOTE_YYYYMMDD_HHMMSS
    """
    return f"CAB003_FASE1B3B_LOTE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def mostrar_payload_registro_mpro(inv: dict, identificador: str, hash_verif: str, es_duplicado: bool):
    """Muestra el payload completo de un registro MPRO."""
    print("\n" + "┌" + "─" * 78 + "┐")
    print("│ REGISTRO 1 de 1 (MPRO)".ljust(79) + "│")
    print("├" + "─" * 78 + "┤")
    print(f"│  {'Campo':<28} │ {'Valor':<45} │")
    print("├" + "─" * 30 + "┼" + "─" * 47 + "┤")
    print(f"│  {'sistema_origen':<28} │ {inv['sistema_origen']:<45} │")
    print(f"│  {'server_id':<28} │ {inv['server_id']:<45} │")
    print(f"│  {'sucursal_id':<28} │ {(inv['sucursal_id'] or '(vacío)'):<45} │")
    print(f"│  {'almacen_id':<28} │ {inv['almacen_id']:<45} │")
    print(f"│  {'comentario':<28} │ {(inv['comentario'] or 'NULL'):<45} │")
    print(f"│  {'folio_inventario':<28} │ {inv['folio_inventario']:<45} │")
    print(f"│  {'fecha_inventario':<28} │ {str(inv['fecha_inventario']):<45} │")
    print(f"│  {'estado_inventario_origen':<28} │ {(inv['estado_inventario_origen'] or 'NULL'):<45} │")
    print(f"│  {'hash_verificacion':<28} │ {hash_verif[:40]+'...':<45} │")
    print(f"│  {'estado':<28} │ {'EN_PROCESO':<45} │")
    print(f"│  {'created_by':<28} │ {identificador:<45} │")
    print("├" + "─" * 30 + "┼" + "─" * 47 + "┤")
    
    if es_duplicado:
        print(f"│  {'VALIDACIÓN DUPLICADO':<28} │ {'❌ YA EXISTE - ABORTANDO':<45} │")
    else:
        print(f"│  {'VALIDACIÓN DUPLICADO':<28} │ {'✅ NO EXISTE - PUEDE INSERTARSE':<45} │")
    
    print("└" + "─" * 30 + "┴" + "─" * 47 + "┘")


async def ejecutar_persistir_lote_mpro():
    """
    Fase 1B.3B: Persistir lote de 1 registro MPRO.
    
    Características HARDCODEADAS:
    - SOLO MPRO (SOFT no habilitado)
    - Máximo 1 registro (lote mínimo)
    - Confirmación obligatoria
    - Detenerse inmediatamente ante error
    - Rollback por identificador único
    """
    print("\n" + "=" * 80)
    print("🔒 FASE 1B.3B - PERSISTIR LOTE MPRO (1 REGISTRO)")
    print("=" * 80)
    print("""
    Este proceso insertará 1 registro MPRO con:
    
    • Verificación previa de candidatos elegibles
    • Validación de duplicado
    • Confirmación OBLIGATORIA antes de inserción
    • Detención INMEDIATA ante cualquier error
    • Identificador único de lote para rollback
    
    ⚠️  Sistema: SOLO MPRO (SOFT no habilitado)
    ⚠️  Máximo: 1 registro (lote mínimo)
    ⚠️  Puede cancelar en cualquier momento con 'salir'
    """)
    print("=" * 80)
    
    # =========================================================================
    # PASO 0: CONFIRMACIÓN DE INICIO
    # =========================================================================
    inicio = solicitar_confirmacion("INICIAR proceso lote MPRO (1 registro)")
    if inicio == 'salir':
        print("\n🛑 Proceso abortado por usuario")
        return
    if inicio == 'n':
        print("\n⚠️  Inicio cancelado")
        return
    
    # =========================================================================
    # PASO 1: VERIFICACIÓN PREVIA DE CANDIDATOS MPRO
    # =========================================================================
    print("\n" + "=" * 80)
    print("PASO 1: VERIFICACIÓN PREVIA DE CANDIDATOS MPRO")
    print("=" * 80)
    print("\n⏳ Ejecutando dry-run para identificar candidatos elegibles...")
    
    resultado_dry = await ejecutar_dry_run()
    
    # Filtrar SOLO MPRO con accion_sugerida='PROCESAR'
    candidatos_mpro = [
        i for i in resultado_dry['inventarios'] 
        if i['accion_sugerida'] == 'PROCESAR' and i['sistema_origen'] == 'MPRO'
    ]
    
    print("\n" + "─" * 80)
    print(f"CANDIDATOS MPRO ELEGIBLES (accion_sugerida = 'PROCESAR'): {len(candidatos_mpro)}")
    print(f"REGISTRO A PROCESAR EN ESTE LOTE: {min(len(candidatos_mpro), LIMITE_LOTE_FASE_1B3B)} (máximo {LIMITE_LOTE_FASE_1B3B})")
    print("─" * 80)
    
    if len(candidatos_mpro) == 0:
        print("\n⚠️  No hay candidatos MPRO elegibles para procesar")
        print("   Proceso abortado")
        return
    
    # Tomar SOLO 1 registro (HARDCODEADO)
    inv = candidatos_mpro[0]
    
    continuar = solicitar_confirmacion("CONTINUAR con selección de 1 registro MPRO")
    if continuar == 'salir':
        print("\n🛑 Proceso abortado por usuario")
        return
    if continuar == 'n':
        print("\n⚠️  Proceso cancelado")
        return
    
    # =========================================================================
    # PASO 2: VALIDACIÓN DE DUPLICADO
    # =========================================================================
    print("\n" + "=" * 80)
    print("PASO 2: VALIDACIÓN DE DUPLICADO")
    print("=" * 80)
    
    print("\n⏳ Verificando registro 1/1...")
    
    existe, registro = repository.verificar_duplicado_en_bd(
        execute_sql_query,
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        inv['sistema_origen'],
        inv['server_id'],
        inv['sucursal_id'],
        inv['almacen_id'],
        inv['comentario'],
        inv['folio_inventario'],
        inv['fecha_inventario'],
        inv['estado_inventario_origen']
    )
    
    if existe:
        print("   ❌ Registro 1/1: YA EXISTE en EDARSAHUB")
        print("\n⚠️  El único candidato ya está procesado")
        print("   Proceso abortado - no hay registros nuevos para insertar")
        return
    
    print("   ✅ Registro 1/1: No existe - puede insertarse")
    
    # =========================================================================
    # PASO 3: GENERAR IDENTIFICADOR ÚNICO DE LOTE
    # =========================================================================
    identificador_lote = generar_identificador_lote_mpro()
    
    print("\n" + "=" * 80)
    print("PASO 3: IDENTIFICADOR DE LOTE GENERADO")
    print("=" * 80)
    print(f"\n🔑 IDENTIFICADOR: {identificador_lote}")
    print("   (Se usará para ROLLBACK si es necesario)")
    
    # =========================================================================
    # PASO 4: MOSTRAR PAYLOAD Y CONFIRMAR REGISTRO
    # =========================================================================
    print("\n" + "=" * 80)
    print("PASO 4: CONFIRMACIÓN DE INSERCIÓN")
    print("=" * 80)
    
    # Generar hash para mostrar
    hash_verif = repository.generar_hash_verificacion(
        inv['sistema_origen'],
        inv['server_id'],
        inv['sucursal_id'],
        inv['almacen_id'],
        inv['comentario'],
        inv['folio_inventario'],
        inv['fecha_inventario'],
        inv['estado_inventario_origen']
    )
    
    # Mostrar payload completo
    mostrar_payload_registro_mpro(inv, identificador_lote, hash_verif, False)
    
    # Solicitar confirmación obligatoria
    confirmacion = solicitar_confirmacion("Registro 1/1 → ¿Insertar este registro MPRO?")
    
    if confirmacion == 'salir':
        print("\n🛑 Proceso abortado por usuario")
        return
    
    if confirmacion == 'n':
        print("\n⚠️  Inserción cancelada por usuario")
        print("   No se insertó ningún registro")
        return
    
    # =========================================================================
    # PASO 5: INSERTAR REGISTRO
    # =========================================================================
    print("\n⏳ Insertando registro 1/1...")
    
    try:
        exito, mensaje, procesado_id = repository.insertar_folio_procesado(
            execute_sql_query,
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            inv['sistema_origen'],
            inv['server_id'],
            inv['sucursal_id'],
            inv['almacen_id'],
            inv['comentario'],
            inv['folio_inventario'],
            inv['fecha_inventario'],
            inv['estado_inventario_origen'],
            identificador_lote
        )
        
        if not exito:
            # DETENERSE INMEDIATAMENTE
            print("\n" + "=" * 80)
            print("🛑 ERROR - INSERCIÓN FALLIDA")
            print("=" * 80)
            print(f"\n   Error: {mensaje}")
            print(f"\n   Identificador de lote: {identificador_lote}")
            print("\n   ⚠️  DETENCIÓN INMEDIATA - No se insertó ningún registro")
            print("\n   Si hubo algún registro parcial (improbable), usar rollback:")
            print(f"   $ python tests/test_simulacion_controlada.py --rollback {identificador_lote}")
            print("\n" + "=" * 80)
            return
        
        # =====================================================================
        # PASO 6: RESUMEN EXITOSO
        # =====================================================================
        print("\n" + "=" * 80)
        print("✅ LOTE COMPLETADO - RESUMEN FINAL")
        print("=" * 80)
        
        print(f"""
    Identificador de lote: {identificador_lote}
    Sistema: MPRO
    
    INSERTADO EXITOSAMENTE: 1
      • Registro 1/1: {inv['folio_inventario']} → procesado_id: {procesado_id}

    Detalles del registro:
      • Sucursal: {inv['sucursal_id']}
      • Almacén: {inv['almacen_id']}
      • Comentario: {inv['comentario']}
      • Estado origen: {inv['estado_inventario_origen']}

    ─────────────────────────────────────────────────────────────────────────────
    Para ROLLBACK de este registro ejecutar:
    $ python tests/test_simulacion_controlada.py --rollback {identificador_lote}
    ─────────────────────────────────────────────────────────────────────────────
    """)
        print("=" * 80)
        
    except Exception as e:
        # DETENERSE INMEDIATAMENTE
        print("\n" + "=" * 80)
        print("🛑 EXCEPCIÓN - INSERCIÓN FALLIDA")
        print("=" * 80)
        print(f"\n   Excepción: {e}")
        print(f"\n   Identificador de lote: {identificador_lote}")
        print("\n   ⚠️  DETENCIÓN INMEDIATA")
        print("\n   Si hubo algún registro parcial, usar rollback:")
        print(f"   $ python tests/test_simulacion_controlada.py --rollback {identificador_lote}")
        print("\n" + "=" * 80)
        return


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

async def main():
    if MODO == 'ROLLBACK':
        await ejecutar_rollback(args.rollback)
    elif MODO == 'PERSISTIR_UNO':
        await ejecutar_persistir_uno()
    elif MODO == 'TEST_SECUENCIA_CONTROLADA':
        await ejecutar_test_secuencia_controlada()
    elif MODO == 'PERSISTIR_LOTE_SOFT':
        await ejecutar_persistir_lote_soft()
    elif MODO == 'PERSISTIR_LOTE_MPRO':
        await ejecutar_persistir_lote_mpro()
    else:
        await ejecutar_dry_run()
        print("\n⚠️  RECORDATORIO: Este fue un DRY-RUN")
        print("   - NO se insertó nada en EDARSAHUB")
        print("   - NO se modificó ningún sistema origen")
        print("   - Para persistir: --persistir-uno")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Ejecución cancelada por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
