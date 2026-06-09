"""
Regresión P0 (2026-06): migración de endpoints de Compras al contrato canónico `unidad`.

Valida la "puerta única" `canonical_server_id(token)` que traduce una unidad canónica
(codigo o pk) al server_id real del POS y preserva la compatibilidad legacy.

NO-LIVE: solo lee el catálogo canónico (dbo.Unidades_Negocio vía UnidadesService),
nunca conecta a POS.
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from core.corporate_filters.request_resolver import (  # noqa: E402
    canonical_server_id,
    resolve_unidad_simple,
)
from core.unidades_service import UnidadesService  # noqa: E402


def _alguna_unidad():
    for u in UnidadesService.get_all():
        if u.get("codigo") and u.get("server_id"):
            return u
    return None


def test_token_none_se_mantiene():
    assert canonical_server_id(None) is None


def test_token_desconocido_se_mantiene_legacy():
    # Comportamiento legacy preservado: aguas abajo dará 404 "Servidor no encontrado".
    assert canonical_server_id("__NO_EXISTE__") == "__NO_EXISTE__"


def test_unidad_codigo_resuelve_a_server_id():
    u = _alguna_unidad()
    assert u is not None, "El catálogo canónico debe exponer al menos una unidad"
    resuelto = canonical_server_id(u["codigo"])
    assert resuelto == u["server_id"]


def test_server_id_legacy_se_mantiene_igual():
    u = _alguna_unidad()
    assert u is not None
    # Un server_id ya real se devuelve intacto (compatibilidad limpia).
    assert canonical_server_id(u["server_id"]) == u["server_id"]


def test_resolve_unidad_simple_marca_origen():
    u = _alguna_unidad()
    assert u is not None
    _u, matched = resolve_unidad_simple(u["codigo"])
    assert matched == "unidad"
    _u2, matched2 = resolve_unidad_simple(u["server_id"])
    assert matched2 == "server"
    _u3, matched3 = resolve_unidad_simple("__NO_EXISTE__")
    assert matched3 == "none"


def test_mpro_unidades_comparten_server_id():
    # Caso MPRO: ORIGEN y 130QRO comparten el mismo server_id (host compartido).
    unidades = {u["codigo"]: u for u in UnidadesService.get_all() if u.get("codigo")}
    if "ORIGEN" in unidades and "130QRO" in unidades:
        assert canonical_server_id("ORIGEN") == canonical_server_id("130QRO")
