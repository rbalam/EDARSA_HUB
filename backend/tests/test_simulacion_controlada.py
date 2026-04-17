#!/usr/bin/env python3
# =============================================================================
# CAB-003 FASE 1B.1 - SCRIPT DE SIMULACIÓN CONTROLADA
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
#     6. NO realiza INSERT/UPDATE en ninguna tabla
#     7. Solo ejecuta operaciones de LECTURA (SELECT)
#    
#     Para ejecutar:
#     $ cd /app/backend
#     $ python tests/test_simulacion_controlada.py
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
from datetime import datetime
from dataclasses import asdict

# Agregar path del backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("=" * 80)
print("CAB-003 FASE 1B.1 - SIMULACIÓN CONTROLADA (DRY-RUN)")
print("=" * 80)
print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
print(f"Modo: DRY-RUN (solo lectura, sin persistencia)")
print("=" * 80)
print()

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# EDARSAHUB conexión
EDARSAHUB_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'HRLectura',
    'password': 'National09$'
}

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
    # Limpiar comillas si existen
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


# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

async def main():
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
    
    # =========================================================================
    # DRY-RUN SOFT
    # =========================================================================
    print("\n" + "=" * 80)
    print("FASE 2: Detección DRY-RUN en SoftRestaurant")
    print("=" * 80)
    
    for server in soft_servers:
        print(f"\n▶ Escaneando: {server['name']}")
        print(f"  Host: {server['host']}")
        print(f"  Database: {server['database']}")
        
        try:
            # Obtener folios ya procesados
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
            
            # Detectar inventarios
            detectados = detectar_inventarios_soft(
                execute_sql_query,
                server,
                folios_procesados
            )
            
            print(f"  Inventarios detectados: {len(detectados)}")
            
            for i, det in enumerate(detectados, 1):
                inv_dict = asdict(det)
                print_inventario(inv_dict, i)
                todos_detectados.append(inv_dict)
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # =========================================================================
    # DRY-RUN MPRO
    # =========================================================================
    print("\n" + "=" * 80)
    print("FASE 3: Detección DRY-RUN en MPRO")
    print("=" * 80)
    
    for server in mpro_servers:
        print(f"\n▶ Escaneando: {server['name']}")
        print(f"  Host: {server['host']}")
        print(f"  Database: {server['database']}")
        
        try:
            # Obtener folios ya procesados
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
            
            # Detectar inventarios
            detectados = detectar_inventarios_mpro(
                execute_sql_query,
                server,
                folios_procesados
            )
            
            print(f"  Inventarios detectados: {len(detectados)}")
            
            # Mostrar solo los primeros 10 para no saturar
            for i, det in enumerate(detectados[:10], 1):
                inv_dict = asdict(det)
                print_inventario(inv_dict, i)
                todos_detectados.append(inv_dict)
            
            if len(detectados) > 10:
                print(f"\n  ... y {len(detectados) - 10} más (truncado)")
                # Agregar el resto sin imprimir
                for det in detectados[10:]:
                    todos_detectados.append(asdict(det))
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # =========================================================================
    # RESUMEN
    # =========================================================================
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
    
    # Guardar resultado JSON
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
    
    print("\n" + "=" * 80)
    print("DRY-RUN COMPLETADO")
    print("=" * 80)
    print("\n⚠️  RECORDATORIO: Este fue un DRY-RUN")
    print("   - NO se insertó nada en EDARSAHUB")
    print("   - NO se modificó ningún sistema origen")
    print("   - Para proceder a Fase 1B.2, requiere autorización")
    print()
    
    return resultado


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    try:
        resultado = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Ejecución cancelada por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
