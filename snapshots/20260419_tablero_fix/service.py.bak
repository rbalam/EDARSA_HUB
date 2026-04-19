"""
EDARSA HUB - Comercial Module Service
=====================================
Lógica de negocio para el módulo comercial.

FASE 5 DEL REFACTOR MODULAR (Diciembre 2025):
- Estructura base creada
- Funciones auxiliares de procesamiento

FASE 5B-2 DEL REFACTOR MODULAR (Abril 2026):
- Migrado: get_kpis_softrestaurant() desde server.py
- Migrado: get_kpis_mpro() desde server.py  
- Migrado: get_kpis_mpro_por_sucursal() desde server.py
- Compatibilidad 100%: server.py ahora importa desde aquí

FUNCIONES MIGRADAS PREVIAMENTE (FASE 5B-1):
- query_api_mpro_local() -> modules/comercial/adapters.py
- obtener_ventas_dia_api_local() -> modules/comercial/adapters.py
- sumar_ventas_api_local_a_sucursal() -> modules/comercial/adapters.py

FIX ESTRUCTURAL (Abril 2026):
- Integración con DateFilterPolicy para validación de rangos de fecha
- Eliminación de bugs por fechas inválidas
"""

from typing import Dict, List, Any, Optional
import logging
import calendar
from datetime import datetime, timezone
from fastapi import HTTPException

from core.db import execute_sql_query
from core.utils.date_filters import DateFilterPolicy, to_yyyymmdd_range, is_valid_range
from modules.comercial.adapters import sumar_ventas_api_local_a_sucursal
from modules.comercial import repository as repo


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def calcular_ticket_promedio(ventas: float, cheques: int) -> float:
    """Calcula el ticket promedio."""
    return round(ventas / cheques, 2) if cheques > 0 else 0.0


def calcular_consumo_promedio(ventas: float, pax: int) -> float:
    """Calcula el consumo promedio por persona."""
    return round(ventas / pax, 2) if pax > 0 else 0.0


def calcular_porcentaje_cumplimiento(actual: float, meta: float) -> float:
    """Calcula el porcentaje de cumplimiento de una meta."""
    return round((actual / meta) * 100, 2) if meta > 0 else 0.0


# ============================================================================
# PROCESAMIENTO DE DATOS
# ============================================================================

def procesar_ventas_sucursal(data: Dict, nombre_sucursal: str = "") -> Dict:
    """
    Procesa y normaliza datos de ventas de una sucursal.
    """
    ventas = float(data.get('ventas', 0) or 0)
    pax = int(data.get('pax', 0) or 0)
    cheques = int(data.get('cheques', 0) or 0)
    
    return {
        "nombre": nombre_sucursal or data.get('nombre', ''),
        "ventas": ventas,
        "pax": pax,
        "cheques": cheques,
        "ticket_promedio": calcular_ticket_promedio(ventas, cheques),
        "consumo_promedio": calcular_consumo_promedio(ventas, pax),
        "status": data.get('status', 'online'),
        "origen": data.get('origen', 'nube')
    }


def agregar_totales(sucursales: List[Dict]) -> Dict:
    """
    Calcula totales agregados de una lista de sucursales.
    """
    total_ventas = sum(s.get('ventas', 0) for s in sucursales)
    total_pax = sum(s.get('pax', 0) for s in sucursales)
    total_cheques = sum(s.get('cheques', 0) for s in sucursales)
    
    return {
        "ventas": total_ventas,
        "pax": total_pax,
        "cheques": total_cheques,
        "ticket_promedio": calcular_ticket_promedio(total_ventas, total_cheques),
        "consumo_promedio": calcular_consumo_promedio(total_ventas, total_pax),
        "num_sucursales": len(sucursales)
    }


# ============================================================================
# OBTENER DATOS BÁSICOS
# ============================================================================

async def obtener_sucursales_servidor(server_id: str) -> List[Dict]:
    """
    Obtiene las sucursales de un servidor.
    """
    server = await repo.get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    return server.get('sucursales', [])


async def obtener_metas(server_id: str, sucursal: str, mes: int, anio: int) -> Dict:
    """
    Obtiene las metas de una sucursal.
    """
    metas = await repo.get_metas_sucursal(server_id, sucursal, mes, anio)
    return metas or {"meta_ventas": 0, "meta_pax": 0, "meta_cheques": 0}


async def guardar_metas(server_id: str, sucursal: str, mes: int, anio: int, metas: Dict) -> Dict:
    """
    Guarda las metas de una sucursal.
    """
    await repo.save_metas_sucursal(server_id, sucursal, mes, anio, metas)
    return {"message": "Metas guardadas correctamente"}


# ============================================================================
# HELPERS DEL TABLERO EJECUTIVO - MIGRADOS FASE 5B-2 (Abril 2026)
# ============================================================================
# Estas funciones fueron migradas desde server.py sin cambios funcionales.
# Mantienen la misma firma, mismos nombres de campos, misma estructura JSON.

def get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia=False):
    """Query reutilizable para SoftRestaurant - misma lógica análisis inventarios
    
    FASE 3.1 - COMPORTAMIENTO:
    - solo_ventas_dia=True → SoftRestaurant NO tiene API local, usa SQL nube (ventas acumuladas)
    - solo_ventas_dia=False → Usa SQL nube del menú Servidores
    
    NOTA: SoftRestaurant no tiene API local configurada. Cuando se solicitan ventas del día,
    se muestran las ventas acumuladas del SQL nube en su lugar.
    PENDIENTE: Inspección local en servidores para revisar configuración de API local SoftRestaurant.
    """
    
    # ============================================================================
    # VENTAS DEL DÍA: Priorizar cheques cerrados del último turno, fallback a tempcheques
    # - Si hay turno cerrado en las últimas 24h → mostrar cheques de ese turno
    # - Si NO hay turno cerrado reciente → mostrar tempcheques (operación en curso)
    # ============================================================================
    if solo_ventas_dia:
        logging.info(f"SoftRestaurant {server['name']}: Modo Ventas del Día")
        
        ventas = 0
        cheques = 0
        pax = 0
        origen = None
        
        # 1. Consultar cheques del último turno cerrado (últimas 24h)
        try:
            query_cerrados = """
SELECT 
    COUNT(DISTINCT c.folio) as cheques,
    ISNULL(SUM(c.total), 0) as ventas,
    ISNULL(SUM(c.nopersonas), 0) as pax
FROM cheques c
INNER JOIN turnos t ON t.idturno = c.idturno
WHERE t.cierre IS NOT NULL
  AND t.apertura >= DATEADD(HOUR, -24, GETDATE())
  AND c.cancelado = 0
"""
            result_cerrados = execute_sql_query(server['host'], server['port'], server['database'], 
                                                server['username'], server['password'], query_cerrados)
            if result_cerrados and len(result_cerrados) > 0:
                ventas = float(result_cerrados[0]['ventas'] or 0)
                cheques = int(result_cerrados[0]['cheques'] or 0)
                pax = int(result_cerrados[0]['pax'] or 0)
                if cheques > 0:
                    origen = "cheques_cerrados"
                    logging.info(f"SoftRestaurant {server['name']} - Cerrados (último turno): ${ventas:,.2f}, {cheques} cheques")
        except Exception as e:
            logging.warning(f"SoftRestaurant {server['name']}: Error cheques cerrados: {e}")
        
        # 2. Si NO hay cerrados recientes, usar tempcheques
        if origen is None:
            try:
                query_temp = """
SELECT 
    COUNT(DISTINCT folio) as cheques,
    ISNULL(SUM(total), 0) as ventas,
    ISNULL(SUM(nopersonas), 0) as pax
FROM tempcheques
WHERE cancelado = 0
"""
                result_temp = execute_sql_query(server['host'], server['port'], server['database'], 
                                                server['username'], server['password'], query_temp)
                if result_temp and len(result_temp) > 0:
                    ventas = float(result_temp[0]['ventas'] or 0)
                    cheques = int(result_temp[0]['cheques'] or 0)
                    pax = int(result_temp[0]['pax'] or 0)
                    if cheques > 0 or ventas > 0:
                        origen = "tempcheques"
                        logging.info(f"SoftRestaurant {server['name']} - Tempcheques: ${ventas:,.2f}, {cheques} cheques")
            except Exception as e:
                logging.warning(f"SoftRestaurant {server['name']}: Error tempcheques: {e}")
        
        # 3. Si no hay datos en ninguna tabla
        if origen is None:
            logging.warning(f"SoftRestaurant {server['name']}: Sin datos del día")
            return None
        
        if pax == 0 and cheques > 0:
            pax = cheques
        
        ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
        cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
        
        return {
            "ventas": ventas,
            "ventas_ant": 0,
            "ventas_año": 0,
            "var_vs_mes_ant": 0,
            "var_vs_año_ant": 0,
            "proyeccion": 0,
            "pax": pax,
            "pax_ant": 0,
            "pax_año": 0,
            "var_pax_mes": 0,
            "var_pax_año": 0,
            "cheques": cheques,
            "cheques_ant": 0,
            "cheques_año": 0,
            "var_cheques_mes": 0,
            "var_cheques_año": 0,
            "ticket_prom": ticket_prom,
            "cheque_prom": cheque_prom,
            "es_ventas_dia": True,
            "origen": origen
        }
    
    # ============================================================================
    # VENTAS HISTÓRICAS / ACUMULADAS: Usar SQL nube del menú Servidores
    # (Solo se ejecuta si solo_ventas_dia=False)
    # ============================================================================
    
    # VALIDACIÓN DE RANGO DE FECHAS (FIX ESTRUCTURAL)
    if not is_valid_range(fecha_ini, fecha_fin):
        logging.error(f"SoftRestaurant {server['name']}: Rango de fechas inválido ({fecha_ini} > {fecha_fin})")
        return None
    
    # Usar formato YYYYMMDD sin guiones para evitar problemas de conversión de fecha
    try:
        fi, ff = to_yyyymmdd_range(fecha_ini, fecha_fin)
    except ValueError as e:
        logging.error(f"SoftRestaurant {server['name']}: Error convirtiendo fechas: {e}")
        return None
    
    # DEBUG: Log para verificar fechas recibidas
    logging.info(f"SoftRestaurant {server['name']} - Fechas recibidas: fecha_ini={fecha_ini}, fecha_fin={fecha_fin}, fecha_ini_año_ant={fecha_ini_año_ant}, fecha_fin_año_ant={fecha_fin_año_ant}")
    
    # Extraer mes y año de fecha_fin para usarlos en recálculos (importante para multiselección de meses)
    mes_final = int(fecha_fin[5:7])  # Mes de fecha_fin (ej: 04 para abril)
    anio_final = int(fecha_fin[:4])  # Año de fecha_fin
    
    # PASO 1: Detectar el último día real con ventas en el período
    query_ultimo_dia = f"""
SELECT MAX(CONVERT(DATE, turnos.apertura)) as ultimo_dia_venta
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fi} 00:00:00'
  AND turnos.apertura <= '{ff} 23:59:59'
  AND cheques.cancelado = 0
"""
    try:
        result_ultimo = execute_sql_query(server['host'], server['port'], server['database'], 
                                          server['username'], server['password'], query_ultimo_dia)
        if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
            ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
            if isinstance(ultimo_dia_venta, str):
                # Parsear la fecha completa (YYYY-MM-DD)
                partes = ultimo_dia_venta.split('-') if '-' in ultimo_dia_venta else None
                if partes and len(partes) == 3:
                    anio_ultimo = int(partes[0])
                    mes_ultimo = int(partes[1])
                    dia_con_datos = int(partes[2])
                else:
                    dia_con_datos = int(ultimo_dia_venta[-2:])
                    mes_ultimo = mes_final
                    anio_ultimo = anio_final
            else:
                dia_con_datos = ultimo_dia_venta.day
                mes_ultimo = ultimo_dia_venta.month
                anio_ultimo = ultimo_dia_venta.year
            
            logging.info(f"SoftRestaurant {server['name']} - Último día con ventas: {anio_ultimo}-{mes_ultimo:02d}-{dia_con_datos:02d}")
            
            # Actualizar fecha_fin usando el MES CORRECTO del último día con ventas
            # CORRECCIÓN: Usar el mes y año del último día con ventas, no del mes inicial
            ff = f"{anio_ultimo}{str(mes_ultimo).zfill(2)}{str(dia_con_datos).zfill(2)}"
            
            # Calcular días transcurridos desde fecha_ini hasta el último día con ventas
            fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
            fecha_ultimo_dt = datetime(anio_ultimo, mes_ultimo, dia_con_datos)
            dias_transcurridos = (fecha_ultimo_dt - fecha_ini_dt).days + 1
            
            logging.info(f"SoftRestaurant {server['name']} - Período ajustado: {fi} a {ff}, días: {dias_transcurridos}")
            
            # Recalcular fechas de comparación basadas en días reales
            mes_actual = mes_ultimo  # Usar el mes del último día con ventas
            anio_actual = anio_ultimo
            
            # Mes anterior
            if mes_actual == 1:
                mes_ant = 12
                anio_ant = anio_actual - 1
            else:
                mes_ant = mes_actual - 1
                anio_ant = anio_actual
            
            max_dia_mes_ant = calendar.monthrange(anio_ant, mes_ant)[1]
            dia_comparar = min(dia_con_datos, max_dia_mes_ant)
            fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
            fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
            
            # Año anterior - CORRECCIÓN: NO sobrescribir fecha_ini_año_ant
            # El Tablero Ejecutivo ya calcula correctamente el rango completo (ej: 01-ene-2025 a 08-abr-2025)
            # Solo ajustamos fecha_fin_año_ant al día correcto del mes final
            anio_pasado = anio_actual - 1
            max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_ultimo)[1]
            dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
            # PRESERVAR fecha_ini_año_ant original (viene del Tablero con el mes inicial correcto)
            # Solo actualizar fecha_fin_año_ant con el día ajustado del mes final
            fecha_fin_año_ant = f"{anio_pasado}-{str(mes_ultimo).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
            
            logging.info(f"Períodos ajustados - Actual: {fi[:4]}-{fi[4:6]}-01 a {ff}, Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
    except Exception as e:
        logging.warning(f"Error detectando último día: {e}")
        # Si falla, continuar con las fechas originales
    
    # Query principal
    query = f"""
SELECT 
    COUNT(DISTINCT cheques.folio) as cheques,
    ISNULL(SUM(cheques.total), 0) as ventas,
    ISNULL(SUM(cheques.nopersonas), 0) as pax
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fi} 00:00:00'
  AND turnos.apertura <= '{ff} 23:59:59'
  AND cheques.cancelado = 0
"""
    try:
        result = execute_sql_query(server['host'], server['port'], server['database'], 
                                   server['username'], server['password'], query)
        if result and len(result) > 0:
            ventas = float(result[0]['ventas'] or 0)
            pax = int(result[0]['pax'] or 0)
            cheques = int(result[0]['cheques'] or 0)
        else:
            ventas, pax, cheques = 0, 0, 0
    except Exception as e:
        logging.warning(f"Error consultando {server['name']}: {e}")
        return None
    
    # SUMAR ventas del día sin corte (tempcheques) a las ventas históricas
    try:
        query_temp = """
SELECT 
    COUNT(DISTINCT folio) as cheques,
    ISNULL(SUM(total), 0) as ventas,
    ISNULL(SUM(nopersonas), 0) as pax
FROM tempcheques
WHERE cancelado = 0
"""
        result_temp = execute_sql_query(server['host'], server['port'], server['database'], 
                                        server['username'], server['password'], query_temp)
        if result_temp and len(result_temp) > 0:
            ventas_temp = float(result_temp[0]['ventas'] or 0)
            pax_temp = int(result_temp[0]['pax'] or 0)
            cheques_temp = int(result_temp[0]['cheques'] or 0)
            # Sumar a los totales
            ventas += ventas_temp
            pax += pax_temp
            cheques += cheques_temp
            logging.info(f"SoftRestaurant {server['name']} - Tempcheques sumados: ventas={ventas_temp}, pax={pax_temp}, cheques={cheques_temp}")
    except Exception as e:
        logging.warning(f"Error consultando tempcheques {server['name']}: {e} - continuando sin ventas del día")
    
    # Mes anterior (mismos días)
    fia = fecha_ini_ant.replace('-', '')
    ffa = fecha_fin_ant.replace('-', '')
    query_ant = f"""
SELECT ISNULL(SUM(cheques.total), 0) as ventas, ISNULL(SUM(cheques.nopersonas), 0) as pax, COUNT(DISTINCT cheques.folio) as cheques
FROM cheques INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fia} 00:00:00' AND turnos.apertura <= '{ffa} 23:59:59' AND cheques.cancelado = 0
"""
    try:
        r_ant = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], query_ant)
        ventas_ant = float(r_ant[0]['ventas'] or 0) if r_ant else 0
        pax_ant = int(r_ant[0]['pax'] or 0) if r_ant else 0
        cheques_ant = int(r_ant[0]['cheques'] or 0) if r_ant else 0
    except:
        ventas_ant, pax_ant, cheques_ant = 0, 0, 0
    
    # Año anterior (mismos días)
    fiaa = fecha_ini_año_ant.replace('-', '')
    ffaa = fecha_fin_año_ant.replace('-', '')
    query_año = f"""
SELECT ISNULL(SUM(cheques.total), 0) as ventas, ISNULL(SUM(cheques.nopersonas), 0) as pax, COUNT(DISTINCT cheques.folio) as cheques
FROM cheques INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fiaa} 00:00:00' AND turnos.apertura <= '{ffaa} 23:59:59' AND cheques.cancelado = 0
"""
    try:
        r_año = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], query_año)
        ventas_año = float(r_año[0]['ventas'] or 0) if r_año else 0
        pax_año = int(r_año[0]['pax'] or 0) if r_año else 0
        cheques_año = int(r_año[0]['cheques'] or 0) if r_año else 0
    except:
        ventas_año, pax_año, cheques_año = 0, 0, 0
    
    # Cálculos
    ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
    cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
    
    # Proyección mes completo
    proyeccion = round((ventas / dias_transcurridos) * dias_mes, 2) if dias_transcurridos > 0 else 0
    
    # Variaciones %
    var_vs_mes_ant = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
    var_vs_año_ant = round(((ventas - ventas_año) / ventas_año * 100), 1) if ventas_año > 0 else 0
    var_pax_mes = round(((pax - pax_ant) / pax_ant * 100), 1) if pax_ant > 0 else 0
    var_pax_año = round(((pax - pax_año) / pax_año * 100), 1) if pax_año > 0 else 0
    var_cheques_mes = round(((cheques - cheques_ant) / cheques_ant * 100), 1) if cheques_ant > 0 else 0
    var_cheques_año = round(((cheques - cheques_año) / cheques_año * 100), 1) if cheques_año > 0 else 0
    
    return {
        "ventas": ventas,
        "ventas_ant": ventas_ant,
        "ventas_año": ventas_año,
        "var_vs_mes_ant": var_vs_mes_ant,
        "var_vs_año_ant": var_vs_año_ant,
        "proyeccion": proyeccion,
        "pax": pax,
        "pax_ant": pax_ant,
        "pax_año": pax_año,
        "var_pax_mes": var_pax_mes,
        "var_pax_año": var_pax_año,
        "cheques": cheques,
        "cheques_ant": cheques_ant,
        "cheques_año": cheques_año,
        "var_cheques_mes": var_cheques_mes,
        "var_cheques_año": var_cheques_año,
        "ticket_prom": ticket_prom,
        "cheque_prom": cheque_prom
    }


def get_kpis_mpro(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes):
    """Query reutilizable para MPRO - ventas desde tabla Venta"""
    
    # Formato YYYYMMDD para MPRO
    fi = fecha_ini.replace('-', '')
    ff = fecha_fin.replace('-', '')
    
    # Extraer mes y año de fecha_fin para usarlos en recálculos (importante para multiselección de meses)
    mes_final = int(fecha_fin[5:7])  # Mes de fecha_fin (ej: 04 para abril)
    anio_final = int(fecha_fin[:4])  # Año de fecha_fin
    
    # PASO 1: Detectar el último día real con ventas en el período
    query_ultimo_dia = f"""
SELECT MAX(CONVERT(DATE, Vn_Fecha)) as ultimo_dia_venta
FROM Venta
WHERE Vn_Fecha >= '{fi}' AND Vn_Fecha <= '{ff} 23:59:59'
  AND ISNULL(Es_Cve_Estado, '') <> 'CA'
"""
    try:
        result_ultimo = execute_sql_query(server['host'], server['port'], server['database'], 
                                          server['username'], server['password'], query_ultimo_dia)
        if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
            ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
            if isinstance(ultimo_dia_venta, str):
                # Parsear la fecha completa (YYYY-MM-DD)
                partes = ultimo_dia_venta.split('-') if '-' in ultimo_dia_venta else None
                if partes and len(partes) == 3:
                    anio_ultimo = int(partes[0])
                    mes_ultimo = int(partes[1])
                    dia_con_datos = int(partes[2])
                else:
                    dia_con_datos = int(ultimo_dia_venta[-2:])
                    mes_ultimo = mes_final
                    anio_ultimo = anio_final
            else:
                dia_con_datos = ultimo_dia_venta.day
                mes_ultimo = ultimo_dia_venta.month
                anio_ultimo = ultimo_dia_venta.year
            
            logging.info(f"MPRO {server['name']} - Último día con ventas: {anio_ultimo}-{mes_ultimo:02d}-{dia_con_datos:02d}")
            
            # CORRECCIÓN: Usar el mes y año del último día con ventas, no del mes inicial
            ff = f"{anio_ultimo}{str(mes_ultimo).zfill(2)}{str(dia_con_datos).zfill(2)}"
            
            # Calcular días transcurridos desde fecha_ini hasta el último día con ventas
            fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
            fecha_ultimo_dt = datetime(anio_ultimo, mes_ultimo, dia_con_datos)
            dias_transcurridos = (fecha_ultimo_dt - fecha_ini_dt).days + 1
            
            logging.info(f"MPRO {server['name']} - Período ajustado: {fi} a {ff}, días: {dias_transcurridos}")
            
            # Recalcular fechas de comparación basadas en días reales
            mes_actual = mes_ultimo  # Usar el mes del último día con ventas
            anio_actual = anio_ultimo
            
            # Mes anterior
            if mes_actual == 1:
                mes_ant = 12
                anio_ant = anio_actual - 1
            else:
                mes_ant = mes_actual - 1
                anio_ant = anio_actual
            
            max_dia_mes_ant = calendar.monthrange(anio_ant, mes_ant)[1]
            dia_comparar = min(dia_con_datos, max_dia_mes_ant)
            fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
            fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
            
            # Año anterior - usar el RANGO completo de meses (desde mes_min hasta mes_max)
            # Extraer mes_min de fecha_ini
            mes_min = int(fecha_ini[5:7])
            anio_pasado = int(fecha_ini[:4]) - 1
            
            # fecha_ini_año_ant: primer día del primer mes del año anterior
            fecha_ini_año_ant = f"{anio_pasado}-{str(mes_min).zfill(2)}-01"
            
            # fecha_fin_año_ant: mismo día del año anterior
            max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_ultimo)[1]
            dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
            fecha_fin_año_ant = f"{anio_pasado}-{str(mes_ultimo).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
            
            logging.info(f"MPRO Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
    except Exception as e:
        logging.warning(f"MPRO Error detectando último día: {e}")
    
    # MPRO usa Vn_Folio para identificar tickets y Vn_Precio_Neto_Importe para el monto de venta
    query = f"""
SELECT 
    COUNT(DISTINCT Vn_Folio) as cheques,
    ISNULL(SUM(Vn_Precio_Neto_Importe), 0) as ventas
FROM Venta
WHERE Vn_Fecha >= '{fi}' AND Vn_Fecha <= '{ff} 23:59:59'
  AND ISNULL(Es_Cve_Estado, '') <> 'CA'
"""
    try:
        result = execute_sql_query(server['host'], server['port'], server['database'], 
                                   server['username'], server['password'], query)
        if result and len(result) > 0:
            ventas = float(result[0]['ventas'] or 0)
            cheques = int(result[0]['cheques'] or 0)
        else:
            ventas, cheques = 0, 0
        logging.info(f"MPRO {server['name']}: Ventas={ventas}, Cheques={cheques}")
    except Exception as e:
        logging.warning(f"Error consultando MPRO {server['name']}: {e}")
        return None
    
    # MPRO no tiene PAX normalmente, estimamos como cheques
    pax = cheques
    
    # Mes anterior
    fia = fecha_ini_ant.replace('-', '')
    ffa = fecha_fin_ant.replace('-', '')
    query_ant = f"""
SELECT ISNULL(SUM(Vn_Precio_Neto_Importe), 0) as ventas, COUNT(DISTINCT Vn_Folio) as cheques
FROM Venta WHERE Vn_Fecha >= '{fia}' AND Vn_Fecha <= '{ffa} 23:59:59' AND ISNULL(Es_Cve_Estado, '') <> 'CA'
"""
    try:
        r_ant = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], query_ant)
        ventas_ant = float(r_ant[0]['ventas'] or 0) if r_ant else 0
        cheques_ant = int(r_ant[0]['cheques'] or 0) if r_ant else 0
    except:
        ventas_ant, cheques_ant = 0, 0
    pax_ant = cheques_ant
    
    # Año anterior
    fiaa = fecha_ini_año_ant.replace('-', '')
    ffaa = fecha_fin_año_ant.replace('-', '')
    query_año = f"""
SELECT ISNULL(SUM(Vn_Precio_Neto_Importe), 0) as ventas, COUNT(DISTINCT Vn_Folio) as cheques
FROM Venta WHERE Vn_Fecha >= '{fiaa}' AND Vn_Fecha <= '{ffaa} 23:59:59' AND ISNULL(Es_Cve_Estado, '') <> 'CA'
"""
    try:
        r_año = execute_sql_query(server['host'], server['port'], server['database'], server['username'], server['password'], query_año)
        ventas_año = float(r_año[0]['ventas'] or 0) if r_año else 0
        cheques_año = int(r_año[0]['cheques'] or 0) if r_año else 0
    except:
        ventas_año, cheques_año = 0, 0
    pax_año = cheques_año
    
    # Cálculos
    ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
    cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
    proyeccion = round((ventas / dias_transcurridos) * dias_mes, 2) if dias_transcurridos > 0 else 0
    
    # Variaciones %
    var_vs_mes_ant = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
    var_vs_año_ant = round(((ventas - ventas_año) / ventas_año * 100), 1) if ventas_año > 0 else 0
    var_pax_mes = round(((pax - pax_ant) / pax_ant * 100), 1) if pax_ant > 0 else 0
    var_pax_año = round(((pax - pax_año) / pax_año * 100), 1) if pax_año > 0 else 0
    var_cheques_mes = round(((cheques - cheques_ant) / cheques_ant * 100), 1) if cheques_ant > 0 else 0
    var_cheques_año = round(((cheques - cheques_año) / cheques_año * 100), 1) if cheques_año > 0 else 0
    
    return {
        "ventas": ventas,
        "ventas_ant": ventas_ant,
        "ventas_año": ventas_año,
        "var_vs_mes_ant": var_vs_mes_ant,
        "var_vs_año_ant": var_vs_año_ant,
        "proyeccion": proyeccion,
        "pax": pax,
        "pax_ant": pax_ant,
        "pax_año": pax_año,
        "var_pax_mes": var_pax_mes,
        "var_pax_año": var_pax_año,
        "cheques": cheques,
        "cheques_ant": cheques_ant,
        "cheques_año": cheques_año,
        "var_cheques_mes": var_cheques_mes,
        "var_cheques_año": var_cheques_año,
        "ticket_prom": ticket_prom,
        "cheque_prom": cheque_prom
    }


def get_kpis_mpro_por_sucursal(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia=False):
    """
    Query para MPRO que devuelve KPIs DIVIDIDOS POR SUCURSAL (como en Inventarios).
    Retorna una lista de unidades, no un solo bloque.
    
    FASE 3.1 - COMPORTAMIENTO:
    - solo_ventas_dia=True → Intenta API local. Si falla, usa SQL nube (ventas acumuladas sin ventas del día)
    - solo_ventas_dia=False → Usa SQL nube del menú Servidores
    
    NOTA: Si API local no responde, se muestran ventas acumuladas.
    PENDIENTE: Inspección local en servidores para revisar por qué no levanta SQL local o API local.
    """
    
    logging.debug(f"MPRO {server['name']}: solo_ventas_dia={solo_ventas_dia}, fecha_ini={fecha_ini}, fecha_fin={fecha_fin}")
    
    # ============================================================================
    # VENTAS DEL DÍA: Intentar API local primero
    # ============================================================================
    if solo_ventas_dia:
        logging.info(f"MPRO {server['name']}: Modo Ventas del Día - intentando API local")
        
        # NOTA: sumar_ventas_api_local_a_sucursal se importa globalmente en la línea 29
        from datetime import datetime as dt_local
        
        hoy = dt_local.now()
        
        # Mapeo de sucursales MPRO conocidas para buscar en APIs locales
        sucursales_mpro = [
            {"nombre": "ORIGEN", "sucursal_id": "ORIGEN"},
            {"nombre": "QUERETARO", "sucursal_id": "130_QRO"},
        ]
        
        unidades = []
        api_local_funciono = False
        
        for suc in sucursales_mpro:
            try:
                ventas_api = sumar_ventas_api_local_a_sucursal(
                    server_host=server['host'],
                    sucursal_nombre=suc['nombre'],
                    fecha_fin=fecha_fin,
                    mes_solicitado=hoy.month,
                    anio_solicitado=hoy.year,
                    solo_ventas_dia=True
                )
                
                if ventas_api.get("aplicado", False) and ventas_api.get("ventas", 0) > 0:
                    # Solo contar como éxito si realmente hay ventas
                    api_local_funciono = True
                    ventas = ventas_api.get("ventas", 0)
                    cheques = ventas_api.get("cheques", 0)
                    pax = ventas_api.get("pax", 0) or cheques
                    
                    ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
                    cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
                    
                    unidades.append({
                        "unidad": suc['nombre'],
                        "server_id": server['id'],
                        "system_type": "MPRO",
                        "ventas": ventas,
                        "ventas_ant": 0,
                        "ventas_año": 0,
                        "var_vs_mes_ant": 0,
                        "var_vs_año_ant": 0,
                        "proyeccion": 0,
                        "pax": pax,
                        "pax_ant": 0,
                        "pax_año": 0,
                        "var_pax_mes": 0,
                        "var_pax_año": 0,
                        "cheques": cheques,
                        "cheques_ant": 0,
                        "cheques_año": 0,
                        "var_cheques_mes": 0,
                        "var_cheques_año": 0,
                        "ticket_prom": ticket_prom,
                        "cheque_prom": cheque_prom,
                        "es_ventas_dia": True,
                        "origen": "api_local"
                    })
                    logging.info(f"MPRO {server['name']} - {suc['nombre']}: API local OK - ${ventas:,.2f}")
            except Exception as e:
                logging.warning(f"MPRO {server['name']} - {suc['nombre']}: API local error - {e}")
        
        if api_local_funciono and unidades:
            return unidades
        
        # ============================================================================
        # API LOCAL FALLÓ EN MODO VENTAS DEL DÍA
        # ============================================================================
        # REGLA CRÍTICA: Si es "ventas del día" y la API local no funciona,
        # NO contaminar con datos acumulados del mes. Retornar lista vacía.
        # El usuario pidió explícitamente ver SOLO las ventas del día.
        logging.warning(f"MPRO {server['name']}: API local no disponible - SIN DATOS para ventas del día")
        return []
    
    # ============================================================================
    # VENTAS HISTÓRICAS / ACUMULADAS: Usar SQL nube del menú Servidores
    # (Solo se ejecuta si solo_ventas_dia=False)
    # ============================================================================
    
    logging.debug(f"MPRO SQL NUBE: {server['host']}:{server['port']}/{server['database']}")
    logging.debug(f"MPRO SQL NUBE: Fechas {fecha_ini} a {fecha_fin}")
    
    # VALIDACIÓN DE RANGO DE FECHAS (FIX ESTRUCTURAL)
    # Usar helper centralizado para evitar rangos inválidos
    if not is_valid_range(fecha_ini, fecha_fin):
        logging.error(f"MPRO {server['name']}: Rango de fechas inválido ({fecha_ini} > {fecha_fin})")
        return []
    
    # Formato YYYYMMDD para MPRO (SQL Server con configuración regional español)
    try:
        fi, ff = to_yyyymmdd_range(fecha_ini, fecha_fin)
    except ValueError as e:
        logging.error(f"MPRO {server['name']}: Error convirtiendo fechas: {e}")
        return []
    
    logging.debug(f"MPRO SQL: fi={fi}, ff={ff}")
    
    # Extraer mes y año de fecha_fin para usarlos en recálculos (importante para multiselección de meses)
    mes_final = int(fecha_fin[5:7])  # Mes de fecha_fin (ej: 04 para abril)
    anio_final = int(fecha_fin[:4])  # Año de fecha_fin
    
    # PASO 1: Detectar el último día real con ventas en el período
    query_ultimo_dia = f"""
SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
FROM Venta_Encabezado VE
WHERE VE.Vn_Fecha >= '{fi}' AND VE.Vn_Fecha <= '{ff}'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""
    try:
        result_ultimo = execute_sql_query(server['host'], server['port'], server['database'], 
                                          server['username'], server['password'], query_ultimo_dia)
        if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
            ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
            if isinstance(ultimo_dia_venta, str):
                # Parsear la fecha completa (YYYY-MM-DD)
                partes = ultimo_dia_venta.split('-') if '-' in ultimo_dia_venta else None
                if partes and len(partes) == 3:
                    anio_ultimo = int(partes[0])
                    mes_ultimo = int(partes[1])
                    dia_con_datos = int(partes[2])
                else:
                    dia_con_datos = int(ultimo_dia_venta[-2:])
                    mes_ultimo = mes_final
                    anio_ultimo = anio_final
            else:
                dia_con_datos = ultimo_dia_venta.day
                mes_ultimo = ultimo_dia_venta.month
                anio_ultimo = ultimo_dia_venta.year
            
            logging.debug(f"MPRO por sucursal {server['name']} - Ultimo dia con ventas: {anio_ultimo}-{mes_ultimo:02d}-{dia_con_datos:02d}")
            
            # CORRECCIÓN: Usar el mes y año del último día con ventas, no del mes inicial
            ff = f"{anio_ultimo}{str(mes_ultimo).zfill(2)}{str(dia_con_datos).zfill(2)}"
            
            # Calcular días transcurridos desde fecha_ini hasta el último día con ventas
            fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
            fecha_ultimo_dt = datetime(anio_ultimo, mes_ultimo, dia_con_datos)
            dias_transcurridos = (fecha_ultimo_dt - fecha_ini_dt).days + 1
            
            logging.debug(f"MPRO por sucursal {server['name']} - Período ajustado: {fi} a {ff}, días: {dias_transcurridos}")
            
            # Recalcular fechas de comparación basadas en días reales
            mes_actual = mes_ultimo  # Usar el mes del último día con ventas
            anio_actual = anio_ultimo
            
            # Mes anterior
            if mes_actual == 1:
                mes_ant = 12
                anio_ant = anio_actual - 1
            else:
                mes_ant = mes_actual - 1
                anio_ant = anio_actual
            
            max_dia_mes_ant = calendar.monthrange(anio_ant, mes_ant)[1]
            dia_comparar = min(dia_con_datos, max_dia_mes_ant)
            fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
            fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
            
            # Año anterior - usar el RANGO completo de meses (desde mes_min hasta mes_max)
            mes_min = int(fecha_ini[5:7])
            anio_pasado = int(fecha_ini[:4]) - 1
            
            fecha_ini_año_ant = f"{anio_pasado}-{str(mes_min).zfill(2)}-01"
            
            max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_ultimo)[1]
            dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
            fecha_fin_año_ant = f"{anio_pasado}-{str(mes_ultimo).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
            
            logging.info(f"MPRO por sucursal Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
    except Exception as e:
        logging.warning(f"MPRO por sucursal Error detectando último día: {e}")
    
    fia = fecha_ini_ant.replace('-', '')
    ffa = fecha_fin_ant.replace('-', '')
    fiaa = fecha_ini_año_ant.replace('-', '')
    ffaa = fecha_fin_año_ant.replace('-', '')
    
    logging.info(f"MPRO {server['name']}: Consultando ventas del {fi} al {ff}")
    
    # Query principal agrupando por sucursal - INCLUYE PAX desde Comanda
    # IMPORTANTE: Usar formato YYYYMMDD para evitar errores de conversión regional
    query = f"""
SELECT 
    S.Sc_Cve_Sucursal as sucursal_id,
    S.Sc_Descripcion as sucursal_nombre,
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{fi}' AND VE.Vn_Fecha <= '{ff}'
GROUP BY S.Sc_Cve_Sucursal, S.Sc_Descripcion
ORDER BY SUM(VE.Vn_Precio_Neto_Importe) DESC
"""
    
    try:
        logging.debug(f"MPRO: Ejecutando query principal con fechas {fi} a {ff}")
        result = execute_sql_query(server['host'], server['port'], server['database'], 
                                   server['username'], server['password'], query)
        logging.debug(f"MPRO: Query principal retornó {len(result) if result else 0} filas")
        if result:
            for r in result[:3]:
                logging.debug(f"  Fila: sucursal={r.get('sucursal_id')}, ventas={r.get('ventas')}, cheques={r.get('cheques')}")
        if not result:
            logging.warning(f"MPRO {server['name']}: No se encontraron sucursales con ventas")
            return []
    except Exception as e:
        logging.warning(f"Error consultando MPRO por sucursal {server['name']}: {e}")
        return []
    
    unidades = []
    
    for row in result:
        sucursal_id = row.get('sucursal_id', '')
        sucursal_nombre = row.get('sucursal_nombre', 'Sin nombre')
        ventas = float(row.get('ventas') or 0)
        cheques = int(row.get('cheques') or 0)
        pax = int(row.get('pax') or 0)  # PAX real desde Comanda.Co_Personas
        
        # Si PAX es 0 pero hay cheques, estimamos PAX = cheques (1 persona por ticket mínimo)
        if pax == 0 and cheques > 0:
            pax = cheques
        
        # PASO 2: Detectar el último día con ventas PARA ESTA SUCURSAL específica
        query_ultimo_dia_suc = f"""
SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
FROM Venta_Encabezado VE
WHERE VE.Sc_Cve_Sucursal = '{sucursal_id}'
  AND VE.Vn_Fecha >= '{fi}' AND VE.Vn_Fecha <= '{ff}'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""
        try:
            result_ultimo_suc = execute_sql_query(server['host'], server['port'], server['database'], 
                                                  server['username'], server['password'], query_ultimo_dia_suc)
            if result_ultimo_suc and result_ultimo_suc[0]['ultimo_dia_venta']:
                ultimo_dia_suc = result_ultimo_suc[0]['ultimo_dia_venta']
                if isinstance(ultimo_dia_suc, str):
                    dia_suc = int(ultimo_dia_suc.split('-')[2]) if '-' in ultimo_dia_suc else int(ultimo_dia_suc[-2:])
                else:
                    dia_suc = ultimo_dia_suc.day
                
                logging.debug(f"MPRO {sucursal_nombre} - Ultimo dia con ventas: dia {dia_suc}")
                
                # Recalcular fechas de comparación para esta sucursal
                mes_actual = int(fi[4:6])
                anio_actual = int(fi[:4])
                
                # Mes anterior
                if mes_actual == 1:
                    mes_ant = 12
                    anio_ant = anio_actual - 1
                else:
                    mes_ant = mes_actual - 1
                    anio_ant = anio_actual
                
                max_dia_mes_ant = calendar.monthrange(anio_ant, mes_ant)[1]
                dia_comparar = min(dia_suc, max_dia_mes_ant)
                fia_suc = f"{anio_ant}{str(mes_ant).zfill(2)}01"
                ffa_suc = f"{anio_ant}{str(mes_ant).zfill(2)}{str(dia_comparar).zfill(2)}"
                
                # Año anterior - CORRECCIÓN: Usar el RANGO COMPLETO de meses
                # fiaa y ffaa ya están calculadas correctamente a nivel global (desde mes_min hasta mes_max del año anterior)
                # Solo necesitamos ajustar ffaa al día correcto de esta sucursal específica
                anio_pasado = anio_actual - 1
                # Obtener el mes final del rango (mes del último día con ventas global)
                mes_final_rango = int(ffaa[4:6])  # ffaa tiene formato YYYYMMDD
                max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_final_rango)[1]
                dia_ano_ant = min(dia_suc, max_dia_ano_ant)
                # PRESERVAR el mes inicial de fiaa (rango completo desde enero o el mes inicial seleccionado)
                fiaa_suc = fiaa  # Ya tiene el formato correcto con mes inicial
                ffaa_suc = f"{anio_pasado}{str(mes_final_rango).zfill(2)}{str(dia_ano_ant).zfill(2)}"
            else:
                # Si no hay datos, usar fechas globales
                fia_suc, ffa_suc = fia, ffa
                fiaa_suc, ffaa_suc = fiaa, ffaa
                dia_suc = dias_transcurridos
        except Exception as e:
            logging.warning(f"Error detectando ultimo dia para {sucursal_nombre}: {e}")
            fia_suc, ffa_suc = fia, ffa
            fiaa_suc, ffaa_suc = fiaa, ffaa
            dia_suc = dias_transcurridos
        
        # Query mes anterior para esta sucursal - con PAX (formato YYYYMMDD)
        query_ant = f"""
SELECT 
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas, 
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Sc_Cve_Sucursal = '{sucursal_id}'
  AND VE.Vn_Fecha >= '{fia_suc}' AND VE.Vn_Fecha <= '{ffa_suc} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""
        try:
            r_ant = execute_sql_query(server['host'], server['port'], server['database'], 
                                      server['username'], server['password'], query_ant)
            ventas_ant = float(r_ant[0]['ventas'] or 0) if r_ant else 0
            cheques_ant = int(r_ant[0]['cheques'] or 0) if r_ant else 0
            pax_ant = int(r_ant[0]['pax'] or 0) if r_ant else 0
            if pax_ant == 0 and cheques_ant > 0:
                pax_ant = cheques_ant
        except:
            ventas_ant, cheques_ant, pax_ant = 0, 0, 0
        
        # Query año anterior para esta sucursal - con PAX (formato YYYYMMDD)
        query_año = f"""
SELECT 
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas, 
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Sc_Cve_Sucursal = '{sucursal_id}'
  AND VE.Vn_Fecha >= '{fiaa_suc}' AND VE.Vn_Fecha <= '{ffaa_suc} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""
        try:
            r_año = execute_sql_query(server['host'], server['port'], server['database'], 
                                      server['username'], server['password'], query_año)
            ventas_año = float(r_año[0]['ventas'] or 0) if r_año else 0
            cheques_año = int(r_año[0]['cheques'] or 0) if r_año else 0
            pax_año = int(r_año[0]['pax'] or 0) if r_año else 0
            if pax_año == 0 and cheques_año > 0:
                pax_año = cheques_año
        except:
            ventas_año, cheques_año, pax_año = 0, 0, 0
        
        # ============= INTEGRACIÓN API LOCAL =============
        # Sumar ventas del día desde API local si aplica
        # Solo se suma si: el período incluye HOY y estamos ANTES de la hora de réplica
        # En modo "Ventas del Día" (solo_ventas_dia=True): las ventas de API local REEMPLAZAN las de nube
        ventas_api_local = sumar_ventas_api_local_a_sucursal(
            server_host=server['host'],
            sucursal_nombre=sucursal_nombre,
            fecha_fin=fecha_fin,  # fecha_fin original en formato YYYY-MM-DD
            mes_solicitado=mes_final,
            anio_solicitado=anio_final,
            solo_ventas_dia=solo_ventas_dia  # Pasar flag para modo Ventas del Día
        )
        
        if ventas_api_local.get("aplicado", False):
            if ventas_api_local.get("reemplazar", False):
                # Modo "Ventas del Día": REEMPLAZAR datos de nube con API local
                # Si hay ventas reales en la API local, usar esas
                if ventas_api_local["ventas"] > 0 or ventas_api_local["cheques"] > 0:
                    ventas = ventas_api_local["ventas"]
                    cheques = ventas_api_local["cheques"]
                    pax = ventas_api_local["pax"]
                    logging.info(f"API Local REEMPLAZÓ datos de {sucursal_nombre}: ${ventas_api_local['ventas']:,.2f} de {ventas_api_local.get('api', 'N/A')}")
                else:
                    # API local retornó $0 - en modo Ventas del Día, usar $0 (no hay ventas hoy)
                    ventas = 0
                    cheques = 0
                    pax = 0
                    logging.info(f"API Local retornó $0 para {sucursal_nombre} - Ventas del día = $0")
            else:
                # Modo normal: SUMAR ventas de API local a las de nube
                ventas += ventas_api_local["ventas"]
                cheques += ventas_api_local["cheques"]
                pax += ventas_api_local["pax"]
                logging.info(f"API Local sumada a {sucursal_nombre}: +${ventas_api_local['ventas']:,.2f} de {ventas_api_local.get('api', 'N/A')}")
        elif solo_ventas_dia:
            # Modo "Ventas del Día" pero no hay API local configurada o no aplicó
            # Las ventas deben ser $0 (no mostrar el acumulado del mes)
            ventas = 0
            cheques = 0
            pax = 0
            logging.info(f"Modo Ventas del Día pero sin API local para {sucursal_nombre} - Ventas = $0")
        # Si no es modo ventas del día y no hay API local, mantener datos de la nube (ya asignados)
        # ============= FIN INTEGRACIÓN API LOCAL =============
        
        # Cálculos
        ticket_prom = round(ventas / pax, 2) if pax > 0 else 0
        cheque_prom = round(ventas / cheques, 2) if cheques > 0 else 0
        proyeccion = round((ventas / dias_transcurridos) * dias_mes, 2) if dias_transcurridos > 0 else 0
        
        # Variaciones %
        var_vs_mes_ant = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
        var_vs_año_ant = round(((ventas - ventas_año) / ventas_año * 100), 1) if ventas_año > 0 else 0
        
        logging.debug(f"MPRO {sucursal_nombre}: Dia={dia_suc}, Actual={ventas:.2f}, MesAnt({fia_suc}-{ffa_suc})={ventas_ant:.2f} -> {var_vs_mes_ant}%, AnoAnt({fiaa_suc}-{ffaa_suc})={ventas_año:.2f} -> {var_vs_año_ant}%")
        var_pax_mes = round(((pax - pax_ant) / pax_ant * 100), 1) if pax_ant > 0 else 0
        var_pax_año = round(((pax - pax_año) / pax_año * 100), 1) if pax_año > 0 else 0
        var_cheques_mes = round(((cheques - cheques_ant) / cheques_ant * 100), 1) if cheques_ant > 0 else 0
        var_cheques_año = round(((cheques - cheques_año) / cheques_año * 100), 1) if cheques_año > 0 else 0
        
        unidades.append({
            "unidad": sucursal_nombre,
            "sucursal": sucursal_nombre,  # Para filtrar en endpoints de detalle
            "server_id": server['id'],
            "sucursal_id": sucursal_id,
            "system_type": "MPRO",
            "parent_server": server['name'],
            "ventas": ventas,
            "ventas_ant": ventas_ant,
            "ventas_año": ventas_año,
            "var_vs_mes_ant": var_vs_mes_ant,
            "var_vs_año_ant": var_vs_año_ant,
            "proyeccion": proyeccion,
            "pax": pax,
            "pax_ant": pax_ant,
            "pax_año": pax_año,
            "var_pax_mes": var_pax_mes,
            "var_pax_año": var_pax_año,
            "cheques": cheques,
            "cheques_ant": cheques_ant,
            "cheques_año": cheques_año,
            "var_cheques_mes": var_cheques_mes,
            "var_cheques_año": var_cheques_año,
            "ticket_prom": ticket_prom,
            "cheque_prom": cheque_prom
        })
        
        logging.info(f"MPRO {server['name']} - Sucursal '{sucursal_nombre}': Ventas={ventas}, Cheques={cheques}")
    
    return unidades


__all__ = [
    # Auxiliares
    'calcular_ticket_promedio',
    'calcular_consumo_promedio',
    'calcular_porcentaje_cumplimiento',
    # Procesamiento
    'procesar_ventas_sucursal',
    'agregar_totales',
    # Datos
    'obtener_sucursales_servidor',
    'obtener_metas',
    'guardar_metas',
    # Helpers del Tablero Ejecutivo (Migrados FASE 5B-2)
    'get_kpis_softrestaurant',
    'get_kpis_mpro',
    'get_kpis_mpro_por_sucursal',
]
