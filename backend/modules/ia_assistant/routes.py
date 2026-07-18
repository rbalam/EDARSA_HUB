"""Endpoints protegidos del Asistente IA."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel, Field

from core.rbac.middleware import (
    require_explicit_permission,
)
from modules.ia_assistant import repository
from modules.ia_assistant import service

IA_PERMISSION = "IA_ASSISTANT_VER"

router = APIRouter(
    prefix="/ia",
    tags=["Asistente IA"],
)


class CrearSesionRequest(BaseModel):
    titulo: Optional[str] = Field(
        default=None,
        max_length=300,
    )


class ChatRequest(BaseModel):
    sesion_id: UUID
    mensaje: str = Field(
        ...,
        min_length=1,
        max_length=8000,
    )


def _current_email(
    current_user: dict,
) -> str:
    email = str(
        current_user.get("email")
        or ""
    ).strip().lower()

    if not email:
        raise HTTPException(
            status_code=403,
            detail={
                "error": (
                    "IDENTIDAD_INCOMPLETA"
                ),
                "mensaje": (
                    "El usuario autenticado "
                    "no contiene una identidad "
                    "de email válida"
                ),
            },
        )

    return email


def _translate_error(
    exc: Exception,
) -> None:
    if isinstance(
        exc,
        service.SessionNotFoundError,
    ):
        raise HTTPException(
            status_code=404,
            detail="Sesión no encontrada",
        ) from exc

    if isinstance(
        exc,
        repository.SchemaNotReadyError,
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "El esquema SQL "
                "del Asistente IA "
                "no está disponible"
            ),
        ) from exc

    if isinstance(
        exc,
        service.LLMTimeoutError,
    ):
        raise HTTPException(
            status_code=504,
            detail=(
                "El proveedor IA excedió "
                "el tiempo límite"
            ),
        ) from exc

    if isinstance(
        exc,
        service.LLMProviderError,
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "El proveedor IA "
                "no está disponible"
            ),
        ) from exc

    if isinstance(
        exc,
        ValueError,
    ):
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("/health")
async def health(
    current_user: dict = Depends(
        require_explicit_permission(
            IA_PERMISSION
        )
    ),
):
    _current_email(current_user)
    return service.health()


@router.get("/sesiones")
async def listar_sesiones(
    current_user: dict = Depends(
        require_explicit_permission(
            IA_PERMISSION
        )
    ),
):
    try:
        return {
            "success": True,
            "sesiones": (
                service.listar_sesiones(
                    _current_email(
                        current_user
                    )
                )
            ),
        }

    except Exception as exc:
        _translate_error(exc)


@router.post("/sesiones")
async def crear_sesion(
    request: CrearSesionRequest,
    current_user: dict = Depends(
        require_explicit_permission(
            IA_PERMISSION
        )
    ),
):
    try:
        title = (
            request.titulo.strip()
            if request.titulo
            else None
        )

        sesion = service.crear_sesion(
            _current_email(
                current_user
            ),
            title,
        )

        return {
            "success": True,
            "sesion": sesion,
            **sesion,
        }

    except Exception as exc:
        _translate_error(exc)


@router.get(
    "/sesiones/{sesion_id}/mensajes"
)
async def obtener_mensajes(
    sesion_id: UUID,
    current_user: dict = Depends(
        require_explicit_permission(
            IA_PERMISSION
        )
    ),
):
    try:
        return {
            "success": True,
            "mensajes": (
                service.obtener_mensajes(
                    str(sesion_id),
                    _current_email(
                        current_user
                    ),
                )
            ),
        }

    except Exception as exc:
        _translate_error(exc)


@router.delete(
    "/sesiones/{sesion_id}"
)
async def eliminar_sesion(
    sesion_id: UUID,
    current_user: dict = Depends(
        require_explicit_permission(
            IA_PERMISSION
        )
    ),
):
    try:
        service.eliminar_sesion(
            str(sesion_id),
            _current_email(
                current_user
            ),
        )

        return {
            "success": True,
        }

    except Exception as exc:
        _translate_error(exc)


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(
        require_explicit_permission(
            IA_PERMISSION
        )
    ),
):
    try:
        message = (
            request.mensaje.strip()
        )

        if not message:
            raise ValueError(
                "El mensaje no puede "
                "estar vacío"
            )

        return await service.enviar_mensaje(
            str(request.sesion_id),
            _current_email(
                current_user
            ),
            message,
        )

    except Exception as exc:
        _translate_error(exc)
