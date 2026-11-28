from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AttributionTransactionRequest(BaseModel):
    server_id: str
    agent_id: Optional[str] = None
    source_transaction_uuid: str = Field(min_length=1, max_length=200)
    source_system: str = Field(min_length=1, max_length=50)
    occurred_at_utc: datetime
    unit_source_id: str = Field(min_length=1, max_length=100)

    cliente_id: Optional[int] = None
    commercial_system: Optional[str] = Field(default=None, max_length=40)
    native_transaction_id: Optional[str] = Field(default=None, max_length=128)
    native_ticket_number: Optional[str] = Field(default=None, max_length=128)
    native_folio: Optional[str] = Field(default=None, max_length=200)
    payload_hash: Optional[str] = Field(default=None, max_length=64)


class AttributionTransactionResponse(BaseModel):
    status: str
    source_key: str
    attributed: bool
    event_id: Optional[int] = None
    fecha_operacion: Optional[str] = None
    message: Optional[str] = None
