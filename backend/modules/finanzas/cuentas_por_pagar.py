from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Cuentas por Pagar (Facturas Pendientes)
=====================================================
Módulo para gestionar facturas pendientes de pago agrupadas por proveedor.
PROTEGIDO CON RBAC (Fase 3.1)

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
from core.security import get_current_user, get_user_empresas_permitidas, get_servers_for_empresas
import secrets  # Reemplaza random para generación de datos demo

# Importar función de filtrado de visibilidad
from modules.comercial.repository import get_sucursales_visibles_config
from core.sql_first.db import get_sql_connection, fetch_all_dict

router = APIRouter(prefix="/finanzas/cuentas-por-pagar", tags=["Cuentas por Pagar"])


# Helper functions para datos demo (reemplazan random)
def demo_uniform(min_val: float, max_val: float) -> float:
    """Genera float aleatorio en rango [min_val, max_val] para datos demo."""
    range_val = max_val - min_val
    return min_val + (secrets.randbelow(int(range_val * 100)) / 100)

def demo_randint(min_val: int, max_val: int) -> int:
    """Genera int aleatorio en rango [min_val, max_val] para datos demo."""
    return min_val + secrets.randbelow(max_val - min_val + 1)

def demo_random() -> float:
    """Genera float aleatorio en rango [0, 1) para datos demo."""
    return secrets.randbelow(1000) / 1000

def demo_choice(options: list):
    """Selecciona elemento aleatorio de lista para datos demo."""
    return options[secrets.randbelow(len(options))]


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
# LECTURA NO-LIVE (CANÓNICA) · dbo.Finanzas_CxP_Sync
# La pantalla de CxP lee EXCLUSIVAMENTE de esta tabla, poblada por el job
# core/scheduler/jobs/cxp_sync_job.py (registrado en el scheduler).
# ============================================================================
def _cxp_rows_canonico(unidad=None, tipo=None, solo_vencidas=False):
    where = ["Activo=1", "Saldo>0", "ISNULL(EsDemo,0)=0"]
    params = []
    if unidad and str(unidad).lower() not in ("todas", "all", ""):
        where.append("(UPPER(UnidadNegocio)=UPPER(%s) OR UPPER(ISNULL(UnidadNegocioNombre,''))=UPPER(%s) "
                     "OR UPPER(ISNULL(UnidadNegocioNombre,'')) LIKE UPPER(%s))")
        params += [unidad, unidad, f"%{unidad}%"]
    if tipo:
        where.append("TipoProveedor=%s"); params.append(tipo)
    if solo_vencidas:
        where.append("DiasVencido>0")
    sql = "SELECT * FROM dbo.Finanzas_CxP_Sync WHERE " + " AND ".join(where) + " ORDER BY Saldo DESC"
    return fetch_all_dict(sql, tuple(params))


def _cxp_factura_dict(r):
    dias = int(r.get('DiasVencido') or 0)
    saldo = float(r.get('Saldo') or 0)
    fe, fv = r.get('FechaEntrada'), r.get('FechaVencimiento')
    return {
        "factura_id": f"CXP_{r.get('CxpSyncID')}",
        "proveedor_id": r.get('ProveedorID'),
        "proveedor_nombre": r.get('ProveedorNombre') or 'N/A',
        "proveedor_rfc": r.get('ProveedorRFC') or '',
        "tipo_proveedor": r.get('TipoProveedor') or 'X',
        "tipo_proveedor_nombre": r.get('TipoProveedorNombre') or 'OTROS',
        "sucursal_id": r.get('UnidadNegocio'),
        "sucursal_nombre": r.get('UnidadNegocioNombre'),
        "folio_entrada": r.get('FolioEntrada') or '-',
        "folio_factura": r.get('FolioFactura') or '-',
        "fecha_entrada": str(fe)[:10] if fe else None,
        "fecha_vencimiento": str(fv)[:10] if fv else '-',
        "referencia": r.get('Referencia') or '-',
        "dias_vencida": dias,
        "importe_original": float(r.get('MontoOriginal') or 0),
        "saldo": saldo,
        "por_vencer": saldo if dias <= 0 else 0,
        "venc_1_30": saldo if 1 <= dias <= 30 else 0,
        "venc_31_60": saldo if 31 <= dias <= 60 else 0,
        "venc_61_90": saldo if 61 <= dias <= 90 else 0,
        "venc_91_plus": saldo if dias > 90 else 0,
        "decision_pago": False, "importe_a_pagar": 0,
        "fuente": r.get('Fuente'),
    }


def _cxp_listar_canonico(unidad, tipo, solo_vencidas):
    facturas = [_cxp_factura_dict(r) for r in _cxp_rows_canonico(unidad, tipo, solo_vencidas)]
    nombres = {'A': 'ALIMENTOS', 'B': 'BEBIDAS', 'X': 'OTROS'}
    tipos = {}
    for f in facturas:
        t = f['tipo_proveedor']
        if t not in tipos:
            tipos[t] = {"proveedor_id": t, "proveedor_nombre": f"{t} - {nombres.get(t, 'OTROS')}",
                        "proveedor_rfc": "", "cantidad_facturas": 0, "subtotal_importe": 0.0,
                        "subtotal_saldo": 0.0, "cantidad_vencidas": 0, "facturas": []}
        g = tipos[t]
        g["facturas"].append(f); g["cantidad_facturas"] += 1
        g["subtotal_importe"] += f["importe_original"]; g["subtotal_saldo"] += f["saldo"]
        if f["dias_vencida"] > 0:
            g["cantidad_vencidas"] += 1
    provs = [tipos[t] for t in ['A', 'B', 'X'] if t in tipos]
    totales = {
        "total_saldo": round(sum(p["subtotal_saldo"] for p in provs), 2),
        "total_importe": round(sum(p["subtotal_importe"] for p in provs), 2),
        "total_proveedores": len(provs),
        "cantidad_facturas": sum(p["cantidad_facturas"] for p in provs),
        "cantidad_vencidas": sum(p["cantidad_vencidas"] for p in provs),
    }
    return {"fuente": "CANONICO_EDARSAHUB", "proveedores": provs,
            "total_facturas": totales["cantidad_facturas"], "totales": totales}


def _cxp_resumen_canonico(unidad):
    rows = _cxp_rows_canonico(unidad)
    b = {'c': [0, 0.0], 'v1': [0, 0.0], 'v2': [0, 0.0], 'v3': [0, 0.0], 'v4': [0, 0.0]}
    total = 0.0; n = 0
    for r in rows:
        s = float(r.get('Saldo') or 0); d = int(r.get('DiasVencido') or 0)
        if s <= 0:
            continue
        n += 1; total += s
        k = 'c' if d <= 0 else 'v1' if d <= 30 else 'v2' if d <= 60 else 'v3' if d <= 90 else 'v4'
        b[k][0] += 1; b[k][1] += s
    bk = lambda k: {"cantidad": b[k][0], "monto": round(b[k][1], 2)}
    return {"fuente": "CANONICO_EDARSAHUB",
            "resumen": {"total_facturas": n, "total_saldo": round(total, 2),
                        "total_decision_pago": 0, "facturas_con_decision": 0},
            "antiguedad": {"corriente": bk('c'), "vencidas_1_30": bk('v1'), "vencidas_31_60": bk('v2'),
                           "vencidas_61_90": bk('v3'), "vencidas_90_plus": bk('v4'),
                           "total_facturas": n, "total_saldo": round(total, 2)}}


def _cxp_proveedores_canonico(unidad):
    rows = _cxp_rows_canonico(unidad)
    provs = {}
    for r in rows:
        pid = r.get('ProveedorID')
        if pid not in provs:
            provs[pid] = {"proveedor_id": pid, "proveedor_nombre": r.get('ProveedorNombre') or f"Proveedor {pid}",
                          "proveedor_rfc": r.get('ProveedorRFC') or '', "total_saldo": 0.0, "cantidad_facturas": 0}
        provs[pid]["total_saldo"] += float(r.get('Saldo') or 0)
        provs[pid]["cantidad_facturas"] += 1
    return {"fuente": "CANONICO_EDARSAHUB",
            "proveedores": sorted(provs.values(), key=lambda x: -x["total_saldo"])}


def _cxp_sucursales_canonico():
    rows = fetch_all_dict(
        "SELECT UnidadNegocio, MAX(UnidadNegocioNombre) nombre, MAX(Fuente) fuente, "
        "COUNT(*) n, SUM(Saldo) saldo FROM dbo.Finanzas_CxP_Sync "
        "WHERE Activo=1 AND Saldo>0 AND ISNULL(EsDemo,0)=0 GROUP BY UnidadNegocio ORDER BY saldo DESC")
    return {"fuente": "CANONICO_EDARSAHUB",
            "sucursales": [{"SucursalID": r["UnidadNegocio"], "Nombre_Sucursal": r.get("nombre") or r["UnidadNegocio"],
                            "CantidadFacturas": int(r["n"] or 0), "SaldoTotal": float(r["saldo"] or 0),
                            "Sistema": r.get("fuente")} for r in rows]}

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
        {"id": 2, "nombre": UnidadesService.resolver_codigo("ORIGEN") or "ORIGEN"},
        {"id": 3, "nombre": "130° TULUM"},
        {"id": 4, "nombre": "CIEN FUEGOS"},
        {"id": 5, "nombre": "XCANATUN"},
    ]
    
    facturas = []
    folio_entrada = 1000
    
    for _ in range(75):  # 75 facturas demo
        proveedor = demo_choice(proveedores)
        sucursal = demo_choice(sucursales)
        
        # Fechas aleatorias en los últimos 90 días
        dias_atras = demo_randint(5, 90)
        fecha_entrada = datetime.now() - timedelta(days=dias_atras)
        dias_credito = demo_choice([15, 30, 45, 60])
        fecha_vencimiento = fecha_entrada + timedelta(days=dias_credito)
        
        # Calcular días vencida
        hoy = datetime.now()
        dias_vencida = (hoy - fecha_vencimiento).days if hoy > fecha_vencimiento else 0
        
        # Importes
        importe_total = round(demo_uniform(1500, 85000), 2)
        pagos_realizados = round(demo_uniform(0, importe_total * 0.7), 2) if demo_random() > 0.4 else 0
        saldo = round(importe_total - pagos_realizados, 2)
        
        facturas.append({
            "factura_id": len(facturas) + 1,
            "folio_entrada": f"ENT-{folio_entrada}",
            "folio_factura": f"FA-{demo_randint(10000, 99999)}",
            "fecha_entrada": fecha_entrada.strftime("%Y-%m-%d"),
            "fecha_vencimiento": fecha_vencimiento.strftime("%Y-%m-%d"),
            "dias_vencida": max(0, dias_vencida),
            "referencia": f"Pedido #{demo_randint(100, 999)} - {demo_choice(['Mercancía', 'Insumos', 'Servicios', 'Materiales'])}",
            "importe_total": importe_total,
            "pagos_realizados": pagos_realizados,
            "saldo": saldo,
            "decision_pago": demo_choice([True, False]) if saldo > 0 else False,
            "importe_a_pagar": saldo if demo_random() > 0.3 else round(saldo * demo_uniform(0.3, 1), 2),
            "tiene_pdf_factura": demo_random() > 0.2,
            "tiene_xml": demo_random() > 0.15,
            "tiene_pdf_entrada": demo_random() > 0.1,
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
    facturas_ids: List[str]  # Cambiado de int a str para soportar IDs compuestos de SoftRestaurant
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
    # === NO-LIVE: lee EXCLUSIVAMENTE de la tabla canónica Finanzas_CxP_Sync ===
    return _cxp_listar_canonico(sucursal_id, tipo_proveedor, solo_vencidas)
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
        # FASE 1 CxP FIX: NO consultar SoftRestaurant si el filtro es exclusivamente MPRO
        es_filtro_mpro_exclusivo = sucursal_id and any(
            alias.upper() in sucursal_id.upper() or sucursal_id.upper() in alias.upper()
            for alias in [UnidadesService.resolver_codigo('ORIGEN') or 'ORIGEN', UnidadesService.resolver_codigo('130QRO') or '130QRO', '130 QRO', '130° QRO', '130° QUERETARO', '0021', '0023']
        )
        
        if softrest_repo and not es_filtro_mpro_exclusivo:
            try:
                # Pasar siempre el sucursal_id - el repositorio hace el matching flexible
                cxp_softrest = await softrest_repo.get_cuentas_por_pagar(
                    sucursal_id=sucursal_id,  # El repo maneja el matching
                    tipo_proveedor=tipo_proveedor
                )
                
                for c in cxp_softrest:
                    saldo = float(c.get('Saldo', 0) or 0)
                    if saldo <= 0:
                        continue
                    
                    tipo = c.get('TipoProveedor', 'X')
                    dias_vencido = int(c.get('DiasVencido', 0) or 0)
                    
                    # ABRIL 2026: Ahora la query de SoftRestaurant incluye campos detallados:
                    # FolioEntrada, FolioFactura, FechaVencimiento, FechaFactura, Referencia
                    
                    factura = {
                        "factura_id": c.get('CuentaPorPagarID'),
                        "proveedor_id": c.get('ProveedorID'),
                        "proveedor_nombre": c.get('ProveedorNombre', 'N/A'),
                        "proveedor_rfc": c.get('ProveedorRFC', ''),
                        "tipo_proveedor": tipo,
                        "tipo_proveedor_nombre": c.get('TipoProveedorNombre', 'OTROS'),
                        "sucursal_id": c.get('SucursalID'),
                        "sucursal_nombre": c.get('SucursalNombre'),
                        # Campos detallados desde tabla compras (SoftRestaurant)
                        "folio_entrada": c.get('FolioEntrada') or '-',
                        "folio_factura": c.get('FolioFactura') or '-',
                        "fecha_entrada": c.get('FechaEntrada') if isinstance(c.get('FechaEntrada'), str) else (c.get('FechaEntrada').isoformat() if c.get('FechaEntrada') else None),
                        "fecha_factura": c.get('FechaFactura') or None,
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
        
        # 2. Obtener datos de MPRO (CENTRAL2020)
        # FINANZAS-CXP-MPRO-COMBINE-01: Consultar MPRO siempre que no sea filtro exclusivo SoftRestaurant
        softrest_sucursales = [UnidadesService.resolver_codigo('CIENFUEGOS') or 'CIENFUEGOS', UnidadesService.resolver_codigo('ESTELAR') or 'ESTELAR', UnidadesService.resolver_codigo('130MID') or '130MID', 'CF', 'EST', '130M', 'LA ESTELAR', '130 MERIDA', '130° MERIDA', 'CIEN FUEGOS']
        mpro_sucursales = [UnidadesService.resolver_codigo('ORIGEN') or 'ORIGEN', UnidadesService.resolver_codigo('130QRO') or '130QRO', '130 QRO', '130° QRO', '130° QUERETARO', '0021', '0023']
        
        es_filtro_softrest = sucursal_id and any(
            alias.upper() in sucursal_id.upper() or sucursal_id.upper() in alias.upper()
            for alias in softrest_sucursales
        )
        es_filtro_mpro = sucursal_id and any(
            alias.upper() in sucursal_id.upper() or sucursal_id.upper() in alias.upper()
            for alias in mpro_sucursales
        )
        
        # Consultar MPRO si: no hay filtro, o hay filtro MPRO, o no es filtro exclusivo SR
        if mpro_repo and not es_filtro_softrest:
            try:
                # Mapear sucursal a código MPRO si aplica
                mpro_sucursal = None
                if es_filtro_mpro:
                    if sucursal_id and (UnidadesService.resolver_codigo('ORIGEN') or 'ORIGEN' in sucursal_id.upper() or sucursal_id == '0023'):
                        mpro_sucursal = '0023'
                    elif sucursal_id and ('QRO' in sucursal_id.upper() or sucursal_id == '0021'):
                        mpro_sucursal = '0021'
                    else:
                        mpro_sucursal = sucursal_id
                
                cxp_mpro = await mpro_repo.get_cuentas_por_pagar(
                    sucursal_id=mpro_sucursal,
                    proveedor_id=proveedor_id,
                    solo_vencidas=solo_vencidas,
                    fecha_corte=fecha_corte
                )
                
                # Mapeo de códigos MPRO a nombres
                mpro_nombres = {
                    '0023': UnidadesService.resolver_codigo('ORIGEN') or 'ORIGEN',
                    '0021': '130° QRO',
                    '0012': '130° TULUM',
                    '0026': 'MECA',
                    '0027': 'CIEN FUEGOS MPRO'
                }
                
                for c in cxp_mpro:
                    saldo = float(c.get('Saldo', 0) or 0)
                    if saldo <= 0:
                        continue
                    
                    dias_vencido = int(c.get('DiasVencido', 0) or 0)
                    suc_id = str(c.get('SucursalID', ''))
                    suc_nombre = mpro_nombres.get(suc_id, c.get('SucursalNombre', f"MPRO {suc_id}"))
                    
                    # ABRIL 2026 - CLASIFICACIÓN MPRO por Grupo_Proveedor:
                    # Gp_Cve_Grupo_Proveedor = '0001' → ALIMENTOS (A)
                    # Gp_Cve_Grupo_Proveedor = '0002' → BEBIDAS (B)
                    # Cualquier otro → OTROS (X)
                    grupo_prov = str(c.get('GrupoProveedor', '') or '').strip()
                    if grupo_prov == '0001':
                        tipo_prov = 'A'
                        tipo_prov_nombre = 'ALIMENTOS'
                    elif grupo_prov == '0002':
                        tipo_prov = 'B'
                        tipo_prov_nombre = 'BEBIDAS'
                    else:
                        tipo_prov = 'X'
                        tipo_prov_nombre = 'OTROS'
                    
                    # CORRECCIÓN MAPEO CAMPOS MPRO:
                    # FolioEntrada = Cxp_Documento
                    # FolioFactura = Cxp_Referencia
                    # Referencia = Cxp_Concepto
                    folio_entrada = c.get('FolioEntrada') or c.get('CuentaPorPagarID', 'N/A')
                    folio_factura = c.get('FolioFactura') or ''
                    referencia = c.get('Referencia') or ''
                    
                    factura = {
                        "factura_id": f"MPRO_{c.get('CuentaPorPagarID')}",
                        "proveedor_id": c.get('ProveedorID'),
                        "proveedor_nombre": c.get('ProveedorNombre') or f"Proveedor {c.get('ProveedorID')}",
                        "proveedor_rfc": c.get('ProveedorRFC', ''),
                        "tipo_proveedor": tipo_prov,
                        "tipo_proveedor_nombre": tipo_prov_nombre,
                        "sucursal_id": suc_id,
                        "sucursal_nombre": suc_nombre,
                        "folio_entrada": folio_entrada,
                        "folio_factura": folio_factura,
                        "fecha_entrada": str(c.get('FechaEntrada', ''))[:10] if c.get('FechaEntrada') else None,
                        "fecha_vencimiento": str(c.get('FechaVencimiento', ''))[:10] if c.get('FechaVencimiento') else None,
                        "dias_vencida": max(0, dias_vencido),
                        "referencia": referencia,
                        "importe_original": float(c.get('MontoOriginal', 0) or 0),
                        "saldo": saldo,
                        "por_vencer": saldo if dias_vencido <= 0 else 0,
                        "venc_1_30": saldo if 1 <= dias_vencido <= 30 else 0,
                        "venc_31_60": saldo if 31 <= dias_vencido <= 60 else 0,
                        "venc_61_90": saldo if 61 <= dias_vencido <= 90 else 0,
                        "venc_91_plus": saldo if dias_vencido > 90 else 0,
                        "decision_pago": False,
                        "importe_a_pagar": 0,
                        "fuente": "MANAGEMENTPRO"
                    }
                    all_facturas.append(factura)
                
                if cxp_mpro:
                    fuentes_activas.append("MANAGEMENTPRO")
                    logging.info(f"[CxP] MPRO: {len(cxp_mpro)} registros")
            except Exception as e:
                logging.error(f"[CxP] Error MPRO: {e}")
        
        # 3. Si hay datos, APLICAR FILTROS y agrupar por TIPO DE PROVEEDOR (A, B, X)
        # El frontend espera: { proveedor_id: "A", proveedor_nombre: "A - ALIMENTOS", facturas: [...] }
        # El frontend luego reagrupa las facturas por proveedor_nombre dentro de cada categoría
        if all_facturas:
            # APLICAR FILTROS antes de agrupar
            if solo_vencidas:
                all_facturas = [f for f in all_facturas if f.get('dias_vencida', 0) > 0]
            
            if solo_decision_pago:
                all_facturas = [f for f in all_facturas if f.get('decision_pago', False)]
            
            # Agrupar por TIPO DE PROVEEDOR (A, B, X)
            # REGLAS DE CLASIFICACIÓN:
            # - SoftRestaurant: Según clave del proveedor (A = ALIMENTOS, B = BEBIDAS, X = OTROS)
            # - MPRO: Según Grupo_Proveedor (0001 = ALIMENTOS, 0002 = BEBIDAS, otros = OTROS)
            tipos = {}
            nombres_tipos = {
                'A': 'ALIMENTOS',
                'B': 'BEBIDAS',
                'X': 'OTROS'
            }
            
            for factura in all_facturas:
                tipo = factura.get('tipo_proveedor', 'X')
                tipo_nombre = nombres_tipos.get(tipo, 'OTROS')
                
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
                tipos[tipo]["subtotal_importe"] += factura.get("importe_original", 0)
                tipos[tipo]["subtotal_saldo"] += factura.get("saldo", 0)
                if factura.get("dias_vencida", 0) > 0:
                    tipos[tipo]["cantidad_vencidas"] += 1
            
            # Ordenar tipos: A, B, X (ALIMENTOS, BEBIDAS, OTROS)
            orden_tipos = ['A', 'B', 'X']
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


def _calcular_antiguedad_en_memoria(cxp_data: List[Dict]) -> Dict[str, Any]:
    """
    Calcula la antigüedad de facturas EN MEMORIA a partir de una lista de CxP.
    Evita queries adicionales a la base de datos.
    
    FASE 4A: Función implementada para corregir variable indefinida.
    """
    hoy = datetime.now().date()
    
    corriente = []
    vencidas_1_30 = []
    vencidas_31_60 = []
    vencidas_61_90 = []
    vencidas_90_plus = []
    
    for factura in cxp_data:
        # Calcular días vencido
        fecha_venc = factura.get('FechaVencimiento') or factura.get('fecha_vencimiento')
        saldo = float(factura.get('Saldo', 0) or factura.get('saldo', 0) or 0)
        
        if saldo <= 0:
            continue  # Solo facturas con saldo pendiente
            
        dias_vencido = 0
        if fecha_venc:
            if isinstance(fecha_venc, str):
                try:
                    fecha_venc = datetime.strptime(fecha_venc[:10], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    fecha_venc = hoy
            elif hasattr(fecha_venc, 'date'):
                fecha_venc = fecha_venc.date()
            dias_vencido = max(0, (hoy - fecha_venc).days)
        
        item = {'saldo': saldo, 'dias_vencido': dias_vencido}
        
        if dias_vencido == 0:
            corriente.append(item)
        elif dias_vencido <= 30:
            vencidas_1_30.append(item)
        elif dias_vencido <= 60:
            vencidas_31_60.append(item)
        elif dias_vencido <= 90:
            vencidas_61_90.append(item)
        else:
            vencidas_90_plus.append(item)
    
    total_facturas = len(corriente) + len(vencidas_1_30) + len(vencidas_31_60) + len(vencidas_61_90) + len(vencidas_90_plus)
    total_saldo = sum(f['saldo'] for f in corriente + vencidas_1_30 + vencidas_31_60 + vencidas_61_90 + vencidas_90_plus)
    
    return {
        "total_facturas": total_facturas,
        "total_saldo": round(total_saldo, 2),
        "corriente": {
            "cantidad": len(corriente),
            "monto": round(sum(f['saldo'] for f in corriente), 2)
        },
        "vencidas_1_30": {
            "cantidad": len(vencidas_1_30),
            "monto": round(sum(f['saldo'] for f in vencidas_1_30), 2)
        },
        "vencidas_31_60": {
            "cantidad": len(vencidas_31_60),
            "monto": round(sum(f['saldo'] for f in vencidas_31_60), 2)
        },
        "vencidas_61_90": {
            "cantidad": len(vencidas_61_90),
            "monto": round(sum(f['saldo'] for f in vencidas_61_90), 2)
        },
        "vencidas_90_plus": {
            "cantidad": len(vencidas_90_plus),
            "monto": round(sum(f['saldo'] for f in vencidas_90_plus), 2)
        }
    }


def _calcular_por_tipo_en_memoria(cxp_data: List[Dict]) -> Dict[str, Any]:
    """
    Calcula distribución por tipo de documento EN MEMORIA.
    Evita queries adicionales a la base de datos.
    
    FASE 4A: Función implementada para corregir variable indefinida.
    """
    por_tipo = {}
    
    for factura in cxp_data:
        tipo = factura.get('TipoDocumento') or factura.get('tipo_documento') or 'FACTURA'
        saldo = float(factura.get('Saldo', 0) or factura.get('saldo', 0) or 0)
        
        if saldo <= 0:
            continue
            
        if tipo not in por_tipo:
            por_tipo[tipo] = {'cantidad': 0, 'monto': 0.0}
        
        por_tipo[tipo]['cantidad'] += 1
        por_tipo[tipo]['monto'] += saldo
    
    # Redondear montos
    for tipo in por_tipo:
        por_tipo[tipo]['monto'] = round(por_tipo[tipo]['monto'], 2)
    
    return por_tipo


@router.get("/resumen")
async def get_resumen_cuentas_por_pagar(
    sucursal_id: Optional[str] = None,
    use_demo: bool = Query(False, description="Usar datos demo en lugar de SQL real"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Resumen ejecutivo de cuentas por pagar.
    
    FINANZAS-CXP-MPRO-COMBINE-01 (Dic 2025):
    COMBINA SoftRestaurant + ManagementPro (no usa fallback).
    
    Fuentes:
    - SoftRestaurant: CIENFUEGOS, LA ESTELAR, 130° MERIDA
    - ManagementPro: ORIGEN (0023), 130° QRO (0021)
    
    Si una fuente falla, reporta resultado parcial con la otra.
    """
    # === NO-LIVE: lee EXCLUSIVAMENTE de la tabla canónica Finanzas_CxP_Sync ===
    return _cxp_resumen_canonico(sucursal_id)
    if use_demo:
        # Ir directo a modo demo (código existente abajo)
        pass
    else:
        # COMBINAR SR + MPRO (no fallback)
        softrest_repo = await get_softrest_repo()
        mpro_repo = await get_mpro_repo()
        
        fuentes_activas = []
        fuentes_fallidas = []
        all_cxp_data = []
        
        # Detectar si filtro es específico de una fuente
        softrest_sucursales = [UnidadesService.resolver_codigo('CIENFUEGOS') or 'CIENFUEGOS', UnidadesService.resolver_codigo('ESTELAR') or 'ESTELAR', UnidadesService.resolver_codigo('130MID') or '130MID', 'CF', 'EST', '130M', 
                               'LA ESTELAR', '130 MERIDA', '130° MERIDA', 'CIEN FUEGOS']
        mpro_sucursales = [UnidadesService.resolver_codigo('ORIGEN') or 'ORIGEN', UnidadesService.resolver_codigo('130QRO') or '130QRO', '130 QRO', '130° QRO', '130° QUERETARO', 
                          '0021', '0023']
        
        es_filtro_sr = sucursal_id and any(
            alias.upper() in sucursal_id.upper() or sucursal_id.upper() in alias.upper()
            for alias in softrest_sucursales
        )
        es_filtro_mpro = sucursal_id and any(
            alias.upper() in sucursal_id.upper() or sucursal_id.upper() in alias.upper()
            for alias in mpro_sucursales
        )
        
        # 1. Consultar SoftRestaurant (si no es filtro exclusivo MPRO)
        if softrest_repo and not es_filtro_mpro:
            try:
                cxp_sr = await softrest_repo.get_cuentas_por_pagar(
                    sucursal_id=sucursal_id if es_filtro_sr else None, 
                    limit=5000
                )
                if cxp_sr:
                    for c in cxp_sr:
                        c['_fuente'] = 'SOFTRESTAURANT'
                    all_cxp_data.extend(cxp_sr)
                    fuentes_activas.append("SOFTRESTAURANT")
                    logging.info(f"[CxP Resumen] SoftRestaurant: {len(cxp_sr)} registros")
            except Exception as e:
                logging.error(f"[CxP Resumen] Error SoftRestaurant: {e}")
                fuentes_fallidas.append(f"SOFTRESTAURANT: {str(e)[:50]}")
        
        # 2. Consultar MPRO (si no es filtro exclusivo SoftRestaurant)
        if mpro_repo and not es_filtro_sr:
            try:
                # Mapear código de sucursal MPRO si aplica
                mpro_suc = None
                if es_filtro_mpro:
                    if sucursal_id and (UnidadesService.resolver_codigo('ORIGEN') or 'ORIGEN' in sucursal_id.upper() or sucursal_id == '0023'):
                        mpro_suc = '0023'
                    elif sucursal_id and ('QRO' in sucursal_id.upper() or sucursal_id == '0021'):
                        mpro_suc = '0021'
                    else:
                        mpro_suc = sucursal_id
                
                cxp_mpro = await mpro_repo.get_cuentas_por_pagar(sucursal_id=mpro_suc)
                if cxp_mpro:
                    for c in cxp_mpro:
                        c['_fuente'] = 'MANAGEMENTPRO'
                    all_cxp_data.extend(cxp_mpro)
                    fuentes_activas.append("MANAGEMENTPRO")
                    logging.info(f"[CxP Resumen] MPRO: {len(cxp_mpro)} registros")
            except Exception as e:
                logging.error(f"[CxP Resumen] Error MPRO: {e}")
                fuentes_fallidas.append(f"MANAGEMENTPRO: {str(e)[:50]}")
        
        # 3. Si hay datos de cualquier fuente, calcular resumen combinado
        if all_cxp_data:
            antiguedad = _calcular_antiguedad_en_memoria(all_cxp_data)
            por_tipo = _calcular_por_tipo_en_memoria(all_cxp_data)
            
            # Calcular resumen por fuente
            por_fuente = {}
            for c in all_cxp_data:
                fuente = c.get('_fuente', 'UNKNOWN')
                saldo = float(c.get('Saldo', 0) or 0)
                if fuente not in por_fuente:
                    por_fuente[fuente] = {'facturas': 0, 'saldo': 0}
                por_fuente[fuente]['facturas'] += 1
                por_fuente[fuente]['saldo'] += saldo
            
            return {
                "fuente": "+".join(fuentes_activas) if fuentes_activas else "NINGUNA",
                "fuentes_detalle": por_fuente,
                "fuentes_fallidas": fuentes_fallidas if fuentes_fallidas else None,
                "resumen": {
                    "total_facturas": antiguedad['total_facturas'],
                    "total_saldo": round(antiguedad['total_saldo'], 2),
                    "total_decision_pago": 0,
                    "facturas_con_decision": 0
                },
                "antiguedad": antiguedad,
                "por_tipo": por_tipo
            }
        
        # Si ambas fuentes fallaron, reportar error parcial (no $0 falso)
        if fuentes_fallidas and not all_cxp_data:
            return {
                "fuente": "ERROR_PARCIAL",
                "fuentes_fallidas": fuentes_fallidas,
                "resumen": {
                    "total_facturas": -1,  # Indicador de error, no $0 falso
                    "total_saldo": -1,
                    "total_decision_pago": 0,
                    "facturas_con_decision": 0,
                    "error": "No se pudieron obtener datos de ninguna fuente"
                },
                "antiguedad": None,
                "por_tipo": None
            }
    
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
    """Lista proveedores que tienen facturas pendientes - NO-LIVE (canónico)"""
    return _cxp_proveedores_canonico(sucursal_id)
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
    """
    Lista sucursales con datos de CxP.
    
    FINANZAS-CXP-MPRO-COMBINE-01 (Dic 2025):
    COMBINA SoftRestaurant + ManagementPro (no usa fallback).
    
    Fuentes:
    - SoftRestaurant: CIENFUEGOS, LA ESTELAR, 130° MERIDA
    - ManagementPro: ORIGEN (0023), 130° QRO (0021)
    """
    # === NO-LIVE: lee EXCLUSIVAMENTE de la tabla canónica Finanzas_CxP_Sync ===
    return _cxp_sucursales_canonico()
    softrest_repo = await get_softrest_repo()
    mpro_repo = await get_mpro_repo()
    
    all_sucursales = []
    fuentes_activas = []
    fuentes_fallidas = []
    
    # 1. Obtener sucursales de SoftRestaurant
    if softrest_repo:
        try:
            resumen_sr = await softrest_repo.get_resumen_por_sucursal()
            if resumen_sr:
                for s in resumen_sr:
                    all_sucursales.append({
                        "SucursalID": s.get('SucursalID'),
                        "Nombre_Sucursal": s.get('SucursalNombre') or f"Sucursal {s.get('SucursalID')}",
                        "CantidadFacturas": int(s.get('CantidadFacturas', 0) or 0),
                        "SaldoTotal": float(s.get('SaldoTotal', 0) or 0),
                        "Sistema": "SOFTRESTAURANT"
                    })
                fuentes_activas.append("SOFTRESTAURANT")
                logging.info(f"[CxP Sucursales] SoftRestaurant: {len(resumen_sr)} sucursales")
        except Exception as e:
            logging.error(f"[CxP Sucursales] Error SoftRestaurant: {e}")
            fuentes_fallidas.append(f"SOFTRESTAURANT: {str(e)[:50]}")
    
    # 2. Obtener sucursales de MPRO
    if mpro_repo:
        try:
            resumen_mpro = await mpro_repo.get_resumen_por_sucursal()
            if resumen_mpro:
                # Mapeo de códigos MPRO a nombres legibles
                mpro_nombres = {
                    '0023': UnidadesService.resolver_codigo('ORIGEN') or 'ORIGEN',
                    '0021': '130° QRO',
                    '0012': '130° TULUM',
                    '0026': 'MECA',
                    '0027': 'CIEN FUEGOS MPRO'
                }
                
                for s in resumen_mpro:
                    suc_id = s.get('SucursalID')
                    nombre = mpro_nombres.get(str(suc_id), s.get('SucursalNombre') or f"MPRO {suc_id}")
                    
                    all_sucursales.append({
                        "SucursalID": suc_id,
                        "Nombre_Sucursal": nombre,
                        "CantidadFacturas": int(s.get('CantidadFacturas', 0) or 0),
                        "SaldoTotal": float(s.get('SaldoTotal', 0) or 0),
                        "Sistema": "MANAGEMENTPRO"
                    })
                fuentes_activas.append("MANAGEMENTPRO")
                logging.info(f"[CxP Sucursales] MPRO: {len(resumen_mpro)} sucursales")
        except Exception as e:
            logging.error(f"[CxP Sucursales] Error MPRO: {e}")
            fuentes_fallidas.append(f"MANAGEMENTPRO: {str(e)[:50]}")
    
    # 3. Aplicar filtro de visibilidad si corresponde
    if not include_hidden and all_sucursales:
        try:
            from modules.finanzas.repository_mpro import MPRO_SERVER_ID
            config = await get_sucursales_visibles_config(MPRO_SERVER_ID)
            if config:
                sucursales_antes = len(all_sucursales)
                all_sucursales = [s for s in all_sucursales if config.get(s['Nombre_Sucursal'], True)]
                logging.info(f"[CxP Sucursales] Filtradas {len(all_sucursales)} de {sucursales_antes} por visibilidad")
        except Exception as e:
            logging.warning(f"[CxP Sucursales] Error aplicando filtro visibilidad: {e}")
    
    # 4. Retornar resultado combinado
    if all_sucursales:
        return {
            "fuente": "+".join(fuentes_activas) if fuentes_activas else "NINGUNA",
            "fuentes_fallidas": fuentes_fallidas if fuentes_fallidas else None,
            "sucursales": all_sucursales
        }
    
    # Si no hay datos, retornar demo o error
    if fuentes_fallidas:
        return {
            "fuente": "ERROR_PARCIAL",
            "fuentes_fallidas": fuentes_fallidas,
            "sucursales": []
        }
    
    return {
        "fuente": "DEMO",
        "sucursales": [
            {"SucursalID": 1, "Nombre_Sucursal": "DEMO 1", "Sistema": "DEMO"},
            {"SucursalID": 2, "Nombre_Sucursal": "DEMO 2", "Sistema": "DEMO"}
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
        # Comparar como string para soportar IDs compuestos de SoftRestaurant
        factura = next((f for f in _facturas_db if str(f.get("factura_id", "")) == str(factura_id)), None)
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
