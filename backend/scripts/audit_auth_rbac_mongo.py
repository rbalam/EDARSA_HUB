from pathlib import Path
import re

targets = [
    "/app/backend/core/auth/user_repository_sql.py",
    "/app/backend/core/connection_resolver.py",
    "/app/backend/core/rbac/middleware.py"
]

for target in targets:
    p = Path(target)

    print("\n" + "="*120)
    print("ARCHIVO:", p)
    print("="*120)

    if not p.exists():
        print("NO EXISTE")
        continue

    txt = p.read_text(errors="ignore")
    lines = txt.splitlines()

    print("\n--- REFERENCIAS MONGO ---")
    mongo_count = 0
    for i,line in enumerate(lines, start=1):
        if re.search(r"pymongo|motor|mongodb|MongoClient|AsyncIOMotorClient|get_mongo|get_database|\.find\(|\.insert|\.update|\.delete", line, re.I):
            print(f"L{i}: {line.strip()[:100]}")
            mongo_count += 1
    if mongo_count == 0:
        print("(ninguna)")

    print("\n--- FUNCIONES PRINCIPALES ---")
    for i,line in enumerate(lines, start=1):
        if re.match(r"^(def|async def|class)\s+", line):
            print(f"L{i}: {line.strip()[:80]}")

    print("\n--- IMPORTADORES (primeros 15) ---")
    name = p.stem
    import_count = 0

    for py in Path("/app/backend").rglob("*.py"):
        if py == p or ".bak" in str(py) or "__pycache__" in str(py):
            continue

        try:
            t = py.read_text(errors="ignore")
        except:
            continue

        if name in t:
            for n,l in enumerate(t.splitlines(), start=1):
                if name in l and import_count < 15:
                    print(f"{py.relative_to('/app')}:{n}: {l.strip()[:80]}")
                    import_count += 1
            if import_count >= 15:
                break

