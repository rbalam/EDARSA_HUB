"""
EDARSA HUB - Script RBAC para Tablajería
=========================================
Crea módulos, permisos y asignaciones de roles para el módulo de Tablajería.

Ejecutar una sola vez para configurar RBAC.

Uso:
    python create_tablajeria_rbac.py
"""

import pymssql
import os
from datetime import datetime

# Configuración de conexión
DB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_HOST', os.getenv('EDARSAHUB_SQL_HOST')),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'username': os.environ.get('EDARSAHUB_USERNAME', os.getenv('EDARSAHUB_SQL_USER')),
    'password': os.environ.get('EDARSAHUB_PASSWORD', os.getenv('EDARSAHUB_SQL_PASSWORD'))
}


def get_connection():
    return pymssql.connect(
        server=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        autocommit=False
    )


def create_tablajeria_modules(cursor):
    """Crea los módulos de Tablajería en Usuario_Modulos."""
    
    now = datetime.utcnow()
    
    # Módulos a crear
    modulos = [
        # Módulo padre
        {
            'codigo': 'tablajeria',
            'nombre': 'Tablajería',
            'descripcion': 'Módulo de producción y transformación de insumos',
            'tipo': 'MODULO',
            'ruta': '/tablajeria',
            'icono': 'Scissors',
            'orden': 50,
            'visible': True,
            'padre_codigo': None
        },
        # Submódulos
        {
            'codigo': 'tablajeria.dashboard',
            'nombre': 'Dashboard Tablajería',
            'descripcion': 'Panel principal de tablajería',
            'tipo': 'SUBMODULO',
            'ruta': '/tablajeria/dashboard',
            'icono': 'LayoutDashboard',
            'orden': 1,
            'visible': True,
            'padre_codigo': 'tablajeria'
        },
        {
            'codigo': 'tablajeria.ordenes',
            'nombre': 'Órdenes de Tablaje',
            'descripcion': 'Gestión de órdenes de producción',
            'tipo': 'SUBMODULO',
            'ruta': '/tablajeria/ordenes',
            'icono': 'ClipboardList',
            'orden': 2,
            'visible': True,
            'padre_codigo': 'tablajeria'
        },
        {
            'codigo': 'tablajeria.captura_directa',
            'nombre': 'Captura Directa',
            'descripcion': 'Crear órdenes sin plantilla predefinida',
            'tipo': 'SUBMODULO',
            'ruta': '/tablajeria/captura-directa',
            'icono': 'FilePlus',
            'orden': 3,
            'visible': True,
            'padre_codigo': 'tablajeria'
        },
        {
            'codigo': 'tablajeria.plantillas',
            'nombre': 'Plantillas',
            'descripcion': 'Gestión de plantillas de transformación',
            'tipo': 'SUBMODULO',
            'ruta': '/tablajeria/plantillas',
            'icono': 'FileText',
            'orden': 4,
            'visible': True,
            'padre_codigo': 'tablajeria'
        },
        {
            'codigo': 'tablajeria.rendimientos',
            'nombre': 'Rendimientos',
            'descripcion': 'Histórico de rendimientos',
            'tipo': 'SUBMODULO',
            'ruta': '/tablajeria/rendimientos',
            'icono': 'TrendingUp',
            'orden': 5,
            'visible': True,
            'padre_codigo': 'tablajeria'
        },
        {
            'codigo': 'tablajeria.mermas',
            'nombre': 'Mermas',
            'descripcion': 'Control de mermas',
            'tipo': 'SUBMODULO',
            'ruta': '/tablajeria/mermas',
            'icono': 'AlertTriangle',
            'orden': 6,
            'visible': True,
            'padre_codigo': 'tablajeria'
        },
        {
            'codigo': 'tablajeria.costeo',
            'nombre': 'Costeo',
            'descripcion': 'Costeo de producción',
            'tipo': 'SUBMODULO',
            'ruta': '/tablajeria/costeo',
            'icono': 'Calculator',
            'orden': 7,
            'visible': True,
            'padre_codigo': 'tablajeria'
        },
        {
            'codigo': 'tablajeria.polizas',
            'nombre': 'Pólizas Contables',
            'descripcion': 'Pólizas generadas',
            'tipo': 'SUBMODULO',
            'ruta': '/tablajeria/polizas',
            'icono': 'Receipt',
            'orden': 8,
            'visible': True,
            'padre_codigo': 'tablajeria'
        },
        {
            'codigo': 'tablajeria.sync',
            'nombre': 'Sincronización',
            'descripcion': 'Sincronización desde sistemas legacy',
            'tipo': 'SUBMODULO',
            'ruta': '/tablajeria/sync',
            'icono': 'RefreshCw',
            'orden': 9,
            'visible': True,
            'padre_codigo': 'tablajeria'
        },
        {
            'codigo': 'tablajeria.config',
            'nombre': 'Configuración',
            'descripcion': 'Configuración del módulo',
            'tipo': 'SUBMODULO',
            'ruta': '/tablajeria/config',
            'icono': 'Settings',
            'orden': 10,
            'visible': True,
            'padre_codigo': 'tablajeria'
        },
    ]
    
    modulos_creados = 0
    modulo_ids = {}
    
    for mod in modulos:
        # Verificar si ya existe
        cursor.execute("""
            SELECT ModuloID FROM Usuario_Modulos 
            WHERE CodigoModulo = %s
        """, (mod['codigo'],))
        
        existing = cursor.fetchone()
        if existing:
            modulo_ids[mod['codigo']] = existing[0]
            print(f"  [EXISTE] {mod['codigo']}")
            continue
        
        # Obtener ID del padre si aplica
        padre_id = None
        if mod['padre_codigo']:
            padre_id = modulo_ids.get(mod['padre_codigo'])
        
        # Crear módulo
        cursor.execute("""
            INSERT INTO Usuario_Modulos (
                ModuloPadreID, CodigoModulo, NombreModulo, Descripcion,
                TipoModulo, Ruta, Icono, OrdenMenu, EsVisibleMenu,
                RequiereAutorizacion, Activo, FechaAlta
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            padre_id, mod['codigo'], mod['nombre'], mod['descripcion'],
            mod['tipo'], mod['ruta'], mod['icono'], mod['orden'],
            mod['visible'], False, True, now
        ))
        
        # Obtener el ID generado
        cursor.execute("SELECT @@IDENTITY")
        modulo_ids[mod['codigo']] = cursor.fetchone()[0]
        modulos_creados += 1
        print(f"  [CREADO] {mod['codigo']}")
    
    return modulos_creados, modulo_ids


def create_tablajeria_permissions(cursor, modulo_ids):
    """Asigna permisos de Tablajería a los roles."""
    
    now = datetime.utcnow()
    
    # Acciones disponibles
    ACCIONES = {
        'VER': 1,
        'CREAR': 2,
        'EDITAR': 3,
        'ELIMINAR': 4,
        'EXPORTAR': 5,
        'AUTORIZAR': 7,
        'CANCELAR': 9,
        'EJECUTAR': 10,
        'CONFIGURAR': 13
    }
    
    # Roles y sus permisos por módulo
    # Formato: {rol_id: {modulo_codigo: [acciones]}}
    PERMISOS_POR_ROL = {
        # SUPERADMIN (6) - Todos los permisos
        6: {
            'tablajeria': ['VER', 'CREAR', 'EDITAR', 'ELIMINAR', 'EXPORTAR', 'AUTORIZAR', 'CANCELAR', 'EJECUTAR', 'CONFIGURAR'],
            'tablajeria.dashboard': ['VER', 'EXPORTAR'],
            'tablajeria.ordenes': ['VER', 'CREAR', 'EDITAR', 'ELIMINAR', 'EXPORTAR', 'AUTORIZAR', 'CANCELAR', 'EJECUTAR'],
            'tablajeria.captura_directa': ['VER', 'CREAR', 'EJECUTAR'],
            'tablajeria.plantillas': ['VER', 'CREAR', 'EDITAR', 'ELIMINAR', 'EXPORTAR', 'AUTORIZAR'],
            'tablajeria.rendimientos': ['VER', 'EXPORTAR'],
            'tablajeria.mermas': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'AUTORIZAR'],
            'tablajeria.costeo': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR'],
            'tablajeria.polizas': ['VER', 'CREAR', 'EXPORTAR', 'AUTORIZAR'],
            'tablajeria.sync': ['VER', 'EJECUTAR', 'CONFIGURAR'],
            'tablajeria.config': ['VER', 'EDITAR', 'CONFIGURAR'],
        },
        # ADMIN (1) - Casi todos los permisos
        1: {
            'tablajeria': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'AUTORIZAR', 'CANCELAR', 'EJECUTAR'],
            'tablajeria.dashboard': ['VER', 'EXPORTAR'],
            'tablajeria.ordenes': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'AUTORIZAR', 'CANCELAR', 'EJECUTAR'],
            'tablajeria.captura_directa': ['VER', 'CREAR', 'EJECUTAR'],
            'tablajeria.plantillas': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'AUTORIZAR'],
            'tablajeria.rendimientos': ['VER', 'EXPORTAR'],
            'tablajeria.mermas': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'AUTORIZAR'],
            'tablajeria.costeo': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR'],
            'tablajeria.polizas': ['VER', 'CREAR', 'EXPORTAR'],
            'tablajeria.sync': ['VER', 'EJECUTAR'],
            'tablajeria.config': ['VER', 'EDITAR'],
        },
        # GERENCIA (2) - Permisos de gestión
        2: {
            'tablajeria': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'AUTORIZAR'],
            'tablajeria.dashboard': ['VER', 'EXPORTAR'],
            'tablajeria.ordenes': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'AUTORIZAR'],
            'tablajeria.captura_directa': ['VER', 'CREAR', 'EJECUTAR'],
            'tablajeria.plantillas': ['VER', 'EDITAR', 'EXPORTAR'],
            'tablajeria.rendimientos': ['VER', 'EXPORTAR'],
            'tablajeria.mermas': ['VER', 'EXPORTAR', 'AUTORIZAR'],
            'tablajeria.costeo': ['VER', 'EXPORTAR'],
            'tablajeria.polizas': ['VER', 'EXPORTAR'],
            'tablajeria.sync': ['VER'],
            'tablajeria.config': ['VER'],
        },
        # GERENTE_OPS (11) - Operaciones
        11: {
            'tablajeria': ['VER', 'CREAR', 'EDITAR', 'EJECUTAR', 'CANCELAR'],
            'tablajeria.dashboard': ['VER', 'EXPORTAR'],
            'tablajeria.ordenes': ['VER', 'CREAR', 'EDITAR', 'EJECUTAR', 'CANCELAR'],
            'tablajeria.captura_directa': ['VER', 'CREAR', 'EJECUTAR'],
            'tablajeria.plantillas': ['VER', 'EDITAR'],
            'tablajeria.rendimientos': ['VER', 'EXPORTAR'],
            'tablajeria.mermas': ['VER', 'CREAR', 'EDITAR'],
            'tablajeria.costeo': ['VER'],
            'tablajeria.polizas': ['VER'],
            'tablajeria.sync': ['VER', 'EJECUTAR'],
            'tablajeria.config': ['VER'],
        },
        # SUPERVISOR (7) - Supervisión
        7: {
            'tablajeria': ['VER', 'CREAR', 'EJECUTAR'],
            'tablajeria.dashboard': ['VER'],
            'tablajeria.ordenes': ['VER', 'CREAR', 'EJECUTAR'],
            'tablajeria.captura_directa': ['VER', 'CREAR', 'EJECUTAR'],
            'tablajeria.plantillas': ['VER'],
            'tablajeria.rendimientos': ['VER'],
            'tablajeria.mermas': ['VER', 'CREAR'],
            'tablajeria.costeo': ['VER'],
            'tablajeria.polizas': ['VER'],
        },
        # OPERADOR (12) - Ejecución básica
        12: {
            'tablajeria': ['VER', 'EJECUTAR'],
            'tablajeria.dashboard': ['VER'],
            'tablajeria.ordenes': ['VER', 'EJECUTAR'],
            'tablajeria.captura_directa': ['VER', 'CREAR', 'EJECUTAR'],
            'tablajeria.plantillas': ['VER'],
            'tablajeria.rendimientos': ['VER'],
            'tablajeria.mermas': ['VER', 'CREAR'],
        },
        # AUDITOR (13) - Solo lectura
        13: {
            'tablajeria': ['VER', 'EXPORTAR'],
            'tablajeria.dashboard': ['VER', 'EXPORTAR'],
            'tablajeria.ordenes': ['VER', 'EXPORTAR'],
            'tablajeria.captura_directa': ['VER'],
            'tablajeria.plantillas': ['VER', 'EXPORTAR'],
            'tablajeria.rendimientos': ['VER', 'EXPORTAR'],
            'tablajeria.mermas': ['VER', 'EXPORTAR'],
            'tablajeria.costeo': ['VER', 'EXPORTAR'],
            'tablajeria.polizas': ['VER', 'EXPORTAR'],
            'tablajeria.sync': ['VER'],
            'tablajeria.config': ['VER'],
        },
        # VISOR (9) - Solo ver
        9: {
            'tablajeria': ['VER'],
            'tablajeria.dashboard': ['VER'],
            'tablajeria.ordenes': ['VER'],
            'tablajeria.plantillas': ['VER'],
            'tablajeria.rendimientos': ['VER'],
        },
    }
    
    permisos_creados = 0
    
    for rol_id, modulos in PERMISOS_POR_ROL.items():
        for modulo_codigo, acciones in modulos.items():
            modulo_id = modulo_ids.get(modulo_codigo)
            if not modulo_id:
                print(f"  [WARN] Módulo no encontrado: {modulo_codigo}")
                continue
            
            for accion_nombre in acciones:
                accion_id = ACCIONES.get(accion_nombre)
                if not accion_id:
                    continue
                
                # Verificar si ya existe
                cursor.execute("""
                    SELECT PermisoRolModuloID FROM Usuario_PermisosRolModulo
                    WHERE RolID = %s AND ModuloID = %s AND AccionID = %s
                """, (rol_id, modulo_id, accion_id))
                
                if cursor.fetchone():
                    continue
                
                # Crear permiso
                cursor.execute("""
                    INSERT INTO Usuario_PermisosRolModulo (
                        RolID, ModuloID, AccionID, Permitido,
                        RestriccionPropietario, RestriccionSucursal,
                        RequiereAutorizacion, NivelAutorizacionRequerido,
                        Activo, FechaAlta, CreatedBy
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    rol_id, modulo_id, accion_id, True,
                    False, False,
                    accion_nombre == 'AUTORIZAR', 2 if accion_nombre == 'AUTORIZAR' else 0,
                    True, now, 'SCRIPT_RBAC_TABLAJERIA'
                ))
                permisos_creados += 1
    
    return permisos_creados


def main():
    print("=" * 60)
    print("EDARSA HUB - Script RBAC Tablajería")
    print("=" * 60)
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Crear módulos
        print("\n[1/2] Creando módulos de Tablajería...")
        modulos_creados, modulo_ids = create_tablajeria_modules(cursor)
        print(f"      {modulos_creados} módulos creados")
        
        # 2. Asignar permisos
        print("\n[2/2] Asignando permisos a roles...")
        permisos_creados = create_tablajeria_permissions(cursor, modulo_ids)
        print(f"      {permisos_creados} permisos asignados")
        
        # Confirmar transacción
        conn.commit()
        
        print("\n" + "=" * 60)
        print("RBAC Tablajería configurado exitosamente")
        print("=" * 60)
        
        # Mostrar resumen
        print("\nMódulos creados:")
        for codigo, mod_id in modulo_ids.items():
            print(f"  - {codigo} (ID: {mod_id})")
        
        print("\nRoles con permisos de Tablajería:")
        print("  - SUPERADMIN: Todos los permisos")
        print("  - ADMIN: Gestión completa")
        print("  - GERENCIA: Gestión y autorización")
        print("  - GERENTE_OPS: Operaciones")
        print("  - SUPERVISOR: Supervisión")
        print("  - OPERADOR: Ejecución básica")
        print("  - AUDITOR: Solo lectura")
        print("  - VISOR: Ver dashboard")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
