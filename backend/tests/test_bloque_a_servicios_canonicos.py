"""
Regresión Bloque A (2026-06-09): capa de servicios CANÓNICOS de producto.
========================================================================
ProductosService / InsumosService / RecetasService / ConsumoRecetaService.

Valida (NO-LIVE, contra EDARSAHUB real):
- Lectura de producto por codigo/id.
- Costo de receta = SUM(CostoTotal) de componentes.
- Consumo = Cantidad * cantidad_vendida (regla canónica del usuario).
- Agregado por insumo suma correctamente.
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from core.productos_service import ProductosService  # noqa: E402
from core.insumos_service import InsumosService  # noqa: E402
from core.recetas_service import RecetasService  # noqa: E402
from core.consumo_receta_service import ConsumoRecetaService  # noqa: E402

# Servidores canónicos de prueba
SRV_MPRO = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
SRV_SOFT = "6d053c22-523e-48c0-b72b-96081e2d781b"  # CIENFUEGOS


def _producto_con_receta(server_id):
    for p in ProductosService.listar(server_ids=[server_id], solo_con_receta=True, limit=15):
        comps = RecetasService.get_componentes(server_id, p["codigo_fuente"])
        if comps:
            return p, comps
    return None, None


def test_productos_service_lectura():
    items = ProductosService.listar(server_ids=[SRV_MPRO], limit=3)
    assert isinstance(items, list) and len(items) > 0
    uno = items[0]
    assert uno.get("producto_id") and uno.get("codigo_fuente")
    # round-trip por codigo
    p = ProductosService.get_by_codigo(SRV_MPRO, uno["codigo_fuente"])
    assert p is not None and p["codigo_fuente"] == uno["codigo_fuente"]
    # round-trip por id
    p2 = ProductosService.get_by_id(uno["producto_id"])
    assert p2 is not None and p2["producto_id"] == uno["producto_id"]


def test_productos_service_contar():
    n = ProductosService.contar(server_ids=[SRV_MPRO])
    assert n > 0


def test_receta_costo_es_suma_de_componentes():
    p, comps = _producto_con_receta(SRV_MPRO)
    assert p is not None, "Debe existir al menos un producto con receta en MPRO"
    suma = sum(float(c.get("costo_total") or 0) for c in comps)
    costo = RecetasService.get_costo_total(SRV_MPRO, p["codigo_fuente"])
    assert abs(costo - suma) < 0.01


def test_consumo_es_cantidad_por_unidades():
    p, comps = _producto_con_receta(SRV_MPRO)
    assert p is not None
    N = 7
    d = ConsumoRecetaService.calcular_consumo(SRV_MPRO, p["codigo_fuente"], N)
    assert len(d["insumos"]) == len(comps)
    for ins, comp in zip(d["insumos"], comps):
        esperado = float(comp.get("cantidad") or 0) * N
        assert abs(ins["cantidad_consumida"] - esperado) < 1e-6
    costo_unit = RecetasService.get_costo_total(SRV_MPRO, p["codigo_fuente"])
    assert abs(d["costo_total"] - costo_unit * N) < 0.01


def test_consumo_agregado_suma_por_insumo():
    p, comps = _producto_con_receta(SRV_MPRO)
    assert p is not None
    cod = p["codigo_fuente"]
    ag = ConsumoRecetaService.calcular_consumo_agregado(
        SRV_MPRO, [{"producto_codigo_fuente": cod, "cantidad": 10},
                   {"producto_codigo_fuente": cod, "cantidad": 5}]
    )
    # mismo producto dos veces -> mismos insumos, cantidades sumadas (x15)
    assert len(ag["insumos"]) == len(comps)
    assert ag["productos_procesados"] == 2
    costo_unit = RecetasService.get_costo_total(SRV_MPRO, cod)
    assert abs(ag["costo_total"] - costo_unit * 15) < 0.01


def test_insumos_service_softrestaurant():
    # InsumosService responde para SoftRestaurant (CIENFUEGOS)
    items = InsumosService.listar(server_ids=[SRV_SOFT], limit=3)
    assert isinstance(items, list)
    if items:
        uno = items[0]
        got = InsumosService.get_by_codigo(SRV_SOFT, uno["codigo_fuente"])
        assert got is not None
