"""
Emergent Object Storage helper (EDARSA HUB)
===========================================
Archiva archivos (adjuntos de ingesta, etc.) en el object storage de Emergent.
Usa EMERGENT_LLM_KEY. La referencia/metadata se guarda en SQL (fuente de verdad),
NO en MongoDB. No hay API de borrado: el borrado es logico en SQL.
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "edarsa-hub"

_storage_key = None


def _emergent_key() -> str:
    key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not key:
        raise RuntimeError("EMERGENT_LLM_KEY no configurada en .env")
    return key


def init_storage(force: bool = False) -> str:
    """Inicializa (una vez por proceso) y retorna un storage_key reutilizable."""
    global _storage_key
    if _storage_key and not force:
        return _storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": _emergent_key()}, timeout=30)
    resp.raise_for_status()
    _storage_key = resp.json()["storage_key"]
    logger.info("[OBJSTORE] storage inicializado")
    return _storage_key


def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Sube un archivo. Retorna {'path','size','etag'}. Reintenta init si 403."""
    key = init_storage()
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120,
    )
    if resp.status_code == 403:
        key = init_storage(force=True)
        resp = requests.put(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key, "Content-Type": content_type},
            data=data, timeout=120,
        )
    resp.raise_for_status()
    return resp.json()


def get_object(path: str):
    """Descarga un archivo. Retorna (bytes, content_type)."""
    key = init_storage()
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60,
    )
    if resp.status_code == 403:
        key = init_storage(force=True)
        resp = requests.get(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key}, timeout=60,
        )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")
