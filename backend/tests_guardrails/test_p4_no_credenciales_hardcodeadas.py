from pathlib import Path
import re
import sys

ROOTS = [Path("/app/backend"), Path("/app/frontend/src")]

ALLOW = [
    "tests_guardrails",
    "auditorias_",
    "venv",
    "node_modules",
    "__pycache__",
    ".git",
]

PATTERNS = [
    re.compile(r"admin123", re.IGNORECASE),
    re.compile(r"os\.environ\.get\([^,\)]*,\s*['\"][^'\"]+['\"]\)"),
    re.compile(r"os\.getenv\([^,\)]*,\s*['\"][^'\"]+['\"]\)"),
    re.compile(r"(password|pwd|secret|token)\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"(username|user)\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"(host|server)\s*=\s*['\"]\d{1,3}(\.\d{1,3}){3}['\"]", re.IGNORECASE),
    re.compile(r"EDARSAHUB_PASSWORD\s*="),
    re.compile(r"EDARSAHUB_USERNAME\s*="),
    re.compile(r"EDARSAHUB_HOST\s*="),
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
        if p.suffix.lower() not in [".py", ".js", ".jsx", ".ts", ".tsx", ".sh", ".md", ".txt"]:
            continue
        txt = p.read_text(errors="ignore")
        for pattern in PATTERNS:
            for m in pattern.finditer(txt):
                hits.append((sp.replace("/app/backend/", ""), pattern.pattern, m.group(0)[:80]))

if hits:
    print("FAIL credenciales/defaults hardcodeados:")
    for h in hits[:200]:
        print(h)
    sys.exit(1)

print("PASS sin credenciales/defaults críticos")
