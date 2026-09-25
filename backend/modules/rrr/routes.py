from fastapi import APIRouter, Depends, HTTPException

from api.sync_receiver import get_agent_from_token, validate_server_id_match

from .attribution_service import (
    AttributionConflict,
    AttributionInvalidCommercial,
    AttributionInvalidCustomer,
    AttributionOrgScopeError,
    process_attribution,
)
from .schemas import AttributionTransactionRequest, AttributionTransactionResponse


router = APIRouter(prefix="/rrr/attribution", tags=["RRR Attribution"])


@router.post("/transactions", response_model=AttributionTransactionResponse)
async def receive_attribution_transaction(
    payload: AttributionTransactionRequest,
    agent=Depends(get_agent_from_token),
):
    validate_server_id_match(agent, payload.server_id)

    if payload.agent_id and payload.agent_id != agent.get("agent_id"):
        raise HTTPException(status_code=403, detail="agent_id mismatch")

    try:
        return process_attribution(payload)
    except AttributionInvalidCustomer as exc:
        raise HTTPException(status_code=422, detail={"status": "REJECTED_INVALID_CUSTOMER", "message": str(exc)})
    except AttributionInvalidCommercial as exc:
        raise HTTPException(status_code=422, detail={"status": "REJECTED_INVALID_COMMERCIAL", "message": str(exc)})
    except AttributionOrgScopeError as exc:
        raise HTTPException(status_code=422, detail={"status": "REJECTED_ORG_SCOPE", "message": str(exc)})
    except AttributionConflict as exc:
        raise HTTPException(status_code=409, detail={"status": "REJECTED_CONFLICT", "message": str(exc)})
