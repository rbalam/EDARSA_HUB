"""
EDARSA HUB - Cuentas por Pagar (Facturas Pendientes)
=====================================================
Módulo para gestionar facturas pendientes de pago agrupadas por proveedor.

Datos a mostrar:
1. Folio de entrada
1a. Folio de factura
2. Fecha de entrada
3. Fecha de vencimiento
4. Días de vencida
5. Referencia/comentario
6. Importe total
7. Saldo del documento
8. Decisión de pago (si/no)
9. Importe a pagar
10. PDF factura
11. XML
12. Entrada al sistema (PDF)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from core.security import get_current_user
import random

router = APIRouter(prefix="/finanzas/cuentas-por-pagar", tags=["Cuentas por Pagar"])

# ============================================================================
# DATOS DEMO (Producción: conectar a SQL Server)
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

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("")
async def listar_facturas_pendientes(
    sucursal_id: Optional[int] = None,
    proveedor_id: Optional[int] = None,
    fecha_corte: Optional[str] = None,  # YYYY-MM-DD
    solo_vencidas: bool = False,
    solo_decision_pago: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """
    Listar facturas pendientes de pago.
    Filtros: sucursal, proveedor, fecha de corte, solo vencidas, solo con decisión de pago.
    Agrupa por proveedor con subtotales.
    """
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
        "totales": {
            "total_importe": round(total_importe, 2),
            "total_saldo": round(total_saldo, 2),
            "total_a_pagar": round(total_a_pagar, 2),
            "total_facturas": total_facturas,
            "total_vencidas": total_vencidas,
            "total_proveedores": len(proveedores_list)
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
    sucursal_id: Optional[int] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Resumen ejecutivo de cuentas por pagar.
    """
    facturas = [f for f in _facturas_db if f["saldo"] > 0]
    
    if sucursal_id:
        facturas = [f for f in facturas if f["sucursal_id"] == sucursal_id]
    
    # Clasificar por antigüedad
    corriente = [f for f in facturas if f["dias_vencida"] == 0]
    vencidas_1_30 = [f for f in facturas if 1 <= f["dias_vencida"] <= 30]
    vencidas_31_60 = [f for f in facturas if 31 <= f["dias_vencida"] <= 60]
    vencidas_61_90 = [f for f in facturas if 61 <= f["dias_vencida"] <= 90]
    vencidas_90_plus = [f for f in facturas if f["dias_vencida"] > 90]
    
    return {
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
    sucursal_id: Optional[int] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Lista proveedores que tienen facturas pendientes"""
    facturas = [f for f in _facturas_db if f["saldo"] > 0]
    
    if sucursal_id:
        facturas = [f for f in facturas if f["sucursal_id"] == sucursal_id]
    
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
        "proveedores": sorted(proveedores.values(), key=lambda x: x["proveedor_nombre"])
    }


@router.put("/{factura_id}/decision-pago")
async def actualizar_decision_pago(
    factura_id: int,
    data: ActualizarDecisionPago,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualizar la decisión de pago de una factura.
    """
    factura = next((f for f in _facturas_db if f["factura_id"] == factura_id), None)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    factura["decision_pago"] = data.decision_pago
    if data.importe_a_pagar is not None:
        factura["importe_a_pagar"] = min(data.importe_a_pagar, factura["saldo"])
    elif data.decision_pago:
        factura["importe_a_pagar"] = factura["saldo"]
    else:
        factura["importe_a_pagar"] = 0
    
    logging.info(f"[CxP] Factura {factura_id} - Decisión: {data.decision_pago}, Importe: {factura['importe_a_pagar']}")
    
    return {
        "success": True,
        "factura": factura
    }


@router.put("/decision-pago-masivo")
async def actualizar_decision_pago_masivo(
    facturas_ids: List[int],
    decision_pago: bool,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualizar decisión de pago de múltiples facturas.
    """
    actualizadas = 0
    for factura_id in facturas_ids:
        factura = next((f for f in _facturas_db if f["factura_id"] == factura_id), None)
        if factura:
            factura["decision_pago"] = decision_pago
            factura["importe_a_pagar"] = factura["saldo"] if decision_pago else 0
            actualizadas += 1
    
    return {
        "success": True,
        "actualizadas": actualizadas,
        "total_solicitadas": len(facturas_ids)
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
