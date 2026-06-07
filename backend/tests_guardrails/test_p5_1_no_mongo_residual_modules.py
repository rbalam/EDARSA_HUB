"""Guardrail P5-1: Blindaje permanente NO-MONGO en /app/backend/modules/.

Falla (pytest assert / exit 1) si reaparece cualquiera de:
  1) imports vivos de Mongo: `import pymongo`, `from pymongo`, `import motor`,
     `from motor`, `MongoClient`, `AsyncIOMotorClient`.
  2) patrón roto de stub Mongo: una variable seteada a `None` y luego usada como
     conexión Mongo (`client = None` ... `db = client[...]` / `client.find(` /
     `client.find_one(`), que reventaría con NoneType si se reactivara.

Excluye backups, caches, auditorías y comentarios de deprecación.
Ejecutable con pytest o `python3 test_p5_1_no_mongo_residual_modules.py`.
"""
from pathlib import Path
import re

MODULES_ROOT = Path("/app/backend/modules")

# Subcadenas en la RUTA que excluyen el archivo del escaneo
PATH_ALLOW = (
    ".bak_", "__pycache__", "auditorias_p", "backup", "/scripts/", "legacy",
)

# Imports Mongo prohibidos (línea de código viva)
FORBIDDEN_IMPORTS = (
    re.compile(r"^\s*import\s+pymongo\b", re.M),
    re.compile(r"^\s*from\s+pymongo\b", re.M),
    re.compile(r"^\s*import\s+motor\b", re.M),
    re.compile(r"^\s*from\s+motor\b", re.M),
    re.compile(r"\bMongoClient\s*\(", re.M),
    re.compile(r"\bAsyncIOMotorClient\s*\(", re.M),
)

# Patrón roto: conexión seteada a None y luego usada como Mongo
RE_CLIENT_NONE = re.compile(r"^\s*client\s*=\s*None\b", re.M)
RE_CLIENT_AS_MONGO = re.compile(r"=\s*client\[|client\.(find_one|find|servers)\b", re.M)


def _strip_comments(text: str) -> str:
    """Elimina líneas de comentario completo para no falsos-positivos en docstrings simples."""
    out = []
    for ln in text.splitlines():
        stripped = ln.lstrip()
        if stripped.startswith("#"):
            continue
        out.append(ln)
    return "\n".join(out)


def _scan():
    forbidden_imports = []
    broken_stub = []
    if not MODULES_ROOT.exists():
        return forbidden_imports, broken_stub
    for p in MODULES_ROOT.rglob("*.py"):
        sp = str(p)
        if any(a in sp for a in PATH_ALLOW):
            continue
        raw = p.read_text(errors="ignore")
        code = _strip_comments(raw)
        for rx in FORBIDDEN_IMPORTS:
            if rx.search(code):
                forbidden_imports.append((sp, rx.pattern))
        if RE_CLIENT_NONE.search(code) and RE_CLIENT_AS_MONGO.search(code):
            broken_stub.append(sp)
    return forbidden_imports, broken_stub


def test_no_mongo_imports_in_modules():
    forbidden_imports, _ = _scan()
    assert not forbidden_imports, (
        "Imports Mongo vivos reintroducidos en /app/backend/modules/:\n"
        + "\n".join(f"  {f}: /{pat}/" for f, pat in forbidden_imports)
    )


def test_no_broken_mongo_stub_in_modules():
    _, broken_stub = _scan()
    assert not broken_stub, (
        "Patrón roto Mongo (`client = None` usado como conexión) en:\n"
        + "\n".join(f"  {f}" for f in broken_stub)
    )


if __name__ == "__main__":
    imports, broken = _scan()
    if imports or broken:
        if imports:
            print("FAIL - imports Mongo vivos:")
            for f, pat in imports:
                print(f"  {f}: /{pat}/")
        if broken:
            print("FAIL - patrón roto Mongo (client=None usado como conexión):")
            for f in broken:
                print(f"  {f}")
        raise SystemExit(1)
    print("PASS - /app/backend/modules sin residual Mongo (imports ni stubs rotos)")
