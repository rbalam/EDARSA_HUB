"""Servicio del Asistente IA SQL-first."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List

from modules.ia_assistant import repository

logger = logging.getLogger(__name__)

MODELO_IA = "gpt-5.5"
PROVEEDOR_IA = "openai"
LLM_TIMEOUT_SECONDS = 60

SYSTEM_PROMPT = """
Eres el Asistente IA interno de EDARSA HUB.
Responde de forma profesional, precisa y estructurada.
No inventes datos empresariales.
No generes ni ejecutes SQL.
No reveles secretos, credenciales ni configuración sensible.
Cuando falte información, indícalo expresamente.
""".strip()


class SessionNotFoundError(LookupError):
    """Sesión inexistente o perteneciente a otro usuario."""


class LLMTimeoutError(TimeoutError):
    """El proveedor no respondió dentro del límite."""


class LLMProviderError(RuntimeError):
    """Fallo controlado del proveedor LLM."""


def _api_key() -> str:
    key = os.environ.get(
        "EMERGENT_LLM_KEY",
        "",
    ).strip()

    if not key:
        raise LLMProviderError(
            "Proveedor IA no configurado"
        )

    return key


def crear_sesion(
    usuario_email: str,
    titulo: str | None = None,
) -> Dict[str, Any]:
    return repository.create_session(
        usuario_email=usuario_email,
        titulo=(
            titulo or "Nueva conversación"
        ),
        modelo=MODELO_IA,
    )


def listar_sesiones(
    usuario_email: str,
) -> List[Dict[str, Any]]:
    return repository.list_sessions(
        usuario_email
    )


def obtener_mensajes(
    sesion_id: str,
    usuario_email: str,
) -> List[Dict[str, Any]]:
    if not repository.session_exists_for_user(
        sesion_id,
        usuario_email,
    ):
        raise SessionNotFoundError(
            "Sesión no encontrada"
        )

    return repository.get_messages(
        sesion_id,
        usuario_email,
    )


def eliminar_sesion(
    sesion_id: str,
    usuario_email: str,
) -> bool:
    deleted = repository.deactivate_session(
        sesion_id,
        usuario_email,
    )

    if not deleted:
        raise SessionNotFoundError(
            "Sesión no encontrada"
        )

    return True


async def _send_llm(
    sesion_id: str,
    texto: str,
) -> str:
    from emergentintegrations.llm.chat import (
        LlmChat,
        UserMessage,
    )

    chat = LlmChat(
        api_key=_api_key(),
        session_id=sesion_id,
        system_message=SYSTEM_PROMPT,
    ).with_model(
        PROVEEDOR_IA,
        MODELO_IA,
    )

    try:
        raw_response = await asyncio.wait_for(
            chat.send_message(
                UserMessage(
                    text=texto
                )
            ),
            timeout=LLM_TIMEOUT_SECONDS,
        )

    except asyncio.TimeoutError as exc:
        raise LLMTimeoutError(
            "El proveedor IA excedió "
            "el tiempo límite"
        ) from exc

    except Exception as exc:
        logger.exception(
            "Fallo controlado "
            "del proveedor IA"
        )

        raise LLMProviderError(
            "El proveedor IA "
            "no está disponible"
        ) from exc

    if isinstance(
        raw_response,
        str,
    ):
        response = raw_response
    else:
        response = (
            getattr(
                raw_response,
                "text",
                None,
            )
            or getattr(
                raw_response,
                "content",
                None,
            )
            or str(
                raw_response or ""
            )
        )

    response = response.strip()

    if not response:
        raise LLMProviderError(
            "El proveedor IA devolvió "
            "una respuesta vacía"
        )

    return response


async def enviar_mensaje(
    sesion_id: str,
    usuario_email: str,
    texto: str,
) -> Dict[str, Any]:
    if not repository.session_exists_for_user(
        sesion_id,
        usuario_email,
    ):
        raise SessionNotFoundError(
            "Sesión no encontrada"
        )

    clean_text = str(
        texto or ""
    ).strip()

    if not clean_text:
        raise ValueError(
            "El mensaje no puede estar vacío"
        )

    response = await _send_llm(
        sesion_id,
        clean_text,
    )

    saved = repository.save_exchange(
        sesion_id=sesion_id,
        usuario_email=usuario_email,
        user_text=clean_text,
        assistant_text=response,
    )

    if not saved:
        raise SessionNotFoundError(
            "Sesión no encontrada"
        )

    return {
        "success": True,
        "sesion_id": sesion_id,
        "respuesta": response,
        "modelo": MODELO_IA,
    }


def health() -> Dict[str, Any]:
    schema = repository.schema_status()

    key_configured = bool(
        os.environ.get(
            "EMERGENT_LLM_KEY",
            "",
        ).strip()
    )

    ready = bool(
        schema.get("ready")
        and key_configured
    )

    return {
        "status": (
            "ok"
            if ready
            else "degraded"
        ),
        "modelo": MODELO_IA,
        "proveedor": (
            "OpenAI via EMERGENT_LLM_KEY"
        ),
        "key_configured": key_configured,
        "sql_schema": schema,
        "mongodb": False,
    }
