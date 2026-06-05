from pathlib import Path
import re

ROOT = Path("/app/backend")

targets = [
    "core/connection_resolver.py",
    "core/rbac/middleware.py"
]

patterns = [
    r"EDARSAHUB_SQL_PASSWORD",
    r"EDARSAHUB_PASSWORD",
    r"PASSWORD",
    r"PWD=",
    r"MongoClient",
    r"AsyncIOMotorClient",
    r"get_mongo_db",
    r"_get_mongo_connection",
]

print("=== ARCHIVOS CRÍTICOS P2 ===")

for t in targets:
    p = ROOT / t
    print("\n", "="*100)
    print(t)
    print("="*100)

    if not p.exists():
        print("NO EXISTE")
        continue

    txt = p.read_text(errors="ignore")

    for i,line in enumerate(txt.splitlines(), start=1):
        for pat in patterns:
            if re.search(pat, line, re.I):
                print(f"L{i}: {line.strip()[:100]}")
                break

print("\n=== CREDENCIALES HARDCODEADAS (primeras 100) ===")

count = 0
for p in ROOT.rglob("*.py"):
    if ".bak" in str(p) or "__pycache__" in str(p) or "backup" in str(p).lower():
        continue
    try:
        txt = p.read_text(errors="ignore")
    except:
        continue

    for i,line in enumerate(txt.splitlines(), start=1):
        if count >= 100:
            break
        line_lower = line.lower()
        if (
            ("password" in line_lower and "=" in line and "'" in line)
            or ("pwd=" in line_lower and "'" in line)
            or "national09" in line_lower
            or "hrlectura" in line_lower
        ):
            print(f"{p.relative_to(ROOT)}:{i}: {line.strip()[:120]}")
            count += 1
    if count >= 100:
        break

print(f"\n(Mostradas {count} referencias)")
