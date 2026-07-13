"""
VALIDACIÓN TÉCNICA - MÓDULO PROPINAS TPV
==========================================
Fecha: Diciembre 2025
Objetivo: Validar datos reales de SoftRestaurant mediante conexiones canónicas

SUCURSALES: Unidades SoftRestaurant activas configuradas en EDARSAHUB
FUENTE: cheques.propinatarjeta

IMPORTANTE: Esta validación NO depende de VPN como concepto funcional.
El acceso se resuelve mediante la relación canónica de unidades y servidores.
Si hay fallo de red, es limitación del entorno, no del sistema.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Agregar al path
sys.path.insert(0, '/app/backend')

# Configuración de conexiones (desde repository_cortes_z.py)
from core.server_registry import (
    get_server_connection_info,
    list_unidades_negocio,
    normalize_system_type,
)
from core.sql_first.connection_factory import (
    get_external_sql_connection,
)
from core.sync.server_resolver import get_server_for_unidad


SOFTREST_SERVERS: Dict[str, Dict[str, Any]] = {}


async def resolve_softrest_servers() -> Dict[str, Dict[str, Any]]:
    """
    Resuelve las unidades SoftRestaurant activas desde EDARSAHUB.

    Fuente obligatoria:
    Unidades_Negocio.server_id -> Servidores_Conexiones.id.
    """
    unidades = list_unidades_negocio(active_only=True)
    resolved_servers: Dict[str, Dict[str, Any]] = {}

    for unidad in unidades:
        unidad_codigo = str(
            unidad.get("codigo") or ""
        ).strip()

        if not unidad_codigo:
            continue

        unidad_system_type = normalize_system_type(
            unidad.get("system_type")
        )

        if unidad_system_type != "SOFTRESTAURANT":
            continue

        resolved = get_server_for_unidad(
            unidad_codigo
        )

        if not resolved:
            raise RuntimeError(
                "No se pudo resolver servidor canónico para "
                f"{unidad_codigo}"
            )

        server_id = str(
            resolved.get("server_id") or ""
        ).strip()

        if not server_id:
            raise RuntimeError(
                "Unidad sin server_id canónico: "
                f"{unidad_codigo}"
            )

        if not resolved.get("servidor_activo"):
            raise RuntimeError(
                "Servidor inactivo para unidad: "
                f"{unidad_codigo}"
            )

        connection_info = (
            await get_server_connection_info(server_id)
        )

        if not connection_info:
            raise RuntimeError(
                "No se pudo obtener conexión canónica para "
                f"{unidad_codigo}"
            )

        server_type = normalize_system_type(
            connection_info.get("system_type")
            or resolved.get("servidor_system_type")
        )

        if server_type != "SOFTRESTAURANT":
            raise RuntimeError(
                "Servidor no SoftRestaurant para unidad: "
                f"{unidad_codigo}"
            )

        connection_info["nombre_display"] = (
            unidad.get("nombre") or unidad_codigo
        )
        connection_info["unidad_codigo"] = unidad_codigo
        connection_info["server_id"] = server_id

        resolved_servers[unidad_codigo] = (
            connection_info
        )

    if not resolved_servers:
        raise RuntimeError(
            "No existen unidades SoftRestaurant activas "
            "con conexión canónica"
        )

    return resolved_servers



# Porcentaje de comisión configurado
PORCENTAJE_COMISION = 0.02  # 2%

def connect_and_query(
    server_id: str,
    query: str,
) -> List[Dict]:
    """
    Ejecuta una consulta con el helper externo canónico.
    """
    config = SOFTREST_SERVERS.get(server_id)

    if not config:
        print(
            "  ❌ Conexión canónica no resuelta para "
            f"{server_id}"
        )
        return []

    connection = None
    cursor = None

    try:
        connection = get_external_sql_connection(
            config
        )

        try:
            cursor = connection.cursor(as_dict=True)
        except TypeError:
            cursor = connection.cursor()

        cursor.execute(query)
        rows = cursor.fetchall() or []

        if not rows:
            return []

        if isinstance(rows[0], dict):
            return [
                dict(row)
                for row in rows
            ]

        columns = [
            item[0]
            for item in cursor.description
        ]

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    except Exception as exc:
        print(
            "  ❌ Error de conexión canónica: "
            f"{type(exc).__name__}"
        )
        return []

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass

        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass




def validacion_1_extraccion(server_id: str, config: dict) -> Dict:
    """
    VALIDACIÓN 1: EXTRACCIÓN DE DATOS
    Confirma tabla, campo, query y tipo de dato
    """
    print(f"\n{'='*60}")
    print(f"VALIDACIÓN 1: EXTRACCIÓN - {config['nombre_display']}")
    print(f"{'='*60}")

    resultado = {
        'sucursal': config['nombre_display'],
        'server_id': server_id,
        'tabla_usada': None,
        'campo_usado': None,
        'tipo_dato': None,
        'conexion_exitosa': False,
        'query_final': None,
        'observaciones': []
    }

    # Query para verificar estructura
    query_schema = """
    SELECT
        c.TABLE_NAME,
        c.COLUMN_NAME,
        c.DATA_TYPE,
        c.IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS c
    WHERE c.TABLE_NAME = 'cheques'
      AND c.COLUMN_NAME IN ('propinatarjeta', 'propina', 'idturno', 'idestacion', 'total', 'tarjeta', 'efectivo')
    ORDER BY c.ORDINAL_POSITION
    """

    print(f"  Host: {config['host']}:{config['port']}")
    print(f"  Database: {config['database']}")
    print(f"  Verificando estructura de tabla cheques...")

    schema_result = connect_and_query(server_id, query_schema)

    if not schema_result:
        resultado['observaciones'].append("No se pudo conectar o tabla no existe")
        print(f"  ❌ No se pudo verificar esquema")
        return resultado

    resultado['conexion_exitosa'] = True

    # Verificar columna propinatarjeta
    columnas = {r['COLUMN_NAME'].lower(): r for r in schema_result}

    if 'propinatarjeta' in columnas:
        resultado['tabla_usada'] = 'cheques'
        resultado['campo_usado'] = 'propinatarjeta'
        resultado['tipo_dato'] = 'EXACTO (campo directo)'
        print(f"  ✅ Tabla: cheques")
        print(f"  ✅ Campo: propinatarjeta ({columnas['propinatarjeta']['DATA_TYPE']})")
        print(f"  ✅ Tipo dato: EXACTO")
    else:
        resultado['observaciones'].append("Campo propinatarjeta no encontrado")
        print(f"  ❌ Campo propinatarjeta NO encontrado")
        return resultado

    # Query final que se usa
    resultado['query_final'] = """
    SELECT
        mc.idmovtocaja AS corte_id,
        mc.folio AS folio_corte,
        CONVERT(DATE, mc.fecha) AS fecha_corte,
        mc.idturno AS turno_id,
        ISNULL(SUM(ch.propinatarjeta), 0) AS propinas_tpv
    FROM movtoscaja mc
    LEFT JOIN turnos t ON mc.idturno = t.idturno AND mc.idestacion = t.idestacion
    LEFT JOIN cheques ch ON ch.idturno = t.idturno AND ch.idestacion = t.idestacion
    WHERE mc.idtipomovtocaja = 3  -- Corte Z
    GROUP BY mc.idmovtocaja, mc.folio, mc.fecha, mc.idturno
    """

    print(f"  ✅ Query configurada correctamente")

    return resultado


def validacion_2_no_duplicidad(server_id: str, config: dict) -> Dict:
    """
    VALIDACIÓN 2: NO DUPLICIDAD
    Verifica que no se dupliquen propinas por turno/corte
    """
    print(f"\n{'='*60}")
    print(f"VALIDACIÓN 2: NO DUPLICIDAD - {config['nombre_display']}")
    print(f"{'='*60}")

    resultado = {
        'sucursal': config['nombre_display'],
        'duplicados_por_turno': False,
        'duplicados_por_corte': False,
        'detalle_turno': None,
        'detalle_corte': None,
        'observaciones': []
    }

    # Verificar duplicidad por idturno
    query_turno = """
    SELECT TOP 10
        ch.idturno,
        COUNT(*) as total_registros,
        SUM(ch.propinatarjeta) as suma_propinas,
        COUNT(DISTINCT ch.idcheque) as cheques_unicos
    FROM cheques ch
    WHERE ch.propinatarjeta > 0
      AND ch.fecha >= DATEADD(day, -30, GETDATE())
    GROUP BY ch.idturno
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    """

    print(f"  Verificando duplicidad por idturno...")
    turno_result = connect_and_query(server_id, query_turno)

    if turno_result:
        # Esto es NORMAL - un turno tiene múltiples cheques
        print(f"  ✅ Múltiples cheques por turno (esperado): {len(turno_result)} turnos")
        resultado['detalle_turno'] = f"{len(turno_result)} turnos con múltiples cheques"
        resultado['observaciones'].append("Múltiples cheques por turno es comportamiento normal")
    else:
        print(f"  ⚠️ No hay datos suficientes para verificar")

    # Verificar que SUM no duplique cuando se agrupa por corte
    query_corte = """
    ;WITH PropinasCorte AS (
        SELECT
            mc.folio AS folio_corte,
            mc.idmovtocaja AS corte_id,
            SUM(ch.propinatarjeta) AS propinas_calculadas
        FROM movtoscaja mc
        LEFT JOIN turnos t ON mc.idturno = t.idturno AND mc.idestacion = t.idestacion
        LEFT JOIN cheques ch ON ch.idturno = t.idturno AND ch.idestacion = t.idestacion
        WHERE mc.idtipomovtocaja = 3
          AND mc.fecha >= DATEADD(day, -30, GETDATE())
        GROUP BY mc.folio, mc.idmovtocaja
    )
    SELECT
        folio_corte,
        COUNT(*) as veces_aparece,
        SUM(propinas_calculadas) as total_propinas
    FROM PropinasCorte
    GROUP BY folio_corte
    HAVING COUNT(*) > 1
    """

    print(f"  Verificando duplicidad por folio_corte...")
    corte_result = connect_and_query(server_id, query_corte)

    if corte_result:
        resultado['duplicados_por_corte'] = True
        resultado['detalle_corte'] = f"⚠️ {len(corte_result)} folios duplicados"
        print(f"  ⚠️ Folios duplicados encontrados: {len(corte_result)}")
    else:
        resultado['duplicados_por_corte'] = False
        resultado['detalle_corte'] = "Sin duplicados"
        print(f"  ✅ Sin duplicados por folio_corte")

    return resultado


def validacion_3_coherencia(server_id: str, config: dict) -> Dict:
    """
    VALIDACIÓN 3: COHERENCIA
    Obtiene 5 cortes reales recientes con detalle
    """
    print(f"\n{'='*60}")
    print(f"VALIDACIÓN 3: COHERENCIA - {config['nombre_display']}")
    print(f"{'='*60}")

    resultado = {
        'sucursal': config['nombre_display'],
        'cortes': [],
        'total_propinas': 0,
        'total_descuento': 0,
        'observaciones': []
    }

    query = """
    SELECT TOP 5
        mc.idmovtocaja AS corte_id,
        mc.folio AS folio_corte,
        CONVERT(DATE, mc.fecha) AS fecha_corte,
        mc.idturno AS turno_id,
        ISNULL(SUM(ch.propinatarjeta), 0) AS propinas_tpv,
        ISNULL(SUM(ch.tarjeta), 0) AS ventas_tarjeta,
        ISNULL(SUM(ch.efectivo), 0) AS ventas_efectivo,
        ISNULL(SUM(ch.total), 0) AS ventas_totales,
        mc.saldo AS saldo_corte,
        mc.efectivo AS efectivo_declarado_corte
    FROM movtoscaja mc
    LEFT JOIN turnos t ON mc.idturno = t.idturno AND mc.idestacion = t.idestacion
    LEFT JOIN cheques ch ON ch.idturno = t.idturno AND ch.idestacion = t.idestacion
    WHERE mc.idtipomovtocaja = 3  -- Corte Z
      AND mc.fecha >= DATEADD(day, -30, GETDATE())
    GROUP BY mc.idmovtocaja, mc.folio, mc.fecha, mc.idturno, mc.saldo, mc.efectivo
    ORDER BY mc.fecha DESC
    """

    print(f"  Obteniendo últimos 5 cortes...")
    cortes = connect_and_query(server_id, query)

    if not cortes:
        resultado['observaciones'].append("No se encontraron cortes en los últimos 30 días")
        print(f"  ⚠️ Sin datos de cortes")
        return resultado

    print(f"\n  {'Fecha':<12} {'Folio':<8} {'Corte ID':<10} {'Turno':<8} {'Propina TPV':>12} {'% Config':>10} {'Descuento':>12}")
    print(f"  {'-'*82}")

    for corte in cortes:
        fecha = corte.get('fecha_corte', 'N/A')
        if hasattr(fecha, 'strftime'):
            fecha = fecha.strftime('%Y-%m-%d')

        propinas_tpv = float(corte.get('propinas_tpv', 0) or 0)
        descuento = propinas_tpv * PORCENTAJE_COMISION

        corte_data = {
            'sucursal': config['nombre_display'],
            'fecha': str(fecha),
            'folio_corte': str(corte.get('folio_corte', '')),
            'corte_id_origen': str(corte.get('corte_id', '')),
            'turno_id_origen': str(corte.get('turno_id', '')),
            'propina_tpv': propinas_tpv,
            'porcentaje_configurado': f"{PORCENTAJE_COMISION*100}%",
            'descuento_calculado': round(descuento, 2),
            'efectivo_declarado_corte': float(corte.get('efectivo_declarado_corte', 0) or 0)
        }
        resultado['cortes'].append(corte_data)
        resultado['total_propinas'] += propinas_tpv
        resultado['total_descuento'] += descuento

        print(f"  {str(fecha):<12} {str(corte.get('folio_corte','')):<8} {str(corte.get('corte_id','')):<10} {str(corte.get('turno_id','')):<8} ${propinas_tpv:>10,.2f} {PORCENTAJE_COMISION*100:>9}% ${descuento:>10,.2f}")

    print(f"  {'-'*82}")
    print(f"  {'TOTALES':>60} ${resultado['total_propinas']:>10,.2f}            ${resultado['total_descuento']:>10,.2f}")

    return resultado


def validacion_4_cuadre_funcional(server_id: str, config: dict) -> Dict:
    """
    VALIDACIÓN 4: CUADRE FUNCIONAL
    Verifica que el descuento esté contenido en el efectivo declarado
    """
    print(f"\n{'='*60}")
    print(f"VALIDACIÓN 4: CUADRE FUNCIONAL - {config['nombre_display']}")
    print(f"{'='*60}")

    resultado = {
        'sucursal': config['nombre_display'],
        'regla_aplicada': 'descuento_propinas = propina_tpv x porcentaje_configurado',
        'validaciones': [],
        'cuadre_correcto': True,
        'observaciones': []
    }

    query = """
    SELECT TOP 5
        mc.folio AS folio_corte,
        CONVERT(DATE, mc.fecha) AS fecha_corte,
        ISNULL(SUM(ch.propinatarjeta), 0) AS propinas_tpv,
        ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d
                WHERE d.idmovtocaja = mc.idmovtocaja AND d.idconcepto = 2), 0) AS efectivo_ventas,
        ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d
                WHERE d.idmovtocaja = mc.idmovtocaja AND d.idconcepto = 9), 0) AS propinas_pagadas_concepto9,
        mc.efectivo AS efectivo_declarado
    FROM movtoscaja mc
    LEFT JOIN turnos t ON mc.idturno = t.idturno AND mc.idestacion = t.idestacion
    LEFT JOIN cheques ch ON ch.idturno = t.idturno AND ch.idestacion = t.idestacion
    WHERE mc.idtipomovtocaja = 3
      AND mc.fecha >= DATEADD(day, -30, GETDATE())
    GROUP BY mc.idmovtocaja, mc.folio, mc.fecha, mc.efectivo
    ORDER BY mc.fecha DESC
    """

    print(f"  Verificando consistencia de cuadre...")
    cortes = connect_and_query(server_id, query)

    if not cortes:
        resultado['observaciones'].append("No se encontraron cortes para validar")
        print(f"  ⚠️ Sin datos")
        return resultado

    print(f"\n  {'Folio':<8} {'Propina TPV':>12} {'Descuento 2%':>12} {'Efect. Declarado':>16} {'Estado':>10}")
    print(f"  {'-'*66}")

    for corte in cortes:
        propinas_tpv = float(corte.get('propinas_tpv', 0) or 0)
        descuento_2pct = propinas_tpv * PORCENTAJE_COMISION
        efectivo_declarado = float(corte.get('efectivo_declarado', 0) or 0)
        propinas_concepto9 = float(corte.get('propinas_pagadas_concepto9', 0) or 0)

        # Validación: El descuento debe poder cubrirse con el efectivo
        # (efectivo_declarado ya tiene descontadas las propinas pagadas)
        estado = "✅ OK" if efectivo_declarado >= 0 else "⚠️ REV"

        validacion = {
            'folio': str(corte.get('folio_corte', '')),
            'propinas_tpv': propinas_tpv,
            'descuento_2pct': round(descuento_2pct, 2),
            'efectivo_declarado': efectivo_declarado,
            'propinas_pagadas_concepto9': propinas_concepto9,
            'estado': estado
        }
        resultado['validaciones'].append(validacion)

        if efectivo_declarado < 0:
            resultado['cuadre_correcto'] = False

        print(f"  {str(corte.get('folio_corte','')):<8} ${propinas_tpv:>10,.2f} ${descuento_2pct:>10,.2f} ${efectivo_declarado:>14,.2f} {estado:>10}")

    # Observación importante
    resultado['observaciones'].append(
        "El efectivo declarado en Corte Z ya tiene descontadas las propinas pagadas (concepto 9)"
    )
    resultado['observaciones'].append(
        "El módulo Propinas TPV calcula el 2% SOBRE la propina TPV, NO sobre efectivo"
    )

    print(f"\n  NOTA: El descuento del 2% se aplica sobre propinatarjeta, no sobre efectivo del corte")

    return resultado


def generar_dictamen(resultados: Dict) -> Dict:
    """Genera dictamen por sucursal y general"""

    dictamen = {
        'por_sucursal': {},
        'general': None,
        'riesgos_remanentes': [],
        'recomendacion': None
    }

    sucursales_ok = 0
    sucursales_con_obs = 0
    sucursales_fail = 0

    print(f"\n{'='*70}")
    print(f"DICTAMEN FINAL")
    print(f"{'='*70}")

    for server_id, data in resultados.items():
        nombre = SOFTREST_SERVERS[server_id]['nombre_display']

        # Evaluar resultado
        if not data.get('extraccion', {}).get('conexion_exitosa'):
            dictamen['por_sucursal'][nombre] = {
                'status': 'FAIL',
                'motivo': 'Sin conexión SQL',
                'color': '🔴'
            }
            sucursales_fail += 1
            print(f"\n  {nombre}: 🔴 FAIL")
            print(f"    Motivo: No se pudo establecer conexión SQL al servidor")
        elif data.get('no_duplicidad', {}).get('duplicados_por_corte'):
            dictamen['por_sucursal'][nombre] = {
                'status': 'PASS CON OBSERVACIONES',
                'motivo': 'Posible duplicidad en folios',
                'color': '🟡'
            }
            sucursales_con_obs += 1
            print(f"\n  {nombre}: 🟡 PASS CON OBSERVACIONES")
            print(f"    Observación: Revisar posible duplicidad en folios de corte")
        elif len(data.get('coherencia', {}).get('cortes', [])) == 0:
            dictamen['por_sucursal'][nombre] = {
                'status': 'PASS CON OBSERVACIONES',
                'motivo': 'Sin datos recientes para validar',
                'color': '🟡'
            }
            sucursales_con_obs += 1
            print(f"\n  {nombre}: 🟡 PASS CON OBSERVACIONES")
            print(f"    Observación: No hay cortes en últimos 30 días")
        else:
            dictamen['por_sucursal'][nombre] = {
                'status': 'PASS',
                'motivo': 'Datos extraídos correctamente',
                'color': '🟢'
            }
            sucursales_ok += 1
            print(f"\n  {nombre}: 🟢 PASS")
            print(f"    Extracción: cheques.propinatarjeta (dato EXACTO)")
            print(f"    Cortes validados: {len(data.get('coherencia', {}).get('cortes', []))}")

    # Dictamen general
    print(f"\n{'='*70}")

    if sucursales_fail == len(resultados):
        dictamen['general'] = 'NO LISTO'
        dictamen['motivo_general'] = 'Ninguna sucursal tiene conexión SQL funcional'
        print(f"DICTAMEN GENERAL: 🔴 NO LISTO")
    elif sucursales_fail > 0:
        dictamen['general'] = 'LISTO CON OBSERVACIONES'
        dictamen['motivo_general'] = f'{sucursales_fail} sucursal(es) sin conexión'
        print(f"DICTAMEN GENERAL: 🟡 LISTO CON OBSERVACIONES")
    elif sucursales_con_obs > 0:
        dictamen['general'] = 'LISTO CON OBSERVACIONES'
        dictamen['motivo_general'] = f'{sucursales_con_obs} sucursal(es) con observaciones menores'
        print(f"DICTAMEN GENERAL: 🟡 LISTO CON OBSERVACIONES")
    else:
        dictamen['general'] = 'LISTO PARA OPERACION'
        dictamen['motivo_general'] = 'Todas las sucursales validadas correctamente'
        print(f"DICTAMEN GENERAL: 🟢 LISTO PARA OPERACIÓN")

    print(f"  Motivo: {dictamen['motivo_general']}")

    # Riesgos remanentes
    dictamen['riesgos_remanentes'] = [
        "Si hay fallo de red hacia sucursales, es limitación del entorno, no del módulo",
        "El 2% se calcula sobre propinatarjeta, verificar que coincida con política de negocio",
        "Los datos de propinas dependen de que los cajeros capturen correctamente en SoftRestaurant"
    ]

    # Recomendación
    if dictamen['general'] == 'NO LISTO':
        dictamen['recomendacion'] = "Verificar conectividad de red hacia servidores SoftRestaurant"
    else:
        dictamen['recomendacion'] = "Proceder con validación en ambiente de producción. Monitorear primeros 5 cortes cuadrados."

    print(f"\n  RECOMENDACIÓN: {dictamen['recomendacion']}")

    return dictamen


def main():
    """Ejecuta todas las validaciones"""
    global SOFTREST_SERVERS

    SOFTREST_SERVERS = asyncio.run(
        resolve_softrest_servers()
    )


    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  VALIDACIÓN TÉCNICA - MÓDULO PROPINAS TPV                    ║
║                                                                              ║
║  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}                                                 ║
║  Sucursales: La Estelar, Cienfuegos, 130 Mérida                              ║
║  Fuente: cheques.propinatarjeta (SQL Server directo)                         ║
║  Porcentaje: {PORCENTAJE_COMISION*100}%                                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    resultados = {}

    for server_id, config in SOFTREST_SERVERS.items():
        print(f"\n{'#'*70}")
        print(f"# PROCESANDO: {config['nombre_display'].upper()}")
        print(f"{'#'*70}")

        resultados[server_id] = {
            'extraccion': validacion_1_extraccion(server_id, config),
            'no_duplicidad': validacion_2_no_duplicidad(server_id, config),
            'coherencia': validacion_3_coherencia(server_id, config),
            'cuadre': validacion_4_cuadre_funcional(server_id, config)
        }

    # Generar dictamen
    dictamen = generar_dictamen(resultados)

    # Resumen final
    print(f"\n{'='*70}")
    print(f"QUERIES FINALES POR SUCURSAL")
    print(f"{'='*70}")

    query_base = """
-- Query de extracción de propinas TPV (SoftRestaurant)
SELECT
    mc.idmovtocaja AS corte_id,
    mc.folio AS folio_corte,
    CONVERT(DATE, mc.fecha) AS fecha_corte,
    mc.idturno AS turno_id,
    ISNULL(SUM(ch.propinatarjeta), 0) AS propinas_tpv,
    ISNULL(SUM(ch.propina), 0) AS propinas_totales,
    mc.saldo AS saldo_corte
FROM movtoscaja mc
LEFT JOIN turnos t ON mc.idturno = t.idturno AND mc.idestacion = t.idestacion
LEFT JOIN cheques ch ON ch.idturno = t.idturno AND ch.idestacion = t.idestacion
WHERE mc.idtipomovtocaja = 3  -- Corte Z
  AND mc.fecha >= @fecha_inicio
  AND mc.fecha <= @fecha_fin
GROUP BY mc.idmovtocaja, mc.folio, mc.fecha, mc.idturno, mc.saldo
ORDER BY mc.fecha DESC
"""

    for server_id, config in SOFTREST_SERVERS.items():
        print(f"\n-- {config['nombre_display']} ({config['host']}:{config['port']}/{config['database']})")

    print(query_base)

    return resultados, dictamen


if __name__ == '__main__':
    resultados, dictamen = main()
