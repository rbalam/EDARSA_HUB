"""
EDARSA HUB - Comercial Module Repository
========================================
Acceso a datos para el módulo comercial.

FASE 5 DEL REFACTOR MODULAR (Diciembre 2025):
- Queries SQL para ventas por origen (MPRO, SoftRestaurant)
- Acceso a MongoDB para configuración de servidores
- Integración con APIs locales MPRO

NOTA: Las funciones de APIs locales (query_api_mpro_local, obtener_ventas_dia_api_local,
sumar_ventas_api_local_a_sucursal) permanecen en server.py por sus dependencias globales.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from core.db import execute_sql_query


# ============================================================================
# INYECCIÓN DE DEPENDENCIA: MongoDB
# ============================================================================

_db = None


def init_comercial_repository(database) -> None:
    """Inicializa el repositorio con la conexión a MongoDB."""
    global _db
    _db = database


def get_db():
    """Obtiene la conexión a MongoDB inyectada."""
    if _db is None:
        raise RuntimeError("Comercial repository not initialized. Call init_comercial_repository(db) first.")
    return _db


# ============================================================================
# SERVIDORES
# ============================================================================

async def get_server_by_id(server_id: str) -> Optional[Dict]:
    """Obtiene un servidor activo por ID."""
    return await get_db().servers.find_one({"id": server_id, "active": True}, {"_id": 0})


async def get_servers_for_tablero() -> List[Dict]:
    """Obtiene servidores visibles para el tablero ejecutivo."""
    cursor = get_db().servers.find(
        {"active": True, "visible_en_operaciones": {"$ne": False}},
        {"_id": 0}
    )
    return await cursor.to_list(100)


# ============================================================================
# QUERIES SQL - VENTAS MPRO
# ============================================================================

def query_ventas_mpro(server: Dict, mes: int, anio: int, sucursal_id: str = None) -> List[Dict]:
    """
    Obtiene ventas de MPRO para un mes/año específico.
    """
    sucursal_filtro = f"AND Sc_Cve_Sucursal = '{sucursal_id}'" if sucursal_id else ""
    
    query = f"""
    SELECT 
        Sc_Cve_Sucursal as sucursal_id,
        SUM(Cm_Total) as ventas,
        COUNT(DISTINCT Cm_Folio) as cheques,
        SUM(Cm_NumPersonas) as pax
    FROM Comanda
    WHERE MONTH(Cm_Fecha) = {mes}
      AND YEAR(Cm_Fecha) = {anio}
      AND Cm_Estado IN ('C', 'F')
      {sucursal_filtro}
    GROUP BY Sc_Cve_Sucursal
    """
    
    return execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )


def query_ventas_softrestaurant(server: Dict, mes: int, anio: int) -> List[Dict]:
    """
    Obtiene ventas de SoftRestaurant para un mes/año específico.
    Usa la Regla J de homologación: cheques + tempcheques con totalprecuenta > 0.
    """
    query = f"""
    SELECT 
        ISNULL(SUM(totalprecuenta), 0) as ventas,
        ISNULL(SUM(nopersonas), 0) as pax,
        COUNT(*) as cheques
    FROM (
        SELECT totalprecuenta, nopersonas 
        FROM cheques 
        WHERE MONTH(fecha) = {mes} AND YEAR(fecha) = {anio}
          AND totalprecuenta > 0 AND cancelado = 0
        UNION ALL
        SELECT totalprecuenta, nopersonas 
        FROM tempcheques 
        WHERE MONTH(fecha) = {mes} AND YEAR(fecha) = {anio}
          AND totalprecuenta > 0 AND cancelado = 0
    ) AS ventas_unificadas
    """
    
    return execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )


# ============================================================================
# QUERIES SQL - TICKET PERFECTO
# ============================================================================

def query_ticket_perfecto_mpro(server: Dict, mes: int, anio: int, sucursal_id: str = None) -> List[Dict]:
    """
    Obtiene datos de ticket perfecto para MPRO.
    """
    sucursal_filtro = f"AND C.Sc_Cve_Sucursal = '{sucursal_id}'" if sucursal_id else ""
    
    query = f"""
    SELECT 
        C.Cm_Folio as folio,
        C.Cm_Total as total,
        C.Cm_NumPersonas as pax,
        COUNT(D.Cd_Cantidad) as items,
        SUM(CASE WHEN P.Pr_Tipo = 'B' THEN 1 ELSE 0 END) as bebidas,
        SUM(CASE WHEN P.Pr_Tipo = 'A' THEN 1 ELSE 0 END) as alimentos,
        SUM(CASE WHEN P.Pr_Tipo = 'P' THEN 1 ELSE 0 END) as postres
    FROM Comanda C
    INNER JOIN Comanda_Detalle D ON D.Cm_Folio = C.Cm_Folio
    INNER JOIN Producto P ON P.Pr_Cve_Producto = D.Pr_Cve_Producto
    WHERE MONTH(C.Cm_Fecha) = {mes}
      AND YEAR(C.Cm_Fecha) = {anio}
      AND C.Cm_Estado IN ('C', 'F')
      {sucursal_filtro}
    GROUP BY C.Cm_Folio, C.Cm_Total, C.Cm_NumPersonas
    """
    
    return execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )


# ============================================================================
# QUERIES SQL - METAS
# ============================================================================

async def get_metas_sucursal(server_id: str, sucursal: str, mes: int, anio: int) -> Optional[Dict]:
    """
    Obtiene las metas de una sucursal desde MongoDB.
    """
    return await get_db().metas.find_one(
        {"server_id": server_id, "sucursal": sucursal, "mes": mes, "anio": anio},
        {"_id": 0}
    )


async def save_metas_sucursal(server_id: str, sucursal: str, mes: int, anio: int, metas: Dict) -> None:
    """
    Guarda las metas de una sucursal en MongoDB.
    """
    await get_db().metas.update_one(
        {"server_id": server_id, "sucursal": sucursal, "mes": mes, "anio": anio},
        {"$set": {**metas, "server_id": server_id, "sucursal": sucursal, "mes": mes, "anio": anio}},
        upsert=True
    )


__all__ = [
    'init_comercial_repository',
    'get_db',
    'get_server_by_id',
    'get_servers_for_tablero',
    # Ventas
    'query_ventas_mpro',
    'query_ventas_softrestaurant',
    # Ticket perfecto
    'query_ticket_perfecto_mpro',
    # Metas
    'get_metas_sucursal',
    'save_metas_sucursal',
]
