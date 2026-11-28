"""Filtro canónico, en lectura, de conceptos origen para inventarios.

Los códigos elegidos en Servidores_Conexiones.tipos_movimiento gobiernan
MOVIMIENTOS de MPRO y SoftRestaurant. Nunca son una política fija.
El ledger almacena TODOS los movimientos; la configuración no borra historia.
"""
from typing import Any, Iterable, List, Tuple


def normalize_movement_code(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("codigo", "ConceptoOrigen", "concepto_origen",
                    "Tm_Cve_Tipo_Movimiento", "code", "id", "value"):
            v = value.get(key)
            if v is not None and str(v).strip():
                value = v
                break
        else:
            return ""
    if value is None:
        return ""
    return str(value).strip().upper()


def normalize_movement_codes(values: Iterable[Any] = None) -> List[str]:
    result = []
    seen = set()
    for value in values or []:
        code = normalize_movement_code(value)
        if code and code not in seen:
            result.append(code)
            seen.add(code)
    return result


def movement_origin_sql_filter(
    selected: Iterable[Any],
    *,
    reference_column: str = "m.ReferenciaTipo",
) -> Tuple[str, List[str]]:
    """Predicado parametrizado SOLO sobre ConceptoOrigen trazable.

    Un registro legacy sin MOVIMIENTO_POS|codigo es ambiguo y no puede ser
    clasificado por TipoMovimientoID: varios conceptos convergen allí.
    Los códigos sin selección devuelven cero filas; no se hace fallback.
    """
    codes = normalize_movement_codes(selected)
    if not codes:
        return "1=0", []
    code_expr = (
        f"UPPER(LTRIM(RTRIM(SUBSTRING({reference_column}, "
        f"LEN('MOVIMIENTO_POS|')+1, 50))))"
    )
    # pymssql usa formato estilo printf con parametros %s: un % literal
    # en la consulta parametrizada DEBE escaparse como %%, de lo contrario
    # se interpreta como formato y puede fallar todo el reporte/drilldown.
    predicate = (
        f"{reference_column} LIKE 'MOVIMIENTO_POS|%%' "
        f"AND {code_expr} IN ({','.join(['%s'] * len(codes))})"
    )
    return predicate, codes
