"""
EDARSA HUB - Comercial Module Routes
====================================
Endpoints del módulo comercial.

FASE 5B DEL REFACTOR MODULAR (Abril 2026):

ESTADO ACTUAL:
- ✅ Adapters (APIs locales MPRO) migrados a adapters.py
- ✅ Helpers del tablero migrados a service.py (Fase 5B-2)
- ✅ Endpoint /comercial/tablero-ejecutivo migrado (Fase 5B-3)
- ⏸️ Resto de endpoints pendientes de migrar (permanecen en server.py)

COMPONENTES MIGRADOS:
1. adapters.py:
   - APIS_MPRO_LOCALES (configuración)
   - query_api_mpro_local()
   - obtener_ventas_dia_api_local()
   - sumar_ventas_api_local_a_sucursal()

2. service.py:
   - get_kpis_softrestaurant()
   - get_kpis_mpro()
   - get_kpis_mpro_por_sucursal()

3. routes.py (este archivo):
   - GET /comercial/tablero-ejecutivo

ENDPOINTS PENDIENTES (9 total en server.py):
- GET /comercial/dashboard/{server_id} - Dashboard principal
- GET /comercial/ticket-perfecto/{server_id} - Análisis de ticket perfecto
- GET /comercial/metas/{server_id} - Metas por sucursal
- GET /comercial/ventas-tiempo/{server_id} - Ventas por tiempo
- GET /comercial/mesas/{server_id} - Estado de mesas
- GET /comercial/detalle-movimientos/{server_id} - Detalle de movimientos
- GET /comercial/reporte-pax/{server_id} - Reporte PAX (más complejo)
- GET /comercial/sucursales/{server_id} - Lista de sucursales
- GET /comercial/precios-constantes/{server_id} - Precios constantes
"""

from fastapi import APIRouter, Query, Depends
from typing import Dict
import logging
import calendar
from datetime import datetime, timedelta, timezone

from core.security import get_current_user
from modules.comercial.service import (
    get_kpis_softrestaurant,
    get_kpis_mpro,
    get_kpis_mpro_por_sucursal,
)
from modules.comercial.repository import (
    get_servers_for_tablero,
    get_cached_kpis,
    save_kpis_cache,
    get_cached_kpis_by_prefix,
    save_server_connection_status,
    is_server_recently_offline,
)

# Router - los endpoints serán migrados incrementalmente
router = APIRouter(tags=["comercial"])


@router.get("/comercial/tablero-ejecutivo")
async def tablero_ejecutivo(
    mes: int = Query(default=0),  # 0 = mes actual (legacy, compatibilidad)
    anio: int = Query(default=0),  # 0 = año actual, -1 = ventas del día (legacy)
    meses: str = Query(default=""),  # "01,02,03" - Lista de meses (nuevo, multiselección)
    anios: str = Query(default=""),  # "2025,2024" - Lista de años (nuevo, multiselección)
    periodo: str = Query(default="mes"),  # dia, semana, mes (nuevo)
    tipo_comparacion: str = Query(default="dias_equiv"),  # dias_equiv o mes_completo (nuevo)
    current_user: Dict = Depends(get_current_user)
):
    """
    Tablero ejecutivo con KPIs de TODAS las unidades.
    Comparativo vs mes anterior y año anterior (mismos días).
    Soporta multiselección de meses y años (homologado con Dashboard Comercial).
    anio=-1 o anios="-1": Modo "Ventas del Día" - solo tempcheques (ventas sin corte).
    """
    hoy = datetime.now()
    
    # Detectar modo "Ventas del Día" (anio=-1 legacy o anios="-1" nuevo o meses="ventas_dia")
    solo_ventas_dia = (anio == -1) or (anios == "-1") or (meses == "ventas_dia")
    
    # Procesar parámetros nuevos (multiselección) o legacy (simple)
    mes_min = None  # Para multiselección de meses
    mes_max = None
    
    if meses and meses != "ventas_dia" and not solo_ventas_dia:
        # Nuevo formato: multiselección de meses (solo si son números)
        try:
            lista_meses = [int(m.strip()) for m in meses.split(',') if m.strip() and m.strip().isdigit()]
            if lista_meses:
                mes_min = min(lista_meses)  # Primer mes del rango
                mes_max = max(lista_meses)  # Último mes del rango
                mes = mes_max  # Para compatibilidad con lógica existente
            else:
                # Si no hay meses válidos, usar mes actual
                mes = hoy.month
                mes_min = mes
                mes_max = mes
        except ValueError:
            # Si falla la conversión, usar mes actual
            mes = hoy.month
            mes_min = mes
            mes_max = mes
    elif mes == 0:
        mes = hoy.month
        mes_min = mes
        mes_max = mes
    else:
        mes_min = mes
        mes_max = mes
    
    if anios and anios != "-1":
        # Nuevo formato: multiselección de años
        lista_anios = [int(a.strip()) for a in anios.split(',') if a.strip()]
        anio = max(lista_anios)  # Usar el año más reciente
    elif anio == 0 or anio == -1:
        if not solo_ventas_dia:
            anio = hoy.year
        else:
            anio = hoy.year  # Para ventas del día, usar año actual
    
    # Fechas del período actual - CORREGIDO para multiselección de meses
    # fecha_ini: primer día del PRIMER mes seleccionado
    fecha_ini = f"{anio}-{mes_min:02d}-01"
    
    # fecha_fin: depende de si el último mes es el actual o ya pasó
    if anio == hoy.year and mes_max == hoy.month:
        # Mes actual incompleto - ventas hasta AYER (hoy no se cuenta)
        ayer = hoy - timedelta(days=1)
        fecha_fin = ayer.strftime('%Y-%m-%d')
        # Calcular días transcurridos desde inicio del rango hasta ayer
        fecha_inicio_dt = datetime(anio, mes_min, 1)
        dias_transcurridos = (ayer - fecha_inicio_dt).days + 1
    elif anio == hoy.year and mes_max > hoy.month:
        # Meses futuros seleccionados - usar hasta el día actual
        fecha_fin = hoy.strftime('%Y-%m-%d')
        fecha_inicio_dt = datetime(anio, mes_min, 1)
        dias_transcurridos = (hoy - fecha_inicio_dt).days + 1
    else:
        # Todos los meses seleccionados ya pasaron - usar meses completos
        ultimo_dia = calendar.monthrange(anio, mes_max)[1]
        fecha_fin = f"{anio}-{mes_max:02d}-{ultimo_dia:02d}"
        # Calcular días totales del rango completo
        fecha_inicio_dt = datetime(anio, mes_min, 1)
        fecha_fin_dt = datetime(anio, mes_max, ultimo_dia)
        dias_transcurridos = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    # Calcular días totales del período (si todo el rango estuviera completo)
    if mes_max == 12:
        fecha_fin_completo = datetime(anio + 1, 1, 1) - timedelta(days=1)
    else:
        fecha_fin_completo = datetime(anio, mes_max + 1, 1) - timedelta(days=1)
    fecha_inicio_dt = datetime(anio, mes_min, 1)
    dias_mes = (fecha_fin_completo - fecha_inicio_dt).days + 1
    
    # Mes anterior (para comparar vs período anterior)
    if mes_min == 1:
        mes_ant_ini = 12 - (mes_max - mes_min)  # Mismo número de meses, pero del año anterior
        if mes_ant_ini < 1:
            mes_ant_ini = 1
        mes_ant_fin = 12
        anio_mes_ant = anio - 1
    else:
        # Período anterior del mismo año
        meses_en_rango = mes_max - mes_min + 1
        mes_ant_ini = mes_min - meses_en_rango
        if mes_ant_ini < 1:
            mes_ant_ini = 1
        mes_ant_fin = mes_min - 1
        anio_mes_ant = anio
    
    fecha_ini_ant = f"{anio_mes_ant}-{mes_ant_ini:02d}-01"
    # Para período anterior, usar mismos días transcurridos
    ultimo_dia_ant = calendar.monthrange(anio_mes_ant, mes_ant_fin)[1]
    fecha_fin_ant = f"{anio_mes_ant}-{mes_ant_fin:02d}-{ultimo_dia_ant:02d}"
    
    # Año anterior (MISMO RANGO DE MESES Y DÍAS - esto es lo que estaba mal)
    # Si estamos viendo 01-ene a 08-abr 2026, comparar con 01-ene a 08-abr 2025
    fecha_ini_año_ant = f"{anio-1}-{mes_min:02d}-01"
    
    # Calcular el día final del año anterior equivalente
    if anio == hoy.year and mes_max >= hoy.month:
        # Si estamos en el año actual y el mes actual está en el rango,
        # comparar hasta el mismo día del año anterior
        if mes_max == hoy.month:
            dia_fin_año_ant = min(hoy.day - 1, calendar.monthrange(anio-1, mes_max)[1])
        else:
            dia_fin_año_ant = min(hoy.day, calendar.monthrange(anio-1, mes_max)[1])
        fecha_fin_año_ant = f"{anio-1}-{mes_max:02d}-{dia_fin_año_ant:02d}"
    else:
        # Meses completos, comparar con meses completos del año anterior
        ultimo_dia_año_ant = calendar.monthrange(anio-1, mes_max)[1]
        fecha_fin_año_ant = f"{anio-1}-{mes_max:02d}-{ultimo_dia_año_ant:02d}"
    
    # Año anterior MES COMPLETO (para comparar proyección vs período completo)
    ultimo_dia_año_ant_completo = calendar.monthrange(anio-1, mes_max)[1]
    fecha_fin_año_ant_completo = f"{anio-1}-{mes_max:02d}-{ultimo_dia_año_ant_completo:02d}"
    
    logging.info(f"Tablero Ejecutivo: {mes_min}-{mes_max}/{anio} ({fecha_ini} a {fecha_fin}), días: {dias_transcurridos}/{dias_mes}")
    logging.info(f"Tablero Ejecutivo - Año anterior: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
    
    # Obtener todos los servidores activos Y visibles en operaciones
    servers = await get_servers_for_tablero()
    logging.info(f"Servidores encontrados: {len(servers)} - Tipos: {[s['system_type'] for s in servers]}")
    
    # Filtrar por permisos del usuario
    if current_user.get('role') != 'Administrador':
        allowed = current_user.get('allowed_servers', [])
        servers = [s for s in servers if s['id'] in allowed]
    
    resultados = []
    totales = {"ventas": 0, "ventas_ant": 0, "ventas_año": 0, "ventas_año_completo": 0, "pax": 0, "pax_ant": 0, "pax_año": 0, 
               "cheques": 0, "cheques_ant": 0, "cheques_año": 0, "proyeccion": 0}
    
    periodo_key = f"{anio}-{mes:02d}"
    
    for server in servers:
        logging.info(f"Procesando servidor: {server['name']} - Tipo: {server['system_type']}")
        
        # Verificar si el servidor está offline recientemente (evitar timeouts)
        server_offline = await is_server_recently_offline(server['id'], minutes_threshold=10)
        
        if server['system_type'] == 'SoftRestaurant':
            kpis = None
            
            # Solo intentar conexión si el servidor NO está marcado como offline recientemente
            if not server_offline:
                kpis = get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant,
                                               fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia)
                if kpis:
                    # Conexión exitosa - marcar como online
                    await save_server_connection_status(server['id'], True)
                else:
                    # Conexión fallida - marcar como offline
                    await save_server_connection_status(server['id'], False)
            else:
                logging.info(f"Servidor {server['name']} marcado como offline - usando caché")
            
            if kpis:
                # Conexión exitosa - guardar en caché
                kpis["unidad"] = server['name']
                kpis["server_id"] = server['id']
                kpis["system_type"] = server['system_type']
                kpis["status"] = "online"
                kpis["updated_at"] = datetime.now(timezone.utc).isoformat()
                resultados.append(kpis)
                # Guardar en caché
                await save_kpis_cache(server['id'], periodo_key, kpis)
                # Acumular totales
                for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                          "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                    totales[k] += kpis.get(k, 0)
            else:
                # Conexión fallida - buscar en caché
                cached = await get_cached_kpis(server['id'], periodo_key)
                if cached and cached.get('kpis'):
                    kpis = cached['kpis']
                    kpis["status"] = "offline"
                    kpis["updated_at"] = cached.get('updated_at', '')
                    kpis["unidad"] = server['name']
                    kpis["server_id"] = server['id']
                    kpis["system_type"] = server['system_type']
                    resultados.append(kpis)
                    logging.info(f"Usando caché para {server['name']} - última actualización: {cached.get('updated_at')}")
                    # Acumular totales del caché
                    for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                              "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                        totales[k] += kpis.get(k, 0)
                else:
                    logging.warning(f"Sin caché disponible para {server['name']}")
        
        elif server['system_type'] == 'MPRO':
            # MPRO: Dividir por sucursal (igual que en Inventarios)
            logging.info(f"Procesando servidor MPRO: {server['name']}")
            try:
                unidades_mpro = get_kpis_mpro_por_sucursal(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant,
                                                           fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia)
                logging.info(f"MPRO {server['name']}: Encontradas {len(unidades_mpro)} unidades")
                for unidad in unidades_mpro:
                    unidad["status"] = "online"
                    unidad["updated_at"] = datetime.now(timezone.utc).isoformat()
                    resultados.append(unidad)
                    # Guardar en caché cada unidad
                    unidad_key = f"{periodo_key}-{unidad.get('unidad', 'unknown')}"
                    await save_kpis_cache(server['id'], unidad_key, unidad)
                    # Acumular totales
                    for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                              "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                        totales[k] += unidad.get(k, 0)
            except Exception as mpro_error:
                logging.error(f"Error procesando MPRO {server['name']}: {mpro_error}")
                # Buscar en caché para MPRO
                cached_list = await get_cached_kpis_by_prefix(server['id'], periodo_key)
                for cached in cached_list:
                    if cached.get('kpis'):
                        kpis = cached['kpis']
                        kpis["status"] = "offline"
                        kpis["updated_at"] = cached.get('updated_at', '')
                        resultados.append(kpis)
                        for k in ["ventas", "ventas_ant", "ventas_año", "pax", "pax_ant", "pax_año", 
                                  "cheques", "cheques_ant", "cheques_año", "proyeccion"]:
                            totales[k] += kpis.get(k, 0)
    
    # Calcular variaciones de totales
    totales["var_vs_mes_ant"] = round(((totales["ventas"] - totales["ventas_ant"]) / totales["ventas_ant"] * 100), 1) if totales["ventas_ant"] > 0 else 0
    totales["var_vs_año_ant"] = round(((totales["ventas"] - totales["ventas_año"]) / totales["ventas_año"] * 100), 1) if totales["ventas_año"] > 0 else 0
    totales["var_pax_mes"] = round(((totales["pax"] - totales["pax_ant"]) / totales["pax_ant"] * 100), 1) if totales["pax_ant"] > 0 else 0
    totales["var_pax_año"] = round(((totales["pax"] - totales["pax_año"]) / totales["pax_año"] * 100), 1) if totales["pax_año"] > 0 else 0
    totales["var_cheques_mes"] = round(((totales["cheques"] - totales["cheques_ant"]) / totales["cheques_ant"] * 100), 1) if totales["cheques_ant"] > 0 else 0
    totales["var_cheques_año"] = round(((totales["cheques"] - totales["cheques_año"]) / totales["cheques_año"] * 100), 1) if totales["cheques_año"] > 0 else 0
    totales["ticket_prom"] = round(totales["ventas"] / totales["pax"], 2) if totales["pax"] > 0 else 0
    totales["cheque_prom"] = round(totales["ventas"] / totales["cheques"], 2) if totales["cheques"] > 0 else 0
    
    # Estimar ventas del año anterior MES COMPLETO (proyección proporcional)
    # Si tenemos 7 días de año anterior con X ventas, el mes completo sería X * (días_mes / días_transcurridos)
    ventas_año_completo_estimado = (totales["ventas_año"] / dias_transcurridos * dias_mes) if dias_transcurridos > 0 and totales["ventas_año"] > 0 else 0
    totales["ventas_año_completo"] = round(ventas_año_completo_estimado, 0)
    
    # Proyección vs ventas año anterior MES COMPLETO (no solo los días equivalentes)
    totales["var_proy_vs_año"] = round(((totales["proyeccion"] - ventas_año_completo_estimado) / ventas_año_completo_estimado * 100), 1) if ventas_año_completo_estimado > 0 else 0
    
    # Contar unidades que tenían ventas el año anterior (ventas_año > 0)
    totales["unidades_año_ant"] = sum(1 for u in resultados if u.get("ventas_año", 0) > 0)
    
    # Ordenar unidades de mayor a menor venta
    resultados_ordenados = sorted(resultados, key=lambda x: x.get('ventas', 0), reverse=True)
    
    # Período para respuesta
    periodo_info = {
        "mes": mes, 
        "anio": anio, 
        "dias_transcurridos": dias_transcurridos, 
        "dias_mes": dias_mes,
        "modo_ventas_dia": solo_ventas_dia
    }
    
    # Si es modo ventas del día, ajustar el período para mostrarlo diferente
    if solo_ventas_dia:
        periodo_info["mes"] = 0
        periodo_info["anio"] = -1
        periodo_info["label"] = "Ventas del Día (sin corte)"
    
    return {
        "periodo": periodo_info,
        "comparativo_con": {"mes_anterior": f"{mes_ant_ini}-{mes_ant_fin}/{anio_mes_ant}", "año_anterior": f"{mes_min}-{mes_max}/{anio-1}"},
        "unidades": resultados_ordenados,
        "totales": totales
    }


__all__ = ['router']
