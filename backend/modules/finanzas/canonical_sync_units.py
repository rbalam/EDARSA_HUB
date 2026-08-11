"""
Resolver canónico de unidades elegibles para sincronizaciones financieras.

Contrato V1.0:
- Fuente única: dbo.Unidades_Negocio -> dbo.Servidores_Conexiones.
- Solo unidades y servidores activos.
- system_type normalizado mediante core.system_type_utils.
- MPRO exige sucursal_origen_id canónica.
- Sin listas de unidades hardcodeadas.
- Sin caché.
- Sin fallback.
- Sin MongoDB.
- Fail-closed ante catálogo inconsistente.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from core.sql_first.db import (
    fetch_all_dict_readonly,
)
from core.system_type_utils import (
    SystemType,
    normalize_system_type,
)


_CANONICAL_UNITS_SQL = """
SELECT
    CONVERT(NVARCHAR(100), u.id)
        AS unidad_negocio_pk,
    u.codigo
        AS unidad_negocio_codigo,
    u.nombre
        AS unidad_negocio_nombre,
    CONVERT(NVARCHAR(100), u.server_id)
        AS server_id,
    CONVERT(NVARCHAR(100), u.sucursal_origen_id)
        AS sucursal_origen_id,
    u.system_type
        AS unidad_system_type,
    s.system_type
        AS servidor_system_type,
    u.activo
        AS unidad_activo,
    s.activo
        AS servidor_activo
FROM dbo.Unidades_Negocio AS u
INNER JOIN dbo.Servidores_Conexiones AS s
    ON s.id = u.server_id
WHERE u.activo = 1
  AND s.activo = 1
ORDER BY
    u.orden,
    u.codigo
"""


_SUPPORTED_SYNC_SYSTEMS = frozenset(
    {
        SystemType.MANAGEMENTPRO.value,
        SystemType.SOFTRESTAURANT.value,
    }
)


class FinanzasCanonicalUnitError(RuntimeError):
    """Catálogo canónico inválido o no disponible."""


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _effective_system_type(
    row: Dict[str, Any],
) -> str:
    unit_type = normalize_system_type(
        row.get("unidad_system_type")
    )
    server_type = normalize_system_type(
        row.get("servidor_system_type")
    )

    unit_supported = (
        unit_type in _SUPPORTED_SYNC_SYSTEMS
    )
    server_supported = (
        server_type in _SUPPORTED_SYNC_SYSTEMS
    )

    if (
        unit_supported
        and server_supported
        and unit_type != server_type
    ):
        raise FinanzasCanonicalUnitError(
            "Conflicto system_type entre unidad "
            "y servidor: "
            f"unidad={unit_type}, "
            f"servidor={server_type}, "
            "codigo="
            f"{_clean(row.get('unidad_negocio_codigo'))}"
        )

    if unit_supported:
        return unit_type

    if server_supported:
        return server_type

    return SystemType.UNKNOWN.value


def get_canonical_finance_sync_units(
    target_system: str,
) -> Tuple[Dict[str, Any], ...]:
    """
    Retorna las unidades activas del sistema solicitado.

    No utiliza caché ni valores alternos.
    """
    normalized_target = normalize_system_type(
        target_system
    )

    if normalized_target not in _SUPPORTED_SYNC_SYSTEMS:
        raise ValueError(
            "Sistema financiero de sincronización "
            f"no soportado: {target_system!r}"
        )

    try:
        rows = fetch_all_dict_readonly(
            _CANONICAL_UNITS_SQL
        )
    except Exception as exc:
        raise FinanzasCanonicalUnitError(
            "No fue posible leer el catálogo "
            "canónico de unidades financieras"
        ) from exc

    result = []

    for row in rows or ():
        effective_type = _effective_system_type(
            row
        )

        if effective_type != normalized_target:
            continue

        unit_pk = _clean(
            row.get("unidad_negocio_pk")
        )
        unit_code = _clean(
            row.get("unidad_negocio_codigo")
        )
        unit_name = _clean(
            row.get("unidad_negocio_nombre")
        )
        server_id = _clean(
            row.get("server_id")
        )
        branch = _clean(
            row.get("sucursal_origen_id")
        )

        missing = [
            name
            for name, value in (
                ("unidad_negocio_pk", unit_pk),
                ("unidad_negocio_codigo", unit_code),
                ("unidad_negocio_nombre", unit_name),
                ("server_id", server_id),
            )
            if not value
        ]

        if missing:
            raise FinanzasCanonicalUnitError(
                "Unidad financiera canónica "
                "incompleta: "
                + ", ".join(missing)
            )

        if (
            normalized_target
            == SystemType.MANAGEMENTPRO.value
            and not branch
        ):
            raise FinanzasCanonicalUnitError(
                "Unidad MPRO sin "
                "sucursal_origen_id canónica: "
                f"{unit_code}"
            )

        result.append(
            {
                "unidad_negocio_pk": unit_pk,
                "unidad_negocio_codigo": unit_code,
                "unidad_negocio_nombre": unit_name,
                "server_id": server_id,
                "sucursal_origen_id": (
                    branch or None
                ),
                "system_type": effective_type,
            }
        )

    if not result:
        raise FinanzasCanonicalUnitError(
            "El catálogo canónico no contiene "
            "unidades activas para "
            f"{normalized_target}"
        )

    identifiers = set()

    for unit in result:
        key = unit["unidad_negocio_pk"].casefold()

        if key in identifiers:
            raise FinanzasCanonicalUnitError(
                "Unidad financiera canónica "
                "duplicada: "
                + unit["unidad_negocio_pk"]
            )

        identifiers.add(key)

    return tuple(result)


def get_canonical_finance_sync_unit_names(
    target_system: str,
) -> Tuple[str, ...]:
    """
    Retorna nombres canónicos, preservando la interfaz
    histórica de los cuatro sincronizadores financieros.
    """
    return tuple(
        unit["unidad_negocio_nombre"]
        for unit in get_canonical_finance_sync_units(
            target_system
        )
    )


__all__ = [
    "FinanzasCanonicalUnitError",
    "get_canonical_finance_sync_units",
    "get_canonical_finance_sync_unit_names",
]
