from __future__ import annotations

from datetime import date
from abc import ABC, abstractmethod


class AdquirenteConnectorBase(ABC):
    @abstractmethod
    async def obtener_transacciones(self, fecha_desde: date, fecha_hasta: date, unidad_negocio_id: int):
        raise NotImplementedError

    @abstractmethod
    async def obtener_depositos(self, fecha_desde: date, fecha_hasta: date, unidad_negocio_id: int):
        raise NotImplementedError

    @abstractmethod
    async def obtener_comisiones(self, fecha_desde: date, fecha_hasta: date, unidad_negocio_id: int):
        raise NotImplementedError

    @abstractmethod
    async def guardar_payload_original(self, payload, metadata: dict):
        raise NotImplementedError


class NetPayApiConnectorStub(AdquirenteConnectorBase):
    """Stub listo para API administrativa futura NetPay.

    No tiene funcionalidad productiva porque no hay documentación pública confirmada para reportes administrativos.
    """

    async def obtener_transacciones(self, fecha_desde: date, fecha_hasta: date, unidad_negocio_id: int):
        raise NotImplementedError('NetPay API administrativa no configurada.')

    async def obtener_depositos(self, fecha_desde: date, fecha_hasta: date, unidad_negocio_id: int):
        raise NotImplementedError('NetPay API administrativa no configurada.')

    async def obtener_comisiones(self, fecha_desde: date, fecha_hasta: date, unidad_negocio_id: int):
        raise NotImplementedError('NetPay API administrativa no configurada.')

    async def guardar_payload_original(self, payload, metadata: dict):
        raise NotImplementedError('NetPay API administrativa no configurada.')
