"""Guardrail P5-3C: core/mongo_compat retirado (NO-MONGO end-state).

Falla si el shim de compatibilidad Mongo reaparece o si algún módulo lo importa.
"""
import re
from pathlib import Path

BACK = Path("/app/backend")
SKIP = ("__pycache__", ".bak_", "auditorias_p")


def test_mongo_compat_file_removed():
    assert not (BACK / "core" / "mongo_compat.py").exists(), \
        "core/mongo_compat.py debe estar retirado (sunset Mongo completado)"


def test_no_imports_of_mongo_compat():
    rx = re.compile(r"(from\s+core\.mongo_compat|import\s+core\.mongo_compat)")
    bad = []
    for p in BACK.rglob("*.py"):
        s = str(p)
        if any(x in s for x in SKIP):
            continue
        if rx.search(p.read_text(encoding="utf-8", errors="ignore")):
            bad.append(s)
    assert not bad, f"Imports residuales de core.mongo_compat: {bad}"
