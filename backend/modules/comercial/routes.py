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
   - GET /comercial/tablero-ejecutivo (Fase 5B-3)
   - GET /comercial/sucursales/{server_id} (Fase 5B-4A)
   - GET /comercial/metas/{server_id} (Fase 5B-4A)
   - GET /comercial/ticket-perfecto/{server_id} (Fase 5B-4C)
   - GET /comercial/ventas-tiempo/{server_id} (Fase 5B-4C)
   - GET /comercial/mesas/{server_id} (Fase 5B-4E)
   - GET /comercial/detalle-movimientos/{server_id} (Fase 5B-4E)

ENDPOINTS PENDIENTES (3 total en server.py):
- GET /comercial/dashboard/{server_id} - Dashboard principal (COMPLEJO)
- GET /comercial/reporte-pax/{server_id} - Reporte PAX (más complejo)
- GET /comercial/precios-constantes/{server_id} - Precios constantes
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Dict
import logging
import calendar
from datetime import datetime, timedelta, timezone

from core.db import execute_sql_query
from core.security import get_current_user, user_has_server_access
from modules.comercial.service import (
    get_kpis_softrestaurant,
    get_kpis_mpro,
    get_kpis_mpro_por_sucursal,
)
from modules.comercial.repository import (
    get_servers_for_tablero,
    get_server_by_id,
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


# ============================================================================
# ENDPOINTS MIGRADOS FASE 5B-4A (Abril 2026)
# ============================================================================

@router.get("/comercial/sucursales/{server_id}")
async def obtener_sucursales(
    server_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene las sucursales/empresas de un servidor"""
    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    if not user_has_server_access(current_user, server_id):
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
    
    if not user_has_server_access(current_user, server_id):
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


__all__ = ['router']
