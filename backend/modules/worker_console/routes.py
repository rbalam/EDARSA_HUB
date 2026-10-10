"""
EDARSAHUB Universal Worker Console - API SOLO LECTURA (Fase 1).

Contrato de seguridad:
- No escribe archivos, no ejecuta SQL, no muta la cola ni Producción.
- Cualquier usuario autenticado puede consultar.
- (Fase 2, no incluida) publicar/limpiar requerirá SUPERADMIN.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.rbac.routes import get_current_user
from modules.worker_console import contract as C

router = APIRouter(prefix="/worker/console", tags=["worker-console"])


def _list_state(directory: Path) -> List[Path]:
    if not directory.exists():
        return []
    return [p for p in directory.iterdir() if p.is_file()]


def _job_id_from_name(name: str) -> str:
    # quitar extensiones .json / .json.raw_backup / etc.
    base = re.sub(r"\.(json)(\..*)?$", "", name, flags=re.IGNORECASE)
    return base


@router.get("/dashboard")
async def dashboard(current_user: dict = Depends(get_current_user)):
    """Conteos por estado + estado del runtime del worker."""
    states: Dict[str, int] = {}
    for st in ["requests"] + C.LIFECYCLE_STATES:
        d = C.state_dir(st)
        states[st] = len(_list_state(d)) if d else 0

    runtime_dir = C.QUEUE_ROOT / "runtime"

    def _read_txt(name: str) -> Optional[str]:
        p = runtime_dir / name
        try:
            return p.read_text(encoding="utf-8", errors="replace").strip() if p.exists() else None
        except Exception:
            return None

    control_plane = C.read_json_file(runtime_dir / "control_plane_status.json")
    reconciler = C.read_json_file(runtime_dir / "reconciler.json")
    orphaned = (runtime_dir / "orphaned-preferred").exists()
    preferred = C.read_json_file(runtime_dir / "preferred_job.json")

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "states": states,
        "runtime": {
            "current_job_id": _read_txt("current_job_id"),
            "generation": _read_txt("generation"),
            "last_cycle_utc": _read_txt("last_cycle_utc"),
            "last_receive_utc": _read_txt("last_receive_utc"),
            "last_terminal_utc": _read_txt("last_terminal_utc"),
            "control_plane_status": control_plane,
            "reconciler": reconciler,
            "preferred_job": preferred,
            "preferred_job_orphaned": orphaned,
        },
    }


@router.get("/jobs/{state}")
async def list_jobs(
    state: str,
    q: Optional[str] = Query(None, description="filtro por job_id"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Lista jobs de un estado (solo metadata: job_id, tamaño, fecha)."""
    d = C.state_dir(state)
    if d is None:
        raise HTTPException(status_code=400, detail="Estado no válido")
    files = _list_state(d)
    items = []
    for p in files:
        jid = _job_id_from_name(p.name)
        if q and q.lower() not in jid.lower():
            continue
        try:
            stt = p.stat()
            items.append({
                "job_id": jid,
                "file": p.name,
                "size": stt.st_size,
                "modified_utc": datetime.fromtimestamp(stt.st_mtime, timezone.utc).isoformat(),
            })
        except Exception:
            continue
    items.sort(key=lambda x: x["modified_utc"], reverse=True)
    return {"state": state, "total": len(items), "limit": limit, "offset": offset,
            "items": items[offset:offset + limit]}


def _find_in_state(state: str, job_id: str) -> Optional[Path]:
    d = C.state_dir(state)
    if d is None or not d.exists():
        return None
    for p in _list_state(d):
        if _job_id_from_name(p.name) == job_id:
            return p
    return None


@router.get("/lifecycle/{job_id}")
async def lifecycle(job_id: str, current_user: dict = Depends(get_current_user)):
    """Traza un job_id a través de todos los estados + interpreta su result."""
    presence = {}
    job_doc = None
    for st in ["requests"] + C.LIFECYCLE_STATES:
        p = _find_in_state(st, job_id)
        present = p is not None
        presence[st] = present
        if present and job_doc is None and st in ("requests", "pending", "processing"):
            doc = C.read_json_file(p)
            if doc is not None:
                job_doc = C.extract_job(doc)

    result_interp = None
    rp = _find_in_state("results", job_id) or _find_in_state("done", job_id) or _find_in_state("published", job_id)
    if rp is not None:
        doc = C.read_json_file(rp)
        if doc is not None:
            result_interp = C.interpret_result(doc)

    if not any(presence.values()):
        raise HTTPException(status_code=404, detail="job_id no encontrado en ningún estado")

    return {
        "job_id": job_id,
        "presence": presence,
        "job": job_doc,
        "result": result_interp,
    }


@router.get("/result/{job_id}")
async def result(job_id: str, current_user: dict = Depends(get_current_user)):
    """Intérprete de resultado de un job (results/done/published/rejected)."""
    for st in ("results", "done", "published", "rejected"):
        p = _find_in_state(st, job_id)
        if p is not None:
            doc = C.read_json_file(p)
            return {
                "job_id": job_id,
                "found_in": st,
                "interpretation": C.interpret_result(doc) if doc is not None else None,
                "raw": doc,
            }
    raise HTTPException(status_code=404, detail="Sin resultado para ese job_id")


@router.post("/validate")
async def validate(payload: dict, current_user: dict = Depends(get_current_user)):
    """Valida un job contra el contrato v2 SIN escribir nada (previo a Fase 2)."""
    return C.validate_job(payload)


# --- Caso Tablajerías: checklist precargado leyendo results reales ---
TABLAJERIAS_PATTERNS = [
    ("R24E certificado", r"TABLAJERIA.*R24E"),
    ("R24F certificado", r"TABLAJERIA.*R24F"),
    ("R24E+R24F compatibility", r"TABLAJERIA.*R24E.*R24F.*COMPAT|TABLAJERIA.*COMPAT.*R24"),
    ("Release Package Manifest R1B", r"TABLAJERIA.*(PACKAGE|MANIFEST).*R1B"),
    ("Release Patch Plan R1B", r"TABLAJERIA.*PATCH.*PLAN.*R1B"),
    ("Release Dry Run R1B", r"TABLAJERIA.*DRY.?RUN.*R1B"),
    ("Release Go/No-Go R1B", r"TABLAJERIA.*(GO.?NO.?GO|GO_NO_GO).*R1B"),
]


@router.get("/tablajerias/checklist")
async def tablajerias_checklist(current_user: dict = Depends(get_current_user)):
    """Checklist ejecutivo de cierre de Tablajerías, leyendo results reales."""
    # indexar results/done PRIMERO (JSON completo), luego published (marcador)
    index: Dict[str, Path] = {}
    for st in ("results", "done", "published"):
        d = C.state_dir(st)
        if d and d.exists():
            for p in _list_state(d):
                jid = _job_id_from_name(p.name)
                index.setdefault(jid.upper(), p)

    items = []
    all_pass = True
    prod_touched_any = False
    for label, pat in TABLAJERIAS_PATTERNS:
        rx = re.compile(pat, re.IGNORECASE)
        candidates = [jid for jid in index if rx.search(jid)]
        best = None  # (rank, jid, interp)
        for jid in candidates:
            doc = C.read_json_file(index[jid])
            interp = C.interpret_result(doc) if doc is not None else None
            if not interp:
                continue
            rank = {"PASS": 3, "FAIL": 2}.get(interp.get("verdict"), 1)
            if best is None or rank > best[0]:
                best = (rank, jid, interp)
        if best:
            match_jid, interp = best[1], best[2]
            verdict = interp["verdict"]
            pt = interp.get("production_touched")
            if pt is True:
                prod_touched_any = True
            if verdict != "PASS":
                all_pass = False
            items.append({
                "check": label,
                "job_id": match_jid,
                "verdict": verdict,
                "production_touched": pt,
                "blocker_count": interp.get("blocker_count"),
            })
        else:
            all_pass = False
            items.append({"check": label, "job_id": None, "verdict": "NOT_FOUND",
                          "production_touched": None, "blocker_count": None})

    return {
        "case": "Tablajerías",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "items": items,
        "all_pass": all_pass,
        "production_touched": prod_touched_any,
        "technical_status": "GO técnico READ_ONLY" if (all_pass and not prod_touched_any) else "PENDIENTE",
        "next_decision": "Autorización humana explícita antes de Producción",
        "note": "GO técnico READ_ONLY. NO es autorización automática para Producción. "
                "Requiere autorización humana explícita (Fase 2).",
    }


@router.get("/audit")
async def audit(tail: int = Query(80, ge=1, le=500), current_user: dict = Depends(get_current_user)):
    """Visor de evidencia/auditoría del runtime (solo lectura de logs existentes)."""
    runtime_dir = C.QUEUE_ROOT / "runtime"

    def _tail(name: str) -> List[str]:
        p = runtime_dir / name
        if not p.exists():
            return []
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            return lines[-tail:]
        except Exception:
            return []

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cert_log": _tail("universal-worker-cert.log"),
        "launch_log": _tail("universal-worker-launch.log"),
        "control_plane_status": C.read_json_file(runtime_dir / "control_plane_status.json"),
        "reconciler": C.read_json_file(runtime_dir / "reconciler.json"),
    }
