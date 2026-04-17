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
#     $ python tests/test_simulacion_controlada.py              # Dry-run
#     $ python tests/test_simulacion_controlada.py --persistir-uno   # Persistir 1
#     $ python tests/test_simulacion_controlada.py --rollback ID     # Rollback
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
  python tests/test_simulacion_controlada.py                    # Dry-run
  python tests/test_simulacion_controlada.py --persistir-uno    # Persistir 1 registro
  python tests/test_simulacion_controlada.py --rollback ID      # Rollback por ID
    """
)
parser.add_argument('--persistir-uno', action='store_true', 
                    help='Modo de persistencia: insertar 1 registro manual')
parser.add_argument('--rollback', type=str, metavar='ID',
                    help='Rollback por identificador de ejecución')
parser.add_argument('--sistema', type=str, choices=['SOFT', 'MPRO'],
                    help='Filtrar por sistema (solo para --persistir-uno)')

args = parser.parse_args()

# Determinar modo
if args.rollback:
    MODO = 'ROLLBACK'
elif args.persistir_uno:
    MODO = 'PERSISTIR_UNO'
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
        print(f"\n  Para rollback usar:")
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
# PUNTO DE ENTRADA
# =============================================================================

async def main():
    if MODO == 'ROLLBACK':
        await ejecutar_rollback(args.rollback)
    elif MODO == 'PERSISTIR_UNO':
        await ejecutar_persistir_uno()
    else:
        resultado = await ejecutar_dry_run()
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
