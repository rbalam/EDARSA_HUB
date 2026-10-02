"""
Contrato del Universal Worker + intérprete de resultados (SOLO LECTURA).

- No escribe archivos.
- No ejecuta SQL.
- Valida el esquema edarsahub.worker-job.v2 en memoria.
- Interpreta results/done/published de forma tolerante.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path("/app")
REQUESTS_DIR = REPO_ROOT / "worker" / "requests"
QUEUE_ROOT = REPO_ROOT / ".git" / "universal-worker-queue"

# Estados del lifecycle (carpetas canónicas de la cola)
LIFECYCLE_STATES: List[str] = [
    "pending",
    "processing",
    "results",
    "done",
    "published",
    "rejected",
]

SCHEMA_ID = "edarsahub.worker-job.v2"
VALID_MODES = {"READ_ONLY", "MUTATION"}


def state_dir(state: str) -> Optional[Path]:
    """Devuelve el Path de una carpeta de estado válida, o None."""
    if state == "requests":
        return REQUESTS_DIR
    if state == "runtime":
        return QUEUE_ROOT / "runtime"
    if state in LIFECYCLE_STATES:
        return QUEUE_ROOT / state
    return None


def _safe_json(path: Path) -> Optional[Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def extract_job(doc: Any) -> Dict[str, Any]:
    """Un archivo puede ser el job directo o un envoltorio {'job': {...}}."""
    if isinstance(doc, dict) and isinstance(doc.get("job"), dict):
        return doc["job"]
    if isinstance(doc, dict):
        return doc
    return {}


def validate_job(doc: Any) -> Dict[str, Any]:
    """
    Valida el contrato edarsahub.worker-job.v2 SIN escribir nada.
    Retorna {valid, errors[], warnings[], normalized}.
    """
    errors: List[str] = []
    warnings: List[str] = []
    job = extract_job(doc)

    if job.get("schema") != SCHEMA_ID:
        errors.append(f"schema debe ser '{SCHEMA_ID}'")
    if not job.get("job_id"):
        errors.append("job_id es obligatorio")
    mode = job.get("mode")
    if mode not in VALID_MODES:
        errors.append(f"mode debe ser uno de {sorted(VALID_MODES)}")
    if not job.get("objective"):
        warnings.append("objective vacío")

    actions = job.get("actions", None)
    if mode == "READ_ONLY":
        if actions not in ([], None):
            errors.append("READ_ONLY debe tener actions=[] (sin mutaciones)")
    if job.get("production_allowed", False) is True:
        errors.append("production_allowed=true no está permitido (No tocar Producción)")

    tgt = job.get("target_branch")
    if tgt and str(tgt).lower() in {"main", "master", "produccion", "production", "prod"}:
        errors.append(f"target_branch '{tgt}' apunta a Producción (prohibido)")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "job_id": job.get("job_id"),
        "mode": mode,
        "schema": job.get("schema"),
    }


# Claves comunes en results (tolerante a variaciones de formato)
_CERT_KEYS = ["certification", "cert", "certified", "result", "status", "verdict"]
_GATE_KEYS = ["quality_gate", "gate", "go_no_go", "go_nogo", "release_gate"]
_BLOCKER_KEYS = ["blockers", "blocking", "errors", "failures", "issues"]
_PROD_KEYS = ["production_touched", "produccion_tocada", "prod_touched"]
_FILES_KEYS = ["files_changed", "changed_files", "files", "diff_files"]


def _first(d: Dict[str, Any], keys: List[str]) -> Tuple[Optional[str], Any]:
    for k in keys:
        if k in d:
            return k, d[k]
    return None, None


def interpret_result(doc: Any) -> Dict[str, Any]:
    """Interpreta un result de forma tolerante y produce un veredicto legible."""
    root = doc if isinstance(doc, dict) else {}
    # buscar en la raíz y en subllaves comunes
    candidates: List[Dict[str, Any]] = [root]
    for sub in ("result", "summary", "report", "outcome", "data"):
        if isinstance(root.get(sub), dict):
            candidates.append(root[sub])

    def scan(keys):
        for c in candidates:
            k, v = _first(c, keys)
            if k is not None:
                return v
        return None

    certification = scan(_CERT_KEYS)
    quality_gate = scan(_GATE_KEYS)
    blockers = scan(_BLOCKER_KEYS)
    production_touched = scan(_PROD_KEYS)
    files_changed = scan(_FILES_KEYS)

    if isinstance(blockers, list):
        blocker_count = len(blockers)
    elif blockers:
        blocker_count = 1
    else:
        blocker_count = 0

    if isinstance(files_changed, list):
        files_count = len(files_changed)
    elif isinstance(files_changed, int):
        files_count = files_changed
    else:
        files_count = None

    verdict_text = str(certification or quality_gate or "").upper()
    passed = any(w in verdict_text for w in ("PASS", "OK", "CERTIF", "GO", "SUCCESS", "APROB"))
    failed = any(w in verdict_text for w in ("FAIL", "BLOCK", "NO-GO", "NO_GO", "RECHAZ", "ERROR"))

    if failed or blocker_count > 0:
        verdict = "FAIL"
    elif passed:
        verdict = "PASS"
    else:
        verdict = "UNKNOWN"

    return {
        "verdict": verdict,
        "certification": certification,
        "quality_gate": quality_gate,
        "blockers": blockers,
        "blocker_count": blocker_count,
        "production_touched": production_touched,
        "files_changed_count": files_count,
        "job_id": root.get("job_id") or extract_job(root).get("job_id"),
    }


def _parse_marker(text: str) -> Optional[Dict[str, Any]]:
    """Los archivos de published/ son marcadores 'clave=valor' por línea."""
    out: Dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("{"):
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out or None


def read_json_file(path: Path) -> Optional[Any]:
    doc = _safe_json(path)
    if doc is not None:
        return doc
    # fallback: marcador clave=valor (published/)
    try:
        return _parse_marker(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None
