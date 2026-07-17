"""Alcance RBAC fail-closed para Finanzas / Tesorería / Cortes Z."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Dict, Iterable, Mapping

from fastapi import HTTPException, status

from core.rbac_sql.service import RBACSQLService
from core.sql_first.db import fetch_all_dict_readonly
from core.system_type_utils import normalize_system_type


logger = logging.getLogger(__name__)

# Códigos canónicos producidos por AuthRepository desde dbo.Usuario_Roles.
# La ausencia o cualquier código distinto falla como alcance limitado.
TES_CUADRES_Z_MODULE_CODE = "TES_CUADRES_Z"
TES_CUADRES_Z_VER = f"{TES_CUADRES_Z_MODULE_CODE}_VER"
TES_CUADRES_Z_CREAR = f"{TES_CUADRES_Z_MODULE_CODE}_CREAR"
TES_CUADRES_Z_EDITAR = f"{TES_CUADRES_Z_MODULE_CODE}_EDITAR"
TES_CUADRES_Z_ELIMINAR = f"{TES_CUADRES_Z_MODULE_CODE}_ELIMINAR"
TES_CUADRES_Z_VALIDAR = f"{TES_CUADRES_Z_MODULE_CODE}_VALIDAR"

TES_CUADRES_Z_PERMISSION_CODES = frozenset(
    {
        TES_CUADRES_Z_VER,
        TES_CUADRES_Z_CREAR,
        TES_CUADRES_Z_EDITAR,
        TES_CUADRES_Z_ELIMINAR,
        TES_CUADRES_Z_VALIDAR,
    }
)


def _resolve_usuario_id(
    current_user: Mapping[str, Any],
) -> Any:
    return (
        current_user.get("_sql_usuario_id")
        or current_user.get("UsuarioID")
        or current_user.get("usuario_id")
    )


def _coerce_rbac_flag(
    value: Any,
    field_name: str,
) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, int) and value in (0, 1):
        return bool(value)

    raise TesoreriaAccessResolutionError(
        f"El campo RBAC {field_name} tiene un valor inválido."
    )


def _resolve_permission_scope(
    current_user: Mapping[str, Any],
    permission_code: str = TES_CUADRES_Z_VER,
) -> Dict[str, Any]:
    normalized = str(
        permission_code or ""
    ).strip().upper()

    if normalized not in TES_CUADRES_Z_PERMISSION_CODES:
        raise TesoreriaAccessResolutionError(
            "Permiso funcional fuera del contrato de Cuadres Z."
        )

    usuario_id = _resolve_usuario_id(current_user)

    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "No existe identidad SQL canónica para evaluar "
                "el permiso de Tesorería."
            ),
        )

    try:
        raw_scope = (
            RBACSQLService.get_permission_scope_by_code(
                usuario_id,
                normalized,
            )
        )
    except Exception as exc:
        raise TesoreriaAccessResolutionError(
            "No fue posible resolver el permiso funcional "
            "de Tesorería."
        ) from exc

    if raw_scope is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "El usuario no tiene el permiso funcional "
                f"requerido: {normalized}."
            ),
        )

    if not isinstance(raw_scope, Mapping):
        raise TesoreriaAccessResolutionError(
            "El permiso funcional de Tesorería tiene "
            "un formato inválido."
        )

    if "permitido" not in raw_scope:
        raise TesoreriaAccessResolutionError(
            "El permiso funcional no contiene permitido."
        )

    if "restriccion_sucursal" not in raw_scope:
        raise TesoreriaAccessResolutionError(
            "El permiso funcional no contiene "
            "restriccion_sucursal."
        )

    permitido = _coerce_rbac_flag(
        raw_scope.get("permitido"),
        "permitido",
    )

    restricted = _coerce_rbac_flag(
        raw_scope.get("restriccion_sucursal"),
        "restriccion_sucursal",
    )

    if not permitido:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "El usuario no tiene el permiso funcional "
                f"requerido: {normalized}."
            ),
        )

    scope = dict(raw_scope)
    scope["permission_code"] = normalized
    scope["permitido"] = True
    scope["restriccion_sucursal"] = restricted

    return scope


def _has_global_access(
    current_user: Mapping[str, Any],
    permission_code: str = TES_CUADRES_Z_VER,
) -> bool:
    """Resuelve alcance global desde el permiso funcional SQL."""
    permission_scope = _resolve_permission_scope(
        current_user,
        permission_code,
    )

    return not permission_scope["restriccion_sucursal"]


_TESORERIA_SYSTEM_TYPES = {
    "SOFTRESTAURANT",
    "MANAGEMENTPRO",
}


class TesoreriaAccessResolutionError(RuntimeError):
    """No fue posible resolver de forma confiable el alcance RBAC."""


def _normalize(value: Any) -> str:
    return str(value or "").strip().casefold()


def _extract_values(
    rows: Iterable[Mapping[str, Any]],
    field: str,
) -> frozenset[str]:
    return frozenset(
        normalized
        for row in rows or ()
        if (normalized := _normalize(row.get(field)))
    )


@dataclass(frozen=True)
class TesoreriaUnit:
    unidad_negocio_pk: str
    unidad_negocio_codigo: str
    unidad_negocio_nombre: str
    empresa_id: str
    server_id: str
    sucursal_origen_id: str
    system_type: str
    active_units_on_server: int

    @property
    def identifiers(self) -> frozenset[str]:
        """Identificadores exactos de unidad.

        Empresa y servidor se excluyen deliberadamente porque pueden
        representar varias unidades de negocio.
        """
        return frozenset(
            normalized
            for value in (
                self.unidad_negocio_pk,
                self.unidad_negocio_codigo,
                self.unidad_negocio_nombre,
                self.sucursal_origen_id,
            )
            if (normalized := _normalize(value))
        )

    @property
    def branch_key(self) -> tuple[str, str]:
        return (
            _normalize(self.server_id),
            _normalize(self.sucursal_origen_id),
        )

    def matches_identifier(self, value: Any) -> bool:
        return _normalize(value) in self.identifiers

    def matches_server_id(self, value: Any) -> bool:
        return _normalize(value) == _normalize(self.server_id)

    def matches_unit_identifier(self, value: Any) -> bool:
        normalized = _normalize(value)
        return normalized in {
            _normalize(self.unidad_negocio_pk),
            _normalize(self.unidad_negocio_codigo),
            _normalize(self.unidad_negocio_nombre),
            _normalize(self.sucursal_origen_id),
        }

    def to_frontend_dict(self) -> Dict[str, Any]:
        fuente = (
            "SOFTRESTAURANT"
            if self.system_type == "SOFTRESTAURANT"
            else "MPRO"
        )

        return {
            "id": self.unidad_negocio_pk,
            "server_id": self.server_id,
            "unidad_negocio_pk": self.unidad_negocio_pk,
            "codigo": self.unidad_negocio_codigo,
            "nombre": self.unidad_negocio_nombre,
            "empresa_id": self.empresa_id or None,
            "sucursal_origen_id": self.sucursal_origen_id or None,
            "fuente": fuente,
            "system_type": self.system_type,
            "activo": True,
        }


@dataclass(frozen=True)
class TesoreriaAccessScope:
    global_access: bool
    units: tuple[TesoreriaUnit, ...]

    @property
    def unit_ids(self) -> frozenset[str]:
        return frozenset(
            unit.unidad_negocio_pk
            for unit in self.units
            if unit.unidad_negocio_pk
        )

    def ensure_any_access(self) -> None:
        if not self.global_access and not self.units:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario no tiene unidades autorizadas para Tesorería.",
            )

    def require_server_id(
        self,
        server_id: Any,
    ) -> None:
        """Autoriza un servidor sin elegir una unidad arbitraria."""
        matches = [
            unit
            for unit in self.units
            if unit.matches_server_id(server_id)
        ]

        if not matches:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "El servidor solicitado no pertenece al "
                    "alcance efectivo del usuario."
                ),
            )

        topology_counts = {
            unit.active_units_on_server
            for unit in matches
        }

        if len(topology_counts) != 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "La topología canónica del servidor es "
                    "inconsistente."
                ),
            )

        expected_units = next(iter(topology_counts))

        if len(matches) != expected_units:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "El servidor contiene varias unidades y el "
                    "usuario no tiene alcance sobre todas ellas. "
                    "Debe seleccionar una unidad exacta."
                ),
            )

        return None

    def require_unit_identifier(
        self,
        identifier: Any,
    ) -> TesoreriaUnit:
        for unit in self.units:
            if unit.matches_unit_identifier(identifier):
                return unit

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La unidad solicitada no pertenece al alcance efectivo del usuario.",
        )

    def match_record(
        self,
        record: Mapping[str, Any],
    ) -> TesoreriaUnit | None:
        """Resuelve un registro usando identidad exacta de unidad.

        Nunca autoriza por empresa. Un server_id solo puede resolver un
        registro cuando la topología contiene exactamente una unidad.
        """

        unit_candidates = tuple(
            normalized
            for value in (
                record.get("unidad_negocio_pk"),
                record.get("unidad_negocio_id"),
                record.get("unidad_negocio_codigo"),
                record.get("unidad_negocio_nombre"),
                record.get("sucursal_id"),
                record.get("sucursal_codigo"),
                record.get("sucursal_nombre"),
                record.get("sucursal_origen_id"),
            )
            if (normalized := _normalize(value))
        )

        for candidate in unit_candidates:
            matches = [
                unit
                for unit in self.units
                if candidate in unit.identifiers
            ]

            if len(matches) == 1:
                return matches[0]

            if len(matches) > 1:
                return None

        server_candidates = tuple(
            normalized
            for value in (
                record.get("server_id"),
                record.get("sucursal_id"),
            )
            if (normalized := _normalize(value))
        )

        for candidate in server_candidates:
            matches = [
                unit
                for unit in self.units
                if unit.matches_server_id(candidate)
            ]

            if (
                len(matches) == 1
                and matches[0].active_units_on_server == 1
            ):
                return matches[0]

        return None

    def require_record(
        self,
        record: Mapping[str, Any],
    ) -> TesoreriaUnit:
        unit = self.match_record(record)

        if unit is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El registro solicitado no pertenece al alcance efectivo del usuario.",
            )

        return unit

    def filter_records(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> list[Dict[str, Any]]:
        return [
            dict(record)
            for record in records or ()
            if self.match_record(record) is not None
        ]

    def to_sucursales(self) -> list[Dict[str, Any]]:
        return [
            unit.to_frontend_dict()
            for unit in sorted(
                self.units,
                key=lambda item: (
                    item.unidad_negocio_codigo,
                    item.unidad_negocio_nombre,
                ),
            )
        ]


def _load_canonical_units() -> tuple[TesoreriaUnit, ...]:
    rows = fetch_all_dict_readonly(
        """
        SELECT
            CONVERT(NVARCHAR(100), u.id) AS unidad_negocio_pk,
            u.codigo AS unidad_negocio_codigo,
            u.nombre AS unidad_negocio_nombre,
            CONVERT(NVARCHAR(100), s.empresa_id) AS empresa_id,
            CONVERT(NVARCHAR(100), u.server_id) AS server_id,
            CONVERT(NVARCHAR(100), u.sucursal_origen_id)
                AS sucursal_origen_id,
            s.system_type,
            COUNT_BIG(*) OVER (
                PARTITION BY u.server_id
            ) AS active_units_on_server
        FROM dbo.Unidades_Negocio AS u
        INNER JOIN dbo.Servidores_Conexiones AS s
            ON s.id = u.server_id
        WHERE u.activo = 1
          AND s.activo = 1
        ORDER BY u.orden, u.codigo
        """
    )

    units: list[TesoreriaUnit] = []

    for row in rows:
        system_type = normalize_system_type(row.get("system_type"))

        if system_type not in _TESORERIA_SYSTEM_TYPES:
            continue

        unit = TesoreriaUnit(
            unidad_negocio_pk=str(
                row.get("unidad_negocio_pk") or ""
            ).strip(),
            unidad_negocio_codigo=str(
                row.get("unidad_negocio_codigo") or ""
            ).strip().upper(),
            unidad_negocio_nombre=str(
                row.get("unidad_negocio_nombre") or ""
            ).strip(),
            empresa_id=str(
                row.get("empresa_id") or ""
            ).strip(),
            server_id=str(
                row.get("server_id") or ""
            ).strip(),
            sucursal_origen_id=str(
                row.get("sucursal_origen_id") or ""
            ).strip(),
            system_type=system_type,
            active_units_on_server=int(
                row.get("active_units_on_server") or 0
            ),
        )

        missing = [
            name
            for name, value in (
                ("unidad_negocio_pk", unit.unidad_negocio_pk),
                ("unidad_negocio_codigo", unit.unidad_negocio_codigo),
                ("unidad_negocio_nombre", unit.unidad_negocio_nombre),
                ("server_id", unit.server_id),
            )
            if not value
        ]

        if missing:
            raise TesoreriaAccessResolutionError(
                "Catálogo canónico de Tesorería incompleto: "
                + ", ".join(missing)
            )

        if unit.active_units_on_server < 1:
            raise TesoreriaAccessResolutionError(
                "Topología canónica inválida para "
                f"{unit.unidad_negocio_codigo}."
            )

        units.append(unit)

    return tuple(units)


def _resolve_limited_units(
    catalog: tuple[TesoreriaUnit, ...],
    context: Mapping[str, Any],
) -> tuple[TesoreriaUnit, ...]:
    company_ids = _extract_values(
        context.get("empresas") or (),
        "EmpresaID",
    )
    server_ids = _extract_values(
        context.get("servidores") or (),
        "ServidorID",
    )
    unit_ids = _extract_values(
        context.get("unidades_negocio") or (),
        "UnidadNegocioID",
    )

    branch_keys = frozenset(
        (
            _normalize(row.get("ServidorID")),
            _normalize(row.get("SucursalCodigo")),
        )
        for row in context.get("sucursales") or ()
        if _normalize(row.get("ServidorID"))
        and _normalize(row.get("SucursalCodigo"))
    )

    allowed: list[TesoreriaUnit] = []

    for unit in catalog:
        unit_id = _normalize(unit.unidad_negocio_pk)
        company_id = _normalize(unit.empresa_id)
        server_id = _normalize(unit.server_id)

        allowed_by_unit = unit_id in unit_ids
        allowed_by_company = (
            bool(company_id)
            and company_id in company_ids
        )
        allowed_by_branch = (
            bool(unit.sucursal_origen_id)
            and unit.branch_key in branch_keys
        )
        allowed_by_server = (
            server_id in server_ids
            and unit.active_units_on_server == 1
        )

        if (
            allowed_by_unit
            or allowed_by_company
            or allowed_by_branch
            or allowed_by_server
        ):
            allowed.append(unit)

    return tuple(allowed)


def resolve_tesoreria_access_scope(
    current_user: Mapping[str, Any],
    permission_code: str = TES_CUADRES_Z_VER,
) -> TesoreriaAccessScope:
    if not isinstance(current_user, Mapping):
        raise TesoreriaAccessResolutionError(
            "El usuario autenticado tiene un formato inválido."
        )

    global_access = _has_global_access(
        current_user,
        permission_code,
    )

    try:
        catalog = _load_canonical_units()
    except TesoreriaAccessResolutionError:
        raise
    except Exception as exc:
        raise TesoreriaAccessResolutionError(
            "No fue posible resolver el catálogo canónico "
            "de Tesorería."
        ) from exc

    if not catalog:
        raise TesoreriaAccessResolutionError(
            "No existen unidades canónicas activas "
            "para Tesorería."
        )

    if global_access:
        return TesoreriaAccessScope(
            global_access=True,
            units=catalog,
        )

    usuario_id = _resolve_usuario_id(current_user)

    try:
        context = RBACSQLService.build_context(usuario_id)
    except Exception as exc:
        raise TesoreriaAccessResolutionError(
            "No fue posible resolver el alcance RBAC "
            "de Tesorería."
        ) from exc

    if not isinstance(context, Mapping):
        raise TesoreriaAccessResolutionError(
            "El contexto RBAC de Tesorería es inválido."
        )

    return TesoreriaAccessScope(
        global_access=False,
        units=_resolve_limited_units(
            catalog,
            context,
        ),
    )


def require_tesoreria_access_scope(
    current_user: Mapping[str, Any],
    permission_code: str = TES_CUADRES_Z_VER,
) -> TesoreriaAccessScope:
    try:
        scope = resolve_tesoreria_access_scope(
            current_user,
            permission_code,
        )
        scope.ensure_any_access()
        return scope
    except HTTPException:
        raise
    except TesoreriaAccessResolutionError as exc:
        logger.error(
            "[TESORERIA_RBAC] Resolución fail-closed: %s",
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No fue posible resolver los permisos de "
                "Tesorería. El acceso fue cerrado "
                "preventivamente."
            ),
        ) from exc


__all__ = [
    "TesoreriaAccessResolutionError",
    "TesoreriaAccessScope",
    "TesoreriaUnit",
    "require_tesoreria_access_scope",
    "resolve_tesoreria_access_scope",
]
