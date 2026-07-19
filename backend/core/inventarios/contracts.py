import re
from dataclasses import dataclass
from typing import Any, Dict, List


MAX_FOLIOS = 50


def validate_inventory_identifier(value: Any, max_length: int = 100) -> bool:
    text = str(value or "").strip()
    if not text or len(text) > max_length:
        return False
    return re.fullmatch(r"[A-Za-z0-9_-]+", text) is not None


def sanitize_folio_list(folios: List[Any], max_count: int = MAX_FOLIOS) -> List[str]:
    if not folios:
        return []
    sanitized: List[str] = []
    for folio in folios[:max_count]:
        folio_text = str(folio or "").strip()
        if folio_text and validate_inventory_identifier(folio_text, max_length=50):
            sanitized.append(folio_text.replace("'", "''"))
    return sanitized


@dataclass(frozen=True)
class NormalizedInventoryRequest:
    server_id: str
    sucursal_id_param: Any
    sucursal: Any
    almacen: Any
    almacenes: List[Any]
    fecha_ini: Any
    fecha_fin: Any
    lista_folios_ini: List[str]
    lista_folios_fin: List[str]
    inventarios_iniciales_info: List[Any]
    inventarios_finales_info: List[Any]
    filtro_categorias_frontend: List[Any]
    filtro_familias_frontend: List[Any]
    filtro_subfamilias_frontend: List[Any]
    agrupar_insumos: bool


def build_normalized_inventory_request(report_params: Dict[str, Any], server_id: str) -> NormalizedInventoryRequest:
    sucursal_id_param = report_params.get("sucursal_id")
    sucursal = report_params.get("sucursal")
    almacen = report_params.get("almacen")
    almacenes = report_params.get("almacenes", [])
    fecha_ini = report_params.get("fecha_ini")
    fecha_fin = report_params.get("fecha_fin")
    folio_inicial = report_params.get("folio_inicial")
    folio_final = report_params.get("folio_final")

    folios_iniciales = report_params.get("folios_iniciales", [])
    folios_finales = report_params.get("folios_finales", [])

    if folios_iniciales:
        lista_folios_ini = folios_iniciales
    elif folio_inicial:
        lista_folios_ini = [folio_inicial]
    else:
        lista_folios_ini = []

    if folios_finales:
        lista_folios_fin = folios_finales
    elif folio_final:
        lista_folios_fin = [folio_final]
    else:
        lista_folios_fin = []

    lista_folios_ini = sanitize_folio_list(lista_folios_ini)
    lista_folios_fin = sanitize_folio_list(lista_folios_fin)

    return NormalizedInventoryRequest(
        server_id=server_id,
        sucursal_id_param=sucursal_id_param,
        sucursal=sucursal,
        almacen=almacen,
        almacenes=almacenes,
        fecha_ini=fecha_ini,
        fecha_fin=fecha_fin,
        lista_folios_ini=lista_folios_ini,
        lista_folios_fin=lista_folios_fin,
        inventarios_iniciales_info=report_params.get("inventarios_iniciales_info", []),
        inventarios_finales_info=report_params.get("inventarios_finales_info", []),
        filtro_categorias_frontend=report_params.get("categorias", []),
        filtro_familias_frontend=report_params.get("familias", []),
        filtro_subfamilias_frontend=report_params.get("subfamilias", []),
        agrupar_insumos=bool(report_params.get("agrupar_insumos", False)),
    )
