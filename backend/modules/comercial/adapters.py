"""
EDARSA HUB - Comercial Module Adapters
======================================
Adaptadores para integración con APIs locales MPRO.

FASE 5B DEL REFACTOR MODULAR (Diciembre 2025):
- Lógica de consulta a APIs locales MPRO
- Homologación de ventas del día en tiempo real
- Fallback entre MongoDB y configuración hardcodeada

Funciones migradas desde server.py:
- APIS_MPRO_LOCALES (configuración hardcodeada)
- query_api_mpro_local()
- obtener_ventas_dia_api_local()
- sumar_ventas_api_local_a_sucursal()
"""

import os
import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

# ============================================================================
# CONFIGURACIÓN APIs LOCALES MPRO (HARDCODED - FALLBACK)
# ============================================================================
# Estas APIs obtienen ventas del día en tiempo real desde servidores locales.
# Los datos se replican al servidor en la nube por la noche (hora_replica).
# Solo se consultan si la fecha incluye HOY y estamos ANTES de la hora de réplica.

APIS_MPRO_LOCALES = {
    "130_qro": {
        "nombre": "130° QRO LOCAL",
        "url": os.environ.get("API_MPRO_QRO_URL", "http://54.39.104.176:8001/query"),
        "api_key": os.environ.get("API_MPRO_KEY", "EDARSA_2026_SECURE_KEY"),
        "sucursal_destino": "QUERETARO",
        "servidor_padre_host": "54.39.104.176",
        "hora_replica": 4,
        "activo": True
    },
    "origen": {
        "nombre": "ORIGEN LOCAL",
        "url": os.environ.get("API_MPRO_ORIGEN_URL", "http://54.39.104.176:8000/query"),
        "api_key": os.environ.get("API_MPRO_KEY", "EDARSA_2026_SECURE_KEY"),
        "sucursal_destino": "ORIGEN",
        "servidor_padre_host": "54.39.104.176",
        "hora_replica": 4,
        "activo": True
    }
}


def query_api_mpro_local(api_config: dict, sql_query: str, timeout: int = 3) -> dict:
    """
    Consulta una API MPRO local y retorna los resultados.
    
    Args:
        api_config: Configuración de la API (nombre, url, api_key, etc.)
        sql_query: Query SQL a ejecutar
        timeout: Timeout en segundos (default: 3)
    
    Returns:
        dict con 'success', 'data' o 'error'
    """
    print(f"*** query_api_mpro_local: Iniciando query a {api_config.get('nombre', 'N/A')} ***")
    print(f"*** query_api_mpro_local: URL = {api_config.get('url', 'N/A')} ***")
    print(f"*** query_api_mpro_local: activo = {api_config.get('activo', 'N/A')} ***")
    
    if not api_config.get("activo", False):
        print(f"*** query_api_mpro_local: API desactivada, omitiendo ***")
        return {"success": False, "error": "API desactivada", "data": None}
    
    try:
        headers = {"x-api-key": api_config["api_key"]}
        params = {"sql": sql_query}
        
        print(f"*** query_api_mpro_local: Enviando request... ***")
        response = requests.get(
            api_config["url"],
            headers=headers,
            params=params,
            timeout=timeout
        )
        
        print(f"*** query_api_mpro_local: Response status = {response.status_code} ***")
        
        if response.status_code == 200:
            data = response.json()
            logging.info(f"API Local {api_config['nombre']}: Query exitoso")
            return {"success": True, "data": data, "error": None}
        else:
            logging.warning(f"API Local {api_config['nombre']}: HTTP {response.status_code}")
            print(f"*** query_api_mpro_local: Response body = {response.text[:200]} ***")
            return {"success": False, "error": f"HTTP {response.status_code}", "data": None}
            
    except requests.exceptions.Timeout:
        logging.warning(f"API Local {api_config['nombre']}: Timeout")
        return {"success": False, "error": "Timeout", "data": None}
    except requests.exceptions.ConnectionError:
        logging.warning(f"API Local {api_config['nombre']}: Error de conexión")
        return {"success": False, "error": "Sin conexión", "data": None}
    except Exception as e:
        logging.warning(f"API Local {api_config['nombre']}: Error - {str(e)}")
        return {"success": False, "error": str(e), "data": None}


def obtener_ventas_dia_api_local(api_config: dict, forzar_consulta: bool = False) -> dict:
    """
    Obtiene las ventas del día actual desde una API MPRO local.
    
    Args:
        api_config: Configuración de la API
        forzar_consulta: Si True (modo Ventas del Día), ignora la restricción de hora de réplica
    
    Returns:
        dict con ventas, cheques, pax
    """
    # Usar zona horaria de México (UTC-6) para determinar si ya pasó la hora de réplica
    mexico_tz = timezone(timedelta(hours=-6))
    ahora_mexico = datetime.now(timezone.utc).astimezone(mexico_tz)
    hora_actual = ahora_mexico.hour
    hora_replica = api_config.get("hora_replica", 4)
    
    logging.info(f"API Local {api_config['nombre']}: Hora México = {ahora_mexico.strftime('%H:%M')}, Hora réplica = {hora_replica}:00, forzar={forzar_consulta}")
    
    # Si ya pasó la hora de réplica EN MÉXICO Y no es modo forzado, los datos ya están en la nube
    if hora_actual >= hora_replica and not forzar_consulta:
        logging.info(f"API Local {api_config['nombre']}: Hora actual ({hora_actual}) >= hora réplica ({hora_replica}), omitiendo (datos ya replicados)")
        return {"ventas": 0, "cheques": 0, "pax": 0, "omitido": True, "razon": "post_replica"}
    
    if forzar_consulta:
        logging.info(f"API Local {api_config['nombre']}: FORZANDO consulta (modo Ventas del Día)")
    else:
        logging.info(f"API Local {api_config['nombre']}: Consultando ventas del día (hora {hora_actual} < {hora_replica})")
    
    # Query para obtener ventas del día actual
    sql_ventas_hoy = """
    SELECT 
        ISNULL(SUM(cd_importe), 0) as ventas,
        COUNT(DISTINCT Comanda.co_folio) as cheques,
        (SELECT ISNULL(SUM(co_personas), 0) FROM Comanda WHERE CONVERT(date, co_fecha, 101) = CONVERT(date, GETDATE(), 101)) as pax
    FROM Comanda 
    INNER JOIN Comanda_Detalle ON Comanda.co_folio = Comanda_Detalle.co_folio 
    WHERE CONVERT(date, co_fecha, 101) = CONVERT(date, GETDATE(), 101)
    """
    
    result = query_api_mpro_local(api_config, sql_ventas_hoy)
    
    if result["success"] and result["data"]:
        data = result["data"]
        
        # Manejar diferentes formatos de respuesta
        # Formato 1: {"total_registros":1,"data":[{"ventas":1590.0}]}
        # Formato 2: [{"ventas": 1590.0}]
        # Formato 3: {"ventas": 1590.0}
        
        if isinstance(data, dict) and "data" in data:
            inner_data = data.get("data", [])
            if isinstance(inner_data, list) and len(inner_data) > 0:
                row = inner_data[0]
            else:
                row = {}
        elif isinstance(data, list) and len(data) > 0:
            row = data[0]
        elif isinstance(data, dict):
            row = data
        else:
            row = {}
        
        ventas = float(row.get("ventas", 0) or 0)
        cheques = int(row.get("cheques", 0) or 0)
        pax = int(row.get("pax", 0) or 0)
        
        logging.info(f"API Local {api_config['nombre']}: Ventas HOY = ${ventas:,.2f}, Cheques = {cheques}, PAX = {pax}")
        print(f"*** API Local {api_config['nombre']}: Ventas HOY = ${ventas:,.2f}, Cheques = {cheques}, PAX = {pax} ***")
        return {"ventas": ventas, "cheques": cheques, "pax": pax, "omitido": False}
    else:
        error_msg = result.get('error', 'desconocido')
        logging.warning(f"API Local {api_config['nombre']}: Error obteniendo ventas - {error_msg}")
        print(f"*** API Local {api_config['nombre']}: ERROR - {error_msg} ***")
        return {"ventas": 0, "cheques": 0, "pax": 0, "omitido": True, "razon": "error", "error": error_msg}


def sumar_ventas_api_local_a_sucursal(
    server_host: str, 
    sucursal_nombre: str, 
    fecha_fin: str, 
    mes_solicitado: int = None, 
    anio_solicitado: int = None, 
    solo_ventas_dia: bool = False
) -> dict:
    """
    Busca si hay una API local asociada a esta sucursal y servidor,
    y si el período solicitado incluye HOY, suma las ventas del día.
    
    Cuando solo_ventas_dia=True, las ventas de API local REEMPLAZAN (no suman) las de la nube.
    
    Args:
        server_host: Host del servidor padre (ej: "54.39.104.176")
        sucursal_nombre: Nombre de la sucursal a buscar
        fecha_fin: Fecha fin del período (YYYY-MM-DD)
        mes_solicitado: Mes del período (opcional)
        anio_solicitado: Año del período (opcional)
        solo_ventas_dia: Si True, modo "Ventas del Día" - reemplazar datos nube
    
    Returns:
        dict con ventas_adicionales, cheques_adicionales, pax_adicionales
    """
    # Usar zona horaria de México para determinar "hoy"
    mexico_tz = timezone(timedelta(hours=-6))
    ahora_mexico = datetime.now(timezone.utc).astimezone(mexico_tz)
    hoy = ahora_mexico.strftime("%Y-%m-%d")
    mes_actual = ahora_mexico.month
    anio_actual = ahora_mexico.year
    
    print(f"*** API Local Check: server_host={server_host}, sucursal={sucursal_nombre}, fecha_fin={fecha_fin}, hoy_mexico={hoy}, MODO_VENTAS_DIA={solo_ventas_dia} ***")
    print(f"*** API Local: mes_solicitado={mes_solicitado}, anio_solicitado={anio_solicitado}, mes_actual={mes_actual}, anio_actual={anio_actual} ***")
    
    # Determinar si el período incluye HOY
    periodo_incluye_hoy = False
    
    if fecha_fin >= hoy:
        periodo_incluye_hoy = True
        print(f"*** API Local: fecha_fin >= hoy, período incluye HOY ***")
    elif mes_solicitado and anio_solicitado:
        if mes_solicitado == mes_actual and anio_solicitado == anio_actual:
            periodo_incluye_hoy = True
            print(f"*** API Local: mes/año solicitado = mes/año actual, período incluye HOY ***")
    
    if not periodo_incluye_hoy:
        print(f"*** API Local: período NO incluye hoy, omitiendo ***")
        return {"ventas": 0, "cheques": 0, "pax": 0, "aplicado": False, "reemplazar": False, "razon": "fecha_no_incluye_hoy"}
    
    # ========== BUSCAR APIs LOCALES DESDE MONGODB ==========
    print(f"*** API Local: Buscando APIs tipo 'api_mpro' en MongoDB ***")
    try:
        from pymongo import MongoClient
        sync_client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        sync_db = sync_client[os.environ.get('DB_NAME', 'test_database')]
        apis_locales_db = list(sync_db.servers.find({"tipo": "api_mpro", "active": True}))
        sync_client.close()
        print(f"*** API Local: Encontradas {len(apis_locales_db)} APIs en MongoDB ***")
    except Exception as e:
        print(f"*** API Local: Error buscando en MongoDB: {e} ***")
        apis_locales_db = []
    
    for api_doc in apis_locales_db:
        api_nombre = api_doc.get("name", "Sin nombre")
        api_endpoint = api_doc.get("endpoint", "")
        api_key = api_doc.get("api_key", "")
        sucursal_destino = api_doc.get("sucursal_destino", "").upper()
        servidor_padre_host = api_doc.get("servidor_padre_host", "")
        hora_replica = api_doc.get("hora_replica", 4)
        
        print(f"*** API Local DB: {api_nombre}, endpoint={api_endpoint[:50]}..., sucursal_destino={sucursal_destino} ***")
        
        # Verificar si el servidor padre coincide (si está configurado)
        if servidor_padre_host and servidor_padre_host != server_host:
            print(f"*** API Local: {api_nombre} host {servidor_padre_host} != {server_host}, omitiendo ***")
            continue
        
        # Verificar si la sucursal destino coincide (comparación flexible)
        sucursal_actual = sucursal_nombre.upper()
        
        print(f"*** API Local: Comparando '{sucursal_destino}' con '{sucursal_actual}' ***")
        
        # Matching flexible: "QUERETARO" debe matchear con "130° QUERETARO", "QRO", etc.
        if sucursal_destino and (sucursal_destino in sucursal_actual or sucursal_actual in sucursal_destino):
            print(f"*** API Local MATCH: {api_nombre} -> Sucursal {sucursal_nombre} ***")
            
            api_config = {
                "nombre": api_nombre,
                "url": api_endpoint,
                "api_key": api_key,
                "hora_replica": hora_replica
            }
            
            # En modo Ventas del Día, forzar consulta ignorando hora de réplica
            ventas_api = obtener_ventas_dia_api_local(api_config, forzar_consulta=solo_ventas_dia)
            
            if not ventas_api.get("omitido", True):
                modo = "REEMPLAZANDO" if solo_ventas_dia else "SUMANDO"
                print(f"*** API Local {modo}: +${ventas_api['ventas']:,.2f} de {api_nombre} ***")
                return {
                    "ventas": ventas_api["ventas"],
                    "cheques": ventas_api["cheques"],
                    "pax": ventas_api["pax"],
                    "aplicado": True,
                    "reemplazar": solo_ventas_dia,
                    "api": api_nombre
                }
            else:
                razon = ventas_api.get("razon", "omitido")
                print(f"*** API Local OMITIDO: {razon} ***")
                return {
                    "ventas": 0, "cheques": 0, "pax": 0,
                    "aplicado": False,
                    "reemplazar": solo_ventas_dia,
                    "razon": razon,
                    "api": api_nombre
                }
        else:
            print(f"*** API Local: NO match '{sucursal_destino}' vs '{sucursal_actual}' ***")
    
    # ========== FALLBACK: Buscar en APIS_MPRO_LOCALES (hardcoded) ==========
    print(f"*** API Local: No encontrada en MongoDB, buscando en config hardcodeada ***")
    for api_id, api_config in APIS_MPRO_LOCALES.items():
        if not api_config.get("activo", False):
            print(f"*** API Local: {api_id} desactivada, omitiendo ***")
            continue
            
        # Verificar si el servidor padre coincide
        if api_config.get("servidor_padre_host") != server_host:
            print(f"*** API Local: {api_id} host {api_config.get('servidor_padre_host')} != {server_host}, omitiendo ***")
            continue
        
        # Verificar si la sucursal destino coincide (comparación flexible)
        sucursal_destino = api_config.get("sucursal_destino", "").upper()
        sucursal_actual = sucursal_nombre.upper()
        
        print(f"*** API Local: Comparando '{sucursal_destino}' con '{sucursal_actual}' ***")
        
        # Matching flexible: "QUERETARO" debe matchear con "130 GRADOS QUERETARO", "QRO", etc.
        if sucursal_destino in sucursal_actual or sucursal_actual in sucursal_destino:
            print(f"*** API Local MATCH: {api_config['nombre']} -> Sucursal {sucursal_nombre} ***")
            
            # En modo Ventas del Día, forzar consulta ignorando hora de réplica
            ventas_api = obtener_ventas_dia_api_local(api_config, forzar_consulta=solo_ventas_dia)
            
            if not ventas_api.get("omitido", True):
                modo = "REEMPLAZANDO" if solo_ventas_dia else "SUMANDO"
                print(f"*** API Local {modo}: +${ventas_api['ventas']:,.2f} de {api_config['nombre']} ***")
                return {
                    "ventas": ventas_api["ventas"],
                    "cheques": ventas_api["cheques"],
                    "pax": ventas_api["pax"],
                    "aplicado": True,
                    "reemplazar": solo_ventas_dia,
                    "api": api_config["nombre"]
                }
            else:
                razon = ventas_api.get("razon", "omitido")
                print(f"*** API Local OMITIDO: {razon} ***")
                return {
                    "ventas": 0, "cheques": 0, "pax": 0,
                    "aplicado": False,
                    "reemplazar": solo_ventas_dia,
                    "razon": razon,
                    "api": api_config["nombre"]
                }
        else:
            print(f"*** API Local: NO match '{sucursal_destino}' vs '{sucursal_actual}' ***")
    
    # No se encontró API local para esta sucursal
    return {"ventas": 0, "cheques": 0, "pax": 0, "aplicado": False, "reemplazar": False, "razon": "sin_api_local"}


__all__ = [
    'APIS_MPRO_LOCALES',
    'query_api_mpro_local',
    'obtener_ventas_dia_api_local',
    'sumar_ventas_api_local_a_sucursal',
]
