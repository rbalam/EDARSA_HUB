from pathlib import Path
import sys

files = [
    "modules/auth/repository.py",
]

bad = []

for f in files:
    p = Path(f)
    if not p.exists():
        continue
    txt = p.read_text(errors="ignore").lower()
    if "pymongo" in txt or "mongoclient" in txt or "users.find" in txt:
        bad.append(f)

if bad:
    print("FAIL Auth repository todavía referencia Mongo:", bad)
    sys.exit(1)

print("PASS Auth repository sin MongoDB")
