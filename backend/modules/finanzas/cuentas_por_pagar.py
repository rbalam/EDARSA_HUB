"""
EDARSA HUB - Cuentas por Pagar (Facturas Pendientes)
=====================================================
Módulo para gestionar facturas pendientes de pago agrupadas por proveedor.

ABRIL 2026: Conectado a SQL Server real (Finanzas_CuentasPorPagar)
- Si hay datos en SQL, usa datos reales
- Si no hay datos, puede usar modo demo (parámetro use_demo=true)

Datos a mostrar:
1. Número de documento / Folio
2. Proveedor
3. Sucursal
4. Fecha de documento
5. Fecha de vencimiento
6. Días vencido
7. Monto original
8. Monto pagado
9. Saldo pendiente
10. Estatus de pago
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from core.security import get_current_user
import random

# Importar función de filtrado de visibilidad
from modules.comercial.repository import get_sucursales_visibles_config

router = APIRouter(prefix="/finanzas/cuentas-por-pagar", tags=["Cuentas por Pagar"])

# ============================================================================
# REPOSITORIO REAL
# ============================================================================

# Variables globales para repositorios
_finanzas_repo = None  # Repositorio EDARSA HUB (legacy)
_mpro_repo = None      # Repositorio MPRO (datos reales CxP)
_softrest_repo = None  # Repositorio SoftRestaurant (CF, Estelar, 130 Mid)

def set_finanzas_repository(repo):
    """Configura el repositorio de finanzas EDARSA HUB (llamado desde server.py)"""
    global _finanzas_repo
    _finanzas_repo = repo

def set_mpro_repository(repo):
    """Configura el repositorio MPRO para CxP reales (llamado desde server.py)"""
    global _mpro_repo
    _mpro_repo = repo

def set_softrestaurant_repository(repo):
    """Configura el repositorio SoftRestaurant para CxP (llamado desde server.py)"""
    global _softrest_repo
    _softrest_repo = repo

async def get_repo():
    """Obtiene el repositorio de finanzas (prefiere SoftRestaurant > MPRO > EDARSA HUB)"""
    # Primero SoftRestaurant (CF, Estelar, 130 Mid)
    if _softrest_repo:
        return _softrest_repo
    # Luego MPRO
    if _mpro_repo:
        return _mpro_repo
    # Fallback a EDARSA HUB
    if _finanzas_repo:
        return _finanzas_repo
    return None

async def get_mpro_repo():
    """Obtiene específicamente el repositorio MPRO"""
    return _mpro_repo

async def get_softrest_repo():
    """Obtiene específicamente el repositorio SoftRestaurant"""
    return _softrest_repo

# ============================================================================
# DATOS DEMO (Solo se usan si SQL no tiene datos o use_demo=true)
# ============================================================================

def generar_facturas_demo():
    """Genera facturas demo para pruebas"""
    proveedores = [
        {"id": 1, "nombre": "SYSCOM S.A. de C.V.", "rfc": "SYS850101AB1"},
        {"id": 2, "nombre": "DISTRIBUIDORA DE ALIMENTOS DEL SURESTE", "rfc": "DAS920315XY2"},
        {"id": 3, "nombre": "CARNES Y EMBUTIDOS LA SUPERIOR", "rfc": "CES880612MN3"},
        {"id": 4, "nombre": "PRODUCTOS LACTEOS DEL BAJIO", "rfc": "PLB950423QR4"},
        {"id": 5, "nombre": "COMERCIALIZADORA DE ABARROTES PENINSULAR", "rfc": "CAP870908ST5"},
        {"id": 6, "nombre": "VERDURAS Y FRUTAS YUCATAN", "rfc": "VFY900115UV6"},
        {"id": 7, "nombre": "MARISCOS DEL GOLFO", "rfc": "MDG860720WX7"},
        {"id": 8, "nombre": "BEBIDAS Y REFRESCOS DEL CARIBE", "rfc": "BRC910302YZ8"},
    ]
    
    sucursales = [
        {"id": 1, "nombre": "130° QUERETARO"},
        {"id": 2, "nombre": "ORIGEN"},
        {"id": 3, "nombre": "130° TULUM"},
        {"id": 4, "nombre": "CIEN FUEGOS"},
        {"id": 5, "nombre": "XCANATUN"},
    ]
    
    facturas = []
    folio_entrada = 1000
    
    for _ in range(75):  # 75 facturas demo
        proveedor = random.choice(proveedores)
        sucursal = random.choice(sucursales)
        
        # Fechas aleatorias en los últimos 90 días
        dias_atras = random.randint(5, 90)
        fecha_entrada = datetime.now() - timedelta(days=dias_atras)
        dias_credito = random.choice([15, 30, 45, 60])
        fecha_vencimiento = fecha_entrada + timedelta(days=dias_credito)
        
        # Calcular días vencida
        hoy = datetime.now()
        dias_vencida = (hoy - fecha_vencimiento).days if hoy > fecha_vencimiento else 0
        
        # Importes
        importe_total = round(random.uniform(1500, 85000), 2)
        pagos_realizados = round(random.uniform(0, importe_total * 0.7), 2) if random.random() > 0.4 else 0
        saldo = round(importe_total - pagos_realizados, 2)
        
        facturas.append({
            "factura_id": len(facturas) + 1,
            "folio_entrada": f"ENT-{folio_entrada}",
            "folio_factura": f"FA-{random.randint(10000, 99999)}",
            "fecha_entrada": fecha_entrada.strftime("%Y-%m-%d"),
            "fecha_vencimiento": fecha_vencimiento.strftime("%Y-%m-%d"),
            "dias_vencida": max(0, dias_vencida),
            "referencia": f"Pedido #{random.randint(100, 999)} - {random.choice(['Mercancía', 'Insumos', 'Servicios', 'Materiales'])}",
            "importe_total": importe_total,
            "pagos_realizados": pagos_realizados,
            "saldo": saldo,
            "decision_pago": random.choice([True, False]) if saldo > 0 else False,
            "importe_a_pagar": saldo if random.random() > 0.3 else round(saldo * random.uniform(0.3, 1), 2),
            "tiene_pdf_factura": random.random() > 0.2,
            "tiene_xml": random.random() > 0.15,
            "tiene_pdf_entrada": random.random() > 0.1,
            "proveedor_id": proveedor["id"],
            "proveedor_nombre": proveedor["nombre"],
            "proveedor_rfc": proveedor["rfc"],
            "sucursal_id": sucursal["id"],
            "sucursal_nombre": sucursal["nombre"],
            "estatus": "Pendiente" if saldo > 0 else "Pagada"
        })
        
        folio_entrada += 1
    
    return facturas

_facturas_db = generar_facturas_demo()

# ============================================================================
# SCHEMAS
# ============================================================================

class ActualizarDecisionPago(BaseModel):
    """Actualizar decisión de pago de una factura"""
    decision_pago: bool
    importe_a_pagar: Optional[float] = None

class ActualizarDecisionPagoMasivo(BaseModel):
    """Actualizar decisión de pago de múltiples facturas"""
    facturas_ids: List[int]
    decision_pago: bool

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("")
async def listar_facturas_pendientes(
    sucursal_id: Optional[str] = None,  # CIENFUEGOS, ESTELAR, 130MID o código MPRO
    proveedor_id: Optional[str] = None,
    tipo_proveedor: Optional[str] = None,  # A=Alimentos, B=Bebidas, X=Otros
    fecha_corte: Optional[str] = None,  # YYYY-MM-DD
    solo_vencidas: bool = False,
    solo_decision_pago: bool = False,
    use_demo: bool = Query(False, description="Usar datos demo en lugar de SQL real"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Listar facturas/cuentas pendientes de pago.
    
    CONECTADO A SOFTRESTAURANT (CF, Estelar, 130 Mid) + MPRO (CENTRAL2020)
    Combina datos de ambas fuentes para mostrar CxP de todas las operaciones.
    Si use_demo=true, usa datos demo para pruebas.
    
    Filtros: sucursal, proveedor, tipo (A/B/X), fecha de corte, solo vencidas.
    Agrupa por TIPO DE PROVEEDOR (A=Alimentos, B=Bebidas, X=Otros).
    """
    if use_demo:
        # Ir directo a modo demo
        pass
    else:
        # Combinar datos de SoftRestaurant + MPRO
        all_facturas = []
        fuentes_activas = []
        
        softrest_repo = await get_softrest_repo()
        mpro_repo = await get_mpro_repo()
        
        # 1. Obtener datos de SoftRestaurant (CF, Estelar, 130 Mid)
        if softrest_repo:
            try:
                cxp_softrest = await softrest_repo.get_cuentas_por_pagar(
                    sucursal_id=sucursal_id if sucursal_id in ['CIENFUEGOS', 'ESTELAR', '130MID'] else None,
                    tipo_proveedor=tipo_proveedor
                )
                
                for c in cxp_softrest:
                    saldo = float(c.get('Saldo', 0) or 0)
                    if saldo <= 0:
                        continue
                    
                    tipo = c.get('TipoProveedor', 'X')
                    dias_vencido = int(c.get('DiasVencido', 0) or 0)
                    
                    # ABRIL 2026: Ahora la query de SoftRestaurant incluye campos detallados:
                    # FolioEntrada, FolioFactura, FechaVencimiento, Referencia
                    
                    factura = {
                        "factura_id": c.get('CuentaPorPagarID'),
                        "proveedor_id": c.get('ProveedorID'),
                        "proveedor_nombre": c.get('ProveedorNombre', 'N/A'),
                        "proveedor_rfc": c.get('ProveedorRFC', ''),
                        "tipo_proveedor": tipo,
                        "tipo_proveedor_nombre": c.get('TipoProveedorNombre', 'OTROS'),
                        "sucursal_id": c.get('SucursalID'),
                        "sucursal_nombre": c.get('SucursalNombre'),
                        # Campos detallados desde tabla compras
                        "folio_entrada": c.get('FolioEntrada') or '-',
                        "folio_factura": c.get('FolioFactura') or '-',
                        "fecha_entrada": c.get('FechaEntrada').isoformat() if c.get('FechaEntrada') else None,
                        "fecha_vencimiento": c.get('FechaVencimiento') or '-',
                        "referencia": c.get('Referencia') or '-',
                        "observaciones": c.get('Observaciones', ''),
                        "dias_vencida": dias_vencido,
                        "importe_original": float(c.get('MontoOriginal', 0) or 0),
                        "saldo": saldo,
                        "por_vencer": float(c.get('PorVencer', 0) or 0),
                        "venc_1_30": float(c.get('Venc1_30', 0) or 0),
                        "venc_31_60": float(c.get('Venc31_60', 0) or 0),
                        "venc_61_90": float(c.get('Venc61_90', 0) or 0),
                        "venc_91_plus": float(c.get('Venc91Plus', 0) or 0),
                        "decision_pago": False,
                        "importe_a_pagar": 0,
                        "fuente": "SOFTRESTAURANT"
                    }
                    all_facturas.append(factura)
                
                if cxp_softrest:
                    fuentes_activas.append("SOFTRESTAURANT")
                    logging.info(f"[CxP] SoftRestaurant: {len(cxp_softrest)} registros")
            except Exception as e:
                logging.error(f"[CxP] Error SoftRestaurant: {e}")
        
        # 2. Obtener datos de MPRO (CENTRAL2020) - SOLO si no se está filtrando por sucursal SoftRestaurant
        softrest_sucursales = ['CIENFUEGOS', 'ESTELAR', '130MID']
        es_filtro_softrest = sucursal_id and sucursal_id in softrest_sucursales
        
        if mpro_repo and not es_filtro_softrest:
            try:
                # Si se filtra por sucursal MPRO específica, usar ese filtro
                mpro_sucursal = sucursal_id if sucursal_id and sucursal_id not in softrest_sucursales else None
                
                cxp_mpro = await mpro_repo.get_cuentas_por_pagar(
                    sucursal_id=mpro_sucursal,
                    proveedor_id=proveedor_id,
                    solo_vencidas=solo_vencidas,
                    fecha_corte=fecha_corte
                )
                
                for c in cxp_mpro:
                    saldo = float(c.get('Saldo', 0) or 0)
                    if saldo <= 0:
                        continue
                    
                    dias_vencido = int(c.get('DiasVencido', 0) or 0)
                    
                    # MPRO no tiene clasificación A/B/X, usar X por defecto
                    factura = {
                        "factura_id": f"MPRO_{c.get('CuentaPorPagarID')}",
                        "proveedor_id": c.get('ProveedorID'),
                        "proveedor_nombre": c.get('ProveedorNombre') or c.get('ProveedorNombreComercial') or f"Proveedor {c.get('ProveedorID')}",
                        "proveedor_rfc": c.get('ProveedorRFC', ''),
                        "tipo_proveedor": "M",  # M = MPRO
                        "tipo_proveedor_nombre": "MPRO",
                        "sucursal_id": c.get('SucursalID'),
                        "sucursal_nombre": c.get('SucursalNombre', f"MPRO {c.get('SucursalID')}"),
                        "folio_entrada": c.get('FolioEntrada', c.get('NumeroDocumento', 'N/A')),
                        "folio_factura": c.get('FolioFactura', c.get('NumeroDocumento', '')),
                        "fecha_entrada": str(c.get('FechaEntrada', c.get('FechaDocumento', '')))[:10] if c.get('FechaEntrada') or c.get('FechaDocumento') else None,
                        "fecha_vencimiento": str(c.get('FechaVencimiento', ''))[:10] if c.get('FechaVencimiento') else None,
                        "dias_vencida": max(0, dias_vencido),
                        "importe_original": float(c.get('MontoOriginal', 0) or 0),
                        "saldo": saldo,
                        "por_vencer": saldo if dias_vencido <= 0 else 0,
                        "venc_1_30": saldo if 1 <= dias_vencido <= 30 else 0,
                        "venc_31_60": saldo if 31 <= dias_vencido <= 60 else 0,
                        "venc_61_90": saldo if 61 <= dias_vencido <= 90 else 0,
                        "venc_91_plus": saldo if dias_vencido > 90 else 0,
                        "decision_pago": False,
                        "importe_a_pagar": 0,
                        "fuente": "MPRO"
                    }
                    all_facturas.append(factura)
                
                if cxp_mpro:
                    fuentes_activas.append("MPRO")
                    logging.info(f"[CxP] MPRO: {len(cxp_mpro)} registros")
            except Exception as e:
                logging.error(f"[CxP] Error MPRO: {e}")
        
        # 3. Si hay datos, APLICAR FILTROS y agrupar por tipo de proveedor
        if all_facturas:
            # APLICAR FILTROS antes de agrupar
            if solo_vencidas:
                all_facturas = [f for f in all_facturas if f.get('dias_vencida', 0) > 0]
            
            if solo_decision_pago:
                all_facturas = [f for f in all_facturas if f.get('decision_pago', False)]
            
            # Agrupar por TIPO DE PROVEEDOR (A, B, X, M)
            tipos = {}
            for factura in all_facturas:
                tipo = factura.get('tipo_proveedor', 'X')
                tipo_nombre = factura.get('tipo_proveedor_nombre', 'OTROS')
                
                if tipo not in tipos:
                    tipos[tipo] = {
                        "proveedor_id": tipo,
                        "proveedor_nombre": f"{tipo} - {tipo_nombre}",
                        "proveedor_rfc": "",
                        "cantidad_facturas": 0,
                        "subtotal_importe": 0.0,
                        "subtotal_saldo": 0.0,
                        "cantidad_vencidas": 0,
                        "facturas": []
                    }
                
                tipos[tipo]["facturas"].append(factura)
                tipos[tipo]["cantidad_facturas"] += 1
                tipos[tipo]["subtotal_importe"] += factura["importe_original"]
                tipos[tipo]["subtotal_saldo"] += factura["saldo"]
                if factura["dias_vencida"] > 0:
                    tipos[tipo]["cantidad_vencidas"] += 1
            
            # Ordenar tipos: A, B, X, M (MPRO al final)
            orden_tipos = ['A', 'B', 'X', 'M']
            proveedores_ordenados = [tipos.get(t) for t in orden_tipos if t in tipos]
            
            totales = {
                "total_saldo": sum(p["subtotal_saldo"] for p in proveedores_ordenados),
                "total_importe": sum(p["subtotal_importe"] for p in proveedores_ordenados),
                "total_proveedores": len(proveedores_ordenados),
                "cantidad_facturas": sum(p["cantidad_facturas"] for p in proveedores_ordenados),
                "cantidad_vencidas": sum(p["cantidad_vencidas"] for p in proveedores_ordenados)
            }
            
            return {
                "fuente": "+".join(fuentes_activas) if fuentes_activas else "NINGUNA",
                "proveedores": proveedores_ordenados,
                "total_facturas": totales["cantidad_facturas"],
                "totales": totales
            }
    
    # Fallback a MPRO solo (si no se ejecutó el bloque combinado)
    mpro_repo = await get_mpro_repo()
    
    # Usar MPRO como fuente principal de CxP
    if mpro_repo and not use_demo:
        try:
            cxp_sql = await mpro_repo.get_cuentas_por_pagar(
                sucursal_id=sucursal_id,
                proveedor_id=proveedor_id,
                solo_vencidas=solo_vencidas,
                fecha_corte=fecha_corte
            )
            
            # Si hay datos reales, usarlos
            if cxp_sql:
                # Transformar a formato del frontend
                facturas = []
                for c in cxp_sql:
                    saldo = float(c.get('Saldo', 0) or 0)
                    if saldo <= 0:
                        continue  # Solo pendientes
                    
                    dias_vencido = int(c.get('DiasVencido', 0) or 0)
                    
                    factura = {
                        "factura_id": c.get('CuentaPorPagarID'),
                        "documento_fiscal_id": c.get('DocumentoFiscalID'),
                        "proveedor_id": c.get('ProveedorID'),
                        "proveedor_nombre": c.get('ProveedorNombre') or c.get('ProveedorNombreComercial') or f"Proveedor {c.get('ProveedorID')}",
                        "proveedor_rfc": c.get('ProveedorRFC'),
                        "sucursal_id": c.get('SucursalID'),
                        "sucursal_nombre": c.get('SucursalNombre', f"Sucursal {c.get('SucursalID')}"),
                        "numero_documento": c.get('NumeroDocumento'),
                        "folio_entrada": c.get('NumeroDocumento'),
                        "folio_factura": c.get('NumeroDocumento'),
                        "fecha_documento": str(c.get('FechaDocumento', ''))[:10],
                        "fecha_entrada": str(c.get('FechaDocumento', ''))[:10],
                        "fecha_vencimiento": str(c.get('FechaVencimiento', ''))[:10],
                        "fecha_recepcion": str(c.get('FechaRecepcion', ''))[:10] if c.get('FechaRecepcion') else None,
                        "dias_credito": c.get('DiasCredito', 0),
                        "dias_vencida": max(0, dias_vencido),
                        "importe_total": float(c.get('MontoOriginal', 0) or 0),
                        "monto_pagado": float(c.get('MontoPagado', 0) or 0),
                        "saldo": saldo,
                        "estatus_pago_id": c.get('EstatusPagoID'),
                        "estatus_nombre": c.get('EstatusNombre', 'Pendiente'),
                        "moneda_id": c.get('MonedaID', 1),
                        "tipo_cambio": float(c.get('TipoCambio', 1) or 1),
                        "observaciones": c.get('Observaciones'),
                        "decision_pago": False,  # Campo para UI
                        "importe_a_pagar": 0,     # Campo para UI
                        "ruta_pdf_factura": None,
                        "ruta_xml": None,
                        "ruta_pdf_entrada": None,
                        "fuente": "SQL_SERVER_REAL"
                    }
                    facturas.append(factura)
                
                # Agrupar por proveedor
                proveedores_dict = {}
                for f in facturas:
                    prov_id = f["proveedor_id"]
                    if prov_id not in proveedores_dict:
                        proveedores_dict[prov_id] = {
                            "proveedor_id": prov_id,
                            "proveedor_nombre": f["proveedor_nombre"],
                            "proveedor_rfc": f["proveedor_rfc"],
                            "facturas": [],
                            "subtotal_importe": 0,
                            "subtotal_saldo": 0,
                            "subtotal_a_pagar": 0,
                            "cantidad_facturas": 0,
                            "cantidad_vencidas": 0
                        }
                    
                    proveedores_dict[prov_id]["facturas"].append(f)
                    proveedores_dict[prov_id]["subtotal_importe"] += f["importe_total"]
                    proveedores_dict[prov_id]["subtotal_saldo"] += f["saldo"]
                    proveedores_dict[prov_id]["cantidad_facturas"] += 1
                    if f["dias_vencida"] > 0:
                        proveedores_dict[prov_id]["cantidad_vencidas"] += 1
                
                # Ordenar proveedores por saldo descendente
                proveedores_list = sorted(
                    proveedores_dict.values(),
                    key=lambda x: x["subtotal_saldo"],
                    reverse=True
                )
                
                # Totales generales
                total_importe = sum(f["importe_total"] for f in facturas)
                total_saldo = sum(f["saldo"] for f in facturas)
                total_vencidas = sum(1 for f in facturas if f["dias_vencida"] > 0)
                
                return {
                    "proveedores": proveedores_list,
                    "total_facturas": len(facturas),
                    "fuente": "SQL_SERVER_REAL",
                    "totales": {
                        "total_importe": round(total_importe, 2),
                        "total_saldo": round(total_saldo, 2),
                        "total_a_pagar": 0,
                        "cantidad_proveedores": len(proveedores_list),
                        "cantidad_facturas": len(facturas),
                        "cantidad_vencidas": total_vencidas
                    }
                }
            else:
                # Sin datos en SQL - retornar vacío
                return {
                    "proveedores": [],
                    "total_facturas": 0,
                    "fuente": "SQL_SERVER_REAL",
                    "mensaje": "No hay cuentas por pagar registradas. La tabla Finanzas_CuentasPorPagar está vacía.",
                    "totales": {
                        "total_importe": 0,
                        "total_saldo": 0,
                        "total_a_pagar": 0,
                        "cantidad_proveedores": 0,
                        "cantidad_facturas": 0,
                        "cantidad_vencidas": 0
                    }
                }
        except Exception as e:
            logging.error(f"Error obteniendo CxP de SQL: {e}")
            # Continuar con datos demo si hay error
    
    # MODO DEMO - usar datos generados
    facturas = [f for f in _facturas_db if f["saldo"] > 0]  # Solo pendientes
    
    # Aplicar filtros
    if sucursal_id:
        facturas = [f for f in facturas if f["sucursal_id"] == sucursal_id]
    
    if proveedor_id:
        facturas = [f for f in facturas if f["proveedor_id"] == proveedor_id]
    
    if fecha_corte:
        facturas = [f for f in facturas if f["fecha_entrada"] <= fecha_corte]
    
    if solo_vencidas:
        facturas = [f for f in facturas if f["dias_vencida"] > 0]
    
    if solo_decision_pago:
        facturas = [f for f in facturas if f["decision_pago"]]
    
    # Marcar fuente
    for f in facturas:
        f["fuente"] = "DEMO"
    
    # Agrupar por proveedor
    proveedores_dict = {}
    for f in facturas:
        prov_id = f["proveedor_id"]
        if prov_id not in proveedores_dict:
            proveedores_dict[prov_id] = {
                "proveedor_id": prov_id,
                "proveedor_nombre": f["proveedor_nombre"],
                "proveedor_rfc": f["proveedor_rfc"],
                "facturas": [],
                "subtotal_importe": 0,
                "subtotal_saldo": 0,
                "subtotal_a_pagar": 0,
                "cantidad_facturas": 0,
                "cantidad_vencidas": 0
            }
        
        proveedores_dict[prov_id]["facturas"].append(f)
        proveedores_dict[prov_id]["subtotal_importe"] += f["importe_total"]
        proveedores_dict[prov_id]["subtotal_saldo"] += f["saldo"]
        proveedores_dict[prov_id]["subtotal_a_pagar"] += f["importe_a_pagar"] if f["decision_pago"] else 0
        proveedores_dict[prov_id]["cantidad_facturas"] += 1
        if f["dias_vencida"] > 0:
            proveedores_dict[prov_id]["cantidad_vencidas"] += 1
    
    # Ordenar facturas dentro de cada proveedor por fecha de vencimiento
    for prov in proveedores_dict.values():
        prov["facturas"].sort(key=lambda x: x["fecha_vencimiento"])
    
    # Convertir a lista ordenada por nombre de proveedor
    proveedores_list = sorted(proveedores_dict.values(), key=lambda x: x["proveedor_nombre"])
    
    # Calcular totales generales
    total_importe = sum(p["subtotal_importe"] for p in proveedores_list)
    total_saldo = sum(p["subtotal_saldo"] for p in proveedores_list)
    total_a_pagar = sum(p["subtotal_a_pagar"] for p in proveedores_list)
    total_facturas = sum(p["cantidad_facturas"] for p in proveedores_list)
    total_vencidas = sum(p["cantidad_vencidas"] for p in proveedores_list)
    
    return {
        "proveedores": proveedores_list,
        "total_facturas": total_facturas,
        "fuente": "DEMO",
        "mensaje": "Datos de demostración. Para usar datos reales, asegúrese de tener registros en Finanzas_CuentasPorPagar.",
        "totales": {
            "total_importe": round(total_importe, 2),
            "total_saldo": round(total_saldo, 2),
            "total_a_pagar": round(total_a_pagar, 2),
            "cantidad_facturas": total_facturas,
            "cantidad_vencidas": total_vencidas,
            "cantidad_proveedores": len(proveedores_list)
        },
        "filtros_aplicados": {
            "sucursal_id": sucursal_id,
            "proveedor_id": proveedor_id,
            "fecha_corte": fecha_corte,
            "solo_vencidas": solo_vencidas,
            "solo_decision_pago": solo_decision_pago
        }
    }


@router.get("/resumen")
async def get_resumen_cuentas_por_pagar(
    sucursal_id: Optional[str] = None,
    use_demo: bool = Query(False, description="Usar datos demo en lugar de SQL real"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Resumen ejecutivo de cuentas por pagar.
    
    CONECTADO A SOFTRESTAURANT (CF, Estelar, 130 Mid)
    Calcula antigüedad desde datos reales.
    """
    softrest_repo = await get_softrest_repo()
    
    # Primero intentar SoftRestaurant
    if softrest_repo and not use_demo:
        try:
            antiguedad = await softrest_repo.get_resumen_antiguedad(sucursal_id=sucursal_id)
            
            if antiguedad.get('total_facturas', 0) > 0:
                # Obtener también resumen por tipo
                por_tipo = await softrest_repo.get_resumen_por_tipo(sucursal_id=sucursal_id)
                
                return {
                    "fuente": "SOFTRESTAURANT_REAL",
                    "resumen": {
                        "total_facturas": antiguedad['total_facturas'],
                        "total_saldo": round(antiguedad['total_saldo'], 2),
                        "total_decision_pago": 0,
                        "facturas_con_decision": 0
                    },
                    "antiguedad": antiguedad,
                    "por_tipo": por_tipo
                }
        except Exception as e:
            logging.error(f"Error obteniendo resumen CxP de SoftRestaurant: {e}")
    
    # Fallback a MPRO
    mpro_repo = await get_mpro_repo()
    
    # Usar MPRO que tiene método optimizado para antigüedad
    if mpro_repo and not use_demo:
        try:
            antiguedad = await mpro_repo.get_resumen_antiguedad(sucursal_id=sucursal_id)
            
            if antiguedad.get('total_facturas', 0) > 0:
                return {
                    "fuente": "MPRO_REAL",
                    "resumen": {
                        "total_facturas": antiguedad['total_facturas'],
                        "total_saldo": round(antiguedad['total_saldo'], 2),
                        "total_decision_pago": 0,
                        "facturas_con_decision": 0
                    },
                    "antiguedad": antiguedad
                }
        except Exception as e:
            logging.error(f"Error obteniendo resumen CxP de MPRO: {e}")
    
    # MODO DEMO - usar datos generados
    facturas = [f for f in _facturas_db if f["saldo"] > 0]
    
    if sucursal_id:
        # Convertir a int si viene como string para demo
        try:
            suc_id = int(sucursal_id) if sucursal_id else None
            facturas = [f for f in facturas if f["sucursal_id"] == suc_id]
        except ValueError:
            pass  # Si no es int, ignorar filtro
    
    # Clasificar por antigüedad
    corriente = [f for f in facturas if f["dias_vencida"] == 0]
    vencidas_1_30 = [f for f in facturas if 1 <= f["dias_vencida"] <= 30]
    vencidas_31_60 = [f for f in facturas if 31 <= f["dias_vencida"] <= 60]
    vencidas_61_90 = [f for f in facturas if 61 <= f["dias_vencida"] <= 90]
    vencidas_90_plus = [f for f in facturas if f["dias_vencida"] > 90]
    
    return {
        "fuente": "DEMO",
        "resumen": {
            "total_facturas": len(facturas),
            "total_saldo": round(sum(f["saldo"] for f in facturas), 2),
            "total_decision_pago": round(sum(f["importe_a_pagar"] for f in facturas if f["decision_pago"]), 2),
            "facturas_con_decision": len([f for f in facturas if f["decision_pago"]])
        },
        "antiguedad": {
            "corriente": {
                "cantidad": len(corriente),
                "monto": round(sum(f["saldo"] for f in corriente), 2)
            },
            "vencidas_1_30": {
                "cantidad": len(vencidas_1_30),
                "monto": round(sum(f["saldo"] for f in vencidas_1_30), 2)
            },
            "vencidas_31_60": {
                "cantidad": len(vencidas_31_60),
                "monto": round(sum(f["saldo"] for f in vencidas_31_60), 2)
            },
            "vencidas_61_90": {
                "cantidad": len(vencidas_61_90),
                "monto": round(sum(f["saldo"] for f in vencidas_61_90), 2)
            },
            "vencidas_90_plus": {
                "cantidad": len(vencidas_90_plus),
                "monto": round(sum(f["saldo"] for f in vencidas_90_plus), 2)
            }
        }
    }


@router.get("/proveedores")
async def listar_proveedores_con_saldo(
    sucursal_id: Optional[str] = None,
    use_demo: bool = Query(False, description="Usar datos demo en lugar de SQL real"),
    current_user: Dict = Depends(get_current_user)
):
    """Lista proveedores que tienen facturas pendientes - CONECTADO A MPRO"""
    mpro_repo = await get_mpro_repo()
    
    # Usar MPRO como fuente principal
    if mpro_repo and not use_demo:
        try:
            proveedores = await mpro_repo.get_resumen_por_proveedor(sucursal_id=sucursal_id)
            
            if proveedores:
                return {
                    "fuente": "MPRO_REAL",
                    "proveedores": [
                        {
                            "proveedor_id": p.get('ProveedorID'),
                            "proveedor_nombre": p.get('ProveedorNombre') or f"Proveedor {p.get('ProveedorID')}",
                            "proveedor_rfc": p.get('ProveedorRFC'),
                            "total_saldo": float(p.get('SaldoTotal', 0) or 0),
                            "cantidad_facturas": int(p.get('CantidadFacturas', 0) or 0)
                        }
                        for p in proveedores
                    ]
                }
        except Exception as e:
            logging.error(f"Error obteniendo proveedores CxP de MPRO: {e}")
    
    # MODO DEMO
    facturas = [f for f in _facturas_db if f["saldo"] > 0]
    
    if sucursal_id:
        try:
            suc_id = int(sucursal_id) if sucursal_id else None
            facturas = [f for f in facturas if f["sucursal_id"] == suc_id]
        except ValueError:
            pass
    
    proveedores = {}
    for f in facturas:
        prov_id = f["proveedor_id"]
        if prov_id not in proveedores:
            proveedores[prov_id] = {
                "proveedor_id": prov_id,
                "proveedor_nombre": f["proveedor_nombre"],
                "proveedor_rfc": f["proveedor_rfc"],
                "total_saldo": 0,
                "cantidad_facturas": 0
            }
        proveedores[prov_id]["total_saldo"] += f["saldo"]
        proveedores[prov_id]["cantidad_facturas"] += 1
    
    return {
        "fuente": "DEMO",
        "proveedores": sorted(proveedores.values(), key=lambda x: x["proveedor_nombre"])
    }


@router.get("/sucursales")
async def listar_sucursales_cxp(
    include_hidden: bool = Query(default=False, description="Incluir sucursales ocultas"),
    current_user: Dict = Depends(get_current_user)
):
    """Lista sucursales desde MPRO/SoftRestaurant con datos de CxP, filtradas por visibilidad"""
    softrest_repo = await get_softrest_repo()
    
    # Primero SoftRestaurant (no tiene config de sucursales, devolver todo)
    if softrest_repo:
        try:
            resumen = await softrest_repo.get_resumen_por_sucursal()
            if resumen:
                return {
                    "fuente": "SOFTRESTAURANT_REAL",
                    "sucursales": [
                        {
                            "SucursalID": s.get('SucursalID'),
                            "Nombre_Sucursal": s.get('SucursalNombre') or f"Sucursal {s.get('SucursalID')}",
                            "CantidadFacturas": int(s.get('CantidadFacturas', 0) or 0),
                            "SaldoTotal": float(s.get('SaldoTotal', 0) or 0)
                        }
                        for s in resumen
                    ]
                }
        except Exception as e:
            logging.error(f"Error obteniendo sucursales SoftRestaurant: {e}")
    
    # Fallback a MPRO
    mpro_repo = await get_mpro_repo()
    
    if mpro_repo:
        try:
            resumen = await mpro_repo.get_resumen_por_sucursal()
            if resumen:
                sucursales = [
                    {
                        "SucursalID": s.get('SucursalID'),
                        "Nombre_Sucursal": s.get('SucursalNombre') or f"Sucursal {s.get('SucursalID')}",
                        "CantidadFacturas": int(s.get('CantidadFacturas', 0) or 0),
                        "SaldoTotal": float(s.get('SaldoTotal', 0) or 0)
                    }
                    for s in resumen
                ]
                
                # FILTRAR por configuración de visibilidad
                if not include_hidden:
                    # Importar el ID del servidor MPRO
                    from modules.finanzas.repository_mpro import MPRO_SERVER_ID
                    config = await get_sucursales_visibles_config(MPRO_SERVER_ID)
                    if config:  # Solo filtrar si hay configuración
                        sucursales_antes = len(sucursales)
                        sucursales = [s for s in sucursales if config.get(s['Nombre_Sucursal'], True)]
                        logging.info(f"CxP Sucursales: filtradas {len(sucursales)} de {sucursales_antes} por visibilidad")
                
                return {
                    "fuente": "MPRO_REAL",
                    "sucursales": sucursales
                }
        except Exception as e:
            logging.error(f"Error obteniendo sucursales MPRO: {e}")
    
    return {
        "fuente": "DEMO",
        "sucursales": [
            {"SucursalID": 1, "Nombre_Sucursal": "DEMO 1"},
            {"SucursalID": 2, "Nombre_Sucursal": "DEMO 2"}
        ]
    }


@router.put("/{factura_id}/decision-pago")
async def actualizar_decision_pago(
    factura_id: str,  # Cambiado a str para soportar IDs compuestos (ej: "MPRO_12345", "CIENFUEGOS_xxx")
    data: ActualizarDecisionPago,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualizar la decisión de pago de una factura.
    Soporta IDs numéricos (legacy), MPRO_xxx, y SUCURSAL_xxx (SoftRestaurant).
    """
    from urllib.parse import unquote
    
    # Decodificar URL encoding si existe
    factura_id_decoded = unquote(factura_id)
    logging.info(f"[CxP] Decision-pago recibido: {factura_id_decoded} (original: {factura_id})")
    
    # Importar helper de auditoría
    from core.auditoria_helpers import registrar_auditoria_cxp
    
    # Detectar tipo de ID y procesar
    if factura_id_decoded.startswith("MPRO_"):
        # ID compuesto de MPRO
        logging.info(f"[CxP] Factura MPRO {factura_id_decoded} - Decisión: {data.decision_pago}")
        
        # Registrar auditoría
        await registrar_auditoria_cxp(
            current_user=current_user,
            accion='EDIT',
            factura_id=factura_id_decoded,
            valor_anterior={'decision_pago': not data.decision_pago},
            valor_nuevo={'decision_pago': data.decision_pago, 'importe_a_pagar': data.importe_a_pagar},
            motivo='Marcar/desmarcar factura para pago'
        )
        
        return {
            "success": True,
            "factura_id": factura_id_decoded,
            "decision_pago": data.decision_pago,
            "fuente": "MPRO",
            "mensaje": "Decisión registrada (persistencia MPRO pendiente)"
        }
    
    # ID compuesto de SoftRestaurant (CIENFUEGOS_xxx, ESTELAR_xxx, 130MID_xxx)
    softrest_prefixes = ['CIENFUEGOS_', 'ESTELAR_', '130MID_']
    is_softrest = any(factura_id_decoded.startswith(p) for p in softrest_prefixes)
    
    if is_softrest:
        logging.info(f"[CxP] Factura SoftRestaurant {factura_id_decoded} - Decisión: {data.decision_pago}")
        
        # Registrar auditoría
        await registrar_auditoria_cxp(
            current_user=current_user,
            accion='EDIT',
            factura_id=factura_id_decoded,
            valor_anterior={'decision_pago': not data.decision_pago},
            valor_nuevo={'decision_pago': data.decision_pago, 'importe_a_pagar': data.importe_a_pagar},
            motivo='Marcar/desmarcar factura SoftRestaurant para pago'
        )
        
        return {
            "success": True,
            "factura_id": factura_id_decoded,
            "decision_pago": data.decision_pago,
            "fuente": "SOFTRESTAURANT",
            "mensaje": "Decisión registrada (persistencia SoftRestaurant pendiente)"
        }
    
    # ID numérico - buscar en datos demo/cache
    try:
        numeric_id = int(factura_id_decoded)
    except ValueError:
        logging.warning(f"[CxP] ID de factura no reconocido: {factura_id_decoded}")
        raise HTTPException(status_code=400, detail=f"ID de factura inválido: {factura_id_decoded}")
    
    factura = next((f for f in _facturas_db if f["factura_id"] == numeric_id), None)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    factura["decision_pago"] = data.decision_pago
    if data.importe_a_pagar is not None:
        factura["importe_a_pagar"] = min(data.importe_a_pagar, factura["saldo"])
    elif data.decision_pago:
        factura["importe_a_pagar"] = factura["saldo"]
    else:
        factura["importe_a_pagar"] = 0
    
    logging.info(f"[CxP] Factura {factura_id_decoded} - Decisión: {data.decision_pago}, Importe: {factura['importe_a_pagar']}")
    
    # Registrar auditoría
    await registrar_auditoria_cxp(
        current_user=current_user,
        accion='EDIT',
        factura_id=factura_id_decoded,
        valor_nuevo={'decision_pago': data.decision_pago, 'importe_a_pagar': factura['importe_a_pagar']},
        motivo='Marcar/desmarcar factura para pago'
    )
    
    return {
        "success": True,
        "factura": factura
    }


@router.put("/decision-pago-masivo")
async def actualizar_decision_pago_masivo(
    data: ActualizarDecisionPagoMasivo,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualizar decisión de pago de múltiples facturas.
    """
    from core.auditoria_helpers import registrar_auditoria_cxp
    
    actualizadas = 0
    monto_total = 0.0
    
    for factura_id in data.facturas_ids:
        factura = next((f for f in _facturas_db if f["factura_id"] == factura_id), None)
        if factura:
            factura["decision_pago"] = data.decision_pago
            factura["importe_a_pagar"] = factura["saldo"] if data.decision_pago else 0
            monto_total += factura["importe_a_pagar"]
            actualizadas += 1
    
    # Registrar auditoría para pago masivo (ALTO riesgo)
    await registrar_auditoria_cxp(
        current_user=current_user,
        accion='EDIT',
        factura_id=f'MASIVO_{len(data.facturas_ids)}',
        valor_nuevo={
            'decision_pago': data.decision_pago, 
            'cantidad_facturas': actualizadas,
            'monto_total': round(monto_total, 2)
        },
        motivo=f'Pago masivo: {actualizadas} facturas'
    )
    
    return {
        "success": True,
        "actualizadas": actualizadas,
        "total_solicitadas": len(data.facturas_ids)
    }


@router.get("/{factura_id}")
async def get_factura_detalle(
    factura_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Obtener detalle de una factura"""
    factura = next((f for f in _facturas_db if f["factura_id"] == factura_id), None)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    return {"factura": factura}
