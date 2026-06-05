from pathlib import Path
import re
import json
from datetime import datetime

ROOT = Path("/app/backend")

EXCLUDE = [
    ".bak_",
    "__pycache__",
    "/scripts/",
    "/tests/",
    "test_",
    "audit_",
    "backup",
    "dryrun",
    "dry_run",
    "core/config/",  # El config centralizado es válido
]

# Patrones estrictos de conexiones LIVE prohibidas
LIVE_PATTERNS = [
    r"SQL_LIVE\s*=\s*True",  # Conexión live activa
]

# Patrones estrictos de MongoDB productivo
MONGO_PATTERNS = [
    r"from\s+pymongo\s+import\s+MongoClient",
    r"MongoClient\s*\(",
    r"AsyncIOMotorClient\s*\(",
    r"\.find_one\s*\(",
    r"\.insert_one\s*\(",
    r"\.update_one\s*\(",
    r"db\s*=\s*client\[",
]

# Patrones estrictos de credenciales hardcodeadas (excluye comentarios y strings)
CREDENTIAL_PATTERNS = [
    r"os\.environ\.get\s*\(\s*['\"]EDARSAHUB_(HOST|DATABASE|USERNAME|PASSWORD)['\"]",
    r"os\.getenv\s*\(\s*['\"]EDARSAHUB_(HOST|DATABASE|USERNAME|PASSWORD)['\"]",
    r"os\.environ\.get\s*\(\s*['\"]EDARSAHUB_SQL_(HOST|DATABASE|USER|PASSWORD)['\"]",
    r"os\.getenv\s*\(\s*['\"]EDARSAHUB_SQL_(HOST|DATABASE|USER|PASSWORD)['\"]",
]

def excluded(path: Path):
    rel = str(path)
    return any(x in rel for x in EXCLUDE)

def is_comment_or_docstring(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''")

def scan(patterns, skip_comments=True):
    hits = []
    files = [ROOT / "server.py"] + list((ROOT / "core").rglob("*.py")) + list((ROOT / "modules").rglob("*.py"))
    for p in files:
        if not p.exists() or excluded(p):
            continue
        text = p.read_text(errors="ignore")
        for i, line in enumerate(text.splitlines(), start=1):
            if skip_comments and is_comment_or_docstring(line):
                continue
            for pat in patterns:
                if re.search(pat, line, re.I):
                    hits.append({
                        "file": str(p.relative_to("/app")),
                        "line": i,
                        "pattern": pat,
                        "code": line.strip()[:200]
                    })
                    break
    return hits

result = {
    "generated_at": datetime.now().isoformat(),
    "status": "OK",
    "checks": {
        "productive_live_connections": scan(LIVE_PATTERNS),
        "productive_mongo_imports": scan(MONGO_PATTERNS),
        "productive_hardcoded_credentials": scan(CREDENTIAL_PATTERNS),
    }
}

counts = {k: len(v) for k, v in result["checks"].items()}
result["counts"] = counts

# Determinar status
if counts["productive_hardcoded_credentials"] > 0:
    result["status"] = "FAIL"
    result["message"] = "Credenciales hardcodeadas detectadas en código productivo"
elif counts["productive_mongo_imports"] > 0:
    result["status"] = "WARNING"
    result["message"] = "Referencias MongoDB en código productivo (revisar si son legacy)"
elif counts["productive_live_connections"] > 0:
    result["status"] = "WARNING"  
    result["message"] = "Conexiones LIVE activas detectadas (verificar que sean solo para sync jobs)"
else:
    result["status"] = "OK"
    result["message"] = "SQL-First: Sin violaciones detectadas"

out = Path("/app/docs/auditorias/SQLFIRST_HEALTH_AUDIT.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "status": result["status"],
    "message": result.get("message", ""),
    "counts": counts,
}, indent=2))
