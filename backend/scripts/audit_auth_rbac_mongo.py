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
        if re.search(r"pymongo|motor|mongodb|MongoClient|AsyncIOMotorClient|get_mongo|get_database", line, re.I):
            print(f"L{i}: {line.strip()[:100]}")
            mongo_count += 1
    print(f"Total: {mongo_count}")

    print("\n--- FUNCIONES / CLASES ---")
    for i,line in enumerate(lines, start=1):
        if re.match(r"^(def|async def|class)\s+", line):
            print(f"L{i}: {line.strip()[:80]}")

