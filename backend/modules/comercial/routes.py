"""
EDARSA HUB - Comercial Module Routes
====================================
Endpoints del módulo comercial.

FASE 5B DEL REFACTOR MODULAR (Abril 2026):

ESTADO ACTUAL:
- ✅ Adapters (APIs locales MPRO) migrados a adapters.py
- ✅ Helpers del tablero migrados a service.py (Fase 5B-2)
- ✅ Endpoint /comercial/tablero-ejecutivo migrado (Fase 5B-3)
- ✅ Endpoints /comercial/sucursales y /comercial/metas migrados (Fase 5B-4A)
- ✅ Endpoints /comercial/ticket-perfecto y /comercial/ventas-tiempo migrados (Fase 5B-4C)
- ✅ Endpoints /comercial/mesas y /comercial/detalle-movimientos migrados (Fase 5B-4E)
- ✅ Endpoint /comercial/precios-constantes migrado (Fase 5B-4G)
- ✅ Endpoint /comercial/reporte-pax migrado (Fase 5B-4H)
- ✅ Endpoint /comercial/dashboard migrado (Fase 5B-5B) - CIERRE MÓDULO COMERCIAL

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
   - GET /comercial/tablero-ejecutivo (Fase 5B-3)
   - GET /comercial/sucursales/{server_id} (Fase 5B-4A)
   - GET /comercial/metas/{server_id} (Fase 5B-4A)
   - GET /comercial/ticket-perfecto/{server_id} (Fase 5B-4C)
   - GET /comercial/ventas-tiempo/{server_id} (Fase 5B-4C)
   - GET /comercial/mesas/{server_id} (Fase 5B-4E)
   - GET /comercial/detalle-movimientos/{server_id} (Fase 5B-4E)
   - GET /comercial/precios-constantes/{server_id} (Fase 5B-4G)
   - GET /comercial/reporte-pax/{server_id} (Fase 5B-4H)
   - GET /comercial/dashboard/{server_id} (Fase 5B-5B)

ENDPOINTS PENDIENTES (0 en server.py):
- NINGUNO - Módulo Comercial 100% migrado
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Dict, List
import logging
import calendar
from datetime import datetime, timedelta, timezone

from core.db import execute_sql_query
from core.security import (
    get_current_user, 
    user_has_server_access,
    get_user_empresas_permitidas,
    get_servers_for_empresas,
)
from modules.comercial.service import (
    get_kpis_softrestaurant,
    get_kpis_mpro,
    get_kpis_mpro_por_sucursal,
)
from modules.comercial.adapters import (
    sumar_ventas_api_local_a_sucursal,
)
from modules.comercial.repository import (
    get_servers_for_tablero,
    get_server_by_id,
    get_cached_kpis,
    save_kpis_cache,
    get_cached_kpis_by_prefix,
    save_server_connection_status,
    is_server_recently_offline,
    filtrar_unidades_por_visibilidad,
    get_sucursales_visibles_config,
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
    
    # FASE 3: Filtrar por empresas permitidas del usuario (nuevo modelo)
    empresas_permitidas = await get_user_empresas_permitidas(current_user)
    if empresas_permitidas:
        # Traducir empresas a servidores permitidos
        servers_permitidos = await get_servers_for_empresas(empresas_permitidas)
        if servers_permitidos:
            servers = [s for s in servers if s['id'] in servers_permitidos]
            logging.info(f"FASE 3: Filtrado por empresas - {len(servers)} servidores permitidos")
    
    # Fallback legacy: Si no tiene empresas asignadas, usar modelo viejo
    elif current_user.get('role') != 'Administrador':
        allowed = current_user.get('allowed_servers', [])
        if allowed:
            servers = [s for s in servers if s['id'] in allowed]
            logging.info(f"Legacy: Filtrado por allowed_servers - {len(servers)} servidores")
    
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
                
                # FILTRAR por configuración de visibilidad de sucursales
                unidades_mpro = await filtrar_unidades_por_visibilidad(unidades_mpro, server['id'])
                logging.info(f"MPRO {server['name']}: {len(unidades_mpro)} unidades después de filtro de visibilidad")
                
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


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-4A (Abril 2026)
# ============================================================================

@router.get("/comercial/sucursales/{server_id}")
async def obtener_sucursales(
    server_id: str,
    include_hidden: bool = Query(default=False, description="Incluir sucursales ocultas (para admin)"),
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene las sucursales/empresas de un servidor, filtradas por configuración de visibilidad"""
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # FASE 3.1: Validar acceso por empresa primero
    empresas_permitidas = await get_user_empresas_permitidas(current_user)
    if empresas_permitidas:
        servers_permitidos = await get_servers_for_empresas(empresas_permitidas)
        if server_id not in servers_permitidos:
            raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")
    elif not user_has_server_access(current_user, server_id):
        # Fallback legacy
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        if server['system_type'] == 'MPRO':
            # MPRO: Tabla sucursal (relacionada con venta por Sc_Cve_Sucursal)
            query = """
            SELECT Sc_Cve_Sucursal as id, Sc_Descripcion as nombre 
            FROM sucursal 
            WHERE Es_Cve_Estado = 'AC' 
            ORDER BY Sc_Descripcion
            """
        else:
            # SoftRestaurant: No tiene múltiples sucursales, devolver el servidor como única opción
            return {
                "servidor": server['name'],
                "sucursales": [{
                    "id": "all",
                    "nombre": server['name']
                }]
            }
        
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'], query
        ) or []
        
        sucursales = [{"id": r['id'], "nombre": r['nombre']} for r in result]
        
        # FILTRAR por configuración de visibilidad (si no es include_hidden)
        if not include_hidden and server['system_type'] == 'MPRO':
            config = await get_sucursales_visibles_config(server_id)
            if config:  # Solo filtrar si hay configuración
                sucursales = [s for s in sucursales if config.get(s['nombre'], True)]
                logging.info(f"Sucursales filtradas por visibilidad: {len(sucursales)} de {len(result)}")
        
        # Agregar opción "Todas" al inicio
        sucursales.insert(0, {"id": "all", "nombre": "Todas las sucursales"})
        
        return {
            "servidor": server['name'],
            "system_type": server['system_type'],
            "sucursales": sucursales
        }
    except Exception as e:
        logging.error(f"Error obteniendo sucursales: {str(e)}")
        return {
            "servidor": server['name'],
            "sucursales": [{"id": "all", "nombre": server['name']}],
            "error": str(e)
        }


@router.get("/comercial/metas/{server_id}")
async def comercial_metas(
    server_id: str, 
    sucursal: str = Query(default=""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Metas de ventas por producto y vendedor.
    Nota: Las metas se configuran externamente, aquí mostramos ventas reales.
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # FASE 3.1: Validar acceso por empresa
    empresas_permitidas = await get_user_empresas_permitidas(current_user)
    if empresas_permitidas:
        servers_permitidos = await get_servers_for_empresas(empresas_permitidas)
        if server_id not in servers_permitidos:
            raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")
    elif not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        hoy = datetime.now()
        fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        
        if server['system_type'] == 'SoftRestaurant':
            # Ventas por producto (top 10)
            query_productos = f"""
SELECT TOP 10
    p.descripcion as producto,
    SUM(cd.cantidad * cd.precio) as real_ventas
FROM cheqdet cd
INNER JOIN cheques ON cheques.folio = cd.foliodet
INNER JOIN productos p ON p.idproducto = cd.idproducto
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY p.descripcion
ORDER BY SUM(cd.cantidad * cd.precio) DESC
"""
            result_prod = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_productos
            )
            
            metas_producto = []
            for r in (result_prod or []):
                real_ventas = float(r['real_ventas'] or 0)
                # Estimamos meta como 110% del real (sin tabla de metas real)
                meta_estimada = real_ventas * 1.1
                cumplimiento = round((real_ventas / meta_estimada * 100), 0) if meta_estimada > 0 else 0
                metas_producto.append({
                    "producto": r['producto'],
                    "meta": meta_estimada,
                    "real": real_ventas,
                    "cumplimiento": cumplimiento
                })
            
            # Ventas por mesero/vendedor
            query_vendedor = f"""
SELECT TOP 10
    ISNULL(m.nombre, 'Sin asignar') as vendedor,
    SUM(cheques.total) as real_ventas
FROM cheques
LEFT JOIN meseros m ON m.idmesero = cheques.idmesero
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY m.nombre
ORDER BY SUM(cheques.total) DESC
"""
            result_vend = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_vendedor
            )
            
            metas_vendedor = []
            for r in (result_vend or []):
                real_ventas = float(r['real_ventas'] or 0)
                meta_estimada = real_ventas * 1.1
                cumplimiento = round((real_ventas / meta_estimada * 100), 0) if meta_estimada > 0 else 0
                metas_vendedor.append({
                    "vendedor": r['vendedor'],
                    "meta": meta_estimada,
                    "real": real_ventas,
                    "cumplimiento": cumplimiento
                })
            
            return {
                "por_producto": metas_producto,
                "por_vendedor": metas_vendedor
            }
        
        return {"por_producto": [], "por_vendedor": []}
        
    except Exception as e:
        logging.error(f"Error en metas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-4C (Abril 2026)
# ============================================================================

@router.get("/comercial/ticket-perfecto/{server_id}")
async def comercial_ticket_perfecto(
    server_id: str, 
    sucursal: str = Query(default=""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Análisis de ticket perfecto y rentabilidad por producto.
    Solo SoftRestaurant tiene los datos necesarios.
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        hoy = datetime.now()
        fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        
        if server['system_type'] == 'SoftRestaurant':
            # Análisis de categorías en los tickets (entrada, plato fuerte, postre, etc.)
            # Basado en clasificacionventa de productos
            query_categorias = f"""
SELECT 
    COUNT(DISTINCT cheques.folio) as tickets_totales,
    COUNT(DISTINCT CASE WHEN p.clasificacionventa = 1 THEN cheques.folio END) as con_alimentos,
    COUNT(DISTINCT CASE WHEN p.clasificacionventa = 2 THEN cheques.folio END) as con_bebidas
FROM cheques
INNER JOIN cheqdet cd ON cd.foliodet = cheques.folio
INNER JOIN productos p ON p.idproducto = cd.idproducto
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
  AND cheques.total > 0
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_categorias
            )
            
            tickets_totales = int(result[0]['tickets_totales'] or 0) if result else 0
            con_alimentos = int(result[0]['con_alimentos'] or 0) if result else 0
            con_bebidas = int(result[0]['con_bebidas'] or 0) if result else 0
            
            # Tickets "completos" = tienen alimentos Y bebidas
            tickets_completos = min(con_alimentos, con_bebidas)  # Aproximación
            
            ticket_data = {
                "tickets_totales": tickets_totales,
                "tickets_completos": tickets_completos,
                "pct_completos": round((tickets_completos / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
                "con_entrada": con_alimentos,
                "pct_entrada": round((con_alimentos / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
                "con_plato_fuerte": con_alimentos,
                "pct_plato_fuerte": round((con_alimentos / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
                "con_postre": 0,  # Necesita categoría específica
                "pct_postre": 0,
                "con_digestivo": con_bebidas,
                "pct_digestivo": round((con_bebidas / tickets_totales * 100), 0) if tickets_totales > 0 else 0,
                "oportunidad_perdida": 0
            }
            
            # Top productos por rentabilidad
            query_rentabilidad = f"""
SELECT TOP 20
    p.idproducto as codigo,
    p.descripcion as producto,
    SUM(cd.cantidad * cd.precio) as ventas,
    SUM(cd.cantidad * ISNULL(p.costo, 0)) as costo
FROM cheqdet cd
INNER JOIN cheques ON cheques.folio = cd.foliodet
INNER JOIN productos p ON p.idproducto = cd.idproducto
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY p.idproducto, p.descripcion
HAVING SUM(cd.cantidad * cd.precio) > 0
ORDER BY SUM(cd.cantidad * cd.precio) DESC
"""
            result_rent = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_rentabilidad
            )
            
            rentabilidad = []
            for r in (result_rent or []):
                ventas = float(r['ventas'] or 0)
                costo = float(r['costo'] or 0)
                margen = round(((ventas - costo) / ventas * 100), 0) if ventas > 0 else 0
                categoria = 'A' if margen >= 60 else ('B' if margen >= 40 else 'C')
                rentabilidad.append({
                    "codigo": str(r['codigo']),
                    "producto": r['producto'],
                    "ventas": ventas,
                    "costo": costo,
                    "margen": margen,
                    "categoria": categoria
                })
            
            return {
                "ticket": ticket_data,
                "rentabilidad": rentabilidad
            }
        
        # Para MPRO devolvemos estructura vacía
        return {
            "ticket": {"tickets_totales": 0, "tickets_completos": 0, "pct_completos": 0},
            "rentabilidad": []
        }
        
    except Exception as e:
        logging.error(f"Error en ticket perfecto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comercial/ventas-tiempo/{server_id}")
async def comercial_ventas_tiempo(
    server_id: str, 
    sucursal: str = Query(default=""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Ventas por hora y día de la semana.
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        hoy = datetime.now()
        # Última semana
        fecha_ini = (hoy - timedelta(days=7)).strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        
        if server['system_type'] == 'SoftRestaurant':
            # Ventas por hora
            query_hora = f"""
SELECT 
    DATEPART(HOUR, turnos.apertura) as hora,
    SUM(cheques.total) as ventas,
    SUM(cheques.nopersonas) as pax
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY DATEPART(HOUR, turnos.apertura)
ORDER BY SUM(cheques.total) DESC
"""
            result_hora = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_hora
            )
            
            ventas_por_hora = []
            for r in (result_hora or [])[:6]:  # Top 6 horas
                hora_int = int(r['hora'] or 0)
                ventas_por_hora.append({
                    "hora": f"{hora_int:02d}:00",
                    "ventas": float(r['ventas'] or 0),
                    "pax": int(r['pax'] or 0)
                })
            
            # Ventas por día de la semana
            query_dia = f"""
SELECT 
    DATEPART(WEEKDAY, turnos.apertura) as dia_num,
    SUM(cheques.total) as ventas
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
GROUP BY DATEPART(WEEKDAY, turnos.apertura)
ORDER BY DATEPART(WEEKDAY, turnos.apertura)
"""
            result_dia = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_dia
            )
            
            # Mapeo SQL Server DATEPART(WEEKDAY): 1=Domingo, 2=Lunes, ..., 7=Sábado
            # Reordenamos para que sea Lunes a Domingo (2,3,4,5,6,7,1)
            dias_semana = {1: 'Dom', 2: 'Lun', 3: 'Mar', 4: 'Mié', 5: 'Jue', 6: 'Vie', 7: 'Sáb'}
            
            # Crear diccionario con todos los días inicializados en 0
            ventas_dict = {dia: 0 for dia in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']}
            
            for r in (result_dia or []):
                dia_num = int(r['dia_num'] or 1)
                dia_nombre = dias_semana.get(dia_num, 'Otro')
                if dia_nombre in ventas_dict:
                    ventas_dict[dia_nombre] = float(r['ventas'] or 0)
            
            # Convertir a lista ordenada de Lunes a Domingo
            ventas_por_dia = [{"dia": dia, "ventas": ventas_dict[dia]} for dia in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']]
            
            return {
                "por_hora": ventas_por_hora,
                "por_dia": ventas_por_dia
            }
        
        elif server['system_type'] == 'ManagmentPro' or server['system_type'] == 'MPRO':
            # Filtro de sucursal para MPRO - no filtrar si es "default" o nombre del servidor
            sucursal_filter = ""
            nombre_servidor_1 = server.get('name', '').lower()
            sucursal_lower_1 = (sucursal or '').lower()
            skip_filter_1 = (not sucursal or sucursal_lower_1 == 'default' or sucursal_lower_1 == nombre_servidor_1)
            if sucursal and not skip_filter_1:
                sucursal_filter = f"AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            # Ventas por hora para MPRO
            query_hora = f"""
SELECT 
    DATEPART(HOUR, VE.Vn_Fecha) as hora,
    SUM(VE.Vn_Precio_Neto_Importe) as ventas,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND VE.Es_Cve_Estado <> 'CA'
  {sucursal_filter}
GROUP BY DATEPART(HOUR, VE.Vn_Fecha)
ORDER BY SUM(VE.Vn_Precio_Neto_Importe) DESC
"""
            result_hora = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_hora
            )
            
            ventas_por_hora = []
            for r in (result_hora or [])[:6]:  # Top 6 horas
                hora_int = int(r['hora'] or 0)
                ventas_por_hora.append({
                    "hora": f"{hora_int:02d}:00",
                    "ventas": float(r['ventas'] or 0),
                    "pax": int(r['pax'] or 0)
                })
            
            # Ventas por día de la semana para MPRO
            query_dia = f"""
SELECT 
    DATEPART(WEEKDAY, VE.Vn_Fecha) as dia_num,
    SUM(VE.Vn_Precio_Neto_Importe) as ventas
FROM Venta_Encabezado VE
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND VE.Es_Cve_Estado <> 'CA'
  {sucursal_filter}
GROUP BY DATEPART(WEEKDAY, VE.Vn_Fecha)
ORDER BY DATEPART(WEEKDAY, VE.Vn_Fecha)
"""
            result_dia = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_dia
            )
            
            # Mapeo SQL Server DATEPART(WEEKDAY): 1=Domingo, 2=Lunes, ..., 7=Sábado
            # Reordenamos para que sea Lunes a Domingo
            dias_semana = {1: 'Dom', 2: 'Lun', 3: 'Mar', 4: 'Mié', 5: 'Jue', 6: 'Vie', 7: 'Sáb'}
            
            # Crear diccionario con todos los días inicializados en 0
            ventas_dict = {dia: 0 for dia in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']}
            
            for r in (result_dia or []):
                dia_num = int(r['dia_num'] or 1)
                dia_nombre = dias_semana.get(dia_num, 'Otro')
                if dia_nombre in ventas_dict:
                    ventas_dict[dia_nombre] = float(r['ventas'] or 0)
            
            # Convertir a lista ordenada de Lunes a Domingo
            ventas_por_dia = [{"dia": dia, "ventas": ventas_dict[dia]} for dia in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']]
            
            return {
                "por_hora": ventas_por_hora,
                "por_dia": ventas_por_dia
            }
        
        return {"por_hora": [], "por_dia": []}
        
    except Exception as e:
        logging.error(f"Error en ventas tiempo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-4E (Abril 2026)
# ============================================================================

@router.get("/comercial/mesas/{server_id}")
async def comercial_mesas(
    server_id: str, 
    sucursal: str = Query(default=""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Análisis de mesas y comensales.
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        hoy = datetime.now()
        fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        
        if server['system_type'] == 'SoftRestaurant':
            # KPIs generales de mesas - sin usar numcuenta que no existe en todas las instalaciones
            query_unidad = f"""
SELECT 
    COUNT(DISTINCT cheques.folio) as cheques_mes,
    ISNULL(SUM(cheques.nopersonas), 0) as comensales_mes,
    AVG(cheques.total) as ticket_promedio,
    ISNULL(AVG(CAST(cheques.nopersonas as float)), 0) as pax_promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
  AND cheques.total > 0
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_unidad
            )
            
            if result and len(result) > 0:
                row = result[0]
                cheques_mes = int(row['cheques_mes'] or 0)
                comensales_mes = int(row['comensales_mes'] or 0)
                ticket_promedio = float(row['ticket_promedio'] or 0)
                pax_promedio = float(row['pax_promedio'] or 0)
                # Estimamos mesas únicas como cheques / 2 (asumiendo 2 servicios por mesa por día en promedio)
                total_mesas = max(1, cheques_mes // max(1, hoy.day * 2))
            else:
                total_mesas = 0
                cheques_mes = 0
                comensales_mes = 0
                ticket_promedio = 0
                pax_promedio = 0
            
            rotacion_promedio = round(cheques_mes / total_mesas, 1) if total_mesas > 0 else 0
            
            # Obtener número de días del mes hasta hoy
            dias_mes = hoy.day
            vueltas_por_dia = round(cheques_mes / dias_mes, 0) if dias_mes > 0 else 0
            
            unidad_data = {
                "nombre": sucursal or server['name'],
                "total_mesas": total_mesas,
                "capacidad_total": total_mesas * 4,  # Estimado 4 personas por mesa
                "mesas_atendidas_mes": cheques_mes,
                "comensales_mes": comensales_mes,
                "rotacion_promedio": rotacion_promedio,
                "ticket_promedio": round(ticket_promedio, 2),
                "cheque_promedio": round(ticket_promedio * pax_promedio, 2) if pax_promedio > 0 else ticket_promedio,
                "pax_promedio": round(pax_promedio, 1),
                "vueltas_por_dia": vueltas_por_dia,
                "vueltas_por_hora_pico": round(vueltas_por_dia / 4, 0)  # Estimado 4 horas pico
            }
            
            # Rotación por hora - más útil sin numcuenta
            query_rotacion = f"""
SELECT TOP 15
    DATEPART(HOUR, turnos.apertura) as hora,
    COUNT(*) as vueltas,
    ISNULL(AVG(CAST(cheques.nopersonas as float)), 2) as capacidad_promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{fecha_ini} 00:00:00'
  AND turnos.apertura <= '{fecha_fin} 23:59:59'
  AND cheques.cancelado = 0
  AND cheques.total > 0
GROUP BY DATEPART(HOUR, turnos.apertura)
ORDER BY COUNT(*) DESC
"""
            result_rot = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_rotacion
            )
            
            max_vueltas = max([int(r['vueltas'] or 0) for r in result_rot]) if result_rot else 1
            
            rotacion_por_mesa = []
            for r in result_rot:
                vueltas = int(r['vueltas'] or 0)
                ocupacion = round((vueltas / max_vueltas * 100), 0) if max_vueltas > 0 else 0
                hora = int(r['hora'] or 0)
                rotacion_por_mesa.append({
                    "mesa": f"Hora {hora:02d}:00",
                    "capacidad": int(r['capacidad_promedio'] or 2),
                    "vueltas": vueltas,
                    "ocupacion": ocupacion
                })
            
            return {
                "unidad": unidad_data,
                "rotacion": rotacion_por_mesa
            }
        
        elif server['system_type'] == 'ManagmentPro' or server['system_type'] == 'MPRO':
            # Filtro de sucursal para MPRO
            # Filtro de sucursal para MPRO - no filtrar si es "default" o nombre del servidor
            sucursal_filter = ""
            nombre_servidor_2 = server.get('name', '').lower()
            sucursal_lower_2 = (sucursal or '').lower()
            skip_filter_2 = (not sucursal or sucursal_lower_2 == 'default' or sucursal_lower_2 == nombre_servidor_2)
            if sucursal and not skip_filter_2:
                sucursal_filter = f"AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            # KPIs generales de mesas para MPRO
            query_unidad = f"""
SELECT 
    COUNT(DISTINCT VE.Vn_Folio) as cheques_mes,
    ISNULL(SUM(C.Co_Personas), 0) as comensales_mes,
    AVG(VE.Vn_Precio_Neto_Importe) as ticket_promedio,
    ISNULL(AVG(CAST(C.Co_Personas as float)), 0) as pax_promedio
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND VE.Es_Cve_Estado <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {sucursal_filter}
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_unidad
            )
            
            if result and len(result) > 0:
                row = result[0]
                cheques_mes = int(row['cheques_mes'] or 0)
                comensales_mes = int(row['comensales_mes'] or 0)
                ticket_promedio = float(row['ticket_promedio'] or 0)
                pax_promedio = float(row['pax_promedio'] or 0)
                total_mesas = max(1, cheques_mes // max(1, hoy.day * 2))
            else:
                total_mesas = 0
                cheques_mes = 0
                comensales_mes = 0
                ticket_promedio = 0
                pax_promedio = 0
            
            rotacion_promedio = round(cheques_mes / total_mesas, 1) if total_mesas > 0 else 0
            dias_mes = hoy.day
            vueltas_por_dia = round(cheques_mes / dias_mes, 0) if dias_mes > 0 else 0
            
            unidad_data = {
                "nombre": sucursal or server['name'],
                "total_mesas": total_mesas,
                "capacidad_total": total_mesas * 4,
                "mesas_atendidas_mes": cheques_mes,
                "comensales_mes": comensales_mes,
                "rotacion_promedio": rotacion_promedio,
                "ticket_promedio": round(ticket_promedio, 2),
                "cheque_promedio": round(ticket_promedio * pax_promedio, 2) if pax_promedio > 0 else ticket_promedio,
                "pax_promedio": round(pax_promedio, 1),
                "vueltas_por_dia": vueltas_por_dia,
                "vueltas_por_hora_pico": round(vueltas_por_dia / 4, 0)
            }
            
            # Rotación por hora para MPRO
            query_rotacion = f"""
SELECT TOP 15
    DATEPART(HOUR, VE.Vn_Fecha) as hora,
    COUNT(*) as vueltas,
    ISNULL(AVG(CAST(C.Co_Personas as float)), 2) as capacidad_promedio
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND VE.Es_Cve_Estado <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {sucursal_filter}
GROUP BY DATEPART(HOUR, VE.Vn_Fecha)
ORDER BY COUNT(*) DESC
"""
            result_rotacion = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_rotacion
            )
            
            rotacion_por_mesa = []
            for r in (result_rotacion or []):
                hora = int(r['hora'] or 0)
                vueltas = int(r['vueltas'] or 0)
                ocupacion = min(100, round((vueltas / max(1, vueltas_por_dia)) * 100, 1)) if vueltas_por_dia > 0 else 0
                rotacion_por_mesa.append({
                    "mesa": f"Hora {hora:02d}:00",
                    "capacidad": int(r['capacidad_promedio'] or 2),
                    "vueltas": vueltas,
                    "ocupacion": ocupacion
                })
            
            return {
                "unidad": unidad_data,
                "rotacion": rotacion_por_mesa
            }
        
        return {
            "unidad": {"nombre": sucursal, "total_mesas": 0},
            "rotacion": []
        }
        
    except Exception as e:
        logging.error(f"Error en mesas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comercial/detalle-movimientos/{server_id}")
async def comercial_detalle_movimientos(
    server_id: str, 
    sucursal: str = Query(default=""),
    tipo: str = Query(default="ventas"),  # ventas, pax, cheques
    periodo: str = Query(default="mes"),  # dia, semana, mes
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200),
    current_user: Dict = Depends(get_current_user)
):
    """
    Detalle de movimientos para drill-down en KPIs.
    Devuelve cheques/facturas individuales con su detalle.
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        hoy = datetime.now()
        
        # Calcular fechas según período
        if periodo == "dia":
            fecha_ini = hoy.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
        elif periodo == "semana":
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fecha_ini = inicio_semana.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
        else:  # mes
            fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
        
        offset = (page - 1) * limit
        
        if server['system_type'] == 'SoftRestaurant':
            # Formato de fecha para SoftRestaurant (YYYYMMDD)
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # Query para obtener detalle de cheques - Sin columnas opcionales que pueden no existir
            query_detalle = f"""
SELECT 
    cheques.folio,
    turnos.apertura as fecha,
    cheques.total as importe,
    ISNULL(cheques.nopersonas, 0) as pax,
    ISNULL(cheques.descuento, 0) as descuento,
    ISNULL(cheques.propina, 0) as propina,
    'Comedor' as tipo_servicio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini} 00:00:00'
  AND turnos.apertura <= '{f_fin} 23:59:59'
  AND cheques.cancelado = 0
  AND cheques.total > 0
ORDER BY turnos.apertura DESC
OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_detalle
            )
            
            # Query para contar total
            query_total = f"""
SELECT COUNT(*) as total
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini} 00:00:00'
  AND turnos.apertura <= '{f_fin} 23:59:59'
  AND cheques.cancelado = 0
  AND cheques.total > 0
"""
            result_total = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_total
            )
            total = int(result_total[0]['total']) if result_total else 0
            
            movimientos = []
            for row in result or []:
                fecha_val = row.get('fecha')
                fecha_str = fecha_val.strftime('%Y-%m-%d %H:%M') if hasattr(fecha_val, 'strftime') else str(fecha_val) if fecha_val else ''
                movimientos.append({
                    "folio": str(row.get('folio', '')),
                    "fecha": fecha_str,
                    "importe": float(row.get('importe') or 0),
                    "pax": int(row.get('pax') or 0),
                    "descuento": float(row.get('descuento') or 0),
                    "propina": float(row.get('propina') or 0),
                    "tipo_servicio": row.get('tipo_servicio', 'Comedor'),
                    "num_productos": 0
                })
            
            return {
                "movimientos": movimientos,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit,
                "periodo": {"inicio": fecha_ini, "fin": fecha_fin},
                "servidor": server['name']
            }
        
        elif server['system_type'] == 'ManagmentPro' or server['system_type'] == 'MPRO' or server['system_type'] == 'MPRO':
            # Formato de fecha para MPRO (YYYYMMDD)
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            # Filtro de sucursal si viene - no filtrar si es "default" o nombre del servidor
            sucursal_filter = ""
            nombre_servidor = server.get('name', '').lower()
            sucursal_lower = (sucursal or '').lower()
            skip_sucursal_filter = (
                not sucursal or 
                sucursal_lower == 'default' or 
                sucursal_lower == nombre_servidor or
                sucursal_lower == 'managmentpro' or
                sucursal_lower == 'mpro'
            )
            
            if sucursal and not skip_sucursal_filter:
                # Detectar si es un código de sucursal (4 dígitos como "0021") o un nombre
                if len(sucursal) == 4 and sucursal.isdigit():
                    # Es un código de sucursal - buscar por Sc_Cve_Sucursal
                    sucursal_filter = f"AND VE.Sc_Cve_Sucursal = '{sucursal}'"
                else:
                    # Es un nombre - buscar por descripción parcial
                    sucursal_filter = f"AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            logging.info(f"Detalle MPRO: f_ini={f_ini}, f_fin={f_fin}, sucursal={sucursal}, skip_filter={skip_sucursal_filter}, sucursal_filter={sucursal_filter}")
            
            # Query para MPRO - usa Venta_Encabezado con Comanda para PAX
            query_detalle = f"""
SELECT 
    VE.Vn_Folio as folio,
    VE.Vn_Fecha as fecha,
    VE.Vn_Precio_Neto_Importe as importe,
    ISNULL(C.Co_Personas, 0) as pax,
    'Comedor' as tipo_servicio
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{f_ini}'
  AND VE.Vn_Fecha <= '{f_fin} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {sucursal_filter}
ORDER BY VE.Vn_Fecha DESC
OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
"""
            logging.info(f"Query MPRO detalle: {query_detalle[:200]}...")
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_detalle
            )
            
            # Query para contar total
            query_total = f"""
SELECT COUNT(*) as total
FROM Venta_Encabezado VE
LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{f_ini}'
  AND VE.Vn_Fecha <= '{f_fin} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  AND VE.Vn_Precio_Neto_Importe > 0
  {sucursal_filter}
"""
            result_total = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_total
            )
            total = int(result_total[0]['total']) if result_total else 0
            
            movimientos = []
            for row in result or []:
                fecha_val = row.get('fecha')
                fecha_str = fecha_val.strftime('%Y-%m-%dT%H:%M:%S') if hasattr(fecha_val, 'strftime') else str(fecha_val) if fecha_val else ''
                movimientos.append({
                    "folio": str(row.get('folio', '')),
                    "fecha": fecha_str,
                    "importe": float(row.get('importe') or 0),
                    "pax": int(row.get('pax') or 0),
                    "descuento": 0,
                    "propina": 0,
                    "tipo_servicio": row.get('tipo_servicio', 'Comedor'),
                    "num_productos": 0
                })
            
            return {
                "movimientos": movimientos,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if total > 0 else 0,
                "periodo": {"inicio": fecha_ini, "fin": fecha_fin},
                "servidor": server['name']
            }
        
        return {"movimientos": [], "total": 0, "page": 1, "limit": limit, "pages": 0}
        
    except Exception as e:
        logging.error(f"Error en detalle movimientos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-4G (Abril 2026)
# ============================================================================

@router.get("/comercial/precios-constantes/{server_id}")
async def ventas_precios_constantes(
    server_id: str,
    periodo_actual: str = Query(..., description="Período actual: YYYY-MM o YYYY-MM,YYYY-MM"),
    periodo_base: str = Query(..., description="Período base para precios: YYYY-MM o YYYY-MM,YYYY-MM"),
    granularidad: str = Query(default="categoria", description="categoria, familia, producto"),
    sucursal: str = Query(default="all", description="ID de sucursal o 'all' para todas"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Análisis de ventas valuando a precios constantes de un período base.
    Permite comparar ventas eliminando el efecto inflacionario.
    
    - periodo_actual: Mes(es) de ventas a analizar (ej: "2025-03" o "2025-01,2025-02,2025-03")
    - periodo_base: Período de donde tomar los precios de referencia (ej: "2024-03")
    - granularidad: Nivel de detalle (categoria, familia, producto)
    - sucursal: ID de la sucursal a filtrar o 'all' para todas
    
    Productos In/Out:
    - Nuevos (no existían en período base): Usan precio actual
    - Descontinuados (no existen en período actual): Usan último precio conocido
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        # Parsear períodos (pueden ser múltiples meses separados por coma)
        def parse_periodos(periodo_str):
            meses = [m.strip() for m in periodo_str.split(',')]
            fechas = []
            for mes in meses:
                year, month = mes.split('-')
                year, month = int(year), int(month)
                ultimo_dia = calendar.monthrange(year, month)[1]
                fechas.append({
                    'mes': mes,
                    'year': year,
                    'month': month,
                    'fecha_ini': f"{year}-{month:02d}-01",
                    'fecha_fin': f"{year}-{month:02d}-{ultimo_dia:02d}"
                })
            return fechas
        
        periodos_actual = parse_periodos(periodo_actual)
        periodos_base = parse_periodos(periodo_base)
        
        # Fechas consolidadas
        fecha_ini_actual = min(p['fecha_ini'] for p in periodos_actual)
        fecha_fin_actual = max(p['fecha_fin'] for p in periodos_actual)
        fecha_ini_base = min(p['fecha_ini'] for p in periodos_base)
        fecha_fin_base = max(p['fecha_fin'] for p in periodos_base)
        
        logging.info(f"Precios Constantes - Actual: {fecha_ini_actual} a {fecha_fin_actual}, Base: {fecha_ini_base} a {fecha_fin_base}")
        
        if server['system_type'] == 'SoftRestaurant':
            # Formato YYYYMMDD para SoftRestaurant
            f_ini_actual = fecha_ini_actual.replace('-', '')
            f_fin_actual = fecha_fin_actual.replace('-', '')
            f_ini_base = fecha_ini_base.replace('-', '')
            f_fin_base = fecha_fin_base.replace('-', '')
            
            # PASO 1: Obtener VENTAS REALES del período (misma lógica que Dashboard)
            # Esto asegura que los totales coincidan con el Tablero Ejecutivo
            query_ventas_reales = f"""
SELECT SUM(cheques.total) as ventas_reales
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini_actual} 00:00:00'
  AND turnos.apertura <= '{f_fin_actual} 23:59:59'
  AND cheques.cancelado = 0
"""
            result_ventas_reales = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_reales
            )
            ventas_reales_periodo = float(result_ventas_reales[0]['ventas_reales'] or 0) if result_ventas_reales else 0
            
            # Query para ventas del período ACTUAL con precios actuales
            # Agrupa por producto y calcula precio promedio
            # NOTA: En SoftRestaurant la tabla de detalle es 'cheqdet' (no 'chequedetalle')
            query_ventas_actual = f"""
SELECT 
    p.idproducto as producto_id,
    p.descripcion as producto,
    'SoftRestaurant' as categoria,
    'Productos' as familia,
    SUM(cd.cantidad) as cantidad,
    SUM(cd.precio * cd.cantidad) as importe_actual,
    AVG(cd.precio) as precio_promedio_actual
FROM cheqdet cd
INNER JOIN cheques c ON c.folio = cd.foliodet
INNER JOIN turnos t ON t.idturno = c.idturno
INNER JOIN productos p ON p.idproducto = cd.idproducto
WHERE t.apertura >= '{f_ini_actual} 00:00:00'
  AND t.apertura <= '{f_fin_actual} 23:59:59'
  AND c.cancelado = 0
  AND cd.cantidad > 0
GROUP BY p.idproducto, p.descripcion
"""
            
            # Query para precios del período BASE
            query_precios_base = f"""
SELECT 
    p.idproducto as producto_id,
    p.descripcion as producto,
    AVG(cd.precio) as precio_promedio_base
FROM cheqdet cd
INNER JOIN cheques c ON c.folio = cd.foliodet
INNER JOIN turnos t ON t.idturno = c.idturno
INNER JOIN productos p ON p.idproducto = cd.idproducto
WHERE t.apertura >= '{f_ini_base} 00:00:00'
  AND t.apertura <= '{f_fin_base} 23:59:59'
  AND c.cancelado = 0
  AND cd.cantidad > 0
GROUP BY p.idproducto, p.descripcion
"""
            
            # Ejecutar queries
            ventas_actual = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_actual
            ) or []
            
            precios_base = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_precios_base
            ) or []
            
            # Crear diccionario de precios base
            precios_base_dict = {str(p['producto_id']): float(p['precio_promedio_base'] or 0) for p in precios_base}
            
            # PASO 2: Calcular suma de productos para obtener factor de ajuste
            suma_productos_actual = sum(float(v['importe_actual'] or 0) for v in ventas_actual)
            
            # Factor de ajuste: ventas reales / suma de productos
            # Esto distribuye propinas, impuestos, descuentos proporcionalmente
            factor_ajuste = ventas_reales_periodo / suma_productos_actual if suma_productos_actual > 0 else 1
            logging.info(f"SoftRestaurant - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
            
            # Procesar resultados aplicando factor de ajuste
            productos_detalle = []
            total_actual = 0
            total_constante = 0
            
            for venta in ventas_actual:
                producto_id = str(venta['producto_id'])
                cantidad = float(venta['cantidad'] or 0)
                precio_actual = float(venta['precio_promedio_actual'] or 0)
                # Aplicar factor de ajuste al importe para que coincida con ventas reales
                importe_actual = float(venta['importe_actual'] or 0) * factor_ajuste
                
                # Determinar precio a usar para valuación constante
                if producto_id in precios_base_dict:
                    precio_base = precios_base_dict[producto_id]
                    es_nuevo = False
                else:
                    # Producto nuevo - usar precio actual
                    precio_base = precio_actual
                    es_nuevo = True
                
                # El importe constante también debe ajustarse con el factor
                importe_constante = (cantidad * precio_base) * factor_ajuste
                efecto_precio = importe_actual - importe_constante
                variacion_precio_pct = ((precio_actual - precio_base) / precio_base * 100) if precio_base > 0 else 0
                
                productos_detalle.append({
                    'producto_id': producto_id,
                    'producto': venta['producto'],
                    'categoria': venta['categoria'],
                    'familia': venta['familia'],
                    'cantidad': cantidad,
                    'precio_actual': precio_actual,
                    'precio_base': precio_base,
                    'importe_actual': importe_actual,
                    'importe_constante': importe_constante,
                    'efecto_precio': efecto_precio,
                    'variacion_precio_pct': round(variacion_precio_pct, 2),
                    'es_nuevo': es_nuevo,
                    'es_descontinuado': False
                })
                
                total_actual += importe_actual
                total_constante += importe_constante
            
            # Buscar productos descontinuados (estaban en base pero no en actual)
            productos_actuales_ids = {str(v['producto_id']) for v in ventas_actual}
            for producto_id, precio_base in precios_base_dict.items():
                if producto_id not in productos_actuales_ids:
                    # Obtener info del producto descontinuado
                    query_info = f"SELECT TOP 1 descripcion FROM productos WHERE idproducto = {producto_id}"
                    info_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_info
                    )
                    nombre_producto = info_result[0]['descripcion'] if info_result else f'Producto {producto_id}'
                    
                    productos_detalle.append({
                        'producto_id': producto_id,
                        'producto': nombre_producto,
                        'categoria': 'Descontinuado',
                        'familia': '-',
                        'cantidad': 0,
                        'precio_actual': 0,
                        'precio_base': precio_base,
                        'importe_actual': 0,
                        'importe_constante': 0,
                        'efecto_precio': 0,
                        'variacion_precio_pct': 0,
                        'es_nuevo': False,
                        'es_descontinuado': True
                    })
            
            # Agrupar según granularidad
            if granularidad == 'categoria':
                agrupado = {}
                for p in productos_detalle:
                    key = p['categoria']
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                    if p['es_descontinuado']:
                        agrupado[key]['productos_descontinuados'] += 1
                
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            
            elif granularidad == 'familia':
                agrupado = {}
                for p in productos_detalle:
                    key = f"{p['categoria']} > {p['familia']}"
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'categoria': p['categoria'],
                            'familia': p['familia'],
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                    if p['es_descontinuado']:
                        agrupado[key]['productos_descontinuados'] += 1
                
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            
            else:  # producto
                datos_agrupados = sorted(productos_detalle, key=lambda x: x['importe_actual'], reverse=True)
            
            # Calcular métricas resumen
            efecto_precio_total = total_actual - total_constante
            variacion_real = round(((total_constante - total_actual) / total_actual * 100), 2) if total_actual > 0 else 0
            efecto_inflacion_pct = round((efecto_precio_total / total_constante * 100), 2) if total_constante > 0 else 0
            
            return {
                'servidor': server['name'],
                'system_type': server['system_type'],
                'periodo_actual': periodo_actual,
                'periodo_base': periodo_base,
                'granularidad': granularidad,
                'kpis': {
                    'ventas_actuales': round(total_actual, 2),
                    'ventas_constantes': round(total_constante, 2),
                    'efecto_precio': round(efecto_precio_total, 2),
                    'efecto_inflacion_pct': efecto_inflacion_pct,
                    'variacion_real_pct': variacion_real,
                    'productos_analizados': len([p for p in productos_detalle if not p['es_descontinuado']]),
                    'productos_nuevos': len([p for p in productos_detalle if p.get('es_nuevo')]),
                    'productos_descontinuados': len([p for p in productos_detalle if p.get('es_descontinuado')])
                },
                'datos': datos_agrupados,
                'detalle_productos': productos_detalle if granularidad == 'producto' else None
            }
        
        elif server['system_type'] == 'MPRO':
            # Para MPRO - Las ventas están en la tabla 'venta' directamente
            # La sucursal está en la tabla 'sucursal' relacionada por Sc_Cve_Sucursal
            
            # Filtro de sucursal - en MPRO se relaciona venta con sucursal
            filtro_sucursal = f"AND V.Sc_Cve_Sucursal = '{sucursal}'" if sucursal != 'all' else ""
            filtro_sucursal_ve = f"AND VE.Sc_Cve_Sucursal = '{sucursal}'" if sucursal != 'all' else ""
            
            # PASO 1: Obtener VENTAS REALES del período (misma lógica que Dashboard)
            # Esto asegura que los totales coincidan con el Tablero Ejecutivo
            query_ventas_reales_mpro = f"""
SELECT ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas_reales
FROM Venta_Encabezado VE
WHERE VE.Vn_Fecha >= '{fecha_ini_actual}'
  AND VE.Vn_Fecha <= '{fecha_fin_actual} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {filtro_sucursal_ve}
"""
            result_ventas_reales = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_reales_mpro
            )
            ventas_reales_periodo = float(result_ventas_reales[0]['ventas_reales'] or 0) if result_ventas_reales else 0
            
            query_ventas_actual = f"""
SELECT 
    V.Pr_Cve_Producto as producto_id,
    P.Pr_Descripcion as producto,
    ISNULL(S.Sc_Descripcion, 'Sin Sucursal') as categoria,
    'Productos' as familia,
    SUM(V.Vn_Cantidad_Control_1) as cantidad,
    SUM(V.Vn_Precio_Lista * V.Vn_Cantidad_Control_1) as importe_actual,
    AVG(V.Vn_Precio_Lista) as precio_promedio_actual
FROM venta V
INNER JOIN Producto P ON P.Pr_Cve_Producto = V.Pr_Cve_Producto
LEFT JOIN sucursal S ON S.Sc_Cve_Sucursal = V.Sc_Cve_Sucursal
WHERE V.Vn_Fecha >= '{fecha_ini_actual}'
  AND V.Vn_Fecha <= '{fecha_fin_actual} 23:59:59'
  AND ISNULL(V.Es_Cve_Estado, '') <> 'CA'
  AND V.Vn_Cantidad_Control_1 > 0
  {filtro_sucursal}
GROUP BY V.Pr_Cve_Producto, P.Pr_Descripcion, S.Sc_Descripcion
"""
            
            query_precios_base = f"""
SELECT 
    V.Pr_Cve_Producto as producto_id,
    AVG(V.Vn_Precio_Lista) as precio_promedio_base
FROM venta V
WHERE V.Vn_Fecha >= '{fecha_ini_base}'
  AND V.Vn_Fecha <= '{fecha_fin_base} 23:59:59'
  AND ISNULL(V.Es_Cve_Estado, '') <> 'CA'
  AND V.Vn_Cantidad_Control_1 > 0
  {filtro_sucursal}
GROUP BY V.Pr_Cve_Producto
"""
            
            # Ejecutar queries
            ventas_actual = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ventas_actual
            ) or []
            
            precios_base = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_precios_base
            ) or []
            
            # Crear diccionario de precios base
            precios_base_dict = {str(p['producto_id']): float(p['precio_promedio_base'] or 0) for p in precios_base}
            
            # PASO 2: Calcular suma de productos para obtener factor de ajuste
            suma_productos_actual = sum(float(v['importe_actual'] or 0) for v in ventas_actual)
            
            # Factor de ajuste: ventas reales / suma de productos
            factor_ajuste = ventas_reales_periodo / suma_productos_actual if suma_productos_actual > 0 else 1
            logging.info(f"MPRO - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
            
            productos_detalle = []
            total_actual = 0
            total_constante = 0
            
            for venta in ventas_actual:
                producto_id = str(venta['producto_id'])
                cantidad = float(venta['cantidad'] or 0)
                precio_actual = float(venta['precio_promedio_actual'] or 0)
                # Aplicar factor de ajuste al importe para que coincida con ventas reales
                importe_actual = float(venta['importe_actual'] or 0) * factor_ajuste
                
                if producto_id in precios_base_dict:
                    precio_base = precios_base_dict[producto_id]
                    es_nuevo = False
                else:
                    precio_base = precio_actual
                    es_nuevo = True
                
                # El importe constante también debe ajustarse con el factor
                importe_constante = (cantidad * precio_base) * factor_ajuste
                efecto_precio = importe_actual - importe_constante
                variacion_precio_pct = ((precio_actual - precio_base) / precio_base * 100) if precio_base > 0 else 0
                
                productos_detalle.append({
                    'producto_id': producto_id,
                    'producto': venta['producto'],
                    'categoria': venta['categoria'],
                    'familia': venta['familia'],
                    'cantidad': cantidad,
                    'precio_actual': precio_actual,
                    'precio_base': precio_base,
                    'importe_actual': importe_actual,
                    'importe_constante': importe_constante,
                    'efecto_precio': efecto_precio,
                    'variacion_precio_pct': round(variacion_precio_pct, 2),
                    'es_nuevo': es_nuevo,
                    'es_descontinuado': False
                })
                
                total_actual += importe_actual
                total_constante += importe_constante
            
            # Agrupar según granularidad (mismo código)
            if granularidad == 'categoria':
                agrupado = {}
                for p in productos_detalle:
                    key = p['categoria']
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            elif granularidad == 'familia':
                agrupado = {}
                for p in productos_detalle:
                    key = f"{p['categoria']} > {p['familia']}"
                    if key not in agrupado:
                        agrupado[key] = {
                            'nombre': key,
                            'categoria': p['categoria'],
                            'familia': p['familia'],
                            'cantidad': 0,
                            'importe_actual': 0,
                            'importe_constante': 0,
                            'efecto_precio': 0,
                            'productos_nuevos': 0,
                            'productos_descontinuados': 0
                        }
                    agrupado[key]['cantidad'] += p['cantidad']
                    agrupado[key]['importe_actual'] += p['importe_actual']
                    agrupado[key]['importe_constante'] += p['importe_constante']
                    agrupado[key]['efecto_precio'] += p['efecto_precio']
                    if p['es_nuevo']:
                        agrupado[key]['productos_nuevos'] += 1
                datos_agrupados = sorted(agrupado.values(), key=lambda x: x['importe_actual'], reverse=True)
            else:
                datos_agrupados = sorted(productos_detalle, key=lambda x: x['importe_actual'], reverse=True)
            
            efecto_precio_total = total_actual - total_constante
            variacion_real = round(((total_constante - total_actual) / total_actual * 100), 2) if total_actual > 0 else 0
            efecto_inflacion_pct = round((efecto_precio_total / total_constante * 100), 2) if total_constante > 0 else 0
            
            return {
                'servidor': server['name'],
                'system_type': server['system_type'],
                'periodo_actual': periodo_actual,
                'periodo_base': periodo_base,
                'granularidad': granularidad,
                'kpis': {
                    'ventas_actuales': round(total_actual, 2),
                    'ventas_constantes': round(total_constante, 2),
                    'efecto_precio': round(efecto_precio_total, 2),
                    'efecto_inflacion_pct': efecto_inflacion_pct,
                    'variacion_real_pct': variacion_real,
                    'productos_analizados': len([p for p in productos_detalle if not p['es_descontinuado']]),
                    'productos_nuevos': len([p for p in productos_detalle if p.get('es_nuevo')]),
                    'productos_descontinuados': len([p for p in productos_detalle if p.get('es_descontinuado')])
                },
                'datos': datos_agrupados,
                'detalle_productos': productos_detalle if granularidad == 'producto' else None
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Sistema no soportado: {server['system_type']}")
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error en precios constantes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-4H (Abril 2026)
# ============================================================================

@router.get("/comercial/reporte-pax/{server_id}")
async def comercial_reporte_pax(
    server_id: str, 
    sucursal: str = Query(default=""),
    fecha: str = Query(default=""),  # Formato YYYY-MM-DD
    agrupacion: str = Query(default="vendedor"),  # vendedor o ticket
    current_user: Dict = Depends(get_current_user)
):
    """
    Reporte de PAX con drill-down por vendedor o ticket.
    Incluye comparativas vs día/mes/año anterior.
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        # Fecha seleccionada o hoy
        if fecha:
            fecha_sel = datetime.strptime(fecha, '%Y-%m-%d')
        else:
            fecha_sel = datetime.now()
        
        fecha_str = fecha_sel.strftime('%Y-%m-%d')
        
        # Fechas para comparativos
        fecha_dia_ant = (fecha_sel - timedelta(days=1)).strftime('%Y-%m-%d')
        fecha_mes_ant = (fecha_sel.replace(day=1) - timedelta(days=1)).replace(day=min(fecha_sel.day, 28)).strftime('%Y-%m-%d')
        fecha_ano_ant = fecha_sel.replace(year=fecha_sel.year - 1).strftime('%Y-%m-%d')
        
        items = []
        resumen = {"pax_total": 0, "ventas_total": 0, "total_cheques": 0, "pax_promedio": 0, "cheque_promedio": 0}
        comparativo = {"vs_dia_anterior": 0, "vs_mes_anterior": 0, "vs_ano_anterior": 0}
        
        if server['system_type'] == 'SoftRestaurant':
            f_fmt = fecha_str.replace('-', '')
            
            if agrupacion == 'vendedor':
                # Agrupar por vendedor con detalle de cheques
                query = f"""
SELECT 
    ISNULL(emp.nombre, 'Sin Vendedor') as vendedor,
    COUNT(DISTINCT ch.folio) as num_cheques,
    ISNULL(SUM(ch.nopersonas), 0) as pax,
    ISNULL(SUM(ch.total), 0) as total
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
LEFT JOIN empleados emp ON emp.idempleado = ch.idempleado
WHERE t.apertura >= '{f_fmt} 00:00:00'
  AND t.apertura <= '{f_fmt} 23:59:59'
  AND ch.cancelado = 0
  AND ch.total > 0
GROUP BY emp.nombre
ORDER BY SUM(ch.total) DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
                
                for idx, row in enumerate(result or []):
                    vendedor = row.get('vendedor', 'Sin Vendedor')
                    pax = int(row.get('pax') or 0)
                    total = float(row.get('total') or 0)
                    num_cheques = int(row.get('num_cheques') or 0)
                    
                    # Obtener detalle de cheques por vendedor
                    query_detalle = f"""
SELECT 
    ch.folio,
    ISNULL(ch.nopersonas, 0) as pax,
    ch.total
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
LEFT JOIN empleados emp ON emp.idempleado = ch.idempleado
WHERE t.apertura >= '{f_fmt} 00:00:00'
  AND t.apertura <= '{f_fmt} 23:59:59'
  AND ch.cancelado = 0
  AND ch.total > 0
  AND ISNULL(emp.nombre, 'Sin Vendedor') = '{vendedor.replace("'", "''")}'
ORDER BY ch.total DESC
"""
                    detalle_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_detalle
                    )
                    
                    detalle = []
                    for det in detalle_result or []:
                        det_pax = int(det.get('pax') or 0)
                        det_total = float(det.get('total') or 0)
                        detalle.append({
                            "folio": str(det.get('folio', '')),
                            "pax": det_pax,
                            "total": det_total,
                            "pax_promedio": det_total / det_pax if det_pax > 0 else det_total
                        })
                    
                    items.append({
                        "id": f"v_{idx}",
                        "nombre": vendedor,
                        "pax": pax,
                        "total": total,
                        "num_cheques": num_cheques,
                        "pax_promedio": total / pax if pax > 0 else total,
                        "detalle": detalle
                    })
            else:
                # Agrupar por ticket/cheque con detalle de vendedor
                query = f"""
SELECT 
    ch.folio,
    ISNULL(emp.nombre, 'Sin Vendedor') as vendedor,
    ISNULL(ch.nopersonas, 0) as pax,
    ch.total
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
LEFT JOIN empleados emp ON emp.idempleado = ch.idempleado
WHERE t.apertura >= '{f_fmt} 00:00:00'
  AND t.apertura <= '{f_fmt} 23:59:59'
  AND ch.cancelado = 0
  AND ch.total > 0
ORDER BY ch.total DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
                
                for idx, row in enumerate(result or []):
                    pax = int(row.get('pax') or 0)
                    total = float(row.get('total') or 0)
                    items.append({
                        "id": f"t_{idx}",
                        "folio": str(row.get('folio', '')),
                        "nombre": str(row.get('folio', '')),
                        "vendedor": row.get('vendedor', 'Sin Vendedor'),
                        "pax": pax,
                        "total": total,
                        "pax_promedio": total / pax if pax > 0 else total,
                        "detalle": [{
                            "vendedor": row.get('vendedor', 'Sin Vendedor'),
                            "pax": pax,
                            "total": total,
                            "pax_promedio": total / pax if pax > 0 else total
                        }]
                    })
            
            # Calcular totales
            resumen["pax_total"] = sum(i['pax'] for i in items)
            resumen["ventas_total"] = sum(i['total'] for i in items)
            resumen["total_cheques"] = len(items) if agrupacion == 'ticket' else sum(i.get('num_cheques', 1) for i in items)
            resumen["pax_promedio"] = resumen["ventas_total"] / resumen["pax_total"] if resumen["pax_total"] > 0 else 0
            resumen["cheque_promedio"] = resumen["ventas_total"] / resumen["total_cheques"] if resumen["total_cheques"] > 0 else 0
            
            # Comparativos - helper interno
            def get_pax_fecha(f):
                f_q = f.replace('-', '')
                q = f"""
SELECT ISNULL(SUM(ch.nopersonas), 0) as pax, ISNULL(SUM(ch.total), 0) as total
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
WHERE t.apertura >= '{f_q} 00:00:00' AND t.apertura <= '{f_q} 23:59:59'
  AND ch.cancelado = 0 AND ch.total > 0
"""
                r = execute_sql_query(server['host'], server['port'], server['database'], 
                                      server['username'], server['password'], q)
                return int(r[0]['pax'] or 0) if r else 0, float(r[0]['total'] or 0) if r else 0
            
            pax_ant, total_ant = get_pax_fecha(fecha_dia_ant)
            pax_mes, total_mes = get_pax_fecha(fecha_mes_ant)
            pax_ano, total_ano = get_pax_fecha(fecha_ano_ant)
            
            pax_prom_actual = resumen["pax_promedio"]
            pax_prom_ant = total_ant / pax_ant if pax_ant > 0 else 0
            pax_prom_mes = total_mes / pax_mes if pax_mes > 0 else 0
            pax_prom_ano = total_ano / pax_ano if pax_ano > 0 else 0
            
            comparativo["vs_dia_anterior"] = ((pax_prom_actual - pax_prom_ant) / pax_prom_ant * 100) if pax_prom_ant > 0 else 0
            comparativo["vs_mes_anterior"] = ((pax_prom_actual - pax_prom_mes) / pax_prom_mes * 100) if pax_prom_mes > 0 else 0
            comparativo["vs_ano_anterior"] = ((pax_prom_actual - pax_prom_ano) / pax_prom_ano * 100) if pax_prom_ano > 0 else 0
        
        elif server['system_type'] == 'ManagmentPro' or server['system_type'] == 'MPRO':
            # Implementación para MPRO
            if agrupacion == 'vendedor':
                query = f"""
SELECT 
    ISNULL(E.Em_Nombre, 'Sin Vendedor') as vendedor,
    COUNT(DISTINCT V.Vn_Folio) as num_cheques,
    ISNULL(SUM(C.Co_Personas), 0) as pax,
    SUM(V.Vn_Precio_Neto_Importe) as total
FROM Venta_Encabezado V
LEFT JOIN Comanda C ON C.Co_Folio = V.Vn_Folio
LEFT JOIN Empleado E ON E.Em_Cve = V.Em_Cve_Mesero
WHERE V.Vn_Fecha = '{fecha_str}'
  AND V.Vn_Cancelacion = 0
  AND V.Vn_Precio_Neto_Importe > 0
GROUP BY E.Em_Nombre
ORDER BY SUM(V.Vn_Precio_Neto_Importe) DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
                
                for idx, row in enumerate(result or []):
                    vendedor = row.get('vendedor', 'Sin Vendedor')
                    pax = int(row.get('pax') or 0)
                    total = float(row.get('total') or 0)
                    num_cheques = int(row.get('num_cheques') or 0)
                    
                    # Detalle por vendedor
                    query_det = f"""
SELECT V.Vn_Folio as folio, ISNULL(C.Co_Personas, 0) as pax, V.Vn_Precio_Neto_Importe as total
FROM Venta_Encabezado V
LEFT JOIN Comanda C ON C.Co_Folio = V.Vn_Folio
LEFT JOIN Empleado E ON E.Em_Cve = V.Em_Cve_Mesero
WHERE V.Vn_Fecha = '{fecha_str}' AND V.Vn_Cancelacion = 0 AND V.Vn_Precio_Neto_Importe > 0
  AND ISNULL(E.Em_Nombre, 'Sin Vendedor') = '{vendedor.replace("'", "''")}'
ORDER BY V.Vn_Precio_Neto_Importe DESC
"""
                    det_result = execute_sql_query(
                        server['host'], server['port'], server['database'],
                        server['username'], server['password'], query_det
                    )
                    
                    detalle = []
                    for det in det_result or []:
                        det_pax = int(det.get('pax') or 0)
                        det_total = float(det.get('total') or 0)
                        detalle.append({
                            "folio": str(det.get('folio', '')),
                            "pax": det_pax,
                            "total": det_total,
                            "pax_promedio": det_total / det_pax if det_pax > 0 else det_total
                        })
                    
                    items.append({
                        "id": f"v_{idx}",
                        "nombre": vendedor,
                        "pax": pax,
                        "total": total,
                        "num_cheques": num_cheques,
                        "pax_promedio": total / pax if pax > 0 else total,
                        "detalle": detalle
                    })
            else:
                # Por ticket
                query = f"""
SELECT 
    V.Vn_Folio as folio,
    ISNULL(E.Em_Nombre, 'Sin Vendedor') as vendedor,
    ISNULL(C.Co_Personas, 0) as pax,
    V.Vn_Precio_Neto_Importe as total
FROM Venta_Encabezado V
LEFT JOIN Comanda C ON C.Co_Folio = V.Vn_Folio
LEFT JOIN Empleado E ON E.Em_Cve = V.Em_Cve_Mesero
WHERE V.Vn_Fecha = '{fecha_str}'
  AND V.Vn_Cancelacion = 0
  AND V.Vn_Precio_Neto_Importe > 0
ORDER BY V.Vn_Precio_Neto_Importe DESC
"""
                result = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query
                )
                
                for idx, row in enumerate(result or []):
                    pax = int(row.get('pax') or 0)
                    total = float(row.get('total') or 0)
                    items.append({
                        "id": f"t_{idx}",
                        "folio": str(row.get('folio', '')),
                        "nombre": str(row.get('folio', '')),
                        "vendedor": row.get('vendedor', 'Sin Vendedor'),
                        "pax": pax,
                        "total": total,
                        "pax_promedio": total / pax if pax > 0 else total,
                        "detalle": [{
                            "vendedor": row.get('vendedor', 'Sin Vendedor'),
                            "pax": pax,
                            "total": total,
                            "pax_promedio": total / pax if pax > 0 else total
                        }]
                    })
            
            # Calcular resumen
            resumen["pax_total"] = sum(i['pax'] for i in items)
            resumen["ventas_total"] = sum(i['total'] for i in items)
            resumen["total_cheques"] = len(items) if agrupacion == 'ticket' else sum(i.get('num_cheques', 1) for i in items)
            resumen["pax_promedio"] = resumen["ventas_total"] / resumen["pax_total"] if resumen["pax_total"] > 0 else 0
            resumen["cheque_promedio"] = resumen["ventas_total"] / resumen["total_cheques"] if resumen["total_cheques"] > 0 else 0
            
            # Comparativos para MPRO - helper interno
            def get_pax_mpro(f):
                q = f"""
SELECT ISNULL(SUM(C.Co_Personas), 0) as pax, SUM(V.Vn_Precio_Neto_Importe) as total
FROM Venta_Encabezado V
LEFT JOIN Comanda C ON C.Co_Folio = V.Vn_Folio
WHERE V.Vn_Fecha = '{f}' AND V.Vn_Cancelacion = 0 AND V.Vn_Precio_Neto_Importe > 0
"""
                r = execute_sql_query(server['host'], server['port'], server['database'],
                                      server['username'], server['password'], q)
                return int(r[0]['pax'] or 0) if r else 0, float(r[0]['total'] or 0) if r else 0
            
            pax_ant, total_ant = get_pax_mpro(fecha_dia_ant)
            pax_mes, total_mes = get_pax_mpro(fecha_mes_ant)
            pax_ano, total_ano = get_pax_mpro(fecha_ano_ant)
            
            pax_prom_actual = resumen["pax_promedio"]
            pax_prom_ant = total_ant / pax_ant if pax_ant > 0 else 0
            pax_prom_mes = total_mes / pax_mes if pax_mes > 0 else 0
            pax_prom_ano = total_ano / pax_ano if pax_ano > 0 else 0
            
            comparativo["vs_dia_anterior"] = ((pax_prom_actual - pax_prom_ant) / pax_prom_ant * 100) if pax_prom_ant > 0 else 0
            comparativo["vs_mes_anterior"] = ((pax_prom_actual - pax_prom_mes) / pax_prom_mes * 100) if pax_prom_mes > 0 else 0
            comparativo["vs_ano_anterior"] = ((pax_prom_actual - pax_prom_ano) / pax_prom_ano * 100) if pax_prom_ano > 0 else 0
        
        return {
            "items": items,
            "resumen": resumen,
            "comparativo": comparativo,
            "fecha": fecha_str,
            "servidor": server['name']
        }
        
    except Exception as e:
        logging.error(f"Error en reporte PAX: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-5B (Abril 2026)
# ============================================================================

@router.get("/comercial/dashboard/{server_id}")
async def comercial_dashboard(
    server_id: str, 
    sucursal: str = Query(default=""), 
    periodo: str = Query(default="dia"),  # dia, semana, mes
    meses: str = Query(default=""),  # "01,02,03" - Lista de meses separados por coma
    anio: str = Query(default=""),  # "2025" - Año específico (compatibilidad)
    anios: str = Query(default=""),  # "2025,2024" - Múltiples años separados por coma
    tipo_comparacion: str = Query(default="dias_equiv"),  # dias_equiv o mes_completo
    current_user: Dict = Depends(get_current_user)
):
    """
    Dashboard principal de ventas con KPIs y comparativos.
    Soporta SoftRestaurant y MPRO.
    Ahora soporta multiselección de meses y múltiples años.
    tipo_comparacion: 'dias_equiv' compara días 1-N vs días 1-N del período anterior
                      'mes_completo' compara vs el mes completo anterior
    """
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Verificar permisos
    if not user_has_server_access(current_user, server_id):
        raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
    
    try:
        # Calcular fechas según período
        hoy = datetime.now()
        
        # Obtener lista de años (priorizar 'anios' sobre 'anio')
        if anios:
            lista_anios = [int(a.strip()) for a in anios.split(',') if a.strip()]
        elif anio:
            lista_anios = [int(anio)]
        else:
            lista_anios = [hoy.year]
        
        # Si se proporcionan meses y años específicos, usar esos
        if meses and lista_anios:
            lista_meses = [m.strip() for m in meses.split(',') if m.strip()]
            
            # Usar el año más reciente para la consulta principal
            year = max(lista_anios)
            
            # Para múltiples meses, calcular rango de fechas
            mes_min = min([int(m) for m in lista_meses])
            mes_max = max([int(m) for m in lista_meses])
            
            # Verificar si estamos consultando el mes actual
            es_mes_actual = (year == hoy.year and mes_max == hoy.month)
            
            fecha_ini = f"{year}-{str(mes_min).zfill(2)}-01"
            
            # ============= HOMOLOGACIÓN: Usar fecha_fin = AYER para mes actual (igual que Tablero Ejecutivo) =============
            if es_mes_actual:
                ayer = hoy - timedelta(days=1)
                fecha_fin = ayer.strftime('%Y-%m-%d')
                dia_provisional = ayer.day
                logging.info(f"Dashboard Comercial: Mes actual - usando fecha_fin=AYER ({fecha_fin}) para homologar con Tablero Ejecutivo")
            else:
                if mes_max == 12:
                    ultimo_dia = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    ultimo_dia = datetime(year, mes_max + 1, 1) - timedelta(days=1)
                fecha_fin = ultimo_dia.strftime('%Y-%m-%d')
                dia_provisional = ultimo_dia.day
            
            if tipo_comparacion == "mes_completo" or not es_mes_actual:
                if mes_min == 1:
                    fecha_ini_ant = f"{year - 1}-12-01"
                    fecha_fin_ant = f"{year - 1}-12-31"
                else:
                    mes_ant = mes_min - 1
                    fecha_ini_ant = f"{year}-{str(mes_ant).zfill(2)}-01"
                    if mes_ant == 12:
                        ultimo_dia_ant = datetime(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        ultimo_dia_ant = datetime(year, mes_ant + 1, 1) - timedelta(days=1)
                    fecha_fin_ant = ultimo_dia_ant.strftime('%Y-%m-%d')
                
                fecha_ini_ano_ant = f"{year - 1}-{str(mes_min).zfill(2)}-01"
                if mes_max == 12:
                    ultimo_dia_ano_ant = datetime(year, 1, 1) - timedelta(days=1)
                else:
                    ultimo_dia_ano_ant = datetime(year - 1, mes_max + 1, 1) - timedelta(days=1)
                fecha_fin_ano_ant = ultimo_dia_ano_ant.strftime('%Y-%m-%d')
            else:
                fecha_ini_ant = "PENDIENTE"
                fecha_fin_ant = "PENDIENTE"
                fecha_ini_ano_ant = "PENDIENTE"
                fecha_fin_ano_ant = "PENDIENTE"
            
            logging.info(f"Comercial Dashboard (multiselección): {server['name']} - Meses: {lista_meses} Año: {year} ({fecha_ini} a {fecha_fin}) - Tipo: {tipo_comparacion}")
        elif periodo == "dia":
            fecha_ini = hoy.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
            fecha_ini_ant = (hoy - timedelta(days=1)).strftime('%Y-%m-%d')
            fecha_fin_ant = fecha_ini_ant
            try:
                fecha_ini_ano_ant = hoy.replace(year=hoy.year - 1).strftime('%Y-%m-%d')
                fecha_fin_ano_ant = fecha_ini_ano_ant
            except ValueError:
                fecha_ini_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-28"
                fecha_fin_ano_ant = fecha_ini_ano_ant
        elif periodo == "semana":
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fecha_ini = inicio_semana.strftime('%Y-%m-%d')
            fecha_fin = hoy.strftime('%Y-%m-%d')
            fecha_ini_ant = (inicio_semana - timedelta(days=7)).strftime('%Y-%m-%d')
            fecha_fin_ant = (inicio_semana - timedelta(days=1)).strftime('%Y-%m-%d')
            try:
                fecha_ini_ano_ant = inicio_semana.replace(year=hoy.year - 1).strftime('%Y-%m-%d')
                fecha_fin_ano_ant = hoy.replace(year=hoy.year - 1).strftime('%Y-%m-%d')
            except ValueError:
                fecha_ini_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-01"
                fecha_fin_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-07"
        else:  # mes
            ayer_periodo = hoy - timedelta(days=1)
            fecha_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
            fecha_fin = ayer_periodo.strftime('%Y-%m-%d')
            dia_actual = ayer_periodo.day
            logging.info(f"Dashboard Comercial período 'mes': usando fecha_fin=AYER ({fecha_fin}) para homologar con Tablero Ejecutivo")
            
            primer_dia_mes = hoy.replace(day=1)
            ultimo_dia_mes_ant = primer_dia_mes - timedelta(days=1)
            
            if tipo_comparacion == "dias_equiv":
                fecha_ini_ant = ultimo_dia_mes_ant.replace(day=1).strftime('%Y-%m-%d')
                dia_max_mes_ant = ultimo_dia_mes_ant.day
                dia_comparar = min(dia_actual - 1, dia_max_mes_ant)
                if dia_comparar < 1:
                    dia_comparar = 1
                fecha_fin_ant = ultimo_dia_mes_ant.replace(day=dia_comparar).strftime('%Y-%m-%d')
                
                try:
                    fecha_ini_ano_ant = hoy.replace(year=hoy.year - 1, day=1).strftime('%Y-%m-%d')
                    ano_ant_ultimo_dia = (datetime(hoy.year - 1, hoy.month + 1, 1) - timedelta(days=1)).day if hoy.month < 12 else 31
                    dia_ano_ant = min(dia_actual - 1, ano_ant_ultimo_dia)
                    if dia_ano_ant < 1:
                        dia_ano_ant = 1
                    fecha_fin_ano_ant = hoy.replace(year=hoy.year - 1, day=dia_ano_ant).strftime('%Y-%m-%d')
                except ValueError:
                    fecha_ini_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-01"
                    fecha_fin_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-28"
            else:
                fecha_ini_ant = ultimo_dia_mes_ant.replace(day=1).strftime('%Y-%m-%d')
                fecha_fin_ant = ultimo_dia_mes_ant.strftime('%Y-%m-%d')
                
                try:
                    fecha_ini_ano_ant = hoy.replace(year=hoy.year - 1, day=1).strftime('%Y-%m-%d')
                    if hoy.month == 12:
                        ultimo_dia_ano_ant = datetime(hoy.year, 1, 1) - timedelta(days=1)
                    else:
                        ultimo_dia_ano_ant = datetime(hoy.year - 1, hoy.month + 1, 1) - timedelta(days=1)
                    fecha_fin_ano_ant = ultimo_dia_ano_ant.strftime('%Y-%m-%d')
                except ValueError:
                    fecha_ini_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-01"
                    fecha_fin_ano_ant = f"{hoy.year - 1}-{str(hoy.month).zfill(2)}-28"
        
        logging.info(f"Comercial Dashboard: {server['name']} - Período: {periodo} ({fecha_ini} a {fecha_fin}) - Tipo: {tipo_comparacion}")
        logging.info(f"Comparación mes ant: {fecha_ini_ant} a {fecha_fin_ant}")
        logging.info(f"Comparación año ant: {fecha_ini_ano_ant} a {fecha_fin_ano_ant}")
        
        if server['system_type'] == 'SoftRestaurant':
            f_ini = fecha_ini.replace('-', '')
            f_fin = fecha_fin.replace('-', '')
            
            if tipo_comparacion == "dias_equiv" and fecha_ini_ant == "PENDIENTE":
                query_ultimo_dia = f"""
SELECT MAX(CONVERT(DATE, turnos.apertura)) as ultimo_dia_venta
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini} 00:00:00'
  AND turnos.apertura <= '{f_fin} 23:59:59'
  AND cheques.cancelado = 0
"""
                result_ultimo = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_ultimo_dia
                )
                
                if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
                    ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
                    if isinstance(ultimo_dia_venta, str):
                        dia_con_datos = int(ultimo_dia_venta.split('-')[2]) if '-' in ultimo_dia_venta else int(ultimo_dia_venta[-2:])
                    else:
                        dia_con_datos = ultimo_dia_venta.day
                    
                    logging.info(f"SoftRestaurant - Último día con ventas: {ultimo_dia_venta} (día {dia_con_datos})")
                    
                    f_fin = f"{year}{str(mes_max).zfill(2)}{str(dia_con_datos).zfill(2)}"
                    
                    mes_actual = mes_max
                    anio_actual = year
                    if mes_actual == 1:
                        mes_ant = 12
                        anio_ant = anio_actual - 1
                    else:
                        mes_ant = mes_actual - 1
                        anio_ant = anio_actual
                    
                    if mes_ant == 12:
                        max_dia_mes_ant = 31
                    elif mes_ant in [4, 6, 9, 11]:
                        max_dia_mes_ant = 30
                    elif mes_ant == 2:
                        max_dia_mes_ant = 29 if (anio_ant % 4 == 0 and (anio_ant % 100 != 0 or anio_ant % 400 == 0)) else 28
                    else:
                        max_dia_mes_ant = 31
                    
                    dia_comparar = min(dia_con_datos, max_dia_mes_ant)
                    fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
                    fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
                    
                    anio_pasado = year - 1
                    fecha_ini_ano_ant = f"{anio_pasado}-{str(mes_min).zfill(2)}-01"
                    
                    if mes_max == 2:
                        max_dia_ano_ant = 29 if (anio_pasado % 4 == 0 and (anio_pasado % 100 != 0 or anio_pasado % 400 == 0)) else 28
                    elif mes_max in [4, 6, 9, 11]:
                        max_dia_ano_ant = 30
                    else:
                        max_dia_ano_ant = 31
                    
                    dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
                    fecha_fin_ano_ant = f"{anio_pasado}-{str(mes_max).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
                    
                    logging.info(f"Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_ano_ant} a {fecha_fin_ano_ant} (multiselección: {mes_min}-{mes_max})")
                else:
                    dia_con_datos = 1
                    fecha_ini_ant = fecha_ini.replace(f"-{str(mes_max).zfill(2)}-", f"-{str(mes_max-1).zfill(2)}-") if mes_max > 1 else fecha_ini.replace(f"{year}-01-", f"{year-1}-12-")
                    fecha_fin_ant = fecha_ini_ant
                    fecha_ini_ano_ant = fecha_ini.replace(str(year), str(year-1))
                    fecha_fin_ano_ant = fecha_ini_ano_ant
            
            f_ini_ant = fecha_ini_ant.replace('-', '')
            f_fin_ant = fecha_fin_ant.replace('-', '')
            f_ini_ano_ant = fecha_ini_ano_ant.replace('-', '')
            f_fin_ano_ant = fecha_fin_ano_ant.replace('-', '')
            
            logging.info(f"SoftRestaurant Query - Período: {f_ini} a {f_fin}, Mes ant: {f_ini_ant} a {f_fin_ant}, Año ant: {f_ini_ano_ant} a {f_fin_ano_ant}")
            
            query_kpis = f"""
SELECT 
    COUNT(DISTINCT cheques.folio) as cheques_total,
    SUM(cheques.total) as ventas_periodo,
    AVG(cheques.total) as ticket_promedio,
    ISNULL(SUM(cheques.nopersonas), 0) as pax_total,
    ISNULL(AVG(CAST(cheques.nopersonas as float)), 0) as pax_promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini} 00:00:00'
  AND turnos.apertura <= '{f_fin} 23:59:59'
  AND cheques.cancelado = 0
"""
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_kpis
            )
            
            if result and len(result) > 0:
                row = result[0]
                cheques_total = int(row['cheques_total'] or 0)
                ventas_periodo = float(row['ventas_periodo'] or 0)
                ticket_promedio = float(row['ticket_promedio'] or 0)
                pax_total = int(row['pax_total'] or 0)
                pax_promedio = float(row['pax_promedio'] or 0)
            else:
                cheques_total = 0
                ventas_periodo = 0
                ticket_promedio = 0
                pax_total = 0
                pax_promedio = 0
            
            mesas_atendidas = cheques_total
            rotacion_mesas = round(cheques_total / mesas_atendidas, 2) if mesas_atendidas > 0 else 0
            
            query_anterior = f"""
SELECT SUM(cheques.total) as ventas_periodo
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini_ant} 00:00:00'
  AND turnos.apertura <= '{f_fin_ant} 23:59:59'
  AND cheques.cancelado = 0
"""
            result_ant = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_anterior
            )
            
            ventas_anterior = float(result_ant[0]['ventas_periodo'] or 0) if result_ant and result_ant[0]['ventas_periodo'] else 0
            vs_periodo_anterior = round(((ventas_periodo - ventas_anterior) / ventas_anterior * 100), 1) if ventas_anterior > 0 else 0
            
            query_pax_ant = f"""
SELECT ISNULL(SUM(cheques.nopersonas), 0) as pax_total, SUM(cheques.total) as ventas
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini_ant} 00:00:00'
  AND turnos.apertura <= '{f_fin_ant} 23:59:59'
  AND cheques.cancelado = 0
"""
            result_pax_ant = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_pax_ant
            )
            
            pax_anterior = int(result_pax_ant[0]['pax_total'] or 0) if result_pax_ant else 0
            ventas_pax_ant = float(result_pax_ant[0]['ventas'] or 0) if result_pax_ant else 0
            pax_promedio_anterior = ventas_pax_ant / pax_anterior if pax_anterior > 0 else 0
            pax_promedio_actual = ventas_periodo / pax_total if pax_total > 0 else 0
            vs_pax_mes_anterior = round(((pax_promedio_actual - pax_promedio_anterior) / pax_promedio_anterior * 100), 1) if pax_promedio_anterior > 0 else 0
            
            query_ano_ant = f"""
SELECT 
    SUM(cheques.total) as ventas_periodo,
    ISNULL(SUM(cheques.nopersonas), 0) as pax_total,
    COUNT(DISTINCT cheques.folio) as cheques_total
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= '{f_ini_ano_ant} 00:00:00'
  AND turnos.apertura <= '{f_fin_ano_ant} 23:59:59'
  AND cheques.cancelado = 0
"""
            result_ano_ant = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_ano_ant
            )
            
            ventas_ano_anterior = float(result_ano_ant[0]['ventas_periodo'] or 0) if result_ano_ant and result_ano_ant[0]['ventas_periodo'] else 0
            pax_ano_anterior = int(result_ano_ant[0]['pax_total'] or 0) if result_ano_ant else 0
            cheques_ano_anterior = int(result_ano_ant[0]['cheques_total'] or 0) if result_ano_ant else 0
            
            vs_ano_anterior = round(((ventas_periodo - ventas_ano_anterior) / ventas_ano_anterior * 100), 1) if ventas_ano_anterior > 0 else 0
            pax_vs_ano_anterior = round(((pax_total - pax_ano_anterior) / pax_ano_anterior * 100), 1) if pax_ano_anterior > 0 else 0
            
            pax_total_vs_ano = round(((pax_total - pax_ano_anterior) / pax_ano_anterior * 100), 1) if pax_ano_anterior > 0 else 0
            cheques_total_vs_ano = round(((cheques_total - cheques_ano_anterior) / cheques_ano_anterior * 100), 1) if cheques_ano_anterior > 0 else 0
            ticket_ano_anterior = ventas_ano_anterior / cheques_ano_anterior if cheques_ano_anterior > 0 else 0
            cheque_vs_ano_anterior = round(((ticket_promedio - ticket_ano_anterior) / ticket_ano_anterior * 100), 1) if ticket_ano_anterior > 0 else 0
            rotacion_ano_anterior = pax_ano_anterior / cheques_ano_anterior if cheques_ano_anterior > 0 else 0
            rotacion_vs_ano = round(((rotacion_mesas - rotacion_ano_anterior) / rotacion_ano_anterior * 100), 1) if rotacion_ano_anterior > 0 else 0
            
            # ============= HOMOLOGACIÓN: SUMAR TEMPCHEQUES (igual que Tablero Ejecutivo) =============
            try:
                query_temp = """
SELECT 
    COUNT(DISTINCT folio) as cheques,
    ISNULL(SUM(total), 0) as ventas,
    ISNULL(SUM(nopersonas), 0) as pax
FROM tempcheques
WHERE cancelado = 0
"""
                result_temp = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_temp
                )
                if result_temp and len(result_temp) > 0:
                    ventas_temp = float(result_temp[0]['ventas'] or 0)
                    pax_temp = int(result_temp[0]['pax'] or 0)
                    cheques_temp = int(result_temp[0]['cheques'] or 0)
                    ventas_periodo += ventas_temp
                    pax_total += pax_temp
                    cheques_total += cheques_temp
                    logging.info(f"Dashboard Comercial SoftRestaurant {server['name']} - Tempcheques sumados: ventas=${ventas_temp:,.2f}, pax={pax_temp}, cheques={cheques_temp}")
            except Exception as e:
                logging.warning(f"Dashboard Comercial SoftRestaurant {server['name']} - Error consultando tempcheques: {e}")
            # ============= FIN HOMOLOGACIÓN TEMPCHEQUES =============
            
            ticket_promedio = ventas_periodo / cheques_total if cheques_total > 0 else 0
            mesas_atendidas = cheques_total
            rotacion_mesas = round(cheques_total / mesas_atendidas, 2) if mesas_atendidas > 0 else 0
            
            kpis = {
                "ventas_periodo": ventas_periodo,
                "ticket_promedio": round(ticket_promedio, 2),
                "cheques_total": cheques_total,
                "pax_total": pax_total,
                "pax_promedio": round(pax_promedio, 1),
                "consumo_persona": round(ventas_periodo / pax_total, 2) if pax_total > 0 else 0,
                "mesas_atendidas": mesas_atendidas,
                "rotacion_mesas": rotacion_mesas,
                "venta_por_hora": round(ventas_periodo / 12, 2) if ventas_periodo > 0 else 0
            }
            
            comparativo = {
                "vs_periodo_anterior": vs_periodo_anterior,
                "vs_ano_anterior": vs_ano_anterior,
                "vs_presupuesto": 0,
                "pax_vs_mes_anterior": vs_pax_mes_anterior,
                "pax_vs_ano_anterior": pax_vs_ano_anterior,
                "pax_total_vs_ano": pax_total_vs_ano,
                "cheques_total_vs_ano": cheques_total_vs_ano,
                "cheque_vs_ano_anterior": cheque_vs_ano_anterior,
                "rotacion_vs_ano": rotacion_vs_ano,
                "tipo_comparacion": tipo_comparacion,
                "periodo_anterior": f"{fecha_ini_ant} a {fecha_fin_ant}",
                "periodo_ano_ant": f"{fecha_ini_ano_ant} a {fecha_fin_ano_ant}"
            }
            
            return {
                "kpis": kpis,
                "comparativo": comparativo,
                "alertas": []
            }
        
        elif server['system_type'] == 'MPRO':
            if tipo_comparacion == "dias_equiv" and fecha_ini_ant == "PENDIENTE":
                sucursal_filter_check = f" AND VE.Sc_Cve_Sucursal IN (SELECT Sc_Cve_Sucursal FROM Sucursal WHERE Sc_Descripcion LIKE '%{sucursal}%')" if sucursal else ""
                
                query_ultimo_dia_mpro = f"""
SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
FROM Venta_Encabezado VE
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter_check}
"""
                result_ultimo = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_ultimo_dia_mpro
                )
                
                if result_ultimo and result_ultimo[0]['ultimo_dia_venta']:
                    ultimo_dia_venta = result_ultimo[0]['ultimo_dia_venta']
                    if isinstance(ultimo_dia_venta, str):
                        dia_con_datos = int(ultimo_dia_venta.split('-')[2]) if '-' in ultimo_dia_venta else int(ultimo_dia_venta[-2:])
                    else:
                        dia_con_datos = ultimo_dia_venta.day
                    
                    logging.info(f"MPRO - Último día con ventas: {ultimo_dia_venta} (día {dia_con_datos})")
                    
                    fecha_fin = f"{year}-{str(mes_max).zfill(2)}-{str(dia_con_datos).zfill(2)}"
                    
                    mes_actual = mes_max
                    anio_actual = year
                    if mes_actual == 1:
                        mes_ant = 12
                        anio_ant = anio_actual - 1
                    else:
                        mes_ant = mes_actual - 1
                        anio_ant = anio_actual
                    
                    if mes_ant == 12:
                        max_dia_mes_ant = 31
                    elif mes_ant in [4, 6, 9, 11]:
                        max_dia_mes_ant = 30
                    elif mes_ant == 2:
                        max_dia_mes_ant = 29 if (anio_ant % 4 == 0 and (anio_ant % 100 != 0 or anio_ant % 400 == 0)) else 28
                    else:
                        max_dia_mes_ant = 31
                    
                    dia_comparar = min(dia_con_datos, max_dia_mes_ant)
                    fecha_ini_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-01"
                    fecha_fin_ant = f"{anio_ant}-{str(mes_ant).zfill(2)}-{str(dia_comparar).zfill(2)}"
                    
                    anio_pasado = year - 1
                    fecha_ini_ano_ant = f"{anio_pasado}-{str(mes_min).zfill(2)}-01"
                    
                    if mes_max == 2:
                        max_dia_ano_ant = 29 if (anio_pasado % 4 == 0 and (anio_pasado % 100 != 0 or anio_pasado % 400 == 0)) else 28
                    elif mes_max in [4, 6, 9, 11]:
                        max_dia_ano_ant = 30
                    else:
                        max_dia_ano_ant = 31
                    
                    dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
                    fecha_fin_ano_ant = f"{anio_pasado}-{str(mes_max).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
                    
                    logging.info(f"MPRO Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_ano_ant} a {fecha_fin_ano_ant} (multiselección: {mes_min}-{mes_max})")
            
            sucursal_join = ""
            sucursal_filter = ""
            nombre_servidor = server.get('name', '').lower()
            sucursal_lower = (sucursal or '').lower()
            skip_sucursal_filter = (
                not sucursal or 
                sucursal == 'all' or 
                sucursal_lower == 'default' or 
                sucursal_lower == nombre_servidor
            )
            
            if not skip_sucursal_filter:
                if sucursal.isdigit() or (len(sucursal) == 4 and sucursal[0] == '0'):
                    sucursal_join = ""
                    sucursal_filter = f" AND VE.Sc_Cve_Sucursal = '{sucursal}'"
                else:
                    sucursal_join = "INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal"
                    sucursal_filter = f" AND S.Sc_Descripcion LIKE '%{sucursal}%'"
            
            query_ultimo_dia_suc = f"""
SELECT MAX(CONVERT(DATE, VE.Vn_Fecha)) as ultimo_dia_venta
FROM Venta_Encabezado VE
{sucursal_join}
WHERE VE.Vn_Fecha >= '{fecha_ini}'
  AND VE.Vn_Fecha <= '{fecha_fin} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter}
"""
            try:
                result_ultimo_suc = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_ultimo_dia_suc
                )
                if result_ultimo_suc and result_ultimo_suc[0]['ultimo_dia_venta']:
                    ultimo_dia_suc = result_ultimo_suc[0]['ultimo_dia_venta']
                    if isinstance(ultimo_dia_suc, str):
                        dia_con_datos = int(ultimo_dia_suc.split('-')[2]) if '-' in ultimo_dia_suc else int(ultimo_dia_suc[-2:])
                    else:
                        dia_con_datos = ultimo_dia_suc.day
                    
                    print(f"*** MPRO Dashboard {sucursal} - Ultimo dia con ventas: dia {dia_con_datos} ***")
                    
                    fecha_fin = f"{year}-{str(mes_max).zfill(2)}-{str(dia_con_datos).zfill(2)}"
                    
                    mes_actual = mes_max
                    anio_actual = year
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
                    
                    anio_pasado = year - 1
                    max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_max)[1]
                    dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
                    fecha_ini_ano_ant = f"{anio_pasado}-{str(mes_min).zfill(2)}-01"
                    fecha_fin_ano_ant = f"{anio_pasado}-{str(mes_max).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
                    
                    print(f"*** Fechas ajustadas: Actual hasta {fecha_fin}, MesAnt {fecha_ini_ant} a {fecha_fin_ant}, AnoAnt {fecha_ini_ano_ant} a {fecha_fin_ano_ant} ***")
            except Exception as e:
                print(f"Error detectando ultimo dia para sucursal {sucursal}: {e}")
            
            fi_mpro = fecha_ini.replace('-', '')
            ff_mpro = fecha_fin.replace('-', '')
            
            fia_mpro = fecha_ini_ant.replace('-', '')
            ffa_mpro = fecha_fin_ant.replace('-', '')
            fiaa_mpro = fecha_ini_ano_ant.replace('-', '')
            ffaa_mpro = fecha_fin_ano_ant.replace('-', '')
            
            query_kpis = f"""
SELECT 
    COUNT(DISTINCT VE.Vn_Folio) as cheques_total,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas_periodo,
    ISNULL(SUM(C.Co_Personas), 0) as pax_total
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
{sucursal_join}
WHERE VE.Vn_Fecha >= '{fi_mpro}'
  AND VE.Vn_Fecha <= '{ff_mpro}'
  {sucursal_filter}
"""
            print(f"*** MPRO Query sucursal_filter={sucursal_filter}, fi={fi_mpro}, ff={ff_mpro} ***")
            result = execute_sql_query(
                server['host'], server['port'], server['database'],
                server['username'], server['password'], query_kpis
            )
            
            if result:
                cheques = int(result[0].get('cheques_total') or 0)
                ventas = float(result[0].get('ventas_periodo') or 0)
                pax = int(result[0].get('pax_total') or 0)
                
                # ============= REGLA J.2.5: Fallback para PAX =============
                if pax == 0 and cheques > 0:
                    pax = cheques
                    logging.info(f"Dashboard Comercial MPRO: PAX estimado = {pax} (igual a cheques) para sucursal '{sucursal}'")
                
                # ============= INTEGRACIÓN API LOCAL HOMOLOGADA =============
                sucursal_para_api = sucursal if sucursal else server.get('name', '')
                
                if periodo == "dia":
                    print(f"*** Dashboard Comercial MPRO HOY: Buscando API local para '{sucursal_para_api}' ***")
                    ventas_api_local = sumar_ventas_api_local_a_sucursal(
                        server_host=server['host'],
                        sucursal_nombre=sucursal_para_api,
                        fecha_fin=fecha_fin,
                        mes_solicitado=hoy.month,
                        anio_solicitado=hoy.year,
                        solo_ventas_dia=True
                    )
                    
                    if ventas_api_local.get("aplicado", False):
                        ventas = ventas_api_local["ventas"]
                        cheques = ventas_api_local["cheques"]
                        pax = ventas_api_local["pax"]
                        print(f"*** Dashboard Comercial MPRO HOY: API Local REEMPLAZÓ - ${ventas:,.2f}, {cheques} cheques, {pax} pax ***")
                    elif ventas_api_local.get("reemplazar", False):
                        ventas = ventas_api_local["ventas"]
                        cheques = ventas_api_local["cheques"]
                        pax = ventas_api_local["pax"]
                        print(f"*** Dashboard Comercial MPRO HOY: API Local no funcionó - usando ${ventas:.2f} ***")
                else:
                    print(f"*** Dashboard Comercial MPRO MES: Buscando API local para '{sucursal_para_api}' ***")
                    ventas_api_local = sumar_ventas_api_local_a_sucursal(
                        server_host=server['host'],
                        sucursal_nombre=sucursal_para_api,
                        fecha_fin=fecha_fin,
                        mes_solicitado=hoy.month,
                        anio_solicitado=hoy.year,
                        solo_ventas_dia=False
                    )
                    
                    if ventas_api_local.get("aplicado", False):
                        ventas += ventas_api_local["ventas"]
                        cheques += ventas_api_local["cheques"]
                        pax += ventas_api_local["pax"]
                        print(f"*** Dashboard Comercial MPRO MES: API Local SUMÓ +${ventas_api_local['ventas']:,.2f}, +{ventas_api_local['cheques']} cheques, +{ventas_api_local['pax']} pax ***")
                # ============= FIN INTEGRACIÓN API LOCAL =============
                
                ticket_promedio = ventas / cheques if cheques > 0 else 0
                consumo_persona = ventas / pax if pax > 0 else 0
                pax_promedio = pax / cheques if cheques > 0 else 0
                
                query_pax_ant_mpro = f"""
SELECT 
    ISNULL(SUM(C.Co_Personas), 0) as pax_total,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
{sucursal_join}
WHERE VE.Vn_Fecha >= '{fia_mpro}'
  AND VE.Vn_Fecha <= '{ffa_mpro} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter}
"""
                result_pax_ant = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_pax_ant_mpro
                )
                
                pax_ant = int(result_pax_ant[0]['pax_total'] or 0) if result_pax_ant else 0
                ventas_ant = float(result_pax_ant[0]['ventas'] or 0) if result_pax_ant else 0
                pax_promedio_anterior = ventas_ant / pax_ant if pax_ant > 0 else 0
                pax_promedio_actual = ventas / pax if pax > 0 else 0
                vs_pax_mes_anterior = round(((pax_promedio_actual - pax_promedio_anterior) / pax_promedio_anterior * 100), 1) if pax_promedio_anterior > 0 else 0
                vs_periodo_anterior = round(((ventas - ventas_ant) / ventas_ant * 100), 1) if ventas_ant > 0 else 0
                
                query_ano_ant_mpro = f"""
SELECT 
    ISNULL(SUM(C.Co_Personas), 0) as pax_total,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
    COUNT(DISTINCT VE.Vn_Folio) as cheques_total
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
{sucursal_join}
WHERE VE.Vn_Fecha >= '{fiaa_mpro}'
  AND VE.Vn_Fecha <= '{ffaa_mpro} 23:59:59'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter}
"""
                result_ano_ant = execute_sql_query(
                    server['host'], server['port'], server['database'],
                    server['username'], server['password'], query_ano_ant_mpro
                )
                
                pax_ano_ant = int(result_ano_ant[0]['pax_total'] or 0) if result_ano_ant else 0
                ventas_ano_ant = float(result_ano_ant[0]['ventas'] or 0) if result_ano_ant else 0
                cheques_ano_ant = int(result_ano_ant[0]['cheques_total'] or 0) if result_ano_ant else 0
                vs_ano_anterior = round(((ventas - ventas_ano_ant) / ventas_ano_ant * 100), 1) if ventas_ano_ant > 0 else 0
                pax_vs_ano_anterior = round(((pax - pax_ano_ant) / pax_ano_ant * 100), 1) if pax_ano_ant > 0 else 0
                
                pax_total_vs_ano = round(((pax - pax_ano_ant) / pax_ano_ant * 100), 1) if pax_ano_ant > 0 else 0
                cheques_total_vs_ano = round(((cheques - cheques_ano_ant) / cheques_ano_ant * 100), 1) if cheques_ano_ant > 0 else 0
                ticket_ano_ant = ventas_ano_ant / cheques_ano_ant if cheques_ano_ant > 0 else 0
                cheque_vs_ano_anterior = round(((ticket_promedio - ticket_ano_ant) / ticket_ano_ant * 100), 1) if ticket_ano_ant > 0 else 0
                
                kpis = {
                    "ventas_periodo": round(ventas, 2),
                    "ticket_promedio": round(ticket_promedio, 2),
                    "cheques_total": cheques,
                    "pax_total": pax,
                    "pax_promedio": round(pax_promedio, 2),
                    "consumo_persona": round(consumo_persona, 2),
                    "rotacion_mesas": 0,
                    "mesas_atendidas": 0
                }
                
                comparativo = {
                    "vs_periodo_anterior": vs_periodo_anterior,
                    "vs_ano_anterior": vs_ano_anterior,
                    "vs_presupuesto": 0,
                    "pax_vs_mes_anterior": vs_pax_mes_anterior,
                    "pax_vs_ano_anterior": pax_vs_ano_anterior,
                    "pax_total_vs_ano": pax_total_vs_ano,
                    "cheques_total_vs_ano": cheques_total_vs_ano,
                    "cheque_vs_ano_anterior": cheque_vs_ano_anterior,
                    "rotacion_vs_ano": 0,
                    "tipo_comparacion": tipo_comparacion,
                    "periodo_anterior": f"{fecha_ini_ant} a {fecha_fin_ant}",
                    "periodo_ano_ant": f"{fecha_ini_ano_ant} a {fecha_fin_ano_ant}"
                }
                
                return {
                    "kpis": kpis,
                    "comparativo": comparativo,
                    "alertas": []
                }
        
        return {"kpis": None, "comparativo": None, "alertas": []}
        
    except Exception as e:
        logging.error(f"Error en comercial dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']
