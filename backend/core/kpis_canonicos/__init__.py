"""
Servicio CANÓNICO de KPIs Comerciales (centralizado — máxima de centralización).
================================================================================
ÚNICA definición de los KPIs comerciales operativos. Cualquier menú (Tablero,
Compras, Inteligencia Comercial, Benchmark, Pricing) DEBE consumir estas
definiciones en lugar de recalcularlas. Glosario canónico con sinónimos:

  ventas           = ventas_total con IVA; propinas separadas
  propinas         = propinas_total
  cheques          = tickets = comandas = cuentas cerradas
  cheque_promedio  = ventas_total / CHEQUES   (promedio por CUENTA)
  pax              = comensales
  ticket_promedio  = alias legacy de cheque_promedio
  pax_promedio     = ventas_total / PAX
  cheques_por_pax  = rotación por comensal           (cheques / pax)

Fuente NO-LIVE: dbo.vw_Comercial_KPIs_Diarios_v2_Runtime (vista runtime canónica diaria).
Llave de unidad: unidad_negocio_pk (catálogo canónico Unidades_Negocio /
UnidadesService). NUNCA server_id operacional (MPRO comparte server).
"""
from core.kpis_canonicos.service import (
    KPIsCanonicosService,
    resolver_metrica,
    aplicar_definicion,
)

__all__ = ["KPIsCanonicosService", "resolver_metrica", "aplicar_definicion"]
