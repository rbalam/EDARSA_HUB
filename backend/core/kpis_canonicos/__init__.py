"""
Servicio CANÓNICO de KPIs Comerciales (centralizado — máxima de centralización).
================================================================================
ÚNICA definición de los KPIs comerciales operativos. Cualquier menú (Tablero,
Compras, Inteligencia Comercial, Benchmark, Pricing) DEBE consumir estas
definiciones en lugar de recalcularlas. Glosario canónico con sinónimos:

  cheques          = tickets = comandas = cuentas cerradas
  ventas           = venta neta
  cheque_promedio  = ticket promedio = ticket medio   (ventas / cheques)
  pax              = comensales
  venta_por_pax    = consumo per cápita                (ventas / pax)
  cheques_por_pax  = rotación por comensal             (cheques / pax)

Fuente NO-LIVE: dbo.Comercial_KPIs_Diarios_v2 (tabla canónica diaria).
Llave de unidad: unidad_negocio_pk (catálogo canónico Unidades_Negocio /
UnidadesService). NUNCA server_id operacional (MPRO comparte server).
"""
from core.kpis_canonicos.service import (
    KPIsCanonicosService,
    METRICAS_CANONICAS,
    resolver_metrica,
)

__all__ = ["KPIsCanonicosService", "METRICAS_CANONICAS", "resolver_metrica"]
