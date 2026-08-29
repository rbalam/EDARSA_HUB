import re, pathlib

ROOTS = ["modules", "api", "core"]
GENERIC = 'detail="Error interno del servidor"'

# Interpolaciones de excepción a eliminar SOLO dentro de detail=f"..."
LEAK_PATTERNS = [
    r":\s*\{str\(e\)\}", r":\s*\{e\}",
    r"\s*-\s*\{str\(e\)\}", r"\s*-\s*\{e\}",
    r"\{str\(e\)\}", r"\{e\}",
]

exact_count = 0
fstr_count = 0
files_changed = set()

for root in ROOTS:
    for p in pathlib.Path(root).rglob("*.py"):
        if "auditorias" in str(p) or "third_party" in str(p):
            continue
        lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
        changed = False
        for i, ln in enumerate(lines):
            orig = ln
            # 1) detail=str(e) exacto
            if "detail=str(e)" in ln:
                ln = ln.replace("detail=str(e)", GENERIC)
                exact_count += 1
            # 2) fugas dentro de detail=f"..."
            if 'detail=f"' in ln and ("{e}" in ln or "{str(e)}" in ln):
                for pat in LEAK_PATTERNS:
                    ln = re.sub(pat, "", ln)
                fstr_count += 1
            if ln != orig:
                lines[i] = ln
                changed = True
        if changed:
            p.write_text("".join(lines), encoding="utf-8")
            files_changed.add(str(p))

print("exact detail=str(e) replaced:", exact_count)
print("f-string detail leaks sanitized:", fstr_count)
print("files changed:", len(files_changed))
