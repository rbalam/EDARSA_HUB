"""Endpoint machine-to-machine del Asistente IA para Universal Worker V2."""

from __future__ import annotations

import hmac
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from core.rbac_sql.service import RBACSQLService
from core.security import create_access_token
from modules.auth.repository import AuthRepository
from modules.ia_assistant import query_bridge
from modules.ia_assistant import repository
from modules.ia_assistant import service

IA_PERMISSION = "IA_ASSISTANT_VER"
WORKER_SOURCE = "universal_worker_v2"
AUTH_ERROR = (
    "No se pudo autenticar con el servicio configurado. "
    "Revisa las credenciales del entorno."
)
UNAVAILABLE_ERROR = (
    "El servicio de IA no está disponible temporalmente. "
    "Inténtalo de nuevo más tarde."
)
INCOMPLETE_ERROR = (
    "La respuesta recibida no contiene información suficiente "
    "para completar la solicitud."
)

router = APIRouter(prefix="/worker", tags=["Asistente IA - Worker"])


class WorkerContext(BaseModel):
    source: str = Field(..., min_length=1, max_length=64)
    user_id: str = Field(..., min_length=1, max_length=255)
    session_id: Optional[str] = Field(default=None, max_length=255)


class WorkerChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    context: WorkerContext


def _validate_worker_bearer(authorization: Optional[str]) -> None:
    expected = os.environ.get("EDARSA_AI_API_KEY", "").strip()
    header = str(authorization or "").strip()

    if not expected or not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail=AUTH_ERROR)

    candidate = header[7:].strip()
    if not candidate or not hmac.compare_digest(candidate, expected):
        raise HTTPException(status_code=401, detail=AUTH_ERROR)


def _resolve_user(identifier: str) -> dict:
    user_id = str(identifier or "").strip()
    user = AuthRepository.get_user_by_id(user_id)

    if not user and "@" in user_id:
        user = AuthRepository.get_user_by_email(user_id.lower())

    if not user or not bool(user.get("active")):
        raise HTTPException(status_code=403, detail="Usuario no autorizado")

    sql_user_id = user.get("_sql_usuario_id") or user.get("UsuarioID")
    if not sql_user_id:
        raise HTTPException(status_code=403, detail="Usuario no autorizado")

    if not RBACSQLService.can_access_permission(sql_user_id, IA_PERMISSION):
        raise HTTPException(status_code=403, detail="Usuario no autorizado")

    return user


def _resolve_session(user_email: str, requested_session_id: Optional[str]) -> str:
    if requested_session_id:
        try:
            normalized = str(UUID(str(requested_session_id).strip()))
        except (TypeError, ValueError):
            normalized = ""

        if normalized and repository.session_exists_for_user(normalized, user_email):
            return normalized

    session = service.crear_sesion(user_email, "Universal Worker V2")
    session_id = str(session.get("sesion_id") or "").strip()
    if not session_id:
        raise service.LLMProviderError("Sesión del Asistente IA no disponible")
    return session_id


@router.post("/chat")
async def worker_chat(
    payload: WorkerChatRequest,
    http_request: Request,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    _validate_worker_bearer(authorization)

    if payload.context.source.strip().lower() != WORKER_SOURCE:
        raise HTTPException(status_code=422, detail="Origen de solicitud no permitido")

    try:
        user = _resolve_user(payload.context.user_id)
        user_email = str(user.get("email") or "").strip().lower()
        if not user_email:
            raise HTTPException(status_code=403, detail="Usuario no autorizado")

        session_id = _resolve_session(user_email, payload.context.session_id)
        message = payload.message.strip()

        internal_token = create_access_token(
            str(user.get("id") or ""),
            user_email,
            str(user.get("role") or "Usuario"),
            token_type="internal",
        )

        catalog = query_bridge.build_readonly_catalog(http_request.app)
        prompt_catalog = query_bridge.catalog_for_prompt(catalog, message)
        planned = await service.plan_system_queries(
            session_id,
            message,
            prompt_catalog,
        )
        system_context = await query_bridge.execute_planned_queries(
            http_request.app,
            catalog,
            planned,
            authorization=f"Bearer {internal_token}",
        )

        result = await service.enviar_mensaje(
            session_id,
            user_email,
            message,
            system_context=system_context,
        )

    except HTTPException:
        raise
    except (
        repository.SchemaNotReadyError,
        service.LLMTimeoutError,
        service.LLMProviderError,
    ) as exc:
        raise HTTPException(status_code=503, detail=UNAVAILABLE_ERROR) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=UNAVAILABLE_ERROR) from exc

    answer = str(result.get("respuesta") or "").strip()
    if not answer:
        raise HTTPException(status_code=502, detail=INCOMPLETE_ERROR)

    return {
        "answer": answer,
        "session_id": session_id,
        "model": result.get("modelo"),
        "data_sources": result.get("data_sources") or [],
    }
