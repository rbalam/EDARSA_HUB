"""Application service for Production Quality / Foto Finish."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from core.rbac_sql.service import RBACSQLService
from core.utils.operational_window import get_operational_window

from .repository import ProductionQualityRepository


class ProductionQualityAccessDenied(Exception):
    pass


class ProductionQualityNotFound(Exception):
    pass


class ProductionQualityConflict(Exception):
    pass


class ProductionQualityService:
    def __init__(self, repository: ProductionQualityRepository | None = None):
        self.repository = repository or ProductionQualityRepository()

    def _usuario_id(self, current_user: dict) -> int:
        public_uuid = str(
            current_user.get("id")
            or current_user.get("usuario_id")
            or ""
        ).strip()

        if not public_uuid:
            raise ProductionQualityAccessDenied("USER_ID_MISSING")

        usuario_id = self.repository.resolve_usuario_id(public_uuid)

        if not usuario_id:
            raise ProductionQualityAccessDenied("CANONICAL_USER_NOT_FOUND")

        return usuario_id

    def _ensure_scope(
        self,
        current_user: dict,
        empresa_id: int,
        unidad_negocio_id: UUID,
    ) -> int:
        usuario_id = self._usuario_id(current_user)

        if not RBACSQLService.can_access_empresa(
            usuario_id,
            empresa_id,
        ):
            raise ProductionQualityAccessDenied(
                "EMPRESA_SCOPE_DENIED"
            )

        if not RBACSQLService.can_access_unidad(
            usuario_id,
            str(unidad_negocio_id),
        ):
            raise ProductionQualityAccessDenied(
                "UNIDAD_SCOPE_DENIED"
            )

        return usuario_id

    def _assert_item_scope(
        self,
        production_item_id: UUID,
        empresa_id: int,
        unidad_negocio_id: UUID,
    ) -> dict:
        item = self.repository.get_item_scope(
            production_item_id
        )

        if not item:
            raise ProductionQualityNotFound(
                "PRODUCTION_ITEM_NOT_FOUND"
            )

        if int(item["EmpresaID"]) != int(empresa_id):
            raise ProductionQualityAccessDenied(
                "ITEM_EMPRESA_SCOPE_MISMATCH"
            )

        if str(item["UnidadNegocioID"]).lower() != str(
            unidad_negocio_id
        ).lower():
            raise ProductionQualityAccessDenied(
                "ITEM_UNIDAD_SCOPE_MISMATCH"
            )

        return item

    def _fecha_operacion(self, unidad_negocio_id: UUID):
        window = get_operational_window(
            str(unidad_negocio_id)
        )
        return window.fecha_operacion

    def list_items(
        self,
        current_user: dict,
        empresa_id: int,
        unidad_negocio_id: UUID,
        limit: int,
        offset: int,
    ) -> list[dict]:
        self._ensure_scope(
            current_user,
            empresa_id,
            unidad_negocio_id,
        )

        return self.repository.list_items(
            empresa_id,
            unidad_negocio_id,
            self._fecha_operacion(unidad_negocio_id),
            limit,
            offset,
        )

    def list_standards(
        self,
        current_user: dict,
        empresa_id: int,
        unidad_negocio_id: UUID,
    ) -> list[dict]:
        self._ensure_scope(
            current_user,
            empresa_id,
            unidad_negocio_id,
        )

        return self.repository.list_standards(
            empresa_id,
            unidad_negocio_id,
        )

    def list_devices(
        self,
        current_user: dict,
        empresa_id: int,
        unidad_negocio_id: UUID,
    ) -> list[dict]:
        self._ensure_scope(
            current_user,
            empresa_id,
            unidad_negocio_id,
        )

        return self.repository.list_devices(
            empresa_id,
            unidad_negocio_id,
        )

    def create_measurement(
        self,
        current_user: dict,
        payload: dict,
    ) -> dict:
        usuario_id = self._ensure_scope(
            current_user,
            payload["empresa_id"],
            payload["unidad_negocio_id"],
        )

        self._assert_item_scope(
            payload["production_item_id"],
            payload["empresa_id"],
            payload["unidad_negocio_id"],
        )

        return self.repository.create_measurement(
            payload,
            usuario_id,
            self._fecha_operacion(
                payload["unidad_negocio_id"]
            ),
        )

    def create_evidence(
        self,
        current_user: dict,
        payload: dict,
    ) -> dict:
        usuario_id = self._ensure_scope(
            current_user,
            payload["empresa_id"],
            payload["unidad_negocio_id"],
        )

        self._assert_item_scope(
            payload["production_item_id"],
            payload["empresa_id"],
            payload["unidad_negocio_id"],
        )

        return self.repository.create_evidence(
            payload,
            usuario_id,
            self._fecha_operacion(
                payload["unidad_negocio_id"]
            ),
        )

    def create_decision(
        self,
        current_user: dict,
        payload: dict,
    ) -> dict:
        usuario_id = self._ensure_scope(
            current_user,
            payload["empresa_id"],
            payload["unidad_negocio_id"],
        )

        self._assert_item_scope(
            payload["production_item_id"],
            payload["empresa_id"],
            payload["unidad_negocio_id"],
        )

        return self.repository.create_decision(
            payload,
            usuario_id,
        )

    def create_action(
        self,
        current_user: dict,
        payload: dict,
    ) -> dict:
        usuario_id = self._ensure_scope(
            current_user,
            payload["empresa_id"],
            payload["unidad_negocio_id"],
        )

        self._assert_item_scope(
            payload["production_item_id"],
            payload["empresa_id"],
            payload["unidad_negocio_id"],
        )

        return self.repository.create_action(
            payload,
            usuario_id,
        )

    def create_calibration(
        self,
        current_user: dict,
        payload: dict,
    ) -> dict:
        usuario_id = self._ensure_scope(
            current_user,
            payload["empresa_id"],
            payload["unidad_negocio_id"],
        )

        return self.repository.create_calibration(
            payload,
            usuario_id,
        )
