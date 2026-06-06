from pathlib import Path
import re
import sys

ROOTS = [Path("/app/backend"), Path("/app/frontend/src")]

ALLOW = [
    "tests_guardrails",
    "auditorias_",
    ".bak",
    "venv",
    "node_modules",
    "__pycache__",
    ".git",
]

PATTERNS = [
    re.compile(r"admin123", re.IGNORECASE),
    re.compile(r"(password|pwd|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE),
]

hits = []

for root in ROOTS:
    if not root.exists():
        continue

    for p in root.rglob("*"):
        if not p.is_file():
            continue

        sp = str(p)

        if any(a in sp for a in ALLOW):
            continue

        if p.suffix not in [".py", ".js", ".jsx", ".ts", ".tsx", ".sh"]:
            continue

        try:
            txt = p.read_text(errors="ignore")
        except:
            continue

        for pattern in PATTERNS:
            for m in pattern.finditer(txt):
                hits.append((sp, pattern.pattern, m.group(0)[:80]))

if hits:
    print("FAIL credenciales/defaults hardcodeados detectados:")
    for h in hits[:50]:
        print(h)
    sys.exit(1)

print("PASS sin credenciales críticas hardcodeadas")
