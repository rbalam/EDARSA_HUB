"""
EDARSA HUB - Script RBAC para Cava de Socios
=============================================
Crea módulos, permisos y asignaciones de roles para el módulo Cava de Socios.

Ubicación ERP: 07. Cava de Socios / Socios Cava
Tipo: Módulo principal (Inventario en custodia de terceros)

Uso:
    python create_cava_socios_rbac.py
"""

import pymssql
import os
from datetime import datetime

DB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'username': os.environ.get('EDARSAHUB_USERNAME', '<REDACTED_EDARSAHUB_SQL_USER>'),
    'password': os.environ.get('EDARSAHUB_PASSWORD', '<REDACTED_EDARSAHUB_SQL_PASSWORD>')
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


def create_cava_socios_modules(cursor):
    """Crea los módulos de Cava de Socios en Usuario_Modulos."""
    
    now = datetime.utcnow()
    
    modulos = [
        # Módulo padre
        {
            'codigo': 'cava_socios',
            'nombre': 'Cava de Socios',
            'descripcion': 'Gestión de inventario en custodia de terceros',
            'tipo': 'MODULO',
            'ruta': '/cava-socios',
            'icono': 'Wine',
            'orden': 70,
            'visible': True,
            'padre_codigo': None
        },
        # Submódulos
        {
            'codigo': 'cava_socios.dashboard',
            'nombre': 'Dashboard Cava',
            'descripcion': 'Panel principal de cava de socios',
            'tipo': 'SUBMODULO',
            'ruta': '/cava-socios/dashboard',
            'icono': 'LayoutDashboard',
            'orden': 1,
            'visible': True,
            'padre_codigo': 'cava_socios'
        },
        {
            'codigo': 'cava_socios.socios',
            'nombre': 'Socios',
            'descripcion': 'Gestión de socios de cava',
            'tipo': 'SUBMODULO',
            'ruta': '/cava-socios/socios',
            'icono': 'Users',
            'orden': 2,
            'visible': True,
            'padre_codigo': 'cava_socios'
        },
        {
            'codigo': 'cava_socios.botellas',
            'nombre': 'Botellas',
            'descripcion': 'Inventario de botellas en custodia',
            'tipo': 'SUBMODULO',
            'ruta': '/cava-socios/botellas',
            'icono': 'Wine',
            'orden': 3,
            'visible': True,
            'padre_codigo': 'cava_socios'
        },
        {
            'codigo': 'cava_socios.movimientos',
            'nombre': 'Movimientos',
            'descripcion': 'Historial de movimientos de cava',
            'tipo': 'SUBMODULO',
            'ruta': '/cava-socios/movimientos',
            'icono': 'ArrowLeftRight',
            'orden': 4,
            'visible': True,
            'padre_codigo': 'cava_socios'
        },
        {
            'codigo': 'cava_socios.consumos',
            'nombre': 'Consumos',
            'descripcion': 'Registro de consumos',
            'tipo': 'SUBMODULO',
            'ruta': '/cava-socios/consumos',
            'icono': 'GlassWater',
            'orden': 5,
            'visible': True,
            'padre_codigo': 'cava_socios'
        },
        {
            'codigo': 'cava_socios.cargos',
            'nombre': 'Cargos',
            'descripcion': 'Cargos por servicios de cava',
            'tipo': 'SUBMODULO',
            'ruta': '/cava-socios/cargos',
            'icono': 'Receipt',
            'orden': 6,
            'visible': True,
            'padre_codigo': 'cava_socios'
        },
        {
            'codigo': 'cava_socios.reportes',
            'nombre': 'Reportes',
            'descripcion': 'Reportes de cava de socios',
            'tipo': 'SUBMODULO',
            'ruta': '/cava-socios/reportes',
            'icono': 'FileBarChart',
            'orden': 7,
            'visible': True,
            'padre_codigo': 'cava_socios'
        },
        {
            'codigo': 'cava_socios.config',
            'nombre': 'Configuración',
            'descripcion': 'Configuración del módulo',
            'tipo': 'SUBMODULO',
            'ruta': '/cava-socios/config',
            'icono': 'Settings',
            'orden': 8,
            'visible': True,
            'padre_codigo': 'cava_socios'
        },
    ]
    
    modulos_creados = 0
    modulo_ids = {}
    
    for mod in modulos:
        cursor.execute("""
            SELECT ModuloID FROM Usuario_Modulos 
            WHERE CodigoModulo = %s
        """, (mod['codigo'],))
        
        existing = cursor.fetchone()
        if existing:
            modulo_ids[mod['codigo']] = existing[0]
            print(f"  [EXISTE] {mod['codigo']}")
            continue
        
        padre_id = None
        if mod['padre_codigo']:
            padre_id = modulo_ids.get(mod['padre_codigo'])
        
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
        
        cursor.execute("SELECT @@IDENTITY")
        modulo_ids[mod['codigo']] = cursor.fetchone()[0]
        modulos_creados += 1
        print(f"  [CREADO] {mod['codigo']}")
    
    return modulos_creados, modulo_ids


def create_cava_socios_permissions(cursor, modulo_ids):
    """Asigna permisos de Cava de Socios a los roles."""
    
    now = datetime.utcnow()
    
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
    
    # Permisos por rol
    PERMISOS_POR_ROL = {
        # SUPERADMIN (6)
        6: {
            'cava_socios': ['VER', 'CREAR', 'EDITAR', 'ELIMINAR', 'EXPORTAR', 'AUTORIZAR', 'CONFIGURAR'],
            'cava_socios.dashboard': ['VER', 'EXPORTAR'],
            'cava_socios.socios': ['VER', 'CREAR', 'EDITAR', 'ELIMINAR', 'EXPORTAR'],
            'cava_socios.botellas': ['VER', 'CREAR', 'EDITAR', 'ELIMINAR', 'EXPORTAR'],
            'cava_socios.movimientos': ['VER', 'CREAR', 'EXPORTAR'],
            'cava_socios.consumos': ['VER', 'CREAR', 'EDITAR', 'CANCELAR'],
            'cava_socios.cargos': ['VER', 'CREAR', 'EDITAR', 'CANCELAR', 'AUTORIZAR'],
            'cava_socios.reportes': ['VER', 'EXPORTAR'],
            'cava_socios.config': ['VER', 'EDITAR', 'CONFIGURAR'],
        },
        # ADMIN (1)
        1: {
            'cava_socios': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'AUTORIZAR'],
            'cava_socios.dashboard': ['VER', 'EXPORTAR'],
            'cava_socios.socios': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR'],
            'cava_socios.botellas': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR'],
            'cava_socios.movimientos': ['VER', 'CREAR', 'EXPORTAR'],
            'cava_socios.consumos': ['VER', 'CREAR', 'EDITAR', 'CANCELAR'],
            'cava_socios.cargos': ['VER', 'CREAR', 'EDITAR', 'AUTORIZAR'],
            'cava_socios.reportes': ['VER', 'EXPORTAR'],
            'cava_socios.config': ['VER', 'EDITAR'],
        },
        # GERENCIA (2)
        2: {
            'cava_socios': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'AUTORIZAR'],
            'cava_socios.dashboard': ['VER', 'EXPORTAR'],
            'cava_socios.socios': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR'],
            'cava_socios.botellas': ['VER', 'CREAR', 'EDITAR', 'EXPORTAR'],
            'cava_socios.movimientos': ['VER', 'EXPORTAR'],
            'cava_socios.consumos': ['VER', 'CREAR'],
            'cava_socios.cargos': ['VER', 'AUTORIZAR'],
            'cava_socios.reportes': ['VER', 'EXPORTAR'],
            'cava_socios.config': ['VER'],
        },
        # SUPERVISOR (7)
        7: {
            'cava_socios': ['VER', 'CREAR', 'EDITAR'],
            'cava_socios.dashboard': ['VER'],
            'cava_socios.socios': ['VER', 'CREAR', 'EDITAR'],
            'cava_socios.botellas': ['VER', 'CREAR', 'EDITAR'],
            'cava_socios.movimientos': ['VER', 'CREAR'],
            'cava_socios.consumos': ['VER', 'CREAR'],
            'cava_socios.cargos': ['VER', 'CREAR'],
            'cava_socios.reportes': ['VER'],
        },
        # OPERADOR (12) - Meseros/Personal operativo
        12: {
            'cava_socios': ['VER', 'CREAR'],
            'cava_socios.dashboard': ['VER'],
            'cava_socios.socios': ['VER'],
            'cava_socios.botellas': ['VER'],
            'cava_socios.movimientos': ['VER', 'CREAR'],
            'cava_socios.consumos': ['VER', 'CREAR'],
            'cava_socios.cargos': ['VER'],
        },
        # AUDITOR (13)
        13: {
            'cava_socios': ['VER', 'EXPORTAR'],
            'cava_socios.dashboard': ['VER', 'EXPORTAR'],
            'cava_socios.socios': ['VER', 'EXPORTAR'],
            'cava_socios.botellas': ['VER', 'EXPORTAR'],
            'cava_socios.movimientos': ['VER', 'EXPORTAR'],
            'cava_socios.consumos': ['VER', 'EXPORTAR'],
            'cava_socios.cargos': ['VER', 'EXPORTAR'],
            'cava_socios.reportes': ['VER', 'EXPORTAR'],
            'cava_socios.config': ['VER'],
        },
        # VISOR (9)
        9: {
            'cava_socios': ['VER'],
            'cava_socios.dashboard': ['VER'],
            'cava_socios.socios': ['VER'],
            'cava_socios.botellas': ['VER'],
        },
    }
    
    permisos_creados = 0
    
    for rol_id, modulos in PERMISOS_POR_ROL.items():
        for modulo_codigo, acciones in modulos.items():
            modulo_id = modulo_ids.get(modulo_codigo)
            if not modulo_id:
                continue
            
            for accion_nombre in acciones:
                accion_id = ACCIONES.get(accion_nombre)
                if not accion_id:
                    continue
                
                cursor.execute("""
                    SELECT PermisoRolModuloID FROM Usuario_PermisosRolModulo
                    WHERE RolID = %s AND ModuloID = %s AND AccionID = %s
                """, (rol_id, modulo_id, accion_id))
                
                if cursor.fetchone():
                    continue
                
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
                    True, now, 'SCRIPT_RBAC_CAVA_SOCIOS'
                ))
                permisos_creados += 1
    
    return permisos_creados


def main():
    print("=" * 60)
    print("EDARSA HUB - Script RBAC Cava de Socios")
    print("=" * 60)
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        print("\n[1/2] Creando módulos de Cava de Socios...")
        modulos_creados, modulo_ids = create_cava_socios_modules(cursor)
        print(f"      {modulos_creados} módulos creados")
        
        print("\n[2/2] Asignando permisos a roles...")
        permisos_creados = create_cava_socios_permissions(cursor, modulo_ids)
        print(f"      {permisos_creados} permisos asignados")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("RBAC Cava de Socios configurado exitosamente")
        print("=" * 60)
        
        print("\nMódulos creados:")
        for codigo in modulo_ids:
            print(f"  - {codigo}")
        
        print("\nRoles con permisos:")
        print("  - SUPERADMIN: Todos los permisos")
        print("  - ADMIN: Gestión completa")
        print("  - GERENCIA: Gestión y autorización")
        print("  - SUPERVISOR: Operación supervisada")
        print("  - OPERADOR: Registro de consumos")
        print("  - AUDITOR: Solo lectura y exportación")
        print("  - VISOR: Solo ver dashboard y socios")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
