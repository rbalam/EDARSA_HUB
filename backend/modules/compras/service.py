"""
EDARSA HUB - Compras Module Service
===================================
Lógica de negocio para el módulo de compras.

FASE 4 DEL REFACTOR MODULAR (Diciembre 2025):
- Lógica de inventarios físicos, pedidos, facturas
- Funciones de procesamiento de datos

NOTA: La lógica compleja de auditoría operativa y cálculo de pedidos
permanece temporalmente en server.py por su complejidad y dependencias.
Se migrará en fases posteriores.
"""

from typing import Dict, List, Any, Optional
import logging
from fastapi import HTTPException

from modules.compras import repository as repo


# ============================================================================
# INVENTARIOS FÍSICOS
# ============================================================================

async def obtener_inventarios_fisicos(
    server_id: str,
    sucursal: str = None,
    sucursal_id: str = None,
    almacen: str = None
) -> List[Dict]:
    """
    Obtiene la lista de inventarios físicos disponibles.
    Soporta MPRO y SoftRestaurant.
    """
    server = await repo.get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
            # Filtro por almacén
            almacen_filtro = ""
            if almacen and almacen != "TODOS":
                almacen_filtro = f"AND F.Al_Cve_Almacen = '{almacen}'"
            
            result = repo.query_inventarios_fisicos_mpro(server, almacen_filtro, sucursal_id)
            
        elif server['system_type'] == 'SoftRestaurant':
            almacen_filtro = ""
            if almacen and almacen != "TODOS":
                almacen_filtro = f"AND F.idalmacen = {almacen}"
            
            result = repo.query_inventarios_fisicos_sr(server, almacen_filtro)
            
        else:
            return []
        
        return [
            {
                "folio": str(r.get('folio', '')),
                "fecha": r.get('fecha', ''),
                "sucursal_id": str(r.get('sucursal_id', '')),
                "sucursal": r.get('sucursal', ''),
                "almacen_id": str(r.get('almacen_id', '')),
                "almacen": r.get('almacen', ''),
                "productos": int(r.get('productos', 0)),
                "origen": r.get('origen', '')
            }
            for r in result
        ]
        
    except Exception as e:
        logging.error(f"Error obteniendo inventarios físicos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PEDIDOS VIGENTES
# ============================================================================

async def obtener_pedidos_vigentes(server_id: str, sucursal_id: str = None) -> List[Dict]:
    """
    Obtiene pedidos/requisiciones vigentes.
    Soporta MPRO y SoftRestaurant.
    """
    server = await repo.get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
            result = repo.query_pedidos_vigentes_mpro(server, sucursal_id)
        elif server['system_type'] == 'SoftRestaurant':
            result = repo.query_pedidos_vigentes_sr(server)
        else:
            return []
        
        return [
            {
                "folio": str(r.get('folio', '')),
                "fecha": r.get('fecha', ''),
                "sucursal_id": str(r.get('sucursal_id', '')),
                "sucursal": r.get('sucursal', ''),
                "almacen_id": str(r.get('almacen_id', '')),
                "almacen": r.get('almacen', ''),
                "total": float(r.get('total', 0) or 0),
                "estado": r.get('estado', ''),
                "productos": int(r.get('productos', 0)),
                "origen": r.get('origen', '')
            }
            for r in result
        ]
        
    except Exception as e:
        logging.error(f"Error obteniendo pedidos vigentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PARÁMETROS DE COMPRAS
# ============================================================================

async def obtener_parametros(server_id: str, sucursal: str) -> Dict:
    """
    Obtiene los parámetros de compras para un servidor/sucursal.
    Retorna valores por defecto si no existen.
    """
    params = await repo.get_compras_params(server_id, sucursal)
    
    if params:
        return {
            "dias_inventario": params.get("dias_inventario", 10),
            "excluir_domingos": params.get("excluir_domingos", True),
            "dias_inhabiles": params.get("dias_inhabiles", []),
            "dias_transito_proveedor": params.get("dias_transito_proveedor", 2)
        }
    
    # Valores por defecto
    return {
        "dias_inventario": 10,
        "excluir_domingos": True,
        "dias_inhabiles": [],
        "dias_transito_proveedor": 2
    }


async def guardar_parametros(server_id: str, sucursal: str, params: Dict) -> Dict:
    """
    Guarda los parámetros de compras para un servidor/sucursal.
    """
    await repo.save_compras_params(server_id, sucursal, params)
    return {"message": "Parámetros guardados correctamente"}


# ============================================================================
# DETALLE DE FACTURA
# ============================================================================

async def obtener_detalle_factura(server_id: str, folio: str) -> List[Dict]:
    """
    Obtiene el detalle de productos de una factura/entrada.
    """
    server = await repo.get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    try:
        if server['system_type'] == 'MPRO':
            result = repo.query_detalle_factura_mpro(server, folio)
            
            return [
                {
                    "codigo": r['codigo'],
                    "producto": r['producto'],
                    "cantidad": float(r['cantidad'] or 0),
                    "costo": float(r['costo'] or 0),
                    "importe": float(r['importe'] or 0)
                }
                for r in result
            ]
        
        return []
        
    except Exception as e:
        logging.error(f"Error obteniendo detalle factura: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FACTURAS DE PROVEEDOR
# ============================================================================

async def obtener_facturas_proveedor(
    server_id: str,
    sucursal: str = None,
    meses: str = None,
    anio: str = None
) -> List[Dict]:
    """
    Obtiene facturas de proveedores filtradas.
    """
    server = await repo.get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Obtener ID de sucursal
    sucursal_id = None
    if sucursal and server['system_type'] == 'MPRO':
        sucursales = server.get('sucursales', [])
        for s in sucursales:
            if s.get('nombre') == sucursal or s.get('id') == sucursal:
                sucursal_id = s.get('id')
                break
    
    try:
        if server['system_type'] == 'MPRO':
            result = repo.query_facturas_proveedor_mpro(server, sucursal_id, meses, anio)
            
            return [
                {
                    "folio": r['folio'],
                    "fecha": r['fecha'],
                    "proveedor": r['proveedor'],
                    "total": float(r['total'] or 0),
                    "sucursal": r['sucursal'],
                    "productos": int(r['productos'] or 0)
                }
                for r in result
            ]
        
        return []
        
    except Exception as e:
        logging.error(f"Error obteniendo facturas proveedor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = [
    'obtener_inventarios_fisicos',
    'obtener_pedidos_vigentes',
    'obtener_parametros',
    'guardar_parametros',
    'obtener_detalle_factura',
    'obtener_facturas_proveedor',
]
