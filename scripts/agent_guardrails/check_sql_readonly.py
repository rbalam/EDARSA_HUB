#!/usr/bin/env python3
import re
import sys
from pathlib import Path

BLOCKED = [
    r"\bDROP\b",
    r"\bTRUNCATE\b",
    r"\bALTER\b",
    r"\bCREATE\s+TABLE\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bMERGE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bsp_[A-Za-z0-9_]+\b",
]

def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: check_sql_readonly.py <archivo.sql|archivo.txt> [...]")
        return 2

    failed = False
    for raw in sys.argv[1:]:
        path = Path(raw)
        if not path.exists():
            print(f"NO_EXISTE: {path}")
            failed = True
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in BLOCKED:
            if re.search(pattern, text, flags=re.IGNORECASE):
                print(f"BLOQUEADO: {path} contiene patron peligroso: {pattern}")
                failed = True

    if failed:
        return 1

    print("OK: no se detectaron patrones SQL destructivos")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
