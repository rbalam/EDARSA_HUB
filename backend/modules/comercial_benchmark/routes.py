"""
Rutas del Benchmark Interno de Grupo (NO-LIVE, SQL-first).
==========================================================
Comparación de cifras propias vs grupo (EDARSA = grupo provisional, decisión 1b)
con CONFIDENCIALIDAD aplicada en backend (AnonymizerService). El frontend nunca
recibe nombres reales sin permiso.

Cada respuesta incluye el envelope exigido (criterios 46–54):
valor_propio, promedio/mediana/p25/p75, diferencia abs/%, percentil, posición,
cobertura, nivel_anonimizacion_aplicado, permiso_usado, advertencias,
source_table, generated_at.
"""
import logging
from datetime import date, datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query

from core.security import get_current_user_dual_dependency
from core.rbac_helper_sql import get_role_code
from core.corporate_filters.request_resolver import resolve_unidad_scope, canonical_server_id
from core.confidencialidad import AnonymizerService
from core.kpis_canonicos import KPIsCanonicosService
from modules.comercial_benchmark import repository as repo
from modules.comercial_benchmark.stats import resumen_benchmark

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/comercial/benchmark", tags=["Comercial - Benchmark Interno"])

# Dependencia de auth DUAL (cookie httpOnly + header Bearer) — funciona tanto en
# el Portal de Inteligencia (cookie) como en el app principal (Bearer).
get_current_user = get_current_user_dual_dependency()

# Umbral mínimo de unidades para evitar identificación indirecta (k-anonymity simple)
K_MIN_GRUPO = 3


def _periodo(desde: Optional[str], hasta: Optional[str]):
    """Default: últimos 12 meses (hasta exclusivo)."""
    h = datetime.strptime(hasta, "%Y-%m-%d").date() if hasta else (date.today() + timedelta(days=1))
    d = datetime.strptime(desde, "%Y-%m-%d").date() if desde else date(h.year - 1, h.month, 1)
    return d.isoformat(), h.isoformat()


async def _scope_y_propia(current_user, unidad: Optional[str]):
    from core.unidades_service import UnidadesService
    scope = await resolve_unidad_scope(current_user)
    allowed = scope.allowed_server_ids or []
    allowed_lower = {str(s).strip().lower() for s in allowed}
    propia_sid = (canonical_server_id(unidad) if unidad else None)
    if propia_sid:
        propia_sid = str(propia_sid).strip().lower()
    # identidad CANÓNICA de la unidad propia (catálogo, no denormalizado)
    propia_pk = UnidadesService.resolver_pk(unidad) if unidad else None
    # RBAC: si el usuario está restringido y pide una unidad fuera de su alcance
    if unidad and allowed_lower and propia_sid not in allowed_lower:
        raise HTTPException(status_code=403, detail="Sin acceso a la unidad solicitada")
    ctx = AnonymizerService.build_context(current_user, allowed_server_ids=allowed)
    return scope, allowed_lower, propia_sid, propia_pk, ctx


def _meta(metrica, desde, hasta, ctx, source_table, advertencias):
    return {
        "metrica": metrica,
        "periodo": {"desde": desde, "hasta": hasta},
        "nivel_anonimizacion_aplicado": ctx.nivel.value,
        "permiso_usado": None,
        "source_table": source_table,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "advertencias": advertencias,
    }


@router.get("/interno/unidades")
async def benchmark_unidades(
    unidad: Optional[str] = Query(None, description="Unidad propia (codigo/pk) para diferencia/percentil"),
    metrica: str = Query("cheque_promedio", pattern="^(ventas|ventas_brutas|ventas_sin_propina|propinas|tickets|cheques|pax|ticket_promedio|cheque_promedio|venta_por_pax|consumo_promedio_pax|cheques_por_pax)$"),
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    d, h = _periodo(desde, hasta)
    scope, allowed_lower, propia_sid, propia_pk, ctx = await _scope_y_propia(current_user, unidad)

    filas = repo.agg_unidades(metrica, d, h)
    advertencias: List[str] = []
    if len(filas) < K_MIN_GRUPO:
        advertencias.append(
            f"Cobertura de {len(filas)} unidades (< {K_MIN_GRUPO}); riesgo de identificación indirecta."
        )

    valores = [f["valor"] for f in filas if f["valor"] is not None]
    valor_propio = None
    if propia_pk:
        prop = next((f for f in filas if str(f["unidad_pk"]) == str(propia_pk)), None)
        valor_propio = prop["valor"] if prop else None
        if prop is None:
            advertencias.append("La unidad propia no tiene datos en el período.")

    envelope = resumen_benchmark(valor_propio, valores)

    # Unidades propias del usuario (por PK canónica): server permitido => propia.
    # allowed vacío = sin restricción => todas propias.
    own_pks = {f["unidad_pk"] for f in filas
               if not allowed_lower or str(f["server_id"]).strip().lower() in allowed_lower}

    salt = scope.unidad_codigo or (unidad or "grp")
    unidades_anon = AnonymizerService.anonymize_rows(
        [{"unidad_pk": f["unidad_pk"], "server_id": f["server_id"],
          "unidad_nombre": f["unidad_nombre"],
          "valor": round(f["valor"], 4) if f["valor"] is not None else None,
          "dias": f["dias"]} for f in filas],
        ctx, salt=str(salt), id_key="unidad_pk",
        name_key="unidad_nombre", own_ids=own_pks,
    )
    unidades_anon.sort(key=lambda r: (r.get("valor") is not None, r.get("valor") or 0), reverse=True)

    meta = _meta(metrica, d, h, ctx, "dbo.Comercial_KPIs_Diarios_v2", advertencias)
    meta["permiso_usado"] = "rol:" + (get_role_code(current_user) or "")
    return {"benchmark": envelope, "unidades": unidades_anon, **meta}


@router.get("/interno/productos")
async def benchmark_productos(
    unidad: str = Query(..., description="Unidad propia (codigo/pk)"),
    metrica: str = Query("ventas", pattern="^(ventas|cantidad)$"),
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    top: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    d, h = _periodo(desde, hasta)
    scope, allowed_lower, propia_sid, propia_pk, ctx = await _scope_y_propia(current_user, unidad)
    if not propia_pk:
        raise HTTPException(status_code=400, detail="No se pudo resolver la unidad propia")
    # código canónico desde el catálogo (la tabla de detalle indexa por código)
    from core.unidades_service import UnidadesService
    u_prop = UnidadesService.get_by_pk(propia_pk)
    propia_code = (u_prop or {}).get("codigo")
    if not propia_code:
        raise HTTPException(status_code=400, detail="Unidad propia no está en el catálogo canónico")

    tops = repo.top_productos_unidad(propia_code, metrica, d, h, top)
    items = []
    for p in tops:
        pid = p.get("producto_id")
        grupo = repo.agg_producto_por_unidad(pid, metrica, d, h) if pid else []
        valores = [g["valor"] for g in grupo if g["valor"] is not None]
        propio = next((g["valor"] for g in grupo
                       if str(g["unidad_pk"]) == str(propia_pk)), None)
        env = resumen_benchmark(propio, valores)
        items.append({
            "producto_id": pid,
            "producto_nombre": p.get("producto_nombre"),
            "familia_nombre": p.get("familia_nombre"),
            "casa": p.get("casa"),
            "es_alcohol": bool(p.get("es_alcohol")),
            "mi_valor": round(float(p.get("valor") or 0), 4),
            "mi_cantidad": round(float(p.get("cantidad") or 0), 4),
            "benchmark_grupo": env,
        })

    advertencias: List[str] = []
    meta = _meta(metrica, d, h, ctx, "dbo.Comercial_Inteligencia_VentasDetalleProducto", advertencias)
    meta["permiso_usado"] = "rol:" + (get_role_code(current_user) or "")
    return {"unidad": scope.unidad_codigo or unidad, "metrica": metrica,
            "productos": items, **meta}


@router.get("/mis-unidades")
async def mis_unidades(current_user: dict = Depends(get_current_user)):
    """Unidades CANÓNICAS que el usuario puede elegir como 'propia' (por scope).
    allowed vacío = sin restricción => todas. Fuente: UnidadesService (catálogo)."""
    from core.unidades_service import UnidadesService
    scope = await resolve_unidad_scope(current_user)
    allowed = {str(s).strip().lower() for s in (scope.allowed_server_ids or [])}
    out = []
    for u in UnidadesService.get_all():
        sid = str(u.get("server_id") or "").strip().lower()
        if allowed and sid not in allowed:
            continue
        out.append({"codigo": u.get("codigo"), "nombre": u.get("nombre")})
    return {"unidades": out}


@router.get("/metricas")
async def metricas(current_user: dict = Depends(get_current_user)):
    """Glosario CANÓNICO de métricas desde SQL (sin hardcode en frontend)."""
    return {"metricas": KPIsCanonicosService.metricas_disponibles()}


@router.get("/cobertura")
async def cobertura(current_user: dict = Depends(get_current_user)):
    return repo.cobertura_detalle()
