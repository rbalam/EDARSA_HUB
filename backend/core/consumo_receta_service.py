"""
ConsumoRecetaService - Cálculo CANÓNICO de consumo de insumos por ventas
========================================================================
Fuente única de la regla de negocio: dada una venta de productos terminados,
explota sus recetas (dbo.Sync_Productos_Recetas) y calcula el consumo de cada
INSUMO en su unidad de medida nativa (ml, gr, pza...).

Ejemplo (regla del usuario):
  - Vender 2 copas Bacardí Blanco (receta: 45 ml de insumo c/u)  -> 90 ml
  - Vender 2 botellas Bacardí Blanco (receta: 1500 ml c/u)       -> 3000 ml
  => consumo agregado del insumo "Bacardí Blanco": 3090 ml
  (la conversión a "presentaciones compradas" usa PresentacionML del catálogo
   enriquecido; aquí se calcula SOLO el consumo en unidad de receta).

Esta es la verdad ÚNICA de consumo usada por Auditoría de compras,
Análisis de inventarios e Inteligencia de ventas: el mismo número en todos.

NO-LIVE: lee EXCLUSIVAMENTE de EDARSAHUB SQL.
"""
import logging
from typing import List, Dict, Optional

from core.recetas_service import RecetasService

logger = logging.getLogger(__name__)


def _key(server_id, insumo_id, componente_codigo, unidad) -> str:
    return f"{server_id}|{insumo_id or ''}|{componente_codigo or ''}|{unidad or ''}"


class ConsumoRecetaService:
    """Cálculo canónico de consumo de insumos a partir de ventas de productos."""

    @staticmethod
    def calcular_consumo(server_id, producto_codigo_fuente, cantidad_vendida: float) -> Dict:
        """
        Consumo de insumos al vender `cantidad_vendida` de UN producto terminado.

        Returns:
            {
              "producto_codigo_fuente": str,
              "cantidad_vendida": float,
              "insumos": [
                 {insumo_id, componente_codigo, componente_nombre, unidad_medida,
                  cantidad_consumida, costo_consumido}
              ],
              "costo_total": float
            }
        """
        try:
            cant = float(cantidad_vendida or 0)
        except (TypeError, ValueError):
            cant = 0.0

        componentes = RecetasService.get_componentes(server_id, producto_codigo_fuente)
        insumos = []
        costo_total = 0.0
        for c in componentes:
            unit_cant = float(c.get("cantidad") or 0)
            unit_costo = float(c.get("costo_total") or 0)
            consumida = unit_cant * cant
            costo = unit_costo * cant
            costo_total += costo
            insumos.append({
                "insumo_id": c.get("insumo_id"),
                "componente_codigo": c.get("componente_codigo_fuente"),
                "componente_nombre": c.get("componente_nombre"),
                "unidad_medida": c.get("unidad_medida"),
                "cantidad_consumida": consumida,
                "costo_consumido": costo,
            })
        return {
            "producto_codigo_fuente": producto_codigo_fuente,
            "cantidad_vendida": cant,
            "insumos": insumos,
            "costo_total": costo_total,
        }

    @staticmethod
    def calcular_consumo_agregado(server_id, ventas: List[Dict]) -> Dict:
        """
        Consumo AGREGADO por insumo a partir de varias ventas de productos.

        Args:
            server_id: ServerID canónico (POS) ya resuelto.
            ventas: [{"producto_codigo_fuente": str, "cantidad": float}, ...]

        Returns:
            {
              "insumos": [
                 {insumo_id, componente_codigo, componente_nombre, unidad_medida,
                  cantidad_consumida, costo_consumido}  # agregado por insumo+unidad
              ],
              "costo_total": float,
              "productos_procesados": int
            }
        """
        agregado: Dict[str, Dict] = {}
        costo_total = 0.0
        procesados = 0
        for v in ventas or []:
            codigo = v.get("producto_codigo_fuente") or v.get("codigo")
            cantidad = v.get("cantidad")
            if not codigo:
                continue
            procesados += 1
            detalle = ConsumoRecetaService.calcular_consumo(server_id, codigo, cantidad)
            for ins in detalle["insumos"]:
                k = _key(server_id, ins["insumo_id"], ins["componente_codigo"], ins["unidad_medida"])
                if k not in agregado:
                    agregado[k] = {
                        "insumo_id": ins["insumo_id"],
                        "componente_codigo": ins["componente_codigo"],
                        "componente_nombre": ins["componente_nombre"],
                        "unidad_medida": ins["unidad_medida"],
                        "cantidad_consumida": 0.0,
                        "costo_consumido": 0.0,
                    }
                agregado[k]["cantidad_consumida"] += ins["cantidad_consumida"]
                agregado[k]["costo_consumido"] += ins["costo_consumido"]
                costo_total += ins["costo_consumido"]
        return {
            "insumos": sorted(
                agregado.values(),
                key=lambda x: x["cantidad_consumida"], reverse=True
            ),
            "costo_total": costo_total,
            "productos_procesados": procesados,
        }
