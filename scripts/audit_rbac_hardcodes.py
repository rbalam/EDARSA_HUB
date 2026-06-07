#!/usr/bin/env python3
"""
Auditoría de hardcodes de rol en TODO el repo (backend + frontend).
SOLO LECTURA. Genera CSV priorizado por riesgo. No modifica código.

Riesgo:
- ALTO  : gate de acceso backend (if/elif/return/raise) por nombre legacy, o clave equivocada .get('rol').
- MEDIO : backend no-gate (display/filtro) o guard de ruta frontend por nombre legacy.
- BAJO  : tests, comentarios, strings de UI o sin contexto claro de rol.

NO marca como hardcode las comparaciones contra el CÓDIGO canónico ('SUPERADMIN', 'ADMIN', ...)
ni el uso de los helpers (get_role_code/es_admin/...), que son la forma correcta.
"""
import csv
import re
import sys
from pathlib import Path

ROOTS = [Path("/app/backend"), Path("/app/frontend/src")]
EXTS = {".py", ".js", ".jsx", ".ts", ".tsx"}
EXCLUDE = {"__pycache__", ".pytest_cache", "node_modules", "build", "dist", ".git"}
# Subcadenas de ruta que indican copias muertas (backups/auditorías), no código vivo
EXCLUDE_SUBSTR = ("auditorias_p4", "/backup", "backup_p", "_backup", "/backups/", ".before")

# Nombres legacy de display (lo que NO debe compararse a mano)
LEGACY_NAMES = [
    "SuperAdministrador", "Administrador", "Supervisor", "Usuario", "Visor", "Dirección",
]
ROLE_CTX = re.compile(r"\b(rol|role|user_role|userRole|perfil|current_user|user)\b", re.IGNORECASE)
WRONG_KEY = re.compile(r"""\.get\(\s*['"]rol['"]\s*\)""")
GATE_TOKENS = re.compile(r"^\s*(if|elif|return|raise|assert)\b|raise\s+HTTPException")
HELPER_OK = re.compile(r"\b(get_role_code|es_admin|es_superadmin|es_supervisor_o_superior|has_full_access)\b")


def legacy_hit(line: str):
    hits = []
    for name in LEGACY_NAMES:
        if f"'{name}'" in line or f'"{name}"' in line:
            hits.append(name)
    return hits


def classify(area, path, line, is_wrong_key, has_ctx, is_gate):
    s = str(path)
    if "/tests/" in s or s.endswith("_test.py") or "test_" in path.name:
        return "BAJO"
    stripped = line.strip()
    if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
        return "BAJO"
    if is_wrong_key:
        return "ALTO"
    if area == "backend":
        if is_gate and has_ctx:
            return "ALTO"
        if has_ctx:
            return "MEDIO"
        return "BAJO"
    # frontend
    if has_ctx:
        return "MEDIO"
    return "BAJO"


def main(out_csv):
    rows = []
    for root in ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_dir() or path.suffix not in EXTS:
                continue
            if any(part in EXCLUDE for part in path.parts):
                continue
            if any(sub in str(path) for sub in EXCLUDE_SUBSTR):
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except Exception:
                continue
            area = "frontend" if "/frontend/" in str(path) else "backend"
            for idx, line in enumerate(lines, 1):
                is_wrong_key = bool(WRONG_KEY.search(line))
                names = legacy_hit(line)
                if not is_wrong_key and not names:
                    continue
                has_ctx = bool(ROLE_CTX.search(line))
                is_gate = bool(GATE_TOKENS.search(line))
                uses_helper = bool(HELPER_OK.search(line))
                # Si la línea ya usa el helper canónico, no es hardcode a corregir
                if uses_helper and not names and not is_wrong_key:
                    continue
                riesgo = classify(area, path, line, is_wrong_key, has_ctx, is_gate)
                patrones = []
                if is_wrong_key:
                    patrones.append("get('rol') [clave-equivocada]")
                if names:
                    patrones.append("nombre_legacy:" + "|".join(names))
                rows.append({
                    "area": area,
                    "archivo": str(path).replace("/app/", ""),
                    "linea": idx,
                    "riesgo": riesgo,
                    "es_gate": "SI" if is_gate else "NO",
                    "contexto_rol": "SI" if has_ctx else "NO",
                    "usa_helper": "SI" if uses_helper else "NO",
                    "patron": ", ".join(patrones),
                    "codigo": line.strip()[:500],
                })

    orden = {"ALTO": 0, "MEDIO": 1, "BAJO": 2}
    rows.sort(key=lambda r: (orden[r["riesgo"]], r["area"], r["archivo"], r["linea"]))

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "area", "archivo", "linea", "riesgo", "es_gate",
            "contexto_rol", "usa_helper", "patron", "codigo"])
        w.writeheader()
        w.writerows(rows)

    tot = len(rows)
    alto = sum(1 for r in rows if r["riesgo"] == "ALTO")
    medio = sum(1 for r in rows if r["riesgo"] == "MEDIO")
    bajo = sum(1 for r in rows if r["riesgo"] == "BAJO")
    be = sum(1 for r in rows if r["area"] == "backend")
    fe = sum(1 for r in rows if r["area"] == "frontend")
    print(f"TOTAL={tot}  ALTO={alto}  MEDIO={medio}  BAJO={bajo}  backend={be}  frontend={fe}")
    print(f"CSV: {out_csv}")
    print("\nTop ALTO (gates backend / clave equivocada):")
    for r in [x for x in rows if x["riesgo"] == "ALTO"][:20]:
        print(f"  {r['archivo']}:{r['linea']}  {r['codigo'][:90]}")


if __name__ == "__main__":
    main(sys.argv[1])
