from pathlib import Path
import sys

roots = [
    Path("/app/backend"),
    Path("/app/frontend/src"),
]

allow = [
    "auditorias_seguridad",
    ".bak_security_",
    ".bak_",
    "__pycache__",
    "node_modules",
    ".git",
    "venv",
    "test_p0_no_admin123.py",
    "memory/",
]

hits=[]

for root in roots:
    if not root.exists():
        continue

    for p in root.rglob("*"):
        if not p.is_file():
            continue

        sp=str(p)

        if any(a in sp for a in allow):
            continue

        if p.suffix not in [".py",".js",".jsx",".ts",".tsx",".sh"]:
            continue

        txt=p.read_text(errors="ignore")

        if "admin123" in txt:
            hits.append(sp)

if hits:
    print("FAIL admin123 encontrado:")
    for h in hits:
        print(h)
    sys.exit(1)

print("PASS sin admin123")
