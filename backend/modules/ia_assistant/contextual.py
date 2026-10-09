"""Contratos seguros para el Asistente IA contextual.

Este modulo no ejecuta SQL, no resuelve permisos y no acepta URLs/rutas.
Solo normaliza metadata de vista y valida acciones UI contra whitelists.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Mapping

MAX_CONTEXT_STRING = 500
MAX_CONTEXT_LIST = 50
MAX_ACTIONS = 4

VIEW_KEYS = {
    "modulo", "view_id", "titulo", "scope", "filtros", "periodo",
    "unidad_negocio", "seleccion", "columnas_visibles", "estado_vista",
}
ACTION_TYPES = {
    "APPLY_FILTERS", "CLEAR_FILTERS", "OPEN_VIEW", "EXPORT_FILE",
}
FILTER_KEYS = {
    "ventas_min", "ventas_max", "pax_min", "pax_max", "ticket_contiene",
}
VIEW_TYPES = {"table", "bar_chart", "line_chart", "kpi_cards"}
VIEW_DATASETS = {"tickets", "lines"}
EXPORT_FORMATS = {"xlsx", "txt", "pdf"}

_SENSITIVE_MARKERS = (
    "password", "passwd", "token", "api_key", "apikey", "secret",
    "credential", "authorization", "cookie", "connection",
)


def _safe_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower())


def _safe_value(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return None
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:MAX_CONTEXT_STRING]
    if isinstance(value, Mapping):
        result: Dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= MAX_CONTEXT_LIST:
                break
            normalized = _safe_key(key)
            if any(marker in normalized for marker in _SENSITIVE_MARKERS):
                continue
            result[str(key)[:80]] = _safe_value(item, depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        return [_safe_value(item, depth + 1) for item in list(value)[:MAX_CONTEXT_LIST]]
    return str(value)[:MAX_CONTEXT_STRING]


def normalize_view_context(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, Mapping):
        return {}
    result: Dict[str, Any] = {}
    for key in VIEW_KEYS:
        if key in raw:
            result[key] = _safe_value(raw.get(key))
    return result


def _dataset_descriptors(datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    for row in datasets or []:
        if not isinstance(row, Mapping):
            continue
        dataset_id = str(row.get("dataset_id") or "").strip()
        if not dataset_id:
            continue
        columns = [
            str(value)
            for value in row.get("columns") or []
            if str(value or "").strip()
        ][:50]
        result.append({
            "dataset_id": dataset_id,
            "title": str(row.get("title") or "")[:120],
            "source_operation_id": str(row.get("source_operation_id") or "")[:120],
            "columns": columns,
            "row_count": int(row.get("row_count") or 0),
            "source_policy": "EDARSAHUB_ONLY",
        })
    return result[:10]


def action_prompt(
    user_text: str,
    assistant_text: str,
    view_context: Mapping[str, Any],
    datasets: List[Dict[str, Any]] | None = None,
) -> str:
    visible = view_context.get("columnas_visibles") or []
    return (
        "SOLICITUD DEL USUARIO:\n"
        + str(user_text or "")[:4000]
        + "\n\nRESPUESTA DEL ASISTENTE:\n"
        + str(assistant_text or "")[:6000]
        + "\n\nCONTEXTO DE VISTA NO AUTORITATIVO:\n"
        + json.dumps(dict(view_context), ensure_ascii=False, default=str)[:8000]
        + "\n\nCOLUMNAS VISIBLES DECLARADAS:\n"
        + json.dumps(visible, ensure_ascii=False, default=str)[:3000]
        + "\n\nDATASETS AUTORIZADOS DE EDARSAHUB:\n"
        + json.dumps(_dataset_descriptors(datasets or []), ensure_ascii=False, default=str)[:6000]
    )


def _column_keys(view_context: Mapping[str, Any]) -> set[str]:
    keys: set[str] = set()
    for row in view_context.get("columnas_visibles") or []:
        if isinstance(row, Mapping):
            value = str(row.get("key") or "").strip()
        else:
            value = str(row or "").strip()
        if value:
            keys.add(value)
    return keys


def _dataset_map(
    datasets: List[Dict[str, Any]] | None,
) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for row in datasets or []:
        if not isinstance(row, Mapping):
            continue
        dataset_id = str(row.get("dataset_id") or "").strip()
        if dataset_id:
            result[dataset_id] = dict(row)
    return result


def _safe_filename(value: Any) -> str:
    cleaned = re.sub(
        r"[^A-Za-z0-9._ -]+",
        "_",
        str(value or "").strip(),
    ).strip(" ._")
    return (cleaned or "edarsahub_ia")[:80]


def validate_actions(
    payload: Any,
    view_context: Mapping[str, Any],
    datasets: List[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    rows = payload.get("actions") or []
    if not isinstance(rows, list):
        return []

    visible_columns = _column_keys(view_context)
    system_datasets = _dataset_map(datasets)
    result: List[Dict[str, Any]] = []

    for raw in rows[:MAX_ACTIONS]:
        if not isinstance(raw, Mapping):
            continue
        action_type = str(raw.get("type") or "").strip().upper()
        if action_type not in ACTION_TYPES:
            continue

        label = str(raw.get("label") or "").strip()[:80]
        if not label:
            label = {
                "APPLY_FILTERS": "Aplicar filtro",
                "CLEAR_FILTERS": "Limpiar filtros",
                "OPEN_VIEW": "Abrir vista",
                "EXPORT_FILE": "Exportar archivo",
            }[action_type]

        if action_type == "CLEAR_FILTERS":
            result.append({"type": action_type, "label": label, "payload": {}})
            continue

        data = raw.get("payload") or {}
        if not isinstance(data, Mapping):
            continue

        if action_type == "APPLY_FILTERS":
            filters = data.get("filters") or {}
            if not isinstance(filters, Mapping):
                continue
            safe_filters: Dict[str, Any] = {}
            for key, value in filters.items():
                key = str(key)
                if key not in FILTER_KEYS:
                    continue
                if key == "ticket_contiene":
                    safe_filters[key] = str(value or "")[:64]
                else:
                    try:
                        safe_filters[key] = float(value)
                    except (TypeError, ValueError):
                        continue
            if safe_filters:
                result.append({
                    "type": action_type,
                    "label": label,
                    "payload": {"filters": safe_filters},
                })
            continue

        dataset_id = str(data.get("dataset_id") or "").strip()
        view_dataset = str(data.get("dataset") or "").strip().lower()
        dataset_row = system_datasets.get(dataset_id) if dataset_id else None

        if dataset_row is not None:
            allowed_columns = {
                str(value)
                for value in dataset_row.get("columns") or []
                if str(value or "").strip()
            }
        elif view_dataset in VIEW_DATASETS:
            allowed_columns = visible_columns
        else:
            continue

        if action_type == "EXPORT_FILE":
            export_format = str(data.get("format") or "").strip().lower()
            if export_format not in EXPORT_FORMATS:
                continue
            payload_out: Dict[str, Any] = {
                "format": export_format,
                "filename": _safe_filename(
                    data.get("filename") or data.get("title") or "edarsahub_ia"
                ),
                "title": str(data.get("title") or "Análisis EDARSAHUB")[:120],
            }
            if dataset_row is not None:
                payload_out["dataset_id"] = dataset_id
            else:
                payload_out["dataset"] = view_dataset
            result.append({
                "type": action_type,
                "label": label,
                "payload": payload_out,
            })
            continue

        view_type = str(data.get("view_type") or "").strip().lower()
        if view_type not in VIEW_TYPES:
            continue

        payload_out = {
            "view_type": view_type,
            "title": str(data.get("title") or "Análisis IA")[:120],
        }
        if dataset_row is not None:
            payload_out["dataset_id"] = dataset_id
        else:
            payload_out["dataset"] = view_dataset

        for key in ("x_key", "y_key"):
            value = str(data.get(key) or "").strip()
            if value and value in allowed_columns:
                payload_out[key] = value

        result.append({
            "type": action_type,
            "label": label,
            "payload": payload_out,
        })

    return result


def parse_actions_response(
    raw: str,
    view_context: Mapping[str, Any],
    datasets: List[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    text = str(raw or "").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return []
    try:
        payload = json.loads(text[start:end + 1])
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return validate_actions(payload, view_context, datasets=datasets)
