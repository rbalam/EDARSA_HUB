"""
EDARSA HUB - Seed RBAC del modulo Comercial Pricing/Benchmark
=============================================================
Crea (idempotente) los modulos, acciones y permisos por rol que requieren los
endpoints de Pricing IA / Benchmark (`routes_pricing_ia.py`, `routes_pricing_ai.py`).

Los endpoints usan permisos con formato punto/minusculas, p.ej.:
  comercial.benchmark.ver / .validar
  comercial.competidores.ver / .crear / .editar / .inactivar / .eliminar
  comercial.perfil_unidad.ver / .editar
  comercial.precios_sugeridos.ver_ia / .generar

El motor RBAC (core/rbac/repository_sql.py) genera, para cada permiso rol-modulo,
tanto el formato legacy `{CodigoModulo}_{CodigoAccion}` como el canonico
`{CodigoModulo}.{codigoaccion_lower}`. Por eso aqui basta con:
  - registrar las acciones faltantes (INACTIVAR, VALIDAR, VER_IA, GENERAR),
  - registrar los modulos comercial.*,
  - asignar permisos rol-modulo-accion.

SuperAdministrador/Administrador ya tienen BYPASS en el motor; se siembran igual
para que la matriz quede explicita y auditable.

Uso:
    python scripts/create_comercial_pricing_rbac.py
"""
import os
import pymssql
from datetime import datetime


def get_connection():
    return pymssql.connect(
        server=os.getenv('EDARSAHUB_SQL_HOST'),
        port=int(os.getenv('EDARSAHUB_SQL_PORT', '1433')),
        database=os.getenv('EDARSAHUB_SQL_DATABASE', 'EDARSAHUB'),
        user=os.getenv('EDARSAHUB_SQL_USER'),
        password=os.getenv('EDARSAHUB_SQL_PASSWORD'),
        autocommit=False,
    )


# Acciones requeridas que NO existen en el catalogo base
ACCIONES_NUEVAS = [
    # CodigoAccion, NombreAccion, Descripcion, EsAutorizable
    ('INACTIVAR', 'Inactivar', 'Baja logica de un registro', 0),
    ('VALIDAR',   'Validar',   'Marcar un registro como validado', 0),
    ('VER_IA',    'Ver IA',    'Ver / consultar resultados de IA', 0),
    ('GENERAR',   'Generar',   'Generar / calcular (precios sugeridos)', 0),
]

# Modulos comercial.*
MODULOS = [
    # codigo, nombre, descripcion, tipo, padre_codigo
    ('comercial', 'Comercial', 'Modulo comercial (Pricing IA / Benchmark)', 'MODULO', None),
    ('comercial.perfil_unidad', 'Perfil Digital de Unidad', 'Perfiles digitales de unidades de negocio', 'SUBMODULO', 'comercial'),
    ('comercial.competidores', 'Competidores', 'Competidores y menu items', 'SUBMODULO', 'comercial'),
    ('comercial.benchmark', 'Benchmark de Productos', 'Mapeos de benchmark producto vs competencia', 'SUBMODULO', 'comercial'),
    ('comercial.precios_sugeridos', 'Precios Sugeridos', 'Calculo de precios sugeridos (IA y base)', 'SUBMODULO', 'comercial'),
]

# Acciones por modulo (universo de permisos del modulo)
ACCIONES_POR_MODULO = {
    'comercial.perfil_unidad': ['VER', 'EDITAR'],
    'comercial.competidores': ['VER', 'CREAR', 'EDITAR', 'INACTIVAR', 'ELIMINAR'],
    'comercial.benchmark': ['VER', 'VALIDAR'],
    'comercial.precios_sugeridos': ['VER_IA', 'GENERAR'],
}

# Matriz rol -> {modulo: [acciones]}. RolID segun Usuario_Roles.
TODO_COMERCIAL = {
    'comercial.perfil_unidad': ['VER', 'EDITAR'],
    'comercial.competidores': ['VER', 'CREAR', 'EDITAR', 'INACTIVAR', 'ELIMINAR'],
    'comercial.benchmark': ['VER', 'VALIDAR'],
    'comercial.precios_sugeridos': ['VER_IA', 'GENERAR'],
}

SOLO_LECTURA = {
    'comercial.perfil_unidad': ['VER'],
    'comercial.competidores': ['VER'],
    'comercial.benchmark': ['VER'],
    'comercial.precios_sugeridos': ['VER_IA'],
}

PERMISOS_POR_ROL = {
    6: TODO_COMERCIAL,   # SUPERADMIN (bypass, explicito)
    1: TODO_COMERCIAL,   # ADMIN (bypass, explicito)
    17: TODO_COMERCIAL,  # ADMIN_COMERCIAL
    10: TODO_COMERCIAL,  # DIRECCION
    18: {                # GERENTE_UNIDAD
        'comercial.perfil_unidad': ['VER'],
        'comercial.competidores': ['VER', 'CREAR', 'EDITAR'],
        'comercial.benchmark': ['VER', 'VALIDAR'],
        'comercial.precios_sugeridos': ['VER_IA', 'GENERAR'],
    },
    21: {                # CONFIGURADOR_COMERCIAL
        'comercial.perfil_unidad': ['VER', 'EDITAR'],
        'comercial.competidores': ['VER', 'CREAR', 'EDITAR', 'INACTIVAR', 'ELIMINAR'],
        'comercial.benchmark': ['VER'],
        'comercial.precios_sugeridos': ['VER_IA'],
    },
    19: {                # ANALISTA_COMERCIAL
        'comercial.perfil_unidad': ['VER'],
        'comercial.competidores': ['VER', 'CREAR', 'EDITAR'],
        'comercial.benchmark': ['VER'],
        'comercial.precios_sugeridos': ['VER_IA', 'GENERAR'],
    },
    20: SOLO_LECTURA,    # VISOR_COMERCIAL
    2: {                 # GERENCIA
        'comercial.perfil_unidad': ['VER'],
        'comercial.competidores': ['VER'],
        'comercial.benchmark': ['VER', 'VALIDAR'],
        'comercial.precios_sugeridos': ['VER_IA', 'GENERAR'],
    },
    13: SOLO_LECTURA,    # AUDITOR (solo lectura)
}


def ensure_acciones(cur):
    creadas = 0
    for codigo, nombre, desc, autorizable in ACCIONES_NUEVAS:
        cur.execute("SELECT AccionID FROM Usuario_Acciones WHERE CodigoAccion = %s", (codigo,))
        if cur.fetchone():
            print(f"  [EXISTE] accion {codigo}")
            continue
        cur.execute(
            """INSERT INTO Usuario_Acciones (CodigoAccion, NombreAccion, Descripcion, EsAutorizable, Activo)
               VALUES (%s, %s, %s, %s, 1)""",
            (codigo, nombre, desc, autorizable),
        )
        creadas += 1
        print(f"  [CREADA] accion {codigo}")
    return creadas


def ensure_modulos(cur):
    now = datetime.utcnow()
    ids = {}
    creados = 0
    for codigo, nombre, desc, tipo, padre in MODULOS:
        cur.execute("SELECT ModuloID FROM Usuario_Modulos WHERE CodigoModulo = %s", (codigo,))
        row = cur.fetchone()
        if row:
            ids[codigo] = row[0]
            print(f"  [EXISTE] modulo {codigo}")
            continue
        padre_id = ids.get(padre) if padre else None
        cur.execute(
            """INSERT INTO Usuario_Modulos
               (ModuloPadreID, CodigoModulo, NombreModulo, Descripcion, TipoModulo,
                Ruta, Icono, OrdenMenu, EsVisibleMenu, RequiereAutorizacion, Activo, FechaAlta)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (padre_id, codigo, nombre, desc, tipo, None, None, 0, 0, 0, 1, now),
        )
        cur.execute("SELECT @@IDENTITY")
        ids[codigo] = cur.fetchone()[0]
        creados += 1
        print(f"  [CREADO] modulo {codigo}")
    return creados, ids


def get_accion_ids(cur):
    cur.execute("SELECT AccionID, CodigoAccion FROM Usuario_Acciones")
    return {r[1]: r[0] for r in cur.fetchall()}


def seed_permisos(cur, modulo_ids, accion_ids):
    now = datetime.utcnow()
    creados = 0
    for rol_id, modulos in PERMISOS_POR_ROL.items():
        for modulo_codigo, acciones in modulos.items():
            modulo_id = modulo_ids.get(modulo_codigo)
            if not modulo_id:
                print(f"  [WARN] modulo no encontrado: {modulo_codigo}")
                continue
            for accion in acciones:
                accion_id = accion_ids.get(accion)
                if not accion_id:
                    print(f"  [WARN] accion no encontrada: {accion}")
                    continue
                cur.execute(
                    """SELECT PermisoRolModuloID FROM Usuario_PermisosRolModulo
                       WHERE RolID = %s AND ModuloID = %s AND AccionID = %s""",
                    (rol_id, modulo_id, accion_id),
                )
                if cur.fetchone():
                    continue
                cur.execute(
                    """INSERT INTO Usuario_PermisosRolModulo
                       (RolID, ModuloID, AccionID, Permitido, RestriccionPropietario,
                        RestriccionSucursal, RequiereAutorizacion, NivelAutorizacionRequerido,
                        Activo, FechaAlta, CreatedBy)
                       VALUES (%s, %s, %s, 1, 0, 0, 0, 0, 1, %s, %s)""",
                    (rol_id, modulo_id, accion_id, now, 'SEED_COMERCIAL_PRICING_RBAC'),
                )
                creados += 1
    return creados


def main():
    print("=" * 60)
    print("EDARSA HUB - Seed RBAC Comercial Pricing/Benchmark")
    print("=" * 60)
    conn = get_connection()
    try:
        cur = conn.cursor()
        print("\n[1/3] Acciones...")
        a = ensure_acciones(cur)
        print(f"      {a} acciones nuevas")

        print("\n[2/3] Modulos...")
        m, modulo_ids = ensure_modulos(cur)
        print(f"      {m} modulos nuevos")

        accion_ids = get_accion_ids(cur)

        print("\n[3/3] Permisos por rol...")
        p = seed_permisos(cur, modulo_ids, accion_ids)
        print(f"      {p} permisos nuevos")

        conn.commit()
        print("\nOK. Seed comercial pricing/benchmark aplicado.")
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
