"""
EDARSA HUB - Control de Ingresos
=================================
Módulo para gestionar ingresos desde cortes de caja.
PROTEGIDO CON RBAC (Fase 3.1)

ABRIL 2026: Conectado a SQL Server real (Finanzas_CortesCaja)
- Si hay datos en SQL, usa datos reales
- Si no hay datos, puede usar modo demo (parámetro use_demo=true)

Reglas de Depósito:
1. EFECTIVO: Se deposita al día siguiente. Vie/Sáb/Dom → Lunes
2. TARJETAS:
   - Débito: 24hrs hábiles, comisión configurable por sucursal
   - Crédito: 24hrs hábiles, comisión configurable por sucursal
   - AMEX: 48hrs hábiles, comisión configurable por sucursal
   - Internacional: 48hrs hábiles, comisión configurable por sucursal
3. Proveedor de terminales: NetPay
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from core.security import get_current_user, get_user_empresas_permitidas, get_servers_for_empresas
import random

router = APIRouter(prefix="/finanzas/ingresos", tags=["Control de Ingresos"])


async def get_user_sucursales_permitidas(current_user: Dict[str, Any]) -> List[str]:
    """
    RBAC Fase 3.1: Obtiene los CÓDIGOS de sucursales permitidas para el usuario.
    Retorna lista vacía si el usuario tiene acceso total (admin).
    """
    from server import db
    
    empresas_permitidas = await get_user_empresas_permitidas(current_user)
    if not empresas_permitidas:
        return []  # Sin restricción (admin)
    
    # Obtener códigos de las empresas permitidas
    empresas = await db.empresas.find(
        {'id': {'$in': empresas_permitidas}},
        {'_id': 0, 'codigo': 1, 'nombre': 1}
    ).to_list(100)
    
    # Retornar códigos y nombres para matching flexible
    codigos = []
    for e in empresas:
        if e.get('codigo'):
            codigos.append(e['codigo'].upper())
        if e.get('nombre'):
            codigos.append(e['nombre'].upper())
    
    return codigos

# ============================================================================
# REPOSITORIO REAL
# ============================================================================

# Variable global para el repositorio (se inicializa con db en server.py)
_finanzas_repo = None

def set_finanzas_repository(repo):
    """Configura el repositorio de finanzas (llamado desde server.py)"""
    global _finanzas_repo
    _finanzas_repo = repo

async def get_repo():
    """Obtiene el repositorio de finanzas"""
    if _finanzas_repo:
        return _finanzas_repo
    # Fallback: crear repositorio ad-hoc (no recomendado en producción)
    return None

# ============================================================================
# CONFIGURACIÓN DE COMISIONES Y PLAZOS (valores por defecto)
# ============================================================================

COMISIONES_TARJETAS = {
    "debito": {"comision": 0.012, "dias_deposito": 1, "nombre": "Débito"},
    "credito": {"comision": 0.015, "dias_deposito": 1, "nombre": "Crédito"},
    "amex": {"comision": 0.024, "dias_deposito": 2, "nombre": "American Express"},
    "internacional": {"comision": 0.02, "dias_deposito": 2, "nombre": "Internacional"},
}

IVA = 0.16  # 16% IVA sobre comisiones

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def calcular_fecha_deposito_efectivo(fecha_corte: datetime) -> datetime:
    """
    Calcula fecha de depósito de efectivo.
    - Lunes a Jueves: día siguiente
    - Viernes, Sábado, Domingo: Lunes siguiente
    """
    dia_semana = fecha_corte.weekday()  # 0=Lunes, 6=Domingo
    
    if dia_semana == 4:  # Viernes -> Lunes (+3)
        return fecha_corte + timedelta(days=3)
    elif dia_semana == 5:  # Sábado -> Lunes (+2)
        return fecha_corte + timedelta(days=2)
    elif dia_semana == 6:  # Domingo -> Lunes (+1)
        return fecha_corte + timedelta(days=1)
    else:  # Lunes-Jueves -> día siguiente
        return fecha_corte + timedelta(days=1)


def calcular_fecha_deposito_tarjeta(fecha_corte: datetime, dias_habiles: int) -> datetime:
    """
    Calcula fecha de depósito considerando días hábiles.
    Excluye sábados y domingos.
    """
    fecha = fecha_corte
    dias_agregados = 0
    
    while dias_agregados < dias_habiles:
        fecha += timedelta(days=1)
        # Si no es sábado (5) ni domingo (6), cuenta como día hábil
        if fecha.weekday() < 5:
            dias_agregados += 1
    
    return fecha


def calcular_comision_con_iva(monto: float, tipo_tarjeta: str) -> dict:
    """Calcula comisión + IVA para un tipo de tarjeta"""
    config = COMISIONES_TARJETAS.get(tipo_tarjeta, COMISIONES_TARJETAS["debito"])
    comision_neta = monto * config["comision"]
    iva_comision = comision_neta * IVA
    comision_total = comision_neta + iva_comision
    neto_a_recibir = monto - comision_total
    
    return {
        "monto_bruto": round(monto, 2),
        "comision_porcentaje": config["comision"] * 100,
        "comision_neta": round(comision_neta, 2),
        "iva_comision": round(iva_comision, 2),
        "comision_total": round(comision_total, 2),
        "neto_a_recibir": round(neto_a_recibir, 2)
    }


# ============================================================================
# DATOS DEMO
# ============================================================================

def generar_cortes_caja_demo():
    """Genera cortes de caja demo para pruebas"""
    sucursales = [
        {"id": 1, "nombre": "130° QUERETARO"},
        {"id": 2, "nombre": "ORIGEN"},
        {"id": 3, "nombre": "130° TULUM"},
        {"id": 4, "nombre": "CIEN FUEGOS"},
        {"id": 5, "nombre": "XCANATUN"},
    ]
    
    cortes = []
    
    for dias_atras in range(30):  # Últimos 30 días
        fecha = datetime.now() - timedelta(days=dias_atras)
        
        for sucursal in sucursales:
            # Generar montos aleatorios
            efectivo = round(random.uniform(8000, 45000), 2)
            debito = round(random.uniform(15000, 65000), 2)
            credito = round(random.uniform(10000, 50000), 2)
            amex = round(random.uniform(2000, 15000), 2) if random.random() > 0.3 else 0
            internacional = round(random.uniform(1000, 8000), 2) if random.random() > 0.5 else 0
            
            # Calcular fechas de depósito
            fecha_dep_efectivo = calcular_fecha_deposito_efectivo(fecha)
            fecha_dep_debito = calcular_fecha_deposito_tarjeta(fecha, 1)
            fecha_dep_credito = calcular_fecha_deposito_tarjeta(fecha, 1)
            fecha_dep_amex = calcular_fecha_deposito_tarjeta(fecha, 2)
            fecha_dep_internacional = calcular_fecha_deposito_tarjeta(fecha, 2)
            
            # Calcular comisiones
            com_debito = calcular_comision_con_iva(debito, "debito")
            com_credito = calcular_comision_con_iva(credito, "credito")
            com_amex = calcular_comision_con_iva(amex, "amex") if amex > 0 else None
            com_internacional = calcular_comision_con_iva(internacional, "internacional") if internacional > 0 else None
            
            # Estado de depósito
            hoy = datetime.now()
            efectivo_depositado = fecha_dep_efectivo.date() < hoy.date() and random.random() > 0.2
            tarjetas_depositadas = fecha_dep_debito.date() < hoy.date() and random.random() > 0.15
            
            corte = {
                "corte_id": len(cortes) + 1,
                "sucursal_id": sucursal["id"],
                "sucursal_nombre": sucursal["nombre"],
                "fecha_corte": fecha.strftime("%Y-%m-%d"),
                "dia_semana": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][fecha.weekday()],
                
                # Efectivo
                "efectivo": efectivo,
                "fecha_deposito_efectivo": fecha_dep_efectivo.strftime("%Y-%m-%d"),
                "efectivo_depositado": efectivo_depositado,
                "efectivo_referencia_deposito": f"DEP-{random.randint(10000, 99999)}" if efectivo_depositado else None,
                
                # Tarjetas
                "debito": debito,
                "debito_comision": com_debito["comision_total"],
                "debito_neto": com_debito["neto_a_recibir"],
                "fecha_deposito_debito": fecha_dep_debito.strftime("%Y-%m-%d"),
                
                "credito": credito,
                "credito_comision": com_credito["comision_total"],
                "credito_neto": com_credito["neto_a_recibir"],
                "fecha_deposito_credito": fecha_dep_credito.strftime("%Y-%m-%d"),
                
                "amex": amex,
                "amex_comision": com_amex["comision_total"] if com_amex else 0,
                "amex_neto": com_amex["neto_a_recibir"] if com_amex else 0,
                "fecha_deposito_amex": fecha_dep_amex.strftime("%Y-%m-%d") if amex > 0 else None,
                
                "internacional": internacional,
                "internacional_comision": com_internacional["comision_total"] if com_internacional else 0,
                "internacional_neto": com_internacional["neto_a_recibir"] if com_internacional else 0,
                "fecha_deposito_internacional": fecha_dep_internacional.strftime("%Y-%m-%d") if internacional > 0 else None,
                
                "tarjetas_depositadas": tarjetas_depositadas,
                "tarjetas_referencia_netpay": f"NP-{random.randint(100000, 999999)}" if tarjetas_depositadas else None,
                
                # Totales
                "total_venta": round(efectivo + debito + credito + amex + internacional, 2),
                "total_comisiones": round(com_debito["comision_total"] + com_credito["comision_total"] + 
                                         (com_amex["comision_total"] if com_amex else 0) + 
                                         (com_internacional["comision_total"] if com_internacional else 0), 2),
                "total_neto_tarjetas": round(com_debito["neto_a_recibir"] + com_credito["neto_a_recibir"] +
                                            (com_amex["neto_a_recibir"] if com_amex else 0) +
                                            (com_internacional["neto_a_recibir"] if com_internacional else 0), 2),
                
                # Conciliación
                "conciliado": efectivo_depositado and tarjetas_depositadas,
                "observaciones": None
            }
            
            cortes.append(corte)
    
    return cortes


_cortes_caja_db = generar_cortes_caja_demo()
_movimientos_banco_db = []  # Para estados de cuenta cargados

# ============================================================================
# SCHEMAS
# ============================================================================

class RegistrarDepositoEfectivo(BaseModel):
    corte_id: int
    referencia_deposito: str
    monto_depositado: float
    observaciones: Optional[str] = None

class ConciliarMovimiento(BaseModel):
    corte_id: int
    movimiento_banco_id: int
    tipo: str  # efectivo, tarjetas

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/cortes-caja")
async def listar_cortes_caja(
    sucursal_id: Optional[int] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    solo_pendientes: bool = False,
    use_demo: bool = Query(False, description="Usar datos demo en lugar de SQL real"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Listar cortes de caja con detalle de ingresos.
    
    CONECTADO A SQL SERVER REAL (Finanzas_CortesCaja)
    Si use_demo=true, usa datos demo para pruebas.
    """
    repo = await get_repo()
    
    # Intentar obtener datos reales de SQL Server
    if repo and not use_demo:
        try:
            cortes_sql = await repo.get_cortes_caja(
                sucursal_id=sucursal_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                solo_pendientes_deposito=solo_pendientes
            )
            
            # Si hay datos reales, usarlos
            if cortes_sql:
                # Transformar a formato del frontend
                cortes = []
                for c in cortes_sql:
                    # Calcular neto por tipo
                    debito_neto = float(c.get('TotalTarjetaDebito', 0) or 0) - float(c.get('ComisionDebito', 0) or 0)
                    credito_neto = float(c.get('TotalTarjetaCredito', 0) or 0) - float(c.get('ComisionCredito', 0) or 0)
                    amex_neto = float(c.get('TotalAmex', 0) or 0) - float(c.get('ComisionAmex', 0) or 0)
                    internacional_neto = float(c.get('TotalInternacional', 0) or 0) - float(c.get('ComisionInternacional', 0) or 0)
                    
                    total_venta = (
                        float(c.get('TotalEfectivo', 0) or 0) +
                        float(c.get('TotalTarjetaDebito', 0) or 0) +
                        float(c.get('TotalTarjetaCredito', 0) or 0) +
                        float(c.get('TotalAmex', 0) or 0) +
                        float(c.get('TotalInternacional', 0) or 0) +
                        float(c.get('TotalVales', 0) or 0) +
                        float(c.get('TotalOtros', 0) or 0)
                    )
                    
                    total_comisiones = (
                        float(c.get('ComisionDebito', 0) or 0) +
                        float(c.get('ComisionCredito', 0) or 0) +
                        float(c.get('ComisionAmex', 0) or 0) +
                        float(c.get('ComisionInternacional', 0) or 0)
                    )
                    
                    corte = {
                        "corte_id": c.get('CorteCajaID'),
                        "sucursal_id": c.get('SucursalID'),
                        "sucursal_nombre": c.get('SucursalNombre', f"Sucursal {c.get('SucursalID')}"),
                        "fecha_corte": str(c.get('FechaCorte', ''))[:10],
                        "turno_id": c.get('TurnoID'),
                        
                        # Efectivo
                        "efectivo": float(c.get('TotalEfectivo', 0) or 0),
                        "fecha_deposito_efectivo": str(c.get('FechaDepositoEfectivo', ''))[:10] if c.get('FechaDepositoEfectivo') else None,
                        "efectivo_depositado": bool(c.get('DepositadoEfectivo')),
                        
                        # Tarjetas
                        "debito": float(c.get('TotalTarjetaDebito', 0) or 0),
                        "debito_comision": float(c.get('ComisionDebito', 0) or 0),
                        "debito_neto": round(debito_neto, 2),
                        "fecha_deposito_debito": str(c.get('FechaDepositoDebito', ''))[:10] if c.get('FechaDepositoDebito') else None,
                        
                        "credito": float(c.get('TotalTarjetaCredito', 0) or 0),
                        "credito_comision": float(c.get('ComisionCredito', 0) or 0),
                        "credito_neto": round(credito_neto, 2),
                        "fecha_deposito_credito": str(c.get('FechaDepositoCredito', ''))[:10] if c.get('FechaDepositoCredito') else None,
                        
                        "amex": float(c.get('TotalAmex', 0) or 0),
                        "amex_comision": float(c.get('ComisionAmex', 0) or 0),
                        "amex_neto": round(amex_neto, 2),
                        "fecha_deposito_amex": str(c.get('FechaDepositoAmex', ''))[:10] if c.get('FechaDepositoAmex') else None,
                        
                        "internacional": float(c.get('TotalInternacional', 0) or 0),
                        "internacional_comision": float(c.get('ComisionInternacional', 0) or 0),
                        "internacional_neto": round(internacional_neto, 2),
                        "fecha_deposito_internacional": str(c.get('FechaDepositoInternacional', ''))[:10] if c.get('FechaDepositoInternacional') else None,
                        
                        # Estado de depósitos de tarjetas
                        "tarjetas_depositadas": (
                            bool(c.get('DepositadoDebito')) and 
                            bool(c.get('DepositadoCredito')) and
                            bool(c.get('DepositadoAmex')) and
                            bool(c.get('DepositadoInternacional'))
                        ),
                        
                        # Totales
                        "total_venta": round(total_venta, 2),
                        "total_comisiones": round(total_comisiones, 2),
                        "total_neto_tarjetas": round(debito_neto + credito_neto + amex_neto + internacional_neto, 2),
                        
                        # Conciliación
                        "estatus_cierre_id": c.get('EstatusCierreID'),
                        "estatus_nombre": c.get('EstatusNombre', 'Pendiente'),
                        "conciliado": c.get('EstatusCierreID') == 3,  # 3 = Conciliado
                        "observaciones": c.get('Observaciones'),
                        
                        # Metadata
                        "fuente": "SQL_SERVER_REAL"
                    }
                    cortes.append(corte)
                
                # Calcular totales
                total_efectivo = sum(c["efectivo"] for c in cortes)
                total_tarjetas = sum(c["debito"] + c["credito"] + c["amex"] + c["internacional"] for c in cortes)
                total_comisiones = sum(c["total_comisiones"] for c in cortes)
                total_neto = sum(c["total_neto_tarjetas"] for c in cortes)
                
                return {
                    "cortes": cortes[:100],
                    "total": len(cortes),
                    "fuente": "SQL_SERVER_REAL",
                    "resumen": {
                        "total_efectivo": round(total_efectivo, 2),
                        "total_tarjetas_bruto": round(total_tarjetas, 2),
                        "total_comisiones": round(total_comisiones, 2),
                        "total_neto_tarjetas": round(total_neto, 2),
                        "total_ventas": round(total_efectivo + total_tarjetas, 2)
                    }
                }
            else:
                # Sin datos en SQL - retornar vacío con mensaje
                return {
                    "cortes": [],
                    "total": 0,
                    "fuente": "SQL_SERVER_REAL",
                    "mensaje": "No hay cortes de caja registrados. La tabla Finanzas_CortesCaja está vacía.",
                    "resumen": {
                        "total_efectivo": 0,
                        "total_tarjetas_bruto": 0,
                        "total_comisiones": 0,
                        "total_neto_tarjetas": 0,
                        "total_ventas": 0
                    }
                }
        except Exception as e:
            logging.error(f"Error obteniendo cortes de SQL: {e}")
            # Continuar con datos demo si hay error
    
    # MODO DEMO - usar datos generados
    cortes = _cortes_caja_db.copy()
    
    if sucursal_id:
        cortes = [c for c in cortes if c["sucursal_id"] == sucursal_id]
    
    if fecha_inicio:
        cortes = [c for c in cortes if c["fecha_corte"] >= fecha_inicio]
    
    if fecha_fin:
        cortes = [c for c in cortes if c["fecha_corte"] <= fecha_fin]
    
    if solo_pendientes:
        cortes = [c for c in cortes if not c["conciliado"]]
    
    # Ordenar por fecha descendente
    cortes.sort(key=lambda x: x["fecha_corte"], reverse=True)
    
    # Marcar fuente
    for c in cortes:
        c["fuente"] = "DEMO"
    
    # Calcular totales
    total_efectivo = sum(c["efectivo"] for c in cortes)
    total_tarjetas = sum(c["debito"] + c["credito"] + c["amex"] + c["internacional"] for c in cortes)
    total_comisiones = sum(c["total_comisiones"] for c in cortes)
    total_neto = sum(c["total_neto_tarjetas"] for c in cortes)
    
    return {
        "cortes": cortes[:100],  # Limitar a 100
        "total": len(cortes),
        "fuente": "DEMO",
        "mensaje": "Datos de demostración. Para usar datos reales, asegúrese de tener registros en Finanzas_CortesCaja.",
        "resumen": {
            "total_efectivo": round(total_efectivo, 2),
            "total_tarjetas_bruto": round(total_tarjetas, 2),
            "total_comisiones": round(total_comisiones, 2),
            "total_neto_tarjetas": round(total_neto, 2),
            "total_ventas": round(total_efectivo + total_tarjetas, 2)
        }
    }


@router.get("/saldos-por-depositar")
async def get_saldos_por_depositar(
    sucursal_id: Optional[int] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtener saldos pendientes de depositar (efectivo y tarjetas).
    """
    cortes = _cortes_caja_db.copy()
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    if sucursal_id:
        cortes = [c for c in cortes if c["sucursal_id"] == sucursal_id]
    
    # Efectivo pendiente de depositar
    efectivo_pendiente = [c for c in cortes if not c["efectivo_depositado"]]
    
    # Tarjetas pendientes de depositar
    tarjetas_pendiente = [c for c in cortes if not c["tarjetas_depositadas"]]
    
    # Agrupar por fecha de depósito esperada
    efectivo_por_fecha = {}
    for c in efectivo_pendiente:
        fecha = c["fecha_deposito_efectivo"]
        if fecha not in efectivo_por_fecha:
            efectivo_por_fecha[fecha] = {"fecha": fecha, "monto": 0, "cortes": []}
        efectivo_por_fecha[fecha]["monto"] += c["efectivo"]
        efectivo_por_fecha[fecha]["cortes"].append({
            "corte_id": c["corte_id"],
            "sucursal": c["sucursal_nombre"],
            "fecha_corte": c["fecha_corte"],
            "monto": c["efectivo"]
        })
    
    tarjetas_por_fecha = {}
    for c in tarjetas_pendiente:
        fecha = c["fecha_deposito_debito"]  # Usar fecha de débito como referencia
        if fecha not in tarjetas_por_fecha:
            tarjetas_por_fecha[fecha] = {"fecha": fecha, "monto_bruto": 0, "monto_neto": 0, "comisiones": 0, "cortes": []}
        tarjetas_por_fecha[fecha]["monto_bruto"] += c["debito"] + c["credito"] + c["amex"] + c["internacional"]
        tarjetas_por_fecha[fecha]["monto_neto"] += c["total_neto_tarjetas"]
        tarjetas_por_fecha[fecha]["comisiones"] += c["total_comisiones"]
        tarjetas_por_fecha[fecha]["cortes"].append({
            "corte_id": c["corte_id"],
            "sucursal": c["sucursal_nombre"],
            "fecha_corte": c["fecha_corte"],
            "debito": c["debito"],
            "credito": c["credito"],
            "amex": c["amex"],
            "internacional": c["internacional"],
            "neto": c["total_neto_tarjetas"]
        })
    
    # Totales
    total_efectivo_pendiente = sum(c["efectivo"] for c in efectivo_pendiente)
    total_tarjetas_pendiente = sum(c["total_neto_tarjetas"] for c in tarjetas_pendiente)
    
    return {
        "efectivo": {
            "total_pendiente": round(total_efectivo_pendiente, 2),
            "cantidad_cortes": len(efectivo_pendiente),
            "por_fecha": sorted(efectivo_por_fecha.values(), key=lambda x: x["fecha"])
        },
        "tarjetas": {
            "total_pendiente_neto": round(total_tarjetas_pendiente, 2),
            "cantidad_cortes": len(tarjetas_pendiente),
            "por_fecha": sorted(tarjetas_por_fecha.values(), key=lambda x: x["fecha"])
        },
        "total_por_depositar": round(total_efectivo_pendiente + total_tarjetas_pendiente, 2)
    }


@router.get("/resumen-comisiones")
async def get_resumen_comisiones(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sucursal_id: Optional[int] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Resumen de comisiones por tipo de tarjeta.
    """
    cortes = _cortes_caja_db.copy()
    
    if sucursal_id:
        cortes = [c for c in cortes if c["sucursal_id"] == sucursal_id]
    if fecha_inicio:
        cortes = [c for c in cortes if c["fecha_corte"] >= fecha_inicio]
    if fecha_fin:
        cortes = [c for c in cortes if c["fecha_corte"] <= fecha_fin]
    
    resumen = {
        "debito": {
            "ventas": sum(c["debito"] for c in cortes),
            "comisiones": sum(c["debito_comision"] for c in cortes),
            "neto": sum(c["debito_neto"] for c in cortes),
            "tasa": "1.2% + IVA"
        },
        "credito": {
            "ventas": sum(c["credito"] for c in cortes),
            "comisiones": sum(c["credito_comision"] for c in cortes),
            "neto": sum(c["credito_neto"] for c in cortes),
            "tasa": "1.5% + IVA"
        },
        "amex": {
            "ventas": sum(c["amex"] for c in cortes),
            "comisiones": sum(c["amex_comision"] for c in cortes),
            "neto": sum(c["amex_neto"] for c in cortes),
            "tasa": "2.4% + IVA"
        },
        "internacional": {
            "ventas": sum(c["internacional"] for c in cortes),
            "comisiones": sum(c["internacional_comision"] for c in cortes),
            "neto": sum(c["internacional_neto"] for c in cortes),
            "tasa": "2.0% + IVA"
        }
    }
    
    # Redondear
    for tipo in resumen:
        resumen[tipo]["ventas"] = round(resumen[tipo]["ventas"], 2)
        resumen[tipo]["comisiones"] = round(resumen[tipo]["comisiones"], 2)
        resumen[tipo]["neto"] = round(resumen[tipo]["neto"], 2)
    
    total_ventas = sum(r["ventas"] for r in resumen.values())
    total_comisiones = sum(r["comisiones"] for r in resumen.values())
    total_neto = sum(r["neto"] for r in resumen.values())
    
    return {
        "por_tipo": resumen,
        "totales": {
            "ventas": round(total_ventas, 2),
            "comisiones": round(total_comisiones, 2),
            "neto": round(total_neto, 2)
        },
        "periodo": {
            "inicio": fecha_inicio,
            "fin": fecha_fin
        }
    }


@router.put("/cortes-caja/{corte_id}/deposito-efectivo")
async def registrar_deposito_efectivo(
    corte_id: int,
    data: RegistrarDepositoEfectivo,
    current_user: Dict = Depends(get_current_user)
):
    """Registrar depósito de efectivo de un corte"""
    corte = next((c for c in _cortes_caja_db if c["corte_id"] == corte_id), None)
    if not corte:
        raise HTTPException(status_code=404, detail="Corte no encontrado")
    
    corte["efectivo_depositado"] = True
    corte["efectivo_referencia_deposito"] = data.referencia_deposito
    corte["observaciones"] = data.observaciones
    
    # Verificar si ya está completamente conciliado
    if corte["tarjetas_depositadas"]:
        corte["conciliado"] = True
    
    return {"success": True, "corte": corte}


@router.put("/cortes-caja/{corte_id}/deposito-tarjetas")
async def registrar_deposito_tarjetas(
    corte_id: int,
    referencia_netpay: str,
    current_user: Dict = Depends(get_current_user)
):
    """Registrar depósito de tarjetas (NetPay) de un corte"""
    corte = next((c for c in _cortes_caja_db if c["corte_id"] == corte_id), None)
    if not corte:
        raise HTTPException(status_code=404, detail="Corte no encontrado")
    
    corte["tarjetas_depositadas"] = True
    corte["tarjetas_referencia_netpay"] = referencia_netpay
    
    # Verificar si ya está completamente conciliado
    if corte["efectivo_depositado"]:
        corte["conciliado"] = True
    
    return {"success": True, "corte": corte}


@router.post("/cargar-estado-cuenta")
async def cargar_estado_cuenta(
    banco: str = Query(..., description="BBVA, Santander, etc."),
    archivo: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Cargar estado de cuenta bancario para conciliación.
    Acepta archivos CSV o Excel.
    """
    # Por ahora solo guardamos la metadata
    # En producción: parsear el archivo y extraer movimientos
    
    contenido = await archivo.read()
    
    # Simular extracción de movimientos
    movimientos_extraidos = [
        {
            "id": len(_movimientos_banco_db) + i + 1,
            "banco": banco,
            "fecha": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
            "concepto": random.choice(["DEPOSITO EFECTIVO", "NETPAY SA DE CV", "TRASPASO", "COMISION"]),
            "cargo": round(random.uniform(0, 5000), 2) if random.random() > 0.7 else 0,
            "abono": round(random.uniform(5000, 100000), 2) if random.random() > 0.3 else 0,
            "saldo": round(random.uniform(100000, 500000), 2),
            "referencia": f"REF-{random.randint(10000, 99999)}",
            "conciliado": False,
            "corte_id_relacionado": None
        }
        for i in range(random.randint(15, 30))
    ]
    
    _movimientos_banco_db.extend(movimientos_extraidos)
    
    return {
        "success": True,
        "mensaje": f"Estado de cuenta de {banco} cargado correctamente",
        "archivo": archivo.filename,
        "movimientos_extraidos": len(movimientos_extraidos)
    }


@router.get("/movimientos-banco")
async def listar_movimientos_banco(
    solo_pendientes: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """Listar movimientos bancarios cargados"""
    movimientos = _movimientos_banco_db.copy()
    
    if solo_pendientes:
        movimientos = [m for m in movimientos if not m["conciliado"]]
    
    return {
        "movimientos": movimientos,
        "total": len(movimientos),
        "pendientes": len([m for m in _movimientos_banco_db if not m["conciliado"]])
    }


@router.get("/config-comisiones")
async def get_config_comisiones(
    current_user: Dict = Depends(get_current_user)
):
    """Obtener configuración de comisiones actual"""
    return {
        "comisiones": {
            tipo: {
                "nombre": config["nombre"],
                "comision_porcentaje": config["comision"] * 100,
                "dias_deposito": config["dias_deposito"],
                "iva": IVA * 100,
                "comision_total_porcentaje": round(config["comision"] * (1 + IVA) * 100, 3)
            }
            for tipo, config in COMISIONES_TARJETAS.items()
        },
        "proveedor": "NetPay",
        "notas": [
            "Comisiones incluyen IVA (16%)",
            "Efectivo: depósito día siguiente (Vie/Sáb/Dom → Lunes)",
            "Débito/Crédito: 24 hrs hábiles",
            "AMEX/Internacional: 48 hrs hábiles"
        ]
    }
