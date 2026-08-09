"""
Decoder genérico de respuestas HTTP para el dominio Economía.

Responsabilidad única:
- convertir payload HTTP JSON o XML a estructuras Python;
- no conoce proveedores;
- no conoce series;
- no conoce endpoints;
- no persiste datos;
- no realiza HTTP.

El normalizador canónico de Economía trabaja posteriormente sobre
la estructura Python resultante.
"""

from __future__ import annotations

from typing import Any
import xml.etree.ElementTree as ET


SUPPORTED_RESPONSE_FORMATS = frozenset({"json", "xml"})


def _strip_namespace(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _xml_element_to_python(element: ET.Element) -> Any:
    """
    Convierte un elemento XML a una estructura Python determinista.

    Reglas:
    - hoja sin atributos -> texto;
    - atributos -> claves prefijadas con "@";
    - texto mezclado con atributos/hijos -> "#text";
    - hijos repetidos -> lista;
    - hijo único -> valor directo.
    """
    children = list(element)

    result: dict[str, Any] = {
        f"@{_strip_namespace(key)}": value
        for key, value in element.attrib.items()
    }

    text = (element.text or "").strip()

    if not children:
        if not result:
            return text

        if text:
            result["#text"] = text

        return result

    grouped: dict[str, list[Any]] = {}

    for child in children:
        key = _strip_namespace(child.tag)
        grouped.setdefault(key, []).append(
            _xml_element_to_python(child)
        )

    for key, values in grouped.items():
        result[key] = (
            values[0]
            if len(values) == 1
            else values
        )

    if text:
        result["#text"] = text

    return result


def decode_xml_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, bytes):
        if not payload:
            raise ValueError("respuesta XML vacía")
        source = payload

    elif isinstance(payload, str):
        if not payload.strip():
            raise ValueError("respuesta XML vacía")
        source = payload

    else:
        raise ValueError(
            "respuesta XML debe ser bytes o texto"
        )

    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        raise ValueError("respuesta XML inválida") from exc

    root_name = _strip_namespace(root.tag)

    if not root_name:
        raise ValueError("respuesta XML sin elemento raíz")

    return {
        root_name: _xml_element_to_python(root)
    }


def decode_xml_text(text: str) -> dict[str, Any]:
    """
    Compatibilidad con callers existentes.
    """
    return decode_xml_payload(text)


def decode_http_response(
    response: Any,
    response_format: str,
) -> Any:
    fmt = str(response_format or "").strip().lower()

    if fmt not in SUPPORTED_RESPONSE_FORMATS:
        raise ValueError(
            f"response_format no soportado: {fmt or '<vacío>'}"
        )

    if fmt == "json":
        return response.json()

    return decode_xml_payload(response.content)
