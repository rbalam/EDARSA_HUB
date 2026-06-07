"""Auditoría read-only de hardcodes de rol restantes (backend + frontend).
Genera un CSV con archivo, línea, riesgo, patrón y código. NO modifica nada."""
import csv
import sys
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/app/docs/reports/P0_RBAC_HARDCODES_RESTANTES.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

ROOTS = [Path("/app/backend"), Path("/app/frontend/src")]
EXCLUDE = {"__pycache__", ".pytest_cache", "node_modules", "build", "dist", ".git",
           "auditorias_p4", "auditorias_p5", "migrations", "backups"}
EXTS = {".py", ".js", ".jsx", ".ts", ".tsx"}

NOMBRES = ("SuperAdministrador", "Administrador", "Supervisor", "Usuario", "Visor")
CODIGOS = ("SUPERADMIN", "ADMIN", "SUPERVISOR", "USUARIO", "VISOR")
COMPARADORES = ("==", "!=", " in ", "not in")

rows = []
for root in ROOTS:
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if path.is_dir() or path.suffix not in EXTS:
            continue
        if any(part in EXCLUDE for part in path.parts):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for idx, line in enumerate(lines, start=1):
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("//") or s.startswith("*"):
                continue
            tiene_nombre = any(n in line for n in NOMBRES)
            tiene_codigo = any(c in line for c in CODIGOS)
            if not (tiene_nombre or tiene_codigo):
                continue
            tiene_comp = any(c in line for c in COMPARADORES)
            clave_rol_mala = "current_user.get('rol')" in line or 'current_user.get("rol")' in line
            if clave_rol_mala:
                riesgo = "ALTO"
            elif tiene_nombre and tiene_comp:
                riesgo = "ALTO"      # compara contra NombreRol legacy directamente
            elif tiene_codigo and tiene_comp:
                riesgo = "MEDIO"     # compara contra código canónico (más robusto)
            else:
                riesgo = "BAJO"      # mención sin comparación (seed/log/UI text)
            matches = [t for t in (NOMBRES + CODIGOS) if t in line]
            rows.append({
                "archivo": str(path),
                "linea": idx,
                "riesgo": riesgo,
                "patrones": ", ".join(matches),
                "codigo": s[:400],
            })

with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["archivo", "linea", "riesgo", "patrones", "codigo"])
    w.writeheader()
    w.writerows(rows)

alto = sum(1 for r in rows if r["riesgo"] == "ALTO")
medio = sum(1 for r in rows if r["riesgo"] == "MEDIO")
bajo = sum(1 for r in rows if r["riesgo"] == "BAJO")
print(f"Total: {len(rows)} | ALTO: {alto} | MEDIO: {medio} | BAJO: {bajo}")
print(f"CSV: {OUT}")
# Top archivos con riesgo ALTO
from collections import Counter
c = Counter(r["archivo"] for r in rows if r["riesgo"] == "ALTO")
print("Top archivos riesgo ALTO:")
for archivo, n in c.most_common(12):
    print(f"  {n:3d}  {archivo}")
