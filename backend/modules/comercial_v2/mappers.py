from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
MAPPERS - Comercial V2
======================

Funciones de mapeo para transformar datos desde SoftRestaurant y MPRO
hacia el formato EDARSAHUB v2.

Incluye:
- Cálculo de HashOrigen para idempotencia
- Mapeo de campos específicos por sistema
- Cálculo de métrica derivada canónica (ticket_promedio)
"""

import hashlib
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List

from .schemas import (
    KPIsDiariosV2,
    VentasDiaAbiertasV2,
    SistemaOrigen,
    FuenteOriginal,
    UnidadNegocioConfig
)


# =============================================================================
# CÁLCULO DE HASH ORIGEN
# =============================================================================

def calcular_hash_origen(
    server_id: str,
    sucursal_id: str,
    fecha: date,
    ventas_total: Decimal,
    tickets_total: int,
    pax_total: int,
    ventas_sin_propina=None
) -> str:
    """
    Calcula un hash SHA256 único para identificar el origen de los datos.
    Permite detectar duplicados y cambios en el sync.
    
    Composición del hash:
    - server_id + sucursal_id + fecha + ventas_total + ventas_sin_propina + tickets + pax + version_semantica
    """
    ventas_hash = ventas_sin_propina if ventas_sin_propina is not None else ventas_total
    data_string = (
        f"{server_id}|{sucursal_id}|{fecha.isoformat()}|"
        f"{ventas_total}|{ventas_hash}|{tickets_total}|{pax_total}|"
        "kpi_visible_sin_propina_v1"
    )
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()[:32]


def calcular_hash_ventas_abiertas(
    server_id: str,
    sucursal_id: str,
    snapshot_timestamp: datetime,
    ventas_abiertas: Decimal
) -> str:
    """
    Hash para snapshot de ventas abiertas.
    Incluye timestamp para diferenciar snapshots del mismo día.
    """
    data_string = f"{server_id}|{sucursal_id}|{snapshot_timestamp.isoformat()}|{ventas_abiertas}"
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()[:32]


# =============================================================================
# MAPEO SOFTRESTAURANT → EDARSAHUB V2
# =============================================================================

def map_softrestaurant_ventas_cerradas(
    row: Dict[str, Any],
    config: UnidadNegocioConfig,
    sync_run_id: str
) -> KPIsDiariosV2:
    """
    Mapea un registro de SoftRestaurant (cheques + turnos) a KPIs Diarios v2.
    
    Campos esperados del query SoftRestaurant:
    - fecha: date
    - ventas_total: Decimal (total de cheques)
    - ventas_sin_propina: Decimal (total - propinas)
    - propinas: Decimal
    - num_cheques: int
    - num_personas: int
    """
    fecha = row.get('fecha')
    if isinstance(fecha, str):
        fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
    
    ventas_total = Decimal(str(row.get('ventas_total', 0) or 0))
    ventas_sin_propina = Decimal(str(row.get('ventas_sin_propina', 0) or 0))
    propinas = Decimal(str(row.get('propinas', 0) or 0))
    tickets = int(row.get('num_cheques', 0) or 0)
    pax = int(row.get('num_personas', 0) or 0)
    
    # Calcular métricas derivadas
    ticket_promedio = ventas_total / tickets if tickets > 0 else Decimal("0")
    pax_promedio = ventas_total / pax if pax > 0 else Decimal("0")
    # Hash para idempotencia
    hash_origen = calcular_hash_origen(
        config.server_id,
        config.sucursal_id,
        fecha,
        ventas_total,
        tickets,
        pax,
        ventas_sin_propina
    )
    
    return KPIsDiariosV2(
        unidad_negocio_pk=config.unidad_negocio_pk,
        unidad_negocio_nombre=config.unidad_negocio_nombre,
        server_id=config.server_id,
        sucursal_id=config.sucursal_id,
        sucursal_nombre=config.sucursal_nombre,
        sistema_origen=SistemaOrigen.SOFTRESTAURANT,
        
        fecha_operacion=fecha,
        anio=fecha.year,
        mes=fecha.month,
        dia=fecha.day,
        
        ventas_total=ventas_total,
        ventas_sin_propina=ventas_sin_propina,
        propinas_total=propinas,
        tickets_total=tickets,
        pax_total=pax,
        ticket_promedio=ticket_promedio,
        pax_promedio=pax_promedio,
        ventas_cerradas=ventas_sin_propina,
        ventas_abiertas=Decimal("0"),
        total_estimado_dia=ventas_sin_propina,
        
        es_venta_abierta=False,
        es_corte_cerrado=True,
        es_demo=False,
        activo=True,
        
        fuente_original=FuenteOriginal.API_LOCAL,
        id_origen=row.get('id_origen'),
        hash_origen=hash_origen,
        sync_run_id=sync_run_id
    )


def map_softrestaurant_ventas_abiertas(
    row: Dict[str, Any],
    config: UnidadNegocioConfig,
    sync_run_id: str,
    ventas_cerradas_dia: Decimal = Decimal("0"),
    tickets_cerrados_dia: int = 0,
    pax_cerrados_dia: int = 0
) -> VentasDiaAbiertasV2:
    """
    Mapea datos de tempcheques (ventas abiertas) a snapshot v2.
    
    Campos esperados del query SoftRestaurant (tempcheques):
    - ventas_abiertas: Decimal
    - tickets_abiertos: int
    - pax_abiertos: int
    """
    now = datetime.utcnow()
    fecha_hoy = now.date()
    
    ventas_abiertas = Decimal(str(row.get('ventas_abiertas', 0) or 0))
    tickets_abiertos = int(row.get('tickets_abiertos', 0) or 0)
    pax_abiertos = int(row.get('pax_abiertos', 0) or 0)
    
    total_estimado = ventas_cerradas_dia + ventas_abiertas
    
    return VentasDiaAbiertasV2(
        unidad_negocio_pk=config.unidad_negocio_pk,
        unidad_negocio_nombre=config.unidad_negocio_nombre,
        server_id=config.server_id,
        sucursal_id=config.sucursal_id,
        sucursal_nombre=config.sucursal_nombre,
        sistema_origen=SistemaOrigen.SOFTRESTAURANT,
        
        snapshot_timestamp=now,
        fecha_operacion=fecha_hoy,
        
        ventas_abiertas=ventas_abiertas,
        tickets_abiertos=tickets_abiertos,
        pax_abiertos=pax_abiertos,
        
        ventas_cerradas_dia=ventas_cerradas_dia,
        tickets_cerrados_dia=tickets_cerrados_dia,
        pax_cerrados_dia=pax_cerrados_dia,
        
        total_estimado_dia=total_estimado,
        
        fuente_original=FuenteOriginal.TEMPCHEQUES,
        sync_run_id=sync_run_id
    )


# =============================================================================
# MAPEO MPRO → EDARSAHUB V2
# =============================================================================

def map_mpro_ventas_cerradas(
    row: Dict[str, Any],
    config: UnidadNegocioConfig,
    sync_run_id: str
) -> KPIsDiariosV2:
    """
    Mapea un registro de MPRO (Venta_Encabezado) a KPIs Diarios v2.
    
    Campos esperados del query MPRO:
    - fecha: date
    - Vn_Precio_Neto_Importe: Decimal (ventas netas)
    - num_folios: int (tickets)
    - total_personas: int (PAX desde Comanda)
    """
    fecha = row.get('fecha')
    if isinstance(fecha, str):
        fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
    
    # MPRO no maneja propinas en la venta directa
    ventas_total = Decimal(str(row.get('Vn_Precio_Neto_Importe', 0) or 0))
    ventas_sin_propina = ventas_total  # MPRO: ventas ya son netas
    propinas = Decimal("0")  # Propinas se manejan aparte en MPRO
    tickets = int(row.get('num_folios', 0) or 0)
    pax = int(row.get('total_personas', 0) or 0)
    
    # Calcular métricas derivadas
    ticket_promedio = ventas_total / tickets if tickets > 0 else Decimal("0")
    pax_promedio = ventas_total / pax if pax > 0 else Decimal("0")
    # Hash para idempotencia
    hash_origen = calcular_hash_origen(
        config.server_id,
        config.sucursal_id,
        fecha,
        ventas_total,
        tickets,
        pax,
        ventas_sin_propina
    )
    
    return KPIsDiariosV2(
        unidad_negocio_pk=config.unidad_negocio_pk,
        unidad_negocio_nombre=config.unidad_negocio_nombre,
        server_id=config.server_id,
        sucursal_id=config.sucursal_id,
        sucursal_nombre=config.sucursal_nombre,
        sistema_origen=SistemaOrigen.MPRO,
        
        fecha_operacion=fecha,
        anio=fecha.year,
        mes=fecha.month,
        dia=fecha.day,
        
        ventas_total=ventas_total,
        ventas_sin_propina=ventas_sin_propina,
        propinas_total=propinas,
        tickets_total=tickets,
        pax_total=pax,
        ticket_promedio=ticket_promedio,
        pax_promedio=pax_promedio,
        ventas_cerradas=ventas_sin_propina,
        ventas_abiertas=Decimal("0"),
        total_estimado_dia=ventas_sin_propina,
        
        es_venta_abierta=False,
        es_corte_cerrado=True,
        es_demo=False,
        activo=True,
        
        fuente_original=FuenteOriginal.API_LOCAL,
        id_origen=row.get('id_origen'),
        hash_origen=hash_origen,
        sync_run_id=sync_run_id
    )


def map_mpro_ventas_abiertas(
    row: Dict[str, Any],
    config: UnidadNegocioConfig,
    sync_run_id: str,
    ventas_cerradas_dia: Decimal = Decimal("0"),
    tickets_cerrados_dia: int = 0,
    pax_cerrados_dia: int = 0
) -> VentasDiaAbiertasV2:
    """
    Mapea datos de API local MPRO (ventas abiertas) a snapshot v2.
    
    Campos esperados:
    - ventas_abiertas: Decimal
    - tickets_abiertos: int
    - pax_abiertos: int
    """
    now = datetime.utcnow()
    fecha_hoy = now.date()
    
    ventas_abiertas = Decimal(str(row.get('ventas_abiertas', 0) or 0))
    tickets_abiertos = int(row.get('tickets_abiertos', 0) or 0)
    pax_abiertos = int(row.get('pax_abiertos', 0) or 0)
    
    total_estimado = ventas_cerradas_dia + ventas_abiertas
    
    return VentasDiaAbiertasV2(
        unidad_negocio_pk=config.unidad_negocio_pk,
        unidad_negocio_nombre=config.unidad_negocio_nombre,
        server_id=config.server_id,
        sucursal_id=config.sucursal_id,
        sucursal_nombre=config.sucursal_nombre,
        sistema_origen=SistemaOrigen.MPRO,
        
        snapshot_timestamp=now,
        fecha_operacion=fecha_hoy,
        
        ventas_abiertas=ventas_abiertas,
        tickets_abiertos=tickets_abiertos,
        pax_abiertos=pax_abiertos,
        
        ventas_cerradas_dia=ventas_cerradas_dia,
        tickets_cerrados_dia=tickets_cerrados_dia,
        pax_cerrados_dia=pax_cerrados_dia,
        
        total_estimado_dia=total_estimado,
        
        fuente_original=FuenteOriginal.API_LOCAL,
        sync_run_id=sync_run_id
    )


# =============================================================================
# UTILIDADES DE MAPEO
# =============================================================================

def safe_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    """Convierte un valor a Decimal de forma segura"""
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Convierte un valor a int de forma segura"""
    if value is None:
        return default
    try:
        return int(value)
    except:
        return default
